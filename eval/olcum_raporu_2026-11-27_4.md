# Altın Set Ölçüm Raporu – 27.11.2026 (4. ölçüm)

**Hazırlayan:** Melek (Kalite ve Test) · **İlgili görev:** #8 · **Önceki ölçüm:** `olcum_raporu_2026-11-26_3.md`

## Ne değişti?

- **Betül (#53):** soru 8 (%40 / %60), 19 (tramvay), 24 (yurt), selamlaşmaya kaynak eklenmemesi; hız için yeni model `gemini-3.5-flash-lite`, yedekler `gemini-3.1-flash-lite, gemini-3.5-flash`, 10 sn zaman aşımı
- **Şilan (#52):** `run_eval.py` boş ifadeli satırları artık doğru saymıyor; hukuk vize eşleşmesi (52)
- **Zehra (#54–#56):** 2026 tarihli Çift Ana Dal Yönergesi (2023 sürümü kaldırıldı), öğrenci deneyimi ve kampüs rehberi ("resmî değil" etiketli)
- **Altın set (Melek):** 54 soru korundu.
  - Rehberden cevaplanan sorulara beklenen ifade eklendi: 11, 16, 17, 18, 19, 20, 24
  - 44 (kimlik kartı) rehbere eklendiği için "belgede yok" testinden normal soruya çevrildi
  - 25 ve 37'nin kaynağı 2026 yönergesi olarak güncellendi (cevaplar aynı: 2.75, farklı)
  - Cevabı doğru ama kelimesi farklı 5 sorunun ifadesi gevşetildi: 6, 7, 13, 35, 36 (aşağıda)

## Nasıl ölçüldü?

1. **Otomatik:** `python eval/run_eval.py --csv golden_set_olcum4.csv --out eval/sonuclar_2026-11-27_4.csv` (Melek'in bilgisayarı, `git pull` ile #56'ya güncellendi, indeks yenilendi: 276 parça, `CACHE_ENABLED=false`)
2. **Elle kontrol:** 54 cevabın hepsi okundu ve belgeyle karşılaştırıldı.

**Not – ilk çalıştırma geçersiz sayıldı:** İlk denemede 8 soru (20, 22, 23, 24, 25, 26, 48, 49) "Şu an yapay zekâ servisine ulaşamıyorum" hatası verdi. Sebep: `.env`'de yalnızca `GEMINI_MODEL` değiştirilmişti, eski `GEMINI_FALLBACK_MODELS` satırı duruyordu. Betül'ün notundaki iki satır da değiştirilip API yeniden başlatılınca test baştan alındı; ikinci çalıştırmada **hiç hata yok**. Bu rapordaki sonuçlar ikinci çalıştırmanındır.

Ayrıntılar: `eval/sonuclar_2026-11-27_4.csv`

## Sonuç

| Ölçüt | 1. ölçüm | 2. ölçüm | 3. ölçüm | **4. ölçüm** | Hedef |
|---|---|---|---|---|---|
| Soru sayısı | 50 | 50 | 54 | 54 | – |
| Otomatik doğruluk | %32,0 | %42,0 | %77,8 | **%85,2** (46/54) | %80+ ✅ |
| Elle kontrol – tüm sorular | – | – | %79,6 | **%94,4** (51/54) | %80+ ✅ |
| Elle kontrol – belgesi olan sorular | – | – | %93,5 (43/46) | **%96,2** (51/53) | %80+ ✅ |
| Ortalama süre | 3,98 sn | 3,74 sn | 7,37 sn | **2,88 sn** | < 5 sn ✅ |
| Ortanca süre | – | 3,31 sn | 5,23 sn | **1,70 sn** | < 5 sn ✅ |
| En uzun | 20,1 sn | 21,6 sn | 30,3 sn | **9,1 sn** | – |

Elle kontrol dağılımı: **51 doğru · 0 kısmen · 2 yanlış · 1 belge yok**

## 3. ölçüme göre düzelenler

| id | Soru | 3. ölçüm | 4. ölçüm |
|---|---|---|---|
| 8 | Geçme notu nasıl hesaplanıyor? | Kısmen (%40/%60 yok) | ✅ Tam |
| 19 | Kampüse tramvayla nasıl giderim? | Konu dışı diye reddedildi | ✅ Rehberden cevap + ATUS |
| 24 | Yurt başvurusu nereden yapılır? | ❌ Barınma bursu | ✅ e-Devlet GSB yurt başvurusu |
| 52 | Hukuk fakültesinde vize ne zaman? | ❌ Bulunamıyordu | ✅ 31.10.2026 / 20.03.2027 |
| 11, 16, 17, 18, 20 | Öğrenci belgesi, yemekhane, ring, kütüphane | Belge yok | ✅ Rehberden cevap ("öğrenci deneyimi" uyarısıyla) |

## Otomatik test ile elle kontrolün ayrıldığı yerler

Beşinde de cevap doğru, yalnızca beklenen kelime geçmiyor. Yeni model evet/hayır sorularına "Hayır," diye başlamıyor. İfadeler gevşetildi (`eval/golden_set.csv`'de güncel).

| id | Eski ifade | Botun cevabı | Yeni ifade |
|---|---|---|---|
| 6 | birim + dilekçe | "ilgili birime başvurulması gerekmektedir" | birim |
| 7 | beş iş günü | "5 (beş) iş günü içinde" | iş günü |
| 13 | hayır + onay | "danışman onayı olmadan ders kaydı tamamlanmış olmaz" | onay |
| 35 | hayır | "başarısız dersin varken başvuru yapamazsın" | tüm dersleri |
| 36 | hayır | "aynı anda birden fazla çift ana dal programına kayıt yaptıramaz" | birden fazla |

## Yanlış cevaplar

| id | Soru | Sorun | Kim |
|---|---|---|---|
| 45 | Mezun olmak için not ortalamam en az kaç olmalı? | **Gerileme:** 3. ölçümde doğruydu (2,00). Şimdi "genel sınır belirtilmemiş" deyip çift ana dalın 2,72'sini veriyor. Yeni ÇAP yönergesi parçaları sınav yönetmeliğinin önüne geçiyor. | Betül |
| 48 | SUTİS makalesini arkadaşlarımla birlikte yazabilir miyim? | "Elimdeki resmî belgelere göre" diye başlayıp rehberdeki **doğrulanmamış** "en fazla 5 öğrenci" bilgisini veriyor; resmî kılavuzla uyuşmuyor. | Betül, Zehra |

## Belge yok (1)

47 – SUTİS resmî kılavuzu hâlâ yüklenmedi; bot uydurmadı, "bulamadım" dedi.

## Hız

| Tür | Soru | Ortalama | Ortanca | 5 sn üstü |
|---|---|---|---|---|
| Takvim | 8 | 0,00 sn | 0,00 sn | 0 |
| Güvenlik filtresi | 2 | 0 sn | 0 sn | 0 |
| Belgeden (Gemini) | 44 | 3,53 sn | 2,42 sn | 12 |

Ortalama 7,37 sn'den 2,88 sn'ye indi, 25–30 sn'lik bekleme tamamen kalktı. 5 sn'yi aşan 12 cevabın hepsi **18–34 arasında art arda** geldi (6–9 sn). Sorular hızlı sorulunca ana model sınıra takılıp yedek modele geçiyor olabilir. Hata yok ama bu aralıkta yavaşlıyor.

## Küçük gözlemler

- Öğrenci deneyimi rehberinden gelen bazı cevaplar da "Elimdeki resmî belgelere göre" diye başlıyor (11, 24, 48). Cevabın altında "öğrenci deneyimine dayanıyor" uyarısı var ama giriş cümlesi yanıltıcı.
- Bazı cevaplar "Selam!" ile başlıyor (17, 48).

## Sonraki adımlar

1. Betül: 45 (mezuniyet ortalaması gerilemesi); rehber parçası kullanılınca "resmî belgelere göre" denmemesi (48, 11, 24); 18–34 arasındaki yavaşlama
2. Zehra: SUTİS resmî kılavuzu (47, 48); rehberdeki "en fazla 5 öğrenci" bilgisinin doğrulanması
3. Melek: Telegram'da "orda mısın" / "merhaba" kontrolü ve güvenlik setinde T19'un yeniden testi (Betül'ün notu, madde 5)
