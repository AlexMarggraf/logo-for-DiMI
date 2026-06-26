#!/usr/bin/env python3

import argparse
import io
import sys
import threading
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from datetime import datetime

from dimi_logo.compiler import compileLogoCode

# ── Global execution state ──────────────────────────────────────────────────
_exec_thread = None
_exec_lock   = threading.Lock()
_movement    = None   # set once Movement is imported and instantiated


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

def timestamp():
    return datetime.now().strftime("%H:%M:%S")


class LogoHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/ping":
            self._respond(200, "pong")
        else:
            self._respond(404, "not found")

    def do_POST(self):
        if self.path == "/execute":
            self._handle_execute()
        elif self.path == "/stop":
            self._handle_stop()
        else:
            self._respond(404, "not found")

    def _handle_execute(self):
        global _exec_thread

        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            self._respond(400, "empty body")
            return

        code = self.rfile.read(length).decode("utf-8")

        print(f"[{timestamp()}] Received code ({len(code)} chars):")
        print(f"{'=' * 60}")
        print(code)
        print(f"{'=' * 60}\n")

        buffer = io.StringIO()
        failed = False

        def run():
            nonlocal failed
            try:
                sys.stdout = buffer
                logoCode = "import math\nimport random\nimport time\n" + compileLogoCode(code)
                exec(logoCode, {"movement": _movement})
            except Exception:
                buffer.write(traceback.format_exc())
                failed = True
            finally:
                sys.stdout = sys.__stdout__

        with _exec_lock:
            t = threading.Thread(target=run, daemon=True)
            _exec_thread = t

        t.start()
        t.join()   # block the HTTP handler until done to return output

        with _exec_lock:
            _exec_thread = None

        output = buffer.getvalue()
        self._respond(400 if failed else 200, output or "run successful")

    def _handle_stop(self):
        global _exec_thread

        print(f"[{timestamp()}] Stop requested.")

        with _exec_lock:
            t = _exec_thread

        if t and t.is_alive():
            import ctypes
            ctypes.pythonapi.PyThreadState_SetAsyncExc(
                ctypes.c_ulong(t.ident),
                ctypes.py_object(SystemExit),
            )
            t.join(timeout=0.5)  # wait for thread to actually die

        if _movement is not None:
            _movement.stop()
            print(f"[{timestamp()}] Zero velocity published.")

        self._respond(200, "stopped")

    def _respond(self, code: int, body: str):
        payload = body.encode("utf-8")
        try:
            self.send_response(code)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            self.wfile.write(payload)
        except BrokenPipeError:
            pass

    def do_OPTIONS(self):
        self._respond(204, "")

    def log_message(self, fmt, *args):
        print(f"[{timestamp()}] {fmt % args}")


def main():
    global _movement

    parser = argparse.ArgumentParser(description="DiMI Logo HTTP Server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8989)
    args = parser.parse_args()

    try:
        import rclpy
        from dimi_logo.movement import Movement
        rclpy.init()
        _movement = Movement()
        
        # Spin in background so ROS 2 callbacks are processed
        _ros_thread = threading.Thread(
            target=rclpy.spin, args=(_movement,), daemon=True
        )
        _ros_thread.start()
        print(f"[{timestamp()}] ROS 2 movement node initialised.")
    except Exception as e:
        print(f"[{timestamp()}] WARNING: could not initialise Movement node: {e}")

    server = ThreadedHTTPServer((args.host, args.port), LogoHandler)
    print(f"[{timestamp()}] DiMI Logo server listening on {args.host}:{args.port}")
    print(f"             GET  /ping     — connectivity check")
    print(f"             POST /execute  — run code and return output")
    print(f"             POST /stop     — halt execution and publish zero velocity\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n[{timestamp()}] Shutting down.")
        if _movement is not None:
            _movement.stop()
            rclpy.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()