#!/bin/bash

# PRISM Orchestration Database Deployment Script
# This script deploys all database services and initializes them

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait for service to be ready
wait_for_service() {
    local service_name=$1
    local check_command=$2
    local max_attempts=60
    local attempt=1
    
    log_info "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if eval "$check_command" >/dev/null 2>&1; then
            log_success "$service_name is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo ""
    log_error "$service_name failed to start within $(($max_attempts * 2)) seconds"
    return 1
}

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command_exists docker; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command_exists docker-compose; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    if ! command_exists python3; then
        log_error "Python 3 is not installed. Please install Python 3 first."
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker daemon is not running. Please start Docker first."
        exit 1
    fi
    
    log_success "All prerequisites are met"
}

# Function to create necessary directories
create_directories() {
    log_info "Creating necessary directories..."
    
    # We're already in the db directory, so create subdirectories
    mkdir -p init
    mkdir -p redis
    mkdir -p weaviate
    mkdir -p kafka
    mkdir -p ../logs
    mkdir -p ../backups
    
    log_success "Directories created"
}

# Function to deploy Docker services
deploy_services() {
    log_info "Deploying Docker services..."
    
    # Change to db directory if not already there
    if [ ! -f "docker-compose.yml" ]; then
        cd "$(dirname "$0")/.."
    fi
    
    # Stop any existing services
    log_info "Stopping existing services..."
    docker-compose down --remove-orphans || true
    
    # Pull latest images
    log_info "Pulling Docker images..."
    docker-compose pull
    
    # Start services in background
    log_info "Starting services..."
    docker-compose up -d
    
    log_success "Docker services started"
}

# Function to wait for all services
wait_for_all_services() {
    log_info "Waiting for all services to be ready..."
    
    # Wait for PostgreSQL
    wait_for_service "PostgreSQL" "docker-compose exec -T postgresql pg_isready -U orch_user -d orch_db"
    
    # Wait for Redis
    wait_for_service "Redis" "docker-compose exec -T redis redis-cli -a redis_password ping"
    
    # Wait for Weaviate
    wait_for_service "Weaviate" "curl -f http://localhost:8080/v1/meta"
    
    # Wait for Kafka
    wait_for_service "Kafka" "docker-compose exec -T kafka kafka-topics --bootstrap-server localhost:9092 --list"
    
    # Wait for Prometheus
    wait_for_service "Prometheus" "curl -f http://localhost:9090/-/healthy"
    
    # Wait for Grafana
    wait_for_service "Grafana" "curl -f http://localhost:3000/api/health"
    
    log_success "All services are ready"
}

# Function to initialize Weaviate
initialize_weaviate() {
    log_info "Initializing Weaviate schema..."
    
    # Install Python dependencies
    if [ -f "weaviate/requirements.txt" ]; then
        log_info "Installing Weaviate Python dependencies..."
        cd ..  # Go to db directory root where pyproject.toml is
        uv add $(cat weaviate/requirements.txt | tr '\n' ' ')
        cd - > /dev/null  # Return to previous directory
    fi
    
    # Run schema initialization
    cd weaviate
    if PYTHONPATH=.. uv run --project .. python schema_init.py; then
        log_success "Weaviate schema initialized"
    else
        log_error "Failed to initialize Weaviate schema"
        cd ..
        return 1
    fi
    cd ..
}

# Function to initialize Kafka topics
initialize_kafka() {
    log_info "Initializing Kafka topics..."
    
    # Install Python dependencies
    if [ -f "kafka/requirements.txt" ]; then
        log_info "Installing Kafka Python dependencies..."
        cd ..  # Go to db directory root where pyproject.toml is
        uv add $(cat kafka/requirements.txt | tr '\n' ' ')
        cd - > /dev/null  # Return to previous directory
    fi
    
    # Run topic creation
    cd kafka
    if PYTHONPATH=.. uv run --project .. python create_topics.py; then
        log_success "Kafka topics initialized"
    else
        log_error "Failed to initialize Kafka topics"
        cd ..
        return 1
    fi
    cd ..
}

