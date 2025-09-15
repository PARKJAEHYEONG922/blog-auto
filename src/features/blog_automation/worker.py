"""
블로그 자동화 모듈의 워커 - 장시간 작업/비동기 처리
"""
import time
import threading
from typing import Optional, Dict, Any
from PySide6.QtCore import QObject, Signal, QTimer
import uuid

from src.foundation.logging import get_logger
from src.foundation.exceptions import BusinessError
from .models import BlogCredentials, LoginStatus
from .service import BlogAutomationService
from src.toolbox.progress import calc_percentage

logger = get_logger("blog_automation.worker")


class WorkerPool(QObject):
    """워커 풀 관리 클래스 - 다중 워커 작업을 효율적으로 관리"""
    
    # 풀 상태 시그널
    pool_status_changed = Signal(str, int, int)  # 상태메시지, 활성워커수, 총워커수
    all_workers_completed = Signal()  # 모든 워커 완료
    
    def __init__(self, max_workers: int = 3):
        super().__init__()
        self.max_workers = max_workers
        self.active_workers: Dict[str, Dict[str, Any]] = {}  # worker_id -> {worker, thread, status}
        self.completed_workers = []
        self.failed_workers = []
        
        # 상태 업데이트 타이머
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._emit_pool_status)
        self.status_timer.start(500)  # 0.5초마다 상태 업데이트
    
    def add_worker(self, worker: QObject, worker_id: str = None) -> str:
        """워커를 풀에 추가하고 시작"""
        if len(self.active_workers) >= self.max_workers:
            logger.warning(f"워커 풀이 가득참 (최대 {self.max_workers}개)")
            return None
            
        if not worker_id:
            worker_id = str(uuid.uuid4())[:8]
            
        # 워커 스레드 생성
        thread = WorkerThread(worker)
        
        # 워커 완료 시그널 연결
        if hasattr(worker, 'login_completed'):
            worker.login_completed.connect(lambda success: self._on_worker_completed(worker_id, success))
        elif hasattr(worker, 'analysis_completed'):
            worker.analysis_completed.connect(lambda result: self._on_worker_completed(worker_id, True))
        elif hasattr(worker, 'writing_completed'):
            worker.writing_completed.connect(lambda result: self._on_worker_completed(worker_id, True))
        elif hasattr(worker, 'titles_generated'):
            worker.titles_generated.connect(lambda result: self._on_worker_completed(worker_id, True))
        elif hasattr(worker, 'completed'):
            worker.completed.connect(lambda result: self._on_worker_completed(worker_id, True))
            
        # 워커 오류 시그널 연결
        if hasattr(worker, 'error_occurred'):
            worker.error_occurred.connect(lambda error: self._on_worker_error(worker_id, error))
        
        # 풀에 추가
        self.active_workers[worker_id] = {
            'worker': worker,
            'thread': thread,
            'status': 'starting',
            'start_time': time.time()
        }
        
        # 워커 시작
        thread.start()
        logger.info(f"워커 풀에 워커 추가: {worker_id} (총 {len(self.active_workers)}개)")
        
        return worker_id
    
    def _on_worker_completed(self, worker_id: str, success: bool):
        """워커 완료 처리"""
        if worker_id in self.active_workers:
            worker_info = self.active_workers.pop(worker_id)
            elapsed = time.time() - worker_info['start_time']
            
            if success:
                self.completed_workers.append(worker_id)
                logger.info(f"워커 완료: {worker_id} ({elapsed:.1f}초)")
            else:
                self.failed_workers.append(worker_id)
                logger.info(f"워커 실패: {worker_id} ({elapsed:.1f}초)")
            
            self._check_all_completed()
    
    def _on_worker_error(self, worker_id: str, error: str):
        """워커 오류 처리"""
        if worker_id in self.active_workers:
            worker_info = self.active_workers.pop(worker_id)
            elapsed = time.time() - worker_info['start_time']
            
            self.failed_workers.append(worker_id)
            logger.error(f"워커 오류: {worker_id} - {error} ({elapsed:.1f}초)")
            
            self._check_all_completed()
    
    def _check_all_completed(self):
        """모든 워커 완료 확인"""
        if len(self.active_workers) == 0:
            total_completed = len(self.completed_workers)
            total_failed = len(self.failed_workers)
            logger.info(f"모든 워커 완료: 성공 {total_completed}개, 실패 {total_failed}개")
            self.all_workers_completed.emit()
    
    def _emit_pool_status(self):
        """풀 상태 시그널 발송"""
        active_count = len(self.active_workers)
        total_count = active_count + len(self.completed_workers) + len(self.failed_workers)
        
        if active_count > 0:
            status_msg = f"실행 중인 작업: {active_count}개"
        elif total_count > 0:
            status_msg = f"완료: {len(self.completed_workers)}개, 실패: {len(self.failed_workers)}개"
        else:
            status_msg = "대기 중"
            
        self.pool_status_changed.emit(status_msg, active_count, total_count)
    
    def cancel_all_workers(self):
        """모든 워커 취소"""
        for worker_id, worker_info in self.active_workers.items():
            if hasattr(worker_info['worker'], 'cancel'):
                worker_info['worker'].cancel()
            worker_info['thread'].quit()
        
        self.active_workers.clear()
        logger.info("모든 워커가 취소됨")
    
    def get_status(self) -> Dict[str, Any]:
        """현재 풀 상태 반환"""
        return {
            'active': len(self.active_workers),
            'completed': len(self.completed_workers),
            'failed': len(self.failed_workers),
            'max_workers': self.max_workers
        }


