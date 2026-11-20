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

## Bölümler

| # | Başlık | Kural / Olay | Son soru (kanca) |
|---|---|---|---|
| 1 | İlk Gece | "Saat 03:00'te heykellere bakma." Kemal bakar; bir heykel ona dönmüştür. | Sen olsan ışığı söndürür müydün? |
| 2 | İkinci Kural | "Bir heykel yer değiştirirse onu sayma." Heykellerin sayısı artıyor. | Kaç tane saydın? |
| 3 | Telsiz | Telsizden Rıza Usta'nın sesi geliyor ama o kaybolalı bir yıl oldu. | Cevap verir miydin? |
| 4 | Kırmızı Oda | Kapısı hiç açılmayan bir oda; içeriden vurma sesleri. | Kapıyı açar mıydın? |
| 5 | Ayak İzleri | Tozlu zeminde çıplak ayak izleri Kemal'in kulübesine çıkıyor. | Kulübeye girer miydin? |
| 6 | Kamera 7 | Güvenlik kamerasında Kemal kendini görüyor, ama o an orada değil. | Hangisi gerçek Kemal? |
| 7 | Rıza Usta'nın Defteri | Eski bekçinin defteri bulunuyor; son sayfada Kemal'in adı yazılı. | Okumaya devam eder miydin? |
| 8 | Boş Kaide | Bir kaide boş. Heykel artık müzenin içinde bir yerde dolaşıyor. | Saklanır mıydın, kaçar mıydın? |
| 9 | Son Kural | "Sabah ezanı okunana kadar müzeden çıkma." Kapı açık bırakılmış. | Dışarı çıkar mıydın? |
| 10 | Sabah | Gerçek ortaya çıkıyor: Rıza Usta bir heykele dönüşmüş, Kemal'in sırası geldi mi? | Yarın gece nöbete gelir miydin? |

## Klasörler

- `bolum01/senaryo.md`: Çekim listesi, ekrandaki yazılar, seslendirme metni
- `bolum01/sahne.py`: Blender sahnesini sıfırdan kuran ve render alan script
- `bolum01/ses.py`: Ortam sesi, efektler ve gerilim müziğini üreten script
- `bolum01/yazilar.py`: Ekrandaki yazıları (başlık, kural, son kart) üreten script
- `bolum01/birlestir.sh`: Render kareleri, yazıları ve sesi videoya dönüştürür
- `cikti/`: Bitmiş videolar
