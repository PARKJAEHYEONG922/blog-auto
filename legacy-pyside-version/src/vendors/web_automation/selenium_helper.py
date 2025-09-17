"""
Selenium 기반 웹 자동화 헬퍼
안정적인 웹 크롤링을 위한 셀레니움 래퍼
"""
import time
import asyncio
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from src.foundation.logging import get_logger

logger = get_logger("selenium_helper")

@dataclass
class SeleniumConfig:
    """셀레니움 설정"""
    headless: bool = False
    window_width: int = 1280
    window_height: int = 720
    user_agent: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    timeout: int = 30
    implicit_wait: int = 10
    
    # 성능 최적화 옵션
    disable_images: bool = True
    disable_css: bool = False
    disable_javascript: bool = False

class SeleniumHelper:
    """셀레니움 기반 웹 자동화 헬퍼 클래스"""
    
    def __init__(self, config: Optional[SeleniumConfig] = None):
        self.config = config or SeleniumConfig()
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
        self.is_running = False
        
    def __enter__(self):
        """컨텍스트 매니저 진입"""
        self.initialize()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self.cleanup()
        
    def initialize(self):
        """셀레니움 드라이버 초기화"""
        try:
            logger.info("셀레니움 드라이버 초기화 시작")
            
            # Chrome 옵션 설정
            chrome_options = Options()
            
            if self.config.headless:
                chrome_options.add_argument('--headless')
                
            # 기본 옵션
            chrome_options.add_argument(f'--user-agent={self.config.user_agent}')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-notifications')
            chrome_options.add_argument('--disable-popup-blocking')
            chrome_options.add_argument(f'--window-size={self.config.window_width},{self.config.window_height}')
            
            # 경고 메시지 억제
            chrome_options.add_argument('--disable-logging')
            chrome_options.add_argument('--log-level=3')
            chrome_options.add_argument('--silent')
            chrome_options.add_argument('--disable-gpu-logging')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--disable-features=TranslateUI')
            chrome_options.add_argument('--disable-ipc-flooding-protection')
            
            # 성능 최적화
            if self.config.disable_images:
                prefs = {"profile.managed_default_content_settings.images": 2}
                chrome_options.add_experimental_option("prefs", prefs)
                
            if self.config.disable_css:
                chrome_options.add_argument('--disable-extensions')
                
            # 자동화 탐지 방지 및 로깅 억제
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_experimental_option("prefs", {"profile.default_content_setting_values.notifications": 2})
            
            # Service 설정 (로깅 억제)
            from selenium.webdriver.chrome.service import Service
            service = Service()
            service.log_level = 'FATAL'  # 치명적 오류만 로깅
            
            # 드라이버 생성
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 자동화 탐지 방지 스크립트
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # 대기 설정
            self.driver.implicitly_wait(self.config.implicit_wait)
            self.wait = WebDriverWait(self.driver, self.config.timeout)
            
            self.is_running = True
            logger.info("셀레니움 드라이버 초기화 완료")
            
        except Exception as e:
            self.cleanup()
            raise RuntimeError(f"셀레니움 초기화 실패: {e}")
            
    def cleanup(self):
        """리소스 정리"""
        self.is_running = False
        
        if self.driver:
            try:
                self.driver.quit()
                logger.info("셀레니움 드라이버 종료 완료")
            except Exception as e:
                logger.error(f"드라이버 종료 중 오류: {e}")
            finally:
                self.driver = None
                self.wait = None
    
    def goto(self, url: str) -> None:
        """페이지 이동"""
        if not self.driver:
            raise RuntimeError("드라이버가 초기화되지 않았습니다")
            
        logger.info(f"페이지 이동: {url}")
        self.driver.get(url)
        time.sleep(1)  # 페이지 로딩 대기
        
    def find_element(self, selector: str, by: By = By.CSS_SELECTOR, timeout: Optional[int] = None):
        """요소 찾기"""
        if not self.driver:
            raise RuntimeError("드라이버가 초기화되지 않았습니다")
            
        try:
            if timeout:
                wait = WebDriverWait(self.driver, timeout)
                return wait.until(EC.presence_of_element_located((by, selector)))
            else:
                return self.driver.find_element(by, selector)
        except TimeoutException:
            logger.warning(f"요소를 찾을 수 없음: {selector}")
            return None
        except NoSuchElementException:
            logger.warning(f"요소가 존재하지 않음: {selector}")
            return None
            
    def find_elements(self, selector: str, by: By = By.CSS_SELECTOR) -> List:
        """여러 요소 찾기"""
        if not self.driver:
            raise RuntimeError("드라이버가 초기화되지 않았습니다")
            
        try:
            return self.driver.find_elements(by, selector)
        except NoSuchElementException:
            logger.warning(f"요소들을 찾을 수 없음: {selector}")
            return []
    
    def wait_for_element(self, selector: str, by: By = By.CSS_SELECTOR, timeout: Optional[int] = None):
        """요소가 나타날 때까지 대기"""
        timeout = timeout or self.config.timeout
        try:
            wait = WebDriverWait(self.driver, timeout)
            return wait.until(EC.presence_of_element_located((by, selector)))
        except TimeoutException:
            logger.warning(f"요소 대기 시간 초과: {selector}")
            return None
            
    def wait_for_clickable(self, selector: str, by: By = By.CSS_SELECTOR, timeout: Optional[int] = None):
        """클릭 가능한 요소 대기"""
        timeout = timeout or self.config.timeout
        try:
            wait = WebDriverWait(self.driver, timeout)
            return wait.until(EC.element_to_be_clickable((by, selector)))
        except TimeoutException:
            logger.warning(f"클릭 가능 요소 대기 시간 초과: {selector}")
            return None
    
    def click_element(self, selector: str, by: By = By.CSS_SELECTOR, timeout: Optional[int] = None) -> bool:
        """요소 클릭"""
        element = self.wait_for_clickable(selector, by, timeout)
        if element:
            try:
                element.click()
                time.sleep(0.5)  # 클릭 후 대기
                return True
            except Exception as e:
                logger.warning(f"클릭 실패: {e}")
                return False
        return False
        
    def type_text(self, selector: str, text: str, by: By = By.CSS_SELECTOR, clear: bool = True) -> bool:
        """텍스트 입력"""
        element = self.find_element(selector, by)
        if element:
            try:
                if clear:
                    element.clear()
                element.send_keys(text)
                time.sleep(0.5)  # 입력 후 대기
                return True
            except Exception as e:
                logger.warning(f"텍스트 입력 실패: {e}")
                return False
        return False
        
    def get_text(self, selector: str, by: By = By.CSS_SELECTOR) -> Optional[str]:
        """요소 텍스트 가져오기"""
        element = self.find_element(selector, by)
        if element:
            try:
                return element.text
            except Exception as e:
                logger.warning(f"텍스트 가져오기 실패: {e}")
        return None
        
    def get_attribute(self, selector: str, attribute: str, by: By = By.CSS_SELECTOR) -> Optional[str]:
        """요소 속성 가져오기"""
        element = self.find_element(selector, by)
        if element:
            try:
                return element.get_attribute(attribute)
            except Exception as e:
                logger.warning(f"속성 가져오기 실패: {e}")
        return None
        
    def execute_script(self, script: str) -> Any:
        """JavaScript 실행"""
        if not self.driver:
            raise RuntimeError("드라이버가 초기화되지 않았습니다")
        return self.driver.execute_script(script)
        
    def scroll_to_element(self, selector: str, by: By = By.CSS_SELECTOR) -> bool:
        """요소까지 스크롤"""
        element = self.find_element(selector, by)
        if element:
            try:
                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(0.5)
                return True
            except Exception as e:
                logger.warning(f"스크롤 실패: {e}")
        return False
        
    def scroll_down(self, pixels: int = 500):
        """아래로 스크롤"""
        self.execute_script(f"window.scrollBy(0, {pixels});")
        time.sleep(0.5)
        
    def scroll_to_bottom(self):
        """페이지 맨 아래로 스크롤"""
        self.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        
    @property
    def current_url(self) -> str:
        """현재 URL 가져오기"""
        if not self.driver:
            return ""
        return self.driver.current_url
        
    @property
    def page_source(self) -> str:
        """페이지 소스 가져오기"""
        if not self.driver:
            return ""
        return self.driver.page_source
        
    def switch_to_window(self, window_handle: str):
        """창 전환"""
        if self.driver:
            self.driver.switch_to.window(window_handle)
            
    def get_window_handles(self) -> List[str]:
        """모든 창 핸들 가져오기"""
        if self.driver:
            return self.driver.window_handles
        return []
        
    def close_current_window(self):
        """현재 창 닫기"""
        if self.driver:
            self.driver.close()

def get_default_selenium_config(headless: bool = False) -> SeleniumConfig:
    """기본 셀레니움 설정 가져오기"""
    return SeleniumConfig(
        headless=headless,
        window_width=1280,
        window_height=720,
        timeout=30,
        implicit_wait=10,
        disable_images=True,
        disable_css=False,
        disable_javascript=False
    )

def get_fast_selenium_config(headless: bool = False) -> SeleniumConfig:
    """빠른 셀레니움 설정 가져오기"""
    return SeleniumConfig(
        headless=headless,
        window_width=1280,
        window_height=720,
        timeout=15,
        implicit_wait=5,
        disable_images=True,
        disable_css=True,
        disable_javascript=False
    )