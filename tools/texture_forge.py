#!/usr/bin/env python3
"""
texture_forge.py - pipeline de polimento de texturas para "Corre pro Ponto".

Pega os scans fotorrealistas versionados em tools/source_textures/ e produz o
conjunto PBR usado pelo jogo (albedo + normal + roughness) em assets/textures/:

  1. normaliza para 1024x1024
  2. remove a iluminacao assada (divide pela luminancia de baixa frequencia)
  3. costura as bordas (heal por eixo) => tileavel de verdade
  4. gera normal map tileavel por Sobel com wrap sobre o height suavizado
  5. gera roughness map por remapeamento da luminancia

Receitas sem scan correspondente sao simplesmente puladas, entao da para ir
substituindo o acervo aos poucos.

Uso:  python3 tools/texture_forge.py
"""

import os
import numpy as np
from PIL import Image, ImageFilter

RAW = "tools/source_textures"
OUT = "assets/textures"
SIZE = 1024


# --------------------------------------------------------------------------
# utilidades
# --------------------------------------------------------------------------
def load(path, size=SIZE):
    im = Image.open(path).convert("RGB")
    if im.size != (size, size):
        w, h = im.size
        s = min(w, h)
        im = im.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s))
        im = im.resize((size, size), Image.LANCZOS)
    return np.asarray(im).astype(np.float32) / 255.0


def save(arr, name):
    a = np.clip(arr, 0.0, 1.0)
    Image.fromarray((a * 255.0 + 0.5).astype(np.uint8)).save(os.path.join(OUT, name))
    print(f"  -> {name}")


def blur_wrap(a, radius):
    """Gaussiana com wrap-around (preserva o tileamento)."""
    if radius <= 0:
        return a.copy()
    pad = int(radius * 3) + 1
    single = a.ndim == 2
    src = a[..., None] if single else a
    padded = np.pad(src, ((pad, pad), (pad, pad), (0, 0)), mode="wrap")
    if padded.shape[2] == 1:
        padded = padded[:, :, 0]
    img = Image.fromarray(np.clip(padded * 255.0, 0, 255).astype(np.uint8))
    img = img.filter(ImageFilter.GaussianBlur(radius))
    out = np.asarray(img).astype(np.float32) / 255.0
    if out.ndim == 2:
        out = out[..., None]
    out = out[pad:-pad, pad:-pad, :]
    return out[..., 0] if single else out


def luminance(rgb):
    return rgb[..., 0] * 0.2126 + rgb[..., 1] * 0.7152 + rgb[..., 2] * 0.0722


# --------------------------------------------------------------------------
# 1. achatar a iluminacao assada
# --------------------------------------------------------------------------
def deshade(rgb, strength=0.85, radius=110):
    """Divide pela luminancia de baixa frequencia: tira sombra/vinheta do scan.

    Sem isso o material carrega manchas escuras fixas que brigam com a luz
    real da cena -- uma das causas do aspecto "sujo" das texturas antigas.
    """
    lo = blur_wrap(luminance(rgb), radius)
    target = float(np.mean(lo))
    gain = target / np.maximum(lo, 1e-3)
    gain = 1.0 + (gain - 1.0) * strength
    return np.clip(rgb * gain[..., None], 0.0, 1.0)


