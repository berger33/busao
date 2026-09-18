class_name GameBalance
extends Resource
## Fonte única dos números que afetam ritmo, economia e sessões.
## O recurso .tres é versionado para que ajustes de design sejam auditáveis.

@export var version: int = 2
@export var phase_count: int = 50
@export var chapter_unlock_phase: int = 19
@export var endless_unlock_phase: int = 49
@export var base_speed: float = 5.0
@export var chapter_one_final_speed: float = 12.0
@export var final_speed: float = 18.0
@export var first_wait_seconds: float = 5.0
@export var final_wait_seconds: float = 2.0
@export var unlock_chapter_stars: int = 45
@export var unlock_endless_stars: int = 120

@export var starting_coins: int = 40
@export var first_clear_reward: int = 30
@export var replay_reward: int = 8
@export var star_upgrade_reward: int = 12
@export var perfect_run_bonus: int = 8
@export var phase_reward_per_level: int = 3
@export var star_reward: int = 5
@export var xp_first_clear: int = 25
@export var xp_replay: int = 10
@export var xp_per_level: int = 4
@export var xp_level_size: int = 250

@export var daily_distance_target: int = 250
@export var daily_coin_target: int = 10
@export var daily_clean_target: int = 1
@export var daily_base_reward: int = 25
@export var daily_step_reward: int = 10
@export var weekly_distance_target: int = 2500
@export var weekly_reward: int = 100
@export var streak_reward_days: int = 7
@export var streak_reward: int = 100

@export var autosave_seconds: float = 6.0
@export var first_session_hint_distance: float = 70.0
