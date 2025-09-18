import { LLMClientFactory, LLMMessage } from './llm-client-factory';
import { naverAPI } from './naver-api';
import { BlogTitleSelector, SelectedBlogTitle, SelectedYouTubeVideo } from './blog-title-selector';
import { BlogCrawler, BlogContent, CrawlingProgress } from './blog-crawler';
import { AnalysisPrompts, SummaryPromptRequest } from './analysis-prompts';
import { youtubeAPI, PrioritizedVideo } from './youtube-api';
import { BaseRequestInfo, PlatformInfo } from '../types/common-interfaces';

export interface DataCollectionRequest extends BaseRequestInfo, PlatformInfo {
  keyword: string; // 기존 호환성을 위해 유지 (searchKeyword와 동일)
  mainKeyword?: string; // 메인키워드 (옵션)
  mode: 'fast' | 'accurate';
}

export interface CollectedBlogData {
  rank: number; // 블로그 순위 (1-10)
  title: string; // 블로그 제목
  url: string; // 블로그 URL
  platform: string; // 플랫폼 (네이버)
}


export interface CollectedYouTubeData {
  videoId: string; // YouTube videoId
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
  description?: string;
  tags?: string[];
  categoryId?: string;
  definition?: string; // hd/sd
  caption?: boolean; // 자막 여부
  priority: number; // 우선순위 점수
  summary?: string; // 자막 요약
}

export interface YouTubeAnalysisResult {
  video_summaries: Array<{
    video_number: number;
    key_points: string;
  }>;
  common_themes: string[];
  practical_tips: string[];
  expert_insights: string[];
  blog_suggestions: string[];
}

export interface BlogAnalysisResult {
  competitor_titles: string[];
  core_keywords: string[];
  essential_content: string[];
  key_points: string[];
  improvement_opportunities: string[];
}

