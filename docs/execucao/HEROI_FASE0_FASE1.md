# Herói 10/10 — execução das Fases 0 e 1 (2026-09-26)

Plano: `docs/PLANO_HEROI_10_10.md`

## Fase 0 — Ambiente e baseline ✅

- `sh tools/blender/make_env.sh` reconstruiu o ambiente headless:
  venv em `/home/user/venv-blender` com **bpy 4.5.14 LTS** + stubs X11/GL em
  `/home/user/blender-stubs`. Teste: `bpy OK 4.5.14 LTS`.
- Novo utilitário `tools/blender/render_turnaround.py`: renderiza
  frente / 3-4 / lado / costas de qualquer GLB em estúdio Cycles CPU.
- Baseline "antes" renderizado a partir de `Humano_F.glb` — metade superior de
  `docs/arte_alvo_final/7_fase1_antes_depois.png`.

O baseline confirma o diagnóstico do plano: manga bufante em bola, mãos sem
dedos, tênis descolados da perna, cabeça em cápsula, silhueta sem cintura nem
panturrilha.

## Fase 1 — Corpo base esculpido ✅ (gate verde)

Novo `tools/blender/build_heroi_julia.py`. Pipeline, em ordem:

1. **Grafo de arestas anatômico** (43 nós com raio por junta) → modificador
   **Skin** + **Subdivision 2** → volume orgânico contínuo, sem costuras de tubo.
2. **Moldagem de seções** em bmesh: tórax elíptico, cintura estreitada, quadril
   alargado, crânio ovoide com nuca projetada, pé achatado e antepé largo.
3. **Retopologia QuadriFlow** (alvo 9.000 quads) → loops distribuídos e
   utilizáveis em ombro, cotovelo, quadril e joelho.
4. **Corrective Smooth** (preserva volume — o Smooth comum derretia a coxa).
5. **Loops de deformação** extras subdivididos em torno de cotovelo, joelho,
   ombro, virilha, punho e tornozelo.
6. **Mãos com 5 dedos**: 30 falanges cônicas (3 por dedo, curl relaxado),
   nomeadas `thumb/index/middle/ring/pinky_01..03_l|r` para casar com o
   `REGION_BONES` de `scripts/runner_character.gd` na Fase 4.
7. **Normalização**: altura 1,72 m e sola em z = +0,012 m (mesmo contrato do
   runner atual).

### Métricas do gate

| Métrica | Valor | Alvo | Status |
| --- | --- | --- | --- |
| Triângulos | **29.104** | 24k–46k | ✅ |
| Faces (quads) | 14.609 (92,3% quads) | maioria quad | ✅ |
| Altura | 1,720 m | 1,70–1,75 | ✅ |
| Sola (z mín) | 0,012 m | 0,012 ±0,005 | ✅ |
| Largura / profundidade | 0,613 m / 0,261 m | humana | ✅ |
| Arestas não-manifold | **0** | 0 | ✅ |
| GLB | 514 KB (sem textura ainda) | — | ✅ |

Comparativo de antes/depois: `docs/arte_alvo_final/7_fase1_antes_depois.png`
(linha de cima = modelo atual do jogo; linha de baixo = corpo base novo).

### Saídas (não versionadas — `tools/blender/out/` está no .gitignore)

```
tools/blender/out/heroi_julia_base.glb      corpo base, 514 KB
tools/blender/out/heroi_julia_base.blend    cena para iteração
tools/blender/out/heroi_julia_metrics.json  métricas do gate
tools/blender/out/turnaround_antes.png      baseline
tools/blender/out/turnaround_depois_f1.png  Fase 1
```

Reproduzir:

```sh
sh tools/blender/make_env.sh                                   # uma vez por sandbox
sh tools/blender/run_bpy.sh tools/blender/build_heroi_julia.py
sh tools/blender/run_bpy.sh tools/blender/render_turnaround.py \
   tools/blender/out/heroi_julia_base.glb tools/blender/out/turnaround_depois_f1.png
```

## O que ainda NÃO está neste marco

Por desenho do plano, ficam para as fases seguintes:

- **Fase 2** — UV + bake PBR (o corpo ainda está com material liso de barro).
- **Fase 3** — rosto detalhado (olho na órbita, pálpebra, lábio) e cabelo em cards.
- **Fase 4** — armature de 60 ossos e skinning.
- **Fase 5** — 10 clips de animação com curva Bézier.
- **Fase 6** — roupa (camisa, legging, tênis) e integração como `hero_julia.glb`.

## Próximo passo sugerido

Fase 2 (UV + bake PBR em Cycles): é ela que mata o aspecto "plástico" e permite
o primeiro comparativo direto com `docs/arte_alvo_final/1_gameplay_avenida.png`.
