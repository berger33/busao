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
- **Economia transacional:** o save calcula preços e recompensas canônicas, ignora valores enviados pela HUD, deduplica inventário e torna claims diários/semanais idempotentes; referências legadas de `water_gun` e anúncios foram removidas.
- **Assets:** SVGs do ícone, superfícies e mapas normais, PNGs de asfalto/calçada, três panoramas de céu (dia, entardecer e nublado), fibras de cabelo, jeans, pintura automotiva e materiais dos adapters 3D, WAVs legíveis e o pacote humano Quaternius em `assets/characters/quaternius/`. Corpo, cabelo, olhos, roupa, binários, mapas PBR, licença, AnimationLibrary, hashes, pedestre, animal, coletáveis, cenário e props ficam versionados; nada é baixado em runtime.
- **Céu e atmosfera:** `PanoramaSkyMaterial` usa panorama tropical com nuvens; fog/aerial perspective, tonemapping, glow sutil, iluminação e energia variam por capítulo, com vida aérea contextual: pombo, urubu, passarinho, drone, avião e gaivota.
- **Personagem principal e NPCs:** catálogo de 10 identidades, cinco masculinas e cinco femininas, com representação baseada no humanoide Quaternius GLTF/skinned real. Corpo, rosto, olhos e cabelo usam o asset Universal Base Characters; roupa modular e mapas PBR vêm de meshes separados. Para Nina Creator, `runner_character.gd` mantém top, shorts jeans, botas, telefone, tatuagem, brincos, pulseiras, lantejoulas e metal em `BoneAttachment3D`, todos acompanhando o esqueleto. `world_character.gd` reutiliza o mesmo humanoide para velha e camelô, em vez de cabeças/cápsulas. `world_animal.gd` concentra o cachorro caramelo 3D com anatomia e animação de cauda/patas. A escala de 2,15 m, os pés no piso, a sombra de contato e os clips de locomoção são preservados, sem montar o corpo principal com cápsulas.
- **Tráfego:** carros, ônibus, motos e caminhões são assemblies 3D detalhados com cabine, vidros, faróis, lanternas, para-choques, placas, retrovisores, maçanetas, rodas orientadas e velocidade própria no eixo da rua. Os carros variam entre hatch compacto, sedã compacto e utilitário/van inspirados na frota popular brasileira, sem logotipos.
- **Preflight reproduzível:** `python3 tools/validate_project.py` passou após a migração.
- **Auditoria determinística de curva:** `python3 tools/audit_balance.py` confirma velocidades/distâncias monotônicas, metas de moedas alcançáveis e densidade de rua maior que calçada nas 50 fases.
- **Preflight auxiliar:** `python3 tools/validate_project.py` inclui referências, binários, texturas, clips, manifesto SHA-256 e o catálogo autoritativo da loja; a importação/renderização dos GLTF/GLB e a sintaxe final da nova camada `BoneAttachment3D` ainda precisam passar pelo editor Godot 4.x.
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

## Correção dos erros de abertura no Godot (18/09/2026)

Os erros reportados ao abrir o projeto no editor foram reproduzidos, corrigidos e
verificados com `tools/check_gdscript.py` (análise estática que replica as regras
de `gdscript_parser.cpp`/`gdscript_analyzer.cpp` do Godot 4.7.2, lidas do código
fonte da mesma versão):

- `scripts/game_3d.gd` — `_build_sidewalk_obstacle()` usava o material `chrome`
  (bicicleta e carrinho de camelô) sem declarar a variável: o script não
  compilava. Declaração adicionada.
- `scripts/game_3d.gd` — `var chapter` era redeclarado dentro de `if sun:` em
  `_apply_scenario_atmosphere()`; a variável externa já estava no escopo. A
  redeclaração foi removida.
- `scripts/save_data.gd` — `Time.get_unix_time_from_datetime_dict()` recebia dois
  argumentos (a API aceita apenas o dicionário). O número do dia local agora usa
  somente a data local com a hora zerada, para que a virada semanal coincida com
  a virada diária de `Time.get_date_string_from_system()`.
- Divisões inteiras (`INTEGER_DIVISION`) eliminadas em `game.gd`, `game_3d.gd`,
  `hud_3d.gd`, `phase_data.gd`, `runner_character.gd`, `save_data.gd` e
  `scenario_data.gd`, mantendo o truncamento exato do operador `/` do engine
  (`OperatorEvaluatorDivNZ<int64_t>`).
- Parâmetros não usados (`UNUSED_PARAMETER`) renomeados com o prefixo `_`, a
  convenção do Godot.

