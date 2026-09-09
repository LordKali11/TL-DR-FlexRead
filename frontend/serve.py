import http.server
import socketserver
import os
import sys
import json
import webbrowser
import urllib.request
import urllib.parse
import time

PORT = 3000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(DIRECTORY, 'data', 'articles.json')

USER_STATE = {
    "name": "Dr. Felix Meier",
    "email": "felix.meier@nzz-fellows.ch",
    "membership": "NZZ Pro Global Subscriber",
    "memberSince": "Member since October 2019",
    "minutesReadToday": 18,
    "minutesSavedToday": 42,
    "syncDevice": "iPhone 14 Pro · Zurich HB (14m ago)",
    "avatarInitials": "FM"
}

def load_articles():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[API Error] Failed to parse {DATA_FILE}: {e}")
    return []

class ThreadedTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

class NZZRequestHandler(http.server.SimpleHTTPRequestHandler):
    extensions_map = http.server.SimpleHTTPRequestHandler.extensions_map.copy()
    extensions_map.update({
        '.js': 'application/javascript',
        '.mjs': 'application/javascript',
        '.css': 'text/css',
        '.svg': 'image/svg+xml',
        '.json': 'application/json',
        '.tsx': 'text/plain',
        '.ts': 'text/plain',
    })

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def forward_to_backend(self, method='GET', body_bytes=None):
        backend_url = f"http://127.0.0.1:8000{self.path}"
        try:
            req_headers = {k: v for k, v in self.headers.items() if k.lower() not in ('host', 'content-length')}
            if body_bytes:
                req_headers['Content-Length'] = str(len(body_bytes))
            req = urllib.request.Request(backend_url, data=body_bytes, headers=req_headers, method=method)
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = resp.read()
                self.send_response(resp.status)
                for k, v in resp.getheaders():
                    if k.lower() not in ('transfer-encoding', 'content-length', 'access-control-allow-origin'):
                        self.send_header(k, v)
                self.send_cors_headers()
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return True
        except Exception:
            return False

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # First attempt to proxy API requests to live FastAPI backend at port 8000
        if path.startswith('/api/'):
            if self.forward_to_backend(method='GET'):
                return

        if path == '/api/health':
            articles = load_articles()
            return self.send_json({
                "status": "healthy",
                "service": "Neue Zürcher Zeitung (NZZ) Editorial Core API",
                "version": "2.4.0",
                "articlesCount": len(articles),
                "timestamp": int(time.time())
            })

        if path in ('/api/articles', '/api/articles/'):
            articles = load_articles()
            topic_filter = query.get('topic', [None])[0]
            search_query = query.get('q', [None])[0]
            offset = int(query.get('offset', ['0'])[0])
            limit = int(query.get('limit', ['24'])[0])
            full_detail = query.get('full', ['0'])[0] in ('1', 'true', 'yes')

            results = articles
            if topic_filter and topic_filter.lower() != 'all':
                results = [a for a in results if a.get('topic', '').lower() == topic_filter.lower()]

            if search_query:
                q = search_query.lower()
                results = [
                    a for a in results
                    if q in a.get('title', '').lower()
                    or q in a.get('subtitle', '').lower()
                    or q in a.get('author', '').lower()
                    or any(q in t.lower() for t in a.get('takeaways', []))
                ]

            if full_detail:
                return self.send_json(results)

            summaries = []
            for a in results:
                summaries.append({
                    "id": a.get("id"),
                    "slug": a.get("slug"),
                    "kicker": a.get("kicker"),
                    "title": a.get("title"),
                    "subtitle": a.get("subtitle"),
                    "author": a.get("author"),
                    "authorRole": a.get("authorRole"),
                    "date": a.get("date"),
                    "publishedAt": a.get("publishedAt"),
                    "topic": a.get("topic"),
                    "heroImage": a.get("heroImage"),
                    "readingTimes": a.get("readingTimes"),
                    "summaryBullets": a.get("summaryBullets", a.get("takeaways", [])),
                    "takeaways": a.get("takeaways", []),
                    "argumentCount": len(a.get("argumentFocusTopics", [])),
                    "dossierCount": len(a.get("progressiveExpanders", a.get("expanders", []))),
                    "paragraphsCount": len(a.get("paragraphs", []))
                })

            total = len(summaries)
            paginated = summaries[offset : offset + limit]
            return self.send_json({
                "total": total,
                "count": len(paginated),
                "offset": offset,
                "limit": limit,
                "articles": paginated
            })

        if path.startswith('/api/articles/'):
            article_id = path.replace('/api/articles/', '').strip('/')
            articles = load_articles()
            for a in articles:
                if a.get('id') == article_id or a.get('slug') == article_id:
                    return self.send_json(a)
            return self.send_json({"error": "Article not found", "id": article_id}, status=404)

        if path == '/api/user':
            return self.send_json(USER_STATE)

        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get('Content-Length', 0))
        raw_body = self.rfile.read(content_length) if content_length > 0 else None

        if path.startswith('/api/'):
            if self.forward_to_backend(method='POST', body_bytes=raw_body):
                return

        if path == '/api/user/reading-time':
            if raw_body:
                try:
                    payload = json.loads(raw_body.decode('utf-8'))
                    saved = payload.get('minutesSaved', 0)
                    read = payload.get('minutesRead', 0)
                    USER_STATE['minutesSavedToday'] += saved
                    USER_STATE['minutesReadToday'] += read
                    return self.send_json(USER_STATE)
                except Exception as e:
                    return self.send_json({"error": "Invalid JSON", "details": str(e)}, status=400)
            return self.send_json(USER_STATE)

        return self.send_json({"error": "Endpoint not found"}, status=404)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

def run():
    os.chdir(DIRECTORY)
    target_ports = [PORT, 3001, 8000, 8080]
    httpd = None
    used_port = PORT

    for p in target_ports:
        try:
            httpd = ThreadedTCPServer(('0.0.0.0', p), NZZRequestHandler)
            used_port = p
            break
        except OSError:
            continue

    if not httpd:
        print(f"ERROR: Could not bind to any ports: {target_ports}")
        sys.exit(1)

    url = f"http://localhost:{used_port}"
    print(f"\n=======================================================")
    print(f"  Neue Zuercher Zeitung (NZZ) - Core Editorial Server & API")
    print(f"  REST API Active: {url}/api/articles")
    print(f"  Health Check:   {url}/api/health")
    print(f"  Root Directory: {DIRECTORY}")
    print(f"  Press Ctrl+C to stop.")
    print(f"=======================================================\n")

    with httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer gracefully shut down.")

if __name__ == '__main__':
    run()
