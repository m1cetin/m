"""GAZİANTEP KALESİ – "...yaptın" formatında 3D sahne (Blender / Cycles).

Sade, oyuncak gibi bir diorama: kesitli bir toprak bloğunun üstünde tepe; seslendirmedeki
her cümlede kaleye yeni bir parça "pop" diye eklenir. Zamanlar cumle_zamanlari.json'dan gelir.

Kullanım:
  python sahne.py --cikti kareler/ --kalite onizleme --kare 1,100,200
  python sahne.py --cikti kareler/ --kalite final --kare 1-1380
"""
import argparse
import json
import math
import os
import random
import sys

import bpy
from mathutils import Vector

FPS = 24
KOK = os.path.dirname(os.path.abspath(__file__))
Z = json.load(open(os.path.join(KOK, "cumle_zamanlari.json")))
T = [c["bas"] for c in Z]          # her cümlenin başlangıç saniyesi
BITIS = Z[-1]["son"] + 2.2          # son karttan sonra kısa bekleme
SON_KARE = int(BITIS * FPS)


def F(sn):
    return int(round(sn * FPS)) + 1


random.seed(7)

# ---------------------------------------------------------------- yardımcılar

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, rough=0.6, emit=None, emit_str=0.0, alpha=1.0, trans=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = emit_str
    if trans:
        b.inputs["Transmission Weight"].default_value = trans
        b.inputs["IOR"].default_value = 1.33
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
    return m


def noisy(m, scale=6.0, dark=0.82, bump=0.25):
    """Taş / toprak için hafif renk oynaması ve pürüz."""
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    base = b.inputs["Base Color"].default_value[:]
    tex = nt.nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = scale
    tex.inputs["Detail"].default_value = 6
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (base[0] * dark, base[1] * dark, base[2] * dark, 1)
    ramp.color_ramp.elements[1].color = base
    nt.links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = bump
    nt.links.new(tex.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


def assign(o, m):
    o.data.materials.clear()
    o.data.materials.append(m)


def bevel(o, w=0.03, seg=2):
    md = o.modifiers.new("bev", "BEVEL")
    md.width = w
    md.segments = seg
    md.limit_method = "ANGLE"


def box(name, loc, size, m, bev=0.03, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(scale=True)
    if bev:
        bevel(o, bev)
    assign(o, m)
    return o


def cyl(name, loc, r, h, m, verts=32, bev=0.03, r2=None):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h, location=loc)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r2, depth=h, location=loc)
    o = bpy.context.object
    o.name = name
    if bev:
        bevel(o, bev)
    assign(o, m)
    bpy.ops.object.shade_smooth()
    return o


def empty(name, loc=(0, 0, 0)):
    o = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    return o


def parent(ch, p):
    mw = ch.matrix_world.copy()
    ch.parent = p
    ch.matrix_parent_inverse = p.matrix_world.inverted()
    ch.matrix_world = mw


def key(o, path, frame, value, interp="BEZIER"):
    setattr(o, path, value)
    o.keyframe_insert(path, frame=frame)
    fc = o.animation_data.action.fcurves if hasattr(o.animation_data.action, "fcurves") else None
    if fc is not None:
        for c in fc:
            if c.data_path == path:
                for k in c.keyframe_points:
                    if int(k.co[0]) == frame:
                        k.interpolation = interp


def pop(o, frame, dur=8, final=None):
    """Nesneyi 0'dan büyüterek, hafif taşmayla 'pop' diye sahneye getirir."""
    s = tuple(final or o.scale)
    key(o, "scale", 1, (0.0001,) * 3, "CONSTANT")
    key(o, "scale", frame, (0.0001,) * 3)
    key(o, "scale", frame + int(dur * 0.65), tuple(v * 1.12 for v in s))
    key(o, "scale", frame + dur, s)


