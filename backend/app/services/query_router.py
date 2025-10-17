"""
사용자 질문을 분류하는 라우터
"""
import re
from typing import Literal


class QueryRouter:
    """질문 유형 분류"""
    
    # 교육과정 관련 키워드
    CURRICULUM_KEYWORDS = [
        '남은', '들었', '이수했', '수강했',
        '전공필수', '전공선택', '교양필수', '교양선택',
        '졸업', '학점 계산', '커리큘럼',
        '나는', '내가', '저는', '제가', '우리',
        '전필', '전선', '교필', '교선',
        '몇 학점', '학점 남', '들어야', '필요',
        '이수', '수강', '들으면',
        '추천', '뭐 들', '어떤 과목',
        '대신', '동일대체', '대체', '바뀐', '과목명',
        'CS', 'XG', 'CE', 'EE',
        '학번',
    ]
    
    # 일반 정보 키워드 (벡터 검색)
    GENERAL_KEYWORDS = [
        '도서관', '책', '대출', '반납', '빌려', '빌릴',
        '열람실', '자료관', '미디어라운지',
        '연락처', '전화', '위치', '실험실', '문의',
        '교수', '운영시간', 
        '개강', '종강', '중간고사', '기말고사',  
        '학사일정', '시험', '방학', '일정',
        '장학금', '버스', '통학',
        '끝나', '시작',
        '졸업생', '휴학생', '지역주민'
    ]
    
    def _has_course_info(self, query: str) -> bool:
        """과목 정보가 있는지 체크"""
        
        # 1. 과목 코드 패턴 (CS0614, XG0800 등)
        if re.search(r'\b[A-Z]{2}\d{4}\b', query.upper()):
            return True
        
        # 2. 이미 들은 과목 언급 (과거형만)
        taken_keywords = ['들었', '이수했', '수강했', '완료했', '들은', '이수한']
        if any(kw in query for kw in taken_keywords):
            return True
        
        return False
    
    def classify(self, query: str) -> Literal["curriculum", "general", "hybrid"]:
        """
        질문 분류
        - curriculum: 교육과정 관련 (개인 정보 필요)
        - general: 일반 정보
        - hybrid: 복합 질문
        """
        query_lower = query.lower()
        
        # 1. 과목 코드 패턴 체크 (최우선)
        if re.search(r'\b[A-Z]{2}\d{4}\b', query.upper()):
            return "curriculum"
        
        # 2. 도서관 관련
        library_keywords = ['도서관', '책', '대출', '반납', '빌려', '빌릴', '열람실', '자료관']
        if any(kw in query_lower for kw in library_keywords):
            has_personal = any(word in query for word in ['나는', '내가', '저는', '제가', '나', '내'])
            if not has_personal:
                return "general"
        
        # 3. 학사일정 키워드
        schedule_keywords = ['개강', '종강', '중간고사', '기말고사', '시험', '방학', '끝나', '시작']
        if any(kw in query_lower for kw in schedule_keywords):
            has_personal = any(word in query for word in ['나는', '내가', '저는', '제가', '나', '내'])
            if not has_personal:
                return "general"
        
        # 4. 이용 자격 질문
        eligibility_keywords = ['졸업생', '휴학생', '지역주민', '외부인']
        if any(kw in query for kw in eligibility_keywords):
            return "general"
        
        # 5. 연락처/문의
        contact_keywords = ['연락처', '전화', '문의', '어디', '몇 번', '번호']
        if any(kw in query for kw in contact_keywords):
            has_personal = any(word in query for word in ['나는', '내가', '저는', '제가', '나', '내', '우리'])
            if not has_personal:
                return "general"
            
        # 6. 개인 졸업사정 요청 (과목 정보 없어도 curriculum으로)    
        personal_assessment_keywords = [
        '졸업사정', '졸업 가능', '졸업할 수 있', '졸업 확인',
        '내 졸업', '나 졸업', '내가 졸업',
        '내 상황', '내 현황', '나 현황',
        '개인 맞춤', '맞춤형',
        '계산해줘', '확인해줘', '분석해줘', '알려줘'  # + 졸업/학점 맥락
        ]
        
        has_assessment_request = any(kw in query for kw in personal_assessment_keywords)
        
        # "계산해줘", "확인해줘" 같은 건 졸업/학점 맥락이 있어야 함
        action_keywords = ['계산해줘', '확인해줘', '분석해줘', '알려줘', '보여줘']
        if any(kw in query for kw in action_keywords):
            context_keywords = ['졸업', '학점', '남은', '이수', '요건', '현황', '진행']
            if any(ctx in query for ctx in context_keywords):
                has_assessment_request = True
        
        if has_assessment_request:
            print("  → 개인 졸업사정 요청: curriculum")
            return "curriculum"
        
        # ===== 7. 졸업/학번 관련 구분 (기존 로직) =====
        has_graduation = '졸업' in query or '학번' in query
        has_requirement_keywords = any(kw in query for kw in [
            '학점', '요건', '조건', '필수', '선택', '몇', '얼마'
        ])
        
        if has_graduation or has_requirement_keywords:
            # 과목 정보가 있는지 체크
            if self._has_course_info(query):
                # 과목 정보 있음 → 개인 졸업사정
                print("  → 과목 정보 있음: curriculum (개인 졸업사정)")
                return "curriculum"
            else:
                # 과목 정보 없음 → 일반 졸업요건 (벡터 DB)
                print("  → 과목 정보 없음: general (일반 졸업요건)")
                return "general"
        
        # 8. 교육과정 강력 키워드 (확실한 curriculum)
        curriculum_strong = [
            # 개인화 키워드
            '남은', '남았', '남아',
            
            # 동일대체
            '대신', '대체', '동일대체', '바뀐', '변경',
            
            # 추천
            '추천', '뭐 들', '어떤 과목',
            
            # 진행 상황
            '진행', '현황', '상태', '완료'
        ]
        
        
        if any(kw in query for kw in curriculum_strong):
            return "curriculum"
        
         # 9. 기존 키워드 기반 분류
        has_personal = any(word in query for word in ['나는', '내가', '저는', '제가', '우리'])
        has_curriculum = any(kw in query_lower for kw in self.CURRICULUM_KEYWORDS)
        has_general = any(kw in query_lower for kw in self.GENERAL_KEYWORDS)
        
        if has_personal and has_curriculum:
            return "curriculum"
        
        if has_general:
            return "general"
        
        if has_curriculum and has_general:
            return "hybrid"
        elif has_curriculum:
            return "curriculum"
        else:
            return "general"
    
    def needs_user_profile(self, query: str) -> bool:
        """사용자 프로필이 필요한 질문인지 확인"""
        personal_indicators = [
            '나는', '내가', '저는', '제가', '우리',
            '남은', '들었', '이수했', '수강했'
        ]
        return any(indicator in query for indicator in personal_indicators)


# 전역 라우터
query_router = QueryRouter()