class_name PhaseData
extends RefCounted
## Catálogo completo das 50 corridas. As 30 telas extras formam a expansão
## "Brasil sem Freio" e usam as mesmas peças vetoriais para manter o APK leve.

const BALANCE = preload("res://resources/game_balance.tres")
const PHASE_COUNT := 50

const THEMES := [
    {"group": "cidade", "sky": Color("#80d7ee"), "horizon": Color("#f3c56a"), "road": Color("#3b4658"), "accent": Color("#f6c945"), "weather": "sol"},
    {"group": "cidade", "sky": Color("#a6e5ef"), "horizon": Color("#ffd27b"), "road": Color("#46505f"), "accent": Color("#ed8c39"), "weather": "sol"},
    {"group": "cidade", "sky": Color("#87c6ed"), "horizon": Color("#ffb86b"), "road": Color("#374255"), "accent": Color("#b7d8ef"), "weather": "sol"},
    {"group": "cidade", "sky": Color("#72c9e4"), "horizon": Color("#ffca72"), "road": Color("#4b5155"), "accent": Color("#e94f4f"), "weather": "sol"},
    {"group": "noite", "sky": Color("#252f58"), "horizon": Color("#ef795f"), "road": Color("#242b40"), "accent": Color("#ffcf4a"), "weather": "poente"},
    {"group": "noite", "sky": Color("#17284d"), "horizon": Color("#d36b61"), "road": Color("#283247"), "accent": Color("#f1aa3e"), "weather": "poente"},
    {"group": "noite", "sky": Color("#172c50"), "horizon": Color("#a95861"), "road": Color("#222b3d"), "accent": Color("#ecdd63"), "weather": "noite"},
    {"group": "noite", "sky": Color("#203656"), "horizon": Color("#718ba0"), "road": Color("#303945"), "accent": Color("#ef6e48"), "weather": "nublado"},
    {"group": "chuva", "sky": Color("#405b73"), "horizon": Color("#7d9aa7"), "road": Color("#34434d"), "accent": Color("#73c9d9"), "weather": "chuva"},
    {"group": "chuva", "sky": Color("#415b69"), "horizon": Color("#879fa7"), "road": Color("#35444d"), "accent": Color("#f4bd4b"), "weather": "chuva"},
    {"group": "verde", "sky": Color("#80d2ee"), "horizon": Color("#c9e88b"), "road": Color("#4b5950"), "accent": Color("#efa642"), "weather": "sol"},
    {"group": "verde", "sky": Color("#60c6ea"), "horizon": Color("#f5b6a0"), "road": Color("#43515a"), "accent": Color("#ef6a66"), "weather": "sol"},
    {"group": "carnaval", "sky": Color("#5abfe2"), "horizon": Color("#f6a36d"), "road": Color("#4b4655"), "accent": Color("#f4428a"), "weather": "sol"},
    {"group": "interior", "sky": Color("#93d8ef"), "horizon": Color("#ffd17d"), "road": Color("#6a5d4e"), "accent": Color("#5cac62"), "weather": "sol"},
    {"group": "interior", "sky": Color("#f4ad7d"), "horizon": Color("#ffdb87"), "road": Color("#574a4e"), "accent": Color("#8d5fd3"), "weather": "poente"},
    {"group": "terminal", "sky": Color("#334865"), "horizon": Color("#a0adab"), "road": Color("#343c4c"), "accent": Color("#f5c945"), "weather": "nublado"},
    {"group": "historico", "sky": Color("#65bfdd"), "horizon": Color("#f5c786"), "road": Color("#5b5256"), "accent": Color("#e46d52"), "weather": "sol"},
    {"group": "industria", "sky": Color("#5d7688"), "horizon": Color("#d18c65"), "road": Color("#3e444b"), "accent": Color("#e3a33f"), "weather": "poeira"},
    {"group": "remix", "sky": Color("#271e4b"), "horizon": Color("#e34d66"), "road": Color("#252b42"), "accent": Color("#55dfc0"), "weather": "caos"},
    {"group": "final", "sky": Color("#141d3b"), "horizon": Color("#e99356"), "road": Color("#1e2639"), "accent": Color("#ffdc50"), "weather": "amanhecer"}
]

const EXTRA_THEMES := [
    {"group": "tecnologia", "sky": Color("#182c57"), "horizon": Color("#3cc4bd"), "road": Color("#202d49"), "accent": Color("#72f2d3"), "weather": "neon"},
    {"group": "festival", "sky": Color("#48316c"), "horizon": Color("#f27e78"), "road": Color("#3b304c"), "accent": Color("#ffd35b"), "weather": "confete"},
    {"group": "agua", "sky": Color("#49bad6"), "horizon": Color("#a4e5d1"), "road": Color("#3f6871"), "accent": Color("#f5d36a"), "weather": "chuva"},
    {"group": "sertao", "sky": Color("#eea05f"), "horizon": Color("#f5d37b"), "road": Color("#70533f"), "accent": Color("#62b879"), "weather": "poeira"},
    {"group": "futuro", "sky": Color("#0f163a"), "horizon": Color("#b64eaa"), "road": Color("#21264b"), "accent": Color("#6fffe9"), "weather": "neon"},
    {"group": "apocalipse", "sky": Color("#281f2c"), "horizon": Color("#d86d4f"), "road": Color("#35333b"), "accent": Color("#ffcf59"), "weather": "cinzas"}
]

