import json
import csv
import os
from datetime import datetime
from typing import List, Dict, Any

# 완전한 테스트 데이터셋 (expected_intent -> expected_intent_type로 수정)
manufacturing_dataset = [
    # ANOMALY_CHECK 케이스 (30건)
    {"id": 1, "query": "3번 엣칭 장비 압력이 이상해요", "expected_intent_type": "ANOMALY_CHECK", "expected_priority": "HIGH"},
    {"id": 2, "query": "CVD 장비 온도가 너무 높은 것 같아요", "expected_intent_type": "ANOMALY_CHECK", "expected_priority": "HIGH"},
    {"id": 3, "query": "5번 장비에서 이상한 소리가 나요", "expected_intent_type": "ANOMALY_CHECK", "expected_priority": "HIGH"},
    {"id": 4, "query": "플라즈마 챔버 압력 센서 상태 확인해주세요", "expected_intent_type": "ANOMALY_CHECK", "expected_priority": "MEDIUM"},
    {"id": 5, "query": "웨이퍼 처리 중 에러가 발생했어요", "expected_intent_type": "ANOMALY_CHECK", "expected_priority": "HIGH"},
    {"id": 6, "query": "증착 장비 진공도가 평소와 달라요", "expected_intent_type": "ANOMALY_CHECK", "expected_priority": "HIGH"},
    {"id": 7, "query": "2번 라인 생산이 갑자기 멈췄어요", "expected_intent_type": "ANOMALY_CHECK", "expected_priority": "HIGH"},
    {"id": 8, "query": "식각 공정에서 불량률이 급증했습니다", "expected_intent_type": "ANOMALY_CHECK", "expected_priority": "HIGH"},
    {"id": 9, "query": "챔버 내부 온도 센서가 오작동하는 것 같아요", "expected_intent_type": "ANOMALY_CHECK", "expected_priority": "HIGH"},
    {"id": 10, "query": "가스 유량계 수치가 불안정해요", "expected_intent_type": "ANOMALY_CHECK", "expected_priority": "MEDIUM"},
    {"id": 11, "query": "RF 파워 공급이 간헐적으로 끊어져요", "expected_intent_type": "ANOMALY_CHECK", "expected_priority": "HIGH"},
    {"id": 12, "query": "로드락 시스템에 문제가 있는 것 같습니다", "expected_intent_type": "ANOMALY_CHECK", "expected_priority": "MEDIUM"},
    {"id": 13, "query": "전체 장비 상태를 점검해주세요", "expected_intent_type": "ANOMALY_CHECK", "expected_priority": "MEDIUM"},
    {"id": 14, "query": "냉각수 온도가 설정값을 벗어났어요", "expected_intent_type": "ANOMALY_CHECK", "expected_priority": "HIGH"},
    {"id": 15, "query": "진공 펌프에서 이상 진동이 감지됩니다", "expected_intent_type": "ANOMALY_CHECK", "expected_priority": "HIGH"},
    {"id": 16, "query": "웨이퍼 이송 로봇이 제대로 작동하지 않아요", "expected_intent_type": "ANOMALY_CHECK", "expected_priority": "HIGH"},
    {"id": 17, "query": "플라즈마 점화가 불안정합니다", "expected_intent_type": "ANOMALY_CHECK", "expected_priority": "HIGH"},
    {"id": 18, "query": "마스크 정렬 시스템 오차가 커요", "expected_intent_type": "ANOMALY_CHECK", "expected_priority": "HIGH"},
    {"id": 19, "query": "화학 기상 증착 중 가스 누출이 의심됩니다", "expected_intent_type": "ANOMALY_CHECK", "expected_priority": "HIGH"},
    {"id": 20, "query": "스퍼터링 타겟 상태를 확인해주세요", "expected_intent_type": "ANOMALY_CHECK", "expected_priority": "MEDIUM"},
    {"id": 21, "query": "이온 주입 장비 빔 전류가 불안정해요", "expected_intent_type": "ANOMALY_CHECK", "expected_priority": "HIGH"},
    {"id": 22, "query": "포토리소그래피 노광 강도가 이상해요", "expected_intent_type": "ANOMALY_CHECK", "expected_priority": "HIGH"},
    {"id": 23, "query": "CMP 장비 패드 압력이 불균등합니다", "expected_intent_type": "ANOMALY_CHECK", "expected_priority": "MEDIUM"},
    {"id": 24, "query": "배기 시스템 효율이 떨어진 것 같아요", "expected_intent_type": "ANOMALY_CHECK", "expected_priority": "MEDIUM"},
    {"id": 25, "query": "웨이퍼 카세트 로딩에 문제가 있어요", "expected_intent_type": "ANOMALY_CHECK", "expected_priority": "MEDIUM"},
    {"id": 26, "query": "플라즈마 밀도 분포가 불균일해요", "expected_intent_type": "ANOMALY_CHECK", "expected_priority": "HIGH"},
    {"id": 27, "query": "반응성 이온 식각 속도가 느려졌어요", "expected_intent_type": "ANOMALY_CHECK", "expected_priority": "HIGH"},
    {"id": 28, "query": "열처리로 온도 프로파일이 이상합니다", "expected_intent_type": "ANOMALY_CHECK", "expected_priority": "HIGH"},
    {"id": 29, "query": "클린룸 입자 농도가 기준치를 초과했어요", "expected_intent_type": "ANOMALY_CHECK", "expected_priority": "HIGH"},
    {"id": 30, "query": "장비 알람이 계속 울리고 있어요", "expected_intent_type": "ANOMALY_CHECK", "expected_priority": "HIGH"},

    # OPTIMIZATION 케이스 (25건)
    {"id": 31, "query": "생산 수율을 개선하고 싶어요", "expected_intent_type": "OPTIMIZATION", "expected_priority": "MEDIUM"},
    {"id": 32, "query": "에너지 효율성을 높이는 방법을 알려주세요", "expected_intent_type": "OPTIMIZATION", "expected_priority": "MEDIUM"},
    {"id": 33, "query": "공정 시간을 단축할 수 있을까요?", "expected_intent_type": "OPTIMIZATION", "expected_priority": "MEDIUM"},
    {"id": 34, "query": "웨이퍼 처리량을 증가시키고 싶습니다", "expected_intent_type": "OPTIMIZATION", "expected_priority": "MEDIUM"},
    {"id": 35, "query": "불량률을 줄이는 최적화 방안을 제안해주세요", "expected_intent_type": "OPTIMIZATION", "expected_priority": "MEDIUM"},
    {"id": 36, "query": "챔버 청소 주기를 최적화하고 싶어요", "expected_intent_type": "OPTIMIZATION", "expected_priority": "MEDIUM"},
    {"id": 37, "query": "가스 사용량을 효율적으로 관리하려면?", "expected_intent_type": "OPTIMIZATION", "expected_priority": "MEDIUM"},
    {"id": 38, "query": "장비 가동률을 높이는 방법을 찾아주세요", "expected_intent_type": "OPTIMIZATION", "expected_priority": "MEDIUM"},
    {"id": 39, "query": "식각 균일도를 개선할 수 있나요?", "expected_intent_type": "OPTIMIZATION", "expected_priority": "MEDIUM"},
    {"id": 40, "query": "전력 소비를 최소화하면서 성능은 유지하고 싶어요", "expected_intent_type": "OPTIMIZATION", "expected_priority": "MEDIUM"},
    {"id": 41, "query": "레시피 파라미터를 최적화해주세요", "expected_intent_type": "OPTIMIZATION", "expected_priority": "MEDIUM"},
    {"id": 42, "query": "장비 활용도를 극대화하려면 어떻게 해야 하나요?", "expected_intent_type": "OPTIMIZATION", "expected_priority": "MEDIUM"},
    {"id": 43, "query": "공정 안정성을 향상시키고 싶어요", "expected_intent_type": "OPTIMIZATION", "expected_priority": "MEDIUM"},
    {"id": 44, "query": "웨이퍼 품질 일관성을 높이려면?", "expected_intent_type": "OPTIMIZATION", "expected_priority": "MEDIUM"},
    {"id": 45, "query": "반도체 제조 비용을 절감하고 싶습니다", "expected_intent_type": "OPTIMIZATION", "expected_priority": "MEDIUM"},
    {"id": 46, "query": "공급망 효율성을 개선할 방법은?", "expected_intent_type": "OPTIMIZATION", "expected_priority": "MEDIUM"},
    {"id": 47, "query": "장비 예방 보전 계획을 최적화해주세요", "expected_intent_type": "OPTIMIZATION", "expected_priority": "MEDIUM"},
    {"id": 48, "query": "생산 스케줄링을 개선하고 싶어요", "expected_intent_type": "OPTIMIZATION", "expected_priority": "MEDIUM"},
    {"id": 49, "query": "원자재 재고를 최적화하려면?", "expected_intent_type": "OPTIMIZATION", "expected_priority": "MEDIUM"},
    {"id": 50, "query": "인력 배치를 효율적으로 하고 싶어요", "expected_intent_type": "OPTIMIZATION", "expected_priority": "MEDIUM"},
    {"id": 51, "query": "설비 투자 우선순위를 정하고 싶어요", "expected_intent_type": "OPTIMIZATION", "expected_priority": "MEDIUM"},
    {"id": 52, "query": "제품 품질 관리 프로세스를 개선해주세요", "expected_intent_type": "OPTIMIZATION", "expected_priority": "MEDIUM"},
    {"id": 53, "query": "생산 라인 밸런싱을 최적화하려면?", "expected_intent_type": "OPTIMIZATION", "expected_priority": "MEDIUM"},
    {"id": 54, "query": "환경 영향을 최소화하면서 생산성을 높이려면?", "expected_intent_type": "OPTIMIZATION", "expected_priority": "MEDIUM"},
    {"id": 55, "query": "스마트 팩토리 구현을 위한 개선 방안은?", "expected_intent_type": "OPTIMIZATION", "expected_priority": "MEDIUM"},

    # CONTROL 케이스 (15건)
    {"id": 56, "query": "CVD 온도를 350도로 설정해주세요", "expected_intent_type": "CONTROL", "expected_priority": "MEDIUM"},
    {"id": 57, "query": "압력을 100mTorr로 조정해주세요", "expected_intent_type": "CONTROL", "expected_priority": "MEDIUM"},
    {"id": 58, "query": "가스 플로우를 50sccm으로 변경해주세요", "expected_intent_type": "CONTROL", "expected_priority": "MEDIUM"},
    {"id": 59, "query": "장비를 긴급 정지시켜주세요", "expected_intent_type": "CONTROL", "expected_priority": "HIGH"},
    {"id": 60, "query": "RF 파워를 2000W로 올려주세요", "expected_intent_type": "CONTROL", "expected_priority": "MEDIUM"},
    {"id": 61, "query": "펌프를 시작해주세요", "expected_intent_type": "CONTROL", "expected_priority": "MEDIUM"},
    {"id": 62, "query": "자동 모드로 전환해주세요", "expected_intent_type": "CONTROL", "expected_priority": "MEDIUM"},
    {"id": 63, "query": "레시피 A를 로드해주세요", "expected_intent_type": "CONTROL", "expected_priority": "MEDIUM"},
    {"id": 64, "query": "웨이퍼 처리를 시작해주세요", "expected_intent_type": "CONTROL", "expected_priority": "MEDIUM"},
    {"id": 65, "query": "챔버 퍼지를 실행해주세요", "expected_intent_type": "CONTROL", "expected_priority": "MEDIUM"},
    {"id": 66, "query": "진공 배기를 중지해주세요", "expected_intent_type": "CONTROL", "expected_priority": "MEDIUM"},
    {"id": 67, "query": "히터를 켜주세요", "expected_intent_type": "CONTROL", "expected_priority": "MEDIUM"},
    {"id": 68, "query": "공정을 일시정지해주세요", "expected_intent_type": "CONTROL", "expected_priority": "MEDIUM"},
    {"id": 69, "query": "안전 모드로 전환해주세요", "expected_intent_type": "CONTROL", "expected_priority": "HIGH"},
    {"id": 70, "query": "시스템을 리셋해주세요", "expected_intent_type": "CONTROL", "expected_priority": "MEDIUM"},

    # PREDICTION 케이스 (15건)
    {"id": 71, "query": "다음 주 생산량을 예측해주세요", "expected_intent_type": "PREDICTION", "expected_priority": "MEDIUM"},
    {"id": 72, "query": "장비 교체 시기가 언제쯤 될까요?", "expected_intent_type": "PREDICTION", "expected_priority": "MEDIUM"},
    {"id": 73, "query": "수율 트렌드 분석 결과를 알고 싶어요", "expected_intent_type": "PREDICTION", "expected_priority": "MEDIUM"},
    {"id": 74, "query": "향후 6개월간 유지보수 비용은?", "expected_intent_type": "PREDICTION", "expected_priority": "MEDIUM"},
    {"id": 75, "query": "이 설정으로 웨이퍼 품질이 어떻게 될까요?", "expected_intent_type": "PREDICTION", "expected_priority": "MEDIUM"},
    {"id": 76, "query": "연말까지 장비 가동률 전망은?", "expected_intent_type": "PREDICTION", "expected_priority": "MEDIUM"},
    {"id": 77, "query": "공정 변경 시 수율 변화를 예측해주세요", "expected_intent_type": "PREDICTION", "expected_priority": "MEDIUM"},
    {"id": 78, "query": "내일 생산 계획에 맞는 처리량 예상은?", "expected_intent_type": "PREDICTION", "expected_priority": "MEDIUM"},
    {"id": 79, "query": "장비 고장 위험도를 분석해주세요", "expected_intent_type": "PREDICTION", "expected_priority": "MEDIUM"},
    {"id": 80, "query": "다음 분기 에너지 사용량 예측이 필요해요", "expected_intent_type": "PREDICTION", "expected_priority": "MEDIUM"},
    {"id": 81, "query": "웨이퍼 불량률 추이를 분석해주세요", "expected_intent_type": "PREDICTION", "expected_priority": "MEDIUM"},
    {"id": 82, "query": "신규 레시피 적용 시 결과 예상치는?", "expected_intent_type": "PREDICTION", "expected_priority": "MEDIUM"},
    {"id": 83, "query": "장비 성능 저하 시점을 예측해주세요", "expected_intent_type": "PREDICTION", "expected_priority": "MEDIUM"},
    {"id": 84, "query": "공급망 차질이 생산에 미칠 영향은?", "expected_intent_type": "PREDICTION", "expected_priority": "MEDIUM"},
    {"id": 85, "query": "시장 수요에 따른 생산량 조정 분석", "expected_intent_type": "PREDICTION", "expected_priority": "MEDIUM"},

    # INFORMATION 케이스 (15건)
    {"id": 86, "query": "현재 생산량이 얼마나 되나요?", "expected_intent_type": "INFORMATION", "expected_priority": "LOW"},
    {"id": 87, "query": "오늘 수율 현황을 알려주세요", "expected_intent_type": "INFORMATION", "expected_priority": "LOW"},
    {"id": 88, "query": "장비 가동률 통계를 보여주세요", "expected_intent_type": "INFORMATION", "expected_priority": "LOW"},
    {"id": 89, "query": "현재 웨이퍼 재고량은 얼마인가요?", "expected_intent_type": "INFORMATION", "expected_priority": "LOW"},
    {"id": 90, "query": "이번 주 생산 실적을 알려주세요", "expected_intent_type": "INFORMATION", "expected_priority": "LOW"},
    {"id": 91, "query": "장비별 처리량 데이터를 보여주세요", "expected_intent_type": "INFORMATION", "expected_priority": "LOW"},
    {"id": 92, "query": "품질 검사 결과를 확인하고 싶어요", "expected_intent_type": "INFORMATION", "expected_priority": "LOW"},
    {"id": 93, "query": "공정 파라미터 설정값을 알려주세요", "expected_intent_type": "INFORMATION", "expected_priority": "LOW"},
    {"id": 94, "query": "유지보수 기록을 조회해주세요", "expected_intent_type": "INFORMATION", "expected_priority": "LOW"},
    {"id": 95, "query": "에너지 사용량 현황은 어떻게 되나요?", "expected_intent_type": "INFORMATION", "expected_priority": "LOW"},
    {"id": 96, "query": "현재 가동 중인 장비 목록을 알려주세요", "expected_intent_type": "INFORMATION", "expected_priority": "LOW"},
    {"id": 97, "query": "공정별 소요시간 데이터를 보여주세요", "expected_intent_type": "INFORMATION", "expected_priority": "LOW"},
    {"id": 98, "query": "원자재 소모량 통계가 궁금해요", "expected_intent_type": "INFORMATION", "expected_priority": "LOW"},
    {"id": 99, "query": "불량품 발생 현황을 알려주세요", "expected_intent_type": "INFORMATION", "expected_priority": "LOW"},
    {"id": 100, "query": "현재 시스템 상태를 확인하고 싶어요", "expected_intent_type": "INFORMATION", "expected_priority": "LOW"}
]

