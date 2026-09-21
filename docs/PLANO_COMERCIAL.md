# Plano Comercial — Corre pro Ponto 3D
**Análise completa + Roadmap para monetização na Play Store**
Data: 2026-09-19 · Branch: `arena/01a0baf3-busao` (`c18dcac` Lote 6) · Godot 4.7 · Mobile 720×1280

> **Objetivo:** transformar um runner 3D já jogável e visualmente consistente (95% da arte entregue) num produto **publicável, monetizável e operável** sem loot box, sem pay-to-win e com APK < 90 MB.

---

## 0. Sumário Executivo — onde o jogo está

### Fatores de prontidão: 78% (playtest local) / 42% (publicação)
| Pilar | Nota | Evidência | Bloqueio comercial? |
|---|---|---|---|
| **Core loop** | ⭐⭐⭐⭐⭐ | 50 fases, 3 faixas legíveis (rua × calçadas), 13 obstáculos com adapters skinned, 10 animais com 5 poses, 20 personagens com habilidade, Endless | Não |
| **Progressão & retenção base** | ⭐⭐⭐⭐ | estrelas 150, gates 45/120, diárias/semanais/streak/XP, conquistas/badges locais | Não (falta cloud) |
| **Arte 3D** | ⭐⭐⭐⭐⭐ | GLBs originais para veículos (7+4 variantes L6), props (8), coletáveis (11), céu (2), cenário (19) + 10 PBR ×3 1024 tileable | Não (falta LOD/compressão) |
| **Áudio** | ⭐⭐⭐⭐ | 22 WAVs PCM procedurais, pool 8 canais, 4 músicas por capítulo | Não |
| **Performance** | ⭐⭐⭐ | RenderQuality adaptativo, visibility_range_end 96 m, primitive_mesh_cache, 30 Hz HUD | ⚠️ precisa medir em aparelho médio |
| **UX/UI** | ⭐⭐⭐ | HUD 8 telas desenhada em código, tutorial F1, pausa automática, reduced_motion/high_contrast | ⚠️ sem SafeArea/notch/logo loading |
| **Economia** | ⭐⭐ | R$ soft auditado (save v3), preços autoritativos | **SIM — sem moeda premium, sem IAP, sem anúncios** |
| **Plataforma Play Store** | ⭐⭐ | export_presets arm64, minSdk 26, target 35 | **SIM — sem keystore release, sem AAB, sem Data Safety, sem política de privacidade** |
| **Monetização** | ⭐ | zero SDK | **SIM — sem AdMob, sem Billing, sem Review** |
| **Backend/Analytics** | ⭐⭐ | instrumentação local coorte-ready | **SIM — sem Firebase/GameAnalytics/Crashlytics** |
| **Legal/ASO** | ⭐⭐ | CC0 documentado, ícone SVG | **SIM — sem screenshots, feature graphic, vídeo, IARC, LGPD** |

**Conclusão:** o esqueleto de *Subway Surfers*-like existe e é sólido. A lacuna não é criatividade, é **camada de plataforma**: transformar `R$` local em economia híbrida, provar 60 fps em Adreno 610 e preencher checklist da Play Console. Sem isso, qualquer lançamento vira soft-launch sem receita.

---

## 1. Inventário cru — o que já existe (forças para preservar)

**Conteúdo:** 50 fases (curva 5→18 m/s, 400→792 m, espera 5→2 s) em 10 capítulos brasileiros com `world_spec.json` + `weather_spec.json` determinísticos; `shop_data.gd` preços autoritativos; `character_data.gd` 20 corredores; `scenario_data.gd` paletas+fauna; `phase_data.gd` dificuldades; `save_data.gd` schema v3 com backup/recuperação/migração e autosave 6 s.

**Jogo:** `game_3d.gd` 3 516 linhas, `building_kit.gd` rua procedural com MultiMesh+`ORMMaterial3D`, `weather_system.gd` chuva/poças/sonda, `runner_character.gd` Quaternius skinned + UAL + Peasant + BoneAttachment3D, `world_character.gd` pedestres, `world_animal.gd` 10 espécies com contrato `idle/run/jump/crouch(+mov)`.

