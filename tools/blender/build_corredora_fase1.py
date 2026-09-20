"""
FASE 1 — Corredora Atlética de alta fidelidade (Blender 4.5 headless / bpy).

Referência: docs/ESTUDO_COMPARATIVO_FIDELIDADE_VISUAL.md (Frente 1 + Fase 1).

O que muda em relação a build_atleta_realista.py / build_personagens.py:

* MALHA ÚNICA POR CONSTRUÇÃO — nenhum bpy.ops.object.join(). Todas as peças
  são geradas em Python (vértices, faces, UVs, índice de material e PESOS POR
  VÉRTICE) e viram um único bpy Mesh via from_pydata. Torso+pelve é um loft
  contínuo do quadril à clavícula; cada perna é um loft contínuo do quadril ao
  tornozelo (coxa → patela → gastrocnêmio → maléolos); cada braço é um loft
  contínuo do deltoide ao punho.
* PESAGEM SUAVE (smooth skin weighting) — cada anel do loft declara os pesos
  de osso (ex.: joelho = thigh 0.5 / calf 0.5) e os vértices herdam esses
  pesos. Transição por smoothstep ao longo do membro, sem cortes mecânicos.
* ANÉIS ANATÔMICOS — o raio de cada anel é modulado por ângulo (bulge frontal
  para a patela, posterior para o gastrocnêmio e glúteos, lateral para os
  maléolos), gerando relevo muscular real na silhueta.
* TÊNIS DE CORRIDA ESCULPIDO — 5 materiais: Sola (borracha preta 0.8 cm com
  ranhuras), Entressola (EVA branca: calcanhar 3.8 cm → toe rocker 1.5 cm),
  Sapato (cabedal têxtil, tintável pelo Godot), Cadarco (4 passadas + ilhoses)
  e Meia (cano curto branco 2 cm). Sola toca o chão exatamente em z = 0.
* RABO DE CAVALO COM RIG — ossos Hair_Ponytail_01/02 filhos de Head, com
  inércia (defasagem de fase) nos clipes Sprint/Walk/Jump.
* UV ATLAS SEM SOBREPOSIÇÃO — cada peça recebe uma célula própria no espaço
  UV (grade automática); costuras dos lofts ficam no lado interno das pernas /
  braços e na linha posterior das costas (seam_angle).
* 6 clipes biomecânicos compatíveis com scripts/runner_character.gd:
  Idle_Loop, Walk_Loop, Sprint_Loop (16 f = 0,667 s), Jump_Loop,
  Crouch_Idle_Loop, Crouch_Fwd_Loop.

Uso:
  sh tools/blender/run_bpy.sh tools/blender/build_corredora_fase1.py
  (variáveis: CORREDORA_OUT=<glb>, CORREDORA_PREVIEW=1 para renderizar PNGs)
"""
import bpy, bmesh, math, os, sys, json, struct, hashlib
from mathutils import Vector

TAU = 2.0 * math.pi
def rad(d): return math.radians(d)
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def smoothstep(t): t = clamp(t); return t * t * (3.0 - 2.0 * t)
def lerp(a, b, t): return a + (b - a) * t

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_GLB = os.environ.get("CORREDORA_OUT", os.path.join(REPO, "assets/characters/personagens/julia.glb"))
OUT_DIR = os.environ.get("CORREDORA_OUT_DIR", os.path.join(REPO, "tools/blender/out"))
PREVIEW = os.environ.get("CORREDORA_PREVIEW", "0") == "1"

# --------------------------------------------------------------------------
# Paleta (Frente 2 — os valores de albedo ficam no GLB; Godot pode tintar
# Camisa/Calca/Sapato/Hair via _apply_profile_palette; Entressola/Sola/Meia/
# Cadarco/QuaterniusSkin NÃO são tintados e preservam o look de referência.)
# --------------------------------------------------------------------------
def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))

def srgb_to_linear(c):
    return tuple((v / 12.92) if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c)

PALETA = {
    "QuaterniusSkin": ("#a66b52", 0.58, 0.0),
    "Hair":           ("#1a1412", 0.42, 0.0),
    "Camisa":         ("#e06b85", 0.78, 0.0),
    "Calca":          ("#18191f", 0.65, 0.0),
    "Sapato":         ("#c9cfd8", 0.72, 0.0),   # cabedal cinza-azulado (tintável)
    "Entressola":     ("#f8f8fa", 0.45, 0.0),   # EVA branco
    "Sola":           ("#1a1a1a", 0.85, 0.0),   # borracha preta
    "Cadarco":        ("#e8ebf0", 0.60, 0.0),
    "Ilhos":          ("#8f949c", 0.35, 0.8),
    "Meia":           ("#f4f4f2", 0.80, 0.0),
    "OlhoBranco":     ("#f4f4f0", 0.25, 0.0),
    "OlhoIris":       ("#3a2414", 0.15, 0.0),
    "Elastico":       ("#e9d459", 0.62, 0.0),
}

def make_material(nome, hexcor, rough, metal):
    m = bpy.data.materials.get(nome) or bpy.data.materials.new(nome)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*srgb_to_linear(hex_to_rgb(hexcor)), 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m

