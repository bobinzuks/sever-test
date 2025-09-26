#!/usr/bin/env python3
"""
Comprehensive Port Scanner - Tests ALL ports for rogue/unexpected services
"""

import socket
import threading
import time
from datetime import datetime
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

class ComprehensivePortScanner:
    def __init__(self, host='147.93.113.37'):
        self.host = host
        self.open_ports = []
        self.closed_ports = []
        self.filtered_ports = []
        self.lock = threading.Lock()
        self.results = {}

        # Known/Expected ports
        self.expected_ports = {
            22: "SSH",
            80: "HTTP",
            443: "HTTPS",
            3000: "API Server",
            3001: "Alt API",
            3306: "MySQL",
            5432: "PostgreSQL",
            6379: "Redis",
            8000: "Django",
            8001: "Service",
            8080: "Admin",
            8081: "Admin Alt",
            8443: "HTTPS Alt",
            8888: "Jupyter",
            8889: "Custom",
            9090: "Dashboard",
            27017: "MongoDB",
            4000: "Test Port 1",
            5000: "Test Port 2",
            6000: "Test Port 3"
        }

        # Common service ports to check
        self.common_ports = {
            21: "FTP",
            23: "Telnet",
            25: "SMTP",
            53: "DNS",
            110: "POP3",
            111: "RPC",
            135: "Windows RPC",
            139: "NetBIOS",
            143: "IMAP",
            445: "SMB",
            993: "IMAPS",
            995: "POP3S",
            1433: "MSSQL",
            1521: "Oracle",
            1723: "PPTP",
            3389: "RDP",
            5900: "VNC",
            5984: "CouchDB",
            8008: "HTTP Alt",
            8086: "InfluxDB",
            8090: "Confluence",
            9200: "Elasticsearch",
            11211: "Memcached",
            27018: "MongoDB Alt",
            27019: "MongoDB Alt2",
            50000: "DB2"
        }

    def scan_port(self, port, timeout=0.5):
        """Quick port scan with short timeout"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((self.host, port))
            sock.close()
            return result == 0
        except:
            return False

    def identify_service(self, port):
        """Try to identify what service is running on the port"""
        try:
            # Try to grab banner
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((self.host, port))
            sock.send(b'HEAD / HTTP/1.0\r\n\r\n')
            banner = sock.recv(1024).decode('utf-8', errors='ignore')
            sock.close()
            return banner[:100] if banner else "Unknown"
        except:
            return "Unknown"

    def scan_range_threaded(self, start_port, end_port, max_threads=100):
        """Scan a range of ports using thread pool"""
        print(f"Scanning ports {start_port}-{end_port}...")

        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = []
            for port in range(start_port, end_port + 1):
                futures.append(executor.submit(self.check_port, port))

            # Process results as they complete
            for future in as_completed(futures):
                pass  # Results are handled in check_port

    def check_port(self, port):
        """Check a single port and categorize it"""
        is_open = self.scan_port(port)

        with self.lock:
            if is_open:
                self.open_ports.append(port)

                # Check if it's expected or rogue
                if port in self.expected_ports:
                    service = self.expected_ports[port]
                    status = "EXPECTED"
                elif port in self.common_ports:
                    service = self.common_ports[port]
                    status = "COMMON SERVICE"
                else:
                    service = self.identify_service(port)
                    status = "ROGUE/UNEXPECTED"

                self.results[port] = {
                    "status": "open",
                    "service": service,
                    "category": status,
                    "timestamp": datetime.now().isoformat()
                }

                # Print immediately for rogue ports
                if status == "ROGUE/UNEXPECTED":
                    print(f"🚨 ROGUE PORT FOUND: {port} - {service}")
                elif status == "COMMON SERVICE":
                    print(f"⚠️  Common Service: {port} ({service})")

    def quick_scan(self):
        """Quick scan of common ports"""
        print("\n" + "="*60)
        print("QUICK SCAN - Common Ports")
        print("="*60)

        all_check_ports = {**self.expected_ports, **self.common_ports}

        for port, service in sorted(all_check_ports.items()):
            if self.scan_port(port):
                self.open_ports.append(port)
                if port in self.expected_ports:
                    print(f"✅ Port {port:5} ({service:15}): OPEN (Expected)")
                else:
                    print(f"⚠️  Port {port:5} ({service:15}): OPEN (Unexpected)")
            else:
                if port in self.expected_ports:
                    print(f"❌ Port {port:5} ({service:15}): CLOSED")

    def full_scan(self):
        """Full scan of all 65535 ports"""
        print("\n" + "="*60)
        print("FULL SCAN - All 65535 Ports")
        print("="*60)
        print("This will take several minutes...")

        # Scan in chunks for efficiency
        ranges = [
            (1, 1000, "System Ports"),
            (1001, 5000, "User Ports"),
            (5001, 10000, "Dynamic Ports"),
            (10001, 30000, "High Ports"),
            (30001, 65535, "Ephemeral Ports")
        ]

        for start, end, description in ranges:
            print(f"\nScanning {description} ({start}-{end})...")
            self.scan_range_threaded(start, end, max_threads=200)

            # Show any rogue ports found in this range
            rogue_in_range = [p for p in self.open_ports if start <= p <= end and p not in self.expected_ports]
            if rogue_in_range:
                print(f"  Found {len(rogue_in_range)} unexpected open ports in this range")

    def generate_report(self):
        """Generate comprehensive report"""
        print("\n" + "="*60)
        print("📊 COMPREHENSIVE PORT SCAN REPORT")
        print("="*60)
        print(f"Host: {self.host}")
        print(f"Scan Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total Open Ports: {len(self.open_ports)}")

        # Categorize results
        expected_open = [p for p in self.open_ports if p in self.expected_ports]
        rogue_ports = [p for p in self.open_ports if p not in self.expected_ports and p not in self.common_ports]
        common_unexpected = [p for p in self.open_ports if p in self.common_ports]

        print(f"\n✅ Expected Open Ports ({len(expected_open)}):")
        for port in sorted(expected_open):
            print(f"  - Port {port:5}: {self.expected_ports[port]}")

        if common_unexpected:
            print(f"\n⚠️  Common Services (Unexpected but Known) ({len(common_unexpected)}):")
            for port in sorted(common_unexpected):
                print(f"  - Port {port:5}: {self.common_ports[port]}")

        if rogue_ports:
            print(f"\n🚨 ROGUE/UNKNOWN PORTS ({len(rogue_ports)}):")
            for port in sorted(rogue_ports):
                service = self.results.get(port, {}).get('service', 'Unknown')
                print(f"  - Port {port:5}: {service}")

        # Security recommendations
        print("\n🔒 SECURITY RECOMMENDATIONS:")
        if rogue_ports:
            print("  ❗ CRITICAL: Unknown ports are open and should be investigated")
            print("     These could be:")
            print("     - Backdoors or malware")
            print("     - Misconfigured services")
            print("     - Development servers that shouldn't be exposed")

        if common_unexpected:
            print("  ⚠️  WARNING: Common services are exposed that might not be needed")
            print("     Consider closing these if not required")

        if not rogue_ports and not common_unexpected:
            print("  ✅ No unexpected ports found - System appears secure")

        # Save detailed report
        report_file = f"port_scan_comprehensive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                "host": self.host,
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_open": len(self.open_ports),
                    "expected": len(expected_open),
                    "common_unexpected": len(common_unexpected),
                    "rogue": len(rogue_ports)
                },
                "open_ports": self.results
            }, f, indent=2)

        print(f"\n💾 Detailed report saved to: {report_file}")

        return {
            "expected": expected_open,
            "rogue": rogue_ports,
            "common": common_unexpected
        }

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║          🔍 COMPREHENSIVE PORT SECURITY SCANNER              ║
╠══════════════════════════════════════════════════════════════╣
║  Scanning for ROGUE and UNEXPECTED open ports                ║
║  Target: 147.93.113.37                                       ║
╚══════════════════════════════════════════════════════════════╝
    """)

    scanner = ComprehensivePortScanner()

    # Quick scan first
    scanner.quick_scan()

    # Ask if user wants full scan
    print("\nQuick scan complete. Perform full scan of all 65535 ports?")
    print("This will take 5-10 minutes but will find ALL open ports.")
    print("Starting full scan in 5 seconds... (Ctrl+C to skip)")

    try:
        time.sleep(5)
        scanner.full_scan()
    except KeyboardInterrupt:
        print("\nSkipping full scan...")

    # Generate report
    results = scanner.generate_report()

    # Return exit code based on findings
    if results['rogue']:
        print("\n❗ SECURITY ALERT: Rogue ports detected!")
        sys.exit(1)
    else:
        print("\n✅ Security scan complete - No rogue ports found")
        sys.exit(0)

if __name__ == '__main__':
    main()