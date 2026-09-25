#!/usr/bin/env python3
"""Replica Python fiel de scripts/pattern_validator.gd (ETAPA 4 + dinamicos ETAPA 8).

Le os dados REAIS de scripts/level_data.gd e scripts/obstacle_rules.gd via
regex (sem duplicar tabelas) e executa o mesmo algoritmo do validador:
estacoes, bloqueio por corredor (amostras em +-Z_WINDOW_M), DFS de rota
com pulo/deslize/troca, nas velocidades base e 1.22x.

Uso: python3 tools/validate_routes.py   (exit 1 se alguma fase sem rota)
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

LANE_X = [-3.25, 0.0, 3.25]
SWITCH_S = 0.25
JUMP_S = 0.9
SLIDE_S = 0.72
BOOST_FACTOR = 1.22
STATION_TOLERANCE_M = 2.0
Z_WINDOW_M = 0.6

JUMP_CLEARS = {"LOW", "GROUND", "SOFT"}
SLIDE_CLEARS = {"SLIDE_UNDER"}


def parse_rules():
    text = (ROOT / "scripts" / "obstacle_rules.gd").read_text(encoding="utf-8")
    classes = dict(re.findall(r'"(\w+)": Classe\.(\w+)', text))
    widths = {k: float(v) for k, v in re.findall(r'"(\w+)": ([\d.]+)', text)}
    assert len(classes) == 27, f"esperava 27 classes, achei {len(classes)}"
    return classes, widths


PATTERN_RE = re.compile(
    r'\{"kind": "(\w+)", "lane": (\d), "at_m": ([\d.]+)'
    r'(, "from_x": ([-\d.]+), "to_x": ([-\d.]+), "cross_mps": ([\d.]+), "lead_m": ([\d.]+))?\}'
)
PHASE_RE = re.compile(r"^const (FASE_\d+|PILOT): Dictionary = \{$")


def parse_levels():
    phases = []
    current = None
    in_patterns = False
    for line in (ROOT / "scripts" / "level_data.gd").read_text(encoding="utf-8").splitlines():
        m = PHASE_RE.match(line)
        if m:
            current = {"name": m.group(1), "patterns": []}
            phases.append(current)
            in_patterns = False
            continue
        if current is None:
            continue
        s = line.strip()
        if s.startswith('"patterns": ['):
            in_patterns = True
            continue
        if in_patterns and s == "],":
            in_patterns = False
            continue
        if in_patterns:
            m = PATTERN_RE.search(s)
            if m:
                p = {"kind": m.group(1), "lane": int(m.group(2)), "at_m": float(m.group(3))}
                if m.group(4):
                    p.update({"from_x": float(m.group(5)), "to_x": float(m.group(6)),
                              "cross_mps": float(m.group(7)), "lead_m": float(m.group(8))})
                current["patterns"].append(p)
            continue
        m = re.match(r'"phase_index": (\d+),?', s)
        if m:
            current["phase_index"] = int(m.group(1))
        m = re.match(r'"base_speed_mps": ([\d.]+),?', s)
        if m:
            current["base_speed_mps"] = float(m.group(1))
    return phases


def stations_from(patterns, classes):
    obstacles = []
    for p in patterns:
        entry = {"kind": p["kind"], "lane": p["lane"], "at_m": p["at_m"],
                 "classe": classes.get(p["kind"], "FULL")}
        for k in ("from_x", "to_x", "lead_m", "cross_mps"):
            if k in p:
                entry[k] = p[k]
        obstacles.append(entry)
    obstacles.sort(key=lambda o: o["at_m"])
    stations = []
    for o in obstacles:
        if not stations or o["at_m"] - stations[-1]["at_m"] > STATION_TOLERANCE_M:
            stations.append({"at_m": o["at_m"], "obstacles": [o]})
        else:
            stations[-1]["obstacles"].append(o)
    return stations


def obstacle_x_at(o, d, speed):
    if "cross_mps" not in o:
        return LANE_X[max(0, min(2, o["lane"]))]
    start_d = o["at_m"] - o["lead_m"]
    walked = o["cross_mps"] * max(0.0, (d - start_d) / speed)
    total = abs(o["to_x"] - o["from_x"])
    direction = 1.0 if o["to_x"] >= o["from_x"] else -1.0
    return o["from_x"] + direction * min(walked, total)


def lane_blocks(stations, speed, widths):
    blocks = []
    for station in stations:
        at_m = station["at_m"]
        lanes = [[], [], []]
        for o in station["obstacles"]:
            width = widths.get(o["kind"], 1.2)
            for sample in (at_m - Z_WINDOW_M, at_m, at_m + Z_WINDOW_M):
                x = obstacle_x_at(o, sample, speed)
                for lane in range(3):
                    if abs(x - LANE_X[lane]) <= width + 0.001 and not any(q is o for q in lanes[lane]):
                        lanes[lane].append(o)
        blocks.append(lanes)
    return blocks


def action_for(obstacles):
    needs_jump = needs_slide = False
    for o in obstacles:
        if o["classe"] in JUMP_CLEARS:
            needs_jump = True
        elif o["classe"] in SLIDE_CLEARS:
            needs_slide = True
        else:
            return "none"
    if needs_jump and needs_slide:
        return "none"
    if needs_jump:
        return "jump"
    if needs_slide:
        return "slide"
    return "free"


def covered_by_last(obstacles, last_action, last_action_end, at_m):
    if last_action_end <= at_m:
        return False
    for o in obstacles:
        if last_action == "jump" and o["classe"] in JUMP_CLEARS:
            continue
        if last_action == "slide" and o["classe"] in SLIDE_CLEARS:
            continue
        return False
    return True


def search(stations, blocks, i, lane, busy_until, last_action, last_action_end, speed, route):
    if i >= len(stations):
        return True
    at_m = stations[i]["at_m"]
    for target_lane in range(3):
        steps = abs(target_lane - lane)
        change_start = at_m - speed * SWITCH_S * steps
        if steps > 0 and busy_until > change_start:
            continue
        in_lane = blocks[i][target_lane]
        next_busy = busy_until if steps == 0 else at_m
        next_action, next_action_end = last_action, last_action_end
        if not in_lane:
            decision = "pass"
        elif covered_by_last(in_lane, last_action, last_action_end, at_m):
            decision = "carry"
        else:
            action = action_for(in_lane)
            if action == "none" or next_busy > at_m:
                continue
            duration = JUMP_S if action == "jump" else SLIDE_S
            decision = action
            next_busy = at_m + speed * duration
            next_action, next_action_end = action, next_busy
        route.append({"at_m": at_m, "lane": target_lane, "action": decision})
        if search(stations, blocks, i + 1, target_lane, next_busy, next_action,
                  next_action_end, speed, route):
            return True
        route.pop()
    return False


def validate_phase(phase, classes, widths):
    base = phase["base_speed_mps"]
    for factor in (1.0, BOOST_FACTOR):
        speed = base * factor
        stations = stations_from(phase["patterns"], classes)
        if not stations:
            continue
        blocks = lane_blocks(stations, speed, widths)
        route = []
        if not search(stations, blocks, 0, 1, -1.0, "", -1.0, speed, route):
            return False, factor, stations, blocks
    return True, 1.0, [], []


def describe_block(station, lanes):
    parts = []
    for lane in range(3):
        kinds = sorted({o["kind"] for o in lanes[lane]})
        parts.append(f"E@{lane}={'+'.join(kinds) if kinds else 'livre'}")
    return f"at_m={station['at_m']:.0f} " + " ".join(parts)


def main():
    classes, widths = parse_rules()
    phases = parse_levels()
    assert len(phases) == 50, f"esperava 50 fases, achei {len(phases)}"
    assert all("phase_index" in p and "base_speed_mps" in p for p in phases), "fase sem indice/velocidade"
    fails = 0
    for phase in sorted(phases, key=lambda p: p["phase_index"]):
        ok, factor, stations, blocks = validate_phase(phase, classes, widths)
        tag = "OK " if ok else "FAIL"
        print(f"  {tag} fase {phase['phase_index']:2d} ({phase['name']:8s}, "
              f"{len(phase['patterns']):2d} padroes, {base if (base := phase['base_speed_mps']) else 0:.1f} m/s)")
        if not ok:
            fails += 1
            print(f"      sem rota legal em {factor}x; estacoes:")
            for st, lanes in zip(stations, blocks):
                print(f"      - {describe_block(st, lanes)}")
    print(f"\nROUTE REPLICA: {50 - fails}/50 fases com rota legal (1.0x e 1.22x)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