class BlogLoginWorker(QObject):
    """블로그 로그인 워커 - 비동기 로그인 처리"""
    
    # 시그널 정의
    login_started = Signal()  # 로그인 시작
    login_completed = Signal(bool)  # 로그인 완료 (성공/실패)
    login_progress = Signal(str, int)  # 로그인 진행 상황 (메시지, 진행률%)
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
            
            # 단계별 진행률 업데이트
            self.login_progress.emit("브라우저 시작 중...", 10)
            time.sleep(1)  # UI 업데이트를 위한 짧은 대기
            
            if self.is_cancelled:
                return
                
            self.login_progress.emit("로그인 페이지 로딩...", 30)
            
            # 실제 로그인 수행
            self.login_progress.emit("로그인 시도 중...", 50)
            success = self.service.login(self.credentials)
            
            if success:
                self.login_progress.emit("로그인 확인 중...", 80)
                time.sleep(1)
                self.login_progress.emit("로그인 완료", 100)
            
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
                    self.login_progress.emit("2차 인증 진행 중... 브라우저에서 인증을 완료해주세요", 60)
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
    """향상된 워커 스레드 관리 클래스"""
    
    def __init__(self, worker):
        self.worker = worker
        self.thread = None
        self.start_time = None
        self.is_running = False
        
    def start(self):
        """워커 스레드 시작"""
        if self.is_running:
            logger.warning("워커가 이미 실행 중입니다")
            return False
            
        self.thread = threading.Thread(
            target=self._safe_run, 
            daemon=True,
            name=f"Worker-{type(self.worker).__name__}"
        )
        self.start_time = time.time()
        self.is_running = True
        self.thread.start()
        logger.info(f"워커 스레드 시작: {self.thread.name}")
        return True
        
    def _safe_run(self):
        """안전한 워커 실행 래퍼"""
        try:
            self.worker.run()
        except Exception as e:
            logger.error(f"워커 실행 중 예외 발생: {e}")
            if hasattr(self.worker, 'error_occurred'):
                self.worker.error_occurred.emit(f"워커 실행 오류: {str(e)}")
        finally:
            self.is_running = False
            elapsed = time.time() - self.start_time if self.start_time else 0
            logger.info(f"워커 스레드 종료: {self.thread.name} ({elapsed:.1f}초)")
            
    def quit(self):
        """스레드 종료 (워커 취소)"""
        if self.worker and hasattr(self.worker, 'cancel'):
            self.worker.cancel()
            logger.info("워커 취소 신호 발송")
            
    def wait(self, timeout=5):
        """스레드 종료 대기"""
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=timeout)
            if self.thread.is_alive():
                logger.warning(f"워커 스레드가 {timeout}초 내에 종료되지 않음")
                return False
        return True
        
    def get_status(self):
        """워커 상태 정보 반환"""
        return {
            'is_running': self.is_running,
            'thread_alive': self.thread.is_alive() if self.thread else False,
            'elapsed_time': time.time() - self.start_time if self.start_time else 0,
            'worker_type': type(self.worker).__name__
        }



