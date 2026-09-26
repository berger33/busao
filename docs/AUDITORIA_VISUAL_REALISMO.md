# Auditoria Visual Completa — Corre pro Ponto 3D (pós-P2 / 2026-09-19)

**Branch auditada**: `arena/01a0baf3-busao` @ `73cb695` (P2) + `a88a03d` (L18)
**Data**: 2026-09-19 · **Auditor**: Agent Mode (Arena) — varredura de `assets/**`, `scripts/**`, `tools/blender/**`, `CREDITS.md`, `PROVENANCE.md`, `tools/validate_project.py`
**Objetivo do solicitante**: checar realismo visual + física “mundo real” e garantir **100 % de assets originais feitos do zero no Blender** (nenhum CC0 de terceiros), com PBR/texturas que passem realismo.

---

## 1) Veredito executivo — 2 linhas

**Visual**: **NÃO está realista nem 100 % original.** 73 % dos GLBs são originais Blender headless do projeto (ótimo), mas os 2 assets-âncora do gameplay — **protagonista humano (Quaternius CC0)** e **cachorro caramelo (Khronos Fox CC0)** — são externos. Texturas do mundo são procedurais PIL 1024 px (tileável, semente 20260918), não baked de high-poly; iluminação é 1 DirectionalLight sem GI/lightmap.

**Física**: **NÃO é física de mundo real.** É *arcade runner*: 3 lanes com `lerp`, salto `sin()`, `dash` invencível, tráfego em `−Z` com bob `sin()`. Zero `RigidBody3D / CharacterBody3D / CollisionShape3D`, zero `gravity / mass / friction / restitution / impulse`. Sem detecção contínua, sem ragdoll.

**Meta 100 % Blender original**: **atingível, mas exige 9–10 lotes dedicados** (estimativa abaixo). O pipeline Blender headless (`bpy==4.5.14` + `kit_base.py`) já existe e já gerou 38 GLBs originais — só precisa ser estendido ao humano + cão + PBR 2–4K + física Bullet.

---

## 2) Metodologia

1. **Inventário file-system**: `find assets -type f` (238 arquivos) + leitura de `LEIA-ME.md` de cada pasta e `PROVENANCE.md` com SHA-256.
2. **Crédito & licença**: `CREDITS.md` + `QUATERNIUS-LICENSE.txt` (CC0 1.0).
3. **Inspeção de código**: `scripts/game_3d.gd` (4207 linhas), `runner_character.gd`, `world_animal.gd`, `building_kit.gd`, `world_spawner.gd`, `economy_handler.gd`, `ads_handler.gd`; grep por `RigidBody`, `CollisionShape`, `move_and_slide`, `gravity`.
4. **Texturas**: `tools/generate_textures.py` (MASTER_SEED 20260918, `height_to_normal` OpenGL), `assets/textures/pbr/*.png` (30 MB), inspeção de resolução e perfil `world_spec.json`.
5. **Render**: `project.godot` (`renderer/mobile` + `gl_compatibility`, `shadow 1024`, `msaa 1`, sem `GI`), `scripts/render_quality.gd`.
6. **Build Blender**: `tools/blender/build_*.py` (`build_pombo`, `build_aves`, `build_quadrupedes`, `build_lote4..9c`, `build_lote5..6` para veículos).
7. **Validação automática**: `tools/validate_project.py` → `PRE-FLIGHT OK` (não valida realismo, só contratos).

---

## 3) Inventário completo — o que é original vs. externo

