#!/usr/bin/env python3
"""build_dub.py — build the Chinese dub track for a BaoCut project.

Pipeline (M4/M5):
  1. read zh groups from `baocut subtitle list <pid> --lang zh --json`
  2. merge pathological units (dur<0.7s & gap<0.2s) into the next same-speaker group
  3. synthesize each unit with edge-tts (async pool, retry/backoff), per-speaker voice
  4. fit each unit into its time slot: allowed = dur + 0.6*gap; overflow -> atempo
  5. place on the absolute timeline -> zh_dub.wav (drift is 0 by construction)
  6. write dub_report.json (per-unit synth/fit stats + stretch histogram)

Run with the venv python that has edge_tts:
  ~/.browser-use-env/bin/python dub/build_dub.py p2 \
      --voice s1=zh-CN-YunjianNeural --voice s2=zh-CN-YunxiNeural --conc 6
"""
import argparse
import asyncio
import json
import os
import subprocess
import sys
import tempfile

BC = "/Applications/BaoCut.app/Contents/MacOS/baocut-cli"
FFMPEG = "ffmpeg"
FFPROBE = "ffprobe"
SR = 24000  # edge-tts output sample rate

import edge_tts  # noqa: E402


def bc_groups(pid, lang):
    # NOTE: `subtitle list` defaults to --limit 200 — long projects silently
    # truncate (p5: returned 200 of total 474). Always pass an explicit limit.
    p = subprocess.run([BC, "--json", "subtitle", "list", pid, "--lang", lang,
                        "--limit", "100000"],
                       capture_output=True, text=True, check=True)
    d = json.loads(p.stdout)
    subs = [s for s in d["subtitles"] if not s.get("hidden")]
    if d.get("returned") != d.get("total"):
        raise RuntimeError(f"subtitle list truncated: {d.get('returned')}/{d.get('total')}")
    return subs


def merge_pathological(groups, min_dur=0.7, max_gap=0.2):
    """Merge a too-short too-tight group into the next same-speaker group."""
    units = []
    i = 0
    while i < len(groups):
        g = dict(groups[i])
        dur = g["end"] - g["start"]
        gap = (groups[i + 1]["start"] - g["end"]) if i + 1 < len(groups) else 9e9
        if dur < min_dur and gap < max_gap and i + 1 < len(groups) \
                and groups[i + 1].get("speakerId") == g.get("speakerId"):
            n = dict(groups[i + 1])
            n["text"] = g["text"] + n["text"]
            n["start"] = g["start"]
            n["merged_from"] = [g["id"], n["id"]]
            units.append(n)
            i += 2
        else:
            units.append(g)
            i += 1
    return units


# ---------- TTS engines ----------
# Voice spec (per --voice sid=SPEC):
#   zh-CN-YunxiNeural                     edge-tts only
#   moss:/path/ref.wav[,edge-voice]       MOSS clone (ref text from ref.wav同名.txt), then edge
#   mimo:/path/ref.wav[,edge-voice]       MiMo clone first, then edge
# Clone engines fall back to the edge voice on failure (429/timeout/5xx).

MOSS_URL = "https://api.mosi.cn/v1/audio/speech"
MOSS_MODEL = "moss-tts"
MOSS_VERSION = "flash-20260626"  # MOSS-TTS was retired upstream; flash is the
                                 # current version and wants JSON (not multipart)
MIMO_MODEL = "mimo-v2.5-tts-voiceclone"
MIMO_CTX = ("这是一档英文播客的中文配音。说话人是在录音室里轻松地访谈聊天，"
            "语气自然、口语化，不要播音腔。")

import base64  # noqa: E402
import urllib.error  # noqa: E402
import urllib.request  # noqa: E402


def _data_uri(path):
    mime = "audio/wav" if path.lower().endswith(".wav") else "audio/mpeg"
    return f"data:{mime};base64," + base64.b64encode(open(path, "rb").read()).decode()


def _http_json(url, obj, headers, timeout):
    req = urllib.request.Request(url, data=json.dumps(obj, ensure_ascii=False).encode(),
                                 headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), r.headers.get("content-type", "")


