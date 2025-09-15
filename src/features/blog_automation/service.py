"""
블로그 자동화 모듈의 비즈니스 로직 서비스
"""
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
        from .models import validate_and_create_credentials
        return validate_and_create_credentials(platform, username, password)
    
    def create_session(self, platform: BlogPlatform, username: str) -> BlogSession:
        """새 블로그 세션 생성"""
        from .models import create_blog_session
        session = create_blog_session(platform, username)
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
                from .models import save_blog_session
                save_blog_session(self.current_session)
            else:
                logger.error(f"블로그 로그인 실패: {login_status}")
            
            return success
            
        except Exception as e:
            logger.error(f"블로그 로그인 오류: {e}")
            if self.current_session:
                self.current_session.status = LoginStatus.LOGIN_FAILED
            raise BusinessError(f"로그인 실패: {str(e)}")
    
    
    def save_credentials(self, credentials: BlogCredentials):
        """로그인 자격증명 저장 (암호화)"""
        from .models import save_blog_credentials
        save_blog_credentials(credentials)
    
    def load_saved_credentials(self, platform: BlogPlatform) -> Optional[tuple]:
        """저장된 자격증명 로드"""
        from .models import load_saved_blog_credentials
        return load_saved_blog_credentials(platform)
    
    def delete_saved_credentials(self, platform: BlogPlatform, username: str):
        """저장된 자격증명 삭제"""
        from .models import delete_saved_blog_credentials
        delete_saved_blog_credentials(platform, username)
    
    
    def check_login_status(self) -> bool:
        """현재 로그인 상태 확인"""
        if not self.adapter:
            return False
            
        try:
            return self.adapter.check_login_status()
        except Exception as e:
            logger.error(f"로그인 상태 확인 실패: {e}")
            return False
    
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
            from .adapters import select_blog_titles_with_ai
            selected_titles = select_blog_titles_with_ai(
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

    




    
    def generate_blog_content_with_summary_detailed(self, main_keyword: str, sub_keywords: str, analyzed_blogs: list, content_type: str = "정보/가이드형", tone: str = "정중한 존댓말체", review_detail: str = "", search_keyword: str = "", selected_title: str = "") -> Dict[str, str]:
        """2단계 파이프라인: 정보요약 AI → 글작성 AI (상세 정보 포함)"""
        try:
            logger.info("2단계 파이프라인으로 블로그 콘텐츠 생성 시작 (상세 정보 포함)")
            
            # 분석 결과가 없는 경우 폴백 처리 - ai_prompts 직접 호출
            if not analyzed_blogs or len(analyzed_blogs) == 0:
                logger.warning("분석된 블로그가 없습니다. 분석 없이 AI 글쓰기로 진행")
                
                # 블로거 정체성 가져오기
                from src.foundation.config import config_manager
                api_config = config_manager.load_api_config()
                blogger_identity = getattr(api_config, 'ai_writing_blogger_identity', '')
                
                # ai_prompts 직접 호출로 빈 분석으로 프롬프트 생성
                from .ai_prompts import create_ai_request_data
                ai_data = create_ai_request_data(
                    main_keyword=main_keyword,
                    sub_keywords=sub_keywords,
                    analyzed_blogs=[],  # 빈 리스트
                    content_type=content_type,
                    tone=tone,
                    review_detail=review_detail,
                    blogger_identity=blogger_identity,
                    summary_result="경쟁 블로그 분석 결과가 없어 직접 작성합니다.",
                    selected_title=selected_title,
                    search_keyword=search_keyword
                )
                
                writing_prompt = ai_data.get('ai_prompt', '')
                from .adapters import blog_ai_adapter
                final_content = blog_ai_adapter.generate_blog_content(writing_prompt)
                
                return {
                    "summary_prompt": "분석 없음 - 직접 글쓰기",
                    "summary_result": "경쟁 블로그 분석 결과가 없어 생략됨",
                    "writing_prompt": writing_prompt,
                    "final_content": final_content,
                    "combined_content": "분석된 블로그 콘텐츠 없음"
                }

            # 1단계: 분석된 블로그들의 콘텐츠를 하나의 텍스트로 통합
            logger.info("1단계: 경쟁 블로그 콘텐츠 통합")
            from .ai_prompts import combine_blog_contents
            combined_content = combine_blog_contents(analyzed_blogs)

            if not combined_content.strip():
                logger.warning("통합할 블로그 콘텐츠가 없습니다. 분석 없이 진행")
                
                # 블로거 정체성 가져오기
                from src.foundation.config import config_manager
                api_config = config_manager.load_api_config()
                blogger_identity = getattr(api_config, 'ai_writing_blogger_identity', '')
                
                # ai_prompts 직접 호출로 빈 분석으로 프롬프트 생성
                from .ai_prompts import create_ai_request_data
                ai_data = create_ai_request_data(
                    main_keyword=main_keyword,
                    sub_keywords=sub_keywords,
                    analyzed_blogs=[],  # 빈 리스트
                    content_type=content_type,
                    tone=tone,
                    review_detail=review_detail,
                    blogger_identity=blogger_identity,
                    summary_result="경쟁 블로그 분석 결과가 없어 직접 작성합니다.",
                    selected_title=selected_title,
                    search_keyword=search_keyword
                )
                
                writing_prompt = ai_data.get('ai_prompt', '')
                from .adapters import blog_ai_adapter
                final_content = blog_ai_adapter.generate_blog_content(writing_prompt)
                
                return {
                    "summary_prompt": "분석 없음 - 직접 글쓰기",
                    "summary_result": "경쟁 블로그 분석 결과가 없어 생략됨",
                    "writing_prompt": writing_prompt,
                    "final_content": final_content,
                    "combined_content": "분석된 블로그 콘텐츠 없음"
                }

            logger.info(f"통합된 콘텐츠 길이: {len(combined_content)}자")

            # 2단계: 정보요약 AI로 콘텐츠 요약
            logger.info("2단계: 정보요약 AI로 콘텐츠 요약")

            # 요약 내용 생성
            from .adapters import generate_content_summary
            summarized_content = generate_content_summary(combined_content, main_keyword, content_type, search_keyword)

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
            
            # 블로거 정체성 가져오기
            from src.foundation.config import config_manager
            api_config = config_manager.load_api_config()
            blogger_identity = getattr(api_config, 'ai_writing_blogger_identity', '')
            
            # ai_prompts(engine_local)를 직접 호출 - CLAUDE.md 구조 준수
            from .ai_prompts import create_ai_request_data
            ai_data = create_ai_request_data(
                main_keyword=main_keyword,
                sub_keywords=sub_keywords,
                analyzed_blogs=analyzed_blogs,
                content_type=content_type,
                tone=tone,
                review_detail=review_detail,
                blogger_identity=blogger_identity,
                summary_result=summarized_content,
                selected_title=selected_title,
                search_keyword=search_keyword
            )
            
            enhanced_prompt = ai_data.get('ai_prompt', '')

            # 글작성 AI로 최종 콘텐츠 생성
            from .adapters import blog_ai_adapter
            final_content = blog_ai_adapter.generate_blog_content(enhanced_prompt)
            
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
    
    def save_ai_writing_settings(self, settings: dict) -> None:
        """AI 글쓰기 설정 저장"""
        try:
            from src.foundation.config import config_manager
            api_config = config_manager.load_api_config()
            
            # AI 글쓰기 설정 저장
            api_config.ai_writing_content_type = settings.get('content_type', '정보/가이드형')
            api_config.ai_writing_content_type_id = settings.get('content_type_id', 1)
            api_config.ai_writing_tone = settings.get('tone', '정중한 존댓말체')
            api_config.ai_writing_tone_id = settings.get('tone_id', 1)
            api_config.ai_writing_blogger_identity = settings.get('blogger_identity', '')
            
            # 후기 세부 옵션이 있는 경우 추가
            if 'review_detail' in settings:
                api_config.ai_writing_review_detail = settings['review_detail']
                api_config.ai_writing_review_detail_id = settings.get('review_detail_id', 0)
            
            # 설정 저장
            config_manager.save_api_config(api_config)
            
            logger.info(f"AI 글쓰기 설정 저장됨: {settings.get('content_type')}, {settings.get('tone')}")
            
        except Exception as e:
            logger.error(f"AI 글쓰기 설정 저장 실패: {e}")
            raise BusinessError(f"AI 설정 저장 실패: {str(e)}")
    
    def load_ai_writing_settings(self) -> dict:
        """저장된 AI 글쓰기 설정 로드"""
        try:
            from src.foundation.config import config_manager
            api_config = config_manager.load_api_config()
            
            settings = {
                'content_type_id': getattr(api_config, 'ai_writing_content_type_id', 1),
                'tone_id': getattr(api_config, 'ai_writing_tone_id', 1),
                'blogger_identity': getattr(api_config, 'ai_writing_blogger_identity', ''),
                'review_detail_id': getattr(api_config, 'ai_writing_review_detail_id', 0),
                'content_type': getattr(api_config, 'ai_writing_content_type', '정보/가이드형'),
                'tone': getattr(api_config, 'ai_writing_tone', '정중한 존댓말체'),
                'review_detail': getattr(api_config, 'ai_writing_review_detail', '내돈내산 후기')
            }
            
            logger.info(f"AI 글쓰기 설정 로드됨: {settings['content_type']}, {settings['tone']}")
            return settings
            
        except Exception as e:
            logger.error(f"AI 글쓰기 설정 로드 실패: {e}")
            # 기본값 반환
            return {
                'content_type_id': 1,
                'tone_id': 1,  
                'blogger_identity': '',
                'review_detail_id': 0,
                'content_type': '정보/가이드형',
                'tone': '정중한 존댓말체',
                'review_detail': '내돈내산 후기'
            }
    
    def generate_title_suggestions(self, main_keyword: str, sub_keywords: str = "", content_type: str = "정보/가이드형", review_detail: str = "") -> str:
        """제목 추천 AI 프롬프트 생성 (UI에서 호출용)"""
        try:
            from .ai_prompts import BlogPromptComponents
            
            prompt = BlogPromptComponents.generate_title_suggestion_prompt(
                main_keyword=main_keyword,
                content_type=content_type,
                sub_keywords=sub_keywords,
                review_detail=review_detail
            )
            
            logger.info(f"제목 추천 프롬프트 생성 완료: {main_keyword}, {content_type}")
            return prompt
            
        except Exception as e:
            logger.error(f"제목 추천 프롬프트 생성 실패: {e}")
            raise BusinessError(f"제목 추천 실패: {str(e)}")
    
    def call_summary_ai(self, prompt: str, response_format: str = "text", context: str = "요약") -> Any:
        """AI 요약 서비스 호출 (어댑터를 통해)"""
        try:
            from .adapters import blog_ai_adapter
            result = blog_ai_adapter.call_summary_ai(prompt, response_format, context)
            logger.info(f"AI 요약 호출 완료: {context}")
            return result
            
        except Exception as e:
            logger.error(f"AI 요약 호출 실패 ({context}): {e}")
            raise BusinessError(f"AI 요약 실패: {str(e)}")
    
    def generate_ui_prompt_for_display(self, main_keyword: str, sub_keywords: str, analyzed_blogs: list, content_type: str = "정보/가이드형", tone: str = "정중한 존댓말체", review_detail: str = "", selected_title: str = "", search_keyword: str = "", summary_result: str = "") -> Dict[str, Any]:
        """UI 표시용 AI 프롬프트 생성 (create_ai_request_data와 동일한 기능)"""
        try:
            # 블로거 정체성 가져오기
            from src.foundation.config import config_manager
            api_config = config_manager.load_api_config()
            blogger_identity = getattr(api_config, 'ai_writing_blogger_identity', '')
            
            # ai_prompts(engine_local)를 직접 호출
            from .ai_prompts import create_ai_request_data
            ai_data = create_ai_request_data(
                main_keyword=main_keyword,
                sub_keywords=sub_keywords,
                analyzed_blogs=analyzed_blogs,
                content_type=content_type,
                tone=tone,
                review_detail=review_detail,
                blogger_identity=blogger_identity,
                summary_result=summary_result,
                selected_title=selected_title,
                search_keyword=search_keyword
            )
            
            logger.info(f"UI 표시용 AI 프롬프트 생성 완료: {main_keyword}")
            return ai_data
            
        except Exception as e:
            logger.error(f"UI 표시용 AI 프롬프트 생성 실패: {e}")
            raise BusinessError(f"UI 프롬프트 생성 실패: {str(e)}")
    
