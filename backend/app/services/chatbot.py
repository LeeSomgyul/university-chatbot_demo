"""
챗봇 메인 로직 - 모든 서비스 통합
"""
from typing import Dict, Any, Optional, List
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from app.config import settings
from app.models.schemas import UserProfile, ChatMessage
from app.services.query_router import query_router
from app.services.vector_service import get_vector_service
from app.services.curriculum_service import curriculum_service


class SchoolChatbot:
    """학교 챗봇 메인 클래스"""
    
    def __init__(self):
        # LLM 초기화 (lazy loading)
        self.llm = None
        self.vector_service = get_vector_service()
    
    def _get_llm(self) -> ChatOpenAI:
        """LLM 인스턴스 가져오기 (싱글톤)"""
        if self.llm is None:
            self.llm = ChatOpenAI(
                model=settings.model_name,
                temperature=settings.temperature,
                max_tokens=settings.max_tokens,
                openai_api_key=settings.openai_api_key
            )
        return self.llm
    
    def chat(
        self,
        message: str,
        user_profile: Optional[UserProfile] = None,
        history: List[ChatMessage] = None
    ) -> Dict[str, Any]:
        """
        메인 챗봇 로직
        
        Args:
            message: 사용자 메시지
            user_profile: 사용자 프로필 (학번, 수강이력 등)
            history: 대화 히스토리
        
        Returns:
            {
                "message": "답변",
                "query_type": "general|curriculum|hybrid",
                "sources": [...],
                "needs_profile": False
            }
        """
        # 1. 질문 분류
        query_type = query_router.classify(message)
        needs_profile = query_router.needs_user_profile(message)
        
        # 2. 사용자 프로필 필요한데 없으면 요청
        if needs_profile and not user_profile:
            return {
                "message": "개인 맞춤 답변을 위해 학번과 수강 이력을 먼저 알려주세요. 😊",
                "query_type": query_type,
                "sources": [],
                "needs_profile": True
            }
        
        # 3. 질문 유형별 처리
        if query_type == "curriculum":
            return self._handle_curriculum_query(message, user_profile)
        
        elif query_type == "general":
            return self._handle_general_query(message)
        
        else:  # hybrid
            return self._handle_hybrid_query(message, user_profile)
    
    def _handle_general_query(self, message: str) -> Dict[str, Any]:
        """일반 정보 질문 처리 (벡터 검색)"""
        # 벡터 검색
        search_results = self.vector_service.search(message, k=3)
        
        if not search_results:
            return {
                "message": "죄송해요, 관련 정보를 찾을 수 없어요. 다른 질문을 해주시겠어요? 🤔",
                "query_type": "general",
                "sources": [],
                "needs_profile": False
            }
        
        # 검색 결과를 컨텍스트로 사용
        context = self.vector_service.format_search_results(search_results)
        
        # LLM 프롬프트
        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 순천대학교 컴퓨터공학과 안내 챗봇입니다.
            주어진 정보를 바탕으로 학생의 질문에 친절하고 정확하게 답변해주세요.

            답변 규칙:
            1. 존댓말을 사용하고 친근하게 답변하세요
            2. 주어진 정보에 없는 내용은 "정보를 찾을 수 없습니다"라고 솔직히 말하세요
            3. 답변은 간결하게 핵심만 전달하세요
            4. 필요시 이모지를 활용해 친근함을 더하세요

            검색된 정보:
            {context}
            """),
            ("user", "{question}")
        ])
        
        # LLM 호출
        llm = self._get_llm()
        chain = prompt | llm
        
        try:
            response = chain.invoke({
                "context": context,
                "question": message
            })
            
            answer = response.content
        except Exception as e:
            print(f"❌ LLM 호출 실패: {e}")
            answer = "죄송해요, 답변 생성 중 오류가 발생했어요. 다시 시도해주세요. 😅"
        
        return {
            "message": answer,
            "query_type": "general",
            "sources": search_results,
            "needs_profile": False
        }
    
    def _handle_curriculum_query(
        self, 
        message: str, 
        user_profile: UserProfile
    ) -> Dict[str, Any]:
        """교육과정 질문 처리 (SQL 계산)"""
        
        # 남은 학점 계산
        calculation = curriculum_service.calculate_remaining_credits(user_profile)
        
        if 'error' in calculation:
            return {
                "message": calculation['error'],
                "query_type": "curriculum",
                "sources": [],
                "needs_profile": False
            }
        
        # 계산 결과 포맷팅
        curriculum_info = curriculum_service.format_curriculum_info(calculation)
        
        # 특정 영역 과목 목록이 필요한지 판단
        course_list = ""
        if any(kw in message for kw in ['과목', '무엇', '뭐', '어떤', '남았']):
            # 질문에서 영역 추출 시도
            area = None
            if '전공필수' in message:
                area = '전공필수'
            elif '전공선택' in message:
                area = '전공선택'
            elif '교양' in message:
                area = '교양필수'
            
            if area:
                not_taken = curriculum_service.get_courses_not_taken(user_profile, area)
                if not_taken:
                    course_list = f"\n\n📚 아직 안 들은 {area} 과목:\n"
                    for course in not_taken[:10]:  # 최대 10개만
                        course_list += f"- {course['course_name']} ({course['credit']}학점)\n"
        
        # LLM으로 자연스러운 답변 생성
        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 순천대학교 컴퓨터공학과 학사 상담 챗봇입니다.
            학생의 졸업요건과 수강이력을 바탕으로 친절하게 안내해주세요.

            답변 규칙:
            1. 계산된 정보를 바탕으로 답변하세요
            2. 학생을 격려하고 응원하는 톤을 유지하세요
            3. 구체적인 숫자와 정보를 포함하세요
            4. 필요시 다음 수강 추천도 해주세요

            학생 정보:
            - 학번: {admission_year}
            - 트랙: {track}

            졸업요건 현황:
            {curriculum_info}

            {course_list}
            """),
            ("user", "{question}")
        ])
        
        llm = self._get_llm()
        chain = prompt | llm
        
        try:
            response = chain.invoke({
                "admission_year": user_profile.admission_year,
                "track": user_profile.track,
                "curriculum_info": curriculum_info,
                "course_list": course_list,
                "question": message
            })
            answer = response.content
        except Exception as e:
            print(f"❌ LLM 호출 실패: {e}")
            # LLM 실패 시 계산 결과만 반환
            
    # app/services/chatbot.py에서 확인

    def _handle_hybrid_query(
        self,
        message: str,
        user_profile: Optional[UserProfile]
    ) -> Dict[str, Any]:
        """복합 질문 처리 (벡터 + SQL)"""
        
        # 1. 벡터 검색
        search_results = self.vector_service.search(message, k=2)
        context = self.vector_service.format_search_results(search_results)
        
        # 2. 교육과정 정보 (프로필이 있으면)
        curriculum_info = ""
        if user_profile:
            calculation = curriculum_service.calculate_remaining_credits(user_profile)
            if 'error' not in calculation:
                curriculum_info = curriculum_service.format_curriculum_info(calculation)
        
        # 3. LLM으로 통합 답변
        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 순천대학교 컴퓨터공학과 종합 안내 챗봇입니다.
            학교 정보와 학생의 개인 학사 정보를 종합해 답변해주세요.

            학교 정보:
            {context}

            {curriculum_section}

            답변 규칙:
            1. 두 가지 정보를 자연스럽게 연결해 답변하세요
            2. 학생의 상황에 맞는 조언을 제공하세요
            3. 친절하고 격려하는 톤을 유지하세요
            """),
                    ("user", "{question}")
        ])
        
        curriculum_section = ""
        if curriculum_info:
            curriculum_section = f"학생 졸업요건 현황:\n{curriculum_info}"
        
        llm = self._get_llm()
        chain = prompt | llm
        
        try:
            response = chain.invoke({
                "context": context,
                "curriculum_section": curriculum_section,
                "question": message
            })
            answer = response.content
        except Exception as e:
            print(f"❌ LLM 호출 실패: {e}")
            answer = f"{context}\n\n{curriculum_info}" if curriculum_info else context
        
        return {
            "message": answer,
            "query_type": "hybrid",
            "sources": search_results,
            "needs_profile": False
        }
chatbot = SchoolChatbot()