// 이미지 생성 API 테스트
// 실제 API 키가 필요합니다

async function testOpenAI() {
  console.log('🔵 OpenAI 이미지 API 테스트...');
  
  try {
    const response = await fetch('https://api.openai.com/v1/images/generations', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer YOUR_OPENAI_API_KEY` // 실제 키로 교체 필요
      },
      body: JSON.stringify({
        model: 'gpt-image-1',
        prompt: 'A cute cat sitting on a table',
        quality: 'high',
        size: '1024x1024',
        response_format: 'url'
      })
    });

    console.log('📊 OpenAI 응답 상태:', response.status, response.statusText);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.log('❌ OpenAI 오류 내용:', errorText);
      return;
    }

    const data = await response.json();
    console.log('✅ OpenAI 성공:', data);
    
  } catch (error) {
    console.error('❌ OpenAI 네트워크 오류:', error);
  }
}

async function testGemini() {
  console.log('🟡 Gemini 이미지 API 테스트...');
  
  try {
    const response = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key=YOUR_GEMINI_API_KEY`, // 실제 키로 교체 필요
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          contents: [{
            parts: [{
              text: `Create an image: A cute cat sitting on a table`
            }]
          }],
          generationConfig: {
            temperature: 0.7,
            maxOutputTokens: 8000
          }
        })
      }
    );

    console.log('📊 Gemini 응답 상태:', response.status, response.statusText);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.log('❌ Gemini 오류 내용:', errorText);
      return;
    }

    const data = await response.json();
    console.log('✅ Gemini 성공:', data);
    
  } catch (error) {
    console.error('❌ Gemini 네트워크 오류:', error);
  }
}

async function testRunware() {
  console.log('🟣 Runware 이미지 API 테스트...');
  
  try {
    const taskUUID = 'test-' + Date.now();
    
    const response = await fetch('https://api.runware.ai/v1', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer YOUR_RUNWARE_API_KEY` // 실제 키로 교체 필요
      },
      body: JSON.stringify([
        {
          taskType: 'imageInference',
          taskUUID: taskUUID,
          positivePrompt: 'A cute cat sitting on a table',
          width: 1024,
          height: 1024,
          model: 'civitai:102438@133677',
          numberResults: 1,
          steps: 20,
          CFGScale: 7,
          seed: Math.floor(Math.random() * 1000000)
        }
      ])
    });

    console.log('📊 Runware 응답 상태:', response.status, response.statusText);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.log('❌ Runware 오류 내용:', errorText);
      return;
    }

    const data = await response.json();
    console.log('✅ Runware 성공:', data);
    
  } catch (error) {
    console.error('❌ Runware 네트워크 오류:', error);
  }
}

// 테스트 실행
console.log('🚀 이미지 생성 API 테스트 시작...');
console.log('⚠️ 실제 API 키를 입력해야 정확한 테스트가 가능합니다.');

// 실제 테스트하려면 아래 주석 해제하고 API 키 입력
// testOpenAI();
// testGemini();
// testRunware();