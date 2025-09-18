import { youtubeAPI, PrioritizedVideo, SubtitleTrack } from './youtube-api';

export interface YouTubeAnalysisRequest {
  keyword: string;
  maxVideos?: number; // 기본 3개
}

export interface YouTubeVideoAnalysis {
  video: PrioritizedVideo;
  subtitles: SubtitleTrack[];
  analysisScore: number;
  hasSubtitles: boolean;
}

export interface YouTubeAnalysisResult {
  keyword: string;
  totalVideosFound: number;
  analyzedVideos: YouTubeVideoAnalysis[];
  summary: {
    videosWithSubtitles: number;
    totalSubtitleLength: number;
    averageScore: number;
    topVideo: PrioritizedVideo | null;
  };
}

export class YouTubeAnalysisEngine {
  private progressCallback?: (message: string, progress: number) => void;

  constructor(progressCallback?: (message: string, progress: number) => void) {
    this.progressCallback = progressCallback;
  }

  async analyzeVideos(request: YouTubeAnalysisRequest): Promise<YouTubeAnalysisResult> {
    const { keyword, maxVideos = 3 } = request;
    
    try {
      this.updateProgress('YouTube API 설정 로드 중...', 0);
      
      // 1. YouTube API 초기화
      await youtubeAPI.loadConfig();

      this.updateProgress(`"${keyword}" 키워드로 동영상 검색 중...`, 10);

      // 2. 우선순위 기반 동영상 검색
      const prioritizedVideos = await youtubeAPI.searchPrioritizedVideos(keyword, maxVideos * 2);
      
      if (prioritizedVideos.length === 0) {
        throw new Error('검색 결과가 없습니다');
      }

      this.updateProgress(`${prioritizedVideos.length}개 동영상 발견, 상위 ${maxVideos}개 분석 시작`, 30);

      // 3. 상위 N개 동영상만 선택
      const selectedVideos = prioritizedVideos.slice(0, maxVideos);
      const analysisResults: YouTubeVideoAnalysis[] = [];

      // 4. 각 동영상의 자막 추출 및 분석
      for (let i = 0; i < selectedVideos.length; i++) {
        const video = selectedVideos[i];
        const progressPercent = 30 + (i / selectedVideos.length) * 60;
        
        this.updateProgress(`동영상 ${i + 1}/${selectedVideos.length}: "${video.title}" 자막 추출 중...`, progressPercent);

        try {
          // 자막 추출
          const subtitles = await youtubeAPI.extractSubtitlesSimple(video.videoId);
          
          const analysis: YouTubeVideoAnalysis = {
            video,
            subtitles,
            analysisScore: this.calculateAnalysisScore(video, subtitles),
            hasSubtitles: subtitles.length > 0
          };

          analysisResults.push(analysis);

          console.log(`✅ 동영상 분석 완료: ${video.title} (자막: ${subtitles.length > 0 ? 'O' : 'X'})`);

        } catch (error) {
          console.warn(`⚠️ 동영상 분석 실패: ${video.title}`, error);
          
          // 자막 없이라도 결과에 포함
          const analysis: YouTubeVideoAnalysis = {
            video,
            subtitles: [],
            analysisScore: video.priority, // 기본 우선순위 점수 사용
            hasSubtitles: false
          };

          analysisResults.push(analysis);
        }
      }

      this.updateProgress('분석 결과 정리 중...', 95);

      // 5. 결과 요약
      const summary = this.generateSummary(analysisResults);

      const result: YouTubeAnalysisResult = {
        keyword,
        totalVideosFound: prioritizedVideos.length,
        analyzedVideos: analysisResults,
        summary
      };

      this.updateProgress('YouTube 분석 완료!', 100);

      console.log('🎯 YouTube 분석 완료:', {
        키워드: keyword,
        분석된_동영상: analysisResults.length,
        자막_있는_동영상: summary.videosWithSubtitles,
        평균_점수: summary.averageScore
      });

      return result;

    } catch (error) {
      console.error('❌ YouTube 분석 실패:', error);
      throw error;
    }
  }

