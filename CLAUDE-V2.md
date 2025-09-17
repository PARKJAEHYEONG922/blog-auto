# CLAUDE-V2.md — 차세대 AI 블로그 자동화 시스템 개발 계획

> **목표**: Electron + MCP + 멀티 LLM을 활용한 지능형 블로그 자동화 시스템 구축  
> **핵심 혁신**: 사용자가 LLM을 용도별로 선택하고, AI가 스스로 크롤링→글쓰기→이미지생성→업로드까지 완전 자동화

---

## 🚀 프로젝트 개요

### 기존 시스템 (legacy-pyside-version/) vs 새 시스템
| 구분 | 기존 (PySide) | 새 시스템 (Electron + MCP) |
|------|---------------|---------------------------|
| **플랫폼** | Python + Qt | JavaScript + Electron |
| **AI 통합** | 고정된 API 호출 | 지능형 MCP 도구 조합 |
| **크롤링** | 하드코딩된 Selenium | LLM이 상황별 판단 |
| **이미지** | 지원 안함 | 자동 이미지 생성/삽입 |
| **확장성** | 제한적 | 무한 확장 가능 |

---

## 🎯 핵심 기능

### 1) 3단계 지능형 워크플로우 (기존 구조 발전)
```
📝 Step 1: 키워드 입력 + 설정 → AI 제목 추천
🔍 Step 2: 제목 선택 → 경쟁사 스마트 분석  
✍️ Step 3: 분석 기반 → 완벽한 글+이미지 생성+업로드
```

### 2) Step 1: 콘텐츠 기획 단계
- **플랫폼 선택**: 네이버 블로그 / 티스토리 / 블로그스팟(구글) / 워드프레스 (SEO 전략 결정)
- **키워드 시스템**: 메인키워드 (필수) + 보조키워드 (선택)
- **콘텐츠 타입**: 정보형 / 후기형 / 비교형 / 노하우형
- **말투 선택**: 정중한 존댓말 / 친근한 반말 / 친근한 존댓말
- **커스텀 프롬프트**: 사용자 추가 요청사항 입력 가능
- **AI 제목 추천**: 듀얼 모드 시스템
  - **⚡ 빠른 모드**: LLM 직접 생성 (5초 이내)
  - **🎯 정확 모드**: 실시간 트렌드 분석 → LLM 생성 (30초)

### 3) Step 2: 지능형 데이터 수집 및 분석
- **스마트 키워드 추출**: LLM이 선택된 제목에서 사용자 검색 의도에 맞는 핵심 키워드 자동 추출
- **멀티 플랫폼 크롤링**: 네이버 블로그/뉴스/쇼핑, 유튜브, 구글 검색, 플랫폼별 상위 콘텐츠 수집
- **네이버 쇼핑 분석**: 상품 정보, 리뷰, 가격 비교 데이터 수집 (리뷰글/비교글 필수)
- **플랫폼별 맞춤 분석**: 선택된 발행 플랫폼의 상위 노출 콘텐츠 패턴 분석
- **평균 이미지 개수 분석**: 상위 노출 글들의 이미지 개수 패턴 파악하여 최적 개수 도출
- **AI 필터링**: 관련도 높고 도움되는 정보만 지능적 선별
- **실시간 진행**: 수집→분석→정제 과정 단계별 실시간 표시

### 4) Step 3: 플랫폼 맞춤 콘텐츠 생성 및 발행
- **맞춤 LLM 선택**: 용도별 최적 AI 모델 사용자 선택
- **플랫폼별 SEO 최적화 글쓰기**: 네이버/구글/티스토리/워드프레스 각 플랫폼 특성에 맞는 최적화된 글 생성
- **스마트 이미지 생성**: 분석된 평균 이미지 개수에 맞춰 글 내용 최적화된 이미지 자동 생성
- **멀티 플랫폼 자동 발행**: 네이버 블로그/티스토리/블로그스팟/워드프레스 중 선택한 플랫폼에 자동 업로드
- **통합 미리보기**: 플랫폼별 최종 결과물 미리보기 및 수정 가능

