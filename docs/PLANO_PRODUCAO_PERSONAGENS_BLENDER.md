# Plano de Produção — 20 Personagens no Blender (malha única)

**Fonte da verdade do progresso.** Se a conversa cair, retome por aqui: leia a tabela
de status, pegue o próximo personagem `⬜` na ordem e siga o checklist da seção 4.
Cada personagem concluído = 1 commit + push em `arena/01a0bfcf-busao`.

Relacionados: `docs/PLANO_PERSONAGENS_REALISTAS.md` (identidade/roupas de cada um),
`docs/ESTUDO_COMPARATIVO_FIDELIDADE_VISUAL.md` §4.1 (Fase 1 concluída — Júlia).

---

## 0. Estado atual (atualizar a cada commit)

| Data | Marco |
| :--- | :--- |
| 2026-09-20 | Fase 1: `julia.glb` com malha única (`build_corredora_fase1.py`). |
| 2026-09-20 | **Bug crítico corrigido:** todos os GLBs eram exportados com Draco; Godot 4 não decodifica → personagem invisível (só a sombra). Todos regenerados sem Draco. `audit_personagens.py` agora falha se Draco aparecer. |
| 2026-09-20 | Tráfego: rodas com pivô próprio, veículos mais rápidos que o jogador e car-following (sem atravessamento). |
| — | **Aguardando validação visual da Júlia pelo usuário no jogo** antes de produzir os demais. |

## 1. Decisão de arquitetura

**Reaproveitar a Júlia como base.** O `build_corredora_fase1.py` já resolve o difícil
(malha contínua, pesos suaves, tênis, UV atlas, 6 clipes, rig com 54 ossos). Os demais
personagens são **variações paramétricas** dessa base, não modelos do zero:

```
tools/blender/
├── build_corredora_fase1.py   ← base (vira biblioteca: corpo_lib)
├── personagens_lib.py         ← [Etapa A] funções reutilizáveis extraídas da base:
│     MeshBuilder, ring_z/ring_x, build_torso(params), build_pernas(params),
│     build_bracos(params), build_tenis/build_bota/build_sandalia,
│     build_cabeca(params), cabelos (curto, cacheado, coque, rabo, grisalho, careca),
│     acessórios (boné, capacete, chapéu, touca, lenço, mochila, bag térmica,
│     bolsa, avental, gravata, fone, faixa, colar, prancheta, garrafa, celular)
└── build_personagens_v2.py    ← [Etapa B] CATALOGO com 20 dicts de parâmetros;
      `-- <id>` gera um; `-- all` gera todos; valida e escreve PROVENANCE.
```

Parâmetros por personagem (o que muda entre eles):

| Grupo | Parâmetros |
| :--- | :--- |
| Corpo | `sexo`, `altura` (1.60–1.80), `ombro`, `quadril`, `busto`, `massa` (magro/atlético/parrudo/curvilínea), `idade` (postura: idosa = ombros caídos, leve cifose) |
| Cabeça | `pele`, `cabelo` (estilo + cor), `barba` (nenhuma/rala/cheia), `oculos` |
| Roupa | `top` (camiseta/regata/camisa social/moletom/colete/jaqueta/blusa/vestido/farda/avental), `mangas` (curta/longa/sem), `baixo` (legging/calça/jeans/bermuda/saia/calção), `calçado` (tênis/bota/sandália/chuteira/sapatilha/sapato) |
| Adereços | lista de `(nome, osso, offset)` |
| Cores | `shirt/pants/shoes/hair/skin/accent` — já existem no `CATALOG` de `build_personagens.py` (manter nomes de material `Camisa/Calca/Sapato/Hair/QuaterniusSkin` para o tintador do Godot) |

## 2. Ordem de produção e status

Ordem por impacto no jogo (padrão equipado → primeiros desbloqueios → resto).

| # | id | Nome | Base | Peças novas necessárias | Status |
| :-: | :--- | :--- | :---: | :--- | :---: |
| 1 | `julia` | Júlia Atleta | F | — (é a base) | ✅ modelada · ⏳ validar no jogo |
| 2 | `ze` | Zé Atrasado | M | corpo M, cabelo crespo curto, camiseta, jeans, mochila tiracolo | ⬜ |
| 3 | `maria` | Maria do Bairro | F | corpo curvilíneo, cacheado curto, blusa, saia, sandália, bolsa | ⬜ |
| 4 | `motoboy` | Rafa Motoboy | M | corpo forte, barba rala, colete refletivo, cargo, capacete+viseira, bag térmica | ⬜ |
| 5 | `nilo` | Nilo Padeiro | M | avental, touca, bandeja com pães (hand_l) | ⬜ |
| 6 | `cida` | Motorista Cida | F | farda, quepe com viseira, crachá | ⬜ |
| 7 | `bia` | Bia Estudante | F | corpo 1.62, camisa branca, jeans, mochila escolar | ⬜ |
| 8 | `luan` | Luan do Skate | M | moletom oversized, bermuda, boné aba reta virado, tênis cano médio | ⬜ |
| 9 | `joao` | João Gamer | M | jaqueta com zíper, fone (torus em Head) | ⬜ |
| 10 | `carlos` | Carlos da Obra | M | corpo parrudo, barba cheia, capacete com aba, colete com bolsos, bota bico aço | ⬜ |
| 11 | `camila` | Camila do Negócio | F | cabelo liso longo, macacão, sapatilha, tablet (hand_l) | ⬜ |
| 12 | `influencer` | Nina Creator | F | top, shorts jeans, botas, celular (hand_r), pulseira | ⬜ |
| 13 | `chico` | Chico Carteiro | M | boné azul, camisa uniforme, sacola amarela (pelvis) | ⬜ |
| 14 | `tiao` | Tião Vaqueiro | M | chapéu de couro aba 0.30, gibão, bota | ⬜ |
| 15 | `beto` | Beto Praiano | M | cabelo loiro, regata, bermuda, colar de contas, pulseira | ⬜ |
| 16 | `professor` | Professor Everaldo | M | grisalho, camisa social manga longa, gravata, livro (hand_l) | ⬜ |
| 17 | `marta` | Dona Marta | F | bandana, avental verde, blusa | ⬜ |
| 18 | `zilda` | Vovó Zilda | F | corpo 1.60 + postura idosa, cabelo branco, vestido florido, lenço, bolsa de mercado | ⬜ |
| 19 | `clara` | Enfermeira Clara | F | uniforme branco, gorro, prancheta (hand_l), crachá | ⬜ |
| 20 | `deise` | Deise Craque | F | camisa 10, calção, chuteira (travas), faixa de capitã (upperarm_l) | ⬜ |

