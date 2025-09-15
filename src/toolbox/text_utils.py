"""
통합 텍스트 처리 및 검증 유틸리티 (CLAUDE.md 구조)
키워드 파싱/정규화, 카테고리 처리, URL/상품ID/파일 검증 등 모든 모듈에서 사용하는 텍스트 관련 기능
validators.py 기능 통합 완료 - 중복 제거 및 단일 책임 원칙 적용
"""
import re
import os
from typing import List, Set, Tuple, Optional, Dict, Any
from urllib.parse import urlparse
from pathlib import Path
from src.foundation.logging import get_logger

logger = get_logger("toolbox.text_utils")


def is_advertisement_content(text_content: str, title: str = "") -> bool:
    """광고/협찬/체험단 글인지 판단"""
    if not text_content:
        return False
    
    # 전체 텍스트를 소문자로 변환하여 검사
    full_text = (text_content + " " + title).lower()
    
    # 광고/협찬 관련 키워드들
    ad_keywords = [
        # 광고 관련
        "광고포스트", "광고 포스트", "광고글", "광고 글", "광고입니다", "광고 입니다",
        "유료광고", "유료 광고", "파트너스", "쿠팡파트너스", "파트너 활동", "추천링크",
        
        # 협찬 관련  
        "협찬", "협찬받", "협찬글", "협찬 글", "협찬으로", "협찬을", "제공받", "무료로 제공",
        "브랜드로부터", "업체로부터", "해당업체", "해당 업체", "제품을 제공", "서비스를 제공", 
        "제공받아", "제공받은", "지원을 받아", "지원받아", "업체에서 제공", "업체로부터 제품",
        
        # 체험단 관련
        "체험단", "체험 단", "리뷰어", "체험후기", "체험 후기", "체험해보", "체험을",
        "무료체험", "무료 체험", "서포터즈", "앰배서더", "인플루언서",
        
        # 기타 상업적 키워드
        "원고료", "대가", "소정의", "혜택을", "증정", "무료로 받", "공짜로", 
        "할인코드", "쿠폰", "프로모션", "이벤트 참여"
    ]
    
    # 키워드 매칭 검사
    for keyword in ad_keywords:
        if keyword in full_text:
            logger.info(f"광고/협찬 글 감지: '{keyword}' 키워드 발견")
            return True
    
    # 패턴 매칭 (정규식)
    ad_patterns = [
        r".*제공받.*작성.*",  # "제공받아 작성한", "제공받고 작성한" 등
        r".*협찬.*받.*글.*",  # "협찬받은 글", "협찬을 받아서" 등  
        r".*무료.*받.*후기.*", # "무료로 받아서 후기", "무료로 받은 후기" 등
        r".*체험.*참여.*",     # "체험에 참여해", "체험단 참여" 등
        r".*광고.*포함.*",     # "광고가 포함", "광고를 포함한" 등
        r".*업체.*지원.*받.*", # "해당 업체에 지원을 받아", "업체로부터 지원받아" 등
        r".*업체.*제품.*제공.*", # "업체로부터 제품을 제공받아" 등
    ]
    
    for pattern in ad_patterns:
        if re.search(pattern, full_text):
            logger.info(f"광고/협찬 글 감지: 패턴 '{pattern}' 매칭")
            return True
    
    return False


