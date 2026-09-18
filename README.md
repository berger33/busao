# Corre pro Ponto 🚌

Um runner mobile-first **totalmente 3D** em **Godot 4.x**, inspirado na leitura de terceira pessoa de Subway Surfers e Sonic Dash. O corredor avança por uma avenida brasileira até o ponto de ônibus: a faixa esquerda é exclusivamente rua, com tráfego mais denso, e as faixas central e direita são calçadas. O mundo combina meshes procedurais leves, assets locais licenciados e materiais PBR; não há download em tempo de execução nem dependência de CDN.

## O que está pronto

- Loop jogável em terceira pessoa: correr para frente, trocar de faixa, pular, deslizar, dash, coletar e pegar o ônibus.
- **50 telas** cadastradas em `scripts/phase_data.gd`: o arco original de 20 fases + 30 telas da expansão **Brasil sem Freio**. A velocidade vai de 5 a 18 m/s, com tráfego, obstáculos urbanos e espera do ônibus cada vez mais apertados.
- Mundo 3D com câmera atrás/acima do personagem, panorama de céu com nuvens, iluminação, prédios, árvores, postes, meio-fio, materiais distintos, linhas da rua, ladrilhos, ponto de ônibus e ônibus amarelo.
- Progressão visual em dez capítulos de cinco fases: favela de terra, rua de bairro, centro, bairro humilde, classe média, vila militar, largo religioso, avenida comercial, orla turística e terminal final. Casas, lojas, obras, igrejas, guaritas, quiosques e skyline mudam junto com a fase.
- O cenário realmente desliza sob o corredor: pista, fachadas, obstáculos, ponto e decorações percorrem o eixo `-Z` com aceleração visual, passos sincronizados, balanço de câmera, inclinação do personagem e FOV progressivo.
- Céu com paleta por capítulo, sol animado, urubus, pombos, passarinhos, drones, aviões e gaivotas em rotas coerentes com o lugar.
- Três faixas caminháveis e semanticamente separadas: **esquerda = rua**, com carros populares brasileiros, ônibus, motos, buracos, caminhões e variações de trânsito; **centro/direita = calçadas**, com pedestres instanciados como personagens humanos 3D skinned, hidrante, orelhão brasileiro, cachorro caramelo 3D articulado, bicicleta, cone laranja de obra com faixas refletivas, carrinho de camelô, banco e objetos urbanos detalhados.
- A rua recebe intencionalmente maior densidade de obstáculos que as calçadas. O HUD reforça a leitura com “RUA”/“CALÇADA”, tutorial de rota e feedback audiovisual de desvio.
- 3 corações (1 nas Telas 20 e 50), colisões, invulnerabilidade do dash, game over e chegada com contagem regressiva no ponto.
- Coletáveis 3D: R$ 0,25, café, pão de queijo, pastel, caldo de cana, vale-transporte, bilhete dourado, coxinha, guaraná, PIX Turbo e guarda-chuva.
- Estrelas por fase, mapa paginado em 5 capítulos, Tela 20 liberada com 45 estrelas e Tela 50 com 120 estrelas.
- **Endless** liberado ao concluir a Tela 50, com corrida de 1000 m, XP, combo e recorde local persistido.
- Sequência diária: login consecutivo, bônus de R$ 100 a cada 7 dias e badges de coleção; a sequência é informativa e não bloqueia fases.
- Loja com **10 perfis humanos brasileiros** (5 masculinos e 5 femininos): o asset skinned compartilhado recebe corpo, pele, cabelo e paletas de roupa diferentes por perfil, enquanto preços, descrições e habilidades ficam persistidos localmente.
- Conquistas, badges, desafios diários, marco semanal e save JSON versionado em `user://corre_pro_ponto.json`, com autosave amortizado, backup e recuperação de escrita interrompida.
- Progressão/economia com primeira conclusão, replay de bônus fixo, diferença de estrela, saldo de moedas sem duplicação e loja com estado adquirido/equipado comunicado na HUD.
- Instrumentação local sem PII para sessões, tentativas, conclusões, falhas, primeiros clears, tempo, distância e compras; não há telemetria de rede neste escopo.
- Ganchos “clipáveis” do runner 3D: perseguição do caramelo, chegada no ônibus amarelo, tráfego pesado, mudança rua/calçada, dash com partículas e bônus de comida brasileira.
- Elementos de retenção: combo de moedas, badges, XP, login streak, capítulo 1 + expansão de 30 telas, mapa por capítulos e Endless final.
- Sons essenciais: passos/ações, pulo, moeda, colisão, buzina, latido, grito do motoboy e trilhas de quatro grupos de cenário.
- **Feedback premium de ação:** pool de oito canais de SFX, assinatura sonora para cada gesto, feedback de combo/recompensa, whoosh, impacto e confirmação de UI sem cortar sons simultâneos.
- **Texturização completa:** o asfalto e a calçada usam imagens raster realistas de alta definição, mapas normais e mapeamento triplanar; terra, paralelepípedo, tijolo, reboco, metal, vidro, tecido, pele, madeira, borracha e folhagem usam materiais SVG leves com roughness, metallic e emissive accents coerentes.
- **Céu e profundidade:** panorama tropical com nuvens, fog/aerial perspective, tonemapping, glow sutil, sombras e iluminação direcional por capítulo; as variações de clima ajustam energia, névoa e cor ambiente sem perder a leitura 3D.
- **Personagens, obstáculos e animais:** o boneco procedural foi substituído pelo asset real e skinned do Quaternius Universal Base Characters, com corpo humano reconhecível, rosto, olhos, cabelo volumoso com material próprio, pele, UVs, materiais PBR, esqueleto humanoide e skin weights. Pedestres de calçada passam pelo mesmo adapter em `scripts/world_character.gd`, portanto velha e camelô são personagens 3D completos, não cabeças/cápsulas. O cachorro caramelo usa `scripts/world_animal.gd`, com corpo, pescoço, cabeça, focinho, nariz, olhos, orelhas, quatro patas, cauda articulada, coleira e tag. O conjunto Peasant adiciona meshes skinned separados com mapas de cor, normal e ORM; para Nina Creator, o runner usa corpo feminino, top texturizado, shorts jeans, botas e detalhes presos ao esqueleto por `BoneAttachment3D`: telefone, tatuagem, brincos, pulseiras, lantejoulas e metal. `scripts/obstacle_data.gd` cataloga os 13 obstáculos, espaço e adapter 3D, enquanto `_audit_3d_entity` verifica em runtime se cada entidade criou `MeshInstance3D`. Carros, ônibus, motos e caminhões avançam no eixo da rua com velocidade própria e rodas animadas.
- **Veículos brasileiros:** os carros de trânsito usam três silhuetas de compactos populares brasileiros — hatch urbano, sedã compacto e utilitário/van — sem logotipos, com pintura metálica, placa, faróis, lanternas, retrovisores, maçanetas, grade, rodas e variantes de cor. O ônibus amarelo, moto de entrega e caminhão também recebem assemblies detalhados e materiais automotivos.
- **Polimento audiovisual 3D:** materiais por ambiente, câmera tremida, HUD sobreposto com barra de progresso, textos de feedback, partículas 3D e microanimações pensadas para 60 FPS sem assets pesados.
- Ícone vetorial original em `assets/art/icon.svg`.

