#!/usr/bin/env python3
"""fake-receipt-old.py — stand-in receipt helper from before 1.8.5 (marker fields, no graph fields).

Used by test_search_graph_expansion.sh. An unknown argument (e.g. --backlinks) makes argparse
exit 2 — the failure the search command must avoid. Writes argv to $FAKE_RCPT_ARGV on success.
"""
import argparse
import os
import sys

p = argparse.ArgumentParser()
for a in ("--session-id", "--query", "--tiers-tried", "--top-hit", "--km-mode", "--vault-mode"):
    p.add_argument(a)
p.add_argument("--n-hits", type=int)
p.add_argument("--km-hits", type=int)
p.parse_args()
with open(os.environ["FAKE_RCPT_ARGV"], "w", encoding="utf-8") as f:
    f.write("\n".join(sys.argv[1:]) + "\n")
