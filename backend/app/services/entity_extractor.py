"""
사용자 메시지에서 정보 추출
"""
import re
from typing import List, Optional, Dict, Any
from app.database.supabase_client import supabase
from app.models.schemas import CourseInput


class EntityExtractor:
    """메시지에서 정보 추출"""
    
    def extract_admission_year(self, message: str) -> Optional[int]:
        """입학년도 추출"""
        # "2024학번", "24학번", "2024년도", "24년", "2024입학"
        patterns = [
            r'(\d{4})\s*학번',           # 2024학번
            r'(\d{2})\s*학번',            # 24학번
            r'(\d{4})\s*년\s*입학',       # 2024년 입학
            r'(\d{4})\s*년\s*입학생',     # 2024년 입학생
            r'(\d{4})\s*입학',            # 2024 입학
            r'(\d{4})\s*입학생',          # 2024 입학생
            r'(\d{4})\s*년도\s*입학',     # 2024년도 입학
            r'(\d{4})\s*년',              # 2024년 (마지막 우선순위)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                year = int(match.group(1))
                # 2자리면 20XX로 변환
                if year < 100:
                    year = 2000 + year
                # 유효성 체크 (2020~2030)
                if 2020 <= year <= 2030:
                    return year
        
        return None
    
    def extract_course_codes(self, message: str) -> List[str]:
        """과목 코드 추출 (CS0614, XG0800 등)"""
        pattern = r'\b[A-Za-z]{2}\d{4}\b'
        codes = re.findall(pattern, message, re.IGNORECASE)
        return [code.upper() for code in set(codes)]
    
    def extract_course_names(self, message: str) -> List[str]:
        """
        과목명 추출
        
        예시:
        "컴퓨터과학과 창업과진로, 명저읽기 들었어"
        → ["컴퓨터과학", "창업과진로", "명저읽기"]
        """
        
        # ===== 1. 전처리: 학번 정보 제거 =====
        message = re.sub(r'(나는|저는|내가|제가)\s*\d{2,4}\s*학번\s*(이고|인데|이며)', '', message)
        message = re.sub(r'\d{2,4}\s*학번\s*(이고|인데|이며)', '', message)
        
        # ===== 2. 전처리: 과목 리스트 시작 문구 제거 =====
        message = re.sub(r'(내가|제가|나는|저는)?\s*(들은|수강한|이수한)\s*(과목은|수업은|과목들은)', '', message)
        message = re.sub(r'(과목은|수업은)', '', message)
        
        # ===== 3. 전처리: 뒤 불용어 제거 =====
        message = re.sub(r'(수업|과목)?\s*(들었어|이수했어|수강했어|들었습니다|이수했습니다)[\.?!]*', '', message)
        message = re.sub(r'[\.?!]+', '', message)
        message = re.sub(r'(졸업사정|졸업)\s*(해줘|부탁해|알려줘)', '', message)
        
        # 불용어
        stopwords = [
            '들었', '수강했', '이수했', '들', '어', '고', '이랑', '과',
            '하고', '그리고', '학번', '인데', '알려줘', '남은', '학점',
            '졸업', '요건', '뭐', '무엇', '수업', '과목', '나는', '저는',
            '내가', '제가'
        ]
        
        # ===== 4. 쉼표로 분리 =====
        words = re.split(r'[,\n]+', message)
        
        course_names = []
        seen = set()  # 중복 제거용
        
        # ===== 5. 각 단어 처리 =====
        for word in words:
            word = word.strip()
            
            sub_words = []
            
            # "컴퓨터과학과 창업과진로" → ["컴퓨터과학", "창업과진로"]
            if re.search(r'[가-힣]+과\s+[가-힣]+', word):
                sub_words = re.split(r'과\s+', word)
            else:
                sub_words = [word]
            
            for sub_word in sub_words:
                sub_word = sub_word.strip()
            
                # 조사 제거 (끝에만)
                sub_word = re.sub(r'(이랑|과|와|랑|을|를|이|가)\s*$', '', sub_word)
                sub_word = sub_word.strip()
                
                # 뒤에 붙은 불용어 제거
                for stop in stopwords:
                    if sub_word.endswith(stop):
                        sub_word = sub_word[:-len(stop)].strip()
                
                # 앞에 붙은 불용어 제거
                for stop in ['나는', '저는', '내가', '제가', '들은', '수강한', '이수한']:
                    if sub_word.startswith(stop):
                        sub_word = sub_word[len(stop):].strip()
                
                # 최소 길이 + 한글 포함 + 불용어 아님
                if len(sub_word) >= 3 and sub_word not in stopwords:
                    if re.search(r'[가-힣]', sub_word):
                        # 중복 체크
                        normalized = sub_word.replace(' ', '').lower()
                        if normalized not in seen:
                            seen.add(normalized)
                            course_names.append(sub_word)
    
        return course_names
    
    def search_course_by_name(
        self,
        course_name: str,
        admission_year: int
    ) -> Optional[Dict]:
        """
        과목명으로 검색 (DB 띄어쓰기 이미 제거됨)
        """
        try:
            # 정규화: 띄어쓰기 제거 + 소문자
            def normalize(text: str) -> str:
                return text.replace(' ', '').lower()
            
            course_name_normalized = normalize(course_name)
            
            if len(course_name_normalized) < 2:
                return None
            
            # === 1단계: 정확한 이름 매칭 (DB도 띄어쓰기 없음) ===
            result = supabase.table('curriculums')\
                .select('*')\
                .eq('admission_year', admission_year)\
                .eq('course_name', course_name_normalized)\
                .limit(1)\
                .execute()
            
            if result.data:
                return result.data[0]
            
            # === 2단계: LIKE 검색 (대소문자 무시) ===
            result = supabase.table('curriculums')\
                .select('*')\
                .eq('admission_year', admission_year)\
                .ilike('course_name', course_name_normalized)\
                .limit(1)\
                .execute()
            
            if result.data:
                return result.data[0]
            
            # === 3단계: 부분 매칭 (유연하게) ===
            result = supabase.table('curriculums')\
                .select('*')\
                .eq('admission_year', admission_year)\
                .ilike('course_name', f'%{course_name_normalized}%')\
                .limit(10)\
                .execute()
            
            if not result.data:
                return None
            
            # 가장 유사한 것 찾기
            best_match = None
            best_score = 0
            
            for row in result.data:
                db_name_normalized = normalize(row['course_name'])
                
                # 완전 일치
                if course_name_normalized == db_name_normalized:
                    return row
                
                # 부분 일치
                if course_name_normalized in db_name_normalized:
                    score = len(course_name_normalized) / len(db_name_normalized)
                    if score > best_score:
                        best_score = score
                        best_match = row
            
            # 유사도 60% 이상
            if best_match and best_score >= 0.6:
                return best_match
            
            return None
        
        except Exception as e:
            print(f"❌ 과목명 검색 실패 {course_name}: {e}")
            return None
    
    def get_course_details(
        self, 
        course_codes: List[str], 
        admission_year: int
    ) -> List[CourseInput]:
        """과목 코드 → 상세 정보 조회"""
        courses = []
        
        for code in course_codes:
            try:
                result = supabase.table('curriculums')\
                    .select('*')\
                    .eq('admission_year', admission_year)\
                    .eq('course_code', code)\
                    .limit(1)\
                    .execute()
                
                if result.data:
                    data = result.data[0]
                    courses.append(CourseInput(
                        course_code=data['course_code'],
                        course_name=data['course_name'],
                        credit=data['credit'],
                        course_area=data['course_area'],
                        requirement_type=data.get('requirement_type')
                    ))
                else:
                    print(f"⚠️ 과목을 찾을 수 없음: {code}")
            
            except Exception as e:
                print(f"❌ 과목 조회 실패 {code}: {e}")
        
        return courses
    
    def extract_course_info(
        self, 
        message: str
    ) -> Dict[str, Any]:
        """메시지에서 모든 정보 추출"""
        
        admission_year = self.extract_admission_year(message)
        
        if not admission_year:
            return {
                "admission_year": None,
                "course_codes": [],
                "courses": [],
                "has_enough_info": False
            }
            
        course_codes = self.extract_course_codes(message)
        course_names = self.extract_course_names(message)
        
        courses = []
        found_codes = set()
        
        # 1. 과목 코드로 조회
        if course_codes:
            courses.extend(self.get_course_details(course_codes, admission_year))
            found_codes.update(course_codes)
        
        # 2. 과목명으로 검색
        if course_names:
            for name in course_names:
                # 이미 찾은 과목은 스킵
                match = self.search_course_by_name(name, admission_year)
                
                if match and match['course_code'] not in found_codes:
                    courses.append(CourseInput(
                        course_code=match['course_code'],
                        course_name=match['course_name'],
                        credit=match['credit'],
                        course_area=match['course_area'],
                        requirement_type=match.get('requirement_type')
                    ))
                    found_codes.add(match['course_code'])
                    print(f"  ✅ '{name}' → {match['course_code']} {match['course_name']}")
                else:
                    print(f"  ⚠️ '{name}' 매칭 실패")
        
        return {
            "admission_year": admission_year,
            "course_codes": list(found_codes),
            "courses": courses,
            "has_enough_info": admission_year is not None and len(courses) > 0
        }
        
# 전역 인스턴스
entity_extractor = EntityExtractor()