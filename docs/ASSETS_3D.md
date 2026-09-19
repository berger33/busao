# Inventario de assets 3D — Corre pro Ponto

Auditoria completa dos assets do jogo (raiz + Lotes 2/3/4) em 2026-09-18.
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
| Obstaculo de calcad a e coletaveis | (sem drop-in ainda — ver roadmap) | montados em `game_3d.gd`. |

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

## 3. Carros e motos — ❌ todos procedurais (6 modelos)

| Asset | Estado | Detalhe |
|---|---|---|
| `car` (obstaculo de rua) | ❌ | `_build_brazilian_car`: 3 silhuetas (hatch, sedan, utilitario/van) de caixas |
| `motorcycle` (motos) | ❌ | moto de entregas em caixas/esferas (o motoqueiro e 3D skinned) |
| `truck` (caminhao) | ❌ | cabine + carga em caixas |
| `bus_traffic` (onibus de transito) | ❌ | caixas + vidro + rodas |
| `onibus` (o amarelo do ponto) | ❌ | `BusBody`/`BusRoofAC` etc. |
| `carro` (parqueado na calcad a) | ❌ | reusa `_build_brazilian_car` |
| `bicycle` (calcad a) | ❌ | quadro em tubos + rodas torus |

Todos tem drop-in GLB pronto (`assets/vehicles/*.glb`, `GLB_FIT` em `game_3d.gd`).

## 4. Objetos / mobiliario de calcada — ❌ todos procedurais (6)

| Asset | Estado |
|---|---|
| `hydrant` (hidrante) | ❌ cilindros + esfera |
| `payphone` (orelhao) | ❌ caixas |
| `cone` (cone de obra) | ❌ cone + cilindros |
| `bench` (banco de praca) | ❌ caixas de madeira/metal |
| carrinho do `vendor` (camelô) | ❌ caixas + rodas (o vendedor e 3D skinned) |
| ponto de ônibus (`bus_stop`: toldo, vidro, banco, placa) | ❌ caixas |

Sem drop-in no codigo hoje — o lote 7 adicione o caminho GLB.

## 5. Coletaveis — ❌ todos procedurais (11)

`coin` (R$ 0,25), `golden` (bilhete dourado), `coffee` (cafe), `bread`
(pao de queijo), `pastel`, `sugarcane` (caldo de cana), `pass`
(vale-transporte), `coxinha`, `guarana`, `pix` (celular), `umbrella`
(guarda-chuva) — todos montados com primitivas em `_build_collectible`
+ esferas de glow. Sem drop-in hoje — o lote 8 adicione o caminho GLB.

## 6. CeU (sky fx) — ❌ 2 procedurais

| Asset | Estado |
|---|---|
| `aviao` | ❌ caixas (corpo, asa, cauda) |
| `drone` | ❌ caixas + cilindro de rotor |

## 7. Estruturas / cenario (Lote 1 do jogo, `game_3d.gd`) — ❌ todos procedurais

Casas (favela/residencial/colonial), predios de perfil, lojinhas, obras
com andaimento, guarita, igreja, quiosque, fachada de terminal, barraca de
mercado, palmeiras, arvores, caixas d'agua, varais, portoes, bandeiras,
placas de publicidade, postes de luz, buraco na rua (`pothole`), tampas de
bueiro — caixas/esferas/cilindros com texturas PBR geradas por codigo.

## 8. Rua do Lote 3 (`building_kit.gd` + `world_spec.json`) — primitivas

Piso, guias, lajes (MultiMesh), mosaicos, predios com janelas (MultiMesh),
lojas com toldo, arvores, bancos, lixeiras, hidrante e horizonte — tudo
primitivo, deterministico por semente. **Faltam as texturas PBR**:
`assets/textures/pbr/` (albedo/normal/orm de calcada_laje, calcada_mosaico,
asfalto, tijolo, reboco, laje_cobertura, metal_pintado, metal_zincado,
madeira, terra_vermelha) nao existe — o kit cai em cor plana com warning.
(Trilha de texturas, nao de objetos 3D.)

---

## Plano de lotes (execucao por Blender headless)

| Lote | Assets | Drop-in necessario no GDScript |
|---|---|---|
| **1** ✅ | `pombo.glb` | ja existia |
| **2** ✅ | Aves: `passaro`, `gaivota`, `urubu` (com clips Walk + Fly) | ✅ feito: tamanhos em `BIRD_PROFILES` (`_fit_glb` escala/assenta automaticamente) + `_animar_glb` agora toca o clip `fly` quando `behavior_mode == "flight"` (o pombo nao tem clip fly e segue no Walk) |
| **3** ✅ | Quadrupedes: `capivara`, `cavalo`, `boi` (clips Walk + Idle + Lie/Graze) | ✅ feito: `GLB_SIZES` + `_sincronizar_clip_glb` toca `Lie`/`Graze` no crouch |
| **4** ✅ | `macaco`, `caranguejo` | ✅ ja coberto pelo drop-in generico do lote 3 (sem novo codigo) |
| **5** | Veiculos: `car`, `motorcycle`, `truck`, `bus_traffic`, `onibus`, `carro` | ja existe (`_optional_model`) |
| **6** | (reserva — variantes de carro/cor) | — |
| **7** | Mobiliario: `hidrante`, `orelhao`, `cone`, `banco`, `caminho_camelô`, `ponto` | novo drop-in em `_build_sidewalk_obstacle` |
| **8** | Coletaveis (11) + `aviao` + `drone` | novo drop-in em `_build_collectible`/`_build_aerial` |
| **9** | Estruturas de cenario (casas, predios, igreja, quiosque, poste, palmeira…) | novo drop-in opcional em `_build_scenario_slice` |
| **10** | Texturas PBR do Lote 3 (`assets/textures/pbr/`) | sem codigo — o kit ja procura |

Toda GLB original do projeto eh CC0 (trabalho original, sem obrigacao de
credito); `CREDITS.md` so muda se entrar asset de terceiro.
