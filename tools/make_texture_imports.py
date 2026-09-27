#!/usr/bin/env python3
"""Cria o .import das texturas novas, no mesmo formato que o Godot geraria.

O nome do arquivo em .godot/imported/ e <arquivo>-<md5 do caminho res://>.ctex
(conferido contra os .import ja existentes no repo), e o uid segue a
codificacao base-36 a-z0-9 do ResourceUID do Godot. Assim da para versionar a
textura nova sem precisar abrir o editor.

Uso:  python3 tools/make_texture_imports.py
"""
import hashlib, os, random, re, glob
TEMPLATE = open('assets/textures/asfalto_realista.png.import').read()
used = set()
for f in glob.glob('**/*.import', recursive=True) + glob.glob('**/*.uid', recursive=True):
    used |= set(re.findall(r'uid://([a-z0-9]+)', open(f, errors='ignore').read()))
def new_uid():
    while True:
        n = random.getrandbits(59); t = ''
        while n:
            c = n % 36
            t = (chr(ord('a') + c) if c < 26 else chr(ord('0') + c - 26)) + t
            n //= 36
        if t and t not in used:
            used.add(t); return t
new = [p for p in sorted(glob.glob('assets/textures/*.png')) if not os.path.exists(p + '.import')]
for path in new:
    res = 'res://' + path; name = os.path.basename(path)
    dest = f'res://.godot/imported/{name}-{hashlib.md5(res.encode()).hexdigest()}.ctex'
    txt = re.sub(r'uid="uid://[a-z0-9]+"', f'uid="uid://{new_uid()}"', TEMPLATE)
    txt = re.sub(r'^path=".*"$', f'path="{dest}"', txt, flags=re.M)
    txt = re.sub(r'^source_file=".*"$', f'source_file="{res}"', txt, flags=re.M)
    txt = re.sub(r'^dest_files=\[.*\]$', f'dest_files=["{dest}"]', txt, flags=re.M)
    if 'normal' in name:
        txt = re.sub(r'^compress/normal_map=\d+$', 'compress/normal_map=1', txt, flags=re.M)
    open(path + '.import', 'w').write(txt); print('  +', path + '.import')
print(len(new), 'novos .import')
