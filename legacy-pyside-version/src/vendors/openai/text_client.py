"""
OpenAI 텍스트 생성 API 클라이언트
GPT-5, GPT-5-mini, GPT-4o, GPT-4o-mini 등 모든 OpenAI 텍스트 모델 지원
Latest Chat Completions API (2025) with new parameters
"""
from typing import Dict, Any, List, Optional, Union
import json

from src.foundation.http_client import default_http_client, rate_limiter_manager
from src.foundation.config import config_manager
from src.foundation.exceptions import OpenAIError, handle_api_exception
from src.foundation.logging import get_logger

logger = get_logger("vendors.openai.text")

# 중앙화된 AI 모델 시스템에서 동적으로 로드
def get_supported_models():
    """중앙 관리되는 OpenAI 모델 정보를 동적으로 가져오기"""
    from src.foundation.ai_models import AIModelRegistry, AIProvider

    supported_models = {}
    openai_text_models = AIModelRegistry.get_text_models_by_provider(AIProvider.OPENAI)

    for model in openai_text_models:
        supported_models[model.id] = {
            "name": model.display_name,
            "description": model.description,
            "max_tokens": model.max_tokens,
            "context_window": model.context_window
        }

    return supported_models

# 동적으로 지원 모델 로드
SUPPORTED_MODELS = get_supported_models()


