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
        '나는', '내가', '저는', '제가', '우리'
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
    
    def classify(self, query: str) -> Literal["curriculum", "general", "hybrid"]:
        """
        질문 분류
        - curriculum: 교육과정 관련 (개인 정보 필요)
        - general: 일반 정보
        - hybrid: 복합 질문
        """
        query_lower = query.lower()
        
        # 1. 도서관 관련 최우선 체크
        library_keywords = ['도서관', '책', '대출', '반납', '빌려', '빌릴', '열람실', '자료관']
        if any(kw in query_lower for kw in library_keywords):
            # 개인 지시어 없으면 무조건 general
            has_personal = any(word in query for word in ['나는', '내가', '저는', '제가', '나', '내'])
            if not has_personal:
                return "general"
        
        # 2. 명확한 학사일정 키워드 체크
        schedule_keywords = ['개강', '종강', '중간고사', '기말고사', '시험', '방학', '끝나', '시작']
        if any(kw in query_lower for kw in schedule_keywords):
            has_personal = any(word in query for word in ['나는', '내가', '저는', '제가', '나', '내'])
            if not has_personal:
                return "general"
        
        # 3. 이용 자격 질문 (졸업생, 휴학생 등)
        eligibility_keywords = ['졸업생', '휴학생', '지역주민', '외부인']
        if any(kw in query for kw in eligibility_keywords):
            return "general"
        
        # 4. 연락처/문의 최우선 체크 (새로 추가!)
        contact_keywords = ['연락처', '전화', '문의', '어디', '몇 번', '번호']
        if any(kw in query for kw in contact_keywords):
            has_personal = any(word in query for word in ['나는', '내가', '저는', '제가', '나', '내', '우리'])
            if not has_personal:
                return "general"
            
        # 5. 졸업 관련 구분
        if '졸업' in query:
            # "졸업 문의", "졸업 신청 어디", "졸업 연락처" → general
            if any(kw in query for kw in ['문의', '어디', '연락처', '전화', '신청 어디', '어떻게']):
                return "general"
            # "졸업 학점", "졸업 요건", "졸업까지" → curriculum (개인정보 필요)
            elif any(kw in query for kw in ['학점', '요건', '남았', '까지', '조건']):
                return "curriculum"
        
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