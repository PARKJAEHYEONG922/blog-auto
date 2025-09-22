import { WorkflowData } from '../../App';

// 발행 상태 타입
export interface PublishStatus {
  isPublishing: boolean;
  isLoggedIn: boolean;
  error: string;
  success: boolean;
}

// 발행 결과 타입
export interface PublishResult {
  success: boolean;
  message: string;
  url?: string; // 발행된 글의 URL
}

// 플랫폼별 발행 컴포넌트 Props
export interface PublishComponentProps {
  data: WorkflowData;
  editedContent: string;
  imageUrls: { [key: number]: string };
  onComplete: (data: Partial<WorkflowData>) => void;
}

// 플랫폼별 발행 컴포넌트가 구현해야 할 인터페이스
export interface IPublishComponent {
  platform: string;
  name: string;
  icon: string;
}