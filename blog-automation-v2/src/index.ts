import { app, BrowserWindow, ipcMain, shell } from 'electron';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
const YTDlpWrap = require('yt-dlp-wrap').default;

// 설정 파일 경로
const getConfigPath = (filename: string) => {
  const userDataPath = app.getPath('userData');
  const configPath = path.join(userDataPath, filename);
  console.log(`📁 설정 파일 경로: ${configPath}`);
  return configPath;
};

// IPC 핸들러 설정
const setupIpcHandlers = () => {
  // 기본 설정 저장
  ipcMain.handle('defaults:save', async (event, defaultSettings) => {
    try {
      const configPath = getConfigPath('defaults.json');
      await fs.promises.writeFile(configPath, JSON.stringify(defaultSettings, null, 2));
      console.log('기본 설정 저장 완료:', configPath);
      return { success: true };
    } catch (error) {
      console.error('기본 설정 저장 실패:', error);
      return { success: false, message: error.message };
    }
  });

  // 기본 설정 로드
  ipcMain.handle('defaults:load', async () => {
    try {
      const configPath = getConfigPath('defaults.json');
      const data = await fs.promises.readFile(configPath, 'utf-8');
      return JSON.parse(data);
    } catch (error) {
      console.log('기본 설정 파일이 없거나 읽기 실패:', error.message);
      return null;
    }
  });

  // LLM 설정 저장
  ipcMain.handle('settings:save', async (event, settings) => {
    try {
      const configPath = getConfigPath('llm-settings.json');
      await fs.promises.writeFile(configPath, JSON.stringify(settings, null, 2));
      console.log('LLM 설정 저장 완료:', configPath);
      return { success: true };
    } catch (error) {
      console.error('LLM 설정 저장 실패:', error);
      return { success: false, message: error.message };
    }
  });

  // LLM 설정 로드
  ipcMain.handle('settings:load', async () => {
    try {
      const configPath = getConfigPath('llm-settings.json');
      const data = await fs.promises.readFile(configPath, 'utf-8');
      return JSON.parse(data);
    } catch (error) {
      console.log('LLM 설정 파일이 없거나 읽기 실패:', error.message);
      return null;
    }
  });

  // 네이버 API 설정 저장
  ipcMain.handle('naverApi:save', async (event, naverApiSettings) => {
    try {
      const configPath = getConfigPath('naver-api.json');
      console.log('🔧 네이버 API 설정 저장 시도:', configPath);
      console.log('📄 저장할 데이터:', naverApiSettings);
      await fs.promises.writeFile(configPath, JSON.stringify(naverApiSettings, null, 2));
      console.log('✅ 네이버 API 설정 저장 완료:', configPath);
      return { success: true };
    } catch (error) {
      console.error('❌ 네이버 API 설정 저장 실패:', error);
      return { success: false, message: error.message };
    }
  });

  // 네이버 API 설정 로드
  ipcMain.handle('naverApi:load', async () => {
    try {
      const configPath = getConfigPath('naver-api.json');
      console.log('🔍 네이버 API 설정 로드 시도:', configPath);
      const data = await fs.promises.readFile(configPath, 'utf-8');
      const parsedData = JSON.parse(data);
      console.log('✅ 네이버 API 설정 로드 성공:', parsedData);
      return { success: true, data: parsedData };
    } catch (error) {
      console.log('❌ 네이버 API 설정 파일이 없거나 읽기 실패:', error.message);
      return { success: false, data: null };
    }
  });

  // 네이버 API 설정 삭제
  ipcMain.handle('naverApi:delete', async () => {
    try {
      const configPath = getConfigPath('naver-api.json');
      await fs.promises.unlink(configPath);
      console.log('네이버 API 설정 삭제 완료:', configPath);
      return { success: true };
    } catch (error) {
      console.error('네이버 API 설정 삭제 실패:', error);
      return { success: false, message: error.message };
    }
  });

  // YouTube API 설정 저장
  ipcMain.handle('youtubeApi:save', async (event, youtubeApiSettings) => {
    try {
      const configPath = getConfigPath('youtube-api.json');
      console.log('🔧 YouTube API 설정 저장 시도:', configPath);
      console.log('📄 저장할 데이터:', youtubeApiSettings);
      await fs.promises.writeFile(configPath, JSON.stringify(youtubeApiSettings, null, 2));
      console.log('✅ YouTube API 설정 저장 완료:', configPath);
      return { success: true };
    } catch (error) {
      console.error('❌ YouTube API 설정 저장 실패:', error);
      return { success: false, message: error.message };
    }
  });

  // YouTube API 설정 로드
  ipcMain.handle('youtubeApi:load', async () => {
    try {
      const configPath = getConfigPath('youtube-api.json');
      console.log('🔍 YouTube API 설정 로드 시도:', configPath);
      const data = await fs.promises.readFile(configPath, 'utf-8');
      const parsedData = JSON.parse(data);
      console.log('✅ YouTube API 설정 로드 성공:', parsedData);
      return { success: true, data: parsedData };
    } catch (error) {
      console.log('❌ YouTube API 설정 파일이 없거나 읽기 실패:', error.message);
      return { success: false, data: null };
    }
  });

  // YouTube API 설정 삭제
  ipcMain.handle('youtubeApi:delete', async () => {
    try {
      const configPath = getConfigPath('youtube-api.json');
      await fs.promises.unlink(configPath);
      console.log('YouTube API 설정 삭제 완료:', configPath);
      return { success: true };
    } catch (error) {
      console.error('YouTube API 설정 삭제 실패:', error);
      return { success: false, message: error.message };
    }
  });

  // API 테스트 핸들러
  ipcMain.handle('api:test', async (event, provider: string, apiKey: string) => {
    try {
      console.log(`API 테스트 시작: ${provider}`);
      
      // 간단한 API 테스트 구현
      if (provider === 'openai') {
        const response = await fetch('https://api.openai.com/v1/models', {
          headers: {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (response.ok) {
          return { success: true, message: 'OpenAI API 연결 성공' };
        } else {
          return { success: false, message: `OpenAI API 오류: ${response.status}` };
        }
      } else if (provider === 'anthropic' || provider === 'claude') {
        const response = await fetch('https://api.anthropic.com/v1/messages', {
          method: 'POST',
          headers: {
            'x-api-key': apiKey,
            'anthropic-version': '2023-06-01',
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            model: 'claude-3-haiku-20240307',
            max_tokens: 10,
            messages: [{ role: 'user', content: 'test' }]
          })
        });
        
        if (response.ok) {
          return { success: true, message: 'Claude API 연결 성공' };
        } else {
          return { success: false, message: `Claude API 오류: ${response.status}` };
        }
      } else if (provider === 'gemini') {
        const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models?key=${apiKey}`);
        
        if (response.ok) {
          return { success: true, message: 'Gemini API 연결 성공' };
        } else {
          return { success: false, message: `Gemini API 오류: ${response.status}` };
        }
      } else if (provider === 'runware') {
        // Runware API 테스트 - 간단한 인증 확인
        try {
          const response = await fetch('https://api.runware.ai/v1', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${apiKey}`
            },
            body: JSON.stringify([{
              taskType: 'imageInference',
              taskUUID: 'test-connection-uuid',
              positivePrompt: 'test image connection',
              width: 512,
              height: 512,
              model: 'civitai:102438@133677',
              numberResults: 1,
              steps: 1,
              CFGScale: 7,
              seed: 12345
            }])
          });
          
          if (response.ok || response.status === 400) {
            // 200 (성공) 또는 400 (잘못된 요청이지만 인증은 성공)
            return { success: true, message: 'Runware API 연결 성공' };
          } else if (response.status === 401 || response.status === 403) {
            return { success: false, message: 'Runware API 키가 유효하지 않습니다' };
          } else {
            return { success: false, message: `Runware API 오류: ${response.status}` };
          }
        } catch (error) {
          return { success: false, message: `Runware API 연결 실패: ${error.message}` };
        }
      } else {
        return { success: false, message: '지원하지 않는 API 제공자입니다' };
      }
    } catch (error) {
      console.error(`API 테스트 실패 (${provider}):`, error);
      return { success: false, message: error.message };
    }
  });

  // 외부 링크 열기
  ipcMain.handle('shell:openExternal', async (event, url: string) => {
    try {
      await shell.openExternal(url);
      console.log(`외부 링크 열기: ${url}`);
    } catch (error) {
      console.error('외부 링크 열기 실패:', error);
    }
  });

  // YouTube 자막 추출 (yt-dlp 사용)
  // Google 차단 감지 함수
  function isGoogleBlocked(text: string): boolean {
    const blockedKeywords = [
      'automated queries',
      'Sorry...',
      'We\'re sorry',
      'protect our users',
      "can't process your request",
      'network may be sending',
      'verdana, arial, sans-serif',
      'GoogleSorry',
      'Google Help for more information',
      'Google Home'
    ];
    
    return blockedKeywords.some(keyword => 
      text.toLowerCase().includes(keyword.toLowerCase())
    );
  }

  // 유튜브 원시 자막 데이터 파싱 함수
  function parseYouTubeRawSubtitles(rawText: string): string {
    try {
      console.log(`🔍 [파싱] 원시 데이터 분석 시작 (${rawText.length}자)`);
      console.log(`🔍 [파싱] 데이터 샘플: ${rawText.substring(0, 300)}...`);
      
      const subtitleTexts: string[] = [];
      
      // 방법 1: 간단한 split 방식으로 segs utf8 찾기
      const segments = rawText.split('segs utf8');
      console.log(`🔍 [파싱] segs utf8로 분할: ${segments.length}개 세그먼트`);
      
      for (let i = 1; i < segments.length; i++) { // 첫 번째는 메타데이터이므로 제외
        let segment = segments[i].trim();
        
        // 다음 tStartMs까지만 자르기
        const nextTimestamp = segment.indexOf('tStartMs');
        if (nextTimestamp > 0) {
          segment = segment.substring(0, nextTimestamp);
        }
        
        // 앞뒤 공백, 쉼표 제거
        segment = segment.replace(/^[\s,]+|[\s,]+$/g, '');
        
        if (segment && segment.length > 1) {
          subtitleTexts.push(segment);
          console.log(`🔍 [파싱] 세그먼트 ${i}: "${segment}"`);
        }
      }
      
      // 방법 2: 세그먼트가 없으면 한국어 텍스트 직접 추출
      if (subtitleTexts.length === 0) {
        console.log(`🔍 [파싱] 대체 방법: 한국어 텍스트 직접 추출`);
        
        // 한국어 문장 패턴 추출 (더 넓은 범위)
        const koreanPattern = /[가-힣][가-힣\s\d?!.,()~]+[가-힣?!.]/g;
        const matches = rawText.match(koreanPattern);
        
        if (matches) {
          console.log(`🔍 [파싱] 한국어 패턴 ${matches.length}개 발견`);
          for (const match of matches) {
            const cleaned = match.trim();
            // 메타데이터 키워드가 포함되지 않은 것만
            if (cleaned.length > 3 && 
                !cleaned.includes('wireMagic') && 
                !cleaned.includes('tStartMs') &&
                !cleaned.includes('dDurationMs') &&
                !cleaned.includes('pb3')) {
              subtitleTexts.push(cleaned);
              console.log(`🔍 [파싱] 한국어 텍스트: "${cleaned}"`);
            }
          }
        }
      }
      
      // 결과 조합
      const result = subtitleTexts.join(' ').replace(/\s+/g, ' ').trim();
      
      console.log(`📝 [파싱] 최종 결과: ${subtitleTexts.length}개 세그먼트, ${result.length}자`);
      console.log(`📝 [파싱] 최종 텍스트: ${result.substring(0, 150)}...`);
      
      return result;
      
    } catch (error) {
      console.error('❌ [파싱] 원시 자막 데이터 파싱 실패:', error);
      return rawText; // 실패 시 원본 반환
    }
  }

  ipcMain.handle('youtube:extractSubtitles', async (event, videoId: string, language = 'ko') => {
    console.log(`🔍 [메인 프로세스] yt-dlp로 자막 추출 시도: ${videoId} (우선 언어: ${language})`);
    
    try {
      const ytDlpWrap = new YTDlpWrap();
      const videoUrl = `https://www.youtube.com/watch?v=${videoId}`;
      
      console.log(`📹 [메인 프로세스] 비디오 메타데이터 가져오는 중: ${videoId}`);
      const metadata = await ytDlpWrap.getVideoInfo(videoUrl);
      
      // 한국어 자막 먼저 시도 (수동 업로드)
      if (metadata.subtitles && metadata.subtitles.ko) {
        console.log(`✅ [메인 프로세스] 한국어 수동 자막 발견`);
        const koSubUrl = metadata.subtitles.ko[0].url;
        const response = await fetch(koSubUrl);
        let subtitleText = await response.text();
        
        // Google 차단 감지
        if (isGoogleBlocked(subtitleText)) {
          console.error(`❌ [메인 프로세스] Google 차단 감지 - 수동 자막`);
          throw new Error('Google에서 자동화 요청을 차단했습니다. 잠시 후 다시 시도해주세요.');
        }
        
        // 원시 데이터 형식인지 확인하고 파싱
        console.log(`🔍 [메인 프로세스] 자막 데이터 형식 검사: ${subtitleText.substring(0, 100)}...`);
        console.log(`🔍 [메인 프로세스] wireMagic 포함: ${subtitleText.includes('wireMagic')}`);
        console.log(`🔍 [메인 프로세스] tStartMs 포함: ${subtitleText.includes('tStartMs')}`);
        console.log(`🔍 [메인 프로세스] segs utf8 포함: ${subtitleText.includes('segs utf8')}`);
        
        if (subtitleText.includes('wireMagic') || subtitleText.includes('tStartMs') || subtitleText.includes('segs utf8')) {
          console.log(`🔄 [메인 프로세스] 원시 자막 데이터 감지! 파싱 시작...`);
          const originalLength = subtitleText.length;
          subtitleText = parseYouTubeRawSubtitles(subtitleText);
          console.log(`🔄 [메인 프로세스] 파싱 완료: ${originalLength}자 → ${subtitleText.length}자`);
        } else {
          console.log(`✅ [메인 프로세스] 일반 자막 형식 (파싱 불필요)`);
        }
        
        if (subtitleText.length >= 300) {
          console.log(`✅ [메인 프로세스] 한국어 수동 자막 추출 성공: ${subtitleText.length}자`);
          return {
            success: true,
            data: {
              language: 'ko',
              text: subtitleText,
              isAutoGenerated: false,
              length: subtitleText.length
            }
          };
        }
      }
      
      // 한국어 자동 생성 자막 시도 (여러 포맷 순서대로)
      if (metadata.automatic_captions && metadata.automatic_captions.ko) {
        console.log(`✅ [메인 프로세스] 한국어 자동 자막 발견`);
        
        // 포맷 우선순위: srt → vtt (깔끔한 포맷만 사용)
        const formatPriority = ['srt', 'vtt'];
        
        for (const format of formatPriority) {
          const subtitleFile = metadata.automatic_captions.ko.find((sub: any) => sub.ext === format);
          if (subtitleFile) {
            try {
              console.log(`🔄 [메인 프로세스] 한국어 ${format} 포맷 시도`);
              const response = await fetch(subtitleFile.url);
              let subtitleText = await response.text();
              
              // Google 차단 감지
              if (isGoogleBlocked(subtitleText)) {
                console.error(`❌ [메인 프로세스] Google 차단 감지 - ${format} 자막`);
                throw new Error('Google에서 자동화 요청을 차단했습니다. 잠시 후 다시 시도해주세요.');
              }
              
              // 원시 데이터 형식인지 확인하고 파싱
              console.log(`🔍 [메인 프로세스] ${format} 자막 데이터 형식 검사: ${subtitleText.substring(0, 100)}...`);
              console.log(`🔍 [메인 프로세스] ${format} wireMagic 포함: ${subtitleText.includes('wireMagic')}`);
              console.log(`🔍 [메인 프로세스] ${format} tStartMs 포함: ${subtitleText.includes('tStartMs')}`);
              console.log(`🔍 [메인 프로세스] ${format} segs utf8 포함: ${subtitleText.includes('segs utf8')}`);
              
              if (subtitleText.includes('wireMagic') || subtitleText.includes('tStartMs') || subtitleText.includes('segs utf8')) {
                console.log(`🔄 [메인 프로세스] ${format} 원시 자막 데이터 감지! 파싱 시작...`);
                const originalLength = subtitleText.length;
                const parsedText = parseYouTubeRawSubtitles(subtitleText);
                console.log(`🔄 [메인 프로세스] ${format} 파싱 완료: ${originalLength}자 → ${parsedText.length}자`);
                
                if (parsedText.length >= 300) {
                  return {
                    success: true,
                    data: {
                      language: 'ko',
                      text: parsedText,
                      isAutoGenerated: true,
                      length: parsedText.length
                    }
                  };
                }
                continue; // 원시 데이터는 일반 파싱을 건너뛰고 다음 포맷 시도
              } else {
                console.log(`✅ [메인 프로세스] ${format} 일반 자막 형식 (파싱 불필요)`);
              }
              
              let textOnly = '';
              
              if (format === 'srt') {
                // SRT 포맷 파싱
                const lines = subtitleText
                  .split('\n')
                  .filter(line => !line.includes('-->') && 
                                 !line.match(/^\d+$/) && 
                                 line.trim() !== '')
                  .map(line => line.replace(/<[^>]*>/g, '').trim())
                  .filter(line => line.length > 0);
                
                const uniqueLines = [...new Set(lines)];
                textOnly = uniqueLines.join(' ').replace(/\s+/g, ' ').trim();
                
              } else if (format === 'vtt') {
                // VTT 포맷 파싱
                const lines = subtitleText
                  .split('\n')
                  .filter(line => !line.startsWith('WEBVTT') && 
                                 !line.startsWith('Kind:') && 
                                 !line.startsWith('Language:') && 
                                 !line.includes('-->') && 
                                 !line.match(/^\d+$/) && 
                                 line.trim() !== '')
                  .map(line => line.replace(/<[^>]*>/g, '').trim())
                  .filter(line => line.length > 0);
                
                const uniqueLines = [...new Set(lines)];
                textOnly = uniqueLines.join(' ').replace(/\s+/g, ' ').trim();
                
              }
              
              if (textOnly.length >= 300) {
                console.log(`✅ [메인 프로세스] 한국어 ${format} 자막 추출 성공: ${textOnly.length}자`);
                return {
                  success: true,
                  data: {
                    language: 'ko',
                    text: textOnly,
                    isAutoGenerated: true,
                    length: textOnly.length
                  }
                };
              } else {
                console.warn(`⚠️ [메인 프로세스] 한국어 ${format} 자막이 너무 짧음: ${textOnly.length}자`);
              }
              
            } catch (error) {
              console.warn(`⚠️ [메인 프로세스] 한국어 ${format} 처리 실패:`, error.message);
              continue;
            }
          }
        }
      }
      
      
      // 모든 시도 실패 (한국어 자막만 시도)
      console.error(`❌ [메인 프로세스] 한국어 자막 추출 실패: ${videoId} - 사용 가능한 한국어 자막이 없거나 너무 짧음`);
      return {
        success: false,
        message: '한국어 자막이 없거나 300자 미만입니다.',
        data: null
      };
      
    } catch (error) {
      console.error(`❌ [메인 프로세스] yt-dlp 자막 추출 오류 (${videoId}):`, error);
      return {
        success: false,
        message: `자막 추출 중 오류: ${error.message}`,
        data: null
      };
    }
  });

};


