#!/bin/bash

# Recursive Port Testing Controller
# Continuously tests and attempts to fix port connectivity until working

set -e

# Configuration
SERVER_IP="147.93.113.37"
MAX_ATTEMPTS=100
RETRY_DELAY=10
LOG_FILE="/home/claude/port-tester/recursive-test.log"
STATUS_FILE="/home/claude/port-tester/port-status.json"
DASHBOARD_PORT=9090

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

# Target ports to test and ensure are working
declare -A TARGET_PORTS=(
    ["3000"]="API Server"
    ["8080"]="Admin Dashboard"
    ["9090"]="Port Test Dashboard"
    ["8001"]="Service Port"
    ["8889"]="Custom Service"
    ["4000"]="Test Port 1"
    ["5000"]="Test Port 2"
)

# Initialize log
echo "$(date): Starting Recursive Port Testing Controller" > "$LOG_FILE"

# Function to log messages
log_message() {
    local level=$1
    shift
    local message="$@"
    echo "$(date) [$level]: $message" >> "$LOG_FILE"

    case $level in
        ERROR)   echo -e "${RED}[ERROR]${NC} $message" ;;
        SUCCESS) echo -e "${GREEN}[SUCCESS]${NC} $message" ;;
        WARNING) echo -e "${YELLOW}[WARNING]${NC} $message" ;;
        INFO)    echo -e "${BLUE}[INFO]${NC} $message" ;;
        *)       echo "$message" ;;
    esac
}

# Function to test a single port
test_port() {
    local port=$1
    nc -z -w2 "$SERVER_IP" "$port" 2>/dev/null
    return $?
}

# Function to test port from Python
test_port_python() {
    local port=$1
    python3 -c "
import socket
import sys
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex(('$SERVER_IP', $port))
    sock.close()
    sys.exit(0 if result == 0 else 1)
except:
    sys.exit(1)
" 2>/dev/null
    return $?
}

# Function to start a test server on a port
start_test_server() {
    local port=$1
    local name=$2

    log_message INFO "Starting test server on port $port ($name)"

    # Kill any existing process on this port
    lsof -ti:$port 2>/dev/null | xargs kill -9 2>/dev/null || true
    sleep 1

    # Create a simple Node.js server for this port
    cat > "/tmp/server_${port}.js" << EOF
const express = require('express');
const app = express();

app.get('/', (req, res) => {
    res.json({
        port: $port,
        service: '$name',
        status: 'running',
        timestamp: new Date().toISOString()
    });
});

app.get('/health', (req, res) => {
    res.json({ healthy: true, port: $port });
});

app.listen($port, '0.0.0.0', () => {
    console.log('Server running on port $port');
});
EOF

    # Start the server in background
    cd /home/claude/port-tester
    nohup node "/tmp/server_${port}.js" > "/tmp/server_${port}.log" 2>&1 &
    local pid=$!

    sleep 2

    # Check if server started successfully
    if ps -p $pid > /dev/null; then
        log_message SUCCESS "Server started on port $port (PID: $pid)"
        echo "$pid" > "/tmp/server_${port}.pid"
        return 0
    else
        log_message ERROR "Failed to start server on port $port"
        return 1
    fi
}

# Function to attempt to open firewall port
attempt_firewall_fix() {
    local port=$1

    log_message INFO "Attempting to configure firewall for port $port"

    # Try UFW if available
    if command -v ufw &> /dev/null; then
        sudo ufw allow "$port/tcp" 2>/dev/null || {
            log_message WARNING "Could not configure UFW for port $port (may need sudo)"
        }
    fi

    # Try iptables as fallback
    if command -v iptables &> /dev/null; then
        sudo iptables -A INPUT -p tcp --dport "$port" -j ACCEPT 2>/dev/null || {
            log_message WARNING "Could not configure iptables for port $port (may need sudo)"
        }
    fi
}

# Function to test and fix a port
test_and_fix_port() {
    local port=$1
    local name=$2
    local attempt=$3

    log_message INFO "Testing port $port ($name) - Attempt $attempt"

    # Test if port is open
    if test_port "$port"; then
        log_message SUCCESS "Port $port is OPEN and responding"
        return 0
    else
        log_message WARNING "Port $port is CLOSED or not responding"

        # Try to start a server on this port
        if start_test_server "$port" "$name"; then
            sleep 3

            # Test again
            if test_port "$port"; then
                log_message SUCCESS "Port $port is now OPEN after starting server"
                return 0
            else
                # Port still closed, might be firewall
                log_message WARNING "Server running but port still appears closed - likely firewall issue"

                # Attempt firewall fix
                attempt_firewall_fix "$port"
                sleep 2

                # Final test
                if test_port "$port"; then
                    log_message SUCCESS "Port $port is now OPEN after firewall configuration"
                    return 0
                else
                    log_message ERROR "Port $port still CLOSED after all attempts"
                    return 1
                fi
            fi
        else
            log_message ERROR "Failed to start server on port $port"
            return 1
        fi
    fi
}

