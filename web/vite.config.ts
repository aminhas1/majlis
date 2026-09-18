// @lovable.dev/vite-tanstack-config already includes the following — do NOT add them manually
// or the app will break with duplicate plugins:
//   - TanStack devtools (dev-only, first), tanstackStart, viteReact, tailwindcss, tsConfigPaths,
//     nitro (build-only using cloudflare as a default target), VITE_* env injection, @ path alias,
//     React/TanStack dedupe, error logger plugins, and sandbox detection (port/host/strictPort).
// You can pass additional config via defineConfig({ vite: { ... }, etc... }) if needed.
import { defineConfig } from "@lovable.dev/vite-tanstack-config";
import fs from "node:fs";
import path from "node:path";
import type { Plugin } from "vite";

const REPO_ROOT = path.resolve(import.meta.dirname, "..");

/**
 * Serve the pipeline's output straight from the repo, so the UI and the agents
 * share one copy of the truth:
 *
 *   /data/map.json      -> ../data/map.json        (the Cartographer's map)
 *   /runs/<slug>.json   -> ../runs/<slug>.json     (a recorded council run)
 *   /runs/index.json    -> built from ../runs/ on each request
 *
 * Re-run the pipeline and refresh the page; no copying, nothing to keep in sync.
 */
function pipelineData(): Plugin {
  const send = (res: any, status: number, body: string) => {
    res.statusCode = status;
    res.setHeader("Content-Type", "application/json");
    res.setHeader("Cache-Control", "no-store");
    res.end(body);
  };

  return {
    name: "majlis-pipeline-data",
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const url = (req.url ?? "").split("?")[0];

        if (url === "/runs/index.json") {
          const dir = path.join(REPO_ROOT, "runs");
          if (!fs.existsSync(dir)) return send(res, 200, "[]");
          const runs = fs
            .readdirSync(dir)
            .filter((f) => f.endsWith(".json") && f !== "index.json")
            .map((f) => {
              const run = JSON.parse(fs.readFileSync(path.join(dir, f), "utf8"));
              return {
                slug: f.replace(/\.json$/, ""),
                subject: run.subject,
                seconds: run.seconds,
                cost_usd: run.cost_usd,
                units: run.syllabus?.units?.length ?? 0,
              };
            });
          return send(res, 200, JSON.stringify(runs));
        }

        const match = url.match(/^\/(data|runs)\/([\w.-]+\.json)$/);
        if (!match) return next();

        const file = path.join(REPO_ROOT, match[1], match[2]);
        if (!file.startsWith(REPO_ROOT) || !fs.existsSync(file)) {
          return send(res, 404, JSON.stringify({ error: "not found" }));
        }
        return send(res, 200, fs.readFileSync(file, "utf8"));
      });
    },
  };
}

export default defineConfig({
  tanstackStart: {
    // Redirect TanStack Start's bundled server entry to src/server.ts (our SSR error wrapper).
    // nitro/vite builds from this
    server: { entry: "server" },
  },
  vite: {
    plugins: [pipelineData()],
    server: {
      // The council itself runs in Python (pipeline/api.py). Start it with
      //   .venv/bin/python pipeline/api.py
      // and the UI can convene a live run from the browser.
      proxy: {
        "/api": { target: "http://127.0.0.1:8765", changeOrigin: true },
      },
    },
  },
});