// This allows TypeScript to pick up the magic constants that's auto-generated by Forge's Webpack
// plugin that tells the Electron app where to look for the Webpack-bundled app code (depending on
// whether you're running in development or production).
declare const MAIN_WINDOW_WEBPACK_ENTRY: string;
declare const MAIN_WINDOW_PRELOAD_WEBPACK_ENTRY: string;

// Handle creating/removing shortcuts on Windows when installing/uninstalling.
if (require('electron-squirrel-startup')) {
  app.quit();
}

const createWindow = (): void => {
  // Create the browser window.
  const mainWindow = new BrowserWindow({
    height: 800,
    width: 1200,
    webPreferences: {
      preload: MAIN_WINDOW_PRELOAD_WEBPACK_ENTRY,
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: false, // 외부 API 호출 허용
      allowRunningInsecureContent: true,
    },
  });

  // CSP 헤더 제거
  mainWindow.webContents.session.webRequest.onHeadersReceived((details, callback) => {
    callback({
      responseHeaders: {
        ...details.responseHeaders,
        'Content-Security-Policy': [''],
      },
    });
  });

  // and load the index.html of the app.
  mainWindow.loadURL(MAIN_WINDOW_WEBPACK_ENTRY);

  // Open the DevTools.
  mainWindow.webContents.openDevTools();
};

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.on('ready', () => {
  setupIpcHandlers();
  createWindow();
});

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  // On OS X it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open.
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// In this file you can include the rest of your app's specific main process
// code. You can also put them in separate files and import them here.