class ManufacturingDatasetManager:
    """제조업 AI 데이터셋 관리자"""
    
    def __init__(self, base_dir: str = "data"):
        self.base_dir = base_dir
        self.ensure_directories()
    
    def ensure_directories(self):
        """필요한 디렉토리 생성"""
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(os.path.join(self.base_dir, "backups"), exist_ok=True)
        print(f"✅ 데이터 디렉토리 준비: {self.base_dir}")
    
    def save_as_json(self, filename: str = "manufacturing_dataset_100.json") -> str:
        """JSON 형식으로 저장 (권장)"""
        filepath = os.path.join(self.base_dir, filename)
        
        # 메타데이터와 함께 저장
        data_with_metadata = {
            "metadata": {
                "title": "제조업 AI 에이전트 명령어 분류 데이터셋",
                "description": "제조업 현장의 자연어 쿼리를 의도별로 분류하기 위한 테스트 데이터셋",
                "created_at": datetime.now().isoformat(),
                "total_samples": len(manufacturing_dataset),
                "format_version": "1.0",
                "intent_types": {
                    "ANOMALY_CHECK": "이상 감지 및 점검",
                    "OPTIMIZATION": "최적화 및 개선",
                    "CONTROL": "제어 및 조작",
                    "PREDICTION": "예측 및 분석",
                    "INFORMATION": "정보 조회"
                },
                "priority_levels": {
                    "HIGH": "긴급/중요",
                    "MEDIUM": "보통",
                    "LOW": "낮음"
                }
            },
            "dataset": manufacturing_dataset
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data_with_metadata, f, ensure_ascii=False, indent=2)
        
        print(f"✅ JSON 데이터셋 저장 완료: {filepath}")
        return filepath
    
    def save_as_csv(self, filename: str = "manufacturing_dataset_100.csv") -> str:
        """CSV 형식으로 저장 (Excel 호환)"""
        filepath = os.path.join(self.base_dir, filename)
        
        fieldnames = ['id', 'query', 'expected_intent_type', 'expected_priority']
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(manufacturing_dataset)
        
        print(f"✅ CSV 데이터셋 저장 완료: {filepath}")
        return filepath
    
    def save_as_excel(self, filename: str = "manufacturing_dataset_100.xlsx") -> str:
        """Excel 형식으로 저장 (분석용)"""
        try:
            import pandas as pd
            
            filepath = os.path.join(self.base_dir, filename)
            
            # 데이터프레임 생성
            df = pd.DataFrame(manufacturing_dataset)
            
            # Excel 파일로 저장 (다중 시트)
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # 전체 데이터
                df.to_excel(writer, sheet_name='전체데이터', index=False)
                
                # 의도별 분리
                for intent in df['expected_intent_type'].unique():
                    intent_df = df[df['expected_intent_type'] == intent]
                    sheet_name = intent.replace('_', ' ')[:31]
                    intent_df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # 통계 정보
                stats_data = []
                for intent in df['expected_intent_type'].unique():
                    count = len(df[df['expected_intent_type'] == intent])
                    percentage = count / len(df) * 100
                    stats_data.append({
                        '의도 유형': intent,
                        '데이터 수': count,
                        '비율(%)': round(percentage, 1)
                    })
                
                stats_df = pd.DataFrame(stats_data)
                stats_df.to_excel(writer, sheet_name='통계', index=False)
            
            print(f"✅ Excel 데이터셋 저장 완료: {filepath}")
            return filepath
            
        except ImportError:
            print("❌ pandas 라이브러리가 필요합니다: pip install pandas openpyxl")
            return ""
    
    def backup_dataset(self) -> str:
        """데이터셋 백업 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"manufacturing_dataset_backup_{timestamp}.json"
        backup_path = os.path.join(self.base_dir, "backups", backup_filename)
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(manufacturing_dataset, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 백업 생성 완료: {backup_path}")
        return backup_path
    
    def load_dataset(self, filename: str = "manufacturing_dataset_100.json") -> List[Dict[str, Any]]:
        """저장된 데이터셋 로드"""
        filepath = os.path.join(self.base_dir, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 메타데이터가 있는 경우 데이터셋만 추출
            if isinstance(data, dict) and "dataset" in data:
                dataset = data["dataset"]
                print(f"✅ 데이터셋 로드 완료: {len(dataset)}건")
                return dataset
            else:
                print(f"✅ 데이터셋 로드 완료: {len(data)}건")
                return data
                
        except FileNotFoundError:
            print(f"❌ 파일을 찾을 수 없습니다: {filepath}")
            return []
        except json.JSONDecodeError:
            print(f"❌ JSON 파일 형식 오류: {filepath}")
            return []
    
    def analyze_dataset(self) -> Dict[str, Any]:
        """데이터셋 분석"""
        intent_counts = {}
        priority_counts = {}
        
        for item in manufacturing_dataset:
            intent = item['expected_intent_type']
            priority = item['expected_priority']
            
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        analysis = {
            "total_samples": len(manufacturing_dataset),
            "intent_distribution": intent_counts,
            "priority_distribution": priority_counts,
            "balance_score": min(intent_counts.values()) / max(intent_counts.values())
        }
        
        print("📊 데이터셋 분석 결과:")
        print(f"총 데이터 수: {analysis['total_samples']}건")
        print("\n의도별 분포:")
        for intent, count in intent_counts.items():
            percentage = count / len(manufacturing_dataset) * 100
            print(f"  {intent}: {count}건 ({percentage:.1f}%)")
        
        print("\n우선순위별 분포:")
        for priority, count in priority_counts.items():
            percentage = count / len(manufacturing_dataset) * 100
            print(f"  {priority}: {count}건 ({percentage:.1f}%)")
        
        print(f"\n데이터 균형도: {analysis['balance_score']:.2f} (1.0에 가까울수록 균형)")
        
        return analysis
    
    def save_all_formats(self) -> Dict[str, str]:
        """모든 형식으로 저장"""
        results = {}
        
        print("💾 모든 형식으로 데이터셋 저장 중...")
        
        # JSON 저장
        results['json'] = self.save_as_json()
        
        # CSV 저장
        results['csv'] = self.save_as_csv()
        
        # Excel 저장 (라이브러리가 있는 경우)
        excel_path = self.save_as_excel()
        if excel_path:
            results['excel'] = excel_path
        
        # 백업 생성
        results['backup'] = self.backup_dataset()
        
        print(f"✅ 모든 형식 저장 완료! 총 {len(results)}개 파일")
        return results

def quick_save():
    """빠른 저장 실행"""
    manager = ManufacturingDatasetManager()
    
    # 데이터셋 분석
    manager.analyze_dataset()
    
    # 모든 형식으로 저장
    saved_files = manager.save_all_formats()
    
    print(f"\n📁 저장된 파일들:")
    for format_type, filepath in saved_files.items():
        print(f"  {format_type.upper()}: {filepath}")
    
    print(f"\n🎯 사용 권장사항:")
    print(f"  - 프로그래밍 작업: manufacturing_dataset_100.json")
    print(f"  - Excel에서 확인: manufacturing_dataset_100.csv")
    print(f"  - 데이터 분석: manufacturing_dataset_100.xlsx")
    
    return saved_files

def create_sample_usage_script():
    """데이터셋 사용 예제 스크립트 생성"""
    
    usage_script = '''#!/usr/bin/env python3
"""
제조업 AI 데이터셋 사용 예제
"""
import json
import os

def load_and_use_dataset():
    """데이터셋 로드 및 사용 예제"""
    
    # 1. JSON 데이터셋 로드
    with open('data/manufacturing_dataset_100.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 메타데이터와 데이터셋 분리
    metadata = data.get('metadata', {})
    dataset = data.get('dataset', [])
    
    print(f"데이터셋 정보:")
    print(f"  제목: {metadata.get('title', 'Unknown')}")
    print(f"  총 데이터 수: {len(dataset)}건")
    print(f"  생성일: {metadata.get('created_at', 'Unknown')}")
    
    # 2. 의도별 데이터 분류
    intent_groups = {}
    for item in dataset:
        intent = item['expected_intent_type']
        if intent not in intent_groups:
            intent_groups[intent] = []
        intent_groups[intent].append(item)
    
    # 3. 샘플 데이터 출력
    print(f"\\n각 의도별 샘플 데이터:")
    for intent, items in intent_groups.items():
        print(f"\\n{intent} ({len(items)}건):")
        for item in items[:3]:  # 각 의도별로 3개씩만 출력
            print(f"  ID {item['id']}: {item['query']}")
            print(f"    → Priority: {item['expected_priority']}")

if __name__ == "__main__":
    load_and_use_dataset()
'''
    
    script_path = "data/usage_example.py"
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(usage_script)
    
    print(f"✅ 사용 예제 스크립트 생성: {script_path}")
    return script_path

def validate_dataset_format():
    """데이터셋 형식 검증"""
    
    print("🔍 데이터셋 형식 검증 중...")
    
    # 필수 필드 검증
    required_fields = ['id', 'query', 'expected_intent_type', 'expected_priority']
    valid_intents = ['ANOMALY_CHECK', 'OPTIMIZATION', 'CONTROL', 'PREDICTION', 'INFORMATION']
    valid_priorities = ['HIGH', 'MEDIUM', 'LOW']
    
    errors = []
    warnings = []
    
    for i, item in enumerate(manufacturing_dataset):
        # 필수 필드 확인
        for field in required_fields:
            if field not in item:
                errors.append(f"ID {item.get('id', i+1)}: 필수 필드 '{field}' 누락")
        
        # 의도 유형 검증
        if 'expected_intent_type' in item:
            if item['expected_intent_type'] not in valid_intents:
                errors.append(f"ID {item['id']}: 잘못된 의도 유형 '{item['expected_intent_type']}'")
        
        # 우선순위 검증
        if 'expected_priority' in item:
            if item['expected_priority'] not in valid_priorities:
                errors.append(f"ID {item['id']}: 잘못된 우선순위 '{item['expected_priority']}'")
        
        # 쿼리 길이 검증
        if 'query' in item:
            if len(item['query']) < 5:
                warnings.append(f"ID {item['id']}: 쿼리가 너무 짧습니다 (5자 미만)")
            elif len(item['query']) > 200:
                warnings.append(f"ID {item['id']}: 쿼리가 너무 깁니다 (200자 초과)")
    
    # ID 중복 검증
    ids = [item['id'] for item in manufacturing_dataset]
    if len(ids) != len(set(ids)):
        errors.append("ID 중복이 발견되었습니다")
    
    # 결과 출력
    if errors:
        print(f"❌ 검증 실패: {len(errors)}개 오류 발견")
        for error in errors[:5]:  # 처음 5개만 출력
            print(f"  - {error}")
        if len(errors) > 5:
            print(f"  ... 및 {len(errors)-5}개 더")
    else:
        print("✅ 데이터셋 형식 검증 통과")
    
    if warnings:
        print(f"⚠️  {len(warnings)}개 경고:")
        for warning in warnings[:3]:  # 처음 3개만 출력
            print(f"  - {warning}")
        if len(warnings) > 3:
            print(f"  ... 및 {len(warnings)-3}개 더")
    
    return len(errors) == 0

def create_evaluation_compatible_format():
    """평가 시스템과 호환되는 형식으로 변환"""
    
    # 기존 코드와 호환성을 위해 필드명 변경
    compatible_dataset = []
    
    for item in manufacturing_dataset:
        compatible_item = {
            "id": item["id"],
            "query": item["query"],
            "expected_intent": item["expected_intent_type"],  # 기존 코드 호환
            "expected_priority": item["expected_priority"]
        }
        compatible_dataset.append(compatible_item)
    
    # 호환 버전 저장
    compat_path = os.path.join("data", "compatible_dataset_100.json")
    with open(compat_path, 'w', encoding='utf-8') as f:
        json.dump(compatible_dataset, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 호환 형식 데이터셋 생성: {compat_path}")
    return compat_path

def generate_readme():
    """README 파일 생성"""
    
    readme_content = """# 제조업 AI 에이전트 명령어 분류 데이터셋