# Function to generate status report
generate_status_report() {
    local working_ports=0
    local total_ports=${#TARGET_PORTS[@]}
    local status_json="{"

    echo -e "\n${CYAN}════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}                 PORT STATUS REPORT                      ${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════${NC}"
    echo -e "Timestamp: $(date)"
    echo -e "Server IP: $SERVER_IP\n"

    for port in "${!TARGET_PORTS[@]}"; do
        local name="${TARGET_PORTS[$port]}"
        if test_port "$port"; then
            echo -e "${GREEN}✅ Port $port ($name): OPEN${NC}"
            working_ports=$((working_ports + 1))
            status_json+='"'$port'":{"status":"open","name":"'$name'"},'
        else
            echo -e "${RED}❌ Port $port ($name): CLOSED${NC}"
            status_json+='"'$port'":{"status":"closed","name":"'$name'"},'
        fi
    done

    status_json="${status_json%,}}"
    echo "$status_json" > "$STATUS_FILE"

    echo -e "\n${WHITE}Summary: $working_ports/$total_ports ports working${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════${NC}\n"

    return $((total_ports - working_ports))
}

# Function to start the main dashboard
start_dashboard() {
    log_message INFO "Starting main dashboard on port $DASHBOARD_PORT"

    # Kill any existing dashboard
    lsof -ti:$DASHBOARD_PORT 2>/dev/null | xargs kill -9 2>/dev/null || true
    sleep 1

    # Start the dashboard
    cd /home/claude/port-tester
    nohup node src/port-test-server.js > /tmp/dashboard.log 2>&1 &
    local dashboard_pid=$!

    sleep 3

    if ps -p $dashboard_pid > /dev/null; then
        log_message SUCCESS "Dashboard started on port $DASHBOARD_PORT (PID: $dashboard_pid)"
        echo "$dashboard_pid" > /tmp/dashboard.pid
        return 0
    else
        log_message ERROR "Failed to start dashboard"
        return 1
    fi
}

# Main recursive testing loop
main() {
    local attempt=1
    local all_working=false

    echo -e "${MAGENTA}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${MAGENTA}║     🔄 RECURSIVE PORT TESTING CONTROLLER 🔄           ║${NC}"
    echo -e "${MAGENTA}╠════════════════════════════════════════════════════════╣${NC}"
    echo -e "${MAGENTA}║  This script will continuously test and fix ports     ║${NC}"
    echo -e "${MAGENTA}║  until all target ports are working.                  ║${NC}"
    echo -e "${MAGENTA}╚════════════════════════════════════════════════════════╝${NC}\n"

    # Start the main dashboard first
    start_dashboard

    while [ $attempt -le $MAX_ATTEMPTS ] && [ "$all_working" = false ]; do
        echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
        echo -e "${YELLOW}                  ATTEMPT #$attempt                     ${NC}"
        echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}\n"

        local failed_ports=0

        # Test and fix each port
        for port in "${!TARGET_PORTS[@]}"; do
            local name="${TARGET_PORTS[$port]}"

            if ! test_and_fix_port "$port" "$name" "$attempt"; then
                failed_ports=$((failed_ports + 1))
            fi

            sleep 1
        done

        # Generate status report
        generate_status_report
        local non_working=$?

        if [ $non_working -eq 0 ]; then
            all_working=true
            log_message SUCCESS "All ports are now working!"
            echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
            echo -e "${GREEN}║            ✅ ALL PORTS ARE WORKING! ✅               ║${NC}"
            echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
        else
            log_message WARNING "$non_working ports still not working. Retrying in $RETRY_DELAY seconds..."
            echo -e "${YELLOW}Waiting $RETRY_DELAY seconds before next attempt...${NC}\n"
            sleep $RETRY_DELAY
        fi

        attempt=$((attempt + 1))
    done

    if [ "$all_working" = false ]; then
        log_message ERROR "Maximum attempts ($MAX_ATTEMPTS) reached. Some ports still not working."
        echo -e "${RED}╔════════════════════════════════════════════════════════╗${NC}"
        echo -e "${RED}║         ❌ FAILED TO FIX ALL PORTS ❌                 ║${NC}"
        echo -e "${RED}║         Manual intervention required                   ║${NC}"
        echo -e "${RED}╚════════════════════════════════════════════════════════╝${NC}"
        exit 1
    fi

    # Keep monitoring
    echo -e "\n${CYAN}Entering monitoring mode. Press Ctrl+C to stop.${NC}"
    while true; do
        sleep 30
        generate_status_report > /dev/null

        # Check if any port stopped working
        if [ $? -ne 0 ]; then
            echo -e "${YELLOW}⚠️  Some ports stopped working. Restarting fix process...${NC}"
            main
        fi
    done
}

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Cleaning up...${NC}"

    # Stop all test servers
    for port in "${!TARGET_PORTS[@]}"; do
        if [ -f "/tmp/server_${port}.pid" ]; then
            kill $(cat "/tmp/server_${port}.pid") 2>/dev/null || true
            rm -f "/tmp/server_${port}.pid" "/tmp/server_${port}.js" "/tmp/server_${port}.log"
        fi
    done

    # Stop dashboard
    if [ -f "/tmp/dashboard.pid" ]; then
        kill $(cat "/tmp/dashboard.pid") 2>/dev/null || true
        rm -f "/tmp/dashboard.pid"
    fi

    log_message INFO "Controller stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start the main loop
main