# Plano — Personagens Realistas 100% Blender (20 corredores)

**Objetivo:** Cada um dos 20 corredores de `scripts/character_data.gd` deve ter identidade visual única, realista e brasileira, modelada do zero no Blender 5.0 headless (sem Quaternius), com esqueleto compatível `runner_character.gd` (pelvis, spine_01..03, neck_01, Head, clavicle, upperarm, lowerarm, hand, thigh, calf, foot, ball + dedos), PBR 4K, e acessórios que contam a história do personagem.

**Saldo de teste:** `resources/game_balance.tres: starting_coins 40 → 100000` + `scripts/save_data.gd: _sanitize_data()` injeta 100k uma única vez (`debug_100k_granted`) — total catálogo = 9.300, então 100k compra tudo com folga. Reverter para 40 em produção.

---

## 1. Princípios de Realismo (para todos)

- **Escala:** Humano base `Humano_M/F` 1.77m, `MODEL_SCALE 1.03 → 1.82m`. Ombro 0.50, quadril 0.36-0.45, cabeça 0.32 diam, perna 0.82. Nada de `Capsule` cru — usar `pilar_z seg24` + `bevel 0.012` + `shade_smooth` (já em `build_humanos.py`).
- **Topologia:** Corpo é `join_parts` com `vertex_groups` por osso (pelvis, spine, etc.) + `ARMATURE` modifier. Evitar `caixa` plana — usar `pilar_z` elíptico ou `caixa` com `BevelMild`.
- **Materiais:** `QuaterniusSkin` (pele), `Hair`, `Camisa/Calca/Sapato` (tintáveis via `_apply_profile_palette`), `OlhoBranco/Iris`. Texturas PBR 4K `assets/textures/` (pele, jeans, tecido, metal, borracha) com `normal`/`roughness` + `uv1_scale 1.5-3.0`.
- **Acessórios:** Presos via `BoneAttachment3D` (`_bone_attachment`) — ex: `hand_r` para celular, `Head` para boné, `spine_02` para mochila. Sempre `cast_shadow ON`.
- **Animações:** 6 clips `Idle/Walk/Sprint/Jump/Crouch_Idle/Crouch_Fwd` gerados por `key_rot/key_loc` + `linearize()` compatível Blender 5 (layers/strips/channelbags). Skeleton idêntico para todos — só muda mesh/materiais/acessórios.

---

## 2. Catálogo Detalhado (20)

### Lote 1 — Cotidiano Urbano (10)

#### 1. Zé Atrasado (`ze`, M, casual, 0 — já desbloqueado)
- **Identidade:** Jovem trabalhador 24a, pardo, 1.78, magro-atlético, cabelo crespo curto, mochila todo dia.
- **Roupa:** Camiseta vermelha `#e55359` levemente desbotada, calça jeans escura `#263a55`, tênis amarelo `#f3ca55` com sola borracha. Mochila tiracolo cinza-azulada `#55c4c8` (strap em `spine_02`).
- **Blender:** Base `Humano_M` pele `#b87655`, cabelo `Hair` curto `elipsoide_bl` sub1, mochila `caixa` 0.32×0.40×0.02 em `spine_01`, tênis `caixa` 0.11×0.18×0.04.

#### 2. Rafa Motoboy (`motoboy`, M, motoboy, 260, +22% vel)
- **Identidade:** Entregador 27a, negro, 1.75, forte, barba rala.
- **Roupa:** Colete refletivo laranja `#f08b3e` com faixas 3M, calça cargo `#202b39`, tênis branco `#e5e9df`, **capacete** `elipsoide_bl` 0.13×0.13×0.11 em `Head` + viseira, **bag térmica** `caixa` 0.28×0.32×0.22 em `spine_02` com logo.
- **Blender:** Já tem `_build_motoqueiro` com `Driving_Loop`; aperfeiçoar bag com `bevel` e material `metal` bordado.

#### 3. Luan do Skate (`luan`, M, skater, 320)
- **Identidade:** Adolescente 17a, pardo claro, 1.72, esguio, boné virado.
- **Roupa:** Moletom roxo `#7659d6` oversized, bermuda mostarda `#d5a45f`, tênis branco `#f3eee0` cano médio, boné aba reta `cylinder` em `Head`.
- **Blender:** Moletom `pilar_z` alargado `scale 1.3`, boné `attach_cap` visor, shape `skate` mini nos pés.

#### 4. João Gamer (`joao`, M, gamer, 380, câmera lenta)
- **Identidade:** Estudante 19a, branco, 1.80, magro, cabelo colorido leve.
- **Roupa:** Jaqueta azul `#2f9fe2` com zíper, calça escura `#303044`, tênis ciano `#8de5d0`, **fone** `torus` 0.08 em `Head`.
- **Blender:** Jaqueta `caixa` 0.38×0.18×0.14 com `metal` zíper, fone `torus` em `Head`.

