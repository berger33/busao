#!/usr/bin/env python3
"""Gera o pacote visual estilizado do ambiente sem dependências externas.

Objetivo: polimento visual de soft-launch. As texturas anteriores que tentavam
simular sujeira fotográfica podiam virar pontilhado preto/pixelado no mobile.
Este gerador usa apenas formas amplas, paleta quente e variação suave/tileable:
rua e prédios ficam coesos, bonitos e legíveis, sem afetar personagem/árvores.

Não depende de Pillow/Numpy; escreve PNG RGB 8-bit com a biblioteca padrão.
"""
from __future__ import annotations

import math
import os
import struct
import zlib
from pathlib import Path
from typing import Callable, Tuple

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "textures"
OUT_PBR = OUT / "pbr"
SIZE = int(os.environ.get("PBR_SIZE", "1024"))
if SIZE not in (512, 1024, 2048):
    SIZE = 1024
MASTER_SEED = 20260927
TAU = math.tau
RGB = Tuple[int, int, int]


def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return lo if v < lo else hi if v > hi else v


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    if edge0 == edge1:
        return 0.0
    t = clamp((x - edge0) / (edge1 - edge0))
    return t * t * (3.0 - 2.0 * t)


def mix_color(a: tuple[float, float, float], b: tuple[float, float, float], t: float) -> tuple[float, float, float]:
    return (lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t))


def to_rgb(c: tuple[float, float, float]) -> RGB:
    return (
        int(clamp(c[0]) * 255.0 + 0.5),
        int(clamp(c[1]) * 255.0 + 0.5),
        int(clamp(c[2]) * 255.0 + 0.5),
    )


def hash01(ix: int, iy: int = 0, seed: int = MASTER_SEED) -> float:
    n = (ix * 374761393 + iy * 668265263 + seed * 1442695041) & 0xFFFFFFFF
    n ^= (n >> 13)
    n = (n * 1274126177) & 0xFFFFFFFF
    n ^= (n >> 16)
    return n / 4294967295.0


def wave_noise(x: int, y: int, seed: int, scale: float = 1.0) -> float:
    u = x / float(SIZE)
    v = y / float(SIZE)
    a = math.sin(TAU * (u * (1.4 + 0.2 * (seed % 3)) + v * 0.55 + seed * 0.017))
    b = math.sin(TAU * (u * 0.45 - v * (1.2 + 0.1 * (seed % 5)) + seed * 0.031))
    c = math.sin(TAU * (u * 2.2 + v * 1.7 + seed * 0.011))
    return (a * 0.50 + b * 0.32 + c * 0.18) * scale


