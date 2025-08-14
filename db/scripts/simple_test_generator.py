#!/usr/bin/env python3
"""
Simple PRISM Test Data Generator
간단한 테스트 데이터 생성기 (외부 라이브러리 최소 사용)
"""

import time
import random
import json
import logging
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import urllib.parse

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PrometheusMetrics:
    def __init__(self):
        self.metrics = {}
        self.reset_metrics()
    
    def reset_metrics(self):
        """메트릭 초기화"""
        self.metrics = {
            'prism_manufacturing_efficiency_percent': {},
            'prism_quality_score': {},
            'prism_agent_success_rate': {},
            'prism_active_agents': {},
            'prism_resource_utilization_percent': {},
            'prism_throughput_units_per_hour': {},
            'prism_errors_total': {},
            'prism_agent_task_duration_seconds_bucket': {}
        }
    
    def set_gauge(self, metric_name, labels, value):
        """Gauge 메트릭 설정"""
        label_str = ','.join([f'{k}="{v}"' for k, v in labels.items()])
        key = f"{metric_name}{{{label_str}}}"
        self.metrics[metric_name][key] = value
    
    def inc_counter(self, metric_name, labels, value=1):
        """Counter 메트릭 증가"""
        label_str = ','.join([f'{k}="{v}"' for k, v in labels.items()])
        key = f"{metric_name}{{{label_str}}}"
        if key not in self.metrics[metric_name]:
            self.metrics[metric_name][key] = 0
        self.metrics[metric_name][key] += value
    
    def to_prometheus_format(self):
        """Prometheus 형식으로 변환"""
        output = []
        
        for metric_name, metric_data in self.metrics.items():
            if not metric_data:
                continue
                
            # 메트릭 헬프와 타입 추가
            if 'efficiency' in metric_name or 'quality' in metric_name or 'success_rate' in metric_name:
                output.append(f"# HELP {metric_name} Percentage metric for PRISM system")
                output.append(f"# TYPE {metric_name} gauge")
            elif 'active_agents' in metric_name or 'throughput' in metric_name:
                output.append(f"# HELP {metric_name} Count metric for PRISM system")
                output.append(f"# TYPE {metric_name} gauge")
            elif 'errors_total' in metric_name:
                output.append(f"# HELP {metric_name} Total error count")
                output.append(f"# TYPE {metric_name} counter")
            elif 'duration' in metric_name:
                output.append(f"# HELP {metric_name} Task duration histogram")
                output.append(f"# TYPE {metric_name} histogram")
            
            for key, value in metric_data.items():
                output.append(f"{key} {value}")
        
        return '\\n'.join(output)

