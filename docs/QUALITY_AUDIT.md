# Auditoria de qualidade — Corre pro Ponto

Data da varredura: 17/09/2026.

## Resultado rápido

- **Cena de entrada:** `scenes/main.tscn` agora instancia `CorreProPonto3D` como `Node3D` e usa `scripts/game_3d.gd`.
- **Apresentação:** runner em terceira pessoa, com câmera atrás/acima do personagem, avanço visual no eixo `-Z`, HUD 2D sobreposta e ponto de ônibus 3D no fim de cada corrida.
- **Movimento:** `course_root` desliza com a distância, levando pista, fachadas, obstáculos e ponto de ônibus; passos, balanço de câmera, inclinação do corpo, pernas/braços, FOV e partículas acompanham a velocidade.
- **Progressão visual:** `ScenarioData` divide as 50 fases em dez capítulos de cinco fases: favela de terra, bairro residencial, centro, bairro humilde, classe média, militar/cívico, religioso, comercial, turístico e terminal final.
- **Pista:** três faixas com contrato espacial fixo: índice 0 / X -3.25 = rua; índices 1 e 2 / X 0.0 e 3.25 = calçadas. Asfalto, ladrilhos, meio-fio, divisor, linhas da rua e obstáculos tornam a separação visível.
- **Densidade:** `_build_course()` usa intervalos menores para a rua que para as calçadas. A rua recebe carros, ônibus, motos, buracos e caminhões; as calçadas recebem velha usando celular, hidrante, orelhão, cachorro, bicicleta, cone, camelô e banco.
- **Catálogo:** 50 fases, incluindo 30 telas da expansão, continuam em `scripts/phase_data.gd` e são consumidas pelo runner 3D.
- **Progressão:** `GameSave`, loja, personagens, desafios diários, conquistas, moedas, estrelas, Endless e streak continuam conectados ao HUD 3D.
- **Assets:** SVGs do ícone, superfícies e mapas normais, PNGs de asfalto/calçada e três panoramas de céu (dia, entardecer e nublado), além de WAVs legíveis; os meshes 3D recebem materiais gerados em GDScript, sem download em runtime.
- **Céu e atmosfera:** `PanoramaSkyMaterial` usa panorama tropical com nuvens; fog/aerial perspective, tonemapping, glow sutil, iluminação e energia variam por capítulo, com vida aérea contextual: pombo, urubu, passarinho, drone, avião e gaivota.
- **Personagens:** catálogo procedural com 10 humanos brasileiros, cinco masculinos e cinco femininos; torso, cabeça, braços, pernas, mãos, rosto, cabelo com fibras, pele com subsurface scattering, jeans e acessórios são meshes 3D texturizados, com juntas de cotovelo/joelho e pivôs de passada, salto e agachamento. O estilo visual é compartilhado por todo o catálogo; o avatar Creator acrescenta top, shorts, botas, brincos e detalhes metálicos.
- **Tráfego:** carros, ônibus, motos e caminhões são assemblies 3D detalhados com cabine, vidros, faróis, lanternas, para-choques, rodas orientadas e velocidade própria no eixo da rua.
- **Preflight reproduzível:** `python3 tools/validate_project.py` passou após a migração.
- **Parser auxiliar:** `gdparse scripts/game_3d.gd` e `gdparse scripts/hud_3d.gd` passaram; isso não substitui a importação pelo editor Godot.
- **Godot editor:** não está instalado neste ambiente; o parser/editor headless, a renderização efetiva e a exportação Android ainda precisam ser executados em uma máquina com Godot 4.x e SDK Android.

## Verificações realizadas nesta etapa

