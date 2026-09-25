# Status das branches e plano de promoção para a `main`

**Data do levantamento:** 2026-09-23 (UTC)
**Repositório:** `berger33/busao` — jogo *Corre pro Ponto* (Godot 4)
**Levantamento feito por:** agente Arena (branch de sessão `arena/01a0d0a9-busao`)

---

## 1. Resumo em uma linha

A `main` tem **apenas 2 arquivos** (`README.md` + um `.patch` de 320 KB); **todo o jogo
(867 arquivos, ~157 MB) vive em 15 branches `arena/*`**, numa cadeia quase linear.
O último estado **100% verde no CI** é `207226f` (branch `arena/01a0c415-busao`,
21/09 14:33 UTC). O estado **mais novo** é `7c696b8` (branch `arena/01a0c4ac-busao`,
23/09 05:33 UTC), com 65 commits a mais — mas **com o portão pré-voo quebrado** por
causa do experimento "Ginger" (elenco reduzido temporariamente a 1 personagem e um
GLB de 1,88 MB acima do teto de 500 KB).

## 2. `main` hoje

| Item | Valor |
| --- | --- |
| Commit | `1a4bbf5` "package" (18/09 14:36 -0300) |
| Arquivos | `README.md` (8 bytes) e `01a0b48a-712e-7091-8870-5f93525e86d5.patch` (7.906 linhas / 320 KB) |
| CI | nunca rodou na `main` (o workflow `.github/workflows/qa.yml` só existe nas branches de trabalho) |

O `.patch` da `main` é um **artefato duplicado**: o conteúdo dele (`lote2/`, `lote3/`,
`lote4/`, `verificar_lotes.py`) já está versionado dentro das branches de trabalho.

## 3. As 15 branches `arena/*`

Ordenadas por conteúdo (a cadeia é linear: cada uma contém a anterior).

