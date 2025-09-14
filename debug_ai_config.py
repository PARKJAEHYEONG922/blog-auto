"""
디버깅용 스크립트 - AI 설정 상태 확인
"""
import sys
import os
import json

# 프로젝트 루트 추가
sys.path.append(os.path.join(os.path.dirname(__file__), "blog-auto"))

try:
    from src.foundation.config import config_manager
    from src.foundation.ai_models import AIModelRegistry

    print("=== API 설정 확인 ===")
    api_config = config_manager.load_api_config()

    print(f"정보요약 AI 제공자: {api_config.current_summary_ai_provider}")
    print(f"정보요약 AI 모델: {api_config.current_summary_ai_model}")
    print(f"OpenAI API 키 상태: {'설정됨' if api_config.openai_api_key and api_config.openai_api_key.strip() else '미설정'}")

    if api_config.openai_api_key:
        print(f"OpenAI API 키 길이: {len(api_config.openai_api_key)} 문자")
        print(f"OpenAI API 키 시작: {api_config.openai_api_key[:10]}...")

    print("\n=== 모델 매핑 확인 ===")
    mapping = AIModelRegistry.get_model_mapping_for_service()

    print("전체 모델 매핑:")
    for ui_name, tech_name in mapping.items():
        print(f"  '{ui_name}' -> '{tech_name}'")

    if api_config.current_summary_ai_model:
        technical_model = mapping.get(api_config.current_summary_ai_model, api_config.current_summary_ai_model)
        print(f"\n현재 정보요약 AI 모델 매핑:")
        print(f"  '{api_config.current_summary_ai_model}' -> '{technical_model}'")

    print("\n=== OpenAI 지원 모델 확인 ===")
    from src.foundation.ai_models import AIProvider
    openai_models = AIModelRegistry.get_text_models_by_provider(AIProvider.OPENAI)
    print(f"등록된 OpenAI 텍스트 모델 수: {len(openai_models)}")
    for model in openai_models:
        print(f"  {model.display_name} -> {model.id}")

    print("\n=== OpenAI 텍스트 클라이언트 지원 모델 확인 ===")
    from src.vendors.openai.text_client import openai_text_client
    supported_models = openai_text_client.get_supported_models()
    print(f"OpenAI 텍스트 클라이언트 지원 모델 수: {len(supported_models)}")
    for model_id, info in supported_models.items():
        print(f"  {model_id}: {info['name']}")

    print(f"\n'gpt-5-nano' 지원 여부: {'지원됨' if 'gpt-5-nano' in supported_models else '지원안됨'}")

except Exception as e:
    print(f"오류 발생: {e}")
    import traceback
    traceback.print_exc()