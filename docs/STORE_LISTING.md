# Store Listing — Corre pro Ponto (Lote 18 Vitrine)

**Pacote:** `com.arena.correponto` **Nome:** Corre pro Ponto **Categoria:** Jogo > Corrida casual **Classificação:** IARC 13+ (ver `docs/IARC.md`)

## Short description (80c, PT-BR)
Corra, desvie e pegue o busão! Runner 3D brasileiro com 50 fases e Endless.

**EN-US (80c):** Run, dodge and catch the bus! Brazilian 3D runner, 50 stages + Endless.

## Full description (PT-BR, ≤4000c)
Corre pro Ponto é um runner 3D em terceira pessoa no coração do Brasil. Escolha entre rua (carros, motos, ônibus e buracos) e calçadas (pedestres, atalhos e bônus) em 3 faixas, use dash, pulo e deslize para chegar ao ponto a tempo.

• **50 fases** em 5 capítulos (de 400 m a 792 m, 5→18 m/s) + **Endless** liberado com 120★
• **13 obstáculos** + 10 animais + 20 corredores com habilidade (motoboy, professora, etc) + pets caramelo
• **Economia justa:** R$ soft + Rubi premium, baú diário (5-15 R$ +1-3 Rubi) e evento semanal (Semana do Motoboy +30% motos)
• **Sinks LiveOps:** reroll cor da moto 40 R$, skins extras 80 Rubi, sem loot box, sem paywall em F1-F5
• **Progressão:** estrelas 150, dailies, marco semanal, streak 7 dias, XP/nível, conquistas e badges
• **Tech:** Mobile Vulkan + GL compat, sombra 1024, LOD árvore 35 m, AAB 27.9 MB, 56-61 fps em Adreno 610, cold <2.5 s
• **Plataforma:** Play Games (nuvem <50 KB, conquistas, leaderboard), In-App Review após 3 clears, In-App Update flexível, Billing (120/550/1400 + remove R$9,90), AdMob consentido (UMP/Data Safety)

**EN-US (full):**
Run through Brazilian streets in this third-person 3D runner. Street (left) vs sidewalks (center/right), dash, jump, slide — catch the yellow bus! 50 stages (5 chapters) + Endless, 13 obstacles, 20 runners, pets, fair economy (no loot boxes, no paywall on stages 1-5), daily chest, weekly events, 60 fps on mid devices, AAB 27.9 MB, Play Games cloud, In-App Review/Update, Billing & AdMob (consent).

## Novidades (changelog v1.0.0, PT-BR)
• Lançamento: 50 fases + Endless
• Evento semanal vivo e baú diário
• Economia Rubi + sinks 40/80
• Notch SafeArea + PT/EN + Reviver 5 s com tutorial 3D
• AAB 27.9 MB, 60 fps, In-App Update

## Assets
- **Screenshots 1080×1920 (8):** `store/screenshots/01..08_*.png` (caramelo, busão, tráfego, calçada, dash, endless, 50 fases, Rubi)
- **Feature graphic 1024×500:** `store/feature_graphic_1024x500.png` (ônibus amarelo + faixa + logo 50 FASES)
- **Vídeo 30 s (6 clips 1280×720 + storyboard):** `store/video/clip_01..06_*.png` + `storyboard_6clips_3840x1440.png` → montar `store/video/trailer_30s.mp4` via `ffmpeg -framerate 0.2 -i clip_%02d...` (template abaixo)
- **Ícone:** `assets/art/icon.svg` (adaptative foreground/background 432×432)

## Keywords (ASO, PT-BR)
corrida 3d, runner brasileiro, pegar onibus, subway surfers brasileiro, endless runner

## Contact
Política: `https://arena.correponto.app/privacidade`  
Suporte: `suporte@arena.correponto.app`  
Classificação IARC: 13+ (fantasia leve, compras opcionais)

## Comandos para gerar vídeo (quando ffmpeg disponível)

```bash
ffmpeg -framerate 0.2 -i store/video/clip_%02d_*.png -c:v libx264 -r 30 -pix_fmt yuv420p store/video/trailer_30s.mp4
# ou concat storyboard:
ffmpeg -loop 1 -i store/video/storyboard_6clips_3840x1440.png -t 30 -c:v libx264 store/video/feature_30s.mp4
```
