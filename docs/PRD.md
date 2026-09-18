# Majlis — AI PRD

*Majlis*: a study assembly. Your bookshelf already contains a dozen courses. A council of agents finds them, argues about them, and writes the syllabus.

**Status:** draft · **Owner:** Abeer Minhas · **Last updated:** 2026-09-18
**Structure:** strategic foundation → AI-specific requirements → operations. Numbers in §6–§11 are targets to design against, not results; measured values land in `docs/EVAL_RESULTS.md`.

**Scope note — v1 is precomputed.** The shelf is analyzed once, and syllabi are generated once, offline. The site serves the map, the finished syllabi, and a replayable recording of the council run that produced each one. Nothing runs when a visitor arrives: no wait, no cost, no abuse surface. Live runs on a visitor's own subject are v2 (§21), and the architecture is built so the same council code serves both.

---

# Tier 1 — Strategic foundation

## 1. Executive summary

Say you've spent fifteen years reading in corners nobody assigns: West African Sufi scholarship, the private equity takeover of American towns, who gets to tell a war's story. Nobody handed you a curriculum for any of it; you assembled one by accident, one book at a time, and it's sitting on your shelves and in a Goodreads export. You could teach a short course on four or five of these subjects. You'd be good at it. You will almost certainly never do it, because writing one syllabus — deciding the order, picking the chapters, admitting what you're missing — is a week of evenings, and you have five subjects and no weeks.

Majlis is the teaching assistant for that problem. It reads the library, tells the professor which subjects it can actually carry, and drafts the syllabus: 6–8 weekly units, objectives, specific chapters, and where the sources disagree — built from books already on the shelf, reaching outside it only for a gap it can name. A council of agents does the work in the open, and strikes anything it can't confirm.

The professor stays the professor. Her ratings, her abandoned books, her two-star verdicts and her review notes shape what gets assigned, and appear in the syllabus in her own words. The machine does the week of evenings.

## 2. Problem

**The knowledge exists and stays stuck.** A serious reader accumulates something like expertise in three or four odd subjects. It lives as a pile of books, a column of star ratings, and a few hundred words of opinion written at midnight. Turning that into something another person could learn from means sequencing it, choosing what to skip, and being honest about the holes — and that work is slow enough that it doesn't happen. The unread half of the shelf makes it worse: 470 books bought with intent, never turned into anything.

**The obvious shortcut doesn't work.** Ask a chatbot for a syllabus and you get a plausible one in seconds: books that don't exist, chapters that don't say what it claims, paywalled articles, no order, and no relationship to the books you already own and have opinions about. It doesn't know you gave that one two stars, or that you abandoned this one on page 200 and were right to.

**So the job is acceleration, not replacement.** The professor's taste, ratings and notes are the input that makes the output worth reading; the slow assembly work is what gets handed off.

## 3. Users

| User | Job to be done | Needs |
|---|---|---|
| **The professor** (primary; today, Abeer) | "I've read enough to teach this. Draft the syllabus I don't have the evenings to write." | A first draft good enough to argue with: right subjects, right order, real chapters, honest about gaps — with her own judgments carried through |
| **Hiring manager on Abeer's portfolio** (primary) | "Can this person design and reason about a multi-agent system, or only talk about one?" | To understand it in five seconds, see the council work, and poke at it |
| **A visitor who reads** (secondary) | "What would this person's library teach me?" | Something browsable and opinionated, with no setup |

Designed for the professor, instrumented for the hiring manager. Where they conflict: the professor wins on output quality, the hiring manager wins on transparency.

**The professor is a role, not a person.** Today it's filled by Abeer and her export. The data the role needs — books, ratings, optional reviews, read/unread/abandoned — is exactly what any Goodreads export contains, so someone else's library could fill it later (§20). Nothing in v1 should assume the professor is Abeer.

## 4. Product concept

**Phase 1 — the map (precomputed, free, instant).** A cartographer pass clusters the shelf by subject and judges what each cluster could support: a full course, a short unit, or nothing yet. This is the answer to "which of my subjects am I actually qualified to teach from what I own?" The landing page is that map: *Sufism and Islamic thought (89 books) · Capitalism and its critics (62) · Colonialism and empire (60) · Grief, trauma and healing (34) · Women, patriarchy and the body (31) · Palestine (8, not yet)*, each with a verdict on whether the shelf can carry it.

