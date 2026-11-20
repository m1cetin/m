# GECE NÖBETİ

Bir şehir müzesine gece bekçisi olarak işe başlayan **Kemal**'in hikâyesi.
Önceki bekçi ortadan kaybolmuş, geride yalnızca kurallar yazılı bir not bırakmış.
Her bölüm bir kuralı ve o kural çiğnendiğinde olanları anlatıyor.

- **Format:** Dikey (9:16), 30–45 saniye, 3D (Blender / Cycles)
- **Ton:** Gerilim + gizem, kan/vahşet yok
- **Karakterler:**
  - **Kemal:** Yeni gece bekçisi. Bıyıklı, endişeli, iyi kalpli. Lacivert üniforma, şapka, el feneri.
  - **Heykeller:** Yüzü olmayan beyaz mermer figürler. Gece bazıları "uyanıyor".
  - **Eski Bekçi (Rıza Usta):** Hiç görünmüyor; sadece notları ve sesi var.

## Bölümler: izleyiciler seçiyor

Her bölüm bir seçimle biter ("Kemal şimdi ne yapmalı? A / B / C"). Yorumlarda en çok
oy alan seçenek bir sonraki bölümün hikâyesi olur. Seriyi izleyiciler birlikte yazar.

| # | Başlık | Durum |
|---|---|---|
| 1 | İlk Gece | Hazır. Seçenekler: A) Işığı söndürsün · B) Koşarak kaçsın · C) Heykele yaklaşsın |
| 2 | ? | 1. bölümün yorumlarındaki oylamaya göre |

Fikir havuzu (ileriki bölümlerde kullanılabilir): telsizden gelen kayıp bekçinin sesi, kapısı hiç açılmayan
kırmızı oda, tozda çıplak ayak izleri, güvenlik kamerasında Kemal'in kendini görmesi, eski bekçinin
defteri, boş kalan kaide.

## Klasörler

- `bolum01/senaryo.md`: Çekim listesi, ekrandaki yazılar, seslendirme metni
- `bolum01/sahne.py`: Blender sahnesini sıfırdan kuran ve render alan script
- `bolum01/ses.py`: Ortam sesi, efektler ve gerilim müziğini üreten script
- `bolum01/yazilar.py`: Ekrandaki yazıları (başlık, kural, son kart) üreten script
- `bolum01/birlestir.sh`: Render kareleri, yazıları ve sesi videoya dönüştürür
- `cikti/`: Bitmiş videolar
