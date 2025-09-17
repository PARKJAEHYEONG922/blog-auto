"""
서로이웃 추가 모듈의 데이터 모델
"""
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
from datetime import datetime


class LoginStatus(Enum):
    """로그인 상태"""
    NOT_LOGGED_IN = "not_logged_in"
    LOGGING_IN = "logging_in"
    LOGGED_IN = "logged_in"
    LOGIN_FAILED = "login_failed"


class NeighborAddStatus(Enum):
    """서로이웃 추가 상태"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    ALREADY_NEIGHBOR = "already_neighbor"
    ALREADY_REQUESTED = "already_requested"  # 이미 신청 진행 중
    DISABLED = "disabled"  # 5000명 꽉참 또는 차단
    DAILY_LIMIT_REACHED = "daily_limit_reached"  # 하루 100명 제한 도달
    NEIGHBOR_LIMIT_EXCEEDED = "neighbor_limit_exceeded"  # 상대방 5000명 초과


@dataclass
class LoginCredentials:
    """네이버 로그인 정보"""
    username: str
    password: str


@dataclass
class BloggerInfo:
    """블로거 정보"""
    blog_id: str
    blog_name: str
    blog_url: str
    profile_image_url: Optional[str] = None
    description: Optional[str] = None


@dataclass
class NeighborAddRequest:
    """서로이웃 추가 요청"""
    blogger_info: BloggerInfo
    message: str
    status: NeighborAddStatus = NeighborAddStatus.PENDING
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class SearchKeyword:
    """검색 키워드 정보"""
    keyword: str
    max_results: int = 50
    search_date: datetime = None
    
    def __post_init__(self):
        if self.search_date is None:
            self.search_date = datetime.now()


@dataclass
class NeighborAddSession:
    """서로이웃 추가 세션 정보"""
    session_id: str
    login_status: LoginStatus = LoginStatus.NOT_LOGGED_IN
    current_keyword: Optional[SearchKeyword] = None
    found_bloggers: List[BloggerInfo] = None
    neighbor_requests: List[NeighborAddRequest] = None
    default_message: str = "안녕하세요! 서로이웃 해요 :)"
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.found_bloggers is None:
            self.found_bloggers = []
        if self.neighbor_requests is None:
            self.neighbor_requests = []


# 데이터베이스 테이블 DDL
NEIGHBOR_ADD_DDL = """
CREATE TABLE IF NOT EXISTS neighbor_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    login_status TEXT NOT NULL DEFAULT 'not_logged_in',
    keyword TEXT,
    max_results INTEGER DEFAULT 50,
    default_message TEXT DEFAULT '안녕하세요! 서로이웃 해요 :)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS found_bloggers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    blog_id TEXT NOT NULL,
    blog_name TEXT NOT NULL,
    blog_url TEXT NOT NULL,
    profile_image_url TEXT,
    description TEXT,
    found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES neighbor_sessions(session_id),
    UNIQUE(session_id, blog_id)
);

CREATE TABLE IF NOT EXISTS neighbor_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    blog_id TEXT NOT NULL,
    message TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES neighbor_sessions(session_id),
    FOREIGN KEY (blog_id) REFERENCES found_bloggers(blog_id)
);

CREATE TABLE IF NOT EXISTS saved_credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_encrypted TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def init_neighbor_db(db_conn):
    """서로이웃 추가 관련 테이블 초기화"""
    cursor = db_conn.cursor()
    cursor.executescript(NEIGHBOR_ADD_DDL)
    db_conn.commit()