"""
API 설정 다이얼로그
사용자가 네이버 API 키들을 입력/관리할 수 있는 UI
"""
import json
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QTabWidget, QWidget, QGroupBox, QFormLayout, QMessageBox, QTextEdit, QComboBox
)
from src.toolbox.ui_kit.components import ModernPrimaryButton, ModernDangerButton, ModernSuccessButton, ModernButton
from PySide6.QtCore import Qt, Signal
from src.toolbox.ui_kit import ModernStyle
from src.toolbox.ui_kit import tokens
from src.foundation.logging import get_logger

logger = get_logger("desktop.api_dialog")

class APISettingsDialog(QDialog):
    """API 설정 다이얼로그"""
    
    # 시그널 정의
    api_settings_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔐 API 설정")
        self.setModal(True)
        
        # 반응형 다이얼로그 크기 설정
        scale = tokens.get_screen_scale_factor()
        dialog_width = int(600 * scale)
        dialog_height = int(500 * scale)
        self.resize(dialog_width, dialog_height)
        
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """UI 설정"""
        scale = tokens.get_screen_scale_factor()
        margin = int(20 * scale)
        spacing = int(20 * scale)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(spacing)
        
        # 제목 (반응형 스케일링)
        scale = tokens.get_screen_scale_factor()
        title_font_size = int(18 * scale)
        title_margin = int(10 * scale)
        
        title_label = QLabel("API 설정")
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: {title_font_size}px;
                font-weight: 700;
                color: {ModernStyle.COLORS['text_primary']};
                margin-bottom: {title_margin}px;
            }}
        """)
        layout.addWidget(title_label)
        
        # 탭 위젯
        self.tab_widget = QTabWidget()
        self.setup_naver_tab()      # 통합된 네이버 API 탭
        self.setup_text_ai_tab()    # 글 작성 AI 탭
        self.setup_image_ai_tab()   # 이미지 생성 AI 탭
        
        layout.addWidget(self.tab_widget)
        
        # 하단 버튼들
        self.setup_buttons(layout)
        
        self.setLayout(layout)
        self.apply_styles()
    
    def setup_naver_tab(self):
        """통합된 네이버 API 탭"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # 전체 설명과 도움말 버튼
        desc_layout = QHBoxLayout()
        desc = QLabel("네이버 관련 조회에 사용되는 개발자 API와\n실제 월 검색량 조회를 위한 검색광고 API 키를 입력하세요.")
        desc.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_secondary']};
                font-size: {tokens.get_font_size('normal')}px;
                line-height: 1.4;
            }}
        """)
        desc_layout.addWidget(desc)
        desc_layout.addStretch()
        
        # 네이버 API 발급방법 버튼 (오른쪽 고정)
        naver_help_btn = ModernButton("📋 발급방법", "secondary")
        naver_help_btn.clicked.connect(self.show_naver_help)
        naver_help_btn.setMaximumWidth(105)
        desc_layout.addWidget(naver_help_btn)
        
        layout.addLayout(desc_layout)
        
        # 네이버 개발자 API 그룹
        developers_group = QGroupBox("네이버 개발자 API")
        developers_layout = QVBoxLayout()
        developers_layout.setSpacing(10)
        
        # 설명
        dev_desc = QLabel("네이버 관련 데이터 조회용")
        dev_desc.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_secondary']};
                font-size: 12px;
                margin-bottom: 8px;
            }}
        """)
        developers_layout.addWidget(dev_desc)
        
        # Client ID
        client_id_layout = QHBoxLayout()
        client_id_layout.addWidget(QLabel("Client ID:"))
        self.shopping_client_id = QLineEdit()
        self.shopping_client_id.setPlaceholderText("네이버 개발자 센터에서 발급받은 Client ID")
        client_id_layout.addWidget(self.shopping_client_id, 1)
        developers_layout.addLayout(client_id_layout)
        
        # Client Secret
        client_secret_layout = QHBoxLayout()
        client_secret_layout.addWidget(QLabel("Client Secret:"))
        self.shopping_client_secret = QLineEdit()
        self.shopping_client_secret.setPlaceholderText("네이버 개발자 센터에서 발급받은 Client Secret")
        self.shopping_client_secret.setEchoMode(QLineEdit.Password)
        client_secret_layout.addWidget(self.shopping_client_secret, 1)
        developers_layout.addLayout(client_secret_layout)
        
        # 개발자 API 버튼
        dev_btn_layout = QHBoxLayout()
        # 반응형 버튼들로 교체
        self.shopping_delete_btn = ModernDangerButton("삭제")
        self.shopping_delete_btn.clicked.connect(self.delete_shopping_api)
        dev_btn_layout.addWidget(self.shopping_delete_btn)
        
        self.shopping_apply_btn = ModernSuccessButton("적용")
        self.shopping_apply_btn.clicked.connect(self.apply_shopping_api)
        dev_btn_layout.addWidget(self.shopping_apply_btn)
        dev_btn_layout.addStretch()
        developers_layout.addLayout(dev_btn_layout)
        
        # 개발자 API 상태
        self.shopping_status = QLabel("")
        self.shopping_status.setStyleSheet(f"color: {ModernStyle.COLORS['text_secondary']};")
        developers_layout.addWidget(self.shopping_status)
        
        developers_group.setLayout(developers_layout)
        layout.addWidget(developers_group)
        
        # 네이버 검색광고 API 그룹
        searchad_group = QGroupBox("네이버 검색광고 API")
        searchad_layout = QVBoxLayout()
        searchad_layout.setSpacing(10)
        
        # 설명
        searchad_desc = QLabel("실제 월 검색량 조회용")
        searchad_desc.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_secondary']};
                font-size: 12px;
                margin-bottom: 8px;
            }}
        """)
        searchad_layout.addWidget(searchad_desc)
        
        # 액세스 라이선스
        api_key_layout = QHBoxLayout()
        api_key_layout.addWidget(QLabel("액세스 라이선스:"))
        self.searchad_access_license = QLineEdit()
        self.searchad_access_license.setPlaceholderText("액세스 라이선스를 입력하세요")
        api_key_layout.addWidget(self.searchad_access_license, 1)
        searchad_layout.addLayout(api_key_layout)
        
        # 비밀키
        secret_key_layout = QHBoxLayout()
        secret_key_layout.addWidget(QLabel("비밀키:"))
        self.searchad_secret_key = QLineEdit()
        self.searchad_secret_key.setPlaceholderText("••••••••••••••••••••••••••••••••")
        self.searchad_secret_key.setEchoMode(QLineEdit.Password)
        secret_key_layout.addWidget(self.searchad_secret_key, 1)
        searchad_layout.addLayout(secret_key_layout)
        
        # Customer ID
        customer_id_layout = QHBoxLayout()
        customer_id_layout.addWidget(QLabel("Customer ID:"))
        self.searchad_customer_id = QLineEdit()
        self.searchad_customer_id.setPlaceholderText("Customer ID를 입력하세요")
        customer_id_layout.addWidget(self.searchad_customer_id, 1)
        searchad_layout.addLayout(customer_id_layout)
        
        # 검색광고 API 버튼
        searchad_btn_layout = QHBoxLayout()
        # 반응형 버튼들로 교체
        self.searchad_delete_btn = ModernDangerButton("삭제")
        self.searchad_delete_btn.clicked.connect(self.delete_searchad_api)
        searchad_btn_layout.addWidget(self.searchad_delete_btn)
        
        self.searchad_apply_btn = ModernSuccessButton("적용")
        self.searchad_apply_btn.clicked.connect(self.apply_searchad_api)
        searchad_btn_layout.addWidget(self.searchad_apply_btn)
        searchad_btn_layout.addStretch()
        searchad_layout.addLayout(searchad_btn_layout)
        
        # 검색광고 API 상태
        self.searchad_status = QLabel("")
        self.searchad_status.setStyleSheet(f"color: {ModernStyle.COLORS['text_secondary']};")
        searchad_layout.addWidget(self.searchad_status)
        
        searchad_group.setLayout(searchad_layout)
        layout.addWidget(searchad_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "네이버 API")
    
    def setup_text_ai_tab(self):
        """글 작성 AI API 설정 탭"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # 전체 설명과 도움말 버튼
        desc_layout = QHBoxLayout()
        desc = QLabel("블로그 글 작성을 위한 AI API를 선택하고 설정하세요.\n정보요약과 글작성 AI를 각각 설정할 수 있습니다.")
        desc.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_secondary']};
                font-size: {tokens.get_font_size('normal')}px;
                line-height: 1.4;
            }}
        """)
        desc_layout.addWidget(desc)
        desc_layout.addStretch()
        
        # 글 작성 AI 발급방법 버튼 (오른쪽 고정)
        text_ai_help_btn = ModernButton("📋 발급방법", "secondary")
        text_ai_help_btn.clicked.connect(self.show_text_ai_help)
        text_ai_help_btn.setMaximumWidth(105)
        desc_layout.addWidget(text_ai_help_btn)
        
        layout.addLayout(desc_layout)
        
        # 정보요약 AI 설정 그룹
        summary_ai_group = QGroupBox("📄 정보요약 AI")
        summary_ai_layout = QVBoxLayout()
        summary_ai_layout.setSpacing(10)
        
        # 정보요약 AI 제공자 선택
        summary_provider_layout = QHBoxLayout()
        summary_provider_layout.addWidget(QLabel("AI 제공자:"))
        
        self.summary_ai_provider_combo = QComboBox()
        self.summary_ai_provider_combo.addItems([
            "AI 제공자를 선택하세요",
            "OpenAI (GPT)",
            "Google (Gemini)",
            "Anthropic (Claude)"
        ])
        self.summary_ai_provider_combo.currentTextChanged.connect(self.on_summary_ai_provider_changed)
        summary_provider_layout.addWidget(self.summary_ai_provider_combo, 1)
        summary_ai_layout.addLayout(summary_provider_layout)

        # AI 모델 선택 (처음에는 숨김)
        summary_model_layout = QHBoxLayout()
        self.summary_model_label = QLabel("AI 모델:")
        self.summary_model_label.setVisible(False)
        summary_model_layout.addWidget(self.summary_model_label)
        
        self.summary_ai_model_combo = QComboBox()
        self.summary_ai_model_combo.setVisible(False)
        self.summary_ai_model_combo.currentTextChanged.connect(self.on_summary_ai_model_changed)
        summary_model_layout.addWidget(self.summary_ai_model_combo, 1)
        summary_ai_layout.addLayout(summary_model_layout)
        
        # 정보요약 AI API 키 설정 (처음에는 숨김)
        self.summary_ai_config_group = QGroupBox("API 설정")
        self.summary_ai_config_group.setVisible(False)
        summary_config_layout = QVBoxLayout()
        
        # API 키 입력
        summary_api_key_layout = QHBoxLayout()
        summary_api_key_layout.addWidget(QLabel("API Key:"))
        self.summary_ai_api_key = QLineEdit()
        self.summary_ai_api_key.setPlaceholderText("API 키를 입력하세요")
        self.summary_ai_api_key.setEchoMode(QLineEdit.Password)
        summary_api_key_layout.addWidget(self.summary_ai_api_key, 1)
        summary_config_layout.addLayout(summary_api_key_layout)
        
        # 정보요약 AI 버튼
        summary_btn_layout = QHBoxLayout()
        self.summary_ai_delete_btn = ModernDangerButton("삭제")
        self.summary_ai_delete_btn.clicked.connect(self.delete_summary_ai_key)
        summary_btn_layout.addWidget(self.summary_ai_delete_btn)
        
        self.summary_ai_apply_btn = ModernSuccessButton("적용")
        self.summary_ai_apply_btn.clicked.connect(self.apply_summary_ai_key)
        summary_btn_layout.addWidget(self.summary_ai_apply_btn)
        summary_btn_layout.addStretch()
        summary_config_layout.addLayout(summary_btn_layout)
        
        # 정보요약 AI 상태
        self.summary_ai_status = QLabel("")
        self.summary_ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['text_secondary']};")
        summary_config_layout.addWidget(self.summary_ai_status)
        
        self.summary_ai_config_group.setLayout(summary_config_layout)
        summary_ai_layout.addWidget(self.summary_ai_config_group)
        
        summary_ai_group.setLayout(summary_ai_layout)
        layout.addWidget(summary_ai_group)
        
        # 글 작성 AI 설정 그룹
        text_ai_group = QGroupBox("✍️ 글작성 AI")
        text_ai_layout = QVBoxLayout()
        text_ai_layout.setSpacing(10)

        # 글작성 AI 제공자 선택
        text_provider_layout = QHBoxLayout()
        text_provider_layout.addWidget(QLabel("AI 제공자:"))
        
        self.text_ai_provider_combo = QComboBox()
        self.text_ai_provider_combo.addItems([
            "AI 제공자를 선택하세요",
            "OpenAI (GPT)",
            "Google (Gemini)",
            "Anthropic (Claude)"
        ])
        self.text_ai_provider_combo.currentTextChanged.connect(self.on_text_ai_provider_changed)
        text_provider_layout.addWidget(self.text_ai_provider_combo, 1)
        text_ai_layout.addLayout(text_provider_layout)

        # AI 모델 선택 (처음에는 숨김)
        text_model_layout = QHBoxLayout()
        self.text_model_label = QLabel("AI 모델:")
        self.text_model_label.setVisible(False)
        text_model_layout.addWidget(self.text_model_label)
        
        self.text_ai_model_combo = QComboBox()
        self.text_ai_model_combo.setVisible(False)
        self.text_ai_model_combo.currentTextChanged.connect(self.on_text_ai_model_changed)
        text_model_layout.addWidget(self.text_ai_model_combo, 1)
        text_ai_layout.addLayout(text_model_layout)

        # 글작성 AI API 키 설정 (처음에는 숨김)
        self.text_ai_config_group = QGroupBox("API 설정")
        self.text_ai_config_group.setVisible(False)
        text_ai_config_layout = QVBoxLayout()
        text_ai_config_layout.setSpacing(10)

        # API 키 입력
        text_api_key_layout = QHBoxLayout()
        text_api_key_layout.addWidget(QLabel("API Key:"))
        
        self.text_ai_api_key = QLineEdit()
        self.text_ai_api_key.setPlaceholderText("API 키를 입력하세요")
        self.text_ai_api_key.setEchoMode(QLineEdit.Password)
        text_api_key_layout.addWidget(self.text_ai_api_key, 1)
        text_ai_config_layout.addLayout(text_api_key_layout)

        # 글작성 AI 버튼
        text_btn_layout = QHBoxLayout()
        self.text_ai_delete_btn = ModernDangerButton("삭제")
        self.text_ai_delete_btn.clicked.connect(self.delete_text_ai_api)
        text_btn_layout.addWidget(self.text_ai_delete_btn)

        self.text_ai_apply_btn = ModernSuccessButton("적용")
        self.text_ai_apply_btn.clicked.connect(self.apply_text_ai_api)
        text_btn_layout.addWidget(self.text_ai_apply_btn)

        text_btn_layout.addStretch()
        text_ai_config_layout.addLayout(text_btn_layout)

        # 글작성 AI 상태
        self.text_ai_status = QLabel("")
        self.text_ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['text_secondary']};")
        text_ai_config_layout.addWidget(self.text_ai_status)

        self.text_ai_config_group.setLayout(text_ai_config_layout)
        text_ai_layout.addWidget(self.text_ai_config_group)

        text_ai_group.setLayout(text_ai_layout)
        layout.addWidget(text_ai_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "📝 글 작성 AI")
    
    def setup_image_ai_tab(self):
        """이미지 생성 AI API 설정 탭"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # 전체 설명과 도움말 버튼
        desc_layout = QHBoxLayout()
        desc = QLabel("블로그 이미지 생성을 위한 AI API를 선택하고 설정하세요.\n글 내용에 맞는 이미지를 자동으로 생성합니다.")
        desc.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_secondary']};
                font-size: {tokens.get_font_size('normal')}px;
                line-height: 1.4;
            }}
        """)
        desc_layout.addWidget(desc)
        desc_layout.addStretch()
        
        # 이미지 생성 AI 발급방법 버튼 (오른쪽 고정)
        image_ai_help_btn = ModernButton("📋 발급방법", "secondary")
        image_ai_help_btn.clicked.connect(self.show_image_ai_help)
        image_ai_help_btn.setMaximumWidth(105)
        desc_layout.addWidget(image_ai_help_btn)
        
        layout.addLayout(desc_layout)
        
        # 이미지 생성 AI 설정 그룹
        image_ai_group = QGroupBox("🎨 이미지 생성 AI")
        image_ai_layout = QVBoxLayout()
        image_ai_layout.setSpacing(10)

        # 이미지 생성 AI 제공자 선택
        image_provider_layout = QHBoxLayout()
        image_provider_layout.addWidget(QLabel("AI 제공자:"))
        
        self.image_ai_provider_combo = QComboBox()
        self.image_ai_provider_combo.addItems([
            "AI 제공자를 선택하세요",
            "OpenAI (DALL-E)",
            "Google (Imagen)"
        ])
        self.image_ai_provider_combo.currentTextChanged.connect(self.on_image_ai_provider_changed)
        image_provider_layout.addWidget(self.image_ai_provider_combo, 1)
        image_ai_layout.addLayout(image_provider_layout)

        # AI 모델 선택 (처음에는 숨김)
        image_model_layout = QHBoxLayout()
        self.image_model_label = QLabel("AI 모델:")
        self.image_model_label.setVisible(False)
        image_model_layout.addWidget(self.image_model_label)
        
        self.image_ai_model_combo = QComboBox()
        self.image_ai_model_combo.setVisible(False)
        self.image_ai_model_combo.currentTextChanged.connect(self.on_image_ai_model_changed)
        image_model_layout.addWidget(self.image_ai_model_combo, 1)
        image_ai_layout.addLayout(image_model_layout)

        # 이미지 생성 AI API 키 설정 (처음에는 숨김)
        self.image_ai_config_group = QGroupBox("API 설정")
        self.image_ai_config_group.setVisible(False)
        image_ai_config_layout = QVBoxLayout()
        image_ai_config_layout.setSpacing(10)

        # API 키 입력
        image_api_key_layout = QHBoxLayout()
        image_api_key_layout.addWidget(QLabel("API Key:"))
        
        self.image_ai_api_key = QLineEdit()
        self.image_ai_api_key.setPlaceholderText("API 키를 입력하세요")
        self.image_ai_api_key.setEchoMode(QLineEdit.Password)
        image_api_key_layout.addWidget(self.image_ai_api_key, 1)
        image_ai_config_layout.addLayout(image_api_key_layout)

        # 이미지 생성 AI 버튼
        image_btn_layout = QHBoxLayout()
        self.image_ai_delete_btn = ModernDangerButton("삭제")
        self.image_ai_delete_btn.clicked.connect(self.delete_image_ai_api)
        image_btn_layout.addWidget(self.image_ai_delete_btn)

        self.image_ai_apply_btn = ModernSuccessButton("적용")
        self.image_ai_apply_btn.clicked.connect(self.apply_image_ai_api)
        image_btn_layout.addWidget(self.image_ai_apply_btn)

        image_btn_layout.addStretch()
        image_ai_config_layout.addLayout(image_btn_layout)

        # 이미지 생성 AI 상태
        self.image_ai_status = QLabel("")
        self.image_ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['text_secondary']};")
        image_ai_config_layout.addWidget(self.image_ai_status)

        self.image_ai_config_group.setLayout(image_ai_config_layout)
        image_ai_layout.addWidget(self.image_ai_config_group)

        image_ai_group.setLayout(image_ai_layout)
        layout.addWidget(image_ai_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "🎨 이미지 생성 AI")
    
    def on_text_ai_provider_changed(self, provider_text):
        """글 작성 AI 제공자 변경시 호출"""
        if provider_text == "AI 제공자를 선택하세요":
            self.text_model_label.setVisible(False)
            self.text_ai_model_combo.setVisible(False)
            self.text_ai_config_group.setVisible(False)
            self.current_text_ai_provider = None
            if hasattr(self, 'text_ai_api_key'):
                self.text_ai_api_key.clear()
        else:
            self.text_model_label.setVisible(True)
            self.text_ai_model_combo.setVisible(True)
            
            self.text_ai_model_combo.clear()
            if provider_text == "OpenAI (GPT)":
                self.text_ai_model_combo.addItems([
                    "모델을 선택하세요",
                    "GPT-4o Mini (유료, 저렴)",
                    "GPT-4o (유료, 표준)",
                    "GPT-4 Turbo (유료, 고단가)"
                ])
                self.current_text_ai_provider = "openai"
                if hasattr(self, 'text_ai_api_key'):
                    self.text_ai_api_key.setPlaceholderText("sk-...")
                    
            elif provider_text == "Google (Gemini)":
                self.text_ai_model_combo.addItems([
                    "모델을 선택하세요",
                    "Gemini 1.5 Flash (무료, 빠름)",
                    "Gemini 1.5 Pro (유료, 고품질)",
                    "Gemini 2.0 Flash (무료, 최신)"
                ])
                self.current_text_ai_provider = "gemini"
                if hasattr(self, 'text_ai_api_key'):
                    self.text_ai_api_key.setPlaceholderText("Google AI API 키")
                    
            elif provider_text == "Anthropic (Claude)":
                self.text_ai_model_combo.addItems([
                    "모델을 선택하세요",
                    "Claude 3.5 Sonnet (유료, 고품질)", 
                    "Claude 3.5 Haiku (유료, 빠름)",
                    "Claude 3 Opus (유료, 최고품질)"
                ])
                self.current_text_ai_provider = "claude"
                if hasattr(self, 'text_ai_api_key'):
                    self.text_ai_api_key.setPlaceholderText("Anthropic API 키")
            
            self.load_text_ai_provider_api_key()
    
    def on_summary_ai_provider_changed(self, provider_text):
        """정보요약 AI 제공자 변경시 호출"""
        if provider_text == "AI 제공자를 선택하세요":
            self.summary_model_label.setVisible(False)
            self.summary_ai_model_combo.setVisible(False)
            self.summary_ai_config_group.setVisible(False)
            self.current_summary_ai_provider = None
            if hasattr(self, 'summary_ai_api_key'):
                self.summary_ai_api_key.clear()
        else:
            self.summary_model_label.setVisible(True)
            self.summary_ai_model_combo.setVisible(True)
            
            self.summary_ai_model_combo.clear()
            if provider_text == "OpenAI (GPT)":
                self.summary_ai_model_combo.addItems([
                    "모델을 선택하세요",
                    "GPT-4o Mini (유료, 저렴)",
                    "GPT-4o (유료, 표준)",
                    "GPT-4 Turbo (유료, 고단가)"
                ])
                self.current_summary_ai_provider = "openai"
                if hasattr(self, 'summary_ai_api_key'):
                    self.summary_ai_api_key.setPlaceholderText("sk-...")
                    
            elif provider_text == "Google (Gemini)":
                self.summary_ai_model_combo.addItems([
                    "모델을 선택하세요",
                    "Gemini 1.5 Flash (무료, 빠름)",
                    "Gemini 1.5 Pro (유료, 고품질)",
                    "Gemini 2.0 Flash (무료, 최신)"
                ])
                self.current_summary_ai_provider = "gemini"
                if hasattr(self, 'summary_ai_api_key'):
                    self.summary_ai_api_key.setPlaceholderText("Google AI API 키")
                    
            elif provider_text == "Anthropic (Claude)":
                self.summary_ai_model_combo.addItems([
                    "모델을 선택하세요",
                    "Claude 3.5 Sonnet (유료, 고품질)", 
                    "Claude 3.5 Haiku (유료, 빠름)",
                    "Claude 3 Opus (유료, 최고품질)"
                ])
                self.current_summary_ai_provider = "claude"
                if hasattr(self, 'summary_ai_api_key'):
                    self.summary_ai_api_key.setPlaceholderText("Anthropic API 키")
            
            self.load_summary_ai_provider_api_key()

    def on_summary_ai_model_changed(self, model_text):
        """정보요약 AI 모델 변경시 호출"""
        if model_text == "모델을 선택하세요":
            self.summary_ai_config_group.setVisible(False)
        else:
            self.summary_ai_config_group.setVisible(True)
            self.current_summary_ai_model = model_text

    def apply_summary_ai_key(self):
        """정보요약 AI API 테스트 후 적용"""
        if not hasattr(self, 'current_summary_ai_provider') or not self.current_summary_ai_provider:
            return

        api_key = self.summary_ai_api_key.text().strip()
        if not api_key:
            self.summary_ai_status.setText("⚠️ API 키를 입력해주세요.")
            self.summary_ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['danger']};")
            return

        self.summary_ai_status.setText("테스트 및 적용 중...")
        self.summary_ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['primary']};")
        self.summary_ai_apply_btn.setEnabled(False)

        try:
            if self.current_summary_ai_provider == "openai":
                result = self.test_openai_api_internal(api_key)
            elif self.current_summary_ai_provider == "gemini":
                result = self.test_google_gemini_api_internal(api_key)
            elif self.current_summary_ai_provider == "claude":
                result = self.test_claude_api_internal(api_key)
            else:
                result = (False, "지원되지 않는 AI 제공자입니다.")

            if result[0]:
                selected_model = getattr(self, 'current_summary_ai_model', '')
                if not selected_model:
                    selected_model = self.summary_ai_model_combo.currentText()

                # 정보요약 AI 설정 저장
                self.save_summary_ai_config(self.current_summary_ai_provider, api_key, selected_model)
                
                self.summary_ai_status.setText(f"✅ {selected_model} API가 적용되었습니다.")
                self.summary_ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['success']};")
            else:
                self.summary_ai_status.setText(f"❌ 연결 실패: {result[1]}")
                self.summary_ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['danger']};")

        except Exception as e:
            self.summary_ai_status.setText(f"❌ 적용 오류: {str(e)}")
            self.summary_ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['danger']};")
        finally:
            self.summary_ai_apply_btn.setEnabled(True)

    def save_summary_ai_config(self, provider: str, api_key: str, selected_model: str):
        """정보요약 AI API 설정 저장"""
        try:
            from src.foundation.config import config_manager
            api_config = config_manager.load_api_config()

            if provider == "openai":
                api_config.openai_api_key = api_key
                api_config.current_summary_ai_provider = "openai"
            elif provider == "gemini":
                api_config.gemini_api_key = api_key
                api_config.current_summary_ai_provider = "google"  # service.py에서 "google"로 확인
            elif provider == "claude":
                api_config.claude_api_key = api_key
                api_config.current_summary_ai_provider = "anthropic"  # service.py에서 "anthropic"으로 확인

            # 선택된 모델 저장
            api_config.current_summary_ai_model = selected_model

            if config_manager.save_api_config(api_config):
                logger.info(f"정보요약 AI API 설정 저장 완료: {provider} - {selected_model}")
            else:
                logger.error("정보요약 AI API 설정 저장 실패")

        except Exception as e:
            logger.error(f"정보요약 AI API 설정 저장 중 오류: {e}")

    def delete_summary_ai_key(self):
        """정보요약 AI API 삭제"""
        if not hasattr(self, 'current_summary_ai_provider') or not self.current_summary_ai_provider:
            return

        reply = QMessageBox.question(
            self, 
            "확인", 
            f"{self.summary_ai_provider_combo.currentText()} API 설정을 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                from src.foundation.config import config_manager
                api_config = config_manager.load_api_config()
                
                # API 키 삭제
                if self.current_summary_ai_provider == "openai":
                    api_config.openai_api_key = ""
                elif self.current_summary_ai_provider == "gemini":
                    api_config.gemini_api_key = ""
                elif self.current_summary_ai_provider == "claude":
                    api_config.claude_api_key = ""
                
                # 현재 설정 초기화
                api_config.current_summary_ai_provider = ""
                api_config.current_summary_ai_model = ""
                
                if config_manager.save_api_config(api_config):
                    # UI 초기화
                    self.summary_ai_api_key.clear()
                    self.summary_ai_provider_combo.setCurrentText("AI 제공자를 선택하세요")
                    self.summary_ai_model_combo.clear()
                    
                    self.summary_model_label.setVisible(False)
                    self.summary_ai_model_combo.setVisible(False)
                    self.summary_ai_config_group.setVisible(False)

                    # 상태 초기화
                    self.current_summary_ai_provider = None
                    if hasattr(self, 'current_summary_ai_model'):
                        self.current_summary_ai_model = None

                    self.summary_ai_status.setText("🟡 API를 다시 설정해 주세요.")
                    self.summary_ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['warning']};")

                    # 완료 메시지
                    QMessageBox.information(self, "완료", "정보요약 AI API 설정이 삭제되었습니다.")

            except Exception as e:
                logger.error(f"정보요약 AI API 삭제 실패: {e}")

    def load_summary_ai_provider_api_key(self):
        """정보요약 AI 제공자의 API 키 로드"""
        try:
            from src.foundation.config import config_manager
            api_config = config_manager.load_api_config()
            
            if hasattr(self, 'current_summary_ai_provider') and self.current_summary_ai_provider:
                if self.current_summary_ai_provider == "openai" and hasattr(api_config, 'openai_api_key'):
                    if api_config.openai_api_key:
                        self.summary_ai_api_key.setText(api_config.openai_api_key)
                    else:
                        self.summary_ai_api_key.clear()
                        
                elif self.current_summary_ai_provider == "gemini" and hasattr(api_config, 'gemini_api_key'):
                    if api_config.gemini_api_key:
                        self.summary_ai_api_key.setText(api_config.gemini_api_key)
                    else:
                        self.summary_ai_api_key.clear()
                        
                elif self.current_summary_ai_provider == "claude" and hasattr(api_config, 'claude_api_key'):
                    if api_config.claude_api_key:
                        self.summary_ai_api_key.setText(api_config.claude_api_key)
                    else:
                        self.summary_ai_api_key.clear()
                        
                else:
                    self.summary_ai_api_key.clear()
            else:
                self.summary_ai_api_key.clear()

        except Exception as e:
            logger.error(f"정보요약 AI API 키 로드 실패: {e}")

    def on_image_ai_provider_changed(self, provider_text):
        """이미지 생성 AI 제공자 변경시 호출"""
        if provider_text == "AI 제공자를 선택하세요":
            self.image_model_label.setVisible(False)
            self.image_ai_model_combo.setVisible(False)
            self.image_ai_config_group.setVisible(False)
            self.current_image_ai_provider = None
            if hasattr(self, 'image_ai_api_key'):
                self.image_ai_api_key.clear()
        else:
            self.image_model_label.setVisible(True)
            self.image_ai_model_combo.setVisible(True)
            
            self.image_ai_model_combo.clear()
            if provider_text == "OpenAI (DALL-E)":
                self.image_ai_model_combo.addItems([
                    "모델을 선택하세요",
                    "DALL-E 3 (유료, 최고품질)",
                    "DALL-E 2 (유료, 저렴)"
                ])
                self.current_image_ai_provider = "dalle"
                if hasattr(self, 'image_ai_api_key'):
                    self.image_ai_api_key.setPlaceholderText("sk-...")
                    
            elif provider_text == "Google (Imagen)":
                self.image_ai_model_combo.addItems([
                    "모델을 선택하세요",
                    "Imagen 3 (유료, 최고품질)",
                    "Imagen 2 (유료, 표준)"
                ])
                self.current_image_ai_provider = "imagen"
                if hasattr(self, 'image_ai_api_key'):
                    self.image_ai_api_key.setPlaceholderText("Google Cloud API 키")
            
            self.load_image_ai_provider_api_key()
    
    def apply_image_ai_api(self):
        """이미지 생성 AI API 테스트 후 적용"""
        if not hasattr(self, 'current_image_ai_provider') or not self.current_image_ai_provider:
            return
            
        api_key = self.image_ai_api_key.text().strip()
        if not api_key:
            self.image_ai_status.setText("⚠️ API 키를 입력해주세요.")
            self.image_ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['danger']};")
            return
        
        self.image_ai_status.setText("테스트 및 적용 중...")
        self.image_ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['primary']};")
        self.image_ai_apply_btn.setEnabled(False)
        
        try:
            # 제공자별 테스트 실행
            if self.current_image_ai_provider == "dalle":
                result = self.test_dalle_api_internal(api_key)
            elif self.current_image_ai_provider == "imagen":
                result = self.test_imagen_api_internal(api_key)
            else:
                result = (False, "지원되지 않는 이미지 AI 제공자입니다.")
            
            if result[0]:  # 테스트 성공시 자동 적용
                selected_model = getattr(self, 'current_image_ai_model', '')
                if not selected_model:
                    selected_model = self.image_ai_model_combo.currentText()
                
                # 이미지 생성 AI 설정 저장
                self.save_image_ai_config(self.current_image_ai_provider, api_key, selected_model)
                
                self.image_ai_status.setText(f"✅ {selected_model} API가 적용되었습니다.")
                self.image_ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['success']};")
                self.api_settings_changed.emit()
            else:
                self.image_ai_status.setText(f"❌ 연결 실패: {result[1]}")
                self.image_ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['danger']};")
                
        except Exception as e:
            self.image_ai_status.setText(f"❌ 적용 오류: {str(e)}")
            self.image_ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['danger']};")
        finally:
            self.image_ai_apply_btn.setEnabled(True)
    
    def test_dalle_api_internal(self, api_key):
        """DALL-E API 내부 테스트 (무료 검증 방식)"""
        try:
            import requests
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # 1차 시도: 모델 목록 조회 (무료)
            try:
                response = requests.get(
                    "https://api.openai.com/v1/models",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    models_data = response.json()
                    # DALL-E 관련 모델이 있는지 확인
                    model_ids = [model.get('id', '') for model in models_data.get('data', [])]
                    dalle_models = [mid for mid in model_ids if 'dall-e' in mid.lower()]
                    
                    if dalle_models:
                        return True, f"연결 성공 (사용 가능한 모델: {', '.join(dalle_models[:2])})"
                    else:
                        return True, "연결 성공 (DALL-E 모델 확인 필요)"
                        
                elif response.status_code == 401:
                    return False, "API 키가 유효하지 않습니다."
                elif response.status_code == 429:
                    return False, "API 할당량을 초과했습니다."
                else:
                    # 모델 목록 조회 실패 시 2차 시도
                    return self._test_openai_account_info(headers)
                    
            except requests.exceptions.RequestException:
                # 1차 실패 시 2차 시도
                return self._test_openai_account_info(headers)
                
        except requests.exceptions.Timeout:
            return False, "연결 시간 초과"
        except requests.exceptions.RequestException as e:
            return False, f"네트워크 오류: {str(e)}"
        except Exception as e:
            return False, str(e)
    
    def _test_openai_account_info(self, headers):
        """OpenAI 계정 정보 조회로 API 키 검증 (무료)"""
        try:
            import requests
            
            # 계정 정보나 사용량 조회 (무료)
            response = requests.get(
                "https://api.openai.com/v1/usage",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return True, "연결 성공 (계정 정보 확인됨)"
            elif response.status_code == 401:
                return False, "API 키가 유효하지 않습니다."
            elif response.status_code == 429:
                return False, "API 할당량을 초과했습니다."
            elif response.status_code == 403:
                return False, "API 키 권한이 부족합니다."
            else:
                # 최후의 수단: 매우 작은 completions 요청으로 검증
                return self._test_openai_minimal_request(headers)
                
        except Exception:
            return self._test_openai_minimal_request(headers)
    
    def _test_openai_minimal_request(self, headers):
        """최소한의 OpenAI 요청으로 검증 (저비용)"""
        try:
            import requests
            
            # 매우 작은 토큰으로 텍스트 완성 요청 (약 $0.001 미만)
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 1  # 최소 토큰
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                return True, "연결 성공 (API 키 유효)"
            elif response.status_code == 401:
                return False, "API 키가 유효하지 않습니다."
            elif response.status_code == 429:
                return False, "API 할당량을 초과했습니다."
            else:
                return False, f"상태 코드: {response.status_code}"
                
        except Exception as e:
            return False, f"검증 실패: {str(e)}"
    
    def test_imagen_api_internal(self, api_key):
        """Imagen API 내부 테스트 (무료 검증 방식)"""
        try:
            import requests
            
            # Google Cloud API 키 검증 방법들 시도
            
            # 1차 시도: Vertex AI API 엔드포인트 접근 테스트
            try:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                
                # Google Cloud의 경우 프로젝트 ID가 필요하므로 일반적인 엔드포인트로 키 유효성 검증
                response = requests.get(
                    "https://cloudresourcemanager.googleapis.com/v1/projects",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    return True, "연결 성공 (Google Cloud API 키 유효)"
                elif response.status_code == 401:
                    return False, "API 키가 유효하지 않습니다."
                elif response.status_code == 403:
                    return False, "API 키 권한이 부족하거나 프로젝트 설정이 필요합니다."
                else:
                    # 2차 시도: AI Platform API 확인
                    return self._test_google_ai_platform(headers)
                    
            except requests.exceptions.RequestException:
                return self._test_google_ai_platform(headers)
                
        except requests.exceptions.Timeout:
            return False, "연결 시간 초과"
        except requests.exceptions.RequestException as e:
            return False, f"네트워크 오류: {str(e)}"
        except Exception as e:
            return False, str(e)
    
    def _test_google_ai_platform(self, headers):
        """Google AI Platform 접근 테스트"""
        try:
            import requests
            
            # AI Platform API 엔드포인트로 테스트
            response = requests.get(
                "https://ml.googleapis.com/v1/projects",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return True, "연결 성공 (AI Platform API 접근 가능)"
            elif response.status_code == 401:
                return False, "API 키가 유효하지 않습니다."
            elif response.status_code == 403:
                return False, "API 키 권한이 부족합니다. Google Cloud 프로젝트 및 권한 설정을 확인하세요."
            elif response.status_code == 404:
                # API가 활성화되지 않은 경우도 키는 유효할 수 있음
                return True, "연결 성공 (API 키 유효, 서비스 활성화 필요할 수 있음)"
            else:
                return False, f"Google Cloud API 오류 (상태 코드: {response.status_code})"
                
        except Exception as e:
            # 최후의 수단: 단순히 키 형식 검증
            if api_key and len(api_key) > 20:
                return True, "API 키 형식 유효 (실제 연결 테스트는 Google Cloud 설정 필요)"
            else:
                return False, f"API 키 검증 실패: {str(e)}"
    
    def save_image_ai_config(self, provider: str, api_key: str, selected_model: str):
        """이미지 생성 AI API 설정 저장"""
        try:
            from src.foundation.config import config_manager
            
            api_config = config_manager.load_api_config()
            
            # 제공자별로 API 키 저장
            if provider == "dalle":
                api_config.dalle_api_key = api_key
            elif provider == "imagen":
                api_config.imagen_api_key = api_key
            
            # 선택된 AI API 저장 (누락된 부분 추가!)
            if provider == "dalle":
                api_config.current_image_ai_provider = "openai"  # service.py에서 "openai"로 확인
            elif provider == "imagen":
                api_config.current_image_ai_provider = "google"  # service.py에서 "google"로 확인
            
            # 선택된 모델 저장
            api_config.current_image_ai_model = selected_model
            
            success = config_manager.save_api_config(api_config)
            
            if success:
                logger.info(f"이미지 생성 AI API 설정 저장 완료: {provider} - {selected_model}")
            else:
                logger.error("이미지 생성 AI API 설정 저장 실패")
                
        except Exception as e:
            logger.error(f"이미지 생성 AI API 설정 저장 중 오류: {e}")
    
    def delete_image_ai_api(self):
        """이미지 생성 AI API 삭제"""
        if not hasattr(self, 'current_image_ai_provider') or not self.current_image_ai_provider:
            return
            
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, "확인", 
            f"{self.image_ai_provider_combo.currentText()} API 설정을 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                from src.foundation.config import config_manager
                
                api_config = config_manager.load_api_config()
                
                if self.current_image_ai_provider == "dalle":
                    api_config.dalle_api_key = ""
                elif self.current_image_ai_provider == "imagen":
                    api_config.imagen_api_key = ""
                
                # 현재 설정된 모델 정보도 삭제
                api_config.current_image_ai_model = ""
                
                config_manager.save_api_config(api_config)
                
                # UI 완전 초기화
                self.image_ai_api_key.clear()
                self.image_ai_provider_combo.setCurrentText("AI 제공자를 선택하세요")
                self.image_ai_model_combo.clear()
                self.image_model_label.setVisible(False)
                self.image_ai_model_combo.setVisible(False)
                self.image_ai_config_group.setVisible(False)
                
                # 현재 제공자 정보 초기화
                self.current_image_ai_provider = None
                if hasattr(self, 'current_image_ai_model'):
                    self.current_image_ai_model = None
                
                self.image_ai_status.setText("🟡 API를 다시 설정해 주세요.")
                self.image_ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['warning']};")
                
                self.api_settings_changed.emit()
                QMessageBox.information(self, "완료", "이미지 생성 AI API 설정이 삭제되었습니다.")
                
            except Exception as e:
                QMessageBox.critical(self, "오류", f"API 설정 삭제 실패: {str(e)}")
    
    def on_text_ai_model_changed(self, model_text):
        """글 작성 AI 모델 변경시 호출"""
        if model_text == "모델을 선택하세요" or not model_text:
            self.text_ai_config_group.setVisible(False)
        else:
            self.text_ai_config_group.setVisible(True)
            self.current_text_ai_model = model_text
    
    def on_image_ai_model_changed(self, model_text):
        """이미지 생성 AI 모델 변경시 호출"""
        if model_text == "모델을 선택하세요" or not model_text:
            self.image_ai_config_group.setVisible(False)
        else:
            self.image_ai_config_group.setVisible(True)
            self.current_image_ai_model = model_text
    
    def load_text_ai_provider_api_key(self):
        """글 작성 AI 제공자의 API 키 로드"""
        try:
            from src.foundation.config import config_manager
            api_config = config_manager.load_api_config()
            
            if hasattr(self, 'current_text_ai_provider') and self.current_text_ai_provider:
                if self.current_text_ai_provider == "openai" and hasattr(api_config, 'openai_api_key'):
                    if api_config.openai_api_key:
                        self.text_ai_api_key.setText(api_config.openai_api_key)
                    else:
                        self.text_ai_api_key.clear()
                        
                elif self.current_text_ai_provider == "gemini" and hasattr(api_config, 'gemini_api_key'):
                    if api_config.gemini_api_key:
                        self.text_ai_api_key.setText(api_config.gemini_api_key)
                    else:
                        self.text_ai_api_key.clear()
                        
                elif self.current_text_ai_provider == "claude" and hasattr(api_config, 'claude_api_key'):
                    if api_config.claude_api_key:
                        self.text_ai_api_key.setText(api_config.claude_api_key)
                    else:
                        self.text_ai_api_key.clear()
                else:
                    self.text_ai_api_key.clear()
            else:
                self.text_ai_api_key.clear()
                
        except Exception as e:
            logger.error(f"글 작성 AI API 키 로드 실패: {e}")
    
    def load_image_ai_provider_api_key(self):
        """이미지 생성 AI 제공자의 API 키 로드"""
        try:
            from src.foundation.config import config_manager
            api_config = config_manager.load_api_config()
            
            if hasattr(self, 'current_image_ai_provider') and self.current_image_ai_provider:
                if self.current_image_ai_provider == "dalle" and hasattr(api_config, 'dalle_api_key'):
                    if api_config.dalle_api_key:
                        self.image_ai_api_key.setText(api_config.dalle_api_key)
                    else:
                        self.image_ai_api_key.clear()
                        
                elif self.current_image_ai_provider == "imagen" and hasattr(api_config, 'imagen_api_key'):
                    if api_config.imagen_api_key:
                        self.image_ai_api_key.setText(api_config.imagen_api_key)
                    else:
                        self.image_ai_api_key.clear()
                else:
                    self.image_ai_api_key.clear()
            else:
                self.image_ai_api_key.clear()
                
        except Exception as e:
            logger.error(f"이미지 생성 AI API 키 로드 실패: {e}")
    
    def load_summary_ai_provider_api_key(self):
        """정보요약 AI 제공자의 API 키 로드"""
        try:
            from src.foundation.config import config_manager
            api_config = config_manager.load_api_config()
            
            if hasattr(self, 'current_summary_ai_provider') and self.current_summary_ai_provider:
                if self.current_summary_ai_provider == "openai" and hasattr(api_config, 'openai_api_key'):
                    if api_config.openai_api_key:
                        self.summary_ai_api_key.setText(api_config.openai_api_key)
                    else:
                        self.summary_ai_api_key.clear()
                        
                elif self.current_summary_ai_provider == "gemini" and hasattr(api_config, 'gemini_api_key'):
                    if api_config.gemini_api_key:
                        self.summary_ai_api_key.setText(api_config.gemini_api_key)
                    else:
                        self.summary_ai_api_key.clear()
                        
                elif self.current_summary_ai_provider == "claude" and hasattr(api_config, 'claude_api_key'):
                    if api_config.claude_api_key:
                        self.summary_ai_api_key.setText(api_config.claude_api_key)
                    else:
                        self.summary_ai_api_key.clear()
                else:
                    self.summary_ai_api_key.clear()
            else:
                self.summary_ai_api_key.clear()
                
        except Exception as e:
            logger.error(f"정보요약 AI API 키 로드 실패: {e}")
    
    def apply_text_ai_api(self):
        """글 작성 AI API 테스트 후 적용"""
        if not hasattr(self, 'current_text_ai_provider') or not self.current_text_ai_provider:
            return
            
        api_key = self.text_ai_api_key.text().strip()
        if not api_key:
            self.text_ai_status.setText("⚠️ API 키를 입력해주세요.")
            self.text_ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['danger']};")
            return
        
        self.text_ai_status.setText("테스트 및 적용 중...")
        self.text_ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['primary']};")
        self.text_ai_apply_btn.setEnabled(False)
        
        try:
            # 제공자별 테스트 실행
            if self.current_text_ai_provider == "openai":
                result = self.test_openai_api_internal(api_key)
            elif self.current_text_ai_provider == "gemini":
                result = self.test_gemini_api_internal(api_key)
            elif self.current_text_ai_provider == "claude":
                result = self.test_claude_api_internal(api_key)
            else:
                result = (False, "지원되지 않는 AI 제공자입니다.")
            
            if result[0]:  # 테스트 성공시 자동 적용
                selected_model = getattr(self, 'current_text_ai_model', '')
                if not selected_model:
                    selected_model = self.text_ai_model_combo.currentText()
                
                # 글 작성 AI 설정 저장
                self.save_text_ai_config(self.current_text_ai_provider, api_key, selected_model)
                
                self.text_ai_status.setText(f"✅ {selected_model} API가 적용되었습니다.")
                self.text_ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['success']};")
                self.api_settings_changed.emit()
            else:
                self.text_ai_status.setText(f"❌ 연결 실패: {result[1]}")
                self.text_ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['danger']};")
                
        except Exception as e:
            self.text_ai_status.setText(f"❌ 적용 오류: {str(e)}")
            self.text_ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['danger']};")
        finally:
            self.text_ai_apply_btn.setEnabled(True)
    
    def save_text_ai_config(self, provider: str, api_key: str, selected_model: str):
        """글 작성 AI API 설정 저장"""
        try:
            from src.foundation.config import config_manager
            
            api_config = config_manager.load_api_config()
            
            # 제공자별로 API 키 저장
            if provider == "openai":
                api_config.openai_api_key = api_key
            elif provider == "gemini":
                api_config.gemini_api_key = api_key
            elif provider == "claude":
                api_config.claude_api_key = api_key
            
            # 선택된 AI API 저장 (누락된 부분 추가!)
            if provider == "openai":
                api_config.current_text_ai_provider = "openai"
            elif provider == "gemini":
                api_config.current_text_ai_provider = "google"  # service.py에서 "google"로 확인
            elif provider == "claude":
                api_config.current_text_ai_provider = "anthropic"  # service.py에서 "anthropic"으로 확인
            
            # 선택된 모델 저장
            api_config.current_text_ai_model = selected_model
            
            success = config_manager.save_api_config(api_config)
            
            if success:
                logger.info(f"글 작성 AI API 설정 저장 완료: {provider} - {selected_model}")
            else:
                logger.error("글 작성 AI API 설정 저장 실패")
                
        except Exception as e:
            logger.error(f"글 작성 AI API 설정 저장 중 오류: {e}")
    
    def apply_summary_ai_key(self):
        """정보요약 AI API 테스트 후 적용"""
        if not hasattr(self, 'current_summary_ai_provider') or not self.current_summary_ai_provider:
            return
            
        api_key = self.summary_ai_api_key.text().strip()
        if not api_key:
            self.summary_ai_status.setText("⚠️ API 키를 입력해주세요.")
            self.summary_ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['danger']};")
            return
        
        self.summary_ai_status.setText("테스트 및 적용 중...")
        self.summary_ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['primary']};")
        self.summary_ai_apply_btn.setEnabled(False)
        
        try:
            # 제공자별 테스트 실행 (기존 text AI와 동일한 메서드 사용)
            if self.current_summary_ai_provider == "openai":
                result = self.test_openai_api_internal(api_key)
            elif self.current_summary_ai_provider == "gemini":
                result = self.test_gemini_api_internal(api_key)
            elif self.current_summary_ai_provider == "claude":
                result = self.test_claude_api_internal(api_key)
            else:
                result = (False, "지원되지 않는 AI 제공자입니다.")
            
            if result[0]:  # 테스트 성공시 자동 적용
                selected_model = getattr(self, 'current_summary_ai_model', '')
                if not selected_model:
                    selected_model = self.summary_ai_model_combo.currentText()
                
                # 정보요약 AI 설정 저장
                self.save_summary_ai_config(self.current_summary_ai_provider, api_key, selected_model)
                
                self.summary_ai_status.setText(f"✅ {selected_model} API가 적용되었습니다.")
                self.summary_ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['success']};")
                self.api_settings_changed.emit()
            else:
                self.summary_ai_status.setText(f"❌ 연결 실패: {result[1]}")
                self.summary_ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['danger']};")
                
        except Exception as e:
            self.summary_ai_status.setText(f"❌ 적용 오류: {str(e)}")
            self.summary_ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['danger']};")
        finally:
            self.summary_ai_apply_btn.setEnabled(True)
    
    def save_summary_ai_config(self, provider: str, api_key: str, selected_model: str):
        """정보요약 AI API 설정 저장"""
        try:
            from src.foundation.config import config_manager
            
            api_config = config_manager.load_api_config()
            
            # 제공자별로 API 키 저장 (기존 키와 동일한 필드 사용)
            if provider == "openai":
                api_config.openai_api_key = api_key
            elif provider == "gemini":
                api_config.gemini_api_key = api_key
            elif provider == "claude":
                api_config.claude_api_key = api_key
            
            # 선택된 요약 AI API 저장
            if provider == "openai":
                api_config.current_summary_ai_provider = "openai"
            elif provider == "gemini":
                api_config.current_summary_ai_provider = "google"  # service.py에서 "google"로 확인
            elif provider == "claude":
                api_config.current_summary_ai_provider = "anthropic"  # service.py에서 "anthropic"으로 확인
            
            # 선택된 요약 모델 저장
            api_config.current_summary_ai_model = selected_model
            
            success = config_manager.save_api_config(api_config)
            
            if success:
                logger.info(f"정보요약 AI API 설정 저장 완료: {provider} - {selected_model}")
            else:
                logger.error("정보요약 AI API 설정 저장 실패")
                
        except Exception as e:
            logger.error(f"정보요약 AI API 설정 저장 중 오류: {e}")
    
    def delete_summary_ai_key(self):
        """정보요약 AI API 삭제"""
        if not hasattr(self, 'current_summary_ai_provider') or not self.current_summary_ai_provider:
            return
            
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, "확인", 
            f"{self.summary_ai_provider_combo.currentText()} API 설정을 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                from src.foundation.config import config_manager
                
                api_config = config_manager.load_api_config()
                
                # 현재 설정된 요약 모델 정보 삭제
                api_config.current_summary_ai_model = ""
                api_config.current_summary_ai_provider = ""
                
                config_manager.save_api_config(api_config)
                
                # UI 완전 초기화
                self.summary_ai_api_key.clear()
                self.summary_ai_provider_combo.setCurrentText("AI 제공자를 선택하세요")
                self.summary_ai_model_combo.clear()
                self.summary_model_label.setVisible(False)
                self.summary_ai_model_combo.setVisible(False)
                self.summary_ai_config_group.setVisible(False)
                
                # 현재 제공자 정보 초기화
                self.current_summary_ai_provider = None
                if hasattr(self, 'current_summary_ai_model'):
                    self.current_summary_ai_model = None
                
                self.summary_ai_status.setText("🟡 API를 다시 설정해 주세요.")
                self.summary_ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['warning']};")
                
                self.api_settings_changed.emit()
                QMessageBox.information(self, "완료", "정보요약 AI API 설정이 삭제되었습니다.")
                
            except Exception as e:
                QMessageBox.critical(self, "오류", f"API 설정 삭제 실패: {str(e)}")
    
    def save_summary_ai_config_only(self):
        """정보요약 AI 모델 선택만 저장 (API 키 테스트 없이)"""
        try:
            if not hasattr(self, 'current_summary_ai_provider') or not self.current_summary_ai_provider:
                return
            
            selected_model = getattr(self, 'current_summary_ai_model', '')
            if not selected_model:
                selected_model = self.summary_ai_model_combo.currentText()
            
            if selected_model == "모델을 선택하세요":
                return
            
            from src.foundation.config import config_manager
            api_config = config_manager.load_api_config()
            
            # 선택된 요약 AI API와 모델 저장
            if self.current_summary_ai_provider == "openai":
                api_config.current_summary_ai_provider = "openai"
            elif self.current_summary_ai_provider == "gemini":
                api_config.current_summary_ai_provider = "google"
            elif self.current_summary_ai_provider == "claude":
                api_config.current_summary_ai_provider = "anthropic"
            
            api_config.current_summary_ai_model = selected_model
            
            success = config_manager.save_api_config(api_config)
            
            if success:
                logger.info(f"정보요약 AI 모델 선택 저장: {selected_model}")
                
        except Exception as e:
            logger.error(f"정보요약 AI 모델 선택 저장 오류: {e}")
    
    def delete_text_ai_api(self):
        """글 작성 AI API 삭제"""
        if not hasattr(self, 'current_text_ai_provider') or not self.current_text_ai_provider:
            return
            
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, "확인", 
            f"{self.text_ai_provider_combo.currentText()} API 설정을 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                from src.foundation.config import config_manager
                
                api_config = config_manager.load_api_config()
                
                if self.current_text_ai_provider == "openai":
                    api_config.openai_api_key = ""
                elif self.current_text_ai_provider == "claude":
                    api_config.claude_api_key = ""
                elif self.current_text_ai_provider == "gemini":
                    api_config.gemini_api_key = ""
                
                # 현재 설정된 모델 정보도 삭제
                api_config.current_text_ai_model = ""
                
                config_manager.save_api_config(api_config)
                
                # UI 완전 초기화
                self.text_ai_api_key.clear()
                self.text_ai_provider_combo.setCurrentText("AI 제공자를 선택하세요")
                self.text_ai_model_combo.clear()
                self.text_model_label.setVisible(False)
                self.text_ai_model_combo.setVisible(False)
                self.text_ai_config_group.setVisible(False)
                
                # 현재 제공자 정보 초기화
                self.current_text_ai_provider = None
                if hasattr(self, 'current_text_ai_model'):
                    self.current_text_ai_model = None
                
                self.text_ai_status.setText("🟡 API를 다시 설정해 주세요.")
                self.text_ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['warning']};")
                
                self.api_settings_changed.emit()
                QMessageBox.information(self, "완료", "글 작성 AI API 설정이 삭제되었습니다.")
                
            except Exception as e:
                QMessageBox.critical(self, "오류", f"API 설정 삭제 실패: {str(e)}")
    
    
    def test_openai_api_internal(self, api_key):
        """OpenAI API 내부 테스트 (UI 업데이트 없이)"""
        try:
            import requests
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # 최소한의 토큰으로 테스트 (약 10-20 토큰 정도)
            data = {
                "model": "gpt-3.5-turbo",  # 가장 저렴한 모델로 테스트
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 5  # 최소 토큰으로 제한
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    return True, "연결 성공"
                else:
                    return False, "API 응답이 예상과 다릅니다."
            elif response.status_code == 401:
                return False, "API 키가 유효하지 않습니다."
            elif response.status_code == 429:
                return False, "API 할당량을 초과했습니다."
            else:
                return False, f"상태 코드: {response.status_code}"
                
        except requests.exceptions.Timeout:
            return False, "연결 시간 초과"
        except requests.exceptions.RequestException as e:
            return False, f"네트워크 오류: {str(e)}"
        except Exception as e:
            return False, str(e)
    
    def test_gemini_api_internal(self, api_key):
        """Gemini API 내부 테스트 (UI 업데이트 없이)"""
        try:
            import requests
            
            # Gemini API 테스트 (최소 토큰으로)
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}"
            
            headers = {
                "Content-Type": "application/json"
            }
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": "Hi"  # 최소한의 텍스트로 테스트
                    }]
                }],
                "generationConfig": {
                    "maxOutputTokens": 5  # 최소 토큰으로 제한
                }
            }
            
            response = requests.post(
                url,
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    return True, "연결 성공"
                else:
                    return False, "API 응답이 예상과 다릅니다."
            elif response.status_code == 400:
                error_info = response.json()
                if 'error' in error_info:
                    return False, f"API 오류: {error_info['error'].get('message', '잘못된 요청')}"
                return False, "API 키가 유효하지 않거나 잘못된 요청입니다."
            elif response.status_code == 403:
                return False, "API 키가 유효하지 않습니다."
            elif response.status_code == 429:
                return False, "API 할당량을 초과했습니다."
            else:
                return False, f"상태 코드: {response.status_code}"
                
        except requests.exceptions.Timeout:
            return False, "연결 시간 초과"
        except requests.exceptions.RequestException as e:
            return False, f"네트워크 오류: {str(e)}"
        except Exception as e:
            return False, str(e)
    
    def test_claude_api_internal(self, api_key):
        """Claude API 내부 테스트 (UI 업데이트 없이)"""
        try:
            import requests
            
            headers = {
                "x-api-key": api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            
            # Claude API 테스트 (최소 토큰으로)
            data = {
                "model": "claude-3-haiku-20240307",  # 가장 저렴한 모델로 테스트
                "max_tokens": 5,  # 최소 토큰으로 제한
                "messages": [{"role": "user", "content": "Hi"}]
            }
            
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'content' in result and len(result['content']) > 0:
                    return True, "연결 성공"
                else:
                    return False, "API 응답이 예상과 다릅니다."
            elif response.status_code == 401:
                return False, "API 키가 유효하지 않습니다."
            elif response.status_code == 429:
                return False, "API 할당량을 초과했습니다."
            elif response.status_code == 400:
                error_info = response.json()
                if 'error' in error_info:
                    return False, f"API 오류: {error_info['error'].get('message', '잘못된 요청')}"
                return False, "잘못된 요청입니다."
            else:
                return False, f"상태 코드: {response.status_code}"
                
        except requests.exceptions.Timeout:
            return False, "연결 시간 초과"
        except requests.exceptions.RequestException as e:
            return False, f"네트워크 오류: {str(e)}"
        except Exception as e:
            return False, str(e)
    
    def setup_buttons(self, layout):
        """버튼 영역 설정"""
        button_layout = QHBoxLayout()
        
        # 반응형 버튼들로 교체
        delete_all_btn = ModernDangerButton("모든 API 삭제")
        delete_all_btn.clicked.connect(self.delete_all_apis)
        button_layout.addWidget(delete_all_btn)
        
        # 가운데 공간
        button_layout.addStretch()
        
        # 취소 버튼 (기본 스타일로 놔둠)
        from src.toolbox.ui_kit.components import ModernButton
        cancel_btn = ModernButton("취소", "secondary")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        # 저장 버튼
        save_btn = ModernSuccessButton("저장")
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def apply_styles(self):
        """반응형 스타일 적용"""
        scale = tokens.get_screen_scale_factor()
        
        # 스케일링된 크기 계산
        border_radius_sm = int(8 * scale)
        border_radius_xs = int(6 * scale)
        border_width = int(1 * scale)
        border_width_lg = int(2 * scale)
        padding_tab_v = int(10 * scale)
        padding_tab_h = int(20 * scale)
        padding_input_v = int(8 * scale)
        padding_input_h = int(12 * scale)
        padding_btn_v = int(tokens.GAP_10 * scale)
        padding_btn_h = int(tokens.GAP_20 * scale)
        margin_v = int(10 * scale)
        margin_right = int(2 * scale)
        padding_top = int(10 * scale)
        left_pos = int(10 * scale)
        title_padding = int(8 * scale)
        min_width_btn = int(100 * scale)
        font_size_normal = tokens.fpx(tokens.get_font_size('normal'))
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {ModernStyle.COLORS['bg_primary']};
                color: {ModernStyle.COLORS['text_primary']};
            }}
            QTabWidget::pane {{
                border: {border_width}px solid {ModernStyle.COLORS['border']};
                border-radius: {border_radius_sm}px;
                background-color: {ModernStyle.COLORS['bg_card']};
            }}
            QTabBar::tab {{
                background-color: {ModernStyle.COLORS['bg_input']};
                border: {border_width}px solid {ModernStyle.COLORS['border']};
                padding: {padding_tab_v}px {padding_tab_h}px;
                margin-right: {margin_right}px;
                border-bottom: none;
                font-weight: 500;
            }}
            QTabBar::tab:selected {{
                background-color: {ModernStyle.COLORS['bg_card']};
                border-bottom: {border_width}px solid {ModernStyle.COLORS['bg_card']};
                font-weight: 600;
            }}
            QGroupBox {{
                font-size: {font_size_normal}px;
                font-weight: 600;
                border: {border_width_lg}px solid {ModernStyle.COLORS['border']};
                border-radius: {border_radius_sm}px;
                margin: {margin_v}px 0;
                padding-top: {padding_top}px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {left_pos}px;
                padding: 0 {title_padding}px;
                background-color: {ModernStyle.COLORS['bg_card']};
            }}
            QLineEdit {{
                padding: {padding_input_v}px {padding_input_h}px;
                border: {border_width_lg}px solid {ModernStyle.COLORS['border']};
                border-radius: {border_radius_xs}px;
                font-size: {font_size_normal}px;
                background-color: {ModernStyle.COLORS['bg_primary']};
            }}
            QLineEdit:focus {{
                border-color: {ModernStyle.COLORS['primary']};
            }}
            QPushButton {{
                background-color: {ModernStyle.COLORS['primary']};
                color: white;
                border: none;
                padding: {padding_btn_v}px {padding_btn_h}px;
                border-radius: {tokens.RADIUS_SM}px;
                font-size: {font_size_normal}px;
                font-weight: 600;
                min-width: {min_width_btn}px;
            }}
            QPushButton:hover {{
                background-color: {ModernStyle.COLORS['primary_hover']};
            }}
        """)
    
    def load_settings(self):
        """foundation config_manager에서 API 키 로드"""
        try:
            from src.foundation.config import config_manager
            
            # foundation config에서 로드
            api_config = config_manager.load_api_config()
            
            # 네이버 검색광고 API
            self.searchad_access_license.setText(api_config.searchad_access_license)
            self.searchad_secret_key.setText(api_config.searchad_secret_key)
            self.searchad_customer_id.setText(api_config.searchad_customer_id)
            
            # 네이버 쇼핑 API
            self.shopping_client_id.setText(api_config.shopping_client_id)
            self.shopping_client_secret.setText(api_config.shopping_client_secret)
            
            # 글쓰기 AI API 설정 로드
            self.load_text_ai_settings(api_config)
            
            # 정보요약 AI API 설정 로드
            self.load_summary_ai_settings(api_config)
            
            # 이미지 생성 AI API 설정 로드
            self.load_image_ai_settings(api_config)
            
            # 로드 후 상태 체크
            self.check_api_status()
            
        except Exception as e:
            print(f"설정 로드 오류: {e}")
            self.check_api_status()
    
    def load_text_ai_settings(self, api_config):
        """글쓰기 AI 설정 로드 및 UI 복원"""
        try:
            # 현재 설정된 모델 확인
            current_model = getattr(api_config, 'current_text_ai_model', '')
            
            if current_model:
                # 모델에서 제공자 추출
                if 'GPT' in current_model:
                    provider = "OpenAI (GPT)"
                    self.current_text_ai_provider = "openai"
                elif 'Gemini' in current_model:
                    provider = "Google (Gemini)"
                    self.current_text_ai_provider = "gemini"
                elif 'Claude' in current_model:
                    provider = "Anthropic (Claude)"
                    self.current_text_ai_provider = "claude"
                else:
                    return
                
                # 제공자 콤보박스 설정 (이벤트 트리거를 일시적으로 차단)
                self.text_ai_provider_combo.blockSignals(True)
                self.text_ai_provider_combo.setCurrentText(provider)
                self.text_ai_provider_combo.blockSignals(False)
                
                # 수동으로 제공자 변경 처리
                self.on_text_ai_provider_changed(provider)
                
                # 모델 콤보박스 설정
                if hasattr(self, 'text_ai_model_combo'):
                    for i in range(self.text_ai_model_combo.count()):
                        if current_model in self.text_ai_model_combo.itemText(i):
                            self.text_ai_model_combo.setCurrentIndex(i)
                            # 수동으로 모델 변경 처리
                            self.on_text_ai_model_changed(current_model)
                            break
                
                # 상태 표시
                if hasattr(self, 'text_ai_status'):
                    self.text_ai_status.setText(f"✅ {current_model} API가 설정되었습니다.")
                    self.text_ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['success']};")
                    
        except Exception as e:
            logger.error(f"글쓰기 AI 설정 로드 실패: {e}")
    
    def load_image_ai_settings(self, api_config):
        """이미지 생성 AI 설정 로드 및 UI 복원"""
        try:
            # 현재 설정된 모델 확인
            current_model = getattr(api_config, 'current_image_ai_model', '')
            
            if current_model:
                # 모델에서 제공자 추출
                if 'DALL-E' in current_model:
                    provider = "OpenAI (DALL-E)"
                    self.current_image_ai_provider = "dalle"
                elif 'Imagen' in current_model:
                    provider = "Google (Imagen)"
                    self.current_image_ai_provider = "imagen"
                else:
                    return
                
                # 제공자 콤보박스 설정 (이벤트 트리거를 일시적으로 차단)
                self.image_ai_provider_combo.blockSignals(True)
                self.image_ai_provider_combo.setCurrentText(provider)
                self.image_ai_provider_combo.blockSignals(False)
                
                # 수동으로 제공자 변경 처리
                self.on_image_ai_provider_changed(provider)
                
                # 모델 콤보박스 설정
                if hasattr(self, 'image_ai_model_combo'):
                    for i in range(self.image_ai_model_combo.count()):
                        if current_model in self.image_ai_model_combo.itemText(i):
                            self.image_ai_model_combo.setCurrentIndex(i)
                            # 수동으로 모델 변경 처리
                            self.on_image_ai_model_changed(current_model)
                            break
                
                # 상태 표시
                if hasattr(self, 'image_ai_status'):
                    self.image_ai_status.setText(f"✅ {current_model} API가 설정되었습니다.")
                    self.image_ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['success']};")
                    
        except Exception as e:
            logger.error(f"이미지 생성 AI 설정 로드 실패: {e}")
    
    def load_summary_ai_settings(self, api_config):
        """정보요약 AI 설정 로드 및 UI 복원"""
        try:
            # 현재 설정된 모델 확인
            current_model = getattr(api_config, 'current_summary_ai_model', '')
            
            if current_model:
                # 모델에서 제공자 추출
                if 'GPT' in current_model:
                    provider = "OpenAI (GPT)"
                    self.current_summary_ai_provider = "openai"
                elif 'Gemini' in current_model:
                    provider = "Google (Gemini)"
                    self.current_summary_ai_provider = "gemini"
                elif 'Claude' in current_model:
                    provider = "Anthropic (Claude)"
                    self.current_summary_ai_provider = "claude"
                else:
                    return
                
                # 제공자 콤보박스 설정 (이벤트 트리거를 일시적으로 차단)
                self.summary_ai_provider_combo.blockSignals(True)
                self.summary_ai_provider_combo.setCurrentText(provider)
                self.summary_ai_provider_combo.blockSignals(False)
                
                # 수동으로 제공자 변경 처리
                self.on_summary_ai_provider_changed(provider)
                
                # 모델 콤보박스 설정
                if hasattr(self, 'summary_ai_model_combo'):
                    for i in range(self.summary_ai_model_combo.count()):
                        if current_model in self.summary_ai_model_combo.itemText(i):
                            self.summary_ai_model_combo.setCurrentIndex(i)
                            # 수동으로 모델 변경 처리
                            self.on_summary_ai_model_changed(current_model)
                            break
                
                # 상태 표시
                if hasattr(self, 'summary_ai_status'):
                    self.summary_ai_status.setText(f"✅ {current_model} API가 설정되었습니다.")
                    self.summary_ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['success']};")
                    
        except Exception as e:
            logger.error(f"정보요약 AI 설정 로드 실패: {e}")
    
    def save_settings(self):
        """설정 저장 (foundation config_manager 사용)"""
        try:
            from src.foundation.config import config_manager
            
            # 현재 설정 로드
            api_config = config_manager.load_api_config()
            
            # 네이버 API 설정 업데이트 (텍스트 필드 값으로)
            api_config.searchad_access_license = self.searchad_access_license.text().strip()
            api_config.searchad_secret_key = self.searchad_secret_key.text().strip()
            api_config.searchad_customer_id = self.searchad_customer_id.text().strip()
            
            api_config.shopping_client_id = self.shopping_client_id.text().strip()
            api_config.shopping_client_secret = self.shopping_client_secret.text().strip()
            
            # AI API 설정은 각 탭에서 개별적으로 저장됨
            
            # foundation config_manager로 저장
            success = config_manager.save_api_config(api_config)
            
            if success:
                QMessageBox.information(self, "완료", "API 설정이 저장되었습니다.")
                self.api_settings_changed.emit()  # 설정 변경 시그널 발송
                self.accept()
            else:
                QMessageBox.critical(self, "오류", "API 설정 저장에 실패했습니다.")
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"설정 저장 실패: {str(e)}")
    
    
    def apply_searchad_api(self):
        """검색광고 API 테스트 후 적용"""
        access_license = self.searchad_access_license.text().strip()
        secret_key = self.searchad_secret_key.text().strip()
        customer_id = self.searchad_customer_id.text().strip()
        
        if not all([access_license, secret_key, customer_id]):
            self.searchad_status.setText("⚠️ 모든 필드를 입력해주세요.")
            self.searchad_status.setStyleSheet(f"color: {ModernStyle.COLORS['danger']};")
            return
        
        self.searchad_status.setText("테스트 및 적용 중...")
        self.searchad_status.setStyleSheet(f"color: {ModernStyle.COLORS['primary']};")
        self.searchad_apply_btn.setEnabled(False)
        
        try:
            # 테스트 먼저 실행
            result = self.test_searchad_api_internal(access_license, secret_key, customer_id)
            if result[0]:  # 테스트 성공시 자동 적용
                # 설정 저장
                self.save_searchad_config(access_license, secret_key, customer_id)
                self.searchad_status.setText("✅ 네이버 검색광고 API가 적용되었습니다.")
                self.searchad_status.setStyleSheet(f"color: {ModernStyle.COLORS['success']};")
                self.api_settings_changed.emit()  # API 적용 시그널 발송
            else:
                self.searchad_status.setText(f"❌ 연결 실패: {result[1]}")
                self.searchad_status.setStyleSheet(f"color: {ModernStyle.COLORS['danger']};")
                
        except Exception as e:
            self.searchad_status.setText(f"❌ 적용 오류: {str(e)}")
            self.searchad_status.setStyleSheet(f"color: {ModernStyle.COLORS['danger']};")
        finally:
            self.searchad_apply_btn.setEnabled(True)
    
    def test_searchad_api_internal(self, access_license, secret_key, customer_id):
        """검색광고 API 내부 테스트 (UI 업데이트 없이)"""
        import requests
        import hashlib
        import hmac
        import base64
        import time
        
        try:
            uri = '/keywordstool'
            timestamp = str(int(time.time() * 1000))
            message = f"{timestamp}.GET.{uri}"
            signature = hmac.new(secret_key.encode(), message.encode(), hashlib.sha256).digest()
            signature = base64.b64encode(signature).decode()
            
            headers = {
                'Content-Type': 'application/json; charset=UTF-8',
                'X-Timestamp': timestamp,
                'X-API-KEY': access_license,
                'X-Customer': customer_id,
                'X-Signature': signature
            }
            
            params = {'hintKeywords': '테스트', 'showDetail': '1'}
            
            response = requests.get(
                'https://api.searchad.naver.com' + uri,
                params=params,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'keywordList' in data:
                    return True, "연결 성공"
                else:
                    return False, "API 응답이 예상과 다릅니다."
            else:
                return False, f"상태 코드: {response.status_code}"
                
        except Exception as e:
            return False, str(e)
    
    
    def apply_shopping_api(self):
        """쇼핑 API 테스트 후 적용"""
        client_id = self.shopping_client_id.text().strip()
        client_secret = self.shopping_client_secret.text().strip()
        
        if not all([client_id, client_secret]):
            self.shopping_status.setText("⚠️ 모든 필드를 입력해주세요.")
            self.shopping_status.setStyleSheet(f"color: {ModernStyle.COLORS['danger']};")
            return
        
        self.shopping_status.setText("테스트 및 적용 중...")
        self.shopping_status.setStyleSheet(f"color: {ModernStyle.COLORS['primary']};")
        self.shopping_apply_btn.setEnabled(False)
        
        try:
            # 테스트 먼저 실행
            result = self.test_shopping_api_internal(client_id, client_secret)
            if result[0]:  # 테스트 성공시 자동 적용
                # 설정 저장
                self.save_shopping_config(client_id, client_secret)
                self.shopping_status.setText("✅ 네이버 개발자 API가 적용되었습니다.")
                self.shopping_status.setStyleSheet(f"color: {ModernStyle.COLORS['success']};")
                self.api_settings_changed.emit()  # API 적용 시그널 발송
            else:
                self.shopping_status.setText(f"❌ 연결 실패: {result[1]}")
                self.shopping_status.setStyleSheet(f"color: {ModernStyle.COLORS['danger']};")
                
        except Exception as e:
            self.shopping_status.setText(f"❌ 적용 오류: {str(e)}")
            self.shopping_status.setStyleSheet(f"color: {ModernStyle.COLORS['danger']};")
        finally:
            self.shopping_apply_btn.setEnabled(True)
    
    def test_shopping_api_internal(self, client_id, client_secret):
        """쇼핑 API 내부 테스트 (UI 업데이트 없이)"""
        import requests
        
        try:
            headers = {
                "X-Naver-Client-Id": client_id,
                "X-Naver-Client-Secret": client_secret
            }
            params = {'query': '테스트', 'display': 1}
            
            response = requests.get(
                "https://openapi.naver.com/v1/search/shop.json",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'items' in data:
                    return True, "연결 성공"
                else:
                    return False, "API 응답이 예상과 다릅니다."
            else:
                return False, f"상태 코드: {response.status_code}"
                
        except Exception as e:
            return False, str(e)
    
    
    def save_searchad_config(self, access_license, secret_key, customer_id):
        """검색광고 API 설정만 저장 (foundation config_manager 사용)"""
        try:
            from src.foundation.config import config_manager
            
            # 현재 설정 로드
            api_config = config_manager.load_api_config()
            
            # 검색광고 API 설정 업데이트
            api_config.searchad_access_license = access_license
            api_config.searchad_secret_key = secret_key
            api_config.searchad_customer_id = customer_id
            
            # foundation config_manager로 저장
            config_manager.save_api_config(api_config)
                
        except Exception as e:
            print(f"검색광고 API 설정 저장 오류: {e}")
    
    def save_shopping_config(self, client_id, client_secret):
        """쇼핑 API 설정만 저장 (foundation config_manager 사용)"""
        try:
            from src.foundation.config import config_manager
            
            # 현재 설정 로드
            api_config = config_manager.load_api_config()
            
            # 쇼핑 API 설정 업데이트
            api_config.shopping_client_id = client_id
            api_config.shopping_client_secret = client_secret
            
            # foundation config_manager로 저장
            config_manager.save_api_config(api_config)
                
        except Exception as e:
            print(f"쇼핑 API 설정 저장 오류: {e}")
    
    def check_api_status(self):
        """API 상태 체크 및 표시 (foundation config_manager 사용)"""
        try:
            from src.foundation.config import config_manager
            
            # foundation config에서 로드
            api_config = config_manager.load_api_config()
            
            # 검색광고 API 상태 체크
            if api_config.is_searchad_valid():
                self.searchad_status.setText("✅ 네이버 검색광고 API가 설정되었습니다.")
                self.searchad_status.setStyleSheet(f"color: {ModernStyle.COLORS['success']};")
            else:
                self.searchad_status.setText("🟡 네이버 검색광고 API를 적용해 주세요.")
                self.searchad_status.setStyleSheet(f"color: {ModernStyle.COLORS['warning']};")
            
            # 쇼핑 API 상태 체크
            if api_config.is_shopping_valid():
                self.shopping_status.setText("✅ 네이버 개발자 API가 설정되었습니다.")
                self.shopping_status.setStyleSheet(f"color: {ModernStyle.COLORS['success']};")
            else:
                self.shopping_status.setText("🟡 네이버 개발자 API를 적용해 주세요.")
                self.shopping_status.setStyleSheet(f"color: {ModernStyle.COLORS['warning']};")
            
            # AI API 상태 체크
            if hasattr(self, 'ai_status'):
                has_ai = (api_config.openai_api_key or api_config.claude_api_key or 
                         getattr(api_config, 'gemini_api_key', ''))
                if has_ai:
                    # 어떤 AI가 설정되어 있는지 확인
                    if api_config.openai_api_key:
                        provider_name = "OpenAI"
                    elif api_config.claude_api_key:
                        provider_name = "Claude"
                    elif getattr(api_config, 'gemini_api_key', ''):
                        provider_name = "Gemini"
                    else:
                        provider_name = "AI"
                    
                    self.ai_status.setText(f"✅ {provider_name} API가 설정되었습니다.")
                    self.ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['success']};")
                else:
                    self.ai_status.setText("🟡 AI API를 설정해 주세요.")
                    self.ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['warning']};")
                
        except Exception as e:
            print(f"API 상태 체크 오류: {e}")
            # 오류시 기본 상태
            self.searchad_status.setText("🟡 네이버 검색광고 API를 적용해 주세요.")
            self.searchad_status.setStyleSheet(f"color: {ModernStyle.COLORS['warning']};")
            self.shopping_status.setText("🟡 네이버 개발자 API를 적용해 주세요.")
            self.shopping_status.setStyleSheet(f"color: {ModernStyle.COLORS['warning']};")
            if hasattr(self, 'ai_status'):
                self.ai_status.setText("🟡 AI API를 설정해 주세요.")
                self.ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['warning']};")
    

    def delete_shopping_api(self):
        """쇼핑 API 삭제 (foundation config_manager 사용)"""
        reply = QMessageBox.question(
            self, "확인", 
            "네이버 개발자 API 설정을 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                from src.foundation.config import config_manager
                
                # 현재 설정 로드
                api_config = config_manager.load_api_config()
                
                # 쇼핑 API 설정 초기화
                api_config.shopping_client_id = ""
                api_config.shopping_client_secret = ""
                
                # foundation config_manager로 저장
                config_manager.save_api_config(api_config)
                
                # UI 초기화
                self.shopping_client_id.clear()
                self.shopping_client_secret.clear()
                self.shopping_status.setText("🟡 네이버 개발자 API를 적용해 주세요.")
                self.shopping_status.setStyleSheet(f"color: {ModernStyle.COLORS['warning']};")
                
                # 시그널 발송
                self.api_settings_changed.emit()
                
                QMessageBox.information(self, "완료", "네이버 개발자 API 설정이 삭제되었습니다.")
                
            except Exception as e:
                QMessageBox.critical(self, "오류", f"API 설정 삭제 실패: {str(e)}")
    
    def delete_searchad_api(self):
        """검색광고 API 삭제 (foundation config_manager 사용)"""
        reply = QMessageBox.question(
            self, "확인", 
            "네이버 검색광고 API 설정을 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                from src.foundation.config import config_manager
                
                # 현재 설정 로드
                api_config = config_manager.load_api_config()
                
                # 검색광고 API 설정 초기화
                api_config.searchad_access_license = ""
                api_config.searchad_secret_key = ""
                api_config.searchad_customer_id = ""
                
                # foundation config_manager로 저장
                config_manager.save_api_config(api_config)
                
                # UI 초기화
                self.searchad_access_license.clear()
                self.searchad_secret_key.clear()
                self.searchad_customer_id.clear()
                self.searchad_status.setText("🟡 네이버 검색광고 API를 적용해 주세요.")
                self.searchad_status.setStyleSheet(f"color: {ModernStyle.COLORS['warning']};")
                
                # 시그널 발송
                self.api_settings_changed.emit()
                
                QMessageBox.information(self, "완료", "네이버 검색광고 API 설정이 삭제되었습니다.")
                
            except Exception as e:
                QMessageBox.critical(self, "오류", f"API 설정 삭제 실패: {str(e)}")
    
    def delete_all_apis(self):
        """모든 API 삭제 (foundation config_manager 사용)"""
        reply = QMessageBox.question(
            self, "확인", 
            "모든 API 설정을 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                from src.foundation.config import config_manager
                from src.foundation.config import APIConfig
                
                # 빈 API 설정으로 초기화
                empty_config = APIConfig()
                config_manager.save_api_config(empty_config)
                
                # 모든 UI 초기화
                self.shopping_client_id.clear()
                self.shopping_client_secret.clear()
                self.searchad_access_license.clear()
                self.searchad_secret_key.clear()
                self.searchad_customer_id.clear()
                
                # 텍스트 AI 설정 초기화
                if hasattr(self, 'text_ai_api_key'):
                    self.text_ai_api_key.clear()
                if hasattr(self, 'text_ai_provider_combo'):
                    self.text_ai_provider_combo.setCurrentText("AI 제공자를 선택하세요")
                if hasattr(self, 'text_ai_config_group'):
                    self.text_ai_config_group.setVisible(False)
                
                # 정보요약 AI 설정 초기화
                if hasattr(self, 'summary_ai_api_key'):
                    self.summary_ai_api_key.clear()
                if hasattr(self, 'summary_ai_provider_combo'):
                    self.summary_ai_provider_combo.setCurrentText("AI 제공자를 선택하세요")
                if hasattr(self, 'summary_ai_config_group'):
                    self.summary_ai_config_group.setVisible(False)
                
                # 이미지 AI 설정 초기화
                if hasattr(self, 'image_ai_api_key'):
                    self.image_ai_api_key.clear()
                if hasattr(self, 'image_ai_provider_combo'):
                    self.image_ai_provider_combo.setCurrentText("AI 제공자를 선택하세요")
                if hasattr(self, 'image_ai_config_group'):
                    self.image_ai_config_group.setVisible(False)
                
                # 상태 초기화
                self.shopping_status.setText("🟡 네이버 개발자 API를 적용해 주세요.")
                self.shopping_status.setStyleSheet(f"color: {ModernStyle.COLORS['warning']};")
                self.searchad_status.setText("🟡 네이버 검색광고 API를 적용해 주세요.")
                self.searchad_status.setStyleSheet(f"color: {ModernStyle.COLORS['warning']};")
                
                if hasattr(self, 'text_ai_status'):
                    self.text_ai_status.setText("🟡 API를 설정해 주세요.")
                    self.text_ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['warning']};")
                
                if hasattr(self, 'summary_ai_status'):
                    self.summary_ai_status.setText("🟡 API를 설정해 주세요.")
                    self.summary_ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['warning']};")
                
                if hasattr(self, 'image_ai_status'):
                    self.image_ai_status.setText("🟡 API를 설정해 주세요.")
                    self.image_ai_status.setStyleSheet(f"color: {ModernStyle.COLORS['warning']};")
                
                # 시그널 발송
                self.api_settings_changed.emit()
                
                QMessageBox.information(self, "완료", "모든 API 설정이 삭제되었습니다.")
                
            except Exception as e:
                QMessageBox.critical(self, "오류", f"API 설정 삭제 실패: {str(e)}")
    
    def show_naver_help(self):
        """네이버 API 발급방법 도움말 표시"""
        cards_data = [
            {
                'title': '🔍 네이버 검색광고 API',
                'steps': [
                    '<a href="https://manage.searchad.naver.com">https://manage.searchad.naver.com</a> 접속',
                    '네이버 계정으로 로그인',
                    '<strong>도구 → API 사용관리</strong> 메뉴 클릭',
                    '<strong>"네이버 검색광고 API 서비스 신청"</strong> 버튼 클릭',
                    '신청 완료 후 액세스 라이선스, 비밀키, Customer ID 확인'
                ],
                'note': '즉시 발급 가능합니다',
                'warnings': [
                    'API 키는 개인정보이므로 타인과 공유하지 마세요',
                    '검색광고 API는 비즈니스 계정이 필요할 수 있습니다'
                ]
            },
            {
                'title': '🛒 네이버 개발자 API',
                'steps': [
                    '<a href="https://developers.naver.com/main/">https://developers.naver.com/main/</a> 접속',
                    '"Application 등록" → "애플리케이션 정보 입력"',
                    '"사용 API" 에서 "검색" 체크',
                    '등록 완료 후 Client ID, Client Secret 확인'
                ],
                'note': '즉시 발급 가능합니다',
                'warnings': [
                    '개발자 API는 일일 호출 제한이 있습니다'
                ]
            }
        ]
        
        self.show_card_help_dialog("네이버 API 발급방법", cards_data)
    
    
    def show_text_ai_help(self):
        """글 작성 AI API 발급방법 도움말 표시"""
        cards_data = [
            {
                'title': '📋 OpenAI (GPT) API',
                'steps': [
                    '<a href="https://platform.openai.com">https://platform.openai.com</a> 접속',
                    '우상단 "API" 메뉴 클릭',
                    '좌측 "API keys" 메뉴에서 "Create new secret key" 클릭',
                    '키 이름 입력 후 생성',
                    '생성된 키를 복사하여 붙여넣기'
                ],
                'cost': '비용: GPT-4o Mini $0.15/1M토큰, GPT-4o $5/1M토큰',
                'note': '키는 한 번만 표시되므로 안전하게 보관하세요'
            },
            {
                'title': '🧠 Google (Gemini) API',
                'steps': [
                    '<a href="https://aistudio.google.com">https://aistudio.google.com</a> 접속',
                    '"Get API key" 버튼 클릭',
                    '"Create API key in new project" 선택',
                    '생성된 키를 복사하여 붙여넣기'
                ],
                'cost': '무료: Flash 모델 15회/분, Pro 모델 $7/1M토큰',
                'note': '초기 크레딧 $300 제공'
            },
            {
                'title': '🌟 Anthropic (Claude) API',
                'steps': [
                    '<a href="https://console.anthropic.com">https://console.anthropic.com</a> 접속',
                    '좌측 "API Keys" 메뉴 클릭',
                    '"Create Key" 버튼 클릭',
                    '키 이름 입력 후 생성',
                    '생성된 키를 복사하여 붙여넣기'
                ],
                'cost': '비용: Haiku $0.25/1M토큰, Sonnet $3/1M토큰, Opus $15/1M토큰',
                'note': '초기 크레딧 $5 제공'
            }
        ]
        
        self.show_card_help_dialog("글 작성 AI API 발급방법", cards_data)
    
    def show_image_ai_help(self):
        """이미지 생성 AI API 발급방법 도움말 표시"""
        cards_data = [
            {
                'title': '🎨 OpenAI (DALL-E) API',
                'steps': [
                    '<a href="https://platform.openai.com">https://platform.openai.com</a> 접속',
                    '우상단 "API" 메뉴 클릭',
                    '좌측 "API keys" 메뉴에서 "Create new secret key" 클릭',
                    '키 이름 입력 후 생성 (글 작성 AI와 동일한 키 사용 가능)',
                    '생성된 키를 복사하여 붙여넣기'
                ],
                'cost': '비용: DALL-E 3 $0.040/이미지, DALL-E 2 $0.016/이미지',
                'note': '고품질 1024x1024 이미지 생성 가능',
                'warnings': [
                    '이미지 생성은 비용이 많이 드는 작업입니다',
                    '한 번에 여러 이미지를 생성하면 비용이 급상승합니다'
                ]
            },
            {
                'title': '🖼️ Google (Imagen) API',
                'steps': [
                    '<a href="https://cloud.google.com/console">Google Cloud Console</a> 접속',
                    '새 프로젝트 생성 또는 기존 프로젝트 선택',
                    'Vertex AI API 활성화',
                    '서비스 계정 생성 및 JSON 키 다운로드',
                    '환경 변수 또는 키 파일 경로 설정'
                ],
                'cost': '비용: Imagen 3 약 $0.020/이미지 (버텍스 AI 기준)',
                'note': '복잡한 설정 과정, Google Cloud 크레딧 필요',
                'warnings': [
                    'API 사용량을 주기적으로 확인하세요',
                    '저작권을 준수하는 이미지를 생성하세요'
                ]
            }
        ]
        
        self.show_card_help_dialog("이미지 생성 AI API 발급방법", cards_data)
    
    def show_help_dialog(self, title: str, content: str):
        """기존 ModernScrollableDialog를 사용한 도움말 다이얼로그"""
        from src.toolbox.ui_kit.modern_dialog import ModernScrollableDialog
        
        dialog = ModernScrollableDialog(
            parent=self,
            title=title,
            message=content,
            confirm_text="확인",
            cancel_text=None,
            icon="📋"
        )
        dialog.exec()
    
    def show_card_help_dialog(self, title: str, cards_data: list):
        """카드 데이터를 HTML로 변환하여 도움말 다이얼로그 표시"""
        html_content = ""
        
        for card in cards_data:
            html_content += f"<h3 style='color: #2c5aa0; margin: 20px 0 10px 0;'>{card['title']}</h3>"
            
            # 단계별 설명
            if 'steps' in card:
                html_content += "<ol style='margin: 10px 0; padding-left: 20px;'>"
                for step in card['steps']:
                    html_content += f"<li style='margin: 5px 0; line-height: 1.5;'>{step}</li>"
                html_content += "</ol>"
            
            # 비용 정보
            if 'cost' in card:
                html_content += f"<p style='background-color: #f0f8ff; padding: 8px; border-left: 4px solid #2c5aa0; margin: 10px 0; font-size: 13px;'><strong>💰 {card['cost']}</strong></p>"
            
            # 참고사항
            if 'note' in card:
                html_content += f"<p style='background-color: #f0fff0; padding: 8px; border-left: 4px solid #28a745; margin: 10px 0; font-size: 13px;'><strong>📝 {card['note']}</strong></p>"
            
            # 주의사항
            if 'warnings' in card:
                html_content += "<div style='background-color: #fff8f0; padding: 8px; border-left: 4px solid #ffa500; margin: 10px 0; font-size: 13px;'>"
                html_content += "<strong>⚠️ 주의사항:</strong><ul style='margin: 5px 0; padding-left: 20px;'>"
                for warning in card['warnings']:
                    html_content += f"<li style='margin: 3px 0;'>{warning}</li>"
                html_content += "</ul></div>"
            
            html_content += "<hr style='margin: 20px 0; border: none; border-top: 1px solid #e0e0e0;'>"
        
        # 마지막 구분선 제거
        if html_content.endswith("<hr style='margin: 20px 0; border: none; border-top: 1px solid #e0e0e0;'>"):
            html_content = html_content[:-85]
        
        self.show_help_dialog(title, html_content)  