class AIBlogAnalysisWorker(QObject):
    """AI 기반 블로그 분석 워커 - AI 제목 선별 사용"""

    # 시그널 정의
    analysis_started = Signal()  # 분석 시작
    analysis_progress = Signal(str, int)  # 분석 진행 상황 (메시지, 진행률)
    analysis_completed = Signal(list)  # 분석 완료 (분석된 블로그 리스트)
    error_occurred = Signal(str)  # 오류 발생
    blog_found = Signal(int)  # 블로그 발견 (개수)

    def __init__(self, service: BlogAutomationService, search_keyword: str, target_title: str, main_keyword: str, content_type: str = "정보/가이드형", sub_keywords: str = ""):
        super().__init__()
        self.service = service
        self.search_keyword = search_keyword
        self.target_title = target_title
        self.main_keyword = main_keyword
        self.content_type = content_type
        self.sub_keywords = sub_keywords
        self.is_cancelled = False

    def run(self):
        """AI 기반 블로그 분석 작업 실행"""
        try:
            logger.info(f"🤖 AI 기반 블로그 분석 워커 시작: 검색키워드={self.search_keyword}, 타겟제목={self.target_title}")
            self.analysis_started.emit()

            # 세밀한 진행 상황 업데이트
            self.analysis_progress.emit("브라우저 준비 중...", 5)
            time.sleep(0.5)

            if self.is_cancelled:
                return

            self.analysis_progress.emit("블로그 제목 30개 수집 중...", 20)
            time.sleep(0.5)

            if self.is_cancelled:
                return

            self.analysis_progress.emit("AI가 관련도 높은 제목 10개 선별 중...", 40)

            if self.is_cancelled:
                return

            self.analysis_progress.emit("선별된 블로그 순차 분석 중...", 60)

            # 실제 AI 기반 블로그 분석 수행
            analyzed_blogs = self.service.analyze_top_blogs_with_ai_selection(
                self.search_keyword,
                self.target_title,
                self.main_keyword,
                self.content_type,
                3,  # max_results
                self.sub_keywords
            )

            if not self.is_cancelled:
                self.analysis_progress.emit("블로그 내용 분석 완료", 90)
                time.sleep(0.5)  # 분석 시뮬레이션

                self.blog_found.emit(len(analyzed_blogs))
                self.analysis_progress.emit("AI 선별 분석 완료", 100)
                self.analysis_completed.emit(analyzed_blogs)

                logger.info(f"✅ AI 기반 블로그 분석 완료: {len(analyzed_blogs)}개")

        except Exception as e:
            logger.error(f"❌ AI 기반 블로그 분석 실패: {e}")
            self.error_occurred.emit(str(e))

    def cancel(self):
        """작업 취소"""
        self.is_cancelled = True
        logger.info("🛑 AI 기반 블로그 분석 워커 취소됨")


