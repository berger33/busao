## Céus panorama equiretangulares Nishita (físicos) para o Corre pro Ponto.
## Rodar: blender --background --python tools/blender/render_ceu_nishita.py
## Gera em tools/blender/out/: ceu_tropical_v2.png (sol a 28°, névoa tropical)
## e ceu_entardecer_v2.png (sol baixo, poeira dourada). sun_disc desligado:
## o sol que ilumina/sombreia é o DirectionalLight3D do jogo; o panorama só
## precisa do brilho do céu coerente com a elevação da luz.
import math
import os

import bpy

OUT = os.path.join(os.path.dirname(__file__), "out")


def render_ceu(nome: str, elev_deg: float, sun_rot_deg: float,
               dust: float, ozone: float, strength: float) -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 24
    scene.cycles.use_denoising = False
    scene.render.resolution_x = 2048
    scene.render.resolution_y = 1024
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "OPEN_EXR"
    scene.render.image_settings.color_depth = "32"
    # Standard: o PNG é asset LDR do jogo; AgX/Filmic lavariam o azul.
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.render.filepath = os.path.join(OUT, nome + ".exr")

    world = bpy.data.worlds.new("Ceu")
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "NISHITA"
    sky.sun_elevation = math.radians(elev_deg)
    sky.sun_rotation = math.radians(sun_rot_deg)
    sky.sun_disc = False
    sky.air_density = 1.0
    sky.dust_density = dust
    sky.ozone_density = ozone
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = strength
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])

    cam_data = bpy.data.cameras.new("PanoCam")
    cam_data.type = "PANO"
    cam_data.panorama_type = "EQUIRECTANGULAR"
    cam = bpy.data.objects.new("PanoCam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    # Sem pitch, a câmera panorama olha para o chão (nadir preto no centro
    # do equiretângulo). X+90° põe o horizonte no meio da imagem.
    cam.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    bpy.ops.render.render(write_still=True)

    # Nishita é físico (luminâncias de céu reais, ordens de grandeza acima
    # de 1.0): em vez de chutar EV de exposição, normaliza pelo percentil
    # 99.7 do EXR float e grava o PNG LDR — cor e razão sol/céu preservadas.
    import numpy as np
    exr_path = os.path.join(OUT, nome + ".exr")
    img = bpy.data.images.load(exr_path)
    w, h = img.size
    buf = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(buf)
    arr = buf.reshape(h, w, 4)
    lum = arr[..., :3].max(axis=2)
    positivos = lum[lum > 0.0]
    p99 = float(np.percentile(positivos, 99.7)) if positivos.size else 1.0
    escala = 0.92 / max(p99, 1e-6)
    arr[..., :3] *= escala
    np.clip(arr, 0.0, 1.0, out=arr)
    out_img = bpy.data.images.new(nome + "_ldr", w, h, alpha=False)
    out_img.pixels.foreach_set(arr.astype(np.float32).ravel())
    out_img.filepath_raw = os.path.join(OUT, nome + ".png")
    out_img.file_format = "PNG"
    out_img.save()
    bpy.data.images.remove(img)
    bpy.data.images.remove(out_img)
    os.remove(exr_path)
    print("CEU_OK", nome)


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    # Sol a ~28° de elevação casa com sun.rotation_degrees.x=-28 do jogo;
    # sun_rotation coloca o brilho em u≈0.61 como no ceu_tropical atual
    # (mapeamento conferido visualmente contra o panorama legado).
    render_ceu("ceu_tropical_v2", 28.0, -39.6, 1.6, 1.1, 1.0)
    render_ceu("ceu_entardecer_v2", 9.0, -39.6, 3.2, 1.0, 1.0)


main()
