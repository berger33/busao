#!/usr/bin/env python3
"""Auditoria engine-free da experiência de obstáculos.

Complementa validate_routes.py: aqui olhamos variedade, densidade e margem de
prazo usando os dados reais de level_data/obstacle_data/obstacle_rules.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PHASE_RE = re.compile(r"^const (FASE_\d+|PILOT): Dictionary = \{$")
PATTERN_RE = re.compile(
    r'\{"kind": "(\w+)", "lane": (\d), "at_m": ([\d.]+)'
    r'(, "from_x": ([-\d.]+), "to_x": ([-\d.]+), "cross_mps": ([\d.]+), "lead_m": ([\d.]+))?\}'
)


def parse_obstacle_catalog() -> list[str]:
    text = (ROOT / "scripts" / "obstacle_data.gd").read_text(encoding="utf-8")
    return re.findall(r'"id": "(\w+)"', text)


def parse_classes() -> dict[str, str]:
    text = (ROOT / "scripts" / "obstacle_rules.gd").read_text(encoding="utf-8")
    return dict(re.findall(r'"(\w+)": Classe\.(\w+)', text))


def parse_levels() -> list[dict]:
    phases: list[dict] = []
    current: dict | None = None
    in_patterns = False
    for line in (ROOT / "scripts" / "level_data.gd").read_text(encoding="utf-8").splitlines():
        m = PHASE_RE.match(line)
        if m:
            current = {"const": m.group(1), "patterns": [], "coins": []}
            phases.append(current)
            in_patterns = False
            continue
        if current is None:
            continue
        s = line.strip()
        for key in ("phase_index", "distance_m", "base_speed_mps", "deadline_seconds"):
            m = re.match(rf'"{key}": ([\d.]+),?', s)
            if m:
                value = float(m.group(1))
                current[key] = int(value) if key == "phase_index" else value
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
                    p.update({"dynamic": True, "from_x": float(m.group(5)), "to_x": float(m.group(6)),
                              "cross_mps": float(m.group(7)), "lead_m": float(m.group(8))})
                current["patterns"].append(p)
    return sorted(phases, key=lambda p: int(p["phase_index"]))


def main() -> int:
    catalog = parse_obstacle_catalog()
    classes = parse_classes()
    phases = parse_levels()
    if len(catalog) != 27:
        raise AssertionError(f"catalogo esperava 27 obstaculos, achou {len(catalog)}")
    if len(phases) != 50:
        raise AssertionError(f"esperava 50 fases autorais, achou {len(phases)}")

    active_text = (ROOT / "scripts" / "level_data.gd").read_text(encoding="utf-8") + "\n" + \
        (ROOT / "scripts" / "game_3d.gd").read_text(encoding="utf-8")
    active_catalog = sorted(kind for kind in catalog if f'"{kind}"' in active_text)

    used = Counter()
    class_counter = Counter()
    warnings: list[str] = []
    rows = []
    for phase in phases:
        idx = int(phase["phase_index"])
        patterns = phase["patterns"]
        distance = float(phase["distance_m"])
        speed = float(phase["base_speed_mps"])
        deadline = float(phase["deadline_seconds"])
        margin = deadline - distance / speed
        density = len(patterns) * 100.0 / distance
        dyn = sum(1 for p in patterns if p.get("dynamic"))
        kinds = sorted({p["kind"] for p in patterns})
        class_mix = Counter(classes.get(p["kind"], "UNKNOWN") for p in patterns)
        used.update(p["kind"] for p in patterns)
        class_counter.update(class_mix)
        if idx == 0 and density < 3.2:
            warnings.append(f"fase 1 com densidade baixa: {density:.2f}/100m")
        if idx == 1 and density < 3.8:
            warnings.append(f"fase 2 com densidade baixa: {density:.2f}/100m")
        if margin > 15.0:
            warnings.append(f"fase {idx + 1} com prazo muito folgado: margem {margin:.1f}s")
        if len(kinds) < 2 and idx > 0:
            warnings.append(f"fase {idx + 1} com pouca variedade: {kinds}")
        rows.append({
            "phase": idx + 1,
            "patterns": len(patterns),
            "density": density,
            "speed": speed,
            "margin": margin,
            "dynamic": dyn,
            "kinds": len(kinds),
        })

    # Alguns obstáculos aparecem só no ciclo procedural/endless e nas gags
    # forçadas; contar o jogo inteiro evita falso positivo contra level_data.
    missing = sorted(set(catalog) - set(active_catalog))
    if missing:
        warnings.append("obstaculos catalogados sem referencia ativa: " + ", ".join(missing))

    print("OBSTACLE AUDIT")
    print(f"catalogo: {len(catalog)} familias | ativas no jogo: {len(active_catalog)} | usadas nas fases autorais: {len(used)} | classes autorais: {dict(class_counter)}")
    print("fase | padroes | dens/100m | vel | margem | dinamicos | tipos")
    sample = rows[:10] + rows[19:20] + rows[29:30] + rows[39:40] + rows[49:50]
    for r in sample:
        print(f"{r['phase']:>4} | {r['patterns']:>7} | {r['density']:>8.2f} | "
              f"{r['speed']:>3.1f} | {r['margin']:>6.1f}s | {r['dynamic']:>8} | {r['kinds']:>5}")
    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(" - " + w)
        return 1
    print("OBSTACLE AUDIT OK: variedade completa, onboarding com densidade mínima e prazos sem folga excessiva.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
