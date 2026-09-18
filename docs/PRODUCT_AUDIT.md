# Auditoria de produto — Corre pro Ponto 3D

**Revisão:** 18 de setembro de 2026  
**Escopo:** gameplay 3D ativo, HUD, progressão de 50 fases, economia local, persistência, feedback audiovisual, acessibilidade e instrumentação sem rede.

Este documento registra as decisões implementadas nesta revisão e o que ainda precisa de validação no Godot e com jogadores. Ele não substitui playtest, teste de acessibilidade, medição de FPS ou revisão de publicação Android.

## Decisões de produto

1. **Diversão e compreensão antes de retenção artificial.** O jogo não usa loot box, recompensa paga aleatória, anúncios interrompendo a corrida, energia, streak punitivo ou perda de progresso.
2. **A rua e as calçadas são escolhas legíveis.** A faixa esquerda permanece exclusivamente rua e recebe mais obstáculos; centro e direita são calçadas, com pedestres, animais e props urbanos.
3. **A primeira vitória deve ser curta e explicada.** A fase inicial parte de 5 m/s, tem poucos obstáculos, espera reduzida no ponto e um hint de controles nos primeiros 70 m.
4. **Recompensa de replay não é igual à de primeira conclusão.** Replays pagam um bônus fixo menor; uma nova estrela paga somente a diferença. As moedas coletadas na pista são o ganho principal da habilidade e não são duplicadas como bônus de conclusão.
5. **A meta fica visível.** Estrelas têm regras explícitas: concluir = 1, terminar sem dano = +1, cumprir a meta de moedas = +1. Tempo serve para recorde, não para esconder uma condição de recompensa.
6. **Loja sem aleatoriedade.** Personagens e itens são compras únicas com preço mostrado. O HUD distingue disponível, adquirido e equipado; efeitos aplicáveis são ativados na próxima corrida.
7. **Retenção com consentimento e controle.** A sequência de retorno é um bônus opcional, não bloqueia conteúdo nem zera metas; movimento reduzido, alto contraste, áudio desligado e pausa automática deixam o jogador no controle.
8. **A economia tem uma fonte autoritativa.** `scripts/shop_data.gd` guarda preços; `GameSave.unlock()` ignora valores enviados pela tela e valida o catálogo antes de gastar moedas.

## Curva atual de gameplay

Os valores editáveis ficam em `resources/game_balance.tres`, consumidos por `scripts/phase_data.gd`, `scripts/game_3d.gd` e `scripts/save_data.gd`.

| Marco | Velocidade | Distância aproximada | Obstáculos | Espera no ponto |
|---|---:|---:|---:|---:|
| Fase 1 | 5,0 m/s | 400 m | intensidade 2 / ~15 rua | 5,0 s |
| Fase 10 | ~8,3 m/s | 472 m | intensidade 7 / ~23 rua | ~3,6 s |
| Fase 20 / terminal do capítulo 1 | 12,0 m/s | 552 m | intensidade 12 / ~37 rua | 2,0 s |
| Fase 40 | ~16,0 m/s | 712 m | intensidade 16 / ~67 rua | 2,0 s |
| Fase 50 | 18,0 m/s | 792 m | intensidade 18 / ~94 rua | 2,0 s |

A duração nominal fica aproximadamente entre 45 e 80 segundos antes de efeitos de velocidade, colisões e pausa. Isso favorece sessões curtas sem transformar uma falha em uma espera longa. O campo `obstacles` é uma intensidade de design: o spawn converte-o em intervalos de 24 m na fase 1 até 8 m na fase 50, sem o erro de transformar a fase inicial em um corredor lotado. A densidade da rua continua maior do que a das calçadas por construção; o preflight simula essa relação nas 50 fases. A meta de moedas começa generosa para ensinar a rota e sobe gradualmente até cerca de 70–78% das moedas nominais no fim do catálogo, portanto é uma meta de leitura, não uma coleta perfeita impossível.

### Estrelas e desbloqueios

