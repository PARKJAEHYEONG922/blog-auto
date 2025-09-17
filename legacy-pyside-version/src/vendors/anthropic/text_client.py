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

# 중앙화된 AI 모델 시스템에서 동적으로 로드
def get_supported_models():
    """중앙 관리되는 Claude 모델 정보를 동적으로 가져오기"""
    from src.foundation.ai_models import AIModelRegistry, AIProvider

    supported_models = {}
    claude_models = AIModelRegistry.get_models_by_provider(AIProvider.ANTHROPIC)

    for model in claude_models:
        supported_models[model.id] = {
            "name": model.display_name,
            "description": model.description,
            "max_tokens": model.max_tokens,
            "context_window": model.context_window
        }

    return supported_models

# 동적으로 지원 모델 로드
SUPPORTED_MODELS = get_supported_models()


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
                     model: str = None,
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

        # 기본 모델 설정 (중앙에서 가져오기)
        if model is None:
            from src.foundation.ai_models import AIModelRegistry, AIProvider
            default_model = AIModelRegistry.get_default_model(AIProvider.ANTHROPIC)
            model = default_model.id if default_model else list(SUPPORTED_MODELS.keys())[0]

        # 모델 지원 여부 확인
        if model not in SUPPORTED_MODELS:
            raise ClaudeAPIError(f"지원하지 않는 모델입니다: {model}")
        
        # 모델별 기본 max_tokens 설정 (출력용)
        if max_tokens is None:
            model_info = SUPPORTED_MODELS.get(model, {})
            # 모든 Claude 모델에서 충분히 긴 블로그 글 생성을 위해 더 큰 토큰 수 사용
            max_tokens = 6000  # 약 4,500-6,000자 블로그 글 생성 가능
        
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
            
            # HTTP 상태 코드 체크 (사용자 친화적 오류 메시지)
            if response.status_code != 200:
                from src.foundation.exceptions import ExceptionMapper
                user_friendly_error = ExceptionMapper.get_user_friendly_message(
                    response.status_code, 
                    f"Claude API Error: {response.text}"
                )
                raise ClaudeAPIError(user_friendly_error)
            
            data = response.json()
            
            if 'error' in data:
                error_message = data['error'].get('message', 'Unknown error')
                # Claude 특정 오류도 사용자 친화적으로 변환
                user_friendly_error = f"🤖 Claude AI 오류\n{error_message}\n잠시 후 다시 시도해주세요."
                raise ClaudeAPIError(user_friendly_error)
            
            if 'content' in data and len(data['content']) > 0:
                generated_text = data['content'][0]['text']
                logger.info(f"Claude 텍스트 생성 완료: {len(generated_text)}자")
                return generated_text
            else:
                raise ClaudeAPIError("🤖 Claude AI가 텍스트를 생성하지 못했습니다.\n잠시 후 다시 시도해주세요.")
            
        except json.JSONDecodeError as e:
            raise ClaudeAPIError(f"🤖 Claude AI 응답 처리 중 오류가 발생했습니다.\n잠시 후 다시 시도해주세요.\n기술적 세부사항: {e}")
        except ClaudeAPIError:
            # 이미 사용자 친화적 메시지인 경우 그대로 전파
            raise
        except Exception as e:
            logger.error(f"Claude 텍스트 생성 API 호출 실패: {e}")
            # 일반 오류도 사용자 친화적으로 변환
            raise ClaudeAPIError(f"🤖 Claude AI 연결 중 문제가 발생했습니다.\n네트워크를 확인하고 잠시 후 다시 시도해주세요.\n기술적 세부사항: {e}")


# 전역 클라이언트 인스턴스
claude_text_client = ClaudeTextClient()