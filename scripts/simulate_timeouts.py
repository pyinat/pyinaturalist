#!/usr/bin/env python
"""Script to simulate a slow connection speed to reproduce timeout issues.
- Runs a local HTTP server that accepts (and discards) multipart uploads
- Wraps urllib3's socket with a client-side throttle at 100 KB/s
- Uploads a 1 MB file via ClientSession (~10 seconds at that rate)
"""

import contextlib
import io
import logging
import os
import socket
import threading
import time
from collections.abc import Generator
from http.server import BaseHTTPRequestHandler, HTTPServer

import urllib3.util.connection
from requests_ratelimiter import InMemoryBucket

from pyinaturalist import enable_logging
from pyinaturalist.session import ClientSession

logger = logging.getLogger(__name__)

UPLOAD_RATE_BYTES_PER_SEC = 100 * 1024  # 100 KB/s
UPLOAD_SIZE_BYTES = 1024 * 1024  # 1 MB
CHUNK_SIZE = 4 * 1024  # 4 KB send chunks


class ThrottledSocket:
    """Wraps a socket.socket, overriding sendall() to enforce a rate limit and detect timeouts.

    ``write_timeout`` is the maximum number of seconds allowed for the entire send of large data.
    It is supplied explicitly rather than read from sock.gettimeout() because urllib3 uses blocking
    sockets (timeout=None) during the send phase; the timeout is managed at a higher level.
    """

    def __init__(self, sock: socket.socket, rate_bps: int, write_timeout: int | None):
        self._sock = sock
        self._rate_bps = rate_bps
        self._write_timeout = write_timeout
        self._bytes_sent = 0
        self._start_time = time.monotonic()
        self._last_print_time = self._start_time

    def sendall(self, data: bytes) -> None:
        # Skip the timeout check and progress printing for small header-only sends
        if len(data) < CHUNK_SIZE:
            self._sock.sendall(data)
            return

        offset = 0
        while offset < len(data):
            chunk = data[offset : offset + CHUNK_SIZE]
            chunk_start = time.monotonic()

            self._sock.sendall(chunk)
            offset += len(chunk)
            self._bytes_sent += len(chunk)

            elapsed = time.monotonic() - chunk_start
            time.sleep(max(0.0, len(chunk) / self._rate_bps - elapsed))

            now = time.monotonic()
            # Check if we've exceeded the configured write timeout
            total_elapsed = now - self._start_time
            if self._write_timeout is not None and total_elapsed > self._write_timeout:
                raise socket.timeout('write operation timed out')

            # Print progress roughly every second
            if now - self._last_print_time >= 1.0:
                kb_sent = self._bytes_sent / 1024
                kb_total = UPLOAD_SIZE_BYTES / 1024
                rate_kbs = self._bytes_sent / total_elapsed / 1024
                print(
                    f'  {kb_sent:.1f} KB / {kb_total:.1f} KB  {total_elapsed:.1f}s  {rate_kbs:.1f} KB/s'
                )
                self._last_print_time = now

    def __getattr__(self, name: str):
        return getattr(self._sock, name)


class UploadHandler(BaseHTTPRequestHandler):
    """HTTP request handler that accepts and discards multipart POST uploads."""

    def do_POST(self) -> None:
        remaining = int(self.headers.get('Content-Length', 0))
        while remaining > 0:
            chunk = self.rfile.read(min(CHUNK_SIZE, remaining))
            if not chunk:
                break
            remaining -= len(chunk)

        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK')

    def log_message(self, fmt: str, *args) -> None:
        logger.debug(fmt, *args)


def start_upload_server() -> HTTPServer:
    """Create a threading HTTP server on a random OS-assigned port and start it in a daemon thread."""
    server = HTTPServer(('127.0.0.1', 0), UploadHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def make_test_session(write_timeout: int) -> ClientSession:
    """Create a ClientSession with no disk writes and no rate-limit interference."""
    return ClientSession(
        cache_file=':memory:',
        ratelimit_path=None,
        bucket_class=InMemoryBucket,
        per_second=10_000,
        write_timeout=write_timeout,
        max_retries=0,
    )


@contextlib.contextmanager
def patch_throttled_socket(
    write_timeout: int, rate_bps: int = UPLOAD_RATE_BYTES_PER_SEC
) -> Generator[None, None, None]:
    """Context manager that monkey-patches urllib3's create_connection to use a ThrottledSocket.

    ``write_timeout`` is passed to ThrottledSocket so it knows when to raise a timeout error.
    urllib3 uses blocking sockets during the send phase so we cannot read the timeout from
    sock.gettimeout(); instead we supply it explicitly here.
    """
    original = urllib3.util.connection.create_connection

    def patched(address, timeout=None, source_address=None, socket_options=None):
        sock = original(address, timeout, source_address, socket_options)
        return ThrottledSocket(sock, rate_bps=rate_bps, write_timeout=write_timeout)

    urllib3.util.connection.create_connection = patched
    try:
        yield
    finally:
        urllib3.util.connection.create_connection = original


def run_upload_scenario(url: str, write_timeout: int, label: str) -> None:
    """Run a single upload scenario and print the result."""
    print(f'\n--- {label} ---')
    session = make_test_session(write_timeout)
    file_data = io.BytesIO(os.urandom(UPLOAD_SIZE_BYTES))

    start = time.monotonic()
    try:
        with patch_throttled_socket(write_timeout=write_timeout):
            response = session.request(
                method='POST', url=url, files=file_data, raise_for_status=False
            )
        elapsed = time.monotonic() - start
        print(f'\nSUCCESS  status={response.status_code}  elapsed={elapsed:.2f}s')
    except Exception as e:
        elapsed = time.monotonic() - start
        print(f'\nFAILED after {elapsed:.2f}s: {type(e).__name__}: {e}')


def main() -> None:
    enable_logging('DEBUG')
    server = start_upload_server()
    host, port = server.server_address  # type: ignore[misc]
    url = f'http://{host}:{port}/upload'  # type: ignore[str-bytes-safe]
    print(f'Upload server started on {url}')

    run_upload_scenario(url, write_timeout=60, label='write_timeout=60s')
    run_upload_scenario(url, write_timeout=5, label='write_timeout=5s')

    server.shutdown()


if __name__ == '__main__':
    main()