| Categoria | Quant. GLB | Originais Blender headless (projeto, CC0 próprio) | Externos CC0 de terceiros | Veredito realismo | Observação |
|---|---|---|---|---|---|
| **Humano protagonista** | 1 rig + 8 parts + 2 anims | **0** | **10** (`quaternius/` base + `parts/` + `UAL1_Standard.*` + `Fox`) — **100 % externo** | Baixo: stylized low-poly (≈1.18 m, 70–90k tris com subsurf 2), pele plástica, cabelo card | `runner_character.gd:22–26` carrega `quaternius/animation/UAL1_Standard.res/.glb`, `base/Superhero_*`, `parts/Male|Female_Peasant_*`. |
| **Dog caramelo** | 1 | 0 | **1 externo**: `animais/caramelo.glb` = Fox Khronos (`glTF-Sample-Assets/Models/Fox`, CC0) | Médio: fox ≠ vira-lata caramelo, focinho curto, orelha pontuda; anim Walk genérico | `world_animal.gd` chama `_modelo_animal_opcional("caramelo")` → Fox; pombo/passaro/gaivota/urubu + 6 quadrupedes já são originais. |
| **Fauna restante (9)** | 9 | **9 originais** (`pombo 13 ossos Walk/Idle`, `passaro/gaivota/urubu 12 ossos Walk/Fly`, `capivara/cavalo/boi 16 ossos Walk/Idle/Lie|Graze`, `macaco 9 ossos`, `caranguejo 9 ossos`) | 0 | Médio-baixo: silhueta ok, mas sem pelos/penas groomed, sem blendshapes | `tools/blender/build_pombo.py`, `build_aves.py`, `build_quadrupedes.py`, `build_lote4.py` |
| **Veículos** | 11 (+4 variantes) | **11 originais** Lote 5 (`car, car_azul/prata, truck/vermelho, motorcycle/verde, bus_traffic, onibus, carro, bicycle`) via `build_lote5.py` + `build_lote6.py` (roda baked 256²) | 0 (pasta aceita CC0 opcional, mas hoje só originais) | Baixo-médio: super-elipse low-poly, vidro sem refração, sem interior, roda nomeada `Wheel*` gira `rotation.x` | `GLB_FIT` 4.4×1.55 m (car) etc; falta painel/instrumentos. |
| **Props urbanos** | 8 | **8 originais** (`cone, hidrante, orelha, banco, lixeira, poste, ponto, carrinho`) via `build_lote7.py` | 0 | Médio: escala real (±0.01 m), mas material `Principled` simples, sem sujeira AO baked | `Tint*` branco pintado por `_tint_glb` |
| **Cena (casas/prédios)** | 14 | **14 originais** (`palmeira, arvore, caixa_dagua, varal, bandeira, outdoor, portao, barraca, casa/favela/colonial, predio2/3, loja, terminal`) via `build_lote9a/b` | 0 | Médio: forma correta, mas teto/parede sem telha/vão real | `TintWall/Roof/Trim/Awning` |
| **Coletáveis** | 11 | **11 originais** (`coin, golden, coffee, bread, pastel, sugarcane, pass, coxinha, guarana, pix, umbrella`) via `build_lote8.py` | 0 | Médio-alto: leitura boa, texto PIL 1K | centro na origem para giro Y |
| **Sky FX** | 2 | **2 originais** (`aviao, drone`) via `build_lote8.py` | 0 | Médio | |
| **Texturas PBR mundo** | 33 imgs (30 MB) | **Geradas PIL 1024²** (`generate_textures.py`, seed 20260918) + 10 `pbr/*` (asfalto, calcada_laje/mosaico, reboco, tijolo, madeira, metal, terra_vermelha — cada com albedo/normal/orm) | 0 externo, mas **não são baked de high-poly** | **Baixo realismo**: noise FBM `value_noise` + cracks random walk, `height_to_normal strength 1.35`, `rough 0.80` — tiling visível a <2 m, sem micro-variação de agregado, sem Height/Displacement | `building_kit.gd:119 _textura("%s_albedo.png")` usa `ORMMaterial3D` quando `pbr/` existe, senão `StandardMaterial3D` flat. |
| **Texturas personagem** | 30 imgs (80 MB) | **Externas Quaternius** (`T_Hair_*, T_Superhero_*_Dark/Normal/Roughness`, `T_Peasant_*`, `T_Regular_*`) + `pelo_realista, pele_realista, jeans, metal_pintado` PIL | **100 % Quaternius** | Baixo-médio: 1–4K mas stylized, sem `SSS` real, sem `anisotropy` cabelo | `runner_character.gd` usa `TEXTURE_CREATOR_*` locais só para acessórios Creator (top/denim/metal/rubber). |
| **Áudio** | 23 WAV | **Procedural PCM 22 kHz** (`generate_audio.py`, `tone/square/noise`, `RATE=22050`) | 0 | Funcional, não real | `step, jump, bark, trovao` são `tone`/`noise`, não foley. |

