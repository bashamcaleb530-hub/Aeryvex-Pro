"""Exercise actual HTTP requests without requiring a downloaded Ollama model."""
import copy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from ai_factory import core, genre3d, providers


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers['Content-Length']))
        self.server.requests.append((self.path, json.loads(body)))
        if self.server.delay:
            time.sleep(self.server.delay)
        self.send_response(self.server.status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        try:
            self.wfile.write(self.server.reply)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, *args):
        pass


class OllamaTests(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.server.reply = b'{}'
        self.server.status = 200
        self.server.delay = 0
        self.server.requests = []
        self.thread = threading.Thread(target=self.server.serve_forever,
                                       kwargs={'poll_interval': 0.01}, daemon=True)
        self.thread.start()
        self.addCleanup(self.close_server)
        self.env = patch.dict(os.environ, {'FACTORY_OLLAMA_URL': 'http://127.0.0.1:' + str(self.server.server_port),
                                          'FACTORY_MODEL': 'local-test-model'})
        self.env.start()
        self.addCleanup(self.env.stop)

    def close_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=1)

    def reply(self, config):
        self.server.reply = json.dumps({'message': {'role': 'assistant',
                                                  'content': json.dumps(config)}}).encode()

    def test_2d_request_is_real_nonstream_json_with_full_current(self):
        before = copy.deepcopy(providers.DEFAULT)
        self.reply(dict(before, coins=8))
        result = providers.OllamaProvider().propose('8 coins', before)
        self.assertEqual(result, {'coins': 8, 'enemies': 0, 'speed': 220, 'color': 'green'})
        self.assertEqual(before, providers.DEFAULT)
        path, body = self.server.requests[0]
        self.assertEqual(path, '/api/chat')
        self.assertEqual(body['model'], 'local-test-model')
        self.assertIs(body['stream'], False)
        self.assertEqual(body['format'], 'json')
        user = json.loads(body['messages'][1]['content'])
        self.assertEqual(user, {'current': before, 'request': '8 coins'})

    def test_shared_api_preserves_extended_3d_fields_and_uses_validator(self):
        before = copy.deepcopy(genre3d.DEFAULT)
        self.reply(dict(before, town=True))
        result = providers.OllamaProvider().propose_config('add a town', before, genre3d.validate,
                                                         'bounded 3D RPG config')
        self.assertTrue(result['town'])
        self.assertEqual(result['missions'], 3)
        self.assertEqual(result['mission_length'], 1)
        self.assertEqual(before, genre3d.DEFAULT)
        self.assertIn('bounded 3D RPG config', self.server.requests[0][1]['messages'][0]['content'])

    def test_legacy_shape_cannot_drop_existing_campaign_fields(self):
        self.reply(genre3d.BASE)
        with self.assertRaisesRegex(ValueError, 'missing|Missing|preserv'):
            providers.OllamaProvider().propose_config('faster', genre3d.DEFAULT, genre3d.validate,
                                                     'bounded 3D RPG config')

    def test_response_shapes_and_invalid_json_are_actionable(self):
        cases = [b'not json', b'[]', b'{}', b'{"message":null}',
                 b'{"message":{"content":{}}}', b'{"message":{"content":"not json"}}',
                 b'{"message":{"content":"[]"}}', b'\xff']
        for reply in cases:
            with self.subTest(reply=reply):
                self.server.reply = reply
                with self.assertRaisesRegex(ValueError, 'Ollama'):
                    providers.OllamaProvider().propose('faster', providers.DEFAULT)

    def test_model_and_http_errors_have_clear_value_errors(self):
        for status, reply in [(200, b'{"error":"model not found"}'),
                              (503, b'{"error":"service unavailable"}')]:
            with self.subTest(status=status):
                self.server.status, self.server.reply = status, reply
                with self.assertRaisesRegex(ValueError, 'Ollama'):
                    providers.OllamaProvider().propose('faster', providers.DEFAULT)

    def test_bounded_response_and_prompt(self):
        self.server.reply = b' ' * 65537
        with self.assertRaisesRegex(ValueError, 'Ollama.*(large|limit|64)'):
            providers.OllamaProvider().propose('faster', providers.DEFAULT)
        count = len(self.server.requests)
        with self.assertRaisesRegex(ValueError, 'prompt|Prompt'):
            providers.OllamaProvider().propose('x' * 8001, providers.DEFAULT)
        self.assertEqual(len(self.server.requests), count)

    def test_unavailable_and_timed_out_server_are_blocked(self):
        # Closed listening socket gives a real refused connection.
        unused = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        port = unused.server_port
        unused.server_close()
        with patch.dict(os.environ, {'FACTORY_OLLAMA_URL': 'http://127.0.0.1:' + str(port)}):
            with self.assertRaisesRegex(ValueError, 'Ollama.*(unavailable|connect|reach)'):
                providers.OllamaProvider().propose('faster', providers.DEFAULT)
        self.server.delay = 0.15
        self.reply(providers.DEFAULT)
        with self.assertRaisesRegex(ValueError, 'Ollama.*(timeout|timed out|unavailable)'):
            providers.OllamaProvider(timeout=0.02).propose('faster', providers.DEFAULT)

    def test_invalid_model_config_does_not_change_project_or_execute_text(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'Demo'
            core.new(path, 'Demo', '5 coins')
            before = (path / 'bible.json').read_bytes()
            self.reply(dict(providers.DEFAULT, code='__import__("os").system("false")'))
            with self.assertRaises(ValueError):
                core.add(path, 'faster', 'ollama')
            self.assertEqual((path / 'bible.json').read_bytes(), before)
            self.assertFalse((path / 'checkpoints/0002.json').exists())

    def test_factory_3d_provider_updates_only_validated_data(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'RPG'
            core.new(path,'RPG','a 3D RPG')
            self.reply(dict(genre3d.DEFAULT,town=True))
            result=core.add(path,'add a town','ollama')
            self.assertTrue(result['config']['town'])
            self.assertEqual(result['config']['missions'],3)
            self.assertEqual(result['history'][-1]['provider'],'ollama')

    def test_duplicate_keys_and_nonfinite_numbers_rejected(self):
        for content in ('{"coins":5,"coins":8,"enemies":0,"speed":220,"color":"green"}',
                        '{"coins":5,"enemies":0,"speed":NaN,"color":"green"}'):
            with self.subTest(content=content):
                self.server.reply = json.dumps({'message': {'content': content}}).encode()
                with self.assertRaisesRegex(ValueError, 'Ollama'):
                    providers.OllamaProvider().propose('faster', providers.DEFAULT)


if __name__ == '__main__':
    unittest.main()