def rise(o, frame, depth=3.0, dur=14):
    """Nesne topraktan yukarı yükselerek gelir (surlar, kuleler)."""
    z = o.location.z
    key(o, "location", 1, (o.location.x, o.location.y, z - depth), "CONSTANT")
    key(o, "location", frame, (o.location.x, o.location.y, z - depth))
    key(o, "location", frame + dur, (o.location.x, o.location.y, z))


# ---------------------------------------------------------------- malzemeler

def materials():
    M = {}
    M["toprak"] = noisy(mat("toprak", (0.36, 0.20, 0.10), 0.9), 4, 0.75, 0.4)
    M["toprak_koyu"] = noisy(mat("toprak_koyu", (0.25, 0.15, 0.08), 0.95), 5, 0.7, 0.4)
    M["kum"] = noisy(mat("kum", (0.62, 0.45, 0.28), 0.95), 3, 0.85, 0.3)
    M["cim"] = noisy(mat("cim", (0.22, 0.40, 0.08), 0.9), 8, 0.8, 0.2)
    M["tas"] = noisy(mat("tas", (0.78, 0.66, 0.48), 0.75), 10, 0.85, 0.35)
    M["tas_koyu"] = noisy(mat("tas_koyu", (0.58, 0.50, 0.40), 0.8), 10, 0.85, 0.35)
    M["kaya"] = noisy(mat("kaya", (0.50, 0.38, 0.26), 0.85), 3, 0.7, 0.6)
    M["su"] = mat("su", (0.05, 0.45, 0.65), 0.05, trans=0.2)
    M["ahsap"] = noisy(mat("ahsap", (0.40, 0.24, 0.12), 0.7), 20, 0.8, 0.2)
    M["kiremit"] = mat("kiremit", (0.65, 0.22, 0.12), 0.6)
    M["kirmizi"] = mat("kirmizi", (0.80, 0.03, 0.05), 0.5)
    M["beyaz"] = mat("beyaz", (0.95, 0.95, 0.95), 0.5)
    M["bakir"] = mat("bakir", (0.85, 0.42, 0.20), 0.25)
    M["bakir"].node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 1.0
    M["duman"] = mat("duman", (0.85, 0.85, 0.85), 1.0)
    M["ates"] = mat("ates", (1.0, 0.5, 0.1), 0.5, emit=(1.0, 0.45, 0.08), emit_str=6)
    M["baklava"] = mat("baklava", (0.85, 0.58, 0.20), 0.4)
    M["fistik"] = mat("fistik", (0.35, 0.60, 0.15), 0.6)
    M["kumas"] = mat("kumas", (0.70, 0.15, 0.12), 0.8)
    M["ten"] = mat("ten", (0.85, 0.62, 0.48), 0.6)
    M["lacivert"] = mat("lacivert", (0.10, 0.14, 0.30), 0.7)
    return M


# ---------------------------------------------------------------- dünya

def world():
    w = bpy.data.worlds.new("dunya")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "NISHITA" if "NISHITA" in [i.identifier for i in sky.bl_rna.properties["sky_type"].enum_items] else sky.sky_type
    try:
        sky.sun_elevation = math.radians(35)
        sky.sun_rotation = math.radians(140)
        sky.altitude = 500
    except Exception:
        pass
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.18
    return bg, sky


def sun():
    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(50), math.radians(10), math.radians(140)))
    s = bpy.context.object
    s.data.energy = 3.2
    s.data.angle = math.radians(3)
    s.data.color = (1.0, 0.96, 0.88)
    return s


# ---------------------------------------------------------------- diorama

R_TEPE = 3.2      # tepe taban yarıçapı
H_TEPE = 1.6      # tepe yüksekliği
BLOK = 11.0       # kesit bloğu kenarı
DERIN = 2.4       # bloğun toprak derinliği