Resultado atual: `python3 tools/check_gdscript.py` → 0 problema(s),
`python3 tools/validate_project.py` → PRE-FLIGHT OK e
`python3 tools/audit_balance.py` → curva consistente.

## Correção do erro de sombra (`receive_shadow`) no Godot 4 (18/09/2026)

O erro reportado ao rodar o jogo — `Invalid assignment of property or key
'receive_shadow' with value of type 'bool' on a base object of type
'MeshInstance3D'` — era um resquício da API do Godot 3. A propriedade não existe
em nenhuma classe do Godot 4.7.2 (conferido nos XMLs oficiais de `doc/classes`):
por instância só existe `GeometryInstance3D.cast_shadow`, e quem controla o
recebimento de sombra é o material (`BaseMaterial3D.disable_receive_shadows`,
`false` por padrão).

- `scripts/runner_character.gd` — removidas as atribuições inválidas em
  `_split_regions()` (linha 204), no rebind de roupas de `_attach_outfit()`
  (284), em `_creator_mesh()` (492) e no laço de `_configure_mesh_shadows()`
  (622); todas ficavam logo depois de `cast_shadow = SHADOW_CASTING_SETTING_ON`.
- `scripts/world_animal.gd` — mesma remoção em `_mesh()` (linha 90).
- O resultado visual é o mesmo: no Godot 4 a malha recebe sombra por padrão
  (nenhum material do projeto usa `disable_receive_shadows`) e a projeção de
  sombra continua garantida por `cast_shadow`.
- `tools/check_gdscript.py` ganhou a checagem `UNKNOWN_MEMBER`: propriedades
  inexistentes em receptores de tipo conhecido passam a ser detectadas sem abrir
  o editor, com dica para nomes do Godot 3 (`receive_shadow` →
  `disable_receive_shadows`, `translation` → `position`, `lightmap_mode` →
  `gi_mode`, `set_as_toplevel` → `top_level`, ...). Para isso o analisador
  também passou a inferir o tipo de construtores (`var x := Classe.new()`), de
  casts (`x as T`) e de laços sobre `Array[T]` (`for mesh in _skinned_meshes(n)`),
  que é exatamente o caso do laço de sombras.

- Varredura complementar de API: todas as chamadas de engine/singleton usadas
  pelos scripts (`Input`, `Time`, `OS`, `DisplayServer`, `RenderingServer`,
  `Engine`, `ProjectSettings`, `ResourceLoader`, `AudioServer`, `FileAccess`,
  `DirAccess`, `JSON`, `SceneTree`, `RandomNumberGenerator`) foram conferidas
  contra os XMLs do Godot 4.7.2 — nenhuma função removida no Godot 4 continua no
  código, e não há `File.new()`, `Directory.new()`, `.instance()`,
  `change_scene()`, `interpolate_property()`, `yield()`, `set_as_toplevel()` nem
  conexões de sinal apontando para métodos inexistentes.
- Atribuições compostas (`mesh.receive_shadow += 1`) também entram na checagem.

Resultado atual: `python3 tools/check_gdscript.py` → 0 problema(s),
`python3 tools/validate_project.py` → PRE-FLIGHT OK e
`python3 tools/audit_balance.py` → mesma curva (piso R$ 5425, 2200 moedas,
metas 20=45 e 50=120). Os 14 scripts continuam com sintaxe válida no parser do
gdtoolkit. Contra o estado anterior do projeto (`git archive` do commit
`c6e7d8b`) o verificador acusa exatamente os 25 defeitos já corrigidos mais os
5 `receive_shadow`, sem nenhum falso positivo; um arquivo de teste com
`if mesh.receive_shadow:` é detectado pela checagem de leitura.

## Orientação, cadência e posição do corredor (18/09/2026)

Sintoma relatado: o boneco corria "para baixo", de frente para a câmera, com
movimentação estranha. A apuração foi feita direto nos assets (geometria e curvas
de animação) e no fluxo do jogo, e virou ferramenta reproduzível:
`python3 tools/audit_runner_rig.py`.

- **Sentido do modelo (causa do "correndo para baixo")**: no
  `Superhero_Male_FullBody.gltf` as sobrancelhas (z = +0,057..+0,094) e os olhos
  (+0,051..+0,081) ficam no lado **+Z**, as costas em -Z, e o vetor
  tornozelo→ponta do pé aponta para +Z nos dois pés. O corredor avança para -Z
  (o cenário desliza para +Z), então o personagem corria com o rosto voltado para
  a câmera. `model_root` agora recebe `rotation.y = PI` (`MODEL_FACING_YAW`).
