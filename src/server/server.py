#!/usr/bin/env python3

import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime


def timestamp():
    return datetime.now().strftime("%H:%M:%S")


class LogoHandler(BaseHTTPRequestHandler):

    # GET /ping - connectivity check from the web editor
    def do_GET(self):
        if self.path == "/ping":
            self._respond(200, "pong")
        else:
            self._respond(404, "not found")

    # POST /execute - receive Logo code and process it
    def do_POST(self):
        if self.path != "/execute":
            self._respond(404, "not found")
            return

        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            self._respond(400, "empty body")
            return

        logo_code = self.rfile.read(length).decode("utf-8")

        print(f"[{timestamp()}] Received Logo code ({len(logo_code)} chars):")
        print(f"{'=' * 60}")
        print(logo_code)
        print(f"{'=' * 60}\n")

        # TODO: pass logo_code to the compiler, then execute the result
        # compiled = compile_logo(logo_code)
        # exec(compiled)

        self._respond(200, "OK — code received and printed")

    # Helpers
    def _respond(self, code: int, body: str):
        payload = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))

        # Allow requests from the web editor running on any origin
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        """Pre-flight CORS request from browser."""
        self._respond(204, "")

    def log_message(self, fmt, *args):
        """Override default logging to use our timestamp format."""
        print(f"[{timestamp()}] {fmt % args}")


def main():
    parser = argparse.ArgumentParser(description="DiMI Logo HTTP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Listen address (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8080, help="Listen port (default: 8080)")
    args = parser.parse_args()

    server = HTTPServer((args.host, args.port), LogoHandler)
    print(f"[{timestamp()}] DiMI Logo server listening on {args.host}:{args.port}")
    print(f"[{timestamp()}] Endpoints:")
    print(f"             GET  /ping     — connectivity check")
    print(f"             POST /execute  — receive and print Logo code")
    print(f"             Press Ctrl+C to stop.\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n[{timestamp()}] Shutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
