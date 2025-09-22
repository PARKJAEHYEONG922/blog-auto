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

      // 글쓰기 버튼 셀렉터들 (네이버 블로그 UI에 따라 달라질 수 있음)
      const writeButtonSelectors = [
        'a[href*="PostWriteForm"]',
        'a:has-text("글쓰기")',
        'button:has-text("글쓰기")',
        '.blog_btn_write',
        '.btn_write',
        'a[title="글쓰기"]',
        '[data-testid="write-button"]'
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
          console.debug(`셀렉터 시도 실패: ${selector}`);
          continue;
        }
      }

      if (writeButton) {
        // 글쓰기 버튼 클릭
        await writeButton.click();
        console.log('글쓰기 버튼 클릭 완료');
      } else {
        // 버튼을 찾지 못하면 직접 URL로 이동
        console.log('글쓰기 버튼을 찾지 못함, 직접 URL로 이동');
        
        if (blogId) {
          await this.page.goto(`${this.SMART_EDITOR_URL}${blogId}`, { waitUntil: 'domcontentloaded' });
        } else {
          await this.page.goto(this.BLOG_WRITE_URL, { waitUntil: 'domcontentloaded' });
        }
      }

      // 글쓰기 페이지 로딩 대기
      await this.page.waitForTimeout(3000);

      // 스마트 에디터가 로드되었는지 확인
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

      // 스마트 에디터 관련 셀렉터들
      const editorSelectors = [
        '#se-root',
        '.se-root-container',
        '#smart_editor',
        '.smart_editor',
        'iframe[id*="se-"]',
        '[data-module="SE"]',
        '.se-main-container'
      ];

      let editorFound = false;

      for (const selector of editorSelectors) {
        try {
          await this.page.waitForSelector(selector, { 
            state: 'visible',
            timeout: 3000 
          });
          console.log(`스마트 에디터 발견: ${selector}`);
          editorFound = true;
          break;
        } catch (error) {
          console.debug(`에디터 셀렉터 실패: ${selector}`);
          continue;
        }
      }

      if (!editorFound) {
        // 페이지 내용 확인
        const pageContent = await this.page.textContent('body');
        if (pageContent?.includes('제목') || pageContent?.includes('내용')) {
          console.log('에디터 요소는 찾지 못했지만 글쓰기 페이지로 보임');
          editorFound = true;
        }
      }

      return editorFound;

    } catch (error) {
      console.error('스마트 에디터 대기 실패:', error);
      return false;
    }
  }

  /**
   * 작성 중인 글 팝업 처리 (기존 초안이 있을 때)
   */
  async handleDraftPopup(): Promise<boolean> {
    try {
      console.log('작성 중인 글 팝업 확인 중...');

      // 팝업 대기 (짧은 시간)
      const popup = await this.page.waitForSelector('.se-popup-container, div[data-layerid], .popup-layer', { 
        state: 'visible',
        timeout: 3000 
      }).catch(() => null);

      if (!popup) {
        console.log('작성 중인 글 팝업 없음');
        return true;
      }

      // 팝업 내용 확인
      const popupText = await popup.textContent();
      if (!popupText?.includes('작성 중인 글')) {
        console.log('다른 종류의 팝업 - 무시');
        return true;
      }

      console.log('작성 중인 글 팝업 발견, 새 글 작성 선택');

      // 새 글 작성 버튼 찾기
      const newPostSelectors = [
        'button:has-text("새 글 작성")',
        'button:has-text("취소")',
        '.se-popup-button-cancel',
        '[data-action="new"]'
      ];

      for (const selector of newPostSelectors) {
        try {
          const button = await popup.$(selector);
          if (button) {
            await button.click();
            console.log(`새 글 작성 버튼 클릭: ${selector}`);
            await this.page.waitForTimeout(1000);
            return true;
          }
        } catch (error) {
          continue;
        }
      }

      console.warn('새 글 작성 버튼을 찾지 못함');
      return false;

    } catch (error) {
      console.error('팝업 처리 실패:', error);
      return false;
    }
  }

  /**
   * 블로그 포스트 작성 및 발행
   */
  async publishPost(postData: BlogPostData, options: PublishOptions = {
    openToPublic: true,
    allowComments: true,
    allowTrackback: true
  }): Promise<PostStatus> {
    try {
      console.log('블로그 포스트 작성 시작...');
      
      // 작성 중인 글 팝업 처리
      await this.handleDraftPopup();
      
      // 제목 입력
      await this.fillTitle(postData.title);
      
      // 내용 입력
      await this.fillContent(postData.content);
      
      // 태그 입력
      if (postData.tags && postData.tags.length > 0) {
        await this.fillTags(postData.tags);
      }
      
      // 발행 설정
      await this.configurePublishSettings(options);
      
      // 발행 버튼 클릭
      const publishResult = await this.clickPublishButton();
      
      if (publishResult) {
        console.log('✅ 블로그 포스트 발행 완료');
        return PostStatus.PUBLISHED;
      } else {
        console.error('❌ 블로그 포스트 발행 실패');
        return PostStatus.FAILED;
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
        '.se-title-input',
        'input[data-testid="title"]'
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
        await this.fillContentInIframe(contentFrame, content);
        return true;
      } else {
        // iframe이 없으면 일반 텍스트 에디터 시도
        return await this.fillContentInTextarea(content);
      }

    } catch (error) {
      console.error('내용 입력 실패:', error);
      return false;
    }
  }

  /**
   * iframe 내부 에디터에 내용 입력
   */
  private async fillContentInIframe(frame: any, content: string): Promise<boolean> {
    try {
      // 에디터 body 찾기
      const editorBody = await frame.waitForSelector('body', { timeout: 5000 });
      
      if (editorBody) {
        // 기존 내용 삭제 후 새 내용 입력
        await editorBody.click();
        await frame.keyboard.press('Control+a');
        await frame.keyboard.press('Delete');
        
        // HTML 내용을 텍스트로 변환하여 입력
        const textContent = content.replace(/<[^>]*>/g, '\n').trim();
        await editorBody.type(textContent);
        
        console.log('✅ iframe 에디터에 내용 입력 완료');
        return true;
      }

      return false;
    } catch (error) {
      console.error('iframe 내용 입력 실패:', error);
      return false;
    }
  }

  /**
   * 일반 텍스트 에디터에 내용 입력
   */
  private async fillContentInTextarea(content: string): Promise<boolean> {
    try {
      const contentSelectors = [
        'textarea[placeholder*="내용"]',
        'textarea[name="content"]',
        '#post-content',
        '.se-content-area textarea',
        '[data-testid="content"]'
      ];

      for (const selector of contentSelectors) {
        try {
          const contentArea = await this.page.waitForSelector(selector, { timeout: 3000 });
          
          if (contentArea) {
            await contentArea.click();
            await contentArea.fill('');
            
            // HTML을 텍스트로 변환
            const textContent = content.replace(/<[^>]*>/g, '\n').trim();
            await contentArea.type(textContent);
            
            console.log(`✅ 텍스트 에디터에 내용 입력 완료: ${selector}`);
            return true;
          }
        } catch (error) {
          continue;
        }
      }

      console.error('❌ 내용 입력란을 찾을 수 없음');
      return false;

    } catch (error) {
      console.error('텍스트 에디터 내용 입력 실패:', error);
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
            
            // 각 태그를 하나씩 입력
            for (const tag of tags) {
              await tagInput.type(tag);
              await this.page.keyboard.press('Enter'); // 태그 구분
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
   * 발행 설정 구성
   */
  private async configurePublishSettings(options: PublishOptions): Promise<boolean> {
    try {
      console.log('발행 설정 구성 중...');

      // 공개 설정
      if (options.openToPublic) {
        const publicRadio = await this.page.$('input[value="public"], input[value="전체공개"]');
        if (publicRadio) {
          await publicRadio.click();
          console.log('공개 설정: 전체공개');
        }
      }

      // 댓글 허용 설정
      if (options.allowComments) {
        const commentCheckbox = await this.page.$('input[name*="comment"], input[id*="comment"]');
        if (commentCheckbox && !(await commentCheckbox.isChecked())) {
          await commentCheckbox.click();
          console.log('댓글 허용 설정');
        }
      }

      return true;

    } catch (error) {
      console.error('발행 설정 실패:', error);
      return true; // 설정은 선택적이므로 실패해도 계속 진행
    }
  }

  /**
   * 발행 버튼 클릭
   */
  private async clickPublishButton(): Promise<boolean> {
    try {
      console.log('발행 버튼 클릭 중...');

      const publishSelectors = [
        'button:has-text("발행")',
        'button:has-text("완료")',
        'button[type="submit"]',
        '.btn-publish',
        '#publish-btn',
        '[data-testid="publish"]'
      ];

      for (const selector of publishSelectors) {
        try {
          const publishButton = await this.page.waitForSelector(selector, { 
            state: 'visible',
            timeout: 3000 
          });
          
          if (publishButton) {
            await publishButton.click();
            console.log(`발행 버튼 클릭: ${selector}`);
            
            // 발행 완료 대기
            await this.page.waitForTimeout(3000);
            
            // 발행 완료 확인
            const isPublished = await this.verifyPublishSuccess();
            return isPublished;
          }
        } catch (error) {
          continue;
        }
      }

      console.error('❌ 발행 버튼을 찾을 수 없음');
      return false;

    } catch (error) {
      console.error('발행 버튼 클릭 실패:', error);
      return false;
    }
  }

  /**
   * 발행 성공 확인
   */
  private async verifyPublishSuccess(): Promise<boolean> {
    try {
      // URL 변화 확인 (발행 후 포스트 페이지로 이동)
      const currentUrl = this.page.url();
      if (currentUrl.includes('/PostView.naver') || currentUrl.includes('blog.naver.com')) {
        console.log('✅ URL 기반 발행 성공 확인');
        return true;
      }

      // 성공 메시지 확인
      const successSelectors = [
        ':has-text("발행되었습니다")',
        ':has-text("등록되었습니다")',
        ':has-text("완료")',
        '.success-message'
      ];

      for (const selector of successSelectors) {
        try {
          const successElement = await this.page.waitForSelector(selector, { timeout: 5000 });
          if (successElement) {
            console.log(`성공 메시지 확인: ${selector}`);
            return true;
          }
        } catch (error) {
          continue;
        }
      }

      // 페이지 제목으로 확인
      const pageTitle = await this.page.title();
      if (pageTitle.includes('포스트') || pageTitle.includes('블로그')) {
        console.log('페이지 제목 기반 발행 성공 추정');
        return true;
      }

      console.warn('발행 성공을 명확히 확인할 수 없음');
      return false;

    } catch (error) {
      console.error('발행 성공 확인 실패:', error);
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