# Auditoria — Primeira impressão, retenção D0–D30, balanceamento, economia e monetização

Data: 2026-09-27  
Branch auditada: `arena/01a0e45c-busao`  
Base local auditada: `7bcdf0b Estiliza texturas do ambiente sem ruido`  
Escopo: leitura estática de `scripts/`, `resources/game_balance.tres`, `project.godot`, dados autorais de fase e documentação de produto. Godot não está disponível no sandbox, então esta auditoria não substitui playtest real em aparelho.

---

## 1. Veredito executivo

**A mecânica principal está promissora e já tem boa base de retenção de curto prazo:** corridas de cerca de 1 minuto, objetivo claro de pegar o ônibus, 3 faixas, pulo/deslize/dash, 3 corações, retry rápido, fases autorais, personagens com habilidades, baú diário, missões, anúncios rewarded, billing e cloud save.

**Mas a versão atual ainda não está pronta para medir nem otimizar retenção/monetização real**, por quatro motivos críticos:

1. **Economia de produção está desligada por debug:** `starting_coins = 100000` e injeção de 100k no save tornam loja, IAP, daily, baú, rewarded e progressão econômica irrelevantes.
2. **Gates de estrelas são agressivos demais para D2–D7:** fase 20 exige 45★, ou 79% das estrelas possíveis até ali; fase 50/endless exige 120★, ou 82% das estrelas antes dela.
3. **Monetização rewarded existe, mas está concentrada só em derrota/vitória:** revive e 2× moedas são bons, mas não há ainda “ofertas rewarded de transição” em baú, gate, streak, loja ou mapa.
4. **Infra real ainda é mock-first:** Ads, Billing, Analytics, Push, Remote Config e Play Services estão bem desenhados como wrappers, mas precisam de plugin/SDK real e eventos por funil para soft-launch.

**Prioridade recomendada:** antes de mexer em conteúdo novo, corrigir P0 de economia/UX/ads e só então rodar playtest/soft-launch.

---

## 2. Snapshot do sistema atual

### 2.1 Core loop

1. Jogador abre menu.
2. Toca em **JOGAR AGORA** ou mapa.
3. Entra em contagem 3-2-1.
4. Corre em 3 faixas até o ponto do ônibus.
5. Evita obstáculos com troca de faixa, pulo, deslize e dash.
6. Coleta moedas/itens.
7. Vitória: ganha estrelas, moedas, XP, possíveis conquistas e oferta de 2× moedas via rewarded.
8. Derrota: pode receber revive via rewarded; se desistir, resultado/retry e possível interstitial após derrota.
9. Fora da corrida: loja, mapa, desafios diários, baú diário, conquistas, compras IAP.

### 2.2 Conteúdo e ritmo

Dados extraídos de `LevelData`:

| Faixa de fases | Distância | Velocidade autoral | Prazo | Tempo médio de rota | Folga média | Obstáculos médios | Moedas médias |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1–5 | 224–364 m | 5.5–6.2 m/s | 55–69 s | 51.9 s | 11.9 s | 9.0 | 9.6 |
| 6–10 | 364–420 m | 6.2–6.5 m/s | 70–75 s | 60.5 s | 11.7 s | 10.8 | 9.0 |
| 11–20 | 392–504 m | 6.6–7.5 m/s | 71–76 s | 62.2 s | 10.7 s | 10.8 | 9.8 |
| 21–30 | 448–532 m | 7.4–8.0 m/s | 72–78 s | 64.6 s | 10.1 s | 11.4 | 9.0 |
| 31–40 | 476–560 m | 7.8–8.3 m/s | 73–77 s | 64.3 s | 10.2 s | 12.2 | 9.6 |
| 41–50 | 504–616 m | 8.2–9.0 m/s | 72–76 s | 65.7 s | 8.6 s | 12.7 | 9.6 |

