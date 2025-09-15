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
        tone = ai_settings.get('tone', '정중한 존댓말체')

        blog_count = self.step2_data.get('blog_count', 0)
        generated_content = self.step2_data.get('generated_content', '')
        content_length = len(generated_content.replace(' ', '')) if generated_content else 0
        
        # 이미지 태그 개수 계산
        image_count = generated_content.count('(이미지)') if generated_content else 0

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
            "대제목 (24px)",    # 네이버 24px
            "소제목 (19px)",    # 네이버 19px  
            "강조 (16px)",      # 네이버 16px
            "일반 (15px)"       # 네이버 15px
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
        
        # 적용 버튼 (선택한 텍스트에 폰트 적용)
        self.apply_font_btn = ModernButton("🎨 선택 텍스트에 적용")
        self.apply_font_btn.clicked.connect(self.apply_font_to_selection)
        tools_layout.addWidget(self.apply_font_btn)
        
        tools_layout.addStretch()
        layout.addLayout(tools_layout)
        
        # 현재 폰트 크기 추적 (새 텍스트 입력용)
        self.current_font_size = '15'  # 기본값: 일반 (15px)

        # 텍스트 에디터 (스크롤 가능)
        self.content_editor = QTextEdit()
        
        # 원본 내용을 모바일 최적화 형태로 자동 변환
        original_content = self.step2_data.get('generated_content', '')
        formatted_content = self.auto_format_for_mobile(original_content)
        
        # HTML 컨텐츠 설정 (마크다운 폰트 적용을 위해)
        self.content_editor.setHtml(formatted_content)
        self.content_editor.setMinimumHeight(tokens.spx(400))
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
        
        # 커서 위치 변경 시 현재 폰트 크기 감지
        self.content_editor.cursorPositionChanged.connect(self.update_current_font_from_cursor)

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

    def auto_format_for_mobile(self, content: str) -> str:
        """원본 글을 모바일 최적화 형태로 자동 변환 + 마크다운 폰트 적용"""
        try:
            if not content:
                return content
            
            # 기본 줄바꿈으로 분리
            lines = content.split('\n')
            formatted_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    formatted_lines.append('')  # 빈 줄 유지
                    continue
                    
                # 한 줄이 너무 길면 모바일 최적화 길이로 분리 (25~28자 기준)
                if len(line) > 30:  # 30자 이상이면 분리 검토
                    sentences = self.split_for_mobile_korean(line)
                    formatted_lines.extend(sentences)
                else:
                    formatted_lines.append(line)
            
            # 연속된 빈 줄 제거 (최대 1개만 유지)
            result_lines = []
            prev_empty = False
            
            for line in formatted_lines:
                if line.strip() == '':
                    if not prev_empty:
                        result_lines.append('')
                        prev_empty = True
                else:
                    result_lines.append(line)
                    prev_empty = False
            
            # 마크다운 폰트 적용 HTML 변환
            formatted_content = self.apply_markdown_fonts('\n'.join(result_lines))
            logger.info(f"모바일 최적화 + 마크다운 폰트 적용 완료: 원본 {len(content)}자 → 변환 {len(formatted_content)}자")
            return formatted_content
            
        except Exception as e:
            logger.error(f"모바일 최적화 오류: {e}")
            return content  # 오류 시 원본 반환

    def apply_markdown_fonts(self, content: str) -> str:
        """마크다운 기반 폰트 크기 적용 + 네이버 블로그 자동화 준비 (HTML 변환)"""
        try:
            import re
            
            html_lines = []
            lines = content.split('\n')
            
            # 표 처리를 위한 상태 변수
            in_table = False
            table_lines = []
            
            i = 0
            while i < len(lines):
                line = lines[i]
                
                if not line.strip():
                    if in_table:
                        # 표가 끝났으면 처리
                        html_lines.append(self.convert_markdown_table_to_naver_format(table_lines))
                        table_lines = []
                        in_table = False
                    html_lines.append('<br>')
                    i += 1
                    continue
                
                # 마크다운 표 감지
                if line.strip().startswith('|') and line.strip().endswith('|') and line.strip().count('|') >= 3:
                    if not in_table:
                        in_table = True
                    table_lines.append(line)
                    i += 1
                    continue
                
                # 표가 진행 중이었는데 표가 아닌 라인을 만나면 표 처리
                if in_table:
                    html_lines.append(self.convert_markdown_table_to_naver_format(table_lines))
                    table_lines = []
                    in_table = False
                
                # ## 대제목 - 24px
                if line.strip().startswith('## '):
                    title_text = line.strip()[3:].strip()  # ## 제거
                    html_lines.append(f'<div data-naver-font="24" style="font-size: 24px; font-weight: 700; margin: 8px 0; color: {ModernStyle.COLORS["text_primary"]};">{title_text}</div>')
                    i += 1
                    continue
                
                # ### 소제목 - 19px
                elif line.strip().startswith('### '):
                    subtitle_text = line.strip()[4:].strip()  # ### 제거
                    html_lines.append(f'<div data-naver-font="19" style="font-size: 19px; font-weight: 600; margin: 6px 0; color: {ModernStyle.COLORS["text_primary"]};">{subtitle_text}</div>')
                    i += 1
                    continue
                
                # 일반 라인에서 **강조** 처리 - 16px
                else:
                    # **텍스트** 패턴 찾기
                    processed_line = re.sub(
                        r'\*\*(.*?)\*\*',
                        lambda m: f'<span data-naver-font="16" style="font-size: 16px; font-weight: 600; color: {ModernStyle.COLORS["text_primary"]};">{m.group(1)}</span>',
                        line
                    )
                    
                    # 일반 텍스트 - 15px
                    html_lines.append(f'<div data-naver-font="15" style="font-size: 15px; font-weight: 400; line-height: 1.6; margin: 2px 0; color: {ModernStyle.COLORS["text_primary"]};">{processed_line}</div>')
                
                i += 1
            
            # 마지막에 표가 남아있다면 처리
            if in_table and table_lines:
                html_lines.append(self.convert_markdown_table_to_naver_format(table_lines))
            
            return '\n'.join(html_lines)
            
        except Exception as e:
            logger.error(f"마크다운 폰트 적용 오류: {e}")
            return content

    def convert_markdown_table_to_naver_format(self, table_lines: list) -> str:
        """마크다운 표를 네이버 블로그 자동화 형식으로 변환"""
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
            
            # 네이버 블로그 자동화를 위한 데이터 구조 생성
            html_parts = []
            html_parts.append(f'<div class="naver-auto-table" data-table-rows="{rows}" data-table-cols="{cols}">')
            
            # 시각적 표 표시 (Step 3 에디터용)
            html_parts.append('<table style="border-collapse: collapse; width: 100%; margin: 10px 0; border: 1px solid #ddd;">')
            
            for row_idx, row_data in enumerate(table_data):
                # 헤더 행 스타일
                if row_idx == 0:
                    html_parts.append('<tr style="background-color: #f8f9fa;">')
                else:
                    html_parts.append('<tr>')
                
                for col_idx, cell_data in enumerate(row_data):
                    # 자동화 데이터 속성 추가
                    cell_html = f'<td data-row="{row_idx}" data-col="{col_idx}" data-naver-font="15" style="border: 1px solid #ddd; padding: 12px; text-align: center;">{cell_data}</td>'
                    html_parts.append(cell_html)
                
                html_parts.append('</tr>')
            
            html_parts.append('</table>')
            html_parts.append('</div>')
            
            logger.info(f"표 변환 완료: {rows}행 × {cols}열")
            return ''.join(html_parts)
            
        except Exception as e:
            logger.error(f"표 변환 오류: {e}")
            # 실패 시 원본 마크다운 표 반환
            return '\n'.join(table_lines)

    def split_for_mobile_korean(self, line: str) -> list:
        """한국어 텍스트를 모바일 최적화 길이(25~28자)로 분리"""
        try:
            if len(line) <= 28:
                return [line]
            
            # 구조화된 콘텐츠는 분리하지 않음
            if self.is_structured_content(line):
                return [line]
                
            result = []
            current = line
            
            # 1순위: 문장 끝 기호로 분리 (. ! ? 등)
            sentence_endings = ['. ', '! ', '? ', '.', '!', '?']
            for ending in sentence_endings:
                if ending in current:
                    parts = current.split(ending)
                    if len(parts) > 1:
                        temp_result = []
                        for i, part in enumerate(parts[:-1]):
                            sentence = part.strip() + ending
                            if len(sentence) <= 28:
                                temp_result.append(sentence)
                            else:
                                # 문장이 너무 길면 재귀적으로 분리
                                temp_result.extend(self.split_by_natural_breaks(sentence, 25))
                        
                        if parts[-1].strip():  # 마지막 부분
                            last_part = parts[-1].strip()
                            if len(last_part) <= 28:
                                temp_result.append(last_part)
                            else:
                                temp_result.extend(self.split_by_natural_breaks(last_part, 25))
                        
                        if len(temp_result) > 1:
                            return temp_result
            
            # 2순위: 자연스러운 구분점으로 분리
            return self.split_by_natural_breaks(current, 25)
            
        except Exception as e:
            logger.error(f"한국어 모바일 분리 오류: {e}")
            return [line]

    def split_by_natural_breaks(self, text: str, target_length: int) -> list:
        """자연스러운 구분점을 찾아서 텍스트 분리"""
        if len(text) <= target_length + 3:  # 여유분 3자
            return [text]
        
        result = []
        current = text
        
        while len(current) > target_length + 3:
            # 자연스러운 분리점 찾기 (우선순위 순)
            break_points = [
                ', ',      # 쉼표
                ' + ',     # 덧셈 (기존 사료 75% + 새 사료 25%)
                ' - ',     # 뺄셈 (100g - 20g)
                ' × ',     # 곱셈 (3 × 5)
                ' ÷ ',     # 나눗셈 (10 ÷ 2)
                ' = ',     # 등호 (A = B)
                ' ≠ ',     # 부등호 (A ≠ B)
                ' > ',     # 크다 (10 > 5)
                ' < ',     # 작다 (5 < 10)
                ' ≥ ',     # 크거나 같다 (A ≥ B)
                ' ≤ ',     # 작거나 같다 (A ≤ B)
                ' ± ',     # 플러스마이너스 (10 ± 2)
                '% ',      # 퍼센트 뒤 (20% 이상)
                '℃ ',     # 섭씨 (25℃ 이상)
                '° ',      # 도 (90° 각도)
                '는 ',     # 조사
                '을 ', '를 ',  # 목적격 조사  
                '이 ', '가 ',  # 주격 조사
                '에 ', '에서 ', '으로 ', '로 ',  # 부사격 조사
                '와 ', '과 ', '하고 ',  # 접속 조사
                '입니다 ', '습니다 ', '합니다 ',  # 존댓말 어미
                '있습니다 ', '없습니다 ',
                '됩니다 ', '됐습니다 ',
                '한다 ', '한다는 ', '하는 ',  # 관형사형
                '하지만 ', '그러나 ', '또한 ', '그리고 ',  # 접속사
                ' 때문에 ', ' 덕분에 ', ' 위해 ',
                ' 등 ', ' 및 ', ' 또는 ',
            ]
            
            found_break = False
            
            # target_length 근처에서 적절한 분리점 찾기
            for break_point in break_points:
                # target_length-5 ~ target_length+8 범위에서 찾기
                start_search = max(target_length - 5, 15)  # 최소 15자
                end_search = min(target_length + 8, len(current))
                
                search_area = current[start_search:end_search]
                if break_point in search_area:
                    break_index = current.find(break_point, start_search)
                    if break_index != -1:
                        split_point = break_index + len(break_point)
                        result.append(current[:split_point].strip())
                        current = current[split_point:].strip()
                        found_break = True
                        break
            
            if not found_break:
                # 자연스러운 분리점을 못 찾으면 공백 기준으로 분리
                words = current[:target_length + 5].split(' ')
                if len(words) > 1:
                    # 마지막 단어를 제외하고 분리 (단어가 잘리지 않게)
                    split_text = ' '.join(words[:-1])
                    if split_text.strip():
                        result.append(split_text.strip())
                        remaining_words = words[-1:] + current[target_length + 5:].split(' ')
                        current = ' '.join(remaining_words).strip()
                    else:
                        # 단어가 너무 길어서 분리가 안 되는 경우 강제 분리
                        result.append(current[:target_length])
                        current = current[target_length:].strip()
                else:
                    # 공백이 없는 긴 단어는 강제 분리
                    result.append(current[:target_length])
                    current = current[target_length:].strip()
        
        if current.strip():
            result.append(current.strip())
        
        return result

    def is_structured_content(self, line: str) -> bool:
        """구조화된 콘텐츠인지 판별 (리스트, 단계별 설명 등)"""
        try:
            line_strip = line.strip()
            
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
            # 네이버 폰트 크기 직접 사용 (표시용도 동일하게)
            font_sizes = ['24', '19', '16', '15']  # 대제목, 소제목, 강조, 일반
            
            self.current_font_size = font_sizes[index]
            
            # 새로운 텍스트 입력을 위해 에디터 폰트 설정 업데이트
            self.setup_editor_font_insertion()
            
            logger.info(f"현재 폰트 크기 변경: {self.current_font_size}px")
            
        except Exception as e:
            logger.error(f"드롭박스 폰트 크기 변경 오류: {e}")

    def apply_font_to_selection(self):
        """선택된 텍스트에 현재 폰트 크기 적용"""
        try:
            cursor = self.content_editor.textCursor()
            if not cursor.hasSelection():
                TableUIDialogHelper.show_info_dialog(
                    self, "텍스트 선택 필요", "폰트를 적용할 텍스트를 먼저 선택해주세요.", "ℹ️"
                )
                return
                
            selected_text = cursor.selectedText()
            
            # HTML 스타일로 감싸기 (마크다운과 동일한 형식 사용)
            if self.current_font_size == '24':  # 대제목
                formatted_text = f'<div data-naver-font="24" style="font-size: 24px; font-weight: 700; margin: 8px 0; color: {ModernStyle.COLORS["text_primary"]};">{selected_text}</div>'
            elif self.current_font_size == '19':  # 소제목
                formatted_text = f'<div data-naver-font="19" style="font-size: 19px; font-weight: 600; margin: 6px 0; color: {ModernStyle.COLORS["text_primary"]};">{selected_text}</div>'
            elif self.current_font_size == '16':  # 강조
                formatted_text = f'<span data-naver-font="16" style="font-size: 16px; font-weight: 600; color: {ModernStyle.COLORS["text_primary"]};">{selected_text}</span>'
            else:  # 일반 (15px)
                formatted_text = f'<div data-naver-font="15" style="font-size: 15px; font-weight: 400; line-height: 1.6; margin: 2px 0; color: {ModernStyle.COLORS["text_primary"]};">{selected_text}</div>'
            
            # setHtml() 방식으로 통일 (마크다운과 동일한 방식)
            cursor.removeSelectedText()
            cursor.insertText(f"__TEMP_REPLACE__{selected_text}__TEMP_REPLACE__")
            
            # 전체 HTML 내용 가져와서 임시 마커를 실제 HTML로 교체
            full_html = self.content_editor.toHtml()
            updated_html = full_html.replace(f"__TEMP_REPLACE__{selected_text}__TEMP_REPLACE__", formatted_text)
            self.content_editor.setHtml(updated_html)
            
            logger.info(f"텍스트에 폰트 적용: {self.current_font_size}px")
            
        except Exception as e:
            logger.error(f"텍스트 폰트 적용 오류: {e}")

    def update_current_font_from_cursor(self):
        """커서 위치의 폰트 크기를 감지하여 드롭박스 업데이트"""
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
            from PySide6.QtGui import QTextCharFormat
            
            cursor = self.content_editor.textCursor()
            char_format = QTextCharFormat()
            
            # 현재 선택된 폰트 크기 적용
            char_format.setFontPointSize(int(self.current_font_size))
            cursor.setCharFormat(char_format)
            
            # 커서를 에디터에 다시 설정
            self.content_editor.setTextCursor(cursor)
            
        except Exception as e:
            logger.error(f"에디터 폰트 설정 오류: {e}")

    def restore_original_content(self):
        """원본 내용으로 복원"""
        try:
            original_content = self.step2_data.get('generated_content', '')
            # 원본 내용도 마크다운 폰트 적용하여 복원
            formatted_content = self.auto_format_for_mobile(original_content)
            self.content_editor.setHtml(formatted_content)
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