"""GECE NÖBETİ – Bölüm 1 sahnesi.

Blender sahnesini sıfırdan kurar: müze koridoru, Kemal, heykeller, ışıklar,
kameralar ve animasyon. Kullanım:

    python sahne.py --cikti /kareler/klasoru [--kalite test|final] [--kare 1-816] [--blend kayit.blend]

(Blender'ın kendi içinden de çalışır: blender -b -P sahne.py -- --cikti ...)
"""
import argparse
import math
import random
import sys

import bpy
from mathutils import Matrix, Vector

FPS = 24
# Çekim aralıkları (kare numaraları, dahil)
S1 = (1, 120)     # koridorda yürüyüş
S2 = (121, 264)   # Kemal yakın plan
S3 = (265, 360)   # duvar saati
S4 = (361, 528)   # fener heykellerde
S5 = (529, 588)   # heykel dönmüş
S5B = (589, 648)  # Kemal'in korkmuş yüzü
S6 = (649, 816)   # heykelin yüzü
SON = S6[1]

HALL_W, HALL_L, HALL_H = 8.0, 30.0, 6.0
STATUE_YS = [6.0, 9.5, 13.0, 16.5, 20.0, 23.5]
STATUE_X = -2.6
CLOCK_Y = 10.25
EVIL = 2  # üçüncü heykel

random.seed(7)


# ----------------------------------------------------------------- yardımcılar
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True


def bevel(obj, width=0.02, segments=3):
    m = obj.modifiers.new("bevel", "BEVEL")
    m.width = width
    m.segments = segments
    m.limit_method = "ANGLE"
    return m


def subsurf(obj, levels=2):
    m = obj.modifiers.new("subsurf", "SUBSURF")
    m.levels = levels
    m.render_levels = levels
    return m


