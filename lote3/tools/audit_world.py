#!/usr/bin/env python3
"""Auditor do cenario (Lote 3).

Confere tres coisas:

1. A ESPECIFICACAO (resources/world_spec.json): medidas dentro das faixas da
   imagem de referencia, materiais que existem no Lote 1, orcamento de malhas,
   paletas completas e coerentes (sol quente, sombra fria).

2. O LEIAUTE que a especificacao produz: um espelho em Python do preenchimento
   do quarteirao (lajes, lotes, mobilio) que prova as invariantes - nada dentro
   da faixa de corrida, espacamento dos postes e das arvores, lotes que fecham
   o quarteirao, tudo dentro do limite lateral. O espelho NAO tenta reproduzir
   bit a bit o RandomNumberGenerator do Godot (algoritmo diferente): o que se
   garante e que o gerador do jogo usa a mesma semente do spec, e isso e
   conferido por analise estatica do building_kit.gd.

3. O CODIGO do kit: materiais via ORMMaterial3D, MultiMesh para o que se
   repete, semente fixa, nenhuma medida solta, metas para o Lote 5.

Tambem desenha docs/preview_world_lote3.png (corte transversal, planta de dois
quarteiroes, tabela de materiais e paletas).

Rode:  python3 tools/audit_world.py [--quieto]
"""

from __future__ import annotations

import hashlib
import json
import random
import re
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
SPEC = ROOT / "resources" / "world_spec.json"
KIT = ROOT / "scripts" / "building_kit.gd"
FACTS = TOOLS / "world_facts.json"
OUT_PNG = ROOT / "docs" / "preview_world_lote3.png"

# Materiais que o Lote 1 gera (assets/textures/pbr/<nome>_{albedo,normal,orm}.png).
MATERIAIS_LOTE1 = {
    "asfalto", "laje_cobertura", "calcada_laje", "tijolo", "calcada_mosaico",
    "reboco", "metal_pintado", "metal_zincado", "madeira", "terra_vermelha",
}

# Cor aproximada de cada material, so para desenhar o preview (o visual real vem
# das texturas PBR do projeto).
CORES_APROX = {
    "calcada_laje": (150, 148, 143),
    "calcada_mosaico": (168, 166, 160),
    "asfalto": (58, 58, 60),
    "metal_pintado": (196, 168, 24),
    "tijolo": (150, 88, 66),
    "reboco": (198, 190, 176),
    "laje_cobertura": (122, 120, 116),
    "metal_zincado": (136, 140, 146),
    "madeira": (140, 102, 62),
    "terra_vermelha": (122, 74, 52),
    "folhagem": (58, 92, 44),
    "esfera_verde": (36, 120, 62),
    "vidro": (30, 38, 52),
}

# Faixas aceitas (medidas da referencia), com o motivo.
FAIXAS = {
    ("faixas", "piso_central_m"): (3.5, 6.0, "deck de calcada largo o suficiente para correr"),
    ("faixas", "piso_borda_esq_m"): (0.6, 2.6, "meia-largura da calcada ate a guia (a rua fica a oeste)"),
    ("faixas", "guia_altura_m"): (0.08, 0.22, "altura da guia: degrau visivel, mas sem tropecar"),
    ("faixas", "guia_largura_m"): (0.20, 0.60, "largura da guia na referencia"),
    ("faixas", "pista_m"): (6.0, 12.0, "pista de rolamento"),
    ("faixas", "calcada_lateral_m"): (1.5, 4.5, "calcada lateral com arvores e mobiliario"),
    ("faixas", "linha_amarela_largura_m"): (0.08, 0.20, "espessura da linha pintada"),
    ("horizonte", "distancia_min_m"): (120.0, 300.0, "o horizonte precisa ficar atras dos predios"),
    ("horizonte", "passo_m"): (10.0, 60.0, "espacamento dos blocos do horizonte"),
    ("predios", "pe_direito_m"): (2.6, 4.2, "pe-direito de predio de 2 a 3 pavimentos"),
    ("predios", "recuo_calcada_m"): (0.0, 1.5, "recuo da fachada em relacao a calcada"),
    ("predios", "profundidade_m"): (4.0, 16.0, "profundidade do lote"),
    ("props", "arvore",): (None, None, ""),
}

