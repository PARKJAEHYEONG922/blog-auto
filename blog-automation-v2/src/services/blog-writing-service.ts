import { LLMClientFactory } from './llm-client-factory';
import { getContentTypeDescription, getContentTypeName, getContentTypeGuidelines, getToneDescription, getToneName, getToneGuidelines, getReviewTypeDescription, getReviewTypeName, getReviewTypeGuidelines } from '../constants/content-options';
import { RequiredKeywordInfo, SelectedTitleInfo, ContentTypeInfo, ReviewTypeInfo, ToneInfo } from '../types/common-interfaces';
import { BlogContent } from './blog-crawler';

export interface BlogWritingRequest extends RequiredKeywordInfo, SelectedTitleInfo, ContentTypeInfo, ReviewTypeInfo, ToneInfo {
  bloggerIdentity?: string;
  blogAnalysisResult?: any;
  youtubeAnalysisResult?: any;
  crawledBlogs?: BlogContent[]; // 크롤링된 블로그 데이터 (태그 추출용)
}

export interface BlogWritingResult {
  success: boolean;
  content?: string;
  error?: string;
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
}

export class BlogWritingService {
  /**
   * 크롤링된 블로그들에서 공통 태그 추출
   */
  private static extractCommonTags(crawledBlogs: BlogContent[]): string[] {
    const tagCount = new Map<string, number>();
    
    // 성공한 블로그들의 태그 수집
    crawledBlogs
      .filter(blog => blog.success && blog.tags && blog.tags.length > 0)
      .forEach(blog => {
        blog.tags.forEach(tag => {
          const cleanTag = tag.replace('#', '').trim();
          if (cleanTag) {
            tagCount.set(cleanTag, (tagCount.get(cleanTag) || 0) + 1);
          }
        });
      });
    
    // 빈도순으로 정렬하여 상위 5개 반환
    return Array.from(tagCount.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([tag]) => tag);
  }

  /**
   * 컨텐츠 유형별 상세 지침 반환
   */
  private static getDetailedContentGuidelines(contentType: string): string {
    const guidelines = getContentTypeGuidelines(contentType);
    if (!guidelines) return '';

    return `
- **접근 방식**: ${guidelines.approach}
- **글 구조**: ${guidelines.structure}
- **핵심 키워드**: ${guidelines.keywords.join(', ')}
- **중점 영역**: ${guidelines.focus_areas.join(', ')}`;
  }

  /**
   * 말투별 상세 지침 반환
   */
  private static getDetailedToneGuidelines(tone: string): string {
    const guidelines = getToneGuidelines(tone);
    if (!guidelines) return '';

    return `
- **문체 스타일**: ${guidelines.style}
- **예시 표현**: ${guidelines.examples.join(', ')}
- **글 마무리**: ${guidelines.ending}
- **문장 특징**: ${guidelines.sentence_style}
- **핵심 요소**: ${guidelines.key_features.join(', ')}`;
  }

  /**
   * 후기 유형별 상세 지침 반환
   */
  private static getDetailedReviewGuidelines(reviewType: string): string {
    const guidelines = getReviewTypeGuidelines(reviewType);
    if (!guidelines) return '';

    return `
- **핵심 포인트**:
${guidelines.key_points.map(point => `  • ${point}`).join('\n')}
- **투명성 원칙**: ${guidelines.transparency}`;
  }

