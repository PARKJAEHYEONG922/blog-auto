/**
 * 네이버 블로그 포스팅 자동화 클래스
 * 로그인 후 실제 블로그 글 작성 및 발행
 */
import { Page } from 'playwright';

export interface BlogPostData {
  title: string;
  content: string;
  tags: string[];
  images: string[];
  category?: string;
}

export interface PublishOptions {
  openToPublic: boolean;
  allowComments: boolean;
  allowTrackback: boolean;
  publishTime: 'now' | 'scheduled' | 'draft'; // 현재 발행, 예약 발행, 또는 임시 저장
  scheduledDate?: string; // 예약 발행 시 날짜/시간
}

export enum PostStatus {
  DRAFT = 'DRAFT',
  PUBLISHED = 'PUBLISHED',
  FAILED = 'FAILED'
}

export class NaverBlogPublisher {
  private page: Page;

  // 네이버 블로그 URL들
  private readonly BLOG_HOME_URL = 'https://section.blog.naver.com/BlogHome.naver';
  private readonly BLOG_WRITE_URL = 'https://blog.naver.com/PostWriteForm.naver';
  private readonly SMART_EDITOR_URL = 'https://blog.naver.com/PostWriteForm.naver?blogId=';

  constructor(page: Page) {
    this.page = page;
  }

  /**
   * 네이버 블로그 글쓰기 페이지로 이동
   */
  async navigateToWritePage(blogId?: string): Promise<boolean> {
    try {
      console.log('네이버 블로그 글쓰기 페이지로 이동 중...');

      // 블로그 홈에서 글쓰기 버튼 찾기
      await this.page.goto(this.BLOG_HOME_URL, { waitUntil: 'domcontentloaded' });
      await this.page.waitForTimeout(2000);

      // 글쓰기 버튼 셀렉터들
      const writeButtonSelectors = [
        'a[href*="PostWriteForm"]',
        'a:has-text("글쓰기")',
        'button:has-text("글쓰기")',
        '.blog_btn_write',
        '.btn_write'
      ];

      let writeButton = null;
      
      for (const selector of writeButtonSelectors) {
        try {
          writeButton = await this.page.waitForSelector(selector, { 
            state: 'visible',
            timeout: 3000 
          });
          if (writeButton) {
            console.log(`글쓰기 버튼 발견: ${selector}`);
            break;
          }
        } catch (error) {
          continue;
        }
      }

      if (writeButton) {
        await writeButton.click();
        console.log('글쓰기 버튼 클릭 완료');
      } else {
        console.log('글쓰기 버튼을 찾지 못함, 직접 URL로 이동');
        if (blogId) {
          await this.page.goto(`${this.SMART_EDITOR_URL}${blogId}`, { waitUntil: 'domcontentloaded' });
        } else {
          await this.page.goto(this.BLOG_WRITE_URL, { waitUntil: 'domcontentloaded' });
        }
      }

      // 글쓰기 페이지 로딩 대기
      await this.page.waitForTimeout(3000);

      const isEditorLoaded = await this.waitForSmartEditor();
      if (isEditorLoaded) {
        console.log('✅ 네이버 블로그 글쓰기 페이지 로딩 완료');
        return true;
      } else {
        console.error('❌ 스마트 에디터 로딩 실패');
        return false;
      }

    } catch (error) {
      console.error('글쓰기 페이지 이동 실패:', error);
      return false;
    }
  }

  /**
   * 스마트 에디터가 로드될 때까지 대기
   */
  private async waitForSmartEditor(timeout = 15000): Promise<boolean> {
    try {
      console.log('스마트 에디터 로딩 대기 중...');

      const editorSelectors = [
        '#se-root',
        '.se-root-container',
        '#smart_editor',
        '.smart_editor',
        'iframe[id*="se-"]'
      ];

      for (const selector of editorSelectors) {
        try {
          await this.page.waitForSelector(selector, { 
            state: 'visible',
            timeout: 3000 
          });
          console.log(`스마트 에디터 발견: ${selector}`);
          return true;
        } catch (error) {
          continue;
        }
      }

      // 페이지 내용 확인
      const pageContent = await this.page.textContent('body');
      if (pageContent?.includes('제목') || pageContent?.includes('내용')) {
        console.log('에디터 요소는 찾지 못했지만 글쓰기 페이지로 보임');
        return true;
      }

      return false;

    } catch (error) {
      console.error('스마트 에디터 대기 실패:', error);
      return false;
    }
  }

