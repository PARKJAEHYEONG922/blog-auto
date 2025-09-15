"""
중앙화된 AI 모델 관리 시스템
모든 AI 제공업체의 모델 정보를 한 곳에서 관리
"""
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional
import requests
from src.foundation.logging import get_logger

logger = get_logger("foundation.ai_models")


class AIProvider(Enum):
    """AI 제공업체"""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    NAVER = "naver"


class AIModelType(Enum):
    """AI 모델 타입"""
    TEXT = "text"
    IMAGE = "image"
    MULTIMODAL = "multimodal"
    SEARCH = "search"
    SEARCH_AD = "search_ad"


@dataclass
class AIModel:
    """AI 모델 정보"""
    id: str                    # API에서 사용하는 실제 모델명
    display_name: str         # UI에 표시되는 이름
    provider: AIProvider      # 제공업체
    model_type: AIModelType   # 모델 타입 (text/image/multimodal)
    description: str          # 설명
    max_tokens: int          # 최대 토큰 (이미지 모델은 0)
    context_window: int      # 컨텍스트 윈도우 (이미지 모델은 0)
    tier: str                # "basic", "premium", "enterprise"
    is_default: bool = False # 기본 모델 여부
    is_active: bool = True   # 사용 가능 여부
    is_test_model: bool = False  # API 테스트용 모델 여부