**Leitura:** a duração de fase está boa para mobile. A curva de prazo também é saudável: começa generosa e aperta no fim. O risco não é duração; é repetição, gates e economia.

---

## 3. Primeira impressão — D0, primeiros 5 minutos

### Pontos fortes

- **Tema forte:** “perder o busão” é simples, brasileiro e imediatamente compreensível.
- **CTA principal claro:** menu tem botão grande de jogar.
- **Objetivo no início da fase 1:** `_start_run()` mostra “PEGUE O BUSÃO!” e “alcance o ponto a tempo”.
- **Tutorial melhorou:** ordem atual é faixa → pulo → deslize → dash, que é mais correta para sobrevivência.
- **Corrida curta:** excelente para aprender por tentativa.
- **Feedback de derrota bom:** informa se faltavam metros/segundos ou se acabou o fôlego.
- **Retry rápido:** ótimo para D0.

### Problemas que afetam D0

| Problema | Impacto | Evidência |
|---|---|---|
| Menu inicial com muitos botões/toggles | Pode confundir antes da 1ª corrida | menu exibe Play, Mapa, Loja, Conquistas, Desafios, idioma, som, movimento, contraste, daltonismo, vibração, gesto |
| Economia debug dá 100k moedas | Mata descoberta e desejo da loja | `resources/game_balance.tres:19`, `scripts/save_data.gd:241-249` |
| Tutorial ainda é texto, não treino validado | Jogador pode ignorar e “passar” sem aprender | `tutorial_seen` vira true após distância; não há checagem de gesto correto |
| Tela “Como jogar” tem copy incorreta | Diz “dash + invencibilidade”, mas dash não dá imunidade | `hud_3d.gd:641`, `game_3d.gd:1717-1720` |
| Baú/desafios/loja aparecem antes do jogador entender valor | Dilui foco da primeira sessão | menu D0 abre todos os sistemas |

### Recomendação D0

- **Progressive disclosure:** na primeira instalação, mostrar só “JOGAR AGORA”, “Como jogar” e configurações essenciais. Liberar Loja após fase 2–3, Desafios após primeira vitória, Conquistas após primeira conquista.
- **Tutorial interativo curto:** fase 1 deve exigir uma troca de faixa, um pulo e um deslize em trechos seguros antes de contar `tutorial_seen`.
- **Sem interstitial antes de 3–5 corridas:** manter D0 limpo; usar apenas rewarded opt-in se o jogador falhar.
- **Primeira oferta de monetização:** depois da fase 3 ou da primeira falha relevante: “Dobre as moedas” ou “Pack Motoboy” se faltar pouco para comprar o primeiro personagem.

---

## 4. Retenção D0–D30 — auditoria por dia

### Leitura geral

| Janela | Estado atual | Risco | Melhor alavanca |
|---|---|---|---|
| D0 | Boa base, mas menu/economia atrapalham | Confusão + economia debug | onboarding + remover 100k |
| D1 | Tem baú, streak, daily e push mock | Retorno pouco guiado | calendário D1–D7 visível |
| D2–D3 | Jogador chega perto do 1º gate | Gate 45★ e repetição | aliviar gate/assistência |
| D4–D6 | Conteúdo precisa variar | Sem eventos fortes por dia | missões/tarefas temáticas |
| D7 | Streak e semanal existem | recompensa semanal fraca | marco D7 com Rubi/personagem/desconto |
| D8–D14 | campanha sustenta, mas variedade cai | D14 termina campanha para engajado | endless antecipado + ranking |
| D15–D30 | falta plano forte de liveops | churn pós-campanha | temporada, ranking, passe/eventos |

### Plano diário recomendado

