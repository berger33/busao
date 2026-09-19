# Estruturas de cenário — `assets/scene/`

GLBs originais do projeto (Lote 9A), modelados por Blender headless 4.5 LTS
via `tools/blender/build_lote9a.py`. Nenhum download em runtime.

## Contrato de drop-in

- **Origem no chão**, escala **real em metros** — o jogo instancia sem fit
  (só `position`, e `scale` uniforme em palmeira/árvore).
- **Frente -Z no Godot** (= +Y no Blender) onde houver frente.
- O builder procedural correspondente em `scripts/game_3d.gd` continua como
  **fallback** quando o GLB não existir.

## Peças

| GLB | Builder | Notas |
|---|---|---|
| `palmeira.glb` | `_build_palm` | tronco 2,7 m com anéis, 6 folhas + flecha, 3 cocos; `scale` uniforme |
| `arvore.glb` | `_build_tree` | tronco 1,7 m + galhos + 4 copas achatadas; `scale` uniforme |
| `caixa_dagua.glb` | `_build_water_tank` | cavalete de 4 pés com travessas em X, bojo + tampa cônica; modelada para height 2.9 |
| `varal.glb` | `_build_clothesline` | 2 mastros + corda + 4 roupas coloridas com prendedores |
| `bandeira.glb` | `_build_flag` | mastro 2,7 m + pano ondulado; tecido em `TintFabric` |
| `outdoor.glb` | `_build_billboard` | poste + painel dupla-face com moldura; painel em `TintPaint` |
| `portao.glb` | `_build_gate` | 1,8×1,7 m, barras com lanças; todo em `TintMetal` |
| `barraca.glb` | `_build_market_stall` | balcão de ripas + toldo em `TintFabric` + vendedor + frutas |

## Materiais `Tint*` (cor da fase)

Peças que acompanham a cor `accent` do cenário usam materiais de albedo
**branco** com nome iniciado por `Tint`:

- `TintFabric` (tecido, roughness 0.64) — pano da bandeira, lona da barraca;
- `TintPaint` (tinta, roughness 0.38) — painéis do outdoor;
- `TintMetal` (metal 0.35, roughness 0.45) — portão.

`_tint_glb()` em `game_3d.gd` duplica esses materiais por instância e aplica
a cor da fase via `set_surface_override_material` (não polui o cache).
Nos previews de `tools/blender/out/lote9a_*.png` os `Tint*` aparecem com uma
cor-amostra mostarda só para a foto — o GLB sai de fábrica branco.
