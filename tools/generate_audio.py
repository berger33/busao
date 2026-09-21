import math, random, wave, os, struct
from pathlib import Path

root = str(Path(__file__).resolve().parents[1] / 'assets' / 'audio')
os.makedirs(root, exist_ok=True)
RATE=22050
random.seed(1337)

def write(name, samples, channels=1):
    path=os.path.join(root,name)
    with wave.open(path,'wb') as w:
        w.setnchannels(channels); w.setsampwidth(2); w.setframerate(RATE)
        frames=bytearray()
        for x in samples:
            if channels==1:
                vals=[x]
            else:
                vals=x if isinstance(x,tuple) else [x,x]
            for v in vals:
                frames += struct.pack('<h', max(-32768,min(32767,int(v*32767))))
        w.writeframes(frames)

def tone(freq,dur,vol=.35,kind='sine',bend=0):
    n=int(RATE*dur); out=[]
    for i in range(n):
        t=i/RATE; env=min(1,t*80)*min(1,max(0,(dur-t)*22))
        f=freq*(1+bend*t/dur)
        if kind=='square': y=1 if math.sin(2*math.pi*f*t)>=0 else -1
        elif kind=='noise': y=random.uniform(-1,1)
        else: y=math.sin(2*math.pi*f*t)
        out.append(y*vol*env)
    return out

def concat(*parts):
    out=[]
    for p in parts: out += p
    return out

# Lote25 — Foley Realista: 4 variações de passo, caramelo real, buzina 2 tons, reverb por clima
def _reverb(samples, delay_ms=110, decay=0.28):
    # simples eco para simular IR de rua
    d = int(RATE * delay_ms / 1000.0)
    out = samples[:]
    for i in range(len(samples)):
        if i >= d:
            out[i] = out[i] + samples[i-d] * decay
    # normaliza
    peak = max(abs(x) for x in out) or 1.0
    if peak > 0.95:
        out = [x * 0.95/peak for x in out]
    return out

def _stereo(samples, pan=0.0):
    # pan -1 esquerda, 1 direita, retorna lista de tuplas
    return [(x * (1-pan)*0.5 + x*0.5, x * (1+pan)*0.5 + x*0.5) for x in samples]

write('click.wav', concat(tone(720,.045,.26),tone(980,.055,.18)))
# 4 variações de passo em superficies (asfalto/calcada/terra/metal) — Foley 105Hz base + reverb curto
step_asfalto = _reverb(concat(tone(105,.055,.18,'noise'), tone(135,.045,.10)), 85, 0.22)
step_calcada = _reverb(concat(tone(125,.055,.16,'noise'), tone(155,.045,.09)), 95, 0.24)
step_terra = _reverb(concat(tone(85,.060,.20,'noise'), tone(110,.045,.12,'noise')), 105, 0.26)
step_metal = _reverb(concat(tone(165,.045,.14,'square'), tone(220,.035,.10,'sine')), 70, 0.20)
write('step.wav', step_asfalto)
write('step_asfalto.wav', step_asfalto)
write('step_calcada.wav', step_calcada)
write('step_terra.wav', step_terra)
write('step_metal.wav', step_metal)
write('jump.wav', tone(300,.25,.3,bend=1.5))
write('coin.wav', concat(tone(880,.08,.33),tone(1320,.11,.31)))
write('pickup.wav', concat(tone(420,.08,.25),tone(620,.08,.25),tone(930,.15,.22)))
write('hit.wav', concat(tone(120,.16,.45,'noise'),tone(75,.22,.25,'sine')))
# buzina 2 tons brasileira (Fá-Mi) com reverb rua
_horn = concat(tone(220,.20,.42),tone(175,.28,.40),tone(220,.14,.35))
write('bus_horn.wav', _reverb(_horn, 120, 0.32))
# latido caramelo SRD realista — 3 camadas noise + formante + reverb curta
_bark_core = concat(tone(180,.09,.5,'noise'),tone(240,.11,.42,'noise'),tone(155,.08,.35,'noise'))
_bark_formant = concat(tone(520,.09,.12,'sine'), tone(780,.09,.10,'sine'))
write('bark.wav', _reverb(concat(_bark_core, _bark_formant), 60, 0.18))
write('shout.wav', concat(tone(310,.10,.22),tone(420,.13,.20),tone(260,.16,.2)))
write('slide.wav', tone(240,.22,.28,'noise'))
write('wall.wav', concat(tone(520,.08,.2),tone(780,.08,.18),tone(1040,.10,.16)))
# UI feedback uses distinct ascending/descending signatures so taps, rewards,
# combos and damage are readable even with the phone screen out of sight.
write('ui_confirm.wav', concat(tone(520,.055,.22), tone(780,.075,.22), tone(1040,.11,.18)))
write('ui_back.wav', concat(tone(620,.06,.18), tone(390,.10,.16)))
write('reward.wav', concat(tone(660,.07,.24), tone(880,.08,.24), tone(1320,.16,.22)))
write('combo.wav', concat(tone(440,.06,.20), tone(660,.06,.22), tone(990,.07,.23), tone(1320,.14,.24)))
write('streak.wav', concat(tone(392,.08,.22), tone(523,.08,.22), tone(659,.08,.22), tone(784,.20,.24)))
write('whoosh.wav', tone(460,.28,.22,'noise',bend=1.8))
write('impact_heavy.wav', concat(tone(92,.18,.45,'noise'), tone(54,.28,.32,'sine'), tone(180,.07,.15,'noise')))
# Lote25 — trovao com IR reverb longa (raio)
_trovao = concat(tone(60,.42,.52,'noise'), tone(35,.68,.44,'noise'), tone(80,.38,.31,'sine'))
write('trovao.wav', _reverb(_trovao, 280, 0.45))

