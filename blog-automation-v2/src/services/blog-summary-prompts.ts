import { BlogContent } from './blog-crawler';

export interface SummaryPromptRequest {
  selectedTitle: string;
  searchKeyword: string;
  mainKeyword: string;
  contentType: string;
  contentTypeDescription?: string;
  reviewType?: string;
  reviewTypeDescription?: string;
  competitorBlogs: BlogContent[];
  subKeywords?: string[];
}

export class BlogSummaryPrompts {
  /**
   * 정보요약 AI용 1차 가공 프롬프트 생성 - JSON 입력 구조화
   */
  static generateContentSummaryPrompt(request: SummaryPromptRequest): string {
    // JSON 입력 데이터 구조화
    const inputData = {
      target_info: {
        selected_title: request.selectedTitle,
        search_keyword: request.searchKeyword,
        main_keyword: request.mainKeyword,
        content_type: request.contentType,
        content_type_description: request.contentTypeDescription || ''
      } as any,
      competitor_blogs: [] as any[]
    };

    // 후기형인 경우 후기 유형 정보 추가
    if (request.reviewType && request.reviewTypeDescription) {
      inputData.target_info.review_type = request.reviewType;
      inputData.target_info.review_type_description = request.reviewTypeDescription;
    }

    // 보조키워드가 있으면 추가
    if (request.subKeywords && request.subKeywords.length > 0) {
      inputData.target_info.sub_keywords = request.subKeywords.join(', ');
    }

    // 경쟁 블로그 데이터 추가 (성공한 것만)
    const successfulBlogs = request.competitorBlogs.filter(blog => blog.success);
    for (let i = 0; i < successfulBlogs.length; i++) {
      const blog = successfulBlogs[i];
      inputData.competitor_blogs.push({
        blog_number: i + 1,
        title: blog.title || '제목 없음',
        content: (blog.textContent || '내용 없음').substring(0, 2000) // 내용 길이 제한
      });
    }

    // JSON 문자열로 변환
    const jsonInput = JSON.stringify(inputData, null, 2);

    // 1차 가공 프롬프트 (정보요약 AI용) - JSON 입력 구조
    const summaryPrompt = `아래 JSON 데이터를 분석해서 다음 형식으로 정확히 출력해주세요:

## 1. 경쟁 블로그 제목들
- (분석한 ${successfulBlogs.length}개 블로그들의 제목을 나열)

## 2. 핵심 키워드
- (자주 나오는 관련 키워드들을 나열)

## 3. 필수 내용
- (모든 글이 다루는 공통 주제들을 정리)

## 4. 주요 포인트
- (각 글이 중점적으로 다루는 핵심 내용들을 정리)

## 5. 부족한 점
- (기존 글들이 놓친 부분이나 개선 가능한 점들을 정리)

## 6. 추가 정보 수집 제안
선택된 제목 "${request.selectedTitle}"에 맞는 고품질 글을 작성하기 위해 추가로 필요한 정보를 분석해주세요:

**네이버 쇼핑 API 수집 필요성**: 
- 제품 가격, 리뷰, 구매 관련 정보가 필요한가? (필요/불필요)
- 이유: (간단히 설명)

**네이버 뉴스 API 수집 필요성**:
- 최신 동향, 트렌드, 뉴스 정보가 필요한가? (필요/불필요)  
- 이유: (간단히 설명)

**JSON 데이터 설명**:
- target_info: 내가 작성할 블로그의 정보
  - selected_title: 내가 선택한 블로그 제목 (실제 작성할 제목)
  - search_keyword: 관련 블로그를 찾기 위해 사용한 검색 키워드
  - main_keyword: 내 글의 핵심 타겟 키워드 (SEO 목표)
  - content_type: 내 글의 유형 (${request.contentType})
  - content_type_description: 콘텐츠 유형 상세 설명 (${request.contentTypeDescription || '없음'})${request.reviewType ? `
  - review_type: 후기 유형 (${request.reviewType})
  - review_type_description: 후기 유형 상세 설명 (${request.reviewTypeDescription || '없음'})` : ''}
  - sub_keywords: 보조 키워드들 (있는 경우에만 포함)
- competitor_blogs: search_keyword로 검색해서 찾은 경쟁사 분석용 참고 블로그 ${successfulBlogs.length}개 (제목과 본문 내용)

**분석 데이터**:
\`\`\`json
${jsonInput}
\`\`\`

위 JSON 데이터를 기반으로 '${request.mainKeyword}' 키워드와 '${request.contentType}' 컨텐츠 유형에 맞춰 분석해주세요.
각 항목마다 구체적이고 실용적인 내용을 포함해주세요.`;

    return summaryPrompt;
  }
}