1. A cena principal deixou de apontar para o controlador 2D e passou a apontar para `res://scripts/game_3d.gd` em um nó raiz `Node3D`.
2. `scripts/hud_3d.gd` foi criado como `Control` desenhado sobre um `CanvasLayer`, com menu, mapa das 50 fases, corrida, pausa, chegada, resultados, loja, conquistas, desafios diários e guia de controles.
3. O controlador 3D cria iluminação direcional, panorama tropical, fog, glow, câmera, jogador, prédios, árvores, postes, ponto e ônibus no carregamento do mundo.
4. A geração de obstáculos mantém categorias por espaço: tráfego somente na rua e elementos urbanos/pedestres somente nas calçadas; veículos recebem velocidade e animação de rodas enquanto avançam.
5. A troca de faixa, pulo, deslize, dash, colisão, coleta, combo, partículas 3D, tremor, áudio, save e progressão foram mantidos na implementação 3D.
6. A movimentação do mundo foi ligada à distância da corrida: a câmera permanece em terceira pessoa enquanto `course_root` avança sob o personagem, evitando a sensação de personagem deslizando em um fundo parado.
7. Os 10 personagens foram catalogados em `scripts/character_data.gd` e o menu de loja passou a mostrar seus estilos, gênero de apresentação, preço, descrição e estado equipado.
8. Os meshes recebem texturas raster realistas para asfalto/calçada, mapas normais e mapeamento triplanar; as demais superfícies usam materiais SVG específicos para terra, tijolo, reboco, metal, vidro, tecido, pele, madeira, borracha e folhas.
9. O personagem usa pivôs de membros, cotovelos/joelhos, rosto, cabelo e materiais de pele, fibra e jeans; a passada, o salto e o agachamento mudam a pose. Os meshes de tráfego possuem detalhes 3D reconhecíveis: cabine, faróis, vidros, para-choques, guidão, carga, rodas e acessórios.
10. O preflight confirmou caminhos `res://`, ausência de funções duplicadas, balanceamento de catálogo, 50 fases, SVG e metadados dos WAVs:

   ```text
   PRE-FLIGHT OK: paths, scripts, 50-phase catalog, SVG/PNG textures, WAV and feedback audio assets
   ```

## Limitações conhecidas / validação ainda obrigatória

- Não há binário Godot 4.x disponível no sandbox para executar `godot --headless --editor --quit --path .`; portanto, a confirmação final de parser, import de cena, APIs 3D e warnings do editor está pendente.
- Ainda é necessário fazer uma exportação APK debug, instalar em Android 8.0 ou superior e medir FPS, memória, aquecimento e consumo em um aparelho médio.
- É necessário testar safe areas, notch, botão Voltar do Android, pausa ao perder foco, áudio interrompido por chamada/notificação e gestos em telas com diferentes densidades.
- O pacote usa `GL Compatibility` para manter o alvo Android amplo. A contagem de meshes, sombras e partículas deve ser medida em aparelho real antes da publicação.
- O runner 3D usa geometria procedural e não substitui a validação de design/arte por capítulo; o HUD, o balanceamento de colisão e a legibilidade dos obstáculos devem receber playtest.
- Não há SDK de anúncios ou permissões de rede no runner 3D. Qualquer revive recompensado só deve entrar depois de consentimento, política de privacidade e fluxo validado para a LGPD.

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
- [x] Dez personagens humanoides 3D, cinco masculinos e cinco femininos, com rosto, pele, cabelo, jeans/tecidos, juntas de cotovelo/joelho, acessórios, passada, salto e agachamento.
- [x] Texturização realista do chão com PNGs e mapas normais, além de prédios, lojas, construções, veículos, obstáculos, personagens e vegetação.
- [x] Carros, ônibus, motos e caminhões avançando na rua com velocidades próprias e rodas animadas.
- [x] Obstáculos urbanos detalhados em assemblies 3D reconhecíveis, em vez de um único bloco geométrico.
- [x] 50 fases, save, progressão, loja, personagens, desafios, áudio e feedback conectados.
- [ ] Parser/importação real no Godot 4.x.
- [ ] APK Android e teste em aparelho real.

## Próximos passos de produção

1. Rodar o editor Godot 4.7 em modo headless e abrir a cena principal.
2. Corrigir qualquer erro de parser, warning de API ou material reportado pelo editor.
3. Exportar APK debug, instalar em um Android 8.0+ e executar o checklist de gestos, pausa e safe area.
4. Medir 60 FPS em celular médio; reduzir sombras, segmentos de meshes ou partículas se necessário.
5. Exportar AAB assinado com keystore fora do repositório e validar em internal testing do Play Console.
6. Só então considerar a migração 3D pronta para publicação.