def synth_moss(text, ref_wav, ref_text, out, timeout=300):
    key = os.environ.get("MOSS_API_KEY")
    if not key:
        raise RuntimeError("MOSS_API_KEY not set")
    obj = {"model": MOSS_MODEL, "version": MOSS_VERSION, "input": text,
           "ref_audio": _data_uri(ref_wav), "ref_text": ref_text,
           "language": "Chinese", "response_format": "wav"}
    data, ct = _http_json(MOSS_URL, obj,
                          {"Authorization": f"Bearer {key}",
                           "Content-Type": "application/json"}, timeout)
    if len(data) < 1000:
        raise RuntimeError(f"moss audio too small ({len(data)}B)")
    open(out, "wb").write(data)


def synth_mimo(text, ref_wav, out, timeout=120):
    key = os.environ.get("XIAOMI_API_KEY")
    # NOTE: XIAOMI_BASE_URL in some env files points at the anthropic chat
    # endpoint (…/anthropic) — TTS voiceclone lives at api.xiaomimimo.com/v1.
    base = os.environ.get("XIAOMI_TTS_BASE_URL", "https://api.xiaomimimo.com/v1")
    if not key:
        raise RuntimeError("XIAOMI_API_KEY not set")
    obj = {"model": MIMO_MODEL,
           "messages": [{"role": "user", "content": MIMO_CTX},
                        {"role": "assistant", "content": text}],
           "audio": {"format": "wav", "voice": _data_uri(ref_wav)}}
    data, _ = _http_json(base.rstrip("/") + "/chat/completions", obj,
                         {"api-key": key, "Authorization": f"Bearer {key}",
                          "Content-Type": "application/json"}, timeout)
    audio = json.loads(data)["choices"][0]["message"]["audio"]["data"]
    open(out, "wb").write(base64.b64decode(audio))


async def synth_edge(text, voice, out, rate=None):
    kw = {"rate": rate} if rate else {}
    await edge_tts.Communicate(text, voice, **kw).save(out)


def parse_voice_spec(spec):
    """-> ordered chain of engine dicts.

    SPEC: engine1+engine2,edge-fallback — clone engines join with '+',
    plain names are edge-tts voices (fallbacks). Examples:
      moss:/ref.wav+yunxi            -> moss clone, edge yunxi
      mimo:/a.wav+moss:/b.wav,yunxi  -> mimo, moss, edge yunxi
    """
    chain = []
    parts = spec.split(",")
    for first in parts[0].split("+"):
        if first.startswith("moss:"):
            ref = first[5:]
            txt = os.path.splitext(ref)[0] + ".txt"
            chain.append({"engine": "moss", "ref": ref,
                          "ref_text": open(txt).read() if os.path.exists(txt) else ""})
        elif first.startswith("mimo:"):
            chain.append({"engine": "mimo", "ref": first[5:]})
        elif first.startswith("es:"):
            # es:user:<uuid>[:model] — EdgeSpeak local clone (default omnivoice)
            rest = first[3:]
            vid, _, mdl = rest.rpartition(":") if rest.count(":") > 1 else (rest, "", "")
            chain.append({"engine": "espeak",
                          "voice": vid if mdl else rest,
                          "model": mdl or "omnivoice"})
        elif first:
            chain.append({"engine": "edge", "voice": first})
    for p in parts[1:]:
        if p:
            chain.append({"engine": "edge", "voice": p})
    return chain


ESPEAK_CLI = "/Applications/EdgeSpeak.app/Contents/Resources/edgespeak-cli"


def synth_espeak(text, voice_id, out, model="omnivoice", timeout=300):
    """EdgeSpeak local on-device TTS (no key, no quota; ~3.5x RTF, serial)."""
    p = subprocess.run([ESPEAK_CLI, "speech", text, "-o", out,
                        "--model", model, "--voice", voice_id,
                        "--language", "zh-CN"],
                       capture_output=True, text=True, timeout=timeout)
    if p.returncode != 0 or not os.path.exists(out):
        raise RuntimeError(f"edgespeak: {(p.stderr or p.stdout)[:200]}")


_espeak_lock = None  # asyncio.Lock created lazily inside the event loop


