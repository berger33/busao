# Manifest de Proveniência — Personagens Dedicados (20 GLBs)

Gerados proceduralmente pelo Blender 4.5 via `tools/blender/build_personagens.py` (julia.glb: `tools/blender/build_corredora_fase1.py`, Fase 1).
Cada arquivo contém malha humana 3D anatômica e orgânica contínua com UV unwrapped em anéis de quads, paleta PBR, tênis esportivos moldados com entressola EVA, esqueleto de 52 ossos e 6 animações biomecânicas completas.

## Arquivos e Hashes SHA-256

20f88cd6a31721c2d690d19bd5cf87e964625aa9c128057681acf62574eb3a20  beto.glb  (373068 bytes)
ca73326effc857de4018bbe675c4f7c0301a166826b8f69894068ee6519bd642  bia.glb  (390024 bytes)
8048d22b71d56cb0d0e9055c33043f0a9b0c984bb12b709ceb7deaca947768d1  camila.glb  (387024 bytes)
2f292cb6bc2bc88f5a9bd97117a30e5d41cf346e6d0e4764d0bb062b2e1f60a8  carlos.glb  (394796 bytes)
55f8ea9bfd70f5b64ba4dcb1e484a0efe5b2892d028613b9ba568331d5e3f18f  chico.glb  (383068 bytes)
b292c54640b2e17a68a41bf1d24d7761a0260c1800b6c2d60077ff433ecedfcc  cida.glb  (387024 bytes)
86dd1e90f6f42f95d6027bc47fdadad19a6bcf1a040d0d7c33e5ed32319fbeff  clara.glb  (387020 bytes)
45b378b0d0fb616f1d1ed187c4261a03f4dc0be02514157d5c3a3b3e4ead7222  deise.glb  (387024 bytes)
640759895c3a7fcd36226a2a16e53e325f6d2006ce5f6da91f239f30f4a59f49  influencer.glb  (387036 bytes)
663f5c2fd7a8be0ed14e0c0c9ff2bd4da2bfec2f89df88b597c709cf60ddda02  joao.glb  (373072 bytes)
3753a14eb81df0bee2a84a2ba75e48c41f37855409aebb9a7e205bcc8e821a49  julia.glb  (531180 bytes)
be476777bda71e867f4cb29791b8020ec064d145b9fa381dbdce2a72c8a788cb  luan.glb  (373072 bytes)
1cb4b49bbe74ce4fed18e8051b7e25015e51a775963aa3354b01ee1a6aac06b6  maria.glb  (387024 bytes)
b7232a737763e0ccaed4c0afaebb2b548565ae439b7eb813ee49ea073b7045eb  marta.glb  (387020 bytes)
269978fc8b5346849b037076e4b2747c94b3628811befb41bcb2a400800bf759  motoboy.glb  (396588 bytes)
447cd5e3b06f842cfea5513ca11fa57bf88ba5eb345367bc685e280d8bac59b1  nilo.glb  (373068 bytes)
659d9e65191c40faeb2e42190f4b633da0883831c8bcfe6a293716d6427548a5  professor.glb  (373088 bytes)
172d7e104efa7a68dd172153ad059ad7ce42eff26f4e0cc73c57367fb60e213c  tiao.glb  (380060 bytes)
381b8ae3bebcc9f7abfd119115237ffde9719e0ef48ebe300a0c4295869ea30a  ze.glb  (373068 bytes)
f42256d257a09cebce2eae0b3fe1a7d7be6adfcd2e76ecd6555f3bbeb639044d  zilda.glb  (387024 bytes)


> 2026-09-20: todos regenerados **sem** Draco (`export_draco_mesh_compression_enable=False`). Godot 4 não decodifica `KHR_draco_mesh_compression` — os GLBs anteriores importavam sem geometria (personagem invisível, só a sombra).