### 5) 사용자 맞춤 LLM 선택 시스템 (3가지 선택)
```
🔍 정보처리 LLM (키워드→제목→정보수집→요약)
- Gemini 2.0 Flash (무료/빠름 ⭐ 추천) / Gemini 2.5 Flash-Lite (무료/초고속) / GPT-5 Nano (초저렴/초고속) / Claude 3.5 Haiku (빠름/정확)

✍️ 글쓰기 LLM (최종 콘텐츠 생성 - 가장 중요!)  
- Claude Sonnet 4 (최고품질/가성비 ⭐ 추천) / GPT-5 (최신/강력) / Gemini 2.5 Pro (추론능력)

🎨 이미지 생성 LLM
- Gemini 2.5 Flash Image (최신/다기능) / DALL-E 3 (안정성) / GPT-Image-1 (정확성)
```

**역할 분담:**
- **정보처리 LLM**: Step 1 제목추천 + Step 2 데이터수집/분석/요약 (빠르고 저렴하게)
- **글쓰기 LLM**: Step 3 최종 글쓰기 (성능 최우선 - 가장 비싼 모델 사용)
- **이미지 생성 LLM**: 글 내용 기반 이미지 생성

---

## 🛠️ 기술 스택

### Frontend (사용자 인터페이스)
```bash
Electron                    # 데스크톱 앱 프레임워크
React                       # UI 컴포넌트
Tailwind CSS               # 스타일링
React Query                # 상태 관리
```

### Backend (AI 엔진)
```bash
# 꼭 필요한 MCP 서버들 (6개) - 공식 인증 + 검증됨 ✅
@modelcontextprotocol/server-puppeteer     # 공식 브라우저 자동화 (Step 3) 🎭
@anaisbetts/mcp-youtube                    # YouTube 서브타이틀/요약 (MIT 라이센스) 📺
naver-search-mcp                           # 네이버 전문 (DataLab+트렌드분석) 🇰🇷 ⭐
kimcp                                      # 한국 통합 (네이버/카카오/Daum/TMAP) 🇰🇷
crawl4ai-mcp-server                        # 공식 등재 웹크롤링 (무료/검증됨) 🕷️
@modelcontextprotocol/server-filesystem   # 공식 파일 관리 (다운로드/업로드) 📁

# LLM 클라이언트들 (직접 연결 - 빠르고 안정적)
openai                     # GPT-5, GPT-5 Mini/Nano, DALL-E
@anthropic-ai/sdk         # Claude Sonnet 4, Haiku
@google/generative-ai     # Gemini 2.0 Flash, 2.5 Pro/Flash/Flash-Lite, Flash Image
```

**MCP 사용 원칙 (공식 인증 + 검증된 서버들):**
- **Step 1**: 선택적 MCP 사용 (트렌드 기반 제목 생성)
  - **기본 모드**: LLM 직접 제목 생성 (빠름)
  - **고급 모드**: Naver DataLab + YouTube 트렌드 → LLM 제목 생성 (정확함)
- **Step 2**: 웹 크롤링/검색 전용 MCP (공식 등재)
  - **YouTube MCP**: 유튜브 영상 분석/요약 (트렌드 파악 필수) 📺
  - **Crawl4AI**: 공식 디렉토리 등재 웹크롤링 (구글 검색 대응) 🕷️
  - **Naver Search MCP**: 네이버 전문 (11개 검색 + DataLab 트렌드분석) ⭐
  - **KiMCP**: 한국 통합 (네이버/카카오/Daum/TMAP 다중 플랫폼)
- **Step 3**: 브라우저 자동화 전용 MCP
  - **Puppeteer MCP**: Anthropic 공식 브라우저 자동화 🎭
- **파일 관리**: 공식 파일시스템 MCP (이미지 처리) 📁
- **LLM**: 모두 직접 연결 (속도/안정성)

### 개발/배포
```bash
Vite                      # 빌드 도구
Electron Builder          # 앱 패키징
GitHub Actions           # CI/CD
```

---

## 📁 프로젝트 구조

