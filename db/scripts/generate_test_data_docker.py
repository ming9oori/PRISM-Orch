#!/usr/bin/env python3
"""
PRISM Orchestration Test Data Generator for Docker Environment
Docker 환경에서 실행하기 위한 간단한 테스트 데이터 생성기
"""

import psycopg2
from faker import Faker
import random
import json
from datetime import datetime, timedelta
import uuid

fake = Faker('ko_KR')

# PostgreSQL 연결 설정 (Docker 내부에서는 localhost 사용)
DB_CONFIG = {
    'dbname': 'prism_orchestration',
    'user': 'prism_user',
    'password': 'prism_password',
    'host': 'localhost',  # 같은 컨테이너 내부이므로 localhost
    'port': '5432'
}

def create_tables(conn):
    """테이블 생성"""
    cur = conn.cursor()
    
    # 에이전트 테이블
    cur.execute('''
        CREATE TABLE IF NOT EXISTS agents (
            id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100),
            type VARCHAR(50),
            status VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP,
            capabilities JSONB,
            performance_metrics JSONB
        )
    ''')
    
    # 태스크 테이블
    cur.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id VARCHAR(50) PRIMARY KEY,
            agent_id VARCHAR(50) REFERENCES agents(id),
            task_type VARCHAR(50),
            status VARCHAR(20),
            priority INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            parameters JSONB,
            result JSONB
        )
    ''')
    
    # 제조 데이터 테이블
    cur.execute('''
        CREATE TABLE IF NOT EXISTS manufacturing_data (
            id SERIAL PRIMARY KEY,
            machine_id VARCHAR(50),
            product_id VARCHAR(50),
            process_type VARCHAR(50),
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            quality_score DECIMAL(5,2),
            production_rate DECIMAL(10,2),
            defect_count INTEGER,
            parameters JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 시스템 로그 테이블
    cur.execute('''
        CREATE TABLE IF NOT EXISTS system_logs (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            level VARCHAR(20),
            component VARCHAR(50),
            message TEXT,
            metadata JSONB
        )
    ''')
    
    conn.commit()
    print("✅ 테이블 생성 완료")

def generate_agents(conn, count=10):
    """에이전트 데이터 생성"""
    cur = conn.cursor()
    agent_types = ['planner', 'executor', 'monitor', 'optimizer', 'analyzer']
    statuses = ['active', 'idle', 'maintenance', 'error']
    
    agents = []
    for i in range(count):
        agent_id = f"agent_{uuid.uuid4().hex[:8]}"
        agents.append(agent_id)
        
        capabilities = {
            'max_tasks': random.randint(5, 20),
            'supported_operations': random.sample(['planning', 'execution', 'monitoring', 'analysis', 'optimization'], 3),
            'performance_level': random.choice(['high', 'medium', 'low'])
        }
        
        performance_metrics = {
            'success_rate': round(random.uniform(0.7, 0.99), 2),
            'avg_task_time': round(random.uniform(10, 300), 2),
            'total_tasks_completed': random.randint(100, 10000)
        }
        
        cur.execute('''
            INSERT INTO agents (id, name, type, status, last_active, capabilities, performance_metrics)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (
            agent_id,
            f"{fake.first_name()}_{random.choice(agent_types)}",
            random.choice(agent_types),
            random.choice(statuses),
            datetime.now() - timedelta(minutes=random.randint(0, 60)),
            json.dumps(capabilities),
            json.dumps(performance_metrics)
        ))
    
    conn.commit()
    print(f"✅ {count}개 에이전트 생성 완료")
    return agents

def generate_tasks(conn, agents, count=50):
    """태스크 데이터 생성"""
    cur = conn.cursor()
    task_types = ['manufacture', 'quality_check', 'optimization', 'maintenance', 'analysis']
    statuses = ['pending', 'in_progress', 'completed', 'failed', 'cancelled']
    
    for _ in range(count):
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        created_at = datetime.now() - timedelta(hours=random.randint(0, 72))
        
        status = random.choice(statuses)
        started_at = None
        completed_at = None
        
        if status in ['in_progress', 'completed', 'failed']:
            started_at = created_at + timedelta(minutes=random.randint(1, 30))
        
        if status in ['completed', 'failed']:
            completed_at = started_at + timedelta(minutes=random.randint(5, 120))
        
        parameters = {
            'target_quantity': random.randint(100, 1000),
            'quality_threshold': round(random.uniform(0.8, 0.99), 2),
            'deadline': (created_at + timedelta(hours=random.randint(1, 24))).isoformat()
        }
        
        result = None
        if status == 'completed':
            result = {
                'actual_quantity': random.randint(90, 1100),
                'quality_score': round(random.uniform(0.75, 1.0), 2),
                'execution_time': random.randint(10, 200),
                'success': True
            }
        elif status == 'failed':
            result = {
                'error': random.choice(['timeout', 'resource_unavailable', 'quality_fail', 'system_error']),
                'success': False
            }
        
        cur.execute('''
            INSERT INTO tasks (id, agent_id, task_type, status, priority, created_at, started_at, completed_at, parameters, result)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            task_id,
            random.choice(agents),
            random.choice(task_types),
            status,
            random.randint(1, 10),
            created_at,
            started_at,
            completed_at,
            json.dumps(parameters) if parameters else None,
            json.dumps(result) if result else None
        ))
    
    conn.commit()
    print(f"✅ {count}개 태스크 생성 완료")