const NAMES := [
    "Segunda-feira", "Terça do pão", "Quarta do chefe", "Quinta da feira", "Sexta do rolê",
    "Sábado do camelô", "Domingo de jogo", "Segunda de novo", "Terça da chuva", "Quarta do motoboy",
    "Quinta do cachorro", "Sexta da praia", "Sábado do bloco", "Domingo do interior", "Segunda da favela",
    "Terça da rodoviária", "Quarta do centro histórico", "Quinta do caminhão", "Sexta do caos", "O DIA DO BUSÃO"
]
const LOCATIONS := [
    "Centro da cidade", "Padaria de bairro", "Escritório / Av. Paulista", "Feira livre", "Botequim",
    "Rua do comércio", "Estádio", "Zona de obras", "Rua alagada", "Avenida movimentada",
    "Parque", "Orla de Copacabana", "Carnaval de rua", "Cidade pequena", "Ladeira / escadaria",
    "Terminal interestadual", "Centro histórico", "Zona industrial", "REMIX: tudo ao mesmo tempo", "Maratona final"
]
const SPECIALS := [
    "Acorda, Zé! O relógio não perdoa.", "Pão de queijo dá um pulo que nem mineiro atrasado.", "Pessoas no celular fazem zigue-zague corporativo.",
    "Barracas estreitas: olha o pastel voando!", "Mesa de boteco e a buzina já começa.", "Camelôs liberam o modo panfleto.",
    "A torcida está gritando. Não tropeça na faixa!", "Britadeira: TRRRRRR! Use as rampas da obra.", "Enchente: geladeira boiando é obstáculo real.",
    "Motoboy em alta velocidade: SAI DA RUA!", "Cachorro caramelo detectado. Corra por dez segundos!", "A praia tem água, areia e um busão amarelo.",
    "Confete, marchinha e caos colorido.", "Capivara e cavalo têm prioridade no interior.", "Ladeira turbo: wall-run é seu melhor amigo.",
    "Terminal lotado. Ache a plataforma certa.", "Turista parou no meio da foto. Desvia!", "Caminhão desgovernado: timing exato.",
    "REMIX: cada pista tem uma surpresa.", "O último ponto. O ônibus NÃO espera!"
]

const EXTRA_NAMES := [
    "Quarta do Pix", "Quinta do pagode", "Sexta do aeroporto", "Sábado da quermesse", "Domingo do churrasco",
    "Segunda do home office", "Terça do influencer", "Quarta do metrô", "Quinta do parque aquático", "Sexta da balada",
    "Sábado do festival", "Domingo da trilha", "Segunda do condomínio", "Terça da biblioteca", "Quarta do shopping",
    "Quinta do trem lotado", "Sexta cyber-Brasil", "Sábado do mangue", "Domingo do sertão", "Segunda da greve",
    "Terça do apagão", "Quarta do calor", "Quinta do rodízio", "Sexta do streaming", "Sábado da megafeira",
    "Domingo da virada", "Segunda do multiverso", "Terça do tempo", "Quarta dos chefes finais", "O ÚLTIMO PONTO"
]
const EXTRA_LOCATIONS := [
    "Bairro high-tech", "Quadra da escola de samba", "Aeroporto internacional", "Quermesse da paróquia", "Churrasco na laje",
    "Prédio do home office", "Avenida dos trends", "Estação Sé", "Parque aquático municipal", "Rua das baladas",
    "Festival de música", "Trilha ecológica", "Condomínio fechado", "Biblioteca silenciosa", "Shopping lotado",
    "Plataforma do trem", "Cidade cyber-Brasil", "Manguezal urbano", "Estrada do sertão", "Greve geral",
    "Bairro sem luz", "Asfalto derretendo", "Avenida do rodízio", "Estúdio de streaming", "Megafeira nacional",
    "Praça da virada", "Multiverso brasileiro", "Rua que muda de época", "Arena dos chefes", "Ponto final do Brasil"
]
const EXTRA_SPECIALS := [
    "PIX caiu! Drones de entrega e notificações voam na sua cara.", "O pandeiro acelera e o pagode muda o ritmo da pista.", "Bagagem sem dono: mala gigante atravessa a sua faixa.",
    "Pescaria, correio elegante e milho: festa junina não dá passagem.", "Espetinho, caixa de som e uma bola perdida. Desvia com respeito.",
    "Reunião que podia ser e-mail: cadeiras de escritório ocupam a rua.", "Trend do momento: influencer tira selfie em câmera lenta.", "Catracas e escadas rolantes: escolha o caminho esperto.",
    "Toboágua de rua! A pista molhada muda o seu freio.", "Luzes piscando e segurança dançando: sobrevive à balada.", "Palco, fãs e drone filmando: pegue o autógrafo dourado.", "A trilha tem macaquinho curioso e ponte de madeira.",
    "Síndico colocou cone em tudo. Jeitinho brasileiro ativado.", "Silêncio na biblioteca! Até o espirro vira obstáculo.", "Promoção relâmpago: carrinhos de compra vêm em combo.",
    "Portas fechando, gente correndo: o trem não espera ninguém.", "Placas holográficas, mototáxi voador e neon de botequim.", "Caranguejo atravessa de lado e o mangue engole o tênis.",
    "O berrante toca e a boiada tem prioridade no asfalto.", "Greve: faixas, cartazes e uma catraca humana.", "Apagão total! Só o reflexo do bilhete mostra o caminho.",
    "Calor de 40 graus: sombra é item raro e o asfalto pula.", "Três voltas no quarteirão e ainda falta uma mesa.", "Live ao vivo: comentários aparecem como obstáculos.",
    "A maior feira do país. Escolha entre pastel, coxinha e atalho.", "Fogos, confete e ônibus dourado: feliz virada, atrasado!", "Duas versões do Zé na mesma pista. Não bata em você.",
    "Uma faixa leva ao passado, outra ao futuro. O ponto está nos dois.", "Nove chefes, nove gags e um ônibus que finalmente respeita você.", "Último ponto: o país inteiro está assistindo. Corre!"
]

