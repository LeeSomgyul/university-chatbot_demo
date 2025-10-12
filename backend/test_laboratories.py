"""
실험실 카테고리 정확도 테스트
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from app.services.chatbot import chatbot


LABORATORY_TESTS = [
    # 실험실 소개
    {
        "id": 1,
        "question": "실험실 몇 개 있어?",
        "expected_keywords": ["4개", "실험실"],
        "category": "실험실"
    },
    {
        "id": 2,
        "question": "컴퓨터공학과 실험실 알려줘",
        "expected_keywords": ["소프트웨어공학", "컴퓨터비전"],
        "category": "실험실"
    },
    
    # AI 관련
    {
        "id": 3,
        "question": "AI 연구하는 실험실 어디야?",
        "expected_keywords": ["컴퓨터비전", "김종찬"],
        "category": "실험실"
    },
    {
        "id": 4,
        "question": "딥러닝 공부하고 싶은데 어느 실험실?",
        "expected_keywords": ["컴퓨터비전", "061-750-3621"],
        "category": "실험실"
    },
    
    # 보안 관련
    {
        "id": 5,
        "question": "보안 관련 실험실은?",
        "expected_keywords": ["정보보호", "정세훈"],
        "category": "실험실"
    },
    {
        "id": 6,
        "question": "해킹 배우고 싶은데",
        "expected_keywords": ["정보보호", "보안"],
        "category": "실험실"
    },
    
    # VR/AR
    {
        "id": 7,
        "question": "VR 연구하는 곳 있어?",
        "expected_keywords": ["실감", "신광성"],
        "category": "실험실"
    },
    {
        "id": 8,
        "question": "메타버스 공부하고 싶어",
        "expected_keywords": ["실감", "멀티미디어"],
        "category": "실험실"
    },
    
    # 블록체인
    {
        "id": 9,
        "question": "블록체인 실험실 어디야?",
        "expected_keywords": ["소프트웨어공학", "정보보호"],
        "category": "실험실"
    },
    
    # 교수님별
    {
        "id": 10,
        "question": "김종찬 교수님 실험실 연락처",
        "expected_keywords": ["061-750-3621", "컴퓨터비전"],
        "category": "실험실"
    },
    {
        "id": 11,
        "question": "정세훈 교수님 이메일",
        "expected_keywords": ["shjung@scnu.ac.kr"],
        "category": "실험실"
    },
    {
        "id": 12,
        "question": "신광성 교수님 전화번호",
        "expected_keywords": ["061-750-3623"],
        "category": "실험실"
    },
    
    # 인턴 지원
    {
        "id": 13,
        "question": "실험실 인턴 어떻게 지원해?",
        "expected_keywords": ["이메일", "전화", "면담"],
        "category": "실험실"
    },
    {
        "id": 14,
        "question": "학부생도 실험실 들어갈 수 있어?",
        "expected_keywords": ["인턴", "지원"],
        "category": "실험실"
    },
    
    # 빅데이터
    {
        "id": 15,
        "question": "빅데이터 실험실 있어?",
        "expected_keywords": ["소프트웨어공학", "정보보호"],
        "category": "실험실"
    },
]


def test_laboratories(test_cases):
    """실험실 테스트 실행"""
    print("=" * 70)
    print("🔬 실험실 카테고리 정확도 테스트")
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


def save_results(results, filename="laboratory_test_results.txt"):
    """결과 저장"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("실험실 카테고리 테스트 결과\n")
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
    print(f"\n🔬 실험실 카테고리 테스트")
    print(f"테스트 케이스: {len(LABORATORY_TESTS)}개\n")
    
    results = test_laboratories(LABORATORY_TESTS)
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