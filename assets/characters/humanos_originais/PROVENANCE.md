# Proveniência — Humanos Originais (Lote 19)

Personagens humanos 100% originais, modelados do zero no **Blender 4.5 LTS headless** via `tools/blender/build_humanos.py`. Não utilizam nenhum mesh, textura ou animação de terceiros (CC0). Substitui o fallback Quaternius como caminho preferencial do `runner_character.gd`.

## Geração

- **Script:** `tools/blender/build_humanos.py` (usa `kit_base.py`: loft não usado, pilar/caixa/elipsoide, armature, skin weight 1.0 por parte, 6 actions).
- **Comando:** `tools/blender/run_bpy.sh tools/blender/build_humanos.py`
- **Saída:** `Humano_M.glb` (M, 356040 bytes) e `Humano_F.glb` (F, 361036 bytes), escala real ~1.75 m (antes de MODEL_SCALE 1.18 → ~2.06 m in-game), origem nos pés (Z=0), frente = -Y, `export_yup=True`. Regenerado Blender 5.0.1 + bevel 0.012 / seg24 / ico3 / shade_smooth (2026-09-20).
- **Esqueleto:** 26 bones principais + 20 dedos (`pelvis`, `spine_01/02/03`, `neck_01`, `Head`, `clavicle_l/r`, `upperarm_l/r`, `lowerarm_l/r`, `hand_l/r`, `thigh_l/r`, `calf_l/r`, `foot_l/r`, `ball_l/r`, `thumb/index/middle/ring/pinky_01..03_l/r`). Compatível com `REGION_BONES` e `_library_drives_skeleton` (>50% match).
- **Mesh:** único `ArrayMesh` com 7 primitivas (7 materiais: `QuaterniusSkin`, `Hair`, `Camisa`, `Calca`, `Sapato`, `OlhoBranco`, `OlhoIris`), ~1270–1332 vértices, `JOINTS_0`/`WEIGHTS_0` por vértice, 1 `Skin` com 26+ binds.
- **Materiais:** `Principled BSDF` nomeados para tintagem dinâmica em `runner_character.gd` (`Camisa`→`shirt`, `Calca`→`pants`, `Sapato`→`shoes`, `Hair`→`hair`, `QuaterniusSkin`→pele via `_apply_skin_tint`). Tintagem preserva textura (cor sólida + roughness) e multiplica por `character_data.gd` palette (20 arquétipos brasileiros).
- **Animações:** 6 clips em `ACTIONS` mode — `Idle_Loop` (48f), `Walk_Loop` (24f), `Sprint_Loop` (16f), `Jump_Loop` (10f), `Crouch_Idle_Loop` (48f), `Crouch_Fwd_Loop` (20f), interpolação `LINEAR`, exportadas com `export_animations=True, export_skins=True`.
- **Licença:** Trabalho original do projeto Corre pro Ponto, **CC0 próprio / domínio do projeto**, sem CC0 de terceiros. Pode ser redistribuído com o jogo.

## Manifesto SHA-256

```text
6da355fefcf4bb9b160082812b84b46fa25569d997eb98567569f9d3c69e34c7  Humano_M.glb  (356040 bytes)
317b72ad9a7057f08c618ecefcb77d43f8c489f6655e3d2c62dc513700e7fca3  Humano_F.glb  (361036 bytes)
```