class AIModelRegistry:
    """모든 AI 모델 중앙 관리"""

    _models: Dict[str, AIModel] = {
        # Anthropic Claude Models (2025 최신)
        "claude-sonnet-4": AIModel(
            id="claude-sonnet-4-20250514",
            display_name="Claude Sonnet 4 (유료, 최신 고품질)",
            provider=AIProvider.ANTHROPIC,
            model_type=AIModelType.TEXT,
            description="최신 Claude Sonnet 4 모델 - 코딩과 추론에 탁월",
            max_tokens=8192,
            context_window=200000,
            tier="premium",
            is_default=True
        ),
        "claude-opus-4-1": AIModel(
            id="claude-opus-4-1-20250805",
            display_name="Claude Opus 4.1 (유료, 최고품질)",
            provider=AIProvider.ANTHROPIC,
            model_type=AIModelType.TEXT,
            description="최고 성능 Claude 모델 - 복잡한 추론과 고급 코딩",
            max_tokens=8192,
            context_window=200000,
            tier="premium"
        ),
        "claude-haiku-3-5": AIModel(
            id="claude-3-5-haiku-20241022",
            display_name="Claude 3.5 Haiku (유료, 빠름)",
            provider=AIProvider.ANTHROPIC,
            model_type=AIModelType.TEXT,
            description="빠르고 경제적인 Claude 3.5 Haiku",
            max_tokens=8192,
            context_window=200000,
            tier="basic",
            is_test_model=True  # API 테스트용으로 사용 (가장 저렴)
        ),

        # OpenAI Models (2025 최신 - GPT-5 시리즈 포함)
        "gpt-5": AIModel(
            id="gpt-5",
            display_name="GPT-5 (유료, 최고 성능)",
            provider=AIProvider.OPENAI,
            model_type=AIModelType.MULTIMODAL,
            description="OpenAI 최신 GPT-5 모델. 추론 능력과 효율성이 크게 향상됨. reasoning_effort/verbosity 지원",
            max_tokens=10000,
            context_window=200000,
            tier="enterprise",
            is_default=True
        ),
        "gpt-5-mini": AIModel(
            id="gpt-5-mini",
            display_name="GPT-5 Mini (유료, 균형)",
            provider=AIProvider.OPENAI,
            model_type=AIModelType.MULTIMODAL,
            description="GPT-5 소형 버전. 뛰어난 성능과 효율성의 균형. reasoning_effort/verbosity 지원",
            max_tokens=8000,
            context_window=200000,
            tier="premium"
        ),
        "gpt-5-nano": AIModel(
            id="gpt-5-nano",
            display_name="GPT-5 Nano (유료, 고효율)",
            provider=AIProvider.OPENAI,
            model_type=AIModelType.MULTIMODAL,
            description="GPT-5 초소형 버전. 빠르고 경제적. reasoning_effort/verbosity 지원",
            max_tokens=6000,
            context_window=128000,
            tier="basic",
            is_test_model=True  # API 테스트용으로 사용 (가장 경제적)
        ),

        # Google Gemini Models (2025 최신 - Gemini 2.5 시리즈)
        "gemini-2-5-pro": AIModel(
            id="gemini-2.5-pro-preview",
            display_name="Gemini 2.5 Pro (유료, 최고성능)",
            provider=AIProvider.GOOGLE,
            model_type=AIModelType.MULTIMODAL,
            description="최신 Gemini 2.5 Pro 모델 - 수학, 과학, 코딩에서 최고 성능. 사고 과정 지원",
            max_tokens=8192,
            context_window=1000000,
            tier="enterprise",
            is_default=True
        ),
        "gemini-2-5-flash": AIModel(
            id="gemini-2.5-flash-preview",
            display_name="Gemini 2.5 Flash (유료, 균형)",
            provider=AIProvider.GOOGLE,
            model_type=AIModelType.MULTIMODAL,
            description="최신 Gemini 2.5 Flash 모델 - 가성비와 성능의 균형. 사고 과정 지원",
            max_tokens=8192,
            context_window=1000000,
            tier="premium"
        ),
        "gemini-2-0-flash": AIModel(
            id="gemini-2.0-flash-preview",
            display_name="Gemini 2.0 Flash (부분무료, 고효율)",
            provider=AIProvider.GOOGLE,
            model_type=AIModelType.MULTIMODAL,
            description="Gemini 2.0 Flash 모델 - 빠르고 효율적. 네이티브 도구 사용 지원. 무료 할당량 제공",
            max_tokens=8192,
            context_window=1000000,
            tier="basic",
            is_test_model=True  # API 테스트용으로 사용 (가장 효율적)
        ),

        # OpenAI Image Models (2025 최신)
        "gpt-image-1": AIModel(
            id="gpt-image-1",
            display_name="GPT Image 1 (유료, 최고품질)",
            provider=AIProvider.OPENAI,
            model_type=AIModelType.IMAGE,
            description="최신 GPT Image 1 모델 - DALL-E 3 대체, 향상된 명령 이해, 텍스트 렌더링, 상세 편집",
            max_tokens=0,  # 이미지 모델은 토큰 개념 없음
            context_window=0,
            tier="enterprise",
            is_default=True
        ),

        # Google Image Models (2025 최신)
        "gemini-2-5-flash-image": AIModel(
            id="gemini-2.5-flash-image-preview",
            display_name="Gemini 2.5 Flash Image (유료, 최고품질)",
            provider=AIProvider.GOOGLE,
            model_type=AIModelType.IMAGE,
            description="최신 Gemini 2.5 Flash Image 모델 - 대화형 이미지 생성 및 편집, SynthID 워터마크 포함",
            max_tokens=0,
            context_window=0,
            tier="enterprise",
            is_default=True
        ),

        # Naver Search APIs
        "naver-shopping": AIModel(
            id="shop",
            display_name="네이버 쇼핑 검색 (무료)",
            provider=AIProvider.NAVER,
            model_type=AIModelType.SEARCH,
            description="네이버 쇼핑 상품 검색 API",
            max_tokens=100,  # max_display
            context_window=1000,  # max_start
            tier="free",
            is_default=True
        ),
        "naver-news": AIModel(
            id="news",
            display_name="네이버 뉴스 검색 (무료)",
            provider=AIProvider.NAVER,
            model_type=AIModelType.SEARCH,
            description="네이버 뉴스 검색 API",
            max_tokens=100,
            context_window=1000,
            tier="free"
        ),
        "naver-blog": AIModel(
            id="blog",
            display_name="네이버 블로그 검색 (무료)",
            provider=AIProvider.NAVER,
            model_type=AIModelType.SEARCH,
            description="네이버 블로그 검색 API",
            max_tokens=100,
            context_window=1000,
            tier="free"
        ),
        "naver-book": AIModel(
            id="book",
            display_name="네이버 도서 검색 (무료)",
            provider=AIProvider.NAVER,
            model_type=AIModelType.SEARCH,
            description="네이버 도서 검색 API",
            max_tokens=100,
            context_window=1000,
            tier="free"
        ),
        "naver-cafe": AIModel(
            id="cafearticle",
            display_name="네이버 카페글 검색 (무료)",
            provider=AIProvider.NAVER,
            model_type=AIModelType.SEARCH,
            description="네이버 카페글 검색 API",
            max_tokens=100,
            context_window=1000,
            tier="free"
        ),
        "naver-local": AIModel(
            id="local",
            display_name="네이버 지역 검색 (무료)",
            provider=AIProvider.NAVER,
            model_type=AIModelType.SEARCH,
            description="네이버 지역 검색 API",
            max_tokens=5,  # 지역 검색은 최대 5개
            context_window=1000,
            tier="free"
        ),

        # Naver Search Ad APIs
        "naver-keyword-tool": AIModel(
            id="keywordstool",
            display_name="네이버 키워드 도구 (유료)",
            provider=AIProvider.NAVER,
            model_type=AIModelType.SEARCH_AD,
            description="키워드 도구 - 월 검색량, 경쟁 지수 조회",
            max_tokens=0,  # API별로 다름
            context_window=25000,  # daily quota
            tier="premium",
            is_default=True,
            is_test_model=True
        )
    }

    @classmethod
    def get_model(cls, model_key: str) -> Optional[AIModel]:
        """모델 키로 모델 정보 조회"""
        return cls._models.get(model_key)

    @classmethod
    def get_models_by_provider(cls, provider: AIProvider) -> List[AIModel]:
        """제공업체별 모델 목록 (활성화된 것만)"""
        return [model for model in cls._models.values()
                if model.provider == provider and model.is_active]

    @classmethod
    def get_models_by_type(cls, model_type: AIModelType) -> List[AIModel]:
        """모델 타입별 목록 (활성화된 것만)"""
        return [model for model in cls._models.values()
                if model.model_type == model_type and model.is_active]

    @classmethod
    def get_models_by_provider_and_type(cls, provider: AIProvider, model_type: AIModelType) -> List[AIModel]:
        """제공업체와 모델 타입으로 필터링"""
        return [model for model in cls._models.values()
                if model.provider == provider and model.model_type == model_type and model.is_active]

    @classmethod
    def get_display_names_by_provider(cls, provider: AIProvider) -> List[str]:
        """UI 드롭다운용 표시명 목록"""
        models = cls.get_models_by_provider(provider)
        return [model.display_name for model in models]

    @classmethod
    def get_display_names_by_provider_and_type(cls, provider: AIProvider, model_type: AIModelType) -> List[str]:
        """제공업체와 모델 타입별 UI 드롭다운용 표시명 목록"""
        models = cls.get_models_by_provider_and_type(provider, model_type)
        return [model.display_name for model in models]

    @classmethod
    def get_image_models_by_provider(cls, provider: AIProvider) -> List[AIModel]:
        """제공업체별 이미지 모델 목록"""
        return cls.get_models_by_provider_and_type(provider, AIModelType.IMAGE)

    @classmethod
    def get_text_models_by_provider(cls, provider: AIProvider) -> List[AIModel]:
        """제공업체별 텍스트 모델 목록 (TEXT + MULTIMODAL)"""
        models = cls.get_models_by_provider(provider)
        return [model for model in models
                if model.model_type in [AIModelType.TEXT, AIModelType.MULTIMODAL]]

    @classmethod
    def get_model_by_display_name(cls, display_name: str) -> Optional[AIModel]:
        """표시명으로 모델 찾기"""
        for model in cls._models.values():
            if model.display_name == display_name and model.is_active:
                return model
        return None

    @classmethod
    def get_default_model(cls, provider: AIProvider) -> Optional[AIModel]:
        """제공업체의 기본 모델"""
        models = cls.get_models_by_provider(provider)
        for model in models:
            if model.is_default:
                return model
        return models[0] if models else None

    @classmethod
    def get_default_model_by_type(cls, provider: AIProvider, model_type: AIModelType) -> Optional[AIModel]:
        """제공업체의 특정 타입 기본 모델"""
        models = cls.get_models_by_provider_and_type(provider, model_type)
        for model in models:
            if model.is_default:
                return model
        return models[0] if models else None

    @classmethod
    def get_test_model(cls, provider: AIProvider) -> Optional[AIModel]:
        """API 테스트용 모델 (가장 저렴한 모델)"""
        models = cls.get_models_by_provider(provider)
        # 테스트용으로 지정된 모델 우선
        test_models = [m for m in models if m.is_test_model]
        if test_models:
            return test_models[0]
        # 없으면 basic tier 모델 선택
        basic_models = [m for m in models if m.tier == "basic"]
        return basic_models[0] if basic_models else models[0] if models else None

    @classmethod
    def get_api_endpoint(cls, provider: AIProvider, model_type: AIModelType = AIModelType.TEXT) -> str:
        """제공업체별 API 엔드포인트 (모델 타입별)"""
        endpoints = {
            AIProvider.ANTHROPIC: {
                AIModelType.TEXT: "https://api.anthropic.com/v1/messages",
                AIModelType.MULTIMODAL: "https://api.anthropic.com/v1/messages"
            },
            AIProvider.OPENAI: {
                AIModelType.TEXT: "https://api.openai.com/v1/chat/completions",
                AIModelType.MULTIMODAL: "https://api.openai.com/v1/chat/completions",
                AIModelType.IMAGE: "https://api.openai.com/v1/models"  # 모델 목록 조회로 테스트
            },
            AIProvider.GOOGLE: {
                AIModelType.TEXT: "https://generativelanguage.googleapis.com/v1beta/models",
                AIModelType.MULTIMODAL: "https://generativelanguage.googleapis.com/v1beta/models",
                AIModelType.IMAGE: "https://generativelanguage.googleapis.com/v1beta/models"
            },
            AIProvider.NAVER: {
                AIModelType.SEARCH: "https://openapi.naver.com/v1/search",
                AIModelType.SEARCH_AD: "https://api.naver.com"
            }
        }
        provider_endpoints = endpoints.get(provider, {})
        return provider_endpoints.get(model_type, "")

    @classmethod
    def get_all_models(cls) -> Dict[str, AIModel]:
        """모든 모델 정보 반환"""
        return cls._models.copy()

    @classmethod
    def get_model_mapping_for_service(cls) -> Dict[str, str]:
        """service.py용 UI 표시명 -> API 모델명 매핑"""
        mapping = {}
        for model in cls._models.values():
            if model.is_active:
                mapping[model.display_name] = model.id
        return mapping

    @classmethod
    def get_image_model_mapping_for_service(cls) -> Dict[str, str]:
        """service.py용 이미지 모델 UI 표시명 -> API 모델명 매핑"""
        mapping = {}
        for model in cls._models.values():
            if model.is_active and model.model_type == AIModelType.IMAGE:
                mapping[model.display_name] = model.id
        return mapping

    @classmethod
    def get_naver_search_apis(cls) -> List[AIModel]:
        """네이버 검색 API 목록"""
        return cls.get_models_by_provider_and_type(AIProvider.NAVER, AIModelType.SEARCH)

    @classmethod
    def get_naver_searchad_apis(cls) -> List[AIModel]:
        """네이버 검색광고 API 목록"""
        return cls.get_models_by_provider_and_type(AIProvider.NAVER, AIModelType.SEARCH_AD)

    @classmethod
    def get_naver_api_info(cls, api_type: str) -> Optional[AIModel]:
        """네이버 API ID로 정보 조회 (예: 'shop', 'news', 'keywordstool')"""
        for model in cls._models.values():
            if model.provider == AIProvider.NAVER and model.id == api_type:
                return model
        return None