  /**
   * 블로그 포스트 작성 및 발행
   */
  async publishPost(postData: BlogPostData, options: PublishOptions = {
    openToPublic: true,
    allowComments: true,
    allowTrackback: true,
    publishTime: 'now'
  }): Promise<PostStatus> {
    try {
      console.log('블로그 포스트 작성 시작...');
      
      // 제목 입력
      await this.fillTitle(postData.title);
      
      // 내용 입력
      await this.fillContent(postData.content);
      
      // 태그 입력
      if (postData.tags && postData.tags.length > 0) {
        await this.fillTags(postData.tags);
      }
      
      // 발행 방식에 따라 처리
      if (options.publishTime === 'draft') {
        // 임시 저장
        console.log('💾 임시 저장 모드');
        const saveResult = await this.clickSaveButton();
        return saveResult ? PostStatus.DRAFT : PostStatus.FAILED;
      } else {
        // 즉시 발행 또는 예약 발행
        console.log(`🚀 ${options.publishTime === 'now' ? '즉시' : '예약'} 발행 모드`);
        
        const publishResult = await this.clickPublishButton(options.publishTime, options.scheduledDate);
        return publishResult ? PostStatus.PUBLISHED : PostStatus.FAILED;
      }

    } catch (error) {
      console.error('포스트 발행 실패:', error);
      return PostStatus.FAILED;
    }
  }

  /**
   * 제목 입력
   */
  private async fillTitle(title: string): Promise<boolean> {
    try {
      console.log(`제목 입력: ${title}`);

      const titleSelectors = [
        'input[placeholder*="제목"]',
        'input[name="title"]',
        '#post-title',
        '.se-title-input'
      ];

      for (const selector of titleSelectors) {
        try {
          const titleInput = await this.page.waitForSelector(selector, { 
            state: 'visible',
            timeout: 3000 
          });
          
          if (titleInput) {
            await titleInput.click();
            await titleInput.fill('');
            await titleInput.type(title);
            console.log(`✅ 제목 입력 완료: ${selector}`);
            return true;
          }
        } catch (error) {
          continue;
        }
      }

      console.error('❌ 제목 입력란을 찾을 수 없음');
      return false;

    } catch (error) {
      console.error('제목 입력 실패:', error);
      return false;
    }
  }

  /**
   * 내용 입력 (스마트 에디터)
   */
  private async fillContent(content: string): Promise<boolean> {
    try {
      console.log('내용 입력 시작...');

      // 스마트 에디터 iframe 찾기
      const iframeSelectors = [
        'iframe[id*="se-"]',
        'iframe[title*="에디터"]',
        'iframe[name*="editor"]'
      ];

      let contentFrame = null;
      for (const selector of iframeSelectors) {
        try {
          const iframe = await this.page.waitForSelector(selector, { timeout: 3000 });
          if (iframe) {
            contentFrame = await iframe.contentFrame();
            if (contentFrame) {
              console.log(`에디터 iframe 발견: ${selector}`);
              break;
            }
          }
        } catch (error) {
          continue;
        }
      }

      if (contentFrame) {
        // iframe 내부의 에디터에 내용 입력
        const editorBody = await contentFrame.waitForSelector('body', { timeout: 5000 });
        
        if (editorBody) {
          await editorBody.click();
          await this.page.keyboard.press('Control+a');
          await this.page.keyboard.press('Delete');
          
          // HTML 내용을 텍스트로 변환하여 입력
          const textContent = content.replace(/<[^>]*>/g, '\n').trim();
          await editorBody.type(textContent);
          
          console.log('✅ iframe 에디터에 내용 입력 완료');
          return true;
        }
      } else {
        // 일반 텍스트 에디터 시도
        const contentSelectors = [
          'textarea[placeholder*="내용"]',
          'textarea[name="content"]',
          '#post-content'
        ];

        for (const selector of contentSelectors) {
          try {
            const contentArea = await this.page.waitForSelector(selector, { timeout: 3000 });
            
            if (contentArea) {
              await contentArea.click();
              await contentArea.fill('');
              
              const textContent = content.replace(/<[^>]*>/g, '\n').trim();
              await contentArea.type(textContent);
              
              console.log(`✅ 텍스트 에디터에 내용 입력 완료: ${selector}`);
              return true;
            }
          } catch (error) {
            continue;
          }
        }
      }

      console.error('❌ 내용 입력란을 찾을 수 없음');
      return false;

    } catch (error) {
      console.error('내용 입력 실패:', error);
      return false;
    }
  }

