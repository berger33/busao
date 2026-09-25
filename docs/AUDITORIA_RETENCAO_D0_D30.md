# AUDITORIA — Retenção do jogador e UX (D0 → D30)

Data: 2026-09-21. Escopo: código atual (`scripts/`, `resources/game_balance.tres`,
`docs/execucao/`). Método: leitura dos sistemas + cálculo da economia com os
valores de produção (ignorando a injeção de teste de 100k, que deve ser
revertida antes de qualquer leitura de retenção).

**Veredito em uma frase:** a *largura* dos sistemas de retenção é impressionante
(diárias, semanal, baú, streak, XP, conquistas, push, review, anúncios, cloud —
tudo existe); os vazamentos estão na *profundidade*: afinação de recompensas,
muros de progressão, onboarding e instrumentação de produção.

---

## 1. Resumo executivo — saúde por janela

| Janela | Veredito | Motor principal | Maior risco |
|---|---|---|---|
| D0 (1ª sessão) | 🟡 Bom, com atrito | Campanha + novidade mecânica | Tutorial, framing de objetivo, review precoce |
| D1 | 🟡 Fino | Progresso + 1ª compra | Pacote de retorno fraco (baú irrisório, streak sem prêmio) |
| D2–D3 | 🔴 Muro | Novas famílias até fase 18 | Gate de 45★ na fase 20 (79% das estrelas) |
| D7 | 🟡 Mediano | Semanal + evento + streak 100 | Sem calendário crescente, sem leaderboard |
| D14 | 🟡 Em risco | Capítulos/cenários | Mecânicas planas desde a fase 18 (32 fases de remix) |
| D30 | 🔴 Sem plano | Completismo (150★, coleção) | Sem conteúdo novo, endless trancado no fim, sem social |

**Top 5 alavancas (maior impacto esperado):**
1. Instrumentação real em produção (analytics + push nativo) — sem isso,
   nada aqui é mensurável.
2. Válvula no muro das 45★ (fase 20).
3. Dar payoff aos sistemas mortos: XP/nível, conquistas e Rubi.
4. Reordenar o tutorial + declarar o objetivo antes da 1ª corrida.
5. Abrir o endless mais cedo e/ou adicionar ranking — modo de retenção
   desperdiçado no fim do jogo.

---

## 2. D0 — primeira sessão (minuto a minuto)

### O que funciona ✅
- Cold start < 2,8 s com loading + dica (`game_3d.gd:294`).
- Menu abre com CTA dominante "JOGAR AGORA" (`hud_3d.gd:108`).
- Corridas de ~1 min (224–616 m a 5,5–9 m/s + contagem 2,4 s): chunk ideal.
- Retry rápido e próximo passo claro (MAPA / TENTAR DE NOVO / PRÓXIMA FASE).
- Sem energia: binge liberado; pausa automática ao perder foco.
- Derrota informa causa com números ("faltavam X m (Y s)") — reduz
  frustração cega.
- Estrelas por união entre tentativas (`phase_goals`): não exige run perfeita.

### Pontos de melhoria 🔧
1. **Objetivo nunca é declarado antes da 1ª corrida.** O jogador lê "rua à
   esquerda • calçadas à direita" (layout), mas não "pegue o ônibus antes
   que ele parta" (meta). Risco: correr sem entender o prazo na fase 1.
   *Fix barato:* 1 frase de objetivo no resumo/contagem da fase 1.
2. **Tutorial ensina na ordem errada** (`_update_tutorial_hint`):
   faixa → **dash** → pulo/deslize. Dash é ação avançada; pulo/deslize são
   sobrevivência. *Fix:* faixa → pulo/deslize → dash (após 1º clear?).
3. **Tutorial é texto corrido, sem gating.** Não há gesto obrigatório, momento
   de prática ou checagem de compreensão; `tutorial_seen` vira `true` aos
   70 m de qualquer jeito. Jogador distraído "passa" sem aprender.
4. **Menu D0 com 5 CTAs + toggles + text wall.** Mapa, loja, conquistas e
   desafios competem com JOGAR antes de qualquer contexto. *Fix:* progressive
   disclosure — loja/conquistas/desafios aparecem após a fase 1–3 (com
   badgets de novidade).
5. **Review após 3 first-clears** (`play_services_manager.gd:262`) ≈ 15 min
   de D0. Cedo e agressivo; pede avaliação antes de qualquer vínculo.
   *Fix:* D1+ ou marco (ex.: fase 10, 2º dia, após Baú+diárias).
6. **Toque = dash** pode gerar dashes acidentais (toque exploratório vira
   ação). Monitorar `event_counts`/reclamações; considerar zona de toque ou
   gesto distinto.
7. **Dica de derrota errada para fases autorais** (`hud_3d.gd`, tela de
   resultado): "Rua = mais obstáculos e mais moedas / Calçadas = leitura e
   atalhos" — mas nas 50 fases autorais os 3 corredores são calçada; não há
   moedas na "rua". Coaching enganoso após cada falha. *Fix urgente e barato.*

---

## 3. D1 — o retorno do dia seguinte