**Conta final originalidade**: **38/48 GLBs diretamente visíveis são originais (79 %)**, mas os 2 GLBs que o jogador vê 100 % do tempo (humano + dog) são externos → **não cumpre meta 100 % Blender**.

---

## 4) Auditoria visual — nota 0–10 (10 = foto-real AAA mobile)

| Eixo | Nota | Evidência | O que quebra o realismo |
|---|---|---|---|
| **Modelagem humana** | **3.5** | Quaternius `Superhero` 1.18 scale, Peasant 4 parts, `ModelPivot` Y180, `MODEL_SCALE 1.18`, `Skeleton3D` com `BoneAttachment3D` para `CreatorPhone/Tattoo/Earring` | Corpo “super-herói” estilizado (ombros largos, cabeça pequena), roupa Peasant fantasiosa (colete medieval), sem dobras dinâmicas, mãos sem unhas, pés “Peasant_Feet” sem solado real. |
| **Modelagem dog** | **3.0** | Fox Khronos: 765 KB, Survey/Walk/Run, escala `GLB_SIZES caramelo [0.95,0.72]` via `_fit_glb` | Espécie errada (raposa ≠ caramelo SRD), sem variação de pelagem, cauda volumétrica simples, sem `blendshape` focinho. |
| **Fauna/props/veículos/cena** | **5.5** | `kit_base.py: loft(pilar, elipsoide, painel_pena)` + `join_parts + vertex_groups + armature 9–16 bones` + `export_gltf(yup, skins, ACTIONS)` + preview `CYCLES 24 samples 640×480` | Low-poly com `Subdiv 2` ainda facetado de perto (<1 m); veículos sem porta-maçaneta côncava, sem farol volumétrico; árvores 1.7 m com 4 copas achatadas, sem folhas alpha-card com translucency. |
| **Texturas PBR** | **4.0** | `gen_asphalt: fbm 256/48/6, gravel 0.6+mid0.4, cracks 9×150 steps, repair patch>0.68` + `gen_sidewalk: stone 64, wave senoide, grout 3px` + `gen_facade: 4×4 janelas 256 px, frame/glass/sill/ao` | **1024 px** estica a 5 m (`uv1_scale 5` em `_texture_scale` → texel 0.5 cm mas tiling repetitivo), `asfalto_albedo 1.1M, normal 2.9M` sem pedra 3D, `rough 0.80` uniforme, sem `height/parallax`, sem `detail map`; `calcada_laje` sem desgaste de junta. `pbr/` ORM tem `metal_zincado_albedo 485 KB` minúsculo → pinta. |
| **Materiais** | **5.0** | `building_kit.gd: material()` → `ORMMaterial3D(albedo+normal0.8+orm) else StandardMaterial3D`; `game_3d.gd:_material()` com `albedo_texture, normal_scale 0.32–0.85, roughness_texture, metal 0.42–0.85, subsurf_skin 0.12, hair anisotropy 0.24` | `metal_pintado_normal 28 KB` (quase vazio), `roughness 1.0` quando há `rough_map`, mas `asphalt roughness` é gray 8-bit sem `AO`; `chrome` sem `reflection probe`; pele `subsurf_scatter_strength 0.06` insuficiente para SSS. |
| **Iluminação / sombra** | **4.5** | `WorldEnvironment: BG_SKY PanoramaSkyMaterial (ceu_tropical/sunset/nublado 2048×1024), ambient 0.72, tonemap ACES exposure 1.06, glow 0.42, fog 0.0072/ aerial 0.5`, `DirectionalLight WarmSun -48°/-28° 1.25, shadow 1024 bias0.045 opacity0.72 max72m`, `camera fov 49→52, near0.1 far380, LOD visibility_range_end 35–96 + impostor quad billboard` | **Sem GI/baked lightmap, sem reflection probe, sem SSAO/SSIL, sem contact shadow**, sombra 1024 borra a 8 m, `shadow_normal_bias 1.2` causa peter-panning, `fog_sky_affect 0.22` flat, céu `Panorama` sem `sun disk`. `blob_shadow` P2 é `PlaneMesh UNISHADED α0.30` — funciona, mas sem `Variance Shadow Map`. |
| **LOD / performance** | **6.5** | `MultiMesh` para lajes/mosaicos/janelas/postes/folhas, `visibility_range 35/96`, `TreeImpostor Quad 1.6×2.4 billboard + LEAVES_REAL texture`, `particle dust 80/splash 64` | `tree` high 35 m → impostor 1 quad já ajuda, mas sem `HLOD` para quarteirão (28 m) inteiro; `draw_pass_1 = QuadMesh` barato, mas `GPUParticles` sem `Sort`. |
| **Animação** | **5.0** | `UAL1_Standard.res 2.6M + UAL1_Standard.glb 7.6M` → `Idle/Walk/Sprint/Jump/Crouch_Idle/Crouch_Fwd`, `LOCOMOTION_CLIP_SPEED 4.0 m/s, max_playback 2.2`, `world_animal: _enter_pose("jump" 0.45), _animate_caramelo tail -1.12..0.30, leg sin(10* t)` | `Walk` patina se `player_speed` ≠ 4.0 (escala linear), sem `foot IK`, sem `head look-at`, `crouch` squash `0.94` achata esqueleto, dog `Fox Walk` sem `play bow` real. |
| **Escala / proporção** | **7.0** | `LANE_X [-3.25,0,3.25]` (3.25 m entre faixas, ok para rua 6.6 m + calçada 6+2.5 m), `PLAYER_HEIGHT 2.15` (alto — brasileiro médio 1.71), `HORIZON_Z -75` | Jogador 2.15 m parece 12 % gigante vs. porta 0.62×0.82 m (`HouseDoor`); `bus_traffic 7.4×3.0` ok, mas `onibus 8.2×3.0` baixo (real 12×2.6×3.2). |
| **UI vs. mundo** | **6.0** | `hud_3d.gd` com `shop_scroll_mask 1125→1280`, `character_data 20 (10M/10F)` | HUD não oclui mundo, mas `set_motion` chamado todo frame sem `delta` adaptado → micro-stutter em 30 Hz. |