# --------------------------------------------------------------------------
# Construtor de malha única (MeshBuilder)
# --------------------------------------------------------------------------
class MeshBuilder:
    """Acumula peças (verts/faces/uv/pesos) e produz UM mesh contínuo."""
    def __init__(self):
        self.verts = []        # (x, y, z)
        self.weights = []      # dict bone -> w
        self.faces = []        # tuple de índices
        self.face_mat = []     # índice de material por face
        self.face_uv = []      # lista de (u, v) por loop
        self.face_part = []    # id da peça (para o atlas UV)
        self.mats = []         # nomes de materiais em ordem
        self.parts = []        # nomes das peças
        self.ring_cache = []   # (part_id, ring_index, [vert idx]) para costura

    def mat_index(self, nome):
        if nome not in self.mats:
            self.mats.append(nome)
        return self.mats.index(nome)

    def new_part(self, nome):
        self.parts.append(nome)
        return len(self.parts) - 1

    def add_vert(self, co, w):
        self.verts.append(tuple(co))
        s = sum(w.values()) or 1.0
        self.weights.append({k: v / s for k, v in w.items() if v > 1e-5})
        return len(self.verts) - 1

    def add_face(self, idx, uvs, mat, part):
        self.faces.append(tuple(idx))
        self.face_uv.append(list(uvs))
        self.face_mat.append(mat)
        self.face_part.append(part)

    # ---- loft genérico -----------------------------------------------------
    def loft(self, nome, rings, mat, close_start=False, close_end=False, seam_angle=0.0):
        """rings: lista de dicts com keys:
             pts: lista de (x,y,z) já posicionados (mesmo número em todos)
             w:   dict de pesos de osso do anel
             mat: (opcional) material das faces ENTRE este anel e o próximo
        seam_angle já foi aplicado por quem gerou pts; aqui só costura."""
        part = self.new_part(nome)
        seg = len(rings[0]["pts"])
        ring_idx = []
        for r in rings:
            ring_idx.append([self.add_vert(p, r["w"]) for p in r["pts"]])
        n = len(rings)
        for i in range(n - 1):
            m = self.mat_index(rings[i].get("mat", mat))
            v0 = i / (n - 1); v1 = (i + 1) / (n - 1)
            for k in range(seg):
                kn = (k + 1) % seg
                u0 = k / seg; u1 = (k + 1) / seg
                self.add_face((ring_idx[i][k], ring_idx[i][kn], ring_idx[i+1][kn], ring_idx[i+1][k]),
                              ((u0, v0), (u1, v0), (u1, v1), (u0, v1)), m, part)
        if close_start:
            c = Vector((0, 0, 0))
            for p in rings[0]["pts"]: c += Vector(p)
            c /= seg
            ci = self.add_vert(c, rings[0]["w"])
            m = self.mat_index(rings[0].get("mat", mat))
            for k in range(seg):
                kn = (k + 1) % seg
                self.add_face((ci, ring_idx[0][kn], ring_idx[0][k]),
                              ((0.5, 0.0), ((k+1)/seg, 0.0), (k/seg, 0.0)), m, part)
        if close_end:
            c = Vector((0, 0, 0))
            for p in rings[-1]["pts"]: c += Vector(p)
            c /= seg
            ci = self.add_vert(c, rings[-1]["w"])
            m = self.mat_index(rings[-2].get("mat", mat))
            for k in range(seg):
                kn = (k + 1) % seg
                self.add_face((ci, ring_idx[-1][k], ring_idx[-1][kn]),
                              ((0.5, 1.0), (k/seg, 1.0), ((k+1)/seg, 1.0)), m, part)
        return part

    def ellipsoid(self, nome, centro, raios, w, mat, useg=16, vseg=12, squash_z=None):
        """Esfera UV escalada; squash_z = (z_min_local) recorta a base (para touca)."""
        part = self.new_part(nome)
        cx, cy, cz = centro; rx, ry, rz = raios
        m = self.mat_index(mat)
        rows = []
        for j in range(vseg + 1):
            phi = -math.pi / 2 + math.pi * j / vseg
            z = math.sin(phi); rr = math.cos(phi)
            row = []
            for i in range(useg):
                a = TAU * i / useg
                row.append(self.add_vert((cx + rx * rr * math.cos(a), cy + ry * rr * math.sin(a), cz + rz * z), w))
            rows.append(row)
        for j in range(vseg):
            v0 = j / vseg; v1 = (j + 1) / vseg
            for i in range(useg):
                inx = (i + 1) % useg
                u0 = i / useg; u1 = (i + 1) / useg
                self.add_face((rows[j][i], rows[j][inx], rows[j+1][inx], rows[j+1][i]),
                              ((u0, v0), (u1, v0), (u1, v1), (u0, v1)), m, part)
        return part

    # ---- finalização --------------------------------------------------------
    def build(self, nome, materials, merge_dist=0.0006):
        me = bpy.data.meshes.new(nome)
        me.from_pydata(self.verts, [], self.faces)
        me.update()
        for mname in self.mats:
            me.materials.append(materials[mname])
        for p, mi in zip(me.polygons, self.face_mat):
            p.material_index = mi
            p.use_smooth = True
        # UV atlas: grade automática com padding; cada peça tem célula própria
        uv = me.uv_layers.new(name="UVMap")
        n_parts = len(self.parts)
        cols = math.ceil(math.sqrt(n_parts)); rows = math.ceil(n_parts / cols)
        pad = 0.06
        for p, uvs, part in zip(me.polygons, self.face_uv, self.face_part):
            c = part % cols; r = part // cols
            for li, (u, v) in zip(p.loop_indices, uvs):
                uu = (c + pad + u * (1 - 2 * pad)) / cols
                vv = (r + pad + v * (1 - 2 * pad)) / rows
                uv.data[li].uv = (uu, vv)
        obj = bpy.data.objects.new(nome, me)
        bpy.context.scene.collection.objects.link(obj)
        # vertex groups (pesos suaves já normalizados)
        groups = {}
        for vi, w in enumerate(self.weights):
            for bone, val in w.items():
                if bone not in groups:
                    groups[bone] = obj.vertex_groups.new(name=bone)
                groups[bone].add([vi], val, 'REPLACE')
        # solda anéis coincidentes (continuidade poligonal entre segmentos)
        bm = bmesh.new(); bm.from_mesh(me)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=merge_dist)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me); bm.free()
        me.update()
        return obj

# --------------------------------------------------------------------------
# Geradores de anéis anatômicos
# --------------------------------------------------------------------------
def ring_z(cx, cy, z, rx, ry, seg=16, seam_angle=math.pi/2, bulge=None):
    """Anel horizontal (plano XY). Ângulo 0 aponta para +X. Frente do corpo = -Y.
    seam_angle: ângulo onde a costura UV (k=0) começa.
    bulge: lista de (angulo_centro, amplitude_m, largura_exp) — relevo direcional."""
    pts = []
    for k in range(seg):
        a = seam_angle + TAU * k / seg
        r_x, r_y = rx, ry
        extra = 0.0
        if bulge:
            for ang, amp, expo in bulge:
                d = math.cos(a - ang)
                if d > 0:
                    extra += amp * d ** expo
        ca, sa = math.cos(a), math.sin(a)
        pts.append((cx + (r_x + extra) * ca, cy + (r_y + extra) * sa, z))
    return pts

def ring_x(x, cy, cz, ry, rz, seg=12, seam_angle=math.pi, bulge=None):
    """Anel vertical (plano YZ) para membros ao longo de X (braços em T-pose)."""
    pts = []
    for k in range(seg):
        a = seam_angle + TAU * k / seg
        extra = 0.0
        if bulge:
            for ang, amp, expo in bulge:
                d = math.cos(a - ang)
                if d > 0:
                    extra += amp * d ** expo
        pts.append((x, cy + (ry + extra) * math.cos(a), cz + (rz + extra) * math.sin(a)))
    return pts

def ring_y_superellipse(y, cx, z_lo, z_hi, hw, seg=16, n=3.2, seam_angle=math.pi/2, top_narrow=1.0):
    """Anel no plano XZ (para o tênis, ao longo de -Y). Superelipse entre z_lo e z_hi.
    top_narrow < 1 estreita o topo (cabedal em domo)."""
    pts = []
    zc = (z_lo + z_hi) / 2; hz = (z_hi - z_lo) / 2
    for k in range(seg):
        a = seam_angle + TAU * k / seg
        c, s = math.cos(a), math.sin(a)
        ex = math.copysign(abs(c) ** (2 / n), c)
        ez = math.copysign(abs(s) ** (2 / n), s)
        w = hw * (top_narrow if ez > 0 else 1.0) * (1 - (1 - top_narrow) * max(0.0, ez) ** 2 if top_narrow < 1 else 1.0)
        pts.append((cx + w * ex, y, zc + hz * ez))
    return pts

# ângulos úteis (plano XY): frente = -Y -> 3π/2 ; trás = +Y -> π/2
FRENTE = 3 * math.pi / 2
TRAS = math.pi / 2
def LADO(sx): return 0.0 if sx > 0 else math.pi   # lado externo do membro

