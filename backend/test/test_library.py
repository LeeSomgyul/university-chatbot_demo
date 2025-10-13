"""
도서관 카테고리 정확도 테스트
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from app.services.chatbot import chatbot


# 도서관 테스트 케이스
LIBRARY_TESTS = [
    # 운영시간 관련 (기본)
    {
        "id": 1,
        "question": "도서관 운영시간 알려줘",
        "expected_keywords": ["09:00", "20:00"],
        "category": "도서관"
    },
    {
        "id": 2,
        "question": "자료관 몇 시까지 해?",
        "expected_keywords": ["20:00", "자료관"],
        "category": "도서관"
    },
    {
        "id": 3,
        "question": "열람실 24시간이야?",
        "expected_keywords": ["06:00", "24:00", "열람실"],
        "category": "도서관"
    },
    {
        "id": 4,
        "question": "미디어라운지 운영시간은?",
        "expected_keywords": ["09:00", "18:00"],
        "category": "도서관"
    },
    {
        "id": 5,
        "question": "도서관 주말에 열어?",
        "expected_keywords": ["열람실", "휴관"],
        "category": "도서관"
    },
    
    # 대출/반납 관련
    {
        "id": 6,
        "question": "책 몇 권 빌릴 수 있어?",
        "expected_keywords": ["7책", "학부생"],
        "category": "도서관"
    },
    {
        "id": 7,
        "question": "대출 기간은?",
        "expected_keywords": ["14일", "학부생"],
        "category": "도서관"
    },
    {
        "id": 8,
        "question": "책 연장 가능해?",
        "expected_keywords": ["1회", "연장"],
        "category": "도서관"
    },
    {
        "id": 9,
        "question": "책 어떻게 빌려?",
        "expected_keywords": ["대출", "학생증"],
        "category": "도서관"
    },
    {
        "id": 10,
        "question": "무인반납기 어디 있어?",
        "expected_keywords": ["1층", "제증명발급기"],
        "category": "도서관"
    },
    
    # 시설 안내
    {
        "id": 11,
        "question": "그룹스터디실 어디 있어?",
        "expected_keywords": ["1층", "3층"],
        "category": "도서관"
    },
    {
        "id": 12,
        "question": "스터디룸 예약 어떻게 해?",
        "expected_keywords": ["모바일", "애플리케이션"],
        "category": "도서관"
    },
    {
        "id": 13,
        "question": "2층에 뭐 있어?",
        "expected_keywords": ["열람실", "창의마루"],
        "category": "도서관"
    },
    {
        "id": 14,
        "question": "미디어라운지에서 뭐 할 수 있어?",
        "expected_keywords": ["DVD", "VR"],
        "category": "도서관"
    },
    {
        "id": 15,
        "question": "복사는 어디서 해?",
        "expected_keywords": ["2층", "복사실"],
        "category": "도서관"
    },
    
    # 이용 자격
    {
        "id": 16,
        "question": "휴학생도 도서관 이용 가능해?",
        "expected_keywords": ["휴학생", "가능"],
        "category": "도서관"
    },
    {
        "id": 17,
        "question": "졸업생도 책 빌릴 수 있어?",
        "expected_keywords": ["졸업생", "2년"],
        "category": "도서관"
    },
    {
        "id": 18,
        "question": "지역주민 이용 가능해?",
        "expected_keywords": ["특별열람증", "30,000"],
        "category": "도서관"
    },
    
    # 연체/규정
    {
        "id": 19,
        "question": "책 연체하면 어떻게 돼?",
        "expected_keywords": ["대출 정지", "연체"],
        "category": "도서관"
    },
    {
        "id": 20,
        "question": "책 잃어버렸는데 어떡해?",
        "expected_keywords": ["변상", "동일"],
        "category": "도서관"
    },
]


def test_library(test_cases):
    """도서관 테스트 실행"""
    print("=" * 70)
    print("📚 도서관 카테고리 정확도 테스트")
    print("=" * 70)
    
    results = []
    correct_count = 0
    total_count = len(test_cases)
    
    for test in test_cases:
        print(f"\n테스트 #{test['id']}: {test['question']}")
        print("-" * 70)
        
        try:
            response = chatbot.chat(
                message=test['question'],
                user_profile=None,
                history=[]
            )
            answer = response['message']
            
            # 키워드 체크
            keywords_found = []
            keywords_missing = []
            
            for keyword in test['expected_keywords']:
                if keyword in answer:
                    keywords_found.append(keyword)
                else:
                    keywords_missing.append(keyword)
            
            # 정답 판단
            is_correct = len(keywords_missing) == 0 or \
                        len(keywords_found) >= len(test['expected_keywords']) / 2
            
            if is_correct:
                correct_count += 1
                status = "✅"
            else:
                status = "❌"
            
            print(f"답변: {answer[:150]}{'...' if len(answer) > 150 else ''}")
            print(f"상태: {status}")
            print(f"포함: {keywords_found}")
            if keywords_missing:
                print(f"누락: {keywords_missing}")
            
            results.append({
                "id": test['id'],
                "question": test['question'],
                "answer": answer,
                "is_correct": is_correct,
                "keywords_found": keywords_found,
                "keywords_missing": keywords_missing
            })
            
        except Exception as e:
            print(f"❌ 에러: {e}")
            results.append({
                "id": test['id'],
                "question": test['question'],
                "answer": f"ERROR: {e}",
                "is_correct": False,
                "keywords_found": [],
                "keywords_missing": test['expected_keywords']
            })
    
    # 결과 요약
    print("\n" + "=" * 70)
    print("📊 테스트 결과 요약")
    print("=" * 70)
    
    accuracy = (correct_count / total_count) * 100
    print(f"\n정확도: {correct_count}/{total_count} = {accuracy:.1f}%")
    
    # 오답 목록
    wrong_answers = [r for r in results if not r['is_correct']]
    if wrong_answers:
        print(f"\n❌ 오답 케이스 ({len(wrong_answers)}개):")
        for wa in wrong_answers:
            print(f"\n  #{wa['id']}: {wa['question']}")
            print(f"  답변: {wa['answer'][:100]}...")
            print(f"  누락: {wa['keywords_missing']}")
    
    # 정답 목록
    correct_answers = [r for r in results if r['is_correct']]
    if correct_answers:
        print(f"\n✅ 정답 케이스 ({len(correct_answers)}개):")
        for ca in correct_answers[:5]:  # 처음 5개만
            print(f"  #{ca['id']}: {ca['question']}")
        if len(correct_answers) > 5:
            print(f"  ... 외 {len(correct_answers) - 5}개")
    
    print("\n" + "=" * 70)
    
    return {
        "accuracy": accuracy,
        "correct": correct_count,
        "total": total_count,
        "results": results
    }


def save_results(results, filename="library_test_results.txt"):
    """결과 저장"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("도서관 카테고리 테스트 결과\n")
        f.write("=" * 70 + "\n\n")
        
        f.write(f"정확도: {results['accuracy']:.1f}% ({results['correct']}/{results['total']})\n\n")
        
        f.write("=" * 70 + "\n")
        f.write("상세 결과\n")
        f.write("=" * 70 + "\n\n")
        
        for r in results['results']:
            status = "✅" if r['is_correct'] else "❌"
            f.write(f"{status} 테스트 #{r['id']}: {r['question']}\n")
            f.write(f"답변: {r['answer']}\n")
            f.write(f"포함: {r['keywords_found']}\n")
            if r['keywords_missing']:
                f.write(f"누락: {r['keywords_missing']}\n")
            f.write("\n" + "-" * 70 + "\n\n")
    
    print(f"\n💾 결과가 {filename}에 저장되었습니다.")


def main():
    print(f"\n📚 도서관 카테고리 테스트")
    print(f"테스트 케이스: {len(LIBRARY_TESTS)}개\n")
    
    results = test_library(LIBRARY_TESTS)
    save_results(results)
    
    print("\n📌 다음 단계:")
    if results['accuracy'] < 90:
        print("1. 오답 케이스 분석")
        print("2. 데이터 개선 (다양한 표현 추가)")
        print("3. 프롬프트 튜닝 (도서관 전용)")
        print("4. 재테스트")
    else:
        print("🎉 목표 정확도 달성!")


if __name__ == "__main__":
    print("⚠️  백엔드 서버가 실행 중이어야 합니다.\n")
    input("준비되었으면 Enter...")
    main()