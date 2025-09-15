"""
블로그 자동화 모듈의 비즈니스 로직 서비스
"""
import time
import base64
import hashlib
from typing import Optional, Dict, Any, List
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
        """블로그 글쓰기 페이지 열기 (현재 비활성화)"""
        logger.info("글쓰기 페이지 기능은 현재 비활성화되어 있습니다")
        return True  # 일단 성공으로 처리
    
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
    

    def analyze_top_blogs_with_ai_selection(self, search_keyword: str, target_title: str, main_keyword: str, content_type: str = "정보/가이드형", max_results: int = 3, sub_keywords: str = "") -> list:
        """AI 제목 선별을 사용한 상위 블로그 분석"""
        try:
            logger.info(f"AI 제목 선별을 사용한 블로그 분석 시작: '{search_keyword}' -> 타겟: '{target_title}'")

            # 키워드 정리
            cleaned_keyword = clean_keyword(search_keyword)
            if not cleaned_keyword:
                raise ValidationError("유효한 키워드를 입력해주세요")

            # 어댑터 생성 (분석 전용)
            if not self.adapter:
                self.adapter = create_blog_adapter(BlogPlatform.NAVER)

            # 분석 전용 브라우저 시작
            self.adapter.start_browser_for_analysis()

            # 1단계: 블로그 제목 30개 수집
            logger.info("🔍 1단계: 블로그 제목 30개 수집 중...")
            blog_titles_data = self.adapter.get_blog_titles_for_ai_selection(cleaned_keyword, 30)

            if not blog_titles_data or len(blog_titles_data) < 30:
                if blog_titles_data:
                    logger.warning(f"'{cleaned_keyword}' 검색 결과 부족: {len(blog_titles_data)}개. 메인키워드로 재시도...")
                else:
                    logger.warning(f"'{cleaned_keyword}' 검색 결과가 없습니다. 메인키워드로 재시도...")

                # 폴백 1: 메인키워드만으로 다시 검색
                main_keyword_cleaned = clean_keyword(main_keyword)
                if main_keyword_cleaned and main_keyword_cleaned != cleaned_keyword:
                    blog_titles_data = self.adapter.get_blog_titles_for_ai_selection(main_keyword_cleaned, 30)
                    logger.info(f"메인키워드 '{main_keyword_cleaned}'로 재검색 시도")

                if not blog_titles_data:
                    logger.warning("메인키워드 검색도 실패. 분석 없이 AI 글쓰기로 진행")
                    return []  # 빈 분석 결과 반환 (폴백 처리는 상위에서)

            logger.info(f"✅ {len(blog_titles_data)}개 블로그 제목 수집 완료")

            # 제목만 추출 (AI 분석용)
            titles_only = [blog['title'] for blog in blog_titles_data]

            # 2단계: AI로 관련도 높은 상위 10개 제목 선별
            logger.info("🤖 2단계: AI를 사용한 제목 선별 중...")
            selected_titles = self.select_blog_titles_with_ai(
                target_title, search_keyword, main_keyword, content_type, titles_only, sub_keywords
            )

            if not selected_titles:
                logger.warning("AI가 선별한 제목이 없습니다. 원본 순서대로 진행합니다")
                selected_indices = list(range(min(10, len(blog_titles_data))))
                selected_urls = [blog_titles_data[i]['url'] for i in selected_indices]
            else:
                logger.info(f"✅ AI가 {len(selected_titles)}개 제목을 선별했습니다")
                # 선별된 제목의 URL 매핑
                selected_urls = []
                for selected in selected_titles:
                    original_index = selected['original_index']
                    if 0 <= original_index < len(blog_titles_data):
                        selected_urls.append(blog_titles_data[original_index]['url'])

            if not selected_urls:
                logger.warning("분석할 URL이 없습니다")
                return []

            # 3단계: 선별된 URL들을 어댑터에서 필터링과 함께 분석
            logger.info(f"📝 3단계: 선별된 {len(selected_urls)}개 URL 분석 시작...")
            analyzed_blogs = self.adapter.analyze_selected_urls_with_filtering(selected_urls, max_results)

            logger.info(f"🎯 AI 선별 기반 블로그 분석 완료: {len(analyzed_blogs)}개")
            return analyzed_blogs

        except Exception as e:
            logger.error(f"AI 선별 기반 블로그 분석 오류: {e}")
            raise BusinessError(f"AI 선별 블로그 분석 실패: {str(e)}")

    def get_platform_display_name(self, platform: BlogPlatform) -> str:
        """플랫폼 표시명 반환"""
        display_names = {
            BlogPlatform.NAVER: "네이버 (네이버블로그)",
            BlogPlatform.TISTORY: "다음 (티스토리)", 
            BlogPlatform.BLOGGER: "구글 (블로거)"
        }
        return display_names.get(platform, platform.value)
    
    def _map_ui_model_to_technical_name(self, ui_model_name: str) -> str:
        """UI 모델명을 기술적 모델명으로 매핑 - 중앙화된 AI 모델 시스템 사용"""
        from src.foundation.ai_models import AIModelRegistry

        model_mapping = AIModelRegistry.get_model_mapping_for_service()

        mapped_model = model_mapping.get(ui_model_name, ui_model_name)
        if mapped_model == ui_model_name and ui_model_name not in model_mapping:
            logger.warning(f"UI 모델명 '{ui_model_name}'에 대한 매핑을 찾을 수 없음. 원본 모델명 사용")
        else:
            logger.info(f"모델 매핑: '{ui_model_name}' -> '{mapped_model}'")
        return mapped_model
    
    def call_summary_ai(self, prompt: str, response_format: str = "text", context: str = "정보요약") -> Any:
        """통합 정보요약 AI 호출 함수 - 프롬프트만 받아서 처리"""
        try:
            # API 설정 로드
            from src.foundation.config import config_manager
            api_config = config_manager.load_api_config()

            # 정보요약 AI 설정 확인
            summary_provider = api_config.current_summary_ai_provider
            summary_ui_model = api_config.current_summary_ai_model

            if not summary_provider:
                raise BusinessError("정보요약 AI 제공자가 설정되지 않았습니다. API 설정에서 정보요약 AI를 선택해주세요.")

            if not summary_ui_model:
                raise BusinessError("정보요약 AI 모델이 설정되지 않았습니다. API 설정에서 모델을 선택해주세요.")

            logger.info(f"통합 정보요약 AI 호출 ({context}) - Provider: {summary_provider}, Model: {summary_ui_model}")

            # UI 모델명을 기술적 모델명으로 변환
            technical_model = self._map_ui_model_to_technical_name(summary_ui_model)

            # 메시지 구성
            messages = [{"role": "user", "content": prompt}]

            # AI 호출
            if summary_provider == "openai" and api_config.openai_api_key and api_config.openai_api_key.strip():
                logger.info(f"OpenAI API 사용 ({context}): {summary_ui_model} -> {technical_model}")
                from src.vendors.openai.text_client import openai_text_client
                response = openai_text_client.generate_text(messages, model=technical_model)

            elif summary_provider == "google" and api_config.gemini_api_key and api_config.gemini_api_key.strip():
                logger.info(f"Google Gemini API 사용 ({context}): {summary_ui_model} -> {technical_model}")
                from src.vendors.google.text_client import gemini_text_client
                response = gemini_text_client.generate_text(messages, model=technical_model)

            elif summary_provider == "anthropic" and api_config.claude_api_key and api_config.claude_api_key.strip():
                logger.info(f"Anthropic Claude API 사용 ({context}): {summary_ui_model} -> {technical_model}")
                from src.vendors.anthropic.text_client import claude_text_client
                response = claude_text_client.generate_text(messages, model=technical_model)

            else:
                logger.error("정보요약 AI가 설정되지 않음. API 설정에서 정보요약 AI를 설정해주세요.")
                raise BusinessError("정보요약 AI가 설정되지 않았습니다. API 설정에서 정보요약 AI를 먼저 설정해주세요.")

            if not response or not response.strip():
                raise BusinessError("AI 응답이 비어있습니다")

            response = response.strip()

            # 응답 형식에 따른 처리
            if response_format == "json":
                return self._parse_json_response(response)
            else:
                return response

        except BusinessError:
            raise
        except Exception as e:
            logger.error(f"통합 정보요약 AI 호출 실패 ({context}): {e}")
            raise BusinessError(f"정보요약 AI 처리 중 오류가 발생했습니다: {str(e)}")

    def _parse_json_response(self, response: str) -> Any:
        """JSON 응답 파싱"""
        try:
            import json

            # 마크다운 코드 블록 제거 (```json...``` 또는 ```...```)
            cleaned_response = response.strip()
            if cleaned_response.startswith('```'):
                lines = cleaned_response.split('\n')
                if len(lines) > 2 and lines[0].startswith('```') and lines[-1].strip() == '```':
                    cleaned_response = '\n'.join(lines[1:-1])

            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 실패: {e}\n응답: {response}")
            raise BusinessError(f"AI 응답을 JSON으로 파싱할 수 없습니다: {str(e)}")

    def generate_content_summary(self, combined_content: str, main_keyword: str, content_type: str, search_keyword: str = "") -> str:
        """콘텐츠 요약 생성 - ai_prompts의 BlogSummaryPrompts 사용"""
        try:
            from .ai_prompts import BlogSummaryPrompts

            # 임시 블로그 데이터 구성 (combined_content 기반)
            temp_blogs = [{
                'title': f"{main_keyword} 관련 콘텐츠",
                'text_content': combined_content
            }] if combined_content.strip() else []

            # ai_prompts의 정식 프롬프트 사용
            summary_prompt = BlogSummaryPrompts.generate_content_summary_prompt(
                selected_title=f"{main_keyword} 관련 정보",
                search_keyword=search_keyword or main_keyword,
                main_keyword=main_keyword,
                content_type=content_type,
                competitor_blogs=temp_blogs,
                sub_keywords=""
            )

            return self.call_summary_ai(summary_prompt, "text", "콘텐츠요약")
        except Exception as e:
            logger.error(f"콘텐츠 요약 실패: {e}")
            return f"{main_keyword}에 대한 요약 정보"

    def generate_blog_content(self, prompt: str) -> str:
        """API 설정에서 선택된 AI를 사용하여 블로그 콘텐츠 생성"""
        try:
            logger.info("AI 블로그 콘텐츠 생성 시작")
            
            # API 설정 로드
            from src.foundation.config import config_manager
            api_config = config_manager.load_api_config()
            
            # ai_prompts에서 완성된 프롬프트를 그대로 AI에게 전달
            messages = [
                {
                    "role": "user", 
                    "content": prompt
                }
            ]
            
            # 설정된 AI 프로바이더와 모델에 따라 호출
            provider = api_config.current_text_ai_provider
            ui_model = api_config.current_text_ai_model

            if not provider:
                raise BusinessError("글쓰기 AI 제공자가 설정되지 않았습니다. API 설정에서 글쓰기 AI를 선택해주세요.")

            if not ui_model:
                raise BusinessError("글쓰기 AI 모델이 설정되지 않았습니다. API 설정에서 모델을 선택해주세요.")

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

    def generate_blog_content_with_summary(self, main_keyword: str, sub_keywords: str, analyzed_blogs: list, content_type: str = "정보/가이드형", tone: str = "정중한 존댓말체", review_detail: str = "", search_keyword: str = "") -> str:
        """2단계 파이프라인: 정보요약 AI → 글작성 AI"""
        try:
            logger.info("2단계 파이프라인으로 블로그 콘텐츠 생성 시작")

            # 1단계: 분석된 블로그들의 콘텐츠를 하나의 텍스트로 통합
            logger.info("1단계: 경쟁 블로그 콘텐츠 통합")
            combined_content = self._combine_blog_contents(analyzed_blogs)

            if not combined_content.strip():
                logger.warning("통합할 블로그 콘텐츠가 없습니다.")
                combined_content = "분석할 콘텐츠가 없습니다."

            logger.info(f"통합된 콘텐츠 길이: {len(combined_content)}자")

            # 2단계: 정보요약 AI로 콘텐츠 요약
            logger.info("2단계: 정보요약 AI로 콘텐츠 요약")
            summarized_content = self.generate_content_summary(combined_content, main_keyword, content_type, search_keyword)
            logger.info(f"요약된 콘텐츠 길이: {len(summarized_content)}자")

            # 3단계: 요약된 내용을 포함한 프롬프트로 글작성 AI 호출
            logger.info("3단계: 요약 내용 기반 최종 블로그 글 생성")

            # 블로그 구조 분석
            from .ai_prompts import BlogContentStructure, BlogAIPrompts
            structure_analyzer = BlogContentStructure()
            structured_data = structure_analyzer.analyze_blog_structure(analyzed_blogs)

            # 블로거 정체성 가져오기
            from src.foundation.config import config_manager
            api_config = config_manager.load_api_config()
            blogger_identity = getattr(api_config, 'ai_writing_blogger_identity', '')

            # 1차 결과를 포함한 완전한 프롬프트 생성
            enhanced_prompt = BlogAIPrompts.generate_content_analysis_prompt(
                main_keyword=main_keyword,
                sub_keywords=sub_keywords,
                structured_data=structured_data,
                content_type=content_type,
                tone=tone,
                review_detail=review_detail,
                blogger_identity=blogger_identity,
                summary_result=summarized_content,
                search_keyword=search_keyword
            )

            # 글작성 AI로 최종 콘텐츠 생성
            final_content = self.generate_blog_content(enhanced_prompt)

            logger.info("2단계 파이프라인 완료")
            return final_content

        except Exception as e:
            logger.error(f"2단계 파이프라인 실패: {e}")
            raise BusinessError(f"블로그 콘텐츠 생성 실패: {str(e)}")

    def _combine_blog_contents(self, analyzed_blogs: list) -> str:
        """분석된 블로그들의 텍스트 콘텐츠를 하나로 통합 (전체 내용 포함)"""
        combined_parts = []
        
        for i, blog in enumerate(analyzed_blogs):
            title = blog.get('title', '제목 없음')
            text_content = blog.get('text_content', '')
            
            if text_content and text_content != '분석 실패':
                blog_section = f"""=== {i+1}위 블로그: {title} ===

{text_content}

===============================
"""
                combined_parts.append(blog_section)
                logger.info(f"{i+1}위 블로그 내용 추가: {len(text_content)}자")
        
        if not combined_parts:
            return "분석할 수 있는 블로그 콘텐츠가 없습니다."
        
        combined_content = '\n'.join(combined_parts)
        logger.info(f"최종 결합된 전체 콘텐츠 길이: {len(combined_content)}자 (길이 제한 없음)")
        return combined_content

    def _generate_content_without_analysis(self, main_keyword: str, sub_keywords: str, content_type: str, tone: str, review_detail: str, search_keyword: str = "") -> Dict[str, str]:
        """분석 없이 AI 글쓰기만으로 콘텐츠 생성"""
        try:
            logger.info("분석 없이 AI 글쓰기로 콘텐츠 생성")

            # 블로거 정체성 가져오기
            from src.foundation.config import config_manager
            api_config = config_manager.load_api_config()
            blogger_identity = getattr(api_config, 'ai_writing_blogger_identity', '')

            # 분석 없는 글쓰기 프롬프트 생성 (기존 메서드 활용)
            from .ai_prompts import BlogAIPrompts
            # 빈 구조화 데이터로 직접 글쓰기 프롬프트 생성
            empty_structured_data = {"competitor_analysis": {"top_blogs": [], "summary": {}}}
            writing_prompt = BlogAIPrompts.generate_content_analysis_prompt(
                main_keyword=main_keyword,
                sub_keywords=sub_keywords,
                structured_data=empty_structured_data,
                content_type=content_type,
                tone=tone,
                review_detail=review_detail,
                blogger_identity=blogger_identity,
                summary_result="경쟁 블로그 분석 결과가 없어 직접 작성합니다.",
                search_keyword=search_keyword
            )

            # AI로 직접 콘텐츠 생성
            final_content = self.generate_blog_content(writing_prompt)

            logger.info("분석 없는 AI 글쓰기 완료")

            return {
                "summary_prompt": "분석 없음 - 직접 글쓰기",
                "summary_result": "경쟁 블로그 분석 결과가 없어 생략됨",
                "writing_prompt": writing_prompt,
                "final_content": final_content,
                "combined_content": "분석된 블로그 콘텐츠 없음"
            }

        except Exception as e:
            logger.error(f"분석 없는 AI 글쓰기 실패: {e}")
            raise BusinessError(f"AI 글쓰기 실패: {str(e)}")
    
    def generate_blog_content_with_summary_detailed(self, main_keyword: str, sub_keywords: str, analyzed_blogs: list, content_type: str = "정보/가이드형", tone: str = "정중한 존댓말체", review_detail: str = "", search_keyword: str = "") -> Dict[str, str]:
        """2단계 파이프라인: 정보요약 AI → 글작성 AI (상세 정보 포함)"""
        try:
            logger.info("2단계 파이프라인으로 블로그 콘텐츠 생성 시작 (상세 정보 포함)")
            
            # 분석 결과가 없는 경우 폴백 처리
            if not analyzed_blogs or len(analyzed_blogs) == 0:
                logger.warning("분석된 블로그가 없습니다. 분석 없이 AI 글쓰기로 진행")
                return self._generate_content_without_analysis(main_keyword, sub_keywords, content_type, tone, review_detail, search_keyword)

            # 1단계: 분석된 블로그들의 콘텐츠를 하나의 텍스트로 통합
            logger.info("1단계: 경쟁 블로그 콘텐츠 통합")
            combined_content = self._combine_blog_contents(analyzed_blogs)

            if not combined_content.strip():
                logger.warning("통합할 블로그 콘텐츠가 없습니다. 분석 없이 진행")
                return self._generate_content_without_analysis(main_keyword, sub_keywords, content_type, tone, review_detail, search_keyword)

            logger.info(f"통합된 콘텐츠 길이: {len(combined_content)}자")

            # 2단계: 정보요약 AI로 콘텐츠 요약
            logger.info("2단계: 정보요약 AI로 콘텐츠 요약")

            # 요약 내용 생성
            summarized_content = self.generate_content_summary(combined_content, main_keyword, content_type, search_keyword)

            # UI용 프롬프트 생성 (ai_prompts.py에서)
            from .ai_prompts import BlogSummaryPrompts
            temp_blogs = [{
                'title': f"{main_keyword} 관련 콘텐츠",
                'text_content': combined_content
            }] if combined_content.strip() else []
            summary_prompt = BlogSummaryPrompts.generate_content_summary_prompt(
                f"{main_keyword} 관련 정보",
                search_keyword or main_keyword,
                main_keyword,
                content_type,
                temp_blogs,
                ""
            )
            logger.info(f"요약된 콘텐츠 길이: {len(summarized_content)}자")
            
            # 3단계: 요약된 내용을 포함한 프롬프트로 글작성 AI 호출
            logger.info("3단계: 요약 내용 기반 최종 블로그 글 생성")
            
            # 블로그 구조 분석
            from .ai_prompts import BlogContentStructure, BlogAIPrompts
            structure_analyzer = BlogContentStructure()
            structured_data = structure_analyzer.analyze_blog_structure(analyzed_blogs)
            
            # 블로거 정체성 가져오기
            from src.foundation.config import config_manager
            api_config = config_manager.load_api_config()
            blogger_identity = getattr(api_config, 'ai_writing_blogger_identity', '')
            
            # 1차 결과를 포함한 완전한 프롬프트 생성
            enhanced_prompt = BlogAIPrompts.generate_content_analysis_prompt(
                main_keyword=main_keyword,
                sub_keywords=sub_keywords,
                structured_data=structured_data,
                content_type=content_type,
                tone=tone,
                review_detail=review_detail,
                blogger_identity=blogger_identity,
                summary_result=summarized_content,
                search_keyword=search_keyword
            )

            # 글작성 AI로 최종 콘텐츠 생성
            final_content = self.generate_blog_content(enhanced_prompt)
            
            logger.info("2단계 파이프라인 완료 (상세 정보 포함)")
            
            return {
                "summary_prompt": summary_prompt,
                "summary_result": summarized_content,
                "writing_prompt": enhanced_prompt,
                "final_content": final_content,
                "combined_content": combined_content
            }
            
        except Exception as e:
            logger.error(f"2단계 파이프라인 실패 (상세): {e}")
            raise BusinessError(f"블로그 콘텐츠 생성 실패: {str(e)}")
    
    def _map_ui_image_model_to_technical_name(self, ui_model_name: str) -> str:
        """UI 이미지 모델명을 기술적 모델명으로 매핑 - 중앙 관리 시스템 사용"""
        from src.foundation.ai_models import AIModelRegistry
        image_model_mapping = AIModelRegistry.get_image_model_mapping_for_service()
        return image_model_mapping.get(ui_model_name, ui_model_name)

    def select_blog_titles_with_ai(self, target_title: str, search_keyword: str, main_keyword: str, content_type: str, blog_titles: list, sub_keywords: str = "") -> list:
        """AI를 사용하여 30개 블로그 제목 중 관련도 높은 10개 선별"""
        try:
            logger.info("🤖 AI 블로그 제목 선별 시작")

            # ai_prompts에서 프롬프트 가져오기
            from .ai_prompts import BlogPromptComponents
            prompt = BlogPromptComponents.generate_blog_title_selection_prompt(
                target_title, search_keyword, main_keyword, content_type, blog_titles, sub_keywords
            )

            logger.info(f"제목 선별 프롬프트 생성 완료: {len(blog_titles)}개 제목 중 10개 선별 요청")

            # AI 호출 (JSON 응답 받기) - ai_prompts의 프롬프트가 JSON 형식으로 응답하도록 설계됨
            result = self.call_summary_ai(prompt, "json", "제목선별")

            # JSON에서 선별된 제목들 추출
            selected_titles = []
            if result and isinstance(result, dict) and 'selected_titles' in result:
                for item in result['selected_titles']:
                    if isinstance(item, dict) and 'title' in item and 'original_index' in item:
                        selected_titles.append({
                            'title': item['title'],
                            'original_index': item['original_index'],
                            'relevance_reason': item.get('relevance_reason', '')
                        })

            logger.info(f"✅ AI 제목 선별 완료: {len(selected_titles)}개")
            return selected_titles

        except Exception as e:
            logger.error(f"AI 제목 선별 실패: {e}")
            return []

    def generate_blog_images(self, prompt: str, image_count: int = 1) -> list:
        """API 설정에서 선택된 이미지 생성 AI를 사용하여 블로그 이미지 생성"""
        try:
            logger.info("AI 블로그 이미지 생성 시작")
            
            # API 설정 로드
            from src.foundation.config import config_manager
            api_config = config_manager.load_api_config()
            
            # 설정된 AI 프로바이더와 모델에 따라 호출
            provider = api_config.current_image_ai_provider
            ui_model = api_config.current_image_ai_model

            if not provider:
                raise BusinessError("이미지 생성 AI 제공자가 설정되지 않았습니다. API 설정에서 이미지 생성 AI를 선택해주세요.")

            if not ui_model:
                raise BusinessError("이미지 생성 AI 모델이 설정되지 않았습니다. API 설정에서 모델을 선택해주세요.")

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

