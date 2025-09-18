import { LLMClientFactory, LLMMessage } from './llm-client-factory';
import { naverAPI } from './naver-api';
import { BlogTitleSelector, SelectedBlogTitle, SelectedYouTubeVideo } from './blog-title-selector';
import { BlogCrawler, BlogContent, CrawlingProgress } from './blog-crawler';
import { BlogSummaryPrompts, SummaryPromptRequest } from './blog-summary-prompts';
import { youtubeAPI, PrioritizedVideo } from './youtube-api';

export interface DataCollectionRequest {
  keyword: string; // 서치키워드
  mainKeyword?: string; // 메인키워드
  subKeywords?: string[];
  selectedTitle: string;
  platform: string;
  contentType: string;
  contentTypeDescription?: string;
  reviewType?: string;
  reviewTypeDescription?: string;
  mode: 'fast' | 'accurate';
}

export interface CollectedBlogData {
  rank: number; // 블로그 순위 (1-10)
  title: string; // 블로그 제목
  url: string; // 블로그 URL
  platform: string; // 플랫폼 (네이버)
}


export interface CollectedYouTubeData {
  title: string;
  channelName: string;
  channelId?: string;
  viewCount: number;
  likeCount?: string;
  commentCount?: string;
  publishedAt: string;
  duration: number; // seconds
  subscriberCount?: number;
  thumbnail?: string;
  url: string;
  description?: string;
  tags?: string[];
  categoryId?: string;
  definition?: string; // hd/sd
  caption?: boolean; // 자막 여부
  priority: number; // 우선순위 점수
  summary?: string; // 자막 요약
}

export interface KeywordAnalysis {
  mainKeyword: string;
  relatedKeywords: string[];
  searchVolume?: number;
  competition?: string;
  suggestions: string[];
}

export interface SEOInsights {
  titleLength: string;
  keywordDensity: string;
  contentLength: string;
  headingStructure: string;
  imageRecommendations: string;
}

export interface DataCollectionResult {
  keywords: KeywordAnalysis;
  blogs: CollectedBlogData[]; // 전체 50개 블로그
  selectedBlogs: SelectedBlogTitle[]; // AI가 선별한 상위 10개
  crawledBlogs: BlogContent[]; // 크롤링된 블로그 본문 데이터
  contentSummary?: string; // 블로그 콘텐츠 요약 분석 결과
  youtube: CollectedYouTubeData[];
  seoInsights: SEOInsights;
  summary: {
    totalSources: number;
    dataQuality: 'high' | 'medium' | 'low';
    processingTime: number;
    recommendations: string[];
  };
}

export interface AnalysisProgress {
  step: string;
  progress: number;
  status: 'pending' | 'running' | 'completed' | 'error';
  data?: any;
  message?: string;
}

export class DataCollectionEngine {
  private progressCallback?: (progress: AnalysisProgress[]) => void;
  private analysisSteps: AnalysisProgress[] = [
    { step: '키워드 분석 및 확장', progress: 0, status: 'pending' },
    { step: '네이버 블로그 데이터 수집 (서치키워드 우선, 최대 50개)', progress: 0, status: 'pending' },
    { step: '유튜브 데이터 수집 및 선별', progress: 0, status: 'pending' },
    { step: 'AI 블로그+YouTube 통합 선별 (상위 10개씩)', progress: 0, status: 'pending' },
    { step: '선별된 YouTube 영상 자막 추출 및 요약', progress: 0, status: 'pending' },
    { step: '선별된 블로그 본문 크롤링 (상위 3개)', progress: 0, status: 'pending' },
    { step: '블로그 콘텐츠 요약 분석', progress: 0, status: 'pending' },
    { step: 'SEO 최적화 가이드 생성', progress: 0, status: 'pending' },
    { step: '데이터 요약 및 인사이트 도출', progress: 0, status: 'pending' }
  ];

  constructor(progressCallback?: (progress: AnalysisProgress[]) => void) {
    this.progressCallback = progressCallback;
  }

