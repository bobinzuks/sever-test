const express = require('express');
const net = require('net');
const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');
const WebSocket = require('ws');

class PortTestServer {
    constructor() {
        this.servers = {};
        this.results = {};
        this.app = express();
        this.setupMainServer();
    }

    setupMainServer() {
        this.app.use(express.json());

        // CORS for external access
        this.app.use((req, res, next) => {
            res.header('Access-Control-Allow-Origin', '*');
            res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
            res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
            next();
        });

        // Dashboard route
        this.app.get('/', (req, res) => {
            res.send(this.getDashboardHTML());
        });

        // API endpoint to get port status
        this.app.get('/api/ports', (req, res) => {
            res.json(this.getPortStatus());
        });

        // API endpoint to test specific port
        this.app.post('/api/test-port', (req, res) => {
            const { port, protocol = 'tcp' } = req.body;
            this.testPort(port, protocol)
                .then(result => res.json(result))
                .catch(err => res.status(500).json({ error: err.message }));
        });

        // API endpoint to start listening on a port
        this.app.post('/api/listen', (req, res) => {
            const { port, protocol = 'http' } = req.body;
            this.startListening(port, protocol)
                .then(result => res.json(result))
                .catch(err => res.status(500).json({ error: err.message }));
        });

        // API endpoint to stop listening on a port
        this.app.post('/api/stop', (req, res) => {
            const { port } = req.body;
            this.stopListening(port)
                .then(result => res.json(result))
                .catch(err => res.status(500).json({ error: err.message }));
        });

        // Health check endpoint
        this.app.get('/health', (req, res) => {
            res.json({
                status: 'healthy',
                serverIP: '147.93.113.37',
                timestamp: new Date().toISOString(),
                activeServers: Object.keys(this.servers)
            });
        });
    }

