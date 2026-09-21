# AUDITORIA — conformidade com o Blueprint (antes das 50 fases)

Data: 2026-09-21 (ETAPA 6). Documentação: cruza cada requisito do
`BLUEPRINT_CORRE_PRO_PONTO.md` com a implementação atual e registra o que
ainda falta, por quê, e a quem pertence (etapa de conteúdo, aparelho ou
decisão humana). O `PLANO_50_FASES_CORRE_PRO_PONTO.md` é o próximo passo;
esta auditoria confirma que a infraestrutura que ele exige está pronta.

**Legenda**
- ✅ implementado e coberto por QA headless reproduzível
- 🟡 implementado com nota/pendência registrada (não bloqueia)
- 📱 exige aparelho real ou julgamento humano (fora do alcance do sandbox)
- ⏭️ conteúdo do passo das 50 fases (mecanismo pronto; a família/etapa é o próprio trabalho)
- 🎯 decisão do usuário (ex.: câmera mantida como está)

---

## §1 — Decisões da inspeção inicial

| Requisito | Estado | Evidência |
|---|---|---|
| Evoluir a base 3D existente (`main.tscn`/`game_3d.gd`) | ✅ | todas as etapas sobre a mesma cena |
| Revisar resposta e coerência das ações | ✅ | ETAPA 2 (buffer, posição real, dash sem imunidade) — QA 10/10 |
| Substituir progressão numérica por percursos autorais | 🟡 | infraestrutura pronta (ETAPA 4); fase 3 autoral; fases 1-2 e 4-50 migram no passo das 50 fases |
| Sequências com caminho válido e ritmo controlado | ✅ | `PatternValidator` + `LevelData` — QA etapa 4 |
| Três corredores na calçada; rua como contexto | ✅ | deck de 9,9 m cobre −3,25/0/+3,25 na fase 3 (ETAPA 5, QA X); demais fases mantêm o leiaute até migrar |
| Prazo contado durante a corrida | ✅ | ETAPA 1 — QA 9/9 |
| Altura/volume/ações por obstáculo | ✅ | ETAPA 2/3 (`obstacle_rules.gd`) — QA 10/10 + 5/5 |
| Kit de cenário como base de módulos editáveis | ✅ | `world_spec.json` + overrides por nível (ETAPA 5) |
| Escolher uma protagonista para o padrão da referência | 📱 | personagens existem (`assets/characters`); aprovação visual é humana |
| Câmera: calibrar a partir da base | 🎯 | **usuário decidiu manter como está** (2026-09-21) |
| Validar renderer no aparelho exportado | 📱 | sem Android no sandbox |
| Simplificar experiência da corrida | ✅ | HUD de prazo, contagem, embarque, causa de derrota |
| Separar economia de teste do lançamento | 🟡 | `game_balance.tres: starting_coins=100000 # TESTE` e bloco de injeção em `save_data.gd:162-176` marcados com comentário de reversão; reverter ao publicar |

## §2 — Experiência fixada

Ciclo completo implementado: mapa → resumo da fase → contagem → corrida →
ponto/ônibus visíveis → embarque no prazo → resultado com estrelas e
repetição rápida (QA etapas 1 e 4).

**Lista explícita do que pertence à fase piloto** (pedido no "Pronto quando"):
1. 336 m em 12 módulos de 28 m, velocidade 6,0 m/s, prazo 66 s (`LevelData.PILOT`);
2. 9 obstáculos autorais + 12 moedas do roteiro §8 (nada procedural no desafio);
3. Deck cobrindo os três corredores + ipês amarelos + rua à esquerda (`scenery`);
4. Barreira suspensa (`barreira.glb`) ensinando o deslize;
5. Ponto de ônibus com abrigo e ônibus de embarque no fim;
6. Validação: rota legal na base e no impulso (1,22x), prazo e causa de derrota.

## §3 — Direção de arte

| Item | Estado | Nota |
|---|---|---|
| Composição 1:1 e 9:16, câmera final | 📱 | câmera mantida (decisão do usuário); comparação exige aparelho |
| Protagonista (silhueta, rig, clips, passada) | 📱 | GLBs e clips existem; aprovação e sincronização fina exigem aparelho |
| Risco passada × velocidade (4 m/s ref vs 18 m/s) | 🟡 | passos das 50 fases usa 5,5–9 m/s por nível; curva antiga fica só nas fases não migradas |
| Horário único (fim de tarde) no piloto | ✅ | paleta do capítulo via `world_spec.json`/`chapter_profile` |
| Materiais compartilhados (piso, asfalto, tijolo...) | ✅ | PBR Lote 1 + `materiais` do spec |
| Moeda legível (maior que o real) | ✅ | coletável com escala própria (`_build_collectible`) |
| Sem SDFGI/VoxelGI como requisito Android | ✅ | Mobile/Compatibility; luz direcional + AO |
| Lightmaps só após teste do modelo de chunks | 🟡 | não aplicados; cenário reciclado por design |
| Captura real no aparelho | 📱 | — |

