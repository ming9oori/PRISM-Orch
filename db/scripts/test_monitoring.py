#!/usr/bin/env python3
"""
Monitoring System Test Script for PRISM Orchestration
Tests Prometheus, Grafana, and metrics collection
"""

import requests
import time
import logging
import json
from typing import Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Monitoring endpoints
MONITORING_CONFIG = {
    "prometheus": {
        "url": "http://localhost:9090",
        "health_endpoint": "/-/healthy",
        "metrics_endpoint": "/api/v1/query"
    },
    "grafana": {
        "url": "http://localhost:3000",
        "health_endpoint": "/api/health",
        "auth": ("admin", "admin_password")
    },
    "exporters": {
        "postgres": "http://localhost:9187/metrics",
        "redis": "http://localhost:9121/metrics",
        "kafka": "http://localhost:9308/metrics",
        "node": "http://localhost:9100/metrics",
        "cadvisor": "http://localhost:8888/metrics"
    }
}

class MonitoringTester:
    """Test class for monitoring system functionality"""
    
    def __init__(self):
        self.test_results = {}
    
    def test_prometheus_health(self) -> bool:
        """Test Prometheus health and basic functionality"""
        logger.info("Testing Prometheus health...")
        
        try:
            # Health check
            response = requests.get(
                f"{MONITORING_CONFIG['prometheus']['url']}{MONITORING_CONFIG['prometheus']['health_endpoint']}",
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"Prometheus health check failed: {response.status_code}")
                return False
            
            # Test basic query
            query_params = {"query": "up"}
            response = requests.get(
                f"{MONITORING_CONFIG['prometheus']['url']}{MONITORING_CONFIG['prometheus']['metrics_endpoint']}",
                params=query_params,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"Prometheus query failed: {response.status_code}")
                return False
            
            data = response.json()
            if data["status"] != "success":
                logger.error(f"Prometheus query unsuccessful: {data}")
                return False
            
            # Check if we have metrics
            results = data["data"]["result"]
            if not results:
                logger.warning("No metrics found in Prometheus")
                return False
            
            logger.info(f"Prometheus test passed - Found {len(results)} metrics")
            return True
            
        except Exception as e:
            logger.error(f"Prometheus test failed: {e}")
            return False
    
    def test_grafana_health(self) -> bool:
        """Test Grafana health and API access"""
        logger.info("Testing Grafana health...")
        
        try:
            # Health check
            response = requests.get(
                f"{MONITORING_CONFIG['grafana']['url']}{MONITORING_CONFIG['grafana']['health_endpoint']}",
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"Grafana health check failed: {response.status_code}")
                return False
            
            health_data = response.json()
            if health_data.get("database") != "ok":
                logger.error(f"Grafana database not healthy: {health_data}")
                return False
            
            # Test datasource
            response = requests.get(
                f"{MONITORING_CONFIG['grafana']['url']}/api/datasources",
                auth=MONITORING_CONFIG['grafana']['auth'],
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"Grafana datasource check failed: {response.status_code}")
                return False
            
            datasources = response.json()
            prometheus_ds = [ds for ds in datasources if ds.get("type") == "prometheus"]
            
            if not prometheus_ds:
                logger.warning("No Prometheus datasource found in Grafana")
                return False
            
            logger.info("Grafana test passed - Prometheus datasource configured")
            return True
            
        except Exception as e:
            logger.error(f"Grafana test failed: {e}")
            return False
    
    def test_exporters(self) -> Dict[str, bool]:
        """Test all metric exporters"""
        logger.info("Testing metric exporters...")
        
        results = {}
        
        for exporter_name, endpoint in MONITORING_CONFIG["exporters"].items():
            try:
                logger.info(f"Testing {exporter_name} exporter...")
                
                response = requests.get(endpoint, timeout=10)
                
                if response.status_code == 200:
                    # Check if response contains Prometheus metrics format
                    content = response.text
                    if "# HELP" in content and "# TYPE" in content:
                        logger.info(f"{exporter_name} exporter test passed")
                        results[exporter_name] = True
                    else:
                        logger.warning(f"{exporter_name} exporter returned non-metrics content")
                        results[exporter_name] = False
                else:
                    logger.error(f"{exporter_name} exporter failed: {response.status_code}")
                    results[exporter_name] = False
                    
            except Exception as e:
                logger.error(f"{exporter_name} exporter test failed: {e}")
                results[exporter_name] = False
        
        return results
    
    def test_service_metrics(self) -> bool:
        """Test if we can query metrics for our services"""
        logger.info("Testing service metrics...")
        
        try:
            # Query for service status
            queries = [
                "up{job='postgresql'}",
                "up{job='redis'}",
                "up{job='kafka'}",
                "up{job='weaviate'}"
            ]
            
            all_services_up = True
            
            for query in queries:
                params = {"query": query}
                response = requests.get(
                    f"{MONITORING_CONFIG['prometheus']['url']}{MONITORING_CONFIG['prometheus']['metrics_endpoint']}",
                    params=params,
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data["status"] == "success":
                        results = data["data"]["result"]
                        if results:
                            value = float(results[0]["value"][1])
                            service = results[0]["metric"]["job"]
                            if value == 1.0:
                                logger.info(f"✅ {service} service is UP")
                            else:
                                logger.warning(f"⚠️  {service} service is DOWN")
                                all_services_up = False
                        else:
                            logger.warning(f"No results for query: {query}")
                            all_services_up = False
                    else:
                        logger.error(f"Query failed: {query}")
                        all_services_up = False
                else:
                    logger.error(f"Request failed for query: {query}")
                    all_services_up = False
            
            return all_services_up
            
        except Exception as e:
            logger.error(f"Service metrics test failed: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all monitoring tests"""
        logger.info("Starting comprehensive monitoring tests...")
        
        # Wait a bit for services to be fully ready
        time.sleep(5)
        
        self.test_results = {
            "prometheus_health": self.test_prometheus_health(),
            "grafana_health": self.test_grafana_health(),
            "service_metrics": self.test_service_metrics()
        }
        
        # Test exporters
        exporter_results = self.test_exporters()
        self.test_results.update({f"exporter_{k}": v for k, v in exporter_results.items()})
        
        return self.test_results

def print_monitoring_results(results: Dict[str, bool]):
    """Print formatted monitoring test results"""
    print("\n" + "="*60)
    print("PRISM ORCHESTRATION MONITORING TEST RESULTS")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    # Core services
    core_services = ["prometheus_health", "grafana_health", "service_metrics"]
    print("\n📊 Core Monitoring Services:")
    for test_name in core_services:
        if test_name in results:
            status = "✅ PASSED" if results[test_name] else "❌ FAILED"
            print(f"  {test_name:25} {status}")
    
    # Exporters
    exporter_tests = {k: v for k, v in results.items() if k.startswith("exporter_")}
    if exporter_tests:
        print("\n📈 Metric Exporters:")
        for test_name, result in exporter_tests.items():
            exporter_name = test_name.replace("exporter_", "").upper()
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"  {exporter_name:25} {status}")
    
    print("-" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print("="*60)
    
    if passed_tests == total_tests:
        print("🎉 ALL MONITORING TESTS PASSED! System is fully monitored.")
        print("\n🔍 Access your dashboards:")
        print("  • Grafana:    http://localhost:3000 (admin/admin_password)")
        print("  • Prometheus: http://localhost:9090")
        print("  • cAdvisor:   http://localhost:8888")
    else:
        print("⚠️  Some monitoring tests failed. Check the logs above for details.")
    print()

def main():
    """Main function to run all monitoring tests"""
    tester = MonitoringTester()
    results = tester.run_all_tests()
    
    print_monitoring_results(results)
    
    # Return exit code
    all_passed = all(results.values())
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)