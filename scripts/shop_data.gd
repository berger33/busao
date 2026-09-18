class_name ShopData
extends RefCounted
## Catálogo autoritativo da loja.
## A HUD pode exibir os valores, mas o save sempre consulta esta tabela para
## impedir que uma tela antiga ou um preço enviado pelo cliente altere a economia.

const CHARACTER_DATA = preload("res://scripts/character_data.gd")

const ITEM_CATALOG: Array[Dictionary] = [
    {
        "id": "tenis",
        "title": "Tênis turbo",
        "subtitle": "velocidade +",
        "price": 200,
        "accent": Color("#63e6d2")
    },
    {
        "id": "mochila",
        "title": "Mochila",
        "subtitle": "escudo extra",
        "price": 180,
        "accent": Color("#ffb83e")
    },
    {
        "id": "fone",
        "title": "Fone",
        "subtitle": "ímã de moedas",
        "price": 220,
        "accent": Color("#ac8cff")
    },
    {
        "id": "cafe",
        "title": "Café térmico",
        "subtitle": "slow-motion",
        "price": 150,
        "accent": Color("#c68053")
    },
    {
        "id": "confete",
        "title": "Kit confete",
        "subtitle": "efeito visual",
        "cosmetic": true,
        "price": 120,
        "accent": Color("#f2635e")
    },
    {
        "id": "placa",
        "title": "Placa VIP",
        "subtitle": "placa decorativa",
        "cosmetic": true,
        "price": 300,
        "accent": Color("#63c8ed")
    }
]

static func canonical_id(id: String) -> String:
    var aliases: Dictionary = {
        "chefe": "carlos",
        "caramelo": "julia",
        "nina": "influencer"
    }
    return str(aliases.get(id, id))

static func item_catalog() -> Array[Dictionary]:
    var output: Array[Dictionary] = []
    for item in ITEM_CATALOG:
        output.append(item.duplicate(true))
    return output

static func is_item(id: String) -> bool:
    var wanted := canonical_id(id)
    for item in ITEM_CATALOG:
        if str(item.get("id", "")) == wanted:
            return true
    return false

static func is_character(id: String) -> bool:
    var wanted := canonical_id(id)
    for character in CHARACTER_DATA.all():
        if str(character.get("id", "")) == wanted:
            return true
    return false

static func price_for(id: String) -> int:
    var wanted := canonical_id(id)
    for item in ITEM_CATALOG:
        if str(item.get("id", "")) == wanted:
            return maxi(0, int(item.get("price", 0)))
    for character in CHARACTER_DATA.all():
        if str(character.get("id", "")) == wanted:
            return maxi(0, int(character.get("price", 0)))
    return -1

static func is_purchasable(id: String) -> bool:
    return price_for(id) >= 0
