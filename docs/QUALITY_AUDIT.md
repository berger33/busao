# Auditoria de qualidade — Corre pro Ponto

Data da varredura: 18/09/2026.

## Resultado rápido

- **Cena de entrada:** `scenes/main.tscn` agora instancia `CorreProPonto3D` como `Node3D` e usa `scripts/game_3d.gd`.
- **Apresentação:** runner em terceira pessoa, com câmera atrás/acima do personagem, avanço visual no eixo `-Z`, HUD 2D sobreposta e ponto de ônibus 3D no fim de cada corrida.
- **Movimento:** `course_root` desliza com a distância, levando pista, fachadas, obstáculos e ponto de ônibus; passos, balanço de câmera, inclinação do corpo, pernas/braços, FOV e partículas acompanham a velocidade.
- **Progressão visual:** `ScenarioData` divide as 50 fases em dez capítulos de cinco fases: favela de terra, bairro residencial, centro, bairro humilde, classe média, militar/cívico, religioso, comercial, turístico e terminal final.
- **Pista:** três faixas com contrato espacial fixo: índice 0 / X -3.25 = rua; índices 1 e 2 / X 0.0 e 3.25 = calçadas. Asfalto, ladrilhos, meio-fio, divisor, linhas da rua e obstáculos tornam a separação visível.
- **Densidade:** `_build_course()` usa intervalos menores para a rua que para as calçadas. A rua recebe carros, ônibus, motos, buracos e caminhões; as calçadas recebem velha usando celular, hidrante, orelhão, cachorro, bicicleta, cone, camelô e banco.
- **Catálogo:** 50 fases, incluindo 30 telas da expansão, continuam em `scripts/phase_data.gd` e são consumidas pelo runner 3D.
- **Progressão:** `GameSave`, loja, personagens, desafios diários, conquistas, moedas, estrelas, Endless e streak continuam conectados ao HUD 3D.
- **Assets:** SVGs do ícone, superfícies e mapas normais, PNGs de asfalto/calçada, três panoramas de céu (dia, entardecer e nublado), fibras de cabelo, jeans, pintura automotiva e materiais dos adapters 3D, WAVs legíveis e o pacote humano Quaternius em `assets/characters/quaternius/`. Corpo, cabelo, olhos, roupa, binários, mapas PBR, licença, AnimationLibrary, hashes, pedestre, animal, coletáveis, cenário e props ficam versionados; nada é baixado em runtime.
- **Céu e atmosfera:** `PanoramaSkyMaterial` usa panorama tropical com nuvens; fog/aerial perspective, tonemapping, glow sutil, iluminação e energia variam por capítulo, com vida aérea contextual: pombo, urubu, passarinho, drone, avião e gaivota.
- **Personagem principal e NPCs:** catálogo de 10 identidades, cinco masculinas e cinco femininas, com representação baseada no humanoide Quaternius GLTF/skinned real. Corpo, rosto, olhos e cabelo usam o asset Universal Base Characters; roupa modular e mapas PBR vêm de meshes separados. Para Nina Creator, `runner_character.gd` mantém top, shorts jeans, botas, telefone, tatuagem, brincos, pulseiras, lantejoulas e metal em `BoneAttachment3D`, todos acompanhando o esqueleto. `world_character.gd` reutiliza o mesmo humanoide para velha e camelô, em vez de cabeças/cápsulas. `world_animal.gd` concentra o cachorro caramelo 3D com anatomia e animação de cauda/patas. A escala de 2,15 m, os pés no piso, a sombra de contato e os clips de locomoção são preservados, sem montar o corpo principal com cápsulas.
- **Tráfego:** carros, ônibus, motos e caminhões são assemblies 3D detalhados com cabine, vidros, faróis, lanternas, para-choques, placas, retrovisores, maçanetas, rodas orientadas e velocidade própria no eixo da rua. Os carros variam entre hatch compacto, sedã compacto e utilitário/van inspirados na frota popular brasileira, sem logotipos.
- **Preflight reproduzível:** `python3 tools/validate_project.py` passou após a migração.
- **Preflight auxiliar:** `python3 tools/validate_project.py` inclui referências, binários, texturas, clips e manifesto SHA-256; a importação/renderização dos GLTF/GLB e a sintaxe final da nova camada `BoneAttachment3D` ainda precisam passar pelo editor Godot 4.x.
- **Godot/parser:** não estão instalados neste ambiente; o parser/editor headless, a renderização efetiva, o retarget da AnimationLibrary e a exportação Android ainda precisam ser executados em uma máquina com Godot 4.x e SDK Android.

