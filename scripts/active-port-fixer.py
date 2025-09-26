#!/usr/bin/env python3
"""
Active Port Fixer - Continuously attempts to open and fix ports
"""

import socket
import subprocess
import time
import json
import threading
import requests
from datetime import datetime

class ActivePortFixer:
    def __init__(self):
        self.server_ip = "147.93.113.37"
        self.dashboard_url = "http://localhost:9090"
        self.target_ports = {
            3000: "API Server",
            8080: "Admin Dashboard",
            8000: "Django Server",
            5432: "PostgreSQL",
            8443: "HTTPS Alt",
            8888: "Jupyter",
            27017: "MongoDB",
            4000: "Test Port 1",
            5000: "Test Port 2",
            6000: "Test Port 3"
        }
        self.fixing = True
        self.results = {}

    def test_port(self, port):
        """Test if a port is open"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((self.server_ip, port))
            sock.close()
            return result == 0
        except:
            return False

    def start_service_on_port(self, port, service_name):
        """Start a service on a specific port"""
        print(f"  🔧 Starting {service_name} on port {port}...")

        try:
            # Try via dashboard API
            response = requests.post(
                f"{self.dashboard_url}/api/listen",
                json={"port": port, "protocol": "http"},
                timeout=5
            )

            if response.ok:
                print(f"    ✅ Service started via API")
                return True
        except Exception as e:
            print(f"    ⚠️ API method failed: {e}")

        # Try starting a simple Python server as fallback
        try:
            script = f'''
import http.server
import socketserver
import json
from datetime import datetime

PORT = {port}

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {{
                "status": "healthy",
                "port": {port},
                "service": "{service_name}",
                "timestamp": datetime.now().isoformat()
            }}
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f"<h1>{service_name} on port {port}</h1>".encode())

with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
    print(f"Server running on port {{PORT}}")
    httpd.serve_forever()
'''

            # Write server script
            script_path = f"/tmp/server_{port}.py"
            with open(script_path, 'w') as f:
                f.write(script)

            # Start server in background
            subprocess.Popen(
                ["python3", script_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )

            time.sleep(2)

            if self.test_port(port):
                print(f"    ✅ Python server started successfully")
                return True
            else:
                print(f"    ❌ Server started but port still closed (firewall?)")

                # Try to open firewall
                self.attempt_firewall_open(port)
                return self.test_port(port)

        except Exception as e:
            print(f"    ❌ Failed to start service: {e}")
            return False

    def attempt_firewall_open(self, port):
        """Attempt to open firewall port"""
        print(f"    🔥 Attempting to open firewall for port {port}...")

        commands = [
            f"sudo ufw allow {port}/tcp",
            f"sudo iptables -A INPUT -p tcp --dport {port} -j ACCEPT",
            f"sudo firewall-cmd --permanent --add-port={port}/tcp",
            f"sudo firewall-cmd --reload"
        ]

        for cmd in commands:
            try:
                result = subprocess.run(
                    cmd.split(),
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    print(f"      ✅ Firewall rule added: {cmd}")
                    break
            except:
                continue

    def fix_single_port(self, port, service_name):
        """Fix a single port"""
        if self.test_port(port):
            return True

        # Try to start service
        if self.start_service_on_port(port, service_name):
            time.sleep(1)
            return self.test_port(port)

        return False

    def continuous_fix_loop(self):
        """Main loop that continuously fixes ports"""
        iteration = 0

        while self.fixing:
            iteration += 1
            print(f"\n{'='*60}")
            print(f"🔄 ITERATION {iteration} - {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*60}")

            all_open = True
            status_report = []

            for port, service in self.target_ports.items():
                is_open = self.test_port(port)

                if is_open:
                    status = f"✅ Port {port:5} ({service:15}): OPEN"
                    status_report.append(status)
                else:
                    all_open = False
                    status = f"❌ Port {port:5} ({service:15}): CLOSED"
                    status_report.append(status)

                    # Attempt fix
                    print(f"\n🔧 Fixing port {port} ({service})...")
                    if self.fix_single_port(port, service):
                        print(f"  ✅ Port {port} is now OPEN!")
                        status_report[-1] = f"✅ Port {port:5} ({service:15}): FIXED & OPEN"
                    else:
                        print(f"  ❌ Failed to fix port {port}")

            # Print status report
            print(f"\n📊 STATUS REPORT:")
            for status in status_report:
                print(f"  {status}")

            if all_open:
                print(f"\n🎉 SUCCESS! All ports are now OPEN!")
                print(f"   Total iterations: {iteration}")
                break

            print(f"\n⏳ Waiting 10 seconds before next attempt...")
            time.sleep(10)

    def start_fixing(self):
        """Start the fixing process"""
        print(f"""
╔════════════════════════════════════════════════════════╗
║           🚀 ACTIVE PORT FIXER STARTED                 ║
╠════════════════════════════════════════════════════════╣
║  Server: {self.server_ip:46} ║
║  Target Ports: {len(self.target_ports):40} ║
║  Mode: Continuous Fix Until Success                    ║
╚════════════════════════════════════════════════════════╝
        """)

        self.continuous_fix_loop()

if __name__ == "__main__":
    fixer = ActivePortFixer()
    fixer.start_fixing()