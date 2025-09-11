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