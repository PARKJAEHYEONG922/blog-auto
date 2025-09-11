"""
API 설정 검증 유틸리티
모든 모듈에서 공용으로 사용할 수 있는 API 확인 함수
"""
from typing import Optional
from PySide6.QtWidgets import QWidget

from src.foundation.logging import get_logger

logger = get_logger("toolbox.api_validator")


def check_api_requirements(
    parent: QWidget,
    action_name: str,
    need_developer: bool = False,
    need_searchad: bool = False, 
    need_ai: bool = False
) -> bool:
    """
    API 설정 요구사항 확인 및 사용자 안내
    
    Args:
        parent: 부모 위젯 (다이얼로그 표시용)
        action_name: 작업명 (예: "키워드 검색", "순위 확인", "파워링크 분석")
        need_developer: 네이버 개발자 API 필요 여부
        need_searchad: 네이버 검색광고 API 필요 여부
        need_ai: OpenAI API 필요 여부
        
    Returns:
        bool: API 요구사항 충족 여부 (True: 진행 가능, False: API 설정 필요)
    """
    try:
        from src.foundation.config import config_manager
        api_config = config_manager.load_api_config()
        
        # 필요한 API 확인
        missing_apis = []
        api_status = []
        
        if need_developer:
            is_valid = api_config.is_shopping_valid()
            api_status.append(f"개발자API={is_valid}")
            if not is_valid:
                missing_apis.append("네이버 개발자 API")
        
        if need_searchad:
            is_valid = api_config.is_searchad_valid()
            api_status.append(f"검색광고API={is_valid}")
            if not is_valid:
                missing_apis.append("네이버 검색광고 API")
        
        if need_ai:
            # 현재 설정된 AI 모델에 따라 검증
            current_model = getattr(api_config, 'current_ai_model', '')
            ai_valid = False
            
            if current_model and current_model != "AI 제공자를 선택하세요":
                # 설정된 모델에 맞는 API 키가 있는지 확인
                if "openai" in current_model.lower() or "gpt" in current_model.lower():
                    ai_valid = bool(getattr(api_config, 'openai_api_key', '').strip())
                elif "claude" in current_model.lower():
                    ai_valid = bool(getattr(api_config, 'claude_api_key', '').strip())
                elif "gemini" in current_model.lower():
                    ai_valid = bool(getattr(api_config, 'gemini_api_key', '').strip())
                else:
                    # 알 수 없는 모델인 경우 모든 AI API 키 중 하나라도 있으면 통과
                    ai_valid = any([
                        getattr(api_config, 'openai_api_key', '').strip(),
                        getattr(api_config, 'claude_api_key', '').strip(),
                        getattr(api_config, 'gemini_api_key', '').strip()
                    ])
            
            api_status.append(f"AI API={ai_valid}")
            if not ai_valid:
                if current_model and current_model != "AI 제공자를 선택하세요":
                    missing_apis.append(f"AI API ({current_model}에 대한 API 키)")
                else:
                    missing_apis.append("AI API (모델 선택 및 API 키)")
        
        # API 체크 로그 출력
        logger.info(f"{action_name} API 체크: {', '.join(api_status) if api_status else '요구사항 없음'}")
        
        # 모든 요구사항을 충족하면 성공
        if not missing_apis:
            return True
        
        # 필요한 API가 없으면 사용자에게 안내
        _show_api_required_dialog(parent, action_name, missing_apis)
        return False
        
    except Exception as e:
        logger.error(f"API 설정 확인 중 오류: {e}")
        return False


def _show_api_required_dialog(parent: QWidget, action_name: str, missing_apis: list) -> None:
    """API 설정 필요 다이얼로그 표시"""
    try:
        from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
        
        dialog = ModernConfirmDialog(
            parent,
            title="API 설정 필요",
            message=f"{action_name}을(를) 위해서는 다음 API 설정이 필요합니다:\n\n• {chr(10).join(missing_apis)}\n\nAPI 설정 화면으로 이동하시겠습니까?",
            confirm_text="API 설정하러가기",
            cancel_text="취소",
            icon="🔑"
        )
        
        if dialog.exec():
            _open_api_settings_dialog(parent)
            
    except Exception as e:
        logger.error(f"API 설정 다이얼로그 표시 오류: {e}")


def _open_api_settings_dialog(parent: QWidget) -> None:
    """API 설정 다이얼로그 열기"""
    try:
        from src.desktop.api_dialog import APISettingsDialog
        api_dialog = APISettingsDialog(parent)
        api_dialog.exec()
    except Exception as e:
        logger.error(f"API 설정 다이얼로그 열기 오류: {e}")


# 편의 함수들 - 자주 사용되는 조합들
def check_developer_api_only(parent: QWidget, action_name: str) -> bool:
    """네이버 개발자 API만 필요한 작업용"""
    return check_api_requirements(parent, action_name, need_developer=True)


def check_developer_and_searchad_apis(parent: QWidget, action_name: str) -> bool:
    """네이버 개발자 API + 검색광고 API 필요한 작업용"""
    return check_api_requirements(parent, action_name, need_developer=True, need_searchad=True)


def check_searchad_api_only(parent: QWidget, action_name: str) -> bool:
    """네이버 검색광고 API만 필요한 작업용"""
    return check_api_requirements(parent, action_name, need_searchad=True)


def check_ai_api_only(parent: QWidget, action_name: str) -> bool:
    """AI API만 필요한 작업용"""
    return check_api_requirements(parent, action_name, need_ai=True)


def check_all_apis(parent: QWidget, action_name: str) -> bool:
    """모든 API (개발자 + 검색광고 + AI) 필요한 작업용"""
    return check_api_requirements(parent, action_name, need_developer=True, need_searchad=True, need_ai=True)