async def synth_one(sem, unit, chain, outdir, rate=None, retries=3, broken=None,
                    guard_secs=0.35):
    """Try each engine in the chain; per-engine circuit breaker for 429/401/403.

    Duration guard: clone engines can hallucinate long pauses (observed: moss
    turning "因为它们…" into 10s of mostly silence). If synth exceeds
    chars*guard_secs, retry the same engine once, then fall through.
    """
    broken = broken if broken is not None else {}
    text = unit["text"].replace("…", "，").replace("...", "，")  # … drives long pauses
    limit = max(len(text) * guard_secs, 1.5)
    last = None
    for eng in chain:
        name = eng["engine"]
        ext = ".mp3" if name == "edge" else ".wav"
        out = os.path.join(outdir, f"{unit['uid']}.{name}{ext}")
        if os.path.exists(out) and os.path.getsize(out) > 0:
            unit["src"] = out
            unit["engine"] = name
            return  # resume: skip already-synthesized
        if broken.get(name):
            last = f"{name} circuit-open"
            continue
        async with sem:
            for attempt in range(retries):
                try:
                    if name == "edge":
                        await synth_edge(text, eng["voice"], out, rate)
                    elif name == "moss":
                        await asyncio.to_thread(synth_moss, text, eng["ref"],
                                                eng["ref_text"], out)
                    elif name == "mimo":
                        await asyncio.to_thread(synth_mimo, text, eng["ref"], out)
                    elif name == "espeak":
                        global _espeak_lock
                        if _espeak_lock is None:
                            _espeak_lock = asyncio.Lock()
                        async with _espeak_lock:  # local GPU: serialize
                            await asyncio.to_thread(synth_espeak, text,
                                                    eng["voice"], out,
                                                    eng.get("model", "omnivoice"))
                    dur = ffprobe_dur(out)
                    if dur > limit:
                        last = f"{name} dur-guard {dur:.1f}s>{limit:.1f}s"
                        os.unlink(out)
                        if attempt == 0:
                            continue  # one free resample on the same engine
                        break  # then fall through to the next engine
                    unit["src"] = out
                    unit["engine"] = name
                    return
                except urllib.error.HTTPError as e:
                    last = f"{name} HTTP {e.code}"
                    if e.code in (401, 403, 429):
                        broken[name] = True  # quota/auth problems: stop trying
                        break
                    await asyncio.sleep(2 ** attempt)
                except Exception as e:  # noqa: BLE001
                    last = f"{name}: {repr(e)[:150]}"
                    await asyncio.sleep(2 ** attempt)
    raise RuntimeError(f"all engines failed for {unit['uid']}: {last}")


# edge-tts pads utterances with leading/trailing silence (measured: ~1.15s on a
# 3.9s clip) — trim both ends before measuring, it matters most on short groups
TRIM = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,"
        "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,"
        "areverse")


def ffprobe_dur(path):
    p = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", path], capture_output=True, text=True, check=True)
    return float(p.stdout.strip())


