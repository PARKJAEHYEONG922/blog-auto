import React, { useState, useEffect } from 'react';
import { WorkflowData } from '../App';

interface Step2Props {
  data: WorkflowData;
  onNext: (data: Partial<WorkflowData>) => void;
  onBack: () => void;
}

interface AnalysisProgress {
  step: string;
  progress: number;
  status: 'pending' | 'running' | 'completed' | 'error';
  data?: any;
}

const Step2: React.FC<Step2Props> = ({ data, onNext, onBack }) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisSteps, setAnalysisSteps] = useState<AnalysisProgress[]>([
    { step: '키워드 추출 및 분석', progress: 0, status: 'pending' },
    { step: '네이버 블로그 데이터 수집', progress: 0, status: 'pending' },
    { step: '유튜브 콘텐츠 분석', progress: 0, status: 'pending' },
    { step: '네이버 쇼핑 데이터 수집', progress: 0, status: 'pending' },
    { step: '경쟁사 콘텐츠 분석', progress: 0, status: 'pending' },
    { step: '이미지 개수 패턴 분석', progress: 0, status: 'pending' },
    { step: 'SEO 키워드 최적화', progress: 0, status: 'pending' },
    { step: '데이터 정제 및 요약', progress: 0, status: 'pending' }
  ]);
  const [collectedData, setCollectedData] = useState<any>(null);

  const startAnalysis = async () => {
    setIsAnalyzing(true);
    
    // 단계별 분석 시뮬레이션
    for (let i = 0; i < analysisSteps.length; i++) {
      // 현재 단계 실행 중으로 표시
      setAnalysisSteps(prev => prev.map((step, idx) => 
        idx === i ? { ...step, status: 'running' } : step
      ));

      // 진행률 시뮬레이션
      for (let progress = 0; progress <= 100; progress += 20) {
        await new Promise(resolve => setTimeout(resolve, 200));
        setAnalysisSteps(prev => prev.map((step, idx) => 
          idx === i ? { ...step, progress } : step
        ));
      }

      // 완료 처리
      setAnalysisSteps(prev => prev.map((step, idx) => 
        idx === i ? { ...step, status: 'completed', progress: 100 } : step
      ));

      await new Promise(resolve => setTimeout(resolve, 500));
    }

    // 수집된 데이터 시뮬레이션
    const mockData = {
      keywords: {
        main: data.keyword,
        extracted: ['SEO 최적화', '콘텐츠 마케팅', '블로그 운영', '검색엔진'],
        suggestions: ['블로그 수익화', '콘텐츠 전략', '키워드 분석']
      },
      competitors: [
        {
          title: `${data.keyword} 완벽 가이드 - 초보자를 위한 실전 팁`,
          url: 'https://example1.com',
          views: '15,234',
          images: 8,
          platform: 'naver'
        },
        {
          title: `${data.keyword} 성공 사례와 노하우 공유`,
          url: 'https://example2.com',
          views: '12,890',
          images: 12,
          platform: 'tistory'
        },
        {
          title: `${data.keyword} 완벽 정복! 전문가 추천`,
          url: 'https://example3.com',
          views: '9,567',
          images: 6,
          platform: 'youtube'
        }
      ],
      shopping: {
        products: [
          { name: `${data.keyword} 관련 도구`, price: '29,900원', rating: 4.8, reviews: 342 },
          { name: `${data.keyword} 전문서적`, price: '18,500원', rating: 4.6, reviews: 156 },
          { name: `${data.keyword} 온라인강의`, price: '99,000원', rating: 4.9, reviews: 89 }
        ],
        avgPrice: '49,133원',
        topKeywords: ['완벽', '초보자', '실전', '노하우', '전문가']
      },
      imageAnalysis: {
        averageCount: 9,
        recommendations: '상위 노출 글들은 평균 8-12개의 이미지를 사용합니다.',
        optimalRange: '10-12개'
      },
      seoInsights: {
        titleLength: '30-40자',
        keywordDensity: '2-3%',
        headingStructure: 'H2 3-5개, H3 각 섹션별 2-3개',
        contentLength: '2000-3000자'
      }
    };

    setCollectedData(mockData);
    setIsAnalyzing(false);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return '✅';
      case 'running': return '🔄';
      case 'error': return '❌';
      default: return '⏳';
    }
  };

  const handleNext = () => {
    if (!collectedData) {
      alert('분석을 완료해주세요.');
      return;
    }

    onNext({ collectedData });
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            🔍 Step 2: 지능형 데이터 수집 및 분석
          </h2>
          <p className="text-gray-600">
            선택된 제목: <span className="font-medium text-blue-600">{data.selectedTitle}</span>
          </p>
        </div>

        {!isAnalyzing && !collectedData && (
          <div className="text-center py-12">
            <div className="mb-6">
              <div className="text-6xl mb-4">🎯</div>
              <h3 className="text-xl font-medium text-gray-900 mb-2">
                경쟁사 분석을 시작할 준비가 되었습니다
              </h3>
              <p className="text-gray-600">
                AI가 멀티플랫폼에서 데이터를 수집하고 분석합니다
              </p>
            </div>
            <button
              onClick={startAnalysis}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
            >
              🚀 분석 시작하기
            </button>
          </div>
        )}

        {isAnalyzing && (
          <div className="space-y-4">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-medium text-gray-900">분석 진행 상황</h3>
              <div className="text-sm text-gray-500">
                {analysisSteps.filter(s => s.status === 'completed').length} / {analysisSteps.length} 완료
              </div>
            </div>

            {analysisSteps.map((step, index) => (
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
                      step.status === 'running' ? 'bg-blue-500' :
                      step.status === 'error' ? 'bg-red-500' : 'bg-gray-300'
                    }`}
                    style={{ width: `${step.progress}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}

        {collectedData && (
          <div className="space-y-6">
            <div className="border-t pt-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">📊 분석 결과</h3>
              
              {/* 키워드 분석 */}
              <div className="grid md:grid-cols-2 gap-6 mb-6">
                <div className="border rounded-lg p-4">
                  <h4 className="font-medium mb-3">🎯 추출된 키워드</h4>
                  <div className="space-y-2">
                    <div>
                      <span className="text-sm text-gray-600">메인:</span>
                      <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm">
                        {collectedData.keywords.main}
                      </span>
                    </div>
                    <div>
                      <span className="text-sm text-gray-600">연관:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {collectedData.keywords.extracted.map((kw: string, idx: number) => (
                          <span key={idx} className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                            {kw}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="border rounded-lg p-4">
                  <h4 className="font-medium mb-3">🖼️ 이미지 분석</h4>
                  <div className="space-y-2 text-sm">
                    <p><span className="text-gray-600">평균 개수:</span> {collectedData.imageAnalysis.averageCount}개</p>
                    <p><span className="text-gray-600">권장 범위:</span> {collectedData.imageAnalysis.optimalRange}개</p>
                    <p className="text-xs text-gray-500">{collectedData.imageAnalysis.recommendations}</p>
                  </div>
                </div>
              </div>

              {/* 경쟁사 분석 */}
              <div className="border rounded-lg p-4 mb-6">
                <h4 className="font-medium mb-3">🏆 상위 경쟁 콘텐츠</h4>
                <div className="space-y-3">
                  {collectedData.competitors.map((comp: any, idx: number) => (
                    <div key={idx} className="flex items-start justify-between p-3 bg-gray-50 rounded">
                      <div className="flex-1">
                        <p className="font-medium text-sm">{comp.title}</p>
                        <div className="flex items-center space-x-4 mt-1 text-xs text-gray-500">
                          <span>조회수: {comp.views}</span>
                          <span>이미지: {comp.images}개</span>
                          <span className="px-2 py-1 bg-white rounded">{comp.platform}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* SEO 권장사항 */}
              <div className="border rounded-lg p-4">
                <h4 className="font-medium mb-3">📈 SEO 최적화 가이드</h4>
                <div className="grid md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <p><span className="text-gray-600">제목 길이:</span> {collectedData.seoInsights.titleLength}</p>
                    <p><span className="text-gray-600">키워드 밀도:</span> {collectedData.seoInsights.keywordDensity}</p>
                  </div>
                  <div>
                    <p><span className="text-gray-600">글자 수:</span> {collectedData.seoInsights.contentLength}</p>
                    <p><span className="text-gray-600">구조:</span> {collectedData.seoInsights.headingStructure}</p>
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
            onClick={handleNext}
            disabled={!collectedData}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            다음 단계 →
          </button>
        </div>
      </div>
    </div>
  );
};

export default Step2;