"""
사용자 질문을 분류하는 라우터
"""
import re
from typing import Literal


class QueryRouter:
    """질문 유형 분류"""
    
    # 1. general 키워드(백터db 관련)
    STRONG_GENERAL_KEYWORDS = [
        # 학사 일정
        '개강', '종강', '중간고사', '기말고사', '시험', '방학', '일정',
        '언제', '기간', '날짜',
        
        # 도서관
        '도서관', '책', '대출', '반납', '빌려', '빌릴', '열람실', '자료관',
        
        # 연락처/위치
        '연락처', '전화', '번호', '위치', '어디', '몇 번',
        '사무실', '교수', '실험실', '문의',
        
        # 기타 학교 정보
        '운영시간', '시간표', '통학', '버스', '장학금',
        '졸업생', '휴학생', '지역주민', '외부인'
    ]
    
    # 2. 교육과정 관련 키워드
    CURRICULUM_KEYWORDS = [
        # 과목 정보
        '들었', '이수했', '수강했', '완료했',
        
        # 요건
        '전공필수', '전공선택', '교양필수', '교양선택',
        '전필', '전선', '교필', '교선',
        
        # 졸업사정
        '졸업사정', '남은', '남았', '진행', '현황', '상태',
        
        # 동일대체
        '대신', '대체', '동일대체', '바뀐', '변경',
        
        # 학번
        '학번'
    ]
    
    
    def _has_course_info(self, query: str) -> bool:
        """과목 정보가 있는지 체크"""
        
        # 1. 과목 코드 패턴 (CS0614, XG0800 등)
        if re.search(r'\b[A-Z]{2}\d{4}\b', query.upper()):
            return True
        
        # 2. 이미 들은 과목 언급 (과거형만)
        taken_keywords = ['들었', '이수했', '수강했', '완료했', '들은', '이수한']
        has_taken_keyword = any(kw in query for kw in taken_keywords)
        
        if has_taken_keyword and ',' in query:
            return True
        
        if has_taken_keyword and any(kw in query for kw in ['과목은', '과목:', '수업은']):
            return True
        
        return False
    
    def classify(self, query: str) -> Literal["curriculum", "general"]:
        """
        질문 분류 - 관계형 db를 사용하는 3가지 케이스
        1. 개인 맞춤 졸업사정
        2. 교육과정 조회 (과목 리스트)
        3. 동일대체 과목 조회
        """
        query_lower = query.lower()
        
        # ===== 1. 강력한 general 키워드 =====
        if any(kw in query_lower for kw in self.STRONG_GENERAL_KEYWORDS):
            print("  → 강력한 general 키워드: general (벡터 DB)")
            return "general"
        
        # ===== 2. 동일대체 질문 =====
        equivalent_keywords = ['대신', '대체', '동일대체', '바뀐', '변경']
        if any(kw in query for kw in equivalent_keywords):
            print("  → 동일대체 질문: curriculum")
            return "curriculum"
        
        # ===== 3. 과목 코드 또는 과목 정보 있음 → 개인 졸업사정 =====
        if self._has_course_info(query):
            print("  → 과목 정보 있음: curriculum (개인 졸업사정)")
            return "curriculum"
        
        # ===== 4. 교육과정 조회 (학번 + 요건 키워드) =====
        has_admission_year = '학번' in query or re.search(r'\b20\d{2}\b', query)
        requirement_keywords = [
            '전공필수', '전공선택', '교양필수', '교양선택',
            '전필', '전선', '교필', '교선', '교양', '전공'
        ]
        has_requirement = any(kw in query for kw in requirement_keywords)
        
        if has_admission_year and has_requirement:
            print("  → 교육과정 조회: curriculum")
            return "curriculum"
        
        # ===== 5. 졸업사정 요청 키워드 =====
        assessment_keywords = [
            '졸업사정', '남은 학점', '남은 과목', '졸업 가능',
            '이수 현황', '진행 현황', '졸업 확인'
        ]
        if any(kw in query for kw in assessment_keywords):
            print("  → 졸업사정 요청: curriculum")
            return "curriculum"
        
        # ===== 6. 졸업 요건 설명 (과목 정보 없음) =====
        if '졸업' in query:
            # 설명 요청 키워드
            explanation_keywords = ['뭐야', '어떻게', '설명', '구조', '알려줘']
            if any(kw in query for kw in explanation_keywords):
                print("  → 졸업 요건 설명: general (벡터 DB)")
                return "general"
            
            # 명확하지 않으면 general (안전하게)
            print("  → 졸업 관련 (명확하지 않음): general")
            return "general"
        
        # ===== 7. 기본값 =====
        # curriculum 키워드가 있으면 curriculum
        if any(kw in query_lower for kw in self.CURRICULUM_KEYWORDS):
            print("  → curriculum 키워드: curriculum")
            return "curriculum"
        
        # 나머지는 모두 general
        print("  → 기본값: general")
        return "general"
    
    def needs_user_profile(self, query: str) -> bool:
        """사용자 프로필이 필요한 질문인지 확인"""
        personal_indicators = [
            '나는', '내가', '저는', '제가',
            '남은', '들었', '이수했', '수강했'
        ]
        return any(indicator in query for indicator in personal_indicators)


# 전역 라우터
query_router = QueryRouter()