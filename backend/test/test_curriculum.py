"""
교육과정 정확도 테스트
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from app.services.curriculum_service import curriculum_service
from app.models.schemas import UserProfile, CourseInput


# ===== 샘플 데이터 =====

# 샘플 사용자 1: 1학년 (일부 이수)
SAMPLE_USER_1 = UserProfile(
    admission_year=2024,
    current_semester=2,
    courses_taken=[
        CourseInput(
            course_code="CS0614",
            course_name="컴퓨터과학",
            credit=3,
            grade="A+",
            course_area="전공",
            requirement_type="전공필수"
        ),
        CourseInput(
            course_code="XG0800",
            course_name="대학생활과목표설정",
            credit=1,
            course_area="교양",
            requirement_type="공통교양"
        ),
        CourseInput(
            course_code="XG0700",
            course_name="독서와표현",
            credit=2,
            course_area="교양",
            requirement_type="공통교양"
        ),
    ]
)

# 샘플 사용자 2: 3학년 (많이 이수)
SAMPLE_USER_2 = UserProfile(
    admission_year=2024,
    current_semester=2,
    courses_taken=[
        # 전공필수
        CourseInput(course_code="CS0614", course_name="컴퓨터과학", credit=3, course_area="전공", requirement_type="전공필수"),
        CourseInput(course_code="CS0623", course_name="이산수학", credit=3, course_area="전공", requirement_type="전공필수"),
        CourseInput(course_code="CS0603", course_name="자료구조", credit=3, course_area="전공", requirement_type="전공필수"),
        
        # 전공선택
        CourseInput(course_code="CS0855", course_name="고급컴퓨터프로그래밍", credit=3, course_area="전공", requirement_type="전공선택"),
        CourseInput(course_code="CS0860", course_name="어드벤쳐디자인", credit=3, course_area="전공", requirement_type="전공선택"),
        
        # 교양
        CourseInput(course_code="XG0800", course_name="대학생활과목표설정", credit=1, course_area="교양", requirement_type="공통교양"),
        CourseInput(course_code="XG0700", course_name="독서와표현", credit=2, course_area="교양", requirement_type="공통교양"),
        CourseInput(course_code="XG1004", course_name="데이터와 코딩", credit=2, course_area="교양", requirement_type="공통교양"),
        CourseInput(course_code="XG0701", course_name="사고와글쓰기", credit=2, course_area="교양", requirement_type="공통교양"),
        CourseInput(course_code="XG0703", course_name="문학과삶", credit=3, course_area="교양", requirement_type="공통교양"),
        CourseInput(course_code="XG0707", course_name="글로벌시민정치", credit=3, course_area="교양", requirement_type="공통교양"),
        CourseInput(course_code="XG0869", course_name="컴퓨터의개념및실습", credit=3, course_area="교양", requirement_type="공통교양"),
        CourseInput(course_code="XG0717", course_name="커뮤니케이션영어", credit=2, course_area="교양", requirement_type="공통교양"),
    ]
)

SAMPLE_USER_2025_1 = UserProfile(
    admission_year=2025,
    current_semester=2,
    courses_taken=[
        # 기초교양-필수 3과목
        CourseInput(
            course_code="XG1100",
            course_name="명저 읽기",
            credit=2,
            course_area="교양",
            requirement_type="기초교양"
        ),
        CourseInput(
            course_code="XG0701",
            course_name="사고와글쓰기",
            credit=2,
            course_area="교양",
            requirement_type="기초교양"
        ),
        CourseInput(
            course_code="XG1004",
            course_name="데이터와 코딩",
            credit=2,
            course_area="교양",
            requirement_type="기초교양"
        ),
        # 전공필수 1과목
        CourseInput(
            course_code="CS0614",
            course_name="컴퓨터과학",
            credit=3,
            course_area="전공",
            requirement_type="전공필수"
        ),
    ]
)

# 샘플 사용자 4: 2025학번 3학년 (많이 이수)
SAMPLE_USER_2025_2 = UserProfile(
    admission_year=2025,
    current_semester=2,
    courses_taken=[
        # 기초교양
        CourseInput(course_code="XG1100", course_name="명저 읽기", credit=2, course_area="교양", requirement_type="기초교양"),
        CourseInput(course_code="XG0701", course_name="사고와글쓰기", credit=2, course_area="교양", requirement_type="기초교양"),
        CourseInput(course_code="XG1004", course_name="데이터와 코딩", credit=2, course_area="교양", requirement_type="기초교양"),
        CourseInput(course_code="XG0717", course_name="커뮤니케이션영어", credit=2, course_area="교양", requirement_type="기초교양"),
        CourseInput(course_code="XG1139", course_name="디지털 추론과 문제해결", credit=2, course_area="교양", requirement_type="기초교양"),
        
        # 창의교양
        CourseInput(course_code="XG1138", course_name="대학생활", credit=1, course_area="교양", requirement_type="창의교양"),
        CourseInput(course_code="XG0801", course_name="흙에서배우는삶의지혜", credit=2, course_area="교양", requirement_type="창의교양"),
        CourseInput(course_code="XG1157", course_name="미래 설계 I", credit=2, course_area="교양", requirement_type="창의교양"),
        
        # 전공필수
        CourseInput(course_code="CS0614", course_name="컴퓨터과학", credit=3, course_area="전공", requirement_type="전공필수"),
        CourseInput(course_code="CS0623", course_name="이산수학", credit=3, course_area="전공", requirement_type="전공필수"),
        CourseInput(course_code="CS0603", course_name="자료구조", credit=3, course_area="전공", requirement_type="전공필수"),
        
        # 전공선택
        CourseInput(course_code="CS0855", course_name="고급컴퓨터프로그래밍", credit=3, course_area="전공", requirement_type="전공선택"),
        CourseInput(course_code="CS0860", course_name="어드벤쳐디자인", credit=3, course_area="전공", requirement_type="전공선택"),
    ]
)

SAMPLE_USER_OVERFLOW = UserProfile(
    admission_year=2024,
    current_semester=3,
    courses_taken=[
        # 기초교양 필수
        CourseInput(course_code="XG0800", course_name="대학생활과목표설정", credit=1, course_area="교양", requirement_type="공통교양"),
        CourseInput(course_code="XG0700", course_name="독서와표현", credit=2, course_area="교양", requirement_type="공통교양"),
        CourseInput(course_code="XG1004", course_name="데이터와코딩", credit=2, course_area="교양", requirement_type="공통교양"),
        
        # 기초 > 택1 둘 다 들음 (overflow 발생!)
        CourseInput(course_code="XG0701", course_name="사고와글쓰기", credit=2, course_area="교양", requirement_type="공통교양"),
        CourseInput(course_code="XG0702", course_name="정량적사고와컴퓨팅사고", credit=2, course_area="교양", requirement_type="공통교양"),
        
        # 글로벌의사소통 2과목 (overflow 발생!)
        CourseInput(course_code="XG0717", course_name="커뮤니케이션영어", credit=2, course_area="교양", requirement_type="공통교양"),
        CourseInput(course_code="XG0718", course_name="커뮤니케이션중국어", credit=2, course_area="교양", requirement_type="공통교양"),
        
        # 핵심교양 12학점 (8학점 초과 → overflow 발생!)
        CourseInput(course_code="XG0703", course_name="인문학과목1", credit=3, course_area="교양", requirement_type="공통교양"),
        CourseInput(course_code="XG0704", course_name="인문학과목2", credit=3, course_area="교양", requirement_type="공통교양"),
        CourseInput(course_code="XG0707", course_name="사회과학과목1", credit=3, course_area="교양", requirement_type="공통교양"),
        CourseInput(course_code="XG0708", course_name="사회과학과목2", credit=3, course_area="교양", requirement_type="공통교양"),
    ]
)


# ===== 테스트 케이스 =====

CURRICULUM_TESTS = [
    # 1. 졸업 요건 조회
    # {
    #     "id": 1,
    #     "name": "졸업 요건 조회",
    #     "test_func": lambda: curriculum_service.get_graduation_requirements(2024),
    #     "evaluation": lambda result: len(result) > 0,
    #     "expected": "졸업 요건 데이터 존재"
    # },
    
    # # 2. 남은 학점 계산 (샘플 1)
    # {
    #     "id": 2,
    #     "name": "남은 학점 계산 (1학년)",
    #     "test_func": lambda: curriculum_service.calculate_remaining_credits(SAMPLE_USER_1),
    #     "evaluation": lambda result: 'error' not in result and result['total_taken'] == 6,
    #     "expected": "총 6학점 이수"
    # },
    
    # # 3. 남은 학점 계산 (샘플 2)
    # {
    #     "id": 3,
    #     "name": "남은 학점 계산 (3학년)",
    #     "test_func": lambda: curriculum_service.calculate_remaining_credits(SAMPLE_USER_2),
    #     "evaluation": lambda result: 'error' not in result and result['total_taken'] == 33,
    #     "expected": "총 33학점 이수"
    # },
    
    # # 4. 미이수 전공필수 과목
    # {
    #     "id": 4,
    #     "name": "미이수 전공필수 과목",
    #     "test_func": lambda: curriculum_service.get_courses_not_taken(SAMPLE_USER_1, "전공필수"),
    #     "evaluation": lambda result: len(result) > 0,
    #     "expected": "미이수 전공필수 과목 존재"
    # },
    
    # # 5. 포맷팅 테스트
    # {
    #     "id": 5,
    #     "name": "결과 포맷팅",
    #     "test_func": lambda: curriculum_service.format_curriculum_info(
    #         curriculum_service.calculate_remaining_credits(SAMPLE_USER_1)
    #     ),
    #     "evaluation": lambda result: "졸업 요건 현황" in result and "전공" in result,
    #     "expected": "포맷팅된 문자열 반환"
    # },
    
    {
        "id": 6,
        "name": "2025학번 졸업사정 (1학년)",
        "test_func": lambda: curriculum_service.calculate_remaining_credits(SAMPLE_USER_2025_1),
        "evaluation": lambda result: (
            'error' not in result and 
            result['admission_year'] == 2025 and
            result['total_taken'] == 9
        ),
        "expected": "2025학번 9학점 이수"
    },
    
    {
        "id": 7,
        "name": "2025학번 졸업사정 (3학년)",
        "test_func": lambda: curriculum_service.calculate_remaining_credits(SAMPLE_USER_2025_2),
        "evaluation": lambda result: (
            'error' not in result and 
            result['admission_year'] == 2025 and
            result['total_taken'] >= 30
        ),
        "expected": "2025학번 30학점 이상 이수"
    },
    
    # {
    #     "id": 8,
    #     "name": "2024학번 Overflow 처리",
    #     "test_func": lambda: curriculum_service.calculate_remaining_credits(SAMPLE_USER_OVERFLOW),
    #     "evaluation": lambda result: (
    #         'error' not in result and 
    #         '심화교양' in result['liberal_arts']['details'] and
    #         result['liberal_arts']['details']['심화교양'].get('overflow', 0) > 0
    #     ),
    #     "expected": "초과 학점이 심화교양으로 인정됨"
    # },
]


def run_tests():
    """테스트 실행"""
    print("=" * 70)
    print("🎓 교육과정 서비스 테스트")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for test in CURRICULUM_TESTS:
        print(f"\n테스트 #{test['id']}: {test['name']}")
        print("-" * 70)
        
        try:
            result = test['test_func']()
            is_pass = test['evaluation'](result)
            
            if is_pass:
                print(f"✅ 통과: {test['expected']}")
                passed += 1
            else:
                print(f"❌ 실패: {test['expected']}")
                print(f"결과: {result}")
                failed += 1
                
        except Exception as e:
            print(f"❌ 에러: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"📊 테스트 결과: {passed}개 통과 / {failed}개 실패")
    print("=" * 70)
    
    return passed, failed


def test_sample_scenarios():
    """샘플 시나리오 테스트"""
    print("\n" + "=" * 70)
    print("📝 샘플 시나리오 테스트")
    print("=" * 70)
    
    # # ===== 2024학번 테스트 =====
    
    # print("\n" + "🎓 2024학번 테스트")
    # print("=" * 70)
    
    # # 시나리오 1: 2024학번 1학년
    # print("\n▶️ 시나리오 1: 2024학번 1학년 (6학점 이수)")
    # print("-" * 70)
    # result1 = curriculum_service.calculate_remaining_credits(SAMPLE_USER_1)
    # formatted1 = curriculum_service.format_curriculum_info(result1)
    # print(formatted1)
    
    # # 시나리오 2: 2024학번 3학년
    # print("\n▶️ 시나리오 2: 2024학번 3학년 (33학점 이수)")
    # print("-" * 70)
    # result2 = curriculum_service.calculate_remaining_credits(SAMPLE_USER_2)
    # formatted2 = curriculum_service.format_curriculum_info(result2)
    # print(formatted2)
    
    # # 시나리오 3: 2024학번 미이수 과목
    # print("\n▶️ 시나리오 3: 2024학번 미이수 전공필수 과목")
    # print("-" * 70)
    # not_taken1 = curriculum_service.get_courses_not_taken(SAMPLE_USER_1, "전공필수")
    # print(f"총 {len(not_taken1)}개 과목")
    # for i, course in enumerate(not_taken1[:5], 1):
    #     print(f"  {i}. {course['course_name']} ({course['course_code']}) - {course['credit']}학점 - {course['grade']}학년 {course['semester']}학기")
    # if len(not_taken1) > 5:
    #     print(f"  ... 외 {len(not_taken1) - 5}개")
    
    # # ===== 2025학번 테스트 =====
    
    # print("\n" + "🎓 2025학번 테스트")
    # print("=" * 70)
    
    # # 시나리오 4: 2025학번 1학년
    # print("\n▶️ 시나리오 4: 2025학번 1학년 (9학점 이수)")
    # print("-" * 70)
    # result3 = curriculum_service.calculate_remaining_credits(SAMPLE_USER_2025_1)
    # formatted3 = curriculum_service.format_curriculum_info(result3)
    # print(formatted3)
    
    # # 시나리오 5: 2025학번 3학년
    # print("\n▶️ 시나리오 5: 2025학번 3학년 (30+학점 이수)")
    # print("-" * 70)
    # result4 = curriculum_service.calculate_remaining_credits(SAMPLE_USER_2025_2)
    # formatted4 = curriculum_service.format_curriculum_info(result4)
    # print(formatted4)
    
    # # 시나리오 6: 2025학번 미이수 과목
    # print("\n▶️ 시나리오 6: 2025학번 미이수 전공필수 과목")
    # print("-" * 70)
    # not_taken2 = curriculum_service.get_courses_not_taken(SAMPLE_USER_2025_1, "전공필수")
    # print(f"총 {len(not_taken2)}개 과목")
    # for i, course in enumerate(not_taken2[:5], 1):
    #     print(f"  {i}. {course['course_name']} ({course['course_code']}) - {course['credit']}학점 - {course['grade']}학년 {course['semester']}학기")
    # if len(not_taken2) > 5:
    #     print(f"  ... 외 {len(not_taken2) - 5}개")

    # # ===== Overflow 테스트 =====
    
    # print("\n" + "🔄 Overflow 처리 테스트")
    # print("=" * 70)
    
    # print("\n▶️ 시나리오 7: 2024학번 초과 학점 처리")
    # print("-" * 70)
    # result_overflow = curriculum_service.calculate_remaining_credits(SAMPLE_USER_OVERFLOW)
    
    # if '심화교양' in result_overflow['liberal_arts']['details']:
    #     심화교양 = result_overflow['liberal_arts']['details']['심화교양']
    #     overflow = 심화교양.get('overflow', 0)
        
    #     print(f"✅ 심화교양 overflow: {overflow}학점")
    #     print(f"   - 기초 택1 둘 다: 2학점")
    #     print(f"   - 글로벌 2과목: 2학점")
    #     print(f"   - 핵심 초과(12-8): 4학점")
    #     print(f"   - 예상 총 overflow: 8학점")
    #     print(f"   - 실제 overflow: {overflow}학점")
    
    # formatted_overflow = curriculum_service.format_curriculum_info(result_overflow)
    # print(formatted_overflow)
    
    # ===== 미이수 과목 테스트 추가 =====

    print("\n" + "📌 미이수 필수 과목 테스트")
    print("=" * 70)

    # 2024학번 전공필수 미이수
    print("\n▶️ 2024학번: 미이수 전공필수")
    print("-" * 70)
    not_taken_major = curriculum_service.get_required_courses_not_taken(
        SAMPLE_USER_1,
        course_area="전공",
        requirement_type="전공필수"
    )
    formatted_major = curriculum_service.format_not_taken_courses(
        not_taken_major,
        title="미이수 전공필수"
    )
    print(formatted_major)

    # 2024학번 교양 미이수
    print("\n▶️ 2024학번: 미이수 교양필수")
    print("-" * 70)
    not_taken_liberal = curriculum_service.get_required_courses_not_taken(
        SAMPLE_USER_1,
        course_area="교양"
    )
    formatted_liberal = curriculum_service.format_not_taken_courses(
        not_taken_liberal,
        title="미이수 교양필수"
    )
    print(formatted_liberal)

    # 2025학번 미이수
    print("\n▶️ 2025학번: 미이수 전공필수")
    print("-" * 70)
    not_taken_2025 = curriculum_service.get_required_courses_not_taken(
        SAMPLE_USER_2025_1,
        course_area="전공",
        requirement_type="전공필수"
    )
    formatted_2025 = curriculum_service.format_not_taken_courses(
        not_taken_2025,
        title="미이수 전공필수 (2025학번)"
    )
    print(formatted_2025)

def main():
    print("🎓 교육과정 서비스 테스트 시작\n")
    
    # 기본 테스트
    passed, failed = run_tests()
    
    # 샘플 시나리오
    test_sample_scenarios()
    
    print("\n✅ 테스트 완료!")
    
    if failed == 0:
        print("🎉 모든 테스트 통과!")
    else:
        print(f"⚠️ {failed}개 테스트 실패")


if __name__ == "__main__":
    main()