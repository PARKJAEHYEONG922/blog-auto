"""
OpenAI API 페이로드 디버깅
"""
import sys
import os
import json
import requests

# 프로젝트 루트 추가
sys.path.append(os.path.join(os.path.dirname(__file__), "blog-auto"))

from src.foundation.config import config_manager

def test_simple_request():
    """가장 간단한 OpenAI API 요청으로 테스트"""
    print("=== OpenAI API 직접 테스트 ===")

    # API 키 확인
    api_config = config_manager.load_api_config()
    if not api_config.openai_api_key:
        print("OpenAI API 키가 설정되지 않았습니다")
        return

    print(f"API 키 설정됨 (길이: {len(api_config.openai_api_key)})")

    # 가장 기본적인 페이로드
    payload = {
        "model": "gpt-3.5-turbo",  # 안전한 모델로 테스트
        "messages": [
            {"role": "user", "content": "Hello"}
        ],
        "max_tokens": 50,
        "temperature": 0.7
    }

    headers = {
        'Authorization': f'Bearer {api_config.openai_api_key}',
        'Content-Type': 'application/json'
    }

    url = "https://api.openai.com/v1/chat/completions"

    print(f"요청 URL: {url}")
    print(f"페이로드: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"응답 상태코드: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"성공! 응답: {result['choices'][0]['message']['content']}")
        else:
            error_data = response.json()
            print(f"실패! 오류 응답:")
            print(json.dumps(error_data, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"요청 실패: {e}")

def test_gpt4o_model():
    """GPT-4o 모델 테스트"""
    print("\n=== GPT-4o 모델 테스트 ===")

    api_config = config_manager.load_api_config()

    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "user", "content": "Hello"}
        ],
        "max_tokens": 50,
        "temperature": 0.7
    }

    headers = {
        'Authorization': f'Bearer {api_config.openai_api_key}',
        'Content-Type': 'application/json'
    }

    url = "https://api.openai.com/v1/chat/completions"

    print(f"페이로드: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"응답 상태코드: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"GPT-4o 성공! 응답: {result['choices'][0]['message']['content']}")
        else:
            error_data = response.json()
            print(f"GPT-4o 실패! 오류 응답:")
            print(json.dumps(error_data, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"GPT-4o 요청 실패: {e}")

def test_gpt5_nano_model():
    """GPT-5-nano 모델 테스트"""
    print("\n=== GPT-5-nano 모델 테스트 ===")

    api_config = config_manager.load_api_config()

    payload = {
        "model": "gpt-5-nano",
        "messages": [
            {"role": "user", "content": "Hello"}
        ],
        "max_completion_tokens": 50,
        "temperature": 1.0  # GPT-5-nano는 1.0만 지원
    }

    headers = {
        'Authorization': f'Bearer {api_config.openai_api_key}',
        'Content-Type': 'application/json'
    }

    url = "https://api.openai.com/v1/chat/completions"

    print(f"페이로드: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"응답 상태코드: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"GPT-5-nano 성공! 응답: {result['choices'][0]['message']['content']}")
        else:
            error_data = response.json()
            print(f"GPT-5-nano 실패! 오류 응답:")
            print(json.dumps(error_data, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"GPT-5-nano 요청 실패: {e}")

if __name__ == "__main__":
    test_simple_request()
    test_gpt4o_model()
    test_gpt5_nano_model()