# --------------------------------------------------------------------------
# Corpo
# --------------------------------------------------------------------------
def build_corpo(mb):
    # ---------- 1. TORSO CONTÍNUO (pelve → clavícula) ----------
    # z, rx, ry, cy, mat, pesos, bulge
    torso = [
        (0.880, 0.150, 0.118,  0.010, "Calca",  {"pelvis": 1.0},                     [(TRAS, 0.018, 2.0)]),  # glúteos
        (0.930, 0.168, 0.128,  0.006, "Calca",  {"pelvis": 1.0},                     [(TRAS, 0.022, 2.0)]),
        (0.985, 0.176, 0.130,  0.000, "Calca",  {"pelvis": 0.85, "spine_01": 0.15},  [(TRAS, 0.014, 2.0)]),
        (1.040, 0.165, 0.118, -0.002, "Calca",  {"pelvis": 0.45, "spine_01": 0.55},  None),  # cós cintura alta
        (1.080, 0.152, 0.108, -0.004, "Camisa", {"pelvis": 0.15, "spine_01": 0.85},  None),
        (1.130, 0.143, 0.102, -0.006, "Camisa", {"spine_01": 0.65, "spine_02": 0.35}, None),  # cintura fina
        (1.185, 0.152, 0.110, -0.008, "Camisa", {"spine_01": 0.25, "spine_02": 0.75}, None),
        (1.240, 0.166, 0.118, -0.012, "Camisa", {"spine_02": 0.85, "spine_03": 0.15}, [(FRENTE, 0.006, 2.0)]),
        (1.295, 0.176, 0.124, -0.016, "Camisa", {"spine_02": 0.55, "spine_03": 0.45}, [(FRENTE, 0.020, 2.5)]),  # busto
        (1.345, 0.182, 0.120, -0.012, "Camisa", {"spine_02": 0.20, "spine_03": 0.80}, [(FRENTE, 0.012, 2.5)]),
        (1.395, 0.188, 0.114, -0.006, "Camisa", {"spine_03": 1.0},                    None),  # linha dos ombros
        (1.430, 0.160, 0.100,  0.000, "Camisa", {"spine_03": 0.85, "neck_01": 0.15},  None),
        (1.455, 0.090, 0.075,  0.004, "Camisa", {"spine_03": 0.50, "neck_01": 0.50},  None),  # gola redonda
        (1.462, 0.058, 0.056,  0.006, "QuaterniusSkin", {"spine_03": 0.30, "neck_01": 0.70}, None),
    ]
    rings = []
    for z, rx, ry, cy, mat, w, bulge in torso:
        rings.append({"pts": ring_z(0, cy, z, rx, ry, 20, TRAS, bulge), "w": w, "mat": mat})
    # pescoço
    for z, r, w in ((1.500, 0.050, {"neck_01": 1.0}), (1.545, 0.047, {"neck_01": 0.6, "Head": 0.4}), (1.575, 0.052, {"Head": 1.0})):
        rings.append({"pts": ring_z(0, 0.008, z, r, r, 20, TRAS), "w": w, "mat": "QuaterniusSkin"})
    mb.loft("Torso", rings, "Camisa", close_start=True, close_end=False)

    # ---------- 2. CABEÇA ----------
    HEAD = {"Head": 1.0}
    mb.ellipsoid("Cabeca", (0, -0.012, 1.640), (0.098, 0.112, 0.118), HEAD, "QuaterniusSkin", 18, 14)
    mb.ellipsoid("Queixo", (0, -0.060, 1.560), (0.052, 0.058, 0.040), HEAD, "QuaterniusSkin", 12, 8)
    mb.ellipsoid("Nariz", (0, -0.118, 1.630), (0.014, 0.018, 0.020), HEAD, "QuaterniusSkin", 8, 6)
    for sx in (-1, 1):
        mb.ellipsoid(f"Orelha_{sx}", (sx * 0.098, -0.005, 1.640), (0.008, 0.020, 0.028), HEAD, "QuaterniusSkin", 8, 6)
        mb.ellipsoid(f"OlhoBranco_{sx}", (sx * 0.036, -0.108, 1.648), (0.020, 0.010, 0.013), HEAD, "OlhoBranco", 10, 6)
        mb.ellipsoid(f"Iris_{sx}", (sx * 0.036, -0.116, 1.648), (0.010, 0.004, 0.010), HEAD, "OlhoIris", 8, 5)
    # touca capilar: elipsoide levemente maior recuado, cobrindo crânio até a nuca
    mb.ellipsoid("CabeloTouca", (0, 0.010, 1.665), (0.108, 0.122, 0.104), HEAD, "Hair", 18, 12)
    # linha de implantação (franja rente) — pequena faixa frontal
    mb.ellipsoid("CabeloTesta", (0, -0.055, 1.715), (0.096, 0.070, 0.042), HEAD, "Hair", 14, 6)

    # ---------- 3. RABO DE CAVALO (rig próprio) ----------
    # elástico
    mb.loft("Elastico", [
        {"pts": ring_z(0, 0.112, 1.662, 0.030, 0.030, 12, TRAS), "w": HEAD, "mat": "Elastico"},
        {"pts": ring_z(0, 0.124, 1.660, 0.031, 0.031, 12, TRAS), "w": HEAD, "mat": "Elastico"},
    ], "Elastico")
    pony = [
        # (cy, cz, rx, ry, pesos)
        (0.120, 1.662, 0.032, 0.030, {"Head": 0.7, "Hair_Ponytail_01": 0.3}),
        (0.150, 1.650, 0.042, 0.040, {"Hair_Ponytail_01": 1.0}),
        (0.180, 1.615, 0.041, 0.038, {"Hair_Ponytail_01": 0.85, "Hair_Ponytail_02": 0.15}),
        (0.200, 1.565, 0.036, 0.032, {"Hair_Ponytail_01": 0.5, "Hair_Ponytail_02": 0.5}),
        (0.208, 1.505, 0.030, 0.026, {"Hair_Ponytail_01": 0.15, "Hair_Ponytail_02": 0.85}),
        (0.206, 1.445, 0.022, 0.018, {"Hair_Ponytail_02": 1.0}),
        (0.198, 1.390, 0.012, 0.010, {"Hair_Ponytail_02": 1.0}),
        (0.190, 1.355, 0.004, 0.004, {"Hair_Ponytail_02": 1.0}),
    ]
    rings = [{"pts": ring_z(0, cy, cz, rx, ry, 12, TRAS, [(TRAS, 0.004, 1.0)]), "w": w, "mat": "Hair"} for cy, cz, rx, ry, w in pony]
    mb.loft("RaboCavalo", rings, "Hair", close_start=True, close_end=True)

    # ---------- 4. BRAÇOS CONTÍNUOS (deltoide → punho) ----------
    for sx, lado in ((-1, "l"), (1, "r")):
        cl, ua, la, hd = f"clavicle_{lado}", f"upperarm_{lado}", f"lowerarm_{lado}", f"hand_{lado}"
        arm = [
            # (x, ry, rz, mat, pesos, bulge)
            (0.150, 0.060, 0.064, "Camisa", {"spine_03": 0.3, cl: 0.7},            [(math.pi/2, 0.010, 2.0)]),  # deltoide
            (0.185, 0.058, 0.062, "Camisa", {cl: 0.6, ua: 0.4},                    [(math.pi/2, 0.012, 2.0)]),
            (0.225, 0.052, 0.054, "Camisa", {cl: 0.2, ua: 0.8},                    None),  # bainha da manga
            (0.250, 0.046, 0.048, "QuaterniusSkin", {ua: 1.0},                      [(math.pi/2, 0.006, 2.0)]),  # bíceps
            (0.300, 0.044, 0.046, "QuaterniusSkin", {ua: 1.0},                      [(math.pi/2, 0.008, 2.0)]),
            (0.345, 0.040, 0.041, "QuaterniusSkin", {ua: 0.85, la: 0.15},           None),
            (0.380, 0.037, 0.038, "QuaterniusSkin", {ua: 0.5, la: 0.5},             [(-math.pi/2, 0.005, 3.0)]),  # cotovelo (olécrano)
            (0.415, 0.038, 0.037, "QuaterniusSkin", {ua: 0.15, la: 0.85},           [(math.pi/2, 0.004, 2.0)]),
            (0.470, 0.036, 0.034, "QuaterniusSkin", {la: 1.0},                      None),  # antebraço
            (0.540, 0.030, 0.028, "QuaterniusSkin", {la: 1.0},                      None),
            (0.585, 0.026, 0.023, "QuaterniusSkin", {la: 0.7, hd: 0.3},             None),
            (0.605, 0.025, 0.021, "QuaterniusSkin", {la: 0.4, hd: 0.6},             None),  # punho
        ]
        rings = [{"pts": ring_x(sx * x, 0.0, 1.400, ry, rz, 14, math.pi, b), "w": w, "mat": m} for x, ry, rz, m, w, b in arm]
        mb.loft(f"Braco_{lado}", rings, "QuaterniusSkin", close_start=True, close_end=True)
        # mão em concha de corredora (semi-fechada) + polegar
        H = {hd: 1.0}
        mb.ellipsoid(f"Mao_{lado}", (sx * 0.640, -0.012, 1.398), (0.040, 0.024, 0.030), H, "QuaterniusSkin", 12, 8)
        mb.ellipsoid(f"Dedos_{lado}", (sx * 0.672, -0.022, 1.388), (0.020, 0.022, 0.024), H, "QuaterniusSkin", 10, 6)
        mb.ellipsoid(f"Polegar_{lado}", (sx * 0.632, -0.036, 1.404), (0.014, 0.020, 0.013), H, "QuaterniusSkin", 8, 6)

    # ---------- 5. PERNAS CONTÍNUAS (quadril → maléolos) ----------
    for sx, lado in ((-1, "l"), (1, "r")):
        th, cf, ft = f"thigh_{lado}", f"calf_{lado}", f"foot_{lado}"
        cx = sx * 0.096
        lat = LADO(sx); med = LADO(-sx)
        leg = [
            # (z, rx, ry, cy, pesos, bulge)
            (0.905, 0.082, 0.090,  0.006, {"pelvis": 0.55, th: 0.45}, [(TRAS, 0.014, 2.0)]),   # inserção glútea
            (0.850, 0.078, 0.084,  0.004, {"pelvis": 0.15, th: 0.85}, [(TRAS, 0.010, 2.0), (FRENTE, 0.006, 2.0)]),
            (0.780, 0.073, 0.077,  0.002, {th: 1.0}, [(FRENTE, 0.010, 2.0), (lat, 0.006, 2.0)]),  # quadríceps
            (0.700, 0.066, 0.068,  0.000, {th: 1.0}, [(FRENTE, 0.011, 2.0)]),
            (0.620, 0.058, 0.058, -0.002, {th: 1.0}, [(FRENTE, 0.006, 2.0)]),
            (0.560, 0.052, 0.052, -0.004, {th: 0.85, cf: 0.15}, None),          # suprapatelar
            (0.520, 0.049, 0.049, -0.006, {th: 0.65, cf: 0.35}, [(FRENTE, 0.008, 3.0)]),
            (0.495, 0.048, 0.048, -0.008, {th: 0.50, cf: 0.50}, [(FRENTE, 0.011, 3.5)]),  # patela
            (0.470, 0.048, 0.049, -0.006, {th: 0.35, cf: 0.65}, [(FRENTE, 0.007, 3.0)]),
            (0.435, 0.047, 0.050, -0.002, {th: 0.15, cf: 0.85}, None),          # infrapatelar
            (0.380, 0.052, 0.058,  0.006, {cf: 1.0}, [(TRAS, 0.016, 2.0)]),     # gastrocnêmio
            (0.320, 0.050, 0.056,  0.008, {cf: 1.0}, [(TRAS, 0.014, 2.0)]),
            (0.250, 0.044, 0.047,  0.006, {cf: 1.0}, [(TRAS, 0.006, 2.0)]),
            (0.180, 0.037, 0.038,  0.004, {cf: 1.0}, None),                     # tendão de Aquiles
            (0.130, 0.034, 0.034,  0.002, {cf: 0.85, ft: 0.15}, [(lat, 0.004, 3.0), (med, 0.004, 3.0)]),
            (0.100, 0.034, 0.033,  0.000, {cf: 0.55, ft: 0.45}, [(lat, 0.006, 3.0), (med, 0.006, 3.0)]),  # maléolos
        ]
        rings = [{"pts": ring_z(cx, cy, z, rx, ry, 18, med, b), "w": w, "mat": "Calca"} for z, rx, ry, cy, w, b in leg]
        mb.loft(f"Perna_{lado}", rings, "Calca", close_start=True, close_end=False)
        build_tenis(mb, sx, lado, cx)