## §4 — Controle preciso e colisões compreensíveis

| Item | Estado | Evidência |
|---|---|---|
| Três corredores lógicos sem linhas pintadas | ✅ | deck contínuo (ETAPA 5) |
| Protótipo de escala 1,1–1,3 m | 🟡 | **decisão registrada**: manter 3,25 m (`LANE_X`) e adaptar o cenário (ETAPA 5) em vez de trocar `LANE_X` isoladamente, como o próprio blueprint alerta |
| Troca de corredor 0,18–0,25 s | ✅ | converge em ~0,2 s; validador usa 0,25 s/corredor |
| Pulo com tolerância de entrada | ✅ | buffer 0,12 s em tempo de simulação (QA I) |
| Deslize 0,65–0,80 s | ✅ | 0,72 s |
| Pausa congela simulação e prazo | ✅ | QA F2 |
| Arrancada curta e limitada após núcleo validado | ✅ | dash = explosão, cooldown 3,2 s, sem imunidade |
| Buffer ~120 ms; 1 gesto = 1 ação; sem ação no retorno da pausa | ✅ | QA etapa 2 |
| Visualização de collider em modo de teste | ✅ | `debug_hitboxes` (ETAPA 6, QA E) |
| Colisão pela posição real na troca | ✅ | QA F etapa 2 |
| 3 pontos de fôlego; +2 s por impacto mostrado | ✅ | QA G etapa 1 |
| 1 impacto por entidade; recuperação ~1 s | ✅ | `passed` + invulnerabilidade 1,15 s |
| Zero fôlego/prazo encerram com causa exibida | ✅ | QA C/D + HUD (atraso mostra m **e s** — ETAPA 6) |
| Pulo não atravessa ônibus/caminhão; deslize não resolve banco/hidrante/pessoa | ✅ | matriz ETAPA 2 (QA B/C) |
| Pessoas/animais: esbarrão sem dano | ✅ | classe SOFT (QA G) |
| Dez tentativas repetem a mesma resposta | ✅ | determinismo QA J/O/T |

## §5 — O ônibus como meta real

| Item | Estado | Evidência |
|---|---|---|
| Prazo começa na largada; HUD "ônibus parte em MM:SS" | ✅ | ETAPA 1 |
| Pausa/segundo plano suspendem | ✅ | notificações tratadas + QA F2 |
| Estados preparação→…→resultado | ✅ | `RunDirector` |
| Regra autoritativa + ordem determinística + sem dupla conclusão | ✅ | `crossed_boarding`/`finished` |
| Sem toque extra no último quadro | ✅ | zona de embarque ampla (28 m) |
| Prazo = referência + margem (protótipo d/v) | ✅ | DEADLINE_MARGINS; níveis autorais definem o próprio prazo (66 s = 56+10 do §8) |
| 70–90 m: ponto visível; 40–60 m: aviso; últimos 28 m limpos | ✅ | `APPROACH_DISTANCE_M=90`, `APPROACH_NEAR_M=45`, `BOARDING_ZONE_M=28` |
| Atraso: ônibus parte, informar segundos faltando, repetir rápido | ✅ | **ETAPA 6**: `shortfall_s` no diretor, feedback e resultado (QA A) |
| Toda fase vencível sem arrancada | ✅ | validador aprova sem boost obrigatório; dash nunca é requisito |

## §6 — Biblioteca de obstáculos

Famílias com regra e colisão implementadas: cone/LOW, buraco/GROUND,
banco-hidrante-orelhão-bicicleta/FULL, veículos/VEHICLE, pedestres e
cachorro/SOFT, barreira/SLIDE_UNDER (QA etapas 2-3). Cada uma com ID
estável, visual (GLB com fallback procedural), largura de colisão, ações
válidas e teste de passagem.

✅ Famílias introduzidas na ETAPA 8 pelo mecanismo gated: lixeira/FULL
(fase 6), pedestre em travessia/SOFT com trajetória anunciada (7), carrinho
de entrega/FULL com travessia lenta (8), van parada/VEHICLE (9).

