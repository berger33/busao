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
| 8 | 50 fases, lote 2 (comércio e praça): fases 6–10 autorais ("Na porta da padaria", "Passagem de pedestres", "Hora da entrega", "A van da esquina", "Feira de sábado") + 4 famílias (lixeira, pedestre em travessia, carrinho de entrega, van parada); travessias laterais com aviso; validador com posições temporais | concluída | `tools/qa_etapa8_lote2.gd`: 6/6 verificações verdes (M–R); validador aprova as 10 fases (base e impulso); colisão de travessia pela posição real; regressões 1–7 verdes |
| 9 | 50 fases, lote 3: fases 11–15 autorais ("Sob o andaime", "Poças da manhã", "Ciclovia na praça", "Olha a moto", "Desvio de obra") + 5 famílias (andaime, poça, floreira, ciclista, moto em cruzamento); travessias rápidas, rumo do modelo e som de aviso da moto | concluída | `tools/qa_etapa9_lote3.gd`: 6/6 verificações verdes (S–X); validador aprova as 15 fases (base e impulso); regressões 1–8 verdes |
| 10 | 50 fases, lote 4 (avenida, fecha a campanha inicial): fases 16–20 autorais ("O caramelo da praça", "Entregas da avenida", "Travessia do caminhão", "Últimas quadras", "Peguei o ônibus!") + 4 famílias (cachorro cruzando, caixa baixa, caminhão e ônibus em cruzamento); pesados com colisão no nariz, área sinalizada e buzina; fase 20 com respiros e bilhetes dourados | concluída | `tools/qa_etapa10_lote4.gd`: 6/6 verificações verdes (L4-A–L4-F); validador aprova as 20 fases (base e impulso); regressões 1–9 verdes |
| 11 | 50 fases, lote 5 (centro histórico, reuso): fases 21–25 autorais ("Rua das fachadas", "Entrega na livraria", "Foto na praça", "Restauração da fachada", "O ponto da igreja"), sem família nova; rua de comércio antigo (vitrines/toldos), praça com ipês e igreja ao lado do ponto na fase 25 | concluída | `tools/qa_etapa11_lote5.gd`: 6/6 verificações verdes (L5-A–L5-F); validador aprova as 25 fases (base e impulso); regressões 1–10 verdes |

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
- ETAPA 8 (21/09): lote 2 das 50 fases — comércio e praça. Fases 6–10
  autorais em `LevelData` (bairro_06–10) com distâncias, velocidades,
  prazos e roteiros do PLANO_50_FASES (364/6,2/71; 364/6,3/70; 392/6,4/73;
  392/6,5/72; 420/6,5/75). Quatro famílias novas pelo mecanismo gated, cada
  uma na sua fase de introdução do §6: lixeira/FULL (6), pedestre em
  travessia/SOFT (7), carrinho de entrega/FULL (8), van parada/VEHICLE (9);
  fase 10 é revisão sem novidade.
- Travessia lateral com aviso (primeiras famílias dinâmicas): padrões com
  `cross_mps/from_x/to_x/lead_m` esperam no ponto de partida e cruzam
  quando o corredor alcança `start_d = at_m − lead_m`, no relógio da
  simulação (pausa congela; independe de fps). `_resolve_entity` usa a
  posição real do nó para entidades em travessia (antes usava o corredor
  de spawn). Visuais: `lixeira.glb` e `carrinho.glb` como drop-in,
  pedestre estilizado e van procedurais.
- Validador com posições temporais (§7): bloqueio por corredor avaliado na
  posição do obstáculo no instante da passagem (±0,6 m em Z), na base e no
  impulso 1,22x — pedestres param no corredor-alvo e carrinhos atravessam
  e saem do tabuleiro, sempre com rota livre declarada.
- QA etapa 8 (6/6): dados do plano + matriz das famílias + gates,
  validador nas 10 fases, montagem exata, dinâmica das travessias
  (espera, cruzamento no relógio, esbarrão SOFT vs dano FULL pela posição
  real), ordem de aprendizagem e determinismo. Regressões 1–7 verdes
  (QA5 X2 agora usa a fase 11, ainda procedural). Analisador: só falsos
  positivos ambientais (sem doc de API do engine); fixture intencional
  `erro_sintaxe.gd` quebra o parse do projeto — excluída da varredura.
- Ambiente reconstruído após reprovisionamento do sandbox: swap de 8G,
  venv de ferramentas (scons/gdtoolkit/pkgconf), Godot 4.7-stable
  (5b4e0cb) recompilado headless (`x11=no wayland=no`), `--import` limpo.
