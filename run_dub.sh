#!/bin/bash
# run_dub.sh — end-to-end: media -> BaoCut -> LLM bot -> dub track -> muxed mp4
#
# Usage:
#   ./run_dub.sh <media-file-or-URL> [--title T] [--voice s1=zh-CN-X --voice s2=zh-CN-Y ...]
#                [--conc 6] [--rate +15%] [--outdir work]
#
# Needs: OPENCODE_GO_API_KEY in env (source ~/Downloads/soft/podcast-workbench/.env)
#        ffmpeg, yt-dlp (URL only), ~/.browser-use-env (edge-tts), BaoCut.app
set -euo pipefail
cd "$(dirname "$0")"

BC=/Applications/BaoCut.app/Contents/MacOS/baocut-cli
PY=$HOME/.browser-use-env/bin/python
MEDIA=$1; shift
TITLE="e2e dub"
VOICES=(--voice s1=zh-CN-YunjianNeural --voice s2=zh-CN-YunxiNeural)
CONC=6; RATE="+15%"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --title) TITLE=$2; shift 2;;
    --voice) VOICES+=(--voice "$2"); shift 2;;
    --no-default-voices) VOICES=(); shift;;
    --conc) CONC=$2; shift 2;;
    --rate) RATE=$2; shift 2;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done
: "${OPENCODE_GO_API_KEY:?missing OPENCODE_GO_API_KEY — source ~/Downloads/soft/podcast-workbench/.env}"

echo "== 1/6 auto (transcribe+speakers, then LLM stages pend)"
META=$($BC --json auto "$MEDIA" --lang zh --source-lang en --title "$TITLE")
TID=$(echo "$META" | python3 -c 'import json,sys; print(json.load(sys.stdin)["taskId"])')
PID=$(echo "$META" | python3 -c 'import json,sys; print(json.load(sys.stdin)["projectId"])')
echo "   projectId=$PID taskId=$TID"

echo "== 2/6 wait for transcription"
while :; do
  S=$($BC --json task status "$TID")
  PC=$(echo "$S" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("pendingCount") or 0)')
  PH=$(echo "$S" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("phase"))')
  echo "   $(date +%H:%M:%S) $PH pending=$PC"
  [[ "$PC" -gt 0 ]] && break
  sleep 20
done

echo "== 3/6 LLM worker bot"
python3 worker/llm_worker.py "$TID" --worker llm-bot --log "work/${PID}_bot.jsonl"

echo "== 4/6 speaker gate (stats only; multi-speaker runs the M3 gate manually)"
$BC speakers show "$PID" || true

echo "== 5/6 build dub track"
VDUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$MEDIA" 2>/dev/null || echo "")
TOTAL=${VDUR%.*}
$PY dub/build_dub.py "$PID" "${VOICES[@]}" --conc "$CONC" --rate "$RATE" \
    ${VDUR:+--total-dur "$VDUR"}

echo "== 6/6 mux + QC"
mkdir -p output
$BC export "$PID" --srt --translated --lang zh -o "output/${PID}_zh.srt"
$BC export "$PID" --srt -o "output/${PID}_en.srt"
ffmpeg -v error -y -i "$MEDIA" -i "work/$PID/zh_dub.wav" \
  -i "output/${PID}_zh.srt" -i "output/${PID}_en.srt" \
  -map 0:v -c:v copy \
  -map 1:a -c:a:0 aac -b:a:0 128k -ar 48000 -metadata:s:a:0 language=chi \
      -metadata:s:a:0 title="中文配音" -disposition:a:0 default \
  -map 0:a -c:a:1 copy -metadata:s:a:1 language=eng \
      -metadata:s:a:1 title="原声" -disposition:a:1 none \
  -map 2 -c:s:0 mov_text -metadata:s:s:0 language=chi \
  -map 3 -c:s:1 mov_text -metadata:s:s:1 language=eng \
  -movflags +faststart "output/${PID}_dubbed.mp4"
ffprobe -v error -show_entries format=duration -of csv=p=0 "output/${PID}_dubbed.mp4"
echo "DONE -> output/${PID}_dubbed.mp4"
