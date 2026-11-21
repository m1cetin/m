"""Kalenin etrafında zamanla büyüyen canlı şehir: dönem dönem evler, ağaçlar, yollar, yürüyen insanlar."""
import math
import random

import bpy

import sahne as S


def renkler():
    M = {}
    for ad, c in {
        "kerpic": (0.72, 0.50, 0.30), "tas_ev": (0.92, 0.84, 0.66), "tas_ev2": (0.86, 0.74, 0.55),
        "kiremit": (0.80, 0.25, 0.10), "kiremit2": (0.66, 0.18, 0.08), "ahsap_kapi": (0.35, 0.18, 0.08),
        "pencere": (0.10, 0.18, 0.28), "apt1": (0.96, 0.92, 0.84), "apt2": (0.95, 0.76, 0.62),
        "apt3": (0.70, 0.84, 0.92), "apt4": (0.98, 0.88, 0.55), "yaprak": (0.18, 0.55, 0.12),
        "yaprak2": (0.32, 0.62, 0.10), "govde": (0.30, 0.18, 0.08), "yol": (0.80, 0.72, 0.58),
        "cati_gri": (0.45, 0.45, 0.48), "kisi1": (0.85, 0.20, 0.15), "kisi2": (0.15, 0.35, 0.75),
        "kisi3": (0.95, 0.75, 0.15), "kisi4": (0.20, 0.60, 0.35),
    }.items():
        M[ad] = S.noisy(S.mat(ad, c, 0.7), 14, 0.9, 0.15) if ad not in ("pencere",) else S.mat(ad, c, 0.15)
    return M


def piramit_cati(ad, x, y, z, w, d, h, m, rot):
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=1, radius2=0, depth=h, location=(x, y, z + h / 2),
                                    rotation=(0, 0, rot + math.pi / 4))
    o = bpy.context.object
    o.name = ad
    o.scale = (w * 0.75, d * 0.75, 1)
    S.assign(o, m)
    return o


def ev(C, M, ad, x, y, donem, rnd):
    """donem: 0 kerpiç köy evi, 1 taş ev (düz dam), 2 kiremit çatılı taş ev, 3 apartman."""
    g = S.empty(ad, (x, y, 0))
    rot = rnd.choice([0, math.pi / 2]) + rnd.uniform(-0.15, 0.15)
    parcalar = []
    if donem == 0:
        w, d, h = rnd.uniform(0.45, 0.6), rnd.uniform(0.4, 0.55), 0.35
        parcalar.append(S.box(ad + "_g", (x, y, h / 2), (w, d, h), C["kerpic"], bev=0.03, rot=(0, 0, rot)))
    elif donem in (1, 2):
        w, d, h = rnd.uniform(0.55, 0.8), rnd.uniform(0.5, 0.7), rnd.uniform(0.45, 0.65)
        m = C[rnd.choice(["tas_ev", "tas_ev2"])]
        parcalar.append(S.box(ad + "_g", (x, y, h / 2), (w, d, h), m, bev=0.02, rot=(0, 0, rot)))
        if donem == 2:
            parcalar.append(piramit_cati(ad + "_c", x, y, h, w * 1.1, d * 1.1, 0.28,
                                         C[rnd.choice(["kiremit", "kiremit2"])], rot))
        else:
            parcalar.append(S.box(ad + "_k", (x, y, h + 0.03), (w * 1.04, d * 1.04, 0.06), C["tas_ev2"], bev=0.01,
                                  rot=(0, 0, rot)))
    else:
        kat = rnd.randint(3, 6)
        w, d, h = rnd.uniform(0.7, 0.95), rnd.uniform(0.6, 0.8), 0.28 * kat
        m = C[rnd.choice(["apt1", "apt2", "apt3", "apt4"])]
        parcalar.append(S.box(ad + "_g", (x, y, h / 2), (w, d, h), m, bev=0.02, rot=(0, 0, rot)))
        parcalar.append(S.box(ad + "_k", (x, y, h + 0.04), (w * 1.02, d * 1.02, 0.08), C["cati_gri"], bev=0.01,
                              rot=(0, 0, rot)))
    # pencereler / kapı: kameraya bakan iki yüze
    ca, sa = math.cos(rot), math.sin(rot)
    if donem >= 1:
        satir = [h * 0.55] if donem < 3 else [0.16 + 0.28 * k for k in range(int(h / 0.28))]
        for zz in satir:
            for u in (-0.22, 0.22):
                px, py = x + ca * u * w - sa * (-d / 2 - 0.005), y + sa * u * w + ca * (-d / 2 - 0.005)
                parcalar.append(S.box(ad + "_p", (px, py, zz), (w * 0.16, 0.02, 0.11), C["pencere"], bev=0.0,
                                      rot=(0, 0, rot)))
    kx, ky = x - sa * (-d / 2 - 0.005), y + ca * (-d / 2 - 0.005)
    parcalar.append(S.box(ad + "_kapi", (kx, ky, 0.1), (0.12, 0.02, 0.2), C["ahsap_kapi"], bev=0.0, rot=(0, 0, rot)))
    for p in parcalar:
        S.parent(p, g)
    return g


def agac(C, ad, x, y, rnd):
    g = S.empty(ad, (x, y, 0))
    s = rnd.uniform(0.8, 1.2)
    t = S.cyl(ad + "_g", (x, y, 0.15 * s), 0.04 * s, 0.3 * s, C["govde"], verts=8, bev=0.0)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.22 * s, location=(x, y, 0.42 * s))
    y_ = bpy.context.object
    y_.scale.z = 0.85
    S.assign(y_, C[rnd.choice(["yaprak", "yaprak2"])])
    bpy.ops.object.shade_smooth()
    for p in (t, y_):
        S.parent(p, g)
    return g


