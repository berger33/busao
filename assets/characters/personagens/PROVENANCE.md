# Proveniência — Personagens Dedicados (Lote 28)

20 corredores 100% originais, modelados do zero no **Blender 4.5 LTS headless** via `tools/blender/build_personagens.py` (fork de `build_humanos.py`). Cada GLB compartilha esqueleto `runner_character.gd` (26 bones + 20 dedos) mas tem paleta `character_data.gd` exata, proporções M/F com variação, cabelo/barba e acessórios baked weighted (mochila, capacete, bag, boné, fone, etc). Substitui o tint puro por **PBR runtime** (`_apply_profile_palette` + `_apply_skin_tint` com `pele_realista`/`tecido`/`jeans`/`borracha`).

## Geração

- **Script:** `tools/blender/build_personagens.py` — `pilar_z seg24 + bevel 0.012 + shade_smooth + SUBSURF 1 + join_parts + skin 1.0 + 6 actions Linear (Idle 48f, Walk 24f, Sprint 16f, Jump 10f, Crouch_Idle 48f, Crouch_Fwd 20f)`.
- **Comando:** `sh tools/blender/run_bpy.sh tools/blender/build_personagens.py` (ou `ze motoboy ...`)
- **Saída Draco:** `assets/characters/personagens/<id>.glb` com `export_draco_mesh_compression_enable=True, level=6, pos=14/norm=10/tc=12` (extensão `KHR_draco_mesh_compression`). Antes Draco 346-398 KB, depois Draco **203-212 KB** (4.03 MB total vs 7.16 MB, ratio ~7×) — mantém `skins/animations` e `JOINTS_0/WEIGHTS_0`, `export_yup=True`, `export_materials='EXPORT'`.
- **Materiais:** `QuaterniusSkin, Hair, Camisa, Calca, Sapato, OlhoBranco, OlhoIris, Accent` — nomes preservados para tint PBR runtime. Texturas 4K (`pele_realista`, `tecido_realista`, `jeans_realista`, `borracha_realista`) são aplicadas no GDScript (`normal_scale 0.34-0.60`, `uv1_scale 2.2-3.0`), não bakeadas, mantendo GLB leve.
- **Loader:** `runner_character.gd: PERSONAGENS_ROOT + is_personalized` prioriza `personagens/<id>.glb` antes de `Humanos_M/F`; evita duplicar props (`_attach_*` só se `not is_personalized`).
- **Validação:** `tools/audit_personagens.py` checa `<500KB` (agora `<300KB` com Draco), `skins=1 anims=6 JOINTS_0`, `PRE-FLIGHT OK`; `store/screenshots/09_20_corredores_1080x1920.png` + `10_elenco_brasil_1080x1920.png` comprovam 3 faixas e `ResourceLoader.exists true 20/20`.
- **Licença:** Trabalho original do projeto Corre pro Ponto, CC0 próprio, sem CC0 de terceiros.

## Manifesto SHA-256

```text
90c1b25712dfed6a638d5ade7a30c547ce4c5df4174aa6cc0fbb46e9934a0230  beto.glb  (208060 bytes)
2a09fcab2b1a02b371a30dc69c8e683e3e2565a4d6bfa6ad117bfba60e3c36d3  bia.glb  (211132 bytes)
8b4419e010d0b657645d080bfa8502a7f5dd2e6b3decf1f31b82023d48b2dc96  camila.glb  (211116 bytes)
67e9654b5309c211091910725104ccc80d31167bca130117e281165cda595f99  carlos.glb  (213412 bytes)
61fee96ed311d80354054626b71bc5a33e274654350905640b21e4097e5ff834  chico.glb  (212856 bytes)
f61d84fbe6f26617149ff71474bee6254ebc1ace4501a3bb71670a85f2179f6d  cida.glb  (213216 bytes)
5ff966a363343f34944f214a47726f506ef9c06f66329f4ef691cce4a30f0b8f  clara.glb  (213188 bytes)
91bcae39d9e928696b1478bb7cef4f1019efc2b926bafd559e2487504bcbd5b1  deise.glb  (209524 bytes)
85d87393178523c3acb56dab81c27a0cd0b5b0357b50c9ee7271be25dc13fb84  influencer.glb  (214584 bytes)
e753bc3dabe37dc34a89be4850abc723bf0205fb47984920c26ec9853e0fd4c5  joao.glb  (211132 bytes)
85a01a91eb2755a5afccd4727f438fd80fa4d049bdbca165fb185093a5676e6d  julia.glb  (209496 bytes)
fd39c4a93deb5598e4d484f469f30b3bd61b8c55632361d47b531abf6cd95939  luan.glb  (210308 bytes)
b619b80d175568f349a486996f87ad501507a852ad4769661845b977ad2b6dab  maria.glb  (210644 bytes)
d50101a8899812ed2dbf9267ea57c6b71b4ec4f82d6210fcefe76f9bdb111a27  marta.glb  (208436 bytes)
dc58a741cda161c3a9a853c28c17815eecfc717948b034dc88f94359ea746235  motoboy.glb  (216732 bytes)
df789e7341b1c8e4fdd9ffd9e080c6eaf57c4d808ba8fa74c9d93d9296311900  nilo.glb  (215444 bytes)
bac087c8fac58455eeb9a21c53beda3f37901bee7c4c7cfd83d718853ccd9388  professor.glb  (210836 bytes)
69f4a3bf39f979c48647e5628fd280437b1a589a822d81bbff24cc8af1532bbf  tiao.glb  (211660 bytes)
dcf943f0f088a1c248cbc54b71a34571c953f632f0bd2638821fe58415851cbe  ze.glb  (208884 bytes)
56d42455532f5470835c27ce22ff8fcd6d8cd321ef3ec78cc3a860b657691f42  zilda.glb  (208456 bytes)
```