**Média visual ponderada: 4.8/10** — jogável e coerente como arcade stylized, distante de realismo foto (precisa 7.5+).

---

## 5) Auditoria física — “se comporta como mundo real?” **NÃO**

**Inspeção grep**: `game_3d.gd` 4207 linhas → **0** ocorrências de `RigidBody3D, CharacterBody3D, CollisionShape3D, Area3D, move_and_slide, gravity` (só `ParticleProcessMaterial.gravity (0,-1.2)` para poeira e `(0,-6)` para respingo).

| Subsistema | Atual (arcade) | Mundo real (esperado) | Gap crítico |
|---|---|---|---|
| **Locomoção** | `distance += speed*dt` (`player_speed 5.0 → _phase_speed_for 5→18`, `speed_boost 1.22, slow 0.55, dash 2.0`), `player_x = lerp(player_x, LANE_X[lane], dt*13)`, `lane_change_velocity` | `CharacterBody3D` com `velocity.x = input* accel`, `mass 70–85 kg`, `friction μ=0.35 asfalto / 0.55 calçada`, `max lateral accel 4 m/s²`, `inércia` para não teleportar de faixa | Sem inércia: troca de faixa é cinemática instantânea, sem derrapagem, sem desaceleração em curva. |
| **Pulo** | `jump_timer 0.9 (julia/tiao 1.15)`, `jump_height = sin(progress*PI)*2.05`, `jump_duration` fixo, `safe = jump_timer>0 or dash>0` para `pothole/car` | `velocity.y` com `gravity 9.81, jump_impulse = sqrt(2*g*h) ≈ 6.3 m/s para h=2.05`, `air_time ≈ 1.28 s`, parábola `y = v0*t -0.5*g*t²`, colisão contínua com `move_and_slide_with_snap` | Salto é **senoide sem gravidade**: altura e duração desacopladas da física; “invencível” vence obstáculo mesmo atravessando geometria. |
| **Colisão** | `passed = entity_z>=0.6 → _resolve_entity` por `lane == player_lane` + `jump/slide/dash` booleano; `hit → hearts--, camera_shake 0.55, flash 0.18` | `CollisionShape3D` (capsule 0.35×1.75) + `Area3D` por obstáculo com `layer/mask`, `Swept test` para `motorcycle 3.8 m/s`, `impulse = m*Δv` para dano, `cooldown` baseado em `invincibility frames` + `knockback` | Sem shape: “colisão” é checagem de `z` no eixo, atravessa lateralmente se `lane` diferente mesmo com sobreposição visual; `truck 6.4×2.7` bloqueia 2 faixas mas só 1 lane conta. |
| **Atrito / terreno** | `surface == "asphalt/dirt/sidewalk/cobble"` só muda `material` e `tile_color`; `dirt: DirtTrack 2.65×0.02` visual | `μ` diferente muda `braking distance = v²/(2*μ*g)` e `footstep sound`, `poça: _clima.wetness>0.35 → splash` já existe mas não afeta `friction` | `dirt/cobble` não altera jogabilidade — deveria retardar 12–18 % e aumentar `slip`. |
| **Massa / impulso tráfego** | `traffic_speed_for: car 2.3, bus 1.35, moto 3.8, truck 1.05 + seed%3*0.42` + `node.position.z -= traffic_speed*dt` + `wheel_spin speed*dt/0.30` + `body_bob sin` | `mass: car 1200, truck 8000, moto 180 kg`, `drag`, `braking`, `momentum conservação` em colisão | Veículos são `Node3D` sem massa: `truck` a 1.05 m/s não empurra, `moto 3.8` atravessa `bus` sem desvio. |
| **Queda / ragdoll** | `hearts<=0 → revive 5s ou game_over`, sem queda física | `Ragdoll` com `PhysicalBone3D + Joint` + `impulse` no `hit` + `get_tree().reload` | Morte é HUD, sem corpo caindo — quebra imersão realista. |

