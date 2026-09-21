# STATUS — Corre pro Ponto (execução do blueprint)

Referências: `BLUEPRINT_CORRE_PRO_PONTO.md` (regras e decisões) e
`PLANO_50_FASES_CORRE_PRO_PONTO.md` (catálogo das 50 fases).

## Etapas

| Etapa | Objetivo | Estado | Evidência |
|---|---|---|---|
| 0 | Ambiente reproduzível: Godot 4.7 compilado, import limpo, smoke headless | concluída | binário 4.7.stable.custom_build.5b4e0cb0f (headless, x11=no wayland=no); `--import` com 0 erros de recurso (540 importados); suíte QA carrega `scenes/main.tscn` e roda corridas completas headless |
| 1 | Regra de prazo real (RunDirector): largada com contagem, relógio durante a corrida, impacto +2 s, ônibus parte no prazo | concluída | `tools/qa_etapa1_deadline.gd`: 9/9 verificações verdes (A–H, incluindo limite exato e pausa do relógio); `ETAPA1_QA_OK`, exit 0 |
| 2 | Controle preciso e colisões compreensíveis (blueprint §4/§6): matriz ação x família por classe de altura/volume, colisão pela posição real, buffer de entrada, dash sem imunidade | concluída | `tools/qa_etapa2_colisao.gd`: 10/10 verificações verdes (A–J); suíte da etapa 1 segue 9/9 (sem regressão) |

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
- ETAPA 2 (21/09): `scripts/obstacle_rules.gd` — classes LOW / GROUND / FULL /
  VEHICLE / SOFT / SLIDE_UNDER com ações válidas próprias (blueprint §4/§6):
  pulo não atravessa ônibus/caminhão/carro; deslize não resolve banco,
  hidrante, orelhão ou bicicleta; pessoas e animais produzem esbarrão
  (lentidão de 0,8 s) sem dano; dash deixa de conceder imunidade (vira
  explosão curta de velocidade, como no §4 "após núcleo validado").
- Colisão agora usa a posição real da personagem (inclusive no meio da troca
  de corredor), com largura de colisão por família; coletáveis seguem por
  corredor/ímã. Um impacto segue pontuando uma vez por entidade
  (`passed`) e a invulnerabilidade de 1,15 s impede cascata.
- Buffer de entrada de 0,12 s de simulação para pulo/deslize (independe do
  fps; limpo na pausa — nenhuma ação no retorno, como pede o blueprint).
  Duração do deslize já estava na faixa proposta (0,72 s); troca de corredor
  já converge em ~0,2 s com o lerp atual.
- QA etapa 2 (10/10): desvio limpo com pulo (cone/buraco), dano quando a ação
  não resolve (deslize no banco, pulo no ônibus), posição real decide na troca
  de corredor, esbarrão sem dano, dash sem imunidade, buffer executado na
  aterrissagem e determinismo. Suíte da etapa 1 re-rodou 9/9 (sem regressão).
- Classe SLIDE_UNDER (barreira suspensa/andaime) já existe na matriz, à espera
  dos IDs de obra/toldo do lote de assets (próxima frente de conteúdo).
- Cachorro Caramelo: a perseguição de 10 s agora só começa no esbarrão;
  pular/desviar do cachorro é desvio limpo (antes a perseguição começava em
  qualquer encontro).

## Regras de engenharia desta execução

- Uma etapa por vez; cada etapa fecha com demonstração reproduzível
  (QA headless) antes da próxima.
- Edições grandes em escrita atômica com contagem assertiva de ocorrências.
- Nenhuma conclusão normal exige personagem específico; habilidades atuais
  serão normalizadas em M5 (pendência registrada no blueprint).
