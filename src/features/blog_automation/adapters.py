"""
블로그 자동화 모듈의 웹 자동화 어댑터
"""
import time
import random
import re
from typing import Optional, Dict, Any, List
from functools import wraps
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

from src.vendors.web_automation.selenium_helper import SeleniumHelper, get_default_selenium_config
from src.foundation.logging import get_logger
from src.foundation.http_client import default_http_client
from src.foundation.exceptions import BusinessError, APIResponseError, APITimeoutError
from .models import BlogCredentials, BlogPlatform, LoginStatus

logger = get_logger("blog_automation.adapters")


def is_advertisement_content(text_content: str, title: str = "") -> bool:
    """광고/협찬/체험단 글인지 판단"""
    if not text_content:
        return False
    
    # 전체 텍스트를 소문자로 변환하여 검사
    full_text = (text_content + " " + title).lower()
    
    # 광고/협찬 관련 키워드들
    ad_keywords = [
        # 광고 관련
        "광고포스트", "광고 포스트", "광고글", "광고 글", "광고입니다", "광고 입니다",
        "유료광고", "유료 광고", "파트너스", "쿠팡파트너스", "파트너 활동", "추천링크",
        
        # 협찬 관련  
        "협찬", "협찬받", "협찬글", "협찬 글", "협찬으로", "협찬을", "제공받", "무료로 제공",
        "브랜드로부터", "업체로부터", "해당업체", "해당 업체", "제품을 제공", "서비스를 제공", 
        "제공받아", "제공받은", "지원을 받아", "지원받아", "업체에서 제공", "업체로부터 제품",
        
        # 체험단 관련
        "체험단", "체험 단", "리뷰어", "체험후기", "체험 후기", "체험해보", "체험을",
        "무료체험", "무료 체험", "서포터즈", "앰배서더", "인플루언서",
        
        # 기타 상업적 키워드
        "원고료", "대가", "소정의", "혜택을", "증정", "무료로 받", "공짜로", 
        "할인코드", "쿠폰", "프로모션", "이벤트 참여"
    ]
    
    # 키워드 매칭 검사
    for keyword in ad_keywords:
        if keyword in full_text:
            logger.info(f"광고/협찬 글 감지: '{keyword}' 키워드 발견")
            return True
    
    # 패턴 매칭 (정규식)
    ad_patterns = [
        r".*제공받.*작성.*",  # "제공받아 작성한", "제공받고 작성한" 등
        r".*협찬.*받.*글.*",  # "협찬받은 글", "협찬을 받아서" 등  
        r".*무료.*받.*후기.*", # "무료로 받아서 후기", "무료로 받은 후기" 등
        r".*체험.*참여.*",     # "체험에 참여해", "체험단 참여" 등
        r".*광고.*포함.*",     # "광고가 포함", "광고를 포함한" 등
        r".*업체.*지원.*받.*", # "해당 업체에 지원을 받아", "업체로부터 지원받아" 등
        r".*업체.*제품.*제공.*", # "업체로부터 제품을 제공받아" 등
    ]
    
    for pattern in ad_patterns:
        if re.search(pattern, full_text):
            logger.info(f"광고/협찬 글 감지: 패턴 '{pattern}' 매칭")
            return True
    
    return False