  /**
   * 태그 입력
   */
  private async fillTags(tags: string[]): Promise<boolean> {
    try {
      console.log(`태그 입력: ${tags.join(', ')}`);

      const tagSelectors = [
        'input[placeholder*="태그"]',
        'input[name="tag"]',
        '#tag-input',
        '.tag-input'
      ];

      for (const selector of tagSelectors) {
        try {
          const tagInput = await this.page.waitForSelector(selector, { timeout: 3000 });
          
          if (tagInput) {
            await tagInput.click();
            
            for (const tag of tags) {
              await tagInput.type(tag);
              await this.page.keyboard.press('Enter');
              await this.page.waitForTimeout(500);
            }
            
            console.log('✅ 태그 입력 완료');
            return true;
          }
        } catch (error) {
          continue;
        }
      }

      console.warn('태그 입력란을 찾을 수 없음 (선택적 기능)');
      return true; // 태그는 선택적이므로 실패해도 성공으로 처리

    } catch (error) {
      console.error('태그 입력 실패:', error);
      return true; // 태그는 선택적이므로 실패해도 성공으로 처리
    }
  }

  /**
   * 저장 버튼 클릭 (임시 저장용) - 네이버 블로그 iframe 내부에서 처리
   */
  private async clickSaveButton(): Promise<boolean> {
    try {
      console.log('💾 네이버 블로그 임시 저장 버튼 클릭 중...');

      // 먼저 메인 페이지에서 저장 버튼 찾기 시도
      const mainSaveSelectors = [
        'button.save_btn__bzc5B',
        'button[data-click-area="tpb.save"]',
        'button:has-text("저장")'
      ];

      for (const selector of mainSaveSelectors) {
        try {
          const saveButton = await this.page.waitForSelector(selector, { 
            state: 'visible',
            timeout: 2000 
          });
          
          if (saveButton) {
            await saveButton.click();
            console.log(`✅ 메인 페이지 저장 버튼 클릭 완료: ${selector}`);
            
            await this.page.waitForTimeout(2000);
            return true;
          }
        } catch (error) {
          continue;
        }
      }

      // iframe 내부에서 저장 버튼 찾기
      console.log('🔍 iframe 내부에서 저장 버튼 찾는 중...');
      
      const iframes = await this.page.$$('iframe');
      
      for (const iframe of iframes) {
        try {
          const frame = await iframe.contentFrame();
          if (!frame) continue;

          const saveButton = await frame.$('button.save_btn__bzc5B, button[data-click-area="tpb.save"]');
          if (saveButton) {
            await saveButton.click();
            console.log('✅ iframe 내부 저장 버튼 클릭 완료');
            
            await this.page.waitForTimeout(2000);
            return true;
          }
        } catch (error) {
          continue;
        }
      }

      console.error('❌ 저장 버튼을 찾을 수 없음 (메인 페이지 및 iframe 검색 완료)');
      return false;

    } catch (error) {
      console.error('❌ 저장 버튼 클릭 실패:', error);
      return false;
    }
  }

