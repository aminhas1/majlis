# Majlis — AI PRD

*Majlis*: a study assembly. You bring a question; a council of agents researches it, argues about it, and hands you a syllabus.

**Status:** draft · **Owner:** Abeer Minhas · **Last updated:** 2026-09-18
**Structure:** strategic foundation → AI-specific requirements → operations. Numbers in §6–§9 are targets to design against, not results; measured values land in `docs/EVAL_RESULTS.md` once §14 runs.

---

# Tier 1 — Strategic foundation

## 1. Executive summary

Majlis turns a question ("I want to understand the partition of India") into a real 6–8 week syllabus: units with learning objectives, assigned readings with specific chapters, and a note on where scholars disagree. A council of specialist agents builds it — researchers work threads in parallel, then three reviewers with conflicting mandates attack the draft before a lead reconciles it. Nothing reaches the reader unless it has been verified to exist and to be obtainable without a university library.

## 2. Problem

Ask a chatbot for a reading list on Sudanese history and you get a plausible one in ten seconds. Some of those books don't exist. Several are paywalled. Nothing says what to read first, what the argument between the sources is, or whether someone with a job could finish it.

Two failures underneath: **nothing checks the work**, and **nothing plans it**. People who want to learn a subject seriously, without enrolling anywhere, have no equivalent of a course.

## 3. Users

| User | Job to be done | Needs |
|---|---|---|
| **Curious adult, no institutional access** (primary) | "Actually understand X, not skim ten articles about it." | A course they can start tonight, built from things they can get hold of |
| **Hiring manager on Abeer's portfolio** (primary) | "Can this person design and reason about a multi-agent system, or only talk about one?" | To see the council work, understand it in under a minute, and poke at it |

Designed for the learner, instrumented for the hiring manager. Where they conflict: the learner wins on output quality, the hiring manager wins on transparency.

## 4. Product concept

One line in, a syllabus out, with the council's argument visible along the way.