  /**
   * 블로그 글쓰기용 프롬프트 생성 (레거시 모델 기반)
   */
  private static generateWritingPrompt(request: BlogWritingRequest): string {
    // 역할 설정
    const roleDescription = request.bloggerIdentity && request.bloggerIdentity.trim()
      ? `당신은 네이버 블로그에서 ${request.bloggerIdentity.trim()} 블로그를 운영하고 있습니다. 독자들이 진짜 도움이 되고 재미있게 읽을 수 있는 글을 쓰는 것이 목표입니다.`
      : "당신은 네이버 블로그에서 인기 있는 글을 쓰는 블로거입니다. 독자들이 진짜 도움이 되고 재미있게 읽을 수 있는 글을 쓰는 것이 목표입니다.";

    // 컨텐츠 유형, 말투, 후기 유형 설명 (Step1에서 정의된 것 사용)
    const contentTypeName = getContentTypeName(request.contentType);
    const contentTypeDescription = getContentTypeDescription(request.contentType);
    const toneName = getToneName(request.tone);
    const toneDescription = getToneDescription(request.tone);
    const reviewTypeName = request.reviewType ? getReviewTypeName(request.reviewType) : '';
    const reviewTypeDescription = request.reviewType ? getReviewTypeDescription(request.reviewType) : '';

    // 블로그 분석 결과 포함
    let blogAnalysisSection = '';
    if (request.blogAnalysisResult) {
      const analysis = request.blogAnalysisResult;
      blogAnalysisSection = `
## 경쟁 블로그 분석 결과
**핵심 키워드**: ${analysis.core_keywords?.join(', ') || '없음'}
**필수 포함 내용**: ${analysis.essential_content?.join(', ') || '없음'}
**차별화 포인트**: ${analysis.improvement_opportunities?.join(', ') || '없음'}
**경쟁사 제목들**: ${analysis.competitor_titles?.join(', ') || '없음'}`;
    }

    // 크롤링된 블로그에서 공통 태그 추출
    let commonTagsSection = '';
    if (request.crawledBlogs && request.crawledBlogs.length > 0) {
      const commonTags = this.extractCommonTags(request.crawledBlogs);
      if (commonTags.length > 0) {
        const formattedTags = commonTags.map(tag => tag.startsWith('#') ? tag : `#${tag}`);
        commonTagsSection = `[상위 블로그 인기 태그 참고: ${formattedTags.join(', ')}]`;
      }
    }

    // YouTube 분석 결과 포함
    let youtubeAnalysisSection = '';
    if (request.youtubeAnalysisResult) {
      const analysis = request.youtubeAnalysisResult;
      youtubeAnalysisSection = `
## YouTube 영상 분석 결과
**공통 주제**: ${analysis.common_themes?.join(', ') || '없음'}
**실용적 팁**: ${analysis.practical_tips?.join(', ') || '없음'}
**전문가 인사이트**: ${analysis.expert_insights?.join(', ') || '없음'}
**블로그 활용 제안**: ${analysis.blog_suggestions?.join(', ') || '없음'}`;
    }

    // 보조 키워드 섹션
    const subKeywordsSection = request.subKeywords && request.subKeywords.length > 0
      ? `\n**보조 키워드**: ${request.subKeywords.join(', ')}`
      : '';

    // 평균 이미지 개수 계산 (크롤링된 블로그에서)
    let avgImageCount = 3; // 기본값
    if (request.crawledBlogs && request.crawledBlogs.length > 0) {
      const successfulBlogs = request.crawledBlogs.filter(blog => blog.success);
      if (successfulBlogs.length > 0) {
        const totalImages = successfulBlogs.reduce((sum, blog) => {
          return sum + (blog.imageCount || 0) + (blog.gifCount || 0);
        }, 0);
        const calculatedAvg = totalImages / successfulBlogs.length;
        avgImageCount = Math.max(3, Math.round(calculatedAvg));
      }
    }

    // 컨텐츠 유형 가이드라인 가져오기
    const contentGuidelines = getContentTypeGuidelines(request.contentType);
    const toneGuidelines = getToneGuidelines(request.tone);
    
    // 보조 키워드 처리
    const subKeywordsText = request.subKeywords && request.subKeywords.length > 0 
      ? request.subKeywords.join(', ')
      : '메인 키워드와 관련된 보조 키워드들을 3-5개 직접 생성하여 활용';

    const prompt = `# AI 역할 설정
${roleDescription}

## 참고할 경쟁 블로그 및 YouTube 요약 정보
'${request.searchKeyword}'로 검색시 노출되는 상위 블로그 글과 YouTube 자막을 추출하여 분석한 결과입니다. 
아래 정보는 참고용이며, 선택된 제목과 내용이 다르더라도 선택된 제목에 맞춰서 알아서 적절한 글을 작성해주세요:

${blogAnalysisSection || '참고할 만한 경쟁사 분석 정보가 없으니, 자연스럽고 유용한 컨텐츠로 작성해주세요.'}

${youtubeAnalysisSection}

# 작성 지침

## 🚨 절대 규칙: 제목 고정 🚨
**❌ 제목 변경 절대 금지 ❌**
**🔒 기본 정보의 제목으로 내용을 작성해주세요 🔒**

## 기본 정보
- **작성할 글 제목**: "${request.selectedTitle}"
- **메인 키워드**: "${request.mainKeyword}"
- **보조 키워드**: "${subKeywordsText}"
- **컨텐츠 유형**: ${contentTypeName} (${contentGuidelines?.approach || contentTypeDescription})

${request.reviewType ? `## 후기 세부 유형
- **후기 유형**: ${reviewTypeName}
- **후기 설명**: ${reviewTypeDescription}
- **투명성 원칙**: ${getReviewTypeGuidelines(request.reviewType)?.transparency || ''}
- **핵심 포인트**: ${getReviewTypeGuidelines(request.reviewType)?.key_points?.join(', ') || ''}` : ''}

## 말투 지침
- **선택된 말투**: ${toneName}
- **말투 스타일**: ${toneGuidelines?.style || toneDescription}
- **예시 표현**: ${toneGuidelines?.examples?.join(', ') || ''}
- **문장 특징**: ${toneGuidelines?.sentence_style || ''}
- **주요 특색**: ${toneGuidelines?.key_features?.join(', ') || ''}
- **마무리 문구**: ${toneGuidelines?.ending || ''}

## 글 구성 방식
- **글 구조**: ${contentGuidelines?.structure || ''}
- **주요 초점**: ${contentGuidelines?.focus_areas?.join(', ') || ''}
- **핵심 표현**: ${contentGuidelines?.keywords?.join(', ') || ''}

## SEO 및 기술적 요구사항
- 글자 수: 1,700-2,000자 (공백 제외)
- 메인 키워드: 5-6회 자연 반복
- 보조 키워드: 각각 3-4회 사용
- 이미지: ${avgImageCount}개 이상 (이미지) 표시로 배치, 필요시 연속 4개 배치 가능
- 동영상: 1개 (동영상) 표시로 배치

## 마크다운 구조 규칙 (자동화 호환성)
- **대제목**: ## 만 사용 (### 사용 금지)
- **소제목**: ### 텍스트 (세부 항목용)
- **강조**: **텍스트** (단계명, 중요 포인트)
- **리스트**: - 항목 (일반 목록)
- **체크리스트**: ✓ 항목 (완료/확인 항목)
- **번호 목록**: 1. 항목 (순서가 중요한 경우)

## 글쓰기 품질 요구사항
- **제목 중심 작성**: 참고 자료와 선택된 제목이 다르더라도 반드시 선택된 제목에 맞는 내용으로 작성
- **참고 자료 활용**: 위 분석 결과는 참고용이므로, 제목과 관련된 부분만 선별적으로 활용
- **자연스러운 문체**: AI 생성티 없는 개성 있고 자연스러운 어투로 작성
- **완전한 내용**: XX공원, OO병원 같은 placeholder 사용 금지. 구체적인 정보가 없다면 "근처 공원", "동네 병원" 등 일반적 표현 사용

# 출력 형식

중요: 제목은 절대 바꾸지 마세요!
다른 설명 없이 아래 형식으로만 출력하세요:

\`\`\`
제목: ${request.selectedTitle}

[서론 - 3초의 법칙으로 핵심 답변 즉시 제시]

[본문은 다양한 형식으로 구성하세요]
- 소제목 + 본문
- 체크리스트 (✓ 항목들)
- 비교표 (| 항목 | 특징 | 가격 |)
- TOP5 순위 (1위: 제품명 - 특징)
- 단계별 가이드 (1단계, 2단계...)
- Q&A 형식 등을 적절히 조합

[결론 - 요약 및 독자 행동 유도]

${commonTagsSection}
[${commonTagsSection.trim() ? '위 참고 태그와 작성한 글 내용을 토대로' : '작성한 글 내용을 토대로'} 적합한 태그 5개 이상을 # 형태로 작성]
\`\`\`
`;

    return prompt.trim();
  }


