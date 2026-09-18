import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowUpRight, Pause, Play, RotateCcw } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { CouncilStage } from "../components/council-stage";
import { compressTimeline, loadRun, type Run } from "../lib/majlis";

export const Route = createFileRoute("/council/$slug")({
  component: CouncilRoute,
});

const SPEEDS = [1, 4, 10, 40];

/** Replays a recorded run: the real transcript, on the real clock, minus the dead air. */
function CouncilRoute() {
  const { slug } = Route.useParams();
  const [run, setRun] = useState<Run | null>(null);
  const [cursor, setCursor] = useState(0);
  const [playing, setPlaying] = useState(true);
  const [speed, setSpeed] = useState(4);
  const [clock, setClock] = useState(0);

  useEffect(() => {
    loadRun(slug).then(setRun).catch(() => setRun(null));
  }, [slug]);

  const timeline = useMemo(() => (run ? compressTimeline(run.events) : []), [run]);
  const end = timeline.length ? timeline[timeline.length - 1].showAt : 0;
  const finished = Boolean(timeline.length) && cursor >= timeline.length;

  useEffect(() => {
    if (!playing || !timeline.length || finished) return;
    const tick = setInterval(() => setClock((c) => c + 0.1 * speed), 100);
    return () => clearInterval(tick);
  }, [playing, speed, timeline.length, finished]);

  useEffect(() => {
    let next = cursor;
    while (next < timeline.length && timeline[next].showAt <= clock) next += 1;
    if (next !== cursor) setCursor(next);
  }, [clock, cursor, timeline]);

  if (!run) {
    return (
      <main className="council-shell">
        <div className="council-empty">
          <p className="eyebrow">No recorded run</p>
          <h1 className="font-display text-4xl uppercase">This council hasn't sat yet</h1>
          <Link to="/" className="council-back">Back to the territories</Link>
        </div>
      </main>
    );
  }

  const shown = timeline.slice(0, cursor);
  const progress = end ? Math.min(1, clock / end) : 0;

  return (
    <main className="council-shell">
      <nav className="council-nav">
        <Link to="/" className="font-display text-lg uppercase">Majlis</Link>
        <span className="council-subject">{run.subject} · recorded run</span>
        <span className="council-models">lead {run.models.lead} · workers {run.models.workers}</span>
      </nav>

      <CouncilStage
        title={run.syllabus.course_title}
        events={shown}
        nextAgent={cursor < timeline.length ? timeline[cursor].agent : null}
        elapsed={run.seconds * progress}
        cost={run.cost_usd * progress}
        waitingLabel="The lead is reading the shelf…"
        controls={
          <>
            <button
              type="button"
              onClick={() => (finished ? (setCursor(0), setClock(0), setPlaying(true)) : setPlaying((p) => !p))}
            >
              {finished ? <RotateCcw size={14} /> : playing ? <Pause size={14} /> : <Play size={14} />}
              {finished ? "Replay" : playing ? "Pause" : "Play"}
            </button>
            <button type="button" onClick={() => setSpeed(SPEEDS[(SPEEDS.indexOf(speed) + 1) % SPEEDS.length])}>
              {speed}×
            </button>
            <button type="button" onClick={() => { setCursor(timeline.length); setClock(end); setPlaying(false); }}>
              Skip
            </button>
            <Link to="/syllabus/$slug" params={{ slug }} className="record-syllabus">
              Syllabus <ArrowUpRight size={14} />
            </Link>
          </>
        }
      />
    </main>
  );
}
