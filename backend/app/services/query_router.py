"""
사용자 질문을 분류하는 라우터
"""
import re
from typing import Literal


class QueryRouter:
    """질문 유형 분류"""
    
    # 교육과정 관련 키워드
    CURRICULUM_KEYWORDS = [
        '학점', '과목', '수강', '졸업', '이수', 
        '전공필수', '전공선택', '교양', '남은', '들었',
        '커리큘럼', '교육과정', '필수과목', '선택과목'
    ]
    
    # 일반 정보 키워드 (벡터 검색)
    GENERAL_KEYWORDS = [
        '도서관', '연락처', '전화', '위치', '실험실', 
        '교수', '운영시간', '학사일정', '개강', '종강',
        '중간고사', '기말고사', '시험', '방학'
    ]
    
    def classify(self, query: str) -> Literal["curriculum", "general", "hybrid"]:
        """
        질문 분류
        - curriculum: 교육과정 관련 (개인 정보 필요)
        - general: 일반 정보
        - hybrid: 복합 질문
        """
        query_lower = query.lower()
        
        has_curriculum = any(kw in query_lower for kw in self.CURRICULUM_KEYWORDS)
        has_general = any(kw in query_lower for kw in self.GENERAL_KEYWORDS)
        
        if has_curriculum and has_general:
            return "hybrid"
        elif has_curriculum:
            return "curriculum"
        else:
            return "general"
    
    def needs_user_profile(self, query: str) -> bool:
        """사용자 프로필이 필요한 질문인지 확인"""
        personal_indicators = [
            '나', '내가', '저', '제가', '우리',
            '남은', '들었', '이수했', '수강했'
        ]
        return any(indicator in query for indicator in personal_indicators)


# 전역 라우터
query_router = QueryRouter()