**Conclusão física**: o jogo é **determinístico por `distance` e `rng 20240917`**, não por integração física (`60 Hz` em `project.godot` existe mas não é usado). Para “mundo real” precisa trocar `Node3D` por `CharacterBody3D` + `PhysicsServer3D` com `space`.

---

## 6) Texturas — “passam ainda mais realismo?” **NÃO, ainda são placeholder procedural**

- **Pipeline atual**: `generate_textures.py` → `1024²` com `numpy` FBM 3 octaves (`freq 256→48→6`), `speck>0.9975` pedrinha, `cracks 9×150 random_walk`, `repair patch>0.68` → `albedo_realista.png 1.1M`, `normal 2.9M` via `height_to_normal strength 1.35`, `roughness gray 809K`. `fachada_reboco/tijolo 1024² 4×4 janelas 256 px` com `glass 0.10,0.15,0.21`, `frame 0.90`, `sill`. `pbr/ 30M` com `albedo/normal/orm` mas `orm` é `rough+metal+AO` em 8-bit sem `height`.

**Falhas de realismo**:
- **Resolução**: 1024 a 5 m de calçada (`uv1_scale 5`) → 0.2 texel/cm mas repetição a cada 1.02 m visível; `asfalto_normal 2.9M` sem micro-agregado 2–4K.
- **Sem baker**: sem `high-poly → low-poly bake` (AO curvature, thickness), sem `height/displacement`, sem `edge wear` Curvature, sem `dust streak` por gravidade.
- **Tiling**: `fbm 6` para `patch` cria mancha circular sem fluxo de água; rachadura `random_walk 1.6 px` sem `branch` real.
- **Metal**: `metal_pintado_normal 28 KB` quase plano → reflexo sem variação, sem `clearcoat`.