def handle_web_automation_errors(operation_name: str):
    """웹 자동화 오류 처리 데코레이터 (중복 코드 제거용)"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except TimeoutException as e:
                logger.error(f"{operation_name} 타임아웃: {e}")
                raise BusinessError(f"{operation_name} 실패 (타임아웃): 요소를 찾을 수 없습니다")
            except NoSuchElementException as e:
                logger.error(f"{operation_name} 요소 없음: {e}")
                raise BusinessError(f"{operation_name} 실패: 필요한 요소를 찾을 수 없습니다")
            except Exception as e:
                logger.error(f"{operation_name} 실패: {e}")
                raise BusinessError(f"{operation_name} 실패: {str(e)}")
        return wrapper
    return decorator


def is_low_quality_content(text_content: str) -> bool:
    """콘텐츠 품질이 낮은 글인지 판단 (숫자만 나열, 특수문자 과다)"""
    if not text_content:
        return False

    import re

    # 텍스트 전처리 (공백 제거)
    cleaned_text = text_content.strip()
    if len(cleaned_text) < 100:  # 너무 짧은 글은 별도 체크
        return False

    # 1. 숫자만 나열된 글 체크 (전화번호, 가격표, 주소 등)
    # 숫자, 공백, 하이픈, 콤마, 괄호, 원화표시 외에는 거의 없는 경우
    numbers_and_symbols = re.sub(r'[0-9\s\-,()원₩\.\+#]', '', cleaned_text)
    if len(numbers_and_symbols) / len(cleaned_text) < 0.3:  # 의미있는 문자가 30% 미만
        logger.info(f"품질 낮은 글 감지: 숫자/기호만 나열됨 (의미있는 문자 비율: {len(numbers_and_symbols) / len(cleaned_text) * 100:.1f}%)")
        return True

    # 2. 특수문자 비율이 너무 높은 글 체크
    # 한글, 영문, 숫자, 공백을 제외한 특수문자 비율
    special_chars = re.sub(r'[가-힣ㄱ-ㅎㅏ-ㅣa-zA-Z0-9\s]', '', cleaned_text)
    special_char_ratio = len(special_chars) / len(cleaned_text)
    if special_char_ratio > 0.15:  # 특수문자가 15% 초과
        logger.info(f"품질 낮은 글 감지: 특수문자 과다 (비율: {special_char_ratio * 100:.1f}%)")
        return True

    # 3. 반복 패턴 체크 (같은 문자나 기호의 반복)
    # 같은 문자 5개 이상 연속 반복 체크
    if re.search(r'(.)\1{4,}', cleaned_text):  # 같은 문자 5개 이상 반복
        logger.info("품질 낮은 글 감지: 같은 문자 반복 패턴")
        return True

    return False


class NaverBlogAdapter:
    """네이버 블로그 자동화 어댑터"""
    
    def __init__(self):
        # Selenium Helper 사용 (헤드리스 모드 비활성화)
        config = get_default_selenium_config(headless=False)
        self.helper = SeleniumHelper(config)

        self.is_logged_in = False
        self.two_factor_auth_detected = False
        self.username = None  # 로그인한 사용자 아이디 저장

        # 네이버 블로그 URL들
        self.main_url = "https://section.blog.naver.com/"
        self.login_start_url = "https://section.blog.naver.com/"
        self.blog_home_url = "https://section.blog.naver.com/BlogHome.naver?directoryNo=0&currentPage=1&groupId=0"
    
    @handle_web_automation_errors("브라우저 시작")
    def start_browser(self, for_login=True):
        """브라우저 시작"""
        logger.info("네이버 블로그 브라우저 시작")
        self.helper.initialize()
        
        if for_login:
            # 로그인용: 블로그 홈으로 이동
            self.helper.goto(self.login_start_url)
            logger.info("네이버 블로그 로그인 페이지 로드 완료")
        else:
            # 분석 전용: 초기 페이지 로딩 없이 브라우저만 시작
            logger.info("분석 전용 브라우저 시작 완료")
    
    def start_browser_for_analysis(self):
        """분석 전용 브라우저 시작 (초기 페이지 로딩 없음)"""
        return self.start_browser(for_login=False)
    
    def close_browser(self):
        """브라우저 종료"""
        try:
            logger.info("네이버 블로그 브라우저 종료 중...")
            self.helper.cleanup()
            self.is_logged_in = False
            self.two_factor_auth_detected = False
            logger.info("브라우저 종료 완료")
            
        except Exception as e:
            logger.error(f"브라우저 종료 중 오류: {e}")
            self.is_logged_in = False
            self.two_factor_auth_detected = False
    
    def _wait_and_find_element(self, selectors, timeout=10, condition=EC.element_to_be_clickable):
        """여러 셀렉터를 시도하여 요소 찾기 (중복 코드 제거용 헬퍼)"""
        wait = WebDriverWait(self.helper.driver, timeout)
        
        for by, selector in selectors:
            try:
                logger.debug(f"요소 찾기 시도: {selector}")
                element = wait.until(condition((by, selector)))
                if element:
                    logger.debug(f"요소 발견: {selector}")
                    return element, selector
            except TimeoutException:
                logger.debug(f"요소 찾기 실패: {selector}")
                continue
        
        return None, None
    
    def _wait_and_click_element(self, selectors, timeout=10):
        """여러 셀렉터를 시도하여 요소 클릭 (중복 코드 제거용 헬퍼)"""
        element, used_selector = self._wait_and_find_element(selectors, timeout)
        
        if element:
            try:
                element.click()
                logger.info(f"요소 클릭 성공: {used_selector}")
                return True
            except Exception as e:
                logger.error(f"요소 클릭 실패: {e}")
                return False
        else:
            logger.error("클릭할 요소를 찾을 수 없습니다")
            return False
    
    def click_login_button(self) -> bool:
        """메인 페이지에서 로그인 버튼 클릭 - WebDriverWait 사용"""
        try:
            logger.info("네이버 블로그 로그인 버튼 클릭 시도")
            
            wait = WebDriverWait(self.helper.driver, 10)
            
            # 로그인 버튼 찾기 (CSS 셀렉터들)
            login_selectors = [
                (By.CSS_SELECTOR, "a[href*='nidlogin.login']"),  # href 속성으로 찾기 (가장 확실)
                (By.CSS_SELECTOR, "a[ng-href*='nidlogin.login']"),  # Angular href
                (By.CSS_SELECTOR, "a.login_button"),  # 클래스명으로 찾기
                (By.CSS_SELECTOR, ".login_button"),
                (By.CSS_SELECTOR, "a[class*='login']"),  # 클래스에 login이 포함된 링크
                (By.CSS_SELECTOR, ".ugc_login_text"),
                (By.CSS_SELECTOR, "span.ugc_login_text")  # span 내부 텍스트
            ]
            
            # 헬퍼 메서드 사용 - CSS 셀렉터 시도
            login_element, used_selector = self._wait_and_find_element(login_selectors, timeout=10)
            
            # CSS 셀렉터로 못 찾으면 XPath도 시도
            if not login_element:
                xpath_selectors = [
                    (By.XPATH, "//a[contains(@href, 'nidlogin.login')]"),  # href에 로그인 URL 포함
                    (By.XPATH, "//a[contains(@ng-href, 'nidlogin.login')]"),  # ng-href에 로그인 URL 포함
                    (By.XPATH, "//a[contains(@class, 'login')]"),  # 클래스에 login 포함
                    (By.XPATH, "//a[contains(text(), 'NAVER')]"),  # 텍스트에 NAVER 포함
                    (By.XPATH, "//a[contains(text(), '로그인')]"),  # 텍스트에 로그인 포함
                    (By.XPATH, "//span[contains(@class, 'ugc_login_text')]"),  # 특정 클래스
                    (By.XPATH, "//span[contains(text(), 'NAVER')]//parent::a"),  # NAVER 텍스트의 부모 링크
                    (By.XPATH, "//em[contains(text(), '로그인')]//ancestor::a")  # 로그인 텍스트의 조상 링크
                ]
                
                # 헬퍼 메서드 사용 - XPath 셀렉터 시도
                login_element, used_selector = self._wait_and_find_element(xpath_selectors, timeout=10)
            
            if not login_element:
                logger.error("로그인 버튼을 찾을 수 없습니다")
                return False
            
            # 로그인 버튼 클릭 (여러 방법 시도)
            try:
                logger.info(f"로그인 버튼 클릭 시도 (셀렉터: {used_selector})")
                
                # 방법 1: 일반 클릭
                login_element.click()
                
            except Exception as e:
                logger.warning(f"일반 클릭 실패, JavaScript 클릭 시도: {e}")
                try:
                    # 방법 2: JavaScript 클릭
                    self.helper.driver.execute_script("arguments[0].click();", login_element)
                except Exception as e2:
                    logger.error(f"JavaScript 클릭도 실패: {e2}")
                    return False
            
            # 로그인 페이지로 이동할 때까지 대기 (URL 변화 감지)
            try:
                # https://nid.naver.com/nidlogin.login 로 정확히 이동하는지 확인
                wait.until(EC.url_contains("nid.naver.com/nidlogin.login"))
                logger.info("로그인 페이지로 성공적으로 이동")
                return True
            except TimeoutException:
                current_url = self.helper.current_url
                logger.warning(f"로그인 페이지로 이동 타임아웃. 현재 URL: {current_url}")
                # URL에 nidlogin.login이 포함되어 있으면 성공으로 간주
                if "nidlogin.login" in current_url:
                    logger.info("로그인 페이지 URL 확인됨")
                    return True
                return False
            
        except Exception as e:
            logger.error(f"로그인 버튼 클릭 실패: {e}")
            return False
    
    def login_with_credentials(self, credentials: BlogCredentials) -> LoginStatus:
        """자격증명으로 로그인 수행"""
        try:
            logger.info(f"네이버 블로그 로그인 시작: {credentials.username}")
            
            # 로그인 페이지가 아니면 로그인 버튼 클릭
            current_url = self.helper.current_url
            logger.info(f"현재 URL: {current_url}")
            
            if "nid.naver.com/nidlogin.login" not in current_url:
                logger.info("로그인 페이지가 아님, 로그인 버튼 클릭 시도")
                
                # 여러 번 시도
                login_clicked = False
                for attempt in range(3):
                    logger.info(f"로그인 버튼 클릭 시도 {attempt + 1}/3")
                    
                    if self.click_login_button():
                        # 잠시 대기 후 URL 확인
                        time.sleep(2)
                        current_url = self.helper.current_url
                        logger.info(f"클릭 후 URL: {current_url}")
                        
                        if "nid.naver.com/nidlogin.login" in current_url:
                            logger.info("로그인 페이지로 성공적으로 이동")
                            login_clicked = True
                            break
                        else:
                            logger.warning(f"아직 로그인 페이지로 이동하지 않음. 재시도... (시도 {attempt + 1})")
                    else:
                        logger.warning(f"로그인 버튼 클릭 실패 (시도 {attempt + 1})")
                    
                    time.sleep(1)  # 재시도 전 대기
                
                if not login_clicked:
                    logger.error("로그인 버튼 클릭 최종 실패")
                    return LoginStatus.LOGIN_FAILED
            else:
                logger.info("이미 로그인 페이지에 있음")
            
            # 로그인 폼 대기 (nidlogin 페이지) - WebDriverWait 사용
            logger.info("로그인 폼 로딩 대기 중...")
            wait = WebDriverWait(self.helper.driver, 15)
            
            # 아이디 입력란이 클릭 가능할 때까지 대기
            try:
                id_input = wait.until(
                    EC.element_to_be_clickable((By.ID, "id"))
                )
                logger.info("아이디 입력란 준비 완료")
            except TimeoutException:
                raise BusinessError("아이디 입력란을 찾을 수 없습니다 (타임아웃)")
            
            # 아이디 입력란 클릭 후 클립보드 입력 (서로이웃 방식 적용)
            logger.info("아이디 입력 중...")
            id_input.click()
            time.sleep(1.0)  # 포커스 안정화 대기
            
            # 기존 내용 완전히 제거
            id_input.clear()
            time.sleep(0.5)
            id_input.send_keys(Keys.CONTROL + 'a')
            time.sleep(0.3)
            id_input.send_keys(Keys.DELETE)
            time.sleep(0.5)
            
            # JavaScript로 클립보드에 아이디 복사
            copy_script = f"""
                return navigator.clipboard.writeText('{credentials.username}').then(function() {{
                    console.log('아이디가 클립보드에 복사됨: {credentials.username}');
                    return true;
                }}).catch(function(err) {{
                    console.error('클립보드 복사 실패:', err);
                    return false;
                }});
            """
            self.helper.driver.execute_script(copy_script)
            time.sleep(1.2)  # 클립보드 복사 완료 대기
            
            # 아이디 필드에 포커스 재확인 후 붙여넣기
            id_input.click()
            time.sleep(0.3)
            id_input.send_keys(Keys.CONTROL + 'v')
            time.sleep(0.8)
            
            # 입력 결과 확인
            actual_value = id_input.get_attribute('value')
            if actual_value == credentials.username:
                logger.info(f"✅ 아이디 입력 성공: {credentials.username}")
            else:
                logger.warning(f"⚠️ 아이디 입력 불일치 - 입력: '{actual_value}', 예상: '{credentials.username}'")
                raise BusinessError("아이디 입력 실패")
            
            # 비밀번호 입력란이 클릭 가능할 때까지 대기
            try:
                pw_input = wait.until(
                    EC.element_to_be_clickable((By.ID, "pw"))
                )
                logger.info("비밀번호 입력란 준비 완료")
            except TimeoutException:
                raise BusinessError("비밀번호 입력란을 찾을 수 없습니다 (타임아웃)")
            
            # 비밀번호 입력란 클릭 후 클립보드 입력 (서로이웃 방식 적용)
            logger.info("비밀번호 입력 중...")
            pw_input.click()
            time.sleep(1.0)  # 포커스 안정화 대기
            
            # 기존 내용 완전히 제거
            pw_input.clear()
            time.sleep(0.5)
            pw_input.send_keys(Keys.CONTROL + 'a')
            time.sleep(0.3)
            pw_input.send_keys(Keys.DELETE)
            time.sleep(0.5)
            
            # JavaScript로 클립보드에 비밀번호 복사
            copy_script = f"""
                return navigator.clipboard.writeText('{credentials.password}').then(function() {{
                    console.log('비밀번호가 클립보드에 복사됨');
                    return true;
                }}).catch(function(err) {{
                    console.error('클립보드 복사 실패:', err);
                    return false;
                }});
            """
            self.helper.driver.execute_script(copy_script)
            time.sleep(1.2)  # 클립보드 복사 완료 대기
            
            # 비밀번호 필드에 포커스 재확인 후 붙여넣기
            pw_input.click()
            time.sleep(0.3)
            pw_input.send_keys(Keys.CONTROL + 'v')
            time.sleep(0.8)
            
            # 입력 결과 확인 (비밀번호는 길이만 확인)
            actual_value = pw_input.get_attribute('value')
            if len(actual_value) == len(credentials.password):
                logger.info(f"✅ 비밀번호 입력 성공 (길이: {len(credentials.password)})")
            else:
                logger.warning(f"⚠️ 비밀번호 입력 길이 불일치 - 입력 길이: {len(actual_value)}, 예상 길이: {len(credentials.password)}")
                raise BusinessError("비밀번호 입력 실패")
            
            # 로그인 버튼 클릭 (nidlogin 페이지의 로그인 버튼) - WebDriverWait 사용
            logger.info("로그인 버튼 찾는 중...")
            
            # 다양한 셀렉터로 로그인 버튼 찾기
            login_btn_selectors = [
                (By.ID, "log.login"),  # ID 선택자
                (By.CSS_SELECTOR, "button[id='log.login']"),  # 속성 선택자
                (By.CSS_SELECTOR, "button.btn_login"),  # 클래스 선택자
                (By.CSS_SELECTOR, "button[type='submit'].btn_login"),  # 복합 선택자
                (By.CSS_SELECTOR, "button[type='submit']"),  # 기본 submit 버튼
                (By.CSS_SELECTOR, ".btn_login_wrap button"),  # 부모 클래스 기반
            ]
            
            login_btn = None
            used_selector = None
            
            for by, selector in login_btn_selectors:
                try:
                    logger.debug(f"로그인 버튼 찾기 시도: {selector}")
                    login_btn = wait.until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    if login_btn:
                        used_selector = selector
                        logger.info(f"로그인 버튼 발견: {selector}")
                        break
                except TimeoutException:
                    logger.debug(f"셀렉터 {selector} 타임아웃")
                    continue
                except Exception as e:
                    logger.debug(f"셀렉터 {selector} 실패: {e}")
                    continue
            
            # CSS 셀렉터로 못 찾으면 XPath도 시도
            if not login_btn:
                xpath_selectors = [
                    "//button[@id='log.login']",
                    "//button[contains(@class, 'btn_login')]",
                    "//button[@type='submit']",
                    "//div[@class='btn_login_wrap']//button"
                ]
                
                for xpath in xpath_selectors:
                    try:
                        logger.debug(f"XPath로 로그인 버튼 찾기 시도: {xpath}")
                        login_btn = wait.until(
                            EC.element_to_be_clickable((By.XPATH, xpath))
                        )
                        if login_btn:
                            used_selector = xpath
                            logger.info(f"XPath로 로그인 버튼 발견: {xpath}")
                            break
                    except TimeoutException:
                        logger.debug(f"XPath {xpath} 타임아웃")
                        continue
                    except Exception as e:
                        logger.debug(f"XPath {xpath} 실패: {e}")
                        continue
            
            if not login_btn:
                raise BusinessError("네이버 로그인 버튼을 찾을 수 없습니다")
            
            # 로그인 버튼 클릭
            logger.info(f"로그인 버튼 클릭 시도 (셀렉터: {used_selector})")
            login_btn.click()
            logger.info("로그인 버튼 클릭 완료")
            
            # 로그인 결과 대기 및 확인
            return self._wait_for_login_result(credentials=credentials)
            
        except Exception as e:
            logger.error(f"로그인 수행 실패: {e}")
            return LoginStatus.LOGIN_FAILED
    
    def _wait_for_login_result(self, timeout: int = 90, credentials=None) -> LoginStatus:
        """로그인 결과 대기 - 간단한 URL 체크"""
        logger.info("로그인 결과 대기 시작...")

        start_time = time.time()
        device_registration_attempted = False

        while (time.time() - start_time) < timeout:
            try:
                current_url = self.helper.current_url
                logger.info(f"🔍 현재 URL: {current_url}")

                # 1. 기기 등록 페이지 → 등록안함 버튼 클릭 (먼저 체크!)
                if "deviceConfirm" in current_url and not device_registration_attempted:
                    logger.info("🆔 새로운 기기 등록 페이지 감지!")
                    device_registration_attempted = True

                    try:
                        # WebDriverWait으로 등록안함 버튼이 클릭 가능할 때까지 대기
                        from selenium.webdriver.support.ui import WebDriverWait
                        from selenium.webdriver.support import expected_conditions as EC

                        logger.info("등록안함 버튼이 나타날 때까지 대기 중...")
                        wait = WebDriverWait(self.helper.driver, 15)

                        # 다양한 셀렉터로 등록안함 버튼 찾기 시도 (정확한 HTML 구조 기반)
                        selectors = [
                            "#new\\.dontsave",  # CSS 이스케이프 방식
                            "[id='new.dontsave']",  # 속성 방식
                            "a[id='new.dontsave']",  # 태그+속성 방식
                            ".btn_cancel a",  # 부모 클래스 > 자식
                            ".btn_cancel a.btn",  # 더 구체적
                            "//a[@id='new.dontsave']",  # XPath 방식
                            "//a[contains(text(), '등록안함')]",
                            "//span[@class='btn_cancel']//a",
                            ".btn_cancel",
                            "#skipBtn",
                            "#cancelBtn"
                        ]

                        skip_button = None
                        used_selector = None

                        for i, selector in enumerate(selectors, 1):
                            try:
                                logger.info(f"[{i}/{len(selectors)}] 등록안함 버튼 찾는 중... (셀렉터: {selector})")

                                # 각 셀렉터마다 짧은 대기 시간 사용
                                short_wait = WebDriverWait(self.helper.driver, 3)

                                if selector.startswith("//"):
                                    # XPath 셀렉터
                                    logger.debug(f"XPath 셀렉터 사용: {selector}")
                                    skip_button = short_wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                                else:
                                    # CSS 셀렉터
                                    logger.debug(f"CSS 셀렉터 사용: {selector}")
                                    skip_button = short_wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))

                                used_selector = selector
                                logger.info(f"✅ 버튼 발견! 셀렉터: {used_selector}")
                                logger.info(f"📍 버튼 위치: {skip_button.location}")
                                logger.info(f"📏 버튼 크기: {skip_button.size}")
                                logger.info(f"📝 버튼 텍스트: '{skip_button.text}'")
                                logger.info(f"🔗 버튼 태그: {skip_button.tag_name}")
                                break
                            except Exception as e:
                                logger.debug(f"❌ 셀렉터 [{i}/{len(selectors)}] {selector} 실패: {e}")
                                if i == len(selectors):
                                    logger.error(f"🚨 모든 셀렉터 실패! 페이지 상태 확인:")
                                    try:
                                        page_title = self.helper.driver.title
                                        logger.error(f"📄 페이지 제목: {page_title}")
                                        body_text = self.helper.driver.find_element(By.TAG_NAME, "body").text[:200]
                                        logger.error(f"📝 페이지 내용 (첫 200자): {body_text}")
                                    except Exception as debug_error:
                                        logger.error(f"페이지 상태 확인 실패: {debug_error}")
                                continue

                        if skip_button is None:
                            # 페이지 소스를 확인해서 디버그 정보 제공
                            page_source = self.helper.driver.page_source
                            if "등록안함" in page_source:
                                logger.warning("페이지에 '등록안함' 텍스트는 있지만 버튼을 찾을 수 없습니다")
                            if "나중에" in page_source:
                                logger.warning("페이지에 '나중에' 텍스트는 있지만 버튼을 찾을 수 없습니다")
                            raise Exception("등록안함 버튼을 찾을 수 없습니다")

                        logger.info(f"🎯 등록안함 버튼 클릭 시작... (사용된 셀렉터: {used_selector})")

                        # 버튼 상태 확인
                        logger.info(f"🔍 클릭 전 버튼 상태:")
                        logger.info(f"   - 표시됨: {skip_button.is_displayed()}")
                        logger.info(f"   - 활성화됨: {skip_button.is_enabled()}")

                        # 버튼을 화면에 보이도록 스크롤
                        logger.info("📜 버튼을 화면에 표시하기 위해 스크롤 중...")
                        self.helper.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", skip_button)
                        time.sleep(1)

                        # 스크롤 후 상태 재확인
                        logger.info(f"🔍 스크롤 후 버튼 상태:")
                        logger.info(f"   - 표시됨: {skip_button.is_displayed()}")
                        logger.info(f"   - 활성화됨: {skip_button.is_enabled()}")
                        logger.info(f"   - 현재 위치: {skip_button.location}")

                        # JavaScript 클릭을 우선 시도 (href="#" 링크이므로)
                        click_success = False
                        try:
                            logger.info("🖱️  JavaScript 클릭 시도 중...")
                            # 클릭 전 마지막 상태 확인
                            if not skip_button.is_displayed():
                                logger.warning("⚠️  버튼이 화면에 표시되지 않음!")
                            if not skip_button.is_enabled():
                                logger.warning("⚠️  버튼이 비활성화 상태!")

                            self.helper.driver.execute_script("arguments[0].click();", skip_button)
                            logger.info("✅ JavaScript 클릭 명령 실행 완료")
                            click_success = True
                        except Exception as js_error:
                            logger.warning(f"❌ JavaScript 클릭 실패: {js_error}")
                            try:
                                logger.info("🖱️  일반 Selenium 클릭 시도 중...")
                                skip_button.click()
                                logger.info("✅ 일반 클릭 성공")
                                click_success = True
                            except Exception as click_error:
                                logger.error(f"❌ 모든 클릭 방법 실패: {click_error}")
                                logger.error(f"🔍 실패 시점 버튼 상태:")
                                logger.error(f"   - 표시됨: {skip_button.is_displayed()}")
                                logger.error(f"   - 활성화됨: {skip_button.is_enabled()}")
                                logger.error(f"   - 위치: {skip_button.location}")
                                raise

                        if click_success:
                            logger.info("🎉 등록안함 버튼 클릭 완료!")
                            logger.info("⏳ 2초 대기 후 URL 변경 확인...")

                        # 2초 대기 후 URL 확인
                        time.sleep(2)
                        new_url = self.helper.current_url
                        logger.info(f"🔗 클릭 후 URL: {new_url}")

                        # URL 변경 상세 분석
                        if "deviceConfirm" not in new_url:
                            logger.info("✅ 기기 등록 처리 완료! 성공적으로 페이지 이동")
                            if "BlogHome.naver" in new_url or "section.blog.naver.com" in new_url:
                                logger.info("🎉 블로그 홈으로 이동 완료!")
                            elif "nidlogin.login" in new_url:
                                logger.info("🔄 로그인 페이지로 돌아감 - 로그인 계속 진행")
                            else:
                                logger.info(f"📍 새로운 페이지로 이동: {new_url}")
                            continue
                        else:
                            logger.warning("⚠️  아직 deviceConfirm 페이지에 있음")
                            logger.warning("🤔 클릭이 제대로 처리되지 않았거나 페이지 로딩 지연일 수 있음")

                            # 추가 대기 후 재시도
                            logger.info("⏳ 3초 더 대기 후 재확인...")
                            time.sleep(3)
                            final_url = self.helper.current_url
                            logger.info(f"🔗 재확인 URL: {final_url}")

                            if "deviceConfirm" not in final_url:
                                logger.info("✅ 지연 후 페이지 이동 확인됨")
                                continue
                            else:
                                logger.error("❌ 클릭 후에도 여전히 deviceConfirm 페이지에 있음")
                                logger.error("💡 수동 클릭이 필요할 수 있습니다")

                    except Exception as e:
                        logger.error(f"❌ 기기 등록 버튼 클릭 실패: {e}")
                        logger.info("💡 수동으로 등록 또는 등록안함 버튼을 클릭해주세요...")

                # 2. 로그인 성공 체크 - 최종 목적지 페이지 도달
                elif current_url.startswith("https://section.blog.naver.com/BlogHome.naver"):
                    logger.info("✅ 네이버 블로그 로그인 성공! 최종 페이지 도달")
                    self.is_logged_in = True
                    if credentials:
                        self.username = credentials.username
                        logger.info(f"👤 사용자 아이디 저장: {self.username}")
                    return LoginStatus.LOGGED_IN

                # 3. 2차 인증 페이지 → 사용자 입력 대기
                elif any(keyword in current_url for keyword in ["auth", "otp", "verify"]):
                    logger.info("🔐 2차 인증 페이지 감지 - 사용자 입력 대기 중...")
                    return LoginStatus.TWO_FACTOR_AUTH_REQUIRED

                # 4. 로그인 실패 체크 (빠른 체크)
                elif current_url == "https://nid.naver.com/nidlogin.login":
                    # 로그인 페이지에 오래 머물러 있으면 실패 가능성 높음
                    if (time.time() - start_time) > 10:  # 10초 이상
                        try:
                            error_element = self.helper.driver.find_element(By.CSS_SELECTOR, ".error_message, .alert_area")
                            if error_element and error_element.is_displayed():
                                logger.error(f"❌ 로그인 실패: {error_element.text}")
                                return LoginStatus.LOGIN_FAILED
                        except:
                            pass

                # 2초마다 확인
                time.sleep(2)

            except Exception as e:
                logger.error(f"URL 확인 중 오류: {e}")
                time.sleep(2)

        logger.error("⏰ 로그인 대기 시간 초과")
        return LoginStatus.LOGIN_FAILED
    
    # 더 이상 필요 없는 복잡한 감지 메서드들 - URL 기반으로 단순화됨
    # def _detect_two_factor_auth(self) -> bool:
    #     """2차 인증 감지 - URL 기반으로 단순화"""
    #     current_url = self.helper.current_url
    #     return any(keyword in current_url for keyword in ["auth", "otp", "verify"])
    #
    # def _detect_login_failure(self) -> bool:
    #     """로그인 실패 감지 - URL과 오류 메시지 기반으로 단순화"""
    #     try:
    #         error_element = self.helper.driver.find_element(By.CSS_SELECTOR, ".error_message, .alert_area")
    #         return error_element and error_element.is_displayed()
    #     except:
    #         return False
    
    def check_login_status(self) -> bool:
        """현재 로그인 상태 확인"""
        try:
            # 현재 URL이 블로그 홈이면 로그인됨
            current_url = self.helper.current_url
            
            if "BlogHome.naver" in current_url:
                self.is_logged_in = True
                return True
            
            # 블로그 홈으로 이동 시도
            self.helper.goto(self.blog_home_url)
            time.sleep(3)
            
            current_url = self.helper.current_url
            if "BlogHome.naver" in current_url:
                self.is_logged_in = True
                return True
            else:
                self.is_logged_in = False
                return False
                
        except Exception as e:
            logger.error(f"로그인 상태 확인 실패: {e}")
            self.is_logged_in = False
            return False
    
    def click_write_button(self) -> bool:
        """글쓰기 버튼 클릭 (현재 비활성화)"""
        logger.info("글쓰기 버튼 기능은 현재 비활성화되어 있습니다")
        return True  # 일단 성공으로 처리
    
    def handle_draft_popup(self) -> bool:
        """글쓰기 페이지에서 '작성 중인 글이 있습니다' 팝업 처리"""
        try:
            logger.info("작성 중인 글 팝업 확인 중...")
            
            wait = WebDriverWait(self.helper.driver, 5)  # 5초만 대기
            
            # 팝업 컨테이너 확인
            popup_selectors = [
                'div.se-popup-container',
                'div.__se-pop-layer',
                'div[data-layerid]'
            ]
            
            popup_found = False
            popup_element = None
            
            for selector in popup_selectors:
                try:
                    popup_element = wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if popup_element and popup_element.is_displayed():
                        logger.info(f"작성 중인 글 팝업 발견: {selector}")
                        popup_found = True
                        break
                except TimeoutException:
                    continue
                except Exception as e:
                    logger.debug(f"팝업 확인 중 오류: {e}")
                    continue
            
            if not popup_found:
                logger.info("작성 중인 글 팝업이 없음 - 정상 진행")
                return True
            
            # 팝업 제목으로 확인
            title_text = ""
            try:
                title_element = popup_element.find_element(By.CSS_SELECTOR, '.se-popup-title')
                title_text = title_element.text
                logger.info(f"팝업 제목: {title_text}")
                
                if "작성 중인 글" not in title_text:
                    logger.info("다른 종류의 팝업 - 무시")
                    return True
                    
            except Exception as e:
                logger.debug(f"팝업 제목 확인 실패: {e}")
            
            # 취소 버튼 찾기 및 클릭
            cancel_button_selectors = [
                'button.se-popup-button-cancel',
                'button.se-popup-button.se-popup-button-cancel',
                'button[class*="se-popup-button-cancel"]'
            ]
            
            cancel_button = None
            used_selector = None
            
            for selector in cancel_button_selectors:
                try:
                    cancel_button = popup_element.find_element(By.CSS_SELECTOR, selector)
                    if cancel_button and cancel_button.is_displayed():
                        used_selector = selector
                        logger.info(f"취소 버튼 발견: {selector}")
                        break
                except Exception as e:
                    logger.debug(f"취소 버튼 찾기 실패 ({selector}): {e}")
                    continue
            
            # XPath로도 시도
            if not cancel_button:
                xpath_selectors = [
                    "//button[contains(@class, 'se-popup-button-cancel')]",
                    "//button[.//span[contains(text(), '취소')]]",
                    "//span[contains(text(), '취소')]//parent::button"
                ]
                
                for xpath in xpath_selectors:
                    try:
                        cancel_button = popup_element.find_element(By.XPATH, xpath)
                        if cancel_button and cancel_button.is_displayed():
                            used_selector = xpath
                            logger.info(f"XPath로 취소 버튼 발견: {xpath}")
                            break
                    except Exception as e:
                        logger.debug(f"XPath 취소 버튼 찾기 실패 ({xpath}): {e}")
                        continue
            
            if not cancel_button:
                logger.warning("취소 버튼을 찾을 수 없음")
                return False
            
            # 취소 버튼 클릭
            try:
                logger.info(f"취소 버튼 클릭 시도 (셀렉터: {used_selector})")
                cancel_button.click()
                
                # 팝업이 사라질 때까지 잠시 대기
                time.sleep(1)
                
                # 팝업이 실제로 사라졌는지 확인
                try:
                    if popup_element.is_displayed():
                        logger.warning("팝업이 아직 표시됨 - JavaScript 클릭 시도")
                        self.helper.driver.execute_script("arguments[0].click();", cancel_button)
                        time.sleep(1)
                except:
                    pass  # 팝업이 사라졌으면 정상
                
                logger.info("✅ 작성 중인 글 팝업 취소 완료")
                return True
                
            except Exception as e:
                logger.error(f"취소 버튼 클릭 실패: {e}")
                try:
                    # JavaScript 클릭 시도
                    self.helper.driver.execute_script("arguments[0].click();", cancel_button)
                    time.sleep(1)
                    logger.info("✅ JavaScript로 취소 버튼 클릭 완료")
                    return True
                except Exception as e2:
                    logger.error(f"JavaScript 클릭도 실패: {e2}")
                    return False
            
        except TimeoutException:
            logger.info("작성 중인 글 팝업 없음 (타임아웃)")
            return True
        except Exception as e:
            logger.error(f"작성 중인 글 팝업 처리 실패: {e}")
            return False
    
    def search_top_blogs(self, keyword: str, max_results: int = 3) -> list:
        """키워드로 네이버 블로그 검색 (Selenium 방식만 사용)"""
        try:
            logger.info(f"🌐 Selenium 블로그 검색 시작: {keyword} (최대 {max_results}개)")
            
            # 분석 전용 브라우저 시작 (초기화되지 않은 경우)
            if not hasattr(self.helper, 'driver') or not self.helper.driver:
                logger.info("🔧 분석 전용 브라우저 시작")
                self.start_browser_for_analysis()
            
            # Selenium으로 블로그 검색
            selenium_blogs = self._search_blogs_via_selenium(keyword, max_results)
            
            if not selenium_blogs:
                logger.warning("❌ Selenium 블로그 검색 결과 없음")
                return []
            
            # source 필드 추가
            for blog in selenium_blogs:
                blog['source'] = 'selenium'
            
            logger.info(f"✅ Selenium 검색 완료: {len(selenium_blogs)}개 블로그 발견")
            return selenium_blogs
            
        except Exception as e:
            logger.error(f"Selenium 블로그 검색 실패: {e}")
            return []
    
    
    def _search_blogs_via_selenium(self, keyword: str, max_results: int = 3) -> list:
        """Selenium으로 블로그 검색 (기존 방식)"""
        try:
            # URL 인코딩
            import urllib.parse
            encoded_keyword = urllib.parse.quote(keyword)
            search_url = f"https://search.naver.com/search.naver?ssc=tab.blog.all&sm=tab_jum&query={encoded_keyword}"
            
            logger.info(f"Selenium 검색 URL: {search_url}")
            
            # 검색 페이지로 이동
            self.helper.goto(search_url)
            time.sleep(3)  # 페이지 로딩 대기
            
            wait = WebDriverWait(self.helper.driver, 10)
            
            # 블로그 검색 결과 수집
            blog_results = []
            
            # title_area div 찾기
            title_areas = self.helper.find_elements('div.title_area')
            logger.info(f"Selenium 검색 결과 개수: {len(title_areas)}")
            
            for i, title_area in enumerate(title_areas):
                if len(blog_results) >= max_results:
                    break
                
                try:
                    # a.title_link 찾기
                    link_element = title_area.find_element(By.CSS_SELECTOR, 'a.title_link')
                    href = link_element.get_attribute('href')
                    title = link_element.text.strip()
                    
                    # 광고 링크 제외 (ader.naver로 시작하는 링크)
                    if href and 'ader.naver.com' in href:
                        logger.info(f"광고 링크 스킵: {href[:50]}...")
                        continue
                    
                    # 네이버 블로그 링크만 허용
                    if href and 'blog.naver.com' in href:
                        logger.info(f"Selenium 블로그 발견 [{len(blog_results)+1}]: {title}")
                        logger.debug(f"링크: {href}")
                        
                        blog_info = {
                            'rank': len(blog_results) + 1,
                            'title': title,
                            'url': href,
                            'preview': title[:50] + '...' if len(title) > 50 else title,
                            'source': 'selenium'
                        }
                        blog_results.append(blog_info)
                    else:
                        logger.debug(f"네이버 블로그가 아닌 링크 스킵: {href}")
                
                except Exception as e:
                    logger.debug(f"블로그 링크 추출 오류 (항목 {i+1}): {e}")
                    continue
            
            logger.info(f"Selenium으로 {len(blog_results)}개 블로그 수집 완료")
            return blog_results
            
        except Exception as e:
            logger.error(f"Selenium 블로그 검색 실패: {e}")
            raise
    
    
    def analyze_blog_content(self, blog_url: str) -> dict:
        """개별 블로그 페이지 분석"""
        try:
            logger.info(f"블로그 콘텐츠 분석 시작: {blog_url}")
            
            # 새 탭에서 블로그 페이지 열기
            original_window = self.helper.driver.current_window_handle
            self.helper.driver.execute_script(f"window.open('{blog_url}', '_blank');")
            
            # 새 탭으로 전환
            new_window = None
            for handle in self.helper.driver.window_handles:
                if handle != original_window:
                    new_window = handle
                    break
            
            if new_window:
                self.helper.driver.switch_to.window(new_window)
                
                # 페이지 초기 로딩 대기
                wait = WebDriverWait(self.helper.driver, 10)
                wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
                
                # 블로그 콘텐츠 컨테이너가 로드될 때까지 대기
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.se-main-container, #post_view, .post_content')))
                except:
                    logger.debug("블로그 콘텐츠 컨테이너 대기 타임아웃 - 계속 진행")
                
                # iframe이 있는지 확인하고 전환
                is_iframe = self._handle_iframe_if_exists()
                
                # 자연스러운 스크롤 다운으로 모든 콘텐츠 로드 (iframe 내부에서)
                self._smooth_scroll_to_bottom()
                
            else:
                raise Exception("새 탭을 찾을 수 없습니다")
            
            analysis_result = {
                'url': blog_url,
                'title': '',
                'content_length': 0,
                'image_count': 0,
                'gif_count': 0,
                'video_count': 0,
                'tags': [],
                'text_content': '',
                'content_structure': []  # 글-이미지-글 순서 구조
            }
            
            # 제목 추출 (스마트에디터 모듈 우선)
            try:
                # 1. 스마트에디터 3.0 제목 모듈에서 추출
                title_module = self.helper.find_element('.se-module.se-module-text.se-title-text')
                if title_module:
                    title_text = title_module.get_attribute('textContent') or title_module.text or ''
                    clean_title = ' '.join(title_text.split())  # 공백 정리
                    if clean_title:
                        analysis_result['title'] = clean_title
                        logger.info(f"스마트에디터 제목 추출: {analysis_result['title']}")
                
                # 2. fallback 선택자들
                if not analysis_result['title']:
                    title_selectors = [
                        'h3.se-title-text',  # 스마트에디터 3.0
                        '.se-title-text',
                        'h2.htitle',  # 구 에디터
                        '.blog-title',
                        'h1', 'h2', 'h3'
                    ]
                    
                    for selector in title_selectors:
                        title_element = self.helper.find_element(selector)
                        if title_element:
                            title_text = title_element.get_attribute('textContent') or title_element.text or ''
                            clean_title = ' '.join(title_text.split())
                            if clean_title:
                                analysis_result['title'] = clean_title
                                logger.info(f"Fallback 제목 추출: {analysis_result['title']} - {selector}")
                                break
                                
            except Exception as e:
                logger.debug(f"제목 추출 실패: {e}")
            
            # 본문 텍스트 길이 계산 (정확하고 빠른 방식)
            try:
                total_text = ""
                
                # 1. 본문 텍스트 모듈만 추출 (제목/캐션 제외, 속도 최적화)
                text_modules = self.helper.find_elements('.se-module.se-module-text:not(.se-title-text):not(.se-caption):not(.se-quote)')
                
                if text_modules:
                    for module in text_modules:
                        try:
                            module_text = module.get_attribute('textContent') or module.text or ''
                            if module_text:
                                clean_text = ' '.join(module_text.split())
                                if clean_text:
                                    total_text += clean_text + ' '
                        except:
                            continue
                else:
                    # fallback: 전체 컨테이너에서 추출
                    content_selectors = [
                        '.se-viewer',
                        '#post_view',  # 구 에디터
                        '.post_content'
                    ]
                    
                    for selector in content_selectors:
                        content_element = self.helper.find_element(selector)
                        if content_element:
                            text_content = content_element.get_attribute('textContent') or content_element.text or ''
                            total_text = ' '.join(text_content.split())
                            if total_text:
                                break
                
                # 결과 설정
                final_text = total_text.strip()
                analysis_result['content_length'] = len(final_text.replace(' ', ''))  # 공백 제거한 글자수
                analysis_result['text_content'] = final_text  # 전체 텍스트 사용 (정보요약 AI를 위해)
                
                logger.info(f"본문 글자수 (공백제거): {analysis_result['content_length']}")
                
            except Exception as e:
                logger.debug(f"본문 분석 실패: {e}")
            
            # 이미지/GIF 개수 분석 (빠른 방식)
            try:
                # 스마트에디터 이미지 모듈 개수 (빠른 카운트)
                se_image_modules = self.helper.find_elements('.se-module.se-module-image')
                
                # 간단한 GIF 감지 (정확도보다 속도 우선)
                gif_count = 0
                regular_images = len(se_image_modules)
                
                # GIF는 video._gifmp4 태그로만 빠르게 감지
                gif_videos = self.helper.find_elements('video._gifmp4')
                gif_count = len(gif_videos)
                regular_images = max(0, regular_images - gif_count)
                
                # fallback: 스마트에디터 없으면 일반 img 태그
                if len(se_image_modules) == 0:
                    all_images = self.helper.find_elements('img')
                    regular_images = len(all_images)
                    # 간단한 GIF 감지
                    for img in all_images:
                        src = img.get_attribute('src') or ''
                        if '.gif' in src.lower():
                            gif_count += 1
                            regular_images -= 1
                
                analysis_result['image_count'] = regular_images
                analysis_result['gif_count'] = gif_count
                logger.info(f"이미지/GIF 분석 완료 - 일반: {regular_images}, GIF: {gif_count}")
                
            except Exception as e:
                logger.debug(f"이미지 분석 실패: {e}")
            
            # 동영상 개수 분석 (중복 방지)
            try:
                video_count = 0
                
                # 1. 스마트에디터 3.0 비디오 모듈 (가장 정확한 방법)
                se_video_modules = self.helper.find_elements('.se-module.se-module-video')
                video_count = len(se_video_modules)
                logger.debug(f"스마트에디터 비디오 모듈: {len(se_video_modules)}개")
                
                # 2. 스마트에디터 모듈이 없으면 웹플레이어로 카운트 (fallback)
                if video_count == 0:
                    webplayer_videos = self.helper.find_elements('.webplayer-internal-source-wrapper')
                    video_count = len(webplayer_videos)
                    logger.debug(f"네이버 웹플레이어 동영상: {len(webplayer_videos)}개")
                
                # 3. 둘 다 없으면 외부 동영상 (YouTube, Vimeo) 카운트 (fallback)
                if video_count == 0:
                    external_videos = self.helper.find_elements('iframe[src*="youtube"], iframe[src*="vimeo"], iframe[src*="youtu.be"]')
                    video_count = len(external_videos)
                    logger.debug(f"외부 동영상: {len(external_videos)}개")
                
                analysis_result['video_count'] = video_count
                logger.info(f"동영상 분석 완료 - 총 {video_count}개 (중복 제거)")
                
            except Exception as e:
                logger.debug(f"동영상 분석 실패: {e}")
            
            # 태그 추출 (네이버 블로그 태그 영역 우선)
            try:
                tags = []
                
                # 1. 네이버 블로그 태그 영역에서 #태그 추출
                tag_list_div = self.helper.find_element('div[id*="tagList_"]')
                if tag_list_div:
                    # 태그 링크들 찾기
                    tag_links = tag_list_div.find_elements(By.CSS_SELECTOR, 'a.item.pcol2.itemTagfont')
                    for tag_link in tag_links:
                        try:
                            # span.ell 안의 텍스트 추출
                            span_element = tag_link.find_element(By.CSS_SELECTOR, 'span.ell')
                            tag_text = span_element.text.strip()
                            if tag_text and tag_text.startswith('#'):
                                tags.append(tag_text)
                        except Exception as tag_error:
                            logger.debug(f"개별 태그 추출 오류: {tag_error}")
                    
                    if tags:
                        analysis_result['tags'] = tags  # 모든 태그 가져오기 (제한 없음)
                        logger.info(f"네이버 블로그 태그 추출 완료: {len(tags)}개 - {tags[:5]}{'...' if len(tags) > 5 else ''}")
                
                # 2. 태그가 없으면 대체 방법들 시도
                if not tags:
                    fallback_selectors = [
                        '.se-module.se-module-text .se-tag-text',  # 스마트에디터 3.0 태그
                        '.se-tag-text',  # 스마트에디터 태그
                        '.blog2_tag_area a span',  # 블로그 태그 영역 span
                        '.tag',
                        '.post-tag',
                        'a[href*="tag"]'
                    ]
                    
                    for selector in fallback_selectors:
                        tag_elements = self.helper.find_elements(selector)
                        if tag_elements:
                            fallback_tags = []
                            for tag_element in tag_elements:
                                tag_text = tag_element.text.strip()
                                if tag_text:
                                    # #이 없으면 추가
                                    if not tag_text.startswith('#'):
                                        tag_text = '#' + tag_text
                                    fallback_tags.append(tag_text)
                            
                            if fallback_tags:
                                analysis_result['tags'] = fallback_tags
                                logger.info(f"대체 태그 추출 완료: {len(fallback_tags)}개 - {selector}")
                                break
                
            except Exception as e:
                logger.debug(f"태그 분석 실패: {e}")
            
            # 콘텐츠 구조 분석 (상세 스마트에디터 구조)
            try:
                content_structure = self._extract_content_structure_selenium()
                analysis_result['content_structure'] = content_structure
                logger.info(f"콘텐츠 구조 추출 완료: {len(content_structure)}개 요소")
            except Exception as e:
                logger.debug(f"콘텐츠 구조 추출 실패: {e}")
            
            # iframe에서 빠져나오기 (분석 완료 후)
            self._exit_iframe_if_exists()
            
            # 원래 탭으로 돌아가기
            self.helper.driver.close()  # 새 탭 닫기
            self.helper.driver.switch_to.window(original_window)
            
            logger.info(f"블로그 분석 완료: 제목={analysis_result['title'][:30]}..., 글자수(공백제거)={analysis_result['content_length']}, 이미지={analysis_result['image_count']}, GIF={analysis_result['gif_count']}, 동영상={analysis_result['video_count']}, 태그={len(analysis_result['tags'])}개, 구조={len(analysis_result['content_structure'])}개")
            return analysis_result
            
        except Exception as e:
            logger.error(f"블로그 콘텐츠 분석 실패 ({blog_url}): {e}")
            
            # 오류 발생 시 원래 탭으로 복귀 시도
            try:
                if len(self.helper.driver.window_handles) > 1:
                    self.helper.driver.close()
                self.helper.driver.switch_to.window(original_window)
            except:
                pass
            
            return {
                'url': blog_url,
                'title': '분석 실패',
                'category': '',
                'publish_date': '',
                'content_length': 0,
                'image_count': 0,
                'gif_count': 0,
                'video_count': 0,
                'tags': [],
                'text_content': '분석 중 오류 발생',
                'content_structure': []
            }
    
    def analyze_blog_content_http(self, blog_url: str) -> dict:
        """HTTP 기반 블로그 콘텐츠 분석 (Selenium 대체)"""
        try:
            logger.info(f"HTTP 기반 블로그 분석 시작: {blog_url}")
            
            # HTTP 요청으로 페이지 컨텐츠 가져오기 (foundation HTTP 클라이언트 사용)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # 향상된 HTTP 클라이언트로 여러 URL 시도 (PostView URL + 원본 URL)
            urls_to_try = []
            
            # PostView URL 변환 시도
            postview_url = self._convert_to_postview_url(blog_url)
            if postview_url:
                urls_to_try.append(postview_url)
                logger.info(f"PostView URL 생성: {postview_url}")
            
            # 원본 URL도 시도 목록에 추가
            urls_to_try.append(blog_url)
            
            # 향상된 HTTP 클라이언트의 다중 URL 시도 기능 사용
            response = default_http_client.get_with_retry_fallback(urls_to_try, headers=headers)
            
            if not response or response.status_code != 200:
                logger.error("모든 URL에서 HTTP 요청 실패")
                return self._get_empty_analysis_result(blog_url)
            
            logger.info(f"HTTP 요청 성공: {response.status_code} - {len(response.text)} bytes")
            
            # HTML 파싱
            soup = BeautifulSoup(response.text, 'html.parser')
            logger.info(f"HTML 파싱 완료")
            
            # iframe 확인 및 실제 콘텐츠 페이지 추출
            content_soup = None
            iframe = soup.select_one('iframe#mainFrame')
            
            if iframe:
                iframe_src = iframe.get('src', '')
                if iframe_src:
                    # 상대 URL을 절대 URL로 변환
                    if iframe_src.startswith('/'):
                        iframe_url = 'https://blog.naver.com' + iframe_src
                    else:
                        iframe_url = iframe_src
                    
                    logger.info(f"iframe 콘텐츠 URL 발견: {iframe_url}")
                    
                    try:
                        # iframe 내부 콘텐츠 요청 (인코딩 자동 감지 포함)
                        iframe_response = default_http_client.get_with_encoding_detection(iframe_url, headers=headers)
                        if iframe_response.status_code == 200:
                            content_soup = BeautifulSoup(iframe_response.text, 'html.parser')
                            logger.info(f"iframe 콘텐츠 로드 성공: {len(iframe_response.text)} bytes")
                        else:
                            logger.warning(f"iframe 요청 실패: {iframe_response.status_code}")
                    except APIResponseError as e:
                        if "Resource not found" in str(e):
                            logger.warning(f"iframe 404 오류: {iframe_url}")
                        else:
                            logger.warning(f"iframe API 오류: {e}")
                    except APITimeoutError as e:
                        logger.warning(f"iframe 타임아웃: {e}")
                    except Exception as iframe_error:
                        logger.warning(f"iframe 요청 오류: {iframe_error}")
            
            # 실제 분석할 soup 결정 (iframe 콘텐츠가 있으면 그것을, 없으면 원본)
            analysis_soup = content_soup if content_soup else soup
            
            analysis_result = {
                'url': blog_url,
                'title': '',
                'content_length': 0,
                'image_count': 0,
                'gif_count': 0,
                'video_count': 0,
                'tags': [],
                'text_content': '',
                'content_structure': []
            }
            
            # 제목 추출 (원본 페이지에서 먼저, iframe에서 보완)
            title = self._extract_title_http(soup)
            if not title or title == '제목 없음':
                title = self._extract_title_http(analysis_soup)
            analysis_result['title'] = title
            logger.info(f"HTTP 제목 추출: {title}")
            
            # 본문 텍스트 추출 및 길이 계산 (iframe 콘텐츠에서)
            text_content, content_length = self._extract_text_content_http(analysis_soup)
            analysis_result['text_content'] = text_content  # 전체 텍스트 사용 (정보요약 AI를 위해)
            analysis_result['content_length'] = content_length
            logger.info(f"HTTP 본문 글자수: {content_length}")
            
            # 콘텐츠 구조 분석 (iframe 콘텐츠에서)
            content_structure = self._extract_content_structure_http(analysis_soup)
            analysis_result['content_structure'] = content_structure
            logger.info(f"HTTP 콘텐츠 구조: {len(content_structure)}개 요소")
            
            # 구조 분석 결과에서 미디어 카운트 집계 (주요 방식)
            image_count, gif_count, video_count = self._count_media_from_structure(content_structure)
            
            # 기존 방식도 참고 (비교용)
            legacy_image_count, legacy_gif_count, legacy_video_count = self._count_media_http(analysis_soup)
            logger.debug(f"구조 기반: 이미지={image_count}, GIF={gif_count}, 비디오={video_count}")
            logger.debug(f"Legacy 기반: 이미지={legacy_image_count}, GIF={legacy_gif_count}, 비디오={legacy_video_count}")
            
            # 구조 분석 결과만 사용 (가장 정확함)
            analysis_result['image_count'] = image_count
            analysis_result['gif_count'] = gif_count  
            analysis_result['video_count'] = video_count
            
            # Legacy 방식은 참고용으로만 사용 (중복 카운팅 방지)
            logger.debug(f"최종 미디어 카운트 (구조 기반): 이미지={image_count}, GIF={gif_count}, 비디오={video_count}")
            logger.debug(f"참고 (Legacy 방식): 이미지={legacy_image_count}, GIF={legacy_gif_count}, 비디오={legacy_video_count}")
            
            # Legacy에서만 발견된 특수 GIF가 있다면 추가 (video._gifmp4 태그 등)
            if legacy_gif_count > gif_count:
                additional_gifs = legacy_gif_count - gif_count
                analysis_result['gif_count'] = legacy_gif_count
                logger.debug(f"Legacy에서 추가 GIF 발견: +{additional_gifs}개 -> 총 {legacy_gif_count}개")
            
            logger.info(f"HTTP 미디어 카운트 - 이미지: {analysis_result['image_count']}, GIF: {analysis_result['gif_count']}, 비디오: {analysis_result['video_count']}")
            
            # HTTP 분석: HTML과 본문 텍스트에서 해시태그 패턴 추출
            logger.info("HTTP 분석: 해시태그 패턴 추출 중...")
            content_hashtags = self._extract_content_hashtags_from_html(analysis_soup, text_content)
            analysis_result['tags'] = content_hashtags[:10]  # 최대 10개
            logger.info(f"해시태그 추출: {len(analysis_result['tags'])}개")
            
            logger.info(f"HTTP 블로그 분석 완료: {title}")
            return analysis_result
            
        except APIResponseError as e:
            logger.error(f"HTTP API 응답 오류 ({blog_url}): {e}")
            return self._get_empty_analysis_result(blog_url)
        except APITimeoutError as e:
            logger.error(f"HTTP 타임아웃 오류 ({blog_url}): {e}")
            return self._get_empty_analysis_result(blog_url)
        except Exception as e:
            logger.error(f"HTTP 블로그 분석 실패 ({blog_url}): {e}")
            return self._get_empty_analysis_result(blog_url)
    
    def _convert_to_postview_url(self, blog_url: str) -> str:
        """네이버 블로그 URL을 PostView URL로 변환"""
        try:
            # 이미 PostView URL인 경우
            if "PostView.naver" in blog_url:
                return blog_url
            
            # 일반 네이버 블로그 URL에서 blogId와 logNo 추출
            # 예: https://blog.naver.com/blogid/123456789 또는 https://blog.naver.com/blogid/postid
            pattern = r'https://blog\.naver\.com/([^/]+)/(\d+)'
            match = re.search(pattern, blog_url)
            
            if match:
                blog_id = match.group(1)
                log_no = match.group(2)
                
                # PostView URL 생성
                postview_url = f"https://blog.naver.com/PostView.naver?blogId={blog_id}&logNo={log_no}"
                return postview_url
            
            logger.warning(f"URL 패턴 매칭 실패: {blog_url}")
            return None
            
        except Exception as e:
            logger.error(f"PostView URL 변환 실패: {e}")
            return None
    
    def _extract_title_http(self, soup: BeautifulSoup) -> str:
        """HTML에서 블로그 제목 추출"""
        try:
            # 다양한 제목 선택자 시도 (우선순위 순)
            title_selectors = [
                # iframe 내부 제목들
                'iframe[id*="mainFrame"] .se-title-text',
                'iframe .se-title-text',
                # 일반 제목들  
                '.se-title-text',  # 스마트에디터 3.0
                'h3.se-title-text',
                '.se-module.se-module-text.se-title-text',
                'h2.htitle',  # 구 에디터
                '.blog-title',
                'h1', 'h2', 'h3',  # 일반 헤더들
                'title'  # 페이지 타이틀 (최후 수단)
            ]
            
            for selector in title_selectors:
                element = soup.select_one(selector)
                if element:
                    title = element.get_text(strip=True)
                    # 유효한 제목 체크
                    if title and len(title) > 1 and title not in ['네이버 블로그', 'Naver Blog', '블로그']:
                        logger.debug(f"제목 추출 성공 ({selector}): {title}")
                        return title
            
            # 메타 태그에서도 시도
            meta_title = soup.select_one('meta[property="og:title"]')
            if meta_title:
                title = meta_title.get('content', '').strip()
                if title and title != '네이버 블로그':
                    logger.debug(f"메타 제목 추출: {title}")
                    return title
            
            return '제목 없음'
            
        except Exception as e:
            logger.debug(f"HTTP 제목 추출 실패: {e}")
            return '제목 없음'
    
    def _extract_text_content_http(self, soup: BeautifulSoup) -> tuple:
        """HTML에서 본문 텍스트 추출 및 길이 계산"""
        try:
            total_text = ""
            
            # 스마트에디터 3.0 텍스트 모듈 추출 (제목 제외)
            text_modules = soup.select('.se-module.se-module-text:not(.se-title-text):not(.se-caption)')
            
            if text_modules:
                logger.debug(f"스마트에디터 텍스트 모듈 {len(text_modules)}개 발견")
                for module in text_modules:
                    module_text = module.get_text(strip=True)
                    if module_text:
                        total_text += module_text + ' '
            
            # 추가 텍스트 추출 시도 (fallback)
            if not total_text.strip():
                fallback_selectors = [
                    '.se-viewer',
                    '#post_view', 
                    '.post_content',
                    '.se-main-container',
                    '.blog2_series',
                    'body'  # 최후 수단
                ]
                
                for selector in fallback_selectors:
                    element = soup.select_one(selector)
                    if element:
                        logger.debug(f"Fallback 선택자 시도: {selector}")
                        # 불필요한 요소들 제거
                        for unwanted in element(['script', 'style', 'nav', 'header', 'footer', 'aside', '.sidebar']):
                            unwanted.decompose()
                        
                        text_content = element.get_text(strip=True)
                        if text_content and len(text_content) > 100:  # 최소 100자 이상
                            total_text = text_content
                            logger.debug(f"Fallback 성공: {len(text_content)}자")
                            break
            
            # 메타 description도 시도 (추가 정보용)
            if not total_text.strip():
                meta_desc = soup.select_one('meta[name="description"]')
                if meta_desc:
                    desc_content = meta_desc.get('content', '').strip()
                    if desc_content:
                        total_text = desc_content
                        logger.debug(f"메타 설명 사용: {desc_content[:50]}...")
            
            # 공백 정리 및 길이 계산
            clean_text = ' '.join(total_text.split()) if total_text else ""
            content_length = len(clean_text.replace(' ', ''))  # 공백 제거한 글자수
            
            logger.debug(f"최종 텍스트 길이: {content_length}자")
            return clean_text, content_length
            
        except Exception as e:
            logger.debug(f"HTTP 본문 추출 실패: {e}")
            return "", 0
    
    def _count_media_http(self, soup: BeautifulSoup) -> tuple:
        """HTML에서 이미지, GIF, 비디오 개수 카운트 (개선된 GIF 감지)"""
        try:
            # 1. 실제 GIF 감지 (video._gifmp4 태그)
            gif_videos = soup.select('video._gifmp4')
            gif_count = len(gif_videos)
            
            # 2. 이미지 요소들 검사
            all_images = soup.select('img')
            image_count = 0
            
            for img in all_images:
                src = img.get('src', '')
                if self._is_actual_gif(src):
                    gif_count += 1
                    logger.debug(f"Legacy GIF 감지: {src}")
                else:
                    image_count += 1
            
            # 3. 스마트에디터 모듈 기반 카운트 (보조적으로)
            se_image_modules = soup.select('.se-module.se-module-image')
            se_image_count = len(se_image_modules)
            
            # 구조 분석 결과와 비교해서 더 정확한 값 사용
            if se_image_count > image_count:
                logger.debug(f"SE 모듈 기반 카운트가 더 많음: {se_image_count} vs {image_count}")
                image_count = se_image_count
            
            # 4. 비디오 카운트
            video_modules = soup.select('.se-module.se-module-video')
            video_count = len(video_modules)
            
            # fallback: 웹플레이어 또는 외부 동영상
            if video_count == 0:
                webplayer_videos = soup.select('.webplayer-internal-source-wrapper')
                external_videos = soup.select('iframe[src*="youtube"], iframe[src*="vimeo"], iframe[src*="youtu.be"]')
                video_count = len(webplayer_videos) + len(external_videos)
            
            logger.debug(f"Legacy HTTP 미디어 카운트: 이미지={image_count}, GIF={gif_count}, 비디오={video_count}")
            return image_count, gif_count, video_count
            
        except Exception as e:
            logger.debug(f"HTTP 미디어 카운트 실패: {e}")
            return 0, 0, 0
    
    def _extract_content_hashtags_from_html(self, soup: BeautifulSoup, text_content: str) -> list:
        """HTML과 본문 텍스트에서 해시태그 패턴 추출 (네이버 스마트에디터 해시태그 포함)"""
        try:
            logger.debug("해시태그 추출 시작")
            hashtags = []
            
            # 1. 네이버 스마트에디터 해시태그 클래스에서 직접 추출 (최우선)
            se_hashtag_elements = soup.select('span.__se-hash-tag')
            logger.debug(f"스마트에디터 해시태그 요소: {len(se_hashtag_elements)}개")
            
            for element in se_hashtag_elements:
                tag_text = element.get_text(strip=True)
                if tag_text and tag_text.startswith('#') and len(tag_text) >= 3:  # 최소 #XX 형태
                    if tag_text not in hashtags:
                        hashtags.append(tag_text)
                        logger.debug(f"스마트에디터 해시태그 발견: {tag_text}")
            
            # 2. 본문 텍스트에서 해시태그 패턴도 추가로 찾기
            if text_content:
                text_hashtags = self._extract_content_hashtags(text_content)
                for tag in text_hashtags:
                    if tag not in hashtags:
                        hashtags.append(tag)
            
            # 3. HTML 전체에서 해시태그 패턴 백업 검색 (스마트에디터가 없는 경우)
            if not hashtags:
                logger.debug("스마트에디터 해시태그 없음, 본문에서만 패턴 검색")
                # HTML 전체가 아닌 본문 텍스트에서만 검색 (CSS/HTML ID 혼입 방지)
                if text_content:
                    html_hashtags = self._extract_content_hashtags(text_content)
                    hashtags.extend(html_hashtags)
            
            # 중복 제거 및 정렬
            unique_hashtags = []
            for tag in hashtags:
                if tag not in unique_hashtags:
                    unique_hashtags.append(tag)
            
            # 길이순 정렬 (긴 것부터 - 더 구체적일 가능성)
            unique_hashtags.sort(key=len, reverse=True)
            
            if unique_hashtags:
                logger.info(f"해시태그 추출 성공: {len(unique_hashtags)}개 - {unique_hashtags[:3]}{'...' if len(unique_hashtags) > 3 else ''}")
            else:
                logger.debug("해시태그를 찾지 못함")
            
            return unique_hashtags[:15]  # 최대 15개 (나중에 10개로 제한됨)
            
        except Exception as e:
            logger.debug(f"해시태그 추출 실패: {e}")
            return []
    
    def _extract_content_hashtags(self, text_content: str) -> list:
        """본문 텍스트에서 해시태그 패턴 추출 (블로거가 본문에 직접 입력한 태그들)"""
        try:
            if not text_content:
                return []
            
            logger.debug(f"본문 해시태그 추출 시작: {len(text_content)} 글자")
            
            import re
            hashtags = []
            
            # 1. 기본 해시태그 패턴 (#한글영숫자)
            basic_pattern = r'#([가-힣a-zA-Z0-9_]+)'
            basic_matches = re.findall(basic_pattern, text_content)
            
            for match in basic_matches:
                hashtag = f"#{match}"
                if hashtag not in hashtags and len(match) >= 2:  # 최소 2글자 이상
                    hashtags.append(hashtag)
            
            logger.debug(f"기본 패턴 해시태그: {len(hashtags)}개")
            
            # 2. 본문 마지막 부분에 있는 태그들 우선 처리 (더 정확한 태그일 가능성 높음)
            # 마지막 200자에서 해시태그가 집중되어 있는지 확인
            if len(text_content) > 200:
                last_part = text_content[-200:]
                last_part_hashtags = re.findall(basic_pattern, last_part)
                
                if len(last_part_hashtags) >= 3:  # 마지막 부분에 태그가 많으면 우선순위
                    logger.debug(f"마지막 200자에서 {len(last_part_hashtags)}개 해시태그 발견 - 우선순위 적용")
                    
                    # 마지막 부분의 태그들을 앞쪽에 배치
                    priority_tags = []
                    remaining_tags = []
                    
                    for hashtag in hashtags:
                        tag_name = hashtag[1:]  # # 제거
                        if tag_name in last_part_hashtags:
                            priority_tags.append(hashtag)
                        else:
                            remaining_tags.append(hashtag)
                    
                    hashtags = priority_tags + remaining_tags
            
            # 3. 콤마나 공백으로 구분된 연속 해시태그 패턴도 확인
            # 예: #민생회복지원금,#지원금,#민생회복2025 또는 #민생회복지원금 #지원금 #민생회복2025
            consecutive_pattern = r'#[가-힣a-zA-Z0-9_]+(?:[,\s]*#[가-힣a-zA-Z0-9_]+)+'
            consecutive_matches = re.findall(consecutive_pattern, text_content)
            
            for match in consecutive_matches:
                # 연속 패턴에서 개별 해시태그들 추출
                individual_tags = re.findall(r'#([가-힣a-zA-Z0-9_]+)', match)
                for tag in individual_tags:
                    hashtag = f"#{tag}"
                    if hashtag not in hashtags and len(tag) >= 2:
                        hashtags.append(hashtag)
            
            logger.debug(f"연속 패턴 추가 후: {len(hashtags)}개")
            
            # 4. 일반적이지 않은 태그들 필터링
            filtered_hashtags = []
            
            # 제외할 패턴들 (CSS/HTML 요소, 너무 일반적이거나 의미없는 것들)
            exclude_patterns = [
                r'^#\d+$',  # 순수 숫자만
                r'^#[a-zA-Z_\-]+$',  # 순수 영어만 (한글 없음) - CSS ID 형태
                r'^#.{1}$',  # 1글자
                r'^#(좋아요|감사|부탁|댓글|공감|추천)$',  # 너무 일반적인 단어들
                # CSS/HTML 관련 패턴들
                r'^#(wrapper|container|content|main|header|footer|sidebar).*',
                r'^#(post|blog|article|div|section|span|p).*',
                r'^#.*(_|-).*$',  # 언더스코어나 하이픈 포함 (CSS ID 패턴)
                r'^#(floating|banword|btn|bw_).*',  # 네이버 블로그 특정 요소들
                r'^#[0-9a-fA-F]{6}$',  # 색상 코드
                r'^#[0-9a-fA-F]{3}$',   # 짧은 색상 코드
            ]
            
            for hashtag in hashtags:
                should_exclude = False
                for pattern in exclude_patterns:
                    if re.match(pattern, hashtag):
                        should_exclude = True
                        break
                
                if not should_exclude:
                    filtered_hashtags.append(hashtag)
            
            logger.debug(f"필터링 후 최종: {len(filtered_hashtags)}개")
            
            # 5. 중복 제거 및 길이순 정렬 (긴 태그가 더 구체적일 가능성)
            unique_hashtags = []
            for hashtag in filtered_hashtags:
                if hashtag not in unique_hashtags:
                    unique_hashtags.append(hashtag)
            
            # 길이순 정렬 (긴 것부터)
            unique_hashtags.sort(key=len, reverse=True)
            
            if unique_hashtags:
                logger.info(f"본문 해시태그 추출 성공: {len(unique_hashtags)}개 - {unique_hashtags[:3]}{'...' if len(unique_hashtags) > 3 else ''}")
            else:
                logger.debug("본문에서 해시태그를 찾지 못함")
            
            return unique_hashtags[:15]  # 최대 15개 (나중에 10개로 제한됨)
            
        except Exception as e:
            logger.debug(f"본문 해시태그 추출 실패: {e}")
            return []
    
    def _count_media_from_structure(self, content_structure: list) -> tuple:
        """구조 분석 결과에서 미디어 개수 집계 (개선된 GIF 감지)"""
        try:
            image_count = 0
            gif_count = 0  
            video_count = 0
            
            for component in content_structure:
                comp_type = component.get('type', '')
                
                if comp_type == 'image':
                    # 이미지인데 실제 GIF인지 정확히 확인
                    src = component.get('attributes', {}).get('src', '')
                    if self._is_actual_gif(src):
                        gif_count += 1
                        logger.debug(f"GIF 감지: {src}")
                    else:
                        image_count += 1
                        logger.debug(f"이미지 감지: {src}")
                
                elif comp_type == 'gallery':
                    # 갤러리의 이미지들 개수 추가
                    gallery_image_count = component.get('attributes', {}).get('image_count', 0)
                    
                    # 갤러리 이미지들 중 실제 GIF 확인
                    image_urls = component.get('attributes', {}).get('image_urls', [])
                    gallery_gif_count = 0
                    
                    for url in image_urls:
                        if self._is_actual_gif(url):
                            gallery_gif_count += 1
                    
                    gif_count += gallery_gif_count
                    image_count += (gallery_image_count - gallery_gif_count)
                
                elif comp_type == 'video':
                    video_count += 1
                
                elif comp_type == 'sticker':
                    # 스티커는 블로그 콘텐츠가 아닌 표현/장식용이므로 
                    # 실제 이미지 개수에서 제외 (카운트하지 않음)
                    pass
                
                elif comp_type == 'image_strip':
                    # 이미지 스트립/슬라이더의 이미지들 개수 추가
                    strip_image_count = component.get('attributes', {}).get('image_count', 0)
                    
                    # 스트립 이미지들 중 실제 GIF 확인
                    image_urls = component.get('attributes', {}).get('image_urls', [])
                    strip_gif_count = 0
                    
                    for url in image_urls:
                        if self._is_actual_gif(url):
                            strip_gif_count += 1
                    
                    gif_count += strip_gif_count
                    image_count += (strip_image_count - strip_gif_count)
                
                elif comp_type == 'oglink':
                    # OG 링크 프리뷰의 썸네일은 외부 사이트 미리보기용이므로 
                    # 블로그 실제 이미지 개수에서 제외 (카운트하지 않음)
                    pass
            
            logger.debug(f"구조 기반 미디어 카운트: 이미지={image_count}, GIF={gif_count}, 비디오={video_count}")
            return image_count, gif_count, video_count
            
        except Exception as e:
            logger.debug(f"구조 기반 미디어 카운트 실패: {e}")
            return 0, 0, 0
    
    def _is_actual_gif(self, url: str) -> bool:
        """실제 GIF 파일인지 정확히 판단"""
        if not url:
            return False
        
        url_lower = url.lower()
        
        # 확실한 GIF 패턴
        definite_gif_patterns = [
            '.gif?',  # 실제 .gif 확장자
            '.gifv',  # gifv 포맷
            'format=gif',  # URL 파라미터로 gif 명시
            'type=gif',
            '_gif.',   # 파일명에 gif 포함
        ]
        
        # 네이버 블로그 특수 패턴 (실제로는 정적 이미지)
        naver_image_patterns = [
            'postfiles.pstatic.net',  # 네이버 정적 이미지
            'type=w80_blur',  # 블러 썸네일
            'type=w773',      # 리사이즈 이미지
            'type=w80',       # 작은 썸네일
            '.jpeg',          # JPEG 이미지
            '.jpg',           # JPG 이미지
            '.png',           # PNG 이미지
        ]
        
        # 네이버 정적 이미지 패턴이면 GIF가 아님
        for pattern in naver_image_patterns:
            if pattern in url_lower:
                return False
        
        # 확실한 GIF 패턴이면 GIF
        for pattern in definite_gif_patterns:
            if pattern in url_lower:
                return True
        
        return False
    
    # =================================
    # 공통 HTML 구조 분석 (HTTP/Selenium 통합)
    # =================================
    
    def _extract_content_structure_unified(self, soup: BeautifulSoup) -> list:
        """통합된 네이버 스마트에디터 콘텐츠 구조 분석 (HTTP/Selenium 공용)"""
        try:
            content_structure = []
            
            # 스마트에디터 메인 컨테이너에서 컴포넌트들을 순서대로 찾기
            main_container = soup.select_one('.se-main-container')
            if not main_container:
                # fallback: 전체 문서에서 se-component 찾기
                components = soup.select('.se-component')
            else:
                components = main_container.select('.se-component')
            
            logger.debug(f"발견된 se-component 개수: {len(components)}")
            
            for i, component in enumerate(components):
                component_info = self._analyze_se_component_unified(component, i + 1)
                if component_info:
                    content_structure.append(component_info)
            
            logger.debug(f"분석된 콘텐츠 구조: {len(content_structure)}개")
            return content_structure
            
        except Exception as e:
            logger.debug(f"통합 콘텐츠 구조 분석 실패: {e}")
            return []
    
    def _analyze_se_component_unified(self, component, order: int) -> dict:
        """통합된 개별 se-component 분석 (HTTP/Selenium 공용)"""
        try:
            # BeautifulSoup과 WebElement 둘 다 지원
            if hasattr(component, 'get'):  # BeautifulSoup
                classes = component.get('class', [])
                html_str = str(component)
            else:  # WebElement
                classes = component.get_attribute('class').split() if component.get_attribute('class') else []
                html_str = component.get_attribute('outerHTML')
            
            component_info = {
                'order': order,
                'type': 'unknown',
                'subtype': '',
                'content': '',
                'attributes': {},
                'raw_html': html_str[:200] + '...' if len(html_str) > 200 else html_str
            }
            
            # 1. 텍스트 컴포넌트 (단락/헤딩)
            if 'se-text' in classes:
                component_info.update(self._analyze_text_component_unified(component))
            
            # 2. 이미지 컴포넌트 (단일)
            elif 'se-image' in classes:
                component_info.update(self._analyze_image_component_unified(component))
            
            # 3. 갤러리 컴포넌트 (다중 이미지)
            elif 'se-imageGroup' in classes or 'se-image-group' in classes:
                component_info.update(self._analyze_gallery_component_unified(component))
            
            # 4. 비디오 컴포넌트
            elif 'se-video' in classes:
                component_info.update(self._analyze_video_component_unified(component))
            
            # 5. 인용문 컴포넌트
            elif 'se-quotation' in classes:
                component_info.update(self._analyze_quotation_component_unified(component))
            
            # 6. 표 컴포넌트
            elif 'se-table' in classes:
                component_info.update(self._analyze_table_component_unified(component))
            
            # 7. 구분선 컴포넌트
            elif 'se-horizontalLine' in classes or 'se-horizontal-line' in classes:
                component_info.update(self._analyze_horizontal_line_component_unified(component))
            
            # 8. 스티커 컴포넌트
            elif 'se-sticker' in classes:
                component_info.update(self._analyze_sticker_component_unified(component))
            
            # 9. 외부 임베드 컴포넌트 (OEmbed)
            elif 'se-oembed' in classes:
                component_info.update(self._analyze_oembed_component_unified(component))
            
            # 10. 외부 링크 프리뷰 컴포넌트 (OG Link)
            elif 'se-oglink' in classes:
                component_info.update(self._analyze_oglink_component_unified(component))
            
            # 11. 이미지 스트립/슬라이더 컴포넌트
            elif 'se-imageStrip' in classes:
                component_info.update(self._analyze_image_strip_component_unified(component))
            
            # 12. 기타/알 수 없는 컴포넌트
            else:
                component_info.update(self._analyze_unknown_component_unified(component))
            
            return component_info
            
        except Exception as e:
            logger.debug(f"통합 se-component 분석 실패: {e}")
            return None
    
    def _get_element_text(self, element):
        """BeautifulSoup/WebElement 텍스트 추출 통합"""
        if hasattr(element, 'get_text'):  # BeautifulSoup
            return element.get_text(strip=True)
        else:  # WebElement
            return element.text.strip()
    
    def _find_element(self, parent, selector):
        """BeautifulSoup/WebElement 요소 찾기 통합"""
        if hasattr(parent, 'select_one'):  # BeautifulSoup
            return parent.select_one(selector)
        else:  # WebElement
            try:
                return parent.find_element(By.CSS_SELECTOR, selector)
            except:
                return None
    
    def _find_elements(self, parent, selector):
        """BeautifulSoup/WebElement 여러 요소 찾기 통합"""
        if hasattr(parent, 'select'):  # BeautifulSoup
            return parent.select(selector)
        else:  # WebElement
            try:
                return parent.find_elements(By.CSS_SELECTOR, selector)
            except:
                return []
    
    def _get_attribute(self, element, attr):
        """BeautifulSoup/WebElement 속성 추출 통합"""
        if hasattr(element, 'get'):  # BeautifulSoup
            return element.get(attr, '')
        else:  # WebElement
            return element.get_attribute(attr) or ''
    
    def _analyze_text_component_unified(self, component) -> dict:
        """통합된 텍스트 컴포넌트 분석"""
        try:
            result = {
                'type': 'text',
                'subtype': 'paragraph',
                'content': '',
                'attributes': {}
            }
            
            # 텍스트 콘텐츠 추출
            content_elements = self._find_elements(component, '.se-fs, .se-text-paragraph, p, h1, h2, h3, h4, h5, h6')
            text_parts = []
            
            heading_detected = False
            
            for elem in content_elements:
                text = self._get_element_text(elem)
                if text:
                    text_parts.append(text)
                    
                    # 헤딩 타입 확인
                    tag_name = elem.tag_name if hasattr(elem, 'tag_name') else elem.name
                    if tag_name and tag_name.lower() in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        result['subtype'] = 'heading'
                        result['attributes']['heading_level'] = int(tag_name[1])
                        heading_detected = True
                    
                    # 클래스 기반 헤딩 확인
                    classes = self._get_attribute(elem, 'class').split() if self._get_attribute(elem, 'class') else []
                    if any('se-fs' in cls for cls in classes):
                        # 폰트 크기 기반으로 헤딩 추정
                        if any('se-fs-' in cls for cls in classes):
                            result['subtype'] = 'heading'
                            heading_detected = True
            
            result['content'] = ' '.join(text_parts)
            
            # 전체 텍스트에서도 헤딩 패턴 확인
            if not heading_detected:
                full_text = self._get_element_text(component)
                if full_text:
                    result['content'] = full_text
                    # 짧고 굵은 텍스트는 제목일 가능성
                    if len(full_text) < 50 and '\n' not in full_text:
                        result['subtype'] = 'heading'
            
            result['attributes']['char_count'] = len(result['content'])
            return result
            
        except Exception as e:
            logger.debug(f"통합 텍스트 컴포넌트 분석 실패: {e}")
            return {'type': 'text', 'content': '', 'attributes': {}}
    
    def _analyze_image_component_unified(self, component) -> dict:
        """통합된 이미지 컴포넌트 분석"""
        try:
            result = {
                'type': 'image',
                'subtype': 'single',
                'content': '',
                'attributes': {}
            }
            
            # 이미지 요소 찾기
            img = self._find_element(component, 'img')
            if img:
                src = self._get_attribute(img, 'src')
                alt = self._get_attribute(img, 'alt')
                
                result['content'] = alt or '이미지'
                result['attributes'] = {
                    'src': src,
                    'alt': alt,
                    'width': self._get_attribute(img, 'width'),
                    'height': self._get_attribute(img, 'height')
                }
            
            return result
            
        except Exception as e:
            logger.debug(f"통합 이미지 컴포넌트 분석 실패: {e}")
            return {'type': 'image', 'content': '이미지', 'attributes': {}}
    
    def _analyze_gallery_component_unified(self, component) -> dict:
        """통합된 갤러리 컴포넌트 분석"""
        try:
            result = {
                'type': 'gallery',
                'subtype': 'multiple',
                'content': '',
                'attributes': {}
            }
            
            images = self._find_elements(component, 'img')
            result['content'] = f'{len(images)}개 이미지 갤러리'
            result['attributes'] = {
                'image_count': len(images),
                'image_urls': [self._get_attribute(img, 'src') for img in images if self._get_attribute(img, 'src')]
            }
            
            return result
            
        except Exception as e:
            logger.debug(f"통합 갤러리 컴포넌트 분석 실패: {e}")
            return {'type': 'gallery', 'content': '이미지 갤러리', 'attributes': {}}
    
    def _analyze_video_component_unified(self, component) -> dict:
        """통합된 비디오 컴포넌트 분석"""
        try:
            result = {
                'type': 'video',
                'subtype': 'embedded',
                'content': '',
                'attributes': {}
            }
            
            # iframe 기반 비디오 확인
            iframe = self._find_element(component, 'iframe')
            if iframe:
                src = self._get_attribute(iframe, 'src')
                result['content'] = '동영상'
                result['attributes'] = {
                    'src': src,
                    'width': self._get_attribute(iframe, 'width'),
                    'height': self._get_attribute(iframe, 'height')
                }
                
                # 플랫폼 구분
                if 'youtube.com' in src or 'youtu.be' in src:
                    result['attributes']['platform'] = 'youtube'
                elif 'vimeo.com' in src:
                    result['attributes']['platform'] = 'vimeo'
                elif 'naver.com' in src:
                    result['attributes']['platform'] = 'naver'
            
            # video 태그 확인
            video = self._find_element(component, 'video')
            if video:
                src = self._get_attribute(video, 'src')
                result['content'] = '동영상'
                result['attributes'] = {
                    'src': src,
                    'width': self._get_attribute(video, 'width'),
                    'height': self._get_attribute(video, 'height'),
                    'platform': 'direct'
                }
            
            return result
            
        except Exception as e:
            logger.debug(f"통합 비디오 컴포넌트 분석 실패: {e}")
            return {'type': 'video', 'content': '동영상', 'attributes': {}}
    
    def _analyze_quotation_component_unified(self, component) -> dict:
        """통합된 인용문 컴포넌트 분석"""
        try:
            result = {
                'type': 'quotation',
                'subtype': 'quote',
                'content': '',
                'attributes': {}
            }
            
            content = self._get_element_text(component)
            result['content'] = content
            result['attributes']['char_count'] = len(content)
            
            return result
            
        except Exception as e:
            logger.debug(f"통합 인용문 컴포넌트 분석 실패: {e}")
            return {'type': 'quotation', 'content': '', 'attributes': {}}
    
    def _analyze_table_component_unified(self, component) -> dict:
        """통합된 표 컴포넌트 분석"""
        try:
            result = {
                'type': 'table',
                'subtype': 'data',
                'content': '',
                'attributes': {}
            }
            
            # 표 정보 수집
            rows = self._find_elements(component, 'tr')
            cols = self._find_elements(component, 'th, td')
            
            result['content'] = f'{len(rows)}행 표'
            result['attributes'] = {
                'row_count': len(rows),
                'col_count': len(cols) // len(rows) if rows else 0
            }
            
            return result
            
        except Exception as e:
            logger.debug(f"통합 표 컴포넌트 분석 실패: {e}")
            return {'type': 'table', 'content': '표', 'attributes': {}}
    
    def _analyze_horizontal_line_component_unified(self, component) -> dict:
        """통합된 구분선 컴포넌트 분석"""
        return {
            'type': 'horizontal_line',
            'subtype': 'divider',
            'content': '구분선',
            'attributes': {}
        }
    
    def _analyze_sticker_component_unified(self, component) -> dict:
        """통합된 스티커 컴포넌트 분석"""
        try:
            result = {
                'type': 'sticker',
                'subtype': 'emoji',
                'content': '',
                'attributes': {}
            }
            
            img = self._find_element(component, 'img')
            if img:
                alt = self._get_attribute(img, 'alt')
                src = self._get_attribute(img, 'src')
                result['content'] = alt or '스티커'
                result['attributes'] = {'src': src, 'alt': alt}
            else:
                result['content'] = '스티커'
            
            return result
            
        except Exception as e:
            logger.debug(f"통합 스티커 컴포넌트 분석 실패: {e}")
            return {'type': 'sticker', 'content': '스티커', 'attributes': {}}
    
    def _analyze_oembed_component_unified(self, component) -> dict:
        """통합된 외부 임베드 컴포넌트 분석"""
        try:
            result = {
                'type': 'oembed',
                'subtype': 'external',
                'content': '',
                'attributes': {}
            }
            
            # iframe 찾기
            iframe = self._find_element(component, 'iframe')
            if iframe:
                src = self._get_attribute(iframe, 'src')
                result['content'] = '외부 콘텐츠 임베드'
                result['attributes'] = {'src': src}
                
                # 플랫폼 구분
                if 'instagram.com' in src:
                    result['attributes']['platform'] = 'instagram'
                elif 'twitter.com' in src or 'x.com' in src:
                    result['attributes']['platform'] = 'twitter'
                elif 'facebook.com' in src:
                    result['attributes']['platform'] = 'facebook'
            
            return result
            
        except Exception as e:
            logger.debug(f"통합 외부 임베드 컴포넌트 분석 실패: {e}")
            return {'type': 'oembed', 'content': '외부 콘텐츠', 'attributes': {}}
    
    def _analyze_oglink_component_unified(self, component) -> dict:
        """통합된 외부 링크 프리뷰 컴포넌트 분석 (OG Link)"""
        try:
            result = {
                'type': 'oglink',
                'subtype': 'link_preview',
                'content': '',
                'attributes': {}
            }
            
            # 링크 정보 추출
            link_element = self._find_element(component, 'a')
            if link_element:
                href = self._get_attribute(link_element, 'href')
                result['attributes']['href'] = href
                
                # 도메인 추출
                if href:
                    import re
                    domain_match = re.search(r'https?://([^/]+)', href)
                    if domain_match:
                        result['attributes']['domain'] = domain_match.group(1)
            
            # 제목과 설명 추출
            title_element = self._find_element(component, '.se-oglink-title, .se-text-title')
            if title_element:
                title = self._get_element_text(title_element)
                result['content'] = title
                result['attributes']['title'] = title
            
            desc_element = self._find_element(component, '.se-oglink-summary, .se-text-summary')
            if desc_element:
                description = self._get_element_text(desc_element)
                result['attributes']['description'] = description
            
            # 이미지 정보
            img_element = self._find_element(component, 'img')
            if img_element:
                src = self._get_attribute(img_element, 'src')
                result['attributes']['thumbnail'] = src
            
            if not result['content']:
                result['content'] = '외부 링크 프리뷰'
            
            return result
            
        except Exception as e:
            logger.debug(f"통합 외부 링크 프리뷰 컴포넌트 분석 실패: {e}")
            return {'type': 'oglink', 'content': '외부 링크', 'attributes': {}}
    
    def _analyze_image_strip_component_unified(self, component) -> dict:
        """통합된 이미지 스트립/슬라이더 컴포넌트 분석"""
        try:
            result = {
                'type': 'image_strip',
                'subtype': 'slider',
                'content': '',
                'attributes': {}
            }
            
            # 이미지들 추출
            images = self._find_elements(component, 'img')
            image_urls = []
            
            for img in images:
                src = self._get_attribute(img, 'src')
                if src:
                    image_urls.append(src)
            
            result['content'] = f'이미지 슬라이더 ({len(images)}개)'
            result['attributes'] = {
                'image_count': len(images),
                'image_urls': image_urls,
                'strip_type': 'horizontal'
            }
            
            # 슬라이더 유형 감지
            if 'se-imageStrip2' in self._get_attribute(component, 'class'):
                result['attributes']['strip_version'] = '2'
            
            return result
            
        except Exception as e:
            logger.debug(f"통합 이미지 스트립 컴포넌트 분석 실패: {e}")
            return {'type': 'image_strip', 'content': '이미지 슬라이더', 'attributes': {}}
    
    def _analyze_unknown_component_unified(self, component) -> dict:
        """통합된 알 수 없는 컴포넌트 분석"""
        try:
            result = {
                'type': 'unknown',
                'subtype': 'other',
                'content': '',
                'attributes': {}
            }
            
            content = self._get_element_text(component)
            if content:
                result['content'] = content[:100]  # 최대 100자
                result['attributes']['char_count'] = len(content)
            else:
                result['content'] = '기타 콘텐츠'
            
            # 디버그용 클래스 정보 추가
            classes = self._get_attribute(component, 'class')
            if classes:
                se_classes = [cls for cls in classes.split() if cls.startswith('se-')]
                if se_classes:
                    result['attributes']['se_classes'] = se_classes
                    logger.debug(f"Unknown 컴포넌트 클래스: {se_classes}")
            
            return result
            
        except Exception as e:
            logger.debug(f"통합 알 수 없는 컴포넌트 분석 실패: {e}")
            return {'type': 'unknown', 'content': '기타', 'attributes': {}}
    
    # =================================
    # 기존 HTTP 방식 (통합 함수 사용)
    # =================================
    
    def _extract_content_structure_http(self, soup: BeautifulSoup) -> list:
        """HTTP 방식: 통합된 구조 분석 함수 사용"""
        return self._extract_content_structure_unified(soup)
    
    def _extract_content_structure_selenium(self) -> list:
        """Selenium 방식: WebElement를 BeautifulSoup으로 변환 후 통합 분석 함수 사용"""
        try:
            # Selenium에서 HTML 가져와서 BeautifulSoup으로 변환
            html = self.helper.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # 통합 분석 함수 사용
            return self._extract_content_structure_unified(soup)
            
        except Exception as e:
            logger.debug(f"Selenium 콘텐츠 구조 분석 실패: {e}")
            return []
    
    
    def _get_empty_analysis_result(self, blog_url: str) -> dict:
        """분석 실패 시 기본 결과 반환"""
        return {
            'url': blog_url,
            'title': '분석 실패',
            'content_length': 0,
            'image_count': 0,
            'gif_count': 0,
            'video_count': 0,
            'tags': [],
            'text_content': '분석 실패',
            'content_structure': []
        }
    
    def _smooth_scroll_to_bottom(self):
        """빠른 스크롤 - 최소 대기시간으로 최적화"""
        try:
            logger.info("⬇️ 빠른 스크롤 시작")
            
            # 한번에 스크롤 후 짧게 대기
            self.helper.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.3)  # 대기시간 단축: 0.8s → 0.3s
            
            # 높이가 변할 수 있는 경우만 한 번 더 시도
            last_height = self.helper.driver.execute_script("return document.body.scrollHeight")
            self.helper.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.2)  # 추가 대기시간 최소화
            
            final_height = self.helper.driver.execute_script("return document.body.scrollHeight")
            logger.info(f"✅ 빠른 스크롤 완료 - 높이: {final_height}px")
            
        except Exception as e:
            logger.error(f"❌ 스크롤 실패: {e}")
    
    def _handle_iframe_if_exists(self):
        """iframe 빠른 감지 및 전환"""
        try:
            # 가장 일반적인 네이버 블로그 iframe만 먼저 시도 (속도 우선)
            common_selectors = [
                'iframe#mainFrame',
                'iframe[name="mainFrame"]', 
                'iframe'  # 대부분 첫 번째 iframe이 메인 콘텐츠
            ]
            
            for selector in common_selectors:
                try:
                    iframes = self.helper.find_elements(selector)
                    if iframes:
                        logger.debug(f"iframe 발견: {selector}")
                        self.helper.driver.switch_to.frame(iframes[0])
                        
                        # 간단한 로딩 확인 (시간 단축)
                        time.sleep(0.2)  # 최소 대기
                        
                        self._is_in_iframe = True
                        return True
                except Exception:
                    continue
            
            logger.debug("iframe 없음")
            self._is_in_iframe = False
            return False
            
        except Exception as e:
            logger.error(f"iframe 처리 오류: {e}")
            self._is_in_iframe = False
            return False
    
    def _exit_iframe_if_exists(self):
        """iframe에서 빠져나오기"""
        try:
            if hasattr(self, '_is_in_iframe') and self._is_in_iframe:
                logger.debug("iframe에서 메인 페이지로 복귀")
                self.helper.driver.switch_to.default_content()
                self._is_in_iframe = False
        except Exception as e:
            logger.error(f"iframe 복귀 오류: {e}")
    

    def analyze_selected_urls_with_filtering(self, selected_urls: list, max_results: int = 3) -> list:
        """선별된 URL들을 순차 분석하면서 모든 필터링 적용"""
        try:
            logger.info(f"📝 선별된 {len(selected_urls)}개 URL 순차 분석 시작 (필터링 포함)")
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
                        analysis_result = self.analyze_blog_content_http(url)
                        if analysis_result and analysis_result.get('title') != '분석 실패' and analysis_result.get('content_length', 0) > 0:
                            logger.info(f"✅ HTTP 방식 분석 성공")
                        else:
                            analysis_result = None
                    except Exception:
                        analysis_result = None

                    # HTTP 실패 시 Selenium으로 백업
                    if not analysis_result:
                        try:
                            analysis_result = self.analyze_blog_content(url)
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

                    # 모든 필터링 적용
                    text_content = integrated_result.get('text_content', '')
                    title = integrated_result.get('title', '')

                    # 1. 광고/협찬 글 필터링
                    if is_advertisement_content(text_content, title):
                        logger.warning(f"🚫 {i+1}번째 URL 제외: 광고/협찬/체험단 글로 판단됨")
                        continue

                    # 2. 본문 길이 필터링 (1000자 미만 제외)
                    content_length = integrated_result.get('content_length', 0)
                    if content_length < 1000:
                        logger.warning(f"🚫 {i+1}번째 URL 제외: 본문이 너무 짧음 ({content_length}자 < 1000자)")
                        continue

                    # 3. 콘텐츠 품질 필터링 (숫자만 나열, 특수문자 과다)
                    if is_low_quality_content(text_content):
                        logger.warning(f"🚫 {i+1}번째 URL 제외: 저품질 콘텐츠로 판단됨")
                        continue

                    # 모든 필터를 통과한 양질의 글만 추가
                    analyzed_blogs.append(integrated_result)
                    logger.info(f"✅ {i+1}번째 URL 분석 완료 (고품질 정보성 글)")

                except Exception as e:
                    logger.error(f"❌ {i+1}번째 URL 분석 실패: {e}")
                    continue

            logger.info(f"🎯 선별된 URL 분석 완료: {len(analyzed_blogs)}개 (모든 필터링 적용)")
            return analyzed_blogs

        except Exception as e:
            logger.error(f"선별된 URL 분석 오류: {e}")
            raise BusinessError(f"선별된 URL 분석 실패: {str(e)}")

    def _handle_device_registration(self) -> bool:
        """새로운 기기 등록 페이지에서 '등록' 버튼 클릭"""
        try:
            logger.info("새로운 기기 등록 페이지 처리 시작")

            wait = WebDriverWait(self.helper.driver, 10)

            # 페이지 완전 로딩 대기
            logger.info("새로운 기기 등록 페이지 로딩 대기 중...")
            time.sleep(5)  # 더 긴 안정화 대기

            # '등록' 버튼 찾기 (실제 HTML 구조에 맞춘 셀렉터들)
            register_button_selectors = [
                (By.ID, "new.save"),  # 가장 정확한 ID 셀렉터
                (By.CSS_SELECTOR, '.btn_upload a.btn'),  # 클래스 조합
                (By.CSS_SELECTOR, '.btn_upload a[href="#"]'),  # href + 클래스
                (By.XPATH, "//a[@id='new.save']"),  # XPath ID
                (By.XPATH, "//span[@class='btn_upload']/a[@class='btn']"),  # 정확한 경로
                (By.XPATH, "//a[contains(text(), '등록') and @class='btn']"),  # 텍스트 + 클래스
                (By.XPATH, "//form[@id='frmNIDLogin']//a[@id='new.save']"),  # form 내부에서 찾기
            ]

            register_button = None
            used_selector = None

            # 현재 페이지 HTML 확인 (디버깅용)
            current_url = self.helper.current_url
            logger.info(f"현재 페이지 URL: {current_url}")

            try:
                page_title = self.helper.driver.title
                logger.info(f"페이지 제목: {page_title}")
            except:
                pass

            for by, selector in register_button_selectors:
                try:
                    logger.info(f"등록 버튼 찾기 시도: {selector}")  # debug → info로 변경
                    register_button = wait.until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    if register_button:
                        used_selector = selector
                        logger.info(f"✅ 등록 버튼 발견: {selector}")
                        break
                except TimeoutException:
                    logger.warning(f"❌ 셀렉터 {selector} 타임아웃")  # debug → warning으로 변경
                    continue
                except Exception as e:
                    logger.warning(f"❌ 셀렉터 {selector} 실패: {e}")  # debug → warning으로 변경
                    continue

            if not register_button:
                logger.warning("등록 버튼을 직접 찾을 수 없음, form submit 방식 시도")
                return self._submit_device_registration_form()

            # regyn 값을 '1'로 설정 (등록 의사 표시)
            try:
                regyn_input = self.helper.driver.find_element(By.ID, "regyn")
                self.helper.driver.execute_script("arguments[0].value = '1';", regyn_input)
                logger.info("regyn 값을 '1'로 설정 완료")
            except Exception as e:
                logger.debug(f"regyn 설정 실패 (무시 가능): {e}")

            # 등록 버튼 클릭
            logger.info(f"등록 버튼 클릭 시도 (셀렉터: {used_selector})")
            try:
                register_button.click()
                logger.info("✅ 새로운 기기 등록 버튼 클릭 완료")

                # 클릭 후 페이지 이동 대기 (BlogHome으로 이동하는지 확인)
                time.sleep(2)
                current_url = self.helper.current_url
                logger.info(f"등록 후 현재 URL: {current_url}")

                return True

            except Exception as e:
                logger.warning(f"일반 클릭 실패, JavaScript 클릭 시도: {e}")
                try:
                    self.helper.driver.execute_script("arguments[0].click();", register_button)
                    logger.info("✅ JavaScript로 새로운 기기 등록 버튼 클릭 완료")
                    time.sleep(2)
                    return True
                except Exception as e2:
                    logger.error(f"JavaScript 클릭도 실패: {e2}")
                    return False

        except Exception as e:
            logger.error(f"새로운 기기 등록 처리 실패: {e}")
            return False


    def _submit_device_registration_form(self) -> bool:
        """form submit 방식으로 새로운 기기 등록"""
        try:
            logger.info("form submit 방식으로 새로운 기기 등록 시도")

            # regyn 값을 '1'로 설정 (등록 의사)
            regyn_input = self.helper.driver.find_element(By.ID, "regyn")
            self.helper.driver.execute_script("arguments[0].value = '1';", regyn_input)
            logger.info("regyn 값을 '1'로 설정")

            # form 찾기 및 submit
            form = self.helper.driver.find_element(By.ID, "frmNIDLogin")
            logger.info("frmNIDLogin form 발견, submit 실행")

            form.submit()
            logger.info("✅ form submit으로 새로운 기기 등록 완료")

            time.sleep(3)  # 페이지 이동 대기
            return True

        except Exception as e:
            logger.error(f"form submit 방식 실패: {e}")
            return False

    def navigate_to_write_page(self, user_id: str = None) -> bool:
        """네이버 블로그 글쓰기 페이지로 이동"""
        try:
            if not self.is_logged_in:
                logger.error("로그인이 필요합니다")
                return False

            # 사용자 ID가 없으면 현재 로그인된 사용자 ID 사용
            if not user_id:
                user_id = self.username
                if not user_id:
                    logger.error("사용자 ID를 찾을 수 없습니다")
                    return False

            write_url = f"https://blog.naver.com/{user_id}?Redirect=Write&"
            logger.info(f"글쓰기 페이지로 이동: {write_url}")

            self.helper.goto(write_url)
            time.sleep(2)  # 페이지 로딩 대기

            # 페이지 이동 확인
            current_url = self.helper.current_url
            if "Redirect=Write" in current_url or "PostWriteForm" in current_url:
                logger.info("✅ 글쓰기 페이지 이동 성공")
                return True
            else:
                logger.warning(f"⚠️ 글쓰기 페이지 이동 확인 필요: {current_url}")
                return True  # 일단 성공으로 처리

        except Exception as e:
            logger.error(f"글쓰기 페이지 이동 실패: {e}")
            return False

    def handle_draft_popup(self) -> bool:
        """작성 중인 글 팝업 처리 (취소 버튼 클릭)"""
        try:
            logger.info("작성 중인 글 팝업 확인 중...")

            # 팝업이 나타날 때까지 잠시 대기
            time.sleep(1)

            # 다양한 셀렉터로 취소 버튼 찾기
            cancel_selectors = [
                "button:contains('취소')",  # 텍스트 기반
                ".btn_cancel",  # 클래스 기반
                "[onclick*='cancel']",  # onclick 속성 기반
                ".popup_footer button:first-child",  # 팝업 푸터의 첫 번째 버튼
                ".btn_area button:first-child",  # 버튼 영역의 첫 번째 버튼
            ]

            for selector in cancel_selectors:
                try:
                    if selector.startswith("button:contains"):
                        # jQuery 스타일 텍스트 선택자를 JavaScript로 변환
                        elements = self.helper.driver.execute_script("""
                            var buttons = document.querySelectorAll('button');
                            for (var i = 0; i < buttons.length; i++) {
                                if (buttons[i].textContent.includes('취소')) {
                                    return buttons[i];
                                }
                            }
                            return null;
                        """)
                        if elements:
                            elements.click()
                            logger.info("✅ '취소' 버튼 클릭 성공 (텍스트 기반)")
                            time.sleep(1)
                            return True
                    else:
                        element = self.helper.find_element(selector)
                        if element and element.is_displayed():
                            element.click()
                            logger.info(f"✅ 취소 버튼 클릭 성공: {selector}")
                            time.sleep(1)
                            return True
                except:
                    continue

            logger.info("작성 중인 글 팝업이 없거나 취소 버튼을 찾을 수 없음")
            return True  # 팝업이 없는 것도 정상 상황

        except Exception as e:
            logger.error(f"팝업 처리 실패: {e}")
            return True  # 팝업 처리 실패해도 계속 진행

    def switch_to_editor_iframe(self) -> bool:
        """네이버 블로그 에디터 iframe으로 전환"""
        try:
            logger.info("에디터 iframe 감지 및 전환 시작...")

            # iframe이 로드될 때까지 대기
            time.sleep(2)

            # iframe 감지를 위한 셀렉터들
            iframe_selectors = [
                "iframe[src*='blog.naver.com']",  # 네이버 블로그 에디터 iframe
                "iframe[name*='editor']",  # 에디터 이름 포함
                "iframe[id*='editor']",  # 에디터 ID 포함
                "iframe[src*='PostWriteForm']",  # 글쓰기 폼 포함
                "iframe",  # 모든 iframe (마지막 대안)
            ]

            for selector in iframe_selectors:
                try:
                    iframes = self.helper.find_elements(selector)
                    if iframes:
                        logger.info(f"iframe 발견: {selector} (개수: {len(iframes)})")

                        for i, iframe in enumerate(iframes):
                            try:
                                # iframe 속성 로깅
                                src = iframe.get_attribute('src') or ''
                                name = iframe.get_attribute('name') or ''
                                id_attr = iframe.get_attribute('id') or ''

                                logger.info(f"iframe[{i}] - src: {src[:100]}..., name: {name}, id: {id_attr}")

                                # 블로그 에디터와 관련된 iframe인지 확인
                                if any(keyword in (src + name + id_attr).lower() for keyword in
                                      ['blog.naver.com', 'editor', 'postwriteform', 'write']):

                                    # iframe으로 전환 시도
                                    self.helper.driver.switch_to.frame(iframe)
                                    logger.info(f"✅ iframe으로 전환 성공: {selector}[{i}]")

                                    # iframe 내부 확인 (body 태그 존재 여부)
                                    try:
                                        body = self.helper.driver.find_element(By.TAG_NAME, "body")
                                        if body:
                                            logger.info("iframe 내부 body 요소 확인됨")
                                            return True
                                    except:
                                        logger.warning("iframe 내부 body 요소를 찾을 수 없음")

                                    # 다시 기본 프레임으로 돌아가서 다른 iframe 시도
                                    self.helper.driver.switch_to.default_content()

                            except Exception as e:
                                logger.warning(f"iframe[{i}] 전환 실패: {e}")
                                # 실패했을 경우 기본 프레임으로 돌아가기
                                self.helper.driver.switch_to.default_content()
                                continue

                except Exception as e:
                    logger.warning(f"iframe 셀렉터 {selector} 실패: {e}")
                    continue

            logger.warning("적절한 에디터 iframe을 찾을 수 없음")
            return False

        except Exception as e:
            logger.error(f"iframe 전환 실패: {e}")
            # 안전을 위해 기본 프레임으로 돌아가기
            try:
                self.helper.driver.switch_to.default_content()
            except:
                pass
            return False

    def click_publish_button(self) -> bool:
        """발행 버튼 클릭"""
        try:
            logger.info("발행 버튼 클릭 시도...")

            # 발행 버튼을 위한 다양한 셀렉터
            publish_selectors = [
                "button:contains('발행')",  # 텍스트 기반
                ".btn_publish",  # 클래스 기반
                "#publish",  # ID 기반
                "[value='발행']",  # value 속성 기반
                "input[type='submit'][value*='발행']",  # submit 버튼
                ".publish_btn",  # 발행 버튼 클래스
                "button[onclick*='publish']",  # onclick 속성 기반
                ".btn_area button:last-child",  # 버튼 영역의 마지막 버튼 (보통 발행)
            ]

            for selector in publish_selectors:
                try:
                    if selector.startswith("button:contains"):
                        # jQuery 스타일 텍스트 선택자를 JavaScript로 변환
                        element = self.helper.driver.execute_script("""
                            var buttons = document.querySelectorAll('button, input[type="button"], input[type="submit"]');
                            for (var i = 0; i < buttons.length; i++) {
                                var text = buttons[i].textContent || buttons[i].value || '';
                                if (text.includes('발행') || text.includes('게시') || text.includes('등록')) {
                                    return buttons[i];
                                }
                            }
                            return null;
                        """)
                        if element:
                            # 스크롤해서 버튼을 화면에 표시
                            self.helper.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                            time.sleep(0.5)

                            # 클릭 시도
                            self.helper.driver.execute_script("arguments[0].click();", element)
                            logger.info("✅ 발행 버튼 클릭 성공 (텍스트 기반)")
                            time.sleep(2)
                            return True
                    else:
                        element = self.helper.find_element(selector)
                        if element and element.is_displayed():
                            # 스크롤해서 버튼을 화면에 표시
                            self.helper.scroll_to_element(selector)
                            time.sleep(0.5)

                            # 클릭 시도
                            if self.helper.click_element(selector):
                                logger.info(f"✅ 발행 버튼 클릭 성공: {selector}")
                                time.sleep(2)
                                return True
                except Exception as e:
                    logger.debug(f"셀렉터 {selector} 실패: {e}")
                    continue

            logger.warning("발행 버튼을 찾을 수 없음")
            return False

        except Exception as e:
            logger.error(f"발행 버튼 클릭 실패: {e}")
            return False

    def publish_post(self, user_id: str = None) -> bool:
        """네이버 블로그 글 발행 전체 프로세스"""
        try:
            logger.info("==== 네이버 블로그 글 발행 시작 ====")

            # 1. 글쓰기 페이지로 이동
            if not self.navigate_to_write_page(user_id):
                logger.error("글쓰기 페이지 이동 실패")
                return False

            # 2. 작성 중인 글 팝업 처리
            if not self.handle_draft_popup():
                logger.warning("팝업 처리 실패, 계속 진행...")

            # 3. iframe으로 전환
            if not self.switch_to_editor_iframe():
                logger.warning("iframe 전환 실패, 기본 프레임에서 진행...")

            # 4. 발행 버튼 클릭
            if not self.click_publish_button():
                logger.error("발행 버튼 클릭 실패")
                return False

            logger.info("✅ 네이버 블로그 글 발행 완료!")
            return True

        except Exception as e:
            logger.error(f"글 발행 프로세스 실패: {e}")
            return False
        finally:
            # 안전을 위해 기본 프레임으로 돌아가기
            try:
                self.helper.driver.switch_to.default_content()
            except:
                pass

    def get_blog_titles_for_ai_selection(self, keyword: str, max_results: int = 30) -> List[Dict]:
        """AI 선별을 위한 블로그 제목 30개 수집 (제목과 URL만)"""
        try:
            logger.info(f"🔍 AI 선별용 블로그 제목 수집 시작: '{keyword}' (최대 {max_results}개)")

            # 분석 전용 브라우저 시작 (초기화되지 않은 경우)
            if not hasattr(self.helper, 'driver') or not self.helper.driver:
                logger.info("🔧 분석 전용 브라우저 시작")
                self.start_browser_for_analysis()

            # Selenium으로 블로그 검색 (제목과 URL만 수집)
            blog_titles = self._search_blogs_for_titles_only(keyword, max_results)

            if not blog_titles:
                logger.warning("❌ 블로그 제목 검색 결과 없음")
                return []

            logger.info(f"✅ 블로그 제목 수집 완료: {len(blog_titles)}개")
            return blog_titles

        except Exception as e:
            logger.error(f"AI 선별용 블로그 제목 수집 실패: {e}")
            return []

    def _search_blogs_for_titles_only(self, keyword: str, max_results: int = 30) -> List[Dict]:
        """제목과 URL만 빠르게 수집하는 경량화된 블로그 검색"""
        try:
            # URL 인코딩 (기존 검색과 동일)
            import urllib.parse
            encoded_keyword = urllib.parse.quote(keyword)
            search_url = f"https://search.naver.com/search.naver?ssc=tab.blog.all&sm=tab_jum&query={encoded_keyword}"
            logger.info(f"블로그 검색 페이지로 이동: {search_url}")
            self.helper.driver.get(search_url)

            time.sleep(2)  # 페이지 로딩 대기

            blogs = []
            collected_urls = set()  # 중복 URL 방지

            # 여러 페이지에서 제목 수집 (최대 3페이지)
            for page in range(1, 4):  # 1, 2, 3 페이지
                try:
                    if page > 1:
                        # 다음 페이지로 이동 (네이버 검색은 start 파라미터 사용)
                        start_num = (page - 1) * 10 + 1
                        next_page_url = f"https://search.naver.com/search.naver?ssc=tab.blog.all&sm=tab_jum&query={encoded_keyword}&start={start_num}"
                        logger.info(f"📄 {page}페이지로 이동")
                        self.helper.driver.get(next_page_url)
                        time.sleep(2)

                    # 블로그 포스트 요소들 찾기 (기존 검색과 동일한 셀렉터 사용)
                    post_elements = self.helper.driver.find_elements(By.CSS_SELECTOR, "div.title_area")

                    if not post_elements:
                        logger.warning(f"📄 {page}페이지에서 블로그 요소를 찾을 수 없음")
                        break

                    page_blogs = 0
                    for element in post_elements:
                        try:
                            if len(blogs) >= max_results:
                                break

                            # 제목과 링크 추출 (기존 검색과 동일한 방식)
                            try:
                                title_link = element.find_element(By.CSS_SELECTOR, 'a.title_link')
                            except:
                                continue

                            if not title_link:
                                continue

                            # 제목과 URL 추출
                            title = title_link.text.strip()
                            url = title_link.get_attribute("href")

                            # 유효성 검사
                            if not title or not url or url in collected_urls:
                                continue

                            # 광고 링크 제외 (기존 검색과 동일)
                            if 'ader.naver.com' in url:
                                logger.debug(f"광고 링크 스킵: {url[:50]}...")
                                continue

                            # 네이버 블로그 URL인지 확인
                            if "blog.naver.com" not in url:
                                continue

                            collected_urls.add(url)
                            blogs.append({
                                'rank': len(blogs) + 1,
                                'title': title,
                                'url': url
                            })

                            page_blogs += 1

                        except Exception as e:
                            logger.debug(f"개별 블로그 요소 처리 실패: {e}")
                            continue

                    logger.info(f"📄 {page}페이지에서 {page_blogs}개 제목 수집 (총 {len(blogs)}개)")

                    if len(blogs) >= max_results:
                        break

                except Exception as e:
                    logger.warning(f"📄 {page}페이지 처리 실패: {e}")
                    break

            logger.info(f"🎯 최종 블로그 제목 수집 완료: {len(blogs)}개")
            return blogs

        except Exception as e:
            logger.error(f"블로그 제목 검색 실패: {e}")
            return []


class TistoryAdapter:
    """티스토리 어댑터 (미구현)"""

    def __init__(self):
        self.is_logged_in = False
    
    def login_with_credentials(self, credentials: BlogCredentials) -> LoginStatus:
        """티스토리 로그인 (미구현)"""
        raise BusinessError("티스토리 로그인은 아직 구현되지 않았습니다")


class BloggerAdapter:
    """구글 블로거 어댑터 (미구현)"""
    
    def __init__(self):
        self.is_logged_in = False
    
    def login_with_credentials(self, credentials: BlogCredentials) -> LoginStatus:
        """구글 블로거 로그인 (미구현)"""
        raise BusinessError("구글 블로거 로그인은 아직 구현되지 않았습니다")


def create_blog_adapter(platform: BlogPlatform):
    """플랫폼에 맞는 어댑터 생성"""
    if platform == BlogPlatform.NAVER:
        return NaverBlogAdapter()
    elif platform == BlogPlatform.TISTORY:
        return TistoryAdapter()
    elif platform == BlogPlatform.BLOGGER:
        return BloggerAdapter()
    else:
        raise BusinessError(f"지원하지 않는 플랫폼: {platform}")