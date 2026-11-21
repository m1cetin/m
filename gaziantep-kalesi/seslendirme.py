"""Gaziantep Kalesi – anlatıcı seslendirmesi (ElevenLabs).
Her cümleyi ayrı MP3 olarak seslendirme/ klasörüne yazar. Kullanım: python seslendirme.py [--yeniden]
"""
import json, os, sys, urllib.request

SES = "c9eIhSvMHBxtYhLX4oBt"   # Orcun Togan (ElevenLabs kütüphanesi; örnek videodaki sese en yakın eşleşme)
MODEL = "eleven_multilingual_v2"  # v3'e göre daha kararlı, takılma az
AYAR = {"stability": 0.5, "similarity_boost": 0.8, "style": 0.0, "speed": 1.0}
KLASOR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seslendirme")

CUMLELER = [
    "Eğer bu düzlüğe bir köy kurarsan, düşmana açık olursun.",
    "Sen de evini eski evin üstüne yaparsın. Beş bin yıl boyunca her köy bir öncekinin üstüne kurulur. Düzlükte kendine bir tepe yapmış olursun.",
    "Ama tepeyi düşman da görür. Sen de tepeye taştan bir gözetleme kulesi dikersin.",
    "Ama kule yetmez. Sen de etrafına kalın surlar örersin.",
    "Ama düşman surların dibine kadar gelir. Sen de tepenin çevresine derin bir hendek kazarsın.",
    "Ama kuşatma aylarca sürer, su biter. Sen de kayanın içine sarnıçlar oyarsın.",
    "Bizans gelir, surlara on iki burç diker. Selçuklu gelir, onarır. Memlük gelir, yeniden güçlendirir.",
    "Bin dokuz yüz yirmi. Şehir kuşatılır. Halk açlığa rağmen on ay direnir.",
    "Sen de şehrin adının önüne bir unvan eklersin: Gazi.",
    "Ama iki bin yirmi üçte, bir kış sabahı yer sallanır. Burçlar yamaçtan aşağı yuvarlanır.",
    "Sen de düşen taşları tek tek numaralar, aynı yerlerine geri örersin.",
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
