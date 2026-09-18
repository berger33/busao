class_name CharacterData
extends RefCounted
## Dez corredores humanos brasileiros, cinco masculinos e cinco femininos.
## As identidades são arquétipos cotidianos, sem depender de retrato ou asset
## externo: o visual final é montado com meshes humanoides 3D detalhados, materiais e acessórios.

const CATALOG: Array[Dictionary] = [
    {
        "id": "ze",
        "name": "Zé Atrasado",
        "gender": "M",
        "role": "trabalhador urbano",
        "description": "camiseta, tênis e mochila de todo dia",
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
        "price": 420,
        "skin": Color("#d49b7b"),
        "hair": Color("#291b2c"),
        "shirt": Color("#171824"),
        "pants": Color("#4f7897"),
        "shoes": Color("#171a26"),
        "accent": Color("#d7b9e9"),
        "style": "creator"
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
