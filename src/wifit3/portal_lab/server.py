from __future__ import annotations

from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
from urllib.parse import urlparse
import webbrowser


_TEMPLATE_DIR = Path(__file__).with_name("templates")
_EVENTS_FILE = Path.home() / ".wifit3" / "portal_lab_events.jsonl"


def _record_test_event() -> None:
    """Persist only a synthetic event; never read or save submitted form values."""
    import json

    _EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "synthetic_portal_form_submitted",
        "stored_secret": False,
    }
    with _EVENTS_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


class _Handler(BaseHTTPRequestHandler):
    def _send_file(self, filename: str, content_type: str) -> None:
        try:
            content = (_TEMPLATE_DIR / filename).read_bytes()
        except OSError:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        files = {
            "/": ("index.html", "text/html"),
            "/index.html": ("index.html", "text/html"),
            "/check.html": ("check.html", "text/html"),
            "/portal.css": ("portal.css", "text/css"),
            "/portal.js": ("portal.js", "application/javascript"),
        }
        entry = files.get(path)
        if entry is None:
            self.send_error(404)
            return
        self._send_file(*entry)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/check.html":
            self.send_error(404)
            return
        # Consume the request body without parsing or retaining submitted form values.
        try:
            length = min(int(self.headers.get("Content-Length", "0")), 8192)
        except ValueError:
            self.send_error(400, "Invalid Content-Length")
            return
        if length:
            self.rfile.read(length)
        _record_test_event()
        self._send_file("check.html", "text/html")

    def log_message(self, format: str, *args) -> None:
        return


class PortalLabServer:
    """Local-only portal lab server with explicit start/stop lifecycle."""

    def __init__(self) -> None:
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return self._server is not None and self._thread is not None and self._thread.is_alive()

    @property
    def url(self) -> str | None:
        if self._server is None:
            return None
        return f"http://127.0.0.1:{self._server.server_port}/"

    def start(self, open_browser: bool = True) -> str:
        if self.running:
            url = self.url
            assert url is not None
            if open_browser:
                webbrowser.open(url)
            return url
        server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        server.daemon_threads = True
        thread = threading.Thread(target=server.serve_forever, name="wifit3-portal-lab", daemon=True)
        self._server, self._thread = server, thread
        thread.start()
        url = self.url
        assert url is not None
        if open_browser:
            webbrowser.open(url)
        return url

    def stop(self) -> None:
        server, thread = self._server, self._thread
        self._server = None
        self._thread = None
        if server is not None:
            server.shutdown()
            server.server_close()
        if thread is not None and thread.is_alive():
            thread.join(timeout=2)