# --------------------------------------------------------------------------
# 2. costura tileavel
# --------------------------------------------------------------------------
def _heal_axis(rgb, axis, feather):
    """Desloca meio tile num eixo e cicatriza a unica costura resultante.

    A imagem deslocada K ja tem as bordas desse eixo perfeitamente continuas
    (vieram do miolo da original) e concentra toda a quebra numa linha no
    meio; a original e continua exatamente ali, entao mistura-se as duas com
    um peso que depende so da coordenada desse eixo. Como o peso e constante
    ao longo do outro eixo, a continuidade ja conquistada nao e desfeita.
    """
    n = rgb.shape[axis]
    k = np.roll(rgb, n // 2, axis=axis)

    band = max(8, int(n * feather))
    c = np.arange(n)
    d = np.minimum(np.abs(c - n / 2.0), band) / band     # 0 na costura, 1 longe
    s = d * d * (3.0 - 2.0 * d)                          # smoothstep
    m = 1.0 - s                                          # peso da original
    shape = [1, 1, 1]
    shape[axis] = n
    return k * (1.0 - m.reshape(shape)) + rgb * m.reshape(shape)


def make_seamless(rgb, feather=0.16):
    return _heal_axis(_heal_axis(rgb, 1, feather), 0, feather)


def seam_error(rgb):
    """Quebra na borda relativa ao contraste interno (~1.0 = tileamento perfeito)."""
    inner_h = np.mean(np.abs(rgb[:, 1:] - rgb[:, :-1]))
    inner_v = np.mean(np.abs(rgb[1:, :] - rgb[:-1, :]))
    edge_h = np.mean(np.abs(rgb[:, 0] - rgb[:, -1]))
    edge_v = np.mean(np.abs(rgb[0, :] - rgb[-1, :]))
    return 0.5 * (edge_h / max(inner_h, 1e-6) + edge_v / max(inner_v, 1e-6))


# --------------------------------------------------------------------------
# 3. normal map
# --------------------------------------------------------------------------
def normal_map(rgb, strength=1.6, detail=1.0, smooth=0.6):
    hgt = luminance(rgb)
    if smooth > 0:
        hgt = blur_wrap(hgt, smooth)
    hgt = hgt + (hgt - blur_wrap(hgt, 16.0)) * detail

    gx = (np.roll(hgt, -1, axis=1) - np.roll(hgt, 1, axis=1)) * 0.5
    gy = (np.roll(hgt, -1, axis=0) - np.roll(hgt, 1, axis=0)) * 0.5

    nx = -gx * strength * 8.0
    ny = gy * strength * 8.0          # Y+ (OpenGL / Godot)
    nz = np.ones_like(nx)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([nx / ln, ny / ln, nz / ln], axis=-1) * 0.5 + 0.5


# --------------------------------------------------------------------------
# 4. roughness map
# --------------------------------------------------------------------------
def roughness_map(rgb, base=0.85, spread=0.15, invert=False, detail=1.0):
    lum = luminance(rgb)
    hi = lum - blur_wrap(lum, 24.0)
    lo = blur_wrap(lum, 24.0)
    lo = lo - float(np.mean(lo))
    v = hi * detail + lo * 0.5
    v = v / max(float(np.std(v)) * 3.0, 1e-3)
    if invert:
        v = -v
    return np.clip(base + v * spread, 0.02, 1.0)


# --------------------------------------------------------------------------
# receitas
# --------------------------------------------------------------------------
RECIPES = {
    "asfalto": dict(albedo="asfalto_realista.png",
                    deshade=0.9, deshade_r=120, feather=0.20,
                    n_strength=1.6, n_detail=1.2, r_base=0.90, r_spread=0.10,
                    saturation=0.9, brightness=1.06),
    "calcada": dict(albedo="calcada_realista.png",
                    deshade=0.75, deshade_r=140, feather=0.055,
                    n_strength=2.6, n_detail=1.5, r_base=0.72, r_spread=0.20,
                    r_invert=True, saturation=0.95, brightness=1.02),
    "concreto": dict(albedo="concreto_realista.png",
                     deshade=0.9, deshade_r=110, feather=0.20,
                     n_strength=1.5, n_detail=1.1, r_base=0.86, r_spread=0.12,
                     saturation=0.85, brightness=1.02),
    "reboco": dict(albedo="fachada_reboco.png",
                   deshade=0.92, deshade_r=100, feather=0.20,
                   n_strength=1.1, n_detail=1.0, r_base=0.80, r_spread=0.12,
                   saturation=0.9, brightness=1.02),
    "tijolo": dict(albedo="fachada_tijolo.png",
                   deshade=0.7, deshade_r=140, feather=0.06,
                   n_strength=2.8, n_detail=1.4, r_base=0.82, r_spread=0.16,
                   r_invert=True, saturation=1.0, brightness=1.0),
    "madeira": dict(albedo="madeira_realista.png",
                    deshade=0.85, deshade_r=120, feather=0.14,
                    n_strength=1.8, n_detail=1.3, r_base=0.70, r_spread=0.18,
                    r_invert=True, saturation=1.02, brightness=1.02),
    "terra": dict(albedo="terra_realista.png",
                  deshade=0.85, deshade_r=120, feather=0.20,
                  n_strength=2.0, n_detail=1.3, r_base=0.94, r_spread=0.08,
                  saturation=1.02, brightness=1.0),
    "metal": dict(albedo="metal_pintado_realista.png",
                  deshade=0.95, deshade_r=90, feather=0.20,
                  n_strength=0.7, n_detail=0.8, r_base=0.42, r_spread=0.16,
                  saturation=0.8, brightness=1.02),
    "tecido": dict(albedo="tecido_realista.png",
                   deshade=0.9, deshade_r=110, feather=0.16,
                   n_strength=1.4, n_detail=1.2, r_base=0.88, r_spread=0.10,
                   saturation=0.85, brightness=1.02),
    "borracha": dict(albedo="borracha_realista.png",
                     deshade=0.9, deshade_r=110, feather=0.18,
                     n_strength=1.2, n_detail=1.0, r_base=0.92, r_spread=0.08,
                     saturation=0.6, brightness=1.0),
    "paralelepipedo": dict(albedo="paralelepipedo_realista.png",
                           deshade=0.8, deshade_r=130, feather=0.07,
                           n_strength=2.8, n_detail=1.5, r_base=0.80,
                           r_spread=0.18, r_invert=True,
                           saturation=0.95, brightness=1.02),
    "pintura": dict(albedo="pintura_realista.png",
                    deshade=0.95, deshade_r=90, feather=0.20,
                    n_strength=0.5, n_detail=0.7, r_base=0.46, r_spread=0.10,
                    saturation=0.85, brightness=1.02),
}

# os mapas derivados usam exatamente os nomes que o jogo ja faz preload
DERIVED = {
    "asfalto": ("asfalto_normal.png", "asfalto_roughness.png"),
    "calcada": ("calcada_normal.png", "calcada_roughness.png"),
    "concreto": ("concreto_realista_normal.png", "concreto_realista_roughness.png"),
    "reboco": ("fachada_reboco_normal.png", "fachada_reboco_roughness.png"),
    "tijolo": ("fachada_tijolo_normal.png", "fachada_tijolo_roughness.png"),
    "madeira": ("madeira_realista_normal.png", "madeira_realista_roughness.png"),
    "terra": ("terra_realista_normal.png", "terra_realista_roughness.png"),
    "metal": ("metal_pintado_realista_normal.png", "metal_pintado_realista_roughness.png"),
    "tecido": ("tecido_realista_normal.png", "tecido_realista_roughness.png"),
    "borracha": ("borracha_realista_normal.png", "borracha_realista_roughness.png"),
    "paralelepipedo": ("paralelepipedo_realista_normal.png",
                       "paralelepipedo_realista_roughness.png"),
    "pintura": ("pintura_realista_normal.png", "pintura_realista_roughness.png"),
}

# a parede de tijolo aparente reusa o mesmo scan da fachada
ALIASES = {
    "tijolo": [("parede_tijolo_realista.png", "parede_tijolo_realista_normal.png",
                "parede_tijolo_realista_roughness.png")],
}


def adjust(rgb, saturation=1.0, brightness=1.0):
    out = rgb * brightness
    if saturation != 1.0:
        g = luminance(out)[..., None]
        out = g + (out - g) * saturation
    return np.clip(out, 0.0, 1.0)


def main():
    os.makedirs(OUT, exist_ok=True)
    for key, rec in RECIPES.items():
        src = os.path.join(RAW, f"{key}.jpg")
        if not os.path.exists(src):
            print(f"[skip] {key}: sem scan em {src}")
            continue
        print(f"[{key}]")
        img = load(src)
        img = deshade(img, rec.get("deshade", 0.85), rec.get("deshade_r", 110))
        img = adjust(img, rec.get("saturation", 1.0), rec.get("brightness", 1.0))
        img = make_seamless(img, rec.get("feather", 0.16))
        print(f"  seam={seam_error(img):.3f}")

        nrm = normal_map(img, rec.get("n_strength", 1.6), rec.get("n_detail", 1.0))
        rgh = roughness_map(img, rec.get("r_base", 0.85), rec.get("r_spread", 0.15),
                            rec.get("r_invert", False))
        rgh3 = np.repeat(rgh[..., None], 3, axis=-1)

        save(img, rec["albedo"])
        n_name, r_name = DERIVED[key]
        save(nrm, n_name)
        save(rgh3, r_name)
        for a_alb, a_nrm, a_rgh in ALIASES.get(key, []):
            save(img, a_alb)
            save(nrm, a_nrm)
            save(rgh3, a_rgh)


if __name__ == "__main__":
    main()
