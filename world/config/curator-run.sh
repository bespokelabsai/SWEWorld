#!/usr/bin/env bash
# Entrypoint for the deployed `curator` service. Kept deliberately small: the
# release is whatever CI built, and this is the contract deploy-service relies
# on — a run.sh that serves /health on $PORT.
set -euo pipefail
cd "$(dirname "$0")"
PORT="${PORT:-9100}"
if [[ -f ./serve.py ]]; then
  exec python3 ./serve.py
fi
# Default: a minimal health responder so a fresh import is deployable before
# the repo grows a real service entrypoint.
exec python3 -c "
import http.server, os, json
port = int(os.environ.get('PORT', '9100'))
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({'status': 'ok', 'service': 'curator'}).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *a): pass
http.server.HTTPServer(('0.0.0.0', port), H).serve_forever()
"
