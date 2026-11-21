"""Ekran yazıları: seslendirmeyle eş zamanlı tek kelimeler + başlık kartları (ASS altyazı dosyası).

Kelime zamanları zamanlama.json'dan (ElevenLabs karakter zamanlaması) gelir.
Çıktı: yazilar.ass  →  birlestir.sh içinde ffmpeg 'ass' filtresiyle videoya basılır.
"""
import json
import os
import re

KOK = os.path.dirname(os.path.abspath(__file__))
a = json.load(open(os.path.join(KOK, "zamanlama.json")))
ch, st, en = a["characters"], a["character_start_times_seconds"], a["character_end_times_seconds"]
Z = json.load(open(os.path.join(KOK, "cumle_zamanlari.json")))
T = [c["bas"] for c in Z]

# --- kelimeleri çıkar (break etiketlerini atla)
metin = "".join(ch)
kelimeler = []
for m in re.finditer(r"<[^>]*>|[^\s<]+", metin):
    if m.group().startswith("<"):
        continue
    w = m.group().strip(".,:;!?…\"'")
    w = re.sub(r"[.,:;!?…]+$", "", m.group())
    i, j = m.start(), m.end() - 1
    kelimeler.append([w, st[i], en[j]])


def buyuk_ilk(w):
    tr = {"i": "İ", "ı": "I"}
    return (tr.get(w[0], w[0].upper()) + w[1:]) if w else w


def buyuk(w):
    return w.replace("i", "İ").replace("ı", "I").upper()


# Sayıları rakamla göster: "Bin dokuz yüz yirmi" → 1920, "iki bin yirmi üçte" → 2023'te
birlesik = []
i = 0
while i < len(kelimeler):
    s = " ".join(k[0].lower() for k in kelimeler[i:i + 4])
    if s.startswith("bin dokuz yüz yirmi"):
        birlesik.append(["1920", kelimeler[i][1], kelimeler[i + 3][2]]); i += 4; continue
    if s.startswith("iki bin yirmi üçte"):
        birlesik.append(["2023'te", kelimeler[i][1], kelimeler[i + 3][2]]); i += 4; continue
    if s.startswith("on iki burç"):
        birlesik.append(["12", kelimeler[i][1], kelimeler[i + 1][2]]); i += 2; continue
    if s.startswith("beş bin yıl"):
        birlesik.append(["5000", kelimeler[i][1], kelimeler[i + 1][2]]); i += 2; continue
    birlesik.append(kelimeler[i]); i += 1


def zaman(t):
    t = max(0, t)
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def kelime_zamani(aranan, sonra=0.0):
    for w, s, e in birlesik:
        if s >= sonra and w.lower().startswith(aranan.lower()):
            return s
    raise ValueError(aranan)


bas = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Kelime,Montserrat ExtraBold,96,&H00FFFFFF,&H00FFFFFF,&H00101010,&H90000000,-1,0,0,0,100,100,0,0,1,7,4,5,40,40,0,1
Style: Baslik,Montserrat ExtraBold,150,&H0030C8FF,&H0030C8FF,&H00102040,&HA0000000,-1,0,0,0,100,100,2,0,1,9,6,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
olaylar = []
BASLIK_KELIMELERI = {"1920", "2023'TE", "GAZİ", "BİZANS", "SELÇUKLU", "MEMLÜK"}
# Tek kelimeler: ekranın ortasının biraz altında, her kelime "pop" diye gelir
for k, (w, s, e) in enumerate(birlesik):
    son = birlesik[k + 1][1] if k + 1 < len(birlesik) else e + 0.6
    son = min(son, e + 0.5)
    yazi = buyuk_ilk(w)
    if buyuk(w) in BASLIK_KELIMELERI:
        continue  # aynı anda başlık kartında zaten büyük yazıyor
    olaylar.append(f"Dialogue: 1,{zaman(s)},{zaman(son)},Kelime,,0,0,0,,"
                   r"{\pos(540,1250)\fscx70\fscy70\t(0,90,\fscx108\fscy108)\t(90,150,\fscx100\fscy100)}" + yazi)

# Başlık kartları: üst bölgede, büyük turuncu-altın
basliklar = [
    ("HÖYÜK", kelime_zamani("tepe", T[1]), T[2] - 0.2),
    ("BİZANS", kelime_zamani("Bizans", T[6]), kelime_zamani("Selçuklu", T[6]) - 0.05),
    ("SELÇUKLU", kelime_zamani("Selçuklu", T[6]), kelime_zamani("Memlük", T[6]) - 0.05),
    ("MEMLÜK", kelime_zamani("Memlük", T[6]), T[7] - 0.2),
    ("1920", T[7], T[8] - 0.2),
    ("GAZİ", kelime_zamani("Gazi", T[8]), T[9] - 0.2),
    ("2023", T[9], T[10] - 0.2),
    ("GAZİANTEP\\NKALESİ", T[12], Z[-1]["son"] + 2.2),
]
for yazi, s, e in basliklar:
    olaylar.append(f"Dialogue: 2,{zaman(s)},{zaman(e)},Baslik,,0,0,0,,"
                   r"{\pos(540,250)\fscx40\fscy40\t(0,120,\fscx112\fscy112)\t(120,220,\fscx100\fscy100)\fad(0,200)}" + yazi)

open(os.path.join(KOK, "yazilar.ass"), "w").write(bas + "\n".join(olaylar) + "\n")
print(len(birlesik), "kelime,", len(basliklar), "başlık")
print(" ".join(w for w, _, _ in birlesik))
