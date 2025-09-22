/**
 * 네이버 블로그 플레이라이트 기능 독립 테스트
 * Step1~3 거치지 않고 바로 테스트 가능
 */

const { chromium } = require('playwright');

// 테스트용 Step3 데이터 (민생지원금 글)
const testData = {
  selectedTitle: "민생지원금 2차 놓치면 손해! 지금 바로 신청하세요 (신청 방법 포함)",
  username: "wogud925",  // 여기에 실제 네이버 아이디 입력
  password: "qkrekfwp12",   // 여기에 실제 비밀번호 입력
  content: `<p class="se-text-paragraph se-text-paragraph-align-left" style="line-height: 1.8;"><span class="se-ff-nanumgothic se-fs24" style="color: rgb(0, 0, 0); font-weight: bold;">민생지원금 2차 놓치면 손해! 지금 바로 신청하세요</span></p>

<p class="se-text-paragraph se-text-paragraph-align-left" style="line-height: 1.8;"><span class="se-ff-nanumgothic se-fs19" style="color: rgb(0, 0, 0); font-weight: bold;">📢 핵심 답변 먼저 확인하세요!</span></p>

<p class="se-text-paragraph se-text-paragraph-align-left" style="line-height: 1.8;"><span class="se-ff-nanumgothic se-fs15" style="color: rgb(0, 0, 0);">민생지원금 2차는 2024년 12월 31일까지 신청 가능하며, 소득 하위 90% 가구에게 1인당 13만원이 지급됩니다. 건강보험료 기준으로 빠르게 자격 확인이 가능하고, 카드사 앱이나 지자체 앱에서 간단히 신청할 수 있습니다.</span></p>

<p class="se-text-paragraph se-text-paragraph-align-left" style="line-height: 1.8;"><span class="se-ff-nanumgothic se-fs16" style="color: rgb(0, 0, 0); font-weight: bold;">지금 바로 신청하지 않으면 혜택을 받을 수 없으니 서둘러 확인해보세요!</span></p>

<p class="se-text-paragraph se-text-paragraph-align-left" style="line-height: 1.8;"><span class="se-ff-nanumgothic se-fs15" style="color: rgb(0, 0, 0);">&nbsp;</span></p>

<p class="se-text-paragraph se-text-paragraph-align-left" style="line-height: 1.8;"><span class="se-ff-nanumgothic se-fs19" style="color: rgb(0, 0, 0); font-weight: bold;">✅ 나도 받을 수 있을까? 지급 대상 자격 체크리스트</span></p>

<p class="se-text-paragraph se-text-paragraph-align-left" style="line-height: 1.8;"><span class="se-ff-nanumgothic se-fs16" style="color: rgb(0, 0, 0); font-weight: bold;">소득 기준 (다음 중 하나라도 해당되면 신청 가능)</span></p>

<p class="se-text-paragraph se-text-paragraph-align-left" style="line-height: 1.8;"><span class="se-ff-nanumgothic se-fs15" style="color: rgb(0, 0, 0);">✓ 건강보험료 본인부담금이 기준 이하인 가구</span></p>

<p class="se-text-paragraph se-text-paragraph-align-left" style="line-height: 1.8;"><span class="se-ff-nanumgothic se-fs15" style="color: rgb(0, 0, 0);">- 1인 가구: 월 97,000원 이하</span></p>

<p class="se-text-paragraph se-text-paragraph-align-left" style="line-height: 1.8;"><span class="se-ff-nanumgothic se-fs15" style="color: rgb(0, 0, 0);">- 2인 가구: 월 162,000원 이하</span></p>

<p class="se-text-paragraph se-text-paragraph-align-left" style="line-height: 1.8;"><span class="se-ff-nanumgothic se-fs15" style="color: rgb(0, 0, 0);">- 3인 가구: 월 209,000원 이하</span></p>

<p class="se-text-paragraph se-text-paragraph-align-left" style="line-height: 1.8;"><span class="se-ff-nanumgothic se-fs15" style="color: rgb(0, 0, 0);">- 4인 가구: 월 255,000원 이하</span></p>`,
  tags: ['민생지원금2차', '민생지원금신청', '소비쿠폰', '정부지원금', '생활지원금']
};

class NaverBlogTester {
  constructor() {
    this.browser = null;
    this.context = null;
    this.page = null;
  }

