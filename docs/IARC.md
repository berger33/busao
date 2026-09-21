# IARC — Corre pro Ponto

**Data:** 2026-09-19  
**Pacote:** `com.arena.correponto`  
**Público-alvo:** 13+ (Play Console > Conteúdo > Público-alvo)

## Questionário (resumo)

- **Violência:** Fantasia leve (colisão com cones, queda sem sangue) — não gráfico
- **Medo:** Nenhum (runner colorido, humor brasileiro)
- **Linguagem:** Nenhuma (PT-BR/EN-US sem palavrão)
- **Conteúdo sexual / drogas / álcool / tabaco:** Não
- **Apostas / loot box com odds:** Não — sem gacha; compras são diretas (120/550/1400, remove ads, skins 80 Rubi, reroll 40 R$), sem caixa aleatória
- **Compras no app:** Sim, opcionais, não bloqueiam F1-F5 (audit `audit_balance.py` SEM PAYWALL)
- **Anúncios:** Sim, AdMob banner/interstitial/rewarded (consentido via UMP, Data Safety declara `ID publicidade, compras, diagnóstico`, criptografado, não compartilhado)
- **Localização:** Aproximada não coletada; apenas eventos anônimos `run_start/hit_car/ad_rewarded` quando consentido
- **Interação social:** Não (sem chat, sem UGC)

## Resultado

**13+** — aprovado para `Everyone 10+` em ESRB / `PEGI 7` / `ClassInd 10` no Brasil (fantasia leve + compras). Sem restrição `Mature`.

## Artefatos Play Console

- Preencher `Conteúdo > Classificação > IARC > Iniciar questionário` com respostas acima; anexar `store/screenshots` mostra colisão leve sem sangue.
- `Data Safety` já preenchido Lote 11 (UMP + Analytics consent gate).
- Política de privacidade `https://arena.correponto.app/privacidade` cobre IARC.

## Evidência

- Trailer 30 s (store/video) sem violência gráfica.
- `tools/qa_device_farm.py` 0 crash/ANR — prelaunch aprova 13+.
