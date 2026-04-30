#!/usr/bin/env python3

import argparse
import io
import sys
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime

from compiler import compileLogoCode


def timestamp():
    return datetime.now().strftime("%H:%M:%S")


class LogoHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/ping":
            self._respond(200, "pong")
        else:
            self._respond(404, "not found")

    def do_POST(self):
        if self.path != "/execute":
            self._respond(404, "not found")
            return

        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            self._respond(400, "empty body")
            return

        code = self.rfile.read(length).decode("utf-8")

        print(f"[{timestamp()}] Received code ({len(code)} chars):")
        print(f"{'=' * 60}")
        print(code)
        print(f"{'=' * 60}\n")

        failed = False

        # Capture stdout from exec into a string
        buffer = io.StringIO()
        try:
            sys.stdout = buffer
            # TODO: replace exec(code) with exec(compile_logo(code))
            exec(compileLogoCode(code), {})
            # in case of compile error: self._respond(400, "Compilation failed")
        except Exception:
            buffer.write(traceback.format_exc())
            failed = True
        finally:
            sys.stdout = sys.__stdout__

        output = buffer.getvalue()

        self._respond(400 if failed else 200, output or "run successful")

    def _respond(self, code: int, body: str):
        payload = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        self._respond(204, "")

    def log_message(self, fmt, *args):
        print(f"[{timestamp()}] {fmt % args}")


def main():
    parser = argparse.ArgumentParser(description="DiMI Logo HTTP Server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8989)
    args = parser.parse_args()

    server = HTTPServer((args.host, args.port), LogoHandler)
    print(f"[{timestamp()}] DiMI Logo server listening on {args.host}:{args.port}")
    print(f"             GET  /ping     ? connectivity check")
    print(f"             POST /execute  ? run code and return output\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n[{timestamp()}] Shutting down.")
        server.server_close()


if __name__ == "__main__":
    main()