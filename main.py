"""
블로그 자동화 시스템 메인 진입점
블로그 자동화 기능만 로드하여 애플리케이션 시작
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.foundation.logging import get_logger
from src.foundation.config import config_manager

logger = get_logger("main")


def load_features(app):
    """블로그 자동화 기능 모듈 로드 및 등록"""
    try:
        logger.info("블로그 자동화 모듈 로드 시작")
        
        # 블로그 자동화 모듈이 이미 앱에서 동적으로 로드되므로
        # 여기서는 추가 초기화만 수행
        logger.info("블로그 자동화 모듈은 UI에서 동적 로드됩니다")
        
        logger.info("기능 모듈 로드 완료")
        
    except Exception as e:
        import traceback
        logger.error(f"핵심 기능 모듈 로드 실패: {e}")
        logger.error(f"상세 오류: {traceback.format_exc()}")
        raise


def main():
    """메인 함수"""
    try:
        logger.info("블로그 자동화 시스템 시작")
        
        # 1단계: 공용 DB 초기화
        from src.foundation.db import init_db
        init_db()  # 공용 DB 초기화
        logger.info("공용 데이터베이스 초기화 완료")
        
        # 2단계: 설정 로드 (SQLite3에서)
        api_config = config_manager.load_api_config()
        app_config = config_manager.load_app_config()
        logger.info("설정 로드 완료 (SQLite3 기반)")
        
        # 3단계: 데스크톱 앱 실행
        from src.desktop.app import run_app
        run_app(load_features)
        
    except Exception as e:
        logger.error(f"애플리케이션 시작 실패: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()