Para foto-real precisa: **sculpt high 2–5M tris → bake 4K `albedo/normal/AO/height/rough/metal` + `detail 512` + `triplanar 3.0` já existe, mas com mapas reais**.

---

## 7) Lista completa do que **FALTA** alterar/implementar — por LOTES (próximos)

> Cada lote = branch `arena/…`, PR com `tools/validate_project.py PRE-FLIGHT OK`, sem paywall, com `docs/RELEASE_LOTENN.md`.

### Lote 19 — Humano Protagonista 100 % Original (BLOQUEANTE para meta)
**Falta**: substituir `assets/characters/quaternius/**` (10 arquivos externos, CC0) por 20 humanos brasileiros modelados do zero no Blender.
**Escopo**:
- Sculpt high 1.5M + retopo low 12k tris + UV 1×4K por gênero (M/F) + 10 variações de `character_data` (pele, cabelo, roupa brasileira: camiseta, jeans, vestido, uniforme).
- Rig `Humanoid` 55 bones (mixamo-like) + `shapekeys` rosto + `cloth sim` parcial para camiseta.
- Bake `albedo 4K + normal + ORM + SSS mask + anisotropy hair` via `bpy` + `kit_base` estendido.
- Reexporta `Superhero_Male/Female_FullBody.gltf` com mesmo esqueleto (`spine_01..foot_r`) para não quebrar `runner_character.gd: REGION_BONES`.
- Atualiza `PROVENANCE.md` com `BLENDER-ORIGINAL` e remove `QUATERNIUS-LICENSE.txt` externo.
**Entregável**: `assets/characters/humanos/` 20 GLBs + `CREDITS: Modelagem original Blender` + `validate_character_manifest` ok.
**Aceite**: `runner_character.gd` sem `quaternius/` path, `primary_asset_loaded true` sem fallback, `AnimationLibrary` própria.
**Estimativa**: 3–4 dias (1 dia por 5 variações com `build_humanos.py`).

### Lote 20 — Cachorro Caramelo SRD Original
**Falta**: trocar `animais/caramelo.glb` (Fox Khronos externo, CC0, espécie errada) por SRD vira-lata caramelo brasileiro.
**Escopo**: sculpt 800k → retopo 8k, pelos card/groom, rig 17 bones + `DogEye/Collar/Tag`, clips `Walk 24f, Run 16f, Idle 48f, PlayBow 20f, Bark 12f, Jump 10f` (mesmo contrato `world_animal.gd: set_running / _animate_caramelo tail -1.12`); bake 2K `pelo_realista` já existe mas precisa `pelo caramelo 2K` específico.
**Aceite**: `LEIA-ME.md` sem “Fox”, `GLB_SIZES caramelo [0.95,0.72]` mantido, `_audit_3d_entity` encontra `Animal3D_caramelo`.
**Estimativa**: 2 dias via `build_caramelo.py`.

### Lote 21 — Veículos Foto-Real (upgrade dos 11 já originais)
**Falta**: os 11 GLBs Lote 5 são low-poly super-elipse sem interior; `car_azul 316KB` é só cor flat.
**Escopo**: high 2M (casco com vinco, maçaneta côncava, grade, farol com lente) → low 25k + bake 4K `car_paint + interior + glass + tire` (normal + ORM + `emissive` para `onibus` letreiro “PONTO FINAL” com fonte real). Adiciona `CollisionShape3D` box por veículo no `world_spawner` (massa 1200–8000).
**Aceite**: `bus_traffic` não atravessa `truck`, `Wheel*` ainda gira, `GLB_FIT` ajustado para 12 m ônibus real.
**Estimativa**: 3 dias (`build_lote5_v2.py` reaproveita casco).

