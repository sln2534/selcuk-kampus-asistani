"""Altın set değerlendirmesi: doğru yanıt oranı ve yanıt süresi KPI'ları.

API çalışırken:
    python eval/run_eval.py --api http://localhost:8000

Bir yanıt "doğru" sayılır eğer:
  * beklenen_tur ile dönen tur eşleşiyorsa (rag / takvim / guvenlik / rag_bilgi_yok) VE
  * beklenen_anahtar_ifadeler doluysa, '|' ile ayrılmış ifadelerin hepsi yanıtta geçiyorsa.
Beklenen türü "rag" olup anahtar ifadesi BOŞ olan sorular otomatik puanlanamaz: doğru ya da yanlış
sayılmaz, "elle kontrol" diye işaretlenir ve doğruluk oranına katılmaz.
Melek: anahtar ifadeleri ve kaynakları resmî belgelerden doldur; şüpheli satırları elle işaretle.
"""
import argparse
import csv
import statistics
from pathlib import Path

import httpx

HERE = Path(__file__).parent


def kind_of(resp: dict) -> str:
    if resp["kind"] == "rag" and not resp["answered"]:
        return "rag_bilgi_yok"
    return resp["kind"]


def grade(row: dict, got: str, answer: str) -> int | None:
    """1 = doğru, 0 = yanlış, None = otomatik puanlanamaz (elle kontrol edilmeli)."""
    phrases = [p.strip().lower() for p in row["beklenen_anahtar_ifadeler"].split("|") if p.strip()]
    if not phrases and row["beklenen_tur"] == "rag":
        return None  # neyin doğru olduğu bilinmiyor; boş ifade "her şey doğru" demek olmamalı
    return int(got == row["beklenen_tur"] and all(p in answer.lower() for p in phrases))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://localhost:8000")
    ap.add_argument("--csv", default=HERE / "golden_set.csv")
    ap.add_argument("--out", default=HERE / "sonuclar.csv")
    args = ap.parse_args()

    rows = list(csv.DictReader(open(args.csv, encoding="utf-8")))
    results, latencies = [], []
    with httpx.Client(timeout=60) as c:
        for r in rows:
            resp = c.post(f"{args.api}/ask", json={"question": r["soru"]}).json()
            got = kind_of(resp)
            ok = grade(r, got, resp["answer"])
            latencies.append(resp["latency_ms"])
            results.append({**r, "donen_tur": got, "dogru": "" if ok is None else ok, "sure_ms": resp["latency_ms"],
                            "yanit": resp["answer"].replace("\n", " ")[:300]})
            mark = "?" if ok is None else ("✓" if ok else "✗")
            print(f"{mark} [{r['id']}] {r['soru'][:60]}")

    with open(args.out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader()
        w.writerows(results)

    graded = [x["dogru"] for x in results if x["dogru"] != ""]
    acc = sum(graded) / len(graded) if graded else 0.0
    print(f"\nDoğru yanıt oranı: %{acc*100:.1f} ({sum(graded)}/{len(graded)} puanlanan soru; hedef %80+)")
    if len(graded) < len(results):
        print(f"Elle kontrol edilecek (beklenen ifadesi boş): {len(results) - len(graded)} soru, '?' ile işaretli")
    print(f"Ortalama süre: {statistics.mean(latencies)/1000:.2f} sn · en uzun: {max(latencies)/1000:.2f} sn (hedef < 5 sn)")
    print(f"Ayrıntılar: {args.out}")


if __name__ == "__main__":
    main()
