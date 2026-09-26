#!/bin/bash
# Gera o AAB de release assinado: portões -> keystore -> export headless.
# Uso: ./tools/build_aab.sh
# Env: GODOT_BIN (default: godot), KEYSTORE_PASS (default: pergunta via keytool).
# A senha NUNCA é commitada: injeta-se no preset temporariamente e restaura-se.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
GODOT="${GODOT_BIN:-godot}"
PRESET="export_presets.cfg"
KEYSTORE="$ROOT/../corre-pro-ponto.keystore"
AAB="build/corre-pro-ponto.aab"

echo "== portões =="
python3 tools/validate_project.py
python3 tools/qa_full.py > /dev/null
echo "OK  (qa_full verde)"

if [ ! -f "$KEYSTORE" ]; then
  echo "== keystore =="
  ./tools/make_keystore.sh "$KEYSTORE"
fi

if ! command -v "$GODOT" >/dev/null 2>&1; then
  echo "ERRO: binário Godot não encontrado (GODOT_BIN=$GODOT)."
  echo "Instale o Godot 4.x ou rode este script na máquina de release/CI."
  exit 2
fi

cp "$PRESET" "$PRESET.bak"
trap 'mv "$PRESET.bak" "$PRESET"; echo "(preset restaurado)"' EXIT
if [ -n "${KEYSTORE_PASS:-}" ]; then
  sed -i 's|^keystore/release_password=""$|keystore/release_password="'"$KEYSTORE_PASS"'"|' "$PRESET"
  echo "(senha via KEYSTORE_PASS, preset será restaurado)"
else
  echo "AVISO: KEYSTORE_PASS vazio — usando senha do preset/keystore interativo."
fi

mkdir -p build
echo "== exportando AAB =="
"$GODOT" --headless --path . --export-release "Android" "$AAB"
ls -la "$AAB"
echo "AAB pronto: $AAB"
