"""
Entity Extractor 테스트
"""
from app.services.entity_extractor import entity_extractor


def test_extract_year():
    """입학년도 추출 테스트"""
    print("\n📅 입학년도 추출 테스트")
    print("-" * 50)
    
    test_cases = [
        "2024학번이고 CS0614 들었어",
        "24학번, CS0614 들었어",
        "2025년 입학생 전공필수 뭐야?",
        "남은 학점 알려줘"  # 없어야 함
    ]
    
    for message in test_cases:
        year = entity_extractor.extract_admission_year(message)
        print(f"메시지: {message}")
        print(f"→ 추출: {year}\n")


def test_extract_codes():
    """과목 코드 추출 테스트"""
    print("\n📚 과목 코드 추출 테스트")
    print("-" * 50)
    
    test_cases = [
        "CS0614, XG0800 들었어",
        "cs0614 들었어",  # 소문자
        "남은 학점 알려줘"  # 없어야 함
    ]
    
    for message in test_cases:
        codes = entity_extractor.extract_course_codes(message)
        print(f"메시지: {message}")
        print(f"→ 추출: {codes}\n")


def test_full_extraction():
    """전체 정보 추출 테스트"""
    print("\n🔍 전체 정보 추출 테스트")
    print("-" * 50)
    
    message = "2024학번이고 CS0614, XG0800 들었어"
    
    result = entity_extractor.extract_course_info(message)
    
    print(f"메시지: {message}\n")
    print(f"입학년도: {result['admission_year']}")
    print(f"과목 코드: {result['course_codes']}")
    print(f"과목 상세: {len(result['courses'])}개")
    print(f"정보 충분: {result['has_enough_info']}")
    
    for course in result['courses']:
        print(f"  - {course.course_code} {course.course_name} ({course.credit}학점)")


if __name__ == "__main__":
    print("=" * 50)
    print("🧪 Entity Extractor 테스트")
    print("=" * 50)
    
    test_extract_year()
    test_extract_codes()
    test_full_extraction()
    
    print("\n" + "=" * 50)
    print("✅ 테스트 완료!")
    print("=" * 50)