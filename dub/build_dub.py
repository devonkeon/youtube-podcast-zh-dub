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
    p = subprocess.run([BC, "--json", "subtitle", "list", pid, "--lang", lang],
                       capture_output=True, text=True, check=True)
    d = json.loads(p.stdout)
    return [s for s in d["subtitles"] if not s.get("hidden")]


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


async def synth_one(sem, unit, voice, outdir, rate=None, retries=4):
    out = os.path.join(outdir, f"{unit['uid']}.mp3")
    if os.path.exists(out) and os.path.getsize(out) > 0:
        unit["mp3"] = out
        return  # resume: skip already-synthesized
    async with sem:
        for attempt in range(retries):
            try:
                kw = {"rate": rate} if rate else {}
                await edge_tts.Communicate(unit["text"], voice, **kw).save(out)
                unit["mp3"] = out
                return
            except Exception as e:  # noqa: BLE001
                unit["err"] = repr(e)[:200]
                await asyncio.sleep(2 ** attempt)
        raise RuntimeError(f"synth failed for {unit['uid']}: {unit.get('err')}")


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

    voices = dict(v.split("=", 1) for v in a.voice)
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
    async def run():
        await asyncio.gather(*[synth_one(sem, u, voices[u["speakerId"]], outdir,
                                         rate=rate)
                               for u in units])
    asyncio.run(run())

    # fit + place
    wavs = []
    for u in units:
        # decode + trim silence first, THEN measure (edge-tts pads a lot)
        twav = os.path.join(outdir, f"{u['uid']}_trim.wav")
        subprocess.run([FFMPEG, "-v", "error", "-y", "-i", u["mp3"],
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
    report = {
        "project": a.project,
        "units": len(units),
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
