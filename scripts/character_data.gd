class_name CharacterData
extends RefCounted
## Vinte corredores humanos brasileiros, dez masculinos e dez femininos.
## O primeiro lote cobre os arquétipos do dia a dia urbano; o lote 2
## ("Turma do Ponto 2") traz profissões e clima regional do Brasil.
## As identidades são arquétipos cotidianos, sem depender de retrato ou asset
## externo: o visual final é montado com meshes humanoides 3D detalhados, materiais e acessórios.

const CATALOG: Array[Dictionary] = [
    {
        "id": "ze",
        "name": "Zé Atrasado",
        "gender": "M",
        "role": "trabalhador urbano",
        "description": "camiseta, tênis e mochila de todo dia",
        "effect": "equilíbrio padrão",
        "price": 0,
        "skin": Color("#b87655"),
        "hair": Color("#211b1a"),
        "shirt": Color("#e55359"),
        "pants": Color("#263a55"),
        "shoes": Color("#f3ca55"),
        "accent": Color("#55c4c8"),
        "style": "casual"
    },
    {
        "id": "motoboy",
        "name": "Rafa Motoboy",
        "gender": "M",
        "role": "entregador",
        "description": "colete refletivo, capacete e bag térmica",
        "effect": "velocidade +22%",
        "price": 260,
        "skin": Color("#70452f"),
        "hair": Color("#17171d"),
        "shirt": Color("#f08b3e"),
        "pants": Color("#202b39"),
        "shoes": Color("#e5e9df"),
        "accent": Color("#43d6bd"),
        "style": "motoboy"
    },
    {
        "id": "luan",
        "name": "Luan do Skate",
        "gender": "M",
        "role": "skatista",
        "description": "moletom largo, boné e tênis de street",
        "effect": "velocidade +22%",
        "price": 320,
        "skin": Color("#d08b63"),
        "hair": Color("#38221f"),
        "shirt": Color("#7659d6"),
        "pants": Color("#d5a45f"),
        "shoes": Color("#f3eee0"),
        "accent": Color("#ed6aa0"),
        "style": "skater"
    },
    {
        "id": "joao",
        "name": "João Gamer",
        "gender": "M",
        "role": "estudante de tecnologia",
        "description": "jaqueta colorida, fone e mochila pixel",
        "effect": "câmera lenta inicial",
        "price": 380,
        "skin": Color("#e1a47b"),
        "hair": Color("#3a2630"),
        "shirt": Color("#2f9fe2"),
        "pants": Color("#303044"),
        "shoes": Color("#8de5d0"),
        "accent": Color("#b88cff"),
        "style": "gamer"
    },
    {
        "id": "carlos",
        "name": "Carlos da Obra",
        "gender": "M",
        "role": "profissional da construção",
        "description": "capacete, colete e bota de segurança",
        "effect": "escudo de impacto",
        "price": 440,
        "skin": Color("#8d5837"),
        "hair": Color("#211a18"),
        "shirt": Color("#ee793d"),
        "pants": Color("#56606c"),
        "shoes": Color("#5e3828"),
        "accent": Color("#ffe36b"),
        "style": "obra"
    },
    {
        "id": "maria",
        "name": "Maria do Bairro",
        "gender": "F",
        "role": "comerciante",
        "description": "blusa estampada, saia confortável e bolsa",
        "effect": "escudo de impacto",
        "price": 180,
        "skin": Color("#6c3e2d"),
        "hair": Color("#1d1517"),
        "shirt": Color("#e58aab"),
        "pants": Color("#5b4070"),
        "shoes": Color("#f2c65a"),
        "accent": Color("#68c6b1"),
        "style": "bairro"
    },
    {
        "id": "bia",
        "name": "Bia Estudante",
        "gender": "F",
        "role": "estudante",
        "description": "uniforme, mochila e tênis colorido",
        "effect": "ímã de moedas",
        "price": 240,
        "skin": Color("#c98463"),
        "hair": Color("#4c2d24"),
        "shirt": Color("#f2f0e5"),
        "pants": Color("#3a6fa0"),
        "shoes": Color("#ec6b6a"),
        "accent": Color("#f5c85a"),
        "style": "estudante"
    },
    {
        "id": "camila",
        "name": "Camila do Negócio",
        "gender": "F",
        "role": "empreendedora",
        "description": "macacão, tablet e bolsa tiracolo",
        "effect": "moedas em dobro",
        "price": 300,
        "skin": Color("#a96246"),
        "hair": Color("#24191a"),
        "shirt": Color("#46b6a3"),
        "pants": Color("#305a5d"),
        "shoes": Color("#f0b84e"),
        "accent": Color("#f27a5b"),
        "style": "empreendedora"
    },
    {
        "id": "julia",
        "name": "Júlia Atleta",
        "gender": "F",
        "role": "corredora",
        "description": "look esportivo, faixa e garrafa",
        "effect": "pulo prolongado",
        "price": 360,
        "skin": Color("#7b4937"),
        "hair": Color("#171319"),
        "shirt": Color("#e75076"),
        "pants": Color("#242c4c"),
        "shoes": Color("#68e0c0"),
        "accent": Color("#e9d459"),
        "style": "atleta"
    },
    {
        "id": "influencer",
        "name": "Nina Creator",
        "gender": "F",
        "role": "criadora de conteúdo",
        "description": "top texturizado, shorts jeans, botas e celular na mão",
        "effect": "ímã de moedas",
        "price": 420,
        "skin": Color("#d49b7b"),
        "hair": Color("#291b2c"),
        "shirt": Color("#171824"),
        "pants": Color("#4f7897"),
        "shoes": Color("#171a26"),
        "accent": Color("#d7b9e9"),
        "style": "creator"
    },
    {
        "id": "chico",
        "name": "Chico Carteiro",
        "gender": "M",
        "role": "carteiro",
        "description": "boné, sacola de cartas e tênis de entrega",
        "effect": "velocidade +22%",
        "price": 480,
        "skin": Color("#8a5a3c"),
        "hair": Color("#1c1614"),
        "shirt": Color("#2f6db8"),
        "pants": Color("#22314a"),
        "shoes": Color("#2b2b33"),
        "accent": Color("#ffd23e"),
        "style": "carteiro"
    },
    {
        "id": "tiao",
        "name": "Tião Vaqueiro",
        "gender": "M",
        "role": "peão de vaquejada",
        "description": "chapéu de couro, gibão e bota de vaquejada",
        "effect": "pulo prolongado",
        "price": 560,
        "skin": Color("#6e452c"),
        "hair": Color("#191210"),
        "shirt": Color("#a8672f"),
        "pants": Color("#5a3d28"),
        "shoes": Color("#3a2617"),
        "accent": Color("#d9b06a"),
        "style": "vaqueiro"
    },
    {
        "id": "beto",
        "name": "Beto Praiano",
        "gender": "M",
        "role": "surfista",
        "description": "regata, bermuda e colar de contas",
        "effect": "dash recarrega rápido",
        "price": 620,
        "skin": Color("#c98a5e"),
        "hair": Color("#7a5c34"),
        "shirt": Color("#35c4b0"),
        "pants": Color("#e0d29a"),
        "shoes": Color("#f2efe6"),
        "accent": Color("#ff8c42"),
        "style": "praiano"
    },
    {
        "id": "nilo",
        "name": "Nilo Padeiro",
        "gender": "M",
        "role": "padeiro",
        "description": "avental, touca e bandeja de pão de queijo",
        "effect": "+1 coração de energia",
        "price": 700,
        "skin": Color("#e3ad82"),
        "hair": Color("#3d2b1f"),
        "shirt": Color("#f4efe6"),
        "pants": Color("#cfd4da"),
        "shoes": Color("#4b4f57"),
        "accent": Color("#e0993e"),
        "style": "padeiro"
    },
    {
        "id": "professor",
        "name": "Professor Everaldo",
        "gender": "M",
        "role": "professor",
        "description": "camisa social, gravata e livro na mão",
        "effect": "câmera lenta inicial",
        "price": 780,
        "skin": Color("#7f5236"),
        "hair": Color("#8e8e94"),
        "shirt": Color("#eae4d6"),
        "pants": Color("#2e3a52"),
        "shoes": Color("#26221f"),
        "accent": Color("#b8864f"),
        "style": "professor"
    },
    {
        "id": "marta",
        "name": "Dona Marta da Feira",
        "gender": "F",
        "role": "feirante",
        "description": "avental, bandana e banca de frutas",
        "effect": "ímã de moedas",
        "price": 500,
        "skin": Color("#9c6647"),
        "hair": Color("#2a1c1e"),
        "shirt": Color("#ef8f3f"),
        "pants": Color("#4f7a4a"),
        "shoes": Color("#d8c9a8"),
        "accent": Color("#f5d76e"),
        "style": "feirante"
    },
    {
        "id": "zilda",
        "name": "Vovó Zilda",
        "gender": "F",
        "role": "aposentada turbo",
        "description": "vestido florido, lenço e bolsa de mercado",
        "effect": "escudo de impacto",
        "price": 540,
        "skin": Color("#caa07b"),
        "hair": Color("#d8d5cf"),
        "shirt": Color("#d98cb0"),
        "pants": Color("#6a4f7c"),
        "shoes": Color("#3a2e2a"),
        "accent": Color("#8fd4c2"),
        "style": "vovo"
    },
    {
        "id": "clara",
        "name": "Enfermeira Clara",
        "gender": "F",
        "role": "enfermeira",
        "description": "uniforme branco, gorro e prancheta",
        "effect": "+1 coração de cuidado",
        "price": 640,
        "skin": Color("#d9a583"),
        "hair": Color("#5b3a29"),
        "shirt": Color("#f4f7fa"),
        "pants": Color("#dfe7ee"),
        "shoes": Color("#eef1f5"),
        "accent": Color("#e05263"),
        "style": "enfermeira"
    },
    {
        "id": "deise",
        "name": "Deise Craque",
        "gender": "F",
        "role": "jogadora de futebol",
        "description": "camisa dez, calção e chuteira",
        "effect": "velocidade +22%",
        "price": 720,
        "skin": Color("#75492f"),
        "hair": Color("#1f1719"),
        "shirt": Color("#f6c945"),
        "pants": Color("#1f4f8f"),
        "shoes": Color("#245c3f"),
        "accent": Color("#2fa36b"),
        "style": "craque"
    },
    {
        "id": "cida",
        "name": "Motorista Cida",
        "gender": "F",
        "role": "motorista de ônibus",
        "description": "farda da empresa, quepe e crachá do busão",
        "effect": "ônibus espera +2s",
        "price": 860,
        "skin": Color("#8d5c3e"),
        "hair": Color("#241a1c"),
        "shirt": Color("#3f7fae"),
        "pants": Color("#2b3f5e"),
        "shoes": Color("#23252d"),
        "accent": Color("#f6c945"),
        "style": "motorista"
    }
]

static func all() -> Array[Dictionary]:
    var output: Array[Dictionary] = []
    for item in CATALOG:
        output.append(item.duplicate(true))
    return output

static func canonical_id(id: String) -> String:
    var aliases: Dictionary = {
        "chefe": "carlos",
        "caramelo": "julia",
        "ze_atrasado": "ze",
        "nina": "influencer"
    }
    return str(aliases.get(id, id))

static func get_character(id: String) -> Dictionary:
    var wanted: String = canonical_id(id)
    for item in CATALOG:
        if str(item.get("id", "")) == wanted:
            return item.duplicate(true)
    return CATALOG[0].duplicate(true)
