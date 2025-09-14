"""
블로그 자동화 Step 3: 네이버 블로그 발행
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel
)
from PySide6.QtCore import Qt, Signal
import traceback

from src.foundation.logging import get_logger
from src.toolbox.ui_kit.components import (
    ModernButton, ModernCard, ModernDangerButton
)
from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
from src.toolbox.ui_kit.modern_style import ModernStyle
from src.toolbox.ui_kit import tokens
from src.foundation.exceptions import BusinessError, ValidationError

logger = get_logger("blog_automation.ui_table3")


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


class BlogAutomationStep3UI(QWidget):
    """Step 3: 네이버 블로그 발행"""

    # 시그널 정의
    publish_completed = Signal(bool, str)  # 발행 완료 (성공여부, 메시지)

    def __init__(self, step1_data: dict, step2_data: dict, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.step1_data = step1_data
        self.step2_data = step2_data

        self.setup_ui()

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

        # 완성된 작업 요약 카드
        summary_card = self.create_summary_card()
        main_layout.addWidget(summary_card)

        # 발행 준비 카드
        publish_card = self.create_publish_card()
        main_layout.addWidget(publish_card)

        # 네비게이션 버튼들
        nav_layout = QHBoxLayout()

        # 이전 단계 버튼
        self.prev_step_btn = ModernButton("⬅️ 2단계로 돌아가기")
        self.prev_step_btn.clicked.connect(self.on_prev_step_clicked)
        nav_layout.addWidget(self.prev_step_btn)

        nav_layout.addStretch()

        main_layout.addLayout(nav_layout)

        self.setLayout(main_layout)

    def create_step_header(self) -> QWidget:
        """Step 헤더 생성"""
        header_widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, tokens.GAP_8)

        step_label = QLabel("📤 Step 3: 네이버 블로그 발행")
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

    def create_summary_card(self) -> ModernCard:
        """완성된 작업 요약 카드"""
        card = ModernCard("✅ 작업 완료 요약")
        layout = QVBoxLayout()
        layout.setSpacing(tokens.GAP_8)

        # Step 1, 2 요약 정보
        selected_title = self.step1_data.get('selected_title', '제목 없음')
        ai_settings = self.step1_data.get('ai_settings', {})
        content_type = ai_settings.get('content_type', '정보/가이드형')

        blog_count = self.step2_data.get('blog_count', 0)
        generated_content = self.step2_data.get('generated_content', '')
        content_length = len(generated_content.replace(' ', '')) if generated_content else 0

        # 제목 정보
        title_info = QLabel(f"🎯 선택된 제목: {selected_title}")
        title_info.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_primary']};
                font-size: {tokens.get_font_size('normal')}px;
                font-weight: 600;
                background-color: {ModernStyle.COLORS['bg_primary']};
                padding: {tokens.spx(8)}px;
                border-radius: {tokens.RADIUS_SM}px;
                margin-bottom: {tokens.GAP_4}px;
            }}
        """)
        layout.addWidget(title_info)

        # 작업 통계
        stats_info = QLabel(
            f"📊 분석한 블로그: {blog_count}개   |   📝 생성된 글자수: {content_length:,}자   |   📋 콘텐츠 유형: {content_type}"
        )
        stats_info.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_secondary']};
                font-size: {tokens.get_font_size('small')}px;
                padding: {tokens.spx(4)}px 0px;
            }}
        """)
        layout.addWidget(stats_info)

        # 성공 메시지
        success_msg = QLabel("🎉 모든 준비가 완료되었습니다! 이제 네이버 블로그에 발행할 수 있습니다.")
        success_msg.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['success']};
                font-size: {tokens.get_font_size('normal')}px;
                font-weight: 600;
                padding: {tokens.spx(8)}px;
                background-color: {ModernStyle.COLORS['bg_success']};
                border-radius: {tokens.RADIUS_SM}px;
            }}
        """)
        layout.addWidget(success_msg)

        card.setLayout(layout)
        return card

    def create_publish_card(self) -> ModernCard:
        """발행 카드"""
        card = ModernCard("🚀 네이버 블로그 발행")
        layout = QVBoxLayout()
        layout.setSpacing(tokens.GAP_12)

        # 발행 안내
        info_label = QLabel(
            "생성된 블로그 글을 네이버 블로그에 자동으로 발행합니다.\n"
            "발행 전에 결과 탭에서 생성된 글을 한 번 더 확인해보세요."
        )
        info_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_secondary']};
                font-size: {tokens.get_font_size('normal')}px;
                line-height: 1.4;
                padding: {tokens.spx(8)}px 0px;
            }}
        """)
        layout.addWidget(info_label)

        # 발행 버튼
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.publish_btn = ModernDangerButton("🚀 네이버 블로그에 발행하기")
        self.publish_btn.clicked.connect(self.on_publish_clicked)
        button_layout.addWidget(self.publish_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        card.setLayout(layout)
        return card

    def on_publish_clicked(self):
        """네이버 블로그 발행 버튼 클릭"""
        try:
            logger.info("네이버 블로그 발행 시작")

            # TODO: 실제 발행 로직 구현
            # 현재는 구현 예정 메시지만 표시
            TableUIDialogHelper.show_info_dialog(
                self, "구현 예정",
                "네이버 블로그 발행 기능은 곧 구현됩니다.\n"
                f"발행할 내용:\n"
                f"• 제목: {self.step1_data.get('selected_title', '')}\n"
                f"• 글자수: {len(self.step2_data.get('generated_content', '').replace(' ', '')):,}자\n\n"
                "현재는 UI만 구성된 상태입니다.",
                "🚧"
            )

            # 발행 완료 시그널 (임시로 성공 처리)
            self.publish_completed.emit(False, "구현 예정")

        except Exception as e:
            logger.error(f"블로그 발행 오류: {e}")
            TableUIDialogHelper.show_error_dialog(
                self, "발행 오류", f"블로그 발행 중 오류가 발생했습니다:\n{e}"
            )

    def on_prev_step_clicked(self):
        """이전 단계로 돌아가기"""
        try:
            logger.info("2단계로 돌아가기")
            # TODO: Step 2로 돌아가는 로직 구현 (메인 UI에서 처리)
            if hasattr(self.parent, 'load_step'):
                self.parent.load_step(2)

        except Exception as e:
            logger.error(f"이전 단계 이동 오류: {e}")

    def get_step3_data(self) -> dict:
        """Step 3 데이터 반환"""
        return {
            'publish_ready': True,
            'title': self.step1_data.get('selected_title', ''),
            'content': self.step2_data.get('generated_content', ''),
            'content_length': len(self.step2_data.get('generated_content', '').replace(' ', ''))
        }