#!/usr/bin/env python3
"""Fast, dependency-free preflight checks for Corre pro Ponto.

This is intentionally not a Godot replacement: run the Godot editor/headless
export as the final validation. It catches the common repository mistakes
first: missing res:// files, duplicate private functions, broken phase counts,
and invalid binary assets.
"""
from __future__ import annotations

import hashlib
import re
import sys
import wave
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ERRORS: list[str] = []


def fail(message: str) -> None:
    ERRORS.append(message)


def check_paths() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in ROOT.rglob("*.gd"))
    text += "\n" + (ROOT / "project.godot").read_text(encoding="utf-8")
    for raw in sorted(set(re.findall(r"res://[^\"']+", text))):
        resource = raw.split("\"")[0].split("'")[0]
        if "*" not in resource and not (ROOT / resource.removeprefix("res://")).exists():
            fail(f"missing resource: {resource}")


def check_scripts() -> None:
    for path in (ROOT / "scripts").glob("*.gd"):
        text = path.read_text(encoding="utf-8")
        functions = re.findall(r"^func\s+([A-Za-z_]\w*)\s*\(", text, re.MULTILINE)
        duplicates = sorted({name for name in functions if functions.count(name) > 1})
        if duplicates:
            fail(f"duplicate function(s) in {path.name}: {', '.join(duplicates)}")
        for bracket_a, bracket_b in (("(", ")"), ("[", "]"), ("{", "}")):
            if text.count(bracket_a) != text.count(bracket_b):
                fail(f"unbalanced {bracket_a}{bracket_b} in {path.name}")


def check_catalog() -> None:
    phase = (ROOT / "scripts/phase_data.gd").read_text(encoding="utf-8")
    match = re.search(r"const PHASE_COUNT := (\d+)", phase)
    if not match or int(match.group(1)) != 50:
        fail("phase catalog does not declare PHASE_COUNT := 50")
    for name in ("EXTRA_NAMES", "EXTRA_LOCATIONS", "EXTRA_SPECIALS"):
        block = re.search(rf"const {name} := \[(.*?)\]\n\s*(?:const|static func)", phase, re.DOTALL)
        count = len(re.findall(r'"(?:[^"\\]|\\.)*"', block.group(1))) if block else 0
        if count != 30:
            fail(f"{name} has {count} entries; expected 30")


