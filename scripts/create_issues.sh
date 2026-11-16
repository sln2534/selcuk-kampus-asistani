#!/usr/bin/env bash
# docs/GOREVLER.md'deki görevleri GitHub issue'su olarak açar.
# Gerekli: GitHub CLI (gh) ve `gh auth login`. Repo klasöründe çalıştırın:  bash scripts/create_issues.sh
set -euo pipefail

for l in "veri:0E8A16" "rag:1D76DB" "bot:5319E7" "test:FBCA04" "yonetim:D93F0B" "deploy:B60205"; do
  gh label create "${l%%:*}" --color "${l##*:}" --force >/dev/null
done

issue() { gh issue create --title "$1" --label "$2" --body "$3" >/dev/null && echo "✓ $1"; }

issue "Repo, collaborator ve Projects board kurulumu" yonetim "Sorumlu: Seval. 4 ekip üyesini collaborator ekle, Board görünümü: Yapılacak / Sürüyor / İncelemede / Bitti."
issue "BotFather ile bot oluşturma" bot "Sorumlu: Şilan. Açıklamaya 'Öğrenci projesidir, resmî değildir' uyarısı. Token yalnızca .env'de."
issue "Gemini API anahtarı ve güncel model adı" bot "Sorumlu: Şilan. AI Studio'da ücretsiz Flash modelini doğrula, GEMINI_MODEL'i güncelle."
issue "Resmî PDF'lerin toplanması" veri "Sorumlu: Zehra Nur. Yönetmelik, akademik takvim, burs/yurt/yemekhane, kütüphane, topluluk yönergesi → data/pdfs/. Yalnızca herkese açık belgeler."
issue "takvim.json'ı resmî akademik takvimden doldur" veri "Sorumlu: Zehra Nur. Şu anki veri ÖRNEK. 'kaynak' alanını güncelle."
issue "birimler.json iletişim bilgileri" veri "Sorumlu: Zehra Nur. Yalnızca selcuk.edu.tr kaynaklı bilgi."
issue "Gerçek PDF'lerle indeksleme ve parametre ayarı" rag "Sorumlu: Betül. chunk_size, top_k, max_distance değerlerini altın sete göre ayarla."
issue "Altın set v1: beklenen ifadeler ve kaynaklar" test "Sorumlu: Melek. eval/golden_set.csv doldur, run_eval.py ile ilk KPI ölçümü."
issue "KVKK aydınlatma metni ve /gizlilik komutu" test "Sorumlu: Melek + Şilan. docs/KVKK.md son hâli, bot komutu."
issue "Prompt injection güvenlik testleri" test "Sorumlu: Melek. En az 20 deneme, sonuç raporu."
issue "Railway deploy" deploy "Sorumlu: Şilan. api + bot iki servis, data/ için volume."
issue "Prompt v2 (beta geri bildirimine göre)" rag "Sorumlu: Betül."
issue "Kapalı beta (20–30 kişi)" yonetim "Sorumlu: Seval + Melek. Geri bildirim formu."
issue "Ring/otobüs ve yemekhane hızlı modülleri" veri "Sorumlu: Zehra Nur + Şilan. Anketin en çok istenen anlık bilgileri. Resmî kaynak yoksa bağlantı ver."
issue "50–100 kişilik pilot ve QR dağıtımı" yonetim "Sorumlu: Seval."
issue "Etki ölçümü ve KPI raporu" test "Sorumlu: Melek + Seval."
issue "Sonuç raporu, README, devir teslim kılavuzu, final sunumu" yonetim "Sorumlu: tüm ekip."