## Verificações realizadas nesta etapa

1. A cena principal deixou de apontar para o controlador 2D e passou a apontar para `res://scripts/game_3d.gd` em um nó raiz `Node3D`.
2. `scripts/hud_3d.gd` foi criado como `Control` desenhado sobre um `CanvasLayer`, com menu, mapa das 50 fases, corrida, pausa, chegada, resultados, loja, conquistas, desafios diários e guia de controles.
3. O controlador 3D cria iluminação direcional, panorama tropical, fog, glow, câmera, jogador, prédios, árvores, postes, ponto e ônibus no carregamento do mundo.
4. A geração de obstáculos mantém categorias por espaço: tráfego somente na rua e elementos urbanos/pedestres somente nas calçadas; veículos recebem velocidade e animação de rodas enquanto avançam.
5. A troca de faixa, pulo, deslize, dash, colisão, coleta, combo, partículas 3D, tremor, áudio, save e progressão foram mantidos na implementação 3D.
6. A movimentação do mundo foi ligada à distância da corrida: a câmera permanece em terceira pessoa enquanto `course_root` avança sob o personagem, evitando a sensação de personagem deslizando em um fundo parado.
7. Os 10 personagens continuam catalogados em `scripts/character_data.gd` e o menu de loja continua mostrando estilos, gênero de apresentação, preço, descrição e estado equipado; a aparência de gameplay passa pelo adaptador humano skinned compartilhado.
8. Os meshes recebem texturas raster realistas para asfalto/calçada, mapas normais e mapeamento triplanar; as demais superfícies usam materiais SVG específicos para terra, tijolo, reboco, metal, vidro, tecido, pele, madeira, borracha e folhas.
9. O personagem principal usa meshes GLTF reais com esqueleto humanoide, cabelo/olhos/pele texturizados, roupa skinned e materiais PBR separados. Para Nina Creator, o mesmo esqueleto recebe top, shorts jeans, botas, telefone, tatuagem, brincos, pulseiras, lantejoulas e metal com `BoneAttachment3D`. A Universal Animation Library seleciona `Idle_Loop`, `Sprint_Loop`, `Jump_Loop`, `Crouch_Idle_Loop` e `Crouch_Fwd_Loop`; um fallback de pose procedural só é acionado se a importação/clips falharem.
10. Os meshes de tráfego e props possuem detalhes 3D reconhecíveis: silhuetas de hatch, sedã e utilitário populares, cabine, faróis, vidros, placas, retrovisores, para-choques, guidão, carga, rodas, hidrante, orelhão, bicicleta, carrinho, banco e acessórios. O cone de obra é laranja com base e faixas refletivas; velha e camelô são instâncias humanas skinned; o cachorro caramelo possui focinho, olhos, orelhas, quatro pernas, patas, coleira, tag e cauda animada. O contrato de runtime audita `MeshInstance3D` em toda entidade.
11. O preflight confirmou caminhos `res://`, ausência de funções duplicadas, balanceamento de catálogo, 50 fases, SVG e metadados dos WAVs:

   ```text
   PRE-FLIGHT OK: paths, scripts, 50-phase catalog, 13-obstacle 3D contract, SVG/PNG textures, WAV and feedback audio assets
   ```

## Limitações conhecidas / validação ainda obrigatória

- Não há binário Godot 4.x disponível no sandbox para executar `godot --headless --editor --quit --path .`; portanto, a confirmação final de parser, importação GLTF/GLB, retarget da AnimationLibrary, APIs 3D e warnings do editor está pendente.
- Ainda é necessário fazer uma exportação APK debug, instalar em Android 8.0 ou superior e medir FPS, memória, aquecimento e consumo em um aparelho médio.
- É necessário testar safe areas, notch, botão Voltar do Android, pausa ao perder foco, áudio interrompido por chamada/notificação e gestos em telas com diferentes densidades.
- O pacote usa `GL Compatibility` para manter o alvo Android amplo. A contagem de meshes, sombras e partículas deve ser medida em aparelho real antes da publicação.
- O runner 3D usa geometria procedural e não substitui a validação de design/arte por capítulo; o HUD, o balanceamento de colisão e a legibilidade dos obstáculos devem receber playtest.
- Não há SDK de anúncios ou permissões de rede no runner 3D. Qualquer revive recompensado só deve entrar depois de consentimento, política de privacidade e fluxo validado para a LGPD.

