#!/usr/bin/env python3
"""Herói 10/10 — Fase 3A: rosto da heroína Júlia (sem cabelo).

Entrada padrão: ``tools/blender/out/heroi_julia_pbr.glb`` da Fase 2.
Saídas (não versionadas):
  - ``tools/blender/out/heroi_julia_rosto.glb``
  - ``tools/blender/out/heroi_julia_rosto.blend``
  - ``tools/blender/out/heroi_julia_rosto_metrics.json``

Esta é propositalmente a primeira metade da Fase 3. Ela constrói e torna
avaliável o rosto inteiro -- olhos em órbitas, pálpebras, sobrancelhas, cílios,
nariz com narinas e boca com lábios -- sem criar qualquer massa, card ou mecha
de cabelo. Assim a aprovação da identidade facial não fica escondida por uma
silhueta de cabelo que ainda não foi validada.

Uso:
  sh tools/blender/run_bpy.sh tools/blender/build_rosto_heroi_julia.py
  sh tools/blender/run_bpy.sh tools/blender/build_rosto_heroi_julia.py -- \
      --input tools/blender/out/heroi_julia_pbr.glb --output /tmp/rosto.glb
"""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector

REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "tools" / "blender" / "out"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Espaço do modelo antes do export glTF: Z para cima e a frente da personagem
# olha para -Y. Os valores seguem os marcos que já esculpem o crânio em
# build_heroi_julia.py. São concentrados aqui para a revisão artística ser
# objetiva e não exigir mexer em cabelo/rig.
FACE = {
    "eye_z": 1.587,
    "eye_x": 0.043,
    # Centro da nova superfície facial: a abertura fica rente à órbita em vez
    # de projetar um globo para fora do rosto.
    "eye_y": -0.093,
    "brow_z": 1.614,
    "nose_z": 1.558,
    "mouth_z": 1.524,
}


def log(msg: str) -> None:
    print(f"[rosto] {msg}", flush=True)


