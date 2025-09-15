"""
블로그 자동화 Step 3: 네이버 블로그 발행
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QScrollArea
)
from PySide6.QtCore import Qt, Signal
import traceback

from src.foundation.logging import get_logger
from src.toolbox.ui_kit.components import (
    ModernButton, ModernCard, ModernDangerButton, ModernPrimaryButton
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

        # 글 내용 편집 카드
        content_editor_card = self.create_content_editor_card()
        main_layout.addWidget(content_editor_card, 1)  # 가장 많은 공간 할당

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

    def create_content_editor_card(self) -> ModernCard:
        """글 내용 편집 카드"""
        card = ModernCard("✏️ 글 내용 편집")
        layout = QVBoxLayout()
        layout.setSpacing(tokens.GAP_8)

        # 안내 메시지
        info_label = QLabel(
            "AI가 생성한 글을 확인하고 필요한 부분을 수정할 수 있습니다.\n"
            "아래 텍스트 에디터에서 자유롭게 내용을 편집해주세요."
        )
        info_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_secondary']};
                font-size: {tokens.get_font_size('small')}px;
                padding: {tokens.spx(4)}px 0px;
            }}
        """)
        layout.addWidget(info_label)

        # 텍스트 에디터 (스크롤 가능)
        self.content_editor = QTextEdit()
        self.content_editor.setPlainText(self.step2_data.get('generated_content', ''))
        self.content_editor.setMinimumHeight(tokens.spx(400))
        self.content_editor.setStyleSheet(f"""
            QTextEdit {{
                border: {tokens.spx(1)}px solid {ModernStyle.COLORS['border']};
                border-radius: {tokens.RADIUS_SM}px;
                background-color: {ModernStyle.COLORS['bg_card']};
                color: {ModernStyle.COLORS['text_primary']};
                font-size: {tokens.get_font_size('normal')}px;
                font-family: 'Pretendard', 'Malgun Gothic', sans-serif;
                line-height: 1.6;
                padding: {tokens.spx(12)}px;
            }}
            QTextEdit:focus {{
                border-color: {ModernStyle.COLORS['primary']};
            }}
        """)
        layout.addWidget(self.content_editor, 1)

        # 글자 수 표시
        self.char_count_label = QLabel()
        self.update_char_count()
        self.char_count_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_muted']};
                font-size: {tokens.get_font_size('small')}px;
                text-align: right;
                padding: {tokens.spx(4)}px 0px;
            }}
        """)
        self.char_count_label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.char_count_label)

        # 텍스트 변경 시 글자 수 업데이트
        self.content_editor.textChanged.connect(self.update_char_count)

        # 편집 기능 버튼들
        button_layout = QHBoxLayout()
        
        # 원본 복원 버튼
        self.restore_btn = ModernButton("🔄 원본으로 복원")
        self.restore_btn.clicked.connect(self.restore_original_content)
        button_layout.addWidget(self.restore_btn)

        button_layout.addStretch()

        # 내용 저장 버튼
        self.save_content_btn = ModernPrimaryButton("💾 내용 저장")
        self.save_content_btn.clicked.connect(self.save_edited_content)
        button_layout.addWidget(self.save_content_btn)

        layout.addLayout(button_layout)

        card.setLayout(layout)
        return card

    def update_char_count(self):
        """글자 수 업데이트"""
        try:
            content = self.content_editor.toPlainText()
            char_count = len(content.replace(' ', '').replace('\n', ''))
            total_chars = len(content)
            self.char_count_label.setText(f"글자 수: {char_count:,}자 (공백 포함: {total_chars:,}자)")
        except Exception as e:
            logger.error(f"글자 수 계산 오류: {e}")

    def restore_original_content(self):
        """원본 내용으로 복원"""
        try:
            original_content = self.step2_data.get('generated_content', '')
            self.content_editor.setPlainText(original_content)
            logger.info("원본 내용으로 복원됨")
            
            TableUIDialogHelper.show_info_dialog(
                self, "복원 완료", "AI가 생성한 원본 내용으로 복원되었습니다.", "🔄"
            )
        except Exception as e:
            logger.error(f"원본 복원 오류: {e}")

    def save_edited_content(self):
        """편집된 내용 저장"""
        try:
            edited_content = self.content_editor.toPlainText().strip()
            if not edited_content:
                TableUIDialogHelper.show_error_dialog(
                    self, "내용 없음", "저장할 내용이 없습니다."
                )
                return

            # step2_data에 편집된 내용 업데이트
            self.step2_data['generated_content'] = edited_content
            self.step2_data['content_edited'] = True
            
            logger.info(f"편집된 내용 저장됨 ({len(edited_content):,}자)")
            
            TableUIDialogHelper.show_info_dialog(
                self, "저장 완료", f"편집된 내용이 저장되었습니다.\n글자 수: {len(edited_content.replace(' ', '')):,}자", "💾"
            )
        except Exception as e:
            logger.error(f"내용 저장 오류: {e}")
            TableUIDialogHelper.show_error_dialog(
                self, "저장 오류", f"내용 저장 중 오류가 발생했습니다:\n{e}"
            )

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

            # 현재 편집기의 내용 가져오기
            current_content = self.content_editor.toPlainText().strip()
            if not current_content:
                TableUIDialogHelper.show_error_dialog(
                    self, "내용 없음", "발행할 내용이 없습니다.\n글을 작성해주세요."
                )
                return

            # TODO: 실제 발행 로직 구현
            # 현재는 구현 예정 메시지만 표시
            TableUIDialogHelper.show_info_dialog(
                self, "구현 예정",
                "네이버 블로그 발행 기능은 곧 구현됩니다.\n"
                f"발행할 내용:\n"
                f"• 제목: {self.step1_data.get('selected_title', '')}\n"
                f"• 글자수: {len(current_content.replace(' ', '')):,}자\n"
                f"• 편집 여부: {'수정됨' if self.step2_data.get('content_edited', False) else '원본'}\n\n"
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
        current_content = self.content_editor.toPlainText() if hasattr(self, 'content_editor') else self.step2_data.get('generated_content', '')
        return {
            'publish_ready': True,
            'title': self.step1_data.get('selected_title', ''),
            'content': current_content,
            'content_length': len(current_content.replace(' ', '').replace('\n', '')),
            'content_edited': self.step2_data.get('content_edited', False),
            'original_content': self.step2_data.get('generated_content', '')
        }