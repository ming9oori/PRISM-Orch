#!/usr/bin/env python3
"""
PRISM-Orch 종합 테스트 스크립트

이 스크립트는 PRISM-Orch의 모든 주요 기능을 테스트합니다:
1. 서비스 연결 상태 확인
2. Vector DB 검색 기능 테스트
3. 오케스트레이션 API 테스트
4. 임베딩 검증 기능 테스트
5. 전체 워크플로우 테스트
"""

import os
import sys
import json
import time
import requests
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess

# 환경 변수 설정
os.environ.setdefault('PRISM_CORE_BASE_URL', 'http://localhost:8000')
os.environ.setdefault('OPENAI_BASE_URL', 'http://localhost:8001/v1')
os.environ.setdefault('VECTOR_ENCODER_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')

def print_section(title: str):
    """섹션 구분을 위한 출력 함수"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}")

def print_subsection(title: str):
    """서브섹션 구분을 위한 출력 함수"""
    print(f"\n{'-'*60}")
    print(f"  {title}")
    print(f"{'-'*60}")

def print_result(success: bool, message: str, details: str = ""):
    """테스트 결과 출력"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {message}")
    if details:
        print(f"    {details}")

class ComprehensiveTester:
    """종합 테스트 클래스"""
    
    def __init__(self):
        self.prism_core_url = os.getenv('PRISM_CORE_BASE_URL', 'http://localhost:8000')
        self.prism_orch_url = 'http://localhost:8100'
        self.weaviate_url = 'http://localhost:8080'
        self.vllm_url = os.getenv('OPENAI_BASE_URL', 'http://localhost:8001/v1')
        
    def test_service_connections(self) -> Dict[str, bool]:
        """서비스 연결 상태 테스트"""
        print_section("1. 서비스 연결 상태 확인")
        
        results = {}
        
        # 1. Weaviate 연결 확인
        try:
            resp = requests.get(f"{self.weaviate_url}/v1/meta", timeout=5)
            if resp.status_code == 200:
                print_result(True, "Weaviate Vector DB 연결 성공")
                results['weaviate'] = True
            else:
                print_result(False, f"Weaviate 연결 실패: HTTP {resp.status_code}")
                results['weaviate'] = False
        except Exception as e:
            print_result(False, f"Weaviate 연결 실패: {str(e)}")
            results['weaviate'] = False
        
        # 2. PRISM-Core 연결 확인
        try:
            resp = requests.get(f"{self.prism_core_url}/", timeout=5)
            if resp.status_code == 200:
                print_result(True, "PRISM-Core API 연결 성공")
                results['prism_core'] = True
            else:
                print_result(False, f"PRISM-Core 연결 실패: HTTP {resp.status_code}")
                results['prism_core'] = False
        except Exception as e:
            print_result(False, f"PRISM-Core 연결 실패: {str(e)}")
            results['prism_core'] = False
        
        # 3. PRISM-Orch 연결 확인
        try:
            resp = requests.get(f"{self.prism_orch_url}/", timeout=5)
            if resp.status_code == 200:
                print_result(True, "PRISM-Orch API 연결 성공")
                results['prism_orch'] = True
            else:
                print_result(False, f"PRISM-Orch 연결 실패: HTTP {resp.status_code}")
                results['prism_orch'] = False
        except Exception as e:
            print_result(False, f"PRISM-Orch 연결 실패: {str(e)}")
            results['prism_orch'] = False
        
        # 4. vLLM 연결 확인
        try:
            resp = requests.get(f"{self.vllm_url}/models", timeout=5)
            if resp.status_code == 200:
                print_result(True, "vLLM 서비스 연결 성공")
                results['vllm'] = True
            else:
                print_result(False, f"vLLM 연결 실패: HTTP {resp.status_code}")
                results['vllm'] = False
        except Exception as e:
            print_result(False, f"vLLM 연결 실패: {str(e)}")
            results['vllm'] = False
        
        return results
    
    def test_vector_db_schema(self) -> Dict[str, Any]:
        """Vector DB 스키마 및 데이터 확인"""
        print_section("2. Vector DB 스키마 및 데이터 확인")
        
        try:
            # 스키마 조회
            resp = requests.get(f"{self.weaviate_url}/v1/schema", timeout=10)
            if resp.status_code == 200:
                schema = resp.json()
                classes = schema.get('classes', [])
                class_names = [cls['class'] for cls in classes]
                
                print_result(True, f"Vector DB 스키마 조회 성공: {len(classes)}개 클래스")
                print(f"    클래스 목록: {', '.join(class_names)}")
                
                # 각 클래스별 문서 수 확인
                class_counts = {}
                for class_name in class_names:
                    try:
                        resp = requests.get(
                            f"{self.weaviate_url}/v1/objects",
                            params={"class": class_name, "limit": 1},
                            timeout=5
                        )
                        if resp.status_code == 200:
                            result = resp.json()
                            count = result.get('totalResults', 0)
                            class_counts[class_name] = count
                        else:
                            class_counts[class_name] = 0
                    except:
                        class_counts[class_name] = 0
                
                print("    클래스별 문서 수:")
                for class_name, count in class_counts.items():
                    print(f"      - {class_name}: {count}개 문서")
                
                return {
                    'success': True,
                    'classes': class_names,
                    'counts': class_counts
                }
            else:
                print_result(False, f"스키마 조회 실패: HTTP {resp.status_code}")
                return {'success': False}
                
        except Exception as e:
            print_result(False, f"스키마 조회 실패: {str(e)}")
            return {'success': False}
    
    def test_vector_search(self) -> Dict[str, Any]:
        """Vector DB 검색 기능 테스트"""
        print_section("3. Vector DB 검색 기능 테스트")
        
        results = {}
        
        # 각 도메인별 검색 테스트
        test_queries = {
            'OrchResearch': '공정 제어',
            'OrchHistory': '압력 이상',
            'OrchCompliance': '안전 규정'
        }
        
        for class_name, query in test_queries.items():
            try:
                resp = requests.post(
                    f"{self.prism_core_url}/api/vector-db/search/{class_name}",
                    json={"query": query, "limit": 3},
                    params={"client_id": "test", "encoder_model": "sentence-transformers/all-MiniLM-L6-v2"},
                    timeout=10
                )
                
                if resp.status_code == 200:
                    search_results = resp.json()
                    result_count = len(search_results)
                    print_result(True, f"{class_name} 검색 성공: {result_count}개 결과")
                    
                    if result_count > 0:
                        # 첫 번째 결과의 점수 확인
                        first_result = search_results[0]
                        score = first_result.get('score', 0)
                        print(f"    최고 점수: {score:.3f}")
                    
                    results[class_name] = {
                        'success': True,
                        'count': result_count,
                        'score': search_results[0].get('score', 0) if search_results else 0
                    }
                else:
                    print_result(False, f"{class_name} 검색 실패: HTTP {resp.status_code}")
                    results[class_name] = {'success': False}
                    
            except Exception as e:
                print_result(False, f"{class_name} 검색 실패: {str(e)}")
                results[class_name] = {'success': False}
        
        return results
    
    def test_orchestration_api(self) -> Dict[str, Any]:
        """오케스트레이션 API 테스트"""
        print_section("4. 오케스트레이션 API 테스트")
        
        test_cases = [
            {
                'name': '기술 문헌 검색',
                'query': '공정 제어 기술에 대해 알려줘',
                'expected_docs': 1
            },
            {
                'name': '과거 경험 검색',
                'query': '압력 이상 대응 절차를 알려줘',
                'expected_docs': 1
            },
            {
                'name': '안전 규정 검색',
                'query': '안전 규정과 보호구 착용에 대해 알려줘',
                'expected_docs': 1
            }
        ]
        
        results = {}
        
        for test_case in test_cases:
            try:
                print_subsection(f"테스트: {test_case['name']}")
                
                resp = requests.post(
                    f"{self.prism_orch_url}/api/v1/orchestrate/",
                    json={
                        "query": test_case['query'],
                        "user_id": "test_user"
                    },
                    timeout=30
                )
                
                if resp.status_code == 200:
                    result = resp.json()
                    
                    # 응답 구조 확인
                    required_fields = ['session_id', 'final_answer', 'supporting_documents', 'tools_used']
                    missing_fields = [field for field in required_fields if field not in result]
                    
                    if missing_fields:
                        print_result(False, f"응답 필드 누락: {missing_fields}")
                        results[test_case['name']] = {'success': False, 'error': 'missing_fields'}
                        continue
                    
                    # 문서 수 확인
                    doc_count = len(result.get('supporting_documents', []))
                    tools_used = result.get('tools_used', [])
                    
                    print_result(True, f"오케스트레이션 성공")
                    print(f"    세션 ID: {result['session_id']}")
                    print(f"    지원 문서: {doc_count}개")
                    print(f"    사용된 도구: {', '.join(tools_used)}")
                    
                    # 최종 답변 길이 확인
                    final_answer = result.get('final_answer', '')
                    answer_length = len(final_answer)
                    print(f"    답변 길이: {answer_length}자")
                    
                    results[test_case['name']] = {
                        'success': True,
                        'doc_count': doc_count,
                        'tools_used': tools_used,
                        'answer_length': answer_length
                    }
                    
                else:
                    print_result(False, f"API 호출 실패: HTTP {resp.status_code}")
                    results[test_case['name']] = {'success': False, 'error': f'http_{resp.status_code}'}
                    
            except Exception as e:
                print_result(False, f"테스트 실패: {str(e)}")
                results[test_case['name']] = {'success': False, 'error': str(e)}
        
        return results
    
    def test_embedding_validation(self) -> Dict[str, Any]:
        """임베딩 검증 기능 테스트"""
        print_section("5. 임베딩 검증 기능 테스트")
        
        try:
            # 각 클래스의 문서들에 대해 벡터 임베딩 상태 확인
            classes = ['OrchResearch', 'OrchHistory', 'OrchCompliance']
            validation_results = {}
            
            for class_name in classes:
                try:
                    resp = requests.get(
                        f"{self.weaviate_url}/v1/objects",
                        params={"class": class_name, "limit": 5},
                        timeout=10
                    )
                    
                    if resp.status_code == 200:
                        result = resp.json()
                        objects = result.get('objects', [])
                        
                        # 벡터 임베딩 상태 확인
                        docs_with_embeddings = 0
                        docs_without_embeddings = 0
                        
                        for obj in objects:
                            vector_weights = obj.get('vectorWeights')
                            if vector_weights is not None:
                                docs_with_embeddings += 1
                            else:
                                docs_without_embeddings += 1
                        
                        total_docs = len(objects)
                        embedding_rate = (docs_with_embeddings / total_docs * 100) if total_docs > 0 else 0
                        
                        print_result(
                            docs_without_embeddings == 0,
                            f"{class_name}: {total_docs}개 문서, 임베딩 비율 {embedding_rate:.1f}%"
                        )
                        
                        validation_results[class_name] = {
                            'total': total_docs,
                            'with_embeddings': docs_with_embeddings,
                            'without_embeddings': docs_without_embeddings,
                            'embedding_rate': embedding_rate,
                            'all_valid': docs_without_embeddings == 0
                        }
                    else:
                        print_result(False, f"{class_name} 조회 실패: HTTP {resp.status_code}")
                        validation_results[class_name] = {'success': False}
                        
                except Exception as e:
                    print_result(False, f"{class_name} 검증 실패: {str(e)}")
                    validation_results[class_name] = {'success': False}
            
            return validation_results
            
        except Exception as e:
            print_result(False, f"임베딩 검증 테스트 실패: {str(e)}")
            return {'success': False}
    
    def test_full_workflow(self) -> Dict[str, Any]:
        """전체 워크플로우 테스트"""
        print_section("6. 전체 워크플로우 테스트")
        
        try:
            # 복잡한 쿼리로 전체 워크플로우 테스트
            complex_query = """
            A-1 라인에서 압력이 비정상적으로 높아지고 있는데, 
            이전에 비슷한 문제가 있었는지 확인하고, 
            안전 규정에 따라 어떤 조치를 취해야 하는지 알려주세요.
            """
            
            print_subsection("복합 쿼리 테스트")
            print(f"쿼리: {complex_query.strip()}")
            
            resp = requests.post(
                f"{self.prism_orch_url}/api/v1/orchestrate/",
                json={
                    "query": complex_query.strip(),
                    "user_id": "test_user"
                },
                timeout=60
            )
            
            if resp.status_code == 200:
                result = resp.json()
                
                # 결과 분석
                final_answer = result.get('final_answer', '')
                supporting_docs = result.get('supporting_documents', [])
                tools_used = result.get('tools_used', [])
                tool_results = result.get('tool_results', [])
                
                print_result(True, "전체 워크플로우 성공")
                print(f"    답변 길이: {len(final_answer)}자")
                print(f"    지원 문서: {len(supporting_docs)}개")
                print(f"    사용된 도구: {', '.join(tools_used)}")
                print(f"    도구 실행 결과: {len(tool_results)}개")
                
                # 답변 내용 일부 출력
                if final_answer:
                    preview = final_answer[:200] + "..." if len(final_answer) > 200 else final_answer
                    print(f"    답변 미리보기: {preview}")
                
                return {
                    'success': True,
                    'answer_length': len(final_answer),
                    'doc_count': len(supporting_docs),
                    'tools_used': tools_used,
                    'tool_results_count': len(tool_results)
                }
            else:
                print_result(False, f"워크플로우 실패: HTTP {resp.status_code}")
                return {'success': False, 'error': f'http_{resp.status_code}'}
                
        except Exception as e:
            print_result(False, f"워크플로우 테스트 실패: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def generate_report(self, results: Dict[str, Any]):
        """테스트 결과 리포트 생성"""
        print_section("📊 테스트 결과 리포트")
        
        # 1. 서비스 연결 상태
        connections = results.get('connections', {})
        print_subsection("서비스 연결 상태")
        for service, status in connections.items():
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {service}: {'연결됨' if status else '연결 실패'}")
        
        # 2. Vector DB 상태
        vector_db = results.get('vector_db', {})
        if vector_db.get('success'):
            print_subsection("Vector DB 상태")
            counts = vector_db.get('counts', {})
            for class_name, count in counts.items():
                print(f"📁 {class_name}: {count}개 문서")
        
        # 3. 검색 성능
        search_results = results.get('search', {})
        print_subsection("검색 성능")
        for class_name, result in search_results.items():
            if result.get('success'):
                count = result.get('count', 0)
                score = result.get('score', 0)
                print(f"🔍 {class_name}: {count}개 결과 (최고점수: {score:.3f})")
            else:
                print(f"❌ {class_name}: 검색 실패")
        
        # 4. 오케스트레이션 성능
        orchestration = results.get('orchestration', {})
        print_subsection("오케스트레이션 성능")
        for test_name, result in orchestration.items():
            if result.get('success'):
                doc_count = result.get('doc_count', 0)
                answer_length = result.get('answer_length', 0)
                print(f"🤖 {test_name}: {doc_count}개 문서, {answer_length}자 답변")
            else:
                print(f"❌ {test_name}: 실패")
        
        # 5. 임베딩 검증
        validation = results.get('validation', {})
        print_subsection("임베딩 검증")
        for class_name, result in validation.items():
            if isinstance(result, dict) and 'embedding_rate' in result:
                rate = result['embedding_rate']
                status = "✅" if result.get('all_valid') else "⚠️"
                print(f"{status} {class_name}: {rate:.1f}% 임베딩 완료")
        
        # 6. 전체 워크플로우
        workflow = results.get('workflow', {})
        if workflow.get('success'):
            print_subsection("전체 워크플로우")
            print(f"✅ 워크플로우 성공: {workflow.get('answer_length', 0)}자 답변")
            print(f"   📄 {workflow.get('doc_count', 0)}개 지원 문서")
            print(f"   🛠️ {len(workflow.get('tools_used', []))}개 도구 사용")
        
        # 7. 종합 평가
        print_subsection("종합 평가")
        all_tests = [
            ('서비스 연결', connections),
            ('Vector DB', vector_db),
            ('검색 기능', search_results),
            ('오케스트레이션', orchestration),
            ('임베딩 검증', validation),
            ('전체 워크플로우', workflow)
        ]
        
        passed_tests = 0
        total_tests = 0
        
        for test_name, test_results in all_tests:
            if isinstance(test_results, dict):
                if 'success' in test_results:
                    total_tests += 1
                    if test_results['success']:
                        passed_tests += 1
                else:
                    # 개별 결과들을 확인
                    for key, result in test_results.items():
                        if isinstance(result, dict) and 'success' in result:
                            total_tests += 1
                            if result['success']:
                                passed_tests += 1
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"📈 전체 성공률: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        
        if success_rate >= 90:
            print("🎉 시스템이 정상적으로 작동하고 있습니다!")
        elif success_rate >= 70:
            print("⚠️ 시스템이 대부분 정상 작동하지만 일부 문제가 있습니다.")
        else:
            print("❌ 시스템에 심각한 문제가 있습니다. 점검이 필요합니다.")
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print_section("🚀 PRISM-Orch 종합 테스트 시작")
        
        results = {}
        
        # 1. 서비스 연결 테스트
        results['connections'] = self.test_service_connections()
        
        # 2. Vector DB 스키마 테스트
        results['vector_db'] = self.test_vector_db_schema()
        
        # 3. Vector 검색 테스트
        results['search'] = self.test_vector_search()
        
        # 4. 오케스트레이션 API 테스트
        results['orchestration'] = self.test_orchestration_api()
        
        # 5. 임베딩 검증 테스트
        results['validation'] = self.test_embedding_validation()
        
        # 6. 전체 워크플로우 테스트
        results['workflow'] = self.test_full_workflow()
        
        # 7. 결과 리포트 생성
        self.generate_report(results)
        
        return results

def main():
    """메인 함수"""
    print("PRISM-Orch 종합 테스트 스크립트")
    print("=" * 50)
    
    # 테스터 인스턴스 생성
    tester = ComprehensiveTester()
    
    try:
        # 모든 테스트 실행
        results = tester.run_all_tests()
        
        # 결과를 JSON 파일로 저장
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_file = f"test_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 테스트 리포트가 {report_file}에 저장되었습니다.")
        
    except KeyboardInterrupt:
        print("\n⚠️ 테스트가 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류 발생: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 