static func get_phase(index: int) -> Dictionary:
    var i: int = clampi(index, 0, PHASE_COUNT - 1)
    var extra_index := i - NAMES.size()
    var t: Dictionary = THEMES[i] if i < THEMES.size() else EXTRA_THEMES[int(extra_index / 5) % EXTRA_THEMES.size()]
    var phase_name: String = NAMES[i] if i < NAMES.size() else EXTRA_NAMES[extra_index]
    var location: String = LOCATIONS[i] if i < LOCATIONS.size() else EXTRA_LOCATIONS[extra_index]
    var special: String = SPECIALS[i] if i < SPECIALS.size() else EXTRA_SPECIALS[extra_index]
    var speed: float
    var obstacles: int
    var ramps: int
    var wall_runs: int
    var wait_time: float
    if i <= BALANCE.chapter_unlock_phase:
        var chapter_progress := float(i) / float(maxi(1, BALANCE.chapter_unlock_phase))
        speed = lerpf(BALANCE.base_speed, BALANCE.chapter_one_final_speed, chapter_progress)
        obstacles = 2 + int(round(10.0 * chapter_progress))
        ramps = 1 + int(floor(float(i) * 4.0 / float(maxi(1, BALANCE.chapter_unlock_phase))))
        wall_runs = int(floor(float(i) * 4.0 / float(maxi(1, BALANCE.chapter_unlock_phase))))
        wait_time = lerpf(BALANCE.first_wait_seconds, BALANCE.final_wait_seconds, chapter_progress)
    else:
        var expansion_progress := float(i - BALANCE.chapter_unlock_phase) / float(maxi(1, BALANCE.phase_count - BALANCE.chapter_unlock_phase - 1))
        speed = lerpf(BALANCE.chapter_one_final_speed, BALANCE.final_speed, expansion_progress)
        obstacles = 12 + int(round(6.0 * expansion_progress))
        ramps = 5 + int(floor(3.0 * expansion_progress))
        wall_runs = 4 + int(floor(4.0 * expansion_progress))
        wait_time = BALANCE.final_wait_seconds
    var difficulty: int = 1 + int(floor(float(i) * 8.0 / 49.0))
    return {
        "index": i,
        "name": phase_name,
        "location": location,
        "special": special,
        "theme": t["group"],
        "sky": t["sky"],
        "horizon": t["horizon"],
        "road": t["road"],
        "accent": t["accent"],
        "weather": t["weather"],
        "speed": speed,
        "obstacles": obstacles,
        "ramps": ramps,
        "wall_runs": wall_runs,
        "wait": wait_time,
        "difficulty": difficulty,
        "distance": 400.0 + i * 8.0,
        # A meta de moedas fica em cerca de 70–78% das moedas da pista:
        # exige leitura e rota, mas nunca depende de uma coleta perfeita.
        "coin_target": 4 + int(round(float(i) * 0.85)),
        "music_group": int(i / 5) % 4
    }

static func all_phases() -> Array[Dictionary]:
    var output: Array[Dictionary] = []
    for i in PHASE_COUNT:
        output.append(get_phase(i))
    return output
