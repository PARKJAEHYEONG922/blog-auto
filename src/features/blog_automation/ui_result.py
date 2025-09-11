"""
블로그 자동화 모듈의 결과 탭 UI
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTextEdit, QPushButton, QProgressBar,
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget
)
from PySide6.QtCore import Qt
import traceback

from src.foundation.logging import get_logger
from src.toolbox.ui_kit.components import (
    ModernButton, ModernCard, 
    ModernPrimaryButton, ModernSuccessButton, ModernDangerButton
)
from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
from src.toolbox.ui_kit.modern_style import ModernStyle
from src.toolbox.ui_kit import tokens

logger = get_logger("blog_automation.ui_result")


class BlogResultTabWidget(QTabWidget):
    """블로그 자동화 결과 탭 위젯"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
        self.setup_tabs()
        self.setup_styles()
    
    def setup_tabs(self):
        """탭들을 설정"""
        # 탭 1: 경쟁사 분석
        self.analysis_tab = AnalysisResultTab(self.parent)
        self.addTab(self.analysis_tab, "📊 상위 블로그 분석")
        
        # 탭 2: AI 프롬프트
        self.prompt_tab = PromptResultTab(self.parent)
        self.addTab(self.prompt_tab, "📝 AI 프롬프트")
        
        # 탭 3: 생성된 글
        self.content_tab = ContentResultTab(self.parent)
        self.addTab(self.content_tab, "✨ AI 생성 결과")
    
    def setup_styles(self):
        """탭 위젯 스타일 설정"""
        self.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: {tokens.RADIUS_SM}px;
                background-color: {ModernStyle.COLORS['bg_card']};
            }}
            QTabBar::tab {{
                background-color: {ModernStyle.COLORS['bg_muted']};
                border: 1px solid {ModernStyle.COLORS['border']};
                border-bottom: none;
                border-top-left-radius: {tokens.RADIUS_SM}px;
                border-top-right-radius: {tokens.RADIUS_SM}px;
                padding: {tokens.GAP_8}px {tokens.GAP_16}px;
                margin-right: 2px;
                font-weight: 500;
            }}
            QTabBar::tab:selected {{
                background-color: {ModernStyle.COLORS['primary']};
                color: white;
            }}
            QTabBar::tab:hover {{
                background-color: {ModernStyle.COLORS['primary_light']};
            }}
        """)


class AnalysisResultTab(QWidget):
    """경쟁사 분석 결과 탭"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
        self.setup_ui()
        self.setup_styles()
    
    def setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout()
        
        # 분석 진행률
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("분석 진행률:"))
        
        self.analysis_progress = QProgressBar()
        self.analysis_progress.setVisible(False)
        progress_layout.addWidget(self.analysis_progress)
        
        layout.addLayout(progress_layout)
        
        # 상위 블로그 테이블
        self.blog_table = QTableWidget(0, 8)  # 0행 8열
        self.blog_table.setHorizontalHeaderLabels([
            "순위", "제목", "글자수", "이미지수", "GIF수", "동영상수", "태그", "URL"
        ])
        
        # 테이블 설정
        header = self.blog_table.horizontalHeader()
        
        # 고정 너비 설정
        self.blog_table.setColumnWidth(0, 50)   # 순위
        self.blog_table.setColumnWidth(1, 300)  # 제목
        self.blog_table.setColumnWidth(2, 80)   # 글자수
        self.blog_table.setColumnWidth(3, 80)   # 이미지수
        self.blog_table.setColumnWidth(4, 70)   # GIF수
        self.blog_table.setColumnWidth(5, 80)   # 동영상수
        self.blog_table.setColumnWidth(6, 400)  # 태그
        self.blog_table.setColumnWidth(7, 200)  # URL
        
        # 가로 스크롤 활성화
        header.setSectionResizeMode(QHeaderView.Interactive)
        self.blog_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 행 높이 조정
        self.blog_table.verticalHeader().setDefaultSectionSize(60)
        
        # 텍스트 래핑 활성화
        self.blog_table.setWordWrap(True)
        self.blog_table.setAlternatingRowColors(True)
        self.blog_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(self.blog_table)
        
        self.setLayout(layout)
    
    def setup_styles(self):
        """스타일 설정"""
        self.blog_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {ModernStyle.COLORS['bg_card']};
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: {tokens.RADIUS_SM}px;
                gridline-color: {ModernStyle.COLORS['border']};
            }}
            QTableWidget::item {{
                padding: {tokens.GAP_8}px;
                border-bottom: 1px solid {ModernStyle.COLORS['border']};
            }}
            QTableWidget::item:selected {{
                background-color: {ModernStyle.COLORS['primary']};
                color: white;
            }}
            QHeaderView::section {{
                background-color: {ModernStyle.COLORS['bg_muted']};
                padding: {tokens.GAP_8}px;
                border: 1px solid {ModernStyle.COLORS['border']};
                font-weight: 600;
            }}
        """)
    
    def populate_blog_table(self, analyzed_blogs):
        """분석된 블로그 데이터를 테이블에 표시"""
        try:
            self.blog_table.setRowCount(len(analyzed_blogs))
            
            for row, blog in enumerate(analyzed_blogs):
                # 순위
                self.blog_table.setItem(row, 0, QTableWidgetItem(str(blog['rank'])))
                
                # 제목
                title = blog['title'][:50] + '...' if len(blog['title']) > 50 else blog['title']
                self.blog_table.setItem(row, 1, QTableWidgetItem(title))
                
                # 글자수
                self.blog_table.setItem(row, 2, QTableWidgetItem(str(blog['content_length'])))
                
                # 이미지 수
                self.blog_table.setItem(row, 3, QTableWidgetItem(str(blog['image_count'])))
                
                # GIF 수
                self.blog_table.setItem(row, 4, QTableWidgetItem(str(blog['gif_count'])))
                
                # 동영상 수
                self.blog_table.setItem(row, 5, QTableWidgetItem(str(blog['video_count'])))
                
                # 태그 (두 줄로 표시)
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
                
                # URL (단축)
                url = blog['url'][:50] + '...' if len(blog['url']) > 50 else blog['url']
                self.blog_table.setItem(row, 7, QTableWidgetItem(url))
            
            logger.info(f"테이블에 {len(analyzed_blogs)}개 블로그 데이터 표시 완료")
            
        except Exception as e:
            logger.error(f"테이블 데이터 표시 오류: {e}")


class PromptResultTab(QWidget):
    """AI 프롬프트 결과 탭"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
        self.setup_ui()
    
    def setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout()
        
        # 제목 표시
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("📝 AI가 받은 프롬프트:"))
        title_layout.addStretch()
        
        # 복사 버튼
        self.copy_prompt_button = ModernButton("📋 프롬프트 복사")
        self.copy_prompt_button.clicked.connect(self.copy_prompt_content)
        title_layout.addWidget(self.copy_prompt_button)
        
        layout.addLayout(title_layout)
        
        # 프롬프트 미리보기
        self.prompt_text = QTextEdit()
        self.prompt_text.setPlaceholderText("AI가 받은 프롬프트가 여기에 표시됩니다...")
        self.prompt_text.setMinimumHeight(400)
        self.prompt_text.setReadOnly(True)  # 읽기 전용
        layout.addWidget(self.prompt_text)
        
        self.setLayout(layout)
    
    def copy_prompt_content(self):
        """프롬프트 내용을 클립보드에 복사"""
        try:
            from PySide6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(self.prompt_text.toPlainText())
            
            # 성공 알림
            dialog = ModernConfirmDialog(
                self,
                title="복사 완료",
                message="AI 프롬프트가 클립보드에 복사되었습니다!",
                confirm_text="확인",
                cancel_text=None,
                icon="📋"
            )
            dialog.exec()
            
        except Exception as e:
            logger.error(f"클립보드 복사 오류: {e}")
    
    def set_prompt_content(self, prompt: str):
        """프롬프트 내용 설정"""
        self.prompt_text.setPlainText(prompt)


