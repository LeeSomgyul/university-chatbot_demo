"""
교내 연락처 카테고리 정확도 테스트
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from app.services.chatbot import chatbot


CONTACT_TESTS = [
    # 학사 관련
    {
        "id": 1,
        "question": "수강신청 문의 어디로 해야 해?",
        "expected_keywords": ["061-750-3032", "교무학사과"],
        "category": "교내 연락처"
    },
    {
        "id": 2,
        "question": "성적 문의 전화번호 알려줘",
        "expected_keywords": ["061-750-3036", "교무학사과"],
        "category": "교내 연락처"
    },
    {
        "id": 3,
        "question": "휴학 복학 관련 문의처?",
        "expected_keywords": ["061-750-3033", "교무학사과"],
        "category": "교내 연락처"
    },
    {
        "id": 4,
        "question": "졸업 문의는 어디로 해야 돼?",
        "expected_keywords": ["061-750-3035", "교무학사과"],
        "category": "교내 연락처"
    },
    {
        "id": 5,
        "question": "전과 문의 연락처 알려줘",
        "expected_keywords": ["061-750-3033", "교무학사과"],
        "category": "교내 연락처"
    },

    # 장학금 관련
    {
        "id": 6,
        "question": "교내 장학금 어디에 물어봐?",
        "expected_keywords": ["061-750-3061", "학생지원과"],
        "category": "교내 연락처"
    },
    {
        "id": 7,
        "question": "국가 장학금 전화번호 알려줘",
        "expected_keywords": ["061-750-3062", "학생지원과"],
        "category": "교내 연락처"
    },
    {
        "id": 8,
        "question": "근로장학금 문의처 알려줘",
        "expected_keywords": ["061-750-3052", "학생지원과"],
        "category": "교내 연락처"
    },

    # 학생생활 관련
    {
        "id": 9,
        "question": "통학버스 문의 어디로 해?",
        "expected_keywords": ["061-750-3051", "학생지원과"],
        "category": "교내 연락처"
    },
    {
        "id": 10,
        "question": "기숙사 관련 문의처 알려줘",
        "expected_keywords": ["061-750-5064", "학생생활관"],
        "category": "교내 연락처"
    },
    {
        "id": 11,
        "question": "보건진료실 전화번호 뭐야?",
        "expected_keywords": ["061-750-3056", "학생지원과"],
        "category": "교내 연락처"
    },
    {
        "id": 12,
        "question": "학생상담센터 연락처 알려줘",
        "expected_keywords": ["061-750-3174", "학생상담센터"],
        "category": "교내 연락처"
    },

    # 도서관 관련
    {
        "id": 13,
        "question": "도서관 대출/반납 문의처 알려줘",
        "expected_keywords": ["061-750-5020", "학술정보운영팀"],
        "category": "교내 연락처"
    },
    {
        "id": 14,
        "question": "도서관 열람실 문의 전화번호 알려줘",
        "expected_keywords": ["061-750-5014", "학술정보지원팀"],
        "category": "교내 연락처"
    },

    # 컴퓨터공학과 관련
    {
        "id": 15,
        "question": "컴퓨터공학과 사무실 전화번호 뭐야?",
        "expected_keywords": ["061-750-3620", "공학관"],
        "category": "교내 연락처"
    },
    {
        "id": 16,
        "question": "컴퓨터공학과 위치 어디야?",
        "expected_keywords": ["공학관", "3층"],
        "category": "교내 연락처"
    },

    # 입학 관련
    {
        "id": 17,
        "question": "신입생 입학 문의는 어디야?",
        "expected_keywords": ["061-750-5502", "입학지원과"],
        "category": "교내 연락처"
    },
    {
        "id": 18,
        "question": "편입학 문의처 알려줘",
        "expected_keywords": ["061-750-5508", "입학지원과"],
        "category": "교내 연락처"
    },

    # SW중심대학사업단
    {
        "id": 19,
        "question": "SW중심대학사업단 전화번호 알려줘",
        "expected_keywords": ["061-750-5329", "SW중심대학사업단"],
        "category": "교내 연락처"
    },
    {
        "id": 20,
        "question": "SW 해외연수 관련 문의는 어디야?",
        "expected_keywords": ["061-750-5326", "SW중심대학사업단"],
        "category": "교내 연락처"
    },
]


def test_contact(test_cases):
    """교내 연락처 테스트 실행"""
    print("=" * 70)
    print("🏫 교내 연락처 카테고리 정확도 테스트")
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

            keywords_found = [kw for kw in test['expected_keywords'] if kw in answer]
            keywords_missing = [kw for kw in test['expected_keywords'] if kw not in answer]

            is_correct = len(keywords_missing) == 0 or len(keywords_found) >= len(test['expected_keywords']) / 2
            status = "✅" if is_correct else "❌"

            if is_correct:
                correct_count += 1

            print(f"답변: {answer[:150]}{'...' if len(answer) > 150 else ''}")
            print(f"상태: {status}")
            print(f"포함: {keywords_found}")
            if keywords_missing:
                print(f"누락: {keywords_missing}")

            results.append({
                "id": test["id"],
                "question": test["question"],
                "answer": answer,
                "is_correct": is_correct,
                "keywords_found": keywords_found,
                "keywords_missing": keywords_missing,
            })

        except Exception as e:
            print(f"❌ 에러: {e}")
            results.append({
                "id": test["id"],
                "question": test["question"],
                "answer": f"ERROR: {e}",
                "is_correct": False,
                "keywords_found": [],
                "keywords_missing": test["expected_keywords"],
            })

    print("\n" + "=" * 70)
    print("📊 테스트 결과 요약")
    print("=" * 70)

    accuracy = (correct_count / total_count) * 100
    print(f"\n정확도: {correct_count}/{total_count} = {accuracy:.1f}%")

    wrongs = [r for r in results if not r["is_correct"]]
    if wrongs:
        print(f"\n❌ 오답 케이스 ({len(wrongs)}개):")
        for w in wrongs:
            print(f"  #{w['id']}: {w['question']} - 누락: {w['keywords_missing']}")

    print("\n" + "=" * 70)
    return {"accuracy": accuracy, "correct": correct_count, "total": total_count, "results": results}


def save_results(results, filename="contact_test_results.txt"):
    """결과 저장"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("교내 연락처 테스트 결과\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"정확도: {results['accuracy']:.1f}% ({results['correct']}/{results['total']})\n\n")

        for r in results["results"]:
            status = "✅" if r["is_correct"] else "❌"
            f.write(f"{status} #{r['id']} {r['question']}\n")
            f.write(f"답변: {r['answer']}\n")
            f.write(f"포함: {r['keywords_found']}\n")
            if r["keywords_missing"]:
                f.write(f"누락: {r['keywords_missing']}\n")
            f.write("\n" + "-" * 70 + "\n\n")

    print(f"\n💾 결과가 {filename}에 저장되었습니다.")


def main():
    print(f"\n🏫 교내 연락처 카테고리 테스트 시작")
    print(f"테스트 케이스: {len(CONTACT_TESTS)}개\n")

    results = test_contact(CONTACT_TESTS)
    save_results(results)

    print("\n📌 다음 단계:")
    if results["accuracy"] < 90:
        print("1. 오답 케이스 분석")
        print("2. 관련 표현 추가 및 벡터데이터 확장")
        print("3. 프롬프트 튜닝 (교내 연락처 전용)")
        print("4. 재테스트")
    else:
        print("🎉 목표 정확도 달성!")


if __name__ == "__main__":
    print("⚠️ 백엔드 서버(FastAPI)가 실행 중이어야 합니다.\n")
    input("준비되었으면 Enter...")
    main()
