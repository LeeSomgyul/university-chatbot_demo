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
        
        # 2. curriculum 질문 처리
        if query_type == "curriculum":
            
            # 메시지에서 정보 추출
            extracted = entity_extractor.extract_course_info(message)
            
            # 정보가 충분하면 UserProfile 생성
            if extracted['has_enough_info']:
                user_profile = UserProfile(
                    admission_year=extracted['admission_year'],
                    courses_taken=extracted['courses']
                )
                print(f"✅ UserProfile 자동 생성: {extracted['admission_year']}학번, {len(extracted['courses'])}과목")
                
                result = self._handle_curriculum_query(message, user_profile)
                result['user_profile'] = user_profile
                return result
            
            elif extracted['admission_year']:
                print(f"✅ 입학년도만 있음: {extracted['admission_year']}학번")
                
                # 빈 UserProfile 생성 (입학년도만)
                user_profile = UserProfile(
                    admission_year=extracted['admission_year'],
                    courses_taken=[]
                )
                
                # "전공필수", "교양" 등 키워드 체크
                return self._handle_curriculum_query(message, user_profile)
            
            # 정보 부족 시 안내
            elif not user_profile:
                is_assessment_request = any(kw in message for kw in [
                    '졸업사정', '졸업 가능', '졸업할 수 있', '졸업 확인',
                    '내 졸업', '나 졸업', '내가 졸업',
                    '내 상황', '내 현황', '나 현황',
                    '계산', '확인', '분석'
                ])
                
                needs_courses = any(kw in message for kw in [
                    '남은', '남았', '몇', '얼마', '들었', '이수', '수강',
                    '진행', '현황', '상태', '완료'
                ])or is_assessment_request
                
                # 어떤 정보가 부족한지 파악
                missing = []
                
                if not extracted['admission_year']:
                    missing.append("입학년도")
                
                if needs_courses and not extracted['course_codes']:
                    missing.append("이수한 과목")
                
                # 안내 메시지 생성
                if missing:
                    guide_message = "개인 맞춤 답변을 위해 다음 정보가 필요해요! 😊\n\n"
                    
                    if "입학년도" in missing:
                        guide_message += "📅 입학년도: 몇 학번이신가요?\n"
                    
                    if "이수한 과목" in missing:
                        guide_message += "📚 이수한 과목: 어떤 과목들을 들으셨나요?\n"
                        guide_message += "   (과목 코드 또는 과목명으로 알려주세요)\n"
                    
                    guide_message += "\n💡 예시:\n"
                    
                    if len(missing) == 2:
                        # 둘 다 필요
                        guide_message += "\"2024학번이고 CS0614, XG0800 들었어. 남은 학점 알려줘\"\n"
                        guide_message += "또는\n"
                        guide_message += "\"24학번, 컴퓨터과학이랑 대학생활 들었어\""
                    elif "입학년도" in missing:
                        # 입학년도만 필요
                        guide_message += "\"2024학번인데 전공필수 뭐야?\"\n"
                        guide_message += "또는\n"
                        guide_message += "\"24학번 교양 몇 학점 들어야 해?\""
                    else:
                        # 과목만 필요 (입학년도는 있음)
                        guide_message += "\"CS0614, XG0800 들었어\"\n"
                        guide_message += "또는\n"
                        guide_message += "\"컴퓨터과학이랑 대학생활 들었어\""
                    
                    return {
                        "message": guide_message,
                        "query_type": query_type,
                        "sources": [],
                        "needs_profile": True
                    }
                
                #  정보 없이 답변 가능한 질문
                # "전공필수 뭐야?", "교양 몇 학점?"
                else:
                    # 입학년도만 물어보기
                    return {
                        "message": """해당 정보를 알려드리려면 "입학년도"가 필요해요!

                        몇 학번이신가요? (예: 2024학번)

                        입학년도에 따라 졸업 요건이 달라져요. 😊""",
                        "query_type": query_type,
                        "sources": [],
                        "needs_profile": True
                    }
            
            # curriculum 처리
            return self._handle_curriculum_query(message, user_profile)
        
        # 3. general 질문 처리
        elif query_type == "general":
            return self._handle_general_query(message)
        
        # 4. hybrid 질문 처리
        else:
            return self._handle_hybrid_query(message, user_profile)
        
    def _extract_requirement_type(self, message: str) -> Dict[str, str]:
        """메시지에서 요건 타입 추출"""
        
        req_type = None
        course_area = None
        
        if '전필' in message or '전공필수' in message:
            req_type = '전공필수'
            course_area = '전공'
        elif '전선' in message or '전공선택' in message:
            req_type = '전공선택'
            course_area = '전공'
        elif '교필' in message or '교양필수' in message or '교양' in message:
            req_type = '공통교양'
            course_area = '교양'
        
        return {
            'type': req_type,
            'area': course_area
        }    
        
    def _get_required_credits(self, admission_year: int, requirement_type: str) -> int:
        """요건별 필요 학점 반환"""
        
        credit_map = {
            '전공선택': 34,
            '교양선택': 0,
            '심화교양': 11,
        }
        
        return credit_map.get(requirement_type, 0)
        
    def _handle_requirement_list_query(
        self,
        admission_year: int,
        course_area: str,
        requirement_type: str
    ) -> Dict[str, Any]:
        """요건별 전체 과목 리스트 반환"""
        
        try:
            from app.database.supabase_client import supabase
            
            # DB에서 해당 요건의 모든 과목 조회
            result = supabase.table('curriculums')\
                .select('*')\
                .eq('admission_year', admission_year)\
                .eq('course_area', course_area)\
                .eq('requirement_type', requirement_type)\
                .order('grade')\
                .order('semester')\
                .order('course_code')\
                .execute()
            
            if not result.data:
                return {
                    "message": f"{admission_year}학번 {requirement_type} 정보를 찾을 수 없어요. 😥",
                    "query_type": "curriculum",
                    "sources": [],
                    "needs_profile": False
                }
            
            # 중복 제거
            seen = set()
            unique_courses = []
            
            for course in result.data:
                code = course['course_code']
                if code not in seen:
                    seen.add(code)
                    unique_courses.append(course)
            
            print(f"  총 {len(result.data)}개 → 중복 제거 후 {len(unique_courses)}개")
            
            # 포맷팅
            answer = f"{admission_year}학번 {requirement_type} 과목 목록이에요!\n\n"
            
            current_grade = None
            for course in result.data:
                grade = course.get('grade')
                semester = course.get('semester')
                
                # 학년별 그룹화
                if grade != current_grade:
                    current_grade = grade
                    answer += f"\n🧑🏻‍🎓 {grade}학년\n"
                
                # 과목 정보
                answer += f"• {course['course_code']} {course['course_name']} ({course['credit']}학점)"
                
                if semester:
                    answer += f" - {semester}학기 권장"
                
                answer += "\n"
            
            # 총 과목 수와 학점
            total_courses = len(unique_courses)
            total_credits = sum(c['credit'] for c in unique_courses)
            
            if '선택' in requirement_type:
                # 전공선택, 교양선택 등
                required_credits = self._get_required_credits(admission_year, requirement_type)

                answer += f"\n💡 총 {total_courses}개 과목 중 선택하여 {required_credits}학점을 채우면 돼요!"
        
            else:
                # 전공필수, 교양필수 등
                answer += f"\n💡 총 {total_courses}개 과목, {total_credits}학점 모두 이수해야 해요!"
            
            return {
                "message": answer,
                "query_type": "curriculum",
                "sources": [],
                "needs_profile": False
            }
        
        except Exception as e:
            print(f"❌ 요건 조회 실패: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "message": "죄송해요, 과목 정보를 가져오는 중 오류가 발생했어요. 😥",
                "query_type": "curriculum",
                "sources": [],
                "needs_profile": False
            }    
            
    def _handle_curriculum_query(
        self, 
        message: str, 
        user_profile: UserProfile
    ) -> Dict[str, Any]:
        """교육과정 질문 처리 (하이브리드)"""
        
        # 0. 특수 질문 라우팅
        if any(kw in message for kw in ['대신', '대체', '바뀐', '과목명', '같은']):
            return self._handle_equivalent_course_query(message, user_profile)
    
        if any(kw in message for kw in ['추천', '뭐 들', '어떤 과목']):
            return self._handle_recommendation_query(message, user_profile)
        
        # 1. 과목 정보 없음 → 요건 조회 모드
        if not user_profile.courses_taken:
            print("  → 과목 정보 없음, 요건 조회 모드")
            
            # 요건 타입 추출
            req_info = self._extract_requirement_type(message)
            
            if req_info['type']:
                # 해당 요건의 전체 과목 리스트 반환
                return self._handle_requirement_list_query(
                    user_profile.admission_year,
                    req_info['area'],
                    req_info['type']
                )
            else:
                # 키워드 없음 → 재질문
                return {
                    "message": f"""{user_profile.admission_year}학번 어떤 과목 정보를 알려드릴까요? 😊

    1️⃣ 전공필수 - 꼭 들어야 하는 전공 과목
    2️⃣ 전공선택 - 선택할 수 있는 전공 과목  
    3️⃣ 교양 - 교양 필수 과목

    💡 예시:
    "{user_profile.admission_year}학번 전공필수 뭐야?"
    "{user_profile.admission_year}학번 교양 필수 알려줘"
    """,
                    "query_type": "curriculum",
                    "sources": [],
                    "needs_profile": False
                }
                
        # ===== 2. 과목 있음 → 기존 졸업사정 처리 =====
        
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
    5. 마크다운 문법(**, ##, - 등)을 사용하지 마세요. 순수 텍스트와 이모지만 사용하세요

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
        
    def _handle_equivalent_course_query(
        self,
        message: str,
        user_profile: UserProfile
    ) -> Dict[str, Any]:
        """동일대체 과목 질문 처리"""
        
        # 1. 과목 코드/명 추출
        course_codes = entity_extractor.extract_course_codes(message)
        course_names = entity_extractor.extract_course_names(message)
        
        print(f"  동일대체 질문: codes={course_codes}, names={course_names}")
        
        # 2. 과목 찾기
        target_course = None
        
        if course_codes:
            target_code = course_codes[0]
            target_course = curriculum_service._get_course_info(
                user_profile.admission_year,
                target_code
            )
        elif course_names:
            match = entity_extractor.search_course_by_name(
                course_names[0],
                user_profile.admission_year
            )
            if match:
                target_course = match
                target_code = match['course_code']
        
        if not target_course:
            return {
                "message": """해당 과목을 찾을 수 없어요. 😥

                과목 코드(예: CS0614) 또는 정확한 과목명을 알려주시겠어요?""",
                "query_type": "curriculum",
                "sources": [],
                "needs_profile": False
            }
        
        # 3. 동일대체 정보 조회
        # 구 → 신
        old_to_new = equivalent_course_service.get_equivalent_course(target_code)
        
        # 신 → 구 (향후 변경)
        future_changes = curriculum_service._get_alternative_codes(
            target_code,
            user_profile.admission_year
        )
        
        # 4. 답변 생성
        answer = f"**{target_course['course_name']}({target_code})**에 대한 동일대체 정보에요!\n\n"
        
        if old_to_new:
            answer += f"📌 **과거 과목명:**\n"
            answer += f"- {old_to_new['old_course_code']} {old_to_new['old_course_name']}\n"
            answer += f"  → {old_to_new['effective_year']}년에 {target_code} {target_course['course_name']}로 변경\n\n"
        
        if future_changes:
            answer += f"🔮 **향후 변경 예정:**\n"
            for change in future_changes:
                answer += f"- {change['year']}학번부터: {change['code']} {change['name']} ({change['type']})\n"
            answer += "\n"
        
        if not old_to_new and not future_changes:
            answer += "동일대체 정보가 없어요. 과목명이 변경된 적이 없는 것 같아요! ✅"
        
        return {
            "message": answer,
            "query_type": "curriculum",
            "sources": [],
            "needs_profile": False
        }
        
    def _handle_recommendation_query(
        self,
        message: str,
        user_profile: UserProfile
    ) -> Dict[str, Any]:
        """과목 추천 질문 처리"""
        
        # 1. 분야 파악
        req_type = None
        
        if '전필' in message or '전공필수' in message:
            req_type = '전공필수'
        elif '전선' in message or '전공선택' in message:
            req_type = '전공선택'
        elif '교양' in message or '교필' in message:
            req_type = '공통교양'
        
        # 2. 분야 명시 안 됨 → 재질문
        if not req_type:
            return {
                "message": """어떤 분야의 과목을 추천해드릴까요? 😊

                1. **전공필수** - 꼭 들어야 하는 전공 과목
                2. **전공선택** - 선택할 수 있는 전공 과목
                3. **교양** - 교양 과목

                예: "전공필수 추천해줘" 또는 "교양 뭐 들으면 좋아?"
                """,
                "query_type": "curriculum",
                "sources": [],
                "needs_profile": True
            }
        
        # 3. 미이수 필수 과목 조회
        not_taken = curriculum_service.get_required_courses_not_taken(
            user_profile,
            course_area="전공" if "전공" in req_type else "교양",
            requirement_type=req_type
        )
        
        if not not_taken:
            return {
                "message": f"**{req_type}** 과목은 모두 이수하셨어요! 👏",
                "query_type": "curriculum",
                "sources": [],
                "needs_profile": False
            }
        
        # 4. 추천 생성
        formatted = curriculum_service.format_not_taken_courses(
            not_taken,
            title=f"추천 {req_type} 과목"
        )
        
        answer = f"**{user_profile.admission_year}학번 {req_type} 추천**이에요!\n\n{formatted}"
        answer += "\n\n💡 학년별 권장 학기를 참고해서 수강하시면 좋아요!"
        
        return {
            "message": answer,
            "query_type": "curriculum",
            "sources": [],
            "needs_profile": False
        }

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
            5. ⚠️ 마크다운 문법(**, ##, - 등)을 사용하지 마세요. 순수 텍스트로만 작성하세요

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
            4. 마크다운 문법(**, ##, - 등)을 사용하지 마세요. 순수 텍스트와 이모지만 사용하세요
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