## Estrutura

```text
project.godot              Configuração Godot 4 e autoloads
export_presets.cfg         Presets Android (AAB/APK) e Linux
scenes/main.tscn           Cena de entrada
scripts/game_3d.gd          Mundo 3D, câmera, pista, entidades, input e corrida
scripts/hud_3d.gd           HUD/menu/mapa/loja/resultados sobre o mundo 3D
scripts/scenario_data.gd     Dez capítulos visuais e paletas do Brasil
scripts/character_data.gd    Catálogo dos 10 corredores humanos
scripts/runner_character.gd  Instância GLTF skinned, roupa modular, rig e clips de locomoção
scripts/world_character.gd   Adaptador de pedestres humanos 3D para obstáculos
scripts/world_animal.gd      Cachorro caramelo 3D articulado e animado
scripts/obstacle_data.gd     Contrato dos 13 obstáculos e adapters 3D
scripts/shop_data.gd         Catálogo autoritativo de preços e itens
scripts/game.gd              Implementação vetorial 2D histórica mantida como referência
scripts/phase_data.gd        Dados das 50 fases e curva de dificuldade
scripts/save_data.gd         Save local/progressão
scripts/audio_manager.gd    Mixagem SFX/trilha, cache e pool de canais
resources/game_balance.tres Balanceamento documentado como recurso Godot
assets/art/icon.svg         Ícone original
assets/textures/*.svg       Texturas procedurais e mapas normais leves para superfícies, roupas, personagens e props
assets/textures/*.png       Asfalto, calçada, panoramas de céu, fibras de cabelo, jeans e pintura automotiva realistas
assets/characters/quaternius/  Corpo humano GLTF, roupa skinned, PBR, licença e AnimationLibrary CC0
assets/audio/*.wav           SFX e músicas procedurais originais
tools/generate_audio.py    Gerador reproduzível dos WAVs
tools/validate_project.py  Preflight de catálogo, caminhos, economia e assets
tools/audit_balance.py     Simulação determinística de curva, metas e densidade
tools/check_gdscript.py    Análise estática GDScript (parser, API do Godot 4, sombreamento e membros inexistentes)
tools/audit_runner_rig.py  Orientação, rig de animação, cadência e contato do corredor com o chão
docs/QUALITY_AUDIT.md      Auditoria e roadmap de qualidade visual/técnica
docs/PRODUCT_AUDIT.md      Auditoria de produto, economia, retenção e métricas
CREDITS.md                 Créditos e licenças
```

