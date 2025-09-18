import { LLMClientFactory, LLMMessage, LLMTool } from './llm-client-factory';

export interface TitleGenerationRequest {
  keyword: string;
  subKeywords?: string[];
  platform: string;
  platformName: string; // UI에서 한국어 플랫폼명 전달
  contentType: string;
  contentTypeName: string; // UI에서 한국어 콘텐츠타입명 전달
  reviewType?: string; // 후기 유형 ID
  reviewTypeName?: string; // 후기 유형 한국어명
  tone: string;
  customPrompt?: string;
  blogDescription?: string;
  mode: 'fast' | 'accurate';
}

export interface TitleWithSearch {
  title: string;
  searchQuery: string; // 서치키워드
}

export interface TitleGenerationResult {
  titles: string[];
  titlesWithSearch: TitleWithSearch[];
  metadata: {
    mode: string;
    sources: string[];
    processingTime: number;
    mcpEnabled?: boolean;
    mcpTools?: any;
  };
}

export class TitleGenerationEngine {
  async generateTitles(request: TitleGenerationRequest): Promise<TitleGenerationResult> {
    const startTime = Date.now();

    try {
      // 간단한 LLM 제목 생성만 수행
      const result = await this.generateTitlesWithLLM(request);

      const processingTime = Date.now() - startTime;

      return {
        titles: result.titles,
        titlesWithSearch: result.titlesWithSearch,
        metadata: {
          mode: 'fast',
          sources: ['AI 기반 제목 생성'],
          processingTime,
          mcpEnabled: false,
          mcpTools: null
        }
      };
    } catch (error) {
      console.error('제목 생성 실패:', error);
      throw error;
    }
  }