    getDashboardHTML() {
        return `
<!DOCTYPE html>
<html>
<head>
    <title>Port Testing Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
        }
        .header p {
            font-size: 1.2rem;
            opacity: 0.9;
        }
        .card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        }
        .port-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 10px;
            margin-bottom: 20px;
        }
        .port-item {
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            font-weight: bold;
            transition: transform 0.2s;
        }
        .port-item:hover {
            transform: translateY(-2px);
        }
        .port-open {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        .port-closed {
            background: #f3f4f6;
            color: #6b7280;
        }
        .port-listening {
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
        }
        .controls {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            cursor: pointer;
            font-size: 16px;
            transition: opacity 0.2s;
        }
        .btn:hover {
            opacity: 0.9;
        }
        .btn-secondary {
            background: #6b7280;
        }
        .btn-danger {
            background: #ef4444;
        }
        input {
            padding: 10px;
            border: 1px solid #d1d5db;
            border-radius: 5px;
            font-size: 16px;
        }
        .status-box {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
        }
        .status-success {
            background: #d1fae5;
            color: #065f46;
            border: 1px solid #6ee7b7;
        }
        .status-error {
            background: #fee2e2;
            color: #991b1b;
            border: 1px solid #fca5a5;
        }
        .status-info {
            background: #dbeafe;
            color: #1e3a8a;
            border: 1px solid #93c5fd;
        }
        .log-container {
            background: #1f2937;
            color: #10b981;
            padding: 15px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            height: 300px;
            overflow-y: auto;
            margin-top: 20px;
        }
        .log-entry {
            margin-bottom: 5px;
            padding: 2px 0;
        }
        .spinner {
            border: 3px solid #f3f4f6;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 20px;
            height: 20px;
            animation: spin 1s linear infinite;
            display: inline-block;
            margin-left: 10px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌐 Port Testing Dashboard</h1>
            <p>Server IP: 147.93.113.37</p>
        </div>

        <div class="card">
            <h2>Quick Port Test</h2>
            <div class="controls">
                <input type="number" id="testPort" placeholder="Port number" min="1" max="65535">
                <button class="btn" onclick="testSinglePort()">Test Port</button>
                <button class="btn" onclick="scanCommonPorts()">Scan Common Ports</button>
                <button class="btn btn-secondary" onclick="refreshStatus()">Refresh Status</button>
            </div>
            <div id="statusMessage"></div>
        </div>

        <div class="card">
            <h2>Common Ports Status</h2>
            <div id="portGrid" class="port-grid"></div>
        </div>

        <div class="card">
            <h2>Server Controls</h2>
            <div class="controls">
                <input type="number" id="listenPort" placeholder="Port to listen on" min="1" max="65535">
                <select id="protocol">
                    <option value="http">HTTP</option>
                    <option value="tcp">TCP</option>
                    <option value="ws">WebSocket</option>
                </select>
                <button class="btn" onclick="startListening()">Start Listening</button>
                <button class="btn btn-danger" onclick="stopListening()">Stop Listening</button>
            </div>
        </div>

        <div class="card">
            <h2>Activity Log</h2>
            <div id="activityLog" class="log-container"></div>
        </div>
    </div>

    <script>
        const API_URL = window.location.origin;
        const commonPorts = [
            { port: 22, name: 'SSH' },
            { port: 80, name: 'HTTP' },
            { port: 443, name: 'HTTPS' },
            { port: 3000, name: 'API' },
            { port: 3001, name: 'Alt API' },
            { port: 8080, name: 'Admin' },
            { port: 8001, name: 'Service' },
            { port: 8889, name: 'Custom' },
            { port: 3306, name: 'MySQL' },
            { port: 6379, name: 'Redis' },
            { port: 5432, name: 'PostgreSQL' },
            { port: 27017, name: 'MongoDB' }
        ];

        function logActivity(message, type = 'info') {
            const log = document.getElementById('activityLog');
            const timestamp = new Date().toLocaleTimeString();
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            entry.style.color = type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : '#93c5fd';
            entry.textContent = \`[\${timestamp}] \${message}\`;
            log.insertBefore(entry, log.firstChild);
            if (log.children.length > 100) {
                log.removeChild(log.lastChild);
            }
        }

        function showStatus(message, type = 'info') {
            const statusDiv = document.getElementById('statusMessage');
            statusDiv.className = 'status-box status-' + type;
            statusDiv.textContent = message;
            setTimeout(() => {
                statusDiv.textContent = '';
                statusDiv.className = '';
            }, 5000);
        }

        async function testSinglePort() {
            const port = document.getElementById('testPort').value;
            if (!port) {
                showStatus('Please enter a port number', 'error');
                return;
            }

            showStatus(\`Testing port \${port}...\`, 'info');
            logActivity(\`Testing port \${port}\`, 'info');

            try {
                const response = await fetch(\`\${API_URL}/api/test-port\`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ port: parseInt(port) })
                });

                const result = await response.json();
                if (result.open) {
                    showStatus(\`Port \${port} is OPEN ✅\`, 'success');
                    logActivity(\`Port \${port} is OPEN\`, 'success');
                } else {
                    showStatus(\`Port \${port} is CLOSED ❌\`, 'error');
                    logActivity(\`Port \${port} is CLOSED\`, 'error');
                }
            } catch (error) {
                showStatus(\`Error testing port: \${error.message}\`, 'error');
                logActivity(\`Error testing port \${port}: \${error.message}\`, 'error');
            }
        }

        async function scanCommonPorts() {
            showStatus('Scanning common ports...', 'info');
            logActivity('Starting common ports scan', 'info');

            const grid = document.getElementById('portGrid');
            grid.innerHTML = '';

            for (const portInfo of commonPorts) {
                const portDiv = document.createElement('div');
                portDiv.className = 'port-item port-closed';
                portDiv.innerHTML = \`
                    <div>\${portInfo.name}</div>
                    <div>Port \${portInfo.port}</div>
                    <div class="spinner"></div>
                \`;
                grid.appendChild(portDiv);

                // Test each port asynchronously
                fetch(\`\${API_URL}/api/test-port\`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ port: portInfo.port })
                }).then(response => response.json())
                  .then(result => {
                    if (result.open) {
                        portDiv.className = 'port-item port-open';
                        portDiv.innerHTML = \`
                            <div>\${portInfo.name}</div>
                            <div>Port \${portInfo.port}</div>
                            <div>✅ OPEN</div>
                        \`;
                        logActivity(\`Port \${portInfo.port} (\${portInfo.name}) is OPEN\`, 'success');
                    } else if (result.listening) {
                        portDiv.className = 'port-item port-listening';
                        portDiv.innerHTML = \`
                            <div>\${portInfo.name}</div>
                            <div>Port \${portInfo.port}</div>
                            <div>🎧 LISTENING</div>
                        \`;
                        logActivity(\`Port \${portInfo.port} (\${portInfo.name}) is LISTENING\`, 'success');
                    } else {
                        portDiv.className = 'port-item port-closed';
                        portDiv.innerHTML = \`
                            <div>\${portInfo.name}</div>
                            <div>Port \${portInfo.port}</div>
                            <div>❌ CLOSED</div>
                        \`;
                    }
                });
            }
        }

        async function startListening() {
            const port = document.getElementById('listenPort').value;
            const protocol = document.getElementById('protocol').value;

            if (!port) {
                showStatus('Please enter a port number', 'error');
                return;
            }

            showStatus(\`Starting \${protocol} server on port \${port}...\`, 'info');
            logActivity(\`Starting \${protocol} server on port \${port}\`, 'info');

            try {
                const response = await fetch(\`\${API_URL}/api/listen\`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ port: parseInt(port), protocol })
                });

                const result = await response.json();
                if (result.success) {
                    showStatus(\`\${protocol.toUpperCase()} server started on port \${port} ✅\`, 'success');
                    logActivity(\`\${protocol.toUpperCase()} server started on port \${port}\`, 'success');
                    setTimeout(scanCommonPorts, 1000);
                } else {
                    showStatus(\`Failed to start server: \${result.error}\`, 'error');
                    logActivity(\`Failed to start server on port \${port}: \${result.error}\`, 'error');
                }
            } catch (error) {
                showStatus(\`Error starting server: \${error.message}\`, 'error');
                logActivity(\`Error starting server: \${error.message}\`, 'error');
            }
        }

        async function stopListening() {
            const port = document.getElementById('listenPort').value;

            if (!port) {
                showStatus('Please enter a port number', 'error');
                return;
            }

            showStatus(\`Stopping server on port \${port}...\`, 'info');
            logActivity(\`Stopping server on port \${port}\`, 'info');

            try {
                const response = await fetch(\`\${API_URL}/api/stop\`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ port: parseInt(port) })
                });

                const result = await response.json();
                if (result.success) {
                    showStatus(\`Server on port \${port} stopped ✅\`, 'success');
                    logActivity(\`Server on port \${port} stopped\`, 'success');
                    setTimeout(scanCommonPorts, 1000);
                } else {
                    showStatus(\`Failed to stop server: \${result.error}\`, 'error');
                    logActivity(\`Failed to stop server: \${result.error}\`, 'error');
                }
            } catch (error) {
                showStatus(\`Error stopping server: \${error.message}\`, 'error');
                logActivity(\`Error stopping server: \${error.message}\`, 'error');
            }
        }

        async function refreshStatus() {
            showStatus('Refreshing port status...', 'info');
            logActivity('Refreshing port status', 'info');
            await scanCommonPorts();
        }

        // Auto-refresh every 30 seconds
        setInterval(refreshStatus, 30000);

        // Initial scan on page load
        window.addEventListener('load', () => {
            logActivity('Dashboard loaded', 'success');
            scanCommonPorts();
        });
    </script>
</body>
</html>
        `;
    }

