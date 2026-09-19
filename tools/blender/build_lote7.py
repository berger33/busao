# Lote 7 — mobiliario urbano (Blender 4.5 headless).
# Contrato: assets/props/<nome>.glb — escala real (metros), origem no chao.
# O lado aberto/visivel fica em -Y no Blender, que o export yup converte para
# +Z no Godot — ou seja, de frente para o corredor que se aproxima.
# Pecas: cone, hidrante, orelhao, banco, lixeira, poste, ponto (abrigo) e
# carrinho de camelô. Rodar: LD_LIBRARY_PATH=~/bpy_env/lib python3 tools/blender/build_lote7.py
import bpy, math, os, sys
from mathutils import Vector
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit_base as K
from kit_base import rad

import bmesh

D = bpy.data
PROPS = str(K.REPO / "assets" / "props")
OUT = K.OUT_DIR
os.makedirs(PROPS, exist_ok=True)
os.makedirs(OUT, exist_ok=True)


# ------------------------------------------------------------------ helpers
def caixa(nome, centro, dims, subd=0):
    """Box reto (sem subsurf por padrao: subsurf em caixa fina vira lente/agulha)."""
    cx, cy, cz = centro
    hx, hy, hz = dims[0] / 2.0, dims[1] / 2.0, dims[2] / 2.0
    v = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
         (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]
    v = [(px + cx, py + cy, pz + cz) for (px, py, pz) in v]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    o = K.novo_obj(nome, K.malha(nome, v, f))
    if subd:
        mm = o.modifiers.new("Subd", 'SUBSURF')
        mm.levels = mm.render_levels = subd
        mm.quality = 4
    return o


def ripa(nome, dims, centro, rot_x=0.0):
    """Box fino centrado na origem, rotacionado em X (se preciso) e movido.
    Rotacao primeiro, aplicada, para orbitar o proprio centro."""
    o = caixa(nome, (0.0, 0.0, 0.0), dims)
    if rot_x:
        K.sozinho(o)
        o.rotation_euler.x = rad(rot_x)
        bpy.ops.object.transform_apply(rotation=True)
    K.sozinho(o)
    o.location = centro
    bpy.ops.object.transform_apply(location=True)
    return o


def coluna_entre(nome, a, b, r, mat=None, seg=10):
    """Cilindro real (eixo Z do pilar) de a até b — para pernas, bicos, tubos."""
    a, b = Vector(a), Vector(b)
    o = K.pilar(nome, r, 1.0, seg=seg)
    o.scale = (1.0, 1.0, (b - a).length)
    K.sozinho(o)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    o.location = a  # o pilar nasce na base (z local 0) — locar em a, nao no meio
    o.rotation_euler = (b - a).normalized().to_track_quat('Z', 'Y').to_euler()
    K.sozinho(o)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=False)
    if mat:
        K.pintar(o, mat)
    return o


def pilar_seco(nome, r, rel, seg=16):
    """Pilar sem subsurf: o subsurf puxa o anel da base para o centro da
    tampa (pernas derretem em ponta). Mobiliario pede cilindro seco."""
    o = K.pilar(nome, r, rel, seg=max(seg, 16))
    for m in list(o.modifiers):
        o.modifiers.remove(m)
    return o


