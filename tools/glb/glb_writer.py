#!/usr/bin/env python3
"""Escritor de GLB binario (glTF 2.0) em Python puro, sem dependencias.

Substitui o bpy neste sandbox (sem libXrender/apt) mantendo a filosofia do
projeto: assets originais modelados por script (ver assets/props/LEIA-ME.md).
Contrato com o jogo:
  - eixos ja no espaco do Godot: Y para cima, frente para -Z, metros;
  - origem no chao (y = 0), escala real 1:1;
  - winding CCW visto de fora (frente da malha).

Uso tipico:
    w = GlbWriter()
    w.box(0, 1, 0, 2, 0.1, 0.1, "pintura", (0.94, 0.47, 0.09), rough=0.55)
    w.write("assets/props/exemplo.glb", root_name="exemplo")
"""
import json
import math
import struct


class GlbWriter:
    def __init__(self):
        # material_key -> lista de triangulos [(pos, normal) x3]
        self._parts = {}
        self._mat_props = {}

    # ------------------------------------------------------------ materiais
    def _mat_key(self, nome, cor, rough, metal):
        key = "%s|%s" % (nome, tuple(round(c, 4) for c in cor))
        if key not in self._mat_props:
            self._mat_props[key] = {
                "name": nome,
                "pbrMetallicRoughness": {
                    "baseColorFactor": [float(cor[0]), float(cor[1]), float(cor[2]), 1.0],
                    "metallicFactor": float(metal),
                    "roughnessFactor": float(rough),
                },
            }
        return key

    def _tri(self, key, a, b, c):
        u = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        v = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
        n = (
            u[1] * v[2] - u[2] * v[1],
            u[2] * v[0] - u[0] * v[2],
            u[0] * v[1] - u[1] * v[0],
        )
        tam = math.sqrt(n[0] ** 2 + n[1] ** 2 + n[2] ** 2) or 1.0
        n = (n[0] / tam, n[1] / tam, n[2] / tam)
        self._parts.setdefault(key, []).append((a, n, b, n, c, n))

    def _quad(self, key, p0, p1, p2, p3):
        # dois triangulos CCW vistos do lado p0->p1->p2
        self._tri(key, p0, p1, p2)
        self._tri(key, p0, p2, p3)

    # ------------------------------------------------------------ geometria
    def box(self, cx, cy, cz, sx, sy, sz, nome, cor, rough=0.62, metal=0.0):
        """Caixa alinhada aos eixos, centro (cx, cy, cz), tamanhos (sx, sy, sz)."""
        k = self._mat_key(nome, cor, rough, metal)
        x0, x1 = cx - sx / 2, cx + sx / 2
        y0, y1 = cy - sy / 2, cy + sy / 2
        z0, z1 = cz - sz / 2, cz + sz / 2
        v = [
            (x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),  # frente (-z)
            (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1),  # tras (+z)
        ]
        # frente (-z): normal -z, CCW visto de -z
        self._quad(k, v[1], v[0], v[3], v[2])
        # tras (+z)
        self._quad(k, v[4], v[5], v[6], v[7])
        # esquerda (-x)
        self._quad(k, v[0], v[4], v[7], v[3])
        # direita (+x)
        self._quad(k, v[5], v[1], v[2], v[6])
        # topo (+y)
        self._quad(k, v[3], v[7], v[6], v[2])
        # fundo (-y)
        self._quad(k, v[0], v[1], v[5], v[4])

    def cylinder(self, cx, cy, cz, r_baixo, r_cima, altura, nome, cor,
                 rough=0.5, metal=0.3, seg=12):
        """Cilindro/cone ao longo de Y, centro em (cx, cy, cz)."""
        k = self._mat_key(nome, cor, rough, metal)
        y0, y1 = cy - altura / 2, cy + altura / 2
        for i in range(seg):
            a0 = i / seg * 2 * math.pi
            a1 = (i + 1) / seg * 2 * math.pi
            b0 = (cx + r_baixo * math.cos(a0), y0, cz + r_baixo * math.sin(a0))
            b1 = (cx + r_baixo * math.cos(a1), y0, cz + r_baixo * math.sin(a1))
            t1 = (cx + r_cima * math.cos(a1), y1, cz + r_cima * math.sin(a1))
            t0 = (cx + r_cima * math.cos(a0), y1, cz + r_cima * math.sin(a0))
            self._quad(k, b0, b1, t1, t0)
            # tampas (leque)
            self._tri(k, (cx, y0, cz), b1, b0)
            self._tri(k, (cx, y1, cz), t0, t1)

    def esfera_cachos(self, cx, cy, cz, raio, nome, cor, rough=0.85, metal=0.0,
                      achatada=0.66, subdiv=1):
        """Icosfera achatada (copa de arvore): leque de triangulos CCW."""
        k = self._mat_key(nome, cor, rough, metal)
        t = (1.0 + math.sqrt(5.0)) / 2.0
        verts = [
            (-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0),
            (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t),
            (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1),
        ]
        norm = math.sqrt(1 + t * t)
        verts = [(x / norm, y / norm, z / norm) for (x, y, z) in verts]
        faces = [
            (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
            (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
            (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
            (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1),
        ]
        for _ in range(subdiv):
            cache, novo = {}, []
            def meio(a, b):
                chave = (min(a, b), max(a, b))
                if chave in cache:
                    return cache[chave]
                va, vb = verts[a], verts[b]
                m = ((va[0] + vb[0]) / 2, (va[1] + vb[1]) / 2, (va[2] + vb[2]) / 2)
                tam = math.sqrt(m[0] ** 2 + m[1] ** 2 + m[2] ** 2) or 1.0
                verts.append((m[0] / tam, m[1] / tam, m[2] / tam))
                cache[chave] = len(verts) - 1
                return cache[chave]
            for (a, b, c) in faces:
                ab, bc, ca = meio(a, b), meio(b, c), meio(c, a)
                novo += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
            faces = novo
        for (a, b, c) in faces:
            pa = (cx + verts[a][0] * raio, cy + verts[a][1] * raio * achatada,
                  cz + verts[a][2] * raio)
            pb = (cx + verts[b][0] * raio, cy + verts[b][1] * raio * achatada,
                  cz + verts[b][2] * raio)
            pc = (cx + verts[c][0] * raio, cy + verts[c][1] * raio * achatada,
                  cz + verts[c][2] * raio)
            self._tri(k, pa, pb, pc)

    # ---------------------------------------------------------------- saida
    def write(self, caminho, root_name="asset"):
        materiais, meshes = [], []
        for chave, tris in self._parts.items():
            indice_material = materiais.index(self._mat_props[chave]) \
                if self._mat_props[chave] in materiais else len(materiais)
            if indice_material == len(materiais):
                materiais.append(self._mat_props[chave])
            posicoes, normais = [], []
            for (a, na, b, nb, c, nc) in tris:
                posicoes += [a, b, c]
                normais += [na, nb, nc]
            meshes.append((indice_material, posicoes, normais))

        buffer = bytearray()
        buffer_views, accessors, primitivas = [], [], []
        def alinha4(n):
            return (4 - (n % 4)) % 4

        for (indice_material, posicoes, normais) in meshes:
            view_pos = len(buffer_views)
            dados = struct.pack("<%df" % (len(posicoes) * 3),
                                *[v for p in posicoes for v in p])
            buffer_views.append({"buffer": 0, "byteOffset": len(buffer),
                                 "byteLength": len(dados), "target": 34962})
            buffer += dados
            buffer += b"\0" * alinha4(len(dados))
            mins = [min(p[i] for p in posicoes) for i in range(3)]
            maxs = [max(p[i] for p in posicoes) for i in range(3)]
            acc_pos = len(accessors)
            accessors.append({"bufferView": view_pos, "componentType": 5126,
                              "count": len(posicoes), "type": "VEC3",
                              "min": mins, "max": maxs})
            view_nor = len(buffer_views)
            dados = struct.pack("<%df" % (len(normais) * 3),
                                *[v for n in normais for v in n])
            buffer_views.append({"buffer": 0, "byteOffset": len(buffer),
                                 "byteLength": len(dados), "target": 34962})
            buffer += dados
            buffer += b"\0" * alinha4(len(dados))
            acc_nor = len(accessors)
            accessors.append({"bufferView": view_nor, "componentType": 5126,
                              "count": len(normais), "type": "VEC3"})
            primitivas.append({"attributes": {"POSITION": acc_pos, "NORMAL": acc_nor},
                               "material": indice_material, "mode": 4})

        doc = {
            "asset": {"version": "2.0",
                      "generator": "busao tools/glb/glb_writer.py (sem bpy)"},
            "scene": 0,
            "scenes": [{"name": root_name, "nodes": [0]}],
            "nodes": [{"name": root_name, "mesh": 0}],
            "meshes": [{"name": root_name, "primitives": primitivas}],
            "materials": materiais,
            "accessors": accessors,
            "bufferViews": buffer_views,
            "buffers": [{"byteLength": len(buffer)}],
        }
        json_bytes = json.dumps(doc, separators=(",", ":")).encode("utf-8")
        json_bytes += b" " * alinha4(len(json_bytes))
        buffer += b"\0" * alinha4(len(buffer))
        total = 12 + 8 + len(json_bytes) + 8 + len(buffer)
        with open(caminho, "wb") as f:
            f.write(struct.pack("<III", 0x46546C67, 2, total))
            f.write(struct.pack("<II", len(json_bytes), 0x4E4F534A))
            f.write(json_bytes)
            f.write(struct.pack("<II", len(buffer), 0x004E4942))
            f.write(bytes(buffer))
        return caminho


def ler_glb(caminho):
    """Reler um GLB e devolver (doc, tamanho_binario) — sanity check."""
    with open(caminho, "rb") as f:
        dados = f.read()
    magic, versao, total = struct.unpack_from("<III", dados, 0)
    assert magic == 0x46546C67 and versao == 2, "cabecalho GLB invalido"
    assert total == len(dados), "tamanho do GLB nao confere"
    tam_json, tipo_json = struct.unpack_from("<II", dados, 12)
    assert tipo_json == 0x4E4F534A, "chunk JSON ausente"
    doc = json.loads(dados[20:20 + tam_json].decode("utf-8").rstrip())
    tam_bin = 0
    if 20 + tam_json + 8 <= len(dados):
        tam_bin, tipo_bin = struct.unpack_from("<II", dados, 20 + tam_json)
        assert tipo_bin == 0x004E4942, "chunk BIN ausente"
    return doc, tam_bin
