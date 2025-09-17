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
    try {
      const response = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.config.apiKey}`
        },
        body: JSON.stringify({
          model: this.config.model,
          messages: messages.map(msg => ({
            role: msg.role,
            content: msg.content
          })),
          temperature: 0.7,
          max_tokens: 2000
        })
      });

      if (!response.ok) {
        throw new Error(`OpenAI API 오류: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      
      return {
        content: data.choices[0]?.message?.content || '',
        usage: {
          promptTokens: data.usage?.prompt_tokens || 0,
          completionTokens: data.usage?.completion_tokens || 0,
          totalTokens: data.usage?.total_tokens || 0
        }
      };
    } catch (error) {
      console.error('OpenAI API 호출 실패:', error);
      throw error;
    }
  }

  async generateImage(prompt: string): Promise<string> {
    try {
      const response = await fetch('https://api.openai.com/v1/images/generations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.config.apiKey}`
        },
        body: JSON.stringify({
          model: 'dall-e-3',
          prompt: prompt,
          n: 1,
          size: '1024x1024'
        })
      });

      if (!response.ok) {
        throw new Error(`OpenAI Image API 오류: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return data.data[0]?.url || '';
    } catch (error) {
      console.error('OpenAI Image API 호출 실패:', error);
      throw error;
    }
  }
}

export class ClaudeClient extends BaseLLMClient {
  async generateText(messages: LLMMessage[]): Promise<LLMResponse> {
    try {
      const response = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': this.config.apiKey,
          'anthropic-version': '2023-06-01'
        },
        body: JSON.stringify({
          model: this.config.model,
          max_tokens: 6000,
          temperature: 0.7,
          messages: messages.map(msg => ({
            role: msg.role === 'system' ? 'user' : msg.role,
            content: msg.role === 'system' ? `System: ${msg.content}` : msg.content
          }))
        })
      });

      if (!response.ok) {
        throw new Error(`Claude API 오류: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      
      return {
        content: data.content[0]?.text || '',
        usage: {
          promptTokens: data.usage?.input_tokens || 0,
          completionTokens: data.usage?.output_tokens || 0,
          totalTokens: (data.usage?.input_tokens || 0) + (data.usage?.output_tokens || 0)
        }
      };
    } catch (error) {
      console.error('Claude API 호출 실패:', error);
      throw error;
    }
  }

  async generateImage(prompt: string): Promise<string> {
    throw new Error('Claude는 이미지 생성을 지원하지 않습니다.');
  }
}

export class GeminiClient extends BaseLLMClient {
  async generateText(messages: LLMMessage[]): Promise<LLMResponse> {
    try {
      // 메시지를 Gemini 형식으로 변환
      let textContent = '';
      for (const message of messages) {
        if (message.role === 'system') {
          textContent += `System: ${message.content}\n\n`;
        } else if (message.role === 'user') {
          textContent += `User: ${message.content}`;
        }
      }

      const response = await fetch(
        `https://generativelanguage.googleapis.com/v1beta/models/${this.config.model}:generateContent?key=${this.config.apiKey}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            contents: [{
              parts: [{
                text: textContent
              }]
            }],
            generationConfig: {
              maxOutputTokens: 8000,
              temperature: 0.7
            }
          })
        }
      );

      if (!response.ok) {
        throw new Error(`Gemini API 오류: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      
      return {
        content: data.candidates[0]?.content?.parts[0]?.text || '',
        usage: {
          promptTokens: data.usageMetadata?.promptTokenCount || 0,
          completionTokens: data.usageMetadata?.candidatesTokenCount || 0,
          totalTokens: data.usageMetadata?.totalTokenCount || 0
        }
      };
    } catch (error) {
      console.error('Gemini API 호출 실패:', error);
      throw error;
    }
  }

  async generateImage(prompt: string): Promise<string> {
    throw new Error('Gemini는 현재 이미지 생성을 지원하지 않습니다.');
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
  static async loadDefaultSettings(): Promise<void> {
    try {
      // Electron API가 있는지 확인
      if (!(window as any).electronAPI || typeof (window as any).electronAPI.loadSettings !== 'function') {
        console.warn('Electron API를 사용할 수 없어 기본값을 사용합니다.');
        this.loadDefaultSettingsFromLocalStorage();
        return;
      }

      // Electron API를 통해 설정 로드
      const savedData = await (window as any).electronAPI.loadSettings();
      console.log('저장된 LLM 설정:', savedData);
      
      if (savedData && savedData.settings) {
        const settings = savedData.settings;
        const testingStatus = savedData.testingStatus || {};
        console.log('파싱된 설정:', settings);
        console.log('테스트 상태:', testingStatus);
        
        // 테스트가 성공한 설정만 적용
        if (settings.information?.apiKey && testingStatus.information?.success) {
          console.log('정보요약 AI 설정 로드:', settings.information);
          this.setInformationClient(settings.information);
        }
        if (settings.writing?.apiKey && testingStatus.writing?.success) {
          console.log('글쓰기 AI 설정 로드:', settings.writing);
          this.setWritingClient(settings.writing);
        }
        if (settings.image?.apiKey && testingStatus.image?.success) {
          console.log('이미지 AI 설정 로드:', settings.image);
          this.setImageClient(settings.image);
        }
      } else {
        console.log('저장된 설정이 없어 기본값을 사용합니다.');
        this.loadDefaultValues();
      }
    } catch (error) {
      console.error('LLM 설정 로드 실패:', error);
      this.loadDefaultValues();
    }
  }

  // localStorage에서 설정 로드 (웹 환경용 백업)
  private static loadDefaultSettingsFromLocalStorage(): void {
    try {
      const savedSettings = localStorage.getItem('llm-settings');
      console.log('localStorage에서 LLM 설정 로드:', savedSettings);
      if (savedSettings) {
        const settings = JSON.parse(savedSettings);
        console.log('파싱된 설정:', settings);
        
        if (settings.information?.apiKey) {
          console.log('정보요약 AI 설정 로드:', settings.information);
          this.setInformationClient(settings.information);
        }
        if (settings.writing?.apiKey) {
          this.setWritingClient(settings.writing);
        }
        if (settings.image?.apiKey) {
          this.setImageClient(settings.image);
        }
      } else {
        this.loadDefaultValues();
      }
    } catch (error) {
      console.error('localStorage LLM 설정 로드 실패:', error);
      this.loadDefaultValues();
    }
  }

  // 기본값 설정
  private static loadDefaultValues(): void {
    console.log('기본값 설정을 로드합니다.');
    // 기본값은 설정하지 않음 - 사용자가 직접 설정해야 함
    // 필요시 아래 주석을 해제하여 기본값 설정 가능
    /*
    this.setInformationClient({
      provider: 'gemini',
      model: 'gemini-2.0-flash',
      apiKey: 'demo'
    });
    this.setWritingClient({
      provider: 'gemini',
      model: 'gemini-2.5-flash',
      apiKey: 'demo'
    });
    this.setImageClient({
      provider: 'gemini',
      model: 'gemini-2.5-flash-image',
      apiKey: 'demo'
    });
    */
  }
}