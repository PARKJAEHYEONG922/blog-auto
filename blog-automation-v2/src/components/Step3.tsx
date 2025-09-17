import React, { useState } from 'react';
import { WorkflowData } from '../App';

interface Step3Props {
  data: WorkflowData;
  onComplete: (data: Partial<WorkflowData>) => void;
  onBack: () => void;
}

interface GenerationProgress {
  step: string;
  progress: number;
  status: 'pending' | 'running' | 'completed' | 'error';
}

const Step3: React.FC<Step3Props> = ({ data, onComplete, onBack }) => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [isPublishing, setIsPublishing] = useState(false);
  const [generatedContent, setGeneratedContent] = useState('');
  const [generatedImages, setGeneratedImages] = useState<string[]>([]);
  const [generationSteps, setGenerationSteps] = useState<GenerationProgress[]>([
    { step: 'SEO 최적화 구조 설계', progress: 0, status: 'pending' },
    { step: '플랫폼별 맞춤 콘텐츠 생성', progress: 0, status: 'pending' },
    { step: '이미지 생성 및 최적화', progress: 0, status: 'pending' },
    { step: '최종 검토 및 포맷팅', progress: 0, status: 'pending' }
  ]);

  const generateContent = async () => {
    setIsGenerating(true);
    
    // 단계별 생성 시뮬레이션
    for (let i = 0; i < generationSteps.length; i++) {
      setGenerationSteps(prev => prev.map((step, idx) => 
        idx === i ? { ...step, status: 'running' } : step
      ));

      for (let progress = 0; progress <= 100; progress += 25) {
        await new Promise(resolve => setTimeout(resolve, 300));
        setGenerationSteps(prev => prev.map((step, idx) => 
          idx === i ? { ...step, progress } : step
        ));
      }

      setGenerationSteps(prev => prev.map((step, idx) => 
        idx === i ? { ...step, status: 'completed', progress: 100 } : step
      ));

      await new Promise(resolve => setTimeout(resolve, 500));
    }

    // 생성된 콘텐츠 시뮬레이션
    const mockContent = `
# ${data.selectedTitle}

## 서론
${data.keyword}에 대해 알아보는 것은 매우 중요합니다. 이번 포스팅에서는 ${data.keyword}의 모든 것을 상세히 다뤄보겠습니다.

## ${data.keyword}란 무엇인가?
${data.keyword}는 현대 디지털 마케팅에서 핵심적인 역할을 담당하는 개념입니다. 

### 주요 특징
1. **효율성**: ${data.keyword}를 통해 더 나은 결과를 얻을 수 있습니다.
2. **접근성**: 누구나 쉽게 시작할 수 있는 분야입니다.
3. **확장성**: 점진적으로 발전시켜 나갈 수 있습니다.

## ${data.keyword} 실전 가이드

### 1단계: 기초 이해하기
먼저 ${data.keyword}의 기본 개념을 정확히 이해하는 것이 중요합니다.

### 2단계: 실습해보기
이론을 바탕으로 직접 실습해보면서 경험을 쌓아보세요.

### 3단계: 최적화하기
${data.keyword}를 더욱 효과적으로 활용하는 방법을 모색해보세요.

## 주의사항
${data.keyword}를 진행할 때 다음 사항들을 주의해야 합니다:
- 지속적인 학습과 개선
- 트렌드 변화에 대한 민감성
- 데이터 기반 의사결정

## 결론
${data.keyword}는 현재와 미래의 디지털 환경에서 필수적인 요소입니다. 이번 가이드를 통해 ${data.keyword}에 대한 이해를 높이고, 실제로 활용해보시기 바랍니다.

## 자주 묻는 질문
**Q: ${data.keyword} 초보자도 쉽게 시작할 수 있나요?**
A: 네, 단계별로 차근차근 접근하면 누구나 성공할 수 있습니다.

**Q: ${data.keyword}의 효과를 보기까지 얼마나 걸리나요?**
A: 개인차가 있지만, 보통 3-6개월 정도의 꾸준한 노력이 필요합니다.
    `.trim();

    // 이미지 URL 시뮬레이션
    const mockImages = [
      'https://via.placeholder.com/600x400?text=Introduction',
      'https://via.placeholder.com/600x400?text=Guide+Step+1',
      'https://via.placeholder.com/600x400?text=Guide+Step+2',
      'https://via.placeholder.com/600x400?text=Guide+Step+3',
      'https://via.placeholder.com/600x400?text=Best+Practices',
      'https://via.placeholder.com/600x400?text=Results',
      'https://via.placeholder.com/600x400?text=Tips',
      'https://via.placeholder.com/600x400?text=Conclusion'
    ];

    setGeneratedContent(mockContent);
    setGeneratedImages(mockImages);
    setIsGenerating(false);
  };

  const publishContent = async () => {
    setIsPublishing(true);
    
    // 발행 시뮬레이션 (3초)
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    setIsPublishing(false);
    alert(`${data.platform}에 성공적으로 발행되었습니다!`);
    onComplete({ generatedContent });
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return '✅';
      case 'running': return '🔄';
      case 'error': return '❌';
      default: return '⏳';
    }
  };

  const getPlatformName = (platform: string) => {
    const platforms: { [key: string]: string } = {
      'naver': '네이버 블로그',
      'tistory': '티스토리',
      'blogspot': '블로그스팟',
      'wordpress': '워드프레스'
    };
    return platforms[platform] || platform;
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            ✍️ Step 3: 플랫폼 맞춤 콘텐츠 생성 및 발행
          </h2>
          <p className="text-gray-600">
            발행 플랫폼: <span className="font-medium text-blue-600">{getPlatformName(data.platform)}</span>
          </p>
        </div>

        {!isGenerating && !generatedContent && (
          <div className="text-center py-12">
            <div className="mb-6">
              <div className="text-6xl mb-4">✨</div>
              <h3 className="text-xl font-medium text-gray-900 mb-2">
                최고 품질의 콘텐츠를 생성할 준비가 되었습니다
              </h3>
              <p className="text-gray-600">
                분석된 데이터를 바탕으로 {getPlatformName(data.platform)}에 최적화된 글과 이미지를 생성합니다
              </p>
            </div>
            <button
              onClick={generateContent}
              className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 font-medium"
            >
              🎨 콘텐츠 생성하기
            </button>
          </div>
        )}

        {isGenerating && (
          <div className="space-y-4">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-medium text-gray-900">생성 진행 상황</h3>
              <div className="text-sm text-gray-500">
                {generationSteps.filter(s => s.status === 'completed').length} / {generationSteps.length} 완료
              </div>
            </div>

            {generationSteps.map((step, index) => (
              <div key={index} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-lg">{getStatusIcon(step.status)}</span>
                    <span className="font-medium">{step.step}</span>
                  </div>
                  <span className="text-sm text-gray-500">{step.progress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-500 ${
                      step.status === 'completed' ? 'bg-green-500' :
                      step.status === 'running' ? 'bg-purple-500' :
                      'bg-gray-300'
                    }`}
                    style={{ width: `${step.progress}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}

        {generatedContent && (
          <div className="space-y-6">
            <div className="border-t pt-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">📝 생성된 콘텐츠</h3>
              
              {/* 콘텐츠 미리보기 */}
              <div className="border rounded-lg p-6 bg-gray-50 max-h-96 overflow-y-auto">
                <div className="prose max-w-none">
                  <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed">
                    {generatedContent}
                  </pre>
                </div>
              </div>

              {/* 생성된 이미지 */}
              <div className="mt-6">
                <h4 className="font-medium mb-3">🖼️ 생성된 이미지 ({generatedImages.length}개)</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {generatedImages.map((img, idx) => (
                    <div key={idx} className="border rounded-lg overflow-hidden">
                      <img 
                        src={img} 
                        alt={`Generated image ${idx + 1}`}
                        className="w-full h-24 object-cover"
                      />
                      <div className="p-2 text-xs text-gray-600 text-center">
                        이미지 {idx + 1}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* 콘텐츠 통계 */}
              <div className="grid md:grid-cols-3 gap-4 mt-6">
                <div className="border rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-blue-600">{generatedContent.length}</div>
                  <div className="text-sm text-gray-600">총 글자 수</div>
                </div>
                <div className="border rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-green-600">{generatedImages.length}</div>
                  <div className="text-sm text-gray-600">이미지 개수</div>
                </div>
                <div className="border rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-purple-600">95%</div>
                  <div className="text-sm text-gray-600">SEO 최적화 점수</div>
                </div>
              </div>

              {/* 발행 버튼 */}
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mt-6">
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    <div className="text-yellow-600 text-xl">⚠️</div>
                  </div>
                  <div className="flex-1">
                    <h4 className="font-medium text-yellow-800 mb-1">발행 전 확인</h4>
                    <p className="text-sm text-yellow-700 mb-3">
                      생성된 콘텐츠를 검토하신 후 {getPlatformName(data.platform)}에 자동으로 발행됩니다.
                    </p>
                    <button
                      onClick={publishContent}
                      disabled={isPublishing}
                      className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                    >
                      {isPublishing ? '🚀 발행 중...' : `📤 ${getPlatformName(data.platform)}에 발행하기`}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 네비게이션 */}
        <div className="flex justify-between pt-6 border-t">
          <button
            onClick={onBack}
            className="px-6 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
          >
            ← 이전 단계
          </button>
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            🔄 새로운 글 작성하기
          </button>
        </div>
      </div>
    </div>
  );
};

export default Step3;