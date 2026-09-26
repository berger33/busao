#!/bin/sh
# Executa um script Python com bpy (Blender 4.5 headless) no sandbox.
# Requer: venv em /home/user/venv-blender (pip install bpy==4.5.14) e os
# stubs X11/GL em /home/user/blender-stubs (ver LEIA-ME.md desta pasta).
export LD_LIBRARY_PATH="/home/user/blender-stubs:/home/user/venv-blender/lib/python3.11/site-packages/bpy/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
exec /home/user/venv-blender/bin/python "$@"
