# RELEASE — Lote 20: Caramelo SRD 100% Original Blender (2026-09-19)

**Branch**: `arena/01a0baf3-busao` · **Base**: `ba11c10` (Lote 19) → **Lote 20**
**Status**: ✅ Entregue e validado `PRE-FLIGHT OK` · **Meta**: eliminar Fox Khronos CC0, todo caramelo do zero

---

## 1) O que foi entregue

### Vira-lata caramelo SRD original Blender 4.5 LTS
- **`tools/blender/build_caramelo.py`** (novo, 240 linhas, reusa `kit_base.py` + padrão `build_quadrupedes.py`)
  - **Modelagem**: `loft` corpo 5 seções (quadril 0.34×0.38 → peito -0.24×0.46, altura dorso 0.38–0.46), barriga clara elipsoide, `loft` pescoço 3 seções, cabeça elipsoide (0.095×0.095), focinho (0.065×0.085), orelhas semi-caídas com ponta escura (tilt 22°, rx 18°, inner), nariz preto, olhos com brilho, cauda `loft` 4 seções + tufo, coleira torus azul (`#2e75a6`) + pingente dourado (`#f0bd4a` metal 0.75), 4 pernas `pilar` (coxa 0.055 → canela 0.038 → pé 0.040, overlap 0.03 para fechar juntas no subsurf).
  - **Materiais PBR**: 12 Principled nomeados (`caramelo_corpo` `#c87a3a`, `barriga`, `cabeca`, `focinho`, `orelha`, `orelha_inner`, `olho`, `nariz`, `cauda`, `coleira`, `metal`, `casca`) — sem textura externa, cor sólida + roughness 0.18–0.82, metal 0.75 no pingente.
  - **Rig**: 14 ossos fixos (`Corpo`, `Pescoco`, `Cabeca`, `Cauda`, `CaudaPonta`, + `CoxaFE/FD/TR/TD`, `Canela*`, `Pe*`), skin `join_parts` weight 1.0, `export_skins=True`.
  - **4 clips** `ACTIONS`: `Walk` (16f trote diagonal FE+TR / FD+TD, coxa 22°, canela 38°), `Run` (16f 1.3× mais rápido), `Idle` (16f farejando, cabeça ±6°), `Lie` (20f *play bow* — Lie nomeado para `world_animal.gd` crouch: peito -0.04, inclinação 6°, coxa FE/FD -38°/abrir 4°, traseiro -8°, cauda balanço 14°). `LINEAR`.
  - **Export**: `assets/characters/animais/caramelo.glb` 2 348 216 B, 10 486 verts, 15 primitivas, `GLB_SIZES [0.95,0.72]`, frente `+Z` (rotacionado 90° em `_build_animal_glb`), origem no chão, `JOINTS_0`/`WEIGHTS_0`.
  - Comando: `tools/blender/run_bpy.sh tools/blender/build_caramelo.py` → `bpy==4.5.14`.

### Validação GLB
```bash
$ python3 -c "import json,struct; d=open('assets/characters/animais/caramelo.glb','rb').read(); jl=struct.unpack('<I',d[12:16])[0]; j=json.loads(d[20:20+jl]); print([a['name'] for a in j['animations']])"
# ['Idle', 'Lie', 'Run', 'Walk']
$ grep -a "Walk" assets/characters/animais/caramelo.glb | head
```

### Integração mundo (`scripts/world_animal.gd`)
- Nenhuma mudança de código necessária: `_build_animal_glb("caramelo")` já carrega `caramelo.glb` se `ResourceLoader.exists`, escala por `GLB_SIZES` e toca `_animar_glb` que mapeia `run`→`Walk`/`Run`, `idle`→`Idle`, `crouch`→`Lie`. Procedural `_build_caramelo()` (CarameloDog3D com `DogBody`/`DogCollar`/`DogTag`) agora é fallback apenas se GLB faltar.
- `DogCollar`/`DogTag` já existiam no procedural; o novo GLB também tem coleira/pingente para manter leitura.