- Cada fase guarda até 3 estrelas; o máximo é 150.
- Fases intermediárias exigem a estrela da fase anterior.
- A fase 20 exige 45 estrelas e a conclusão da fase 19.
- A fase 50 exige 120 estrelas e a conclusão da fase 49.
- Endless é liberado ao concluir a fase 50.
- A tela de mapa mostra o próximo marco de estrelas, em vez de apenas exibir um botão bloqueado.

O requisito de 45 estrelas representa 30% do primeiro capítulo completo; 120 representa 80% do catálogo. Esses limites devem ser ajustados após observar taxa de conclusão e frustração, não por uma meta arbitrária de sessões.

## Orçamento de economia

A economia usa `R$` como unidade fictícia de jogo, sempre apresentada como moeda virtual. Não há compra com dinheiro real neste escopo.

- Saldo inicial: R$ 40.
- Moeda coletada na pista: entra uma vez no saldo no momento da coleta.
- Primeira conclusão: bônus base de R$ 30, mais componente transparente de fase/estrelas e bônus de perfeição.
- Replay sem nova estrela: bônus base de R$ 8.
- Nova estrela em replay: R$ 12 por estrela nova.
- Missões diárias: R$ 25, R$ 35 e R$ 45.
- Marco semanal de distância: R$ 100.
- Retorno em sete dias consecutivos: R$ 100; a sequência é informativa e não bloqueia conteúdo.
- Endless: recompensa inicial maior quando bate recorde e teto reduzido em repetição.
- XP: primeira conclusão dá XP escalável por fase, replay dá XP menor e a HUD mostra nível e progresso até o próximo nível (250 XP por nível).

A persistência usa schema v3 e não grava JSON a cada moeda. Eventos de corrida marcam o save como sujo e fazem autosave amortizado; compras, desbloqueios, login, conclusão e mudança de preferência fazem flush. A escrita usa arquivo temporário, backup e recuperação de JSON inválido; quando o primário está corrompido, o primeiro reparo preserva o backup íntegro em vez de copiá-lo por cima.

## Feedback e UX

### Durante a corrida

- Feedback visual de faixa, pulo, deslize, dash, combo, escudo e impacto.
- SFX específicos para moeda, combo, recompensa, colisão, whoosh e chegada.
- Câmera e flash leves em impacto; o runner possui animação de pernas e o tráfego tem movimento próprio.
- Hint inicial de controles; a legenda inferior permanece disponível durante a sessão.
- Pausa real e leitura de estado no ponto, sem interromper a corrida com anúncio.
- Ao sair para segundo plano no Android, a corrida pausa automaticamente para não converter uma interrupção do sistema em dano.
- Menu com movimento reduzido (remove câmera/partículas/flash intensos), alto contraste e áudio opcional; ações importantes também têm texto, não só cor.
- HUD é sincronizado a 30 Hz durante a corrida e as malhas primitivas repetidas são cacheadas; decoração distante usa visibility range para reduzir custo no mobile.

### Pós-corrida

A tela de resultado separa:

- moedas que foram coletadas na pista;
- bônus de conclusão;
- primeira conclusão, nova estrela ou replay;
- XP ganho;
- novo recorde.

Isso evita que o jogador tenha de adivinhar por que o saldo mudou e facilita investigar inflação da economia.

### Missões e conquistas

A HUD agora lê o estado real salvo. Missões mostram `em andamento`, `resgatar` ou `resgatado`; o marco semanal fica separado do reset diário. A tela de conquistas diferencia conquista e badge e mostra o estado de cada item.

## Instrumentação local

`GameSave` mantém somente contadores anônimos no dispositivo, sem envio de rede:

- sessões e dias de login, com flags locais de retorno D1/D7/D30;
- tentativas, conclusões e falhas de fase, incluindo Endless;
- primeiras conclusões;
- tempo total de corrida, distância total e maior corrida;
- resgates diários, marco semanal e compras;
- moedas criadas/gastas, maior sequência de retorno e primeiro dia observado;
- eventos agregados de tutorial, controles, colisões e buckets de FPS (`fps_60_plus`, `fps_45_59`, `fps_below_45`).

