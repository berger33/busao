#!/bin/sh
# Recria o ambiente de Blender headless do sandbox (venv + stubs X11/GL).
#
# Por que existe: o sandbox nao tem Blender nem as bibliotecas X11/GL que o
# pacote pip `bpy` espera. O ambiente original era:
#   - venv /home/user/venv-blender com bpy==4.5.14 (e gdtoolkit, usado por
#     tools/check_gdscript.py)
#   - stubs .so vazios em /home/user/blender-stubs exportando os simbolos
#     X11/GL/ICE/SM que o bpy referencia (headless: nenhuma chamada X/GL de
#     verdade acontece; Cycles roda em CPU puro)
# Os dois caminhos ficam FORA do repo e podem ser limpos entre sessoes.
# Rode este script para reconstruir:  sh tools/blender/make_env.sh
#
# Requisitos: python3.11 com venv, pip (acesso ao PyPI), gcc, libX11/libXext
# do sistema (vem no container).

set -e
VENV="${VENV:-/home/user/venv-blender}"
STUBS="${STUBS:-/home/user/blender-stubs}"
BVER="4.5.14"

echo "==> venv em $VENV"
python3 -m venv "$VENV"
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q "bpy==$BVER" gdtoolkit

BPLY="$VENV/lib/python3.11/site-packages/bpy"
mkdir -p "$STUBS"
cd "$STUBS"

echo "==> lista de simbolos indefinidos dos .so do bpy"
find "$BPLY" -name '*.so*' -exec nm -D --undefined-only {} + 2>/dev/null \
  | awk '{print $2}' | sed 's/@.*//' | sort -u > all_undef.txt

echo "==> stubs GL (libGL.so.1)"
{
  echo 'void *glXGetProcAddress(const void *p) { (void)p; return 0; }'
  echo 'void *glXGetProcAddressARB(const void *p) { (void)p; return 0; }'
  grep -E '^(gl[A-Z]|GLX[A-Z]|wgl[A-Z])' all_undef.txt | while read -r s; do
    case "$s" in glXGetProcAddress*|glXGetProcAddressARB*) continue;; esac
    echo "void *${s}(void) { return 0; }"
  done
} | awk '!seen[$0]++' > glstub_full.c
gcc -shared -fPIC -o libGL.so.1 glstub_full.c

echo "==> stubs X11 (simbolos publicos + privados que os .so do sistema exigem)"
{
  grep -E '^(X|_X|Sm|Ice|xkbcommon)' all_undef.txt | while read -r s; do
    echo "void *${s}(void) { return 0; }"
  done
  for so in /lib/x86_64-linux-gnu/libXext.so.6 /lib/x86_64-linux-gnu/libX11.so.6; do
    [ -e "$so" ] && nm -D --undefined-only "$so" 2>/dev/null | awk '{print $2}' | sed 's/@.*//'
  done | grep -E '^(X|_X|Sm|Ice)' | sort -u | while read -r s; do
    echo "void *${s}(void) { return 0; }"
  done
} | awk '!seen[$0]++' > xall.c
for lib in libX11.so.6 libXt.so.6 libXfixes.so.3 libXrender.so.1 libXi.so.6 libSM.so.6 libICE.so.6; do
  gcc -shared -fPIC -o "$lib" xall.c
done

echo "==> stub libxkbcommon com versioning V_0.5.0"
{
  echo "// gerado"
  for s in $(grep -oE 'xkb[a-z_0-9]+' all_undef.txt | sort -u); do
    echo "void *${s}(void) { return 0; }"
  done
} | awk '!seen[$0]++' > xall2.c
{
  echo "V_0.5.0 {"
  echo "  global:"
  grep -oE 'xkb[a-z_0-9]+' all_undef.txt | sort -u | sed 's/^/    /; s/$/;/'
  echo "  local:"
  echo "    *;"
  echo "};"
} > xkb.ver
gcc -shared -fPIC -o libxkbcommon.so.0 xall2.c -Wl,--version-script=xkb.ver

echo "==> teste"
LD_LIBRARY_PATH="$STUBS:$BPLY/lib" "$VENV/bin/python" -c \
  "import bpy; print('bpy OK', bpy.app.version_string)"
echo "ambiente pronto. use: sh tools/blender/run_bpy.sh <script.py>"
