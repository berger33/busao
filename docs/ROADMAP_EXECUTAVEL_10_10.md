# Roadmap executável — qualidade gráfica 10/10 mobile 3D

Este roadmap divide a meta em etapas pequenas, verificáveis e reversíveis. Cada etapa deve gerar código/assets, um relatório de aceite e uma captura ou métrica comparável.

## Etapa 1 — Baseline e instrumentação

**Objetivo:** registrar o estado real antes das melhorias.

Entregáveis:
- inventário de assets e tamanhos;
- contagem de GLBs, texturas e scripts visuais;
- verificação do hero atual;
- registro do renderer/configuração;
- lista de bloqueadores gráficos;
- relatório versionado em `docs/quality_baseline.json`.

**Aceite:** script reproduzível, JSON válido e nenhum dado inventado de FPS.

## Etapa 2 — Heroína jogável

- malha humana dedicada;
- rig mínimo compatível;
- Idle/Walk/Sprint/Jump/Crouch;
- validação de escala, eixo, pés, mãos e clipping;
- captura 720×1280.

## Etapa 3 — Pipeline de assets e LOD

- manifesto por asset;
- LOD0/LOD1/LOD2;
- limites de triângulos, materiais e memória;
- importação sem Draco incompatível;
- validação automática.

## Etapa 4 — Chão e calçadas

- macro/micro variation;
- desgaste, remendos, juntas, poças e decals;
- redução de tiling e ruído;
- teste de close-up e corrida.

## Etapa 5 — Arquitetura urbana

- fachadas com profundidade;
- portas, janelas, beirais, grades e lojas;
- variação brasileira por capítulo;
- HLOD de quarteirão.

## Etapa 6 — Veículos e ponto final

- carrocerias beveladas;
- rodas/calotas alinhadas;
- interiores simplificados;
- tráfego na rua;
- ônibus e abrigo com sinalização final.

## Etapa 7 — Vegetação e vida urbana

- espécies variadas;
- LOD/impostors;
- fauna, pedestres, postes e props sem interseção;
- sombras e translucência controladas.

## Etapa 8 — Iluminação e clima

- presets de sol, nublado, chuva e entardecer;
- exposição e balanço de branco;
- sombras de contato;
- fallback Mobile/Compatibility.

## Etapa 9 — HUD, UX e acessibilidade

- HUD mínimo;
- gestos configuráveis;
- tutorial progressivo;
- loja com prévia 3D;
- resultado com ação primária;
- escala de fonte, daltonismo, vibração e alto contraste.

## Etapa 10 — QA final

- matriz de aparelhos/perfis;
- FPS, frame time, memória e draw calls;
- capturas comparativas;
- zero gaps, T-pose, clipping, veículo na calçada ou UI cortada;
- aprovação final ou rollback.

## Regra de avanço

Uma etapa só é marcada como concluída quando seu relatório de aceite está versionado. A próxima etapa é sempre indicada no relatório e no resumo da entrega.
