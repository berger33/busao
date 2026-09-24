# Auditoria de qualidade gráfica — estado atual

**Data:** 2026-09-22  
**Escopo:** cenário 3D, materiais, iluminação, personagens, HUD/UI, câmera, VFX e consistência de runtime.  
**Método:** inspeção dos scripts/assets/configuração + validação do GLB da heroína. Não foi possível executar uma captura real do jogo neste sandbox.

## Veredito

O projeto está visualmente coerente e possui uma boa base de direção de arte, mas ainda está distante de realismo de nível GTA V. O maior bloqueio não é mais o HUD: é a qualidade e o pipeline das malhas humanas, seguido pelo chão/fachadas e pela ausência de animação no novo herói procedural.

**Nota técnica atual estimada: 5,8/10 para mobile 3D estilizado-realista.**  
**Nota para “realismo GTA V”: 2,5/10.**

## Resumo por área

| Área | Nota | Estado | Principal gap |
|---|---:|---|---|
| Iluminação | 6,5 | Boa base | GI/SSAO dependem do renderer; ainda falta iluminação de preenchimento por cenário |
| Sombras | 6,5 | Melhoradas | contato e estabilidade ainda precisam de captura em aparelho real |
| Materiais PBR | 5,5 | PBR presente | mapas procedurais e tiling ainda perceptíveis |
| Asfalto/calçada | 5,0 | Escala/height ajustados | textura ainda pode parecer granular; falta detalhe macro e desgaste por fluxo |
| Prédios | 4,8 | Fachadas com PBR e janelas | volumes muito simples, pouca variação arquitetônica, sem beirais/reentrâncias reais |
| Árvores | 7,0 | Melhor elemento atual | ainda há gap de variação de espécie, folhas e sombras de transparência |
| Veículos | 5,5 | Modelos e materiais funcionais | carrocerias simplificadas e interiores ausentes |
| Personagens | 3,5 | Hero mesh-only criada | sem rig/animação; anatomia e rosto ainda abaixo do objetivo |
| Animação humana | 3,0 | elenco tem clips, hero não | mãos/braços e deformação ainda não estão em nível natural |
| HUD | 7,0 | Hierarquia e ícones melhorados | loja/resultados ainda precisam de mais fluxo e menos texto |
| UX mobile | 6,0 | gestos + tutorial progressivo | falta calibração/sensibilidade e feedback dedicado por gesto |
| VFX/clima | 5,8 | chuva, poças, poeira e relâmpago | efeitos ainda são funcionais, não cinematográficos |
| Consistência visual | 5,5 | paleta e escala em evolução | personagem, prédios e chão ainda parecem de pipelines diferentes |

## Evidências técnicas

### Personagem principal — bloqueador atual

- `hero_julia.glb` existe e passa validação estrutural.
- O asset atual é **mesh-only**, com 26 partes e aproximadamente 67 KB.
- A validação confirma ausência dos clips `Idle_Loop`, `Walk_Loop`, `Sprint_Loop`, `Jump_Loop` e `Crouch_Fwd_Loop`.
- O runtime aceita o mesh-only e movimenta o root, mas não há deformação de esqueleto.
- O resultado não deve ser chamado de qualidade GTA V: faltam rig, dedos articulados, blendshapes, facial, cabelo detalhado, dobras e animação.

**Ação obrigatória:** criar um rig mínimo com pelvis/spine/limbs e retargetar os cinco clips antes de validar a heroína como personagem final.

### Cenário

- O `BuildingKit` já usa `ORMMaterial3D`, normal, roughness, triplanar e height map.
- A variação de comprimento dos quarteirões foi zerada para fechar as lacunas.
- A escala das texturas de asfalto, calçada, tijolo e reboco foi reduzida para conter ruído e repetição.
- Ainda há geometria predominantemente prismática: prédios são fachadas/volumes, com pouca profundidade construtiva.
- O chão precisa de mapas macro/micro separados, manchas de pneu, remendos, juntas e variação de roughness por zona.

### Iluminação

- O projeto tem ACES, debanding, MSAA, SSAO, sombras direcionais e ReflectionProbe.
- O caminho `gl_compatibility` limita recursos avançados; SDFGI/VoxelGI não são garantidos nesse renderer.
- A iluminação deve ser testada em Android real, pois o preview de desktop não representa Adreno/Mali.

### Interface

- HUD da corrida foi simplificado e ganhou rota, ícones e aviso de aproximação.
- A seta que indicava a faixa foi removida corretamente.
- Tutorial agora é progressivo: faixa, dash, pulo e deslize.
- Ainda faltam prévia 3D ampla na loja, filtros, escala tipográfica configurável e modo daltônico completo.

## Bloqueadores de aceite

O jogo não deve ser considerado “realista” enquanto estes itens estiverem abertos:

1. Hero sem rig e sem clips.
2. Hero sem deformação natural de mãos, ombros, joelhos e quadril.
3. Prédios ainda sem profundidade de fachada suficiente.
4. Piso com textura procedural repetitiva em close.
5. Falta de captura comparativa em 720×1280 no Android alvo.
6. Ausência de orçamento medido de draw calls, memória e FPS por renderer.

## Plano recomendado de fechamento

### P0 — Hero jogável

- Criar esqueleto no fallback procedural ou obter runtime Blender funcional.
- Separar cabeça, torso, braços, mãos, pernas, cabelo e roupa como partes skinnable.
- Adicionar rig mínimo compatível com os nomes já usados pelo jogo.
- Gerar `Idle`, `Walk`, `Sprint`, `Jump`, `Crouch` e aterrissagem.
- Validar pés, mãos, cotovelos e alinhamento de eixo.

### P1 — Chão e arquitetura

- Criar macro variation de asfalto/calçada.
- Reduzir tiling visível por quarteirão.
- Adicionar bordas, beirais, sacadas, portas recuadas e variação de altura.
- Usar decals de sujeira, remendo, faixa desgastada e umidade.

### P2 — UX final

- Prévia 3D da personagem na loja.
- Tela de resultado com duas ações primárias.
- Opção de sensibilidade de gesto e botões virtuais.
- Tamanho de fonte, daltonismo e vibração configuráveis.

### P3 — QA visual/performance

- Capturas de cada capítulo em resolução final.
- Teste Forward+/Mobile/Compatibility.
- Medição de FPS, memória, draw calls, tempo de carregamento e artefatos de sombra.
- Checklist de clipping, z-fighting, gaps de chunks e materiais sem textura.

## Conclusão

A base gráfica está evoluindo, mas a auditoria confirma que a principal promessa pendente é a personagem humana. O próximo trabalho deve priorizar rig/animação da heroína e só depois produzir o restante do elenco. O cenário e o HUD já têm uma direção funcional; precisam de refinamento de assets, não de mais efeitos isolados.
