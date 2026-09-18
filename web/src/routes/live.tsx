import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { ArrowUpRight } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { CouncilStage } from "../components/council-stage";
import type { RunEvent } from "../lib/majlis";

export const Route = createFileRoute("/live")({
  validateSearch: (search: Record<string, unknown>) => ({ subject: String(search.subject ?? "") }),
  component: LiveRoute,
});

/**
 * Convenes the council for real: asks the local API to start a run, then shows
 * each agent's step as it arrives. About four minutes and $0.80 of tokens.
 * Needs `.venv/bin/python pipeline/api.py` running alongside the dev server.
 */
function LiveRoute() {
  const { subject } = Route.useSearch();
  const navigate = useNavigate();
  const [events, setEvents] = useState<RunEvent[]>([]);
  const [status, setStatus] = useState<"starting" | "running" | "done" | "error">("starting");
  const [message, setMessage] = useState("");
  const [slug, setSlug] = useState<string | null>(null);
  const started = useRef(false);

  useEffect(() => {
    if (started.current || !subject) return;
    started.current = true;

    (async () => {
      try {
        const res = await fetch("/api/run", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ subject }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error ?? "The council could not be convened.");

        setStatus("running");
        const stream = new EventSource(`/api/stream/${data.id}`);
        stream.onmessage = (e) => {
          const event = JSON.parse(e.data) as RunEvent & { slug?: string; cost_usd?: number };
          if (event.kind === "failed") {
            setStatus("error");
            setMessage(event.text);
            stream.close();
            return;
          }
          if (event.kind === "finished") {
            setSlug(event.slug ?? null);
            setStatus("done");
          }
          setEvents((prev) => [...prev, event]);
        };
        stream.addEventListener("end", () => { stream.close(); setStatus((s) => (s === "error" ? s : "done")); });
        stream.onerror = () => { stream.close(); setStatus((s) => (s === "done" ? s : "error")); };
      } catch (err) {
        setStatus("error");
        setMessage(err instanceof Error ? err.message : String(err));
      }
    })();
  }, [subject]);

  const elapsed = events.length ? events[events.length - 1].at : 0;
  const cost = events.reduce((c, e) => Math.max(c, (e as RunEvent & { cost_usd?: number }).cost_usd ?? 0), 0);

  if (!subject) {
    return (
      <main className="council-shell">
        <div className="council-empty">
          <h1 className="font-display text-4xl uppercase">No territory chosen</h1>
          <Link to="/" className="council-back">Back to the territories</Link>
        </div>
      </main>
    );
  }

  return (
    <main className="council-shell">
      <nav className="council-nav">
        <Link to="/" className="font-display text-lg uppercase">Majlis</Link>
        <span className="council-subject">
          {subject} · {status === "running" ? "council in session, live" : status === "done" ? "run complete" : status === "error" ? "run failed" : "convening"}
        </span>
        <span className="council-models">lead claude-opus-5 · workers claude-sonnet-5</span>
      </nav>

      {status === "error" && (
        <p className="live-error">
          {message || "Couldn't reach the council API."} Start it with{" "}
          <code>.venv/bin/python pipeline/api.py</code> and try again.
        </p>
      )}

      <CouncilStage
        title={subject}
        events={events}
        nextAgent={status === "running" || status === "starting" ? guessWorking(events) : null}
        elapsed={elapsed}
        cost={cost}
        waitingLabel="Convening the council — the lead is reading the shelf…"
        controls={
          <>
            <span className="live-badge">{status === "running" ? "● live" : status === "done" ? "finished" : status === "error" ? "stopped" : "starting"}</span>
            {slug && (
              <button type="button" className="record-syllabus" onClick={() => navigate({ to: "/syllabus/$slug", params: { slug } })}>
                Read the syllabus <ArrowUpRight size={14} />
              </button>
            )}
          </>
        }
      />
    </main>
  );
}

/** Live runs have no future to look at, so infer the working agent from the pipeline order. */
function guessWorking(events: RunEvent[]): string {
  if (!events.length) return "lead";
  const last = events[events.length - 1];
  const after: Record<string, string> = {
    lead: "researcher",
    researcher: "isnad",
    isnad: "counter",
    counter: "realist",
    realist: "lead",
    audit: "lead",
  };
  return last.kind === "plan" ? "researcher" : (after[last.agent] ?? "lead");
}
