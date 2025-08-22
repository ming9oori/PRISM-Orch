"""
PRISM-Orch LLM 기반 규정 준수 분석 예제

LLM을 활용한 지능형 규정 준수 검증을 보여주는 예제입니다.
"""

import asyncio
from src.orchestration.tools import ComplianceTool
from core.tools import ToolRequest


async def example_basic_compliance_check():
    """기본 규정 준수 검증 예제"""
    print("=== 기본 규정 준수 검증 예제 ===")
    
    compliance_tool = ComplianceTool()
    
    # 다양한 조치에 대한 규정 준수 검증
    test_actions = [
        {
            "action": "압력 센서 교체 작업",
            "context": "A-1 라인 정상 운영 중 압력 센서 교체"
        },
        {
            "action": "고온 배관 점검",
            "context": "온도 200도 이상 배관 시스템 점검"
        },
        {
            "action": "화학 물질 취급",
            "context": "독성 화학 물질 저장 탱크 점검"
        },
        {
            "action": "일반 전기 패널 점검",
            "context": "정전 후 전기 패널 상태 확인"
        }
    ]
    
    for i, test_case in enumerate(test_actions, 1):
        print(f"\n--- 테스트 케이스 {i}: {test_case['action']} ---")
        
        request = ToolRequest(
            tool_name="compliance_check",
            parameters={
                "action": test_case["action"],
                "context": test_case["context"]
            }
        )
        
        response = await compliance_tool.execute(request)
        
        if response.success:
            result = response.result
            print(f"준수 상태: {result['compliance_status']}")
            print(f"위험 수준: {result['risk_level']}")
            print(f"권장사항: {', '.join(result['recommendations'])}")
            print(f"분석 근거: {result['reasoning'][:100]}...")
        else:
            print(f"검증 실패: {response.error_message}")


async def example_detailed_compliance_analysis():
    """상세 규정 준수 분석 예제"""
    print("\n=== 상세 규정 준수 분석 예제 ===")
    
    compliance_tool = ComplianceTool()
    
    # 복잡한 시나리오
    complex_scenarios = [
        {
            "action": "고압 가스 배관 누출 수리",
            "context": "운영 중인 고압 가스 배관에서 누출이 발생하여 긴급 수리가 필요한 상황"
        },
        {
            "action": "방사성 물질 취급 시설 점검",
            "context": "방사성 물질을 사용하는 연구 시설의 정기 점검"
        },
        {
            "action": "폭발성 물질 저장소 안전 점검",
            "context": "폭발성 화학 물질을 저장하는 지하 저장소의 안전성 검증"
        }
    ]
    
    for scenario in complex_scenarios:
        print(f"\n--- 시나리오: {scenario['action']} ---")
        print(f"맥락: {scenario['context']}")
        
        request = ToolRequest(
            tool_name="compliance_check",
            parameters={
                "action": scenario["action"],
                "context": scenario["context"]
            }
        )
        
        response = await compliance_tool.execute(request)
        
        if response.success:
            result = response.result
            print(f"✅ 준수 상태: {result['compliance_status']}")
            print(f"⚠️  위험 수준: {result['risk_level']}")
            print(f"📋 권장사항:")
            for rec in result['recommendations']:
                print(f"   - {rec}")
            print(f"🔍 분석 근거: {result['reasoning']}")
            
            if result['related_rules']:
                print(f"📚 관련 규정 ({len(result['related_rules'])}개):")
                for rule in result['related_rules'][:2]:  # 상위 2개만 표시
                    print(f"   - {rule[:80]}...")
        else:
            print(f"❌ 검증 실패: {response.error_message}")


async def example_compliance_comparison():
    """규정 준수 비교 분석 예제"""
    print("\n=== 규정 준수 비교 분석 예제 ===")
    
    compliance_tool = ComplianceTool()
    
    # 유사한 작업의 다른 맥락 비교
    comparison_cases = [
        {
            "name": "일반 점검",
            "action": "압력 밸브 점검",
            "context": "정상 운영 중 정기 점검"
        },
        {
            "name": "긴급 수리",
            "action": "압력 밸브 점검",
            "context": "압력 이상 발생으로 인한 긴급 수리"
        },
        {
            "name": "예방 정비",
            "action": "압력 밸브 점검",
            "context": "계획된 예방 정비 작업"
        }
    ]
    
    results = []
    
    for case in comparison_cases:
        print(f"\n--- {case['name']} ---")
        
        request = ToolRequest(
            tool_name="compliance_check",
            parameters={
                "action": case["action"],
                "context": case["context"]
            }
        )
        
        response = await compliance_tool.execute(request)
        
        if response.success:
            result = response.result
            results.append({
                "name": case["name"],
                "status": result["compliance_status"],
                "risk": result["risk_level"],
                "recommendations": result["recommendations"]
            })
            
            print(f"상태: {result['compliance_status']}")
            print(f"위험: {result['risk_level']}")
            print(f"권장사항: {len(result['recommendations'])}개")
        else:
            print(f"실패: {response.error_message}")
    
    # 비교 결과 요약
    print(f"\n📊 비교 분석 결과:")
    for result in results:
        print(f"  {result['name']}: {result['status']} (위험: {result['risk']})")


