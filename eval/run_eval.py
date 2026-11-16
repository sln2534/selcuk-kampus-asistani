"""Altın set değerlendirmesi: doğru yanıt oranı ve yanıt süresi KPI'ları.

API çalışırken:
    python eval/run_eval.py --api http://localhost:8000

Bir yanıt "doğru" sayılır eğer:
  * beklenen_tur ile dönen tur eşleşiyorsa (rag / takvim / guvenlik / rag_bilgi_yok) VE
  * beklenen_anahtar_ifadeler doluysa, '|' ile ayrılmış ifadelerin hepsi yanıtta geçiyorsa.
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
            phrases = [p.strip().lower() for p in r["beklenen_anahtar_ifadeler"].split("|") if p.strip()]
            ok = got == r["beklenen_tur"] and all(p in resp["answer"].lower() for p in phrases)
            latencies.append(resp["latency_ms"])
            results.append({**r, "donen_tur": got, "dogru": int(ok), "sure_ms": resp["latency_ms"],
                            "yanit": resp["answer"].replace("\n", " ")[:300]})
            print(f"{'✓' if ok else '✗'} [{r['id']}] {r['soru'][:60]}")

    with open(args.out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader()
        w.writerows(results)

    acc = sum(x["dogru"] for x in results) / len(results)
    print(f"\nDoğru yanıt oranı: %{acc*100:.1f} (hedef %80+)")
    print(f"Ortalama süre: {statistics.mean(latencies)/1000:.2f} sn · en uzun: {max(latencies)/1000:.2f} sn (hedef < 5 sn)")
    print(f"Ayrıntılar: {args.out}")


if __name__ == "__main__":
    main()