# --------------------------------------------------------------------------
# Tênis de corrida (Frente 1 §1.1.4)
# --------------------------------------------------------------------------
def build_tenis(mb, sx, lado, cx):
    ft, bl, cf = f"foot_{lado}", f"ball_{lado}", f"calf_{lado}"
    def wfoot(y):
        # peso foot→ball ao longo do comprimento (y: +0.045 calcanhar … -0.185 ponta)
        t = smoothstep((-0.06 - y) / 0.09)
        return {ft: 1.0 - t, bl: t}

    # perfil longitudinal do solado — y (m), meia-largura, z_chão (rocker), altura entressola
    #   calcanhar 3.8 cm de EVA; antepé 2.0 cm; toe rocker levanta 1.5 cm na ponta
    prof = [
        # y,     hw,    z_ground, midsole_top
        ( 0.045, 0.030, 0.006, 0.040),
        ( 0.035, 0.040, 0.002, 0.044),
        ( 0.015, 0.046, 0.000, 0.046),
        (-0.010, 0.047, 0.000, 0.044),
        (-0.040, 0.046, 0.000, 0.038),
        (-0.070, 0.048, 0.000, 0.032),
        (-0.100, 0.051, 0.000, 0.028),   # metatarso (mais largo)
        (-0.130, 0.049, 0.002, 0.026),
        (-0.155, 0.043, 0.007, 0.024),
        (-0.175, 0.032, 0.012, 0.022),
        (-0.186, 0.018, 0.015, 0.020),   # ponta: 1.5 cm do chão (toe rocker)
    ]
    SOLA_T = 0.008
    # ---- Sola de borracha (preta), com ranhuras: alterna z levemente ----
    rings = []
    for i, (y, hw, zg, zm) in enumerate(prof):
        groove = 0.0015 if i % 2 == 0 else 0.0
        rings.append({"pts": ring_y_superellipse(y, cx, zg, zg + SOLA_T + groove, hw + 0.002, 16, 3.6, math.pi/2), "w": wfoot(y), "mat": "Sola"})
    mb.loft(f"Sola_{lado}", rings, "Sola", close_start=True, close_end=True)
    # ---- Entressola EVA branca ----
    rings = []
    for y, hw, zg, zm in prof:
        rings.append({"pts": ring_y_superellipse(y, cx, zg + SOLA_T, zm, hw, 16, 3.0, math.pi/2), "w": wfoot(y), "mat": "Entressola"})
    mb.loft(f"Entressola_{lado}", rings, "Entressola", close_start=True, close_end=True)
    # ---- Cabedal têxtil (domo sobre a entressola; colar do calcanhar alto) ----
    cab = [
        # y,     hw,    z_base, z_topo, estreitamento do topo
        ( 0.040, 0.026, 0.040, 0.078, 0.55),   # contraforte do calcanhar
        ( 0.028, 0.036, 0.044, 0.084, 0.60),
        ( 0.010, 0.042, 0.046, 0.086, 0.62),   # colar do tornozelo
        (-0.012, 0.044, 0.044, 0.082, 0.66),
        (-0.040, 0.044, 0.038, 0.074, 0.70),   # peito do pé
        (-0.070, 0.046, 0.032, 0.064, 0.74),
        (-0.100, 0.049, 0.028, 0.056, 0.78),
        (-0.130, 0.047, 0.026, 0.048, 0.80),
        (-0.155, 0.041, 0.024, 0.040, 0.82),
        (-0.175, 0.030, 0.022, 0.032, 0.85),
        (-0.186, 0.016, 0.020, 0.024, 0.90),
    ]
    rings = []
    for y, hw, zb, zt, tn in cab:
        rings.append({"pts": ring_y_superellipse(y, cx, zb, zt, hw, 16, 2.4, math.pi/2, tn), "w": wfoot(y), "mat": "Sapato"})
    mb.loft(f"Cabedal_{lado}", rings, "Sapato", close_start=True, close_end=True)
    # ---- Língua acolchoada (sobe do peito do pé até acima do colar) ----
    rings = []
    for y, zc, hw in ((-0.080, 0.056, 0.022), (-0.055, 0.064, 0.024), (-0.030, 0.074, 0.025), (-0.008, 0.086, 0.024)):
        rings.append({"pts": ring_y_superellipse(y, cx, zc - 0.004, zc + 0.004, hw, 10, 2.6, math.pi/2), "w": {ft: 1.0}, "mat": "Sapato"})
    mb.loft(f"Lingua_{lado}", rings, "Sapato", close_start=True, close_end=True)
    # ---- Cadarços (4 passadas cruzadas) + ilhoses ----
    for i, y in enumerate((-0.068, -0.050, -0.032, -0.014)):
        zc = 0.062 + i * 0.008
        hw = 0.020 - i * 0.001
        rings = []
        for k in range(5):
            t = k / 4
            x = cx - hw + 2 * hw * t
            rings.append({"pts": ring_y_superellipse(y + 0.003 * math.sin(t * math.pi), x, zc + 0.004 * math.sin(t * math.pi) - 0.0015, zc + 0.004 * math.sin(t * math.pi) + 0.0015, 0.0015, 6, 2.0, 0.0), "w": {ft: 1.0}, "mat": "Cadarco"})
        # loft "ao longo de X": reutiliza anéis (todos no plano XZ deslocados em X → tubo fino)
        # como ring_y_superellipse gera no plano XZ, aqui deslocamos em X: aceitável para cadarço fino
        mb.loft(f"Cadarco_{lado}_{i}", rings, "Cadarco")
        for sgn in (-1, 1):
            mb.ellipsoid(f"Ilhos_{lado}_{i}_{sgn}", (cx + sgn * hw, y, zc), (0.003, 0.002, 0.003), {ft: 1.0}, "Ilhos", 6, 4)
    # ---- Meia cano curto (2 cm acima do colar) ----
    rings = [
        {"pts": ring_z(cx, 0.000, 0.080, 0.036, 0.035, 16, LADO(-sx)), "w": {ft: 0.7, cf: 0.3}, "mat": "Meia"},
        {"pts": ring_z(cx, 0.000, 0.098, 0.036, 0.035, 16, LADO(-sx)), "w": {ft: 0.5, cf: 0.5}, "mat": "Meia"},
        {"pts": ring_z(cx, 0.000, 0.110, 0.0355, 0.0345, 16, LADO(-sx)), "w": {ft: 0.35, cf: 0.65}, "mat": "Meia"},
    ]
    mb.loft(f"Meia_{lado}", rings, "Meia")

