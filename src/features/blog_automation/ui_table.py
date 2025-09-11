"""
블로그 자동화 모듈의 글쓰기 테이블 UI
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QTextEdit, QPushButton, QProgressBar,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, QThread, Signal
import traceback

from src.foundation.logging import get_logger
from src.toolbox.ui_kit.components import (
    ModernButton, ModernLineEdit, ModernCard, 
    ModernPrimaryButton, ModernSuccessButton, ModernDangerButton
)
from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog
from src.toolbox.ui_kit.modern_style import ModernStyle
from src.toolbox.ui_kit import tokens
from src.foundation.exceptions import BusinessError, ValidationError

logger = get_logger("blog_automation.ui_table")


class BlogWriteTableUI(QWidget):
    """블로그 글쓰기 테이블 UI"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent  # BlogAutomationMainUI 참조
        self.ai_prompt_data = None  # AI 프롬프트 데이터 저장
        
        # 워커 관련
        self.analysis_worker = None
        self.analysis_thread = None
        
        self.setup_ui()
        self.setup_styles()
    
    def setup_ui(self):
        """UI 구성"""
        main_layout = QVBoxLayout()
        margin = tokens.GAP_16
        spacing = tokens.GAP_12
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)
        
        # 키워드 입력 카드
        keyword_card = self.create_keyword_input_card()
        main_layout.addWidget(keyword_card)
        
        # 상위 블로그 분석 카드
        analysis_card = self.create_analysis_card()
        main_layout.addWidget(analysis_card)
        
        # AI 글쓰기 카드
        write_card = self.create_write_card()
        main_layout.addWidget(write_card)
        
        # 발행 카드
        publish_card = self.create_publish_card()
        main_layout.addWidget(publish_card)
        
        self.setLayout(main_layout)
    
    def create_keyword_input_card(self) -> ModernCard:
        """키워드 입력 카드 생성"""
        card = ModernCard("🔍 주제 키워드 입력")
        layout = QVBoxLayout()
        
        # 키워드 입력
        keyword_layout = QHBoxLayout()
        keyword_layout.addWidget(QLabel("주제 키워드:"))
        
        self.keyword_input = ModernLineEdit()
        self.keyword_input.setPlaceholderText("블로그 글의 주제를 입력하세요 (예: 프로그래밍 학습법)")
        keyword_layout.addWidget(self.keyword_input)
        
        # 분석 시작 버튼
        self.analyze_button = ModernPrimaryButton("📊 상위 블로그 분석 시작")
        self.analyze_button.clicked.connect(self.on_analyze_clicked)
        keyword_layout.addWidget(self.analyze_button)
        
        layout.addLayout(keyword_layout)
        
        # 설명
        desc_label = QLabel(
            "💡 입력한 키워드로 네이버 블로그 상위 3개 게시글을 분석합니다.\n"
            "로그인 없이도 분석 가능하며, 경쟁력 있는 콘텐츠 작성에 활용할 수 있습니다."
        )
        desc_label.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_muted']};
                font-size: 12px;
                padding: {tokens.GAP_8}px;
                background-color: {ModernStyle.COLORS['bg_muted']};
                border-radius: {tokens.RADIUS_SM}px;
            }}
        """)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        card.setLayout(layout)
        return card
    
    def create_analysis_card(self) -> ModernCard:
        """상위 블로그 분석 카드 생성"""
        card = ModernCard("📈 상위 블로그 분석 결과")
        layout = QVBoxLayout()
        
        # 분석 진행률
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("분석 진행률:"))
        
        self.analysis_progress = QProgressBar()
        self.analysis_progress.setVisible(False)
        progress_layout.addWidget(self.analysis_progress)
        
        layout.addLayout(progress_layout)
        
        # 상위 블로그 테이블 (카테고리, 발행일 제거, 태그 전체 표시)
        self.blog_table = QTableWidget(0, 8)  # 0행 8열
        self.blog_table.setHorizontalHeaderLabels([
            "순위", "제목", "글자수", "이미지수", "GIF수", "동영상수", "태그", "URL"
        ])
        
        # 테이블 설정 (8열 구성) - 가로 스크롤 가능하도록 고정 너비 설정
        header = self.blog_table.horizontalHeader()
        
        # 고정 너비로 설정하여 가로 스크롤 활성화
        self.blog_table.setColumnWidth(0, 50)   # 순위 (더 좁게)
        self.blog_table.setColumnWidth(1, 300)  # 제목 (더 넓게)
        self.blog_table.setColumnWidth(2, 80)   # 글자수
        self.blog_table.setColumnWidth(3, 80)   # 이미지수
        self.blog_table.setColumnWidth(4, 70)   # GIF수
        self.blog_table.setColumnWidth(5, 80)   # 동영상수
        self.blog_table.setColumnWidth(6, 400)  # 태그 (많은 태그를 위해 넓게)
        self.blog_table.setColumnWidth(7, 200)  # URL
        
        # 가로 스크롤 활성화
        header.setSectionResizeMode(QHeaderView.Interactive)
        self.blog_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 태그 컬럼을 두 줄로 표시하기 위해 행 높이 조정
        self.blog_table.verticalHeader().setDefaultSectionSize(60)  # 기본 행 높이 증가
        
        # 텍스트 래핑 활성화
        self.blog_table.setWordWrap(True)
        
        self.blog_table.setAlternatingRowColors(True)
        self.blog_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.blog_table)
        
        card.setLayout(layout)
        return card
    
    def create_write_card(self) -> ModernCard:
        """AI 글쓰기 카드 생성"""
        card = ModernCard("✨ AI 블로그 글 작성")
        layout = QVBoxLayout()
        
        # AI 글쓰기 버튼
        button_layout = QHBoxLayout()
        
        self.write_button = ModernSuccessButton("🤖 AI로 블로그 글 작성하기")
        self.write_button.clicked.connect(self.on_write_clicked)
        self.write_button.setEnabled(False)  # 분석 완료 후 활성화
        button_layout.addWidget(self.write_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 생성된 글 미리보기
        self.generated_text = QTextEdit()
        self.generated_text.setPlaceholderText("AI가 작성한 블로그 글이 여기에 표시됩니다...")
        self.generated_text.setMaximumHeight(200)
        layout.addWidget(self.generated_text)
        
        card.setLayout(layout)
        return card
    
    def create_publish_card(self) -> ModernCard:
        """발행 카드 생성"""
        card = ModernCard("📤 블로그 발행")
        layout = QVBoxLayout()
        
        # 발행 버튼
        button_layout = QHBoxLayout()
        
        self.publish_button = ModernDangerButton("🚀 네이버 블로그에 발행하기")
        self.publish_button.clicked.connect(self.on_publish_clicked)
        self.publish_button.setEnabled(False)  # 글 작성 완료 후 활성화
        button_layout.addWidget(self.publish_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 발행 상태
        self.publish_status = QLabel("발행 준비 중...")
        self.publish_status.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['text_muted']};
                font-size: 12px;
                padding: {tokens.GAP_8}px;
                background-color: {ModernStyle.COLORS['bg_muted']};
                border-radius: {tokens.RADIUS_SM}px;
            }}
        """)
        layout.addWidget(self.publish_status)
        
        card.setLayout(layout)
        return card
    
    def setup_styles(self):
        """스타일 설정"""
        # 테이블 스타일
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
    
    def on_analyze_clicked(self):
        """상위 블로그 분석 시작"""
        try:
            keyword = self.keyword_input.text().strip()
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
            
            # 키워드 저장 (AI 프롬프트에서 사용)
            self.current_keyword = keyword
            
            # 로그인 없이도 상위 블로그 분석 가능
            logger.info("로그인 없이 상위 블로그 분석 시작")
            logger.info(f"상위 블로그 분석 시작: {keyword}")
            
            # UI 상태 변경
            self.analyze_button.setText("🔄 분석 중...")
            self.analyze_button.setEnabled(False)
            self.analysis_progress.setVisible(True)
            self.analysis_progress.setValue(10)
            
            # 테이블 초기화
            self.blog_table.setRowCount(0)
            
            # 비동기 분석 시작
            self.start_async_analysis(keyword)
            
        except Exception as e:
            logger.error(f"분석 시작 오류: {e}")
            self.reset_analysis_ui()
    
    def start_async_analysis(self, keyword: str):
        """비동기 블로그 분석 시작"""
        try:
            logger.info("🚀 비동기 블로그 분석 시작")
            
            # 워커 생성
            from .worker import create_blog_analysis_worker, WorkerThread
            
            self.analysis_worker = create_blog_analysis_worker(self.parent.service, keyword)
            self.analysis_thread = WorkerThread(self.analysis_worker)
            
            # 시그널 연결
            self.analysis_worker.analysis_started.connect(self.on_analysis_started)
            self.analysis_worker.analysis_progress.connect(self.on_analysis_progress)
            self.analysis_worker.analysis_completed.connect(self.on_analysis_completed)
            self.analysis_worker.error_occurred.connect(self.on_analysis_error)
            self.analysis_worker.blog_found.connect(self.on_blog_found)
            
            # 워커 시작
            self.analysis_thread.start()
            logger.info("✅ 비동기 블로그 분석 워커 시작됨")
            
        except Exception as e:
            logger.error(f"❌ 비동기 분석 시작 실패: {e}")
            self.reset_analysis_ui()
    
    def on_analysis_started(self):
        """분석 시작 시그널 처리"""
        logger.info("📊 분석 시작됨")
        self.analysis_progress.setValue(15)
    
    def on_analysis_progress(self, message: str, progress: int):
        """분석 진행 상황 업데이트"""
        logger.info(f"📝 분석 진행: {message} ({progress}%)")
        self.analysis_progress.setValue(progress)
    
    def on_blog_found(self, count: int):
        """블로그 발견 시그널 처리"""
        logger.info(f"🔍 {count}개 블로그 발견")
    
    def on_analysis_completed(self, analyzed_blogs: list):
        """분석 완룼 처리"""
        try:
            logger.info(f"✅ 비동기 분석 성공!")
            
            # 결과를 테이블에 표시
            self.populate_blog_table(analyzed_blogs)
            
            # AI 글쓰기 버튼 활성화
            self.write_button.setEnabled(True)
            
            # AI 프롬프트 생성 및 저장 (테스트를 위해 임시 주석처리)
            # if hasattr(self, 'current_keyword'):
            #     self.generate_ai_prompt(self.current_keyword, analyzed_blogs)
            
            # UI 상태 복원
            self.reset_analysis_ui()
            
            # 성공 다이얼로그
            dialog = ModernConfirmDialog(
                self,
                title="분석 완료",
                message=f"상위 {len(analyzed_blogs)}개 블로그 분석이 완료되었습니다!\n글자수: {analyzed_blogs[0]['content_length'] if analyzed_blogs else 0}자, 이미지: {analyzed_blogs[0]['image_count'] if analyzed_blogs else 0}개",
                confirm_text="확인",
                cancel_text=None,
                icon="🎉"
            )
            dialog.exec()
            
        except Exception as e:
            logger.error(f"분석 완료 처리 중 오류: {e}")
            self.reset_analysis_ui()
    
    def on_analysis_error(self, error_message: str):
        """분석 오류 처리"""
        try:
            logger.error(f"❌ 분석 오류: {error_message}")
            self.reset_analysis_ui()
            
            dialog = ModernConfirmDialog(
                self,
                title="분석 오류",
                message=f"블로그 분석 중 오류가 발생했습니다:\n{error_message}",
                confirm_text="확인",
                cancel_text=None,
                icon="❌"
            )
            dialog.exec()
            
        except Exception as e:
            logger.error(f"분석 오류 처리 중 오류: {e}")
    
    def reset_analysis_ui(self):
        """분석 UI 상태 초기화"""
        self.analyze_button.setText("📊 상위 블로그 분석 시작")
        self.analyze_button.setEnabled(True)
        self.analysis_progress.setVisible(False)
    
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
                tag_item.setToolTip(', '.join(tags) if tags else '태그 없음')  # 마우스 호버 시 전체 태그 표시
                
                # 태그 셀의 텍스트 래핑 활성화
                tag_item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)  # 상단 왼쪽 정렬
                self.blog_table.setItem(row, 6, tag_item)
                
                # URL (단축)
                url = blog['url'][:50] + '...' if len(blog['url']) > 50 else blog['url']
                self.blog_table.setItem(row, 7, QTableWidgetItem(url))
            
            logger.info(f"테이블에 {len(analyzed_blogs)}개 블로그 데이터 표시 완료")
            
        except Exception as e:
            logger.error(f"테이블 데이터 표시 오류: {e}")
    
    def generate_ai_prompt(self, keyword: str, analyzed_blogs: list):
        """분석된 블로그 데이터로 AI 프롬프트 생성"""
        try:
            from .ai_prompts import create_ai_request_data, BlogAIPrompts
            
            # AI 요청 데이터 생성
            ai_data = create_ai_request_data(keyword, analyzed_blogs)
            
            if ai_data:
                # 대화형 구조 프롬프트도 생성
                structure_prompts = []
                for blog in analyzed_blogs:
                    structure_text = self.format_blog_structure(blog)
                    if structure_text:
                        prompt = BlogAIPrompts.generate_blog_structure_prompt(structure_text)
                        structure_prompts.append({
                            'blog_title': blog.get('title', ''),
                            'structure_prompt': prompt
                        })
                
                # 데이터 저장 (임시로 인스턴스 변수에)
                self.ai_prompt_data = {
                    'keyword': keyword,
                    'structured_data': ai_data['structured_data'],
                    'main_prompt': ai_data['ai_prompt'],
                    'structure_prompts': structure_prompts,
                    'raw_blogs': analyzed_blogs
                }
                
                logger.info(f"AI 프롬프트 생성 완료: {keyword}")
                logger.debug(f"메인 프롬프트 길이: {len(self.ai_prompt_data['main_prompt'])}자")
                logger.debug(f"구조 프롬프트 개수: {len(structure_prompts)}개")
                
            else:
                logger.error("AI 프롬프트 생성 실패")
                
        except Exception as e:
            logger.error(f"AI 프롬프트 생성 오류: {e}")
    
    def format_blog_structure(self, blog: dict) -> str:
        """블로그 구조를 AI가 이해할 수 있는 텍스트 형식으로 만들기"""
        try:
            structure = blog.get('content_structure', [])
            if not structure:
                return ""
            
            formatted_text = f"# {blog.get('title', '제목 없음')}\n\n"
            
            for item in structure:
                item_type = item.get('type', '')
                content = item.get('content', '')
                
                if item_type == '제목':
                    formatted_text += f"# {content}\n\n"
                elif item_type == '소제목':
                    formatted_text += f"## {content}\n\n"
                elif item_type == '글':
                    formatted_text += f"{content}\n\n"
                elif item_type == '이미지':
                    formatted_text += f"[이미지 위치]\n\n"
                elif item_type == 'GIF':
                    formatted_text += f"[GIF 위치]\n\n"
                elif item_type == '동영상':
                    formatted_text += f"[동영상 위치]\n\n"
                elif item_type == '이미지설명':
                    formatted_text += f"(이미지 설명: {content})\n\n"
            
            return formatted_text.strip()
            
        except Exception as e:
            logger.error(f"블로그 구조 포맷팅 오류: {e}")
            return ""
    
    def on_write_clicked(self):
        """AI 글쓰기 시작"""
        try:
            logger.info("AI 블로그 글 작성 시작")
            
            # TODO: 실제 AI 글쓰기 로직 구현
            dialog = ModernConfirmDialog(
                self,
                title="구현 예정",
                message="AI 블로그 글 작성 기능은 곧 구현됩니다.\n현재는 UI만 구성된 상태입니다.",
                confirm_text="확인",
                cancel_text=None,
                icon="🚧"
            )
            dialog.exec()
            
        except Exception as e:
            logger.error(f"AI 글쓰기 오류: {e}")
    
    def on_publish_clicked(self):
        """블로그 발행 시작"""
        try:
            logger.info("네이버 블로그 발행 시작")
            
            # TODO: 실제 발행 로직 구현
            dialog = ModernConfirmDialog(
                self,
                title="구현 예정",
                message="네이버 블로그 발행 기능은 곧 구현됩니다.\n현재는 UI만 구성된 상태입니다.",
                confirm_text="확인",
                cancel_text=None,
                icon="🚧"
            )
            dialog.exec()
            
        except Exception as e:
            logger.error(f"블로그 발행 오류: {e}")