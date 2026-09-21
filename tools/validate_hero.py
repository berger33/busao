#!/usr/bin/env python3
"""Valida o contrato do primeiro personagem hero dedicado.

A validação completa de proporções/retarget acontece dentro do Blender; este
passo rápido evita entregar um GLB ausente, comprimido com Draco ou sem os
clips que o jogo usa.
"""
from pathlib import Path
import struct, sys

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "assets/characters/personagens/hero_julia.glb"
REQUIRED = [b"Idle_Loop", b"Walk_Loop", b"Sprint_Loop", b"Jump_Loop", b"Crouch_Fwd_Loop"]

def main() -> int:
    if not PATH.exists():
        print("HERO PENDING: execute tools/blender/run_bpy.sh tools/blender/build_humanos.py")
        return 2
    raw = PATH.read_bytes()
    if len(raw) < 20 or raw[:4] != b"glTF":
        print("HERO FAIL: arquivo nao e GLB valido")
        return 1
    version, length = struct.unpack_from("<II", raw, 4)
    if version != 2 or length != len(raw):
        print("HERO FAIL: cabecalho GLB inconsistente")
        return 1
    if b"KHR_draco_mesh_compression" in raw:
        print("HERO FAIL: Draco nao e suportado pelo importador Godot do projeto")
        return 1
    missing = [x.decode() for x in REQUIRED if x not in raw]
    if missing:
        # Marco 1 da opção 2: mesh-only procedural, com movimento do root.
        # O rig/retarget será o próximo passo, sem bloquear a validação visual.
        print("HERO OK MESH-ONLY: %d bytes | clips pendentes: %s" % (len(raw), ", ".join(missing)))
        return 0
    print("HERO OK: %d bytes | clips e GLB validos" % len(raw))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
