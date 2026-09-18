# Auditoria Completa — Corre pro Ponto (prontidão Play Store)

Data: 2026-09-18 · Base: commit `cfe9942` + lote visual PBR (este commit)

Auditoria de estrutura, interface e paridade com jogos de sucesso da Play Store
(runners casuais: Subway Surfers, Bus Rush, Sonic Dash). Complementa o
[`PRODUCT_AUDIT.md`](PRODUCT_AUDIT.md) (pesquisa de mercado/benchmarks) e o
[`QUALITY_AUDIT.md`](QUALITY_AUDIT.md) (qualidade técnica do código).

---

## 1. Estrutura do projeto (o que existe hoje)

| Camada | Arquivos | Estado |
| --- | --- | --- |
| Cena | `scenes/main.tscn` → `game_3d.gd` | ✅ única cena, mundo 100% procedural |
| Loop de jogo | `game_3d.gd` (2.7k linhas, 118 funções) | ✅ corredor 3D completo com 50 fases |
| HUD/UI | `hud_3d.gd` (11 telas desenhadas em código) | ✅ ver seção 2 |
| Personagem | `runner_character.gd` + asset Quaternius CC0 | ✅ rig real, UAL, MODEL_FACING_YAW |
| NPCs/obstáculos | `world_character.gd`, `obstacle_data.gd` (13 tipos) | ✅ |
| Animais | `world_animal.gd` (10 espécies × 5 poses) | ✅ |
| Conteúdo | `phase_data.gd` (50 fases), `scenario_data.gd` (10 capítulos temáticos) | ✅ |
| Economia | `game_balance.gd` + `resources/game_balance.tres` (2.200 moedas, gates 45/120) | ✅ auditada |
| Loja | `shop_data.gd` (20 personagens + itens com efeitos) | ✅ |
| Persistência | `save_data.gd` (schema versionado + backup + recuperação) | ✅ robusto |
| Áudio | `audio_manager.gd` + 22 WAVs procedurais (4 trilhas por capítulo) | ✅ |
| Texturas | 21 PBR (albedo+normal+roughness) geradas por `tools/generate_textures.py` | ✅ novo lote |
| Validação | 6 ferramentas em `tools/` (parse, contrato, balance, rig, checker) | ✅ todas verdes |
| Exportação | `export_presets.cfg` Android (minSdk 26, arm64, AAB/APK) + Desktop | ✅ configurada |

**Redundância conhecida:** `scripts/game.gd` (versão 2D legada) não é usada por
nenhuma cena nem preload. Candidata a remoção em lote de limpeza.

## 2. Interface — jornada do jogador

Telas existentes (todas em `hud_3d.gd`):

1. **Menu** — CORRER AGORA (destaque), MAPA, LOJA, CONQUISTAS, DESAFIOS,
   COMO JOGAR, toggles SOM/MOVIMENTO/CONTRASTE, contadores de estrelas,
   moedas, 🔥 streak, nível/XP.
2. **Mapa** — 50 fases em 5 páginas, cadeados por estrelas (fase 20: 45★, fase 50: 120★).
3. **Loja** — 20 corredores com efeitos reais + itens, com scroll e provadores.
4. **Conquistas** — catálogo com progresso persistido.
5. **Desafios** — 3 missões diárias + marco semanal com resgate.
6. **HUD de corrida** — moedas, combo, barra de dash, aviso de ônibus.
7. **Cartão de ponto** + **Resultados** com estrelas e recompensas.
8. **Tutorial contextual** na fase 1 (`tutorial_seen` no save).
9. **Feedbacks** universais (toast + som) para toda ação.

Acessibilidade presente: som on/off, movimento reduzido (dash/câmera),
alto contraste. Controles: teclado (A/D, W/Espaço, S, X, M) + toque/gestos.

**Veredito de estrutura:** o núcleo de retenção (dailies, streak, XP, conquistas,
50 fases com 3 estrelas, loja com efeitos) já equivale ao esqueleto de um runner
de sucesso. As lacunas estão na camada de plataforma (seção 3), não no design.

## 3. Lacunas para paridade com jogos de sucesso da Play Store

### P0 — bloqueantes para publicar
| Item | Status | Nota |
| --- | --- | --- |
| Ícone adaptativo | ✅ | `icon.svg` já configurado nos 3 slots do preset |
| AAB assinado (release keystore) | ⚠️ | preset pronto, falta gerar/credenciar keystore de release |
| Política de privacidade (URL) | ❌ | obrigatória ao usar AdMob; criar página + Data Safety |
| SDK de anúncios | ❌ | AdMob via plugin Godot (banner/interstitial/rewarded) |
| IAP | ❌ | Play Billing: pacote de moedas e "remover anúncios" |
| Avaliação in-app | ❌ | Google Play In-App Review API após N corridas |

