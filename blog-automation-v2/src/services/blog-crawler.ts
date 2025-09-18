import { SelectedBlogTitle } from './blog-title-selector';

export interface BlogContent {
  url: string;
  title: string;
  textContent: string;
  contentLength: number;
  imageCount: number;
  gifCount: number;
  videoCount: number;
  tags: string[];
  success: boolean;
  error?: string;
}

export interface CrawlingProgress {
  current: number;
  total: number;
  url: string;
  status: 'crawling' | 'success' | 'failed';
}

export class BlogCrawler {
  private progressCallback?: (progress: CrawlingProgress) => void;

  constructor(progressCallback?: (progress: CrawlingProgress) => void) {
    this.progressCallback = progressCallback;
  }

  async crawlSelectedBlogs(selectedBlogs: SelectedBlogTitle[], targetSuccessCount = 3): Promise<BlogContent[]> {
    const results: BlogContent[] = [];
    let successCount = 0;
    let processedCount = 0;
    
    console.log(`📝 선별된 블로그에서 유효한 콘텐츠 ${targetSuccessCount}개 크롤링 시작 (총 ${selectedBlogs.length}개 중)`);
    
    // 유효한 블로그를 targetSuccessCount개 찾을 때까지 또는 모든 블로그를 확인할 때까지 진행
    for (let i = 0; i < selectedBlogs.length && successCount < targetSuccessCount; i++) {
      const blog = selectedBlogs[i];
      processedCount++;
      
      // 진행률 콜백 호출 (목표 개수 기준으로 계산)
      if (this.progressCallback) {
        this.progressCallback({
          current: Math.min(successCount + 1, targetSuccessCount),
          total: targetSuccessCount,
          url: blog.url,
          status: 'crawling'
        });
      }
      
      try {
        console.log(`🔍 [${processedCount}/${selectedBlogs.length}] 크롤링 시작: ${blog.title} (유효 수집: ${successCount}/${targetSuccessCount})`);
        console.log(`🔗 URL: ${blog.url}`);
        
        const content = await this.crawlBlogContent(blog.url, blog.title);
        console.log(`📊 크롤링 원시 결과 - 제목: "${content.title}", 성공: ${content.success}, 오류: ${content.error || 'none'}`);
        
        // 콘텐츠 필터링 적용
        if (content.success && this.shouldFilterContent(content)) {
          console.log(`⚠️ [${processedCount}/${selectedBlogs.length}] 콘텐츠 필터링됨: ${blog.title}`);
          content.success = false;
          content.error = '광고/협찬 글이거나 품질이 낮은 콘텐츠입니다';
        }
        
        results.push(content);
        
        if (content.success) {
          successCount++;
          console.log(`✅ [${processedCount}/${selectedBlogs.length}] 크롤링 완료: ${content.contentLength}자, 이미지 ${content.imageCount}개 (유효 수집: ${successCount}/${targetSuccessCount})`);
          
          // 성공 콜백
          if (this.progressCallback) {
            this.progressCallback({
              current: successCount,
              total: targetSuccessCount,
              url: blog.url,
              status: 'success'
            });
          }
        } else {
          console.log(`⚠️ [${processedCount}/${selectedBlogs.length}] 필터링됨, 다음 블로그 시도: ${content.error}`);
          
          // 실패 콜백 (하지만 계속 진행)
          if (this.progressCallback) {
            this.progressCallback({
              current: Math.min(successCount + 1, targetSuccessCount),
              total: targetSuccessCount,
              url: blog.url,
              status: 'failed'
            });
          }
        }
        
        // 요청 간 딜레이 (과부하 방지)
        if (i < selectedBlogs.length - 1 && successCount < targetSuccessCount) {
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
        
      } catch (error) {
        console.error(`❌ [${processedCount}/${selectedBlogs.length}] 크롤링 실패: ${blog.url}`, error);
        
        // 실패한 경우에도 결과에 포함 (빈 콘텐츠로)
        results.push({
          url: blog.url,
          title: blog.title,
          textContent: '',
          contentLength: 0,
          imageCount: 0,
          gifCount: 0,
          videoCount: 0,
          tags: [],
          success: false,
          error: error.message || '크롤링 실패'
        });
        
        // 실패 콜백
        if (this.progressCallback) {
          this.progressCallback({
            current: Math.min(successCount + 1, targetSuccessCount),
            total: targetSuccessCount,
            url: blog.url,
            status: 'failed'
          });
        }
      }
    }
    
    console.log(`🎯 블로그 크롤링 완료: ${successCount}/${targetSuccessCount} 목표 달성 (총 ${processedCount}개 시도)`);
    
    if (successCount < targetSuccessCount) {
      console.warn(`⚠️ 목표한 유효 블로그 수(${targetSuccessCount}개)에 못 미침: ${successCount}개만 수집됨`);
    }
    
    return results;
  }

  private async crawlBlogContent(url: string, title: string): Promise<BlogContent> {
    try {
      // 네이버 블로그 URL 검증
      console.log(`🔍 URL 검증: "${url}" (길이: ${url?.length || 0})`);
      
      if (!url || typeof url !== 'string' || url.trim() === '') {
        console.error(`❌ 빈 URL 또는 잘못된 URL 타입: ${JSON.stringify(url)}`);
        return {
          url: url || '',
          title,
          textContent: '',
          contentLength: 0,
          imageCount: 0,
          gifCount: 0,
          videoCount: 0,
          tags: [],
          success: false,
          error: 'URL이 비어있거나 잘못된 형식입니다'
        };
      }
      
      const cleanUrl = url.trim();
      const isNaverBlog = cleanUrl.includes('blog.naver.com');
      const isTistory = cleanUrl.includes('.tistory.com');
      
      if (!isNaverBlog && !isTistory) {
        console.error(`❌ 지원하지 않는 블로그 플랫폼: "${cleanUrl}"`);
        return {
          url: cleanUrl,
          title,
          textContent: '',
          contentLength: 0,
          imageCount: 0,
          gifCount: 0,
          videoCount: 0,
          tags: [],
          success: false,
          error: '네이버 블로그 또는 티스토리만 지원됩니다'
        };
      }

      // User-Agent 설정으로 차단 우회
      const headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
      };

      // 플랫폼별 URL 생성 후 다중 시도
      const urlsToTry = this.generateCrawlingUrls(url, isNaverBlog, isTistory);
      console.log(`🔍 ${isNaverBlog ? '네이버 블로그' : '티스토리'} URL 다중 시도: ${urlsToTry.length}개`);

      for (let i = 0; i < urlsToTry.length; i++) {
        const tryUrl = urlsToTry[i];
        console.log(`🔗 [${i + 1}/${urlsToTry.length}] 시도: ${tryUrl}`);
        
        try {
          const response = await fetch(tryUrl, {
            method: 'GET',
            headers,
            redirect: 'follow'
          });

          if (response.ok) {
            const buffer = await response.arrayBuffer();
            const html = this.decodeWithEncoding(buffer, tryUrl);
            
            console.log(`✅ 성공적으로 HTML 획득 (${html.length}자)`);
            
            // HTML 파싱 및 콘텐츠 추출
            return this.parseHTMLContent(html, url, title, isNaverBlog, isTistory);
          } else {
            console.warn(`⚠️ [${i + 1}/${urlsToTry.length}] HTTP ${response.status}: ${tryUrl}`);
          }
        } catch (error) {
          console.warn(`⚠️ [${i + 1}/${urlsToTry.length}] 요청 실패: ${error.message}`);
        }
      }

      throw new Error('모든 URL 시도 실패');

    } catch (error) {
      console.error(`블로그 크롤링 오류 (${url}):`, error);
      throw error;
    }
  }