  /**
   * 블로그 글쓰기 실행
   */
  static async generateBlogContent(request: BlogWritingRequest): Promise<BlogWritingResult> {
    try {
      console.log('🎯 블로그 글쓰기 시작:', request.selectedTitle);

      // 글쓰기 AI 클라이언트 확인
      if (!LLMClientFactory.hasWritingClient()) {
        throw new Error('글쓰기 AI가 설정되지 않았습니다. 설정에서 글쓰기 AI를 먼저 설정해주세요.');
      }

      const writingClient = LLMClientFactory.getWritingClient();

      // 프롬프트 생성
      const prompt = this.generateWritingPrompt(request);
      console.log('📝 글쓰기 프롬프트 생성 완료');

      // AI에게 글쓰기 요청
      const response = await writingClient.generateText([
        {
          role: 'user',
          content: prompt
        }
      ]);

      if (!response.content || response.content.trim().length === 0) {
        throw new Error('AI가 빈 응답을 반환했습니다.');
      }

      console.log('✅ 블로그 글쓰기 완료');
      console.log('📊 토큰 사용량:', response.usage);

      return {
        success: true,
        content: response.content.trim(),
        usage: response.usage
      };

    } catch (error) {
      console.error('❌ 블로그 글쓰기 실패:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.'
      };
    }
  }

  /**
   * 글쓰기 결과 후처리 (필요시)
   */
  static processWritingResult(content: string): string {
    // 제목 중복 제거 및 포맷팅 정리
    let processed = content.trim();

    // 코드 블록 제거 (```로 감싸진 부분)
    processed = processed.replace(/^```\n?/, '').replace(/\n?```$/, '');

    // 불필요한 앞뒤 공백 정리
    processed = processed.trim();

    return processed;
  }

  /**
   * 글쓰기 AI 설정 확인
   */
  static isWritingClientAvailable(): boolean {
    return LLMClientFactory.hasWritingClient();
  }

  /**
   * 현재 설정된 글쓰기 AI 정보 반환
   */
  static getWritingClientInfo(): string {
    const modelStatus = LLMClientFactory.getCachedModelStatus();
    return modelStatus.writing || '미설정';
  }
}