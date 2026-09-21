# STATUS — Corre pro Ponto (execução do blueprint)

Referências: `BLUEPRINT_CORRE_PRO_PONTO.md` (regras e decisões) e
`PLANO_50_FASES_CORRE_PRO_PONTO.md` (catálogo das 50 fases).

## Etapas

| Etapa | Objetivo | Estado | Evidência |
|---|---|---|---|
| 0 | Ambiente reproduzível: Godot 4.7 compilado, import limpo, smoke headless | concluída | binário 4.7.stable.custom_build.5b4e0cb0f (headless, x11=no wayland=no); `--import` com 0 erros de recurso (540 importados); suíte QA carrega `scenes/main.tscn` e roda corridas completas headless |
| 1 | Regra de prazo real (RunDirector): largada com contagem, relógio durante a corrida, impacto +2 s, ônibus parte no prazo | concluída | `tools/qa_etapa1_deadline.gd`: 9/9 verificações verdes (A–H, incluindo limite exato e pausa do relógio); `ETAPA1_QA_OK`, exit 0 |

## Diário

### 2026-09-20 (sessão original, recuperada)

- ETAPA 1 implementada por completo: RunDirector extraído de `game_3d.gd`
  (máquina de estados preparo → contagem → corrida → aproximação → embarque →
  resultado), prazo = distância/velocidade + margem do catálogo
  (`DEADLINE_MARGINS`, 50 valores transcritos do plano), penalidade de +2 s por
  impacto válido, chegada avaliada antes da expiração no mesmo frame (ordem
  determinística), contagem regressiva de 2,4 s, embarque pulável de 2 s,
  derrota com causa ("atraso" informa os metros restantes; "folego").
- HUD: cápsula "ÔNIBUS MM:SS" (vermelha abaixo de 10 s), overlay 3-2-1 na
  largada, painel de embarque, causa da derrota na tela de resultados.
- Removidos o modo `at_stop`, a espera no ponto (`stop_wait`) e o toque extra
  "PEGAR O BUSÃO" (blueprint §2: sem toque perfeito no último quadro).
- Endless preserva o comportamento antigo (sem prazo).

### 2026-09-21 (recuperação após falha da conversa/sandbox)

- O sandbox anterior foi perdido sem commit do trabalho da ETAPA 1. A branch
  da sessão anterior (`arena/01a0bfcf-busao`, commit `13d4675`) foi recuperada
  via merge nesta branch (`arena/01a0c15a-busao`).
- ETAPA 1 re-aplicada a partir do design da sessão anterior: 21 substituições
  exatas em `game_3d.gd` + 5 em `hud_3d.gd`, aplicadas em escrita atômica única
  (política adotada depois que uma edição incremental corrompeu `game_3d.gd`
  com bytes NUL na sessão anterior).
- `check_gdscript.py --godot-doc` (analisador do repo): 0 problemas novos;
  os 42 restantes são pré-existentes em áreas não tocadas.
- `julia.glb` voltou com Draco no commit `84da362` (posterior ao fix `1a04edf`);
  Godot 4.7 não decodifica KHR_draco_mesh_compression → re-export sem Draco
  via bpy (mesma correção da sessão anterior).
- Ambiente: sem X11/Wayland neste sandbox → binário Godot compilado com
  `x11=no wayland=no` (headless puro; suficiente para import + QA).
- Import limpo: `--import` exit 0, 540 recursos; `.import` regenerados em
  formato 4.7 (commitado). julia.glb sem Draco importou normalmente.
- QA ETAPA 1 (21/09, 01:17 UTC): 9/9 verificações verdes — chegada adiantada,
  chegada no limite exato do prazo (chegada antes da expiração), chegada
  atrasada, expiração no meio do caminho com metros restantes, fôlego zerado,
  relógio andando na corrida, relógio suspenso na pausa, +2 s por impacto e
  prazo da fase 0 = 94,0 s (400 m / 5 m/s + 14 s de margem).

## Regras de engenharia desta execução

- Uma etapa por vez; cada etapa fecha com demonstração reproduzível
  (QA headless) antes da próxima.
- Edições grandes em escrita atômica com contagem assertiva de ocorrências.
- Nenhuma conclusão normal exige personagem específico; habilidades atuais
  serão normalizadas em M5 (pendência registrada no blueprint).
