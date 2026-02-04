import http.server
import socketserver
import os

PORT = 8080
DIRECTORY = "./03_frontend_design/telas"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

print(f"Serving Frontend at http://localhost:{PORT}/page_04.html")
print("Press CTRL+C to stop.")

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()