def is_low_quality_content(text_content: str) -> bool:
    """콘텐츠 품질이 낮은 글인지 판단 (숫자만 나열, 특수문자 과다)"""
    if not text_content:
        return False

    # 텍스트 전처리 (공백 제거)
    cleaned_text = text_content.strip()
    if len(cleaned_text) < 100:  # 너무 짧은 글은 별도 체크
        return False

    # 1. 숫자만 나열된 글 체크 (전화번호, 가격표, 주소 등)
    # 숫자, 공백, 하이픈, 콤마, 괄호, 원화표시 외에는 거의 없는 경우
    numbers_and_symbols = re.sub(r'[0-9\s\-,()원₩\.\+#]', '', cleaned_text)
    if len(numbers_and_symbols) / len(cleaned_text) < 0.3:  # 의미있는 문자가 30% 미만
        logger.info(f"품질 낮은 글 감지: 숫자/기호만 나열됨 (의미있는 문자 비율: {len(numbers_and_symbols) / len(cleaned_text) * 100:.1f}%)")
        return True

    # 2. 특수문자 비율이 너무 높은 글 체크
    # 한글, 영문, 숫자, 공백을 제외한 특수문자 비율
    special_chars = re.sub(r'[가-힣ㄱ-ㅎㅏ-ㅣa-zA-Z0-9\s]', '', cleaned_text)
    special_char_ratio = len(special_chars) / len(cleaned_text)
    if special_char_ratio > 0.15:  # 특수문자가 15% 초과
        logger.info(f"품질 낮은 글 감지: 특수문자 과다 (비율: {special_char_ratio * 100:.1f}%)")
        return True

    # 3. 반복 패턴 체크 (같은 문자나 기호의 반복)
    # 같은 문자 5개 이상 연속 반복 체크
    if re.search(r'(.)\1{4,}', cleaned_text):  # 같은 문자 5개 이상 반복
        logger.info("품질 낮은 글 감지: 같은 문자 반복 패턴")
        return True

    return False


def parse_keywords(text: str) -> List[str]:
    """텍스트에서 키워드 파싱 (keyword_analysis와의 호환성)"""
    return TextProcessor.parse_keywords_from_text(text)


def filter_unique_keywords_with_skipped(keywords: List[str]) -> Tuple[List[str], List[str]]:
    """중복 키워드 필터링 및 건너뛴 목록 반환"""
    unique_keywords = []
    skipped_keywords = []
    seen = set()
    
    for keyword in keywords:
        clean_keyword = keyword.strip().lower()
        if clean_keyword and clean_keyword not in seen:
            unique_keywords.append(keyword.strip())
            seen.add(clean_keyword)
        elif keyword.strip():
            skipped_keywords.append(keyword.strip())
    
    return unique_keywords, skipped_keywords


