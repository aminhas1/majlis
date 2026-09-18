"""The council: turn one subject from the map into a syllabus.

The same code the site will run. Every step emits an event (agent, what it
did, how long, what it cost), printed as it happens and saved to
runs/<subject>.json so the site can replay or stream it later.

  lead        split the subject into threads
  researchers one per thread, in parallel, proposing readings from the shelf
  isnad       verify every claim; strike what it can't confirm  (web search)
  counter     whose account is missing from this shelf          (web search)
  realist     length, order, entry points
  lead        reconcile into units, objectives, and a reading order

Usage:
  .venv/bin/python pipeline/council.py "Capitalism"          # match by name
  .venv/bin/python pipeline/council.py --list
"""

import argparse
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import anthropic

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cartographer import ROOT, SHELF_PATH, load_env  # noqa: E402

MAP_PATH = ROOT / "data" / "map.json"
RUNS_DIR = ROOT / "runs"

LEAD_MODEL = "claude-opus-5"
ISNAD_MODEL = "claude-opus-5"
WORKER_MODEL = "claude-sonnet-5"
PRICES = {  # $ per million tokens (input, output)
    "claude-opus-5": (5, 25),
    "claude-sonnet-5": (2, 10),
}
WEEKS = 6
HOURS_PER_WEEK = 5
PAGES_PER_HOUR = 30

WEB_SEARCH = {"type": "web_search_20260209", "name": "web_search", "max_uses": 4}


# ---------------------------------------------------------------- plumbing