def casca_aberta(nome, raios, centro, rot_x, mat):
    """Meia-casca do orelhão: esfera com as faces frontais-baixas removidas
    (abertura de verdade, o aparelho aparece dentro)."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=14, radius=1.0)
    remover = [f for f in bm.faces
               if f.calc_center_median().y < -0.20 and f.calc_center_median().z < 0.30]
    bmesh.ops.delete(bm, geom=remover, context='FACES')
    me = D.meshes.new(nome)
    bm.to_mesh(me)
    bm.free()
    o = K.novo_obj(nome, me)
    K.pintar(o, mat)
    o.scale = raios
    K.sozinho(o)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.rotation_euler.x = rad(rot_x)
    K.sozinho(o)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    o.location = centro
    K.sozinho(o)
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    return o


# ------------------------------------------------------------------ materiais
# Criados DEPOIS do reset_scene (read_factory_settings invalida structs).
M = {}
quente = None


def criar_materiais():
    global quente
    M.update({
        "aco": K.material("PropAco", (0.24, 0.27, 0.32), 0.38, 0.70),
        "aco_claro": K.material("PropAcoClaro", (0.55, 0.58, 0.62), 0.35, 0.80),
        "madeira": K.material("PropMadeira", (0.60, 0.39, 0.24), 0.72, 0.0),
        "madeira_clara": K.material("PropMadeiraClara", (0.78, 0.54, 0.32), 0.68, 0.0),
        "borracha": K.material("PropBorracha", (0.10, 0.11, 0.12), 0.85, 0.0),
        "laranja": K.material("PropLaranjaCone", (0.85, 0.32, 0.12), 0.55, 0.0),
        "refletivo": K.material("PropRefletivo", (0.96, 0.93, 0.85), 0.25, 0.0),
        "vermelho": K.material("PropVermelhoHidrante", (0.72, 0.18, 0.16), 0.50, 0.0),
        "latao": K.material("PropLatao", (0.94, 0.64, 0.27), 0.35, 0.80),
        "fibra": K.material("PropFibraOrelhao", (0.85, 0.30, 0.10), 0.32, 0.0),
        "fone": K.material("PropFoneEscuro", (0.12, 0.14, 0.17), 0.50, 0.0),
        "teal": K.material("PropTeclado", (0.16, 0.62, 0.64), 0.40, 0.0),
        "verde": K.material("PropVerdeLixeira", (0.18, 0.49, 0.31), 0.55, 0.0),
        "verde_placa": K.material("PropVerdePlaca", (0.75, 0.82, 0.70), 0.55, 0.0),
        "poste_cinza": K.material("PropPosteCinza", (0.30, 0.33, 0.37), 0.45, 0.50),
        "aluminio": K.material("PropAluminio", (0.82, 0.84, 0.86), 0.35, 0.30),
        "vidro": K.material("PropVidroAzul", (0.55, 0.70, 0.78), 0.12, 0.0),
        "amarelo": K.material("PropAmareloTesta", (0.91, 0.77, 0.36), 0.50, 0.0),
        "assento": K.material("PropAssentoLaranja", (0.86, 0.45, 0.20), 0.45, 0.40),
        "azul": K.material("PropAzulPlaca", (0.16, 0.32, 0.60), 0.50, 0.0),
        "toldo": K.material("PropToldoVermelho", (0.91, 0.31, 0.35), 0.60, 0.0),
        "branco": K.material("PropBrancoListra", (0.92, 0.92, 0.90), 0.50, 0.0),
        "interno": K.material("PropInterno", (0.16, 0.15, 0.15), 0.60, 0.0),
    })
    # lente do poste: emissiva quente (sodio)
    quente = K.material("PropLuzQuente", (1.0, 0.85, 0.62), 0.30, 0.0)
    _b = quente.node_tree.nodes["Principled BSDF"]
    _b.inputs["Emission Color"].default_value = (1.0, 0.85, 0.62, 1.0)
    _b.inputs["Emission Strength"].default_value = 3.0



# ------------------------------------------------------------------ pecas
def build_cone(M):
    partes = []
    # base quadrada (x, profundidade, altura)
    base = caixa("ConeBase", (0, 0, 0.0225), (0.55, 0.55, 0.045))
    K.pintar(base, M["laranja"])
    partes.append(base)
    # corpo conico (pilar unitario escalado)
    corpo = pilar_seco("ConeCorpo", 0.19, 0.045, seg=24)
    corpo.scale = (1.0, 1.0, 0.88)
    corpo.location = (0, 0, 0.045)
    K.pintar(corpo, M["laranja"])
    partes.append(corpo)
    # ponta arredondada
    topo = K.elipsoide("ConePonta", (0, 0, 0.905), (0.013, 0.013, 0.028), nivel=1)
    K.pintar(topo, M["laranja"])
    partes.append(topo)

    def r_cone(z):
        t = (z - 0.045) / 0.88
        return 0.19 * (1.0 - t) + 0.19 * 0.045 * t

    for i, zc in enumerate((0.34, 0.62)):
        r0 = r_cone(zc - 0.0425) + 0.013
        r1 = r_cone(zc + 0.0425) + 0.013
        faixa = K.pilar(f"ConeFaixa{i}", r0, r1 / r0, seg=24)
        faixa.scale = (1.0, 1.0, 0.085)
        faixa.location = (0, 0, zc - 0.0425)
        K.pintar(faixa, M["refletivo"])
        partes.append(faixa)
    return partes


def build_hidrante(M):
    partes = []
    brida = pilar_seco("HidranteBrida", 0.21, 1.0, seg=18)
    brida.scale = (1.0, 1.0, 0.07)
    K.pintar(brida, M["vermelho"])
    partes.append(brida)
    bojo = K.elipsoide("HidranteBojo", (0, 0, 0.10), (0.185, 0.185, 0.075), nivel=2)
    K.pintar(bojo, M["vermelho"])
    partes.append(bojo)
    corpo = pilar_seco("HidranteCorpo", 0.175, 0.88, seg=18)
    corpo.scale = (1.0, 1.0, 0.52)
    corpo.location = (0, 0, 0.10)
    K.pintar(corpo, M["vermelho"])
    partes.append(corpo)
    pescoco = pilar_seco("HidrantePescoco", 0.12, 0.90, seg=16)
    pescoco.scale = (1.0, 1.0, 0.16)
    pescoco.location = (0, 0, 0.62)
    K.pintar(pescoco, M["vermelho"])
    partes.append(pescoco)
    domo = K.elipsoide("HidranteDomo", (0, 0, 0.80), (0.125, 0.125, 0.085), nivel=2)
    K.pintar(domo, M["vermelho"])
    partes.append(domo)
    porca = pilar_seco("HidrantePorca", 0.055, 0.80, seg=10)
    porca.scale = (1.0, 1.0, 0.07)
    porca.location = (0, 0, 0.86)
    K.pintar(porca, M["latao"])
    partes.append(porca)
    for s in (-1.0, 1.0):
        bico = coluna_entre(f"HidranteBico{int(s)}", (s * 0.16, 0, 0.40), (s * 0.33, 0, 0.40), 0.075, M["vermelho"], seg=14)
        partes.append(bico)
        tampa = coluna_entre(f"HidranteTampa{int(s)}", (s * 0.33, 0, 0.40), (s * 0.365, 0, 0.40), 0.095, M["latao"], seg=14)
        partes.append(tampa)
    frente = coluna_entre("HidranteBicoFrente", (0, 0.17, 0.30), (0, 0.235, 0.30), 0.045, M["latao"], seg=12)
    partes.append(frente)
    volante = pilar_seco("HidranteVolante", 0.06, 1.0, seg=12)
    volante.scale = (1.0, 1.0, 0.02)
    volante.rotation_euler.x = rad(90)
    volante.location = (0, 0.25, 0.30)
    K.pintar(volante, M["latao"])
    partes.append(volante)
    return partes


def build_orelhao(M):
    partes = []
    pe = pilar_seco("OrelhaoPe", 0.16, 1.0, seg=16)
    pe.scale = (1.0, 1.0, 0.05)
    K.pintar(pe, M["aco"])
    partes.append(pe)
    coluna = pilar_seco("OrelhaoColuna", 0.055, 1.0, seg=14)
    coluna.scale = (1.0, 1.0, 1.45)
    K.pintar(coluna, M["aco"])
    partes.append(coluna)
    capuz = casca_aberta("OrelhaoCapuz", (0.44, 0.38, 0.54), (0, 0.06, 1.82), -12.0, M["fibra"])
    partes.append(capuz)
    aparelho = caixa("OrelhaoAparelho", (0, -0.02, 1.55), (0.28, 0.14, 0.42))
    K.pintar(aparelho, M["fone"])
    partes.append(aparelho)
    teclado = ripa("OrelhaoTeclado", (0.22, 0.035, 0.26), (0, -0.115, 1.55), rot_x=-25.0)
    K.pintar(teclado, M["teal"])
    partes.append(teclado)
    moedeiro = ripa("OrelhaoMoedeiro", (0.10, 0.02, 0.12), (-0.09, -0.10, 1.72))
    K.pintar(moedeiro, M["latao"])
    partes.append(moedeiro)
    fone = coluna_entre("OrelhaoFone", (-0.115, -0.05, 1.52), (-0.115, -0.05, 1.72), 0.028, M["fone"], seg=10)
    partes.append(fone)
    for i, zz in enumerate((1.51, 1.73)):
        campainha = K.elipsoide(f"OrelhaoFonePonta{i}", (-0.115, -0.05, zz), (0.042, 0.042, 0.030), nivel=1)
        K.pintar(campainha, M["fone"])
        partes.append(campainha)
    return partes


def build_banco(M):
    partes = []
    for s in (-0.68, 0.68):
        perna_f = coluna_entre(f"BancoPernaF{int(s*100)}", (s, -0.15, 0.02), (s, -0.15, 0.46), 0.028, M["aco"], seg=10)
        partes.append(perna_f)
        perna_t = coluna_entre(f"BancoPernaT{int(s*100)}", (s, 0.14, 0.02), (s, 0.20, 0.98), 0.028, M["aco"], seg=10)
        partes.append(perna_t)
        travessa = coluna_entre(f"BancoTravessa{int(s*100)}", (s, -0.20, 0.44), (s, 0.16, 0.44), 0.026, M["aco"], seg=10)
        partes.append(travessa)
    for i, yy in enumerate((-0.14, 0.0, 0.14)):
        ripa_a = ripa(f"BancoRipa{i}", (1.70, 0.13, 0.035), (0, yy, 0.46))
        K.pintar(ripa_a, M["madeira"])
        partes.append(ripa_a)
    for i, (yy, zz) in enumerate(((0.205, 0.72), (0.315, 0.905))):
        encosto = ripa(f"BancoEncosto{i}", (1.70, 0.10, 0.035), (0, yy, zz), rot_x=-14.0)
        K.pintar(encosto, M["madeira"])
        partes.append(encosto)
    return partes


def build_lixeira(M):
    partes = []
    pe = caixa("LixeiraPe", (0, 0.10, 0.025), (0.30, 0.30, 0.05))
    K.pintar(pe, M["aco"])
    partes.append(pe)
    poste = caixa("LixeiraPoste", (0, 0.14, 0.53), (0.07, 0.07, 1.02))
    K.pintar(poste, M["aco"])
    partes.append(poste)
    braco = caixa("LixeiraBraco", (0, 0.02, 1.00), (0.06, 0.26, 0.06))
    K.pintar(braco, M["aco"])
    partes.append(braco)
    tambor = pilar_seco("LixeiraTambor", 0.185, 1.0, seg=20)
    tambor.scale = (1.0, 1.0, 0.52)
    tambor.location = (0, -0.08, 0.46)
    K.pintar(tambor, M["verde"])
    partes.append(tambor)
    aro = pilar_seco("LixeiraAro", 0.195, 1.0, seg=20)
    aro.scale = (1.0, 1.0, 0.035)
    aro.location = (0, -0.08, 0.947)
    K.pintar(aro, M["verde"])
    partes.append(aro)
    boca = pilar_seco("LixeiraBoca", 0.16, 1.0, seg=16)
    boca.scale = (1.0, 1.0, 0.012)
    boca.location = (0, -0.08, 0.978)
    K.pintar(boca, M["interno"])
    partes.append(boca)
    simbolo = ripa("LixeiraSimbolo", (0.14, 0.012, 0.14), (0, -0.272, 0.74))
    K.pintar(simbolo, M["verde_placa"])
    partes.append(simbolo)
    return partes


def build_poste(M):
    partes = []
    base = pilar_seco("PosteBase", 0.09, 0.80, seg=16)
    base.scale = (1.0, 1.0, 0.12)
    K.pintar(base, M["poste_cinza"])
    partes.append(base)
    haste = pilar_seco("PosteHaste", 0.055, 0.62, seg=16)
    haste.scale = (1.0, 1.0, 3.30)
    haste.location = (0, 0, 0.10)
    K.pintar(haste, M["poste_cinza"])
    partes.append(haste)
    braco1 = coluna_entre("PosteBraco1", (0, 0, 3.30), (0.30, 0, 3.52), 0.035, M["poste_cinza"], seg=10)
    partes.append(braco1)
    braco2 = coluna_entre("PosteBraco2", (0.30, 0, 3.52), (0.72, 0, 3.56), 0.030, M["poste_cinza"], seg=10)
    partes.append(braco2)
    luminaria = caixa("PosteLuminaria", (0.86, 0, 3.54), (0.52, 0.20, 0.09))
    K.pintar(luminaria, M["aluminio"])
    partes.append(luminaria)
    lente = caixa("PosteLente", (0.86, 0, 3.488), (0.40, 0.14, 0.02))
    K.pintar(lente, quente)
    partes.append(lente)
    return partes


def build_ponto(M):
    """Abrigo do ponto — SEM placa (a StopSign procedural fica, tem
    customizacao de GameSave)."""
    partes = []
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            col = K.pilar(f"PontoColuna{int(sx)}{int(sy)}", 0.045, 1.0, seg=12)
            col.scale = (1.0, 1.0, 2.30)
            col.location = (sx * 1.15, sy * 0.45, 0)
            K.pintar(col, M["aco"])
            partes.append(col)
    teto = caixa("PontoTeto", (0, 0, 2.36), (2.70, 1.20, 0.08))
    K.pintar(teto, M["aluminio"])
    partes.append(teto)
    testa = caixa("PontoTesta", (0, -0.57, 2.29), (2.74, 0.10, 0.20))
    K.pintar(testa, M["amarelo"])
    partes.append(testa)
    vidro_fundo = caixa("PontoVidroFundo", (0, 0.42, 1.42), (2.30, 0.03, 1.35))
    K.pintar(vidro_fundo, M["vidro"])
    partes.append(vidro_fundo)
    for s in (-1.0, 1.0):
        vidro_lat = caixa(f"PontoVidroLateral{int(s)}", (s * 1.10, 0.05, 1.48), (0.03, 0.80, 1.10))
        K.pintar(vidro_lat, M["vidro"])
        partes.append(vidro_lat)
    for s in (-0.75, 0.75):
        perna = K.pilar(f"PontoPerna{int(s*100)}", 0.030, 1.0, seg=10)
        perna.scale = (1.0, 1.0, 0.42)
        perna.location = (s, 0.30, 0)
        K.pintar(perna, M["aco"])
        partes.append(perna)
    assento = caixa("PontoAssento", (0, 0.28, 0.45), (1.80, 0.30, 0.05))
    K.pintar(assento, M["assento"])
    partes.append(assento)
    return partes


def build_carrinho(M):
    partes = []
    corpo = caixa("CarrinhoCorpo", (0, 0.05, 0.62), (1.40, 0.85, 0.85))
    K.pintar(corpo, M["madeira"])
    partes.append(corpo)
    tampo = caixa("CarrinhoTampo", (0, 0.05, 1.08), (1.55, 0.95, 0.06))
    K.pintar(tampo, M["madeira_clara"])
    partes.append(tampo)
    vitrine = caixa("CarrinhoVitrine", (0, 0.05, 1.30), (0.90, 0.55, 0.38))
    K.pintar(vitrine, M["vidro"])
    partes.append(vitrine)
    for s in (-1.0, 1.0):
        roda = coluna_entre(f"CarrinhoRoda{int(s)}", (s * 0.52 - 0.06, 0.30, 0.17), (s * 0.52 + 0.06, 0.30, 0.17), 0.17, M["borracha"], seg=16)
        partes.append(roda)
        cubo = coluna_entre(f"CarrinhoCubo{int(s)}", (s * 0.52 - 0.07, 0.30, 0.17), (s * 0.52 + 0.07, 0.30, 0.17), 0.05, M["latao"], seg=10)
        partes.append(cubo)
    for s in (-1.0, 1.0):
        perna = coluna_entre(f"CarrinhoPerna{int(s)}", (s * 0.55, -0.30, 0.0), (s * 0.55, -0.30, 1.05), 0.025, M["aco"], seg=8)
        partes.append(perna)
        vara = coluna_entre(f"CarrinhoVara{int(s)}", (s * 0.62, -0.30, 1.10), (s * 0.62, -0.30, 1.98), 0.022, M["aco_claro"], seg=8)
        partes.append(vara)
    toldo = ripa("CarrinhoToldo", (1.70, 1.05, 0.045), (0, -0.10, 2.02), rot_x=-8.0)
    K.pintar(toldo, M["toldo"])
    partes.append(toldo)
    for i, xx in enumerate((-0.55, 0.0, 0.55)):
        listra = ripa(f"CarrinhoListra{i}", (0.20, 1.05, 0.012), (xx, -0.10, 2.048), rot_x=-8.0)
        K.pintar(listra, M["branco"])
        partes.append(listra)
    barra = coluna_entre("CarrinhoBarra", (-0.50, 0.48, 0.95), (0.50, 0.48, 0.95), 0.020, M["aco_claro"], seg=8)
    partes.append(barra)
    return partes


# ------------------------------------------------------------------ saida
def limpar():
    for o in list(D.objects):
        D.objects.remove(o, do_unlink=True)


def render_prop(nome, dist, h_alvo, prop):
    # limpa a cena MENOS a peca atual (senao o render sai vazio)
    for o in list(D.objects):
        if o is not prop:
            D.objects.remove(o, do_unlink=True)
    cam = K.setup_preview()
    cam.data.lens = 50
    dist *= 1.45
    for lo in D.objects:
        if lo.type == 'LIGHT':
            if lo.data.name == "Cheia":
                lo.data.energy = 4.0
            elif lo.data.name == "Sol":
                lo.data.energy = 1.3
        if lo.name.startswith("Piso"):
            lo.scale = (dist * 2.2, dist * 2.2, 1.0)
    K.render_de(cam, (0.82 * dist, -1.05 * dist, h_alvo), (0, 0, h_alvo * 0.55),
                f"{OUT}/lote7_{nome}.png")


JOBS = [
    ("cone", build_cone, 1.7, 0.55),
    ("hidrante", build_hidrante, 1.9, 0.55),
    ("orelhao", build_orelhao, 3.2, 1.15),
    ("banco", build_banco, 3.0, 0.55),
    ("lixeira", build_lixeira, 2.2, 0.55),
    ("poste", build_poste, 4.6, 1.80),
    ("ponto", build_ponto, 4.8, 1.20),
    ("carrinho", build_carrinho, 3.4, 1.05),
]


def main():
    K.reset_scene()
    criar_materiais()
    for nome, fn, dist, h in JOBS:
        partes = fn(M)
        # garante matrix_world fresca antes do join (scale/location diretos)
        bpy.context.view_layer.update()
        corpo = K.join_parts([(o, "Prop") for o in partes])
        corpo.name = "Prop_" + nome.capitalize()
        K.sozinho(corpo)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        K.export_glb(f"{PROPS}/{nome}.glb", [corpo])
        xs = [v[0] for v in corpo.bound_box]
        ys = [v[1] for v in corpo.bound_box]
        zs = [v[2] for v in corpo.bound_box]
        print(f"L7 {nome}: {max(xs)-min(xs):.2f} x {max(ys)-min(ys):.2f} x {max(zs)-min(zs):.2f} m "
              f"(x compr, y profund, z altura)")
        render_prop(nome, dist, h, corpo)
    print("LOTE7_OK")


main()
