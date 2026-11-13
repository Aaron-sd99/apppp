"""SprintDesk: backend deliberadamente monolítico para el laboratorio de arquitectura.
Aviso: SOLO desarrollo local, nunca producción. El estado se pierde al reiniciar.
"""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
FRONT = HERE.parent / "frontend"
# Antipatrón intencional: almacenamiento, reglas y HTTP mezclados aquí.
TASKS = [
    {"id": 1, "title": "Revisar requisitos del portal", "done": False},
    {"id": 2, "title": "Diseñar módulo de reportes", "done": False},
]
NEXT_ID = 3


class Handler(BaseHTTPRequestHandler):
    def reply(self, code, data):
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        pathname = urlparse(self.path).path
        if pathname == "/api/tasks":
            self.reply(200, TASKS)
            return
        if pathname == "/api/health":
            self.reply(200, {"ok": True, "project": "sprintdesk"})
            return
        files = {"/": ("index.html", "text/html"), "/app.js": ("app.js", "text/javascript"),
                 "/style.css": ("style.css", "text/css")}
        if pathname in files:
            name, mime = files[pathname]
            data = (FRONT / name).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mime + "; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        self.reply(404, {"error": "No encontrado"})

    def do_POST(self):
        global NEXT_ID
        if urlparse(self.path).path != "/api/tasks":
            self.reply(404, {"message": "ruta no existe"})
            return
        try:
            length = min(int(self.headers.get("Content-Length", "0")), 65536)
            body = json.loads(self.rfile.read(length))
            title = str(body.get("title", "")).strip()
            if not title:
                self.reply(400, {"error": "Se requiere título"})
                return
        except (ValueError, TypeError, AttributeError):
            self.reply(400, {"message": "Datos inválidos"})
            return
        new = {"id": NEXT_ID, "title": title, "done": False}
        NEXT_ID += 1
        TASKS.append(new)
        self.reply(201, new)


def run_server(port=None):
    port = int(port or os.environ.get("SPRINTDESK_PORT", "8765"))
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"SprintDesk http://127.0.0.1:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    run_server()
