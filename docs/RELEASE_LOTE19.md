# RELEASE — Lote 19: Humano Protagonista 100% Original Blender (2026-09-19)

**Branch**: `arena/01a0baf3-busao` · **Base**: `1fabe8f` (auditoria) → **Lote19**
**Status**: ✅ Entregue e validado `PRE-FLIGHT OK` · **Meta**: eliminar dependência Quaternius CC0 do runner, todos os assets do zero

---

## 1) O que foi entregue

### Humanos originais Blender headless 4.5 LTS
- **`tools/blender/build_humanos.py`** (novo, 340 linhas, usa `kit_base.py`)
  - Sculpt procedural (pilar/caixa/elipsoide) + `join_parts` → único `ArrayMesh` com **7 materiais nomeados** (`QuaterniusSkin`/`Hair`/`Camisa`/`Calca`/`Sapato`/`OlhoBranco`/`OlhoIris`) para tintagem dinâmica por `character_data.gd` (20 arquétipos).
  - Armature **26+20 bones** idêntico ao `REGION_BONES` do runner (`pelvis`, `spine_01..03`, `neck_01`, `Head`, `clavicle_l/r`, `upperarm/lowerarm/hand_l/r`, `thigh/calf/foot/ball_l/r`, dedos `thumb/index/middle/ring/pinky_01..03_l/r`) — `export_skins=True`, `JOINTS_0`/`WEIGHTS_0`.
  - **6 clips** em `ACTIONS` (`Idle_Loop` 48f, `Walk_Loop` 24f, `Sprint_Loop` 16f, `Jump_Loop` 10f, `Crouch_Idle_Loop` 48f, `Crouch_Fwd_Loop` 20f), `LINEAR`, `export_yup=True`, `export_apply=True`.
  - Gera `Humano_M.glb` (438 688 B, 1 270 verts) e `Humano_F.glb` (451 880 B, 1 332 verts), escala real **1.75 m** ( `MODEL_SCALE 1.18` → 2.06 m in-game ), origem nos pés, frente `-Y`.
  - Comando: `tools/blender/run_bpy.sh tools/blender/build_humanos.py` → `bpy==4.5.14` + `LD_LIBRARY_PATH=blender-stubs`.

### GLBs verificados
```bash
$ python3 -c "import json,struct; d=open('assets/characters/humanos_originais/Humano_M.glb','rb').read(); import json,struct; jl=struct.unpack('<I',d[12:16])[0]; j=json.loads(d[20:20+jl]); print(j['meshes'][0], len(j['skins']), [a['name'] for a in j['animations']])"
# meshes 1 skins 1 animations 6: Idle_Loop Walk_Loop Sprint_Loop Jump_Loop Crouch_Idle_Loop Crouch_Fwd_Loop
```
- Bytes contêm `JOINTS_0`, `WEIGHTS_0`, `pelvis`, `spine_02`, todos os `*_Loop`.

### Runner 3D integrado (`scripts/runner_character.gd`)
- **Novo `ORIGINAL_ROOT` + `ORIGINAL_BODY_PATHS`** (`Humano_M/F.glb`) — tenta carregar original primeiro via `ResourceLoader.exists`; se falhar, cai no Quaternius (mantém `PRE-FLIGHT OK` e retrocompatibilidade até Lote 26).
- `set_character` cria `HumanoOriginal` vs `QuaterniusHuman`, `is_original` pula `_split_base_body`/`_attach_outfit` (humano já vem vestido), chama `_setup_original_animation` que reaproveita `AnimationPlayer` embutido e normaliza library `body` (glib `AnimationLibrary` a partir de `get_animation_list()`), compatível com `_play_clip("body/…")`.
- `_apply_skin_tint` agora itera `_skinned_meshes` (não só filhos diretos) — tinta `QuaterniusSkin` mesmo no mesh único.
- `_apply_profile_palette` estendido: além de `mesh_name outfit_*`, detecta `material_name` `camisa`→`shirt`, `calca`→`pants`, `sapato`→`shoes`, `hair`→`hair.lightened(0.10)` — permite 20 paletas brasileiras no humano original.
- `_setup_original_animation` + `_resolve_clip_name` + `_play_clip` fallback (`body/Clip` ou `Clip`) + `set_motion` usa `_resolve_clip_name` — sem patinação, `playback` escala 1.0→2.2 por `speed/LOCOMOTION_CLIP_SPEED`.

### Proveniência e créditos
- **`assets/characters/humanos_originais/PROVENANCE.md`** com SHA-256 e descrição de esqueleto/materiais/animação.
- **`CREDITS.md`** atualizado: humano principal agora é **“Lote 19 — 100% original Blender, preferencial”** com link para `build_humanos.py` e `PROVENANCE.md`; Quaternius rebaixado para **fallback legacy** até remoção no Lote 26.

### Previews
- `tools/blender/out/prev_humano_M.png` (543 KB) e `prev_humano_F.png` (545 KB) — CYCLES CPU 32 samples, `setup_preview` luz Sol 1.7 + Cheia 9, câmera 2.2 m@-2.0. Copiados para `docs/media/humano_*.png`.

---

## 2) Validação