**Phase 2 — the council (run offline, replayed on click).** Each subject's syllabus is produced by a council run that is recorded step by step: threads opening, researchers reporting, Isnad striking claims it can't confirm, the counter-reader naming what the shelf is missing, the realist reordering. Choosing a subject replays that recording at readable speed — the visitor watches the argument that produced their syllabus, and can skip to the result. Replay is free and instant; the run behind it was real.

**Phase 3 — the syllabus.** Units with objectives, assigned chapters from books on the shelf with estimated reading time, where the sources disagree, and — where the shelf falls short — a named gap with at most one outside addition per unit, labeled and linked to somewhere it can be obtained for free or cheaply. Where the professor has written about a book, her note appears under the assignment, in her words and attributed to her; where she abandoned one or rated it low, that verdict shapes what gets assigned and how much of it.

**The professor's judgments are inputs, not decoration:** a two-star book is struck rather than assigned, an abandoned book may be assigned one chapter instead of the whole thing, and a five-star book with a note is a natural anchor for a unit.

**The refusal is a feature.** "Your shelf covers four of six units; the hole is the economics" is a better answer than a padded syllabus, and the map says so before you click.

## 5. Goals and non-goals

**Goals**
- Turn a personal library into a browsable map of what it can teach.
- Build genuine 6–8 week syllabi from the shelf, with specific chapters, not book titles.
- Never claim a book covers something it doesn't.
- Name gaps instead of hiding them; keep outside additions rare, justified, and obtainable without a university library.
- Show the council's reasoning, including what it threw away.
- Prove the multi-agent design earns its cost.

**Non-goals**
- Not a book recommender — that's the Sultan (librarian.abeerminhas.com).
- Not a general research agent; the shelf is the corpus.
- No assignments, essays, or grading.
- No accounts, no uploads in v1 (the shelf is Abeer's; other people's libraries are a later question).

## 6. Success metrics

| Dimension | Metric | Target |
|---|---|---|
| Fidelity | Assigned chapters that exist and cover what the syllabus claims | 100% shipped; ≥95% caught before shipping |
| Constraint | Assigned readings that come from the shelf | ≥80% per syllabus |
| Voice | Units anchored on a book the professor rated or reviewed | ≥60% |
| Acceleration | Professor's verdict on a first draft: "worth arguing with" rather than "start over" | ≥4 of 5 subjects |
| Honesty | Subjects where the shelf is thin and the council says so instead of padding | 100% |
| Access | Outside additions obtainable without a university library | 100% |
| Usefulness | Units whose estimated workload fits the stated weekly budget | ≥90% |
| Architecture | Planted flaws caught by the council vs. a single reviewer agent | Council ahead by a margin that justifies its cost |
| Demo | Time to understand the map / to reach a finished syllabus | ~5s / one click, instant |
| Cost | Cost per visit (v1) | zero — everything is precomputed |
| Cost | Cost of a full rebuild (map + all syllabi) | a few dollars, run deliberately |

## 7. Competitive context

| | What it gives you | What it doesn't |
|---|---|---|
| Chatbot, asked directly | A plausible reading list in seconds | No verification, no chapters, no order, and no relationship to books you own |
| Deep-research modes | A long cited report | A report, not a course; ignores your shelf entirely |
| Goodreads shelves and tags | What you own, sorted | No structure, no curriculum, no sense of what's teachable |
| MOOCs, Open Syllabus | Real courses | Only where a course exists; assumes library access; not built from your books |

The wedge: **your own library, read as a curriculum**, with the checking shown rather than claimed.

---

# Tier 2 — AI-specific requirements

## 8. The council

**Offline pass (rebuilt when the shelf changes):**

| Agent | Mandate | Tools |
|---|---|---|
| **Cartographer** | Cluster the shelf into candidate subjects; name each; judge whether it can support a course, a unit, or nothing yet; describe the shape of what's there | shelf data |

The council is convened by **Hudhud**, the assistant the professor sees — the hoopoe who carries word between courts in the story of Sulayman. Hudhud is the name on the page; the agents below are its members.

**On a click:**

