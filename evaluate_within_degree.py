import math
import random

from app import create_app
from app.db import get_db
from app.services.keyword_matcher import keyword_score
from app.services.ranking import rank_opportunities, student_text
from app.services.semantic_matcher import opportunity_text, semantic_scores
from evaluate import KS, load_labels, load_profiles, ndcg_at_k, precision_at_k, recall_at_k

# Each seed gives a different random starting order of the opportunities.
# Ties (for example many keyword scores of 0) are then broken randomly,
# so the result does not depend on the order of ids in the database.
SEEDS = range(10)


def random_baseline(n_rel, n, k):
    """Expected metrics if the opportunities were shown in random order."""
    discount = sum(1 / math.log2(i + 2) for i in range(k))
    ideal = sum(1 / math.log2(i + 2) for i in range(min(k, n_rel)))
    return n_rel / n, k / n, (n_rel / n) * discount / ideal


def main():
    profiles = load_profiles()
    labels = load_labels()
    methods = ("random", "keyword", "semantic", "combined")
    scores = {m: {k: {"P": [], "R": [], "N": []} for k in KS} for m in methods}
    used = set()

    app = create_app()
    with app.app_context():
        all_rows = get_db().execute("SELECT * FROM opportunities ORDER BY id").fetchall()

        for seed in SEEDS:
            rng = random.Random(seed)

            for pid, p in profiles.items():
                rows = [r for r in all_rows if r["degree_level"] == p["target_degree"]]
                if any((pid, r["id"]) not in labels for r in rows):
                    continue
                n_rel = sum(labels[(pid, r["id"])] for r in rows)
                if n_rel == 0 or n_rel == len(rows):
                    continue  # nothing to rank: all or none relevant

                used.add(pid)
                rng.shuffle(rows)  # random starting order, ties are broken randomly

                text = student_text(p)
                kw = [keyword_score(text, opportunity_text(r))[0] for r in rows]
                sem = semantic_scores(text, rows)
                comb = rank_opportunities(p, rows)
                orders = {
                    "keyword": [r["id"] for _, r in sorted(zip(kw, rows), key=lambda x: -x[0])],
                    "semantic": [r["id"] for _, r in sorted(zip(sem, rows), key=lambda x: -x[0])],
                    "combined": [x["opportunity"]["id"] for x in comb],
                }

                for k in KS:
                    rp, rr, rn = random_baseline(n_rel, len(rows), k)
                    scores["random"][k]["P"].append(rp)
                    scores["random"][k]["R"].append(rr)
                    scores["random"][k]["N"].append(rn)
                for name, order in orders.items():
                    rels = [labels[(pid, i)] for i in order]
                    for k in KS:
                        scores[name][k]["P"].append(precision_at_k(rels, k))
                        scores[name][k]["R"].append(recall_at_k(rels, k))
                        scores[name][k]["N"].append(ndcg_at_k(rels, k))

    print(f"Profiles evaluated (same-degree candidates only): {len(used)}")
    print(f"Averaged over {len(SEEDS)} random starting orders\n")
    print("method".ljust(10) + "".join(f"P@{k}  R@{k}  nDCG@{k}   " for k in KS))
    avg = lambda xs: sum(xs) / len(xs) if xs else 0.0
    for name in methods:
        line = name.ljust(10)
        for k in KS:
            m = scores[name][k]
            line += f"{avg(m['P']):.2f}  {avg(m['R']):.2f}  {avg(m['N']):.2f}     "
        print(line)


if __name__ == "__main__":
    main()