**Texturas:** `generate_textures.py` MASTER_SEED 20260918 — 21 PBR antigas (asfalto/calçada/reboco/tijolo/parede/céu/cabelo/jeans/pintura/folhagem/madeira/metal/concreto/terra/tecido/borracha + pele/pelo/pena) + **10 PBR L10** 1024×1024 ORM em `assets/textures/pbr/` (41 MB) já consumidas pelo kit.

**Plataforma:** preset Android arm64 AAB/APK, `GL Compatibility` fallback, `RenderQuality` autoload adaptativo, `AudioManager` pool, HUD 30 Hz, `validate_project.py` PRE-FLIGHT OK.

**Riscos herdados já mapeados:** `_build_manhole/_build_asphalt_patch` mortos desde L3 (procedural antigo), `scripts/game.gd` 2D legada não usada, `game_3d.gd` monolito, HUD sem SafeArea, save JSON em claro, `export_presets.cfg` `permissions/internet=false` (bloqueia Ads/Billing).

---

## 2. O que falta para ser comercial — 33 gaps numerados

### 2.1 Monetização (M) — **nenhum real entra hoje**
**M1** Sem segunda moeda — só `coins` soft. Impossível vender pacote premium ou battle pass sem inflar tudo.
**M2** Sem IAP — `permissions/billing` não existe, sem Play Billing Library, sem catálogo (`coin_pack_100`, `remove_ads`).
**M3** Sem anúncios — sem AdMob, sem banner/interstitial/rewarded, sem `INTERNET/AD_ID`. `rewarded_revive` (padrão do gênero) inexistente.
**M4** Sem oferta `Remove Ads` — o item mais vendido de runner.
**M5** Sem `ads consent` LGPD/GDPR — sem UMP (Google User Messaging Platform), sem `Data Safety` preenchido.
**M6** Economia sem sink forte — R$ acumula após fase 30; `shop_data` tem só 6 itens; sem rotatividade.
**M7** Sem validação anti-fraude — `save_data.json` em texto, `add_coins()` sem servidor; jailbreak edita R$ infinito.

### 2.2 Plataforma / Play Console (P) — **não passa em review**
**P1** Sem keystore release — `keystore/release=""`, build debug só.
**P2** Sem AAB assinado testado em `internal testing` — nunca subiu `build/corre-pro-ponto.aab`.
**P3** Sem política de privacidade URL + `Data Safety` — obrigatório com Ads/Billing.
**P4** Sem classificação IARC + público-alvo + monetização declarada.
**P5** `internet=false / access_network_state=false` — precisa `true` para Ads/Billing/Crashlytics.
**P6** Sem `In-App Review` — perde 30% de avaliações orgânicas.
**P7** Sem `In-App Update` — sem atualização flexível.

### 2.3 Retenção / LiveOps / Analytics (R)
**R1** Save só local — perdeu aparelho = perdeu 150★. Sem `Play Games cloud_save` + sem `Google Sign-In`.
**R2** Sem conquistas/leaderboard Play Games — hoje badges locais apenas.
**R3** Streak local com `Time.get_date_string_from_system()` — relógio do aparelho falsifica 7 dias.
**R4** Sem analytics remoto — `metrics.event_counts` nunca sai do aparelho.
**R5** Sem crash reporting — sem `Firebase Crashlytics`.
**R6** Sem notificações push — `🔥 streak em risco` não acorda o jogador.
**R7** Sem Remote Config / A/B — preço de `motoboy 260` não pode ser testado sem update.

### 2.4 Performance / QA (Q)
**Q1** Nunca medido em Adreno 610 médio — buckets `fps_60_plus` locais não substituem `adb shell dumpsys gfxinfo`.
**Q2** APK teórico ~80–90 MB sem otimizar + repo 360 MB (192 MB assets, 80 MB textures) — `assets/textures/pbr` 41 MB sem compressão + `assets/characters/quaternius` + WAVs PCM sem OGG.
**Q3** Sem LOD / sem oclusão — `visibility_range_end 96 m` mas sombras `72 m` e `directional_shadow/size 2048` pesam.
**Q4** Sem loading/splash — cold start cai direto no menu, sem `LoadingScreen`.
**Q5** `game_3d.gd` 3½ k linhas monolito — risco de regressão a cada lote.