| Agent | Mandate | Tools | Runs |
|---|---|---|---|
| **Lead** | Split the subject into 4–6 threads; later reconcile objections, order units, write objectives | shelf search | twice |
| **Researcher** (one per thread) | Find shelf books for its thread; propose specific chapters with a reason; name a gap when the shelf can't cover the thread | shelf search, book-structure lookup | parallel |
| **Isnad** (verifier) | Does this book really cover this? Does that chapter exist? Strike what can't be confirmed. For outside additions: does it exist, and can a person without a university get it? | Open Library, web search | parallel |
| **Counter-reader** | Whose account is missing *from this shelf*? Name the blind spot, and where an outside addition is worth its slot | shelf search, web search | parallel |
| **Realist** | Length, difficulty, sequence, entry points; is this doable in the stated weeks? | shelf data | parallel |

Named for the *isnad*, the chain of transmission classical scholars used to judge whether a report could be trusted.

**Why a council and not one agent:** the reviewers' mandates conflict — fidelity against breadth against feasibility. One agent told to weigh all three blends them. A hypothesis to measure (§10), not a claim for the page.

**The lead may decline to convene.** Subjects the map marks as thin get a short honest answer, not a fan-out.

## 9. Source and assignment rules

- **The shelf is the corpus.** Every book on it is fair game: read, unread, abandoned.
- **The professor's judgments steer the syllabus**, and are the one input no other tool has:
  - a 4–5 star book with a written note is a natural anchor for a unit;
  - a 1–2 star book is struck unless nothing else covers the thread, and the reason is shown;
  - an abandoned book may be assigned in part (one chapter) rather than whole, citing her verdict;
  - her note appears under the assignment, in her words, attributed to her — never rewritten, never presented as scholarship, and never invented where she wrote nothing.
- **Reviews are optional.** Most books have a rating and no note; the syllabus must read well with ratings alone.
- **Assign parts, not books:** a chapter or section, with estimated reading time.
- **Chapter claims must be verified.** A researcher's "chapter 4 covers the Mahdist revolt" is a hypothesis until Isnad confirms it. Unconfirmed claims are struck, not softened. Where a book's structure can't be established, it may still be assigned as a whole-book reading, marked as such.
- **Outside additions:** at most one per unit, only against a named gap, and only if obtainable without a university library (open access, in print, common in public libraries, freely streamable, public domain). Labeled "not on the shelf" with a link.
- **Nothing unverified ships.** Struck items appear in the visible scrap heap with the reason.

## 10. Eval framework

Two suites, both re-runnable from the repo.

**Suite A — planted flaws.** Draft syllabi seeded with known defects, run through (a) one reviewer agent asked to check everything, (b) the full council.

| Flaw | Should be caught by | Pass threshold |
|---|---|---|
| Shelf book assigned for a subject it doesn't cover | Isnad | ≥95% |
| Chapter number or title that doesn't exist in that book | Isnad | ≥90% |
| Outside addition that doesn't exist, or wrong author | Isnad | ≥95% |
| Outside addition that's paywalled with a free alternative available | Isnad | ≥80% |
| Subject carried entirely by one perspective the shelf happens to over-represent | Counter-reader | ≥80% |
| 4,000 pages presented as six weeks | Realist | ≥90% |
| Three readings making the same argument | Realist / Lead | ≥70% |
| **Clean syllabus** | nobody | false strikes ≤5% |

**Suite B — end-to-end.** A fixed set of subjects drawn from the map, from well-covered (Sufism, colonialism) to deliberately thin (artificial intelligence, grief), plus one the shelf can't support at all.

| Dimension | Measure | Pass |
|---|---|---|
| Chapter fidelity | assigned chapters exist and cover the claim (hand-checked) | 100% |
| Shelf share | readings drawn from the shelf | ≥80% |
| Gap honesty | thin subjects produce a named gap rather than padding | 100% |
| Sequence | a reader could follow unit order without gaps | ≥90% of units |
| Workload honesty | estimated vs. actual pages | within 25% |
| Disagreement note | names a real debate, not a platitude | ≥80% of units |

**Suite C — the map.** Does the cartographer's verdict match reality? For each subject it calls teachable, does the council in fact produce a syllabus meeting Suite B? For each it calls thin, does a forced run confirm it?

**Tracked every run:** wall-clock, cost, tokens per agent, searches, strike rate and reasons, shelf share, gaps named.

## 11. Guardrails specification

**Input filtering**
- The map's subjects are the primary input; free-text subjects are capped in length and matched against the shelf before any agent runs.
- Subjects the shelf can't support get an honest refusal, not a syllabus.
- Instructions found in fetched web pages are data, never commands.