Legenda: ⬜ a fazer · 🔧 em produção · ✅ GLB gerado e auditado · 🎯 validado pelo usuário no jogo.

## 3. Etapas macro

- [ ] **Etapa A — Biblioteca** `personagens_lib.py`: extrair a base da Júlia em funções
  paramétricas; provar que `build_personagens_v2.py -- julia` reproduz a Júlia byte-a-byte
  em geometria (mesma contagem de vértices, mesmo z_min = 0, mesma auditoria de pesos).
- [ ] **Etapa B — Corpo masculino** (`ze`): ombro 0.50, quadril 0.36, sem busto, mandíbula
  mais larga; valida `Humano_M` implícito. Primeiro commit da série.
- [ ] **Etapa C — Lote 1** (`maria`, `motoboy`, `nilo`, `cida`): cobre corpo curvilíneo,
  corpo forte, adereços em `Head/spine_02/hand_l/pelvis`.
- [ ] **Etapa D — Lote 2** (`bia`…`influencer`): roupas variadas (moletom, jaqueta, macacão).
- [ ] **Etapa E — Lote 3** (`chico`…`deise`): chapéus, postura idosa, chuteira.
- [ ] **Etapa F — Polimento**: screenshots `store/screenshots` com 3 personagens por faixa,
  atualizar `docs/PLANO_PERSONAGENS_REALISTAS.md` §4 e `CREDITS.md`.

## 4. Checklist por personagem (não pular)

1. `sh tools/blender/make_env.sh` se `/home/user/venv-blender` não existir (o ambiente
   fica fora do repo e some entre sessões; leva ~30 s).
2. Editar/adicionar o dict do personagem em `build_personagens_v2.py`.
3. `sh tools/blender/run_bpy.sh tools/blender/build_personagens_v2.py -- <id>`
   - saída obrigatória: `contato com o solo: z_min = 0.0000`, `pesagem suave no joelho: N/N`,
     `UV OK`, `Export OK`, **sem** `KHR_draco_mesh_compression`.
4. `CORREDORA_PREVIEW=1 …` (ou flag equivalente) e **olhar** os PNGs `frente34`, `costas`,
   `sprint_costas34` — é a visão do jogo. Corrigir interpenetrações/roupa flutuando.
5. `python3 tools/audit_personagens.py` → `AUDIT OK`.
6. Atualizar hash em `assets/characters/personagens/PROVENANCE.md` e o status na tabela
   da seção 2 deste arquivo.
7. `python3 tools/validate_project.py` → `PRE-FLIGHT OK`.
8. `git add -A && git commit -m "feat(personagens): <id> em malha única" && git push origin arena/01a0bfcf-busao`.

## 5. Regras técnicas fixas (aprendidas — não repetir erros)

- **Nunca** exportar com Draco (`export_draco_mesh_compression_enable=False`). Godot 4 importa
  o GLB sem geometria → só a sombra aparece.
- Cada clipe deve chavear **todos** os ossos principais em cada frame (`clear_pose(arm, f)`);
  senão o clipe herda a pose do anterior (pé a 4 cm do chão no Idle).
- Nomes fixos: ossos do rig `runner_character.gd` (+ `Hair_Ponytail_*` opcionais);
  materiais `QuaterniusSkin/Camisa/Calca/Sapato/Hair` (tintáveis) — os demais
  (`Entressola/Sola/Meia/Cadarco/Ilhos/Elastico/OlhoBranco/OlhoIris` + novos como
  `Metal/Couro/Refletivo`) não são tintados e preservam a leitura do personagem.
- `MODEL_SCALE 1.03` no Godot → modelar em 1.77 m (M) / 1.72 m (F, Júlia) e variar altura
  por personagem dentro de ±0.10 m.
- Limite: < 1,2 MB e < 8k vértices por GLB (sem Draco a Júlia tem 553 KB / 4,4k vértices).
- Frente do corpo = −Y no Blender (export `yup` → −Z no Godot).

## 6. Como validar a Júlia no jogo (pendência atual)

1. Save limpo (ou loja → equipar Júlia Atleta). Ela deve aparecer com camiseta coral,
   legging preta, tênis brancos com sola preta, rabo de cavalo balançando no sprint.
2. Se ainda estiver invisível: `godot --headless --check` + verificar que o `.import` de
   `julia.glb` foi regenerado (apagar `.godot/imported/julia*` força reimport).
3. Feedback esperado do usuário para seguir: proporções, cor, tamanho do tênis, cabelo.
