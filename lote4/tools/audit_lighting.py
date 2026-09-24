#!/usr/bin/env python3
"""Auditor do clima (Lote 4).

Confere o `resources/weather_spec.json`, os assets do clima (nuvens e trovao),
os numeros de luz/nevoa/tom de cada estado e o codigo do `weather_system.gd`.

O modelo de tom e o mesmo do Lote 2 (ACES matricial do Godot + brilho/contraste/
saturacao na ordem do shader), copiado de `tools/audit_render_tone.py` para o
lote poder ser auditado sozinho.

Tambem desenha `docs/preview_clima_lote4.png`.

Rode:  python3 tools/audit_lighting.py [--quieto]
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import struct
import sys
import wave
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
SPEC = ROOT / "resources" / "weather_spec.json"
KIT_SPEC = ROOT / "resources" / "world_spec.json"
KIT_SPEC_REFERENCIA = ROOT / "tests" / "fixtures" / "world_spec.json"
SCRIPT = ROOT / "scripts" / "weather_system.gd"
NUVENS = ROOT / "assets" / "textures" / "ceu" / "nuvens.png"
TROVAO = ROOT / "assets" / "audio" / "trovao.wav"
OUT_PNG = ROOT / "docs" / "preview_clima_lote4.png"

ESTADOS_ORDEM = ["limpo", "nublado", "chuva", "tempestade"]

# ---------------------------------------------------------------------------
# Modelo de tom (identico ao Lote 2 / tonemap.glsl 4.7.2)
# ---------------------------------------------------------------------------

BRIGHTNESS = 1.02
CONTRAST = 1.06
SATURATION = 0.94
TONEMAP_WHITE = 1.0
EXPOSURE = 0.506

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

# Base do Lote 2 (perfil de render) e tom medio da laje/calcada.
BASE_SOL = (1.0, 0.93, 0.80)
BASE_SOL_ENERGIA = 1.1
BASE_AMBIENTE = 0.62
BASE_NEVOA = 0.5
TOM_SOMBRA = (0.33, 0.39, 0.48)
ALBEDO_LAJE = (0.62, 0.61, 0.59)
ALBEDO_ASFALTO = (0.215, 0.215, 0.222)
# Calibracao: com 1.0 o modelo ficaria ~2x acima da ancora do Lote 2 (laje ao sol
# = luma 127 com irradiancia 0.33). Este fator alinha os dois auditores.
ESCALA_IRRADIANCIA = 0.485


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def luma(c) -> float:
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def niveis(c) -> float:
    """Luma na escala 0..255 (a mesma que o olho le num print)."""
    return luma(c) * 255.0


def _mat3(m, v):
    return [m[i][0] * v[0] + m[i][1] * v[1] + m[i][2] * v[2] for i in range(3)]


def aces(color, white: float = TONEMAP_WHITE):
    c = _mat3(RGB_TO_RRT, color)
    c = [((v * (v + ACE_A) - ACE_B) / (v * (ACE_C * v + ACE_D) + ACE_E)) for v in c]
    c = _mat3(ODT_TO_RGB, c)
    return [v / white for v in c]


def srgb(v: float) -> float:
    return v * 12.92 if v <= 0.0031308 else 1.055 * (v ** (1 / 2.4)) - 0.055


def tela(radiancia):
    c = [v * EXPOSURE for v in radiancia]
    c = aces(c)
    c = [v * BRIGHTNESS for v in c]
    c = [srgb(v) for v in c]
    c = [0.5 + (v - 0.5) * CONTRAST for v in c]
    media = sum(c) / 3.0
    c = [media + (v - media) * SATURATION for v in c]
    return tuple(clamp(v) for v in c)


def rad_sol(albedo, sol_energia: float, ambiente: float, face: float = 0.85):
    return [albedo[i] * (sol_energia * BASE_SOL[i] * face + ambiente * TOM_SOMBRA[i])
            * ESCALA_IRRADIANCIA for i in range(3)]


def rad_sombra(albedo, ambiente: float):
    return [albedo[i] * ambiente * TOM_SOMBRA[i] * ESCALA_IRRADIANCIA for i in range(3)]


def rad_relampago(albedo, sol_energia: float, ambiente: float, energia: float, cor):
    base = rad_sol(albedo, sol_energia, ambiente)
    return [base[i] + albedo[i] * energia * cor[i] * 0.85 * ESCALA_IRRADIANCIA for i in range(3)]


# ---------------------------------------------------------------------------
# Verificacoes
# ---------------------------------------------------------------------------

def checar_faixa(problemas, nome, valor, lo, hi, motivo):
    if not (lo <= valor <= hi):
        problemas.append(f"spec: {nome} = {valor} fora de {lo}..{hi} ({motivo})")


def auditar_spec(spec: dict, problemas: list, avisos: list, kit: dict) -> dict:
    if int(spec.get("versao", 0)) < 4:
        problemas.append("spec: versao antiga (esperado >= 4)")
    if int(spec.get("seed", 0)) <= 0:
        problemas.append("spec: sem semente (as pocas e os relampagos deixariam de ser reproduziveis)")

    tr = spec.get("transicoes", {})
    checar_faixa(problemas, "transicoes.molhagem_s", float(tr.get("molhagem_s", 0)), 1.0, 8.0,
                 "molhar devagar demais nao da satisfacao, rapido demais parece interruptor")
    checar_faixa(problemas, "transicoes.secagem_s", float(tr.get("secagem_s", 0)), 6.0, 60.0,
                 "secar tem de ser mais lento que molhar")
    if float(tr.get("secagem_s", 0)) <= float(tr.get("molhagem_s", 0)):
        problemas.append("spec: secagem_s precisa ser maior que molhagem_s")
    checar_faixa(problemas, "transicoes.estado_s", float(tr.get("estado_s", 0)), 2.0, 12.0,
                 "transicao de clima")
    checar_faixa(problemas, "transicoes.reaplicar_s", float(tr.get("reaplicar_s", 0)), 0.5, 5.0,
                 "o clima reaplica o estado para ganhar de quem mexer depois")

    estados = spec.get("estados", {})
    for nome in ESTADOS_ORDEM:
        if nome not in estados:
            problemas.append(f"spec: falta o estado '{nome}'")
    faltando = [n for n in ESTADOS_ORDEM if n not in estados]
    if faltando:
        return {}

    anterior = None
    for nome in ESTADOS_ORDEM:
        e = estados[nome]
        checar_faixa(problemas, f"estados.{nome}.sol_multiplicador", float(e.get("sol_multiplicador", 0)),
                     0.2, 1.05, "luz do sol por estado")
        checar_faixa(problemas, f"estados.{nome}.nevoa_multiplicador", float(e.get("nevoa_multiplicador", 0)),
                     0.9, 2.2, "nevoa por estado")
        checar_faixa(problemas, f"estados.{nome}.nuvens", float(e.get("nuvens", -1)), 0.0, 1.0, "cobertura")
        checar_faixa(problemas, f"estados.{nome}.cinza", float(e.get("cinza", -1)), 0.0, 1.0,
                     "quanto o ceu fica encoberto")
        checar_faixa(problemas, f"estados.{nome}.ambiente_multiplicador",
                     float(e.get("ambiente_multiplicador", 0)), 1.0, 1.4, "luz de ambiente")
        checar_faixa(problemas, f"estados.{nome}.molhado_alvo", float(e.get("molhado_alvo", -1)), 0.0, 1.0,
                     "molhado alvo")
        if anterior is not None:
            if float(e["sol_multiplicador"]) >= float(anterior["sol_multiplicador"]):
                problemas.append(f"spec: {nome} mais claro que o estado anterior (a severidade tem de subir)")
            if float(e["nevoa_multiplicador"]) <= float(anterior["nevoa_multiplicador"]):
                problemas.append(f"spec: {nome} com menos nevoa que o estado anterior")
            if float(e["nuvens"]) < float(anterior["nuvens"]):
                problemas.append(f"spec: {nome} com menos nuvem que o estado anterior")
            if float(e["molhado_alvo"]) < float(anterior["molhado_alvo"]):
                problemas.append(f"spec: {nome} com menos molhado que o estado anterior")
        anterior = e

    # chuva
    chuva = spec.get("chuva", {})
    malha = chuva.get("malha_m", [0, 0, 0])
    orc = chuva.get("orcamento", {})
    espessura = min(float(malha[0]), float(malha[2]))
    checar_faixa(problemas, "chuva.malha_m[espessura]", espessura, 0.005, float(orc.get("espessura_max_m", 0.04)),
                 "pingo fino: grosso demais vira graveto")
    area = chuva.get("area_m", [0, 0, 0])
    checar_faixa(problemas, "chuva.area_m[x]", float(area[0]), 30.0, 80.0, "area da chuva em volta da camera")
    checar_faixa(problemas, "chuva.altura_m", float(chuva.get("altura_m", 0)), 12.0, 40.0, "altura do volume")
    checar_faixa(problemas, "chuva.lifetime_s", float(chuva.get("lifetime_s", 0)), 0.5, 2.0, "tempo de vida")
    checar_faixa(problemas, "chuva.fixed_fps", float(chuva.get("fixed_fps", 0)), 20, 60,
                 "chuva em 30 fps e o que cabe no Adreno 610")
    for nome in ESTADOS_ORDEM:
        d = chuva.get("estados", {}).get(nome)
        if d is None:
            problemas.append(f"spec: chuva.estados.{nome} ausente")
            continue
        q = int(d.get("quantidade", -1))
        v = float(d.get("velocidade_ms", 0.0))
        inc = d.get("inclinacao", [0.0, -1.0, 0.0])
        comprimento = math.sqrt(sum(float(c) ** 2 for c in inc)) or 1.0
        if nome in ("limpo", "nublado") and q != 0:
            problemas.append(f"spec: chuva em '{nome}' deveria ser zero (tem {q})")
        if nome in ("chuva", "tempestade") and q < 400:
            problemas.append(f"spec: chuva em '{nome}' fraca demais ({q} pingos)")
        if q > int(orc.get("max_particulas_mobile", 1200)):
            problemas.append(f"spec: chuva em '{nome}' com {q} pingos estoura o orcamento do celular "
                             f"({orc.get('max_particulas_mobile')})")
        if q > 0:
            checar_faixa(problemas, f"chuva.estados.{nome}.velocidade_ms", v,
                         float(orc.get("min_velocidade_ms", 15.0)), float(orc.get("max_velocidade_ms", 40.0)),
                         "velocidade do pingo")
            if abs(float(inc[1])) / comprimento < 0.9:
                problemas.append(f"spec: chuva em '{nome}' caindo quase deitada (inclinacao {inc})")
    vel_chuva = float(chuva.get("estados", {}).get("chuva", {}).get("velocidade_ms", 0.0))
    vel_temp = float(chuva.get("estados", {}).get("tempestade", {}).get("velocidade_ms", 0.0))
    if vel_temp <= vel_chuva:
        problemas.append("spec: tempestade tem de chover mais rapido que a chuva")

    # relampago
    rel = spec.get("relampago", {})
    faixa = rel.get("intervalo_s", [0, 0])
    checar_faixa(problemas, "relampago.intervalo_s[min]", float(faixa[0]), 2.0, 20.0, "tempo entre raios")
    if float(faixa[1]) < float(faixa[0]) * 1.5:
        problemas.append("spec: intervalo do relampago curto demais entre min e max (fica metralhadora)")
    checar_faixa(problemas, "relampago.quadros_aceso", float(rel.get("quadros_aceso", 0)), 1, 6,
                 "o raio tem de ser um piscar")
    checar_faixa(problemas, "relampago.energia_pico", float(rel.get("energia_pico", 0)), 1.2, 4.0,
                 "energia da luz do raio")
    checar_faixa(problemas, "relampago.tira_alpha", float(rel.get("tira_alpha", 0)), 0.05, 0.35,
                 "veu branco na tela")
    for nome in rel.get("estados", []):
        if nome not in estados:
            problemas.append(f"spec: relampago no estado inexistente '{nome}'")
            continue
        if float(estados[nome].get("nuvens", 0)) < 0.8 or float(estados[nome].get("sol_multiplicador", 1)) > 0.5:
            problemas.append(f"spec: relampago em '{nome}' sem ceu carregado o bastante")
    trovejar = rel.get("trovejar", {})
    atraso = trovejar.get("atraso_s", [0, 0])
    checar_faixa(problemas, "relampago.trovejar.atraso_s[min]", float(atraso[0]), 0.2, 5.0,
                 "o trovao chega depois da luz")
    volume = trovejar.get("volume_db", [0, 0])
    checar_faixa(problemas, "relampago.trovejar.volume_db[max]", float(volume[1]), -30.0, -1.0,
                 "o trovao nao pode estourar o mix")

    # molhado
    molhado = spec.get("molhado", {})
    tabela = molhado.get("materiais", {})
    albedo_minimo = float(molhado.get("albedo_minimo", 0.35))
    materiais_kit = kit.get("materiais", {})
    for nome, cfg in tabela.items():
        if materiais_kit and nome not in materiais_kit:
            problemas.append(f"spec: molhado.materiais.{nome} nao existe no world_spec (nome errado?)")
        r_seca = float(cfg.get("rugosidade_seca", 0))
        r_molhada = float(cfg.get("rugosidade_molhada", 0))
        if r_molhada >= r_seca:
            problemas.append(f"spec: molhado.materiais.{nome} fica MAIS fosco molhado "
                             f"({r_molhada} >= {r_seca})")
        a = float(cfg.get("albedo_molhado", 1.0))
        if a < albedo_minimo:
            problemas.append(f"spec: molhado.materiais.{nome} escurece demais molhado "
                             f"({a} < {albedo_minimo})")
        if a >= 1.0:
            problemas.append(f"spec: molhado.materiais.{nome} nao escurece nada molhado")
        checar_faixa(problemas, f"molhado.materiais.{nome}.especular_extra",
                     float(cfg.get("especular_extra", 0.0)), 0.0, 0.3, "brilho extra do molhado")
    for obrigatorio in ("pista", "linha_amarela", "piso_central", "calcada_lateral"):
        if obrigatorio not in tabela:
            problemas.append(f"spec: molhado.materiais.{obrigatorio} e obrigatorio")
    pista = tabela.get("pista", {})
    if float(pista.get("rugosidade_molhada", 1)) > 0.2:
        problemas.append("spec: asfalto molhado tem de ficar bem liso (rugosidade <= 0.2)")

    # pocas
    pocas = spec.get("pocas", {})
    trecho_pocas = float(pocas.get("trecho_m", 0.0)) if "trecho_m" in pocas else None
    trecho_kit = float(kit.get("quarteirao", {}).get("comprimento_m", 0.0))
    if trecho_pocas is not None and abs(trecho_pocas - trecho_kit) > 0.5:
        problemas.append(f"spec: pocas.trecho_m ({trecho_pocas}) tem de casar com o quarteirao do "
                         f"world_spec ({trecho_kit})")
    visiveis = int(pocas.get("quantidade_por_trecho", 0)) * max(1, int(pocas.get("trechos_a_vista", 1)))
    limite_pocas = int(spec.get("orcamento", {}).get("max_pocas_visiveis", 48))
    if visiveis > limite_pocas:
        problemas.append(f"spec: {visiveis} pocas visiveis estoura o orcamento ({limite_pocas})")
    checar_faixa(problemas, "pocas.rugosidade", float(pocas.get("rugosidade", 1)), 0.02, 0.12,
                 "poca e espelho: rugosidade baixa")
    if luma(pocas.get("cor", [1, 1, 1])[:3]) > 0.12:
        problemas.append("spec: poca clara demais (a agua parada e escura)")
    checar_faixa(problemas, "pocas.aparecer_em", float(pocas.get("aparecer_em", 0)), 0.3, 0.7,
                 "a poca so aparece quando molha de verdade")

    # sonda e orcamento
    sonda = spec.get("sonda", {})
    tam = sonda.get("tamanho_m", [0, 0, 0])
    sonda_max = float(spec.get("orcamento", {}).get("sonda_max_m", 64.0))
    if max(float(tam[0]), float(tam[1]), float(tam[2])) > sonda_max:
        problemas.append(f"spec: sonda maior que {sonda_max} m (custo alto no celular)")
    if bool(sonda.get("ativo_mobile", False)):
        avisos.append("AVISO: sonda de reflexo ligada no mobile (custo alto no Adreno 610)")
    checar_faixa(problemas, "sonda.intensidade", float(sonda.get("intensidade", 0)), 0.2, 0.9,
                 "intensidade da sonda")
    if int(spec.get("orcamento", {}).get("max_particulas_mobile", 99999)) > 1500:
        problemas.append("spec: orcamento de particulas acima do teto do Adreno 610 (1500)")
    if int(spec.get("orcamento", {}).get("max_luzes_extras", 9)) > 1:
        problemas.append("spec: mais de uma luz extra (o Adreno 610 nao aguenta)")

    # ceu
    ceu = spec.get("ceu", {})
    # ceu encoberto de verdade: mais claro no horizonte que no alto (luz espalhada)
    if luma(ceu.get("sobrecast_cor_horizonte", [0, 0, 0])[:3]) <= luma(ceu.get("sobrecast_cor_alto", [1, 1, 1])[:3]):
        problemas.append("spec: ceu encoberto com o horizonte mais escuro que o alto "
                         "(tempestade tem faixa clara no horizonte)")
    checar_faixa(problemas, "ceu.energia_minima", float(ceu.get("energia_minima", 0)), 0.3, 1.0,
                 "energia minima do ceu na tempestade")

    # mapa de capitulos
    mapa = spec.get("mapa_capitulo", [])
    paletas = kit.get("paletas", [])
    if paletas and len(mapa) != len(paletas):
        problemas.append(f"spec: mapa_capitulo com {len(mapa)} itens e o world_spec com "
                         f"{len(paletas)} paletas")
    for nome in mapa:
        if nome not in estados:
            problemas.append(f"spec: mapa_capitulo aponta para estado inexistente '{nome}'")
    return estados


def auditar_tom(spec: dict, estados: dict, problemas: list) -> list:
    """Amostra o tom de 4 cenas: sol limpo, sol na tempestade, sombra e o pico do raio."""
    rel = spec.get("relampago", {})
    cor_raio = rel.get("cor", [0.85, 0.9, 1.0])[:3]
    amostras = []

    def amostrar(nome, rad):
        cor = tela(rad)
        amostras.append((nome, cor, niveis(cor)))

    e_limpo = estados.get("limpo", {})
    e_temp = estados.get("tempestade", {})
    sol_limpo = BASE_SOL_ENERGIA * float(e_limpo.get("sol_multiplicador", 1.0))
    amb_limpo = BASE_AMBIENTE * float(e_limpo.get("ambiente_multiplicador", 1.0))
    sol_temp = BASE_SOL_ENERGIA * float(e_temp.get("sol_multiplicador", 1.0))
    amb_temp = BASE_AMBIENTE * float(e_temp.get("ambiente_multiplicador", 1.0))

    amostrar("Laje ao sol (limpo)", rad_sol(ALBEDO_LAJE, sol_limpo, amb_limpo))
    amostrar("Laje ao sol (tempestade)", rad_sol(ALBEDO_LAJE, sol_temp, amb_temp))
    amostrar("Laje na sombra (tempestade)", rad_sombra(ALBEDO_LAJE, amb_temp))
    amostrar("Asfalto molhado (tempestade)", rad_sol(ALBEDO_ASFALTO, sol_temp, amb_temp))
    amostrar("Pico do relampago", rad_relampago(ALBEDO_LAJE, sol_temp, amb_temp,
                                                float(rel.get("energia_pico", 2.4)), cor_raio))

    valores = {nome: valor for nome, _cor, valor in amostras}
    claro = valores["Laje ao sol (limpo)"]
    tempestade = valores["Laje ao sol (tempestade)"]
    sombra = valores["Laje na sombra (tempestade)"]
    raio = valores["Pico do relampago"]

    if tempestade >= claro:
        problemas.append("tom: a tempestade nao escureceu a rua (sol_multiplicador nao esta fazendo efeito)")
    razao = tempestade / max(1e-6, claro)
    if not (0.40 <= razao <= 0.80):
        problemas.append(f"tom: tempestade com {razao:.2f} do brilho do ceu limpo (esperado 0.40..0.80)")
    if tempestade < 45:
        problemas.append(f"tom: rua na tempestade escura demais (luma {tempestade:.0f} < 45)")
    if sombra < 12:
        problemas.append(f"tom: sombra da tempestade esmagada (luma {sombra:.0f} < 12)")
    if raio > 252:
        problemas.append(f"tom: pico do relampago estoura em branco puro (luma {raio:.0f} > 252)")
    if raio < tempestade + 40:
        problemas.append(f"tom: relampago fraco (ganha so {raio - tempestade:.0f} niveis)")
    # o veu branco (tira_alpha) na tela tem de dar um clarao visivel sem cegar
    alpha = float(rel.get("tira_alpha", 0.2))
    tempestade_cor = next(c for n, c, _v in amostras if n == "Laje ao sol (tempestade)")
    clarao = niveis(tuple(tempestade_cor[i] * (1.0 - alpha) + alpha for i in range(3)))
    if clarao < 90:
        problemas.append(f"tom: o clarao do relampago quase nao aparece (luma {clarao:.0f} < 90)")
    if clarao > 240:
        problemas.append(f"tom: o clarao do relampago cega (luma {clarao:.0f} > 240)")
    amostras.append(("Clarao na tela (raio)", (clarao / 255.0, clarao / 255.0, clarao / 255.0), clarao))
    return amostras


def auditar_assets(problemas: list, avisos: list) -> dict:
    info = {}
    if not NUVENS.exists():
        problemas.append("asset: falta assets/textures/ceu/nuvens.png (rode tools/generate_clouds.py)")
    else:
        try:
            from PIL import Image
        except ImportError:
            avisos.append("AVISO: Pillow ausente; nuvens nao conferidas (pip install pillow)")
        else:
            img = Image.open(NUVENS)
            w, h = img.size
            px = img.convert("RGB").load()
            if abs(w - 2 * h) > 2:
                problemas.append(f"asset: nuvens {w}x{h} nao e equirretangular 2:1")
            if w < 512:
                problemas.append(f"asset: nuvens pequenas demais ({w} px de largura)")
            emenda = sum(abs(px[0, y][0] - px[w - 1, y][0]) for y in range(h)) / max(1, h)
            lums = sorted(px[x, y][0] for y in range(0, h, 4) for x in range(0, w, 4))
            n = len(lums)
            p05, p95 = lums[n // 20], lums[n * 19 // 20]
            if emenda > 3.0:
                problemas.append(f"asset: nuvens com emenda no horizontal ({emenda:.1f}/255)")
            if p95 - p05 < 80:
                problemas.append(f"asset: nuvens sem contraste (p95-p05 = {p95 - p05})")
            if p95 > 200:
                problemas.append(f"asset: nuvens claras demais (p95 = {p95}); como a cor e SOMADA ao ceu, "
                                 "isso estoura o ceu")
            info["nuvens"] = {"tamanho": (w, h), "emenda": emenda, "p05": p05, "p95": p95,
                              "bytes": NUVENS.stat().st_size}
    if not TROVAO.exists():
        problemas.append("asset: falta assets/audio/trovao.wav (rode tools/generate_thunder.py)")
    else:
        with wave.open(str(TROVAO)) as w:
            n = w.getnframes()
            vals = struct.unpack(f"<{n}h", w.readframes(n))
            taxa = w.getframerate()
            canais = w.getnchannels()
            bits = w.getsampwidth() * 8
            dur = n / taxa
            pico = max(abs(v) for v in vals) / 32767
            rms = (sum(v * v for v in vals) / n) ** 0.5 / 32767
            estalo = (sum(v * v for v in vals[:n // 8]) / max(1, n // 8)) ** 0.5 / 32767
            cauda = (sum(v * v for v in vals[n // 2:]) / max(1, n - n // 2)) ** 0.5 / 32767
        if taxa != 44100 or canais != 1 or bits != 16:
            problemas.append(f"asset: trovao em {taxa} Hz/{canais} canais/{bits} bits "
                             "(esperado 44100/mono/16)")
        if not (2.0 <= dur <= 4.0):
            problemas.append(f"asset: trovao com {dur:.1f}s (esperado 2,0 a 4,0 s)")
        if not (0.75 <= pico <= 0.95):
            problemas.append(f"asset: pico do trovao em {pico:.2f} (esperado 0,75 a 0,95)")
        if cauda < 0.02:
            problemas.append(f"asset: sem estrondo no trovao (cauda rms {cauda:.3f})")
        if estalo <= cauda:
            problemas.append("asset: falta o estalo do raio (a primeira parte tem de ser mais forte)")
        info["trovao"] = {"dur": dur, "pico": pico, "rms": rms, "estalo": estalo, "cauda": cauda}
    return info


VALORES_PROIBIDOS = ["22.0", "30.0", "1150", "700", "2.4", "0.14", "0.12"]


def auditar_script(texto: str, problemas: list, avisos: list) -> None:
    if "weather_spec.json" not in texto:
        problemas.append("script: caminho do weather_spec.json ausente")
    if "RandomNumberGenerator" not in texto or "_rng.seed = " not in texto:
        problemas.append("script: o gerador global precisa da semente do spec (_rng.seed = ...); "
                         "sem ela as pocas e os relampagos mudam a cada partida")
    if "randomize()" in texto:
        problemas.append("script: randomize() quebra o determinismo (use _rng com semente do spec)")
    if re.search(r"(?<![\w.])randf\(", texto) or re.search(r"(?<![\w.])randi\(", texto):
        problemas.append("script: randf()/randi() globais: use o _rng com semente")
    for exigido, motivo in (
        ("GPUParticles3D", "chuva em GPU"),
        ("ParticleProcessMaterial", "material da chuva"),
        ("MultiMesh", "as pocas tem de ir em MultiMesh"),
        ("visibility_aabb", "o volume da chuva precisa de AABB (senao some)"),
        ("local_coords", "a chuva acompanha a camera"),
        ("max_particulas_mobile", "a chuva respeita o orcamento do celular"),
        ("get_wetness", "o Lote 5 (fisica) vai consumir isto"),
        ("set_state", "troca de clima"),
        ("BuildingKit.material", "o molhado mexe nos materiais do kit (nomes tem de casar)"),
        ("ResourceLoader.exists", "assets do clima precisam de guarda"),
    ):
        if exigido not in texto:
            problemas.append(f"script: falta {exigido} ({motivo})")
    for num, linha in enumerate(texto.splitlines(), start=1):
        if "sky_cover" in linha and re.search(r"sky_cover\s*=\s*[-+0-9.]", linha):
            problemas.append(f"script linha {num}: sky_cover e Texture2D, nao numero "
                             "(a intensidade vai na sky_cover_modulate)")
    if "volumetric" in texto and "forward_plus" not in texto:
        problemas.append("script: mexe em nevoa volumetrica sem guardar por renderizador "
                         "(so existe no Forward+)")
    for valor in VALORES_PROIBIDOS:
        padrao = re.compile(r"(?<![\d.])" + re.escape(valor) + r"(?![\d])")
        if padrao.search(texto):
            problemas.append(f"script: numero de clima fixo no codigo ({valor}); isso pertence ao spec")
    if 'print("[clima]' not in texto:
        avisos.append("AVISO: o clima nao registra nada no painel Saida")


def desenhar(spec, estados, tom, assets, trecho_kit: float = 28.0) -> bool:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("  AVISO: Pillow ausente; preview nao desenhado")
        return False
    L, A = 960, 1080
    img = Image.new("RGB", (L, A), (18, 21, 26))
    d = ImageDraw.Draw(img)
    F = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    f_tit = ImageFont.truetype(FB, 23)
    f_sub = ImageFont.truetype(FB, 16)
    f_txt = ImageFont.truetype(F, 14)
    f_peq = ImageFont.truetype(F, 12)
    px, pw = 40, 880

    d.text((28, 16), "Lote 4 - clima: chuva, molhado, relampago e tom", font=f_tit, fill=(240, 238, 232))
    d.text((28, 46), f"exposicao {EXPOSURE:.3f} | umidade: molha em {spec['transicoes']['molhagem_s']}s, "
                     f"seca em {spec['transicoes']['secagem_s']}s | seed {spec['seed']}",
           font=f_peq, fill=(150, 158, 170))

    # painel 1: estados
    py = 80
    d.rectangle([px, py, px + pw, py + 208], fill=(25, 29, 36), outline=(60, 66, 76))
    d.text((px + 12, py + 8), "Estados de clima (barras normalizadas por parametro)", font=f_sub,
           fill=(230, 226, 218))
    chaves = [("sol_multiplicador", "sol", (232, 196, 120)),
              ("nevoa_multiplicador", "nevoa", (200, 205, 214)),
              ("nuvens", "nuvens", (170, 178, 190)),
              ("cinza", "cinza", (150, 156, 168)),
              ("molhado_alvo", "molhado", (110, 170, 220))]
    x0 = px + 120
    largura = 130
    for i, (chave, rotulo, cor) in enumerate(chaves):
        d.text((px + 12, py + 40 + i * 32), rotulo, font=f_txt, fill=(210, 214, 222))
        for j, nome in enumerate(ESTADOS_ORDEM):
            v = float(estados[nome].get(chave, 0.0))
            base = float(estados["tempestade"].get(chave, 1.0)) or 1.0
            fracao = clamp(v / base if chave in ("sol_multiplicador", "nevoa_multiplicador") else v)
            bx = x0 + j * (largura + 60)
            d.rectangle([bx, py + 44 + i * 32, bx + largura, py + 58 + i * 32], fill=(40, 45, 54))
            d.rectangle([bx, py + 44 + i * 32, bx + int(largura * fracao), py + 58 + i * 32], fill=cor)
            d.text((bx, py + 30 + i * 32), nome, font=f_peq, fill=(170, 176, 186))
            d.text((bx + largura + 6, py + 44 + i * 32), f"{v:.2f}", font=f_peq, fill=(190, 196, 206))

    # painel 2: chuva
    py2 = py + 232
    d.rectangle([px, py2, px + pw, py2 + 130], fill=(25, 29, 36), outline=(60, 66, 76))
    d.text((px + 12, py2 + 8), "Chuva (pingos por estado; linha branca = orcamento do Adreno 610)",
           font=f_sub, fill=(230, 226, 218))
    teto = int(spec["chuva"]["orcamento"]["max_particulas_mobile"])
    # linha branca = teto de particulas do Adreno 610
    y_teto = py2 + 96 - 70
    d.line([px + 16, y_teto, px + pw - 16, y_teto], fill=(240, 240, 245))
    d.text((px + pw - 132, y_teto - 14), f"teto {teto}", font=f_peq, fill=(230, 230, 238))
    for j, nome in enumerate(ESTADOS_ORDEM):
        q = int(spec["chuva"]["estados"][nome]["quantidade"])
        bx = px + 20 + j * 210
        alt = 70
        d.rectangle([bx, py2 + 96 - alt, bx + 60, py2 + 96], fill=(40, 45, 54))
        h = int(alt * min(1.0, q / teto))
        d.rectangle([bx, py2 + 96 - h, bx + 60, py2 + 96], fill=(120, 170, 220))
        d.text((bx, py2 + 32), nome, font=f_txt, fill=(210, 214, 222))
        d.text((bx, py2 + 100), f"{q} pingos", font=f_peq, fill=(190, 196, 206))
        v = float(spec["chuva"]["estados"][nome]["velocidade_ms"])
        inc = spec["chuva"]["estados"][nome]["inclinacao"]
        d.text((bx + 70, py2 + 40), f"{v:.0f} m/s" if v > 0 else "sem chuva", font=f_peq, fill=(170, 176, 186))
        d.text((bx + 70, py2 + 56), f"inc {inc[0]:.2f}", font=f_peq, fill=(150, 156, 168))

    # painel 3: asfalto seco x molhado
    py3 = py2 + 154
    d.rectangle([px, py3, px + pw, py3 + 150], fill=(25, 29, 36), outline=(60, 66, 76))
    d.text((px + 12, py3 + 8), "Asfalto: seco x molhado (rugosidade e brilho especular)", font=f_sub,
           fill=(230, 226, 218))
    pista = spec["molhado"]["materiais"]["pista"]
    r_seca, r_molhada = float(pista["rugosidade_seca"]), float(pista["rugosidade_molhada"])
    brilho_seco = (1.0 - r_seca) ** 4
    brilho_molhado = ((1.0 - r_molhada) ** 4) * (1.0 + float(pista["especular_extra"]) / 0.5)
    d.text((px + 12, py3 + 40), "rugosidade", font=f_txt, fill=(210, 214, 222))
    for j, (rot, val) in enumerate((("seco", r_seca), ("molhado", r_molhada))):
        bx = px + 130 + j * 250
        d.rectangle([bx, py3 + 40, bx + 200, py3 + 58], fill=(40, 45, 54))
        d.rectangle([bx, py3 + 40, bx + int(200 * val), py3 + 58], fill=(150, 156, 168))
        d.text((bx + 206, py3 + 42), f"{rot} {val:.2f}", font=f_peq, fill=(190, 196, 206))
    d.text((px + 12, py3 + 76), "brilho especular", font=f_txt, fill=(210, 214, 222))
    for j, (rot, val) in enumerate((("seco", brilho_seco), ("molhado", brilho_molhado))):
        bx = px + 130 + j * 250
        larg = int(200 * min(1.0, val / max(brilho_seco, brilho_molhado, 1e-6)))
        d.rectangle([bx, py3 + 76, bx + 200, py3 + 94], fill=(40, 45, 54))
        d.rectangle([bx, py3 + 76, bx + larg, py3 + 94], fill=(120, 190, 230))
        d.text((bx + 206, py3 + 78), f"{rot} {val:.2f}", font=f_peq, fill=(190, 196, 206))
    ganho = brilho_molhado / max(brilho_seco, 1e-6)
    trecho_mostrado = trecho_kit if trecho_kit > 0 else 28.0
    d.text((px + 12, py3 + 112), f"ganho do molhado: {ganho:.1f}x  |  pocas: "
                                 f"{spec['pocas']['quantidade_por_trecho']} por trecho de "
                                 f"{trecho_mostrado:.0f} m, rugosidade {spec['pocas']['rugosidade']}",
           font=f_peq, fill=(170, 176, 186))

    # painel 4: tom
    py4 = py3 + 174
    d.rectangle([px, py4, px + pw, py4 + 150], fill=(25, 29, 36), outline=(60, 66, 76))
    d.text((px + 12, py4 + 8), "Tom (mesmo modelo ACES do Lote 2): cenas de chuva e o pico do raio",
           font=f_sub, fill=(230, 226, 218))
    for i, (nome, cor, valor) in enumerate(tom):
        y = py4 + 34 + i * 22
        d.rectangle([px + 12, y, px + 44, y + 18],
                    fill=tuple(int(255 * clamp(c)) for c in cor))
        d.text((px + 54, y + 2), nome, font=f_txt, fill=(210, 214, 222))
        d.text((px + 320, y + 2), f"luma {valor:.0f}", font=f_txt, fill=(230, 226, 218))

    # painel 5: assets
    py5 = py4 + 174
    d.rectangle([px, py5, px + pw, py5 + 168], fill=(25, 29, 36), outline=(60, 66, 76))
    d.text((px + 12, py5 + 8), "Assets do clima (gerados por tools/, determinísticos)", font=f_sub,
           fill=(230, 226, 218))
    if NUVENS.exists():
        try:
            from PIL import Image as _Im
            mini = _Im.open(NUVENS).convert("RGB").resize((200, 100))
            img.paste(mini, (px + 12, py5 + 36))
            info = assets.get("nuvens", {})
            d.text((px + 224, py5 + 38), f"nuvens.png {info.get('tamanho', '')} | "
                                         f"emenda {info.get('emenda', 0):.2f}/255 | "
                                         f"p05 {info.get('p05')} p95 {info.get('p95')}", font=f_peq,
                   fill=(190, 196, 206))
        except Exception:
            pass
    if TROVAO.exists():
        with wave.open(str(TROVAO)) as w:
            n = w.getnframes()
            vals = struct.unpack(f"<{n}h", w.readframes(n))
        pontos = 220
        passo = max(1, n // pontos)
        x0, y0, hgt = px + 224, py5 + 108, 26
        anterior = None
        for i in range(0, min(n, pontos * passo), passo):
            v = abs(vals[i]) / 32767
            x = x0 + int((i / n) * 300)
            y = y0 + hgt - int(hgt * v)
            if anterior is not None:
                d.line([anterior, (x, y)], fill=(150, 200, 240), width=1)
            anterior = (x, y)
        info = assets.get("trovao", {})
        d.text((px + 224, py5 + 64), f"trovao.wav {info.get('dur', 0):.1f}s | pico {info.get('pico', 0):.2f} | "
                                     f"estalo {info.get('estalo', 0):.2f} / cauda {info.get('cauda', 0):.2f}",
               font=f_peq, fill=(190, 196, 206))
        d.text((px + 224, py5 + 92), "envoltoria do trovao (estalo -> estrondo)", font=f_peq,
               fill=(150, 156, 168))

    resumo = hashlib.sha1(json.dumps(spec, sort_keys=True).encode()).hexdigest()[:12]
    d.text((28, A - 26), f"hash do clima: {resumo} - preview matematico, sem GPU", font=f_peq,
           fill=(120, 128, 140))
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT_PNG)
    print(f"  preview: {OUT_PNG.relative_to(ROOT)}")
    return True


KIT_SPEC_TEXTO = ""


def main() -> int:
    global KIT_SPEC_TEXTO
    problemas: list = []
    avisos: list = []
    if not SPEC.exists():
        print(f"ERRO: {SPEC} nao encontrado")
        return 1
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    caminho_kit = KIT_SPEC if KIT_SPEC.exists() else KIT_SPEC_REFERENCIA
    kit = json.loads(caminho_kit.read_text(encoding="utf-8")) if caminho_kit.exists() else {}
    if kit:
        KIT_SPEC_TEXTO = caminho_kit.read_text(encoding="utf-8")
        if caminho_kit != KIT_SPEC:
            avisos.append(f"AVISO: usando a copia de referencia do Lote 3 ({caminho_kit.relative_to(ROOT)}); "
                          "no projeto de verdade ele vem de resources/world_spec.json")
    estados = auditar_spec(spec, problemas, avisos, kit)
    tom = auditar_tom(spec, estados, problemas) if estados else []
    assets = auditar_assets(problemas, avisos)
    if SCRIPT.exists():
        auditar_script(SCRIPT.read_text(encoding="utf-8"), problemas, avisos)
    else:
        avisos.append("AVISO: weather_system.gd nao encontrado nesta copia")

    quieto = "--quieto" in sys.argv
    print("Auditor do clima (Lote 4)")
    print(f"  spec: {SPEC.name} v{spec.get('versao')} | seed {spec.get('seed')} | "
          f"{len(estados)} estados | orcamento {spec.get('orcamento', {}).get('max_particulas_mobile')} pingos")
    for nome, _cor, valor in tom:
        print(f"  tom: {nome} = {valor:.0f}")
    for chave, info in assets.items():
        if chave == "nuvens":
            print(f"  nuvens: {info['tamanho'][0]}x{info['tamanho'][1]} | emenda {info['emenda']:.2f}/255 | "
                  f"contraste {info['p95'] - info['p05']}")
        else:
            print(f"  trovao: {info['dur']:.1f}s | pico {info['pico']:.2f} | cauda {info['cauda']:.3f}")
    for a in sorted(set(avisos)):
        print("  " + a)
    for p in problemas:
        print("  ERRO: " + p)
    print(f"  resumo: {len(problemas)} problema(s), {len(set(avisos))} aviso(s)")
    if not quieto:
        desenhar(spec, estados, tom, assets,
                 float(kit.get("quarteirao", {}).get("comprimento_m", 28.0)))
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