export interface DataCollectionResult {
  blogs: CollectedBlogData[]; // 전체 50개 블로그
  selectedBlogs: SelectedBlogTitle[]; // AI가 선별한 상위 10개
  crawledBlogs: BlogContent[]; // 크롤링된 블로그 본문 데이터
  contentSummary?: BlogAnalysisResult; // 블로그 콘텐츠 분석 결과 (JSON)
  contentSummaryRaw?: string; // 블로그 콘텐츠 분석 원본 텍스트 (호환성용)
  youtubeAnalysis?: YouTubeAnalysisResult; // YouTube 자막 분석 결과 (JSON)
  youtubeAnalysisRaw?: string; // YouTube 자막 분석 원본 텍스트 (호환성용)
  youtube: CollectedYouTubeData[];
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
    { step: '네이버 블로그 수집 중', progress: 0, status: 'pending' },
    { step: '유튜브 영상 수집 중', progress: 0, status: 'pending' },
    { step: 'AI가 우수 콘텐츠 선별 중', progress: 0, status: 'pending' },
    { step: '유튜브 자막 추출 중', progress: 0, status: 'pending' },
    { step: '블로그 본문 크롤링 중', progress: 0, status: 'pending' },
    { step: '블로그 콘텐츠 분석', progress: 0, status: 'pending' },
    { step: '유튜브 콘텐츠 분석', progress: 0, status: 'pending' }
  ];

  constructor(progressCallback?: (progress: AnalysisProgress[]) => void) {
    this.progressCallback = progressCallback;
  }

  async collectAndAnalyze(request: DataCollectionRequest): Promise<DataCollectionResult> {
    const startTime = Date.now();
    console.log('🔍 데이터 수집 및 분석 시작:', request);

    try {

      // 1. 네이버 블로그 데이터 수집 (50개)
      const blogs = await this.collectBlogData(request.keyword, request.mainKeyword || request.keyword);
      this.updateProgress(0, 'completed', blogs);

      // 2. 유튜브 데이터 수집 (100개→30개 상대평가 선별)
      const youtube = await this.collectYouTubeData(request.keyword);
      this.updateProgress(1, 'completed', youtube);

      // 3. AI 블로그+YouTube 통합 선별 (상위 10개씩)
      const selectedBlogs = await this.selectTopBlogs(request, blogs, youtube);
      this.updateProgress(2, 'completed', selectedBlogs);

      // 4. 선별된 YouTube 영상 자막 추출 (상위 3개)
      const enrichedYouTube = await this.extractYouTubeSubtitles(selectedBlogs.selectedVideos);
      this.updateProgress(3, 'completed', enrichedYouTube);

      // 5. 선별된 블로그 본문 크롤링 (상위 3개)
      const crawledBlogs = await this.crawlSelectedBlogs(selectedBlogs.selectedTitles);
      this.updateProgress(4, 'completed', crawledBlogs);

      // 6. 블로그 콘텐츠 분석 (별도)
      const blogAnalysisData = await this.generateContentSummary(request, crawledBlogs);
      const contentSummaryResult = blogAnalysisData.analysisResult;
      const contentSummaryRaw = blogAnalysisData.rawText;
      this.updateProgress(5, 'completed', contentSummaryResult || contentSummaryRaw);
      
      // 7. YouTube 자막 분석 (별도)
      let youtubeAnalysisResult: YouTubeAnalysisResult | null = null;
      let youtubeAnalysisRaw = '';
      if (enrichedYouTube && enrichedYouTube.length > 0) {
        const analysisData = await this.analyzeYouTubeSubtitles(request, enrichedYouTube);
        youtubeAnalysisResult = analysisData.analysisResult;
        youtubeAnalysisRaw = analysisData.rawText;
      }
      this.updateProgress(6, 'completed', youtubeAnalysisResult || youtubeAnalysisRaw);


      const processingTime = Date.now() - startTime;

      const result: DataCollectionResult = {
        blogs, // 전체 50개 블로그
        selectedBlogs: selectedBlogs.selectedTitles, // AI가 선별한 상위 10개 블로그
        crawledBlogs, // 크롤링된 블로그 본문 데이터
        contentSummary: contentSummaryResult, // 블로그 콘텐츠 분석 결과 (JSON)
        contentSummaryRaw, // 블로그 콘텐츠 분석 원본 텍스트
        youtubeAnalysis: youtubeAnalysisResult, // YouTube 자막 분석 결과 (JSON)
        youtubeAnalysisRaw, // YouTube 자막 분석 원본 텍스트
        youtube: enrichedYouTube, // AI가 선별한 상위 3개 YouTube (자막 추출 완료)
        summary: {
          totalSources: blogs.length + enrichedYouTube.length,
          dataQuality: crawledBlogs.filter(b => b.success).length >= 2 ? 'high' : crawledBlogs.filter(b => b.success).length >= 1 ? 'medium' : 'low',
          processingTime,
          recommendations: [
            '수집된 데이터를 바탕으로 경쟁사 분석 완료',
            contentSummaryResult || contentSummaryRaw ? '블로그 콘텐츠 분석을 참고하여 글 작성' : '블로그 분석 실패',
            youtubeAnalysisResult || youtubeAnalysisRaw ? 'YouTube 자막 분석을 활용하여 영상 콘텐츠 인사이트 반영' : 'YouTube 분석 없음'
          ].filter(rec => !rec.includes('실패') && !rec.includes('없음'))
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


  private async collectBlogData(searchKeyword: string, mainKeyword: string): Promise<CollectedBlogData[]> {
    this.updateProgress(0, 'running');
    
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
    this.updateProgress(4, 'running');
    
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
        this.analysisSteps[4].progress = overallProgress;
        
        // 상세 메시지 업데이트
        this.analysisSteps[4].message = `${crawlingProgress.current}/${crawlingProgress.total}: ${crawlingProgress.url}`;
        
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

  private async generateContentSummary(request: DataCollectionRequest, crawledBlogs: BlogContent[]): Promise<{ analysisResult: BlogAnalysisResult | null, rawText: string }> {
    try {
      if (!crawledBlogs || crawledBlogs.length === 0) {
        console.log('크롤링된 블로그가 없어 콘텐츠 요약을 건너뜁니다');
        const fallbackText = '크롤링된 블로그가 없어 분석할 수 없습니다.';
        return { analysisResult: null, rawText: fallbackText };
      }

      console.log(`📝 ${crawledBlogs.length}개 블로그 콘텐츠 요약 분석 시작`);
      
      // BlogSummaryPrompts 요청 구성 (블로그만)
      const summaryRequest: SummaryPromptRequest = {
        selectedTitle: request.selectedTitle,
        searchKeyword: request.keyword,
        mainKeyword: request.mainKeyword || request.keyword,
        contentType: request.contentType,
        reviewType: request.reviewType,
        competitorBlogs: crawledBlogs,
        // youtubeVideos 제거 - 블로그만 분석
        subKeywords: request.subKeywords
      };

      // 블로그 분석 AI용 프롬프트 생성
      const prompt = AnalysisPrompts.generateBlogAnalysisPrompt(summaryRequest);
      
      // LLM 호출
      const informationClient = LLMClientFactory.getInformationClient();
      const messages: LLMMessage[] = [
        { role: 'user', content: prompt }
      ];

      console.log('🤖 [LLM 요청] 블로그 콘텐츠 요약 분석 요청');
      
      const response = await informationClient.generateText(messages);
      
      console.log('🤖 [LLM 응답] 블로그 콘텐츠 요약 분석 결과 받음');
      
      // JSON 파싱 시도
      try {
        const jsonMatch = response.content.match(/```json\s*([\s\S]*?)\s*```/);
        if (jsonMatch) {
          const analysisResult = JSON.parse(jsonMatch[1]) as BlogAnalysisResult;
          console.log('✅ 블로그 분석 결과 JSON 파싱 성공');
          return { analysisResult, rawText: response.content };
        } else {
          // JSON 블록 없이 바로 JSON이 온 경우
          const trimmedContent = response.content.trim();
          if (trimmedContent.startsWith('{') && trimmedContent.endsWith('}')) {
            const analysisResult = JSON.parse(trimmedContent) as BlogAnalysisResult;
            console.log('✅ 블로그 분석 결과 JSON 파싱 성공 (블록 없음)');
            return { analysisResult, rawText: response.content };
          }
        }
      } catch (parseError) {
        console.warn('⚠️ 블로그 분석 결과 JSON 파싱 실패, 원본 텍스트 사용:', parseError);
      }
      
      // JSON 파싱 실패 시 원본 텍스트만 반환
      return { analysisResult: null, rawText: response.content };
      
    } catch (error) {
      console.error('블로그 콘텐츠 요약 분석 실패:', error);
      const errorText = '콘텐츠 요약 분석 실패';
      return { analysisResult: null, rawText: errorText };
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
        reviewType: request.reviewType,
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
            videoId: video.videoId,
            title: video.title,
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




  private async collectYouTubeData(keyword: string): Promise<CollectedYouTubeData[]> {
    this.updateProgress(1, 'running');
    
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
        videoId: video.videoId,
        title: video.title,
        channelName: video.channelTitle,
        viewCount: video.viewCount,
        duration: video.duration,
        subscriberCount: video.subscriberCount,
        publishedAt: video.publishedAt,
        priority: video.priority,
        // 기본 YouTube 데이터 (자막 추출 전)
        likeCount: (video as any).likeCount || 'N/A',
        commentCount: (video as any).commentCount || 'N/A',
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
    this.updateProgress(3, 'running');
    
    try {
      if (!selectedVideos || selectedVideos.length === 0) {
        console.log('선별된 YouTube 영상이 없어 자막 추출을 건너뜁니다');
        return [];
      }

      console.log(`📝 선별된 YouTube ${selectedVideos.length}개 영상 중 상위 3개 자막 무조건 확보 시작`);
      
      const enrichedVideos: CollectedYouTubeData[] = [];
      const targetCount = 3; // 무조건 3개 확보
      let successCount = 0;
      
      // AI 순위대로 자막 추출 시도 (3개 성공할 때까지)
      for (let i = 0; i < selectedVideos.length && successCount < targetCount; i++) {
        const video = selectedVideos[i];
        
        console.log(`📝 [${i + 1}위] "${video.title}" 자막 추출 중... (목표: ${successCount + 1}/${targetCount})`);
        
        try {
          // 자막 추출 (300자 이상만 통과)
          const subtitles = await youtubeAPI.extractSubtitlesSimple(video.videoId);
          
          // 자막 추출 실패시 다음 영상으로
          if (subtitles.length === 0) {
            console.warn(`⚠️ [${i + 1}위] 자막 추출 실패, 다음 영상 시도`);
            continue;
          }
          
          // 자막 전체를 저장 (요약 제거)
          const fullSubtitleText = subtitles[0].text;
          
          // 자막 텍스트 정리 (JSON 형태나 이상한 데이터 제거)
          let cleanSubtitleText = fullSubtitleText;
          
          // JSON 형태의 데이터인 경우 정리
          if (cleanSubtitleText.includes('"wireMagic"') || cleanSubtitleText.includes('"pens"')) {
            console.warn(`⚠️ JSON 형태의 자막 데이터 발견, 정리 중...`);
            // JSON 부분 제거하고 실제 텍스트만 추출 시도
            const textMatches = cleanSubtitleText.match(/[가-힣a-zA-Z0-9\s.,!?]+/g);
            if (textMatches && textMatches.length > 0) {
              cleanSubtitleText = textMatches.join(' ').trim();
            } else {
              cleanSubtitleText = '자막 추출 실패 (데이터 형식 오류)';
            }
          }
          
          // 너무 짧은 경우 처리
          if (cleanSubtitleText.length < 100) {
            cleanSubtitleText = `자막 추출 성공 (${cleanSubtitleText.length}자 - 짧은 내용)`;
          }

          // CollectedYouTubeData 형태로 변환 (타입 단언 사용)
          const videoWithExtendedData = video as SelectedYouTubeVideo & {
            subscriberCount?: number;
            publishedAt?: string;
            likeCount?: string;
            commentCount?: string;
          };
          
          const enrichedVideo: CollectedYouTubeData = {
            videoId: video.videoId,
            title: video.title,
            channelName: video.channelName,
            viewCount: video.viewCount,
            duration: video.duration,
            subscriberCount: videoWithExtendedData.subscriberCount || 0,
            publishedAt: videoWithExtendedData.publishedAt || new Date().toISOString(),
            priority: video.priority,
            summary: cleanSubtitleText, // 정리된 자막 저장
            likeCount: videoWithExtendedData.likeCount || 'N/A',
            commentCount: videoWithExtendedData.commentCount || 'N/A',
            thumbnail: undefined,
            description: undefined,
            tags: undefined,
            categoryId: undefined,
            definition: undefined,
            caption: true
          };
          
          enrichedVideos.push(enrichedVideo);
          successCount++;
          
          console.log(`✅ [${i + 1}위] "${video.title}" 자막 확보 성공 (${successCount}/${targetCount})`);
          console.log(`   자막 길이: ${fullSubtitleText.length}자`);
          
        } catch (error) {
          console.warn(`⚠️ [${i + 1}위] "${video.title}" 자막 추출 실패, 다음 영상 시도:`, error);
          continue;
        }
      }
      
      // 자막 확보 결과 로그
      if (successCount < targetCount) {
        console.warn(`⚠️ 목표 ${targetCount}개 중 ${successCount}개만 자막 확보됨 (자막 없는 영상은 제외)`);
      }
      
      console.log(`✅ YouTube 자막 추출 완료: ${enrichedVideos.length}개 영상 (자막 있음: ${successCount}개)`);
      
      return enrichedVideos;
      
    } catch (error) {
      console.error('❌ YouTube 자막 추출 시스템 오류:', error);
      
      // 시스템 오류 시 빈 배열 반환
      return [];
    }
  }

  private async analyzeYouTubeSubtitles(request: DataCollectionRequest, youtubeVideos: CollectedYouTubeData[]): Promise<{ analysisResult: YouTubeAnalysisResult | null, rawText: string }> {
    try {
      if (youtubeVideos.length === 0) {
        console.warn('자막이 있는 YouTube 영상이 없어 분석을 건너뜁니다');
        const fallbackText = '자막이 있는 YouTube 영상이 없습니다.';
        return { analysisResult: null, rawText: fallbackText };
      }

      console.log(`📺 YouTube 자막 분석 시작: ${youtubeVideos.length}개 영상`);

      // YouTube 전용 분석 프롬프트 생성
      const prompt = AnalysisPrompts.generateYouTubeAnalysisPrompt(request, youtubeVideos);
      
      // LLM 호출
      const informationClient = LLMClientFactory.getInformationClient();
      const messages: LLMMessage[] = [
        { role: 'user', content: prompt }
      ];

      console.log('🤖 [LLM 요청] YouTube 자막 분석 요청');
      
      const response = await informationClient.generateText(messages);
      
      console.log('🤖 [LLM 응답] YouTube 자막 분석 결과 받음');
      
      // JSON 파싱 시도
      try {
        const jsonMatch = response.content.match(/```json\s*([\s\S]*?)\s*```/);
        if (jsonMatch) {
          const analysisResult = JSON.parse(jsonMatch[1]) as YouTubeAnalysisResult;
          console.log('✅ YouTube 분석 결과 JSON 파싱 성공');
          return { analysisResult, rawText: response.content };
        } else {
          // JSON 블록 없이 바로 JSON이 온 경우
          const trimmedContent = response.content.trim();
          if (trimmedContent.startsWith('{') && trimmedContent.endsWith('}')) {
            const analysisResult = JSON.parse(trimmedContent) as YouTubeAnalysisResult;
            console.log('✅ YouTube 분석 결과 JSON 파싱 성공 (블록 없음)');
            return { analysisResult, rawText: response.content };
          }
        }
      } catch (parseError) {
        console.warn('⚠️ YouTube 분석 결과 JSON 파싱 실패, 원본 텍스트 사용:', parseError);
      }
      
      // JSON 파싱 실패 시 원본 텍스트만 반환
      return { analysisResult: null, rawText: response.content };
      
    } catch (error) {
      console.error('❌ YouTube 자막 분석 실패:', error);
      const errorText = 'YouTube 자막 분석 실패';
      return { analysisResult: null, rawText: errorText };
    }
  }




}