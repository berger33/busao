#!/usr/bin/env python3
"""Diagnóstico geométrico do GLB da heroína Júlia — mede o que está errado no rosto.

Convenção do build: Z para cima, frente = -Y, unidades em metros.
Cabeça humana adulta de referência (~0,22 m do queixo ao topo):
  - largura ~0,145-0,16 | profundidade ~0,19-0,21 (occipital -> glabela)
  - olhos na linha média do crânio (50% entre queixo e topo)
  - orelha ~0,06 de altura, saliência lateral 1,5-2,5 cm
"""
import json
import struct
import sys
from pathlib import Path
import numpy as np

GLB = Path(sys.argv[1] if len(sys.argv) > 1 else
           "assets/characters/source/heroi_julia/heroi_julia_fase3.glb")


def load_glb(path):
    raw = path.read_bytes()
    magic, ver, total = struct.unpack_from("<III", raw, 0)
    assert magic == 0x46546C67, "not glb"
    off, js, binblob = 12, None, b""
    while off < total:
        clen, ctype = struct.unpack_from("<II", raw, off)
        data = raw[off + 8: off + 8 + clen]
        if ctype == 0x4E4F534A:
            js = json.loads(data)
        elif ctype == 0x004E4942:
            binblob = data
        off += 8 + clen
    return js, binblob


def acc_data(js, blob, i):
    acc = js["accessors"][i]
    bv = js["bufferViews"][acc["bufferView"]]
    dt = {5120: "b", 5121: "B", 5122: "h", 5123: "H", 5125: "I", 5126: "f"}[acc["componentType"]]
    n = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[acc["type"]]
    start = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    arr = np.frombuffer(blob, dtype=np.dtype(dt), count=acc["count"] * n, offset=start)
    arr = arr.astype(np.float64)
    if dt in "bh":
        arr /= 127.0
    return arr.reshape(acc["count"], n)


js, blob = load_glb(GLB)
print(f"GLB: {GLB} ({GLB.stat().st_size/1024:.0f} KB) — {len(js['meshes'])} meshes, "
      f"{len(js.get('materials', []))} materiais")


def to_build(v):  # glTF Y-up -> build Z-up
    return np.stack([v[:, 0], -v[:, 2], v[:, 1]], axis=1)


meshes = {}
for m in js["meshes"]:
    name = m.get("name", "mesh")
    pos = acc_data(js, blob, m["primitives"][0]["attributes"]["POSITION"])
    idx = acc_data(js, blob, m["primitives"][0]["indices"]).astype(np.int64).reshape(-1)
    meshes[name] = (to_build(pos), idx)

pts = {n: p for n, (p, i) in meshes.items()}

# pele = malha maior
pele_name = max(meshes, key=lambda n: len(meshes[n][0]))
pele_pos, pele_idx = meshes[pele_name]
tris = pele_pos[pele_idx].reshape(-1, 3, 3)
head_tris = tris[tris[:, :, 2].min(axis=1) > 1.44]

print(f"pele: '{pele_name}' {len(pele_pos)} verts | objetos extras: {len(meshes)-1}")


def ray(o, d, tris=head_tris, tmax=0.6):
    o, d = np.asarray(o, float), np.asarray(d, float)
    v0, v1, v2 = tris[:, 0], tris[:, 1], tris[:, 2]
    e1, e2 = v1 - v0, v2 - v0
    h = np.cross(d, e2)
    a = np.einsum('ij,ij->i', e1, h)
    ok = np.abs(a) > 1e-12
    f = np.zeros_like(a)
    f[ok] = 1.0 / a[ok]
    s = o - v0
    u = f * np.einsum('ij,ij->i', s, h)
    q = np.cross(s, e1)
    v = f * np.einsum('ij,j->i', q, d)
    t = f * np.einsum('ij,ij->i', e2, q)
    hit = ok & (u >= 0) & (u <= 1) & (v >= 0) & (u + v <= 1) & (t > 0) & (t < tmax)
    return t[hit] if hit.any() else None


