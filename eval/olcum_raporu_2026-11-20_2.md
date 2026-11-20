# Altın Set Ölçüm Raporu – 20.11.2026 (2. ölçüm)

**Hazırlayan:** Melek (Kalite ve Test) · **İlgili görev:** #8 · **Önceki ölçüm:** `olcum_raporu_2026-11-20.md`

## Ne değişti?

2. ölçüm, 1. ölçümün bulgularına göre yapılan düzeltmelerden sonra yapıldı:

- **PR #32 (Şilan):** kişisel veri filtresi, uzun mesaj uyarısı, birim yönlendirme düzeltmeleri
- **PR #33 (Betül):** RAG ayarları, ön filtre kalıpları, KONU_DISI kuralı, uydurma engeli (35, 37)
- **PR #34 (Melek):** `golden_set.csv` 50 soruluk sete geçti, 13. sorunun ifadesi gevşetildi (`hayır|onay`)
- **PR #35 (Zehra):** takvim anahtar kelimeleri ("vize", "ders kaydı", "ders ekleme", "ekleme bırakma")
- **PR #36 (Zehra):** ARDEK, ATUS ve KYK iletişim bilgileri

## Nasıl ölçüldü?

- Komut: `python eval/run_eval.py --out sonuclar_2.csv` (varsayılan `eval/golden_set.csv`)
- Bot: Melek'in bilgisayarında, kendi Gemini anahtarıyla, `CACHE_ENABLED=false`, indeks yenilendi (45 parça)
- Ayrıntılı sonuçlar: `eval/sonuclar_2026-11-20_2.csv`
- Yeni PDF yoktu: Zehra'nın Çift Ana Dal ve Yan Dal yönergeleri `ozellik/ek-yonergeler` dalında, henüz birleşmedi.

## Sonuç: 1. ölçüm → 2. ölçüm

| Ölçüt | 1. ölçüm | 2. ölçüm | Hedef | Durum |
|---|---|---|---|---|
| Doğru yanıt oranı (50 soru) | %32,0 (16/50) | **%42,0 (21/50)** | %80+ | ⬆️ 29 soru belge bekliyor |
| Test edilebilir 21 soru | %76,2 (16/21) | **%100 (21/21)** | %80+ | ✅ |
| Ortalama süre | 3,98 sn | **3,74 sn** | < 5 sn | ✅ |
| Ortanca süre | – | 3,31 sn | < 5 sn | ✅ |
| En uzun süre | 20,12 sn (soru 7) | 21,55 sn (soru 14) | < 5 sn | ❌ |

## 1. ölçümde yanlış olup düzelenler (5)

| id | Soru | Neden düzeldi |
|---|---|---|
| 2 | Vize sınavları ne zaman? | Takvime "vize" eklendi; güz ve bahar ara sınavları birlikte geldi (Zehra, #35) |
| 10 | Ders kaydı ne zaman? | Takvime "ders kaydı" eklendi; cevap artık takvimden geliyor (Zehra, #35) |
| 13 | Danışman onayı olmadan ders kaydı tamamlanır mı? | İfade gevşetildi (`hayır\|onay`); bot "Hayır, tamamlanmaz… onaylatması zorunludur" dedi (Melek, #34) |
| 38 | Ders ekleme bırakma ne zaman? | Takvime "ders ekleme / ekleme bırakma" eklendi (Zehra, #35) |
| 49 | Teknofest takımlarına maddi destek | ARDEK birimi eklendi; bot "bulamadım" deyip ARDEK'e yönlendirdi (Zehra, #36) |

## Yönlendirme düzeltmeleri (sonuca yansımayan ama düzelen)

- **22, 23 (topluluk):** Artık SKS'ye yönlendiriliyor (1. ölçümde Öğrenci İşleri'ne gidiyordu).
- **40 (Erasmus not ortalaması):** Artık Erasmus+ Kurum Koordinatörlüğü'ne yönlendiriliyor.
- **18, 19, 24 (ATUS, KYK):** İletişim bilgileri artık görünüyor (1. ölçümde boştu).

## Yanlış çıkanlar (29) – hepsi belge bekliyor

8, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 34, 35, 36, 37, 39, 40, 41, 42, 43, 46, 47, 48

Bot bu soruların 27'sinde uydurmadı ve standart "bulamadım" mesajıyla doğru birime yönlendirdi ✅ (8'de belgede olan YANO hesabını anlattı.)

**35 düzeldi:** 1. ölçümde "Paylaştığın belgelerde…" diye cevap veriyordu; artık standart "bulamadım" mesajı veriyor (Betül, #33).

**37 kısmen düzeldi (Betül'e not):** Artık "Evet" diye uydurmuyor. Ancak standart mesaj yerine *"…açık bir kısıtlama veya izin bilgisi bulunmamaktadır… öğrenci işleri ile görüşmenizi öneririm"* diyor ve `answered=true` dönüyor. Bu yüzden `rag_bilgi_yok` olarak sayılmıyor.

## Küçük gözlemler

- **Soru 5:** Bot cevaba "Selam!" diye başladı; diğer cevaplarda selamlama yok. Üslup tutarlılığı için Betül'e not.
- **Süre:** "Bulamadım" cevabı veren bazı sorular uzun sürdü (14: 21,6 sn, 11: 15,7 sn). 11 soru 5 sn'yi aştı; ortanca 3,3 sn olduğu için bunlar büyük olasılıkla Gemini'nin o anki yavaşlığından kaynaklanıyor. Bir sonraki ölçümde tekrar bakılacak.
- **28, 50 (hava, ATM):** Konu dışı sorular hâlâ varsayılan olarak Öğrenci İşleri'ne yönlendiriliyor (Şilan'ın bilgisine).

## Sonraki adımlar

1. **3. ölçüm:** Zehra'nın `ozellik/ek-yonergeler` dalı (Çift Ana Dal ve Yan Dal yönergeleri) birleşince → 25, 26, 34–37 test edilebilir olacak. İçerik kontrol edildi, cevaplar belgelerle uyumlu. Yalnızca yazım farkına dikkat: belgede "2.75" (nokta), altın sette `2,75` (virgül); 34'te belge sayıları yazıyla ("üçüncü", "beşinci") veriyor. Bot cevabına göre ifade gerekirse gevşetilecek.
2. Erasmus Uygulama Yönergesi, Yaz Okulu Uygulama Esasları, SUTİS kılavuzu, Ölçme ve Değerlendirme Yönergesi ve Burs Yönergesi yüklendikçe ilgili sorular açılacak.
