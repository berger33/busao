# Proveniência — Humanos Originais (Lote 19)

Personagens humanos 100% originais, modelados do zero no **Blender 4.5 LTS headless** via `tools/blender/build_humanos.py`. Não utilizam nenhum mesh, textura ou animação de terceiros (CC0). Substitui o fallback Quaternius como caminho preferencial do `runner_character.gd`.

## Geração

- **Script:** `tools/blender/build_humanos.py` (usa `kit_base.py`: loft não usado, pilar/caixa/elipsoide, armature, skin weight 1.0 por parte, 6 actions).
- **Comando:** `tools/blender/run_bpy.sh tools/blender/build_humanos.py`
- **Saída:** `Humano_M.glb` (M, 438688 bytes) e `Humano_F.glb` (F, 451880 bytes), escala real ~1.75 m (antes de MODEL_SCALE 1.18 → ~2.06 m in-game), origem nos pés (Z=0), frente = -Y, `export_yup=True`.
- **Esqueleto:** 26 bones principais + 20 dedos (`pelvis`, `spine_01/02/03`, `neck_01`, `Head`, `clavicle_l/r`, `upperarm_l/r`, `lowerarm_l/r`, `hand_l/r`, `thigh_l/r`, `calf_l/r`, `foot_l/r`, `ball_l/r`, `thumb/index/middle/ring/pinky_01..03_l/r`). Compatível com `REGION_BONES` e `_library_drives_skeleton` (>50% match).
- **Mesh:** único `ArrayMesh` com 7 primitivas (7 materiais: `QuaterniusSkin`, `Hair`, `Camisa`, `Calca`, `Sapato`, `OlhoBranco`, `OlhoIris`), ~1270–1332 vértices, `JOINTS_0`/`WEIGHTS_0` por vértice, 1 `Skin` com 26+ binds.
- **Materiais:** `Principled BSDF` nomeados para tintagem dinâmica em `runner_character.gd` (`Camisa`→`shirt`, `Calca`→`pants`, `Sapato`→`shoes`, `Hair`→`hair`, `QuaterniusSkin`→pele via `_apply_skin_tint`). Tintagem preserva textura (cor sólida + roughness) e multiplica por `character_data.gd` palette (20 arquétipos brasileiros).
- **Animações:** 6 clips em `ACTIONS` mode — `Idle_Loop` (48f), `Walk_Loop` (24f), `Sprint_Loop` (16f), `Jump_Loop` (10f), `Crouch_Idle_Loop` (48f), `Crouch_Fwd_Loop` (20f), interpolação `LINEAR`, exportadas com `export_animations=True, export_skins=True`.
- **Licença:** Trabalho original do projeto Corre pro Ponto, **CC0 próprio / domínio do projeto**, sem CC0 de terceiros. Pode ser redistribuído com o jogo.

## Manifesto SHA-256

```text
50a2686e6f929086d8f46159821f5de92f2381ef2c2bd4f48e77b62e9528e2f0  Humano_M.glb  (438688 bytes)
148014ac9958b0f9304aace88dc250a848e0e444c8da9947633aa3cdd493ef6e  Humano_F.glb  (451880 bytes)
```
