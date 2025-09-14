"""
OpenAI 텍스트 클라이언트 페이로드 디버깅
"""
import sys
import os
import json

# 프로젝트 루트 추가
sys.path.append(os.path.join(os.path.dirname(__file__), "blog-auto"))

try:
    from src.vendors.openai.text_client import OpenAITextClient

    print("=== OpenAI 텍스트 클라이언트 페이로드 디버깅 ===")

    # 클라이언트 초기화
    client = OpenAITextClient()

    # 테스트용 메시지
    test_messages = [
        {"role": "user", "content": "안녕하세요! 간단한 인사말을 해주세요."}
    ]

    # generate_text 함수의 내부 로직을 직접 실행해서 페이로드 확인
    model = "gpt-5-nano"
    temperature = 0.7
    max_tokens = 100

    print(f"모델: {model}")
    print(f"온도: {temperature}")
    print(f"최대 토큰: {max_tokens}")

    # 페이로드 구성 로직 재현
    payload = {
        "model": model,
        "messages": test_messages,
        "parallel_tool_calls": True
    }

    # GPT-5 시리즈는 max_completion_tokens 사용, 다른 모델은 max_tokens 사용
    if model.startswith("gpt-5"):
        payload["max_completion_tokens"] = max_tokens
        # GPT-5-nano는 temperature=1만 지원
        if model == "gpt-5-nano":
            payload["temperature"] = 1.0
        else:
            payload["temperature"] = temperature
    else:
        payload["max_tokens"] = max_tokens
        payload["temperature"] = temperature

    print("\n생성된 페이로드:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    # 헤더 확인
    headers = client._get_headers()
    print(f"\n헤더 키 개수: {len(headers)}")
    print("헤더 키들:", list(headers.keys()))

except Exception as e:
    print(f"오류 발생: {e}")
    import traceback
    traceback.print_exc()