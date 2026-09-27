#!/usr/bin/env python3
"""Gera o pacote visual estilizado do ambiente.

A versão anterior tentava simular sujeira/ruído fotográfico e, em jogo, isso
virava pontilhado preto e aspecto pixelado nos prédios e no chão. Este gerador
mantém PBR/normal/ORM, mas troca o detalhe por formas limpas, cores quentes e
variação suave: o cenário fica coeso com a personagem/árvores e mais agradável
em mobile.
"""
from __future__ import annotations

import math
import os
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "textures"
OUT_PBR = OUT / "pbr"
SIZE = int(os.environ.get("PBR_SIZE", "1024"))
if SIZE not in (1024, 2048, 4096):
    SIZE = 1024
MASTER_SEED = 20260927


# ---------------------------------------------------------------------------
# Helpers: ruído suave/tileable, normais e escrita
# ---------------------------------------------------------------------------

def value_noise(freq: int, rng: np.random.Generator, size: int = SIZE) -> np.ndarray:
    freq = max(1, min(freq, size))
    grid = rng.random((freq, freq))
    y, x = np.mgrid[0:size, 0:size]
    fx = x * freq / size
    fy = y * freq / size
    x0 = np.floor(fx).astype(np.int64) % freq
    y0 = np.floor(fy).astype(np.int64) % freq
    x1 = (x0 + 1) % freq
    y1 = (y0 + 1) % freq
    sx = 0.5 - 0.5 * np.cos((fx - np.floor(fx)) * math.pi)
    sy = 0.5 - 0.5 * np.cos((fy - np.floor(fy)) * math.pi)
    v00 = grid[y0, x0]
    v10 = grid[y0, x1]
    v01 = grid[y1, x0]
    v11 = grid[y1, x1]
    a = v00 * (1.0 - sx) + v10 * sx
    b = v01 * (1.0 - sx) + v11 * sx
    return a * (1.0 - sy) + b * sy


def fbm(freq: int, octaves: int, rng: np.random.Generator, gain: float = 0.52, size: int = SIZE) -> np.ndarray:
    total = np.zeros((size, size), dtype=np.float64)
    amp = 1.0
    acc = 0.0
    f = freq
    for _ in range(octaves):
        total += value_noise(f, rng, size) * amp
        acc += amp
        amp *= gain
        f = min(size, f * 2)
    total /= max(acc, 1e-9)
    lo, hi = float(total.min()), float(total.max())
    if hi - lo > 1e-9:
        total = (total - lo) / (hi - lo)
    return total


def height_to_normal(height: np.ndarray, strength: float) -> np.ndarray:
    # OpenGL normal map (Y+). Strength baixo: estilo limpo, sem ruído agressivo.
    norm_strength = strength * (1024.0 / float(height.shape[0]))
    dx = np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)
    dy = np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)
    nx = -dx * norm_strength * 64.0
    ny = -dy * norm_strength * 64.0
    nz = np.ones_like(height)
    length = np.sqrt(nx * nx + ny * ny + nz * nz)
    rgb = np.stack([nx / length * 0.5 + 0.5, ny / length * 0.5 + 0.5, nz / length * 0.5 + 0.5], axis=-1)
    return np.clip(rgb * 255.0, 0, 255).astype(np.uint8)


