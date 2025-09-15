"""
서로이웃 추가 모듈의 워커 - 장시간 작업/비동기 처리
"""
import asyncio
import random
from typing import List, Optional, Callable
from dataclasses import dataclass
from PySide6.QtCore import QThread, QObject, Signal
from PySide6.QtWidgets import QApplication

from src.foundation.logging import get_logger
from src.foundation.exceptions import BusinessError
from src.toolbox.progress import calc_percentage
from .models import SearchKeyword, BloggerInfo, NeighborAddRequest
from .service import NeighborAddService

logger = get_logger("neighbor_add.worker")


@dataclass
class WorkerProgress:
    """워커 진행률 정보"""
    current: int = 0
    total: int = 0
    message: str = ""
    stage: str = ""  # "search", "add", "complete"
    
    # 상황판 업데이트를 위한 추가 정보
    extracted_ids: int = 0  # 추출된 ID 개수
    success_count: int = 0  # 성공한 서로이웃 추가 수
    failed_count: int = 0   # 실패한 서로이웃 추가 수
    disabled_count: int = 0  # 비활성화된 계정 수
    already_count: int = 0   # 이미 신청된 계정 수
    current_blogger: str = ""  # 현재 처리 중인 블로거명
    
    @property
    def percentage(self) -> float:
        """진행률 퍼센트 계산"""
        return calc_percentage(self.current, self.total)


class LoginWorker(QObject):
    """로그인 워커"""
    
    # 시그널 정의
    login_completed = Signal(bool)  # success/failure
    error_occurred = Signal(str)
    two_factor_detected = Signal()  # 2차 인증 감지
    
    def __init__(self, service: NeighborAddService, credentials):
        super().__init__()
        self.service = service
        self.credentials = credentials
        self.is_cancelled = False
        
    def run(self):
        """로그인 작업 실행"""
        try:
            logger.info("🔑 로그인 워커 시작")
            
            # 2차 인증 감지를 위한 스레드 생성
            import threading
            two_factor_detected = threading.Event()
            two_factor_thread = threading.Thread(
                target=self._monitor_two_factor_auth,
                args=(two_factor_detected,)
            )
            two_factor_thread.daemon = True
            two_factor_thread.start()
            
            # 동기 로그인 실행
            success = self.service.login(self.credentials)
            
            # 2차 인증 모니터링 종료
            two_factor_detected.set()
            
            if not self.is_cancelled:
                self.login_completed.emit(success)
                logger.info(f"로그인 워커 완료: {'성공' if success else '실패'}")
            
        except Exception as e:
            logger.error(f"❌ 로그인 워커 오류: {e}")
            if not self.is_cancelled:
                self.error_occurred.emit(str(e))
    
    def _monitor_two_factor_auth(self, stop_event):
        """2차 인증 상태를 실시간으로 모니터링"""
        two_factor_already_detected = False
        
        while not stop_event.is_set():
            try:
                # 2차 인증 상태 확인
                if (hasattr(self.service, 'adapter') and 
                    self.service.adapter and 
                    hasattr(self.service.adapter, 'two_factor_auth_detected') and
                    self.service.adapter.two_factor_auth_detected and
                    not two_factor_already_detected and
                    not self.is_cancelled):
                    
                    logger.info("🔐 2차 인증 실시간 감지!")
                    self.two_factor_detected.emit()
                    two_factor_already_detected = True
                
                # 0.5초마다 체크
                stop_event.wait(0.5)
                
            except Exception as e:
                logger.error(f"2차 인증 모니터링 오류: {e}")
                break
    
    def cancel(self):
        """작업 취소"""
        self.is_cancelled = True
        logger.info("🛑 로그인 워커 취소 요청")
        
        # 브라우저 세션 강제 중단
        try:
            if self.service:
                self.service.force_stop_browser_session()
        except Exception as e:
            logger.error(f"로그인 워커 취소 중 브라우저 세션 강제 중단 실패: {e}")





class WorkerThread(QThread):
    """워커 스레드 (QThread 래퍼)"""
    
    def __init__(self, worker: QObject):
        super().__init__()
        self.worker = worker
        
    def run(self):
        """스레드 실행"""
        self.worker.run()


def create_login_worker(service: NeighborAddService, credentials) -> LoginWorker:
    """로그인 워커 생성"""
    return LoginWorker(service, credentials)