def active(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    return obj


def clean_name(name: str) -> str:
    """Nome ASCII estável no GLB; o rótulo humano entra como custom property."""
    return name.replace(" ", "_").replace("ç", "c").replace("ã", "a").replace("á", "a").replace("í", "i")


def principled(name: str, color, rough=0.5, metallic=0.0, subsurface=0.0):
    """Material PBR deliberadamente simples e exportável para glTF/Godot."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    if "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = subsurface
        bsdf.inputs["Subsurface Radius"].default_value = (0.012, 0.005, 0.003)
        bsdf.inputs["Subsurface Scale"].default_value = 0.010
    mat.node_tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def face_materials():
    # Tons lineares calibrados para a pele morena quente já bakeada na Fase 2.
    # Pálpebra/nariz usam a mesma família de cor; não há base lisa bege que
    # transforme o close em uma máscara de plástico.
    return {
        "skin_detail": principled("RostoPeleDetalhe", (0.31, 0.125, 0.066), 0.64, subsurface=0.05),
        "skin_shadow": principled("RostoPeleSombra", (0.18, 0.052, 0.026), 0.61, subsurface=0.04),
        "sclera": principled("OlhoEsclera", (0.87, 0.70, 0.54), 0.24, subsurface=0.04),
        "iris_outer": principled("IrisAnel", (0.070, 0.016, 0.006), 0.31),
        "iris_inner": principled("IrisCastanha", (0.245, 0.055, 0.012), 0.28),
        "pupil": principled("Pupila", (0.003, 0.002, 0.001), 0.20),
        "highlight": principled("OlhoBrilho", (1.0, 0.96, 0.90), 0.12),
        "brow": principled("Sobrancelha", (0.020, 0.006, 0.003), 0.74),
        "lash": principled("Cilios", (0.007, 0.002, 0.001), 0.72),
        "lip": principled("LabiosJulia", (0.22, 0.022, 0.012), 0.58, subsurface=0.03),
        "mouth": principled("InteriorBoca", (0.045, 0.004, 0.003), 0.66),
    }


def smooth(obj):
    if obj.type == "MESH":
        for poly in obj.data.polygons:
            poly.use_smooth = True
    return obj


def add_uv_ellipsoid(name, location, scale, mat, segments=24, rings=12, label=None):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments,
        ring_count=rings,
        location=location,
    )
    obj = bpy.context.object
    obj.name = clean_name(name)
    obj["face_feature"] = label or name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    smooth(obj)
    return obj


def add_curve_tube(name, points, radius, mat, resolution=2, label=None):
    """Tubo PBR ao longo de uma polilinha; mais robusto que transparência/card.

    É usado para as bordas das pálpebras, sobrancelha, cílios e linha da boca.
    São superfícies reais, portanto continuam legíveis no renderer mobile e não
    apresentam os problemas de ordenação alpha que o cabelo terá de resolver
    separadamente na parte 3B.
    """
    curve = bpy.data.curves.new(clean_name(name), "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = resolution
    curve.bevel_depth = radius
    curve.bevel_resolution = 2
    curve.resolution_u = 2
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for bp, co in zip(spline.bezier_points, points):
        bp.co = co
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(clean_name(name), curve)
    bpy.context.scene.collection.objects.link(obj)
    obj["face_feature"] = label or name
    obj.data.materials.append(mat)
    return obj


def add_disc(name, center, radius, depth, mat, label=None, segments=24):
    """Disco convexo voltado para -Y. Esferas achatadas evitam z-fighting."""
    return add_uv_ellipsoid(name, center, (radius, depth, radius), mat, segments, 12, label)


def add_almond_eye(name, center, width, height, mat, label="esclera"):
    """Olho em formato amendoado, exatamente rente à órbita.

    Uma esfera achatada ainda desenhava um círculo inteiro no close. A malha
    fechada abaixo permite a leitura anatômica de canto interno/externo e dá
    à pálpebra uma abertura real, sem depender de transparência.
    """
    cx, cy, cz = center
    upper = [
        (-1.00, 0.00), (-0.78, 0.24), (-0.48, 0.43), (0.00, 0.53),
        (0.48, 0.45), (0.78, 0.25), (1.00, 0.00),
    ]
    lower = [
        (1.00, 0.00), (0.76, -0.22), (0.46, -0.38), (0.00, -0.47),
        (-0.46, -0.38), (-0.76, -0.22), (-1.00, 0.00),
    ]
    outline = upper + lower
    # centro + contorno; fan duplo para manter a leitura em GLTF com culling.
    verts = [(cx, cy, cz)] + [(cx + x * width, cy, cz + z * height) for x, z in outline]
    count = len(outline)
    faces = []
    for i in range(count):
        j = (i + 1) % count
        faces.append((0, i + 1, j + 1))
    mesh = bpy.data.meshes.new(clean_name(name))
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(clean_name(name), mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj["face_feature"] = label
    obj.data.materials.append(mat)
    return obj


def add_lip_ribbon(name, upper, lower, y, mat, label):
    """Faixa de lábio suavemente convexa, rente à superfície facial.

    Ao contrário de uma curva tubular, a faixa não parece um arame rosado nem
    projeta uma sombra dura quando vista em perfil. A face é dupla porque a
    exportação glTF pode aplicar back-face culling no renderer mobile.
    """
    if len(upper) != len(lower):
        raise ValueError("as bordas do lábio precisam ter a mesma quantidade de pontos")
    # Casca fechada de 0,35 mm: um plano duplicado deixava arestas non-manifold
    # e o exportador glTF o marcava como inválido.
    depth = 0.00035
    count = len(upper)
    verts = (
        [(x, y, z) for x, z in upper]
        + [(x, y, z) for x, z in lower]
        + [(x, y + depth, z) for x, z in upper]
        + [(x, y + depth, z) for x, z in lower]
    )
    uf, lf, ub, lb = 0, count, count * 2, count * 3
    faces = []
    for i in range(count - 1):
        # face frontal / traseira e as duas bordas longas
        faces.append((uf + i, uf + i + 1, lf + i + 1, lf + i))
        faces.append((ub + i + 1, ub + i, lb + i, lb + i + 1))
        faces.append((uf + i + 1, uf + i, ub + i, ub + i + 1))
        faces.append((lf + i, lf + i + 1, lb + i + 1, lb + i))
    # tampas nos dois cantos
    faces.append((uf, lf, lb, ub))
    faces.append((uf + count - 1, ub + count - 1, lb + count - 1, lf + count - 1))
    mesh = bpy.data.meshes.new(clean_name(name))
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(clean_name(name), mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj["face_feature"] = label
    obj.data.materials.append(mat)
    return obj


def add_eyes(materials):
    """Esclera, íris em três níveis e brilho: olhos separados, não pintados."""
    features = []
    for side, sign in (("L", 1.0), ("R", -1.0)):
        x = sign * FACE["eye_x"]
        y = FACE["eye_y"]
        z = FACE["eye_z"]
        # Globo ocular encaixado na órbita previamente escavada no corpo.
        # A abertura amendoada senta rente à órbita. O globo é sugerido pela
        # íris em camadas, sem uma esfera que vire uma lente no perfil.
        features.append(add_almond_eye(
            f"OlhoEsclera_{side}", (x, y - 0.0107, z), 0.0215, 0.0145,
            materials["sclera"], "esclera"
        ))
        # Camadas convexas ligeiramente à frente: anel limbal, íris castanha e
        # pupila preta. O relevo dá leitura a 2–3 m mesmo sem depender de uma
        # textura pintada em baixa resolução.
        features.append(add_disc(
            f"IrisAnel_{side}", (x, y - 0.01145, z), 0.0100, 0.00065,
            materials["iris_outer"], "anel_iris"
        ))
        features.append(add_disc(
            f"Iris_{side}", (x, y - 0.01200, z), 0.0083, 0.00055,
            materials["iris_inner"], "iris"
        ))
        features.append(add_disc(
            f"Pupila_{side}", (x, y - 0.01250, z), 0.0046, 0.00050,
            materials["pupil"], "pupila"
        ))
        # Reflexo deslocado de propósito (não fica no centro, onde pareceria
        # um olho pintado). Espelhado para os dois olhos para preservar unidade.
        features.append(add_uv_ellipsoid(
            f"BrilhoOlho_{side}", (x - sign * 0.0028, y - 0.01310, z + 0.0032),
            (0.00175, 0.00035, 0.00175), materials["highlight"], 12, 8, "brilho_cornea"
        ))
    return features


def add_eyelids_brows_lashes(materials):
    features = []
    for side, sign in (("L", 1.0), ("R", -1.0)):
        x0 = sign * FACE["eye_x"]
        y = FACE["eye_y"] - 0.0100
        z0 = FACE["eye_z"]
        # A ordem espelhada por sinal mantém o arco sempre anatômico: canto
        # interno um pouco mais baixo, canto externo levemente elevado.
        upper = [
            (x0 - sign * 0.025, y, z0 + 0.000),
            (x0 - sign * 0.013, y - 0.0015, z0 + 0.015),
            (x0 + sign * 0.004, y - 0.0022, z0 + 0.020),
            (x0 + sign * 0.020, y - 0.0012, z0 + 0.012),
            (x0 + sign * 0.026, y, z0 + 0.004),
        ]
        lower = [
            (x0 - sign * 0.024, y + 0.0015, z0 - 0.001),
            (x0 - sign * 0.009, y - 0.0004, z0 - 0.012),
            (x0 + sign * 0.011, y - 0.0004, z0 - 0.012),
            (x0 + sign * 0.025, y + 0.0015, z0 + 0.001),
        ]
        features.append(add_curve_tube(
            f"PalpebraSuperior_{side}", upper, 0.00032, materials["skin_detail"], label="palpebra_superior"
        ))
        features.append(add_curve_tube(
            f"PalpebraInferior_{side}", lower, 0.00020, materials["skin_shadow"], label="palpebra_inferior"
        ))

        # Sobrancelha de volume levemente irregular -- ainda pertence ao rosto,
        # não cria cabelo de couro cabeludo e não antecipa a parte 3B.
        brow = [
            (x0 - sign * 0.025, y + 0.004, FACE["brow_z"] - 0.002),
            (x0 - sign * 0.012, y - 0.002, FACE["brow_z"] + 0.004),
            (x0 + sign * 0.004, y - 0.003, FACE["brow_z"] + 0.006),
            (x0 + sign * 0.019, y - 0.001, FACE["brow_z"] + 0.003),
            (x0 + sign * 0.026, y + 0.002, FACE["brow_z"] - 0.004),
        ]
        features.append(add_curve_tube(
            f"Sobrancelha_{side}", brow, 0.00185, materials["brow"], label="sobrancelha"
        ))

        # Três cílios discretos na borda externa. Curvas sólidas e finas têm
        # mais estabilidade em motion/LOD do que cards alpha nesta etapa.
        outer = upper[-2:]
        for i, base in enumerate(outer):
            direction = sign * (0.003 + i * 0.002)
            tip = (base[0] + direction, base[1] + 0.0005, base[2] + 0.0035 + i * 0.0015)
            features.append(add_curve_tube(
                f"Cilio_{side}_{i + 1:02d}", [base, tip], 0.00016, materials["lash"],
                label="cilio"
            ))
    return features


def add_nose_and_mouth(materials):
    features = []
    # Ponte/asa/ponta reforçam a forma que a escultura gaussiana de Fase 1 já
    # abriu. As três peças se sobrepõem ao crânio, sem um nariz de primitiva
    # desconectado ou uma sombra pintada.
    features.append(add_uv_ellipsoid(
        "PonteNariz", (0.0, -0.0960, FACE["nose_z"] + 0.018),
        (0.0065, 0.0008, 0.0210), materials["skin_detail"], 20, 12, "ponte_nariz"
    ))
    features.append(add_uv_ellipsoid(
        "PontaNariz", (0.0, -0.1060, FACE["nose_z"] - 0.002),
        (0.0085, 0.0022, 0.0055), materials["skin_detail"], 24, 12, "ponta_nariz"
    ))
    for side, sign in (("L", 1.0), ("R", -1.0)):
        features.append(add_uv_ellipsoid(
            f"AsaNariz_{side}", (sign * 0.0085, -0.1040, FACE["nose_z"] - 0.004),
            (0.0038, 0.0008, 0.0032), materials["skin_detail"], 18, 10, "asa_nariz"
        ))
        features.append(add_uv_ellipsoid(
            f"Narina_{side}", (sign * 0.0076, -0.1085, FACE["nose_z"] - 0.0065),
            (0.0022, 0.00040, 0.0012), materials["mouth"], 14, 8, "narina"
        ))

    # Boca relaxada, com arco de cupido e cavidade em três níveis. A leitura
    # é de sorriso neutro em close e continua sutil na câmera de corrida.
    z = FACE["mouth_z"]
    # Na nova cabeça a superfície da boca está em y≈-0,093. Faixas planas e
    # duplas a 1–2 mm dela dão volume de lábio sem o aspecto de arame de
    # curvas tubulares.
    upper_top = [
        (-0.022, z + 0.000), (-0.013, z + 0.0032), (-0.005, z + 0.0042),
        (0.000, z + 0.0018), (0.005, z + 0.0042), (0.013, z + 0.0032), (0.022, z + 0.000),
    ]
    upper_bottom = [
        (-0.022, z - 0.0010), (-0.013, z - 0.0002), (-0.005, z + 0.0006),
        (0.000, z - 0.0012), (0.005, z + 0.0006), (0.013, z - 0.0002), (0.022, z - 0.0010),
    ]
    lower_top = [
        (-0.019, z - 0.0033), (-0.010, z - 0.0044), (0.000, z - 0.0046),
        (0.010, z - 0.0044), (0.019, z - 0.0033),
    ]
    lower_bottom = [
        (-0.017, z - 0.0070), (-0.008, z - 0.0090), (0.000, z - 0.0095),
        (0.008, z - 0.0090), (0.017, z - 0.0070),
    ]
    mouth_line = [
        (-0.022, -0.0928, z - 0.0014), (-0.010, -0.0932, z - 0.0018),
        (0.000, -0.0934, z - 0.0020), (0.010, -0.0932, z - 0.0018), (0.022, -0.0928, z - 0.0014),
    ]
    features.append(add_lip_ribbon("LabioSuperior", upper_top, upper_bottom, -0.0923, materials["lip"], "labio_superior"))
    features.append(add_curve_tube("LinhaBoca", mouth_line, 0.00032, materials["mouth"], label="cavidade_boca"))
    features.append(add_lip_ribbon("LabioInferior", lower_top, lower_bottom, -0.0926, materials["lip"], "labio_inferior"))
    return features


def rebuild_head(body, skin_mat):
    """Troca o volume provisório da cabeça pelo crânio facial desta fase.

    A Fase 1 concentrava corpo e crânio em uma única malha Skin; isso era útil
    para validar altura/volume, mas não oferece uma face estável para detalhes:
    a testa e a boca ficavam em profundidades incompatíveis. Aqui removemos só
    as faces acima da transição do pescoço e encaixamos uma cabeça oval
    independente, toda manifold. Na Fase 4 ela receberá os pesos do osso Head
    junto dos olhos e demais detalhes.
    """
    cutoff = 1.438
    bm = bmesh.new()
    bm.from_mesh(body.data)
    remove = [face for face in bm.faces if face.calc_center_median().z > cutoff]
    bmesh.ops.delete(bm, geom=remove, context="FACES_ONLY")
    loose = [vertex for vertex in bm.verts if not vertex.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context="VERTS")
    bm.to_mesh(body.data)
    bm.free()
    body.data.update()

    # Crânio, face e mandíbula em uma esfera UV de resolução suficiente para
    # o close. A mandíbula é afinada e a nuca preserva volume, para não ler
    # como um balão nem como a cápsula do placeholder anterior.
    center = Vector((0.0, 0.000, 1.585))
    head = add_uv_ellipsoid(
        "CabecaRostoBase", center, (0.132, 0.108, 0.151), skin_mat,
        segments=48, rings=32, label="cabeca_rosto_base"
    )
    for vertex in head.data.vertices:
        local = vertex.co - center
        # A esfera se afunila até o queixo e discretamente no topo; as maçãs
        # ficam no terço médio. A face é um pouco mais plana que a nuca.
        if local.z < -0.045:
            factor = 0.76 + 0.15 * max(0.0, (local.z + 0.151) / 0.106)
            vertex.co.x = center.x + local.x * factor
        elif local.z > 0.095:
            vertex.co.x = center.x + local.x * 0.90
        if local.y < 0.0:
            vertex.co.y = center.y + local.y * 0.94
        # Projeção moderada do queixo, não uma esfera inteira abaixo da boca.
        if -0.105 < local.z < -0.062 and local.y < -0.045:
            vertex.co.y -= 0.004 * (1.0 - abs(local.z + 0.083) / 0.022)
    smooth(head)

    # Orelhas integradas à cabeça; o volume é baixo para receber depois o
    # cabelo sem interpenetração visual.
    ears = []
    for side, sign in (("L", 1.0), ("R", -1.0)):
        ears.append(add_uv_ellipsoid(
            f"Orelha_{side}", (sign * 0.126, 0.002, 1.585),
            (0.017, 0.011, 0.029), skin_mat, 20, 12, "orelha"
        ))
    return head, ears


def import_body(source: Path):
    if not source.exists():
        raise SystemExit(
            f"entrada ausente: {source}\n"
            "Gere as fases anteriores primeiro:\n"
            "  sh tools/blender/run_bpy.sh tools/blender/build_heroi_julia.py\n"
            "  sh tools/blender/run_bpy.sh tools/blender/bake_heroi_julia.py"
        )
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise SystemExit(f"GLB sem malha: {source}")
    body = max(meshes, key=lambda obj: len(obj.data.polygons))
    body.name = "JuliaCorpoFase2"
    body["face_feature"] = "corpo_base_fase2"
    return body


def nonmanifold_edges(obj) -> int:
    """Conta arestas abertas/não-manifold de uma malha estática."""
    if obj.type != "MESH":
        return 0
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    count = sum(1 for edge in bm.edges if len(edge.link_faces) != 2)
    bm.free()
    return count


def mesh_triangles(obj) -> int:
    if obj.type == "MESH":
        return sum(len(poly.vertices) - 2 for poly in obj.data.polygons)
    # Curvas ainda não têm polígonos até a avaliação; para a métrica/export,
    # convertemos uma cópia avaliada em mesh, sem tocar o objeto real.
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = bpy.data.meshes.new_from_object(evaluated, depsgraph=depsgraph)
    result = sum(len(poly.vertices) - 2 for poly in mesh.polygons)
    bpy.data.meshes.remove(mesh)
    return result


def all_exportable():
    return [obj for obj in bpy.context.scene.objects if obj.type in {"MESH", "CURVE"}]


def export_scene(output: Path, blend_output: Path):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in all_exportable():
        obj.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=str(output),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_draco_mesh_compression_enable=False,
    )
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_output))


def parse_args():
    args = [arg for arg in sys.argv[1:] if not arg.endswith(".py")]
    if "--" in args:
        args = args[args.index("--") + 1:]
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=OUT_DIR / "heroi_julia_pbr.glb")
    parser.add_argument("--output", type=Path, default=OUT_DIR / "heroi_julia_rosto.glb")
    parser.add_argument("--blend", type=Path, default=OUT_DIR / "heroi_julia_rosto.blend")
    return parser.parse_args(args)


def main():
    args = parse_args()
    log("Fase 3A — rosto: iniciando sem cabelo")
    body = import_body(args.input.resolve())
    materials = face_materials()
    head, ears = rebuild_head(body, materials["skin_detail"])
    features = []
    features += ears
    features += add_eyes(materials)
    features += add_eyelids_brows_lashes(materials)
    features += add_nose_and_mouth(materials)

    # Só elementos faciais são permitidos nesta entrega. A checagem protege a
    # separação prometida: nenhum objeto OU material pode introduzir cabelo.
    banned_words = ("hair", "cabelo", "ponytail", "mecha")
    forbidden_objects = [obj.name for obj in all_exportable() if any(word in obj.name.lower() for word in banned_words)]
    forbidden_materials = [mat.name for mat in bpy.data.materials if any(word in mat.name.lower() for word in banned_words)]
    forbidden = forbidden_objects + forbidden_materials
    named = {str(obj.get("face_feature", "")) for obj in features}
    required = {
        "esclera", "anel_iris", "iris", "pupila", "brilho_cornea",
        "palpebra_superior", "palpebra_inferior", "sobrancelha", "cilio",
        "ponte_nariz", "ponta_nariz", "asa_nariz", "narina",
        "labio_superior", "cavidade_boca", "labio_inferior",
    }
    missing = sorted(required - named)
    if forbidden or missing:
        raise SystemExit(f"gate de escopo falhou; cabelo={forbidden}, recursos faltando={missing}")

    triangles = sum(mesh_triangles(obj) for obj in all_exportable())
    face_triangles = sum(mesh_triangles(obj) for obj in features)
    export_scene(args.output.resolve(), args.blend.resolve())

    metrics = {
        "fase": "3A_rosto_sem_cabelo",
        "input": str(args.input),
        "output": str(args.output),
        "cabeca": head.name,
        "arestas_nao_manifold_cabeca": nonmanifold_edges(head),
        "meshes_rosto": len(features),
        "triangulos_rosto": face_triangles,
        "triangulos_total": triangles,
        "materiais_rosto": sorted({slot.material.name for obj in features for slot in obj.material_slots if slot.material}),
        "features": sorted(named),
        "sem_cabelo": not forbidden,
        "gate_cabeca": head.name == "CabecaRostoBase",
        "gate_cabeca_manifold": nonmanifold_edges(head) == 0,
        "gate_features": not missing,
        "gate_sem_cabelo": not forbidden,
        "gate_glb": args.output.exists() and args.output.stat().st_size > 0,
        "glb_kb": round(args.output.stat().st_size / 1024, 1),
    }
    metrics["gate"] = all(metrics[k] for k in ("gate_cabeca", "gate_cabeca_manifold", "gate_features", "gate_sem_cabelo", "gate_glb"))
    metrics_path = OUT_DIR / "heroi_julia_rosto_metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + "\n")
    log(json.dumps(metrics, indent=2, ensure_ascii=False))
    log(f"GLB: {args.output}")
    log(f"BLEND: {args.blend}")
    return 0 if metrics["gate"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
