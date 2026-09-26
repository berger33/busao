extends Node
## Mixagem local do jogo: pequenos WAVs proprios, cacheados e com pool para
## que moeda, UI e impactos possam soar juntos sem cortar uns aos outros.
##
## Auditoria Infra/Audio/Negocios (2026-09-21):
## - canal dedicado de ALERTAS (horn, count_go, victory, defeat, trovao):
##   spam de moeda nunca mais rouba a voz de um aviso de gameplay;
## - buses Music/SFX criados em codigo + ducking (-8 dB na musica a cada alerta);
## - unmute retoma a faixa do capitulo (antes voltava sempre a faixa 0);
## - loops de ambiente (rain_loop) com start/stop dedicados.

const SFX := {
    "click": "res://assets/audio/click.wav",
    "ui_confirm": "res://assets/audio/ui_confirm.wav",
    "ui_back": "res://assets/audio/ui_back.wav",
    "step": "res://assets/audio/step.wav",
    "step_asfalto": "res://assets/audio/step_asfalto.wav",
    "step_calcada": "res://assets/audio/step_calcada.wav",
    "step_metal": "res://assets/audio/step_metal.wav",
    "step_terra": "res://assets/audio/step_terra.wav",
    "trovao": "res://assets/audio/trovao.wav",
    "jump": "res://assets/audio/jump.wav",
    "coin": "res://assets/audio/coin.wav",
    "combo": "res://assets/audio/combo.wav",
    "pickup": "res://assets/audio/pickup.wav",
    "reward": "res://assets/audio/reward.wav",
    "streak": "res://assets/audio/streak.wav",
    "hit": "res://assets/audio/hit.wav",
    "impact_heavy": "res://assets/audio/impact_heavy.wav",
    "horn": "res://assets/audio/bus_horn.wav",
    "bark": "res://assets/audio/bark.wav",
    "shout": "res://assets/audio/shout.wav",
    "slide": "res://assets/audio/slide.wav",
    "whoosh": "res://assets/audio/whoosh.wav",
    "wall": "res://assets/audio/wall.wav",
    "count_beep": "res://assets/audio/count_beep.wav",
    "count_go": "res://assets/audio/count_go.wav",
    "victory": "res://assets/audio/victory.wav",
    "defeat": "res://assets/audio/defeat.wav",
    "levelup": "res://assets/audio/levelup.wav",
    "chest": "res://assets/audio/chest.wav",
    "purchase": "res://assets/audio/purchase.wav",
    "bus_doors": "res://assets/audio/bus_doors.wav",
    "rain_loop": "res://assets/audio/rain_loop.wav",
}
const MUSIC := [
    "res://assets/audio/music_city.wav",
    "res://assets/audio/music_commerce.wav",
    "res://assets/audio/music_beach.wav",
    "res://assets/audio/music_terminal.wav",
]
# Alertas de gameplay: voz dedicada, nunca preemptada pelo pool.
const ALERTS := ["horn", "count_go", "victory", "defeat", "trovao", "levelup"]
const SFX_POOL_SIZE := 8
const MUSIC_VOLUME_DB := -14.0
const DUCK_VOLUME_DB := -22.0
const DUCK_SECONDS := 0.6

var sfx_players: Array[AudioStreamPlayer] = []
var sfx_cache: Dictionary = {}
var sfx_cursor := 0
var alert_player: AudioStreamPlayer
var ambient_player: AudioStreamPlayer
var music_player: AudioStreamPlayer
var music_cache: Dictionary = {}
var muted := false

var _last_music_group := 0
var _duck_tween: Tween
var _ambient_id := ""

func _ready() -> void:
    process_mode = Node.PROCESS_MODE_ALWAYS
    muted = bool(GameSave.data.get("audio_muted", false))
    _ensure_buses()
    for i in SFX_POOL_SIZE:
        var audio := AudioStreamPlayer.new()
        audio.name = "SFX_%02d" % i
        audio.bus = &"SFX"
        add_child(audio)
        sfx_players.append(audio)
    alert_player = AudioStreamPlayer.new()
    alert_player.name = "Alert"
    alert_player.bus = &"SFX"
    add_child(alert_player)
    ambient_player = AudioStreamPlayer.new()
    ambient_player.name = "Ambient"
    ambient_player.bus = &"SFX"
    add_child(ambient_player)
    music_player = AudioStreamPlayer.new()
    music_player.name = "Music"
    music_player.bus = &"Music"
    music_player.volume_db = MUSIC_VOLUME_DB
    add_child(music_player)