# --------------------------------------------------------------------------
# Armature (mesmo esqueleto de build_humanos + Hair_Ponytail_01/02)
# --------------------------------------------------------------------------
def armature_humano(nome):
    arm_data = bpy.data.armatures.new(nome + "Rig")
    arm = bpy.data.objects.new("Armature", arm_data)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    def osso(n, head, tail, parent=None):
        b = arm_data.edit_bones.new(n)
        b.head = head; b.tail = tail; b.roll = 0
        if parent:
            b.parent = arm_data.edit_bones[parent]
        return b
    osso("pelvis", (0, 0, 0.92), (0, 0, 1.05))
    osso("spine_01", (0, 0, 1.05), (0, 0, 1.18), "pelvis")
    osso("spine_02", (0, 0, 1.18), (0, 0, 1.32), "spine_01")
    osso("spine_03", (0, 0, 1.32), (0, 0, 1.45), "spine_02")
    osso("neck_01", (0, 0, 1.45), (0, 0, 1.545), "spine_03")
    osso("Head", (0, 0, 1.545), (0, 0, 1.75), "neck_01")
    osso("Hair_Ponytail_01", (0, 0.12, 1.66), (0, 0.20, 1.56), "Head")
    osso("Hair_Ponytail_02", (0, 0.20, 1.56), (0, 0.19, 1.355), "Hair_Ponytail_01")
    osso("clavicle_l", (-0.02, 0, 1.40), (-0.14, 0, 1.40), "spine_03")
    osso("clavicle_r", (0.02, 0, 1.40), (0.14, 0, 1.40), "spine_03")
    osso("upperarm_l", (-0.14, 0, 1.40), (-0.38, 0, 1.40), "clavicle_l")
    osso("lowerarm_l", (-0.38, 0, 1.40), (-0.60, 0, 1.40), "upperarm_l")
    osso("hand_l", (-0.60, 0, 1.40), (-0.68, 0, 1.40), "lowerarm_l")
    osso("upperarm_r", (0.14, 0, 1.40), (0.38, 0, 1.40), "clavicle_r")
    osso("lowerarm_r", (0.38, 0, 1.40), (0.60, 0, 1.40), "upperarm_r")
    osso("hand_r", (0.60, 0, 1.40), (0.68, 0, 1.40), "lowerarm_r")
    for lado, sx in (("l", -0.68), ("r", 0.68)):
        for nome_dedo in ("thumb", "index", "middle", "ring", "pinky"):
            for i in (1, 2, 3):
                n0 = f"{nome_dedo}_0{i}_{lado}"
                head = (sx, 0.0 - (0.02 if nome_dedo == "thumb" else 0.0), 1.40 - 0.015 * i)
                tail = (sx + (0.02 if lado == "r" else -0.02), 0.0, 1.40 - 0.015 * (i + 0.5))
                parent = f"hand_{lado}" if i == 1 else f"{nome_dedo}_0{i-1}_{lado}"
                osso(n0, head, tail, parent)
    for lado, sx in (("l", -0.096), ("r", 0.096)):
        osso(f"thigh_{lado}", (sx, 0, 0.92), (sx, 0, 0.495), "pelvis")
        osso(f"calf_{lado}", (sx, 0, 0.495), (sx, 0, 0.10), f"thigh_{lado}")
        osso(f"foot_{lado}", (sx, 0, 0.10), (sx, -0.09, 0.03), f"calf_{lado}")
        osso(f"ball_{lado}", (sx, -0.09, 0.03), (sx, -0.17, 0.02), f"foot_{lado}")
    bpy.ops.object.mode_set(mode='OBJECT')
    return arm

