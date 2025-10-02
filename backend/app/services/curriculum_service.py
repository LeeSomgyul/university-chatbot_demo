# backend/app/services/curriculum_service.py
"""
교육과정 계산 서비스
"""
from typing import Dict, List, Any, Optional
from app.database.supabase_client import supabase
from app.models.schemas import UserProfile, CourseInput


class CurriculumService:
    """교육과정 계산 서비스"""
    
    def get_graduation_requirements(
        self, 
        admission_year: int,
        track: str = "일반"
    ) -> List[Dict[str, Any]]:
        """졸업요건 조회"""
        try:
            # track이 None이거나 빈 문자열이면 is null 조건 사용
            if track:
                result = supabase.table('graduation_requirements')\
                    .select('*')\
                    .eq('admission_year', admission_year)\
                    .eq('track', track)\
                    .execute()
            else:
                result = supabase.table('graduation_requirements')\
                    .select('*')\
                    .eq('admission_year', admission_year)\
                    .is_('track', 'null')\
                    .execute()
            
            return result.data if result.data else []
        except Exception as e:
            print(f"❌ 졸업요건 조회 실패: {e}")
            return []
    
    def calculate_remaining_credits(
        self, 
        user_profile: UserProfile
    ) -> Dict[str, Any]:
        """
        남은 학점 계산
        
        Returns:
            {
                "total_required": 130,
                "total_taken": 45,
                "remaining": 85,
                "by_area": {
                    "전공필수": {"required": 60, "taken": 15, "remaining": 45},
                    "전공선택": {"required": 30, "taken": 6, "remaining": 24},
                    ...
                }
            }
        """
        admission_year = user_profile.admission_year
        track = user_profile.track or "일반"
        courses_taken = user_profile.courses_taken
        
        # 졸업요건 조회
        requirements = self.get_graduation_requirements(admission_year, track)
        
        if not requirements:
            return {
                "error": f"{admission_year}학번 {track} 트랙의 졸업요건을 찾을 수 없습니다."
            }
        
        # 영역별 요구학점
        required_by_area = {}
        for req in requirements:
            area = req['course_area']
            required_by_area[area] = {
                'required': req['required_credits'],
                'taken': 0,
                'remaining': req['required_credits'],
                'requirement_type': req.get('requirement_type'),
                'notes': req.get('notes')
            }
        
        # 이수한 학점 계산
        total_taken = 0
        for course in courses_taken:
            area = course.course_area
            credit = course.credit
            total_taken += credit
            
            if area in required_by_area:
                required_by_area[area]['taken'] += credit
                required_by_area[area]['remaining'] = max(
                    0, 
                    required_by_area[area]['required'] - required_by_area[area]['taken']
                )
        
        # 전체 요구학점 계산
        total_required = sum(req['required_credits'] for req in requirements)
        
        return {
            "total_required": total_required,
            "total_taken": total_taken,
            "remaining": max(0, total_required - total_taken),
            "by_area": required_by_area
        }
    
    def get_courses_not_taken(
        self,
        user_profile: UserProfile,
        course_area: str = "전공필수"
    ) -> List[Dict[str, Any]]:
        """아직 안 들은 과목 목록"""
        admission_year = user_profile.admission_year
        courses_taken = user_profile.courses_taken
        
        # 해당 영역의 모든 과목 조회
        try:
            result = supabase.table('curriculums')\
                .select('*')\
                .eq('admission_year', admission_year)\
                .eq('course_area', course_area)\
                .execute()
            
            all_courses = result.data if result.data else []
        except Exception as e:
            print(f"❌ 과목 조회 실패: {e}")
            return []
        
        # 이미 들은 과목 코드 세트
        taken_codes = {course.course_code for course in courses_taken if course.course_code}
        taken_names = {course.course_name for course in courses_taken}
        
        # 안 들은 과목 필터링
        not_taken = []
        for course in all_courses:
            code = course['course_code']
            name = course['course_name']
            
            if code not in taken_codes and name not in taken_names:
                not_taken.append(course)
        
        return not_taken
    
    def format_curriculum_info(self, calculation: Dict[str, Any]) -> str:
        """계산 결과를 텍스트로 포맷팅"""
        if 'error' in calculation:
            return calculation['error']
        
        lines = []
        lines.append(f"📊 졸업 요건 현황")
        lines.append(f"총 필요 학점: {calculation['total_required']}학점")
        lines.append(f"이수한 학점: {calculation['total_taken']}학점")
        lines.append(f"남은 학점: {calculation['remaining']}학점")
        lines.append("")
        lines.append("영역별 상세:")
        
        for area, info in calculation['by_area'].items():
            req_type = f"({info['requirement_type']})" if info.get('requirement_type') else ""
            lines.append(
                f"- {area}{req_type}: "
                f"필요 {info['required']}학점 / "
                f"이수 {info['taken']}학점 / "
                f"남음 {info['remaining']}학점"
            )
            if info.get('notes'):
                lines.append(f"  💡 {info['notes']}")
        
        return "\n".join(lines)


# 전역 서비스
curriculum_service = CurriculumService()