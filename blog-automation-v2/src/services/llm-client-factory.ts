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

export interface LLMTool {
  name: string;
  description: string;
  parameters: any;
}

export interface LLMGenerateOptions {
  messages: LLMMessage[];
  tools?: LLMTool[];
  maxIterations?: number;
}

export abstract class BaseLLMClient {
  protected config: LLMConfig;

  constructor(config: LLMConfig) {
    this.config = config;
  }

  abstract generateText(messages: LLMMessage[], options?: { tools?: LLMTool[] }): Promise<LLMResponse>;
  abstract generateImage(prompt: string): Promise<string>; // 이미지 URL 반환
}

export class OpenAIClient extends BaseLLMClient {
  async generateText(messages: LLMMessage[], options?: { tools?: LLMTool[] }): Promise<LLMResponse> {
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
  async generateText(messages: LLMMessage[], options?: { tools?: LLMTool[] }): Promise<LLMResponse> {
    try {
      const conversationMessages = messages.map(msg => ({
        role: msg.role === 'system' ? 'user' : msg.role,
        content: msg.role === 'system' ? `System: ${msg.content}` : msg.content
      }));

      let finalResponse = '';
      const totalUsage = { promptTokens: 0, completionTokens: 0, totalTokens: 0 };

      // 도구 호출이 완료될 때까지 반복 (최대 2번으로 제한)
      let iteration = 0;
      const maxIterations = 2;

      while (iteration < maxIterations) {
        const requestBody: any = {
          model: this.config.model,
          max_tokens: 6000,
          temperature: 0.7,
          messages: conversationMessages
        };

        // 도구가 제공된 경우 tools 파라미터 추가
        if (options?.tools && options.tools.length > 0) {
          requestBody.tools = options.tools.map(tool => ({
            name: tool.name,
            description: tool.description,
            input_schema: tool.parameters
          }));
          requestBody.tool_choice = { type: "auto" };
        }

        const response = await fetch('https://api.anthropic.com/v1/messages', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'x-api-key': this.config.apiKey,
            'anthropic-version': '2023-06-01'
          },
          body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
          if (response.status === 429) {
            // Rate limit에 걸린 경우 잠시 대기 후 재시도
            const retryAfter = response.headers.get('retry-after') || '5';
            console.log(`⏰ Rate limit 도달. ${retryAfter}초 후 재시도...`);
            await new Promise(resolve => setTimeout(resolve, parseInt(retryAfter) * 1000));
            continue; // 다시 시도
          }
          throw new Error(`Claude API 오류: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();
        
        // 사용량 누적
        totalUsage.promptTokens += data.usage?.input_tokens || 0;
        totalUsage.completionTokens += data.usage?.output_tokens || 0;
        totalUsage.totalTokens += (data.usage?.input_tokens || 0) + (data.usage?.output_tokens || 0);

        // Assistant의 응답을 대화에 추가
        conversationMessages.push({
          role: 'assistant',
          content: data.content
        });

        // 도구 호출이 있는지 확인
        let hasToolUse = false;
        const toolResults: any[] = [];

        if (data.content && Array.isArray(data.content)) {
          for (const content of data.content) {
            if (content.type === 'tool_use') {
              hasToolUse = true;
              console.log(`🔧 Claude가 도구 호출: ${content.name}`, content.input);
              
              try {
                const toolResult = await this.executeTools(content.name, content.input);
                console.log(`📊 도구 실행 결과:`, toolResult);
                
                toolResults.push({
                  type: 'tool_result',
                  tool_use_id: content.id,
                  content: JSON.stringify(toolResult)
                });
              } catch (error) {
                console.error(`❌ 도구 실행 실패 (${content.name}):`, error);
                toolResults.push({
                  type: 'tool_result',
                  tool_use_id: content.id,
                  content: `Error: ${error.message}`,
                  is_error: true
                });
              }
            } else if (content.type === 'text') {
              finalResponse += content.text;
            }
          }
        }

        // 도구 호출이 없으면 종료
        if (!hasToolUse) {
          break;
        }

        // 도구 결과를 대화에 추가
        if (toolResults.length > 0) {
          conversationMessages.push({
            role: 'user',
            content: toolResults.map(result => JSON.stringify(result)).join('\n\n')
          });
        }

        iteration++;
      }

      return {
        content: finalResponse,
        usage: totalUsage
      };
    } catch (error) {
      console.error('Claude API 호출 실패:', error);
      throw error;
    }
  }

  private async executeTools(toolName: string, input: any): Promise<any> {
    // 도구 실행 - MCP 제거됨, 직접 API 사용
    console.log(`도구 실행 요청: ${toolName}`);
    
    try {
      switch (toolName) {
        case 'naver_search_all':
        case 'naver_blog_search':
          // 네이버 관련 도구는 직접 API 사용
          console.log('네이버 도구는 직접 API로 처리됨');
          return { error: '네이버는 직접 API 사용' };
        case 'youtube_search':
          console.log('YouTube 검색 도구는 더 이상 지원되지 않음');
          return { error: 'YouTube 검색 기능 제거됨' };
        default:
          throw new Error(`Unknown tool: ${toolName}`);
      }
    } catch (error) {
      console.error(`도구 실행 실패 (${toolName}):`, error);
      return { error: error.message };
    }
  }

  async generateImage(prompt: string): Promise<string> {
    throw new Error('Claude는 이미지 생성을 지원하지 않습니다.');
  }
}

export class GeminiClient extends BaseLLMClient {
  async generateText(messages: LLMMessage[], options?: { tools?: LLMTool[] }): Promise<LLMResponse> {
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
  private static isLoading = false; // 로딩 중 상태
  private static isLoaded = false; // 로드 완료 상태
  private static cachedSettings: any = null; // 설정 캐시
  private static cachedTestingStatus: any = null; // 테스트 상태 캐시

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

  // 클라이언트 존재 여부 확인 메서드들
  static hasInformationClient(): boolean {
    return this.informationClient !== null;
  }

  static hasWritingClient(): boolean {
    return this.writingClient !== null;
  }

  static hasImageClient(): boolean {
    return this.imageClient !== null;
  }

  // 캐시된 설정 정보 반환 (API 호출 없음)
  static getCachedModelStatus(): { information: string; writing: string; image: string } {
    if (!this.isLoaded || !this.cachedSettings || !this.cachedTestingStatus) {
      return {
        information: '미설정',
        writing: '미설정',
        image: '미설정'
      };
    }

    const settings = this.cachedSettings;
    const testingStatus = this.cachedTestingStatus;

    return {
      information: this.hasInformationClient() && settings.information?.apiKey && testingStatus.information?.success 
        ? `${settings.information.provider} ${settings.information.model}` 
        : '미설정',
      writing: this.hasWritingClient() && settings.writing?.apiKey && testingStatus.writing?.success 
        ? `${settings.writing.provider} ${settings.writing.model}` 
        : '미설정',
      image: this.hasImageClient() && settings.image?.apiKey && testingStatus.image?.success 
        ? `${settings.image.provider} ${settings.image.model}` 
        : '미설정'
    };
  }

  // LLMSettings.tsx에서 사용할 캐시된 설정 데이터 반환
  static getCachedSettings(): { settings: any; testingStatus: any } | null {
    if (!this.isLoaded || !this.cachedSettings || !this.cachedTestingStatus) {
      return null;
    }
    return {
      settings: this.cachedSettings,
      testingStatus: this.cachedTestingStatus
    };
  }

  // 캐시된 설정 업데이트 (자연스러운 방식)
  static updateCachedSettings(settings: any, testingStatus: any): void {
    this.cachedSettings = settings;
    this.cachedTestingStatus = testingStatus;
    
    // 클라이언트도 업데이트
    if (settings.information?.apiKey) {
      this.setInformationClient(settings.information);
    }
    if (settings.writing?.apiKey) {
      this.setWritingClient(settings.writing);
    }
    if (settings.image?.apiKey) {
      this.setImageClient(settings.image);
    }
  }

  // 기본 설정 로드 (싱글톤 패턴으로 중복 방지)
  static async loadDefaultSettings(): Promise<void> {
    // 이미 로드되었으면 스킵
    if (this.isLoaded) {
      return;
    }
    
    // 로딩 중이면 대기
    if (this.isLoading) {
      console.log('⏭️ LLM 설정 로딩 중, 대기...');
      return;
    }

    // 로딩 시작
    this.isLoading = true;

    try {
      console.log('🔄 LLM 설정 로드 시작');
      
      // Electron API가 있는지 확인
      if (!(window as any).electronAPI || typeof (window as any).electronAPI.loadSettings !== 'function') {
        console.warn('Electron API를 사용할 수 없어 기본값을 사용합니다.');
        this.loadDefaultSettingsFromLocalStorage();
        this.isLoaded = true;
        this.isLoading = false;
        return;
      }

      // Electron API를 통해 설정 로드
      const savedData = await (window as any).electronAPI.loadSettings();
      console.log('✅ 저장된 LLM 설정 로드됨:', savedData);
      
      if (savedData && savedData.settings) {
        const settings = savedData.settings;
        const testingStatus = savedData.testingStatus || {};
        
        // 설정과 테스트 상태 캐시
        this.cachedSettings = settings;
        this.cachedTestingStatus = testingStatus;
        
        console.log('파싱된 설정:', settings);
        console.log('테스트 상태:', testingStatus);
        
        // API 키가 있는 설정 적용 (테스트 성공 여부 무시하고 일단 적용)
        if (settings.information?.apiKey) {
          console.log('정보요약 AI 설정 로드:', settings.information);
          console.log('정보요약 AI 테스트 상태:', testingStatus.information);
          this.setInformationClient(settings.information);
        } else {
          console.warn('정보요약 AI 설정이 없습니다:', settings.information);
        }
        
        if (settings.writing?.apiKey) {
          console.log('글쓰기 AI 설정 로드:', settings.writing);
          console.log('글쓰기 AI 테스트 상태:', testingStatus.writing);
          this.setWritingClient(settings.writing);
        } else {
          console.warn('글쓰기 AI 설정이 없습니다:', settings.writing);
        }
        
        if (settings.image?.apiKey) {
          console.log('이미지 AI 설정 로드:', settings.image);
          console.log('이미지 AI 테스트 상태:', testingStatus.image);
          this.setImageClient(settings.image);
        } else {
          console.warn('이미지 AI 설정이 없습니다:', settings.image);
        }
        
        console.log('🎉 LLM 설정 로드 완료');
      } else {
        console.log('저장된 설정이 없어 기본값을 사용합니다.');
        this.loadDefaultValues();
      }
      
      // 로딩 완료
      this.isLoaded = true;
      this.isLoading = false;
    } catch (error) {
      console.error('❌ LLM 설정 로드 실패:', error);
      this.loadDefaultValues();
      this.isLoaded = true;
      this.isLoading = false;
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