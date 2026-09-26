# Arte-alvo — visão do produto final (Corre pro Ponto)

Cinco imagens conceituais do resultado esperado do jogo depois das 9 etapas do
`docs/PLANO_TRANSFORMACAO_GRAFICA_ARTE_ALVO.md`. Estilo: **Stylized PBR Vibrant**
(Subway Surfers / Pixar mobile), identidade brasileira, leitura limpa em tela pequena.

| # | Arquivo | Cena | O que valida |
| --- | --- | --- | --- |
| 1 | `1_gameplay_avenida.png` | Gameplay padrão, avenida tropical ao meio-dia | 3 faixas (rua x calçada portuguesa), moedas R$ em arco, padaria/toldos, orelhão verde, ipês floridos, HUD com corações, moedas e barra de progresso |
| 2 | `2_perseguicao_caramelo.png` | Pulo sobre bueiro no bairro, golden hour | Dash com trail e speed lines, caramelo perseguindo, moto de entrega na rua, camelô na calçada, burst de partículas e combo x4 |
| 3 | `3_chegada_onibus.png` | Embarque no ônibus amarelo (Etapa 9) | Câmera cinemática lateral na porta, confete, card de resultado translúcido com 3 estrelas, moedas, tempo e botões grandes |
| 4 | `4_chuva_orla.png` | Capítulo orla com clima de chuva (Etapa 8) | Poças refletivas, asfalto/calçada molhados, respingos no passo, deslize sob barreira de obras, tutorial de gesto |
| 5 | `5_loja_personagens.png` | Loja de personagens | Pódio 3D do corredor equipado, grade rolável de perfis brasileiros, cards bloqueados com preço em R$, streak diária, estrelas e CTAs |

Imagens geradas como referência de direção de arte — não são capturas do build.

## Extra

| # | Arquivo | Uso |
| --- | --- | --- |
| 6 | `6_model_sheet_heroi.png` | Model sheet da heroína Júlia (frente/lado/costas + insets de rosto, mão, sola, mechas de cabelo e topologia). Referência de produção para `tools/blender/build_heroi_julia.py`, descrito em `docs/PLANO_HEROI_10_10.md`. Sem marcas registradas. |
| 7 | `7_fase1_antes_depois.png` | Turnaround comparativo renderizado em Blender: linha de cima = `Humano_F.glb` que o jogo usa hoje; linha de baixo = corpo base da Fase 1 (`tools/blender/build_heroi_julia.py`). Ver `docs/execucao/HEROI_FASE0_FASE1.md`. |
| 8 | `8_fase2_pbr.png` | Fase 1 (barro, em cima) × Fase 2 (albedo/normal/ORM bakeados, embaixo). |
| 9 | `9_fase2_closeup_pele.png` | Close-up da pele bakeada: variação de tom, AO nas dobras e microrrelevo de poro. |
| 10 | `10_bracos_corrigidos.png` | Três linhas: Fase 1 (barro), PBR com os braços tortos e a versão corrigida (máscara lateral do tronco + cadeia do braço em reta). |
| 11 | `11_mao_detalhe.png` | Close da mão refeita: palha própria (laje) com dedos nascendo de dentro da palma. |
| 12 | `12_turnaround_fase2.png` | Turnaround 4 vistas (frente/3-4/lado/costas) do GLB da Fase 2 reconstruído do zero em 26/09/2026 — `assets/characters/source/heroi_julia/heroi_julia_pbr.glb` (1.672 KB, PBR + rosto esculpido). Ver `docs/execucao/HEROI_REBUILD_2026-09-26.md`. |
| 13 | `13_mao_detalhe_fase2.png` | Close da mão no GLB reconstruído (`tools/blender/render_detalhe.py --alvo mao`): palma em laje, 4 dedos nascendo dentro da palma, polegar lateral. |
| 14 | `14_rosto_detalhe.png` | Close do rosto no GLB reconstruído (`render_detalhe.py --alvo rosto`): órbitas, nariz, boca, queixo e orelhas esculpidos (Fase 3 parcial — ainda sem cabelo). |
