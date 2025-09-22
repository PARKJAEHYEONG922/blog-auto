/**
 * Playwright 기반 네이버 로그인 헬퍼
 * 레거시 Selenium 코드를 Playwright로 변환
 */
import { chromium, Browser, Page, BrowserContext } from 'playwright';

export interface NaverCredentials {
  username: string;
  password: string;
}

export enum LoginStatus {
  NOT_LOGGED_IN = 'NOT_LOGGED_IN',
  LOGGED_IN = 'LOGGED_IN', 
  LOGIN_FAILED = 'LOGIN_FAILED',
  TWO_FACTOR_AUTH_REQUIRED = 'TWO_FACTOR_AUTH_REQUIRED',
  DEVICE_REGISTRATION_REQUIRED = 'DEVICE_REGISTRATION_REQUIRED'
}

export class PlaywrightNaverHelper {
  private browser: Browser | null = null;
  private context: BrowserContext | null = null;
  private page: Page | null = null;
  private isLoggedIn = false;
  private username: string | null = null;
  private twoFactorAuthDetected = false;

  // 네이버 URL들
  private readonly LOGIN_URL = 'https://nid.naver.com/nidlogin.login';
  private readonly BLOG_HOME_URL = 'https://section.blog.naver.com/BlogHome.naver';
  private readonly NAVER_HOME_URL = 'https://www.naver.com';

  constructor() {}

  /**
   * 브라우저 초기화 및 로그인 페이지로 이동
   */
  async initialize(): Promise<void> {
    try {
      console.log('Playwright 브라우저 초기화 시작...');
      
      // 브라우저 실행 (헤드리스 모드 비활성화 - 사용자가 2차 인증 등을 처리할 수 있도록)
      this.browser = await chromium.launch({
        headless: false,
        args: [
          '--disable-blink-features=AutomationControlled',
          '--disable-dev-shm-usage',
          '--no-sandbox',
          '--disable-notifications',
          '--disable-gpu'
        ]
      });

      // 브라우저 컨텍스트 생성
      this.context = await this.browser.newContext({
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        viewport: { width: 1280, height: 720 },
        bypassCSP: true,
        ignoreHTTPSErrors: true,
        extraHTTPHeaders: {
          'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8'
        }
      });

      // 새 페이지 생성
      this.page = await this.context.newPage();

      // 자동화 탐지 방지
      await this.page.addInitScript(() => {
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
      });

      // 로그인 페이지로 이동
      await this.page.goto(this.LOGIN_URL, { waitUntil: 'domcontentloaded' });
      console.log('네이버 로그인 페이지 로드 완료');

    } catch (error) {
      await this.cleanup();
      throw new Error(`Playwright 초기화 실패: ${error}`);
    }
  }

  /**
   * 리소스 정리
   */
  async cleanup(): Promise<void> {
    try {
      if (this.page) {
        await this.page.close();
        this.page = null;
      }
      if (this.context) {
        await this.context.close();
        this.context = null;
      }
      if (this.browser) {
        await this.browser.close();
        this.browser = null;
      }
      this.isLoggedIn = false;
      this.twoFactorAuthDetected = false;
      console.log('브라우저 리소스 정리 완료');
    } catch (error) {
      console.error('브라우저 정리 중 오류:', error);
    }
  }

