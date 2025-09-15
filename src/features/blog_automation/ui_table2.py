"""
블로그 자동화 Step 2: 선택된 제목으로 블로그 분석
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QTabWidget, QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit
)
from PySide6.QtCore import Qt, Signal
import traceback

from src.foundation.logging import get_logger
from src.toolbox.ui_kit.components import (
    ModernButton, ModernCard, ModernPrimaryButton, ModernSuccessButton
)
from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
from src.toolbox.ui_kit.modern_style import ModernStyle
from src.toolbox.ui_kit import tokens
from src.foundation.exceptions import BusinessError, ValidationError

logger = get_logger("blog_automation.ui_table2")


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


class BlogAutomationStep2UI(QWidget):
    """Step 2: 선택된 제목으로 블로그 분석"""

    # 시그널 정의
    step_completed = Signal(dict)  # 다음 단계로 데이터 전달
    analysis_progress = Signal(str, int)  # 진행상황 업데이트
    content_generated = Signal(str)  # AI 글 생성 완료

    def __init__(self, step1_data: dict, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.step1_data = step1_data
        self.analyzed_blogs = []
        self.analysis_worker = None
        self.analysis_thread = None
        self.summary_worker = None
        self.summary_thread = None
        self.ai_writer_worker = None
        self.ai_writer_thread = None
        self.generated_content = ""
        self.is_ai_working = False  # AI 작업 중인지 상태 추가

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

        # Step 1 정보 요약 카드
        step1_summary_card = self.create_step1_summary_card()
        main_layout.addWidget(step1_summary_card)

        # AI 글쓰기 시작 버튼 (독립적으로 배치)
        ai_button_layout = self.create_ai_writing_button_section()
        main_layout.addLayout(ai_button_layout)

        # 블로그 글 생성 결과 카드 (탭만 포함)
        generation_results_card = self.create_generation_results_card()
        main_layout.addWidget(generation_results_card)

        # 네비게이션 버튼들
        nav_layout = QHBoxLayout()

        # 이전 단계 버튼
        self.prev_step_btn = ModernButton("⬅️ 1단계로 돌아가기")
        self.prev_step_btn.clicked.connect(self.on_prev_step_clicked)
        nav_layout.addWidget(self.prev_step_btn)

        nav_layout.addStretch()


        # 다음 단계 버튼
        self.next_step_btn = ModernSuccessButton("➡️ 3단계: 블로그 발행으로 진행")
        self.next_step_btn.clicked.connect(self.on_next_step_clicked)
        self.next_step_btn.setEnabled(False)  # AI 글 생성 완료 후 활성화
        nav_layout.addWidget(self.next_step_btn)

        main_layout.addLayout(nav_layout)

        self.setLayout(main_layout)

    def create_step_header(self) -> QWidget:
        """Step 헤더 생성"""
        header_widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, tokens.GAP_8)

        step_label = QLabel("🤖 Step 2: 블로그 분석 & AI 글 생성")
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

    def create_step1_summary_card(self) -> ModernCard:
        """Step 1 정보 요약 카드"""
        card = ModernCard("📋 선택된 설정 정보")
        layout = QVBoxLayout()
        layout.setSpacing(tokens.GAP_8)

        # Step 1 데이터 표시
        selected_title = self.step1_data.get('selected_title', '제목 없음')
        main_keyword = self.step1_data.get('main_keyword', '키워드 없음')
        search_query = self.step1_data.get('search_query', main_keyword)  # 검색어 가져오기
        ai_settings = self.step1_data.get('ai_settings', {})
        content_type = ai_settings.get('content_type', '정보/가이드형')

        info_layout = QVBoxLayout()
        info_layout.setSpacing(tokens.GAP_4)

        # 선택된 제목
        title_label = QLabel(f"🎯 선택된 제목: {selected_title}")
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_primary']};
                font-size: {tokens.get_font_size('normal')}px;
                font-weight: 600;
                background-color: {ModernStyle.COLORS['bg_primary']};
                padding: {tokens.spx(8)}px;
                border-radius: {tokens.RADIUS_SM}px;
            }}
        """)
        info_layout.addWidget(title_label)

        # 키워드, 컨텐츠 유형, 말투 스타일 (2번째 줄로 이동)
        tone = ai_settings.get('tone', '정중한 존댓말체')
        details_label = QLabel(f"🔍 메인키워드: {main_keyword}   📝 컨텐츠 유형: {content_type}   💬 말투 스타일: {tone}")
        details_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_secondary']};
                font-size: {tokens.get_font_size('small')}px;
                padding: {tokens.spx(4)}px 0px;
            }}
        """)
        info_layout.addWidget(details_label)

        # 최적화된 검색어 (3번째 줄, 수정 가능)
        search_layout = QHBoxLayout()
        search_layout.setSpacing(tokens.GAP_8)

        search_label = QLabel("🔍 최적화된 검색어:")
        search_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_primary']};
                font-size: {tokens.get_font_size('small')}px;
                font-weight: 500;
                min-width: 120px;
            }}
        """)
        search_layout.addWidget(search_label)

        # 검색어 입력 필드
        self.search_query_input = QLineEdit(search_query)
        self.search_query_input.setStyleSheet(f"""
            QLineEdit {{
                color: {ModernStyle.COLORS['text_primary']};
                font-size: {tokens.get_font_size('small')}px;
                background-color: {ModernStyle.COLORS['bg_card']};
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: {tokens.RADIUS_SM}px;
                padding: {tokens.spx(6)}px;
            }}
            QLineEdit:focus {{
                border: 2px solid {ModernStyle.COLORS['primary']};
            }}
        """)
        search_layout.addWidget(self.search_query_input)

        # 초기화 버튼
        reset_btn = QPushButton("초기화")
        reset_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernStyle.COLORS['bg_secondary']};
                color: {ModernStyle.COLORS['text_secondary']};
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: {tokens.RADIUS_SM}px;
                padding: {tokens.spx(4)}px {tokens.spx(8)}px;
                font-size: {tokens.get_font_size('small')}px;
            }}
            QPushButton:hover {{
                background-color: {ModernStyle.COLORS['bg_primary']};
            }}
        """)
        reset_btn.clicked.connect(lambda: self.search_query_input.setText(search_query))
        search_layout.addWidget(reset_btn)

        # 검색어 레이아웃을 카드 스타일로 감싸기
        search_container = QWidget()
        search_container.setLayout(search_layout)
        search_container.setStyleSheet(f"""
            QWidget {{
                background-color: {ModernStyle.COLORS['bg_muted']};
                border-radius: {tokens.RADIUS_SM}px;
                border-left: 3px solid {ModernStyle.COLORS['primary']};
                padding: {tokens.spx(6)}px;
            }}
        """)
        info_layout.addWidget(search_container)

        layout.addLayout(info_layout)
        card.setLayout(layout)
        return card

    def create_analysis_card(self) -> ModernCard:
        """분석 진행 카드"""
        card = ModernCard("🔍 블로그 분석 진행")
        layout = QVBoxLayout()
        layout.setSpacing(tokens.GAP_12)

        # 설명
        desc_label = QLabel("선택된 제목으로 상위 블로그들을 분석하여 경쟁사 정보를 수집합니다")
        desc_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_secondary']};
                font-size: {tokens.get_font_size('normal')}px;
                padding: {tokens.spx(4)}px 0px;
            }}
        """)
        layout.addWidget(desc_label)

        # 진행률 바
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: {tokens.spx(1)}px solid {ModernStyle.COLORS['border']};
                border-radius: {tokens.RADIUS_SM}px;
                text-align: center;
                font-size: {tokens.get_font_size('small')}px;
                color: {ModernStyle.COLORS['text_primary']};
                background-color: {ModernStyle.COLORS['bg_card']};
                height: {tokens.spx(24)}px;
            }}
            QProgressBar::chunk {{
                background-color: {ModernStyle.COLORS['primary']};
                border-radius: {tokens.RADIUS_SM}px;
            }}
        """)
        layout.addWidget(self.progress_bar)

        # 상태 메시지는 메인 UI 왼쪽 상태창에 통합됨

        # 분석 시작 버튼
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.start_analysis_btn = ModernPrimaryButton("🚀 분석 시작")
        self.start_analysis_btn.clicked.connect(self.on_start_analysis_clicked)
        button_layout.addWidget(self.start_analysis_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        card.setLayout(layout)
        return card

    def create_results_card(self) -> ModernCard:
        """분석 결과 카드"""
        card = ModernCard("📊 분석 결과")
        layout = QVBoxLayout()
        layout.setSpacing(tokens.GAP_8)

        # 결과 요약
        self.results_summary_label = QLabel("아직 분석이 시작되지 않았습니다.")
        self.results_summary_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_secondary']};
                font-size: {tokens.get_font_size('normal')}px;
                padding: {tokens.spx(8)}px;
                background-color: {ModernStyle.COLORS['bg_primary']};
                border-radius: {tokens.RADIUS_SM}px;
            }}
        """)
        layout.addWidget(self.results_summary_label)

        # 분석된 블로그 개수 등 통계 정보는 나중에 동적으로 추가

        card.setLayout(layout)
        return card


    def create_result_tabs(self) -> QTabWidget:
        """결과 탭 위젯 생성 (분석 결과 + 생성된 글)"""
        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: {tokens.spx(1)}px solid {ModernStyle.COLORS['border']};
                background-color: {ModernStyle.COLORS['bg_card']};
                border-radius: {tokens.RADIUS_SM}px;
            }}
            QTabBar::tab {{
                padding: {tokens.spx(8)}px {tokens.spx(16)}px;
                margin-right: {tokens.spx(2)}px;
                background-color: {ModernStyle.COLORS['bg_secondary']};
                border: {tokens.spx(1)}px solid {ModernStyle.COLORS['border']};
                border-bottom: none;
                border-radius: {tokens.RADIUS_SM}px {tokens.RADIUS_SM}px 0px 0px;
            }}
            QTabBar::tab:selected {{
                background-color: {ModernStyle.COLORS['bg_card']};
                color: {ModernStyle.COLORS['primary']};
                font-weight: 600;
            }}
            QTabBar::tab:hover {{
                background-color: {ModernStyle.COLORS['bg_primary']};
            }}
        """)

        # 분석 결과 탭
        self.analysis_result_tab = self.create_analysis_result_tab()
        tabs.addTab(self.analysis_result_tab, "📊 분석 결과")

        # 생성된 글 탭
        self.generated_content_tab = self.create_generated_content_tab()
        tabs.addTab(self.generated_content_tab, "📝 생성된 글")

        return tabs

    def create_analysis_result_tab(self) -> QWidget:
        """분석 결과 탭 생성 (기존 테이블 형태로 복원)"""
        tab = QWidget()
        layout = QVBoxLayout()

        # 테이블 위젯 생성 (8컬럼 구조, 순위 제거)
        self.blog_table = QTableWidget(0, 8)  # 0행 8열 (순위 제거)
        logger.info(f"📊 블로그 테이블 위젯 생성됨: {id(self.blog_table)}")
        self.blog_table.setHorizontalHeaderLabels([
            "제목", "내용", "글자수", "이미지수", "GIF수", "동영상수", "태그", "URL"
        ])

        # 테이블 설정 (원본과 동일)
        header = self.blog_table.horizontalHeader()

        # 고정 너비 설정 (순위 제거로 인덱스 조정)
        self.blog_table.setColumnWidth(0, 250)  # 제목
        self.blog_table.setColumnWidth(1, 350)  # 내용
        self.blog_table.setColumnWidth(2, 80)   # 글자수
        self.blog_table.setColumnWidth(3, 80)   # 이미지수
        self.blog_table.setColumnWidth(4, 70)   # GIF수
        self.blog_table.setColumnWidth(5, 80)   # 동영상수
        self.blog_table.setColumnWidth(6, 350)  # 태그
        self.blog_table.setColumnWidth(7, 200)  # URL

        # 가로 스크롤 활성화 (원본과 동일)
        header.setSectionResizeMode(QHeaderView.Interactive)
        self.blog_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # 행 높이 조정 (내용을 보여주기 위해 더 높게 - 원본과 동일)
        self.blog_table.verticalHeader().setDefaultSectionSize(120)

        # 텍스트 래핑 활성화 (원본과 동일)
        self.blog_table.setWordWrap(True)
        self.blog_table.setAlternatingRowColors(True)
        self.blog_table.setSelectionBehavior(QTableWidget.SelectRows)

        # 스타일 설정 (원본과 동일)
        self.blog_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {ModernStyle.COLORS['bg_card']};
                border: {tokens.spx(1)}px solid {ModernStyle.COLORS['border']};
                border-radius: {tokens.RADIUS_SM}px;
                gridline-color: {ModernStyle.COLORS['border']};
            }}
            QTableWidget::item {{
                padding: {tokens.spx(8)}px;
                border-bottom: {tokens.spx(1)}px solid {ModernStyle.COLORS['border']};
            }}
            QTableWidget::item:selected {{
                background-color: {ModernStyle.COLORS['primary']};
                color: white;
            }}
            QHeaderView::section {{
                background-color: {ModernStyle.COLORS['bg_muted']};
                padding: {tokens.spx(8)}px;
                border: {tokens.spx(1)}px solid {ModernStyle.COLORS['border']};
                font-weight: 600;
            }}
        """)

        layout.addWidget(self.blog_table)
        tab.setLayout(layout)
        return tab

    def populate_blog_table(self, analyzed_blogs):
        """분석된 블로그 데이터를 테이블에 표시 (원본 ui_result.py와 동일)"""
        try:
            logger.info(f"📊 populate_blog_table 호출됨 - 블로그 수: {len(analyzed_blogs)}")

            # 테이블 위젯 존재 확인
            if not hasattr(self, 'blog_table') or self.blog_table is None:
                logger.error(f"❌ blog_table이 없습니다! hasattr: {hasattr(self, 'blog_table')}, value: {getattr(self, 'blog_table', 'NOT_FOUND')}")
                return

            logger.info(f"✅ blog_table 확인됨: {id(self.blog_table)}")

            self.blog_table.setRowCount(len(analyzed_blogs))

            for row, blog in enumerate(analyzed_blogs):
                # 제목 (인덱스 0으로 이동)
                title = blog['title'][:50] + '...' if len(blog['title']) > 50 else blog['title']
                self.blog_table.setItem(row, 0, QTableWidgetItem(title))

                # 내용 (인덱스 1로 이동)
                text_content = blog.get('text_content', '내용 없음')
                if text_content and text_content != '분석 실패':
                    # 내용을 200자로 제한하여 표시
                    display_content = text_content[:200] + '...' if len(text_content) > 200 else text_content
                    # 줄바꿈 처리하여 가독성 향상
                    display_content = display_content.replace('\n', ' ').strip()
                else:
                    display_content = '내용 분석 실패'

                content_item = QTableWidgetItem(display_content)
                content_item.setToolTip(text_content if text_content and text_content != '분석 실패' else '내용 분석 실패')
                content_item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
                self.blog_table.setItem(row, 1, content_item)

                # 글자수 (인덱스 2로 이동)
                self.blog_table.setItem(row, 2, QTableWidgetItem(str(blog['content_length'])))

                # 이미지 수 (인덱스 3으로 이동)
                self.blog_table.setItem(row, 3, QTableWidgetItem(str(blog['image_count'])))

                # GIF 수 (인덱스 4로 이동)
                self.blog_table.setItem(row, 4, QTableWidgetItem(str(blog['gif_count'])))

                # 동영상 수 (인덱스 5로 이동)
                self.blog_table.setItem(row, 5, QTableWidgetItem(str(blog['video_count'])))

                # 태그 (인덱스 6으로 이동)
                tags = blog.get('tags', [])
                if tags:
                    # 태그를 두 줄로 나누어 표시
                    tags_per_line = 3  # 한 줄에 3개씩
                    lines = []
                    for i in range(0, len(tags), tags_per_line):
                        line_tags = tags[i:i+tags_per_line]
                        lines.append(', '.join(line_tags))
                    tags_text = '\n'.join(lines)
                else:
                    tags_text = '태그 없음'

                tag_item = QTableWidgetItem(tags_text)
                tag_item.setToolTip(', '.join(tags) if tags else '태그 없음')
                tag_item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
                self.blog_table.setItem(row, 6, tag_item)

                # URL (인덱스 7로 이동)
                url = blog['url'][:50] + '...' if len(blog['url']) > 50 else blog['url']
                self.blog_table.setItem(row, 7, QTableWidgetItem(url))

            logger.info(f"테이블에 {len(analyzed_blogs)}개 블로그 데이터 표시 완료")

        except Exception as e:
            logger.error(f"테이블 데이터 표시 오류: {e}")

    def create_generated_content_tab(self) -> QWidget:
        """생성된 글 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout()

        # 생성된 글 내용
        self.generated_content_display = QTextEdit()
        self.generated_content_display.setPlaceholderText("AI 글 생성이 완료되면 결과가 여기에 표시됩니다.")
        self.generated_content_display.setReadOnly(True)
        self.generated_content_display.setStyleSheet(f"""
            QTextEdit {{
                border: {tokens.spx(1)}px solid {ModernStyle.COLORS['border']};
                border-radius: {tokens.RADIUS_SM}px;
                background-color: {ModernStyle.COLORS['bg_card']};
                color: {ModernStyle.COLORS['text_primary']};
                font-size: {tokens.get_font_size('normal')}px;
                font-family: 'Segoe UI', Arial, sans-serif;
                padding: {tokens.spx(12)}px;
                line-height: 1.6;
            }}
        """)

        layout.addWidget(self.generated_content_display)
        tab.setLayout(layout)
        return tab


    def on_analysis_started(self):
        """분석 시작 시그널 처리"""
        logger.info("📊 블로그 분석 시작됨")
        
        # 메인 UI 상태창 업데이트
        if hasattr(self.parent, 'update_status'):
            self.parent.update_status("블로그 검색 중...", "progress")

    def on_analysis_progress(self, message: str, progress: int):
        """분석 진행 상황 업데이트"""
        logger.info(f"📝 분석 진행: {message} ({progress}%)")

        # 메인 UI 상태창 업데이트
        if hasattr(self.parent, 'update_status'):
            self.parent.update_status(f"{message} ({progress}%)", "progress")

        # 기존 UI 업데이트 (호환성 유지)
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setValue(progress)

        # 통합 UI 업데이트 - 로그로만 상태 표시
        logger.info(f"1단계: {message} ({progress}%)")

    def on_analysis_completed(self, analyzed_blogs: list):
        """분석 완료 처리"""
        try:
            logger.info(f"✅ 블로그 분석 완료! 분석된 블로그: {len(analyzed_blogs)}개")

            self.analyzed_blogs = analyzed_blogs

            # 기존 UI 업데이트 (호환성 유지)
            if hasattr(self, 'progress_bar'):
                self.progress_bar.setValue(100)
            # Step2 내부 상태는 메인 상태창으로 통합됨

            # 결과 요약 업데이트 (호환성 유지)
            blog_count = len(analyzed_blogs)
            if hasattr(self, 'results_summary_label'):
                self.results_summary_label.setText(
                    f"✅ 분석 완료!\n\n📊 총 {blog_count}개의 블로그를 분석했습니다.\n"
                    f"이제 AI 글 생성 버튼을 클릭하여 최적화된 블로그 글을 작성하세요."
                )

            # 통합 UI 업데이트
            if hasattr(self, 'integrated_result_tabs'):
                logger.info("2단계: 정보요약 AI를 시작합니다...")

                # 분석 결과를 테이블에 표시 (기존 방식 복원)
                try:
                    self.populate_blog_table(analyzed_blogs)
                    logger.info("📊 분석 결과 테이블이 업데이트되었습니다.")
                except AttributeError as e:
                    logger.warning(f"⚠️ 블로그 테이블 접근 오류: {e}")

                # 자동으로 AI 글쓰기 계속 진행
                self.continue_ai_writing()

            # 상태 업데이트 완료
            logger.info("✅ 분석 완료! AI 글쓰기 준비됨")
            self.reset_analysis_ui()

            # 성공 다이얼로그 제거 - 자동으로 다음 단계 진행

        except Exception as e:
            logger.error(f"분석 완료 처리 중 오류: {e}")
            self.reset_analysis_ui()

    def on_analysis_error(self, error_message: str):
        """분석 오류 처리"""
        try:
            logger.error(f"❌ 블로그 분석 오류: {error_message}")

            # Step2 내부 상태는 메인 상태창으로 통합됨
            # 메인 UI 상태창 업데이트 (오류)
            if hasattr(self.parent, 'update_status'):
                self.parent.update_status("분석 중 오류 발생", "error")
                
            # 분석 오류시 전체 작업 중단하므로 통합 UI 리셋
            self.reset_integrated_ui()

            TableUIDialogHelper.show_error_dialog(
                self, "분석 오류", f"블로그 분석 중 오류가 발생했습니다:\n{error_message}"
            )

        except Exception as e:
            logger.error(f"분석 오류 처리 중 오류: {e}")

    def reset_analysis_ui(self):
        """분석 UI 상태 초기화"""
        # 분석 완료 후에는 버튼 상태를 변경하지 않음 (AI 작업이 계속 진행중이므로)
        # 버튼은 글쓰기 AI가 완료되거나 오류 발생시에만 활성화
        pass


    def on_prev_step_clicked(self):
        """이전 단계로 돌아가기"""
        try:
            logger.info("1단계로 돌아가기")
            # TODO: Step 1으로 돌아가는 로직 구현 (메인 UI에서 처리)
            if hasattr(self.parent, 'load_step'):
                self.parent.load_step(1)

        except Exception as e:
            logger.error(f"이전 단계 이동 오류: {e}")

    def on_next_step_clicked(self):
        """다음 단계로 진행"""
        try:
            if not self.analyzed_blogs:
                TableUIDialogHelper.show_error_dialog(
                    self, "분석 필요", "먼저 블로그 분석을 완료해주세요."
                )
                return

            if not self.generated_content:
                TableUIDialogHelper.show_error_dialog(
                    self, "글 생성 필요", "먼저 AI 블로그 글 생성을 완료해주세요."
                )
                return

            # Step 2 완료 데이터 준비
            step2_data = {
                'analyzed_blogs': self.analyzed_blogs,
                'analysis_completed': True,
                'blog_count': len(self.analyzed_blogs),
                'generated_content': self.generated_content,
                'content_generated': True
            }

            logger.info(f"Step 2 완료, 분석: {len(self.analyzed_blogs)}개, 글 생성: {len(self.generated_content)}자")

            # 다음 단계로 데이터 전달
            self.step_completed.emit(step2_data)

        except Exception as e:
            logger.error(f"다음 단계 진행 오류: {e}")
            TableUIDialogHelper.show_error_dialog(
                self, "오류", f"다음 단계로 진행 중 오류가 발생했습니다:\n{e}"
            )

    def get_step2_data(self) -> dict:
        """Step 2 데이터 반환"""
        return {
            'analyzed_blogs': self.analyzed_blogs,
            'analysis_completed': bool(self.analyzed_blogs),
            'blog_count': len(self.analyzed_blogs)
        }

    def update_step1_data(self, new_step1_data: dict):
        """Step1 데이터 업데이트 (검색어 입력 필드 등 UI 갱신)"""
        try:
            logger.info("Step1 데이터 업데이트 중...")
            
            # 기존 데이터 업데이트
            self.step1_data = new_step1_data
            
            # UI 업데이트 - 검색어 입력 필드
            search_query = self.step1_data.get('search_query', '')
            if hasattr(self, 'search_query_input'):
                self.search_query_input.setText(search_query)
                logger.info(f"검색어 입력 필드 업데이트: '{search_query}'")
            
            # 선택된 제목 정보 업데이트 (Step1 요약 카드)
            selected_title = self.step1_data.get('selected_title', '제목 없음')
            main_keyword = self.step1_data.get('main_keyword', '키워드 없음')
            ai_settings = self.step1_data.get('ai_settings', {})
            content_type = ai_settings.get('content_type', '정보/가이드형')
            tone = ai_settings.get('tone', '정중한 존댓말체')
            
            logger.info(f"Step1 정보 업데이트 - 제목: {selected_title[:30]}..., 키워드: {main_keyword}, 유형: {content_type}")
            
        except Exception as e:
            logger.error(f"Step1 데이터 업데이트 오류: {e}")

    def create_ai_writing_button_section(self) -> QVBoxLayout:
        """AI 글쓰기 버튼 섹션 (독립적으로 배치)"""
        section_layout = QVBoxLayout()
        section_layout.setSpacing(tokens.GAP_12)

        # 설명
        desc_label = QLabel("최적화된 검색어로 상위블로그를 분석해 선택된 제목에 맞는 글을 작성합니다")
        desc_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_secondary']};
                font-size: {tokens.get_font_size('normal')}px;
                padding: {tokens.spx(4)}px 0px;
                text-align: center;
            }}
        """)
        section_layout.addWidget(desc_label)

        # AI 글쓰기 시작 버튼
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.start_ai_writing_btn = ModernPrimaryButton("🚀 AI 글쓰기 시작")
        self.start_ai_writing_btn.clicked.connect(self.on_start_ai_writing_clicked)
        button_layout.addWidget(self.start_ai_writing_btn)

        button_layout.addStretch()
        section_layout.addLayout(button_layout)

        return section_layout

    def create_generation_results_card(self) -> ModernCard:
        """블로그 글 생성 결과 카드 (탭만 포함, 미리 생성)"""
        card = ModernCard("📝 블로그 글 생성 결과")
        layout = QVBoxLayout()
        layout.setSpacing(tokens.GAP_8)

        # 결과 탭들 (미리 모두 생성)
        self.integrated_result_tabs = self.create_integrated_result_tabs()
        layout.addWidget(self.integrated_result_tabs)

        card.setLayout(layout)
        return card

    def create_integrated_result_tabs(self) -> QTabWidget:
        """통합 결과 탭 위젯 생성"""
        logger.info("🎯 create_integrated_result_tabs 시작")
        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: {tokens.spx(1)}px solid {ModernStyle.COLORS['border']};
                background-color: {ModernStyle.COLORS['bg_card']};
                border-radius: {tokens.RADIUS_SM}px;
            }}
            QTabBar::tab {{
                padding: {tokens.spx(8)}px {tokens.spx(16)}px;
                margin-right: {tokens.spx(2)}px;
                background-color: {ModernStyle.COLORS['bg_secondary']};
                border: {tokens.spx(1)}px solid {ModernStyle.COLORS['border']};
                border-bottom: none;
                border-radius: {tokens.RADIUS_SM}px {tokens.RADIUS_SM}px 0px 0px;
                font-size: {tokens.get_font_size('small')}px;
            }}
            QTabBar::tab:selected {{
                background-color: {ModernStyle.COLORS['bg_card']};
                color: {ModernStyle.COLORS['primary']};
                font-weight: 600;
            }}
            QTabBar::tab:hover {{
                background-color: {ModernStyle.COLORS['bg_primary']};
            }}
        """)

        # 1. 블로그 분석 결과 탭 (테이블 위젯 생성)
        logger.info("🎯 create_analysis_result_tab 호출 전")
        self.tab1_analysis = self.create_analysis_result_tab()
        logger.info(f"🎯 create_analysis_result_tab 호출 후, blog_table 존재 여부: {hasattr(self, 'blog_table')}")
        tabs.addTab(self.tab1_analysis, "📊 블로그 분석 결과")

        # 2. 정보요약 프롬프트 탭
        self.tab2_summary_prompt = QTextEdit()
        self.tab2_summary_prompt.setPlaceholderText("정보요약 AI에게 보낼 프롬프트가 표시됩니다.")
        self.tab2_summary_prompt.setReadOnly(True)
        self.tab2_summary_prompt.setStyleSheet(self.get_text_edit_style())
        tabs.addTab(self.tab2_summary_prompt, "📝 정보요약 프롬프트")

        # 3. 정보요약 AI 답변 탭
        self.tab3_summary_response = QTextEdit()
        self.tab3_summary_response.setPlaceholderText("정보요약 AI의 답변이 표시됩니다.")
        self.tab3_summary_response.setReadOnly(True)
        self.tab3_summary_response.setStyleSheet(self.get_text_edit_style())
        tabs.addTab(self.tab3_summary_response, "🤖 정보요약 AI 답변")

        # 4. 글쓰기 AI 프롬프트 탭
        self.tab4_writing_prompt = QTextEdit()
        self.tab4_writing_prompt.setPlaceholderText("글쓰기 AI에게 보낼 프롬프트가 표시됩니다.")
        self.tab4_writing_prompt.setReadOnly(True)
        self.tab4_writing_prompt.setStyleSheet(self.get_text_edit_style())
        tabs.addTab(self.tab4_writing_prompt, "✍️ 글쓰기 AI 프롬프트")

        # 5. 글쓰기 AI 답변 탭
        self.tab5_writing_response = QTextEdit()
        self.tab5_writing_response.setPlaceholderText("글쓰기 AI가 생성한 최종 블로그 글이 표시됩니다.")
        self.tab5_writing_response.setReadOnly(True)
        self.tab5_writing_response.setStyleSheet(self.get_text_edit_style())
        tabs.addTab(self.tab5_writing_response, "📖 글쓰기 AI 답변")

        return tabs

    def get_text_edit_style(self) -> str:
        """TextEdit 공용 스타일"""
        return f"""
            QTextEdit {{
                border: {tokens.spx(1)}px solid {ModernStyle.COLORS['border']};
                border-radius: {tokens.RADIUS_SM}px;
                background-color: {ModernStyle.COLORS['bg_card']};
                color: {ModernStyle.COLORS['text_primary']};
                font-size: {tokens.get_font_size('normal')}px;
                padding: {tokens.spx(8)}px;
                line-height: 1.5;
            }}
        """

    def on_start_ai_writing_clicked(self):
        """AI 글쓰기 시작/정지 버튼 클릭"""
        try:
            # 현재 AI 작업 중이면 정지
            if self.is_ai_working:
                self.stop_ai_writing()
                return
                
            logger.info("🚀 통합 AI 글쓰기 시작")

            # 메인 UI 상태창 업데이트
            if hasattr(self.parent, 'update_status'):
                self.parent.update_status("AI 글쓰기 준비 중...", "progress")

            # AI 작업 시작 상태로 변경
            self.is_ai_working = True
            
            # 버튼 상태 변경 (정지 버튼으로)
            self.start_ai_writing_btn.setText("🛑 정지")
            self.start_ai_writing_btn.setEnabled(True)  # 정지 버튼은 활성 상태 유지

            # 분석 시작 (사용자가 수정한 검색어 사용)
            selected_title = self.step1_data.get('selected_title', '')
            # 사용자가 수정한 검색어를 search_keyword로 사용
            search_keyword = self.search_query_input.text().strip()

            if not search_keyword:
                # 입력이 비어있으면 기본 검색어 사용
                search_keyword = self.step1_data.get('search_query', selected_title)

            if not search_keyword:
                raise Exception("검색할 키워드가 없습니다.")

            # 로그용으로만 원래 검색어 저장
            original_query = self.step1_data.get('search_query', selected_title)

            # 검색어 정보 로그
            if search_keyword != original_query:
                logger.info(f"🎯 제목: {selected_title}")
                logger.info(f"🔍 AI 추천 검색어: {original_query}")
                logger.info(f"✏️  사용자 수정 검색어: {search_keyword}")
            else:
                logger.info(f"🎯 제목: {selected_title}")
                logger.info(f"🔍 검색어: {search_keyword}")

            logger.info(f"🚀 통합 AI 글쓰기 - 워커에게 전달할 키워드: {search_keyword}")

            # AI 기반 워커 생성 및 시작 (추가 파라미터 수집)
            from .worker import create_ai_blog_analysis_worker, WorkerThread

            # AI 설정 정보 수집
            main_keyword = self.step1_data.get('main_keyword', selected_title)
            sub_keywords = self.step1_data.get('sub_keywords', '')
            ai_settings = self.step1_data.get('ai_settings', {})
            content_type = ai_settings.get('content_type', '정보/가이드형')

            logger.info(f"🤖 AI 워커 파라미터: search={search_keyword}, target={selected_title}, main={main_keyword}, sub={sub_keywords}, type={content_type}")

            self.analysis_worker = create_ai_blog_analysis_worker(
                self.parent.service,
                search_keyword,
                selected_title,
                main_keyword,
                content_type,
                sub_keywords
            )
            self.analysis_thread = WorkerThread(self.analysis_worker)

            # 시그널 연결
            self.analysis_worker.analysis_started.connect(self.on_analysis_started)
            self.analysis_worker.analysis_progress.connect(self.on_analysis_progress)
            self.analysis_worker.analysis_completed.connect(self.on_analysis_completed)
            self.analysis_worker.error_occurred.connect(self.on_analysis_error)

            # 워커 시작
            self.analysis_thread.start()
            logger.info("✅ 통합 AI 글쓰기 블로그 분석 워커 시작됨")

        except Exception as e:
            logger.error(f"통합 AI 글쓰기 시작 오류: {e}")
            self.reset_integrated_ui()
            TableUIDialogHelper.show_error_dialog(
                self, "오류", f"AI 글쓰기 시작 중 오류가 발생했습니다:\n{e}"
            )

    def stop_ai_writing(self):
        """AI 글쓰기 작업 정지"""
        try:
            logger.info("🛑 AI 글쓰기 작업 정지 요청")
            
            # 실행 중인 워커들 정지
            if self.analysis_worker:
                self.analysis_worker.cancel()
            if self.analysis_thread and self.analysis_thread.isRunning():
                self.analysis_thread.quit()
                self.analysis_thread.wait(3000)  # 3초 대기
                
            if self.summary_worker:
                self.summary_worker.cancel()
            if self.summary_thread and self.summary_thread.isRunning():
                self.summary_thread.quit()
                self.summary_thread.wait(3000)
                
            if self.ai_writer_worker:
                self.ai_writer_worker.cancel()
            if self.ai_writer_thread and self.ai_writer_thread.isRunning():
                self.ai_writer_thread.quit()
                self.ai_writer_thread.wait(3000)
            
            # 메인 UI 상태창 업데이트 (정지)
            if hasattr(self.parent, 'update_status'):
                self.parent.update_status("작업이 정지되었습니다", "warning")
            
            # UI 상태 복원
            self.reset_integrated_ui()
            
            logger.info("✅ AI 글쓰기 작업이 정지되었습니다")
            TableUIDialogHelper.show_info_dialog(
                self, "작업 정지", "AI 글쓰기 작업이 정지되었습니다.", "🛑"
            )
            
        except Exception as e:
            logger.error(f"AI 작업 정지 중 오류: {e}")

    def reset_integrated_ui(self):
        """통합 UI 상태 초기화"""
        self.is_ai_working = False
        self.start_ai_writing_btn.setText("🚀 AI 글쓰기 시작")
        self.start_ai_writing_btn.setEnabled(True)

        # 메인 UI 상태창 초기화 (에러나 정지가 아닌 정상 리셋의 경우에만)
        if hasattr(self.parent, 'update_status') and not hasattr(self, '_suppress_status_reset'):
            self.parent.update_status("대기 중...", "info")

        # 다음 단계 버튼 비활성화
        self.next_step_btn.setEnabled(False)

    def continue_ai_writing(self):
        """분석 완료 후 자동으로 AI 글쓰기 계속 진행"""
        try:
            # 2단계: 정보요약 AI 시작
            logger.info("2단계: 정보요약 AI 프롬프트를 생성합니다...")
            
            # 메인 UI 상태창 업데이트
            if hasattr(self.parent, 'update_status'):
                self.parent.update_status("정보요약 프롬프트 생성 중...", "progress")

            # 정보요약 프롬프트 생성 및 탭 업데이트
            from .ai_prompts import BlogSummaryPrompts

            # 새로운 JSON 입력 구조를 위한 데이터 준비
            main_keyword = self.step1_data.get('main_keyword', '')
            sub_keywords = self.step1_data.get('sub_keywords', '')
            ai_settings = self.step1_data.get('ai_settings', {})
            content_type = ai_settings.get('content_type', '정보/가이드형')

            # 선택된 제목과 검색 키워드 가져오기 (실제 입력된 검색어 사용)
            selected_title = self.step1_data.get('selected_title', '')
            search_keyword = self.search_query_input.text().strip()
            if not search_keyword:
                search_keyword = self.step1_data.get('search_query', main_keyword)

            # 상위 3개 블로그만 사용
            competitor_blogs = self.analyzed_blogs[:3]

            summary_prompt = BlogSummaryPrompts.generate_content_summary_prompt(
                selected_title, search_keyword, main_keyword, content_type, competitor_blogs, sub_keywords
            )

            # 정보요약 프롬프트 탭 업데이트
            self.tab2_summary_prompt.setPlainText(summary_prompt)

            # 3단계: 정보요약 AI 호출
            logger.info("3단계: 정보요약 AI를 호출합니다...")
            
            # 메인 UI 상태창 업데이트
            if hasattr(self.parent, 'update_status'):
                self.parent.update_status("정보요약 AI 작업 중...", "progress")

            # 3단계: 통합 정보요약 AI 워커 호출
            if hasattr(self.parent, 'service') and self.parent.service:
                from .worker import create_summary_worker, WorkerThread

                # 통합 정보요약 워커 생성
                self.summary_worker = create_summary_worker(
                    service=self.parent.service,
                    prompt=summary_prompt,
                    response_format="text",
                    context="JSON 구조 정보요약"
                )
                self.summary_thread = WorkerThread(self.summary_worker)

                # 시그널 연결
                self.summary_worker.completed.connect(self.on_summary_ai_completed)
                self.summary_worker.error_occurred.connect(self.on_summary_ai_error)

                # 워커 시작
                self.summary_thread.start()
                logger.info("✅ 정보요약 AI 워커 시작됨")
            else:
                raise Exception("AI 서비스가 설정되지 않았습니다.")

        except Exception as e:
            logger.error(f"AI 글쓰기 계속 진행 오류: {e}")
            self.reset_integrated_ui()
            TableUIDialogHelper.show_error_dialog(
                self, "오류", f"AI 글쓰기 진행 중 오류가 발생했습니다:\n{e}"
            )

    def on_summary_ai_completed(self, summary_result: str):
        """정보요약 AI 완료 후 처리"""
        try:
            # 정보요약 AI 답변 탭 업데이트
            self.tab3_summary_response.setPlainText(summary_result)

            # 4단계: 글쓰기 AI 프롬프트 생성
            logger.info("4단계: 글쓰기 AI 프롬프트를 생성합니다...")
            
            # 메인 UI 상태창 업데이트
            if hasattr(self.parent, 'update_status'):
                self.parent.update_status("글쓰기 프롬프트 생성 중...", "progress")

            # service를 통한 통합 프롬프트 생성 (CLAUDE.md 구조 준수)
            ai_settings = self.step1_data.get('ai_settings', {})
            main_keyword = self.step1_data.get('main_keyword', '')
            sub_keywords = self.step1_data.get('sub_keywords', '')
            selected_title = self.step1_data.get('selected_title', '')
            content_type = ai_settings.get('content_type', '정보/가이드형')
            tone = ai_settings.get('tone', '정중한 존댓말체')
            review_detail = ai_settings.get('review_detail', '')

            # 검색 키워드 가져오기 (동일한 로직)
            search_keyword = self.search_query_input.text().strip()
            if not search_keyword:
                search_keyword = self.step1_data.get('search_query', main_keyword)

            # service를 통해 UI 표시용 프롬프트 생성 (실제 AI 호출과 동일한 프롬프트 보장)
            ai_data = self.parent.service.generate_ui_prompt_for_display(
                main_keyword=main_keyword,
                sub_keywords=sub_keywords, 
                analyzed_blogs=self.analyzed_blogs,
                content_type=content_type,
                tone=tone,
                review_detail=review_detail,
                selected_title=selected_title,
                search_keyword=search_keyword,
                summary_result=summary_result
            )

            if not ai_data:
                raise Exception("글쓰기 AI 프롬프트 생성 실패")
            
            logger.info(f"🔍 DEBUG: ai_data keys = {list(ai_data.keys()) if ai_data else 'None'}")

            writing_prompt = ai_data.get('ai_prompt', '')

            # 글쓰기 AI 프롬프트 탭 업데이트
            self.tab4_writing_prompt.setPlainText(writing_prompt)

            # 5단계: 글쓰기 AI 호출
            logger.info("5단계: 글쓰기 AI가 블로그 글을 생성합니다...")
            
            # 메인 UI 상태창 업데이트
            if hasattr(self.parent, 'update_status'):
                self.parent.update_status("글쓰기 AI 작업 중...", "progress")

            # 5단계: 비동기 글쓰기 AI 워커 호출
            if hasattr(self.parent, 'service') and self.parent.service:
                from .worker import create_ai_writing_worker, WorkerThread

                # 글쓰기 워커 생성 (기본 매개변수로 호출) - 사용자가 수정한 검색어 사용 (1단계와 동일한 로직)
                search_keyword = self.search_query_input.text().strip()
                if not search_keyword:
                    search_keyword = self.step1_data.get('search_query', main_keyword)
                logger.info(f"🔍 통합 AI 글쓰기 워커 search_keyword: '{search_keyword}'")
                self.ai_writer_worker = create_ai_writing_worker(
                    self.parent.service,
                    main_keyword,
                    sub_keywords,
                    ai_data['structured_data'],
                    self.analyzed_blogs,
                    content_type,
                    tone,
                    review_detail,
                    search_keyword,
                    selected_title
                )
                self.ai_writer_thread = WorkerThread(self.ai_writer_worker)

                # 시그널 연결
                self.ai_writer_worker.writing_progress.connect(self.on_analysis_progress)
                self.ai_writer_worker.writing_completed.connect(self.on_writing_ai_completed)
                self.ai_writer_worker.error_occurred.connect(self.on_writing_ai_error)

                # 워커 시작
                self.ai_writer_thread.start()
                logger.info("✅ 글쓰기 AI 워커 시작됨")
            else:
                raise Exception("AI 서비스가 설정되지 않았습니다.")

        except Exception as e:
            logger.error(f"정보요약 AI 완료 처리 오류: {e}")
            self.reset_integrated_ui()

    def on_summary_ai_error(self, error_message: str):
        """정보요약 AI 오류 처리"""
        try:
            logger.error(f"❌ 정보요약 AI 오류: {error_message}")
            
            # 메인 UI 상태창 업데이트 (오류)
            if hasattr(self.parent, 'update_status'):
                self.parent.update_status("정보요약 AI 오류 발생", "error")
                
            self.reset_integrated_ui()
            TableUIDialogHelper.show_error_dialog(
                self, "정보요약 AI 오류", f"정보요약 AI 처리 중 오류가 발생했습니다:\n{error_message}"
            )
        except Exception as e:
            logger.error(f"정보요약 AI 오류 처리 중 오류: {e}")

    def on_writing_ai_completed(self, generated_content: str):
        """글쓰기 AI 완료 후 처리"""
        try:
            # 글쓰기 AI 답변 탭 업데이트
            self.tab5_writing_response.setPlainText(generated_content)

            # 최종 완료
            logger.info("✅ AI 블로그 글 생성이 완료되었습니다!")
            
            # 메인 UI 상태창 업데이트 (성공)
            if hasattr(self.parent, 'update_status'):
                self.parent.update_status("AI 글 생성 완료!", "success")

            # 생성된 내용 저장
            self.generated_content = generated_content

            # AI 작업 완료 상태 업데이트
            self.is_ai_working = False
            
            # 버튼 상태 복원
            self.start_ai_writing_btn.setText("🚀 AI 글쓰기 시작")
            self.start_ai_writing_btn.setEnabled(True)

            # 다음 단계 버튼 활성화
            self.next_step_btn.setEnabled(True)

            # 완료 다이얼로그
            TableUIDialogHelper.show_success_dialog(
                self, "AI 글쓰기 완료",
                "AI가 블로그 글 생성을 완료했습니다!",
                "🎉"
            )

        except Exception as e:
            logger.error(f"글쓰기 AI 완료 처리 오류: {e}")
            self.reset_integrated_ui()

    def on_writing_ai_error(self, error_message: str):
        """글쓰기 AI 오류 처리"""
        try:
            logger.error(f"❌ 글쓰기 AI 오류: {error_message}")
            
            # 메인 UI 상태창 업데이트 (오류)
            if hasattr(self.parent, 'update_status'):
                self.parent.update_status("글쓰기 AI 오류 발생", "error")
                
            self.reset_integrated_ui()
            TableUIDialogHelper.show_error_dialog(
                self, "글쓰기 AI 오류", f"글쓰기 AI 처리 중 오류가 발생했습니다:\n{error_message}"
            )
        except Exception as e:
            logger.error(f"글쓰기 AI 오류 처리 중 오류: {e}")