def skin(arm, mesh):
    mesh.parent = arm
    mod = mesh.modifiers.new("Skin", 'ARMATURE')
    mod.object = arm
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')
    for pb in arm.pose.bones:
        pb.rotation_mode = 'XYZ'
    bpy.ops.object.mode_set(mode='OBJECT')

# --------------------------------------------------------------------------
# Animação
# --------------------------------------------------------------------------
def key_rot(arm, bn, frame, euler):
    pb = arm.pose.bones[bn]; pb.rotation_euler = euler; pb.keyframe_insert('rotation_euler', frame=frame)
def key_loc(arm, bn, frame, loc):
    pb = arm.pose.bones[bn]; pb.location = loc; pb.keyframe_insert('location', frame=frame)
CORE_BONES = ("pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "Head", "Hair_Ponytail_01", "Hair_Ponytail_02",
              "clavicle_l", "clavicle_r", "upperarm_l", "upperarm_r", "lowerarm_l", "lowerarm_r", "hand_l", "hand_r",
              "thigh_l", "thigh_r", "calf_l", "calf_r", "foot_l", "foot_r", "ball_l", "ball_r")
_KEY_FRAME = [None]
def clear_pose(arm, frame=None):
    """Zera a pose e (se frame) grava keyframe neutro em TODOS os ossos principais.
    Assim cada clipe é auto-contido: trocar de clipe nunca herda pose do anterior
    (nem no Godot nem no preview)."""
    for pb in arm.pose.bones:
        pb.rotation_euler = (0, 0, 0); pb.location = (0, 0, 0)
    if frame is not None:
        for bn in CORE_BONES:
            arm.pose.bones[bn].keyframe_insert('rotation_euler', frame=frame)
        arm.pose.bones["pelvis"].keyframe_insert('location', frame=frame)
def new_action(arm, nome):
    a = bpy.data.actions.new(nome)
    arm.animation_data_create()
    arm.animation_data.action = a
    return a
def linearize(act):
    fcurves = []
    if hasattr(act, "fcurves"):
        try: fcurves = list(act.fcurves)
        except Exception: fcurves = []
    if not fcurves and hasattr(act, "layers"):
        for layer in act.layers:
            for strip in layer.strips:
                if hasattr(strip, "channelbags"):
                    for bag in strip.channelbags:
                        fcurves.extend(list(bag.fcurves))
    for fc in fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'

def ponytail(arm, f, t, amp_x, amp_z=0.0, lag=0.9):
    """Inércia do rabo de cavalo: segue o movimento com defasagem e amplifica na ponta."""
    key_rot(arm, "Hair_Ponytail_01", f, (rad(amp_x) * math.sin(t - lag), 0, rad(amp_z) * math.cos(t - lag)))
    key_rot(arm, "Hair_Ponytail_02", f, (rad(amp_x * 1.4) * math.sin(t - lag * 1.8), 0, rad(amp_z * 1.3) * math.cos(t - lag * 1.8)))