def diorama(M):
    # Kesitli toprak bloğu (yanları görünen tabakalar)
    katman = [(0.0, 0.35, "kum"), (-0.35, 0.9, "toprak"), (-1.25, 1.15, "toprak_koyu")]
    for z, h, mn in katman:
        box(f"katman_{mn}", (0, 0, z - h / 2), (BLOK, BLOK, h), M[mn], bev=0.02)
    # Uzaktaki çöl zemini (blok bunun üstünde yüzüyor gibi görünmesin diye aşağıda)
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -DERIN - 0.01))
    yer = bpy.context.object
    assign(yer, noisy(mat("uzak_zemin", (0.35, 0.26, 0.17), 0.95), 0.6, 0.7, 0.1))
    # Tepe: yumuşak, basık bir koni + üstü düz
    bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=R_TEPE, radius2=1.7, depth=H_TEPE,
                                    location=(0, 0, H_TEPE / 2))
    tepe = bpy.context.object
    tepe.name = "tepe"
    assign(tepe, M["kaya"])
    bpy.ops.object.shade_smooth()
    try:
        bpy.ops.object.shade_auto_smooth(angle=math.radians(40))
    except Exception:
        pass
    # Tepenin üstü çim
    c = cyl("tepe_ust", (0, 0, H_TEPE + 0.01), 1.68, 0.04, M["cim"], verts=64, bev=0.01)
    # Kesitte görünen kaya çatlağı (sarnıç bölümünde işe yarar)
    return tepe


# ---------------------------------------------------------------- kale parçaları

def burc(name, loc, r, h, M, mazgal=True):
    """Yuvarlak burç: gövde + mazgallı taç."""
    g = empty(name, loc)
    gov = cyl(name + "_govde", (loc[0], loc[1], loc[2] + h / 2), r, h, M["tas"], verts=32, bev=0.02)
    parent(gov, g)
    tac = cyl(name + "_tac", (loc[0], loc[1], loc[2] + h + 0.06), r * 1.12, 0.12, M["tas_koyu"], verts=32, bev=0.02)
    parent(tac, g)
    if mazgal:
        n = 8
        for i in range(n):
            a = 2 * math.pi * i / n
            m_ = box(f"{name}_m{i}", (loc[0] + math.cos(a) * r * 1.02, loc[1] + math.sin(a) * r * 1.02,
                                      loc[2] + h + 0.2), (0.16, 0.16, 0.18), M["tas"], bev=0.01,
                     rot=(0, 0, a))
            parent(m_, g)
    return g


def sur_halkasi(M, r, z, h, kalinlik, n=28, bosluk=None):
    """Tepenin üstünü çevreleyen sur: halka şeklinde dizilmiş duvar blokları + mazgallar."""
    g = empty("sur", (0, 0, z))
    parcalar = []
    for i in range(n):
        a = 2 * math.pi * (i + 0.5) / n
        if bosluk and any(abs((a - b + math.pi) % (2 * math.pi) - math.pi) < 0.12 for b in bosluk):
            continue
        L = 2 * math.pi * r / n * 1.02
        p = box(f"sur_{i}", (math.cos(a) * r, math.sin(a) * r, z + h / 2), (kalinlik, L, h), M["tas"],
                bev=0.015, rot=(0, 0, a))
        mz = box(f"sur_mz_{i}", (math.cos(a) * (r + kalinlik * 0.3), math.sin(a) * (r + kalinlik * 0.3), z + h + 0.09),
                 (kalinlik * 0.4, L * 0.45, 0.18), M["tas"], bev=0.01, rot=(0, 0, a))
        parent(p, g)
        parent(mz, p)
        parcalar.append(p)
    return g, parcalar


def hendek(M):
    """Tepe eteğinde koyu bir hendek halkası + kapıya giden ahşap köprü."""
    bpy.ops.mesh.primitive_torus_add(major_radius=R_TEPE + 0.55, minor_radius=0.42,
                                     major_segments=96, minor_segments=16, location=(0, 0, 0.0))
    h = bpy.context.object
    h.name = "hendek"
    h.scale.z = 0.25
    assign(h, M["toprak_koyu"])
    bpy.ops.object.shade_smooth()
    kopru = box("kopru", (0, -(R_TEPE + 0.55), 0.14), (0.55, 1.2, 0.08), M["ahsap"], bev=0.01)
    return h, kopru