class AIAPITester:
    """통합 AI API 테스트 클래스"""

    @staticmethod
    def test_api(provider: AIProvider, api_key: str, model_type: AIModelType = AIModelType.TEXT) -> tuple[bool, str]:
        """통합 AI API 테스트 - 모든 제공업체와 모델 타입 지원"""
        try:
            # 네이버 API 테스트
            if provider == AIProvider.NAVER:
                return AIAPITester._test_naver_api(api_key, model_type)
            # 테스트용 모델과 엔드포인트를 중앙에서 가져옴
            elif model_type == AIModelType.IMAGE:
                # 이미지 모델은 별도 테스트 로직 사용
                return AIAPITester._test_image_api(provider, api_key)
            else:
                # 텍스트/멀티모달 모델은 기존 로직 사용
                return AIAPITester._test_text_api(provider, api_key)

        except Exception as e:
            logger.error(f"{provider.value} API 테스트 오류: {e}")
            return False, f"API 테스트 실패: {str(e)}"

    @staticmethod
    def _test_text_api(provider: AIProvider, api_key: str) -> tuple[bool, str]:
        """텍스트/멀티모달 API 테스트"""
        try:
            test_model = AIModelRegistry.get_test_model(provider)
            endpoint = AIModelRegistry.get_api_endpoint(provider, AIModelType.TEXT)

            if not test_model:
                return False, f"{provider.value} 제공업체의 테스트 모델을 찾을 수 없습니다"
            if not endpoint:
                return False, f"{provider.value} 제공업체의 API 엔드포인트를 찾을 수 없습니다"

            logger.info(f"{provider.value} 텍스트 API 테스트 시작 - 모델: {test_model.display_name}")

            # 제공업체별 무료 체크 방법 사용
            if provider == AIProvider.GOOGLE:
                # Google: 모델 목록 조회 (무료)
                full_url = f"{endpoint}?key={api_key}"
                headers = {"Content-Type": "application/json"}
                response = requests.get(full_url, headers=headers, timeout=10)

            elif provider == AIProvider.OPENAI:
                # OpenAI: 모델 목록 조회 (무료)
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                response = requests.get("https://api.openai.com/v1/models", headers=headers, timeout=10)

            elif provider == AIProvider.ANTHROPIC:
                # Claude: usage 조회 시도 (무료), 실패시 최소 토큰 요청
                headers = {
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                }

                # 1차: usage 조회 시도
                try:
                    response = requests.get("https://api.anthropic.com/v1/usage", headers=headers, timeout=10)

                    # 401이면 API 키 오류 - 즉시 실패 반환
                    if response.status_code == 401:
                        return False, "API 키가 유효하지 않습니다."

                    # 200이면 성공
                    if response.status_code == 200:
                        pass  # 아래에서 성공 처리
                    else:
                        # 404나 다른 오류면 메시지 API로 재시도
                        data = {
                            "model": test_model.id,
                            "max_tokens": 1,
                            "messages": [{"role": "user", "content": "Hi"}]
                        }
                        response = requests.post(endpoint, headers=headers, json=data, timeout=10)

                        # 메시지 API에서도 401이면 실패
                        if response.status_code == 401:
                            return False, "API 키가 유효하지 않습니다."

                except requests.exceptions.RequestException:
                    # 네트워크 오류시 메시지 API로 재시도
                    try:
                        data = {
                            "model": test_model.id,
                            "max_tokens": 1,
                            "messages": [{"role": "user", "content": "Hi"}]
                        }
                        response = requests.post(endpoint, headers=headers, json=data, timeout=10)

                        # 메시지 API에서도 401이면 실패
                        if response.status_code == 401:
                            return False, "API 키가 유효하지 않습니다."

                    except:
                        return False, "네트워크 연결 오류"

            else:
                return False, f"지원되지 않는 제공업체: {provider.value}"

            # 응답 처리 (제공업체별로 다름)
            if response.status_code == 200:
                if provider == AIProvider.GOOGLE:
                    # Google: 모델 목록이 있으면 성공
                    try:
                        data = response.json()
                        models = data.get("models", [])
                        if models:
                            logger.info(f"Google 텍스트 API 테스트 성공 - 모델 수: {len(models)}")
                            return True, f"API 연결 성공 (사용 가능한 모델: {len(models)}개)"
                        else:
                            return True, "API 연결 성공"
                    except:
                        return True, "API 연결 성공"

                elif provider == AIProvider.OPENAI:
                    # OpenAI: 모델 목록에서 GPT 모델 확인
                    try:
                        data = response.json()
                        models = [m.get("id", "") for m in data.get("data", [])]
                        gpt_models = [m for m in models if "gpt" in m.lower()]
                        if gpt_models:
                            logger.info(f"OpenAI 텍스트 API 테스트 성공 - GPT 모델: {len(gpt_models)}개")
                            return True, f"API 연결 성공 (GPT 모델: {len(gpt_models)}개)"
                        else:
                            return True, "API 연결 성공"
                    except:
                        return True, "API 연결 성공"

                elif provider == AIProvider.ANTHROPIC:
                    # Claude: usage나 메시지 응답 성공
                    logger.info(f"Claude 텍스트 API 테스트 성공")
                    return True, "API 연결 성공"

                else:
                    logger.info(f"{provider.value} 텍스트 API 테스트 성공")
                    return True, "API 연결 성공"

            elif response.status_code == 400:
                if provider == AIProvider.GOOGLE:
                    return False, "API 키가 유효하지 않거나 잘못된 요청입니다."
                else:
                    return False, f"잘못된 요청 (상태코드: {response.status_code})"
            elif response.status_code == 401:
                return False, "API 키가 유효하지 않습니다."
            elif response.status_code == 403:
                return False, "API 키 권한이 부족합니다."
            elif response.status_code == 404:
                return False, "API 엔드포인트를 찾을 수 없습니다."
            elif response.status_code == 429:
                return False, "API 호출 한도를 초과했습니다."
            else:
                logger.warning(f"{provider.value} 텍스트 API 테스트 실패 - 상태코드: {response.status_code}")
                return False, f"API 오류 (상태코드: {response.status_code})"

        except requests.exceptions.Timeout:
            return False, "연결 시간 초과"
        except requests.exceptions.RequestException as e:
            return False, f"네트워크 오류: {str(e)}"
        except Exception as e:
            logger.error(f"{provider.value} 텍스트 API 테스트 중 오류: {e}")
            return False, f"API 테스트 실패: {str(e)}"

    @staticmethod
    def _test_image_api(provider: AIProvider, api_key: str) -> tuple[bool, str]:
        """이미지 API 테스트"""
        endpoint = AIModelRegistry.get_api_endpoint(provider, AIModelType.IMAGE)

        if not endpoint:
            return False, f"{provider.value} 제공업체의 이미지 API 엔드포인트를 찾을 수 없습니다"

        logger.info(f"{provider.value} 이미지 API 테스트 시작")

        if provider == AIProvider.OPENAI:
            # OpenAI는 모델 목록 조회로 테스트 (DALL-E 관련 모델 확인)
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            response = requests.get(endpoint, headers=headers, timeout=10)

            if response.status_code == 200:
                try:
                    models_data = response.json()
                    model_ids = [model.get("id", "") for model in models_data.get("data", [])]
                    image_models = [mid for mid in model_ids if 'dall-e' in mid.lower() or 'gpt-image' in mid.lower()]

                    if image_models:
                        logger.info(f"OpenAI 이미지 API 테스트 성공 - 사용 가능한 모델: {image_models}")
                        return True, f"API 연결 성공 (사용 가능한 모델: {', '.join(image_models[:3])})"
                    else:
                        return True, "API 연결 성공 (DALL-E 모델 확인 필요)"
                except:
                    return True, "API 연결 성공"
            else:
                return False, f"API 오류 (상태코드: {response.status_code})"

        elif provider == AIProvider.GOOGLE:
            # Google은 API 키를 URL에 포함하여 모델 목록 조회
            full_url = f"{endpoint}?key={api_key}"
            headers = {
                "Content-Type": "application/json"
            }

            response = requests.get(full_url, headers=headers, timeout=10)

            if response.status_code == 200:
                logger.info(f"Google 이미지 API 테스트 성공")
                return True, "API 연결 성공"
            elif response.status_code == 400:
                return False, "API 키가 유효하지 않거나 잘못된 요청입니다."
            elif response.status_code == 401:
                return False, "API 키가 유효하지 않습니다."
            elif response.status_code == 403:
                return False, "API 키 권한이 부족합니다."
            elif response.status_code == 429:
                return False, "API 호출 한도를 초과했습니다."
            else:
                return False, f"API 오류 (상태코드: {response.status_code})"

        else:
            return False, f"지원되지 않는 이미지 AI 제공업체: {provider.value}"


    @staticmethod
    def _test_naver_api(api_key: str, model_type: AIModelType = AIModelType.SEARCH) -> tuple[bool, str]:
        """네이버 API 테스트"""
        try:
            import requests

            if model_type == AIModelType.SEARCH:
                # 네이버 검색 API 테스트 - 블로그 검색으로 테스트
                url = "https://openapi.naver.com/v1/search/blog.json"
                headers = {
                    "X-Naver-Client-Id": api_key.split(":")[0] if ":" in api_key else api_key,
                    "X-Naver-Client-Secret": api_key.split(":")[1] if ":" in api_key else ""
                }
                params = {
                    "query": "테스트",
                    "display": 1
                }

                response = requests.get(url, headers=headers, params=params, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    total = data.get("total", 0)
                    logger.info(f"네이버 검색 API 테스트 성공 - 검색 결과: {total}건")
                    return True, f"네이버 검색 API 연결 성공 (검색 결과: {total:,}건)"
                elif response.status_code == 401:
                    return False, "네이버 Client ID/Secret이 유효하지 않습니다"
                elif response.status_code == 429:
                    return False, "API 호출 한도를 초과했습니다"
                else:
                    return False, f"API 오류 (상태코드: {response.status_code})"

            elif model_type == AIModelType.SEARCH_AD:
                # 네이버 검색광고 API 테스트 - 키워드 도구
                # 검색광고 API는 시그니처 인증이 필요하므로 기본적인 연결 테스트만
                url = "https://api.naver.com"
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code in [200, 404, 403]:  # 서버 응답이 있으면 연결은 정상
                        return True, "네이버 검색광고 API 서버 연결 확인됨 (실제 테스트는 키워드 도구에서 수행)"
                    else:
                        return False, f"서버 연결 실패 (상태코드: {response.status_code})"
                except:
                    return False, "네이버 검색광고 API 서버에 연결할 수 없습니다"
            else:
                return False, f"지원하지 않는 네이버 API 타입: {model_type}"

        except requests.exceptions.Timeout:
            return False, "연결 시간 초과"
        except requests.exceptions.RequestException as e:
            return False, f"네트워크 오류: {str(e)}"
        except Exception as e:
            logger.error(f"네이버 API 테스트 오류: {e}")
            return False, f"API 테스트 실패: {str(e)}"


def map_ui_model_to_technical_name(ui_model_name: str) -> str:
    """UI 모델명을 기술적 모델명으로 매핑 - 중앙화된 AI 모델 시스템 사용"""
    model_mapping = AIModelRegistry.get_model_mapping_for_service()
    mapped_model = model_mapping.get(ui_model_name, ui_model_name)
    
    if mapped_model == ui_model_name and ui_model_name not in model_mapping:
        logger.warning(f"UI 모델명 '{ui_model_name}'에 대한 매핑을 찾을 수 없음. 원본 모델명 사용")
    else:
        logger.info(f"모델 매핑: '{ui_model_name}' -> '{mapped_model}'")
    
    return mapped_model


def map_ui_image_model_to_technical_name(ui_model_name: str) -> str:
    """UI 이미지 모델명을 기술적 모델명으로 매핑 - 중앙 관리 시스템 사용"""
    image_model_mapping = AIModelRegistry.get_image_model_mapping_for_service()
    return image_model_mapping.get(ui_model_name, ui_model_name)