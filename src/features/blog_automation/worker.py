"""
블로그 자동화 모듈의 워커 - 장시간 작업/비동기 처리
"""
import time
import threading
from typing import Optional
from PySide6.QtCore import QObject, Signal

from src.foundation.logging import get_logger
from src.foundation.exceptions import BusinessError
from .models import BlogCredentials, LoginStatus
from .service import BlogAutomationService

logger = get_logger("blog_automation.worker")


class BlogLoginWorker(QObject):
    """블로그 로그인 워커 - 비동기 로그인 처리"""
    
    # 시그널 정의
    login_started = Signal()  # 로그인 시작
    login_completed = Signal(bool)  # 로그인 완료 (성공/실패)
    login_progress = Signal(str)  # 로그인 진행 상황
    error_occurred = Signal(str)  # 오류 발생
    two_factor_detected = Signal()  # 2차 인증 감지
    
    def __init__(self, service: BlogAutomationService, credentials: BlogCredentials):
        super().__init__()
        self.service = service
        self.credentials = credentials
        self.is_cancelled = False
        
    def run(self):
        """로그인 작업 실행"""
        try:
            logger.info("🔑 블로그 로그인 워커 시작")
            self.login_started.emit()
            
            # 2차 인증 감지를 위한 별도 스레드 시작
            two_factor_monitor = threading.Thread(
                target=self._monitor_two_factor_auth,
                daemon=True
            )
            two_factor_monitor.start()
            
            # 로그인 진행 상황 업데이트
            self.login_progress.emit("브라우저 시작 중...")
            
            # 실제 로그인 수행
            success = self.service.login(self.credentials)
            
            # 2차 인증 모니터링 종료
            self._stop_two_factor_monitoring = True
            
            if not self.is_cancelled:
                self.login_completed.emit(success)
                if success:
                    logger.info("✅ 블로그 로그인 워커 완료: 성공")
                else:
                    logger.info("❌ 블로그 로그인 워커 완료: 실패")
            
        except Exception as e:
            logger.error(f"❌ 블로그 로그인 워커 오류: {e}")
            if not self.is_cancelled:
                self.error_occurred.emit(str(e))
    
    def _monitor_two_factor_auth(self):
        """2차 인증 상태를 실시간으로 모니터링"""
        self._stop_two_factor_monitoring = False
        two_factor_already_detected = False
        
        while not self._stop_two_factor_monitoring and not self.is_cancelled:
            try:
                # 어댑터가 생성되고 2차 인증이 감지되었는지 확인
                if (hasattr(self.service, 'adapter') and 
                    self.service.adapter and 
                    hasattr(self.service.adapter, 'two_factor_auth_detected') and
                    self.service.adapter.two_factor_auth_detected and
                    not two_factor_already_detected):
                    
                    logger.info("🔐 2차 인증 실시간 감지!")
                    self.two_factor_detected.emit()
                    self.login_progress.emit("2차 인증 진행 중... 브라우저에서 인증을 완료해주세요")
                    two_factor_already_detected = True
                
                time.sleep(1)  # 1초마다 체크
                
            except Exception as e:
                logger.debug(f"2차 인증 모니터링 오류: {e}")
                time.sleep(1)
    
    def cancel(self):
        """워커 취소"""
        self.is_cancelled = True
        self._stop_two_factor_monitoring = True
        logger.info("블로그 로그인 워커 취소됨")


class WorkerThread:
    """워커 스레드 관리 클래스"""
    
    def __init__(self, worker):
        self.worker = worker
        self.thread = None
        
    def start(self):
        """워커 스레드 시작"""
        self.thread = threading.Thread(target=self.worker.run, daemon=True)
        self.thread.start()
        
    def quit(self):
        """스레드 종료 (워커 취소)"""
        if self.worker:
            self.worker.cancel()
            
    def wait(self, timeout=5):
        """스레드 종료 대기"""
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=timeout)


