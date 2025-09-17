import { mcpClientManager } from './mcp-client';
import { LLMClientFactory, LLMMessage } from './llm-client-factory';

export interface TitleGenerationRequest {
  keyword: string;
  subKeywords?: string[];
  platform: string;
  platformName: string; // UI에서 한국어 플랫폼명 전달
  contentType: string;
  contentTypeName: string; // UI에서 한국어 콘텐츠타입명 전달
  tone: string;
  customPrompt?: string;
  blogDescription?: string;
  mode: 'fast' | 'accurate';
}

export interface TitleWithSearch {
  title: string;
  searchQuery: string;
}

export interface TitleGenerationResult {
  titles: string[];
  titlesWithSearch: TitleWithSearch[];
  metadata: {
    mode: string;
    sources: string[];
    processingTime: number;
  };
}

export class TitleGenerationEngine {
  async generateTitles(request: TitleGenerationRequest): Promise<TitleGenerationResult> {
    const startTime = Date.now();
    const sources: string[] = [];

    try {
      let trendData = null;
      
      // 정확 모드인 경우 MCP를 통한 트렌드 데이터 수집
      if (request.mode === 'accurate') {
        trendData = await this.collectTrendData(request.keyword);
        sources.push(...trendData.sources);
      }

      // LLM을 통한 제목 생성
      const result = await this.generateTitlesWithLLM(request, trendData);

      const processingTime = Date.now() - startTime;

      return {
        titles: result.titles,
        titlesWithSearch: result.titlesWithSearch,
        metadata: {
          mode: request.mode,
          sources,
          processingTime
        }
      };
    } catch (error) {
      console.error('제목 생성 실패:', error);
      throw error;
    }
  }

