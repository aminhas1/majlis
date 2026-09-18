import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowLeft, Quote } from "lucide-react";
import { useEffect, useState } from "react";

import { loadRun, type Run } from "../lib/majlis";

export const Route = createFileRoute("/syllabus/$slug")({
  component: SyllabusRoute,
});

function SyllabusRoute() {
  const { slug } = Route.useParams();
  const [run, setRun] = useState<Run | null>(null);

  useEffect(() => {
    loadRun(slug).then(setRun).catch(() => setRun(null));
  }, [slug]);

  if (!run) {
    return (
      <main className="council-shell">
        <div className="council-empty">
          <p className="eyebrow">No syllabus</p>
          <h1 className="font-display text-4xl uppercase">The council hasn't drafted this one</h1>
          <Link to="/" className="council-back">Back to the territories</Link>
        </div>
      </main>
    );
  }

  const { syllabus } = run;
  const readings = syllabus.units.flatMap((u) => u.readings);
  const fromShelf = readings.filter((r) => r.from_shelf).length;

  return (
    <main className="council-shell">
      <nav className="council-nav">
        <Link to="/" className="font-display text-lg uppercase">Majlis</Link>
        <span className="council-subject">{run.subject}</span>
        <Link to="/council/$slug" params={{ slug }} className="council-back inline-flex items-center gap-2">
          <ArrowLeft size={14} /> Watch the council
        </Link>
      </nav>

      <article className="syllabus">
        <header className="syllabus-head">
          <p className="eyebrow">Six weeks · about five hours a week</p>
          <h1 className="font-display uppercase">{syllabus.course_title}</h1>
          <p className="syllabus-lede">{syllabus.description}</p>
          <div className="syllabus-stats">
            <span><strong>Abeer Minhas</strong>professor</span>
            <span><strong>Hudhud</strong>assembled by</span>
            <span><strong>{fromShelf}/{readings.length}</strong>from her shelf</span>
            <span><strong>{run.seconds}s · ${run.cost_usd.toFixed(2)}</strong>this run</span>
          </div>
        </header>

        {syllabus.units.map((unit) => (
          <section key={unit.week} className="unit">
            <div className="unit-index">
              <span className="font-display">W{String(unit.week).padStart(2, "0")}</span>
            </div>
            <div className="unit-body">
              <h2 className="font-display uppercase">{unit.title}</h2>
              <ul className="unit-objectives">
                {unit.objectives.map((o) => <li key={o}>{o}</li>)}
              </ul>

              {unit.readings.map((r) => (
                <div key={r.title} className="reading">
                  <span className={`reading-source ${r.from_shelf ? "is-shelf" : "is-added"}`}>
                    {r.from_shelf ? "Her shelf" : "Added"}
                  </span>
                  <div>
                    <p className="reading-title">{r.title}</p>
                    <p className="reading-meta">{r.author} · {r.assign} · ~{r.pages}pp</p>
                    {r.professors_note && (
                      <blockquote className="reading-note">
                        <Quote size={13} /> {r.professors_note}
                      </blockquote>
                    )}
                  </div>
                </div>
              ))}

              <div className="unit-disagreement">
                <p className="eyebrow">Where the sources disagree</p>
                <p>{unit.disagreement}</p>
              </div>
            </div>
          </section>
        ))}

        <section className="syllabus-after">
          <div>
            <h3 className="font-display uppercase">What this doesn't cover</h3>
            <p>{syllabus.shortfall || "—"}</p>
            {syllabus.objection && (
              <>
                <h3 className="font-display uppercase mt-6">The counter-reader's objection</h3>
                <p>{syllabus.objection}</p>
              </>
            )}
          </div>
          <div>
            <h3 className="font-display uppercase">Struck by the council</h3>
            <ul className="struck-list">
              {(syllabus.struck ?? []).map((s, i) => (
                <li key={i}>
                  <span className="struck-title">{s.title}</span>
                  <span className="struck-by">{s.struck_by}</span>
                  <span className="struck-reason">{s.reason}</span>
                </li>
              ))}
              {!syllabus.struck?.length && <li>Nothing was struck.</li>}
            </ul>
          </div>
        </section>
      </article>
    </main>
  );
}
