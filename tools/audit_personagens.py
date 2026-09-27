#!/usr/bin/env python3
"""Audit do personagem principal — boneco v2 (personagens/personagem_v2.glb).

O elenco foi reduzido a 1 corredor jogavel (o boneco v2). Os demais ids do
catalogo continuam listados na loja como INDISPONIVEL, sem GLB dedicado.
Checagens: o unico GLB existe, header glTF 2.0 binario, skins/animations/JOINTS_0,
sem Draco, e integra com o loader do runner_character.gd; os corpos humanos base
continuam presentes como fallback dos pedestres."""
import struct, pathlib, sys, json

ROOT = pathlib.Path(__file__).resolve().parents[1]
PERSONAGENS = ROOT / "assets/characters/personagens"
RUNNER = ROOT / "scripts/runner_character.gd"
CHAR_DATA = ROOT / "scripts/character_data.gd"

HERO_GLB = "personagem_v2.glb"


def check_glb_header(path):
    data = path.read_bytes()
    if len(data) < 12:
        return False, "too small"
    magic, version, length = struct.unpack("<4sII", data[:12])
    if magic != b"glTF":
        return False, f"bad magic {magic}"
    if version != 2:
        return False, f"bad version {version}"
    if length != len(data):
        return False, f"length mismatch {length} vs {len(data)}"
    offset = 12
    json_str = None
    while offset + 8 <= len(data):
        chunk_len, chunk_type = struct.unpack("<II", data[offset:offset + 8])
        chunk_data = data[offset + 8: offset + 8 + chunk_len]
        if chunk_type == 0x4E4F534A:  # JSON
            try:
                json_str = chunk_data.decode("utf-8")
                break
            except Exception:
                pass
        offset += 8 + chunk_len
    if not json_str:
        return False, "no JSON chunk"
    doc = json.loads(json_str)
    has_skins = bool(doc.get("skins"))
    has_anims = bool(doc.get("animations"))
    has_meshes = bool(doc.get("meshes"))
    has_skinning = any(
        "JOINTS_0" in (p.get("attributes") or {})
        for m in doc.get("meshes", [])
        for p in m.get("primitives", [])
    )
    return True, {"skins": has_skins, "anims": has_anims, "meshes": has_meshes, "skinning": has_skinning, "doc": doc}


def main():
    errors = []
    print("=== AUDIT PERSONAGEM PRINCIPAL — boneco v2 ===")
    # 1. runner_character loader prioriza o asset dedicado do hero
    runner_text = RUNNER.read_text(encoding="utf-8")
    if "HERO_ASSET_PATH" not in runner_text or "personagem_v2.glb" not in runner_text:
        errors.append("runner_character.gd não aponta HERO_ASSET_PATH para personagem_v2.glb")
    else:
        print("OK runner_character.gd: HERO_ASSET_PATH -> personagem_v2.glb")
    if "_setup_v2_animation" not in runner_text or "_setup_v2_hair" not in runner_text:
        errors.append("runner_character.gd sem setup de animação/cabelo do v2")
    # 2. character_data com 1 id ativo
    char_text = CHAR_DATA.read_text(encoding="utf-8")
    if "ACTIVE_IDS" not in char_text or '"julia"' not in char_text:
        errors.append("character_data.gd sem ACTIVE_IDS/julia")
    else:
        print("OK character_data.gd: ACTIVE_IDS = [julia]")
    # 3. o GLB do hero
    p = PERSONAGENS / HERO_GLB
    if not p.exists():
        errors.append(f"missing GLB {HERO_GLB}")
    else:
        sz = p.stat().st_size
        if sz > 2 * 1024 * 1024:
            errors.append(f"{HERO_GLB} {sz} >2MB")
        ok, info = check_glb_header(p)
        if not ok:
            errors.append(f"{HERO_GLB} header failed: {info}")
        else:
            doc = info["doc"]
            if "KHR_draco_mesh_compression" in doc.get("extensionsRequired", []):
                errors.append(f"{HERO_GLB} usa Draco — Godot 4 não decodifica (personagem invisível)")
            if not info["skins"]:
                errors.append(f"{HERO_GLB} sem skins")
            if not info["anims"]:
                errors.append(f"{HERO_GLB} sem animations")
            if not info["skinning"]:
                errors.append(f"{HERO_GLB} sem JOINTS_0/WEIGHTS_0")
            anims = doc.get("animations", [])
            if len(anims) < 6:
                errors.append(f"{HERO_GLB} animations {len(anims)} <6")
            print(f"OK {HERO_GLB:18s} {sz/1024:7.1f} KB | skins={len(doc.get('skins', []))} anims={len(anims)} meshes={len(doc.get('meshes', []))} skinning={info['skinning']}")
    # 4. não pode sobrar GLB dos personagens antigos
    extras = sorted(g.name for g in PERSONAGENS.glob("*.glb") if g.name != HERO_GLB)
    if extras:
        errors.append("GLBs de personagens antigos ainda presentes: " + ", ".join(extras))
    # 5. corpos humanos base (fallback dos pedestres)
    for fallback in ["Humano_M.glb", "Humano_F.glb"]:
        if not (ROOT / "assets/characters/humanos_originais" / fallback).exists():
            errors.append(f"fallback humano {fallback} ausente")
    if errors:
        print("\nAUDIT FAIL:")
        for e in errors:
            print(" -", e)
        return 1
    print("\nAUDIT OK: 1 personagem jogável (boneco v2), header/skins/animations OK, loader dedicado ativo, fallback humano preservado")
    return 0


if __name__ == "__main__":
    sys.exit(main())