def sarnic(M):
    """Bloğun ön kesitinde görünen, kayaya oyulmuş kemerli sarnıç (su dolu)."""
    g = empty("sarnic", (0, -BLOK / 2, -0.9))
    oyuk = box("sarnic_oyuk", (0, -BLOK / 2 + 0.25, -0.95), (2.0, 0.6, 1.1), M["tas_koyu"], bev=0.02)
    parent(oyuk, g)
    su = box("sarnic_su", (0, -BLOK / 2 - 0.02, -1.25), (1.8, 0.1, 0.45), M["su"], bev=0.0)
    parent(su, g)
    for x in (-0.6, 0.6):
        k = box(f"sarnic_ayak_{x}", (x, -BLOK / 2 - 0.03, -0.95), (0.16, 0.1, 1.1), M["tas"], bev=0.01)
        parent(k, g)
    ust = box("sarnic_ust", (0, -BLOK / 2 - 0.03, -0.38), (2.1, 0.1, 0.14), M["tas"], bev=0.01)
    parent(ust, g)
    # Sarnıçtan kaleye çıkan ince su kanalı
    kanal = box("sarnic_kanal", (0, -BLOK / 2 - 0.02, -0.1), (0.12, 0.08, 0.6), M["su"], bev=0.0)
    parent(kanal, g)
    return g


def bayrak(M, loc):
    g = empty("bayrak", loc)
    direk = cyl("direk", (loc[0], loc[1], loc[2] + 0.6), 0.025, 1.2, M["beyaz"], verts=12, bev=0.0)
    parent(direk, g)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(loc[0] + 0.33, loc[1], loc[2] + 1.0))
    b = bpy.context.object
    b.name = "bayrak_bez"
    b.rotation_euler = (math.radians(90), 0, 0)
    b.scale = (0.6, 0.4, 1)
    md = b.modifiers.new("dalga", "WAVE")
    md.height = 0.04
    md.width = 0.4
    md.speed = 0.08
    md.start_position_x = -0.3
    sub = b.modifiers.new("ss", "SUBSURF")
    sub.levels = 3
    sub.render_levels = 3
    sub.subdivision_type = "SIMPLE"
    md2 = b.modifiers.new("dalga2", "WAVE")
    md2.height = 0.04
    b.modifiers.move(2, 0)  # önce böl, sonra dalgala
    assign(b, M["kirmizi"])
    # Ay-yıldız: bayrağın üstüne beyaz ince diskler
    ay = cyl("ay", (loc[0] + 0.2, loc[1] - 0.012, loc[2] + 1.0), 0.11, 0.005, M["beyaz"], verts=32, bev=0.0)
    ay.rotation_euler = (math.radians(90), 0, 0)
    ic = cyl("ay_ic", (loc[0] + 0.235, loc[1] - 0.014, loc[2] + 1.0), 0.09, 0.006, M["kirmizi"], verts=32, bev=0.0)
    ic.rotation_euler = (math.radians(90), 0, 0)
    bpy.ops.mesh.primitive_circle_add(vertices=5, radius=0.05, fill_type="TRIFAN",
                                      location=(loc[0] + 0.36, loc[1] - 0.015, loc[2] + 1.0),
                                      rotation=(math.radians(90), 0, math.radians(90 - 18)))
    y = bpy.context.object
    assign(y, M["beyaz"])
    for o in (b, ay, ic, y):
        parent(o, g)
    return g


