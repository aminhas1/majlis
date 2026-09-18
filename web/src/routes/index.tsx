import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowDownRight, ArrowUpRight, BookOpen, Sparkles, X } from "lucide-react";
import { useEffect, useState } from "react";

import {
  cluster,
  loadMap,
  loadRunIndex,
  VERDICT_LABEL,
  type RunSummary,
  type Territory,
} from "../lib/majlis";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Majlis — A bookshelf becomes a syllabus" },
      {
        name: "description",
        content:
          "Majlis uses a council of AI agents to map one Goodreads library into research-ready course ideas.",
      },
      { property: "og:title", content: "Majlis — A bookshelf becomes a syllabus" },
      {
        property: "og:description",
        content:
          "Explore the intellectual territories found by the Cartographer agent, then commission a research council to draft a syllabus.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Index,
});

/** Keeps the grid asymmetric however many territories the Cartographer finds. */
const SPANS = ["md:col-span-7", "md:col-span-5", "md:col-span-5", "md:col-span-7", "md:col-span-4", "md:col-span-4", "md:col-span-4"];

function GeometryField() {
  return (
    <svg className="geometry-field" viewBox="0 0 900 620" aria-hidden="true">
      <g className="geometry-spin" fill="none" stroke="currentColor">
        <path d="M450 34 523 166 670 107 611 254 743 327 596 386 655 533 508 474 435 606 376 459 229 518 288 371 156 298 303 239 244 92 391 151Z" />
        <path d="M450 91 497 209 621 173 563 283 670 350 548 366 557 491 465 406 371 489 382 365 260 347 368 282 312 171 435 209Z" />
        <path d="M450 151 493 250 600 254 516 320 545 423 456 366 369 425 396 321 311 256 418 251Z" />
        <circle cx="450" cy="320" r="122" />
        <circle cx="450" cy="320" r="214" />
        <path d="M156 298h587M244 92l411 441M670 107 229 518M450 34l-15 572" />
      </g>
    </svg>
  );
}

function CourseTile({
  territory,
  index,
  hasRun,
  onSelect,
}: {
  territory: Territory;
  index: number;
  hasRun: boolean;
  onSelect: (t: Territory) => void;
}) {
  const tone = index % 2 === 0 ? "course-tile-pink" : "course-tile-blue";
  return (
    <button
      type="button"
      onClick={() => onSelect(territory)}
      className={`course-tile ${tone} ${SPANS[index % SPANS.length]}`}
    >
      <div className="flex items-start justify-between gap-4">
        <span className="course-index">
          TERRITORY / {String(index + 1).padStart(2, "0")}
          {hasRun ? " · COUNCIL SAT" : ""}
        </span>
        <ArrowUpRight className="course-arrow" aria-hidden="true" />
      </div>
      <h2>{territory.name}</h2>
      <div className="course-meta">
        <span>{cluster(territory)}</span>
        <span>{territory.books} books</span>
        <span>{territory.read} read</span>
        <span>{VERDICT_LABEL[territory.verdict]}</span>
      </div>
    </button>
  );
}