  async initialize() {
    console.log('🚀 브라우저 초기화 중...');
    
    this.browser = await chromium.launch({
      headless: false,  // 브라우저 창 보이게
      args: [
        '--disable-blink-features=AutomationControlled',
        '--disable-dev-shm-usage',
        '--no-sandbox',
        '--disable-notifications',
        '--disable-gpu'
      ]
    });

    this.context = await this.browser.newContext({
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      viewport: { width: 1280, height: 720 },
      bypassCSP: true,
      ignoreHTTPSErrors: true,
      extraHTTPHeaders: {
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8'
      }
    });

    this.page = await this.context.newPage();

    // 자동화 탐지 방지
    await this.page.addInitScript(() => {
      Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    });

    console.log('✅ 브라우저 초기화 완료');
  }

  async performNaverLogin() {
    console.log('📝 네이버 로그인 시작...');
    
    // 로그인 페이지로 이동
    await this.page.goto('https://nid.naver.com/nidlogin.login', { waitUntil: 'domcontentloaded' });
    await this.page.waitForTimeout(2000);

    // 아이디 입력
    console.log('👤 아이디 입력 중...');
    await this.page.fill('#id', testData.username);
    await this.page.waitForTimeout(500);

    // 비밀번호 입력
    console.log('🔒 비밀번호 입력 중...');
    await this.page.fill('#pw', testData.password);
    await this.page.waitForTimeout(500);

    // 로그인 버튼 클릭
    console.log('🖱️ 로그인 버튼 클릭...');
    await this.page.click('#log\\.login');

    // 로그인 결과 대기
    console.log('⏳ 로그인 결과 대기 중...');
    return await this.waitForLoginResult();
  }

  async waitForLoginResult(timeout = 90000) {
    const startTime = Date.now();
    let deviceRegistrationAttempted = false;

    while ((Date.now() - startTime) < timeout) {
      await this.page.waitForTimeout(2000);
      
      const currentUrl = this.page.url();
      console.log(`🔍 현재 URL: ${currentUrl}`);

      // 기기 등록 페이지 처리
      if (currentUrl.includes('deviceConfirm') && !deviceRegistrationAttempted) {
        console.log('🆔 기기 등록 페이지 감지, 건너뛰기 시도...');
        deviceRegistrationAttempted = true;
        
        try {
          await this.page.click('#new\\.dontsave', { timeout: 5000 });
          console.log('✅ 기기 등록 건너뛰기 완료');
        } catch (error) {
          console.warn('⚠️ 기기 등록 건너뛰기 실패, 수동 처리 필요');
          return 'device_registration';
        }
        continue;
      }
      
      // 로그인 성공 체크
      if (currentUrl === 'https://www.naver.com' || currentUrl === 'https://www.naver.com/') {
        console.log('✅ 네이버 로그인 성공!');
        return 'success';
      }
      
      // 2차 인증 감지
      if (currentUrl.includes('auth') || currentUrl.includes('otp') || currentUrl.includes('verify')) {
        console.log('🔐 2차 인증 페이지 감지');
        return 'two_factor';
      }
      
      // 로그인 페이지에 계속 있으면 실패
      if (currentUrl.includes('nid.naver.com/nidlogin.login') && (Date.now() - startTime) > 10000) {
        console.log('❌ 로그인 실패 (로그인 페이지에 계속 있음)');
        return 'failed';
      }
    }

    console.log('⏰ 로그인 대기 시간 초과');
    return 'timeout';
  }

  async navigateToBlogWrite() {
    console.log('📝 블로그 글쓰기 페이지로 이동...');
    
    const writeUrl = `https://blog.naver.com/${testData.username}?Redirect=Write&`;
    await this.page.goto(writeUrl, { waitUntil: 'domcontentloaded' });
    await this.page.waitForTimeout(3000);

    console.log('✅ 블로그 페이지 이동 완료');
  }

  async handlePopups() {
    console.log('🔧 팝업 처리 시작...');

    // 작성 중인 글 팝업 처리
    await this.handleDraftPopup();
    
    // 도움말 패널 처리  
    await this.handleHelpPanel();
  }

  async handleDraftPopup() {
    console.log('📄 작성 중인 글 팝업 확인...');
    
    const cancelSelectors = [
      '.se-popup-button-cancel',
      'button.se-popup-button-cancel'
    ];

    for (const selector of cancelSelectors) {
      try {
        // 모든 프레임에서 시도
        const frames = await this.page.frames();
        for (const frame of frames) {
          try {
            const element = await frame.waitForSelector(selector, { state: 'visible', timeout: 3000 });
            if (element) {
              await element.click();
              console.log('✅ 작성 중인 글 팝업 취소 완료');
              await this.page.waitForTimeout(1000);
              return;
            }
          } catch (error) {
            continue;
          }
        }
      } catch (error) {
        continue;
      }
    }
    
    console.log('ℹ️ 작성 중인 글 팝업 없음 또는 처리 완료');
  }