def cell_tint(x: int, y: int, cell_w: int, cell_h: int, seed: int, stagger: bool = False) -> float:
    row = y // max(1, cell_h)
    off = (cell_w // 2) if (stagger and row % 2) else 0
    col = (x + off) // max(1, cell_w)
    return hash01(col, row, seed)


def png_chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def write_png_rgb(path: Path, pixel: Callable[[int, int], RGB]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = bytearray()
    for y in range(SIZE):
        raw.append(0)  # filter: none
        row = bytearray()
        for x in range(SIZE):
            row.extend(pixel(x, y))
        raw.extend(row)
    data = b"\x89PNG\r\n\x1a\n"
    data += png_chunk(b"IHDR", struct.pack(">IIBBBBB", SIZE, SIZE, 8, 2, 0, 0, 0))
    data += png_chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    data += png_chunk(b"IEND", b"")
    path.write_bytes(data)
    print(f"  {path.relative_to(ROOT)} {SIZE}x{SIZE}")


def write_png_gray(path: Path, value: Callable[[int, int], float]) -> None:
    write_png_rgb(path, lambda x, y: (lambda g: (g, g, g))(int(clamp(value(x, y)) * 255.0 + 0.5)))


def write_normal(path: Path, height: Callable[[int, int], float], strength: float = 1.0) -> None:
    def px(x: int, y: int) -> RGB:
        xm, xp = (x - 1) % SIZE, (x + 1) % SIZE
        ym, yp = (y - 1) % SIZE, (y + 1) % SIZE
        dx = (height(xp, y) - height(xm, y)) * strength
        dy = (height(x, yp) - height(x, ym)) * strength
        nx = -dx * 4.0
        ny = -dy * 4.0
        nz = 1.0
        inv = 1.0 / math.sqrt(nx * nx + ny * ny + nz * nz)
        return (
            int((nx * inv * 0.5 + 0.5) * 255.0 + 0.5),
            int((ny * inv * 0.5 + 0.5) * 255.0 + 0.5),
            int((nz * inv * 0.5 + 0.5) * 255.0 + 0.5),
        )
    write_png_rgb(path, px)


def write_orm(path: Path, rough: Callable[[int, int], float], metallic: float = 0.0) -> None:
    def px(x: int, y: int) -> RGB:
        r = rough(x, y)
        ao = clamp(0.94 + (0.70 - r) * 0.08, 0.80, 1.0)
        return (int(ao * 255 + 0.5), int(clamp(r) * 255 + 0.5), int(clamp(metallic) * 255 + 0.5))
    write_png_rgb(path, px)


# ---------------------------------------------------------------------------
# Materiais de rua e arquitetura — funções tileable/estilizadas
# ---------------------------------------------------------------------------

def asphalt_h(x: int, y: int) -> float:
    u = x / SIZE
    v = y / SIZE
    lane = math.exp(-((u - 0.34) ** 2) / 0.005) + math.exp(-((u - 0.67) ** 2) / 0.005)
    broad = wave_noise(x, y, 11, 1.0)
    sweep = math.sin(TAU * (u * 3.0 + v * 0.7 + 0.18)) * 0.35
    # Variação contínua, sem manchas quadradas/células e sem speckles.
    return clamp(0.50 + 0.024 * broad + 0.006 * sweep - 0.022 * lane, 0.40, 0.60)


def asphalt_albedo(x: int, y: int) -> RGB:
    h = asphalt_h(x, y)
    u = x / SIZE
    lane = math.exp(-((u - 0.34) ** 2) / 0.004) + math.exp(-((u - 0.67) ** 2) / 0.004)
    v = 0.305 + (h - 0.50) * 0.55 - lane * 0.012
    c = (v * 0.93, v * 0.98, v * 1.05)
    return to_rgb(c)


def asphalt_rough(x: int, y: int) -> float:
    return clamp(0.83 + (0.50 - asphalt_h(x, y)) * 0.20, 0.72, 0.93)


def mosaic_h(x: int, y: int, wave: bool = True) -> float:
    stone = max(32, SIZE // 16)
    grout = max(2, SIZE // 220)
    in_grout = (x % stone < grout) or (y % stone < grout)
    t = cell_tint(x, y, stone, stone, 21)
    if wave:
        center = 0.52 + 0.20 * math.sin(TAU * x / SIZE + 0.7)
        accent = clamp(1.0 - abs(y / SIZE - center) / 0.075)
    else:
        accent = 0.0
    return 0.38 if in_grout else clamp(0.54 + 0.030 * (t - 0.5) - 0.025 * accent, 0.45, 0.62)


def mosaic_albedo(x: int, y: int, wave: bool = True) -> RGB:
    stone = max(32, SIZE // 16)
    grout = max(2, SIZE // 220)
    in_grout = (x % stone < grout) or (y % stone < grout)
    t = cell_tint(x, y, stone, stone, 22)
    center = 0.52 + 0.20 * math.sin(TAU * x / SIZE + 0.7)
    accent = clamp(1.0 - abs(y / SIZE - center) / 0.075) if wave else 0.0
    base = mix_color((0.66, 0.64, 0.57), (0.77, 0.74, 0.66), t * 0.75)
    accent_col = mix_color(base, (0.50, 0.48, 0.42), accent * 0.58)
    c = (0.45, 0.43, 0.38) if in_grout else accent_col
    return to_rgb(c)


def mosaic_rough(x: int, y: int) -> float:
    return 0.88 if mosaic_h(x, y) < 0.40 else 0.80


def slab_h(x: int, y: int) -> float:
    w, h, grout = max(96, SIZE // 4), max(72, SIZE // 6), max(3, SIZE // 180)
    row = y // h
    off = (w // 2) if row % 2 else 0
    in_grout = ((x + off) % w < grout) or (y % h < grout)
    t = cell_tint(x, y, w, h, 31, True)
    return 0.34 if in_grout else clamp(0.56 + 0.040 * (t - 0.5), 0.48, 0.63)


def slab_albedo(x: int, y: int) -> RGB:
    w, h, grout = max(96, SIZE // 4), max(72, SIZE // 6), max(3, SIZE // 180)
    row = y // h
    off = (w // 2) if row % 2 else 0
    in_grout = ((x + off) % w < grout) or (y % h < grout)
    t = cell_tint(x, y, w, h, 32, True)
    c = (0.40, 0.38, 0.34) if in_grout else mix_color((0.62, 0.59, 0.51), (0.76, 0.72, 0.64), t)
    return to_rgb(c)


def slab_rough(x: int, y: int) -> float:
    return 0.90 if slab_h(x, y) < 0.40 else 0.78


def stucco_h(x: int, y: int) -> float:
    return clamp(0.50 + 0.020 * wave_noise(x, y, 41) + 0.010 * math.sin(TAU * x / SIZE * 5.0), 0.44, 0.57)


def stucco_albedo(x: int, y: int) -> RGB:
    h = stucco_h(x, y)
    streak = smoothstep(0.78, 0.95, hash01(x // 52, 0, 42)) * (y / SIZE) * 0.025
    v = 0.73 + (h - 0.50) * 0.55 - streak
    return to_rgb((v * 1.10, v * 1.03, v * 0.90))


def stucco_rough(x: int, y: int) -> float:
    return 0.84


def brick_h(x: int, y: int, subtle: bool = False) -> float:
    bw, bh, mortar = (128, 46, 5) if subtle else (96, 40, 5)
    row = y // bh
    off = (bw // 2) if row % 2 else 0
    in_mortar = ((x + off) % bw < mortar) or (y % bh < mortar)
    t = cell_tint(x, y, bw, bh, 51, True)
    return 0.40 if in_mortar else clamp(0.56 + 0.030 * (t - 0.5), 0.49, 0.62)


def brick_albedo(x: int, y: int, subtle: bool = False) -> RGB:
    bw, bh, mortar = (128, 46, 5) if subtle else (96, 40, 5)
    row = y // bh
    off = (bw // 2) if row % 2 else 0
    in_mortar = ((x + off) % bw < mortar) or (y % bh < mortar)
    t = cell_tint(x, y, bw, bh, 52, True)
    if in_mortar:
        return to_rgb((0.50, 0.45, 0.38))
    a = (0.58, 0.36, 0.27) if not subtle else (0.62, 0.47, 0.36)
    b = (0.76, 0.49, 0.35) if not subtle else (0.74, 0.56, 0.42)
    return to_rgb(mix_color(a, b, t * 0.85))


def brick_rough(x: int, y: int) -> float:
    return 0.84


def facade_albedo(kind: str) -> Callable[[int, int], RGB]:
    def px(x: int, y: int) -> RGB:
        c = brick_albedo(x, y, True) if kind == "brick" else stucco_albedo(x, y)
        cols, rows = 4, 4
        cw, ch = SIZE / cols, SIZE / rows
        lx = (x % int(cw)) / cw
        ly = (y % int(ch)) / ch
        # Janela limpa com moldura clara e vidro azul escuro; evita ruído/sujeira.
        if 0.25 < lx < 0.75 and 0.24 < ly < 0.70:
            if 0.30 < lx < 0.70 and 0.30 < ly < 0.64:
                shine = 0.12 if abs((lx - 0.34) - (ly - 0.34)) < 0.06 else 0.0
                return to_rgb((0.16 + shine, 0.27 + shine, 0.36 + shine))
            return to_rgb((0.82, 0.80, 0.72))
        if 0.20 < lx < 0.80 and 0.72 < ly < 0.78:
            return to_rgb((0.66, 0.61, 0.52))
        return c
    return px


def simple_material(base_a: tuple[float, float, float], base_b: tuple[float, float, float], seed: int,
        cell: int = 128) -> tuple[Callable[[int, int], RGB], Callable[[int, int], float], Callable[[int, int], float]]:
    del cell  # mantido na assinatura para compatibilidade com chamadas antigas.
    def smooth_value(x: int, y: int, offset: int = 0) -> float:
        return clamp(0.50 + 0.34 * wave_noise(x, y, seed + offset) + 0.06 * math.sin(TAU * (x + y) / SIZE + seed * 0.03))
    def h(x: int, y: int) -> float:
        return clamp(0.50 + 0.040 * (smooth_value(x, y, 1) - 0.5), 0.46, 0.56)
    def alb(x: int, y: int) -> RGB:
        w = smooth_value(x, y, 2)
        return to_rgb(mix_color(base_a, base_b, w))
    def rough(x: int, y: int) -> float:
        return clamp(0.78 + 0.08 * smooth_value(x, y, 3), 0.68, 0.90)
    return alb, h, rough


# ---------------------------------------------------------------------------
# Escrita por material
# ---------------------------------------------------------------------------

def write_root(name: str, alb: Callable[[int, int], RGB], h: Callable[[int, int], float], rough: Callable[[int, int], float], normal_strength: float) -> None:
    write_png_rgb(OUT / f"{name}.png", alb)
    # As versões legadas usadas pelo projeto não incluem o sufixo _realista.
    normal_name = "asfalto_normal" if name == "asfalto_realista" else "calcada_normal" if name == "calcada_realista" else f"{name}_normal"
    rough_name = "asfalto_roughness" if name == "asfalto_realista" else "calcada_roughness" if name == "calcada_realista" else f"{name}_roughness"
    write_normal(OUT / f"{normal_name}.png", h, normal_strength)
    write_png_gray(OUT / f"{rough_name}.png", rough)


def write_pbr(prefix: str, alb: Callable[[int, int], RGB], h: Callable[[int, int], float], rough: Callable[[int, int], float], normal_strength: float, metallic: float = 0.0) -> None:
    write_png_rgb(OUT_PBR / f"{prefix}_albedo.png", alb)
    write_normal(OUT_PBR / f"{prefix}_normal.png", h, normal_strength)
    write_orm(OUT_PBR / f"{prefix}_orm.png", rough, metallic)
    write_png_gray(OUT_PBR / f"{prefix}_height.png", h)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    OUT_PBR.mkdir(parents=True, exist_ok=True)
    print(f"Gerando visual polish estilizado em {OUT} ({SIZE}x{SIZE}, seed={MASTER_SEED})")

    write_root("asfalto_realista", asphalt_albedo, asphalt_h, asphalt_rough, 0.28)
    write_root("calcada_realista", lambda x, y: mosaic_albedo(x, y, True), lambda x, y: mosaic_h(x, y, True), mosaic_rough, 0.25)

    concrete = simple_material((0.48, 0.47, 0.43), (0.64, 0.62, 0.56), 60)
    wood = simple_material((0.42, 0.27, 0.16), (0.66, 0.43, 0.24), 90, 96)
    metal = simple_material((0.38, 0.39, 0.39), (0.62, 0.63, 0.61), 80)
    dirt = simple_material((0.43, 0.25, 0.14), (0.64, 0.39, 0.20), 100)

    write_root("concreto_realista", *concrete, normal_strength=0.22)
    write_root("fachada_reboco", facade_albedo("plaster"), stucco_h, stucco_rough, 0.18)
    write_root("fachada_tijolo", facade_albedo("brick"), lambda x, y: brick_h(x, y, True), brick_rough, 0.20)
    write_root("parede_tijolo_realista", lambda x, y: brick_albedo(x, y, True), lambda x, y: brick_h(x, y, True), brick_rough, 0.22)
    write_root("madeira_realista", *wood, normal_strength=0.22)
    write_root("metal_pintado_realista", *metal, normal_strength=0.16)
    write_root("terra_realista", *dirt, normal_strength=0.18)

    write_pbr("asfalto", asphalt_albedo, asphalt_h, asphalt_rough, 0.28)
    write_pbr("calcada_laje", slab_albedo, slab_h, slab_rough, 0.24)
    write_pbr("calcada_mosaico", lambda x, y: mosaic_albedo(x, y, False), lambda x, y: mosaic_h(x, y, False), mosaic_rough, 0.24)
    write_pbr("reboco", stucco_albedo, stucco_h, stucco_rough, 0.18)
    write_pbr("tijolo", lambda x, y: brick_albedo(x, y, False), lambda x, y: brick_h(x, y, False), brick_rough, 0.22)
    roof = simple_material((0.33, 0.32, 0.30), (0.48, 0.46, 0.41), 70)
    zinc = simple_material((0.50, 0.51, 0.52), (0.68, 0.69, 0.70), 81)
    write_pbr("laje_cobertura", *roof, normal_strength=0.18)
    write_pbr("metal_pintado", *metal, normal_strength=0.16, metallic=0.35)
    write_pbr("metal_zincado", *zinc, normal_strength=0.14, metallic=0.55)
    write_pbr("madeira", *wood, normal_strength=0.22)
    write_pbr("terra_vermelha", *dirt, normal_strength=0.18)
    print("OK: pacote de rua/prédios estilizado sem speckles/pixelado.")


if __name__ == "__main__":
    main()
