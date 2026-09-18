import type { ReactNode } from "react";
import { useEffect, useRef } from "react";

import type { RunEvent } from "../lib/majlis";

/** The council, seated. Order is the order they act, clockwise from the top. */
export const SEATS = [
  { id: "lead", label: "Lead", model: "Opus 5", tools: "shelf", mandate: "Splits the subject into threads, then reconciles what comes back" },
  { id: "researcher", label: "Researchers", model: "Sonnet 5", tools: "shelf + web", mandate: "One per thread, in parallel: propose readings, name gaps" },
  { id: "isnad", label: "Isnad", model: "Opus 5", tools: "web search", mandate: "Verifies every claim about what a book covers. Strikes what it can't confirm" },
  { id: "counter", label: "Counter-reader", model: "Sonnet 5", tools: "web search", mandate: "Whose account is missing from this shelf?" },
  { id: "realist", label: "Realist", model: "Sonnet 5", tools: "—", mandate: "Length, order, entry point: can a person finish this in six weeks?" },
  { id: "audit", label: "Audit", model: "code", tools: "—", mandate: "Every reading ships or has a recorded reason. Quoted notes must be her words" },
] as const;

const KIND_TONE: Record<string, string> = {
  strike: "tone-strike",
  objection: "tone-objection",
  cut: "tone-cut",
  gap: "tone-cut",
  narrow: "tone-narrow",
  done: "tone-done",
  failed: "tone-strike",
  finished: "tone-done",
};

export function seatPosition(index: number, total: number) {
  const angle = (-90 + (360 / total) * index) * (Math.PI / 180);
  return { x: 50 + 38 * Math.cos(angle), y: 50 + 38 * Math.sin(angle) };
}

/** Readings proposed so far — researchers report a count per thread. */
export function countProposed(events: RunEvent[]) {
  return events
    .filter((e) => e.kind === "propose")
    .reduce((n, e) => n + ((e as RunEvent & { count?: number }).count ?? (e.text.split(",").length || 1)), 0);
}

export function CouncilStage({
  title,
  events,
  nextAgent,
  elapsed,
  cost,
  waitingLabel,
  controls,
}: {
  title: string;
  events: RunEvent[];
  /** Whoever is thinking now: the agent whose output comes next. */
  nextAgent: string | null;
  elapsed: number;
  cost: number;
  waitingLabel: string;
  controls: ReactNode;
}) {
  const streamRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    streamRef.current?.scrollTo({ top: streamRef.current.scrollHeight, behavior: "smooth" });
  }, [events.length]);

  const spoken = new Set(events.map((e) => e.agent));
  const struck = events.filter((e) => e.kind === "strike").length;

  return (
    <section className="council-stage">
      <div className="majlis-ring">
        <svg className="ring-threads" viewBox="0 0 100 100" aria-hidden="true">
          <circle cx="50" cy="50" r="38" className="ring-circle" />
          {SEATS.map((seat, i) => {
            const { x, y } = seatPosition(i, SEATS.length);
            const state = nextAgent === seat.id ? "live" : spoken.has(seat.id) ? "done" : "idle";
            return <line key={seat.id} x1="50" y1="50" x2={x} y2={y} className={`thread thread-${state}`} />;
          })}
        </svg>

        <div className="ring-center">
          <p className="eyebrow justify-center">In session</p>
          <h1 className="font-display uppercase">{title}</h1>
          <div className="ring-tally">
            <span><strong>{elapsed.toFixed(0)}s</strong> elapsed</span>
            <span><strong>${cost.toFixed(2)}</strong> spent</span>
            <span><strong>{countProposed(events)}</strong> readings proposed</span>
            <span><strong>{struck}</strong> struck</span>
          </div>
        </div>

        {SEATS.map((seat, i) => {
          const { x, y } = seatPosition(i, SEATS.length);
          const state = nextAgent === seat.id ? "live" : spoken.has(seat.id) ? "done" : "idle";
          return (
            <article key={seat.id} className={`seat seat-${state}`} style={{ left: `${x}%`, top: `${y}%` }}>
              <header><span className="seat-dot" />{seat.label}</header>
              <p>{seat.mandate}</p>
              <footer><span>{seat.model}</span><span>{seat.tools}</span></footer>
            </article>
          );
        })}
      </div>

      <aside className="council-record">
        <div className="record-controls">{controls}</div>
        <div className="record-stream" ref={streamRef}>
          {events.map((event, i) => (
            <div key={i} className="record-event">
              <span className="record-at">{event.at.toFixed(0)}s</span>
              <span className="record-who">{SEATS.find((s) => s.id === event.agent)?.label ?? event.agent}</span>
              <p>
                {KIND_TONE[event.kind] && <span className={`record-kind ${KIND_TONE[event.kind]}`}>{event.kind}</span>}
                {event.text}
              </p>
            </div>
          ))}
          {!events.length && <p className="record-waiting">{waitingLabel}</p>}
        </div>
      </aside>
    </section>
  );
}