class Run:
    """Collects everything that happened, for the terminal and for the site."""

    def __init__(self, subject: dict, on_event=None):
        self.subject = subject
        self.events: list[dict] = []
        self.cost = 0.0
        self.started = time.time()
        # The local API passes a callback so the UI can watch a run as it happens.
        self.on_event = on_event

    def event(self, agent: str, kind: str, text: str, **extra) -> None:
        at = round(time.time() - self.started, 1)
        payload = {"at": at, "agent": agent, "kind": kind, "text": text, **extra}
        self.events.append(payload)
        if self.on_event:
            self.on_event({**payload, "cost_usd": round(self.cost, 3)})
        colour = {"strike": "\033[31m", "objection": "\033[33m", "done": "\033[32m"}.get(kind, "")
        print(f"  {at:6.1f}s  {colour}{agent:<12}\033[0m {text}")

    def spend(self, model: str, usage) -> None:
        rate_in, rate_out = PRICES[model]
        self.cost += usage.input_tokens * rate_in / 1e6 + usage.output_tokens * rate_out / 1e6

    def save(self, syllabus: dict) -> Path:
        RUNS_DIR.mkdir(exist_ok=True)
        slug = re.sub(r"[^a-z0-9]+", "-", self.subject["name"].lower()).strip("-")[:60]
        path = RUNS_DIR / f"{slug}.json"
        path.write_text(json.dumps({
            "subject": self.subject["name"],
            "verdict": self.subject.get("verdict"),
            "seconds": round(time.time() - self.started, 1),
            "cost_usd": round(self.cost, 3),
            "models": {"lead": LEAD_MODEL, "isnad": ISNAD_MODEL, "workers": WORKER_MODEL},
            "events": self.events,
            "syllabus": syllabus,
        }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return path


def ask(client, run: Run, model: str, system: str, content: str, schema: dict,
        tools: list | None = None, max_tokens: int = 12000) -> dict:
    """One agent turn. With tools, the model may search first, so JSON comes back in text."""
    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": content}],
        "betas": ["server-side-fallback-2026-07-01"],
        "fallbacks": "default",
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["output_config"] = {"effort": "medium"}
        kwargs["system"] += (
            "\n\nReply with JSON only, matching this schema, in a ```json fenced block:\n"
            + json.dumps(schema)
        )
    else:
        kwargs["output_config"] = {"effort": "medium", "format": {"type": "json_schema", "schema": schema}}

    response = client.beta.messages.create(**kwargs)
    run.spend(model, response.usage)
    if response.stop_reason == "refusal":
        raise SystemExit(f"Refused: {response.stop_details}")
    text = "".join(b.text for b in response.content if b.type == "text")
    match = re.search(r"```json\s*(.*?)```", text, re.S)
    return json.loads(match.group(1) if match else text)


# ---------------------------------------------------------------- the agents

LEAD_SPLIT_SYSTEM = """You are the lead of a teaching council, planning a six-week course built from one person's personal library.

You see the subject, what the library holds for it, and the holes a previous pass already found.

Split the subject into 4-6 threads: the strands a course would need, in a defensible teaching order. Each thread is a question or move, not a label ("How the machine is supposed to work", not "Economics").

Ground every thread in books that are actually here. If a necessary thread has no support in this library, include it anyway and set needs_outside true — the council will name the gap rather than pretend."""

LEAD_SPLIT_SCHEMA = {
    "type": "object",
    "properties": {
        "course_title": {"type": "string"},
        "description": {"type": "string", "description": "Two sentences on what this course does, in the professor's register."},
        "threads": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "focus": {"type": "string", "description": "What this thread must establish, in one sentence."},
                    "needs_outside": {"type": "boolean"},
                },
                "required": ["title", "focus", "needs_outside"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["course_title", "description", "threads"],
    "additionalProperties": False,
}

RESEARCHER_SYSTEM = """You are a researcher on a teaching council. You have one thread of a course, the professor's own library, and the web.

Propose 3-4 readings for your thread — the best ones for teaching it, wherever they come from.

The professor's shelf is a strong signal, not a boundary:
- A book she rated 4-5 stars, especially one she wrote a note about, is a recommendation from someone who has read it. Prefer it where it fits.
- A book she rated 1-2 stars needs a real justification; say why nothing else will do.
- A book she abandoned may be assigned in part, never whole.
- Where the shelf has nothing good for this thread, search for what a real course would assign. Outside readings are normal, not a failure — but they must be obtainable without a university library (in print, open access, common in public libraries, public domain), and you must say where to get one.

For each reading give: the book, what part to assign (a named chapter or section where you can), what you are claiming that part covers, why it belongs here, and an honest page estimate. A verifier checks every claim, and a wrong claim is worse than a vague one.

Aim for a mix: at least one reading from the professor's shelf per thread where the shelf allows it."""

RESEARCHER_SCHEMA = {
    "type": "object",
    "properties": {
        "readings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "book_id": {"type": "string", "description": "The shelf id in [brackets], or \"outside\" for a book that isn't on the shelf."},
                    "title": {"type": "string"},
                    "author": {"type": "string"},
                    "assign": {"type": "string", "description": "e.g. 'Chapters 1-3' or 'Whole book'"},
                    "claim": {"type": "string", "description": "What this part of the book covers. The verifier checks this."},
                    "why": {"type": "string"},
                    "pages": {"type": "integer"},
                    "where_to_get": {"type": "string", "description": "For outside readings only: how a person without a university gets it."},
                },
                "required": ["book_id", "title", "author", "assign", "claim", "why", "pages", "where_to_get"],
                "additionalProperties": False,
            },
        },
        "gap": {"type": "string", "description": "Empty unless the library can't support this thread."},
    },
    "required": ["readings", "gap"],
    "additionalProperties": False,
}

ISNAD_SYSTEM = """You are Isnad, the verifier on a teaching council, named for the chain of transmission classical scholars used to decide whether a report could be trusted.

For each proposed reading you get a book and a claim about what it covers. Decide whether the claim is true of that book. Search the web when you are not certain — for the book's table of contents, chapter titles, or a description of its argument.

Verdicts:
- "confirmed": the book covers this, and the named part is plausible for it.
- "unconfirmed": the claim is wrong, the chapter doesn't exist, or you cannot establish it.
- "narrowed": the book covers the subject but the named part is wrong; give the correct part in `correction`.

For a reading that is NOT on the professor's shelf, also check that the book exists as described and can be obtained without a university library. If it can't, mark it unconfirmed and say so.

Be strict. An unconfirmed claim is struck from the syllabus, which is the right outcome. Never confirm something to be helpful."""