def check_3d_entrypoint() -> None:
    scene = (ROOT / "scenes/main.tscn").read_text(encoding="utf-8")
    if 'path="res://scripts/game_3d.gd"' not in scene:
        fail("main scene does not use scripts/game_3d.gd")
    if '[node name="CorreProPonto3D" type="Node3D"]' not in scene:
        fail("main scene root is not CorreProPonto3D / Node3D")
    for required_file in (
        "scripts/hud_3d.gd", "scripts/scenario_data.gd", "scripts/character_data.gd",
        "scripts/runner_character.gd", "scripts/world_character.gd", "scripts/world_animal.gd",
        "scripts/obstacle_data.gd",
    ):
        if not (ROOT / required_file).exists():
            fail(f"missing {required_file}")
    scenario_data = (ROOT / "scripts/scenario_data.gd").read_text(encoding="utf-8")
    character_data = (ROOT / "scripts/character_data.gd").read_text(encoding="utf-8")
    obstacle_data = (ROOT / "scripts/obstacle_data.gd").read_text(encoding="utf-8")
    if scenario_data.count('"id":') != 10:
        fail("scenario_data.gd does not declare 10 scenario chapters")
    if character_data.count('"id":') != 10:
        fail("character_data.gd does not declare 10 characters")
    if character_data.count('"gender": "M"') != 5 or character_data.count('"gender": "F"') != 5:
        fail("character_data.gd does not contain five M and five F characters")
    if obstacle_data.count('"id":') != 13:
        fail("obstacle_data.gd does not declare the 13 3D obstacle contracts")
    for obstacle_id in ("car", "bus_traffic", "motorcycle", "pothole", "truck", "old_lady", "hydrant", "payphone", "dog", "bicycle", "cone", "vendor", "bench"):
        if f'"id": "{obstacle_id}"' not in obstacle_data:
            fail(f"obstacle_data.gd missing 3D contract: {obstacle_id}")
    game_3d = (ROOT / "scripts/game_3d.gd").read_text(encoding="utf-8")
    runner_character = (ROOT / "scripts/runner_character.gd").read_text(encoding="utf-8")
    world_character = (ROOT / "scripts/world_character.gd").read_text(encoding="utf-8")
    world_animal = (ROOT / "scripts/world_animal.gd").read_text(encoding="utf-8")
    character_sources = game_3d + "\n" + runner_character + "\n" + world_character + "\n" + world_animal
    required_tokens = (
        'const LANE_X: Array[float] = [-3.25, 0.0, 3.25]',
        'const ROAD_OBSTACLES',
        'const SIDEWALK_OBSTACLES',
        'var road_interval:',
        'var sidewalk_interval:',
        'Camera3D.new()',
        'PanoramaSkyMaterial.new()',
        'TEXTURE_SKY_PANORAMA',
        'TEXTURE_SKY_SUNSET',
        'TEXTURE_SKY_CLOUDY',
        'const RUNNER_CHARACTER_SCRIPT = preload("res://scripts/runner_character.gd")',
        'const WORLD_CHARACTER_SCRIPT = preload("res://scripts/world_character.gd")',
        'const WORLD_ANIMAL_SCRIPT = preload("res://scripts/world_animal.gd")',
        'const OBSTACLE_DATA = preload("res://scripts/obstacle_data.gd")',
        'player_visual.call("set_motion"',
        '_validate_obstacle_catalog()',
        '_audit_3d_entity',
        '_audit_world_geometry',
        'HumanPedestrian3D',
        'Animal3D_caramelo',
        'BoneAttachment3D',
        '_attach_creator_details(profile)',
        'TEXTURE_CREATOR_DENIM',
        'TEXTURE_CREATOR_METAL',
        'CreatorTexturedTop',
        'CreatorDenimShorts',
        'CreatorPhone',
        'CreatorTattoo',
        'CreatorEarring',
        'CreatorBracelet',
        'set_world_mode',
        'CarameloDog3D',
        'DogEye',
        'DogCollar',
        'DogTag',
        'Superhero_Male_FullBody.gltf',
        'UAL1_Standard.res',
        'QuaterniusOutfit_',
        'AnimationLibrary',
        'TEXTURE_DENIM_REAL',
        'TEXTURE_CAR_PAINT_REAL',
        'TEXTURE_ASPHALT_REAL',
        'TEXTURE_SIDEWALK_REAL',
        'material.albedo_texture = texture',
        'material.normal_enabled = true',
        'subsurf_scatter_skin_mode = true',
        '_traffic_speed_for(kind, entities.size())',
        'TorusMesh.new()',
        '_build_brazilian_car(parent, abs(parent.name.hash()) % 3',
        'TrafficCone',
        'DogMuzzle',
        'course_root.position.z = distance',
        '_update_sky_fx(dt)',
    )
    required_obstacles = (
        "car", "bus_traffic", "motorcycle", "pothole", "truck",
        "old_lady", "hydrant", "payphone", "dog", "bicycle", "cone", "vendor", "bench",
    )
    for token in required_tokens:
        if token not in character_sources:
            fail(f"3D runner missing required token: {token}")
    for obstacle in required_obstacles:
        if f'"{obstacle}"' not in game_3d:
            fail(f"3D runner missing required obstacle: {obstacle}")


