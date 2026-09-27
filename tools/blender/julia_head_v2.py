"""Cabeça, rosto, cabelo e paleta corrigidos da Júlia.

Este módulo substitui a tentativa anterior baseada em cards planos. A cabeça é
uma malha ovoide própria, com mandíbula; olhos têm escala humana e ficam dentro
da face; nariz, orelhas, pálpebras e lábios são geometria; o cabelo cacheado é
formado por mechas tubulares com volume e rabo de cavalo.
"""
import math

import bpy
import bmesh
from mathutils import Vector

D = bpy.data
TAU = math.tau


def _mat(name, color, roughness=0.55, metallic=0.0):
    mat = D.materials.get(name) or D.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if name == "PeleJuliaV2" and "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = 0.08
    mat.diffuse_color = (*color, 1.0)
    return mat


def _uv_sphere(name, location, scale, material, segments=48, rings=24):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments, ring_count=rings, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def _curve_tube(name, points, radius, material, cyclic=False, resolution=1):
    curve = D.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = resolution
    curve.bevel_depth = radius
    curve.bevel_resolution = 2
    curve.resolution_u = 2
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for point, co in zip(spline.bezier_points, points):
        point.co = co
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    spline.use_cyclic_u = cyclic
    obj = D.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    for poly in obj.data.polygons:
        poly.use_smooth = True
    obj.select_set(False)
    return obj


def _lip_patch(name, upper, material):
    """Lábio orgânico convexo, com arco do cupido e pontas afiladas."""
    cols, rows = 30, 5
    verts, faces = [], []
    for row in range(rows):
        t = row / (rows - 1)
        for col in range(cols + 1):
            u = -1.0 + 2.0 * col / cols
            taper = max(0.0, 1.0 - abs(u) ** 2.4)
            x = 0.026 * u
            if upper:
                cupids = math.exp(-((abs(u) - 0.36) / 0.22) ** 2)
                z0 = 1.5238
                z1 = 1.5260 + 0.0043 * cupids * taper
                z = z0 * (1.0 - t) + z1 * t
                y = -0.0960 - 0.0032 * math.sin(math.pi * t) * taper
            else:
                z0 = 1.5228
                z1 = 1.5158 - 0.0010 * (1.0 - taper)
                z = z0 * (1.0 - t) + z1 * t
                y = -0.0962 - 0.0040 * math.sin(math.pi * t) * taper
            verts.append((x, y, z))
    for row in range(rows - 1):
        for col in range(cols):
            a = row * (cols + 1) + col
            faces.append((a, a + 1, a + cols + 2, a + cols + 1))
    mesh = D.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(material)
    obj = D.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    for poly in mesh.polygons:
        poly.use_smooth = True
    return obj


def _head_shell(skin):
    head = _uv_sphere("CabecaJuliaV2", (0.0, 0.002, 1.606),
                      (0.087, 0.091, 0.119), skin, 64, 32)
    # Ovoide humano: têmpora/maçã mais largas, mandíbula e queixo afunilados.
    for vert in head.data.vertices:
        z = vert.co.z
        if z < 1.570:
            t = max(0.0, min(1.0, (1.570 - z) / 0.083))
            vert.co.x *= 1.0 - 0.27 * t
            # queixo avança discretamente; nuca não é achatada.
            if vert.co.y < 0.0:
                vert.co.y -= 0.006 * t
        elif z > 1.665:
            t = min(1.0, (z - 1.665) / 0.060)
            vert.co.x *= 1.0 - 0.10 * t
        # Face frontal menos esférica e com maçãs do rosto suaves.
        if vert.co.y < -0.040:
            cheek = math.exp(-((z - 1.570) / 0.031) ** 2)
            vert.co.y -= 0.0045 * cheek * min(1.0, abs(vert.co.x) / 0.040)
            forehead = math.exp(-((z - 1.640) / 0.050) ** 2)
            vert.co.y += 0.002 * forehead
    head.data.update()
    return head


def _nose(skin, nostril):
    """Nariz em volumes suaves (sem a pirâmide facetada da V1)."""
    parts = []
    bridge = _uv_sphere("PonteNarizJuliaV2", (0.0, -0.092, 1.579),
                        (0.0090, 0.0075, 0.031), skin, 32, 18)
    bridge.rotation_euler.x = math.radians(-5)
    parts.append(bridge)
    parts.append(_uv_sphere("PontaNarizJuliaV2", (0.0, -0.105, 1.554),
                            (0.0125, 0.0130, 0.0095), skin, 32, 18))
    for side in (-1, 1):
        parts.append(_uv_sphere(f"AsaNariz_{side}",
                                (side * 0.0105, -0.104, 1.5505),
                                (0.0068, 0.008, 0.0052), skin, 24, 12))
        parts.append(_uv_sphere(f"Narina_{side}",
                                (side * 0.0080, -0.1120, 1.5488),
                                (0.0022, 0.0008, 0.0013), nostril, 16, 8))
    return parts


