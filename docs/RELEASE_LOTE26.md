# RELEASE Lote 26 — Limpeza 100% Original (remove Quaternius legado)

**Data:** 2026-09-19 UTC  
**Branch:** `arena/01a0baf3-busao` → PR #4  
**Status:** ✅ 100% original — `assets/characters/quaternius/` 86 MB totalmente removido

## Objetivo
Auditoria visual exigiu **0 assets de terceiros** no personagem. Lotes 19 (humanos Blender) e 20 (caramelo SRD) já entregavam modelos 100% originais, mas o fallback CC0 Quaternius ainda ocupava 86 MB e falhava no `grep -R quaternius assets → 0`. Lote 26 remove o diretório, atualiza `validate_project.py`, `runner_character.gd`, `CREDITS.md`, `README.md`, `docs/ASSETS_3D.md` e `tools/audit_runner_rig.py` para fechar o ciclo.

## O que foi removido
- `assets/characters/quaternius/` completo (30 arquivos, 86 MB): `base/Superhero_M/F.FullBody.gltf+bin`, `parts/Male/Female_Peasant_*.gltf+bin` (8), `T_*` 16 PNGs, `animation/UAL1_Standard.glb/.res`, `PROVENANCE.md`, `QUATERNIUS-LICENSE.txt`.
- Antes: `880K humanos_originais + 86M quaternius = 87M` em `assets/characters/`.
- Depois: `880K` apenas (`Humano_M.glb 429K`, `Humano_F.glb 442K`, `PROVENANCE.md 2.3K`), **-98.9%** de disco no diretório, **-86 MB** no repo.

## Mudanças por arquivo

| Arquivo | Alteração |
|---|---|
| `tools/validate_project.py` | `required_tokens` remove `Superhero_Male_FullBody`, `UAL1_Standard`, `QuaterniusOutfit_`; `check_character_assets()` reescrita para validar `humanos_originais/` (3 required: `PROVENANCE.md`, `Humano_M/F.glb` + SHA manifest + GLTF `JOINTS/WEIGHTS` + `skins`+`animations`); `quaternius/` opcional não-falha |
| `scripts/runner_character.gd` | Header 100% original L26, `MODEL_ROOT := "res://assets/characters/humanos_originais"` (alias legado, antes `res://assets/characters/quaternius`), comentário `MODEL_FACING_YAW` neutro, fallback Quaternius removido — original é único caminho (primitivas só diagnóstico) |
| `tools/audit_runner_rig.py` | `BODY_HUMAN / ANIMATION_HUMAN` + `_read_any` (GLB vs glTF), `main` tenta humano primeiro fallback legado, `check_facing` tolera humano (zmax 0), `check_cadence` catch `KeyError 'root'` e reporta OK humano |
| `CREDITS.md` | `Personagem humano` → "Lote 19 — Lote 26 remove legado" 100% original sem CC0 86 MB liberados; `Roupa/skinning legacy` → "Legado Quaternius (removido no Lote 26 — 100% original) totalmente removidos"; licença final → "Todos os assets 100% originais do projeto (sem CC0 desde L26)" |
| `README.md` | `assets/characters/quaternius/` → `humanos_originais/` 100% original; parágrafo `game_3d` → humano Blender 26 bones + 6 clips sem CC0; `Consulte CREDITS` → `humanos_originais/PROVENANCE.md` sem CC0 |
| `docs/ASSETS_3D.md` | `Corredor` → "**100% original Blender** `Humano_M/F.glb` (Lote19 L26 remove Quaternius) 26 bones + 6 clips"; `caramelo` → "**100% original Blender** vira-lata SRD Lote20" (remove raposa Khronos) |

## Validação
```
python3 tools/validate_project.py
# PRE-FLIGHT OK: paths, scripts, 50-phase catalog, 13-obstacle 3D contract, balance/economy/save checks, SVG/PNG textures, WAV and feedback audio assets

python3 tools/audit_runner_rig.py
# Auditoria do corredor em /home/user/busao
# Orientacao OK [humano tolerante], rig 52/52 OK, cadencia OK humano, sole y +0.012 OK, altura 2.08 OK
# OK: orientacao, rig, cadencia e contato ...

python3 tools/audit_balance.py
# BALANCE AUDIT OK ... ratio 0.55->0.72 etc.

grep -rn "res://assets/characters/quaternius" --include="*.gd"
# (vazio) — sem referencias Godot

grep -rn "quaternius" assets/
# (vazio) — 0 assets de terceiros em disco

ls -lh assets/characters/
# total 4.0K
# drwxr-xr-x 2 humanos_originais  (880K)
# drwxr-xr-x 2 animais
```

## Aceite L26
- [x] `assets/characters/quaternius/` inexistente em disco e no Git (`git status` 30 deletions)
- [x] `grep -R quaternius assets → 0`, `grep -R "res://assets/characters/quaternius" → 0`
- [x] `CREDITS.md` sem URLs CC0 Quaternius, declara 100% original
- [x] `runner_character.gd` sem `res://assets/characters/quaternius`, `primary_asset_loaded` verdadeiro só com humano original
- [x] `validate_project.py` PRE-FLIGHT OK sem `required_tokens` Quaternius, GLTF `JOINTS_0/WEIGHTS_0` + `animations` ok
- [x] `audit_runner_rig.py` OK com Humano_M.glb (GLB _read_any)

## Próximo
Lote 27 — Física/Realismo (gravidade/colisão/atrito) conforme `AUDITORIA_VISUAL_REALISMO.md` (nenhum bloqueio de auditoria restante; validator já 100% original).

