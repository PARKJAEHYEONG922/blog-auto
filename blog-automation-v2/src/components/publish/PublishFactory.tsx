import React from 'react';
import { PublishComponentProps } from './PublishInterface';

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

export default PublishFactory;