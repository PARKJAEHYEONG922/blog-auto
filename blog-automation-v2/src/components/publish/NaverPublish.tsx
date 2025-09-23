import React, { useState, useRef, useEffect } from 'react';
import { PublishComponentProps, PublishStatus, PublishResult, IPublishComponent } from './PublishInterface';
// import { PlaywrightNaverHelper, NaverCredentials, LoginStatus } from './PlaywrightNaverHelper';
// import { NaverBlogPublisher, BlogPostData, PublishOptions, PostStatus } from './NaverBlogPublisher';

// 네이버 자격 증명 타입
interface NaverCredentials {
  username: string;
  password: string;
}

const NaverPublish: React.FC<PublishComponentProps> = ({ 
  data, 
  editedContent, 
  imageUrls, 
  onComplete,
  copyToClipboard 
}) => {
  
  // 네이버 로그인 상태
  const [naverCredentials, setNaverCredentials] = useState<NaverCredentials>({
    username: '',
    password: ''
  });
  
  const [publishStatus, setPublishStatus] = useState<PublishStatus>({
    isPublishing: false,
    isLoggedIn: false,
    error: '',
    success: false
  });

  // 네이버 로그아웃 및 브라우저 정리 함수
  const logoutFromNaver = async () => {
    try {
      // 브라우저 정리
      await window.electronAPI.playwrightCleanup();
      console.log('브라우저 정리 완료');
    } catch (error) {
      console.error('브라우저 정리 실패:', error);
    }
    
    setPublishStatus(prev => ({
      ...prev,
      isLoggedIn: false,
      error: '',
      success: false
    }));
    setNaverCredentials({ username: '', password: '' });
  };

  // 임시로 Playwright 대신 더미 구현
  const naverHelperRef = useRef<any>(null);

  // 컴포넌트 언마운트 시 브라우저 정리
  useEffect(() => {
    return () => {
      window.electronAPI.playwrightCleanup().catch(console.error);
    };
  }, []);

  // 네이버 로그인 헬퍼 함수들
  const performNaverLogin = async (credentials: NaverCredentials): Promise<'success' | 'two_factor' | 'device_registration' | 'failed'> => {
    // 네이버 로그인 페이지로 이동
    const navigateResult = await window.electronAPI.playwrightNavigate('https://nid.naver.com/nidlogin.login');
    if (!navigateResult.success) {
      throw new Error('로그인 페이지 이동 실패');
    }

    await window.electronAPI.playwrightWaitTimeout(2000);

    // 아이디 입력
    console.log('아이디 입력 중...');
    const idFillResult = await window.electronAPI.playwrightFill('#id', credentials.username);
    if (!idFillResult.success) {
      throw new Error('아이디 입력 실패');
    }

    await window.electronAPI.playwrightWaitTimeout(500);

    // 비밀번호 입력
    console.log('비밀번호 입력 중...');
    const pwFillResult = await window.electronAPI.playwrightFill('#pw', credentials.password);
    if (!pwFillResult.success) {
      throw new Error('비밀번호 입력 실패');
    }

    await window.electronAPI.playwrightWaitTimeout(500);

    // 로그인 버튼 클릭
    console.log('로그인 버튼 클릭 중...');
    const loginBtnResult = await window.electronAPI.playwrightClick('#log\\.login');
    if (!loginBtnResult.success) {
      // 다른 셀렉터들 시도
      const altSelectors = ['button[id="log.login"]', '.btn_login_wrap button', 'button.btn_login'];
      let clicked = false;
      
      for (const selector of altSelectors) {
        const result = await window.electronAPI.playwrightClick(selector);
        if (result.success) {
          clicked = true;
          break;
        }
      }
      
      if (!clicked) {
        throw new Error('로그인 버튼을 찾을 수 없습니다');
      }
    }

    // 로그인 결과 대기 (최대 90초)
    const startTime = Date.now();
    const timeout = 90000;
    let deviceRegistrationAttempted = false;

    while ((Date.now() - startTime) < timeout) {
      await window.electronAPI.playwrightWaitTimeout(2000);
      
      const urlResult = await window.electronAPI.playwrightGetUrl();
      if (!urlResult.success || !urlResult.url) continue;
      
      const currentUrl = urlResult.url;
      console.log(`🔍 현재 URL: ${currentUrl}`);

      // 기기 등록 페이지 확인
      if (currentUrl.includes('deviceConfirm') && !deviceRegistrationAttempted) {
        console.log('🆔 새로운 기기 등록 페이지 감지!');
        deviceRegistrationAttempted = true;
        
        // 등록안함 버튼 클릭 시도
        const skipSelectors = ['#new\\.dontsave', '[id="new.dontsave"]', 'a[id="new.dontsave"]'];
        let skipped = false;
        
        for (const selector of skipSelectors) {
          const result = await window.electronAPI.playwrightClick(selector);
          if (result.success) {
            console.log('✅ 기기 등록 건너뛰기 완료');
            skipped = true;
            break;
          }
        }
        
        if (!skipped) {
          return 'device_registration';
        }
        continue;
      }
      
      // 로그인 성공 체크 (네이버 홈페이지)
      if (currentUrl === 'https://www.naver.com' || currentUrl === 'https://www.naver.com/') {
        console.log(`✅ 네이버 로그인 성공!`);
        return 'success';
      }
      
      // 2차 인증 감지
      if (currentUrl.includes('auth') || currentUrl.includes('otp') || currentUrl.includes('verify')) {
        console.log('🔐 2차 인증 페이지 감지!');
        return 'two_factor';
      }
      
      // 로그인 페이지에 계속 있으면 실패
      if (currentUrl.includes('nid.naver.com/nidlogin.login') && (Date.now() - startTime) > 10000) {
        return 'failed';
      }
    }

    return 'failed';
  };

  const navigateToNaverBlogWrite = async (username: string): Promise<boolean> => {
    const writeUrl = `https://blog.naver.com/${username}?Redirect=Write&`;
    const navigateResult = await window.electronAPI.playwrightNavigate(writeUrl);
    
    if (!navigateResult.success) {
      return false;
    }

    // 페이지 로드 대기 (iframe 로딩 충분히 대기)
    await window.electronAPI.playwrightWaitTimeout(5000);
    
    // iframe이 완전히 로드될 때까지 대기
    const iframeLoadResult = await window.electronAPI.playwrightEvaluateInFrames(`
      (function() {
        return { 
          success: true, 
          loaded: document.readyState === 'complete',
          hasEditor: !!document.querySelector('.se-module-text')
        };
      })()
    `);
    
    console.log('iframe 로드 상태:', iframeLoadResult?.result);
    
    if (!iframeLoadResult?.result?.hasEditor) {
      console.log('에디터 로딩 대기 중...');
      await window.electronAPI.playwrightWaitTimeout(3000);
    }

    // 작성 중인 글 팝업 처리 (더 정확한 확인)
    try {
      console.log('작성 중인 글 팝업 확인 중...');
      
      // 네이버 블로그 정확한 팝업 감지 (.se-popup-dim 확인) - mainFrame 타겟팅
      const popupCheckResult = await window.electronAPI.playwrightEvaluateInFrames(`
        (function() {
          console.log('iframe 내부에서 네이버 블로그 팝업 찾기...');
          
          // 네이버 블로그 팝업 딤 요소 확인 (가장 정확한 방법)
          const popupDim = document.querySelector('.se-popup-dim');
          const popupDimWhite = document.querySelector('.se-popup-dim-white');
          const popupDimElement = popupDim || popupDimWhite;
          
          console.log('se-popup-dim 요소:', popupDimElement);
          console.log('팝업 딤 표시 상태:', popupDimElement ? 'block' : 'none');
          
          if (popupDimElement) {
            console.log('팝업 딤 스타일:', {
              display: popupDimElement.style.display,
              visibility: popupDimElement.style.visibility,
              offsetParent: !!popupDimElement.offsetParent,
              className: popupDimElement.className
            });
          }
          
          // 팝업이 실제로 표시되어 있는지 확인
          const isPopupVisible = popupDimElement && (
            popupDimElement.offsetParent !== null || 
            popupDimElement.style.display !== 'none'
          );
          
          // 취소 버튼들 찾기
          const cancelButtons = [
            document.querySelector('.se-popup-button-cancel'),
            document.querySelector('button.se-popup-button-cancel'),
            document.querySelector('.se-popup .se-button-cancel'),
            document.querySelector('[data-name="cancel"]')
          ].filter(btn => btn && btn.offsetParent !== null);
          
          console.log('팝업 감지 결과:', {
            hasPopupDim: !!popupDimElement,
            isVisible: isPopupVisible,
            cancelButtonsFound: cancelButtons.length
          });
          
          return { 
            success: true, 
            hasPopup: isPopupVisible,
            popupDimFound: !!popupDimElement,
            cancelButtonsCount: cancelButtons.length,
            popupDimClass: popupDimElement?.className || null
          };
        })()
      `, 'PostWriteForm.naver');
      
      console.log('팝업 확인 결과:', popupCheckResult?.result);
      
      if (popupCheckResult?.result?.hasPopup) {
        console.log('📄 작성 중인 글 팝업 발견! (.se-popup-dim 확인됨)');
        console.log('팝업 딤 클래스:', popupCheckResult.result.popupDimClass);
        
        const cancelSelectors = [
          '.se-popup-button-cancel', 
          'button.se-popup-button-cancel',
          'button[data-action="cancel"]',
          '.popup-cancel',
          '.modal-cancel'
        ];
        
        let cancelSuccess = false;
        for (const selector of cancelSelectors) {
          console.log(`취소 버튼 클릭 시도: ${selector}`);
          const result = await window.electronAPI.playwrightClickInFrames(selector, 'PostWriteForm.naver');
          if (result.success) {
            console.log(`✅ 작성 중인 글 팝업 취소 완료: ${selector}`);
            await window.electronAPI.playwrightWaitTimeout(1000);
            cancelSuccess = true;
            break;
          }
        }
        
        if (!cancelSuccess) {
          console.warn('⚠️ 팝업은 발견했지만 취소 버튼을 클릭하지 못했습니다.');
        }
        
      } else {
        console.log('ℹ️ 작성 중인 글 팝업 없음');
      }
      
    } catch (error) {
      console.log('팝업 처리 중 오류 (무시):', error);
    }

    // 2. 도움말 패널 닫기 버튼 처리 (정확한 감지)
    try {
      console.log('도움말 패널 닫기 버튼 확인 중...');
      
      // 네이버 블로그 도움말 패널 정확한 감지
      const helpCheckResult = await window.electronAPI.playwrightEvaluateInFrames(`
        (function() {
          console.log('iframe 내부에서 도움말 패널 찾기...');
          
          // 다양한 도움말 패널 셀렉터 확인
          const helpSelectors = [
            '.se-help-panel',
            '.se-help-panel-close-button',
            'button.se-help-panel-close-button',
            '.se-guide-panel',
            '.se-guide-close-button',
            '[class*="help-panel"]',
            '[class*="guide-panel"]',
            '[data-name*="help"]',
            '[data-name*="guide"]'
          ];
          
          const foundHelpElements = [];
          
          for (const selector of helpSelectors) {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => {
              if (el && (el.offsetParent !== null || el.style.display !== 'none')) {
                foundHelpElements.push({
                  selector: selector,
                  tagName: el.tagName,
                  className: el.className,
                  visible: el.offsetParent !== null,
                  textContent: el.textContent?.substring(0, 30)
                });
              }
            });
          }
          
          console.log('찾은 도움말 요소들:', foundHelpElements);
          
          // 닫기 버튼 확인
          const closeButtons = [
            document.querySelector('.se-help-panel-close-button'),
            document.querySelector('button.se-help-panel-close-button'),
            document.querySelector('.se-guide-close-button'),
            document.querySelector('.se-help-panel .close'),
            document.querySelector('[data-name="help-close"]')
          ].filter(btn => btn && btn.offsetParent !== null);
          
          const hasHelp = foundHelpElements.length > 0;
          
          console.log('도움말 패널 감지 결과:', {
            hasHelp: hasHelp,
            elementsCount: foundHelpElements.length,
            closeButtonsCount: closeButtons.length
          });
          
          return { 
            success: true, 
            hasHelp: hasHelp,
            helpElements: foundHelpElements,
            closeButtonsCount: closeButtons.length
          };
        })()
      `, 'PostWriteForm.naver');
      
      console.log('도움말 패널 확인 결과:', helpCheckResult?.result);
      
      if (helpCheckResult?.result?.hasHelp) {
        console.log('❓ 도움말 패널 발견! 닫기 시도...');
        console.log('발견된 도움말 요소들:', helpCheckResult.result.helpElements);
        
        const helpCloseSelectors = [
          '.se-help-panel-close-button',
          'button.se-help-panel-close-button',
          '.se-help-panel-close-button span.se-blind',
          '.se-guide-close-button',
          '.se-help-panel .close',
          '[data-name="help-close"]',
          '.close-button'
        ];
        
        let closeSuccess = false;
        for (const selector of helpCloseSelectors) {
          console.log(`도움말 닫기 버튼 클릭 시도: ${selector}`);
          const result = await window.electronAPI.playwrightClickInFrames(selector, 'PostWriteForm.naver');
          if (result.success) {
            console.log(`✅ 도움말 패널 닫기 완료: ${selector}`);
            await window.electronAPI.playwrightWaitTimeout(1000);
            closeSuccess = true;
            break;
          }
        }
        
        if (!closeSuccess) {
          console.warn('⚠️ 도움말 패널은 발견했지만 닫기 버튼을 클릭하지 못했습니다.');
        }
        
      } else {
        console.log('ℹ️ 도움말 패널 없음');
      }
      
    } catch (error) {
      console.log('도움말 패널 처리 중 오류 (무시):', error);
    }

    // 3. 제목 입력 처리
    try {
      console.log('제목 입력 시작...');
      
      const titleSelectors = [
        '.se-title-text .se-placeholder.__se_placeholder:not(.se-placeholder-focused)',  // focused 아닌 제목 placeholder
        '.se-title-text .se-placeholder.__se_placeholder',  // 일반 제목 placeholder
        '.se-text-paragraph span.__se-node',  // 실제 제목 input 요소
        '.se-title-text .se-text-paragraph'
      ];
      
      for (const selector of titleSelectors) {
        console.log(`제목 섹션 클릭 시도: ${selector}`);
        
        // iframe에서 제목 섹션 클릭 - mainFrame 타겟팅
        let result = await window.electronAPI.playwrightClickInFrames(selector, 'PostWriteForm.naver');
        
        if (result.success) {
          console.log('✅ 제목 섹션 클릭 성공');
          await window.electronAPI.playwrightWaitTimeout(2000);  // 2초 대기
          
          // 제목 타이핑 (Step3에서 선택된 제목 사용)
          console.log(`제목 타이핑 중: "${data.selectedTitle}"`);
          console.log(`📝 선택된 제목: ${data.selectedTitle}`);
          
          // 제목을 한 글자씩 타이핑 (자연스러운 방식)
          console.log(`📝 제목 타이핑 시작: "${data.selectedTitle}"`);
          
          // 제목 요소 찾기 및 포커스
          const titleFocusResult = await window.electronAPI.playwrightEvaluateInFrames(`
            (function() {
              try {
                console.log('iframe 내부에서 제목 요소 찾기...');
                
                // 더 정확한 제목 셀렉터들
                const titleSelectors = [
                  '.se-title-text span.__se-node',
                  '.se-module-text.se-title-text span.__se-node',
                  '.se-section-documentTitle span.__se-node',
                  '.se-text-paragraph span.__se-node'
                ];
                
                let titleElement = null;
                for (const selector of titleSelectors) {
                  const elements = document.querySelectorAll(selector);
                  for (const el of elements) {
                    if (el && el.offsetParent !== null && !el.classList.contains('se-placeholder')) {
                      titleElement = el;
                      console.log('제목 요소 발견:', selector, el);
                      break;
                    }
                  }
                  if (titleElement) break;
                }
                
                if (!titleElement) {
                  return { success: false, message: '제목 입력 요소를 찾을 수 없음' };
                }
                
                // 기존 내용 완전히 제거
                titleElement.innerHTML = '';
                titleElement.textContent = '';
                
                // 포커스 및 클릭
                titleElement.focus();
                titleElement.click();
                
                return { success: true, message: '제목 요소 포커스 완료' };
              } catch (error) {
                return { success: false, message: error.message };
              }
            })()
          `, 'PostWriteForm.naver');
          
          if (titleFocusResult?.result?.success) {
            console.log('✅ 제목 요소 포커스 완료');
            await window.electronAPI.playwrightWaitTimeout(500);
            
            // 제목을 실제 Playwright 키보드 API로 타이핑
            console.log('🎹 실제 키보드로 제목 타이핑 시작...');
            const titleTypingResult = await window.electronAPI.playwrightType(data.selectedTitle, 30);
            
            if (titleTypingResult.success) {
              console.log('✅ 제목 입력 완료');
              
              // 제목 입력 후 2초 대기
              console.log('📍 2초 대기 후 본문 영역으로 이동...');
              await window.electronAPI.playwrightWaitTimeout(2000);
              
              // 제목 입력 후 바로 본문 입력으로 넘어감 (중복 클릭 제거)
              console.log('✅ 제목 입력 완료, 본문 입력 준비됨');
              await window.electronAPI.playwrightWaitTimeout(1000);
              
            } else {
              console.warn('⚠️ 제목 입력 실패:', titleTypingResult.error);
            }
          } else {
            console.warn('⚠️ 제목 요소 포커스 실패:', titleFocusResult?.result?.message);
          }
          
          await window.electronAPI.playwrightWaitTimeout(1000);
          break;
        }
      }
      
    } catch (error) {
      console.log('제목 입력 중 오류 (무시):', error);
    }

    return true;
  };

  // Step3 글씨 크기 매핑 (4가지만 사용)
  const mapStep3FontSize = (fontSize: string) => {
    const sizeMap: { [key: string]: { size: string; bold: boolean } } = {
      '24px': { size: '24', bold: true },   // 대제목
      '19px': { size: '19', bold: true },   // 소제목  
      '16px': { size: '16', bold: true },   // 강조
      '15px': { size: '15', bold: false }   // 일반
    };
    return sizeMap[fontSize] || { size: '15', bold: false }; // 기본값
  };

  // 네이버 블로그에서 글씨 크기 변경
  const changeFontSize = async (fontSize: string): Promise<boolean> => {
    console.log(`📏 글씨 크기 변경: ${fontSize}`);
    
    try {
      // 글씨 크기 버튼 클릭
      const fontSizeButtonResult = await window.electronAPI.playwrightClickInFrames('.se-font-size-code-toolbar-button');
      
      if (fontSizeButtonResult.success) {
        await window.electronAPI.playwrightWaitTimeout(500);
        
        // 특정 크기 선택
        const sizeSelector = `.se-toolbar-option-font-size-code-fs${fontSize}-button`;
        const sizeOptionResult = await window.electronAPI.playwrightClickInFrames(sizeSelector);
        
        if (sizeOptionResult.success) {
          console.log(`✅ 글씨 크기 ${fontSize} 적용 완료`);
          await window.electronAPI.playwrightWaitTimeout(300);
          return true;
        }
      }
    } catch (error) {
      console.warn(`⚠️ 글씨 크기 변경 실패: ${error}`);
    }
    
    return false;
  };

  // 네이버 블로그에서 굵기 상태 확인
  const getCurrentBoldState = async (): Promise<boolean> => {
    try {
      const stateResult = await window.electronAPI.playwrightEvaluateInFrames(`
        (function() {
          try {
            const boldButton = document.querySelector('.se-bold-toolbar-button');
            if (boldButton) {
              const isSelected = boldButton.classList.contains('se-is-selected');
              console.log('현재 굵기 상태:', isSelected ? '켜짐' : '꺼짐');
              return { success: true, isBold: isSelected };
            }
            return { success: false };
          } catch (error) {
            return { success: false, error: error.message };
          }
        })()
      `);
      
      return stateResult?.result?.isBold || false;
    } catch (error) {
      console.warn('굵기 상태 확인 실패:', error);
      return false;
    }
  };

  // 네이버 블로그에서 굵기 설정 (상태 확인 후 필요시에만 토글)
  const setBoldState = async (targetBold: boolean): Promise<boolean> => {
    console.log(`🔥 굵기 상태 설정: ${targetBold ? '켜기' : '끄기'}`);
    
    try {
      // 현재 굵기 상태 확인
      const currentBold = await getCurrentBoldState();
      
      // 이미 원하는 상태면 토글하지 않음
      if (currentBold === targetBold) {
        console.log(`✅ 이미 원하는 굵기 상태 (${targetBold ? '켜짐' : '꺼짐'})`);
        return true;
      }
      
      console.log(`🔄 굵기 상태 변경: ${currentBold ? '켜짐' : '꺼짐'} → ${targetBold ? '켜짐' : '꺼짐'}`);
      
      // 굵기 버튼 클릭 (토글)
      const boldSelectors = [
        '.se-bold-toolbar-button',
        'button[data-name="bold"]',
        'button[data-log="prt.bold"]'
      ];
      
      for (const selector of boldSelectors) {
        const result = await window.electronAPI.playwrightClickInFrames(selector);
        if (result.success) {
          console.log(`✅ 굵기 토글 완료`);
          await window.electronAPI.playwrightWaitTimeout(300);
          return true;
        }
      }
    } catch (error) {
      console.warn(`⚠️ 굵기 설정 실패: ${error}`);
    }
    
    return false;
  };

  // 기존 applyBold 함수는 setBoldState(true)로 대체
  const applyBold = async (): Promise<boolean> => {
    return await setBoldState(true);
  };

  // 서식 적용 (글씨 크기 + 굵게)
  const applyFormatting = async (formatInfo: { size: string; bold: boolean }): Promise<void> => {
    console.log(`🎨 서식 적용: 크기 ${formatInfo.size}${formatInfo.bold ? ' + 굵게' : ''}`);
    
    // 1. 글씨 크기 변경
    await changeFontSize(formatInfo.size);
    
    // 2. 굵게 처리 (필요한 경우)
    if (formatInfo.bold) {
      await applyBold();
    }
  };

  // 네이버 블로그에 표 추가 (원하는 크기로 조정)
  const addTable = async (rows: number = 3, cols: number = 3): Promise<boolean> => {
    console.log(`📊 표 추가: ${rows}행 ${cols}열`);
    
    try {
      // 1단계: 표 추가 버튼 클릭 (기본 3x3 생성)
      const tableButtonResult = await window.electronAPI.playwrightClickInFrames('.se-table-toolbar-button');
      
      if (!tableButtonResult.success) {
        console.warn('⚠️ 표 추가 버튼 클릭 실패');
        return false;
      }
      
      console.log('✅ 기본 3x3 표 생성 완료');
      await window.electronAPI.playwrightWaitTimeout(1000);
      
      // 2단계: 필요한 경우 행 추가 (3행에서 target까지)
      if (rows > 3) {
        const rowsToAdd = rows - 3;
        console.log(`📏 ${rowsToAdd}개 행 추가 중...`);
        
        for (let i = 0; i < rowsToAdd; i++) {
          // 마지막 행의 "행 추가" 버튼 클릭
          const addRowResult = await window.electronAPI.playwrightEvaluateInFrames(`
            (function() {
              try {
                // 행 컨트롤바에서 마지막 행의 "행 추가" 버튼 찾기
                const rowControlbar = document.querySelector('.se-cell-controlbar-row');
                if (rowControlbar) {
                  const lastRowItem = rowControlbar.lastElementChild;
                  if (lastRowItem) {
                    const addButton = lastRowItem.querySelector('.se-cell-add-button');
                    if (addButton) {
                      addButton.click();
                      console.log('행 추가 버튼 클릭');
                      return { success: true };
                    }
                  }
                }
                return { success: false, error: '행 추가 버튼을 찾을 수 없음' };
              } catch (error) {
                return { success: false, error: error.message };
              }
            })()
          `);
          
          if (addRowResult?.result?.success) {
            console.log(`✅ 행 ${i + 1} 추가 완료`);
            await window.electronAPI.playwrightWaitTimeout(500);
          } else {
            console.warn(`⚠️ 행 ${i + 1} 추가 실패`);
          }
        }
      }
      
      // 3단계: 필요한 경우 열 추가 (3열에서 target까지)
      if (cols > 3) {
        const colsToAdd = cols - 3;
        console.log(`📏 ${colsToAdd}개 열 추가 중...`);
        
        for (let i = 0; i < colsToAdd; i++) {
          // 마지막 열의 "열 추가" 버튼 클릭
          const addColResult = await window.electronAPI.playwrightEvaluateInFrames(`
            (function() {
              try {
                // 열 컨트롤바에서 마지막 열의 "열 추가" 버튼 찾기
                const colControlbar = document.querySelector('.se-cell-controlbar-column');
                if (colControlbar) {
                  const lastColItem = colControlbar.lastElementChild;
                  if (lastColItem) {
                    const addButton = lastColItem.querySelector('.se-cell-add-button');
                    if (addButton) {
                      addButton.click();
                      console.log('열 추가 버튼 클릭');
                      return { success: true };
                    }
                  }
                }
                return { success: false, error: '열 추가 버튼을 찾을 수 없음' };
              } catch (error) {
                return { success: false, error: error.message };
              }
            })()
          `);
          
          if (addColResult?.result?.success) {
            console.log(`✅ 열 ${i + 1} 추가 완료`);
            await window.electronAPI.playwrightWaitTimeout(500);
          } else {
            console.warn(`⚠️ 열 ${i + 1} 추가 실패`);
          }
        }
      }
      
      console.log(`✅ ${rows}행 ${cols}열 표 생성 완료`);
      return true;
      
    } catch (error) {
      console.warn(`⚠️ 표 추가 실패: ${error}`);
      return false;
    }
  };

  // 표 셀에 텍스트 입력 (정확한 네이버 구조 기반)
  const inputTableCell = async (text: string, rowIndex: number, colIndex: number): Promise<boolean> => {
    console.log(`📝 표 셀 입력: (${rowIndex}, ${colIndex}) - "${text}"`);
    
    try {
      // 표 셀 클릭 및 텍스트 입력
      const inputResult = await window.electronAPI.playwrightEvaluateInFrames(`
        (function() {
          try {
            // 네이버 블로그 표 구조에 맞는 셀 찾기
            const table = document.querySelector('.se-table-content');
            if (!table) {
              return { success: false, error: '표를 찾을 수 없음' };
            }
            
            const rows = table.querySelectorAll('tr.se-tr');
            if (rows.length <= ${rowIndex}) {
              return { success: false, error: '행 인덱스 초과: ${rowIndex}' };
            }
            
            const targetRow = rows[${rowIndex}];
            const cells = targetRow.querySelectorAll('td.se-cell');
            if (cells.length <= ${colIndex}) {
              return { success: false, error: '열 인덱스 초과: ${colIndex}' };
            }
            
            const targetCell = cells[${colIndex}];
            
            // 셀 클릭
            targetCell.click();
            targetCell.focus();
            
            // 셀 내부의 span.__se-node 요소 찾기
            const spanElement = targetCell.querySelector('span.__se-node');
            if (spanElement) {
              // 기존 내용 지우고 새 텍스트 입력
              spanElement.textContent = '${text.replace(/'/g, "\\'")}';
              spanElement.innerText = '${text.replace(/'/g, "\\'")}';
              
              // 이벤트 발생
              spanElement.focus();
              const events = ['input', 'change', 'keyup', 'blur'];
              events.forEach(eventType => {
                const event = new Event(eventType, { bubbles: true });
                spanElement.dispatchEvent(event);
              });
              
              return { success: true };
            } else {
              return { success: false, error: 'span.__se-node 요소를 찾을 수 없음' };
            }
          } catch (error) {
            return { success: false, error: error.message };
          }
        })()
      `);
      
      if (inputResult?.result?.success) {
        console.log(`✅ 표 셀 입력 완료: "${text}"`);
        await window.electronAPI.playwrightWaitTimeout(200);
        return true;
      } else {
        console.warn(`⚠️ 표 셀 입력 실패: ${inputResult?.result?.error}`);
        return false;
      }
    } catch (error) {
      console.warn(`⚠️ 표 셀 입력 실패: ${error}`);
      return false;
    }
  };

  // 표 헤더 행 선택 (여러 방식 시도)
  const selectTableHeaderRow = async (): Promise<boolean> => {
    console.log('🎯 표 헤더 행 선택...');
    
    try {
      // 방법 1: 드래그 선택으로 첫 번째 행 전체 선택
      const dragSelectResult = await window.electronAPI.playwrightEvaluateInFrames(`
        (function() {
          try {
            const table = document.querySelector('.se-table-container table') || document.querySelector('table');
            if (!table) return { success: false, message: '표를 찾을 수 없음' };
            
            const firstRow = table.querySelector('tr:first-child');
            if (!firstRow) return { success: false, message: '첫 번째 행을 찾을 수 없음' };
            
            const firstCell = firstRow.querySelector('td:first-child');
            const lastCell = firstRow.querySelector('td:last-child');
            
            if (firstCell && lastCell) {
              // 드래그 시뮬레이션
              const rect1 = firstCell.getBoundingClientRect();
              const rect2 = lastCell.getBoundingClientRect();
              
              // 마우스 다운 이벤트 (첫 번째 셀)
              firstCell.dispatchEvent(new MouseEvent('mousedown', {
                bubbles: true,
                clientX: rect1.left + 5,
                clientY: rect1.top + 5
              }));
              
              // 마우스 무브 이벤트 (마지막 셀로)
              document.dispatchEvent(new MouseEvent('mousemove', {
                bubbles: true,
                clientX: rect2.right - 5,
                clientY: rect2.top + 5
              }));
              
              // 마우스 업 이벤트 (마지막 셀)
              lastCell.dispatchEvent(new MouseEvent('mouseup', {
                bubbles: true,
                clientX: rect2.right - 5,
                clientY: rect2.top + 5
              }));
              
              console.log('드래그 선택 완료');
              return { success: true, method: 'drag' };
            }
            
            return { success: false, message: '셀을 찾을 수 없음' };
          } catch (error) {
            return { success: false, message: error.message };
          }
        })()
      `);
      
      if (dragSelectResult?.result?.success) {
        console.log('✅ 드래그로 헤더 행 선택 완료');
        await window.electronAPI.playwrightWaitTimeout(500);
        return true;
      }
      
      // 방법 2: 행 번호 클릭 (네이버 블로그에 행 번호가 있는 경우)
      const rowNumberSelectors = [
        '.se-table-container table tr:first-child th:first-child',
        '.se-table-container table tr:first-child .se-table-row-header'
      ];
      
      for (const selector of rowNumberSelectors) {
        const result = await window.electronAPI.playwrightClickInFrames(selector);
        if (result.success) {
          console.log('✅ 행 번호 클릭으로 헤더 행 선택 완료');
          return true;
        }
      }
      
      // 방법 3: 첫 번째 셀 클릭 후 Shift+End로 행 전체 선택
      const firstCellSelectors = [
        '.se-table-container table tr:first-child td:first-child',
        'table tbody tr:first-child td:first-child',
        'table tr:first-child td:first-child'
      ];
      
      for (const selector of firstCellSelectors) {
        const cellResult = await window.electronAPI.playwrightClickInFrames(selector);
        if (cellResult.success) {
          console.log('✅ 첫 번째 셀 클릭 완료, 행 전체 선택 시도...');
          
          // Shift+End 키 조합으로 행 전체 선택 시도
          const shiftSelectResult = await window.electronAPI.playwrightEvaluateInFrames(`
            (function() {
              try {
                const cell = document.querySelector('${selector}');
                if (cell) {
                  cell.focus();
                  
                  // Shift + End 키 이벤트
                  const shiftEndEvent = new KeyboardEvent('keydown', {
                    key: 'End',
                    code: 'End',
                    shiftKey: true,
                    bubbles: true
                  });
                  cell.dispatchEvent(shiftEndEvent);
                  
                  return { success: true };
                }
                return { success: false };
              } catch (error) {
                return { success: false, message: error.message };
              }
            })()
          `);
          
          if (shiftSelectResult?.result?.success) {
            console.log('✅ Shift+End로 행 전체 선택 완료');
            return true;
          }
          
          // 단순 첫 번째 셀만 선택된 상태로 진행
          console.log('✅ 첫 번째 셀 선택 완료 (단일 셀)');
          return true;
        }
      }
      
    } catch (error) {
      console.warn(`⚠️ 헤더 행 선택 실패: ${error}`);
    }
    
    return false;
  };

  // 표 셀 배경색 변경 (정확한 hex 코드 입력)
  const changeTableCellBackgroundColor = async (color: string = '#e0e0e0'): Promise<boolean> => {
    console.log(`🎨 표 셀 배경색 변경: ${color}`);
    
    try {
      // 1. 셀 배경색 버튼 클릭
      const cellBgButton = '.se-cell-background-color-toolbar-button';
      const buttonResult = await window.electronAPI.playwrightClickInFrames(cellBgButton);
      
      if (!buttonResult.success) {
        // 대체 셀렉터 시도
        const altSelectors = [
          'button[data-name="cell-background-color"]',
          '.se-property-toolbar-color-picker-button[data-name="cell-background-color"]'
        ];
        
        let altSuccess = false;
        for (const altSelector of altSelectors) {
          const altResult = await window.electronAPI.playwrightClickInFrames(altSelector);
          if (altResult.success) {
            console.log(`✅ 대체 셀 배경색 버튼 클릭 완료: ${altSelector}`);
            altSuccess = true;
            break;
          }
        }
        
        if (!altSuccess) {
          console.warn('⚠️ 셀 배경색 버튼을 찾을 수 없음');
          return false;
        }
      } else {
        console.log('✅ 셀 배경색 버튼 클릭 완료');
      }
      
      await window.electronAPI.playwrightWaitTimeout(500);
      
      // 2. 방법 1: 색상 팔레트에서 선택 시도
      const colorSelector = `.se-color-palette[data-color="${color}"]`;
      const colorResult = await window.electronAPI.playwrightClickInFrames(colorSelector);
      
      if (colorResult.success) {
        console.log(`✅ 팔레트에서 배경색 설정 완료: ${color}`);
        return true;
      }
      
      // 3. 방법 2: 더보기 → hex 입력 방식
      console.log('🔍 팔레트에서 색상을 찾지 못함, 더보기로 직접 입력 시도...');
      
      // 더보기 버튼 클릭
      const moreButtonResult = await window.electronAPI.playwrightClickInFrames('.se-color-picker-more-button');
      
      if (moreButtonResult.success) {
        console.log('✅ 더보기 버튼 클릭 완료');
        await window.electronAPI.playwrightWaitTimeout(300);
        
        // hex 입력 필드에 색상 코드 입력
        const hexInputResult = await window.electronAPI.playwrightEvaluateInFrames(`
          (function() {
            try {
              const hexInput = document.querySelector('.se-selected-color-hex');
              if (hexInput) {
                hexInput.click();
                hexInput.focus();
                hexInput.value = '${color}';
                
                // 이벤트 발생
                const events = ['input', 'change', 'keyup'];
                events.forEach(eventType => {
                  const event = new Event(eventType, { bubbles: true });
                  hexInput.dispatchEvent(event);
                });
                
                return { success: true };
              }
              return { success: false, message: 'hex 입력 필드를 찾을 수 없음' };
            } catch (error) {
              return { success: false, message: error.message };
            }
          })()
        `);
        
        if (hexInputResult?.result?.success) {
          console.log(`✅ hex 코드 입력 완료: ${color}`);
          await window.electronAPI.playwrightWaitTimeout(300);
          
          // 확인 버튼 클릭
          const applyButtonResult = await window.electronAPI.playwrightClickInFrames('.se-color-picker-apply-button');
          
          if (applyButtonResult.success) {
            console.log('✅ 색상 적용 확인 버튼 클릭 완료');
            return true;
          } else {
            console.warn('⚠️ 확인 버튼 클릭 실패');
          }
        } else {
          console.warn('⚠️ hex 코드 입력 실패');
        }
      } else {
        console.warn('⚠️ 더보기 버튼 클릭 실패');
      }
      
    } catch (error) {
      console.warn(`⚠️ 셀 배경색 변경 실패: ${error}`);
    }
    
    return false;
  };

  // 개별 헤더 셀에 스타일 적용
  const applyHeaderCellStyle = async (cellIndex: number, color: string = '#e0e0e0'): Promise<boolean> => {
    console.log(`🎯 헤더 셀 ${cellIndex + 1} 스타일 적용...`);
    
    try {
      // 특정 헤더 셀 선택
      const cellSelectors = [
        `.se-table-container table tr:first-child td:nth-child(${cellIndex + 1})`,
        `table tbody tr:first-child td:nth-child(${cellIndex + 1})`,
        `table tr:first-child td:nth-child(${cellIndex + 1})`
      ];
      
      for (const selector of cellSelectors) {
        const cellResult = await window.electronAPI.playwrightClickInFrames(selector);
        if (cellResult.success) {
          console.log(`✅ 헤더 셀 ${cellIndex + 1} 선택 완료`);
          await window.electronAPI.playwrightWaitTimeout(200);
          
          // 배경색 변경
          const bgChanged = await changeTableCellBackgroundColor(color);
          await window.electronAPI.playwrightWaitTimeout(200);
          
          // 굵게 처리
          const boldApplied = await applyBold();
          await window.electronAPI.playwrightWaitTimeout(200);
          
          console.log(`✅ 헤더 셀 ${cellIndex + 1} 스타일 적용 완료 (배경: ${bgChanged}, 굵게: ${boldApplied})`);
          return true;
        }
      }
      
      return false;
    } catch (error) {
      console.warn(`⚠️ 헤더 셀 ${cellIndex + 1} 스타일 적용 실패: ${error}`);
      return false;
    }
  };

  // 표 헤더 스타일 적용 (배경색 + 굵게)
  const applyTableHeaderStyle = async (): Promise<boolean> => {
    console.log('🎨 표 헤더 스타일 적용...');
    
    try {
      // 방법 1: 전체 행 선택 후 한 번에 적용
      const headerSelected = await selectTableHeaderRow();
      
      if (headerSelected) {
        console.log('✅ 헤더 행 전체 선택 완료, 스타일 적용 중...');
        await window.electronAPI.playwrightWaitTimeout(300);
        
        // 배경색 변경
        const bgChanged = await changeTableCellBackgroundColor('#e0e0e0');
        await window.electronAPI.playwrightWaitTimeout(300);
        
        // 텍스트 굵게 처리
        const boldApplied = await applyBold();
        
        console.log(`✅ 헤더 스타일 일괄 적용 완료 (배경: ${bgChanged}, 굵게: ${boldApplied})`);
        return true;
      }
      
      // 방법 2: 전체 행 선택 실패 시 개별 셀 적용
      console.log('⚠️ 헤더 행 전체 선택 실패, 개별 셀 스타일 적용으로 변경...');
      
      // 표의 첫 번째 행에서 셀 개수 확인
      const cellCountResult = await window.electronAPI.playwrightEvaluateInFrames(`
        (function() {
          try {
            const firstRow = document.querySelector('.se-table-container table tr:first-child') || 
                            document.querySelector('table tr:first-child');
            if (firstRow) {
              const cells = firstRow.querySelectorAll('td');
              return { success: true, cellCount: cells.length };
            }
            return { success: false, cellCount: 0 };
          } catch (error) {
            return { success: false, cellCount: 0 };
          }
        })()
      `);
      
      const cellCount = cellCountResult?.result?.cellCount || 3; // 기본값 3개
      console.log(`📊 헤더 행 셀 개수: ${cellCount}`);
      
      // 각 셀에 개별적으로 스타일 적용
      let successCount = 0;
      for (let i = 0; i < cellCount; i++) {
        const cellSuccess = await applyHeaderCellStyle(i, '#e0e0e0');
        if (cellSuccess) {
          successCount++;
        }
        await window.electronAPI.playwrightWaitTimeout(300);
      }
      
      console.log(`✅ 헤더 스타일 개별 적용 완료: ${successCount}/${cellCount} 셀 성공`);
      return successCount > 0;
      
    } catch (error) {
      console.warn(`⚠️ 헤더 스타일 적용 실패: ${error}`);
      return false;
    }
  };

  // Step3 표 데이터 파싱
  const parseTableData = (tableContent: string) => {
    try {
      console.log('📊 표 내용 파싱 시작...');
      
      // tr 태그별로 행 찾기
      const rowRegex = /<tr[^>]*class="se-tr"[^>]*>(.*?)<\/tr>/g;
      const rows: string[][] = [];
      let rowMatch;
      
      while ((rowMatch = rowRegex.exec(tableContent)) !== null) {
        const rowContent = rowMatch[1];
        const cells: string[] = [];
        
        // td 태그별로 셀 찾기
        const cellRegex = /<td[^>]*>(.*?)<\/td>/g;
        let cellMatch;
        
        while ((cellMatch = cellRegex.exec(rowContent)) !== null) {
          const cellContent = cellMatch[1];
          
          // 셀 내부의 텍스트 추출 (span 태그 내부)
          const textRegex = /<span[^>]*__se-node[^>]*>(.*?)<\/span>/g;
          const textMatch = textRegex.exec(cellContent);
          const cellText = textMatch ? textMatch[1].trim() : '';
          
          cells.push(cellText);
        }
        
        if (cells.length > 0) {
          rows.push(cells);
        }
      }
      
      if (rows.length > 0) {
        const tableData = {
          rows: rows.length,
          cols: rows[0].length,
          data: rows
        };
        
        console.log(`✅ 표 파싱 완료: ${tableData.rows}행 ${tableData.cols}열`);
        console.log('📋 표 데이터:', tableData.data);
        
        return tableData;
      }
      
      return null;
    } catch (error) {
      console.error('❌ 표 파싱 실패:', error);
      return null;
    }
  };

  // Step3에서 편집된 HTML 내용을 문단별로 파싱 (개선된 버전)
  const parseContentByParagraphs = (htmlContent: string) => {
    console.log('🔍 Step3 HTML 구조 분석 시작...');
    
    const paragraphs: {
      segments: {
        text: string;
        fontSize: string;
        isBold: boolean;
      }[];
      isTable?: boolean;
      tableData?: { rows: number; cols: number; data: string[][] };
    }[] = [];
    
    // 1. 먼저 표 처리
    const tableRegex = /<div class="se-component se-table[^>]*">[\s\S]*?<table class="se-table-content[^>]*">([\s\S]*?)<\/table>[\s\S]*?<\/div>/g;
    let tableMatch;
    let processedContent = htmlContent;
    
    while ((tableMatch = tableRegex.exec(htmlContent)) !== null) {
      const tableContent = tableMatch[1];
      console.log('📊 표 발견');
      
      const tableData = parseTableData(tableContent);
      if (tableData) {
        paragraphs.push({
          segments: [],
          isTable: true,
          tableData
        });
        console.log(`✅ 표 파싱: ${tableData.rows}행 ${tableData.cols}열`);
        
        // 처리된 표는 원본에서 제거
        processedContent = processedContent.replace(tableMatch[0], '');
      }
    }
    
    // 2. 문단(p 태그)별로 처리
    const pRegex = /<p[^>]*class="se-text-paragraph[^>]*"[^>]*>([\s\S]*?)<\/p>/g;
    let pMatch;
    
    while ((pMatch = pRegex.exec(processedContent)) !== null) {
      const pContent = pMatch[1];
      
      // 이미지 플레이스홀더 체크
      if (pContent.includes('(이미지)')) {
        console.log('📷 이미지 플레이스홀더 발견 - 건너뛰기');
        continue;
      }
      
      const segments: { text: string; fontSize: string; isBold: boolean; }[] = [];
      
      // span 태그별로 세그먼트 파싱
      const spanRegex = /<span[^>]*class="[^"]*se-ff-nanumgothic[^"]*"[^>]*>(.*?)<\/span>/g;
      let spanMatch;
      
      if (pContent.match(spanRegex)) {
        // span이 있는 경우
        while ((spanMatch = spanRegex.exec(pContent)) !== null) {
          const spanOuterHTML = spanMatch[0];
          const spanInnerHTML = spanMatch[1];
          
          // 폰트 크기 추출
          let fontSize = '15px';
          const fontSizeMatch = spanOuterHTML.match(/se-fs(\d+)/);
          if (fontSizeMatch) {
            fontSize = fontSizeMatch[1] + 'px';
          }
          
          // 굵기 추출
          const isBold = spanOuterHTML.includes('font-weight: bold') || spanOuterHTML.includes('font-weight:bold');
          
          // 중첩된 span 처리
          let text = '';
          const nestedSpanRegex = /<span[^>]*>(.*?)<\/span>/g;
          let nestedMatch;
          
          if (spanInnerHTML.match(nestedSpanRegex)) {
            // 중첩된 span이 있는 경우
            while ((nestedMatch = nestedSpanRegex.exec(spanInnerHTML)) !== null) {
              const nestedSpanOuter = nestedMatch[0];
              let nestedText = nestedMatch[1];
              
              // 중첩된 span의 폰트 크기 우선 적용
              const nestedFontSizeMatch = nestedSpanOuter.match(/se-fs(\d+)/);
              if (nestedFontSizeMatch) {
                fontSize = nestedFontSizeMatch[1] + 'px';
              }
              
              // 중첩된 span의 굵기 우선 적용
              const nestedBold = nestedSpanOuter.includes('font-weight: bold') || nestedSpanOuter.includes('font-weight:bold');
              
              nestedText = nestedText
                .replace(/&nbsp;/g, ' ')
                .replace(/&amp;/g, '&')
                .replace(/&lt;/g, '<')
                .replace(/&gt;/g, '>');
              
              if (nestedText.trim()) {
                segments.push({
                  text: nestedText.trim(),
                  fontSize,
                  isBold: nestedBold || isBold
                });
              }
            }
          } else {
            // 중첩되지 않은 경우
            text = spanInnerHTML
              .replace(/<[^>]*>/g, '')
              .replace(/&nbsp;/g, ' ')
              .replace(/&amp;/g, '&')
              .replace(/&lt;/g, '<')
              .replace(/&gt;/g, '>');
            
            if (text.trim()) {
              segments.push({
                text: text.trim(),
                fontSize,
                isBold
              });
            }
          }
        }
      } else {
        // span이 없는 일반 텍스트
        const text = pContent
          .replace(/<[^>]*>/g, '')
          .replace(/&nbsp;/g, ' ')
          .replace(/&amp;/g, '&')
          .replace(/&lt;/g, '<')
          .replace(/&gt;/g, '>')
          .trim();
        
        if (text) {
          segments.push({
            text,
            fontSize: '15px',
            isBold: false
          });
        }
      }
      
      // 세그먼트가 있는 경우만 문단 추가
      if (segments.length > 0) {
        paragraphs.push({ segments });
        console.log(`📝 문단 파싱 완료: ${segments.length}개 세그먼트`);
        segments.forEach(seg => console.log(`  - "${seg.text}" (${seg.fontSize}${seg.isBold ? ', 굵게' : ''})`));
      }
    }
    
    console.log(`✅ 총 ${paragraphs.length}개 문단 파싱 완료`);
    return paragraphs;
  };

  // 클립보드 붙여넣기로 네이버에 전송 (단순화된 버전)
  const inputContentWithFormatting = async (): Promise<boolean> => {
    console.log('📝 본문 입력 시작 (클립보드 붙여넣기)...');
    
    if (!editedContent) {
      console.warn('⚠️ 편집된 내용이 없습니다.');
      return false;
    }
    
    try {
      // 네이버 블로그 본문 영역 클릭
      console.log('📝 네이버 블로그 본문 영역 클릭 시도...');
      
      const contentSelectors = [
        '.se-placeholder.__se_placeholder:not(.se-placeholder-focused)',
        '.se-placeholder.__se_placeholder',
        '[contenteditable="true"]',
        '.se-module-text.__se-unit',
        '.se-text-paragraph'
      ];
      
      let contentClicked = false;
      for (const selector of contentSelectors) {
        console.log(`네이버 본문 영역 클릭 시도: ${selector}`);
        const clickResult = await window.electronAPI.playwrightClickInFrames(selector, 'PostWriteForm.naver');
        if (clickResult.success) {
          console.log(`✅ 네이버 본문 영역 클릭 성공: ${selector}`);
          contentClicked = true;
          await window.electronAPI.playwrightWaitTimeout(1000);
          break;
        }
      }
      
      if (!contentClicked) {
        console.warn('⚠️ 네이버 본문 영역 클릭 실패');
        return false;
      }
      
      // 바로 붙여넣기 (이미 클립보드에 복사되어 있음)
      console.log('📋 네이버 블로그에서 붙여넣기 시작...');
      
      const pasteResult = await window.electronAPI.playwrightPress('Control+v');
      if (!pasteResult.success) {
        console.warn('⚠️ Ctrl+V 실패');
        return false;
      }
      
      console.log('✅ Ctrl+V 붙여넣기 완료');
      await window.electronAPI.playwrightWaitTimeout(3000); // 네이버 처리 시간 충분히 대기
      
      // 붙여넣기 결과 확인
      const pasteCheckResult = await window.electronAPI.playwrightEvaluateInFrames(`
        (function() {
          try {
            // 다양한 에디터 요소 확인
            const editorSelectors = [
              '[contenteditable="true"]',
              '.se-module-text',
              '.se-text-paragraph',
              '.se-component-content'
            ];
            
            let editor = null;
            let content = '';
            
            for (const selector of editorSelectors) {
              const el = document.querySelector(selector);
              if (el && (el.innerHTML || el.textContent)) {
                editor = el;
                content = el.innerHTML || el.textContent || '';
                if (content.trim().length > 0) {
                  console.log('에디터 발견:', selector, '내용 길이:', content.length);
                  break;
                }
              }
            }
            
            if (!editor) {
              return { success: false, error: '에디터를 찾을 수 없음' };
            }
            
            const hasContent = content.trim().length > 0;
            const hasRichContent = content.includes('<') || content.includes('민생지원금'); // Step3 콘텐츠 키워드 확인
            
            console.log('붙여넣기 결과 상세 확인:', {
              hasContent: hasContent,
              hasRichContent: hasRichContent,
              contentLength: content.length,
              preview: content.substring(0, 100),
              editorClass: editor.className
            });
            
            return { 
              success: hasContent || hasRichContent, // 내용이 있거나 특정 키워드가 있으면 성공
              contentLength: content.length,
              preview: content.substring(0, 200),
              editorFound: editor.className
            };
          } catch (error) {
            console.error('붙여넣기 확인 오류:', error);
            return { success: false, error: error.message };
          }
        })()
      `, 'PostWriteForm.naver');
      
      if (pasteCheckResult?.result?.success) {
        console.log('🎉 키보드 복사/붙여넣기 성공!');
        console.log('붙여넣어진 내용 길이:', pasteCheckResult.result.contentLength);
        console.log('내용 미리보기:', pasteCheckResult.result.preview);
        return true;
      } else {
        console.warn('⚠️ 붙여넣기 결과 확인 실패');
        console.log('확인 결과:', pasteCheckResult?.result);
        return false;
      }
      
    } catch (error) {
      console.error('❌ 클립보드 복사/붙여넣기 실패:', error);
      return false;
    }
  };

  // 네이버 로그인 + 발행 통합 함수
  const publishToNaverBlog = async (): Promise<PublishResult> => {
    if (!naverCredentials.username || !naverCredentials.password) {
      setPublishStatus(prev => ({
        ...prev,
        error: '아이디와 비밀번호를 입력해주세요.'
      }));
      return { success: false, message: '아이디와 비밀번호를 입력해주세요.' };
    }
    
    setPublishStatus(prev => ({
      ...prev,
      error: '',
      isPublishing: true
    }));
    
    try {
      console.log('네이버 로그인 시도:', { username: naverCredentials.username });
      
      // 1단계: 먼저 클립보드에 복사
      if (copyToClipboard) {
        setPublishStatus(prev => ({
          ...prev,
          error: '콘텐츠를 클립보드에 복사하는 중...'
        }));
        
        const copySuccess = await copyToClipboard();
        if (!copySuccess) {
          console.warn('⚠️ HTML 형식 복사 실패, 텍스트로 복사되었습니다.');
        } else {
          console.log('✅ 콘텐츠가 클립보드에 복사되었습니다.');
        }
      }
      
      // 2단계: 브라우저 초기화
      setPublishStatus(prev => ({
        ...prev,
        error: '브라우저를 시작하는 중...'
      }));
      
      const initResult = await window.electronAPI.playwrightInitialize();
      if (!initResult.success) {
        throw new Error(`브라우저 초기화 실패: ${initResult.error}`);
      }
      
      // 2단계: 네이버 로그인
      setPublishStatus(prev => ({
        ...prev,
        error: '네이버 로그인 중...'
      }));
      
      const loginStatus = await performNaverLogin(naverCredentials);
      
      if (loginStatus === 'success') {
        // 로그인 성공
        setPublishStatus(prev => ({ 
          ...prev, 
          isLoggedIn: true,
          error: '로그인 성공! 글쓰기 페이지로 이동 중...'
        }));
        console.log('로그인 성공!');
        
        // 3단계: 블로그 글쓰기 페이지로 이동
        const blogSuccess = await navigateToNaverBlogWrite(naverCredentials.username);
        if (!blogSuccess) {
          throw new Error('블로그 글쓰기 페이지 이동 실패');
        }
        
        // 4단계: 본문 자동 입력 (글씨 크기 포함)
        setPublishStatus(prev => ({
          ...prev,
          error: '본문을 자동으로 입력하는 중...'
        }));
        
        const contentSuccess = await inputContentWithFormatting();
        if (!contentSuccess) {
          console.warn('⚠️ 본문 자동 입력 실패, 수동으로 진행해주세요.');
        }
        
        // 5단계: 완료 안내
        setPublishStatus(prev => ({
          ...prev,
          error: '자동 입력 완료! 브라우저에서 확인 후 발행해주세요...'
        }));
        
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // 성공 처리 (브라우저는 열린 상태로 유지)
        setPublishStatus(prev => ({
          ...prev,
          success: true,
          isPublishing: false,
          error: ''
        }));
        
        const result: PublishResult = {
          success: true,
          message: '네이버 블로그에 로그인 완료! 브라우저에서 글을 작성해주세요.',
          url: `https://blog.naver.com/${naverCredentials.username}?Redirect=Write&`
        };
        
        // 상위 컴포넌트에 완료 알림
        onComplete({ 
          generatedContent: editedContent
        });
        
        return result;
        
      } else if (loginStatus === 'two_factor') {
        setPublishStatus(prev => ({
          ...prev,
          error: '2차 인증이 필요합니다. 브라우저에서 인증을 완료해주세요.',
          isPublishing: false
        }));
        return { 
          success: false, 
          message: '2차 인증이 필요합니다. 브라우저에서 인증을 완료한 후 다시 시도해주세요.' 
        };
        
      } else if (loginStatus === 'device_registration') {
        setPublishStatus(prev => ({
          ...prev,
          error: '새 기기 등록이 필요합니다. 브라우저에서 등록을 완료해주세요.',
          isPublishing: false
        }));
        return { 
          success: false, 
          message: '새 기기 등록이 필요합니다. 브라우저에서 등록을 완료한 후 다시 시도해주세요.' 
        };
        
      } else {
        throw new Error('로그인 실패');
      }
      
    } catch (error) {
      console.error('로그인 또는 발행 실패:', error);
      const errorMessage = error instanceof Error ? error.message : '로그인 또는 발행에 실패했습니다. 아이디와 비밀번호를 확인해주세요.';
      
      setPublishStatus(prev => ({
        ...prev,
        error: errorMessage,
        isLoggedIn: false,
        isPublishing: false
      }));
      
      // 브라우저 정리
      try {
        await window.electronAPI.playwrightCleanup();
      } catch (cleanupError) {
        console.error('브라우저 정리 실패:', cleanupError);
      }
      
      return { success: false, message: errorMessage };
    }
  };

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
      <h4 className="font-medium text-blue-800 mb-3">네이버 블로그 발행</h4>
      
      {!publishStatus.success ? (
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              네이버 아이디
            </label>
            <input
              type="text"
              value={naverCredentials.username}
              onChange={(e) => setNaverCredentials(prev => ({ ...prev, username: e.target.value }))}
              placeholder="네이버 아이디를 입력하세요"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={publishStatus.isPublishing}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              비밀번호
            </label>
            <input
              type="password"
              value={naverCredentials.password}
              onChange={(e) => setNaverCredentials(prev => ({ ...prev, password: e.target.value }))}
              placeholder="비밀번호를 입력하세요"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={publishStatus.isPublishing}
              onKeyPress={(e) => e.key === 'Enter' && publishToNaverBlog()}
            />
          </div>
          
          <div className="text-sm text-gray-600 bg-gray-50 border border-gray-200 rounded p-3">
            <strong>발행 정보:</strong>
            <div className="ml-2 mt-1">
              • 제목: {data.selectedTitle}
              • 메인 키워드: {data.keyword || '없음'}
              • 이미지: {Object.keys(imageUrls).length}개
            </div>
          </div>
          
          {publishStatus.error && (
            <div className={`text-sm border rounded p-2 ${
              publishStatus.isPublishing 
                ? 'text-blue-600 bg-blue-50 border-blue-200' 
                : 'text-red-600 bg-red-50 border-red-200'
            }`}>
              {publishStatus.isPublishing ? '🚀' : '❌'} {publishStatus.error}
            </div>
          )}
          
          {publishStatus.isLoggedIn && !publishStatus.success && (
            <div className="text-green-600 text-sm bg-green-50 border border-green-200 rounded p-2">
              ✅ 로그인 완료! 브라우저에서 글 작성을 진행해주세요.
              <div className="mt-2">
                <button
                  onClick={logoutFromNaver}
                  className="text-xs px-2 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
                >
                  브라우저 닫기
                </button>
              </div>
            </div>
          )}
          
          <button
            onClick={publishToNaverBlog}
            disabled={publishStatus.isPublishing || !naverCredentials.username || !naverCredentials.password}
            className="w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {publishStatus.isPublishing ? (
              publishStatus.error ? `🚀 ${publishStatus.error}` : '🚀 네이버 블로그 발행 중...'
            ) : '📤 네이버 블로그에 자동 발행하기'}
          </button>
          
          {publishStatus.isPublishing && (
            <div className="mt-2 text-xs text-gray-600 bg-gray-50 border border-gray-200 rounded p-2">
              💡 브라우저 창이 열립니다. 2차 인증이나 기기 등록이 필요한 경우 브라우저에서 직접 처리해주세요.
            </div>
          )}
        </div>
      ) : (
        // 발행 완료 후 상태
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <div className="text-green-600 text-xl">✅</div>
              <h4 className="font-medium text-green-800">
                발행 완료: {naverCredentials.username}
              </h4>
            </div>
            <button
              onClick={logoutFromNaver}
              className="text-sm text-gray-600 hover:text-gray-800 underline"
            >
              다시 발행하기
            </button>
          </div>
          
          <p className="text-sm text-green-700">
            네이버 블로그에 성공적으로 발행되었습니다!
          </p>
        </div>
      )}
      
      <div className="mt-3 text-xs text-gray-500">
        ⚠️ 로그인 정보는 발행 목적으로만 사용되며 저장되지 않습니다.
      </div>
    </div>
  );
};

// 네이버 발행 컴포넌트 메타정보
export const NaverPublishMeta: IPublishComponent = {
  platform: 'naver',
  name: '네이버 블로그',
  icon: '🟢'
};

export default NaverPublish;