"""
블로그 자동화 모듈의 비즈니스 로직 서비스
"""
import time
import base64
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime

from src.foundation.logging import get_logger
from src.foundation.db import get_db
from src.foundation.exceptions import BusinessError, ValidationError
from src.toolbox.text_utils import clean_keyword

from .models import (
    BlogCredentials, BlogPlatform, LoginStatus, BlogSession,
    init_blog_automation_db
)
from .adapters import create_blog_adapter

logger = get_logger("blog_automation.service")


class BlogAutomationService:
    """블로그 자동화 서비스"""
    
    def __init__(self):
        self.adapter = None
        self.current_session: Optional[BlogSession] = None
        self._init_database()
    
    def _init_database(self):
        """데이터베이스 초기화"""
        try:
            with get_db().get_connection() as conn:
                init_blog_automation_db(conn)
            logger.info("블로그 자동화 데이터베이스 초기화 완료")
        except Exception as e:
            logger.error(f"데이터베이스 초기화 실패: {e}")
            raise BusinessError(f"데이터베이스 초기화 실패: {str(e)}")
    
    def validate_credentials(self, platform: str, username: str, password: str) -> BlogCredentials:
        """자격증명 유효성 검사 및 생성"""
        try:
            # 플랫폼 변환
            if platform == "네이버":
                blog_platform = BlogPlatform.NAVER
            elif platform == "다음":
                blog_platform = BlogPlatform.TISTORY
            elif platform == "구글":
                blog_platform = BlogPlatform.BLOGGER
            else:
                raise ValidationError(f"지원하지 않는 플랫폼: {platform}")
            
            credentials = BlogCredentials(
                platform=blog_platform,
                username=username.strip(),
                password=password.strip()
            )
            
            credentials.validate()
            return credentials
            
        except ValueError as e:
            raise ValidationError(str(e))
    
    def create_session(self, platform: BlogPlatform, username: str) -> BlogSession:
        """새 블로그 세션 생성"""
        session = BlogSession(
            platform=platform,
            username=username,
            status=LoginStatus.NOT_LOGGED_IN,
            created_at=datetime.now()
        )
        
        self.current_session = session
        return session
    
    def login(self, credentials: BlogCredentials) -> bool:
        """블로그 플랫폼 로그인"""
        try:
            logger.info(f"블로그 로그인 시작: {credentials.platform.value} - {credentials.username}")
            
            # 어댑터 생성
            self.adapter = create_blog_adapter(credentials.platform)
            
            # 세션 생성
            self.create_session(credentials.platform, credentials.username)
            
            # 브라우저 시작
            self.adapter.start_browser()
            
            # 로그인 수행
            login_status = self.adapter.login_with_credentials(credentials)
            
            # 세션 상태 업데이트
            if self.current_session:
                self.current_session.status = login_status
                self.current_session.last_activity = datetime.now()
            
            # 로그인 성공 여부 반환
            success = login_status == LoginStatus.LOGGED_IN
            
            if success:
                logger.info("블로그 로그인 성공")
                # 로그인 세션 저장
                self._save_session()
            else:
                logger.error(f"블로그 로그인 실패: {login_status}")
            
            return success
            
        except Exception as e:
            logger.error(f"블로그 로그인 오류: {e}")
            if self.current_session:
                self.current_session.status = LoginStatus.LOGIN_FAILED
            raise BusinessError(f"로그인 실패: {str(e)}")
    
    def _save_session(self):
        """현재 세션을 데이터베이스에 저장"""
        if not self.current_session:
            return
        
        try:
            with get_db().get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO blog_sessions 
                    (platform, username, status, created_at, last_activity)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    self.current_session.platform.value,
                    self.current_session.username,
                    self.current_session.status.value,
                    self.current_session.created_at,
                    self.current_session.last_activity
                ))
                conn.commit()
                logger.info("블로그 세션 저장 완료")
                
        except Exception as e:
            logger.error(f"세션 저장 실패: {e}")
    
    def save_credentials(self, credentials: BlogCredentials):
        """로그인 자격증명 저장 (암호화)"""
        try:
            encrypted_password = self._encrypt_password(credentials.password)
            
            with get_db().get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO blog_credentials 
                    (platform, username, encrypted_password, updated_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    credentials.platform.value,
                    credentials.username,
                    encrypted_password,
                    datetime.now()
                ))
                conn.commit()
                logger.info(f"블로그 자격증명 저장: {credentials.platform.value} - {credentials.username}")
                
        except Exception as e:
            logger.error(f"자격증명 저장 실패: {e}")
            raise BusinessError(f"자격증명 저장 실패: {str(e)}")
    
    def load_saved_credentials(self, platform: BlogPlatform) -> Optional[tuple]:
        """저장된 자격증명 로드"""
        try:
            with get_db().get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT username, encrypted_password 
                    FROM blog_credentials 
                    WHERE platform = ?
                    ORDER BY updated_at DESC
                    LIMIT 1
                """, (platform.value,))
                
                result = cursor.fetchone()
                if result:
                    username, encrypted_password = result
                    password = self._decrypt_password(encrypted_password)
                    return username, password
                
                return None
                
        except Exception as e:
            logger.error(f"자격증명 로드 실패: {e}")
            return None
    
    def delete_saved_credentials(self, platform: BlogPlatform, username: str):
        """저장된 자격증명 삭제"""
        try:
            with get_db().get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM blog_credentials 
                    WHERE platform = ? AND username = ?
                """, (platform.value, username))
                conn.commit()
                logger.info(f"자격증명 삭제: {platform.value} - {username}")
                
        except Exception as e:
            logger.error(f"자격증명 삭제 실패: {e}")
    
    def _encrypt_password(self, password: str) -> str:
        """비밀번호 암호화 (간단한 Base64 인코딩)"""
        # 실제 운영환경에서는 더 강력한 암호화 사용 권장
        encoded = base64.b64encode(password.encode('utf-8')).decode('utf-8')
        return encoded
    
    def _decrypt_password(self, encrypted_password: str) -> str:
        """비밀번호 복호화"""
        try:
            decoded = base64.b64decode(encrypted_password.encode('utf-8')).decode('utf-8')
            return decoded
        except Exception:
            return ""
    
    def check_login_status(self) -> bool:
        """현재 로그인 상태 확인"""
        if not self.adapter:
            return False
            
        try:
            return self.adapter.check_login_status()
        except Exception as e:
            logger.error(f"로그인 상태 확인 실패: {e}")
            return False
    
    def open_blog_write_page(self) -> bool:
        """블로그 글쓰기 페이지 열기"""
        try:
            logger.info("블로그 글쓰기 페이지 열기 시작")
            
            if not self.adapter:
                raise BusinessError("로그인되지 않았습니다")
            
            if not self.adapter.is_logged_in:
                raise BusinessError("로그인 상태를 확인해주세요")
            
            # 글쓰기 버튼 클릭
            success = self.adapter.click_write_button()
            
            if success:
                logger.info("✅ 블로그 글쓰기 페이지 열기 성공")
                return True
            else:
                logger.error("❌ 블로그 글쓰기 페이지 열기 실패")
                return False
                
        except Exception as e:
            logger.error(f"블로그 글쓰기 페이지 열기 오류: {e}")
            raise BusinessError(f"글쓰기 페이지 열기 실패: {str(e)}")
    
    def force_stop_browser_session(self):
        """브라우저 세션 강제 중단"""
        try:
            if self.adapter and hasattr(self.adapter, 'close_browser'):
                logger.info("블로그 자동화 브라우저 세션 강제 중단")
                self.adapter.close_browser()
                
            self.adapter = None
            if self.current_session:
                self.current_session.status = LoginStatus.NOT_LOGGED_IN
                
        except Exception as e:
            logger.error(f"브라우저 세션 강제 중단 실패: {e}")
    
    def analyze_top_blogs(self, keyword: str) -> list:
        """상위 블로그 분석"""
        try:
            logger.info(f"상위 블로그 분석 시작: {keyword}")
            
            # 키워드 정리
            cleaned_keyword = clean_keyword(keyword)
            if not cleaned_keyword:
                raise ValidationError("유효한 키워드를 입력해주세요")
            
            # 어댑터 생성 (분석 전용)
            if not self.adapter:
                self.adapter = create_blog_adapter(BlogPlatform.NAVER)
            
            # 분석 전용 브라우저 시작
            self.adapter.start_browser_for_analysis()
            
            # 상위 블로그 분석 수행
            analyzed_blogs = self.adapter.analyze_top_blogs(cleaned_keyword)
            
            logger.info(f"상위 블로그 분석 완료: {len(analyzed_blogs)}개")
            return analyzed_blogs
            
        except Exception as e:
            logger.error(f"상위 블로그 분석 오류: {e}")
            raise BusinessError(f"블로그 분석 실패: {str(e)}")

    def get_platform_display_name(self, platform: BlogPlatform) -> str:
        """플랫폼 표시명 반환"""
        display_names = {
            BlogPlatform.NAVER: "네이버 (네이버블로그)",
            BlogPlatform.TISTORY: "다음 (티스토리)", 
            BlogPlatform.BLOGGER: "구글 (블로거)"
        }
        return display_names.get(platform, platform.value)
    
    def _map_ui_model_to_technical_name(self, ui_model_name: str) -> str:
        """UI 모델명을 기술적 모델명으로 매핑"""
        model_mapping = {
            # OpenAI 모델들
            "GPT-4o Mini (무료, 빠름)": "gpt-4o-mini",
            "GPT-4o (유료, 표준)": "gpt-4o", 
            "GPT-4 Turbo (유료, 고품질)": "gpt-4-turbo",
            
            # Google Gemini 모델들
            "Gemini 1.5 Flash (무료, 빠름)": "gemini-1.5-flash-latest",
            "Gemini 1.5 Pro (무료, 고품질)": "gemini-1.5-pro-latest", 
            "Gemini 2.0 Flash (무료, 최신)": "gemini-2.0-flash-exp",
            
            # Anthropic Claude 모델들
            "Claude 3.5 Sonnet (유료, 고품질)": "claude-3-5-sonnet-20241022",
            "Claude 3.5 Haiku (유료, 빠름)": "claude-3-5-haiku-20241022",
            "Claude 3 Opus (유료, 최고품질)": "claude-3-opus-20240229"
        }
        
        return model_mapping.get(ui_model_name, ui_model_name)
    
    def generate_blog_content(self, prompt: str) -> str:
        """API 설정에서 선택된 AI를 사용하여 블로그 콘텐츠 생성"""
        try:
            logger.info("AI 블로그 콘텐츠 생성 시작")
            
            # API 설정 로드
            from src.foundation.config import config_manager
            api_config = config_manager.load_api_config()
            
            # 메시지 형식으로 변환
            messages = [
                {
                    "role": "system",
                    "content": "당신은 15년 경력의 네이버 블로그 전문 마케터이자 SEO 전문가입니다."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ]
            
            # 설정된 AI 프로바이더와 모델에 따라 호출
            provider = api_config.current_text_ai_provider or "openai"
            ui_model = api_config.current_text_ai_model or "GPT-4o (유료, 표준)"
            
            # 디버그: 현재 설정 상태 로깅
            logger.info(f"현재 AI 설정 - Provider: {provider}, Model: {ui_model}")
            logger.info(f"API 키 상태 - OpenAI: {bool(api_config.openai_api_key)}, Gemini: {bool(api_config.gemini_api_key)}, Claude: {bool(api_config.claude_api_key)}")
            
            # UI 모델명을 기술적 모델명으로 변환
            technical_model = self._map_ui_model_to_technical_name(ui_model)
            
            if provider == "openai" and api_config.openai_api_key and api_config.openai_api_key.strip():
                logger.info(f"OpenAI API 사용: {ui_model} -> {technical_model}")
                from src.vendors.openai.text_client import openai_text_client
                response = openai_text_client.generate_text(messages, model=technical_model)
                
            elif provider == "google" and api_config.gemini_api_key and api_config.gemini_api_key.strip():
                logger.info(f"Google Gemini API 사용: {ui_model} -> {technical_model}")
                from src.vendors.google.text_client import gemini_text_client
                response = gemini_text_client.generate_text(messages, model=technical_model)
                
            elif provider == "anthropic" and api_config.claude_api_key and api_config.claude_api_key.strip():
                logger.info(f"Anthropic Claude API 사용: {ui_model} -> {technical_model}")
                from src.vendors.anthropic.text_client import claude_text_client
                response = claude_text_client.generate_text(messages, model=technical_model)
                
            else:
                # 디버그 정보 추가
                debug_info = f"provider={provider}, "
                if provider == "openai":
                    debug_info += f"openai_key_exists={bool(api_config.openai_api_key)}, openai_key_length={len(api_config.openai_api_key) if api_config.openai_api_key else 0}"
                elif provider == "google":
                    debug_info += f"gemini_key_exists={bool(api_config.gemini_api_key)}, gemini_key_length={len(api_config.gemini_api_key) if api_config.gemini_api_key else 0}"
                elif provider == "anthropic":
                    debug_info += f"claude_key_exists={bool(api_config.claude_api_key)}, claude_key_length={len(api_config.claude_api_key) if api_config.claude_api_key else 0}"
                
                logger.error(f"API 키 확인 실패: {debug_info}")
                raise BusinessError(f"선택된 AI API({provider})의 키가 설정되지 않았습니다. API 설정에서 확인해주세요.")
            
            if response:
                logger.info(f"AI 콘텐츠 생성 완료: {len(response)}자")
                return response
            else:
                raise BusinessError("AI API 응답을 처리할 수 없습니다")
                
        except Exception as e:
            logger.error(f"AI 콘텐츠 생성 실패: {e}")
            raise BusinessError(f"AI 콘텐츠 생성 실패: {str(e)}")
    
    
    def _map_ui_image_model_to_technical_name(self, ui_model_name: str) -> str:
        """UI 이미지 모델명을 기술적 모델명으로 매핑"""
        image_model_mapping = {
            # OpenAI DALL-E 모델들
            "DALL-E 3 (고품질, 유료)": "dall-e-3",
            "DALL-E 2 (표준, 유료)": "dall-e-2",
            
            # Google Imagen 모델들  
            "Imagen 3 (고품질, 유료)": "imagen-3.0-generate-001",
            "Imagen 2 (표준, 유료)": "imagen-2.0-generate-001"
        }
        
        return image_model_mapping.get(ui_model_name, ui_model_name)

    def generate_blog_images(self, prompt: str, image_count: int = 1) -> list:
        """API 설정에서 선택된 이미지 생성 AI를 사용하여 블로그 이미지 생성"""
        try:
            logger.info("AI 블로그 이미지 생성 시작")
            
            # API 설정 로드
            from src.foundation.config import config_manager
            api_config = config_manager.load_api_config()
            
            # 설정된 AI 프로바이더와 모델에 따라 호출
            provider = api_config.current_image_ai_provider or "openai"
            ui_model = api_config.current_image_ai_model or "DALL-E 3 (고품질, 유료)"
            
            # UI 모델명을 기술적 모델명으로 변환
            technical_model = self._map_ui_image_model_to_technical_name(ui_model)
            
            if provider == "openai" and (api_config.dalle_api_key or api_config.openai_api_key):
                logger.info(f"OpenAI DALL-E API 사용: {ui_model} -> {technical_model}")
                from src.vendors.openai.image_client import openai_image_client
                images = openai_image_client.generate_images(prompt, model=technical_model, n=image_count)
                
            elif provider == "google" and api_config.imagen_api_key:
                logger.info(f"Google Imagen API 사용: {ui_model} -> {technical_model}")
                from src.vendors.google.image_client import imagen_client
                images = imagen_client.generate_images(prompt, model=technical_model, n=image_count)
                
            else:
                raise BusinessError(f"선택된 이미지 AI API({provider})의 키가 설정되지 않았습니다. API 설정에서 확인해주세요.")
            
            if images:
                logger.info(f"AI 이미지 생성 완료: {len(images)}개")
                return images
            else:
                raise BusinessError("AI API 응답을 처리할 수 없습니다")
                
        except Exception as e:
            logger.error(f"AI 이미지 생성 실패: {e}")
            raise BusinessError(f"AI 이미지 생성 실패: {str(e)}")
    