def kisi(M, loc, govde_mat, rot=0.0, oturan=False):
    """Basit, yüzsüz oyuncak insan figürü."""
    g = empty("kisi", loc)
    zb = 0.0 if not oturan else -0.12
    parcalar = [
        cyl("bacak", (loc[0], loc[1], loc[2] + 0.18 + zb), 0.06, 0.36 if not oturan else 0.12, M["lacivert"], verts=12, bev=0.01),
        cyl("govde", (loc[0], loc[1], loc[2] + 0.48 + zb), 0.09, 0.3, govde_mat, verts=16, bev=0.02),
        cyl("bas", (loc[0], loc[1], loc[2] + 0.72 + zb), 0.075, 0.15, M["ten"], verts=16, bev=0.04),
    ]
    for p in parcalar:
        parent(p, g)
    g.rotation_euler.z = rot
    return g


def carsi(M):
    """Kale eteğinde bakırcı çarşısı: kiremit çatılı küçük dükkânlar ve parlayan bakır kaplar."""
    g = empty("carsi")
    dukkanlar = []
    for i, (x, y) in enumerate([(-3.0, -4.6), (-1.6, -4.6), (1.6, -4.6), (3.0, -4.6)]):
        d = empty(f"dukkan_{i}", (x, y, 0))
        govde = box(f"dk_{i}", (x, y, 0.35), (1.1, 0.8, 0.7), M["tas"], bev=0.02)
        cati = box(f"dk_cati_{i}", (x, y + 0.05, 0.76), (1.25, 1.0, 0.1), M["kiremit"], bev=0.02,
                   rot=(math.radians(-8), 0, 0))
        tente = box(f"dk_tente_{i}", (x, y - 0.55, 0.62), (1.0, 0.4, 0.03), M["kumas"], bev=0.0,
                    rot=(math.radians(18), 0, 0))
        for p in (govde, cati, tente):
            parent(p, d)
        for j in range(3):
            k = cyl(f"bakir_{i}_{j}", (x - 0.3 + j * 0.3, y - 0.5, 0.12), 0.11, 0.18, M["bakir"],
                    verts=24, bev=0.03, r2=0.07)
            parent(k, d)
        parent(d, g)
        dukkanlar.append(d)
    return g, dukkanlar


def manzara_masasi(M):
    """Kalenin önünde iki kişilik bank, masa, çay ve bir dilim baklava (fıstıklı)."""
    g = empty("masa", (2.6, -2.2, 0.0))
    x, y = 2.6, -2.2
    bank = box("bank", (x, y + 0.3, 0.22), (1.1, 0.3, 0.06), M["ahsap"], bev=0.01)
    masa = box("masa_ust", (x, y - 0.15, 0.36), (0.7, 0.45, 0.05), M["ahsap"], bev=0.01)
    ayak = box("masa_ayak", (x, y - 0.15, 0.17), (0.08, 0.08, 0.34), M["ahsap"], bev=0.0)
    tabak = cyl("tabak", (x + 0.12, y - 0.15, 0.40), 0.12, 0.02, M["beyaz"], verts=32, bev=0.005)
    bk = box("baklava", (x + 0.12, y - 0.15, 0.44), (0.14, 0.14, 0.06), M["baklava"], bev=0.01,
             rot=(0, 0, math.radians(45)))
    fs = box("baklava_fistik", (x + 0.12, y - 0.15, 0.475), (0.11, 0.11, 0.012), M["fistik"], bev=0.0,
             rot=(0, 0, math.radians(45)))
    cay = cyl("cay", (x - 0.18, y - 0.12, 0.44), 0.035, 0.1, M["kirmizi"], verts=16, bev=0.005)
    for p in (bank, masa, ayak, tabak, bk, fs, cay):
        parent(p, g)
    k1 = kisi(M, (x - 0.25, y + 0.3, 0.25), M["lacivert"], oturan=True)
    k2 = kisi(M, (x + 0.25, y + 0.3, 0.25), M["kumas"], oturan=True)
    parent(k1, g)
    parent(k2, g)
    return g, bk


