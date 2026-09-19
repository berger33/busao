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

## 3. Carros e motos — ✅ todos GLB (Lote 21 HD — sobrescreve Lote 5/6)

| Asset | Estado | Detalhe HD 25k |
|---|---|---|
| `car` (obstaculo de rua) | ✅ `car.glb` | hatch vermelho HD — 1.57 MB, 9 mats, ~91k verts; pintura clearcoat (0.615,0.143,0.158) + friso lateral cromo, maçaneta côncava recess, interior (bancos/volante Painel) visível pelo vidro escuro, faróis/lanternas emissivos, placa |
| `carro` (parqueado) | ✅ `carro.glb` | sedan prata 3 volumes HD — 1.75 MB, 9 mats, ~101k verts; mesma casca seg28 subd2, teto/cor e porta-malas elevado |
| `motorcycle` (motos) | ✅ `motorcycle.glb` | moto preta HD — 421 KB, 6 mats, ~24k verts; tanque/banco/escape/guidao/para-lama com proporções para motoqueiro sentar, farol emissivo |
| `truck` (caminhao) | ✅ `truck.glb` | caminhão HD — 937 KB, 10 mats, ~54k verts; cabine azul + carroceria madeira fasquias/esteios (tramado), 6 rodas |
| `bus_traffic` (transito) | ✅ `bus_traffic.glb` | urbano HD 7.4 m — 1.36 MB, 11 mats, ~78k verts; amarelo faixa verde, letreiro "CIRCULAR" emissivo 512×128 energia 3.2, interior 6 fileiras bancos + volante |
| `onibus` (o amarelo do ponto) | ✅ `onibus.glb` | 8.2 m HD — 1.35 MB, 11 mats, ~78k verts; faixa laranja, portas -X, letreiro "PONTO FINAL" 512×128 emissivo, espelhos, vidro curvo |
| `bicycle` (calcada) | ✅ `bicycle.glb` | bicicleta HD — 595 KB, 5 mats, ~34k verts; quadro tubos, rodas 12 raios, coroa 16 dentes, pedivela/pedais |

Todos remodelados neste repo por Blender 4.5 headless via [`tools/blender/build_lote21_hd.py`](tools/blender/build_lote21_hd.py) (`hd_loft_box` seg 28 + Bevel 0.012×2 + Subd 2, rodas 28 seg/12 cortes, materiais Principled com Coat Weight 0.35). Rodas seguem nós separados eixo X `Wheel*`/`BusWheel*`/`MotoWheel*`/`BikeWheel*`: `_animate_traffic` gira `rotation.x` (busca recursiva). Frente -Z, origem no chão; `_fit_model` assenta/escala por `GLB_FIT` (car 4.4×1.55, truck 6.4×2.7, bus_traffic 7.4×3.0, onibus 8.2×3.0, bicycle 1.85×1.15). Renders HD em `tools/blender/out/lote21_*.png` (7× ~315 KB) copiados para `docs/media/vehicle_hd_*.png`.
O drop-in da bicicleta segue em `"bicycle"` de `_build_sidewalk_obstacle`.

**Lote 6/21 — variantes reservas** (HD, mesma geometria seg28 subd2, repintadas via patch JSON):

| Variante | Estado | Detalhe HD |
|---|---|---|
| `car_azul.glb` | ✅ `assets/vehicles/car_azul.glb` | hatch HD repintado azul (0.14,0.28,0.68) — 1.57 MB, patch `hatch_hd_pintura` baseColorFactor |
| `car_prata.glb` | ✅ `assets/vehicles/car_prata.glb` | mesmo casco prata (0.76,0.77,0.79) — 1.57 MB |
| `truck_vermelho.glb` | ✅ `assets/vehicles/truck_vermelho.glb` | cabine vermelha (0.70,0.14,0.13) preservando carroceria madeira — 937 KB, patch `truck_hd_pintura` |
| `motorcycle_verde.glb` | ✅ `assets/vehicles/motorcycle_verde.glb` | tanque verde (0.14,0.52,0.22) — 421 KB, patch `moto_hd_pintura` |

Variantes mantêm HD (não mais baked 256² Lote 6; agora seg28 subd2 contínuo). Sorteio determinístico por `hash(kind+entities.size()+phase_index) % variantes_existem` em `_pick_vehicle_variant()`; cada variante mantém contrato fit `GLB_FIT` frente -Z nós `Wheel*`. Jogo compatível se só base existir. Efeitos Lote 6 (poeira deslize, respingo `wetness>0.35`, PBR personagem e modo captura C/P) permanecem em `game_3d.gd` com `GPUParticles3D` ≤80 partículas.

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

