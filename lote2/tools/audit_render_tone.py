#!/usr/bin/env python3
"""Auditoria de tom, paleta e nevoa do Lote 2.

Nao existe GPU/Godot no ambiente de trabalho, entao o que da para provar sem
inventar nada e a matematica: este script reproduz o caminho de tone mapping do
Godot 4.7.2 (shader effects/tonemap.glsl, tag 4.7.2: matrizes do BakingLab com
bias 1.8 + ACES, depois brilho/contraste/saturacao) e resolve a exposicao que
poe a calcada ao sol no luma da imagem de referencia. Em seguida confere se o
resto da cena cai nas faixas da referencia (sombra azulada e clara o bastante,
realce quase branco, nevoa clara sem estourar, folhagem com croma visivel).

Tambem desenha docs/preview_render_lote2.png com a curva, a paleta, a rampa de
nevoa e os degraus de qualidade, e grava docs/render_tone_report.json com a
exposicao calculada (que vai para o perfil do Lote 2).

Rode:  python3 tools/audit_render_tone.py [--quieto]
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
OUT_PNG = ROOT / "docs" / "preview_render_lote2.png"
OUT_JSON = ROOT / "docs" / "render_tone_report.json"

# --- parametros do Lote 2 (espelham scripts/game_3d_lote2_patch.gd) --------
BRIGHTNESS = 1.02
CONTRAST = 1.06
SATURATION = 0.94
TONEMAP_WHITE = 1.0
FOG_COLOR = (0.84, 0.79, 0.70)
FOG_BEGIN = 30.0
FOG_END = 260.0
FOG_DENSITY = 0.5
FOG_MODE_DEPTH = 0

# --- metas tiradas da imagem de referencia (espaco de tela, 0..1) ----------
ALVO_LAJE = 0.50                 # calcada ao sol: cinza medio
PISO_SOMBRA = 2.0 / 255.0        # a sombra mais profunda mantem algum detalhe (nao vira preto puro)
FAIXA_SOMBRA_LAJE = (0.12, 0.26)  # calcada na sombra (azulada, mas legivel)
FAIXA_NEVOA_LONGE = (0.60, 0.92)  # nevoa a 260 m: clara, mas sem estourar
FAIXA_NEVOA_PERTO = (0.25, 0.70)  # nevoa a 60 m: ainda discreta
REALCE_MIN = 0.97                # o sol precisa chegar no branco
CROMA_REALCE_MAX = 0.08          # realce quase sem cor
SEPARACAO_MIN = 0.60             # distancia entre sombra e sol
CROMA_FOLHAGEM_MIN = 0.25        # verde visivel
CROMA_MAX_SUPERFICIE = 0.80      # nada de cor de neon
FAIXA_EXPOSICAO = (0.30, 0.90)   # janela aceitavel para a exposicao resolvida

# --- amostras de cena: radiometria LINEAR, antes da exposicao --------------
# Cada valor e a radiometria RGB da superficie: albedo x luz recebida
# (sol, ou ambiente do ceu + sol difuso no caso das sombras).
AMOSTRAS = [
    ("Sol no ceu (disco)", (9.000, 8.200, 7.000), "realce"),
    ("Ceu perto do sol", (1.500, 1.420, 1.300), "realce"),
    ("Laje sob o sol", (0.330, 0.325, 0.315), "alvo"),
    ("Tijolo ao sol", (0.185, 0.115, 0.090), "superficie"),
    ("Folhagem", (0.070, 0.130, 0.055), "superficie"),
    ("Laje na sombra", (0.062, 0.075, 0.092), "superficie"),
    ("Sombra funda", (0.018, 0.022, 0.028), "sombra"),
]


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def luma(c) -> float:
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def chroma(c) -> float:
    mx, mn = max(c), min(c)
    return 0.0 if mx <= 1e-6 else (mx - mn) / mx


# Matrizes do tone mapping ACES do Godot (colunas do shader = estas linhas,
# cada linha soma 1: sao as matrizes do BakingLab/BakingLab ACES.hlsl).
RGB_TO_RRT = [
    (0.59719 * 1.8, 0.35458 * 1.8, 0.04823 * 1.8),
    (0.07600 * 1.8, 0.90834 * 1.8, 0.01566 * 1.8),
    (0.02840 * 1.8, 0.13383 * 1.8, 0.83777 * 1.8),
]
ODT_TO_RGB = [
    (1.60475, -0.53108, -0.07367),
    (-0.10208, 1.10813, -0.00605),
    (-0.00327, -0.07276, 1.07602),
]
ACE_A, ACE_B, ACE_C, ACE_D, ACE_E = 0.0245786, 0.000090537, 0.983729, 0.432951, 0.238081


def _mat3(m, v):
    return [m[i][0] * v[0] + m[i][1] * v[1] + m[i][2] * v[2] for i in range(3)]


def aces(color, white: float = TONEMAP_WHITE):
    c = _mat3(RGB_TO_RRT, color)
    c = [((v * (v + ACE_A) - ACE_B) / (v * (ACE_C * v + ACE_D) + ACE_E)) for v in c]
    c = _mat3(ODT_TO_RGB, c)
    return [v / white for v in c]


def srgb(v: float) -> float:
    return v * 12.92 if v <= 0.0031308 else 1.055 * (v ** (1 / 2.4)) - 0.055


def bcs(linear):
    """Copia do bloco FLAG_USE_BCS do main() do tonemap.glsl 4.7.2.

    Ordem real: brilho em linear -> converte para sRGB -> contraste em sRGB
    (por isso as sombras nao esmagam) -> saturacao em direcao a media dos
    canais (nao a luminancia).
    """
    c = [v * BRIGHTNESS for v in linear]
    c = [srgb(v) for v in c]
    c = [0.5 + (v - 0.5) * CONTRAST for v in c]
    media = sum(c) / 3.0
    c = [media + (v - media) * SATURATION for v in c]
    return [clamp(v) for v in c]


def pipeline(radiancia, exposure: float):
    """Radiometria linear -> exposicao -> ACES -> brilho/contraste/saturacao.

    Devolve ja em espaco de tela (sRGB 0..1), como o quadro final do Godot.
    """
    return tuple(bcs(aces([c * exposure for c in radiancia])))


def tela(radiancia, exposure: float):
    return pipeline(radiancia, exposure)


def resolve_exposicao(alvo: float = ALVO_LAJE) -> float:
    """Exposicao que poe a calcada ao sol no luma alvo da referencia."""
    rad = next(r for n, r, c in AMOSTRAS if c == "alvo")
    lo, hi = 0.05, 4.0
    for _ in range(60):
        meio = (lo + hi) / 2
        if luma(tela(rad, meio)) < alvo:
            lo = meio
        else:
            hi = meio
    return (lo + hi) / 2


def fog_factor(dist: float) -> float:
    """Environment.FOG_MODE_DEPTH com os valores do perfil do Lote 2."""
    if dist <= FOG_BEGIN:
        return 0.0
    span = max(1e-6, FOG_END - FOG_BEGIN)
    x = clamp((dist - FOG_BEGIN) / span)
    return clamp(1.0 - math.pow(1.0 - x, 2.0))


def rampa_nevoa(exposure: float, distancias=(60.0, 140.0, 260.0)):
    """Luma de tela de uma calcada cinza vista a varias distancias (com nevoa)."""
    base = [c * 0.6 for c in (0.45, 0.44, 0.42)]
    saida = []
    for dist in distancias:
        f = fog_factor(dist)
        rad = [b + (fc - b) * f for b, fc in zip(base, FOG_COLOR)]
        saida.append(luma(pipeline(rad, exposure)))
    return saida


def auditar(quieto: bool = False) -> tuple:
    problemas = []
    exposicao = resolve_exposicao()
    linhas = []
    for nome, rad, classe in AMOSTRAS:
        cor = tela(rad, exposicao)
        linhas.append((nome, classe, rad, cor, luma(cor), chroma(cor)))

    por_nome = {x[0]: x for x in linhas}
    realces = [x for x in linhas if x[1] == "realce"]
    superficies = [x for x in linhas if x[1] == "superficie"]
    mais_escura = min(x[4] for x in linhas)
    sol = max(realces, key=lambda x: x[4])
    laje_sombra = por_nome["Laje na sombra"]
    folhagem = por_nome["Folhagem"]
    rampa = rampa_nevoa(exposicao)

    def checar(condicao: bool, mensagem: str) -> None:
        if not condicao:
            problemas.append(mensagem)

    checar(FAIXA_EXPOSICAO[0] <= exposicao <= FAIXA_EXPOSICAO[1],
           f"exposicao resolvida {exposicao:.3f} fora da janela {FAIXA_EXPOSICAO}")
    pior = min(linhas, key=lambda x: x[4])
    checar(max(pior[3]) >= PISO_SOMBRA,
           f"a sombra mais profunda zerou (canal maximo {max(pior[3])*255:.0f}/255): preto puro perde detalhe")
    # detalhe preservado: dois tons escuros diferentes continuam distinguiveis
    escuro_a = tela([0.018, 0.022, 0.028], exposicao)
    escuro_b = tela([0.036, 0.044, 0.056], exposicao)
    checar(abs(luma(escuro_b) - luma(escuro_a)) * 255 >= 2.0,
           "os dois tons mais escuros ficaram indistinguiveis (detalhe perdido nas sombras)")
    checar(rampa[0] < rampa[1] < rampa[2],
           f"a rampa de nevoa nao cresce com a distancia: {[f'{v*255:.0f}' for v in rampa]}")
    checar(FAIXA_NEVOA_PERTO[0] <= rampa[0] <= FAIXA_NEVOA_PERTO[1],
           f"nevoa a 60 m em {rampa[0]*255:.0f} (esperado {FAIXA_NEVOA_PERTO[0]*255:.0f}..{FAIXA_NEVOA_PERTO[1]*255:.0f})")
    checar(FAIXA_NEVOA_LONGE[0] <= rampa[2] <= FAIXA_NEVOA_LONGE[1],
           f"nevoa a 260 m em {rampa[2]*255:.0f} (esperado {FAIXA_NEVOA_LONGE[0]*255:.0f}..{FAIXA_NEVOA_LONGE[1]*255:.0f})")
    checar(FAIXA_SOMBRA_LAJE[0] <= laje_sombra[4] <= FAIXA_SOMBRA_LAJE[1],
           f"a calcada na sombra ficou em {laje_sombra[4]*255:.0f} (esperado {FAIXA_SOMBRA_LAJE[0]*255:.0f}..{FAIXA_SOMBRA_LAJE[1]*255:.0f})")
    checar(sol[4] >= REALCE_MIN, f"o sol ficou em {sol[4]*255:.0f} (minimo {REALCE_MIN*255:.0f})")
    checar(sol[5] <= CROMA_REALCE_MAX, f"o sol tem croma {sol[5]:.3f} (maximo {CROMA_REALCE_MAX})")
    checar(sol[4] - mais_escura >= SEPARACAO_MIN,
           f"separacao sombra/sol {sol[4]-mais_escura:.3f} (minimo {SEPARACAO_MIN})")
    checar(folhagem[5] >= CROMA_FOLHAGEM_MIN,
           f"a folhagem ficou com croma {folhagem[5]:.3f} (minimo {CROMA_FOLHAGEM_MIN})")
    pior_croma = max(superficies, key=lambda x: x[5])
    checar(pior_croma[5] <= CROMA_MAX_SUPERFICIE,
           f"{pior_croma[0]} com croma {pior_croma[5]:.3f} (maximo {CROMA_MAX_SUPERFICIE})")

    if not quieto:
        print("Auditoria de tom, paleta e nevoa do Lote 2")
        print(f"  modelo: exposicao {exposicao:.3f} -> ACES white {TONEMAP_WHITE}"
              f" -> brilho {BRIGHTNESS} / contraste {CONTRAST} / saturacao {SATURATION}")
        print("  (matrizes e polinomio conferidos no shader effects/tonemap.glsl do 4.7.2)")
        print("  amostra                  radiometria         tela RGB    luma  croma")
        for nome, classe, rad, cor, lm, cr in linhas:
            print(f"  {nome:<22} ({rad[0]:5.3f},{rad[1]:5.3f},{rad[2]:5.3f})  "
                  f"{cor[0]*255:3.0f} {cor[1]*255:3.0f} {cor[2]*255:3.0f}  {lm*255:4.0f}  {cr:5.3f}  ({classe})")
        print(f"  separacao sombra/sol: {(sol[4]-mais_escura)*255:.0f} niveis")
        print("  rampa de nevoa (60/140/260 m): " + " / ".join(f"{v*255:.0f}" for v in rampa)
              + f"  |  calcada na sombra: {laje_sombra[4]*255:.0f}  |  folhagem: croma {folhagem[5]:.2f}")
        for p in problemas:
            print("  ERRO: " + p)
        print(f"  resumo: {len(problemas)} problema(s)")

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps({
        "exposicao": round(exposicao, 4),
        "tonemap_white": TONEMAP_WHITE,
        "brilho": BRIGHTNESS,
        "contraste": CONTRAST,
        "saturacao": SATURATION,
        "alvo_laje": ALVO_LAJE,
        "modelo": "Godot 4.7.2 tonemap.glsl (ACES/BakingLab, bias 1.8) + bcs",
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return problemas, linhas, exposicao


# ---------------------------------------------------------------------------
# Preview desenhado
# ---------------------------------------------------------------------------

def desenhar(linhas, exposicao) -> bool:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("  AVISO: Pillow ausente; preview nao desenhado (pip install pillow)")
        return False

    L, A = 940, 930
    img = Image.new("RGB", (L, A), (18, 21, 26))
    d = ImageDraw.Draw(img)
    f_tit = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 23)
    f_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    f_txt = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
    f_peq = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)

    def rgb255(c):
        return tuple(int(round(255 * clamp(v))) for v in c)

    d.text((28, 16), "Lote 2 - tom, paleta, nevoa e degraus de qualidade", font=f_tit, fill=(240, 238, 232))
    d.text((28, 46), "modelo do shader de tone mapping do Godot 4.7.2 (ACES + BCS)"
                     f" | exposicao resolvida: {exposicao:.3f}", font=f_peq, fill=(150, 158, 170))

    # ---- painel 1: curva de tom ----
    px, py, pw, ph = 40, 78, 860, 330
    ox, oy = px + 52, py + 46           # area interna do grafico
    ow, oh = pw - 66, ph - 66
    d.rectangle([px, py, px + pw, py + ph], fill=(25, 29, 36), outline=(60, 66, 76))
    d.text((px + 12, py + 8), "Curva de tom: entrada HDR -> saida de tela", font=f_sub, fill=(230, 226, 218))
    d.text((px + pw - 296, py + 9), "cinza: linear   azul: ACES   laranja: Lote 2",
           font=f_peq, fill=(178, 185, 195))
    for i in range(7):
        gx = ox + int(i * ow / 6)
        d.line([gx, oy, gx, oy + oh], fill=(38, 43, 52), width=1)
        d.text((gx + 2, oy + oh + 4), str(i), font=f_peq, fill=(118, 126, 138))
    for i in range(5):
        gy = oy + oh - int(i * oh / 4)
        d.line([ox, gy, ox + ow, gy], fill=(38, 43, 52), width=1)
        d.text((px + 6, gy + 2), str(i * 64), font=f_peq, fill=(118, 126, 138))
    d.text((px + pw - 74, py + ph - 20), "HDR", font=f_peq, fill=(118, 126, 138))
    d.text((px + 6, py + 30), "tela", font=f_peq, fill=(118, 126, 138))

    def curva(funcao, cor, largura):
        pontos = []
        for i in range(ow + 1):
            hdr = 9.0 * i / ow
            pontos.append((ox + i, oy + oh - int(clamp(funcao(hdr)) * oh)))
        d.line(pontos, fill=cor, width=largura)

    curva(lambda h: clamp(h / 9.0), (100, 106, 116), 1)
    curva(lambda h: clamp(luma([aces([h, h, h])[i] for i in range(3)])), (90, 160, 220), 2)
    curva(lambda h: clamp(luma(pipeline([h, h, h], exposicao))), (240, 170, 90), 3)
    for i, (nome, classe, rad, cor, lm, cr) in enumerate(linhas):
        v = min(9.0, rad[0])
        gx = ox + int(v * ow / 9.0)
        gy = oy + oh - int(clamp(lm) * oh)
        d.ellipse([gx - 4, gy - 4, gx + 4, gy + 4], fill=(255, 255, 255), outline=(30, 34, 40))
        rotulo = nome.split(" (")[0]
        if gx > ox + ow * 0.6:
            d.text((gx - 8 - 7 * len(rotulo), gy - 7), rotulo, font=f_peq, fill=(208, 212, 220))
        else:
            d.text((gx + 8, gy - 7 - 12 * (i % 2)), rotulo, font=f_peq, fill=(208, 212, 220))

    # ---- painel 2: paleta ----
    py2 = py + ph + 46
    d.text((px + 12, py2 - 24), "Paleta resultante (as amostras da imagem de referencia)",
           font=f_sub, fill=(230, 226, 218))
    largura = int(pw / len(linhas))
    for i, (nome, classe, rad, cor, lm, cr) in enumerate(linhas):
        x0 = px + i * largura
        d.rectangle([x0, py2, x0 + largura - 8, py2 + 62], fill=rgb255(cor), outline=(70, 76, 86))
        d.text((x0, py2 + 66), nome.split(" (")[0], font=f_peq, fill=(200, 205, 212))
        d.text((x0, py2 + 80), f"luma {lm*255:.0f}", font=f_peq, fill=(150, 158, 170))

    # ---- painel 3: nevoa ----
    py3 = py2 + 132
    d.text((px + 12, py3 - 22), "Nevoa de profundidade (30 m -> 260 m): a rua some no creme",
           font=f_sub, fill=(230, 226, 218))
    base_rad = [c * 0.6 for c in (0.45, 0.44, 0.42)]
    for i in range(pw + 1):
        dist = 300.0 * i / pw
        f = fog_factor(dist)
        rad = [b + (fc - b) * f for b, fc in zip(base_rad, FOG_COLOR)]
        d.line([(px + i, py3), (px + i, py3 + 52)], fill=rgb255(pipeline(rad, exposicao)), width=1)
    d.text((px + 4, py3 + 56), "0 m", font=f_peq, fill=(150, 158, 170))
    d.text((px + pw - 62, py3 + 56), "300 m", font=f_peq, fill=(150, 158, 170))

    # ---- painel 4: degraus ----
    py4 = py3 + 120
    d.text((px + 12, py4 - 22), "Degraus no Honor X8b (Mobile): o FPS decide, o quadro nao pisca",
           font=f_sub, fill=(230, 226, 218))
    degraus = [
        ("alto", 0.95, "MSAA 2x + DOF 0,75", (86, 156, 214)),
        ("medio", 0.85, "MSAA 2x + DOF 0,45", (96, 178, 140)),
        ("leve", 0.75, "sem MSAA, sem DOF", (216, 172, 92)),
        ("minimo", 0.68, "sem MSAA, sem DOF", (200, 108, 96)),
    ]
    for i, (nome, escala, extra, cor) in enumerate(degraus):
        y = py4 + i * 30
        d.text((px + 8, y + 2), nome, font=f_txt, fill=(216, 220, 226))
        d.rectangle([px + 100, y, px + 100 + int(escala * 340), y + 21], fill=cor)
        d.text((px + 110 + int(escala * 340), y + 2), f"escala 3D {escala:.2f} - {extra}",
               font=f_peq, fill=(160, 168, 180))

    d.text((28, A - 26), "preview matematico (o ambiente de trabalho nao tem GPU); "
                         "a conferencia final e no editor do Godot", font=f_peq, fill=(120, 128, 140))
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT_PNG)
    print(f"  preview: {OUT_PNG.relative_to(ROOT)}  |  relatorio: {OUT_JSON.relative_to(ROOT)}")
    return True


def main() -> int:
    quieto = "--quieto" in sys.argv
    problemas, linhas, exposicao = auditar(quieto=quieto)
    if not quieto:
        desenhar(linhas, exposicao)
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
