"""
OpenAI 이미지 생성 API 클라이언트
DALL-E 3, DALL-E 2 지원
"""
from typing import Dict, Any, List, Optional
import json

from src.foundation.http_client import default_http_client, rate_limiter_manager
from src.foundation.config import config_manager
from src.foundation.exceptions import OpenAIError, handle_api_exception
from src.foundation.logging import get_logger

logger = get_logger("vendors.openai.image")

# 중앙화된 AI 모델 시스템에서 동적으로 로드
def get_supported_models():
    """중앙 관리되는 OpenAI 이미지 모델 정보를 동적으로 가져오기"""
    from src.foundation.ai_models import AIModelRegistry, AIProvider, AIModelType

    supported_models = {}
    openai_image_models = AIModelRegistry.get_models_by_provider_and_type(AIProvider.OPENAI, AIModelType.IMAGE)

    for model in openai_image_models:
        model_info = {
            "name": model.display_name,
            "description": model.description,
            "max_images": 10 if "2" in model.id else 1,  # DALL-E 2는 최대 10개, DALL-E 3는 1개
            "sizes": ["1024x1024", "1792x1024", "1024x1792"] if "3" in model.id else ["256x256", "512x512", "1024x1024"],
            "quality": ["standard", "hd"] if "3" in model.id else ["standard"]
        }
        supported_models[model.id] = model_info

    return supported_models

# 동적으로 지원 모델 로드
SUPPORTED_MODELS = get_supported_models()


class OpenAIImageClient:
    """OpenAI 이미지 생성 API 클라이언트"""
    
    def __init__(self):
        self.base_url = "https://api.openai.com/v1"
        self.rate_limiter = rate_limiter_manager.get_limiter("openai_image", 1.0)  # 1초당 1회
    
    def _get_headers(self) -> Dict[str, str]:
        """API 호출용 헤더 생성"""
        api_config = config_manager.load_api_config()
        return {
            'Authorization': f'Bearer {api_config.dalle_api_key or api_config.openai_api_key}',
            'Content-Type': 'application/json'
        }
    
    def _check_config(self) -> bool:
        """API 설정 확인"""
        api_config = config_manager.load_api_config()
        return bool(api_config.dalle_api_key or api_config.openai_api_key)
    
    def get_supported_models(self) -> Dict[str, Dict]:
        """지원하는 모델 목록 반환"""
        return SUPPORTED_MODELS
    
    def get_model_info(self, model: str) -> Optional[Dict]:
        """특정 모델 정보 반환"""
        return SUPPORTED_MODELS.get(model)
    
    @handle_api_exception
    def generate_images(self,
                       prompt: str,
                       model: str = None,
                       n: int = 1,
                       size: str = "1024x1024",
                       quality: str = "standard") -> List[str]:
        """
        이미지 생성
        
        Args:
            prompt: 이미지 생성 프롬프트
            model: 사용할 DALL-E 모델
            n: 생성할 이미지 수
            size: 이미지 크기
            quality: 이미지 품질 (standard, hd)
        
        Returns:
            List[str]: 생성된 이미지 URL 목록
        """
        if not self._check_config():
            raise OpenAIError("OpenAI API 키 또는 DALL-E API 키가 설정되지 않았습니다")

        # 기본 모델 설정 (중앙에서 가져오기)
        if model is None:
            from src.foundation.ai_models import AIModelRegistry, AIProvider, AIModelType
            default_model = AIModelRegistry.get_default_model_by_type(AIProvider.OPENAI, AIModelType.IMAGE)
            model = default_model.id if default_model else "dall-e-3"

        # 모델 지원 여부 확인
        if model not in SUPPORTED_MODELS:
            raise OpenAIError(f"지원하지 않는 모델입니다: {model}")
        
        model_info = SUPPORTED_MODELS[model]
        
        # 모델별 제한 확인
        if n > model_info["max_images"]:
            logger.warning(f"{model}는 최대 {model_info['max_images']}개 이미지만 생성 가능합니다. {model_info['max_images']}개로 제한합니다.")
            n = model_info["max_images"]
        
        if size not in model_info["sizes"]:
            logger.warning(f"{model}에서 지원하지 않는 크기입니다: {size}. 기본값 {model_info['sizes'][0]}을 사용합니다.")
            size = model_info["sizes"][0]
        
        if quality not in model_info["quality"]:
            quality = "standard"
        
        # 속도 제한 적용
        self.rate_limiter.wait()
        
        payload = {
            "model": model,
            "prompt": prompt,
            "n": n,
            "size": size
        }
        
        # DALL-E 3만 quality 지원
        if model == "dall-e-3":
            payload["quality"] = quality
        
        headers = self._get_headers()
        url = f"{self.base_url}/images/generations"
        
        logger.info(f"OpenAI 이미지 생성 API 호출: {model} ({n}개, {size}, {quality})")
        
        try:
            response = default_http_client.post(url, headers=headers, json=payload)
            data = response.json()
            
            if 'error' in data:
                raise OpenAIError(f"API 에러: {data['error'].get('message', 'Unknown error')}")
            
            if 'data' in data and len(data['data']) > 0:
                image_urls = [item['url'] for item in data['data']]
                logger.info(f"OpenAI 이미지 생성 완료: {len(image_urls)}개")
                return image_urls
            else:
                raise OpenAIError("API 응답에 생성된 이미지가 없습니다")
            
        except json.JSONDecodeError as e:
            raise OpenAIError(f"API 응답 파싱 실패: {e}")
        except Exception as e:
            logger.error(f"OpenAI 이미지 생성 API 호출 실패: {e}")
            raise OpenAIError(f"API 호출 실패: {e}")


# 전역 클라이언트 인스턴스
openai_image_client = OpenAIImageClient()