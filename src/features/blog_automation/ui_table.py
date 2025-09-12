"""
블로그 자동화 모듈의 글쓰기 테이블 UI
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QTextEdit, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget, QComboBox
)
from PySide6.QtCore import Qt, QThread, Signal
import traceback

from src.foundation.logging import get_logger
from src.toolbox.ui_kit.components import (
    ModernButton, ModernLineEdit, ModernCard, 
    ModernPrimaryButton, ModernSuccessButton, ModernDangerButton
)
from src.toolbox.ui_kit.modern_dialog import ModernConfirmDialog, ModernScrollableDialog
from src.toolbox.ui_kit.modern_style import ModernStyle
from src.toolbox.ui_kit import tokens
from src.foundation.exceptions import BusinessError, ValidationError

logger = get_logger("blog_automation.ui_table")


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
    def show_warning_dialog(parent, title: str = "경고", message: str = "", icon: str = "⚠️"):
        """경고 다이얼로그 표시"""
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
    
    @staticmethod
    def show_scrollable_success_dialog(parent, title: str = "성공", message: str = "", icon: str = "✅"):
        """스크롤 가능한 성공 다이얼로그 표시 (긴 텍스트용)"""
        dialog = ModernScrollableDialog(
            parent,
            title=title,
            message=message,
            confirm_text="확인",
            cancel_text=None,
            icon=icon
        )
        return dialog.exec()


class BlogWriteTableUI(QWidget):
    """블로그 글쓰기 테이블 UI"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent  # BlogAutomationMainUI 참조
        self.ai_prompt_data = None  # AI 프롬프트 데이터 저장
        
        # 워커 관련
        self.analysis_worker = None
        self.analysis_thread = None
        
        # 결과 창 관리
        self.results_dialog = None  # 결과 창이 열려있는지 추적
        
        self.setup_ui()
        self.setup_styles()
        self.load_ai_settings()  # AI 설정 로드 추가
    
    def setup_ui(self):
        """UI 구성"""
        main_layout = QVBoxLayout()
        margin = tokens.GAP_16
        spacing = tokens.GAP_12
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)
        
        # AI 글쓰기 설정 카드 (맨 위)
        ai_settings_card = self.create_ai_settings_card()
        main_layout.addWidget(ai_settings_card)
        
        # 키워드 입력 카드
        keyword_card = self.create_keyword_input_card()
        main_layout.addWidget(keyword_card)
        
        # 블로그 발행 카드 (항상 보임)
        publish_card = self.create_publish_card()
        main_layout.addWidget(publish_card)
        
        # 결과 탭 위젯 (처음엔 숨김) - 별도 위젯으로 생성만 하고 표시하지 않음
        from .ui_result import BlogResultTabWidget
        self.result_tabs = BlogResultTabWidget(self.parent)
        self.result_tabs.setVisible(False)  # 처음엔 숨김
        
        self.setLayout(main_layout)
    
    def create_keyword_input_card(self) -> ModernCard:
        """키워드 입력 카드 생성"""
        card = ModernCard("🔍 블로그 키워드 설정")
        layout = QVBoxLayout()
        layout.setSpacing(tokens.GAP_8)  # 요소 간 간격 조정
        
        # 간단한 설명
        simple_desc = QLabel("메인키워드 입력 후 자동생성 버튼을 클릭해주세요\n   • 보조키워드는 생략 가능하며, 여러 개 입력할 수 있습니다")
        simple_desc.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['primary']};
                font-size: {tokens.get_font_size('normal')}px;
                font-weight: 600;
                padding: 4px 0px;
                margin-bottom: {tokens.GAP_8}px;
                line-height: 1.4;
            }}
        """)
        layout.addWidget(simple_desc)
        
        # 메인키워드 입력
        main_keyword_layout = QHBoxLayout()
        main_keyword_label = QLabel("메인키워드:")
        main_keyword_label.setMinimumWidth(80)  # 라벨 너비 고정
        main_keyword_label.setStyleSheet(f"font-size: {tokens.get_font_size('normal')}px;")
        main_keyword_layout.addWidget(main_keyword_label)
        
        self.main_keyword_input = ModernLineEdit()
        self.main_keyword_input.setPlaceholderText("메인키워드 필수 (예: 프로그래밍 학습법)")
        self.main_keyword_input.setMinimumHeight(40)  # 높이 증가
        main_keyword_layout.addWidget(self.main_keyword_input, 1)  # 확장 가능
        
        layout.addLayout(main_keyword_layout)
        
        # 보조키워드 입력
        sub_keyword_layout = QHBoxLayout()
        sub_keyword_label = QLabel("보조키워드:")
        sub_keyword_label.setMinimumWidth(80)  # 라벨 너비 고정
        sub_keyword_label.setStyleSheet(f"font-size: {tokens.get_font_size('normal')}px;")
        sub_keyword_layout.addWidget(sub_keyword_label)
        
        self.sub_keyword_input = ModernLineEdit()
        self.sub_keyword_input.setPlaceholderText("보조 키워드들을 쉼표로 구분 (예: 개발자, 코딩, 입문)")
        self.sub_keyword_input.setMinimumHeight(40)  # 높이 증가
        sub_keyword_layout.addWidget(self.sub_keyword_input, 1)  # 확장 가능
        
        layout.addLayout(sub_keyword_layout)
        
        # AI 자동 생성 버튼과 결과 보기 버튼
        button_layout = QHBoxLayout()
        button_layout.setSpacing(tokens.GAP_8)  # 버튼 간 간격
        button_layout.addStretch()
        
        # 자동 생성 버튼
        self.auto_generate_button = ModernPrimaryButton("🚀 AI 블로그 글 자동 생성")
        self.auto_generate_button.clicked.connect(self.on_auto_generate_clicked)
        button_layout.addWidget(self.auto_generate_button)
        
        # 결과 보기 버튼 (처음엔 비활성화)
        self.show_results_button = ModernSuccessButton("📋 결과 보기")
        self.show_results_button.clicked.connect(self.on_show_results_clicked)
        self.show_results_button.setEnabled(False)  # 처음엔 비활성화
        button_layout.addWidget(self.show_results_button)
        
        layout.addLayout(button_layout)
        
        card.setLayout(layout)
        
        # 카드 사이즈 최적화 - 2줄 설명 텍스트로 높이 증가
        card.setMaximumHeight(250)
        
        return card
    
    def create_publish_card(self) -> ModernCard:
        """발행 카드 생성"""
        card = ModernCard("📤 블로그 발행")
        layout = QVBoxLayout()
        
        # 발행 버튼만 중앙에 배치
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.publish_button = ModernDangerButton("🚀 네이버 블로그에 발행하기")
        self.publish_button.clicked.connect(self.on_publish_clicked)
        self.publish_button.setEnabled(False)  # 글 작성 완료 후 활성화
        button_layout.addWidget(self.publish_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        card.setLayout(layout)
        
        # 카드 사이즈 최적화 - 기존 카드들과 통일
        # card.setMaximumHeight() 제거 - 자동 사이즈 조정
        
        return card
    
    def create_ai_settings_card(self) -> ModernCard:
        """AI 글쓰기 설정 카드 생성"""
        card = ModernCard("🤖 AI 글쓰기 설정")
        layout = QVBoxLayout()
        layout.setSpacing(tokens.GAP_4)  # 간격을 더 줄여서 더 컴팩트하게
        
        # 간단한 설명
        simple_desc = QLabel("원하는 글쓰기 스타일을 선택하고 설정을 저장하세요")
        simple_desc.setStyleSheet(f"""
            QLabel {{
                color: {ModernStyle.COLORS['primary']};
                font-size: {tokens.get_font_size('normal')}px;
                font-weight: 600;
                padding: 4px 0px;
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
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: {tokens.RADIUS_SM}px;
                background-color: {ModernStyle.COLORS['bg_card']};
                color: {ModernStyle.COLORS['text_primary']};
                font-size: {tokens.get_font_size('normal')}px;
                min-height: 20px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {ModernStyle.COLORS['text_secondary']};
                margin-right: 5px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {ModernStyle.COLORS['bg_card']};
                border: 1px solid {ModernStyle.COLORS['border']};
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
                border: 1px solid {ModernStyle.COLORS['border']};
                border-radius: {tokens.RADIUS_SM}px;
                background-color: {ModernStyle.COLORS['bg_card']};
                color: {ModernStyle.COLORS['text_primary']};
                font-size: {tokens.get_font_size('normal')}px;
                min-height: 20px;
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
        
        # AI 설정 카드는 제일 위에 있어서 높이 제한 필요 (드롭박스 간격 정리)
        card.setMaximumHeight(310)  # 블로그 소개 필드 추가로 높이 40px 증가
        
        return card
    
    def on_content_type_changed(self, index):
        """컨텐츠 유형 변경 시 후기 세부 옵션 표시/숨김"""
        try:
            # 후기/리뷰형(인덱스 0)일 때만 세부 옵션 표시
            if index == 0:  # 후기/리뷰형
                self.review_detail_widget.setVisible(True)
            else:  # 정보/가이드형, 비교/추천형
                self.review_detail_widget.setVisible(False)
        except Exception as e:
            logger.error(f"컨텐츠 유형 변경 처리 오류: {e}")
    
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
        """AI 글쓰기 설정 저장"""
        try:
            settings = self.get_ai_writing_settings()
            
            # 설정을 config 파일에 저장
            from src.foundation.config import config_manager
            api_config = config_manager.load_api_config()
            
            # AI 글쓰기 설정 추가
            api_config.ai_writing_content_type = settings['content_type']
            api_config.ai_writing_content_type_id = settings['content_type_id']
            api_config.ai_writing_tone = settings['tone']
            api_config.ai_writing_tone_id = settings['tone_id']
            api_config.ai_writing_blogger_identity = settings['blogger_identity']
            
            # 후기 세부 옵션이 있는 경우 추가
            if 'review_detail' in settings:
                api_config.ai_writing_review_detail = settings['review_detail']
                api_config.ai_writing_review_detail_id = settings['review_detail_id']
            
            # 설정 저장
            config_manager.save_api_config(api_config)
            
            logger.info(f"AI 글쓰기 설정 저장됨: {settings['content_type']}, {settings['tone']}")
            
            # 메인 UI의 AI 정보 표시 업데이트
            if hasattr(self.parent, 'update_ai_info_display'):
                self.parent.update_ai_info_display()
            
            # 성공 다이얼로그
            TableUIDialogHelper.show_success_dialog(
                self, "설정 저장 완료", 
                f"AI 글쓰기 설정이 저장되었습니다!\n\n컨텐츠 유형: {settings['content_type']}\n말투 스타일: {settings['tone']}"
            )
            
        except Exception as e:
            logger.error(f"AI 글쓰기 설정 저장 실패: {e}")
            TableUIDialogHelper.show_error_dialog(
                self, "저장 실패", f"설정 저장 중 오류가 발생했습니다:\n{e}"
            )
    
    def load_ai_settings(self):
        """저장된 AI 글쓰기 설정 로드"""
        try:
            from src.foundation.config import config_manager
            api_config = config_manager.load_api_config()
            
            # 컨텐츠 유형 로드
            content_type_id = getattr(api_config, 'ai_writing_content_type_id', 1)  # 기본값: 정보/가이드형
            if 0 <= content_type_id <= 2:
                self.content_type_combo.setCurrentIndex(content_type_id)
            
            # 말투 스타일 로드
            tone_id = getattr(api_config, 'ai_writing_tone_id', 1)  # 기본값: 정중한 존댓말체
            if 0 <= tone_id <= 2:
                self.tone_combo.setCurrentIndex(tone_id)
            
            # 블로거 정체성 로드
            blogger_identity = getattr(api_config, 'ai_writing_blogger_identity', '')
            self.blogger_identity_edit.setText(blogger_identity)
            
            # 후기 세부 옵션 로드
            review_detail_id = getattr(api_config, 'ai_writing_review_detail_id', 0)  # 기본값: 내돈내산 후기
            if 0 <= review_detail_id <= 3:
                self.review_detail_combo.setCurrentIndex(review_detail_id)
            
            # 컨텐츠 유형에 따라 후기 세부 옵션 표시/숨김
            self.on_content_type_changed(self.content_type_combo.currentIndex())
            
            logger.info(f"AI 설정 로드됨: 컨텐츠유형={content_type_id}, 말투={tone_id}, 후기세부={review_detail_id}")
            
        except Exception as e:
            logger.error(f"AI 설정 로드 실패: {e}")
    
    def setup_styles(self):
        """스타일 설정"""
        pass
    
    def on_auto_generate_clicked(self):
        """AI 자동 생성 버튼 클릭 처리"""
        try:
            # 메인키워드 확인
            main_keyword = self.main_keyword_input.text().strip()
            if not main_keyword:
                TableUIDialogHelper.show_warning_dialog(
                    self, "입력 오류", "메인키워드를 입력해주세요."
                )
                return
            
            # 보조키워드는 선택사항
            sub_keywords = self.sub_keyword_input.text().strip()
            
            # 버튼 상태 변경
            self.auto_generate_button.setText("🔄 자동 생성 중...")
            self.auto_generate_button.setEnabled(False)
            self.show_results_button.setEnabled(True)  # 바로 활성화
            
            # 1단계: 블로그 분석 시작
            self.start_auto_analysis(main_keyword, sub_keywords)
            
        except Exception as e:
            logger.error(f"AI 자동 생성 시작 오류: {e}")
            self.reset_auto_generate_ui()
    
    def start_auto_analysis(self, main_keyword: str, sub_keywords: str):
        """자동 블로그 분석 시작"""
        try:
            logger.info(f"🚀 자동 블로그 분석 시작: {main_keyword}")
            
            # 분석 준비 - UI 상태 업데이트
            logger.info("분석 준비 중...")
            
            # 워커 생성
            from .worker import create_blog_analysis_worker, WorkerThread
            
            self.analysis_worker = create_blog_analysis_worker(self.parent.service, main_keyword)
            self.analysis_thread = WorkerThread(self.analysis_worker)
            
            # 시그널 연결
            self.analysis_worker.analysis_started.connect(self.on_auto_analysis_started)
            self.analysis_worker.analysis_progress.connect(self.on_auto_analysis_progress)
            self.analysis_worker.analysis_completed.connect(
                lambda blogs: self.on_auto_analysis_completed(blogs, main_keyword, sub_keywords)
            )
            self.analysis_worker.error_occurred.connect(self.on_auto_analysis_error)
            
            # 워커 시작
            self.analysis_thread.start()
            logger.info("✅ 자동 분석 워커 시작됨")
            
        except Exception as e:
            logger.error(f"❌ 자동 분석 시작 실패: {e}")
            self.reset_auto_generate_ui()
    
    def on_auto_analysis_started(self):
        """자동 분석 시작 시그널 처리"""
        logger.info("📊 자동 분석 시작됨")
        # 메인 UI 상태창에 표시
        if hasattr(self, 'parent') and hasattr(self.parent, 'status_label'):
            self.parent.status_label.setText("📊 블로그 분석 시작...")
    
    def on_auto_analysis_progress(self, message: str, progress: int):
        """자동 분석 진행 상황 업데이트"""
        logger.info(f"📝 자동 분석 진행: {message} ({progress}%)")
        # 메인 UI 상태창에 진행 상황 표시
        if hasattr(self, 'parent') and hasattr(self.parent, 'status_label'):
            self.parent.status_label.setText(f"📊 {message} ({progress}%)")
    
    def on_auto_analysis_completed(self, analyzed_blogs: list, main_keyword: str, sub_keywords: str):
        """자동 분석 완료 후 AI 글쓰기 시작"""
        try:
            logger.info(f"✅ 자동 분석 성공! 이제 AI 글쓰기 시작")
            
            # 분석 결과를 테이블에 표시
            analysis_tab = self.result_tabs.analysis_tab
            analysis_tab.populate_blog_table(analyzed_blogs)
            
            # 메인 UI 상태창에 분석 완료 표시
            if hasattr(self, 'parent') and hasattr(self.parent, 'status_label'):
                self.parent.status_label.setText("📊 블로그 분석 완료, AI 글쓰기 시작...")
            
            # AI 프롬프트 생성 및 저장
            self.generate_ai_prompt_for_auto(main_keyword, sub_keywords, analyzed_blogs)
            
            # 글작성 AI 프롬프트 탭에 내용 설정
            if self.ai_prompt_data and 'main_prompt' in self.ai_prompt_data:
                writing_prompt_tab = self.result_tabs.writing_prompt_tab
                writing_prompt_tab.set_prompt_content(self.ai_prompt_data['main_prompt'])
            
            # 2단계: AI 글쓰기 시작
            self.start_auto_writing(main_keyword, sub_keywords, analyzed_blogs)
            
        except Exception as e:
            logger.error(f"자동 분석 완료 처리 중 오류: {e}")
            self.reset_auto_generate_ui()
    
    def on_auto_analysis_error(self, error_message: str):
        """자동 분석 오류 처리"""
        try:
            logger.error(f"❌ 자동 분석 오류: {error_message}")
            
            # 메인 UI 상태창에 오류 표시
            if hasattr(self, 'parent') and hasattr(self.parent, 'status_label'):
                self.parent.status_label.setText("❌ 블로그 분석 오류")
                
            self.reset_auto_generate_ui()
            
            TableUIDialogHelper.show_error_dialog(
                self, "분석 오류", f"블로그 분석 중 오류가 발생했습니다:\n{error_message}"
            )
            
        except Exception as e:
            logger.error(f"자동 분석 오류 처리 중 오류: {e}")
    
    def generate_ai_prompt_for_auto(self, main_keyword: str, sub_keywords: str, analyzed_blogs: list):
        """자동 생성용 AI 프롬프트 생성"""
        try:
            from .ai_prompts import create_ai_request_data
            
            # 현재 UI에서 설정 가져오기
            settings = self.get_ai_writing_settings()
            content_type = settings.get('content_type', '정보/가이드형')
            tone = settings.get('tone', '정중한 존댓말체')
            review_detail = settings.get('review_detail', '')
            
            # AI 요청 데이터 생성 (메인키워드와 보조키워드 분리)
            ai_data = create_ai_request_data(main_keyword, sub_keywords, analyzed_blogs, content_type, tone, review_detail)
            
            if ai_data:
                self.ai_prompt_data = {
                    'main_keyword': main_keyword,
                    'sub_keywords': sub_keywords,
                    'structured_data': ai_data['structured_data'],
                    'main_prompt': ai_data['ai_prompt'],
                    'raw_blogs': analyzed_blogs,
                    'content_type': content_type,
                    'tone': tone,
                    'review_detail': review_detail
                }
                logger.info(f"AI 프롬프트 생성 완료: {main_keyword} + {sub_keywords}")
            else:
                logger.error("AI 프롬프트 생성 실패")
                
        except Exception as e:
            logger.error(f"AI 프롬프트 생성 오류: {e}")
    
    def start_auto_writing(self, main_keyword: str, sub_keywords: str, analyzed_blogs: list):
        """자동 AI 글쓰기 시작"""
        try:
            logger.info("🤖 자동 AI 글쓰기 시작")
            
            # AI 프롬프트 데이터 확인
            if not self.ai_prompt_data:
                raise Exception("AI 프롬프트 데이터가 없습니다")
            
            # 컨텐츠 탭 준비 (별도 창에서 표시될 예정)
            
            # 워커 생성
            from .worker import create_ai_writing_worker, WorkerThread
            
            main_keyword = self.ai_prompt_data['main_keyword']
            sub_keywords = self.ai_prompt_data['sub_keywords']
            structured_data = self.ai_prompt_data['structured_data']
            content_type = self.ai_prompt_data['content_type']
            tone = self.ai_prompt_data['tone']
            review_detail = self.ai_prompt_data['review_detail']
            
            self.ai_writer_worker = create_ai_writing_worker(
                self.parent.service, main_keyword, sub_keywords, structured_data, analyzed_blogs, content_type, tone, review_detail
            )
            self.ai_writer_thread = WorkerThread(self.ai_writer_worker)
            
            # 시그널 연결
            self.ai_writer_worker.writing_started.connect(self.on_auto_writing_started)
            self.ai_writer_worker.writing_completed.connect(self.on_auto_writing_completed)
            self.ai_writer_worker.error_occurred.connect(self.on_auto_writing_error)
            
            # 2단계 파이프라인 시그널 연결
            self.ai_writer_worker.summary_prompt_generated.connect(self.on_summary_prompt_generated)
            self.ai_writer_worker.summary_completed.connect(self.on_summary_completed)
            self.ai_writer_worker.writing_prompt_generated.connect(self.on_writing_prompt_generated)
            
            # 워커 시작
            self.ai_writer_thread.start()
            logger.info("✅ 자동 AI 글쓰기 워커 시작됨")
            
        except Exception as e:
            logger.error(f"❌ 자동 AI 글쓰기 시작 실패: {e}")
            self.reset_auto_generate_ui()
    
    def on_auto_writing_started(self):
        """자동 AI 글쓰기 시작 시그널 처리"""
        logger.info("🤖 자동 AI 글쓰기 시작됨")
        # 메인 UI 상태창에 표시
        if hasattr(self, 'parent') and hasattr(self.parent, 'status_label'):
            self.parent.status_label.setText("🤖 AI가 블로그 글을 생성 중...")
    
    def on_auto_writing_completed(self, generated_content: str):
        """자동 AI 글쓰기 완료 처리"""
        try:
            logger.info("✅ 자동 AI 글쓰기 완료!")
            
            # 생성된 글을 최종 결과 탭에 표시
            writing_result_tab = self.result_tabs.writing_result_tab
            writing_result_tab.set_generated_content(generated_content)
            
            # 발행 버튼 활성화
            self.publish_button.setEnabled(True)
            
            # 메인 UI 상태창에 완료 표시
            if hasattr(self, 'parent') and hasattr(self.parent, 'status_label'):
                self.parent.status_label.setText("✅ AI 글 생성 완료!")
            
            # 버튼 상태 복원
            self.reset_auto_generate_ui()
            
            # 성공 알림 (스크롤 가능한 다이얼로그 사용)
            TableUIDialogHelper.show_scrollable_success_dialog(
                self, "자동 생성 완료", 
                f"AI 블로그 글 자동 생성이 완료되었습니다!\n\n글자수: {len(generated_content.replace(' ', ''))}자\n\n생성된 글을 확인하고 '네이버 블로그에 발행하기' 버튼을 클릭하세요.",
                "🎉"
            )
            
        except Exception as e:
            logger.error(f"자동 AI 글쓰기 완료 처리 중 오류: {e}")
            self.reset_auto_generate_ui()
    
    def on_auto_writing_error(self, error_message: str):
        """자동 AI 글쓰기 오류 처리"""
        try:
            logger.error(f"❌ 자동 AI 글쓰기 오류: {error_message}")
            
            # 메인 UI 상태창에 오류 표시
            if hasattr(self, 'parent') and hasattr(self.parent, 'status_label'):
                self.parent.status_label.setText("❌ AI 글쓰기 오류")
            
            self.reset_auto_generate_ui()
            
            TableUIDialogHelper.show_error_dialog(
                self, "AI 글쓰기 오류", 
                f"AI 글쓰기 중 오류가 발생했습니다:\n{error_message}\n\nAPI 키 설정을 확인해주세요."
            )
            
        except Exception as e:
            logger.error(f"자동 AI 글쓰기 오류 처리 중 오류: {e}")
    
    def reset_auto_generate_ui(self):
        """자동 생성 UI 상태 초기화"""
        self.auto_generate_button.setText("🚀 AI 블로그 글 자동 생성")
        self.auto_generate_button.setEnabled(True)
        
        # 메인 UI 상태 초기화
        if hasattr(self, 'parent') and hasattr(self.parent, 'status_label'):
            self.parent.status_label.setText("대기 중...")
    
    def on_show_results_clicked(self):
        """결과 보기 버튼 클릭 처리 - 별도 창에서 결과 표시"""
        try:
            # 이미 창이 열려있으면 앞으로 가져오기
            if self.results_dialog and self.results_dialog.isVisible():
                self.results_dialog.raise_()
                self.results_dialog.activateWindow()
                return
            
            logger.info("결과 보기 창 열기")
            
            # 별도 창으로 결과 표시
            from PySide6.QtWidgets import QDialog, QVBoxLayout
            
            self.results_dialog = QDialog(self)
            self.results_dialog.setWindowTitle("🎯 블로그 자동화 결과")
            self.results_dialog.setModal(False)  # 비모달 다이얼로그
            self.results_dialog.resize(1000, 700)
            
            # 결과 탭 위젯을 다이얼로그에 추가
            layout = QVBoxLayout()
            layout.addWidget(self.result_tabs)
            self.results_dialog.setLayout(layout)
            
            # 결과 탭 표시
            self.result_tabs.setVisible(True)
            self.result_tabs.setCurrentIndex(0)  # 첫 번째 탭(분석 결과)으로 이동
            
            # 창이 닫힐 때 참조 정리
            def on_dialog_closed():
                self.results_dialog = None
                
            self.results_dialog.finished.connect(on_dialog_closed)
            
            # 다이얼로그 표시
            self.results_dialog.show()
            
            logger.info("결과 보기 창이 열렸습니다")
            
        except Exception as e:
            logger.error(f"결과 보기 창 열기 오류: {e}")
            TableUIDialogHelper.show_error_dialog(
                self, "오류", f"결과 창을 열 수 없습니다:\n{e}"
            )
    
    def on_summary_prompt_generated(self, summary_prompt: str):
        """정보요약 AI 프롬프트 생성 시그널 처리"""
        try:
            logger.info("📋 정보요약 AI 프롬프트 생성됨")
            # 정보요약 AI 프롬프트 탭에 내용 설정
            summary_prompt_tab = self.result_tabs.summary_prompt_tab
            summary_prompt_tab.set_prompt_content(summary_prompt)
        except Exception as e:
            logger.error(f"정보요약 AI 프롬프트 표시 오류: {e}")
    
    def on_summary_completed(self, summary_result: str):
        """정보요약 AI 결과 완료 시그널 처리"""
        try:
            logger.info("📋 정보요약 AI 결과 완료됨")
            # 정보요약 AI 결과 탭에 내용 설정
            summary_result_tab = self.result_tabs.summary_result_tab
            summary_result_tab.set_generated_content(summary_result)
        except Exception as e:
            logger.error(f"정보요약 AI 결과 표시 오류: {e}")
    
    def on_writing_prompt_generated(self, writing_prompt: str):
        """글작성 AI 프롬프트 생성 시그널 처리"""
        try:
            logger.info("📝 글작성 AI 프롬프트 생성됨")
            # 글작성 AI 프롬프트 탭에 내용 설정 (기존 프롬프트 덮어쓰기)
            writing_prompt_tab = self.result_tabs.writing_prompt_tab
            writing_prompt_tab.set_prompt_content(writing_prompt)
        except Exception as e:
            logger.error(f"글작성 AI 프롬프트 표시 오류: {e}")
    
    def on_publish_clicked(self):
        """블로그 발행 시작"""
        try:
            logger.info("네이버 블로그 발행 시작")
            
            # TODO: 실제 발행 로직 구현
            TableUIDialogHelper.show_info_dialog(
                self, "구현 예정", 
                "네이버 블로그 발행 기능은 곧 구현됩니다.\n현재는 UI만 구성된 상태입니다.",
                "🚧"
            )
            
        except Exception as e:
            logger.error(f"블로그 발행 오류: {e}")