"""
OpenAI API 직접 테스트 스크립트
"""
import sys
import os
import json
import requests

# 프로젝트 루트 추가
sys.path.append(os.path.join(os.path.dirname(__file__), "blog-auto"))

try:
    from src.foundation.config import config_manager

    print("=== OpenAI API 직접 테스트 ===")
    api_config = config_manager.load_api_config()

    if not api_config.openai_api_key:
        print("OpenAI API 키가 설정되지 않았습니다.")
        exit(1)

    headers = {
        'Authorization': f'Bearer {api_config.openai_api_key}',
        'Content-Type': 'application/json'
    }

    # 1. 모델 리스트 조회 테스트
    print("\n1. 모델 리스트 조회 테스트...")
    try:
        response = requests.get('https://api.openai.com/v1/models', headers=headers, timeout=30)
        print(f"모델 리스트 조회 상태 코드: {response.status_code}")

        if response.status_code == 200:
            models = response.json()
            gpt5_models = [m for m in models['data'] if 'gpt-5' in m['id']]
            print(f"GPT-5 시리즈 모델 수: {len(gpt5_models)}")
            for model in gpt5_models:
                print(f"  - {model['id']}")
        else:
            print(f"모델 리스트 조회 실패: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"모델 리스트 조회 오류: {e}")

    # 2. Chat Completions API 테스트 - gpt-5-nano
    print("\n2. Chat Completions API 테스트 - gpt-5-nano...")
    payload = {
        "model": "gpt-5-nano",
        "messages": [
            {"role": "user", "content": "안녕하세요! 간단한 인사말을 해주세요."}
        ],
        "max_tokens": 100,
        "temperature": 0.7
    }

    try:
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=30
        )
        print(f"Chat Completions 상태 코드: {response.status_code}")
        print(f"응답 내용: {response.text[:500]}...")

        if response.status_code != 200:
            try:
                error_data = response.json()
                print(f"에러 상세: {error_data}")
            except:
                print("JSON 파싱 실패")
    except Exception as e:
        print(f"Chat Completions 오류: {e}")

    # 3. 대체 모델로 테스트 - gpt-4o (실제 존재하는 모델)
    print("\n3. 대체 모델 테스트 - gpt-4o...")
    payload_alt = {
        "model": "gpt-4o",
        "messages": [
            {"role": "user", "content": "안녕하세요! 간단한 인사말을 해주세요."}
        ],
        "max_tokens": 100,
        "temperature": 0.7
    }

    try:
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=payload_alt,
            timeout=30
        )
        print(f"대체 모델 상태 코드: {response.status_code}")
        print(f"대체 모델 응답: {response.text[:300]}...")
    except Exception as e:
        print(f"대체 모델 테스트 오류: {e}")

except Exception as e:
    print(f"전체 오류 발생: {e}")
    import traceback
    traceback.print_exc()