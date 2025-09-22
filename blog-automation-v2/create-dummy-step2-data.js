// Step2에서 바로 사용할 수 있는 더미 데이터 생성
// 이 파일을 실행하면 localStorage에 완전한 데이터가 저장됩니다

const dummyData = {
  // Step1 데이터
  platform: 'naver',
  keyword: '홈트레이닝',
  subKeywords: ['집에서운동', '근력운동', '유산소운동', '요가', '필라테스'],
  contentType: 'health_fitness',
  reviewType: 'experience',
  tone: 'friendly',
  customPrompt: '',
  blogDescription: '건강한 라이프스타일을 위한 홈트레이닝 정보를 공유하는 블로그입니다.',
  bloggerIdentity: '3년차 홈트레이닝 애호가',
  selectedTitle: '홈트레이닝 초보자를 위한 완벽 가이드 - 집에서 시작하는 건강한 운동',
  generatedTitles: [
    '홈트레이닝 초보자를 위한 완벽 가이드 - 집에서 시작하는 건강한 운동',
    '집에서 하는 효과적인 홈트레이닝 루틴 10가지',
    '헬스장 없이도 가능한 홈트레이닝 완전정복',
    '홈트레이닝으로 만드는 완벽한 몸매 - 3개월 후기'
  ],
  titlesWithSearch: [
    { title: '홈트레이닝 초보자를 위한 완벽 가이드 - 집에서 시작하는 건강한 운동', searchQuery: '홈트레이닝 초보자 가이드' },
    { title: '집에서 하는 효과적인 홈트레이닝 루틴 10가지', searchQuery: '홈트레이닝 루틴' },
    { title: '헬스장 없이도 가능한 홈트레이닝 완전정복', searchQuery: '홈트레이닝 운동법' },
    { title: '홈트레이닝으로 만드는 완벽한 몸매 - 3개월 후기', searchQuery: '홈트레이닝 후기' }
  ],
  searchKeyword: '홈트레이닝 초보자 가이드',
  
  // Step2 수집된 데이터
  collectedData: {
    success: true,
    blogData: [
      {
        rank: 1,
        title: "홈트레이닝 시작하기 - 운동 초보자를 위한 가이드",
        url: "https://blog.naver.com/example1",
        platform: "네이버",
        summary: "집에서 운동을 시작하는 초보자를 위한 기본적인 가이드를 제공합니다. 준비운동부터 본운동까지 체계적으로 설명합니다.",
        keyPoints: ["준비운동의 중요성", "기본 동작 익히기", "운동 강도 조절", "꾸준함의 중요성"]
      },
      {
        rank: 2,
        title: "집에서 하는 전신 운동 루틴 추천",
        url: "https://blog.naver.com/example2",
        platform: "네이버",
        summary: "집에서 할 수 있는 효과적인 전신 운동 루틴을 소개합니다. 도구 없이도 가능한 운동들로 구성되어 있습니다.",
        keyPoints: ["전신 운동의 장점", "맨몸 운동 방법", "운동 순서", "휴식의 중요성"]
      },
      {
        rank: 3,
        title: "홈트레이닝 3개월 후기 및 변화 과정",
        url: "https://blog.naver.com/example3",
        platform: "네이버",
        summary: "홈트레이닝을 3개월간 실시한 후기와 몸의 변화 과정을 솔직하게 공유합니다.",
        keyPoints: ["꾸준한 운동의 효과", "몸의 변화 과정", "어려웠던 점들", "동기부여 방법"]
      }
    ],
    youtubeData: [
      {
        videoId: "ABC123",
        title: "홈트레이닝 완전 초보 가이드 | 집에서 시작하는 운동",
        channelName: "헬스트레이너 김코치",
        viewCount: 250000,
        duration: 1200,
        priority: 95,
        summary: "홈트레이닝을 처음 시작하는 사람들을 위한 기본 운동법과 주의사항을 설명합니다. 스쿼트, 푸시업, 플랭크 등 기본 동작들을 자세히 보여줍니다."
      },
      {
        videoId: "DEF456",
        title: "20분 홈트레이닝 루틴 | 전신 운동 따라하기",
        channelName: "홈트운동TV",
        viewCount: 180000,
        duration: 1200,
        priority: 88,
        summary: "20분 동안 할 수 있는 효과적인 전신 운동 루틴을 제공합니다. 워밍업부터 쿨다운까지 체계적으로 구성되어 있습니다."
      }
    ],
    blogAnalysisResult: {
      summary: "홈트레이닝 관련 블로그들을 분석한 결과, 초보자들이 가장 관심있어 하는 주제는 '시작하는 방법', '기본 동작', '꾸준히 하는 방법'입니다.",
      commonThemes: ["기본 동작 익히기", "꾸준함의 중요성", "올바른 자세", "점진적 강도 증가"],
      keyInsights: ["준비운동과 마무리 운동이 중요", "무리하지 않고 천천히 시작", "정확한 자세가 효과를 좌우", "개인 체력에 맞는 강도 조절"]
    },
    youtubeAnalysisResult: {
      video_summaries: [
        {
          video_number: 1,
          key_points: "홈트레이닝 기본 동작 설명, 올바른 자세의 중요성, 초보자 주의사항"
        },
        {
          video_number: 2,
          key_points: "20분 전신 운동 루틴, 워밍업과 쿨다운, 운동 강도 조절"
        }
      ],
      common_themes: ["기본 동작", "올바른 자세", "점진적 강도 증가", "꾸준함"],
      practical_tips: ["하루 20-30분씩 꾸준히", "정확한 자세 우선", "무리하지 말고 점진적으로", "준비운동 필수"]
    }
  },

  // Step2 글쓰기 결과
  writingResult: {
    success: true,
    content: `# 홈트레이닝 초보자를 위한 완벽 가이드 - 집에서 시작하는 건강한 운동

안녕하세요! 3년차 홈트레이닝 애호가입니다. 😊

오늘은 홈트레이닝을 처음 시작하는 분들을 위한 완벽한 가이드를 준비했어요. 헬스장에 가지 않고도 집에서 충분히 건강한 몸을 만들 수 있다는 걸 직접 경험했기 때문에, 여러분들께 그 노하우를 공유하고 싶어요!

## 🏃‍♀️ 홈트레이닝이 왜 좋을까요?

**편리함이 최고!**
- 언제든지 원하는 시간에 운동 가능
- 헬스장 월 회비 부담 없음
- 다른 사람들 시선 신경 쓸 필요 없음
- 코로나19 같은 상황에도 안전하게 운동

[이미지] 집에서 운동하는 모습

## 💪 홈트레이닝 시작하기 전 준비사항

### 1. 운동 공간 확보
최소 2m x 2m 정도의 공간만 있으면 충분해요. 거실이나 방 한 켠을 활용해보세요!

### 2. 기본 준비물
- **요가매트**: 바닥 운동 시 필수
- **수건**: 땀 닦기용
- **물병**: 수분 보충용
- **편한 운동복**: 움직임이 자유로운 옷

[이미지] 홈트레이닝 준비물들

### 3. 마음가짐
가장 중요한 건 **꾸준함**이에요! 하루에 20분씩이라도 매일 하는 게 일주일에 한 번 2시간 하는 것보다 훨씬 효과적이에요.

## 🔥 초보자를 위한 기본 운동 루틴

### 워밍업 (5분)
1. **제자리 걷기** - 2분
2. **팔 돌리기** - 1분
3. **어깨 스트레칭** - 2분

[이미지] 워밍업 동작들

### 본 운동 (15분)
#### 1. 스쿼트 (3세트 x 10회)
**올바른 자세:**
- 발을 어깨너비로 벌리기
- 무릎이 발끝을 넘지 않게 주의
- 엉덩이를 뒤로 빼면서 앉기

> 💡 **초보자 팁**: 처음에는 의자에 앉았다 일어나는 동작으로 연습해보세요!

#### 2. 푸시업 (3세트 x 5-10회)
**단계별 접근:**
- 1단계: 벽 푸시업
- 2단계: 무릎 푸시업
- 3단계: 일반 푸시업

[이미지] 푸시업 단계별 동작

#### 3. 플랭크 (3세트 x 30초)
**핵심 포인트:**
- 몸이 일직선이 되도록 유지
- 엉덩이가 너무 올라가거나 내려가지 않게 주의
- 호흡은 자연스럽게

### 쿨다운 (5분)
1. **전신 스트레칭** - 3분
2. **심호흡** - 2분

[이미지] 쿨다운 스트레칭

## 📅 주간 운동 계획표

| 요일 | 운동 내용 | 시간 |
|------|-----------|------|
| 월 | 전신 운동 | 25분 |
| 화 | 상체 집중 | 20분 |
| 수 | 유산소 운동 | 30분 |
| 목 | 하체 집중 | 20분 |
| 금 | 전신 운동 | 25분 |
| 토 | 요가/스트레칭 | 15분 |
| 일 | 휴식 | - |

## ⚠️ 초보자가 주의해야 할 점들

### 1. 무리하지 마세요!
처음부터 과도한 운동은 부상의 원인이 돼요. 본인의 체력에 맞게 강도를 조절하세요.

### 2. 올바른 자세가 최우선
잘못된 자세로 100번 하는 것보다 올바른 자세로 10번 하는 게 훨씬 효과적이에요.

### 3. 꾸준함이 핵심
일주일에 3-4번은 꼭 운동하려고 노력해보세요. 습관이 되면 자연스럽게 몸이 움직여요!

[이미지] 꾸준한 운동의 중요성을 보여주는 이미지

## 🎯 3개월 후 기대할 수 있는 변화

**1개월 차:**
- 기초 체력 향상
- 운동 습관 형성
- 몸의 유연성 개선

**2개월 차:**
- 근력 향상 체감
- 체중 감량 효과
- 자신감 증가

**3개월 차:**
- 눈에 띄는 몸의 변화
- 일상생활 활력 증가
- 더 도전적인 운동 가능

## 💬 마무리하며

홈트레이닝은 정말 누구나 할 수 있는 운동이에요! 저도 처음엔 스쿼트 10개도 힘들었는데, 지금은 100개도 거뜬하답니다. 💪

가장 중요한 건 **시작하는 것**이에요. 완벽할 필요 없어요. 오늘 당장 운동복으로 갈아입고 스쿼트 5개부터 시작해보세요!

여러분도 건강한 홈트레이닝 라이프를 시작하시길 응원합니다! 궁금한 점이 있으면 언제든지 댓글로 물어보세요~ 😊

**태그:** #홈트레이닝 #집에서운동 #초보자운동 #건강관리 #다이어트`,

    imagePrompts: [
      {
        index: 1,
        position: "홈트레이닝 소개 섹션",
        context: "집에서 편안하게 운동하는 모습을 보여주는 이미지",
        prompt: "A person doing home workout in a clean, modern living room, wearing comfortable exercise clothes, natural lighting from windows, motivational and welcoming atmosphere"
      },
      {
        index: 2,
        position: "준비물 섹션",
        context: "홈트레이닝에 필요한 기본 준비물들",
        prompt: "Home workout equipment laid out neatly on wooden floor: yoga mat, water bottle, towel, dumbbells, exercise clothes, clean and organized setup"
      },
      {
        index: 3,
        position: "워밍업 섹션",
        context: "워밍업 동작들을 보여주는 이미지",
        prompt: "Person doing warm-up exercises at home: arm circles, stretching, light movements, bright room with natural lighting, energetic mood"
      },
      {
        index: 4,
        position: "푸시업 설명 섹션",
        context: "푸시업의 단계별 동작",
        prompt: "Step-by-step push-up progression: wall push-up, knee push-up, regular push-up, demonstration of proper form, educational style"
      },
      {
        index: 5,
        position: "쿨다운 섹션",
        context: "운동 후 스트레칭하는 모습",
        prompt: "Person doing cool-down stretches on yoga mat, relaxed atmosphere, soft lighting, peaceful and calming mood, post-workout relaxation"
      },
      {
        index: 6,
        position: "주의사항 섹션",
        context: "꾸준한 운동의 중요성",
        prompt: "Motivational concept image showing consistency in exercise: calendar with workout marks, progress chart, positive mindset visualization"
      }
    ],
    
    usage: {
      promptTokens: 2500,
      completionTokens: 1800,
      totalTokens: 4300
    }
  },

  generatedContent: `# 홈트레이닝 초보자를 위한 완벽 가이드 - 집에서 시작하는 건강한 운동

안녕하세요! 3년차 홈트레이닝 애호가입니다. 😊

오늘은 홈트레이닝을 처음 시작하는 분들을 위한 완벽한 가이드를 준비했어요...` // 위의 content와 동일
};

