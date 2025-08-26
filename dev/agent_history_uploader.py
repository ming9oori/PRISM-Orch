#!/usr/bin/env python3
"""
Agent History Uploader

Orchestration Agent의 하위 에이전트들의 요청/응답 결과를 
AgentInteractionSummaryTool을 사용하여 요약한 후 Weaviate의 history 도메인에 업로드합니다.

Based on scenarios:
- assets/agent_interaction_scenarios.json
"""

import json
import os
import sys
import time
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import requests

# Python path setup for local development  
sys.path.append('/app/src')
sys.path.append('/app')  # Add for local prism_core

# PRISM-Orch tools import
try:
    from src.orchestration.tools import AgentInteractionSummaryTool
    from src.orchestration.tools.agent_interaction_summary_tool import ToolRequest, ToolResponse
    ORCH_TOOLS_AVAILABLE = True
    logger_msg = "PRISM-Orch tools 사용"
except ImportError:
    ORCH_TOOLS_AVAILABLE = False  
    logger_msg = "PRISM-Orch tools 없음 - 직접 Weaviate API 사용"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentHistoryUploader:
    def __init__(self, 
                 weaviate_url: str = "http://weaviate:8080",
                 openai_base_url: str = "http://localhost:8000/v1",
                 openai_api_key: str = "dummy-key",
                 model_name: str = "gpt-3.5-turbo",
                 class_prefix: str = "ORCH"):
        """
        Initialize Agent History Uploader
        
        Args:
            weaviate_url: Weaviate instance URL
            openai_base_url: OpenAI compatible API URL
            openai_api_key: OpenAI API key
            model_name: Model name for summarization
            class_prefix: Prefix for Weaviate class names (ORCHHistory)
        """
        self.weaviate_url = weaviate_url
        self.class_prefix = class_prefix
        self.history_class = f"{class_prefix}History"
        
        # Initialize AgentInteractionSummaryTool if available
        self.summary_tool = None
        if ORCH_TOOLS_AVAILABLE:
            try:
                self.summary_tool = AgentInteractionSummaryTool(
                    weaviate_url=weaviate_url,
                    openai_base_url=openai_base_url,
                    openai_api_key=openai_api_key,
                    model_name=model_name,
                    client_id="agent_history_uploader",
                    class_prefix=class_prefix
                )
                logger.info("✅ AgentInteractionSummaryTool 초기화 완료")
            except Exception as e:
                logger.warning(f"⚠️  AgentInteractionSummaryTool 초기화 실패: {e}")
                self.summary_tool = None
        
        # Wait for Weaviate to be ready
        self._wait_for_weaviate()
        
        # Create schema
        self._create_history_schema()
        
        logger.info(f"Initialized Agent History Uploader with class: {self.history_class} ({logger_msg})")
    
    def _wait_for_weaviate(self):
        """Wait for Weaviate to be ready"""
        max_retries = 30
        retry_delay = 10
        
        for attempt in range(max_retries):
            try:
                response = requests.get(f"{self.weaviate_url}/v1/.well-known/ready", timeout=5)
                if response.status_code == 200:
                    logger.info("Successfully connected to Weaviate")
                    return
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    logger.error("Failed to connect to Weaviate after all retries")
                    sys.exit(1)
    
    def _create_history_schema(self):
        """Create Weaviate history schema"""
        schema = {
            "class": self.history_class,
            "description": "Agent execution history - requests, responses, and workflow tracking",
            "vectorizer": "text2vec-transformers",
            "moduleConfig": {
                "text2vec-transformers": {
                    "vectorizeClassName": False
                }
            },
            "properties": [
                {
                    "name": "title",
                    "dataType": ["text"],
                    "description": "History entry title"
                },
                {
                    "name": "content",
                    "dataType": ["text"],
                    "description": "Detailed history content"
                },
                {
                    "name": "metadata",
                    "dataType": ["text"],
                    "description": "Agent interaction metadata (JSON string)"
                }
            ]
        }
        
        try:
            response = requests.post(
                f"{self.weaviate_url}/v1/schema",
                json=schema,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            if response.status_code == 200:
                logger.info(f"✅ Created schema: {self.history_class}")
            elif response.status_code == 422:
                logger.info(f"Schema {self.history_class} already exists")
            else:
                logger.warning(f"⚠️  Failed to create schema {self.history_class}: {response.status_code}")
        except Exception as e:
            logger.error(f"Error creating schema {self.history_class}: {e}")
    
    def _upload_history_entry(self, title: str, content: str, metadata: Dict[str, Any]) -> bool:
        """Upload single history entry to Weaviate"""
        try:
            doc = {
                "title": title,
                "content": content,
                "metadata": json.dumps(metadata)
            }
            
            response = requests.post(
                f"{self.weaviate_url}/v1/objects",
                json={
                    "class": self.history_class,
                    "properties": doc
                },
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Uploaded history entry: {title}")
                return True
            else:
                logger.error(f"❌ Upload failed: {response.status_code} - {title}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Upload error: {e} - {title}")
            return False
    
    def _load_scenarios(self) -> Dict:
        """Load agent interaction scenarios from JSON file"""
        try:
            scenario_file = "/app/assets/agent_interaction_scenarios.json"
            with open(scenario_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load scenarios: {e}")
            raise
    
    async def create_sample_agent_interactions(self):
        """
        Create sample agent interactions based on JSON scenarios
        Uses AgentInteractionSummaryTool to generate intelligent summaries
        """
        scenarios_data = self._load_scenarios()
        
        total_uploaded = 0
        
        for scenario in scenarios_data["scenarios"]:
            incident_id = scenario["incident_id"]
            equipment = scenario["equipment"]
            timestamp = datetime.now(timezone.utc).isoformat()
            
            logger.info(f"Processing scenario: {scenario['title']} ({incident_id})")
            
            # Generate summary using AgentInteractionSummaryTool
            if self.summary_tool:
                summary_result = await self._generate_intelligent_summary(scenario)
                if summary_result:
                    # Upload summarized workflow entry
                    success = self._upload_summary_entry(scenario, summary_result, timestamp)
                    if success:
                        total_uploaded += 1
                else:
                    # Fallback to basic entry
                    success = self._upload_basic_entry(scenario, timestamp)
                    if success:
                        total_uploaded += 1
            else:
                # Fallback to basic entry when summary tool is not available
                success = self._upload_basic_entry(scenario, timestamp)
                if success:
                    total_uploaded += 1
        
        return total_uploaded

    async def _generate_intelligent_summary(self, scenario: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate intelligent summary using AgentInteractionSummaryTool"""
        try:
            # Prepare agent interactions data for the summary tool
            agent_interactions = scenario.get('agent_interactions', [])
            
            if not agent_interactions:
                logger.warning(f"No agent interactions found for scenario {scenario['incident_id']}")
                return None
            
            # Create tool request
            request = ToolRequest(parameters={
                "agent_interactions": agent_interactions,
                "incident_id": scenario['incident_id'],
                "context": f"Equipment: {scenario['equipment']}, Parameter: {scenario['parameter']}, User Query: {scenario['user_query']}"
            })
            
            # Execute summary tool
            response = await self.summary_tool.execute(request)
            
            if response.success:
                logger.info(f"✅ Generated summary for {scenario['incident_id']}")
                return response.data
            else:
                logger.error(f"❌ Summary generation failed: {response.error}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error generating summary: {e}")
            return None

    def _upload_summary_entry(self, scenario: Dict[str, Any], summary_data: Dict[str, Any], timestamp: str) -> bool:
        """Upload intelligent summary entry to Weaviate"""
        try:
            incident_id = scenario['incident_id']
            
            # Create rich summary content
            summary_content = f"""🔍 **에이전트 워크플로우 종합 요약**

**인시던트**: {incident_id} - {scenario['title']}
**장비**: {scenario['equipment']} | **매개변수**: {scenario['parameter']}
**사용자 문의**: "{scenario['user_query']}"

## 📊 워크플로우 분석
{summary_data['intelligent_summary']['workflow_summary']}

## 🔑 주요 발견사항
{chr(10).join(f"• {finding}" for finding in summary_data['intelligent_summary']['key_findings'])}

## ⚡ 성능 분석
- 총 상호작용: {summary_data['total_interactions']}개
- 평균 실행시간: {summary_data['performance_analysis']['average_execution_time_ms']:.1f}ms
- 효율성 등급: {summary_data['performance_analysis']['efficiency_grade']}

## 🤝 에이전트 협업 효과성
{summary_data['intelligent_summary']['agent_collaboration_effectiveness']}

## 📈 의사결정 품질
{summary_data['intelligent_summary']['decision_quality']}

## 💡 개선 권고사항
{chr(10).join(f"• {rec}" for rec in summary_data['intelligent_summary']['recommendations'])}

## ⚠️ 위험 요소
{chr(10).join(f"• {risk}" for risk in summary_data['intelligent_summary']['risk_factors'])}

## 🎯 전반적 평가
{summary_data['intelligent_summary']['overall_assessment']}
"""
            
            # Create metadata
            metadata = {
                "incident_id": incident_id,
                "workflow_type": "multi_agent_collaboration",
                "equipment": scenario['equipment'],
                "parameter": scenario['parameter'],
                "timestamp": timestamp,
                "summary_generated_by": "AgentInteractionSummaryTool",
                "total_interactions": summary_data['total_interactions'],
                "performance_grade": summary_data['performance_analysis']['efficiency_grade'],
                "workflow_metrics": summary_data.get('basic_metrics', {}),
                "intelligent_analysis": summary_data['intelligent_summary']
            }
            
            return self._upload_history_entry(
                title=f"[{incident_id}] 에이전트 워크플로우 종합 분석 - {scenario['title']}",
                content=summary_content,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to upload summary entry: {e}")
            return False

    def _upload_basic_entry(self, scenario: Dict[str, Any], timestamp: str) -> bool:
        """Upload basic entry when summary tool is not available"""
        try:
            incident_id = scenario['incident_id']
            
            # Basic content without intelligent analysis
            basic_content = f"""📋 **에이전트 상호작용 기록**

**인시던트**: {incident_id} - {scenario['title']}
**장비**: {scenario['equipment']} | **매개변수**: {scenario['parameter']}
**사용자 문의**: "{scenario['user_query']}"

## 상호작용 통계
- 총 상호작용 수: {len(scenario.get('agent_interactions', []))}개
- 관련 에이전트: {len(set([i.get('requester') for i in scenario.get('agent_interactions', [])] + [i.get('target') for i in scenario.get('agent_interactions', [])]))}개

## 최종 권고안
**선택된 조치**: {scenario.get('final_recommendation', {}).get('selected_action', 'N/A')}
**근거**: {scenario.get('final_recommendation', {}).get('rationale', 'N/A')}
**신뢰도**: {scenario.get('final_recommendation', {}).get('confidence_level', 'N/A')}

*참고: 상세한 분석을 위해 AgentInteractionSummaryTool을 활성화하세요.*
"""
            
            # Basic metadata
            metadata = {
                "incident_id": incident_id,
                "workflow_type": "basic_record",
                "equipment": scenario['equipment'],
                "parameter": scenario['parameter'],
                "timestamp": timestamp,
                "summary_generated_by": "basic_fallback",
                "total_interactions": len(scenario.get('agent_interactions', [])),
                "final_recommendation": scenario.get('final_recommendation', {})
            }
            
            return self._upload_history_entry(
                title=f"[{incident_id}] 에이전트 상호작용 기록 - {scenario['title']}",
                content=basic_content,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to upload basic entry: {e}")
            return False


async def main():
    """Main function"""
    # Environment variables
    weaviate_url = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
    openai_base_url = os.getenv("OPENAI_BASE_URL", "http://localhost:8000/v1")
    openai_api_key = os.getenv("OPENAI_API_KEY", "dummy-key")
    model_name = os.getenv("VLLM_MODEL", "gpt-3.5-turbo")
    class_prefix = os.getenv("CLASS_PREFIX", "ORCH")
    
    logger.info(f"🚀 Starting Agent History Uploader with {logger_msg}")
    
    # Initialize uploader
    uploader = AgentHistoryUploader(
        weaviate_url=weaviate_url,
        openai_base_url=openai_base_url,
        openai_api_key=openai_api_key,
        model_name=model_name,
        class_prefix=class_prefix
    )
    
    # Create and upload sample agent interactions
    total_uploaded = await uploader.create_sample_agent_interactions()
    
    logger.info(f"🎉 Agent history upload completed! Total entries: {total_uploaded}")


if __name__ == "__main__":
    asyncio.run(main())