  async handleHelpPanel() {
    console.log('❓ 도움말 패널 확인...');
    
    const helpCloseSelectors = [
      '.se-help-panel-close-button',
      'button.se-help-panel-close-button'
    ];

    for (const selector of helpCloseSelectors) {
      try {
        // 모든 프레임에서 시도
        const frames = await this.page.frames();
        for (const frame of frames) {
          try {
            const element = await frame.waitForSelector(selector, { state: 'visible', timeout: 3000 });
            if (element) {
              await element.click();
              console.log('✅ 도움말 패널 닫기 완료');
              await this.page.waitForTimeout(1000);
              return;
            }
          } catch (error) {
            continue;
          }
        }
      } catch (error) {
        continue;
      }
    }
    
    console.log('ℹ️ 도움말 패널 없음 또는 처리 완료');
  }

  async inputTitle() {
    console.log('📝 제목 입력 시작...');
    
    const titleSelectors = [
      '.se-section-documentTitle .se-module-text p',
      '.se-section-documentTitle .se-text-paragraph',
      '.se-title-text p'
    ];

    for (const selector of titleSelectors) {
      try {
        // 모든 프레임에서 시도
        const frames = await this.page.frames();
        for (const frame of frames) {
          try {
            const element = await frame.waitForSelector(selector, { state: 'visible', timeout: 5000 });
            if (element) {
              console.log(`📌 제목 섹션 발견: ${selector}`);
              
              // 클릭하여 활성화
              await element.click();
              await this.page.waitForTimeout(500);
              
              // 제목 입력 스크립트 실행
              const success = await frame.evaluate((title) => {
                try {
                  const titleElements = [
                    document.querySelector('.se-section-documentTitle span.__se-node'),
                    document.querySelector('.se-title-text span.__se-node'),
                    document.activeElement
                  ];
                  
                  const titleElement = titleElements.find(el => el && el.tagName);
                  
                  if (titleElement) {
                    // 기존 내용 지우고 새 제목 입력
                    titleElement.textContent = title;
                    titleElement.innerText = title;
                    
                    // 이벤트 발생
                    titleElement.focus();
                    const events = ['input', 'change', 'keyup'];
                    events.forEach(eventType => {
                      const event = new Event(eventType, { bubbles: true });
                      titleElement.dispatchEvent(event);
                    });
                    
                    return true;
                  }
                  return false;
                } catch (error) {
                  console.error('제목 입력 오류:', error);
                  return false;
                }
              }, testData.selectedTitle);
              
              if (success) {
                console.log('✅ 제목 입력 완료!');
                return;
              }
            }
          } catch (error) {
            continue;
          }
        }
      } catch (error) {
        continue;
      }
    }
    
    console.warn('⚠️ 제목 입력 실패');
  }

  // Step3 글씨 크기 매핑 (4가지만 사용)
  mapStep3FontSize(fontSize) {
    const sizeMap = {
      '24px': { size: '24', bold: true },   // 대제목
      '19px': { size: '19', bold: true },   // 소제목  
      '16px': { size: '16', bold: true },   // 강조
      '15px': { size: '15', bold: false }   // 일반
    };
    return sizeMap[fontSize] || { size: '15', bold: false }; // 기본값
  }

  async changeFontSize(fontSize) {
    console.log(`📏 글씨 크기 변경: ${fontSize}`);
    
    try {
      const frames = await this.page.frames();
      for (const frame of frames) {
        try {
          // 글씨 크기 버튼 클릭
          const fontSizeButton = await frame.waitForSelector('.se-font-size-code-toolbar-button', { 
            state: 'visible', 
            timeout: 3000 
          });
          
          if (fontSizeButton) {
            await fontSizeButton.click();
            await this.page.waitForTimeout(500);
            
            // 특정 크기 선택
            const sizeSelector = `.se-toolbar-option-font-size-code-fs${fontSize}-button`;
            const sizeOption = await frame.waitForSelector(sizeSelector, { 
              state: 'visible', 
              timeout: 3000 
            });
            
            if (sizeOption) {
              await sizeOption.click();
              console.log(`✅ 글씨 크기 ${fontSize} 적용 완료`);
              await this.page.waitForTimeout(300);
              return true;
            }
          }
        } catch (error) {
          continue;
        }
      }
    } catch (error) {
      console.warn(`⚠️ 글씨 크기 변경 실패: ${error.message}`);
    }
    
    return false;
  }

