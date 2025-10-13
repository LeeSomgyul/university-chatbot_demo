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


# ===== 테스트 케이스 =====

CURRICULUM_TESTS = [
    # 1. 졸업 요건 조회
    {
        "id": 1,
        "name": "졸업 요건 조회",
        "test_func": lambda: curriculum_service.get_graduation_requirements(2024),
        "evaluation": lambda result: len(result) > 0,
        "expected": "졸업 요건 데이터 존재"
    },
    
    # 2. 남은 학점 계산 (샘플 1)
    {
        "id": 2,
        "name": "남은 학점 계산 (1학년)",
        "test_func": lambda: curriculum_service.calculate_remaining_credits(SAMPLE_USER_1),
        "evaluation": lambda result: 'error' not in result and result['total_taken'] == 6,
        "expected": "총 6학점 이수"
    },
    
    # 3. 남은 학점 계산 (샘플 2)
    {
        "id": 3,
        "name": "남은 학점 계산 (3학년)",
        "test_func": lambda: curriculum_service.calculate_remaining_credits(SAMPLE_USER_2),
        "evaluation": lambda result: 'error' not in result and result['total_taken'] == 33,
        "expected": "총 33학점 이수"
    },
    
    # 4. 미이수 전공필수 과목
    {
        "id": 4,
        "name": "미이수 전공필수 과목",
        "test_func": lambda: curriculum_service.get_courses_not_taken(SAMPLE_USER_1, "전공필수"),
        "evaluation": lambda result: len(result) > 0,
        "expected": "미이수 전공필수 과목 존재"
    },
    
    # 5. 포맷팅 테스트
    {
        "id": 5,
        "name": "결과 포맷팅",
        "test_func": lambda: curriculum_service.format_curriculum_info(
            curriculum_service.calculate_remaining_credits(SAMPLE_USER_1)
        ),
        "evaluation": lambda result: "졸업 요건 현황" in result and "전공" in result,
        "expected": "포맷팅된 문자열 반환"
    },
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
    
    # 시나리오 1: 1학년 학생
    print("\n▶️ 시나리오 1: 1학년 학생 (7학점 이수)")
    print("-" * 70)
    result1 = curriculum_service.calculate_remaining_credits(SAMPLE_USER_1)
    formatted1 = curriculum_service.format_curriculum_info(result1)
    print(formatted1)
    
    # 시나리오 2: 3학년 학생
    print("\n▶️ 시나리오 2: 3학년 학생 (30+학점 이수)")
    print("-" * 70)
    result2 = curriculum_service.calculate_remaining_credits(SAMPLE_USER_2)
    formatted2 = curriculum_service.format_curriculum_info(result2)
    print(formatted2)
    
    # 시나리오 3: 미이수 과목 조회
    print("\n▶️ 시나리오 3: 미이수 전공필수 과목")
    print("-" * 70)
    not_taken = curriculum_service.get_courses_not_taken(SAMPLE_USER_1, "전공필수")
    print(f"총 {len(not_taken)}개 과목")
    for i, course in enumerate(not_taken[:5], 1):
        print(f"  {i}. {course['course_name']} ({course['course_code']}) - {course['credit']}학점 - {course['grade']}학년 {course['semester']}학기")
    if len(not_taken) > 5:
        print(f"  ... 외 {len(not_taken) - 5}개")


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