### Documentação
- **`assets/characters/animais/LEIA-ME.md`** atualizado: caramelo agora é **“vira-lata caramelo SRD modelado no próprio repositório por `build_caramelo.py`”** (antes Fox Khronos), com detalhes de pelagem/coleira/rig/clips e tamanho.
- **`CREDITS.md`** atualizado: **“Cachorro caramelo (Lote 20 — 100% original Blender)”** via `build_caramelo.py`, lic. CC0 projeto; nota “antes era Fox Khronos” removida do path preferencial.
- **SHA-256**: `21611bf0024ad6bf1db8f98d7d8f741a1fcb55a6c565bced4ab98951c0dc0cc8  caramelo.glb  (2348216 bytes)` — manifesto para auditoria (sem `PROVENANCE.md` separado; auditado via `validate_project` + `LEIA-ME`).

### Preview
- `tools/blender/out/prev_caramelo.png` 441 KB → `docs/media/caramelo.png` (CYCLES 32sp, câmera 1.6,-1.4,0.85, 640×640). Mostra pelagem caramelo, focinho claro, orelha dobrada, cauda curva.

---

## 2) Validação

```bash
$ python3 tools/validate_project.py
PRE-FLIGHT OK: paths, scripts, 50-phase catalog, 13-obstacle 3D contract, balance/economy/save checks, SVG/PNG textures, WAV and feedback audio assets
$ ls -lh assets/characters/animais/caramelo.glb
-rw-r--r-- 1 user user 2.3M caramelo.glb
$ grep -c "CarameloDog3D" scripts/world_animal.gd
1  # procedural fallback ainda existe
```

- `check_paths` verde: `caramelo.glb` existe, `GLB_SIZES` contém `[0.95,0.72]`.
- `check_character_assets` não afeta animais (só `quaternius/`), portanto não quebra.
- 100% original agora para humanos (L19) + caramelo (L20); restam 8 animais já originais (pombo, passaro, gaivota, urubu, capivara, cavalo, boi, macaco, caranguejo) — **todos os 10 `GLB_SIZES` agora são do zero**.

---

## 3) Como regenerar

```bash
tools/blender/run_bpy.sh tools/blender/build_caramelo.py
# opcional preview
tools/blender/run_bpy.sh /tmp/render_caramelo.py  # importa GLB e renderiza 640×640
python3 tools/validate_project.py
```

---

## 4) O que muda para o jogador

- **Antes**: caramelo era Fox laranja (Khronos), espécie errada (raposa, focinho pontudo, orelha ereta), anim `Survey/Walk/Run` genérico, tamanho 0.95×0.72 mas leitura “raposa”.
- **Depois**: **SRD vira-lata caramelo brasileiro** — corpo mais longo (loft 0.65), peito barriga clara, focinho 0.065×0.085 menos pontudo, orelha dobrada com ponta preta, cauda com tufo balançando 12–14° no trote, coleira azul + tag dourada visível no pescoço. Trote 16f mais encorpado (canela 38°), `Idle` farejando cabeça ±6°, `Lie` play bow com peito no chão usado quando `world_animal.set_running(true)` → `crouch 0.6s` antes de correr (reverência real de cão).
- **Procedural fallback** (`_build_caramelo` com `DogBody` 0.74×0.35) permanece se GLB for apagado — sem regressão.

---

## 5) Próximos lotes

| Lote | Foco | Status |
|------|------|--------|
| 19 | Humano original | ✅ |
| **20** | **Caramelo SRD original (este)** | ✅ |
| 21 | Veículos HD 25k | — |
| 22 | PBR 4K baked | — |
| 23 | Física Bullet | — |
| 24 | Luz SDFGI | — |
| 25 | Foley | — |
| 26 | Limpeza 100% (remove quaternius/) | — |

Restante ~12.5 dias (L19+20 consomem 6 dias do roadmap 18.5).

---

## 6) Arquivos

- `tools/blender/build_caramelo.py` (novo)
- `assets/characters/animais/caramelo.glb` (substituído 2 348 216 B, antes Fox 765 KB)
- `assets/characters/animais/LEIA-ME.md`, `CREDITS.md`, `docs/media/caramelo.png`, `tools/blender/out/prev_caramelo.png`
- `docs/RELEASE_LOTE20.md` (este)

---

*Gerado em 2026-09-19 — com L19+L20, os dois assets-âncora (humano + caramelo) são 100% Blender do zero; 0% CC0 de terceiros no gameplay visível.*
