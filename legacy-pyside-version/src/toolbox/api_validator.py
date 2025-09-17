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
    need_text_ai: bool = False,
    need_image_ai: bool = False
) -> bool:
    """
    API 설정 요구사항 확인 및 사용자 안내
    
    Args:
        parent: 부모 위젯 (다이얼로그 표시용)
        action_name: 작업명 (예: "키워드 검색", "순위 확인", "블로그 글 생성")
        need_developer: 네이버 개발자 API 필요 여부
        need_searchad: 네이버 검색광고 API 필요 여부
        need_text_ai: 글 작성 AI API 필요 여부
        need_image_ai: 이미지 생성 AI API 필요 여부
        
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
        
        if need_text_ai:
            # 현재 설정된 글 작성 AI 모델에 따라 검증
            current_model = getattr(api_config, 'current_text_ai_model', '')
            text_ai_valid = False
            
            if current_model and current_model != "모델을 선택하세요":
                # 설정된 모델에 맞는 API 키가 있는지 확인
                if "GPT" in current_model:
                    text_ai_valid = bool(getattr(api_config, 'openai_api_key', '').strip())
                elif "Claude" in current_model:
                    text_ai_valid = bool(getattr(api_config, 'claude_api_key', '').strip())
                elif "Gemini" in current_model:
                    text_ai_valid = bool(getattr(api_config, 'gemini_api_key', '').strip())
                else:
                    # 알 수 없는 모델인 경우 모든 글 작성 AI API 키 중 하나라도 있으면 통과
                    text_ai_valid = any([
                        getattr(api_config, 'openai_api_key', '').strip(),
                        getattr(api_config, 'claude_api_key', '').strip(),
                        getattr(api_config, 'gemini_api_key', '').strip()
                    ])
            
            api_status.append(f"글작성AI={text_ai_valid}")
            if not text_ai_valid:
                if current_model and current_model != "모델을 선택하세요":
                    missing_apis.append(f"글 작성 AI API ({current_model})")
                else:
                    missing_apis.append("글 작성 AI API (모델 선택 및 API 키 설정 필요)")
        
        if need_image_ai:
            # 현재 설정된 이미지 생성 AI 모델에 따라 검증
            current_model = getattr(api_config, 'current_image_ai_model', '')
            image_ai_valid = False
            
            if current_model and current_model != "모델을 선택하세요":
                # 설정된 모델에 맞는 API 키가 있는지 확인
                if "DALL-E" in current_model:
                    image_ai_valid = bool(getattr(api_config, 'dalle_api_key', '').strip())
                elif "Imagen" in current_model:
                    image_ai_valid = bool(getattr(api_config, 'imagen_api_key', '').strip())
                else:
                    # 알 수 없는 모델인 경우 모든 이미지 생성 AI API 키 중 하나라도 있으면 통과
                    image_ai_valid = any([
                        getattr(api_config, 'dalle_api_key', '').strip(),
                        getattr(api_config, 'imagen_api_key', '').strip()
                    ])
            
            api_status.append(f"이미지AI={image_ai_valid}")
            if not image_ai_valid:
                if current_model and current_model != "모델을 선택하세요":
                    missing_apis.append(f"이미지 생성 AI API ({current_model})")
                else:
                    missing_apis.append("이미지 생성 AI API (모델 선택 및 API 키 설정 필요)")
        
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

# 네이버 API 전용 함수들
def check_developer_api_only(parent: QWidget, action_name: str) -> bool:
    """네이버 개발자 API만 필요한 작업용 (검색, 블로그 등)"""
    return check_api_requirements(parent, action_name, need_developer=True)


def check_searchad_api_only(parent: QWidget, action_name: str) -> bool:
    """네이버 검색광고 API만 필요한 작업용 (월 검색량 등)"""
    return check_api_requirements(parent, action_name, need_searchad=True)


def check_developer_and_searchad_apis(parent: QWidget, action_name: str) -> bool:
    """네이버 개발자 API + 검색광고 API 필요한 작업용 (종합 분석)"""
    return check_api_requirements(parent, action_name, need_developer=True, need_searchad=True)


# AI API 전용 함수들
def check_text_ai_only(parent: QWidget, action_name: str) -> bool:
    """글 작성 AI API만 필요한 작업용 (블로그 글 생성)"""
    return check_api_requirements(parent, action_name, need_text_ai=True)


def check_image_ai_only(parent: QWidget, action_name: str) -> bool:
    """이미지 생성 AI API만 필요한 작업용 (이미지 생성)"""
    return check_api_requirements(parent, action_name, need_image_ai=True)


def check_both_ai_apis(parent: QWidget, action_name: str) -> bool:
    """글 작성 + 이미지 생성 AI API 모두 필요한 작업용 (완전 자동 블로그 생성)"""
    return check_api_requirements(parent, action_name, need_text_ai=True, need_image_ai=True)


# 종합 함수들
def check_blog_creation_apis(parent: QWidget, action_name: str) -> bool:
    """블로그 작성에 필요한 모든 API (네이버 개발자 + 글 작성 AI)"""
    return check_api_requirements(parent, action_name, need_developer=True, need_text_ai=True)


def check_full_blog_automation_apis(parent: QWidget, action_name: str) -> bool:
    """완전 블로그 자동화에 필요한 모든 API (네이버 개발자 + 검색광고 + 글 작성 AI + 이미지 생성 AI)"""
    return check_api_requirements(
        parent, action_name, 
        need_developer=True, 
        need_searchad=True, 
        need_text_ai=True, 
        need_image_ai=True
    )


def check_content_analysis_apis(parent: QWidget, action_name: str) -> bool:
    """콘텐츠 분석에 필요한 API (네이버 개발자 + 검색광고)"""
    return check_api_requirements(parent, action_name, need_developer=True, need_searchad=True)


# 레거시 호환성 함수 (기존 코드와의 호환성 유지)
def check_ai_api_only(parent: QWidget, action_name: str) -> bool:
    """레거시: 글 작성 AI API만 필요한 작업용 (구 check_ai_api_only와 호환)"""
    return check_text_ai_only(parent, action_name)


def check_all_apis(parent: QWidget, action_name: str) -> bool:
    """레거시: 모든 API 필요한 작업용 (구 check_all_apis와 호환)"""
    return check_full_blog_automation_apis(parent, action_name)