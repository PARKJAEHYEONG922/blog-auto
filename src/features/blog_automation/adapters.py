"""
블로그 자동화 모듈의 웹 자동화 어댑터
"""
import time
import random
from typing import Optional, Dict, Any
from functools import wraps
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from src.vendors.web_automation.selenium_helper import SeleniumHelper, get_default_selenium_config
from src.foundation.logging import get_logger
from src.foundation.exceptions import BusinessError
from .models import BlogCredentials, BlogPlatform, LoginStatus

logger = get_logger("blog_automation.adapters")


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


class NaverBlogAdapter:
    """네이버 블로그 자동화 어댑터"""
    
    def __init__(self):
        # Selenium Helper 사용 (헤드리스 모드 비활성화)
        config = get_default_selenium_config(headless=False)
        self.helper = SeleniumHelper(config)
        
        self.is_logged_in = False
        self.two_factor_auth_detected = False
        
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
            return self._wait_for_login_result()
            
        except Exception as e:
            logger.error(f"로그인 수행 실패: {e}")
            return LoginStatus.LOGIN_FAILED
    
    def _wait_for_login_result(self, timeout: int = 90) -> LoginStatus:
        """로그인 결과 대기 (2차 인증 포함) - WebDriverWait 사용"""
        wait = WebDriverWait(self.helper.driver, timeout)
        
        try:
            # 블로그 홈 페이지로 이동하거나 2차 인증 페이지가 나타날 때까지 대기
            def check_login_result(driver):
                current_url = driver.current_url
                logger.debug(f"현재 URL 확인: {current_url}")
                
                # 성공: 블로그 홈으로 리다이렉트됨
                if "BlogHome.naver" in current_url or "section.blog.naver.com" in current_url:
                    logger.info("네이버 블로그 로그인 성공!")
                    self.is_logged_in = True
                    return "success"
                
                # 2차 인증 감지
                if self._detect_two_factor_auth():
                    if not self.two_factor_auth_detected:
                        logger.info("2차 인증이 감지되었습니다. 사용자 입력 대기 중...")
                        self.two_factor_auth_detected = True
                    return "two_factor"
                
                # 로그인 실패 감지
                if self._detect_login_failure():
                    logger.error("로그인 실패 감지")
                    return "failed"
                
                return False  # 계속 대기
            
            # 2차 인증 또는 성공을 기다림
            result = None
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                result = check_login_result(self.helper.driver)
                
                if result == "success":
                    return LoginStatus.LOGGED_IN
                elif result == "failed":
                    return LoginStatus.LOGIN_FAILED
                elif result == "two_factor":
                    # 2차 인증이 감지되면 계속 모니터링
                    time.sleep(2)
                    continue
                else:
                    time.sleep(1)  # 1초마다 체크
            
            # 타임아웃 발생
            logger.warning("로그인 결과 대기 타임아웃")
            return LoginStatus.LOGIN_FAILED
            
        except Exception as e:
            logger.error(f"로그인 결과 대기 중 오류: {e}")
            return LoginStatus.LOGIN_FAILED
    
    def _detect_two_factor_auth(self) -> bool:
        """2차 인증 감지"""
        try:
            # 2차 인증 관련 요소들 확인
            two_factor_indicators = [
                ".otp_area",
                ".auth_number", 
                "input[name*='otp']",
                "input[name*='auth']",
                ".two_factor",
                "[data-testid*='otp']"
            ]
            
            for selector in two_factor_indicators:
                element = self.helper.find_element(selector)
                if element and element.is_displayed():
                    return True
            
            # URL로도 확인
            current_url = self.helper.current_url
            if any(keyword in current_url for keyword in ["auth", "otp", "verify"]):
                return True
            
            return False
            
        except Exception:
            return False
    
    def _detect_login_failure(self) -> bool:
        """로그인 실패 감지"""
        try:
            # 오류 메시지 확인
            error_selectors = [
                ".error_message",
                ".alert_area",
                "[role='alert']",
                ".input_error"
            ]
            
            for selector in error_selectors:
                element = self.helper.find_element(selector)
                if element and element.is_displayed():
                    error_text = element.text.strip()
                    if error_text and any(keyword in error_text for keyword in 
                                        ["잘못", "오류", "실패", "확인", "존재하지 않는"]):
                        logger.error(f"로그인 오류 메시지: {error_text}")
                        return True
            
            return False
            
        except Exception:
            return False
    
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
        """블로그 홈에서 글쓰기 버튼 클릭"""
        try:
            logger.info("글쓰기 버튼 클릭 시도")
            
            if not self.is_logged_in:
                raise BusinessError("로그인이 필요합니다")
            
            # 현재 URL이 블로그 홈인지 확인
            current_url = self.helper.current_url
            if "BlogHome.naver" not in current_url:
                logger.info("블로그 홈으로 이동 중...")
                self.helper.goto(self.blog_home_url)
                time.sleep(2)
            
            wait = WebDriverWait(self.helper.driver, 10)
            
            # 글쓰기 버튼 선택자들
            write_button_selectors = [
                (By.CSS_SELECTOR, 'a[href="https://blog.naver.com/GoBlogWrite.naver"]'),  # 정확한 href
                (By.CSS_SELECTOR, 'a[ng-href="https://blog.naver.com/GoBlogWrite.naver"]'),  # ng-href
                (By.CSS_SELECTOR, 'a.item[alt="글쓰기"]'),  # alt 속성
                (By.CSS_SELECTOR, 'a[bg-nclick="hmp*s.write"]'),  # bg-nclick 속성
                (By.CSS_SELECTOR, 'a.item i.icon_write'),  # 아이콘으로 찾기
                (By.CSS_SELECTOR, 'a[href*="GoBlogWrite.naver"]'),  # href 포함
            ]
            
            write_button = None
            used_selector = None
            
            for by, selector in write_button_selectors:
                try:
                    logger.debug(f"글쓰기 버튼 찾기 시도: {selector}")
                    
                    write_button = wait.until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    
                    if write_button:
                        used_selector = selector
                        logger.info(f"글쓰기 버튼 발견: {selector}")
                        break
                        
                except TimeoutException:
                    logger.debug(f"셀렉터 {selector} 타임아웃")
                    continue
                except Exception as e:
                    logger.debug(f"셀렉터 {selector} 실패: {e}")
                    continue
            
            # CSS 셀렉터로 못 찾으면 XPath도 시도
            if not write_button:
                xpath_selectors = [
                    "//a[@href='https://blog.naver.com/GoBlogWrite.naver']",
                    "//a[@ng-href='https://blog.naver.com/GoBlogWrite.naver']",
                    "//a[@alt='글쓰기']",
                    "//a[contains(@href, 'GoBlogWrite.naver')]",
                    "//a[contains(text(), '글쓰기')]",
                    "//a[@bg-nclick='hmp*s.write']",
                    "//i[@class='sp_common icon_write']//parent::a"
                ]
                
                for xpath in xpath_selectors:
                    try:
                        logger.debug(f"XPath로 글쓰기 버튼 찾기 시도: {xpath}")
                        write_button = wait.until(
                            EC.element_to_be_clickable((By.XPATH, xpath))
                        )
                        
                        if write_button:
                            used_selector = xpath
                            logger.info(f"XPath로 글쓰기 버튼 발견: {xpath}")
                            break
                            
                    except TimeoutException:
                        logger.debug(f"XPath {xpath} 타임아웃")
                        continue
                    except Exception as e:
                        logger.debug(f"XPath {xpath} 실패: {e}")
                        continue
            
            if not write_button:
                logger.error("글쓰기 버튼을 찾을 수 없습니다")
                return False
            
            # 글쓰기 버튼 클릭 (새 창에서 열림)
            try:
                logger.info(f"글쓰기 버튼 클릭 시도 (셀렉터: {used_selector})")
                
                # 클릭 전 현재 창 개수 확인
                current_windows = len(self.helper.driver.window_handles)
                
                # 방법 1: 일반 클릭
                write_button.click()
                
                # 새 창이 열릴 때까지 잠시 대기
                time.sleep(2)
                
                # 새 창이 열렸는지 확인
                new_windows = len(self.helper.driver.window_handles)
                if new_windows > current_windows:
                    logger.info("✅ 글쓰기 버튼 클릭 성공 - 새 창에서 글쓰기 페이지 열림")
                    
                    # 새 창으로 전환
                    new_window_handle = None
                    for handle in self.helper.driver.window_handles:
                        if handle != self.helper.driver.current_window_handle:
                            new_window_handle = handle
                            break
                    
                    if new_window_handle:
                        logger.info("새 창으로 전환 중...")
                        self.helper.driver.switch_to.window(new_window_handle)
                        time.sleep(2)  # 페이지 로딩 대기
                        
                        # 글쓰기 페이지 URL 확인
                        current_url = self.helper.current_url
                        logger.info(f"새 창 URL: {current_url}")
                        
                        # 작성 중인 글 팝업 처리
                        if "blog.naver.com" in current_url and "Redirect=Write" in current_url:
                            logger.info("글쓰기 페이지 확인됨 - 팝업 처리 시작")
                            popup_handled = self.handle_draft_popup()
                            if popup_handled:
                                logger.info("✅ 글쓰기 페이지 준비 완료")
                            else:
                                logger.warning("팝업 처리 실패했지만 계속 진행")
                            return True
                        else:
                            logger.warning(f"예상과 다른 글쓰기 페이지 URL: {current_url}")
                            return True  # 일단 성공으로 처리
                    
                    return True
                else:
                    logger.warning("새 창이 열리지 않음 - 현재 창에서 이동되었을 수 있음")
                    # 현재 URL 확인
                    current_url = self.helper.current_url
                    if "GoBlogWrite.naver" in current_url or ("blog.naver.com" in current_url and "Redirect=Write" in current_url):
                        logger.info("✅ 현재 창에서 글쓰기 페이지로 이동됨")
                        
                        # 작성 중인 글 팝업 처리
                        popup_handled = self.handle_draft_popup()
                        if popup_handled:
                            logger.info("✅ 글쓰기 페이지 준비 완료")
                        else:
                            logger.warning("팝업 처리 실패했지만 계속 진행")
                        return True
                    else:
                        logger.warning(f"예상과 다른 페이지: {current_url}")
                        return False
                
            except Exception as e:
                logger.warning(f"일반 클릭 실패, JavaScript 클릭 시도: {e}")
                try:
                    # 방법 2: JavaScript 클릭
                    self.helper.driver.execute_script("arguments[0].click();", write_button)
                    time.sleep(2)
                    
                    # 새 창 확인
                    new_windows = len(self.helper.driver.window_handles)
                    if new_windows > current_windows:
                        logger.info("✅ JavaScript 클릭으로 글쓰기 페이지 열림")
                        
                        # 새 창으로 전환
                        new_window_handle = None
                        for handle in self.helper.driver.window_handles:
                            if handle != self.helper.driver.current_window_handle:
                                new_window_handle = handle
                                break
                        
                        if new_window_handle:
                            logger.info("새 창으로 전환 중...")
                            self.helper.driver.switch_to.window(new_window_handle)
                            time.sleep(2)  # 페이지 로딩 대기
                            
                            # 작성 중인 글 팝업 처리
                            current_url = self.helper.current_url
                            if "blog.naver.com" in current_url and "Redirect=Write" in current_url:
                                logger.info("글쓰기 페이지 확인됨 - 팝업 처리 시작")
                                popup_handled = self.handle_draft_popup()
                                if popup_handled:
                                    logger.info("✅ 글쓰기 페이지 준비 완료")
                                else:
                                    logger.warning("팝업 처리 실패했지만 계속 진행")
                        
                        return True
                    else:
                        current_url = self.helper.current_url
                        if "GoBlogWrite.naver" in current_url or ("blog.naver.com" in current_url and "Redirect=Write" in current_url):
                            logger.info("✅ JavaScript 클릭으로 글쓰기 페이지로 이동됨")
                            
                            # 작성 중인 글 팝업 처리
                            popup_handled = self.handle_draft_popup()
                            if popup_handled:
                                logger.info("✅ 글쓰기 페이지 준비 완료")
                            else:
                                logger.warning("팝업 처리 실패했지만 계속 진행")
                            return True
                        else:
                            logger.error("JavaScript 클릭도 실패")
                            return False
                            
                except Exception as e2:
                    logger.error(f"JavaScript 클릭도 실패: {e2}")
                    return False
            
        except Exception as e:
            logger.error(f"글쓰기 버튼 클릭 실패: {e}")
            return False
    
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
        """키워드로 네이버 블로그 상위 검색 후 상위 블로그 분석"""
        try:
            logger.info(f"네이버 블로그 검색 시작: {keyword}")
            
            # URL 인코딩
            import urllib.parse
            encoded_keyword = urllib.parse.quote(keyword)
            search_url = f"https://search.naver.com/search.naver?ssc=tab.blog.all&sm=tab_jum&query={encoded_keyword}"
            
            logger.info(f"검색 URL: {search_url}")
            
            # 검색 페이지로 이동
            self.helper.goto(search_url)
            time.sleep(3)  # 페이지 로딩 대기
            
            wait = WebDriverWait(self.helper.driver, 10)
            
            # 블로그 검색 결과 수집
            blog_results = []
            
            # title_area div 찾기
            title_areas = self.helper.find_elements('div.title_area')
            logger.info(f"검색 결과 개수: {len(title_areas)}")
            
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
                        logger.info(f"상위 블로그 발견 [{len(blog_results)+1}]: {title}")
                        logger.debug(f"링크: {href}")
                        
                        blog_info = {
                            'rank': len(blog_results) + 1,
                            'title': title,
                            'url': href,
                            'preview': title[:50] + '...' if len(title) > 50 else title
                        }
                        blog_results.append(blog_info)
                    else:
                        logger.debug(f"네이버 블로그가 아닌 링크 스킵: {href}")
                
                except Exception as e:
                    logger.debug(f"블로그 링크 추출 오류 (항목 {i+1}): {e}")
                    continue
            
            logger.info(f"상위 {len(blog_results)}개 블로그 수집 완료")
            return blog_results
            
        except Exception as e:
            logger.error(f"블로그 검색 실패: {e}")
            return []
    
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
                analysis_result['text_content'] = final_text[:500] + '...' if len(final_text) > 500 else final_text
                
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
            
            # 콘텐츠 구조 분석 (글-이미지-글 순서)
            try:
                content_structure = self.extract_content_structure()
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
    
    def analyze_top_blogs(self, keyword: str, max_results: int = 3) -> list:
        """상위 블로그 검색 및 분석 통합"""
        try:
            logger.info(f"📊 상위 블로그 통합 분석 시작: '{keyword}' (상위 {max_results}개)")
            
            # 1단계: 블로그 검색
            logger.info("🔍 1단계: 블로그 검색 중...")
            blog_list = self.search_top_blogs(keyword, max_results)
            
            if not blog_list:
                logger.warning("검색된 블로그가 없습니다")
                return []
            
            logger.info(f"✅ {len(blog_list)}개 블로그 검색 완료")
            
            # 2단계: 각 블로그 상세 분석
            analyzed_blogs = []
            for i, blog in enumerate(blog_list):
                try:
                    logger.info(f"📝 2단계: {i+1}/{len(blog_list)} - '{blog['title'][:30]}...' 분석 중...")
                    
                    # 개별 블로그 분석
                    analysis_result = self.analyze_blog_content(blog['url'])
                    
                    # 검색 결과와 분석 결과 통합
                    integrated_result = {
                        'rank': blog['rank'],
                        'title': analysis_result.get('title', blog['title']),
                        'url': blog['url'],
                        'content_length': analysis_result.get('content_length', 0),
                        'image_count': analysis_result.get('image_count', 0),
                        'gif_count': analysis_result.get('gif_count', 0),
                        'video_count': analysis_result.get('video_count', 0),
                        'tags': analysis_result.get('tags', []),
                        'text_content': analysis_result.get('text_content', ''),
                        'content_structure': analysis_result.get('content_structure', [])
                    }
                    
                    analyzed_blogs.append(integrated_result)
                    logger.info(f"✅ {i+1}번째 블로그 분석 완료")
                    
                except Exception as e:
                    logger.error(f"❌ {i+1}번째 블로그 분석 실패: {e}")
                    # 분석 실패해도 기본 정보는 포함
                    failed_result = {
                        'rank': blog['rank'],
                        'title': blog['title'],
                        'url': blog['url'],
                        'content_length': 0,
                        'image_count': 0,
                        'gif_count': 0,
                        'video_count': 0,
                        'tags': [],
                        'text_content': '분석 실패',
                        'content_structure': []
                    }
                    analyzed_blogs.append(failed_result)
                    continue
            
            logger.info(f"🎉 상위 블로그 통합 분석 완료: {len(analyzed_blogs)}개")
            return analyzed_blogs
            
        except Exception as e:
            logger.error(f"❌ 상위 블로그 통합 분석 실패: {e}")
            raise BusinessError(f"블로그 분석 실패: {str(e)}")


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