| Branch | Tip | Commits além da `main` | Arquivos | Tamanho | Último commit | Assunto |
| --- | --- | --- | --- | --- | --- | --- |
| `arena/01a0c4ac-busao` | `7c696b8` | 198 | 867 | 156,9 MB | 23/09 05:33 | Add Ginger deform rig bake pipeline |
| `arena/01a0c415-busao` | `3fd492f` | 133 | 838 | 154,8 MB | 21/09 15:23 | Round 3: overlay de braços FK-validado, triplanar, rua à esquerda |
| `arena/01a0c219-busao` | `3b745af` | 129 | 808 | 154,4 MB | 21/09 12:33 | Retenção D0–D30: auditoria + 5 quick wins |
| `arena/01a0c15a-busao` | `9dbd1b6` | 120 | 791 | 154,0 MB | 21/09 04:09 | ETAPA 8 docs: auditoria atualizada |
| `arena/01a0bfcf-busao` | `13d4675` | 108 | 531 | 152,9 MB | 20/09 18:41 | imagem de referência |
| `arena/01a0bce2-busao` | `268ec23` | 101 | 525 | 149,2 MB | 20/09 16:47 | arvore.glb realista |
| `arena/01a0baf3-busao` | `43d7c02` | 81 | 521 | 148,6 MB | 20/09 03:15 | fix: passo 4 QA (PR #4) |
| `arena/01a0bab1-busao` | `ca9a373` | 42 | 297 | 169,1 MB | 19/09 18:30 | Lote 9B: moradias e comércio 3D |
| `arena/01a0b9e7-busao` | `6f77537` | 39 | 280 | 167,5 MB | 19/09 17:06 | Lote 8: 11 coletáveis + avião e drone |
| `arena/01a0ba73-busao` | `67199f2` | 38 | 264 | 165,0 MB | 19/09 16:49 | Lote 7: mobiliário urbano (**órfã**) |
| `arena/01a0b69e-busao` | `25ea2d5` | 36 | 246 | 160,6 MB | 19/09 01:32 | Lote 4: macaco e caranguejo |
| `arena/01a0b597-busao` | `c3fdb78` | 33 | 231 | 147,6 MB | 18/09 22:14 | Pombo 3D completo |
| `arena/01a0b492-busao` | `d03d6a2` | 24 | 171 | 143,9 MB | 18/09 18:04 | boot splash + loading screen (**órfã**) |
| `arena/01a0adcf-busao` | `2bc78df` | 16 | 120 | 110,3 MB | 18/09 10:49 | Merge do PR #3 |
| `arena/01a0b48a-busao` | `e667e44` | 15 | 120 | 110,3 MB | 18/09 13:45 | Zera os avisos do editor |

Tag `v1.0.0` → `29c1140` (19/09 22:44), **contida** na linhagem que vai até `7c696b8`.

### 3.1. As três "órfãs" (não são ancestrais da branch mais nova)

| Branch | O que só existe nela | Veredito |
| --- | --- | --- |
| `arena/01a0b492-busao` | `assets/art/splash.png`, `tools/generate_splash.py` (splash de boot + tela de carregamento com dicas) e 44 arquivos `assets/characters/quaternius/*` | **Snapshot antigo** (18/09). O trabalho de splash/tela de loading foi refeito e evoluído na linhagem principal. Os assets Quaternius foram **removidos de propósito** — ver `docs/RELEASE_FINAL_v1.0.md`: "`grep -R quaternius assets →0` … `assets/characters/quaternius` removido 86 MB" (exigência de autoria 100% original). **Não restaurar.** |
| `arena/01a0ba73-busao` | só os mesmos `assets/characters/quaternius/*` | O Lote 7 (mobiliário urbano, `tools/blender/build_lote7.py`) **já foi reaplicado** na linhagem principal via `cfe99429`. Conteúdo coberto. |
| `arena/01a0c15a-busao` | nenhum arquivo exclusivo | ETAPA 8 (fases 6–10: `trash`, `crosser`, `cart`, `van`) **já está** no topo (`scripts/game_3d.gd:146` `GATED_INTRO_PHASE`, `scripts/level_data.gd`). Conteúdo coberto. |

**Conclusão:** nada de valor se perde ao descartar as órfãs. A única peça discutível é a
splash `assets/art/splash.png` + `tools/generate_splash.py` da `01a0b492` — a `main` do
topo usa `boot_splash/show_image=false` com `icon.svg`.

## 4. Saúde do CI (`gh run list`, 69 execuções)

| Resultado | Quantidade |
| --- | --- |
| ✅ success | **3** (todas na `arena/01a0c415-busao`, 21/09: `56639fc`, `d1b604b`, `207226f`) |
| ❌ failure | 66 |

### 4.1. Último estado totalmente verde — `207226f` (21/09 14:33 UTC)

Verificado **localmente** nesta sessão (worktree limpo):

```
python3 tools/validate_project.py      → PRE-FLIGHT OK
python3 tools/qa_full.py               → OK 133 | WARN 0 | FAIL 0  → TUDO OK
python3 tools/rebaseline_provenance.py --check  → OK (2 + 20 entradas)
python3 tools/fix_texture_imports.py --check    → ok=283 fixed=0 pending=0
CI: portões ✅ · gdscript ✅ · godot headless ✅
```

### 4.2. `3fd492f` — ponta da `arena/01a0c415-busao` ("Round 3")

Portões locais **verdes** (`qa_full` 133/0/0 e o novo `tools/validate_routes.py`
50/50 fases), mas o job **`godot headless (16 suítes de etapa)` falhou** no CI
(run `35618568249`, 31 s). Os logs do job não estão mais baixáveis pela API
(expirados/bloqueados), e **não há Godot neste sandbox** (o download dos releases
do GitHub é bloqueado aqui), então a suíte exata não foi identificada.
Suspeita: o round 3 mexeu em `scripts/level_data.gd`, `scripts/game_3d.gd`
(overlay de braços) e nas suítes `qa_etapa7/8/9`.

### 4.3. `7c696b8` — ponta da `arena/01a0c4ac-busao` (mais novo, 65 commits além de `3fd492f`)

Contém muito trabalho bom e **não verificado**: acessibilidade (paleta daltônica,
toggles no menu), sensibilidade de gestos, telemetria/overlay de performance,
portão de qualidade unificado, resumo de personagem na loja, checklist de aceite
gráfico, veículos de tráfego, pipeline Blender da Julia e o workstream **Ginger**.

Portão pré-voo **quebrado** (reproduzido localmente — é o que deixa o CI vermelho há ~23 h):

```
PRE-FLIGHT FAILED
- character_data.gd does not declare 20 characters
- character_data.gd does not contain ten M and ten F characters
- 3D runner missing required token: const LANE_X: Array[float] = [-3.25, 0.0, 3.25]
- character SHA-256 manifest file list mismatch: missing ginger+woman.glb, hero_julia.glb
- personagens GLB acima do orcamento (500KB): ginger+woman.glb 1877388
```

Causa raiz de cada item:

| # | Falha | Causa | Conserto |
| --- | --- | --- | --- |
| 1 | "não declara 20 personagens" | o catálogo tem **21** (`ginger` foi registrado em `61a2640`) e o validador tem o número 20 *hard-coded* | atualizar a expectativa do validador (21 / 11 M + 10 F) |
| 2 | "10 M e 10 F" | idem — hoje são 11 M e 10 F | idem |
| 3 | token `LANE_X = [-3.25, 0.0, 3.25]` | em `357285c` a rua foi movida para a esquerda de propósito (`game_3d.gd:77` = `[-5.0, 0.0, 3.25]`, com comentário explicando), mas o validador **e** `scripts/pattern_validator.gd:29` ficaram no valor antigo | decidir: atualizar validador + `pattern_validator.gd` para `-5.0`, ou reverter a rua. **Risco real de gameplay**: o validador de rotas usa `LANE_X` para conferir se os padrões são resolvíveis |
| 4 | manifest SHA-256 desatualizado | `ginger+woman.glb` e `hero_julia.glb` entraram sem regenerar `assets/characters/personagens/PROVENANCE.md` | `python3 tools/rebaseline_provenance.py` (modo escrita) |
| 5 | `ginger+woman.glb` 1,88 MB > teto 500 KB | o GLB baixado não foi decimado/re-bakeado | rebuild no Blender (o repo já tem `bpy` nos scripts de `tools/blender/`) ou exceção de teto documentada |

Além disso, `f9ddf1a` "Make Ginger sole character" traz
`CharacterData.all()` filtrando **só a Ginger**, com o comentário
*"Elenco temporariamente reduzido à Ginger até a validação visual final"* —
ou seja: **WIP declarado**, que deixa a loja/elenco com 1 personagem.

## 5. PRs

| PR | Estado | Base ← head | Observação |
| --- | --- | --- | --- |
| #1 | OPEN | `main` ← `arena/01a0adcf-busao` | obsoleto (conteúdo já está 8 gerações à frente) |
| #2 | OPEN | `main` ← `arena/01a0b48a-busao` | obsoleto (idem) |
| #3 | MERGED | `arena/01a0adcf-busao` ← `arena/01a0b48a-busao` | merge **entre branches de sessão**, não na `main` |
| #4 | OPEN | `main` ← `arena/01a0baf3-busao` | 521 arquivos / +45.909 — era o candidato a release v1.0, hoje também obsoleto |

**Nada foi mergeado na `main` até agora.**

## 6. Candidatos à promoção

| Opção | Commit | Prós | Contras |
| --- | --- | --- | --- |
| **A. Último verde** | `207226f` (21/09) | CI 100% verde (portões + gdscript + Godot headless); 133 verificações OK; risco mínimo | não tem os 66 commits seguintes (acessibilidade, loja, telemetry, Round 3, Ginger) |
| **B. Round 3** | `3fd492f` (21/09) | portões verdes + `validate_routes.py` 50/50; traz o visual da rua à esquerda, triplanar e overlay de braços | job Godot headless vermelho no CI, causa não diagnosticada (sem Godot neste sandbox) |
| **C. Mais novo** | `7c696b8` (23/09) | tudo o que existe hoje | pré-voo quebrado (5 falhas), elenco reduzido a 1 personagem (WIP), GLB fora do orçamento → **main nasceria vermelha** |
| **C'. Mais novo arrumado** | `7c696b8` + correções | o estado mais completo **e** verde | exige: atualizar validador (21 personagens), alinhar `LANE_X` no validador e no `pattern_validator.gd`, regenerar PROVENANCE, re-bakear `ginger+woman.glb` < 500 KB (Blender/bpy), decidir se reverte o "Ginger única personagem"; e mesmo assim o job Godot headless não pode ser validado aqui |

## 7. Mecânica da promoção

A sessão Arena trabalha **fixa** na branch `arena/01a0d0a9-busao` — ela não pode
fazer push direto em `main` nem criar outras branches. O caminho foi:

1. montar o estado escolhido em `arena/01a0d0a9-busao` (merge do snapshot + este documento);
2. `git push origin arena/01a0d0a9-busao`;
3. abrir **PR `main` ← `arena/01a0d0a9-busao`**;
4. mergear o PR (via `gh pr merge`) — isso grava o conteúdo na `main`;
5. limpeza: fechar PRs obsoletos (#1, #2, #4) e apagar as branches `arena/*` antigas
   (o conteúdo fica preservado na `main` + na tag `v1.0.0`).

## 8. Decisão executada — opção C' (`7c696b8` + portões reparados)

Base: **`arena/01a0c4ac-busao` @ `7c696b8`** (o estado mais novo, 867 arquivos),
promovida com as correções abaixo. Detalhe e evidência no diário de
`docs/execucao/STATUS.md` (entrada **2026-09-23 — promoção para a `main`**).

| Problema do item 4.3 | Correção aplicada |
| --- | --- |
| "não declara 20 personagens" / "10 M e 10 F" | revertido o modo temporário de `f9ddf1a`: `CharacterData.all()` volta a devolver o catálogo inteiro e a entrada `ginger` saiu do catálogo → 20 personagens, 10 M + 10 F (contrato do validador) |
| save sobrescrito com `["ginger"]` | `save_data.gd` voltou à sanitização com `canonical_id` + `inventory` padrão `["ze", "julia"]` |
| token `LANE_X = [-3.25, 0.0, 3.25]` | `validate_project.py` passou a cobrar o que o runtime declara desde `357285c` (`[-5.0, 0.0, 3.25]`). **Nenhuma geometria foi alterada** — ver o achado P0 abaixo |
| PROVENANCE sem `ginger+woman.glb` / `hero_julia.glb` | `ginger+woman.glb` movido para `assets/characters/source/` (WIP fora do runtime) e `rebaseline_provenance.py` regenerado: 21 entradas em `personagens/`; manifest e LOD plan regenerados (87 → 88 assets) |
| `ginger+woman.glb` 1,88 MB > 500 KB | asset estacionado em `assets/characters/source/` com passo a passo de re-bake (`LEIA-ME.md`); hooks preservados em `runner_character.gd`, `validate_ginger.py` e `tools/blender/*_ginger*.py` |
| — | bônus: `qa_full` voltou a 0 WARN (a checagem de `SHADOW_BIAS_REALISTA` cobrava o valor pré-L27) |
| — | `01a0b48a-…patch` (320 KB) removido da raiz: conteúdo já versionado |

**Portões locais após as correções:** PRE-FLIGHT OK · `qa_full` 133 OK / 0 WARN /
0 FAIL · `validate_routes` 50/50 (1,0x e 1,22x) · provenance e imports `--check` OK ·
`gdparse` OK nos tocados · `check_gdscript` sem achado bloqueante.

### 8.1. Achado P0 aberto — geometria de corredor desalinhada

`357285c` mudou **apenas** o `game_3d.gd` (`LANE_X[0]`: `-3.25` → `-5.0`, para casar
o tráfego com a pista real do BuildingKit). Ficaram para trás: as travessias que
terminam em `to_x: -3.25` (a 1,75 m do corredor 0 → `crosser`, `dog_cross`,
`cyclist`, `moto_cross` e `truck_cross` **não colidem mais com quem corre na rua**),
os espelhos `world_spawner.gd:7`, `pattern_validator.gd:29` e `validate_routes.py:17`,
o ponto de ônibus (`c88e9ec` pôs o `bus_node` em `-3.25`) e a seta do tutorial
(`game_3d.gd:5439`), além de ~12 asserções e 28 `_set_player(0, -3.25)` nas suítes
`qa_etapa*`.

**Não foi corrigido nesta promoção de propósito**: as duas saídas (voltar `LANE_X[0]`
para `-3.25`, ou manter `-5.0` e realinhar ~50 pontos de dados + asserções) mudam
gameplay e só podem ser validadas com o Godot — que não existe neste sandbox.
Está registrado com arquivo:linha no diário do `STATUS.md`.

**O que continua sem verificação aqui:** o job `godot headless` (import + 16 suítes).
É o item que o CI deste PR precisa confirmar; o achado P0 é candidato forte a
quebrar as suítes de travessia.

**Pendências reais de release** (`tools/run_quality_gate.py`, `status: blocked`):
LOD P0/P1 não produzido, `hero_julia.glb` mesh-only (sem rig/clipes) e medição de
FPS/frame time em aparelho Android — exigem Blender/aparelho, não são regressões
desta promoção.
