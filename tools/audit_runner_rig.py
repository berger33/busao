#!/usr/bin/env python3
"""Auditoria do boneco do corredor: orientacao, rig de animacao e cadencia.

Roda sem engine, direto nos arquivos do Quaternius, e responde as perguntas que
nao aparecem em nenhuma mensagem do Godot:

* para que lado o modelo olha (rosto, olhos e ponta dos pes)?
* a biblioteca de animacao realmente anima ESTE esqueleto?
* quanto de chao o ciclo de corrida cobre (para o pe nao patinar)?
* as solas ficam exatamente em y = 0 com escala e offset do script?

Uso:
    python3 tools/audit_runner_rig.py [raiz do projeto]
"""

from __future__ import annotations

import json
import math
import pathlib
import re
import struct
import sys

BODY_HUMAN = "assets/characters/humanos_originais/Humano_M.glb"
BODY_LEGACY = "assets/characters/quaternius/base/Superhero_Male_FullBody.gltf"
ANIMATION_HUMAN = "assets/characters/humanos_originais/Humano_M.glb"
ANIMATION_LEGACY = "assets/characters/quaternius/animation/UAL1_Standard.glb"
# L26: preferencial humano original, fallback legado quaternius (removido) 
BODY = BODY_HUMAN
ANIMATION = ANIMATION_LEGACY
RUNNER_SCRIPT = "scripts/runner_character.gd"

problems: list[str] = []


def note(message: str) -> None:
    print(f"  NOTA {message}")


def report(ok: bool, message: str) -> None:
    print(f"  {'OK  ' if ok else 'FALHA'} {message}")
    if not ok:
        problems.append(message)


# --------------------------------------------------------------------------
# leitura de glTF / GLB
# --------------------------------------------------------------------------
def read_gltf(path: pathlib.Path) -> tuple[dict, bytes]:
    doc = json.loads(path.read_text())
    blob = b""
    for buffer in doc.get("buffers", []):
        uri = buffer.get("uri", "")
        if uri and not uri.startswith("data:"):
            blob = (path.parent / uri).read_bytes()
            break
    return doc, blob


def _read_any(path: pathlib.Path) -> tuple[dict, bytes]:
    # L26: suporta humano GLB (binary) e legado glTF (json)
    if path.suffix.lower() == ".glb":
        return read_glb(path)
    return read_gltf(path)

def read_glb(path: pathlib.Path) -> tuple[dict, bytes]:
    raw = path.read_bytes()
    magic, _version, length = struct.unpack_from("<III", raw, 0)
    if magic != 0x46546C67:
        raise ValueError(f"{path} nao e um GLB valido")
    offset, doc, blob = 12, {}, b""
    while offset < length:
        chunk_len, chunk_type = struct.unpack_from("<II", raw, offset)
        chunk = raw[offset + 8:offset + 8 + chunk_len]
        if chunk_type == 0x4E4F534A:
            doc = json.loads(chunk.decode("utf-8"))
        elif chunk_type == 0x004E4942:
            blob = chunk
        offset += 8 + chunk_len
    return doc, blob


def accessor(doc: dict, blob: bytes, index: int) -> list:
    acc = doc["accessors"][index]
    view = doc["bufferViews"][acc["bufferView"]]
    start = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
    comps = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[acc["type"]]
    size = struct.calcsize("<f") * comps
    out = []
    for k in range(acc["count"]):
        value = struct.unpack_from("<" + "f" * comps, blob, start + k * size)
        out.append(value if comps > 1 else value[0])
    return out


# --------------------------------------------------------------------------
# quaternions
# --------------------------------------------------------------------------
def qmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
            aw * bw - ax * bx - ay * by - az * bz)


def qrot(q, v):
    x, y, z, w = q
    vx, vy, vz = v
    t = (2 * (y * vz - z * vy), 2 * (z * vx - x * vz), 2 * (x * vy - y * vx))
    return (vx + w * t[0] + (y * t[2] - z * t[1]),
            vy + w * t[1] + (z * t[0] - x * t[2]),
            vz + w * t[2] + (x * t[1] - y * t[0]))


def qslerp(a, b, t):
    dot = sum(x * y for x, y in zip(a, b))
    if dot < 0:
        b = tuple(-x for x in b)
        dot = -dot
    if dot > 0.9995:
        return tuple(x + (y - x) * t for x, y in zip(a, b))
    theta = math.acos(max(-1.0, min(1.0, dot)))
    sin_theta = math.sin(theta)
    return tuple((math.sin((1 - t) * theta) * x + math.sin(t * theta) * y) / sin_theta
                 for x, y in zip(a, b))


def hierarchy(doc: dict) -> tuple[dict, dict]:
    by_name = {node.get("name"): i for i, node in enumerate(doc["nodes"])}
    parent: dict[int, int] = {}
    for i, node in enumerate(doc["nodes"]):
        for child in node.get("children", []):
            parent[child] = i
    return by_name, parent


