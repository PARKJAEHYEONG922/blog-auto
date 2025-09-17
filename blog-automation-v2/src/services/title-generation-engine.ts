import { mcpClientManager } from './mcp-client';
import { LLMClientFactory, LLMMessage } from './llm-client-factory';

export interface TitleGenerationRequest {
  keyword: string;
  platform: string;
  contentType: string;
  tone: string;
  customPrompt?: string;
  blogDescription?: string;
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
      
      // 응답에서 제목 목록 추출
      const titles = this.extractTitles(response.content);
      
      return titles;
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
    const platformInfo: { [key: string]: string } = {
      'naver': '네이버 블로그 (SEO 최적화 필요)',
      'tistory': '티스토리 (검색엔진 친화적)',
      'blogspot': '블로그스팟 (글로벌 SEO)',
      'wordpress': '워드프레스 (다양한 플러그인)'
    };

    const contentTypeInfo: { [key: string]: string } = {
      'info': '정보/가이드형',
      'review': '후기/리뷰형',
      'compare': '비교/추천형',
      'howto': '노하우형'
    };


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

    return `${platformInfo[request.platform] || request.platform}에 최적화된 '${contentTypeInfo[request.contentType] || request.contentType}' 스타일의 제목 10개를 추천해주세요.

**발행 플랫폼**: ${platformInfo[request.platform] || request.platform}
**콘텐츠 타입**: ${contentTypeInfo[request.contentType] || request.contentType}

**${contentTypeInfo[request.contentType] || request.contentType} 특징**:
- 접근법: ${guideline.approach}
- 핵심 키워드: ${guideline.keywords.join(', ')}
- 중점 영역: ${guideline.focusAreas.join(', ')}

**제목 생성 규칙**:
1. 메인키워드를 자연스럽게 포함
2. 클릭 유도와 궁금증 자극
3. 30-60자 내외 권장
4. ${contentTypeInfo[request.contentType] || request.contentType}의 특성 반영
5. ${platformInfo[request.platform] || request.platform} SEO 최적화
6. **이모티콘 절대 사용 금지** (🚫, ✅, 💯 등 모든 이모티콘 금지. 순수 한글/영문 텍스트만 사용)
7. 구체적 년도 표기 금지 (2024, 2025 등 특정 년도 사용 금지. "최신", "현재" 등으로 대체)

제목은 다음 형식으로 응답하세요:
1. [제목1]
2. [제목2]
3. [제목3]
4. [제목4]
5. [제목5]
6. [제목6]
7. [제목7]
8. [제목8]
9. [제목9]
10. [제목10]`;
  }

  private buildUserPrompt(request: TitleGenerationRequest, trendData?: any): string {
    let prompt = `**메인키워드**: ${request.keyword}`;

    // 블로그 설명 추가
    if (request.blogDescription) {
      prompt = `# AI 역할 설정
${request.blogDescription}

${prompt}`;
    }

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

  private extractTitles(content: string): string[] {
    const lines = content.split('\n');
    const titles: string[] = [];

    for (const line of lines) {
      const match = line.match(/^\d+\.\s*(.+)$/);
      if (match) {
        titles.push(match[1].trim());
      }
    }

    return titles.slice(0, 10);
  }

}