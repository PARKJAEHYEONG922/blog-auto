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
      // YouTube 트렌드 데이터 수집 (MCP 사용)
      if (await mcpClientManager.isConnected('youtube')) {
        try {
          const youtubeData = await mcpClientManager.callTool('youtube', 'search', {
            query: keyword,
            maxResults: 5
          });
          trendData.youtube = youtubeData;
          sources.push('YouTube MCP');
        } catch (error) {
          console.warn('YouTube MCP 호출 실패:', error);
        }
      }

      // 네이버 트렌드 데이터 수집 시뮬레이션
      try {
        // 실제로는 naver-search-mcp 사용
        const naverData = {
          keywords: [`${keyword} 가이드`, `${keyword} 방법`, `${keyword} 추천`],
          trends: ['완벽', '초보자', '실전', '노하우']
        };
        trendData.naver = naverData;
        sources.push('Naver DataLab (시뮬레이션)');
      } catch (error) {
        console.warn('네이버 데이터 수집 실패:', error);
      }

      // 구글 트렌드 데이터 수집 시뮬레이션
      try {
        // 실제로는 crawl4ai-mcp 사용
        const googleData = {
          relatedQueries: [`${keyword} 비교`, `${keyword} 후기`, `${keyword} 장단점`],
          risingQueries: [`${keyword} 2024`, `${keyword} 최신`, `${keyword} 신제품`]
        };
        trendData.google = googleData;
        sources.push('Google Trends (시뮬레이션)');
      } catch (error) {
        console.warn('구글 데이터 수집 실패:', error);
      }

    } catch (error) {
      console.error('트렌드 데이터 수집 실패:', error);
    }

    return trendData;
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
      prompt += '\n\n=== 트렌드 분석 데이터 ===';
      
      if (trendData.youtube) {
        prompt += `\nYouTube 인기 콘텐츠: ${JSON.stringify(trendData.youtube)}`;
      }
      
      if (trendData.naver) {
        prompt += `\n네이버 관련 키워드: ${trendData.naver.keywords.join(', ')}`;
        prompt += `\n네이버 트렌드: ${trendData.naver.trends.join(', ')}`;
      }
      
      if (trendData.google) {
        prompt += `\n구글 관련 검색어: ${trendData.google.relatedQueries.join(', ')}`;
        prompt += `\n구글 급상승 검색어: ${trendData.google.risingQueries.join(', ')}`;
      }
      
      prompt += '\n\n위 트렌드 데이터를 참고하여 더욱 매력적이고 검색에 최적화된 제목을 만들어주세요.';
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