#### 5. Carlos da Obra (`carlos`, M, obra, 440, escudo)
- **Identidade:** Pedreiro 35a, pardo, 1.74, parrudo, barba.
- **Roupa:** Capacete branco `elipsoide_bl` 0.12, colete laranja `#ee793d` com bolsos, calça cinza `#56606c`, bota marrom `#5e3828` bico aço.
- **Blender:** Capacete `attach_hat` 0.30 brim, colete `caixa` 0.38×0.14, bota `caixa` 0.12×0.24×0.07.

#### 6. Maria do Bairro (`maria`, F, bairro, 180, escudo)
- **Identidade:** Comerciante 38a, negra, 1.65, curvilínea, cabelo cacheado curto.
- **Roupa:** Blusa estampada rosa `#e58aab`, saia roxa `#5b4070`, sandália amarela `#f2c65a`, bolsa tiracolo `#68c6b1`.
- **Blender:** Base `Humano_F` quadril 0.21, saia `pilar_z` 0.34 elíptico, bolsa `attach_side_pouch`.

#### 7. Bia Estudante (`bia`, F, estudante, 240, ímã)
- **Identidade:** Estudante 16a, parda, 1.62, mochila escolar.
- **Roupa:** Camisa branca `#f2f0e5`, calça jeans `#3a6fa0`, tênis vermelho `#ec6b6a`, mochila pixel `caixa` 0.24×0.32.
- **Blender:** Uniforme `Camisa/Calca`, mochila `BoxMesh` em `spine_02`.

#### 8. Camila do Negócio (`camila`, F, empreendedora, 300, 2× moedas)
- **Identidade:** Jovem empreendedora 26a, morena, 1.70, cabelo liso longo.
- **Roupa:** Macacão verde `#46b6a3`, bolsa tiracolo marrom `#305a5d`, sapatilha amarela `#f0b84e`, **tablet** `caixa` 0.17×0.01×0.23 em `hand_l`.
- **Blender:** Macacão `pilar_z` 0.38, tablet `attach_hand_book`.

#### 9. Júlia Atleta (`julia`, F, atleta, 360, pulo)
- **Identidade:** Corredora 22a, negra, 1.72, atlética, rabo de cavalo.
- **Roupa:** Top rosa `#e75076`, legging escura `#242c4c`, tênis ciano `#68e0c0`, faixa cabeça, garrafa `cylinder` em `hand_r`.
- **Blender:** Top `cylinder` 0.27, legging `pilar_z` 0.07, faixa `torus` em `Head`.

#### 10. Nina Creator (`influencer`, F, creator, 420, ímã)
- **Identidade:** Criadora 23a, parda, 1.68, estilosa, celular sempre.
- **Roupa:** Top texturizado preto `#171824` (`TEXTURE_CREATOR_TOP`), shorts jeans `#4f7897` (`TEXTURE_CREATOR_DENIM`), botas `#171a26` (`TEXTURE_CREATOR_RUBBER`), **celular** `BoxMesh` 0.105×0.20 em `hand_r`, pulseira, tatuagem.
- **Blender:** Já tem `_attach_creator_details` completo — aperfeiçoar com `normal/roughness` e `sequin` metal.

### Lote 2 — Turma do Ponto 2 (10)

#### 11. Chico Carteiro (`chico`, M, carteiro, 480)
- **Identidade:** Carteiro 32a, pardo, 1.76, boné azul `#2f6db8`, sacola amarela `#ffd23e`.
- **Blender:** `_attach_cap` `PostmanCap`, `PostmanStrap` em `spine_02`, `PostmanBag` em `pelvis`.

#### 12. Tião Vaqueiro (`tiao`, M, vaqueiro, 560, pulo)
- **Identidade:** Vaqueiro 40a, sertanejo, 1.80, chapéu couro `#a8672f`, gibão marrom `#5a3d28`, bota `3a2617`.
- **Blender:** `_attach_hat` `VaqueroHat` brim 0.30, gibão `caixa` 0.38.

#### 13. Beto Praiano (`beto`, M, praiano, 620, dash rápido)
- **Identidade:** Surfista 25a, bronzeado, cabelo loiro, regata ciano `#35c4b0`, bermuda areia `#e0d29a`, colar contas.
- **Blender:** `_attach_torus` `SurferNecklace` em `neck_01`, `SurferWristband` em `lowerarm_r`.

#### 14. Nilo Padeiro (`nilo`, M, padeiro, 700, +1 coração)
- **Identidade:** Padeiro 45a, branco, 1.70, avental branco, touca, **bandeja pão de queijo** `sphere` dourado.
- **Blender:** `_attach_hat` `BakerToque`, `_attach_baker_tray` com 3 `SphereMesh` pães.