ISNAD_SCHEMA = {
    "type": "object",
    "properties": {
        "verdicts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "ref": {"type": "string", "description": "The [ref] of the proposal being judged."},
                    "verdict": {"type": "string", "enum": ["confirmed", "unconfirmed", "narrowed"]},
                    "reason": {"type": "string"},
                    "correction": {"type": "string"},
                },
                "required": ["ref", "verdict", "reason", "correction"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["verdicts"],
    "additionalProperties": False,
}

COUNTER_SYSTEM = """You are the counter-reader on a teaching council. Your mandate is the library's blind spots, not the world's.

You see the draft readings. Ask: whose account of this subject is doing the talking, and whose is missing? Name the specific perspective, period, or kind of source that isn't here — the way a good external examiner would.

Then propose at most one outside reading that would close the most important gap. It must exist, and it must be obtainable without a university library: in print, open access, common in public libraries, or public domain. Search to confirm both.

If the draft is genuinely balanced, say so and propose nothing. An objection nobody acts on is worse than no objection."""

COUNTER_SCHEMA = {
    "type": "object",
    "properties": {
        "objection": {"type": "string"},
        "addition": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "author": {"type": "string"},
                "assign": {"type": "string"},
                "why": {"type": "string"},
                "where_to_get": {"type": "string"},
                "pages": {"type": "integer"},
            },
            "required": ["title", "author", "assign", "why", "where_to_get", "pages"],
            "additionalProperties": False,
        },
        "balanced": {"type": "boolean", "description": "True if no addition is needed."},
    },
    "required": ["objection", "addition", "balanced"],
    "additionalProperties": False,
}

REALIST_SYSTEM = """You are the realist on a teaching council. You care about whether a person with a job can actually do this course.

The budget is {weeks} weeks at about {hours} hours a week — roughly {pages} pages a week at reading speed.

Given the confirmed readings and their page counts, say: which readings to cut, which to trim to a smaller part, what order the units should go in, and which single reading is the right entry point for someone who knows nothing.

Cut rather than compress: a week with two readings someone finishes beats four they abandon."""

REALIST_SCHEMA = {
    "type": "object",
    "properties": {
        "cuts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "ref": {"type": "string", "description": "The [ref] of the reading."},
                    "action": {"type": "string", "enum": ["cut", "trim"]},
                    "reason": {"type": "string"},
                    "trim_to": {"type": "string"},
                },
                "required": ["ref", "action", "reason", "trim_to"],
                "additionalProperties": False,
            },
        },
        "entry_point": {"type": "string", "description": "Title of the reading to start with, and why."},
        "verdict": {"type": "string", "description": "One sentence on whether the workload is honest."},
    },
    "required": ["cuts", "entry_point", "verdict"],
    "additionalProperties": False,
}

RECONCILE_SYSTEM = """You are the lead of the teaching council, writing the final syllabus.

You have the threads, the readings that survived verification, the verifier's corrections, the counter-reader's objection and proposed addition, and the realist's cuts and ordering.

Write {weeks} units. Each unit: a title, 2-3 learning objectives (what a reader should be able to argue afterwards), its readings, and one note on where the sources disagree — a real debate with positions named, or an honest "these sources mostly agree, and here is what that hides".

Rules:
- Only use readings given to you. Never add a book.
- Honour the realist's cuts and the verifier's corrections.
- If the counter-reader's addition was accepted, give it a unit slot and mark it as not from the shelf.
- The professor's notes are given to you separately, under "THE PROFESSOR'S OWN NOTES". For a reading that has one, copy her words verbatim into `professors_note` — never paraphrase, never summarise, and never write one yourself. For every other reading, `professors_note` MUST be empty. A book's catalogue description is not her note; using it there is a fabrication and will be caught.
- If there isn't enough material for {weeks} units, write fewer and say why in `shortfall`."""