def duman(M, loc, frame, n=5):
    """Top atışı: kısa bir alev parlaması + büyüyüp sönen duman topları."""
    for i in range(n):
        p = (loc[0] + random.uniform(-0.2, 0.2), loc[1] + random.uniform(-0.2, 0.2), loc[2] + random.uniform(0, 0.3))
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.25, location=p)
        s = bpy.context.object
        assign(s, M["duman"] if i else M["ates"])
        bpy.ops.object.shade_smooth()
        f0 = frame + i * 2
        key(s, "scale", 1, (0.0001,) * 3, "CONSTANT")
        key(s, "scale", f0, (0.0001,) * 3)
        key(s, "scale", f0 + 6, (1.0,) * 3)
        key(s, "location", f0 + 6, tuple(p))
        key(s, "location", f0 + 30, (p[0], p[1], p[2] + 0.8))
        key(s, "scale", f0 + 30, (1.4,) * 3)
        key(s, "scale", f0 + 40, (0.0001,) * 3)


# ---------------------------------------------------------------- kurgu

def build():
    M = materials()
    bg, sky = world()
    gunes = sun()
    diorama(M)

    # 1) Gözetleme kulesi (cümle 2)
    kule = burc("kule", (0, 0, H_TEPE), 0.42, 1.5, M)
    rise(kule, F(T[1] + 2.4), depth=1.6, dur=12)

    # 2) Surlar (cümle 3) — yükselerek gelir
    sur, sur_parca = sur_halkasi(M, 1.55, H_TEPE, 0.55, 0.22, bosluk=[-math.pi / 2])
    rise(sur, F(T[2] + 2.4), depth=0.7, dur=14)

    # 3) Hendek + köprü (cümle 4)
    h, kopru = hendek(M)
    pop(h, F(T[3] + 2.4), dur=10)
    pop(kopru, F(T[3] + 3.2), dur=8)

    # 4) Sarnıç (cümle 5) — kesitte belirir
    s = sarnic(M)
    pop(s, F(T[4] + 2.6), dur=10)

    # 5) Yüzyıllar: her medeniyet bir burç ekler (cümle 6)
    burclar = []
    acilar = [math.radians(a) for a in (20, 75, 130, 200, 250, 320)]
    for i, a in enumerate(acilar):
        b = burc(f"burc_{i}", (math.cos(a) * 1.58, math.sin(a) * 1.58, H_TEPE), 0.26, 0.85, M)
        pop(b, F(T[5] + 1.2 + i * 0.55), dur=8)
        burclar.append(b)
    # Kale kapısı (iki burç arası kemer)
    kapi = box("kapi", (0, -1.62, H_TEPE + 0.32), (0.5, 0.3, 0.64), M["tas_koyu"], bev=0.02)
    pop(kapi, F(T[5] + 0.6), dur=8)

    # 6) 1920 kuşatması: etrafta top atışları (cümle 7)
    for i, a in enumerate((200, 250, 300, 340, 160)):
        r = R_TEPE + 1.8
        duman(M, (math.cos(math.radians(a)) * r, math.sin(math.radians(a)) * r, 0.15), F(T[6] + 1.0 + i * 0.6))

    # 7) Gazi: kulenin tepesinde bayrak (cümle 8)
    bk = bayrak(M, (0, 0, H_TEPE + 1.72))
    pop(bk, F(T[7] + 2.2), dur=10)

    # 8) Deprem (cümle 9): iki burç ve birkaç sur parçası yamaçtan aşağı devrilir, 10. cümlede geri gelir
    dusenler = [burclar[3], burclar[4]] + [sur_parca[i] for i in (17, 18, 19, 21)]
    f_dep = F(T[8] + 1.4)
    f_geri = F(T[9] + 1.0)
    for i, o in enumerate(dusenler):
        loc0 = o.location.copy()
        rot0 = o.rotation_euler.copy()
        dis = Vector((loc0.x, loc0.y, 0)).normalized() if loc0.length > 0.1 else Vector((-0.7, -0.7, 0))
        if o.parent is not None and o.parent.name == "sur":
            # sur parçası: dünya koordinatı halka yarıçapında
            dis = Vector((o.matrix_world.translation.x, o.matrix_world.translation.y, 0)).normalized()
        hedef = loc0 + dis * 1.2 + Vector((0, 0, -0.9))
        key(o, "location", f_dep + i, tuple(loc0))
        key(o, "rotation_euler", f_dep + i, tuple(rot0))
        key(o, "location", f_dep + 14 + i, tuple(hedef))
        key(o, "rotation_euler", f_dep + 14 + i, (rot0.x + dis.y * 1.3, rot0.y - dis.x * 1.3, rot0.z + 0.4))
        key(o, "location", f_geri + i * 2, tuple(hedef))
        key(o, "rotation_euler", f_geri + i * 2, (rot0.x + dis.y * 1.3, rot0.y - dis.x * 1.3, rot0.z + 0.4))
        key(o, "location", f_geri + 12 + i * 2, tuple(loc0))
        key(o, "rotation_euler", f_geri + 12 + i * 2, tuple(rot0))
    # Taşlara numara: geri gelirken kısa parlama yok; sade tutuyoruz.

    # 9) Bakırcı çarşısı + manzara masası + gün batımı (cümle 11)
    c, dukkanlar = carsi(M)
    for i, d in enumerate(dukkanlar):
        pop(d, F(T[10] + 0.6 + i * 0.35), dur=8)
    masa, baklava = manzara_masasi(M)
    pop(masa, F(T[10] + 4.6), dur=10)

    # Işık: gün batımına (pembe-turuncu) geçiş
    f_gb0, f_gb1 = F(T[10] + 2.0), F(T[10] + 5.0)
    for f, en, rk, el in ((f_gb0, 4.0, (1.0, 0.96, 0.88), 35), (f_gb1, 3.0, (1.0, 0.55, 0.45), 6)):
        gunes.data.energy = en
        gunes.data.keyframe_insert("energy", frame=f)
        gunes.data.color = rk
        gunes.data.keyframe_insert("color", frame=f)
        gunes.rotation_euler = (math.radians(90 - el), math.radians(10), math.radians(140))
        gunes.keyframe_insert("rotation_euler", frame=f)
        try:
            sky.sun_elevation = math.radians(el)
            sky.keyframe_insert("sun_elevation", frame=f)
        except Exception:
            pass

    kamera()
    deprem_sarsinti(f_dep)


