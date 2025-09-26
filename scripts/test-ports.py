#!/usr/bin/env python3
"""
Port Testing Utility
Tests port connectivity from external perspective
"""

import socket
import sys
import time
import threading
from datetime import datetime
import json
import argparse
import subprocess

class PortTester:
    def __init__(self, host='147.93.113.37'):
        self.host = host
        self.results = {}
        self.lock = threading.Lock()

    def test_port(self, port, timeout=2):
        """Test if a specific port is open"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((self.host, port))
            sock.close()
            return result == 0
        except socket.gaierror:
            return False
        except Exception as e:
            print(f"Error testing port {port}: {e}")
            return False

    def test_port_threaded(self, port, service_name=""):
        """Thread-safe port testing"""
        is_open = self.test_port(port)
        with self.lock:
            self.results[port] = {
                'port': port,
                'service': service_name,
                'status': 'OPEN' if is_open else 'CLOSED',
                'timestamp': datetime.now().isoformat()
            }

            # Print result immediately
            status_symbol = "✅" if is_open else "❌"
            status_color = "\033[92m" if is_open else "\033[91m"
            print(f"{status_color}  Port {port:5} ({service_name:15}) : {status_symbol} {self.results[port]['status']}\033[0m")

    def scan_common_ports(self):
        """Scan commonly used ports"""
        common_ports = {
            22: 'SSH',
            80: 'HTTP',
            443: 'HTTPS',
            3000: 'Node.js API',
            3001: 'Alt API',
            3306: 'MySQL',
            5432: 'PostgreSQL',
            6379: 'Redis',
            8000: 'Django/Python',
            8001: 'Service Port',
            8080: 'Admin/Proxy',
            8443: 'HTTPS Alt',
            8888: 'Jupyter',
            8889: 'Custom Service',
            9090: 'Port Tester',
            27017: 'MongoDB'
        }

        print(f"\n🔍 Scanning ports on {self.host}")
        print("=" * 60)

        threads = []
        for port, service in common_ports.items():
            thread = threading.Thread(target=self.test_port_threaded, args=(port, service))
            thread.start()
            threads.append(thread)

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        return self.results

    def scan_range(self, start_port, end_port):
        """Scan a range of ports"""
        print(f"\n🔍 Scanning port range {start_port}-{end_port} on {self.host}")
        print("=" * 60)

        threads = []
        for port in range(start_port, end_port + 1):
            thread = threading.Thread(target=self.test_port_threaded, args=(port, f"Port {port}"))
            thread.start()
            threads.append(thread)

            # Limit concurrent threads
            if len(threads) >= 50:
                for t in threads:
                    t.join()
                threads = []

        # Wait for remaining threads
        for thread in threads:
            thread.join()

        return self.results

    def test_http_service(self, port):
        """Test if HTTP service is responding"""
        try:
            import urllib.request
            response = urllib.request.urlopen(f'http://{self.host}:{port}/health', timeout=5)
            return response.status == 200
        except:
            return False

    def check_firewall_status(self):
        """Check local firewall status"""
        print("\n🔥 Checking Firewall Status")
        print("=" * 60)

        try:
            # Check UFW status
            result = subprocess.run(['sudo', 'ufw', 'status', 'numbered'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("UFW Firewall Status:")
                print(result.stdout)
            else:
                print("Unable to check UFW status (may need sudo)")
        except:
            print("UFW not available or not configured")

        try:
            # Check iptables rules
            result = subprocess.run(['sudo', 'iptables', '-L', '-n'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("\nIPTables Rules (first 20 lines):")
                lines = result.stdout.split('\n')[:20]
                print('\n'.join(lines))
        except:
            print("Unable to check iptables (may need sudo)")

    def generate_report(self):
        """Generate a summary report"""
        open_ports = [p for p, r in self.results.items() if r['status'] == 'OPEN']
        closed_ports = [p for p, r in self.results.items() if r['status'] == 'CLOSED']

        print("\n" + "=" * 60)
        print("📊 PORT SCAN SUMMARY")
        print("=" * 60)
        print(f"Host: {self.host}")
        print(f"Total ports scanned: {len(self.results)}")
        print(f"Open ports: {len(open_ports)}")
        print(f"Closed ports: {len(closed_ports)}")

        if open_ports:
            print("\n✅ Open Ports:")
            for port in sorted(open_ports):
                service = self.results[port]['service']
                print(f"  - {port:5} : {service}")

        if closed_ports:
            print("\n❌ Closed Ports:")
            for port in sorted(closed_ports)[:10]:  # Show first 10 only
                service = self.results[port]['service']
                print(f"  - {port:5} : {service}")
            if len(closed_ports) > 10:
                print(f"  ... and {len(closed_ports) - 10} more")

        # Save results to file
        report_file = f'port_scan_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n💾 Full report saved to: {report_file}")

    def suggest_firewall_rules(self):
        """Suggest firewall rules for closed ports"""
        closed_ports = [p for p, r in self.results.items() if r['status'] == 'CLOSED']

        if closed_ports:
            print("\n🛡️ Suggested Firewall Rules")
            print("=" * 60)
            print("To open closed ports, you can use these commands:")
            print("\n# Using UFW (Ubuntu Firewall):")
            for port in sorted(closed_ports)[:5]:
                print(f"sudo ufw allow {port}/tcp")
            print("\n# Using iptables:")
            for port in sorted(closed_ports)[:5]:
                print(f"sudo iptables -A INPUT -p tcp --dport {port} -j ACCEPT")
            print("\n# Save iptables rules:")
            print("sudo iptables-save > /etc/iptables/rules.v4")

def main():
    parser = argparse.ArgumentParser(description='Port Testing Utility')
    parser.add_argument('--host', default='147.93.113.37', help='Host to scan')
    parser.add_argument('--common', action='store_true', help='Scan common ports')
    parser.add_argument('--range', nargs=2, type=int, metavar=('START', 'END'),
                       help='Scan a port range')
    parser.add_argument('--port', type=int, help='Test a specific port')
    parser.add_argument('--firewall', action='store_true', help='Check firewall status')
    parser.add_argument('--suggest', action='store_true', help='Suggest firewall rules')

    args = parser.parse_args()

    tester = PortTester(args.host)

    print(f"""
╔════════════════════════════════════════════════════╗
║           🌐 Port Testing Utility                  ║
╠════════════════════════════════════════════════════╣
║  Target Host: {args.host:37} ║
║  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S'):39} ║
╚════════════════════════════════════════════════════╝
    """)

    if args.firewall:
        tester.check_firewall_status()

    if args.port:
        is_open = tester.test_port(args.port)
        status = "✅ OPEN" if is_open else "❌ CLOSED"
        print(f"Port {args.port}: {status}")
    elif args.range:
        tester.scan_range(args.range[0], args.range[1])
        tester.generate_report()
    else:
        # Default to common ports scan
        tester.scan_common_ports()
        tester.generate_report()

    if args.suggest:
        tester.suggest_firewall_rules()

if __name__ == '__main__':
    main()