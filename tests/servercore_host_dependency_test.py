"""Missing/stale Host socket binds must not be healthy or persist forever."""
import http.client
import json
from pathlib import Path
import socket
import sys
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import servercore_bounded_host_receiver as receiver
from http.server import ThreadingHTTPServer


class HostDependencies(unittest.TestCase):
    def test_absent_regular_symlink_and_unlistened_socket_are_unavailable(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'regular').write_text('not a socket')
            (root / 'link').symlink_to(root / 'regular')
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                sock.bind(str(root / 'dead'))
                result = receiver.host_dependency_status({n: root / n for n in ['absent', 'regular', 'link', 'dead']})
            self.assertEqual(result, dict.fromkeys(result, False))

    def test_socket_probe_is_empty_object_not_a_command(self):
        with tempfile.TemporaryDirectory() as d:
            path = str(Path(d) / 'rpc')
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
                listener.bind(path)
                listener.listen(1)
                seen = []
                def handle():
                    with listener.accept()[0] as client:
                        seen.append(client.recv(4096))
                        client.sendall(b'{"ok":false,"error":"REQUEST_INVALID"}\n')
                thread = threading.Thread(target=handle)
                thread.start()
                self.assertEqual(receiver.host_dependency_status({'host_writer': path}), {'host_writer': True})
                thread.join(2)
                self.assertEqual(seen, [b'{}\n'])

    def test_health_fails_when_either_required_dependency_is_missing(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), receiver.make_handler({}))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            for writer, sink in [(True, True), (False, True), (True, False), (False, False)]:
                with patch.object(receiver, 'host_dependency_status', return_value={'host_writer': writer, 'result_sink': sink}):
                    conn = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=2)
                    conn.request('GET', '/healthz')
                    response = conn.getresponse()
                    self.assertEqual(response.status, 200 if writer and sink else 503)
                    self.assertEqual(json.loads(response.read())['ok'], writer and sink)
                    conn.close()
        finally:
            server.shutdown()
            server.server_close()

    def run_watch(self, outcomes):
        server = Mock()
        stop = Mock()
        stop.wait.side_effect = [False] * len(outcomes) + [True]
        clock = iter(range(len(outcomes)))
        receiver.watch_host_dependencies(server, stop, interval=1, grace_seconds=2,
                                         ready=Mock(side_effect=outcomes), monotonic=lambda: next(clock))
        return server

    def test_sustained_loss_shuts_down_for_compose_rebind(self):
        server = self.run_watch([False, False, False])
        self.assertTrue(server.host_dependency_shutdown)
        server.shutdown.assert_called_once()

    def test_transient_loss_and_recovery_does_not_restart(self):
        server = self.run_watch([False, True, False, False, True])
        server.shutdown.assert_not_called()


if __name__ == '__main__':
    unittest.main()
