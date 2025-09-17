import { mcpClientManager } from './mcp-client';
import { LLMClientFactory, LLMMessage } from './llm-client-factory';

export interface TitleGenerationRequest {
  keyword: string;
  platform: string;
  contentType: string;
  tone: string;
  customPrompt?: string;
  mode: 'fast' | 'accurate';
}

export interface TitleGenerationResult {
  titles: string[];
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
      const titles = await this.generateTitlesWithLLM(request, trendData);

      const processingTime = Date.now() - startTime;

      return {
        titles,
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
  ): Promise<string[]> {
    const informationClient = LLMClientFactory.getInformationClient();

    // 프롬프트 구성
    const systemPrompt = this.buildSystemPrompt(request);
    const userPrompt = this.buildUserPrompt(request, trendData);

    const messages: LLMMessage[] = [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: userPrompt }
    ];

    try {
      const response = await informationClient.generateText(messages);
      
      // 응답에서 제목 목록 추출
      const titles = this.extractTitles(response.content);
      
      return titles;
    } catch (error) {
      console.error('LLM 제목 생성 실패:', error);
      // 폴백: 기본 제목들 반환
      return this.generateFallbackTitles(request.keyword);
    }
  }

  private buildSystemPrompt(request: TitleGenerationRequest): string {
    const platformInfo: { [key: string]: string } = {
      'naver': '네이버 블로그 (SEO 최적화 필요)',
      'tistory': '티스토리 (검색엔진 친화적)',
      'blogspot': '블로그스팟 (글로벌 SEO)',
      'wordpress': '워드프레스 (다양한 플러그인)'
    };

    const contentTypeInfo: { [key: string]: string } = {
      'info': '정보 제공형 콘텐츠',
      'review': '후기 및 리뷰형 콘텐츠',
      'compare': '비교 분석형 콘텐츠',
      'howto': '노하우 및 가이드형 콘텐츠'
    };

    const toneInfo: { [key: string]: string } = {
      'formal': '정중하고 전문적인 존댓말',
      'casual': '친근하고 편안한 반말',
      'friendly': '따뜻하면서도 예의바른 존댓말'
    };

    return `당신은 블로그 제목 생성 전문가입니다.

플랫폼: ${platformInfo[request.platform] || request.platform}
콘텐츠 타입: ${contentTypeInfo[request.contentType] || request.contentType}
말투: ${toneInfo[request.tone] || request.tone}

다음 규칙을 따라 제목을 생성하세요:
1. 30-40자 내외의 길이
2. 클릭률을 높이는 매력적인 키워드 포함
3. SEO에 최적화된 구조
4. 해당 플랫폼의 특성에 맞는 스타일
5. 정확히 5개의 제목을 생성

제목은 다음 형식으로 응답하세요:
1. [제목1]
2. [제목2]
3. [제목3]
4. [제목4]
5. [제목5]`;
  }

  private buildUserPrompt(request: TitleGenerationRequest, trendData?: any): string {
    let prompt = `키워드: "${request.keyword}"에 대한 ${request.contentType} 블로그 제목을 생성해주세요.`;

    if (request.customPrompt) {
      prompt += `\n\n추가 요청사항: ${request.customPrompt}`;
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

  private extractTitles(content: string): string[] {
    const lines = content.split('\n');
    const titles: string[] = [];

    for (const line of lines) {
      const match = line.match(/^\d+\.\s*(.+)$/);
      if (match) {
        titles.push(match[1].trim());
      }
    }

    // 5개가 안 되면 기본 제목으로 채우기
    while (titles.length < 5) {
      titles.push(`기본 제목 ${titles.length + 1}`);
    }

    return titles.slice(0, 5);
  }

  private generateFallbackTitles(keyword: string): string[] {
    return [
      `${keyword} 완벽 가이드 - 초보자도 쉽게 따라하는 방법`,
      `${keyword} 추천 TOP 10 - 2024년 최신 트렌드`,
      `${keyword} 후기 솔직 리뷰 - 장단점 총정리`,
      `${keyword} 비교 분석 - 어떤 것을 선택해야 할까?`,
      `${keyword} 노하우 공유 - 전문가의 실전 팁`
    ];
  }
}