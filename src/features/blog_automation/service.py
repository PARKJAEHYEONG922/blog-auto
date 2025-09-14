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

    def analyze_top_blogs_with_ai_selection(self, search_keyword: str, target_title: str, main_keyword: str, content_type: str = "정보/가이드형", max_results: int = 3) -> list:
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

            if not blog_titles_data:
                logger.warning("수집된 블로그 제목이 없습니다")
                return []

            logger.info(f"✅ {len(blog_titles_data)}개 블로그 제목 수집 완료")

            # 제목만 추출 (AI 분석용)
            titles_only = [blog['title'] for blog in blog_titles_data]

            # 2단계: AI로 관련도 높은 상위 10개 제목 선별
            logger.info("🤖 2단계: AI를 사용한 제목 선별 중...")
            selected_titles = self.select_blog_titles_with_ai(
                target_title, search_keyword, main_keyword, content_type, titles_only
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

            # 3단계: 선별된 URL들을 순차적으로 크롤링 (광고 필터링하면서 3개까지)
            logger.info(f"📝 3단계: 선별된 {len(selected_urls)}개 URL 순차 분석 중...")
            analyzed_blogs = []

            for i, url in enumerate(selected_urls):
                if len(analyzed_blogs) >= max_results:
                    logger.info(f"🎯 목표 개수 {max_results}개 달성, 분석 중단")
                    break

                try:
                    logger.info(f"📝 {i+1}/{len(selected_urls)} - URL 분석 중: {url}")

                    # HTTP 방식으로 먼저 시도
                    analysis_result = None
                    try:
                        analysis_result = self.adapter.analyze_blog_content_http(url)
                        if analysis_result and analysis_result.get('title') != '분석 실패' and analysis_result.get('content_length', 0) > 0:
                            logger.info(f"✅ HTTP 방식 분석 성공")
                        else:
                            analysis_result = None
                    except Exception:
                        analysis_result = None

                    # HTTP 실패 시 Selenium으로 백업
                    if not analysis_result:
                        try:
                            analysis_result = self.adapter.analyze_blog_content(url)
                            logger.info(f"✅ Selenium 방식 분석 성공")
                        except Exception as selenium_error:
                            logger.error(f"❌ 분석 실패: {selenium_error}")
                            continue

                    if not analysis_result:
                        continue

                    # 결과 정리
                    integrated_result = {
                        'rank': len(analyzed_blogs) + 1,
                        'title': analysis_result.get('title', '제목 없음'),
                        'url': url,
                        'content_length': analysis_result.get('content_length', 0),
                        'image_count': analysis_result.get('image_count', 0),
                        'gif_count': analysis_result.get('gif_count', 0),
                        'video_count': analysis_result.get('video_count', 0),
                        'tags': analysis_result.get('tags', []),
                        'text_content': analysis_result.get('text_content', ''),
                        'content_structure': analysis_result.get('content_structure', [])
                    }

                    # 광고/협찬 글 필터링 체크
                    text_content = integrated_result.get('text_content', '')
                    title = integrated_result.get('title', '')

                    from .adapters import is_advertisement_content
                    if is_advertisement_content(text_content, title):
                        logger.warning(f"🚫 {i+1}번째 URL 제외: 광고/협찬/체험단 글로 판단됨")
                        continue

                    # 정상적인 정보성 글만 추가
                    analyzed_blogs.append(integrated_result)
                    logger.info(f"✅ {i+1}번째 URL 분석 완료 (정보성 글)")

                except Exception as e:
                    logger.error(f"❌ {i+1}번째 URL 분석 실패: {e}")
                    continue

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
        """UI 모델명을 기술적 모델명으로 매핑"""
        model_mapping = {
            # OpenAI 모델들
            "GPT-4o Mini (유료, 저렴)": "gpt-4o-mini",
            "GPT-4o (유료, 표준)": "gpt-4o", 
            "GPT-4 Turbo (유료, 고단가)": "gpt-4-turbo",
            
            # Google Gemini 모델들
            "Gemini 1.5 Flash (무료, 빠름)": "gemini-1.5-flash-latest",
            "Gemini 1.5 Pro (유료, 고품질)": "gemini-1.5-pro-latest", 
            "Gemini 2.0 Flash (무료, 최신)": "gemini-2.0-flash-exp",
            
            # Anthropic Claude 모델들
            "Claude 3.5 Sonnet (유료, 고품질)": "claude-3-5-sonnet-20241022",
            "Claude 3.5 Haiku (유료, 빠름)": "claude-3-5-haiku-20241022",
            "Claude 3 Opus (유료, 최고품질)": "claude-3-opus-20240229"
        }
        
        mapped_model = model_mapping.get(ui_model_name, ui_model_name)
        if mapped_model == ui_model_name and ui_model_name not in model_mapping:
            logger.warning(f"UI 모델명 '{ui_model_name}'에 대한 매핑을 찾을 수 없음. 원본 모델명 사용")
        else:
            logger.info(f"모델 매핑: '{ui_model_name}' -> '{mapped_model}'")
        return mapped_model
    
    def _call_summary_ai(self, messages: list, context: str = "") -> str:
        """정보요약 AI 공용 호출 함수"""
        try:
            # API 설정 로드
            from src.foundation.config import config_manager
            api_config = config_manager.load_api_config()

            # 정보요약 AI 설정 확인
            summary_provider = api_config.current_summary_ai_provider or "openai"
            summary_ui_model = api_config.current_summary_ai_model or "GPT-4o Mini (유료, 저렴)"

            logger.info(f"정보요약 AI 호출 ({context}) - Provider: {summary_provider}, Model: {summary_ui_model}")

            # UI 모델명을 기술적 모델명으로 변환
            technical_model = self._map_ui_model_to_technical_name(summary_ui_model)

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

            return response.strip()

        except BusinessError:
            raise
        except Exception as e:
            logger.error(f"정보요약 AI 호출 실패 ({context}): {e}")
            raise BusinessError(f"정보요약 AI 처리 중 오류가 발생했습니다: {str(e)}")

    def generate_content_summary(self, content: str, main_keyword: str = "", content_type: str = "정보/가이드형") -> str:
        """정보요약 AI를 사용하여 블로그 콘텐츠 요약"""
        try:
            logger.info(f"정보요약 AI를 사용한 콘텐츠 요약 시작 - 키워드: {main_keyword}")

            # ai_prompts.py에서 1차 가공 프롬프트 생성
            from .ai_prompts import BlogSummaryPrompts
            summary_prompt = BlogSummaryPrompts.generate_content_summary_prompt(content, main_keyword, content_type)

            messages = [{"role": "user", "content": summary_prompt}]

            # 공용 정보요약 AI 호출
            response = self._call_summary_ai(messages, "콘텐츠 요약")

            logger.info(f"콘텐츠 요약 완료: {len(response)}자")
            return response
                
        except BusinessError:
            # BusinessError는 그대로 재발생
            raise
        except Exception as e:
            logger.error(f"콘텐츠 요약 실패: {e}")
            raise BusinessError(f"정보요약 AI 처리 중 오류가 발생했습니다: {str(e)}")

    def generate_titles_with_summary_ai(self, prompt: str, main_keyword: str, content_type: str) -> list:
        """정보요약 AI를 사용하여 제목 추천 (사용자 설정 AI 사용)"""
        try:
            logger.info(f"정보요약 AI를 사용한 제목 추천 시작 - 키워드: {main_keyword}")

            # 공용 정보요약 AI 호출
            messages = [{"role": "user", "content": prompt}]
            response = self._call_summary_ai(messages, "제목 추천")

            # JSON 응답 파싱하여 제목 리스트 추출
            import json

            # 마크다운 코드 블록 제거 (```json...``` 또는 ```...```)
            cleaned_response = response.strip()
            if cleaned_response.startswith('```'):
                # 첫번째 ```와 마지막 ``` 제거
                lines = cleaned_response.split('\n')
                if len(lines) > 2 and lines[0].startswith('```') and lines[-1].strip() == '```':
                    cleaned_response = '\n'.join(lines[1:-1])
                elif len(lines) > 1 and lines[0].startswith('```'):
                    # 마지막 ```가 별도 라인에 없는 경우
                    cleaned_response = '\n'.join(lines[1:])
                    if cleaned_response.endswith('```'):
                        cleaned_response = cleaned_response[:-3]

            try:
                result = json.loads(cleaned_response.strip())

                # 새로운 JSON 구조 처리 (제목 + 검색어)
                if isinstance(result, dict) and "titles_with_search" in result:
                    titles_data = result["titles_with_search"]
                    if isinstance(titles_data, list) and len(titles_data) > 0:
                        # 제목과 검색어가 함께 있는 구조
                        clean_data = []
                        for item in titles_data[:10]:  # 최대 10개
                            if isinstance(item, dict) and "title" in item and "search_query" in item:
                                title = str(item["title"]).strip()
                                search_query = str(item["search_query"]).strip()
                                if title and search_query:
                                    clean_data.append({
                                        "title": title,
                                        "search_query": search_query
                                    })

                        if clean_data:
                            logger.info(f"제목 추천 완료: {len(clean_data)}개 (제목+검색어)")
                            return clean_data

                # 기존 JSON 구조 처리 (제목만)
                elif isinstance(result, dict) and "titles" in result:
                    titles = result["titles"]
                elif isinstance(result, list):
                    titles = result
                else:
                    # JSON이 아닌 경우 문자열에서 제목 추출 시도
                    titles = self._extract_titles_from_text(response)

                # 기존 제목 리스트 검증 및 정리 (하위 호환성)
                if isinstance(titles, list) and len(titles) > 0:
                    # 문자열만 추출하고 빈 값 제거
                    clean_titles = [str(title).strip() for title in titles if str(title).strip()]
                    logger.info(f"제목 추천 완료: {len(clean_titles)}개 (제목만)")
                    return clean_titles[:10]  # 최대 10개
                else:
                    logger.warning("유효한 제목이 추출되지 않음")
                    return []

            except json.JSONDecodeError:
                logger.warning("JSON 파싱 실패, 텍스트에서 제목 추출 시도")
                titles = self._extract_titles_from_text(response)
                return titles[:10] if titles else []

        except Exception as e:
            logger.error(f"제목 추천 AI 처리 실패: {e}")
            raise BusinessError(f"제목 추천 생성 실패: {e}")

    def _extract_titles_from_text(self, text: str) -> list:
        """텍스트에서 제목 리스트 추출 (JSON 파싱 실패시 폴백)"""
        try:
            titles = []
            lines = text.strip().split('\n')

            for line in lines:
                line = line.strip()
                # 번호나 기호로 시작하는 라인에서 제목 추출
                if line and (
                    line[0].isdigit() or
                    line.startswith('-') or
                    line.startswith('•') or
                    line.startswith('*')
                ):
                    # 번호나 기호 제거
                    clean_title = line
                    for prefix in ['1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.', '-', '•', '*']:
                        if clean_title.startswith(prefix):
                            clean_title = clean_title[len(prefix):].strip()
                            break

                    if clean_title:
                        titles.append(clean_title)

            return titles[:10]  # 최대 10개

        except Exception as e:
            logger.error(f"텍스트에서 제목 추출 실패: {e}")
            return []

    def select_blog_titles_with_ai(self, target_title: str, search_keyword: str, main_keyword: str, content_type: str, blog_titles: List[str]) -> List[Dict]:
        """AI를 사용하여 블로그 제목들 중 관련도 높은 상위 10개 선별"""
        try:
            logger.info(f"AI 블로그 제목 선별 시작 - 대상: {len(blog_titles)}개 제목")

            # ai_prompts.py에서 제목 선별 프롬프트 생성
            from .ai_prompts import BlogPromptComponents
            selection_prompt = BlogPromptComponents.generate_blog_title_selection_prompt(
                target_title, search_keyword, main_keyword, content_type, blog_titles
            )

            # 정보요약 AI를 사용하여 제목 선별 (기존 API 재사용)
            messages = [{"role": "user", "content": selection_prompt}]
            response = self._call_summary_ai(messages, "블로그 제목 선별")

            # JSON 응답 파싱
            import json

            # 마크다운 코드 블록 제거
            cleaned_response = response.strip()
            if cleaned_response.startswith('```'):
                lines = cleaned_response.split('\n')
                if len(lines) > 2 and lines[0].startswith('```') and lines[-1].strip() == '```':
                    cleaned_response = '\n'.join(lines[1:-1])
                elif len(lines) > 1 and lines[0].startswith('```'):
                    cleaned_response = '\n'.join(lines[1:])
                    if cleaned_response.endswith('```'):
                        cleaned_response = cleaned_response[:-3]

            try:
                result = json.loads(cleaned_response.strip())

                if isinstance(result, dict) and "selected_titles" in result:
                    selected_data = result["selected_titles"]
                    if isinstance(selected_data, list) and len(selected_data) > 0:
                        # 선별된 제목 데이터 검증 및 정리
                        clean_selections = []
                        for item in selected_data[:10]:  # 최대 10개
                            if isinstance(item, dict) and all(key in item for key in ["rank", "original_index", "title"]):
                                rank = item.get("rank", 0)
                                original_index = item.get("original_index", 0)
                                title = str(item.get("title", "")).strip()
                                reason = str(item.get("relevance_reason", "")).strip()

                                # 인덱스 유효성 검사 (1-based에서 0-based로 변환)
                                if 1 <= original_index <= len(blog_titles) and title:
                                    clean_selections.append({
                                        "rank": rank,
                                        "original_index": original_index - 1,  # 0-based로 변환
                                        "title": title,
                                        "relevance_reason": reason
                                    })

                        if clean_selections:
                            logger.info(f"AI 제목 선별 완료: {len(clean_selections)}개 선별됨")
                            return clean_selections

                logger.warning("AI 응답에서 유효한 제목 선별 결과를 찾을 수 없음")
                return []

            except json.JSONDecodeError as e:
                logger.warning(f"JSON 파싱 실패: {e}")
                return []

        except Exception as e:
            logger.error(f"AI 제목 선별 실패: {e}")
            raise BusinessError(f"AI 제목 선별 처리 실패: {str(e)}")

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
    
    def generate_blog_content_with_summary(self, main_keyword: str, sub_keywords: str, analyzed_blogs: list, content_type: str = "정보/가이드형", tone: str = "정중한 존댓말체", review_detail: str = "") -> str:
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
            summarized_content = self.generate_content_summary(combined_content, main_keyword, content_type)
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
                summary_result=summarized_content
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
    
    def generate_blog_content_with_summary_detailed(self, main_keyword: str, sub_keywords: str, analyzed_blogs: list, content_type: str = "정보/가이드형", tone: str = "정중한 존댓말체", review_detail: str = "") -> Dict[str, str]:
        """2단계 파이프라인: 정보요약 AI → 글작성 AI (상세 정보 포함)"""
        try:
            logger.info("2단계 파이프라인으로 블로그 콘텐츠 생성 시작 (상세 정보 포함)")
            
            # 1단계: 분석된 블로그들의 콘텐츠를 하나의 텍스트로 통합
            logger.info("1단계: 경쟁 블로그 콘텐츠 통합")
            combined_content = self._combine_blog_contents(analyzed_blogs)
            
            if not combined_content.strip():
                logger.warning("통합할 블로그 콘텐츠가 없습니다.")
                combined_content = "분석할 콘텐츠가 없습니다."
            
            logger.info(f"통합된 콘텐츠 길이: {len(combined_content)}자")
            
            # 2단계: 정보요약 AI로 콘텐츠 요약
            logger.info("2단계: 정보요약 AI로 콘텐츠 요약")
            
            # 기존 generate_content_summary 메서드 사용
            summarized_content = self.generate_content_summary(combined_content, main_keyword, content_type)
            
            # UI용 프롬프트 생성 (ai_prompts.py에서)
            from .ai_prompts import BlogSummaryPrompts
            summary_prompt = BlogSummaryPrompts.generate_content_summary_prompt(combined_content, main_keyword, content_type)
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
                summary_result=summarized_content
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
    
