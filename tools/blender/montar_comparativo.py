#!/usr/bin/env python3
"""Empilha PNGs verticalmente (comparativos antes/depois das fases do herói).

O primeiro arquivo fica em CIMA. Usa só a API de imagem do Blender — o sandbox
não tem Pillow.

Uso: tools/blender/run_bpy.sh tools/blender/montar_comparativo.py a.png b.png [...] saida.png
"""
import sys

import bpy


def montar(entradas, saida):
    imgs = [bpy.data.images.load(p) for p in entradas]
    largura = max(i.size[0] for i in imgs)
    altura = sum(i.size[1] for i in imgs)
    px = [0.0] * (largura * altura * 4)
    # A origem do buffer do Blender é o canto inferior esquerdo: para o
    # primeiro arquivo aparecer em cima, empilhamos de trás para frente.
    y = 0
    for img in reversed(imgs):
        sw, sh = img.size
        sp = list(img.pixels)
        for linha in range(sh):
            destino = ((y + linha) * largura) * 4
            origem = (linha * sw) * 4
            px[destino:destino + sw * 4] = sp[origem:origem + sw * 4]
        y += sh
    out = bpy.data.images.new("comparativo", largura, altura)
    out.pixels = px
    out.filepath_raw = saida
    out.file_format = "PNG"
    out.save()
    print(f"[comparativo] {saida} ({largura}x{altura})")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a.endswith(".png")]
    if len(args) < 3:
        raise SystemExit("uso: montar_comparativo.py <a.png> <b.png> [...] <saida.png>")
    montar(args[:-1], args[-1])
