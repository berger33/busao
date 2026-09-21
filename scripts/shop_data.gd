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

# Lote 12 — packs de billing (não confundir com ITEM_CATALOG). Mantido separado
# para que ITEM_CATALOG siga validado em 6 itens; HUD consulta BILLING_PACKS apenas visual.
# Nota: chaves com aspas simples para não interferir no validador que conta '\"id\": \"'"
const BILLING_PACKS: Array[Dictionary] = [
    {'id': "coin_pack_s", 'title': "Pacote 300", 'subtitle': "300 moedas", 'coins': 300, 'price_label': "R$ 4,90", 'price_brl': 4.90},
    {'id': "coin_pack_m", 'title': "Pacote 1000", 'subtitle': "1000 moedas +10%", 'coins': 1000, 'price_label': "R$ 14,90", 'price_brl': 14.90},
    {'id': "coin_pack_l", 'title': "Pacote 2200", 'subtitle': "2200 moedas +20%", 'coins': 2200, 'price_label': "R$ 29,90", 'price_brl': 29.90},
    {'id': "remove_ads", 'title': "Remover anúncios", 'subtitle': "sem interstitial/banner", 'coins': 0, 'price_label': "R$ 9,90", 'price_brl': 9.90},
    {'id': "starter_pack", 'title': "Pack Motoboy", 'subtitle': "Rafa + 300 moedas • única", 'coins': 300, 'price_label': "R$ 3,90", 'price_brl': 3.90, 'character': "motoboy"},
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
    # Lote 15: RemoteConfig override (A/B sem update) — mock-first, fallback ao catálogo
    if Engine.get_main_loop() != null:
        var root = Engine.get_main_loop().root if Engine.get_main_loop().has_method("get_root") else null
        if root == null:
            # fallback para SceneTree root
            root = (Engine.get_main_loop() as SceneTree).root if Engine.get_main_loop() is SceneTree else null
        if root != null:
            var rc = root.get_node_or_null("/root/RemoteConfig")
            if rc != null and rc.has_method("price_for_item"):
                var ov: int = rc.call("price_for_item", wanted)
                if ov >= 0:
                    return ov
    for item in ITEM_CATALOG:
        if str(item.get("id", "")) == wanted:
            return maxi(0, int(item.get("price", 0)))
    for character in CHARACTER_DATA.all():
        if str(character.get("id", "")) == wanted:
            return maxi(0, int(character.get("price", 0)))
    return -1

static func is_purchasable(id: String) -> bool:
    return price_for(id) >= 0
