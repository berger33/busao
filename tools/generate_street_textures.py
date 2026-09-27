#!/usr/bin/env python3
"""Regenera somente as texturas de rua/calçada com PBR mais realista.

Uso:
  python3 tools/generate_street_textures.py

Requer Pillow + NumPy. O gerador é determinístico, tileable e escreve:
- assets/textures/asfalto_realista + normal + roughness
- assets/textures/calcada_realista + normal + roughness
- assets/textures/pbr/asfalto_* / calcada_laje_* / calcada_mosaico_*

A ideia é trocar o visual procedural "nuvem cinza" por material de rua usado:
agregado fino, marcas de pneu, remendos sutis, óleo, sujeira de sarjeta,
juntas com AO e pedras com variação real.
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


def fbm(freq: int, octaves: int, rng: np.random.Generator, gain: float = 0.5, size: int = SIZE) -> np.ndarray:
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
    # OpenGL normal map (Y+); strength compensada pela resolução.
    norm_strength = strength * (1024.0 / float(height.shape[0]))
    dx = np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)
    dy = np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)
    nx = -dx * norm_strength * 64.0
    ny = -dy * norm_strength * 64.0
    nz = np.ones_like(height)
    l = np.sqrt(nx * nx + ny * ny + nz * nz)
    rgb = np.stack([nx / l * 0.5 + 0.5, ny / l * 0.5 + 0.5, nz / l * 0.5 + 0.5], axis=-1)
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
    img = Image.fromarray(np.clip(height * 65535.0, 0, 65535).astype(np.uint16), "I;16")
    img.save(path, optimize=True)
    print(f"  {path.relative_to(ROOT)} {img.size[0]}x{img.size[1]} 16-bit")


def random_walk_cracks(rng: np.random.Generator, count: int, steps: int, size: int = SIZE) -> np.ndarray:
    cracks = np.zeros((size, size), dtype=np.float64)
    for _ in range(count):
        x = float(rng.integers(0, size))
        y = float(rng.integers(0, size))
        angle = float(rng.random() * math.tau)
        for step in range(steps):
            angle += float((rng.random() - 0.5) * 0.44)
            speed = 1.15 + 0.8 * float(rng.random())
            x = (x + math.cos(angle) * speed) % size
            y = (y + math.sin(angle) * speed) % size
            xi, yi = int(x) % size, int(y) % size
            value = 1.0 - 0.45 * float(step) / float(max(steps, 1))
            cracks[yi, xi] = max(cracks[yi, xi], value)
            cracks[yi, (xi + 1) % size] = max(cracks[yi, (xi + 1) % size], value * 0.38)
            cracks[(yi + 1) % size, xi] = max(cracks[(yi + 1) % size, xi], value * 0.28)
            if rng.random() < 0.018:
                branch = angle + (rng.random() - 0.5) * 1.2
                bx, by = x, y
                for _branch_step in range(18):
                    bx = (bx + math.cos(branch) * 1.1) % size
                    by = (by + math.sin(branch) * 1.1) % size
                    bxi, byi = int(bx) % size, int(by) % size
                    cracks[byi, bxi] = max(cracks[byi, bxi], value * 0.35)
    for _ in range(2):
        cracks = np.maximum(cracks, np.roll(cracks, 1, 0) * 0.35)
        cracks = np.maximum(cracks, np.roll(cracks, -1, 1) * 0.25)
    return np.clip(cracks, 0.0, 1.0)


def asphalt_maps(seed_offset: int = 0) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(MASTER_SEED + 100 + seed_offset)
    y, x = np.mgrid[0:SIZE, 0:SIZE]
    xf = x / float(SIZE)

    macro = fbm(5, 4, rng, 0.54)
    mid = fbm(34, 4, rng, 0.50)
    aggregate = fbm(190, 3, rng, 0.52)
    grit = fbm(520, 2, rng, 0.45)
    tar_flow = fbm(11, 3, rng, 0.58)

    # Dois rastros de pneu longitudinais: visíveis, mas não pintados demais.
    lane_track = np.exp(-((xf - 0.34) ** 2) / 0.0022) + np.exp(-((xf - 0.68) ** 2) / 0.0024)
    lane_track = np.clip(lane_track, 0.0, 1.0) * (0.55 + 0.45 * fbm(9, 2, rng))

    # Remendos e áreas oleosas suavizadas; contraste baixo para fugir do "mapa de nuvens".
    repair_noise = fbm(7, 3, rng, 0.55)
    repair = repair_noise > 0.72
    oil = (fbm(13, 2, rng, 0.5) > 0.77) & (lane_track > 0.18)
    cracks = random_walk_cracks(rng, 7, 118)

    v = 0.235 + 0.060 * macro + 0.052 * mid + 0.050 * aggregate + 0.025 * grit
    v = v - 0.035 * lane_track - 0.030 * np.clip(tar_flow - 0.58, 0.0, 1.0)
    v = np.where(repair, v * 0.86 + 0.025, v)
    v = np.where(oil, v * 0.70, v)
    v = np.where(cracks > 0.03, v * (1.0 - 0.46 * cracks), v)

    # Pedrinhas: bege/cinza, sem pontos brancos estourados.
    pebble_mask = rng.random((SIZE, SIZE)) > 0.9952
    pebble_tone = rng.random((SIZE, SIZE))
    pebble_rgb = np.stack([
        0.42 + 0.20 * pebble_tone,
        0.40 + 0.18 * pebble_tone,
        0.36 + 0.14 * pebble_tone,
    ], axis=-1)

    albedo = np.stack([v * 0.94, v * 0.97, v], axis=-1)
    albedo = np.where(pebble_mask[..., None], pebble_rgb, albedo)
    albedo = np.clip(albedo, 0.035, 0.58)

    height = 0.43 + 0.23 * aggregate + 0.14 * grit + 0.13 * mid
    height = np.where(repair, height * 0.58 + 0.17, height)
    height = height - cracks * 0.24 - lane_track * 0.035
    height = np.where(pebble_mask, height + 0.18, height)
    height = np.clip(height, 0.0, 1.0)

    ao = 0.97 - 0.12 * np.clip(0.55 - mid, 0.0, 1.0) - 0.28 * cracks
    ao = np.where(oil, ao * 0.86, ao)
    ao = np.clip(ao + (aggregate - 0.5) * 0.035, 0.42, 1.0)

    rough = 0.86 + 0.08 * grit + 0.05 * aggregate
    rough = rough - 0.17 * lane_track - 0.22 * oil.astype(np.float64) - 0.10 * repair.astype(np.float64)
    rough = np.clip(rough, 0.46, 0.98)
    metallic = np.zeros((SIZE, SIZE), dtype=np.float64)
    orm = np.stack([ao, rough, metallic], axis=-1)
    return albedo, height, orm, rough


def slab_maps(seed_offset: int = 0) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(MASTER_SEED + 200 + seed_offset)
    y, x = np.mgrid[0:SIZE, 0:SIZE]
    slab_w, slab_h, mortar = 246, 184, 5
    row = y // slab_h
    off = (row % 2) * (slab_w // 2)
    col = (x + off) // slab_w
    bid = row * 83 + col
    tile_rng = np.random.default_rng(MASTER_SEED + 211)
    tint = tile_rng.random(8192)[bid % 8192]
    grain = fbm(128, 2, rng)
    pores = fbm(360, 2, rng)
    dirt = fbm(12, 3, rng)
    grout = ((x + off) % slab_w < mortar) | (y % slab_h < mortar)
    edge = ((x + off) % slab_w < mortar + 7) | (y % slab_h < mortar + 7)

    base = np.stack([
        0.61 + 0.10 * tint,
        0.59 + 0.095 * tint,
        0.54 + 0.075 * tint,
    ], axis=-1)
    albedo = base * (0.90 + 0.15 * grain + 0.08 * (dirt - 0.5))[..., None]
    albedo = np.where(grout[..., None], albedo * 0.46, albedo)
    albedo = np.where((edge & ~grout)[..., None], albedo * 0.86, albedo)

    gum = rng.random((SIZE, SIZE)) > 0.9992
    for _ in range(3):
        gum = gum | (np.roll(gum, 1, 0) & (rng.random((SIZE, SIZE)) > 0.45)) | (np.roll(gum, -1, 1) & (rng.random((SIZE, SIZE)) > 0.45))
    albedo = np.where(gum[..., None], albedo * 0.55 + np.array([0.05, 0.05, 0.045]), albedo)

    height = np.where(grout, 0.25, 0.57 + 0.12 * grain + 0.09 * pores + 0.05 * tint)
    height = np.where(edge & ~grout, height - 0.07, height)
    height = np.where(gum, height - 0.08, height)
    ao = np.where(grout, 0.58, 0.98 - 0.09 * edge.astype(np.float64) - 0.07 * np.clip(dirt - 0.62, 0, 1))
    rough = np.where(grout, 0.94, 0.82 + 0.10 * (1.0 - pores) - 0.05 * fbm(8, 2, rng))
    metallic = np.zeros((SIZE, SIZE), dtype=np.float64)
    orm = np.stack([np.clip(ao, 0.35, 1.0), np.clip(rough, 0.58, 1.0), metallic], axis=-1)
    return np.clip(albedo, 0, 1), np.clip(height, 0, 1), orm, rough


def mosaic_maps(seed_offset: int = 0, wave: bool = False) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(MASTER_SEED + 300 + seed_offset)
    y, x = np.mgrid[0:SIZE, 0:SIZE]
    stone = 28
    n = SIZE // stone + 2
    cell_y = y // stone
    cell_x = x // stone
    cell = cell_y * n + cell_x
    tile_rng = np.random.default_rng(MASTER_SEED + 311)
    tint = tile_rng.random(n * n + n)[cell % (n * n)]
    grain = fbm(160, 2, rng)
    dirt = fbm(10, 3, rng)
    grout = ((x % stone < 2) | (y % stone < 2))

    if wave:
        wave_center = 0.52 + 0.22 * np.sin(2.0 * math.pi * (x / float(SIZE)) + 0.8)
        dark = np.abs(y / float(SIZE) - wave_center) < 0.060
    else:
        # A faixa lateral nao deve virar um tabuleiro preto/branco. Mantem
        # algumas pedras mais escuras, mas com baixa incidencia e contraste.
        dark = tint < 0.055

    light_base = 0.58 + 0.10 * tint + 0.05 * (grain - 0.5)
    dark_base = 0.31 + 0.06 * tint + 0.035 * (grain - 0.5)
    base = np.where(dark, dark_base, light_base)
    albedo = np.stack([base * 1.03, base * 1.00, base * 0.94], axis=-1)
    albedo = albedo * (0.92 + 0.14 * dirt)[..., None]
    albedo = np.where(grout[..., None], albedo * 0.50, albedo)

    wear = fbm(7, 2, rng)
    albedo = np.where((~grout)[..., None], albedo * (0.96 + 0.08 * (wear[..., None] - 0.5)), albedo)
    height = np.where(grout, 0.23, 0.56 + 0.15 * grain + 0.05 * tint)
    ao = np.where(grout, 0.62, 0.97 - 0.08 * np.clip(dirt - 0.64, 0, 1))
    rough = np.where(grout, 0.95, 0.79 + 0.10 * (1.0 - grain) - 0.06 * wear)
    metallic = np.zeros((SIZE, SIZE), dtype=np.float64)
    orm = np.stack([np.clip(ao, 0.33, 1.0), np.clip(rough, 0.58, 1.0), metallic], axis=-1)
    return np.clip(albedo, 0, 1), np.clip(height, 0, 1), orm, rough


def write_asphalt() -> None:
    albedo, height, orm, rough = asphalt_maps(0)
    save_rgb(albedo * 255.0, OUT / "asfalto_realista.png")
    save_rgb(height_to_normal(height, 1.75), OUT / "asfalto_normal.png")
    save_rgb(rough * 255.0, OUT / "asfalto_roughness.png")
    save_rgb(albedo * 255.0, OUT_PBR / "asfalto_albedo.png")
    save_rgb(height_to_normal(height, 1.75), OUT_PBR / "asfalto_normal.png")
    save_rgb(orm * 255.0, OUT_PBR / "asfalto_orm.png")
    save_height(height, OUT_PBR / "asfalto_height.png")


def write_sidewalk() -> None:
    slab_albedo, slab_height, slab_orm, slab_rough = slab_maps(0)
    mos_albedo, mos_height, mos_orm, mos_rough = mosaic_maps(0, False)
    wave_albedo, wave_height, _wave_orm, wave_rough = mosaic_maps(7, True)

    save_rgb(wave_albedo * 255.0, OUT / "calcada_realista.png")
    save_rgb(height_to_normal(wave_height, 1.85), OUT / "calcada_normal.png")
    save_rgb(wave_rough * 255.0, OUT / "calcada_roughness.png")

    save_rgb(slab_albedo * 255.0, OUT_PBR / "calcada_laje_albedo.png")
    save_rgb(height_to_normal(slab_height, 1.65), OUT_PBR / "calcada_laje_normal.png")
    save_rgb(slab_orm * 255.0, OUT_PBR / "calcada_laje_orm.png")
    save_height(slab_height, OUT_PBR / "calcada_laje_height.png")

    save_rgb(mos_albedo * 255.0, OUT_PBR / "calcada_mosaico_albedo.png")
    save_rgb(height_to_normal(mos_height, 1.95), OUT_PBR / "calcada_mosaico_normal.png")
    save_rgb(mos_orm * 255.0, OUT_PBR / "calcada_mosaico_orm.png")
    save_height(mos_height, OUT_PBR / "calcada_mosaico_height.png")


def main() -> None:
    write_asphalt()
    write_sidewalk()


if __name__ == "__main__":
    main()