    startListening(port, protocol = 'http') {
        return new Promise((resolve, reject) => {
            if (this.servers[port]) {
                return resolve({ success: false, error: 'Server already running on this port' });
            }

            try {
                let server;

                switch (protocol) {
                    case 'http':
                        server = http.createServer((req, res) => {
                            res.writeHead(200, { 'Content-Type': 'application/json' });
                            res.end(JSON.stringify({
                                message: `HTTP server on port ${port}`,
                                timestamp: new Date().toISOString()
                            }));
                        });
                        break;

                    case 'tcp':
                        server = net.createServer((socket) => {
                            socket.write(`TCP server on port ${port}\\r\\n`);
                            socket.on('data', (data) => {
                                socket.write(`Echo: ${data}`);
                            });
                        });
                        break;

                    case 'ws':
                        server = http.createServer();
                        const wss = new WebSocket.Server({ server });
                        wss.on('connection', (ws) => {
                            ws.send(JSON.stringify({
                                message: `WebSocket connected on port ${port}`,
                                timestamp: new Date().toISOString()
                            }));
                            ws.on('message', (message) => {
                                ws.send(`Echo: ${message}`);
                            });
                        });
                        break;

                    default:
                        return reject(new Error('Unsupported protocol'));
                }

                server.listen(port, '0.0.0.0', () => {
                    this.servers[port] = { server, protocol };
                    resolve({ success: true, port, protocol });
                });

                server.on('error', (err) => {
                    reject(err);
                });
            } catch (error) {
                reject(error);
            }
        });
    }

    stopListening(port) {
        return new Promise((resolve, reject) => {
            if (!this.servers[port]) {
                return resolve({ success: false, error: 'No server running on this port' });
            }

            try {
                this.servers[port].server.close(() => {
                    delete this.servers[port];
                    resolve({ success: true, port });
                });
            } catch (error) {
                reject(error);
            }
        });
    }

    testPort(port, protocol = 'tcp') {
        return new Promise((resolve) => {
            const client = new net.Socket();
            const timeout = setTimeout(() => {
                client.destroy();
                resolve({ port, open: false, error: 'Timeout' });
            }, 2000);

            client.connect(port, '147.93.113.37', () => {
                clearTimeout(timeout);
                client.destroy();
                resolve({ port, open: true, listening: true });
            });

            client.on('error', () => {
                clearTimeout(timeout);
                resolve({ port, open: false });
            });
        });
    }

    getPortStatus() {
        const status = {
            serverIP: '147.93.113.37',
            activeServers: {},
            timestamp: new Date().toISOString()
        };

        for (const [port, info] of Object.entries(this.servers)) {
            status.activeServers[port] = {
                protocol: info.protocol,
                status: 'listening'
            };
        }

        return status;
    }

    start() {
        const PORT = process.env.PORT || 9090;
        this.app.listen(PORT, '0.0.0.0', () => {
            console.log(`
╔════════════════════════════════════════════════════╗
║        🌐 Port Test Server Started                 ║
╠════════════════════════════════════════════════════╣
║  Dashboard: http://147.93.113.37:${PORT}            ║
║  API Base: http://147.93.113.37:${PORT}/api         ║
║  Health: http://147.93.113.37:${PORT}/health        ║
╠════════════════════════════════════════════════════╣
║  Features:                                         ║
║  • Test any port for connectivity                  ║
║  • Start HTTP/TCP/WebSocket servers                ║
║  • Real-time port scanning                         ║
║  • Web-based dashboard                             ║
╚════════════════════════════════════════════════════╝
            `);
        });
    }
}

// Start the server
const portTester = new PortTestServer();
portTester.start();

module.exports = PortTestServer;