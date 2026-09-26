# `assets/characters/source/` — berço de assets-fonte (fora do runtime)

Arquivos daqui **não são carregados pelo jogo**: são fonte/Work-In-Progress que
ainda não cumpriram o contrato de runtime dos personagens
(`assets/characters/personagens/`, teto de **500 KB** por GLB, sem Draco —
o Godot 4 não decodifica `KHR_draco_mesh_compression`).

## Ginger (`ginger+woman.glb`, `Ginger+Woman.blend`)

| Item | Estado |
| --- | --- |
| `Ginger+Woman.blend` | fonte via Git LFS (37,9 MB) |
| `ginger+woman.glb` | export rigged: 1,88 MB, 7 malhas, 1 skin, **7 clipes** (`Idle_Loop`, `Walk_Loop`, `Sprint_Loop`, `Jump_Loop`, `Crouch_Idle_Loop`, `Crouch_Fwd_Loop`, `Landing`) com 177 canais cada |
| Contrato de runtime | **não cumprido** — 1,88 MB > 500 KB |

O peso está nas animações, não na malha: ~453 KB de rotações (VEC4 float32) +
~317 KB de índices de keyframe + 228 KB de JSON (1.239 canais). Para voltar ao
runtime é preciso re-bakear com menos canais/keys, por exemplo:

```bash
blender --background --python tools/blender/bake_ginger_deform.py   # re-bake do deform
blender --background --python tools/blender/animate_ginger.py        # clipes
python3 tools/validate_ginger.py                                     # contrato dos 7 clipes
```

Depois: mover o GLB para `assets/characters/personagens/`, readicionar a entrada
no catálogo (`scripts/character_data.gd`, que hoje fecha em 20 personagens —
10 M e 10 F, como cobra `tools/validate_project.py`), atualizar a expectativa do
validador para 21, rodar `python3 tools/rebaseline_provenance.py` e os portões.

**Histórico:** a Ginger entrou no catálogo em `61a2640` e o commit `f9ddf1a`
("Make Ginger sole character") reduziu temporariamente o elenco a ela
(`CharacterData.all()` filtrada + `inventory = ["ginger"]` na sanitização do
save). Esse modo foi **revertido** na promoção para a `main` porque quebrava o
contrato de 20 personagens, derrubava a loja/elenco para 1 opção e sobrescrevia
o save do jogador. O encadeamento dos hooks (`runner_character.gd`,
`tools/validate_ginger.py`) foi preservado para o trabalho continuar.
