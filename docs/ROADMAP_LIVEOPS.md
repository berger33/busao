# Roadmap LiveOps — 90 dias pós-lançamento

Premissa: economia atual (soft R$ + Rubi, baú diário, evento semanal,
sinks reroll/skins) + auditoria de retenção D0–D30 implementada.

## Dias 1–14 — estabilizar
- Acompanhar Crashlytics: meta 0 crash/ANR no Test Lab antes de abrir 100%.
- Funil D0: tutorial → F1–F5 → review (10 clears + 2º dia). Alvo: D1 ≥ 40%.
- Validar ledger de billing em produção (reconcile, zero duplicata, zero reembolso).
- UMP: taxa de opt-in personalizado por região; NPA como fallback.

## Dias 15–45 — reter
- 1º evento semanal temático ( concurso “Semana do Motoboy” já codado).
- Rotação de loja + reroll: medir `sink_rerolls`/`sink_skins` (`audit_balance.py`).
- Push com valor de balance (já implementado): D1/D7/D30 por coorte.
- A/B via Remote Config: preço Maria 180 vs 150; review 10 vs 8 clears.

## Dias 46–90 — monetizar com respeito
- Starter pack: conversão D0 (meta ≥ 2%); Pack S cruzando Maria.
- Rewarded: revive 1× + 2× moedas; interstitial segue 1/2 derrotas.
- Sazonal: pista/jingle de festa junina (pipeline de áudio procedural pronto).
- Validação servidor-side de receipts (fecha M7 de verdade).

## Métricas de saúde (semanal)
`D1/D7/D30` · `first_clears` médio · `coins_earned/spent` · `shop_purchases` ·
`chest_claims` · `review_requests` × avaliação média · crash-free %.

Tudo já instrumentado via `GameSave.record_event()` + `metrics/event_counts`.
