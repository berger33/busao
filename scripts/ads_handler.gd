extends RefCounted
class_name AdsHandler
## AdsHandler — P2 refactor
## Centraliza regras de banner/interstitial/rewarded e remove_ads.

static func setup_ads_billing(game: Node) -> void:
    var ads: Node = game.get_node_or_null("/root/AdsManager") if game.has_method("get_node_or_null") else null
    if ads != null:
        if not ads.is_connected("rewarded_completed", Callable(game, "_on_ads_rewarded_completed")):
            ads.rewarded_completed.connect(Callable(game, "_on_ads_rewarded_completed"))
        if not ads.is_connected("interstitial_closed", Callable(game, "_on_ads_interstitial_closed")):
            ads.interstitial_closed.connect(Callable(game, "_on_ads_interstitial_closed"))
        if not ads.is_connected("rewarded_failed", Callable(game, "_on_ads_rewarded_failed")):
            ads.rewarded_failed.connect(Callable(game, "_on_ads_rewarded_failed"))
        if not ads.is_connected("banner_loaded", Callable(game, "_on_ads_banner_loaded")):
            ads.banner_loaded.connect(Callable(game, "_on_ads_banner_loaded"))
    var billing: Node = game.get_node_or_null("/root/BillingManager") if game.has_method("get_node_or_null") else null
    if billing != null:
        if not billing.is_connected("purchase_success", Callable(game, "_on_billing_success")):
            billing.purchase_success.connect(Callable(game, "_on_billing_success"))
        if not billing.is_connected("purchase_failed", Callable(game, "_on_billing_failed")):
            billing.purchase_failed.connect(Callable(game, "_on_billing_failed"))
        if not billing.is_connected("products_loaded", Callable(game, "_on_billing_products_loaded")):
            billing.products_loaded.connect(Callable(game, "_on_billing_products_loaded"))
        if not billing.is_connected("owned_restored", Callable(game, "_on_billing_restored")):
            billing.owned_restored.connect(Callable(game, "_on_billing_restored"))

static func update_banner_visibility(game: Node) -> void:
    var ads: Node = game.get_node_or_null("/root/AdsManager") if game.has_method("get_node_or_null") else null
    if ads == null: return
    # GameSave autoload
    var gs: Node = game.get_node_or_null("/root/GameSave") if game.has_method("get_node_or_null") else null
    if gs != null and gs.has_method("get") and false: pass
    # checa remove_ads direto no singleton
    var data: Dictionary = {}
    if gs != null and "data" in gs:
        data = gs.data
    if bool(data.get("remove_ads", false)):
        if ads.has_method("hide_banner"): ads.hide_banner()
        return
    var screen: int = int(game.get("screen")) if "screen" in game else 0
    if screen in [0,1,4,5,6,7]:
        if ads.has_method("show_banner"): ads.show_banner()
    else:
        if ads.has_method("hide_banner"): ads.hide_banner()

static func try_show_interstitial_after_defeat(game: Node) -> void:
    var ads: Node = game.get_node_or_null("/root/AdsManager") if game.has_method("get_node_or_null") else null
    if ads == null: return
    var gs: Node = game.get_node_or_null("/root/GameSave") if game.has_method("get_node_or_null") else null
    if gs != null and "data" in gs and bool(gs.data.get("remove_ads", false)):
        return
    var failed: int = int(game.get("_ads_failed_runs")) if "_ads_failed_runs" in game else 0
    failed += 1
    game.set("_ads_failed_runs", failed)
    if gs != null and gs.has_method("record_ad_counter"):
        gs.call("record_ad_counter", "interstitial")
        var saved: int = int(gs.data.get("ad_counters",{}).get("interstitial_run", failed))
        failed = maxi(failed, saved)
        game.set("_ads_failed_runs", failed)
    if ads.has_method("can_show_interstitial_now") and ads.call("can_show_interstitial_now", failed):
        var ok: bool = ads.call("show_interstitial")
        if ok and game.has_method("_show_feedback"):
            game.call("_show_feedback", "ANÚNCIO", "Voltamos em segundos...", Color("#a9b9ca"), "ui_confirm")

static func request_rewarded(game: Node, placement: String) -> bool:
    var ads: Node = game.get_node_or_null("/root/AdsManager") if game.has_method("get_node_or_null") else null
    if ads == null or not ads.has_method("show_rewarded"):
        return false
    return ads.call("show_rewarded", placement)
