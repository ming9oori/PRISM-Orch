#!/usr/bin/env python3
"""
Vector Search Tester using prism-core RAGSearchTool

벡터 기반 검색 기능을 테스트하는 스크립트입니다.
업로드된 문서들을 대상으로 다양한 쿼리를 테스트하여 
벡터 유사도 검색이 올바르게 작동하는지 확인합니다.
"""

import os
import sys
import json
import logging
import requests
from typing import List, Dict, Any

# Python path setup for local development
sys.path.append('/app/src')
sys.path.append('/app')  # Add for local prism_core

# PRISM-Orch tools import
try:
    from src.orchestration.tools import OrchToolSetup
    ORCH_TOOLS_AVAILABLE = True
    logger_msg = "PRISM-Orch OrchToolSetup 사용"
except ImportError:
    ORCH_TOOLS_AVAILABLE = False
    logger_msg = "PRISM-Orch tools 없음 - 직접 prism-core 사용"
    # Fallback to direct prism-core import
    try:
        from prism_core.core.tools.rag_search_tool import RAGSearchTool
        from prism_core.core.tools.schemas import ToolRequest
        from prism_core.core.config import settings
        PRISM_CORE_AVAILABLE = True
    except ImportError:
        PRISM_CORE_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VectorSearchTester:
    def __init__(self):
        self.weaviate_url = os.getenv('WEAVIATE_URL', 'http://weaviate:8080')
        self.class_prefix = os.getenv('CLASS_PREFIX', 'KOSHA')
        
        # GraphQL endpoint
        self.graphql_url = f"{self.weaviate_url}/v1/graphql"
        
        # Class mappings
        self.class_mapping = {
            "history": f"{self.class_prefix}History",
            "compliance": f"{self.class_prefix}Compliance", 
            "research": f"{self.class_prefix}Research"
        }
        
        # Test scenarios for different domains
        self.test_scenarios = {
            "history": [
                {
                    "query": "압력 이상 문제",
                    "description": "압력 관련 이상 상황 검색",
                    "expected_keywords": ["pressure", "압력", "anomaly", "이상"]
                },
                {
                    "query": "온도 제어 시스템 오작동",
                    "description": "온도 관련 문제 검색",
                    "expected_keywords": ["temperature", "온도", "control", "제어", "malfunction", "오작동"]
                },
                {
                    "query": "CVD 챔버 온도 상승",
                    "description": "CVD 챔버 온도 관련 검색",
                    "expected_keywords": ["CVD", "chamber", "챔버", "temperature", "온도"]
                },
                {
                    "query": "Etching Machine pressure monitoring",
                    "description": "엣칭 머신 압력 모니터링 관련 검색 (영어)",
                    "expected_keywords": ["Etching", "Machine", "pressure", "monitoring"]
                },
                {
                    "query": "agent interaction workflow",
                    "description": "에이전트 상호작용 워크플로우 검색",
                    "expected_keywords": ["agent", "interaction", "workflow", "orchestration"]
                }
            ],
            "compliance": [
                {
                    "query": "안전 규정",
                    "description": "안전 규정 관련 문서 검색",
                    "expected_keywords": ["안전", "규정", "safety", "regulation"]
                },
                {
                    "query": "개인보호구 착용",
                    "description": "개인보호구 관련 규정 검색",
                    "expected_keywords": ["개인보호구", "착용", "PPE", "protection"]
                }
            ]
        }

    def search_domain(self, domain: str, query: str, top_k: int = 3) -> Dict[str, Any]:
        """특정 도메인에서 벡터 검색 수행"""
        class_name = self.class_mapping.get(domain)
        if not class_name:
            return {"success": False, "error": f"Unknown domain: {domain}"}
        
        # GraphQL query for nearText search
        graphql_query = {
            "query": f'''
            {{
                Get {{
                    {class_name}(
                        nearText: {{
                            concepts: ["{query}"]
                        }}
                        limit: {top_k}
                    ) {{
                        title
                        content
                        metadata
                        _additional {{
                            id
                            certainty
                            distance
                            vector
                        }}
                    }}
                }}
            }}
            '''
        }
        
        try:
            response = requests.post(
                self.graphql_url,
                json=graphql_query,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if "errors" in data:
                    return {"success": False, "error": f"GraphQL errors: {data['errors']}"}
                
                results = data.get("data", {}).get("Get", {}).get(class_name, [])
                return {"success": True, "results": results}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"success": False, "error": f"Request failed: {str(e)}"}

    def test_domain_search(self, domain: str, test_cases: List[Dict]) -> Dict[str, Any]:
        """특정 도메인에서 검색 테스트 수행"""
        logger.info(f"🔍 Testing {domain} domain searches...")
        
        results = {
            "domain": domain,
            "total_tests": len(test_cases),
            "successful_tests": 0,
            "failed_tests": 0,
            "test_results": []
        }
        
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"  Test {i}/{len(test_cases)}: {test_case['description']}")
            logger.info(f"  Query: '{test_case['query']}'")
            
            try:
                # Execute search
                response = self.search_domain(domain, test_case["query"], 3)
                
                if response["success"]:
                    search_results = response.get("results", [])
                    logger.info(f"  ✅ Found {len(search_results)} results")
                    
                    test_result = {
                        "test_case": test_case,
                        "status": "success",
                        "results_count": len(search_results),
                        "results": []
                    }
                    
                    # Analyze results
                    for idx, result in enumerate(search_results, 1):
                        # Handle both GraphQL and direct API response formats
                        if "properties" in result:
                            properties = result["properties"]
                        else:
                            properties = result
                        
                        additional = result.get("_additional", {})
                        certainty = additional.get("certainty", 0)
                        distance = additional.get("distance", 1)
                        vector = additional.get("vector")
                        
                        title = result.get('title') or properties.get('title', 'N/A')
                        content = result.get('content') or properties.get('content', '')
                        metadata_raw = result.get('metadata') or properties.get('metadata', '{}')
                        
                        # Parse metadata if it's a string
                        try:
                            metadata = json.loads(metadata_raw) if isinstance(metadata_raw, str) else metadata_raw
                        except:
                            metadata = {}
                        
                        result_info = {
                            "rank": idx,
                            "title": title,
                            "certainty": certainty,
                            "distance": distance,
                            "has_vector": vector is not None and len(vector) > 0 if vector else False,
                            "content_preview": content[:200] + "..." if len(content) > 200 else content,
                            "metadata": metadata
                        }
                        
                        test_result["results"].append(result_info)
                        
                        logger.info(f"    [{idx}] {title}")
                        logger.info(f"        Certainty: {certainty:.4f}, Distance: {distance:.4f}")
                        logger.info(f"        Vector: {'✅' if result_info['has_vector'] else '❌'}")
                        logger.info(f"        Preview: {content[:100]}...")
                    
                    results["successful_tests"] += 1
                    results["test_results"].append(test_result)
                    
                else:
                    error_msg = response.get("error", "Unknown error")
                    logger.error(f"  ❌ Search failed: {error_msg}")
                    results["failed_tests"] += 1
                    results["test_results"].append({
                        "test_case": test_case,
                        "status": "failed",
                        "error": error_msg
                    })
                    
            except Exception as e:
                logger.error(f"  ❌ Exception occurred: {str(e)}")
                results["failed_tests"] += 1
                results["test_results"].append({
                    "test_case": test_case,
                    "status": "error",
                    "error": str(e)
                })
            
            logger.info("")  # Empty line for readability
        
        return results

    def run_all_tests(self) -> Dict[str, Any]:
        """모든 테스트 실행"""
        logger.info("=" * 80)
        logger.info("Vector Search Functionality Test")
        logger.info("=" * 80)
        
        all_results = {
            "total_domains": len(self.test_scenarios),
            "domain_results": {},
            "summary": {
                "total_tests": 0,
                "successful_tests": 0,
                "failed_tests": 0
            }
        }
        
        # Test each domain
        for domain, test_cases in self.test_scenarios.items():
            domain_results = self.test_domain_search(domain, test_cases)
            all_results["domain_results"][domain] = domain_results
            
            # Update summary
            all_results["summary"]["total_tests"] += domain_results["total_tests"]
            all_results["summary"]["successful_tests"] += domain_results["successful_tests"]
            all_results["summary"]["failed_tests"] += domain_results["failed_tests"]
        
        return all_results

    def print_summary(self, results: Dict[str, Any]):
        """테스트 결과 요약 출력"""
        logger.info("=" * 80)
        logger.info("TEST SUMMARY")
        logger.info("=" * 80)
        
        summary = results["summary"]
        logger.info(f"📊 Total Tests: {summary['total_tests']}")
        logger.info(f"✅ Successful: {summary['successful_tests']}")
        logger.info(f"❌ Failed: {summary['failed_tests']}")
        
        success_rate = (summary['successful_tests'] / summary['total_tests']) * 100 if summary['total_tests'] > 0 else 0
        logger.info(f"📈 Success Rate: {success_rate:.1f}%")
        
        logger.info("\nDomain Breakdown:")
        for domain, domain_results in results["domain_results"].items():
            domain_success_rate = (domain_results['successful_tests'] / domain_results['total_tests']) * 100 if domain_results['total_tests'] > 0 else 0
            logger.info(f"  {domain.upper()}: {domain_results['successful_tests']}/{domain_results['total_tests']} ({domain_success_rate:.1f}%)")
        
        # Vector analysis
        logger.info("\nVector Analysis:")
        total_results_with_vectors = 0
        total_results = 0
        
        for domain_results in results["domain_results"].values():
            for test_result in domain_results["test_results"]:
                if test_result["status"] == "success":
                    for result in test_result["results"]:
                        total_results += 1
                        if result["has_vector"]:
                            total_results_with_vectors += 1
        
        if total_results > 0:
            vector_rate = (total_results_with_vectors / total_results) * 100
            logger.info(f"  Vectorized Results: {total_results_with_vectors}/{total_results} ({vector_rate:.1f}%)")
        
        logger.info("=" * 80)
        
        # Overall assessment
        if success_rate >= 90 and (total_results_with_vectors / total_results * 100 if total_results > 0 else 0) >= 90:
            logger.info("🎉 EXCELLENT: Vector search is working perfectly!")
        elif success_rate >= 70:
            logger.info("✅ GOOD: Vector search is working well with minor issues")
        elif success_rate >= 50:
            logger.info("⚠️  NEEDS IMPROVEMENT: Vector search has some issues")
        else:
            logger.info("❌ POOR: Vector search needs significant fixes")

def main():
    """메인 실행 함수"""
    tester = VectorSearchTester()
    
    try:
        # Run all tests
        results = tester.run_all_tests()
        
        # Print summary
        tester.print_summary(results)
        
        # Save detailed results (optional)
        try:
            with open('/tmp/vector_search_test_results.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info("📁 Detailed results saved to /tmp/vector_search_test_results.json")
        except Exception as e:
            logger.warning(f"Could not save detailed results: {e}")
        
        # Exit with appropriate code
        if results["summary"]["failed_tests"] == 0:
            logger.info("🎉 All tests passed!")
            sys.exit(0)
        else:
            logger.warning(f"⚠️  {results['summary']['failed_tests']} tests failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Fatal error during testing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()