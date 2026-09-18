# Majlis

*Majlis*: a study assembly. A council of agents reads one personal library and works out which courses are hidden in it, then drafts the syllabus.

The premise: a serious reader accumulates real expertise in three or four odd subjects, and it stays stuck — a pile of books, a column of star ratings, a few hundred words written at midnight. Turning that into a course someone could work through takes a week of evenings per subject. Majlis does the assembly work; the reader stays the professor.

**Status: in progress.** The [PRD](docs/PRD.md) is written, the [prototype](prototype/) is clickable, the cartographer has mapped the shelf into 16 subjects, and the council has produced its first real syllabus — see [`runs/`](runs/). Still to come: the eval suite, the rest of the syllabi, and the site that replays a run.

A run costs about $0.80 and takes four minutes, so syllabi are generated offline and the site replays the recorded run rather than convening the council per visitor.

## How it's meant to work

```
              837 books, 470 unread, catalogued by subject
                              │
                       ┌──────▼───────┐
                       │ Cartographer │  which subjects can this shelf teach?
                       └──────┬───────┘  → a map, with an honest verdict each
                              │
              the professor picks a subject
                              │
                       ┌──────▼──────┐
                       │    Lead     │  split into 4–6 threads
                       └──────┬──────┘
         ┌──────────┬─────────┴────────┬──────────┐
         ▼          ▼                  ▼          ▼
     Researcher  Researcher        Researcher  Researcher   ← shelf search
         └──────────┴─────────┬────────┴──────────┘
                              ▼
                       draft syllabus
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
   Isnad (verifier)     Counter-reader          Realist
   does this book       whose account is        can a person
   really cover this?   missing from this       read this in
                        shelf?                  six weeks?
         └────────────────────┼────────────────────┘
                              ▼
                       ┌──────────────┐
                       │     Lead     │  reconcile, order, write objectives
                       └──────┬───────┘
                              ▼
        a 6–8 week syllabus, plus everything that was struck
```

Named for the *isnad*, the chain of transmission classical scholars used to decide whether a report could be trusted.

## Two rules the whole thing rests on

1. **Nothing unverified is assigned.** A researcher's "chapter 4 covers the Mahdist revolt" is a hypothesis until Isnad confirms it against the book. Unconfirmed claims are struck and shown, not softened.
2. **The professor's judgments are inputs.** A two-star book is struck with the reason shown; an abandoned book may be assigned one chapter instead of the whole thing; a five-star book with a written note anchors a unit, and the note appears in her words.

## What's here

| Path | What it is |
|---|---|
| [`docs/PRD.md`](docs/PRD.md) | The product spec: users, eval framework, guardrails, model strategy, failure modes |
| [`pipeline/cartographer.py`](pipeline/cartographer.py) | Reads the shelf, proposes subjects, assigns books, judges what each can teach |
| [`data/shelf.json`](data/shelf.json) | The library: 837 books with status, rating, review, and a catalog entry per book |
| [`data/map.json`](data/map.json) | The cartographer's output: subjects, verdicts, and what each is missing |
| [`pipeline/council.py`](pipeline/council.py) | The council: lead → researchers → Isnad → counter-reader → realist → lead |
| [`runs/`](runs/) | Real council runs: every agent's step with timing and cost, plus the syllabus it produced |
| [`prototype/project/`](prototype/project/) | The clickable prototype: the map, the council at work, a syllabus, and the refusal screen |

## The data the cartographer eats

Everything starts as a **Goodreads export** — the CSV anyone can download from Goodreads under *My Books → Import and export*. Of its 24 columns, this project uses seven: `Title`, `Author`, `Exclusive Shelf` (read / to-read / currently-reading / did-not-finish), `My Rating`, `My Review`, `Number of Pages`, `ISBN13`. `Private Notes` and custom shelf tags are dropped, and reading dates are stripped from this copy.

That alone isn't enough to find courses in a library. **Only 82 of 837 books here have a written review**, and a title tells you almost nothing: nothing in the words *Bad Company* says "private equity". So each book gets a **catalog entry** written by Claude — genres, themes, mood, a one-line description, and a few well-known similar books — from what the model reliably knows about the book. It never sees the owner's reviews; it describes the book, not the opinion. If it doesn't confidently recognize a book it must say so, and 81 of 837 came back unknown rather than guessed. (That enrichment step lives in the sibling project that produces the export; this repo consumes its output.)

