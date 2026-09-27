#!/usr/bin/env python3
"""
sky_forge.py - constroi os panoramas de ceu equiretangulares do jogo.

Problema dos ceus antigos: eram gradientes verticais desenhados a mao, sem
UMA nuvem, e com o hemisferio INFERIOR totalmente preto. Como o Environment
usa BG_SKY, esse preto entrava em tudo que reflete (vidro, pintura de carro,
metal) e puxava o ambiente para baixo -- o cenario ficava chapado e sujo.

Aqui o panorama e montado de verdade:

  * hemisferio superior: reprojecao exata de uma foto olho-de-peixe
    equidistante apontada para o zenite. Para cada pixel equiretangular
    (azimute phi, elevacao theta) amostra-se o fisheye em
        r = (1 - theta / (pi/2)) * R,  (x, y) = centro + r * (cos phi, sin phi)
    o que garante continuidade perfeita em 360 graus (sem emenda lateral) e
    sem esticar nuvem no zenite.

  * faixa do horizonte: bruma atmosferica, que e o que da profundidade e
    esconde o corte do cenario ao longe.

  * hemisferio inferior: rebatimento do chao (nunca preto), escurecendo de
    forma suave ate a tonalidade do asfalto. E isso que devolve luz de baixo
    nos reflexos e faz carro/vidro pararem de parecer plastico.

  * brilho solar suave (sem disco duro) na direcao aproximada do sol da cena,
    so para o ceu nao ficar uniforme; a luz direta continua vindo do
    DirectionalLight3D.

Uso:  python3 tools/sky_forge.py
"""

import numpy as np
from PIL import Image, ImageFilter

OUT = "assets/textures"
SRC = "tools/source_textures"
W, H = 2048, 1024

# Direcao do sol da cena: sun.rotation_degrees = (-28, -56, 0) em game_3d.gd
SUN_AZIMUTH = -56.0     # graus
SUN_ELEVATION = 28.0    # graus acima do horizonte


def fisheye_to_equirect(fish):
    """Reprojeta o fisheye do zenite para o hemisferio superior equiretangular."""
    size = fish.shape[0]
    cx = cy = (size - 1) * 0.5
    radius = size * 0.5

    half = H // 2
    u = (np.arange(W) + 0.5) / W                 # 0..1 -> azimute
    v = (np.arange(half) + 0.5) / (H)            # 0..0.5 -> zenite..horizonte

    phi = (u * 2.0 - 1.0) * np.pi                # -pi..pi
    theta = (0.5 - v) * np.pi                    # pi/2 (zenite) .. 0 (horizonte)

    r = (1.0 - theta / (np.pi * 0.5))[:, None] * radius
    sx = cx + r * np.cos(phi)[None, :]
    sy = cy + r * np.sin(phi)[None, :]

    # amostragem bilinear
    x0 = np.floor(sx).astype(np.int32)
    y0 = np.floor(sy).astype(np.int32)
    fx = (sx - x0)[..., None]
    fy = (sy - y0)[..., None]
    x0c = np.clip(x0, 0, size - 1)
    x1c = np.clip(x0 + 1, 0, size - 1)
    y0c = np.clip(y0, 0, size - 1)
    y1c = np.clip(y0 + 1, 0, size - 1)

    top = fish[y0c, x0c] * (1 - fx) + fish[y0c, x1c] * fx
    bot = fish[y1c, x0c] * (1 - fx) + fish[y1c, x1c] * fx
    return top * (1 - fy) + bot * fy


