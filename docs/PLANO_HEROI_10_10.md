# Plano do Herói 10/10 — do boneco atual ao personagem da arte-alvo

> Execução: fases 0 e 1 em `docs/execucao/HEROI_FASE0_FASE1.md`; fase 2 em `docs/execucao/HEROI_FASE2.md`
>
> Base: comparação entre o print real do build (26/09) e `docs/arte_alvo_final/1_gameplay_avenida.png`.
> Substitui operacionalmente o `docs/PLANO_HEROI_REALISTA.md` (que ficou em Marco 1 sem execução).

---

## 1. Diagnóstico: por que o print não parece a imagem 1

### 1.1 Números medidos nos assets atuais

| Métrica | Build atual (`Humano_M.glb`) | Necessário p/ arte-alvo |
| --- | --- | --- |
| Triângulos | **4.384** | 28.000–45.000 |
| Vértices | 2.543 | ~18.000–25.000 |
| **Imagens/texturas no GLB** | **0** (só `baseColorFactor` liso) | 5 mapas (albedo, normal, ORM, máscara de pele, alpha do cabelo) em 2K |
| Materiais | 7, todos cor chapada `Principled` | 7 com textura + SSS na pele + alpha nas mechas |
| Ossos | 52 (26 + 20 dedos) | 58–65 (+ olhos, mandíbula, 2 twist por braço/perna) |
| Animações | 6 clips, **Sprint = 17 frames, LINEAR** | 8–10 clips, 30–40 frames, Bézier, root motion medida |
| Geração | `tools/blender/build_humanos.py` — **tubos lofted** (anéis de quads extrudados) | escultura/retopologia com loops reais |

O `ginger+woman.glb` (54k tris, 59 ossos) prova que o engine aguenta a densidade —
mas ele também tem **0 texturas** e está estacionado em `assets/characters/source/`
por causa do teto de tamanho.

### 1.2 Diferenças visíveis, item a item

| # | Imagem 1 (alvo) | Print atual | Causa raiz |
| --- | --- | --- | --- |
| 1 | Silhueta humana com ombro, cintura, panturrilha | Silhueta de cruz/manequim, membros cilíndricos | malha lofted de tubos, sem edge loops de deformação |
| 2 | Pele com poro, oclusão, SSS, variação de roughness | Pele bege plástica uniforme | zero mapas UV-bakeados no GLB; tinte é cor sólida em runtime |
| 3 | Camisa com costura, barra, dobras, número 10 | Retângulo amarelo liso | sem textura de tecido nem normal map de dobras |
| 4 | Cabelo em mechas com alpha e volume | Massa escura fechada | cabelo é mesh sólida, sem cards/alpha |
| 5 | Rosto legível (olhos na órbita, sobrancelha, boca) | Cabeça sem leitura facial a 3 m | olho é primitiva; sem mapa de rosto |
| 6 | Corrida com antifase de braços, lean, contato de pé | Pose travada, braços abertos, pé patinando | 17 frames LINEAR e `LOCOMOTION_CLIP_SPEED` fixo em 4 m/s |
| 7 | Sombra de contato + rim light quente separando do fundo | Personagem "colado" no fundo | falta rim/fill dedicado na camada 3 do runner e AO de contato |
| 8 | Tênis com sola, cadarço, solado EVA | Bloco escuro | sem detalhe de calçado nem textura |

> Observação de cena (fora do escopo do personagem, mas presente no print):
> névoa cinza cobrindo o fim do quarteirão, fachadas sem toldo/vitrine, moedas como
> esferas amarelas sem relevo "R$", céu sem nuvem, faixa de rua sem sinalização.
> Isso é o restante do trilho de cenário — tratado no item 6 (fase paralela).

### 1.3 Resposta direta à sua pergunta

Sim: **é mais barato construir um herói novo do zero do que corrigir o atual.**
O `build_humanos.py` gera geometria por revolução de anéis; ele não tem loops de
cotovelo/joelho/axila nem ilhas de UV utilizáveis. Qualquer textura aplicada nele
vai esticar. O caminho é um novo script de build dedicado
(`tools/blender/build_heroi_julia.py`) que produz **um** personagem de referência com
qualidade final — e, só depois de aprovado, vira base do elenco.

---

## 2. Estratégia

Um herói único e caprichado (`julia`), 100% original em Blender headless, com bake de
texturas PBR próprio. O elenco (20 perfis) é derivado depois por variação de mapas e
paleta, reaproveitando corpo, rig e clips — sem re-esculpir 20 vezes.

Ferramental já existente no repo que será reutilizado:
`tools/blender/run_bpy.sh`, `tools/blender/make_env.sh` (recria o venv `bpy==4.5.14`
com stubs X11/GL — hoje o sandbox está **sem** esse ambiente), `tools/blender/kit_base.py`,
`tools/audit_personagens.py`, `tools/audit_runner_rig.py`, `tools/captura_visual.gd`,
`tools/qa_full.py`.