### Lote 22 — PBR Mundo 4K Realista (texturas)
**Falta**: `generate_textures.py` 1024 PIL → 4K baked.
**Escopo**: manter semente 20260918 mas trocar `fbm` por sculpt high: asfalto com agregado 5–19 mm scan, `height_to_normal` via baker (não `dx` numpy), `rough` por `cavity`, `calcada portuguesa` com pedra irregular + rejunte 5 mm desnivelado, `fachada` com `tijolo 128×34` real + `reboco` com `stain streak` por gravidade. Gera `pbr/* 4K` + `height 16-bit` para `parallax` shader. Atualiza `world_spec.json` `uv_escala` e `triplanar_sharpness`.
**Aceite**: `building_kit` sem tiling visível a 1 m (foto a 640×480 `kit_base setup_preview` sem repetição), `validate_project` continua `albedo_texture`.
**Estimativa**: 2 dias (bake batch).

### Lote 23 — Física Mundo Real (Bullet)
**Falta**: arcade `lerp/sin` → `PhysicsServer3D`.
**Escopo**: `player_root` → `CharacterBody3D` (`capsule 0.35×1.75, mass 75, friction 0.4, gravity 9.81, jump_impulse 6.3, snap 0.4`), `move_and_slide()` + `is_on_floor()`, `slide` = `crouch` com `head clearance raycast`, `dash` = `impulse 900 N·s` com `cooldown 3.2`. Obstáculos → `RigidBody3D` (car/moto/truck) ou `StaticBody3D` (hydrant, bench) com `CollisionShape3D` (box/cylinder). `pothole` → `Area3D` com `friction 0.15` e `impulse -Y 3`. `road_surface` muda `physics_material_override`. Ragdoll em `hearts==0` via `PhysicalBone3D`.
**Aceite**: salto parábola 1.28 s medida, `truck` empurra `car`, `hearts` só perde se `shape` intersecta fora de `invencible`.
**Estimativa**: 4 dias, maior risco.

### Lote 24 — Iluminação Realista
**Falta**: 1 `DirectionalLight 1024` → IBL + GI.
**Escopo**: `WorldEnvironment` com `SDFGI` ou `VoxelGI` + `ReflectionProbe` por quarteirão (28 m) + `lightmap bake` para `building_kit` static (`72×72 probe`, `AO 0.6`), `shadow 4096 VSM`, `SSIL/SSAO 0.4`, `volumetric fog` já existe mas com `fog_aerial 0.5` → `VolumetricFog 64`, `sky` com `PhysicalSky` + `sun disk` + `clouds 3D` em vez de `Panorama 2048`.
**Aceite**: sombra contact a 0.5 m nítida, `TreeImpostor` com `translucency`, `cold_start <2800` ainda ok em `Adreno 610` com `MSAA 1`.
**Estimativa**: 2 dias.

### Lote 25 — Áudio Foley Realista (opcional p/ 100 %)
**Falta**: `generate_audio.py` `tone/square/noise` → foley gravado/baked com `reverb` por `scenario.weather`.
**Escopo**: substituir `step.wav (noise 105 Hz)` por 4 variações de passo em asfalto/calcada/terra, `bark` por caramelo real, `bus_horn` por buzina 2 tons, `trovao 224K noise` por IR. Mantém `RATE 22050` mas com `stereo` + `Bus` em `AudioServer`.
**Aceite**: `AudioManager` sem `tone()` em prod, `CREDITS` lista gravação própria CC0.
**Estimativa**: 1 dia.

### Lote 26 — Limpeza Final 100 % Original + Legal
**Falta**: remover `QUATERNIUS-LICENSE.txt` e `Fox` residual, atualizar `CREDITS.md` para “Modelagem original Blender” em todos, assinar `PROVENANCE human/dog` com SHA-256 novo, garantir `tools/validate_project.py` não falha por `QUATERNIUS*` token ausente (atualizar `required_tokens` para não exigir `QuaterniusOutfit_`).
**Aceite**: `grep -R quaternius assets → 0`, `grep -R "Fox" assets → 0`, `CREDITS` sem URLs CC0 externos, `project.godot` sem `quaternius` path.
**Estimativa**: 0.5 dia.

---

## 8) Roadmap recomendado — ordem de execução

