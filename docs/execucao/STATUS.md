# STATUS — Corre pro Ponto (execução do blueprint)

Referências: `BLUEPRINT_CORRE_PRO_PONTO.md` (regras e decisões) e
`PLANO_50_FASES_CORRE_PRO_PONTO.md` (catálogo das 50 fases).

## Etapas

| Etapa | Objetivo | Estado | Evidência |
|---|---|---|---|
| 0 | Ambiente reproduzível: Godot 4.7 compilado, import limpo, smoke headless | concluída | binário 4.7.stable.custom_build.5b4e0cb0f (headless, x11=no wayland=no); `--import` com 0 erros de recurso (540 importados); suíte QA carrega `scenes/main.tscn` e roda corridas completas headless |
| 1 | Regra de prazo real (RunDirector): largada com contagem, relógio durante a corrida, impacto +2 s, ônibus parte no prazo | concluída | `tools/qa_etapa1_deadline.gd`: 9/9 verificações verdes (A–H, incluindo limite exato e pausa do relógio); `ETAPA1_QA_OK`, exit 0 |
| 2 | Controle preciso e colisões compreensíveis (blueprint §4/§6): matriz ação x família por classe de altura/volume, colisão pela posição real, buffer de entrada, dash sem imunidade | concluída | `tools/qa_etapa2_colisao.gd`: 10/10 verificações verdes (A–J); suíte da etapa 1 segue 9/9 (sem regressão) |
| 3 | Primeira família SLIDE_UNDER: barreira suspensa de obra com fase de introdução (fase 3), dando função ao deslize no percurso | concluída | `tools/qa_etapa3_barreira.gd`: 5/5 verificações verdes (K–O); fases 1-2 sem barreira, fase 3 com 2; percurso determinístico |
| 4 | Estrutura de fase piloto (blueprint §7/§8): módulos editáveis em dados, validador de caminho com estado do jogador, fase 3 autoral "Rua do Ipê" (336 m, 12 módulos) | concluída | `tools/qa_etapa4_piloto.gd`: 10/10 verificações verdes (P–T); validador aprova o piloto na velocidade base e no impulso 1,22x e rejeita estação sem saída; fase 3 montada só com os dados do nível (`scripts/level_data.gd`), sem loop procedural |
| 5 | Frente de conteúdo/arte do piloto: `barreira.glb` (fecha o drop-in da ETAPA 3), deck cobrindo os três corredores na fase 3, `ipe_amarelo.glb` na Rua do Ipê — tudo gerado sem bpy (`tools/glb/`) | concluída | `tools/qa_etapa5_arte.gd`: 8/8 verificações verdes (V–X); barreiras da fase 3 instanciam o GLB (0 fallbacks), deck cobre -3,25/0/+3,25 só na fase 3, 16 ipês no cenário do piloto; fases sem nível preservam o leiaute padrão |
| 6 | Auditoria de conformidade com o blueprint antes das 50 fases: matriz completa em `docs/execucao/AUDITORIA_BLUEPRINT.md` + fechamento dos gaps verificáveis (segundos faltando no atraso, estrelas por objetivo em tentativas diferentes, collider visível em modo de teste) | concluída | `tools/qa_etapa6_auditoria.gd`: 6/6 verificações verdes (A–F, idempotente); save schema v3→v4 com migração; regressões 1–5 verdes |
| 7 | 50 fases, lote 1: fases 1, 2, 4 e 5 autorais ("Saiu atrasada", "A praça do bairro", "Remendo na calçada", "Primeiro compromisso") conforme PLANO_50_FASES; visual de calçada nos três corredores; buraco como obstáculo de calçada | concluída | `tools/qa_etapa7_lote1.gd`: 6/6 verificações verdes (G–L); validador aprova as 5 fases do bairro (base e impulso); ordem de aprendizagem preservada; regressões 1–6 verdes |

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
- ETAPA 3 (21/09): barreira suspensa de obra (`barrier`) — primeira família
  SLIDE_UNDER. ID estável no catálogo ObstacleData; classe na matriz de
  regras (largura de colisão 1,3 m); visual procedural com vão inferior livre
  (drop-in `assets/props/barreira.glb` quando o lote de assets chegar); entra
  no pool de calçada e numa gag forçada a partir da fase 3 (índice 2),
  conforme a introdução do §6. Com ela, as três ações (pular, deslizar,
  trocar de corredor) passam a ter família dedicada no percurso.
