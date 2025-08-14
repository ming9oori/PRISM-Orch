#!/bin/bash

echo "🚀 PRISM Monitoring Setup Script"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

echo -e "${BLUE}📦 Starting PRISM infrastructure...${NC}"
cd "$(dirname "$0")/.."

# Start the infrastructure
docker-compose up -d

echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
sleep 30

# Check service health
echo -e "${BLUE}🔍 Checking service health...${NC}"

services=(
    "postgres:15432:PostgreSQL"
    "redis:16379:Redis"
    "grafana:13000:Grafana"
    "prometheus:19090:Prometheus"
)

for service in "${services[@]}"; do
    IFS=':' read -r name port display_name <<< "$service"
    if nc -z localhost "$port" 2>/dev/null; then
        echo -e "${GREEN}✅ $display_name is running on port $port${NC}"
    else
        echo -e "${RED}❌ $display_name is not responding on port $port${NC}"
    fi
done

# Install Python dependencies
echo -e "${BLUE}📝 Installing Python dependencies...${NC}"
cd scripts
pip3 install -r requirements.txt

# Generate dummy data
echo -e "${BLUE}🎲 Generating dummy data for dashboards...${NC}"
python3 generate_dashboard_dummy_data.py

echo -e "${GREEN}✅ Setup completed!${NC}"
echo
echo "🌐 Access your dashboards:"
echo "  📊 Main Overview:    http://localhost:13000/d/prism-overview"
echo "  🐘 PostgreSQL:      http://localhost:13000/d/prism-postgresql" 
echo "  🔴 Redis:           http://localhost:13000/d/prism-redis"
echo "  🔄 Kafka:           http://localhost:13000/d/prism-kafka"
echo "  🏭 Manufacturing:   http://localhost:13000/d/prism-ai-manufacturing"
echo
echo "🔐 Grafana Login: admin / admin123"
echo "📈 Prometheus:    http://localhost:19090"
echo
echo "💡 To regenerate dummy data, run:"
echo "   python3 scripts/generate_dashboard_dummy_data.py"