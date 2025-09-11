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
            
            # 설정된 AI API 확인 및 호출 (우선순위: OpenAI → Gemini → Claude)
            if api_config.openai_api_key:
                logger.info("OpenAI API 사용")
                response = self._call_openai_api(messages, api_config.openai_api_key)
                
            elif hasattr(api_config, 'gemini_api_key') and api_config.gemini_api_key:
                logger.info("Google Gemini API 사용")
                response = self._call_gemini_api(messages, api_config.gemini_api_key)
                
            elif api_config.claude_api_key:
                logger.info("Anthropic Claude API 사용")
                response = self._call_claude_api(messages, api_config.claude_api_key)
                
            else:
                raise BusinessError("텍스트 생성 AI API 키가 설정되지 않았습니다. API 설정에서 글 작성 AI API를 설정해주세요.")
            
            if response:
                logger.info(f"AI 콘텐츠 생성 완료: {len(response)}자")
                return response
            else:
                raise BusinessError("AI API 응답을 처리할 수 없습니다")
                
        except Exception as e:
            logger.error(f"AI 콘텐츠 생성 실패: {e}")
            raise BusinessError(f"AI 콘텐츠 생성 실패: {str(e)}")
    
    def _call_openai_api(self, messages: list, api_key: str) -> str:
        """OpenAI API 호출"""
        try:
            from src.vendors.openai.client import openai_client
            
            response = openai_client.create_completion(
                messages=messages,
                model="gpt-4o-mini",
                temperature=0.7,
                max_tokens=4000
            )
            
            if response and 'choices' in response and len(response['choices']) > 0:
                return response['choices'][0]['message']['content']
            else:
                raise BusinessError("OpenAI API 응답이 비어있습니다")
                
        except Exception as e:
            logger.error(f"OpenAI API 호출 실패: {e}")
            raise BusinessError(f"OpenAI API 호출 실패: {str(e)}")
    
    def _call_gemini_api(self, messages: list, api_key: str) -> str:
        """Google Gemini API 호출"""
        try:
            import requests
            
            # 메시지를 Gemini 형식으로 변환
            text_content = ""
            for message in messages:
                if message['role'] == 'system':
                    text_content += f"System: {message['content']}\n\n"
                elif message['role'] == 'user':
                    text_content += f"User: {message['content']}"
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}"
            
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
                    "maxOutputTokens": 4000,
                    "temperature": 0.7
                }
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    content = result['candidates'][0]['content']['parts'][0]['text']
                    return content
                else:
                    raise BusinessError("Gemini API 응답이 예상과 다릅니다")
            else:
                raise BusinessError(f"Gemini API 오류: 상태 코드 {response.status_code}")
                
        except Exception as e:
            logger.error(f"Gemini API 호출 실패: {e}")
            raise BusinessError(f"Gemini API 호출 실패: {str(e)}")
    
    def _call_claude_api(self, messages: list, api_key: str) -> str:
        """Anthropic Claude API 호출"""
        try:
            from src.vendors.openai.client import claude_client
            
            response = claude_client.create_message(
                messages=messages,
                model="claude-3-haiku-20240307",
                max_tokens=4000,
                temperature=0.7
            )
            
            if response and 'content' in response and len(response['content']) > 0:
                return response['content'][0]['text']
            else:
                raise BusinessError("Claude API 응답이 비어있습니다")
                
        except Exception as e:
            logger.error(f"Claude API 호출 실패: {e}")
            raise BusinessError(f"Claude API 호출 실패: {str(e)}")
    
    def generate_blog_images(self, prompt: str, image_count: int = 1) -> list:
        """API 설정에서 선택된 이미지 생성 AI를 사용하여 블로그 이미지 생성"""
        try:
            logger.info("AI 블로그 이미지 생성 시작")
            
            # API 설정 로드
            from src.foundation.config import config_manager
            api_config = config_manager.load_api_config()
            
            # 설정된 이미지 생성 AI API 확인 및 호출
            if hasattr(api_config, 'dalle_api_key') and api_config.dalle_api_key:
                logger.info("DALL-E API 사용")
                images = self._call_dalle_api(prompt, api_config.dalle_api_key, image_count)
                
            elif hasattr(api_config, 'imagen_api_key') and api_config.imagen_api_key:
                logger.info("Google Imagen API 사용")
                images = self._call_imagen_api(prompt, api_config.imagen_api_key, image_count)
                
            else:
                raise BusinessError("이미지 생성 AI API 키가 설정되지 않았습니다. API 설정에서 이미지 생성 AI API를 설정해주세요.")
            
            if images:
                logger.info(f"AI 이미지 생성 완료: {len(images)}개")
                return images
            else:
                raise BusinessError("AI API 응답을 처리할 수 없습니다")
                
        except Exception as e:
            logger.error(f"AI 이미지 생성 실패: {e}")
            raise BusinessError(f"AI 이미지 생성 실패: {str(e)}")
    
    def _call_dalle_api(self, prompt: str, api_key: str, image_count: int = 1) -> list:
        """DALL-E API 호출"""
        try:
            import requests
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "prompt": prompt,
                "n": min(image_count, 4),  # DALL-E는 최대 4개까지
                "size": "1024x1024",
                "quality": "standard"
            }
            
            response = requests.post(
                "https://api.openai.com/v1/images/generations",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'data' in result and len(result['data']) > 0:
                    return [item['url'] for item in result['data']]
                else:
                    raise BusinessError("DALL-E API 응답이 비어있습니다")
            else:
                raise BusinessError(f"DALL-E API 오류: 상태 코드 {response.status_code}")
                
        except Exception as e:
            logger.error(f"DALL-E API 호출 실패: {e}")
            raise BusinessError(f"DALL-E API 호출 실패: {str(e)}")
    
    def _call_imagen_api(self, prompt: str, api_key: str, image_count: int = 1) -> list:
        """Google Imagen API 호출"""
        try:
            # Google Imagen API는 복잡한 인증 과정이 필요하므로 일단 플레이스홀더로 구현
            logger.warning("Google Imagen API는 아직 구현되지 않았습니다.")
            
            # 임시로 DALL-E와 유사한 더미 응답 반환
            return [f"https://placeholder-image-{i+1}.jpg" for i in range(image_count)]
                
        except Exception as e:
            logger.error(f"Imagen API 호출 실패: {e}")
            raise BusinessError(f"Imagen API 호출 실패: {str(e)}")