async def example_compliance_workflow():
    """규정 준수 워크플로우 예제"""
    print("\n=== 규정 준수 워크플로우 예제 ===")
    
    compliance_tool = ComplianceTool()
    
    # 단계별 규정 준수 검증
    workflow_steps = [
        {
            "step": "초기 평가",
            "action": "고온 배관 점검 계획",
            "context": "온도 300도 배관 시스템 점검 계획 수립"
        },
        {
            "step": "안전 조치 검증",
            "action": "고온 배관 점검 안전 조치",
            "context": "보호구 착용, 냉각 시스템 점검, 응급 대응 계획"
        },
        {
            "step": "실행 승인",
            "action": "고온 배관 점검 실행",
            "context": "모든 안전 조치 완료 후 실제 점검 작업"
        }
    ]
    
    for step in workflow_steps:
        print(f"\n--- {step['step']} ---")
        
        request = ToolRequest(
            tool_name="compliance_check",
            parameters={
                "action": step["action"],
                "context": step["context"]
            }
        )
        
        response = await compliance_tool.execute(request)
        
        if response.success:
            result = response.result
            print(f"✅ 준수 상태: {result['compliance_status']}")
            print(f"⚠️  위험 수준: {result['risk_level']}")
            
            if result['recommendations']:
                print(f"📋 다음 단계 권장사항:")
                for rec in result['recommendations']:
                    print(f"   - {rec}")
            
            # 다음 단계 진행 여부 결정
            if result['compliance_status'] in ['compliant', 'conditional']:
                print(f"✅ {step['step']} 단계 진행 가능")
            else:
                print(f"❌ {step['step']} 단계 재검토 필요")
                break
        else:
            print(f"❌ 검증 실패: {response.error_message}")
            break


async def example_custom_compliance_rules():
    """커스텀 규정 준수 검증 예제"""
    print("\n=== 커스텀 규정 준수 검증 예제 ===")
    
    compliance_tool = ComplianceTool()
    
    # 특정 업계 규정에 따른 검증
    industry_specific_cases = [
        {
            "industry": "화학 공업",
            "action": "독성 화학물질 취급",
            "context": "화학 공장에서 독성 물질을 사용한 제조 공정"
        },
        {
            "industry": "전력 산업",
            "action": "고전압 장비 점검",
            "context": "발전소에서 10kV 이상 고전압 장비 점검"
        },
        {
            "industry": "제철 산업",
            "action": "고온 용광로 점검",
            "context": "철강 공장에서 1500도 이상 고온 용광로 점검"
        }
    ]
    
    for case in industry_specific_cases:
        print(f"\n--- {case['industry']} 규정 준수 검증 ---")
        
        request = ToolRequest(
            tool_name="compliance_check",
            parameters={
                "action": case["action"],
                "context": case["context"]
            }
        )
        
        response = await compliance_tool.execute(request)
        
        if response.success:
            result = response.result
            print(f"업계: {case['industry']}")
            print(f"준수 상태: {result['compliance_status']}")
            print(f"위험 수준: {result['risk_level']}")
            print(f"특별 주의사항: {len(result['recommendations'])}개")
            
            # 업계별 특별 권장사항 강조
            industry_keywords = {
                "화학 공업": ["독성", "화학", "보호구"],
                "전력 산업": ["전압", "전기", "절연"],
                "제철 산업": ["고온", "용광로", "열"]
            }
            
            keywords = industry_keywords.get(case['industry'], [])
            relevant_recommendations = [
                rec for rec in result['recommendations']
                if any(keyword in rec for keyword in keywords)
            ]
            
            if relevant_recommendations:
                print(f"업계 특화 권장사항:")
                for rec in relevant_recommendations:
                    print(f"   ⚠️  {rec}")
        else:
            print(f"검증 실패: {response.error_message}")


async def main():
    """메인 실행 함수"""
    print("🚀 PRISM-Orch LLM 기반 규정 준수 분석 예제")
    print("=" * 60)
    
    try:
        # 1. 기본 규정 준수 검증
        await example_basic_compliance_check()
        
        # 2. 상세 규정 준수 분석
        await example_detailed_compliance_analysis()
        
        # 3. 규정 준수 비교 분석
        await example_compliance_comparison()
        
        # 4. 규정 준수 워크플로우
        await example_compliance_workflow()
        
        # 5. 커스텀 규정 준수 검증
        await example_custom_compliance_rules()
        
        print("\n✅ 모든 LLM 기반 규정 준수 분석 예제 실행 완료!")
        
    except Exception as e:
        print(f"\n❌ 예제 실행 중 오류 발생: {str(e)}")
        print("LLM 서비스 연결 상태를 확인하세요.")


if __name__ == "__main__":
    asyncio.run(main()) 