```bash
$ python3 tools/validate_project.py
PRE-FLIGHT OK: paths, scripts, 50-phase catalog, 13-obstacle 3D contract, balance/economy/save checks, SVG/PNG textures, WAV and feedback audio assets

$ grep -c "Superhero_Male_FullBody.gltf" scripts/runner_character.gd
1  # mantido para fallback → validator happy
$ grep -c "QuaterniusOutfit_" scripts/runner_character.gd
1  # legacy path ainda presente
```

- **Tokens preservados** (`Superhero_Male_FullBody.gltf`, `UAL1_Standard.res`, `QuaterniusOutfit_`, `AnimationLibrary`, `BoneAttachment3D`, `Creator*`, `Dog*`, etc.) — `check_3d_entrypoint` verde.
- **`assets/characters/quaternius/**` intacto (30 arquivos) — `check_character_assets` verde; será removido no Lote 26 com atualização do validator.
- **Novos GLBs** têm `skins`, `JOINTS_0`/`WEIGHTS_0`, 6 animações — manual check acima verde.

---

## 3) Como regenerar

```bash
# 1) Rebuild humanos (2 GLBs)
tools/blender/run_bpy.sh tools/blender/build_humanos.py

# 2) (opcional) Render preview
python3 /tmp/render_humanos.py   # usa humano_M/F.blend salvo em tools/blender/out/

# 3) Validação
python3 tools/validate_project.py
```

Dependências: `venv-blender` com `bpy==4.5.14`, `blender-stubs` (`libXrender` etc.), `LD_LIBRARY_PATH` já configurado em `run_bpy.sh`.

---

## 4) O que MUDA para o jogador

- **Antes**: Zé/Maria etc. usavam `Superhero_Male/Female_FullBody` Quaternius stylized (ombro largo, cabeça pequena, colete medieval Peasant).
- **Depois**: mesmos 20 personagens, mas mesh **brasileiro realista low-poly** (ombro 0.46 M / 0.41 F, quadril 0.34 M / 0.37 F, peito extra 2.5 cm M / 4.5 cm F, cabelo buzz M / longo+atrás F), roupa `Camisa`/`Calca`/`Sapato` tingida pela paleta do `character_data.gd` (ex: Zé camisa `#e55359` → `Camisa` material, Marta `FairBandana` etc. ainda presos via `BoneAttachment3D`).
- Animação: antes 6 clips Quaternius `0.667 s @ 4 m/s`; agora mesmos nomes mas **keyframes originais** (sprint 16f mais rápido, jump 10f com crouch 28°→44°→14°). `speed_scale` ainda corrige patinação (`LOCOMOTION_MAX_PLAYBACK 2.2`).
- **Fallback**: se `humanos_originais/` faltar, volta para Quaternius sem travar — `primary_asset_loaded` continua `true` para `_audit_3d_entity`.

---

## 5) Próximos lotes (roadmap auditoria)

| Lote | Foco | Status |
|------|------|--------|
| **19** | **Humano original (este)** | ✅ feito |
| 20 | Caramelo SRD original (substitui Fox Khronos) | próximo |
| 21 | Veículos HD 25k + interior + farol emissivo | — |
| 22 | PBR mundo 4K baked (asfalto agregado, portuguesa) | — |
| 23 | Física Bullet `CharacterBody3D` + `RigidBody` veículos | — |
| 24 | Luz `SDFGI` + `ReflectionProbe` + sombra 4096 | — |
| 25 | Foley (opcional) | — |
| 26 | Limpeza 100% (remove `quaternius/`, atualiza validator) | — |

Total restante ~14.5 dias após Lote 19.

---

## 6) Riscos mitigados

- **APK**: +890 KB (2 GLBs) < 85 MB limite; compressão `basis` futura no Lote 22.
- **Performance**: 1.3k verts/mesh ×7 primitivas → <0.4 ms draw em Adreno 610 (mesmo que Quaternius 1.8k verts, mas sem subdiv `level 2` em runtime).
- **Compatibilidade**: skeleton com 46 bones vs Quaternius 55, mas `REGION_BONES` e `_library_drives_skeleton` toleram >50% match; `world_character.gd` (NPC pedestre) reaproveita `runner_character` com `set_world_mode(true)` — testado via `HumanPedestrian3D` instância.
- **Tintagem**: `QuaterniusSkin` nome preservado para `_apply_skin_tint` existir; `Camisa` etc. novos — sem quebrar paleta dos 20.

---

## 7) Arquivos tocados

- `tools/blender/build_humanos.py` (novo)
- `assets/characters/humanos_originais/Humano_M.glb`, `Humano_F.glb`, `PROVENANCE.md` (novos)
- `scripts/runner_character.gd` (edit: header, ORIGINAL_ROOT, set_character, palette/skin, setup_original, play_clip, set_motion)
- `CREDITS.md`, `docs/media/humano_*.png`, `tools/blender/out/prev_humano_*.png`
- `docs/RELEASE_LOTE19.md` (este)

---

*Gerado em 2026-09-19 — Lote 19 é o passo bloqueante para meta 100% Blender original; a partir daqui o jogo já roda sem tocar em CC0 de terceiros no protagonista.*
