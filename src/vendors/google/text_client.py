"""
Google Gemini 텍스트 생성 API 클라이언트
Gemini 1.5 Pro, Gemini 1.5 Flash 등 지원
"""
from typing import Dict, Any, List, Optional
import json

from src.foundation.http_client import default_http_client, rate_limiter_manager
from src.foundation.config import config_manager
from src.foundation.exceptions import BusinessError, handle_api_exception
from src.foundation.logging import get_logger

logger = get_logger("vendors.google.text")

# 지원하는 Gemini 모델들
SUPPORTED_MODELS = {
    "gemini-2.0-flash-exp": {
        "name": "Gemini 2.0 Flash (Experimental)",
        "description": "최신 Gemini 2.0 Flash 모델 (무료, 실험적)",
        "max_tokens": 8192,
        "context_window": 1000000
    },
    "gemini-1.5-pro-latest": {
        "name": "Gemini 1.5 Pro",
        "description": "최고 품질의 Gemini 모델 (긴 컨텍스트 지원)",
        "max_tokens": 8192,
        "context_window": 2000000
    },
    "gemini-1.5-flash-latest": {
        "name": "Gemini 1.5 Flash", 
        "description": "빠르고 효율적인 Gemini 모델",
        "max_tokens": 8192,
        "context_window": 1000000
    },
    "gemini-pro": {
        "name": "Gemini Pro",
        "description": "기본 Gemini Pro 모델",
        "max_tokens": 8192,
        "context_window": 32768
    }
}


class GeminiTextClient:
    """Google Gemini 텍스트 생성 API 클라이언트"""
    
    def __init__(self):
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.rate_limiter = rate_limiter_manager.get_limiter("gemini_text", 1.0)  # 1초당 1회
    
    def _check_config(self) -> bool:
        """API 설정 확인"""
        api_config = config_manager.load_api_config()
        return bool(api_config.gemini_api_key)
    
    def get_supported_models(self) -> Dict[str, Dict]:
        """지원하는 모델 목록 반환"""
        return SUPPORTED_MODELS
    
    def get_model_info(self, model: str) -> Optional[Dict]:
        """특정 모델 정보 반환"""
        return SUPPORTED_MODELS.get(model)
    
    def _convert_messages_to_gemini_format(self, messages: List[Dict[str, str]]) -> str:
        """메시지 목록을 Gemini 형식으로 변환"""
        text_content = ""
        for message in messages:
            if message['role'] == 'system':
                text_content += f"System: {message['content']}\\n\\n"
            elif message['role'] == 'user':
                text_content += f"User: {message['content']}"
        return text_content
    
    @handle_api_exception
    def generate_text(self,
                     messages: List[Dict[str, str]],
                     model: str = "gemini-2.0-flash-exp",
                     temperature: float = 0.7,
                     max_tokens: Optional[int] = None) -> str:
        """
        텍스트 생성
        
        Args:
            messages: 메시지 목록
            model: 사용할 Gemini 모델
            temperature: 온도 설정
            max_tokens: 최대 토큰 수
        
        Returns:
            str: 생성된 텍스트
        """
        if not self._check_config():
            raise BusinessError("Google Gemini API 키가 설정되지 않았습니다")
        
        # 모델 지원 여부 확인
        if model not in SUPPORTED_MODELS:
            raise BusinessError(f"지원하지 않는 모델입니다: {model}")
        
        # 모델별 기본 max_tokens 설정 (출력용 - 무료 티어 최대 활용)
        if max_tokens is None:
            model_info = SUPPORTED_MODELS[model]
            # Gemini는 무료이므로 모델 최대값 사용
            max_tokens = model_info["max_tokens"]
        
        # 속도 제한 적용
        self.rate_limiter.wait()
        
        # API 키 가져오기
        api_config = config_manager.load_api_config()
        api_key = api_config.gemini_api_key
        
        # 메시지를 Gemini 형식으로 변환
        text_content = self._convert_messages_to_gemini_format(messages)
        
        url = f"{self.base_url}/{model}:generateContent?key={api_key}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "contents": [{
                "parts": [{
                    "text": text_content
                }]
            }],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature
            }
        }
        
        logger.info(f"Gemini 텍스트 생성 API 호출: {model} (max_tokens: {max_tokens})")
        
        try:
            response = default_http_client.post(url, headers=headers, json=data)
            result = response.json()
            
            if 'error' in result:
                raise BusinessError(f"Gemini API 에러: {result['error'].get('message', 'Unknown error')}")
            
            if 'candidates' in result and len(result['candidates']) > 0:
                content = result['candidates'][0]['content']['parts'][0]['text']
                logger.info(f"Gemini 텍스트 생성 완료: {len(content)}자")
                return content
            else:
                raise BusinessError("Gemini API 응답이 예상과 다릅니다")
            
        except json.JSONDecodeError as e:
            raise BusinessError(f"API 응답 파싱 실패: {e}")
        except Exception as e:
            logger.error(f"Gemini 텍스트 생성 API 호출 실패: {e}")
            raise BusinessError(f"API 호출 실패: {e}")


# 전역 클라이언트 인스턴스
gemini_text_client = GeminiTextClient()