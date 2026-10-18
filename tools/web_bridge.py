#!/usr/bin/env python3
import sys
import os
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

# Add the esqet_core directory to path so we can import master_scanner
sys.path.append(os.path.expanduser("~/Beta-Rocks/src/esqet_core"))
from master_scanner import classify

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        data = json.loads(self.rfile.read(length))
        
        img_path = data.get("image_path")
        if not img_path or not os.path.exists(img_path):
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"error": "File not found"}')
            return
            
        try:
            result = classify(img_path)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_GET(self):
        # Allow the browser to CORS check the endpoint
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Web Bridge is running. Send a POST request with image_path.")

if __name__ == "__main__":
    PORT = 8081  # Using 8081 to avoid conflict with AUM Surveyor on 8080
    print(f"Starting Web Bridge on port {PORT}...")
    server = HTTPServer(('localhost', PORT), Handler)
    server.serve_forever()