func _ensure_buses() -> void:
    for bus_name in [&"Music", &"SFX"]:
        if AudioServer.bus_count > 0 and AudioServer.get_bus_index(bus_name) == -1:
            AudioServer.add_bus()
            AudioServer.set_bus_name(AudioServer.bus_count - 1, bus_name)
            AudioServer.set_bus_send(AudioServer.bus_count - 1, &"Master")

func _stream_for(id: String) -> AudioStream:
    var stream = sfx_cache.get(id)
    if stream != null:
        return stream as AudioStream
    stream = load(SFX[id]) as AudioStream
    if stream == null:
        return null
    sfx_cache[id] = stream
    return stream as AudioStream

func play_sfx(id: String, volume_db := 0.0, pitch_scale := 1.0) -> void:
    if muted or not SFX.has(id) or sfx_players.is_empty():
        return
    if id in ALERTS:
        play_alert(id, volume_db, pitch_scale)
        return
    var stream := _stream_for(id)
    if stream == null:
        return
    var audio: AudioStreamPlayer = sfx_players[sfx_cursor]
    sfx_cursor = (sfx_cursor + 1) % sfx_players.size()
    audio.stream = stream
    audio.volume_db = volume_db
    audio.pitch_scale = pitch_scale
    audio.play()

func play_alert(id: String, volume_db := 0.0, pitch_scale := 1.0) -> void:
    # Voz dedicada: alertas nunca disputam o pool com moeda/passos.
    if muted or not SFX.has(id) or alert_player == null:
        return
    var stream := _stream_for(id)
    if stream == null:
        return
    alert_player.stream = stream
    alert_player.volume_db = volume_db
    alert_player.pitch_scale = pitch_scale
    alert_player.play()
    _duck_music()

func _duck_music() -> void:
    if music_player == null or not music_player.playing:
        return
    if _duck_tween and _duck_tween.is_valid():
        _duck_tween.kill()
    music_player.volume_db = DUCK_VOLUME_DB
    _duck_tween = create_tween()
    _duck_tween.tween_interval(DUCK_SECONDS)
    _duck_tween.tween_property(music_player, "volume_db", MUSIC_VOLUME_DB, 0.4)

func play_music(group: int) -> void:
    var index := clampi(group, 0, MUSIC.size() - 1)
    _last_music_group = index
    if muted or music_player == null:
        return
    var stream = music_cache.get(index)
    if stream == null:
        stream = load(MUSIC[index]) as AudioStream
        if stream == null:
            return
        music_cache[index] = stream
    if music_player.stream == stream and music_player.playing:
        return
    music_player.stream = stream
    var wav := stream as AudioStreamWAV
    if wav:
        wav.loop_mode = AudioStreamWAV.LOOP_FORWARD
        wav.loop_begin = 0
        wav.loop_end = int(wav.get_length() * wav.mix_rate)
    music_player.volume_db = MUSIC_VOLUME_DB - 10.0
    music_player.play()
    var tween := create_tween()
    tween.tween_property(music_player, "volume_db", MUSIC_VOLUME_DB, 0.35)

func start_ambient(id: String, volume_db := -12.0) -> void:
    # Loop de ambiente (chuva): player proprio, sem roubar voz de nada.
    if ambient_player == null or not SFX.has(id):
        return
    if _ambient_id == id and ambient_player.playing:
        return
    var stream := _stream_for(id)
    if stream == null:
        return
    var wav := stream as AudioStreamWAV
    if wav:
        wav.loop_mode = AudioStreamWAV.LOOP_FORWARD
        wav.loop_begin = 0
        wav.loop_end = int(wav.get_length() * wav.mix_rate)
    _ambient_id = id
    ambient_player.stream = stream
    ambient_player.volume_db = volume_db if not muted else -80.0
    ambient_player.play()

func stop_ambient() -> void:
    _ambient_id = ""
    if ambient_player:
        ambient_player.stop()

func toggle_mute() -> void:
    muted = not muted
    GameSave.data["audio_muted"] = muted
    GameSave.flush()
    if muted:
        if music_player:
            music_player.stop()
        stop_ambient()
    else:
        play_music(_last_music_group)