  /**
   * 네이버 로그인 수행
   */
  async loginWithCredentials(credentials: NaverCredentials): Promise<LoginStatus> {
    if (!this.page) {
      throw new Error('페이지가 초기화되지 않았습니다');
    }

    try {
      console.log(`네이버 로그인 시작: ${credentials.username}`);

      // 로그인 페이지에 있는지 확인
      const currentUrl = this.page.url();
      if (!currentUrl.includes('nid.naver.com/nidlogin.login')) {
        await this.page.goto(this.LOGIN_URL, { waitUntil: 'domcontentloaded' });
        await this.page.waitForTimeout(2000);
      }

      // 아이디 입력란 대기 및 입력
      console.log('아이디 입력 중...');
      const idInput = await this.page.waitForSelector('#id', { 
        state: 'visible',
        timeout: 15000 
      });

      // 아이디 입력란 클릭 및 기존 내용 제거
      await idInput.click();
      await this.page.waitForTimeout(1000);
      await idInput.fill('');  // 기존 내용 제거
      await this.page.waitForTimeout(500);

      // 클립보드를 통한 아이디 입력 (자동화 탐지 방지)
      await this.page.evaluate((username) => {
        return navigator.clipboard.writeText(username);
      }, credentials.username);
      await this.page.waitForTimeout(1200);

      // 붙여넣기
      await idInput.click();
      await this.page.waitForTimeout(300);
      await this.page.keyboard.press('Control+v');
      await this.page.waitForTimeout(800);

      // 입력 결과 확인
      const actualId = await idInput.inputValue();
      if (actualId === credentials.username) {
        console.log(`✅ 아이디 입력 성공: ${credentials.username}`);
      } else {
        console.warn(`⚠️ 아이디 입력 불일치 - 입력: '${actualId}', 예상: '${credentials.username}'`);
        throw new Error('아이디 입력 실패');
      }

      // 비밀번호 입력란 대기 및 입력
      console.log('비밀번호 입력 중...');
      const pwInput = await this.page.waitForSelector('#pw', { 
        state: 'visible',
        timeout: 15000 
      });

      // 비밀번호 입력란 클릭 및 기존 내용 제거
      await pwInput.click();
      await this.page.waitForTimeout(1000);
      await pwInput.fill('');  // 기존 내용 제거
      await this.page.waitForTimeout(500);

      // 클립보드를 통한 비밀번호 입력
      await this.page.evaluate((password) => {
        return navigator.clipboard.writeText(password);
      }, credentials.password);
      await this.page.waitForTimeout(1200);

      // 붙여넣기
      await pwInput.click();
      await this.page.waitForTimeout(300);
      await this.page.keyboard.press('Control+v');
      await this.page.waitForTimeout(800);

      // 입력 결과 확인 (길이만 확인)
      const actualPwLength = (await pwInput.inputValue()).length;
      if (actualPwLength === credentials.password.length) {
        console.log(`✅ 비밀번호 입력 성공 (길이: ${credentials.password.length})`);
      } else {
        console.warn(`⚠️ 비밀번호 입력 길이 불일치 - 입력 길이: ${actualPwLength}, 예상 길이: ${credentials.password.length}`);
        throw new Error('비밀번호 입력 실패');
      }

      // 로그인 버튼 클릭
      console.log('로그인 버튼 클릭 중...');
      await this.clickLoginButton();

      // 로그인 결과 대기
      return await this.waitForLoginResult(credentials);

    } catch (error) {
      console.error('로그인 수행 실패:', error);
      return LoginStatus.LOGIN_FAILED;
    }
  }

  /**
   * 로그인 버튼 클릭
   */
  private async clickLoginButton(): Promise<void> {
    if (!this.page) throw new Error('페이지가 초기화되지 않았습니다');

    const loginButtonSelectors = [
      '#log\\.login',
      'button[id="log.login"]',
      '.btn_login_wrap button',
      'button.btn_login',
      'button[type="submit"]'
    ];

    let clicked = false;

    // CSS 셀렉터로 시도
    for (const selector of loginButtonSelectors) {
      try {
        const button = await this.page.waitForSelector(selector, { 
          state: 'visible',
          timeout: 3000 
        });
        if (button) {
          await button.click();
          console.log(`로그인 버튼 클릭 성공 (셀렉터: ${selector})`);
          clicked = true;
          break;
        }
      } catch (error) {
        console.debug(`셀렉터 ${selector} 실패:`, error);
        continue;
      }
    }

    // CSS 셀렉터로 실패하면 JavaScript로 직접 클릭
    if (!clicked) {
      console.log('CSS 셀렉터 실패, JavaScript로 직접 클릭 시도...');
      const jsClickResult = await this.page.evaluate(() => {
        const loginBtn = document.getElementById('log.login') || 
                         document.querySelector('button.btn_login') ||
                         document.querySelector('.btn_login_wrap button') ||
                         document.querySelector('button[type="submit"]');
        if (loginBtn) {
          (loginBtn as HTMLElement).click();
          return true;
        }
        return false;
      });

      if (jsClickResult) {
        console.log('JavaScript로 로그인 버튼 클릭 성공');
      } else {
        throw new Error('로그인 버튼을 찾을 수 없습니다');
      }
    }
  }

