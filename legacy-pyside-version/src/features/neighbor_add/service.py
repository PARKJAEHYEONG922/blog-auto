"""
서로이웃 추가 모듈의 비즈니스 로직 서비스
"""
import time
import random
from typing import List, Optional, Tuple
from datetime import datetime
import uuid
import base64
import hashlib

from src.foundation.logging import get_logger
from src.foundation.db import get_db
from src.foundation.exceptions import BusinessError, ValidationError
from src.toolbox.text_utils import clean_keyword

from .models import (
    LoginCredentials, BloggerInfo, NeighborAddRequest, SearchKeyword,
    NeighborAddSession, LoginStatus, NeighborAddStatus, init_neighbor_db
)
from .adapters import create_naver_blog_adapter

logger = get_logger("neighbor_add.service")


class NeighborAddService:
    """서로이웃 추가 서비스"""
    
    def __init__(self):
        self.adapter = None
        self.current_session: Optional[NeighborAddSession] = None
        self._init_database()
    
    def _init_database(self):
        """데이터베이스 초기화"""
        try:
            with get_db().get_connection() as conn:
                init_neighbor_db(conn)
            logger.info("서로이웃 추가 데이터베이스 초기화 완료")
        except Exception as e:
            logger.error(f"데이터베이스 초기화 실패: {e}")
            raise BusinessError(f"데이터베이스 초기화 실패: {str(e)}")
    
    def force_stop_browser_session(self):
        """브라우저 세션 강제 중단"""
        try:
            if self.adapter and hasattr(self.adapter, 'helper') and self.adapter.helper:
                logger.info("🛑 브라우저 세션 강제 중단 시작")
                
                # SeleniumHelper의 cleanup 메서드 호출하여 브라우저 완전 종료
                self.adapter.helper.cleanup()
                
                # adapter 상태 초기화
                self.adapter.is_logged_in = False
                self.adapter.two_factor_auth_detected = False
                self.adapter.main_tab_handle = None
                self.adapter.neighbor_add_tab_handle = None
                
                logger.info("✅ 브라우저 세션 강제 중단 완료")
            else:
                logger.info("ℹ️ 중단할 브라우저 세션이 없음")
                
        except Exception as e:
            logger.error(f"❌ 브라우저 세션 강제 중단 중 오류: {e}")
            # 오류가 발생해도 adapter를 None으로 설정하여 재시작 가능하도록 함
            self.adapter = None
    
    def create_session(self, default_message: str = "안녕하세요! 서로이웃 해요 :)") -> NeighborAddSession:
        """새 세션 생성"""
        try:
            session_id = str(uuid.uuid4())
            
            # 메시지 유효성 검증
            if not default_message or not default_message.strip():
                default_message = "안녕하세요! 서로이웃 해요 :)"
            
            cleaned_message = clean_keyword(default_message)
            if len(cleaned_message) > 200:
                raise ValidationError("서로이웃 메시지는 200자 이하여야 합니다")
            
            session = NeighborAddSession(
                session_id=session_id,
                default_message=cleaned_message
            )
            
            # 데이터베이스에 세션 저장
            with get_db().get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO neighbor_sessions 
                    (session_id, login_status, default_message, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    session.session_id,
                    session.login_status.value,
                    session.default_message,
                    session.created_at,
                    session.created_at
                ))
                conn.commit()
            
            self.current_session = session
            logger.info(f"새 세션 생성: {session_id}")
            return session
            
        except Exception as e:
            logger.error(f"세션 생성 실패: {e}")
            raise BusinessError(f"세션 생성 실패: {str(e)}")
    
    def validate_credentials(self, username: str, password: str) -> LoginCredentials:
        """로그인 정보 유효성 검증"""
        if not username or not username.strip():
            raise ValidationError("아이디를 입력해주세요")
        
        if not password or not password.strip():
            raise ValidationError("비밀번호를 입력해주세요")
        
        username = username.strip()
        
        # 아이디 형식 검증 (영문, 숫자, _, - 허용)
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            raise ValidationError("아이디는 영문, 숫자, _, -만 사용 가능합니다")
        
        if len(username) < 3 or len(username) > 20:
            raise ValidationError("아이디는 3-20자 사이여야 합니다")
        
        if len(password) < 4:
            raise ValidationError("비밀번호는 4자 이상이어야 합니다")
        
        return LoginCredentials(username=username, password=password)
    
    def validate_search_keyword(self, keyword: str, max_results: int = 50) -> SearchKeyword:
        """검색 키워드 유효성 검증"""
        if not keyword or not keyword.strip():
            raise ValidationError("검색 키워드를 입력해주세요")
        
        cleaned_keyword = clean_keyword(keyword)
        
        if len(cleaned_keyword) < 2:
            raise ValidationError("검색 키워드는 2자 이상이어야 합니다")
        
        if len(cleaned_keyword) > 50:
            raise ValidationError("검색 키워드는 50자 이하여야 합니다")
        
        if max_results < 1 or max_results > 200:
            raise ValidationError("검색 결과 수는 1-200 사이여야 합니다")
        
        return SearchKeyword(keyword=cleaned_keyword, max_results=max_results)
    
    async def login_async(self, credentials: LoginCredentials) -> bool:
        """네이버 로그인 (비동기 처리)"""
        try:
            if not self.current_session:
                raise BusinessError("세션이 생성되지 않았습니다")
            
            logger.info(f"🔑 비동기 로그인 시작: {credentials.username}")
            self.current_session.login_status = LoginStatus.LOGGING_IN
            self._update_session_status()
            
            # 기존 어댑터 정리
            if self.adapter:
                try:
                    self.adapter.close_browser()
                except:
                    pass
            
            # 어댑터 생성 및 브라우저 시작 (비동기 처리)
            logger.info("어댑터 생성 중...")
            import asyncio
            await asyncio.sleep(0.1)  # 비동기 처리 포인트
            
            self.adapter = create_naver_blog_adapter()
            
            logger.info("브라우저 시작 중...")
            await asyncio.sleep(0.2)  # 브라우저 시작 대기
            self.adapter.start_browser()
            
            logger.info("로그인 시도 중...")
            success = self.adapter.login_naver(credentials)
            
            if success:
                self.current_session.login_status = LoginStatus.LOGGED_IN
                logger.info("✅ 비동기 로그인 성공")
            else:
                self.current_session.login_status = LoginStatus.LOGIN_FAILED
                logger.error("❌ 비동기 로그인 실패")
            
            self._update_session_status()
            return success
            
        except Exception as e:
            if self.current_session:
                self.current_session.login_status = LoginStatus.LOGIN_FAILED
                self._update_session_status()
            
            logger.error(f"❌ 비동기 로그인 중 오류: {e}")
            import traceback
            logger.error(f"상세 오류:\n{traceback.format_exc()}")
            raise BusinessError(f"비동기 로그인 실패: {str(e)}")
    
    def login(self, credentials: LoginCredentials) -> bool:
        """네이버 로그인 (동기 처리로 단순화) - 호환성 유지"""
        try:
            if not self.current_session:
                raise BusinessError("세션이 생성되지 않았습니다")
            
            logger.info(f"🔑 로그인 시작: {credentials.username}")
            self.current_session.login_status = LoginStatus.LOGGING_IN
            self._update_session_status()
            
            # 기존 어댑터 정리
            if self.adapter:
                try:
                    self.adapter.close_browser()
                except:
                    pass
            
            # 어댑터 생성 및 브라우저 시작
            logger.info("어댑터 생성 중...")
            self.adapter = create_naver_blog_adapter()
            
            logger.info("브라우저 시작 중...")
            self.adapter.start_browser()
            
            logger.info("로그인 시도 중...")
            success = self.adapter.login_naver(credentials)
            
            if success:
                self.current_session.login_status = LoginStatus.LOGGED_IN
                logger.info("✅ 로그인 성공")
            else:
                self.current_session.login_status = LoginStatus.LOGIN_FAILED
                logger.error("❌ 로그인 실패")
            
            self._update_session_status()
            return success
            
        except Exception as e:
            if self.current_session:
                self.current_session.login_status = LoginStatus.LOGIN_FAILED
                self._update_session_status()
            
            logger.error(f"❌ 로그인 중 오류: {e}")
            import traceback
            logger.error(f"상세 오류:\n{traceback.format_exc()}")
            raise BusinessError(f"로그인 실패: {str(e)}")
    
    def search_bloggers(self, search_keyword: SearchKeyword) -> List[BloggerInfo]:
        """키워드로 블로거 검색"""
        try:
            if not self.current_session:
                raise BusinessError("세션이 생성되지 않았습니다")
            
            if self.current_session.login_status != LoginStatus.LOGGED_IN:
                raise BusinessError("로그인이 필요합니다")
            
            if not self.adapter:
                raise BusinessError("브라우저가 시작되지 않았습니다")
            
            logger.info(f"블로거 검색 시작: {search_keyword.keyword}")
            
            # 로그인 상태 확인
            if not self.adapter.is_logged_in:
                raise BusinessError("네이버 블로그에 로그인해야 합니다. 먼저 로그인을 완료해주세요.")
            
            # 어댑터를 통해 블로거 검색 (동기식)
            bloggers = self.adapter.search_bloggers_by_keyword(
                search_keyword.keyword, 
                search_keyword.max_results
            )
            
            # 세션에 검색 결과 저장
            self.current_session.current_keyword = search_keyword
            self.current_session.found_bloggers = bloggers
            
            # 데이터베이스에 검색 결과 저장
            self._save_found_bloggers(bloggers)
            
            logger.info(f"블로거 검색 완료: {len(bloggers)}개 발견")
            return bloggers
            
        except Exception as e:
            logger.error(f"블로거 검색 중 오류: {e}")
            raise BusinessError(f"블로거 검색 실패: {str(e)}")
    
    def prepare_neighbor_add_requests(self, blogger_ids: List[str], message: str) -> List[NeighborAddRequest]:
        """서로이웃 추가 요청 준비 (worker에서 사용할 요청 객체 생성)"""
        try:
            if not self.current_session:
                raise BusinessError("세션이 생성되지 않았습니다")
            
            if self.current_session.login_status != LoginStatus.LOGGED_IN:
                raise BusinessError("로그인이 필요합니다")
            
            # 메시지 유효성 검증
            if not message or not message.strip():
                message = self.current_session.default_message
            
            cleaned_message = clean_keyword(message)
            if len(cleaned_message) > 200:
                raise ValidationError("서로이웃 메시지는 200자 이하여야 합니다")
            
            # 선택된 블로거들로 요청 객체 생성
            requests = []
            for blogger_id in blogger_ids:
                blogger_info = next(
                    (b for b in self.current_session.found_bloggers if b.blog_id == blogger_id),
                    None
                )
                if blogger_info:
                    request = NeighborAddRequest(
                        blogger_info=blogger_info,
                        message=cleaned_message,
                        status=NeighborAddStatus.PENDING
                    )
                    requests.append(request)
            
            if not requests:
                raise BusinessError("추가할 블로거가 선택되지 않았습니다")
            
            logger.info(f"서로이웃 추가 요청 준비 완료: {len(requests)}개")
            return requests
            
        except Exception as e:
            logger.error(f"서로이웃 추가 요청 준비 실패: {e}")
            raise BusinessError(f"서로이웃 추가 요청 준비 실패: {str(e)}")
    
    def save_completed_requests(self, completed_requests: List[NeighborAddRequest]):
        """완료된 요청들을 세션과 DB에 저장"""
        try:
            if self.current_session:
                # 세션에 요청 결과 저장
                self.current_session.neighbor_requests.extend(completed_requests)
                
                # 데이터베이스에 결과 저장
                self._save_neighbor_requests(completed_requests)
                
                logger.info(f"서로이웃 추가 결과 저장 완료: {len(completed_requests)}개")
            
        except Exception as e:
            logger.error(f"서로이웃 추가 결과 저장 실패: {e}")
    
    def validate_target_add_params(self, blogger_ids: List[str], message: str, target_success_count: int) -> str:
        """목표 달성형 서로이웃 추가 파라미터 검증"""
        try:
            if not self.current_session:
                raise BusinessError("세션이 생성되지 않았습니다")
            
            if self.current_session.login_status != LoginStatus.LOGGED_IN:
                raise BusinessError("로그인이 필요합니다")
            
            if not self.adapter:
                raise BusinessError("브라우저가 시작되지 않았습니다")
            
            # 메시지 유효성 검증
            if not message or not message.strip():
                message = self.current_session.default_message
            
            cleaned_message = clean_keyword(message)
            if len(cleaned_message) > 200:
                raise ValidationError("서로이웃 메시지는 200자 이하여야 합니다")
            
            if target_success_count < 1 or target_success_count > 200:
                raise ValidationError("목표 성공 수는 1-200 사이여야 합니다")
            
            logger.info(f"목표 달성형 서로이웃 추가 파라미터 검증 완료: {target_success_count}명 목표")
            return cleaned_message
            
        except Exception as e:
            logger.error(f"목표 달성형 서로이웃 추가 파라미터 검증 실패: {e}")
            raise BusinessError(f"목표 달성형 서로이웃 추가 파라미터 검증 실패: {str(e)}")
    
    def add_neighbors_batch_until_target(self, blogger_ids: List[str], message: str, 
                                               target_success_count: int = 50, delay_seconds: int = 3) -> List[NeighborAddRequest]:
        """목표 달성형 서로이웃 추가 (worker에서 실제 처리)"""
        try:
            # 파라미터 검증
            cleaned_message = self.validate_target_add_params(blogger_ids, message, target_success_count)
            
            # worker.py에서 실제 처리해야 하지만 일단 간단 구현
            logger.info(f"목표 달성형 서로이웃 추가: {target_success_count}명 목표")
            
            # 임시로 기본 배치 처리 방식 사용
            requests = self.prepare_neighbor_add_requests(blogger_ids, message)
            
            # 간단한 순차 처리 (추후 worker로 개선 필요)
            completed_requests = []
            success_count = 0
            
            for request in requests:
                if success_count >= target_success_count:
                    break
                    
                try:
                    result = self.adapter.add_neighbor(request.blogger_info, request.message)
                    
                    if result == True:
                        request.status = NeighborAddStatus.SUCCESS  
                        success_count += 1
                    elif result == "disabled":
                        request.status = NeighborAddStatus.DISABLED
                        request.error_message = "서로이웃 추가 비활성화"
                    elif result == "neighbor_limit_exceeded":
                        request.status = NeighborAddStatus.NEIGHBOR_LIMIT_EXCEEDED
                        request.error_message = "상대방 이웃수 5000명 초과"
                    elif result == "already_requested":
                        request.status = NeighborAddStatus.ALREADY_REQUESTED
                        request.error_message = "이미 서로이웃 신청 진행 중"
                    else:
                        request.status = NeighborAddStatus.FAILED
                        request.error_message = "서로이웃 추가 실패"
                    
                    completed_requests.append(request)
                    
                    # 지연
                    time.sleep(delay_seconds)
                    
                except Exception as e:
                    logger.error(f"서로이웃 추가 실패: {e}")
                    request.status = NeighborAddStatus.FAILED
                    request.error_message = str(e)
                    completed_requests.append(request)
            
            # 결과 저장
            self.save_completed_requests(completed_requests)
            
            logger.info(f"목표 달성형 서로이웃 추가 완료: 성공 {success_count}/{target_success_count}")
            return completed_requests
            
        except Exception as e:
            logger.error(f"목표 달성형 서로이웃 추가 실패: {e}")
            raise BusinessError(f"목표 달성형 서로이웃 추가 실패: {str(e)}")

    def close_session(self):
        """세션 종료 및 리소스 정리 (동기 처리로 단순화)"""
        try:
            if self.adapter:
                self.adapter.close_browser()
                self.adapter = None
            
            if self.current_session:
                logger.info(f"세션 종료: {self.current_session.session_id}")
                self.current_session = None
            
        except Exception as e:
            logger.error(f"세션 종료 중 오류: {e}")
    
    def _update_session_status(self):
        """세션 상태 데이터베이스 업데이트"""
        if not self.current_session:
            return
        
        try:
            with get_db().get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE neighbor_sessions 
                    SET login_status = ?, updated_at = ?
                    WHERE session_id = ?
                """, (
                    self.current_session.login_status.value,
                    datetime.now(),
                    self.current_session.session_id
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"세션 상태 업데이트 실패: {e}")
    
    def _save_found_bloggers(self, bloggers: List[BloggerInfo]):
        """검색된 블로거 정보 데이터베이스 저장"""
        if not self.current_session:
            return
        
        try:
            with get_db().get_connection() as conn:
                cursor = conn.cursor()
                
                # 기존 데이터 삭제
                cursor.execute("DELETE FROM found_bloggers WHERE session_id = ?", 
                             (self.current_session.session_id,))
                
                # 새 데이터 저장
                for blogger in bloggers:
                    cursor.execute("""
                        INSERT OR IGNORE INTO found_bloggers 
                        (session_id, blog_id, blog_name, blog_url, profile_image_url, description)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        self.current_session.session_id,
                        blogger.blog_id,
                        blogger.blog_name,
                        blogger.blog_url,
                        blogger.profile_image_url,
                        blogger.description
                    ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"블로거 정보 저장 실패: {e}")
    
    def _save_neighbor_requests(self, requests: List[NeighborAddRequest]):
        """서로이웃 요청 결과 데이터베이스 저장"""
        if not self.current_session:
            return
        
        try:
            with get_db().get_connection() as conn:
                cursor = conn.cursor()
                
                for request in requests:
                    cursor.execute("""
                        INSERT OR REPLACE INTO neighbor_requests 
                        (session_id, blog_id, message, status, error_message, created_at, completed_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        self.current_session.session_id,
                        request.blogger_info.blog_id,
                        request.message,
                        request.status.value,
                        request.error_message,
                        request.created_at,
                        request.completed_at or datetime.now()
                    ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"서로이웃 요청 결과 저장 실패: {e}")
    
    
    def save_credentials(self, username: str, password: str) -> None:
        """로그인 정보 저장 (단순 저장)"""
        try:
            with get_db().get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO saved_credentials 
                    (username, password_encrypted, updated_at)
                    VALUES (?, ?, ?)
                """, (username, password, datetime.now()))  # 단순 저장
                conn.commit()
            
            logger.info(f"로그인 정보 저장 완료: {username}")
            
        except Exception as e:
            logger.error(f"로그인 정보 저장 실패: {e}")
            raise BusinessError(f"로그인 정보 저장 실패: {str(e)}")
    
    def load_saved_credentials(self) -> Optional[Tuple[str, str]]:
        """저장된 로그인 정보 로드"""
        try:
            with get_db().get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT username, password_encrypted 
                    FROM saved_credentials 
                    ORDER BY updated_at DESC 
                    LIMIT 1
                """)
                row = cursor.fetchone()
                
                if row:
                    username, password = row
                    logger.info(f"저장된 로그인 정보 로드: {username}")
                    return username, password  # 단순 반환
                
                return None
                
        except Exception as e:
            logger.error(f"저장된 로그인 정보 로드 실패: {e}")
            return None
    
    def delete_saved_credentials(self, username: str = None) -> None:
        """저장된 로그인 정보 삭제"""
        try:
            with get_db().get_connection() as conn:
                cursor = conn.cursor()
                if username:
                    cursor.execute("DELETE FROM saved_credentials WHERE username = ?", (username,))
                else:
                    cursor.execute("DELETE FROM saved_credentials")
                conn.commit()
            
            logger.info(f"저장된 로그인 정보 삭제: {username or '전체'}")
            
        except Exception as e:
            logger.error(f"저장된 로그인 정보 삭제 실패: {e}")
    
    def get_session_summary(self) -> dict:
        """현재 세션 요약 정보"""
        if not self.current_session:
            return {"session": None}
        
        return {
            "session_id": self.current_session.session_id,
            "login_status": self.current_session.login_status.value,
            "keyword": self.current_session.current_keyword.keyword if self.current_session.current_keyword else None,
            "found_bloggers_count": len(self.current_session.found_bloggers),
            "neighbor_requests_count": len(self.current_session.neighbor_requests),
            "success_count": len([r for r in self.current_session.neighbor_requests if r.status == NeighborAddStatus.SUCCESS]),
            "failed_count": len([r for r in self.current_session.neighbor_requests if r.status == NeighborAddStatus.FAILED])
        }
    
    def search_and_add_until_target(self, keyword: str, target_count: int, message: str = "", progress_callback=None) -> List[NeighborAddRequest]:
        """목표 달성까지 지속적 검색 및 서로이웃 추가"""
        try:
            logger.info(f"🎯 [서비스] search_and_add_until_target 시작: '{keyword}' {target_count}명 목표, 메시지='{message}'")
            
            if not self.current_session or self.current_session.login_status != LoginStatus.LOGGED_IN:
                raise BusinessError("로그인이 필요합니다")
            
            all_requests = []
            success_count = 0
            failed_count = 0
            disabled_count = 0
            already_count = 0
            total_searched = 0
            
            # 성공률을 고려한 검색 크기 계산 (성공률 30% 가정)
            success_rate = 0.3
            safety_margin = 1.5  # 추가 안전 마진
            
            # 초기 검색 크기: 목표의 4-5배 정도
            batch_size = max(20, int(target_count / success_rate * safety_margin))
            batch_size = min(batch_size, 100)  # 최대 100개로 제한
            
            # 재검색 크기: 목표의 2-3배 정도
            retry_batch_size = max(10, int(target_count / success_rate))
            retry_batch_size = min(retry_batch_size, 50)  # 최대 50개로 제한
            
            logger.info(f"📊 목표 {target_count}명 → 초기 검색: {batch_size}개, 재검색: {retry_batch_size}개 (성공률 {success_rate*100}% 가정)")
            
            # 서로이웃 추가 탭 생성
            if not self.adapter.create_neighbor_add_tab():
                raise BusinessError("서로이웃 추가 탭 생성에 실패했습니다")
            
            while success_count < target_count:
                # 1. 블로거 검색 (메인 탭에서 - 명시적 탭 전환)
                logger.info(f"🔍 메인 탭으로 전환하여 블로거 검색 중...")
                self.adapter.switch_to_main_tab()  # 명시적 메인 탭 전환
                
                # 검색 단계 진행률 업데이트 (상세 정보 포함)
                if progress_callback:
                    progress_callback(success_count, f"'{keyword}' 키워드 블로거 검색 중... (현재 성공: {success_count}/{target_count})", 
                                    extracted_ids=total_searched, stage="search")
                
                if total_searched == 0:
                    # 첫 번째 검색
                    search_keyword = SearchKeyword(keyword=keyword, max_results=batch_size)
                    bloggers = self.search_bloggers(search_keyword)
                    logger.info(f"✅ 메인 탭에서 초기 검색 완료: {len(bloggers)}명")
                else:
                    # 추가 검색 (부족한 인원에 비례하여 동적 계산)
                    remaining_needed = target_count - success_count
                    dynamic_batch_size = max(10, int(remaining_needed / success_rate * safety_margin))
                    dynamic_batch_size = min(dynamic_batch_size, 50)  # 최대 50개로 제한
                    
                    logger.info(f"📊 부족 인원 {remaining_needed}명 → 추가 검색: {dynamic_batch_size}개 (성공률 {success_rate*100}% 기준)")
                    
                    bloggers = self.adapter.search_more_bloggers_with_scroll(
                        keyword, total_searched, dynamic_batch_size
                    )
                    logger.info(f"✅ 메인 탭에서 추가 검색 완료: {len(bloggers)}명 (누적: {total_searched}명)")
                
                if not bloggers:
                    logger.warning(f"더 이상 검색할 블로거가 없습니다 (성공: {success_count}/{target_count})")
                    break
                
                total_searched += len(bloggers)
                
                # 검색 완료 진행률 업데이트
                if progress_callback:
                    progress_callback(success_count, f"블로거 {len(bloggers)}명 검색 완료 - 서로이웃 추가 시작...", 
                                    extracted_ids=total_searched, stage="search_complete")
                
                # 2. 서로이웃 추가 시도 (전용 탭에서 - 명시적 탭 전환)
                logger.info(f"🤝 서로이웃 추가 탭으로 전환하여 추가 작업 시작...")
                self.adapter.switch_to_neighbor_add_tab()  # 명시적 서로이웃 탭 전환
                
                for blogger in bloggers:
                    if success_count >= target_count:
                        logger.info(f"🎯 목표 달성! {success_count}/{target_count}명 완료")
                        break
                    
                    try:
                        # 서로이웃 추가 요청 생성
                        request = NeighborAddRequest(
                            blogger_info=blogger,
                            message=message,
                            status=NeighborAddStatus.PENDING
                        )
                        
                        # 서로이웃 추가 시도 (이미 전용 탭에 있음)
                        logger.debug(f"서로이웃 추가 탭에서 '{blogger.blog_name}' 처리 중...")
                        result = self.adapter.add_neighbor(blogger, message)
                        logger.info(f"🔍 [결과 확인] {blogger.blog_name} → result={result} (type: {type(result)})")
                        
                        # 결과 처리 및 실시간 통계 업데이트
                        logger.info(f"🔍 [결과 처리 전] 현재 통계: success={success_count}, failed={failed_count}, disabled={disabled_count}, already={already_count}")
                        if result == True:
                            request.status = NeighborAddStatus.SUCCESS
                            success_count += 1
                            logger.info(f"🎯 [SUCCESS 상태 설정] 성공 {success_count}/{target_count}: {blogger.blog_name} → status={request.status.value}")
                        elif result == "daily_limit_reached":
                            request.status = NeighborAddStatus.DAILY_LIMIT_REACHED
                            request.error_message = "하루 100명 제한 도달 - 더 이상 서로이웃 추가 불가"
                            all_requests.append(request)
                            logger.warning(f"🚫 하루 100명 제한 도달! 작업 중단: {blogger.blog_name}")
                            
                            # 진행률 콜백으로 제한 도달 알림
                            if progress_callback:
                                progress_callback(success_count, f"하루 100명 제한 도달 - 작업이 중단되었습니다",
                                                extracted_ids=total_searched,
                                                success_count=success_count,
                                                failed_count=failed_count,
                                                disabled_count=disabled_count,
                                                already_count=already_count,
                                                current_blogger=blogger.blog_name,
                                                stage="daily_limit_reached")
                            
                            # 하루 제한 도달시 즉시 전체 작업 중단
                            break
                        elif result == "disabled":
                            request.status = NeighborAddStatus.DISABLED
                            request.error_message = "서로이웃 추가 비활성화"
                            disabled_count += 1
                            logger.debug(f"🚫 비활성화: {blogger.blog_name}")
                        elif result == "neighbor_limit_exceeded":
                            request.status = NeighborAddStatus.NEIGHBOR_LIMIT_EXCEEDED
                            request.error_message = "상대방 이웃수 5000명 초과"
                            disabled_count += 1  # disabled_count에 포함
                            logger.debug(f"🚫 5000명 초과: {blogger.blog_name}")
                        elif result == "already_requested":
                            request.status = NeighborAddStatus.ALREADY_REQUESTED
                            request.error_message = "이미 서로이웃 신청 진행 중"
                            already_count += 1
                            logger.debug(f"🔄 이미 요청됨: {blogger.blog_name}")
                        else:
                            request.status = NeighborAddStatus.FAILED
                            request.error_message = "서로이웃 추가 실패"
                            failed_count += 1
                            logger.debug(f"❌ 실패: {blogger.blog_name}")
                        
                        # daily_limit_reached는 이미 위에서 append했으므로 여기서는 제외
                        if result != "daily_limit_reached":
                            all_requests.append(request)
                        
                        # 진행률 콜백 호출 (상세 상황판 정보 포함)
                        logger.info(f"🔍 [결과 처리 후] 최종 통계: success={success_count}, failed={failed_count}, disabled={disabled_count}, already={already_count}")
                        if progress_callback:
                            logger.debug(f"서비스 통계: success={success_count}, failed={failed_count}, disabled={disabled_count}, already={already_count}")
                            logger.info(f"🔍 [콜백 호출] UI에 전달할 통계: success_count={success_count}, failed_count={failed_count}, disabled_count={disabled_count}, already_count={already_count}")
                            progress_callback(success_count, f"'{blogger.blog_name}' 처리 완료 - 성공 {success_count}/{target_count}",
                                            extracted_ids=total_searched,
                                            success_count=success_count,
                                            failed_count=failed_count,
                                            disabled_count=disabled_count,
                                            already_count=already_count,
                                            current_blogger=blogger.blog_name,
                                            stage="add")
                        
                        # 랜덤 대기 (0.3~1.2초) - 자연스러운 패턴
                        delay = random.uniform(0.3, 1.2)
                        time.sleep(delay)
                        logger.debug(f"⏱️ 랜덤 대기: {delay:.2f}초")
                        
                    except Exception as e:
                        logger.error(f"서로이웃 추가 오류: {blogger.blog_id} - {e}")
                        request.status = NeighborAddStatus.FAILED
                        request.error_message = str(e)
                        all_requests.append(request)
                
                # 목표 달성 확인
                if success_count >= target_count:
                    logger.info(f"🎯 목표 달성! {success_count}명 성공")
                    break
                
                logger.info(f"현재 진행상황: 성공 {success_count}/{target_count}, 검색됨 {total_searched}명")
            
            # 결과 저장
            self.save_completed_requests(all_requests)
            
            logger.info(f"🎯 [서비스] search_and_add_until_target 완료: 성공 {success_count}/{target_count}명 (총 시도: {len(all_requests)}개)")
            
            # 최종 상태 분석 로그
            final_status = {}
            for req in all_requests:
                status = req.status.value if hasattr(req.status, 'value') else str(req.status) 
                final_status[status] = final_status.get(status, 0) + 1
            logger.info(f"🎯 [서비스] 최종 상태 분석: {final_status}")
            
            return all_requests
            
        except Exception as e:
            logger.error(f"목표 달성형 서로이웃 추가 실패: {e}")
            raise BusinessError(f"목표 달성형 서로이웃 추가 실패: {str(e)}")
    
