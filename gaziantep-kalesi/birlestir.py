"""Gaziantep Kalesi – son kurgu.

Yapay zekâ görselleri (ai_gorseller/Sxx.png) ve dönüşüm videoları (ai_videolar/V_*.mp4) seslendirmeye
göre sıralanır: her cümlede "Sen de ..." kısmında bir dönüşüm videosu oynar, aralarda görsel sabit durur.
Üstüne kelime kelime yazılar (yazilar.ass), altına seslendirme + efektler eklenir.

Kullanım: python birlestir.py  →  cikti/gaziantep_kalesi.mp4
"""
import json
import os
import re
import subprocess

KOK = os.path.dirname(os.path.abspath(__file__))
G = os.path.join(KOK, "ai_gorseller")
V = os.path.join(KOK, "ai_videolar")
EF = os.path.join(KOK, "efektler")
ARA = os.path.join(KOK, "ara")
CIKTI = os.path.join(KOK, "cikti")
os.makedirs(ARA, exist_ok=True)
os.makedirs(CIKTI, exist_ok=True)
FPS = 30
W, H = 1080, 1920

Z = json.load(open(os.path.join(KOK, "cumle_zamanlari.json")))
T = [c["bas"] for c in Z]
SON = Z[-1]["son"] + 2.4

# --- kelime zamanları
a = json.load(open(os.path.join(KOK, "zamanlama.json")))
metin = "".join(a["characters"])
KEL = []
for m in re.finditer(r"<[^>]*>|[^\s<]+", metin):
    if not m.group().startswith("<"):
        KEL.append((re.sub(r"[.,:;!?…]+$", "", m.group()).lower(), a["character_start_times_seconds"][m.start()],
                    a["character_end_times_seconds"][m.end() - 1]))


def kelime(aranan, sonra=0.0, son=False):
    for w, s, e in KEL:
        if s >= sonra - 0.01 and w.startswith(aranan.lower()):
            return e if son else s
    raise ValueError(aranan)


def sende(i):
    """i. cümledeki 'Sen de' başlangıcı."""
    return kelime("sen", T[i])


# --- zaman çizelgesi: (başlangıç, bitiş, tür, kaynak, ek)
#   tür: "gorsel" (sabit kare) | "video" (süreye sığdırılır) | "ters" (videoyu tersten oynat)
P = []


def gorsel(s, e, ad):
    if e - s > 0.04:
        P.append((s, e, "gorsel", ad, None))


def video(s, e, ad, tersten=False, kirp=None):
    P.append((s, e, "ters" if tersten else "video", ad, kirp))


k1 = sende(1) + 1.2
gorsel(0, k1, "S00")
video(k1, T[2] - 0.2, "V_00_01")                    # höyük büyür
k = sende(2); gorsel(T[2] - 0.2, k, "S01")
video(k, T[3] - 0.15, "V_01_02")                    # gözetleme kulesi
k = sende(3); gorsel(T[3] - 0.15, k, "S02")
video(k, T[4] - 0.15, "V_02_03")                    # surlar
k = sende(4); gorsel(T[4] - 0.15, k, "S03")
video(k, T[5] - 0.15, "V_03_04")                    # hendek
k = sende(5); gorsel(T[5] - 0.15, k, "S04")
video(k, T[6] - 0.1, "V_04_05")                     # sarnıç
video(T[6] - 0.1, T[7] - 0.1, "V_05_06")            # Bizans–Selçuklu–Memlük
video(T[7] - 0.1, T[8], "V_06_07")                  # kasaba + 1920 kuşatması
video(T[8], T[9] - 0.05, "V_07_08")                 # duman dağılır, bayrak
m = T[9] + 2.0
video(T[9] - 0.05, m, "V_08_10")                    # modern şehir (hızlı)
video(m, T[10] - 0.1, "V_10_09")                    # deprem
video(T[10] - 0.1, T[11] - 0.1, "V_10_09", tersten=True)  # taşlar yerine
k = T[11] + 0.6; gorsel(T[11] - 0.1, k, "S10")
video(k, T[12] + 0.3, "V_10_11")                    # gün batımı, çarşı, baklava
gorsel(T[12] + 0.3, SON, "S11")


def calistir(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-1500:])
        raise SystemExit(1)


def sure(yol):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", yol]).strip())