PALETA_CHAVES = ["sol", "nevoa", "sombra", "ceu_alto", "ceu_horizonte", "sol_rotacao",
                 "sol_energia", "energia_ambiente", "nevoa_densidade", "exposicao", "nuvens"]

PERFIL_LOTE2 = ["sky_mode", "clouds", "sky_top", "sky_horizon", "fog_color", "fog_density",
                "fog_begin", "fog_end", "sun_rotation", "sun_color", "sun_energy",
                "shadow_distance", "shadow_tint", "ambient_energy", "sky_energy",
                "tonemap_white", "exposure", "brightness", "contrast", "saturation", "glow",
                "fov", "far", "dof_far", "dof_transition", "deband"]


def luma(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def chroma(c):
    mx, mn = max(c), min(c)
    return 0.0 if mx <= 1e-6 else (mx - mn) / mx


# ---------------------------------------------------------------------------
# 1. Especificacao
# ---------------------------------------------------------------------------

def auditar_spec(spec: dict, problemas: list, avisos: list) -> None:
    if int(spec.get("versao", 0)) < 3:
        problemas.append("spec: versao antiga (esperado >= 3)")

    for (secao, chave), faixa in FAIXAS.items():
        if faixa[0] is None:
            continue
        bloco = spec.get(secao, {})
        if chave not in bloco:
            problemas.append(f"spec: falta {secao}.{chave}")
            continue
        valor = float(bloco[chave])
        if not (faixa[0] <= valor <= faixa[1]):
            problemas.append(
                f"spec: {secao}.{chave} = {valor} fora da faixa {faixa[0]}..{faixa[1]} ({faixa[2]})")

    # corte transversal (layout "rua_esquerda") tem de cobrir o jogo:
    # a rua cobre o transito na faixa -3.25, a calcada cobre 0 e +3.25
    f = spec.get("faixas", {})
    piso = float(f.get("piso_central_m", 0))
    borda = float(f.get("piso_borda_esq_m", 0))
    guia = float(f.get("guia_largura_m", 0))
    pista = float(f.get("pista_m", 0))
    calcada = float(f.get("calcada_lateral_m", 0))
    limite = float(f.get("limite_lateral_m", 0))
    x_rua_esq = -(borda + guia + pista)
    x_rua_dir = -(borda + guia)
    if piso <= 0 or borda <= 0 or guia <= 0 or pista <= 0 or calcada <= 0:
        problemas.append("spec: alguma faixa transversal zerada")
    if x_rua_esq > -4.55 or x_rua_dir < -1.95:
        problemas.append(f"spec: a rua [{x_rua_esq:.2f}, {x_rua_dir:.2f}] nao cobre o "
                         "transito da faixa -3.25 do jogo")
    if borda < 0.9:
        problemas.append(f"spec: a calcada comeca em {-borda:.2f} e nao alcanca a faixa central (0)")
    if borda + piso < 4.45:
        problemas.append(f"spec: o deck termina em {borda + piso:.2f} e nao cobre a faixa direita (+3.25)")
    previsto = max(abs(x_rua_esq), borda + piso + calcada) + 0.5
    if limite < previsto:
        problemas.append(f"spec: limite lateral {limite} menor que a cidade desenhada ({previsto:.2f})")

    lajes = spec.get("lajes", {})
    tam = lajes.get("tamanho_m", [0, 0])
    if not (0.40 <= float(tam[0]) <= float(tam[1]) <= 1.00):
        problemas.append(f"spec: lajes.tamanho_m {tam} fora de 0.40..1.00")
    if float(lajes.get("junta_m", 0.0)) < 0.005:
        problemas.append("spec: junta das lajes pequena demais (some no celular)")

    # materiais
    materiais = spec.get("materiais", {})
    usados_sem_textura = []
    for nome, cfg in materiais.items():
        pbr = cfg.get("pbr", None)
        if pbr is None:
            usados_sem_textura.append(nome)
            continue
        if pbr not in MATERIAIS_LOTE1:
            problemas.append(f"spec: material '{nome}' aponta para PBR inexistente '{pbr}'")
        if not (0.05 <= float(cfg.get("uv_escala", 0.0)) <= 3.0):
            problemas.append(f"spec: material '{nome}' com uv_escala fora de 0.05..3.0")
    if len(materiais) < 8:
        problemas.append("spec: poucos materiais para a variedade da referencia")

    # orcamento
    orc = spec.get("orcamento", {})
    facts = json.loads(FACTS.read_text(encoding="utf-8"))["orcamento"]
    malhas = int(orc.get("malhas_max_por_quarteirao", 999))
    if malhas > int(facts["malhas_max_por_quarteirao"]):
        problemas.append(f"spec: orcamento de {malhas} malhas por quarteirao estoura o teto do Adreno 610 "
                         f"({facts['malhas_max_por_quarteirao']})")
    multi = int(orc.get("multimesh_limite", 999))
    if multi > int(facts["multimesh_limite"]):
        problemas.append(f"spec: multimesh_limite {multi} acima do teto {facts['multimesh_limite']}")
    vis = float(orc.get("distancia_visibilidade_m", 0.0))
    if not (facts["distancia_visibilidade_min_m"] <= vis <= facts["distancia_visibilidade_max_m"]):
        problemas.append(f"spec: distancia_visibilidade_m {vis} fora de "
                         f"{facts['distancia_visibilidade_min_m']}..{facts['distancia_visibilidade_max_m']}")

    # paletas
    paletas = spec.get("paletas", [])
    if len(paletas) < 4:
        problemas.append("spec: menos de 4 paletas (o plano pede variacao por capitulo)")
    nomes = set()
    for i, pal in enumerate(paletas):
        for chave in PALETA_CHAVES:
            if chave not in pal:
                problemas.append(f"spec: paleta {i} sem '{chave}'")
        nome = pal.get("nome", f"paleta{i}")
        if nome in nomes:
            problemas.append(f"spec: paleta repetida '{nome}'")
        nomes.add(nome)
        sol = pal.get("sol", [1, 1, 1])
        sombra = pal.get("sombra", [0, 0, 0])
        nevoa = pal.get("nevoa", [0, 0, 0])
        if luma(sol) <= luma(sombra) + 0.25:
            problemas.append(f"spec: paleta '{nome}' com sol e sombra parecidos demais")
        if sombra[2] <= sombra[0]:
            problemas.append(f"spec: paleta '{nome}' com sombra quente (a referencia tem sombra fria/azulada)")
        if luma(nevoa) <= luma(sombra):
            problemas.append(f"spec: paleta '{nome}' com nevoa mais escura que a sombra")
        if not (0.20 <= float(pal.get("nevoa_densidade", 0.0)) <= 0.85):
            problemas.append(f"spec: paleta '{nome}' com nevoa_densidade fora de 0.20..0.85")
        if not (0.30 <= float(pal.get("exposicao", 0.0)) <= 0.90):
            problemas.append(f"spec: paleta '{nome}' com exposicao fora de 0.30..0.90")
    if len(usados_sem_textura) >= len(materiais):
        avisos.append("AVISO: nenhum material usa textura PBR (o Lote 1 nao foi aplicado?)")


# ---------------------------------------------------------------------------
# 2. Espelho do leiaute
# ---------------------------------------------------------------------------

def leiaute(spec: dict, indice: int) -> dict:
    """Espelho do preenchimento do quarteirao (mesma semente, mesmo espirito)."""
    rng = random.Random(int(spec.get("seed", 1)) * 7919 + indice * 104729)
    f = spec["faixas"]
    q = spec["quarteirao"]
    comprimento = float(q["comprimento_m"]) + rng.uniform(-1, 1) * float(q.get("variacao_comprimento_m", 0.0))
    piso = float(f["piso_central_m"])
    borda = float(f["piso_borda_esq_m"])
    guia = float(f["guia_largura_m"])
    pista = float(f["pista_m"])
    calcada = float(f["calcada_lateral_m"])

    # lajes do deck de calcada
    lajes = []
    tam = spec["lajes"]["tamanho_m"]
    x = -borda
    coluna = 0
    while x < borda + piso - 0.05:
        largura = min(rng.uniform(tam[0], tam[1]), borda + piso - x)
        z = -rng.uniform(0.15, 0.45) if coluna % 2 else 0.0
        while z < comprimento - 0.05:
            prof = min(rng.uniform(tam[0], tam[1]), comprimento - z)
            lajes.append((x, z, largura, prof))
            z += prof
        x += largura
        coluna += 1

    # lotes (predios) dos dois lados
    p = spec["predios"]
    lotes = []
    for lado in (-1, 1):
        z = 0.0
        while z < comprimento - 0.6:
            largura = min(rng.uniform(p["largura_lote_m"][0], p["largura_lote_m"][1]), comprimento - z)
            andares = rng.randint(p["pisos"][0], p["pisos"][1])
            altura = andares * float(p["pe_direito_m"])
            lotes.append((lado, z, largura, altura))
            z += largura

    # arvores e postes
    passo_poste = float(spec["props"]["poste"]["espacamento_m"])
    postes = []
    z = 0.4
    while z < comprimento:
        postes.append(z)
        z += passo_poste
    passo_arvore = float(spec["props"]["arvore"]["espacamento_m"])
    arvores = []
    z = rng.uniform(1.0, passo_arvore)
    lado = 1
    while z < comprimento:
        arvores.append((lado, z))
        z += passo_arvore * rng.uniform(0.85, 1.15)
        lado = -lado

    impressao = hashlib.sha1(json.dumps({
        "lajes": [[round(v, 2) for v in l] for l in lajes],
        "lotes": [[l[0], round(l[1], 2), round(l[2], 2), round(l[3], 2)] for l in lotes],
        "postes": [round(z, 2) for z in postes],
        "arvores": [[l, round(z, 2)] for l, z in arvores],
    }, sort_keys=True).encode()).hexdigest()[:10]
    resumo = {
        "impressao": impressao,
        "indice": indice,
        "comprimento_m": round(comprimento, 3),
        "lajes": len(lajes),
        "lotes": len(lotes),
        "postes": len(postes),
        "arvores": len(arvores),
        "x_min_laje": round(min(l[0] for l in lajes), 3),
        "x_max_laje": round(max(l[0] + l[2] for l in lajes), 3),
        "faixas": {"piso": piso, "guia": guia, "pista": pista, "calcada": calcada},
    }
    return {"resumo": resumo, "lajes": lajes, "lotes": lotes, "postes": postes, "arvores": arvores}


def auditar_leiaute(spec: dict, problemas: list, avisos: list) -> dict:
    f = spec["faixas"]
    piso = float(f["piso_central_m"])
    borda = float(f["piso_borda_esq_m"])
    guia = float(f["guia_largura_m"])
    calcada = float(f["calcada_lateral_m"])
    comprimento = float(spec["quarteirao"]["comprimento_m"])
    limites = []
    for indice in range(3):
        dados = leiaute(spec, indice)
        r = dados["resumo"]
        # o hash cobre o leiaute inteiro (nao so o resumo), para qualquer mudanca aparecer
        limites.append(r)
        # a faixa de corrida fica livre: nada de prop dentro dela
        if r["x_min_laje"] < -borda - 0.01 or r["x_max_laje"] > borda + piso + 0.01:
            problemas.append(f"leiaute {indice}: lajes fora do deck de calcada ({r['x_min_laje']}..{r['x_max_laje']})")
        if r["lajes"] < 40:
            problemas.append(f"leiaute {indice}: poucas lajes ({r['lajes']}) para 28 m de faixa")
        # lotes fecham o quarteirao
        for lado in (-1, 1):
            largura_total = sum(l[2] for l in dados["lotes"] if l[0] == lado)
            if largura_total < comprimento * 0.85:
                problemas.append(f"leiaute {indice}: lado {lado} com lotes cobrindo "
                                 f"{largura_total:.1f} m de {comprimento:.1f} m")
            estreitos = 0
            lotes_do_lado = [l for l in dados["lotes"] if l[0] == lado]
            for _lado_lote, _z, largura, altura in lotes_do_lado:
                # o ultimo lote existe para fechar o quarteirao (o kit permite
                # que ele seja estreito, desde que nao vire um ﬁso)
                fecha = _z + largura >= comprimento - 0.75
                if not (2.5 <= largura <= 15.0) and not (fecha and largura >= 1.2):
                    problemas.append(f"leiaute {indice}: lote de {largura:.1f} m fora de 2.5..15 m")
                if largura < 5.0 and not fecha:
                    estreitos += 1
                if not (5.0 <= altura <= 12.0):
                    problemas.append(f"leiaute {indice}: predio de {altura:.1f} m fora de 5..12 m "
                                     "(2 a 3 pavimentos, como na referencia)")
            if estreitos > max(1, int(0.25 * len([l for l in dados["lotes"] if l[0] == lado]))):
                problemas.append(f"leiaute {indice}: lado {lado} com lotes estreitos demais "
                                 f"({estreitos} abaixo de 5 m)")
        # espacamento dos postes e das arvores
        passo_poste = float(spec["props"]["poste"]["espacamento_m"])
        if len(dados["postes"]) and abs(passo_poste - (comprimento / len(dados["postes"]))) > 0.4:
            problemas.append(f"leiaute {indice}: postes fora do espacamento do spec")
        faixa_arvore = (5.0, 12.0)
        zs = [z for _lado, z in dados["arvores"]]
        espacamentos = [b - a for a, b in zip(zs, zs[1:])]
        for e in espacamentos:
            if not (faixa_arvore[0] * 0.8 <= e <= faixa_arvore[1] * 1.3):
                problemas.append(f"leiaute {indice}: arvores com espacamento de {e:.1f} m")
        # a calcada tem espaco para arvore + prop
        if calcada < 1.5:
            problemas.append(f"leiaute {indice}: calcada de {calcada} m nao cabe arvore + props")
        # nada de prop na faixa de corrida
        x_arvore = borda + piso + calcada * 0.5
        if x_arvore <= borda + piso - 0.5:
            problemas.append(f"leiaute {indice}: arvore cairia dentro da faixa de corrida")
    hash_leiaute = hashlib.sha1(json.dumps(limites, sort_keys=True).encode()).hexdigest()[:12]
    return {"limites": limites, "hash": hash_leiaute}


# ---------------------------------------------------------------------------
# 3. Codigo do kit
# ---------------------------------------------------------------------------

def auditar_kit(texto: str, problemas: list, avisos: list) -> None:
    if "ORMMaterial3D" not in texto or "orm_texture" not in texto:
        problemas.append("kit: materiais PBR devem entrar via ORMMaterial3D + orm_texture (Lote 1)")
    if "normal_texture" not in texto:
        problemas.append("kit: sem normal_texture (o relevo das texturas do Lote 1 fica sem efeito)")
    if "uv1_scale" not in texto or "uv1_triplanar" not in texto:
        problemas.append("kit: sem uv1_scale/uv1_triplanar (a escala das texturas vira chute)")
    if "MultiMesh" not in texto or "set_instance_transform" not in texto:
        problemas.append("kit: o que se repete (lajes, mosaicos, janelas, postes) precisa de MultiMesh")
    if "RandomNumberGenerator" not in texto or ".seed = " not in texto:
        problemas.append("kit: leiaute precisa de RandomNumberGenerator com semente do spec")
    for ruim in ("randf()", "randi()", "randomize()"):
        for num, linha in enumerate(texto.splitlines(), start=1):
            if ruim in linha and "." not in linha.split(ruim)[0][-1:]:
                avisos.append(f"AVISO (linha {num}): {ruim} sem semente - leiaute deixa de ser reproduzivel")
    if "set_meta(" not in texto or "\"colisor\"" not in texto:
        problemas.append("kit: faltam metas ('superficie'/'colisor') para o Lote 5 achar as superficies")
    if "res://resources/world_spec.json" not in texto:
        problemas.append("kit: caminho do spec ausente/errado")
    if "13.9" in texto:
        problemas.append("kit: medida fixa 13.9 no codigo (a borda da calcada tem de sair do spec)")
    if "class ChunkStreamer" not in texto or "update_head" not in texto:
        problemas.append("kit: sem ChunkStreamer/update_head para reciclar quarteiroes")
    if "visibility_range_end" not in texto:
        problemas.append("kit: sem visibility_range_end (o que esta longe tem de sair de cena)")
    for chave in PERFIL_LOTE2:
        if chave not in texto:
            problemas.append(f"kit: perfil do Lote 2 incompleto - falta '{chave}'")


# ---------------------------------------------------------------------------
# Preview
# ---------------------------------------------------------------------------

def desenhar(spec: dict, espelho: dict) -> bool:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("  AVISO: Pillow ausente; preview nao desenhado (pip install pillow)")
        return False
    f = spec["faixas"]
    piso = float(f["piso_central_m"])
    guia = float(f["guia_largura_m"])
    pista = float(f["pista_m"])
    calcada = float(f["calcada_lateral_m"])
    limite = float(f["limite_lateral_m"])
    comprimento = float(spec["quarteirao"]["comprimento_m"])
    pal = spec["paletas"][0]

    L, A = 960, 940
    img = Image.new("RGB", (L, A), (18, 21, 26))
    d = ImageDraw.Draw(img)
    F = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    f_tit = ImageFont.truetype(FB, 23)
    f_sub = ImageFont.truetype(FB, 16)
    f_txt = ImageFont.truetype(F, 14)
    f_peq = ImageFont.truetype(F, 12)

    d.text((28, 16), "Lote 3 - corte da rua, planta de 2 quarteiroes e paletas", font=f_tit,
           fill=(240, 238, 232))
    d.text((28, 46), f"faixas: central {piso} m | guia {guia} m | pista {pista} m | "
                     f"calcada {calcada} m | limite {limite} m", font=f_peq, fill=(150, 158, 170))

    cor_piso = CORES_APROX["calcada_laje"]
    cor_pista = CORES_APROX["asfalto"]
    cor_calcada = CORES_APROX["calcada_mosaico"]

    # ---- painel 1: corte transversal (o sol vem de cima e de tras) ----
    px, py, pw, ph = 40, 80, 880, 300
    d.rectangle([px, py, px + pw, py + ph], fill=(25, 29, 36), outline=(60, 66, 76))
    d.text((px + 12, py + 8), "Corte transversal: faixa elevada entre guias, pistas e predios",
           font=f_sub, fill=(230, 226, 218))
    escala = min(19.0, (pw - 80) / (limite * 2))
    cx = px + pw // 2
    y_rua = py + ph - 46                      # topo do asfalto
    y_alto = int(y_rua - 26)                  # topo da faixa central e das calcadas
    # 1) ceu (primeiro, senao cobre o resto)
    cor_ceu = tuple(int(255 * c) for c in pal["ceu_alto"])
    cor_ceu_h = tuple(int(255 * c) for c in pal["ceu_horizonte"])
    topo = py + 32
    for i in range(max(1, y_alto - topo)):
        t = i / max(1, y_alto - topo)
        cor = tuple(int(cor_ceu_h[k] + (cor_ceu[k] - cor_ceu_h[k]) * t) for k in range(3))
        d.line([(px + 1, topo + i), (px + pw - 1, topo + i)], fill=cor)
    borda = float(f["piso_borda_esq_m"])
    # 2) asfalto: a rua inteira fica a oeste do deck
    x_rua_dir = cx - (borda + guia) * escala
    x_rua_esq = cx - (borda + guia + pista) * escala
    d.rectangle([x_rua_esq, y_rua, x_rua_dir, y_rua + 20], fill=cor_pista)
    # 3) deck de calcada elevado (o corredor passa aqui) e a guia
    d.rectangle([cx - borda * escala, y_alto + 26, cx + (borda + piso) * escala, y_rua],
                fill=cor_piso)
    d.rectangle([cx - (borda + guia) * escala, y_alto, cx - borda * escala, y_rua + 20],
                fill=tuple(max(0, c - 30) for c in cor_piso))
    # 4) faixa lateral de props da calcada
    d.rectangle([cx + (borda + piso) * escala, y_alto,
                 cx + (borda + piso + calcada) * escala, y_rua + 20], fill=cor_calcada)
    # 5) linha dupla amarela junto da guia
    for par in range(2):
        xl = cx - (borda + guia + float(f["linha_amarela_afastamento_m"]) +
                   float(f["linha_amarela_largura_m"]) * (0.5 + 1.6 * par)) * escala
        d.line([xl, y_rua + 2, xl, y_rua + 18], fill=(232, 200, 46), width=2)
    # 7) predios (por ultimo, para aparecerem na frente do ceu)
    recuo_p = float(spec["predios"]["recuo_calcada_m"])
    for lado in (-1, 1):
        x0 = (borda + piso + calcada + recuo_p) if lado > 0 else (borda + guia + pista + recuo_p)
        cores = CORES_APROX["reboco"] if lado > 0 else CORES_APROX["tijolo"]
        for i, altura in enumerate((7.0, 10.2, 6.8)):
            ini = cx + lado * (x0 + i * 4.0) * escala
            fim = cx + lado * (x0 + (i + 1) * 4.0) * escala
            d.rectangle([min(ini, fim), y_alto - altura * escala, max(ini, fim), y_alto + 20], fill=cores)
    # 6) arvores (faixa de props e alem da rua) e postes na guia
    for xa in (cx + (borda + piso + calcada * 0.5) * escala,
               cx - (borda + guia + pista + 1.2) * escala):
        d.line([xa, y_alto, xa, y_alto - 1.3 * escala], fill=(120, 88, 58), width=3)
        d.ellipse([xa - 1.05 * escala, y_alto - 3.1 * escala, xa + 1.05 * escala, y_alto - 1.1 * escala],
                  fill=CORES_APROX["folhagem"])
    xp = cx - (borda + guia * 0.5) * escala
    d.rectangle([xp - 2, y_alto - 0.95 * escala, xp + 2, y_alto],
                fill=CORES_APROX["metal_zincado"])
    # 8) rotulos
    d.text((int(x_rua_esq) + 8, y_rua + 4), "pista", font=f_peq, fill=(190, 195, 205))
    d.text((int(cx + (borda + piso * 0.45) * escala) - 52, y_rua + 4), "calcada (corre aqui)",
           font=f_peq, fill=(235, 232, 225))
    d.text((px + 10, py + 34), "ceu da paleta 'manha_limpa'", font=f_peq, fill=(210, 214, 222))

    # ---- painel 2: planta de 2 quarteiroes ----
    py2 = py + ph + 44
    d.text((px + 12, py2 - 26), "Planta (2 quarteiroes de 28 m): lajes, lotes, arvores e postes",
           font=f_sub, fill=(230, 226, 218))
    escala2 = (pw - 60) / (comprimento * 2 + 4)
    x_planta = px + 30
    for q in range(2):
        dados = leiaute(spec, q)
        zx = x_planta + q * (comprimento + 4) * escala2
        y_lat = py2 + 30
        d.rectangle([zx, y_lat - 6, zx + comprimento * escala2, y_lat + 10], fill=cor_pista)
        d.rectangle([zx, y_lat + 10, zx + comprimento * escala2, y_lat + 52], fill=cor_piso)
        d.rectangle([zx, y_lat + 52, zx + comprimento * escala2, y_lat + 76], fill=cor_calcada)
        for lado, zz, largura, altura in dados["lotes"]:
            y = y_lat + 76 if lado > 0 else y_lat - 40
            cor = CORES_APROX["tijolo"] if int(altura) % 2 else CORES_APROX["reboco"]
            d.rectangle([zx + zz * escala2, y, zx + (zz + largura) * escala2, y + 12], fill=cor)
        for lado, zz in dados["arvores"]:
            y = y_lat + 62 if lado > 0 else y_lat - 16
            d.ellipse([zx + zz * escala2 - 3, y - 3, zx + zz * escala2 + 3, y + 3],
                      fill=CORES_APROX["folhagem"])
        for zz in dados["postes"]:
            d.point((zx + zz * escala2, y_lat + 13), fill=(235, 235, 235))
        d.text((zx + 4, y_lat + 82), f"q{q}: {dados['resumo']['lajes']} lajes, "
                                     f"{dados['resumo']['lotes']} lotes, {dados['resumo']['arvores']} arvores"
                                     f" | {dados['resumo']['impressao']}", font=f_peq, fill=(170, 176, 186))

    # ---- painel 3: materiais ----
    py3 = py2 + 176
    d.text((px + 12, py3 - 26), "Materiais do cenario (texturas PBR do Lote 1)", font=f_sub,
           fill=(230, 226, 218))
    for i, nome in enumerate(spec["materiais"].keys()):
        col = i % 3
        lin = i // 3
        x0 = px + col * 290
        y0 = py3 + lin * 30
        cfg = spec["materiais"][nome]
        pbr = cfg.get("pbr", None)
        cor = CORES_APROX.get(pbr if pbr else nome, (128, 128, 128))
        d.rectangle([x0, y0, x0 + 22, y0 + 20], fill=cor, outline=(70, 76, 86))
        rotulo = f"{nome} - {pbr if pbr else 'cor plana'} (uv {cfg.get('uv_escala')})"
        d.text((x0 + 28, y0 + 3), rotulo[:36], font=f_peq, fill=(200, 205, 212))

    # ---- painel 4: paletas ----
    linhas_mat = (len(spec["materiais"]) + 2) // 3
    py4 = py3 + linhas_mat * 30 + 30
    d.text((px + 12, py4 - 26), "Paletas por capitulo (sol / nevoa / sombra / ceu)", font=f_sub,
           fill=(230, 226, 218))
    for i, paleta in enumerate(spec["paletas"]):
        y = py4 + i * 30
        d.text((px + 8, y + 3), paleta["nome"][:16], font=f_txt, fill=(216, 220, 226))
        for j, chave in enumerate(["sol", "nevoa", "sombra", "ceu_alto"]):
            cor = tuple(int(255 * c) for c in paleta[chave])
            d.rectangle([px + 150 + j * 46, y, px + 150 + j * 46 + 42, y + 22], fill=cor,
                        outline=(70, 76, 86))
        d.text((px + 350, y + 3), f"sol {paleta['sol_energia']:.2f} / nevoa {paleta['nevoa_densidade']:.2f}"
                                  f" / exposicao {paleta['exposicao']:.2f}", font=f_peq, fill=(160, 168, 180))

    d.text((28, A - 26), f"espelho do leiaute (hash {espelho['hash']}) - preview matematico, sem GPU",
           font=f_peq, fill=(120, 128, 140))
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT_PNG)
    print(f"  preview: {OUT_PNG.relative_to(ROOT)}")
    return True