def _ears(skin, inner):
    extras = []
    for side in (-1, 1):
        ear = _uv_sphere(f"Orelha_{side}", (side * 0.086, 0.003, 1.586),
                         (0.0095, 0.0075, 0.026), skin, 32, 18)
        ear.rotation_euler.y = side * math.radians(7)
        extras.append(ear)
        # Hélice e concha dão leitura lateral, em vez de uma bolha sem detalhe.
        pts = []
        for i in range(15):
            a = math.pi * (0.70 + 1.60 * i / 14)
            pts.append((side * (0.086 + 0.0032 * math.cos(a)),
                        -0.0048, 1.586 + 0.018 * math.sin(a)))
        extras.append(_curve_tube(f"HeliceOrelha_{side}", pts, 0.0015, inner))
        extras.append(_uv_sphere(f"ConchaOrelha_{side}",
                                 (side * 0.0865, -0.0052, 1.584),
                                 (0.0026, 0.0009, 0.006), inner, 16, 8))
    return extras


def _eyes(skin, sclera, iris, pupil, dark):
    extras = []
    for side in (-1, 1):
        cx = side * 0.0305
        eye = _uv_sphere(f"Esclera_{side}", (cx, -0.0870, 1.588),
                         (0.0175, 0.0060, 0.0092), sclera, 36, 18)
        extras.append(eye)
        extras.append(_uv_sphere(f"Iris_{side}", (cx, -0.0930, 1.588),
                                 (0.0056, 0.0008, 0.0058), iris, 28, 14))
        extras.append(_uv_sphere(f"Pupila_{side}", (cx, -0.0938, 1.588),
                                 (0.0022, 0.00045, 0.0023), pupil, 20, 10))
        extras.append(_uv_sphere(f"Brilho_{side}",
                                 (cx - side * 0.0017, -0.0943, 1.5905),
                                 (0.0010, 0.0003, 0.0010), sclera, 12, 6))
        # Pálpebras curvas acompanham o globo e fecham os cantos do olho.
        top = [(side * x, -0.0942, z) for x, z in
               ((0.048, 1.588), (0.041, 1.593), (0.0305, 1.596),
                (0.020, 1.593), (0.013, 1.588))]
        bottom = [(side * x, -0.0938, z) for x, z in
                  ((0.048, 1.587), (0.041, 1.582), (0.0305, 1.580),
                   (0.020, 1.582), (0.013, 1.587))]
        extras.append(_curve_tube(f"PalpebraSuperior_{side}", top, 0.0018, skin))
        extras.append(_curve_tube(f"PalpebraInferior_{side}", bottom, 0.00125, skin))
        brow = [(side * x, -0.0950, z) for x, z in
                ((0.052, 1.610), (0.043, 1.616), (0.031, 1.619),
                 (0.021, 1.616), (0.014, 1.613))]
        extras.append(_curve_tube(f"Sobrancelha_{side}", brow, 0.0025, dark))
        lash = [(side * x, -0.0950, z) for x, z in
                ((0.047, 1.589), (0.040, 1.594), (0.0305, 1.596),
                 (0.021, 1.594), (0.014, 1.589))]
        extras.append(_curve_tube(f"LinhaCilios_{side}", lash, 0.00065, dark))
        # Cílios curtos inclinados para fora, sem o aspecto de grade do V1.
        for i, (x, z) in enumerate(((0.043, 1.593), (0.035, 1.596),
                                    (0.027, 1.596), (0.020, 1.593))):
            xx = side * x
            extras.append(_curve_tube(f"Cilio_{side}_{i}",
                                      [(xx, -0.0952, z),
                                       (xx + side * 0.0010, -0.0972, z + 0.0025)],
                                      0.00025, dark))
    return extras


def _hair(hair, hair_hi):
    extras = []
    # Volume-base segue o crânio, recuado para não invadir testa/rosto.
    cap = _uv_sphere("CabeloBaseV2", (0.0, 0.028, 1.650),
                     (0.090, 0.084, 0.104), hair, 48, 24)
    extras.append(cap)

    # Cachos da linha frontal: mechas finas e irregulares, nunca placas planas.
    front_x = (-0.064, -0.042, -0.018, 0.010, 0.036, 0.061)
    for i, x0 in enumerate(front_x):
        length = 0.030 + 0.008 * (i % 3)
        pts = []
        for j in range(8):
            t = j / 7
            pts.append((x0 + 0.0055 * math.sin(t * TAU * 1.5 + i),
                        -0.082 - 0.003 * math.sin(t * math.pi),
                        1.704 - length * t))
        extras.append(_curve_tube(f"CachoFrontal_{i}", pts, 0.0025, hair_hi))

    # Laterais contornam o rosto, preservando orelhas e olhos visíveis.
    for side in (-1, 1):
        for i in range(6):
            y0 = -0.045 + i * 0.018
            pts = []
            for j in range(9):
                t = j / 8
                pts.append((side * (0.091 + 0.006 * math.sin(t * TAU * 1.6 + i)),
                            y0 + 0.005 * math.cos(t * TAU),
                            1.688 - (0.105 + 0.012 * (i % 2)) * t))
            extras.append(_curve_tube(f"CachoLateral_{side}_{i}", pts,
                                      0.0042, hair if i % 2 else hair_hi))

    # Elástico e rabo de cavalo volumoso, cacheado, alto como na arte-alvo.
    extras.append(_curve_tube("ElasticoCabelo", [
        (0.040 * math.cos(a), 0.105, 1.650 + 0.040 * math.sin(a))
        for a in [i * TAU / 20 for i in range(20)]], 0.0030, dark_mat(), cyclic=True))
    for i in range(14):
        angle = i / 14 * TAU
        x0 = 0.042 * math.cos(angle)
        z0 = 1.650 + 0.035 * math.sin(angle)
        pts = []
        for j in range(13):
            t = j / 12
            wave = t * TAU * (1.7 + 0.12 * (i % 3)) + angle
            pts.append((x0 + (0.014 + 0.020 * t) * math.sin(wave),
                        0.105 + 0.105 * t + 0.018 * math.cos(wave),
                        z0 - 0.270 * t + 0.018 * math.sin(wave * 1.08)))
        extras.append(_curve_tube(f"RaboCacho_{i}", pts,
                                  0.0048 - 0.0012 * (i % 2),
                                  hair if i % 3 else hair_hi))
    return extras