RECONCILE_SCHEMA = {
    "type": "object",
    "properties": {
        "course_title": {"type": "string"},
        "description": {"type": "string"},
        "units": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "week": {"type": "integer"},
                    "title": {"type": "string"},
                    "objectives": {"type": "array", "items": {"type": "string"}},
                    "readings": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ref": {"type": "string", "description": "The [ref] of the confirmed reading."},
                                "book_id": {"type": "string"},
                                "title": {"type": "string"},
                                "author": {"type": "string"},
                                "assign": {"type": "string"},
                                "pages": {"type": "integer"},
                                "from_shelf": {"type": "boolean"},
                                "professors_note": {"type": "string", "description": "Her own words, verbatim, or empty."},
                            },
                            "required": ["ref", "book_id", "title", "author", "assign", "pages", "from_shelf", "professors_note"],
                            "additionalProperties": False,
                        },
                    },
                    "disagreement": {"type": "string"},
                },
                "required": ["week", "title", "objectives", "readings", "disagreement"],
                "additionalProperties": False,
            },
        },
        "shortfall": {"type": "string"},
    },
    "required": ["course_title", "description", "units", "shortfall"],
    "additionalProperties": False,
}


# ---------------------------------------------------------------- the run

def book_line(b: dict, full: bool = False) -> str:
    rating = f"{b['rating']} stars" if b["rating"] else "unrated"
    line = f"[{b['id']}] {b['title']} — {b['author']} ({b['status']}, {rating}, {b['pages'] or '?'}pp)"
    if b["about"]:
        line += f"\n    {b['about']['description']}"
        if full:
            line += f"\n    themes: {', '.join(b['about']['themes'])}"
    if b["review"]:
        note = b["review"] if full else b["review"][:200]
        line += f"\n    PROFESSOR'S NOTE: {note}"
    return line


def notes_block(kept: list[dict], books: dict) -> str:
    out = []
    for p in kept:
        book = books.get(p["book_id"])
        if book and book.get("review"):
            out.append(f"[{p['ref']}] {book['title']} — she wrote:\n\"{book['review']}\"")
    return "\n\n".join(out)


def check_notes(syllabus: dict, books: dict, run: Run) -> None:
    """A quoted note must be her actual words. Anything else is a fabrication; blank it."""
    for unit in syllabus["units"]:
        for r in unit["readings"]:
            note = (r.get("professors_note") or "").strip().strip('"')
            if not note:
                continue
            review = (books.get(r.get("book_id"), {}) or {}).get("review") or ""
            normalise = lambda t: " ".join(t.lower().split())
            if not review or normalise(note[:120]) not in normalise(review):
                run.event("audit", "strike", f"note on {r['title'][:40]} was not the professor's words — removed")
                r["professors_note"] = ""


def audit_trail(syllabus: dict, kept: list[dict], real: dict, run: Run) -> list[dict]:
    """Every confirmed reading either ships or has a recorded reason for not shipping."""
    shipped = {r.get("ref") for unit in syllabus["units"] for r in unit["readings"]}
    cuts = {c["ref"]: c for c in real["cuts"] if c["action"] == "cut"}
    dropped = []
    for p in kept:
        if p["ref"] in shipped:
            continue
        cut = cuts.get(p["ref"])
        reason = cut["reason"] if cut else "Dropped by the lead while reconciling, without a stated reason."
        by = "Realist" if cut else "Lead"
        dropped.append({**p, "struck_by": by, "reason": reason})
        if not cut:
            run.event("audit", "strike", f"{p['title'][:44]} vanished with no reason given")
    return dropped