- Mecanismo de famílias gated: `SIDEWALK_OBSTACLES_GATED` +
  `GATED_INTRO_PHASE` — próximas famílias do §6 (carrinho, ciclista,
  poça...) entram pelo mesmo caminho, cada uma com sua fase de introdução.
- QA etapa 3 (5/5): desvio limpo deslizando, dano pulando ou sem ação,
  gate por fase (0/0/2 barreiras nas fases 1/2/3) e percurso determinístico
  sob a mesma semente.
- ETAPA 4 (21/09): estrutura de fase piloto (blueprint §7/§8).
  `scripts/level_data.gd` — nível autoral `bairro_03` ("Rua do Ipê", fase 3):
  336 m em 12 módulos de 28 m, 6,0 m/s, prazo 66 s, 9 padrões + 12 moedas
  com posição longitudinal e corredor explícitos (roteiro fixo do §8).
  `scripts/pattern_validator.gd` — validador de caminho que modela o estado
  do jogador (corredor, tempo da troca lateral 0,25 s por corredor, pulo
  0,9 s, deslize 0,72 s cobrindo estações seguintes dentro da mesma ação)
  e revalida na velocidade base e no impulso máximo (1,22x), como pede o §7.
  Integração em `game_3d.gd`: fase com nível substitui os loops procedurais
  e as gags forçadas na camada de desafio; cenário (pista, kit de rua,
  decals, ponto de ônibus, auditoria) permanece procedural e independente —
  as duas camadas do §7 ficam separadas de verdade. Velocidade, prazo e
  distância da corrida passam a vir dos dados do nível quando ele existe.
- QA etapa 4 (10/10, P–T): dados do piloto corretos e usados pela fase 3;
  validador aprova o piloto (base e 1,22x) e rejeita estação sem corredor
  livre; controle negativo exige pulo e deslize quando as saídas laterais
  fecham; fase 3 montada com exatamente as 21 entidades dos dados (nada
  procedural); percurso do nível não depende de semente. Regressões:
  etapa 1 9/9, etapa 2 10/10, etapa 3 5/5.
- Cadastro de `class_name` novo exige `--import` para atualizar
  `.godot/global_script_class_cache.cfg` antes dos QAs headless.
- ETAPA 5 (21/09): frente de conteúdo/arte do piloto, sem bpy (indisponível
  neste sandbox). `tools/glb/glb_writer.py` — escritor de GLB binário
  (glTF 2.0) em Python puro: caixas, cilindros e icosferas achatadas,
  materiais PBR (cor/roughness/metallic), modelado direto no espaço do
  Godot (Y para cima, frente -Z, origem no chão, escala real — contrato de
  assets/props/LEIA-ME.md). `tools/glb/build_etapa5.py` gera os dois assets
  e se auto-verifica (releitura do GLB + limites de altura/origem).
- `assets/props/barreira.glb`: mesmo desenho do fallback procedural da
  ETAPA 3 (postes zincados, barra listrada entre 1,12 e 1,50 m com vão
  livre, topo a 1,90 m). O drop-in já existia no código — as duas barreiras
  da fase 3 agora instanciam o GLB (QA V3: 2 com GLB, 0 fallbacks).
- Corredores legíveis na fase 3: o nível referencia o próprio perfil de
  cenário (`LevelData.PILOT.scenery`) e o `ChunkStreamer` aplica overrides
  profundos no spec (`BuildingKit.spec_with_overrides`): deck de 9,9 m
  cobrindo os três corredores (bordas ±4,95 m), guia e rua deslocadas junto
  (tudo derivado do spec, nenhuma medida nova no código de geometria).
  Fases sem nível seguem com o leiaute padrão (QA X2).
- `assets/scene/ipe_amarelo.glb` (4,83 m): tronco com galhos de apoio e
  copa em seis cachos amarelos achatados. `_build_arvores` agora lê o nome
  do GLB do spec (`props.arvore.glb`), então o piloto usa ipês e as demais
  fases seguem com `arvore.glb` (QA W3/W4: 16 ipês na fase 3; fase 1
  intacta).
