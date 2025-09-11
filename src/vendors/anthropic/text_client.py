"""
Anthropic Claude 텍스트 생성 API 클라이언트
Claude 3.5 Sonnet, Claude 3 Haiku, Claude 3 Opus 지원
"""
from typing import Dict, Any, List, Optional
import json

from src.foundation.http_client import default_http_client, rate_limiter_manager
from src.foundation.config import config_manager
from src.foundation.exceptions import ClaudeAPIError, handle_api_exception
from src.foundation.logging import get_logger

logger = get_logger("vendors.anthropic.text")

# 지원하는 Claude 모델들
SUPPORTED_MODELS = {
    "claude-3-5-sonnet-20241022": {
        "name": "Claude 3.5 Sonnet",
        "description": "최신 Claude 3.5 Sonnet 모델 (최고 성능)",
        "max_tokens": 8192,
        "context_window": 200000
    },
    "claude-3-5-haiku-20241022": {
        "name": "Claude 3.5 Haiku",
        "description": "빠르고 경제적인 Claude 3.5 Haiku",
        "max_tokens": 8192,
        "context_window": 200000
    },
    "claude-3-opus-20240229": {
        "name": "Claude 3 Opus",
        "description": "가장 강력한 Claude 3 모델",
        "max_tokens": 4096,
        "context_window": 200000
    },
    "claude-3-sonnet-20240229": {
        "name": "Claude 3 Sonnet",
        "description": "균형잡힌 Claude 3 모델",
        "max_tokens": 4096,
        "context_window": 200000
    },
    "claude-3-haiku-20240307": {
        "name": "Claude 3 Haiku",
        "description": "빠르고 경제적인 Claude 3 모델",
        "max_tokens": 4096,
        "context_window": 200000
    }
}


class ClaudeTextClient:
    """Anthropic Claude 텍스트 생성 API 클라이언트"""
    
    def __init__(self):
        self.base_url = "https://api.anthropic.com/v1"
        self.rate_limiter = rate_limiter_manager.get_limiter("claude_text", 0.2)  # 5초당 1회
    
    def _get_headers(self) -> Dict[str, str]:
        """API 호출용 헤더 생성"""
        api_config = config_manager.load_api_config()
        return {
            'x-api-key': api_config.claude_api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        }
    
    def _check_config(self) -> bool:
        """API 설정 확인"""
        api_config = config_manager.load_api_config()
        return bool(api_config.claude_api_key)
    
    def get_supported_models(self) -> Dict[str, Dict]:
        """지원하는 모델 목록 반환"""
        return SUPPORTED_MODELS
    
    def get_model_info(self, model: str) -> Optional[Dict]:
        """특정 모델 정보 반환"""
        return SUPPORTED_MODELS.get(model)
    
    @handle_api_exception
    def generate_text(self,
                     messages: List[Dict[str, str]],
                     model: str = "claude-3-5-sonnet-20241022",
                     temperature: float = 0.7,
                     max_tokens: Optional[int] = None) -> str:
        """
        텍스트 생성
        
        Args:
            messages: 메시지 목록
            model: 사용할 Claude 모델
            temperature: 온도 설정
            max_tokens: 최대 토큰 수
        
        Returns:
            str: 생성된 텍스트
        """
        if not self._check_config():
            raise ClaudeAPIError("Claude API 키가 설정되지 않았습니다")
        
        # 모델 지원 여부 확인
        if model not in SUPPORTED_MODELS:
            raise ClaudeAPIError(f"지원하지 않는 모델입니다: {model}")
        
        # 모델별 기본 max_tokens 설정 (출력용)
        if max_tokens is None:
            # 충분한 길이의 블로그 글을 위해 (3,000~4,000자)
            max_tokens = 2,000
        
        # 속도 제한 적용
        self.rate_limiter.wait()
        
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages
        }
        
        headers = self._get_headers()
        url = f"{self.base_url}/messages"
        
        logger.info(f"Claude 텍스트 생성 API 호출: {model} (max_tokens: {max_tokens})")
        
        try:
            response = default_http_client.post(url, headers=headers, json=payload)
            data = response.json()
            
            if 'error' in data:
                raise ClaudeAPIError(f"API 에러: {data['error'].get('message', 'Unknown error')}")
            
            if 'content' in data and len(data['content']) > 0:
                generated_text = data['content'][0]['text']
                logger.info(f"Claude 텍스트 생성 완료: {len(generated_text)}자")
                return generated_text
            else:
                raise ClaudeAPIError("API 응답에 생성된 텍스트가 없습니다")
            
        except json.JSONDecodeError as e:
            raise ClaudeAPIError(f"API 응답 파싱 실패: {e}")
        except Exception as e:
            logger.error(f"Claude 텍스트 생성 API 호출 실패: {e}")
            raise ClaudeAPIError(f"API 호출 실패: {e}")


# 전역 클라이언트 인스턴스
claude_text_client = ClaudeTextClient()