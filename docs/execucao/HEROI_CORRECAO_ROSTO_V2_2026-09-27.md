# Correção visual da Júlia — rosto V2 (27/09/2026)

## Diagnóstico do modelo reprovado

A reprovação visual estava correta. O GLB anterior não falhou por iluminação: a
geometria estava errada.

- A cabeça era a ponta do mesmo grafo `Skin` usado no tronco. Isso produziu um
  crânio alto, bulboso e sem mandíbula definida.
- As “orelhas” eram apenas deslocamentos gaussianos de alguns vértices; não
  existia uma malha de orelha legível.
- Olhos, pálpebras, sobrancelhas, cílios e boca eram fitas/cards frontais. Em
  perfil, as peças flutuavam; de frente, pareciam recortes.
- Os olhos tinham proporção e profundidade incompatíveis com o rosto.
- O nariz era pouco definido e o cabelo era composto por placas largas com
  silhueta quebrada.
- O export de runtime continuava apontando para o placeholder de 61 KB, não
  para o trabalho de rosto em andamento.

## O que foi reconstruído

O módulo `tools/blender/julia_head_v2.py` agora gera:

- cabeça ovoide independente, com têmporas, maçãs, mandíbula e queixo;
- duas orelhas completas, com hélice e concha;
- nariz volumétrico suave, com ponte, ponta, asas e narinas;
- olhos menores e separados, com esclera, íris, pupila e brilho;
- quatro pálpebras geométricas, sobrancelhas e cílios curtos;
- boca com lábios volumétricos e linha de fechamento;
- cabelo cacheado opaco e volumétrico em tubos, sem cards, incluindo seis
  cachos frontais, laterais e catorze mechas no rabo de cavalo;
- materiais separados para pele, camisa, legging, tênis, olhos, lábios e cabelo.

O antigo crânio do corpo é encolhido para dentro da nova cabeça. Assim, o corpo
permanece manifold e o pescoço continua conectado sem z-fighting.

## Resultado técnico

- 68.096 triângulos no LOD de autoria;
- 1,72 m de altura;
- piso em z = 0,012 m;
- zero arestas não-manifold no corpo-base;
- 1,40 MB, GLB 2.0 sem Draco;
- asset corrigido promovido a
  `assets/characters/personagens/hero_julia.glb`.

Evidências visuais:

- `docs/arte_alvo_final/19_turnaround_rosto_v2.png`;
- `docs/arte_alvo_final/20_rosto_v2_5_angulos.png`;
- `docs/arte_alvo_final/21_rosto_v2_frente.png`.

## Escopo ainda pendente

Esta correção resolve a identidade e a construção visual do GLB estático. Rig,
skinning, animações faciais/corporais e acabamento final de roupa continuam nas
fases 4–6; não devem ser declarados concluídos antes dos respectivos gates.
