# assets/props/ — Mobiliário urbano 3D (Lote 7)

Modelos originais do projeto, criados por Blender headless 4.5 LTS
(`tools/blender/build_lote7.py`). Todos **CC0** (trabalho original).
Nenhum download em runtime.

## Contrato de drop-in

O jogo procura estes arquivos e usa o GLB no lugar da peça procedural
(`_optional_prop` em `game_3d.gd` e `_prop_glb` em `building_kit.gd`).
Se o arquivo faltar, o fallback procedural (que permanece no código)
é usado — nada quebra.

| Arquivo | Substitui | Medidas (larg × prof × alt) | Onde aparece |
|---|---|---|---|
| `cone.glb` | obstáculo `cone` | 0,55 × 0,55 × 0,93 m | obstáculo de calçada |
| `hidrante.glb` | `hydrant` (obstáculo + kit) | 0,73 × 0,46 × 0,93 m | calçada (bicos de latão, volante frontal) |
| `orelhao.glb` | `payphone` | 0,88 × 0,72 × 2,35 m | calçada (capuz laranja com abertura real, teclado, moedeiro, fone) |
| `banco.glb` | `bench` (obstáculo) + `_build_banco` (kit) | 1,70 × 0,57 × 0,96 m | praças/parques (ripas de madeira, pés de aço; no kit gira +90° para abrir para a rua) |
| `lixeira.glb` | `_build_prop_linear("lixeira")` (kit) | 0,39 × 0,53 × 1,04 m | calçadas do kit (tambor verde suspenso, placa de reciclagem) |
| `poste.glb` | `_build_lamp` | 1,21 × 0,20 × 3,59 m | postes de luz (braço +X, lente emissiva quente) |
| `ponto.glb` | abrigo do `_create_bus_stop` | 2,74 × 1,22 × 2,40 m | ponto final (colunas, teto com testa amarela, vidros, banco laranja) |
| `carrinho.glb` | carrinho do `vendor` | 1,70 × 1,15 × 2,13 m | camelô (tampo, vitrine, toldo listrado; o vendedor continua 3D skinned) |

## Convenções

- **Escala real** (metros) e **origem no chão** — não há `_fit_model` para
  props; o tamanho do GLB é o tamanho no jogo.
- **Frente/abertura para +Z** no espaço Godot (no Blender, a peça é
  modelada com a abertura para −Y; o export `yup` converte −Y → +Z).
  O corredor se aproxima vendo a face aberta.
- `ponto.glb` cobre só o **abrigo**: a placa `StopSign` continua
  procedural porque recebe skin/cor de `GameSave` (`placa`).
- Regenerar: `sh tools/blender/run_bpy.sh tools/blender/build_lote7.py`
  (ou `LD_LIBRARY_PATH=~/bpy_env/lib python3 tools/blender/build_lote7.py`).
  Previews em `tools/blender/out/lote7_*.png`.