class ContentResultTab(QWidget):
    """생성된 콘텐츠 결과 탭"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
        self.setup_ui()
    
    def setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout()
        
        # 제목 표시
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("📝 생성된 블로그 글:"))
        title_layout.addStretch()
        
        # 복사 버튼
        self.copy_button = ModernButton("📋 전체 복사")
        self.copy_button.clicked.connect(self.copy_content)
        title_layout.addWidget(self.copy_button)
        
        layout.addLayout(title_layout)
        
        # 생성된 글 미리보기
        self.generated_text = QTextEdit()
        self.generated_text.setPlaceholderText("AI가 작성한 블로그 글이 여기에 표시됩니다...")
        self.generated_text.setMinimumHeight(400)
        layout.addWidget(self.generated_text)
        
        self.setLayout(layout)
    
    def copy_content(self):
        """생성된 글을 클립보드에 복사"""
        try:
            from PySide6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(self.generated_text.toPlainText())
            
            # 성공 알림
            dialog = ModernConfirmDialog(
                self,
                title="복사 완료",
                message="생성된 글이 클립보드에 복사되었습니다!",
                confirm_text="확인",
                cancel_text=None,
                icon="📋"
            )
            dialog.exec()
            
        except Exception as e:
            logger.error(f"클립보드 복사 오류: {e}")
    
    def set_generated_content(self, content: str):
        """생성된 콘텐츠 설정"""
        self.generated_text.setPlainText(content)