## As 30 telas novas

A expansão fica acessível no mapa paginado, dez fases por capítulo:

- **21–25:** Quarta do Pix, Quinta do pagode, Sexta do aeroporto, Sábado da quermesse, Domingo do churrasco.
- **26–30:** Segunda do home office, Terça do influencer, Quarta do metrô, Quinta do parque aquático, Sexta da balada.
- **31–35:** Sábado do festival, Domingo da trilha, Segunda do condomínio, Terça da biblioteca, Quarta do shopping.
- **36–40:** Quinta do trem lotado, Sexta cyber-Brasil, Sábado do mangue, Domingo do sertão, Segunda da greve.
- **41–45:** Terça do apagão, Quarta do calor, Quinta do rodízio, Sexta do streaming, Sábado da megafeira.
- **46–50:** Domingo da virada, Segunda do multiverso, Terça do tempo, Quarta dos chefes finais, O Último Ponto.

As telas novas variam tema, velocidade, densidade, clima e especiais no catálogo. No runner 3D, a expansão mantém o tráfego e os objetos urbanos do contrato de faixa e acrescenta PIX Turbo, coxinha, guaraná, guarda-chuva e outros bônus brasileiros.

## Os 10 corredores

- **Masculinos:** Zé Atrasado (casual), Rafa Motoboy (colete e capacete), Luan do Skate (moletom e skate), João Gamer (fone e mochila pixel) e Carlos da Obra (capacete e colete).
- **Femininos:** Maria do Bairro (bolsa e saia), Bia Estudante (uniforme e mochila), Camila do Negócio (macacão e tablet), Júlia Atleta (look esportivo) e Nina Creator (cabelo volumoso, top, botas e celular).

