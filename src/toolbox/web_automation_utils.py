"""
웹 자동화 관련 유틸리티 함수들
"""
from functools import wraps
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from src.foundation.logging import get_logger
from src.foundation.exceptions import BusinessError

logger = get_logger("toolbox.web_automation_utils")


def handle_web_automation_errors(operation_name: str):
    """웹 자동화 오류 처리 데코레이터 (중복 코드 제거용)"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except TimeoutException as e:
                logger.error(f"{operation_name} 타임아웃: {e}")
                raise BusinessError(f"{operation_name} 실패 (타임아웃): 요소를 찾을 수 없습니다")
            except NoSuchElementException as e:
                logger.error(f"{operation_name} 요소 없음: {e}")
                raise BusinessError(f"{operation_name} 실패: 필요한 요소를 찾을 수 없습니다")
            except Exception as e:
                logger.error(f"{operation_name} 실패: {e}")
                raise BusinessError(f"{operation_name} 실패: {str(e)}")
        return wrapper
    return decorator