def save_rgb(arr: np.ndarray, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if arr.ndim == 2:
        arr = np.stack([arr, arr, arr], axis=-1)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")
    img.save(path, optimize=True)
    print(f"  {path.relative_to(ROOT)} {img.size[0]}x{img.size[1]}")


def save_height(height: np.ndarray, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.fromarray(np.clip(height * 65535.0, 0, 65535).astype(np.uint16))
    img.save(path, optimize=True)
    print(f"  {path.relative_to(ROOT)} {img.size[0]}x{img.size[1]} 16-bit")


def orm_map(ao: np.ndarray, rough: np.ndarray, metallic: np.ndarray | float = 0.0) -> np.ndarray:
    if not isinstance(metallic, np.ndarray):
        metallic = np.full_like(ao, float(metallic))
    return np.stack([np.clip(ao, 0, 1), np.clip(rough, 0, 1), np.clip(metallic, 0, 1)], axis=-1)


def soft_rect_mask(x: np.ndarray, y: np.ndarray, x0: float, x1: float, y0: float, y1: float, edge: float = 2.0) -> np.ndarray:
    # Retângulo com borda levemente anti-aliased para textura estilizada.
    inside_x = np.minimum(x - x0, x1 - x)
    inside_y = np.minimum(y - y0, y1 - y)
    d = np.minimum(inside_x, inside_y)
    return np.clip((d + edge) / max(edge, 0.001), 0.0, 1.0)


# ---------------------------------------------------------------------------
# Materiais estilizados principais
# ---------------------------------------------------------------------------

def gen_asphalt() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(MASTER_SEED + 10)
    y, x = np.mgrid[0:SIZE, 0:SIZE]
    xf = x / float(SIZE)
    macro = fbm(5, 4, rng)
    mid = fbm(18, 3, rng)
    fine = fbm(56, 2, rng)
    # Base azul-grafite suave: sem pontos pretos/brancos e sem granulação fina.
    v = 0.265 + 0.032 * macro + 0.018 * mid + 0.006 * fine
    lane_track = np.exp(-((xf - 0.34) ** 2) / 0.0032) + np.exp(-((xf - 0.67) ** 2) / 0.0034)
    lane_track = np.clip(lane_track, 0, 1) * (0.55 + 0.45 * fbm(9, 2, rng))
    v -= lane_track * 0.014
    # Remendos grandes e quase no mesmo tom: dão forma sem parecer sujeira.
    patch = fbm(7, 3, rng) > 0.84
    v = np.where(patch, v * 0.965 + 0.006, v)
    cracks = np.zeros((SIZE, SIZE), dtype=np.float64)
    albedo = np.stack([v * 0.94, v * 0.97, v * 1.03], axis=-1)
    height = 0.50 + 0.055 * fine + 0.045 * mid - 0.040 * lane_track
    height = np.where(patch, height * 0.92 + 0.035, height)
    rough = 0.86 + 0.035 * fine - 0.045 * lane_track - 0.025 * patch.astype(np.float64)
    return np.clip(albedo, 0, 1), np.clip(height, 0, 1), np.clip(rough, 0.55, 0.96)


def gen_large_slabs() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(MASTER_SEED + 20)
    y, x = np.mgrid[0:SIZE, 0:SIZE]
    slab_w, slab_h, grout_w = 246, 184, 5
    row = y // slab_h
    off = (row % 2) * (slab_w // 2)
    col = (x + off) // slab_w
    tile_id = row * 83 + col
    tint_rng = np.random.default_rng(MASTER_SEED + 21)
    tint = tint_rng.random(8192)[tile_id % 8192]
    grain = fbm(42, 3, rng)
    smooth = fbm(9, 2, rng)
    grout = ((x + off) % slab_w < grout_w) | (y % slab_h < grout_w)
    edge = ((x + off) % slab_w < grout_w + 9) | (y % slab_h < grout_w + 9)
    base = np.stack([
        0.63 + 0.08 * tint,
        0.59 + 0.07 * tint,
        0.50 + 0.055 * tint,
    ], axis=-1)
    albedo = base * (0.95 + 0.07 * (grain - 0.5) + 0.04 * (smooth - 0.5))[..., None]
    albedo = np.where(grout[..., None], np.array([0.38, 0.36, 0.31])[None, None, :], albedo)
    albedo = np.where((edge & ~grout)[..., None], albedo * 0.93, albedo)
    # Poucas marcas suaves, sem pontinhos pretos.
    stain = fbm(6, 2, rng) > 0.82
    albedo = np.where((stain & ~grout)[..., None], albedo * 0.92, albedo)
    height = np.where(grout, 0.30, 0.56 + 0.08 * grain + 0.04 * tint)
    height = np.where(edge & ~grout, height - 0.045, height)
    rough = np.where(grout, 0.92, 0.78 + 0.07 * (1.0 - grain))
    return np.clip(albedo, 0, 1), np.clip(height, 0, 1), np.clip(rough, 0.58, 1.0)


def gen_mosaic(wave: bool = False) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(MASTER_SEED + (31 if wave else 30))
    y, x = np.mgrid[0:SIZE, 0:SIZE]
    stone, grout_w = 64, 4
    cell_y = y // stone
    cell_x = x // stone
    cell = cell_y * (SIZE // stone + 1) + cell_x
    tint_rng = np.random.default_rng(MASTER_SEED + 32)
    tint = tint_rng.random(4096)[cell % 4096]
    grain = fbm(18, 2, rng)
    grout = ((x % stone < grout_w) | (y % stone < grout_w))
    if wave:
        center = 0.52 + 0.22 * np.sin(2.0 * math.pi * (x / float(SIZE)) + 0.8)
        accent = np.clip(1.0 - np.abs(y / float(SIZE) - center) / 0.075, 0.0, 1.0)
    else:
        # Nada de pedras pretas aleatórias: só variação sutil por ladrilho.
        accent = np.zeros((SIZE, SIZE), dtype=np.float64)
    light = 0.60 + 0.045 * tint + 0.018 * (grain - 0.5)
    accent_v = 0.49 + 0.030 * tint + 0.012 * (grain - 0.5)
    base = light * (1.0 - accent) + accent_v * accent
    albedo = np.stack([base * 1.035, base, base * 0.925], axis=-1)
    albedo = np.where(grout[..., None], np.array([0.47, 0.45, 0.40])[None, None, :], albedo)
    height = np.where(grout, 0.40, 0.54 + 0.045 * grain + 0.018 * tint)
    rough = np.where(grout, 0.88, 0.80 + 0.045 * (1.0 - grain))
    return np.clip(albedo, 0, 1), np.clip(height, 0, 1), np.clip(rough, 0.58, 1.0)


def gen_stucco() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(MASTER_SEED + 40)
    mott = fbm(10, 3, rng)
    broad = fbm(4, 2, rng)
    v = 0.70 + 0.028 * (mott - 0.5) + 0.045 * (broad - 0.5)
    albedo = np.stack([v * 1.08, v * 1.02, v * 0.90], axis=-1)
    # Escorridos muito suaves, sem speckles.
    y, x = np.mgrid[0:SIZE, 0:SIZE]
    streak_seed = fbm(12, 2, rng)
    streak = (streak_seed > 0.84) * np.clip(y / SIZE, 0, 1) * 0.018
    albedo = albedo * (1.0 - streak[..., None])
    height = 0.50 + 0.030 * mott + 0.025 * broad
    rough = 0.84 + 0.035 * (1.0 - mott)
    return np.clip(albedo, 0, 1), np.clip(height, 0, 1), np.clip(rough, 0.68, 0.96)


def gen_brick(subtle: bool = False) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(MASTER_SEED + (51 if subtle else 50))
    y, x = np.mgrid[0:SIZE, 0:SIZE]
    bw, bh, mortar = (128, 42, 6) if subtle else (96, 38, 5)
    row = y // bh
    off = (row % 2) * (bw // 2)
    brick_col = (x + off) // bw
    bid = row * 101 + brick_col
    tint_rng = np.random.default_rng(MASTER_SEED + 52)
    tint = tint_rng.random(8192)[bid % 8192]
    grain = fbm(18, 2, rng)
    mortar_mask = ((x + off) % bw < mortar) | (y % bh < mortar)
    if subtle:
        base = np.stack([0.61 + 0.08 * tint, 0.45 + 0.06 * tint, 0.34 + 0.05 * tint], axis=-1)
        mortar_col = np.array([0.51, 0.45, 0.38])
    else:
        base = np.stack([0.58 + 0.12 * tint, 0.34 + 0.07 * tint, 0.25 + 0.05 * tint], axis=-1)
        mortar_col = np.array([0.50, 0.44, 0.37])
    albedo = base * (0.97 + 0.030 * (grain - 0.5))[..., None]
    albedo = np.where(mortar_mask[..., None], mortar_col[None, None, :], albedo)
    height = np.where(mortar_mask, 0.42, 0.55 + 0.035 * grain + 0.020 * tint)
    rough = np.where(mortar_mask, 0.88, 0.81 + 0.045 * (1.0 - grain))
    return np.clip(albedo, 0, 1), np.clip(height, 0, 1), np.clip(rough, 0.62, 0.96)


def gen_concrete() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(MASTER_SEED + 60)
    mott = fbm(10, 3, rng)
    fine = fbm(24, 2, rng)
    base = 0.56 + 0.040 * (mott - 0.5) + 0.010 * (fine - 0.5)
    albedo = np.stack([base * 1.04, base * 1.02, base * 0.96], axis=-1)
    height = 0.50 + 0.030 * mott + 0.018 * fine
    rough = 0.82 + 0.040 * (1.0 - fine)
    return np.clip(albedo, 0, 1), np.clip(height, 0, 1), np.clip(rough, 0.62, 0.96)


def gen_roof() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(MASTER_SEED + 70)
    y, x = np.mgrid[0:SIZE, 0:SIZE]
    stripe = ((x // 96) % 2) * 0.025
    mott = fbm(10, 3, rng)
    v = 0.36 + stripe + 0.04 * (mott - 0.5)
    albedo = np.stack([v * 1.06, v * 1.03, v * 0.96], axis=-1)
    height = 0.50 + stripe + 0.05 * mott
    rough = 0.80 + 0.06 * (1.0 - mott)
    return np.clip(albedo, 0, 1), np.clip(height, 0, 1), np.clip(rough, 0.62, 0.94)


def gen_metal(zinc: bool = False) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    rng = np.random.default_rng(MASTER_SEED + (81 if zinc else 80))
    brushed = fbm(12, 2, rng)
    broad = fbm(5, 2, rng)
    v = (0.58 if zinc else 0.50) + 0.028 * (brushed - 0.5) + 0.030 * (broad - 0.5)
    if zinc:
        albedo = np.stack([v * 1.03, v * 1.04, v * 1.05], axis=-1)
        metallic = 0.55
    else:
        albedo = np.stack([v * 1.02, v * 1.00, v * 0.96], axis=-1)
        metallic = 0.35
    height = 0.50 + 0.020 * brushed
    rough = (0.50 if zinc else 0.60) + 0.035 * (1.0 - brushed)
    return np.clip(albedo, 0, 1), np.clip(height, 0, 1), np.clip(rough, 0.36, 0.76), metallic


def gen_wood() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(MASTER_SEED + 90)
    y, x = np.mgrid[0:SIZE, 0:SIZE]
    veins = 0.5 + 0.5 * np.sin((x / SIZE) * math.tau * 7.0 + fbm(5, 2, rng) * 1.5)
    fine = fbm(18, 2, rng)
    v = 0.42 + 0.11 * veins + 0.018 * (fine - 0.5)
    albedo = np.stack([v * 1.10, v * 0.74, v * 0.42], axis=-1)
    height = 0.50 + 0.060 * veins + 0.020 * fine
    rough = 0.72 + 0.045 * (1.0 - fine)
    return np.clip(albedo, 0, 1), np.clip(height, 0, 1), np.clip(rough, 0.54, 0.90)


def gen_dirt() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(MASTER_SEED + 100)
    mott = fbm(10, 3, rng)
    fine = fbm(24, 2, rng)
    base = 0.37 + 0.060 * mott + 0.012 * (fine - 0.5)
    albedo = np.stack([base * 1.30, base * 0.80, base * 0.48], axis=-1)
    height = 0.47 + 0.070 * mott + 0.025 * fine
    rough = 0.91 + 0.030 * (1.0 - fine)
    return np.clip(albedo, 0, 1), np.clip(height, 0, 1), np.clip(rough, 0.72, 1.0)


def facade_with_windows(kind: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    # Textura fallback do game_3d antigo: limpa, estilizada, sem sujeira pontilhada.
    if kind == "brick":
        wall, height, rough = gen_brick(subtle=True)
    else:
        wall, height, rough = gen_stucco()
    y, x = np.mgrid[0:SIZE, 0:SIZE]
    rows, cols = 4, 4
    cell_w, cell_h = SIZE / cols, SIZE / rows
    for r in range(rows):
        for c in range(cols):
            cx = (c + 0.5) * cell_w
            cy = (r + 0.40) * cell_h
            ww, wh = cell_w * 0.52, cell_h * 0.50
            frame = soft_rect_mask(x, y, cx - ww / 2 - 7, cx + ww / 2 + 7, cy - wh / 2 - 7, cy + wh / 2 + 7, 2.0)
            glass = soft_rect_mask(x, y, cx - ww / 2, cx + ww / 2, cy - wh / 2, cy + wh / 2, 2.0)
            frame_mask = frame > 0.5
            glass_mask = glass > 0.5
            wall = np.where(frame_mask[..., None], np.array([0.86, 0.84, 0.78])[None, None, :], wall)
            rel = np.clip((y - (cy - wh / 2)) / wh, 0, 1)
            glass_col = np.stack([0.24 - 0.10 * rel, 0.36 - 0.17 * rel, 0.46 - 0.24 * rel], axis=-1)
            sheen = np.abs((x - (cx - ww * 0.25)) - (y - (cy - wh * 0.35))) < 16
            glass_col = np.where(sheen[..., None], glass_col + np.array([0.10, 0.12, 0.12]), glass_col)
            wall = np.where(glass_mask[..., None], np.clip(glass_col, 0, 1), wall)
            sill = (np.abs(x - cx) < ww * 0.58) & (y > cy + wh / 2 + 8) & (y < cy + wh / 2 + 22)
            wall = np.where(sill[..., None], np.array([0.68, 0.64, 0.56])[None, None, :], wall)
            height = np.where(glass_mask, 0.30, height)
            height = np.where(frame_mask, 0.62, height)
            height = np.where(sill, 0.67, height)
            rough = np.where(glass_mask, 0.18, rough)
    return np.clip(wall, 0, 1), np.clip(height, 0, 1), np.clip(rough, 0.12, 0.96)


# ---------------------------------------------------------------------------
# Escrita por material
# ---------------------------------------------------------------------------

def write_root_triplet(name: str, albedo: np.ndarray, height: np.ndarray, rough: np.ndarray, normal_strength: float = 0.55) -> None:
    save_rgb(albedo * 255.0, OUT / f"{name}.png")
    save_rgb(height_to_normal(height, normal_strength), OUT / f"{name}_normal.png")
    save_rgb(rough * 255.0, OUT / f"{name}_roughness.png")


def write_pbr(prefix: str, albedo: np.ndarray, height: np.ndarray, rough: np.ndarray,
        normal_strength: float = 0.55, metallic: float = 0.0) -> None:
    save_rgb(albedo * 255.0, OUT_PBR / f"{prefix}_albedo.png")
    save_rgb(height_to_normal(height, normal_strength), OUT_PBR / f"{prefix}_normal.png")
    save_rgb(orm_map(np.clip(0.96 - (0.55 - height) * 0.10, 0.78, 1.0), rough, metallic) * 255.0,
            OUT_PBR / f"{prefix}_orm.png")
    save_height(height, OUT_PBR / f"{prefix}_height.png")


def main() -> None:
    asphalt, asphalt_h, asphalt_r = gen_asphalt()
    slabs, slabs_h, slabs_r = gen_large_slabs()
    mosaic, mosaic_h, mosaic_r = gen_mosaic(False)
    mosaic_wave, mosaic_wave_h, mosaic_wave_r = gen_mosaic(True)
    stucco, stucco_h, stucco_r = gen_stucco()
    brick, brick_h, brick_r = gen_brick(False)
    brick_soft, brick_soft_h, brick_soft_r = gen_brick(True)
    concrete, concrete_h, concrete_r = gen_concrete()
    roof, roof_h, roof_r = gen_roof()
    metal, metal_h, metal_r, metal_m = gen_metal(False)
    zinc, zinc_h, zinc_r, zinc_m = gen_metal(True)
    wood, wood_h, wood_r = gen_wood()
    dirt, dirt_h, dirt_r = gen_dirt()
    facade_plaster, facade_plaster_h, facade_plaster_r = facade_with_windows("plaster")
    facade_brick, facade_brick_h, facade_brick_r = facade_with_windows("brick")

    # Texturas runtime usadas por game_3d.gd. Asfalto/calçada têm nomes
    # legados sem o sufixo _realista nos mapas auxiliares.
    save_rgb(asphalt * 255.0, OUT / "asfalto_realista.png")
    save_rgb(height_to_normal(asphalt_h, 0.25), OUT / "asfalto_normal.png")
    save_rgb(asphalt_r * 255.0, OUT / "asfalto_roughness.png")
    save_rgb(mosaic_wave * 255.0, OUT / "calcada_realista.png")
    save_rgb(height_to_normal(mosaic_wave_h, 0.22), OUT / "calcada_normal.png")
    save_rgb(mosaic_wave_r * 255.0, OUT / "calcada_roughness.png")
    write_root_triplet("concreto_realista", concrete, concrete_h, concrete_r, 0.22)
    write_root_triplet("fachada_reboco", facade_plaster, facade_plaster_h, facade_plaster_r, 0.20)
    write_root_triplet("fachada_tijolo", facade_brick, facade_brick_h, facade_brick_r, 0.22)
    write_root_triplet("parede_tijolo_realista", brick_soft, brick_soft_h, brick_soft_r, 0.22)
    write_root_triplet("madeira_realista", wood, wood_h, wood_r, 0.24)
    write_root_triplet("metal_pintado_realista", metal, metal_h, metal_r, 0.16)
    write_root_triplet("terra_realista", dirt, dirt_h, dirt_r, 0.20)

    # PBR do BuildingKit.
    write_pbr("asfalto", asphalt, asphalt_h, asphalt_r, 0.25, 0.0)
    write_pbr("calcada_laje", slabs, slabs_h, slabs_r, 0.24, 0.0)
    write_pbr("calcada_mosaico", mosaic, mosaic_h, mosaic_r, 0.22, 0.0)
    write_pbr("reboco", stucco, stucco_h, stucco_r, 0.20, 0.0)
    write_pbr("tijolo", brick, brick_h, brick_r, 0.22, 0.0)
    write_pbr("laje_cobertura", roof, roof_h, roof_r, 0.18, 0.0)
    write_pbr("metal_pintado", metal, metal_h, metal_r, 0.16, metal_m)
    write_pbr("metal_zincado", zinc, zinc_h, zinc_r, 0.14, zinc_m)
    write_pbr("madeira", wood, wood_h, wood_r, 0.22, 0.0)
    write_pbr("terra_vermelha", dirt, dirt_h, dirt_r, 0.20, 0.0)


if __name__ == "__main__":
    main()