## 개요
반도체 제조업 현장에서 발생하는 자연어 쿼리를 5가지 의도로 분류하기 위한 테스트 데이터셋입니다.

## 데이터셋 구성
- **총 데이터 수**: 100건
- **의도 유형**: 5개 (ANOMALY_CHECK, OPTIMIZATION, CONTROL, PREDICTION, INFORMATION)
- **우선순위**: 3개 (HIGH, MEDIUM, LOW)

### 의도별 분포
- **ANOMALY_CHECK**: 30건 (30%) - 이상 감지 및 점검
- **OPTIMIZATION**: 25건 (25%) - 최적화 및 개선
- **CONTROL**: 15건 (15%) - 제어 및 조작
- **PREDICTION**: 15건 (15%) - 예측 및 분석
- **INFORMATION**: 15건 (15%) - 정보 조회

### 우선순위별 분포
- **HIGH**: 주로 ANOMALY_CHECK와 긴급 CONTROL
- **MEDIUM**: OPTIMIZATION, PREDICTION, 일반 CONTROL
- **LOW**: 대부분의 INFORMATION

## 파일 형식

### 1. JSON 형식 (권장)
```
manufacturing_dataset_100.json
```
- 메타데이터 포함
- 프로그래밍 작업에 최적
- UTF-8 인코딩

