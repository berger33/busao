#!/usr/bin/env python3
"""Gera assets de loja para Lote 18 Vitrine — screenshots 1080x1920, feature 1024x500, storyboard 6 clips.
Determinístico, sem rede, ~2s em CPU.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import hashlib, random

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "store"
SCREENSHOTS = STORE / "screenshots"
VIDEO = STORE / "video"

W, H = 1080, 1920
FEATURE_W, FEATURE_H = 1024, 500

PALETTES = [
    ("#08152f", "#173c5a", "#ffd34e", "CORRE PRO PONTO", "1 — Caramelo no ponto"),
    ("#1a2a45", "#2c9dc1", "#fff8e7", "ÔNIBUS AMARELO", "2 — Pegue o busão"),
    ("#2b1a2f", "#d65b75", "#ffe4ad", "TRÂNSITO BRASILEIRO", "3 — Desvie do tráfego"),
    ("#1f3a2a", "#54d18b", "#fff8e7", "CALÇADA VIVA", "4 — Pedestres e atalhos"),
    ("#2f2a1f", "#f2635e", "#ffd34e", "DASH INVENCÍVEL", "5 — Toque para dash"),
    ("#0f2a3a", "#63c8ed", "#fff8e7", "ENDLESS LIBERADO", "6 — Até onde você vai?"),
    ("#1a1f3a", "#ac8cff", "#fff8e7", "50 FASES", "7 — 5 capítulos brasileiros"),
    ("#2a3a1f", "#ff7ab8", "#fff8e7", "Rubi & Baú Diário", "8 — Economia 2ª moeda"),
]

FEATURE_TEXT = "CORRE PRO PONTO"
FEATURE_SUB = "runner 3D brasileiro  •  50 fases  •  20 corredores  •  Endless"

def font(size):
    # Tenta DejaVu, fallback bitmap
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        if Path(p).exists():
            try: return ImageFont.truetype(p, size)
            except: pass
    return ImageFont.load_default()

def gradient(w,h, c0,c1):
    img = Image.new("RGB", (w,h), c0)
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        r = int(int(c0[1:3],16)*(1-t) + int(c1[1:3],16)*t)
        g = int(int(c0[3:5],16)*(1-t) + int(c1[3:5],16)*t)
        b = int(int(c0[5:7],16)*(1-t) + int(c1[5:7],16)*t)
        draw.line([(0,y),(w,y)], fill=(r,g,b))
    return img

def rounded_rect(draw, rect, radius, fill):
    x0,y0,x1,y1 = rect
    draw.rounded_rectangle(rect, radius=radius, fill=fill)

def make_screenshot(idx, c0,c1, accent, title, subtitle):
    img = gradient(W,H, c0,c1)
    draw = ImageDraw.Draw(img, "RGBA")
    # decor circles
    for i in range(7):
        x = 80 + i*150 + random.randint(-20,20)
        y = 900 - (i%3)*80 + random.randint(-15,15)
        r = 80 + random.randint(-10,10)
        draw.ellipse([x-r,y-r,x+r,y+r], fill=(*hex_to_rgb(accent), 28))
    # top bar
    rounded_rect(draw, [40,40, W-40, 180], 22, (4,8,23, 190))
    draw.text((70,70), title, fill=accent, font=font(46))
    draw.text((70,125), subtitle, fill="#a9b9ca", font=font(18))
    # mock HUD
    rounded_rect(draw, [40, 1600, W-40, 1820], 18, (8,18,36, 210))
    draw.text((70,1630), "★ 120 / 150  •  R$ 480  •  Rubi 12", fill="#fff8e7", font=font(20))
    draw.text((70,1670), "50 FASES  •  ENDLESS  •  3 FAIXAS", fill="#ffe4ad", font=font(16))
    # CTA button
    rounded_rect(draw, [W//2-260, 1850, W//2+260, 1900], 16, hex_to_rgba(accent, 230))
    draw.text((W//2-110, 1865), "JOGAR AGORA", fill="#07101f", font=font(22))
    # bus silhouette (simple rect + circles)
    bus_y = 700
    draw.rounded_rectangle([200, bus_y, 880, bus_y+220], radius=18, fill="#ffb83e", outline="#8a5a12", width=4)
    draw.rounded_rectangle([220, bus_y+20, 420, bus_y+90], radius=8, fill="#0b1224")
    draw.rounded_rectangle([440, bus_y+20, 640, bus_y+90], radius=8, fill="#0b1224")
    draw.ellipse([260, bus_y+170, 340, bus_y+210], fill="#1a1a1a")
    draw.ellipse([620, bus_y+170, 700, bus_y+210], fill="#1a1a1a")
    draw.text((360, bus_y+110), "CORRE PRO PONTO", fill="#07101f", font=font(20))
    # number badge
    draw.ellipse([W-140, 40, W-50, 130], fill=accent)
    draw.text((W-110, 68), f"{idx}", fill="#07101f", font=font(36), anchor="mm")
    return img

def slugify(s: str) -> str:
    repl = str.maketrans({"á":"a","à":"a","ã":"a","â":"a","é":"e","ê":"e","í":"i","ó":"o","ô":"o","õ":"o","ú":"u","ü":"u","ç":"c","Á":"a","À":"a","Ã":"a","Â":"a","É":"e","Ê":"e","Í":"i","Ó":"o","Ô":"o","Õ":"o","Ú":"u","Ü":"u","Ç":"c","&":""})
    t = s.translate(repl).lower().replace(" ", "_")
    while "__" in t:
        t = t.replace("__", "_")
    return t.strip("_")

def hex_to_rgb(h): return tuple(int(h[i:i+2],16) for i in (1,3,5))
def hex_to_rgba(h,a=255):
    r,g,b=hex_to_rgb(h)
    return (r,g,b,a)

def make_feature():
    img = gradient(FEATURE_W, FEATURE_H, "#08152f", "#1a6a9a")
    draw = ImageDraw.Draw(img, "RGBA")
    # faixa amarela diagonal
    draw.polygon([(0,280),(FEATURE_W,220),(FEATURE_W,320),(0,380)], fill="#ffd34e")
    # ônibus amarelo central
    draw.rounded_rectangle([FEATURE_W//2-260, 150, FEATURE_W//2+260, 360], radius=16, fill="#ffb83e", outline="#7a4a08", width=3)
    draw.rounded_rectangle([FEATURE_W//2-240, 170, FEATURE_W//2-80, 240], radius=8, fill="#08152f")
    draw.rounded_rectangle([FEATURE_W//2-60, 170, FEATURE_W//2+100, 240], radius=8, fill="#08152f")
    draw.ellipse([FEATURE_W//2-210, 315, FEATURE_W//2-150, 345], fill="#111")
    draw.ellipse([FEATURE_W//2+150, 315, FEATURE_W//2+210, 345], fill="#111")
    # logo
    draw.text((FEATURE_W//2, 110), FEATURE_TEXT, fill="#fff8e7", font=font(44), anchor="mm")
    draw.text((FEATURE_W//2, 145), FEATURE_SUB, fill="#ffe4ad", font=font(14), anchor="mm")
    # badge 50 fases + 20 corredores (Lote 28)
    draw.rounded_rectangle([FEATURE_W-180, 20, FEATURE_W-20, 70], radius=10, fill="#07101f")
    draw.text((FEATURE_W-100, 45), "50 FASES", fill="#ffd34e", font=font(14), anchor="mm")
    draw.rounded_rectangle([20, 20, 180, 70], radius=10, fill="#ffd34e")
    draw.text((100, 45), "20 CORREDORES", fill="#07101f", font=font(13), anchor="mm")
    return img

def make_clip(idx, title, desc, color):
    w,h = 1280,720
    c0,c1 = color
    img = gradient(w,h,c0,c1)
    draw = ImageDraw.Draw(img,"RGBA")
    rounded_rect(draw, [40,40,w-40,140], 14, (8,18,36,190))
    draw.text((70,65), f"CLIP {idx} — {title}", fill="#ffd34e", font=font(28))
    draw.text((70,105), desc, fill="#a9b9ca", font=font(16))
    # mock play triangle
    draw.polygon([(w//2-30, h//2-30),(w//2-30,h//2+30),(w//2+30,h//2)], fill=(255,255,255,220))
    draw.text((w//2, h-40), "30 s trailer — 6 clips clipáveis", fill="#fff8e7", font=font(14), anchor="mm")
    return img

def main():
    SCREENSHOTS.mkdir(parents=True, exist_ok=True)
    VIDEO.mkdir(parents=True, exist_ok=True)
    random.seed(20260918)
    for i, (c0,c1,accent,title,sub) in enumerate(PALETTES, start=1):
        img = make_screenshot(i,c0,c1,accent,title,sub)
        out = SCREENSHOTS / f"{i:02d}_{slugify(title)}_1080x1920.png"
        img.save(out, "PNG", optimize=True)
        print(f"screenshot {out.name} {out.stat().st_size/1024:.0f} KB")
    feat = make_feature()
    feat_path = STORE / "feature_graphic_1024x500.png"
    feat.save(feat_path, "PNG", optimize=True)
    print(f"feature {feat_path.name} {feat_path.stat().st_size/1024:.0f} KB")
    clips = [
        ("Caramelo", "o caramelo no ponto — 0:00-0:04", ("#1a2a45","#2c9dc1")),
        ("Ônibus", "pegue o busão — 0:04-0:09", ("#1a2a45","#2c9dc1")),
        ("Tráfego", "desvie carros e motos — 0:09-0:15", ("#2b1a2f","#d65b75")),
        ("Calçada", "atalhos de calçada — 0:15-0:20", ("#1f3a2a","#54d18b")),
        ("Dash", "dash invencível — 0:20-0:25", ("#2f2a1f","#f2635e")),
        ("Endless", "endless liberado — 0:25-0:30", ("#0f2a3a","#63c8ed")),
    ]
    for idx,(title,desc,col) in enumerate(clips,1):
        img = make_clip(idx,title,desc,col)
        out = VIDEO / f"clip_{idx:02d}_{slugify(title)}_1280x720.png"
        img.save(out,"PNG",optimize=True)
        print(f"clip {out.name}")
    # gera storyboard concat horizontal
    storyboard = Image.new("RGB", (1280*3, 720*2), "#08152f")
    draw = ImageDraw.Draw(storyboard)
    for idx, p in enumerate(sorted(VIDEO.glob("clip_*.png"))):
        im = Image.open(p)
        x = (idx%3)*1280
        y = (idx//3)*720
        storyboard.paste(im, (x,y))
    sb_path = VIDEO / "storyboard_6clips_3840x1440.png"
    storyboard.save(sb_path, "PNG", optimize=True)
    print(f"storyboard {sb_path.name} {sb_path.stat().st_size/1024:.0f} KB")
    print("OK store assets Lote 18")

if __name__ == "__main__":
    main()
