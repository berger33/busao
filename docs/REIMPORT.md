# Reimport limpo — obrigatório após este lote

Os `.import` de textura foram corrigidos (bloco `metadata` com a chave
inexistente `vram_texture` fazia o Godot recusar **todas** as texturas).
O cache `.godot/` da sua máquina ainda tem os imports falhos — é preciso
limpar uma vez:

1. Feche o Godot (editor e jogo).
2. Apague a pasta `.godot/` na raiz do projeto (é cache — será recriada).
3. Abra o projeto no Godot 4.x e **aguarde o reimport terminar**
   (barra de progresso no canto inferior; ~540 arquivos).
4. Rode com F5.

## Por quê

- `Unexpected identifier 'vram_texture'` → `.import` antigo; corrigido no repo.
- `Failed loading resource: .../julia.glb` → o arquivo foi validado byte a
  byte (contêiner GLB + accessors + skin + animações, tudo íntegro) e o
  `.import` dele está correto; falha local = cache/uid obsoleto no `.godot/`
  — o reimport limpo resolve. O jogo ainda tem fallback (se o GLB falhar,
  usa o corpo original `Humano_F`), então uma falha isolada nunca trava a run.
- Nunca commite a pasta `.godot/` (já está no `.gitignore`).
