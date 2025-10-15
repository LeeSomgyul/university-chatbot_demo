"""
챗봇 메인 로직 - 모든 서비스 통합
"""
from typing import Dict, Any, Optional, List
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from app.config import settings
from app.models.schemas import UserProfile, ChatMessage, CourseInput
from app.services.query_router import query_router
from app.services.vector_service import get_vector_service
from app.services.curriculum_service import curriculum_service
from app.services.entity_extractor import entity_extractor


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
        """메인 챗봇 로직"""
        
        # 1. 질문 분류
        query_type = query_router.classify(message)
        needs_profile = query_router.needs_user_profile(message)
        
        print(f"\n🔍 디버깅:")
        print(f"  메시지: {message}")
        print(f"  query_type: {query_type}")
        print(f"  user_profile: {user_profile}")
        print(f"  needs_profile: {needs_profile}")
        
        if query_type == "curriculum":
            extracted = entity_extractor.extract_course_info(message)
            print(f"  extracted: {extracted}")
            
            # 정보가 충분하면 UserProfile 생성
            if extracted['has_enough_info']:
                user_profile = UserProfile(
                    admission_year=extracted['admission_year'],
                    courses_taken=extracted['courses']
                )
                
                print(f"✅ UserProfile 자동 생성: {extracted['admission_year']}학번, {len(extracted['courses'])}과목")
            
            # 여전히 정보 부족하면 안내
            elif not user_profile:
                missing = []
                if not extracted['admission_year']:
                    missing.append("입학년도")
                if not extracted['course_codes']:
                    missing.append("이수 과목")
                
                return {
                    "message": f"""개인 맞춤 답변을 위해 정보가 필요해요! 😊

                    다음 정보를 알려주세요:
                    {'📅 입학년도 (예: 2024학번)' if '입학년도' in missing else ''}
                    {'📚 이수한 과목 코드 (예: CS0614, XG0800)' if '이수 과목' in missing else ''}

                    예시: "2024학번이고 CS0614, XG0800 들었어"
                    """,
                                        "query_type": query_type,
                                        "sources": [],
                                        "needs_profile": True
                }
                
            return self._handle_curriculum_query(message, user_profile)
        
        # 3. 질문 유형별 처리 (기존 코드)      
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
        """교육과정 질문 처리 (하이브리드)"""
        
        # 1. 남은 학점 계산
        calculation = curriculum_service.calculate_remaining_credits(user_profile)
        
        if 'error' in calculation:
            return {
                "message": calculation['error'],
                "query_type": "curriculum",
                "sources": [],
                "needs_profile": False
            }
        
        # 2. 포맷팅된 결과
        formatted_info = curriculum_service.format_curriculum_info(calculation)
        
        # 3. 간단한 질문인지 판단
        simple_keywords = [
            '남은', '얼마', '몇', '진행', '현황', '학점', '상태',
            '남았', '이수', '들었', '완료'
        ]
        
        is_simple = any(kw in message for kw in simple_keywords)
        
        # 복잡한 질문 키워드
        complex_keywords = [
            '졸업', '가능', '추천', '어떤', '무엇', '뭐',
            '해야', '하면', '좋', '조언', '도움'
        ]
        
        is_complex = any(kw in message for kw in complex_keywords)
        
        # 4-A. 간단한 질문 → 포맷팅만 반환
        if is_simple and not is_complex:
            print("  → 간단한 질문: 포맷팅만 반환")
            
            # 미이수 과목 추가 (요청 시)
            additional_info = ""
            if any(kw in message for kw in ['과목', '뭐', '어떤']):
                not_taken = curriculum_service.get_required_courses_not_taken(
                    user_profile,
                    course_area="전공",
                    requirement_type="전공필수"
                )
                
                if not_taken:
                    formatted_not_taken = curriculum_service.format_not_taken_courses(not_taken)
                    additional_info = "\n\n" + formatted_not_taken
            
            return {
                "message": formatted_info + additional_info,
                "query_type": "curriculum",
                "sources": [],
                "needs_profile": False
            }
        
        # 4-B. 복잡한 질문 → LLM 사용
        print("  → 복잡한 질문: LLM 사용")
        
        # 미이수 과목 정보
        not_taken_info = ""
        if any(kw in message for kw in ['과목', '무엇', '뭐', '어떤', '남았', '필수']):
            # 질문에서 영역 추출
            area = None
            req_type = None
            
            if '전공필수' in message:
                area = "전공"
                req_type = "전공필수"
            elif '전공선택' in message:
                area = "전공"
                req_type = "전공선택"
            elif '교양' in message:
                area = "교양"
            
            not_taken = curriculum_service.get_required_courses_not_taken(
                user_profile,
                course_area=area,
                requirement_type=req_type
            )
            
            if not_taken:
                not_taken_info = "\n\n📚 미이수 과목:\n"
                for course in not_taken[:10]:  # 최대 10개
                    not_taken_info += f"- {course['course_name']} ({course['credit']}학점)"
                    if course.get('recommended_semester'):
                        not_taken_info += f" [권장: {course['grade']}학년 {course['semester']}학기]"
                    not_taken_info += "\n"
        
        # LLM 프롬프트
        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 순천대학교 컴퓨터공학과 학사 상담 챗봇입니다.

    주어진 졸업요건 현황을 **정확히** 바탕으로 학생의 질문에 답변하세요.

    ⚠️ 중요:
    1. 아래 졸업요건 현황의 숫자를 정확히 사용하세요
    2. 임의로 숫자를 만들거나 추측하지 마세요
    3. 학생을 격려하고 응원하는 톤을 유지하세요
    4. 구체적인 조언을 제공하세요

    졸업요건 현황:
    {formatted_info}

    {not_taken_info}
    """),
            ("user", "{question}")
        ])
        
        llm = self._get_llm()
        chain = prompt | llm
        
        try:
            response = chain.invoke({
                "formatted_info": formatted_info,
                "not_taken_info": not_taken_info,
                "question": message
            })
            answer = response.content
            
        except Exception as e:
            print(f"❌ LLM 호출 실패: {e}")
            # LLM 실패 시 포맷팅 결과 반환
            answer = formatted_info + not_taken_info
        
        return {
            "message": answer,
            "query_type": "curriculum",
            "sources": [],
            "needs_profile": False
        }

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