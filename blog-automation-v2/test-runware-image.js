// TypeScript 모듈을 직접 import하는 대신 컴파일된 버전 사용하거나 
// 또는 아래와 같이 동적 import 사용

async function loadRunwareClient() {
  try {
    // ES6 dynamic import를 사용하여 TypeScript 모듈 로드
    const module = await import('./src/services/llm-client-factory.ts');
    return module.RunwareClient;
  } catch (error) {
    console.error('❌ RunwareClient 로드 실패:', error);
    
    // 대체 방법: LLMClientFactory를 통한 접근
    try {
      const factoryModule = await import('./src/services/llm-client-factory.ts');
      const { LLMClientFactory } = factoryModule;
      
      // Runware 클라이언트 생성
      const config = {
        provider: 'runware',
        model: 'civitai:102438@133677',
        apiKey: 'test-key'
      };
      
      return LLMClientFactory.createClient(config);
    } catch (factoryError) {
      console.error('❌ LLMClientFactory 로드도 실패:', factoryError);
      throw new Error('RunwareClient를 로드할 수 없습니다');
    }
  }
}

async function testRunwareImageGeneration() {
  console.log('🖼️ Runware 이미지 생성 테스트 시작...');
  
  try {
    // RunwareClient 로드
    console.log('📦 RunwareClient 로드 중...');
    const RunwareClientClass = await loadRunwareClient();
    
    // 테스트용 설정 (실제 API 키 필요)
    const config = {
      provider: 'runware',
      model: 'civitai:102438@133677', // 기본 Stable Diffusion 모델
      apiKey: 'YOUR_RUNWARE_API_KEY_HERE' // 실제 API 키로 교체 필요
    };
    
    // API 키 체크
    if (config.apiKey === 'YOUR_RUNWARE_API_KEY_HERE') {
      console.log('⚠️ API 키를 설정해주세요!');
      console.log('1. Runware 웹사이트에서 API 키를 발급받으세요');
      console.log('2. 이 파일의 apiKey 값을 실제 키로 교체하세요');
      return;
    }
    
    console.log('🔧 Runware 클라이언트 생성 중...');
    const client = new RunwareClientClass(config);
    console.log('✅ 클라이언트 생성 완료!');
  
  // 테스트 프롬프트들
  const testPrompts = [
    {
      prompt: 'A beautiful sunset over mountains, digital art style',
      description: '기본 풍경 이미지'
    },
    {
      prompt: 'Modern minimalist blog header design, clean and professional',
      description: '블로그 헤더용'
    },
    {
      prompt: 'Cute cartoon character for blog mascot, friendly smile',
      description: '블로그 마스코트'
    }
  ];
  
  for (let i = 0; i < testPrompts.length; i++) {
    const { prompt, description } = testPrompts[i];
    
    try {
      console.log(`\n📝 테스트 ${i + 1}: ${description}`);
      console.log(`프롬프트: "${prompt}"`);
      console.log('이미지 생성 중...');
      
      const startTime = Date.now();
      
      // 다양한 옵션으로 테스트
      const options = {
        quality: i === 0 ? 'high' : i === 1 ? 'medium' : 'low',
        size: '1024x1024'
      };
      
      console.log(`설정: 품질=${options.quality}, 크기=${options.size}`);
      
      const imageUrl = await client.generateImage(prompt, options);
      const duration = Date.now() - startTime;
      
      console.log(`✅ 생성 성공! (${duration}ms)`);
      console.log(`🖼️ 이미지 URL: ${imageUrl}`);
      console.log(`📏 예상 크기: ${options.size}`);
      console.log(`🎨 품질: ${options.quality}`);
      
      // URL 유효성 간단 체크
      if (imageUrl.startsWith('http')) {
        console.log('✅ URL 형식이 올바릅니다');
      } else {
        console.log('⚠️ URL 형식이 이상합니다');
      }
      
    } catch (error) {
      console.error(`❌ 테스트 ${i + 1} 실패:`, error.message);
      
      // 에러 타입별 안내
      if (error.message.includes('401') || error.message.includes('403')) {
        console.log('💡 API 키를 확인해주세요');
      } else if (error.message.includes('429')) {
        console.log('💡 API 사용량 한도에 도달했습니다');
      } else if (error.message.includes('500')) {
        console.log('💡 Runware 서버 오류입니다');
      }
    }
    
    // 요청 간 간격 (API 제한 방지)
    if (i < testPrompts.length - 1) {
      console.log('⏱️ 잠시 대기 중... (API 제한 방지)');
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }
  
  console.log('\n🎉 Runware 이미지 생성 테스트 완료!');
  console.log('\n📋 사용법:');
  console.log('1. API 키 발급: https://runware.ai');
  console.log('2. 이 파일의 apiKey 값 수정');
  console.log('3. node test-runware-image.js 실행');
}

// 즉시 실행
testRunwareImageGeneration().catch(console.error);