def yuruyen(C, M, ad, p1, p2, f0, f1, rnd):
    k = S.kisi(M, (p1[0], p1[1], 0.0), C[rnd.choice(["kisi1", "kisi2", "kisi3", "kisi4"])],
               rot=math.atan2(p2[1] - p1[1], p2[0] - p1[0]) + math.pi / 2)
    k.scale = (0.6, 0.6, 0.6)
    S.pop(k, f0, dur=6, final=(0.6, 0.6, 0.6))
    S.key(k, "location", f0, (p1[0], p1[1], 0.0), "LINEAR")
    S.key(k, "location", f1, (p2[0], p2[1], 0.0), "LINEAR")
    return k


def bos_mu(x, y, R_TEPE, BLOK):
    r = math.hypot(x, y)
    if r < R_TEPE + 1.25:                     # tepe + hendek
        return False
    if abs(x) > BLOK / 2 - 0.5 or abs(y) > BLOK / 2 - 0.5:
        return False
    if y < -3.6 and abs(x) < 3.9:             # çarşı + kapı yolu
        return False
    if abs(x - 4.3) < 1.0 and abs(y + 2.0) < 0.9:  # manzara masası
        return False
    if abs(x) < 0.5 and y < 0:                # köprüden inen ana yol
        return False
    return True


def kur(M, T, F, R_TEPE, BLOK):
    C = renkler()
    rnd = random.Random(42)
    # Yollar: kale kapısından aşağı ana yol + çevre yolu
    S.box("anayol", (0, -(R_TEPE + 1.25 + BLOK / 2) / 2 - 0.3, 0.005), (0.7, BLOK / 2 - R_TEPE - 0.6, 0.02),
          C["yol"], bev=0.0)
    bpy.ops.mesh.primitive_torus_add(major_radius=R_TEPE + 1.45, minor_radius=0.28, major_segments=96,
                                     minor_segments=8, location=(0, 0, -0.02))
    cevre = bpy.context.object
    cevre.scale.z = 0.12
    S.assign(cevre, C["yol"])
    S.pop(cevre, F(T[6] + 0.2), dur=10)

    # Ev yerleri: halka halka, dışa doğru
    yerler = []
    for r in [R_TEPE + 1.9 + k * 0.78 for k in range(7)]:
        n = int(2 * math.pi * r / 0.85)
        for i in range(n):
            a = 2 * math.pi * (i + rnd.uniform(-0.2, 0.2)) / n
            x, y = math.cos(a) * r, math.sin(a) * r
            if bos_mu(x, y, R_TEPE, BLOK):
                yerler.append((r, x, y))
    yerler.sort(key=lambda t: t[0] + rnd.uniform(-0.6, 0.6))

    # Dönemler: (başlangıç sn, süre sn, ev sayısı, dönem tipi)
    plan = [
        (T[1] + 1.5, 5.0, 18, 0),   # höyük çevresinde ilk kerpiç evler
        (T[6] + 0.5, 5.0, 30, 1),   # Bizans–Selçuklu–Memlük: taş evler
        (T[7] + 0.3, 3.5, 40, 2),   # 1920: kiremit çatılı Antep evleri
        (T[10] + 0.5, 3.5, 30, 3),  # günümüz: apartmanlar
    ]
    evler = []
    yi = 0
    for bas, sure, n, donem in plan:
        for k in range(n):
            if yi >= len(yerler):
                break
            _, x, y = yerler[yi]
            yi += 1
            e = ev(C, M, f"ev_{donem}_{k}", x, y, donem, rnd)
            S.pop(e, F(bas + sure * k / n), dur=7)
            evler.append(e)

    # Ağaçlar (fıstık bahçeleri) boş kalan yerlere
    for k in range(90):
        for _ in range(30):
            x, y = rnd.uniform(-BLOK / 2 + 0.5, BLOK / 2 - 0.5), rnd.uniform(-BLOK / 2 + 0.5, BLOK / 2 - 0.5)
            if bos_mu(x, y, R_TEPE, BLOK) and all(math.hypot(x - e.location.x, y - e.location.y) > 0.45 for e in evler):
                a = agac(C, f"agac_{k}", x, y, rnd)
                S.pop(a, F(T[1] + 2.0 + (k / 90) * 12), dur=8)
                break

    # Yürüyen insanlar: çarşı ve ana yolda (son bölüm)
    for k in range(10):
        x0 = rnd.uniform(-3.4, 3.4)
        y0 = rnd.uniform(-5.4, -3.9)
        yuruyen(C, M, f"yaya_{k}", (x0, y0), (x0 + rnd.choice([-1.5, 1.5]), y0 + rnd.uniform(-0.3, 0.3)),
                F(T[11] + 0.2 + k * 0.15), F(T[12] + 3.0), rnd)
    for k in range(6):
        y0 = -BLOK / 2 + 0.6 + k * 0.5
        yuruyen(C, M, f"yolcu_{k}", (rnd.uniform(-0.2, 0.2), y0), (rnd.uniform(-0.2, 0.2), y0 + 1.8),
                F(T[10] + 1.0 + k * 0.3), F(T[12] + 3.0), rnd)
    return evler