# ---------------------------------------------------------------- kamera

def kamera():
    """Diorama etrafında yavaş dönen, her adımda ilgili parçaya yaklaşan kamera."""
    hedef = empty("kamera_hedef", (0, 0, 1.2))
    bpy.ops.object.camera_add()
    cam = bpy.context.object
    cam.data.lens = 32
    cam.data.dof.use_dof = False
    bpy.context.scene.camera = cam
    con = cam.constraints.new("TRACK_TO")
    con.target = hedef
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"

    def nokta(aci, uzak, yuks):
        a = math.radians(aci)
        return (math.cos(a) * uzak, math.sin(a) * uzak, yuks)

    # (saniye, açı, uzaklık, yükseklik, hedef)
    plan = [
        (0.0, -60, 15.0, 9.0, (0, 0, 0.6)),
        (T[1], -75, 9.0, 5.5, (0, 0, 2.0)),        # kule
        (T[2], -95, 10.0, 6.0, (0, 0, 1.8)),       # surlar
        (T[3], -110, 12.0, 6.5, (0, -1.5, 0.5)),   # hendek
        (T[4], -90, 13.5, 1.6, (0, -BLOK / 2 + 1.5, -0.2)),  # sarnıç (kesite önden bakış)
        (T[5], -60, 11.0, 6.5, (0, 0, 1.8)),       # burçlar
        (T[6], -30, 15.0, 7.0, (0, 0, 0.8)),       # kuşatma
        (T[7], -70, 6.5, 4.6, (0, 0, 3.0)),        # bayrak
        (T[8], -100, 12.0, 5.0, (0, 0, 1.0)),      # deprem
        (T[9], -80, 10.0, 6.0, (0, 0, 1.6)),       # yeniden örme
        (T[10], -50, 12.0, 4.0, (0, -3, 0.6)),     # çarşı
        (T[10] + 4.2, -40, 7.5, 2.8, (2.4, -2.2, 0.5)),  # masa ve baklava
        (T[11], -60, 17.0, 10.0, (0, 0, 0.8)),     # final geniş plan
        (BITIS, -45, 18.0, 10.5, (0, 0, 0.8)),
    ]
    for i, (sn, aci, uz, yk, hd) in enumerate(plan):
        f = F(sn)
        key(cam, "location", f, nokta(aci, uz, yk))
        key(hedef, "location", f, hd)
        # her plan içinde hafif sürüklenme (statik durmasın)
        if i + 1 < len(plan):
            f2 = F(plan[i + 1][0]) - 6
            if f2 > f + 6:
                key(cam, "location", f2, nokta(aci + 8, uz * 0.94, yk))
                key(hedef, "location", f2, hd)
    return cam