**Output validation**
- No reading reaches a unit without a fidelity check (does this book cover this?) and, for outside additions, an existence and access check.
- Every reading carries: source (shelf / addition), chapter or section, estimated time, and for additions, where to get it.
- Unit workload must fit the weekly budget or the realist sends it back once; after that it ships with a visible warning.
- Scholarly positions are attributed to named sources; no invented quotes.
- Abeer's reviews may be quoted as Abeer's opinion, never as the council's judgment or as scholarship.

**Action boundaries**
- The council reads the shelf and the web; it never posts, buys, emails, or downloads files.
- Search calls capped per researcher per run.
- No visitor data stored; questions aren't retained after a run.

**Escalation and confidence**
- Isnad returns confirmed / unconfirmed / uncertain; uncertain is treated as unconfirmed.
- A thread with fewer than two confirmed readings is merged, dropped, or turned into a named gap.
- Fewer than four surviving units ships a short syllabus that says why.
- Agent error or timeout ships the syllabus without that pass, labeled.

**Rate and spend**
- v1 runs nothing for visitors, so there is no per-visit spend or abuse surface. Generation happens offline, under Abeer's hand, with a per-rebuild budget.
- v2 adds: per-visitor run cap per day, hard daily spend cap, and the precomputed map and syllabi as the always-available fallback when the cap is hit.

## 12. Model strategy

| Role | Starting choice | Rationale | Upgrade / fallback |
|---|---|---|---|
| Cartographer (offline) | Claude Opus 5 | Runs rarely, shapes everything downstream | — |
| Lead | Claude Opus 5 | Hardest judgment: structure, conflict resolution, ordering | Sonnet 5 on overload |
| Researcher | Claude Sonnet 5 | Highest volume, cost driver; retrieval and summarizing | Measured against Opus 5 in Suite B before fixing |
| Isnad | Claude Opus 5 | The guardrail the product's credibility rests on | — |
| Counter-reader / Realist | Claude Sonnet 5 | Narrow mandates, short outputs | Promote if Suite A shows misses |
| LLM judge (offline) | Claude Opus 5 | At least as strong as the system judged; agreement with hand checks reported | — |

Model choice is a measured tradeoff. First experiment: Sonnet vs. Opus researchers on Suite B, reported as quality against dollars. Model IDs pinned in config; no silent upgrades. On a new model release, both suites run against pinned and candidate, and the decision is recorded.

## 13. Data requirements

| Data | Source | Handling |
|---|---|---|
| The shelf (837 books: title, author, status, rating, review, and a Claude-written catalog entry) | `shelf-librarian` repo | Committed copy, refreshed deliberately; private notes and shelf tags already stripped upstream |
| Subject map | Cartographer output | Committed; rebuilt when the shelf changes |
| Book structure (tables of contents, chapter titles) | Open Library, web search | Cached per book; the cache is what makes chapter-level assignment affordable |
| Outside additions: existence, edition, obtainability | Open Library, open-access registries, web search | Cached with the item |
| Cached syllabi | Council runs | Committed with the date and model IDs that produced them |
| Eval sets | Hand-built | Versioned so numbers stay comparable |
| Visitor questions | — | Not stored, not logged with identifiers |

No training, no fine-tuning. Aggregate counters only.

## 14. Responsible AI

- **A library is an argument.** Reading a shelf as a curriculum makes its biases visible, which is why the counter-reader's mandate is aimed at the shelf itself, not at the world. It's judged on whether it changes the syllabus, not on whether it produces commentary.
- **It's one person's library.** The page says so plainly: this is a defensible path through what Abeer happens to own, not a canon.
- **Access as fairness.** Outside additions must be obtainable without a university, or they're struck.
- **Transparency.** The scrap heap is public; so is the map's verdict on thin subjects.
- **Abeer's reviews** appear as personal opinion, attributed, never as scholarship.
- **Regulatory.** No profiling, no automated decisions about people, no sensitive data. Minimal-risk tier under the EU AI Act; the applicable obligation is disclosing that the content is AI-generated, which the page does prominently.

---

# Tier 3 — Operations

## 15. User stories (with quality clauses)

