#!/usr/bin/env python3
"""ETAPA 5 — frente de arte: gera barreira.glb e ipe_amarelo.glb.

Sem bpy (indisponivel neste sandbox); usa tools/glb/glb_writer.py para
escrever GLB binario direto no espaco do Godot (Y para cima, frente -Z,
origem no chao, escala real em metros — contrato de assets/props/LEIA-ME.md).

  python3 tools/glb/build_etapa5.py
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from glb_writer import GlbWriter, ler_glb

REPO = Path(__file__).resolve().parents[2]

# Cores (mesma leitura do kit procedural)
ZINCADO = (0.62, 0.64, 0.66)
LARANJA = (0.94, 0.47, 0.09)
BRANCO = (0.91, 0.93, 0.95)
CASCA = (0.36, 0.27, 0.18)
AMARELO_A = (0.95, 0.76, 0.15)
AMARELO_B = (1.00, 0.85, 0.30)
AMARELO_C = (0.85, 0.64, 0.10)


def build_barreira():
    """Barreira suspensa de obra: mesmo desenho do fallback procedural —
    barra listrada entre 1,12 e 1,50 m com vao inferior livre (deslize)."""
    w = GlbWriter()
    for lado in (-1.05, 1.05):
        w.cylinder(lado, 0.95, 0.0, 0.06, 0.05, 1.90, "zincado", ZINCADO,
                   rough=0.35, metal=0.75, seg=12)
        w.box(lado, 0.03, 0.0, 0.34, 0.06, 0.34, "zincado", ZINCADO,
              rough=0.35, metal=0.75)
    # Barra entre 1,12 e 1,50 m (o colisor superior corresponde a barra).
    w.box(0.0, 1.31, 0.0, 2.30, 0.38, 0.09, "pintura", LARANJA, rough=0.55)
    for i in range(4):
        w.box(-0.92 + i * 0.61, 1.31, 0.0, 0.24, 0.38, 0.095, "pintura",
              BRANCO, rough=0.50)
    w.box(0.0, 1.63, 0.0, 2.30, 0.10, 0.06, "pintura", LARANJA, rough=0.55)
    caminho = w.write(str(REPO / "assets" / "props" / "barreira.glb"),
                      root_name="barreira")
    return caminho


def build_ipe():
    """Ipe-amarelo: tronco com dois galhos de apoio e copa em cachos
    amarelos achatados (florada), ~4,8 m, origem no chao."""
    w = GlbWriter()
    w.cylinder(0.0, 1.10, 0.0, 0.17, 0.10, 2.20, "madeira", CASCA,
               rough=0.85, metal=0.0, seg=10)
    for sinal in (-1.0, 1.0):
        # galho de apoio inclinado (aproximacao: tres tocos em escada)
        for j, (dy, dx) in enumerate([(0.30, 0.10), (0.30, 0.14), (0.28, 0.16)]):
            y = 1.90 + j * dy
            x = sinal * (0.06 + j * dx)
            w.cylinder(x, y, 0.0, 0.055 - 0.012 * j, 0.045 - 0.010 * j,
                       dy + 0.10, "madeira", CASCA, rough=0.85, seg=8)
    # copa em cachos amarelos: anel externo + topo, todos achatados
    cachos = [
        (1.05, 2.95, 0.20, 1.15, AMARELO_A),
        (-1.00, 3.05, -0.35, 1.05, AMARELO_B),
        (0.25, 3.30, 0.85, 1.00, AMARELO_C),
        (-0.40, 3.55, -0.75, 0.95, AMARELO_A),
        (0.55, 3.75, -0.30, 0.90, AMARELO_B),
        (0.0, 4.15, 0.05, 1.10, AMARELO_C),
    ]
    for (x, y, z, raio, cor) in cachos:
        w.esfera_cachos(x, y, z, raio, "flor", cor, rough=0.85,
                        achatada=0.62, subdiv=1)
    caminho = w.write(str(REPO / "assets" / "scene" / "ipe_amarelo.glb"),
                      root_name="ipe_amarelo")
    return caminho


def conferir(caminho, altura_min, altura_max, nome_esperado):
    doc, tam_bin = ler_glb(caminho)
    assert doc["asset"]["version"] == "2.0"
    assert doc["nodes"][0]["name"] == nome_esperado, doc["nodes"]
    primitivas = doc["meshes"][0]["primitives"]
    assert len(primitivas) >= 1
    ys_min, ys_max = [], []
    for p in primitivas:
        acc = doc["accessors"][p["attributes"]["POSITION"]]
        assert acc["type"] == "VEC3" and acc["count"] % 3 == 0
        ys_min.append(acc["min"][1])
        ys_max.append(acc["max"][1])
    ymin, ymax = min(ys_min), max(ys_max)
    assert abs(ymin) < 0.02, "origem deve ficar no chao (ymin=%.3f)" % ymin
    assert altura_min <= ymax <= altura_max, \
        "altura fora da faixa: %.2f" % ymax
    print("ok  %s: %d primitivas, %d triangulos, altura %.2f m, bin %d bytes"
          % (caminho, len(primitivas),
             sum(doc["accessors"][p["attributes"]["POSITION"]]["count"]
                 for p in primitivas) // 3, ymax, tam_bin))


if __name__ == "__main__":
    b = build_barreira()
    i = build_ipe()
    conferir(b, 1.85, 2.00, "barreira")   # topo dos postes em 1,90 m
    conferir(i, 4.00, 5.30, "ipe_amarelo")
    print("ETAPA5_GLB_OK")
