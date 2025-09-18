import { LLMClientFactory, LLMMessage } from './llm-client-factory';
import { CollectedBlogData } from './data-collection-engine';

export interface BlogSelectionRequest {
  targetTitle: string;
  mainKeyword: string;
  subKeywords?: string[];
  searchKeyword: string;
  contentType: string;
  contentTypeDescription?: string;
  reviewType?: string;
  reviewTypeDescription?: string;
  blogTitles: CollectedBlogData[];
}

export interface SelectedBlogTitle {
  title: string;
  url: string;
  relevanceReason: string;
}

export interface BlogSelectionResult {
  selectedTitles: SelectedBlogTitle[];
}

export class BlogTitleSelector {
  async selectTopBlogs(request: BlogSelectionRequest): Promise<BlogSelectionResult> {
    try {
      console.log('🤖 정보요약 AI로 상위 10개 블로그 선별 시작');
      
      const informationClient = LLMClientFactory.getInformationClient();
      
      // 레거시 프롬프트 사용
      const userPrompt = this.buildLegacyPrompt(request);
      
      const messages: LLMMessage[] = [
        { role: 'user', content: userPrompt }
      ];
      
      console.log('🤖 [LLM 요청] 블로그 제목 선별 요청');
      
      const response = await informationClient.generateText(messages);
      
      console.log('🤖 [LLM 응답] 블로그 선별 결과 받음');
      
      // JSON 응답 파싱
      const result = this.parseSelectionResult(response.content, request.blogTitles);
      
      console.log(`✅ 상위 ${result.selectedTitles.length}개 블로그 선별 완료`);
      
      return result;
      
    } catch (error) {
      console.error('블로그 제목 선별 실패:', error);
      
      // 오류 시 순위대로 상위 10개 반환
      const fallbackResult: BlogSelectionResult = {
        selectedTitles: request.blogTitles.slice(0, 10).map((blog) => ({
          title: blog.title,
          url: blog.url,
          relevanceReason: '자동 선별 (AI 분석 실패)'
        }))
      };
      
      return fallbackResult;
    }
  }
  
  private buildLegacyPrompt(request: BlogSelectionRequest): string {
    // 블로그 제목들 텍스트 구성 (레거시와 동일)
    const titlesText = request.blogTitles.map((blog, index) => 
      `${index + 1}. ${blog.title}`
    ).join('\n');
    
    // 보조키워드 텍스트 준비 (레거시와 동일)
    let subKeywordsText = "";
    let subKeywordsCriteria = "";
    if (request.subKeywords && request.subKeywords.length > 0) {
      const subKeywordsStr = request.subKeywords.join(', ');
      subKeywordsText = `**보조 키워드**: ${subKeywordsStr}`;
      subKeywordsCriteria = `6. 보조 키워드(${subKeywordsStr})와 관련성이 있는 제목`;
    }
    
    // 콘텐츠 유형 설명 구성
    let contentTypeInfo = `**콘텐츠 유형**: ${request.contentType}`;
    if (request.contentTypeDescription) {
      contentTypeInfo += ` (${request.contentTypeDescription})`;
    }
    
    // 후기 유형 정보 구성 (있는 경우)
    let reviewTypeInfo = '';
    if (request.reviewType) {
      reviewTypeInfo = `\n**후기 유형**: ${request.reviewType}`;
      if (request.reviewTypeDescription) {
        reviewTypeInfo += ` (${request.reviewTypeDescription})`;
      }
    }

    return `네이버 블로그에서 '${request.searchKeyword}' 키워드로 검색한 블로그 제목들 중에서, 아래 조건에 가장 적합한 상위 10개를 선별해주세요.

**타겟 제목**: ${request.targetTitle}
**메인 키워드**: ${request.mainKeyword}
${subKeywordsText}
**검색 키워드**: ${request.searchKeyword}
${contentTypeInfo}${reviewTypeInfo}

**선별 기준**:
1. 타겟 제목 "${request.targetTitle}"과 가장 주제적 관련성이 높은 글 (최우선)
2. 메인 키워드와 직접적으로 연관된 내용
3. ${request.contentType} 유형에 적합한 접근방식의 글${request.reviewType ? ` (${request.reviewType} 관점)` : ''}
4. 구체적이고 실용적인 정보를 담고 있을 것으로 예상되는 제목
5. 광고성이나 홍보성보다는 정보성 콘텐츠로 보이는 제목
${subKeywordsCriteria}

**검색된 블로그 제목들**:
${titlesText}

**중요**: 타겟 제목과 가장 관련성이 높은 블로그부터 1위, 2위, 3위 순서로 정확히 관련도 순서대로 배치해주세요.

**출력 형식**:
타겟 제목과의 관련도가 가장 높은 순서대로 상위 10개를 JSON 형태로 선별해주세요.

{
  "selected_titles": [
    {
      "title": "타겟 제목과 가장 관련성 높은 제목 (1위)",
      "relevance_reason": "타겟 제목과의 관련성 및 선별 이유"
    },
    {
      "title": "두 번째로 관련성 높은 제목 (2위)",
      "relevance_reason": "타겟 제목과의 관련성 및 선별 이유"
    },
    ...
    {
      "title": "열 번째로 관련성 높은 제목 (10위)",
      "relevance_reason": "타겟 제목과의 관련성 및 선별 이유"
    }
  ]
}

반드시 타겟 제목 "${request.targetTitle}"과의 관련도를 기준으로 1위부터 10위까지 순서를 매겨서 반환해주세요.`;
  }
  
