#!/usr/bin/env python3
"""
Generate dummy data for PRISM monitoring dashboards
This script creates realistic sample data for PostgreSQL tables and metrics
"""

import psycopg2
import redis
import json
import random
import time
from datetime import datetime, timedelta
from typing import List, Dict
import uuid

# Database connection settings
PG_CONFIG = {
    'host': 'localhost',
    'port': 15432,
    'database': 'prism_orchestration',
    'user': 'prism_user',
    'password': 'prism_password'
}

REDIS_CONFIG = {
    'host': 'localhost',
    'port': 16379,
    'db': 0
}

def connect_postgres():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        return None

def connect_redis():
    """Connect to Redis"""
    try:
        r = redis.Redis(**REDIS_CONFIG)
        r.ping()
        return r
    except Exception as e:
        print(f"❌ Failed to connect to Redis: {e}")
        return None

def generate_agent_types() -> List[str]:
    """Generate realistic agent types"""
    return [
        'data_processor',
        'quality_inspector',
        'resource_optimizer',
        'predictive_maintenance',
        'workflow_coordinator',
        'error_handler',
        'performance_monitor',
        'batch_processor',
        'real_time_analyzer',
        'compliance_checker'
    ]

def generate_task_types() -> List[str]:
    """Generate realistic task types"""
    return [
        'data_ingestion',
        'quality_analysis',
        'predictive_modeling',
        'resource_allocation',
        'anomaly_detection',
        'report_generation',
        'data_validation',
        'workflow_execution',
        'system_monitoring',
        'batch_processing'
    ]

def generate_dummy_tasks(conn, num_tasks: int = 500):
    """Generate dummy task data"""
    print(f"🔄 Generating {num_tasks} dummy tasks...")
    
    cursor = conn.cursor()
    
    # Create tasks table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            task_type VARCHAR(100),
            status VARCHAR(50),
            agent_id VARCHAR(100),
            agent_type VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            task_data JSONB
        )
    """)
    
    # Clear existing dummy data
    cursor.execute("DELETE FROM tasks WHERE agent_id LIKE 'dummy_%'")
    
    agent_types = generate_agent_types()
    task_types = generate_task_types()
    statuses = ['completed', 'failed', 'running', 'pending']
    status_weights = [0.7, 0.1, 0.1, 0.1]  # 70% completed, 10% each for others
    
    tasks_data = []
    
    for i in range(num_tasks):
        # Generate timestamps over last 7 days
        created_at = datetime.now() - timedelta(
            days=random.uniform(0, 7),
            hours=random.uniform(0, 24),
            minutes=random.uniform(0, 60)
        )
        
        status = random.choices(statuses, weights=status_weights)[0]
        task_type = random.choice(task_types)
        agent_type = random.choice(agent_types)
        agent_id = f"dummy_{agent_type}_{random.randint(1, 5)}"
        
        # Generate completed_at based on status and realistic duration
        completed_at = None
        if status in ['completed', 'failed']:
            duration_seconds = random.uniform(5, 3600)  # 5 seconds to 1 hour
            completed_at = created_at + timedelta(seconds=duration_seconds)
        
        # Generate realistic task data
        task_data = {
            'input_size': random.randint(100, 10000),
            'processing_steps': random.randint(1, 10),
            'resource_usage': {
                'cpu_percent': random.uniform(10, 95),
                'memory_mb': random.randint(128, 2048),
                'disk_io_mb': random.randint(10, 1000)
            },
            'metadata': {
                'priority': random.choice(['low', 'medium', 'high', 'critical']),
                'source': random.choice(['api', 'scheduler', 'user', 'system']),
                'category': random.choice(['manufacturing', 'quality', 'maintenance', 'analytics'])
            }
        }
        
        if status == 'failed':
            task_data['error'] = {
                'code': random.choice(['E001', 'E002', 'E003', 'E004', 'E005']),
                'message': random.choice([
                    'Connection timeout',
                    'Invalid input data',
                    'Resource unavailable',
                    'Processing error',
                    'Validation failed'
                ])
            }
        
        tasks_data.append((
            task_type, status, agent_id, agent_type, 
            created_at, completed_at, json.dumps(task_data)
        ))
    
    # Batch insert
    cursor.executemany("""
        INSERT INTO tasks (task_type, status, agent_id, agent_type, created_at, completed_at, task_data)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, tasks_data)
    
    print(f"✅ Generated {num_tasks} dummy tasks")

