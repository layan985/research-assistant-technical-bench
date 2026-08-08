from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import os
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parent/'archive'; os.chdir(ROOT)
COUNTS={}
class H(SimpleHTTPRequestHandler):
    def log_message(self, format, *args): pass
    def do_GET(self):
        path=urlparse(self.path).path
        COUNTS[path]=COUNTS.get(path,0)+1
        if path.startswith('/redirect/'):
            self.send_response(302); self.send_header('Location','/docs/'+path.split('/')[-1]); self.end_headers(); return
        digits=''.join(ch for ch in path if ch.isdigit())
        n=int(digits[-6:]) if len(digits)>=6 else 0
        if COUNTS[path]==1 and n and n%401==0:
            self.send_response(429); self.send_header('Retry-After','0'); self.end_headers(); return
        if COUNTS[path]==1 and n and n%607==0:
            self.send_response(500); self.end_headers(); return
        return super().do_GET()
print('Serving benchmark archive at http://127.0.0.1:8765')
ThreadingHTTPServer(('127.0.0.1',8765),H).serve_forever()