```
blog-automation-v2/
├─ electron/                          # Electron 메인 프로세스
│  ├─ main.js                         # 앱 진입점
│  ├─ preload.js                      # 렌더러-메인 브릿지
│  └─ mcp-manager.js                  # MCP 서버 관리
│
├─ src/                               # React 프론트엔드
│  ├─ components/                     # 공용 컴포넌트
│  │  ├─ LLMSettings.tsx              # LLM 선택 설정
│  │  ├─ CostTracker.tsx              # 비용 추적기
│  │  ├─ ProgressMonitor.tsx          # 실시간 진행 상황
│  │  ├─ PlatformSelector.tsx         # 블로그 플랫폼 선택
│  │  ├─ TitleRefresh.tsx             # 제목 새로고침 컴포넌트
│  │  └─ common/                      # 공통 UI 컴포넌트
│  │     ├─ ModernButton.tsx
│  │     ├─ ModernInput.tsx
│  │     └─ ModernCard.tsx
│  │
│  ├─ pages/                          # 3단계 페이지 컴포넌트
│  │  ├─ Step1.tsx                    # 플랫폼 선택 + 키워드 입력 + 제목 추천
│  │  ├─ Step2.tsx                    # 제목 선택 + 멀티플랫폼 데이터 수집/분석
│  │  ├─ Step3.tsx                    # 플랫폼 맞춤 콘텐츠 생성 + 자동 발행
│  │  ├─ Dashboard.tsx                # 메인 대시보드
│  │  ├─ Settings.tsx                 # API 키 & LLM 설정
│  │  └─ Analytics.tsx                # 성과 분석
│  │
│  ├─ services/                       # 비즈니스 로직 (3단계 엔진)
│  │  ├─ llm-client-factory.ts        # LLM 클라이언트 팩토리
│  │  ├─ platform-selector.ts         # 블로그 플랫폼 관리 서비스
│  │  ├─ title-generation-engine.ts   # Step 1: 제목 생성 엔진 (새로고침 포함)
│  │  ├─ multi-platform-crawler.ts    # Step 2: 멀티플랫폼 크롤링 엔진
│  │  ├─ seo-optimizer.ts             # 플랫폼별 SEO 최적화 엔진
│  │  ├─ image-analyzer.ts            # 이미지 개수 분석 엔진
│  │  ├─ content-generation-engine.ts # Step 3: 플랫폼 맞춤 콘텐츠 생성 엔진
│  │  ├─ auto-publisher.ts            # 멀티플랫폼 자동 발행 엔진
│  │  ├─ cost-calculator.ts           # 비용 계산기
│  │  └─ settings-manager.ts          # 설정 관리
│  │
│  ├─ types/                          # TypeScript 타입 정의
│  │  ├─ llm-types.ts                 # LLM 관련 타입
│  │  ├─ platform-types.ts            # 블로그 플랫폼 관련 타입
│  │  ├─ content-types.ts             # 콘텐츠/SEO 관련 타입
│  │  └─ ui-types.ts                  # UI 관련 타입
│  │
│  ├─ hooks/                          # React 커스텀 훅
│  │  ├─ useLLMClient.ts              # LLM 클라이언트 훅
│  │  ├─ usePlatformSelector.ts       # 플랫폼 선택 훅
│  │  ├─ useMultiPlatformCrawler.ts   # 멀티플랫폼 크롤링 훅
│  │  ├─ useBlogGeneration.ts         # 블로그 생성 훅
│  │  ├─ useAutoPublisher.ts          # 자동 발행 훅
│  │  └─ useCostTracking.ts           # 비용 추적 훅
│
├─ mcp-servers/                       # MCP 서버 설정 (총 6개 필수)
│  ├─ config.json                     # MCP 서버 설정
│  ├─ playwright-automation/          # 브라우저 자동화 (Step 3)
│  │  ├─ naver-blog-publisher.js      # 네이버 블로그 자동 발행
│  │  ├─ tistory-publisher.js         # 티스토리 자동 발행  
│  │  ├─ blogspot-publisher.js        # 블로그스팟 자동 발행
│  │  └─ wordpress-publisher.js       # 워드프레스 자동 발행
│  ├─ data-collection/                # 데이터 수집 (Step 2) - 완전 무료 🆓
│  │  ├─ crawl4ai-mcp.js              # 오픈소스 웹크롤링 (구글/유튜브) - 무료/무제한
│  │  ├─ naver-search-mcp.js          # 네이버 전용 (블로그/뉴스/쇼핑/DataLab) 🇰🇷
│  │  ├─ kimcp.js                     # 한국 API 통합 (네이버/카카오) 🇰🇷
│  │  ├─ web-search-mcp.js            # 기본 웹검색 - 무료
│  │  └─ image-count-analyzer.js      # 이미지 개수 분석
│  └─ start-servers.js                # 필요한 MCP만 시작
│
├─ assets/                            # 정적 리소스
├─ build/                             # 빌드 결과물
└─ package.json                       # 의존성 관리
```