  async collectAndAnalyze(request: DataCollectionRequest): Promise<DataCollectionResult> {
    const startTime = Date.now();
    console.log('🔍 데이터 수집 및 분석 시작:', request);

    try {
      // 1. 키워드 분석 및 확장
      const keywords = await this.analyzeKeywords(request.keyword, request.subKeywords);
      this.updateProgress(0, 'completed', keywords);

      // 2. 네이버 블로그 데이터 수집 (50개)
      const blogs = await this.collectBlogData(request.keyword, request.mainKeyword || request.keyword);
      this.updateProgress(1, 'completed', blogs);

      // 3. 유튜브 데이터 수집 (100개→30개 상대평가 선별)
      const youtube = await this.collectYouTubeData(request.keyword);
      this.updateProgress(2, 'completed', youtube);

      // 4. AI 블로그+YouTube 통합 선별 (상위 10개씩)
      const selectedBlogs = await this.selectTopBlogs(request, blogs, youtube);
      this.updateProgress(3, 'completed', selectedBlogs);

      // 5. 선별된 YouTube 영상 자막 추출 및 요약
      const enrichedYouTube = await this.extractYouTubeSubtitles(selectedBlogs.selectedVideos);
      this.updateProgress(4, 'completed', enrichedYouTube);

      // 6. 선별된 블로그 본문 크롤링
      const crawledBlogs = await this.crawlSelectedBlogs(selectedBlogs.selectedTitles);
      this.updateProgress(5, 'completed', crawledBlogs);

      // 7. 블로그 콘텐츠 요약 분석
      const contentSummary = await this.generateContentSummary(request, crawledBlogs);
      this.updateProgress(6, 'completed', contentSummary);


      // 8. SEO 최적화 가이드 생성
      const seoInsights = await this.generateSEOInsights(request, selectedBlogs.selectedTitles);
      this.updateProgress(7, 'completed', seoInsights);

      // 9. 데이터 요약 및 인사이트 도출
      const summary = await this.generateSummaryInsights(keywords, blogs, enrichedYouTube);
      this.updateProgress(8, 'completed', summary);

      const processingTime = Date.now() - startTime;

      const result: DataCollectionResult = {
        keywords,
        blogs, // 전체 50개 블로그
        selectedBlogs: selectedBlogs.selectedTitles, // AI가 선별한 상위 10개 블로그
        crawledBlogs, // 크롤링된 블로그 본문 데이터
        contentSummary, // 블로그 콘텐츠 요약 분석 결과
        youtube: enrichedYouTube, // AI가 선별한 상위 10개 YouTube (자막 추출 완료)
        seoInsights,
        summary: {
          ...summary,
          processingTime
        }
      };

      console.log('✅ 데이터 수집 및 분석 완료:', result);
      return result;

    } catch (error) {
      console.error('❌ 데이터 수집 중 오류:', error);
      
      // 현재 진행 중인 단계를 오류로 표시
      const currentStepIndex = this.analysisSteps.findIndex(step => step.status === 'running');
      if (currentStepIndex !== -1) {
        this.updateProgress(currentStepIndex, 'error', null, error.message);
      }
      
      throw error;
    }
  }

  private updateProgress(stepIndex: number, status: 'pending' | 'running' | 'completed' | 'error', data?: any, message?: string) {
    this.analysisSteps[stepIndex].status = status;
    this.analysisSteps[stepIndex].progress = status === 'completed' ? 100 : status === 'running' ? 50 : 0;
    
    if (data) {
      this.analysisSteps[stepIndex].data = data;
    }
    
    if (message) {
      this.analysisSteps[stepIndex].message = message;
    }

    // 다음 단계를 running으로 표시 (완료된 경우)
    if (status === 'completed' && stepIndex < this.analysisSteps.length - 1) {
      this.analysisSteps[stepIndex + 1].status = 'running';
    }

    // 콜백 호출
    if (this.progressCallback) {
      this.progressCallback([...this.analysisSteps]);
    }
  }