  /**
   * 로그인 결과 대기 및 확인
   */
  private async waitForLoginResult(credentials: NaverCredentials, timeout = 90000): Promise<LoginStatus> {
    if (!this.page) throw new Error('페이지가 초기화되지 않았습니다');

    console.log('로그인 결과 대기 시작...');
    const startTime = Date.now();
    let deviceRegistrationAttempted = false;

    while ((Date.now() - startTime) < timeout) {
      try {
        const currentUrl = this.page.url();
        console.log(`🔍 현재 URL: ${currentUrl}`);

        // 1. 기기 등록 페이지 확인
        if (currentUrl.includes('deviceConfirm') && !deviceRegistrationAttempted) {
          console.log('🆔 새로운 기기 등록 페이지 감지!');
          deviceRegistrationAttempted = true;

          try {
            await this.handleDeviceRegistration();
          } catch (error) {
            console.error('기기 등록 처리 실패:', error);
            console.log('💡 수동으로 등록 또는 등록안함 버튼을 클릭해주세요...');
          }
        }
        // 2. 로그인 성공 체크
        else if (currentUrl.includes('section.blog.naver.com/BlogHome.naver') ||
                 currentUrl === this.NAVER_HOME_URL ||
                 currentUrl === this.NAVER_HOME_URL + '/') {
          console.log(`✅ 네이버 로그인 성공! 최종 페이지: ${currentUrl}`);
          this.isLoggedIn = true;
          this.username = credentials.username;
          return LoginStatus.LOGGED_IN;
        }
        // 3. 2차 인증 감지
        else if (currentUrl.includes('auth') || currentUrl.includes('otp') || currentUrl.includes('verify')) {
          if (!this.twoFactorAuthDetected) {
            console.log('🔐 2차 인증 페이지 감지!');
            console.log('📱 2차 인증을 완료해 주세요. 완료될 때까지 대기합니다...');
            this.twoFactorAuthDetected = true;
          }
          
          // 10초마다 메시지 출력
          if (Math.floor((Date.now() - startTime) / 1000) % 10 === 0) {
            console.log(`⏳ 2차 인증 대기 중... (${Math.floor((Date.now() - startTime) / 1000)}초 경과)`);
          }
        }
        // 4. 로그인 실패 체크
        else if (currentUrl === this.LOGIN_URL) {
          if ((Date.now() - startTime) > 10000) { // 10초 이상
            try {
              const errorElement = await this.page.$('.error_message, .alert_area');
              if (errorElement && await errorElement.isVisible()) {
                const errorText = await errorElement.textContent();
                console.error(`❌ 로그인 실패: ${errorText}`);
                return LoginStatus.LOGIN_FAILED;
              }
            } catch (error) {
              // 에러 요소 찾기 실패는 무시
            }
          }
        }

        // 2초 대기
        await this.page.waitForTimeout(2000);

      } catch (error) {
        console.error('URL 확인 중 오류:', error);
        await this.page.waitForTimeout(2000);
      }
    }

    console.error('⏰ 로그인 대기 시간 초과');
    return LoginStatus.LOGIN_FAILED;
  }

