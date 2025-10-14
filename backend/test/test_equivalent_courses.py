"""
동일대체교과목 테스트
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from app.services.equivalent_course_service import equivalent_course_service
from app.services.curriculum_service import curriculum_service
from app.models.schemas import UserProfile, CourseInput


# ===== 테스트 케이스 =====

EQUIVALENT_TESTS = [
    # 1. 구 → 신 과목 조회
    {
        "id": 1,
        "name": "구 → 신 과목 조회 (CS0119 → CS0601)",
        "test_func": lambda: equivalent_course_service.get_equivalent_course("CS0119"),
        "evaluation": lambda result: result is not None and result['new_course_code'] == 'CS0601',
        "expected": "CS0119 → CS0601 (동일)"
    },
    
    # 2. 신 → 구 과목 조회
    {
        "id": 2,
        "name": "신 → 구 과목 조회 (CS0601 → CS0119)",
        "test_func": lambda: equivalent_course_service.get_equivalent_course("CS0601", "new_to_old"),
        "evaluation": lambda result: result is not None and result['old_course_code'] == 'CS0119',
        "expected": "CS0601 → CS0119 (역방향)"
    },
    
    # 3. 동일 과목 확인
    {
        "id": 3,
        "name": "동일 과목 확인",
        "test_func": lambda: equivalent_course_service.is_equivalent("CS0119", "CS0601"),
        "evaluation": lambda result: result == True,
        "expected": "CS0119와 CS0601은 동일"
    },
    
    # 4. 대체 과목 (다른 이름)
    {
        "id": 4,
        "name": "대체 과목 확인 (CS0122 → CS0665)",
        "test_func": lambda: equivalent_course_service.get_equivalent_course("CS0122"),
        "evaluation": lambda result: (
            result is not None and 
            result['new_course_code'] == 'CS0665' and 
            result['mapping_type'] == '대체'
        ),
        "expected": "정보통신개론 → 컴퓨터과학 (대체)"
    },
    
    # 5. 최신 코드로 변환
    {
        "id": 5,
        "name": "최신 코드 변환",
        "test_func": lambda: equivalent_course_service.resolve_course_code("CS0252"),
        "evaluation": lambda result: result == "CS0603",
        "expected": "CS0252 → CS0603"
    },
    
    # 6. 변경 정보 문자열
    {
        "id": 6,
        "name": "변경 정보 조회",
        "test_func": lambda: equivalent_course_service.get_mapping_info("CS0119"),
        "evaluation": lambda result: "CS0119" in result and "CS0601" in result and "동일" in result,
        "expected": "CS0119 기초설계 → CS0601 기초설계 (동일)"
    },
]

CURRICULUM_INTEGRATION_TESTS = [
    {
        "id": 7,
        "name": "졸업사정 - 구 과목 코드 인정",
        "test_func": lambda: curriculum_service.calculate_remaining_credits(SAMPLE_USER_OLD_CODE),
        "evaluation": lambda result: (
            'error' not in result and 
            result['major']['details']['전공필수']['taken'] >= 15
        ),
        "expected": "구 과목 코드 5개(15학점)를 전공필수로 인정"
    },
    {
        "id": 8,
        "name": "졸업사정 - 대체 과목 인정",
        "test_func": lambda: curriculum_service.calculate_remaining_credits(SAMPLE_USER_SUBSTITUTION),
        "evaluation": lambda result: (
            'error' not in result and 
            result['major']['details']['전공필수']['taken'] >= 6
        ),
        "expected": "대체 과목도 전공필수로 인정"
    }
]

CHAIN_TESTS = [
    # 8. 체인 추적 - 최종 코드
    {
        "id": 9,
        "name": "체인 추적 - 최종 코드 (CS0116 → CS0863)",
        "test_func": lambda: equivalent_course_service.get_latest_course_code("CS0116"),
        "evaluation": lambda result: result == "CS0863",
        "expected": "CS0116의 최종 코드는 CS0863"
    },
    
    # 9. 체인 이력 조회
    {
        "id": 10,
        "name": "체인 이력 조회 (CS0116)",
        "test_func": lambda: equivalent_course_service.get_course_history("CS0116"),
        "evaluation": lambda result: (
            len(result) == 3 and 
            result[0]['code'] == "CS0116" and
            result[1]['code'] == "CS0612" and
            result[2]['code'] == "CS0863"
        ),
        "expected": "CS0116 → CS0612 → CS0863 (3단계)"
    },
    
    # 10. 체인 형식화
    {
        "id": 11,
        "name": "체인 형식화",
        "test_func": lambda: equivalent_course_service.format_course_history("CS0116"),
        "evaluation": lambda result: (
            "CS0116" in result and 
            "CS0612" in result and 
            "CS0863" in result and
            "→" in result
        ),
        "expected": "CS0116 → CS0612 → CS0863 (화살표 포함)"
    },
    
    # 11. 체인의 중간 코드 조회
    {
        "id": 12,
        "name": "중간 코드에서 최종 코드 찾기 (CS0612 → CS0863)",
        "test_func": lambda: equivalent_course_service.get_latest_course_code("CS0612"),
        "evaluation": lambda result: result == "CS0863",
        "expected": "CS0612도 CS0863으로 변환"
    },
    
    # 12. 체인 동일성 확인
    {
        "id": 13,
        "name": "체인 동일성 (CS0116 = CS0863)",
        "test_func": lambda: equivalent_course_service.is_equivalent("CS0116", "CS0863"),
        "evaluation": lambda result: result == True,
        "expected": "CS0116과 CS0863은 같은 과목"
    },
    
    # 13. 모든 코드 조회
    {
        "id": 14,
        "name": "전체 코드 목록 (CS0116)",
        "test_func": lambda: equivalent_course_service.get_all_equivalent_codes("CS0116"),
        "evaluation": lambda result: (
            "CS0116" in result and 
            "CS0612" in result and 
            "CS0863" in result
        ),
        "expected": "[CS0116, CS0612, CS0863]"
    },
]



# ===== 졸업사정 통합 테스트 =====

# 구 과목 코드로 들은 학생
SAMPLE_USER_OLD_CODE = UserProfile(
    admission_year=2024,
    current_semester=2,
    courses_taken=[
        # CS0252 → CS0603 (자료구조)
        CourseInput(
            course_code="CS0252",
            course_name="자료구조",
            credit=3,
            course_area="전공",
            requirement_type="전공필수"
        ),
        # CS0851 → CS0623 (이산수학)
        CourseInput(
            course_code="CS0851",
            course_name="컴퓨터수학",
            credit=3,
            course_area="전공",
            requirement_type="전공필수"
        ),
        # CS0111 → CS0610 (운영체제)
        CourseInput(
            course_code="CS0111",
            course_name="운영체제",
            credit=3,
            course_area="전공",
            requirement_type="전공필수"
        ),
        # CS0406 → CS0662 (인공지능)
        CourseInput(
            course_code="CS0406",
            course_name="인공지능",
            credit=3,
            course_area="전공",
            requirement_type="전공필수"
        ),
        # CS0116 → CS0612 (컴퓨터그래픽스)
        CourseInput(
            course_code="CS0116",
            course_name="컴퓨터그래픽스",
            credit=3,
            course_area="전공",
            requirement_type="전공필수"
        ),
    ]
)

SAMPLE_USER_SUBSTITUTION = UserProfile(
    admission_year=2024,
    current_semester=2,
    courses_taken=[
        # CS0609 → CS0617 (데이터베이스설계 → 데이터베이스) [대체]
        CourseInput(
            course_code="CS0609",
            course_name="데이터베이스설계",
            credit=3,
            course_area="전공",
            requirement_type="전공필수"
        ),
        # CS0619 → CS0621 (패턴인식 → 디지털이미징) [대체]
        CourseInput(
            course_code="CS0619",
            course_name="패턴인식",
            credit=3,
            course_area="전공",
            requirement_type="전공필수"
        ),
    ]
)


def run_tests():
    """테스트 실행"""
    print("=" * 70)
    print("🔄 동일대체교과목 테스트")
    print("=" * 70)
    
    all_tests = EQUIVALENT_TESTS + CHAIN_TESTS + CURRICULUM_INTEGRATION_TESTS
    passed = 0
    failed = 0
    
    for test in all_tests:
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
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"📊 테스트 결과: {passed}개 통과 / {failed}개 실패")
    print("=" * 70)
    
    return passed, failed


def main():
    print("🔄 동일대체교과목 테스트 시작\n")
    
    passed, failed = run_tests()
    
    print("\n✅ 테스트 완료!")
    
    if failed == 0:
        print("🎉 모든 테스트 통과!")
    else:
        print(f"⚠️ {failed}개 테스트 실패")


if __name__ == "__main__":
    main()