✅ Famílias introduzidas na ETAPA 9: andaime/SLIDE_UNDER (fase 11),
poça/SOFT com lentidão determinística (12), floreira/FULL (13),
ciclista/FULL em travessia rápida (13), moto em cruzamento/VEHICLE com som
+ sinal visual (14).

⏭️ Famílias cuja **introdução pertence aos próximos lotes**: cachorro
cruzando (16), caminhão/ônibus em janela (18). O mecanismo de famílias
gated (`SIDEWALK_OBSTACLES_GATED` + `GATED_INTRO_PHASE`, ETAPA 3) é o
caminho aprovado para cada uma entrar na sua fase de introdução.

Regras transversais do §6 atendidas: veículos decorativos não colidem;
props fora da rota não têm collider de gameplay; espaçamento procedural em
intervalos de distância (legibilidade final medida por módulo no passo das
50 fases).

## §7 — Módulos editáveis e validador

| Item | Estado | Evidência |
|---|---|---|
| Fase montável com módulos e dados sem editar o controlador | ✅ | "Pronto quando" atendido (ETAPA 4): basta entrada em `LevelData.LEVELS` |
| Módulos de 28 m | ✅ | `chunk_length_m: 28` |
| Duas camadas independentes (cenário ≠ desafio) | ✅ | desafio em `patterns/coins`; cenário referenciado via `scenery` (ETAPA 5) |
| Validador considera estado do jogador (corredor, transição, ação, recuperação) | ✅ | `PatternValidator` (QA Q/R2) |
| Revalidação na velocidade máxima | ✅ | fator 1,22x (QA Q) |
| Boost nunca torna a única saída impossível | ✅ | mesma validação nos dois fatores |
| Posições temporais de pedestres/veículos no validador | ✅ | ETAPA 8: bloqueio por corredor avaliado na posição temporal (±janela Z), base e impulso (QA M/N/P) |
| Encaixe de chunks (comprimento variável ±1 m) | 🟡 | sobreposição cosmética ≤ 1 m possível; blueprint pede confirmação visual antes de classificar defeito (📱) |
| Estrutura de cena `Trecho28m`/.tscn por módulo | 🟡 | substituída por dados declarativos (padrões em dicionário) — mesmo contrato, mais leve; cenas por módulo podem voltar se a edição visual exigir |

## §8 — Fase piloto 336 m

✅ integral: nome, velocidade, prazo, 12 módulos e as 12 situações da tabela
(QA etapa 4: dados, validador, montagem exata das 21 entidades,
determinismo). Arte do piloto na ETAPA 5 (deck de três corredores, ipês,
barreira com GLB).

## §9 — Escalar a campanha

| Item | Estado | Nota |
|---|---|---|
| Velocidades 5,5–6,5 iniciais, teto ~8,5–10 | ⏭️ | cada nível define `base_speed_mps` (o plano traz a tabela); não adotar 18 m/s — registrado |
| Ritmo apresentação→prática→combinação→respiro→clímax→embarque | ⏭️ | roteiro por fase no passo das 50 fases |
| Vencer libera a próxima; estrelas não bloqueiam campanha | ✅ | desbloqueio por conclusão |
| Estrela 1 = prazo; 2 = sem colisão; 3 = rota de moedas/objetivo | ✅ | regra existente no `_finish_run` |
| Estrelas 2 e 3 em tentativas diferentes (melhor realização) | ✅ | **ETAPA 6**: `phase_goals` por objetivo, schema v4 (QA B/C/D) |
| Moedas compram aparência; protagonista inicial completa a campanha | ✅ | nenhuma conclusão exige compra |
| Habilidades de personagem normalizadas | 🟡 | pendência M5 registrada no blueprint; conclusões normais não dependem delas |
| Fracasso sem energia/espera | ✅ | não existe sistema de energia |
| ID estável, saves versionados, sem remapear estrelas antigas | ✅ | schema v3→v4 deriva `prazo` das estrelas antigas sem recalcular o resto (QA C) |
| Assistência opcional (antecipação/prazo) | ⏭️ | M7 (acessibilidade) |

## §10 — Interface e som

| Item | Estado | Nota |
|---|---|---|
| HUD: pausa, prazo/progresso, moedas, fôlego | ✅ | cápsula de prazo + feedback |
| Tutoriais somem ao aprender | ✅ | `tutorial_stage` |
| Resultado: causa, objetivos, moedas, repetir/próxima | ✅ | tela 3D de resultados |
| Sons essenciais (pulo, impacto, moeda, buzina, música) | ✅ | `assets/audio/*` + `AudioManager` |
| Passos por superfície, raspão, portas do ônibus | 🟡 | polish M4 |
| Jogar sem som entendendo tudo | ✅ | todos os avisos têm contraparte visual |