A book in `data/shelf.json` after both steps:

```json
{
  "id": "218671853",
  "title": "Bad Company: Private Equity and the Death of the American Dream",
  "author": "Megan Greenwell",
  "status": "read",
  "rating": 5,
  "review": "Last week I ran into someone who mentioned they work in PE, I joked…",
  "pages": 294,
  "isbn13": "9780063299351",
  "about": {
    "genres": ["journalism", "business", "nonfiction"],
    "themes": ["private equity", "corporate extraction", "labor", "american economy", "inequality"],
    "mood": ["investigative", "infuriating"],
    "description": "Reported narratives of workers and communities whose jobs and institutions were hollowed out after private equity takeovers.",
    "similar_to": ["Bad Blood by John Carreyrou", "Nickel and Dimed by Barbara Ehrenreich", "Empire of Pain by Patrick Radden Keefe"]
  }
}
```

The owner's `status`, `rating` and `review` are the professor's voice; `about` is what makes an unread, unreviewed book findable at all.

### How the cartographer uses it

**1. Propose.** Every catalogued book is flattened to one line — `title | author | status rating | genres | themes` — and all 756 of them go into a single request. The whole library fits in one context window, so the model proposes subjects having seen everything, not a sample. It returns 10–16 candidate subjects, each defined by the themes and genres that belong to it, and is told to use only tags that actually appear in the data.

**2. Assign, in code.** Books are matched to subjects by those tags, so the counts are real and reproducible rather than another model guess. Raw tag matching is far too loose: one shared tag put *Sophie's World* in a course on the critique of technology. So each tag is **weighted by how rare it is on this shelf** — a tag on ≤15 books counts 1.0, on ≤40 counts 0.4, anything more common counts 0.15 — genres count half as much as themes, and a book needs a total of 1.0 to join. "Nakba" or "technique" carries a book in; "technology" or "resistance" barely moves it. That one change took *Technique and Attention* from 128 books to 23.

**3. Judge.** Each subject's actual books — titles, authors, statuses, ratings, descriptions — go back to the model, which returns a verdict (`course`, `unit`, `not_yet`), a description of the shape of this library's version of the subject, the holes a course would have, and any book that clearly doesn't belong. Misfiled titles are dropped from the subject.

A subject in `data/map.json`:

```json
{
  "name": "Ink and Sand: Islam and Scholarship in West Africa",
  "description": "The intellectual, spiritual, and political history of Muslim West Africa…",
  "themes": ["west africa", "islamic scholarship", "embodied knowledge", "muridiyya", "…"],
  "genres": ["african studies", "islamic studies", "primary source"],
  "why_this_library": "Ware (twice), Kane, Babou, Kimball, Ogunnaike, Diouf and Ibn Battuta form a coherent syllabus on a region usually reduced to a footnote in Islamic studies.",
  "verdict": "course",
  "shape": "Senegal-weighted and Sufi-centered, with a genuine spine: Ware's two volumes give both the embodied-pedagogy argument and a translated anthology…",
  "holes": "…",
  "misfiled": ["…"],
  "books": 8, "read": 5, "unread": 3, "abandoned": 0, "rated": 5, "reviewed": 1,
  "book_ids": ["…"]
}
```

## Running the cartographer

Python 3.11+, an Anthropic API key in `.env` (see `.env.example`).

```sh
python3 -m venv .venv && .venv/bin/pip install anthropic
.venv/bin/python pipeline/cartographer.py --dry-run   # subjects + book assignment, no model calls after the first
.venv/bin/python pipeline/cartographer.py             # full run, including the verdict on each subject
```

The expensive first pass is cached in `data/subjects_proposal.json`; `--repropose` redoes it.

## About the data

The shelf is a Goodreads export from [The Complete Shelf](https://shelf.abeerminhas.com), cleaned by a script in that project: private notes and custom shelf tags are stripped, and reading dates are removed from this copy. Each book carries a short catalog entry — genres, themes, mood, a description, similar books — written by Claude, which is what makes an unreviewed book findable at all. Ratings and reviews are Abeer's own.

One library's view of these subjects. Not a canon.