def check_character_manifest(root: Path) -> None:
    manifest_path = root / "PROVENANCE.md"
    text = manifest_path.read_text(encoding="utf-8")
    entries = re.findall(
        r"^([0-9a-f]{64})\s+([^\s]+)\s+\((\d+) bytes\)$",
        text,
        re.MULTILINE,
    )
    manifest_files = {relative for _, relative, _ in entries}
    expected_files = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.name != "PROVENANCE.md"
    }
    if not entries:
        fail("character provenance has no SHA-256 manifest entries")
        return
    if manifest_files != expected_files:
        missing = sorted(expected_files - manifest_files)
        extra = sorted(manifest_files - expected_files)
        detail = []
        if missing:
            detail.append("missing " + ", ".join(missing))
        if extra:
            detail.append("extra " + ", ".join(extra))
        fail("character SHA-256 manifest file list mismatch: " + "; ".join(detail))
    for expected_hash, relative, expected_size in entries:
        path = root / relative
        if not path.is_file():
            continue
        payload = path.read_bytes()
        actual_hash = hashlib.sha256(payload).hexdigest()
        if actual_hash != expected_hash or len(payload) != int(expected_size):
            fail(f"character SHA-256 mismatch: {relative}")


def check_character_assets() -> None:
    root = ROOT / "assets/characters/quaternius"
    required = [
        "QUATERNIUS-LICENSE.txt",
        "PROVENANCE.md",
        "animation/UAL1_Standard.res",
        "animation/UAL1_Standard.glb",
        "base/Superhero_Male_FullBody.gltf",
        "base/Superhero_Male_FullBody.bin",
        "base/Superhero_Female_FullBody.gltf",
        "base/Superhero_Female_FullBody.bin",
        "base/T_Hair_1_BaseColor.png",
        "base/T_Hair_1_Normal.png",
        "base/T_Hair_2_BaseColor.png",
        "base/T_Hair_2_Normal.png",
        "base/T_Eye_Brown.png",
        "base/T_Eye_Normal.png",
        "base/T_Superhero_Male_Dark.png",
        "base/T_Superhero_Male_Normal.png",
        "base/T_Superhero_Male_Roughness.png",
        "base/T_Superhero_Female_Dark_BaseColor.png",
        "base/T_Superhero_Female_Normal.png",
        "base/T_Superhero_Female_Roughness.png",
        "parts/T_Peasant_BaseColor.png",
        "parts/T_Peasant_Normal.png",
        "parts/T_Peasant_ORM.png",
        "parts/T_Regular_Male_Dark_BaseColor.png",
        "parts/T_Regular_Male_Normal.png",
        "parts/T_Regular_Male_Roughness.png",
        "parts/T_Regular_Female_Dark_BaseColor.png",
        "parts/T_Regular_Female_Normal.png",
        "parts/T_Regular_Female_Roughness.png",
    ]
    for gender in ("Male", "Female"):
        for part in ("Body", "Arms", "Legs", "Feet"):
            required.extend([
                f"parts/{gender}_Peasant_{part}.gltf",
                f"parts/{gender}_Peasant_{part}.bin",
            ])
    for relative in required:
        if not (root / relative).is_file():
            fail(f"missing character asset: assets/characters/quaternius/{relative}")
    try:
        check_character_manifest(root)
    except (OSError, UnicodeError) as exc:
        fail(f"cannot read character SHA-256 manifest: {exc}")
    for gltf in sorted(root.rglob("*.gltf")):
        try:
            import json
            document = json.loads(gltf.read_text(encoding="utf-8"))
            for buffer in document.get("buffers", []):
                uri = buffer.get("uri")
                if uri and not (gltf.parent / uri).is_file():
                    fail(f"missing GLTF buffer: {gltf.relative_to(ROOT)} -> {uri}")
            for image in document.get("images", []):
                uri = image.get("uri")
                if uri and not (gltf.parent / uri).is_file():
                    fail(f"missing GLTF texture: {gltf.relative_to(ROOT)} -> {uri}")
            if not document.get("skins"):
                fail(f"character GLTF is not skinned: {gltf.relative_to(ROOT)}")
            if not any("JOINTS_0" in primitive.get("attributes", {}) and "WEIGHTS_0" in primitive.get("attributes", {})
                       for mesh in document.get("meshes", []) for primitive in mesh.get("primitives", [])):
                fail(f"character GLTF has no joint weights: {gltf.relative_to(ROOT)}")
        except (OSError, ValueError) as exc:
            fail(f"invalid character GLTF {gltf.relative_to(ROOT)}: {exc}")
    animation = root / "animation/UAL1_Standard.res"
    try:
        payload = animation.read_bytes()
        if not payload.startswith(b"RSRC") or b"AnimationLibrary" not in payload:
            fail("animation/UAL1_Standard.res is not a Godot AnimationLibrary resource")
        for clip in (b"Idle_Loop", b"Jog_Fwd_Loop", b"Sprint_Loop", b"Crouch_Idle_Loop", b"Crouch_Fwd_Loop"):
            if clip not in payload:
                fail(f"animation library missing clip: {clip.decode()}")
    except OSError as exc:
        fail(f"cannot read character animation library: {exc}")
    animation_source = root / "animation/UAL1_Standard.glb"
    try:
        source_payload = animation_source.read_bytes()
        if source_payload[:4] != b"glTF":
            fail("animation/UAL1_Standard.glb is not a GLB")
        for clip in (b"Idle_Loop", b"Walk_Loop", b"Sprint_Loop", b"Jump_Loop", b"Crouch_Fwd_Loop"):
            if clip not in source_payload:
                fail(f"animation GLB missing clip: {clip.decode()}")
    except OSError as exc:
        fail(f"cannot read character animation GLB: {exc}")
    for texture in root.rglob("*.png"):
        try:
            if texture.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
                fail(f"invalid character PNG signature: {texture.relative_to(ROOT)}")
        except OSError as exc:
            fail(f"{texture.relative_to(ROOT)}: {exc}")