  /**
   * 기기 등록 페이지 처리
   */
  private async handleDeviceRegistration(): Promise<void> {
    if (!this.page) throw new Error('페이지가 초기화되지 않았습니다');

    console.log('등록안함 버튼 찾는 중...');

    const skipButtonSelectors = [
      'a:has-text("등록안함")',
      'button:has-text("등록안함")',
      '#new\\.dontsave',
      '[id="new.dontsave"]',
      'a[id="new.dontsave"]',
      '.btn_cancel a',
      '.btn_cancel a.btn'
    ];

    let skipButton = null;
    let usedSelector = '';

    // 각 셀렉터 시도
    for (const selector of skipButtonSelectors) {
      try {
        console.log(`등록안함 버튼 찾기 시도: ${selector}`);
        skipButton = await this.page.waitForSelector(selector, { 
          state: 'visible',
          timeout: 3000 
        });
        if (skipButton) {
          usedSelector = selector;
          console.log(`✅ 버튼 발견! 셀렉터: ${usedSelector}`);
          break;
        }
      } catch (error) {
        console.debug(`셀렉터 ${selector} 실패:`, error);
        continue;
      }
    }

    if (!skipButton) {
      // 페이지 내용 확인
      const pageContent = await this.page.textContent('body');
      if (pageContent?.includes('등록안함')) {
        console.warn('페이지에 "등록안함" 텍스트는 있지만 버튼을 찾을 수 없습니다');
      }
      throw new Error('등록안함 버튼을 찾을 수 없습니다');
    }

    console.log(`🎯 등록안함 버튼 클릭 시작... (사용된 셀렉터: ${usedSelector})`);

    // 버튼을 화면에 보이도록 스크롤
    await skipButton.scrollIntoViewIfNeeded();
    await this.page.waitForTimeout(1000);

    // 클릭 시도
    let clickSuccess = false;
    try {
      console.log('🖱️ 버튼 클릭 시도 중...');
      await skipButton.click();
      console.log('✅ 버튼 클릭 완료');
      clickSuccess = true;
    } catch (error) {
      console.error('버튼 클릭 실패:', error);
      throw error;
    }

    if (clickSuccess) {
      console.log('🎉 등록안함 버튼 클릭 완료!');
      console.log('⏳ 2초 대기 후 URL 변경 확인...');
      await this.page.waitForTimeout(2000);

      const newUrl = this.page.url();
      console.log(`🔗 클릭 후 URL: ${newUrl}`);

      if (!newUrl.includes('deviceConfirm')) {
        console.log('✅ 기기 등록 처리 완료! 성공적으로 페이지 이동');
      } else {
        console.warn('⚠️ 아직 deviceConfirm 페이지에 있음');
        // 추가 대기
        await this.page.waitForTimeout(3000);
        const finalUrl = this.page.url();
        console.log(`🔗 재확인 URL: ${finalUrl}`);
        
        if (!finalUrl.includes('deviceConfirm')) {
          console.log('✅ 지연 후 페이지 이동 확인됨');
        } else {
          console.error('❌ 클릭 후에도 여전히 deviceConfirm 페이지에 있음');
          console.error('💡 수동 클릭이 필요할 수 있습니다');
        }
      }
    }
  }

  /**
   * 로그인 상태 확인
   */
  async checkLoginStatus(): Promise<boolean> {
    if (!this.page) return false;

    try {
      const currentUrl = this.page.url();
      
      // 로그인된 상태의 URL 패턴 확인
      const loggedInPatterns = [
        'section.blog.naver.com',
        'www.naver.com'
      ];

      return loggedInPatterns.some(pattern => currentUrl.includes(pattern)) && this.isLoggedIn;
    } catch (error) {
      console.error('로그인 상태 확인 실패:', error);
      return false;
    }
  }

  /**
   * 네이버 블로그 홈으로 이동
   */
  async navigateToBlogHome(): Promise<void> {
    if (!this.page) throw new Error('페이지가 초기화되지 않았습니다');

    try {
      await this.page.goto(this.BLOG_HOME_URL, { waitUntil: 'domcontentloaded' });
      console.log('네이버 블로그 홈으로 이동 완료');
    } catch (error) {
      console.error('블로그 홈 이동 실패:', error);
      throw error;
    }
  }

  /**
   * 현재 로그인된 사용자명 반환
   */
  getLoggedInUsername(): string | null {
    return this.username;
  }

  /**
   * 페이지 객체 반환 (추가 작업용)
   */
  getPage(): Page | null {
    return this.page;
  }
}