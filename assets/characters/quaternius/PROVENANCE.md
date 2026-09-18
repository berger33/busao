# Proveniência do personagem humano principal

Este diretório substitui o personagem procedural pelo humanoide 3D rigged/skinned do **Universal Base Characters**, de Quaternius, vestido com o conjunto modular **Peasant**. O corpo, cabelo, olhos e roupas são meshes reais com UVs, mapas de cor, normal e roughness/ORM; não são cápsulas do gameplay.

## Licença e origem

- **Autor:** Quaternius.
- **Pacote-base oficial:** [Universal Base Characters](https://quaternius.itch.io/universal-base-characters). A página oficial informa 6 modelos humanoides game-ready, rig humanoide, compatibilidade com retargeting e licença **CC0 1.0 Universal**.
- **Pacote de roupa oficial:** [Modular Character Outfits — Fantasy](https://quaternius.com/packs/modularcharacteroutfitsfantasy.html). A página oficial informa partes modulares rigged, texturizadas, compatíveis com o Universal Base Characters e licença **CC0 1.0 Universal**. O conjunto Peasant foi escolhido por ter camisa/colete, calça, mangas e calçados separados; o tema visual é estilizado e não representa uma profissão ou comunidade brasileira.
- **Animações:** [Universal Animation Library](https://quaternius.itch.io/universal-animation-library). A página oficial informa animações humanoides para Godot/Unity/Unreal, incluindo locomoção, sprint e salto, e licença **CC0 1.0 Universal**.
- **Texto da licença:** `QUATERNIUS-LICENSE.txt` foi preservado junto do asset-base.
- **Licença legal:** [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/). O código do jogo continua sob a licença/proveniência do projeto; a dedicação CC0 do asset é independente.

## Preparação e integração

- O corpo masculino e feminino, as partes de roupa, binários e texturas foram copiados para o repositório em 18/09/2026 a partir do mirror público `alesousz/teste`, commit `5e1af485ddd7aa05ddd624ebdfcc336a6c1b43b4`, que referencia as páginas oficiais acima.
- A `UAL1_Standard.res` é uma `AnimationLibrary` Godot derivada da versão Standard da Universal Animation Library e fica como cache compacto offline. Como ela não contém todos os clips de locomoção, `UAL1_Standard.glb` também foi incluído como fonte Godot-compatible; `scripts/runner_character.gd` extrai dele a biblioteca completa quando necessário e usa `Idle_Loop`, `Walk_Loop`, `Sprint_Loop`, `Jump_Loop`, `Crouch_Idle_Loop` e `Crouch_Fwd_Loop` no runner. O recurso `.res` foi obtido do extrator público do projeto `shellybotmoyer/stargate-universe`, commit `84e7b1add6e2895eed8eb7f91c2392fa264ddd98`; o GLB Standard veio do mirror público `alesousz/teste`, commit `5e1af485ddd7aa05ddd624ebdfcc336a6c1b43b4`. Ambos estão versionados para que o jogo não dependa de download em runtime.
- A integração monta o corpo base, divide a malha de pele por regiões quando necessário e anexa meshes de roupa skinned ao mesmo esqueleto. O controlador `scripts/runner_character.gd` seleciona os clips por estado de corrida, salto e agachamento; só cria um fallback simples se a importação do asset principal falhar.
- A arte é estilizada/game-ready, não fotorealista. A escolha mantém leitura arcade, custo de render compatível com Android e materiais PBR mais completos do que o boneco procedural anterior.
## Manifesto SHA-256

Os hashes abaixo ajudam a detectar alterações acidentais no asset importado. O próprio `PROVENANCE.md` fica fora do bloco para evitar uma referência circular; o manifesto cobre os demais arquivos deste diretório.

```text
c232257c8a2545520aa120cda96acb23d00a355d2e3339cba20b7ebf56f28a09  QUATERNIUS-LICENSE.txt  (782 bytes)
69591853d817488edaa8fd9bf8fc1d821eaeaf789f8627b3cd23b41c4ed67997  animation/UAL1_Standard.glb  (7618436 bytes)
7d5eac97cb4a6294c90db76da0ed4a4c4aa5bc31f5b9c1df908349f5f25f58e6  animation/UAL1_Standard.res  (2647188 bytes)
3a8220a485b33d05d879115a50697728b45a151781106033afb8b8c243fca208  base/Superhero_Female_FullBody.bin  (990808 bytes)
215f2af81ad91eecfcee807bad19b541704b800844d997286b78d5dbed7a3b5e  base/Superhero_Female_FullBody.gltf  (31652 bytes)
459003f9745853ae562a85506a2b94dd56515c1f37728f9fa3d2ce1a3e4cd92f  base/Superhero_Male_FullBody.bin  (720076 bytes)
e2a68c400eedbaed172fc0f2de8e665df66ceccab27fcbcf2152682322405ce4  base/Superhero_Male_FullBody.gltf  (30981 bytes)
d08e3356a83211bc6ca21fe3a8e39f4b5c1a3b8f85457fc2c0fb57be09935025  base/T_Eye_Brown.png  (35958 bytes)
9ed61f7726a54fe346a78b9e5a18905d8e2b88f86235d97f53cd207a26f3f8c7  base/T_Eye_Normal.png  (15099 bytes)
bc7aa863bd22ab0a995cd838cceb4d3a5186ee54ee2fb0108fad85d20c057e6e  base/T_Hair_1_BaseColor.png  (1570376 bytes)
57fd0ad8c96a4d01b38769637e066cecaa285b456f6e48ce00863754a457affb  base/T_Hair_1_Normal.png  (4326126 bytes)
f9f4f2fb3eeeefb0b6f0fdef38b0770fd6607640c1c680b8139dd76697e9f9b3  base/T_Hair_2_BaseColor.png  (1729467 bytes)
172f230aae0d4366c3cfc0402b2e6d1811b11f8487344bff28605eeacac1558d  base/T_Hair_2_Normal.png  (4710013 bytes)
d366843ee7d9e9f37ec87a0e1c98c7f2e45573c08eeb80a51a6d9344e68cf288  base/T_Superhero_Female_Dark_BaseColor.png  (1319410 bytes)
cf922460b43ccd31e983e34db05514c9d451dd2f9cdd01a843978e797719f859  base/T_Superhero_Female_Normal.png  (3940537 bytes)
d2beabf2bd0313e32c68dcdbb80dca371a6e994fabf96efa97128bf9f14fa57b  base/T_Superhero_Female_Roughness.png  (3277022 bytes)
df680cbc1967a61e85998bfafb8f7bc0a36dd604bb3266486c4b06b1a184bb45  base/T_Superhero_Male_Dark.png  (1384380 bytes)
9b25cf9200216eb754b79cf4c63b5380c419780788322f3c57cdd2b3e02679a6  base/T_Superhero_Male_Normal.png  (4252937 bytes)
c70dabf48574cda55644d556beae1ee7cf1bdcf68a50d259d20f2f2358f27991  base/T_Superhero_Male_Roughness.png  (3152049 bytes)
b79abe12089d1894fa5349fbc29d2864f8c1e6f976665eb74edb328204872565  parts/Female_Peasant_Arms.bin  (327920 bytes)
7f2446a7bab93b882e4095a9583219de3f381962551e8a7d451c287d74a8987e  parts/Female_Peasant_Arms.gltf  (23970 bytes)
f1346372e81f9e906709b3adb84320c8f86f520efcbfa0292323fabecd2f4f22  parts/Female_Peasant_Body.bin  (203524 bytes)
9c4edd8d18a028ee721fbaa5431a42e6ae1b579ac3bd756604bf888b387d4529  parts/Female_Peasant_Body.gltf  (88739 bytes)
0e1f7ac2f5a349dbeb3560c820f9b8588ab5c205fc2b0b70f852c153a19c6262  parts/Female_Peasant_Feet.bin  (140776 bytes)
1c8cfde62c44e578d10194f769a568dd40a7f0523d0d286661660141704715de  parts/Female_Peasant_Feet.gltf  (24397 bytes)
4a86e2896a6efec9c72828b0fd9a0c8d483495061c45ef1f3e434a6951823abb  parts/Female_Peasant_Legs.bin  (74376 bytes)
1369d75a8197e9e9fdbaf9491b276e7a31c08944377145ff5e497a7c1ac81ea3  parts/Female_Peasant_Legs.gltf  (23962 bytes)
d24f6475c4edf51fe9383eca73a0cff76762c54df3a4cc96506533a20617f660  parts/Male_Peasant_Arms.bin  (274868 bytes)
4eb0fff5637cb65909103fee86c799f13883c9fa18a0118cc5233a77b67db1d2  parts/Male_Peasant_Arms.gltf  (26703 bytes)
d9b380153cbac7850ab3c65c95e831164873f1f7ff696cf8d20a9532c8a45e0f  parts/Male_Peasant_Body.bin  (219680 bytes)
daaa452abe8762c3bee7b1b30066c76d62077873c72cbf826de1a0f575ac3cb0  parts/Male_Peasant_Body.gltf  (23738 bytes)
cb35f50fb3e784cac5e3193ed82034454af550a9e7f33d01345ce615d7b05add  parts/Male_Peasant_Feet.bin  (139880 bytes)
191a2d70d6c2e550669bb7b1fc1c07be650d7168512e18eb2acb0e55d0535c52  parts/Male_Peasant_Feet.gltf  (23740 bytes)
529bfc210a2de7e7ef6e704b59a11f88704068726cdda7d3b8db8e705273d5dc  parts/Male_Peasant_Legs.bin  (52816 bytes)
207933393b7a2ef436c0ffea65b70e35feaee084992e798c3eb31e0c771fabb0  parts/Male_Peasant_Legs.gltf  (23721 bytes)
a43635628d95571cd62fd4db0cc3a6ea32778b2bc02f242dda224c89d07f1ade  parts/T_Peasant_BaseColor.png  (5055760 bytes)
7598fa7b63e46fd4dac29708bf5a81e05eb9a67280f7b13c61e28a9110eeb679  parts/T_Peasant_Normal.png  (14110336 bytes)
e1932f5f91104afca89c501416a5fec09069b8552734237fc09045fabc4ca9b4  parts/T_Peasant_ORM.png  (9903835 bytes)
3b6ab973f9f3d6f8961226a0dbd99cf6d1b72df3795a8a5c1620a55754c161c2  parts/T_Regular_Female_Dark_BaseColor.png  (1348542 bytes)
e1051d3d56df9cf061bc14c769c37253aecd595f8275f9d4c0d6e0e953c00e18  parts/T_Regular_Female_Normal.png  (3913459 bytes)
da541fbd4b3bffe754fada5c29f8a0d8f836bf20ce7df8273607af4729a3a5ae  parts/T_Regular_Female_Roughness.png  (3274215 bytes)
b4dcc0f4139aab548d7c070c4655bd2080ef16caeaaabee6c4aeb693c524e802  parts/T_Regular_Male_Dark_BaseColor.png  (1316151 bytes)
10cd71e2453e577fdd43e912b6016a99baf64964f0593e524bdd304855e15e2a  parts/T_Regular_Male_Normal.png  (4064184 bytes)
086c2eb25bddfdb77d8e639ccbffb8df723ef4a1910d8e1b217e852f8668bfe5  parts/T_Regular_Male_Roughness.png  (3160102 bytes)
```
