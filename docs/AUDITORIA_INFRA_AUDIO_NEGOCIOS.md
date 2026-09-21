# Auditoria — Infraestrutura, Desempenho, QA · Áudio · Negócios/Monetização/Jurídico

Data: 2026-09-21 · Base: `3b745af` (Retenção D0–D30) · Status: **implementada nesta sessão**
(commit “Infra/Áudio/Negócios: auditoria + hardening P0/P1” nesta branch)

## Resumo executivo

Veredito: o jogo está **tecnicamente rico e comercialmente desligado**.
Engine, QA automatizado e áudio procedural são fortes; faltava ligar tudo ao
mundo real — e os portões que deveriam garantir isso estavam quebrados ou
desatualizados. Esta sessão implementou tudo que é implementável sem
binário Godot/aparelho físico, e deixou automação + docs prontos para o resto.

| Eixo | Bons | Críticos (P0) | Implementado aqui |
|---|---|---|---|
| Infra/QA | export AAB configurado, save atômico, qualidade adaptativa, 16 suítes headless | nenhum AAB jamais gerado; métricas de vitrine simuladas; sem keystore/CI/SDKs | validador ressuscitado, CI real, build/trailer scripts, VRAM, re-baseline |
| Áudio | 100% procedural versionado, cobertura ampla, jogável sem som | pool rouba voz de alerta; sem ducking/buses; bug de unmute; sem beeps/haptics | 9 SFX novos, canal de alertas, ducking, buses, unmute fix, haptics, fiação |
| Negócios | catálogo autoritativo, billing/ads com fallback mock | consume stub (= reembolso Google); UMP mock autoconcedido; Pack S não cruza desejo | ledger idempotente + reconcile, rebalance S/M/L, UMP-ready + NPA, HMAC no save |

**O que continua pendente (exige engine/aparelho, scripts prontos):**
rodar QA headless com binário Godot, gerar o primeiro AAB real, Firebase Test
Lab, medição real de fps/tamanho/crash, wiring dos plugins nativos
(`docs/PLUGINS_NATIVOS.md`), conta Play Console + Data Safety.

---

## Eixo 1 — Infraestrutura, Desempenho e QA

### Bons (mantidos)
- `export_presets.cfg`: preset Android/AAB coerente (arm64, minSdk 26,
  targetSdk 35, `package/classify_as_game`, immersive).
- Save atômico (temp → backup → rename) com migração v1→v4 sem perda.
- `render_quality.gd`: qualidade adaptativa; 16 suítes `qa_etapa*.gd` headless.
- `tools/make_keystore.sh`: gera keystore **fora do repo** (nunca commitar).

### Achados → correção

**🔴 A1. Nenhum AAB jamais gerado; métricas de vitrine são simuladas.**
`tools/qa_device_farm.py` gera “27,9 MB / 56–61 fps / 0 crash” com seed fixa —
os relatórios em `store/qa/` são ficção até medição real.
→ Correção: `tools/build_aab.sh` (portões → keystore → export AAB via
`godot --headless --export-release`, senhas via env, preset restaurado) +
`store/qa/README.md` marcado como simulado + CI bloqueia merge se portões
falharem. Medição real segue pendente (Test Lab).

**🔴 A2. `tools/validate_project.py` quebrado (portão que não executa).**
Crash `OSError: File name too long` no `check_paths`: regex
`res://[^\"]+` atravessava quebras de linha e montava “caminhos” de KBs.
→ Correção: regex restrita a `res://[^\s\"']+` + guarda `OSError`; tokens
sincronizados (schema **v4**, **27** obstáculos, exceção `julia.glb`
documentada); mensagem final atualizada. Resultado: **PRE-FLIGHT OK**.

**🔴 A3. Tokens obsoletos em `tools/qa_full.py`.**
Esperava schema v3 e 13 obstáculos; o projeto evoluiu para v4/27.
→ Correção: tokens sincronizados → **OK 133, WARN 0, FAIL 0**.

**🔧 A4. Texturas sem compressão VRAM (`compress/mode=0`).**
157 `.import` de textura em modo lossless (`compress/mode=0`): ~94 MB de PNG crus na RAM/VRAM —
risco de OOM em aparelhos low (Galaxy A10/Mali-G71 do device farm).
→ Correção: `tools/fix_texture_imports.py` migrou 157 para VRAM comprimida (+29 normal_map)
(albedo/normal/roughness/height); re-executável e idempotente.