Isso permite um primeiro diagnóstico em QA sem criar perfil remoto. Para uma versão comercial, o próximo passo é um provedor de telemetria com consentimento, política de privacidade, retenção limitada e eventos sem PII. O código local já usa nomes equivalentes a `tutorial_step`, `run_start`, `lane_change`, `hit_*`, `run_finish`, `daily_claim`, `weekly_claim`, `shop_purchase` e `fps_bucket`; `phase_unlock` e `load_time_bucket` continuam candidatos para uma camada de QA posterior.

## Métricas e critérios de decisão

Benchmarks públicos de mobile ajudam a contextualizar D1/D7/D30, mas não devem virar promessa ou meta universal. O jogo deve ser comparado primeiro consigo mesmo, por coorte de versão e aparelho.

| Área | Métrica | Sinal para agir |
|---|---|---|
| Onboarding | primeiro início → primeira conclusão; abandono antes de 70 m | hint ou fase inicial confusos |
| Dificuldade | tentativas por fase, falhas por obstáculo, taxa de nova estrela | pico de falha sem aprendizado |
| Progressão | estrelas por sessão, fase desbloqueada por coorte | requisito vira parede ou não tem valor |
| Economia | moeda criada por sessão, moeda gasta, saldo mediano por dia | saldo sem sink ou compra inalcançável |
| Retorno | sessões por jogador, retorno D1/D7/D30, missões concluídas | reduzir atrito; nunca adicionar punição |
| Performance | FPS p50/p95, frame time, memória, tempo até primeira corrida | reduzir partículas/draw calls no Android médio |
| Acessibilidade | tamanho de toque, contraste, leitura sem cor, vibração/áudio opcional | qualquer ação que dependa apenas de cor/som |

Como referência contextual, a revisão considerou benchmarks públicos de GameAnalytics, relatórios de live ops da PocketGamer e Sensor Tower, recomendações de desempenho Android e diretrizes de onboarding/acessibilidade da Apple. Odds de itens aleatórios em lojas também foram verificadas nas regras da Apple e Google Play; o projeto não adiciona esse modelo.

## Pendências obrigatórias antes de publicação

1. Rodar projeto no Godot 4.x em editor e modo headless; validar parser, importação GLTF, colisões, input touch e exportação Android 8+.
2. Medir FPS, frame time, memória, draw calls e carregamento em pelo menos três aparelhos Android, incluindo um modelo médio; os buckets locais ajudam a localizar uma queda, mas não substituem o profiler.
3. Fazer playtest moderado com onboarding e fases 1, 9, 20, 40 e 50; registrar compreensão das faixas, tempo até a primeira vitória e percepção de justiça.
4. Testar backup/recuperação interrompendo uma gravação e migrando um JSON da versão anterior, incluindo a nova migração v3.
5. Testar zoom/fonte grande, modo sem áudio, movimento reduzido, alto contraste, toque com uma mão e ausência de feedback exclusivamente cromático.
6. Calibrar preços e recompensas somente após observar moeda criada versus moeda gasta e taxa de conclusão; não usar dificuldade artificial para vender vantagem.
7. Executar `python3 tools/audit_balance.py` junto do preflight em cada ajuste de curva; o script é uma barreira matemática, não uma substituição de jogadores.

## Referências públicas consultadas

- [GameAnalytics — Mobile & PC Gaming Benchmarks 2026](https://www.gameanalytics.com/reports/2026-mobile-pc-gaming-benchmarks)
- [PocketGamer — Live ops trends](https://pocketgamer.biz/2026-live-ops-trends-templatisation-personalisation-and-ai/)
- [Sensor Tower — Live ops strategies](https://sensortower.com/blog/top-grossing-mobile-games-live-ops-strategies-2025-report)
- [Android Developers — Games performance guides](https://developer.android.com/games/guides)
- [Apple — App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- [Google Play — Payments policy](https://support.google.com/googleplay/android-developer/answer/9858738)
- [Apple — Onboarding HIG](https://developer.apple.com/design/human-interface-guidelines/onboarding)
- [Apple — Accessibility HIG](https://developer.apple.com/design/human-interface-guidelines/accessibility)
