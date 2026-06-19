import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

HOST = "localhost"
PORT = 3000

STORAGE_DIR = "storage"
DATA_FILE = os.path.join(STORAGE_DIR, "data.json")
TEMPLATES_DIR = "templates"
STATIC_DIR = "static"


# ---------- JINJA2 ----------
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))


# ---------- HELPERS ----------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def save_data(data):
    os.makedirs(STORAGE_DIR, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def render(template_name, **kwargs):
    template = env.get_template(template_name)
    return template.render(**kwargs).encode("utf-8")


# ---------- SERVER ----------
class SimpleHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        # home page
        if self.path == "/" or self.path == "/index":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(render("index.html"))
            return

        # message page
        if self.path == "/message":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(render("message.html"))
            return

        # read messages (Jinja2)
        if self.path == "/read":
            data = load_data()
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(render("read.html", messages=data))
            return

        # static files
        if self.path.startswith("/static/"):
            file_path = self.path.lstrip("/")
            if os.path.exists(file_path):
                self.send_response(200)
                if file_path.endswith(".css"):
                    self.send_header("Content-type", "text/css")
                elif file_path.endswith(".png"):
                    self.send_header("Content-type", "image/png")
                else:
                    self.send_header("Content-type", "application/octet-stream")
                self.end_headers()
                with open(file_path, "rb") as f:
                    self.wfile.write(f.read())
                return

        # 404
        self.send_response(404)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(render("error.html"))

    def do_POST(self):
        if self.path == "/message":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            form_data = parse_qs(body)

            username = form_data.get("username", [""])[0]
            message = form_data.get("message", [""])[0]

            if username and message:
                data = load_data()

                timestamp = str(datetime.now())

                data[timestamp] = {
                    "username": username,
                    "message": message
                }

                save_data(data)

            self.send_response(303)
            self.send_header("Location", "/message")
            self.end_headers()


def run():
    server = HTTPServer((HOST, PORT), SimpleHandler)
    print(f"Server running on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    run()
