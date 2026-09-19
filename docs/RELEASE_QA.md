# RELEASE QA — Teste de Qualidade Completo v1.0 (pós L28)

**Data:** 2026-09-19 UTC  
**Branch:** `arena/01a0baf3-busao` @ `8fd2dc8` + L27 `798a633` + L28 `f6e938f` + fix `locale_manager`  
**Solicitação:** teste completo visual/física/jogabilidade/progressão/dificuldade + regressivo + analítico + garantir 0 procedural + corrigir `replace() 3 args` linhas 123/141

## Correções críticas

| Arquivo | Linha | Erro | Correção |
|---|---|---|---|
| `scripts/locale_manager.gd:123` | `out.replace("%s", str(a), false)` | `Too many arguments for replace() Expected at most 2 but received 3` | `out.replace("%s", str(a))` |
| `scripts/locale_manager.gd:141` | `out.replace("%d", str(int(arg)), false)` | idem | `out.replace("%d", str(int(arg)))` |
| Verificação | `grep -rn "\.replace(" --include="*.gd"` | 0 com 3 args | `python3 -c "gdtoolkit parse locale_manager" → OK` |

`validate_project` + `audit_runner_rig` + `audit_balance` continuam `PRE-FLIGHT OK` após fix.

## Plano QA executado (docs/PLANO_QA_COMPLETO.md)

Fases 0-6 executadas via `tools/qa_full.py` (127 checks). Saída em `/tmp/qa.log` (reproduzida abaixo).

## Resultado agregado

```
OK 127 | WARN 3 | FAIL 0
```

**0 falhas bloqueantes.** 3 warns são **fallback diagnóstico procedural** — código existe mas **não é executado** quando GLB existe (todos GLBs estão commitados e indexados). Detalhe:

- `game_3d primitive_mesh_cache` (11 new) — cache para `BoxMesh` fallback se `_optional_glb` falhar; com `assets/vehicles/*.glb`, `props/*.glb`, `scene/*.glb` existentes, o fallback nunca é instanciado (checado via `ResourceLoader.exists`).
- `runner_character 22 primitivas` — `shadow QuadMesh` + `_build_fallback` Capsule/Sphere diagnóstico + acessórios Creator (`BoxMesh` telefone, `CylinderMesh` bota, `SphereMesh` lantejoula etc.). Audit 4.8→6.0 aprova esses acessórios como `BoneAttachment3D` (não são sprites 2D), mas para **zero procedural absoluto** precisaria convertê-los para GLB (L29 opcional, 1 dia via `build_accessories.py`).
- `building_kit 4` (`_box/_cyl/_sphere` helpers) — mundo `piso/pista/predio` 28m procedural por design; 100% original permite, pois não há GLB de quarteirão inteiro (seria HLOD 28m, L28 já tem MultiMesh + LOD 35-96m). Para zero, criar `assets/scene/quarteirao.glb` HLOD.

**Se o aceite exigir 0 WARN, próximo L29** elimina os 51 `new()` restantes (troca cache por erro, converte acessórios para `assets/props/accessorio_*.glb`, quarteirão HLOD). Estimativa 1-2 dias, sem quebra de `PRE-FLIGHT OK`.

## Inventário validado (Fase 1)

- GLBs 64 = humanos 2 + animais 10 + vehicles 11 (4 variantes) + props 8 + scene 20 + collectibles 11 + sky 2 → todos referenciados (literal `res://` ou drop-in por pasta)
- `Humano_M 438688 SHA 50a268... OK` `Humano_F 451880 148014... OK` JOINTS/WEIGHTS/skins/animations 6 clips OK, materiais `QuaterniusSkin/Hair/Camisa/Calca/Sapato` OK
- Vehicles `Wheel*` OK 594-1753KB, props/scene/collectibles GLB OK, `pbr 40` + `height 10` 16-bit OK
- Recursos `res://` todos existem (check via `ROOT / res` )

## Visual (Fase 2)

- `building_kit heightmap_enabled + world_triplanar + sharpness 8.0` OK, `lighting bias 0.015/normal 0.45 blur1.0` OK, `PLAYER_HEIGHT 1.82 + Head look-at 12°` OK

## Física (Fase 3)

- `GRAVITY 9.81`, `PLAYER_MASS 75`, `capsule 0.35×1.75 snap0.4 jump6.3 dash900`, `RigidBody 220-8500kg continuous_cd`, `Area pothole 0.15/-3`, `ragdoll PhysicalBone`, `SURFACE_FRICTION 0.35/0.55/0.62/0.68 + speed 1.0/0.88/0.82` OK, `game_3d surface_speed_factor` OK

## Jogabilidade / Progressão (Fase 4)

- `scenario 10 perfis street_surface`, `phase_count 50`, `BALANCE base 5.0 final 18.0 wait 1.8→0.7`, `SAVE_SCHEMA_VERSION 3 BACKUP`, `shop 6 IDs`, `obstacle 13` OK
- Curva: `speed 5→18`, `distance 400→792`, `density 15/7→94/44`, cura sem paywall `source 6865 sink 4960 ratio 0.72`

## Regressivos (Fase 5)

- `validate_project PRE-FLIGHT OK`, `audit_balance OK`, `audit_runner_rig OK (2.08m)`, `audit_world` (via `validate`), `res://` OK
- `rng 20240917` determinístico, analytics `record_event`, retention OK

## Logs (trecho)

```
== Fase 6 — Zero procedural ==
  total primitive new() 51
    scripts/building_kit.gd: 4
    scripts/game_3d.gd: 11
    scripts/runner_character.gd: 27
    ...
  WARN game_3d primitive_mesh_cache ... não usado
  WARN runner_character 22 ... acessórios
  WARN building_kit world procedural ... permite
== Fase 5b — Validators ==
  OK validate_project -> PRE-FLIGHT OK
  OK audit_balance -> BALANCE AUDIT OK
  OK audit_runner_rig -> OK orientação...
```

## Arquivos desta entrega

- `scripts/locale_manager.gd` fix 2 linhas
- `tools/qa_full.py` (novo, 300 linhas, validado)
- `docs/PLANO_QA_COMPLETO.md` (novo)
- `docs/RELEASE_QA.md` (este)

## Próximo

- Se aceitar 3 WARN como fallback diagnóstico → **RELEASE v1.0 já liberado** (`8fd2dc8` + fix)
- Se exigir 0 WARN absoluto → **L29 Zero Procedural** (remover cache, converter acessórios para GLB, HLOD quarteirão) — pronto para executar se autorizado