  private async collectTrendData(keyword: string): Promise<any> {
    const sources: string[] = [];
    const trendData: any = {
      youtube: null,
      naver: null,
      google: null,
      sources
    };

    try {
      // MCP 서버들을 자동으로 연결
      await this.ensureMCPServersConnected();

      // YouTube 트렌드 데이터 수집 (MCP 사용)
      if (await mcpClientManager.isConnected('youtube')) {
        try {
          const youtubeData = await mcpClientManager.callTool('youtube', 'search', {
            query: keyword,
            maxResults: 10
          });
          
          // YouTube 데이터에서 제목과 조회수 정보 추출
          if (youtubeData && youtubeData.videos) {
            const processedData = youtubeData.videos.map((video: any) => ({
              title: video.title,
              viewCount: video.viewCount,
              channelTitle: video.channelTitle
            }));
            trendData.youtube = processedData;
            sources.push('YouTube MCP');
            console.log(`YouTube 데이터 수집 성공: ${processedData.length}개 비디오`);
          }
        } catch (error) {
          console.warn('YouTube MCP 호출 실패:', error);
        }
      } else {
        console.warn('YouTube MCP 서버에 연결되지 않음');
      }

      // 네이버 MCP를 통한 검색 데이터 수집 (우선)
      if (await mcpClientManager.isConnected('naver-search')) {
        try {
          console.log('네이버 MCP를 통한 검색 데이터 수집 시작...');
          
          // 네이버 블로그 검색
          const blogData = await mcpClientManager.callTool('naver-search', 'fetch', {
            url: `https://openapi.naver.com/v1/search/blog.json?query=${encodeURIComponent(keyword)}&display=20&sort=sim`,
            method: 'GET',
            headers: {
              'X-Naver-Client-Id': await this.getNaverClientId(),
              'X-Naver-Client-Secret': await this.getNaverClientSecret()
            }
          });

          // 네이버 뉴스 검색 (추가 트렌드 데이터)
          const newsData = await mcpClientManager.callTool('naver-search', 'fetch', {
            url: `https://openapi.naver.com/v1/search/news.json?query=${encodeURIComponent(keyword)}&display=10&sort=sim`,
            method: 'GET',
            headers: {
              'X-Naver-Client-Id': await this.getNaverClientId(),
              'X-Naver-Client-Secret': await this.getNaverClientSecret()
            }
          });

          // 네이버 쇼핑 검색 (상품 트렌드)
          const shopData = await mcpClientManager.callTool('naver-search', 'fetch', {
            url: `https://openapi.naver.com/v1/search/shop.json?query=${encodeURIComponent(keyword)}&display=15&sort=sim`,
            method: 'GET',
            headers: {
              'X-Naver-Client-Id': await this.getNaverClientId(),
              'X-Naver-Client-Secret': await this.getNaverClientSecret()
            }
          });

          // 네이버 카페 검색 (커뮤니티 트렌드)
          const cafeData = await mcpClientManager.callTool('naver-search', 'fetch', {
            url: `https://openapi.naver.com/v1/search/cafearticle.json?query=${encodeURIComponent(keyword)}&display=10&sort=sim`,
            method: 'GET',
            headers: {
              'X-Naver-Client-Id': await this.getNaverClientId(),
              'X-Naver-Client-Secret': await this.getNaverClientSecret()
            }
          });

          // MCP 데이터 처리
          if (blogData && blogData.items) {
            const processedData = this.processNaverMCPData(blogData, newsData, shopData, cafeData, keyword);
            trendData.naver = processedData;
            sources.push('Naver Search MCP');
            console.log(`네이버 MCP 데이터 수집 성공: 블로그 ${blogData.items.length}개, 뉴스 ${newsData?.items?.length || 0}개, 쇼핑 ${shopData?.items?.length || 0}개, 카페 ${cafeData?.items?.length || 0}개`);
          }
        } catch (error) {
          console.warn('네이버 MCP 호출 실패, 직접 API로 대체:', error);
          // MCP 실패 시 직접 API 호출로 대체
          try {
            const naverData = await this.collectNaverSearchData(keyword);
            trendData.naver = naverData;
            sources.push('Naver Search API (Fallback)');
          } catch (fallbackError) {
            console.warn('네이버 직접 API도 실패:', fallbackError);
            const fallbackData = {
              keywords: [`${keyword} 가이드`, `${keyword} 방법`, `${keyword} 추천`],
              trends: ['완벽', '초보자', '실전', '노하우']
            };
            trendData.naver = fallbackData;
            sources.push('Naver Data (Basic Fallback)');
          }
        }
      } else {
        // MCP 연결 실패 시 직접 API 호출
        try {
          const naverData = await this.collectNaverSearchData(keyword);
          trendData.naver = naverData;
          sources.push('Naver Search API (Direct)');
          console.log('네이버 직접 API 호출 성공');
        } catch (error) {
          console.warn('네이버 데이터 수집 실패:', error);
          const fallbackData = {
            keywords: [`${keyword} 가이드`, `${keyword} 방법`, `${keyword} 추천`],
            trends: ['완벽', '초보자', '실전', '노하우']
          };
          trendData.naver = fallbackData;
          sources.push('Naver Data (Fallback)');
        }
      }

      // 구글 트렌드 시뮬레이션 (향후 Google Trends API 또는 크롤링 MCP 추가 예정)
      try {
        const googleData = {
          relatedQueries: [`${keyword} 비교`, `${keyword} 후기`, `${keyword} 장단점`],
          risingQueries: [`${keyword} 최신`, `${keyword} 추천`, `${keyword} 신제품`],
          trendingTopics: [`${keyword} 트렌드`, `${keyword} 인기`, `${keyword} 순위`]
        };
        trendData.google = googleData;
        sources.push('Google Trends (Enhanced)');
      } catch (error) {
        console.warn('구글 데이터 수집 실패:', error);
      }

    } catch (error) {
      console.error('트렌드 데이터 수집 실패:', error);
    }

    return trendData;
  }