| Dia | Estado provável do jogador | Gancho atual | Risco atual | Recomendação |
|---|---|---|---|---|
| D0 | Aprende controles, joga 3–8 fases | tutorial, primeiras estrelas, loja | 100k mata economia; menu cheio | onboarding guiado + first purchase hint sem pressão |
| D1 | Retorna para continuar campanha | baú diário, daily, streak | retorno não tem tela “bem-vindo de volta” forte | modal curto: baú + objetivo do dia + personagem quase liberado |
| D2 | Já entende mecânica | daily/baú/campanha | começa cobrança por estrelas | missão de maestria com prêmio visível, sem gate duro ainda |
| D3 | Pode estar nas fases 10–18 | novidade de obstáculos/cenário | risco de bater no gate 45★ | antecipar aviso do gate e oferecer caminho alternativo |
| D4 | Busca variedade | capítulos/cenários | rotina começa a repetir | evento diário: “dia da chuva”, “dia do motoboy”, reward extra |
| D5 | Precisa de meta de fim de semana | weekly 2500 m | weekly é só 100 moedas | recompensa semanal escalonada + badge/skin temporária |
| D6 | Véspera de streak D7 | streak em andamento | sem proteção de streak | oferecer “congelar streak” via rewarded ou Rubi |
| D7 | Marco de hábito | +100 moedas a cada 7 dias | prêmio fraco para uma semana | D7: 250 moedas + 10 Rubi + desconto/personagem em destaque |
| D8 | Começo da 2ª semana | campanha | “mais do mesmo” | abrir endless beta após fase 20/gate 1 |
| D9 | Explora personagens | loja | duplicate effects sem diferenciação clara | classificar personagens por arquétipo: velocidade, escudo, moeda, controle |
| D10 | Pode bater no gate final intermediário | estrelas | grind se faltam bônus | “rota recomendada para 3★” + rewarded para dica/assistência |
| D11 | Fadiga leve | dailies | daily completa em 1 corrida | daily em tiers: 250/600/1200 m |
| D12 | Procura novidade | cenário | mecânica já estabilizou | desafio com mutador: sem dash, chuva, moedas raras |
| D13 | Pré-D14 | semanal/streak | recompensa previsível | teaser da próxima semana/evento |
| D14 | Engajado pode estar fechando campanha | campanha + loja | pós-jogo fraco | ranking endless e metas de coleção |
| D15 | Pós-campanha parcial | completar estrelas | gate 120★ pode frustrar | liberar endless antes do 120★; 120★ vira recompensa, não requisito |
| D16 | Coleção/personagens | moedas | catálogo pode ficar caro sem meta emocional | missões de personagem: “corra 1000 m com Maria” |
| D17 | Dailies repetem | baú/daily | rotina sem novidade | calendário D8–D30 com variação visual e prêmio mensal |
| D18 | Busca competição | best times local | sem ranking social real | Play Games leaderboard por fase/endless |
| D19 | Retenção depende de meta pessoal | estrelas | completismo sem vitrine | álbum de conquistas/skins com progresso visível |
| D20 | Pode converter se envolvido | loja/IAP | coin packs sem urgência se economia debug/alta | oferta personalizada: falta X para personagem Y |
| D21 | Terceiro marco semanal | streak/weekly | recompensa igual D7 | marco D21 maior: Rubi + cosmético |
| D22 | Pós-hábito | liveops | sem temporada | temporada de 30 dias com ranking e cosmético |
| D23 | Reengajamento | push mock | push nativo ausente | push de baú pronto/evento/streak em risco |
| D24 | Coleção final | personagens | muitos personagens com efeitos repetidos | upgrades cosméticos/persona-specific challenges |
| D25 | Long tail | endless/local best | sem leaderboard | ranking semanal resetável |
| D26 | Monetização tardia | remove_ads/IAP | pouco valor se anúncios leves | bundle “remove ads + starter + Rubi” |
| D27 | Risco alto de churn | dailies | daily previsível | evento de fim de mês, recompensa única |
| D28 | Marco mensal | streak | prêmio semanal plano | D28: grande baú mensal + cosmetic/skin |
| D29 | Pré-D30 | completismo | sem meta de D30 | teaser nova temporada/personagem |
| D30 | Decisão de permanecer | coleção/endless | sem conteúdo social/liveops | temporada, ranking, desafios semanais e roadmap de conteúdo |

