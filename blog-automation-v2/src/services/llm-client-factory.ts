// LLM 클라이언트 팩토리
export interface LLMConfig {
  provider: 'openai' | 'claude' | 'gemini';
  model: string;
  apiKey: string;
}

export interface LLMResponse {
  content: string;
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
}

export interface LLMMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export abstract class BaseLLMClient {
  protected config: LLMConfig;

  constructor(config: LLMConfig) {
    this.config = config;
  }

  abstract generateText(messages: LLMMessage[]): Promise<LLMResponse>;
  abstract generateImage(prompt: string): Promise<string>; // 이미지 URL 반환
}

export class OpenAIClient extends BaseLLMClient {
  async generateText(messages: LLMMessage[]): Promise<LLMResponse> {
    // OpenAI API 호출 시뮬레이션
    
    // 실제로는 OpenAI SDK 사용
    const mockResponse = {
      content: `[${this.config.model}] 생성된 응답입니다.`,
      usage: {
        promptTokens: 100,
        completionTokens: 200,
        totalTokens: 300
      }
    };

    return new Promise(resolve => {
      setTimeout(() => resolve(mockResponse), 1000);
    });
  }

  async generateImage(prompt: string): Promise<string> {
    
    // 실제로는 OpenAI DALL-E API 호출
    return new Promise(resolve => {
      setTimeout(() => {
        resolve(`https://via.placeholder.com/512x512?text=${encodeURIComponent(prompt)}`);
      }, 2000);
    });
  }
}

export class ClaudeClient extends BaseLLMClient {
  async generateText(messages: LLMMessage[]): Promise<LLMResponse> {
    
    const mockResponse = {
      content: `[${this.config.model}] Claude가 생성한 고품질 응답입니다.`,
      usage: {
        promptTokens: 120,
        completionTokens: 250,
        totalTokens: 370
      }
    };

    return new Promise(resolve => {
      setTimeout(() => resolve(mockResponse), 1500);
    });
  }

  async generateImage(prompt: string): Promise<string> {
    throw new Error('Claude는 이미지 생성을 지원하지 않습니다.');
  }
}

export class GeminiClient extends BaseLLMClient {
  async generateText(messages: LLMMessage[]): Promise<LLMResponse> {
    
    const mockResponse = {
      content: `[${this.config.model}] Gemini가 생성한 빠른 응답입니다.`,
      usage: {
        promptTokens: 80,
        completionTokens: 180,
        totalTokens: 260
      }
    };

    return new Promise(resolve => {
      setTimeout(() => resolve(mockResponse), 800);
    });
  }

  async generateImage(prompt: string): Promise<string> {
    
    return new Promise(resolve => {
      setTimeout(() => {
        resolve(`https://via.placeholder.com/512x512?text=Gemini+${encodeURIComponent(prompt)}`);
      }, 1500);
    });
  }
}

export class LLMClientFactory {
  private static informationClient: BaseLLMClient | null = null;
  private static writingClient: BaseLLMClient | null = null;
  private static imageClient: BaseLLMClient | null = null;

  static createClient(config: LLMConfig): BaseLLMClient {
    switch (config.provider) {
      case 'openai':
        return new OpenAIClient(config);
      case 'claude':
        return new ClaudeClient(config);
      case 'gemini':
        return new GeminiClient(config);
      default:
        throw new Error(`지원되지 않는 LLM 공급업체: ${config.provider}`);
    }
  }

  static setInformationClient(config: LLMConfig): void {
    this.informationClient = this.createClient(config);
  }

  static setWritingClient(config: LLMConfig): void {
    this.writingClient = this.createClient(config);
  }

  static setImageClient(config: LLMConfig): void {
    this.imageClient = this.createClient(config);
  }

  static getInformationClient(): BaseLLMClient {
    if (!this.informationClient) {
      throw new Error('Information LLM client not configured');
    }
    return this.informationClient;
  }

  static getWritingClient(): BaseLLMClient {
    if (!this.writingClient) {
      throw new Error('Writing LLM client not configured');
    }
    return this.writingClient;
  }

  static getImageClient(): BaseLLMClient {
    if (!this.imageClient) {
      throw new Error('Image LLM client not configured');
    }
    return this.imageClient;
  }

  // 기본 설정 로드
  static loadDefaultSettings(): void {
    try {
      const savedSettings = localStorage.getItem('llm-settings');
      if (savedSettings) {
        const settings = JSON.parse(savedSettings);
        
        if (settings.information?.apiKey) {
          this.setInformationClient(settings.information);
        }
        if (settings.writing?.apiKey) {
          this.setWritingClient(settings.writing);
        }
        if (settings.image?.apiKey) {
          this.setImageClient(settings.image);
        }
      } else {
        // 기본값 설정 (무료 조합)
        this.setInformationClient({
          provider: 'gemini',
          model: 'gemini-2.0-flash',
          apiKey: 'demo' // 실제로는 사용자가 입력
        });
        this.setWritingClient({
          provider: 'gemini',
          model: 'gemini-2.5-flash-free',
          apiKey: 'demo'
        });
        this.setImageClient({
          provider: 'gemini',
          model: 'gemini-2.5-flash-image',
          apiKey: 'demo'
        });
      }
    } catch (error) {
      console.error('LLM 설정 로드 실패:', error);
    }
  }
}