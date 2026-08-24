"""Quick sanity check for the scorer. Run: python test_scorer.py"""
from main import Pair, score_minilm

pairs = [Pair(stimulus="bread", response="butter"),
         Pair(stimulus="head", response="hair"),
         Pair(stimulus="to sing", response="song"),
         Pair(stimulus="green", response="grass"),
         Pair(stimulus="window", response="Tuesday"),
         Pair(stimulus="frog", response="spreadsheet")]
for p, s in zip(pairs, score_minilm(pairs)):
    print(f"{p.stimulus:>10} -> {p.response:<12} {s:.2f}")
