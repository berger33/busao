# Estruturas de cenário — `assets/scene/`

GLBs originais do projeto (Lotes 9A e 9B), modelados por Blender headless 4.5 LTS
via `tools/blender/build_lote9a.py`. Nenhum download em runtime.

## Contrato de drop-in

- **Origem no chão**, escala **real em metros** — o jogo instancia sem fit
  (só `position`, e `scale` uniforme em palmeira/árvore).
- **Frente -Z no Godot** (= +Y no Blender) onde houver frente.
- O builder procedural correspondente em `scripts/game_3d.gd` continua como
  **fallback** quando o GLB não existir.
- Exceção: os prédios escalam por instância — `predio2` tem corpo de 5,2 m e
  `predio3` de 7,8 m (ambos com 3,0 m de largura e 3,8 m de profundidade); o
  jogo aplica `scale = (width/3.0, height/5.2|7.8, 1.0)` para cobrir as
  alturas 4,6–10 m do `_build_profile_building` (corte em 6,5 m).

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
| `casa.glb` | `_build_house_facade` (não-empilhada) | 2,6×3,1×2,65 m + telhado de 2 águas; paredes `TintWall`, telhado `TintRoof` |
| `casa_favela.glb` | `_build_house_facade` (empilhada) | tijolo aparente + laje + vergalhões + toldo `TintAwning`; telhado `TintRoof` |
| `colonial.glb` | `_build_colonial_facade` | casa + esquadrias azuis + faixa `TintTrim` + cunhais claros |
| `predio2.glb` | `_build_profile_building` (h < 6,5) | 2 andares (corpo 5,2 m); coroa `TintTrim`; escala X/Y por instância |
| `predio3.glb` | `_build_profile_building` (h ≥ 6,5) | 3 andares (corpo 7,8 m); coroa `TintTrim`; escala X/Y por instância |
| `loja.glb` | `_build_shopfront` | vitrine + toldo `TintAwning` + placa `TintSign` com letreiro MERCEARIA |

## Materiais `Tint*` (cor da fase)

Peças que acompanham a cor `accent` do cenário usam materiais de albedo
**branco** com nome iniciado por `Tint`:

- `TintFabric` (tecido, roughness 0.64) — pano da bandeira, lona da barraca;
- `TintPaint` (tinta, roughness 0.38) — painéis do outdoor;
- `TintMetal` (metal 0.35, roughness 0.45) — portão.
- `TintWall` (roughness 0.95) — paredes de casas/prédios/loja;
- `TintRoof` (roughness 0.85) — telhados de casas;
- `TintTrim` (roughness 0.5) — faixa colonial, coroamento dos prédios, verso da placa;
- `TintAwning` (tecido, roughness 0.62) — toldos da favela e da loja;
- `TintSign` (roughness 0.4) — placa da loja; textura PIL branca com texto
  escuro, de modo que a cor da fase vira o fundo e o texto segue legível.

`_tint_glb()` em `game_3d.gd` duplica esses materiais por instância e aplica
a cor da fase via `set_surface_override_material` (não polui o cache);
aceita um `Color` ou um `Dictionary` {material: cor} para peças bicolores.
Nos previews de `tools/blender/out/lote9a_*.png` os `Tint*` aparecem com uma
cor-amostra mostarda só para a foto — o GLB sai de fábrica branco.
