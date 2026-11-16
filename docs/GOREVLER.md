# Görevler ve yol haritası

Durum: 16 Kasım 2026. Teklif planına göre 6–7. hafta (2–15 Kas, "Bot + RAG") yeni bitti; kod iskeleti bu hafta kuruldu. **9. haftaya (23 Kas) kadar** aşağıdaki "Hemen" maddeleri kapatılırsa plan yakalanır.

Her madde `scripts/create_issues.sh` ile GitHub issue'su olarak açılabilir. Kanban: GitHub → Projects → *Board* (Yapılacak / Sürüyor / İncelemede / Bitti).

## ✅ Hazır (iskelet)
- Repo yapısı, FastAPI `/ask` `/health` `/stats`, Telegram botu (`/start`, `/takvim`, "yazıyor…")
- PDF → temizleme → parçalama → ChromaDB indeksleme
- Kaynak gösteren RAG yanıtı + "bilmiyorum" akışı + birim yönlendirme
- Takvim modülü (LLM'siz tarih yanıtı), anonim KPI kaydı, prompt-injection ön filtresi
- Docker Compose, GitHub Actions CI, 16 birim testi, 30 soruluk altın set taslağı

## 🔥 Hemen (16–22 Kas)
| # | Görev | Sorumlu |
|---|---|---|
| 1 | GitHub reposunu aç, 4 kişiyi *collaborator* ekle, Projects board kur, issue'ları aç | Seval |
| 2 | BotFather ile botu oluştur (ad, açıklamaya "Öğrenci projesidir, resmî değildir" uyarısı, profil resmi) | Şilan |
| 3 | Google AI Studio API anahtarı al, güncel ücretsiz Flash model adını `.env`'e yaz | Şilan |
| 4 | Resmî PDF'leri topla → `data/pdfs/` (Ön Lisans ve Lisans Eğitim-Öğretim ve Sınav Yönetmeliği, akademik takvim, burs/yurt/yemekhane, kütüphane, öğrenci toplulukları yönergesi). Anket önceliği: ulaşım, burs, yemekhane, topluluk, kütüphane, sınav | Zehra Nur |
| 5 | `data/takvim.json`'ı 2026-27 resmî akademik takvimden doldur (şu an ÖRNEK veri) | Zehra Nur |
| 6 | `data/birimler.json` iletişim bilgilerini resmî siteden doldur | Zehra Nur |
| 7 | Gerçek PDF'lerle `ingest` çalıştır; chunk_size / top_k / max_distance ayarla | Betül |
| 8 | Altın sete beklenen anahtar ifade + kaynak sayfası yaz, ilk KPI ölçümü | Melek |
| 9 | KVKK aydınlatma metnini (`docs/KVKK.md`) son hâline getir, bot `/gizlilik` komutuna bağla | Melek + Şilan |

## 9–11. hafta (23 Kas – 13 Ara) · Test ve pilot
| # | Görev | Sorumlu |
|---|---|---|
| 10 | Prompt injection / güvenlik test seti (en az 20 deneme), sonuç raporu | Melek |
| 11 | Railway'e deploy (api + bot iki servis, `data/` için volume) | Şilan |
| 12 | Prompt v2: kapalı beta hatalarına göre düzenleme | Betül |
| 13 | 20–30 kişilik kapalı beta, geri bildirim formu | Seval + Melek |
| 14 | Anlık bilgi için hızlı modüller (anket: ring/otobüs %19,6, yemekhane %17,4): resmî kaynak varsa JSON/bağlantı | Zehra Nur + Şilan |
| 15 | 50–100 kişilik pilot, QR kod afişi ve öğrenci grubu duyurusu | Seval |

## 12. hafta (14–20 Ara) · Etki ölçümü
| 16 | Pilot sonu memnuniyet anketi, `/stats` + `run_eval.py` KPI raporu | Melek + Seval |

## 13–14. hafta (21 Ara – 3 Oca) · Teslim
| 17 | Sonuç raporu, final sunumu | Tüm ekip |
| 18 | Devir teslim kılavuzu (yeni dönem PDF'leri nasıl eklenir, takvim nasıl güncellenir) | Seval + Zehra Nur |
