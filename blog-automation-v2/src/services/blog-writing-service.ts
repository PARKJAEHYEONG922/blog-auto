import { LLMClientFactory } from './llm-client-factory';
import { getContentTypeDescription, getContentTypeName, getContentTypeGuidelines, getToneDescription, getToneName, getToneGuidelines, getReviewTypeDescription, getReviewTypeName, getReviewTypeGuidelines } from '../constants/content-options';
import { RequiredKeywordInfo, SelectedTitleInfo, ContentTypeInfo, ReviewTypeInfo, ToneInfo } from '../types/common-interfaces';

export interface BlogWritingRequest extends RequiredKeywordInfo, SelectedTitleInfo, ContentTypeInfo, ReviewTypeInfo, ToneInfo {
  bloggerIdentity?: string;
  blogAnalysisResult?: any;
  youtubeAnalysisResult?: any;
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

    const prompt = `# AI 역할 설정
${roleDescription}

## 작성할 글 정보
- **제목**: ${request.selectedTitle}
- **검색 키워드**: ${request.searchKeyword}
- **메인 키워드**: ${request.mainKeyword}${subKeywordsSection}
- **컨텐츠 유형**: ${contentTypeName} (${request.contentType})
- **말투**: ${toneName} (${request.tone})

${blogAnalysisSection}

${youtubeAnalysisSection}

## 컨텐츠 유형별 세부 지침
- **유형**: ${contentTypeName} (${request.contentType})
- **설명**: ${contentTypeDescription}
${this.getDetailedContentGuidelines(request.contentType)}

## 말투별 세부 지침  
- **말투**: ${toneName} (${request.tone})
- **스타일**: ${toneDescription}
${this.getDetailedToneGuidelines(request.tone)}

${request.reviewType ? `## 후기 유형별 세부 지침
- **후기 유형**: ${reviewTypeName} (${request.reviewType})
- **설명**: ${reviewTypeDescription}
${this.getDetailedReviewGuidelines(request.reviewType)}` : ''}

## 글쓰기 원칙
1. **3초의 법칙**: 서론에서 독자가 찾는 핵심 답변을 즉시 제시
2. **실용성 우선**: 구체적이고 실행 가능한 정보 제공
3. **가독성**: 소제목, 리스트, 표 등을 활용한 구조화
4. **SEO 최적화**: 메인 키워드와 보조 키워드 자연스럽게 포함
5. **독자 몰입**: 독자의 관심사와 니즈에 맞는 내용 구성

## 글 구성 방식
1. **서론**: 핵심 답변 즉시 제시 (3초의 법칙)
2. **본문**: 다양한 형식 조합
   - 소제목 + 본문
   - 체크리스트 (✓ 항목들)
   - 비교표 (| 항목 | 특징 | 가격 |)
   - TOP5 순위 (1위: 제품명 - 특징)
   - 단계별 가이드 (1단계, 2단계...)
   - Q&A 형식
3. **결론**: 요약 및 독자 행동 유도

## 주의사항
- 제목은 절대 변경하지 말 것
- 경쟁사 분석과 YouTube 분석 결과를 적극 활용
- 구체적인 정보와 실례 포함
- 독자가 바로 활용할 수 있는 실용적 내용 제공
- 자연스러운 키워드 배치로 SEO 최적화

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

[관련 태그 5개 이상을 # 형태로 작성]
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