class AllKeywordsWorker(QObject):
    """모든 키워드를 순차 처리하는 통합 워커"""
    
    # 시그널 정의
    progress_updated = Signal(WorkerProgress)
    batch_completed = Signal(list)  # 전체 완료된 요청 리스트
    error_occurred = Signal(str)
    
    def __init__(self, service: NeighborAddService, keyword_configs: List[tuple], message: str = ""):
        super().__init__()
        self.service = service
        self.keyword_configs = keyword_configs  # [(keyword, target_count), ...]
        self.message = message
        self.is_cancelled = False
        
    def run(self):
        """모든 키워드를 순차 처리"""
        try:
            logger.info(f"🎯 모든 키워드 워커 시작: {len(self.keyword_configs)}개 키워드")
            
            # 전체 목표 계산
            total_target = sum(target for _, target in self.keyword_configs)
            all_completed_requests = []
            
            # 진행률 초기화
            progress = WorkerProgress(
                current=0,
                total=total_target,
                message="키워드별 서로이웃 추가 시작...",
                stage="start"
            )
            logger.info(f"📡 [Worker] 초기 progress_updated 시그널 발송: {progress.message}")
            self.progress_updated.emit(progress)
            
            current_success = 0
            
            # 키워드별 순차 처리
            for idx, (keyword, target_count) in enumerate(self.keyword_configs):
                if self.is_cancelled:
                    break
                    
                logger.info(f"🔍 키워드 처리 중: '{keyword}' ({idx + 1}/{len(self.keyword_configs)})")
                
                # 진행률 업데이트
                progress.message = f"'{keyword}' 키워드 처리 중... ({idx + 1}/{len(self.keyword_configs)})"
                progress.stage = "processing"
                self.progress_updated.emit(progress)
                
                try:
                    # 서비스의 search_and_add_until_target 호출
                    def update_progress_callback(success_count: int, message: str, **kwargs):
                        logger.info(f"📞 [Worker] 콜백 호출됨! success_count={success_count}, message='{message}'")
                        
                        if self.is_cancelled:
                            logger.info("❌ [Worker] 콜백 - 취소됨으로 인한 건너뜀")
                            return
                        
                        # 전체 진행률에서 현재 키워드의 진행률 반영
                        progress.current = current_success + success_count
                        progress.message = f"[{idx + 1}/{len(self.keyword_configs)}] {message}"
                        
                        # 상황판 정보 업데이트
                        progress.success_count = kwargs.get('success_count', current_success + success_count)
                        progress.failed_count = kwargs.get('failed_count', 0)
                        progress.disabled_count = kwargs.get('disabled_count', 0)
                        progress.already_count = kwargs.get('already_count', 0)
                        progress.current_blogger = kwargs.get('current_blogger', '')
                        progress.stage = kwargs.get('stage', 'processing')
                        
                        logger.info(f"🔍 [AllKeywords] 진행률 업데이트 후 시그널 발송: {progress.current}/{progress.total}")
                        self.progress_updated.emit(progress)
                    
                    # 키워드별 서로이웃 추가 실행
                    keyword_requests = self.service.search_and_add_until_target(
                        keyword, target_count, self.message, progress_callback=update_progress_callback
                    )
                    
                    if keyword_requests:
                        # 성공 개수 계산
                        keyword_success = len([r for r in keyword_requests if hasattr(r.status, 'value') and r.status.value == "success"])
                        current_success += keyword_success
                        all_completed_requests.extend(keyword_requests)
                        
                        logger.info(f"✅ 키워드 '{keyword}' 완료: {keyword_success}/{target_count}명 성공")
                        
                        # 하루 제한 도달 체크
                        daily_limit_reached = any(
                            hasattr(r.status, 'value') and r.status.value == "daily_limit_reached"
                            for r in keyword_requests
                        )
                        
                        if daily_limit_reached:
                            logger.warning("🚫 하루 100명 제한 도달 - 모든 키워드 처리 중단")
                            break
                    
                except Exception as e:
                    logger.error(f"❌ 키워드 '{keyword}' 처리 실패: {e}")
                    # 개별 키워드 실패는 전체를 중단하지 않음
                    continue
            
            if not self.is_cancelled:
                # 최종 완료
                progress.current = current_success
                progress.message = f"모든 키워드 처리 완료: 총 {current_success}명 성공"
                progress.stage = "complete"
                self.progress_updated.emit(progress)
                
                self.batch_completed.emit(all_completed_requests)
                logger.info(f"🏁 모든 키워드 워커 완료: {len(all_completed_requests)}개 처리, {current_success}명 성공")
            
        except Exception as e:
            logger.error(f"❌ 모든 키워드 워커 오류: {e}")
            self.error_occurred.emit(str(e))
    
    def cancel(self):
        """작업 취소"""
        self.is_cancelled = True
        logger.info("🛑 모든 키워드 워커 취소 요청")
        
        # 브라우저 세션 강제 중단
        try:
            if self.service:
                self.service.force_stop_browser_session()
        except Exception as e:
            logger.error(f"워커 취소 중 브라우저 세션 강제 중단 실패: {e}")


def create_all_keywords_worker(service: NeighborAddService, keyword_configs: List[tuple], 
                              message: str = "") -> AllKeywordsWorker:
    """모든 키워드 처리 워커 생성"""
    return AllKeywordsWorker(service, keyword_configs, message)