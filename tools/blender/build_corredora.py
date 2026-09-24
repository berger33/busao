#!/usr/bin/env python3
"""Gera somente a corredora Julia rigged para o jogo.

Execute pelo Blender local:
  blender --background --python tools/blender/build_corredora.py

O script reaproveita o construtor humano, exporta skeleton/skinning e as ações
Idle_Loop, Walk_Loop, Sprint_Loop, Jump_Loop, Crouch_Idle_Loop e
Crouch_Fwd_Loop em GLB sem Draco.
"""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from build_humanos import build_one, REPO

OUT = REPO / "assets" / "characters" / "personagens" / "hero_julia.glb"
OUT.parent.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    build_one(False, str(OUT))
    print("JULIA RIGGED OK:", OUT)
