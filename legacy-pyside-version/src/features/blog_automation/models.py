"""
블로그 자동화 모듈의 데이터 모델
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List
from datetime import datetime


class BlogPlatform(Enum):
    """블로그 플랫폼 타입"""
    NAVER = "naver"
    TISTORY = "tistory" 
    BLOGGER = "blogger"  # 구글 블로거


class LoginStatus(Enum):
    """로그인 상태"""
    NOT_LOGGED_IN = "not_logged_in"
    LOGGING_IN = "logging_in"
    LOGGED_IN = "logged_in"
    TWO_FACTOR_REQUIRED = "two_factor_required"
    LOGIN_FAILED = "login_failed"


@dataclass
class BlogCredentials:
    """블로그 로그인 자격증명"""
    platform: BlogPlatform
    username: str
    password: str
    
    def validate(self) -> None:
        """자격증명 유효성 검사"""
        if not self.username or not self.password:
            raise ValueError("아이디와 비밀번호는 필수입니다")
        
        if len(self.username.strip()) == 0:
            raise ValueError("아이디를 입력해주세요")
            
        if len(self.password.strip()) == 0:
            raise ValueError("비밀번호를 입력해주세요")


@dataclass
class BlogSession:
    """블로그 세션 정보"""
    platform: BlogPlatform
    username: str
    status: LoginStatus
    created_at: datetime
    last_activity: Optional[datetime] = None
    session_id: Optional[str] = None


@dataclass
class BlogPost:
    """블로그 포스트 데이터"""
    title: str
    content: str
    tags: List[str]
    category: Optional[str] = None
    is_public: bool = True
    allow_comments: bool = True
    thumbnail_url: Optional[str] = None
    

def init_blog_automation_db(conn):
    """블로그 자동화 데이터베이스 테이블 초기화"""
    cursor = conn.cursor()
    
    # 블로그 세션 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blog_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            username TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            last_activity TIMESTAMP,
            session_data TEXT,
            created_date DATE DEFAULT (date('now'))
        )
    """)
    
    # 블로그 포스트 히스토리 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blog_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            tags TEXT,
            category TEXT,
            is_public BOOLEAN DEFAULT 1,
            allow_comments BOOLEAN DEFAULT 1,
            thumbnail_url TEXT,
            post_url TEXT,
            published_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 블로그 자격증명 저장 테이블 (암호화된 상태로 저장)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blog_credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            username TEXT NOT NULL,
            encrypted_password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(platform, username)
        )
    """)
    
    conn.commit()


# ============================================
# 데이터 처리 및 검증 함수들
# ============================================

def validate_and_create_credentials(platform: str, username: str, password: str) -> BlogCredentials:
    """자격증명 유효성 검사 및 생성"""
    from src.foundation.exceptions import ValidationError
    
    try:
        # 플랫폼 변환
        if platform == "네이버":
            blog_platform = BlogPlatform.NAVER
        elif platform == "다음":
            blog_platform = BlogPlatform.TISTORY
        elif platform == "구글":
            blog_platform = BlogPlatform.BLOGGER
        else:
            raise ValidationError(f"지원하지 않는 플랫폼: {platform}")
        
        credentials = BlogCredentials(
            platform=blog_platform,
            username=username.strip(),
            password=password.strip()
        )
        
        credentials.validate()
        return credentials
        
    except ValueError as e:
        raise ValidationError(str(e))


def create_blog_session(platform: BlogPlatform, username: str) -> BlogSession:
    """새 블로그 세션 생성"""
    from datetime import datetime
    
    session = BlogSession(
        platform=platform,
        username=username,
        status=LoginStatus.NOT_LOGGED_IN,
        created_at=datetime.now()
    )
    
    return session


def save_blog_session(session: BlogSession) -> None:
    """블로그 세션을 데이터베이스에 저장"""
    from src.foundation.db import get_db
    from src.foundation.logging import get_logger
    
    logger = get_logger("blog_automation.models")
    
    if not session:
        return
    
    try:
        with get_db().get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO blog_sessions 
                (platform, username, status, created_at, last_activity)
                VALUES (?, ?, ?, ?, ?)
            """, (
                session.platform.value,
                session.username,
                session.status.value,
                session.created_at,
                session.last_activity
            ))
            conn.commit()
            logger.info("블로그 세션 저장 완료")
            
    except Exception as e:
        logger.error(f"세션 저장 실패: {e}")


def save_blog_credentials(credentials: BlogCredentials) -> None:
    """로그인 자격증명 저장 (암호화)"""
    from src.foundation.db import get_db
    from src.foundation.exceptions import BusinessError
    from src.foundation.logging import get_logger
    from src.toolbox.text_utils import encrypt_password
    from datetime import datetime
    
    logger = get_logger("blog_automation.models")
    
    try:
        encrypted_password = encrypt_password(credentials.password)
        
        with get_db().get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO blog_credentials 
                (platform, username, encrypted_password, updated_at)
                VALUES (?, ?, ?, ?)
            """, (
                credentials.platform.value,
                credentials.username,
                encrypted_password,
                datetime.now()
            ))
            conn.commit()
            logger.info(f"블로그 자격증명 저장: {credentials.platform.value} - {credentials.username}")
            
    except Exception as e:
        logger.error(f"자격증명 저장 실패: {e}")
        raise BusinessError(f"자격증명 저장 실패: {str(e)}")


def load_saved_blog_credentials(platform: BlogPlatform) -> Optional[tuple]:
    """저장된 자격증명 로드"""
    from src.foundation.db import get_db
    from src.foundation.logging import get_logger
    from src.toolbox.text_utils import decrypt_password
    from typing import Optional
    
    logger = get_logger("blog_automation.models")
    
    try:
        with get_db().get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT username, encrypted_password 
                FROM blog_credentials 
                WHERE platform = ?
                ORDER BY updated_at DESC
                LIMIT 1
            """, (platform.value,))
            
            result = cursor.fetchone()
            if result:
                username, encrypted_password = result
                password = decrypt_password(encrypted_password)
                return username, password
            
            return None
            
    except Exception as e:
        logger.error(f"자격증명 로드 실패: {e}")
        return None


def delete_saved_blog_credentials(platform: BlogPlatform, username: str) -> None:
    """저장된 자격증명 삭제"""
    from src.foundation.db import get_db
    from src.foundation.logging import get_logger
    
    logger = get_logger("blog_automation.models")
    
    try:
        with get_db().get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM blog_credentials 
                WHERE platform = ? AND username = ?
            """, (platform.value, username))
            conn.commit()
            logger.info(f"자격증명 삭제: {platform.value} - {username}")
            
    except Exception as e:
        logger.error(f"자격증명 삭제 실패: {e}")