---

## 5. Progressão e balanceamento

### O que está bom

- **Fases autorais:** 50 fases existem e usam distância/obstáculos/moedas definidos.
- **Duração:** 55–78 s de prazo por corrida é ótimo para mobile.
- **Estrelas por união de objetivos:** o save guarda objetivos separados; isso reduz frustração porque o jogador pode conquistar “sem dano” e “moedas” em tentativas diferentes.
- **Personagens têm efeitos reais:** velocidade, escudo, ímã, pulo, coração, dash, tempo etc.
- **Impacto adiciona penalidade de tempo:** boa ligação entre habilidade e tema do ônibus.

### Problemas de progressão

#### 5.1 Gate da fase 20: muito duro para D2–D4

- `unlock_chapter_stars = 45`.
- Fase 20 tem índice 19 e exige 45★ + clear da fase anterior.
- Antes dela há 19 fases × 3★ = 57★ possíveis.
- 45/57 = **79% das estrelas possíveis**.

Isso cobra desempenho de completista muito cedo. Para retenção casual, o ideal é o gate cobrar algo como 60–70% das estrelas disponíveis, ou aceitar alternativa.

**Recomendação:** reduzir para 36–40★ ou adicionar alternativa:

- passe de capítulo por moedas;
- passe por rewarded ad;
- assistência após 5 falhas;
- evento “2× estrelas bônus” temporário;
- “treino de rota” que ajuda a completar a estrela faltante.

#### 5.2 Gate do endless: modo de retenção trancado tarde demais

- Endless só libera no fim: `endless_unlock_phase = 49` e `unlock_endless_stars = 120`.
- Antes da fase 50 há 49 fases × 3★ = 147★.
- 120/147 = **82% das estrelas possíveis**.

Endless é a ferramenta natural de D7–D30, mas está atrás do fim da campanha. Isso reduz retenção tardia.

**Recomendação:** abrir endless “beta” depois da fase 20 ou 25. O gate de 120★ pode virar “Endless Pro”, ranking competitivo ou recompensa cosmética.

#### 5.3 Curva de novidade

A curva de distância/velocidade está boa, mas após as mecânicas principais o jogo depende de recombinações/cenário. Para D7–D30, precisa de pelo menos uma destas camadas:

- mutadores semanais;
- ranking endless;
- desafios por personagem;
- missões com restrição;
- eventos temporários;
- recompensas cosméticas por temporada.

---

## 6. Economia

### 6.1 Fontes de moeda soft

| Fonte | Valor atual aproximado | Comentário |
|---|---:|---|
| Moedas da pista | ~9–12 por fase autoral | São creditadas imediatamente em `_collect()` |
| First clear | R$ 35–200 conforme fase/estrelas | Soma catálogo: R$ 5.425 a R$ 6.325, sem contar moedas da pista |
| Replay | R$ 8 + estrela nova se houver | Bom para não inflar replay |
| Daily | 25 + 35 + 45 = R$ 105/dia | Forte para hábito; talvez completa rápido demais |
| Weekly | R$ 100/semana | Fraco para marco semanal |
| Baú diário | R$ 25–250 + Rubi 1–10 | Boa direção; precisa tela de calendário |
| Streak 7 dias | R$ 100 | Fraco para 7 dias |
| Conquistas/badges | 20–150 | Bom payoff |
| Level up | Existe, mas com possível duplicidade | Ver P0/P1 abaixo |
| IAP coin packs | 300/1000/2200 | Só vale após remover 100k |

### 6.2 Sinks de moeda soft

| Sink | Custo total |
|---|---:|
| Personagens pagos | R$ 8.940 |
| Itens | R$ 1.170 |
| Reroll visual | R$ 40 por uso |
| Total base sem reroll | R$ 10.110 |