class BlogAnalysisWorker(QObject):
    """블로그 분석 워커 - 상위 블로그 분석 처리"""
    
    # 시그널 정의
    analysis_started = Signal()  # 분석 시작
    analysis_progress = Signal(str, int)  # 분석 진행 상황 (메시지, 진행률)
    analysis_completed = Signal(list)  # 분석 완료 (분석된 블로그 리스트)
    error_occurred = Signal(str)  # 오류 발생
    blog_found = Signal(int)  # 블로그 발견 (개수)
    
    def __init__(self, service: BlogAutomationService, keyword: str):
        super().__init__()
        self.service = service
        self.keyword = keyword
        self.is_cancelled = False
        
    def run(self):
        """블로그 분석 작업 실행"""
        try:
            logger.info(f"📊 블로그 분석 워커 시작: {self.keyword}")
            self.analysis_started.emit()
            
            # 진행 상황 업데이트
            self.analysis_progress.emit("키워드 검색 중...", 20)
            
            # 실제 블로그 분석 수행
            analyzed_blogs = self.service.analyze_top_blogs(self.keyword)
            
            if not self.is_cancelled:
                self.blog_found.emit(len(analyzed_blogs))
                self.analysis_progress.emit("분석 완료", 100)
                self.analysis_completed.emit(analyzed_blogs)
                logger.info(f"✅ 블로그 분석 워커 완료: {len(analyzed_blogs)}개 블로그")
            
        except Exception as e:
            logger.error(f"❌ 블로그 분석 워커 오류: {e}")
            if not self.is_cancelled:
                self.error_occurred.emit(str(e))
    
    def cancel(self):
        """워커 취소"""
        self.is_cancelled = True
        logger.info("블로그 분석 워커 취소됨")


class AIWritingWorker(QObject):
    """AI 블로그 글쓰기 워커 - AI API 호출 처리"""
    
    # 시그널 정의
    writing_started = Signal()  # 글쓰기 시작
    writing_completed = Signal(str)  # 글쓰기 완료 (생성된 콘텐츠)
    error_occurred = Signal(str)  # 오류 발생
    
    def __init__(self, service: BlogAutomationService, keyword: str, structured_data: dict):
        super().__init__()
        self.service = service
        self.keyword = keyword
        self.structured_data = structured_data
        self.is_cancelled = False
        
    def run(self):
        """AI 글쓰기 작업 실행"""
        try:
            logger.info(f"🤖 AI 글쓰기 워커 시작: {self.keyword}")
            self.writing_started.emit()
            
            # AI 프롬프트 생성
            from .ai_prompts import BlogAIPrompts
            prompt = BlogAIPrompts.generate_naver_seo_prompt(self.keyword, self.structured_data)
            
            # AI API 호출
            generated_content = self.service.generate_blog_content(prompt)
            
            if not self.is_cancelled and generated_content:
                self.writing_completed.emit(generated_content)
                logger.info("✅ AI 글쓰기 워커 완료")
            elif not generated_content:
                self.error_occurred.emit("AI가 콘텐츠를 생성하지 못했습니다. API 키를 확인해주세요.")
            
        except Exception as e:
            logger.error(f"❌ AI 글쓰기 워커 오류: {e}")
            if not self.is_cancelled:
                self.error_occurred.emit(str(e))
    
    def cancel(self):
        """워커 취소"""
        self.is_cancelled = True
        logger.info("AI 글쓰기 워커 취소됨")


def create_blog_login_worker(service: BlogAutomationService, credentials: BlogCredentials) -> BlogLoginWorker:
    """블로그 로그인 워커 생성"""
    return BlogLoginWorker(service, credentials)


def create_blog_analysis_worker(service: BlogAutomationService, keyword: str) -> BlogAnalysisWorker:
    """블로그 분석 워커 생성"""
    return BlogAnalysisWorker(service, keyword)


def create_ai_writing_worker(service: BlogAutomationService, keyword: str, structured_data: dict) -> AIWritingWorker:
    """AI 글쓰기 워커 생성"""
    return AIWritingWorker(service, keyword, structured_data)