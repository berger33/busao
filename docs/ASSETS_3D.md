# Inventario de assets 3D — Corre pro Ponto

Auditoria completa dos assets do jogo (raiz + Lotes 2/3/4 + 9A/9B/9C/10) em 2026-09-19.
Convencao: **"3D completo"** = mesh modelada (GLB/skinned) com materiais e,
quando animado, clips de animacao. **"Procedural"** = montado em codigo com
primitivas Godot (box/sphere/cylinder/torus) em `scripts/game_3d.gd`,
`scripts/world_animal.gd` e `scripts/building_kit.gd`.

## Contrato de drop-in (o que o jogo aceita)

| Categoria | Caminho | Regra |
|---|---|---|
| Animal | `assets/characters/animais/<especie>.glb` | frente +Z, origem no chao, clip com "walk"/"trot" no nome (o jogo escolhe); escala/assentamento automaticos. Aves aceitam clip "fly" para o ciclo aereo. |
| Veiculo (rua) | `assets/vehicles/car.glb`, `motorcycle.glb`, `truck.glb`, `bus_traffic.glb` | comprimento no eixo Z, virado para -Z; tamanho-alvo definido em `GLB_FIT`. |
| Veiculo (ponto/parqueado) | `assets/vehicles/onibus.glb`, `carro.glb` | idem. |
| Bicicleta (calcada) | `assets/vehicles/bicycle.glb` | idem (fit 1,85 x 1,15 no obstaculo `bicycle`). |
| Mobiliario urbano | `assets/props/<nome>.glb` (cone, hidrante, orelhao, banco, lixeira, poste, ponto, carrinho) | escala real 1:1, origem no chao, frente -Z; `_optional_prop` (game_3d) e `_prop_glb` (kit). |

---

## 1. Personagens — ✅ ja estao 3D completos

| Asset | Origem | Estado |
|---|---|---|
| Corredor (20 perfis da loja) | Quaternius Universal Base Characters (CC0) + roupa Peasant skinned + acessorios `BoneAttachment3D` | ✅ skinned, PBR, clips UAL (Sprint/Jump/Crouch) |
| Pedestre `old_lady` (Zilda/Maria) | idem, via `world_character.gd` | ✅ |
| Pedestre `vendor` (Marta/Zé) | idem | ✅ |
| Motoqueiro (na moto) | idem, clip `Driving_Loop` | ✅ |

Nada a criar nesta categoria.

## 2. Animais — ✅ 10 / ❌ 0 (categoria completa)

| Especie | Estado | Detalhe |
|---|---|---|
| `pombo` | ✅ `pombo.glb` | modelado neste repo por Blender headless (lote 1); rig de 13 ossos; clips Walk+Idle; validado (14 materiais, 33k verts) |
| `caramelo` (o cachorro) | ✅ `caramelo.glb` | raposa Khronos CC0 (glTF-Sample-Assets), rigada, Survey/Walk/Run |
| `passaro` | ✅ `passaro.glb` | tico-tico modelado neste repo (lote 2); rig de 12 ossos; clips Walk (14f) + Fly; resting/Walk assentado no chao |
| `gaivota` | ✅ `gaivota.glb` | gaivota de praia modelada neste repo (lote 2); rig de 12 ossos; clips Walk (16f) + Fly; resting/Walk assentado no chao |
| `urubu` | ✅ `urubu.glb` | urubu-de-crista modelado neste repo (lote 2); rig de 12 ossos; clips Walk (22f) + Fly; resting/Walk assentado no chao |
| `capivara` | ✅ `capivara.glb` | modelada neste repo (lote 3); rig de 16 ossos; clips Walk + Idle + Lie (deitada no crouch) |
| `cavalo` | ✅ `cavalo.glb` | modelado neste repo (lote 3); rig de 16 ossos; clips Walk + Idle + Graze (pastando no crouch) |
| `boi` | ✅ `boi.glb` | modelado neste repo (lote 3); rig de 16 ossos; clips Walk + Idle + Graze |
| `macaco` | ✅ `macaco.glb` | modelado neste repo (lote 4); rig de 9 ossos; clips Walk + Idle + Lie (agachado com cauda enrolada) |
| `caranguejo` | ✅ `caranguejo.glb` | modelado neste repo (lote 4); rig de 9 ossos; clips Walk (garra de tesoura) + Idle (pinça saudação) + Lie (abaixado) |