  private async generateTitlesWithLLM(
    request: TitleGenerationRequest
  ): Promise<{ titles: string[], titlesWithSearch: TitleWithSearch[] }> {
    try {
      console.log('🤖 정보처리 클라이언트 요청 중...');
      const informationClient = LLMClientFactory.getInformationClient();
      console.log('✅ 정보처리 클라이언트 획득 성공:', informationClient);

      // 프롬프트 구성
      const systemPrompt = this.buildSystemPrompt(request);
      const userPrompt = this.buildUserPrompt(request);

      const messages: LLMMessage[] = [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userPrompt }
      ];

      console.log('🤖 [LLM 요청] 시스템 프롬프트:', systemPrompt.substring(0, 200) + '...');
      console.log('🤖 [LLM 요청] 유저 프롬프트:', userPrompt.substring(0, 200) + '...');

      // 도구 호출 대신 일반적인 텍스트 생성만 사용
      const response = await informationClient.generateText(messages);
      
      console.log('🤖 [LLM 응답] 받음:', response.content.substring(0, 200) + '...');
      
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

  private async buildMCPTools(availableTools: any): Promise<LLMTool[]> {
    const tools: LLMTool[] = [];

    // 네이버 도구들
    if (availableTools.naver && availableTools.naver.length > 0) {
      tools.push({
        name: 'naver_search_all',
        description: '네이버 통합 검색 (블로그, 뉴스, 쇼핑, 카페, 지식인)',
        parameters: {
          type: 'object',
          properties: {
            query: {
              type: 'string',
              description: '검색할 키워드'
            },
            display: {
              type: 'number',
              description: '검색 결과 개수 (최대 100)',
              default: 10
            }
          },
          required: ['query']
        }
      });

      tools.push({
        name: 'naver_blog_search',
        description: '네이버 블로그 검색',
        parameters: {
          type: 'object',
          properties: {
            query: {
              type: 'string',
              description: '검색할 키워드'
            },
            display: {
              type: 'number',
              description: '검색 결과 개수 (최대 100)',
              default: 10
            }
          },
          required: ['query']
        }
      });
    }

    // YouTube 도구들
    if (availableTools.youtube && availableTools.youtube.length > 0) {
      tools.push({
        name: 'youtube_search',
        description: 'YouTube 비디오 검색',
        parameters: {
          type: 'object',
          properties: {
            query: {
              type: 'string',
              description: '검색할 키워드'
            },
            maxResults: {
              type: 'number',
              description: '검색 결과 개수 (최대 50)',
              default: 10
            }
          },
          required: ['query']
        }
      });
    }

    return tools;
  }

  private getContentGuideline(contentType: string): any {
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

    return contentGuidelines[contentType] || contentGuidelines['info'];
  }

  private getReviewDetailGuideline(reviewType: string): any {
    const reviewGuidelines: { [key: string]: any } = {
      'self-purchase': {
        description: '직접 구매해서 써본 솔직한 개인 후기',
        transparency: '내돈내산이라는 점을 자연스럽게 어필하며 솔직하고 신뢰성 있는 톤'
      },
      'sponsored': {
        description: '브랜드에서 제공받은 제품의 정직한 리뷰',
        transparency: '협찬임을 명시하되 객관적이고 균형잡힌 평가를 강조하는 톤'
      },
      'experience': {
        description: '체험단 참여를 통한 제품 사용 후기',
        transparency: '체험 기회를 통해 얻은 경험을 바탕으로 한 상세한 후기'
      },
      'rental': {
        description: '렌탈 서비스를 이용한 제품 사용 후기',
        transparency: '렌탈 경험을 바탕으로 한 실용적이고 현실적인 후기'
      }
    };

    return reviewGuidelines[reviewType] || {};
  }

  private buildSystemPrompt(request: TitleGenerationRequest): string {
    // 해당 유형의 지침 가져오기
    const contentGuideline = this.getContentGuideline(request.contentType);
    const approach = contentGuideline.approach || '';
    const keywords = contentGuideline.keywords || [];
    const focusAreas = contentGuideline.focusAreas || [];

    // 후기 세부 유형 지침 가져오기 (후기/리뷰형일 때만)
    const reviewGuideline = (request.reviewType && request.contentType === 'review') 
      ? this.getReviewDetailGuideline(request.reviewType) : {};

    const systemPrompt = `네이버 블로그 상위 노출에 유리한 '${request.contentTypeName}' 스타일의 제목 10개를 추천해주세요.

**${request.contentTypeName} 특징**:
- 접근법: ${approach}
- 핵심 키워드: ${keywords.join(', ')}
- 중점 영역: ${focusAreas.join(', ')}${reviewGuideline.description ? `

**후기 세부 유형**: ${request.reviewTypeName}
- 설명: ${reviewGuideline.description}
- 적절한 톤: ${reviewGuideline.transparency}` : ''}

**제목 생성 규칙**:
1. 메인키워드를 자연스럽게 포함
2. 클릭 유도와 궁금증 자극
3. 30-60자 내외 권장
4. ${request.contentTypeName}의 특성 반영
5. 네이버 블로그 SEO 최적화
6. 이모티콘 사용 금지 (텍스트만 사용)
7. 구체적 년도 표기 금지 (2024, 2025 등 특정 년도 사용 금지. "최신", "현재" 등으로 대체)

**출력 형식**:
JSON 형태로 정확히 10개 제목과 각 제목에 맞는 블로그 검색어를 함께 반환해주세요.

각 제목마다 "해당 제목과 유사한 내용의 블로그를 찾기 위한 네이버 블로그 검색어"를 함께 생성해주세요.
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

    return systemPrompt;
  }

  private buildUserPrompt(request: TitleGenerationRequest): string {
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
    let subKeywordInstruction = "";
    if (request.subKeywords && request.subKeywords.length > 0) {
      prompt += `\n**보조키워드**: ${request.subKeywords.join(', ')}`;
      subKeywordInstruction = "- 보조키워드는 필수는 아니지만, 적절히 활용하면 더 구체적인 제목 생성 가능";
    }

    // 4. 추가 요청사항 (있는 경우)
    if (request.customPrompt) {
      prompt += `\n\n**추가 요청사항**: ${request.customPrompt}`;
    }

    // 5. 보조키워드 사용 안내 (있는 경우)
    if (subKeywordInstruction) {
      prompt += `\n\n${subKeywordInstruction}`;
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