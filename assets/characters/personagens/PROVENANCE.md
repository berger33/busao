# Manifest de Proveniência — Personagem principal (boneco v2)

Único corredor jogável do jogo por enquanto. Asset "revisão 2" (`corre_pro_ponto_personagem_v2.zip`, gerado no Blender 5.2.2 LTS via `criar_personagem_corre_pro_ponto.py`).
Malha humana rigged/skinned (25 ossos, 18.688 triângulos, 3 materiais, texturas 512×512) com 15 clipes de animação (idle, run_loop, jump_start/air/fall/land, crouch_enter/loop/run_loop/exit, lane_left/right + variantes *_motion) e rabo de cavalo com física de mola em runtime (`scripts/cabelo_fisico.gd` + `SpringBoneSimulator3D`).

Os demais personagens do catálogo (`scripts/character_data.gd`) continuam listados na loja como **INDISPONÍVEL** (sem asset dedicado): seus GLBs foram removidos e os pedestres de calçada usam o corpo humano base (`assets/characters/humanos_originais/Humano_M/F.glb`).

## Arquivos e Hashes SHA-256

4b24b0ba432d612b93284af50e70b6a4fff702e3d476e8996a3423e8e7d89430  personagem_v2.glb  (1815112 bytes)


> 2026-09-27: elenco reduzido a 1 personagem jogável (boneco v2). GLBs dedicados dos outros 20 corredores + hero_julia.glb removidos; catálogo mantém os metadados só para exibir os cards indisponíveis na loja.
