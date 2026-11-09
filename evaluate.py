import csv
import math

from app import create_app
from app.db import get_db
from app.services.keyword_matcher import keyword_score
from app.services.ranking import rank_opportunities, student_text
from app.services.semantic_matcher import opportunity_text, semantic_scores

PROFILES = "data/eval_profiles.csv"
LABELS = "data/relevance_labels.csv"
KS = (3, 5)


def to_number(value):
    value = (value or "").strip()
    return float(value) if value else None


def load_profiles():
    with open(PROFILES, newline="", encoding="utf-8-sig") as f:
        profiles = {}
        for row in csv.DictReader(f):
            row["cgpa"] = to_number(row["cgpa"])
            row["ielts"] = to_number(row["ielts"])
            profiles[row["profile_id"]] = row
        return profiles


def load_labels():
    labels = {}
    with open(LABELS, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            value = row["relevant"].strip()
            if value in ("0", "1"):
                labels[(row["profile_id"], int(row["opportunity_id"]))] = int(value)
    return labels


def precision_at_k(rels, k):
    return sum(rels[:k]) / k


def recall_at_k(rels, k):
    total = sum(rels)
    return sum(rels[:k]) / total if total else 0.0


def ndcg_at_k(rels, k):
    dcg = sum(r / math.log2(i + 2) for i, r in enumerate(rels[:k]))
    ideal = sorted(rels, reverse=True)
    idcg = sum(r / math.log2(i + 2) for i, r in enumerate(ideal[:k]))
    return dcg / idcg if idcg else 0.0


def main():
    profiles = load_profiles()
    labels = load_labels()
    app = create_app()

    scores = {name: {k: {"P": [], "R": [], "N": []} for k in KS}
              for name in ("keyword", "semantic", "combined")}
    skipped = []

    with app.app_context():
        rows = get_db().execute("SELECT * FROM opportunities ORDER BY id").fetchall()

        for pid, p in profiles.items():
            ids = [r["id"] for r in rows]
            if any((pid, i) not in labels for i in ids):
                skipped.append(pid + " (not fully labelled)")
                continue
            if not any(labels[(pid, i)] for i in ids):
                skipped.append(pid + " (no relevant opportunity)")
                continue

            text = student_text(p)
            kw = [keyword_score(text, opportunity_text(r))[0] for r in rows]
            sem = semantic_scores(text, rows)
            combined = rank_opportunities(p, rows)

            orders = {
                "keyword": [r["id"] for _, r in sorted(zip(kw, rows), key=lambda x: -x[0])],
                "semantic": [r["id"] for _, r in sorted(zip(sem, rows), key=lambda x: -x[0])],
                "combined": [res["opportunity"]["id"] for res in combined],
            }
            for name, order in orders.items():
                rels = [labels[(pid, i)] for i in order]
                for k in KS:
                    scores[name][k]["P"].append(precision_at_k(rels, k))
                    scores[name][k]["R"].append(recall_at_k(rels, k))
                    scores[name][k]["N"].append(ndcg_at_k(rels, k))

    used = len(scores["keyword"][KS[0]]["P"])
    print(f"Profiles evaluated: {used}")
    for s in skipped:
        print("  skipped:", s)
    print()
    header = "method".ljust(10) + "".join(f"P@{k}  R@{k}  nDCG@{k}   " for k in KS)
    print(header)
    for name in ("keyword", "semantic", "combined"):
        line = name.ljust(10)
        for k in KS:
            m = scores[name][k]
            avg = lambda xs: sum(xs) / len(xs) if xs else 0.0
            line += f"{avg(m['P']):.2f}  {avg(m['R']):.2f}  {avg(m['N']):.2f}     "
        print(line)


if __name__ == "__main__":
    main()