def main() -> int:
    problemas: list = []
    avisos: list = []
    if not SPEC.exists():
        print(f"ERRO: {SPEC} nao encontrado")
        return 1
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    auditar_spec(spec, problemas, avisos)
    espelho = auditar_leiaute(spec, problemas, avisos)
    if KIT.exists():
        auditar_kit(KIT.read_text(encoding="utf-8"), problemas, avisos)
    else:
        avisos.append("AVISO: building_kit.gd nao encontrado nesta copia")

    quieto = "--quieto" in sys.argv
    print("Auditor do cenario (Lote 3)")
    print(f"  spec: {SPEC.name} v{spec.get('versao')} | seed {spec.get('seed')} | "
          f"{len(spec.get('materiais', {}))} materiais | {len(spec.get('paletas', []))} paletas")
    for r in espelho["limites"]:
        print(f"  quarteirao {r['indice']}: {r['comprimento_m']} m, {r['lajes']} lajes, "
              f"{r['lotes']} lotes, {r['postes']} postes, {r['arvores']} arvores")
    print(f"  hash do leiaute: {espelho['hash']}")
    for a in sorted(set(avisos)):
        print("  " + a)
    for p in problemas:
        print("  ERRO: " + p)
    print(f"  resumo: {len(problemas)} problema(s), {len(set(avisos))} aviso(s)")
    if not quieto:
        desenhar(spec, espelho)
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
