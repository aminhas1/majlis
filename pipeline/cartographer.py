"""The cartographer: read the shelf, work out which subjects it can teach.

Three passes:
  1. Claude reads a digest of the whole shelf and proposes candidate subjects,
     each defined by the themes/genres that belong to it.
  2. Books are assigned to subjects deterministically from those definitions,
     so counts are real and reproducible.
  3. Claude sees each subject's actual books (titles, ratings, status) and
     returns a verdict — course / unit / not yet — plus what the shelf is
     strong and weak on, and any book that clearly doesn't belong.

Writes data/map.json. Costs a couple of dollars; run deliberately.

Usage: .venv/bin/python pipeline/cartographer.py [--dry-run]
"""

import argparse
import json
import os
from collections import Counter
from pathlib import Path

import anthropic

ROOT = Path(__file__).resolve().parent.parent
SHELF_PATH = ROOT / "data" / "shelf.json"
MAP_PATH = ROOT / "data" / "map.json"
PROPOSAL_PATH = ROOT / "data" / "subjects_proposal.json"  # cached pass 1
MODEL = "claude-opus-5"

MIN_BOOKS = 8  # below this a subject isn't worth a verdict
MAX_BOOKS = 60  # a subject's shelf; more than this and the verdict prompt bloats
KEEP_SCORE = 1.0  # a book needs this much evidence to join a subject

PROPOSE_SYSTEM = """You are cataloguing one person's personal library to find the courses hidden in it.

You will see every catalogued book: title, author, status, rating, and the genres and themes it was tagged with.

Propose 10-16 candidate subjects this library could teach. A good subject is:
- specific enough to be a course, not a shelf label ("Capitalism and its critics", not "Business")
- supported by books actually in this library, across several authors
- something a curious adult would want to spend six weeks on

For each subject, give the themes and genres that define it, using ONLY tags that appear in the data. These are used to select the subject's books automatically, so be precise: broad tags like "nonfiction" or "history" pull in everything and are worse than useless.

Prefer subjects where this library is unusual. Skip subjects that are only one author's books."""

PROPOSE_SCHEMA = {
    "type": "object",
    "properties": {
        "subjects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string", "description": "One sentence: what this course would be about."},
                    "themes": {"type": "array", "items": {"type": "string"}},
                    "genres": {"type": "array", "items": {"type": "string"}},
                    "why_this_library": {"type": "string", "description": "One sentence on what makes this library's version of the subject distinctive."},
                },
                "required": ["name", "description", "themes", "genres", "why_this_library"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["subjects"],
    "additionalProperties": False,
}

VERDICT_SYSTEM = """You are judging whether a personal library can actually teach a subject as a 6-8 week course.

You see the subject and every book the library holds for it, with the owner's status (read / to-read / did-not-finish) and rating.

Return:
- verdict: "course" (enough range and depth for 6-8 units), "unit" (a strong week or two, not a course), or "not_yet" (too thin, or one perspective only).
- shape: two or three sentences on what this library's version of the subject looks like — what it is strong on, in concrete terms.
- holes: what a course would be missing. Be specific: name the perspective, period, or kind of source that isn't here.
- misfiled: titles that clearly don't belong to this subject (novels swept in by a tag, books about something else). Use exact titles from the list.

Judge the books actually present, not the subject in the abstract. A library with ten books all making the same argument is "unit", not "course"."""

VERDICT_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["course", "unit", "not_yet"]},
        "shape": {"type": "string"},
        "holes": {"type": "string"},
        "misfiled": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["verdict", "shape", "holes", "misfiled"],
    "additionalProperties": False,
}


def load_env() -> None:
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())


def ask(client: anthropic.Anthropic, system: str, schema: dict, content: str, max_tokens: int = 16000) -> tuple[dict, object]:
    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        output_config={"effort": "high", "format": {"type": "json_schema", "schema": schema}},
        system=system,
        messages=[{"role": "user", "content": content}],
    )
    if response.stop_reason != "end_turn":
        raise SystemExit(f"Model stopped with {response.stop_reason}")
    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text), response.usage


def digest(books: list[dict]) -> str:
    """One compact line per catalogued book — the whole shelf fits in context."""
    lines = []
    for b in books:
        if not b["about"]:
            continue
        rating = f"{b['rating']}*" if b["rating"] else "-"
        lines.append(
            f"{b['title'][:70]} | {b['author'][:30]} | {b['status']} {rating} | "
            f"{'/'.join(b['about']['genres'])} | {'/'.join(b['about']['themes'])}"
        )
    return "\n".join(lines)


