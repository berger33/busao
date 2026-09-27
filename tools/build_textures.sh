#!/usr/bin/env bash
# Reconstroi todo o acervo de texturas a partir dos scans fotorrealistas
# versionados em tools/source_textures/.
#
# A ORDEM IMPORTA: texture_forge gera as superficies lisas (inclusive a
# alvenaria lisa de reboco/tijolo) e facade_forge depois SOBRESCREVE
# fachada_reboco.png / fachada_tijolo.png com o atlas de janelas montado por
# cima dessa alvenaria.
set -euo pipefail
cd "$(dirname "$0")/.."

python3 tools/texture_forge.py      # asfalto, calcada, concreto, tijolo, ...
python3 tools/sky_forge.py          # panoramas equiretangulares 360
python3 tools/facade_forge.py       # atlas de fachada 4x4
python3 tools/make_texture_imports.py  # .import das texturas novas
python3 tools/fix_texture_imports.py   # mipmaps + compressao VRAM

echo "Texturas reconstruidas. Abra o projeto no Godot para reimportar."
