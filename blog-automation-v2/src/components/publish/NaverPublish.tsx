import React, { useState, useRef } from 'react';
import { PublishComponentProps, PublishStatus, PublishResult, IPublishComponent } from './PublishInterface';

// 네이버 로그인 자격증명
interface NaverCredentials {
  username: string;
  password: string;
}

const NaverPublish: React.FC<PublishComponentProps> = ({ 
  data, 
  editedContent, 
  imageUrls, 
  onComplete 
}) => {
  
  // 네이버 로그인 상태
  const [naverCredentials, setNaverCredentials] = useState<NaverCredentials>({
    username: '',
    password: ''
  });
  
  const [publishStatus, setPublishStatus] = useState<PublishStatus>({
    isPublishing: false,
    isLoggedIn: false,
    error: '',
    success: false
  });

  // 네이버 로그아웃 함수
  const logoutFromNaver = () => {
    setPublishStatus(prev => ({
      ...prev,
      isLoggedIn: false,
      error: '',
      success: false
    }));
    setNaverCredentials({ username: '', password: '' });
  };

  // 네이버 로그인 + 발행 통합 함수
  const publishToNaverBlog = async (): Promise<PublishResult> => {
    if (!naverCredentials.username || !naverCredentials.password) {
      setPublishStatus(prev => ({
        ...prev,
        error: '아이디와 비밀번호를 입력해주세요.'
      }));
      return { success: false, message: '아이디와 비밀번호를 입력해주세요.' };
    }
    
    setPublishStatus(prev => ({
      ...prev,
      error: '',
      isPublishing: true
    }));
    
    try {
      // 1단계: 네이버 로그인
      console.log('네이버 로그인 시도:', { username: naverCredentials.username });
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // 로그인 성공
      setPublishStatus(prev => ({ ...prev, isLoggedIn: true }));
      console.log('로그인 성공, 발행 시작...');
      
      // 2단계: 블로그 발행
      const htmlContent = editedContent;
      
      const blogData = {
        title: data.selectedTitle,
        content: htmlContent,
        tags: data.keyword ? [data.keyword] : [],
        htmlContent: htmlContent,
        credentials: naverCredentials,
        images: Object.values(imageUrls)
      };
      
      console.log('네이버 블로그 발행 데이터:', blogData);
      
      // 실제 네이버 블로그 API 호출 (현재는 시뮬레이션)
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      // 성공 처리
      setPublishStatus(prev => ({
        ...prev,
        success: true,
        isPublishing: false
      }));
      
      const result: PublishResult = {
        success: true,
        message: '네이버 블로그에 성공적으로 발행되었습니다!',
        url: 'https://blog.naver.com/example' // 실제로는 API 응답에서 받아옴
      };
      
      // 상위 컴포넌트에 완료 알림
      onComplete({ 
        generatedContent: editedContent,
        publishResult: result
      });
      
      return result;
      
    } catch (error) {
      console.error('로그인 또는 발행 실패:', error);
      const errorMessage = '로그인 또는 발행에 실패했습니다. 아이디와 비밀번호를 확인해주세요.';
      
      setPublishStatus(prev => ({
        ...prev,
        error: errorMessage,
        isLoggedIn: false,
        isPublishing: false
      }));
      
      return { success: false, message: errorMessage };
    }
  };

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
      <h4 className="font-medium text-blue-800 mb-3">네이버 블로그 발행</h4>
      
      {!publishStatus.success ? (
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              네이버 아이디
            </label>
            <input
              type="text"
              value={naverCredentials.username}
              onChange={(e) => setNaverCredentials(prev => ({ ...prev, username: e.target.value }))}
              placeholder="네이버 아이디를 입력하세요"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={publishStatus.isPublishing}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              비밀번호
            </label>
            <input
              type="password"
              value={naverCredentials.password}
              onChange={(e) => setNaverCredentials(prev => ({ ...prev, password: e.target.value }))}
              placeholder="비밀번호를 입력하세요"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={publishStatus.isPublishing}
              onKeyPress={(e) => e.key === 'Enter' && publishToNaverBlog()}
            />
          </div>
          
          <div className="text-sm text-gray-600 bg-gray-50 border border-gray-200 rounded p-3">
            <strong>발행 정보:</strong>
            <div className="ml-2 mt-1">
              • 제목: {data.selectedTitle}
              • 태그: {data.keyword || '없음'}
              • 이미지: {Object.keys(imageUrls).length}개
            </div>
          </div>
          
          {publishStatus.error && (
            <div className="text-red-600 text-sm bg-red-50 border border-red-200 rounded p-2">
              ❌ {publishStatus.error}
            </div>
          )}
          
          <button
            onClick={publishToNaverBlog}
            disabled={publishStatus.isPublishing || !naverCredentials.username || !naverCredentials.password}
            className="w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {publishStatus.isPublishing ? '🚀 로그인 중... 발행 준비 중...' : '📤 네이버 블로그에 발행하기'}
          </button>
        </div>
      ) : (
        // 발행 완료 후 상태
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <div className="text-green-600 text-xl">✅</div>
              <h4 className="font-medium text-green-800">
                발행 완료: {naverCredentials.username}
              </h4>
            </div>
            <button
              onClick={logoutFromNaver}
              className="text-sm text-gray-600 hover:text-gray-800 underline"
            >
              다시 발행하기
            </button>
          </div>
          
          <p className="text-sm text-green-700">
            네이버 블로그에 성공적으로 발행되었습니다!
          </p>
        </div>
      )}
      
      <div className="mt-3 text-xs text-gray-500">
        ⚠️ 로그인 정보는 발행 목적으로만 사용되며 저장되지 않습니다.
      </div>
    </div>
  );
};

// 네이버 발행 컴포넌트 메타정보
export const NaverPublishMeta: IPublishComponent = {
  platform: 'naver',
  name: '네이버 블로그',
  icon: '🟢'
};

export default NaverPublish;