Com economia de produção, a relação fonte/sink pode funcionar: campanha + dailies + semanais sustentam 3–4 semanas de coleção. **Com 100k debug, tudo quebra.**

### 6.3 Rubi / hard currency

Rubi existe e é ganho por baú e nível. O custo real da skin extra foi reduzido para 15 Rubi em `EconomyManager`, mas a HUD e feedback ainda usam 80 Rubi.

- Custo real: `SKIN_EXTRA_COST_RUBI := 15`.
- HUD habilita botão só com `rubi >= 80`.
- Feedback diz “-80 Rubi” / “Precisa 80 Rubi”.

**Impacto:** o jogador pode ter Rubi suficiente no backend, mas a UI não permite comprar. Isso é bug de monetização/retenção.

### 6.4 P0 econômico

1. Reverter `starting_coins = 100000` para 40.
2. Remover bloco de injeção de 100k no save.
3. Alinhar skin extra: 15 Rubi em HUD, feedback e lógica.
4. Conferir se level-up não está pagando duas vezes: `GameSave.add_xp()` já paga moedas/Rubi e `_apply_levelup_rewards()` também adiciona recompensa.
5. Separar build de teste e build de produção por flag/feature toggle, nunca por valor commitado em `game_balance.tres`.

---

## 7. Monetização — anúncios e IAP

### 7.1 Estado atual de anúncios

| Formato | Implementado? | Onde | Avaliação |
|---|---|---|---|
| Banner | Sim | menu/mapa/loja/desafios/conquistas | ok, mas baixa receita |
| Interstitial | Sim | pós-derrota, 1 a cada 2 derrotas, cooldown 90s | bom para não punir vitória |
| Rewarded revive | Sim | ao perder/ficar sem corações | muito bom para retenção e receita |
| Rewarded 2× moedas | Sim | tela de vitória | bom, mas pode ser mais visível |
| Rewarded baú/daily | Não | — | oportunidade alta |
| Rewarded gate/skip | Não | — | oportunidade alta se bem dosada |
| Rewarded loja | Não | — | oportunidade média/alta |

### 7.2 “Rewarded video nas trocas de telas” — recomendação de design

Evitar forçar vídeo em toda troca de tela. Para retenção, o melhor é **oferta rewarded contextual e opt-in** durante transições naturais:

| Transição | Oferta rewarded sugerida | Limite |
|---|---|---|
| Vitória → Próxima fase/mapa | 2× bônus da corrida | 1× por vitória |
| Derrota → Retry/mapa | Revive ou “tentar de novo com +1 coração” | 1× por corrida |
| Menu → Desafios | Dobrar recompensa de uma daily já completa | 1–2×/dia |
| Desafios → Menu | Abrir segundo baú pequeno | 1×/dia |
| Mapa bloqueado por estrelas | Passe temporário/assistência por anúncio | 1× por gate/dia |
| Loja sem moedas | “Ganhe R$ 40 agora” | 3×/dia com cooldown |
| Streak em risco | Congelar streak por anúncio | 1×/semana |
| Antes de evento semanal | Boost de moedas por 15 min | 1×/dia |

### 7.3 Interstitial

O interstitial atual pós-derrota é razoável. Mas para monetizar em transições sem destruir retenção:

- não mostrar interstitial nos primeiros 3–5 runs da instalação;
- nunca mostrar imediatamente antes da corrida;
- nunca mostrar depois de compra/IAP;
- limitar a 1 interstitial a cada 2–3 derrotas, 90–120 s de cooldown;
- usar Remote Config real para `ad_freq` e `ad_interstitial_cooldown`.

Hoje `RemoteConfig` define `ad_freq`, mas a lógica usa fixo `run_count % 2`.

### 7.4 IAP

Catálogo atual:

