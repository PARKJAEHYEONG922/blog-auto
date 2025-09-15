"""
블로그 자동화 Step 1: AI 설정 + 키워드 입력 + 제목 추천
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QFrame
)
from PySide6.QtCore import Qt, Signal
import traceback

from src.foundation.logging import get_logger
from src.toolbox.ui_kit.components import (
    ModernButton, ModernLineEdit, ModernCard,
    ModernPrimaryButton, ModernSuccessButton
)
from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
from src.toolbox.ui_kit.modern_style import ModernStyle
from src.toolbox.ui_kit import tokens
from src.foundation.exceptions import BusinessError, ValidationError

logger = get_logger("blog_automation.ui_table1")


class TableUIDialogHelper:
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


class BlogAutomationStep1UI(QWidget):
    """Step 1: AI 설정 + 키워드 입력 + 제목 추천"""

    # 시그널 정의
    step_completed = Signal(dict)  # 다음 단계로 데이터 전달

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.titles_with_search = []  # 제목과 검색어 데이터 저장
        self.setup_ui()
        self.load_ai_settings()

    def setup_ui(self):
        """UI 구성"""
        main_layout = QVBoxLayout()
        margin = tokens.GAP_16
        spacing = tokens.GAP_12
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)

        # Step 헤더
        step_header = self.create_step_header()
        main_layout.addWidget(step_header)

        # 통합 설정 카드 (AI 설정 + 키워드 + 제목 추천)
        unified_card = self.create_unified_settings_card()
        main_layout.addWidget(unified_card)

        # 진행 버튼
        next_button_layout = QHBoxLayout()
        next_button_layout.addStretch()
        self.next_step_btn = ModernSuccessButton("➡️ 2단계: 블로그 분석으로 진행")
        self.next_step_btn.clicked.connect(self.on_next_step_clicked)
        self.next_step_btn.setEnabled(False)  # 제목 선택 후 활성화
        next_button_layout.addWidget(self.next_step_btn)
        main_layout.addLayout(next_button_layout)

        self.setLayout(main_layout)

    def create_unified_settings_card(self) -> ModernCard:
        """통합 설정 카드 생성 (AI 설정 + 키워드 + 제목 추천)"""
        card = ModernCard("🚀 블로그 자동화 설정")
        layout = QVBoxLayout()
        layout.setSpacing(tokens.GAP_16)


        # ========== 섹션 1: AI 글쓰기 설정 ==========
        ai_section_label = self.create_section_label("🤖 1단계: AI 글쓰기 설정")
        layout.addWidget(ai_section_label)

        # AI 설정 내용 (기존 AI 설정 카드의 내용)
        ai_content = self.create_ai_settings_content()
        layout.addLayout(ai_content)

        # 구분선 추가
        divider2 = self.create_section_divider()
        layout.addWidget(divider2)

        # ========== 섹션 2: 키워드 & 제목 추천 ==========
        keyword_section_label = self.create_section_label("🔍 2단계: 키워드 & 제목 추천")
        layout.addWidget(keyword_section_label)

        # 키워드 & 제목 추천 내용 (기존 키워드 카드의 내용)
        keyword_content = self.create_keyword_content()
        layout.addLayout(keyword_content)

        card.setLayout(layout)
        return card

    def create_section_label(self, text: str) -> QLabel:
        """섹션 라벨 생성"""
        label = QLabel(text)
        label.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_primary']};
                font-size: {tokens.get_font_size('medium')}px;
                font-weight: 600;
                padding: {tokens.spx(8)}px 0px;
                margin-bottom: {tokens.GAP_4}px;
                border-left: {tokens.spx(3)}px solid {ModernStyle.COLORS['primary']};
                padding-left: {tokens.spx(12)}px;
                background-color: {ModernStyle.COLORS['bg_muted']};
                border-radius: {tokens.RADIUS_SM}px;
            }}
        """)
        return label

    def create_section_divider(self) -> QFrame:
        """섹션 구분선 생성"""
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet(f"""
            QFrame {{
                color: {ModernStyle.COLORS['border']};
                margin: {tokens.GAP_8}px 0px;
            }}
        """)
        return line

    def create_ai_settings_content(self) -> QVBoxLayout:
        """AI 설정 컨텐츠 생성"""
        layout = QVBoxLayout()
        layout.setSpacing(tokens.GAP_8)

        # 간단한 설명
        simple_desc = QLabel("원하는 글쓰기 스타일을 선택하고 설정을 저장하세요")
        simple_desc.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_secondary']};
                font-size: {tokens.get_font_size('normal')}px;
                font-weight: 500;
                padding: {tokens.spx(4)}px 0px;
                margin-bottom: {tokens.GAP_4}px;
            }}
        """)
        layout.addWidget(simple_desc)

        # 컨텐츠 유형 선택
        content_type_layout = QHBoxLayout()
        content_type_label = QLabel("📝 컨텐츠 유형:")
        content_type_label.setStyleSheet(f"font-size: {tokens.get_font_size('normal')}px;")
        content_type_layout.addWidget(content_type_label)

        self.content_type_combo = QComboBox()
        self.content_type_combo.addItems([
            "후기/리뷰형 - 개인 경험과 솔직한 후기 중심",
            "정보/가이드형 - 객관적 정보와 가이드 중심",
            "비교/추천형 - 여러 옵션 비교분석 중심"
        ])
        self.content_type_combo.setCurrentIndex(1)  # 정보/가이드형을 기본값으로

        # 콤보박스 스타일 설정
        combo_style = f"""
            QComboBox {{
                padding: {tokens.GAP_8}px {tokens.GAP_12}px;
                border: {tokens.spx(1)}px solid {ModernStyle.COLORS['border']};
                border-radius: {tokens.RADIUS_SM}px;
                background-color: {ModernStyle.COLORS['bg_card']};
                color: {ModernStyle.COLORS['text_primary']};
                font-size: {tokens.get_font_size('normal')}px;
                min-height: {tokens.spx(20)}px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: {tokens.spx(20)}px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: {tokens.spx(5)}px solid transparent;
                border-right: {tokens.spx(5)}px solid transparent;
                border-top: {tokens.spx(5)}px solid {ModernStyle.COLORS['text_secondary']};
                margin-right: {tokens.spx(5)}px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {ModernStyle.COLORS['bg_card']};
                border: {tokens.spx(1)}px solid {ModernStyle.COLORS['border']};
                selection-background-color: {ModernStyle.COLORS['primary']};
                selection-color: white;
                font-size: {tokens.get_font_size('normal')}px;
            }}
        """
        self.content_type_combo.setStyleSheet(combo_style)
        content_type_layout.addWidget(self.content_type_combo)

        # 후기 세부 유형 드롭박스 (오른쪽에 배치, 초기에는 숨김)
        self.review_detail_combo = QComboBox()
        self.review_detail_combo.addItems([
            "내돈내산 후기",
            "협찬 후기",
            "체험단 후기",
            "대여/렌탈 후기"
        ])
        self.review_detail_combo.setStyleSheet(combo_style)
        self.review_detail_combo.setVisible(False)  # 초기에는 숨김
        content_type_layout.addWidget(self.review_detail_combo)

        layout.addLayout(content_type_layout)

        # 말투 선택
        tone_layout = QHBoxLayout()
        tone_label = QLabel("🗣️ 말투 스타일:")
        tone_label.setStyleSheet(f"font-size: {tokens.get_font_size('normal')}px;")
        tone_layout.addWidget(tone_label)

        self.tone_combo = QComboBox()
        self.tone_combo.addItems([
            "친근한 반말체 - '써봤는데 진짜 좋더라~', '완전 강추!'",
            "정중한 존댓말체 - '사용해보았습니다', '추천드립니다'",
            "친근한 존댓말체 - '써봤는데 좋더라구요~', '도움이 될 것 같아요'"
        ])
        self.tone_combo.setCurrentIndex(1)  # 정중한 존댓말체를 기본값으로
        self.tone_combo.setStyleSheet(combo_style)
        tone_layout.addWidget(self.tone_combo)
        layout.addLayout(tone_layout)

        # 블로거 정체성
        identity_layout = QHBoxLayout()
        identity_label = QLabel("👤 블로거 정체성:")
        identity_label.setStyleSheet(f"font-size: {tokens.get_font_size('normal')}px;")
        identity_layout.addWidget(identity_label)

        self.blogger_identity_edit = ModernLineEdit()
        self.blogger_identity_edit.setPlaceholderText("블로거 정체성 입력 (예: IT 전문가, 육아맘, 여행블로거)")
        self.blogger_identity_edit.setMinimumHeight(tokens.spx(40))
        identity_layout.addWidget(self.blogger_identity_edit, 1)
        layout.addLayout(identity_layout)

        # 설정 저장 버튼
        save_button_layout = QHBoxLayout()
        save_button_layout.addStretch()
        self.save_settings_button = ModernSuccessButton("💾 설정 저장")
        self.save_settings_button.clicked.connect(self.save_ai_settings)
        save_button_layout.addWidget(self.save_settings_button)
        layout.addLayout(save_button_layout)

        # 컨텐츠 유형 변경 시 후기 세부 옵션 토글
        self.content_type_combo.currentIndexChanged.connect(self.on_content_type_changed)
        self.on_content_type_changed(1)  # 초기 상태 설정 (정보/가이드형)

        return layout

    def create_keyword_content(self) -> QVBoxLayout:
        """키워드 & 제목 추천 컨텐츠 생성"""
        layout = QVBoxLayout()
        layout.setSpacing(tokens.GAP_10)

        # 간단한 설명
        simple_desc = QLabel("메인키워드 입력 → 제목 추천받기 → 선택\n   • 보조키워드는 선택사항이며, 여러 개 입력 가능합니다")
        simple_desc.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_secondary']};
                font-size: {tokens.get_font_size('normal')}px;
                font-weight: 500;
                padding: {tokens.spx(4)}px 0px;
                margin-bottom: {tokens.GAP_8}px;
                line-height: 1.4;
            }}
        """)
        layout.addWidget(simple_desc)

        # 메인키워드 입력
        main_keyword_layout = QHBoxLayout()
        main_keyword_label = QLabel("메인키워드:")
        main_keyword_label.setMinimumWidth(80)
        main_keyword_label.setStyleSheet(f"font-size: {tokens.get_font_size('normal')}px;")
        main_keyword_layout.addWidget(main_keyword_label)

        self.main_keyword_input = ModernLineEdit()
        self.main_keyword_input.setPlaceholderText("메인키워드 필수 (예: 프로그래밍 학습법)")
        self.main_keyword_input.setMinimumHeight(tokens.spx(40))
        main_keyword_layout.addWidget(self.main_keyword_input, 1)

        layout.addLayout(main_keyword_layout)

        # 보조키워드 입력
        sub_keyword_layout = QHBoxLayout()
        sub_keyword_label = QLabel("보조키워드:")
        sub_keyword_label.setMinimumWidth(80)
        sub_keyword_label.setStyleSheet(f"font-size: {tokens.get_font_size('normal')}px;")
        sub_keyword_layout.addWidget(sub_keyword_label)

        self.sub_keyword_input = ModernLineEdit()
        self.sub_keyword_input.setPlaceholderText("보조 키워드들을 쉼표로 구분 (예: 개발자, 코딩, 입문)")
        self.sub_keyword_input.setMinimumHeight(tokens.spx(40))
        sub_keyword_layout.addWidget(self.sub_keyword_input, 1)

        layout.addLayout(sub_keyword_layout)

        # 제목 추천 버튼
        title_button_layout = QHBoxLayout()
        title_button_layout.setSpacing(tokens.GAP_8)
        title_button_layout.addStretch()

        self.suggest_title_btn = ModernPrimaryButton("🎯 제목 추천받기")
        self.suggest_title_btn.clicked.connect(self.on_suggest_titles_clicked)
        title_button_layout.addWidget(self.suggest_title_btn)

        self.refresh_title_btn = ModernButton("🔄 새로고침")
        self.refresh_title_btn.clicked.connect(self.on_refresh_titles_clicked)
        self.refresh_title_btn.setEnabled(False)
        title_button_layout.addWidget(self.refresh_title_btn)

        layout.addLayout(title_button_layout)

        # 추천 제목 드롭박스
        title_select_layout = QHBoxLayout()
        title_select_label = QLabel("추천 제목:")
        title_select_label.setMinimumWidth(80)
        title_select_label.setStyleSheet(f"font-size: {tokens.get_font_size('normal')}px;")
        title_select_layout.addWidget(title_select_label)

        self.title_suggestion_combo = QComboBox()
        self.title_suggestion_combo.addItem("먼저 제목 추천을 받아보세요")
        self.title_suggestion_combo.setEnabled(False)

        # 콤보박스 스타일 설정 (AI 설정과 동일)
        combo_style = f"""
            QComboBox {{
                padding: {tokens.GAP_8}px {tokens.GAP_12}px;
                border: {tokens.spx(1)}px solid {ModernStyle.COLORS['border']};
                border-radius: {tokens.RADIUS_SM}px;
                background-color: {ModernStyle.COLORS['bg_card']};
                color: {ModernStyle.COLORS['text_primary']};
                font-size: {tokens.get_font_size('normal')}px;
                min-height: {tokens.spx(20)}px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: {tokens.spx(20)}px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: {tokens.spx(5)}px solid transparent;
                border-right: {tokens.spx(5)}px solid transparent;
                border-top: {tokens.spx(5)}px solid {ModernStyle.COLORS['text_secondary']};
                margin-right: {tokens.spx(5)}px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {ModernStyle.COLORS['bg_card']};
                border: {tokens.spx(1)}px solid {ModernStyle.COLORS['border']};
                selection-background-color: {ModernStyle.COLORS['primary']};
                selection-color: white;
                font-size: {tokens.get_font_size('normal')}px;
            }}
        """

        self.title_suggestion_combo.setStyleSheet(combo_style)
        self.title_suggestion_combo.currentTextChanged.connect(self.on_title_selected)
        title_select_layout.addWidget(self.title_suggestion_combo, 1)

        layout.addLayout(title_select_layout)

        return layout

    def create_step_header(self) -> QWidget:
        """Step 헤더 생성"""
        header_widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, tokens.GAP_8)

        step_label = QLabel("🎯 Step 1: AI 설정 & 제목 기획")
        step_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['primary']};
                font-size: {tokens.get_font_size('large')}px;
                font-weight: 700;
                padding: {tokens.spx(8)}px 0px;
            }}
        """)

        layout.addWidget(step_label)
        layout.addStretch()

        header_widget.setLayout(layout)
        return header_widget

    def create_ai_settings_card(self) -> ModernCard:
        """AI 글쓰기 설정 카드 생성"""
        card = ModernCard("🤖 AI 글쓰기 설정")
        layout = QVBoxLayout()
        layout.setSpacing(tokens.GAP_4)

        # 간단한 설명
        simple_desc = QLabel("원하는 글쓰기 스타일을 선택하고 설정을 저장하세요")
        simple_desc.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['primary']};
                font-size: {tokens.get_font_size('normal')}px;
                font-weight: 600;
                padding: {tokens.spx(4)}px 0px;
                margin-bottom: {tokens.GAP_4}px;
            }}
        """)
        layout.addWidget(simple_desc)

        # 컨텐츠 유형 선택
        content_type_layout = QHBoxLayout()
        content_type_label = QLabel("📝 컨텐츠 유형:")
        content_type_label.setStyleSheet(f"font-size: {tokens.get_font_size('normal')}px;")
        content_type_layout.addWidget(content_type_label)

        self.content_type_combo = QComboBox()
        self.content_type_combo.addItems([
            "후기/리뷰형 - 개인 경험과 솔직한 후기 중심",
            "정보/가이드형 - 객관적 정보와 가이드 중심",
            "비교/추천형 - 여러 옵션 비교분석 중심"
        ])
        self.content_type_combo.setCurrentIndex(1)  # 정보/가이드형을 기본값으로

        # 콤보박스 스타일 설정
        combo_style = f"""
            QComboBox {{
                padding: {tokens.GAP_8}px {tokens.GAP_12}px;
                border: {tokens.spx(1)}px solid {ModernStyle.COLORS['border']};
                border-radius: {tokens.RADIUS_SM}px;
                background-color: {ModernStyle.COLORS['bg_card']};
                color: {ModernStyle.COLORS['text_primary']};
                font-size: {tokens.get_font_size('normal')}px;
                min-height: {tokens.spx(20)}px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: {tokens.spx(20)}px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: {tokens.spx(5)}px solid transparent;
                border-right: {tokens.spx(5)}px solid transparent;
                border-top: {tokens.spx(5)}px solid {ModernStyle.COLORS['text_secondary']};
                margin-right: {tokens.spx(5)}px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {ModernStyle.COLORS['bg_card']};
                border: {tokens.spx(1)}px solid {ModernStyle.COLORS['border']};
                selection-background-color: {ModernStyle.COLORS['primary']};
                selection-color: white;
                font-size: {tokens.get_font_size('normal')}px;
            }}
        """
        self.content_type_combo.setStyleSheet(combo_style)
        content_type_layout.addWidget(self.content_type_combo)
        layout.addLayout(content_type_layout)

        # 후기형 세부 옵션 (후기/리뷰형 선택 시에만 표시)
        self.review_detail_layout = QHBoxLayout()
        review_detail_label = QLabel("📋 후기 유형:")
        review_detail_label.setStyleSheet(f"font-size: {tokens.get_font_size('normal')}px;")
        self.review_detail_layout.addWidget(review_detail_label)

        self.review_detail_combo = QComboBox()
        self.review_detail_combo.addItems([
            "내돈내산 후기 - 직접 구매해서 써본 솔직 후기",
            "협찬 후기 - 브랜드 제공 제품의 정직한 리뷰",
            "체험단 후기 - 체험단 참여 후기",
            "대여/렌탈 후기 - 렌탈 서비스 이용 후기"
        ])
        self.review_detail_combo.setStyleSheet(combo_style)
        self.review_detail_layout.addWidget(self.review_detail_combo)

        # 후기형 세부 옵션을 위젯으로 감싸기 (숨기기/보이기 위해)
        self.review_detail_widget = QWidget()
        self.review_detail_widget.setLayout(self.review_detail_layout)
        layout.addWidget(self.review_detail_widget)

        # 말투 선택
        tone_layout = QHBoxLayout()
        tone_label = QLabel("🗣️ 말투 스타일:")
        tone_label.setStyleSheet(f"font-size: {tokens.get_font_size('normal')}px;")
        tone_layout.addWidget(tone_label)

        self.tone_combo = QComboBox()
        self.tone_combo.addItems([
            "친근한 반말체 - '써봤는데 진짜 좋더라~', '완전 강추!'",
            "정중한 존댓말체 - '사용해보았습니다', '추천드립니다'",
            "친근한 존댓말체 - '써봤는데 좋더라구요~', '도움이 될 것 같아요'"
        ])
        self.tone_combo.setCurrentIndex(1)  # 정중한 존댓말체를 기본값으로
        self.tone_combo.setStyleSheet(combo_style)
        tone_layout.addWidget(self.tone_combo)
        layout.addLayout(tone_layout)

        # 블로그 소개 입력
        blogger_identity_layout = QHBoxLayout()
        blogger_identity_label = QLabel("📝 블로그 소개:")
        blogger_identity_label.setStyleSheet(f"font-size: {tokens.get_font_size('normal')}px;")
        blogger_identity_layout.addWidget(blogger_identity_label)

        self.blogger_identity_edit = ModernLineEdit()
        self.blogger_identity_edit.setPlaceholderText("예: 음악과 작곡에 대한 전문 정보를 공유하는 블로그")
        self.blogger_identity_edit.setStyleSheet(f"""
            ModernLineEdit {{
                padding: {tokens.GAP_8}px {tokens.GAP_12}px;
                border: {tokens.spx(1)}px solid {ModernStyle.COLORS['border']};
                border-radius: {tokens.RADIUS_SM}px;
                background-color: {ModernStyle.COLORS['bg_card']};
                color: {ModernStyle.COLORS['text_primary']};
                font-size: {tokens.get_font_size('normal')}px;
                min-height: {tokens.spx(20)}px;
            }}
            ModernLineEdit:focus {{
                border-color: {ModernStyle.COLORS['primary']};
                background-color: {ModernStyle.COLORS['bg_primary']};
            }}
        """)
        blogger_identity_layout.addWidget(self.blogger_identity_edit)
        layout.addLayout(blogger_identity_layout)

        # 컨텐츠 유형 변경 시 후기 세부 옵션 표시/숨김 처리
        self.content_type_combo.currentIndexChanged.connect(self.on_content_type_changed)

        # 초기 상태 설정 (정보/가이드형이 기본이므로 후기 옵션 숨김)
        self.review_detail_widget.setVisible(False)

        # 저장 버튼
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        self.save_settings_button = ModernButton("💾 설정 저장")
        self.save_settings_button.clicked.connect(self.save_ai_settings)
        save_layout.addWidget(self.save_settings_button)
        layout.addLayout(save_layout)

        card.setLayout(layout)
        card.setMaximumHeight(tokens.spx(310))

        return card

    def create_keyword_input_card(self) -> ModernCard:
        """키워드 입력 & 제목 추천 카드 생성"""
        card = ModernCard("🔍 키워드 설정 & 제목 추천")
        layout = QVBoxLayout()
        layout.setSpacing(tokens.GAP_8)

        # 간단한 설명
        simple_desc = QLabel("메인키워드 입력 → 제목 추천받기 → 선택\n   • 보조키워드는 선택사항이며, 여러 개 입력 가능합니다")
        simple_desc.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['primary']};
                font-size: {tokens.get_font_size('normal')}px;
                font-weight: 600;
                padding: {tokens.spx(4)}px 0px;
                margin-bottom: {tokens.GAP_8}px;
                line-height: 1.4;
            }}
        """)
        layout.addWidget(simple_desc)

        # 메인키워드 입력
        main_keyword_layout = QHBoxLayout()
        main_keyword_label = QLabel("메인키워드:")
        main_keyword_label.setMinimumWidth(80)
        main_keyword_label.setStyleSheet(f"font-size: {tokens.get_font_size('normal')}px;")
        main_keyword_layout.addWidget(main_keyword_label)

        self.main_keyword_input = ModernLineEdit()
        self.main_keyword_input.setPlaceholderText("메인키워드 필수 (예: 프로그래밍 학습법)")
        self.main_keyword_input.setMinimumHeight(tokens.spx(40))
        main_keyword_layout.addWidget(self.main_keyword_input, 1)

        layout.addLayout(main_keyword_layout)

        # 보조키워드 입력
        sub_keyword_layout = QHBoxLayout()
        sub_keyword_label = QLabel("보조키워드:")
        sub_keyword_label.setMinimumWidth(80)
        sub_keyword_label.setStyleSheet(f"font-size: {tokens.get_font_size('normal')}px;")
        sub_keyword_layout.addWidget(sub_keyword_label)

        self.sub_keyword_input = ModernLineEdit()
        self.sub_keyword_input.setPlaceholderText("보조 키워드들을 쉼표로 구분 (예: 개발자, 코딩, 입문)")
        self.sub_keyword_input.setMinimumHeight(tokens.spx(40))
        sub_keyword_layout.addWidget(self.sub_keyword_input, 1)

        layout.addLayout(sub_keyword_layout)

        # 제목 추천 버튼
        title_button_layout = QHBoxLayout()
        title_button_layout.setSpacing(tokens.GAP_8)
        title_button_layout.addStretch()

        self.suggest_title_btn = ModernPrimaryButton("🎯 제목 추천받기")
        self.suggest_title_btn.clicked.connect(self.on_suggest_titles_clicked)
        title_button_layout.addWidget(self.suggest_title_btn)

        self.refresh_title_btn = ModernButton("🔄 새로고침")
        self.refresh_title_btn.clicked.connect(self.on_refresh_titles_clicked)
        self.refresh_title_btn.setEnabled(False)
        title_button_layout.addWidget(self.refresh_title_btn)

        layout.addLayout(title_button_layout)

        # 추천 제목 드롭박스
        title_select_layout = QHBoxLayout()
        title_select_label = QLabel("추천 제목:")
        title_select_label.setMinimumWidth(80)
        title_select_label.setStyleSheet(f"font-size: {tokens.get_font_size('normal')}px;")
        title_select_layout.addWidget(title_select_label)

        self.title_suggestion_combo = QComboBox()
        self.title_suggestion_combo.addItem("먼저 제목 추천을 받아보세요")
        self.title_suggestion_combo.setEnabled(False)

        # 콤보박스 스타일 설정 (AI 설정 카드와 동일)
        combo_style = f"""
            QComboBox {{
                padding: {tokens.GAP_8}px {tokens.GAP_12}px;
                border: {tokens.spx(1)}px solid {ModernStyle.COLORS['border']};
                border-radius: {tokens.RADIUS_SM}px;
                background-color: {ModernStyle.COLORS['bg_card']};
                color: {ModernStyle.COLORS['text_primary']};
                font-size: {tokens.get_font_size('normal')}px;
                min-height: {tokens.spx(20)}px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: {tokens.spx(20)}px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: {tokens.spx(5)}px solid transparent;
                border-right: {tokens.spx(5)}px solid transparent;
                border-top: {tokens.spx(5)}px solid {ModernStyle.COLORS['text_secondary']};
                margin-right: {tokens.spx(5)}px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {ModernStyle.COLORS['bg_card']};
                border: {tokens.spx(1)}px solid {ModernStyle.COLORS['border']};
                selection-background-color: {ModernStyle.COLORS['primary']};
                selection-color: white;
                font-size: {tokens.get_font_size('normal')}px;
            }}
        """
        self.title_suggestion_combo.setStyleSheet(combo_style)
        title_select_layout.addWidget(self.title_suggestion_combo, 1)
        layout.addLayout(title_select_layout)

        card.setLayout(layout)
        card.setMaximumHeight(tokens.spx(280))

        return card

    def on_content_type_changed(self, index):
        """컨텐츠 유형 변경 시 후기 세부 옵션 표시/숨김"""
        try:
            # 후기/리뷰형(인덱스 0)일 때만 세부 옵션 표시
            if index == 0:  # 후기/리뷰형
                self.review_detail_combo.setVisible(True)
            else:  # 정보/가이드형, 비교/추천형
                self.review_detail_combo.setVisible(False)
        except Exception as e:
            logger.error(f"컨텐츠 유형 변경 처리 오류: {e}")

    def on_title_selected(self, title_text):
        """제목 선택 시 다음 단계 버튼 활성화"""
        try:
            # 기본 안내 메시지가 아닌 실제 제목이 선택된 경우
            if title_text and title_text != "먼저 제목 추천을 받아보세요":
                self.next_step_btn.setEnabled(True)
                logger.info(f"제목 선택됨: {title_text[:50]}...")
            else:
                self.next_step_btn.setEnabled(False)
        except Exception as e:
            logger.error(f"제목 선택 처리 오류: {e}")

    def get_ai_writing_settings(self) -> dict:
        """사용자가 선택한 AI 글쓰기 설정 반환"""
        content_types = ["후기/리뷰형", "정보/가이드형", "비교/추천형"]
        tones = ["친근한 반말체", "정중한 존댓말체", "친근한 존댓말체"]
        review_details = ["내돈내산 후기", "협찬 후기", "체험단 후기", "대여/렌탈 후기"]

        selected_content_type = content_types[self.content_type_combo.currentIndex()]
        selected_tone = tones[self.tone_combo.currentIndex()]

        settings = {
            "content_type": selected_content_type,
            "tone": selected_tone,
            "content_type_id": self.content_type_combo.currentIndex(),
            "tone_id": self.tone_combo.currentIndex(),
            "blogger_identity": self.blogger_identity_edit.text().strip()
        }

        # 후기/리뷰형인 경우 세부 옵션 추가
        if self.content_type_combo.currentIndex() == 0:  # 후기/리뷰형
            settings["review_detail"] = review_details[self.review_detail_combo.currentIndex()]
            settings["review_detail_id"] = self.review_detail_combo.currentIndex()

        return settings

    def save_ai_settings(self):
        """AI 글쓰기 설정 저장 (service 통해 호출)"""
        try:
            settings = self.get_ai_writing_settings()

            # service를 통해 설정 저장
            if hasattr(self.parent, 'service') and self.parent.service:
                self.parent.service.save_ai_writing_settings(settings)
                
                # 메인 UI의 AI 정보 표시 업데이트
                if hasattr(self.parent, 'update_ai_info_display'):
                    self.parent.update_ai_info_display()

                # 성공 다이얼로그
                TableUIDialogHelper.show_success_dialog(
                    self, "설정 저장 완료",
                    f"AI 글쓰기 설정이 저장되었습니다!\n\n컨텐츠 유형: {settings['content_type']}\n말투 스타일: {settings['tone']}"
                )
            else:
                TableUIDialogHelper.show_error_dialog(
                    self, "서비스 오류", "서비스가 초기화되지 않았습니다."
                )

        except Exception as e:
            logger.error(f"AI 글쓰기 설정 저장 실패: {e}")
            TableUIDialogHelper.show_error_dialog(
                self, "저장 실패", f"설정 저장 중 오류가 발생했습니다:\n{e}"
            )

    def load_ai_settings(self):
        """저장된 AI 글쓰기 설정 로드 (service 통해 호출)"""
        try:
            # service를 통해 설정 로드
            if hasattr(self.parent, 'service') and self.parent.service:
                settings = self.parent.service.load_ai_writing_settings()
                
                # 컨텐츠 유형 로드
                content_type_id = settings.get('content_type_id', 1)
                if 0 <= content_type_id <= 2:
                    self.content_type_combo.setCurrentIndex(content_type_id)

                # 말투 스타일 로드
                tone_id = settings.get('tone_id', 1)
                if 0 <= tone_id <= 2:
                    self.tone_combo.setCurrentIndex(tone_id)

                # 블로거 정체성 로드
                blogger_identity = settings.get('blogger_identity', '')
                self.blogger_identity_edit.setText(blogger_identity)

                # 후기 세부 옵션 로드
                review_detail_id = settings.get('review_detail_id', 0)
                if 0 <= review_detail_id <= 3:
                    self.review_detail_combo.setCurrentIndex(review_detail_id)

                # 컨텐츠 유형에 따라 후기 세부 옵션 표시/숨김
                self.on_content_type_changed(self.content_type_combo.currentIndex())

        except Exception as e:
            logger.error(f"AI 설정 로드 실패: {e}")

    def on_suggest_titles_clicked(self):
        """제목 추천 버튼 클릭"""
        try:
            main_keyword = self.main_keyword_input.text().strip()
            if not main_keyword:
                TableUIDialogHelper.show_error_dialog(
                    self, "입력 오류", "메인키워드를 입력해주세요."
                )
                return

            sub_keywords = self.sub_keyword_input.text().strip()
            ai_settings = self.get_ai_writing_settings()
            content_type = ai_settings.get('content_type', '정보/가이드형')

            logger.info(f"제목 추천 요청: {main_keyword}, AI 설정 유형: {content_type}")

            # 후기 세부 유형 가져오기 (후기/리뷰형일 때만)
            review_detail = ""
            if content_type == "후기/리뷰형":
                review_details = ["내돈내산 후기", "협찬 후기", "체험단 후기", "대여/렌탈 후기"]
                review_detail = review_details[self.review_detail_combo.currentIndex()]

            # service를 통해 제목 추천 프롬프트 생성
            if hasattr(self.parent, 'service') and self.parent.service:
                prompt = self.parent.service.generate_title_suggestions(
                    main_keyword=main_keyword,
                    sub_keywords=sub_keywords,
                    content_type=content_type,
                    review_detail=review_detail
                )

                logger.info(f"제목 추천 AI 프롬프트 생성 완료 (보조키워드: '{sub_keywords}', 후기유형: '{review_detail}')")
                logger.debug(f"생성된 프롬프트: {prompt[:300]}{'...' if len(prompt) > 300 else ''}")

                # 버튼 상태 변경
                self.suggest_title_btn.setText("🔄 AI가 제목을 추천 중...")
                self.suggest_title_btn.setEnabled(False)

                # 실제 AI API 호출하여 제목 추천 받기
                self.call_ai_for_titles(prompt, main_keyword, content_type)
            else:
                TableUIDialogHelper.show_error_dialog(
                    self, "서비스 오류", "서비스가 초기화되지 않았습니다."
                )

        except Exception as e:
            logger.error(f"제목 추천 오류: {e}")
            TableUIDialogHelper.show_error_dialog(
                self, "오류", f"제목 추천 중 오류가 발생했습니다:\n{e}"
            )

    def on_refresh_titles_clicked(self):
        """새로고침 버튼 클릭"""
        try:
            # 새로고침 버튼 상태 변경
            self.refresh_title_btn.setText("🔄 새로고침 중...")
            self.refresh_title_btn.setEnabled(False)

            # 제목 추천 실행
            self.on_suggest_titles_clicked()

        except Exception as e:
            logger.error(f"제목 새로고침 오류: {e}")
            # 오류 시 버튼 상태 복원
            self.refresh_title_btn.setText("🔄 새로고침")
            self.refresh_title_btn.setEnabled(True)

    def call_ai_for_titles(self, prompt: str, main_keyword: str, content_type: str):
        """AI API 호출하여 제목 추천 받기"""
        try:
            # AI 서비스를 통해 제목 추천 요청
            if hasattr(self.parent, 'service') and self.parent.service:
                # 비동기 AI 호출 (워커 사용)
                from .worker import create_title_suggestion_worker, WorkerThread

                self.title_worker = create_title_suggestion_worker(
                    self.parent.service, prompt, main_keyword, content_type
                )
                self.title_thread = WorkerThread(self.title_worker)

                # 시그널 연결
                self.title_worker.titles_generated.connect(self.on_titles_received)
                self.title_worker.error_occurred.connect(self.on_title_generation_error)

                # 워커 시작
                self.title_thread.start()
                logger.info("제목 추천 AI 워커 시작됨")

            else:
                # 서비스가 없는 경우 오류 표시
                logger.error("AI 서비스가 설정되지 않음")
                TableUIDialogHelper.show_error_dialog(
                    self, "AI 서비스 오류", "AI 서비스가 설정되지 않았습니다. API 키를 확인해주세요."
                )
                self.reset_title_ui()

        except Exception as e:
            logger.error(f"AI 제목 추천 호출 오류: {e}")
            # 오류 시 사용자에게 알림
            TableUIDialogHelper.show_error_dialog(
                self, "제목 추천 오류", f"제목 추천 중 오류가 발생했습니다:\n{e}"
            )
            self.reset_title_ui()

    def on_titles_received(self, titles: list):
        """AI로부터 제목 추천을 받았을 때"""
        try:
            logger.info(f"AI 제목 추천 완료: {len(titles)}개")

            if titles and len(titles) > 0:
                # AI가 추천한 제목들 사용
                self.update_title_suggestions(titles)
            else:
                # 빈 결과인 경우 오류 표시
                logger.warning("AI 제목 추천 결과가 비어있음")
                TableUIDialogHelper.show_error_dialog(
                    self, "제목 추천 결과 없음", "AI가 제목을 생성하지 못했습니다. 다시 시도해주세요."
                )

            self.reset_title_ui()

        except Exception as e:
            logger.error(f"제목 수신 처리 오류: {e}")
            self.reset_title_ui()

    def on_title_generation_error(self, error_message: str):
        """AI 제목 추천 오류 처리"""
        try:
            logger.error(f"AI 제목 추천 오류: {error_message}")

            self.reset_title_ui()

            # 사용자에게 오류 알림
            TableUIDialogHelper.show_error_dialog(
                self, "제목 추천 오류",
                f"AI 제목 추천 중 오류가 발생했습니다:\n{error_message}\n\nAPI 키 설정을 확인해주세요."
            )

        except Exception as e:
            logger.error(f"제목 추천 오류 처리 중 오류: {e}")

    def reset_title_ui(self):
        """제목 추천 UI 상태 초기화"""
        self.suggest_title_btn.setText("🎯 제목 추천받기")
        self.suggest_title_btn.setEnabled(True)
        self.refresh_title_btn.setText("🔄 새로고침")
        self.refresh_title_btn.setEnabled(True)


    def update_title_suggestions(self, titles_data):
        """제목 추천 드롭박스 업데이트"""
        self.title_suggestion_combo.clear()

        # 새로운 구조 (제목 + 검색어)인지 확인
        if isinstance(titles_data, list) and len(titles_data) > 0:
            first_item = titles_data[0]

            # 새로운 구조: [{"title": "...", "search_query": "..."}, ...]
            if isinstance(first_item, dict) and "title" in first_item and "search_query" in first_item:
                self.titles_with_search = titles_data
                titles_only = [item["title"] for item in titles_data]
                self.title_suggestion_combo.addItems(titles_only)
                logger.info(f"제목+검색어 구조로 드롭박스 업데이트: {len(titles_data)}개")

            # 기존 구조: ["제목1", "제목2", ...]
            else:
                self.titles_with_search = []
                self.title_suggestion_combo.addItems(titles_data)
                logger.info(f"기존 제목 구조로 드롭박스 업데이트: {len(titles_data)}개")

        self.title_suggestion_combo.setEnabled(True)
        self.refresh_title_btn.setEnabled(True)
        self.next_step_btn.setEnabled(True)

    def get_search_query_for_title(self, title: str) -> str:
        """선택된 제목에 해당하는 검색어 반환"""
        try:
            for item in self.titles_with_search:
                if isinstance(item, dict) and item.get('title') == title:
                    return item.get('search_query', title)  # 검색어가 없으면 제목 자체 사용
            return title  # 매칭되는 항목이 없으면 제목 자체 사용
        except Exception as e:
            logger.warning(f"검색어 조회 오류, 제목 사용: {e}")
            return title

    def on_next_step_clicked(self):
        """다음 단계로 진행"""
        try:
            selected_title = self.title_suggestion_combo.currentText()
            if selected_title == "먼저 제목 추천을 받아보세요" or not selected_title:
                TableUIDialogHelper.show_error_dialog(
                    self, "선택 오류", "추천받은 제목 중 하나를 선택해주세요."
                )
                return

            # 선택된 제목에 해당하는 검색어 찾기
            search_query = self.get_search_query_for_title(selected_title)

            # Step 1 완료 데이터 준비
            step1_data = {
                'ai_settings': self.get_ai_writing_settings(),
                'main_keyword': self.main_keyword_input.text().strip(),
                'sub_keywords': self.sub_keyword_input.text().strip(),
                'selected_title': selected_title,
                'search_query': search_query  # 검색어 추가
            }

            logger.info(f"Step 1 완료, 선택된 제목: {selected_title}")
            logger.info(f"사용할 검색어: {search_query}")

            # 다음 단계로 데이터 전달
            self.step_completed.emit(step1_data)

        except Exception as e:
            logger.error(f"다음 단계 진행 오류: {e}")
            TableUIDialogHelper.show_error_dialog(
                self, "오류", f"다음 단계로 진행 중 오류가 발생했습니다:\n{e}"
            )