### O que existe
- Login diário com streak (`register_login`), baú diário, reset de diárias,
  push de "streak em risco" (mock-first), evento semanal rotativo.

### Pontos de melhoria 🔧
1. **Pacote D1 fraco.** Baú = 5–15 moedas + 1–3 Rubi (irrisório perto de um
   first-clear de ~45–60); streak só paga no 7º dia. O retorno D1 é movido
   quase só por "continuar a campanha". *Fix:* calendário D1–D7 crescente
   (ex.: D1 25 → … → D7 150 + Rubi), com o dia atual visível no menu.
2. **Push não existe em produção.** `PushManager` é mock-first; sem plugin
   nativo, não há win-back real (D1, streak em risco, baú pronto).
   É o maior gap infra de retenção junto com analytics.
3. **Sem "gancho de sessão":** nada diz "volte amanhã para X" (baú pronto,
   evento novo, loja rotativa). O evento semanal existe mas é discreto no
   mapa. *Fix:* banner de retorno + push de baú/evento.
4. **1ª compra (Maria 180 / Bia 240 / motoboy 260) é alcançável no D0–D1**
   (~3–5 first-clears a partir de 40 iniciais) — bom, MAS não há descoberta
   guiada da loja nem "faltam X para seu 1º personagem". *Fix:* hint
   pós-fase-3 ("você pode comprar a Maria!") + badge na loja.

---

## 4. D2–D3 — hábito se formando, muro à vista

### O muro das 45★ 🔴 (achado mais crítico de progressão)
- Fase 20 (índice 19) exige **45★ + clear da 19** (`save_data.gd:354`).
- Máximo possível até lá: 19 fases × 3★ = 57. **Exige 79% das estrelas**,
  ou seja, ~26 das 38 estrelas bônus (sem_dano + moedas).
- Estrela 1 ≈ clear (prazo é obrigatório); as bônus exigem runs limpas e
  rotas de moedas em fases que o jogador casual mal venceu.
- Para o jogador mediano, isso é um **muro de grind no D2–D4 sem válvula**:
  sem assistência, sem skip, sem "passe" alternativo.
- Opções (escolher 1–2):
  - Reduzir para ~36–40★ (63–70%) — mantém prestígio, destrava fluxo;
  - "Passe de capítulo": liberar com moedas (sink!) ou rewarded ad;
  - Evento "2× estrelas" de fim de semana;
  - Assistência opcional pós-N-falhas (M7 já previsto; antecipar o mínimo).
- Comunicação do muro é boa (mapa mostra "próximo marco", resultado mostra
  ★ acumuladas) — o problema é o número, não o aviso.

### Diárias: hábito sim, profundidade não
- Metas: 250 m + 10 moedas + 1 clean → 25/35/45 = **105 moedas/dia**.
- 250 m < 1 fase: a diária se completa em ~1 corrida. Ótimo para hábito,
  fraco para tempo de sessão; e 105/dia domina a economia (1 first-clear
  ≈ 45–60). *Fix:* tiers (250/600/1200 m) ou rotação de tipos
  (deslize ×N, sem dano em fase Y, moedas em fase Z).

---

## 5. D7 — semanal, streak e evento

### O que existe
- Semanal: 2500 m → 100 moedas (~5 fases). OK.
- Streak: 100 a cada 7 dias. Fraco e plano (ver §3.1).
- Evento semanal rotativo (ex.: semana_motoboy: bônus de moedas, +Rubi no
  baú, item em destaque) + push de streak. Direção certa, intensidade baixa.

### Pontos de melhoria 🔧
1. **Sem calendário de streak D1–D7** (o padrão-ouro do gênero). Implementar
   com recompensa crescente + marco D7 relevante (ex.: Rubi + personagem
   com desconto).
2. **Sem proteção de streak** (freeze/congelamento por anúncio ou Rubi).
   Perder 6 dias por 1 esquecimento é churn clássico.
3. **Sem ranking/competição.** Play Games existe, mas não há leaderboard de
   endless/distância/tempo verificado. Competição assíncrona é a alavanca
   D7–D30 mais barata do gênero.
4. Copy do push com valor fixo ("R$ 100") em vez do balance — trocar pelo
   valor canônico.

---

## 6. D14–D30 — fim de campanha e pós-jogo

### Curva de conteúdo
- Mecânicas novas param na fase 18 (caminhão/ônibus). **Fases 19–50 = 32
  fases de recombinação** (novidade via cenário/clima/multidão/capítulos).
  Capítulos a cada 5 fases aliviam, mas a sensação de "mais do mesmo"
  aparece ~D3–D5. Mitigações: mutators semanais, desafios com restrição
  ("só deslize"), fases-espelho de evento.
- Ritmo estimado: 50 fases × ~2–3 tentativas × ~1,5 min ≈ 4–6 h. Jogador
  diário de 20 min termina em ~2 semanas → **D14+ precisa de pós-jogo**.

### Pós-jogo atual (fino)
- 150★ (completismo), best-times por fase, coleção (~9,3k moedas ≈ 3–4
  semanas), ~10 conquistas, endless.