  private async analyzeKeywords(mainKeyword: string, subKeywords?: string[]): Promise<KeywordAnalysis> {
    this.updateProgress(0, 'running');
    
    try {
      // AI를 활용한 키워드 분석
      const informationClient = LLMClientFactory.getInformationClient();
      
      const systemPrompt = `당신은 SEO 키워드 분석 전문가입니다. 주어진 키워드를 분석하고 관련 키워드를 추천해주세요.`;
      
      const userPrompt = `메인 키워드: "${mainKeyword}"
${subKeywords && subKeywords.length > 0 ? `서브 키워드: ${subKeywords.join(', ')}` : ''}

다음 형식으로 키워드 분석 결과를 JSON으로 반환해주세요:
{
  "relatedKeywords": ["관련키워드1", "관련키워드2", "관련키워드3", "관련키워드4", "관련키워드5"],
  "suggestions": ["추천키워드1", "추천키워드2", "추천키워드3"]
}

관련 키워드는 검색량이 높고 경쟁도가 적당한 롱테일 키워드 위주로 선정해주세요.`;

      const messages: LLMMessage[] = [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userPrompt }
      ];

      const response = await informationClient.generateText(messages);
      
      try {
        const jsonMatch = response.content.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
          const analysisResult = JSON.parse(jsonMatch[0]);
          
          return {
            mainKeyword,
            relatedKeywords: analysisResult.relatedKeywords || [],
            suggestions: analysisResult.suggestions || [],
            competition: 'medium' // 기본값
          };
        }
      } catch (parseError) {
        console.warn('키워드 분석 JSON 파싱 실패:', parseError);
      }