### 2. CSV 형식 (Excel 호환)
```
manufacturing_dataset_100.csv
```
- Excel에서 바로 열람 가능
- UTF-8 BOM 인코딩

### 3. Excel 형식 (분석용)
```
manufacturing_dataset_100.xlsx
```
- 다중 시트 구조
- 의도별 분리된 시트
- 통계 정보 시트 포함

## 데이터 구조

### JSON 형식
```json
{
  "metadata": {
    "title": "제조업 AI 에이전트 명령어 분류 데이터셋",
    "created_at": "2024-12-18T...",
    "total_samples": 100,
    "intent_types": {...},
    "priority_levels": {...}
  },
  "dataset": [
    {
      "id": 1,
      "query": "3번 엣칭 장비 압력이 이상해요",
      "expected_intent_type": "ANOMALY_CHECK",
      "expected_priority": "HIGH"
    }
  ]
}
```

## 사용법

### 1. Python에서 로드
```python
import json

with open('data/manufacturing_dataset_100.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

dataset = data['dataset']
```

### 2. 평가 시스템과 연동
```python
from enhanced_instruction_rf import EnhancedInstructionRefinementClient
from evaluation_script import InstructionRFEvaluator

# 클라이언트 초기화
client = EnhancedInstructionRefinementClient()

# 평가 실행
evaluator = InstructionRFEvaluator(client, dataset)
metrics = evaluator.run_evaluation()
```

