import base64
import ipaddress
import sqlite3
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from visitor_site import make_server, visitor_ip, korean_time


class SiteTest(unittest.TestCase):
    def test_korean_time(self):
        self.assertEqual(korean_time('2026-10-14T18:30:00+00:00'), '2026-10-15 03:30:00')

    def test_logging_and_access(self):
        with tempfile.TemporaryDirectory() as directory:
            database = directory + '/visits.db'
            server = make_server('127.0.0.1', 0, 'test-password-123456', database)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            url = 'http://127.0.0.1:' + str(server.server_port)
            try:
                with urlopen(Request(url + '/', headers={'X-Forwarded-For': '1.2.3.4'})) as response:
                    self.assertIn('IP', response.read().decode())
                with self.assertRaises(HTTPError) as error:
                    urlopen(url + '/admin')
                self.assertEqual(error.exception.code, 401)
                token = base64.b64encode(b'admin:test-password-123456').decode()
                with urlopen(Request(url + '/admin', headers={'Authorization': 'Basic ' + token})) as response:
                    self.assertIn('127.0.0.1', response.read().decode())
                with sqlite3.connect(database) as db:
                    self.assertEqual(db.execute('SELECT ip FROM visits').fetchall(), [('127.0.0.1',)])
            finally:
                server.shutdown()
                server.server_close()
                thread.join()

    def test_proxy_chain(self):
        trusted = (ipaddress.ip_network('127.0.0.0/8'),)
        self.assertEqual(visitor_ip('127.0.0.1', '1.2.3.4, 127.0.0.2', trusted), '1.2.3.4')
        self.assertEqual(visitor_ip('8.8.8.8', '1.2.3.4', trusted), '8.8.8.8')
        self.assertEqual(visitor_ip('127.0.0.1', 'bad', trusted), '127.0.0.1')


if __name__ == '__main__':
    unittest.main()