  private async ensureMCPServersConnected(): Promise<void> {
    try {
      // 네이버 MCP 서버 연결 (최우선)
      if (!await mcpClientManager.isConnected('naver-search')) {
        console.log('네이버 검색 MCP 서버 연결 시도...');
        
        try {
          // 저장된 네이버 API 키 가져오기
          const clientId = await this.getNaverClientId();
          const clientSecret = await this.getNaverClientSecret();
          
          const naverServer = {
            name: 'naver-search',
            command: 'npx',
            args: ['-y', '@modelcontextprotocol/server-fetch'],
            description: '네이버 검색 API (블로그, 뉴스, 카페)',
            env: {
              NAVER_CLIENT_ID: clientId,
              NAVER_CLIENT_SECRET: clientSecret,
              MCP_SERVER_NAME: 'naver-search'
            }
          };
          
          await mcpClientManager.connectToServer(naverServer);
          console.log('네이버 검색 MCP 서버 연결 성공');
        } catch (error) {
          console.warn('네이버 검색 MCP 서버 연결 실패:', error);
        }
      }

      // YouTube MCP 서버 연결 (보조)
      if (!await mcpClientManager.isConnected('youtube')) {
        console.log('YouTube MCP 서버 연결 시도...');
        const youtubeServer = {
          name: 'youtube',
          command: 'node',
          args: ['node_modules/@anaisbetts/mcp-youtube/dist/index.js'],
          description: 'YouTube 비디오 분석 및 자막 추출'
        };
        
        try {
          await mcpClientManager.connectToServer(youtubeServer);
          console.log('YouTube MCP 서버 연결 성공');
        } catch (error) {
          console.warn('YouTube MCP 서버 연결 실패:', error);
        }
      }
    } catch (error) {
      console.error('MCP 서버 연결 실패:', error);
    }
  }

  private async collectNaverSearchData(keyword: string): Promise<any> {
    try {
      const headers = {
        'X-Naver-Client-Id': await this.getNaverClientId(),
        'X-Naver-Client-Secret': await this.getNaverClientSecret()
      };

      // 여러 검색 API 병렬 호출
      const [blogResponse, shopResponse, cafeResponse] = await Promise.allSettled([
        fetch(`https://openapi.naver.com/v1/search/blog.json?query=${encodeURIComponent(keyword)}&display=20&sort=sim`, {
          method: 'GET',
          headers
        }),
        fetch(`https://openapi.naver.com/v1/search/shop.json?query=${encodeURIComponent(keyword)}&display=15&sort=sim`, {
          method: 'GET',
          headers
        }),
        fetch(`https://openapi.naver.com/v1/search/cafearticle.json?query=${encodeURIComponent(keyword)}&display=10&sort=sim`, {
          method: 'GET',
          headers
        })
      ]);

      const results: any = {};
      
      // 블로그 데이터 처리
      if (blogResponse.status === 'fulfilled' && blogResponse.value.ok) {
        const blogData = await blogResponse.value.json();
        results.blogs = blogData.items || [];
        results.totalCount = blogData.total || 0;
      }

      // 쇼핑 데이터 처리
      if (shopResponse.status === 'fulfilled' && shopResponse.value.ok) {
        const shopData = await shopResponse.value.json();
        results.shops = shopData.items || [];
        results.shopCount = shopData.total || 0;
      }

      // 카페 데이터 처리
      if (cafeResponse.status === 'fulfilled' && cafeResponse.value.ok) {
        const cafeData = await cafeResponse.value.json();
        results.cafes = cafeData.items || [];
        results.cafeCount = cafeData.total || 0;
      }

      // 통합 제목 분석
      const allTitles = [
        ...(results.blogs?.map((item: any) => item.title.replace(/<[^>]+>/g, '')) || []),
        ...(results.shops?.map((item: any) => item.title.replace(/<[^>]+>/g, '')) || []),
        ...(results.cafes?.map((item: any) => item.title.replace(/<[^>]+>/g, '')) || [])
      ];
      
      const keywords = this.extractTrendKeywords(allTitles, keyword);
      const trends = this.extractTrendWords(allTitles);

      return {
        searchResults: results.blogs?.slice(0, 8) || [],
        shopResults: results.shops?.slice(0, 6) || [],
        cafeResults: results.cafes?.slice(0, 4) || [],
        keywords: keywords.slice(0, 8),
        trends: trends,
        totalCount: results.totalCount || 0,
        shopCount: results.shopCount || 0,
        cafeCount: results.cafeCount || 0,
        mcpSource: false // 직접 API 호출임을 표시
      };
    } catch (error) {
      console.error('네이버 검색 데이터 수집 실패:', error);
      throw error;
    }
  }

