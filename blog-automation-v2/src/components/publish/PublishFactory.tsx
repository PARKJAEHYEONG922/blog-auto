import React from 'react';
import { PublishComponentProps } from './PublishInterface';
import { PlaywrightNaverHelper } from './PlaywrightNaverHelper';
import { NaverBlogPublisher, BlogPostData, PublishOptions, PostStatus } from './NaverBlogPublisher';

// 플랫폼별 발행 컴포넌트 import
import NaverPublish, { NaverPublishMeta } from './NaverPublish';
import TistoryPublish, { TistoryPublishMeta } from './TistoryPublish';
import VelogPublish, { VelogPublishMeta } from './VelogPublish';

// 지원되는 플랫폼 목록
export const SUPPORTED_PLATFORMS = {
  naver: {
    component: NaverPublish,
    meta: NaverPublishMeta
  },
  tistory: {
    component: TistoryPublish,
    meta: TistoryPublishMeta
  },
  velog: {
    component: VelogPublish,
    meta: VelogPublishMeta
  }
} as const;

// 플랫폼 타입
export type SupportedPlatform = keyof typeof SUPPORTED_PLATFORMS;

// 발행 컴포넌트 팩토리
interface PublishFactoryProps extends PublishComponentProps {
  platform: string;
}

const PublishFactory: React.FC<PublishFactoryProps> = ({ 
  platform, 
  ...publishProps 
}) => {
  // 플랫폼이 지원되는지 확인
  if (!(platform in SUPPORTED_PLATFORMS)) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <div className="flex-shrink-0">
            <div className="text-gray-600 text-xl">❓</div>
          </div>
          <div className="flex-1">
            <h4 className="font-medium text-gray-800 mb-1">지원되지 않는 플랫폼</h4>
            <p className="text-sm text-gray-700">
              '{platform}' 플랫폼은 아직 지원되지 않습니다.
            </p>
            <div className="mt-2 text-sm text-gray-600">
              <strong>지원 플랫폼:</strong> {Object.values(SUPPORTED_PLATFORMS).map(p => p.meta.name).join(', ')}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // 해당 플랫폼의 컴포넌트 렌더링
  const PlatformComponent = SUPPORTED_PLATFORMS[platform as SupportedPlatform].component;
  const platformMeta = SUPPORTED_PLATFORMS[platform as SupportedPlatform].meta;

  return (
    <div className="section-card" style={{padding: '20px', marginBottom: '16px'}}>
      <div className="section-header" style={{marginBottom: '16px'}}>
        <div className="section-icon red" style={{width: '32px', height: '32px', fontSize: '16px'}}>
          🚀
        </div>
        <h2 className="section-title" style={{fontSize: '16px'}}>
          {platformMeta.icon} {platformMeta.name} 발행
        </h2>
      </div>
      
      <PlatformComponent {...publishProps} />
    </div>
  );
};

// 네이버 블로그 발행을 위한 정적 메서드
class PublishFactoryClass {
  static async publishToNaverBlog(
    postData: BlogPostData, 
    options: PublishOptions
  ): Promise<{ success: boolean; error?: string }> {
    let naverHelper: PlaywrightNaverHelper | null = null;
    let naverPublisher: NaverBlogPublisher | null = null;
    
    try {
      console.log('🚀 네이버 블로그 발행 시작');
      
      // 1. Playwright 네이버 헬퍼 초기화
      naverHelper = new PlaywrightNaverHelper();
      await naverHelper.initialize();
      
      console.log('📋 네이버 로그인이 필요합니다. 브라우저에서 로그인을 완료해주세요...');
      
      // 2. 사용자가 수동으로 로그인할 때까지 대기
      // 실제 프로덕션에서는 자격 증명을 사용할 수 있지만, 
      // 2차 인증 등을 고려하여 수동 로그인을 권장
      const page = naverHelper.getPage();
      if (!page) {
        throw new Error('페이지 초기화 실패');
      }
      
      // 로그인 상태 확인 대기 (최대 5분)
      const loginTimeout = 5 * 60 * 1000; // 5분
      const startTime = Date.now();
      
      while (Date.now() - startTime < loginTimeout) {
        const isLoggedIn = await naverHelper.checkLoginStatus();
        if (isLoggedIn) {
          console.log('✅ 네이버 로그인 확인됨');
          break;
        }
        
        // 10초마다 확인
        await new Promise(resolve => setTimeout(resolve, 10000));
        console.log('⏳ 네이버 로그인 대기 중... (브라우저에서 로그인해주세요)');
      }
      
      // 최종 로그인 상태 확인
      const finalLoginCheck = await naverHelper.checkLoginStatus();
      if (!finalLoginCheck) {
        throw new Error('네이버 로그인이 완료되지 않았습니다. 브라우저에서 로그인을 완료해주세요.');
      }
      
      // 3. 네이버 블로그 발행자 초기화
      naverPublisher = new NaverBlogPublisher(page);
      
      // 4. 블로그 글쓰기 페이지로 이동
      const writePageSuccess = await naverPublisher.navigateToWritePage();
      if (!writePageSuccess) {
        throw new Error('네이버 블로그 글쓰기 페이지 이동 실패');
      }
      
      // 5. 블로그 포스트 발행
      const publishResult = await naverPublisher.publishPost(postData, options);
      
      if (publishResult === PostStatus.PUBLISHED) {
        console.log('✅ 네이버 블로그 발행 완료');
        return { success: true };
      } else {
        throw new Error('블로그 포스트 발행 실패');
      }
      
    } catch (error) {
      console.error('❌ 네이버 블로그 발행 실패:', error);
      return {
        success: false,
        error: error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.'
      };
    } finally {
      // 리소스 정리
      if (naverHelper) {
        await naverHelper.cleanup();
      }
    }
  }
}

// 기본 컴포넌트와 클래스 메서드를 모두 제공
const PublishFactoryWithMethods = Object.assign(PublishFactory, PublishFactoryClass);

export default PublishFactoryWithMethods;