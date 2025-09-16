"""
블로그 자동화 Step 3: 네이버 블로그 발행
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView
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

        # 글 내용 편집 카드 (더 많은 공간 할당)
        content_editor_card = self.create_content_editor_card()
        main_layout.addWidget(content_editor_card, 2)  # stretch factor를 2로 증가

        # 발행 준비 카드 (최소 공간)
        publish_card = self.create_publish_card()
        main_layout.addWidget(publish_card, 0)  # 고정 크기 유지

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
        tone = ai_settings.get('tone', '정중한 존댓말체')

        blog_count = self.step2_data.get('blog_count', 0)
        generated_content = self.step2_data.get('generated_content', '')
        content_length = len(generated_content.replace(' ', '')) if generated_content else 0
        
        # 이미지 태그 개수 계산 (괄호형과 대괄호형 모두 포함)
        if generated_content:
            paren_images = generated_content.count('(이미지)')
            bracket_images = generated_content.count('[이미지]')
            image_count = paren_images + bracket_images
        else:
            image_count = 0

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
            f"📊 분석한 블로그: {blog_count}개   |   📝 생성된 글자수: {content_length:,}자   |   🖼️ 권장 이미지: {image_count}개   |   📋 콘텐츠 유형: {content_type}   |   💬 말투: {tone}"
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
                background-color: {ModernStyle.COLORS['bg_muted']};
                border-radius: {tokens.RADIUS_SM}px;
                border-left: {tokens.spx(3)}px solid {ModernStyle.COLORS['success']};
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

        # 안내 메시지 (간결하게)
        info_label = QLabel("AI 생성 글을 확인하고 자유롭게 편집하세요.")
        info_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_secondary']};
                font-size: {tokens.get_font_size('small')}px;
                padding: {tokens.spx(4)}px 0px;
            }}
        """)
        layout.addWidget(info_label)

        # 텍스트 편집 도구 모음
        tools_layout = QHBoxLayout()
        tools_layout.setSpacing(tokens.GAP_12)
        
        # 글씨 크기 라벨
        font_size_label = QLabel("📏 글씨 크기:")
        font_size_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_primary']};
                font-size: {tokens.get_font_size('small')}px;
                font-weight: 600;
            }}
        """)
        tools_layout.addWidget(font_size_label)
        
        # 글씨 크기 드롭박스
        from PySide6.QtWidgets import QComboBox
        self.font_size_combo = QComboBox()
        self.font_size_combo.addItems([
            "대제목 (20px)",    # UI 표시 20px (발행시 24px)
            "소제목 (15px)",    # UI 표시 15px (발행시 19px)  
            "강조 (12px)",      # UI 표시 12px (발행시 16px)
            "일반 (11px)"       # UI 표시 11px (발행시 15px)
        ])
        self.font_size_combo.setCurrentIndex(3)  # 기본값: 일반
        self.font_size_combo.currentIndexChanged.connect(self.on_font_size_combo_changed)
        
        # 드롭박스 스타일링
        self.font_size_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {ModernStyle.COLORS['bg_card']};
                color: {ModernStyle.COLORS['text_primary']};
                border: {tokens.spx(1)}px solid {ModernStyle.COLORS['border']};
                border-radius: {tokens.RADIUS_SM}px;
                padding: {tokens.spx(6)}px {tokens.spx(12)}px;
                font-size: {tokens.get_font_size('small')}px;
                min-width: {tokens.spx(120)}px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: {tokens.spx(20)}px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid {ModernStyle.COLORS['text_secondary']};
                margin-right: {tokens.spx(4)}px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {ModernStyle.COLORS['bg_card']};
                border: {tokens.spx(1)}px solid {ModernStyle.COLORS['border']};
                border-radius: {tokens.RADIUS_SM}px;
                selection-background-color: {ModernStyle.COLORS['primary']};
                color: {ModernStyle.COLORS['text_primary']};
                outline: none;
            }}
        """)
        tools_layout.addWidget(self.font_size_combo)
        
        # 글자 수 표시를 도구 영역 맨 오른쪽에 추가
        self.char_count_label = QLabel()
        self.char_count_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_muted']};
                font-size: {tokens.get_font_size('small')}px;
                text-align: right;
                padding: {tokens.spx(4)}px {tokens.spx(8)}px;
                margin-left: {tokens.spx(12)}px;
            }}
        """)
        self.char_count_label.setAlignment(Qt.AlignRight)
        
        tools_layout.addStretch()
        tools_layout.addWidget(self.char_count_label)
        layout.addLayout(tools_layout)
        
        # 현재 폰트 크기 추적 (새 텍스트 입력용)
        self.current_font_size = '11'  # 기본값: UI 일반 (11px, 발행시 15px)

        # 텍스트 에디터 (스크롤 가능)
        self.content_editor = QTextEdit()
        
        # 원본 내용을 모바일 최적화 형태로 자동 변환 (QTextCharFormat 방식)
        original_content = self.step2_data.get('generated_content', '')
        
        # 3단계에서 AI 콘텐츠 정리 (구조 설명, 태그 정리 등)
        from src.toolbox.text_utils import clean_ai_generated_content
        cleaned_content = clean_ai_generated_content(original_content)
        
        # 마크다운 처리와 줄바꿈을 한 번에 처리 (포맷팅 손실 없음)
        self.apply_markdown_fonts_with_line_breaks(cleaned_content)
        self.content_editor.setMinimumHeight(tokens.spx(300))  # 최소 높이 조정 (350→300px)
        self.content_editor.setStyleSheet(f"""
            QTextEdit {{
                border: {tokens.spx(1)}px solid {ModernStyle.COLORS['border']};
                border-radius: {tokens.RADIUS_SM}px;
                background-color: {ModernStyle.COLORS['bg_card']};
                color: {ModernStyle.COLORS['text_primary']};
                font-size: 15px;
                font-family: 'Pretendard', 'Malgun Gothic', sans-serif;
                line-height: 1.6;
                padding: {tokens.spx(12)}px;
            }}
            QTextEdit:focus {{
                border-color: {ModernStyle.COLORS['primary']};
            }}
        """)
        layout.addWidget(self.content_editor, 1)
        
        # 글자수 초기 업데이트
        self.update_char_count()

        # 텍스트 변경 시 글자 수 업데이트
        self.content_editor.textChanged.connect(self.update_char_count)
        
        # 클릭 시에만 폰트 크기 감지 (드래그 시에는 방해하지 않음)
        self.content_editor.cursorPositionChanged.connect(self.smart_update_font_from_cursor)

        # 편집 기능 버튼들
        button_layout = QHBoxLayout()
        
        # 원본 복원 버튼
        self.restore_btn = ModernButton("🔄 원본으로 복원")
        self.restore_btn.clicked.connect(self.restore_original_content)
        button_layout.addWidget(self.restore_btn)


        button_layout.addStretch()

        # 클립보드 복사 버튼
        self.copy_content_btn = ModernPrimaryButton("📋 클립보드 복사")
        self.copy_content_btn.clicked.connect(self.copy_content_to_clipboard)
        button_layout.addWidget(self.copy_content_btn)

        layout.addLayout(button_layout)

        card.setLayout(layout)
        return card


    def simple_split_by_space(self, text: str, max_length: int) -> list:
        """공백 기준으로 텍스트를 분할 (최대 길이 제한)"""
        if len(text) <= max_length:
            return [text]
        
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if len(test_line) <= max_length:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines if lines else [text]

    def is_structured_content(self, text: str) -> bool:
        """구조화된 콘텐츠인지 확인 (대제목, 소제목, 표, 이미지 등)"""
        text = text.strip()
        
        # 대제목, 소제목
        if text.startswith('##') or text.startswith('###'):
            return True
        
        # 표 형태
        if text.startswith('|') and text.endswith('|') and text.count('|') >= 3:
            return True
        
        # 이미지 표시
        if '(이미지)' in text or '[이미지]' in text:
            return True
        
        # 체크리스트 형태
        if text.startswith('✓') or text.startswith('- ') or text.startswith('* '):
            return True
        
        return False

    def apply_markdown_fonts_with_line_breaks(self, content: str):
        """마크다운 처리와 줄바꿈을 동시에 처리 (포맷팅 손실 없음)"""
        try:
            import re
            from PySide6.QtGui import QTextCursor, QTextCharFormat, QFont
            from PySide6.QtCore import Qt
            
            logger.info(f"🔄 통합 마크다운+줄바꿈 처리 시작. 내용 길이: {len(content)}자")
            
            # 에디터 초기화
            self.content_editor.clear()
            cursor = self.content_editor.textCursor()
            
            lines = content.split('\n')
            logger.info(f"📄 총 {len(lines)}줄 처리 예정")
            
            # 표 처리를 위한 상태 변수
            in_table = False
            table_lines = []
            
            i = 0
            while i < len(lines):
                line = lines[i]
                stripped = line.strip()
                
                if not stripped:
                    if in_table:
                        # 표가 끝났으면 HTML 방식으로 처리
                        self.insert_table_html(table_lines, cursor)
                        table_lines = []
                        in_table = False
                    # 빈 줄 처리
                    cursor.insertText('\n')
                    i += 1
                    continue
                
                # 마크다운 표 감지
                stripped_line = line.strip()
                is_table_line = (
                    stripped_line.startswith('|') and 
                    stripped_line.endswith('|') and 
                    stripped_line.count('|') >= 3
                )
                
                if is_table_line:
                    if not in_table:
                        in_table = True
                    table_lines.append(line)
                    i += 1
                    continue
                
                # 표가 진행 중이었는데 표가 아닌 라인을 만나면 표 처리
                if in_table:
                    self.insert_table_html(table_lines, cursor)
                    table_lines = []
                    in_table = False
                
                # ## 대제목 처리 (줄바꿈 체크 없음 - 한 줄 유지)
                if line.strip().startswith('## '):
                    title_text = line.strip()[3:].strip()
                    format = QTextCharFormat()
                    format.setFontPointSize(20)
                    format.setFontWeight(QFont.DemiBold)
                    cursor.insertText(title_text, format)
                    
                # ### 소제목 처리 (줄바꿈 체크 없음 - 한 줄 유지)
                elif line.strip().startswith('### '):
                    subtitle_text = line.strip()[4:].strip()
                    format = QTextCharFormat()
                    format.setFontPointSize(15)
                    format.setFontWeight(QFont.DemiBold)
                    cursor.insertText(subtitle_text, format)
                
                # 일반 라인에서 **강조** 처리 + 줄바꿈 체크
                else:
                    # 긴 줄인지 체크
                    if len(stripped) > 30 and not self.is_structured_content(stripped):
                        # 긴 줄을 짧게 나누기
                        split_lines = self.simple_split_by_space(stripped, 25)
                        
                        for split_idx, split_line in enumerate(split_lines):
                            self.process_text_line_with_bold(cursor, split_line)
                            # 마지막 분할 라인이 아니면 줄바꿈 추가
                            if split_idx < len(split_lines) - 1:
                                cursor.insertText('\n')
                    else:
                        # 짧은 줄은 그대로 처리
                        self.process_text_line_with_bold(cursor, stripped)
                
                # 줄바꿈 추가 (마지막 줄 제외)
                if i < len(lines) - 1:
                    cursor.insertText('\n')
                
                i += 1
            
            # 마지막에 표가 남아있다면 HTML로 처리
            if in_table and table_lines:
                self.insert_table_html(table_lines, cursor)
            
            logger.info("✅ 통합 마크다운+줄바꿈 처리 완료")
            
        except Exception as e:
            logger.error(f"❌ 통합 마크다운+줄바꿈 처리 오류: {e}")

    def process_text_line_with_bold(self, cursor, text_line):
        """한 줄에서 **강조** 처리"""
        import re
        from PySide6.QtGui import QTextCharFormat, QFont
        
        # **텍스트** 패턴 찾기 및 처리
        parts = re.split(r'(\*\*.*?\*\*)', text_line)
        
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                # 강조 텍스트
                bold_text = part[2:-2]  # ** 제거
                format = QTextCharFormat()
                format.setFontPointSize(12)
                format.setFontWeight(QFont.DemiBold)
                cursor.insertText(bold_text, format)
            else:
                # 일반 텍스트
                format = QTextCharFormat()
                format.setFontPointSize(11)
                format.setFontWeight(QFont.Normal)
                cursor.insertText(part, format)

    def insert_table_html(self, table_lines: list, cursor):
        """마크다운 표를 HTML 형식으로 변환하여 삽입 (하이브리드 렌더링)"""
        try:
            if not table_lines:
                return
            
            logger.debug(f"HTML 표 변환 시작. 표 라인 수: {len(table_lines)}")
            
            # 마크다운 표를 HTML로 변환
            html_table = self.convert_markdown_table_to_html(table_lines)
            
            if html_table:
                logger.debug(f"생성된 HTML 표: {html_table[:200]}...")
                
                # HTML 형식으로 표 삽입
                cursor.insertHtml(html_table)
                cursor.insertText('\n')  # 표 다음에 줄바꿈 추가
                
                logger.info(f"HTML 표 삽입 완료")
            else:
                logger.warning("HTML 표 변환 실패 - 일반 텍스트로 삽입")
                # 변환 실패시 마크다운 원본 삽입
                for line in table_lines:
                    cursor.insertText(line + '\n')
                    
        except Exception as e:
            logger.error(f"HTML 표 삽입 오류: {e}")
            # 오류 시 마크다운 원본 삽입
            try:
                for line in table_lines:
                    cursor.insertText(line + '\n')
            except:
                pass

    def convert_markdown_table_to_html(self, table_lines: list) -> str:
        """마크다운 표를 HTML 표로 변환 (기존 깃 방식과 동일한 가로줄 세로줄 포함)"""
        try:
            if not table_lines:
                return ""
            
            # 표 데이터 파싱
            table_data = []
            for line in table_lines:
                if '---' in line:  # 구분선 스킵
                    continue
                
                # | 기호로 분리하고 양쪽 공백 제거
                cells = [cell.strip() for cell in line.split('|')[1:-1]]  # 양쪽 빈 요소 제거
                if cells:
                    table_data.append(cells)
            
            if not table_data:
                return ""
            
            rows = len(table_data)
            cols = len(table_data[0]) if table_data else 0
            
            # 기존 깃 방식과 동일한 스타일로 표 생성
            html_parts = ['<table style="border-collapse: collapse; width: 100%; margin: 10px 0; border: 1px solid #ddd;">']
            
            for row_idx, row_data in enumerate(table_data):
                # 헤더 행 스타일 (기존과 동일)
                if row_idx == 0:
                    html_parts.append('<tr style="background-color: #f8f9fa;">')
                else:
                    html_parts.append('<tr>')
                
                for col_idx, cell_data in enumerate(row_data):
                    # 기존 깃과 동일한 셀 스타일: 가로줄 세로줄 + 패딩 + 가운데 정렬
                    cell_html = f'<td style="border: 1px solid #ddd; padding: 12px; text-align: center;">{cell_data}</td>'
                    html_parts.append(cell_html)
                
                html_parts.append('</tr>')
            
            html_parts.append('</table>')
            
            html_result = ''.join(html_parts)
            logger.debug(f"HTML 표 변환 완료 (가로줄 세로줄 포함): {rows}행 × {cols}열")
            return html_result
            
        except Exception as e:
            logger.error(f"마크다운→HTML 표 변환 오류: {e}")
            return ""

    def simple_split_by_space(self, text: str, target_length: int) -> list:
        """단순 길이 기반 텍스트 분리 (공백 우선)"""
        if len(text) <= target_length + 3:
            return [text]
        
        result = []
        current = text
        
        while len(current) > target_length + 3:
            # 25±3자 범위에서 가장 적절한 공백 찾기
            best_pos = target_length
            
            # target_length-3 ~ target_length+5 범위에서 공백 찾기
            for i in range(max(target_length - 3, 10), min(target_length + 6, len(current))):
                if current[i] == ' ':
                    best_pos = i
                    break
            
            # 공백을 찾았으면 그 위치에서 분리
            if best_pos < len(current) and current[best_pos] == ' ':
                result.append(current[:best_pos].strip())
                current = current[best_pos:].strip()
            else:
                # 공백이 없으면 target_length에서 강제 분리
                result.append(current[:target_length])
                current = current[target_length:]
        
        # 남은 텍스트 추가
        if current.strip():
            result.append(current.strip())
        
        return result

    def is_structured_content(self, line: str) -> bool:
        """구조화된 콘텐츠인지 판별 (리스트, 단계별 설명 등)"""
        try:
            line_strip = line.strip()
            
            # 해시태그 줄 (# 기호가 여러 개 있는 경우 - 줄바꿈 제외)
            if '#' in line_strip and len([part for part in line_strip.split() if part.startswith('#')]) >= 2:
                return True
            
            # 마크다운 소제목 (## 또는 ###로 시작 - 줄바꿈 제외)
            if line_strip.startswith('## ') or line_strip.startswith('### '):
                return True
            
            # 체크리스트/불릿 포인트 패턴 (다양한 형태)
            bullet_patterns = [
                '✓ ', '✔ ', '✔️ ', '☑ ', '☑️ ', '✅ ',  # 체크마크
                '- ', '• ', '◦ ', '▪ ', '▫ ', '‣ ',     # 불릿
                '→ ', '➤ ', '► ', '▶ ', '🔸 ', '🔹 ',    # 화살표/도형
                '★ ', '⭐ ', '🌟 ', '💡 ', '📌 ', '🎯 '   # 기타 강조
            ]
            
            for pattern in bullet_patterns:
                if line_strip.startswith(pattern):
                    return True
            
            # 번호 목록 패턴 (숫자, 로마자, 한글 등)
            # 1. 2. 3. 또는 1) 2) 3) 패턴
            if line_strip and (line_strip[0].isdigit() and ('. ' in line_strip[:5] or ') ' in line_strip[:5])):
                return True
            
            # 로마자 패턴 (a. b. c. 또는 A. B. C.)
            if len(line_strip) >= 3 and line_strip[1] in '. )' and line_strip[0].isalpha():
                return True
            
            # 한글 자모 패턴 (가. 나. 다. 또는 ㄱ. ㄴ. ㄷ.)
            korean_chars = 'ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅍㅎ가나다라마바사아자차카타파하'
            if len(line_strip) >= 3 and line_strip[1] in '. )' and line_strip[0] in korean_chars:
                return True
            
            # 단계별 패턴 (**1단계:**, **2단계:** 등)
            if '단계:' in line_strip or '**단계' in line_strip:
                return True
            
            # 표 형태나 구조화된 데이터 (: 기호가 많이 있는 경우)
            if line_strip.count(':') >= 2:
                return True
            
            # 마크다운 표 형태 (| 기호로 구분)
            if line_strip.startswith('|') and line_strip.endswith('|') and line_strip.count('|') >= 3:
                return True
            
            # 표 구분선 (---|---|--- 형태)
            if '---' in line_strip and '|' in line_strip:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"구조화된 콘텐츠 판별 오류: {e}")
            return False

    def update_char_count(self):
        """글자 수 업데이트"""
        try:
            # HTML 모드에서도 텍스트 내용을 정확히 가져오기
            content = self.content_editor.toPlainText()
            char_count = len(content.replace(' ', '').replace('\n', ''))
            total_chars = len(content)
            self.char_count_label.setText(f"글자 수: {char_count:,}자 (공백 포함: {total_chars:,}자)")
        except Exception as e:
            logger.error(f"글자 수 계산 오류: {e}")

    def on_font_size_combo_changed(self, index: int):
        """드롭박스에서 폰트 크기 변경 시"""
        try:
            # UI 표시용 폰트 크기 (발행시 +4해서 네이버 크기로)
            font_sizes = ['20', '15', '12', '11']  # UI용: 20, 15, 12, 11 (발행시: 24, 19, 16, 15)
            
            self.current_font_size = font_sizes[index]
            
            # 새로운 텍스트 입력을 위해 에디터 폰트 설정 업데이트
            self.setup_editor_font_insertion()
            
            logger.info(f"현재 폰트 크기 변경: {self.current_font_size}px")
            
        except Exception as e:
            logger.error(f"드롭박스 폰트 크기 변경 오류: {e}")

    def smart_update_font_from_cursor(self):
        """스마트 폰트 크기 감지 - 텍스트 선택 중이 아닐 때만 드롭박스 업데이트"""
        try:
            cursor = self.content_editor.textCursor()
            
            # 텍스트가 선택되어 있으면 드롭박스 업데이트하지 않음 (드래그 방해 방지)
            if cursor.hasSelection():
                return
                
            char_format = cursor.charFormat()
            
            # 현재 위치의 폰트 크기 확인
            current_size = int(char_format.fontPointSize()) if char_format.fontPointSize() > 0 else 11
            
            # UI 표시용 폰트 크기에 따라 드롭박스 선택 업데이트
            if current_size >= 20:
                self.font_size_combo.setCurrentIndex(0)  # UI 대제목 (20px)
                self.current_font_size = '20'
            elif current_size >= 15:
                self.font_size_combo.setCurrentIndex(1)  # UI 소제목 (15px)
                self.current_font_size = '15'
            elif current_size >= 12:
                self.font_size_combo.setCurrentIndex(2)  # UI 강조 (12px)
                self.current_font_size = '12'
            else:
                self.font_size_combo.setCurrentIndex(3)  # UI 일반 (11px)
                self.current_font_size = '11'
                
        except Exception as e:
            logger.error(f"스마트 폰트 크기 감지 오류: {e}")

    def update_current_font_from_cursor(self):
        """커서 위치의 폰트 크기를 감지하여 드롭박스 업데이트 (기존 메서드 유지)"""
        try:
            cursor = self.content_editor.textCursor()
            char_format = cursor.charFormat()
            
            # 현재 위치의 폰트 크기 확인
            current_size = int(char_format.fontPointSize()) if char_format.fontPointSize() > 0 else 15
            
            # 폰트 크기에 따라 드롭박스 선택 업데이트
            if current_size >= 24:
                self.font_size_combo.setCurrentIndex(0)  # 대제목 (24px)
                self.current_font_size = '24'
            elif current_size >= 19:
                self.font_size_combo.setCurrentIndex(1)  # 소제목 (19px)
                self.current_font_size = '19'
            elif current_size >= 16:
                self.font_size_combo.setCurrentIndex(2)  # 강조 (16px)
                self.current_font_size = '16'
            else:
                self.font_size_combo.setCurrentIndex(3)  # 일반 (15px)
                self.current_font_size = '15'
                
        except Exception as e:
            logger.error(f"커서 폰트 크기 감지 오류: {e}")

    def setup_editor_font_insertion(self):
        """에디터에서 새 텍스트 입력 시 현재 선택된 폰트로 입력되도록 설정"""
        try:
            from PySide6.QtGui import QTextCharFormat, QFont
            
            cursor = self.content_editor.textCursor()
            char_format = QTextCharFormat()
            
            # 현재 선택된 폰트 크기 적용
            font_size = int(self.current_font_size)
            char_format.setFontPointSize(font_size)
            
            # 폰트 두께도 함께 설정 (UI 표시용 크기 기준)
            if font_size == 20:  # UI 대제목 (발행시 24px)
                char_format.setFontWeight(QFont.DemiBold)  # font-weight: 600
            elif font_size == 15:  # UI 소제목 (발행시 19px)
                char_format.setFontWeight(QFont.DemiBold)  # font-weight: 600
            elif font_size == 12:  # UI 강조 (발행시 16px)
                char_format.setFontWeight(QFont.DemiBold)  # font-weight: 600
            else:  # UI 일반 (11px, 발행시 15px)
                char_format.setFontWeight(QFont.Normal)  # font-weight: 400
            
            cursor.setCharFormat(char_format)
            
            # 커서를 에디터에 다시 설정
            self.content_editor.setTextCursor(cursor)
            
        except Exception as e:
            logger.error(f"에디터 폰트 설정 오류: {e}")

    def restore_original_content(self):
        """원본 내용으로 복원 - QTextCharFormat 방식"""
        try:
            original_content = self.step2_data.get('generated_content', '')
            # 원본 내용을 QTextCharFormat 방식으로 복원
            self.auto_format_for_mobile(original_content)  # 이미 QTextCharFormat 방식으로 에디터에 직접 적용됨
            logger.info("원본 내용으로 복원됨 (QTextCharFormat 방식)")
            
            TableUIDialogHelper.show_info_dialog(
                self, "복원 완료", "AI가 생성한 원본 내용으로 복원되었습니다.", "🔄"
            )
        except Exception as e:
            logger.error(f"원본 복원 오류: {e}")

    def copy_content_to_clipboard(self):
        """편집기 내용을 클립보드에 복사 (테이블 구조 보존)"""
        try:
            from PySide6.QtWidgets import QApplication
            import re
            
            # HTML 내용과 일반 텍스트 내용 모두 가져오기
            html_content = self.content_editor.toHtml()
            plain_content = self.content_editor.toPlainText().strip()
            
            if not plain_content:
                TableUIDialogHelper.show_error_dialog(
                    self, "내용 없음", "복사할 내용이 없습니다."
                )
                return
            
            # 테이블이 포함된 경우 구조화된 텍스트로 변환
            formatted_content = self.convert_html_tables_to_readable_text(html_content, plain_content)
            
            # 클립보드에 복사
            clipboard = QApplication.clipboard()
            clipboard.setText(formatted_content)
            
            # 편집기와 동일한 방식으로 글자수 계산 (원본 텍스트 기준)
            char_count = len(plain_content.replace(' ', '').replace('\n', ''))
            
            logger.info(f"클립보드 복사 완료 ({len(formatted_content):,}자)")
            
            TableUIDialogHelper.show_info_dialog(
                self, "복사 완료", 
                f"편집된 내용이 클립보드에 복사되었습니다.\n"
                f"글자 수: {char_count:,}자", 
                "📋"
            )
            
        except Exception as e:
            logger.error(f"클립보드 복사 오류: {e}")
            TableUIDialogHelper.show_error_dialog(
                self, "복사 오류", f"클립보드 복사 중 오류가 발생했습니다:\n{e}"
            )

    def convert_html_tables_to_readable_text(self, html_content: str, plain_content: str) -> str:
        """HTML 테이블을 읽기 쉬운 텍스트 형태로 변환"""
        try:
            import re
            from html import unescape
            
            # HTML에 테이블이 없으면 일반 텍스트 반환
            if "<table" not in html_content:
                return plain_content
            
            logger.info("HTML 테이블을 텍스트로 변환 시작")
            
            # HTML 테이블 추출 및 변환
            table_pattern = r'<table[^>]*>(.*?)</table>'
            tables = re.findall(table_pattern, html_content, re.DOTALL | re.IGNORECASE)
            
            if not tables:
                return plain_content
            
            # 원본 HTML을 기반으로 테이블별로 변환
            result_content = html_content
            
            for table_html in tables:
                # 테이블을 읽기 쉬운 텍스트로 변환
                readable_table = self.parse_html_table_to_text(f"<table>{table_html}</table>")
                
                # 원본 테이블을 변환된 텍스트로 교체
                original_table = f"<table[^>]*>{re.escape(table_html)}</table>"
                result_content = re.sub(original_table, readable_table, result_content, flags=re.DOTALL | re.IGNORECASE)
            
            # HTML 태그 제거하고 텍스트만 추출
            # <p>, <div>, <br> 등은 줄바꿈으로 변환
            result_content = re.sub(r'<(p|div|br)[^>]*>', '\n', result_content, flags=re.IGNORECASE)
            result_content = re.sub(r'</(p|div)>', '\n', result_content, flags=re.IGNORECASE)
            
            # 나머지 HTML 태그 제거
            result_content = re.sub(r'<[^>]+>', '', result_content)
            
            # HTML 엔티티 디코딩
            result_content = unescape(result_content)
            
            # 연속된 줄바꿈 정리 (3개 이상의 줄바꿈을 2개로)
            result_content = re.sub(r'\n{3,}', '\n\n', result_content)
            
            # 앞뒤 공백 제거
            result_content = result_content.strip()
            
            logger.info(f"HTML 테이블 변환 완료: {len(tables)}개 테이블 처리됨")
            return result_content
            
        except Exception as e:
            logger.error(f"HTML 테이블 변환 오류: {e}")
            # 오류 시 원본 텍스트 반환
            return plain_content
    
    def parse_html_table_to_text(self, table_html: str) -> str:
        """개별 HTML 테이블을 마크다운 테이블 형태로 변환"""
        try:
            import re
            from html import unescape
            
            # 행 추출
            row_pattern = r'<tr[^>]*>(.*?)</tr>'
            rows = re.findall(row_pattern, table_html, re.DOTALL | re.IGNORECASE)
            
            if not rows:
                return ""
            
            text_rows = []
            
            # 각 행의 셀 데이터 추출
            for row_html in rows:
                cell_pattern = r'<t[dh][^>]*>(.*?)</t[dh]>'
                cells = re.findall(cell_pattern, row_html, re.DOTALL | re.IGNORECASE)
                
                # HTML 태그 제거 및 엔티티 디코딩
                clean_cells = []
                for cell in cells:
                    clean_cell = re.sub(r'<[^>]+>', '', cell)
                    clean_cell = unescape(clean_cell).strip()
                    # 마크다운 파이프 문자 이스케이프
                    clean_cell = clean_cell.replace('|', '\\|')
                    clean_cells.append(clean_cell)
                
                text_rows.append(clean_cells)
            
            if not text_rows:
                return ""
            
            # 마크다운 테이블 생성
            result_lines = []
            
            # 첫 번째 행(헤더)
            if text_rows:
                header_row = "| " + " | ".join(text_rows[0]) + " |"
                result_lines.append(header_row)
                
                # 구분선 (열 개수만큼 생성)
                separator = "|" + "|".join("------" for _ in text_rows[0]) + "|"
                result_lines.append(separator)
                
                # 나머지 행들(데이터)
                for row in text_rows[1:]:
                    # 헤더와 열 개수 맞추기
                    while len(row) < len(text_rows[0]):
                        row.append("")
                    
                    data_row = "| " + " | ".join(row[:len(text_rows[0])]) + " |"
                    result_lines.append(data_row)
            
            return "\n".join(result_lines)
            
        except Exception as e:
            logger.error(f"HTML 테이블 파싱 오류: {e}")
            return ""

    def create_publish_card(self) -> ModernCard:
        """발행 카드"""
        card = ModernCard("🚀 네이버 블로그 발행")
        layout = QVBoxLayout()
        layout.setSpacing(tokens.GAP_12)

        # 발행 안내 (간결하게)
        info_label = QLabel("완성된 글을 네이버 블로그에 자동 발행합니다.")
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
        # HTML 모드에서 실제 텍스트 내용 추출
        current_content = self.content_editor.toPlainText() if hasattr(self, 'content_editor') else self.step2_data.get('generated_content', '')
        return {
            'publish_ready': True,
            'title': self.step1_data.get('selected_title', ''),
            'content': current_content,
            'html_content': self.content_editor.toHtml() if hasattr(self, 'content_editor') else '',  # HTML 버전도 저장
            'content_length': len(current_content.replace(' ', '').replace('\n', '')),
            'content_edited': self.step2_data.get('content_edited', False),
            'original_content': self.step2_data.get('generated_content', '')
        }