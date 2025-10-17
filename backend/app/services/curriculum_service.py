"""
교육과정 계산 서비스
"""
from typing import Dict, List, Any, Optional
from app.database.supabase_client import supabase
from app.models.schemas import UserProfile
from app.services.equivalent_course_service import equivalent_course_service
from app.rules.graduation_rules import get_rules, get_overflow_target_key


class CurriculumService:
    """교육과정 계산 서비스"""
    
    # 총 졸업 학점 (기본값)
    TOTAL_GRADUATION_CREDITS = 140
    
    def get_graduation_requirements(
        self, 
        admission_year: int
    ) -> List[Dict[str, Any]]:
        """
        졸업요건 전체 조회
        """
        try:
            result = supabase.table('graduation_requirements')\
                .select('*')\
                .eq('admission_year', admission_year)\
                .execute()
            
            if not result.data:
                print(f"⚠️ {admission_year}학번 졸업요건을 찾을 수 없습니다.")
            
            return result.data if result.data else []
        except Exception as e:
            print(f"❌ 졸업요건 조회 실패: {e}")
            return []
    
    def get_total_graduation_credits(self, admission_year: int) -> int:
        """총 졸업 학점 조회"""
        try:
            result = supabase.table('graduation_requirements')\
                .select('required_credits')\
                .eq('admission_year', admission_year)\
                .eq('course_area', '전체')\
                .eq('requirement_type', '총졸업학점')\
                .single()\
                .execute()
            
            if result.data:
                return result.data['required_credits']
        except:
            pass
        
        # 설정에서 가져오기
        rules = get_rules(admission_year)
        return rules.get('total_credits', self.TOTAL_GRADUATION_CREDITS)
    
    def get_curriculum(
        self,
        admission_year: int,
        course_area: Optional[str] = None,
        requirement_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        교육과정 조회
        """
        try:
            query = supabase.table('curriculums')\
                .select('*')\
                .eq('admission_year', admission_year)
            
            if course_area:
                query = query.eq('course_area', course_area)
            
            if requirement_type:
                query = query.eq('requirement_type', requirement_type)
            
            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"❌ 교육과정 조회 실패: {e}")
            return []
    
    def get_selectable_courses(
        self,
        admission_year: int,
        course_area: str,
        requirement_type: str
    ) -> List[str]:
        """
        선택 가능한 과목 코드 목록 (동적 조회)
        """
        try:
            #추가선택인 경우 특별 처리
            if requirement_type == '추가선택':
                codes = []
                
                # 브릿지 과목 (기초교양/브릿지)
                bridge_result = supabase.table('curriculums')\
                    .select('course_code')\
                    .eq('admission_year', admission_year)\
                    .eq('course_area', '교양')\
                    .eq('requirement_type', '기초교양')\
                    .eq('track', '브릿지')\
                    .execute()
                
                if bridge_result.data:
                    codes.extend([row['course_code'] for row in bridge_result.data if row['course_code']])
                
                # 자유선택 과목 (창의교양/자유선택*)
                free_result = supabase.table('curriculums')\
                    .select('course_code')\
                    .eq('admission_year', admission_year)\
                    .eq('course_area', '교양')\
                    .eq('requirement_type', '창의교양')\
                    .like('track', '자유선택%')\
                    .execute()
                
                if free_result.data:
                    codes.extend([row['course_code'] for row in free_result.data if row['course_code']])
                
                # 중복 제거
                return list(set(codes))
            
            #기존 로직 (일반 경우)
            result = supabase.table('curriculums')\
                .select('course_code')\
                .eq('admission_year', admission_year)\
                .eq('course_area', course_area)\
                .eq('requirement_type', requirement_type)\
                .execute()
            
            if result.data:
                # 중복 제거
                codes = list(set([row['course_code'] for row in result.data if row['course_code']]))
                return codes
            return []
        except Exception as e:
            print(f"❌ 선택 가능 과목 조회 실패: {e}")
            return []
    
    def calculate_remaining_credits(
        self, 
        user_profile: UserProfile
    ) -> Dict[str, Any]:
        """
        남은 학점 계산 (overflow 처리 포함)
        """
        admission_year = user_profile.admission_year
        courses_taken = user_profile.courses_taken
        
        # 1. 졸업요건 조회
        requirements = self.get_graduation_requirements(admission_year)
        requirements = [r for r in requirements if r.get('course_area') != '전체']
        
        if not requirements:
            return {
                "error": f"{admission_year}학번의 졸업요건을 찾을 수 없습니다.",
                "message": "학번을 확인해주세요."
            }
        
        total_graduation_credits = self.get_total_graduation_credits(admission_year)
        
        # 2. 요건 구조화
        major_requirements = {}
        liberal_arts_requirements = {}
        
        for req in requirements:
            course_area = req['course_area']
            req_type = req['requirement_type']
            track = req.get('track')
            
            requirement_info = {
                'required': req['required_credits'],
                'min_credits': req.get('min_credits', req['required_credits']),
                'max_credits': req.get('max_credits', req['required_credits']),
                'taken': 0,
                'remaining': req['required_credits'],
                'required_all': req.get('required_all', []),
                'required_one_of': req.get('required_one_of', []),
                'selectable_codes': req.get('selectable_course_codes', []),
                'taken_courses': [],
            }
            
            # 동적 조회
            if not requirement_info['selectable_codes'] and not requirement_info['required_all']:
                if req_type in ['전공선택', '심화교양']:
                    dynamic_codes = self.get_selectable_courses(
                        admission_year, 
                        course_area, 
                        req_type
                    )
                    requirement_info['selectable_codes'] = dynamic_codes
            
            if course_area == '전공':
                major_requirements[req_type] = requirement_info
            elif course_area == '교양':
                key = track if track else req_type
                liberal_arts_requirements[key] = requirement_info
        
        # 3. 이수 학점 계산
        total_taken = 0
        major_taken = 0
        liberal_arts_taken = 0
        unmatched_courses = []
        
        for course in courses_taken:
            course_code = course.course_code
            course_name = course.course_name
            credit = course.credit
            course_area = course.course_area
            req_type = course.requirement_type
            
            total_taken += credit
            
            course_info = {
                'code': course_code,
                'name': course_name,
                'credit': credit,
                'grade': course.grade
            }
            
            # 전공 과목
            if course_area == '전공':
                major_taken += credit
                
                if req_type and req_type in major_requirements:
                    req_info = major_requirements[req_type]
                    is_matched = False
                    
                    for required_code in req_info['required_all']:
                        if equivalent_course_service.is_equivalent(course_code, required_code):
                            req_info['taken'] += credit
                            req_info['taken_courses'].append(course_info)
                            is_matched = True
                            break
                    
                    if not is_matched:
                        for selectable_code in req_info['selectable_codes']:
                            if equivalent_course_service.is_equivalent(course_code, selectable_code):
                                req_info['taken'] += credit
                                req_info['taken_courses'].append(course_info)
                                is_matched = True
                                break
                    
                    if not is_matched:
                        unmatched_courses.append(course_info)
                else:
                    unmatched_courses.append(course_info)
            
            # 교양 과목
            elif course_area == '교양':
                liberal_arts_taken += credit
                matched = False
                
                for track_name, track_info in liberal_arts_requirements.items():
                    selectable = track_info['selectable_codes']
                    required_all = track_info['required_all']
                    required_one_of = track_info['required_one_of']
                    
                    all_codes = required_all + required_one_of + selectable
                    for req_code in all_codes:
                        if equivalent_course_service.is_equivalent(course_code, req_code):
                            track_info['taken'] += credit
                            track_info['taken_courses'].append(course_info)
                            matched = True
                            break
                    
                    if matched:
                        break
                
                if not matched:
                    unmatched_courses.append(course_info)
        
        # 3.5. Overflow 처리 (설정 기반 통합)
        overflow_credits = self._handle_overflow(
            admission_year,
            liberal_arts_requirements,
            courses_taken
        )
        
        # 심화교양/창의교양에 overflow 추가
        overflow_key = get_overflow_target_key(admission_year)
        if overflow_key in liberal_arts_requirements:
            liberal_arts_requirements[overflow_key]['taken'] += overflow_credits
            liberal_arts_requirements[overflow_key]['overflow'] = overflow_credits
        
        # 4. 남은 학점 계산
        for req_dict in [major_requirements, liberal_arts_requirements]:
            for key, info in req_dict.items():
                info['remaining'] = max(0, info['required'] - info['taken'])
        
        # 5. 교양/전공 필요 학점
        major_required = sum(info['required'] for info in major_requirements.values())
        liberal_arts_required = sum(info['required'] for info in liberal_arts_requirements.values())
        
        # 6. 일반선택 계산
        general_elective_taken = total_taken - major_taken - liberal_arts_taken
        remaining_to_graduate = max(0, total_graduation_credits - total_taken)

        # 일반선택으로 채울 수 있는 여유 공간
        general_elective_available = max(
            0,
            total_graduation_credits - major_required - liberal_arts_required
        )
        
        result = {
            "admission_year": admission_year,
            "total_required": total_graduation_credits,
            "total_taken": total_taken,
            "remaining": max(0, total_graduation_credits - total_taken),
            "progress_percent": round((total_taken / total_graduation_credits) * 100, 1),
            
            "major": {
                "total_required": major_required,
                "total_taken": major_taken,
                "remaining": max(0, major_required - major_taken),
                "details": major_requirements
            },
            
            "liberal_arts": {
                "total_required": liberal_arts_required,
                "total_taken": liberal_arts_taken,
                "remaining": max(0, liberal_arts_required - liberal_arts_taken),
                "details": liberal_arts_requirements
            },
            
            "general_elective": {
                "available": general_elective_available, 
                "taken": general_elective_taken,
                "remaining": remaining_to_graduate  
            }
        }
        
        if unmatched_courses:
            result["warnings"] = {
                "unmatched_courses": unmatched_courses,
                "message": f"일부 과목({len(unmatched_courses)}개)이 졸업 요건에 매칭되지 않았습니다."
            }
        
        return result


    # ===== Overflow 처리 (리팩토링 - 설정 기반) =====
    
    def _handle_overflow(
        self,
        admission_year: int,
        liberal_arts_requirements: Dict,
        courses_taken: List
    ) -> int:
        """
        학번별 overflow 처리 (통합)
        설정 기반으로 동작하여 학번 추가 시 코드 수정 불필요
        
        Returns:
            심화교양/창의교양으로 인정할 초과 학점
        """
        # 규칙 가져오기
        rules = get_rules(admission_year)
        overflow_rules = rules.get('overflow', {})
        
        if not overflow_rules:
            return 0  # overflow 규칙 없음
        
        total_overflow = 0
        
        # 각 overflow 규칙 적용
        for rule_name, rule_config in overflow_rules.items():
            rule_type = rule_config.get('type')
            
            if rule_type == 'course_selection':
                # 과목 선택 overflow (예: 사고와글쓰기/정량적사고 중 택1)
                overflow = self._check_course_selection_overflow(
                    rule_config,
                    courses_taken
                )
                total_overflow += overflow
                
                if overflow > 0:
                    print(f"  Overflow [{rule_name}]: +{overflow}학점")
            
            elif rule_type == 'track_based':
                # 트랙 기반 overflow (예: 핵심 8학점 초과)
                overflow = self._check_track_overflow(
                    rule_config,
                    liberal_arts_requirements
                )
                total_overflow += overflow
                
                if overflow > 0:
                    print(f"  Overflow [{rule_name}]: +{overflow}학점")
        
        if total_overflow > 0:
            print(f"  총 Overflow: {total_overflow}학점 → {get_overflow_target_key(admission_year)}")
        
        return total_overflow


    def _check_course_selection_overflow(
        self,
        rule: Dict,
        courses_taken: List
    ) -> int:
        """
        과목 선택 overflow 체크 (범용)
        
        예시:
        - 사고와글쓰기/정량적사고 중 1개만 필수인데 2개 들음
        - 글로벌 의사소통 1개만 필수인데 2개 들음
        
        Args:
            rule: overflow 규칙
                - codes: 해당 과목 코드 리스트
                - max_allowed: 최대 허용 과목 수
                - credit_per_course: 과목당 학점
            courses_taken: 이수한 과목 리스트
        
        Returns:
            overflow 학점
        """
        codes = rule.get('codes', [])
        max_allowed = rule.get('max_allowed', 1)
        credit_per_course = rule.get('credit_per_course', 2)
        
        taken_count = sum(
            1 for c in courses_taken 
            if c.course_code in codes
        )
        
        if taken_count > max_allowed:
            overflow_count = taken_count - max_allowed
            return overflow_count * credit_per_course
        
        return 0


    def _check_track_overflow(
        self,
        rule: Dict,
        liberal_arts_requirements: Dict
    ) -> int:
        """
        트랙 기반 overflow 체크 (범용)
        
        예시:
        - 핵심 8학점 필수인데 더 들으면 최대 6학점까지 overflow
        
        Args:
            rule: overflow 규칙
                - track_names: 해당 트랙 이름 리스트
                - base_required: 기본 필수 학점
                - max_overflow: 최대 overflow 학점
            liberal_arts_requirements: 교양 요건 dict
        
        Returns:
            overflow 학점
        """
        track_names = rule.get('track_names', [])
        base_required = rule.get('base_required', 0)
        max_overflow = rule.get('max_overflow', 0)
        
        total_taken = 0
        for track_name in track_names:
            if track_name in liberal_arts_requirements:
                total_taken += liberal_arts_requirements[track_name]['taken']
        
        if total_taken > base_required:
            overflow = min(total_taken - base_required, max_overflow)
            return overflow
        
        return 0
    
    
    # ===== 기타 메서드 (기존 유지) =====
    
    def get_courses_not_taken(
        self,
        user_profile: UserProfile,
        requirement_type: str = "전공필수"
    ) -> List[Dict[str, Any]]:
        """
        아직 안 들은 과목 목록
        """
        admission_year = user_profile.admission_year
        courses_taken = user_profile.courses_taken
        
        # 해당 영역의 모든 과목 조회
        all_courses = self.get_curriculum(
            admission_year=admission_year,
            requirement_type=requirement_type
        )
        
        # 이미 들은 과목 코드/이름 세트
        taken_codes = {
            course.course_code 
            for course in courses_taken 
            if course.course_code
        }
        taken_names = {course.course_name for course in courses_taken}
        
        # 안 들은 과목 필터링
        not_taken = []
        seen_codes = set()  # 중복 제거
        
        for course in all_courses:
            code = course['course_code']
            name = course['course_name']
            
            # 이미 들었거나 이미 추가한 과목은 제외
            if code in taken_codes or name in taken_names or code in seen_codes:
                continue
            
            seen_codes.add(code)
            not_taken.append({
                'course_code': code,
                'course_name': name,
                'credit': course['credit'],
                'grade': course['grade'],
                'semester': course['semester'],
                'is_required': course.get('is_required_to_graduate', False)
            })
        
        # 학년-학기 순으로 정렬
        not_taken.sort(key=lambda x: (x['grade'], x['semester']))
        
        return not_taken
    
    def format_curriculum_info(self, calculation: Dict[str, Any]) -> str:
        """계산 결과를 사용자 친화적으로 포맷팅"""
        
        if 'error' in calculation:
            return f"❌ {calculation['error']}\n\n💡 {calculation.get('message', '')}"
        
        lines = []
        admission_year = calculation['admission_year']
        
        # 헤더
        lines.append(f"📊 {admission_year}학번 졸업 요건 현황\n")
        
        # 전체 학점
        lines.append(f"🎓 전체")
        lines.append(f"  총 졸업 학점: {calculation['total_required']}학점")
        lines.append(f"  이수 완료: {calculation['total_taken']}학점")
        lines.append(f"  남은 학점: {calculation['remaining']}학점")
        lines.append(f"  진행률: {calculation['progress_percent']}%\n")
        
        # 전공
        major = calculation['major']
        lines.append(f"📚 전공 (필요: {major['total_required']}학점)")
        lines.append(f"  이수: {major['total_taken']}학점 / 남음: {major['remaining']}학점")
        
        for req_type, info in major['details'].items():
            status = "✅" if info['remaining'] == 0 else "⏳"
            lines.append(
                f"  {status} {req_type}: "
                f"{info['taken']}/{info['required']}학점"
            )
            
            if info['taken_courses'] and len(info['taken_courses']) <= 5:
                for c in info['taken_courses']:
                    lines.append(f"     - {c['name']} ({c['credit']}학점)")
        
        lines.append("")
        
        # 교양
        liberal = calculation['liberal_arts']
        lines.append(f"📖 교양 (필요: {liberal['total_required']}학점)")
        lines.append(f"  이수: {liberal['total_taken']}학점 / 남음: {liberal['remaining']}학점")
        
        for track, info in liberal['details'].items():
            status = "✅" if info['remaining'] == 0 else "⏳"
            
            # 최소/최대 학점 표시
            if info['min_credits'] != info['max_credits']:
                credit_range = f"{info['min_credits']}~{info['max_credits']}학점"
            else:
                credit_range = f"{info['required']}학점"
            
            overflow_text = ""
            if 'overflow' in info and info['overflow'] > 0:
                overflow_text = f" (overflow: +{info['overflow']}학점)"
            
            lines.append(
                f"  {status} {track}: "
                f"{info['taken']}/{credit_range}{overflow_text}"
            )
            
            if info['taken_courses'] and len(info['taken_courses']) <= 3:
                for c in info['taken_courses']:
                    lines.append(f"     - {c['name']} ({c['credit']}학점)")
        
        lines.append("")
        
        # 일반선택
        general = calculation['general_elective']
        lines.append("\n📝 일반선택 (선택사항)")
        lines.append(f"  이수: {general['taken']}학점")
        lines.append(f"  선택 가능: 최대 {general['available']}학점")

        if general['remaining'] > 0:
            lines.append(f"  💡 졸업까지 {general['remaining']}학점 더 필요 (교양/전공/일반선택 자유)")
        else:
            lines.append(f"  ✅ 졸업 학점 충족!")
            
        lines.append("\n" + "=" * 50)
        lines.append("📌 참고사항")
        
        # 학번별 특이사항
        rules = get_rules(admission_year)
        notes = rules.get('notes', {})
        
        if notes:
            lines.append("")
            for note_key, note_text in notes.items():
                lines.append(f"- {note_text}")
        
        # 경고
        if 'warnings' in calculation:
            lines.append(f"\n⚠️ {calculation['warnings']['message']}")
        
        return "\n".join(lines)
    
    def get_required_courses_not_taken(
        self, 
        user_profile: UserProfile,
        course_area: str = None,
        requirement_type: str = None
    ) -> List[Dict]:
        """
        미이수 필수 과목 목록
        """
        admission_year = user_profile.admission_year
        courses_taken = user_profile.courses_taken
        
        # 1. 이수한 과목 코드 수집 (동일대체 포함)
        taken_codes = set()
        for course in courses_taken:
            taken_codes.add(course.course_code)
            
            # 동일대체 교과목 확인 (구 코드 → 신 코드)
            equiv = equivalent_course_service.get_equivalent_course(course.course_code)
            if equiv:
                taken_codes.add(equiv['new_course_code'])
        
        # 2. 필수 과목 조회
        requirements = self.get_graduation_requirements(admission_year)
        
        not_taken = []
        
        for req in requirements:
            # 필터링
            if course_area and req.get('course_area') != course_area:
                continue
            if requirement_type and req.get('requirement_type') != requirement_type:
                continue
            
            required_all = req.get('required_all', [])
            
            for course_code in required_all:
                # 이미 이수했으면 제외
                if course_code in taken_codes:
                    continue
                
                # 과목 정보 조회
                course_info = self._get_course_info(admission_year, course_code)
                
                if course_info:
                    # 동일대체 교과목 정보 추가
                    course_info['alternative_codes'] = self._get_alternative_codes(
                        course_code,
                        admission_year  # 입학년도 이후 변경사항만
                    )
                    not_taken.append(course_info)
        
        # 3. 학기 순으로 정렬
        not_taken.sort(key=lambda x: (x.get('grade', 99), x.get('semester', 99)))
        
        return not_taken


    def _get_course_info(
        self, 
        admission_year: int, 
        course_code: str
    ) -> Dict:
        """
        특정 과목의 상세 정보 조회
        """
        try:
            result = supabase.table('curriculums')\
                .select('*')\
                .eq('admission_year', admission_year)\
                .eq('course_code', course_code)\
                .limit(1)\
                .execute()
            
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            print(f"❌ 과목 정보 조회 실패: {e}")
            return None


    def _get_alternative_codes(
        self, 
        course_code: str,
        admission_year: int = None 
    ) -> List[Dict]:
        """
        동일대체 교과목 목록 조회 (입학년도 이후만)
        """
        try:
            query = supabase.table('equivalent_courses')\
                .select('new_course_code, new_course_name, mapping_type, effective_year')\
                .eq('old_course_code', course_code)
            
            # 입학년도 이후만 필터링
            if admission_year:
                query = query.gt('effective_year', admission_year)
            
            result = query.execute()
            
            if result.data:
                seen = set()
                alternatives = []
                
                for row in result.data:
                    new_code = row['new_course_code']
                    
                    if new_code not in seen:
                        seen.add(new_code)
                        alternatives.append({
                            'code': new_code,
                            'name': row['new_course_name'],
                            'type': row['mapping_type'],
                            'year': row.get('effective_year')
                        })
                
                return alternatives
            return []
        except Exception as e:
            print(f"❌ 동일대체 교과목 조회 실패: {e}")
            return []
        
    def format_not_taken_courses(
        self,
        not_taken: List[Dict],
        title: str = "미이수 필수 과목"
    ) -> str:
        """
        미이수 과목 목록 포맷팅
        """
        if not not_taken:
            return f"✅ {title}: 모두 이수 완료!"
        
        lines = []
        lines.append(f"\n📌 {title} ({len(not_taken)}개)")
        lines.append("=" * 70)
        
        for i, course in enumerate(not_taken, 1):
            code = course.get('course_code', 'N/A')
            name = course.get('course_name', 'N/A')
            credit = course.get('credit', 0)
            grade = course.get('grade', '?')
            semester = course.get('semester', '?')
            
            lines.append(f"\n{i}. {code} {name} ({credit}학점)")
            lines.append(f"   권장: {grade}학년 {semester}학기")
            
            # 동일대체 교과목 정보
            alternatives = course.get('alternative_codes', [])
            if alternatives:
                lines.append(f"   💡 향후 과목명 변경:")
                for alt in alternatives:
                    alt_code = alt['code']
                    alt_name = alt['name']
                    alt_type = alt['type']
                    alt_year = alt.get('year', '?')
                    lines.append(f"      - {alt_year}학번부터: {alt_code} {alt_name} ({alt_type})")
        
        return "\n".join(lines)


# 전역 서비스
curriculum_service = CurriculumService()