/**
 * The data the Majlis pipeline produces.
 *
 * `public/data/map.json` is the Cartographer's output: it read 837 books from a
 * Goodreads export and worked out which subjects the library can teach.
 * `public/runs/*.json` are recorded council runs — every agent's step, with
 * timing and cost, plus the syllabus it produced.
 *
 * Nothing here is invented in the UI. If a number isn't in these files, it
 * doesn't get shown.
 */

export type Verdict = "course" | "unit" | "not_yet";

export type Territory = {
  name: string;
  description: string;
  why_this_library: string;
  /** What this library's version of the subject actually looks like. */
  shape: string;
  /** What a course built from it would be missing. */
  holes: string;
  themes: string[];
  genres: string[];
  verdict: Verdict;
  books: number;
  read: number;
  unread: number;
  abandoned: number;
  rated: number;
  reviewed: number;
};

export type RunEvent = {
  at: number;
  agent: "lead" | "researcher" | "isnad" | "counter" | "realist" | "audit";
  kind: string;
  text: string;
  thread?: string;
};

export type Reading = {
  title: string;
  author: string;
  assign: string;
  pages: number;
  from_shelf: boolean;
  professors_note: string;
};

export type Unit = {
  week: number;
  title: string;
  objectives: string[];
  readings: Reading[];
  disagreement: string;
};

export type Syllabus = {
  course_title: string;
  description: string;
  units: Unit[];
  shortfall: string;
  objection?: string;
  struck?: { title: string; struck_by: string; reason: string }[];
};

export type Run = {
  subject: string;
  verdict: Verdict;
  seconds: number;
  cost_usd: number;
  models: { lead: string; isnad: string; workers: string };
  events: RunEvent[];
  syllabus: Syllabus;
};

export type RunSummary = { slug: string; subject: string; seconds: number; cost_usd: number; units: number };

export const VERDICT_LABEL: Record<Verdict, string> = {
  course: "Research-ready",
  unit: "One strong unit",
  not_yet: "Not yet",
};

/** The short label under a territory's name: its most specific theme. */
export function cluster(t: Territory): string {
  return (t.themes[0] ?? t.genres[0] ?? "").replace(/\b\w/g, (c) => c.toUpperCase());
}

export async function loadMap(): Promise<Territory[]> {
  const res = await fetch("/data/map.json");
  const map = (await res.json()) as { subjects: Territory[] };
  return map.subjects;
}

export async function loadRunIndex(): Promise<RunSummary[]> {
  const res = await fetch("/runs/index.json");
  return res.ok ? ((await res.json()) as RunSummary[]) : [];
}

export async function loadRun(slug: string): Promise<Run> {
  const res = await fetch(`/runs/${slug}.json`);
  return (await res.json()) as Run;
}

/**
 * Real runs have long silences — the lead thinks for 47 seconds before it says
 * anything. Replay keeps the real clock but caps dead air, so the council view
 * never looks stalled.
 */
export function compressTimeline<T extends { at: number }>(events: T[], maxGap = 4): (T & { showAt: number })[] {
  let shown = 0;
  let last = 0;
  return events.map((e) => {
    shown += Math.min(e.at - last, maxGap);
    last = e.at;
    return { ...e, showAt: shown };
  });
}