# ---- 1. silhueta da cabeça
zmax = pele_pos[:, 2].max()
print(f"\n== SILHUETA DA CABEÇA (pele) — topo em z={zmax:.3f} ==")
print(f"{'z':>6} {'larg_x':>7} {'prof_y':>7} {'y_front':>8} {'y_tras':>7}")
for z in np.arange(1.45, zmax + 0.001, 0.02):
    sel = pele_pos[(pele_pos[:, 2] > z - 0.012) & (pele_pos[:, 2] < z + 0.012)]
    if len(sel) < 3:
        continue
    print(f"{z:6.2f} {sel[:,0].ptp():7.3f} {sel[:,1].ptp():7.3f} "
          f"{sel[:,1].min():8.3f} {sel[:,1].max():7.3f}")

# ---- 2. cada peça facial vs pele
print("\n== PEÇAS FACIAIS vs SUPERFÍCIE DA PELE ==")
print("(flutua = distância da peça à frente da pele; negativo = enterrada)")
ordem = ["esclera", "iris", "pupila", "cornea", "brilho", "palpebra", "sobrancelha",
         "cilios", "labio", "linha_boca", "narina"]
for pref in ordem:
    for name in sorted(meshes):
        if name == pele_name or not name.startswith(pref):
            continue
        p = pts[name]
        c = p.mean(axis=0)
        t = ray((c[0], c[1] - 0.30, c[2]), (0, 1, 0))
        flut = (c[1] - 0.30 + t.min()) if t is not None else None
        msg = f"{flut:+.4f} m" if flut is not None else "  sem pele atrás!"
        print(f"{name:20s} c=({c[0]:+.3f},{c[1]:+.3f},{c[2]:+.3f}) pele_y={msg}")
        break  # um lado basta (simétrico)

# ---- 3. orelha
print("\n== ORELHAS ==")
print("malhas de orelha dedicadas:", [n for n in meshes if "orelha" in n.lower()] or "NENHUMA")
for s, lado in ((1, "x+"), (-1, "x-")):
    for z in (1.555, 1.572, 1.588, 1.605):
        t = ray((s * 0.30, 0.006, z), (-s, 0, 0))
        if t is not None:
            print(f"  {lado} z={z:.3f}: borda lateral da pele em x={s*(0.30-t.min()):+.4f}")

# ---- 4. cobertura de cabelo no couro
print("\n== CABELO: cobertura do couro cabeludo (amostras no topo) ==")
hair_names = [n for n in meshes if any(k in n for k in ("calota", "franja", "rabo", "coque", "elastico"))]
hair_pts = [pts[n] for n in hair_names]
hair_all = np.concatenate(hair_pts) if hair_pts else np.zeros((0, 3))
for ax, ay in [(0, 0), (0, 0.04), (0, 0.08), (0.05, 0), (0.05, 0.05),
               (-0.05, 0), (0, -0.04), (0.07, 0.02), (0.07, 0.07), (0.02, -0.05)]:
    t = ray((ax, ay, 1.40), (0, 0, 1), tris=tris[tris[:, :, 2].min(axis=1) > 1.40], tmax=0.5)
    z_pele = 1.40 + t.min() if t is not None else float("nan")
    d = np.sqrt((hair_all[:, 0] - ax) ** 2 + (hair_all[:, 1] - ay) ** 2) if len(hair_all) else np.array([])
    near = hair_all[d < 0.010]
    z_cab = near[:, 2].max() if len(near) else None
    cobre = z_cab is not None and z_cab >= z_pele - 0.002
    print(f"  (x={ax:+.2f},y={ay:+.2f}) pele z={z_pele:.3f}  cabelo z="
          f"{'--' if z_cab is None else f'{z_cab:.3f}'}  {'OK' if cobre else 'SEM CABELO AQUI'}")
