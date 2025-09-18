import { BlogContent } from './blog-crawler';
import { CollectedYouTubeData, DataCollectionRequest } from './data-collection-engine';
import { BaseRequestInfo } from '../types/common-interfaces';
import { getContentTypeDescription, getReviewTypeDescription } from '../constants/content-options';

export interface SummaryPromptRequest extends BaseRequestInfo {
  competitorBlogs: BlogContent[];
  // youtubeVideos 제거 - 별도 분석으로 분리
}

export class AnalysisPrompts {
  /**
   * 블로그 콘텐츠 분석용 프롬프트 생성 - JSON 입력 구조화
   */
  static generateBlogAnalysisPrompt(request: SummaryPromptRequest): string {
    // JSON 입력 데이터 구조화
    const inputData = {
      target_info: {
        selected_title: request.selectedTitle,
        search_keyword: request.searchKeyword,
        main_keyword: request.mainKeyword,
        content_type: request.contentType,
        content_type_description: getContentTypeDescription(request.contentType)
      } as any,
      competitor_blogs: [] as any[]
    };

    // 후기형인 경우 후기 유형 정보 추가
    if (request.reviewType) {
      inputData.target_info.review_type = request.reviewType;
      inputData.target_info.review_type_description = getReviewTypeDescription(request.reviewType);
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
        content: (blog.textContent || '내용 없음').substring(0, 3000) // 내용 길이 제한
      });
    }

    // 블로그 분석 프롬프트
    const summaryPrompt = `"${request.selectedTitle}" 제목의 블로그 글 작성을 위한 경쟁사 분석을 수행해주세요.

**분석 목적**:
아래 작성할 블로그 정보에 따라 경쟁사 블로그들을 분석하여, 우리가 선택한 제목으로 더 나은 블로그 글을 작성할 수 있도록 도움이 되는 인사이트를 제공해주세요.

**작성할 블로그 정보**:
\`\`\`json
${JSON.stringify(inputData.target_info, null, 2)}
\`\`\`

**데이터 설명**:
아래는 "${request.searchKeyword}" 키워드로 검색해서 찾은 ${successfulBlogs.length}개의 경쟁사 블로그들의 제목과 본문 내용입니다.

**분석 대상 데이터**:
\`\`\`json
${JSON.stringify(inputData.competitor_blogs, null, 2)}
\`\`\`

**요청 사항**:
위 경쟁사 블로그들을 분석하여 다음 JSON 형식으로 결과를 반환해주세요:

\`\`\`json
{
  "competitor_titles": [
    "분석한 경쟁 블로그 제목 1",
    "분석한 경쟁 블로그 제목 2"
  ],
  "core_keywords": [
    "자주 나오는 핵심 키워드 1",
    "자주 나오는 핵심 키워드 2"
  ],
  "essential_content": [
    "모든 블로그가 다루는 공통 주제 1",
    "모든 블로그가 다루는 공통 주제 2"
  ],
  "key_points": [
    "각 블로그가 중점적으로 다루는 핵심 내용 1",
    "각 블로그가 중점적으로 다루는 핵심 내용 2"
  ],
  "improvement_opportunities": [
    "기존 블로그들이 놓친 부분이나 개선 가능한 점 1",
    "기존 블로그들이 놓친 부분이나 개선 가능한 점 2"
  ]
}
\`\`\`

분석 지침:
- **중요**: 타겟 제목 "${request.selectedTitle}"과 관련성이 낮거나 주제가 맞지 않는 블로그는 분석에서 제외해주세요
- 관련성이 있는 블로그들만 선별하여 분석 수행
- 구체적이고 실용적인 내용을 우선적으로 포함
- 경쟁사 분석을 통해 차별화 포인트를 명확히 제시
- 반드시 위의 JSON 형식으로만 답변해주세요`;

    return summaryPrompt;
  }

  /**
   * YouTube 자막 분석용 프롬프트 생성
   */
  static generateYouTubeAnalysisPrompt(request: DataCollectionRequest, youtubeVideos: CollectedYouTubeData[]): string {
    // 영상별 자막 데이터 구성
    const videosText = youtubeVideos.map((video, index) => {
      let subtitlePreview = video.summary || '자막 없음';
      let lengthNote = '';
      
      if (video.summary && video.summary.length > 0) {
        const originalLength = video.summary.length;
        
        if (originalLength > 3000) {
          // 3000자 넘으면 앞 1500자 + 뒤 1500자 추출 (핵심 부분 유지)
          const firstPart = video.summary.substring(0, 1500);
          const lastPart = video.summary.substring(originalLength - 1500);
          subtitlePreview = firstPart + '\n\n...(중간 생략)...\n\n' + lastPart;
          lengthNote = `\n**원본 자막 길이**: ${originalLength.toLocaleString()}자 (전체 중 앞뒤 1500자씩 발췌)`;
        } else if (originalLength > 1500) {
          // 1500자 넘으면 1500자까지만
          subtitlePreview = video.summary.substring(0, 1500) + '...(이하 생략)';
          lengthNote = `\n**원본 자막 길이**: ${originalLength.toLocaleString()}자 (앞 1500자 발췌)`;
        } else {
          lengthNote = `\n**자막 길이**: ${originalLength.toLocaleString()}자 (전체)`;
        }
      }
      
      return `## ${index + 1}번 영상
**제목**: ${video.title}
**채널**: ${video.channelName}
**조회수**: ${video.viewCount.toLocaleString()}회
**길이**: ${Math.floor(video.duration / 60)}분 ${video.duration % 60}초${lengthNote}

**자막 내용**:
${subtitlePreview}

---`;
    }).join('\n\n');

    // target_info 구성
    const targetInfo = {
      selected_title: request.selectedTitle,
      search_keyword: request.keyword,
      main_keyword: request.mainKeyword || request.keyword,
      content_type: request.contentType,
      content_type_description: getContentTypeDescription(request.contentType)
    } as any;

    // 보조키워드가 있으면 추가
    if (request.subKeywords && request.subKeywords.length > 0) {
      targetInfo.sub_keywords = request.subKeywords.join(', ');
    }

    return `"${request.selectedTitle}" 제목의 블로그 글 작성을 위한 YouTube 영상 자막 분석을 수행해주세요.

**분석 목적**:
아래 작성할 블로그 정보에 따라 YouTube 영상들의 자막을 분석하여, 우리가 선택한 제목으로 더 나은 블로그 글을 작성할 수 있도록 도움이 되는 인사이트를 제공해주세요.

**작성할 블로그 정보**:
\`\`\`json
${JSON.stringify(targetInfo, null, 2)}
\`\`\`

**데이터 설명**:
아래는 "${request.keyword}" 키워드로 검색해서 찾은 상위 ${youtubeVideos.length}개 YouTube 영상들의 자막 데이터입니다.
각 영상의 제목, 채널, 조회수, 길이, 자막 내용을 포함합니다.

**분석 대상 영상 자막 스크립트**:
${videosText}

**요청 사항**:
위 YouTube 영상들의 자막을 분석하여 다음 JSON 형식으로 결과를 반환해주세요:

\`\`\`json
{
  "video_summaries": [
    {
      "video_number": 1,
      "key_points": "핵심 포인트 2-3줄 요약"
    },
    {
      "video_number": 2,
      "key_points": "핵심 포인트 2-3줄 요약"
    }
  ],
  "common_themes": [
    "영상들에서 공통적으로 다루는 주제 1",
    "영상들에서 공통적으로 다루는 주제 2"
  ],
  "practical_tips": [
    "블로그 글에 활용할 수 있는 구체적인 정보나 방법 1",
    "블로그 글에 활용할 수 있는 구체적인 정보나 방법 2"
  ],
  "expert_insights": [
    "영상에서 언급된 전문적 관점이나 인사이트 1",
    "영상에서 언급된 전문적 관점이나 인사이트 2"
  ],
  "blog_suggestions": [
    "이 정보들을 블로그 글에 어떻게 활용할지 구체적 제안 1",
    "이 정보들을 블로그 글에 어떻게 활용할지 구체적 제안 2"
  ]
}
\`\`\`

분석 지침:
- **중요**: 타겟 제목 "${request.selectedTitle}"과 관련성이 낮거나 주제가 맞지 않는 영상은 분석에서 제외해주세요
- 관련성이 있는 영상들만 선별하여 분석 수행
- **자막 길이 참고**: 긴 영상의 경우 발췌된 부분만 제공되므로, 전체 흐름을 고려하여 분석해주세요
- 광고나 홍보성 내용은 제외하고 분석
- 블로그 글 작성에 실질적으로 도움되는 정보 위주로 정리
- 구체적이고 실용적인 내용을 우선적으로 포함
- 반드시 위의 JSON 형식으로만 답변해주세요`;
  }
}