Nota: o drop-in GLB cobre as 10 especies (pombo, aves do lote 2,
quadrupedes do lote 3 e macaco/caranguejo do lote 4) — `_build_animal_glb`
no `_ready`, tamanhos em `GLB_SIZES`, troca de clip por pose em
`_sincronizar_clip_glb` (crouch usa `Graze`/`Lie`). O caramelo (obstaculo
`dog`) ja era GLB desde o lote 0.

## 3. Carros e motos — ✅ todos GLB (Lote 5)

| Asset | Estado | Detalhe |
|---|---|---|
| `car` (obstaculo de rua) | ✅ `car.glb` | hatch vermelho (Gol/Onix), cabine de vidro + teto na cor, farois/lanternas emissivos, placa |
| `carro` (parqueado) | ✅ `carro.glb` | sedan prata 3 volumes (porta-malas elevado) |
| `motorcycle` (motos) | ✅ `motorcycle.glb` | tanque/banco/escape/guidao/para-lama; proporcoes iguais as da procedural para o motoqueiro sentar certo |
| `truck` (caminhao) | ✅ `truck.glb` | cabine avancada + carroceria de madeira (fasquias e esteios), bem brasileiro |
| `bus_traffic` (transito) | ✅ `bus_traffic.glb` | urbano amarelo com faixa verde, letreiro "CIRCULAR" |
| `onibus` (o amarelo do ponto) | ✅ `onibus.glb` | 8,2 m, faixa vermelha, portas no lado -X e letreiro LED emissivo "PONTO FINAL" (textura gerada por PIL no proprio build) |
| `bicycle` (calcada) | ✅ `bicycle.glb` | quadro de tubos, 12 raios por roda, coroa, pedivela e pedais |

Todos modelados neste repo por Blender headless (`tools/blender/build_lote5.py`,
`loft_box` = casco super-elipse + subd 1). Rodas sao nos separados com eixo
no X e nomes `Wheel*`/`BusWheel*`/`MotoWheel*`: `_animate_traffic` gira
`rotation.x` delas (busca recursiva — pega rodas aninhadas nos GLBs).
Frente -Z, origem no chao; `_fit_model` assenta/escala por `GLB_FIT`.
O drop-in da bicicleta foi adicionado ao `"bicycle"` de
`_build_sidewalk_obstacle` (fit 1,85 x 1,15).

## 4. Objetos / mobiliario de calcada — ✅ todos GLB (Lote 7)

| Asset | Estado | Detalhe |
|---|---|---|
| `hydrant` (hidrante) | ✅ `hidrante.glb` | corpo vermelho com domo, bicos laterais e volante de latão |
| `payphone` (orelhao) | ✅ `orelhao.glb` | capuz laranja com abertura real, teclado/moedeiro/fone dentro |
| `cone` (cone de obra) | ✅ `cone.glb` | base quadrada + 2 faixas refletivas |
| `bench` (banco de praca) | ✅ `banco.glb` | ripas de madeira + pés/travessas de aço |
| carrinho do `vendor` (camelô) | ✅ `carrinho.glb` | corpo/tampo de madeira, vitrine, toldo listrado (o vendedor e 3D skinned) |
| ponto de ônibus (`bus_stop`) | ✅ `ponto.glb` | abrigo: colunas, teto com testa amarela, vidros, banco laranja |
| lixeira de rua | ✅ `lixeira.glb` | tambor verde suspenso em poste, placa de reciclagem |
| poste de luz | ✅ `poste.glb` | haste afilada + braço curvo + lente emissiva quente |

Modelados neste repo por Blender headless (`tools/blender/build_lote7.py`),
escala real 1:1, origem no chao, frente -Z. Drop-in via `_optional_prop`
(`_build_sidewalk_obstacle`, `_build_lamp`, `_create_bus_stop`) e `_prop_glb`
no `building_kit.gd` (banco/lixeira/hidrante dos quarteirões). A placa
`StopSign` segue procedural de propósito (recebe skin/cor do GameSave).

## 5. Coletaveis — ✅ todos GLB (Lote 8)

| Asset | Estado | Detalhe |
|---|---|---|
| `coin` | ✅ `coin.glb` | Moeda de R$ 0,25 em pe, face "R$ 0,25" e verso "BRASIL 2026" (texturas PIL no build) |
| `golden` | ✅ `golden.glb` | Bilhete dourado "PREMIADO" com estrela emissiva |
| `coffee` | ✅ `coffee.glb` | Copo com tampa e faixa kraft |
| `bread` | ✅ `bread.glb` | Pao de queijo com manchas de forno |
| `pastel` | ✅ `pastel.glb` | Pastel com borda crimpada (gominhos) |
| `sugarcane` | ✅ `sugarcane.glb` | Tres talos com nos + folhas no topo |
| `pass` | ✅ `pass.glb` | Vale-transporte "BUSÃO" com tarja |
| `coxinha` | ✅ `coxinha.glb` | Gota empanada com bico |
| `guarana` | ✅ `guarana.glb` | Garrafa verde com rotulo |
| `pix` | ✅ `pix.glb` | Celular "PIX TURBO" com tela emissiva |
| `umbrella` | ✅ `umbrella.glb` | Guarda-chuva azul fechado |