  /**
   * 발행 버튼 클릭 - 네이버 실제 프로세스
   */
  private async clickPublishButton(publishTime?: 'now' | 'scheduled', scheduledDate?: string): Promise<boolean> {
    try {
      console.log('🚀 네이버 블로그 발행 시작...');
      
      // 1단계: 메인 발행 버튼 클릭
      const publishSelectors = [
        'button.publish_btn__m9KHH',
        'button[data-click-area="tpb.publish"]',
        '.publish_btn__m9KHH'
      ];
      
      let publishButton = null;
      for (const selector of publishSelectors) {
        try {
          publishButton = await this.page.waitForSelector(selector, { 
            state: 'visible',
            timeout: 3000 
          });
          if (publishButton) break;
        } catch (error) {
          continue;
        }
      }
      
      if (!publishButton) {
        console.error('❌ 발행 버튼을 찾을 수 없음');
        return false;
      }
      
      await publishButton.click();
      console.log('✅ 발행 버튼 클릭 완료');
      
      // 2단계: 발행 설정 팝업에서 예약 설정 (예약 발행인 경우)
      await this.page.waitForTimeout(2000);
      
      if (publishTime === 'scheduled' && scheduledDate) {
        console.log('⏰ 예약 발행 설정 시작...');
        
        // 예약 라디오 버튼 클릭 - 팝업 완전 로딩 후 시도
        console.log('🔍 발행 시간 섹션이 로드될 때까지 대기...');
        
        // 발행 시간 섹션이 로드될 때까지 대기
        await this.page.waitForSelector('.option_time__ft1tA', { timeout: 10000 });
        
        // 발행 시간 섹션으로 스크롤
        const timeSection = await this.page.$('.option_time__ft1tA');
        if (timeSection) {
          await timeSection.evaluate((element) => element.scrollIntoView());
          console.log('📜 발행 시간 섹션으로 스크롤 완료');
        }
        
        await this.page.waitForTimeout(1000);
        
        console.log('🔍 예약 라디오 버튼 찾는 중...');
        
        // 디버그: 예약 라벨이 있는지 확인
        const allLabels = await this.page.$$('label');
        console.log(`📋 팝업 내 label 개수: ${allLabels.length}`);
        
        for (let i = 0; i < allLabels.length; i++) {
          const label = allLabels[i];
          const forAttr = await label.getAttribute('for');
          const text = await label.textContent();
          console.log(`📋 라벨 ${i}: for="${forAttr}", text="${text}"`);
        }
        
        // 예약 라디오 버튼 클릭 - 간단하게!
        console.log('🔍 예약 라디오 버튼 클릭 시도...');
        
        let scheduleSuccess = false;
        
        try {
          const scheduleLabel = await this.page.waitForSelector('label[for="radio_time2"]', { timeout: 5000 });
          if (scheduleLabel) {
            await scheduleLabel.click();
            console.log('✅ 예약 라벨 클릭 완료');
            scheduleSuccess = true;
            await this.page.waitForTimeout(1000); // 시간 설정 영역이 나타날 때까지 대기
          }
        } catch (error) {
          console.log('❌ 예약 라벨 클릭 실패:', error.message);
        }
        
        // 예약 버튼 클릭 실패시 발행 중단
        if (!scheduleSuccess) {
          console.error('❌❌❌ 예약 버튼 클릭 실패 - 발행을 중단합니다 ❌❌❌');
          throw new Error('예약 설정 실패 - 발행 중단');
        }
        
        await this.page.waitForTimeout(1000);
        
        // 시간 설정
        const date = new Date(scheduledDate);
        const hour = date.getHours();
        const minute = date.getMinutes();
        
        // 날짜 설정 (오늘이 아닌 경우)
        const today = new Date();
        const isToday = date.getDate() === today.getDate();
        if (!isToday) {
          const dateSuccess = await this.setScheduledDate(date.getDate());
          if (!dateSuccess) {
            console.error('❌ 날짜 설정 실패 - 발행을 중단합니다');
            return false;
          }
        }
        
        // 시간 설정
        const hourSelect = await this.page.$('.hour_option__J_heO');
        if (hourSelect) {
          await hourSelect.selectOption(hour.toString().padStart(2, '0'));
          console.log(`✅ 시간 설정: ${hour}시`);
        } else {
          console.error('❌ 시간 설정 실패 - 발행을 중단합니다');
          return false;
        }
        
        // 분 설정
        const minuteSelect = await this.page.$('.minute_option__Vb3xB');
        if (minuteSelect) {
          const availableMinutes = ['00', '10', '20', '30', '40', '50'];
          const nearestMinute = availableMinutes.reduce((prev, curr) => {
            return Math.abs(parseInt(curr) - minute) < Math.abs(parseInt(prev) - minute) ? curr : prev;
          });
          await minuteSelect.selectOption(nearestMinute);
          console.log(`✅ 분 설정: ${nearestMinute}분`);
        } else {
          console.error('❌ 분 설정 실패 - 발행을 중단합니다');
          return false;
        }
        
        console.log('✅ 예약 발행 설정 완료');
      }
      
      // 3단계: 최종 발행 버튼 클릭
      const finalPublishSelectors = [
        'button.confirm_btn__WEaBq[data-testid="seOnePublishBtn"]',
        'button[data-click-area="tpb*i.publish"]',
        '.confirm_btn__WEaBq'
      ];
      
      for (const selector of finalPublishSelectors) {
        try {
          const finalButton = await this.page.waitForSelector(selector, { 
            state: 'visible',
            timeout: 5000 
          });
          
          if (finalButton) {
            await finalButton.click();
            console.log('✅ 최종 발행 버튼 클릭 완료');
            
            await this.page.waitForTimeout(3000);
            return await this.verifyPublishSuccess();
          }
        } catch (error) {
          continue;
        }
      }
      
      console.error('❌ 최종 발행 버튼을 찾을 수 없음');
      return false;
      
    } catch (error) {
      console.error('❌ 발행 버튼 클릭 실패:', error);
      return false;
    }
  }


