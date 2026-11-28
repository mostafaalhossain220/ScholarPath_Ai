import csv
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.db import get_db
from app.services.keyword_matcher import keyword_score
from app.services.ranking import rank_opportunities, student_text
from app.services.semantic_matcher import HAS_MODEL

K = 5
EVAL_DIR = Path(__file__).resolve().parent


def load_profiles():
    with open(EVAL_DIR / "profiles.csv", newline="", encoding="utf-8") as f:
        return {row["profile_id"]: row for row in csv.DictReader(f)}


def load_labels():
    labels = {}
    with open(EVAL_DIR / "labels.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            labels.setdefault(row["profile_id"], {})[int(row["opportunity_id"])] = int(row["relevant"])
    return labels


def to_profile(row):
    return {
        "target_degree": row["target_degree"] or None,
        "cgpa": float(row["cgpa"]) if row["cgpa"] else None,
        "ielts": float(row["ielts"]) if row["ielts"] else None,
        "field": row["field"],
        "preferred_countries": row["preferred_countries"],
        "research_interests": row["research_interests"],
        "skills": row["skills"],
    }


def keyword_ranking(profile, rows):
    text = student_text(profile)
    scored = []
    for opp in rows:
        opp_text = " ".join(p for p in [opp["title"], opp["field"], opp["description"]] if p)
        score, _ = keyword_score(text, opp_text)
        scored.append((score, opp["id"]))
    scored.sort(reverse=True)
    return [oid for _, oid in scored]


def semantic_ranking(profile, rows):
    return [r["opportunity"]["id"] for r in rank_opportunities(profile, rows)]


def precision_at_k(ranked, rel, k):
    return sum(rel.get(o, 0) for o in ranked[:k]) / k


def recall_at_k(ranked, rel, k):
    total = sum(rel.values())
    if total == 0:
        return None
    return sum(rel.get(o, 0) for o in ranked[:k]) / total


def ndcg_at_k(ranked, rel, k):
    dcg = sum(rel.get(o, 0) / math.log2(i + 2) for i, o in enumerate(ranked[:k]))
    ideal = sorted(rel.values(), reverse=True)[:k]
    idcg = sum(r / math.log2(i + 2) for i, r in enumerate(ideal))
    return dcg / idcg if idcg else None


def average(values):
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else 0.0


def main():
    profiles = load_profiles()
    labels = load_labels()
    app = create_app()
    methods = {
        "keyword baseline": keyword_ranking,
        "semantic" if HAS_MODEL else "TF-IDF (light)": semantic_ranking,
    }

    # Profiles with no relevant opportunity (e.g. P20) cannot be scored
    # for recall or nDCG, so they are excluded from all metrics.
    evaluated = {
        pid: row
        for pid, row in profiles.items()
        if labels.get(pid) and sum(labels[pid].values()) > 0
    }
    skipped = [pid for pid in profiles if pid not in evaluated]

    with app.app_context():
        rows = get_db().execute("SELECT * FROM opportunities").fetchall()
        print(
            f"Profiles: {len(profiles)} (evaluated: {len(evaluated)}, "
            f"skipped: {', '.join(skipped) or 'none'}), "
            f"opportunities: {len(rows)}, K = {K}"
        )
        print(f"{'method':<20}{'P@K':>8}{'R@K':>8}{'nDCG@K':>8}")
        for name, fn in methods.items():
            p, r, n = [], [], []
            for pid, row in evaluated.items():
                rel = labels[pid]
                ranked = fn(to_profile(row), rows)
                p.append(precision_at_k(ranked, rel, K))
                r.append(recall_at_k(ranked, rel, K))
                n.append(ndcg_at_k(ranked, rel, K))
            print(f"{name:<20}{average(p):>8.3f}{average(r):>8.3f}{average(n):>8.3f}")


if __name__ == "__main__":
    main()