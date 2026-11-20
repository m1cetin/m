"""GECE NÖBETİ – Bölüm 1 seslendirmesi (ElevenLabs).

Her repliği ilgili karakterin sesiyle üretip seslendirme/ klasörüne MP3 olarak kaydeder.
ses.py bu dosyaları zamanlamalarıyla miksajlar.

API anahtarı ELEVENLABS_API_KEY ortam değişkeninden okunur. (Claude Code bulut
oturumunda anahtar ağ proxy'si tarafından eklenir; değişkene herhangi bir değer verilebilir.)
Kullanım:  python seslendirme.py [--yeniden]
"""
import json
import os
import sys
import urllib.request

MODEL = "eleven_v3"
HIZ = 1.12  # konuşma hızı (1.0 = normal)
KLASOR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seslendirme")

# ElevenLabs hazır sesleri
SESLER = {
    "riza": "pqHfZKP75CvOlQylNhV4",       # Bill: yaşlı adam
    "kemal": "iP95p4xoKVk53GoZ742B",      # Chris: Kemal, hikâyeyi de kendisi anlatır
}

# (dosya adı, karakter, başlangıç saniyesi, metin) — başlangıçlar ses.py'de kullanılır
REPLIKLER = [
    ("01_kemal", "kemal", 0.6, "Müzedeki ilk gecemdi. Elime bir fener ve bir not verdiler."),
    ("02_riza", "riza", 5.8, "[whispers] Saat üçte heykellere bakma evlat, ne olursa olsun."),
    ("03_kemal", "kemal", 16.4, "[nervously] Bir kere bakmaktan ne olur ki?"),
    ("04_kemal", "kemal", 28.2, "[scared whisper] Az önce yüzü duvara dönüktü!"),
    ("05_kemal", "kemal", 34.7, "[scared] Şimdi ne yapmalıyım? Yorumlara yaz, sen seç."),
]


def tts(text, voice_id, out):
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=mp3_44100_128",
        data=json.dumps({
            "text": text,
            "model_id": MODEL,
            "language_code": "tr",
            "seed": 1907,  # aynı karakter her replikte aynı tınıda kalsın
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.8, "speed": HIZ},
        }).encode(),
        headers={
            "xi-api-key": os.environ.get("ELEVENLABS_API_KEY", "proxy-injected"),
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as r, open(out, "wb") as f:
        f.write(r.read())


def main():
    yeniden = "--yeniden" in sys.argv
    os.makedirs(KLASOR, exist_ok=True)
    for name, who, _, text in REPLIKLER:
        out = os.path.join(KLASOR, name + ".mp3")
        if os.path.exists(out) and not yeniden:
            continue
        tts(text, SESLER[who], out)
        print("üretildi:", out)


if __name__ == "__main__":
    main()
