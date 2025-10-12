"""
통학버스 카테고리 정확도 테스트
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from app.services.chatbot import chatbot


SCHOOL_BUS_TESTS = [
    # 노선 - 지역별
    {
        "id": 1,
        "question": "통학버스 어디 가?",
        "expected_keywords": ["광주", "여수", "동광양"],
        "category": "통학버스"
    },
    {
        "id": 2,
        "question": "광주 통학버스 있어?",
        "expected_keywords": ["광주", "4개", "노선"],
        "category": "통학버스"
    },
    {
        "id": 3,
        "question": "여수 가는 버스",
        "expected_keywords": ["여수", "3개"],
        "category": "통학버스"
    },
    {
        "id": 4,
        "question": "동광양 버스",
        "expected_keywords": ["동광양", "백운아트홀"],
        "category": "통학버스"
    },
    {
        "id": 5,
        "question": "순천 시내 버스",
        "expected_keywords": ["순천", "조례동"],
        "category": "통학버스"
    },
    
    # 시간
    {
        "id": 6,
        "question": "광주 버스 몇 시에 와?",
        "expected_keywords": ["07:00", "07:25"],
        "category": "통학버스"
    },
    {
        "id": 7,
        "question": "여수 버스 시간표",
        "expected_keywords": ["07:25", "18:30"],
        "category": "통학버스"
    },
    {
        "id": 8,
        "question": "야간 버스 있어?",
        "expected_keywords": ["21:30", "여수", "3호차"],
        "category": "통학버스"
    },
    {
        "id": 9,
        "question": "첫차 몇 시야?",
        "expected_keywords": ["07:00", "첫차"],
        "category": "통학버스"
    },
    
    # 예약
    {
        "id": 10,
        "question": "통학버스 예약 어떻게 해?",
        "expected_keywords": ["scnu.unibus.kr", "예약"],
        "category": "통학버스"
    },
    {
        "id": 11,
        "question": "통학버스 예약 사이트",
        "expected_keywords": ["scnu.unibus.kr"],
        "category": "통학버스"
    },
    {
        "id": 12,
        "question": "버스 QR코드 어떻게 써?",
        "expected_keywords": ["모바일", "승차권", "스캔"],
        "category": "통학버스"
    },
    
    # 문의
    {
        "id": 13,
        "question": "통학버스 문의 어디로?",
        "expected_keywords": ["061-750-3054"],
        "category": "통학버스"
    },
    {
        "id": 14,
        "question": "순천 버스 연락처",
        "expected_keywords": ["061-750-3088"],
        "category": "통학버스"
    },
    
    # 정류장
    {
        "id": 15,
        "question": "광천터미널에서 타는 버스",
        "expected_keywords": ["광주", "광천터미널"],
        "category": "통학버스"
    },
    {
        "id": 16,
        "question": "여수터미널 버스",
        "expected_keywords": ["여수", "터미널"],
        "category": "통학버스"
    },
    
    # 문제 상황
    {
        "id": 17,
        "question": "통학버스 회원가입 안 돼",
        "expected_keywords": ["향림통", "휴대폰"],
        "category": "통학버스"
    },
    {
        "id": 18,
        "question": "버스 예약 취소",
        "expected_keywords": ["scnu.unibus.kr", "취소"],
        "category": "통학버스"
    },
    
    # 특정 상황
    {
        "id": 19,
        "question": "늦게 끝나는데 버스 있어?",
        "expected_keywords": ["21:30", "야간", "여수"],
        "category": "통학버스"
    },
    {
        "id": 20,
        "question": "통학버스 요금",
        "expected_keywords": ["061-750-3054", "문의"],
        "category": "통학버스"
    },
]


def test_school_bus(test_cases):
    """통학버스 테스트 실행"""
    print("=" * 70)
    print("🚌 통학버스 카테고리 정확도 테스트")
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
                if keyword.lower() in answer.lower():
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
            print(f"  #{wa['id']}: {wa['question']} - 누락: {wa['keywords_missing']}")
    
    # 정답 목록
    correct_answers = [r for r in results if r['is_correct']]
    if correct_answers:
        print(f"\n✅ 정답 케이스 ({len(correct_answers)}개):")
        for ca in correct_answers[:5]:
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


def main():
    print(f"\n🚌 통학버스 카테고리 테스트")
    print(f"테스트 케이스: {len(SCHOOL_BUS_TESTS)}개\n")
    
    results = test_school_bus(SCHOOL_BUS_TESTS)
    
    print("\n📌 결과:")
    if results['accuracy'] >= 90:
        print("🎉 목표 정확도 달성!")
    else:
        print("📝 개선 필요")


if __name__ == "__main__":
    print("⚠️  백엔드 서버가 실행 중이어야 합니다.\n")
    input("준비되었으면 Enter...")
    main()