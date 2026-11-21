# Gaziantep Kalesi'ni yaptın

"…yaptın" formatında dikey (9:16) YouTube Shorts videosu, yaklaşık 69 saniye.
Bir düzlükteki köyden başlayıp höyüğe, kaleye ve bugünkü şehre kadar her şey adım adım eklenir.

**Bitmiş video:** `cikti/gaziantep_kalesi.mp4`

## Nasıl yapıldı

| Parça | Araç | Dosyalar |
|---|---|---|
| Seslendirme | ElevenLabs, "Orcun Togan" sesi, tek seferde ve kelime zamanlı | `seslendirme.py`, `seslendirme_tam.mp3`, `zamanlama.json` |
| Görseller (13 aşama) | ElevenLabs Flows, GPT Image 2.5. Son hâl üretildi, önceki aşamalar ondan geriye doğru türetildi | `ai_gorseller/S00…S11.png` |
| Dönüşüm videoları | ElevenLabs Flows, Kling 2.5 Turbo (başlangıç ve bitiş karesi) | `ai_videolar/V_xx_yy.mp4` |
| Ekran yazıları | Kelime kelime ve başlık kartları, Montserrat ExtraBold (OFL lisanslı, ücretsiz) | `yazilar.py`, `font/` |
| Efektler ve müzik | numpy ile sentezlendi, telif yok | `efekt_uret.py`, `muzik_uret.py`, `efektler/` |
| Kurgu | ffmpeg | `birlestir.py` |

ElevenLabs flow'u: "Gaziantep Kalesi – Yaptın". Bütün görsel ve video düğümleri orada duruyor.

## Yeniden üretmek

```bash
python3 seslendirme.py      # metin değişirse (cumle_zamanlari.json'u da güncelleyin)
python3 birlestir.py        # görseller + videolar + yazılar + ses → cikti/gaziantep_kalesi.mp4
```

## Bilgi kontrolü

- Kale bir höyük üzerinde kurulu. Höyük M.Ö. 3600'lere tarihleniyor.
- Bizans İmparatoru I. Justinianus (527–565) 12 burç, sur ve hendek yaptırdı.
- Antep savunması 1920–21 yıllarında yaklaşık 10,5 ay sürdü. "Gazi" unvanı 8 Şubat 1921'de verildi.
- 6 Şubat 2023 depremlerinde kalenin burçları ağır hasar gördü.

`sahne.py` ve `sehir.py` ilk Blender denemesi. Final videoda kullanılmadı.