---

## 🗓️ 개발 로드맵

### 🚀 Phase 1: MCP 기반 인프라 구축 (1주) - 핵심 가치 구현
- [x] ~~기존 PySide 코드 legacy 폴더로 이동~~
- [ ] Electron + React 기본 앱 생성 ✅ **확실**
- [ ] MCP 클라이언트 연결 시스템 구축 ⚠️ **복잡하지만 핵심**
- [ ] 기본 MCP 서버 1-2개 연동 테스트 ⚠️ **학습 필요**
- [ ] Step 1 구현: LLM이 MCP 도구 활용한 제목 추천 🎯 **MCP 가치**

**목표**: MCP 기반으로 LLM이 스스로 도구를 선택해서 제목 추천

### 🔍 Phase 2: MCP 서버 확장 구현 (2주) - 핵심 가치 극대화
- [ ] 네이버 Search MCP 연동 (포크 후 커스터마이징) 🎯 **MCP 가치**
- [ ] YouTube MCP 연동 및 테스트 🎯 **MCP 가치**
- [ ] LLM이 상황별 MCP 도구 자동 선택 시스템 🎯 **핵심 혁신**
- [ ] 크롤링 결과를 LLM이 자동 분석/정제 🎯 **지능형**
- [ ] MCP 도구 체인 동작 (도구1 → 도구2 → 종합분석) 🎯 **MCP만의 장점**

**목표**: LLM이 필요에 따라 MCP 도구들을 조합해서 최적 정보 수집

### 🎨 Phase 3: 현실적 콘텐츠 생성 (1주)  
- [ ] 기본 글쓰기 (플랫폼별 템플릿 활용) ✅ **확실**
- [ ] DALL-E 직접 연동 (MCP 없이) ✅ **확실**
- [ ] 이미지 로컬 저장 및 관리 ✅ **가능**
- [ ] 콘텐츠 미리보기 시스템 ✅ **확실**
- [ ] 반자동 발행 (사용자 확인 후 업로드) ✅ **현실적**

**목표**: 기본 글+이미지 생성 → 사용자 검토 → 반자동 발행

### 🤖 Phase 4: 멀티플랫폼 완전 자동화 통합 (1주)
- [ ] 네이버 블로그/티스토리/블로그스팟/워드프레스 자동 로그인/업로드
- [ ] 3단계 워크플로우 완전 연결 및 플랫폼별 최적화
- [ ] 실시간 진행 상황 표시 시스템
- [ ] 플랫폼별 에러 처리 및 재시도 메커니즘
- [ ] 통합 성공/실패 리포팅 시스템

**목표**: 키워드 입력 → 3단계 완전 자동 실행 → 선택한 플랫폼에 최적화된 글 발행

### 📊 Phase 5: 고급 기능 & 최적화 (1주)
- [ ] 사용자 맞춤 LLM 선택 시스템 완성
- [ ] 실시간 비용 추적 및 최적화
- [ ] 배치 처리 (여러 글 동시 생성)
- [ ] 성과 분석 대시보드

**목표**: 프로 블로거 수준의 완전 자동화 시스템

---

## 💰 비용 최적화 전략

### 3단계 워크플로우별 최적화 프리셋