## 목표 성능
- **Intent 분류 정확도**: 99% 이상
- **Priority 분류 정확도**: 99% 이상
- **전체 정확도**: 99% 이상

## 데이터 예시

### ANOMALY_CHECK (이상 감지)
- "3번 엣칭 장비 압력이 이상해요" (HIGH)
- "플라즈마 챔버 압력 센서 상태 확인해주세요" (MEDIUM)

### OPTIMIZATION (최적화)
- "생산 수율을 개선하고 싶어요" (MEDIUM)
- "에너지 효율성을 높이는 방법을 알려주세요" (MEDIUM)

### CONTROL (제어)
- "장비를 긴급 정지시켜주세요" (HIGH)
- "CVD 온도를 350도로 설정해주세요" (MEDIUM)

### PREDICTION (예측)
- "다음 주 생산량을 예측해주세요" (MEDIUM)
- "장비 교체 시기가 언제쯤 될까요?" (MEDIUM)

### INFORMATION (정보)
- "현재 생산량이 얼마나 되나요?" (LOW)
- "오늘 수율 현황을 알려주세요" (LOW)

## 버전 관리
- v1.0: 초기 100건 데이터셋
- 백업 파일: `data/backups/manufacturing_dataset_backup_YYYYMMDD_HHMMSS.json`

