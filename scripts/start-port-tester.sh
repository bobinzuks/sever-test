#!/bin/bash

# Port Testing Server Startup Script

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}          🌐 Starting Port Testing Server 🌐               ${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Server configuration
SERVER_IP="147.93.113.37"
PORT="${1:-9090}"

echo -e "${GREEN}Configuration:${NC}"
echo -e "  Server IP: ${YELLOW}$SERVER_IP${NC}"
echo -e "  Port: ${YELLOW}$PORT${NC}"
echo ""

# Check if port is already in use
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}Port $PORT is already in use. Killing existing process...${NC}"
    lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Install required dependencies if not present
echo -e "${GREEN}Checking dependencies...${NC}"
if ! npm list express >/dev/null 2>&1; then
    echo -e "${YELLOW}Installing missing dependencies...${NC}"
    npm install express ws --save
fi

# Start the port test server
echo -e "${GREEN}Starting Port Test Server on port $PORT...${NC}"
cd /home/claude
PORT=$PORT node src/port-test-server.js &
SERVER_PID=$!

sleep 3

# Check if server started successfully
if ps -p $SERVER_PID > /dev/null; then
    echo -e "${GREEN}✅ Port Test Server started successfully!${NC}"
    echo ""
    echo -e "${BLUE}Access Points:${NC}"
    echo -e "  📊 Dashboard: ${YELLOW}http://$SERVER_IP:$PORT${NC}"
    echo -e "  🔌 API: ${YELLOW}http://$SERVER_IP:$PORT/api/ports${NC}"
    echo -e "  💚 Health: ${YELLOW}http://$SERVER_IP:$PORT/health${NC}"
    echo ""
    echo -e "${BLUE}Quick Test Commands:${NC}"
    echo -e "  Test from local:"
    echo -e "    ${YELLOW}curl http://localhost:$PORT/health${NC}"
    echo ""
    echo -e "  Test from external:"
    echo -e "    ${YELLOW}curl http://$SERVER_IP:$PORT/health${NC}"
    echo ""
    echo -e "${BLUE}Port Testing:${NC}"
    echo -e "  The dashboard will automatically scan common ports"
    echo -e "  You can also test specific ports using the web interface"
    echo ""
    echo -e "${GREEN}Server PID: $SERVER_PID${NC}"
    echo -e "${YELLOW}To stop: kill $SERVER_PID${NC}"
else
    echo -e "${RED}❌ Failed to start Port Test Server${NC}"
    exit 1
fi