  // 분석 점수 계산 (우선순위 + 자막 품질)
  private calculateAnalysisScore(video: PrioritizedVideo, subtitles: SubtitleTrack[]): number {
    let score = video.priority; // 기본 우선순위 점수

    // 자막 보너스 점수
    if (subtitles.length > 0) {
      score += 10; // 자막 존재 보너스

      for (const subtitle of subtitles) {
        if (subtitle.language === 'ko') {
          score += 15; // 한국어 자막 보너스
        } else if (subtitle.language === 'en') {
          score += 5; // 영어 자막 보너스
        }

        // 자막 길이 보너스
        const textLength = subtitle.text.length;
        if (textLength > 5000) score += 10;
        else if (textLength > 2000) score += 5;
        else if (textLength > 500) score += 2;
      }
    } else {
      score -= 5; // 자막 없음 페널티
    }

    return Math.round(score);
  }

  // 결과 요약 생성
  private generateSummary(analyses: YouTubeVideoAnalysis[]) {
    const videosWithSubtitles = analyses.filter(a => a.hasSubtitles).length;
    const totalSubtitleLength = analyses.reduce((sum, a) => 
      sum + a.subtitles.reduce((subSum, s) => subSum + s.text.length, 0), 0
    );
    const averageScore = analyses.reduce((sum, a) => sum + a.analysisScore, 0) / analyses.length;
    
    // 최고 점수 동영상 찾기
    const topAnalysis = analyses.reduce((best, current) => 
      current.analysisScore > best.analysisScore ? current : best
    );

    return {
      videosWithSubtitles,
      totalSubtitleLength,
      averageScore: Math.round(averageScore * 10) / 10,
      topVideo: topAnalysis ? topAnalysis.video : null
    };
  }

  // 진행상황 업데이트
  private updateProgress(message: string, progress: number) {
    console.log(`📺 [${progress}%] ${message}`);
    if (this.progressCallback) {
      this.progressCallback(message, progress);
    }
  }

  // AI 분석용 텍스트 추출
  static extractTextForAI(analysisResult: YouTubeAnalysisResult): string {
    const { keyword, analyzedVideos } = analysisResult;
    
    let aiText = `YouTube 동영상 분석 결과 (키워드: "${keyword}")\n\n`;

    analyzedVideos.forEach((analysis, index) => {
      const { video, subtitles, hasSubtitles } = analysis;
      
      aiText += `=== 동영상 ${index + 1}: ${video.title} ===\n`;
      aiText += `채널: ${video.channelTitle}\n`;
      aiText += `조회수: ${video.viewCount.toLocaleString()}회\n`;
      aiText += `길이: ${Math.floor(video.duration / 60)}분\n`;
      aiText += `업로드: ${new Date(video.publishedAt).toLocaleDateString()}\n`;
      aiText += `우선순위: ${video.priority}점\n`;
      
      if (hasSubtitles && subtitles.length > 0) {
        aiText += `\n[자막 내용]\n`;
        subtitles.forEach(subtitle => {
          if (subtitle.text.trim()) {
            aiText += `${subtitle.text}\n`;
          }
        });
      } else {
        aiText += `\n[자막 없음]\n`;
      }
      
      aiText += `\n${'='.repeat(50)}\n\n`;
    });

    return aiText;
  }
}

// 사용 예시를 위한 간단한 테스트 함수
export async function testYouTubeAnalysis(keyword: string) {
  const engine = new YouTubeAnalysisEngine((message, progress) => {
    console.log(`[${progress}%] ${message}`);
  });

  try {
    const result = await engine.analyzeVideos({ keyword, maxVideos: 3 });
    
    console.log('\n📊 분석 결과 요약:');
    console.log(`- 총 ${result.totalVideosFound}개 동영상 중 ${result.analyzedVideos.length}개 분석`);
    console.log(`- 자막 있는 동영상: ${result.summary.videosWithSubtitles}개`);
    console.log(`- 평균 점수: ${result.summary.averageScore}점`);
    
    if (result.summary.topVideo) {
      console.log(`- 최고 점수: "${result.summary.topVideo.title}"`);
    }

    // AI 분석용 텍스트 출력
    const aiText = YouTubeAnalysisEngine.extractTextForAI(result);
    console.log('\n📝 AI 분석용 텍스트 (일부):');
    console.log(aiText.substring(0, 500) + '...');

    return result;

  } catch (error) {
    console.error('❌ 테스트 실패:', error);
    throw error;
  }
}