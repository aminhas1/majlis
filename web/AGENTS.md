# Working in this repo

`web/` is the UI (React + TanStack Start + Tailwind, originally designed in Lovable and now
maintained here). The pipeline that feeds it lives one level up:

- `pipeline/cartographer.py` writes `data/map.json`
- `pipeline/council.py` writes `runs/<subject>.json`

The dev server serves those two folders straight from the repo root (see `vite.config.ts`),
so the UI always shows what the agents actually produced. Never hardcode territory data,
counts, or scores in components: if a number isn't in the pipeline's output, it doesn't ship.
