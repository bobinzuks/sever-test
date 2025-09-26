# 🌐 Port Test Server

A comprehensive port testing and monitoring server with web dashboard for checking network connectivity and port availability.

## Features

- **Web Dashboard**: Real-time port status monitoring
- **Port Scanner**: Test individual ports or scan common ports
- **Multi-Protocol Support**: HTTP, TCP, WebSocket servers
- **External Access Testing**: Test ports from external network perspective
- **Activity Logging**: Track all port testing activities
- **Firewall Suggestions**: Get recommendations for opening closed ports

## Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/port-test-server.git
cd port-test-server

# Install dependencies
npm install express ws

# Make scripts executable
chmod +x scripts/*.sh
```

## Usage

### Start the Port Test Server

```bash
# Default port 9090
./scripts/start-port-tester.sh

# Custom port
./scripts/start-port-tester.sh 8090
```

### Access the Dashboard

Open your browser and navigate to:
- Local: `http://localhost:9090`
- External: `http://YOUR_SERVER_IP:9090`

### Python Port Scanner

```bash
# Scan common ports
python3 scripts/test-ports.py --common

# Test specific port
python3 scripts/test-ports.py --port 3000

# Scan port range
python3 scripts/test-ports.py --range 8000 8100

# Check firewall status
python3 scripts/test-ports.py --firewall

# Get firewall rule suggestions
python3 scripts/test-ports.py --common --suggest
```

## API Endpoints

### Health Check
```bash
GET /health
```

### Get Port Status
```bash
GET /api/ports
```

### Test Specific Port
```bash
POST /api/test-port
Content-Type: application/json

{
  "port": 3000,
  "protocol": "tcp"
}
```

### Start Listening on Port
```bash
POST /api/listen
Content-Type: application/json

{
  "port": 8888,
  "protocol": "http"  # Options: http, tcp, ws
}
```

### Stop Listening on Port
```bash
POST /api/stop
Content-Type: application/json

{
  "port": 8888
}
```

## Dashboard Features

1. **Quick Port Test**: Test any port instantly
2. **Common Ports Scan**: Automatically scan frequently used ports
3. **Server Controls**: Start/stop servers on specific ports
4. **Activity Log**: Real-time logging of all operations
5. **Visual Status**: Color-coded port status indicators

## Common Ports Checked

- **22** - SSH
- **80** - HTTP
- **443** - HTTPS
- **3000** - Node.js API
- **3306** - MySQL
- **5432** - PostgreSQL
- **6379** - Redis
- **8080** - Admin/Proxy
- **27017** - MongoDB

## Firewall Configuration

If ports appear closed, you may need to configure your firewall:

### Ubuntu/Debian (UFW)
```bash
# Allow specific port
sudo ufw allow 9090/tcp

# Check status
sudo ufw status
```

### Using iptables
```bash
# Allow port
sudo iptables -A INPUT -p tcp --dport 9090 -j ACCEPT

# Save rules
sudo iptables-save
```

## File Structure

```
port-test-server/
├── src/
│   └── port-test-server.js     # Main server application
├── scripts/
│   ├── start-port-tester.sh    # Server startup script
│   └── test-ports.py           # Python port scanner utility
├── package.json
└── README.md
```

## Requirements

- Node.js 14+
- Python 3.6+ (for scanner utility)
- npm packages: express, ws

## Security Notes

- The server binds to `0.0.0.0` to accept external connections
- Ensure proper firewall rules are in place
- Use authentication in production environments
- Monitor access logs regularly

## Troubleshooting

### Port Already in Use
```bash
# Find process using port
lsof -i :9090

# Kill process
kill -9 <PID>
```

### Cannot Access Externally
1. Check firewall rules
2. Verify server is binding to 0.0.0.0
3. Confirm external IP is correct
4. Test from different network

## License

MIT

## Contributing

Pull requests are welcome. For major changes, please open an issue first.

## Author

Your Name

## Support

For issues and questions, please open a GitHub issue.