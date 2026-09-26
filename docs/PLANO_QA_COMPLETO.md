# Plano de QA Completo — Corre pro Ponto v1.0

**Data:** 2026-09-19 UTC  
**Branch:** `arena/01a0baf3-busao` @ `8fd2dc8` + L27 `798a633` + L28 `f6e938f`  
**Solicitante:** teste de qualidade completo (visual, física, jogabilidade, progressão, dificuldade, regressivo, analítico) + garantir **zero procedural** + corrigir `replace() 3 args` linhas 123/141

---

## Fase 0 — Correções críticas (bloqueante)
- [x] `scripts/locale_manager.gd:123` `replace("%s",…,false)` → 2 args
- [x] `scripts/locale_manager.gd:141` `replace("%d",…,false)` → 2 args
- Verificar `grep -rn "\.replace("` em todos GDs, garantir ≤2 args
- `python3 tools/validate_project.py` + `audit_runner_rig` + `audit_balance` verdes

## Fase 1 — Inventário & indexação (garantir tudo conectado)
- Enumerar `assets/**` (GLB 2 humanos + 10 animais + 11 veículos + 4 variantes + 8 props + 14 scene + 11 collectibles + 2 sky + 95 PNG + 27 WAV)
- Checar cada GLB é referenciado: `res://assets/...` em GDs, `world_spec.json` materiais, `obstacle_data 13`, `shop_data 6`, `character_data 20`, `scenario_data street_surface`
- Validar `GLTF JOINTS_0/WEIGHTS_0 + skins + animations` para skinned, `buffers/images` existem, `SHAs` em PROVENANCE
- `ResourceLoader.exists` para cada `res://` em `project.godot`, `export_presets.cfg`, `localization`

## Fase 2 — Visual (modelagem/textura/iluminação/escala)
- **Modelagem:** humano 12k tris 2.08m, caramelo 8k, veículos 25k, props/scene low→HD, árvores impostor 2 tris, checar `MODEL_SCALE 1.18`, `PLAYER_HEIGHT 1.82`
- **Textura:** PBR 4K `albedo+normal+orm+height16` 44M, `heightmap_scale 0.025` + `triplanar 8.0` ativo, `anisotropic`, sem tiling a 1m, `detail`?
- **Iluminação:** SDFGI/VoxelGI 28m + Probe128, VSM4096 `bias 0.015/normal 0.45 blur1.0`, SSAO/SSIL 0.4, PhysicalSky, VolumetricFog 0.012
- **Sombreamento:** `cast_shadow ON` em `_skinned_meshes`, `receive_shadows` via material, `blob_shadow Quad α0.30` + VSM, checar `peter-panning`
- **Escala:** `LANE_X [-3.25,0,3.25]` 6.6m pista + 6+2.5m calcada, porta 1.6×2.4, ônibus 7.4m vs real 12m

## Fase 3 — Física (gravidade/colisão/atrito/inércia)
- `PhysicsHandler` `GRAVITY 9.81`, `PLAYER_MASS 75`, `capsule 0.35×1.75`, `snap 0.4`, `jump 6.3`, `dash 900`, `pothole 0.15/-3`, `vehicle 220-8500kg`, `surface 0.35/0.55/0.62/0.68` + `speed 1.0/0.88/0.82`
- `CharacterBody3D move_and_slide + is_on_floor`, `RigidBody continuous_cd`, `Area pothole`, `StaticBody props`, `PhysicalBone ragdoll`
- Testar salto parábola 1.28s, truck empurra car, `hearts` só fora de `dash/invencível`, `head clearance raycast` crouch

## Fase 4 — Jogabilidade / Progressão / Dificuldade
- 50 fases `phase_data` + `world_spec_orcamento`, `BALANCE` `base 5.0→18.0`, `wait 1.8→0.7`, `phase_speed_for`, `phase_wait_for`, `record_phase_result`
- Curva: `speed 5→8.3→12→16→18`, `distance 400→792`, `density 15/7→94/44`, `coins 4/29→46/59`, `gates 45/120/150`
- `GameSave` `SAVE_SCHEMA_VERSION 3` `BACKUP_PATH/TEMP_PATH/DirAccess.rename`, `retention_flags`, `weekly_distance_target`, `autosave 7s`
- `shop_data` 6 IDs `tenis/mochila/fone/cafe/confete/placa` + 2 cosmetics, `EconomyHandler`, `AdsHandler` mock

## Fase 5 — Testes regressivos & analíticos
- `validate_project PRE-FLIGHT OK`, `audit_balance OK`, `audit_runner_rig OK`, `audit_world`, `check_gdscript` (gdtoolkit), `grep res://` exists
- RNG determinístico `20240917`, `seed 20260918` texturas, `record_event` analytics, `retention`
- `QA device farm` `cold_start <2.8s`, `shadow 1024→4096`, `HLOD MultiMesh`, `Basis KTX2 AAB 31.3≤85`

## Fase 6 — Zero procedural (garantia)
- `grep -rn "BoxMesh\|SphereMesh\|CylinderMesh\|CapsuleMesh\|QuadMesh"` → deve ser **0 fora de fallback diagnóstico** (`_build_fallback`, `runner_shadow`, `building_kit piso/pista/predio` procedural vs GLB drop-in)
- Para cada `_prop_glb`, `_optional_glb`, `world_animal _modelo_animal_opcional`, garantir GLB existe: `assets/props 8/8`, `scene 14/14`, `vehicles 11+4`, `collectibles 11/11`, `animais 10/10`, `humanos 2/2`
- Se GLB existe, código não instância primitiva; primitiva só em `fallback` quando `ResourceLoader.exists==false` → deve ser inatingível com assets commitados

## Fase 7 — Correções & revalidação
- Listar falhas → patch → `validate` + `audit` + `rg` de novo → commit `QA-FIX` → `RELEASE_QA.md` + `git push` PR #4

---

**Execução nesta sessão:** fases 0-5 já iniciadas (replace fix + validate OK); fases 1-6 em `tools/qa_full.py` abaixo, resultado em `docs/RELEASE_QA.md`.
