#!/usr/bin/env python3
"""
facade_forge.py - monta os atlas de fachada fotorrealistas.

As fachadas do jogo usam um ATLAS de 4 janelas x 4 andares: game_3d.gd faz
uv1_scale = (width/6, height/12, ...) e uv1_offset.y = 0.75 para mostrar so o
terreo nas casas baixas. O atlas original era desenhado a mao, chapado e
cartunesco -- destoava do personagem e das arvores.

Aqui o atlas e composto por cima do scan realista de tijolo/reboco:
  * vao recuado com ambient occlusion no batente
  * sombra de verga/ombreira projetada dentro do vao
  * vidro com reflexo de ceu, e persiana ou cortina variando por janela
  * caixilho pintado e peitoril de concreto
  * escorrimento de sujeira abaixo do peitoril (o detalhe que vende idade)

Normal e roughness sao construidos das MASCARAS reais de cada elemento (nao
estimados da luminancia), entao o vidro fica espelhado e a alvenaria fosca.

Rodar SEMPRE depois de texture_forge.py (ver tools/build_textures.sh).
"""

import numpy as np
from PIL import Image, ImageFilter

OUT = "assets/textures"
SRC = "tools/source_textures"
SIZE = 1024
COLS, ROWS = 4, 4
CELL = SIZE // COLS  # 256


def load_base(path, tiles=1):
    """Carrega o scan da alvenaria repetindo-o `tiles` vezes.

    O atlas cobre 6 m de fachada; sem repetir, um tijolo ficaria com 65 cm.
    tiles=4 devolve fiadas de ~8 cm, que e a medida real.
    """
    im = Image.open(path).convert("RGB")
    if tiles > 1:
        step = SIZE // tiles
        im = im.resize((step, step), Image.LANCZOS)
        full = Image.new("RGB", (SIZE, SIZE))
        for ty in range(tiles):
            for tx in range(tiles):
                full.paste(im, (tx * step, ty * step))
        im = full
    else:
        im = im.resize((SIZE, SIZE), Image.LANCZOS)
    return np.asarray(im).astype(np.float32) / 255.0


def blur(a, r):
    single = a.ndim == 2
    src = a[..., None] if single else a
    pad = int(r * 3) + 1
    p = np.pad(src, ((pad, pad), (pad, pad), (0, 0)), mode="wrap")
    if p.shape[2] == 1:
        p = p[:, :, 0]
    img = Image.fromarray(np.clip(p * 255, 0, 255).astype(np.uint8))
    img = img.filter(ImageFilter.GaussianBlur(r))
    o = np.asarray(img).astype(np.float32) / 255.0
    if o.ndim == 2:
        o = o[..., None]
    o = o[pad:-pad, pad:-pad, :]
    return o[..., 0] if single else o


def rect(mask, x0, y0, x1, y1, value=1.0):
    mask[int(y0):int(y1), int(x0):int(x1)] = value


def vgrad(h, top, bottom):
    t = np.linspace(0.0, 1.0, h)[:, None]
    return np.array(top)[None, None, :] * (1 - t[..., None]) + \
        np.array(bottom)[None, None, :] * t[..., None]