  private generateCrawlingUrls(originalUrl: string, isNaverBlog: boolean, isTistory: boolean): string[] {
    const urls: string[] = [];
    
    if (isNaverBlog) {
      // 1. PostView URL 직접 생성 (네이버 블로그 레거시 방식)
      const postViewUrl = this.convertToPostViewUrl(originalUrl);
      if (postViewUrl) {
        urls.push(postViewUrl);
      }
      
      // 2. 원본 URL 폴백
      urls.push(originalUrl);
    } else if (isTistory) {
      // 티스토리는 원본 URL을 그대로 사용
      urls.push(originalUrl);
      
      // 티스토리 모바일 버전도 시도해볼 수 있음
      if (originalUrl.includes('.tistory.com/') && !originalUrl.includes('m.')) {
        const mobileUrl = originalUrl.replace('.tistory.com/', '.tistory.com/m/');
        urls.push(mobileUrl);
      }
    }
    
    return urls;
  }

  private convertToPostViewUrl(blogUrl: string): string | null {
    // 레거시 패턴: https://blog.naver.com/{blogId}/{logNo}
    const pattern = /https:\/\/blog\.naver\.com\/([^\/]+)\/(\d+)/;
    const match = blogUrl.match(pattern);

    if (match) {
      const blogId = match[1];
      const logNo = match[2];
      
      // PostView URL 직접 생성
      return `https://blog.naver.com/PostView.naver?blogId=${blogId}&logNo=${logNo}`;
    }

    // 이미 PostView URL인 경우 그대로 반환
    if (blogUrl.includes('PostView.naver')) {
      return blogUrl;
    }

    return null;
  }

