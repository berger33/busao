#!/usr/bin/env python3
"""Gera a textura de nuvens usada pelo clima (sky_cover do ProceduralSkyMaterial).

Por que existe: `ProceduralSkyMaterial.sky_cover` e uma **textura** equirretangular
(as cores dela sao SOMADAS ao ceu), nao um numero. Entao as nuvens do clima saem
daqui, e a intensidade e controlada no jogo por `sky_cover_modulate`.

Regras:
  - determinismo: semente fixa, mesmo PNG sempre;
  - sem emenda no horizontal (equirretangular: a coluna 0 casa com a ultima);
  - sem emenda visivel tambem quando o ceu repete;
  - nada de ruido branco: fbm (varias oitavas de value noise) para parecer nuvem.

Rode:  python3 tools/generate_clouds.py
Saida: assets/textures/ceu/nuvens.png (1024x512, RGB)
"""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "assets" / "textures" / "ceu" / "nuvens.png"

LARGURA = 1024
ALTURA = 512
SEMENTE = 20260918
OITAVAS = 6
GRADE_BASE = 6          # celulas no eixo X na primeira oitava (periodico)
LUMINANCIA_MAX = 0.62   # as cores sao somadas ao ceu: nao pode estourar


def _grade_periodica(altura_grade: int, rng: random.Random) -> list:
    """Grade de valores aleatorios que fecha no horizontal (equirretangular)."""
    return [rng.random() for _ in range(altura_grade * (altura_grade // 2))]


def _amostrar_grade(grade: list, largura_grade: int, altura_grade: int, x: float, y: float) -> float:
    xi = int(math.floor(x)) % largura_grade
    yi = int(math.floor(y)) % altura_grade
    xf = x - math.floor(x)
    yf = y - math.floor(y)
    x1 = (xi + 1) % largura_grade
    y1 = (yi + 1) % altura_grade

    def valor(col: int, lin: int) -> float:
        return grade[lin * largura_grade + col]

    def suave(t: float) -> float:
        return t * t * (3.0 - 2.0 * t)

    u = suave(xf)
    v = suave(yf)
    a = valor(xi, yi)
    b = valor(x1, yi)
    c = valor(xi, y1)
    d = valor(x1, y1)
    return (a + (b - a) * u) + ((c + (d - c) * u) - (a + (b - a) * u)) * v


def fbm(x: float, y: float, grades: list, largura_grade: int, altura_grade: int) -> float:
    total = 0.0
    amplitude = 1.0
    soma = 0.0
    freq = 1.0
    for oitava in range(OITAVAS):
        g = grades[oitava]
        lg = largura_grade * (2 ** oitava)
        ag = altura_grade * (2 ** oitava)
        total += amplitude * _amostrar_grade(g, lg, ag, x * freq, y * freq)
        soma += amplitude
        amplitude *= 0.55
        freq *= 2.0
    return total / soma


def main() -> int:
    try:
        from PIL import Image
    except ImportError:
        print("ERRO: Pillow ausente (pip install pillow)")
        return 1
    rng = random.Random(SEMENTE)
    grades = []
    for oitava in range(OITAVAS):
        lg = GRADE_BASE * (2 ** oitava)
        ag = max(2, GRADE_BASE // 2 * (2 ** oitava))
        grades.append(_grade_periodica(max(lg, ag) * 2, rng))

    img = Image.new("RGB", (LARGURA, ALTURA))
    pixels = img.load()
    for y in range(ALTURA):
        # equirretangular: comprime perto dos polos, como uma esfera de verdade
        lat = (y + 0.5) / ALTURA * math.pi - math.pi / 2.0
        escala_y = max(0.35, math.cos(lat))
        for x in range(LARGURA):
            u = (x + 0.5) / LARGURA
            v = (y + 0.5) / (ALTURA * escala_y)
            n = fbm(u * GRADE_BASE, v * GRADE_BASE, grades, GRADE_BASE, GRADE_BASE // 2)
            # cobertura: so a parte de cima da distribuicao vira nuvem; o ganho
            # alto e o que da contraste (ceu limpo escuro, nuvem clara)
            c = min(1.0, max(0.0, (n - 0.44) * 3.2))
            c = c * c * (3.0 - 2.0 * c)
            # nuvem mais "cheia" perto do horizonte (y maior) e mais rala no zenite
            c *= 0.8 + 0.35 * ((y + 0.5) / ALTURA)
            tom = LUMINANCIA_MAX * min(1.0, c)
            cor = (int(255 * tom * 0.99), int(255 * tom * 0.995), int(255 * tom))
            pixels[x, y] = cor
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    img.save(SAIDA)
    print(f"nuvens: {SAIDA.relative_to(RAIZ)} ({LARGURA}x{ALTURA}, "
          f"{SAIDA.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
