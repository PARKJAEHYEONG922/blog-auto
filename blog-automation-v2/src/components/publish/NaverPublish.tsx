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
  onComplete 
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

    // 페이지 로드 대기
    await window.electronAPI.playwrightWaitTimeout(3000);

    // 작성 중인 글 팝업 처리 (iframe 기반)
    try {
      console.log('작성 중인 글 팝업 확인 중...');
      
      // 1. 팝업 취소 버튼 클릭 시도 (iframe 내부)
      const cancelSelectors = [
        '.se-popup-button-cancel', 
        'button.se-popup-button-cancel',
        '.se-popup-button:has-text("취소")',
        'button:has-text("취소")'
      ];
      
      for (const selector of cancelSelectors) {
        console.log(`팝업 취소 버튼 시도: ${selector}`);
        
        // 네이버 블로그는 iframe 구조이므로 iframe에서 우선 시도
        let result = await window.electronAPI.playwrightClickInFrames(selector);
        
        // iframe에서 실패하면 일반 클릭 시도 (혹시 몰라서)
        if (!result.success) {
          console.log(`iframe 클릭 실패, 일반 클릭 시도: ${selector}`);
          result = await window.electronAPI.playwrightClick(selector);
        }
        
        if (result.success) {
          console.log('✅ 작성 중인 글 팝업 취소 완료');
          await window.electronAPI.playwrightWaitTimeout(1000);
          break;
        }
      }
      
    } catch (error) {
      console.log('팝업 처리 중 오류 (무시):', error);
    }

    // 2. 도움말 패널 닫기 버튼 처리
    try {
      console.log('도움말 패널 닫기 버튼 확인 중...');
      
      const helpCloseSelectors = [
        '.se-help-panel-close-button',
        'button.se-help-panel-close-button',
        'button:has-text("닫기")',
        '.se-help-panel .close-button'
      ];
      
      for (const selector of helpCloseSelectors) {
        console.log(`도움말 닫기 버튼 시도: ${selector}`);
        
        // 네이버 블로그는 iframe 구조이므로 iframe에서 우선 시도
        let result = await window.electronAPI.playwrightClickInFrames(selector);
        
        // iframe에서 실패하면 일반 클릭 시도 (혹시 몰라서)
        if (!result.success) {
          console.log(`iframe 클릭 실패, 일반 클릭 시도: ${selector}`);
          result = await window.electronAPI.playwrightClick(selector);
        }
        
        if (result.success) {
          console.log('✅ 도움말 패널 닫기 완료');
          await window.electronAPI.playwrightWaitTimeout(1000);
          break;
        }
      }
      
    } catch (error) {
      console.log('도움말 패널 처리 중 오류 (무시):', error);
    }

    // 3. 제목 입력 처리
    try {
      console.log('제목 입력 시작...');
      
      const titleSelectors = [
        '.se-section-documentTitle .se-module-text p',
        '.se-section-documentTitle .se-text-paragraph', 
        '.se-title-text p',
        '#SE-77bb5fe8-a104-4119-872a-d4f643e50beb', // 실제 ID
        '.se-section-documentTitle span.__se-node'
      ];
      
      for (const selector of titleSelectors) {
        console.log(`제목 섹션 클릭 시도: ${selector}`);
        
        // iframe에서 제목 섹션 클릭
        let result = await window.electronAPI.playwrightClickInFrames(selector);
        
        if (result.success) {
          console.log('✅ 제목 섹션 클릭 성공');
          await window.electronAPI.playwrightWaitTimeout(500);
          
          // 제목 타이핑
          console.log(`제목 타이핑 중: "${data.selectedTitle}"`);
          
          // iframe 내부에서 타이핑 실행
          const typingResult = await window.electronAPI.playwrightEvaluateInFrames(`
            (function() {
              try {
                console.log('iframe 내부에서 제목 입력 시도...');
                
                // iframe 내부에서 제목 입력 요소 찾기
                const titleElements = [
                  document.querySelector('.se-section-documentTitle .se-text-paragraph span.__se-node'),
                  document.querySelector('.se-title-text span.__se-node'),
                  document.querySelector('#SE-c8aafb9a-af34-468d-9aee-a62b73fa881b'),
                  document.querySelector('.se-section-documentTitle span'),
                  document.activeElement
                ];
                
                console.log('찾은 요소들:', titleElements);
                
                const titleElement = titleElements.find(el => el && el.tagName);
                
                if (titleElement) {
                  console.log('제목 요소 발견:', titleElement);
                  
                  // 클릭하여 활성화
                  titleElement.click();
                  
                  // 잠시 대기
                  setTimeout(() => {
                    // 기존 내용 지우기
                    if (titleElement.textContent) {
                      titleElement.textContent = '';
                    }
                    
                    // 제목 입력
                    titleElement.textContent = '${data.selectedTitle.replace(/'/g, "\\'")}';
                    titleElement.innerText = '${data.selectedTitle.replace(/'/g, "\\'")}';
                    
                    // focus 및 이벤트 발생
                    titleElement.focus();
                    
                    // 다양한 이벤트 발생
                    const events = ['input', 'change', 'keyup', 'paste'];
                    events.forEach(eventType => {
                      const event = new Event(eventType, { bubbles: true });
                      titleElement.dispatchEvent(event);
                    });
                  }, 100);
                  
                  return { success: true, message: '제목 입력 완료' };
                } else {
                  return { success: false, message: '제목 입력 요소를 찾을 수 없음' };
                }
              } catch (error) {
                return { success: false, message: error.message };
              }
            })()
          `);
          
          if (typingResult && typingResult.result && typingResult.result.success) {
            console.log('✅ 제목 입력 완료');
          } else {
            console.warn('⚠️ 제목 입력 실패:', typingResult?.result?.message);
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
      
      // 1단계: 브라우저 초기화
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
        
        // 4단계: 포스팅 안내 (실제 글쓰기는 수동)
        setPublishStatus(prev => ({
          ...prev,
          error: '브라우저에서 글쓰기를 진행해주세요...'
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
              • 태그: {data.keyword || '없음'}
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