  private decodeWithEncoding(buffer: ArrayBuffer, url: string): string {
    const uint8Array = new Uint8Array(buffer);
    
    // 네이버 블로그는 일반적으로 UTF-8이지만, 구 버전은 EUC-KR 사용
    const encodings = ['utf-8', 'euc-kr', 'cp949'];
    
    for (const encoding of encodings) {
      try {
        // TextDecoder로 디코딩 시도
        const decoder = new TextDecoder(encoding, { fatal: true });
        const html = decoder.decode(uint8Array);
        
        // 한국어 문자가 포함되어 있고 깨짐이 없으면 성공
        if (html.includes('네이버') || html.includes('블로그') || /[가-힣]/.test(html.substring(0, 1000))) {
          console.log(`인코딩 감지 성공: ${encoding} for ${url}`);
          return html;
        }
      } catch (error) {
        // 디코딩 실패 시 다음 인코딩 시도
        continue;
      }
    }
    
    // 모든 인코딩 실패 시 UTF-8 강제 사용
    console.warn(`인코딩 자동감지 실패, UTF-8로 강제 디코딩: ${url}`);
    const decoder = new TextDecoder('utf-8', { fatal: false });
    return decoder.decode(uint8Array);
  }

  private parseHTMLContent(html: string, url: string, originalTitle: string, isNaverBlog = true, isTistory = false): BlogContent {
    // 블로그 플랫폼별 HTML 파싱
    let extractedTitle = originalTitle;
    let textContent = '';
    let imageCount = 0;
    let gifCount = 0;
    let videoCount = 0;
    let tags: string[] = [];

    console.log(`🔍 ${isNaverBlog ? '네이버 블로그' : '티스토리'} HTML 파싱 시작`);

    try {
      // 1. 제목 설정 - 원본 제목 그대로 사용
      extractedTitle = originalTitle;
      console.log(`🏷️ 제목 설정: "${extractedTitle}"`);

      // 2. 본문 텍스트 추출 - 플랫폼별 로직
      // 먼저 script, style 태그 제거
      let cleanHtml = html.replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '');
      cleanHtml = cleanHtml.replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '');
      
      let totalText = '';
      
      if (isNaverBlog) {
        // 네이버 블로그: 레거시 방식 - 스마트에디터 3.0 텍스트 모듈 추출
        const textModulePattern = /<div[^>]*class="[^"]*se-module[^"]*se-module-text[^"]*"[^>]*(?![^>]*se-title-text)(?![^>]*se-caption)[^>]*>([\s\S]*?)<\/div>/gi;
        let textMatch;
        
        while ((textMatch = textModulePattern.exec(cleanHtml)) !== null) {
          if (textMatch[1]) {
            const moduleText = this.extractTextFromHtml(textMatch[1]);
            if (moduleText && moduleText.trim()) {
              totalText += moduleText.trim() + ' ';
            }
          }
        }
        