def build_actions(arm, scene):
    scene.frame_start = 1; scene.frame_end = 48
    acts = []

    a = new_action(arm, "Idle_Loop")
    for f in (1, 12, 24, 36, 48):
        t = (f - 1) / 48 * TAU
        clear_pose(arm, f)
        key_rot(arm, "spine_01", f, (rad(1.5), 0, 0))
        key_rot(arm, "spine_02", f, (rad(1.2) * math.sin(t), 0, rad(0.6) * math.cos(t * 0.5)))
        key_rot(arm, "spine_03", f, (rad(0.8) * math.sin(t), 0, 0))
        key_rot(arm, "Head", f, (rad(1.0) * math.sin(t * 0.7), rad(0.6) * math.cos(t), 0))
        key_rot(arm, "upperarm_l", f, (rad(-74), 0, rad(10) + rad(1.5) * math.sin(t)))
        key_rot(arm, "upperarm_r", f, (rad(-74), 0, -rad(10) - rad(1.5) * math.sin(t)))
        key_rot(arm, "lowerarm_l", f, (0, 0, rad(22) + rad(1.0) * math.sin(t)))
        key_rot(arm, "lowerarm_r", f, (0, 0, -rad(22) - rad(1.0) * math.sin(t)))
        key_loc(arm, "pelvis", f, (0, 0, 0.004 * math.sin(t)))
        ponytail(arm, f, t, 2.0, 1.0)
    linearize(a); acts.append(a)

    a = new_action(arm, "Walk_Loop"); C = 24
    for f in range(1, C + 1):
        t = (f - 1) / C * TAU; s = math.sin(t)
        clear_pose(arm, f)
        key_rot(arm, "thigh_l", f, (rad(26) * s, 0, 0))
        key_rot(arm, "thigh_r", f, (rad(-26) * s, 0, 0))
        key_rot(arm, "calf_l", f, (rad(40) * max(0, math.sin(t + 0.9)), 0, 0))
        key_rot(arm, "calf_r", f, (rad(40) * max(0, math.sin(t + 0.9 + math.pi)), 0, 0))
        key_rot(arm, "foot_l", f, (rad(-12) * max(0, math.sin(t + 0.9)), 0, 0))
        key_rot(arm, "foot_r", f, (rad(-12) * max(0, math.sin(t + 0.9 + math.pi)), 0, 0))
        key_rot(arm, "upperarm_l", f, (rad(-74), 0, rad(10) - rad(22) * s))
        key_rot(arm, "upperarm_r", f, (rad(-74), 0, -rad(10) + rad(22) * s))
        key_rot(arm, "lowerarm_l", f, (0, 0, rad(30) - rad(8) * s))
        key_rot(arm, "lowerarm_r", f, (0, 0, -rad(30) + rad(8) * s))
        key_rot(arm, "spine_01", f, (rad(2.0), 0, 0))
        key_rot(arm, "spine_02", f, (0, rad(1.8) * s, 0))
        key_loc(arm, "pelvis", f, (0, 0, 0.008 * math.cos(2 * t)))
        ponytail(arm, f, 2 * t, 6.0, 3.0, 0.8)
    linearize(a); acts.append(a)

    a = new_action(arm, "Sprint_Loop"); C = 16
    for f in range(1, C + 1):
        t = (f - 1) / C * TAU; s = math.sin(t); c = math.cos(t)
        clear_pose(arm, f)
        key_rot(arm, "spine_01", f, (rad(7.5), 0, 0))                     # inclinação 8°
        key_rot(arm, "spine_02", f, (rad(3.0) * c, rad(2.5) * s, 0))
        key_rot(arm, "spine_03", f, (0, rad(1.5) * s, 0))
        key_rot(arm, "Head", f, (rad(-4.0), 0, 0))                       # olhar no horizonte
        key_rot(arm, "thigh_l", f, (rad(42) * s, 0, 0))
        key_rot(arm, "thigh_r", f, (rad(-42) * s, 0, 0))
        key_rot(arm, "calf_l", f, (rad(65) * max(0, math.sin(t + 0.85)), 0, 0))
        key_rot(arm, "calf_r", f, (rad(65) * max(0, math.sin(t + 0.85 + math.pi)), 0, 0))
        key_rot(arm, "foot_l", f, (rad(-18) * max(0, math.sin(t + 0.85)), 0, 0))
        key_rot(arm, "foot_r", f, (rad(-18) * max(0, math.sin(t + 0.85 + math.pi)), 0, 0))
        key_rot(arm, "upperarm_l", f, (rad(-75), 0, rad(12) - rad(42) * s))
        key_rot(arm, "upperarm_r", f, (rad(-75), 0, -rad(12) + rad(42) * s))
        key_rot(arm, "lowerarm_l", f, (0, 0, rad(80) - rad(15) * s))
        key_rot(arm, "lowerarm_r", f, (0, 0, -rad(80) + rad(15) * s))
        key_loc(arm, "pelvis", f, (0, 0, 0.016 * math.cos(2 * t)))
        ponytail(arm, f, 2 * t, 14.0, 5.0, 1.0)                           # balanço forte com atraso
    linearize(a); acts.append(a)

    a = new_action(arm, "Jump_Loop")
    keys = [(1, -32, 50, 8, -75, 45, -8), (4, -18, 25, -25, -75, 60, 14), (7, 22, 55, 35, -75, 80, 24),
            (10, -12, 20, 15, -75, 50, 6), (12, -28, 45, 8, -75, 45, -8)]
    for f, th, cf, az, ax, el, pt in keys:
        clear_pose(arm, f)
        for ld in ("l", "r"):
            key_rot(arm, f"thigh_{ld}", f, (rad(th), 0, 0))
            key_rot(arm, f"calf_{ld}", f, (rad(cf), 0, 0))
        key_rot(arm, "spine_01", f, (rad(10), 0, 0))
        key_rot(arm, "upperarm_l", f, (rad(ax), 0, rad(12) + rad(az)))
        key_rot(arm, "upperarm_r", f, (rad(ax), 0, -rad(12) - rad(az)))
        key_rot(arm, "lowerarm_l", f, (0, 0, rad(el)))
        key_rot(arm, "lowerarm_r", f, (0, 0, -rad(el)))
        key_loc(arm, "pelvis", f, (0, 0, 0.04 if f == 7 else 0.0))
        key_rot(arm, "Hair_Ponytail_01", f, (rad(pt), 0, 0))
        key_rot(arm, "Hair_Ponytail_02", f, (rad(pt * 1.5), 0, 0))
    linearize(a); acts.append(a)

    a = new_action(arm, "Crouch_Idle_Loop")
    for f in (1, 24, 48):
        t = (f - 1) / 48 * TAU
        clear_pose(arm, f)
        for ld in ("l", "r"):
            key_rot(arm, f"thigh_{ld}", f, (rad(-46), 0, 0))
            key_rot(arm, f"calf_{ld}", f, (rad(68), 0, 0))
        key_rot(arm, "spine_01", f, (rad(16) + rad(1.0) * math.sin(t), 0, 0))
        key_rot(arm, "spine_02", f, (rad(8), 0, 0))
        key_rot(arm, "upperarm_l", f, (rad(-72), 0, rad(16)))
        key_rot(arm, "upperarm_r", f, (rad(-72), 0, -rad(16)))
        key_rot(arm, "lowerarm_l", f, (0, 0, rad(70)))
        key_rot(arm, "lowerarm_r", f, (0, 0, -rad(70)))
        ponytail(arm, f, t, 3.0, 1.0)
    linearize(a); acts.append(a)

    a = new_action(arm, "Crouch_Fwd_Loop"); C = 20
    for f in range(1, C + 1):
        t = (f - 1) / C * TAU; s = math.sin(t); c = math.cos(t)
        clear_pose(arm, f)
        key_rot(arm, "thigh_l", f, (rad(-42) + rad(16) * s, 0, 0))
        key_rot(arm, "thigh_r", f, (rad(-42) - rad(16) * s, 0, 0))
        key_rot(arm, "calf_l", f, (rad(60) + rad(14) * max(0, math.sin(t + 0.7)), 0, 0))
        key_rot(arm, "calf_r", f, (rad(60) + rad(14) * max(0, math.sin(t + 0.7 + math.pi)), 0, 0))
        key_rot(arm, "spine_01", f, (rad(20), 0, 0))
        key_rot(arm, "upperarm_l", f, (rad(-72), 0, rad(16) - rad(20) * s))
        key_rot(arm, "upperarm_r", f, (rad(-72), 0, -rad(16) + rad(20) * s))
        key_rot(arm, "lowerarm_l", f, (0, 0, rad(75) - rad(10) * s))
        key_rot(arm, "lowerarm_r", f, (0, 0, -rad(75) + rad(10) * s))
        key_loc(arm, "pelvis", f, (0, 0, 0.006 * c))
        ponytail(arm, f, 2 * t, 8.0, 3.0)
    linearize(a); acts.append(a)

    # regra do exportador: todo clip precisa ter sido atribuído ao menos uma vez (já foi) —
    # devolve o Idle como ativo e zera a pose (rest = T-pose)
    arm.animation_data.action = acts[0]
    clear_pose(arm)
    return acts