  async applyBold() {
    console.log(`🔥 굵게 처리 적용`);
    
    try {
      const frames = await this.page.frames();
      for (const frame of frames) {
        try {
          // 굵게 버튼 찾기 (네이버 블로그 정확한 셀렉터)
          const boldSelectors = [
            '.se-bold-toolbar-button',
            'button[data-name="bold"]',
            'button[data-log="prt.bold"]',
            '.se-property-toolbar-toggle-button[data-name="bold"]'
          ];
          
          for (const selector of boldSelectors) {
            try {
              const boldButton = await frame.waitForSelector(selector, { 
                state: 'visible', 
                timeout: 2000 
              });
              
              if (boldButton) {
                await boldButton.click();
                console.log(`✅ 굵게 처리 적용 완료`);
                await this.page.waitForTimeout(300);
                return true;
              }
            } catch (error) {
              continue;
            }
          }
        } catch (error) {
          continue;
        }
      }
    } catch (error) {
      console.warn(`⚠️ 굵게 처리 실패: ${error.message}`);
    }
    
    return false;
  }

  async applyFormatting(formatInfo) {
    console.log(`🎨 서식 적용: 크기 ${formatInfo.size}${formatInfo.bold ? ' + 굵게' : ''}`);
    
    // 1. 글씨 크기 변경
    await this.changeFontSize(formatInfo.size);
    
    // 2. 굵게 처리 (필요한 경우)
    if (formatInfo.bold) {
      await this.applyBold();
    }
  }

  async inputContentWithFormatting() {
    console.log('📝 본문 입력 및 서식 적용 시작...');
    
    const contentSelectors = [
      '.se-content',
      '.se-module-text', 
      '.se-text-paragraph',
      '[contenteditable="true"]',
      '.se-component-content'
    ];

    // HTML 파싱해서 서식 정보 추출
    const contentParts = this.parseContentWithStyles(testData.content);
    
    for (const selector of contentSelectors) {
      try {
        const frames = await this.page.frames();
        for (const frame of frames) {
          try {
            const element = await frame.waitForSelector(selector, { state: 'visible', timeout: 5000 });
            if (element) {
              console.log(`📌 본문 섹션 발견: ${selector}`);
              
              // 클릭하여 활성화
              await element.click();
              await this.page.waitForTimeout(500);
              
              // 서식이 적용된 내용을 순차적으로 타이핑
              for (const part of contentParts) {
                console.log(`📝 입력할 텍스트: "${part.text.substring(0, 30)}..." (크기: ${part.fontSize})`);
                
                // 1. 먼저 서식 설정 (글씨 크기 + 굵게)
                if (part.fontSize) {
                  const formatInfo = this.mapStep3FontSize(part.fontSize);
                  await this.applyFormatting(formatInfo);
                  await this.page.waitForTimeout(300);
                }
                
                // 2. 텍스트를 한 글자씩 타이핑
                for (const char of part.text) {
                  await frame.evaluate((character) => {
                    const contentElement = document.querySelector('[contenteditable="true"]') || 
                                         document.querySelector('.se-content') || 
                                         document.activeElement;
                    if (contentElement) {
                      // 커서 위치에 글자 삽입
                      document.execCommand('insertText', false, character);
                    }
                  }, char);
                  
                  // 타이핑 속도 조절 (너무 빠르면 네이버에서 감지할 수 있음)
                  await this.page.waitForTimeout(50);
                }
                
                await this.page.waitForTimeout(200);
              }
              
              console.log('✅ 서식이 적용된 본문 입력 완료!');
              return;
            }
          } catch (error) {
            continue;
          }
        }
      } catch (error) {
        continue;
      }
    }
    
    console.warn('⚠️ 본문 입력 실패');
  }

