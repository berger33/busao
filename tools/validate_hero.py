#!/usr/bin/env python3
"""Valida o contrato visual/estrutural do hero sem exigir Blender ou Godot."""
from pathlib import Path
import struct, json, sys

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "assets/characters/personagens/hero_julia.glb"
REQUIRED = [b"Idle_Loop", b"Walk_Loop", b"Sprint_Loop", b"Jump_Loop", b"Crouch_Fwd_Loop"]
PARTS = {"LeftThigh", "RightThigh", "LeftCalf", "RightCalf", "UpperArmL", "UpperArmR", "ForearmL", "ForearmR", "Torso"}

def glb_json(raw):
    chunk_len, chunk_type = struct.unpack_from("<II", raw, 12)
    if chunk_type != 0x4E4F534A:
        return {}
    return json.loads(raw[20:20 + chunk_len].decode("utf-8"))

def main() -> int:
    if not PATH.exists():
        print("HERO PENDING: asset ausente")
        return 2
    raw = PATH.read_bytes()
    if len(raw) < 20 or raw[:4] != b"glTF":
        print("HERO FAIL: arquivo nao e GLB valido"); return 1
    version, length = struct.unpack_from("<II", raw, 4)
    if version != 2 or length != len(raw):
        print("HERO FAIL: cabecalho GLB inconsistente"); return 1
    if b"KHR_draco_mesh_compression" in raw:
        print("HERO FAIL: Draco nao e suportado"); return 1
    doc = glb_json(raw)
    names = {n.get("name", "") for n in doc.get("nodes", [])}
    found = PARTS & names
    missing_parts = sorted(PARTS - found)
    missing_clips = [x.decode() for x in REQUIRED if x not in raw]
    if missing_parts:
        print("HERO WARN PARTS: " + ", ".join(missing_parts))
    if missing_clips:
        print("HERO OK MESH-ONLY: %d bytes | partes %d/%d | clips pendentes: %s" % (len(raw), len(found), len(PARTS), ", ".join(missing_clips)))
    else:
        print("HERO OK RIGGED: %d bytes | clips e partes validos" % len(raw))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
