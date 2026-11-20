# Altın Set Ölçüm Raporu – 20.11.2026 (1. ölçüm)

**Hazırlayan:** Melek (Kalite ve Test) · **İlgili görev:** #8

## Nasıl ölçüldü?

- Altın set: `eval/golden_set_50.csv` (50 soru)
- Komut: `python eval/run_eval.py --csv eval/golden_set_50.csv`
- Bot: Melek'in bilgisayarında, kendi Gemini anahtarıyla, `CACHE_ENABLED=false`
- Ayrıntılı sonuçlar: `eval/sonuclar_2026-11-20.csv`

> ⚠️ Test çalıştırılırken `--csv eval/golden_set_50.csv` mutlaka yazılmalı. Yazılmazsa program eski şablonu (`golden_set.csv`) okur.

## Altın setin içeriği

| Tür | Sayı |
|---|---|
| rag | 40 |
| takvim | 4 |
| rag_bilgi_yok (belgede yok) | 4 |
| guvenlik | 2 |
| **Toplam** | **50** |

- 1–30: Rehberdeki sorular · 31–50: Melek'in eklediği sorular
- 21 soru şu an test edilebilir, 29 soru "BELGE BEKLIYOR" (belgesi henüz yüklenmedi)

## Sonuç

| Ölçüt | Sonuç | Hedef | Durum |
|---|---|---|---|
| Doğru yanıt oranı (50 soru) | %32,0 (16/50) | %80+ | ❌ (29 soru belge bekliyor) |
| Doğru yanıt oranı (test edilebilir 21 soru) | %76,2 (16/21) | %80+ | 🟡 Çok yakın |
| Ortalama süre | 3,98 sn | < 5 sn | ✅ |
| En uzun süre | 20,12 sn (soru 7) | < 5 sn | ❌ |

## Doğru çıkanlar (16)

1, 3, 4, 5, 6, 7, 9 · 28, 44, 50 (belgede yok) · 29, 30 (güvenlik) · 31, 32, 33, 45

## Yanlış çıkanların sınıflandırması (34)

### 1) İfade çok katı → Melek düzeltecek (1)

| id | Botun cevabı | Sorun |
|---|---|---|
| 13 | "Hayır, ders kaydının tamamlanması için danışman onayı zorunludur." | Cevap doğru. Beklenen ifade `gerekiyor`, bot "zorunludur" dedi. Bir sonraki sürümde ifade gevşetilecek. |

### 2) Veri eksik → Zehra (7)

| id | Sorun | Çözüm |
|---|---|---|
| 2 | Sadece güz ara sınavları geldi, bahar gelmedi | takvim.json: bahar ara sınavlarına "vize" anahtar kelimesi |
| 10 | Tarihler doğru ama takvim yerine Gemini cevapladı | takvim.json: "ders kaydı" anahtar kelimesi |
| 38 | Tarihler doğru ama takvim yerine Gemini cevapladı | takvim.json: "ders ekleme bırakma" anahtar kelimesi |
| 49 | ARDEK birimi yok, Öğrenci İşleri'ne yönlendirdi | birimler.json: ARDEK birimi (teknofest, yarışma, proje, 2209) |
| 18, 19, 24 | "…ile iletişime geçebilirsin:" deyip boş bırakıyor | birimler.json: ATUS ve KYK iletişim bilgileri boş |

Ayrıca **22 ve 23** (topluluk) soruları SKS yerine Öğrenci İşleri'ne yönlendirildi. Sebep Türkçe ünsüz yumuşaması: soruda "topluluğ-una", anahtar kelime "topluluk". birimler.json'a "topluluğ" eklenmeli (veya eşleştirme kodu ekleri dikkate almalı).

### 3) Belge yüklenmemiş → Zehra (24)

8, 11, 12, 14, 15, 16, 17, 20, 21, 22, 23, 25, 26, 27, 34, 36, 39, 40, 41, 42, 43, 46, 47, 48

Bot bu soruların hepsinde **uydurmadı**, "bulamadım" deyip birime yönlendirdi ✅ (8'de belgede olan harf notlarını anlattı.)

### 4) Bot gerçekten hatalı → Betül (2)

| id | Botun cevabı | Sorun |
|---|---|---|
| 35 | "Paylaştığın belgelerde … doğrudan bir kısıtlayıcı bilgi bulunmamaktadır." | Belge yokken "bulamadım" demesi gerekirdi; `answered=true` döndü. "Paylaştığın belgeler" ifadesi öğrenciye tuhaf geliyor. |
| 37 | "Evet, çift ana dal ve yan dal eğitimi alabilirsiniz…" | Belge yokken cevap verdi, "farklı programlarda olmalı" şartını atladı. Eksik / uydurmaya yakın. |

### 5) Şilan'ın bilgisine

- **Süre:** Soru 7, 20,1 sn sürdü; diğerleri 7 sn'nin altında.
- **Konu dışı sorular:** 28 (hava) ve 50 (ATM) varsayılan olarak Öğrenci İşleri'ne yönlendiriliyor. Hiçbir anahtar kelime eşleşmezse birim önermemek daha doğru olabilir.
- **Eşitlik durumu:** 40 (Erasmus not ortalaması) Erasmus yerine Öğrenci İşleri'ne gitti; "erasmus" ve "not" birer puan aldı, listede ilk sıradaki birim kazandı.

## Sonraki adımlar

1. Zehra belgeleri ve veri düzeltmelerini yükleyince 2. ölçüm yapılacak.
2. 13. sorunun ifadesi gevşetilecek.
3. Betül'ün düzeltmelerinden sonra 35 ve 37 tekrar denenecek.
4. Her ölçümün tarihi ve oranı bu klasörde `olcum_raporu_<tarih>.md` olarak saklanacak.
