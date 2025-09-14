"""
Claude API 연결 테스트
"""
import sys
import os
import json
import requests

# 프로젝트 루트 추가
sys.path.append(os.path.join(os.path.dirname(__file__), "blog-auto"))

try:
    from src.vendors.anthropic.text_client import claude_text_client
    from src.foundation.config import config_manager

    print("=== Claude API 연결 테스트 ===")

    # API 키 확인
    api_config = config_manager.load_api_config()
    if not api_config.claude_api_key:
        print("Claude API 키가 설정되지 않았습니다")
        exit(1)

    print(f"Claude API 키 설정됨 (길이: {len(api_config.claude_api_key)})")

    # 간단한 메시지로 테스트
    test_messages = [
        {"role": "user", "content": "안녕하세요! 간단한 인사말 하나만 해주세요."}
    ]

    print("Claude Sonnet 4 모델로 텍스트 생성 테스트 중...")

    try:
        response = claude_text_client.generate_text(
            messages=test_messages,
            model="claude-sonnet-4-20250514",
            temperature=0.7,
            max_tokens=100
        )
        print(f"성공! 응답 길이: {len(response) if response else 0} 문자")
        if response:
            print(f"첫 50자: {response[:50]}...")

    except Exception as e:
        print(f"실패: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

    print("\n=== 제목 추천 테스트 ===")
    title_prompt = """다음 키워드에 대한 블로그 제목을 5개 추천해주세요:

메인키워드: 파이썬 프로그래밍

요구사항:
1. 검색에 유리한 제목
2. 클릭하고 싶은 제목
3. 실용적인 내용을 담은 제목

JSON 형식으로 응답해주세요:
{"titles": ["제목1", "제목2", "제목3", "제목4", "제목5"]}"""

    title_messages = [{"role": "user", "content": title_prompt}]

    try:
        response = claude_text_client.generate_text(
            messages=title_messages,
            model="claude-sonnet-4-20250514",
            temperature=0.7,
            max_tokens=300
        )
        print(f"제목 추천 성공!")
        print(f"응답: {response}")

        # JSON 파싱 테스트
        import json
        try:
            # 마크다운 코드 블록 제거
            cleaned_response = response.strip()
            if cleaned_response.startswith('```'):
                lines = cleaned_response.split('\n')
                if len(lines) > 2 and lines[0].startswith('```') and lines[-1].strip() == '```':
                    cleaned_response = '\n'.join(lines[1:-1])

            titles_data = json.loads(cleaned_response)
            print(f"JSON 파싱 성공! 제목 수: {len(titles_data.get('titles', []))}")
            for i, title in enumerate(titles_data.get('titles', []), 1):
                print(f"  {i}. {title}")
        except json.JSONDecodeError as je:
            print(f"JSON 파싱 실패: {je}")

    except Exception as e:
        print(f"제목 추천 실패: {e}")

except Exception as e:
    print(f"전체 오류 발생: {e}")
    import traceback
    traceback.print_exc()