- ETAPA 9 (21/09): lote 3 das 50 fases. Fases 11–15 autorais em `LevelData`
  (bairro_11–15) com números do PLANO_50_FASES (392/6,6/72; 392/6,6/72;
  420/6,8/72; 420/6,8/73; 448/7,0/73). Cinco famílias pelo mecanismo
  gated, cada uma na sua fase de introdução do §6: andaime/SLIDE_UNDER
  (11, barra alta com vão + apoios laterais), poça/SOFT (12, atravessar
  molha o pé com lentidão determinística), floreira/FULL (13, mesma regra
  do banco), ciclista/FULL (13, travessia rápida a 3,0 m/s) e moto em
  cruzamento/VEHICLE (14, 4,5 m/s com som + sinal visual antes da
  passagem); fase 15 é revisão sem novidade.
- Travessias rápidas usam o mesmo sistema da ETAPA 8 (validador temporal
  sem mudanças: na base bloqueiam o corredor-alvo, no impulso ficam no
  vão). Modelos em travessia agora encaram o rumo no spawn (giro genérico
  para cart/crosser/cyclist/moto_cross, com hitbox de teste
  contra-girada); a moto toca buzina aguda ao arrancar. Reações de desvio
  completadas para as 9 famílias dos lotes 2–3.
- QA etapa 9 (6/6): dados do plano + matriz + gates, validador nas 15
  fases, montagem exata, comportamentos (andaime deslize/pulo, poça
  pulo/molhar, ciclista FULL, moto VEHICLE nem com pulo, rumos),
  ordem de aprendizagem + novas famílias seguras paradas (pool
  procedural) e determinismo. Regressões 1–8 verdes (QA1 H e QA5 X2 agora
  usam fases ainda procedurais, índice 15).
- ETAPA 10 (21/09): lote 4 das 50 fases, fecha a campanha inicial.
  Fases 16–20 autorais em `LevelData` (bairro_16–20) com números do
  PLANO_50_FASES (420/7,0/71; 448/7,2/73; 448/7,2/73; 476/7,4/74;
  504/7,5/76) e cenário de avenida (deck + `palmeira.glb`).
  Quatro famílias pelo mecanismo gated: cachorro cruzando/SOFT (16, sem
  perseguição: kind distinto do "dog", sem `dog_chase_timer` nem
  mobilidade), caixa baixa de entrega/LOW (17, pular resolve), caminhão e
  ônibus em cruzamento/VEHICLE (18, sempre da esquerda para a direita).
  Pesados com origem de colisão no nariz (ponta exatamente na origem,
  carroceria a reboque), área sinalizada zebrada no chão sob cada
  cruzamento e buzina grave/aguda ao arrancar (nunca o único aviso:
  veículo espera visível + faixa no chão). Parados no pool procedural,
  encaram quem chega (180°). Fase 20 em três blocos com respiros e três
  bilhetes dourados no embarque final.
- QA etapa 10 (6/6): dados do plano + matriz + gates + palmeiras,
  validador nas 20 fases, montagem exata, comportamentos (cachorro sem
  perseguição, caixa LOW, pesados VEHICLE nem com pulo, rumos, 5 zonas
  na fase 18, nariz na origem, palmeiras só no lote 4), ordem de
  aprendizagem + novas famílias seguras paradas e determinismo.
  Regressões 1–9 verdes (QA1 H e QA5 X2 migrados para o índice 20,
  primeira fase ainda procedural).
- Lições do lote registradas nos testes: `find_child`/`find_children`
  com `owned=true` (padrão) ignora nós criados em runtime; sem frames
  entre `_start_run` os irmãos liberados seguem na árvore e o Godot
  renomeia os novos para `@Node3D@N` — consultas por nome entre
  montagens precisam de identidade estrutural/posição (zonas achadas
  pela `CrossZoneBase`).
- ETAPA 11 (21/09): lote 5 das 50 fases (centro histórico, reuso).
  Fases 21–25 autorais em `LevelData` (bairro_21–25) com números do
  PLANO_50_FASES (448/7,4/72; 476/7,5/74; 476/7,6/73; 504/7,6/76;
  504/7,7/74), só com famílias já apresentadas (banco, floreira,
  pedestre, caixa, carrinho, andaime, vala, cone). Cenário pelo
  building_kit (camada viva): pesos de loja/reboco dominando a rua,
  ipês na praça, bancos e postes adensados; fase 25 com `marco:
  igreja` ao lado do ponto (fora dos corredores, sem colisão).
