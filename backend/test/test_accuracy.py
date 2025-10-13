"""
챗봇 정확도 테스트 스크립트
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from app.services.chatbot import chatbot
from app.models.schemas import UserProfile


# 학사일정 테스트 케이스
ACADEMIC_CALENDAR_TESTS = [
    {
        "id": 1,
        "question": "2025년 1학기 개강일은?",
        "expected_keywords": ["3월 4일", "2025"],
        "category": "학사일정"
    },
    {
        "id": 2,
        "question": "개강 언제야?",
        "expected_keywords": ["3월 4일", "개강"],
        "category": "학사일정"
    },
    {
        "id": 3,
        "question": "1학기 시작일 알려줘",
        "expected_keywords": ["3월 4일"],
        "category": "학사일정"
    },
    {
        "id": 4,
        "question": "중간고사 언제야?",
        "expected_keywords": ["4월 21일", "4월 25일"],
        "category": "학사일정"
    },
    {
        "id": 5,
        "question": "중간고사 기간은?",
        "expected_keywords": ["4월", "중간"],
        "category": "학사일정"
    },
    {
        "id": 6,
        "question": "기말고사 언제 봐?",
        "expected_keywords": ["6월", "기말"],
        "category": "학사일정"
    },
    {
        "id": 7,
        "question": "2025년 1학기 종강일은?",
        "expected_keywords": ["6월 23일", "종강"],
        "category": "학사일정"
    },
    {
        "id": 8,
        "question": "학기 언제 끝나?",
        "expected_keywords": ["6월", "종강"],
        "category": "학사일정"
    },
    {
        "id": 9,
        "question": "여름방학 언제부터야?",
        "expected_keywords": ["6월", "여름"],
        "category": "학사일정"
    },
    {
        "id": 10,
        "question": "2025년 2학기 개강일은?",
        "expected_keywords": ["9월 1일", "2025", "2학기"],
        "category": "학사일정"
    },
    {
        "id": 11,
        "question": "개강은 3월 몇 일이야?",
        "expected_keywords": ["4일"],
        "category": "학사일정"
    },
    {
        "id": 12,
        "question": "시험 언제 봐?",
        "expected_keywords": ["중간", "기말"],  # 둘 중 하나라도 있으면
        "category": "학사일정"
    },
    {
        "id": 13,
        "question": "개강 전 수강신청 기간은?",
        "expected_keywords": ["2월", "수강신청"],
        "category": "학사일정"
    },
    {
        "id": 14,
        "question": "휴일은 언제야?",
        "expected_keywords": ["공휴일", "휴일"],
        "category": "학사일정"
    },
    {
        "id": 15,
        "question": "개강 몇 월이야?",
        "expected_keywords": ["3월"],
        "category": "학사일정"
    },
]


def test_chatbot(test_cases):
    """챗봇 테스트 실행"""
    print("=" * 70)
    print("🧪 챗봇 정확도 테스트 시작")
    print("=" * 70)
    
    results = []
    correct_count = 0
    total_count = len(test_cases)
    
    for test in test_cases:
        print(f"\n테스트 #{test['id']}: {test['question']}")
        print("-" * 70)
        
        # 챗봇 호출
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
            
            # 정답 판단 (모든 키워드가 있거나, 절반 이상 있으면 정답)
            is_correct = len(keywords_missing) == 0 or \
                        len(keywords_found) >= len(test['expected_keywords']) / 2
            
            if is_correct:
                correct_count += 1
                status = "✅ 정답"
            else:
                status = "❌ 오답"
            
            print(f"답변: {answer[:150]}{'...' if len(answer) > 150 else ''}")
            print(f"상태: {status}")
            print(f"포함된 키워드: {keywords_found}")
            if keywords_missing:
                print(f"누락된 키워드: {keywords_missing}")
            
            # 결과 저장
            results.append({
                "id": test['id'],
                "question": test['question'],
                "answer": answer,
                "is_correct": is_correct,
                "keywords_found": keywords_found,
                "keywords_missing": keywords_missing
            })
            
        except Exception as e:
            print(f"❌ 에러 발생: {e}")
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
        for ca in correct_answers:
            print(f"  #{ca['id']}: {ca['question']}")
    
    print("\n" + "=" * 70)
    
    return {
        "accuracy": accuracy,
        "correct": correct_count,
        "total": total_count,
        "results": results
    }


def save_results(results, filename="test_results.txt"):
    """결과를 파일로 저장"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("챗봇 정확도 테스트 결과\n")
        f.write("=" * 70 + "\n\n")
        
        f.write(f"정확도: {results['accuracy']:.1f}% ({results['correct']}/{results['total']})\n\n")
        
        f.write("=" * 70 + "\n")
        f.write("상세 결과\n")
        f.write("=" * 70 + "\n\n")
        
        for r in results['results']:
            status = "✅" if r['is_correct'] else "❌"
            f.write(f"{status} 테스트 #{r['id']}: {r['question']}\n")
            f.write(f"답변: {r['answer']}\n")
            f.write(f"포함된 키워드: {r['keywords_found']}\n")
            if r['keywords_missing']:
                f.write(f"누락된 키워드: {r['keywords_missing']}\n")
            f.write("\n" + "-" * 70 + "\n\n")
    
    print(f"\n💾 결과가 {filename}에 저장되었습니다.")


def main():
    """메인 실행"""
    print("\n🎯 학사일정 카테고리 테스트")
    print(f"테스트 케이스: {len(ACADEMIC_CALENDAR_TESTS)}개\n")
    
    # 테스트 실행
    results = test_chatbot(ACADEMIC_CALENDAR_TESTS)
    
    # 결과 저장
    save_results(results, "academic_calendar_test_results.txt")
    
    # 다음 단계 안내
    print("\n📌 다음 단계:")
    if results['accuracy'] < 90:
        print("1. 오답 케이스 분석")
        print("2. 데이터 또는 프롬프트 개선")
        print("3. 다시 테스트")
    else:
        print("🎉 목표 정확도 달성!")


if __name__ == "__main__":
    # 백엔드 서버가 실행 중이어야 함
    print("⚠️  주의: 백엔드 서버가 실행 중이어야 합니다.")
    print("   다른 터미널에서 'python app/main.py' 실행 확인\n")
    
    input("준비되었으면 Enter를 누르세요...")
    
    main()