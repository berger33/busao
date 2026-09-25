# Checklist do Lote 4 — clima (passo a passo)

Faça na ordem. Se algo der errado, pare e me mande o texto do painel **Saída**.

---

## 1. Instalar os 4 arquivos

| Do pacote | Para o projeto |
| --- | --- |
| `scripts/weather_system.gd` | pasta `scripts/` |
| `resources/weather_spec.json` | pasta `resources/` |
| `assets/textures/ceu/nuvens.png` | crie a pasta `assets/textures/ceu/` |
| `assets/audio/trovao.wav` | pasta `assets/audio/` |

## 2. Abrir o projeto no Godot 4.7.2

- Na primeira abertura ele importa a imagem e o som (leva alguns segundos).
- Se aparecer **erro vermelho** em algum arquivo, pare e me mande o texto.

## 3. Colar os 3 blocos no `game_3d.gd`

Siga `docs/PATCH_GAME_3D_LOTE4.md`: 1 constante, 1 variável, 3 funções e
3 chamadas (no `_ready`, no `_process` e na troca de capítulo).

## 4. Rodar (F5) e testar os climas

Para ver a chuva na hora, logo depois de `_setup_clima()` chame:

```gdscript
	_clima.set_state("tempestade")
```

Depois teste `chuva`, `nublado` e `limpo` (um por vez).

## 5. Conferir no painel Saída

```
[clima] sistema pronto | metodo=mobile | estados=limpo,nublado,chuva,tempestade
[clima] bases: sol=1.10 nevoa=0.50 ambiente=0.62 nuvens=0.30
[clima] estado=tempestade molhado_alvo=1.00 chuva=1150
```

## 6. Conferir o visual

- **chuva**: pingos finos descendo; asfalto escuro com brilho; poças nas pistas;
  céu carregado (cinza) e névoa maior;
- **tempestade**: piscadas rápidas de luz + véu branco por um instante e o som do
  trovão um pouco depois;
- **limpo** (depois de ~16 s): o chão seca devagar e volta ao normal.

## 7. Exportar para o Honor X8b

Exporte o APK como você já fez. No celular, olhe principalmente:

- se a chuva roda liso (a tempestade tem 1150 pingos — é o teto que eu calculei para o Adreno 610);
- se esquenta/trava (e em qual clima);
- se o trovão toca.

## 8. O que me mandar de volta

1. **Prints**: um de `chuva` e um de `tempestade` (PC ou celular);
2. Painel **Saída** com todas as linhas `[clima]`;
3. No celular: FPS aproximado em cada clima (ou "travou"/"esquentou").

Com isso eu fecho o **Lote 5** (física de verdade: personagem com colisão,
degrau na guia, atrito que muda no chão molhado — o clima já entrega o valor de
umidade pronto).
