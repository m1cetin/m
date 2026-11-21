"""Gaziantep Kalesi – anlatıcı seslendirmesi (ElevenLabs).
Her cümleyi ayrı MP3 olarak seslendirme/ klasörüne yazar. Kullanım: python seslendirme.py [--yeniden]
"""
import json, os, sys, urllib.request

SES = "dVlqdPSbCzy23eQaIjPB"   # "Anlatıcı – Gaziantep Kalesi" (tasarlanmış ses C)
MODEL = "eleven_multilingual_v2"  # v3'e göre daha kararlı, takılma az
AYAR = {"stability": 0.6, "similarity_boost": 0.8, "style": 0.15, "speed": 1.03}
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

def uret(i, metin):
    yol = os.path.join(KLASOR, f"{i:02d}.mp3")
    if os.path.exists(yol) and "--yeniden" not in sys.argv:
        return
    onceki = CUMLELER[i - 2] if i > 1 else ""
    sonraki = CUMLELER[i] if i < len(CUMLELER) else ""
    govde = {"text": metin, "model_id": MODEL, "language_code": "tr", "voice_settings": AYAR,
             "previous_text": onceki, "next_text": sonraki}
    r = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{SES}",
        data=json.dumps(govde).encode(),
        headers={"xi-api-key": os.environ.get("ELEVENLABS_API_KEY", "x"), "Content-Type": "application/json"})
    open(yol, "wb").write(urllib.request.urlopen(r).read())
    print("ok", yol)

if __name__ == "__main__":
    os.makedirs(KLASOR, exist_ok=True)
    for i, c in enumerate(CUMLELER, 1):
        uret(i, c)
