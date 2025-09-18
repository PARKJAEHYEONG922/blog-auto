// 공통으로 사용되는 기본 정보 인터페이스들

/**
 * 키워드 정보 - 모든 서비스에서 공통으로 사용
 */
export interface KeywordInfo {
  /** 검색에 사용하는 키워드 (사용자가 수정 가능) */
  searchKeyword: string;
  /** 메인 키워드 (원본, 옵션) */
  mainKeyword?: string;
  /** 보조 키워드들 */
  subKeywords?: string[];
}

/**
 * 선택된 제목 정보
 */
export interface SelectedTitleInfo {
  /** 사용자가 선택한 제목 */
  selectedTitle: string;
}

/**
 * 콘텐츠 타입 정보
 */
export interface ContentTypeInfo {
  /** 콘텐츠 유형 ID */
  contentType: string;
}

/**
 * 후기 타입 정보
 */
export interface ReviewTypeInfo {
  /** 후기 유형 ID */
  reviewType?: string;
}

/**
 * 말투 정보
 */
export interface ToneInfo {
  /** 말투 ID */
  tone: string;
}

/**
 * 플랫폼 정보
 */
export interface PlatformInfo {
  /** 플랫폼 ID */
  platform: string;
  /** 플랫폼 이름 (옵션) */
  platformName?: string;
}

/**
 * 필수 키워드 정보 - 글쓰기 등에서 메인키워드가 반드시 필요한 경우
 */
export interface RequiredKeywordInfo {
  /** 검색에 사용하는 키워드 (사용자가 수정 가능) */
  searchKeyword: string;
  /** 메인 키워드 (원본, 필수) */
  mainKeyword: string;
  /** 보조 키워드들 */
  subKeywords?: string[];
}

/**
 * 기본 요청 정보 - 대부분의 서비스에서 사용하는 공통 정보
 */
export interface BaseRequestInfo extends KeywordInfo, SelectedTitleInfo, ContentTypeInfo, ReviewTypeInfo {
}

/**
 * 전체 요청 정보 - 모든 정보 포함
 */
export interface FullRequestInfo extends BaseRequestInfo, ToneInfo, PlatformInfo {
  /** 블로거 정체성 */
  bloggerIdentity?: string;
}