```javascript
// 무료 조합 (월 0원)
free: {
  info_llm: "gemini-2.0-flash-free",      // 정보처리 (제목추천+수집+요약) ⭐ 빠르고 안정적
  writing_llm: "gemini-2.5-flash-free",   // 글쓰기 (무료 최고모델)
  image_llm: "stable-diffusion-free"      // 이미지 생성 (무료/로컬)
}

// 경제형 조합 (월 5천원)  
budget: {
  info_llm: "gpt-5-nano",                 // 정보처리 (초저렴 $0.05/1M)
  writing_llm: "gpt-5-mini",              // 글쓰기 (저렴 $0.25/1M)
  image_llm: "dalle-3"                    // 이미지 생성 (안정성)
}

// 프리미엄 조합 (월 2만원)
premium: {
  info_llm: "claude-3.5-haiku",           // 정보처리 (빠름/정확)
  writing_llm: "claude-sonnet-4",         // 글쓰기 (최고품질/가성비)
  image_llm: "gemini-2.5-flash-image"     // 이미지 생성 (최신/다기능)
}
```

### 실시간 비용 모니터링
- 토큰 사용량 실시간 추적
- 월 예산 설정 및 알림
- 모델별 성능/비용 분석
- 자동 절약 모드 (예산 초과시 저렴한 모델로 자동 전환)

---

## 🔒 보안 및 안정성

### API 키 관리
- 로컬 암호화 저장 (electron-store)
- 환경변수 분리
- API 키 유효성 자동 검증

### 에러 처리
- MCP 서버 장애시 자동 재시작
- LLM API 장애시 폴백 모델 자동 전환
- 네트워크 오류 자동 재시도

### 사용자 데이터 보호
- 생성된 콘텐츠 로컬 저장
- 개인정보 수집 최소화
- GDPR 준수

---

## 🎯 성공 지표

### 사용자 경험
- **설치 후 5분 내 첫 블로그 글 생성** 가능
- **자연어 요청으로 복잡한 작업** 처리
- **월 100편 블로그 글을 1만원 이하 비용**으로 생성

### 기술적 목표  
- **99% 업타임** (MCP 서버 안정성)
- **평균 응답시간 30초 이내** (글 생성 완료)
- **95% 사용자 만족도** (생성된 글 품질)

---

## 🔄 기존 시스템 마이그레이션

### legacy-pyside-version/ 활용
- 기존 네이버 API 클라이언트 로직 참고
- 검증된 크롤링 패턴 재사용
- 사용자 설정/데이터 마이그레이션 도구 제공

### 점진적 전환
1. **Phase 1**: 새 시스템으로 기본 기능 구현
2. **Phase 2**: 기존 사용자 설정 자동 마이그레이션  
3. **Phase 3**: 기존 시스템 단계적 폐기

---

## 🌟 차별화 포인트

### 1) 지능형 자동화
- **기존**: 정해진 템플릿으로만 글 생성
- **신규**: AI가 상황별로 최적 전략 수립

### 2) 사용자 맞춤화
- **기존**: 일률적 AI 사용
- **신규**: 예산/품질 요구사항별 LLM 조합

### 3) 완전 자동화
- **기존**: 글 생성만 자동화
- **신규**: 정보수집→글쓰기→이미지→업로드 전체 자동화

### 4) 확장성
- **기존**: 새 기능 추가시 대규모 개발 필요
- **신규**: 새 MCP 서버 추가만으로 기능 확장

---

## 📞 개발 지원

### 실시간 음성 알림
```powershell
# 작업 완료시
powershell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('블로그 글 생성이 완료되었습니다')"

# 오류 발생시  
powershell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('오류가 발생했습니다. 확인이 필요합니다')"
```

### 개발 도구
- **Hot Reload**: 코드 변경시 즉시 반영
- **Debugger**: MCP 통신 실시간 모니터링
- **Profiler**: 성능 병목 지점 자동 탐지

---

> **다음 단계**: Phase 1 시작 - Electron 기본 앱 생성 및 첫 번째 MCP 연동 테스트

이제 차세대 AI 블로그 자동화 시스템 개발을 시작합니다! 🚀