        // 네이버 블로그 Fallback 방식들
        if (totalText.trim().length < 100) {
          console.log(`⚠️ 스마트에디터 텍스트 부족 (${totalText.length}자), Fallback 시도`);
          const fallbackSelectors = [
            '.se-viewer', '#post_view', '.post_content', '.se-main-container',
            '.postViewArea', '.se-component-wrap', '.se-component'
          ];
          
          for (const selector of fallbackSelectors) {
            const selectorPattern = new RegExp(`<[^>]*class="[^"]*${selector.replace('.', '')}[^"]*"[^>]*>([\\s\\S]*?)<\\/[^>]*>`, 'i');
            const idPattern = new RegExp(`<[^>]*id="${selector.replace('#', '')}"[^>]*>([\\s\\S]*?)<\\/[^>]*>`, 'i');
            
            const match = cleanHtml.match(selectorPattern) || cleanHtml.match(idPattern);
            if (match && match[1]) {
              const text = this.extractTextFromHtml(match[1]);
              if (text.length > totalText.length) {
                totalText = text;
                break;
              }
            }
          }
        }
      } else if (isTistory) {
        // 티스토리: article 태그 우선, 기타 컨텐츠 영역 폴백
        let contentExtracted = false;
        
        // 1. article 태그에서 추출 (가장 확실한 방법)
        const articleMatch = cleanHtml.match(/<article[^>]*>([\s\S]*?)<\/article>/i);
        if (articleMatch && articleMatch[1]) {
          totalText = this.extractTextFromHtml(articleMatch[1]);
          contentExtracted = true;
          console.log(`✅ 티스토리 article 태그에서 텍스트 추출: ${totalText.length}자`);
        }
        
        // 2. area_view 클래스에서 추출 (티스토리 특화)
        if (!contentExtracted || totalText.length < 100) {
          const areaViewMatch = cleanHtml.match(/<div[^>]*class="[^"]*area_view[^"]*"[^>]*>([\s\S]*?)<\/div>/i);
          if (areaViewMatch && areaViewMatch[1]) {
            const areaText = this.extractTextFromHtml(areaViewMatch[1]);
            if (areaText.length > totalText.length) {
              totalText = areaText;
              contentExtracted = true;
              console.log(`✅ 티스토리 area_view에서 텍스트 추출: ${totalText.length}자`);
            }
          }
        }
        
        // 3. 기타 티스토리 컨텐츠 영역들
        if (!contentExtracted || totalText.length < 100) {
          const tistorySelectors = ['.contents_style', '.entry-content', '.post-content'];
          for (const selector of tistorySelectors) {
            const pattern = new RegExp(`<[^>]*class="[^"]*${selector.replace('.', '')}[^"]*"[^>]*>([\\s\\S]*?)<\\/[^>]*>`, 'i');
            const match = cleanHtml.match(pattern);
            if (match && match[1]) {
              const text = this.extractTextFromHtml(match[1]);
              if (text.length > totalText.length) {
                totalText = text;
                console.log(`✅ 티스토리 ${selector}에서 텍스트 추출: ${totalText.length}자`);
                break;
              }
            }
          }
        }
      }
      
      // 공통 Fallback: p 태그에서 텍스트 추출
      if (totalText.trim().length < 100) {
        console.log(`⚠️ 플랫폼별 추출 실패, p 태그 Fallback 시도`);
        const pMatches = cleanHtml.match(/<p[^>]*>(.*?)<\/p>/gi);
        if (pMatches) {
          let pText = '';
          pMatches.forEach(p => {
            const text = this.extractTextFromHtml(p);
            if (text.trim() && text.length > 5) {
              pText += text + ' ';
            }
          });
          if (pText.length > totalText.length) {
            totalText = pText;
          }
        }
      }
      
      textContent = totalText.trim();

      // 3. 이미지 개수 계산 - 레거시 방식 적용 (스마트에디터 3.0 모듈 우선)
      // 스마트에디터 이미지 모듈 우선 카운팅
      const seImageModules = html.match(/<[^>]*class="[^"]*se-module[^"]*se-module-image[^"]*"[^>]*>/gi);
      imageCount = seImageModules ? seImageModules.length : 0;
      
      // 이미지 모듈이 없으면 일반 img 태그로 카운팅
      if (imageCount === 0) {
        const imgTags = html.match(/<img[^>]*src="[^"]*"[^>]*>/gi);
        if (imgTags) {
          const uniqueImages = new Set();
          imgTags.forEach(img => {
            const srcMatch = img.match(/src="([^"]*)"/);
            if (srcMatch && srcMatch[1] && !this.isActualGif(srcMatch[1])) {
              uniqueImages.add(srcMatch[1]);
            }
          });
          imageCount = uniqueImages.size;
        }
      }

      // 4. GIF 개수 계산 - 레거시 방식 적용
      // video._gifmp4 태그로 GIF 감지 (네이버 블로그 특화)
      const gifVideoTags = html.match(/<video[^>]*class="[^"]*_gifmp4[^"]*"[^>]*>/gi);
      gifCount = gifVideoTags ? gifVideoTags.length : 0;
      
      // Fallback: 실제 .gif 파일 감지
      if (gifCount === 0) {
        const gifImgTags = html.match(/<img[^>]*src="[^"]*"[^>]*>/gi);
        if (gifImgTags) {
          gifImgTags.forEach(img => {
            const srcMatch = img.match(/src="([^"]*)"/);
            if (srcMatch && srcMatch[1] && this.isActualGif(srcMatch[1])) {
              gifCount++;
            }
          });
        }
      }

      // 5. 동영상 개수 계산 - 레거시 방식 적용 (스마트에디터 비디오 모듈 우선)
      // 스마트에디터 비디오 모듈
      const seVideoModules = html.match(/<[^>]*class="[^"]*se-module[^"]*se-module-video[^"]*"[^>]*>/gi);
      videoCount = seVideoModules ? seVideoModules.length : 0;
      
      // Fallback: 웹플레이어 및 외부 동영상
      if (videoCount === 0) {
        const videoSources = new Set();
        
        // 웹플레이어
        const webplayerMatches = html.match(/<[^>]*class="[^"]*webplayer-internal-source-wrapper[^"]*"[^>]*>/gi);
        if (webplayerMatches) {
          webplayerMatches.forEach(match => videoSources.add(match));
        }
        
        // 외부 동영상 (YouTube, Vimeo 등)
        const externalVideoPatterns = [
          /<iframe[^>]*src="[^"]*(?:youtube\.com|youtu\.be)[^"]*"[^>]*>/gi,
          /<iframe[^>]*src="[^"]*vimeo[^"]*"[^>]*>/gi,
          /<iframe[^>]*src="[^"]*tv\.naver[^"]*"[^>]*>/gi
        ];
        
        externalVideoPatterns.forEach(pattern => {
          const matches = html.match(pattern);
          if (matches) {
            matches.forEach(match => {
              const srcMatch = match.match(/src="([^"]*)"/);
              if (srcMatch) {
                videoSources.add(srcMatch[1]);
              }
            });
          }
        });
        
        videoCount = videoSources.size;
      }

      // 6. 해시태그 추출 (네이버 블로그만 - 레거시 방식 적용)
      if (isNaverBlog) {
        tags = this.extractHashtagsFromHtml(html, textContent);
        console.log(`✅ 네이버 블로그 해시태그 추출: ${tags.length}개`);
      }

    } catch (error) {
      console.warn(`HTML 파싱 오류 (${url}):`, error);
    }

    // 레거시 방식: 공백 정리 및 글자수 계산
    const finalText = textContent.split(/\s+/).join(' ').trim(); // 연속 공백을 하나로 정리
    const contentLength = finalText.replace(/\s/g, '').length; // 공백 제거한 순수 글자수 (레거시와 동일)
    textContent = finalText;

    console.log(`📊 크롤링 결과 - 제목: "${extractedTitle}", 본문: ${contentLength}자, 이미지: ${imageCount}개`);
    
    return {
      url,
      title: extractedTitle,
      textContent,
      contentLength,
      imageCount,
      gifCount,
      videoCount,
      tags,
      success: true
    };
  }

  private shouldFilterContent(content: BlogContent): boolean {
    if (!content.success || !content.textContent) {
      return false;
    }

    // 광고/협찬 글 필터링
    if (this.isAdvertisementContent(content.textContent, content.title)) {
      return true;
    }

    // 저품질 콘텐츠 필터링
    if (this.isLowQualityContent(content.textContent)) {
      return true;
    }

    return false;
  }

  private isAdvertisementContent(textContent: string, title: string = ''): boolean {
    if (!textContent) {
      return false;
    }

    const fullText = (textContent + ' ' + title).toLowerCase();

    // 광고/협찬 관련 키워드들 (레거시와 동일)
    const adKeywords = [
      // 광고 관련
      '광고포스트', '광고 포스트', '광고글', '광고 글', '광고입니다', '광고 입니다',
      '유료광고', '유료 광고', '파트너스', '쿠팡파트너스', '파트너 활동', '추천링크',
      
      // 협찬 관련  
      '협찬', '협찬받', '협찬글', '협찬 글', '협찬으로', '협찬을', '제공받', '무료로 제공',
      '브랜드로부터', '업체로부터', '해당업체', '해당 업체', '제품을 제공', '서비스를 제공', 
      '제공받아', '제공받은', '지원을 받아', '지원받아', '업체에서 제공', '업체로부터 제품',
      
      // 체험단 관련
      '체험단', '체험 단', '리뷰어', '체험후기', '체험 후기', '체험해보', '체험을',
      '무료체험', '무료 체험', '서포터즈', '앰배서더', '인플루언서',
      
      // 기타 상업적 키워드
      '원고료', '대가', '소정의', '혜택을', '증정', '무료로 받', '공짜로', 
      '할인코드', '쿠폰', '프로모션', '이벤트 참여'
    ];

    // 키워드 매칭 검사
    for (const keyword of adKeywords) {
      if (fullText.includes(keyword)) {
        console.log(`광고/협찬 글 감지: '${keyword}' 키워드 발견`);
        return true;
      }
    }

    // 패턴 매칭 (정규식)
    const adPatterns = [
      /.*제공받.*작성.*/,  // "제공받아 작성한", "제공받고 작성한" 등
      /.*협찬.*받.*글.*/,  // "협찬받은 글", "협찬을 받아서" 등  
      /.*무료.*받.*후기.*/, // "무료로 받아서 후기", "무료로 받은 후기" 등
      /.*체험.*참여.*/,     // "체험에 참여해", "체험단 참여" 등
      /.*광고.*포함.*/,     // "광고가 포함", "광고를 포함한" 등
      /.*업체.*지원.*받.*/, // "해당 업체에 지원을 받아", "업체로부터 지원받아" 등
      /.*업체.*제품.*제공.*/, // "업체로부터 제품을 제공받아" 등
    ];

    for (const pattern of adPatterns) {
      if (pattern.test(fullText)) {
        console.log(`광고/협찬 글 감지: 패턴 '${pattern}' 매칭`);
        return true;
      }
    }

    return false;
  }

  private isLowQualityContent(textContent: string): boolean {
    if (!textContent) {
      return false;
    }

    const cleanedText = textContent.trim();
    if (cleanedText.length < 100) {
      return false;
    }

    // 1. 숫자만 나열된 글 체크
    const numbersAndSymbols = cleanedText.replace(/[0-9\s\-,()원₩\.\+#]/g, '');
    const meaningfulCharRatio = numbersAndSymbols.length / cleanedText.length;
    if (meaningfulCharRatio < 0.3) {
      console.log(`품질 낮은 글 감지: 숫자/기호만 나열됨 (의미있는 문자 비율: ${(meaningfulCharRatio * 100).toFixed(1)}%)`);
      return true;
    }

    // 2. 특수문자 비율이 너무 높은 글 체크
    const specialChars = cleanedText.replace(/[가-힣ㄱ-ㅎㅏ-ㅣa-zA-Z0-9\s]/g, '');
    const specialCharRatio = specialChars.length / cleanedText.length;
    if (specialCharRatio > 0.15) {
      console.log(`품질 낮은 글 감지: 특수문자 과다 (비율: ${(specialCharRatio * 100).toFixed(1)}%)`);
      return true;
    }

    // 3. 반복 패턴 체크
    if (/(.)\1{4,}/.test(cleanedText)) {
      console.log('품질 낮은 글 감지: 같은 문자 반복 패턴');
      return true;
    }

    return false;
  }

  private isActualGif(url: string): boolean {
    /**
     * 실제 GIF 파일인지 정확히 판단 (레거시 방식)
     */
    if (!url) {
      return false;
    }
    
    const urlLower = url.toLowerCase();
    
    // 확실한 GIF 패턴들
    const definiteGifPatterns = [
      '.gif?',     // 실제 .gif 확장자
      '.gifv',     // gifv 포맷
      'format=gif', // URL 파라미터로 gif 명시
      'type=gif',
      '_gif.',     // 파일명에 gif 포함
    ];
    
    return definiteGifPatterns.some(pattern => urlLower.includes(pattern));
  }

  // 레거시 방식: HTML에서 순수 텍스트 추출 (BeautifulSoup의 get_text()와 동일)
  private extractTextFromHtml(html: string): string {
    if (!html) return '';
    
    // HTML 태그 완전 제거
    let text = html.replace(/<[^>]*>/g, '');
    
    // HTML 엔티티 디코딩
    text = text
      .replace(/&nbsp;/g, ' ')
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'")
      .replace(/&apos;/g, "'")
      .replace(/&#(\d+);/g, (_, num) => String.fromCharCode(parseInt(num)))
      .replace(/&#x([0-9a-fA-F]+);/g, (_, hex) => String.fromCharCode(parseInt(hex, 16)));
    
    // 공백 정리 (연속 공백, 탭, 줄바꿈을 하나의 공백으로)
    text = text.replace(/\s+/g, ' ').trim();
    
    return text;
  }

  private cleanText(html: string): string {
    // HTML 태그 제거
    let text = html.replace(/<[^>]*>/g, '');
    
    // HTML 엔티티 디코딩
    text = text
      .replace(/&nbsp;/g, ' ')
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'")
      .replace(/&apos;/g, "'");
    
    // 연속된 공백을 하나로 정리
    text = text.replace(/\s+/g, ' ').trim();
    
    return text;
  }

  private extractHashtagsFromHtml(html: string, textContent: string): string[] {
    /**
     * 네이버 스마트에디터 해시태그 추출 (레거시 Python 방식 적용)
     * legacy-pyside-version/src/features/blog_automation/adapters.py의 _extract_content_hashtags_from_html과 동일
     */
    const hashtags = new Set<string>();

    try {
      // 1. 네이버 스마트에디터 해시태그 요소에서 추출
      const hashtagElementPattern = /<span[^>]*class="[^"]*__se-hash-tag[^"]*"[^>]*>(.*?)<\/span>/gi;
      let elementMatch;
      
      while ((elementMatch = hashtagElementPattern.exec(html)) !== null) {
        if (elementMatch[1]) {
          const tagText = this.cleanText(elementMatch[1]).trim();
          if (tagText.startsWith('#')) {
            // #을 제거하고 태그만 추출
            const cleanTag = tagText.substring(1).trim();
            if (cleanTag.length > 0 && cleanTag.length <= 20) {
              hashtags.add(cleanTag);
            }
          }
        }
      }

      // 2. 텍스트 콘텐츠에서 해시태그 패턴 추출 (레거시 방식 적용)
      const extractedFromText = this.extractContentHashtags(textContent);
      extractedFromText.forEach(tag => hashtags.add(tag));

      // 3. HTML 전체에서 fallback 해시태그 패턴 검색 (스마트에디터 요소가 없을 때만)
      if (hashtags.size < 3) {
        const htmlText = this.extractTextFromHtml(html);
        const fallbackHashtags = this.extractContentHashtags(htmlText);
        fallbackHashtags.forEach(tag => hashtags.add(tag));
      }

      // 4. 결과 정리 (레거시와 동일한 방식)
      let results = Array.from(hashtags);
      
      // 길이순 정렬 (긴 것부터) 후 최대 15개로 제한
      results.sort((a, b) => b.length - a.length);
      results = results.slice(0, 15);

      console.log(`🏷️ 해시태그 추출 결과: [${results.join(', ')}]`);
      return results;

    } catch (error) {
      console.warn('해시태그 추출 오류:', error);
      return [];
    }
  }

  private extractContentHashtags(textContent: string): string[] {
    /**
     * 본문 텍스트에서 해시태그 패턴 추출 (레거시 Python 방식 완전 포팅)
     */
    try {
      if (!textContent) {
        return [];
      }

      console.log(`🏷️ 본문 해시태그 추출 시작: ${textContent.length} 글자`);
      
      let hashtags: string[] = [];

      // 1. 기본 해시태그 패턴 (#한글영숫자)
      const basicPattern = /#([가-힣a-zA-Z0-9_]+)/g;
      let match;
      
      while ((match = basicPattern.exec(textContent)) !== null) {
        const hashtagFull = `#${match[1]}`;
        if (!hashtags.includes(hashtagFull) && match[1].length >= 2) { // 최소 2글자 이상
          hashtags.push(hashtagFull);
        }
      }

      console.log(`🏷️ 기본 패턴 해시태그: ${hashtags.length}개`);

      // 2. 본문 마지막 부분에 있는 태그들 우선 처리 (더 정확한 태그일 가능성 높음)
      if (textContent.length > 200) {
        const lastPart = textContent.slice(-200);
        const lastPartHashtags: string[] = [];
        const lastPartPattern = /#([가-힣a-zA-Z0-9_]+)/g;
        let lastMatch;
        
        while ((lastMatch = lastPartPattern.exec(lastPart)) !== null) {
          lastPartHashtags.push(lastMatch[1]);
        }

        if (lastPartHashtags.length >= 3) { // 마지막 부분에 태그가 많으면 우선순위
          console.log(`🏷️ 마지막 200자에서 ${lastPartHashtags.length}개 해시태그 발견 - 우선순위 적용`);
          
          // 마지막 부분의 태그들을 앞쪽에 배치
          const priorityTags: string[] = [];
          const remainingTags: string[] = [];
          
          hashtags.forEach(hashtag => {
            const tagName = hashtag.substring(1); // # 제거
            if (lastPartHashtags.includes(tagName)) {
              priorityTags.push(hashtag);
            } else {
              remainingTags.push(hashtag);
            }
          });
          
          hashtags = priorityTags.concat(remainingTags);
        }
      }

      // 3. 콤마나 공백으로 구분된 연속 해시태그 패턴도 확인
      const consecutivePattern = /#[가-힣a-zA-Z0-9_]+(?:[,\s]*#[가-힣a-zA-Z0-9_]+)+/g;
      let consecutiveMatch;
      
      while ((consecutiveMatch = consecutivePattern.exec(textContent)) !== null) {
        // 연속 패턴에서 개별 해시태그들 추출
        const individualPattern = /#([가-힣a-zA-Z0-9_]+)/g;
        let individualMatch;
        
        while ((individualMatch = individualPattern.exec(consecutiveMatch[0])) !== null) {
          const hashtagFull = `#${individualMatch[1]}`;
          if (!hashtags.includes(hashtagFull) && individualMatch[1].length >= 2) {
            hashtags.push(hashtagFull);
          }
        }
      }

      console.log(`🏷️ 연속 패턴 추가 후: ${hashtags.length}개`);

      // 4. 일반적이지 않은 태그들 필터링 (레거시와 동일)
      const filteredHashtags: string[] = [];
      
      // 제외할 패턴들 (CSS/HTML 요소, 너무 일반적이거나 의미없는 것들)
      const excludePatterns = [
        /^#\d+$/,  // 순수 숫자만
        /^#[a-zA-Z_\-]+$/,  // 순수 영어만 (한글 없음) - CSS ID 형태
        /^#.{1}$/,  // 1글자
        /^#(좋아요|감사|부탁|댓글|공감|추천)$/,  // 너무 일반적인 단어들
        // CSS/HTML 관련 패턴들
        /^#(wrapper|container|content|main|header|footer|sidebar).*/,
        /^#(post|blog|article|div|section|span|p).*/,
        /^#.*(_|-).*/,  // 언더스코어나 하이픈 포함 (CSS ID 패턴)
        /^#(floating|banword|btn|bw_).*/,  // 네이버 블로그 특정 요소들
        /^#[0-9a-fA-F]{6}$/,  // 색상 코드
        /^#[0-9a-fA-F]{3}$/,   // 짧은 색상 코드
      ];

      for (const hashtag of hashtags) {
        let shouldExclude = false;
        for (const pattern of excludePatterns) {
          if (pattern.test(hashtag)) {
            shouldExclude = true;
            break;
          }
        }
        
        if (!shouldExclude) {
          filteredHashtags.push(hashtag);
        }
      }

      console.log(`🏷️ 필터링 후 최종: ${filteredHashtags.length}개`);

      // 5. 중복 제거 및 길이순 정렬 (긴 태그가 더 구체적일 가능성)
      const uniqueHashtags: string[] = [];
      for (const hashtag of filteredHashtags) {
        if (!uniqueHashtags.includes(hashtag)) {
          uniqueHashtags.push(hashtag);
        }
      }

      // 길이순 정렬 (긴 것부터)
      uniqueHashtags.sort((a, b) => b.length - a.length);

      if (uniqueHashtags.length > 0) {
        console.log(`🏷️ 본문 해시태그 추출 성공: ${uniqueHashtags.length}개 - ${uniqueHashtags.slice(0, 3).join(', ')}${uniqueHashtags.length > 3 ? '...' : ''}`);
      } else {
        console.log('🏷️ 본문에서 해시태그를 찾지 못함');
      }

      // # 제거하고 태그명만 반환 (레거시와 동일)
      return uniqueHashtags.slice(0, 15).map(tag => tag.substring(1)); // 최대 15개, # 제거

    } catch (error) {
      console.warn('🏷️ 본문 해시태그 추출 실패:', error);
      return [];
    }
  }
}