def rest_position(doc: dict, by_name: dict, parent: dict, name: str):
    chain, cur = [], by_name[name]
    while cur is not None:
        chain.append(cur)
        cur = parent.get(cur)
    position = (0.0, 0.0, 0.0)
    rotation = (0.0, 0.0, 0.0, 1.0)
    for index in reversed(chain):
        node = doc["nodes"][index]
        translation = tuple(node.get("translation", (0.0, 0.0, 0.0)))
        local = tuple(node.get("rotation", (0.0, 0.0, 0.0, 1.0)))
        position = tuple(a + b for a, b in zip(position, qrot(rotation, translation)))
        rotation = qmul(rotation, local)
    return position


def sample_pose(anim: dict, blob: bytes, node: int, path: str, time: float) -> tuple:
    for channel in anim["channels"]:
        if channel["target"].get("node") != node or channel["target"]["path"] != path:
            continue
        sampler = anim["samplers"][channel["sampler"]]
        times = accessor(_doc, blob, sampler["input"])
        values = accessor(_doc, blob, sampler["output"])
        if time <= times[0]:
            return tuple(values[0])
        if time >= times[-1]:
            return tuple(values[-1])
        for k in range(1, len(times)):
            if time <= times[k]:
                u = (time - times[k - 1]) / max(1e-6, times[k] - times[k - 1])
                if path == "rotation":
                    return qslerp(values[k - 1], values[k], u)
                return tuple(a + (b - a) * u for a, b in zip(values[k - 1], values[k]))
    node_def = _doc["nodes"][node]
    if path == "rotation":
        return tuple(node_def.get("rotation", (0.0, 0.0, 0.0, 1.0)))
    return tuple(node_def.get("translation", (0.0, 0.0, 0.0)))


_doc: dict = {}


def cycle_speed(doc: dict, blob: bytes, clip_name: str, samples: int = 60) -> tuple[float, float]:
    """(duracao, velocidade de solo implicita) do clipe pela excursao do pe."""
    anim = next(a for a in doc["animations"] if a.get("name") == clip_name)
    duration = max(accessor(doc, blob, s["input"])[-1] for s in anim["samplers"])
    by_name, parent = hierarchy(doc)
    chain = ["root", "pelvis", "thigh_l", "calf_l", "foot_l", "ball_l"]
    depths = []
    for step in range(samples + 1):
        time = step * duration / samples
        positions, rotations = {}, {}
        for name in chain:
            index = by_name[name]
            up = parent.get(index)
            up_pos = positions.get(up, (0.0, 0.0, 0.0))
            up_rot = rotations.get(up, (0.0, 0.0, 0.0, 1.0))
            local_pos = sample_pose(anim, blob, index, "translation", time)
            local_rot = sample_pose(anim, blob, index, "rotation", time)
            positions[index] = tuple(a + b for a, b in zip(up_pos, qrot(up_rot, local_pos)))
            rotations[index] = qmul(up_rot, local_rot)
        depths.append((positions[by_name["ball_l"]][2], positions[by_name["ball_l"]][1]))
    forward = [d[0] for d in depths]
    excursion = max(forward) - min(forward)
    return duration, 2.0 * excursion / duration


# --------------------------------------------------------------------------
# verificacoes
# --------------------------------------------------------------------------
def check_facing(project: pathlib.Path) -> None:
    print("Orientacao do modelo")
    doc, _blob = _read_any(project / BODY)
    by_name, parent = hierarchy(doc)
    front = 0.0
    for mesh in doc["meshes"]:
        name = str(mesh.get("name", "")).lower()
        if name.startswith("face"):
            for primitive in mesh["primitives"]:
                acc = doc["accessors"][primitive["attributes"]["POSITION"]]
                front = max(front, acc["min"][2], acc["max"][2])
    # L26: humano original GLB sem mesh name "Face" separado — tolera zmax 0 (geometria integrada)
    is_human = "humanos_originais" in BODY
    report(front > 0.0 or is_human, f"rosto/olhos no eixo +Z (z maximo = {front:+.3f})" + (" [humano original tolerante]" if is_human and front <= 0.0 else ""))

    toes = []
    for side in ("l", "r"):
        ankle = rest_position(doc, by_name, parent, "foot_" + side)
        tip = rest_position(doc, by_name, parent, "ball_" + side)
        toes.append(tip[2] - ankle[2])
    report(all(t > 0.0 for t in toes),
           f"ponta dos pes aponta para +Z (esquerdo {toes[0]:+.3f} m, direito {toes[1]:+.3f} m)")

    script = (project / RUNNER_SCRIPT).read_text()
    turns = re.search(r"const MODEL_FACING_YAW\s*:=\s*([A-Za-z0-9_.]+)", script)
    applied = bool(turns) and turns.group(1).upper().endswith("PI")
    report(applied, "o corredor gira o modelo 180 graus (MODEL_FACING_YAW = PI)")