O catálogo continua oferecendo dez identidades e progressão de loja, mas a representação de gameplay agora usa um asset humano 3D real compartilhado: corpo Quaternius masculino/feminino, rosto, olhos, cabelo com material próprio e roupa modular Peasant com meshes skinned e mapas PBR separados. A identidade Nina Creator recebe uma camada de figurino texturizada de top, shorts jeans e botas, além de acessórios metálicos e celular ancorados nos ossos, sem transformar o corpo principal em uma montagem de primitivas. Os NPCs de obstáculo reutilizam o mesmo corpo profissional no modo de mundo, e o caramelo possui um animal 3D próprio com animação de cauda/patas. O esqueleto humanoide é animado pelos clips CC0 da Universal Animation Library; `Sprint_Loop`, `Jump_Loop`, `Crouch_Idle_Loop` e `Crouch_Fwd_Loop` acompanham corrida, pulo e deslize, com fallback somente para diagnóstico. O modelo é girado 180° (`MODEL_FACING_YAW`) porque o GLTF do Quaternius olha para `+Z` enquanto o corredor avança para `-Z`: sem isso ele aparece correndo de frente para a câmera. A cadência do `AnimationPlayer` acompanha a velocidade real do cenário (`Sprint_Loop` cobre ~4 m/s por ciclo), o que evita o pé patinar durante o dash e os capítulos rápidos. O asset, os binários, as texturas, o texto de licença e o manifesto SHA-256 estão em `assets/characters/quaternius/`. As cores/estilos da loja permanecem dados de progressão.

## Abrir e rodar no Godot 4

1. Instale o **Godot 4.7 estável** ou uma versão 4.x posterior (a versão Compatibility é suficiente).
2. Abra o Project Manager → **Import** → selecione a pasta que contém este `project.godot`.
3. Se o Godot perguntar pelo renderer, escolha **Compatibility / GL Compatibility**.
4. Pressione **F6** para a cena atual ou **F5** para o projeto. A cena principal já é `scenes/main.tscn`.
5. O jogo abre em retrato, viewport lógico de 720×1280, na cena `Node3D` `CorreProPonto3D`. No desktop, use `A/D` ou setas para mudar entre rua e calçadas, `W/↑/Espaço` para pular, `S/↓` para deslizar, `X` para dash e `M` para ligar/desligar o som. No Android, use os gestos indicados na HUD; o menu também oferece movimento reduzido e alto contraste, além do botão de som.

O projeto não precisa de plugins, fontes, conexão de internet, banco de dados ou assets baixados. O save é criado automaticamente em `user://`; para reiniciar o progresso, apague `corre_pro_ponto.json`, `corre_pro_ponto.bak.json` e `corre_pro_ponto.tmp.json` na pasta de dados do usuário do Godot.

Antes de abrir um PR, rode `python3 tools/validate_project.py`, `python3 tools/audit_balance.py` e `python3 tools/check_gdscript.py`. O primeiro valida contratos e integridade estrutural; o segundo confirma que as metas de moedas são alcançáveis e que a rua permanece mais densa que as calçadas; o terceiro reproduz, sem precisar do editor, os erros e avisos que aparecem no console e na aba de depuração (identificador não declarado, variável duplicada, argumentos a mais, divisão inteira, propriedades que não existem no Godot 4 — como o `receive_shadow` do Godot 3 — e nomes locais que sombreiam um membro da classe, de um script pai ou da classe nativa, com o mesmo texto que o Godot usa). Ele aceita `--selftest` para conferir as próprias regras numa fixture temporária — para checar também as assinaturas da API do engine, rode `python3 tools/check_gdscript.py --godot-doc /caminho/para/doc/classes`. Os três são barreiras rápidas, não substitutos para playtest. Para mexer no boneco (modelo, animação, escala ou pé no chão), rode também `python3 tools/audit_runner_rig.py`: ele lê os GLTF/GLB do Quaternius e confere para que lado o modelo olha, se os clips animam os 65 ossos deste corpo, quantos metros por segundo o ciclo de sprint cobre e se as solas ficam em `y = 0`.

## Android 8.0+

O código roda em Android 8.0 (API 26) ou superior e usa apenas GDScript + renderer Compatibility.

### Ambiente de exportação