      // 폴백: 기본 키워드 확장
      return {
        mainKeyword,
        relatedKeywords: subKeywords || [
          `${mainKeyword} 방법`,
          `${mainKeyword} 팁`,
          `${mainKeyword} 가이드`,
          `${mainKeyword} 추천`,
          `${mainKeyword} 후기`
        ],
        suggestions: [
          `${mainKeyword} 초보자`,
          `${mainKeyword} 완벽`,
          `${mainKeyword} 전문가`
        ],
        competition: 'medium'
      };

    } catch (error) {
      console.error('키워드 분석 실패:', error);
      throw new Error(`키워드 분석 실패: ${error.message}`);
    }
  }

  private async collectBlogData(searchKeyword: string, mainKeyword: string): Promise<CollectedBlogData[]> {
    this.updateProgress(1, 'running');
    
    try {
      const searchResults = [];
      let currentRank = 1;
      const targetTotal = 50; // 목표 50개
      
      // 1. 서치키워드로 50개 시도
      console.log(`🔍 서치키워드로 최대 50개 검색: ${searchKeyword}`);
      const searchKeywordResults = await this.searchNaverBlogsWithRank(searchKeyword, 50, currentRank);
      searchResults.push(...searchKeywordResults);
      currentRank += searchKeywordResults.length;
      
      console.log(`📊 서치키워드 검색 결과: ${searchKeywordResults.length}개`);
      
      // 2. 50개 미만이면 메인키워드로 추가 수집 (서치키워드와 다른 경우만)
      if (searchResults.length < targetTotal && mainKeyword && mainKeyword !== searchKeyword) {
        const remaining = targetTotal - searchResults.length;
        console.log(`🎯 메인키워드로 ${remaining}개 추가 검색: ${mainKeyword}`);
        
        const mainKeywordResults = await this.searchNaverBlogsWithRank(mainKeyword, remaining, currentRank);
        searchResults.push(...mainKeywordResults);
        
        console.log(`📊 메인키워드 검색 결과: ${mainKeywordResults.length}개 추가`);
      } else if (searchResults.length >= targetTotal) {
        console.log(`✅ 서치키워드로 충분한 결과 확보 (${searchResults.length}개)`);
      } else {
        console.log(`⚠️ 메인키워드와 서치키워드가 동일하여 추가 검색 생략`);
      }
      
      console.log(`✅ 총 ${searchResults.length}개 블로그 데이터 수집 완료`);
      return searchResults;
      
    } catch (error) {
      console.error('블로그 데이터 수집 실패:', error);
      // 실패해도 빈 배열 반환하여 다음 단계 진행
      return [];
    }
  }

  // 순위를 유지하면서 지정된 개수만큼 블로그 검색
  private async searchNaverBlogsWithRank(query: string, count: number, startRank: number): Promise<CollectedBlogData[]> {
    try {
      console.log(`🔍 네이버 블로그 검색 (${count}개): ${query}`);
      
      const blogItems = await naverAPI.searchBlogs(query, count);
      
      return blogItems.map((item, index) => ({
        rank: startRank + index, // 연속된 순위
        title: naverAPI.cleanHtmlTags(item.title),
        url: item.link,
        platform: 'naver'
      }));
      
    } catch (error) {
      console.error(`네이버 블로그 검색 실패 (${query}):`, error);
      
      // API 실패 시 빈 배열 반환
      return [];
    }
  }

  private async crawlSelectedBlogs(selectedBlogs: SelectedBlogTitle[]): Promise<BlogContent[]> {
    this.updateProgress(3, 'running');
    
    try {
      if (!selectedBlogs || selectedBlogs.length === 0) {
        console.log('선별된 블로그가 없어 크롤링을 건너뜁니다');
        return [];
      }

      console.log(`📝 선별된 ${selectedBlogs.length}개 블로그 크롤링 시작`);
      
      // 크롤링 진행률 콜백 설정
      const crawler = new BlogCrawler((crawlingProgress: CrawlingProgress) => {
        // 크롤링 진행률을 메인 진행률에 반영
        const overallProgress = Math.round((crawlingProgress.current / crawlingProgress.total) * 100);
        this.analysisSteps[3].progress = overallProgress;
        
        // 상세 메시지 업데이트
        this.analysisSteps[3].message = `${crawlingProgress.current}/${crawlingProgress.total}: ${crawlingProgress.url}`;
        
        // 콜백 호출
        if (this.progressCallback) {
          this.progressCallback([...this.analysisSteps]);
        }
      });

      const crawledBlogs = await crawler.crawlSelectedBlogs(selectedBlogs, 3); // 상위 3개만 크롤링
      
      const successCount = crawledBlogs.filter(blog => blog.success).length;
      console.log(`✅ 블로그 크롤링 완료: ${successCount}/${selectedBlogs.length} 성공`);
      
      return crawledBlogs;
      
    } catch (error) {
      console.error('블로그 크롤링 실패:', error);
      return [];
    }
  }

  private async generateContentSummary(request: DataCollectionRequest, crawledBlogs: BlogContent[]): Promise<string> {
    this.updateProgress(4, 'running');
    
    try {
      if (!crawledBlogs || crawledBlogs.length === 0) {
        console.log('크롤링된 블로그가 없어 콘텐츠 요약을 건너뜁니다');
        return '';
      }

      console.log(`📝 ${crawledBlogs.length}개 블로그 콘텐츠 요약 분석 시작`);
      
      // BlogSummaryPrompts 요청 구성
      const summaryRequest: SummaryPromptRequest = {
        selectedTitle: request.selectedTitle,
        searchKeyword: request.keyword,
        mainKeyword: request.mainKeyword || request.keyword,
        contentType: request.contentType,
        contentTypeDescription: request.contentTypeDescription,
        reviewType: request.reviewType,
        reviewTypeDescription: request.reviewTypeDescription,
        competitorBlogs: crawledBlogs,
        subKeywords: request.subKeywords
      };

      // 정보요약 AI용 프롬프트 생성
      const prompt = BlogSummaryPrompts.generateContentSummaryPrompt(summaryRequest);
      
      // LLM 호출
      const informationClient = LLMClientFactory.getInformationClient();
      const messages: LLMMessage[] = [
        { role: 'user', content: prompt }
      ];

      console.log('🤖 [LLM 요청] 블로그 콘텐츠 요약 분석 요청');
      
      const response = await informationClient.generateText(messages);
      
      console.log('🤖 [LLM 응답] 콘텐츠 요약 분석 결과 받음');
      
      return response.content;
      
    } catch (error) {
      console.error('블로그 콘텐츠 요약 분석 실패:', error);
      return '콘텐츠 요약 분석 실패';
    }
  }



  private async selectTopBlogs(
    request: DataCollectionRequest, 
    blogs: CollectedBlogData[], 
    youtube: CollectedYouTubeData[]
  ): Promise<{ selectedTitles: SelectedBlogTitle[], selectedVideos: SelectedYouTubeVideo[] }> {
    this.updateProgress(2, 'running');
    
    try {
      if (!blogs || blogs.length === 0) {
        console.log('수집된 블로그가 없어 선별을 건너뜁니다');
        return { selectedTitles: [], selectedVideos: [] };
      }

      const hasYouTube = youtube && youtube.length > 0;
      if (hasYouTube) {
        console.log(`🤖 수집된 블로그 ${blogs.length}개 + YouTube ${youtube.length}개 통합 선별 시작`);
      } else {
        console.log(`🤖 수집된 ${blogs.length}개 블로그 중 상위 10개 선별 시작`);
      }
      
      const selector = new BlogTitleSelector();
      
      const selectionRequest = {
        targetTitle: request.selectedTitle,
        mainKeyword: request.mainKeyword || request.keyword,
        subKeywords: request.subKeywords,
        searchKeyword: request.keyword,
        contentType: request.contentType,
        contentTypeDescription: request.contentTypeDescription,
        reviewType: request.reviewType,
        reviewTypeDescription: request.reviewTypeDescription,
        blogTitles: blogs,
        youtubeTitles: hasYouTube ? youtube : undefined
      };
      
      const result = await selector.selectTopBlogs(selectionRequest);
      return {
        selectedTitles: result.selectedTitles,
        selectedVideos: result.selectedVideos
      };
      
    } catch (error) {
      console.error('블로그 제목 선별 실패:', error);
      
      // 실패 시 상위 10개씩 반환
      const fallbackBlogs = blogs.slice(0, 10).map((blog) => ({
        title: blog.title,
        url: blog.url,
        relevanceReason: '자동 선별 (AI 분석 실패)'
      }));
      
      const fallbackVideos = youtube && youtube.length > 0 
        ? youtube.slice(0, 10).map((video) => ({
            title: video.title,
            url: video.url,
            channelName: video.channelName,
            viewCount: video.viewCount,
            duration: video.duration,
            priority: video.priority,
            relevanceReason: '자동 선별 (AI 분석 실패)'
          }))
        : [];

      return { 
        selectedTitles: fallbackBlogs,
        selectedVideos: fallbackVideos
      };
    }
  }

  private async generateSEOInsights(request: DataCollectionRequest, selectedBlogs: SelectedBlogTitle[]): Promise<SEOInsights> {
    this.updateProgress(7, 'running');
    
    try {
      const informationClient = LLMClientFactory.getInformationClient();
      
      const systemPrompt = `당신은 SEO 최적화 전문가입니다. 주어진 데이터를 분석하여 SEO 최적화 가이드를 제공해주세요.`;
      
      const competitorTitles = selectedBlogs.slice(0, 5).map(blog => blog.title).join('\n- ');
      
      const userPrompt = `키워드: "${request.keyword}"
선택된 제목: "${request.selectedTitle}"
콘텐츠 타입: ${request.contentType}

상위 경쟁사 제목들:
- ${competitorTitles}

다음 형식으로 SEO 최적화 가이드를 JSON으로 반환해주세요:
{
  "titleLength": "권장 제목 길이",
  "keywordDensity": "권장 키워드 밀도",
  "contentLength": "권장 글자 수",
  "headingStructure": "권장 제목 구조",
  "imageRecommendations": "이미지 사용 권장사항"
}`;

      const messages: LLMMessage[] = [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userPrompt }
      ];

      const response = await informationClient.generateText(messages);
      
      try {
        const jsonMatch = response.content.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
          const insights = JSON.parse(jsonMatch[0]);
          
          // headingStructure가 객체인 경우 문자열로 변환
          if (typeof insights.headingStructure === 'object' && insights.headingStructure !== null) {
            insights.headingStructure = JSON.stringify(insights.headingStructure);
          }
          
          return insights;
        }
      } catch (parseError) {
        console.warn('SEO 인사이트 JSON 파싱 실패:', parseError);
      }

      // 폴백: 기본 SEO 가이드
      return {
        titleLength: '30-60자',
        keywordDensity: '1-3%',
        contentLength: '1500-3000자',
        headingStructure: 'H1(1개), H2(3-5개), H3(섹션별 2-3개)',
        imageRecommendations: '8-12개, 제목과 연관된 고품질 이미지 사용'
      };

    } catch (error) {
      console.error('SEO 인사이트 생성 실패:', error);
      return {
        titleLength: '30-60자',
        keywordDensity: '1-3%',
        contentLength: '1500-3000자',
        headingStructure: 'H1(1개), H2(3-5개), H3(섹션별 2-3개)',
        imageRecommendations: '8-12개, 제목과 연관된 고품질 이미지 사용'
      };
    }
  }

  private async generateSummaryInsights(
    keywords: KeywordAnalysis,
    blogs: CollectedBlogData[],
    youtube: CollectedYouTubeData[]
  ): Promise<{ totalSources: number; dataQuality: 'high' | 'medium' | 'low'; recommendations: string[] }> {
    this.updateProgress(8, 'running');
    
    const totalSources = blogs.length + youtube.length;
    
    let dataQuality: 'high' | 'medium' | 'low' = 'high';
    if (totalSources < 5) dataQuality = 'low';
    else if (totalSources < 10) dataQuality = 'medium';
    
    const recommendations = [
      `총 ${totalSources}개의 데이터 소스에서 정보를 수집했습니다.`,
      `주요 키워드 "${keywords.mainKeyword}"를 중심으로 콘텐츠를 구성하세요.`,
      `관련 키워드 ${keywords.relatedKeywords.length}개를 자연스럽게 활용하세요.`,
      `경쟁사 분석 결과를 참고하여 차별화된 관점을 제시하세요.`
    ];

    if (blogs.length > 0) {
      recommendations.push(`블로그 ${blogs.length}개 분석 완료: 트렌드와 관점을 참고하세요.`);
    }
    
    
    if (youtube.length > 0) {
      recommendations.push(`유튜브 ${youtube.length}개 영상 분석: 시각적 요소를 강화하세요.`);
    }

    return {
      totalSources,
      dataQuality,
      recommendations
    };
  }



  private async collectYouTubeData(keyword: string): Promise<CollectedYouTubeData[]> {
    this.updateProgress(2, 'running');
    
    try {
      console.log(`📺 YouTube 데이터 수집 시작: ${keyword}`);
      
      // 1. YouTube API 설정 로드
      await youtubeAPI.loadConfig();
      
      // 2. 50개 동영상 검색 및 스마트 선별
      console.log('📺 50개 동영상 검색 및 우선순위 분석 중...');
      const prioritizedVideos = await youtubeAPI.searchPrioritizedVideos(keyword, 50);
      
      if (prioritizedVideos.length === 0) {
        console.warn('YouTube 검색 결과가 없습니다');
        return [];
      }
      
      // 3. 상대평가 로직: 15개 이상이면 70% 선별, 10-14개면 10개로 선별, 10개 미만이면 모두 사용
      let selectedVideos: PrioritizedVideo[];
      if (prioritizedVideos.length >= 15) {
        const targetCount = Math.floor(prioritizedVideos.length * 0.7);
        selectedVideos = prioritizedVideos
          .sort((a, b) => b.priority - a.priority)
          .slice(0, targetCount);
        console.log(`📺 상대평가 완료: ${prioritizedVideos.length}개 중 상위 70%(${selectedVideos.length}개) 선별`);
      } else if (prioritizedVideos.length >= 10) {
        selectedVideos = prioritizedVideos
          .sort((a, b) => b.priority - a.priority)
          .slice(0, 10);
        console.log(`📺 상대평가로 10개 선별: ${prioritizedVideos.length}개 중 상위 10개 AI에게 전달`);
      } else {
        selectedVideos = prioritizedVideos.sort((a, b) => b.priority - a.priority);
        console.log(`📺 소량 데이터로 상대평가 생략: ${selectedVideos.length}개 모두 AI에게 전달`);
      }
      
      // 4. CollectedYouTubeData 형식으로 변환
      const youtubeData: CollectedYouTubeData[] = selectedVideos.map((video: PrioritizedVideo) => ({
        title: video.title,
        channelName: video.channelTitle,
        viewCount: video.viewCount,
        duration: video.duration,
        subscriberCount: video.subscriberCount,
        publishedAt: video.publishedAt,
        url: video.url,
        priority: video.priority,
        // 나중에 AI 선별 후 자막 추출할 예정이므로 일단 기본값
        likeCount: undefined as string | undefined,
        commentCount: undefined as string | undefined,
        thumbnail: undefined as string | undefined,
        description: undefined as string | undefined,
        tags: undefined as string[] | undefined,
        categoryId: undefined as string | undefined,
        definition: undefined as string | undefined,
        caption: undefined as boolean | undefined,
        summary: undefined as string | undefined
      }));
      
      console.log(`✅ YouTube 데이터 ${youtubeData.length}개 수집 완료`);
      
      return youtubeData;
      
    } catch (error) {
      console.error('❌ YouTube 데이터 수집 실패:', error);
      
      // YouTube API 설정이 없거나 실패 시 빈 배열 반환
      return [];
    }
  }

  private async extractYouTubeSubtitles(selectedVideos: SelectedYouTubeVideo[]): Promise<CollectedYouTubeData[]> {
    this.updateProgress(4, 'running');
    
    try {
      if (!selectedVideos || selectedVideos.length === 0) {
        console.log('선별된 YouTube 영상이 없어 자막 추출을 건너뜁니다');
        return [];
      }

      console.log(`📝 선별된 YouTube ${selectedVideos.length}개 영상의 자막 추출 시작`);
      
      const enrichedVideos: CollectedYouTubeData[] = [];
      
      // 각 영상의 자막 추출
      for (let i = 0; i < selectedVideos.length; i++) {
        const video = selectedVideos[i];
        
        console.log(`📝 [${i + 1}/${selectedVideos.length}] "${video.title}" 자막 추출 중...`);
        
        try {
          // YouTube URL에서 videoId 추출
          const videoId = this.extractVideoIdFromUrl(video.url);
          if (!videoId) {
            console.warn(`⚠️ YouTube URL에서 videoId 추출 실패: ${video.url}`);
            continue;
          }
          
          // 자막 추출
          const subtitles = await youtubeAPI.extractSubtitlesSimple(videoId);
          
          // 자막이 있으면 AI로 요약 생성
          let summary = '';
          if (subtitles.length > 0 && subtitles[0].text) {
            summary = await this.generateVideoSummary(video.title, subtitles[0].text);
          }
          
          // CollectedYouTubeData 형태로 변환
          const enrichedVideo: CollectedYouTubeData = {
            title: video.title,
            channelName: video.channelName,
            viewCount: video.viewCount,
            duration: video.duration,
            subscriberCount: undefined, // SelectedYouTubeVideo에는 없음
            publishedAt: new Date().toISOString(), // 임시값
            url: video.url,
            priority: video.priority,
            summary: summary || (subtitles.length > 0 ? '자막 추출 완료 (요약 생성 실패)' : '자막 없음'),
            likeCount: undefined,
            commentCount: undefined,
            thumbnail: undefined,
            description: undefined,
            tags: undefined,
            categoryId: undefined,
            definition: undefined,
            caption: subtitles.length > 0
          };
          
          enrichedVideos.push(enrichedVideo);
          
          console.log(`✅ [${i + 1}] "${video.title}" 자막 추출 완료 (자막: ${subtitles.length > 0 ? 'O' : 'X'}, 요약: ${summary ? 'O' : 'X'})`);
          
        } catch (error) {
          console.warn(`⚠️ [${i + 1}] "${video.title}" 자막 추출 실패:`, error);
          
          // 자막 추출 실패해도 기본 정보는 포함
          const basicVideo: CollectedYouTubeData = {
            title: video.title,
            channelName: video.channelName,
            viewCount: video.viewCount,
            duration: video.duration,
            publishedAt: new Date().toISOString(),
            url: video.url,
            priority: video.priority,
            summary: '자막 추출 실패',
            caption: false
          };
          
          enrichedVideos.push(basicVideo);
        }
      }
      
      console.log(`✅ YouTube 자막 추출 완료: ${enrichedVideos.length}개 영상 처리`);
      
      return enrichedVideos;
      
    } catch (error) {
      console.error('❌ YouTube 자막 추출 실패:', error);
      
      // 실패 시 기본 형태로 변환해서 반환
      return selectedVideos.map(video => ({
        title: video.title,
        channelName: video.channelName,
        viewCount: video.viewCount,
        duration: video.duration,
        publishedAt: new Date().toISOString(),
        url: video.url,
        priority: video.priority,
        summary: '자막 추출 시스템 오류',
        caption: false
      }));
    }
  }

  private extractVideoIdFromUrl(url: string): string | null {
    try {
      // YouTube URL 형태: https://www.youtube.com/watch?v=VIDEO_ID
      const urlObj = new URL(url);
      if (urlObj.hostname === 'www.youtube.com' && urlObj.pathname === '/watch') {
        return urlObj.searchParams.get('v');
      }
      // 다른 YouTube URL 형태도 지원 가능
      return null;
    } catch (error) {
      console.warn('YouTube URL 파싱 실패:', url);
      return null;
    }
  }

  private async generateVideoSummary(title: string, subtitleText: string): Promise<string> {
    try {
      if (!subtitleText || subtitleText.trim().length < 100) {
        return '자막이 너무 짧아 요약 불가';
      }

      const informationClient = LLMClientFactory.getInformationClient();
      
      // 자막이 너무 길면 앞부분만 사용 (토큰 제한)
      const maxSubtitleLength = 3000;
      const truncatedText = subtitleText.length > maxSubtitleLength 
        ? subtitleText.substring(0, maxSubtitleLength) + '...'
        : subtitleText;

      const userPrompt = `다음 YouTube 영상의 자막을 분석하여 블로그 작성에 도움될 만한 핵심 내용을 150자 이내로 요약해주세요.

영상 제목: "${title}"

자막 내용:
${truncatedText}

요약 요구사항:
- 블로그 글 작성에 활용할 수 있는 핵심 정보와 인사이트 위주로 정리
- 광고나 불필요한 내용은 제외
- 150자 이내로 간결하게 작성
- 이모지나 특수문자 사용 금지`;

      const messages: LLMMessage[] = [
        { role: 'user', content: userPrompt }
      ];

      const response = await informationClient.generateText(messages);
      
      // 응답에서 150자까지만 추출
      const summary = response.content.trim().substring(0, 150);
      
      return summary || '요약 생성 실패';
      
    } catch (error) {
      console.warn('영상 요약 생성 실패:', error);
      return '요약 생성 중 오류 발생';
    }
  }

}