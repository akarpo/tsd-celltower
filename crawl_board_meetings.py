#!/usr/bin/env python3
"""
Pull EVERY Troy School District Board of Education meeting record since
2021-01-01 and scan it for any action approving the AT&T cell tower / ground
lease on the Boulan Park Middle School parcel.

Unlike the sibling `crawl_agendas.py` (which only keeps keyword-matching items),
this crawls the *complete* agenda corpus — every item of every meeting — so the
full record is on disk and the keyword search runs locally and is re-runnable.

Reuses the reverse-engineered BoardDocs Public API client from the tsd-budget
project (`~/Downloads/tsd-budget/scripts/boarddocs_api.py`).

Outputs (next to this script):
  board_meetings_2021plus.json   -- full corpus: every meeting, every agenda item
  celltower_hits.json            -- items whose title/action match tower keywords

Run:  python3 crawl_board_meetings.py
"""
import json
import os
import re
import sys
import time

# Reuse the BoardDocs client from the tsd-budget sibling project.
sys.path.insert(0, os.path.expanduser("~/Downloads/tsd-budget/scripts"))
from boarddocs_api import get_meetings, get_agenda  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SINCE = "20210101"                       # numberdate is YYYYMMDD
DELAY = 0.35                             # polite gap between BoardDocs requests

# Tower-specific keywords. Deliberately broad — a ground lease can be agendaed
# under "lease", "easement", "license agreement", "land use", a vendor name,
# or just the site. We over-match here and review hits by hand.
KEYWORDS = [
    "cell tower", "cell site", "cellular", "monopole", "antenna", "wireless",
    "at&t", "att mobility", "at & t", "telecommunication", "telecom",
    "ground lease", "land lease", "lease agreement", " lease", "leasing",
    "easement", "right of way", "right-of-way", "license agreement",
    "boulan", "northfield", "tower",
]
KEYWORD_RE = re.compile("|".join(re.escape(k) for k in KEYWORDS), re.I)


def main():
    print("Fetching full meetings list ...", file=sys.stderr)
    all_meetings = get_meetings()
    meetings = sorted(
        (m for m in all_meetings if m.get("numberdate", "") >= SINCE),
        key=lambda m: m["numberdate"],
    )
    print(f"{len(meetings)} meetings since {SINCE[:4]}-{SINCE[4:6]}-{SINCE[6:]}",
          file=sys.stderr)

    corpus = []        # one record per meeting, with every agenda item
    hits = []          # flat list of keyword-matching items
    total_items = 0

    for i, m in enumerate(meetings):
        items = get_agenda(m["unique"])
        total_items += len(items)
        corpus.append({
            "meeting_date": m["numberdate"],
            "meeting_unique": m["unique"],
            "meeting_name": m["name"],
            "item_count": len(items),
            "items": items,
        })
        for it in items:
            text = f"{it['title']} {it['action']}"
            mo = KEYWORD_RE.search(text)
            if mo:
                hits.append({
                    "meeting_date": m["numberdate"],
                    "meeting_name": m["name"],
                    "meeting_unique": m["unique"],
                    "item_unique": it["unique"],
                    "item_title": it["title"],
                    "item_action": it["action"],
                    "has_attachment": it["has_attachment"],
                    "matched": mo.group(0),
                })
        if (i + 1) % 10 == 0 or i == len(meetings) - 1:
            print(f"  [{i+1:>3}/{len(meetings)}] {m['numberdate']} | "
                  f"{total_items} items so far, {len(hits)} keyword hits",
                  file=sys.stderr)
        time.sleep(DELAY)

    corpus_path = os.path.join(HERE, "board_meetings_2021plus.json")
    hits_path = os.path.join(HERE, "celltower_hits.json")
    with open(corpus_path, "w") as f:
        json.dump(corpus, f, indent=2)
    with open(hits_path, "w") as f:
        json.dump(hits, f, indent=2)

    empty = [c for c in corpus if c["item_count"] == 0]
    print(f"\nCrawled {len(corpus)} meetings / {total_items} agenda items.",
          file=sys.stderr)
    if empty:
        print(f"  ({len(empty)} meetings returned 0 items — typically "
              f"closed-session specials or not-yet-published agendas)",
              file=sys.stderr)
    print(f"  Full corpus -> {os.path.relpath(corpus_path)}", file=sys.stderr)
    print(f"  {len(hits)} keyword hits -> {os.path.relpath(hits_path)}",
          file=sys.stderr)

    if hits:
        print("\n=== keyword-matching agenda items ===", file=sys.stderr)
        for h in hits:
            att = " [has attachment]" if h["has_attachment"] else ""
            print(f"  {h['meeting_date']} | match='{h['matched']}' | "
                  f"{h['item_title']}{att}", file=sys.stderr)
            if h["item_action"]:
                print(f"      action: {h['item_action']}", file=sys.stderr)


if __name__ == "__main__":
    main()
