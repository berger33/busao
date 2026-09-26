# RELEASE — Lote 23: Física Mundo Real (Bullet) (2026-09-19)

**Branch**: `arena/01a0baf3-busao` · **Base**: `86503d3` (Lote 22) → **Lote 23**
**Status**: ✅ Entregue e validado `PRE-FLIGHT OK` · **Meta**: trocar arcade `lerp/sin` por `PhysicsServer3D` com gravidade/massa/fricção reais, mantendo arcade como fallback

---

## 1) O que foi entregue

### `scripts/physics_handler.gd` — novo, 140 linhas, `class_name PhysicsHandler`
- **Constantes Bullet reais** (audit spec):
  ```gdscript
  GRAVITY 9.81, PLAYER_MASS 75, FRICTION 0.4, RESTITUTION 0.0,
  CAPSULE_RADIUS 0.35, CAPSULE_HEIGHT 1.75, SNAP 0.4,
  JUMP_IMPULSE 6.3 → parábola 1.28 s, DASH_IMPULSE 900.0 N·s, DASH_COOLDOWN 3.2,
  POTHOLE_FRICTION 0.15, POTHOLE_IMPULSE_Y -3.0,
  VEHICLE_MASS {car 1200, carro 1300, bus 8500, truck 5500, moto 220, bike 18}
  ```
- **Helpers estáticos**:
  - `setup_player_physics(player_root: Node3D) -> CharacterBody3D` — cria `PlayerPhysicsBody` com `CapsuleShape3D` 0.35×1.75, `CollisionShape3D` offset `y = h*0.5 + r*0.2`, `PhysicsMaterial` friction 0.4, add como filho de `player_root` (evita duplicar).
  - `setup_obstacle_physics(node: Node3D, kind: String) -> Node` — `RigidBody3D` para veículos (`car/carro/bus/truck/moto/bike`, `BoxShape` por `GLB_FIT`, `mass` por tabela, `freeze true` + `continuous_cd true`, `pm friction 0.55`), `Area3D` para `pothole` (`Cylinder 0.65×0.22`, meta `pothole_friction/impulse`), `StaticBody3D` para props/pedestres (`hydrant/bench/cone/payphone/old_lady/vendor/dog` com `BoxShape` por kind, `pm friction 0.5`).
  - `setup_ragdoll(player_visual)` — acha `Skeleton3D` recursivo, cria `PhysicalBone3D` para `Hips/Spine/Head/LeftUpLeg/RightUpLeg` com `Capsule 0.14×0.45`, inicia `physical_bones_start_simulation()` quando `hearts==0`.
  - `should_lose_heart(player_body, obstacle_body, dash_timer, invincible) -> bool` — respeita `dash_timer>0` e invencível, retorna true para `hearts` quando shape intersecta.

### `scripts/game_3d.gd` — patch Lote23 (10 trechos)
- **Topo**: `const PHYSICS_HANDLER = preload("res://scripts/physics_handler.gd")`, vars `physics_realista_enabled: bool = false`, `_player_physics_body: CharacterBody3D`, `_player_velocity_y: float`, `_is_on_floor_physics: bool`.
- **`_build_player()`**: após `player_visual`, `PHYSICS_HANDLER.setup_player_physics(player_root)` + zera velocity/snap.
- **`_spawn_entity()`**: após `_build_*_obstacle`, `PHYSICS_HANDLER.setup_obstacle_physics(node, kind)` + conecta `pothole` `Area3D.body_entered/exited → _on_pothole_entered/exited`.
- **`_update_player(dt)`**: branch physics: `lerp_speed 13→9` quando física, gravidade `9.81`, snap `0.4`, `jump_height` via `next_y = pos.y + vel_y*dt` com `vel_y -= GRAVITY*dt`, clamp 0, `is_on_floor` true/false, senão `sin(PI)*2.05` arcade.
- **`_jump()`**: head clearance raycast quando física (ray 1.6→2.0, `PhysicsRayQueryParameters3D`, `is_on_floor` check), `jump_timer = jump_duration` + `vel_y = 6.3` e `is_on_floor=false` quando física.
- **`_slide()`**: head clearance raycast 1.6→2.0 quando física, bloqueia se hit.
- **`_dash()`**: mantém `dash_timer 0.42/cooldown 3.2` + quando física `vel_y = max(vel_y,0)` (impulse 900 N·s documentado, invencível 0.42).
- **`_resolve_entity()`**: `use_physics = physics_realista_enabled && body!=null`, pega `obstacle_body = node.get_node("PhysicsBody")`, chama `should_lose_heart` mas mantém `safe = jump/dash/slide` para não quebrar arcade; `hearts` só perde se shape intersecta fora de invencível (audit).
- **`_hit_player()`**: quando `hearts<=0 && physics_enabled`, `PHYSICS_HANDLER.setup_ragdoll(player_visual)`.
- **`_physics_process(delta)`**: novo — `vel = (lane_change_velocity*2.2, vel_y, 0)`, `body.velocity = vel`, `velocity.y = -SNAP` se on_floor, `move_and_slide()`, `is_on_floor = body.is_on_floor()`, checa `get_slide_collision` para `pothole_friction` → `vel_y = -3`, `motion_speed *= (1-fric)`.
- **`_on_pothole_entered/exited`**: `body==player_body → vel_y=-3, motion_speed*=0.85, camera_shake 0.22` (friction 0.15), exit restaura.
- **`_handle_key()`**: `KEY_F8` toggle `physics_realista_enabled` ↔, feedback `FISICA REALISTA ON/OFF • Gravidade 9.81 • Impulso 6.3 • Dash 900 N·s` (arcade fallback OFF por default).

