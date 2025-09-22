import React from 'react';
import { PublishComponentProps, IPublishComponent } from './PublishInterface';

const VelogPublish: React.FC<PublishComponentProps> = ({ 
  data, 
  editedContent, 
  imageUrls, 
  onComplete 
}) => {
  return (
    <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0">
          <div className="text-purple-600 text-xl">🚧</div>
        </div>
        <div className="flex-1">
          <h4 className="font-medium text-purple-800 mb-1">준비 중</h4>
          <p className="text-sm text-purple-700">
            Velog 발행 기능이 곧 추가될 예정입니다.
          </p>
          <div className="mt-3 text-sm text-gray-600">
            <strong>예정 기능:</strong>
            <div className="ml-2 mt-1">
              • GitHub 연동 인증
              • 마크다운 자동 변환
              • 시리즈 설정
              • 태그 및 썸네일 자동 설정
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Velog 발행 컴포넌트 메타정보
export const VelogPublishMeta: IPublishComponent = {
  platform: 'velog',
  name: 'Velog',
  icon: '🟣'
};

export default VelogPublish;