"""Gaziantep Kalesi – anlatıcı seslendirmesi (ElevenLabs).
Her cümleyi ayrı MP3 olarak seslendirme/ klasörüne yazar. Kullanım: python seslendirme.py [--yeniden]
"""
import json, os, sys, urllib.request

SES = "i4Vkimmf9IrZ2RdG16Rv"   # Ayaz – Warm, Calm & Expressive (ElevenLabs kütüphanesi, Starter plan)
MODEL = "eleven_multilingual_v2"  # v3'e göre daha kararlı, takılma az
AYAR = {"stability": 0.5, "similarity_boost": 0.8, "style": 0.0, "speed": 1.0}
KLASOR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seslendirme")

CUMLELER = [
    "Eğer bu düzlükte bir tepeye çıkarsan, her yönü görürsün.",
    "Ama düşman da seni görür. Sen de tepenin üstüne taştan bir gözetleme kulesi dikersin.",
    "Ama kule yetmez, düşman tepeye tırmanır. Sen de etrafına kalın surlar örersin.",
    "Ama surların dibine kadar gelirler. Sen de tepenin çevresine derin bir hendek kazarsın.",
    "Ama kuşatma aylarca sürer, su biter. Sen de kayanın içine sarnıçlar oyarsın.",
    "Yüzyıllar geçer. Bizans, Selçuklu, Memlük... Her gelen bir kule ekler.",
    "Bin dokuz yüz yirmi. Şehir kuşatılır. Halk on ay boyunca direnir.",
    "Sen de şehrin adının önüne bir unvan eklersin: Gazi.",
    "Ama bir kış gecesi yer sallanır. Burçlar yamaçtan aşağı yıkılır.",
    "Sen de taşları tek tek numaralar, yeniden örersin.",
    "Son olarak kalenin dibine bir bakırcı çarşısı, havaya fıstık kokusu ve tam manzarayı izlerken tabağına konan bir dilim baklava eklersin.",
    "Tebrikler, Gaziantep Kalesi'ni yaptın.",
]

def tek_parca():
    """Tüm metni tek seferde üretir: ton baştan sona aynı kalır, geçişler doğal olur.
    Kelime zamanlamaları zamanlama.json'a yazılır (yazılar ve sahne geçişleri için)."""
    import base64
    metin = ' <break time="0.6s" /> '.join(CUMLELER)
    govde = {"text": metin, "model_id": MODEL, "language_code": "tr", "voice_settings": AYAR}
    r = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{SES}/with-timestamps",
        data=json.dumps(govde).encode(),
        headers={"xi-api-key": os.environ.get("ELEVENLABS_API_KEY", "x"), "Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(r))
    kok = os.path.dirname(KLASOR)
    open(os.path.join(kok, "seslendirme_tam.mp3"), "wb").write(base64.b64decode(d["audio_base64"]))
    json.dump(d["alignment"], open(os.path.join(kok, "zamanlama.json"), "w"), ensure_ascii=False)
    print("ok")

if __name__ == "__main__":
    tek_parca()
