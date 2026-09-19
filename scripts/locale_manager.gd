extends Node
## LocaleManager — Lote 16 (Língua)
## i18n pt_BR / en_US com CSV + TranslationServer + persistência GameSave.locale.
## Mock-first: carrega localization/strings.csv em Dictionary; `tr_key()` faz lookup
## e cai em `TranslationServer.translate` quando .translation importado existir.
## Troca em runtime via `set_locale("en_US")` — HUD re-desenha no próximo `state` update.

signal locale_changed(locale: String)

const DEFAULT_LOCALE := "pt_BR"
const CSV_PATH := "res://localization/strings.csv"
const SAVE_KEY := "locale"

var current_locale: String = DEFAULT_LOCALE
var _dict: Dictionary = {} # locale -> {key: translation}

func _ready() -> void:
    process_mode = Node.PROCESS_MODE_ALWAYS
    _load_csv()
    # Restaura preferência
    if GameSave and GameSave.data.has(SAVE_KEY):
        var saved := str(GameSave.data[SAVE_KEY])
        if saved in ["pt_BR", "en_US", "pt", "en"]:
            if saved == "pt": saved = "pt_BR"
            if saved == "en": saved = "en_US"
            current_locale = saved
    else:
        # Detecta do OS se ainda não escolheu
        var sys := OS.get_locale()
        if sys.begins_with("en"):
            current_locale = "en_US"
    TranslationServer.set_locale(current_locale)
    print("[locale] pronto locale=%s csv_keys=%d" % [current_locale, _dict.get(current_locale, {}).size()])

func _load_csv() -> void:
    var path := CSV_PATH
    # Tenta carregar via ResourceLoader (se importado) e fallback manual
    if not FileAccess.file_exists(path):
        # fallback para pt_BR.csv
        path = "res://localization/pt_BR.csv"
        if not FileAccess.file_exists(path):
            print("[locale] CSV não encontrado")
            return
    var txt := FileAccess.get_file_as_string(path)
    if txt.is_empty():
        return
    var lines := txt.split("\n", false)
    if lines.is_empty():
        return
    var header := lines[0].split(",", false)
    # header: keys,pt_BR,en_US
    var idx_pt := header.find("pt_BR")
    var idx_en := header.find("en_US")
    if idx_pt == -1: idx_pt = 1
    if idx_en == -1: idx_en = 2
    _dict["pt_BR"] = {}
    _dict["en_US"] = {}
    for i in range(1, lines.size()):
        var cols := lines[i].split(",", false)
        # CSV simples sem aspas com vírgula, mas nossas strings não têm vírgula exceto em traduções? já evitamos
        # Para linhas com vírgula, usa split max 3? Nossas chaves não têm vírgula, e valores também evitam vírgula
        if cols.size() < 3:
            continue
        var key := cols[0].strip_edges()
        var pt := cols[1].strip_edges()
        var en := cols[2].strip_edges()
        if key == "":
            continue
        _dict["pt_BR"][key] = pt
        _dict["en_US"][key] = en
    # Fallback en_US.csv individual se strings.csv não tinha en?
    if _dict["en_US"].is_empty() and FileAccess.file_exists("res://localization/en_US.csv"):
        var txt2 := FileAccess.get_file_as_string("res://localization/en_US.csv")
        for line in txt2.split("\n", false):
            if line.begins_with("keys"): continue
            var cols2 := line.split(",", false)
            if cols2.size() >= 2:
                _dict["en_US"][cols2[0].strip_edges()] = cols2[1].strip_edges()

func set_locale(locale: String) -> void:
    var want := locale
    if want == "pt": want = "pt_BR"
    if want == "en": want = "en_US"
    if want not in ["pt_BR", "en_US"]:
        return
    if current_locale == want:
        return
    current_locale = want
    TranslationServer.set_locale(want)
    if GameSave:
        GameSave.data[SAVE_KEY] = want
        GameSave.flush()
    locale_changed.emit(want)
    print("[locale] trocado para %s" % want)

func get_locale() -> String:
    return current_locale

func toggle() -> String:
    set_locale("en_US" if current_locale == "pt_BR" else "pt_BR")
    return current_locale

func tr_key(key: String) -> String:
    # 1 - Nosso dicionário (funciona sem import .translation)
    var table: Dictionary = _dict.get(current_locale, {})
    if table.has(key):
        return str(table[key])
    # 2 - TranslationServer (quando CSV importado gera .translation)
    var ts := TranslationServer.translate(key)
    if ts != key:
        return ts
    return key

func tr_format(key: String, args: Array = []) -> String:
    var base := tr_key(key)
    if args.is_empty():
        return base
    # Usa % formatting simples
    # Suporta "%s" e "%d"
    var out := base
    for a in args:
        # substitui primeiro %s/%d/%0*d
        out = out.replace("%s", str(a)) if "%s" in out else out
        # Para %d e %02d etc, usa String % Array quando possível
    # Fallback: se ainda tem % e args, tenta sprintf
    if "%" in out and not args.is_empty():
        # Tenta usar String.sprintf via % operator com Array
        # GDScript 4: "foo %s" % [val] funciona
        # Aqui usamos via call
        var fmt_args := args
        # se base tem um único placeholder, usa single
        # workaround: usa `out % fmt_args` se fmt_args size 1
        # mas para múltiplos, GDScript precisa de Array
        # Vamos tentar:
        var ok := false
        # Use `out % fmt_args` quando out contém % e fmt_args não vazio
        # Em GDScript, `"a %d b %d" % [1,2]` funciona
        # Não há try, então fazemos simples replace para %d
        for arg in args:
            if "%d" in out:
                out = out.replace("%d", str(int(arg)))
            elif "%02d" in out:
                out = out.replace("%02d", "%02d" % int(arg))
    return out
