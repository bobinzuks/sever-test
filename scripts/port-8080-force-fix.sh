#!/bin/bash

# Force fix for port 8080
echo "🔧 Force fixing port 8080..."

# Kill any existing process on 8080
lsof -ti:8080 | xargs kill -9 2>/dev/null || true
sleep 2

# Create a simple Python server that binds to all interfaces
cat > /tmp/port8080_server.py << 'EOF'
#!/usr/bin/env python3
import http.server
import socketserver
import json
from datetime import datetime

PORT = 8080

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            response = '''
            <html>
            <head><title>Port 8080 - Admin Dashboard</title></head>
            <body>
            <h1>✅ Port 8080 is WORKING!</h1>
            <p>Admin Dashboard is now accessible</p>
            <p>Server Time: ''' + datetime.now().isoformat() + '''</p>
            <p>Access from: http://147.93.113.37:8080</p>
            </body>
            </html>
            '''
            self.wfile.write(response.encode())
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                "status": "healthy",
                "port": 8080,
                "service": "Admin Dashboard",
                "timestamp": datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            super().do_GET()

# Bind to all interfaces (0.0.0.0)
with socketserver.TCPServer(("0.0.0.0", PORT), CustomHandler) as httpd:
    httpd.allow_reuse_address = True
    print(f"✅ Server running on port {PORT}")
    print(f"   Local: http://localhost:{PORT}")
    print(f"   External: http://147.93.113.37:{PORT}")
    httpd.serve_forever()
EOF

# Start the server
echo "Starting Python server on port 8080..."
nohup python3 /tmp/port8080_server.py > /tmp/port8080.log 2>&1 &
SERVER_PID=$!

sleep 3

# Test locally
if curl -s http://localhost:8080/health | grep -q "healthy"; then
    echo "✅ Port 8080 is running locally"
else
    echo "❌ Failed to start service on port 8080"
    exit 1
fi

# Test externally
if timeout 3 bash -c "echo > /dev/tcp/147.93.113.37/8080" 2>/dev/null; then
    echo "✅ Port 8080 is accessible externally!"
else
    echo "⚠️ Port 8080 is running but blocked by firewall"
    echo ""
    echo "Try using an alternative port that might not be blocked:"

    # Try port 8081 instead
    echo "Attempting port 8081 as alternative..."

    kill $SERVER_PID 2>/dev/null || true

    # Modify the script for port 8081
    sed -i 's/PORT = 8080/PORT = 8081/' /tmp/port8080_server.py
    nohup python3 /tmp/port8080_server.py > /tmp/port8081.log 2>&1 &

    sleep 2

    if timeout 3 bash -c "echo > /dev/tcp/147.93.113.37/8081" 2>/dev/null; then
        echo "✅ Alternative port 8081 is working!"
        echo "   Access at: http://147.93.113.37:8081"
    fi
fi

echo ""
echo "Current status:"
netstat -tuln | grep -E "808[0-9]"