"""GECE NÖBETİ – Bölüm 1 ekran yazıları.

Her yazıyı 1080x1920 şeffaf PNG olarak üretir ve zamanlamasını
yazilar.txt dosyasına yazar (birlestir.sh okur).
Kullanım:  python yazilar.py <cikti_klasoru>
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
FONT_DIR = "/usr/share/fonts/opentype/inter"
BLACK = os.path.join(FONT_DIR, "InterDisplay-Black.otf")
BOLD = os.path.join(FONT_DIR, "Inter-Bold.otf")
AMBER = (255, 176, 32)
WHITE = (255, 255, 255)
GREY = (170, 170, 170)

# (dosya, başlangıç sn, bitiş sn, satırlar[(metin, font, boyut, renk, harf_aralığı)], dikey merkez)
YAZILAR = [
    ("01_baslik", 0.4, 4.7, [
        ("GECE NÖBETİ", BLACK, 120, WHITE, 6),
        ("BÖLÜM 1 · İLK GECE", BOLD, 40, AMBER, 10),
    ], 0.30),
    ("02_not", 5.5, 8.0, [
        ("Eski bekçi tek bir not bırakmıştı:", BOLD, 46, WHITE, 0),
    ], 0.70),
    ("03_kural", 7.9, 11.0, [
        ("SAAT 03:00'TE", BLACK, 64, WHITE, 2),
        ("HEYKELLERE", BLACK, 104, AMBER, 2),
        ("BAKMA.", BLACK, 104, AMBER, 2),
    ], 0.70),
    ("04_bakti", 16.2, 21.4, [
        ("AMA KEMAL", BLACK, 64, WHITE, 2),
        ("BAKTI.", BLACK, 120, AMBER, 4),
    ], 0.72),
    ("05_o_da", 28.3, 33.2, [
        ("O DA", BLACK, 64, WHITE, 2),
        ("SANA BAKIYORDU.", BLACK, 92, AMBER, 2),
    ], 0.74),
    ("06_son", 34.4, 40.5, [
        ("KEMAL ŞİMDİ", BLACK, 64, WHITE, 2),
        ("NE YAPMALI?", BLACK, 104, AMBER, 2),
        ("", BOLD, 30, GREY, 0),
        ("A) Işığı söndürsün", BOLD, 54, WHITE, 0),
        ("B) Koşarak kaçsın", BOLD, 54, WHITE, 0),
        ("C) Heykele yaklaşsın", BOLD, 54, WHITE, 0),
        ("", BOLD, 30, GREY, 0),
        ("Yorumlara yaz,", BOLD, 46, AMBER, 0),
        ("2. bölümü SEN seç!", BLACK, 64, AMBER, 2),
    ], 0.5),
]


def text_width(draw, text, font, spacing):
    if not text:
        return 0
    w = sum(draw.textlength(ch, font=font) for ch in text)
    return w + spacing * (len(text) - 1)


def draw_line(draw, x, y, text, font, color, spacing):
    for ch in text:
        draw.text((x, y), ch, font=font, fill=color)
        x += draw.textlength(ch, font=font) + spacing


def render(lines, center_y):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    ds = ImageDraw.Draw(shadow)
    fonts = [ImageFont.truetype(f, s) for _, f, s, _, _ in lines]
    heights = [int(s * 1.08) for _, _, s, _, _ in lines]
    total = sum(heights)
    y = int(H * center_y - total / 2)
    for (text, _, size, color, sp), font, h in zip(lines, fonts, heights):
        tw = text_width(d, text, font, sp)
        x = (W - tw) / 2
        draw_line(ds, x, y + 4, text, font, (0, 0, 0, 230), sp)
        draw_line(d, x, y, text, font, color + (255,), sp)
        y += h
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    return Image.alpha_composite(shadow, img)


def main(out):
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "yazilar.txt"), "w") as f:
        for name, a, b, lines, cy in YAZILAR:
            path = os.path.join(out, name + ".png")
            render(lines, cy).save(path)
            f.write(f"{path} {a} {b}\n")
    print("yazılar hazır:", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "yazilar")