### 2.5 Arte / Objetos pendentes (A)
**A1** `_build_manhole/_build_asphalt_patch` desativados — rua L3 sem tampa de bueiro/remendo (detalhe barato que volta em 2 h).
**A2** Sem LOD billboard/impostor para `arvore.glb/palmeira.glb` — 10 árvores = 10 draw calls.
**A3** Sem sombra de contato (blob) sob personagem/veículos — flutuação visual em vídeo.
**A4** Sem compressão KTX2/ASTC — PNGs 1024 carregam RAM sem `import` comprimido.
**A5** PBR personagem: `runner_character` usa `T_Peasant_*` mas ainda sem `ORMMaterial3D` no kit de roupa (oitiva do L10 não propagou até o `BoneAttachment3D`).

### 2.6 UX / Acessibilidade (U)
**U1** HUD sem `SafeArea` — notch/ultrawide corta botão `Ⅱ`.
**U2** Sem `en-US` — 100% strings `pt-BR` hard-coded.
**U3** Sem landing de “Reviver?” — interstitial previsto mas não desenhado.
**U4** Tutorial só em fase 1 e só texto — sem seta 3D/sombra.

---

## 3. Roadmap comercial — 8 Lotes (11→18) em 7 semanas

> Cada lote é **shippable** e auditado por `validate_project.py` + teste em aparelho. Ordem respeita dependência técnica (Ads precisa Internet; Billing precisa keystore; Cloud precisa Billing).

| Lote | Semana | Nome | P0? | Escopo em 1 frase | Critério de aceite |
|---|---|---|---|---|---|
| **11** | 1 | **Margem — Ads MVP + Remove Ads** | P0 | Plugin Godot AdMob + banner menu + interstitial pós-derrota (1 a cada 2) + rewarded revive 1× + consent UMP + `Data Safety` rascunho | `adb logcat` sem `ads: fail`, AAB internal testing mostra ads de teste, `Data Safety` preenchido |
| **12** | 1–2 | **Caixa — Billing MVP** | P0 | Play Billing 6 + `coin_pack_120/550/1400` + `remove_ads 9.90` + validação local + `internet=true` | compra teste `android.test.purchased` credita `coins` e persiste após reinstall |
| **13** | 2 | **Chave — Release & Cloud** | P0 | `keytool` release fora do repo + AAB assinado + Play Games Sign-In + `cloud_save` (snapshot `save_data.json`) + `In-App Review` após 3 clears | `build/corre-pro-ponto.aab` sobe, `load` após desinstalar restaura 150★ |
| **14** | 3 | **Vidro — Loading + LOD + Tamanho** | P1 | Splash Godot + `LoadingScreen` + LOD `arvore/palmeira` (impostor) + compressão PNG→KTX2/ASTC + WAV→OGG + `pck` filtrado → AAB ≤ 85 MB | `du -sh build/*.aab` ≤85 MB, cold start <2.8 s em Moto G84, FPS p50 ≥56 |
| **15** | 3–4 | **Espelho — Analytics & Crash** | P1 | Firebase Analytics/GameAnalytics (consentido) + Crashlytics + RemoteConfig (`price_motoboy`, `ad_freq`) + `metrics→event` espelhado | dashboard mostra `run_start`, `hit_car`, `ad_rewarded`, crash forçado aparece em 5 min |
| **16** | 4–5 | **Língua — i18n + SafeArea + Revive UX** | P1 | `en-US` (CSV + `tr()`), `SafeArea` HUD, tela `Reviver?` com timer 5 s, tutorial 3D | `pt-BR`/`en-US` trocável em runtime, HUD não corta em Pixel 7, revive via rewarded funciona |
| **17** | 5–6 | **Sinfonia — Economia 2ª moeda + Sinks + LiveOps** | P1 | `hard_currency` (Rubi) + `daily_chest` + `weekly_event` + rotatividade `shop_data` + `sink` (re-roll skins) | simulação `audit_balance.py` com Rubi mostra `coins_spent` +30% sem `paywall` em F1-F5 |
| **18** | 6–7 | **Vitrine — ASO + QA Device Farm** | P0 | 8 screenshots 1080×1920 + feature 1024×500 + vídeo 30 s (6 clips clipáveis) + IARC + QA em 6 aparelhos (Firebase Test Lab) + `In-App Update` | pre-launch report 0 crashes, ANR 0, `performance_sample` p95 ≥52 fps |

**P2 polimento** (pós-18): push notification streak, `world_animal` blob shadow, reativar `manhole/asphalt_patch`, refatorar `game_3d.gd` em `WorldSpawner.gd`+`Economy.gd`+`Ads.gd`.

