extends Node
## InAppUpdateManager — Lote 18 (Vitrine)
## Mock-first: Play Core In-App Update (flexível / imediato) para AAB.
## Contrato: check_for_update(), start_flexible_update(), complete_flexible_update(), is_update_available()
## Nativo: GodotInAppUpdate / PlayCore quando singleton presente.

signal update_available(version_code: int)
signal update_not_available
signal update_downloaded
signal update_failed(reason: String)
signal update_installed

const FLEXIBLE := 0
const IMMEDIATE := 1

var _native := false
var _available := false
var _downloaded := false
var _mock_timer: float = 0.0
var _update_type: int = FLEXIBLE
var _version_code: int = 2

func _ready() -> void:
    process_mode = Node.PROCESS_MODE_ALWAYS
    _native = _detect_native()
    print("[update] pronto nativo=%s" % str(_native))
    # Check automático 1.5 s após boot (não bloqueia)
    call_deferred("_auto_check")

func _detect_native() -> bool:
    if Engine.has_singleton("GodotInAppUpdate") or Engine.has_singleton("InAppUpdate"):
        return true
    if ClassDB.class_exists("GodotInAppUpdate"):
        return true
    if Engine.has_singleton("PlayCore"):
        return true
    return false

func _auto_check() -> void:
    await get_tree().create_timer(1.5).timeout
    check_for_update()

func check_for_update() -> void:
    if _native:
        print("[update] check nativo…")
        # GodotInAppUpdate.checkForUpdate()
        _mock_timer = 0.9
    else:
        print("[update] check mock…")
        _mock_timer = 0.7

func _process(delta: float) -> void:
    if _mock_timer > 0.0:
        _mock_timer -= delta
        if _mock_timer <= 0.0:
            _mock_timer = 0.0
            _finish_mock_check()

func _finish_mock_check() -> void:
    # Mock: considera update disponível se version_code local < 2 e random 1/3
    # Para teste determinístico em Test Lab, sempre retorna disponível no primeiro check
    _available = true
    _version_code = 2
    update_available.emit(_version_code)
    print("[update] mock update disponível v%d (flexível)" % _version_code)
    # Auto inicia flexível após 0.5 s se consent
    await get_tree().create_timer(0.5).timeout
    start_flexible_update()

func is_update_available() -> bool:
    return _available

func is_update_downloaded() -> bool:
    return _downloaded

func start_flexible_update() -> void:
    if not _available:
        update_failed.emit("no_update")
        return
    _update_type = FLEXIBLE
    if _native:
        print("[update] start flexível nativo…")
        # GodotInAppUpdate.startFlexibleUpdate()
        _mock_timer = 2.2  # download simulado
    else:
        print("[update] start flexível mock…")
        _mock_timer = 1.4
        # Simula download
        await get_tree().create_timer(1.4).timeout
        _downloaded = true
        update_downloaded.emit()
        print("[update] mock flexível baixado — pronto para instalar (snackbar)")
        # Auto completa após 1 s para Test Lab não travar
        await get_tree().create_timer(1.0).timeout
        complete_flexible_update()

func complete_flexible_update() -> void:
    if not _downloaded:
        update_failed.emit("not_downloaded")
        return
    if _native:
        print("[update] complete nativo…")
        # GodotInAppUpdate.completeUpdate()
    else:
        print("[update] complete mock — reiniciaria app (Test Lab)")
    update_installed.emit()
    _available = false
    _downloaded = false

func start_immediate_update() -> void:
    _update_type = IMMEDIATE
    if _native:
        print("[update] imediato nativo…")
    else:
        print("[update] imediato mock — bloquearia UX até instalar")
        update_failed.emit("mock_immediate")
