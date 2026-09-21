#!/usr/bin/env python3
"""Gera o som do trovao do clima (assets/audio/trovao.wav).

Estrutura (como um trovao de verdade):
  - estalo: 0,15 s de ruido agudo com queda rapida (o "clack" do raio);
  - estrondo: 2,4 s de ruido grave com dois inchos (o rolar no ceu);
  - distancia: o grave vem depois, entao o estalo e mais curto que o estrondo.

Deterministico (semente fixa) e sem dependencia de audio externa.

Rode:  python3 tools/generate_thunder.py
Saida: assets/audio/trovao.wav (44100 Hz, mono, 16 bits)
"""

from __future__ import annotations

import math
import random
import struct
import sys
import wave
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "assets" / "audio" / "trovao.wav"

TAXA = 44100
DURACAO = 2.6
SEMENTE = 20260918
PICO = 0.89          # -1 dBFS: pico alto sem estourar


def main() -> int:
    rng = random.Random(SEMENTE)
    n = int(TAXA * DURACAO)
    amostras = [0.0] * n
    # filtros simples de um polo (passa-baixa) e diferenca (passa-alta)
    lp1 = 0.0
    lp2 = 0.0
    anterior = 0.0
    for i in range(n):
        t = i / TAXA
        branco = rng.uniform(-1.0, 1.0)
        # ---- estalo (15 a 200 ms): agudo, decai rapido
        if t < 0.22:
            agudo = branco - anterior          # passa-alta grosseira
            env = math.exp(-t / 0.045)
            amostras[i] += agudo * env * 0.72
        anterior = branco
        # ---- estrondo (100 ms a 2,6 s): grave, com dois inchos
        lp1 += (branco - lp1) * 0.035          # ~250 Hz
        lp2 += (lp1 - lp2) * 0.035             # ~120 Hz, bem grave
        if t > 0.1:
            env = math.exp(-(t - 0.1) / 1.15)
            inchos = 1.0 + 0.45 * math.sin((t - 0.1) * 11.0) + 0.3 * math.sin((t - 0.1) * 4.3)
            amostras[i] += lp2 * env * inchos * 6.2
            amostras[i] += lp1 * env * 0.5
    # normaliza no pico e converte para 16 bits
    pico = max(abs(a) for a in amostras) or 1.0
    escala = PICO / pico
    quadros = bytearray()
    for a in amostras:
        v = int(max(-1.0, min(1.0, a * escala)) * 32767)
        quadros += struct.pack("<h", v)
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(SAIDA), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(TAXA)
        w.writeframes(bytes(quadros))
    print(f"trovao: {SAIDA.relative_to(RAIZ)} ({DURACAO}s, {TAXA} Hz, mono, "
          f"{SAIDA.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
