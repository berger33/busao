#!/usr/bin/env python3
"""Gera a splash screen de boot do Corre pro Ponto (assets/art/splash.png).

Deterministico (sem ruido aleatorio). Requer pillow. Rode:

    python3 tools/generate_splash.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "art" / "splash.png"
W, H = 1080, 1920

# paleta da identidade (mesma da HUD)
DEEP = (8, 21, 47)
MID = (23, 60, 90)
YELLOW = (244, 191, 61)
CYAN = (108, 196, 204)
RED = (237, 99, 76)
WHITE = (255, 248, 231)
MUTED = (169, 185, 202)
INK = (32, 43, 58)


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ):
        path = Path(candidate)
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    try:
        return ImageFont.load_default(size)
    except TypeError:  # pillow antigo sem tamanho
        return ImageFont.load_default()


def vertical_gradient(draw: ImageDraw.ImageDraw) -> None:
    for y in range(H):
        t = y / (H - 1)
        # curva suave com uma faixa mais clara no terco medio
        k = t * t * (3 - 2 * t)
        r = int(DEEP[0] + (MID[0] - DEEP[0]) * k)
        g = int(DEEP[1] + (MID[1] - DEEP[1]) * k)
        b = int(DEEP[2] + (MID[2] - DEEP[2]) * k)
        draw.line([(0, y), (W, y)], fill=(r, g, b))


def glow(layer: Image.Image, center: tuple[int, int], radius: int, color: tuple[int, int, int, int]) -> None:
    d = ImageDraw.Draw(layer)
    steps = 28
    for i in range(steps, 0, -1):
        alpha = int(color[3] * (1.0 - i / steps) ** 2)
        r = int(radius * i / steps)
        d.ellipse(
            [center[0] - r, center[1] - r, center[0] + r, center[1] + r],
            fill=(color[0], color[1], color[2], alpha),
        )


def draw_bus(d: ImageDraw.ImageDraw, cx: int, cy: int, scale: float = 1.0) -> None:
    s = scale
    body_w, body_h = int(760 * s), int(360 * s)
    x0, y0 = cx - body_w // 2, cy - body_h // 2
    radius = int(46 * s)
    # sombra no chao
    d.ellipse(
        [cx - int(430 * s), cy + int(150 * s), cx + int(430 * s), cy + int(220 * s)],
        fill=(4, 10, 22),
    )
    # corpo
    d.rounded_rectangle([x0, y0, x0 + body_w, y0 + body_h], radius=radius, fill=YELLOW)
    # letreiro de destino
    d.rounded_rectangle(
        [x0 + int(90 * s), y0 + int(26 * s), x0 + int(340 * s), y0 + int(88 * s)],
        radius=int(14 * s),
        fill=(43, 47, 54),
    )
    d.rounded_rectangle(
        [x0 + int(100 * s), y0 + int(34 * s), x0 + int(330 * s), y0 + int(80 * s)],
        radius=int(10 * s),
        fill=(255, 217, 122),
    )
    # faixa de janelas
    d.rounded_rectangle(
        [x0 + int(60 * s), y0 + int(110 * s), x0 + body_w - int(60 * s), y0 + int(220 * s)],
        radius=int(18 * s),
        fill=CYAN,
    )
    # parabrisa (frente a esquerda)
    d.rounded_rectangle(
        [x0 + int(70 * s), y0 + int(118 * s), x0 + int(190 * s), y0 + int(212 * s)],
        radius=int(14 * s),
        fill=(238, 247, 244),
    )
    # colunas das janelas
    for i in range(1, 5):
        px = x0 + int((60 + i * 128) * s)
        d.rectangle([px, y0 + int(110 * s), px + int(10 * s), y0 + int(220 * s)], fill=YELLOW)
    # faixa vermelha
    d.rectangle([x0, y0 + int(250 * s), x0 + body_w, y0 + int(290 * s)], fill=RED)
    # farois
    d.rounded_rectangle(
        [x0 + int(6 * s), y0 + int(196 * s), x0 + int(56 * s), y0 + int(236 * s)],
        radius=int(10 * s),
        fill=(255, 242, 186),
    )
    # rodas
    for wx in (x0 + int(190 * s), x0 + body_w - int(190 * s)):
        wy = y0 + body_h - int(10 * s)
        r = int(78 * s)
        d.ellipse([wx - r, wy - r, wx + r, wy + r], fill=INK)
        hub = int(30 * s)
        d.ellipse([wx - hub, wy - hub, wx + hub, wy + hub], fill=(195, 200, 191))


def draw_road(d: ImageDraw.ImageDraw) -> None:
    y = 1430
    d.rectangle([0, y, W, H], fill=(26, 32, 44))
    d.rectangle([0, y, W, y + 10], fill=(58, 66, 82))
    # faixa central tracejada
    for i in range(-1, 10):
        x = i * 140 + 30
        d.rectangle([x, y + 235, x + 78, y + 261], fill=(240, 210, 110))
    # faixa de pedestre
    for i in range(12):
        x = 40 + i * 88
        d.rectangle([x, y + 340, x + 54, y + 460], fill=(226, 230, 233))


def centered_text(d: ImageDraw.ImageDraw, y: int, text: str, font, fill, shadow=(4, 10, 22)) -> None:
    bbox = d.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    x = (W - w) // 2
    d.text((x + 5, y + 7), text, font=font, fill=shadow)
    d.text((x, y), text, font=font, fill=fill)


def main() -> None:
    img = Image.new("RGB", (W, H), DEEP)
    d = ImageDraw.Draw(img)

    vertical_gradient(d)

    # brilho suave atras do onibus
    glow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow(glow_layer, (W // 2, 900), 560, (90, 160, 210, 90))
    img = Image.alpha_composite(img.convert("RGBA"), glow_layer).convert("RGB")
    d = ImageDraw.Draw(img)

    draw_road(d)
    draw_bus(d, W // 2, 880, 1.0)

    title = load_font(150)
    sub = load_font(58)
    small = load_font(40)

    centered_text(d, 170, "CORRE", title, WHITE)
    centered_text(d, 355, "PRO PONTO", title, YELLOW)
    centered_text(d, 560, "runner 3D brasileiro", sub, MUTED)
    centered_text(d, 1210, " Pegue o busão antes que ele vá embora", small, WHITE)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, optimize=True)
    print(f"splash gerado: {OUT} ({W}x{H})")


if __name__ == "__main__":
    main()
