"""
Raw OpenAI API 테스트 - max_completion_tokens 사용
"""
import requests
import json
import sys
import os

# 프로젝트 루트 추가
sys.path.append(os.path.join(os.path.dirname(__file__), "blog-auto"))

try:
    from src.foundation.config import config_manager

    print("=== Raw OpenAI API 테스트 - max_completion_tokens ===")
    api_config = config_manager.load_api_config()

    headers = {
        'Authorization': f'Bearer {api_config.openai_api_key}',
        'Content-Type': 'application/json'
    }

    # GPT-5 nano with max_completion_tokens, temperature=1, and parallel_tool_calls
    payload = {
        "model": "gpt-5-nano",
        "messages": [
            {"role": "user", "content": "안녕하세요! 간단한 인사말을 해주세요."}
        ],
        "max_completion_tokens": 100,
        "temperature": 1.0,
        "parallel_tool_calls": True
    }

    print("요청 페이로드:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    try:
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=30
        )
        print(f"\n상태 코드: {response.status_code}")

        if response.status_code == 200:
            print("성공!")
            data = response.json()
            print("응답:", data['choices'][0]['message']['content'])
        else:
            print("실패!")
            print("응답 내용:")
            print(response.text)

            # JSON 파싱 시도
            try:
                error_data = response.json()
                print("\n파싱된 에러:")
                print(json.dumps(error_data, indent=2, ensure_ascii=False))
            except:
                print("JSON 파싱 실패")

    except Exception as e:
        print(f"요청 오류: {e}")

except Exception as e:
    print(f"전체 오류: {e}")
    import traceback
    traceback.print_exc()