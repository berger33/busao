# Execução — correção de braços e mãos da heroína Júlia

Data: 2026-09-26  
Branch: `arena/01a0dc6c-busao`

## Diagnóstico

A evolução anterior já tinha corrigido o zigue-zague principal dos braços, mas o
close ainda denunciava uma mão artificial: palma em bloco, dedos como cápsulas
separadas e sombra/oclusão marcando emendas de falanges. A lateral do corpo
continuava aceitável; o problema restante era a leitura de punho/palma/dedos.

## Correção aplicada

Arquivo principal: `tools/blender/build_heroi_julia.py`.

1. **Dedos contínuos** — cada dedo deixou de ser 3 cápsulas independentes e virou
   um tubo orgânico único com perfil de raio por anel. As articulações agora são
   estreitamentos suaves, não cortes geométricos.
2. **Ponta arredondada** — o perfil final usa queda curta de raio em múltiplos
   anéis, evitando dedo cônico/pontudo.
3. **Palma superelíptica** — a palma voltou a ser um volume arredondado e
   estável para bake/rig, estreito no punho e na linha dos nós.
4. **Nós dos dedos** — pequenas almofadas elipsoides escondem a borda da palma e
   dão leitura de mão real sem boolean destrutivo.
5. **Gate manifold preservado** — os elipsoides usam polos únicos (sem anéis
   degenerados), mantendo 0 arestas não-manifold.
6. **Render de close dedicado** — criado `tools/blender/render_hand_closeup.py`
   para auditar mão/punho sem depender do turnaround distante.

## Métricas finais do checkpoint

| Métrica | Resultado |
| --- | ---: |
| Vértices | 19.594 |
| Faces | 19.601 |
| Triângulos | 39.104 |
| Quads | 93,1% |
| Altura | 1,720 m |
| Piso | 0,012 m |
| Não-manifold | 0 |
| UV atlas | 61,1% |
| GLB PBR | 1.736,5 KB |

Gates Fase 1/Fase 2 continuam verdes: triângulos dentro do alvo, escala correta,
malha manifold, 3 texturas PBR embarcadas, atlas acima de 45% e GLB abaixo de
2 MB.

## Artefatos salvos

- `docs/arte_alvo_final/12_bracos_maos_corrigidos.png` — turnaround PBR final.
- `docs/arte_alvo_final/13_mao_corrigida_closeup.png` — close final da mão.
- `assets/characters/source/heroi_julia_bracos_maos_wip.glb` — checkpoint WIP,
  fora do runtime por enquanto.

## Próximo passo

Não precisa criar do zero. O corpo base está aproveitável. O próximo trabalho é
continuar a Fase 3: rosto/cabelo/olhos; depois rig/skin (Fase 4) e roupa de jogo
(Fase 6) antes de promover para `assets/characters/personagens/hero_julia.glb`.