- **Inclinação lateral preservada**: o balanço lateral passou para um pivô
  (`ModelPivot`) acima do modelo, e o giro de 180° ficou no próprio `model_root`.
  Separar os dois mantém o balanço exatamente igual ao de antes (mesma rotação em
  espaço de mundo) sem depender da ordem de Euler do Godot para o sinal.
- **Rig de animação**: o `UAL1_Standard.glb` usa o mesmo rig de 65 ossos do corpo
  (`root`, `pelvis`, `spine_01`, ...), então `Sprint_Loop`, `Jump_Loop` e os
  clips de deslize realmente animam o personagem. Já o `UAL1_Standard.res`
  comitado é de outro rig (Universal Humanoid: `%GeneralSkeleton`,
  `Hips`/`LeftUpperLeg`) e não mexe em osso nenhum deste corpo — por isso
  `_library_drives_skeleton()` confere se as trilhas apontam para ossos
  existentes antes de ligar `using_external_animation`; sem essa checagem o
  corredor congelaria na pose de repouso se a biblioteca errada fosse a
  escolhida.
- **Cadência (o "skate")**: medindo por cinemática direta, um ciclo do
  `Sprint_Loop` dura 0,667 s e desloca o pé ~1,35 m — o equivalente a ~4,0 m/s de
  solo. O jogo anda de 5 m/s (início) até 18 m/s (fim da campanha, 12 m/s no fim
  do capítulo 1, com dash ×1,22), então as pernas giravam muito devagar para o
  mundo. `AnimationPlayer.speed_scale` agora segue a velocidade real
  (`_match_playback_to_speed`, limitado a 2,2×) e `game_3d.gd` passa
  `motion_speed` para `set_motion()`.
- **Posição e contato com o chão**: o pé mais baixo do GLTF está em y = -0,01;
  com `MODEL_SCALE` 1,18 e `MODEL_FLOOR_OFFSET` 0,012 as solas ficam em
  y = +0,0008, sem flutuar nem afundar. Altura final 1,81 × 1,18 = 2,14 m,
  coerente com `PLAYER_HEIGHT` (2,15).

Resultado: `python3 tools/audit_runner_rig.py` → OK (rosto em +Z, 65/65 ossos
compatíveis, ciclo de 4,04 m/s batendo com a constante do script, sola em y≈0);
`python3 tools/check_gdscript.py` → 0 problema(s);
`python3 tools/validate_project.py` → PRE-FLIGHT OK;
`python3 tools/audit_balance.py` → curva inalterada.

## Limitações conhecidas / validação ainda obrigatória

- Não há binário Godot 4.x disponível no sandbox para executar `godot --headless --editor --quit --path .`; a checagem possível aqui é estática (`tools/check_gdscript.py`, que reproduz as classes de erro do analisador) e a confirmação final de importação GLTF/GLB, retarget da AnimationLibrary, renderização e warnings restantes precisa ser feita em uma máquina com Godot 4.x.
- Ainda é necessário fazer uma exportação APK debug, instalar em Android 8.0 ou superior e medir FPS, memória, aquecimento e consumo em um aparelho médio.
- O runner trata `NOTIFICATION_WM_GO_BACK_REQUEST`: primeiro Voltar pausa a corrida, o segundo encerra sem perda de save e Voltar no ponto embarca; ainda é necessário testar safe areas, notch, áudio interrompido por chamada/notificação e gestos em telas com diferentes densidades.
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
- [x] 50 fases, save schema v3, progressão, loja com preços autoritativos, personagens, desafios, áudio e feedback conectados.
- [x] Onboarding em etapas, pausa automática ao perder foco, movimento reduzido e alto contraste.
- [x] Cache de meshes primitivas, culling de decoração distante e HUD desacelerada para reduzir trabalho no Android.
- [ ] Parser/importação real no Godot 4.x.
- [ ] APK Android e teste em aparelho real.

## Próximos passos de produção

1. Rodar o editor Godot 4.7 em modo headless e abrir a cena principal; confirmar a importação dos GLTF/GLB Quaternius.
2. Verificar visualmente o Skeleton3D, o encaixe Body/Arms/Legs/Feet, os pés no piso, o sentido de corrida e os clips de sprint, jump e crouch; corrigir qualquer erro de parser, retarget, warning de API ou material.
3. Exportar APK debug, instalar em um Android 8.0+ e executar o checklist de gestos, pausa e safe area.
4. Medir 60 FPS em celular médio; reduzir sombras, segmentos de meshes ou partículas se necessário.
5. Exportar AAB assinado com keystore fora do repositório e validar em internal testing do Play Console.
6. Só então considerar a migração 3D pronta para publicação.
