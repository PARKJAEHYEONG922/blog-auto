interface NaverAPIConfig {
  clientId: string;
  clientSecret: string;
}

interface NaverBlogItem {
  title: string;
  link: string;
  description: string;
  bloggername: string;
  bloggerlink: string;
  postdate: string;
}

interface NaverShoppingItem {
  title: string;
  link: string;
  image: string;
  lprice: string;
  hprice: string;
  mallName: string;
  productId: string;
  productType: string;
  brand: string;
  maker: string;
  category1: string;
  category2: string;
  category3: string;
  category4: string;
}

interface NaverSearchResponse<T> {
  lastBuildDate: string;
  total: number;
  start: number;
  display: number;
  items: T[];
}

export class NaverAPI {
  private config: NaverAPIConfig | null = null;

  async loadConfig(): Promise<void> {
    try {
      // 네이버 API 설정을 로컬스토리지나 Electron 설정에서 로드
      if ((window as any).electronAPI && typeof (window as any).electronAPI.loadNaverApiSettings === 'function') {
        const result = await (window as any).electronAPI.loadNaverApiSettings();
        if (result && result.success && result.data) {
          this.config = {
            clientId: result.data.clientId,
            clientSecret: result.data.clientSecret
          };
          console.log('✅ 네이버 API 설정 로드 완료');
        } else {
          throw new Error('네이버 API 설정이 없습니다.');
        }
      } else {
        throw new Error('Electron API를 사용할 수 없습니다.');
      }
    } catch (error) {
      console.error('네이버 API 설정 로드 실패:', error);
      throw error;
    }
  }

  private async makeRequest<T>(endpoint: string, query: string, display: number = 10, start: number = 1, sort: string = 'sim'): Promise<NaverSearchResponse<T>> {
    if (!this.config) {
      await this.loadConfig();
    }

    if (!this.config) {
      throw new Error('네이버 API 설정이 없습니다. API 설정에서 네이버 클라이언트 ID와 Secret을 설정해주세요.');
    }

    // MCP 서버와 동일한 방식으로 파라미터 구성
    const params = new URLSearchParams({
      query,
      display: display.toString(),
      start: start.toString(),
      sort: sort
    });

    const url = `https://openapi.naver.com/v1/search/${endpoint}?${params}`;

    try {
      console.log(`📡 네이버 API 호출: ${url}`);
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'X-Naver-Client-Id': this.config.clientId,
          'X-Naver-Client-Secret': this.config.clientSecret,
          'User-Agent': 'blog-automation/1.0'
        }
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`네이버 API 요청 실패 (${response.status}): ${errorText}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error(`네이버 API 호출 실패 (${endpoint}):`, error);
      throw error;
    }
  }

  async searchBlogs(query: string, display: number = 10, start: number = 1, sort: string = 'sim', contentType?: string): Promise<NaverBlogItem[]> {
    try {
      console.log(`🔍 네이버 블로그 검색: ${query}`);
      const response = await this.makeRequest<NaverBlogItem>('blog.json', query, display, start, sort);
      
      // 지원하는 블로그 플랫폼 필터링 (네이버 블로그 + 티스토리)
      const supportedBlogs = (response.items || []).filter(item => 
        item.link && (
          item.link.includes('blog.naver.com') || 
          item.link.includes('.tistory.com')
        )
      );
      
      // 콘텐츠 타입에 따른 조건부 필터링
      let filteredBlogs = supportedBlogs;
      
      // 후기형과 비교추천형이 아닌 경우에만 광고성 키워드 필터링
      if (contentType !== 'review' && contentType !== 'compare') {
        filteredBlogs = supportedBlogs.filter(item => {
          const title = this.cleanHtmlTags(item.title).toLowerCase();
          const description = this.cleanHtmlTags(item.description).toLowerCase();
          const fullText = `${title} ${description}`;
          
          // 정보형과 노하우형에서만 필터링할 키워드들
          const excludeKeywords = [
            '할인', '세일', '특가', '이벤트', '무료배송',
            '최저가', '가격비교', '구매', '주문', '배송',
            '추천템', '리뷰이벤트', '체험단', '협찬', '제공'
          ];
          
          return !excludeKeywords.some(keyword => fullText.includes(keyword));
        });
      }
      
      console.log(`📊 전체 ${response.items?.length || 0}개 → 지원 블로그 ${supportedBlogs.length}개 → 필터링 후 ${filteredBlogs.length}개`);
      
      return filteredBlogs;
    } catch (error) {
      console.error('네이버 블로그 검색 실패:', error);
      return [];
    }
  }

  async searchShopping(query: string, display: number = 10, start: number = 1, sort: string = 'sim'): Promise<NaverShoppingItem[]> {
    try {
      console.log(`🛒 네이버 쇼핑 검색: ${query}`);
      const response = await this.makeRequest<NaverShoppingItem>('shop.json', query, display, start, sort);
      return response.items || [];
    } catch (error) {
      console.error('네이버 쇼핑 검색 실패:', error);
      return [];
    }
  }

  cleanHtmlTags(text: string): string {
    return text.replace(/<[^>]*>/g, '').replace(/&[^;]+;/g, ' ').trim();
  }

  formatPrice(price: string): string {
    const numPrice = parseInt(price);
    return numPrice ? `${numPrice.toLocaleString()}원` : '가격 정보 없음';
  }

  formatDate(dateString: string): string {
    if (!dateString || dateString.length !== 8) return dateString;
    
    const year = dateString.substring(0, 4);
    const month = dateString.substring(4, 6);
    const day = dateString.substring(6, 8);
    
    return `${year}-${month}-${day}`;
  }
}

export const naverAPI = new NaverAPI();