def load_fisheye(path, trim=0.955):
    """Carrega o fisheye e recorta o circulo util (as quinas pretas fora)."""
    im = Image.open(path).convert("RGB")
    s = min(im.size)
    im = im.crop(((im.size[0] - s) // 2, (im.size[1] - s) // 2,
                  (im.size[0] - s) // 2 + s, (im.size[1] - s) // 2 + s))
    a = np.asarray(im).astype(np.float32) / 255.0
    # o circulo raramente encosta na borda; um leve zoom descarta o vinhetamento
    if trim < 1.0:
        k = int(s * (1.0 - trim) * 0.5)
        if k > 0:
            a = a[k:s - k, k:s - k]
            a = np.asarray(Image.fromarray((a * 255).astype(np.uint8))
                           .resize((s, s), Image.LANCZOS)).astype(np.float32) / 255.0
    return a


def sample_ring(sky_top, frac=0.06):
    """Cor media da faixa mais baixa do hemisferio superior (= cor do horizonte)."""
    n = max(1, int(sky_top.shape[0] * frac))
    return sky_top[-n:].reshape(-1, 3).mean(axis=0)


def build(fish_path, out_name, haze=None, ground=None,
          exposure=1.0, saturation=1.0, sun_glow=0.0, horizon_lift=0.55):
    fish = load_fisheye(fish_path)
    top = fisheye_to_equirect(fish)

    # exposicao / saturacao do ceu
    top = top * exposure
    if saturation != 1.0:
        g = (top @ np.array([0.2126, 0.7152, 0.0722]))[..., None]
        top = g + (top - g) * saturation
    top = np.clip(top, 0.0, 1.0)

    horizon = sample_ring(top) if haze is None else np.array(haze, np.float32)

    # ---- bruma perto do horizonte: clareia e dessatura os ultimos graus ----
    half = H // 2
    t = np.linspace(0.0, 1.0, half)[:, None, None]          # 0 zenite, 1 horizonte
    mist = np.clip((t - 0.62) / 0.38, 0.0, 1.0) ** 1.35 * horizon_lift
    haze_col = horizon * 1.06 + 0.06
    top = top * (1.0 - mist) + haze_col[None, None, :] * mist

    # ---- hemisferio inferior: rebatimento do chao, nunca preto ----
    ground_col = np.array(ground if ground is not None
                          else horizon * 0.34 + 0.02, np.float32)
    b = np.linspace(0.0, 1.0, H - half)[:, None, None]
    # A borda precisa ser a MEDIA azimutal suavizada das ultimas linhas: usar a
    # ultima linha crua esticaria cada nuvem numa listra vertical ate o nadir.
    edge = top[-10:].mean(axis=0)
    edge = np.stack([np.convolve(np.pad(edge[:, c], (96, 96), mode="wrap"),
                                 np.ones(193) / 193.0, mode="same")[96:-96]
                     for c in range(3)], axis=-1)[None, :, :]
    falloff = b ** 0.55
    bottom = edge * (1.0 - falloff) + ground_col[None, None, :] * falloff

    pano = np.concatenate([top, bottom], axis=0)

    # ---- brilho solar suave (sem disco: a luz direta e do DirectionalLight) ----
    if sun_glow > 0.0:
        uu = ((np.arange(W) + 0.5) / W)
        vv = ((np.arange(H) + 0.5) / H)
        su = (SUN_AZIMUTH / 360.0) % 1.0
        sv = (90.0 - SUN_ELEVATION) / 180.0
        du = np.minimum(np.abs(uu - su), 1.0 - np.abs(uu - su))[None, :]
        dv = (vv - sv)[:, None]
        d2 = (du * 2.2) ** 2 + dv ** 2
        glow = np.exp(-d2 / 0.035) * sun_glow
        pano = pano + glow[..., None] * np.array([1.0, 0.95, 0.86])

    pano = np.clip(pano, 0.0, 1.0)

    img = Image.fromarray((pano * 255 + 0.5).astype(np.uint8))
    # suaviza o ruido de compressao do scan sem perder a borda das nuvens
    img = img.filter(ImageFilter.SMOOTH)
    img.save(f"{OUT}/{out_name}")
    print(f"  -> {out_name}  horizonte={np.round(horizon, 3)}")


def main():
    print("[ceu tropical]")
    for name in ("ceu_tropical_v2.png", "ceu_tropical.png"):
        build(f"{SRC}/ceu_tropical_fish.jpg", name,
              exposure=1.04, saturation=1.02, sun_glow=0.30, horizon_lift=0.62)

    print("[ceu entardecer]")
    for name in ("ceu_entardecer_v2.png", "ceu_entardecer.png"):
        build(f"{SRC}/ceu_entardecer_fish.jpg", name,
              exposure=0.92, saturation=0.70, sun_glow=0.34, horizon_lift=0.58,
              ground=(0.13, 0.11, 0.10))

    print("[ceu nublado]")
    build(f"{SRC}/ceu_nublado_fish.jpg", "ceu_nublado.png",
          exposure=1.02, saturation=0.9, sun_glow=0.06, horizon_lift=0.66,
          ground=(0.16, 0.16, 0.17))


if __name__ == "__main__":
    main()