# Function to run health checks
run_health_checks() {
    log_info "Running health checks..."
    
    # Check PostgreSQL
    if docker-compose exec -T postgresql psql -U orch_user -d orch_db -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" >/dev/null; then
        log_success "PostgreSQL health check passed"
    else
        log_error "PostgreSQL health check failed"
        return 1
    fi
    
    # Check Redis
    if docker-compose exec -T redis redis-cli -a redis_password info server | grep "redis_version" >/dev/null; then
        log_success "Redis health check passed"
    else
        log_error "Redis health check failed"
        return 1
    fi
    
    # Check Weaviate
    if curl -f http://localhost:8080/v1/meta >/dev/null 2>&1; then
        log_success "Weaviate health check passed"
    else
        log_error "Weaviate health check failed"
        return 1
    fi
    
    # Check Kafka
    if docker-compose exec -T kafka kafka-broker-api-versions --bootstrap-server localhost:9092 >/dev/null 2>&1; then
        log_success "Kafka health check passed"
    else
        log_error "Kafka health check failed"
        return 1
    fi
    
    # Check Prometheus
    if curl -f http://localhost:9090/-/healthy >/dev/null 2>&1; then
        log_success "Prometheus health check passed"
    else
        log_error "Prometheus health check failed"
        return 1
    fi
    
    # Check Grafana
    if curl -f http://localhost:3000/api/health >/dev/null 2>&1; then
        log_success "Grafana health check passed"
    else
        log_error "Grafana health check failed"
        return 1
    fi
    
    log_success "All health checks passed"
}

# Function to display service URLs
display_service_urls() {
    log_success "Deployment completed successfully!"
    echo ""
    log_info "Service URLs:"
    echo "  PostgreSQL:     localhost:5432 (user: orch_user, db: orch_db)"
    echo "  Redis:          localhost:6379 (password: redis_password)"
    echo "  Weaviate:       http://localhost:8080"
    echo "  Kafka:          localhost:9092"
    echo ""
    log_info "Management UIs:"
    echo "  pgAdmin:        http://localhost:8082 (admin@orch.com / admin_password)"
    echo "  Redis Insight:  http://localhost:8001"
    echo "  Kafka UI:       http://localhost:8081"
    echo ""
    log_info "Monitoring Dashboards:"
    echo "  Grafana:        http://localhost:3000 (admin / admin_password)"
    echo "  Prometheus:     http://localhost:9090"
    echo "  cAdvisor:       http://localhost:8888"
    echo ""
    log_info "Logs can be viewed with:"
    echo "  docker-compose logs [service-name]"
    echo ""
    log_info "To stop services:"
    echo "  docker-compose down"
}

# Function to create backup
create_backup() {
    log_info "Creating initial backup..."
    
    timestamp=$(date +"%Y%m%d_%H%M%S")
    backup_dir="../backups/${timestamp}"
    mkdir -p "$backup_dir"
    
    # Backup PostgreSQL
    docker-compose exec -T postgresql pg_dump -U orch_user orch_db > "$backup_dir/postgresql_backup.sql"
    
    # Backup configuration files
    cp docker-compose.yml "$backup_dir/"
    cp -r . "$backup_dir/db/"
    
    log_success "Backup created at $backup_dir"
}

# Main deployment function
main() {
    echo ""
    log_info "Starting PRISM Orchestration Database Deployment..."
    echo "=================================================="
    echo ""
    
    check_prerequisites
    create_directories
    deploy_services
    wait_for_all_services
    initialize_weaviate
    initialize_kafka
    run_health_checks
    
    # Run monitoring tests
    log_info "Running monitoring system tests..."
    cd scripts
    if uv run --project .. python test_monitoring.py; then
        log_success "Monitoring tests passed"
    else
        log_warning "Some monitoring tests failed, but core services are running"
    fi
    cd ..
    
    create_backup
    display_service_urls
    
    echo ""
    log_success "🚀 PRISM Orchestration Database deployment completed successfully!"
    echo ""
}

# Handle script interruption
cleanup() {
    echo ""
    log_warning "Deployment interrupted. Cleaning up..."
    docker-compose down --remove-orphans || true
    exit 1
}

trap cleanup INT TERM

# Run main function
main "$@"