- **Endless trancado no fim** (índice 49 + 120★ = 82% das estrelas):
  o modo com maior potencial de retenção D7–D30 está atrás do muro final.
  *Fix:* abrir após a fase 20 (gate 1) como modo paralelo + ranking.
- Sem temporadas, sem social, sem pipeline de fases pós-50. Para D30+,
  definir live-ops mínimo: temporada de endless com ranking + desafio
  semanal ranqueado + 1 personagem/mês.

### Sistemas de progressão paralela — diagnóstico
| Sistema | Estado | Problema | Fix |
|---|---|---|---|
| XP/Nível (250 XP/nível) | 🔴 Morto | Sem recompensa de level-up (grep: zero hooks) | Moedas/Rubi por nível + fanfarra |
| Conquistas (~10) | 🔴 Quase morto | `award_achievement` não paga nada | 25–100 moedas por conquista + tela com resgate |
| Personagens (20) | ✅ Vivo | Habilidades todas implementadas ✅ | Comunicar duplicatas (4× velocidade etc. = visual) |
| Baú diário | 🟡 Fraco | 5–15 moedas irrelevantes | Escalar com streak (ex.: ×dia) |
| Rubi (hard) | 🔴 Quebrado | Skin 80 Rubi vs renda 1–3/dia = **27–80 dias/skin** | Custo 12–20 OU renda maior (streak/evento) |
| Sinks | 🟡 Rasos | Só reroll 40 + skins 80 | Passe de capítulo, freeze de streak, dobra-baú |
| Best-times | 🟡 Órfão | Guardado, sem vitrine | Fantasma/ranking por fase |

---

## 7. Economia da retenção (números de produção)

- Início: 40 moedas. First-clear típico: ~30 base + 3×fase + 5×★ + moedas
  da pista ≈ **45–70/corrida** no início.
- 1ª compra (Maria 180): **~3–5 clears** ✅ ritmo D0 correto.
- Catálogo total ≈ 9,3k; campanha paga ~2,5–3k em first-clears → resto via
  diárias (105/dia) + semanal (100) + replays → **coleção ≈ 3–4 semanas** ✅.
- Diárias dominam a renda (€105/dia ≈ 2 first-clears) — intencional para
  hábito, mas achata o incentivo a progredir. Considerar bônus de
  first-clear crescente por capítulo.
- ⚠️ Tudo acima vale **após reverter a injeção de 100k** (`save_data.gd:174`,
  `game_balance.tres`). Com 100k, loja/streak/diárias são irrelevantes e
  nenhum teste de retenção é válido.

---

## 8. Instrumentação — o gap meta 🔴

- `retention_flags` (d1/d7/d30) e `event_counts` existem, mas **só locais**.
- Firebase/GA/Crash são **mock-first**: em produção, não há funil por fase,
  taxa de conclusão, fonte de churn, funil de loja ou D1/D7/D30 reais.
- Sem funil por fase, o muro das 45★ e qualquer spike de dificuldade são
  invisíveis. **Prioridade máxima antes/depois do soft-launch:**
  `run_start/run_finish/run_fail + phase_index`, `first_clear`, `gate_block`,
  `shop_view/purchase`, `daily_claim`, `chest_claim`, `streak_day`,
  `review_prompt/accept`, `tutorial_step/complete`, `session_start` com
  `days_since_install`.

---

## 9. Backlog priorizado

### P0 — crítico (antes de qualquer leitura de retenção)
- [ ] Reverter economia de teste (100k → 40) — pendência já registrada.
- [ ] Corrigir dica de derrota (rua × calçada) para fases autorais.
- [ ] Mover review para D1+/marco (fase 10 ou 2º dia).
- [ ] Plano para push nativo (plugin) — pelo menos streak/baú/D1 win-back.
- [ ] Plano para analytics real (funis mínimos do §8).

### P1 — alto impacto
- [ ] Válvula no gate 45★ (reduzir e/ou passe alternativo).
- [ ] Tutorial: objetivo declarado + ordem (pulo/deslize antes de dash).
- [ ] Recompensa de level-up (XP) + recompensa de conquistas.
- [ ] Rebalance Rubi (custo 12–20 ou renda maior).
- [ ] Calendário de streak D1–D7 + freeze de proteção.
- [ ] Descoberta guiada da loja (hint pós-fase-3 + badge).
- [ ] Progressive disclosure no menu D0.

### P2 — médio (D7–D30)
- [ ] Abrir endless após fase 20 + leaderboard.
- [ ] Tiers/rotatividade nas diárias.
- [ ] Ranking Play Games (endless, tempos).
- [ ] Mutators/desafios semanais para variedade pós-fase-18.
- [ ] Definir live-ops mínimo pós-50 (temporadas, personagem/mês).
- [ ] Revisar tap=dash (toques acidentais).

## 10. O que está genuinamente bom (preservar)
Cold start rápido • runs de ~1 min • retry imediato • sem energia • meta
legível sem som • estrelas por união • causa de derrota com números •
revive/2× rewarded • auto-pause • cloud save • acessibilidade •
20 personagens com habilidades reais • breadth completa de sistemas.