| Produto | Preço | Conteúdo | Avaliação |
|---|---:|---|---|
| `starter_pack` | R$ 3,90 | Motoboy + 300 moedas | melhor 1ª compra |
| `remove_ads` | R$ 9,90 | remove banner/interstitial; rewarded continua | bom |
| `coin_pack_s` | R$ 4,90 | 300 moedas | desbloqueia 1º personagem/itens |
| `coin_pack_m` | R$ 14,90 | 1000 moedas | ok |
| `coin_pack_l` | R$ 29,90 | 2200 moedas | ok |

**Problema:** com 100k debug, nenhum produto tem valor. Depois de corrigir:

- ofertar starter pack quando o jogador já entende personagem, idealmente após fase 3–5;
- bundle recomendado: “Starter do Ponto” = Motoboy + 300 moedas + sem anúncios por 48 h ou desconto de remove_ads;
- `remove_ads` deve prometer exatamente “sem banners/interstitial; rewarded opcional continua”; o código já segue isso;
- considerar pacote de Rubi pequeno se Rubi virar sink importante, mas só após estabilizar a economia soft.

### 7.5 Compliance e receita

- Ads usam UMP e NPA por padrão, bom para segurança.
- `TAG_FOR_UNDER_AGE_OF_CONSENT := true` reduz inventário/receita se o jogo não for direcionado a menores. Deve ser decisão de classificação/IARC, não default permanente.
- Analytics está preso ao consentimento de ads; para produto, talvez separar consentimento de analytics essencial/first-party do consentimento de anúncios personalizados.

---

## 8. Métricas obrigatórias para soft-launch

Sem telemetria real, D0–D30 vira palpite. Eventos mínimos:

### Funil D0

- `install_open`
- `session_start` com `days_since_install`
- `tutorial_step_view`
- `tutorial_step_success`
- `run_start` com `phase_index`, `attempt_number`
- `run_finish` com `success`, `stars`, `coins`, `hits`, `duration`, `fail_reason`
- `first_clear`
- `screen_view`
- `shop_view`

### Retenção/progressão

- `phase_unlocked`
- `gate_blocked` com `stars_have`, `stars_need`, `phase_index`
- `daily_claim`
- `weekly_claim`
- `daily_chest_claim`
- `streak_day`
- `endless_unlocked`
- `endless_start/end`

### Monetização

- `ad_offer` com placement
- `ad_show`
- `ad_complete`
- `ad_fail`
- `ad_reward_granted`
- `iap_view`
- `iap_attempt`
- `iap_success`
- `iap_fail`
- `remove_ads_owned`
- `starter_pack_owned`

### Métricas-alvo iniciais

| Métrica | Alvo inicial razoável |
|---|---:|
| D1 | 35–45% |
| D3 | 20–28% |
| D7 | 10–18% |
| D14 | 6–12% |
| D30 | 3–8% |
| Tutorial completo | >85% |
| Fase 1 clear | >75% |
| Fase 3 clear | >55% |
| Rewarded opt-in em vitória | 25–45% |
| Rewarded opt-in em revive | 20–40% dos elegíveis |
| Conversão IAP D7 | 1–3% no soft-launch |

---

## 9. Achados técnicos prioritários

### P0 — bloquear antes de soft-launch

1. **Remover economia debug 100k**
   - `resources/game_balance.tres:19`
   - `scripts/save_data.gd:241-249`
   - Impacto: invalida retenção, loja, IAP, rewarded e economia.

2. **Corrigir custo de skin extra na UI**
   - Real: `SKIN_EXTRA_COST_RUBI := 15`.
   - UI/feedback: ainda exige 80.
   - Arquivos: `economy_manager.gd`, `hud_3d.gd`, `game_3d.gd`.