class TextProcessor:
    """텍스트 처리기"""
    
    @staticmethod
    def parse_keywords_from_text(text: str) -> List[str]:
        """
        텍스트에서 키워드 목록 파싱 (엔터, 쉼표 구분 지원)
        
        Args:
            text: 입력 텍스트
        
        Returns:
            List[str]: 파싱된 키워드 목록
        """
        if not text.strip():
            return []
        
        keywords = []
        
        # 개행문자와 쉼표로 분리
        text = text.replace(',', '\n').replace('，', '\n')  # 영문/한글 쉼표 모두 지원
        
        for line in text.strip().split('\n'):
            line = line.strip()
            if line:
                # 세미콜론이나 기타 구분자도 처리
                for keyword in line.replace(';', '\n').replace('|', '\n').split('\n'):
                    keyword = keyword.strip()
                    if keyword:
                        keywords.append(keyword)
        
        logger.info(f"텍스트에서 {len(keywords)}개 키워드 파싱 완료")
        return keywords
    
    @staticmethod
    def clean_keyword(keyword: str) -> str:
        """
        키워드 정리 (공백 제거, 대소문자 통일 등)
        
        Args:
            keyword: 원본 키워드
        
        Returns:
            str: 정리된 키워드
        """
        if not keyword:
            return ""
        
        # 앞뒤 공백 제거
        cleaned = keyword.strip()
        
        # 연속된 공백을 하나로 통일
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned
    
    @staticmethod
    def normalize_keyword(keyword: str) -> str:
        """
        키워드 정규화 (비교용)
        
        Args:
            keyword: 원본 키워드
        
        Returns:
            str: 정규화된 키워드
        """
        if not keyword:
            return ""
        
        # 공백 제거 + 대문자 변환 (PowerLink 방식과 호환)
        normalized = keyword.strip().replace(' ', '').upper()
        return normalized
    
    @staticmethod
    def filter_unique_keywords(keywords: List[str], existing_keywords: Set[str] = None) -> List[str]:
        """
        중복 제거 및 기존 키워드 필터링
        
        Args:
            keywords: 키워드 목록
            existing_keywords: 기존 키워드 집합
        
        Returns:
            List[str]: 중복 제거된 키워드 목록
        """
        if existing_keywords is None:
            existing_keywords = set()
        
        unique_keywords = []
        seen = set()
        
        for keyword in keywords:
            # 정리 및 정규화
            cleaned = TextProcessor.clean_keyword(keyword)
            normalized = TextProcessor.normalize_keyword(cleaned)
            
            if normalized and normalized not in seen and normalized not in existing_keywords:
                unique_keywords.append(cleaned)  # 원본 형태로 저장
                seen.add(normalized)
        
        logger.debug(f"중복 제거 완료: {len(keywords)} -> {len(unique_keywords)}개")
        return unique_keywords
    
    @staticmethod
    def filter_unique_keywords_with_skipped(keywords: List[str], 
                                          existing_keywords: Set[str] = None) -> Tuple[List[str], List[str]]:
        """
        중복 제거 및 기존 키워드 필터링 (건너뛴 키워드 목록도 반환)
        
        Args:
            keywords: 키워드 목록
            existing_keywords: 기존 키워드 집합
        
        Returns:
            Tuple[List[str], List[str]]: (고유 키워드, 건너뛴 키워드)
        """
        if existing_keywords is None:
            existing_keywords = set()
        
        unique_keywords = []
        skipped_keywords = []
        seen = set()
        
        for keyword in keywords:
            # 정리 및 정규화
            cleaned = TextProcessor.clean_keyword(keyword)
            normalized = TextProcessor.normalize_keyword(cleaned)
            
            if normalized:
                if normalized in existing_keywords:
                    # 이미 검색된 키워드
                    skipped_keywords.append(cleaned)
                elif normalized not in seen:
                    # 새로운 키워드
                    unique_keywords.append(cleaned)
                    seen.add(normalized)
        
        logger.info(f"중복 제거 완료: {len(keywords)} -> {len(unique_keywords)}개 (건너뛴: {len(skipped_keywords)}개)")
        return unique_keywords, skipped_keywords
    
    @staticmethod
    def validate_keyword(keyword: str) -> bool:
        """키워드 유효성 검사"""
        if not keyword or not keyword.strip():
            return False
        
        cleaned = TextProcessor.clean_keyword(keyword)
        
        # 최소/최대 길이 검사
        if len(cleaned) < 1 or len(cleaned) > 100:
            return False
        
        # 특수문자만으로 이루어진 키워드 제외
        if not any(c.isalnum() for c in cleaned):
            return False
        
        return True
    
    @staticmethod
    def extract_keywords_from_mixed_text(text: str) -> List[str]:
        """혼합된 텍스트에서 키워드 추출 (더 유연한 파싱)"""
        if not text.strip():
            return []
        
        # 다양한 구분자로 분리
        separators = ['\n', ',', '，', ';', '|', '\t']
        
        # 모든 구분자를 개행문자로 통일
        for sep in separators:
            text = text.replace(sep, '\n')
        
        keywords = []
        for line in text.split('\n'):
            # 공백으로도 분리 시도 (단어 단위)
            words = line.split()
            for word in words:
                word = word.strip()
                if word and TextProcessor.validate_keyword(word):
                    keywords.append(word)
        
        return keywords
    
    @staticmethod
    def split_keywords_by_batch_size(keywords: List[str], batch_size: int = 100) -> List[List[str]]:
        """키워드를 배치 크기별로 분할"""
        batches = []
        for i in range(0, len(keywords), batch_size):
            batch = keywords[i:i + batch_size]
            batches.append(batch)
        return batches


