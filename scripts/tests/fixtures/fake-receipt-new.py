#!/usr/bin/env python3
"""fake-receipt-new.py — stand-in receipt helper that knows the 1.8.5 graph fields.

Used by test_search_graph_expansion.sh. Writes its argv (one per line) to $FAKE_RCPT_ARGV.
"""
import argparse
import os
import sys

p = argparse.ArgumentParser()
for a in ("--session-id", "--query", "--tiers-tried", "--top-hit", "--km-mode", "--vault-mode",
          "--graph-expansion"):
    p.add_argument(a)
p.add_argument("--n-hits", type=int)
p.add_argument("--km-hits", type=int)
p.add_argument("--backlinks", type=int)
p.parse_args()
with open(os.environ["FAKE_RCPT_ARGV"], "w", encoding="utf-8") as f:
    f.write("\n".join(sys.argv[1:]) + "\n")
