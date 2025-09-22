import { RunwareClient, LLMClientFactory } from './src/services/llm-client-factory';

async function testRunwareImageGeneration() {
  console.log('🖼️ Runware 이미지 생성 테스트 시작...');
  
  try {
    // 테스트용 설정 (실제 API 키 필요)
    const config = {
      provider: 'runware' as const,
      model: 'civitai:102438@133677', // 기본 Stable Diffusion 모델
      apiKey: 'YOUR_RUNWARE_API_KEY_HERE' // 실제 API 키로 교체 필요
    };
    
    // API 키 체크
    if (config.apiKey === 'YOUR_RUNWARE_API_KEY_HERE') {
      console.log('⚠️ API 키를 설정해주세요!');
      console.log('1. Runware 웹사이트 (https://runware.ai)에서 API 키를 발급받으세요');
      console.log('2. 이 파일의 apiKey 값을 실제 키로 교체하세요');
      console.log('3. npx ts-node test-runware-image.ts 로 실행하세요');
      return;
    }
    
    console.log('🔧 Runware 클라이언트 생성 중...');
    
    // 방법 1: 직접 RunwareClient 생성
    console.log('📝 방법 1: 직접 클라이언트 생성');
    const directClient = new RunwareClient(config);
    
    // 방법 2: Factory를 통한 생성 
    console.log('📝 방법 2: Factory를 통한 생성');
    const factoryClient = LLMClientFactory.createClient(config);
    
    console.log('✅ 클라이언트 생성 완료!');
    
    // 테스트 프롬프트들
    const testPrompts = [
      {
        prompt: 'A beautiful sunset over mountains, digital art style',
        description: '기본 풍경 이미지',
        options: { quality: 'high' as const, size: '1024x1024' as const }
      },
      {
        prompt: 'Modern minimalist blog header design, clean and professional',
        description: '블로그 헤더용',
        options: { quality: 'medium' as const, size: '1024x1536' as const }
      },
      {
        prompt: 'Cute cartoon character for blog mascot, friendly smile',
        description: '블로그 마스코트',
        options: { quality: 'low' as const, size: '1536x1024' as const }
      }
    ];
    
    for (let i = 0; i < testPrompts.length; i++) {
      const { prompt, description, options } = testPrompts[i];
      
      try {
        console.log(`\n📝 테스트 ${i + 1}: ${description}`);
        console.log(`프롬프트: "${prompt}"`);
        console.log(`설정: 품질=${options.quality}, 크기=${options.size}`);
        console.log('이미지 생성 중...');
        
        const startTime = Date.now();
        
        // 직접 클라이언트로 테스트
        const imageUrl = await directClient.generateImage(prompt, options);
        const duration = Date.now() - startTime;
        
        console.log(`✅ 생성 성공! (${duration}ms)`);
        console.log(`🖼️ 이미지 URL: ${imageUrl}`);
        
        // URL 유효성 간단 체크
        if (imageUrl.startsWith('http')) {
          console.log('✅ URL 형식이 올바릅니다');
        } else {
          console.log('⚠️ URL 형식이 이상합니다');
        }
        
        // Factory 클라이언트로도 테스트
        console.log('🔄 Factory 클라이언트로 재테스트...');
        const factoryImageUrl = await factoryClient.generateImage(prompt, options);
        console.log(`🏭 Factory 결과: ${factoryImageUrl}`);
        
      } catch (error) {
        console.error(`❌ 테스트 ${i + 1} 실패:`, error);
        
        // 에러 타입별 안내
        if (error instanceof Error) {
          if (error.message.includes('401') || error.message.includes('403')) {
            console.log('💡 API 키를 확인해주세요');
          } else if (error.message.includes('429')) {
            console.log('💡 API 사용량 한도에 도달했습니다');
          } else if (error.message.includes('500')) {
            console.log('💡 Runware 서버 오류입니다');
          } else if (error.message.includes('지원하지 않는')) {
            console.log('💡 RunwareClient가 LLMClientFactory에 제대로 등록되지 않았습니다');
            console.log('   llm-client-factory.ts의 createClient 메서드를 확인해주세요');
          }
        }
      }
      
      // 요청 간 간격 (API 제한 방지)
      if (i < testPrompts.length - 1) {
        console.log('⏱️ 잠시 대기 중... (API 제한 방지)');
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    }
    
  } catch (error) {
    console.error('❌ 전체 테스트 실패:', error);
    
    if (error instanceof Error && error.message.includes('지원하지 않는 API 제공자')) {
      console.log('\n🔍 문제 진단:');
      console.log('1. LLMClientFactory.createClient()에서 "runware" case가 없음');
      console.log('2. llm-client-factory.ts 파일 확인 필요');
      console.log('3. export { RunwareClient } 확인 필요');
    }
  }
  
  console.log('\n🎉 Runware 이미지 생성 테스트 완료!');
  console.log('\n📋 사용법:');
  console.log('1. API 키 발급: https://runware.ai');
  console.log('2. 이 파일의 apiKey 값 수정');
  console.log('3. npx ts-node test-runware-image.ts 실행');
  console.log('4. 또는 npm run start 후 앱에서 이미지 AI 설정 테스트');
}

// 즉시 실행
testRunwareImageGeneration().catch(console.error);