def check_assets() -> None:
    for svg in [ROOT / "assets/art/icon.svg", *sorted((ROOT / "assets/textures").glob("*.svg"))]:
        try:
            ET.parse(svg)
        except (ET.ParseError, OSError) as exc:
            fail(f"{svg.relative_to(ROOT)}: {exc}")
    required_textures = {
        "asfalto_realista.png", "calcada_realista.png", "ceu_tropical.png",
        "ceu_entardecer.png", "ceu_nublado.png", "cabelo_realista.png", "jeans_realista.png", "pintura_carro_realista.png"
    }
    available_textures = {path.name for path in (ROOT / "assets/textures").glob("*.png")}
    for name in sorted(required_textures - available_textures):
        fail(f"missing raster texture: assets/textures/{name}")
    for path in (ROOT / "assets/textures").glob("*.png"):
        try:
            if path.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
                fail(f"invalid PNG signature: {path.relative_to(ROOT)}")
        except OSError as exc:
            fail(f"{path.relative_to(ROOT)}: {exc}")
    required_audio = {
        "click.wav", "ui_confirm.wav", "ui_back.wav", "coin.wav", "combo.wav",
        "reward.wav", "streak.wav", "whoosh.wav", "impact_heavy.wav"
    }
    available_audio = {path.name for path in (ROOT / "assets/audio").glob("*.wav")}
    for name in sorted(required_audio - available_audio):
        fail(f"missing feedback audio: assets/audio/{name}")
    for path in (ROOT / "assets/audio").glob("*.wav"):
        try:
            with wave.open(str(path), "rb") as audio:
                if audio.getnchannels() < 1 or audio.getframerate() < 8000:
                    fail(f"invalid audio metadata: {path}")
        except (wave.Error, OSError) as exc:
            fail(f"{path}: {exc}")


def main() -> int:
    check_paths()
    check_scripts()
    check_catalog()
    check_3d_entrypoint()
    check_character_assets()
    check_assets()
    if ERRORS:
        print("PRE-FLIGHT FAILED")
        print("\n".join(f"- {error}" for error in ERRORS))
        return 1
    print("PRE-FLIGHT OK: paths, scripts, 50-phase catalog, 13-obstacle 3D contract, SVG/PNG textures, WAV and feedback audio assets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