3. **Corrigir recompensa dupla de level-up**
   - `GameSave.add_xp()` já paga moedas/Rubi.
   - `_apply_levelup_rewards()` paga de novo após `add_xp()`.
   - Decidir fonte única: idealmente `GameSave.add_xp()` retorna resumo, e `game_3d.gd` apenas exibe.

4. **Corrigir hitbox do botão “DESISTIR” na tela de revive**
   - Input usa y=690; botão desenhado y=720.
   - Pode causar toque perdido e frustração no momento mais sensível.

5. **Corrigir copy de dash**
   - “dash + invencibilidade” é falso; dash é velocidade sem imunidade.

### P1 — alta retenção/monetização

1. Reduzir gate 45★ para 36–40★ ou criar passe alternativo.
2. Liberar endless antes do fim e adicionar ranking.
3. Criar calendário D1–D7 visível com prêmio crescente.
4. Adicionar rewarded de baú/daily/gate/loja.
5. Progressive disclosure no menu D0.
6. Implementar plugins nativos reais de Ads/Billing/Analytics/Push antes de qualquer decisão de produto.
7. Usar Remote Config de verdade para `ad_freq`, `ad_cooldown`, rewards e preços.

### P2 — D14–D30

1. Temporadas semanais/mensais.
2. Leaderboards Play Games para endless e best time.
3. Desafios por personagem.
4. Mutadores semanais.
5. Vitrine de coleção e badges com progresso.
6. Streak freeze por rewarded/Rubi.

---

## 10. A mecânica do jogo está ok?

**Sim, o núcleo está ok.** O jogo tem uma fantasia simples, controles compatíveis com mobile, duração correta, feedbacks, objetivos e uma estrutura de conteúdo suficiente para validar D0–D7.

**Pode e deve melhorar para D7–D30:**

- dash precisa ter comunicação clara;
- tutorial precisa validar ação, não só exibir texto;
- gates precisam ser menos punitivos ou ter alternativa;
- endless/ranking precisa aparecer mais cedo;
- daily/weekly precisam parecer calendário/hábito, não apenas lista;
- monetização deve ser contextual, opt-in e ligada ao momento emocional da tela.

---

## 11. Plano recomendado de execução

### Sprint 1 — deixar a economia auditável

- [ ] Reverter 100k para produção.
- [ ] Remover injeção debug do save.
- [ ] Criar flag dev para saldo infinito apenas em build debug.
- [ ] Corrigir Rubi 15 vs 80.
- [ ] Corrigir level-up duplicado.
- [ ] Corrigir botão desistir do revive.
- [ ] Corrigir copy de dash.

### Sprint 2 — retenção D0–D7

- [ ] Menu D0 progressivo.
- [ ] Tutorial interativo validado.
- [ ] Calendário D1–D7.
- [ ] Gate 45★ com alternativa.
- [ ] Rewarded daily/baú/gate.
- [ ] Primeiro offer starter pack após fase 3–5.

### Sprint 3 — D7–D30 e monetização real

- [ ] Endless após fase 20/25.
- [ ] Ranking endless.
- [ ] Temporada semanal.
- [ ] Push nativo: baú pronto, streak em risco, evento semanal.
- [ ] Analytics/Firebase real com funis.
- [ ] A/B via Remote Config real.

---

## 12. Conclusão

O jogo já tem bastante “largura” de sistema: campanha, personagens, loja, IAP, ads, baú, daily, weekly, streak, achievements, XP, cloud, push e analytics. O próximo salto não é adicionar mais sistemas; é **afinar a profundidade e remover inconsistências que impedem retenção/monetização real**.

A ordem correta é:

1. **corrigir economia debug e bugs de UX monetizada;**
2. **reduzir fricção de gate;**
3. **abrir endless/ranking antes;**
4. **transformar rewarded em ofertas de transição opt-in;**
5. **medir tudo com analytics real.**

Se isso for feito, a base tem chance boa de performar como casual runner brasileiro com D1 saudável e monetização híbrida via rewarded + starter/remove_ads.
