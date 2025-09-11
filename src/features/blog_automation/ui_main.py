"""
블로그 자동화 모듈의 메인 UI
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QLineEdit, QCheckBox, QFrame
)
from PySide6.QtCore import Qt
import traceback

from src.foundation.logging import get_logger
from src.toolbox.ui_kit.components import (
    ModernButton, ModernLineEdit, ModernCard, 
    ModernPrimaryButton, ModernSuccessButton, ModernHelpButton
)
from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog, ModernScrollableDialog
from src.toolbox.ui_kit.modern_style import ModernStyle
from src.toolbox.ui_kit import tokens
from src.foundation.exceptions import BusinessError, ValidationError

from .service import BlogAutomationService
from .models import BlogPlatform, LoginStatus
from .worker import create_blog_login_worker, WorkerThread
from .ui_table import BlogWriteTableUI


class UIDialogHelper:
    """UI 다이얼로그 헬퍼 클래스 (중복 코드 제거용)"""
    
    @staticmethod
    def show_error_dialog(parent, title: str = "오류", message: str = "", icon: str = "❌"):
        """오류 다이얼로그 표시"""
        dialog = ModernConfirmDialog(
            parent,
            title=title,
            message=message,
            confirm_text="확인",
            cancel_text=None,
            icon=icon
        )
        return dialog.exec()
    
    @staticmethod
    def show_success_dialog(parent, title: str = "성공", message: str = "", icon: str = "✅"):
        """성공 다이얼로그 표시"""
        dialog = ModernConfirmDialog(
            parent,
            title=title,
            message=message,
            confirm_text="확인",
            cancel_text=None,
            icon=icon
        )
        return dialog.exec()
    
    @staticmethod
    def show_warning_dialog(parent, title: str = "경고", message: str = "", icon: str = "⚠️"):
        """경고 다이얼로그 표시"""
        dialog = ModernConfirmDialog(
            parent,
            title=title,
            message=message,
            confirm_text="확인",
            cancel_text=None,
            icon=icon
        )
        return dialog.exec()
    
    @staticmethod
    def show_info_dialog(parent, title: str = "알림", message: str = "", icon: str = "ℹ️"):
        """정보 다이얼로그 표시"""
        dialog = ModernConfirmDialog(
            parent,
            title=title,
            message=message,
            confirm_text="확인",
            cancel_text=None,
            icon=icon
        )
        return dialog.exec()

logger = get_logger("blog_automation.ui_main")


class BlogAutomationMainUI(QWidget):
    """블로그 자동화 메인 UI"""
    
    def __init__(self):
        super().__init__()
        self.service = BlogAutomationService()
        self.current_platform = None
        self.is_logged_in = False
        
        # 워커 관련
        self.login_worker = None
        self.login_thread = None
        
        self.setup_ui()
        self.setup_styles()
        self.reset_ui_state()
    
    def setup_ui(self):
        """UI 구성"""
        main_layout = QVBoxLayout()
        margin = tokens.GAP_16
        spacing = tokens.GAP_10
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)
        
        # 헤더 (제목 + 사용법 버튼)
        self.setup_header(main_layout)
        
        # 메인 콘텐츠 영역 (좌우 분할)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(tokens.GAP_20)
        
        # 왼쪽 패널 (상태 + 플랫폼 선택 + 로그인)
        left_panel = self.create_left_panel()
        content_layout.addWidget(left_panel, 1)
        
        # 오른쪽 패널 (블로그 분석 및 작성)
        right_panel = self.create_right_panel()
        content_layout.addWidget(right_panel, 2)
        
        main_layout.addLayout(content_layout, 1)
        self.setLayout(main_layout)
    
    def setup_header(self, layout):
        """헤더 섹션 (제목 + AI 설정 정보 + 사용법 버튼)"""
        header_layout = QHBoxLayout()
        
        # 제목과 사용법 버튼을 함께 배치
        title_help_layout = QHBoxLayout()
        title_help_layout.setSpacing(tokens.GAP_8)
        
        # 제목
        title_label = QLabel("📝 블로그 자동화")
        title_font_size = tokens.fpx(tokens.get_font_size('title'))
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: {title_font_size}px;
                font-weight: 700;
                color: {ModernStyle.COLORS['text_primary']};
            }}
        """)
        title_help_layout.addWidget(title_label)
        
        # 사용법 버튼 (제목 바로 옆)
        help_button = ModernHelpButton("❓ 사용법")
        help_button.clicked.connect(self.show_usage_help)
        title_help_layout.addWidget(help_button)
        
        header_layout.addLayout(title_help_layout)
        header_layout.addStretch()
        
        # AI 설정 정보 표시 (한 줄로)
        self.ai_info_label = QLabel("")
        self.ai_info_label.setStyleSheet(f"""
            QLabel {{
                font-size: {tokens.fpx(tokens.get_font_size('small'))}px;
                color: {ModernStyle.COLORS['text_secondary']};
                background-color: {ModernStyle.COLORS['bg_muted']};
                padding: 6px 12px;
                border-radius: {tokens.RADIUS_SM}px;
                border: 1px solid {ModernStyle.COLORS['border']};
            }}
        """)
        header_layout.addWidget(self.ai_info_label)
        
        # 초기 AI 정보 로드
        self.update_ai_info_display()
        
        layout.addLayout(header_layout)
    
    def create_left_panel(self):
        """왼쪽 패널 생성 (상태 + 플랫폼 선택 + 로그인)"""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(tokens.GAP_16)
        
        # 상태 표시 카드
        self.status_card = self.create_status_card()
        layout.addWidget(self.status_card)
        
        # 플랫폼 선택 + 로그인 통합 카드
        platform_login_card = self.create_platform_login_card()
        layout.addWidget(platform_login_card)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
    
    def create_right_panel(self):
        """오른쪽 패널 생성 (블로그 분석 및 작성)"""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(tokens.GAP_16)
        
        # 블로그 글쓰기 테이블 UI 추가
        self.blog_table_ui = BlogWriteTableUI(parent=self)
        layout.addWidget(self.blog_table_ui)
        
        panel.setLayout(layout)
        return panel
    
    def create_platform_login_card(self) -> ModernCard:
        """플랫폼 선택 + 로그인 통합 카드 생성"""
        card = ModernCard("🔑 블로그 플랫폼 로그인")
        layout = QVBoxLayout()
        
        # 플랫폼 선택 드롭박스
        platform_layout = QHBoxLayout()
        platform_layout.addWidget(QLabel("플랫폼:"))
        
        self.platform_combo = QComboBox()
        self.platform_combo.addItems([
            "네이버 (네이버블로그)",
            "다음 (티스토리)", 
            "구글 (블로거)"
        ])
        self.platform_combo.setStyleSheet(f"""
            QComboBox {{
                padding: {tokens.GAP_8}px {tokens.GAP_12}px;
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: {tokens.RADIUS_SM}px;
                background-color: {ModernStyle.COLORS['bg_card']};
                color: {ModernStyle.COLORS['text_primary']};
                font-size: 14px;
                min-height: 20px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {ModernStyle.COLORS['text_secondary']};
                margin-right: 5px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {ModernStyle.COLORS['bg_card']};
                border: 1px solid {ModernStyle.COLORS['border']};
                selection-background-color: {ModernStyle.COLORS['primary']};
                selection-color: white;
            }}
        """)
        self.platform_combo.currentTextChanged.connect(self.on_platform_changed)
        platform_layout.addWidget(self.platform_combo)
        
        platform_layout.addStretch()
        layout.addLayout(platform_layout)
        
        # 플랫폼 설명
        self.platform_description = QLabel()
        self.platform_description.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_muted']};
                font-size: 12px;
                padding: {tokens.GAP_8}px;
                background-color: {ModernStyle.COLORS['bg_muted']};
                border-radius: {tokens.RADIUS_SM}px;
            }}
        """)
        self.platform_description.setWordWrap(True)
        layout.addWidget(self.platform_description)
        
        # 구분선
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet(f"QFrame {{ color: {ModernStyle.COLORS['border']}; }}")
        layout.addWidget(separator)
        
        # 로그인 섹션
        login_section_label = QLabel("🔑 로그인 정보")
        login_section_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_primary']};
                font-size: 14px;
                font-weight: 600;
                margin-top: {tokens.GAP_8}px;
                margin-bottom: {tokens.GAP_8}px;
            }}
        """)
        layout.addWidget(login_section_label)
        
        # 아이디 입력
        id_layout = QHBoxLayout()
        id_layout.addWidget(QLabel("아이디:"))
        self.username_input = ModernLineEdit()
        self.username_input.setPlaceholderText("아이디를 입력하세요")
        id_layout.addWidget(self.username_input)
        layout.addLayout(id_layout)
        
        # 비밀번호 입력
        pw_layout = QHBoxLayout()
        pw_layout.addWidget(QLabel("비밀번호:"))
        self.password_input = ModernLineEdit()
        self.password_input.setPlaceholderText("비밀번호를 입력하세요")
        self.password_input.setEchoMode(QLineEdit.Password)
        pw_layout.addWidget(self.password_input)
        layout.addLayout(pw_layout)
        
        # 로그인 정보 저장 체크박스
        self.save_credentials_checkbox = QCheckBox("로그인 정보 저장 (다음에도 사용)")
        self.save_credentials_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {ModernStyle.COLORS['text_secondary']};
                font-size: 12px;
                spacing: 5px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: 3px;
                background-color: {ModernStyle.COLORS['bg_card']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {ModernStyle.COLORS['primary']};
                border-color: {ModernStyle.COLORS['primary']};
            }}
        """)
        layout.addWidget(self.save_credentials_checkbox)
        
        # 로그인 버튼
        self.login_button = ModernPrimaryButton("로그인")
        self.login_button.clicked.connect(self.on_login_clicked)
        layout.addWidget(self.login_button)
        
        # 글쓰기 버튼 (로그인 후 활성화)
        self.write_button = ModernSuccessButton("📝 글쓰기 페이지 열기")
        self.write_button.clicked.connect(self.on_write_clicked)
        self.write_button.setEnabled(False)  # 초기에는 비활성화
        layout.addWidget(self.write_button)
        
        card.setLayout(layout)
        return card
    
    def create_status_card(self) -> ModernCard:
        """상태 표시 카드 생성"""
        card = ModernCard("📊 상태")
        layout = QVBoxLayout()
        
        # 현재 상태
        self.status_label = QLabel("대기 중...")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_primary']};
                font-size: 14px;
                font-weight: 600;
                padding: {tokens.GAP_8}px;
                background-color: {ModernStyle.COLORS['bg_muted']};
                border-radius: {tokens.RADIUS_SM}px;
                border-left: 3px solid {ModernStyle.COLORS['primary']};
            }}
        """)
        layout.addWidget(self.status_label)
        
        card.setLayout(layout)
        return card
    
    
    def setup_styles(self):
        """스타일 설정"""
        pass  # 개별 컴포넌트에서 스타일 적용됨
    
    def reset_ui_state(self):
        """UI 상태 초기화"""
        self.current_platform = None
        self.is_logged_in = False
        self.status_label.setText("대기 중...")
        
        # 플랫폼 선택에 따른 초기 설정
        self.on_platform_changed(self.platform_combo.currentText())
        
        # 저장된 로그인 정보 로드
        self.load_saved_credentials()
        
        # AI 설정 정보 업데이트 (table UI에서 로드 후)
        if hasattr(self, 'blog_table_ui'):
            # 약간의 지연 후 AI 정보 업데이트 (UI 초기화 완료 후)
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, self.update_ai_info_display)
    
    def on_platform_changed(self, platform_text: str):
        """플랫폼 변경 이벤트"""
        try:
            logger.info(f"플랫폼 변경: {platform_text}")
            
            # 플랫폼 매핑
            if "네이버" in platform_text:
                self.current_platform = BlogPlatform.NAVER
                description = "✅ 완전 구현됨 - 자동 로그인 및 포스팅 지원"
            elif "다음" in platform_text or "티스토리" in platform_text:
                self.current_platform = BlogPlatform.TISTORY
                description = "🚧 준비 중 - 아직 구현되지 않았습니다"
            elif "구글" in platform_text or "블로거" in platform_text:
                self.current_platform = BlogPlatform.BLOGGER
                description = "🚧 준비 중 - 아직 구현되지 않았습니다"
            else:
                self.current_platform = None
                description = "플랫폼을 선택해주세요"
            
            self.platform_description.setText(description)
            
            # 로그인 섹션 활성화/비활성화
            if self.current_platform == BlogPlatform.NAVER:
                self.username_input.setEnabled(True)
                self.password_input.setEnabled(True)
                self.save_credentials_checkbox.setEnabled(True)
                self.login_button.setEnabled(True)
                self.username_input.setPlaceholderText("네이버 아이디")
                self.password_input.setPlaceholderText("네이버 비밀번호")
            else:
                self.username_input.setEnabled(False)
                self.password_input.setEnabled(False)
                self.save_credentials_checkbox.setEnabled(False)
                self.login_button.setEnabled(False)
                self.username_input.setPlaceholderText("아직 지원되지 않습니다")
                self.password_input.setPlaceholderText("아직 지원되지 않습니다")
            
            # 저장된 자격증명 로드
            self.load_saved_credentials()
            
        except Exception as e:
            logger.error(f"플랫폼 변경 처리 오류: {e}")
    
    def load_saved_credentials(self):
        """저장된 로그인 정보 로드"""
        try:
            if not self.current_platform:
                return
            
            credentials = self.service.load_saved_credentials(self.current_platform)
            if credentials:
                username, password = credentials
                self.username_input.setText(username)
                self.password_input.setText(password)
                self.save_credentials_checkbox.setChecked(True)
                logger.info(f"저장된 로그인 정보 로드됨: {username}")
                
        except Exception as e:
            logger.error(f"로그인 정보 로드 실패: {e}")
    
    def on_login_clicked(self):
        """로그인 버튼 클릭"""
        try:
            username = self.username_input.text().strip()
            password = self.password_input.text().strip()
            platform_text = self.platform_combo.currentText()
            
            if not username or not password:
                UIDialogHelper.show_warning_dialog(
                    self,
                    title="입력 오류",
                    message="아이디와 비밀번호를 모두 입력해주세요."
                )
                return
            
            if not self.current_platform:
                UIDialogHelper.show_warning_dialog(
                    self,
                    title="플랫폼 선택 오류",
                    message="플랫폼을 선택해주세요."
                )
                return
            
            # 아직 구현되지 않은 플랫폼 체크
            if self.current_platform != BlogPlatform.NAVER:
                dialog = ModernConfirmDialog(
                    self,
                    title="구현 예정",
                    message=f"{platform_text}는 아직 구현되지 않았습니다.\n현재는 네이버 블로그만 지원됩니다.",
                    confirm_text="확인",
                    cancel_text=None,
                    icon="🚧"
                )
                dialog.exec()
                return
            
            # 자격증명 유효성 검사
            platform_key = platform_text.split()[0]  # "네이버", "다음", "구글"
            credentials = self.service.validate_credentials(platform_key, username, password)
            
            # 비동기 로그인 시작
            self.start_async_login(credentials, platform_text)
            
        except ValidationError as e:
            self.login_button.setText("로그인")
            self.login_button.setEnabled(True)
            dialog = ModernConfirmDialog(
                self,
                title="입력 오류",
                message=str(e),
                confirm_text="확인",
                cancel_text=None,
                icon="⚠️"
            )
            dialog.exec()
            
        except Exception as e:
            logger.error(f"로그인 오류: {e}")
            self.login_button.setText("로그인")
            self.login_button.setEnabled(True)
            self.status_label.setText("로그인 오류")
            
            dialog = ModernConfirmDialog(
                self,
                title="오류",
                message=f"로그인 중 오류가 발생했습니다:\n{str(e)}",
                confirm_text="확인",
                cancel_text=None,
                icon="❌"
            )
            dialog.exec()
    
    def show_usage_help(self):
        """사용법 도움말 표시"""
        help_text = (
            "📝 블로그 자동화 사용법\n\n"
            
            "📋 사용 순서:\n"
            "1️⃣ 블로그 플랫폼 선택\n"
            "• 네이버 블로그: 완전 구현됨\n"
            "• 티스토리, 구글 블로거: 준비 중\n\n"
            
            "2️⃣ 로그인\n"
            "• 선택한 플랫폼의 아이디와 비밀번호 입력\n"
            "• 로그인 정보 저장 체크박스로 다음에도 자동 입력\n"
            "• 네이버의 경우 2차 인증이 있으면 브라우저에서 처리\n\n"
            
            "3️⃣ 자동화 기능 (준비 중)\n"
            "• 컨텐츠 자동 생성\n"
            "• 자동 포스팅\n"
            "• 스케줄링\n"
            "• SEO 최적화\n\n"
            
            "⚠️ 주의사항:\n"
            "• 현재는 로그인 기능만 구현됨\n"
            "• 네이버 블로그만 완전 지원\n"
            "• 클립보드 입력 방식으로 보안 우회\n"
            "• 브라우저 창을 임의로 닫지 말 것\n\n"
            
            "🔧 문제 해결:\n"
            "• 로그인 실패: 아이디/비밀번호 재확인\n"
            "• 2차 인증: 브라우저에서 직접 처리\n"
            "• 브라우저 오류: 프로그램 재시작"
        )
        
        dialog = ModernScrollableDialog(
            self,
            title="❓ 블로그 자동화 사용법",
            message=help_text.strip(),
            confirm_text="확인",
            cancel_text=None,
            icon="❓"
        )
        dialog.exec()
    
    def update_ai_info_display(self):
        """AI 설정 정보 표시 업데이트 (한 줄로)"""
        try:
            from src.foundation.config import config_manager
            api_config = config_manager.load_api_config()
            
            # 글 작성 AI 정보
            current_text_model = getattr(api_config, 'current_text_ai_model', '')
            if current_text_model and current_text_model != "모델을 선택하세요":
                text_ai_info = f"📝 {current_text_model}"
            else:
                # API 키가 설정되어 있는지 확인
                text_ai_configured = any([
                    getattr(api_config, 'openai_api_key', '').strip(),
                    getattr(api_config, 'claude_api_key', '').strip(),
                    getattr(api_config, 'gemini_api_key', '').strip()
                ])
                
                if text_ai_configured:
                    text_ai_info = "📝 글작성AI: 모델미선택"
                else:
                    text_ai_info = "📝 글작성AI: 미설정"
            
            # 이미지 생성 AI 정보
            current_image_model = getattr(api_config, 'current_image_ai_model', '')
            if current_image_model and current_image_model != "모델을 선택하세요":
                image_ai_info = f"🎨 {current_image_model}"
            else:
                # API 키가 설정되어 있는지 확인
                image_ai_configured = any([
                    getattr(api_config, 'dalle_api_key', '').strip(),
                    getattr(api_config, 'imagen_api_key', '').strip()
                ])
                
                if image_ai_configured:
                    image_ai_info = "🎨 이미지AI: 모델미선택"
                else:
                    image_ai_info = "🎨 이미지AI: 미설정"
            
            # 한 줄로 표시 (구분자로 | 사용)
            combined_info = f"{text_ai_info} | {image_ai_info}"
            self.ai_info_label.setText(combined_info)
            self.ai_info_label.setVisible(True)
                    
        except Exception as e:
            logger.error(f"AI 정보 표시 업데이트 오류: {e}")
            self.ai_info_label.setText("📝 글작성AI: 오류 | 🎨 이미지AI: 오류")
    
    def _on_api_settings_changed(self):
        """API 설정 변경 시 호출 (메인 앱에서 브로드캐스트)"""
        try:
            logger.info("블로그 자동화 모듈: API 설정 변경 감지")
            self.update_ai_info_display()
        except Exception as e:
            logger.error(f"API 설정 변경 처리 오류: {e}")
    
    def start_async_login(self, credentials, platform_text):
        """비동기 로그인 시작"""
        try:
            logger.info("🚀 비동기 로그인 시작")
            
            # UI 상태 업데이트
            self.login_button.setText("🔄 로그인 중...")
            self.login_button.setEnabled(False)
            self.status_label.setText("로그인 준비 중...")
            
            # 현재 플랫폼 정보 저장 (콜백에서 사용)
            self.current_platform_text = platform_text
            
            # 로그인 워커 생성
            self.login_worker = create_blog_login_worker(self.service, credentials)
            self.login_thread = WorkerThread(self.login_worker)
            
            # 시그널 연결
            self.login_worker.login_started.connect(self.on_login_started)
            self.login_worker.login_progress.connect(self.on_login_progress)
            self.login_worker.login_completed.connect(self.on_login_completed)
            self.login_worker.error_occurred.connect(self.on_login_error)
            self.login_worker.two_factor_detected.connect(self.on_two_factor_detected)
            
            # 워커 시작
            self.login_thread.start()
            logger.info("✅ 비동기 로그인 워커 시작됨")
            
        except Exception as e:
            logger.error(f"❌ 비동기 로그인 시작 실패: {e}")
            self.reset_login_ui()
            
            dialog = ModernConfirmDialog(
                self,
                title="오류",
                message=f"로그인 시작 실패: {str(e)}",
                confirm_text="확인",
                cancel_text=None,
                icon="❌"
            )
            dialog.exec()
    
    def on_login_started(self):
        """로그인 시작 시그널 처리"""
        logger.info("🔑 로그인 시작됨")
        self.status_label.setText("브라우저 시작 중...")
    
    def on_login_progress(self, message):
        """로그인 진행 상황 업데이트"""
        logger.info(f"📝 로그인 진행: {message}")
        self.status_label.setText(message)
    
    def on_login_completed(self, success: bool):
        """로그인 완료 처리"""
        try:
            if success:
                # 로그인 성공
                logger.info("✅ 비동기 로그인 성공!")
                self.is_logged_in = True
                self.login_button.setText("✅ 로그인 완료")
                self.login_button.setEnabled(False)  # 로그인 완료 후 비활성화
                self.status_label.setText(f"✅ {self.current_platform_text} 로그인 완료")
                
                # 자격증명 저장 (체크된 경우)
                if self.save_credentials_checkbox.isChecked():
                    username = self.username_input.text().strip()
                    password = self.password_input.text().strip()
                    platform_key = self.current_platform_text.split()[0]
                    credentials = self.service.validate_credentials(platform_key, username, password)
                    self.service.save_credentials(credentials)
                else:
                    # 체크 해제시 기존 저장된 정보 삭제
                    if self.current_platform:
                        username = self.username_input.text().strip()
                        self.service.delete_saved_credentials(self.current_platform, username)
                
                # 글쓰기 버튼 활성화
                self.write_button.setEnabled(True)
                
                # 성공 다이얼로그
                dialog = ModernConfirmDialog(
                    self,
                    title="로그인 성공",
                    message=f"{self.current_platform_text} 로그인이 완료되었습니다.\n이제 '글쓰기 페이지 열기' 버튼을 클릭하여 블로그 포스팅을 시작할 수 있습니다.",
                    confirm_text="확인",
                    cancel_text=None,
                    icon="🎉"
                )
                dialog.exec()
                
            else:
                # 로그인 실패
                logger.error("❌ 비동기 로그인 실패")
                self.reset_login_ui()
                self.status_label.setText("로그인 실패")
                
                dialog = ModernConfirmDialog(
                    self,
                    title="로그인 실패",
                    message="로그인에 실패했습니다.\n아이디와 비밀번호를 확인해주세요.",
                    confirm_text="확인",
                    cancel_text=None,
                    icon="❌"
                )
                dialog.exec()
                
        except Exception as e:
            logger.error(f"로그인 완료 처리 중 오류: {e}")
            self.reset_login_ui()
    
    def on_login_error(self, error_message: str):
        """로그인 오류 처리"""
        try:
            logger.error(f"❌ 로그인 오류: {error_message}")
            self.reset_login_ui()
            self.status_label.setText("로그인 오류")
            
            dialog = ModernConfirmDialog(
                self,
                title="로그인 오류",
                message=f"로그인 중 오류가 발생했습니다:\n{error_message}",
                confirm_text="확인",
                cancel_text=None,
                icon="❌"
            )
            dialog.exec()
            
        except Exception as e:
            logger.error(f"로그인 오류 처리 중 오류: {e}")
    
    def on_two_factor_detected(self):
        """2차 인증 감지 처리"""
        try:
            logger.info("🔐 2차 인증 감지됨")
            self.login_button.setText("🔐 2차 인증 진행 중...")
            self.status_label.setText("🔐 2차 인증 진행 중 - 브라우저에서 인증을 완료해주세요")
            
            # 2차 인증 안내 토스트
            try:
                from src.toolbox.ui_kit.components import show_toast
                show_toast(self, "🔐 2차 인증이 감지되었습니다. 브라우저에서 인증을 완료해주세요.", "info", 5000)
            except:
                pass  # 토스트 실패 시 무시
            
        except Exception as e:
            logger.error(f"2차 인증 처리 중 오류: {e}")
    
    def on_write_clicked(self):
        """글쓰기 버튼 클릭 이벤트"""
        try:
            logger.info("글쓰기 페이지 열기 버튼 클릭됨")
            
            if not self.is_logged_in:
                dialog = ModernConfirmDialog(
                    self,
                    title="로그인 필요",
                    message="먼저 로그인을 완료해주세요.",
                    confirm_text="확인",
                    cancel_text=None,
                    icon="⚠️"
                )
                dialog.exec()
                return
            
            # 글쓰기 페이지 열기
            self.write_button.setText("🔄 글쓰기 페이지 여는 중...")
            self.write_button.setEnabled(False)
            
            success = self.service.open_blog_write_page()
            
            if success:
                self.status_label.setText("✅ 글쓰기 페이지가 열렸습니다")
                
                dialog = ModernConfirmDialog(
                    self,
                    title="글쓰기 페이지 열기 성공",
                    message="새 창에서 블로그 글쓰기 페이지가 열렸습니다.\n브라우저를 확인해주세요.",
                    confirm_text="확인",
                    cancel_text=None,
                    icon="✅"
                )
                dialog.exec()
            else:
                self.status_label.setText("❌ 글쓰기 페이지 열기 실패")
                
                dialog = ModernConfirmDialog(
                    self,
                    title="글쓰기 페이지 열기 실패",
                    message="글쓰기 페이지를 열 수 없습니다.\n로그인 상태를 확인해주세요.",
                    confirm_text="확인",
                    cancel_text=None,
                    icon="❌"
                )
                dialog.exec()
            
            # 버튼 상태 복원
            self.write_button.setText("📝 글쓰기 페이지 열기")
            self.write_button.setEnabled(True)
            
        except Exception as e:
            logger.error(f"글쓰기 페이지 열기 오류: {e}")
            
            self.write_button.setText("📝 글쓰기 페이지 열기")
            self.write_button.setEnabled(True)
            self.status_label.setText("글쓰기 페이지 열기 오류")
            
            dialog = ModernConfirmDialog(
                self,
                title="오류",
                message=f"글쓰기 페이지 열기 중 오류가 발생했습니다:\n{str(e)}",
                confirm_text="확인",
                cancel_text=None,
                icon="❌"
            )
            dialog.exec()
    
    def reset_login_ui(self):
        """로그인 UI 상태 초기화"""
        self.login_button.setText("로그인")
        self.login_button.setEnabled(True)
        self.write_button.setEnabled(False)  # 글쓰기 버튼 비활성화
        self.is_logged_in = False
    
    def closeEvent(self, event):
        """창 닫기 이벤트"""
        # 워커 취소
        if self.login_worker:
            self.login_worker.cancel()
        if self.login_thread:
            self.login_thread.quit()
            self.login_thread.wait()
        
        # 브라우저 세션 정리
        if self.service:
            try:
                self.service.force_stop_browser_session()
            except Exception as e:
                logger.error(f"앱 종료 시 브라우저 세션 종료 실패: {e}")
        
        event.accept()