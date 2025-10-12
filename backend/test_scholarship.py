# backend/test_scholarship.py
"""
장학금 카테고리 정확도 테스트
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from app.services.chatbot import chatbot


SCHOLARSHIP_TESTS = [
    # 장학금 종류
    {
        "id": 1,
        "question": "장학금 종류 뭐 있어?",
        "expected_keywords": ["우석", "성적우수", "국가장학금"],
        "category": "장학금"
    },
    {
        "id": 2,
        "question": "신입생 장학금 알려줘",
        "expected_keywords": ["우석", "글로컬", "성적우수"],
        "category": "장학금"
    },
    
    # 우석장학생
    {
        "id": 3,
        "question": "우석장학생이 뭐야?",
        "expected_keywords": ["5등급", "전액", "200만원"],
        "category": "장학금"
    },
    {
        "id": 4,
        "question": "우석장학생 조건은?",
        "expected_keywords": ["5등급", "3.90"],
        "category": "장학금"
    },
    
    # 성적 기준
    {
        "id": 5,
        "question": "장학금 받으려면 성적이 얼마나?",
        "expected_keywords": ["2.75", "1.75"],
        "category": "장학금"
    },
    {
        "id": 6,
        "question": "성적 장학금 조건",
        "expected_keywords": ["2.75", "12학점"],
        "category": "장학금"
    },
    
    # 국가장학금
    {
        "id": 7,
        "question": "국가장학금 신청 어떻게 해?",
        "expected_keywords": ["한국장학재단", "홈페이지"],
        "category": "장학금"
    },
    {
        "id": 8,
        "question": "국가장학금 얼마 받아?",
        "expected_keywords": ["285만원", "분위"],
        "category": "장학금"
    },
    {
        "id": 9,
        "question": "국가장학금 신청 시기",
        "expected_keywords": ["11월", "5월"],
        "category": "장학금"
    },
    
    # 특별 장학금
    {
        "id": 10,
        "question": "가족이 같이 다니면 장학금 있어?",
        "expected_keywords": ["가족", "2인", "2.50"],
        "category": "장학금"
    },
    {
        "id": 11,
        "question": "국가유공자 장학금",
        "expected_keywords": ["전액", "1.75"],
        "category": "장학금"
    },
    {
        "id": 12,
        "question": "장애 학생 장학금",
        "expected_keywords": ["장애", "전액"],
        "category": "장학금"
    },
    
    # 연락처/문의
    {
        "id": 13,
        "question": "장학금 문의 어디로?",
        "expected_keywords": ["061-750-3061", "061-750-3062"],
        "category": "장학금"
    },
    {
        "id": 14,
        "question": "교내 장학금 연락처",
        "expected_keywords": ["061-750-3061"],
        "category": "장학금"
    },
    
    # 기타
    {
        "id": 15,
        "question": "포스코 엘리트 장학금",
        "expected_keywords": ["50만원", "3.90"],
        "category": "장학금"
    },
    {
        "id": 16,
        "question": "농업인 자녀 장학금",
        "expected_keywords": ["농업인", "학과", "상관없"],
        "category": "장학금"
    },
    {
        "id": 17,
        "question": "장학금 중복으로 받을 수 있어?",
        "expected_keywords": ["중복", "가능", "불가"],
        "category": "장학금"
    },
    {
        "id": 18,
        "question": "글로컬 장학금이 뭐야?",
        "expected_keywords": ["600만원", "전액"],
        "category": "장학금"
    },
    {
        "id": 19,
        "question": "장학금 신청 언제 해?",
        "expected_keywords": ["매 학기", "11월", "5월"],
        "category": "장학금"
    },
    {
        "id": 20,
        "question": "재학생 장학금",
        "expected_keywords": ["성적우수", "12학점"],
        "category": "장학금"
    },
]


def test_scholarships(test_cases):
    """장학금 테스트 실행"""
    print("=" * 70)
    print("💰 장학금 카테고리 정확도 테스트")
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
            print(f"\n  #{wa['id']}: {wa['question']}")
            print(f"  답변: {wa['answer'][:100]}...")
            print(f"  누락: {wa['keywords_missing']}")
    
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


def save_results(results, filename="scholarship_test_results.txt"):
    """결과 저장"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("장학금 카테고리 테스트 결과\n")
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
    print(f"\n💰 장학금 카테고리 테스트")
    print(f"테스트 케이스: {len(SCHOLARSHIP_TESTS)}개\n")
    
    results = test_scholarships(SCHOLARSHIP_TESTS)
    save_results(results)
    
    print("\n📌 다음 단계:")
    if results['accuracy'] < 90:
        print("1. 오답 케이스 분석")
        print("2. 데이터 개선")
        print("3. 재테스트")
    else:
        print("🎉 목표 정확도 달성!")


if __name__ == "__main__":
    print("⚠️  백엔드 서버가 실행 중이어야 합니다.\n")
    input("준비되었으면 Enter...")
    main()