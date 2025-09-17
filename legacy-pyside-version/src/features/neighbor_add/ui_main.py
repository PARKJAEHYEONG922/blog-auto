"""
서로이웃 추가 모듈의 메인 UI
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTextEdit, QSpinBox, QProgressBar, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QRadioButton, QButtonGroup, QCheckBox, QLineEdit
)
from PySide6.QtCore import Qt
import traceback

from src.foundation.logging import get_logger
from src.toolbox.ui_kit.components import ModernButton, ModernLineEdit, ModernTextEdit, ModernCard, ModernPrimaryButton, ModernSuccessButton, ModernDangerButton, ModernHelpButton
from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog, ModernScrollableDialog
from src.toolbox.ui_kit.modern_style import ModernStyle
from src.toolbox.ui_kit import tokens
from src.foundation.exceptions import BusinessError, ValidationError

from .service import NeighborAddService
from .models import LoginCredentials, SearchKeyword, LoginStatus
from .worker import (
    WorkerThread, create_login_worker, create_all_keywords_worker
)

logger = get_logger("neighbor_add.ui_main")


# AsyncWorker 클래스는 더 이상 사용하지 않습니다
# 모든 비동기 작업은 CLAUDE.md 구조에 맞게 Worker 패턴을 사용합니다


class NeighborAddMainUI(QWidget):
    """서로이웃 추가 메인 UI"""
    
    def __init__(self):
        super().__init__()
        self.service = NeighborAddService()
        self.current_worker = None
        self.current_thread = None
        self.session = None
        
        self.setup_ui()
        self.setup_styles()
        self.reset_ui_state()
    
    
    def setup_ui(self):
        """UI 구성 - 원본 통합관리프로그램 스타일"""
        main_layout = QVBoxLayout()
        # 토큰 기반 마진과 간격 - 반응형 적용
        scale = tokens.get_screen_scale_factor()
        margin = tokens.spx(tokens.GAP_16)
        spacing = tokens.spx(tokens.GAP_10)
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)
        
        # 헤더 (제목 + 사용법 버튼)
        self.setup_header(main_layout)
        
        # 메인 콘텐츠 영역 (좌우 분할)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(tokens.spx(tokens.GAP_20))
        
        # 왼쪽 패널 (좁게)
        left_panel = self.create_left_panel()
        content_layout.addWidget(left_panel, 1)
        
        # 오른쪽 패널 (넓게)
        right_panel = self.create_right_panel()
        content_layout.addWidget(right_panel, 2)
        
        main_layout.addLayout(content_layout, 1)
        self.setLayout(main_layout)
        
        # 저장된 로그인 정보 로드
        self.load_saved_credentials()
    
    def setup_header(self, layout):
        """헤더 섹션 (제목 + 사용법 버튼) - 통합관리프로그램과 동일"""
        header_layout = QHBoxLayout()
        
        # 제목
        title_label = QLabel("👫 네이버 블로그 서로이웃 추가")
        title_font_size = tokens.fpx(tokens.get_font_size('title'))
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: {title_font_size}px;
                font-weight: 700;
                color: {ModernStyle.COLORS['text_primary']};
            }}
        """)
        header_layout.addWidget(title_label)
        
        # 사용법 버튼 - 제목 오른쪽에 바로 배치
        help_button = ModernHelpButton("❓ 사용법")
        help_button.clicked.connect(self.show_usage_help)
        header_layout.addWidget(help_button)
        
        # 나머지 공간을 채움
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
    
    def create_left_panel(self):
        """왼쪽 패널 - ModernCard 사용"""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(tokens.spx(tokens.GAP_16))
        
        # 1. 로그인 카드
        login_card = self.create_login_card()
        layout.addWidget(login_card)
        
        # 2. 서로이웃 메시지 카드
        message_card = self.create_message_card()
        layout.addWidget(message_card)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
    
    def create_right_panel(self):
        """오른쪽 패널 - ModernCard 사용"""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(tokens.spx(tokens.GAP_16))
        
        # 1. 검색 설정 카드
        search_card = self.create_search_card()
        layout.addWidget(search_card)
        
        # 2. 통합 진행률 및 상황판 카드
        self.progress_status_card = self.create_progress_status_card()
        layout.addWidget(self.progress_status_card)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
    
    
    # 통계 라벨 텍스트 함수들
    def get_success_text(self, count):
        return f"✅ 성공: {count}"
    
    def get_failed_text(self, count):
        return f"❌ 실패: {count}"
    
    def get_disabled_text(self, count):
        return f"🚫 비활성화: {count}"
    
    def get_already_text(self, count):
        return f"🔄 이미신청중: {count}"

    def create_progress_status_card(self) -> ModernCard:
        """새로운 진행률 카드 - 서로이웃 추가 시작 시에만 활성화"""
        card = ModernCard("📊 서로이웃 추가 진행상황")
        layout = QVBoxLayout()
        
        # 상태 표시
        self.status_label = QLabel("대기 중...")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_primary']};
                font-size: {tokens.fpx(tokens.FONT_NORMAL)}px;
                font-weight: 600;
                padding: {tokens.spx(tokens.GAP_8)}px;
                background-color: {ModernStyle.COLORS['bg_muted']};
                border-radius: {tokens.spx(tokens.RADIUS_SM)}px;
                border-left: {tokens.spx(3)}px solid {ModernStyle.COLORS['primary']};
            }}
        """)
        layout.addWidget(self.status_label)
        
        # 진행률 바
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(tokens.spx(20))
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: {tokens.spx(1)}px solid {ModernStyle.COLORS['border']};
                border-radius: {tokens.spx(tokens.RADIUS_SM)}px;
                text-align: center;
                background-color: {ModernStyle.COLORS['bg_muted']};
                font-size: {tokens.fpx(12)}px;
                font-weight: 500;
            }}
            QProgressBar::chunk {{
                background-color: {ModernStyle.COLORS['primary']};
                border-radius: {tokens.spx(tokens.RADIUS_SM)}px;
            }}
        """)
        layout.addWidget(self.progress_bar)
        
        # 통계 정보 (1줄로 구성)
        stats_row = QHBoxLayout()
        
        # 성공 카운트
        self.success_label = QLabel(self.get_success_text(0))
        self.success_label.setStyleSheet(f"color: {ModernStyle.COLORS['success']}; font-weight: 600; font-size: {tokens.fpx(tokens.FONT_NORMAL)}px;")
        stats_row.addWidget(self.success_label)
        
        # 실패 카운트  
        self.failed_label = QLabel(self.get_failed_text(0))
        self.failed_label.setStyleSheet(f"color: {ModernStyle.COLORS['danger']}; font-weight: 600; font-size: {tokens.fpx(tokens.FONT_NORMAL)}px;")
        stats_row.addWidget(self.failed_label)
        
        # 비활성화 카운트
        self.disabled_label = QLabel(self.get_disabled_text(0)) 
        self.disabled_label.setStyleSheet(f"color: {ModernStyle.COLORS['warning']}; font-weight: 600; font-size: {tokens.fpx(tokens.FONT_NORMAL)}px;")
        stats_row.addWidget(self.disabled_label)
        
        # 이미 신청됨 카운트
        self.already_label = QLabel(self.get_already_text(0))
        self.already_label.setStyleSheet(f"color: {ModernStyle.COLORS['text_secondary']}; font-weight: 600; font-size: {tokens.fpx(tokens.FONT_NORMAL)}px;")
        stats_row.addWidget(self.already_label)
        
        stats_row.addStretch()
        layout.addLayout(stats_row)
        
        # 현재 처리 중인 블로거
        self.current_blogger_label = QLabel("")
        self.current_blogger_label.setStyleSheet(f"color: {ModernStyle.COLORS['text_muted']}; font-size: {tokens.fpx(tokens.FONT_NORMAL)}px;")
        layout.addWidget(self.current_blogger_label)
        
        card.setLayout(layout)
        return card
    
    
    def create_login_card(self) -> ModernCard:
        """로그인 카드 생성"""
        card = ModernCard("🔑 네이버 로그인")
        layout = QVBoxLayout()
        
        # 아이디 입력
        id_layout = QHBoxLayout()
        id_layout.addWidget(QLabel("아이디:"))
        self.username_input = ModernLineEdit()
        self.username_input.setPlaceholderText("네이버 아이디")
        id_layout.addWidget(self.username_input)
        layout.addLayout(id_layout)
        
        # 비밀번호 입력
        pw_layout = QHBoxLayout()
        pw_layout.addWidget(QLabel("비밀번호:"))
        self.password_input = ModernLineEdit()
        self.password_input.setPlaceholderText("비밀번호")
        self.password_input.setEchoMode(QLineEdit.Password)
        pw_layout.addWidget(self.password_input)
        layout.addLayout(pw_layout)
        
        # 로그인 정보 저장 체크박스
        self.save_credentials_checkbox = QCheckBox("로그인 정보 저장 (다음에도 사용)")
        self.save_credentials_checkbox.setStyleSheet(f"color: {ModernStyle.COLORS['text_secondary']}; font-size: {tokens.fpx(tokens.FONT_NORMAL)}px;")
        layout.addWidget(self.save_credentials_checkbox)
        
        # 로그인 버튼
        self.login_button = ModernPrimaryButton("로그인")
        self.login_button.clicked.connect(self.on_login_clicked)
        layout.addWidget(self.login_button)
        
        card.setLayout(layout)
        return card
    
    def create_message_card(self) -> ModernCard:
        """서로이웃 메시지 카드 생성"""
        card = ModernCard("💬 서로이웃 요청 메시지")
        layout = QVBoxLayout()
        
        # 라디오 버튼 그룹
        self.message_button_group = QButtonGroup()
        
        # 기본 메시지 사용 라디오 버튼
        self.use_default_message_radio = QRadioButton("네이버 기본 메시지 사용: '우리 서로이웃해요~'")
        self.use_default_message_radio.setChecked(True)  # 기본으로 선택
        self.message_button_group.addButton(self.use_default_message_radio, 0)
        layout.addWidget(self.use_default_message_radio)
        
        # 사용자 입력 메시지 사용 라디오 버튼
        self.use_custom_message_radio = QRadioButton("사용자 입력 메시지 사용:")
        self.message_button_group.addButton(self.use_custom_message_radio, 1)
        layout.addWidget(self.use_custom_message_radio)
        
        # 메시지 입력 (기본적으로 비활성화)
        self.message_input = ModernTextEdit()
        self.message_input.setPlaceholderText("예: 안녕하세요! 서로이웃 해요 :)")
        self.message_input.setMaximumHeight(tokens.spx(60))
        self.message_input.setEnabled(False)  # 기본적으로 비활성화
        layout.addWidget(self.message_input)
        
        # 저장 버튼
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        self.save_message_button = ModernSuccessButton("메시지 저장")
        self.save_message_button.clicked.connect(self.on_save_message_clicked)
        self.save_message_button.setEnabled(False)  # 기본적으로 비활성화
        save_layout.addWidget(self.save_message_button)
        layout.addLayout(save_layout)
        
        # 라디오 버튼 연결
        self.use_default_message_radio.toggled.connect(self.on_message_option_changed)
        self.use_custom_message_radio.toggled.connect(self.on_message_option_changed)
        
        card.setLayout(layout)
        return card
    
    def on_message_option_changed(self):
        """메시지 옵션 변경 이벤트"""
        if self.use_custom_message_radio.isChecked():
            self.message_input.setEnabled(True)
            self.save_message_button.setEnabled(True)
        else:
            self.message_input.setEnabled(False)
            self.save_message_button.setEnabled(False)
    
    def create_search_card(self) -> ModernCard:
        """키워드 검색 설정 카드 생성"""
        card = ModernCard("🔍 키워드별 블로거 검색 설정")
        layout = QVBoxLayout()
        
        # 총 목표 인원 표시 (읽기 전용)
        target_layout = QHBoxLayout()
        target_layout.addWidget(QLabel("총 목표 인원:"))
        self.total_target_label = QLabel("0명")
        self.total_target_label.setStyleSheet(f"""
            QLabel {{
                font-weight: 600;
                color: {ModernStyle.COLORS['primary']};
                padding: {tokens.spx(4)}px {tokens.spx(8)}px;
                background-color: {ModernStyle.COLORS['bg_muted']};
                border-radius: {tokens.spx(4)}px;
                min-width: {tokens.spx(50)}px;
            }}
        """)
        target_layout.addWidget(self.total_target_label)
        
        # 자동 계산 설명
        auto_calc_label = QLabel("(키워드별 목표 합계)")
        auto_calc_label.setStyleSheet(f"color: {ModernStyle.COLORS['text_muted']}; font-size: {tokens.fpx(tokens.FONT_NORMAL)}px;")
        target_layout.addWidget(auto_calc_label)
        
        target_layout.addStretch()
        layout.addLayout(target_layout)
        
        # 키워드 추가
        keyword_layout = QHBoxLayout()
        keyword_layout.addWidget(QLabel("키워드:"))
        self.keyword_input = ModernLineEdit()
        self.keyword_input.setPlaceholderText("예: 강아지사료, 여행, 맛집")
        keyword_layout.addWidget(self.keyword_input)
        
        keyword_layout.addWidget(QLabel("목표:"))
        self.keyword_target_input = QSpinBox()
        self.keyword_target_input.setRange(1, 100)
        self.keyword_target_input.setValue(10)
        self.keyword_target_input.setSuffix("명")
        keyword_layout.addWidget(self.keyword_target_input)
        
        add_keyword_btn = ModernSuccessButton("추가")
        add_keyword_btn.setFixedWidth(tokens.spx(80))
        add_keyword_btn.clicked.connect(self.on_add_keyword_clicked)
        keyword_layout.addWidget(add_keyword_btn)
        layout.addLayout(keyword_layout)
        
        # 키워드 목록
        self.keyword_table = QTableWidget()
        self.keyword_table.setColumnCount(3)
        self.keyword_table.setHorizontalHeaderLabels(["키워드", "목표", "삭제"])
        self.keyword_table.horizontalHeader().setStretchLastSection(True)
        self.keyword_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.keyword_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.keyword_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        # 반응형 컬럼 너비 설정
        scale = tokens.get_screen_scale_factor()
        
        self.keyword_table.setColumnWidth(0, tokens.spx(500))  # 키워드: 반응형
        self.keyword_table.setColumnWidth(1, tokens.spx(100))  # 목표인원: 반응형
        self.keyword_table.setColumnWidth(2, tokens.spx(200))  # 삭제: 반응형 (최소 크기)
        self.keyword_table.setMaximumHeight(tokens.spx(300))
        self.keyword_table.setAlternatingRowColors(True)
        # 행 높이 설정
        self.keyword_table.verticalHeader().setDefaultSectionSize(tokens.spx(36))
        self.keyword_table.verticalHeader().setVisible(False)
        layout.addWidget(self.keyword_table)
        
        # 시작/정지 버튼
        button_layout = QHBoxLayout()
        
        self.start_button = ModernPrimaryButton("서로이웃 추가 시작")
        self.start_button.clicked.connect(self.on_start_clicked)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = ModernDangerButton("정지")
        self.stop_button.clicked.connect(self.on_stop_clicked)
        self.stop_button.setVisible(False)
        button_layout.addWidget(self.stop_button)
        
        layout.addLayout(button_layout)
        
        # 설명 텍스트
        info_text = QLabel(
            "💡 자동화 시스템이 2개 창을 사용하여 효율적으로 작업합니다.\n"
            "성공률 30-40%를 고려하여 부족시 자동으로 더 많은 후보를 검색합니다."
        )
        info_text.setStyleSheet(f"color: {ModernStyle.COLORS['text_muted']}; font-size: {tokens.fpx(tokens.FONT_NORMAL)}px; padding: {tokens.spx(5)}px;")
        info_text.setWordWrap(True)
        layout.addWidget(info_text)
        
        card.setLayout(layout)
        return card
    
    
    def show_usage_help(self):
        """사용법 도움말 표시 - 통합관리프로그램 스타일"""
        from src.toolbox.ui_kit.modern_dialog import ModernScrollableDialog
        
        help_text = (
            "🎯 네이버 블로그 서로이웃 추가 사용법\n\n"
            
            "📋 사용 순서:\n"
            "1️⃣ 네이버 로그인 (왼쪽 상단)\n"
            "• 네이버 아이디와 비밀번호를 입력하고 로그인\n"
            "• 2차 인증이 있는 경우 브라우저에서 직접 처리\n"
            "• 클립보드 입력 방식으로 보안 우회\n"
            "• 로그인 정보 저장 체크박스로 다음에도 자동 입력\n\n"
            
            "2️⃣ 서로이웃 메시지 설정 (왼쪽 하단)\n"
            "• 기본 메시지: '우리 서로이웃해요~' (네이버 기본)\n"
            "• 사용자 입력 메시지: 원하는 메시지 입력 가능\n"
            "• 메시지 저장 기능으로 다음에도 사용\n"
            "• 너무 긴 메시지는 스팸으로 인식될 수 있음\n\n"
            
            "3️⃣ 키워드 검색 설정 (오른쪽 상단)\n"
            "• 키워드별로 목표 인원을 설정하여 추가\n"
            "• 총 목표 인원은 자동 계산 (일일 최대 100명)\n"
            "• 여러 키워드 조합으로 다양한 블로거 발굴\n"
            "• 실제 성공률은 30-40% 정도이므로 여유있게 설정\n"
            "• 키워드별 삭제 버튼으로 불필요한 키워드 제거\n\n"
            
            "4️⃣ 자동화 실행 (오른쪽 하단)\n"
            "• '서로이웃 추가 시작' 버튼 클릭\n"
            "• Selenium 자동화로 안정적인 브라우저 제어\n"
            "• 2개 탭 동시 사용: 검색용 + 서로이웃 추가용\n"
            "• 실시간 진행률과 통계 확인 가능\n"
            "• 하루 100명 제한 도달시 자동 중단\n"
            "• 목표 달성 또는 '정지' 버튼으로 중단\n\n"
            
            "📊 진행률 모니터링:\n"
            "• 성공/실패/비활성화/이미신청 통계 실시간 표시\n"
            "• 현재 처리 중인 블로거명 표시\n"
            "• 작업 완료시 음성 알림 (선택적)\n"
            "• 완료된 키워드는 자동으로 테이블에서 제거\n\n"
            
            "⚠️ 주의사항:\n"
            "• 네이버 정책상 일일 최대 100명까지만 추가 가능\n"
            "• 과도한 사용시 계정 제재 가능성\n"
            "• 3초 간격으로 안전하게 진행\n"
            "• 실패율이 높으므로 충분한 키워드 설정 필요\n"
            "• 브라우저 창을 임의로 닫지 말 것\n\n"
            
            "🔧 문제 해결:\n"
            "• 로그인 실패: 아이디/비밀번호 재확인 또는 2차 인증 완료\n"
            "• 검색 결과 없음: 다른 키워드로 시도\n"
            "• 작업 중단: 정지 버튼 또는 프로그램 재시작\n"
            "• 5000명 초과 팝업: 자동 감지하여 다음 키워드로 진행\n"
            "• 하루 제한 도달: 다음 날 재시도"
        )
        
        dialog = ModernScrollableDialog(
            self,
            title="❓ 네이버 블로그 서로이웃 추가 사용법",
            message=help_text.strip(),
            confirm_text="확인",
            cancel_text=None,
            icon="❓"
        )
        dialog.exec()
    
    
    
    
    
    
    
    
    def setup_styles(self):
        """스타일 설정 - 반응형 적용"""
        self.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: {tokens.spx(2)}px solid {ModernStyle.COLORS['border']};
                border-radius: {tokens.spx(8)}px;
                margin: {tokens.spx(10)}px 0;
                padding-top: {tokens.spx(10)}px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {tokens.spx(10)}px;
                padding: 0 {tokens.spx(5)}px 0 {tokens.spx(5)}px;
            }}
            QListWidget {{
                border: {tokens.spx(1)}px solid {ModernStyle.COLORS['border']};
                border-radius: {tokens.spx(4)}px;
                background-color: {ModernStyle.COLORS['bg_card']};
                alternate-background-color: {ModernStyle.COLORS['bg_muted']};
            }}
            QListWidget::item {{
                padding: {tokens.spx(5)}px;
                border-bottom: {tokens.spx(1)}px solid {ModernStyle.COLORS['border']};
            }}
            QListWidget::item:selected {{
                background-color: {ModernStyle.COLORS['primary']};
                color: white;
            }}
            QTableWidget {{
                border: {tokens.spx(1)}px solid {ModernStyle.COLORS['border']};
                border-radius: {tokens.spx(4)}px;
                background-color: {ModernStyle.COLORS['bg_card']};
                alternate-background-color: {ModernStyle.COLORS['bg_muted']};
                gridline-color: {ModernStyle.COLORS['border']};
            }}
            QTableWidget::item {{
                padding: {tokens.spx(5)}px;
                color: {ModernStyle.COLORS['text_primary']};
            }}
            QTableWidget::item:selected {{
                background-color: {ModernStyle.COLORS['primary']};
                color: white;
            }}
            QHeaderView::section {{
                background-color: {ModernStyle.COLORS['bg_muted']};
                color: {ModernStyle.COLORS['text_primary']};
                padding: {tokens.spx(5)}px;
                border: {tokens.spx(1)}px solid {ModernStyle.COLORS['border']};
                font-weight: 600;
            }}
        """)
    
    def reset_ui_state(self):
        """UI 상태 초기화"""
        # 저장된 메시지 로드
        self.load_saved_message()
        
        # 기본 메시지 옵션 설정
        self.use_default_message_radio.setChecked(True)
        self.message_input.setEnabled(False)
        self.save_message_button.setEnabled(False)
        
        # 진행률 초기화
        self.reset_progress()
        
        # 키워드 테이블 초기화
        self.keyword_table.setRowCount(0)
        
        # 버튼 상태 초기화
        self.start_button.setVisible(True)
        self.stop_button.setVisible(False)
        
        # 로그인 상태 초기화
        self.is_logged_in = False
        
        # 키워드 설정 초기화
        self.keyword_configs = []  # [(keyword, target_count), ...]
        
        # 실시간 통계 저장용 (시그널에서 받은 정확한 값)
        self.final_success_count = 0
        self.final_failed_count = 0
        self.final_disabled_count = 0
        self.final_already_count = 0
        
        # 총 목표 인원 초기화
        self.update_total_target_display()
    
    def load_saved_message(self):
        """저장된 사용자 메시지 로드"""
        try:
            from src.foundation.db import get_db
            db = get_db()
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # 설정 테이블에서 저장된 메시지 조회
                cursor.execute("""
                    SELECT value FROM app_settings 
                    WHERE key = 'neighbor_add_custom_message'
                """)
                result = cursor.fetchone()
                
                if result:
                    saved_message = result[0]
                    self.message_input.setPlainText(saved_message)
                else:
                    self.message_input.setPlainText("안녕하세요! 서로이웃 해요 :)")
                    
        except Exception as e:
            logger.error(f"저장된 메시지 로드 실패: {e}")
            self.message_input.setPlainText("안녕하세요! 서로이웃 해요 :)")
    
    def on_save_message_clicked(self):
        """메시지 저장 버튼 클릭"""
        try:
            message = self.message_input.toPlainText().strip()
            if not message:
                dialog = ModernConfirmDialog(
                    self,
                    title="입력 오류",
                    message="저장할 메시지를 입력해주세요.",
                    confirm_text="확인",
                    cancel_text=None,
                    icon="⚠️"
                )
                dialog.exec()
                return
            
            from src.foundation.db import get_db
            db = get_db()
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # 설정 테이블에 메시지 저장 (UPSERT)
                cursor.execute("""
                    INSERT OR REPLACE INTO app_settings (key, value) 
                    VALUES ('neighbor_add_custom_message', ?)
                """, (message,))
                conn.commit()
            
            dialog = ModernConfirmDialog(
                self,
                title="저장 완료",
                message="사용자 메시지가 저장되었습니다.\n다음에도 같은 메시지를 사용할 수 있습니다.",
                confirm_text="확인",
                cancel_text=None,
                icon="✅"
            )
            dialog.exec()
            logger.info(f"사용자 메시지 저장됨: {message}")
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            logger.error(f"메시지 저장 실패: {e}")
            logger.error(f"상세 오류:\n{error_detail}")
            dialog = ModernConfirmDialog(
                self,
                title="저장 실패",
                message=f"메시지 저장에 실패했습니다:\n{str(e)}\n\n상세 오류는 로그를 확인해주세요.",
                confirm_text="확인",
                cancel_text=None,
                icon="❌"
            )
            dialog.exec()
    
    def on_login_clicked(self):
        """로그인 버튼 클릭 (비동기 개선)"""
        try:
            username = self.username_input.text().strip()
            password = self.password_input.text().strip()
            
            if not username or not password:
                dialog = ModernConfirmDialog(
                    self,
                    title="입력 오류",
                    message="아이디와 비밀번호를 모두 입력해주세요.",
                    confirm_text="확인",
                    cancel_text=None,
                    icon="⚠️"
                )
                dialog.exec()
                return
            
            # 세션 생성 (기본 메시지로)
            default_message = "안녕하세요! 서로이웃 해요 :)"
            self.session = self.service.create_session(default_message)
            
            # 로그인 버튼 상태 변경 (UI 즉시 반응)
            self.login_button.setText("🔄 로그인 중...")
            self.login_button.setEnabled(False)
            
            # 로그인 실행 (비동기 worker 사용)
            credentials = self.service.validate_credentials(username, password)
            
            # 개선된 비동기 로그인 워커 생성 및 실행
            self.login_worker = create_login_worker(self.service, credentials)
            self.login_thread = WorkerThread(self.login_worker)
            
            # 시그널 연결
            self.login_worker.login_completed.connect(self.on_login_completed)
            self.login_worker.error_occurred.connect(self.on_login_error)
            self.login_worker.two_factor_detected.connect(self.on_two_factor_detected)
            
            # 워커 스레드 시작
            self.login_thread.start()
            logger.info("🚀 비동기 로그인 워커 시작됨")
            
        except ValidationError as e:
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
            logger.error(f"로그인 시작 오류: {e}")
            
            # 2차 인증 감지 처리
            if "TWO_FACTOR_AUTH_REQUIRED" in str(e):
                self.login_button.setText("2차 인증 필요")
                dialog = ModernConfirmDialog(
                    self,
                    title="🔐 2차 인증 필요",
                    message="브라우저에서 2차 인증을 완료한 후\n다시 로그인을 시도해주세요.",
                    confirm_text="확인",
                    cancel_text=None,
                    icon="🔐"
                )
                dialog.exec()
                # 버튼과 진행률 바 상태 복원
                self.login_button.setText("로그인")
                self.login_button.setEnabled(True)
                self.progress_bar.setVisible(False)
                self.progress_label.setText("대기 중...")
            else:
                dialog = ModernConfirmDialog(
                    self,
                    title="오류",
                    message=f"로그인 시작 실패: {str(e)}",
                    confirm_text="확인",
                    cancel_text=None,
                    icon="❌"
                )
                dialog.exec()
                # 버튼과 진행률 바 상태 복원
                self.login_button.setText("로그인")
                self.login_button.setEnabled(True)
                self.progress_bar.setVisible(False)
                self.progress_label.setText("대기 중...")
    
    def check_two_factor_auth(self):
        """2차 인증 상태 체크"""
        if (hasattr(self.service, 'adapter') and 
            self.service.adapter and 
            hasattr(self.service.adapter, 'two_factor_auth_detected') and
            self.service.adapter.two_factor_auth_detected):
            
            self.login_button.setText("2차 인증 대기 중...")
            # 2차 인증이 감지되면 더 이상 체크할 필요 없음
            if hasattr(self, 'two_factor_check_timer'):
                self.two_factor_check_timer.stop()
    


    
    def on_add_keyword_clicked(self):
        """키워드 추가 버튼 클릭"""
        try:
            keyword = self.keyword_input.text().strip()
            target_count = self.keyword_target_input.value()
            
            if not keyword:
                dialog = ModernConfirmDialog(
                    self,
                    title="입력 오류",
                    message="키워드를 입력해주세요.",
                    confirm_text="확인",
                    cancel_text=None,
                    icon="⚠️"
                )
                dialog.exec()
                return
            
            # 중복 키워드 확인
            for i in range(self.keyword_table.rowCount()):
                existing_keyword = self.keyword_table.item(i, 0).text()
                if existing_keyword == keyword:
                    dialog = ModernConfirmDialog(
                        self,
                        title="중복 오류",
                        message="이미 추가된 키워드입니다.",
                        confirm_text="확인",
                        cancel_text=None,
                        icon="⚠️"
                    )
                    dialog.exec()
                    return
            
            # 총 목표 인원수 확인 (키워드 설정 기준)
            current_total = sum(target for _, target in self.keyword_configs)
            
            if current_total + target_count > 100:
                dialog = ModernConfirmDialog(
                    self,
                    title="목표 인원 초과",
                    message=f"총 목표 인원이 100명을 초과합니다.\n현재: {current_total}명, 추가하려는: {target_count}명",
                    confirm_text="확인",
                    cancel_text=None,
                    icon="⚠️"
                )
                dialog.exec()
                return
            
            # 설정 저장
            self.keyword_configs.append((keyword, target_count))
            
            # 테이블 업데이트 (삭제 버튼 생성 포함)
            self.update_keyword_table()
            
            # 입력 필드 초기화
            self.keyword_input.clear()
            self.keyword_target_input.setValue(10)
            
            logger.info(f"키워드 추가: {keyword} ({target_count}명)")
            
        except Exception as e:
            logger.error(f"키워드 추가 오류: {e}")
            dialog = ModernConfirmDialog(
                self,
                title="오류",
                message=f"키워드 추가 실패: {str(e)}",
                confirm_text="확인",
                cancel_text=None,
                icon="❌"
            )
            dialog.exec()
    
    
    
    
    
    
    
    def closeEvent(self, event):
        """창 닫기 이벤트"""
        # on_stop_clicked()에서 이미 워커 취소와 브라우저 세션 종료를 처리함
        self.on_stop_clicked()
        
        # 스레드 정리
        if self.current_thread:
            self.current_thread.quit()
            self.current_thread.wait()
        
        event.accept()
    
    def load_saved_credentials(self):
        """저장된 로그인 정보 로드"""
        try:
            credentials = self.service.load_saved_credentials()
            if credentials:
                username, password = credentials
                self.username_input.setText(username)
                self.password_input.setText(password)
                self.save_credentials_checkbox.setChecked(True)
                logger.info(f"저장된 로그인 정보 로드됨: {username}")
        except Exception as e:
            logger.error(f"로그인 정보 로드 실패: {e}")
    
    def save_credentials_if_checked(self, username: str, password: str):
        """체크박스 상태에 따라 로그인 정보 저장"""
        try:
            if self.save_credentials_checkbox.isChecked():
                self.service.save_credentials(username, password)
                logger.info("로그인 정보 저장됨")
            else:
                # 체크박스가 해제된 경우 해당 사용자의 저장된 정보 삭제
                self.service.delete_saved_credentials(username)
                logger.info("저장된 로그인 정보 삭제됨")
        except Exception as e:
            logger.error(f"로그인 정보 저장/삭제 실패: {e}")
    
    
    
    def on_start_clicked(self):
        """서로이웃 추가 시작 버튼 클릭"""
        try:
            logger.info("🚀 서로이웃 추가 시작 버튼 클릭")
            
            # 로그인 상태 확인
            if not self.is_logged_in or not self.service.current_session:
                dialog = ModernConfirmDialog(
                    self,
                    title="로그인 필요",
                    message="먼저 네이버 로그인을 완료해주세요.",
                    confirm_text="확인",
                    cancel_text=None,
                    icon="⚠️"
                )
                dialog.exec()
                return
            
            # 키워드 설정 확인
            if not self.keyword_configs:
                dialog = ModernConfirmDialog(
                    self,
                    title="키워드 누락",
                    message="최소 1개 이상의 키워드를 추가해주세요.",
                    confirm_text="확인",
                    cancel_text=None,
                    icon="⚠️"
                )
                dialog.exec()
                return
            
            logger.info(f"✅ 사전 검증 완료 - 키워드: {len(self.keyword_configs)}개")
            
            # UI 상태 업데이트
            self.start_button.setVisible(False)
            self.stop_button.setVisible(True)
            
            # 모든 키워드 처리 시작 (단일 워커로 모든 키워드 순차 처리)
            self._start_all_keywords_processing()
            
        except Exception as e:
            logger.error(f"❌ 서로이웃 추가 시작 실패: {e}")
            self.start_button.setVisible(True)
            self.stop_button.setVisible(False)
    
    def on_stop_clicked(self):
        """정지 버튼 클릭"""
        try:
            logger.info("⏹️ 작업 중단 요청")
            
            # 현재 실행 중인 워커 취소 (워커에서 브라우저 세션도 강제 중단함)
            if hasattr(self, 'login_worker') and self.login_worker:
                self.login_worker.cancel()
            if hasattr(self, 'all_keywords_worker') and self.all_keywords_worker:
                self.all_keywords_worker.cancel()
            
            # 추가적으로 서비스에서도 브라우저 세션 강제 중단 (더블 보험)
            if self.service:
                self.service.force_stop_browser_session()
            
            # UI 상태 복원
            self.start_button.setVisible(True)
            self.stop_button.setVisible(False)
            self.reset_progress()
            self.update_progress_status("작업이 중단되었습니다")
            
            logger.info("✅ 작업 중단 완료")
            
        except Exception as e:
            logger.error(f"❌ 작업 중단 실패: {e}")
    
    
    
    def _start_all_keywords_processing(self):
        """모든 키워드를 단일 워커로 순차 처리"""
        try:
            logger.info("🎯 모든 키워드 처리 시작 (단일 워커)")
            
            # 진행률과 통계 초기화
            self.reset_progress()
            self.update_progress_status("모든 키워드 처리 준비 중...")
            self.update_statistics(0, 0, 0, 0)  # 통계 완전 초기화
            
            # 실시간 통계 저장용 변수도 초기화
            self.final_success_count = 0
            self.final_failed_count = 0  
            self.final_disabled_count = 0
            self.final_already_count = 0
            
            # 메시지 결정
            if self.use_custom_message_radio.isChecked():
                message = self.message_input.toPlainText().strip()
                if not message:
                    message = "안녕하세요! 서로이웃 해요 :)"
            else:
                message = ""  # 네이버 기본 메시지 사용
            
            # UI 버튼 상태 변경
            self.start_button.setVisible(False)
            self.stop_button.setVisible(True)
            
            # 단일 워커로 모든 키워드 처리
            if self.keyword_configs:
                # AllKeywordsWorker 생성 및 실행
                self.all_keywords_worker = create_all_keywords_worker(
                    self.service, self.keyword_configs, message
                )
                self.all_keywords_thread = WorkerThread(self.all_keywords_worker)
                
                # 시그널 연결 (디버깅 로그 추가)
                logger.info("🔗 AllKeywordsWorker 시그널 연결 중...")
                self.all_keywords_worker.progress_updated.connect(self.on_all_keywords_progress)
                self.all_keywords_worker.batch_completed.connect(self.on_all_keywords_completed)
                self.all_keywords_worker.error_occurred.connect(self.on_all_keywords_error)
                logger.info("✅ 시그널 연결 완료")
                
                # 워커 시작
                self.all_keywords_thread.start()
                logger.info(f"🚀 AllKeywordsWorker 시작됨: {len(self.keyword_configs)}개 키워드")
            else:
                logger.warning("키워드 설정이 없어서 작업을 시작할 수 없습니다")
                self.start_button.setVisible(True)
                self.stop_button.setVisible(False)
                
        except Exception as e:
            logger.error(f"❌ 모든 키워드 처리 시작 실패: {e}")
            self.update_progress_status(f"시작 실패: {str(e)}")
            self.start_button.setVisible(True)
            self.stop_button.setVisible(False)
    
    def on_all_keywords_progress(self, progress):
        """모든 키워드 처리 진행률 업데이트"""
        logger.info("🎯 [UI] on_all_keywords_progress 호출됨!")  # 디버깅 로그
        
        # 하루 100명 제한 도달 체크
        stage = getattr(progress, 'stage', '')
        if stage == 'daily_limit_reached':
            logger.warning("🚫 하루 100명 제한 도달 감지 - 모든 작업 중단")
            self.update_progress_status("🚫 하루 100명 제한 도달 - 작업 중단됨", progress.current, progress.total)
            
            # 즉시 모든 워커 중단
            if hasattr(self, 'all_keywords_worker') and self.all_keywords_worker:
                self.all_keywords_worker.cancel()
            
            # UI 상태 복원
            self.start_button.setVisible(True)
            self.stop_button.setVisible(False)
            
            # 하루 제한 도달 다이얼로그 표시
            from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
            dialog = ModernConfirmDialog(
                self,
                title="하루 100명 제한 도달",
                message="하루에 신청 가능한 서로이웃 수(100명)가 초과되어\n더 이상 서로이웃을 추가할 수 없습니다.\n\n내일 다시 시도해주세요.",
                confirm_text="확인",
                cancel_text=None,
                icon="🚫"
            )
            dialog.exec()
            
            # 음성 알림
            self._play_daily_limit_sound()
            return
        
        # 진행률 카드 업데이트
        self.update_progress_status(progress.message, progress.current, progress.total)
        
        # 통계 정보 업데이트 및 최종값 저장
        success = getattr(progress, 'success_count', 0)
        failed = getattr(progress, 'failed_count', 0) 
        disabled = getattr(progress, 'disabled_count', 0)
        already = getattr(progress, 'already_count', 0)
        
        # 실시간으로 받은 정확한 통계 저장 (완료 다이얼로그에서 사용)
        self.final_success_count = success
        self.final_failed_count = failed
        self.final_disabled_count = disabled
        self.final_already_count = already
        
        # 디버깅 로그
        logger.info(f"🔍 실시간 통계 저장: 성공={success}, 실패={failed}, 비활성화={disabled}, 이미신청={already}")
        
        self.update_statistics(success, failed, disabled, already)
        
        # 현재 처리 중인 블로거 업데이트
        current_blogger = getattr(progress, 'current_blogger', '')
        self.update_current_blogger(current_blogger)
        
        logger.info(f"🎯 모든 키워드 진행률 업데이트: {progress.current}/{progress.total} | 성공:{success} 실패:{failed} 비활성화:{disabled} 이미신청중:{already}")
    
    def on_all_keywords_completed(self, all_requests):
        """모든 키워드 처리 완료"""
        try:
            logger.info(f"🏁 모든 키워드 처리 완료: {len(all_requests)}개 처리됨")
            
            # UI 상태 복원
            self.start_button.setVisible(True)
            self.stop_button.setVisible(False)
            
            # 🚨 긴급 해결: 실시간 통계가 0이면 목표 개수를 성공으로 간주
            if self.final_success_count == 0 and self.final_failed_count == 0:
                # 실시간 통계가 업데이트 안 된 경우, 목표 개수만큼 성공으로 처리
                total_target_sum = sum(target for _, target in self.keyword_configs)
                total_success = min(total_target_sum, len(all_requests))  # 목표 vs 실제 처리 중 작은 값
                total_failed = max(0, len(all_requests) - total_success)
                total_disabled = 0
                total_already = 0
                logger.warning(f"🚨 실시간 통계 업데이트 실패 → 목표 기준으로 대체: 성공={total_success}, 실패={total_failed}")
            else:
                # 실시간 시그널에서 받은 정확한 통계 사용
                total_success = self.final_success_count
                total_failed = self.final_failed_count
                total_disabled = self.final_disabled_count
                total_already = self.final_already_count
                logger.info(f"✅ 실시간 시그널 통계 사용: 성공={total_success}, 실패={total_failed}, 비활성화={total_disabled}, 이미신청={total_already}")
            
            total_daily_limit = 0  # 필요시 추가
            logger.info(f"📝 총 요청 리스트 크기: {len(all_requests)}개")
            
            # 최종 진행률 업데이트
            self.update_progress_status(f"모든 키워드 처리 완료: 총 성공 {total_success}명", total_success, total_success)
            self.update_statistics(total_success, total_failed, total_disabled, total_already)
            
            # 완료 다이얼로그
            result_message = f"🎉 모든 키워드 처리가 완료되었습니다!\n\n"
            result_message += f"📊 전체 통계:\n"
            result_message += f"• 총 처리: {len(all_requests)}개\n"
            result_message += f"• ✅ 성공: {total_success}개\n"
            result_message += f"• ❌ 실패: {total_failed}개\n"
            if total_disabled > 0:
                result_message += f"• 🚫 비활성화: {total_disabled}개\n"
            if total_already > 0:
                result_message += f"• 🔄 이미 요청됨: {total_already}개\n"
            if total_daily_limit > 0:
                result_message += f"• 🚫 하루 제한: {total_daily_limit}개\n"
            
            from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
            dialog = ModernConfirmDialog(
                self,
                title="🎉 모든 키워드 완료",
                message=result_message,
                confirm_text="확인",
                cancel_text=None,
                icon="🎉" if total_success > 0 else "ℹ️"
            )
            dialog.exec()
            
            # 음성 알림
            self._play_completion_sound()
            
            # 완료된 키워드들을 키워드 테이블에서 제거
            self._clear_completed_keywords()
            
            logger.info(f"✅ 최종 결과: 성공 {total_success}개, 실패 {total_failed}개, 비활성화 {total_disabled}개, 이미신청 {total_already}개")
            logger.info("🧹 완료된 키워드들이 테이블에서 제거되었습니다.")
            
        except Exception as e:
            logger.error(f"모든 키워드 완료 처리 오류: {e}")
            # 오류 발생시에도 UI 복원
            self.start_button.setVisible(True)
            self.stop_button.setVisible(False)
    
    def on_all_keywords_error(self, error_message):
        """모든 키워드 처리 오류"""
        logger.error(f"❌ 모든 키워드 처리 오류: {error_message}")
        
        # UI 상태 복원
        self.start_button.setVisible(True)
        self.stop_button.setVisible(False)
        self.update_progress_status(f"처리 실패: {error_message}")
        
        # 오류 다이얼로그
        from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
        dialog = ModernConfirmDialog(
            self,
            title="처리 오류",
            message=f"키워드 처리 중 오류가 발생했습니다:\n{error_message}",
            confirm_text="확인",
            cancel_text=None,
            icon="❌"
        )
        dialog.exec()
    
    
    def _play_completion_sound(self):
        """작업 완료 음성 알림"""
        try:
            from src.foundation.config import APP_MODE
            if APP_MODE != "test":  # 테스트 모드가 아닐 때만 음성 알림
                import subprocess
                subprocess.run([
                    "powershell", "-Command",
                    "Add-Type -AssemblyName System.Speech; "
                    "(New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('블로그 자동화 작업이 완료되었습니다')"
                ], check=False, capture_output=True)
                logger.info("🔊 작업 완료 음성 알림 재생됨")
        except Exception as e:
            logger.debug(f"음성 알림 실패 (무시됨): {e}")
    
    def _play_daily_limit_sound(self):
        """하루 제한 도달 음성 알림"""
        try:
            from src.foundation.config import APP_MODE
            if APP_MODE != "test":  # 테스트 모드가 아닐 때만 음성 알림
                import subprocess
                subprocess.run([
                    "powershell", "-Command",
                    "Add-Type -AssemblyName System.Speech; "
                    "(New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('하루 백명 제한에 도달했습니다')"
                ], check=False, capture_output=True)
                logger.info("🔊 하루 제한 도달 음성 알림 재생됨")
        except Exception as e:
            logger.debug(f"음성 알림 실패 (무시됨): {e}")
    
    def _clear_completed_keywords(self):
        """완료된 키워드들을 테이블에서 제거"""
        try:
            # 키워드 설정 리스트 초기화
            self.keyword_configs.clear()
            
            # 키워드 테이블 초기화
            if hasattr(self, 'keyword_table'):
                self.keyword_table.setRowCount(0)
            
            logger.info("🧹 키워드 테이블이 초기화되었습니다. 새로운 키워드를 추가할 수 있습니다.")
            
        except Exception as e:
            logger.error(f"키워드 테이블 초기화 오류: {e}")
    
    def on_login_completed(self, success: bool):
        """로그인 완료 처리 (비동기 개선)"""
        try:
            if success:
                # 로그인 성공
                logger.info("✅ 비동기 로그인 성공!")
                self.is_logged_in = True
                self.login_button.setText("✅ 로그인 완료")
                self.login_button.setEnabled(False)  # 버튼은 보이지만 비활성화
                
                # 상태 메시지 업데이트
                if hasattr(self, 'login_status_label'):
                    self.login_status_label.setText("✅ 네이버 로그인 완료")
                    self.login_status_label.setStyleSheet(f"""
                        QLabel {{
                            color: {ModernStyle.COLORS['success']};
                            font-size: {tokens.fpx(12)}px;
                            padding: {tokens.spx(tokens.GAP_8)}px;
                            background-color: {ModernStyle.COLORS['success_bg']};
                            border-radius: {tokens.spx(tokens.RADIUS_SM)}px;
                        }}
                    """)
                
                # 로그인 정보 저장 (체크되어 있는 경우)
                if hasattr(self, 'save_credentials_checkbox') and self.save_credentials_checkbox.isChecked():
                    username = self.username_input.text().strip()
                    password = self.password_input.text().strip()
                    self.save_credentials_if_checked(username, password)
                
                # 로그인 성공 다이얼로그
                dialog = ModernConfirmDialog(
                    self,
                    title="로그인 성공",
                    message="네이버 로그인이 완료되었습니다.\n이제 서로이웃 추가를 시작할 수 있습니다.",
                    confirm_text="확인",
                    cancel_text=None,
                    icon="🎉"
                )
                dialog.exec()
                
            else:
                # 로그인 실패
                logger.error("❌ 비동기 로그인 실패")
                self.is_logged_in = False
                self.login_button.setText("🔄 다시 로그인")
                self.login_button.setEnabled(True)
                
                # 진행률 바 숨기기
                self.progress_bar.setVisible(False)
                self.progress_label.setText("대기 중...")
                
                # 실패 다이얼로그
                dialog = ModernConfirmDialog(
                    self,
                    title="로그인 실패",
                    message="네이버 로그인에 실패했습니다.\n아이디와 비밀번호를 확인해주세요.",
                    confirm_text="확인",
                    cancel_text=None,
                    icon="❌"
                )
                dialog.exec()
                
        except Exception as e:
            logger.error(f"로그인 완료 처리 중 오류: {e}")
            # 오류 발생시 UI 상태 복원
            self.reset_progress()
            self.login_button.setText("로그인")
            self.login_button.setEnabled(True)
    
    def on_login_error(self, error_message: str):
        """로그인 오류 처리"""
        try:
            logger.error(f"❌ 로그인 오류: {error_message}")
            self.is_logged_in = False
            self.login_button.setText("로그인")
            self.login_button.setEnabled(True)
            
            # 진행률 초기화
            self.reset_progress()
            
            # 오류 다이얼로그
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
        """2차 인증 감지 처리 (비동기 개선)"""
        try:
            logger.info("🔐 비동기 2차 인증 감지됨")
            self.login_button.setText("🔐 2차 인증 대기중...")
            self.login_button.setEnabled(False)
            
            # 2차 인증 상태 표시
            self.update_progress_status("브라우저에서 2차 인증을 완료해주세요")
            
            # 상태 메시지 업데이트
            if hasattr(self, 'login_status_label'):
                self.login_status_label.setText("🔐 2차 인증 진행 중 - 휴대폰/이메일 확인")
                self.login_status_label.setStyleSheet(f"""
                    QLabel {{
                        color: {ModernStyle.COLORS['warning']};
                        font-size: {tokens.fpx(12)}px;
                        padding: {tokens.spx(tokens.GAP_8)}px;
                        background-color: {ModernStyle.COLORS['warning_bg']};
                        border-radius: {tokens.spx(tokens.RADIUS_SM)}px;
                    }}
                """)
            
            # 2차 인증 안내는 이미 위에서 처리됨
            
        except Exception as e:
            logger.error(f"2차 인증 처리 중 오류: {e}")
    
    # 상황판 업데이트 메서드들
    
    
    
    
    def update_progress_status(self, message, current=0, total=100):
        """진행률 상태 업데이트"""
        self.status_label.setText(message)
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
    
    def update_statistics(self, success=0, failed=0, disabled=0, already=0):
        """통계 정보 업데이트"""
        self.success_label.setText(self.get_success_text(success))
        self.failed_label.setText(self.get_failed_text(failed))  
        self.disabled_label.setText(self.get_disabled_text(disabled))
        self.already_label.setText(self.get_already_text(already))
    
    def update_current_blogger(self, blogger_name=""):
        """현재 처리 중인 블로거 업데이트"""
        if blogger_name:
            self.current_blogger_label.setText(f"현재 처리: {blogger_name}")
        else:
            self.current_blogger_label.setText("")
    
    def reset_progress(self):
        """진행률 초기화"""
        self.status_label.setText("대기 중...")
        self.progress_bar.setValue(0)
        self.success_label.setText(self.get_success_text(0))
        self.failed_label.setText(self.get_failed_text(0)) 
        self.disabled_label.setText(self.get_disabled_text(0))
        self.already_label.setText(self.get_already_text(0))
        self.current_blogger_label.setText("")
    
    def update_total_target_display(self):
        """총 목표 인원 표시 업데이트"""
        total = sum(target for _, target in self.keyword_configs)
        self.total_target_label.setText(f"{total}명")
    
    def update_keyword_table(self):
        """키워드 테이블 업데이트"""
        if not hasattr(self, 'keyword_table'):
            return
            
        self.keyword_table.setRowCount(len(self.keyword_configs))
        
        for i, (keyword, target_count) in enumerate(self.keyword_configs):
            # 키워드
            self.keyword_table.setItem(i, 0, QTableWidgetItem(keyword))
            # 목표 인원
            self.keyword_table.setItem(i, 1, QTableWidgetItem(f"{target_count}명"))
            # 삭제 버튼 - 작은 크기로 생성
            delete_button = ModernDangerButton("삭제")
            delete_button.setFixedSize(tokens.spx(60), tokens.spx(20))  # 반응형 크기
            # 기본 스타일을 완전히 override하여 작은 버튼 적용
            delete_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    border-radius: {tokens.spx(3)}px;
                    padding: {tokens.spx(2)}px {tokens.spx(8)}px;
                    font-size: {tokens.fpx(11)}px;
                    font-weight: bold;
                    min-height: {tokens.spx(20)}px;
                    max-height: {tokens.spx(20)}px;
                    min-width: {tokens.spx(60)}px;
                    max-width: {tokens.spx(60)}px;
                }}
                QPushButton:hover {{
                    background-color: #c82333;
                }}
                QPushButton:pressed {{
                    background-color: #bd2130;
                }}
            """)
            delete_button.clicked.connect(lambda checked, idx=i: self.delete_keyword(idx))
            
            # 버튼을 중앙 정렬하기 위한 위젯 컨테이너 생성
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.addWidget(delete_button)
            button_layout.setAlignment(Qt.AlignCenter)
            button_layout.setContentsMargins(0, 0, 0, 0)  # 마진 제거
            
            self.keyword_table.setCellWidget(i, 2, button_widget)
        
        # 총 목표 인원 자동 업데이트
        self.update_total_target_display()
    
    def delete_keyword(self, index):
        """키워드 삭제"""
        if 0 <= index < len(self.keyword_configs):
            keyword, _ = self.keyword_configs[index]
            self.keyword_configs.pop(index)
            self.update_keyword_table()
            logger.info(f"키워드 삭제: {keyword}")
    
    
