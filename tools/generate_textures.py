#!/usr/bin/env python3
"""Gerador de texturas PBR do Corre pro Ponto.

Gera todas as texturas raster (albedo + normal + roughness) usadas pelo jogo,
de forma deterministica (semente fixa) e tileable. Rode:

    python3 tools/generate_textures.py

Requer: pillow, numpy. Todos os arquivos sao escritos em assets/textures/.
Normais seguem a convencao OpenGL (Y+ para cima), exigida pelo Godot 4.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "textures"
SIZE = 1024
SKY_W, SKY_H = 2048, 1024
MASTER_SEED = 20260918


# ----------------------------------------------------------------------------
# Ruido tileable e helpers
# ----------------------------------------------------------------------------

def value_noise(freq: int, rng: np.random.Generator) -> np.ndarray:
    """Grade de ruido (freq x freq) suavemente amostrada em SIZE x SIZE, tileable."""
    grid = rng.random((freq, freq))
    y, x = np.mgrid[0:SIZE, 0:SIZE]
    fx = x * freq / SIZE
    fy = y * freq / SIZE
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


def fbm(freq: int, octaves: int, rng: np.random.Generator, gain: float = 0.5) -> np.ndarray:
    """Fractal browniano tileable, normalizado em ~[0, 1]."""
    total = np.zeros((SIZE, SIZE))
    amp = 1.0
    acc = 0.0
    for _ in range(octaves):
        total += value_noise(freq, rng) * amp
        acc += amp
        amp *= gain
        freq *= 2
        if freq > SIZE:
            freq = SIZE
    total /= acc
    lo, hi = total.min(), total.max()
    if hi - lo > 1e-9:
        total = (total - lo) / (hi - lo)
    return total


def height_to_normal(height: np.ndarray, strength: float = 1.0) -> np.ndarray:
    """Converte altura em normal map OpenGL (azul = plano)."""
    dx = np.roll(height, -1, 1) - np.roll(height, 1, 1)
    dy = np.roll(height, -1, 0) - np.roll(height, 1, 0)
    nx = -dx * strength * 64.0
    ny = -dy * strength * 64.0
    nz = np.ones_like(height)
    length = np.sqrt(nx * nx + ny * ny + nz * nz)
    nx /= length
    ny /= length
    nz /= length
    rgb = np.stack([nx * 0.5 + 0.5, ny * 0.5 + 0.5, nz * 0.5 + 0.5], axis=-1)
    return np.clip(rgb * 255.0, 0, 255).astype(np.uint8)


def save(arr: np.ndarray, name: str) -> None:
    if arr.ndim == 2:
        arr = np.stack([arr] * 3, axis=-1)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")
    img.save(OUT / name, optimize=True)
    print(f"  {name} ({img.size[0]}x{img.size[1]})")


def rough_to_gray(rough: np.ndarray) -> np.ndarray:
    return np.clip(rough * 255.0, 0, 255)


# ----------------------------------------------------------------------------
# Asfalto
# ----------------------------------------------------------------------------

def gen_asphalt(rng: np.random.Generator) -> None:
    gravel = fbm(256, 3, rng)
    mid = fbm(48, 3, rng)
    patch = fbm(6, 3, rng)
    base = 0.30 + 0.34 * mid + 0.16 * (patch - 0.5)
    albedo = base * (0.72 + 0.55 * gravel)
    # pedrinhas claras espalhadas (areia/quentito)
    speck = rng.random((SIZE, SIZE))
    albedo = np.where(speck > 0.9975, albedo + 0.35, albedo)
    # rachaduras: caminhadas aleatorias escuras
    cracks = np.zeros((SIZE, SIZE))
    for _ in range(9):
        x = float(rng.integers(0, SIZE))
        y = float(rng.integers(0, SIZE))
        ang = rng.random() * math.tau
        for _step in range(150):
            ang += (rng.random() - 0.5) * 0.55
            x = (x + math.cos(ang) * 1.6) % SIZE
            y = (y + math.sin(ang) * 1.6) % SIZE
            xi, yi = int(x) % SIZE, int(y) % SIZE
            cracks[yi, xi] = 1.0
            cracks[yi, (xi + 1) % SIZE] = 0.6
    cracks = np.maximum(cracks, np.roll(cracks, 1, 0) * 0.5)
    albedo = np.where(cracks > 0.01, albedo * (1.0 - 0.55 * np.clip(cracks, 0, 1)), albedo)
    # manchas de remendo (asfalto novo, mais liso e escuro)
    repair = patch > 0.68
    albedo = np.where(repair, albedo * 0.72 + 0.04, albedo)
    height = gravel * 0.6 + mid * 0.4
    height = np.where(repair, height * 0.4 + 0.1, height)
    rough = 0.80 + 0.17 * gravel - 0.10 * repair.astype(float) + 0.05 * (mid - 0.5)
    save(albedo * 255.0, "asfalto_realista.png")
    save(height_to_normal(height, 1.35), "asfalto_normal.png")
    save(rough_to_gray(rough), "asfalto_roughness.png")


# ----------------------------------------------------------------------------
# Calcada portuguesa (padrao Copacabana: onda escura sobre pedra clara)
# ----------------------------------------------------------------------------

def gen_sidewalk(rng: np.random.Generator) -> None:
    stone = 64  # 16 x 16 pedras
    n = SIZE // stone
    y, x = np.mgrid[0:SIZE, 0:SIZE]
    cell = (y // stone) * n + (x // stone)
    rng_stone = np.random.default_rng(MASTER_SEED + 11)
    stone_tint = rng_stone.random(n * n)
    tint_map = stone_tint[cell]
    # onda: pedras escuras perto de uma senoide horizontal (1 ciclo por tile)
    cy = (np.arange(n) * stone + stone / 2.0)
    cx = (np.arange(n) * stone + stone / 2.0)
    wave_x = 512.0 + 265.0 * np.sin(2.0 * math.pi * cx / SIZE + 0.65)
    dark_col = np.zeros(n, dtype=bool)
    for j in range(n):
        if abs(cy[j] - wave_x).min() if False else False:
            dark_col[j] = True
    dark = np.zeros((n, n), dtype=bool)
    for i in range(n):
        for j in range(n):
            dark[j, i] = abs(cy[j] - wave_x[i]) < 105.0
    dark_map = dark[y // stone, x // stone]
    # grade de rejunte
    grout = ((x % stone < 3) | (y % stone < 3))
    grain = fbm(128, 2, rng)
    light = 0.80 + 0.14 * tint_map + 0.05 * (grain - 0.5)
    darkv = 0.16 + 0.10 * tint_map + 0.05 * (grain - 0.5)
    v = np.where(dark_map, darkv, light)
    v = np.where(grout, v * 0.55, v)
    # desgaste: areas mais lisas/polidas
    wear = fbm(8, 2, rng)
    v = v + 0.05 * (wear - 0.5)
    height = np.where(grout, 0.25, 0.75 + 0.12 * grain + 0.08 * (tint_map - 0.5))
    rough = np.where(dark_map, 0.74, 0.80) + 0.12 * (1.0 - grain) - 0.08 * wear
    save(np.stack([v, v, v * 0.995] , axis=-1) * 255.0, "calcada_realista.png")
    save(height_to_normal(height, 1.9), "calcada_normal.png")
    save(rough_to_gray(rough), "calcada_roughness.png")


# ----------------------------------------------------------------------------
# Fachadas com janelas (reboco e tijolo) — 4 andares x 4 janelas por tile
# ----------------------------------------------------------------------------

def _window_mask(x: np.ndarray, y: np.ndarray) -> dict:
    cols, rows = 4, 4
    cw, rh = SIZE / cols, SIZE / rows  # 256 px
    win_w, win_h = 0.62 * cw, 0.56 * rh
    masks = {}
    for r in range(rows):
        for c in range(cols):
            cx = (c + 0.5) * cw
            cy = (r + 0.38) * rh
            half_w, half_h = win_w / 2.0, win_h / 2.0
            dx = np.abs(x - cx)
            dy = np.abs(y - cy)
            glass = (dx < half_w - 7) & (dy < half_h - 7)
            frame = (dx < half_w) & (dy < half_h) & ~glass
            sill = (dx < half_w + 4) & (y > cy + half_h) & (y < cy + half_h + 9)
            ao = (dx < half_w + 26) & (y > cy + half_h + 9) & (y < cy + half_h + 42)
            masks[(r, c)] = {"glass": glass, "frame": frame, "sill": sill, "ao": ao, "cx": cx, "cy": cy}
    return masks


def gen_facade(rng: np.random.Generator, variant: str) -> None:
    y, x = np.mgrid[0:SIZE, 0:SIZE]
    masks = _window_mask(x, y)
    stain = fbm(16, 3, rng)
    grain = fbm(128, 2, rng)
    streak = fbm(64, 2, rng) * 0.5 + fbm(128, 2, rng) * 0.5

    if variant == "reboco":
        prefix = "fachada_reboco"
        base = np.array([0.78, 0.74, 0.67])
        albedo = base[None, None, :] * (0.92 + 0.13 * stain + 0.05 * (grain - 0.5))[..., None]
        rough_wall = 0.86 + 0.07 * grain
        height = 0.5 + 0.10 * grain + 0.05 * (stain - 0.5)
        frame_col = np.array([0.90, 0.89, 0.86])
    else:
        prefix = "fachada_tijolo"
        base = None
        bw, bh, mortar = 128, 34, 5
        row = y // bh
        off = (row % 2) * (bw // 2)
        bid = row * 97 + ((x + off) // bw)
        rng_brick = np.random.default_rng(MASTER_SEED + (31 if variant == "tijolo" else 33))
        btint = rng_brick.random(4096)
        bt = btint[bid % 4096]
        brick_r = 0.62 + 0.22 * bt
        brick_g = (0.30 + 0.14 * bt) * (0.9 + 0.2 * grain)
        brick_b = (0.24 + 0.10 * bt) * (0.9 + 0.2 * grain)
        albedo = np.stack([brick_r, brick_g, brick_b], axis=-1)
        is_mortar = ((x + off) % bw < mortar) | (y % bh < mortar)
        albedo = np.where(is_mortar[..., None], np.array([0.72, 0.70, 0.66])[None, None, :], albedo)
        albedo = albedo * (0.88 + 0.18 * stain)[..., None]
        rough_wall = np.where(is_mortar, 0.94, 0.88 + 0.08 * grain)
        height = np.where(is_mortar, 0.42, 0.58 + 0.08 * grain + 0.06 * bt)
        frame_col = np.array([0.88, 0.89, 0.84])

    glass_col = np.array([0.10, 0.15, 0.21])
    glass = np.zeros((SIZE, SIZE, 3))
    glass[:] = glass_col[None, None, :]
    rough = rough_wall.copy()

    for key, m in masks.items():
        rng_w = np.random.default_rng(MASTER_SEED + 101 + key[0] * 4 + key[1])
        # vidro com gradiente vertical (reflexo do ceu em cima)
        local = np.zeros((SIZE, SIZE, 3))
        rel_y = (y - (m["cy"] - 0.28 * SIZE / 4)) / (0.56 * SIZE / 4)
        top = np.array([0.30, 0.42, 0.52])
        bot = np.array([0.05, 0.08, 0.13])
        for ch in range(3):
            local[..., ch] = top[ch] * (1.0 - np.clip(rel_y, 0, 1)) + bot[ch] * np.clip(rel_y, 0, 1)
        if rng_w.random() < 0.45:  # cortina
            local = local * 0.6 + np.array([0.42, 0.40, 0.34])[None, None, :] * 0.6
        glass = np.where(m["glass"][..., None], local, glass)
        # brilho diagonal sutil no vidro
        sheen = (np.abs(x - y) % 256) < 26
        glass = np.where((m["glass"] & sheen)[..., None], glass * 1.25, glass)
        albedo = np.where(m["frame"][..., None], frame_col[None, None, :] * 0.94, albedo)
        albedo = np.where(m["sill"][..., None], np.array([0.82, 0.80, 0.76])[None, None, :], albedo)
        # AO sob a peitoril + escorridos de sujeira
        ao_m = m["ao"]
        albedo = np.where(ao_m[..., None], albedo * 0.82, albedo)
        streak_m = ao_m & (streak > 0.62)
        albedo = np.where(streak_m[..., None], albedo * 0.70, albedo)
        height = np.where(m["glass"], 0.22, height)
        height = np.where(m["frame"], 0.55, height)
        height = np.where(m["sill"], 0.70, height)
        rough[m["glass"]] = 0.14
        rough[m["frame"]] = 0.48
        rough[m["sill"]] = 0.70
    # vidro entra por cima de tudo
    for key, m in masks.items():
        albedo = np.where(m["glass"][..., None], glass, albedo)

    save(albedo * 255.0, f"{prefix}.png")
    save(height_to_normal(height, 1.7), f"{prefix}_normal.png")
    save(rough_to_gray(rough), f"{prefix}_roughness.png")


# ----------------------------------------------------------------------------
# Parede de tijolo aparente (sem janelas)
# ----------------------------------------------------------------------------

def gen_brick_wall(rng: np.random.Generator) -> None:
    y, x = np.mgrid[0:SIZE, 0:SIZE]
    bw, bh, mortar = 86, 36, 6
    row = y // bh
    off = (row % 2) * (bw // 2)
    bid = row * 131 + ((x + off) // bw)
    rng_b = np.random.default_rng(MASTER_SEED + 47)
    bt = rng_b.random(8192)[bid % 8192]
    grain = fbm(128, 2, rng)
    soot = fbm(8, 3, rng)
    r = 0.55 + 0.25 * bt
    g = (0.26 + 0.12 * bt) * (0.9 + 0.2 * grain)
    b = (0.20 + 0.09 * bt) * (0.9 + 0.2 * grain)
    albedo = np.stack([r, g, b], axis=-1) * (0.86 + 0.2 * soot)[..., None]
    is_mortar = ((x + off) % bw < mortar) | (y % bh < mortar)
    albedo = np.where(is_mortar[..., None], np.array([0.66, 0.64, 0.60])[None, None, :] * (0.9 + 0.2 * soot[..., None]), albedo)
    height = np.where(is_mortar, 0.40, 0.58 + 0.09 * grain + 0.06 * bt)
    rough = np.where(is_mortar, 0.95, 0.90 + 0.07 * grain)
    save(albedo * 255.0, "parede_tijolo_realista.png")
    save(height_to_normal(height, 1.6), "parede_tijolo_realista_normal.png")
    save(rough_to_gray(rough), "parede_tijolo_realista_roughness.png")


# ----------------------------------------------------------------------------
# Pintura automotiva ( flakes metalicos )
# ----------------------------------------------------------------------------

def gen_car_paint(rng: np.random.Generator) -> None:
    flake = rng.random((SIZE, SIZE))
    flake = np.where(flake > 0.986, 1.0, 0.42 + 0.18 * fbm(64, 2, rng))
    waves = fbm(8, 2, rng)
    albedo = 0.86 + 0.10 * (flake - 0.5) + 0.05 * (waves - 0.5)
    save(np.stack([albedo, albedo * 0.995, albedo * 0.99], axis=-1) * 255.0, "pintura_carro_realista.png")
    height = flake * 0.22 + waves * 0.78
    save(height_to_normal(height, 0.35), "pintura_carro_normal.png")


# ----------------------------------------------------------------------------
# Cabelo e jeans (reprodutiveis)
# ----------------------------------------------------------------------------

def gen_hair(rng: np.random.Generator) -> None:
    strand = fbm(96, 2, rng)
    along = fbm(12, 2, rng)
    v = 0.10 + 0.30 * strand * 0.7 + 0.18 * along
    v = np.clip(v, 0.05, 0.55)
    save(np.stack([v * 1.06, v * 0.78, v * 0.55], axis=-1) * 255.0, "cabelo_realista.png")


def gen_denim(rng: np.random.Generator) -> None:
    y, x = np.mgrid[0:SIZE, 0:SIZE]
    twill = ((x + y) % 8) < 4
    noise = fbm(96, 2, rng)
    base = np.where(twill, 0.30, 0.22) + 0.16 * noise
    save(np.stack([base * 0.82, base * 1.0, base * 1.55, ] , axis=-1) * 255.0, "jeans_realista.png")


# ----------------------------------------------------------------------------
# Folhagem (copa de arvore)
# ----------------------------------------------------------------------------

def gen_leaves(rng: np.random.Generator) -> None:
    clump = fbm(48, 3, rng)
    leaf = fbm(256, 2, rng)
    gap = clump < 0.34
    g_dark = np.array([0.13, 0.34, 0.12])
    g_lit = np.array([0.33, 0.57, 0.19])
    t = np.clip(clump * 0.6 + leaf * 0.5 - 0.05, 0, 1)
    albedo = g_dark[None, None, :] * (1 - t[..., None]) + g_lit[None, None, :] * t[..., None]
    albedo = np.where(gap[..., None], albedo * 0.35, albedo)
    height = clump * 0.55 + leaf * 0.45
    height = np.where(gap, height * 0.3, height)
    rough = 0.52 + 0.30 * (1.0 - leaf)
    save(albedo * 255.0, "folhagem_realista.png")
    save(height_to_normal(height, 1.0), "folhagem_realista_normal.png")
    save(rough_to_gray(rough), "folhagem_realista_roughness.png")


# ----------------------------------------------------------------------------
# Madeira (veios verticais + nos)
# ----------------------------------------------------------------------------

def gen_wood(rng: np.random.Generator) -> None:
    src = fbm(24, 2, rng)
    smear = np.zeros((SIZE, SIZE))
    for k in range(16):
        smear += np.roll(src, k * (SIZE // 16), axis=0)
    smear /= 16.0
    # estica o contraste dos veios (a media do smear achata a variacao)
    smear = np.clip((smear - smear.mean()) * 3.2 + 0.5, 0.0, 1.0)
    fine = fbm(128, 2, rng)
    grain = np.clip(smear * 0.75 + fine * 0.35, 0.0, 1.0)
    yy, xx = np.mgrid[0:SIZE, 0:SIZE]
    knots = np.zeros((SIZE, SIZE))
    for _ in range(3):
        kx = float(rng.integers(120, SIZE - 120))
        ky = float(rng.integers(120, SIZE - 120))
        dx = np.minimum(np.abs(xx - kx), SIZE - np.abs(xx - kx))
        dy = np.minimum(np.abs(yy - ky), SIZE - np.abs(yy - ky))
        d = np.sqrt(dx * dx + dy * dy) * (1.6 + rng.random() * 0.6)
        rings = 0.5 + 0.5 * np.sin(d * 1.4)
        knots = np.maximum(knots, np.where(d < 90.0, rings * np.exp(-d / 60.0), 0.0))
    grain = np.clip(grain - knots * 0.55, 0, 1)
    base = np.array([0.46, 0.30, 0.17])
    shade = 0.55 + 0.90 * grain
    albedo = base[None, None, :] * shade[..., None]
    albedo = np.where((knots > 0.15)[..., None], albedo * 0.75, albedo)
    height = 0.5 + (grain - 0.5) * 0.5 - knots * 0.2
    rough = 0.72 + 0.18 * (1.0 - grain)
    save(albedo * 255.0, "madeira_realista.png")
    save(height_to_normal(height, 0.6), "madeira_realista_normal.png")
    save(rough_to_gray(rough), "madeira_realista_roughness.png")


# ----------------------------------------------------------------------------
# Metal pintado (riscos, lascas e po)
# ----------------------------------------------------------------------------

def gen_painted_metal(rng: np.random.Generator) -> None:
    wear = fbm(16, 3, rng)
    albedo = np.full((SIZE, SIZE, 3), 0.84)
    rough = 0.38 + 0.10 * wear
    height = np.full((SIZE, SIZE), 0.5)
    for _ in range(46):  # riscos finos de uso
        x = float(rng.integers(0, SIZE))
        y = float(rng.integers(0, SIZE))
        ang = rng.random() * math.tau
        for _step in range(60):
            ang += (rng.random() - 0.5) * 0.4
            x = (x + math.cos(ang) * 2.0) % SIZE
            y = (y + math.sin(ang) * 2.0) % SIZE
            xi, yi = int(x) % SIZE, int(y) % SIZE
            albedo[yi, xi] = 0.70
            rough[yi, xi] = 0.55
            height[yi, xi] = 0.46
    yy, xx = np.mgrid[0:SIZE, 0:SIZE]
    for _ in range(26):  # lascas expondo o metal
        cx = float(rng.integers(0, SIZE))
        cy = float(rng.integers(0, SIZE))
        r = 2.0 + rng.random() * 5.0
        dx = np.minimum(np.abs(xx - cx), SIZE - np.abs(xx - cx))
        dy = np.minimum(np.abs(yy - cy), SIZE - np.abs(yy - cy))
        chip = (dx * dx + dy * dy) < r * r
        albedo = np.where(chip[..., None], np.array([0.42, 0.44, 0.47])[None, None, :], albedo)
        rough = np.where(chip, 0.72, rough)
        height = np.where(chip, 0.36, height)
    albedo = albedo * (0.95 + 0.08 * wear)[..., None]
    save(albedo * 255.0, "metal_pintado_realista.png")
    save(height_to_normal(height, 0.5), "metal_pintado_realista_normal.png")
    save(rough_to_gray(rough), "metal_pintado_realista_roughness.png")


# ----------------------------------------------------------------------------
# Concreto (motas, poros, manchas e juntas de forma)
# ----------------------------------------------------------------------------

def gen_concrete(rng: np.random.Generator) -> None:
    mottle = fbm(16, 3, rng)
    fine = fbm(96, 2, rng)
    stain = fbm(6, 2, rng)
    base = 0.60 + 0.14 * mottle + 0.06 * fine - 0.10 * np.clip(stain - 0.6, 0, 1)
    speck = rng.random((SIZE, SIZE))
    base = np.where(speck > 0.9955, base - 0.22, base)
    yy, xx = np.mgrid[0:SIZE, 0:SIZE]
    seam = (yy % 256) < 2
    base = np.where(seam, base * 0.9, base)
    albedo = np.stack([base, base * 0.995, base * 0.985], axis=-1)
    height = 0.5 + (mottle - 0.5) * 0.25 + (fine - 0.5) * 0.2
    height = np.where(speck > 0.9955, height - 0.25, height)
    height = np.where(seam, height - 0.15, height)
    rough = 0.87 + 0.07 * fine - 0.05 * (stain - 0.5)
    save(albedo * 255.0, "concreto_realista.png")
    save(height_to_normal(height, 0.7), "concreto_realista_normal.png")
    save(rough_to_gray(rough), "concreto_realista_roughness.png")


# ----------------------------------------------------------------------------
# Terra vermelha (granular + pedrinhas)
# ----------------------------------------------------------------------------

def gen_dirt(rng: np.random.Generator) -> None:
    grain = fbm(192, 3, rng)
    patch = fbm(8, 2, rng)
    base = np.array([0.52, 0.30, 0.17])
    shade = 0.65 + 0.60 * grain + 0.18 * (patch - 0.5)
    albedo = base[None, None, :] * shade[..., None]
    yy, xx = np.mgrid[0:SIZE, 0:SIZE]
    height = 0.45 + grain * 0.4 + (patch - 0.5) * 0.2
    rough = np.full((SIZE, SIZE), 0.95)
    for _ in range(260):
        cx = float(rng.integers(0, SIZE))
        cy = float(rng.integers(0, SIZE))
        r = 1.5 + rng.random() * 3.5
        dx = np.minimum(np.abs(xx - cx), SIZE - np.abs(xx - cx))
        dy = np.minimum(np.abs(yy - cy), SIZE - np.abs(yy - cy))
        peb = (dx * dx + dy * dy) < r * r
        stone = np.array([0.62, 0.50, 0.38]) if rng.random() < 0.7 else np.array([0.55, 0.55, 0.55])
        albedo = np.where(peb[..., None], stone[None, None, :] * (0.85 + 0.3 * rng.random()), albedo)
        height = np.where(peb, height + 0.3, height)
        rough = np.where(peb, 0.80, rough)
    save(albedo * 255.0, "terra_realista.png")
    save(height_to_normal(height, 1.1), "terra_realista_normal.png")
    save(rough_to_gray(rough), "terra_realista_roughness.png")


# ----------------------------------------------------------------------------
# Tecido tramado (toldos e roupas de varal)
# ----------------------------------------------------------------------------

def gen_fabric(rng: np.random.Generator) -> None:
    block = 8
    yy, xx = np.mgrid[0:SIZE, 0:SIZE]
    over = (((xx // block) + (yy // block)) % 2) == 0
    fine = fbm(128, 2, rng)
    base = np.where(over, 0.88, 0.78) + 0.08 * (fine - 0.5)
    diag = ((xx + yy) % (block * 2)) < 3
    base = np.where(diag & over, base + 0.05, base)
    albedo = np.stack([base, base * 0.995, base * 0.99], axis=-1)
    height = np.where(over, 0.62, 0.42) + fine * 0.08
    rough = 0.84 + 0.10 * (1.0 - fine)
    save(albedo * 255.0, "tecido_realista.png")
    save(height_to_normal(height, 0.9), "tecido_realista_normal.png")
    save(rough_to_gray(rough), "tecido_realista_roughness.png")


# ----------------------------------------------------------------------------
# Borracha (pneus)
# ----------------------------------------------------------------------------

def gen_rubber(rng: np.random.Generator) -> None:
    grain = fbm(160, 2, rng)
    wear = fbm(24, 2, rng)
    base = 0.09 + 0.05 * grain + 0.03 * wear
    albedo = np.stack([base, base, base * 1.05], axis=-1)
    height = 0.5 + (grain - 0.5) * 0.4
    rough = 0.62 + 0.14 * (1.0 - grain) + 0.06 * wear
    save(albedo * 255.0, "borracha_realista.png")
    save(height_to_normal(height, 0.45), "borracha_realista_normal.png")
    save(rough_to_gray(rough), "borracha_realista_roughness.png")


# ----------------------------------------------------------------------------
# Ceus equiretangulares (2048 x 1024)
# ----------------------------------------------------------------------------

def _sky_base() -> tuple[np.ndarray, np.ndarray]:
    yy, xx = np.mgrid[0:SKY_H, 0:SKY_W]
    u = xx / SKY_W  # 0..1 longitude
    v = yy / SKY_H  # 0 topo .. 1 base
    lat = (0.5 - v) * math.pi  # +pi/2 topo
    return u, lat


def _fbm_sky(freq: int, octaves: int, rng: np.random.Generator, warp: np.ndarray | None = None) -> np.ndarray:
    total = np.zeros((SKY_H, SKY_W))
    amp = 1.0
    acc = 0.0
    y2, x2 = np.mgrid[0:SKY_H, 0:SKY_W]
    for _ in range(octaves):
        grid = rng.random((freq, freq * 2))
        fx = x2 * (freq * 2) / SKY_W
        fy = y2 * freq / SKY_H
        x0 = np.floor(fx).astype(np.int64) % (freq * 2)
        y0 = np.floor(fy).astype(np.int64) % freq
        x1 = (x0 + 1) % (freq * 2)
        y1 = (y0 + 1) % freq
        tx = 0.5 - 0.5 * np.cos((fx - np.floor(fx)) * math.pi)
        ty = 0.5 - 0.5 * np.cos((fy - np.floor(fy)) * math.pi)
        a = grid[y0, x0] * (1 - tx) + grid[y0, x1] * tx
        b = grid[y1, x0] * (1 - tx) + grid[y1, x1] * tx
        total += (a * (1 - ty) + b * ty) * amp
        acc += amp
        amp *= 0.55
        freq *= 2
        if freq > SKY_H:
            break
    total /= acc
    lo, hi = total.min(), total.max()
    if hi - lo > 1e-9:
        total = (total - lo) / (hi - lo)
    if warp is not None:
        total = np.clip(total + warp * 0.25, 0, 1)
    return total


def gen_sky(kind: str, rng: np.random.Generator) -> None:
    u, lat = _sky_base()
    above = lat > 0
    t = np.clip(lat / (math.pi / 2), 0, 1)  # 0 horizonte, 1 zenite

    if kind == "tropical":
        zenith = np.array([0.16, 0.38, 0.74])
        horizon = np.array([0.66, 0.80, 0.90])
        ground = np.array([0.36, 0.38, 0.39])
        cloud_cover, cloud_soft, sun_lat = 0.34, 0.30, 0.62
        sun_col = np.array([1.0, 0.96, 0.86])
        glow = np.array([1.0, 0.90, 0.70])
    elif kind == "entardecer":
        zenith = np.array([0.14, 0.15, 0.32])
        horizon = np.array([0.98, 0.62, 0.30])
        ground = np.array([0.22, 0.17, 0.18])
        cloud_cover, cloud_soft, sun_lat = 0.40, 0.36, 0.18
        sun_col = np.array([1.0, 0.88, 0.62])
        glow = np.array([1.0, 0.72, 0.42])
    else:  # nublado
        zenith = np.array([0.42, 0.47, 0.53])
        horizon = np.array([0.72, 0.75, 0.78])
        ground = np.array([0.34, 0.35, 0.36])
        cloud_cover, cloud_soft, sun_lat = 0.62, 0.5, None
        sun_col = np.array([0.9, 0.9, 0.9])
        glow = None

    img = np.zeros((SKY_H, SKY_W, 3))
    for ch in range(3):
        sky = horizon[ch] * (1 - t) ** 0.55 + zenith[ch] * (1 - (1 - t) ** 0.55)
        gnd = ground[ch] * (0.55 + 0.45 * np.clip(-lat / (math.pi / 2), 0, 1))
        img[..., ch] = np.where(above, sky, gnd)

    # nuvens: fbm com bandas mais densas perto do horizonte
    band = np.exp(-(np.abs(lat) / 0.55) ** 2)
    cl = _fbm_sky(6, 5, rng)
    cl = np.clip((cl - 0.5) * 2.6 + 0.5, 0.0, 1.0)  # estica a distribuicao concentrada do fbm
    cl = cl * (0.45 + 0.75 * band)
    threshold = 1.0 - 1.35 * cloud_cover
    cloud = np.clip((cl - threshold) / max(cloud_soft, 1e-3), 0, 1)
    cloud = cloud * np.clip(above.astype(float) * (1.02 - t * 0.55), 0, 1)
    shade = 0.72 + 0.28 * cl
    for ch in range(3):
        ccol = (0.94 * shade if kind != "entardecer" else np.array([1.0, 0.80, 0.66])[ch] * shade)
        img[..., ch] = img[..., ch] * (1 - cloud) + ccol * cloud

    if sun_lat is not None:
        sun_u = 0.62
        sun_lon = (u - sun_u + 0.5) % 1.0 - 0.5  # -0.5..0.5 relativo
        d2 = (sun_lon * 2.0 * math.pi * 0.42) ** 2 + (lat - sun_lat) ** 2
        disk = np.exp(-d2 / (2 * 0.0016))
        halo = np.exp(-d2 / (2 * 0.045))
        for ch in range(3):
            img[..., ch] += sun_col[ch] * disk * 1.1
            if glow is not None:
                img[..., ch] += glow[ch] * halo * 0.30

    save(img * 255.0, f"ceu_{kind}.png")


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"Gerando texturas PBR em {OUT} (semente {MASTER_SEED})")
    gen_asphalt(np.random.default_rng(MASTER_SEED + 1))
    gen_sidewalk(np.random.default_rng(MASTER_SEED + 2))
    gen_facade(np.random.default_rng(MASTER_SEED + 3), "reboco")
    gen_facade(np.random.default_rng(MASTER_SEED + 4), "tijolo")
    gen_brick_wall(np.random.default_rng(MASTER_SEED + 5))
    gen_car_paint(np.random.default_rng(MASTER_SEED + 6))
    gen_hair(np.random.default_rng(MASTER_SEED + 7))
    gen_denim(np.random.default_rng(MASTER_SEED + 8))
    gen_leaves(np.random.default_rng(MASTER_SEED + 9))
    gen_wood(np.random.default_rng(MASTER_SEED + 12))
    gen_painted_metal(np.random.default_rng(MASTER_SEED + 13))
    gen_concrete(np.random.default_rng(MASTER_SEED + 14))
    gen_dirt(np.random.default_rng(MASTER_SEED + 15))
    gen_fabric(np.random.default_rng(MASTER_SEED + 16))
    gen_rubber(np.random.default_rng(MASTER_SEED + 17))
    for kind in ["tropical", "entardecer", "nublado"]:
        gen_sky(kind, np.random.default_rng(MASTER_SEED + 20 + ["tropical", "entardecer", "nublado"].index(kind)))
    print("OK: texturas regeneradas.")


if __name__ == "__main__":
    main()
