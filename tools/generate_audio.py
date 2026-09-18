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

write('click.wav', concat(tone(720,.045,.26),tone(980,.055,.18)))
write('step.wav', concat(tone(105,.055,.18,'noise'), tone(135,.045,.10)))
write('jump.wav', tone(300,.25,.3,bend=1.5))
write('coin.wav', concat(tone(880,.08,.33),tone(1320,.11,.31)))
write('pickup.wav', concat(tone(420,.08,.25),tone(620,.08,.25),tone(930,.15,.22)))
write('hit.wav', concat(tone(120,.16,.45,'noise'),tone(75,.22,.25,'sine')))
write('bus_horn.wav', concat(tone(220,.20,.42),tone(175,.28,.40),tone(220,.14,.35)))
write('bark.wav', concat(tone(180,.09,.5,'noise'),tone(240,.11,.42,'noise'),tone(155,.08,.35,'noise')))
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
print('generated',len(os.listdir(root)),'wav files')