## Auditoria do asset humano

- **Asset principal:** `assets/characters/quaternius/base/Superhero_Male_FullBody.gltf` e variante feminina, com binário, cabelo, olhos, pele, normal e roughness.
- **Roupa:** `assets/characters/quaternius/parts/*Peasant*.gltf`, com Body/Arms/Legs/Feet separados e mapas `T_Peasant_*`/`T_Regular_*`.
- **Rig e animação:** cada GLTF de corpo/roupa declara skin, joints e weights; `animation/UAL1_Standard.glb` contém os clips completos e `animation/UAL1_Standard.res` é o cache compacto offline.
- **Integração:** `runner_character.gd` monta o asset no `_ready`, anexa as roupas ao Skeleton3D, remove o poke-through por divisão regional/inflação de malha, controla estado de locomoção e expõe fallback isolado.
- **Licença:** CC0 1.0 e origem oficial registradas em `CREDITS.md`, `QUATERNIUS-LICENSE.txt` e `PROVENANCE.md`; o validator verifica a presença dos arquivos, referências de textura/binário, skin weights, assinatura GLB, clips e PNGs.

## Checklist de aceite do modo 3D

- [x] Terceira pessoa correndo para frente até o ponto de ônibus.
- [x] Faixa esquerda exclusivamente rua.
- [x] Faixas central e direita exclusivamente calçadas.
- [x] Rua com densidade maior de obstáculos.
- [x] Carros, ônibus, motos, buracos, caminhões e variações de trânsito na rua.
- [x] Velha usando celular, hidrante, orelhão, cachorro, bicicleta, cone, camelô, banco e objetos urbanos nas calçadas.
- [x] Separação comunicada por geometria, meio-fio, materiais, ladrilhos, linhas e categorias.
- [x] Cenário móvel com animação de corrida, passos, câmera, FOV e scroll do mundo.
- [x] Dez capítulos de cenário brasileiro com casas, prédios, lojas, construções e marcos temáticos.
- [x] Panorama tropical com nuvens, fog, aerial perspective, glow sutil, cores por capítulo e fauna/tráfego aéreo animado.
- [x] Asset humano 3D principal rigged/skinned, com corpos masculino/feminino, rosto, pele, cabelo, olhos, roupa modular com materiais PBR separados, escala e contato dos pés; corrida, salto e agachamento usam clips/pose de fallback.
- [x] Texturização realista do chão com PNGs e mapas normais, além de prédios, lojas, construções, veículos, obstáculos, personagens e vegetação.
- [x] Carros, ônibus, motos e caminhões avançando na rua com velocidades próprias e rodas animadas.
- [x] Obstáculos urbanos brasileiros detalhados em assemblies 3D reconhecíveis: cone laranja refletivo, cachorro caramelo articulado, hidrante, orelhão, bicicleta, camelô, banco e pedestre.
- [x] Pedestres de calçada usam personagens Quaternius GLTF/skinned reais; animais usam adapter 3D com anatomia, materiais e animação própria.
- [x] Contrato de obstáculos valida 13 tipos, espaço rua/calçada, `MeshInstance3D` e presença dos adapters humano/animal.
- [x] Carros com três silhuetas inspiradas em compactos populares brasileiros, pintura automotiva, placas, faróis, rodas, retrovisores e detalhes de carroceria.
- [x] 50 fases, save, progressão, loja, personagens, desafios, áudio e feedback conectados.
- [ ] Parser/importação real no Godot 4.x.
- [ ] APK Android e teste em aparelho real.

## Próximos passos de produção

1. Rodar o editor Godot 4.7 em modo headless e abrir a cena principal; confirmar a importação dos GLTF/GLB Quaternius.
2. Verificar visualmente o Skeleton3D, o encaixe Body/Arms/Legs/Feet, os pés no piso, o sentido de corrida e os clips de sprint, jump e crouch; corrigir qualquer erro de parser, retarget, warning de API ou material.
3. Exportar APK debug, instalar em um Android 8.0+ e executar o checklist de gestos, pausa e safe area.
4. Medir 60 FPS em celular médio; reduzir sombras, segmentos de meshes ou partículas se necessário.
5. Exportar AAB assinado com keystore fora do repositório e validar em internal testing do Play Console.
6. Só então considerar a migração 3D pronta para publicação.
