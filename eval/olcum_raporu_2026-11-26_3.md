# Altın Set Ölçüm Raporu – 26.11.2026 (3. ölçüm)

**Hazırlayan:** Melek (Kalite ve Test) · **İlgili görev:** #8 · **Önceki ölçüm:** `olcum_raporu_2026-11-20_2.md`

## Ne değişti?

- **Zehra:** 12 yeni belge (Çift Ana Dal, Yan Dal, Erasmus, Yaz Okulu, Burs, Kısmi Zamanlı, Kütüphane, Öğrenci Toplulukları, Ölçme ve Değerlendirme, Kurum İçi Yatay Geçiş, Mazeretler, Muafiyet ve İntibak), fakülteye özel takvimler (Tıp, Diş Hekimliği, Hukuk, Veteriner, Hazırlık) ve akademik birim rehberi
- **Şilan:** belgede yok cevabının yeni hâli, KVKK onay düğmesi ve günlük rastgele tuz (#48)
- **Altın set (Melek):** 50 → 54 soru. 20 soru yeni belgelerden dolduruldu; 15. soru güncellendi; 43'teki hata düzeltildi (normal öğrenci yaz okulunda en fazla 3 ders / 12 kredi); fakülte takvimi için 4 soru eklendi (51–54)

## Nasıl ölçüldü?

1. **Otomatik:** `python eval/run_eval.py` (`eval/golden_set.csv`, 54 soru) (Melek'in bilgisayarı, indeks yenilendi: 238 parça, `CACHE_ENABLED=false`)
2. **Elle kontrol:** 54 cevabın hepsi tek tek okundu ve belgeyle karşılaştırıldı. Otomatik test yalnızca kelimeye baktığı için anlamca doğru ama kelimesi farklı cevapları ✗, kelimesi geçen ama yanıltıcı cevapları ✓ sayabiliyor.
3. **Elle tekrar deneme:** Şüpheli ve belge bekleyen 11 soru tekrar soruldu: 8, 11, 16, 17, 18, 19, 20, 24 Şilan'ın çalıştırdığı bot üzerinden Telegram'da; 47, 48, 52 yerel API'de (Swagger, /ask). Sonuçların hepsi otomatik testle aynı çıktı.

Ayrıntılar: `eval/sonuclar_2026-11-26_3.csv`

## Sonuç

| Ölçüt | 1. ölçüm | 2. ölçüm | **3. ölçüm** | Hedef |
|---|---|---|---|---|
| Soru sayısı | 50 | 50 | 54 | – |
| Otomatik doğruluk | %32,0 | %42,0 | **%77,8** (42/54) | %80+ |
| Elle kontrol – tüm sorular | – | – | **%79,6** (43/54) | %80+ |
| Elle kontrol – belgesi olan 46 soru | – | – | **%93,5** (43/46) | %80+ ✅ |
| Ortalama süre | 3,98 sn | 3,74 sn | 7,37 sn | < 5 sn ❌ |
| Ortanca süre | – | 3,31 sn | 5,23 sn | < 5 sn |

Elle kontrol dağılımı: **43 doğru · 1 kısmen · 2 yanlış · 8 belge yok**

## Otomatik test ile elle kontrolün ayrıldığı yerler

| id | Otomatik | Elle | Neden |
|---|---|---|---|
| 24 | ✓ | ❌ Yanlış | Yurt başvurusu sorusuna "barınma bursu" anlatıldı. Soru belge beklediği için beklenen ifade boştu; `run_eval.py` boş ifadeyi doğru sayıyor. |
| 37 | ✗ | ✅ Doğru | "Farklı programlarda hem çift ana dal hem yan dal yapılabilir" dedi; yalnızca "evet" kelimesi yoktu. İfade `farklı` olarak gevşetildi. |
| 46 | ✗ | ✅ Doğru | "Kesin kayıttan sonra ekleme ve silme uygulanmaz" dedi; "hayır" kelimesi yoktu. İfade `uygulanmaz` olarak gevşetildi. |

## Yanlış / eksik cevaplar

| id | Soru | Sorun | Kim |
|---|---|---|---|
| 8 | Geçme notu nasıl hesaplanıyor? | Formül var, %40 / %60 katkı yüzdeleri yok (kısmen) | Betül |
| 24 | Yurt başvurusu nereden yapılır? | "Barınma bursu" anlatıyor, alakasız kaynaklar gösteriyor | Betül |
| 52 | Hukuk fakültesinde vize ne zaman? | Takvimde var, bot bulamıyor (anahtar kelime) | Zehra |

## Belge bekleyen sorular (8)

11, 16, 17, 18, 19, 20, 47, 48 – bot uydurmadı, "bulamadım" deyip doğru birime yönlendirdi. **İstisna – 19:** "Kampüse tramvayla nasıl giderim?" sorusu konu dışı sayılıp "yardımcı olamam" diye reddedildi; "bulamadım + ATUS" demeliydi (Betül).

## Hız

| Tür | Soru | Ortalama | Ortanca | 5 sn üstü |
|---|---|---|---|---|
| Takvim | 8 | 0,01 sn | 0,01 sn | 0 |
| Güvenlik filtresi | 2 | 0 sn | 0 sn | 0 |
| Belgeden (Gemini) | 44 | 9,04 sn | 5,71 sn | 32 |

25 sn'yi aşan 6 cevap (soru 1, 9, 18, 25, 37, 48) yaklaşık her 8–9 soruda bir geliyor. Bu düzen, Gemini ücretsiz sürümünün dakika sınırına takılıp beklendiğini düşündürüyor (indekslemedeki "65 sn bekleniyor" ile aynı sınır). Bu 6 soru hariç ortalama ~4,8 sn. Elle tekrar denemede 47. soru 3,1 sn'de geldi; 48. soru yine yavaştı (46,6 sn) ama API açıldıktan sonra sorulan ilk soruydu, yani bu süreye ilk açılıştaki yükleme de eklenmiş olabilir. Belge sayısı 2'den 15'e çıktığı için arama süresi de bir miktar arttı.

## Küçük gözlem

- Telegram'da "orda mısın" yazınca bot "Buradayım!" diye cevap verdi ama altına yönetmelik kaynakları ekledi (Betül).

## Sonraki adımlar

1. Betül: hız (dakika sınırı), 8, 19, 24 ve selamlaşmaya kaynak gösterme
2. Zehra: 52 (hukuk vize anahtar kelimesi), kalan 8 sorunun belgeleri
3. Şilan: `run_eval.py` beklenen ifadesi boş satırları doğru saymasın
4. Düzeltmelerden sonra 4. ölçüm