class SummaryAIWorker(QObject):
    """통합 정보요약 AI 워커 - 프롬프트만 받아서 처리"""

    # 통합 시그널 정의
    completed = Signal(object)  # 작업 완료 (결과 데이터)
    error_occurred = Signal(str)  # 오류 발생

    def __init__(self, service: BlogAutomationService, prompt: str, response_format: str = "text", context: str = "정보요약"):
        super().__init__()
        self.service = service
        self.prompt = prompt
        self.response_format = response_format
        self.context = context
        self.is_cancelled = False

    def run(self):
        """통합 정보요약 AI 작업 실행"""
        try:
            if self.is_cancelled:
                return

            logger.info(f"통합 정보요약 워커 시작: {self.context}")

            # 통합 AI 호출
            result = self.service.call_summary_ai(
                prompt=self.prompt,
                response_format=self.response_format,
                context=self.context
            )

            if self.is_cancelled:
                return

            logger.info(f"통합 정보요약 워커 완료: {self.context}")
            self.completed.emit(result)

        except Exception as e:
            logger.error(f"통합 정보요약 워커 오류 ({self.context}): {e}")
            self.error_occurred.emit(str(e))

    def cancel(self):
        """워커 취소"""
        self.is_cancelled = True
        logger.info("정보요약 AI 워커 취소됨")


class TitleSuggestionWorker(QObject):
    """제목 추천 AI 워커 - 제목 추천 API 호출 처리"""

    # 시그널 정의
    titles_generated = Signal(list)  # 제목 생성 완료 (제목 리스트)
    error_occurred = Signal(str)  # 오류 발생

    def __init__(self, service: BlogAutomationService, prompt: str, main_keyword: str, content_type: str):
        super().__init__()
        self.service = service
        self.prompt = prompt
        self.main_keyword = main_keyword
        self.content_type = content_type
        self.is_cancelled = False

    def _extract_titles_from_json(self, json_result) -> list:
        """JSON 결과에서 제목들을 추출"""
        try:
            titles_data = []

            if isinstance(json_result, dict):
                # {"titles_with_search": [{"title": "...", "search_query": "..."}, ...]} 형식
                if 'titles_with_search' in json_result:
                    for item in json_result['titles_with_search']:
                        if isinstance(item, dict) and 'title' in item:
                            title = item['title']
                            search_query = item.get('search_query', title)
                            titles_data.append({"title": title, "search_query": search_query})
                    logger.info(f"titles_with_search 구조로 파싱: {len(titles_data)}개")

                # {"titles": ["title1", "title2", ...]} 형식 (fallback)
                elif 'titles' in json_result:
                    for title in json_result['titles']:
                        if isinstance(title, str):
                            titles_data.append(title)
                    logger.info(f"titles 구조로 파싱: {len(titles_data)}개")

            elif isinstance(json_result, list):
                # 리스트 형태 JSON
                for item in json_result:
                    if isinstance(item, dict) and 'title' in item:
                        title = item['title']
                        search_query = item.get('search_query', title)
                        titles_data.append({"title": title, "search_query": search_query})
                    elif isinstance(item, str):
                        titles_data.append(item)
                logger.info(f"리스트 구조로 파싱: {len(titles_data)}개")

            return titles_data

        except Exception as e:
            logger.error(f"JSON 제목 추출 오류: {e}")
            return []

    def run(self):
        """제목 추천 작업 실행"""
        try:
            logger.info(f"🎯 제목 추천 AI 워커 시작: {self.main_keyword} ({self.content_type})")

            if self.is_cancelled:
                return

            # 통합 AI 호출을 사용하여 제목 추천 (JSON 형식으로 받기)
            result = self.service.call_summary_ai(
                prompt=self.prompt,
                response_format="json",
                context="제목 추천"
            )

            if self.is_cancelled:
                return

            # JSON 결과에서 제목과 검색어 추출
            titles = []
            if result:
                titles = self._extract_titles_from_json(result)
            else:
                logger.warning("AI 응답이 비어있거나 None입니다")

            if titles:
                logger.info(f"✅ 제목 추천 완료: {len(titles)}개")
                self.titles_generated.emit(titles)
            else:
                self.error_occurred.emit("제목 추천 결과가 비어있습니다.")

        except Exception as e:
            logger.error(f"❌ 제목 추천 워커 오류: {e}")
            if not self.is_cancelled:
                self.error_occurred.emit(str(e))

    def cancel(self):
        """워커 취소"""
        self.is_cancelled = True
        logger.info("제목 추천 워커 취소됨")


