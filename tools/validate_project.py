#!/usr/bin/env python3
"""Fast, dependency-free preflight checks for Corre pro Ponto.

This is intentionally not a Godot replacement: run the Godot editor/headless
export as the final validation. It catches the common repository mistakes
first: missing res:// files, duplicate private functions, broken phase counts,
and invalid binary assets.
"""
from __future__ import annotations

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
    for required_file in ("scripts/hud_3d.gd", "scripts/scenario_data.gd", "scripts/character_data.gd"):
        if not (ROOT / required_file).exists():
            fail(f"missing {required_file}")
    scenario_data = (ROOT / "scripts/scenario_data.gd").read_text(encoding="utf-8")
    character_data = (ROOT / "scripts/character_data.gd").read_text(encoding="utf-8")
    if scenario_data.count('"id":') != 10:
        fail("scenario_data.gd does not declare 10 scenario chapters")
    if character_data.count('"id":') != 10:
        fail("character_data.gd does not declare 10 characters")
    if character_data.count('"gender": "M"') != 5 or character_data.count('"gender": "F"') != 5:
        fail("character_data.gd does not contain five M and five F characters")
    game_3d = (ROOT / "scripts/game_3d.gd").read_text(encoding="utf-8")
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
        'TEXTURE_HAIR_REAL',
        'TEXTURE_DENIM_REAL',
        'TEXTURE_ASPHALT_REAL',
        'TEXTURE_SIDEWALK_REAL',
        'material.albedo_texture = texture',
        'material.normal_enabled = true',
        'subsurf_scatter_skin_mode = true',
        '_traffic_speed_for(kind, entities.size())',
        'LeftLegPivotElbow',
        'TorusMesh.new()',
        'course_root.position.z = distance',
        '_update_sky_fx(dt)',
    )
    required_obstacles = (
        "car", "bus_traffic", "motorcycle", "pothole", "truck",
        "old_lady", "hydrant", "payphone", "dog", "bicycle", "cone", "vendor", "bench",
    )
    for token in required_tokens:
        if token not in game_3d:
            fail(f"3D runner missing required token: {token}")
    for obstacle in required_obstacles:
        if f'"{obstacle}"' not in game_3d:
            fail(f"3D runner missing required obstacle: {obstacle}")


def check_assets() -> None:
    for svg in [ROOT / "assets/art/icon.svg", *sorted((ROOT / "assets/textures").glob("*.svg"))]:
        try:
            ET.parse(svg)
        except (ET.ParseError, OSError) as exc:
            fail(f"{svg.relative_to(ROOT)}: {exc}")
    required_textures = {
        "asfalto_realista.png", "calcada_realista.png", "ceu_tropical.png",
        "ceu_entardecer.png", "ceu_nublado.png", "cabelo_realista.png", "jeans_realista.png"
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
    check_assets()
    if ERRORS:
        print("PRE-FLIGHT FAILED")
        print("\n".join(f"- {error}" for error in ERRORS))
        return 1
    print("PRE-FLIGHT OK: paths, scripts, 50-phase catalog, SVG/PNG textures, WAV and feedback audio assets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