Todos modelados neste repo por Blender headless (`tools/blender/build_lote8.py`),
**centrados na origem** (o node pai gira em Y) e com frente -Y no Blender.
Drop-in em `_build_collectible` via `_optional_glb("collectibles/<kind>.glb")`;
o glow translucido continua nos dois caminhos. Fallback procedural preservado.

## 6. CeU (sky fx) — ✅ GLB (Lote 8)

| Asset | Estado | Detalhe |
|---|---|---|
| `aviao` | ✅ `aviao.glb` | Fuselagem loftera, asa baixa, deriva azul e motores |
| `drone` | ✅ `drone.glb` | Quadricoptero com 4 rotores, gimbal e trens |

Centrados na origem (o jogo gira o node em Y) e escala 1:1. Drop-in em
`_build_aerial` via `_optional_glb("sky_fx/<kind>.glb")`. As aves seguem no
`Animal3D` articulado.

## 7. Estruturas / cenario (Lote 1 do jogo, `game_3d.gd`) — ✅ GLB completo (9A/9B/9C)

| Builder | GLB (`assets/scene/`) | Estado |
|---|---|---|
| `_build_palm` | `palmeira.glb` | ✅ Lote 9A (tronco + 6 folhas + cocos) |
| `_build_tree` | `arvore.glb` | ✅ Lote 9A (tronco + galhos + 4 copas) |
| `_build_water_tank` | `caixa_dagua.glb` | ✅ Lote 9A (cavalete + bojo + tampa cônica) |
| `_build_clothesline` | `varal.glb` | ✅ Lote 9A (mastros + corda + roupas) |
| `_build_flag` | `bandeira.glb` | ✅ Lote 9A (pano `TintFabric`) |
| `_build_billboard` | `outdoor.glb` | ✅ Lote 9A (painel `TintPaint`) |
| `_build_gate` | `portao.glb` | ✅ Lote 9A (`TintMetal`) |
| `_build_market_stall` | `barraca.glb` | ✅ Lote 9A (lona `TintFabric`) |
| `_build_house_facade` | `casa.glb` / `casa_favela.glb` | ✅ Lote 9B (`TintWall`/`TintRoof`/`TintAwning`) |
| `_build_colonial_facade` | `colonial.glb` | ✅ Lote 9B (+ `TintTrim`, esquadrias azuis) |
| `_build_profile_building` | `predio2.glb` / `predio3.glb` | ✅ Lote 9B (escala X/Y por instância, `TintTrim`) |
| `_build_shopfront` | `loja.glb` | ✅ Lote 9B (placa `TintSign` MERCEARIA) |
| `_build_church` | `igreja.glb` | ✅ Lote 9C (nave + torre sineira + cruz + frontão, 682v, TintWall/Roof/Trim) |
| `_build_tourist_kiosk` | `quiosque.glb` | ✅ Lote 9C (octógono + ripas + toldo, 800v, TintWall/Trim) |
| `_build_guard_post` | `guarita.glb` | ✅ Lote 9C (abrigos + balcão + cortina, 464v, TintWall/Trim/Fabric) |
| `_build_terminal_facade` | `terminal.glb` | ✅ Lote 9C (fachada + vidro + placa TERMINAL 512×128, 744v, TintWall/Trim/Sign) |
| `_build_construction` | `obra.glb` | ✅ Lote 9C (tapume + andaime 3 níveis + rede + cata-vento, 632v) |
| `pothole` (obstáculo de rua) | `pothole.glb` | ✅ Lote 9C (cratera irregular + 7 fragmentos, 124v) |
| `_build_manhole` / `_build_asphalt_patch` | — | ➖ só usados em `_build_track_antigo` (morto desde o Lote 3) |

Drop-ins via `_optional_glb("scene/<nome>.glb")` + `_tint_glb()` (cor da
fase por instância); fallback procedural preservado em todos.

## 8. Rua do Lote 3 (`building_kit.gd` + `world_spec.json`) — ✅ com PBR (Lote 10)