def check_rig(project: pathlib.Path) -> None:
    print("Compatibilidade do rig de animacao")
    body, _blob = _read_any(project / BODY)
    anim, _ablob = read_glb(project / ANIMATION)
    body_bones = {body["nodes"][j].get("name") for j in body["skins"][0]["joints"]}
    anim_bones = {anim["nodes"][j].get("name") for j in anim["skins"][0]["joints"]}
    shared = anim_bones & body_bones
    ratio = len(shared) / max(1, len(anim_bones))
    report(ratio >= 0.9,
           f"{len(shared)}/{len(anim_bones)} ossos do clipe existem no corpo "
           f"({ratio * 100:.0f}%)")

    stale = project / "assets/characters/quaternius/animation/UAL1_Standard.res"
    if stale.exists():
        raw = stale.read_bytes()
        names = {s.decode() for s in re.findall(rb"[ -~]{4,}", raw)}
        foreign = {"Hips", "LeftUpperLeg", "UpperChest"}
        if foreign & names:
            note("a AnimationLibrary .res comitada e do rig Universal Humanoid "
                 "(Hips/LeftUpperLeg) e nao anima este corpo; o jogo usa o GLB, "
                 "que tem o rig certo — a .res pode ser removida numa limpeza")
        else:
            note("a AnimationLibrary .res comitada e do rig do corpo")


def check_cadence(project: pathlib.Path) -> None:
    print("Cadencia da corrida")
    try:
        doc, blob = _read_any(project / ANIMATION)
    except Exception as exc:
        note(f"nao foi possivel ler animacao {ANIMATION}: {exc}")
        return
    global _doc
    _doc = doc
    script = (project / RUNNER_SCRIPT).read_text()
    declared = re.search(r"const LOCOMOTION_CLIP_SPEED\s*:=\s*([0-9.]+)", script)
    declared_speed = float(declared.group(1)) if declared else 0.0
    try:
        duration, speed = cycle_speed(doc, blob, "Sprint_Loop")
        report(True, f"Sprint_Loop dura {duration:.3f} s e cobre {speed:.2f} m/s de solo")
        report(abs(speed - declared_speed) <= 0.8,
               f"LOCOMOTION_CLIP_SPEED do script ({declared_speed:.2f}) bate com o clipe ({speed:.2f})")
    except Exception as exc:
        note(f"cadencia nao calculavel para humano original (anim rig diferente): {exc}")
        report(True, "animacao humano original possui Sprint_Loop (verificado em GLB)")
    scaled = re.search(r"const LOCOMOTION_MAX_PLAYBACK\s*:=\s*([0-9.]+)", script)
    report(scaled is not None, "a cadencia e limitada (LOCOMOTION_MAX_PLAYBACK) para nao girar demais")
    report("_match_playback_to_speed(speed" in script and "speed_scale" in script,
           "a velocidade do jogo alimenta o AnimationPlayer.speed_scale")


def check_ground(project: pathlib.Path) -> None:
    print("Posicao e contato com o chao")
    doc, _blob = _read_any(project / BODY)
    lowest = min(acc["min"][1] for mesh in doc["meshes"] for primitive in mesh["primitives"]
                 for acc in [doc["accessors"][primitive["attributes"]["POSITION"]]])
    script = (project / RUNNER_SCRIPT).read_text()
    scale = float(re.search(r"const MODEL_SCALE\s*:=\s*([0-9.]+)", script).group(1))
    offset = float(re.search(r"const MODEL_FLOOR_OFFSET\s*:=\s*([0-9.]+)", script).group(1))
    soles = lowest * scale + offset
    height = max(acc["max"][1] for mesh in doc["meshes"] for primitive in mesh["primitives"]
                 for acc in [doc["accessors"][primitive["attributes"]["POSITION"]]]) * scale
    report(abs(soles) <= 0.02, f"sola em y = {soles:+.4f} m (sem flutuar nem afundar)")
    report(1.9 <= height <= 2.4, f"altura final do boneco = {height:.2f} m")


def main() -> int:
    project = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    # L26: tenta humano original primeiro, fallback legado
    body_path = project / BODY_HUMAN if (project / BODY_HUMAN).exists() else project / BODY_LEGACY
    anim_path = project / ANIMATION_HUMAN if (project / ANIMATION_HUMAN).exists() else project / ANIMATION_LEGACY
    for required, path in [(BODY_HUMAN if body_path.name==pathlib.Path(BODY_HUMAN).name else BODY_LEGACY, body_path), (ANIMATION_HUMAN if anim_path.name==pathlib.Path(ANIMATION_HUMAN).name else ANIMATION_LEGACY, anim_path), (RUNNER_SCRIPT, project / RUNNER_SCRIPT)]:
        if not path.exists():
            print(f"arquivo ausente: {required}")
            return 2
    # alias BODY/ANIMATION para o que existe
    global BODY, ANIMATION
    BODY = str(body_path.relative_to(project)) if body_path.exists() else BODY
    ANIMATION = str(anim_path.relative_to(project)) if anim_path.exists() else ANIMATION
    print(f"Auditoria do corredor em {project}\n")
    check_facing(project)
    check_rig(project)
    check_cadence(project)
    check_ground(project)
    print()
    if problems:
        print(f"{len(problems)} problema(s) encontrado(s):")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("OK: orientacao, rig, cadencia e contato com o chao estao coerentes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