# Four original, low-volume loop beds. Percussive sine/noise patterns keep the
# game lively while remaining tiny and safe to redistribute.
def music(bpm, root_freq, flavor):
    beat=60/bpm; total=8.0; n=int(RATE*total); out=[]
    notes=[0,4,7,11,7,4,2,7] if flavor==0 else ([0,7,5,7,0,9,7,5] if flavor==1 else ([0,3,7,10,7,3,5,7] if flavor==2 else [0,5,7,12,10,7,5,2]))
    for i in range(n):
        t=i/RATE; beat_i=int(t/beat); local=t-beat_i*beat
        note=notes[beat_i%len(notes)]; freq=root_freq*2**(note/12)
        melody=math.sin(2*math.pi*freq*t)*.075*min(1,local*28)*min(1,(beat-local)*18)
        bass=math.sin(2*math.pi*(root_freq/2)*t)*.045
        kick=0
        if local<.055: kick=math.sin(2*math.pi*(110-70*local/.055)*t)*.16*(1-local/.055)
        snare=0
        if beat_i%2==1 and .16<local<.21: snare=random.uniform(-.08,.08)*(1-(local-.16)/.05)
        hat=random.uniform(-.015,.015) if (int(t/(beat/2))%2==1 and local<.035) else 0
        out.append(max(-.8,min(.8,melody+bass+kick+snare+hat)))
    return out
for idx,(bpm,freq,flavor) in enumerate([(112,220,0),(124,196,1),(118,247,2),(108,174,3)]):
    write(['music_city.wav','music_commerce.wav','music_beach.wav','music_terminal.wav'][idx],music(bpm,freq,flavor))
# Auditoria Infra/Audio/Negocios (2026-09-21) — 9 SFX novos, append-only:
# arquivos antigos seguem byte-identicos (mesma seed, mesma ordem anterior).
write('count_beep.wav', tone(880,.12,.30))
write('count_go.wav', concat(tone(880,.09,.30),tone(1320,.28,.34)))
write('victory.wav', concat(tone(523,.12,.30),tone(659,.12,.30),tone(784,.12,.32),tone(1047,.34,.34)))
write('defeat.wav', concat(tone(392,.20,.30),tone(330,.20,.30),tone(262,.22,.30),tone(196,.44,.28)))
write('levelup.wav', concat(tone(660,.07,.26),tone(880,.07,.26),tone(1320,.07,.28),tone(1760,.22,.28)))
write('chest.wav', concat(tone(140,.22,.30,'noise',bend=-0.5),tone(660,.09,.24),tone(990,.20,.24)))
write('purchase.wav', concat(tone(1568,.07,.28),tone(2093,.16,.26),tone(880,.08,.20),tone(1320,.14,.22)))
# portas do busao: jato pneumatico + batida grave
_doors = concat(tone(1200,.28,.20,'noise',bend=-0.7),tone(90,.18,.40,'noise'),tone(65,.24,.30,'sine'))
write('bus_doors.wav', _reverb(_doors, 90, 0.20))
# chuva: 4 s com crossfade nas bordas para loop sem clique
def _rain_loop(dur=4.0):
    n = int(RATE*dur)
    base = [ (random.uniform(-1,1)*0.5 + random.uniform(-1,1)*0.3)*0.16*(0.75+0.25*math.sin(2*math.pi*0.4*i/RATE)) for i in range(n) ]
    xf = int(RATE*0.4)
    out = base[:]
    for i in range(xf):
        k = i/xf
        out[i] = base[n-xf+i]*(1-k) + base[i]*k
    return out
write('rain_loop.wav', _reverb(_rain_loop(), 60, 0.12))

print('generated',len(os.listdir(root)),'wav files')