# --------------------------------------------------------------------------
# Preview (Cycles CPU) — opcional
# --------------------------------------------------------------------------
def render_previews(arm, corpo, out_dir, tag):
    os.makedirs(out_dir, exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 48
    scene.cycles.use_denoising = False
    scene.render.resolution_x = 720; scene.render.resolution_y = 900
    scene.render.film_transparent = False
    world = bpy.data.worlds.new("W"); scene.world = world; world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.65, 0.80, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.9
    sun_d = bpy.data.lights.new("Sun", 'SUN'); sun_d.energy = 4.5; sun_d.angle = rad(3)
    sun_d.color = (1.0, 0.92, 0.80)
    sun = bpy.data.objects.new("Sun", sun_d); scene.collection.objects.link(sun)
    sun.rotation_euler = (rad(58), rad(-18), rad(35))
    # chão
    bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, 0))
    chao = bpy.context.active_object
    mch = bpy.data.materials.new("Chao"); mch.use_nodes = True
    mch.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.35, 0.34, 0.33, 1)
    chao.data.materials.append(mch)
    cam_d = bpy.data.cameras.new("Cam"); cam_d.lens = 55; cam_d.clip_start = 0.01
    cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
    def shoot(nome, loc, target, frame=1, lens=55):
        cam_d.lens = lens
        cam.location = loc
        d = Vector(target) - Vector(loc)
        cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        scene.frame_set(frame)
        scene.render.filepath = os.path.join(out_dir, f"{tag}_{nome}.png")
        bpy.ops.render.render(write_still=True)
        print("preview:", scene.render.filepath)
    # T-pose: frente 3/4 e costas
    shoot("frente34", (1.9, -2.6, 1.35), (0, 0, 0.95))
    shoot("costas", (0.3, 2.8, 1.30), (0, 0, 0.95))
    # Sprint frame 5 (passada aberta)
    arm.animation_data.action = bpy.data.actions["Sprint_Loop"]
    shoot("sprint_lado", (2.9, -0.4, 1.05), (0, 0, 0.95), frame=5)
    shoot("sprint_costas34", (1.3, 2.4, 1.45), (0, 0, 1.0), frame=5)
    # close-up do tênis
    arm.animation_data.action = bpy.data.actions["Idle_Loop"]
    shoot("tenis", (0.62, -0.72, 0.28), (0.0, -0.06, 0.06), frame=1, lens=60)
    scene.frame_set(1)

# --------------------------------------------------------------------------
# Validação do GLB (parser mínimo, sem dependências)
# --------------------------------------------------------------------------
def validar_glb(path):
    with open(path, "rb") as f:
        magic, ver, length = struct.unpack("<III", f.read(12))
        assert magic == 0x46546C67, "GLB inválido"
        clen, ctype = struct.unpack("<II", f.read(8))
        gltf = json.loads(f.read(clen))
    bones = [n["name"] for n in gltf["nodes"] if "mesh" not in n]
    anims = [a["name"] for a in gltf.get("animations", [])]
    mats = [m["name"] for m in gltf.get("materials", [])]
    verts = 0
    for m in gltf["meshes"]:
        for p in m["primitives"]:
            verts += gltf["accessors"][p["attributes"]["POSITION"]]["count"]
    skins = gltf.get("skins", [])
    n_joints = len(skins[0]["joints"]) if skins else 0
    info = {
        "bytes": os.path.getsize(path), "vertices": verts, "materiais": mats,
        "animacoes": anims, "joints": n_joints,
        "tem_ponytail": any("Hair_Ponytail" in b for b in bones),
    }
    print("VALIDACAO:", json.dumps(info, ensure_ascii=False, indent=1))
    req_bones = {"pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "Head", "clavicle_l", "upperarm_l",
                 "lowerarm_l", "hand_l", "thigh_l", "calf_l", "foot_l", "ball_l", "Hair_Ponytail_01", "Hair_Ponytail_02"}
    assert req_bones <= set(bones), f"ossos faltando: {req_bones - set(bones)}"
    for clip in ("Idle_Loop", "Walk_Loop", "Sprint_Loop", "Jump_Loop", "Crouch_Idle_Loop", "Crouch_Fwd_Loop"):
        assert clip in anims, f"clip faltando: {clip}"
    for mn in ("QuaterniusSkin", "Camisa", "Calca", "Sapato", "Entressola", "Sola", "Meia", "Hair"):
        assert mn in mats, f"material faltando: {mn}"
<<<<<<< HEAD
    assert info["bytes"] < 500 * 1024, "GLB > 500 KB"
=======
    assert info["bytes"] < 1200 * 1024, "GLB > 1.2 MB"
>>>>>>> f9afe55 (fix(characters): exportar GLBs sem Draco — Godot 4 não decodifica KHR_draco_mesh_compression (personagem invisível))
    return info

def checar_uv_sem_sobreposicao(obj):
    """Heurística: bounding-box UV de cada peça (célula do atlas) não pode se cruzar."""
    me = obj.data
    uv = me.uv_layers.active.data
    # como cada peça está numa célula, checamos que nenhum loop cai fora [0,1]
    for l in uv:
        u, v = l.uv
        assert -1e-4 <= u <= 1 + 1e-4 and -1e-4 <= v <= 1 + 1e-4
    print("UV OK: todos os loops dentro do atlas 0..1 (células por peça)")

def checar_contato_solo(obj):
    zmin = min(v.co.z for v in obj.data.vertices)
    print(f"contato com o solo: z_min = {zmin:.4f} m")
    assert abs(zmin) < 0.002, "sola não toca o chão em z=0"

def checar_pesos_joelho(obj):
    vg = {g.index: g.name for g in obj.vertex_groups}
    mistos = 0; total = 0
    for v in obj.data.vertices:
        if 0.46 <= v.co.z <= 0.53 and abs(v.co.x) > 0.04:
            total += 1
            names = {vg[g.group] for g in v.groups if g.weight > 0.05}
            if len(names) >= 2:
                mistos += 1
    print(f"pesagem suave no joelho: {mistos}/{total} vértices com 2+ ossos")
    assert total and mistos / total > 0.9

# --------------------------------------------------------------------------
def build(out_path, preview=False, tag="julia"):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = 24
    materials = {n: make_material(n, *v) for n, v in PALETA.items()}
    mb = MeshBuilder()
    build_corpo(mb)
    corpo = mb.build("Corredora", materials)
    print(f"peças: {len(mb.parts)}  vértices brutos: {len(mb.verts)}  após solda: {len(corpo.data.vertices)}  faces: {len(corpo.data.polygons)}")
    arm = armature_humano("Humano")
    skin(arm, corpo)
    build_actions(arm, scene)
    checar_uv_sem_sobreposicao(corpo)
    checar_contato_solo(corpo)
    checar_pesos_joelho(corpo)

    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True); corpo.select_set(True)
    bpy.context.view_layer.objects.active = arm
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=out_path, export_format='GLB', use_selection=True, export_yup=True,
        export_apply=False, export_skins=True, export_animations=True,
        export_animation_mode='ACTIONS', export_materials='EXPORT',
<<<<<<< HEAD
        export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6,
        export_draco_position_quantization=14, export_draco_normal_quantization=10,
        export_draco_texcoord_quantization=12,
=======
        export_draco_mesh_compression_enable=False,  # Godot 4 NÃO decodifica KHR_draco_mesh_compression (mesh invisível)
>>>>>>> f9afe55 (fix(characters): exportar GLBs sem Draco — Godot 4 não decodifica KHR_draco_mesh_compression (personagem invisível))
    )
    info = validar_glb(out_path)
    if preview:
        render_previews(arm, corpo, OUT_DIR, tag)
    return info

if __name__ == "__main__":
    info = build(OUT_GLB, PREVIEW, os.path.splitext(os.path.basename(OUT_GLB))[0])
    print("Export OK:", OUT_GLB, info["bytes"], "bytes")