- **Landing:** three finished syllabi, one click each, served from cache — instant and free. Most visitors stop here.
- **Ask:** one line, an optional why-chip (curiosity / an argument I keep losing / a trip I'm taking), a 6 or 8 week toggle.
- **The council convenes in the open:** threads appear, researchers report, Isnad strikes items with reasons, the counter-reader objects, the realist reorders. Units stream in as they settle.
- **The syllabus:** units with objectives, readings with access labels, and the live scholarly disagreement. Below it, the struck list. Books already on Abeer's shelf are marked.
- **Take it:** copy as Markdown, with a link for getting hold of each reading.

## 5. Goals and non-goals

**Goals**
- A genuine 6–8 week syllabus, not a reading list.
- Every assigned item verified to exist and to be obtainable without a university library.
- The council's reasoning visible, including what it threw away.
- Evidence that the multi-agent design earns its cost.

**Non-goals**
- Not a chatbot, not a general research agent.
- No assignments, essays, or grading.
- No accounts, no history, no personalization beyond the question asked.
- Not a book recommender — that's the Sultan (librarian.abeerminhas.com).

## 6. Success metrics

| Dimension | Metric | Target |
|---|---|---|
| Trust | Assigned items that exist as described | 100% (nothing unverified ships) |
| Access | Assigned items obtainable without a university library | 100% |
| Usefulness | Units whose estimated workload fits the stated weekly budget | ≥90% |
| Structure | Syllabi with objectives, ordered units, and a disagreement note in every unit | 100% |
| Architecture | Planted flaws caught by the council vs. a single reviewer agent | Council ahead by a margin that justifies its cost |
| Demo | Time to first visible unit / full run | ≤15s / ≤60s |
| Cost | Cost per live run | cents, not dollars |

## 7. Competitive context

| | What it gives you | What it doesn't |
|---|---|---|
| ChatGPT / Claude, asked directly | A plausible list in seconds | No verification, no access check, no sequence, no visible reasoning |
| Deep-research modes | A long report with citations | A report, not a course; citations checked for existence, not obtainability |
| Coursera / MOOCs | Real courses, verified | Only where a course exists; not on "how perfume became an industry" |
| Syllabus archives (e.g. Open Syllabus) | Real syllabi from real courses | Static, institution-shaped, assumes library access |

The wedge: **course structure + obtainability**, with the checking shown rather than claimed.

---

# Tier 2 — AI-specific requirements

## 8. The council

| Agent | Mandate | Tools | Runs |
|---|---|---|---|
| **Lead** | Split the question into 4–6 threads; later reconcile objections, order units, write objectives | — | twice (open, close) |
| **Researcher** (one per thread) | Propose candidate readings with a reason and a specific chapter/section | web search | parallel |
| **Isnad** (verifier) | Does each item exist as described, and can a person without a university get it? Strike what fails | Open Library, web search | parallel with reviewers |
| **Counter-reader** | Whose account dominates? Demand the missing perspective | web search | parallel |
| **Realist** | Length, difficulty, sequence, entry points; is this doable in the stated weeks? | — | parallel |

Named for the *isnad*, the chain of transmission classical scholars used to judge whether a report could be trusted.

**Why a council and not one agent:** the reviewers' mandates conflict — rigor against breadth against feasibility. One agent asked to weigh all three blends them. Treated as a hypothesis to measure (§10), not a claim to put on the page.

**The lead may decline to convene.** Small or non-subject questions get a short answer instead of a fan-out. Spending 60 seconds and five agents on "three books about bread" is a bug, and how often the lead gets this right is measured.

## 9. Source and assignment rules

- **Allowed:** books and chapters, academic articles, primary sources, film/audio/lectures.
- **Obtainability is a hard requirement:** open access, in print, common in public libraries, freely streamable, or public domain. An item that fails is struck even when it's the best thing on the subject — with a free alternative proposed where one exists.
- **Nothing unverified ships.** Struck items appear only in the visible scrap heap.
- **Assign parts, not whole books:** specific chapters or page ranges, with an estimated reading time.

## 10. Eval framework

Acceptance is measured, not asserted. Two suites, both re-runnable from the repo.

**Suite A — planted flaws.** Draft syllabi seeded with known defects, run through (a) one reviewer agent asked to check everything, (b) the full council.

| Flaw | Should be caught by | Pass threshold |
|---|---|---|
| Fabricated book: plausible title, real author | Isnad | ≥95% |
| Real book, wrong author or year | Isnad | ≥90% |
| Key reading paywalled, free alternative exists | Isnad | ≥80% |
| Every source by outsiders to the subject | Counter-reader | ≥80% |
| 4,000 pages presented as six weeks | Realist | ≥90% |
| Three readings making the same argument | Realist / Lead | ≥70% |
| **Clean syllabus** (no planted flaw) | nobody | false strikes ≤5% |

**Suite B — end-to-end syllabi.** A fixed set of questions across history, science, craft, and religion. Every assigned item checked by hand once, then graded by an LLM judge whose agreement with those hand checks is reported.

| Dimension | Measure | Pass |
|---|---|---|
| Existence | items that exist as described | 100% |
| Obtainability | items gettable without a university | 100% |
| Sequence | a reader could follow unit order without gaps | ≥90% of units |
| Workload honesty | estimated vs. actual pages/runtime | within 25% |
| Disagreement note | names a real live debate, not a platitude | ≥80% of units |

**Also tracked every run:** wall-clock, cost, tokens per agent, searches per researcher, strike rate, and how often the lead declines to convene.

## 11. Guardrails specification

**Input filtering**
- Question length capped; one question per run.
- The lead refuses non-subjects, requests for a person's private information, and anything where a wrong curriculum does harm (medical, legal, or safety instructions presented as a course) with a plain explanation.
- Instructions embedded in fetched pages are data, never commands; researchers pass along findings, not directives.

**Output validation**
- No item reaches a unit without an existence check and an access check.
- Every assigned reading carries an access label and a link.
- Unit workload must fall within the stated weekly budget or the realist sends it back (one reconciliation pass, then it ships with a visible warning).
- No invented quotes or fabricated scholarly positions; disagreement notes must name a source.

**Action boundaries**
- The council reads the web; it never posts, buys, emails, or downloads files.
- Search is capped per researcher per run; no unbounded crawling.
- No user data is stored; questions are not retained after a run.

**Escalation and confidence**
- Isnad returns verified / unverified / uncertain. Uncertain is treated as unverified: struck, and shown in the scrap heap with the reason.
- If a thread returns fewer than two verified items, the lead merges or drops the thread rather than padding it.
- If fewer than four units survive verification, the run returns a short syllabus and says so, rather than inventing filler.
- Hard failure (an agent errors or times out): the syllabus ships without that agent's pass, labeled on the page.

**Rate and spend**
- Per-visitor run cap per day; hard daily spend cap; cached examples stay available when the cap is hit.

## 12. Model strategy

| Role | Starting choice | Rationale | Upgrade / fallback |
|---|---|---|---|
| Lead (decompose, reconcile) | Claude Opus 5 | Hardest judgment: structure, conflict resolution, ordering | Falls back to Sonnet 5 on overload |
| Researcher | Claude Sonnet 5 | Highest volume and the cost driver; search-and-summarize is well within range | Measured against Opus 5 in Suite B before fixing |
| Isnad | Claude Opus 5 | The guardrail that the product's credibility rests on; false negatives are the worst failure | — |
| Counter-reader / Realist | Claude Sonnet 5 | Narrow mandates, short outputs | Promote if Suite A shows misses |
| LLM judge (evals, offline) | Claude Opus 5 | Judge should be at least as strong as the system judged | Agreement with hand checks reported |

**Model choice is a measured tradeoff, not a default.** The researcher tier is the whole cost story; the first real experiment is Sonnet-vs-Opus researchers on Suite B, reported as quality against dollars.

**Upgrade protocol:** when a new model ships, run both suites against the current pinned setup and the candidate, compare quality, cost, and latency, and record the decision in `docs/EVAL_RESULTS.md`. Model IDs are pinned in config; no silent upgrades.

## 13. Data requirements

| Data | Source | Handling |
|---|---|---|
| Candidate readings | Live web search at run time | Not stored beyond the run |
| Existence and edition facts | Open Library API | Cached locally to cut repeat calls and cost |
| Obtainability signals | Open access registries, in-print status, public-domain status, streaming availability | Cached with the item |
| Abeer's shelf (for "already on the shelf" marks) | The Sultan's `shelf.json` | Read-only copy; ratings and review text are Abeer's, never presented as the council's judgment |
| Cached example syllabi | Pre-run, committed to the repo | Public, re-runnable |
| Eval sets | Hand-built, in the repo | Fixed; changes are versioned so numbers stay comparable |
| Visitor questions | — | Not stored, not logged with identifiers, not used for anything after the run |

No training, no fine-tuning, no user data retention. Aggregate counters only (runs per day, spend).

## 14. Responsible AI

- **Whose knowledge counts.** A syllabus is a claim about what matters. The counter-reader exists because the easy default — a subject explained entirely by outsiders to it — is a real failure, not a stylistic one. It's judged on whether it changes the syllabus, not on whether it speaks.
- **Access as fairness.** Assigning paywalled scholarship to someone without a university is a way of excluding them. Obtainability is a hard requirement for that reason.
- **Transparency.** The scrap heap is public by design: a reader can see what the council rejected and why, and disagree.
- **Honest limits.** The page states that the council can be wrong, that verification covers existence and access rather than quality, and that a syllabus is one defensible path through a subject, not the canon.
- **Attribution.** Scholarly positions are attributed to named sources, never invented.
- **Regulatory.** No profiling, no automated decisions about people, no biometric or sensitive data. Under the EU AI Act this sits in the minimal-risk tier; the applicable obligation is disclosure that the content is AI-generated, which the page does prominently.

---

# Tier 3 — Operations

## 15. User stories (with quality clauses)

- As a curious adult, I want a course on a subject I care about, **where every assigned reading exists, states where to get it free or cheaply, and the whole thing fits the hours I said I had** — and where, if the council can only verify four units' worth, it tells me instead of padding.
- As a curious adult, I want to know what I'm being assigned and why, **where each unit names a real scholarly disagreement with sources**, and gracefully says "the sources here mostly agree" when there isn't one.
- As a hiring manager, I want to watch the council work, **where I can see each agent's mandate, what it objected to, and what was struck and why**, within 60 seconds and without reading code.
- As a hiring manager, I want to know whether the multi-agent design was worth it, **where the repo shows planted-flaw results for one agent versus the council, with cost and latency alongside**.
- As a visitor on a phone, I want to read a finished example instantly, **where cached syllabi load with no wait and no cost**, including when the daily cap has been hit.

## 16. Failure modes and fallbacks

| Failure | Detection | Behavior |
|---|---|---|
| Researcher returns nothing usable | fewer than 2 verified items in a thread | Lead merges or drops the thread |
| Isnad can't verify an item | uncertain verdict | Struck; shown in scrap heap with reason |
| Too little survives verification | fewer than 4 units | Ship a short syllabus, say why |
| A reviewer times out | per-agent timeout | Ship without that pass, labeled on the page |
| Web search unavailable | tool error | Abort with an honest message; offer cached examples |
| Daily cap reached | counter | Live runs disabled, cached examples still served |
| Model overload / 429 | API error | Retry with backoff, then fall back a tier (§12) |
| Question outside scope | lead's refusal path | Short explanation, suggest a rephrase |

## 17. Monitoring

- **Per run:** wall-clock and cost per agent, searches per researcher, items proposed vs. struck, strike reasons, units shipped, whether the lead declined.
- **Daily:** runs, spend against cap, error and timeout rates, guardrail trigger counts (refusals, cap hits, short syllabi).
- **Drift:** both eval suites re-run on every model change and monthly; results appended to `docs/EVAL_RESULTS.md` with the model IDs and date, so a regression is visible rather than inferred.
- **Human review:** every syllabus in the eval set is hand-checked at least once; the LLM judge's agreement with those checks is reported alongside its scores. Live runs are not reviewed (nothing is stored), which is a deliberate tradeoff of observability for privacy.

## 18. Cost and infrastructure envelope

- Target cents per live run; hard daily spend cap; Open Library results cached to avoid repeat calls.
- Cached examples cost nothing to serve and carry most of the traffic.
- Hosting: Replit, its own subdomain, alongside the other projects.
- Secrets: Anthropic key server-side only, rotated on the same quarterly schedule as the other projects.

## 19. Milestones

1. **Skeleton:** lead → researchers → draft syllabus in a terminal. No UI.
2. **Isnad:** existence and access checks, struck list.
3. **Suite A:** planted flaws, single agent vs. council, first real numbers.
4. **Counter-reader and realist**, then reconciliation, ordering, and objectives.
5. **Suite B** and the researcher model comparison.
6. **The page:** live council view, streaming units, cached examples.
7. **Deploy**, then write the portfolio page from the measurements.

## 20. Open questions

- Which model for researchers — settled by §12's first experiment, not by preference.
- Does the shelf cross-reference read the Sultan's data live or a committed copy?
- Is "where scholars disagree" reliable enough to ship, or does it need its own verification pass?
- Do cached examples need re-running on a schedule, or are they snapshots with a visible date?