class OpenAITextClient:
    """OpenAI 텍스트 생성 API 클라이언트 - Latest Chat Completions API (2025)"""

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
                     max_tokens: Optional[int] = None,
                     reasoning_effort: Optional[str] = None,
                     verbosity: Optional[str] = None) -> str:
        """
        텍스트 생성 - Latest OpenAI Chat Completions API (2025)

        Args:
            messages: 메시지 목록
            model: 사용할 OpenAI 모델 (gpt-5, gpt-5-mini, gpt-4o 등)
            temperature: 온도 설정 (0.0-2.0)
            max_tokens: 최대 토큰 수 (None이면 모델 기본값 사용)
            reasoning_effort: GPT-5 시리즈 추론 노력 수준 ("minimal", "low", "medium", "high")
            verbosity: GPT-5 시리즈 출력 상세도 (Responses API 전용, Chat Completions에서는 사용하지 않음)

        Returns:
            str: 생성된 텍스트
        """
        if not self._check_config():
            raise OpenAIError("OpenAI API 키가 설정되지 않았습니다")

        # 모델 지원 여부 확인
        if model not in SUPPORTED_MODELS:
            raise OpenAIError(f"지원하지 않는 모델입니다: {model}")

        # 모델별 기본 max_tokens 설정 (2025 업데이트)
        if max_tokens is None:
            if model.startswith("gpt-5"):
                # GPT-5 시리즈는 더 효율적인 토큰 사용
                if model == "gpt-5":
                    max_tokens = 10000  # GPT-5 최대 성능
                elif model == "gpt-5-mini":
                    max_tokens = 8000   # GPT-5-mini 균형
                elif model == "gpt-5-nano":
                    max_tokens = 6000   # GPT-5-nano 효율
                else:
                    max_tokens = 8000   # 기타 GPT-5 variants
            elif model == "gpt-4o":
                max_tokens = 8000  # 긴 블로그 글 생성
            elif model == "gpt-4o-mini":
                max_tokens = 6000  # 충분한 길이 지원
            elif model == "gpt-4-turbo":
                max_tokens = 4000
            else:
                max_tokens = 3000

        # 속도 제한 적용
        self.rate_limiter.wait()

        # API 페이로드 구성 (Chat Completions API 호환)
        payload = {
            "model": model,
            "messages": messages
        }
        # NOTE: tools를 실제로 쓰는 별도 메서드에서만 parallel_tool_calls를 붙이세요.

        # GPT-5 시리즈는 max_completion_tokens 사용, 다른 모델은 max_tokens 사용
        if model.startswith("gpt-5"):
            payload["max_completion_tokens"] = max_tokens
            # GPT-5 시리즈는 temperature 파라미터를 보내지 않음 (기본값 1.0 사용)
            # Chat Completions에서는 reasoning 객체로 전달
            if reasoning_effort:
                payload["reasoning"] = {"effort": reasoning_effort}  # "minimal"|"low"|"medium"|"high"
            # NOTE: verbosity는 Responses API 측 기능 리포트가 있어
            # Chat Completions에 넣으면 400(Unknown parameter)이 날 수 있어 제거합니다.
        else:
            payload["max_tokens"] = max_tokens
            payload["temperature"] = temperature

        headers = self._get_headers()
        url = f"{self.base_url}/chat/completions"

        logger.info(f"OpenAI 텍스트 생성 API 호출: {model} (max_tokens: {max_tokens})")
        logger.info(f"OpenAI API 페이로드 상세: model={model}, max_tokens={max_tokens}, temperature={temperature}")

        try:
            response = default_http_client.post(url, headers=headers, json=payload)
            
            # HTTP 상태 코드 체크 (사용자 친화적 오류 메시지)
            if response.status_code != 200:
                from src.foundation.exceptions import ExceptionMapper
                user_friendly_error = ExceptionMapper.get_user_friendly_message(
                    response.status_code, 
                    f"OpenAI API Error: {response.text}"
                )
                raise OpenAIError(user_friendly_error)
            
            data = response.json()

            if 'error' in data:
                error_msg = data['error'].get('message', 'Unknown error')
                error_type = data['error'].get('type', 'unknown_error')
                logger.error(f"OpenAI API 에러 [{error_type}]: {error_msg}")
                
                # OpenAI 특정 오류도 사용자 친화적으로 변환
                user_friendly_error = f"🤖 OpenAI 오류\n{error_msg}\n잠시 후 다시 시도해주세요."
                raise OpenAIError(user_friendly_error)

            if 'choices' in data and len(data['choices']) > 0:
                choice = data['choices'][0]
                generated_text = choice['message']['content']
                finish_reason = choice.get('finish_reason', 'unknown')

                # 사용량 정보 로깅 (2025 업데이트)
                usage = data.get('usage', {})
                prompt_tokens = usage.get('prompt_tokens', 0)
                completion_tokens = usage.get('completion_tokens', 0)
                total_tokens = usage.get('total_tokens', 0)

                logger.info(f"OpenAI 텍스트 생성 완료: {len(generated_text)}자, finish_reason: {finish_reason}")
                logger.info(f"토큰 사용량 - prompt: {prompt_tokens}, completion: {completion_tokens}, total: {total_tokens}")

                # finish_reason 분석 로깅 (2025 업데이트)
                if finish_reason == 'length':
                    logger.warning(f"OpenAI 응답이 max_tokens({max_tokens}) 제한으로 잘렸습니다. 더 긴 글을 원한다면 max_tokens를 늘려주세요.")
                elif finish_reason == 'content_filter':
                    logger.warning("OpenAI 콘텐츠 필터로 인해 생성이 중단되었습니다.")
                elif finish_reason == 'stop':
                    logger.info("OpenAI 응답이 자연스럽게 완료되었습니다.")
                elif finish_reason == 'tool_calls':
                    logger.info("OpenAI가 도구 호출로 응답을 완료했습니다.")

                return generated_text
            else:
                raise OpenAIError("🤖 OpenAI가 텍스트를 생성하지 못했습니다.\n잠시 후 다시 시도해주세요.")

        except json.JSONDecodeError as e:
            logger.error(f"OpenAI API 응답 파싱 실패: {e}")
            raise OpenAIError(f"🤖 OpenAI 응답 처리 중 오류가 발생했습니다.\n잠시 후 다시 시도해주세요.\n기술적 세부사항: {e}")
        except OpenAIError:
            # 이미 사용자 친화적 메시지인 경우 그대로 전파
            raise
        except Exception as e:
            logger.error(f"OpenAI 텍스트 생성 API 호출 실패: {e}")
            raise OpenAIError(f"🤖 OpenAI 연결 중 문제가 발생했습니다.\n네트워크를 확인하고 잠시 후 다시 시도해주세요.\n기술적 세부사항: {e}")


# 전역 클라이언트 인스턴스
openai_text_client = OpenAITextClient()