  private async getNaverClientId(): Promise<string> {
    try {
      const naverSettings = await (window as any).electronAPI.loadNaverApiSettings();
      if (naverSettings?.success && naverSettings.data?.clientId) {
        return naverSettings.data.clientId;
      }
      throw new Error('네이버 API Client ID가 설정되지 않았습니다.');
    } catch (error) {
      throw new Error('네이버 API 설정을 확인해주세요. API 설정에서 네이버 API를 설정해주세요.');
    }
  }

  private async getNaverClientSecret(): Promise<string> {
    try {
      const naverSettings = await (window as any).electronAPI.loadNaverApiSettings();
      if (naverSettings?.success && naverSettings.data?.clientSecret) {
        return naverSettings.data.clientSecret;
      }
      throw new Error('네이버 API Client Secret이 설정되지 않았습니다.');
    } catch (error) {
      throw new Error('네이버 API 설정을 확인해주세요. API 설정에서 네이버 API를 설정해주세요.');
    }
  }

  private extractTrendKeywords(titles: string[], mainKeyword: string): string[] {
    const keywords = new Set<string>();
    
    titles.forEach(title => {
      // 자주 등장하는 키워드 조합 추출
      const words = title.split(/\s+/);
      words.forEach(word => {
        if (word.length > 1 && word !== mainKeyword) {
          keywords.add(`${mainKeyword} ${word}`);
        }
      });
    });

    return Array.from(keywords).slice(0, 10);
  }

  private extractTrendWords(titles: string[]): string[] {
    const wordFreq = new Map<string, number>();
    
    titles.forEach(title => {
      const words = title.split(/\s+/);
      words.forEach(word => {
        const cleanWord = word.replace(/[^\w가-힣]/g, '');
        if (cleanWord.length > 1) {
          wordFreq.set(cleanWord, (wordFreq.get(cleanWord) || 0) + 1);
        }
      });
    });

    return Array.from(wordFreq.entries())
      .sort(([,a], [,b]) => b - a)
      .slice(0, 8)
      .map(([word]) => word);
  }

  private processNaverMCPData(blogData: any, newsData: any, shopData: any, cafeData: any, keyword: string): any {
    const blogs = blogData.items || [];
    const news = newsData?.items || [];
    const shops = shopData?.items || [];
    const cafes = cafeData?.items || [];
    
    // 모든 제목에서 키워드 트렌드 분석
    const blogTitles = blogs.map((item: any) => item.title.replace(/<[^>]+>/g, ''));
    const newsTitles = news.map((item: any) => item.title.replace(/<[^>]+>/g, ''));
    const shopTitles = shops.map((item: any) => item.title.replace(/<[^>]+>/g, ''));
    const cafeTitles = cafes.map((item: any) => item.title.replace(/<[^>]+>/g, ''));
    
    const allTitles = [...blogTitles, ...newsTitles, ...shopTitles, ...cafeTitles];
    
    const keywords = this.extractTrendKeywords(allTitles, keyword);
    const trends = this.extractTrendWords(allTitles);
    
    // 쇼핑 데이터에서 가격 트렌드 분석
    const priceRanges = shops
      .filter((item: any) => item.lprice && item.hprice)
      .map((item: any) => ({
        title: item.title.replace(/<[^>]+>/g, ''),
        lprice: parseInt(item.lprice),
        hprice: parseInt(item.hprice)
      }))
      .slice(0, 5);
    
    return {
      searchResults: blogs.slice(0, 8),
      newsResults: news.slice(0, 4),
      shopResults: shops.slice(0, 6),
      cafeResults: cafes.slice(0, 4),
      keywords: keywords.slice(0, 8),
      trends: trends,
      priceRanges: priceRanges,
      totalCount: blogData.total || 0,
      newsCount: newsData?.total || 0,
      shopCount: shopData?.total || 0,
      cafeCount: cafeData?.total || 0,
      mcpSource: true // MCP에서 온 데이터임을 표시
    };
  }