def generate_manufacturing_metrics(conn, num_records: int = 200):
    """Generate manufacturing-related metrics"""
    print(f"🔄 Generating {num_records} manufacturing metrics...")
    
    cursor = conn.cursor()
    
    # Create manufacturing metrics table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS manufacturing_metrics (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            line_id VARCHAR(50),
            process_type VARCHAR(100),
            efficiency_percent FLOAT,
            throughput_units_per_hour FLOAT,
            quality_score FLOAT,
            downtime_minutes FLOAT,
            resource_utilization JSONB,
            error_count INTEGER
        )
    """)
    
    # Clear existing data
    cursor.execute("DELETE FROM manufacturing_metrics WHERE line_id LIKE 'dummy_%'")
    
    production_lines = ['dummy_line_A', 'dummy_line_B', 'dummy_line_C', 'dummy_line_D']
    processes = ['assembly', 'testing', 'packaging', 'quality_control', 'finishing']
    
    metrics_data = []
    
    for i in range(num_records):
        timestamp = datetime.now() - timedelta(
            hours=random.uniform(0, 168),  # Last week
            minutes=random.uniform(0, 60)
        )
        
        line_id = random.choice(production_lines)
        process_type = random.choice(processes)
        
        # Generate correlated metrics (high efficiency = high quality, low errors)
        base_performance = random.uniform(0.6, 0.95)
        efficiency = base_performance * 100
        quality_score = base_performance * random.uniform(0.9, 1.0) * 100
        throughput = base_performance * random.uniform(50, 200)
        downtime = (1 - base_performance) * random.uniform(0, 60)
        error_count = int((1 - base_performance) * random.uniform(0, 20))
        
        resource_utilization = {
            'cpu_percent': random.uniform(30, 90),
            'memory_percent': random.uniform(40, 85),
            'network_mbps': random.uniform(10, 100),
            'operators_active': random.randint(2, 8)
        }
        
        metrics_data.append((
            timestamp, line_id, process_type, efficiency, throughput,
            quality_score, downtime, json.dumps(resource_utilization), error_count
        ))
    
    cursor.executemany("""
        INSERT INTO manufacturing_metrics 
        (timestamp, line_id, process_type, efficiency_percent, throughput_units_per_hour,
         quality_score, downtime_minutes, resource_utilization, error_count)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, metrics_data)
    
    print(f"✅ Generated {num_records} manufacturing metrics")

def populate_redis_cache(redis_client, num_keys: int = 100):
    """Populate Redis with realistic cache data"""
    print(f"🔄 Populating Redis with {num_keys} cache entries...")
    
    # Clear existing dummy data
    for key in redis_client.scan_iter("dummy:*"):
        redis_client.delete(key)
    
    cache_types = ['session', 'config', 'temp_data', 'user_prefs', 'api_cache']
    
    for i in range(num_keys):
        cache_type = random.choice(cache_types)
        key = f"dummy:{cache_type}:{uuid.uuid4().hex[:8]}"
        
        # Generate different types of data
        if cache_type == 'session':
            data = {
                'user_id': f"user_{random.randint(1000, 9999)}",
                'login_time': datetime.now().isoformat(),
                'permissions': random.sample(['read', 'write', 'admin', 'monitor'], k=random.randint(1, 3))
            }
        elif cache_type == 'config':
            data = {
                'feature_flags': {
                    'new_ui': random.choice([True, False]),
                    'advanced_analytics': random.choice([True, False]),
                    'beta_features': random.choice([True, False])
                },
                'thresholds': {
                    'cpu_warning': random.randint(70, 85),
                    'memory_critical': random.randint(90, 95)
                }
            }
        else:
            data = {
                'id': str(uuid.uuid4()),
                'value': random.uniform(0, 1000),
                'timestamp': datetime.now().isoformat(),
                'category': random.choice(['A', 'B', 'C'])
            }
        
        # Set with random TTL
        ttl = random.randint(300, 3600)  # 5 minutes to 1 hour
        redis_client.setex(key, ttl, json.dumps(data))
    
    # Add some special monitoring keys
    redis_client.set("dummy:stats:total_requests", random.randint(10000, 50000))
    redis_client.set("dummy:stats:active_users", random.randint(50, 500))
    redis_client.set("dummy:stats:cache_hit_rate", f"{random.uniform(0.8, 0.95):.3f}")
    
    print(f"✅ Populated Redis with {num_keys} cache entries")