// 브라우저 콘솔에서 실행할 함수
function saveDummyData() {
  try {
    // WorkflowData 저장
    localStorage.setItem('workflow-data', JSON.stringify(dummyData));
    
    console.log('✅ 더미 데이터가 성공적으로 저장되었습니다!');
    console.log('📋 저장된 데이터:');
    console.log('- Step1 기본 설정 완료');
    console.log('- Step2 분석 결과 완료');
    console.log('- Step2 글쓰기 결과 완료');
    console.log('- 이미지 프롬프트 6개 생성 완료');
    console.log('');
    console.log('🚀 이제 애플리케이션을 새로고침하고 Step3으로 직접 이동할 수 있습니다!');
    
    // 저장된 데이터 확인
    const saved = localStorage.getItem('workflow-data');
    if (saved) {
      const parsed = JSON.parse(saved);
      console.log('');
      console.log('🔍 저장 확인:');
      console.log('- 선택된 제목:', parsed.selectedTitle);
      console.log('- 수집된 블로그 수:', parsed.collectedData?.blogData?.length || 0);
      console.log('- 수집된 유튜브 수:', parsed.collectedData?.youtubeData?.length || 0);
      console.log('- 글쓰기 성공:', parsed.writingResult?.success || false);
      console.log('- 이미지 프롬프트 수:', parsed.writingResult?.imagePrompts?.length || 0);
    }
    
  } catch (error) {
    console.error('❌ 데이터 저장 실패:', error);
  }
}

// 더미 데이터 삭제 함수
function clearDummyData() {
  try {
    localStorage.removeItem('workflow-data');
    console.log('🗑️ 더미 데이터가 삭제되었습니다.');
    console.log('🔄 페이지를 새로고침하면 Step1부터 다시 시작됩니다.');
  } catch (error) {
    console.error('❌ 데이터 삭제 실패:', error);
  }
}

// 브라우저에서 바로 실행
if (typeof window !== 'undefined' && window.localStorage) {
  saveDummyData();
} else {
  console.log('📌 이 스크립트는 브라우저 콘솔에서 실행해주세요!');
  console.log('');
  console.log('🔧 사용 방법:');
  console.log('1. 애플리케이션 실행');
  console.log('2. F12를 눌러 개발자 도구 열기');
  console.log('3. Console 탭으로 이동');
  console.log('4. 이 파일의 전체 내용을 복사해서 붙여넣기');
  console.log('5. Enter 키를 눌러 실행');
  console.log('');
  console.log('💡 유용한 함수들:');
  console.log('- saveDummyData(): 더미 데이터 저장');
  console.log('- clearDummyData(): 더미 데이터 삭제');
}