def mat(name, color, rough=0.5, metal=0.0, sss=0.0, emit=None, emit_str=0.0,
        coat=0.0, spec=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Subsurface Weight"].default_value = sss
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Specular IOR Level"].default_value = spec
    if sss:
        b.inputs["Subsurface Radius"].default_value = (0.4, 0.25, 0.2)
        b.inputs["Subsurface Scale"].default_value = 0.05
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = emit_str
    return m


def add_noise_bump(m, scale=40.0, strength=0.08, rough_var=None):
    """Malzemeye ince yüzey kusuru ekler (gerçekçilik için)."""
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 3
    nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = strength
    bump.inputs["Distance"].default_value = 0.02
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    if rough_var:
        lo, hi = rough_var
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["To Min"].default_value = lo
        mr.inputs["To Max"].default_value = hi
        nt.links.new(noise.outputs["Fac"], mr.inputs["Value"])
        nt.links.new(mr.outputs["Result"], b.inputs["Roughness"])
    return m


def assign(obj, m):
    obj.data.materials.clear()
    obj.data.materials.append(m)


def sphere(name, loc, scale, m, parent=None, segs=48):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=segs // 2,
                                         radius=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    smooth(o)
    assign(o, m)
    if parent:
        set_parent(o, parent)
    return o


def box(name, loc, size, m, bev=0.02, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bev:
        bevel(o, bev, 3)
    assign(o, m)
    if parent:
        set_parent(o, parent)
    return o


def cyl(name, loc, r, depth, m, rot=(0, 0, 0), verts=64, bev=0.01, parent=None,
        r2=None):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth,
                                            location=loc, rotation=rot)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r2,
                                        depth=depth, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    smooth(o)
    if bev:
        bevel(o, bev, 3)
    assign(o, m)
    if parent:
        set_parent(o, parent)
    return o


def empty(name, loc=(0, 0, 0), parent=None, local=False):
    o = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    if parent:
        if local:
            o.parent = parent
        else:
            set_parent(o, parent)
    return o


def set_parent(child, parent):
    """Çocuğu, dünya konumunu koruyarak ebeveyne bağlar."""
    bpy.context.view_layer.update()
    mw = child.matrix_world.copy()
    child.parent = parent
    child.matrix_world = mw


def key(obj, path, frame, value=None, interp=None):
    if value is not None:
        setattr(obj, path, value)
    obj.keyframe_insert(data_path=path, frame=frame)
    if interp:
        ad = obj.animation_data or obj.id_data.animation_data
        for fc in ad.action.fcurves:
            if fc.data_path == path:
                for kp in fc.keyframe_points:
                    if kp.co[0] == frame:
                        kp.interpolation = interp


def set_all_interp(obj, interp):
    ad = obj.animation_data
    if ad and ad.action:
        for fc in ad.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = interp


def look_at(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def lathe(name, profile, m, segs=96, folds=None, loc=(0, 0, 0), parent=None, levels=1):
    """Z ekseni etrafında döndürülmüş yüzey. profile: [(z, r)], folds(theta, z) -> dr."""
    verts, faces = [], []
    for z, r in profile:
        for i in range(segs):
            th = i / segs * math.tau
            rr = max(0.0, r + (folds(th, z) if folds and r > 0 else 0))
            verts.append((rr * math.cos(th), rr * math.sin(th), z))
    rings = len(profile)
    for j in range(rings - 1):
        for i in range(segs):
            a, b = j * segs + i, j * segs + (i + 1) % segs
            faces.append((a, b, b + segs, a + segs))
    verts.append((0, 0, profile[0][0]))
    bc = len(verts) - 1
    faces += [(bc, (i + 1) % segs, i) for i in range(segs)]
    verts.append((0, 0, profile[-1][0]))
    tc = len(verts) - 1
    base = (rings - 1) * segs
    faces += [(tc, base + i, base + (i + 1) % segs) for i in range(segs)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    smooth(o)
    assign(o, m)
    if levels:
        subsurf(o, levels)
    if parent:
        set_parent(o, parent)
    return o


def tube(name, p1, p2, r1, r2, m, parent=None, folds=None):
    """p1'den p2'ye uzanan, uçları yuvarlatılmış konik boru (kol, kordon vb.)."""
    p1, p2 = Vector(p1), Vector(p2)
    d = p2 - p1
    L = d.length
    prof = [(-r1 * 0.9, 0.0), (-r1 * 0.6, r1 * 0.8), (0, r1), (L, r2), (L + r2 * 0.6, r2 * 0.8), (L + r2 * 0.9, 0.0)]
    o = lathe(name, prof, m, segs=32, folds=folds, loc=p1, levels=1)
    o.rotation_euler = Vector((0, 0, 1)).rotation_difference(d).to_euler()
    if parent:
        set_parent(o, parent)
    return o


def frame_ring(name, x, y, z, w, h, bar, depth, m):
    """Duvara asılı çerçeve halkası (dört çıta)."""
    xc = x - depth / 2
    for k, (dy, dz, sy, sz) in enumerate(((0, (h - bar) / 2, w, bar), (0, -(h - bar) / 2, w, bar),
                                         ((w - bar) / 2, 0, bar, h - 2 * bar), (-(w - bar) / 2, 0, bar, h - 2 * bar))):
        box(f"{name}_{k}", (xc, y + dy, z + dz), (depth, sy, sz), m, bev=min(0.02, bar / 3))


# ----------------------------------------------------------------- malzemeler
def veined_marble(name, base, vein, scale, vein_w=0.06):
    """Damarlı mermer: dalga dokusu + bozulma ile ince gri damarlar."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_profile = "SIN"
    wave.inputs["Scale"].default_value = scale
    wave.inputs["Distortion"].default_value = 10
    wave.inputs["Detail"].default_value = 4
    wave.inputs["Detail Scale"].default_value = 1.5
    nt.links.new(tc.outputs["Object"], wave.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.elements[0].position = 0.0
    cr.elements[0].color = (*vein, 1)
    cr.elements[1].position = vein_w
    cr.elements[1].color = (*base, 1)
    nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    # hafif renk dalgalanması
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3
    noise.inputs["Detail"].default_value = 3
    nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "OVERLAY"
    mix.inputs["Factor"].default_value = 0.25
    nt.links.new(ramp.outputs["Color"], mix.inputs["A"])
    nt.links.new(noise.outputs["Color"], mix.inputs["B"])
    nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = 0.18
    mr.inputs["To Max"].default_value = 0.42
    nt.links.new(noise.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], b.inputs["Roughness"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.04
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def oil_painting():
    """Karanlık, çatlamış eski yağlı boya tablo."""
    m = bpy.data.materials.new("yagliboya")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 1.8
    noise.inputs["Detail"].default_value = 6
    noise.inputs["Distortion"].default_value = 0.8
    nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.elements[0].color = (0.01, 0.012, 0.008, 1)
    cr.elements[1].color = (0.25, 0.16, 0.06, 1)
    e = cr.elements.new(0.55)
    e.color = (0.06, 0.07, 0.04, 1)
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.35
    b.inputs["Coat Weight"].default_value = 0.6  # vernik
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = 60
    nt.links.new(tc.outputs["Object"], vor.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.25
    bump.inputs["Distance"].default_value = 0.002
    nt.links.new(vor.outputs["Distance"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def beam_material():
    """Fener huzmesi: havadaki tozda görünen ışık konisi (hacim yerine ucuz sahte)."""
    m = bpy.data.materials.new("huzme")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1.0, 0.8, 0.55, 1)
    add = nt.nodes.new("ShaderNodeAddShader")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    # uzunluk boyunca sönme (generated z: 0 fener, 1 uç)
    fade = nt.nodes.new("ShaderNodeMath")
    fade.operation = "SUBTRACT"
    fade.inputs[0].default_value = 1.0
    nt.links.new(sep.outputs["Z"], fade.inputs[1])
    fade2 = nt.nodes.new("ShaderNodeMath")
    fade2.operation = "POWER"
    fade2.inputs[1].default_value = 1.8
    nt.links.new(fade.outputs[0], fade2.inputs[0])
    # kenarlarda yumuşak geçiş
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.5
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    nt.links.new(lw.outputs["Facing"], inv.inputs[1])
    edge = nt.nodes.new("ShaderNodeMath")
    edge.operation = "POWER"
    edge.inputs[1].default_value = 2.5
    nt.links.new(inv.outputs[0], edge.inputs[0])
    # toz zerrecikleri
    dust = nt.nodes.new("ShaderNodeTexNoise")
    dust.inputs["Scale"].default_value = 18
    dust.inputs["Detail"].default_value = 2
    nt.links.new(tc.outputs["Object"], dust.inputs["Vector"])
    dmr = nt.nodes.new("ShaderNodeMapRange")
    dmr.inputs["From Min"].default_value = 0.35
    dmr.inputs["From Max"].default_value = 0.75
    dmr.inputs["To Min"].default_value = 0.55
    dmr.inputs["To Max"].default_value = 1.4
    nt.links.new(dust.outputs["Fac"], dmr.inputs["Value"])
    m1 = nt.nodes.new("ShaderNodeMath")
    m1.operation = "MULTIPLY"
    nt.links.new(fade2.outputs[0], m1.inputs[0])
    nt.links.new(edge.outputs[0], m1.inputs[1])
    m2 = nt.nodes.new("ShaderNodeMath")
    m2.operation = "MULTIPLY"
    nt.links.new(m1.outputs[0], m2.inputs[0])
    nt.links.new(dmr.outputs["Result"], m2.inputs[1])
    strength = nt.nodes.new("ShaderNodeValue")
    strength.name = "huzme_guc"
    strength.outputs[0].default_value = 0.15
    m3 = nt.nodes.new("ShaderNodeMath")
    m3.operation = "MULTIPLY"
    nt.links.new(m2.outputs[0], m3.inputs[0])
    nt.links.new(strength.outputs[0], m3.inputs[1])
    nt.links.new(m3.outputs[0], em.inputs["Strength"])
    nt.links.new(tr.outputs[0], add.inputs[0])
    nt.links.new(em.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs["Surface"])
    m.use_backface_culling = False
    return m


def materials():
    M = {}
    # zemin: siyah-beyaz mermer dama
    m = bpy.data.materials.new("zemin")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    chk = nt.nodes.new("ShaderNodeTexChecker")
    chk.inputs["Scale"].default_value = 1.0
    chk.inputs["Color1"].default_value = (0.55, 0.53, 0.5, 1)
    chk.inputs["Color2"].default_value = (0.03, 0.03, 0.035, 1)
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (0.8, 0.8, 0.8)
    nt.links.new(tc.outputs["Object"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], chk.inputs["Vector"])
    # mermer damar
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.inputs["Scale"].default_value = 3
    wave.inputs["Distortion"].default_value = 12
    wave.inputs["Detail"].default_value = 3
    nt.links.new(tc.outputs["Object"], wave.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 0.25
    nt.links.new(chk.outputs["Color"], mix.inputs["A"])
    nt.links.new(wave.outputs["Color"], mix.inputs["B"])
    nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 6
    nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = 0.08
    mr.inputs["To Max"].default_value = 0.35
    nt.links.new(noise.outputs["Fac"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], b.inputs["Roughness"])
    M["zemin"] = m

    M["duvar"] = add_noise_bump(mat("duvar", (0.16, 0.035, 0.035), 0.85), 25, 0.15)
    M["lambri"] = add_noise_bump(mat("lambri", (0.035, 0.022, 0.015), 0.45, coat=0.3), 60, 0.05)
    M["tavan"] = mat("tavan", (0.08, 0.075, 0.07), 0.9)
    M["sutun"] = add_noise_bump(mat("sutun", (0.6, 0.57, 0.52), 0.35), 8, 0.05, (0.25, 0.5))
    M["mermer"] = veined_marble("mermer", (0.68, 0.66, 0.62), (0.5, 0.49, 0.47), 3.5, vein_w=0.018)
    M["kaide"] = veined_marble("kaide", (0.035, 0.035, 0.04), (0.2, 0.19, 0.18), 1.5, vein_w=0.02)
    M["kadife"] = mat("kadife", (0.22, 0.005, 0.015), 0.85)
    M["kadife"].node_tree.nodes["Principled BSDF"].inputs["Sheen Weight"].default_value = 1.0
    M["kadife"].node_tree.nodes["Principled BSDF"].inputs["Sheen Tint"].default_value = (1.0, 0.4, 0.4, 1)
    M["pirinc"] = add_noise_bump(mat("pirinc", (0.75, 0.55, 0.25), 0.3, metal=1.0), 60, 0.03)
    M["koyu_ahsap"] = add_noise_bump(mat("koyu_ahsap", (0.03, 0.015, 0.008), 0.5), 40, 0.1)
    M["yagliboya"] = oil_painting()
    M["huzme"] = beam_material()
    M["cerceve"] = mat("cerceve", (0.5, 0.35, 0.1), 0.35, metal=1.0)
    M["tablo"] = add_noise_bump(mat("tablo", (0.05, 0.06, 0.04), 0.7), 30, 0.3)
    M["pencere"] = mat("pencere", (0, 0, 0), 1, emit=(0.35, 0.5, 1.0), emit_str=0.35)
    M["kayit"] = mat("kayit", (0.02, 0.02, 0.025), 0.5, metal=0.6)
    M["cikis"] = mat("cikis", (0, 0, 0), 1, emit=(0.1, 1.0, 0.3), emit_str=6)
    M["cikis_kutu"] = mat("cikis_kutu", (0.02, 0.05, 0.03), 0.4)
    M["saat_yuz"] = add_noise_bump(mat("saat_yuz", (0.75, 0.7, 0.58), 0.6), 50, 0.05)
    M["siyah"] = mat("siyah", (0.01, 0.01, 0.01), 0.4)
    M["oyuk"] = mat("oyuk", (0.0, 0.0, 0.0), 1.0, spec=0.0)
    # Kemal
    M["ten"] = mat("ten", (0.8, 0.55, 0.42), 0.45, sss=0.08)
    M["uniforma"] = add_noise_bump(mat("uniforma", (0.03, 0.05, 0.12), 0.75), 120, 0.12)
    M["pantolon"] = add_noise_bump(mat("pantolon", (0.02, 0.025, 0.05), 0.8), 120, 0.12)
    M["ayakkabi"] = mat("ayakkabi", (0.01, 0.01, 0.01), 0.25, coat=0.5)
    M["altin"] = mat("altin", (0.9, 0.65, 0.25), 0.25, metal=1.0)
    M["goz"] = mat("goz", (0.005, 0.005, 0.005), 0.05, coat=1.0)
    M["biyik"] = add_noise_bump(mat("biyik", (0.04, 0.025, 0.015), 0.8), 200, 0.4)
    M["fener"] = add_noise_bump(mat("fener", (0.06, 0.06, 0.065), 0.3, metal=1.0), 80, 0.05)
    M["fener_cam"] = mat("fener_cam", (1, 1, 1), 0.1, emit=(1.0, 0.85, 0.6), emit_str=30)
    return M


# ----------------------------------------------------------------- mekân
def build_hall(M):
    # zemin, tavan, duvarlar
    box("zemin", (0, HALL_L / 2, -0.05), (HALL_W, HALL_L + 2, 0.1), M["zemin"], bev=0)
    box("tavan", (0, HALL_L / 2, HALL_H + 0.05), (HALL_W, HALL_L + 2, 0.1), M["tavan"], bev=0)
    box("duvar_sol", (-HALL_W / 2 - 0.1, HALL_L / 2, HALL_H / 2), (0.2, HALL_L + 2, HALL_H), M["duvar"], bev=0)
    box("duvar_sag", (HALL_W / 2 + 0.1, HALL_L / 2, HALL_H / 2), (0.2, HALL_L + 2, HALL_H), M["duvar"], bev=0)
    box("duvar_son", (0, HALL_L + 0.1, HALL_H / 2), (HALL_W, 0.2, HALL_H), M["duvar"], bev=0)
    box("duvar_bas", (0, -1.1, HALL_H / 2), (HALL_W, 0.2, HALL_H), M["duvar"], bev=0)
    # lambri (alt ahşap panel) ve süpürgelik
    for sx in (-1, 1):
        box(f"lambri_{sx}", (sx * (HALL_W / 2 - 0.03), HALL_L / 2, 0.6), (0.06, HALL_L + 2, 1.2), M["lambri"], bev=0.01)
        box(f"lambri_ust_{sx}", (sx * (HALL_W / 2 - 0.06), HALL_L / 2, 1.22), (0.1, HALL_L + 2, 0.06), M["lambri"], bev=0.015)
    # tavan kirişleri
    for y in range(0, int(HALL_L) + 1, 3):
        box(f"kiris_{y}", (0, y, HALL_H - 0.15), (HALL_W, 0.3, 0.3), M["tavan"], bev=0.02)
    # sütunlar (iki yanda)
    for y in [1.5 + 3.5 * i for i in range(8)]:
        for sx in (-1, 1):
            x = sx * (HALL_W / 2 - 0.35)
            cyl(f"sutun_{sx}_{y}", (x, y, HALL_H / 2), 0.28, HALL_H, M["sutun"], verts=48, bev=0.01)
            box(f"sutun_alt_{sx}_{y}", (x, y, 0.15), (0.75, 0.75, 0.3), M["sutun"], bev=0.03)
            box(f"sutun_ust_{sx}_{y}", (x, y, HALL_H - 0.4), (0.7, 0.7, 0.2), M["sutun"], bev=0.03)
    # sağ duvarda yüksek pencereler (ay ışığı)
    for y in [3.25, 13.75, 24.25]:
        bpy.ops.mesh.primitive_plane_add(size=1, location=(HALL_W / 2 - 0.005, y, 3.9),
                                         rotation=(0, math.radians(-90), 0))
        p = bpy.context.active_object
        p.name = f"pencere_{y}"
        p.scale = (3.2, 1.6, 1)
        assign(p, M["pencere"])
        # kayıtlar (gölge deseni için)
        for dz in (-1.0, 0, 1.0):
            box(f"kayit_y_{y}_{dz}", (HALL_W / 2 - 0.08, y, 3.9 + dz), (0.08, 1.7, 0.06), M["kayit"], bev=0)
        for dy in (-0.4, 0.4):
            box(f"kayit_d_{y}_{dy}", (HALL_W / 2 - 0.08, y + dy, 3.9), (0.08, 0.06, 3.3), M["kayit"], bev=0)
        bpy.ops.object.light_add(type="AREA", location=(HALL_W / 2 - 0.15, y, 3.9),
                                 rotation=(0, math.radians(55), 0))
        L = bpy.context.active_object
        L.name = f"ay_{y}"
        L.data.shape = "RECTANGLE"
        L.data.size = 3.2
        L.data.size_y = 1.6
        L.data.energy = 260
        L.data.color = (0.4, 0.55, 1.0)
    # sağ duvarda tablolar
    X = HALL_W / 2
    for y in [6.75, 20.75]:
        z = 2.6
        frame_ring(f"cerceve_dis_{y}", X, y, z, 2.1, 1.62, 0.13, 0.12, M["cerceve"])
        frame_ring(f"cerceve_ic_{y}", X, y, z, 1.86, 1.38, 0.05, 0.07, M["koyu_ahsap"])
        frame_ring(f"cerceve_kenar_{y}", X, y, z, 1.78, 1.3, 0.03, 0.09, M["cerceve"])
        box(f"tablo_{y}", (X - 0.03, y, z), (0.02, 1.74, 1.26), M["yagliboya"], bev=0)
        for dy in (-1, 1):  # köşe süsleri
            for dz in (-1, 1):
                sphere(f"rozet_{y}_{dy}_{dz}", (X - 0.13, y + dy * 0.985, z + dz * 0.745), (0.035, 0.07, 0.07),
                       M["cerceve"], segs=16)
        # tablo lambası (gece kapalı)
        cyl(f"lamba_kol_{y}", (X - 0.2, y, z + 0.98), 0.012, 0.4, M["pirinc"], rot=(0, math.radians(90), 0))
        cyl(f"lamba_{y}", (X - 0.4, y, z + 0.95), 0.05, 0.7, M["pirinc"], rot=(math.radians(90), 0, 0))
    stanchions(M)


def stanchions(M):
    """Heykellerin önünde pirinç direkler ve aralarında sarkan kadife kordonlar."""
    x = STATUE_X + 0.95
    ys = [STATUE_YS[0] - 1.75] + [(a + b) / 2 for a, b in zip(STATUE_YS, STATUE_YS[1:])] + [STATUE_YS[-1] + 1.75]
    top = 0.92
    for i, y in enumerate(ys):
        cyl(f"direk_taban_{i}", (x, y, 0.015), 0.15, 0.03, M["pirinc"], bev=0.008)
        cyl(f"direk_{i}", (x, y, top / 2), 0.024, top, M["pirinc"], bev=0.004)
        sphere(f"direk_bas_{i}", (x, y, top + 0.03), (0.045, 0.045, 0.05), M["pirinc"], segs=24)
    for i, (y1, y2) in enumerate(zip(ys, ys[1:])):
        cu = bpy.data.curves.new(f"kordon_{i}", "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = 0.026
        cu.bevel_resolution = 4
        sp = cu.splines.new("BEZIER")
        sp.bezier_points.add(2)
        pts = [(x, y1 + 0.05, top - 0.02), (x, (y1 + y2) / 2, top - 0.3), (x, y2 - 0.05, top - 0.02)]
        for bp, p in zip(sp.bezier_points, pts):
            bp.co = p
            bp.handle_left_type = bp.handle_right_type = "AUTO"
        o = bpy.data.objects.new(f"kordon_{i}", cu)
        bpy.context.scene.collection.objects.link(o)
        o.data.materials.append(M["kadife"])
    # koridor sonunda ÇIKIŞ levhası
    box("cikis_kutu", (0, HALL_L - 0.05, 4.6), (1.1, 0.1, 0.38), M["cikis_kutu"], bev=0.01)
    bpy.ops.object.text_add(location=(0, HALL_L - 0.11, 4.6), rotation=(math.radians(90), 0, 0))
    t = bpy.context.active_object
    t.name = "cikis_yazi"
    t.data.body = "ÇIKIŞ"
    t.data.align_x = "CENTER"
    t.data.align_y = "CENTER"
    t.data.size = 0.26
    t.data.extrude = 0.005
    assign(t, M["cikis"])
    bpy.ops.object.light_add(type="POINT", location=(0, HALL_L - 0.5, 4.4))
    L = bpy.context.active_object
    L.name = "cikis_isik"
    L.data.energy = 25
    L.data.color = (0.1, 1.0, 0.3)
    L.data.shadow_soft_size = 0.3


def build_clock(M):
    """Sağ duvarda, y=12'de duvar saati. Akrep/yelkovan döndürülebilir."""
    x = HALL_W / 2 - 0.02
    c = empty("saat", (x, CLOCK_Y, 3.4))
    # yerel +Z -> dünya -X (koridora bakar), yerel +Y (saat 12) -> yukarı
    rm = Matrix(((0, 0, -1), (-1, 0, 0), (0, 1, 0)))
    c.rotation_euler = rm.to_euler()
    cyl("saat_cerceve", (0, 0, 0.04), 0.42, 0.08, M["cerceve"], parent=None, bev=0.02)
    fr = bpy.context.active_object
    fr.parent = c
    cyl("saat_yuz", (0, 0, 0.081), 0.37, 0.01, M["saat_yuz"], bev=0)
    bpy.context.active_object.parent = c
    # saat çizgileri
    for i in range(12):
        a = i * math.tau / 12
        L = 0.06 if i % 3 == 0 else 0.035
        o = box(f"saat_cizgi_{i}", (math.sin(a) * 0.31, math.cos(a) * 0.31, 0.09), (0.012, L, 0.004), M["siyah"], bev=0)
        o.rotation_euler = (0, 0, -a)
        o.parent = c
    hands = {}
    for name, length, width in (("akrep", 0.18, 0.018), ("yelkovan", 0.28, 0.012)):
        piv = empty(f"{name}_pivot", (0, 0, 0.1), parent=c, local=True)
        h = box(name, (0, length / 2 - 0.03, 0), (width, length, 0.004), M["siyah"], bev=0)
        h.parent = piv
        hands[name] = piv
    cyl("saat_merkez", (0, 0, 0.105), 0.015, 0.01, M["altin"], bev=0).parent = c
    # Saat 02:59 -> 03:00
    def set_time(h, mnt, frame):
        hands["yelkovan"].rotation_euler = (0, 0, -mnt / 60 * math.tau)
        hands["akrep"].rotation_euler = (0, 0, -((h % 12) + mnt / 60) / 12 * math.tau)
        for p in hands.values():
            p.keyframe_insert("rotation_euler", frame=frame)
    set_time(2, 59, 1)
    set_time(2, 59, 309)
    set_time(3, 0, 312)
    for p in hands.values():
        set_all_interp(p, "BACK")


# ----------------------------------------------------------------- karakterler
def build_statue(M, i, y):
    """Klasik cüppeli mermer heykel (ön yüz -Y), basamaklı kaide üzerinde."""
    root = empty(f"heykel_{i}", (STATUE_X, y, 0))
    X = STATUE_X
    # basamaklı kaide + pirinç plaket (koridora bakan yüzde)
    box(f"kaide_alt_{i}", (X, y, 0.06), (1.12, 1.12, 0.12), M["kaide"], bev=0.02, parent=root)
    box(f"kaide_{i}", (X, y, 0.45), (0.9, 0.9, 0.68), M["kaide"], bev=0.025, parent=root)
    box(f"kaide_ust_{i}", (X, y, 0.825), (1.04, 1.04, 0.07), M["kaide"], bev=0.02, parent=root)
    box(f"plaket_{i}", (X + 0.455, y, 0.52), (0.012, 0.36, 0.13), M["pirinc"], bev=0.004, parent=root)
    z0 = 0.86
    fig = empty(f"figur_{i}", (X, y, z0), parent=root)
    rnd = random.Random(100 + i)
    ph = rnd.uniform(0, math.tau)

    def W(dx, dy, dz):  # figüre göre yerel -> dünya
        return (X + dx, y + dy, z0 + dz)

    # cüppe: aşağı doğru derinleşen kumaş kıvrımları
    def folds(th, z):
        k = max(0.0, 1 - z / 1.35) ** 0.8
        return k * (0.034 * math.sin(9 * th + ph + 0.8 * z) + 0.012 * math.sin(23 * th + 2 * ph)) \
            + 0.006 * math.sin(5 * th + ph)
    robe = lathe(f"cuppe_{i}", [(0.0, 0.0), (0.0, 0.4), (0.08, 0.415), (0.4, 0.36), (0.8, 0.29), (1.05, 0.255),
                               (1.25, 0.27), (1.4, 0.275), (1.5, 0.2), (1.54, 0.0)],
                 M["mermer"], segs=128, folds=folds, loc=W(0, 0, 0))
    robe.scale = (1, 0.8, 1)
    set_parent(robe, fig)
    sphere(f"omuz_{i}", W(0, 0, 1.43), (0.36, 0.22, 0.15), M["mermer"], parent=fig)
    # göğüsten kalçaya çapraz kumaş kuşak
    sash = sphere(f"kusak_{i}", W(0.02, -0.2, 1.12), (0.075, 0.05, 0.42), M["mermer"], segs=32)
    sash.rotation_euler = (0, math.radians(38), 0)
    set_parent(sash, fig)
    # kollar: biri yanda sarkık, diğeri göğüste kumaşı tutar
    tube(f"sag_ust_kol_{i}", W(0.33, 0, 1.43), W(0.37, -0.02, 0.98), 0.085, 0.07, M["mermer"], parent=fig)
    tube(f"sag_on_kol_{i}", W(0.37, -0.02, 0.98), W(0.33, -0.1, 0.64), 0.066, 0.05, M["mermer"], parent=fig)
    sphere(f"sag_el_{i}", W(0.32, -0.12, 0.58), (0.045, 0.035, 0.07), M["mermer"], parent=fig, segs=24)
    tube(f"sol_ust_kol_{i}", W(-0.33, 0, 1.43), W(-0.36, -0.06, 1.0), 0.085, 0.07, M["mermer"], parent=fig)
    tube(f"sol_on_kol_{i}", W(-0.36, -0.06, 1.0), W(-0.04, -0.25, 1.1), 0.066, 0.05, M["mermer"], parent=fig)
    sphere(f"sol_el_{i}", W(0.0, -0.265, 1.12), (0.05, 0.04, 0.06), M["mermer"], parent=fig, segs=24)
    sphere(f"boyun_{i}", W(0, 0, 1.6), (0.075, 0.075, 0.11), M["mermer"], parent=fig, segs=32)
    # kafa: klasik yüz hatları
    hz = 1.84
    head = empty(f"kafa_{i}", W(0, 0, hz), parent=fig)
    sphere(f"kafatasi_{i}", W(0, 0.01, hz), (0.135, 0.155, 0.17), M["mermer"], parent=head)
    nose = sphere(f"burun_{i}", W(0, -0.152, hz - 0.005), (0.02, 0.035, 0.055), M["mermer"], segs=24)
    nose.rotation_euler = (math.radians(-12), 0, 0)
    set_parent(nose, head)
    sphere(f"kas_kemeri_{i}", W(0, -0.118, hz + 0.05), (0.08, 0.022, 0.015), M["mermer"], parent=head, segs=32)
    for s in (-1, 1):
        sphere(f"kulak_{i}_{s}", W(s * 0.13, 0.0, hz), (0.014, 0.028, 0.04), M["mermer"], parent=head, segs=16)
        if i != EVIL:  # kapalı göz kapakları
            sphere(f"kapak_{i}_{s}", W(s * 0.048, -0.128, hz + 0.018), (0.03, 0.018, 0.016), M["mermer"],
                   parent=head, segs=24)
    # bukle bukle saç
    for k in range(70):
        th = rnd.uniform(0, math.tau)
        zz = rnd.uniform(0.05, 1.0)
        d = Vector((math.cos(th) * math.sqrt(1 - zz * zz), math.sin(th) * math.sqrt(1 - zz * zz), zz))
        if d.y < -0.45 and d.z < 0.55:  # yüzü açık bırak
            continue
        p = Vector((d.x * 0.135, 0.01 + d.y * 0.155, hz + d.z * 0.17))
        r = rnd.uniform(0.028, 0.042)
        sphere(f"bukle_{i}_{k}", W(p.x, p.y, p.z), (r, r, r * 0.85), M["mermer"], parent=head, segs=16)
    if i == EVIL:
        # oyuk gözler ve alında çatlak (yalnız dönünce görünür)
        for s in (-1, 1):
            e = sphere(f"oyuk_goz_{s}", W(s * 0.05, -0.127, hz + 0.015), (0.032, 0.022, 0.034), M["oyuk"], segs=24)
            e.rotation_euler = (0, s * math.radians(20), s * math.radians(-12))
            set_parent(e, head)
        for k, (dx, dz, rot) in enumerate([(0.03, 0.09, 25), (0.05, 0.13, -30), (0.035, 0.05, 10)]):
            cr = sphere(f"catlak_{k}", W(dx, -0.135, hz + dz), (0.0015, 0.004, 0.03), M["oyuk"], segs=12)
            cr.rotation_euler = (0, math.radians(rot), 0)
            set_parent(cr, head)
    # duvara dönük (ön yüz -Y; -90 => -X'e bakar)
    fig.rotation_euler = (0, 0, math.radians(-90))
    return root, fig, head


def build_kemal(M):
    root = empty("kemal", (0, 0, 0))
    body = empty("kemal_govde", (0, 0, 0), parent=root)
    # bacaklar (kalçada pivot)
    legs = []
    for s in (-1, 1):
        piv = empty(f"bacak_pivot_{s}", (s * 0.13, 0, 0.52), parent=body)
        sphere(f"bacak_{s}", (s * 0.13, 0, 0.3), (0.115, 0.115, 0.26), M["pantolon"], parent=piv, segs=32)
        sh = sphere(f"ayakkabi_{s}", (s * 0.13, -0.06, 0.05), (0.11, 0.17, 0.07), M["ayakkabi"], parent=piv, segs=32)
        legs.append(piv)
    # gövde (ceket)
    torso = sphere("ceket", (0, 0, 0.82), (0.31, 0.25, 0.36), M["uniforma"], parent=body)
    sphere("kemer", (0, 0, 0.56), (0.28, 0.23, 0.06), M["ayakkabi"], parent=body, segs=32)
    box("toka", (0, -0.225, 0.56), (0.07, 0.02, 0.05), M["altin"], bev=0.005, parent=body)
    for k, z in enumerate((0.95, 0.83, 0.71)):
        sphere(f"dugme_{k}", (0, -0.245, z), (0.022, 0.012, 0.022), M["altin"], parent=body, segs=16)
    box("rozet", (0.14, -0.215, 0.98), (0.07, 0.015, 0.08), M["altin"], bev=0.008, parent=body)
    for s in (-1, 1):
        sphere(f"apolet_{s}", (s * 0.24, 0, 1.1), (0.1, 0.08, 0.025), M["altin"], parent=body, segs=24)
    # sol kol aşağıda
    larm = empty("sol_omuz", (-0.33, 0, 1.04), parent=body)
    la = sphere("sol_kol", (-0.37, 0, 0.84), (0.085, 0.085, 0.24), M["uniforma"], segs=32)
    la.rotation_euler = (0, math.radians(-12), 0)
    set_parent(la, larm)
    sphere("sol_el", (-0.42, 0, 0.6), (0.075, 0.075, 0.08), M["ten"], parent=larm, segs=32)
    # sağ kol öne uzanmış, fener tutuyor
    ra = sphere("sag_kol", (0.33, -0.18, 0.95), (0.085, 0.24, 0.085), M["uniforma"], parent=body, segs=32)
    ra.rotation_euler = (math.radians(-10), 0, math.radians(8))
    sphere("sag_el", (0.31, -0.42, 0.93), (0.075, 0.08, 0.075), M["ten"], parent=body, segs=32)
    # fener (pivot elde)
    fpiv = empty("fener_pivot", (0.31, -0.45, 0.95), parent=body)
    cyl("fener_govde", (0.31, -0.55, 0.95), 0.04, 0.28, M["fener"], rot=(math.radians(90), 0, 0), bev=0.005, parent=fpiv)
    cyl("fener_bas", (0.31, -0.72, 0.95), 0.065, 0.1, M["fener"], rot=(math.radians(90), 0, 0), r2=0.045, bev=0.005, parent=fpiv)
    cyl("fener_cam", (0.31, -0.772, 0.95), 0.058, 0.005, M["fener_cam"], rot=(math.radians(90), 0, 0), bev=0, parent=fpiv)
    bpy.ops.object.light_add(type="SPOT", location=(0.31, -0.78, 0.95), rotation=(math.radians(-90), 0, 0))
    spot = bpy.context.active_object
    spot.name = "fener_isik"
    spot.data.energy = 600
    spot.data.color = (1.0, 0.82, 0.6)
    spot.data.spot_size = math.radians(28)
    spot.data.spot_blend = 0.35
    spot.data.shadow_soft_size = 0.03
    set_parent(spot, fpiv)
    # görünür ışık huzmesi (havadaki toz)
    BL = 5.2
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.05, radius2=BL * math.tan(math.radians(13)),
                                    depth=BL, end_fill_type="NOTHING",
                                    location=(0.31, -0.78 - BL / 2, 0.95), rotation=(math.radians(90), 0, 0))
    beam = bpy.context.active_object
    beam.name = "huzme"
    smooth(beam)
    assign(beam, M["huzme"])
    beam.visible_shadow = False
    set_parent(beam, fpiv)
    # huzme parlaklığı fenerin gücünü izler (sürücü)
    val = M["huzme"].node_tree.nodes["huzme_guc"].outputs[0]
    fc = val.driver_add("default_value")
    v = fc.driver.variables.new()
    v.name = "e"
    v.targets[0].id_type = "LIGHT"
    v.targets[0].id = spot.data
    v.targets[0].data_path = "energy"
    fc.driver.expression = "e * 0.0012"
    # kafa
    head = empty("kemal_kafa", (0, 0, 1.18), parent=body)
    eyes, brows = [], []
    sphere("kafa", (0, 0, 1.42), (0.36, 0.34, 0.34), M["ten"], parent=head)
    sphere("burun", (0, -0.335, 1.38), (0.055, 0.045, 0.05), M["ten"], parent=head, segs=24)
    for s in (-1, 1):
        sphere(f"kulak_{s}", (s * 0.355, 0, 1.4), (0.04, 0.07, 0.09), M["ten"], parent=head, segs=24)
        sphere(f"goz_{s}", (s * 0.12, -0.3, 1.47), (0.042, 0.03, 0.05), M["goz"], parent=head, segs=24)
        # endişeli kaşlar: iç uçları yukarıda
        b = sphere(f"kas_{s}", (s * 0.125, -0.305, 1.56), (0.065, 0.02, 0.016), M["biyik"], segs=24)
        b.rotation_euler = (math.radians(-15), 0, 0)
        b.rotation_euler.y = s * math.radians(18)
        set_parent(b, head)
        bm = sphere(f"biyik_{s}", (s * 0.08, -0.315, 1.31), (0.1, 0.04, 0.035), M["biyik"], segs=24)
        bm.rotation_euler = (0, s * math.radians(12), s * math.radians(-10))
        set_parent(bm, head)
        eyes.append(bpy.data.objects[f"goz_{s}"])
        brows.append(b)
    mouth = sphere("agiz", (0, -0.29, 1.245), (0.035, 0.02, 0.04), M["oyuk"], parent=head, segs=24)
    mouth.scale = (0, 0, 0)
    # şapka
    cap = empty("sapka", (0, 0, 1.68), parent=head)
    cyl("sapka_govde", (0, 0, 1.72), 0.34, 0.16, M["uniforma"], r2=0.37, bev=0.02, parent=cap)
    cyl("sapka_bant", (0, 0, 1.67), 0.345, 0.05, M["ayakkabi"], bev=0.005, parent=cap)
    v = sphere("siper", (0, -0.27, 1.645), (0.26, 0.17, 0.025), M["ayakkabi"], parent=cap, segs=32)
    v.rotation_euler = (math.radians(-12), 0, 0)
    sphere("sapka_rozet", (0, -0.34, 1.73), (0.04, 0.012, 0.04), M["altin"], parent=cap, segs=16)
    cap.rotation_euler = (math.radians(-6), math.radians(4), 0)
    face = {"eyes": eyes, "brows": brows, "mouth": mouth, "larm": larm}
    return root, body, head, legs, fpiv, spot, face


# ----------------------------------------------------------------- animasyon
def animate_kemal(root, body, head, legs, fpiv, spot, face):
    # Ç1: koridorda +Y yönünde yürür (ön yüz -Y => rot z = pi)
    a, b = S1
    for f in range(a, b + 1):
        t = (f - a) / (b - a)
        y = 2.0 + 6.8 * t
        root.location = (1.0, y, 0)
        root.rotation_euler = (0, 0, math.pi)
        key(root, "location", f)
        key(root, "rotation_euler", f)
        ph = (f - a) / FPS * math.tau * 0.9
        body.location = (0, 0, abs(math.sin(ph)) * 0.035)
        body.rotation_euler = (0, math.sin(ph) * 0.04, 0)
        key(body, "location", f)
        key(body, "rotation_euler", f)
        for s, leg in zip((1, -1), legs):
            leg.rotation_euler = (s * math.sin(ph) * 0.45, 0, 0)
            key(leg, "rotation_euler", f)
        fpiv.rotation_euler = (math.radians(12), 0, math.sin(ph * 0.35) * 0.25)
        key(fpiv, "rotation_euler", f)
        face["larm"].rotation_euler = (-math.sin(ph) * 0.35, 0, 0)  # sol kol sallanır
        key(face["larm"], "rotation_euler", f)
    # Ç2: durur, sağa sola bakar
    a, b = S2
    for leg in legs:
        key(leg, "rotation_euler", a, (0, 0, 0))
    key(body, "location", a, (0, 0, 0))
    key(body, "rotation_euler", a, (0, 0, 0))
    key(root, "location", a, (1.0, 8.8, 0))
    key(fpiv, "rotation_euler", a, (math.radians(35), 0, 0))
    key(fpiv, "rotation_euler", b, (math.radians(35), 0, 0))
    for f, rz, rx in ((a, 0, 0), (a + 24, 0.5, -0.05), (a + 60, 0.5, -0.05),
                      (a + 84, -0.55, 0.0), (a + 115, -0.55, 0.0), (b, 0.05, 0.12)):
        key(head, "rotation_euler", f, (rx, 0, rz))
    key(face["larm"], "rotation_euler", a, (0, 0, 0))
    # göz kırpma
    for e in face["eyes"]:
        sc = tuple(e.scale)
        key(e, "scale", 1, sc)
        for f in (a + 14, a + 72, a + 128, S4[0] + 40):
            key(e, "scale", f - 1, sc)
            key(e, "scale", f + 1, (sc[0], sc[1], sc[2] * 0.1))
            key(e, "scale", f + 3, sc)
    # nefes alma
    for f in range(a, b + 1, 12):
        k = ((f - a) // 12) % 2
        key(body, "location", f, (0, 0, 0.012 * k))
    # Ç4–Ç6: heykellere dönük durur (-X'e bakar)
    a = S4[0]
    key(root, "location", a, (1.6, 10.2, 0), "CONSTANT")
    key(root, "rotation_euler", a, (0, 0, -math.pi / 2), "CONSTANT")
    key(head, "rotation_euler", a, (0.05, 0, 0), "CONSTANT")
    key(body, "location", a, (0, 0, 0), "CONSTANT")
    # fener tarama: heykel 3'e (y=13) bakış açısı ~ -0.6 rad
    sweep = [(S4[0], 0.75, -8), (S4[0] + 50, 0.2, -10), (S4[0] + 95, -0.25, -6), (S4[0] + 140, -0.95, -8),
             (S4[1], -1.1, -8),
             (S5[0], -1.1, -8), (S5[0] + 30, -0.68, -16), (S5[1], -0.66, -17),
             (S6[0], -0.66, -18), (SON, -0.67, -19)]
    for f, rz, rx in sweep:
        key(fpiv, "rotation_euler", f, (math.radians(rx), 0, rz))
    # heykeli görünce irkilip geri sıçrar (fener titrerken)
    jolt = S5[0] + 27
    key(body, "location", jolt, (0, 0, 0))
    key(body, "rotation_euler", jolt, (0, 0, 0))
    key(head, "rotation_euler", jolt, (0.05, 0, 0))
    key(body, "location", jolt + 5, (0, 0.24, 0.03))
    key(body, "rotation_euler", jolt + 5, (math.radians(-9), 0, 0))
    key(head, "rotation_euler", jolt + 5, (-0.12, 0, 0))
    key(body, "location", jolt + 16, (0, 0.22, 0))
    key(body, "rotation_euler", jolt + 16, (math.radians(-4), 0, 0))
    key(head, "rotation_euler", jolt + 16, (-0.04, 0, 0))
    # korkmuş yüz: gözler büyür, kaşlar kalkar, ağız açılır
    a5 = S5B[0]
    for e in face["eyes"]:
        sc = tuple(e.scale)
        key(e, "scale", a5 - 1, sc, "CONSTANT")
        key(e, "scale", a5, (sc[0] * 1.3, sc[1], sc[2] * 1.4), "CONSTANT")
    for b_ in face["brows"]:
        loc, rot = tuple(b_.location), tuple(b_.rotation_euler)
        key(b_, "location", a5 - 1, loc, "CONSTANT")
        key(b_, "rotation_euler", a5 - 1, rot, "CONSTANT")
        key(b_, "location", a5, (loc[0], loc[1], loc[2] + 0.035), "CONSTANT")
        key(b_, "rotation_euler", a5, (rot[0], rot[1] * 1.6, rot[2]), "CONSTANT")
    mo = face["mouth"]
    key(mo, "scale", a5 - 1, (0, 0, 0), "CONSTANT")
    key(mo, "scale", a5, (0.03, 0.02, 0.035), "CONSTANT")
    key(mo, "scale", S5B[1], (0.034, 0.02, 0.045))
    # titreyen el: fener sallanır
    for fc in fpiv.animation_data.action.fcurves:
        if fc.data_path == "rotation_euler" and fc.array_index in (0, 2):
            mod = fc.modifiers.new("NOISE")
            mod.scale = 4
            mod.strength = 0.035
            mod.phase = 7 * fc.array_index
            mod.use_restricted_range = True
            mod.frame_start = jolt
            mod.frame_end = SON
    # fener ışığı: titreme ve sönme
    spot.data.energy = 600
    spot.data.keyframe_insert("energy", frame=1)
    flick = [(S5[0] + 26, 600), (S5[0] + 28, 80), (S5[0] + 30, 600), (S5[0] + 33, 40), (S5[0] + 36, 600),
             (S6[0], 200), (SON - 30, 200), (SON - 28, 40), (SON - 26, 200), (SON - 20, 15), (SON - 18, 180),
             (SON - 14, 0)]
    for f, e in flick:
        spot.data.energy = e
        spot.data.keyframe_insert("energy", frame=f)
    set_all_interp(spot.data, "CONSTANT")
    # yürüyüş dışı tüm anahtarlar: S4 sonrası sabit geçişler
    for o in (root,):
        for fc in o.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                if kp.co[0] >= S1[1]:
                    kp.interpolation = "CONSTANT"


def animate_statues(statues, M):
    _, fig, head = statues[EVIL]
    key(fig, "rotation_euler", 1, (0, 0, math.radians(-90)), "CONSTANT")
    key(fig, "rotation_euler", S5[0], (0, 0, math.radians(90)), "CONSTANT")
    key(head, "rotation_euler", 1, (0, 0, 0), "CONSTANT")
    key(head, "rotation_euler", S5[0], (0, math.radians(-6), math.radians(4)), "CONSTANT")
    key(head, "rotation_euler", S6[0] + 40, (0, math.radians(-6), math.radians(4)))
    key(head, "rotation_euler", SON - 16, (0, math.radians(-13), math.radians(2)))
    # kırmızı titreyen ışık
    bpy.ops.object.light_add(type="POINT", location=(STATUE_X + 1.3, 13.9, 1.0))
    r = bpy.context.active_object
    r.name = "kirmizi"
    r.data.color = (1.0, 0.04, 0.02)
    r.data.shadow_soft_size = 0.2
    r.data.energy = 0
    r.data.keyframe_insert("energy", frame=1)
    r.data.keyframe_insert("energy", frame=S5[0] - 1)
    rnd = random.Random(3)
    for f in range(S5[0], SON + 1, 3):
        r.data.energy = rnd.choice([0, 20, 50, 80, 110, 130])
        r.data.keyframe_insert("energy", frame=f)
    r.data.energy = 0
    r.data.keyframe_insert("energy", frame=SON - 14)
    set_all_interp(r.data, "CONSTANT")
    # arkadan kırmızı kenar ışığı (yüz çekimi)
    bpy.ops.object.light_add(type="AREA", location=(STATUE_X - 0.8, 13.6, 3.3))
    rim = bpy.context.active_object
    rim.name = "kirmizi_kenar"
    look_at(rim, (STATUE_X, 13.0, 2.7))
    rim.data.size = 0.6
    rim.data.color = (1.0, 0.08, 0.05)
    rim.data.energy = 0
    rim.data.keyframe_insert("energy", frame=1)
    rim.data.energy = 90
    rim.data.keyframe_insert("energy", frame=S5[0])
    rim.data.energy = 0
    rim.data.keyframe_insert("energy", frame=SON - 14)
    set_all_interp(rim.data, "CONSTANT")
    # Kemal'in yüz çekimi: heykel tarafından vuran titrek kırmızı + çok zayıf sıcak dolgu
    bpy.ops.object.light_add(type="POINT", location=(0.6, 10.9, 1.9))
    kr = bpy.context.active_object
    kr.name = "yuz_kirmizi"
    kr.data.color = (1.0, 0.05, 0.03)
    kr.data.shadow_soft_size = 0.3
    rnd = random.Random(4)
    kr.data.energy = 0
    kr.data.keyframe_insert("energy", frame=1)
    for f in range(S5B[0], S5B[1] + 1, 3):
        kr.data.energy = rnd.choice([3, 8, 15, 22, 28])
        kr.data.keyframe_insert("energy", frame=f)
    kr.data.energy = 0
    kr.data.keyframe_insert("energy", frame=S5B[1] + 1)
    set_all_interp(kr.data, "CONSTANT")
    bpy.ops.object.light_add(type="POINT", location=(0.9, 9.6, 1.0))
    wf = bpy.context.active_object
    wf.name = "yuz_dolgu"
    wf.data.color = (1.0, 0.8, 0.6)
    wf.data.shadow_soft_size = 0.4
    for f, e in ((1, 0), (S5B[0], 6), (S5B[1] + 1, 0)):
        wf.data.energy = e
        wf.data.keyframe_insert("energy", frame=f)
    set_all_interp(wf.data, "CONSTANT")


# ----------------------------------------------------------------- kameralar
def camera(name, lens, focus=None, fstop=2.8):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = 36
    cam = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(cam)
    if focus is not None:
        cd.dof.use_dof = True
        cd.dof.focus_object = focus
        cd.dof.aperture_fstop = fstop
    return cam


def cam_move(cam, frames_locs_targets):
    for f, loc, tgt in frames_locs_targets:
        cam.location = loc
        look_at(cam, tgt)
        cam.keyframe_insert("location", frame=f)
        cam.keyframe_insert("rotation_euler", frame=f)


def handheld(cam, a, b, amp=0.004, seed=1):
    """Hafif el kamerası sallantısı."""
    rnd = random.Random(seed)
    fcs = [fc for fc in cam.animation_data.action.fcurves if fc.data_path == "rotation_euler"]
    for fc in fcs:
        mod = fc.modifiers.new("NOISE")
        mod.scale = 30
        mod.strength = amp * 2
        mod.phase = rnd.uniform(0, 100)
        mod.use_restricted_range = True
        mod.frame_start = a
        mod.frame_end = b


def build_cameras(kemal_head, statue_heads):
    scn = bpy.context.scene
    # odak hedefleri
    f_kemal = empty("odak_kemal", parent=None)
    f_kemal.parent = kemal_head
    f_kemal.location = (0, 0, 0.3)
    f_heykel = empty("odak_heykel", (STATUE_X + 0.1, 13.0, 2.75))
    f_heykel_genel = empty("odak_heykeller", (STATUE_X, 12.0, 2.0))
    f_saat = empty("odak_saat", (HALL_W / 2, CLOCK_Y, 3.4))

    c1 = camera("K1_yuruyus", 24, f_kemal, 4.0)
    cam_move(c1, [(S1[0], (1.35, -0.2, 1.05), (0.6, 8, 1.4)),
                  (S1[1], (1.35, 4.8, 1.2), (0.7, 14, 1.5))])
    handheld(c1, *S1, seed=1)

    c2 = camera("K2_kemal", 55, f_kemal, 2.2)
    cam_move(c2, [(S2[0], (1.0, 11.4, 1.5), (1.0, 8.8, 1.45)),
                  (S2[1], (1.0, 10.6, 1.45), (1.0, 8.8, 1.45))])
    handheld(c2, *S2, seed=2)

    c3 = camera("K3_saat", 45, f_saat, 2.0)
    # sabit kamera: yalnız yelkovan oynar (render'da kare tasarrufu)
    cam_move(c3, [(S3[0], (2.3, CLOCK_Y - 0.3, 3.25), (HALL_W / 2, CLOCK_Y, 3.4)),
                  (S3[1], (2.3, CLOCK_Y - 0.3, 3.25), (HALL_W / 2, CLOCK_Y, 3.4))])

    c4 = camera("K4_omuz", 32, f_heykel_genel, 4.0)
    cam_move(c4, [(S4[0], (3.3, 8.2, 2.05), (-2.0, 13.2, 1.7)),
                  (S5[1], (3.1, 8.45, 2.0), (-2.0, 13.2, 1.7))])
    handheld(c4, S4[0], S5[1], seed=4)

    c5 = camera("K5_korku", 50, f_kemal, 2.2)
    cam_move(c5, [(S5B[0], (0.05, 9.92, 1.56), (1.82, 10.2, 1.5)),
                  (S5B[1], (0.35, 9.98, 1.53), (1.82, 10.2, 1.5))])
    handheld(c5, *S5B, amp=0.006, seed=5)

    c6 = camera("K6_yuz", 85, f_heykel, 2.0)
    cam_move(c6, [(S6[0], (0.7, 12.75, 2.5), (STATUE_X, 13.0, 2.7)),
                  (SON, (-1.15, 12.95, 2.7), (STATUE_X, 13.0, 2.72))])
    handheld(c6, *S6, amp=0.003, seed=6)

    for cam, f in ((c1, S1[0]), (c2, S2[0]), (c3, S3[0]), (c4, S4[0]), (c5, S5B[0]), (c6, S6[0])):
        m = scn.timeline_markers.new(cam.name, frame=f)
        m.camera = cam
    scn.camera = c1
    # kesmeler arası enterpolasyon karışmasın
    for cam in (c1, c2, c3, c4, c5, c6):
        for fc in cam.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "BEZIER"
                kp.easing = "EASE_IN_OUT"


# ----------------------------------------------------------------- render
def setup_render(quality, out):
    scn = bpy.context.scene
    scn.render.engine = "CYCLES"
    cy = scn.cycles
    cy.device = "CPU"
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = 0.08
    cy.samples = 12 if quality == "final" else 8
    cy.use_denoising = True
    cy.denoiser = "OPENIMAGEDENOISE"
    cy.max_bounces = 3
    cy.diffuse_bounces = 1
    cy.glossy_bounces = 1
    cy.transmission_bounces = 2
    cy.volume_bounces = 0
    cy.caustics_reflective = False
    cy.caustics_refractive = False
    cy.blur_glossy = 1.0
    scn.render.use_persistent_data = True
    scn.render.fps = FPS
    scn.render.resolution_x = 540 if quality == "final" else 360
    scn.render.resolution_y = 960 if quality == "final" else 640
    scn.render.resolution_percentage = 100
    scn.render.use_motion_blur = False
    scn.render.motion_blur_shutter = 0.5
    scn.view_settings.view_transform = "AgX"
    scn.view_settings.look = "AgX - Medium High Contrast"
    scn.view_settings.exposure = -0.2
    scn.render.image_settings.file_format = "PNG"
    scn.render.image_settings.color_depth = "8"
    scn.render.filepath = out.rstrip("/") + "/####"
    scn.frame_start = 1
    scn.frame_end = SON
    # dünya: çok koyu mavi
    w = bpy.data.worlds.new("dunya")
    scn.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.004, 0.006, 0.012, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0


def build():
    reset()
    M = materials()
    build_hall(M)
    build_clock(M)
    statues = [build_statue(M, i, y) for i, y in enumerate(STATUE_YS)]
    kemal = build_kemal(M)
    animate_kemal(*kemal)
    animate_statues(statues, M)
    build_cameras(kemal[2], [s[2] for s in statues])
    # tavanda zayıf dolgu ışığı (gölgeler simsiyah kalmasın)
    bpy.ops.object.light_add(type="AREA", location=(0, 12, HALL_H - 0.4), rotation=(0, 0, 0))
    fill = bpy.context.active_object
    fill.name = "dolgu"
    fill.data.shape = "RECTANGLE"
    fill.data.size = 3
    fill.data.size_y = 20
    fill.data.energy = 12
    fill.data.color = (0.5, 0.6, 1.0)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--cikti", required=True)
    ap.add_argument("--kalite", default="test", choices=["test", "final"])
    ap.add_argument("--kare", default=None, help="ör. 1-816 veya 1,130,300")
    ap.add_argument("--blend", default=None)
    args = ap.parse_args(argv)
    build()
    setup_render(args.kalite, args.cikti)
    scn = bpy.context.scene
    if args.blend:
        bpy.ops.wm.save_as_mainfile(filepath=args.blend)
    spec = args.kare or f"1-{SON}"
    frames = []
    for part in spec.split(","):
        if "-" in part:
            a, b = map(int, part.split("-"))
            frames += range(a, b + 1)
        else:
            frames.append(int(part))
    import os
    for f in frames:
        out = os.path.join(args.cikti, f"{f:04d}.png")
        if os.path.exists(out):  # yarıda kalırsa kaldığı yerden devam
            continue
        scn.frame_set(f)
        scn.render.filepath = out
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