def create_system_metrics_table(conn):
    """Create table for system-level metrics"""
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_metrics (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metric_name VARCHAR(100),
            metric_value FLOAT,
            metric_unit VARCHAR(50),
            service_name VARCHAR(100),
            metadata JSONB
        )
    """)
    
    # Clear existing data
    cursor.execute("DELETE FROM system_metrics WHERE service_name LIKE 'dummy_%'")
    
    print("✅ Created system_metrics table")

def generate_system_metrics(conn, hours_back: int = 24):
    """Generate realistic system metrics over time"""
    print(f"🔄 Generating system metrics for last {hours_back} hours...")
    
    cursor = conn.cursor()
    
    services = ['dummy_postgresql', 'dummy_redis', 'dummy_kafka', 'dummy_weaviate', 'dummy_influxdb']
    metrics = {
        'cpu_percent': {'min': 10, 'max': 90, 'unit': 'percent'},
        'memory_percent': {'min': 30, 'max': 85, 'unit': 'percent'},
        'disk_usage_percent': {'min': 40, 'max': 95, 'unit': 'percent'},
        'connections_active': {'min': 5, 'max': 100, 'unit': 'count'},
        'requests_per_second': {'min': 10, 'max': 1000, 'unit': 'rps'},
        'response_time_ms': {'min': 1, 'max': 500, 'unit': 'ms'},
        'error_rate_percent': {'min': 0, 'max': 5, 'unit': 'percent'}
    }
    
    metrics_data = []
    
    # Generate metrics every 5 minutes for the specified period
    start_time = datetime.now() - timedelta(hours=hours_back)
    current_time = start_time
    interval_minutes = 5
    
    while current_time <= datetime.now():
        for service in services:
            for metric_name, config in metrics.items():
                # Add some trend and variance
                base_value = random.uniform(config['min'], config['max'])
                
                # Add time-based trends
                hour = current_time.hour
                if metric_name == 'cpu_percent':
                    # Higher CPU during business hours
                    if 9 <= hour <= 17:
                        base_value *= 1.2
                elif metric_name == 'requests_per_second':
                    # Higher RPS during business hours
                    if 9 <= hour <= 17:
                        base_value *= 1.5
                
                metadata = {
                    'collection_method': 'automated',
                    'instance_id': f"{service}_instance_1"
                }
                
                metrics_data.append((
                    current_time, metric_name, base_value, 
                    config['unit'], service, json.dumps(metadata)
                ))
        
        current_time += timedelta(minutes=interval_minutes)
    
    # Batch insert
    cursor.executemany("""
        INSERT INTO system_metrics (timestamp, metric_name, metric_value, metric_unit, service_name, metadata)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, metrics_data)
    
    print(f"✅ Generated {len(metrics_data)} system metric records")

def main():
    """Main function to generate all dummy data"""
    print("🚀 Starting PRISM Dashboard Dummy Data Generation")
    print("=" * 60)
    
    # Connect to databases
    pg_conn = connect_postgres()
    if not pg_conn:
        print("❌ Cannot proceed without PostgreSQL connection")
        return
    
    redis_client = connect_redis()
    if not redis_client:
        print("⚠️  Redis not available, skipping Redis data generation")
    
    try:
        # Generate PostgreSQL data
        print("\n📊 Generating PostgreSQL Data...")
        generate_dummy_tasks(pg_conn, num_tasks=1000)
        generate_manufacturing_metrics(pg_conn, num_records=500)
        create_system_metrics_table(pg_conn)
        generate_system_metrics(pg_conn, hours_back=48)
        
        # Generate Redis data
        if redis_client:
            print("\n🔴 Generating Redis Data...")
            populate_redis_cache(redis_client, num_keys=200)
        
        print("\n" + "=" * 60)
        print("✅ Dummy data generation completed successfully!")
        print("\n📈 You can now view the dashboards at:")
        print("   • Main Overview: http://localhost:13000/d/prism-overview")
        print("   • PostgreSQL: http://localhost:13000/d/prism-postgresql")
        print("   • Redis: http://localhost:13000/d/prism-redis")
        print("   • Kafka: http://localhost:13000/d/prism-kafka")
        print("   • Manufacturing: http://localhost:13000/d/prism-ai-manufacturing")
        print("\n🔐 Grafana Login: admin / admin123")
        
    except Exception as e:
        print(f"❌ Error generating dummy data: {e}")
        
    finally:
        if pg_conn:
            pg_conn.close()
        if redis_client:
            redis_client.close()

if __name__ == "__main__":
    main()