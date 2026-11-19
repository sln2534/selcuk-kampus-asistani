# CLAUDE.md — Claude Code için proje rehberi

Bu dosya, VS Code'da Claude Code ile çalışırken projenin bağlamını verir. Kullanıcılarla **Türkçe** konuş.

## Proje
Selçuk Üniversitesi öğrencileri için Telegram tabanlı RAG botu. Topluma Hizmet Uygulamaları dersi projesi, 5 kişilik ekip, bitiş: 3 Ocak 2027. Sıfır bütçe (ücretsiz katmanlar).

## Mimari
- `app/bot.py` → Telegram, `/ask` uç noktasını HTTP ile çağırır. İş mantığı bota yazılmaz, API'ye yazılır.
- `app/api.py` → sıra: güvenlik filtresi → takvim (`app/takvim.py`) → RAG (`app/rag/answer.py`).
- `app/rag/ingest.py` → `data/pdfs/*.pdf` → temizle → parçala → ChromaDB (`data/chroma/`).
- `app/rag/answer.py` → `answer_question(q, retriever, llm)`; retriever ve llm enjekte edilebilir (testlerde sahte).
- Ayarlar yalnızca `app/config.py` (pydantic-settings, `.env`).
- `app/cache.py` → belgeden verilmiş cevapları `data/cevap_onbellek.json`'da saklar; ingest önbelleği siler, SYSTEM_PROMPT değişince eski kayıtlar geçersiz olur. `CACHE_ENABLED=false` ile kapanır.

## Kesin kurallar
1. **Uydurma yok.** Model yalnızca bağlamdaki belgelere göre yanıt verir; yoksa `BILGI_YOK` → birim yönlendirme. Bu davranışı zayıflatan değişiklik yapma.
2. **Tarihler LLM'den gelmez**, `data/takvim.json`'dan gelir.
3. **KVKK:** Kullanıcı ID'si, adı, kullanıcı adı, telefon, konum asla düz metin olarak loglanmaz/saklanmaz. Yalnızca `stats.anon_user()` özeti.
4. `data/birimler.json` ve `data/takvim.json` içine **resmî kaynakta doğrulanmamış** telefon, e-posta veya tarih yazma. Bilinmeyeni boş bırak.
5. Gizli anahtarlar yalnızca `.env`'de. `.env` commit edilmez.
6. Yanıtlar kısa, sade, samimi Türkçe (anket: %45,7 samimi/yardımsever, %39,1 kısa/net istiyor).

## Komutlar
```bash
pytest -q                          # her değişiklikten sonra çalıştır, API anahtarı gerektirmez
python -m app.rag.ingest --reset   # PDF'leri yeniden indeksle
uvicorn app.api:app --reload       # API
python -m app.bot                  # bot
python eval/run_eval.py            # altın set KPI (API çalışırken)
```

## Çalışma şekli
- Her görev bir GitHub issue'su; dal adı `ozellik/<kisa-ad>`, PR ile `main`'e. Testler geçmeden birleştirme.
- Yeni özellik = yeni test (`tests/`). LLM ve Chroma'yı testlerde sahtele.
- Görev listesi ve kimin ne yaptığı: `docs/GOREVLER.md`.
