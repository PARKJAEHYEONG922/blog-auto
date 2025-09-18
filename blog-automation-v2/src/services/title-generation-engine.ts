import { LLMClientFactory, LLMMessage, LLMTool } from './llm-client-factory';
import { getContentTypeDescription, getReviewTypeDescription } from '../constants/content-options';

export interface TitleGenerationRequest {
  keyword: string; // 기존 호환성을 위해 유지 (searchKeyword와 동일)
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


  private buildSystemPrompt(request: TitleGenerationRequest): string {
    // 공통 모듈에서 설명 가져오기
    const contentTypeDescription = getContentTypeDescription(request.contentType);
    const reviewTypeDescription = request.reviewType ? getReviewTypeDescription(request.reviewType) : '';

    const systemPrompt = `네이버 블로그 상위 노출에 유리한 '${request.contentTypeName}' 스타일의 제목 10개를 추천해주세요.

**${request.contentTypeName} 특징**:
- ${contentTypeDescription}

${request.reviewType ? `**후기 세부 유형**: ${request.reviewTypeName}
- ${reviewTypeDescription}` : ''}

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