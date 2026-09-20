# Proveniência — Humanos Originais (Lote 19 / Atualização Mestria Gráfica)

Personagens humanos 100% originais, modelados do zero no **Blender 4.5 LTS headless** via `tools/blender/build_humanos.py`. Não utilizam nenhum mesh, textura ou animação de terceiros (CC0). Malha orgânica contínua lofted em anéis de quads com coordenadas UV unwrapped, tênis de corrida esculpidos com sola de amortecimento EVA, proporções anatômicas naturais e compressão Draco.

## Geração

- **Script:** `tools/blender/build_humanos.py` (lofted quad rings, pernas anatômicas, tênis de corrida com sola EVA, armature de 52 ossos, 6 actions biomecânicas completas, Draco mesh compression).
- **Comando:** `tools/blender/run_bpy.sh tools/blender/build_humanos.py`
- **Saída:** `Humano_M.glb` (M, 216044 bytes) e `Humano_F.glb` (F, 216872 bytes), escala real ~1.75 m (com MODEL_SCALE 1.18 → ~2.06 m in-game), contato exato com o solo (solas em y = +0.0120 m), frente = -Y, `export_yup=True`.
- **Esqueleto:** 26 bones principais + 20 dedos (`pelvis`, `spine_01/02/03`, `neck_01`, `Head`, `clavicle_l/r`, `upperarm_l/r`, `lowerarm_l/r`, `hand_l/r`, `thigh_l/r`, `calf_l/r`, `foot_l/r`, `ball_l/r`, `thumb/index/middle/ring/pinky_01..03_l/r`). Compatível com `REGION_BONES` e `_library_drives_skeleton` (100% match).
- **Mesh:** único `ArrayMesh` com 7 primitivas (7 materiais: `QuaterniusSkin`, `Hair`, `Camisa`, `Calca`, `Sapato`, `OlhoBranco`, `OlhoIris`), JOINTS_0/WEIGHTS_0 por vértice, 1 `Skin` com 26+ binds.
- **Materiais:** `Principled BSDF` nomeados para tintagem dinâmica em `runner_character.gd` (`Camisa`→`shirt`, `Calca`→`pants`, `Sapato`→`shoes`, `Hair`→`hair`, `QuaterniusSkin`→pele via `_apply_skin_tint`).
- **Animações:** 6 clips em `ACTIONS` mode — `Idle_Loop` (48f), `Walk_Loop` (24f), `Sprint_Loop` (16f), `Jump_Loop` (12f), `Crouch_Idle_Loop` (48f), `Crouch_Fwd_Loop` (20f), interpolação `LINEAR`, exportadas com `export_animations=True, export_skins=True`.
- **Licença:** Trabalho original do projeto Corre pro Ponto, **CC0 próprio / domínio do projeto**, sem CC0 de terceiros. Pode ser redistribuído com o jogo.

## Manifesto SHA-256

```text
a40125df25a8ede85868639377e8303f165f8f33a23b296cda93e350bf733601  Humano_M.glb  (353136 bytes)
ea07f41b9b45bfaf2f5681347c29bd4a89018cbf534d446f7a678049f0ed712c  Humano_F.glb  (359544 bytes)
```


> 2026-09-20: todos regenerados **sem** Draco (`export_draco_mesh_compression_enable=False`). Godot 4 não decodifica `KHR_draco_mesh_compression` — os GLBs anteriores importavam sem geometria (personagem invisível, só a sombra). `julia.glb` vem de `tools/blender/build_corredora_fase1.py`.