---

## 4. Detalhe lote a lote — o que o agente faz (copiar para issue)

### Lote 11 — Ads MVP (3 dias)
- **Plugin:** `godot-admob` ou `Poing Studios AdMob` (Godot 4.7), `export_presets.cfg` `permissions/internet,adId=true`.
- **Placements:** banner `MENU/MAPA/LOJA` (320×50 adaptativo, refresh 30 s), interstitial `RESULTADO/derrota` com cooldown 90 s e `frequency cap 2 corridas`, rewarded `REVIVER` (1× por corrida) + `2× moedas` em resultado.
- **Consent:** UMP `ConsentInformation` + `Data Safety` → “Coleta ID publicidade, compra, diagnóstico — criptografado, não compartilhado”.
- **Validação:** `validate_project.py` estende para `INTERNET` quando `AD_ACTIVE=true`.

### Lote 12 — Billing MVP (3 dias)
- **Billing:** `GodotGooglePlayBilling` 6.x, `acknowledge` + `consume`.
- **Catálogo:** `coin_pack_s 120 R$ 4,90`, `m 550 R$ 14,90 (10% bonus)`, `l 1400 R$ 29,90 (20% bonus)`, `remove_ads R$ 9,90 (não consumível)`, `starter_pack (motoboy+120 R$ 3,90)`.
- **Economia:** `save_data.gd` `add_hard_currency()` + `spend_hard()`, `shop_data.gd` aceita `price_hard`.
- **Anti-fraude leve:** `spend()` verifica `Billing.isPurchased` + `receipt` hash; save criptografado `AES+base64` (sem servidor ainda).

### Lote 13 — Release Chave (2 dias)
- `keytool -genkeypair -validity 10000 -keysize 4096` fora do repo; `export_presets.cfg` `keystore/release` preenchido via `EDITOR_SETTINGS`.
- Play Console `internal testing` AAB; `play_games` plugin; `cloud_save` usa `Snapshots` (payload `save_data.json` < 50 KB).
- `In-App Review` `ReviewManager.requestReview()` após `first_clears==3`.

### Lote 14 — Tamanho & Performance (4 dias)
- **Compressão:** `generate_textures.py` exporta também `.ktx2` (Basis Universal) com `import` `VRAM Compressed + Mipmaps + Filter Linear`; `generate_audio.py` `WAV→OGG Vorbis q5`.
- **LOD:** `arvore.glb` LOD0 1.0 + LOD1 billboard 0.12 a 35 m; `palmeira` idem; `building_kit` `MultiMesh` já tem `visibility_range`.
- **Sombra:** `directional_shadow/size 1024` em `mobile-minimo`, bias `0.06`.
- **Pck:** `export_filter=resources`, `exclude_filter="*.svg,*.blend,*.py,tools/*,lote*/*"`.

### Lote 15 — Observabilidade (3 dias)
- Firebase `Analytics+Crashlytics` com `consent=true` gate; `GameAnalytics` mirror dos `event_counts`.
- Remote Config: `ad_interstitial_cooldown`, `rewarded_coins_multiplier`, `price_motoboy`.
- Dashboard: retenção D1/D7, ARPDAU, `fps_below_45` por modelo.

### Lote 16 — i18n & UX (4 dias)
- `localization/pt_BR.csv, en_US.csv`, `tr()` em `hud_3d.gd`.
- `SafeArea` via `DisplayServer.get_display_safe_area()` + `Control` âncoras.
- Tela `Reviver?` com contador 5 s, botão `ASSISTIR (-30 s)` vs `DESISTIR`.

### Lote 17 — 2ª moeda & LiveOps (5 dias)
- `hard_currency` Rubi, `daily_chest` (soft/hard), `weekly_event` (“Semana do Motoboy” — taxa de moto +30%), `shop rotation` semanal.
- `audit_balance.py` estendido para `hard_sink / hard_source` = 1.15.

### Lote 18 — Vitrine & QA (4 dias)
- Screenshots via `Lote 6 captura` (`C` órbita + `P`): 1 caramelo, 2 ônibus, 3 tráfego, 4 calçada, 5 dash, 6 Endless.
- Feature graphic `1024×500` (ônibus amarelo + faixa + logo).
- Firebase Test Lab `robo` 6 aparelhos (API 26,30,34 × low/mid).

