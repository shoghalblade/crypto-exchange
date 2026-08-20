#!/usr/bin/env python3
"""FixedFloat API proxy + static site server. Stdlib only."""
import json, hmac, hashlib, os, sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.request import Request, urlopen
from urllib.error import HTTPError

API_KEY = "fdhGLulaU7vqldU3qhBFwPKA8KVrzxeBxo2jq0Uc"
API_SECRET = "6eiNSm1boLgom9Rgc0NFSGqkwl6bdAkG39eciFLP"
API_BASE = "https://ff.io/api/v2"
HEADERS = {
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Origin': 'https://ff.io',
    'Referer': 'https://ff.io/',
}

def sign(data: str) -> str:
    return hmac.new(API_SECRET.encode(), data.encode(), hashlib.sha256).hexdigest()

def api_post(endpoint: str, payload: dict = None) -> dict:
    body = json.dumps(payload or {})
    h = {**HEADERS, 'X-API-KEY': API_KEY, 'X-API-SIGN': sign(body)}
    req = Request(f"{API_BASE}/{endpoint}", data=body.encode(), headers=h, method='POST')
    with urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=os.path.dirname(os.path.abspath(__file__)), **kw)

    def do_GET(self):
        if self.path == "/": self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        routes = {"currencies": "ccies", "price": "price", "create": "create", "order": "order"}
        endpoint = routes.get(self.path.lstrip("/"))
        if not endpoint:
            self.send_error(404); return
        try:
            result = api_post(endpoint, body)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        except HTTPError as e:
            err = e.read().decode() if e.fp else str(e)
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(err.encode())
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    print(f"🚀 http://localhost:{port}")
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