class AIWritingWorker(QObject):
    """AI 블로그 글쓰기 워커 - AI API 호출 처리"""

    # 시그널 정의
    writing_started = Signal()  # 글쓰기 시작
    writing_progress = Signal(str, int)  # 글쓰기 진행 상황 (메시지, 진행률%)
    writing_completed = Signal(str)  # 글쓰기 완료 (생성된 콘텐츠)
    error_occurred = Signal(str)  # 오류 발생
    
    # 2단계 파이프라인 추가 시그널
    summary_prompt_generated = Signal(str)  # 정보요약 AI 프롬프트 생성
    summary_completed = Signal(str)  # 정보요약 AI 결과 완료
    writing_prompt_generated = Signal(str)  # 글작성 AI 프롬프트 생성
    
    def __init__(self, service: BlogAutomationService, main_keyword: str, sub_keywords: str, structured_data: dict, analyzed_blogs: list = None, content_type: str = "정보/가이드형", tone: str = "정중한 존댓말체", review_detail: str = "", search_keyword: str = ""):
        super().__init__()
        self.service = service
        self.main_keyword = main_keyword
        self.sub_keywords = sub_keywords
        self.structured_data = structured_data
        self.analyzed_blogs = analyzed_blogs or []
        self.content_type = content_type
        self.tone = tone
        self.review_detail = review_detail
        self.search_keyword = search_keyword or main_keyword
        self.is_cancelled = False

        # DEBUG: 워커 초기화 시 search_keyword 확인
        logger.info(f"🔍 DEBUG AIWritingWorker init: received search_keyword='{search_keyword}', final search_keyword='{self.search_keyword}'")
        
    def run(self):
        """AI 글쓰기 작업 실행 (2단계 파이프라인)"""
        try:
            logger.info(f"🤖 AI 글쓰기 워커 시작 (2단계 파이프라인): {self.main_keyword}")
            logger.info(f"🔍 DEBUG: search_keyword='{self.search_keyword}', main_keyword='{self.main_keyword}'")
            self.writing_started.emit()
            
            # 분석된 블로그 데이터가 있는지 확인
            if self.analyzed_blogs:
                logger.info(f"2단계 파이프라인 사용: {len(self.analyzed_blogs)}개 블로그 분석 데이터 활용")
                self.writing_progress.emit("경쟁 블로그 콘텐츠 통합 중...", 10)
                
                if self.is_cancelled:
                    return
                
                self.writing_progress.emit("정보요약 AI로 콘텐츠 요약 중...", 30)
                
                if self.is_cancelled:
                    return
                    
                self.writing_progress.emit("글작성 AI로 최종 콘텐츠 생성 중... (시간이 좀 걸릴 수 있습니다)", 60)
                
                # 2단계 파이프라인으로 콘텐츠 생성 (상세 정보 포함)
                detailed_results = self.service.generate_blog_content_with_summary_detailed(
                    self.main_keyword,
                    self.sub_keywords,
                    self.analyzed_blogs,
                    self.content_type,
                    self.tone,
                    self.review_detail,
                    self.search_keyword,
                    self.target_title
                )
                
                # 각 단계별 시그널 발송
                if not self.is_cancelled and detailed_results:
                    # 정보요약 AI 프롬프트 시그널
                    self.summary_prompt_generated.emit(detailed_results.get("summary_prompt", ""))
                    
                    # 정보요약 AI 결과 시그널  
                    self.summary_completed.emit(detailed_results.get("summary_result", ""))
                    
                    # 글작성 AI 프롬프트 시그널
                    self.writing_prompt_generated.emit(detailed_results.get("writing_prompt", ""))
                    
                    # 최종 생성 콘텐츠
                    generated_content = detailed_results.get("final_content", "")
                
            else:
                logger.info("기존 방식 사용: 분석 데이터 없이 프롬프트만으로 생성")
                self.writing_progress.emit("프롬프트 준비 중...", 10)
                
                if self.is_cancelled:
                    return
                    
                # 기존 방식: 프롬프트만으로 생성
                from .ai_prompts import BlogAIPrompts
                prompt = BlogAIPrompts.generate_content_analysis_prompt(
                    self.main_keyword, self.sub_keywords, self.structured_data, 
                    self.content_type, self.tone, self.review_detail, "", ""
                )
                
                self.writing_progress.emit("AI 모델 연결 중...", 30)
                time.sleep(1)
                
                if self.is_cancelled:
                    return
                    
                self.writing_progress.emit("콘텐츠 생성 중... (시간이 좀 걸릴 수 있습니다)", 50)
                
                # 기존 AI API 호출
                generated_content = self.service.generate_blog_content(prompt)
            
            if not self.is_cancelled:
                if generated_content:
                    self.writing_progress.emit("콘텐츠 후처리 중...", 90)
                    time.sleep(0.5)
                    
                    self.writing_progress.emit("글쓰기 완료", 100)
                    self.writing_completed.emit(generated_content)
                    logger.info("✅ AI 글쓰기 워커 완료")
                else:
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



