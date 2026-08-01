#!/usr/bin/env python3
"""llm_worker.py — drive a BaoCut task queue with an OpenAI-compatible LLM API.

Replaces the human agent loop: claim -> read contract+payload -> LLM -> submit --next.

Usage:
  OPENCODE_GO_API_KEY=sk-... python3 llm_worker.py <taskId> [--worker NAME]
      [--model deepseek-v4-flash] [--base-url https://opencode.ai/zen/go/v1]
      [--max-rounds 200] [--log FILE]

Exit 0 when the task reaches a terminal state (done/review), 2 on failure.
Stdlib only. Tested against BaoCut 0.8.3 task protocol (see docs/BAOCUT_NOTES.md).
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request

BC = "/Applications/BaoCut.app/Contents/MacOS/baocut-cli"


def bc_json(*args, timeout=120):
    p = subprocess.run([BC, "--json", *args], capture_output=True, text=True, timeout=timeout)
    out = (p.stdout or "").strip()
    try:
        return json.loads(out), p.returncode
    except json.JSONDecodeError:
        return {"_raw": out, "_stderr": p.stderr}, p.returncode


def llm(base_url, api_key, model, system, user, max_tokens=16000, temperature=None):
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": max_tokens,
        # deepseek-v4-flash on opencode.ai reasons by default and can burn the
        # whole completion budget on reasoning_content (observed: 16k tokens,
        # empty content). Disabled by default; pass --thinking to re-enable.
        "thinking": {"type": "disabled"},
    }
    if temperature is not None:
        body["temperature"] = temperature
    req = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(body).encode(),
        headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json",
            # opencode.ai is behind Cloudflare; the default urllib UA gets
            # blocked with "error code: 1010" — send a browser UA instead
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/126.0 Safari/537.36",
        },
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        d = json.loads(r.read().decode())
    msg = d["choices"][0]["message"]
    usage = d.get("usage", {})
    return msg.get("content") or "", usage


def log_line(logf, rec):
    rec["at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    line = json.dumps(rec, ensure_ascii=False)
    print(line, flush=True)
    if logf:
        with open(logf, "a") as f:
            f.write(line + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("task_id")
    ap.add_argument("--worker", default="llm-bot")
    ap.add_argument("--model", default="deepseek-v4-flash")
    ap.add_argument("--base-url", default="https://opencode.ai/zen/go/v1")
    ap.add_argument("--api-key-env", default="OPENCODE_GO_API_KEY")
    ap.add_argument("--max-rounds", type=int, default=200)
    ap.add_argument("--max-retries", type=int, default=3)
    ap.add_argument("--log", default=None)
    a = ap.parse_args()

    api_key = os.environ.get(a.api_key_env)
    if not api_key:
        sys.exit("missing env " + a.api_key_env)

    problems = None
    for rnd in range(a.max_rounds):
        claim, rc = bc_json("task", "claim", a.task_id, "--worker", a.worker, "--timeout", "90")
        state = claim.get("state") or claim.get("status")
        if claim.get("terminal") or state in ("done", "review", "failed", "cancelled"):
            log_line(a.log, {"ev": "terminal", "state": state, "task": a.task_id})
            return 0 if state in ("done", "review") else 2
        if state == "already-claimed":
            # a previous (crashed) run of this worker still holds the lease:
            # release it and re-claim fresh to recover full metadata
            log_line(a.log, {"ev": "release-stale", "call": claim.get("heldCallId")})
            bc_json("task", "release", a.task_id, "--call", claim.get("heldCallId"),
                    "--lease-id", claim.get("heldLeaseId"), "--reason", "worker-restart")
            claim, rc = bc_json("task", "claim", a.task_id, "--worker", a.worker, "--timeout", "90")
            state = claim.get("status")
        call_id = claim.get("callId")
        if not call_id:
            # timeout with no pending call: check status, maybe finished
            st, _ = bc_json("task", "status", a.task_id)
            s = st.get("status")
            if s in ("done", "review"):
                log_line(a.log, {"ev": "terminal", "state": s, "task": a.task_id})
                return 0
            if s in ("failed", "cancelled", "stalled"):
                log_line(a.log, {"ev": "terminal", "state": s, "task": a.task_id})
                return 2
            log_line(a.log, {"ev": "wait", "raw": str(claim)[:300]})
            time.sleep(5)
            continue

        kind = claim.get("kind")
        lease = claim.get("leaseId")
        payload_file = claim.get("payloadFile")
        contract_file = claim.get("contractFile")
        if not contract_file and claim.get("contractsDir"):
            contract_file = os.path.join(claim["contractsDir"],
                                         claim.get("contract") or f"{kind}.md")
        t0 = time.time()
        system = open(contract_file).read() if contract_file else ""
        user = open(payload_file).read() if payload_file else ""
        if problems:
            user += ("\n\n# Previous attempt was REJECTED by the linter. "
                     "Fix these problems and answer again:\n" + json.dumps(problems, ensure_ascii=False))

        answer, usage = "", {}
        err = None
        try:
            answer, usage = llm(a.base_url, api_key, a.model, system, user)
        except Exception as e:  # noqa: BLE001
            err = repr(e)
        if err or not answer.strip():
            log_line(a.log, {"ev": "llm-error", "call": call_id, "err": err or "empty"})
            time.sleep(10)
            continue

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            f.write(answer)
            ans_file = f.name
        sub, _ = bc_json("task", "submit", a.task_id, "--call", call_id,
                         "--lease-id", lease, "--file", ans_file)
        os.unlink(ans_file)
        ok = sub.get("status") == "accepted" or sub.get("submitted") or sub.get("ok")
        if sub.get("status") == "rejected" or (sub.get("problems") and not ok):
            problems = sub.get("problems")
            log_line(a.log, {"ev": "rejected", "call": call_id, "kind": kind,
                             "problems": str(problems)[:500]})
            # release so we can re-claim immediately with feedback
            bc_json("task", "release", a.task_id, "--call", call_id,
                    "--lease-id", lease, "--reason", "lint-retry")
            continue
        problems = None
        log_line(a.log, {"ev": "accepted", "call": call_id, "kind": kind,
                         "sec": round(time.time() - t0, 1),
                         "inTok": usage.get("prompt_tokens"),
                         "outTok": usage.get("completion_tokens")})
    return 2


if __name__ == "__main__":
    sys.exit(main())
