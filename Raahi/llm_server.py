#!/usr/bin/env python3
"""Raahi LLM endpoint — run this on your own PC, point the deployed app at it.

The deployed Django app already reads its LLM address from the OLLAMA_BASE_URL
environment variable and talks Ollama's /api/chat protocol (see
Backend/home/helper.py: ask_ollama_sync). This script speaks that exact
protocol, so the deployed app needs ZERO code changes — only its env var
points here instead of at localhost.

What it does:
  * Listens on your PC (default port 11435) and forwards chat requests to
    your local Ollama (default http://127.0.0.1:11434).
  * Exposes an Ollama-compatible POST /api/chat, a GET /api/tags
    passthrough, and a GET /healthz for uptime checks.
  * Stdlib only — no pip install, runs with any python3.

Usage on your PC:
  1. Make sure Ollama is running:  ollama list
  2. Start this server:            python3 llm_server.py
     (options: --port 11435 --upstream http://127.0.0.1:11434
               --model smallthinker:3b-preview-q4_K_M)
  3. Expose it for the demo, e.g.: cloudflared tunnel --url http://localhost:11435
     (or: ngrok http 11435)
  4. In the deployed app's environment set:
       OLLAMA_BASE_URL=https://<your-tunnel-url>
     Everything else stays the same.

Security note: this is for a short interview demo. Anyone with the tunnel
URL can call it, so stop the tunnel (and this script) when the demo is over.
"""

import argparse
import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

CONNECT_TIMEOUT = 10
READ_TIMEOUT = 600


class Config:
    upstream = os.environ.get("RAAHI_LLM_UPSTREAM", "http://127.0.0.1:11434")
    model_override = os.environ.get("RAAHI_LLM_MODEL", "")
    port = int(os.environ.get("RAAHI_LLM_PORT", "11435"))


def _forward_chat(payload: dict) -> tuple[int, dict]:
    """Forward one chat request to the local Ollama. Returns (status, body)."""
    model = Config.model_override or payload.get("model", "")
    body = {
        "model": model,
        "messages": payload.get("messages", []),
        # The Django app always uses stream:false; even if a client asks
        # for streaming, answer in one JSON object (fine for a demo).
        "stream": False,
    }
    if "think" in payload:
        body["think"] = payload["think"]
    data = json.dumps(body).encode()

    req = urllib.request.Request(
        Config.upstream.rstrip("/") + "/api/chat",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=READ_TIMEOUT) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read().decode())
        except Exception:
            return exc.code, {"error": f"upstream HTTP {exc.code}"}
    except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
        return 502, {"error": f"local Ollama not reachable at {Config.upstream}: {exc}"}


def _passthrough_tags() -> tuple[int, dict]:
    try:
        with urllib.request.urlopen(
            Config.upstream.rstrip("/") + "/api/tags", timeout=CONNECT_TIMEOUT
        ) as resp:
            return resp.status, json.loads(resp.read().decode())
    except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
        return 502, {"error": f"local Ollama not reachable at {Config.upstream}: {exc}"}
    except urllib.error.HTTPError as exc:
        return exc.code, {"error": f"upstream HTTP {exc.code}"}


class Handler(BaseHTTPRequestHandler):
    server_version = "RaahiLLM/1.0"

    def _send(self, status: int, body: dict) -> None:
        raw = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        try:
            self.wfile.write(raw)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _read_json(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}

    def do_GET(self) -> None:  # noqa: N802 (http.server naming)
        if self.path == "/healthz":
            self._send(200, {"status": "ok", "upstream": Config.upstream})
        elif self.path == "/api/tags":
            status, body = _passthrough_tags()
            self._send(status, body)
        else:
            self._send(404, {"error": "unknown endpoint (try /api/chat, /api/tags, /healthz)"})

    def do_POST(self) -> None:  # noqa: N802 (http.server naming)
        if self.path != "/api/chat":
            self._send(404, {"error": "unknown endpoint (try /api/chat)"})
            return
        payload = self._read_json()
        if not payload.get("messages"):
            self._send(400, {"error": "missing 'messages' (Ollama /api/chat format expected)"})
            return
        status, body = _forward_chat(payload)
        if status == 200:
            content = ((body.get("message") or {}).get("content") or "").strip()
            if not content:
                self._send(502, {"error": "upstream returned an empty reply"})
                return
        self._send(status, body)
        print(f"POST /api/chat -> {status} (model={payload.get('model', '')})", flush=True)

    def log_message(self, fmt: str, *args) -> None:  # quieter default logging
        print(f"{self.address_string()} {fmt % args}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Raahi demo LLM endpoint (Ollama-compatible).")
    parser.add_argument("--port", type=int, default=Config.port)
    parser.add_argument("--upstream", default=Config.upstream)
    parser.add_argument("--model", default=Config.model_override,
                        help="Force a model name instead of the client's (empty = pass through).")
    args = parser.parse_args()
    Config.port = args.port
    Config.upstream = args.upstream.rstrip("/")
    Config.model_override = args.model

    server = ThreadingHTTPServer(("127.0.0.1", Config.port), Handler)
    print(f"Raahi LLM endpoint on http://127.0.0.1:{Config.port} -> {Config.upstream}", flush=True)
    print("Expose with e.g.  cloudflared tunnel --url "
          f"http://localhost:{Config.port}  (Ctrl+C to stop)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.", flush=True)


if __name__ == "__main__":
    main()
