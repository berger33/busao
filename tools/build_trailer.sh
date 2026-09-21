#!/bin/bash
# Monta o trailer de 30 s (Play Store): screenshots + trilha própria.
# Uso: ./tools/build_trailer.sh [saida.mp4]
# Requer: ffmpeg.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
OUT="${1:-build/trailer_30s.mp4}"
SHOTS=(store/screenshots/0*.png)
MUSIC="assets/audio/music_terminal.wav"

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ERRO: ffmpeg não encontrado."
  exit 2
fi
if [ ! -f "$MUSIC" ]; then
  echo "ERRO: trilha $MUSIC ausente."
  exit 1
fi
echo "shots: ${#SHOTS[@]}"

LIST="$(mktemp)"
trap 'rm -f "$LIST"' EXIT
PER=3.75
for s in "${SHOTS[@]}"; do
  echo "file '$ROOT/$s'" >> "$LIST"
  echo "duration $PER" >> "$LIST"
done
# último frame precisa repetir (quirky do concat)
echo "file '$ROOT/${SHOTS[-1]}'" >> "$LIST"

mkdir -p build
ffmpeg -y -f concat -safe 0 -i "$LIST" -stream_loop 4 -i "$MUSIC" \
  -t 30 -vf "scale=1080:1920,format=yuv420p" -c:v libx264 -preset veryfast \
  -c:a aac -shortest "$OUT"
ls -la "$OUT"
echo "Trailer pronto: $OUT"