  private parseSelectionResult(content: string, originalBlogs: CollectedBlogData[]): BlogSelectionResult {
    try {
      // JSON 추출
      const jsonMatch = content.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        const jsonData = JSON.parse(jsonMatch[0]);
        
        if (jsonData.selected_titles && Array.isArray(jsonData.selected_titles)) {
          console.log(`🎯 AI가 선별한 제목 ${jsonData.selected_titles.length}개 처리 시작`);
          
          const selectedTitles: SelectedBlogTitle[] = jsonData.selected_titles.slice(0, 10).map((item: any, aiIndex: number) => {
            console.log(`\n🔍 [${aiIndex + 1}] AI 선별 제목: "${item.title}"`);
            
            // 제목으로 원본 블로그 찾기 (정확 매칭 + 부분 매칭)
            let originalBlog = originalBlogs.find(blog => blog.title === item.title);
            console.log(`   정확 매칭: ${originalBlog ? '성공' : '실패'}`);
            
            // 정확 매칭 실패 시 부분 매칭 시도
            if (!originalBlog) {
              originalBlog = originalBlogs.find(blog => 
                blog.title.includes(item.title) || item.title.includes(blog.title)
              );
              console.log(`   부분 매칭: ${originalBlog ? '성공' : '실패'}`);
            }
            
            // 여전히 매칭 실패 시 인덱스 기반 매칭 (순서대로)
            if (!originalBlog && originalBlogs.length > 0) {
              const index = Math.min(originalBlogs.length - 1, aiIndex);
              originalBlog = originalBlogs[index];
              console.log(`   인덱스 매칭: ${index}번째 블로그 사용`);
            }
            
            const url = originalBlog?.url || '';
            console.log(`   매칭된 원본: "${originalBlog?.title || 'N/A'}"`);
            console.log(`   추출된 URL: "${url}" (타입: ${typeof url}, 길이: ${url?.length || 0})`);
            console.log(`   URL 유효성: ${url && url.includes('blog.naver.com')}`);
            
            if (!url) {
              console.error(`❌ [${aiIndex + 1}] URL을 찾을 수 없음: "${item.title}"`);
            }
            
            return {
              title: item.title,
              url: url,
              relevanceReason: item.relevance_reason || '선별됨'
            };
          }).filter((blog: SelectedBlogTitle) => {
            const hasUrl = !!blog.url;
            if (!hasUrl) {
              console.warn(`⚠️ URL이 없어 제외됨: "${blog.title}"`);
            }
            return hasUrl;
          }); // URL이 있는 것만 필터링
          
          console.log(`✅ 최종 선별된 블로그: ${selectedTitles.length}개 (URL 유효)`);
          selectedTitles.forEach((blog, index) => {
            console.log(`   ${index + 1}. "${blog.title}" - ${blog.url}`);
          });
          
          return { selectedTitles };
        }
      }
    } catch (error) {
      console.warn('블로그 선별 결과 JSON 파싱 실패:', error);
    }
    
    // 파싱 실패 시 상위 10개 반환
    return {
      selectedTitles: originalBlogs.slice(0, 10).map((blog) => ({
        title: blog.title,
        url: blog.url,
        relevanceReason: '자동 선별 (파싱 실패)'
      }))
    };
  }
}