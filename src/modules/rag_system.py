from typing import List
from ..core.config import settings

class RAGSystem:
    """
    Retrieval-Augmented Generation (RAG) 시스템을 담당하는 클래스입니다.
    외부 지식 베이스(Vector DB)와 에이전트 메모리로부터 관련 정보를 검색하여
    에이전트의 응답 생성을 보강합니다.
    """
    def __init__(self):
        """
        RAGSystem을 초기화합니다.
        Vector DB 클라이언트, 임베딩 모델 등을 로드합니다.
        """
        # self.vector_store = Chroma(persist_directory=settings.VECTOR_DB_PATH)
        # self.embedding_function = SentenceTransformer('all-MiniLM-L6-v2')
        print(f"INFO:     RAGSystem initialized. (Vector DB path: {settings.VECTOR_DB_PATH})")
        pass

    def retrieve_knowledge(self, query: str, top_k: int = 3) -> List[str]:
        """
        주어진 질의와 관련된 외부 지식(문서)을 검색합니다.

        Args:
            query (str): 검색할 질의
            top_k (int): 검색할 문서의 수

        Returns:
            List[str]: 검색된 문서 내용 또는 ID 목록
        """
        print(f"INFO:     Retrieving knowledge for query: '{query}'")

        # --- 실제 RAG 로직 (향후 구현) ---
        # query_embedding = self.embedding_function.encode(query)
        # results = self.vector_store.similarity_search_by_vector(query_embedding, k=top_k)
        # return [doc.page_content for doc in results]

        # 현재는 목업 데이터를 반환합니다.
        mock_documents = [
            f"'{query}' 관련 문서 1: ...내용...",
            f"'{query}' 관련 문서 2: ...내용...",
            f"'{query}' 관련 문서 3: ...내용...",
        ]
        return mock_documents[:top_k]

    def retrieve_from_memory(self, user_id: str, top_k: int = 3) -> List[str]:
        """
        과거 상호작용 기록(에이전트 메모리)을 검색합니다.

        Args:
            user_id (str): 사용자의 ID
            top_k (int): 검색할 기록의 수

        Returns:
            List[str]: 관련 과거 상호작용 기록 목록
        """
        print(f"INFO:     Retrieving memory for user: '{user_id}'")
        # Agent Memory DB에서 데이터를 가져오는 로직 구현
        return [
            f"'{user_id}'의 과거 상호작용 1",
            f"'{user_id}'의 과거 상호작용 2",
        ][:top_k] 