class CategoryProcessor:
    """카테고리 처리기"""
    
    @staticmethod
    def extract_last_category(category_path: str, separator: str = ' > ') -> str:
        """
        카테고리 경로에서 마지막 카테고리 추출
        
        Args:
            category_path: 카테고리 경로 (예: "가전 > 컴퓨터 > 노트북")
            separator: 구분자
        
        Returns:
            str: 마지막 카테고리
        """
        if not category_path:
            return ""
        
        categories = category_path.split(separator)
        return categories[-1].strip() if categories else ""
    
    @staticmethod
    def build_category_path(categories: List[str], separator: str = ' > ') -> str:
        """
        카테고리 목록을 경로로 결합
        
        Args:
            categories: 카테고리 목록
            separator: 구분자
        
        Returns:
            str: 카테고리 경로
        """
        if not categories:
            return ""
        
        # 빈 카테고리 제거
        valid_categories = [cat.strip() for cat in categories if cat.strip()]
        return separator.join(valid_categories)
    
    @staticmethod
    def calculate_category_similarity(category1: str, category2: str) -> float:
        """
        두 카테고리 간 유사도 계산 (간단한 문자열 매칭)
        
        Args:
            category1: 첫 번째 카테고리
            category2: 두 번째 카테고리
        
        Returns:
            float: 유사도 (0.0 ~ 1.0)
        """
        if not category1 or not category2:
            return 0.0
        
        # 대소문자 통일 및 공백 제거
        cat1 = category1.lower().replace(' ', '')
        cat2 = category2.lower().replace(' ', '')
        
        if cat1 == cat2:
            return 1.0
        
        # 포함 관계 확인
        if cat1 in cat2 or cat2 in cat1:
            return 0.7
        
        # 간단한 문자 매칭
        common_chars = set(cat1) & set(cat2)
        total_chars = set(cat1) | set(cat2)
        
        if total_chars:
            return len(common_chars) / len(total_chars)
        
        return 0.0


# ================================
# 편의 함수들 (하위 호환성)
# ================================

def parse_keywords_from_text(text: str) -> List[str]:
    """키워드 파싱 편의 함수"""
    return TextProcessor.parse_keywords_from_text(text)


def clean_keyword(keyword: str) -> str:
    """키워드 정리 편의 함수"""
    return TextProcessor.clean_keyword(keyword)


def normalize_keyword(keyword: str) -> str:
    """키워드 정규화 편의 함수"""
    return TextProcessor.normalize_keyword(keyword)


def filter_unique_keywords(keywords: List[str], existing_keywords: Set[str] = None) -> List[str]:
    """중복 제거 편의 함수"""
    return TextProcessor.filter_unique_keywords(keywords, existing_keywords)


def filter_unique_keywords_with_skipped(keywords: List[str], 
                                      existing_keywords: Set[str] = None) -> Tuple[List[str], List[str]]:
    """중복 제거 및 기존 키워드 필터링 (건너뛴 키워드 목록도 반환)"""
    return TextProcessor.filter_unique_keywords_with_skipped(keywords, existing_keywords)


def validate_keyword(keyword: str) -> bool:
    """키워드 유효성 검사 편의 함수"""
    return TextProcessor.validate_keyword(keyword)


def clean_keywords(keywords: List[str]) -> List[str]:
    """키워드 목록 정리 편의 함수"""
    return [TextProcessor.clean_keyword(kw) for kw in keywords if kw.strip()]


def filter_valid_keywords(keywords: List[str]) -> List[str]:
    """유효한 키워드만 필터링"""
    return [keyword for keyword in keywords if validate_keyword(keyword)]


def get_last_category(category_path: str) -> str:
    """마지막 카테고리 추출 편의 함수"""
    return CategoryProcessor.extract_last_category(category_path)


def split_keywords_by_batch_size(keywords: List[str], batch_size: int = 100) -> List[List[str]]:
    """키워드를 배치 크기별로 분할"""
    return TextProcessor.split_keywords_by_batch_size(keywords, batch_size)


# ================================
# 하위 호환성 함수들 (필요시에만 유지)
# ================================

def process_keywords(keywords: List[str], existing_keywords: set = None) -> List[str]:
    """PowerLink 호환용 키워드 처리 함수"""
    if existing_keywords is None:
        existing_keywords = set()
    
    return filter_unique_keywords(keywords, existing_keywords)


