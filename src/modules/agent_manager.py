from typing import Dict, List, Optional
from ..api.schemas import AgentInfo

class AgentManager:
    """
    시스템에 등록된 모든 AI 에이전트를 관리하는 클래스입니다.
    에이전트의 등록, 정보 조회, 특정 능력을 갖춘 에이전트 검색 등의 기능을 담당합니다.
    """
    def __init__(self):
        """
        AgentManager를 초기화합니다.
        현재는 에이전트 정보를 인메모리 딕셔너리에 저장하지만,
        향후에는 데이터베이스나 서비스 레지스트리에서 정보를 불러올 수 있습니다.
        """
        self._agents: Dict[str, AgentInfo] = {}
        self._load_mock_agents()
        print(f"INFO:     AgentManager initialized with {len(self._agents)} agents.")

    def _load_mock_agents(self):
        """개발용 목업 에이전트들을 등록합니다."""
        mock_agents = [
            AgentInfo(id="agent_monitor_001", name="모니터링 에이전트", description="센서 데이터 조회 및 이상 감지", capabilities=["pressure_monitoring", "temperature_analysis"]),
            AgentInfo(id="agent_analysis_002", name="원인 분석 에이전트", description="데이터 기반 근본 원인 분석", capabilities=["root_cause_analysis"]),
            AgentInfo(id="agent_control_003", name="자율 제어 에이전트", description="분석 결과에 따른 시스템 자동 제어", capabilities=["valve_control", "parameter_adjustment"]),
        ]
        for agent in mock_agents:
            self.register_agent(agent)

    def register_agent(self, agent_info: AgentInfo):
        """
        새로운 에이전트를 시스템에 등록합니다.

        Args:
            agent_info (AgentInfo): 등록할 에이전트의 정보
        """
        print(f"INFO:     Registering agent: {agent_info.name} (ID: {agent_info.id})")
        self._agents[agent_info.id] = agent_info

    def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """
        주어진 ID를 가진 에이전트의 정보를 반환합니다.

        Args:
            agent_id (str): 찾으려는 에이전트의 ID

        Returns:
            Optional[AgentInfo]: 에이전트 정보. 없으면 None을 반환합니다.
        """
        return self._agents.get(agent_id)

    def list_agents(self) -> List[AgentInfo]:
        """
        시스템에 등록된 모든 에이전트의 목록을 반환합니다.

        Returns:
            List[AgentInfo]: 에이전트 정보 목록
        """
        return list(self._agents.values())

    def find_agent_for_capability(self, capability: str) -> Optional[AgentInfo]:
        """
        특정 능력(capability)을 수행할 수 있는 에이전트를 찾습니다.
        (현재는 가장 먼저 찾은 에이전트를 반환하는 간단한 방식입니다.)

        Args:
            capability (str): 필요한 능력

        Returns:
            Optional[AgentInfo]: 해당 능력을 가진 에이전트 정보. 없으면 None.
        """
        for agent in self._agents.values():
            if capability in agent.capabilities:
                return agent
        return None 