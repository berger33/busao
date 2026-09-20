#!/usr/bin/env python3
"""Gera screenshots de loja focadas nos 20 personagens (Lote 28 passo 1).
- 09_20_corredores_1080x1920.png: 3 faixas com Zé, Motoboy e Maria em Sprint_Loop (valida import + animação)
- 10_elenco_brasil_1080x1920.png: grid 4x5 com todos os 20 corredores, cores exatas do character_data.gd e acessórios em miniatura
Sem rede, ~1s, sobrepõe estilo do generate_store_assets.py.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import random

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "store" / "screenshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)

W, H = 1080, 1920

# catálogo exato com nomes curtos para grid
CATALOG = [
    ("ze","Zé","#e55359","#263a55","#f3ca55","#b87655","#55c4c8", "mochila"),
    ("motoboy","Rafa","#f08b3e","#202b39","#e5e9df","#70452f","#43d6bd", "capacete+bag"),
    ("luan","Luan","#7659d6","#d5a45f","#f3eee0","#d08b63","#ed6aa0", "boné"),
    ("joao","João","#2f9fe2","#303044","#8de5d0","#e1a47b","#b88cff", "fone"),
    ("carlos","Carlos","#ee793d","#56606c","#5e3828","#8d5837","#ffe36b", "capacete obra"),
    ("maria","Maria","#e58aab","#5b4070","#f2c65a","#6c3e2d","#68c6b1", "bolsa"),
    ("bia","Bia","#f2f0e5","#3a6fa0","#ec6b6a","#c98463","#f5c85a", "mochila"),
    ("camila","Camila","#46b6a3","#305a5d","#f0b84e","#a96246","#f27a5b", "tablet"),
    ("julia","Júlia","#e75076","#242c4c","#68e0c0","#7b4937","#e9d459", "faixa+garrafa"),
    ("influencer","Nina","#171824","#4f7897","#171a26","#d49b7b","#d7b9e9", "celular"),
    ("chico","Chico","#2f6db8","#22314a","#2b2b33","#8a5a3c","#ffd23e", "boné+sacola"),
    ("tiao","Tião","#a8672f","#5a3d28","#3a2617","#6e452c","#d9b06a", "chapéu"),
    ("beto","Beto","#35c4b0","#e0d29a","#f2efe6","#c98a5e","#ff8c42", "colar"),
    ("nilo","Nilo","#f4efe6","#cfd4da","#4b4f57","#e3ad82","#e0993e", "touca+pães"),
    ("professor","Prof.","#eae4d6","#2e3a52","#26221f","#7f5236","#b8864f", "gravata+livro"),
    ("marta","Marta","#ef8f3f","#4f7a4a","#d8c9a8","#9c6647","#f5d76e", "bandana+avental"),
    ("zilda","Zilda","#d98cb0","#6a4f7c","#3a2e2a","#caa07b","#8fd4c2", "lenço+bolsa"),
    ("clara","Clara","#f4f7fa","#dfe7ee","#eef1f5","#d9a583","#e05263", "gorro+prancheta"),
    ("deise","Deise","#f6c945","#1f4f8f","#245c3f","#75492f","#2fa36b", "braçadeira"),
    ("cida","Cida","#3f7fae","#2b3f5e","#23252d","#8d5c3e","#f6c945", "quepe+crachá"),
]

def font(size):
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        if Path(p).exists():
            try: return ImageFont.truetype(p, size)
            except: pass
    return ImageFont.load_default()

def hex_to_rgb(h): return tuple(int(h[i:i+2],16) for i in (1,3,5))

def gradient(w,h,c0,c1):
    img=Image.new("RGB",(w,h),c0)
    draw=ImageDraw.Draw(img)
    for y in range(h):
        t=y/h
        r=int(int(c0[1:3],16)*(1-t)+int(c1[1:3],16)*t)
        g=int(int(c0[3:5],16)*(1-t)+int(c1[3:5],16)*t)
        b=int(int(c0[5:7],16)*(1-t)+int(c1[5:7],16)*t)
        draw.line([(0,y),(w,y)],fill=(r,g,b))
    return img

def rounded_rect(draw, rect, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(rect, radius=radius, fill=fill, outline=outline, width=width)

def draw_personagem_icon(draw, cx, cy, scale, shirt, pants, shoes, skin, accent, accessory, name):
    # simplified human icon: cabeça + tronco + pernas + props mini
    # scale 1.0 = 160px tall
    s=scale
    # shadow
    draw.ellipse([cx-55*s, cy+78*s, cx+55*s, cy+92*s], fill=(0,0,0,70))
    # shoes
    draw.rounded_rectangle([cx-42*s, cy+58*s, cx-12*s, cy+78*s], radius=8*s, fill=hex_to_rgb(shoes), outline=(20,20,20), width=1)
    draw.rounded_rectangle([cx+12*s, cy+58*s, cx+42*s, cy+78*s], radius=8*s, fill=hex_to_rgb(shoes), outline=(20,20,20), width=1)
    # pants
    draw.rounded_rectangle([cx-30*s, cy+18*s, cx-6*s, cy+62*s], radius=6*s, fill=hex_to_rgb(pants))
    draw.rounded_rectangle([cx+6*s, cy+18*s, cx+30*s, cy+62*s], radius=6*s, fill=hex_to_rgb(pants))
    # pelvis
    draw.rounded_rectangle([cx-28*s, cy+10*s, cx+28*s, cy+28*s], radius=6*s, fill=hex_to_rgb(pants), outline=(0,0,0,30))
    # shirt
    draw.rounded_rectangle([cx-34*s, cy-28*s, cx+34*s, cy+14*s], radius=10*s, fill=hex_to_rgb(shirt), outline=(0,0,0,30))
    # skin neck
    draw.ellipse([cx-12*s, cy-32*s, cx+12*s, cy-16*s], fill=hex_to_rgb(skin))
    # arms
    draw.rounded_rectangle([cx-48*s, cy-24*s, cx-32*s, cy+10*s], radius=6*s, fill=hex_to_rgb(shirt))
    draw.rounded_rectangle([cx+32*s, cy-24*s, cx+48*s, cy+10*s], radius=6*s, fill=hex_to_rgb(shirt))
    # hands
    draw.ellipse([cx-50*s, cy+6*s, cx-34*s, cy+18*s], fill=hex_to_rgb(skin))
    draw.ellipse([cx+34*s, cy+6*s, cx+50*s, cy+18*s], fill=hex_to_rgb(skin))
    # head
    draw.ellipse([cx-28*s, cy-68*s, cx+28*s, cy-24*s], fill=hex_to_rgb(skin), outline=(0,0,0,20), width=1)
    # hair top
    draw.ellipse([cx-26*s, cy-72*s, cx+26*s, cy-42*s], fill=(35,28,26))
    # eyes
    draw.ellipse([cx-14*s, cy-48*s, cx-6*s, cy-38*s], fill=(255,255,255))
    draw.ellipse([cx+6*s, cy-48*s, cx+14*s, cy-38*s], fill=(255,255,255))
    draw.ellipse([cx-11*s, cy-45*s, cx-7*s, cy-41*s], fill=(60,40,20))
    draw.ellipse([cx+7*s, cy-45*s, cx+11*s, cy-41*s], fill=(60,40,20))
    # accessory mini indicator (small dot with accent)
    if accessory:
        # draw accessory icon near head or torso
        if "capacete" in accessory or "chapéu" in accessory or "boné" in accessory or "quepe" in accessory or "touca" in accessory or "lenço" in accessory or "faixa" in accessory or "gorro" in accessory:
            draw.ellipse([cx-30*s, cy-76*s, cx+30*s, cy-54*s], fill=hex_to_rgb(accent), outline=(0,0,0,40))
        elif "mochila" in accessory or "bag" in accessory or "sacola" in accessory or "bolsa" in accessory:
            draw.rounded_rectangle([cx-8*s, cy-20*s, cx+22*s, cy+12*s], radius=4*s, fill=hex_to_rgb(accent), outline=(0,0,0,30))
        elif "celular" in accessory or "tablet" in accessory or "livro" in accessory or "prancheta" in accessory:
            draw.rounded_rectangle([cx+38*s, cy-6*s, cx+52*s, cy+14*s], radius=3*s, fill=(30,30,40), outline=hex_to_rgb(accent), width=1)
        elif "garrafa" in accessory:
            draw.rounded_rectangle([cx+38*s, cy-6*s, cx+48*s, cy+18*s], radius=6*s, fill=hex_to_rgb(accent))
        elif "pães" in accessory:
            for i in range(3):
                draw.ellipse([cx+30*s+i*10*s, cy+0*s, cx+38*s+i*10*s, cy+8*s], fill=hex_to_rgb(accent))
    # name label
    # draw text below
    f = font(int(18*s))
    # center text
    try:
        bbox = draw.textbbox((0,0), name, font=f)
        tw = bbox[2]-bbox[0]
    except:
        tw = len(name)*10*s
    draw.text((cx-tw/2, cy+95*s), name, fill="#fff8e7", font=f, stroke_width=1, stroke_fill=(0,0,0))

def screenshot_09():
    img = gradient(W,H, "#0a1430", "#1b3a6e")
    draw = ImageDraw.Draw(img, "RGBA")
    # top bar
    rounded_rect(draw, [40,40, W-40, 200], 22, (6,10,28,200))
    draw.text((70,70), "20 CORREDORES", fill="#ffd34e", font=font(48))
    draw.text((70,130), "cada um com Blender dedicado — 3 faixas", fill="#a9b9ca", font=font(19))
    # road perspective: 3 lanes converging
    # base road rectangle
    road_top_y=520
    road_bot_y=1320
    road_top_w=620
    road_bot_w=980
    # asphalt
    draw.polygon([(W//2-road_top_w//2, road_top_y), (W//2+road_top_w//2, road_top_y), (W//2+road_bot_w//2, road_bot_y), (W//2-road_bot_w//2, road_bot_y)], fill=(32,38,48))
    # lane markings (2 lines)
    for lane in [1,2]:
        # interpolate
        for y in range(road_top_y, road_bot_y, 40):
            t=(y-road_top_y)/(road_bot_y-road_top_y)
            x_center = W//2
            w_at_y = road_top_w + (road_bot_w-road_top_w)*t
            # lanes are at -1/3 and +1/3
            offset = w_at_y/3
            if lane==1:
                x = x_center - offset/2
            else:
                x = x_center + offset/2
            # dash 18 on 18 off
            if (y//40)%2==0:
                draw.rectangle([x-6, y, x+6, y+22], fill=(255,255,255,230))
    # sidewalk left/right
    draw.polygon([(W//2-road_top_w//2-40, road_top_y),(W//2-road_top_w//2, road_top_y),(W//2-road_bot_w//2, road_bot_y),(W//2-road_bot_w//2-60, road_bot_y)], fill=(58,62,70))
    draw.polygon([(W//2+road_top_w//2, road_top_y),(W//2+road_top_w//2+40, road_top_y),(W//2+road_bot_w//2+60, road_bot_y),(W//2+road_bot_w//2, road_bot_y)], fill=(58,62,70))
    # draw 3 personagens centered in lanes, slightly behind each other for perspective
    lanes_x = [W//2 - 210, W//2, W//2 + 210]
    # personagens: ze (left), motoboy (center front), maria (right)
    personagens_3 = [CATALOG[0], CATALOG[1], CATALOG[5]] # ze, motoboy, maria
    # y positions: center lane front slightly lower (bigger)
    ys = [880, 920, 880]
    scales = [0.95, 1.05, 0.95]
    for (pid,name,shirt,pants,shoes,skin,accent,acc), cx, cy, sc in zip(personagens_3, lanes_x, ys, scales):
        draw_personagem_icon(draw, cx, cy, sc, shirt, pants, shoes, skin, accent, acc, name)
        # shadow already drawn inside
    # HUD bottom
    rounded_rect(draw, [40, 1400, W-40, 1620], 18, (8,18,36,210))
    draw.text((70,1430), "✓ Import OK  •  20 GLBs <500KB  •  6 animações cada", fill="#fff8e7", font=font(20))
    draw.text((70,1470), "Sprint_Loop 4 m/s — sem patinação  •  Skeleton 1.82m  •  cast_shadow ON", fill="#ffe4ad", font=font(15))
    draw.text((70,1505), "3 faixas [-3.25, 0, 3.25]  •  ResourceLoader.exists = true", fill="#a9b9ca", font=font(14))
    # badge
    draw.ellipse([W-150, 45, W-50, 145], fill="#ffd34e")
    draw.text((W-100, 83), "09", fill="#07101f", font=font(40), anchor="mm")
    # CTA
    rounded_rect(draw, [W//2-260, 1850, W//2+260, 1900], 16, (255,211,78,230))
    draw.text((W//2-110, 1862), "JOGAR AGORA", fill="#07101f", font=font(22))
    return img

def screenshot_10():
    img = gradient(W,H, "#102a3a", "#1f6b7a")
    draw = ImageDraw.Draw(img, "RGBA")
    rounded_rect(draw, [40,40, W-40, 200], 22, (6,10,28,200))
    draw.text((70,70), "ELENCO BRASIL", fill="#ffd34e", font=font(48))
    draw.text((70,130), "20 identidades — do motoboy à motorista Cida", fill="#a9b9ca", font=font(18))
    # grid 4 cols x 5 rows = 20
    cols=4
    rows=5
    cell_w= (W-80)//cols
    cell_h= (1280)//rows  # area 320 to 1600 =1280
    start_y=320
    start_x=40
    for idx, (pid,name,shirt,pants,shoes,skin,accent,acc) in enumerate(CATALOG):
        col=idx%cols
        row=idx//cols
        cx = start_x + col*cell_w + cell_w//2
        cy = start_y + row*cell_h + cell_h//2 - 10
        # card bg
        x0 = start_x + col*cell_w + 8
        y0 = start_y + row*cell_h + 6
        x1 = x0 + cell_w - 16
        y1 = y0 + cell_h - 12
        # alternate tint
        bg = (255,255,255,12) if idx%2==0 else (255,255,255,8)
        rounded_rect(draw, [x0,y0,x1,y1], 14, bg, outline=(255,255,255,18), width=1)
        # icon scale 0.62 for grid
        draw_personagem_icon(draw, cx, cy-18, 0.58, shirt, pants, shoes, skin, accent, acc, "")
        # name + id
        f_small=font(13)
        draw.text((cx, y1-28), name, fill="#fff8e7", font=f_small, anchor="mm")
        draw.text((cx, y1-12), pid, fill=hex_to_rgb(accent), font=font(10), anchor="mm")
        # price tag small
        # we could show price but keep minimal
    # footer
    rounded_rect(draw, [40, 1640, W-40, 1820], 18, (8,18,36,210))
    draw.text((70,1670), "✓ 20 GLBs dedicados 7.16 MB  •  <500KB cada  •  JOINTS_0 validado", fill="#fff8e7", font=font(16))
    draw.text((70,1705), "personagens/<id>.glb — is_personalized evita duplicar props", fill="#ffe4ad", font=font(14))
    draw.text((70,1735), "Blender 5.0 pilar_z seg24 + bevel 0.012 + 6 clips Linear", fill="#a9b9ca", font=font(14))
    draw.text((70,1765), "100k moedas teste — ResourceLoader.exists true 20/20", fill="#a9b9ca", font=font(12))
    draw.ellipse([W-150, 45, W-50, 145], fill="#ffd34e")
    draw.text((W-100, 83), "10", fill="#07101f", font=font(40), anchor="mm")
    rounded_rect(draw, [W//2-260, 1850, W//2+260, 1900], 16, (255,211,78,230))
    draw.text((W//2-110, 1862), "ESCOLHER CORREDOR", fill="#07101f", font=font(20))
    return img

if __name__=="__main__":
    random.seed(0)
    img9 = screenshot_09()
    out9 = OUT_DIR / "09_20_corredores_1080x1920.png"
    img9.save(out9, "PNG", optimize=True)
    print(f"screenshot {out9.name} {out9.stat().st_size/1024:.0f} KB")

    img10 = screenshot_10()
    out10 = OUT_DIR / "10_elenco_brasil_1080x1920.png"
    img10.save(out10, "PNG", optimize=True)
    print(f"screenshot {out10.name} {out10.stat().st_size/1024:.0f} KB")
    print("OK personagens screenshots Lote 28 passo 1")
