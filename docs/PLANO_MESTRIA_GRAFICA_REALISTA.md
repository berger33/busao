# PLANO MESTRE DE FIDELIDADE VISUAL E REALISMO 3D
**Referência Visual Canônica:** `abb89707-7fb0-4adc-a5f4-f3e4e81b48ef.jpg`  
**Data de Aprovação:** 20/09/2026  
**Status:** Em Execução (Etapa 1 Concluída, Etapa 2 em Andamento)

---

## 1. Visão Geral e Meta de Qualidade

Este documento é a **fonte única de verdade** para a evolução gráfica e física de *Corre pro Ponto*.
A meta estabelecida é transitar de um protótipo geométrico primitivo para uma experiência visual de alta fidelidade 3D no padrão de jogos mobile modernos triple-A, exatamente como demonstrado na imagem de referência **`abb89707-7fb0-4adc-a5f4-f3e4e81b48ef.jpg`**.

### Pilares da Referência Canônica:
1. **Corredora Atlética Realista:** Anatomia feminina natural (~1,75 m, 8 cabeças), postura biomecânica de corrida de alta performance (tronco inclinado a 8-10°, cotovelos flexionados a 90° bombeando no plano sagital, pernas com ciclo de passada amplo e contato de calcanhar/médio-pé no chão sem deslizamento). Cabelo escuro preso em rabo de cavalo com caimento dinâmico. Roupas esportivas modernas: camiseta técnica rosa/coral com microdobras de tecido, calça legging de compressão preta fosca de cintura alta, tênis de corrida com entressola branca de amortecimento e solado preto aderente.
2. **Calçada Ampla e Pavimentação Portuguesa / Concreto:** Lajes retangulares e paralelepípedos com juntas marcadas, desníveis sutis e variação de albedo/rugosidade. Canteiros de árvores com bordas de granito e bancos de praça de madeira e ferro fundido.
3. **Pista Viária e Sarjeta:** Meio-fio chanfrado de 15 cm separando a calçada da pista. Sarjeta com grelhas metálicas de bueiro para escoamento de chuva. Asfalto cinza escuro com granulação mineral, marcas de frenagem emborrachadas, faixas duplas contínuas amarelas desgastadas e carros contemporâneos proporcionais (hatchback branco, sedãs).
4. **Iluminação Golden Hour & Atmosfera:** Luz solar matinal/tarde quente incidindo em ângulo lateral (~32° de elevação), gerando sombras longas, suaves e diagonais cortando a calçada da esquerda para a direita. Preenchimento de céu aberto azulado suave nas sombras (contraste cromático quente/frio). Névoa atmosférica gradual no ponto de fuga da avenida, integrando prédios ao horizonte sem cortes abruptos.
5. **Interface (HUD) Minimalista:** Botão de pausa semi-transparente arredondado no canto superior esquerdo; mostrador de moedas no canto superior direito com moeda dourada 3D em alto relevo e tipografia limpa; controles de toque translúcidos e discretos na parte inferior.

---

## 2. Diagnóstico dos Erros Anteriores vs. Física Real

| Erro Anterior no Jogo | Causa no Código / Asset | Resolução Definitiva |
| :--- | :--- | :--- |
| **Cones na cabeça dos personagens** | `runner_character.gd:_get_placeholder_mesh()` carregava `cone.glb` como fallback de chapéus e adereços. | `_get_placeholder_mesh()` retorna `ArrayMesh.new()` vazio. Nenhum acessório é instanciado como cone viário. |
| **Sombra triangular no chão** | `runner_character.gd:_build_shadow()` carregava `cone.glb` rotacionado em -90°. | Substituído por disco elíptico suave gerado via `SurfaceTool` com gradiente radial transparente (`Color(0.015, 0.02, 0.03, 0.40)`). |
| **Pernas cônicas e cintura em caixa** | `build_humanos.py` e `build_personagens.py` montavam o corpo com `caixa()` e `pilar_z()` rígidos com pesos de vértice 1.0 (sem suavização). | Modelagem orgânica contínua com musculatura suave, joelhos e cotovelos definidos e *smooth skin weighting*. |
| **Braços em T-pose / Batendo palmas** | `_apply_procedural_fallback_pose()` rotacionava braços no eixo Z (plano lateral), batendo contra o peito ou para cima. Além disso, `using_external_animation` falhava na detecção. | Animações GLB em loop linear acionadas diretamente (`Sprint_Loop`). Fallback recalculado com cotovelos a 80° e balanço longitudinal sagittal (eixo X). |
| **Pedestres em pose estática** | `world_character.gd` pedia `Walk_Formal_Loop`, clipe inexistente no esqueleto. | Mapeado para o clipe nativo `Walk_Loop`. Todos os pedestres caminham suavemente pela calçada. |
| **Luz solar vertical e neblina sólida** | Sol em -48° vertical, neblina em densidade 0.0072 criando parede cinza opaca a 50 metros. | Sol reclinado em -32° lateral com sombras longas diagonais idênticas à referência `abb89707`. Neblina suavizada para 0.0034. |
| **Câmera distante e inclinada** | Câmera em Y=2.65 e Z=6.2 com inclinação excessiva. | Câmera rebaixada para Y=2.25 e Z=4.85 no ombro, mirando na linha do horizonte e nas costas da corredora com FOV 54°. |

---

## 3. Estrutura de Execução em 5 Etapas