function Index() {
  const [territories, setTerritories] = useState<Territory[]>([]);
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [selected, setSelected] = useState<Territory | null>(null);

  useEffect(() => {
    loadMap().then(setTerritories).catch(() => setTerritories([]));
    loadRunIndex().then(setRuns).catch(() => setRuns([]));
  }, []);

  const runFor = (t: Territory | null) => (t ? runs.find((r) => r.subject === t.name) : undefined);
  const ready = territories.filter((t) => t.verdict === "course").length;

  return (
    <main className="min-h-screen overflow-hidden bg-background text-foreground">
      <section className="hero-shell">
        <GeometryField />
        <div className="calligraphy" lang="ar" dir="rtl" aria-hidden="true">مجلس</div>

        <nav className="relative z-20 flex items-center justify-between border-b border-border px-5 py-4 md:px-10">
          <a href="#top" className="font-display text-xl uppercase text-foreground">Majlis</a>
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <span className="status-dot" />
            Cartographer pass complete
          </div>
        </nav>

        <div id="top" className="relative z-10 mx-auto grid max-w-[1480px] grid-cols-1 gap-8 px-5 pb-10 pt-8 md:grid-cols-12 md:px-10 md:pb-12 md:pt-10">
          <header className="md:col-span-8">
            <p className="eyebrow"><Sparkles size={13} /> Cartographer output</p>
            <h1 className="mt-3 max-w-4xl font-display text-[clamp(2rem,5vw,5rem)] uppercase leading-[0.88]">
              {territories.length || 16} territories<br />
              <span className="text-primary">mapped from one</span><br />
              <span className="text-accent">Goodreads shelf.</span>
            </h1>
          </header>

          <aside className="flex flex-col justify-end md:col-span-4 md:pb-1">
            <p className="max-w-md text-sm leading-relaxed text-muted-foreground md:text-base">
              The Cartographer clustered 837 books into topics. Pick a territory to generate a syllabus.
            </p>
            <a href="#territories" className="mt-5 inline-flex w-fit items-center gap-3 border-b border-primary pb-1.5 text-sm font-semibold text-primary">
              Browse territories <ArrowDownRight size={18} />
            </a>
          </aside>
        </div>

        <div className="analysis-strip relative z-10">
          <div className="analysis-lead"><span>Cartographer / output</span><strong>Knowledge map resolved</strong></div>
          <div><strong>837</strong><span>books scanned</span></div>
          <div><strong>756</strong><span>catalogued</span></div>
          <div><strong>{territories.length || 16}</strong><span>territories found</span></div>
          <div><strong>{ready || 11}</strong><span>research-ready</span></div>
        </div>
      </section>

      <section id="territories" className="territories-section">
        <div className="territories-heading">
          <div>
            <p className="eyebrow"><BookOpen size={13} /> Select a territory</p>
            <h2 className="font-display text-4xl uppercase md:text-6xl">Candidate courses</h2>
          </div>
          <p>Shape reflects evidence depth. Every count comes from the shelf itself — books held, books read, and the Cartographer's verdict on whether that is enough to teach.</p>
        </div>
        <div className="course-grid">
          {territories.map((t, i) => (
            <CourseTile
              key={t.name}
              territory={t}
              index={i}
              hasRun={Boolean(runs.find((r) => r.subject === t.name))}
              onSelect={setSelected}
            />
          ))}
        </div>
      </section>

      {selected && (
        <div className="selection-overlay" role="dialog" aria-modal="true" aria-labelledby="selected-course-title">
          <button className="selection-dismiss" type="button" onClick={() => setSelected(null)} aria-label="Close course preview"><X /></button>
          <div className="selection-geometry" aria-hidden="true" />
          <p className="eyebrow">{VERDICT_LABEL[selected.verdict]}</p>
          <h2 id="selected-course-title" className="font-display uppercase">{selected.name}</h2>
          <p className="selection-copy">{selected.shape}</p>
          <p className="selection-copy mt-4 text-sm opacity-80"><strong className="text-accent">What it's missing: </strong>{selected.holes}</p>
          <div className="selection-stats">
            <span><strong>{selected.books}</strong> source books</span>
            <span><strong>{selected.read}</strong> already read</span>
            <span><strong>{selected.reviewed}</strong> with her notes</span>
            <span><strong>{selected.unread}</strong> unread</span>
          </div>
          {runFor(selected) ? (
            <Link to="/council/$slug" params={{ slug: runFor(selected)!.slug }} className="commission-button">
              Watch the council <ArrowUpRight size={20} />
            </Link>
          ) : (
            <Link to="/live" search={{ subject: selected.name }} className="commission-button">
              Commission syllabus <ArrowUpRight size={20} />
            </Link>
          )}
        </div>
      )}
    </main>
  );
}
