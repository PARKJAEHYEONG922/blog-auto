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

# 지원하는 DALL-E 모델들
SUPPORTED_MODELS = {
    "dall-e-3": {
        "name": "DALL-E 3",
        "description": "최신 이미지 생성 모델 (고품질)",
        "max_images": 1,  # DALL-E 3는 한 번에 1개만
        "sizes": ["1024x1024", "1792x1024", "1024x1792"],
        "quality": ["standard", "hd"]
    },
    "dall-e-2": {
        "name": "DALL-E 2",
        "description": "이전 버전 이미지 생성 모델 (경제적)",
        "max_images": 10,
        "sizes": ["256x256", "512x512", "1024x1024"],
        "quality": ["standard"]
    }
}


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
                       model: str = "dall-e-3",
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