class MetricsHandler(BaseHTTPRequestHandler):
    def __init__(self, metrics, *args, **kwargs):
        self.metrics = metrics
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        if self.path == '/metrics':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            
            metrics_output = self.metrics.to_prometheus_format()
            self.wfile.write(metrics_output.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # 로그 출력 억제
        pass

class SimpleTestGenerator:
    def __init__(self):
        self.running = False
        self.metrics = PrometheusMetrics()
        self.error_counter = 0
        
    def generate_manufacturing_data(self):
        """제조 공정 데이터 생성"""
        processes = ['cnc_milling', 'assembly', 'quality_check', 'packaging']
        product_types = ['component_a', 'component_b', 'finished_product']
        
        while self.running:
            try:
                # 제조 효율성
                for process in processes:
                    efficiency = random.uniform(75, 95)
                    self.metrics.set_gauge('prism_manufacturing_efficiency_percent', 
                                         {'process_name': process}, efficiency)
                
                # 품질 점수
                for product in product_types:
                    quality = random.uniform(85, 99)
                    self.metrics.set_gauge('prism_quality_score', 
                                         {'product_type': product}, quality)
                
                # 처리량
                for line_id in ['line_1', 'line_2', 'line_3']:
                    throughput = random.randint(80, 150)
                    self.metrics.set_gauge('prism_throughput_units_per_hour', 
                                         {'line_id': line_id}, throughput)
                
                # 리소스 사용률
                resources = ['equipment', 'labor', 'material', 'energy']
                for resource in resources:
                    utilization = random.uniform(60, 90)
                    self.metrics.set_gauge('prism_resource_utilization_percent', 
                                         {'resource_type': resource}, utilization)
                
                # 간헐적 에러 발생
                if random.random() < 0.1:
                    error_types = ['timeout', 'connection_failed', 'invalid_data']
                    components = ['database', 'sensor', 'network']
                    self.metrics.inc_counter('prism_errors_total', {
                        'error_type': random.choice(error_types),
                        'component': random.choice(components)
                    })
                
                logger.info(f"제조 데이터 업데이트 완료 - 시간: {datetime.now().strftime('%H:%M:%S')}")
                time.sleep(random.uniform(3, 7))
                
            except Exception as e:
                logger.error(f"제조 데이터 생성 오류: {e}")
                time.sleep(1)
    
    def generate_agent_data(self):
        """에이전트 활동 데이터 생성"""
        agent_types = ['monitoring', 'prediction', 'control', 'orchestration']
        
        while self.running:
            try:
                for agent_type in agent_types:
                    # 성공률
                    success_rate = random.uniform(0.85, 0.99)
                    self.metrics.set_gauge('prism_agent_success_rate', 
                                         {'agent_type': agent_type}, success_rate)
                    
                    # 활성 에이전트 수
                    active_count = random.randint(2, 8)
                    self.metrics.set_gauge('prism_active_agents', 
                                         {'agent_type': agent_type}, active_count)
                
                logger.info(f"에이전트 데이터 업데이트 완료 - 시간: {datetime.now().strftime('%H:%M:%S')}")
                time.sleep(random.uniform(2, 5))
                
            except Exception as e:
                logger.error(f"에이전트 데이터 생성 오류: {e}")
                time.sleep(1)
    
    def send_to_influxdb(self):
        """InfluxDB에 시계열 데이터 전송 (시뮬레이션)"""
        while self.running:
            try:
                # 센서 데이터 시뮬레이션
                sensor_data = {
                    'temperature': random.uniform(20, 35),
                    'humidity': random.uniform(40, 60),
                    'vibration': random.uniform(0.1, 0.8),
                    'pressure': random.uniform(1.0, 1.5)
                }
                
                # InfluxDB 라인 프로토콜 형식으로 데이터 준비
                timestamp = int(time.time() * 1000000000)  # 나노초
                lines = []
                
                for sensor, value in sensor_data.items():
                    line = f"manufacturing_sensors,sensor_type={sensor},line_id=line_1 value={value} {timestamp}"
                    lines.append(line)
                
                # 실제로는 InfluxDB에 전송하지만, 여기서는 로그만 출력
                logger.info(f"InfluxDB 데이터 전송 시뮬레이션: {len(lines)}개 포인트")
                
                time.sleep(10)
                
            except Exception as e:
                logger.error(f"InfluxDB 데이터 전송 오류: {e}")
                time.sleep(5)
    
    def start_metrics_server(self):
        """Prometheus 메트릭 서버 시작"""
        def handler(*args, **kwargs):
            return MetricsHandler(self.metrics, *args, **kwargs)
        
        server = HTTPServer(('0.0.0.0', 8000), handler)
        logger.info("Prometheus 메트릭 서버 시작 (포트 8000)")
        
        while self.running:
            server.handle_request()
    
    def start(self):
        """테스트 데이터 생성 시작"""
        logger.info("=== PRISM 테스트 데이터 생성기 시작 ===")
        self.running = True
        
        # 각 생성기를 별도 스레드에서 실행
        threads = []
        
        # 메트릭 서버 스레드
        metrics_thread = threading.Thread(target=self.start_metrics_server, daemon=True)
        metrics_thread.start()
        threads.append(metrics_thread)
        
        # 데이터 생성 스레드들
        manufacturing_thread = threading.Thread(target=self.generate_manufacturing_data, daemon=True)
        agent_thread = threading.Thread(target=self.generate_agent_data, daemon=True)
        influx_thread = threading.Thread(target=self.send_to_influxdb, daemon=True)
        
        manufacturing_thread.start()
        agent_thread.start()
        influx_thread.start()
        
        threads.extend([manufacturing_thread, agent_thread, influx_thread])
        
        try:
            logger.info("테스트 데이터 생성 중... (Ctrl+C로 중지)")
            logger.info("Prometheus 메트릭: http://localhost:8000/metrics")
            logger.info("Grafana 대시보드: http://localhost:13000")
            
            # 메인 스레드에서 상태 모니터링
            while self.running:
                time.sleep(5)
                active_threads = sum(1 for t in threads if t.is_alive())
                logger.info(f"활성 스레드: {active_threads}/{len(threads)}, 총 에러: {self.error_counter}")
                
        except KeyboardInterrupt:
            logger.info("키보드 인터럽트 감지, 정리 중...")
        finally:
            self.stop()
    
    def stop(self):
        """테스트 데이터 생성 중지"""
        logger.info("테스트 데이터 생성 중지")
        self.running = False

def main():
    generator = SimpleTestGenerator()
    
    try:
        generator.start()
    except KeyboardInterrupt:
        logger.info("프로그램 종료")
    finally:
        generator.stop()

if __name__ == "__main__":
    main()