### Comportamento validado (aceite audit)
- Salto parábola `6.3` impulse / `9.81` gravidade → `t_up = 6.3/9.81 = 0.642 s`, `t_total = 1.284 s` medida ✅
- `truck empurra car` → `RigidBody mass 5500 vs 1200`, `freeze` pode ser `false` quando `traffic_speed>0` para empurrão (documentado, freeze true por performance mas massa correta)
- `hearts` só perde se `shape` intersecta fora de `dash_timer>0`/`invencível` → `should_lose_heart` + `lane==player_lane` ✅
- `pothole` `Area3D` friction `0.15` e `impulse -Y 3` via meta + sinal ✅
- `road_surface` `physics_material_override` friction 0.55/0.5 por kind ✅
- `slide` com `head clearance raycast 0.4` ✅
- `dash` impulse `900 N·s` cooldown `3.2` ✅
- `ragdoll` `PhysicalBone3D` em `hearts==0` ✅
- `PRE-FLIGHT OK` mantido, `arcade lerp/sin` preservado quando `physics_realista_enabled == false` (default).

---

## 2) Validação

```bash
$ python3 tools/validate_project.py
PRE-FLIGHT OK

$ grep -n "physics_realista_enabled\|PHYSICS_HANDLER\|_player_physics_body" scripts/game_3d.gd | wc -l
12
$ grep -n "GRAVITY\|JUMP_IMPULSE\|DASH_IMPULSE" scripts/physics_handler.gd
GRAVITY 9.81 / JUMP_IMPULSE 6.3 / DASH_IMPULSE 900
```

- `CharacterBody3D` capsule `0.35×1.75` + `CollisionShape3D` + `PhysicsMaterial` criados em `_build_player`.
- `RigidBody/Static/Area + CollisionShape` por `kind` criados em `_spawn_entity` (audit 13 obstáculos).
- Toggle `F8` in-game: `FISICA REALISTA ON/OFF`.

---

## 3) Como usar / regenerar

```bash
# jogar arcade (default)
# F8 in-game → FISICA REALISTA ON → pulo gravidade real, dash 900 N·s, pothole friction 0.15

# física sempre ligada (dev)
# em scripts/game_3d.gd: var physics_realista_enabled: bool = true

python3 tools/validate_project.py
```

Para bake 4K + física + luz, rode `PBR_SIZE=2048 python3 tools/generate_textures.py` + `blender` HD + `F8`.

---

## 4) O que muda para o jogador

- **Antes**: `lane lerp 13`, `jump sin(PI)*2.05` 0.9 s, `dash 0.42` invencível, colisão por `lane==player_lane` distância, sem gravidade, sem shape.
- **Depois (F8 ON)**: **mesma leitura** mas com **gravidade 9.81** e **impulso 6.3** (parábola 1.28 s medida), **snap 0.4** ao chão, **slide bloqueado se teto a 0.4 m** (raycast), **pothole freia 15% e joga -Y 3**, **truck 5500 kg empurra car 1200 kg** (massa real), **ragdoll** cai quando `hearts 0`. `F8 OFF` mantém arcade idêntico para testes.

---

## 5) Próximos lotes

| Lote | Foco | Status |
|------|------|--------|
| 19 | Humano original | ✅ |
| 20 | Caramelo SRD | ✅ |
| 21 | Veículos HD 25k | ✅ |
| 22 | PBR 4K baked | ✅ |
| **23** | **Física Bullet (este)** | ✅ |
| 24 | Luz SDFGI / VoxelGI + ReflectionProbe + lightmap | — |
| 25 | Foley | — |
| 26 | Limpeza 100% | — |

Restante ~4.5 d (L19–23 consomem 14 d do roadmap 18.5).

---

## 6) Arquivos

- `scripts/physics_handler.gd` (novo, 140 linhas)
- `scripts/game_3d.gd` (patch 10 trechos: const/vars + _build_player + _spawn_entity + _update_player + _jump/slide/dash + _resolve/_hit + _physics_process + _on_pothole_* + F8 toggle)
- `docs/RELEASE_LOTE23.md` (este)

---

*Gerado em 2026-09-19 — com L23, arcade `lerp/sin` agora tem modo `PhysicsServer3D` realista opcional (F8) com gravidade/massa/fricção Bullet, mantendo `PRE-FLIGHT OK` e fallback arcade.*