**🔧 A5. `game.gd` legado ia para o export.**
`export_filter="resources"` inclui o runner 2D legado (~+1 MB e superfície
de confusão no AAB).
→ Correção: `exclude_filter` com `scripts/game.gd` (+ `.uid`). O arquivo
segue no repo para referência/testes.

**🔧 A6. Manifestos PROVENANCE sem ferramenta de re-baseline.**
Qualquer asset novo quebrava o validador sem caminho de correção.
→ Correção: `tools/rebaseline_provenance.py` (regenera SHA-256 + `--check`
para o CI).

**🔧 A7. Sem CI.**
→ Correção: `.github/workflows/qa.yml` — portões + 16 suítes headless a cada
push/PR (com fallback de versão do Godot), `check_gdscript` com `--exclude`
para fixtures intencionais.

**🔧 A8. Trailer manual.**
→ Correção: `tools/build_trailer.sh` — mp4 30 s a partir de
`store/screenshots/` + trilha própria (`music_terminal.wav`).

### Correções honestas à v1 desta auditoria
- `assets/textures/pbr/` **não** são duplicatas: só `asfalto_normal.png`
  colide em nome com a raiz e o conteúdo **difere** (heightmaps/ORM próprios).
- `trovao.wav` **é** tocado (`weather_system.gd`, player 3D com atraso);
  `hit.wav` **é** tocado (feedback de escudo via `_show_feedback`).

---

## Eixo 2 — Áudio e Sonoplastia

### Bons (mantidos)
- 100% procedural versionado em `tools/generate_audio.py` (risco autoral zero,
  regenerável, determinístico por seed).
- Cobertura ampla (passos por superfície, buzina 2 tons, latido, trovão,
  4 loops musicais); jogável sem som (feedback visual espelhado).

### Achados → correção

**🔧 S1. Pool round-robin rouba voz de alerta.**
8 vozes circulares: spam de moeda podia calar a buzina (`horn`) no aviso de
moto/caminhão — perda de informação de gameplay.
→ Correção: **canal prioritário de alertas** (`horn`, `count_go`, `defeat`,
`victory`, `trovao`) em player dedicado que nunca é preemptado; `play_alert()`
novo; `play_sfx()` segue para o resto.

**🔧 S2. Sem ducking/buses.**
Música competia com alertas no mesmo barramento implícito.
→ Correção: buses `Music`/`SFX` criados em código + **ducking** (−8 dB na
música por 0,6 s a cada alerta).

**🔧 S3. Bug de unmute.**
`toggle_mute()` sempre voltava para a faixa 0 (`music_city`), ignorando o
capítulo.
→ Correção: guarda `_last_music_group`; unmute retoma a faixa do capítulo.

**🔧 S4. 9 lacunas de feedback sonoro.**
Sem beeps de contagem, sem jingle de vitória/derrota/level-up, sem som de
baú/compra/portas, sem ambiente de chuva.
→ Correção: gerados `count_beep/count_go/victory/defeat/levelup/chest/
purchase/bus_doors/rain_loop.wav` (antigos byte-idênticos — append-only no
gerador) + fiação completa no `game_3d.gd`/`weather_system.gd`:
contagem 3-2-1 + “vai”, vitória/derrota, level-up, baú, compra na loja,
portas no embarque, loop de chuva com o estado do clima.

**🔧 S5. Sem haptics.**
→ Correção: `scripts/haptics.gd` (`Input.vibrate_handheld`, respeita
`reduced_motion`): dano, derrota, embarque, marcos (level-up, conquista).

**Órfãos reais após a fiação:** `pickup.wav`, `wall.wav` seguem sem uso em
`game_3d.gd` (só legado `game.gd`) — mantidos como reserva, custo ~0.
`step.wav` é alias de `step_asfalto.wav` por design (fallback de superfície).

---

## Eixo 3 — Negócios, Monetização e Jurídico

### Achados → correção

