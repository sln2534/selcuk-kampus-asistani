# Selçuk Üniversitesi Kampüs Asistanı 🎓🤖

Telegram tabanlı, yapay zekâ destekli öğrenci bilgi botu. Öğrencilerin akademik takvim, sınav/mazeret kuralları, burs, yurt ve kampüs hizmetleriyle ilgili sorularını **resmî, herkese açık belgelere dayanarak** ve **kaynağını göstererek** yanıtlar. Belgelerde cevap yoksa uydurmaz, ilgili birime yönlendirir.

> Topluma Hizmet Uygulamaları dersi projesi · Selçuk Üniversitesi Teknoloji Fakültesi Bilgisayar Mühendisliği · Danışman: Prof. Dr. Nurettin Doğan
>
> ⚠️ Öğrenci projesidir, resmî bir üniversite hizmeti değildir.

## Nasıl çalışır?

```
Öğrenci (Telegram) ──► bot.py ──HTTP──► api.py /ask
                                          ├─ güvenlik filtresi (prompt injection)
                                          ├─ tarih sorusu mu? ──► data/takvim.json  (LLM'siz, kesin tarih)
                                          └─ RAG: ChromaDB'den ilgili parçalar ──► Gemini ──► kaynaklı yanıt
                                                    └─ bulunamazsa ──► data/birimler.json ("bilmiyorum" akışı)
```

## Klasör yapısı

| Yol | İçerik | Sorumlu |
|---|---|---|
| `app/bot.py` | Telegram botu (python-telegram-bot v21) | Şilan |
| `app/api.py` | FastAPI: `/ask`, `/health`, `/stats` | Şilan |
| `app/rag/ingest.py` | PDF okuma, temizleme, parçalama, indeksleme | Betül |
| `app/rag/answer.py` | Retriever, prompt, "bilmiyorum" akışı | Betül |
| `app/takvim.py` · `data/takvim.json` | Akademik takvim modülü | Zehra Nur |
| `app/units.py` · `data/birimler.json` | Birim yönlendirme tablosu | Zehra Nur |
| `data/pdfs/` | Resmî PDF'ler (yalnızca herkese açık belgeler) | Zehra Nur |
| `app/stats.py` | Anonim kullanım ve KPI kayıtları | Melek |
| `eval/` | Altın soru seti ve değerlendirme betiği | Melek |
| `docs/` | Görevler, KVKK metni | Seval |

## Kurulum (yerel)

Gerekenler: Python 3.11+, Git. İsteğe bağlı: Docker Desktop.

```bash
git clone https://github.com/<kullanici>/selcuk-kampus-asistani.git
cd selcuk-kampus-asistani
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # Windows: copy .env.example .env
```

`.env` dosyasını doldurun:
1. **TELEGRAM_BOT_TOKEN**: Telegram'da [@BotFather](https://t.me/BotFather) → `/newbot` → token'ı kopyalayın.
2. **GEMINI_API_KEY**: [Google AI Studio](https://aistudio.google.com/apikey) → *Create API key* (ücretsiz).
3. **GEMINI_MODEL**: AI Studio'da ücretsiz katmandaki güncel Flash modelinin adını yazın. (Teklifteki Gemini 1.5 Flash artık kullanımda değil.)

## Çalıştırma

```bash
# 1) PDF'leri data/pdfs/ klasörüne koyun, sonra indeksleyin
python -m app.rag.ingest --reset

# 2) API'yi başlatın  (http://localhost:8000/docs adresinden deneyebilirsiniz)
uvicorn app.api:app --reload

# 3) Ayrı bir terminalde botu başlatın
python -m app.bot
```

Docker ile ikisi birden: `docker compose up --build`

## Test ve değerlendirme

```bash
pytest -q                                   # birim testleri (API anahtarı gerekmez)
python eval/run_eval.py                     # altın set: doğru yanıt oranı + yanıt süresi
curl http://localhost:8000/stats            # anonim kullanım özeti
```

## Başarı ölçütleri

| Ölçüt | Hedef | Ölçüm |
|---|---|---|
| Aktif kullanıcı | 50–100 | `/stats` anonim sayaç |
| Doğru yanıt oranı | %80+ | `eval/run_eval.py` (30+ soru) |
| Yanıt süresi | < 5 sn | `/stats`, sistem logları |
| Memnuniyet | 4+/5 | Pilot sonu anketi |

## Etik ve KVKK

- Yalnızca üniversitenin web sitesinde herkese açık belgeler kullanılır.
- Kullanıcı kimliği, adı, telefon numarası veya konumu kaydedilmez. Aktif kullanıcı sayımı için Telegram ID'si günlük değişen tuzla tek yönlü özetlenir.
- `.env` (token ve anahtarlar) hiçbir zaman GitHub'a yüklenmez.

## Ekip

Seval Özgür (proje yöneticisi) · Zehra Nur Kaya (veri ve içerik) · Betül Acar (RAG) · Şilan Akdemir (backend ve bot) · Melek Güngöl (kalite ve test)

## Lisans

MIT