| Ordem | Lote | Dependência | Impacto realismo | Risco | Esforço |
|---|---|---|---|---|---|
| 1 | **19 Humano** | — | ★★★★★ (jogador 100 % tempo) | médio (rig) | 4 d |
| 2 | 20 Dog SRD | 19 (mesmo rig pipeline) | ★★★★ | baixo | 2 d |
| 3 | 23 Física | 19 (CharacterBody precisa do novo esqueleto) | ★★★★★ (mundo real) | **alto** | 4 d |
| 4 | 22 PBR 4K | — | ★★★★ | médio | 2 d |
| 5 | 21 Veículos HD | 22 (mesmo PBR) | ★★★★ | médio | 3 d |
| 6 | 24 Luz | 22 (materiais) | ★★★★ | médio | 2 d |
| 7 | 25 Áudio | — | ★★ | baixo | 1 d |
| 8 | 26 Limpeza | todos | ★ (legal 100 %) | baixo | 0.5 d |

**Total estimado**: **18.5 dias** (≈3 semanas) para 100 % original + física/gi realista, mantendo `PRE-FLIGHT OK` e `APK ≤85 MB` (com `compress_assets_lote14.py` → `basis` para 4K).

---

## 9) Riscos & mitigação para meta 100 %

- **APK estourar 85 MB** com 4K → mitigar com `basis_universal` + `compress_assets` já existente + `HLOD` por quarteirão.
- **Performance Adreno 610** com `SDFGI + 4K` → fallback `project.godot.lote2` já tem `gl_compatibility`; manter `shadow 1024` em `low tier` via `RenderQuality`.
- **Anim UAL CC0** ainda externa → Lote 19 cria `AnimationLibrary` própria (8 clips) com `bpy` keyframe, dispensando `UAL1_Standard.*` (hoje 10 MB).
- **Quebra de contrato** (`HumanPedestrian3D, Animal3D_caramelo`) → novos GLBs mantêm `skeleton bone names` e `animation clip` contendo `walk/idle` no nome (audit busca string, não hash).

---

## 10) Próximo passo imediato (se autorizado)

**Começar pelo Lote 19** (humano original) — criar `tools/blender/build_humanos.py` a partir de `kit_base.py: loft/armature/skin/join_parts` com sculpt base `Male/Female` 1.5M, retopo 12k, UV 0–1, bake 4K, export `human_m_01..10.glb / human_f_01..10.glb`, atualizar `runner_character.gd: BODY_PATHS/OUTFIT_PATHS` e `character_data.gd` sem mudar API.

Se preferir física primeiro, começamos pelo Lote 23 (CharacterBody3D) em paralelo — mas o humano novo já facilita o `PhysicalBone3D` ragdoll.

---

### Anexos — comandos de regeneração (atuais, já originais)

```bash
python3 tools/generate_textures.py          # 1024 PIL → será substituído por bake 4K no Lote 22
python3 tools/blender/build_pombo.py        # pombo 13 ossos
python3 tools/blender/build_aves.py         # passaro/gaivota/urubu
python3 tools/blender/build_quadrupedes.py  # capivara/cavalo/boi
python3 tools/blender/build_lote4.py        # macaco/caranguejo
python3 tools/blender/build_lote5.py        # 11 veículos low-poly (será HD no Lote 21)
python3 tools/blender/build_lote6.py        # variantes roda baked 256²
python3 tools/blender/build_lote7.py        # 8 props
python3 tools/blender/build_lote8.py        # 11 coletáveis + 2 sky
python3 tools/blender/build_lote9a.py       # palmeira/árvore/caixa/varal/bandeira/outdoor/portão/barraca
python3 tools/blender/build_lote9b.py       # casa/favela/colonial/predio2/3/loja
python3 tools/validate_project.py           # PRE-FLIGHT OK
```

**Resultado final desta auditoria**: o jogo **não está realista nem 100 % original hoje**, mas **o pipeline para ficar está 70 % pronto** (38/48 GLBs já Blender headless, `kit_base.py` maduro, `pbr/` ORM já usado). Com os 8 lotes acima (19–26) o projeto atinge física de mundo real + todos os assets do zero com PBR 4K baked, mantendo `validate_project` verde e jogabilidade arcade como modo opcional (“Arcade vs. Realista” em `Options`).