### P1 — esperados pelo padrão do gênero
- Conquistas/leaderboard **Google Play Games** (hoje são locais) + cloud save.
- Localização `en-US` (strings hoje hardcoded pt-BR; estrutura já centralizada nas telas).
- Tela de loading/splash dedicada e transição suave entre capítulos.
- "Reviver" assistindo anúncio (padrão do gênero, liga retenção à monetização).
- Segunda moeda (premium) — a economia atual já é auditável para isso.

### P2 — polimento
- Notificações de retorno (streak em risco) · analytics (GameAnalytics/Firebase) ·
  LOD/sombra de contato para aparelhos fracos · tratamento de notch/ultrawide ·
  trailer de loja e screenshots 1080p.

## 4. Inconsistências gráficas — CORRIGIDAS neste lote

1. **Mundo metade PBR / metade chapado** — casas, prédios de perfil e comércio
   usavam cor lisa com SVG flat; agora usam fachadas com albedo+normal+roughness
   (reboco e tijolo à vista), janelas com moldura, peitoril, AO e escorridos.
2. **Normais de asfalto/calçada vetoriais (SVG)** → PNGs reais derivados de mapa
   de altura (Sobel), + mapas de roughness; asfalto escuro com brita, remendos e
   rachaduras.
3. **Calçada genérica** → padrão português Copacabana: pedra clara com onda
   escura de basalto, rebaixo de junta no normal.
4. **Céu 1456×720 liso** → panoramas equiretangulares 2048×1024 com nuvens FBM
   por banda de latitude, disco solar + halo (tropical, entardecer, nublado).
5. **Tonemap Filmic** → **ACES** com exposição 1.06 + névoa mais densa
   (leitura de profundidade e cor "fotográfica").
6. **Tinta de veículos chapada** → flakes metálicos (normal map) em carros
   (3 variantes), caminhão, moto, ônibus e carros estacionados.
7. **Ônibus sem identidade** → letreiro de destino emissivo + ar-condicionado no teto.
8. **Prédios sem acabamento** → platibanda de concreto + ar-condicionado de janela.
9. **Veículos presos ao procedural** → pipeline drop-in de GLB CC0
   (`assets/vehicles/README.md`) com auto-escala, assentamento no chão e fallback
   transparente (Quaternius/Poly Haven/Kenney, todos comerciais).
10. **Lote B — props com cor lisa** → todas as superfícies de adereço agora têm
    albedo+normal+roughness: folhagem de copa com profundidade entre tufos,
    madeira com veios e nós, metal pintado com riscos/lascas (postes, grades,
    telhados, caixas d'água, andaimes), concreto com poros/juntas de fôrma
    (meio-fio, platibandas, guaritas), terra vermelha granular com pedrinhas
    (capítulos de favela), tecido tramado (toldos e varais) e borracha granulada
    (pneus). Novo acabamento **cromo** (sem textura de pintura) para para-choques,
    calotas e racks; "stucco" e "concreto" unificados no concreto PBR.

## 5. Inconsistências conhecidas — pendentes (próximos lotes)

- Props (árvores, postes, bancos, banca) ainda com cor lisa — próximo lote:
  texturas de madeira/folhagem/metal pintado com normal+roughness.
- Animais são estilizados de propósito (silhuetas de primitivas) junto a humanos
  realistas — opção de estilo a validar com jogadores.
- Conferir no editor se algum normal map pede "Invert Y" (geramos OpenGL; o
  Godot 4 detecta e reimporta sozinho ao ser usado como normal).
- `game.gd` 2D legado não referenciado (remover ou arquivar).
- Sombra direcional com 72 m de alcance: avaliar acne em horizontes baixos.

## 6. Roadmap sugerido

| Lote | Escopo | Pronto para |
| --- | --- | --- |
| A (este) | Consistência PBR do mundo + pipeline GLB + auditoria | testes de olho no PC |
| B | Texturas de props + splash/loading + polimento de câmera | demo fechada |
| C | AdMob + política de privacidade + In-App Review + keystore | beta na Play Store |
| D | i18n en-US + Play Games (conquistas/leaderboard/cloud) | lançamento global |
| E | Balanceamento final + screenshots/trailer + data safety | produção |