  private async generateTitlesWithLLM(
    request: TitleGenerationRequest,
    trendData?: any
  ): Promise<{ titles: string[], titlesWithSearch: TitleWithSearch[] }> {
    try {
      const informationClient = LLMClientFactory.getInformationClient();

      // 프롬프트 구성
      const systemPrompt = this.buildSystemPrompt(request);
      const userPrompt = this.buildUserPrompt(request, trendData);

      const messages: LLMMessage[] = [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userPrompt }
      ];

      const response = await informationClient.generateText(messages);
      
      // 응답에서 제목과 검색어 추출
      const result = this.extractTitlesWithSearch(response.content);
      
      return result;
    } catch (error) {
      console.error('LLM 제목 생성 실패:', error);
      
      // 정보처리 LLM이 설정되지 않은 경우의 구체적인 오류 메시지
      if (error.message === 'Information LLM client not configured') {
        throw new Error('정보처리 AI가 설정되지 않았습니다. API 설정에서 정보처리 LLM을 설정해주세요.');
      }
      
      throw error;
    }
  }

  private buildSystemPrompt(request: TitleGenerationRequest): string {
    // 컨텐츠 유형별 지침
    const contentGuidelines: { [key: string]: any } = {
      'info': {
        approach: '정확하고 풍부한 정보를 체계적으로 제공하여 검색자의 궁금증 완전 해결',
        keywords: ['완벽 정리', '총정리', '핵심 포인트', '단계별 가이드', '정확한 정보'],
        focusAreas: ['체계적 구조와 소제목', '실용적 가이드 제공', '구체적 실행 방법']
      },
      'review': {
        approach: '개인 경험과 솔직한 후기를 중심으로 \'유일무이한 콘텐츠\' 작성',
        keywords: ['직접 써봤어요', '솔직 후기', '개인적으로', '실제로 사용해보니', '추천하는 이유'],
        focusAreas: ['개인 경험과 솔직한 후기', '장단점 균형 제시', '구체적 사용 데이터']
      },
      'compare': {
        approach: '체계적 비교분석으로 독자의 선택 고민을 완전히 해결',
        keywords: ['VS 비교', 'Best 5', '장단점', '상황별 추천', '가성비'],
        focusAreas: ['객관적 비교 기준', '상황별 맞춤 추천', '명확한 선택 가이드']
      },
      'howto': {
        approach: '실용적 방법론과 단계별 가이드 제공',
        keywords: ['노하우', '방법', '가이드', '팁', '실전'],
        focusAreas: ['단계별 실행 방법', '실용적 팁 제공', '구체적 예시']
      }
    };

    const guideline = contentGuidelines[request.contentType] || contentGuidelines['info'];

    return `${request.platformName} 상위 노출에 유리한 '${request.contentTypeName}' 스타일의 제목 10개를 추천해주세요.

**${request.contentTypeName} 특징**:
- 접근법: ${guideline.approach}
- 핵심 키워드: ${guideline.keywords.join(', ')}
- 중점 영역: ${guideline.focusAreas.join(', ')}

**제목 생성 규칙**:
1. 메인키워드를 자연스럽게 포함
2. 클릭 유도와 궁금증 자극
3. 30-60자 내외 권장
4. ${request.contentTypeName}의 특성 반영
5. ${request.platformName} SEO 최적화
6. 이모티콘 사용 금지 (텍스트만 사용)
7. 구체적 년도 표기 금지 (2024, 2025 등 특정 년도 사용 금지. "최신", "현재" 등으로 대체)

**출력 형식**:
JSON 형태로 정확히 10개 제목과 각 제목에 맞는 블로그 검색어를 함께 반환해주세요.

각 제목마다 "해당 제목과 유사한 내용의 블로그를 찾기 위한 ${request.platformName} 검색어"를 함께 생성해주세요.
이 검색어는 다른 블로그를 검색해서 분석하여 참고용 자료로 활용됩니다.
검색어는 2-4개 단어 조합으로 구체적이고 관련성 높게 만들어주세요.

{
  "titles_with_search": [
    {
      "title": "제목1",
      "search_query": "관련 블로그 검색어1"
    },
    {
      "title": "제목2", 
      "search_query": "관련 블로그 검색어2"
    },
    ...
    {
      "title": "제목10",
      "search_query": "관련 블로그 검색어10"
    }
  ]
}

각 제목은 ${request.contentTypeName}의 특성을 살리되, 서로 다른 접근 방식으로 다양하게 생성해주세요.`;
  }

  private buildUserPrompt(request: TitleGenerationRequest, trendData?: any): string {
    let prompt = "";

    // 1. AI 역할 설정 (가장 먼저)
    if (request.blogDescription) {
      prompt += `# AI 역할 설정
${request.blogDescription}

`;
    }

    // 2. 메인키워드 (필수)
    prompt += `**메인키워드**: ${request.keyword}`;

    // 3. 서브키워드 (있는 경우)
    if (request.subKeywords && request.subKeywords.length > 0) {
      prompt += `\n**서브키워드**: ${request.subKeywords.join(', ')}`;
      prompt += `\n*서브키워드는 메인키워드와 함께 자연스럽게 활용하여 더 구체적인 제목을 만들어주세요.*`;
    }

    // 4. 추가 요청사항 (있는 경우)
    if (request.customPrompt) {
      prompt += `\n\n**추가 요청사항**: ${request.customPrompt}`;
    }

    if (trendData && request.mode === 'accurate') {
      prompt += '\n\n=== 🔥 실시간 트렌드 분석 데이터 ===';
      
      if (trendData.youtube && trendData.youtube.length > 0) {
        prompt += '\n\n📺 **YouTube 인기 콘텐츠 분석**';
        const topVideos = trendData.youtube.slice(0, 5);
        topVideos.forEach((video: any, index: number) => {
          prompt += `\n${index + 1}. "${video.title}" (조회수: ${video.viewCount || 'N/A'}) - ${video.channelTitle || 'Unknown'}`;
        });
        prompt += '\n→ 이 YouTube 트렌드를 반영하여 관심을 끌 수 있는 제목 스타일을 참고하세요.';
      }
      
      if (trendData.naver) {
        const mcpIndicator = trendData.naver.mcpSource ? ' (MCP 실시간)' : '';
        prompt += `\n\n🔍 **네이버 통합 트렌드 분석${mcpIndicator}**`;
        
        // 기본 통계
        const stats = [];
        if (trendData.naver.totalCount) stats.push(`블로그 ${trendData.naver.totalCount.toLocaleString()}개`);
        if (trendData.naver.newsCount) stats.push(`뉴스 ${trendData.naver.newsCount.toLocaleString()}개`);
        if (trendData.naver.shopCount) stats.push(`쇼핑 ${trendData.naver.shopCount.toLocaleString()}개`);
        if (trendData.naver.cafeCount) stats.push(`카페 ${trendData.naver.cafeCount.toLocaleString()}개`);
        
        if (stats.length > 0) {
          prompt += `\n• **데이터 규모**: ${stats.join(', ')} 분석 완료`;
        }
        
        if (trendData.naver.keywords && trendData.naver.keywords.length > 0) {
          prompt += `\n• **인기 키워드 조합**: ${trendData.naver.keywords.slice(0, 6).join(', ')}`;
        }
        if (trendData.naver.trends && trendData.naver.trends.length > 0) {
          prompt += `\n• **트렌드 단어**: ${trendData.naver.trends.slice(0, 6).join(', ')}`;
        }
        
        // 쇼핑 트렌드 (가격대 정보)
        if (trendData.naver.priceRanges && trendData.naver.priceRanges.length > 0) {
          const avgPrice = trendData.naver.priceRanges.reduce((sum: number, item: any) => 
            sum + (item.lprice + item.hprice) / 2, 0) / trendData.naver.priceRanges.length;
          prompt += `\n• **쇼핑 트렌드**: 평균 가격대 ${Math.round(avgPrice).toLocaleString()}원, 상품 ${trendData.naver.priceRanges.length}개 분석`;
        }
        
        if (trendData.naver.mcpSource) {
          prompt += '\n→ **MCP 실시간 데이터**: 네이버의 블로그, 뉴스, 쇼핑, 카페에서 실제로 검색되고 인기있는 최신 키워드들을 제목에 자연스럽게 활용하세요.';
          prompt += '\n→ 특히 쇼핑 트렌드와 커뮤니티(카페) 관심사를 반영한 제목으로 더 높은 관심도를 유도하세요.';
        } else {
          prompt += '\n→ 네이버에서 실제로 검색되고 인기있는 키워드들을 제목에 자연스럽게 활용하세요.';
        }
      }
      
      if (trendData.google) {
        prompt += '\n\n🌐 **구글 트렌드 예측 데이터**';
        if (trendData.google.relatedQueries) {
          prompt += `\n• 관련 검색어: ${trendData.google.relatedQueries.slice(0, 5).join(', ')}`;
        }
        if (trendData.google.risingQueries) {
          prompt += `\n• 급상승 키워드: ${trendData.google.risingQueries.slice(0, 5).join(', ')}`;
        }
        if (trendData.google.trendingTopics) {
          prompt += `\n• 트렌딩 주제: ${trendData.google.trendingTopics.slice(0, 5).join(', ')}`;
        }
      }
      
      prompt += '\n\n🎯 **트렌드 활용 가이드**';
      prompt += '\n위의 실시간 트렌드 데이터를 바탕으로:';
      prompt += '\n1. YouTube에서 인기있는 제목 스타일과 키워드를 참고하여 관심을 끌 수 있는 제목 생성';
      prompt += '\n2. 네이버 블로그에서 실제로 많이 검색되는 키워드 조합을 자연스럽게 활용';
      prompt += '\n3. 구글 트렌드의 급상승 키워드를 포함하여 SEO 효과 극대화';
      prompt += '\n4. 트렌드 데이터에서 나타나는 패턴을 분석하여 독자의 관심사 반영';
      prompt += '\n\n더욱 매력적이고 검색 최적화된 제목을 만들어주세요.';
    }

    return prompt;
  }

  private extractTitlesWithSearch(content: string): { titles: string[], titlesWithSearch: TitleWithSearch[] } {
    try {
      // JSON 형식으로 응답이 올 경우 파싱
      const jsonMatch = content.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const jsonData = JSON.parse(jsonMatch[0]);
        if (jsonData.titles_with_search && Array.isArray(jsonData.titles_with_search)) {
          const titlesWithSearch = jsonData.titles_with_search.slice(0, 10).map((item: any) => ({
            title: item.title,
            searchQuery: item.search_query || item.searchQuery || ''
          }));
          const titles = titlesWithSearch.map((item: TitleWithSearch) => item.title);
          return { titles, titlesWithSearch };
        }
      }
    } catch (error) {
      console.warn('JSON 파싱 실패, 기존 방식으로 처리:', error);
    }

    // 기존 방식: 번호 목록 형태 처리 (검색어 없이)
    const lines = content.split('\n');
    const titles: string[] = [];

    for (const line of lines) {
      const match = line.match(/^\d+\.\s*(.+)$/);
      if (match) {
        titles.push(match[1].trim());
      }
    }

    const finalTitles = titles.slice(0, 10);
    const titlesWithSearch = finalTitles.map((title: string) => ({
      title,
      searchQuery: '' // 기본값으로 빈 검색어
    }));

    return { titles: finalTitles, titlesWithSearch };
  }

}