- Descoberta do lote: `_build_track` só retorna — as fatias
  (`_build_track_antigo`, `building_style`, vitrines/casas/igreja por
  fatia) são código morto desde o Lote 3; a primeira versão da etapa
  ligou um override de fatias sem leitor e foi revertida para o kit.
  Teste novo: `queue_free` marca só o nó direto — peças-filhas de
  marco exigem checar `is_queued_for_deletion` até a raiz.
- QA etapa 11 (6/6): dados do plano + gates intactos + cenários,
  validador nas 25 fases, montagem exata, comportamentos (dois
  pedestres alternados, andaime/vala, cruzamentos pelo centro, igreja
  no ponto, 12 toldos na rua, 15 ipês), reuso sem estreia e
  determinismo. Regressões 1–10 verdes (QA1 H e QA5 X2 migrados para
  o índice 25, primeira fase ainda procedural).
- ETAPA 12 (21/09): lote 6 das 50 fases (Mercado, reuso).
  Fases 26–30 autorais em `LevelData` (bairro_26–30) com números do
  PLANO_50_FASES (476/7,6/74; 504/7,7/76; 504/7,8/75; 532/7,8/78;
  532/8,0/75), só com famílias já apresentadas (caixa, banco, cone,
  carrinho, barreira, van, pedestre, lixeira, ciclista). Cenário pelo
  building_kit (camada viva): árvore comum e bancos de volta, lixeira
  densa, galpões e lojas no fundo; `_spawn_feira` planta barracas
  (`barraca.glb` + reserva procedural, x=±6,4 m a cada 56 m dos dois
  lados, pulando as que caem sobre travessias) — visual puro, sem
  colisão nem entrada em `entities`. Fase 30 sem moeda dourada (não é
  final de campanha).
- QA etapa 12 (6/6): dados do plano + gates intactos + cenário da
  feira, validador nas 30 fases, montagem exata, comportamentos
  (carrinhos a 112 m em sentidos alternados, esquina van+cruzante,
  toldo/caixa, 16/14/18/18/18 barracas fora das pistas e travessias,
  galpões no fundo, só árvore comum), reuso sem estreia e
  determinismo. Regressões 1–11 verdes (QA1 H e QA5 X2 migrados para
  o índice 30, primeira fase ainda procedural).
- ETAPA 13 (21/09): lote 7 das 50 fases (Parque e orla, reuso).
  Fases 31–35 autorais em `LevelData` (bairro_31–35) com números do
  PLANO_50_FASES (476/7,8/73; 504/8,0/73; 504/8,0/73; 532/8,1/75;
  560/8,2/77), só com famílias já apresentadas (banco, floreira,
  cone, cachorro, pedestre, ciclista, vala, barreira). Cenário pelo
  building_kit (camada viva): palmeiras em alameda (cada uma com
  canteiro), bancos de praça, casas baixas de 1–2 pisos (horizonte
  aberto); `_spawn_quiosques` planta quiosques (`quiosque.glb` +
  reserva, x=±6,4 m a cada 112 m dos dois lados, pulando
  travessias) — visual puro; fase 35 com `marco: guarita` ao lado
  do ponto. Luz aberta por paleta do nível (`scenery.paleta`,
  aplicada em `_render_profile_world`; sem ela vale o rodízio
  global do world_spec).
- Descoberta do lote: `_scene_glb` é determinístico — as "árvores
  sem nome" eram palmeiras reais renomeadas para `@Node3D@N`, e o
  `find` case-sensitive não casava `Palmeira`; a contagem do QA13
  compara sem maiúsculas (16/16 na fase 31).
- QA etapa 13 (6/6): dados do plano + gates intactos + cenário do
  parque, validador nas 35 fases, montagem exata, comportamentos
  (passeio SOFT em E/D, ciclistas FULL, vala/barra, 8/8/8/10/10
  quiosques fora das travessias, guarita no ponto, paleta orla
  aplicada com rodízio global intacto, 16 palmeiras), reuso sem
  estreia e determinismo. Regressões 1–12 verdes (QA1 H e QA5 X2
  migrados para o índice 35, primeira fase ainda procedural).

## Regras de engenharia desta execução

- Uma etapa por vez; cada etapa fecha com demonstração reproduzível
  (QA headless) antes da próxima.
- Edições grandes em escrita atômica com contagem assertiva de ocorrências.
- Nenhuma conclusão normal exige personagem específico; habilidades atuais
  serão normalizadas em M5 (pendência registrada no blueprint).
