extends Node
## Mixagem local do jogo: pequenos WAVs próprios, cacheados e com pool para
## que moeda, UI e impactos possam soar juntos sem cortar uns aos outros.

const SFX := {
    "click": "res://assets/audio/click.wav",
    "ui_confirm": "res://assets/audio/ui_confirm.wav",
    "ui_back": "res://assets/audio/ui_back.wav",
    "step": "res://assets/audio/step.wav",
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
    "wall": "res://assets/audio/wall.wav"
}
const MUSIC := [
    "res://assets/audio/music_city.wav",
    "res://assets/audio/music_commerce.wav",
    "res://assets/audio/music_beach.wav",
    "res://assets/audio/music_terminal.wav"
]
const SFX_POOL_SIZE := 8

var sfx_players: Array[AudioStreamPlayer] = []
var sfx_cache: Dictionary = {}
var sfx_cursor := 0
var music_player: AudioStreamPlayer
var music_cache: Dictionary = {}
var muted := false

func _ready() -> void:
    process_mode = Node.PROCESS_MODE_ALWAYS
    muted = bool(GameSave.data.get("audio_muted", false))
    for i in SFX_POOL_SIZE:
        var audio := AudioStreamPlayer.new()
        audio.name = "SFX_%02d" % i
        add_child(audio)
        sfx_players.append(audio)
    music_player = AudioStreamPlayer.new()
    music_player.name = "Music"
    music_player.volume_db = -14.0
    add_child(music_player)

func play_sfx(id: String, volume_db := 0.0, pitch_scale := 1.0) -> void:
    if muted or not SFX.has(id) or sfx_players.is_empty():
        return
    var stream = sfx_cache.get(id)
    if stream == null:
        stream = load(SFX[id]) as AudioStream
        if stream == null:
            return
        sfx_cache[id] = stream
    var audio: AudioStreamPlayer = sfx_players[sfx_cursor]
    sfx_cursor = (sfx_cursor + 1) % sfx_players.size()
    audio.stream = stream
    audio.volume_db = volume_db
    audio.pitch_scale = pitch_scale
    audio.play()

func play_music(group: int) -> void:
    if muted or music_player == null:
        return
    var index := clampi(group, 0, MUSIC.size() - 1)
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
    music_player.volume_db = -24.0
    music_player.play()
    var tween := create_tween()
    tween.tween_property(music_player, "volume_db", -14.0, 0.35)

func toggle_mute() -> void:
    muted = not muted
    GameSave.data["audio_muted"] = muted
    GameSave.flush()
    if muted and music_player:
        music_player.stop()
    elif not muted:
        play_music(0)