def dark_mat():
    return _mat("ElasticoJulia", (0.018, 0.024, 0.019), 0.72)


def _color_body(corpo, skin, shirt, pants, shoes):
    corpo.data.materials.clear()
    for material in (skin, shirt, pants, shoes):
        corpo.data.materials.append(material)
    for poly in corpo.data.polygons:
        c = poly.center
        ax, z = abs(c.x), c.z
        index = 0
        if z < 0.105 and ax < 0.16:
            index = 3
        elif 0.095 <= z < 1.005 and ax < 0.17:
            index = 2
        elif (0.985 <= z < 1.425 and ax < 0.19) or (1.225 <= z < 1.420 and ax < 0.265):
            index = 1
        poly.material_index = index


def build_corrected_head(corpo):
    skin = _mat("PeleJuliaV2", (0.48, 0.245, 0.155), 0.48)
    shirt = _mat("CamisaJuliaAmarela", (0.94, 0.62, 0.025), 0.76)
    pants = _mat("LeggingJulia", (0.018, 0.025, 0.030), 0.80)
    shoes = _mat("TenisJulia", (0.94, 0.69, 0.05), 0.58)
    sclera = _mat("EscleraJuliaV2", (0.91, 0.90, 0.84), 0.28)
    iris = _mat("IrisJuliaCastanha", (0.18, 0.070, 0.025), 0.30)
    pupil = _mat("PupilaJuliaV2", (0.003, 0.002, 0.001), 0.36)
    dark = _mat("SobrancelhaCiliosJuliaV2", (0.030, 0.012, 0.006), 0.68)
    inner = _mat("OrelhaInternaJulia", (0.31, 0.115, 0.085), 0.62)
    nostril = _mat("NarinaJuliaV2", (0.035, 0.010, 0.008), 0.78)
    lips = _mat("LabiosJuliaV2", (0.44, 0.145, 0.135), 0.47)
    hair = _mat("CabeloJuliaV2", (0.035, 0.012, 0.006), 0.66)
    hair_hi = _mat("CabeloJuliaReflexo", (0.095, 0.035, 0.014), 0.60)

    _color_body(corpo, skin, shirt, pants, shoes)

    # O crânio antigo fazia parte do volume Skin do corpo. Encolhê-lo para
    # dentro preserva manifold/continuidade do pescoço sem disputar superfície
    # com a nova cabeça anatômica.
    for vert in corpo.data.vertices:
        if vert.co.z > 1.455:
            t = min(1.0, (vert.co.z - 1.455) / 0.085)
            vert.co.x *= 1.0 - 0.48 * t
            vert.co.y *= 1.0 - 0.55 * t
    corpo.data.update()

    extras = [_head_shell(skin)]
    extras.extend(_ears(skin, inner))
    extras.extend(_nose(skin, nostril))
    extras.extend(_eyes(skin, sclera, iris, pupil, dark))
    # Três volumes ovais formam a boca sem bordas retangulares: dois arcos no
    # lábio superior e um volume central no inferior.
    for side in (-1, 1):
        lip = _uv_sphere(f"LabioSuperiorJuliaV2_{side}",
                         (side * 0.010, -0.0965, 1.5218),
                         (0.0145, 0.0030, 0.0037), lips, 28, 12)
        lip.rotation_euler.y = side * math.radians(8)
        extras.append(lip)
    extras.append(_uv_sphere("LabioInferiorJuliaV2", (0.0, -0.0968, 1.5168),
                             (0.0235, 0.0035, 0.0046), lips, 32, 14))
    extras.append(_curve_tube("LinhaBocaJuliaV2",
                              [(-0.023, -0.1000, 1.5210), (-0.011, -0.1004, 1.5206),
                               (0.0, -0.1005, 1.5205), (0.011, -0.1004, 1.5206),
                               (0.023, -0.1000, 1.5210)], 0.00045, nostril))
    extras.extend(_hair(hair, hair_hi))
    return extras