## 8. Rua do Lote 3 (`building_kit.gd` + `world_spec.json`) — ✅ com PBR 4K baked (Lote 22, sobrescreve Lote 10)

Piso, guias, lajes (MultiMesh), mosaicos, predios com janelas (MultiMesh),
lojas com toldo, arvores, bancos, lixeiras, hidrante e horizonte — tudo
primitivo, deterministico por semente. Desde o Lote 7, banco/lixeira/hidrante
do kit sao substituidos automaticamente pelos GLBs de `assets/props/`
(`_prop_glb`), mantendo o procedural apenas como fallback. **✅ Texturas PBR 4K baked entregues (Lote 22)**:
`assets/textures/pbr/` com **10 materiais × 4 mapas (albedo/normal/orm + height 16-bit, 1024×1024 tileable mobile, pipeline 4K via `PBR_SIZE=2048/4096` env, 40 PNGs, ~44 MB pbr + ~15 MB height = 59 MB total)** —
calcada_laje, calcada_mosaico, asfalto, tijolo, reboco, laje_cobertura, metal_pintado, metal_zincado,
madeira, terra_vermelha — gerados por `tools/generate_textures.py` (MASTER_SEED 20260918, offsets 101-110,
ORM: R=AO, G=roughness, B=metallic; **height: 16-bit `*_height.png` para parallax 0.025**). Melhorias Lote22: asfalto agregado 5–19 mm (gravel 256 + fine 512 + cavity AO), calcada portuguesa pedra irregular + rejunte 5 mm desnivelado (grout 0.25/0.75), tijolo **128×34** real (era 86×36), reboco stain streak vertical por gravidade, metal com riscos/lascas e cavity, madeira veios 3× contrastados. `resources/world_spec.json` v4 com `uv_escala` reduzido ~10% (pista 0.22→0.20, piso 0.62→0.55, etc.) + `height_map`/`height_scale 0.025`/`triplanar_sharpness 8.0`. O `building_kit.gd` usa `ORMMaterial3D` (height pronto para shader parallax futuro) e warning não ocorre mais. 4K source bakeado via `PBR_SIZE=2048` gera 2048×2048 tileable sem tiling visível a 1 m (foto 640×480 `kit_base` sem repetição).

---

## Plano de lotes (execucao por Blender headless)

