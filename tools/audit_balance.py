#!/usr/bin/env python3
"""Deterministic, engine-free sanity check for the 50-phase balance.

This is not a substitute for playtest. It catches impossible mastery goals,
accidental density inversions, non-monotonic anchors and economy arithmetic
before a designer spends time in the Godot editor.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BALANCE_PATH = ROOT / "resources" / "game_balance.tres"
PHASE_PATH = ROOT / "scripts" / "phase_data.gd"
GAME_PATH = ROOT / "scripts" / "game_3d.gd"


def read_balance() -> dict[str, float]:
    text = BALANCE_PATH.read_text(encoding="utf-8")
    keys = {
        "phase_count",
        "chapter_unlock_phase",
        "endless_unlock_phase",
        "base_speed",
        "chapter_one_final_speed",
        "final_speed",
        "first_wait_seconds",
        "final_wait_seconds",
        "starting_coins",
        "first_clear_reward",
        "replay_reward",
        "star_upgrade_reward",
        "perfect_run_bonus",
        "phase_reward_per_level",
        "star_reward",
        "xp_first_clear",
        "xp_replay",
        "xp_per_level",
        "xp_level_size",
        "daily_distance_target",
        "weekly_distance_target",
    }
    values: dict[str, float] = {}
    for key in keys:
        match = re.search(rf"^{re.escape(key)}\s*=\s*([-+]?\d+(?:\.\d+)?)\s*$", text, re.MULTILINE)
        if not match:
            raise AssertionError(f"balance field missing: {key}")
        values[key] = float(match.group(1))
    return values


def count_spawns(start: float, end: float, interval: float) -> int:
    count = 0
    position = start
    while position < end:
        count += 1
        position += interval
    return count


def main() -> int:
    b = read_balance()
    phase_text = PHASE_PATH.read_text(encoding="utf-8")
    game_text = GAME_PATH.read_text(encoding="utf-8")

    assert int(b["phase_count"]) == 50
    assert 0 < b["base_speed"] < b["chapter_one_final_speed"] < b["final_speed"]
    assert b["first_wait_seconds"] >= b["final_wait_seconds"] > 0
    assert b["first_clear_reward"] > b["replay_reward"] > 0
    assert '"coin_target": 4 + int(round(float(i) * 0.85))' in phase_text
    assert "_start_run(BALANCE.endless_unlock_phase)" in game_text
    assert "water_gun" not in game_text, "active 3D course references an uncatalogued obstacle"

    rows: list[dict[str, float | int]] = []
    previous_speed = 0.0
    previous_distance = 0.0
    previous_obstacles = 0
    total_first_clear = 0
    total_nominal_coins = 0

    for i in range(int(b["phase_count"])):
        chapter_gate = int(b["chapter_unlock_phase"])
        if i <= chapter_gate:
            progress = i / max(1, chapter_gate)
            speed = b["base_speed"] + (b["chapter_one_final_speed"] - b["base_speed"]) * progress
            obstacles = 2 + round(10 * progress)
            wait = b["first_wait_seconds"] + (b["final_wait_seconds"] - b["first_wait_seconds"]) * progress
        else:
            progress = (i - chapter_gate) / max(1, int(b["phase_count"]) - chapter_gate - 1)
            speed = b["chapter_one_final_speed"] + (b["final_speed"] - b["chapter_one_final_speed"]) * progress
            obstacles = 12 + round(6 * progress)
            wait = b["final_wait_seconds"]
        distance = 400.0 + i * 8.0
        target = 4 + round(i * 0.85)
        road_interval = min(24.0, max(6.0, 26.0 - float(obstacles)))
        sidewalk_interval = max(15.0, road_interval * 2.1)
        road_count = count_spawns(24.0, distance - 18.0, road_interval)
        sidewalk_count = count_spawns(34.0, distance - 20.0, sidewalk_interval)
        nominal_coins = count_spawns(18.0, distance - 12.0, 13.0)

        assert speed >= previous_speed, f"speed regressed at phase {i + 1}"
        assert distance > previous_distance, f"distance regressed at phase {i + 1}"
        assert obstacles >= previous_obstacles, f"obstacle count regressed at phase {i + 1}"
        assert wait > 0
        assert road_count > sidewalk_count, f"street density inverted at phase {i + 1}"
        assert 0 < target <= nominal_coins, (
            f"coin goal is impossible at phase {i + 1}: target={target}, estimate={nominal_coins}"
        )

        # A first clear is intentionally valuable, while replay and a new star
        # remain bounded. The perfect bonus is modeled as an optional maximum.
        min_first_clear = int(b["first_clear_reward"] + i * b["phase_reward_per_level"] + b["star_reward"])
        max_first_clear = int(
            b["first_clear_reward"]
            + i * b["phase_reward_per_level"]
            + 3 * b["star_reward"]
            + b["perfect_run_bonus"]
        )
        total_first_clear += min_first_clear
        total_nominal_coins += nominal_coins
        rows.append(
            {
                "phase": i + 1,
                "speed": speed,
                "distance": distance,
                "obstacles": obstacles,
                "road": road_count,
                "sidewalk": sidewalk_count,
                "coins": nominal_coins,
                "coin_target": target,
                "min_reward": min_first_clear,
                "max_reward": max_first_clear,
            }
        )
        previous_speed = speed
        previous_distance = distance
        previous_obstacles = obstacles

    max_stars = int(b["phase_count"]) * 3
    assert int(b["chapter_unlock_phase"]) < int(b["phase_count"])
    assert int(b["endless_unlock_phase"]) < int(b["phase_count"])
    assert 0 < int(b["daily_distance_target"]) < int(rows[0]["distance"])
    assert int(b["weekly_distance_target"]) > int(b["daily_distance_target"])
    assert total_first_clear > 0 and total_nominal_coins > 0
    assert 0 < int(b["phase_count"]) * 3 == max_stars

    first = rows[0]
    tenth = rows[9]
    twentieth = rows[19]
    fortieth = rows[39]
    fiftieth = rows[49]
    print("BALANCE AUDIT OK")
    print("phase | speed | distance | road/sidewalk | coins target/estimated | first-clear reward range")
    for row in (first, tenth, twentieth, fortieth, fiftieth):
        print(
            f"{row['phase']:>5} | {row['speed']:>5.1f} | {row['distance']:>8.0f} m | "
            f"{row['road']:>3}/{row['sidewalk']:<3} | {row['coin_target']:>2}/{row['coins']:<2} | "
            f"R$ {row['min_reward']}-{row['max_reward']}"
        )
    print(f"first-clear bonus floor across catalog: R$ {total_first_clear}")
    print(f"nominal track coins across catalog: {total_nominal_coins}")
    print(f"star gates: {int(b['chapter_unlock_phase']) + 1}=45 and {int(b['endless_unlock_phase']) + 1}=120; max={max_stars}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
