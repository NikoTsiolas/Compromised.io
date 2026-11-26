"""A local HTTPS server that plays scripted responses, for testing the fetcher's network safety.

Certificates come from trustme, a throwaway test CA; clients trust it via ``stub.client()``.
"""

import ssl
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx
import trustme


@dataclass
class Reply:
    status: int = 200
    body: bytes = b""
    headers: dict[str, str] = field(default_factory=dict)
    delay: float = 0.0  # seconds before the status line is sent
    chunked: bool = False  # send the body chunked, without Content-Length
    drip: float = 0.0  # seconds between 1-byte chunks (implies chunked)


@dataclass(frozen=True)
class SeenRequest:
    path: str
    headers: dict[str, str]
    at: float


class StubServer:
    def __init__(self):
        self._ca = trustme.CA()
        cert = self._ca.issue_cert("localhost", "127.0.0.1")
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        cert.configure_cert(context)
        self._replies: dict[str, deque[Reply]] = defaultdict(deque)
        self.requests: list[SeenRequest] = []
        stub = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *args):
                pass

            def do_GET(self):
                stub.requests.append(
                    SeenRequest(
                        self.path, {k.lower(): v for k, v in self.headers.items()}, time.monotonic()
                    )
                )
                queue = stub._replies.get(self.path)
                reply = (
                    queue.popleft()
                    if queue and len(queue) > 1
                    else (queue[0] if queue else Reply(404))
                )
                try:
                    self._send(reply)
                except (BrokenPipeError, ConnectionResetError, ssl.SSLError, OSError):
                    pass

            def _send(self, reply: Reply):
                time.sleep(reply.delay)
                self.send_response(reply.status)
                for name, value in reply.headers.items():
                    self.send_header(name, value)
                if reply.chunked or reply.drip:
                    self.send_header("Transfer-Encoding", "chunked")
                    self.end_headers()
                    size = 1 if reply.drip else 16 * 1024
                    for i in range(0, len(reply.body), size):
                        chunk = reply.body[i : i + size]
                        self.wfile.write(b"%x\r\n%s\r\n" % (len(chunk), chunk))
                        self.wfile.flush()
                        time.sleep(reply.drip)
                    self.wfile.write(b"0\r\n\r\n")
                else:
                    self.send_header("Content-Length", str(len(reply.body)))
                    self.end_headers()
                    if reply.status != 304:
                        self.wfile.write(reply.body)

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._server.daemon_threads = True
        self._server.socket = context.wrap_socket(self._server.socket, server_side=True)
        self.port = self._server.server_address[1]
        self._thread = threading.Thread(
            target=self._server.serve_forever, args=(0.05,), daemon=True
        )

    def url(self, path: str, host: str = "localhost") -> str:
        return f"https://{host}:{self.port}{path}"

    def reply(self, path: str, *replies: Reply) -> None:
        """Queue replies for a path; the last one repeats for any further request."""
        self._replies[path].extend(replies)

    def paths(self) -> list[str]:
        return [r.path for r in self.requests]

    def client(self) -> httpx.AsyncClient:
        context = ssl.create_default_context()
        self._ca.configure_trust(context)
        return httpx.AsyncClient(verify=context)

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._server.shutdown()
        self._server.server_close()