- QA etapa 5 (8/8): contratos dos dois assets (origem no chão, alturas),
  drop-ins ativos só onde devem, deck dos três corredores. Regressões:
  etapas 1–4 todas verdes.
- Analisador: `static var` (GDScript 4.4+) é limitação conhecida do
  check_gdscript.py (marca uso como UNDECLARED) — reproduzido em teste
  isolado; falsos positivos de classe interna em game_3d já registrados
  na ETAPA 4. Nenhuma questão real nova.
- ETAPA 6 (21/09): auditoria completa do blueprint antes do passo das 50
  fases (`docs/execucao/AUDITORIA_BLUEPRINT.md`). Decisão do usuário: a
  câmera permanece como está. Gaps fechados em código: (1) derrota por
  atraso informa segundos faltando, além dos metros (`shortfall_s` no
  RunDirector, HUD e feedback — blueprint §5); (2) estrelas por objetivo
  com melhor realização por tentativa (blueprint §9): `phase_goals` no
  save, schema v4 com migração que deriva "prazo" das estrelas antigas,
  `_finish_run` grava prazo/sem_dano/moedas e as estrelas vêm da união;
  (3) `debug_hitboxes` visualiza o colisor dos obstáculos em modo de
  teste (blueprint §4).
- QA etapa 6 (6/6, idempotente entre execuções): atraso em m+s, união de
  estrelas em tentativas distintas, migração v3→v4, caminho real do piloto,
  hitboxes só com o flag, piloto intacto. Regressões 1–5 todas verdes.
- Registro para o passo das 50 fases: famílias novas (lixeira, pedestre em
  travessia, carrinho, poça, ciclista...) entram pelo mecanismo gated na
  fase de introdução marcada no §6; velocidades autorais por nível seguem a
  tabela do PLANO_50_FASES (5,5–9 m/s), não os 18 m/s antigos; economia de
  teste (100k) tem ponto de reversão marcado para a publicação.
- ETAPA 7 (21/09): lote 1 das 50 fases — as fases 1, 2, 4 e 5 viraram níveis
  autorais em `LevelData` (bairro_01/02/04/05), com distâncias, velocidades,
  prazos e roteiros do PLANO_50_FASES (224 m/5,5/55 s; 280/5,8/61; 336/6,0/68;
  364/6,2/69). Ordem de aprendizagem do blueprint §6 preservada: fase 1 só
  cones; fase 2 cone+banco; fase 4 introduz o buraco (pulo) com barreira e
  cone já conhecidos; fase 5 revisa as quatro famílias sem novidade. Clímax
  da fase 4 = buraco seguido de banco com aterrissagem garantida; clímax da
  fase 5 = baixo → alto → desvio com recuperação.
- Cenário compartilhado `CENARIO_TRES_CALCADAS` (deck cobrindo os três
  corredores) aplicado às quatro fases; a fase 3 mantém o ipê por conta.
- Mudanças de suporte: fases autorais usam visual de calçada nos três
  corredores (o índice 0 deixava o mobiliário com cara de rua) via flag
  `sidewalk_style` no `_spawn_entity`; buraco ganhou branch de calçada com o
  mesmo visual da rua (`_build_pothole_visual` compartilhado).
- QA etapa 7 (6/6): dados da tabela do plano, validador nas 5 fases (base e
  impulso), montagem exata sem procedural, ordem de aprendizagem, visuais
  corretos nos corredores e determinismo. Regressões 1–6 verdes (QA1 H agora
  verifica a fórmula do catálogo numa fase procedural; QA5 X2 e QA6 E usam
  fase sem nível).
- Decisão de design: "floreira" segue a regra do banco (família
  "Banco/floreira" do §6); variação visual fica para passe de arte.

## Regras de engenharia desta execução

- Uma etapa por vez; cada etapa fecha com demonstração reproduzível
  (QA headless) antes da próxima.
- Edições grandes em escrita atômica com contagem assertiva de ocorrências.
- Nenhuma conclusão normal exige personagem específico; habilidades atuais
  serão normalizadas em M5 (pendência registrada no blueprint).