- As the shelf's owner, I want to see what my library can teach, **where every subject on the map is backed by books I actually own and labeled honestly as a course, a unit, or not yet**.
- As the shelf's owner, I want a six-week course from books in my house, **where every assigned chapter exists and covers what the syllabus says it covers, and where anything I'd have to buy is one item per unit, justified by a named gap, and obtainable for free or cheaply**.
- As the shelf's owner, I want to be told when my shelf isn't enough, **where the council names the gap instead of padding the syllabus** — and says so on the map before I click.
- As a hiring manager, I want to watch the council work, **where I can see each agent's mandate, its objections, and what was struck and why**, in under a minute and without reading code.
- As a hiring manager, I want to know whether the multi-agent design was worth it, **where the repo shows planted-flaw results for one agent versus the council, with cost and latency alongside**.
- As any visitor, I want the page to be instantly useful, **where the map and cached syllabi load with no wait and no cost**, including when the daily cap is hit.

## 16. Failure modes and fallbacks

| Failure | Detection | Behavior |
|---|---|---|
| Book's structure can't be established | no table of contents found | Assign as a whole-book reading, marked |
| Researcher finds nothing on the shelf for a thread | fewer than 2 confirmed readings | Merge, drop, or convert to a named gap |
| Whole subject too thin | fewer than 4 units | Short syllabus, with the gap stated |
| Isnad can't confirm a chapter claim | uncertain verdict | Struck; shown in the scrap heap |
| A reviewer times out | per-agent timeout | Ship without that pass, labeled |
| Web search unavailable | tool error | Shelf-only syllabus; outside additions deferred, stated on the page |
| Daily cap reached | counter | Live runs off; map and cached syllabi still served |
| Model overload | API error | Backoff, then fall back a tier (§12) |
| Subject outside the shelf | pre-run match | Honest refusal, with the nearest subjects the shelf does support |

## 17. Monitoring

- **Per run:** wall-clock and cost per agent, searches, readings proposed vs. struck with reasons, shelf share, gaps named, units shipped.
- **Daily:** runs, spend against cap, errors and timeouts, guardrail triggers (refusals, cap hits, short syllabi).
- **Drift:** all three suites re-run on every model change and monthly, appended to `docs/EVAL_RESULTS.md` with model IDs and date.
- **Human review:** every syllabus in the eval set is hand-checked at least once; the LLM judge's agreement with those checks is reported alongside its scores. Live runs aren't reviewed, because nothing is stored — observability traded for privacy, deliberately.

## 18. Cost and infrastructure envelope

- **v1:** zero marginal cost per visit. The site is static — map, syllabi, and recorded runs are files in the repo. A full rebuild (map plus every syllabus) costs a few dollars and is run deliberately, with a budget checked before it starts.
- Book-structure and verification caches make rebuilds cheap after the first one.
- Hosting: Replit static deployment, its own subdomain, alongside the other projects. No server and no key in production until v2.
- **v2:** a small server holds the Anthropic key, rotated on the same quarterly schedule as the other projects.

## 19. Milestones

1. **The map:** cartographer over the shelf; subjects, verdicts, and counts printed to a terminal.
2. **Skeleton council:** lead → researchers → draft syllabus for one well-covered subject. No UI.
3. **Isnad:** chapter-fidelity checks and the struck list. This is the make-or-break piece.
4. **Suite A:** planted flaws, single agent vs. council, first real numbers.
5. **Counter-reader and realist**, then reconciliation, ordering, objectives.
6. **Recording:** every run writes a transcript (agent, step, claim, verdict, timing, cost) that the site can replay.
7. **Suite B and C**, plus the researcher model comparison.
8. **Generate:** run the council across the mapped subjects; commit the syllabi and transcripts.
9. **The page:** the map, the replay, the syllabi.
10. **Deploy** as a static site, then write the portfolio page from the measurements.

## 20. Open questions

- How are subjects clustered: from the existing catalog entries (genres and themes already written for each book), by embeddings, or by asking a model to read the whole shelf at once? Cheapest defensible option first.
- Can chapter-level tables of contents be found reliably enough to make chapter assignment the default rather than the exception? Milestone 3 answers this; if not, units assign whole books with page estimates.
- Does the shelf data live as a committed copy or read from the Sultan's repo?
- Should other people be able to upload their own Goodreads export later, and what would that cost per run?
- Do cached syllabi get re-run on a schedule, or are they dated snapshots?

## 21. v2 — live runs

The same council, on a subject a visitor types. Everything needed for it already exists in v1: the council code, the caches, the recorded-transcript format (which becomes a live stream). What it adds is the operational load — a server, a key in production, rate limits, a spend cap, and the guardrails in §11 that v1 doesn't need.

Worth doing when the precomputed version is good enough that a stranger's subject is likely to produce something decent, and not before. The honest failure mode — "your subject isn't in this library" — is already the map's job.