**🔴 P0-B1. `consume_if_needed` era stub → Google reembolsa consumables em ~3 dias.**
Moedas grátis + receita zero + risco de suspensão por “entrega sem consumo”.
→ Correção: **ledger idempotente** `grant→ack→consume` persistido no save
(`billing_ledger`: `purchase_token → {state, product_id, ts}`) +
`reconcile_pending()` no boot (retoma grant/ack/consume após crash) +
chamadas reais ao plugin nativo quando presente (`acknowledge`/`consume`
via `GodotGooglePlayBilling`), com o mock passando pelo **mesmo caminho**.

**🔴 P0-B2. UMP mock autoconcedido vs `PRIVACY.md` prometendo consentimento.**
Violação da EU Consent Policy/LGPD se publicado assim.
→ Correção: `ads_manager.gd` **UMP-ready**: sem autoconcessão; default
**NPA (não personalizado)**; `request_consent_if_required()` abre o fluxo
UMP real quando o plugin existe e mantém `consent_required=true` até decisão;
`can_show_interstitial_now()` exige decisão registrada; estado persistido.

**🔴 P0-B3. Pack S (120) não compra o item mais barato (Maria 180).**
Pacote de entrada que não cruza nenhum marco de desejo = conversão ~0 no D0.
→ Correção: rebalance **S 300 / M 1000 (+bônus) / L 2200 (+bônus)** mantendo
os preços em R$ (valor percebido 2,5× no S); S cruza Maria (180) + sobra;
starter vira **compra-única** (one-time) com Rafa + 300; `restore` real
(restaura `remove_ads` + starter via `queryPurchases` nativo ou ledger).

**🔧 B4. Sem flags de ads / sinais de idade.**
→ Correção: `max_ad_content_rating="PG"`, `tag_for_child_directed_treatment`
e `tag_for_under_age_of_consent` declarados (valores via RemoteConfig para
ajuste por região), aplicados no `initialize()` nativo.

**🔧 B5. Save sem integridade (M7).**
JSON puro editável = moedas/itens forjáveis; billing idempotente precisa de
âncora local.
→ Correção: envelope **HMAC-SHA256** (`{v, data, sig}`, sal por aparelho via
`OS.get_unique_id()`): legado sem assinatura **carrega normalmente** (migra
no próximo flush, zero perda); assinatura inválida → tenta backup → defaults
+ `record_event("save_integrity_fail")`.

**📄 B6. Docs com valores obsoletos pelos quick wins de retenção.**
→ Correção: `STORE_LISTING.md`, `IARC.md`, `PLANO_COMERCIAL.md` atualizados
(skins 15 Rubi, review 10 clears + 2º dia, packs S/M/L novos).
`RELEASE_LOTE17.md` mantido como registro histórico congelado.
Novos: `docs/PLUGINS_NATIVOS.md` (contratos exatos de wiring + checklist) e
`docs/ROADMAP_LIVEOPS.md` (90 dias pós-lançamento).

### Ainda não-fato (declarado como intenção nos docs, não execute aqui)
Conta Play Console, Data Safety preenchido, plugins nativos instalados,
validação servidor-side de receipts (Lote 17 do plano), DPO/canal LGPD real.

---

## Backlog executado nesta sessão

- [x] Validador + `qa_full` verdes (PRE-FLIGHT OK · 133/0/0)
- [x] CI + re-baseline + build AAB + trailer
- [x] VRAM em 157 imports (+29 normal_map) + legado fora do export
- [x] 9 SFX + audio_manager (alertas, ducking, buses, unmute, loops) + haptics
- [x] Fiação: contagem, vitória/derrota, level-up, baú, compra, portas, chuva
- [x] Billing: ledger, reconcile, rebalance, restore, consume/ack reais
- [x] Ads: UMP-ready, NPA padrão, flags PG/idade
- [x] Save HMAC (legado preservado)
- [x] Docs: plugins nativos, roadmap liveops, valores sincronizados, STATUS

## Como validar (quando houver engine/aparelho)

```bash
python3 tools/validate_project.py          # PRE-FLIGHT OK
python3 tools/qa_full.py                   # OK 133 | WARN 0 | FAIL 0
./tools/build_aab.sh                       # gera build/corre-pro-ponto.aab
./tools/build_trailer.sh                   # gera build/trailer_30s.mp4
godot --headless --path . --quit-after 1   # smoke (binário real)
```