Piso, guias, lajes (MultiMesh), mosaicos, predios com janelas (MultiMesh),
lojas com toldo, arvores, bancos, lixeiras, hidrante e horizonte — tudo
primitivo, deterministico por semente. Desde o Lote 7, banco/lixeira/hidrante
do kit sao substituidos automaticamente pelos GLBs de `assets/props/`
(`_prop_glb`), mantendo o procedural apenas como fallback. **✅ Texturas PBR entregues (Lote 10)**:
`assets/textures/pbr/` com 10 materiais × 3 mapas (albedo/normal/orm, 1024×1024 tileable, 30 PNGs, ~41 MB) —
calcada_laje, calcada_mosaico, asfalto, tijolo, reboco, laje_cobertura, metal_pintado, metal_zincado,
madeira, terra_vermelha — gerados por `tools/generate_textures.py` (MASTER_SEED 20260918, offsets 101-110,
ORM: R=AO, G=roughness, B=metallic). O `building_kit.gd` já usa `ORMMaterial3D` e o warning de
textura ausente não ocorre mais.

---

## Plano de lotes (execucao por Blender headless)

| Lote | Assets | Drop-in necessario no GDScript |
|---|---|---|
| **1** ✅ | `pombo.glb` | ja existia |
| **2** ✅ | Aves: `passaro`, `gaivota`, `urubu` (com clips Walk + Fly) | ✅ feito: tamanhos em `BIRD_PROFILES` (`_fit_glb` escala/assenta automaticamente) + `_animar_glb` agora toca o clip `fly` quando `behavior_mode == "flight"` (o pombo nao tem clip fly e segue no Walk) |
| **3** ✅ | Quadrupedes: `capivara`, `cavalo`, `boi` (clips Walk + Idle + Lie/Graze) | ✅ feito: `GLB_SIZES` + `_sincronizar_clip_glb` toca `Lie`/`Graze` no crouch |
| **4** ✅ | `macaco`, `caranguejo` | ✅ ja coberto pelo drop-in generico do lote 3 (sem novo codigo) |
| **5** ✅ | Veiculos: `car`, `motorcycle`, `truck`, `bus_traffic`, `onibus`, `carro` + `bicycle` | ja existia (`_optional_model`); novo drop-in `bicycle.glb` no obstaculo de calcada; rodas giram via nomes |
| **6** | (reserva — variantes de carro/cor/rodas com texturas baked) | — |
| **7** ✅ | Mobiliario: `cone`, `hidrante`, `orelhao`, `banco`, `lixeira`, `poste`, `ponto`, `carrinho` (8 GLBs originais, `assets/props/`) | ✅ feito: `_optional_prop` em `_build_sidewalk_obstacle`/`_build_lamp`/`_create_bus_stop` e `_prop_glb` no `building_kit.gd` (banco/lixeira/hidrante dos quarteirões) |
| **8** ✅ | Coletaveis (11) + `aviao` + `drone` | ✅ feito: `_optional_glb("collectibles/<kind>.glb")` em `_build_collectible` e `_optional_glb("sky_fx/<kind>.glb")` em `_build_aerial` (fallback procedural preservado) |
| **9A** ✅ | Miudezas: `palmeira`, `arvore`, `caixa_dagua`, `varal`, `bandeira`, `outdoor`, `portao`, `barraca` (`assets/scene/`) | ✅ feito: `_optional_glb("scene/<nome>.glb")` nos 8 builders + `_tint_glb()` (cor da fase por instância) |
| **9B** ✅ | Moradias/comércio: `casa`, `casa_favela`, `colonial`, `predio2`, `predio3`, `loja` (`assets/scene/`) | ✅ feito: drop-in nos 4 builders (`_tint_glb` com Dictionary; prédios com escala X/Y por instância) |
| **9C** ✅ | Equipamentos: `igreja`, `quiosque`, `guarita`, `terminal`, `obra` + `pothole` (6 GLBs, 16–139 KB) | ✅ feito: `_optional_glb` + `_tint_glb` (mesmo padrão 9A/9B; pothole com early-return em `_build_road_obstacle`) |
| **10** ✅ | Texturas PBR do Lote 3 (`assets/textures/pbr/` — 10×3 PNGs tileable 1024) | ✅ feito: `tools/generate_textures.py` agora gera `pbr/` (offsets 101-110, ORM R=AO G=rough B=metallic); `building_kit.gd` já consome via `ORMMaterial3D` |

Toda GLB original do projeto eh CC0 (trabalho original, sem obrigacao de
credito); `CREDITS.md` so muda se entrar asset de terceiro.