def build(base_path, out_albedo, out_normal, out_rough,
          frame_color=(0.88, 0.87, 0.84), sill_color=(0.74, 0.72, 0.68),
          seed=7, grime=0.55, base_tiles=1):
    rng = np.random.default_rng(seed)
    albedo = load_base(base_path, base_tiles)

    m_open = np.zeros((SIZE, SIZE), np.float32)    # vao (vidro)
    m_frame = np.zeros((SIZE, SIZE), np.float32)   # caixilho
    m_sill = np.zeros((SIZE, SIZE), np.float32)    # peitoril
    glass_rgb = np.zeros((SIZE, SIZE, 3), np.float32)

    win_w, win_h = 128, 150
    fr = 9                                          # espessura do caixilho

    for r in range(ROWS):
        for c in range(COLS):
            ox, oy = c * CELL, r * CELL
            x0 = ox + (CELL - win_w) // 2
            y0 = oy + 34
            x1, y1 = x0 + win_w, y0 + win_h

            rect(m_frame, x0 - fr, y0 - fr, x1 + fr, y1 + fr)
            rect(m_open, x0, y0, x1, y1)

            # ---- vidro: reflexo do ceu no topo, interior escuro embaixo ----
            g = vgrad(win_h, (0.62, 0.72, 0.80), (0.07, 0.10, 0.14))[:, 0, :]
            g = np.repeat(g[:, None, :], win_w, axis=1)

            # brilho especular diagonal
            yy, xx = np.mgrid[0:win_h, 0:win_w]
            d = (xx / win_w + yy / win_h)
            streak = np.exp(-((d - 0.62) ** 2) / 0.010) * 0.55
            streak += np.exp(-((d - 0.95) ** 2) / 0.004) * 0.25
            g = g + streak[..., None]

            # variacao: persiana, cortina ou vazio
            kind = rng.integers(0, 3)
            if kind == 0:                                   # persiana baixada
                lvl = int(win_h * rng.uniform(0.35, 0.8))
                slats = 0.5 + 0.5 * np.cos(np.arange(lvl) * 1.5)
                blind = (0.52 + slats * 0.14)[:, None, None]
                blind = np.repeat(np.repeat(blind, win_w, axis=1), 3, axis=2)
                blind *= np.array([1.0, 0.98, 0.93])
                g[:lvl] = blind
            elif kind == 1:                                 # cortina clara
                side = int(win_w * rng.uniform(0.3, 0.5))
                cur = np.full((win_h, side, 3), 0.80, np.float32)
                cur *= (0.85 + 0.15 * np.cos(np.arange(side) * 0.9))[None, :, None]
                if rng.random() < 0.5:
                    g[:, :side] = cur
                else:
                    g[:, -side:] = cur

            # montantes (cruzeta) do caixilho
            mid_x, mid_y = win_w // 2, win_h // 2
            g[:, mid_x - 3:mid_x + 3] = np.array(frame_color) * 0.92
            g[mid_y - 3:mid_y + 3, :] = np.array(frame_color) * 0.92

            # sombra do batente: a verga projeta no topo, a ombreira num lado
            rev_y = np.clip(1.0 - np.arange(win_h) / 26.0, 0.0, 1.0)[:, None]
            rev_x = np.clip(1.0 - np.arange(win_w) / 20.0, 0.0, 1.0)[None, :]
            reveal = np.clip(rev_y * 0.55 + rev_x * 0.35, 0.0, 0.75)
            g = g * (1.0 - reveal[..., None] * 0.8)

            glass_rgb[y0:y1, x0:x1] = g

            # ---- peitoril ----
            sx0, sx1 = x0 - fr - 8, x1 + fr + 8
            sy0, sy1 = y1 + fr, y1 + fr + 12
            rect(m_sill, sx0, sy0, sx1, sy1)

            # ---- escorrimento de sujeira sob o peitoril ----
            run_h = int(CELL - (sy1 - oy)) - 6
            if run_h > 8 and grime > 0:
                yy2 = np.arange(run_h)[:, None]
                fade = np.clip(1.0 - yy2 / float(run_h), 0.0, 1.0) ** 1.6
                streaks = 0.5 + 0.5 * np.cos(np.arange(sx1 - sx0) * rng.uniform(0.5, 0.9))
                dirt = fade * streaks[None, :] * grime * 0.22
                reg = albedo[sy1:sy1 + run_h, sx0:sx1]
                albedo[sy1:sy1 + run_h, sx0:sx1] = np.clip(
                    reg * (1.0 - dirt[..., None]) +
                    np.array([0.22, 0.21, 0.19]) * dirt[..., None], 0, 1)

    # ---------------- composicao do albedo ----------------
    frame_only = np.clip(m_frame - m_open, 0, 1)
    solid = np.clip(m_frame + m_sill, 0, 1)
    ao = np.clip(1.0 - (blur(solid, 7.0) - solid) * 0.9, 0.35, 1.0)
    albedo *= ao[..., None]

    grain = blur(rng.random((SIZE, SIZE)).astype(np.float32), 1.2)
    fc = np.array(frame_color)[None, None, :] * (0.94 + 0.12 * grain)[..., None]
    albedo = albedo * (1 - frame_only[..., None]) + fc * frame_only[..., None]
    albedo = albedo * (1 - m_sill[..., None]) + \
        np.array(sill_color)[None, None, :] * m_sill[..., None]
    albedo = albedo * (1 - m_open[..., None]) + glass_rgb * m_open[..., None]
    albedo = np.clip(albedo, 0, 1)

    # ---------------- normal a partir das mascaras ----------------
    height = np.full((SIZE, SIZE), 0.50, np.float32)
    height = height * (1 - m_open) + 0.12 * m_open          # vidro recuado
    height = height * (1 - frame_only) + 0.62 * frame_only  # caixilho saliente
    height = height * (1 - m_sill) + 0.85 * m_sill          # peitoril saliente
    height = blur(height, 1.4)

    lum = albedo @ np.array([0.2126, 0.7152, 0.0722])
    height = height + (lum - blur(lum, 10.0)) * (1.0 - m_open) * 0.35

    gx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * 0.5
    gy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * 0.5
    nx, ny = -gx * 14.0, gy * 14.0
    nz = np.ones_like(nx)
    ln = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
    normal = np.stack([nx / ln, ny / ln, nz / ln], -1) * 0.5 + 0.5

    # ---------------- roughness por elemento ----------------
    rough = np.full((SIZE, SIZE), 0.88, np.float32)
    rough += (lum - blur(lum, 12.0)) * 0.6
    rough = rough * (1 - m_open) + 0.07 * m_open            # vidro espelhado
    rough = rough * (1 - frame_only) + 0.38 * frame_only    # caixilho pintado
    rough = rough * (1 - m_sill) + 0.80 * m_sill
    rough = np.clip(rough, 0.03, 1.0)

    for arr, name in ((albedo, out_albedo), (normal, out_normal),
                      (np.repeat(rough[..., None], 3, -1), out_rough)):
        Image.fromarray((np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8)) \
            .save(f"{OUT}/{name}")
        print("  ->", name)


def main():
    print("[fachada tijolo]")
    build(f"{SRC}/tijolo_base.jpg",
          "fachada_tijolo.png", "fachada_tijolo_normal.png",
          "fachada_tijolo_roughness.png",
          frame_color=(0.90, 0.89, 0.86), sill_color=(0.72, 0.70, 0.66),
          seed=11, grime=0.7, base_tiles=4)
    print("[fachada reboco]")
    build(f"{SRC}/reboco_base.jpg",
          "fachada_reboco.png", "fachada_reboco_normal.png",
          "fachada_reboco_roughness.png",
          frame_color=(0.84, 0.83, 0.79), sill_color=(0.76, 0.74, 0.70),
          seed=23, grime=0.5, base_tiles=2)


if __name__ == "__main__":
    main()