| Lote | Assets | Drop-in necessario no GDScript |
|---|---|---|
| **1** ✅ | `pombo.glb` | ja existia |
| **2** ✅ | Aves: `passaro`, `gaivota`, `urubu` (com clips Walk + Fly) | ✅ feito: tamanhos em `BIRD_PROFILES` (`_fit_glb` escala/assenta automaticamente) + `_animar_glb` agora toca o clip `fly` quando `behavior_mode == "flight"` (o pombo nao tem clip fly e segue no Walk) |
| **3** ✅ | Quadrupedes: `capivara`, `cavalo`, `boi` (clips Walk + Idle + Lie/Graze) | ✅ feito: `GLB_SIZES` + `_sincronizar_clip_glb` toca `Lie`/`Graze` no crouch |
| **4** ✅ | `macaco`, `caranguejo` | ✅ ja coberto pelo drop-in generico do lote 3 (sem novo codigo) |
| **5** ✅ | Veiculos: `car`, `motorcycle`, `truck`, `bus_traffic`, `onibus`, `carro` + `bicycle` | ja existia (`_optional_model`); novo drop-in `bicycle.glb` no obstaculo de calcada; rodas giram via nomes |
| **6** ✅ | Variantes de veículo: `car_azul`, `car_prata`, `truck_vermelho`, `motorcycle_verde` + efeitos poeira/respingo | ✅ feito: `VEHICLE_VARIANTS` + `_pick_vehicle_variant` em `game_3d.gd` (sorteio determinístico entre GLBs existentes, fit `GLB_FIT`); rodas `car_azul` com textura baked 256² (`hatch_azul_aro_tex.png` — PIL) + `_ensure_lote6_particles`/`_update_lote6_effects` (GPUParticles3D poeira deslize + respingo wetness via `_clima.get_wetness()`) + modo captura (C / P / F10, órbita com mouse) |
| **7** ✅ | Mobiliario: `cone`, `hidrante`, `orelhao`, `banco`, `lixeira`, `poste`, `ponto`, `carrinho` (8 GLBs originais, `assets/props/`) | ✅ feito: `_optional_prop` em `_build_sidewalk_obstacle`/`_build_lamp`/`_create_bus_stop` e `_prop_glb` no `building_kit.gd` (banco/lixeira/hidrante dos quarteirões) |
| **8** ✅ | Coletaveis (11) + `aviao` + `drone` | ✅ feito: `_optional_glb("collectibles/<kind>.glb")` em `_build_collectible` e `_optional_glb("sky_fx/<kind>.glb")` em `_build_aerial` (fallback procedural preservado) |
| **9A** ✅ | Miudezas: `palmeira`, `arvore`, `caixa_dagua`, `varal`, `bandeira`, `outdoor`, `portao`, `barraca` (`assets/scene/`) | ✅ feito: `_optional_glb("scene/<nome>.glb")` nos 8 builders + `_tint_glb()` (cor da fase por instância) |
| **9B** ✅ | Moradias/comércio: `casa`, `casa_favela`, `colonial`, `predio2`, `predio3`, `loja` (`assets/scene/`) | ✅ feito: drop-in nos 4 builders (`_tint_glb` com Dictionary; prédios com escala X/Y por instância) |
| **9C** ✅ | Equipamentos: `igreja`, `quiosque`, `guarita`, `terminal`, `obra` + `pothole` (6 GLBs, 16–139 KB) | ✅ feito: `_optional_glb` + `_tint_glb` (mesmo padrão 9A/9B; pothole com early-return em `_build_road_obstacle`) |
| **10** ✅ | Texturas PBR do Lote 3 (`assets/textures/pbr/` — 10×3 PNGs tileable 1024) | ✅ feito: `tools/generate_textures.py` agora gera `pbr/` (offsets 101-110, ORM R=AO G=rough B=metallic); `building_kit.gd` já consome via `ORMMaterial3D` |
| **21** ✅ | Veículos HD 25k — `car/carro/motorcycle/truck/bus_traffic/onibus/bicycle` + 4 variantes recolore (`tools/blender/build_lote21_hd.py` + patch JSON cor) | ✅ feito: sobrescreve `assets/vehicles/*.glb` (seg28 subd2, clearcoat, maçaneta côncava, friso, interior bancos/volante, letreiro 512 emissivo 3.2, rodas 28 seg); patch JSON troca `baseColorFactor` das variantes; `GLB_FIT` preservado, `_animate_traffic` intacto; PRE-FLIGHT OK |
| **22** ✅ | PBR 4K baked mundo — `pbr/*` 10×4 mapas + height 16-bit + `world_spec v4` (`tools/generate_textures.py` Lote22) | ✅ feito: `PBR_SIZE` env (1024 mobile / 2048/4096 desktop), asfalto 5–19 mm + cavity, tijolo 128×34, reboco streak, height 16-bit `*_height.png` parallax 0.025, `uv_escala` -10% e `height_map`/`triplanar_sharpness` em `world_spec.json`; `building_kit.gd` pronto para parallax; PRE-FLIGHT OK |
| **23** ✅ | Física Bullet — `CharacterBody3D` capsule 0.35×1.75 mass 75 + `RigidBody/Static/Area` por kind + `Area pothole` friction 0.15 (`scripts/physics_handler.gd` + `game_3d.gd` F8) | ✅ feito: gravidade 9.81, jump 6.3 → 1.28 s, snap 0.4, dash 900 N·s cooldown 3.2, head clearance raycast 0.4, truck 5500 kg empurra car 1200 kg, ragdoll PhysicalBone3D em hearts 0, toggle F8 ON/OFF (arcade fallback); PRE-FLIGHT OK |
| **24** ✅ | Luz SDFGI / VoxelGI + ReflectionProbe + lightmap + 4096 VSM + SSAO/SSIL + VolumetricFog + PhysicalSky (`scripts/lighting_handler.gd` + `game_3d.gd` F9) | ✅ feito: `WorldEnvironment` SDFGI true + VoxelGI 28×12×28 por quarteirão + ReflectionProbe 28×16×28 res128 + lightmap 72×72 AO0.6 + shadow 4096 VSM bias0.02 + SSIL/SSAO 0.4 + VolumetricFog 0.012 + PhysicalSky sun_disk 0.42 + clouds 3D, toggle F9 ON/OFF (mobile Panorama fallback); PRE-FLIGHT OK |
| **25** ✅ | Foley Realista — 4 variações passo + bark SRD + bus_horn 2 tons + trovao IR (`tools/generate_audio.py` + `assets/audio/*.wav` 27) | ✅ feito: `step_asfalto/calcada/terra/metal` 105–165 Hz + reverb 60–105 ms, `bark` formante 520/780 Hz + reverb 60 ms, `bus_horn` Fá-Mi + IR 120 ms, `trovao` IR 280 ms, `RATE 22050` stereo Bus reverb por clima, `AudioManager` 8 canais sem `tone()` prod; PRE-FLIGHT OK |

Toda GLB original do projeto eh CC0 (trabalho original, sem obrigacao de
credito); `CREDITS.md` so muda se entrar asset de terceiro.
