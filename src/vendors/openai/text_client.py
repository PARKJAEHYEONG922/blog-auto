"""
OpenAI 텍스트 생성 API 클라이언트
GPT-4o, GPT-4o-mini, GPT-4-turbo 등 모든 OpenAI 텍스트 모델 지원
"""
from typing import Dict, Any, List, Optional
import json

from src.foundation.http_client import default_http_client, rate_limiter_manager
from src.foundation.config import config_manager
from src.foundation.exceptions import OpenAIError, handle_api_exception
from src.foundation.logging import get_logger

logger = get_logger("vendors.openai.text")

# 지원하는 OpenAI 모델들
SUPPORTED_MODELS = {
    "gpt-4o": {
        "name": "GPT-4o",
        "description": "최신 GPT-4 옴니 모델 (높은 품질, 비교적 빠름)",
        "max_tokens": 128000,
        "context_window": 128000
    },
    "gpt-4o-mini": {
        "name": "GPT-4o Mini", 
        "description": "경제적인 GPT-4o 모델 (빠르고 저렴)",
        "max_tokens": 16384,
        "context_window": 128000
    },
    "gpt-4-turbo": {
        "name": "GPT-4 Turbo",
        "description": "향상된 GPT-4 모델 (높은 품질)",
        "max_tokens": 4096,
        "context_window": 128000
    },
    "gpt-4": {
        "name": "GPT-4",
        "description": "기본 GPT-4 모델 (높은 품질, 느림)",
        "max_tokens": 8192,
        "context_window": 8192
    },
    "gpt-3.5-turbo": {
        "name": "GPT-3.5 Turbo",
        "description": "경제적이고 빠른 모델",
        "max_tokens": 4096,
        "context_window": 16385
    }
}


class OpenAITextClient:
    """OpenAI 텍스트 생성 API 클라이언트"""
    
    def __init__(self):
        self.base_url = "https://api.openai.com/v1"
        self.rate_limiter = rate_limiter_manager.get_limiter("openai_text", 0.5)  # 2초당 1회
    
    def _get_headers(self) -> Dict[str, str]:
        """API 호출용 헤더 생성"""
        api_config = config_manager.load_api_config()
        return {
            'Authorization': f'Bearer {api_config.openai_api_key}',
            'Content-Type': 'application/json'
        }
    
    def _check_config(self) -> bool:
        """API 설정 확인"""
        api_config = config_manager.load_api_config()
        return bool(api_config.openai_api_key)
    
    def get_supported_models(self) -> Dict[str, Dict]:
        """지원하는 모델 목록 반환"""
        return SUPPORTED_MODELS
    
    def get_model_info(self, model: str) -> Optional[Dict]:
        """특정 모델 정보 반환"""
        return SUPPORTED_MODELS.get(model)
    
    @handle_api_exception
    def generate_text(self,
                     messages: List[Dict[str, str]],
                     model: str = "gpt-4o",
                     temperature: float = 0.7,
                     max_tokens: Optional[int] = None) -> str:
        """
        텍스트 생성
        
        Args:
            messages: 메시지 목록
            model: 사용할 OpenAI 모델
            temperature: 온도 설정
            max_tokens: 최대 토큰 수 (None이면 모델 기본값 사용)
        
        Returns:
            str: 생성된 텍스트
        """
        if not self._check_config():
            raise OpenAIError("OpenAI API 키가 설정되지 않았습니다")
        
        # 모델 지원 여부 확인
        if model not in SUPPORTED_MODELS:
            raise OpenAIError(f"지원하지 않는 모델입니다: {model}")
        
        # 모델별 기본 max_tokens 설정 (출력용)
        if max_tokens is None:
            # 충분한 길이의 블로그 글을 위해 (3,000~4,000자)
            max_tokens = 2,000
        
        # 속도 제한 적용
        self.rate_limiter.wait()
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        headers = self._get_headers()
        url = f"{self.base_url}/chat/completions"
        
        logger.info(f"OpenAI 텍스트 생성 API 호출: {model} (max_tokens: {max_tokens})")
        
        try:
            response = default_http_client.post(url, headers=headers, json=payload)
            data = response.json()
            
            if 'error' in data:
                raise OpenAIError(f"API 에러: {data['error'].get('message', 'Unknown error')}")
            
            if 'choices' in data and len(data['choices']) > 0:
                generated_text = data['choices'][0]['message']['content']
                logger.info(f"OpenAI 텍스트 생성 완료: {len(generated_text)}자")
                return generated_text
            else:
                raise OpenAIError("API 응답에 생성된 텍스트가 없습니다")
            
        except json.JSONDecodeError as e:
            raise OpenAIError(f"API 응답 파싱 실패: {e}")
        except Exception as e:
            logger.error(f"OpenAI 텍스트 생성 API 호출 실패: {e}")
            raise OpenAIError(f"API 호출 실패: {e}")


# 전역 클라이언트 인스턴스
openai_text_client = OpenAITextClient()