def tag_weights(books: list[dict]) -> dict[str, float]:
    """A tag shared by half the shelf ("technology") says little; a rare one says a lot."""
    counts = Counter()
    for b in books:
        if b["about"]:
            counts.update(t.lower() for t in b["about"]["themes"])
            counts.update(g.lower() for g in b["about"]["genres"])
    weights = {}
    for tag, n in counts.items():
        weights[tag] = 1.0 if n <= 15 else 0.4 if n <= 40 else 0.15
    return weights


def assign(books: list[dict], subject: dict, weights: dict[str, float]) -> list[dict]:
    themes = {t.lower() for t in subject["themes"]}
    genres = {g.lower() for g in subject["genres"]}
    scored = []
    for b in books:
        if not b["about"]:
            continue
        book_themes = {t.lower() for t in b["about"]["themes"]}
        book_genres = {g.lower() for g in b["about"]["genres"]}
        score = sum(weights.get(t, 1.0) for t in book_themes & themes)
        score += 0.5 * sum(weights.get(g, 1.0) for g in book_genres & genres)
        if score >= KEEP_SCORE:
            scored.append((score, b))
    scored.sort(key=lambda sb: (-sb[0], sb[1]["title"]))
    return [b for _, b in scored[:MAX_BOOKS]]


def book_lines(hits: list[dict]) -> str:
    out = []
    for b in sorted(hits, key=lambda x: (x["status"] != "read", -(x["rating"] or 0))):
        rating = f"{b['rating']} stars" if b["rating"] else "unrated"
        note = " [has the owner's written note]" if b["review"] else ""
        out.append(f"- {b['title']} — {b['author']} ({b['status']}, {rating}){note}: {b['about']['description']}")
    return "\n".join(out)


def counts(hits: list[dict]) -> dict:
    return {
        "books": len(hits),
        "read": sum(b["status"] == "read" for b in hits),
        "unread": sum(b["status"] == "to-read" for b in hits),
        "abandoned": sum(b["status"] == "did-not-finish" for b in hits),
        "rated": sum(b["rating"] is not None for b in hits),
        "reviewed": sum(b["review"] is not None for b in hits),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="propose subjects and assign books, but skip the verdict pass")
    parser.add_argument("--repropose", action="store_true", help="ask the model for subjects again instead of using the cached proposal")
    args = parser.parse_args()

    load_env()
    client = anthropic.Anthropic()
    books = json.loads(SHELF_PATH.read_text(encoding="utf-8"))
    spend = {"input": 0, "output": 0}

    def track(usage):
        spend["input"] += usage.input_tokens
        spend["output"] += usage.output_tokens

    if PROPOSAL_PATH.exists() and not args.repropose:
        proposal = json.loads(PROPOSAL_PATH.read_text(encoding="utf-8"))
        print(f"Using cached proposal: {len(proposal['subjects'])} subjects (--repropose to redo)")
    else:
        print(f"Reading {sum(1 for b in books if b['about'])} catalogued books…")
        proposal, usage = ask(client, PROPOSE_SYSTEM, PROPOSE_SCHEMA, "The library:\n\n" + digest(books))
        track(usage)
        PROPOSAL_PATH.write_text(json.dumps(proposal, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Proposed {len(proposal['subjects'])} subjects\n")

    weights = tag_weights(books)
    subjects = []
    for subject in proposal["subjects"]:
        hits = assign(books, subject, weights)
        print(f"  {subject['name']}: {len(hits)} books")
        if len(hits) < MIN_BOOKS:
            subjects.append({**subject, **counts(hits), "verdict": "not_yet",
                             "shape": "Too few books in this library to judge.",
                             "holes": "Almost everything.", "misfiled": [],
                             "book_ids": [b["id"] for b in hits]})
            continue
        if args.dry_run:
            subjects.append({**subject, **counts(hits), "book_ids": [b["id"] for b in hits]})
            continue
        judgment, usage = ask(
            client, VERDICT_SYSTEM, VERDICT_SCHEMA,
            f"Subject: {subject['name']}\n{subject['description']}\n\nThe library's books for it:\n{book_lines(hits)}",
        )
        track(usage)
        kept = [b for b in hits if b["title"] not in set(judgment["misfiled"])]
        subjects.append({**subject, **judgment, **counts(kept), "book_ids": [b["id"] for b in kept]})
        print(f"     → {judgment['verdict']}, {len(judgment['misfiled'])} misfiled")

    subjects.sort(key=lambda s: ({"course": 0, "unit": 1, "not_yet": 2}.get(s.get("verdict"), 3), -s["books"]))
    MAP_PATH.write_text(json.dumps({"model": MODEL, "subjects": subjects}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    cost = spend["input"] * 5 / 1e6 + spend["output"] * 25 / 1e6
    print(f"\nWrote {MAP_PATH.relative_to(ROOT)}: {len(subjects)} subjects. "
          f"{spend['input']} input + {spend['output']} output tokens, about ${cost:.2f}")


if __name__ == "__main__":
    main()