def generate_manufacturing_data(conn, count=100):
    """제조 데이터 생성"""
    cur = conn.cursor()
    machine_ids = [f"MCH_{i:03d}" for i in range(1, 11)]
    product_ids = [f"PRD_{fake.random_uppercase_letter()}{random.randint(100, 999)}" for _ in range(20)]
    process_types = ['cutting', 'welding', 'assembly', 'painting', 'packaging', 'inspection']
    
    for _ in range(count):
        start_time = datetime.now() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
        end_time = start_time + timedelta(minutes=random.randint(10, 240))
        
        parameters = {
            'temperature': round(random.uniform(20, 200), 1),
            'pressure': round(random.uniform(1, 10), 2),
            'speed': random.randint(10, 100),
            'material': random.choice(['steel', 'aluminum', 'plastic', 'composite'])
        }
        
        cur.execute('''
            INSERT INTO manufacturing_data (machine_id, product_id, process_type, start_time, end_time, 
                                          quality_score, production_rate, defect_count, parameters)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            random.choice(machine_ids),
            random.choice(product_ids),
            random.choice(process_types),
            start_time,
            end_time,
            round(random.uniform(85, 99.9), 2),
            round(random.uniform(50, 200), 2),
            random.randint(0, 10),
            json.dumps(parameters)
        ))
    
    conn.commit()
    print(f"✅ {count}개 제조 데이터 생성 완료")

def generate_system_logs(conn, count=200):
    """시스템 로그 생성"""
    cur = conn.cursor()
    levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    components = ['agent_manager', 'task_scheduler', 'resource_allocator', 'quality_monitor', 'system_health']
    
    messages = [
        "Task completed successfully",
        "Resource allocation updated",
        "Quality threshold exceeded",
        "System performance optimized",
        "Agent status changed",
        "New task assigned",
        "Maintenance required",
        "Error in processing",
        "Connection established",
        "Data synchronized"
    ]
    
    for _ in range(count):
        level = random.choice(levels)
        metadata = {
            'session_id': uuid.uuid4().hex[:12],
            'user': fake.user_name() if random.random() > 0.5 else None,
            'ip_address': fake.ipv4() if random.random() > 0.5 else None
        }
        
        cur.execute('''
            INSERT INTO system_logs (timestamp, level, component, message, metadata)
            VALUES (%s, %s, %s, %s, %s)
        ''', (
            datetime.now() - timedelta(hours=random.randint(0, 168)),
            level,
            random.choice(components),
            random.choice(messages),
            json.dumps(metadata)
        ))
    
    conn.commit()
    print(f"✅ {count}개 시스템 로그 생성 완료")

def show_sample_data(conn):
    """생성된 데이터 샘플 보기"""
    cur = conn.cursor()
    
    print("\n📊 생성된 데이터 샘플:")
    print("=" * 80)
    
    # 에이전트 샘플
    cur.execute("SELECT id, name, type, status FROM agents LIMIT 3")
    print("\n👤 에이전트:")
    for row in cur.fetchall():
        print(f"  - {row[0]}: {row[1]} ({row[2]}) - {row[3]}")
    
    # 태스크 샘플
    cur.execute("SELECT id, task_type, status, priority FROM tasks LIMIT 3")
    print("\n📋 태스크:")
    for row in cur.fetchall():
        print(f"  - {row[0]}: {row[1]} - {row[2]} (우선순위: {row[3]})")
    
    # 제조 데이터 샘플
    cur.execute("SELECT machine_id, product_id, quality_score, production_rate FROM manufacturing_data LIMIT 3")
    print("\n🏭 제조 데이터:")
    for row in cur.fetchall():
        print(f"  - 기계: {row[0]}, 제품: {row[1]}, 품질: {row[2]}%, 생산율: {row[3]}/hr")
    
    # 통계
    cur.execute("SELECT COUNT(*) FROM agents")
    agent_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM tasks")
    task_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM manufacturing_data")
    mfg_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM system_logs")
    log_count = cur.fetchone()[0]
    
    print("\n📈 전체 통계:")
    print(f"  - 총 에이전트: {agent_count}개")
    print(f"  - 총 태스크: {task_count}개")
    print(f"  - 총 제조 데이터: {mfg_count}개")
    print(f"  - 총 시스템 로그: {log_count}개")

def main():
    """메인 실행 함수"""
    print("🚀 PRISM 테스트 데이터 생성 시작")
    print("=" * 80)
    
    try:
        # 데이터베이스 연결
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ PostgreSQL 연결 성공")
        
        # 테이블 생성
        create_tables(conn)
        
        # 데이터 생성
        agents = generate_agents(conn, 10)
        generate_tasks(conn, agents, 50)
        generate_manufacturing_data(conn, 100)
        generate_system_logs(conn, 200)
        
        # 샘플 데이터 표시
        show_sample_data(conn)
        
        print("\n" + "=" * 80)
        print("✨ 모든 테스트 데이터 생성 완료!")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())