#### 15. Professor Everaldo (`professor`, M, professor, 780)
- **Identidade:** Professor 50a, grisalho `#8e8e94`, camisa social `#eae4d6`, gravata `#b8864f`, livro.
- **Blender:** `_attach_tie` em `spine_02`, `_attach_hand_book` em `hand_l`.

#### 16. Dona Marta da Feira (`marta`, F, feirante, 500, ímã)
- **Identidade:** Feirante 42a, morena, bandana laranja `#ef8f3f`, avental verde `#4f7a4a`.
- **Blender:** `_attach_bandana` em `Head`, `_attach_apron` em `spine_01`.

#### 17. Vovó Zilda (`zilda`, F, vovo, 540, escudo)
- **Identidade:** Idosa 68a, branca, 1.60, cabelo branco `#d8d5cf`, vestido florido `#d98cb0`, lenço, bolsa mercado.
- **Blender:** `_attach_headscarf` `GrannyScarf`, `attach_side_pouch` `GrannyPurse`.

#### 18. Enfermeira Clara (`clara`, F, enfermeira, 640, +1 coração)
- **Identidade:** Enfermeira 29a, parda, 1.67, uniforme branco `#f4f7fa`, gorro, prancheta.
- **Blender:** `_attach_cap` `NurseCap` sem viseira, `_attach_badge`.

#### 19. Deise Craque (`deise`, F, craque, 720, +22% vel)
- **Identidade:** Jogadora 24a, negra, 1.71, camisa 10 amarela `#f6c945`, calção azul `#1f4f8f`, chuteira verde `#245c3f`, faixa braço.
- **Blender:** `_attach_torus` `CaptainArmband` em `upperarm_l`.

#### 20. Motorista Cida (`cida`, F, motorista, 860, bus +2s)
- **Identidade:** Motorista 36a, parda, 1.69, farda azul `#3f7fae`, quepe, crachá dourado.
- **Blender:** `_attach_cap` `DriverCap` com viseira, `_attach_badge` `DriverBadge` em `spine_02`.

---

## 3. Pipeline Blender (por personagem, 2-3h)

1. **Base:** Duplicar `Humano_M/F` (já com skeleton + vertex_groups). Ajustar `largura_ombro/quadril` e `cor_pele/hair` no topo de `build_one`.
2. **Roupa:** Modelar com `caixa`+`bevel` ou `pilar_z` para volumes orgânicos; aplicar `shade_smooth`; materiais `Camisa/Calca/Sapato/Hair` (nomes exatos para `_apply_profile_palette`).
3. **Acessórios:** Criar via `elipsoide_bl`/`pilar_z`/`caixa`/`torus` e anexar com `_bone_attachment` + `_creator_mesh`/`_batch_material`. Sempre `cast_shadow ON`.
4. **Materiais PBR:** Usar `TEXTURE_CREATOR_*` ou `_batch_material` com `roughness 0.48-0.82`, `normal_scale 0.3-0.6`.
5. **Validação:** `join_parts` deve dar `VERTICES ~2158(M)/2220(F)`; export `bpy.ops.export_scene.gltf` com `export_animations/s skins/yup`. Testar no Godot: `runner_character.set_character(id)` deve trocar sem `fallback`.
6. **Teste de proporção:** `MODEL_SCALE 1.03` → 1.82m; `avatar_scale` NPC 0.88-0.92; moeda 0.12 (7cm) para leitura.

**Ordem de produção sugerida (prioridade gameplay):**
- Semana 1: `ze` (base), `motoboy`, `maria`, `nilo` (coração), `cida` (ônibus)
- Semana 2: `julia`, `tiao`, `professor`, `clara`, `deise`
- Semana 3: `luan`, `joao`, `bia`, `camila`, `influencer` (já detalhada)
- Semana 4: `carlos`, `chico`, `beto`, `marta`, `zilda` + polish geral

**Comando de geração (após Blender 5 voltar):**
```bash
LD_LIBRARY_PATH=/tmp/fake_libs:$LD_LIBRARY_PATH python3 tools/blender/build_humanos.py
# gera Humano_M/F base; para variantes por personagem, criar tools/blender/build_personagens.py que chama _attach_* por id
```

Para personagens individuais, criar `tools/blender/build_personagens.py` que importa `build_humanos` e sobrescreve `cor_*` e chama `_attach_*` específicos antes de `join_parts` — mantém skeleton e animações.

---

## 4. Checklist de Entrega por Personagem

- [ ] GLB < 500 KB, < 3k verts, 1 material por `Camisa/Calca/Sapato/Hair` + pele
- [ ] `grep -n "avatar_scale"` 0.88-0.92, `MODEL_SCALE 1.03`
- [ ] `godot --headless --check` sem `fallback` warning
- [ ] Screenshots `store/screenshots` com personagem em 3 faixas
- [ ] Texto `character_data.gd` `description` corresponde ao visual