def council(client, run: Run, books: dict) -> dict:
    subject, shelf = run.subject, [books[i] for i in run.subject["book_ids"] if i in books]
    catalogue = "\n".join(book_line(b, full=True) for b in shelf)

    plan = ask(client, run, LEAD_MODEL, LEAD_SPLIT_SYSTEM,
               f"Subject: {subject['name']}\n{subject['description']}\n\n"
               f"What this library holds: {subject.get('shape', '')}\n"
               f"Known holes: {subject.get('holes', '')}\n\nThe books:\n{catalogue}",
               LEAD_SPLIT_SCHEMA)
    run.event("lead", "plan", f"\"{plan['course_title']}\" — {len(plan['threads'])} threads: "
              + "; ".join(t["title"] for t in plan["threads"]))

    def research(thread: dict) -> tuple[dict, dict]:
        out = ask(client, run, WORKER_MODEL, RESEARCHER_SYSTEM,
                  f"Thread: {thread['title']}\nIt must establish: {thread['focus']}\n\n"
                  f"The professor's shelf for this subject (her ratings are recommendations):\n{catalogue}",
                  RESEARCHER_SCHEMA, tools=[WEB_SEARCH])
        return thread, out

    with ThreadPoolExecutor(max_workers=len(plan["threads"])) as pool:
        results = list(pool.map(research, plan["threads"]))

    proposals = []
    for thread, out in results:
        for r in out["readings"]:
            proposals.append({**r, "thread": thread["title"], "ref": f"r{len(proposals) + 1}"})
        run.event("researcher", "propose",
                  f"{thread['title']}: " + (", ".join(f"{r['title'][:34]} ({r['assign']})" for r in out["readings"]) or "nothing on the shelf"),
                  thread=thread["title"], count=len(out["readings"]))
        if out["gap"]:
            run.event("researcher", "gap", f"{thread['title']}: {out['gap']}", thread=thread["title"])

    claims = "\n".join(
        f"[{p['ref']}] {p['title']} — {p.get('author', '')} "
        f"({'on the shelf' if p['book_id'] != 'outside' else 'NOT on the shelf: ' + (p.get('where_to_get') or 'no source given')}). "
        f"Assigning {p['assign']}. Claim: {p['claim']}" for p in proposals)
    checked = ask(client, run, ISNAD_MODEL, ISNAD_SYSTEM,
                  f"Verify these proposed assignments:\n{claims}", ISNAD_SCHEMA, tools=[WEB_SEARCH])

    verdicts = {v["ref"]: v for v in checked["verdicts"]}
    kept, struck = [], []
    for p in proposals:
        v = verdicts.get(p["ref"], {"verdict": "unconfirmed", "reason": "Isnad returned no verdict for this reading.", "correction": ""})
        if v["verdict"] == "unconfirmed":
            struck.append({**p, "struck_by": "Isnad", "reason": v["reason"]})
            run.event("isnad", "strike", f"{p['title'][:44]} — {v['reason'][:110]}")
        else:
            if v["verdict"] == "narrowed" and v["correction"]:
                run.event("isnad", "narrow", f"{p['title'][:44]} → {v['correction'][:80]}")
                p = {**p, "assign": v["correction"]}
            kept.append(p)
    run.event("isnad", "done", f"{len(kept)} confirmed, {len(struck)} struck",
              confirmed=len(kept), struck=len(struck))

    def source_of(p: dict) -> str:
        if p["book_id"] != "outside":
            return "professor's shelf"
        return "not on the shelf — " + (p.get("where_to_get") or "no source given")

    draft = "\n".join(
        f"- [{p['ref']}] {p['title']} — {p.get('author', '')}, {p['assign']}, ~{p['pages']}pp "
        f"({p['thread']}; {source_of(p)}): {p['claim']}"
        for p in kept)

    def counter_reader():
        return ask(client, run, WORKER_MODEL, COUNTER_SYSTEM,
                   f"Subject: {subject['name']}\n\nThe draft readings:\n{draft}\n\n"
                   f"The whole library for this subject:\n{catalogue}",
                   COUNTER_SCHEMA, tools=[WEB_SEARCH])

    def realist():
        return ask(client, run, WORKER_MODEL,
                   REALIST_SYSTEM.format(weeks=WEEKS, hours=HOURS_PER_WEEK, pages=HOURS_PER_WEEK * PAGES_PER_HOUR),
                   f"Confirmed readings:\n" + "\n".join(
                       f"- [{p['ref']}] {p['title']} — {p['assign']}, ~{p['pages']}pp ({p['thread']})" for p in kept),
                   REALIST_SCHEMA)

    with ThreadPoolExecutor(max_workers=2) as pool:
        counter_future, realist_future = pool.submit(counter_reader), pool.submit(realist)
        counter, real = counter_future.result(), realist_future.result()

    run.event("counter", "objection", counter["objection"][:160])
    if not counter["balanced"]:
        run.event("counter", "addition", f"proposes {counter['addition']['title']} — {counter['addition']['where_to_get'][:60]}")
    by_ref = {p["ref"]: p for p in kept}
    for c in real["cuts"]:
        title = by_ref.get(c["ref"], {}).get("title", c["ref"])
        run.event("realist", "cut", f"{c['action']} {title[:38]}: {c['reason'][:90]}")
    run.event("realist", "verdict", real["verdict"][:140])

    syllabus = ask(client, run, LEAD_MODEL,
                   RECONCILE_SYSTEM.format(weeks=WEEKS),
                   f"Subject: {subject['name']}\nWorking title: {plan['course_title']}\n\n"
                   f"Threads:\n" + "\n".join(f"- {t['title']}: {t['focus']}" for t in plan["threads"]) +
                   f"\n\nConfirmed readings:\n{draft}\n\n"
                   f"Counter-reader's objection: {counter['objection']}\n"
                   f"Proposed addition: {json.dumps(counter['addition']) if not counter['balanced'] else 'none'}\n\n"
                   f"Realist — entry point: {real['entry_point']}; cuts: {json.dumps(real['cuts'])}\n\n"
                   f"THE PROFESSOR'S OWN NOTES (verbatim; the only text allowed in professors_note):\n"
                   + (notes_block(kept, books) or "(none of the confirmed readings has a note from her)"),
                   RECONCILE_SCHEMA, max_tokens=16000)
    run.event("lead", "done", f"{len(syllabus['units'])} units" + (f" — {syllabus['shortfall']}" if syllabus["shortfall"] else ""))

    check_notes(syllabus, books, run)
    syllabus["struck"] = struck + audit_trail(syllabus, kept, real, run)
    syllabus["objection"] = counter["objection"]
    syllabus["realist_verdict"] = real["verdict"]
    run.event("audit", "done",
              f"{sum(len(u['readings']) for u in syllabus['units'])} readings shipped, "
              f"{len(syllabus['struck'])} accounted for as struck or cut")
    return syllabus


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("subject", nargs="?", help="part of a subject name from the map")
    parser.add_argument("--list", action="store_true", help="show the subjects on the map")
    args = parser.parse_args()

    subjects = json.loads(MAP_PATH.read_text(encoding="utf-8"))["subjects"]
    if args.list or not args.subject:
        for s in subjects:
            print(f"  {s.get('verdict', '?'):9} {s['books']:3} books  {s['name']}")
        return

    matches = [s for s in subjects if args.subject.lower() in s["name"].lower()]
    if not matches:
        raise SystemExit(f"No subject matching {args.subject!r}. Try --list.")
    subject = matches[0]

    load_env()
    client = anthropic.Anthropic()
    books = {b["id"]: b for b in json.loads(SHELF_PATH.read_text(encoding="utf-8"))}

    print(f"\n\033[1m{subject['name']}\033[0m — {subject['books']} books, {subject['read']} read, "
          f"the map says {subject.get('verdict')}\n")
    run = Run(subject)
    syllabus = council(client, run, books)
    path = run.save(syllabus)

    print(f"\n\033[1m{syllabus['course_title']}\033[0m")
    print(f"{syllabus['description']}\n")
    for unit in syllabus["units"]:
        print(f"\033[1mWeek {unit['week']} — {unit['title']}\033[0m")
        for o in unit["objectives"]:
            print(f"    · {o}")
        for r in unit["readings"]:
            tag = "" if r["from_shelf"] else "  [not on the shelf]"
            print(f"    {r['title']} — {r['assign']} (~{r['pages']}pp){tag}")
            if r["professors_note"]:
                print(f"        note: \"{r['professors_note'][:150]}\"")
        print(f"    disagreement: {unit['disagreement'][:200]}\n")

    print(f"Struck: {len(syllabus['struck'])}")
    for s in syllabus["struck"]:
        print(f"    {s['title'][:50]} — {s['reason'][:100]}")
    print(f"\n{time.time() - run.started:.0f}s, ${run.cost:.2f} · saved {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
