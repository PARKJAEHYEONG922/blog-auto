"""
서로이웃 추가 모듈의 웹 자동화 어댑터 (Selenium Helper 사용)
"""
from typing import List, Optional, Tuple
import re
import time
from selenium.webdriver.common.keys import Keys

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from src.vendors.web_automation.selenium_helper import SeleniumHelper, get_default_selenium_config
from src.foundation.logging import get_logger
from src.foundation.exceptions import BusinessError
from .models import LoginCredentials, BloggerInfo, LoginStatus, NeighborAddRequest, NeighborAddStatus

logger = get_logger("neighbor_add.adapters")


class NaverBlogAutomationAdapter:
    """네이버 블로그 자동화 어댑터 (Selenium Helper 사용)"""
    
    def __init__(self):
        # Selenium Helper 사용
        config = get_default_selenium_config(headless=False)  # 브라우저 창 표시
        self.helper = SeleniumHelper(config)
        
        self.is_logged_in = False
        self.two_factor_auth_detected = False  # 2차 인증 감지 플래그
        
        # 탭 관리
        self.main_tab_handle = None  # 메인 탭 (로그인/검색)
        self.neighbor_add_tab_handle = None  # 서로이웃 추가 전용 탭
        
        # 네이버 URL들
        self.login_url = "https://nid.naver.com/nidlogin.login?svctype=262144&url=https%3A%2F%2Fm.blog.naver.com%2FRecommendation.naver%3F"
        self.search_url = "https://m.blog.naver.com/SectionSearch.naver"
        self.neighbor_add_form_url = "https://m.blog.naver.com/BuddyAddForm.naver?blogId={}"
    
    def start_browser(self):
        """브라우저 시작 (Selenium Helper 사용)"""
        try:
            logger.info("Selenium Helper로 브라우저 시작")
            
            # 헬퍼 초기화
            self.helper.initialize()
            
            # 메인 탭 핸들 저장
            self.main_tab_handle = self.helper.driver.current_window_handle
            logger.info(f"메인 탭 핸들 저장: {self.main_tab_handle}")
            
            # 네이버 로그인 페이지에서 바로 시작
            self.helper.goto(self.login_url)
            logger.info("네이버 로그인 페이지로 이동 완료")
            
            logger.info("브라우저 시작 완료 - Selenium Helper")
            
        except Exception as e:
            logger.error(f"브라우저 시작 실패: {e}")
            raise BusinessError(f"브라우저 시작 실패: {str(e)}")
    
    def close_browser(self):
        """브라우저 종료"""
        try:
            logger.info("브라우저 종료 중...")
            
            # 헬퍼 정리
            self.helper.cleanup()
                
            # 상태 초기화
            self.is_logged_in = False
            self.two_factor_auth_detected = False
            
            logger.info("브라우저 종료 완료")
        except Exception as e:
            logger.error(f"브라우저 종료 중 오류: {e}")
            # 강제 초기화
            self.is_logged_in = False
            self.two_factor_auth_detected = False
    
    def login_naver(self, credentials: LoginCredentials) -> bool:
        """네이버 로그인 (클립보드 사용으로 보안 우회) - 메인 페이지 사용"""
        try:
            logger.info("네이버 로그인 시작")
            
            if not self.helper.driver:
                raise BusinessError("헬퍼 드라이버가 초기화되지 않았습니다")
            
            # 이미 로그인 페이지에 있는지 확인
            if "nid.naver.com/nidlogin.login" not in self.helper.current_url:
                logger.debug(f"로그인 페이지로 이동: {self.login_url}")
                self.helper.goto(self.login_url)
                time.sleep(1.5)
            else:
                logger.info("이미 로그인 페이지에 있음")
            
            # 아이디 입력 (JavaScript 클립보드 방식 - 타이밍 개선)
            logger.info(f"아이디 입력 중: {credentials.username}")
            try:
                # 로그인 페이지 완전 로딩 대기
                time.sleep(1.5)
                
                # 아이디 필드 찾기 및 클릭
                if self.helper.click_element('#id'):
                    logger.info("아이디 필드 클릭 성공")
                    time.sleep(1.0)  # 포커스 안정화 대기
                    
                    # 기존 내용 취리
                    id_field = self.helper.find_element('#id')
                    if id_field:
                        id_field.clear()  # 기본 clear 먼저 시도
                        time.sleep(0.5)
                        
                        # Ctrl+A 후 Delete로 확실히 비우기
                        id_field.send_keys(Keys.CONTROL + 'a')
                        time.sleep(0.3)
                        id_field.send_keys(Keys.DELETE)
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
                    self.helper.execute_script(copy_script)
                    time.sleep(1.2)  # 클립보드 복사 완료 대기
                    
                    # 아이디 필드에 포커스 재확인 후 붙여넣기
                    id_field = self.helper.find_element('#id')
                    if id_field:
                        # 포커스 재설정
                        id_field.click()
                        time.sleep(0.3)
                        
                        # Ctrl+V로 붙여넣기
                        id_field.send_keys(Keys.CONTROL + 'v')
                        time.sleep(0.8)
                        
                        # 입력 결과 확인
                        actual_value = id_field.get_attribute('value')
                        if actual_value == credentials.username:
                            logger.info(f"✅ 아이디 입력 성공: {credentials.username}")
                        else:
                            logger.warning(f"⚠️ 아이디 입력 불일치 - 입력: '{actual_value}', 예상: '{credentials.username}'")
                            return False
                    else:
                        logger.error("아이디 필드를 다시 찾을 수 없음")
                        return False
                else:
                    logger.error("아이디 필드 클릭 실패")
                    return False
                
            except Exception as e:
                logger.error(f"아이디 입력 실패: {e}")
                return False
            
            # 비밀번호 입력 (JavaScript 클립보드 방식 - 타이밍 개선)
            logger.info("비밀번호 입력 중...")
            try:
                # 아이디 입력 완료 후 충분히 대기
                time.sleep(1.0)
                
                # 비밀번호 필드 찾기 및 클릭
                if self.helper.click_element('#pw'):
                    logger.info("비밀번호 필드 클릭 성공")
                    time.sleep(1.0)  # 포커스 안정화 대기
                    
                    # 기존 내용 취리
                    pw_field = self.helper.find_element('#pw')
                    if pw_field:
                        pw_field.clear()  # 기본 clear 먼저 시도
                        time.sleep(0.5)
                        
                        # Ctrl+A 후 Delete로 확실히 비우기
                        pw_field.send_keys(Keys.CONTROL + 'a')
                        time.sleep(0.3)
                        pw_field.send_keys(Keys.DELETE)
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
                    self.helper.execute_script(copy_script)
                    time.sleep(1.2)  # 클립보드 복사 완료 대기
                    
                    # 비밀번호 필드에 포커스 재확인 후 붙여넣기
                    pw_field = self.helper.find_element('#pw')
                    if pw_field:
                        # 포커스 재설정
                        pw_field.click()
                        time.sleep(0.3)
                        
                        # Ctrl+V로 붙여넣기
                        pw_field.send_keys(Keys.CONTROL + 'v')
                        time.sleep(0.8)
                        
                        # 입력 결과 확인 (비밀번호는 길이만 확인)
                        actual_value = pw_field.get_attribute('value')
                        if len(actual_value) == len(credentials.password):
                            logger.info(f"✅ 비밀번호 입력 성공 (길이: {len(credentials.password)})")
                        else:
                            logger.warning(f"⚠️ 비밀번호 입력 길이 불일치 - 입력 길이: {len(actual_value)}, 예상 길이: {len(credentials.password)}")
                            return False
                    else:
                        logger.error("비밀번호 필드를 다시 찾을 수 없음")
                        return False
                else:
                    logger.error("비밀번호 필드 클릭 실패")
                    return False
                
            except Exception as e:
                logger.error(f"비밀번호 입력 실패: {e}")
                return False
            
            # 최종 입력값 확인 (디버깅)
            logger.info("로그인 전 입력값 최종 확인...")
            try:
                final_check = self.helper.execute_script("""
                    var idVal = document.getElementById('id') ? document.getElementById('id').value : 'NOT_FOUND';
                    var pwVal = document.getElementById('pw') ? document.getElementById('pw').value : 'NOT_FOUND';
                    return {
                        id: idVal,
                        pwLength: pwVal === 'NOT_FOUND' ? 0 : pwVal.length
                    };
                """)
                logger.info(f"최종 확인 - 아이디: '{final_check['id']}', 비밀번호 길이: {final_check['pwLength']}")
            except Exception as e:
                logger.warning(f"입력값 확인 실패: {e}")
            
            # 로그인 버튼 클릭 (정확한 셀렉터 사용)
            logger.info("로그인 버튼 클릭...")
            
            # 여러 가능한 셀렉터로 시도
            login_button_selectors = [
                '#submit_btn',  # 사용자가 제공한 정확한 셀렉터
                'button[id="submit_btn"]',
                'button.btn_check',
                'button[type="submit"]'
            ]
            
            button_clicked = False
            for selector in login_button_selectors:
                if self.helper.click_element(selector):
                    logger.info(f"로그인 버튼 클릭 성공 (셀렉터: {selector})")
                    button_clicked = True
                    break
                else:
                    logger.debug(f"셀렉터 {selector}로 버튼 찾기 실패")
            
            if not button_clicked:
                # 마지막 시도: JavaScript로 직접 클릭
                logger.info("JavaScript로 직접 로그인 버튼 클릭 시도...")
                try:
                    click_result = self.helper.execute_script("""
                        var loginBtn = document.getElementById('submit_btn') || 
                                      document.querySelector('button.btn_check') ||
                                      document.querySelector('button[type="submit"]');
                        if (loginBtn) {
                            loginBtn.click();
                            return true;
                        }
                        return false;
                    """)
                    
                    if click_result:
                        logger.info("JavaScript로 로그인 버튼 클릭 성공")
                        button_clicked = True
                    else:
                        logger.error("JavaScript로도 로그인 버튼을 찾을 수 없음")
                        return False
                except Exception as e:
                    logger.error(f"JavaScript 로그인 버튼 클릭 실패: {e}")
                    return False
            
            # 로그인 완료 대기 (최대 90초 - 2차 인증 시간 고려)
            logger.info("로그인 완료 대기 중...")
            
            # 로그인 완료 대기 (90초 - 2차 인증 포함)
            two_factor_detected = False
            
            for attempt in range(90):  # 90초 동안 1초마다 체크
                time.sleep(1)
                current_url = self.helper.current_url
                
                # 2차 인증 페이지 감지 (로그인 후에도 nid.naver.com에 남아있으면 2차 인증)
                if "nid.naver.com/nidlogin.login" in current_url and attempt > 3:  # 3초 후에도 로그인 페이지에 있으면 2차 인증
                    if not two_factor_detected:
                        logger.info("🔐 2차 인증 감지됨 - 사용자 인증 대기 중...")
                        self.two_factor_auth_detected = True
                        two_factor_detected = True
                    
                    # 2차 인증 중이므로 계속 대기
                    continue
                
                # 로그인 성공 확인: Recommendation.naver 페이지 도달시 성공
                if ("m.blog.naver.com/Recommendation.naver" in current_url):
                    self.is_logged_in = True
                    if two_factor_detected:
                        logger.info("🎉 2차 인증 완료 후 네이버 로그인 성공!")
                    else:
                        logger.info("네이버 로그인 성공!")
                    return True
            
            # 타임아웃 후 현재 URL 최종 확인
            final_url = self.helper.current_url
            logger.info(f"최종 URL: {final_url}")
            
            if "nid.naver.com" in final_url:
                logger.error("네이버 로그인 실패 - 로그인 페이지에서 벗어나지 못함")
                return False
            elif "m.blog.naver.com/Recommendation.naver" in final_url:
                # Recommendation 페이지에 도달했으면 성공
                self.is_logged_in = True
                logger.info("네이버 로그인 성공 (최종 확인)")
                return True
            else:
                logger.error(f"예상치 못한 URL에 도달: {final_url}")
                return False
                    
        except Exception as e:
            logger.error(f"네이버 로그인 중 오류: {e}")
            raise BusinessError(f"로그인 실패: {str(e)}")
    
    def search_bloggers_by_keyword(self, keyword: str, max_results: int = 50) -> List[BloggerInfo]:
        """키워드로 블로거 검색 (검색 페이지 사용)"""
        try:
            logger.info(f"키워드 '{keyword}'로 블로거 검색 시작 (최대 {max_results}개)")
            
            if not self.is_logged_in:
                raise BusinessError("로그인이 필요합니다")
            
            # 방법 1: 직접 검색 URL로 이동 (우선 시도)
            import urllib.parse
            encoded_keyword = urllib.parse.quote(keyword)
            search_url = f"https://m.blog.naver.com/SectionSearch.naver?orderType=sim&pageAccess=direct&periodType=all&searchValue={encoded_keyword}"
            
            logger.info(f"방법 1: 직접 검색 URL로 이동 시도 - {search_url}")
            try:
                self.helper.goto(search_url)
                time.sleep(1)  # 검색 결과 로딩 대기
                
                # 검색 결과 페이지 도착 확인
                current_url = self.helper.current_url
                if "SectionSearch.naver" in current_url:
                    logger.info("✅ 직접 URL 접근 성공")
                    # 블로거 정보 추출
                    bloggers = self._extract_bloggers_from_search_results(max_results)
                    if bloggers:
                        logger.info(f"방법 1로 {len(bloggers)}명의 블로거 추출 성공")
                        return bloggers
                    else:
                        logger.warning("방법 1로 블로거 추출 실패, 방법 2 시도")
                else:
                    logger.warning(f"직접 URL 접근 실패 - 현재 URL: {current_url}")
                    
            except Exception as e:
                logger.error(f"방법 1 실패: {e}")
            
            # 방법 2: 검색 버튼 클릭 방식
            logger.info("방법 2: 검색 버튼 클릭 방식 시도")
            
            # 추천 페이지로 이동
            self.helper.goto("https://m.blog.naver.com/Recommendation.naver")
            time.sleep(2)
            
            # 검색 버튼 클릭
            search_button_clicked = False
            search_button_selectors = [
                'a[data-click-area="gnb.nsearch"]',
                'a[href="/SectionSearch.naver"]',
                'a.btn__PPrNT',
                'button[aria-label="검색"]'
            ]
            
            for selector in search_button_selectors:
                if self.helper.click_element(selector):
                    logger.info(f"검색 버튼 클릭 성공: {selector}")
                    search_button_clicked = True
                    time.sleep(1.5)  # 검색창 나타날 때까지 대기
                    break
            
            if not search_button_clicked:
                raise BusinessError("검색 버튼을 찾을 수 없습니다")
            
            # 검색어 입력
            search_input_selectors = [
                'input[placeholder="검색어를 입력하세요."]',
                'input.input_text__pSGVO',
                'input[data-click-area="sch*g.click"]'
            ]
            
            search_input = None
            for selector in search_input_selectors:
                search_input = self.helper.find_element(selector)
                if search_input:
                    logger.info(f"검색 입력창 발견: {selector}")
                    break
            
            if search_input:
                logger.info(f"검색어 입력: {keyword}")
                search_input.clear()
                search_input.send_keys(keyword)
                time.sleep(0.5)
                search_input.send_keys(Keys.RETURN)  # 엔터키
                time.sleep(1)  # 검색 결과 로딩 대기
                
                # 검색 결과 페이지가 제대로 로드되었는지 확인
                try:
                    current_url = self.helper.current_url
                    logger.info(f"검색 결과 페이지 URL: {current_url}")
                    
                    if "SectionSearch.naver" in current_url:
                        logger.info("✅ 직접 검색 URL 접근 성공")
                        # 블로거 정보 추출 진행
                        bloggers = self._extract_bloggers_from_search_results(max_results)
                        return bloggers
                    else:
                        logger.warning(f"❌ 예상과 다른 URL로 이동: {current_url}")
                        raise Exception("직접 검색 URL 접근 실패")
                except Exception as url_check_error:
                    logger.error(f"URL 확인 중 오류: {url_check_error}")
                    raise
            else:
                raise BusinessError("검색 입력창을 찾을 수 없습니다")
                    
        except Exception as e:
            logger.warning(f"직접 검색 URL 접근 실패: {e}, 검색 버튼 방식으로 시도")
            
            # 방법 2: 로그인 페이지에서 검색 버튼 클릭 방식
            logger.info("로그인 완료 페이지로 이동...")
            self.helper.goto("https://m.blog.naver.com/Recommendation.naver")
            time.sleep(1)
            
            # 검색 버튼 클릭
            logger.info("검색 버튼 찾는 중...")
            search_button = self.helper.find_element('a[data-click-area="gnb.search"]')
            if search_button:
                logger.info("검색 버튼 발견, 클릭...")
                self.helper.click_element(search_button)
                time.sleep(1.5)
            else:
                logger.error("검색 버튼을 찾을 수 없음")
                raise BusinessError("검색 버튼을 찾을 수 없습니다")
            
            # 검색어 입력
            logger.info(f"검색어 '{keyword}' 입력...")
            search_input = self.helper.find_element('input.input_text__pSGVO')
            if search_input:
                self.helper.click_element(search_input)
                time.sleep(0.3)
                search_input.clear()
                self.helper.send_keys(search_input, keyword)
                time.sleep(0.3)
                self.helper.send_keys(search_input, self.helper.Keys.ENTER)
                time.sleep(1)  # 검색 결과 로딩 대기
                logger.info("검색어 입력 및 검색 완료")
            else:
                logger.error("검색어 입력 필드를 찾을 수 없음")
                raise BusinessError("검색어 입력 필드를 찾을 수 없습니다")
            
            # 블로거 정보 추출
            bloggers = self._extract_bloggers_from_search_results(max_results)
            
            if not bloggers:
                # 검색 결과가 없는 경우 페이지 상태 확인
                current_url = self.helper.current_url
                page_content = self.helper.driver.page_source
                logger.warning(f"검색 결과 없음. URL: {current_url}")
                logger.debug(f"페이지 내용 일부: {page_content[:500]}")
                raise BusinessError(f"키워드 '{keyword}'에 대한 검색 결과가 없습니다")
                
            logger.info(f"키워드 '{keyword}' 검색 완료: {len(bloggers)}명의 블로거 발견")
            return bloggers
            
        except BusinessError:
            raise
        except Exception as e:
            logger.error(f"블로거 검색 중 오류: {e}")
            raise BusinessError(f"블로거 검색 실패: {str(e)}")
    
    def _extract_bloggers_from_search_results(self, max_results: int = 50) -> List[BloggerInfo]:
        """검색 결과 페이지에서 블로거 정보 추출"""
        bloggers = []
        collected_count = 0
        scroll_count = 0
        max_scrolls = (max_results // 15) + 2  # 15개씩 나오므로
        
        while collected_count < max_results and scroll_count < max_scrolls:
            logger.info(f"블로거 ID 수집 중... (현재 {collected_count}/{max_results})")
            
            # 현재 페이지 HTML 구조 디버깅
            page_html = self.helper.driver.page_source
            logger.debug(f"현재 페이지 HTML 길이: {len(page_html)}")
            
            # 여러 가능한 셀렉터로 블로거 정보 추출 시도
            extraction_successful = False
            
            # 방법 1: 다중 셀렉터로 네이버 블로그 검색 결과 추출 (디버깅 강화)
            logger.info("방법 1: 다중 셀렉터로 검색 결과에서 ID 추출")
            
            # 실제 네이버 블로그 검색 결과 구조 (2024년 최신)
            container_selectors = [
                'div.postlist__KLANp',       # 실제 네이버 블로그 검색 결과 컨테이너
                'div[class*="postlist"]',    # postlist가 포함된 클래스
                'div.item__MaZSl',           # 사용자 이전 제공 셀렉터 (백업)
                'div[class*="item"]',        # item이 포함된 클래스
                'div[class*="search"]',      # search가 포함된 클래스  
                'div[class*="result"]',      # result가 포함된 클래스
                'article',                   # article 태그
                'li[class*="item"]',        # li 태그 중 item 포함
            ]
            
            search_items = []
            for selector in container_selectors:
                items = self.helper.find_elements(selector)
                if items:
                    logger.info(f"셀렉터 '{selector}': {len(items)}개 요소 발견")
                    # PostView.naver 링크가 있는 항목만 필터링
                    valid_items = []
                    for item in items:
                        try:
                            from selenium.webdriver.common.by import By
                            link = item.find_element(By.CSS_SELECTOR, 'a[href*="PostView.naver"]')
                            if link:
                                valid_items.append(item)
                        except:
                            continue
                    
                    if valid_items:
                        logger.info(f"셀렉터 '{selector}': {len(valid_items)}개 유효한 블로그 항목 발견")
                        search_items = valid_items
                        break  # 첫 번째로 유효한 셀렉터 사용
            
            if not search_items:
                logger.warning("모든 셀렉터로 검색 결과를 찾을 수 없음 - 페이지 구조 확인 필요")
                # 디버깅: 페이지 전체 구조 로깅
                try:
                    page_html = self.helper.driver.page_source[:2000]  # 처음 2000자만
                    logger.debug(f"페이지 HTML 샘플: {page_html}")
                    
                    # PostView.naver 링크 직접 검색
                    all_links = self.helper.find_elements('a[href*="PostView.naver"]')
                    logger.info(f"전체 PostView.naver 링크 개수: {len(all_links)}")
                    
                    if all_links:
                        for i, link in enumerate(all_links[:5]):  # 처음 5개만 확인
                            href = link.get_attribute('href')
                            logger.debug(f"링크 {i+1}: {href}")
                except Exception as e:
                    logger.error(f"디버깅 중 오류: {e}")
            else:
                logger.info(f"총 {len(search_items)}개 검색 결과 항목에서 ID 추출 시작")
                
                for i, item in enumerate(search_items):
                    if collected_count >= max_results:
                        break
                    
                    try:
                        # PostView.naver 링크 찾기
                        link_element = item.find_element(By.CSS_SELECTOR, 'a[href*="PostView.naver"]')
                        href = link_element.get_attribute('href')
                        
                        if href and 'blogId=' in href:
                            # blogId= 뒤의 값 추출
                            import re
                            blog_id_match = re.search(r'blogId=([^&]+)', href)
                            if blog_id_match:
                                blog_id = blog_id_match.group(1)
                                
                                # 블로거 이름 추출 (실제 네이버 블로그 구조 기반)
                                blog_name = f"블로거_{blog_id}"  # 기본값
                                try:
                                    # 실제 네이버 블로그 검색 결과에서 블로거 이름 찾기
                                    name_selectors = [
                                        '.nickname__B1XPu',      # 실제 닉네임 클래스
                                        '.profile_area__riebt .nickname__B1XPu',  # 전체 경로
                                        'span.nickname__B1XPu',  # span 태그 명시
                                        '.name', '.title', '.blog_name', '.user_name', '.nick', '.author',  # 백업 셀렉터들
                                        'strong', 'span'
                                    ]
                                    for selector in name_selectors:
                                        try:
                                            blog_name_elem = item.find_element(By.CSS_SELECTOR, selector)
                                            text = blog_name_elem.text.strip()
                                            if text and len(text) > 0 and len(text) < 50:  # 적절한 길이의 텍스트만
                                                blog_name = text
                                                logger.debug(f"블로거 이름 추출 성공: {blog_name} (셀렉터: {selector})")
                                                break
                                        except:
                                            continue
                                except:
                                    pass  # 기본값 사용
                                
                                # 중복 체크 후 추가
                                if not any(b.blog_id == blog_id for b in bloggers):
                                    blogger_info = BloggerInfo(
                                        blog_id=blog_id,
                                        blog_name=blog_name,
                                        blog_url=f"https://blog.naver.com/{blog_id}"
                                    )
                                    bloggers.append(blogger_info)
                                    collected_count += 1
                                    extraction_successful = True
                                    logger.info(f"✅ 블로거 수집 성공 #{collected_count}: {blog_id} - {blog_name}")
                                else:
                                    logger.debug(f"중복 블로거 스킵: {blog_id}")
                        else:
                            logger.debug(f"항목 {i+1}: blogId가 없는 링크 - {href}")
                            
                    except Exception as e:
                        logger.debug(f"항목 {i+1} 처리 중 오류: {e}")
                        continue
            
            logger.info(f"방법 1 완료: {collected_count}개 ID 추출 성공")
            
            # 방법 2: 페이지 소스에서 직접 파싱 (강화된 백업 방식)
            if not extraction_successful and scroll_count == 0:
                logger.info("방법 2: 페이지 소스에서 정규식으로 blogId 직접 추출")
                try:
                    page_content = self.helper.driver.page_source
                    
                    # 정규식으로 blogId 패턴 추출
                    import re
                    
                    # PostView.naver 링크에서 blogId 추출
                    postview_pattern = r'PostView\.naver\?[^"]*blogId=([a-zA-Z0-9_-]+)'
                    postview_matches = re.findall(postview_pattern, page_content)
                    
                    # blog.naver.com 링크에서 blogId 추출  
                    blog_pattern = r'blog\.naver\.com/([a-zA-Z0-9_-]+)'
                    blog_matches = re.findall(blog_pattern, page_content)
                    
                    # 모든 blogId 수집
                    all_blog_ids = list(set(postview_matches + blog_matches))
                    
                    logger.info(f"방법 2: 정규식으로 {len(all_blog_ids)}개 고유 blogId 발견")
                    
                    for blog_id in all_blog_ids:
                        if collected_count >= max_results:
                            break
                            
                        if not any(b.blog_id == blog_id for b in bloggers):
                            blogger_info = BloggerInfo(
                                blog_id=blog_id,
                                blog_name=f"블로거_{blog_id}",
                                blog_url=f"https://blog.naver.com/{blog_id}"
                            )
                            bloggers.append(blogger_info)
                            collected_count += 1
                            extraction_successful = True
                            logger.info(f"✅ 방법2로 블로거 수집: {blog_id}")
                    
                except Exception as e:
                    logger.error(f"방법 2 실행 중 오류: {e}")
            
            # 검색 결과가 없는 경우 페이지 상태 로그
            if not extraction_successful and scroll_count == 0:
                current_url = self.helper.current_url
                page_title = self.helper.driver.title
                logger.warning(f"블로거 추출 실패 - URL: {current_url}, 제목: {page_title}")
                
                # 검색 결과 관련 요소들 확인
                no_result_elements = self.helper.find_elements('.no_result, .empty_result, .search_empty')
                if no_result_elements:
                    logger.warning("검색 결과 없음 메시지 발견")
            
            # 더 많은 결과가 필요한 경우 스크롤
            if collected_count < max_results and extraction_successful:
                logger.info("더 많은 결과를 위해 스크롤...")
                self.helper.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1)  # 로딩 대기 시간 단축
                scroll_count += 1
            else:
                break
        
        logger.info(f"블로거 추출 완료: {len(bloggers)}개 발견 (스크롤 {scroll_count}회)")
        return bloggers
    
    def _extract_blogger_from_link(self, link_element, href: str) -> BloggerInfo:
        """링크 요소에서 직접 블로거 정보 추출"""
        try:
            # 블로그 ID 추출
            blog_id = None
            
            # PostView.naver URL에서 blogId 파라미터 추출
            if 'PostView.naver' in href:
                blog_id_match = re.search(r'blogId=([^&]+)', href)
                if blog_id_match:
                    blog_id = blog_id_match.group(1)
            
            # 직접 blog.naver.com URL에서 ID 추출
            elif 'blog.naver.com' in href:
                blog_id_match = re.search(r'blog\.naver\.com/([^/?]+)', href)
                if blog_id_match:
                    blog_id = blog_id_match.group(1)
            
            if not blog_id:
                return None
            
            # 블로그 제목 추출
            blog_title = link_element.text
            if not blog_title or blog_title.strip() == '':
                blog_title = f"블로거_{blog_id}"
            
            return BloggerInfo(
                blog_id=blog_id,
                blog_name=blog_title.strip(),
                blog_url=f"https://blog.naver.com/{blog_id}"
            )
            
        except Exception as e:
            logger.debug(f"링크에서 블로거 정보 추출 실패: {e}")
            return None
    
    def _extract_blog_ids_from_html(self, html_content: str) -> List[str]:
        """HTML 소스에서 블로그 ID 직접 추출 (정규식 사용)"""
        blog_ids = []
        
        try:
            # PostView.naver URL의 blogId 파라미터 추출
            blog_id_matches = re.findall(r'blogId=([a-zA-Z0-9_-]+)', html_content)
            blog_ids.extend(blog_id_matches)
            
            # blog.naver.com URL에서 ID 추출
            blog_url_matches = re.findall(r'blog\.naver\.com/([a-zA-Z0-9_-]+)', html_content)
            blog_ids.extend(blog_url_matches)
            
            # 중복 제거
            unique_ids = list(set(blog_ids))
            
            # 유효한 블로그 ID만 필터링 (3자 이상, 특수문자 제외)
            valid_ids = []
            for blog_id in unique_ids:
                if len(blog_id) >= 3 and blog_id not in ['blog', 'post', 'view', 'search']:
                    valid_ids.append(blog_id)
            
            logger.info(f"HTML 파싱으로 {len(valid_ids)}개 블로그 ID 추출")
            return valid_ids[:50]  # 최대 50개까지만
            
        except Exception as e:
            logger.error(f"HTML 파싱 실패: {e}")
            return []

    def _extract_blogger_from_element(self, element, link_selector: str) -> BloggerInfo:
        """요소에서 블로거 정보 추출"""
        try:
            # 링크 찾기
            try:
                link = element.find_element_by_css_selector(link_selector)
            except:
                return None
            
            if not link:
                return None
            
            href = link.get_attribute('href')
            if not href:
                return None
            
            # 블로그 ID 추출
            blog_id = None
            
            # PostView.naver URL에서 blogId 파라미터 추출
            if 'PostView.naver' in href:
                blog_id_match = re.search(r'blogId=([^&]+)', href)
                if blog_id_match:
                    blog_id = blog_id_match.group(1)
            
            # 직접 blog.naver.com URL에서 ID 추출
            elif 'blog.naver.com' in href:
                blog_id_match = re.search(r'blog\.naver\.com/([^/?]+)', href)
                if blog_id_match:
                    blog_id = blog_id_match.group(1)
            
            if not blog_id:
                return None
            
            # 블로그 제목 추출
            blog_title = link.text
            if not blog_title or blog_title.strip() == '':
                blog_title = f"블로거_{blog_id}"
            
            return BloggerInfo(
                blog_id=blog_id,
                blog_name=blog_title.strip(),
                blog_url=f"https://blog.naver.com/{blog_id}"
            )
            
        except Exception as e:
            logger.debug(f"요소에서 블로거 정보 추출 실패: {e}")
            return None
    
    
    def add_neighbor(self, blogger_info: BloggerInfo, message: str) -> bool:
        """서로이웃 추가 요청 (통합 최적화 버전)"""
        try:
            if not self.is_logged_in or not self.helper.driver:
                raise BusinessError("로그인 또는 드라이버 오류")
            
            # 탭 준비
            if not self.neighbor_add_tab_handle and not self.create_neighbor_add_tab():
                raise BusinessError("서로이웃 추가 전용 탭 생성 실패")
            
            self.switch_to_neighbor_add_tab()
            self.helper.goto(f"https://m.blog.naver.com/BuddyAddForm.naver?blogId={blogger_info.blog_id}")
            
            # 통합 처리: 페이지 로딩 + 팝업확인 + 라디오버튼 + 메시지입력 + 확인버튼을 한 번에
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.by import By
            
            # 페이지 로딩 대기 (textarea 또는 라디오 버튼 중 하나라도 있으면 로딩 완료)
            wait = WebDriverWait(self.helper.driver, 2)
            try:
                # textarea나 라디오 버튼 중 하나가 로딩될 때까지 대기
                wait.until(lambda driver: 
                    driver.find_elements(By.ID, 'bothBuddyRadio') or 
                    driver.find_elements(By.CSS_SELECTOR, 'textarea.textarea_t1') or
                    driver.find_elements(By.CSS_SELECTOR, 'p.set_dsc'))
            except:
                # 대기 실패시 그냥 진행
                pass
            
            # 모든 작업을 하나의 JavaScript로 통합 처리
            result = self.helper.execute_script(f"""
                // 1. 가장 간단하고 확실한 방법으로 하루 100명 제한 팝업 확인
                console.log('🔍 하루 100명 제한 팝업 감지 시작');
                
                // 방법 1: _alertLayer 존재 여부로 확인
                var alertLayer = document.querySelector('#_alertLayer');
                var dailyLimitPopup = document.querySelector('div.lyr_cont.lyr_alert');
                console.log('alertLayer 존재:', !!alertLayer);
                
                if (alertLayer) {{
                    console.log('alertLayer display:', alertLayer.style.display);
                    
                    // 방법 2: p.dsc 요소의 텍스트 직접 확인
                    var dscElement = document.querySelector('#_alertLayer p.dsc');
                    console.log('dsc 요소 존재:', !!dscElement);
                    
                    if (dscElement) {{
                        var popupText = dscElement.textContent;
                        console.log('📝 팝업 전체 텍스트:', popupText);
                        
                        // 하루 제한 텍스트 확인
                        if (popupText.includes('하루에 신청 가능한 이웃수가 초과되어')) {{
                            console.log('🚫🚫🚫 하루 100명 제한 확실히 감지됨!');
                            return 'daily_limit_reached';
                        }}
                        
                        // 5000명 초과 텍스트 확인  
                        if (popupText.includes('상대방의 이웃수가 5,000명이 초과되어')) {{
                            console.log('🚫 상대방 5000명 초과 감지됨');
                            return 'neighbor_limit_exceeded';
                        }}
                    }}
                    
                    // 방법 3: 더 넓게 검색
                    var allDscElements = document.querySelectorAll('p.dsc');
                    console.log('전체 p.dsc 요소 개수:', allDscElements.length);
                    
                    for (var i = 0; i < allDscElements.length; i++) {{
                        var text = allDscElements[i].textContent;
                        console.log('p.dsc[' + i + '] 텍스트:', text);
                        
                        if (text.includes('하루에 신청 가능한') || text.includes('이웃수가 초과되어')) {{
                            console.log('🚫🚫🚫 하루 제한 감지됨 (방법3)!');
                            return 'daily_limit_reached';
                        }}
                        
                        if (text.includes('5,000명이 초과되어')) {{
                            console.log('🚫 5000명 초과 감지됨 (방법3)');
                            return 'neighbor_limit_exceeded';
                        }}
                    }}
                }}
                
                // 2. 서로이웃/이웃 추가 완료 상태 확인
                var successPatterns = ['이웃으로 추가하였습니다', '서로이웃을 신청하였습니다'];
                var successSelectors = ['p.txt', 'p.txt strong', 'span.dsc', '.txt'];
                
                for (var i = 0; i < successSelectors.length; i++) {{
                    var elements = document.querySelectorAll(successSelectors[i]);
                    for (var j = 0; j < elements.length; j++) {{
                        var text = elements[j].textContent;
                        for (var k = 0; k < successPatterns.length; k++) {{
                            if (text.includes(successPatterns[k])) {{
                                console.log('완료 상태 감지: ' + text);
                                return 'success_completed';
                            }}
                        }}
                    }}
                }}
                
                // 3. 추가 팝업 확인 (동적으로 생성되는 경우)
                if (dailyLimitPopup && !alertLayer) {{
                    var dscElement = dailyLimitPopup.querySelector('p.dsc');
                    if (dscElement) {{
                        var popupText = dscElement.textContent.trim();
                        console.log('추가 팝업 텍스트 감지:', popupText);
                        
                        if (popupText.includes('하루에 신청 가능한 이웃수가 초과되어') || 
                            popupText.includes('더이상 이웃을 추가할 수 없습니다')) {{
                            
                            console.log('추가 하루 100명 제한 팝업 감지됨');
                            var confirmBtn = dailyLimitPopup.querySelector('a.btn_100.green') || 
                                           dailyLimitPopup.querySelector('.btn_100');
                            if (confirmBtn) {{
                                confirmBtn.click();
                            }}
                            return 'daily_limit_reached';
                        }}
                    }}
                }}
                
                // 4. 이미 서로이웃 신청된 상태 확인 (라디오 버튼이 없고 "신청을 수락하면" 텍스트 존재)
                var alreadyRequestedText = document.querySelector('p.set_dsc');
                if (alreadyRequestedText && alreadyRequestedText.textContent.includes('서로이웃 신청을 수락하면')) {{
                    return 'already_requested';
                }}
                
                // 5. 서로이웃 라디오 버튼 처리 (확실히 선택)
                var bothBuddyRadio = document.getElementById('bothBuddyRadio');
                var buddyRadio = document.getElementById('buddyRadio');
                
                if (bothBuddyRadio) {{
                    if (bothBuddyRadio.disabled || bothBuddyRadio.getAttribute('ng-disabled') === 'true') {{
                        return 'disabled';
                    }}
                    
                    // 먼저 다른 라디오 버튼 해제
                    if (buddyRadio) {{
                        buddyRadio.checked = false;
                    }}
                    
                    // 서로이웃 라디오 버튼 확실히 선택 (ng-dirty, ng-touched 상태로 만들기)
                    bothBuddyRadio.checked = true;
                    
                    // 모든 이벤트 발생시켜서 Angular 상태 업데이트
                    bothBuddyRadio.click(); 
                    bothBuddyRadio.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    bothBuddyRadio.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    bothBuddyRadio.dispatchEvent(new Event('focus', {{ bubbles: true }}));
                    bothBuddyRadio.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                    
                    // Angular 모델 직접 업데이트
                    var angularScope = angular.element(bothBuddyRadio).scope();
                    if (angularScope && angularScope.data) {{
                        angularScope.data.selectedBuddyType = '1'; // 서로이웃 값 (문자열)
                        angularScope.$digest(); // $apply 대신 $digest 사용
                    }}
                    
                    // 클래스도 직접 변경 (ng-dirty, ng-touched 추가)
                    bothBuddyRadio.classList.remove('ng-pristine', 'ng-untouched');
                    bothBuddyRadio.classList.add('ng-dirty', 'ng-touched', 'ng-valid-parse');
                    
                    // 잠시 대기해서 Angular 처리 완료 확인
                    setTimeout(function() {{ console.log('서로이웃 선택 상태: ' + bothBuddyRadio.checked + ', 클래스: ' + bothBuddyRadio.className); }}, 100);
                    
                    console.log('서로이웃 라디오 버튼 선택 완료: ' + bothBuddyRadio.checked);
                }} else {{
                    console.log('서로이웃 라디오 버튼 없음');
                }}
                
                // 6. 메시지 입력 (사용자 메시지가 있는 경우)
                var messageText = `{message.replace("`", "").strip()}`;
                if (messageText) {{
                    var textarea = document.querySelector('textarea.textarea_t1') || 
                                  document.querySelector('textarea') ||
                                  document.querySelector('input[type="text"]');
                    if (textarea) {{
                        // 기존 메시지 완전히 지우고 사용자 메시지로 교체
                        textarea.focus();
                        textarea.select(); // 전체 선택
                        textarea.value = ''; // 먼저 비우기
                        textarea.value = messageText; // 사용자 메시지 입력
                        
                        // 모든 이벤트 발생
                        textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        textarea.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        textarea.dispatchEvent(new Event('keyup', {{ bubbles: true }}));
                        textarea.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                        
                        // Angular 모델 업데이트
                        var angularScope = angular.element(textarea).scope();
                        if (angularScope && angularScope.data) {{
                            angularScope.data.inviteMessage = messageText;
                            angularScope.$digest();
                        }}
                        
                        console.log('사용자 메시지 입력 완료: ' + messageText);
                    }}
                }} else {{
                    console.log('기본 메시지 사용 (메시지 변경 없음)');
                }}
                
                // 7. 확인 버튼 클릭
                var confirmBtn = document.querySelector('a.btn_ok') || 
                               document.querySelector('a[ng-click*="buddyAdd"]') ||
                               document.querySelector('button[type="submit"]') ||
                               document.querySelector('input[type="submit"]');
                if (confirmBtn) {{
                    confirmBtn.click();
                    return 'completed';
                }}
                
                return 'no_confirm_btn';
            """)
            
            # 결과 처리
            if result == 'success_completed':
                # 이미 완료된 상태 - 바로 성공 반환 (추가 대기 없이)
                logger.info(f"🎯 [성공 반환] 서로이웃 추가 이미 완료됨: {blogger_info.blog_id} → True 반환")
                return True
            elif result == 'daily_limit_reached':
                logger.warning(f"🚫 하루 100명 제한 도달: {blogger_info.blog_id}")
                return "daily_limit_reached"
            elif result == 'neighbor_limit_exceeded':
                logger.warning(f"🚫 상대방 5000명 초과로 이웃 추가 불가: {blogger_info.blog_id}")
                return "neighbor_limit_exceeded"
            elif result == 'already_requested':
                return "already_requested"
            elif result == 'disabled':
                return "disabled"
            elif result in ['not_found', 'no_confirm_btn']:
                return False
            elif result == 'completed':
                # 확인 버튼 클릭 완료 - 성공 메시지 확인 (최소 대기)
                time.sleep(0.3)
                try:
                    # 다양한 성공 메시지 패턴 확인
                    success_patterns = [
                        "서로이웃을 신청하였습니다",
                        "이웃으로 추가하였습니다"
                    ]
                    
                    # 여러 선택자로 성공 메시지 찾기
                    selectors = ['.desc', '.dsc', 'p.txt', 'span.dsc', '.txt']
                    
                    for selector in selectors:
                        elements = self.helper.find_elements(selector)
                        for element in elements:
                            element_text = element.text
                            for pattern in success_patterns:
                                if pattern in element_text:
                                    logger.info(f"🎯 [성공 반환] 서로이웃 신청 성공: {blogger_info.blog_id} - {element_text} → True 반환")
                                    return True
                    
                    logger.warning(f"성공 메시지를 찾지 못함: {blogger_info.blog_id}")
                    return False
                except Exception as e:
                    logger.error(f"성공 메시지 확인 실패: {e}")
                    return False
            
            return False
            
        except Exception as e:
            logger.error(f"서로이웃 추가 오류 ({blogger_info.blog_id}): {e}")
            return False
    
    def batch_add_neighbors(self, requests: List[NeighborAddRequest], delay_seconds: int = 3, max_daily_limit: int = 100) -> List[NeighborAddRequest]:
        """일괄 서로이웃 추가 (메인 페이지 사용, 일일 100명 제한 고려)"""
        try:
            logger.info(f"일괄 서로이웃 추가 시작: {len(requests)}개 요청 (일일 최대 {max_daily_limit}명)")
            
            updated_requests = []
            success_count = 0
            failed_count = 0
            disabled_count = 0
            already_requested_count = 0
            
            for i, request in enumerate(requests):
                try:
                    # 일일 제한 확인
                    if success_count >= max_daily_limit:
                        logger.warning(f"일일 서로이웃 추가 제한 ({max_daily_limit}명) 도달")
                        request.status = NeighborAddStatus.FAILED
                        request.error_message = f"일일 제한 {max_daily_limit}명 도달"
                        updated_requests.append(request)
                        failed_count += 1
                        continue
                    
                    logger.info(f"진행률: {i+1}/{len(requests)} - {request.blogger_info.blog_id}")
                    logger.info(f"📊 현재 상태: 성공 {success_count}, 실패 {failed_count}, 비활성화 {disabled_count}, 이미신청 {already_requested_count}")
                    
                    request.status = NeighborAddStatus.IN_PROGRESS
                    result = self.add_neighbor(request.blogger_info, request.message)
                    
                    if result == True:
                        request.status = NeighborAddStatus.SUCCESS
                        success_count += 1
                        logger.info(f"✅ 서로이웃 추가 성공: {request.blogger_info.blog_id} (총 성공: {success_count})")
                    elif result == "disabled":
                        request.status = NeighborAddStatus.DISABLED
                        request.error_message = "서로이웃 추가 비활성화 (5000명 꽉참 또는 차단)"
                        disabled_count += 1
                        logger.info(f"🚫 서로이웃 추가 비활성화: {request.blogger_info.blog_id} (총 비활성화: {disabled_count})")
                    elif result == "already_requested":
                        request.status = NeighborAddStatus.ALREADY_REQUESTED
                        request.error_message = "이미 서로이웃 신청 진행 중"
                        already_requested_count += 1
                        logger.info(f"⏳ 이미 서로이웃 신청 진행 중: {request.blogger_info.blog_id} (총 진행중: {already_requested_count})")
                    else:
                        request.status = NeighborAddStatus.FAILED
                        request.error_message = "서로이웃 추가 실패"
                        failed_count += 1
                        logger.warning(f"❌ 서로이웃 추가 실패: {request.blogger_info.blog_id} (총 실패: {failed_count})")
                    
                    updated_requests.append(request)
                    
                    # 다음 요청 전 대기 (네이버 서버 부하 방지, 메인 페이지에서 다음 블로거로 이동)
                    if i < len(requests) - 1:
                        logger.info(f"{delay_seconds}초 대기 중... (메인 페이지에서 다음 블로거로 이동)")
                        time.sleep(delay_seconds)
                        
                except Exception as e:
                    logger.error(f"서로이웃 추가 예외 발생 ({request.blogger_info.blog_id}): {e}")
                    request.status = NeighborAddStatus.FAILED
                    request.error_message = f"예외 발생: {str(e)}"
                    updated_requests.append(request)
                    failed_count += 1
            
            logger.info(f"일괄 서로이웃 추가 완료 - 총 {len(requests)}개 처리")
            logger.info(f"📊 최종 결과:")
            logger.info(f"  ✅ 성공: {success_count}명")
            logger.info(f"  ❌ 실패: {failed_count}명") 
            logger.info(f"  🚫 비활성화: {disabled_count}명")
            logger.info(f"  ⏳ 이미 신청 진행중: {already_requested_count}명")
            
            return updated_requests
            
        except Exception as e:
            logger.error(f"일괄 서로이웃 추가 중 오류: {e}")
            raise BusinessError(f"일괄 서로이웃 추가 실패: {str(e)}")
    
    def search_more_bloggers(self, keyword: str, max_results: int = 50, existing_ids: set = None) -> List[BloggerInfo]:
        """추가 블로거 검색 (목표 달성형 서로이웃 추가에서 사용)"""
        try:
            logger.info(f"추가 블로거 검색: '{keyword}' (기존 {len(existing_ids) if existing_ids else 0}개 제외)")
            
            # 기존 검색 로직 재사용
            all_bloggers = self.search_bloggers_by_keyword(keyword, max_results * 2)  # 더 많이 검색
            
            # 기존 ID 제외
            if existing_ids:
                new_bloggers = [b for b in all_bloggers if b.blog_id not in existing_ids]
            else:
                new_bloggers = all_bloggers
            
            # 최대 결과 수 제한
            return new_bloggers[:max_results]
            
        except Exception as e:
            logger.error(f"추가 블로거 검색 실패: {e}")
            return []
    
    def create_neighbor_add_tab(self) -> bool:
        """서로이웃 추가 전용 탭 생성 (기존 탭 재사용)"""
        try:
            if not self.helper.driver:
                raise BusinessError("브라우저가 초기화되지 않았습니다")
            
            # 기존 서로이웃 탭이 유효한지 확인
            if self.neighbor_add_tab_handle:
                try:
                    current_handles = self.helper.driver.window_handles
                    if self.neighbor_add_tab_handle in current_handles:
                        # 기존 탭이 유효하면 재사용
                        self.helper.driver.switch_to.window(self.neighbor_add_tab_handle)
                        logger.info(f"기존 서로이웃 탭 재사용: {self.neighbor_add_tab_handle}")
                        return True
                    else:
                        # 기존 탭이 닫혔으면 핸들 초기화
                        self.neighbor_add_tab_handle = None
                except Exception:
                    self.neighbor_add_tab_handle = None
            
            # 새 탭 생성이 필요한 경우만
            self.helper.driver.execute_script("window.open('about:blank', '_blank');")
            
            # 새로 생성된 탭으로 전환 (마지막 탭)
            all_handles = self.helper.driver.window_handles
            self.neighbor_add_tab_handle = all_handles[-1]  # 마지막 생성된 탭
            self.helper.driver.switch_to.window(self.neighbor_add_tab_handle)
            
            logger.info(f"새 서로이웃 탭 생성 완료: {self.neighbor_add_tab_handle}")
            return True
            
        except Exception as e:
            logger.error(f"서로이웃 추가 탭 생성 실패: {e}")
            return False
    
    def switch_to_main_tab(self):
        """메인 탭으로 전환 (로그인/검색용)"""
        try:
            if self.main_tab_handle and self.helper.driver:
                self.helper.driver.switch_to.window(self.main_tab_handle)
                logger.debug("메인 탭으로 전환 완료")
            else:
                logger.warning("메인 탭 핸들이 없습니다")
        except Exception as e:
            logger.error(f"메인 탭 전환 실패: {e}")
    
    def switch_to_neighbor_add_tab(self):
        """서로이웃 추가 탭으로 전환"""
        try:
            if self.neighbor_add_tab_handle and self.helper.driver:
                self.helper.driver.switch_to.window(self.neighbor_add_tab_handle)
                logger.debug("서로이웃 추가 탭으로 전환 완료")
            else:
                # 탭이 없으면 생성
                if not self.create_neighbor_add_tab():
                    raise BusinessError("서로이웃 추가 탭 생성에 실패했습니다")
        except Exception as e:
            logger.error(f"서로이웃 추가 탭 전환 실패: {e}")
    
    def search_more_bloggers_with_scroll(self, keyword: str, current_count: int, batch_size: int = 20) -> List[BloggerInfo]:
        """스크롤을 통한 추가 블로거 검색 (메인 탭에서 실행)"""
        try:
            # 메인 탭으로 전환
            self.switch_to_main_tab()
            
            logger.info(f"키워드 '{keyword}' 추가 검색 시작 (현재: {current_count}명, 배치: {batch_size}개)")
            
            # 현재 위치에서 스크롤하여 더 많은 결과 로드
            for scroll_count in range(3):  # 최대 3번 스크롤
                self.helper.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.5)
                logger.debug(f"스크롤 {scroll_count + 1}/3 완료")
            
            # 새로운 블로거 정보 추출
            new_bloggers = self._extract_bloggers_from_search_results(batch_size)
            logger.info(f"스크롤 후 추가 추출: {len(new_bloggers)}명")
            
            return new_bloggers
            
        except Exception as e:
            logger.error(f"스크롤 기반 추가 검색 실패: {e}")
            return []
    


# 어댑터 인스턴스 생성 헬퍼
def create_naver_blog_adapter() -> NaverBlogAutomationAdapter:
    """네이버 블로그 자동화 어댑터 생성"""
    return NaverBlogAutomationAdapter()