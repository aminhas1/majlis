"""Local API so the UI can convene the council on a subject and watch it work.

  POST /api/run      {"subject": "..."}  -> {"id": ...}; starts a run in a thread
  GET  /api/stream/<id>                  -> server-sent events, one per agent step
  GET  /api/health                       -> {"ok": true}

Runs on this machine, with the key from .env. A run costs about $0.80 and takes
a few minutes; the finished syllabus is written to runs/<slug>.json like any
other, so the recorded view and the live view show the same thing.

Usage: .venv/bin/python pipeline/api.py     (then `npm run dev` in web/)
"""

import json
import queue
import sys
import threading
import traceback
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import anthropic  # noqa: E402

from cartographer import MAP_PATH, ROOT, SHELF_PATH, load_env  # noqa: E402
from council import Run, council  # noqa: E402

PORT = 8765
MAX_CONCURRENT = 1  # a run is a few dollars an hour of tokens; one at a time

runs: dict[str, queue.Queue] = {}
lock = threading.Lock()


def start_run(subject_name: str) -> str:
    subjects = json.loads(MAP_PATH.read_text(encoding="utf-8"))["subjects"]
    subject = next((s for s in subjects if s["name"] == subject_name), None)
    if subject is None:
        raise KeyError(subject_name)

    run_id = uuid.uuid4().hex[:8]
    events: queue.Queue = queue.Queue()
    runs[run_id] = events

    def work():
        client = anthropic.Anthropic()
        books = {b["id"]: b for b in json.loads(SHELF_PATH.read_text(encoding="utf-8"))}
        run = Run(subject, on_event=events.put)
        try:
            syllabus = council(client, run, books)
            path = run.save(syllabus)
            events.put({"kind": "finished", "agent": "audit", "at": round(run.events[-1]["at"], 1),
                        "text": f"Syllabus written to {path.name}",
                        "slug": path.stem, "cost_usd": round(run.cost, 3)})
        except Exception as e:  # a failed run should say so in the UI, not hang
            traceback.print_exc()
            events.put({"kind": "failed", "agent": "audit", "at": 0, "text": str(e)[:300]})
        finally:
            events.put(None)

    threading.Thread(target=work, daemon=True).start()
    return run_id


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):  # quieter console
        print(f"[api] {fmt % args}")

    def _json(self, status: int, payload: dict):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/health":
            return self._json(200, {"ok": True, "active": len(runs)})
        if self.path.startswith("/api/stream/"):
            return self.stream(self.path.rsplit("/", 1)[-1])
        self._json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/api/run":
            return self._json(404, {"error": "not found"})
        with lock:
            if len(runs) >= MAX_CONCURRENT:
                return self._json(429, {"error": "A council is already sitting. Wait for it to finish."})
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
            try:
                run_id = start_run(body.get("subject", ""))
            except KeyError:
                return self._json(404, {"error": f"No territory called {body.get('subject')!r}"})
        self._json(200, {"id": run_id})

    def stream(self, run_id: str):
        events = runs.get(run_id)
        if events is None:
            return self._json(404, {"error": "unknown run"})
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        try:
            while True:
                event = events.get()
                if event is None:
                    self.wfile.write(b"event: end\ndata: {}\n\n")
                    self.wfile.flush()
                    break
                self.wfile.write(f"data: {json.dumps(event)}\n\n".encode())
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass  # the viewer navigated away; the run carries on
        finally:
            runs.pop(run_id, None)


def main():
    load_env()
    if not (ROOT / ".env").exists():
        print("No .env found; the council needs ANTHROPIC_API_KEY.")
    print(f"Council API on http://localhost:{PORT} — the UI proxies /api to it")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