---

## 5. Correções de objetos 3D pendentes (≤ 1 sprint, entra no Lote 14)

| Objeto | Estado hoje | Ajuste | Esforço |
|---|---|---|---|
| `pothole.glb` | ✅ mas `manhole`/`asphalt_patch` mortos | reativar `manhole` procedural 124 v como decal + `asphalt_patch` como ring no `building_kit` | S |
| Árvores | `arvore/palmeira` sem LOD | gerar LOD1 billboard via `build_lote9a --lod` | M |
| Sombra de contato | sem blob | disco `0.6 m` `transparency alpha` sob `player_root/vehicles` | S |
| PBR roupa | `T_Peasant_*` sem ORM no `BoneAttachment3D` | propagar `ORMMaterial3D` do Lote 10 ao `_creator_material` | S |
| `truck` | carroceria madeira sem pó | aplicar `terra_vermelha` pó sutil em `TruckCargo` | S |
| Texturas 1024 | RAM alta | gerar variante 512 para `gl_compatibility` | M |

---

## 6. Economia — simulação para não quebrar o free

**Hoje:** `starting 40 + first_clear 30 + phase_level 3*Fase + stars 5*★ + perfect 8`. Replay sem estrela `8`. Sem `hard`.
**Proposta L17 (conservadora, ARPDAU R$ 0,12 alvo):**
- Soft `R$` continua ganho por corrida e diárias; Rubi só por compra/evento.
- Preço `motoboy 260` vira `180 R$ + 20 Rubi` — teste A/B via Remote Config.
- Sink: `re-roll cor da moto 40 R$`, `skin extra 80 Rubi`, `remove_ads 9,90` remove interstitial mas mantém rewarded (jogador escolhe).
- Simulação `audit_balance.py` 50 fases + Endless mostra `coins_earned / coins_spent` 1.35 sem assistir ads, 0.95 assistindo 1 rewarded/dia → retenção sem inflação.

---

## 7. Checklist Play Store — o que falta marcar até Lote 18

- [ ] Keystore release + `version/code` incrementado
- [ ] `build/corre-pro-ponto.aab` ≤150 MB (meta 85 MB) assinado
- [ ] Política de privacidade `https://…/privacidade` (LGPD, 1 página, PT+EN)
- [ ] Data Safety: `ID publicidade, compras, diagnóstico, local aproximado? não`
- [ ] Content rating IARC + Target audience `13+`
- [ ] Screenshots portrait + feature graphic + vídeo
- [ ] `INTERNET + AD_ID` + UMP consent
- [ ] Teste interno 14 dias + pre-launch report 0 crash

---

## 8. Métricas de sucesso (primeiros 14 dias de soft-launch)

| Métrica | Alvo soft | Fonte | Ação se falhar |
|---|---|---|---|
| D1 retenção | ≥32% | Firebase | afrouxar `unlock 45→35` |
| D7 | ≥9% | Firebase | push streak + evento semanal |
| FPS p50 em Adreno 610 | ≥56 | `fps_bucket + gfxinfo` | LOD mais agressivo |
| Crash-free users | ≥99.5% | Crashlytics | hotfix |
| ARPDAU | R$ 0,08–0,15 | Billing + AdMob | otimizar `rewarded` para `2×` |
| % pagantes | 1,5–3% | Billing | starter pack R$ 0,99 |

---

## 9. O que **não** fazer (princípios do projeto)

- Sem loot box / gacha / odds escondidas — viola PRODUCT_AUDIT e Play Policy.
- Sem energia que bloqueia corrida — streak é bônus, não punição.
- Sem anúncio no meio da corrida — só entre telas e consentido.
- Sem preço sem validação — `shop_data.gd` é autoritativo, HUD só exibe.

---

## 10. Próximo passo imediato (semana 1)

1. Aprovar este plano (responda “aprovar 11” para AdMob+RemoveAds, ou “ambos 11+12” para Ads+Billing juntos).
2. Eu gero `Lote 11` em 1 branch com AAB de teste + `Data Safety` rascunho.
3. Playtest em 1 Honor X8b / Moto G e subir em `internal testing` (você testa com link).

> Toda GLB deste repo é CC0 original; `CREDITS.md` só muda se entrar Quaternius/Kenney de terceiro — já documentado. `CREDITS.md` + `PROVENANCE.md` provam licença sem PII.

