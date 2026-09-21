# Checklist do Lote 3 — a rua da imagem (passo a passo)

Faça na ordem. Se algo der errado, pare e me mande o texto do painel **Saída**.

---

## 1. Instalar os 2 arquivos novos

Do pacote do Lote 3, copie para o projeto (aberto no seu computador):

| Do pacote | Para o projeto |
| --- | --- |
| `scripts/building_kit.gd` | pasta `scripts/` |
| `resources/world_spec.json` | pasta `resources/` (crie se não existir) |

> `building_kit.gd` é o "construtor" da rua. `world_spec.json` é a planta com
> todas as medidas — é ele que manda no resultado, então dá para ajustar
> largura de faixa, altura de prédio etc. sem mexer em código.

## 2. Abrir o projeto no Godot 4.7.2

- Se aparecer **erro vermelho** no `building_kit.gd`, pare aqui e me mande o texto.
- Se o Godot perguntar sobre reimportar/atualizar arquivos, aceite.

## 3. Colar os 4 blocos no `game_3d.gd`

Siga o arquivo **`docs/PATCH_GAME_3D_LOTE3.md`** (está no pacote).
Ele mostra exatamente onde colar cada bloco:

1. **constantes** no topo;
2. **variáveis** junto das outras;
3. **três funções** junto das outras funções;
4. **três chamadas**: no fim do `_ready()`, dentro do `_process(delta)` e quando
   troca de capítulo.

## 4. (Recomendado) desligar o cenário antigo

Se o cenário antigo ficar por cima da rua nova, faça a função antiga
(`_build_track()` ou parecida) retornar logo no começo:

```gdscript
func _build_track() -> void:
	return  # Lote 3: a rua agora vem do building_kit
```

## 5. Rodar (F5) e conferir

Você deve ver: faixa central de lajes com folhas → guias com postes →
pistas escuras com linha amarela dupla → calçadas com árvores e esferas
verdes → prédios de 2-3 andares (tijolo, reboco, alguma loja com toldo) →
horizonte lavado pela névoa.

No painel **Saída** deve aparecer algo assim:

```
[world] quarteirao 0: 29.9 m, 214 malhas (6 multimesh)
[world] quarteirao 1: 28.2 m, 209 malhas (6 multimesh)
...
```

> A contagem muda de quarteirão para quarteirão (são sorteados com a mesma
> semente sempre, então o mesmo quarteirão sai sempre igual).

## 6. Ajustes rápidos (se precisar)

| Sintoma | Ajuste em `game_3d.gd` |
| --- | --- |
| Personagem afundado/flutuando | `WORLD_Y_OFFSET` (0.05 em 0.05) |
| Rua correndo ao contrário | `WORLD_INVERTER = true` |
| Rua muito larga/estreita | `resources/world_spec.json` → `faixas` |
| Prédios altos/baixos demais | `world_spec.json` → `predios.pisos` (hoje 2 a 3) |
| Sem textura (tudo cinza) | falta o Lote 1: `assets/textures/pbr/` |

## 7. Exportar para o Honor X8b (quando o PC estiver bom)

Android → Exportar APK, como você já fez antes. No celular, confira:

- a rua aparece correta;
- anote se **trava** ou **esquenta**;
- mande o print e o painel Saída (linhas `[world]`, `[render]`, `[medicao]`).

---

## 8. O que me mandar de volta

1. **Print** da tela (de preferência no celular, ou F5 no PC);
2. Texto do painel **Saída** (Output) — copie tudo que tiver `[world]`,
   `[render]` e `[medicao]`;
3. Se algo ficou estranho: o que e onde (ex.: "os postes estão dentro da pista").

Com isso eu ajusto o **Lote 4** (clima, chuva, asfalto molhado e reflexos).