## 라이선스
내부 연구용 데이터셋
"""
    
    readme_path = "data/README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"✅ README 파일 생성: {readme_path}")
    return readme_path

# 메인 실행 함수
def main():
    """전체 데이터셋 저장 프로세스 실행"""
    
    print("🚀 제조업 AI 데이터셋 저장 프로세스 시작")
    print("="*50)
    
    # 1. 데이터셋 형식 검증
    if not validate_dataset_format():
        print("❌ 데이터셋 형식 오류로 인해 중단합니다.")
        return
    
    # 2. 데이터셋 매니저 초기화
    manager = ManufacturingDatasetManager()
    
    # 3. 데이터셋 분석
    analysis = manager.analyze_dataset()
    
    # 4. 모든 형식으로 저장
    saved_files = manager.save_all_formats()
    
    # 5. 평가 시스템 호환 형식 생성
    compat_path = create_evaluation_compatible_format()
    
    # 6. 사용 예제 스크립트 생성
    example_path = create_sample_usage_script()
    
    # 7. README 파일 생성
    readme_path = generate_readme()
    
    print("\n" + "="*50)
    print("✅ 데이터셋 저장 프로세스 완료!")
    print(f"\n📊 데이터셋 요약:")
    print(f"  총 데이터: {analysis['total_samples']}건")
    print(f"  의도 유형: {len(analysis['intent_distribution'])}개")
    print(f"  데이터 균형도: {analysis['balance_score']:.2f}")
    
    print(f"\n📁 생성된 파일들:")
    for file_type, path in saved_files.items():
        print(f"  {file_type.upper()}: {path}")
    print(f"  호환성: {compat_path}")
    print(f"  예제: {example_path}")
    print(f"  문서: {readme_path}")
    
    print(f"\n🎯 다음 단계:")
    print(f"  1. 데이터 확인: data/manufacturing_dataset_100.csv 열어보기")
    print(f"  2. 시스템 테스트: python usage_example.py")
    print(f"  3. 평가 실행: enhanced_instruction_rf.py 사용")

if __name__ == "__main__":
    # 빠른 저장 실행
    quick_save()
    
    print("\n" + "="*50)
    print("상세 프로세스를 실행하려면 main() 함수를 호출하세요:")
    print("python complete_dataset_with_storage.py")
    
    # 전체 프로세스 실행 (주석 해제하여 사용)
    main()