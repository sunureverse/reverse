"""Small visitor log site. Run with ADMIN_PASSWORD set."""
import base64
import binascii
import hmac
import html
import ipaddress
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# Cloudflare's published proxy ranges: https://www.cloudflare.com/ips/
# Used only for Render deployments; never trust an arbitrary forwarded header.
CLOUDFLARE_PROXIES = tuple(ipaddress.ip_network(value) for value in (
    '173.245.48.0/20', '103.21.244.0/22', '103.22.200.0/22',
    '103.31.4.0/22', '141.101.64.0/18', '108.162.192.0/18',
    '190.93.240.0/20', '188.114.96.0/20', '197.234.240.0/22',
    '198.41.128.0/17', '162.158.0.0/15', '104.16.0.0/13',
    '104.24.0.0/14', '172.64.0.0/13', '131.0.72.0/22',
    '2400:cb00::/32', '2606:4700::/32', '2803:f800::/32',
    '2405:b500::/32', '2405:8100::/32', '2a06:98c0::/29',
    '2c0f:f248::/32',
))


def proxy_networks(configured, render=False):
    networks = tuple(ipaddress.ip_network(value.strip()) for value in configured.split(',') if value.strip())
    if render:
        networks += tuple(ipaddress.ip_network(value) for value in ('127.0.0.1/32', '::1/128', '10.0.0.0/8'))
        networks += CLOUDFLARE_PROXIES
    return networks


def korean_time(value):
    return datetime.fromisoformat(value).astimezone(timezone(timedelta(hours=9))).strftime('%Y-%m-%d %H:%M:%S')


def visitor_ip(peer, forwarded, trusted):
    address = ipaddress.ip_address(peer)
    if not any(address in network for network in trusted):
        return str(address)
    try:
        chain = [ipaddress.ip_address(part.strip()) for part in forwarded.split(',')]
    except ValueError:
        return str(address)
    for candidate in reversed(chain):
        if not any(candidate in network for network in trusted):
            return str(candidate)
    return str(address)


def make_server(host, port, password, database, trusted=()):
    if len(password) < 16:
        raise ValueError('ADMIN_PASSWORD는 16자 이상으로 설정하세요.')
    database = Path(database)
    database.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database) as db:
        db.execute('CREATE TABLE IF NOT EXISTS visits (id INTEGER PRIMARY KEY, time TEXT NOT NULL, ip TEXT NOT NULL)')
    database.chmod(0o600)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Do not expose visitor IPs or credentials in console logs.

        def respond(self, status, body, challenge=False):
            content = body.encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'none'; style-src 'unsafe-inline'; frame-ancestors 'none'")
            if challenge:
                self.send_header('WWW-Authenticate', 'Basic realm="Visitor logs", charset="UTF-8"')
            self.end_headers()
            self.wfile.write(content)

        def do_GET(self):
            path = self.path.split('?', 1)[0]
            if path == '/health':
                self.respond(200, 'ok')
                return
            if path == '/admin':
                authorized = False
                header = self.headers.get('Authorization', '')
                if header.startswith('Basic '):
                    try:
                        credentials = base64.b64decode(header[6:], validate=True)
                        authorized = hmac.compare_digest(credentials, ('admin:' + password).encode())
                    except (ValueError, binascii.Error):
                        pass
                if not authorized:
                    self.respond(401, '관리자 로그인이 필요합니다.', True)
                    return
                with sqlite3.connect(database) as db:
                    rows = db.execute('SELECT time, ip FROM visits ORDER BY id DESC LIMIT 500').fetchall()
                table = ''.join('<tr><td>' + korean_time(t) + '</td><td>' + html.escape(ip) + '</td></tr>' for t, ip in rows)
                self.respond(200, page('방문 기록', '<p>최근 30일 기록 중 최신 500건 · 시간은 한국 시간(KST, UTC+9) 기준입니다.</p><table><tr><th>접속 시간</th><th>IP 주소</th></tr>' + table + '</table>'))
                return
            if path != '/':
                self.respond(404, '페이지를 찾을 수 없습니다.')
                return
            now = datetime.now(timezone.utc)
            ip = visitor_ip(self.client_address[0], self.headers.get('X-Forwarded-For', ''), trusted)
            with sqlite3.connect(database) as db:
                db.execute('DELETE FROM visits WHERE time < ?', ((now - timedelta(days=30)).isoformat(),))
                db.execute('INSERT INTO visits(time, ip) VALUES (?, ?)', (now.isoformat(), ip))
            self.respond(200, page('환영합니다', '<p>방문해 주셔서 감사합니다.</p><p class="notice">이 사이트는 접속 IP 주소와 시간을 기록합니다. 기록은 관리자만 열람하며 최대 30일간 보관됩니다.</p>'))

    return ThreadingHTTPServer((host, port), Handler)


def page(title, body):
    return '<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' + title + '</title><style>body{font-family:system-ui;background:#f3f5fa;color:#182238;margin:0;padding:8vh 6vw}main{max-width:850px;margin:auto;background:white;padding:36px;border-radius:20px}h1{margin-top:0}.notice{color:#596579;line-height:1.8}table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:12px;border-bottom:1px solid #ddd}</style><main><h1>' + title + '</h1>' + body + '</main></html>'


if __name__ == '__main__':
    networks = proxy_networks(os.environ.get('TRUSTED_PROXIES', ''), render=os.environ.get('RENDER', '').lower() == 'true')
    server = make_server(os.environ.get('HOST', '127.0.0.1'), int(os.environ.get('PORT', '8000')), os.environ.get('ADMIN_PASSWORD', ''), os.environ.get('VISITOR_DB', '/workspace/visitor-site-data/visits.sqlite3'), networks)
    print('Visitor site started', flush=True)
    server.serve_forever()