def filter_duplicates(keywords: List[str], existing: Set[str] = None) -> List[str]:
    """중복 제거 편의 함수 (하위 호환성)"""
    return filter_unique_keywords(keywords, existing)


def format_keyword_for_display(keyword: str) -> str:
    """화면 표시용 키워드 포맷팅"""
    if not keyword:
        return ""
    
    return keyword.strip()


# === 간단한 검증 함수들 (실제 사용되는 것들만) ===

def validate_url(url: str) -> bool:
    """URL 유효성 검사"""
    if not url:
        return False
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def validate_naver_url(url: str) -> bool:
    """네이버 쇼핑 URL 검증"""
    if not validate_url(url):
        return False
    
    naver_domains = [
        'shopping.naver.com',
        'smartstore.naver.com', 
        'brand.naver.com'
    ]
    
    parsed = urlparse(url)
    return any(domain in parsed.netloc for domain in naver_domains)


def extract_product_id(url: str) -> Optional[str]:
    """네이버 쇼핑 URL에서 상품 ID 추출"""
    if not validate_naver_url(url):
        return None
    
    patterns = [
        r'https?://shopping\.naver\.com/catalog/(\d+)',
        r'https?://smartstore\.naver\.com/[^/]+/products/(\d+)',
        r'https?://brand\.naver\.com/[^/]+/products/(\d+)',
        r'/products/(\d+)',
        r'nvMid=(\d+)',
        r'productId=(\d+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def validate_product_id(product_id: str) -> bool:
    """상품 ID 유효성 검사"""
    if not product_id or not isinstance(product_id, str):
        return False
    return bool(re.match(r'^\d{5,}$', product_id.strip()))


def validate_excel_file(filename: str) -> Tuple[bool, str]:
    """엑셀 파일명 검증"""
    if not filename or not isinstance(filename, str):
        return False, "파일명이 없습니다"
    
    # 기본 안전성 검사
    forbidden_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    if any(char in filename for char in forbidden_chars):
        return False, "유효하지 않은 파일명입니다"
    
    # 엑셀 확장자 확인
    valid_extensions = ['.xlsx', '.xls']
    if not any(filename.lower().endswith(ext) for ext in valid_extensions):
        return False, "엑셀 파일 확장자(.xlsx, .xls)가 필요합니다"
    
    return True, "유효한 엑셀 파일명입니다"


# === 중복 편의 함수들 제거됨 ===
# 위에 정의된 함수들을 사용하세요 (parse_keywords, clean_keyword, normalize_keyword)


# === 암호화/복호화 유틸리티 ===

def encrypt_password(password: str) -> str:
    """비밀번호 암호화 (간단한 Base64 인코딩)"""
    import base64
    # 실제 운영환경에서는 더 강력한 암호화 사용 권장
    encoded = base64.b64encode(password.encode('utf-8')).decode('utf-8')
    return encoded


def decrypt_password(encrypted_password: str) -> str:
    """비밀번호 복호화"""
    import base64
    try:
        decoded = base64.b64decode(encrypted_password.encode('utf-8')).decode('utf-8')
        return decoded
    except Exception:
        return ""


# === JSON 처리 유틸리티 ===

def parse_json_response(response: str) -> Any:
    """AI API 응답에서 JSON 파싱 (마크다운 코드 블록 제거 포함)"""
    import json
    
    try:
        # 마크다운 코드 블록 제거 (```json...``` 또는 ```...```)
        cleaned_response = response.strip()
        if cleaned_response.startswith('```'):
            lines = cleaned_response.split('\n')
            if len(lines) > 2 and lines[0].startswith('```') and lines[-1].strip() == '```':
                cleaned_response = '\n'.join(lines[1:-1])

        return json.loads(cleaned_response)
    except json.JSONDecodeError as e:
        from src.foundation.logging import get_logger
        logger = get_logger("toolbox.text_utils")
        logger.error(f"JSON 파싱 실패: {e}\nResponse: {response}")
        raise ValueError(f"JSON 파싱 실패: {str(e)}")