1. No Godot, abra **Editor → Manage Export Templates** e instale os templates da mesma versão do editor.
2. Instale **JDK 17** (Temurin/Adoptium ou OpenJDK equivalente).
3. Instale o Android Studio e, no SDK Manager, os componentes:
   - Android SDK Platform 35 (o preset mantém min SDK 26);
   - Android SDK Build-Tools 35.0.1 ou compatível;
   - Android SDK Platform-Tools 35 ou mais recente;
   - Android SDK Command-line Tools (latest);
   - NDK/CMake compatíveis com a versão do Godot, caso o editor solicite.
4. Em **Editor → Editor Settings → Export → Android**, informe o caminho do JDK 17 e do Android SDK. Em Linux, exemplos comuns são `JAVA_HOME=/usr/lib/jvm/temurin-17-jdk` e `ANDROID_HOME=$HOME/Android/Sdk`.
5. Se o Android pedir permissões de Gradle na primeira exportação, aceite o download/cache padrão.

O preset Android já está no `export_presets.cfg`, com pacote `com.arena.correponto`, orientação portrait, **min SDK 26 (Android 8.0)**, target SDK 35 e arquitetura ARM64. Para testar direto no aparelho, ative a depuração USB, conecte o dispositivo e use **Project → Install Android Build Template** somente se precisar de um build Gradle customizado; para o preset padrão, escolha **Project → Export → Android**.

### APK de teste

- **Project → Export → Android → Export Project**
- Use `build/corre-pro-ponto.apk` ou escolha outro caminho.
- Para um aparelho, instale por USB com `adb install -r build/corre-pro-ponto.apk`.
- O APK de debug serve para testes, não para publicação.

### AAB para Google Play

1. Crie um keystore de release fora do repositório e nunca o adicione ao Git:
   ```bash
   keytool -genkeypair -v -keystore corre-pro-ponto-release.keystore \
     -alias correpro \
     -keyalg RSA -keysize 2048 -validity 10000
   ```
2. No preset Android, desmarque assinatura debug e informe o keystore, alias e senhas em **Editor → Export → Android**. Mantenha o keystore em local seguro e faça backup.
3. Escolha **Export Format: Android App Bundle (AAB)** e exporte para `build/corre-pro-ponto.aab`.
4. Teste primeiro no Play Console usando internal testing. O version code deve sempre crescer entre uploads.
5. Na ficha da Play Store, informe nome, descrição, classificação etária, política de privacidade, screenshots em portrait e o ícone. Gere screenshots usando os seis momentos clipáveis.
6. Preencha a seção de segurança de dados e conteúdo, faça o rollout de teste fechado e só então envie para produção. A assinatura do app deve continuar sendo a mesma em todas as atualizações.

> Os templates de exportação e o SDK/JDK são componentes instalados pelo desenvolvedor do Godot/Android; eles não são copiados para este repositório. O preset, o package id e as instruções estão prontos para a exportação local.

## Clipes de 6–15 segundos

Os momentos são acionados naturalmente nas fases e não dependem de assets externos:

1. **Cachorro caramelo:** o modelo 3D aparece na calçada e o desvio dispara latido e feedback de perseguição.
2. **Ônibus fechando:** o ônibus amarelo aparece no ponto, com buzina e contagem regressiva até o embarque.
3. **Tráfego pesado:** carros, motos, ônibus e caminhões se concentram na faixa esquerda; pulo e dash criam takes de timing.
4. **Calçada brasileira:** velha no celular, hidrante, orelhão, bicicleta, cone, camelô e banco formam uma rota visualmente legível.
5. **Mudança de rota:** a câmera acompanha a troca entre rua e as duas calçadas, com meio-fio e materiais distintos.
6. **Dash em câmera 3D:** partículas, flash, tremor de câmera e whoosh marcam a passagem por um obstáculo.

Para gravar, rode no editor ou em um APK, escolha a fase no mapa e use a gravação de tela do Android. O pause, a HUD limpa e a câmera em terceira pessoa deixam os takes fáceis de enquadrar.

## Créditos

Consulte [`CREDITS.md`](CREDITS.md) e [`assets/characters/quaternius/PROVENANCE.md`](assets/characters/quaternius/PROVENANCE.md). Os assets de personagem são distribuídos localmente com a licença CC0 documentada; não há download em runtime.
