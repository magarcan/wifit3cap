from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
import webbrowser


_PAGE = b"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Wifit3 - Portal Lab</title>
<style>
body{font:16px system-ui,sans-serif;max-width:42rem;margin:3rem auto;padding:0 1rem;background:#101820;color:#eef}
main{border:1px solid #52606d;border-radius:12px;padding:1.5rem}
.notice{padding:1rem;border-left:4px solid #f0b429;background:#202b35}
</style>
</head>
<body><main>
<h1>Wifit3 · Portal Lab</h1>
<p class="notice"><strong>Entorno de laboratorio.</strong> Esta página está servida únicamente en
127.0.0.1 y no solicita, registra ni verifica contraseñas.</p>
<p>El servidor está activo. La integración con las plantillas del portal se añadirá en una fase posterior.</p>
</main></body></html>"""


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if urlparse(self.path).path not in ("/", "/index.html"):
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(_PAGE)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(_PAGE)

    def do_POST(self) -> None:
        self.send_error(405, "Portal Lab does not accept form submissions")

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
