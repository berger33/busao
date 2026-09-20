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
d42220f96ed8af65ec2469c3a95aff10ee24fd8a2790e46cea5d3371ae99e756  beto.glb  (220208 bytes)
243152afc3b89454b039e8463a25f8075142d878fcaf2fdda6edc7e11219506b  bia.glb  (223148 bytes)
d2c2b96f4bb8d844afa4cbdb1435b6e903c9f56e3f61b0fecdcd9ff6328e76a3  camila.glb  (223436 bytes)
de09aa30ee31b7ae77f31c13eaf4aa9f718fc10ebc37408de3ffa29fca026b43  carlos.glb  (225640 bytes)
c3d67d15260ef6e6e6dfe66b231ee6201de6ed4eb9b45cde456f000ac7ef230c  chico.glb  (225116 bytes)
c40d6bc7b706eb21c75360e9b2f950cd8e32e1e90b25ab4943734f7869647fe9  cida.glb  (225420 bytes)
f56b1ba03d7f711c47b219391d1073d78093f6d571e4acce66c88e07e99741ac  clara.glb  (225388 bytes)
55abc49f13e54584aef477eb3a6d8214c890ab8bd005cb2030257fb12587540a  deise.glb  (221584 bytes)
f500aca3e04b9fff981f2376e21fdef11b5ac05ba90eba27a20531790807615b  influencer.glb  (226820 bytes)
873396925a600e268b13cdca573194c92b9f6d3dd77df7bf2b7787325bad6305  joao.glb  (223408 bytes)
fef9aa4507cc1189bfca2378be72d674b35ac96d20d7b3a59478b4abeea67649  julia.glb  (221796 bytes)
8be106d2f7bc35dd10fd5e398274de10180be8080b9e5a27f367dd2b42c152ee  luan.glb  (222412 bytes)
e8d140fbb37f7503ebb8d0b6efb4fcf5b72d58d8021de01f0af9d712b4e2d5f8  maria.glb  (222748 bytes)
c8d8513102e401a29aa00b0fc2912e42db4cd61aaeea048c94ea2285fdea9cde  marta.glb  (220536 bytes)
c3ab1b2f0d8a976c03e1e609ae0a265bc0b4a99f7f334c42de5a19b0338ff7f3  motoboy.glb  (229128 bytes)
385a17246511f8240ed0bc419cc6dd52e3246226b3c1f817d393e54e4a7bba1c  nilo.glb  (227696 bytes)
55efb8c6e086569d1c2e7cfd26032db8a48f6d158f1a9159661584d5563e1e82  professor.glb  (223116 bytes)
38ed1b4eecd5dcbad3c21af3893cabe8b80ae3f57c08bc94e08f22fde407118d  tiao.glb  (223912 bytes)
d2f5073f0d365126c49e331d2839108e49a89e9477ad4fa8fb9d0253b85fc0d2  ze.glb  (221484 bytes)
fea0589b66c12be4fcfffbe5d6fcaad81e81bbe448278c184b767cc113d0fcdd  zilda.glb  (220392 bytes)
```