def deprem_sarsinti(f0):
    cam = bpy.context.scene.camera
    for fc in cam.animation_data.action.fcurves if hasattr(cam.animation_data.action, "fcurves") else []:
        pass
    # Basit sarsıntı: kamera rotasyonuna gürültü modifiye eklemek yerine birkaç anahtar
    random.seed(3)
    for i in range(0, 30, 2):
        cam.delta_rotation_euler = (random.uniform(-0.02, 0.02), random.uniform(-0.02, 0.02), random.uniform(-0.03, 0.03)) if i < 28 else (0, 0, 0)
        cam.keyframe_insert("delta_rotation_euler", frame=f0 + i)
    cam.delta_rotation_euler = (0, 0, 0)
    cam.keyframe_insert("delta_rotation_euler", frame=f0 - 1)
    cam.keyframe_insert("delta_rotation_euler", frame=f0 + 30)


# ---------------------------------------------------------------- render

def setup_render(kalite, cikti):
    scn = bpy.context.scene
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.cycles.samples = 24 if kalite == "final" else 10
    scn.cycles.use_denoising = True
    scn.cycles.max_bounces = 4
    scn.render.fps = FPS
    scn.frame_start = 1
    scn.frame_end = SON_KARE
    olcek = 1.0 if kalite == "final" else 0.5
    scn.render.resolution_x = int(1080 * olcek)
    scn.render.resolution_y = int(1920 * olcek)
    scn.render.resolution_percentage = 100
    scn.render.image_settings.file_format = "PNG"
    scn.view_settings.view_transform = "AgX"
    scn.view_settings.exposure = -0.9
    try:
        scn.view_settings.look = "AgX - Punchy"
    except Exception:
        pass
    scn.render.filepath = os.path.join(cikti, "")


def kareler(s):
    out = []
    for p in s.split(","):
        if "-" in p:
            a, b = p.split("-")
            out += range(int(a), int(b) + 1)
        else:
            out.append(int(p))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cikti", required=True)
    ap.add_argument("--kalite", default="onizleme")
    ap.add_argument("--kare", default=None)
    ap.add_argument("--kaydet", default=None, help=".blend olarak kaydet")
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    reset()
    build()
    setup_render(a.kalite, a.cikti)
    os.makedirs(a.cikti, exist_ok=True)
    if a.kaydet:
        bpy.ops.wm.save_as_mainfile(filepath=a.kaydet)
    scn = bpy.context.scene
    for f in kareler(a.kare) if a.kare else range(1, SON_KARE + 1):
        yol = os.path.join(a.cikti, f"{f:05d}.png")
        if os.path.exists(yol):
            continue
        scn.frame_set(f)
        scn.render.filepath = yol
        bpy.ops.render.render(write_still=True)
        print("Saved", yol, flush=True)
