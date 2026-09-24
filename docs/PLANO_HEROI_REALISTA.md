# Plano de produção — personagem principal realista

## Objetivo

Substituir o humano procedural atual por uma personagem principal com proporções humanas reais, silhueta natural e acabamento de personagem de jogo 3D. A referência de qualidade é GTA V; no primeiro marco a personagem precisa validar a direção visual antes de produzir o restante do elenco.

> GTA V é uma referência AAA de alta complexidade. Não será tratado como um ajuste de textura: exige nova malha, materiais, cabelo, olhos, rig e animações.

## Marco 1 — heroína jogável para validação

- Altura de referência: 1,68–1,75 m.
- 7,25–7,75 cabeças de altura; mãos abaixo do meio da coxa; ombros e quadril com proporções anatômicas, sem silhueta de boneco.
- Malha final: 35–60 mil triângulos, com bevel real em pálpebras, nariz, lábios, dedos, joelhos, cotovelos e tênis.
- Rosto: olhos inseridos na órbita, córnea separada, íris/pupila, pálpebras e boca com volume; sem olhos pintados na textura.
- Cabelo: volume em mechas/cards com alpha, raiz e pontas irregulares; não uma esfera lisa.
- Roupa: camiseta, calça e tênis com costuras, barras, dobras de compressão e materiais separados.
- Texturas: 2K mobile (albedo, normal, roughness, AO/curvature e máscara de pele); 4K apenas para captura de alta qualidade.
- Pele: SSS moderado, variação de roughness, micro-normal e blush/occlusion por máscara.
- Rig: corpo humano de 55–65 ossos, dedos e clavículas; animação preservando contato dos pés.
- Animações: idle respirando, walk, sprint, jump, landing e crouch, com transições e braços em antifase.

## Marco 2 — integração Godot

- O arquivo `hero_julia.glb` será carregado antes dos personagens genéricos.
- O contrato de animação será mantido: `Idle_Loop`, `Walk_Loop`, `Sprint_Loop`, `Jump_Loop`, `Crouch_Fwd_Loop` e `Crouch_Idle_Loop`.
- O personagem deve ficar entre 1,68 e 1,75 m no runtime, medido pela AABB do esqueleto.
- Validação visual em 720×1280, câmera de corrida e modo de captura.
- Critérios: pés no chão, mãos separadas, cotovelos naturais, rosto legível a 2–4 m, sem clipping de roupa/cabelo e sem materiais plásticos.

## Marco 3 — elenco

Depois da aprovação da heroína, derivar o corpo-base para os 20 personagens, variando rosto, pele, cabelo, roupa, idade, peso e postura. Não duplicar apenas a cor do mesmo boneco.

## Próximo trabalho técnico

1. Modelar/retopologizar a heroína em Blender com o checklist acima.
2. Fazer UV e bake dos mapas PBR.
3. Exportar `assets/characters/personagens/hero_julia.glb` sem Draco.
4. Rodar a captura comparativa e ajustar escala, materiais e animação.
5. Só então substituir progressivamente os NPCs.