---

## 3. Fases

### Fase 0 — Ambiente e baseline (0,5 dia) — ✅ CONCLUÍDA 26/09
- `sh tools/blender/make_env.sh` para reconstruir `venv-blender` + stubs.
- Capturar 3 shots do herói atual (frente, 3/4 correndo, close) como "antes".
- Congelar as métricas da tabela 1.1 em `docs/quality_baseline.json`.

**Gate 0:** `tools/blender/run_bpy.sh -c "import bpy"` responde e o "antes" está salvo.

### Fase 1 — Corpo base esculpido (2 dias) — ✅ CONCLUÍDA 26/09 (gate verde; ajuste braços/mãos: 39.104 tris, 1,720 m, 0 não-manifold)
- Novo `tools/blender/build_heroi_julia.py`: corpo em partes com **edge loops de
  deformação** (3 loops no cotovelo/joelho, 2 na axila/virilha), 7,5 cabeças, 1,72 m.
- Subdivision + shrinkwrap para suavizar, depois decimate controlado para o alvo de tris.
- Mãos com 5 dedos separados (3 falanges), pés com sola em 2 camadas.
- Rosto modelado: órbita ocular escavada, pálpebras, nariz com narina, lábios com volume.
- Alvos: **32k tris ±15%**, malha manifold, escala 1,72 m, frente −Y, pés em y ≈ +0,012.

**Gate 1:** `tools/audit_personagens.py` aprova tris/altura/manifold; render de turnaround
(frente/lado/costas) comparado com `docs/arte_alvo_final/6_model_sheet_heroi.png`.

### Fase 2 — UV + bake PBR (1,5 dia) — ✅ CONCLUÍDA 26/09 (gate verde; ajuste braços/mãos: 3 texturas, atlas 61,1%, GLB 1,74 MB)
- Smart UV project + costuras manuais; ilhas: rosto, corpo, cabelo, roupa, calçado.
- Bake em Cycles CPU (já usado no `render_ceu_nishita.py`): **albedo, normal, AO,
  roughness, metallic** → empacotar AO/Rough/Metal em um **ORM**.
- Pele: SSS 0.35 raio 1.2 mm, máscara de blush/oclusão, micro-normal de poro.
- Tecido: dobras esculpidas → normal map; costura e barra no albedo; número 10 e listras
  verdes direto na UV (sem decal em runtime).
- Resolução: **2048²** embarcado (mobile) + 4096² guardado em `tools/blender/out/` para captura.
- Empacotar como WebP/KTX conforme `tools/compress_assets_lote14.py`.

**Gate 2:** GLB com texturas `albedo`, `normal` e `ORM`, sem esticamento crítico de UV no checker, ≤ 1,8 MB com texturas.

> Atualização 26/09 — ajuste de braços/mãos: a cadeia do braço permaneceu reta e
> a mão foi reescrita com dedos contínuos, palma superelíptica e nós elipsoides.
> Ver `docs/execucao/HEROI_BRACOS_MAOS.md` e `docs/arte_alvo_final/12_bracos_maos_corrigidos.png`.

### Fase 3 — Cabelo e olhos (1 dia)
- Cabelo em **cards com alpha** (rabo de cavalo em 5 mechas + franja), material
  `alpha_scissor` (mobile-safe, sem ordenação por transparência).
- Olho: esclera + córnea separada com `refraction` barata, íris com normal radial.
- Sobrancelha e cílios como cards finos.

**Gate 3:** close a 2 m com rosto legível; sem shimmer de alpha em movimento a 60 FPS.

### Fase 4 — Rig e skinning (1,5 dia)
- Armature de **60 ossos**: contrato atual (`pelvis`, `spine_01..03`, `neck_01`, `Head`,
  `clavicle/upperarm/lowerarm/hand`, `thigh/calf/foot/ball`, 20 dedos) **+**
  `twist_upperarm_l/r`, `twist_thigh_l/r`, `eye_l/r`, `jaw`.
- Heat-map weights + correção manual em ombro, axila, joelho e quadril;
  máximo de 4 influências por vértice (limite do Godot mobile).
- Manter 100% de compatibilidade com `REGION_BONES` / `_library_drives_skeleton`
  de `scripts/runner_character.gd` — os nomes novos entram como opcionais.

**Gate 4:** `tools/audit_runner_rig.py` 100% match; sem colapso de volume em cotovelo a 120°.

