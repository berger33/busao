# Política de Privacidade — Corre pro Ponto

**Última atualização:** 2026-09-19  
**Controlador:** Arena (suporte@arena.correponto.app)  
**URL pública (Play Console):** `https://arena.correponto.app/privacidade`

## Resumo LGPD / GDPR

Coletamos **apenas quando você consente** (UMP — Google User Messaging Platform). Sem consent, nenhum dado sai do aparelho (mensuração fica local em `user://corre_pro_ponto.json`).

### O que coletamos (quando consentido)

- **ID de publicidade** (AdMob) — para exibir anúncios relevantes (banner, interstitial, rewarded). Desative em Configurações > Google > Anúncios.
- **Compras** (Play Billing) — para creditar pacotes 120/550/1400, starter e `remove_ads` (não consumível).
- **Diagnóstico / desempenho** — eventos anônimos `run_start`, `hit_car`, `ad_rewarded`, `fps_below_45`, `crash_forced` via Firebase Analytics/Crashlytics, apenas para corrigir bugs e medir retenção D1/D7.

### O que **não** coletamos

- Localização precisa, contatos, arquivos, câmera, microfone.
- Localização aproximada: **não**.
- Dados de crianças: público 13+ (IARC).

### Como usamos

- Anúncios e compras são processados pela Google; nós só recebemos confirmações de crédito (sem dados bancários).
- Analytics é espelhado via `AnalyticsManager` mock → Firebase quando disponível; sem rede, fica em `user://analytics_mock.jsonl`.

### Seus direitos

Exclua o save desinstalando o app; revogue consent em Loja > Restaurar / Configurações do sistema. Escreva para `suporte@arena.correponto.app` para LGPD.

### Data Safety (Play Console)

Declarado: **ID publicidade, compras, diagnóstico — coletados, criptografados em trânsito, não compartilhados com terceiros.**

Versão PT-BR e EN-US disponível na mesma URL (`/privacidade?lang=en`).