### Etapa 1: Correções de Código e Física de Animação [CONCLUÍDA]
- [x] Eliminação de cones em cabeças, torsos e acessórios em `runner_character.gd`.
- [x] Sombra elíptica suave com `SurfaceTool` no chão, extinguindo o cone deitado.
- [x] Remoção do carregamento de `cone.glb` nos helpers `_box`, `_sphere`, `_capsule`, `_cylinder`, `_torus` em `game_3d.gd`.
- [x] Ativação contínua de `Sprint_Loop` no corredor jogável.
- [x] Ativação contínua de `Walk_Loop` nos pedestres em `world_character.gd`.
- [x] Reformulação da biomecânica da pose procedural (cotovelos a 80°, balanço longitudinal sagital).
- [x] Calibração de câmera para visão do ombro (Y=2.25, Z=4.85, FOV=54°).
- [x] Calibração de luz solar rasante (`Vector3(-32, -58, 0)`, `#fff3e0`) e atenuação da neblina (`density 0.0034`).

### Etapa 2: Refinamento dos Personagens 3D (Modelagem Orgânica & Roupas PBR) [EM ANDAMENTO]
- [ ] Geração do modelo anatômico feminino atlético de referência (`Júlia Atleta` / `Humano_F.glb`):
  - Tronco com silhueta humana suave (ombros torneados, peitoral definido, cintura fina, quadril atlético).
  - Pernas com modelagem anatômica contínua: coxas torneadas, joelhos com relevo patelar, panturrilhas com volume muscular afinando no tornozelo e pés em formato de calçado esportivo.
  - Braços com bíceps/tríceps sutis, cotovelos modelados, antebraços proporcionais e mãos relaxadas.
  - Cabeça esculpida com proporções cranianas reais, queixo e rabo de cavalo dinâmico com mechas de cabelo.
- [ ] Roupas esportivas PBR fiéis à imagem `abb89707`:
  - Camiseta esportiva atlética (mangas curtas, gola redonda, cor rosa/coral `#ea638c` com PBR de tecido).
  - Calça legging de compressão (cintura alta, preta fosca `#1a1a20` com textura de lycra/elastano).
  - Tênis esportivo moderno de corrida (entressola grossa de espuma amortecedora branca `#f0f2f5`, cabedal respirável cinza/preto e sola antiderrapante).
- [ ] Sistema de pesagem de ossos (*Skinning*) com transições suaves (interpolação entre ossos adjacentes: joelhos, cotovelos, ombros e cintura), acabando com os cortes mecânicos de cilindro/cone.
- [ ] Exportação GLB otimizada com compressão Draco mantendo arquivo leve (<350 KB) e 100% compatível com a suíte de validação `tools/qa_full.py`.

### Etapa 3: Cenário PBR de Calçada, Meio-fio e Pista
- [ ] Calçada com textura de lajes e paralelepípedos com relevo (Normal Map profundo, Roughness Map variando entre pedras secas e desgastadas).
- [ ] Meio-fio elevado de 15 cm com cantos chanfrados em granito escovado e grelhas pluviais de sarjeta em ferro fundido.
- [ ] Pista de asfalto cinza escuro com agregados minerais finos, marcas de frenagem emborrachadas e tampas redondas de bueiro de ferro fundido.
- [ ] Faixas centrais duplas contínuas amarelas com desgaste e microfissuras.
- [ ] Otimização dos veículos da pista (hatchback branco, sedãs) com pintura automotiva e reflexos de vidro.

### Etapa 4: Cenografia Urbana, Vegetação e Mobiliário
- [ ] Árvores urbanas realistas: troncos texturizados em casca de madeira com ramificações e copas frondosas de folhagem com recorte alfa e folhas semi-transparentes.
- [ ] Canteiros de calçada com moldura retangular de granito e terra vegetal.
- [ ] Postes de iluminação pública clássicos de ferro fundido com luminárias estilizadas distribuídos ao longo do meio-fio.
- [ ] Bancos de praça com ripas de madeira tratada e suportes de ferro fundido.
- [ ] Fachadas de edifícios com janelas recortadas, tijolos aparentes e cornijas arquitetônicas.

### Etapa 5: Pós-processamento e Interface (HUD)
- [ ] Calibração fina de tonemapping ACES com curva de contraste e exposição equilibrada.
- [ ] Bloom suave na iluminação solar e Depth of Field (DoF) sutil no horizonte para destacar a corredora.
- [ ] HUD minimalista integrado:
  - Botão de pausa translúcido arredondado no canto superior esquerdo.
  - Contador de moedas no canto superior direito com ícone 3D dourado e texto limpo.
  - Zonas de toque virtuais semi-transparentes na base da tela para imersão total.

---

## 4. Garantia de Compatibilidade e Não-Regressão

Qualquer modificação realizada deve obrigatoriamente manter os seguintes contratos aprovados:
1. `tools/qa_full.py`: 131 testes OK, 0 advertências, 0 falhas.
2. `tools/validate_project.py`: PRE-FLIGHT OK.
3. `tools/audit_balance.py`: BALANCE AUDIT OK (economia sem paywall).
4. `tools/audit_runner_rig.py`: Rig do corredor com 52 ossos, altura 1.82 m e sola a +0.012 m do solo.
5. Arquitetura orientada a arquivos em Git com rastreamento contínuo no branch `arena/01a0bce2-busao`.