def create_ai_blog_analysis_worker(service: BlogAutomationService, search_keyword: str, target_title: str, main_keyword: str, content_type: str = "정보/가이드형", sub_keywords: str = "") -> AIBlogAnalysisWorker:
    """AI 기반 블로그 분석 워커 생성"""
    return AIBlogAnalysisWorker(service, search_keyword, target_title, main_keyword, content_type, sub_keywords)


def create_ai_writing_worker(service: BlogAutomationService, main_keyword: str, sub_keywords: str, structured_data: dict, analyzed_blogs: list = None, content_type: str = "정보/가이드형", tone: str = "정중한 존댓말체", review_detail: str = "", search_keyword: str = "") -> AIWritingWorker:
    """AI 글쓰기 워커 생성 (2단계 파이프라인 지원)"""
    return AIWritingWorker(service, main_keyword, sub_keywords, structured_data, analyzed_blogs, content_type, tone, review_detail, search_keyword)

def create_summary_worker(service: BlogAutomationService, prompt: str, response_format: str = "text", context: str = "정보요약") -> SummaryAIWorker:
    """통합 정보요약 워커 생성 팩토리 함수"""
    return SummaryAIWorker(
        service=service,
        prompt=prompt,
        response_format=response_format,
        context=context
    )

def create_title_suggestion_worker(service: BlogAutomationService, prompt: str, main_keyword: str, content_type: str) -> TitleSuggestionWorker:
    """제목 추천 워커 생성 팩토리 함수"""
    return TitleSuggestionWorker(service, prompt, main_keyword, content_type)


def create_worker_pool(max_workers: int = 3) -> WorkerPool:
    """워커 풀 생성"""
    return WorkerPool(max_workers)


def create_enhanced_worker_thread(worker: QObject) -> WorkerThread:
    """향상된 워커 스레드 생성"""
    return WorkerThread(worker)


# 전역 워커 풀 인스턴스 (필요 시 사용)
_global_worker_pool = None

def get_global_worker_pool(max_workers: int = 3) -> WorkerPool:
    """전역 워커 풀 인스턴스 가져오기 (싱글톤 패턴)"""
    global _global_worker_pool
    if _global_worker_pool is None:
        _global_worker_pool = WorkerPool(max_workers)
        logger.info(f"전역 워커 풀 생성: 최대 {max_workers}개 워커")
    return _global_worker_pool