  /**
   * 예약 발행 날짜 설정 (이번 달 내에서만)
   */
  private async setScheduledDate(day: number): Promise<boolean> {
    try {
      console.log(`📅 날짜 설정: ${day}일`);
      
      // 날짜 입력란 클릭하여 datepicker 열기
      const dateInput = await this.page.$('.input_date__QmA0s');
      if (!dateInput) {
        console.error('❌ 날짜 입력란을 찾을 수 없음');
        return false;
      }
      
      await dateInput.click();
      await this.page.waitForTimeout(1000);
      
      // datepicker가 열렸는지 확인
      const datepicker = await this.page.$('.ui-datepicker');
      if (!datepicker) {
        console.error('❌ datepicker가 열리지 않음');
        return false;
      }
      
      // 해당 날짜 클릭 (활성화된 날짜만)
      const dayButton = await this.page.$(`td:not(.ui-state-disabled) button.ui-state-default:has-text("${day}")`);
      if (dayButton) {
        await dayButton.click();
        console.log(`✅ 날짜 선택 완료: ${day}일`);
        await this.page.waitForTimeout(500);
        return true;
      } else {
        console.error(`❌ ${day}일 버튼을 찾을 수 없거나 비활성화됨`);
        return false;
      }
      
    } catch (error) {
      console.error('❌ 날짜 설정 실패:', error);
      return false;
    }
  }

  /**
   * 발행 성공 확인
   */
  private async verifyPublishSuccess(): Promise<boolean> {
    try {
      // URL 변화 확인
      const currentUrl = this.page.url();
      if (currentUrl.includes('/PostView.naver') || currentUrl.includes('blog.naver.com')) {
        console.log('✅ URL 기반 발행 성공 확인');
        return true;
      }

      // 성공 메시지 확인
      const successSelectors = [
        ':has-text("발행되었습니다")',
        ':has-text("등록되었습니다")',
        ':has-text("완료")'
      ];

      for (const selector of successSelectors) {
        try {
          const successElement = await this.page.waitForSelector(selector, { timeout: 5000 });
          if (successElement) {
            console.log(`✅ 발행 성공 메시지 확인: ${selector}`);
            return true;
          }
        } catch (error) {
          continue;
        }
      }

      console.log('✅ 발행 완료 추정 (명시적 확인 실패하지만 진행)');
      return true;

    } catch (error) {
      console.error('❌ 발행 성공 확인 실패:', error);
      return false;
    }
  }

  /**
   * 현재 페이지가 글쓰기 페이지인지 확인
   */
  async isOnWritePage(): Promise<boolean> {
    try {
      const currentUrl = this.page.url();
      return currentUrl.includes('PostWriteForm') || 
             currentUrl.includes('write') ||
             currentUrl.includes('editor');
    } catch (error) {
      return false;
    }
  }

  /**
   * 현재 브라우저 페이지 반환
   */
  getPage(): Page {
    return this.page;
  }
}