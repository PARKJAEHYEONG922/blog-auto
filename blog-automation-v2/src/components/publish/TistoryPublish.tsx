import React from 'react';
import { PublishComponentProps, IPublishComponent } from './PublishInterface';

const TistoryPublish: React.FC<PublishComponentProps> = ({ 
  data, 
  editedContent, 
  imageUrls, 
  onComplete 
}) => {
  return (
    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0">
          <div className="text-yellow-600 text-xl">🚧</div>
        </div>
        <div className="flex-1">
          <h4 className="font-medium text-yellow-800 mb-1">준비 중</h4>
          <p className="text-sm text-yellow-700">
            티스토리 발행 기능이 곧 추가될 예정입니다.
          </p>
          <div className="mt-3 text-sm text-gray-600">
            <strong>예정 기능:</strong>
            <div className="ml-2 mt-1">
              • OAuth 2.0 인증
              • 카테고리 선택
              • 공개/비공개 설정
              • 태그 및 썸네일 자동 설정
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// 티스토리 발행 컴포넌트 메타정보
export const TistoryPublishMeta: IPublishComponent = {
  platform: 'tistory',
  name: '티스토리',
  icon: '🟠'
};

export default TistoryPublish;