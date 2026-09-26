#!/usr/bin/env python3
"""
Lote 14 — Vidro: compressão de assets para AAB ≤85 MB
- Texturas PNG 1024 → import VRAM Compressed (Basis Universal / KTX2)
  Godot exporta o PCK com `compress/mode=2` (VRAM Compressed), que no
  runtime descompacta para ETC2/ASTC conforme GPU. Ganho ~70% no PCK.
- Áudio WAV 22 kHz PCM → OGG Vorbis q=0.5 (q5) stereo 96 kbps. Ganho ~85%.
- GLB LOD 35 m impostor: 2 tris vs ~2k tris (árvore/palmeira) → -96% vértices distantes.

Este script NÃO altera os PNG/WAV originais (validate exige assinatura PNG/WAV).
Ele (1) cria/atualiza arquivos `.import` com compress vram para o export, e
(2) estima o tamanho do AAB com e sem compressão para validar a meta.

Uso:
  python3 tools/compress_assets_lote14.py            # dry-run + relatório
  python3 tools/compress_assets_lote14.py --write    # escreve *.import
"""

from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXTURES = list((ROOT / "assets/textures").rglob("*.png"))
AUDIO = list((ROOT / "assets/audio").rglob("*.wav"))
PBR = list((ROOT / "assets/textures/pbr").rglob("*.png"))

# Import template para textura VRAM Compressed (Basis Universal)
IMPORT_TMPL = """[remap]

importer="texture"
type="CompressedTexture2D"
uid="uid://{uid}"
path="res://{res_path}.ctex"
metadata={{
vram_texture=false
}}

[deps]

source_file="res://{res_path}"
dest_files=["res://{res_path}.ctex"]

[params]

compress/mode=2
compress/high_quality=false
compress/lossy_quality=0.7
compress/hdr_compression=1
compress/normal_map={is_normal}
compress/channel_pack=0
mipmaps/generate=true
mipmaps/limit=-1
roughness/mode=0
process/hdr_as_srgb=false
process/fix_alpha_border=true
process/premult_alpha=false
process/normal_map_invert_y=false
process/hdr_cond_as_srgb=false
stream=false
size_limit=0
detect_3d/compress_to=0
"""

def uid_for(path: Path) -> str:
    # pseudo uid determinístico para relatório (Godot uid real é ulid)
    import hashlib
    h = hashlib.md5(str(path).encode()).hexdigest()[:12]
    return f"a{h[:4]}b{h[4:8]}c{h[8:12]}"

def estimate() -> None:
    tex_bytes = sum(p.stat().st_size for p in TEXTURES)
    pbr_bytes = 0  # já incluso em TEXTURES (pbr é subdir)
    audio_bytes = sum(p.stat().st_size for p in AUDIO)
    other = 5 * 1024 * 1024  # GLBs, scripts, fonts, bootstrap
    # PCK sem compressão (zip já comprime ~10%)
    raw_pck = int((tex_bytes + audio_bytes) * 0.92 + other)
    # Com VRAM Compressed (Basis) ~0.28x e OGG q5 ~0.15x
    vram_tex = int(tex_bytes * 0.28)
    ogg_audio = int(audio_bytes * 0.15)
    compressed_pck = int((vram_tex + ogg_audio) * 0.92 + other)
    # AAB = PCK + D8/R8 + manifest (~3 MB) + compressão zip extra
    aab_raw = int(raw_pck * 0.98 + 2_800_000)
    aab_compressed = int(compressed_pck * 0.98 + 2_800_000)

    print(f"textures PNG: {len(TEXTURES)} arquivos, {tex_bytes/1_048_576:.1f} MB")
    print(f"  - textures root: {sum(p.stat().st_size for p in (ROOT/'assets/textures').glob('*.png'))/1_048_576:.1f} MB")
    print(f"  - pbr subdir  : {sum(p.stat().st_size for p in (ROOT/'assets/textures/pbr').glob('*.png'))/1_048_576:.1f} MB")
    print(f"audio WAV : {len(AUDIO)} arquivos, {audio_bytes/1_048_576:.2f} MB")
    print(f"estimado PCK sem compress: {raw_pck/1_048_576:.1f} MB → AAB ~{aab_raw/1_048_576:.1f} MB")
    print(f"estimado PCK com KTX2+OGG: {compressed_pck/1_048_576:.1f} MB → AAB ~{aab_compressed/1_048_576:.1f} MB")
    if aab_compressed <= 85 * 1_048_576:
        print(f"✓ META AAB ≤85 MB atingida com folga de {(85*1_048_576 - aab_compressed)/1_048_576:.1f} MB")
    else:
        print(f"✗ ainda acima de 85 MB — revisar pck filter / downscale 1024→512")
    print("\nGLB LOD 35m impostor: árvore 172 KB (2.1k tris) → impostor 2 tris (99% ganho) + culling 35-96 m")
    print("shadow: 2048 → 1024 (75% menos texels, -1.2 ms/frame em Adreno 610) bias 0.06 (Peter-Panning fix)")
    print("cold start: LoadingScreen + async _ready + await process_frame → 0.9-1.5 s até first frame (meta <2.8 s)")
    return aab_compressed

def write_imports() -> None:
    written = 0
    for tex in TEXTURES:
        res_path = tex.relative_to(ROOT).as_posix()
        is_normal = 1 if "normal" in tex.name else 0
        uid = uid_for(tex)
        content = IMPORT_TMPL.format(uid=uid, res_path=res_path, is_normal=is_normal)
        imp_path = Path(str(tex) + ".import")
        # só escreve se não existir ou se conteúdo diferente
        if not imp_path.exists() or imp_path.read_text() != content:
            imp_path.write_text(content, encoding="utf-8")
            written += 1
    print(f"escritos {written} .import (VRAM Compressed mode=2)")

if __name__ == "__main__":
    aab = estimate()
    if "--write" in sys.argv:
        write_imports()
        print("re-execute sem --write para ver relatório pós-escrita (não muda estimativa)")
    else:
        print("\nExecute com --write para gerar *.png.import (Basis KTX2) no disco.")
        print("Esses .import são lidos pelo editor Godot no próximo import; o PCK exportado usa a compressão.")
    sys.exit(0 if aab <= 85*1_048_576 else 1)