## §11 — Organização da implementação

✅ RunDirector extraído; regras em `obstacle_rules.gd`; fases com IDs
estáveis; cenário spec-driven; obstáculos com contrato por família;
HUD com prazo real; save versionado. 🟡 `game_3d.gd` segue grande
(>4 mil linhas) — migração contínua prevista no blueprint; posição do
jogador tem fonte única (`player_x`/lane) e comportamento independente de
fps (tempo de simulação, QA I).

## §12 — Orçamento de arte/desempenho

📱 aparelho mínimo/referência ainda não definido (fora do sandbox).
Técnicas já aplicadas: MultiMesh no kit, faixas de visibilidade/LOD,
materiais compartilhados, qualidade nunca altera gameplay
(`_apply_render_quality`).

## §13 — Testes

Cobertos por QA headless: largada/pausa/retomada/derrota/repetição,
chegada adiantada/limite/atrasada, expiração no meio do caminho, impacto
+2 s, buffer, posição real, determinismo, save v3→v4, fases vencíveis sem
dash/pagos/personagem específico.
📱 Playtest com pessoas, 30/60 FPS no aparelho, capturas comparativas.

## §15 — Entregáveis do piloto (checklist)

| Entregável | Estado |
|---|---|
| Meta visual + comparação 1:1/9:16 | 📱 |
| Protagonista aprovada (GLB, rig, clips) | 📱 (assets existem) |
| Câmera e escala consistentes | 🎯 câmera mantida; escala real nos assets (contrato LEIA-ME) |
| Kit urbano (6–8 fachadas, piso/guia, 3 árvores, banco, poste, canteiro, ponto) | ✅ (fachadas casa/colonial/loja/predio2/predio3/casa_favela/igreja/obra; árvores arvore/palmeira/ipe_amarelo) |
| Ônibus com embarque + 2 carros de contexto | ✅ |
| Obstáculos básicos (cone/caixa, banco/floreira, barra, buraco, bloqueio alto) | ✅ (floreira = variação visual do banco no passo das 50) |
| Três corredores claros, comandos/colliders coerentes | ✅ |
| Prazo desde a largada, penalidade, resultados corretos | ✅ |
| 12 módulos + fase 336 m com roteiro fixo | ✅ |
| HUD de corrida, resultado, pausa, repetição rápida | ✅ |
| Sons essenciais + alertas sem áudio | ✅ |
| Capturas/vídeo no aparelho | 📱 |
| Playtest com iniciantes | 📱 |

---

## Gaps fechados na ETAPA 6 (esta auditoria)

1. **Segundos faltando no atraso** (§5): `shortfall_s` no diretor + HUD e
   feedback mostrando "X m (Y s)" — QA A.
2. **Estrelas por objetivo em tentativas diferentes** (§9): `phase_goals`,
   save schema v4 com migração, `_finish_run` grava os objetivos — QA B/C/D.
3. **Collider visível em modo de teste** (§4): `debug_hitboxes` — QA E.

## O que NÃO bloqueia o passo das 50 fases

- 📱 Itens de aparelho/julgamento humano (aprovação visual, FPS, playtest):
  o blueprint os coloca em M2/M4/M5, com a campanha sendo construída em
  paralelo e validada por lote.
- ⏭️ Novas famílias de obstáculo e fases 1-2 e 4-50 autorais: **são o
  próprio passo das 50 fases** — o blueprint marca a fase de introdução de
  cada família, e o mecanismo gated + validador + dados de nível é a
  infraestrutura que esse passo usa.
- 🟡 Pendências registradas: economia de teste (reverter ao publicar),
  encaixe cosmético de chunks (confirmar no aparelho), passos/raspão de
  som (polish M4), normalização de habilidades (M5).

## Recomendação de sequência (do PLANO_50_FASES §"Sequência de entrega")

1. ✅ Derivar as fases 1, 2, 4 e 5 com os módulos aprovados do piloto —
   **feito na ETAPA 7** (`bairro_01/02/04/05` em `LevelData`, QA 6/6).
2. ✅ Produzir 6–10 introduzindo lixeira, pedestre em travessia, carrinho
   e van parada — **feito na ETAPA 8** (`bairro_06`–`bairro_10` em
   `LevelData`, travessias laterais com aviso, QA 6/6).
3. Lotes seguintes conforme o plano, cada um fechando com QA reproduzível.