def atempo_chain(ratio):
    """ffmpeg atempo accepts [0.5, 100] since 5.x but quality degrades >2; chain at 2."""
    parts = []
    r = ratio
    while r > 2.0:
        parts.append("atempo=2.0")
        r /= 2.0
    parts.append(f"atempo={r:.4f}")
    return ",".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--voice", action="append", required=True,
                    help="sid=voice, e.g. s1=zh-CN-YunjianNeural")
    ap.add_argument("--conc", type=int, default=6)
    ap.add_argument("--rate", default="+15%",
                    help="edge-tts rate (natural cps 3.9 is too slow for dubbing; "
                         "+15%% measured to cut most over-slot units) | 'none' to disable")
    ap.add_argument("--gap-spill", type=float, default=0.6,
                    help="fraction of the following silence a unit may occupy")
    ap.add_argument("--outdir", default=None)
    ap.add_argument("--total-dur", type=float, default=None,
                    help="target track length (default: last group end)")
    a = ap.parse_args()

    voices = {k: parse_voice_spec(v) for k, v in (s.split("=", 1) for s in a.voice)}
    outdir = a.outdir or f"work/{a.project}"
    os.makedirs(outdir, exist_ok=True)

    groups = bc_groups(a.project, "zh")
    units = merge_pathological(groups)
    for i, u in enumerate(units):
        u["uid"] = f"u{i:03d}"
        u["dur"] = u["end"] - u["start"]
        u["gap"] = (units[i + 1]["start"] - u["end"]) if i + 1 < len(units) else 0.0
    total = a.total_dur or units[-1]["end"]

    missing = {u.get("speakerId") for u in units} - set(voices)
    if missing:
        sys.exit(f"no voice for speakers: {missing}")

    sem = asyncio.Semaphore(a.conc)
    rate = None if a.rate.lower() == "none" else a.rate
    broken = {}  # shared per-engine circuit breaker (429/401/403)
    async def run():
        await asyncio.gather(*[synth_one(sem, u, voices[u["speakerId"]], outdir,
                                         rate=rate, broken=broken)
                               for u in units])
    asyncio.run(run())
    if broken:
        print("circuit-open engines (fell back):", list(broken), file=sys.stderr)

    # fit + place
    wavs = []
    for u in units:
        # decode + trim silence first, THEN measure (edge-tts pads a lot)
        twav = os.path.join(outdir, f"{u['uid']}_trim.wav")
        subprocess.run([FFMPEG, "-v", "error", "-y", "-i", u["src"],
                        "-af", f"aresample={SR},{TRIM}", "-ac", "1", "-ar", str(SR),
                        twav], check=True)
        synth = ffprobe_dur(twav)
        allowed = u["dur"] + a.gap_spill * max(0.0, u["gap"])
        ratio = synth / allowed if allowed > 0.05 else 1.0
        u["synth_dur"] = round(synth, 3)
        u["allowed"] = round(allowed, 3)
        u["stretch"] = round(ratio, 3) if ratio > 1.0 else 1.0
        wav = os.path.join(outdir, f"{u['uid']}.wav")
        if ratio > 1.0:
            subprocess.run([FFMPEG, "-v", "error", "-y", "-i", twav,
                            "-af", atempo_chain(ratio), "-ac", "1", "-ar", str(SR),
                            wav], check=True)
        else:
            os.replace(twav, wav)
        u["final_dur"] = round(ffprobe_dur(wav), 3)
        wavs.append(wav)

    # assemble on the absolute timeline (adelay + amix, no volume normalization)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        graph = f
        for i, u in enumerate(units):
            ms = int(round(u["start"] * 1000))
            f.write(f"[{i}:a]adelay={ms}|{ms}[d{i}];\n")
        mix = "".join(f"[d{i}]" for i in range(len(units)))
        f.write(f"{mix}amix=inputs={len(units)}:normalize=0,"
                f"apad,atrim=0:{total:.3f}[out]\n")
    dub_wav = os.path.join(outdir, "zh_dub.wav")
    cmd = [FFMPEG, "-v", "error", "-y"]
    for w in wavs:
        cmd += ["-i", w]
    cmd += ["-filter_complex_script", graph.name, "-map", "[out]",
            "-ac", "1", "-ar", str(SR), dub_wav]
    subprocess.run(cmd, check=True)
    os.unlink(graph.name)

    stretches = [u["stretch"] for u in units]
    from collections import Counter
    engines = Counter(u.get("engine") for u in units)
    report = {
        "project": a.project,
        "units": len(units),
        "engines": dict(engines),
        "merged": [u.get("merged_from") for u in units if u.get("merged_from")],
        "voices": voices,
        "total_dur": total,
        "dub_wav": dub_wav,
        "stretch_hist": {
            "1.0 (no stretch)": sum(1 for s in stretches if s == 1.0),
            "1.0-1.25": sum(1 for s in stretches if 1.0 < s <= 1.25),
            "1.25-1.5": sum(1 for s in stretches if 1.25 < s <= 1.5),
            ">1.5": sum(1 for s in stretches if s > 1.5),
            "max": max(stretches),
        },
        "detail": [{k: u.get(k) for k in
                    ("uid", "id", "speakerId", "start", "dur", "gap", "allowed",
                     "synth_dur", "stretch", "final_dur", "merged_from", "text")}
                   for u in units],
    }
    with open(os.path.join(outdir, "dub_report.json"), "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print(json.dumps(report["stretch_hist"], ensure_ascii=False))
    print("units:", len(units), "merged:", len(report["merged"]), "->", dub_wav)


if __name__ == "__main__":
    main()