parcalar = []
for n, (s, e, tur, ad, ek) in enumerate(P):
    d = e - s
    out = os.path.join(ARA, f"{n:02d}_{ad}{'_ters' if tur == 'ters' else ''}.mp4")
    ortak = f"scale={W}:{H}:flags=lanczos,setsar=1,fps={FPS},format=yuv420p"
    if tur == "gorsel":
        calistir(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-t", f"{d:.3f}", "-i", os.path.join(G, ad + ".png"),
                  "-vf", ortak, "-c:v", "libx264", "-crf", "17", "-preset", "fast", out])
    else:
        src = os.path.join(V, ad + ".mp4")
        L = sure(src) - 0.05
        oran = d / L
        vf = ("reverse," if tur == "ters" else "") + f"setpts={oran:.5f}*PTS," + ortak
        if oran > 1.15:  # yavaşlatılan videolarda kareleri yumuşat
            vf += f",minterpolate=fps={FPS}:mi_mode=blend"
        calistir(["ffmpeg", "-v", "error", "-y", "-i", src, "-an", "-vf", vf, "-t", f"{d:.3f}",
                  "-c:v", "libx264", "-crf", "17", "-preset", "fast", out])
    parcalar.append(out)
    print(f"{s:6.2f}-{e:6.2f}  {tur:6s} {ad}")

liste = os.path.join(ARA, "liste.txt")
open(liste, "w").write("".join(f"file '{p}'\n" for p in parcalar))
goruntu = os.path.join(ARA, "goruntu.mp4")
calistir(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", liste, "-c", "copy", goruntu])

# --- ses: seslendirme + efektler
efekt = []  # (saniye, dosya, ses seviyesi)
for i in (2, 3, 4):
    efekt.append((T[i + 1] - 0.5, "ping", 0.55))
efekt += [(sende(1) + 1.4, "whoosh", 0.5), (T[2] - 0.5, "ping", 0.55)]
efekt += [(sende(5) + 1.0, "su", 0.7), (T[6] - 0.4, "ping", 0.55)]
efekt += [(kelime("bizans", T[6]) + 0.3, "pop", 0.8), (kelime("selçuklu", T[6]) + 0.3, "pop", 0.8),
          (kelime("memlük", T[6]) + 0.3, "pop", 0.8)]
efekt += [(T[7] + 0.9, "top", 0.8), (T[7] + 2.0, "top", 0.6), (T[7] + 3.1, "top", 0.7)]
efekt += [(kelime("gazi", T[8]), "ping", 0.7)]
efekt += [(T[9] - 0.05, "whoosh", 0.5), (m + 0.1, "deprem", 0.95)]
efekt += [(T[10] + 0.8 + 0.45 * j, "tas", 0.6) for j in range(6)] + [(T[11] - 0.5, "ping", 0.55)]
efekt += [(kelime("baklava", T[11]), "catal", 0.6)]
efekt += [(kelime("tebrikler", T[12]), "ping", 0.7), (kelime("yaptın", T[12], son=True) + 0.15, "davul", 0.9)]

girdi = ["-i", os.path.join(KOK, "seslendirme_tam.mp3")]
filtre = ["[0:a]aformat=sample_rates=44100:channel_layouts=stereo,volume=1.0[a0]"]
for j, (t, ad, v) in enumerate(efekt):
    girdi += ["-i", os.path.join(EF, ad + ".wav")]
    ms = int(max(0, t) * 1000)
    filtre.append(f"[{j + 1}:a]volume={v},adelay={ms}|{ms}[e{j}]")
girdi += ["-i", os.path.join(EF, "muzik.wav")]
filtre.append(f"[{len(efekt) + 1}:a]volume=0.10,afade=t=out:st={SON - 2.5:.2f}:d=2.4[muz]")
filtre.append("".join(f"[e{j}]" for j in range(len(efekt))) + f"[muz][a0]amix=inputs={len(efekt) + 2}:normalize=0,"
              f"alimiter=limit=0.95,apad,atrim=0:{SON:.3f}[aout]")
ses = os.path.join(ARA, "ses.m4a")
calistir(["ffmpeg", "-v", "error", "-y", *girdi, "-filter_complex", ";".join(filtre), "-map", "[aout]",
          "-c:a", "aac", "-b:a", "192k", ses])

# --- yazılar + birleştirme
subprocess.run(["python3", os.path.join(KOK, "yazilar.py")], check=True, capture_output=True)
son = os.path.join(CIKTI, "gaziantep_kalesi.mp4")
ass = os.path.join(KOK, "yazilar.ass").replace(":", "\\:")
calistir(["ffmpeg", "-v", "error", "-y", "-i", goruntu, "-i", ses,
          "-vf", f"scale=w='trunc({W}*(1+0.07*t/{SON:.2f})/2)*2':h='trunc({H}*(1+0.07*t/{SON:.2f})/2)*2'"
                 f":eval=frame:flags=bicubic,crop={W}:{H},"  # tüm videoya yavaş, sürekli yakınlaşma
                 f"ass={ass}:fontsdir={os.path.join(KOK, 'font')}",
          "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "19", "-preset", "medium",
          "-maxrate", "12M", "-bufsize", "24M", "-c:a", "copy", "-movflags", "+faststart", "-shortest", son])
print("BİTTİ", son, f"{sure(son):.1f} sn")