  // Step3에서 편집된 HTML 내용을 파싱해서 실제 글씨 크기 추출
  parseContentWithStyles(htmlContent) {
    const parts = [];
    
    // HTML을 DOM으로 파싱
    const parser = new DOMParser();
    const doc = parser.parseFromString(htmlContent, 'text/html');
    
    // 모든 텍스트 노드와 요소를 순회
    const walker = document.createTreeWalker(
      doc.body,
      NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT,
      null,
      false
    );
    
    let node;
    while (node = walker.nextNode()) {
      if (node.nodeType === Node.TEXT_NODE) {
        const text = node.textContent.trim();
        if (text) {
          // 부모 요소에서 글씨 크기 찾기
          let fontSize = '15px'; // 기본값
          let element = node.parentElement;
          
          while (element) {
            const classList = element.classList;
            if (classList.contains('se-fs24')) {
              fontSize = '24px';
              break;
            } else if (classList.contains('se-fs19')) {
              fontSize = '19px';
              break;
            } else if (classList.contains('se-fs16')) {
              fontSize = '16px';
              break;
            } else if (classList.contains('se-fs15')) {
              fontSize = '15px';
              break;
            }
            element = element.parentElement;
          }
          
          parts.push({ text: text + ' ', fontSize });
        }
      } else if (node.nodeName === 'BR') {
        parts.push({ text: '\n', fontSize: '15px' });
      }
    }
    
    return parts;
  }

  async inputTags() {
    console.log('🏷️ 태그 입력 시작...');
    
    const tagSelectors = [
      '.se-tag-input',
      'input[placeholder*="태그"]',
      '.tag-input',
      '.se-tag-field input'
    ];

    for (const selector of tagSelectors) {
      try {
        // 모든 프레임에서 시도
        const frames = await this.page.frames();
        for (const frame of frames) {
          try {
            const element = await frame.waitForSelector(selector, { state: 'visible', timeout: 5000 });
            if (element) {
              console.log(`📌 태그 입력창 발견: ${selector}`);
              
              // 태그 입력
              for (const tag of testData.tags) {
                await element.click();
                await this.page.waitForTimeout(200);
                await element.type(tag);
                await this.page.waitForTimeout(200);
                await this.page.keyboard.press('Enter');
                await this.page.waitForTimeout(500);
                console.log(`✅ 태그 입력: ${tag}`);
              }
              
              console.log('✅ 모든 태그 입력 완료!');
              return;
            }
          } catch (error) {
            continue;
          }
        }
      } catch (error) {
        continue;
      }
    }
    
    console.warn('⚠️ 태그 입력 실패 (태그 입력창을 찾을 수 없음)');
  }

  async cleanup() {
    console.log('🧹 브라우저 정리 중...');
    if (this.browser) {
      await this.browser.close();
    }
    console.log('✅ 정리 완료');
  }

  async runFullTest() {
    try {
      await this.initialize();
      
      const loginResult = await this.performNaverLogin();
      
      if (loginResult === 'success') {
        await this.navigateToBlogWrite();
        await this.handlePopups();
        await this.inputTitle();
        
        console.log('\n⏳ 잠시 대기 후 본문 입력 시작...');
        await this.page.waitForTimeout(2000);
        
        await this.inputContentWithFormatting();
        
        console.log('\n⏳ 잠시 대기 후 태그 입력 시작...');
        await this.page.waitForTimeout(1000);
        
        await this.inputTags();
        
        console.log('\n🎉 모든 테스트 완료! 브라우저에서 확인해보세요.');
        console.log('📝 제목: ' + testData.selectedTitle);
        console.log('📄 본문: ' + testData.content.substring(0, 100) + '...');
        console.log('🏷️ 태그: ' + testData.tags.join(', '));
        console.log('💡 브라우저를 수동으로 닫거나 Ctrl+C로 스크립트를 종료하세요.');
        
        // 브라우저 열린 상태로 유지 (수동 종료 대기)
        process.stdin.resume();
        
      } else {
        console.log(`❌ 로그인 실패: ${loginResult}`);
        await this.cleanup();
      }
      
    } catch (error) {
      console.error('💥 테스트 실행 중 오류:', error);
      await this.cleanup();
    }
  }
}

// 실행
console.log('🧪 네이버 블로그 플레이라이트 테스트 시작');
console.log('📝 테스트할 글: ' + testData.selectedTitle);
console.log('🏷️ 테스트할 태그: ' + testData.tags.join(', '));
console.log('📄 본문 길이: ' + testData.content.length + '자');
console.log('👤 계정: ' + testData.username);
console.log('⚠️  계정 정보가 정확한지 확인해주세요!\n');

const tester = new NaverBlogTester();
tester.runFullTest();

// Ctrl+C 처리
process.on('SIGINT', async () => {
  console.log('\n🛑 테스트 중단 중...');
  await tester.cleanup();
  process.exit(0);
});