### Fase 5 — Animações (2 dias)
- Reautorar os 6 clips e somar 4: `Sprint_Loop` (32f), `Idle_Loop` (72f com respiração),
  `Walk_Loop` (36f), `Jump_Loop` (24f), `Landing` (16f), `Crouch_Idle/Fwd`,
  **`Slide` (20f)**, **`Dash` (14f)**, **`Stumble` (18f)**, **`Board_Bus` (40f, Etapa 9)**.
- Curvas Bézier (não LINEAR), antifase de braços, pelve com bob vertical de 4 cm,
  rotação de tronco contrária ao passo, cabeça estabilizada.
- **Medir o deslocamento real do pé** e atualizar `LOCOMOTION_CLIP_SPEED` (hoje chutado
  em 4,0) para o valor bakeado → acaba o patinar.
- Blend tree no `runner_character.gd`: `Idle→Walk→Sprint` por velocidade, com
  `AnimationNodeBlendSpace1D` e cross-fade de 0,12 s nas trocas.

**Gate 5:** captura de 5 s a 18 m/s sem deslize de pé > 3 cm/ciclo.

### Fase 6 — Integração e iluminação do personagem (1 dia)
- Exportar `assets/characters/personagens/hero_julia.glb` (sem Draco — Godot 4 não lê).
- `runner_character.gd`: já prefere `hero_julia.glb` para `character_id == "julia"`;
  desligar `_apply_skin_tint` quando o modelo tiver textura de pele (senão a tinta
  achata o bake).
- Rim light + fill na `RUNNER_VISIBILITY_LAYER` calibrados para o novo albedo;
  sombra de contato (decal ou blob) sob os pés.
- LOD: LOD0 32k até 12 m, LOD1 12k até 30 m, LOD2 4k além (via `tools/plan_lod.py`).

**Gate 6:** 60 FPS estáveis no perfil Adreno 610 do `tools/qa_device_farm.py`;
`tools/qa_full.py` verde.

### Fase 7 — Elenco derivado (2 dias, depois da aprovação)
- Corpo/rig/clips compartilhados; variação por **conjunto de mapas** (4 tons de pele,
  6 penteados, 10 kits de roupa) e blendshapes leves de rosto/peso.
- Regenerar os 20 GLBs de `assets/characters/personagens/` pelo mesmo script.

---

## 4. Critérios de aceite do herói (checklist binário)

- [ ] 28k–45k tris, malha manifold, 1,70–1,75 m no runtime (AABB do esqueleto)
- [ ] ≥ 4 texturas embarcadas (albedo, normal, ORM, alpha do cabelo) em 2K
- [ ] Pele com SSS e variação de roughness — reprova se ficar plástica
- [ ] Rosto legível a 3 m na câmera de corrida
- [ ] Cabelo em cards com alpha, sem esfera sólida
- [ ] 60 ossos, 4 influências/vértice, `audit_runner_rig` 100%
- [ ] 10 clips com curva Bézier e contato de pé exato
- [ ] ≤ 2,0 MB por personagem; 60 FPS no perfil mobile-baixo
- [ ] Comparativo lado a lado com `1_gameplay_avenida.png` aprovado visualmente

---

## 5. Cronograma

| Fase | Dias | Acumulado |
| --- | --- | --- |
| 0 Ambiente/baseline | 0,5 | 0,5 |
| 1 Corpo | 2,0 | 2,5 |
| 2 UV + bake PBR | 1,5 | 4,0 |
| 3 Cabelo/olhos | 1,0 | 5,0 |
| 4 Rig/skin | 1,5 | 6,5 |
| 5 Animações | 2,0 | 8,5 |
| 6 Integração/luz/LOD | 1,0 | 9,5 |
| 7 Elenco derivado | 2,0 | 11,5 |

**Herói jogável no nível da arte-alvo: ~9,5 dias de execução.** Fases 1–6 entregam o
personagem; a 7 propaga para o elenco.

---

## 6. Trilho paralelo (cenário) — não bloqueia o herói

Do mesmo print: matar a névoa cinza do fim do quarteirão, toldos/vitrines nas fachadas,
moeda com relevo "R$" e emissão, sinalização da pista, nuvens no panorama e
saturação geral. Isso vive em `scripts/game_3d.gd` + `scripts/building_kit.gd` e pode
rodar em paralelo, porque não toca nos assets do personagem.

---

## 7. Riscos

| Risco | Mitigação |
| --- | --- |
| Ambiente `bpy` não reconstrói (sem PyPI) | `make_env.sh` é idempotente; alternativa é gerar o GLB por `tools/glb/glb_writer.py` sem Blender (perde o bake Cycles) |
| Bake Cycles CPU lento no sandbox | bakear em 1K durante iteração, 2K só no fechamento |
| Personagem pesado derruba o FPS | LOD obrigatório na Fase 6 + teto de 2 MB |
| Quebrar o contrato de animação | nomes de clip e ossos existentes são preservados; novos ossos são aditivos |
