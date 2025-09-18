interface YouTubeAPIConfig {
  apiKey: string;
}

interface YouTubeVideoItem {
  id: {
    videoId: string;
  };
  snippet: {
    title: string;
    description: string;
    channelTitle: string;
    publishedAt: string;
    thumbnails: {
      default: {
        url: string;
      };
    };
  };
}

interface YouTubeSearchResponse {
  items: YouTubeVideoItem[];
  pageInfo: {
    totalResults: number;
    resultsPerPage: number;
  };
}

export class YouTubeAPI {
  private config: YouTubeAPIConfig | null = null;

  async loadConfig(): Promise<void> {
    try {
      // YouTube API 설정을 로컬스토리지나 Electron 설정에서 로드
      if ((window as any).electronAPI && typeof (window as any).electronAPI.loadYouTubeApiSettings === 'function') {
        const result = await (window as any).electronAPI.loadYouTubeApiSettings();
        if (result && result.success && result.data) {
          this.config = {
            apiKey: result.data.apiKey
          };
          console.log('✅ YouTube API 설정 로드 성공');
        } else {
          console.warn('⚠️ YouTube API 설정이 없습니다');
        }
      } else {
        console.warn('⚠️ Electron API가 없습니다 (브라우저 환경)');
      }
    } catch (error) {
      console.error('❌ YouTube API 설정 로드 실패:', error);
      throw new Error(`YouTube API 설정 로드 실패: ${error.message}`);
    }
  }

  async searchVideos(keyword: string, maxResults: number = 10): Promise<YouTubeVideoItem[]> {
    if (!this.config) {
      throw new Error('YouTube API 설정이 로드되지 않았습니다. loadConfig()를 먼저 호출하세요.');
    }

    try {
      const encodedKeyword = encodeURIComponent(keyword);
      const url = `https://www.googleapis.com/youtube/v3/search?part=snippet&q=${encodedKeyword}&key=${this.config.apiKey}&type=video&maxResults=${maxResults}&order=relevance`;

      console.log(`📺 YouTube API 검색: ${keyword} (최대 ${maxResults}개)`);

      const response = await fetch(url);
      
      if (!response.ok) {
        if (response.status === 403) {
          throw new Error('YouTube API 할당량 초과 또는 API 키가 유효하지 않습니다');
        } else if (response.status === 400) {
          throw new Error('YouTube API 요청 형식이 잘못되었습니다');
        } else {
          throw new Error(`YouTube API 호출 실패: ${response.status} ${response.statusText}`);
        }
      }

      const data: YouTubeSearchResponse = await response.json();
      
      console.log(`✅ YouTube 검색 완료: ${data.items.length}개 동영상`);
      
      return data.items;

    } catch (error) {
      console.error('❌ YouTube 검색 실패:', error);
      throw error;
    }
  }

  async getVideoDetails(videoId: string): Promise<any> {
    if (!this.config) {
      throw new Error('YouTube API 설정이 로드되지 않았습니다');
    }

    try {
      const url = `https://www.googleapis.com/youtube/v3/videos?part=statistics,contentDetails&id=${videoId}&key=${this.config.apiKey}`;
      
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`YouTube API 호출 실패: ${response.status}`);
      }

      const data = await response.json();
      return data.items[0];

    } catch (error) {
      console.error('❌ YouTube 동영상 상세 정보 조회 실패:', error);
      throw error;
    }
  }

  // ISO 8601 duration을 사람이 읽기 쉬운 형태로 변환
  static parseDuration(duration: string): string {
    const match = duration.match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/);
    if (!match) return '0:00';

    const hours = parseInt(match[1] || '0');
    const minutes = parseInt(match[2] || '0');
    const seconds = parseInt(match[3] || '0');

    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    } else {
      return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }
  }

  // 조회수를 한국어 형태로 변환
  static formatViewCount(viewCount: string): string {
    const count = parseInt(viewCount);
    if (count >= 10000) {
      return `${Math.floor(count / 10000)}만회`;
    } else if (count >= 1000) {
      return `${(count / 1000).toFixed(1)}천회`;
    } else {
      return `${count}회`;
    }
  }
}

// 싱글톤 인스턴스
export const youtubeAPI = new YouTubeAPI();