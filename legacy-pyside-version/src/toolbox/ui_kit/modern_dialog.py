"""
모던한 스타일의 커스텀 다이얼로그들 - 단순화 버전
"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QApplication, QLineEdit, QTextEdit, QScrollArea)
from PySide6.QtCore import Qt, QPoint
from .modern_style import ModernStyle
from . import tokens

class ModernConfirmDialog(QDialog):
    """모던한 확인 다이얼로그 - 단순화"""
    
    def __init__(self, parent=None, title="확인", message="", 
                 confirm_text="확인", cancel_text="취소", icon="❓", position_near_widget=None):
        super().__init__(parent)
        self.title = title
        self.message = message
        self.confirm_text = confirm_text
        self.cancel_text = cancel_text
        self.icon = icon
        self.result_value = False
        self.position_near_widget = position_near_widget
        
        self.setup_ui()
        if self.position_near_widget:
            self.position_near_widget_func()
        else:
            self.center_on_parent()
    
    def setup_ui(self):
        """UI 구성 - 반응형 스케일링 적용"""
        # 화면 스케일 팩터 가져오기
        scale = tokens.get_screen_scale_factor()
        
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        self.setModal(True)  # 모달 다이얼로그로 설정
        self.setWindowTitle(self.title)
        
        # 메인 레이아웃 - 반응형 스케일링 적용
        main_layout = QVBoxLayout()
        margin_h = int(20 * scale)
        margin_v = int(15 * scale)
        spacing = int(15 * scale)
        main_layout.setContentsMargins(margin_h, margin_v, margin_h, margin_v)
        main_layout.setSpacing(spacing)
        
        # 헤더 (아이콘 + 제목) - 반응형 스케일링 적용
        header_layout = QHBoxLayout()
        header_spacing = int(10 * scale)
        header_layout.setSpacing(header_spacing)
        
        # 아이콘 - 반응형 스케일링 적용
        icon_label = QLabel(self.icon)
        icon_font_size = int(16 * scale)
        icon_min_width = int(20 * scale)
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: {icon_font_size}px;
                color: {ModernStyle.COLORS['text_secondary']};
                min-width: {icon_min_width}px;
            }}
        """)
        header_layout.addWidget(icon_label)
        
        # 제목 - 반응형 스케일링 적용
        title_label = QLabel(self.title)
        title_font_size = int(16 * scale)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: {title_font_size}px;
                font-weight: 600;
                color: {ModernStyle.COLORS['text_primary']};
            }}
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        main_layout.addLayout(header_layout)
        
        # 메시지 - 반응형 스케일링 적용
        message_label = QLabel(self.message)
        message_font_size = int(14 * scale)
        message_margin_h = int(20 * scale)
        message_margin_v = int(10 * scale)
        message_padding = int(15 * scale)
        message_radius = int(8 * scale)
        message_border_width = int(1 * scale)
        message_label.setStyleSheet(f"""
            QLabel {{
                font-size: {message_font_size}px;
                color: {ModernStyle.COLORS['text_secondary']};
                line-height: 1.5;
                margin: {message_margin_v}px {message_margin_h}px;
                padding: {message_padding}px;
                background-color: {ModernStyle.COLORS['bg_input']};
                border-radius: {message_radius}px;
                border: {message_border_width}px solid {ModernStyle.COLORS['border']};
            }}
        """)
        message_label.setWordWrap(True)
        message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)  # 텍스트 선택 가능
        main_layout.addWidget(message_label)
        
        main_layout.addStretch()
        
        # 버튼 영역 - 반응형 스케일링 적용
        button_layout = QHBoxLayout()
        button_spacing = int(10 * scale)
        button_layout.setSpacing(button_spacing)
        button_layout.addStretch()
        
        # 취소 버튼 (cancel_text가 None이 아닐 때만 표시)
        if self.cancel_text is not None:
            self.cancel_button = QPushButton(self.cancel_text)
            self.cancel_button.clicked.connect(self.reject)
            # 취소 버튼 스타일 - 반응형 스케일링 적용
            cancel_padding_v = int(10 * scale)
            cancel_padding_h = int(18 * scale)
            cancel_radius = int(6 * scale)
            cancel_font_size = int(13 * scale)
            cancel_min_width = int(80 * scale)
            cancel_border_width = int(1 * scale)
            self.cancel_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ModernStyle.COLORS['bg_input']};
                    color: {ModernStyle.COLORS['text_primary']};
                    border: {cancel_border_width}px solid {ModernStyle.COLORS['border']};
                    padding: {cancel_padding_v}px {cancel_padding_h}px;
                    border-radius: {cancel_radius}px;
                    font-size: {cancel_font_size}px;
                    min-width: {cancel_min_width}px;
                }}
                QPushButton:hover {{
                    background-color: {ModernStyle.COLORS['border']};
                }}
            """)
            button_layout.addWidget(self.cancel_button)
        else:
            self.cancel_button = None
        
        # 확인 버튼
        self.confirm_button = QPushButton(self.confirm_text)
        self.confirm_button.clicked.connect(self.accept)
        # 확인 버튼 스타일 - 반응형 스케일링 적용
        confirm_padding_v = int(10 * scale)
        confirm_padding_h = int(18 * scale)
        confirm_radius = int(6 * scale)
        confirm_font_size = int(13 * scale)
        confirm_min_width = int(80 * scale)
        self.confirm_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernStyle.COLORS['primary']};
                color: white;
                border: none;
                padding: {confirm_padding_v}px {confirm_padding_h}px;
                border-radius: {confirm_radius}px;
                font-size: {confirm_font_size}px;
                font-weight: 500;
                min-width: {confirm_min_width}px;
            }}
            QPushButton:hover {{
                background-color: {ModernStyle.COLORS['primary_hover']};
            }}
            QPushButton:pressed {{
                background-color: {ModernStyle.COLORS['primary_pressed']};
            }}
        """)
        self.confirm_button.setDefault(True)
        button_layout.addWidget(self.confirm_button)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        
        # 동적 크기 계산을 위한 임시 조정
        self.adjustSize()
        
        # 메시지 내용에 따른 동적 크기 설정
        message_lines = self.message.count('\n') + 1
        message_length = len(self.message)
        
        # 기본 크기 설정 - 반응형 스케일링 적용
        base_width = int(400 * scale)
        base_height = int(180 * scale)
        
        # 텍스트 길이에 따른 너비 조정 (최대 600px) - 반응형 스케일링 적용
        if message_length > 100:
            additional_width = min(int(200 * scale), int((message_length - 100) * 2 * scale))
            base_width += additional_width
        
        # 줄 수에 따른 높이 조정 - 반응형 스케일링 적용
        if message_lines > 3:
            additional_height = int((message_lines - 3) * 25 * scale)
            base_height += additional_height
        
        # 최소/최대 크기 설정 - 반응형 스케일링 적용
        final_width = max(int(350 * scale), min(int(600 * scale), base_width))
        final_height = max(int(180 * scale), min(int(400 * scale), base_height))
        
        self.setMinimumWidth(final_width)
        self.setMaximumWidth(final_width + int(50 * scale))  # 약간의 여유 공간
        self.resize(final_width, final_height)
    
    def center_on_parent(self):
        """화면 중앙에 안전하게 위치"""
        screen = QApplication.primaryScreen()
        screen_rect = screen.availableGeometry()
        
        # 화면 중앙에 배치
        center_x = screen_rect.x() + screen_rect.width() // 2 - self.width() // 2
        center_y = screen_rect.y() + screen_rect.height() // 2 - self.height() // 2
        
        # 화면 경계 체크
        if center_x < screen_rect.x():
            center_x = screen_rect.x() + 20
        elif center_x + self.width() > screen_rect.right():
            center_x = screen_rect.right() - self.width() - 20
            
        if center_y < screen_rect.y():
            center_y = screen_rect.y() + 20
        elif center_y + self.height() > screen_rect.bottom():
            center_y = screen_rect.bottom() - self.height() - 20
        
        self.move(center_x, center_y)
    
    def position_near_widget_func(self):
        """특정 위젯 근처에 위치"""
        if self.position_near_widget:
            # 위젯의 글로벌 위치 가져오기
            widget_pos = self.position_near_widget.mapToGlobal(self.position_near_widget.rect().topLeft())
            widget_rect = self.position_near_widget.geometry()
            
            # 다이얼로그를 버튼 아래쪽에 위치
            dialog_x = widget_pos.x() + widget_rect.width() // 2 - self.width() // 2
            dialog_y = widget_pos.y() + widget_rect.height() + 10  # 버튼 아래 10px 간격
            
            # 화면 경계 체크
            screen = QApplication.primaryScreen()
            screen_rect = screen.availableGeometry()
            
            # 화면 오른쪽 경계 체크
            if dialog_x + self.width() > screen_rect.right():
                dialog_x = screen_rect.right() - self.width() - 10
            
            # 화면 왼쪽 경계 체크
            if dialog_x < screen_rect.left():
                dialog_x = screen_rect.left() + 10
            
            # 화면 아래쪽 경계 체크 (버튼 위쪽으로 이동)
            if dialog_y + self.height() > screen_rect.bottom():
                dialog_y = widget_pos.y() - self.height() - 10  # 버튼 위쪽으로
            
            self.move(dialog_x, dialog_y)
        else:
            self.center_on_parent()
    
    def accept(self):
        """확인 버튼 클릭"""
        self.result_value = True
        super().accept()
    
    def reject(self):
        """취소 버튼 클릭"""
        self.result_value = False
        super().reject()
    
    @classmethod
    def question(cls, parent, title, message, confirm_text="확인", cancel_text="취소"):
        """질문 다이얼로그 표시"""
        dialog = cls(parent, title, message, confirm_text, cancel_text, "❓")
        dialog.center_on_parent()
        dialog.exec()
        return dialog.result_value
    
    @classmethod
    def warning(cls, parent, title, message, confirm_text="삭제", cancel_text="취소"):
        """경고 다이얼로그 표시"""
        dialog = cls(parent, title, message, confirm_text, cancel_text, "⚠️")
        dialog.center_on_parent()
        dialog.exec()
        return dialog.result_value

class ModernInfoDialog(QDialog):
    """모던한 정보 다이얼로그 - 단순화"""
    
    def __init__(self, parent=None, title="알림", message="", icon="ℹ️"):
        super().__init__(parent)
        self.title = title
        self.message = message
        self.icon = icon
        
        self.setup_ui()
        self.center_on_parent()
    
    def setup_ui(self):
        """UI 구성 - 반응형 스케일링 적용"""
        # 화면 스케일 팩터 가져오기
        scale = tokens.get_screen_scale_factor()
        
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self.setWindowTitle(self.title)
        self.setModal(True)
        
        # 아이콘별 색상 정의
        if self.icon == "✅":
            icon_color = "#10b981"  # 성공
            bg_color = "#f0fdf4"
            border_color = "#bbf7d0"
        elif self.icon == "❌":
            icon_color = "#ef4444"  # 에러
            bg_color = "#fef2f2"
            border_color = "#fecaca"
        elif self.icon == "⚠️":
            icon_color = "#f59e0b"  # 경고
            bg_color = "#fffbeb"
            border_color = "#fed7aa"
        else:
            icon_color = "#3b82f6"  # 기본 정보
            bg_color = "#f8fafc"
            border_color = "#e2e8f0"
        
        # 메인 레이아웃 - 반응형 스케일링 적용
        layout = QVBoxLayout(self)
        layout_spacing = int(16 * scale)
        margin_h = int(24 * scale)
        margin_v = int(20 * scale)
        layout.setSpacing(layout_spacing)
        layout.setContentsMargins(margin_h, margin_v, margin_h, margin_v)
        
        # 헤더 (아이콘 + 제목) - 반응형 스케일링 적용
        header_layout = QHBoxLayout()
        header_spacing = int(12 * scale)
        header_layout.setSpacing(header_spacing)
        
        # 아이콘 - 반응형 스케일링 적용
        icon_label = QLabel(self.icon)
        icon_font_size = int(20 * scale)
        icon_width = int(24 * scale)
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: {icon_font_size}px;
                color: {icon_color};
                min-width: {icon_width}px;
                max-width: {icon_width}px;
            }}
        """)
        header_layout.addWidget(icon_label)
        
        # 제목 - 반응형 스케일링 적용
        title_label = QLabel(self.title)
        title_font_size = int(16 * scale)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: {title_font_size}px;
                font-weight: 600;
                color: {icon_color};
                margin: 0;
            }}
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # 메시지 - 반응형 스케일링 적용
        message_label = QLabel(self.message)
        message_label.setWordWrap(True)
        message_font_size = int(13 * scale)
        message_padding_v = int(14 * scale)
        message_padding_h = int(16 * scale)
        message_radius = int(6 * scale)
        message_border_width = int(1 * scale)
        message_label.setStyleSheet(f"""
            QLabel {{
                font-size: {message_font_size}px;
                color: #4a5568;
                line-height: 1.6;
                padding: {message_padding_v}px {message_padding_h}px;
                background-color: {bg_color};
                border-radius: {message_radius}px;
                border: {message_border_width}px solid {border_color};
                margin: 0;
            }}
        """)
        message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(message_label)
        
        # 버튼 - 반응형 스케일링 적용
        button_layout = QHBoxLayout()
        button_margin_top = int(8 * scale)
        button_layout.setContentsMargins(0, button_margin_top, 0, 0)
        button_layout.addStretch()
        
        self.ok_button = QPushButton("확인")
        self.ok_button.clicked.connect(self.accept)
        # 확인 버튼 스타일 - 반응형 스케일링 적용
        ok_padding_v = int(8 * scale)
        ok_padding_h = int(20 * scale)
        ok_radius = int(6 * scale)
        ok_font_size = int(13 * scale)
        ok_min_width = int(70 * scale)
        self.ok_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {icon_color};
                color: white;
                border: none;
                padding: {ok_padding_v}px {ok_padding_h}px;
                border-radius: {ok_radius}px;
                font-size: {ok_font_size}px;
                font-weight: 500;
                min-width: {ok_min_width}px;
            }}
            QPushButton:hover {{
                background-color: {icon_color}dd;
            }}
            QPushButton:pressed {{
                background-color: {icon_color}bb;
            }}
        """)
        self.ok_button.setDefault(True)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
        
        # 크기를 내용에 맞게 동적 조정
        self.adjustSize()
        
        # 최소/최대 크기 설정 - 반응형 스케일링 적용
        min_width = int(350 * scale)
        max_width = int(500 * scale)
        min_height = int(150 * scale)
        max_height = int(400 * scale)
        
        # 메시지 길이에 따른 크기 조정
        message_lines = self.message.count('\n') + 1
        message_length = len(self.message)
        
        # 너비 계산 - 반응형 스케일링 적용
        if message_length > 80:
            width = min(max_width, min_width + int((message_length - 80) * 1.5 * scale))
        else:
            width = min_width
            
        # 높이 계산 - 반응형 스케일링 적용
        base_height = int(180 * scale)
        if message_lines > 2:
            height = min(max_height, base_height + int((message_lines - 2) * 20 * scale))
        else:
            height = base_height
            
        self.resize(int(width), int(height))
    
    def center_on_parent(self):
        """화면 중앙에 안전하게 위치"""
        screen = QApplication.primaryScreen()
        screen_rect = screen.availableGeometry()
        
        # 화면 중앙에 배치
        center_x = screen_rect.x() + screen_rect.width() // 2 - self.width() // 2
        center_y = screen_rect.y() + screen_rect.height() // 2 - self.height() // 2
        
        # 화면 경계 체크
        if center_x < screen_rect.x():
            center_x = screen_rect.x() + 20
        elif center_x + self.width() > screen_rect.right():
            center_x = screen_rect.right() - self.width() - 20
            
        if center_y < screen_rect.y():
            center_y = screen_rect.y() + 20
        elif center_y + self.height() > screen_rect.bottom():
            center_y = screen_rect.bottom() - self.height() - 20
        
        self.move(center_x, center_y)
    
    @classmethod
    def success(cls, parent, title, message):
        """성공 다이얼로그 표시"""
        dialog = cls(parent, title, message, "✅")
        dialog.center_on_parent()
        dialog.exec()
        return True
    
    @classmethod
    def warning(cls, parent, title, message, relative_widget=None):
        """경고 다이얼로그 표시 - 특정 위젯 근처에 표시 가능"""
        dialog = cls(parent, title, message, "⚠️")
        
        if relative_widget:
            dialog.position_near_widget(relative_widget)
        else:
            dialog.center_on_parent()
        
        dialog.exec()
        return True
    
    @classmethod
    def error(cls, parent, title, message):
        """에러 다이얼로그 표시"""
        dialog = cls(parent, title, message, "❌")
        dialog.center_on_parent()
        dialog.exec()
        return True
    
    def position_near_widget(self, widget):
        """특정 위젯 근처에 다이얼로그 위치"""
        if not widget:
            self.center_on_parent()
            return
            
        try:
            # 위젯의 전역 좌표 계산
            widget_pos = widget.mapToGlobal(widget.rect().topLeft())
            widget_bottom = widget_pos.y() + widget.height()
            widget_center_x = widget_pos.x() + widget.width() // 2
            
            # 다이얼로그를 위젯 바로 아래 중앙에 위치
            dialog_x = widget_center_x - self.width() // 2
            dialog_y = widget_bottom + 10  # 위젯 아래 10px 간격
            
            # 화면 경계 체크
            screen = QApplication.primaryScreen()
            screen_rect = screen.availableGeometry()
            
            # x 좌표 조정 (화면 밖으로 나가지 않도록)
            if dialog_x < screen_rect.x():
                dialog_x = screen_rect.x() + 10
            elif dialog_x + self.width() > screen_rect.right():
                dialog_x = screen_rect.right() - self.width() - 10
                
            # y 좌표 조정 (화면 아래로 나가면 위젯 위로)
            if dialog_y + self.height() > screen_rect.bottom():
                dialog_y = widget_pos.y() - self.height() - 10
                
            self.move(dialog_x, dialog_y)
            
        except Exception as e:
            print(f"위젯 근처 위치 설정 실패: {e}")
            self.center_on_parent()


class ModernHelpDialog(QDialog):
    """사용법 전용 다이얼로그 - 동적 크기 조정 및 위치 지정 가능"""
    
    def __init__(self, parent=None, title="사용법", message="", button_pos=None):
        super().__init__(parent)
        self.title = title
        self.message = message
        self.button_pos = button_pos
        
        self.setup_ui()
        self.position_dialog()
    
    def setup_ui(self):
        """UI 구성 - 반응형 스케일링 적용"""
        # 화면 스케일 팩터 가져오기
        scale = tokens.get_screen_scale_factor()
        
        self.setWindowFlags(Qt.Dialog)
        self.setWindowTitle(self.title)
        
        # 메인 레이아웃 - 반응형 스케일링 적용
        layout = QVBoxLayout()
        margin_h = int(20 * scale)
        margin_v = int(15 * scale)
        layout_spacing = int(15 * scale)
        layout.setContentsMargins(margin_h, margin_v, margin_h, margin_v)
        layout.setSpacing(layout_spacing)
        
        # 헤더 - 반응형 스케일링 적용
        header_layout = QHBoxLayout()
        header_spacing = int(10 * scale)
        header_layout.setSpacing(header_spacing)
        
        # 아이콘 - 반응형 스케일링 적용
        icon_label = QLabel("📖")
        icon_font_size = int(20 * scale)
        icon_radius = int(8 * scale)
        icon_padding = int(8 * scale)
        icon_min_width = int(24 * scale)
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: {icon_font_size}px;
                color: {ModernStyle.COLORS['primary']};
                background-color: {ModernStyle.COLORS['primary']}15;
                border-radius: {icon_radius}px;
                padding: {icon_padding}px;
                min-width: {icon_min_width}px;
                qproperty-alignment: AlignCenter;
            }}
        """)
        header_layout.addWidget(icon_label)
        
        # 제목 - 반응형 스케일링 적용
        title_label = QLabel(self.title)
        title_font_size = int(17 * scale)
        title_margin_left = int(4 * scale)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: {title_font_size}px;
                font-weight: 700;
                color: {ModernStyle.COLORS['text_primary']};
                margin-left: {title_margin_left}px;
            }}
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # 메시지 - 반응형 스케일링 적용
        message_label = QLabel()
        message_label.setText(self.message)
        message_font_size = int(13 * scale)
        message_margin_lr = int(4 * scale)
        message_radius = int(8 * scale)
        message_padding = int(18 * scale)
        message_border_width = int(1 * scale)
        message_label.setStyleSheet(f"""
            QLabel {{
                font-size: {message_font_size}px;
                color: {ModernStyle.COLORS['text_secondary']};
                line-height: 1.6;
                margin-left: {message_margin_lr}px;
                margin-right: {message_margin_lr}px;
                background-color: {ModernStyle.COLORS['bg_input']};
                border-radius: {message_radius}px;
                padding: {message_padding}px;
                border: {message_border_width}px solid {ModernStyle.COLORS['border']};
            }}
        """)
        message_label.setWordWrap(True)
        message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(message_label)
        
        # 확인 버튼
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        ok_button = QPushButton("확인")
        ok_button.clicked.connect(self.accept)
        # 확인 버튼 스타일 - 반응형 스케일링 적용
        ok_padding_v = int(10 * scale)
        ok_padding_h = int(24 * scale)
        ok_radius = int(6 * scale)
        ok_font_size = int(13 * scale)
        ok_min_width = int(80 * scale)
        ok_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernStyle.COLORS['primary']};
                color: white;
                border: none;
                padding: {ok_padding_v}px {ok_padding_h}px;
                border-radius: {ok_radius}px;
                font-size: {ok_font_size}px;
                font-weight: 600;
                min-width: {ok_min_width}px;
            }}
            QPushButton:hover {{
                background-color: {ModernStyle.COLORS['primary_hover']};
            }}
            QPushButton:pressed {{
                background-color: {ModernStyle.COLORS['primary_pressed']};
            }}
        """)
        ok_button.setDefault(True)
        button_layout.addWidget(ok_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # 크기를 내용에 맞게 조정 - 반응형 스케일링 적용
        self.adjustSize()
        self.setMinimumWidth(int(500 * scale))
        self.setMaximumWidth(int(600 * scale))
        self.setMaximumHeight(int(700 * scale))
    
    def position_dialog(self):
        """버튼 위치 근처에 다이얼로그 표시"""
        if self.button_pos and self.parent():
            # 버튼 위치를 전역 좌표로 변환
            global_pos = self.parent().mapToGlobal(self.button_pos)
            
            # 화면 크기 가져오기
            screen = QApplication.primaryScreen()
            screen_rect = screen.availableGeometry()
            
            # 다이얼로그가 화면을 벗어나지 않도록 조정
            x = global_pos.x() + 30  # 버튼 오른쪽에 표시
            y = global_pos.y() - 20  # 버튼 위쪽에 약간 겹치게
            
            # 화면 경계 검사
            if x + self.width() > screen_rect.right():
                x = global_pos.x() - self.width() - 10  # 버튼 왼쪽에 표시
            if y + self.height() > screen_rect.bottom():
                y = screen_rect.bottom() - self.height() - 10
            if y < screen_rect.top():
                y = screen_rect.top() + 10
            
            self.move(x, y)
        else:
            # 기본 중앙 정렬
            self.center_on_parent()
    
    def center_on_parent(self):
        """부모 윈도우 중앙에 위치"""
        if self.parent():
            parent_geo = self.parent().geometry()
            parent_pos = self.parent().mapToGlobal(parent_geo.topLeft())
            
            center_x = parent_pos.x() + parent_geo.width() // 2 - self.width() // 2
            center_y = parent_pos.y() + parent_geo.height() // 2 - self.height() // 2
            self.move(center_x, center_y)
        else:
            screen = QApplication.primaryScreen()
            screen_rect = screen.availableGeometry()
            center_x = screen_rect.x() + screen_rect.width() // 2 - self.width() // 2
            center_y = screen_rect.y() + screen_rect.height() // 2 - self.height() // 2
            self.move(center_x, center_y)
    
    @classmethod
    def show_help(cls, parent, title, message, button_widget=None):
        """도움말 다이얼로그 표시"""
        button_pos = None
        if button_widget:
            # 버튼의 중앙 위치 계산
            button_rect = button_widget.geometry()
            button_pos = button_rect.center()
        
        dialog = cls(parent, title, message, button_pos)
        dialog.exec()
        return True


class ModernTextInputDialog(QDialog):
    """모던한 텍스트 입력 다이얼로그"""
    
    def __init__(self, parent=None, title="입력", message="", default_text="", 
                 placeholder="", multiline=False):
        super().__init__(parent)
        self.title = title
        self.message = message
        self.default_text = default_text
        self.placeholder = placeholder
        self.multiline = multiline
        self.result_text = ""
        self.result_ok = False
        
        self.setup_ui()
        self.center_on_parent()
    
    def setup_ui(self):
        """UI 구성 - 반응형 스케일링 적용"""
        # 화면 스케일 팩터 가져오기
        scale = tokens.get_screen_scale_factor()
        
        self.setWindowFlags(Qt.Dialog)
        self.setWindowTitle(self.title)
        
        # 메인 레이아웃 - 반응형 스케일링 적용
        main_layout = QVBoxLayout()
        margin_h = int(25 * scale)
        margin_v = int(20 * scale)
        spacing = int(15 * scale)
        main_layout.setContentsMargins(margin_h, margin_v, margin_h, margin_v)
        main_layout.setSpacing(spacing)
        
        # 제목 - 반응형 스케일링 적용
        if self.message:
            title_label = QLabel(self.message)
            title_font_size = tokens.fpx(14)
            title_margin_bottom = int(5 * scale)
            title_label.setStyleSheet(f"""
                QLabel {{
                    font-size: {title_font_size}px;
                    color: {ModernStyle.COLORS['text_primary']};
                    font-weight: 500;
                    margin-bottom: {title_margin_bottom}px;
                }}
            """)
            title_label.setWordWrap(True)
            main_layout.addWidget(title_label)
        
        # 입력 필드 - 반응형 스케일링 적용
        if self.multiline:
            self.text_input = QTextEdit()
            self.text_input.setPlainText(self.default_text)
            multiline_min_height = int(120 * scale)
            self.text_input.setMinimumHeight(multiline_min_height)
            if self.placeholder:
                self.text_input.setPlaceholderText(self.placeholder)
        else:
            self.text_input = QLineEdit()
            self.text_input.setText(self.default_text)
            if self.placeholder:
                self.text_input.setPlaceholderText(self.placeholder)
            self.text_input.selectAll()
        
        # 입력 필드 스타일 - 반응형 스케일링 적용
        input_padding_v = int(10 * scale)
        input_padding_h = int(12 * scale)
        input_border_width = int(2 * scale)
        input_radius = int(6 * scale)
        input_font_size = tokens.fpx(13)
        input_style = f"""
            QLineEdit, QTextEdit {{
                padding: {input_padding_v}px {input_padding_h}px;
                border: {input_border_width}px solid {ModernStyle.COLORS['border']};
                border-radius: {input_radius}px;
                font-size: {input_font_size}px;
                background-color: white;
                color: {ModernStyle.COLORS['text_primary']};
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border-color: {ModernStyle.COLORS['primary']};
                outline: none;
            }}
        """
        self.text_input.setStyleSheet(input_style)
        main_layout.addWidget(self.text_input)
        
        # 버튼 영역 - 반응형 스케일링 적용
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 취소 버튼 - 반응형 스케일링 적용
        self.cancel_button = QPushButton("취소")
        self.cancel_button.clicked.connect(self.reject)
        cancel_padding_v = int(10 * scale)
        cancel_padding_h = int(20 * scale)
        cancel_border_width = int(1 * scale)
        cancel_radius = int(6 * scale)
        cancel_font_size = tokens.fpx(13)
        cancel_min_width = int(80 * scale)
        cancel_margin_right = int(10 * scale)
        self.cancel_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernStyle.COLORS['bg_secondary']};
                color: {ModernStyle.COLORS['text_secondary']};
                border: {cancel_border_width}px solid {ModernStyle.COLORS['border']};
                padding: {cancel_padding_v}px {cancel_padding_h}px;
                border-radius: {cancel_radius}px;
                font-size: {cancel_font_size}px;
                min-width: {cancel_min_width}px;
                margin-right: {cancel_margin_right}px;
            }}
            QPushButton:hover {{
                background-color: {ModernStyle.COLORS['border']};
            }}
        """)
        button_layout.addWidget(self.cancel_button)
        
        # 확인 버튼 - 반응형 스케일링 적용
        self.confirm_button = QPushButton("확인")
        self.confirm_button.clicked.connect(self.accept)
        confirm_padding_v = int(10 * scale)
        confirm_padding_h = int(20 * scale)
        confirm_radius = int(6 * scale)
        confirm_font_size = tokens.fpx(13)
        confirm_min_width = int(80 * scale)
        self.confirm_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernStyle.COLORS['primary']};
                color: white;
                border: none;
                padding: {confirm_padding_v}px {confirm_padding_h}px;
                border-radius: {confirm_radius}px;
                font-size: {confirm_font_size}px;
                font-weight: 500;
                min-width: {confirm_min_width}px;
            }}
            QPushButton:hover {{
                background-color: {ModernStyle.COLORS['primary_hover']};
            }}
            QPushButton:pressed {{
                background-color: {ModernStyle.COLORS['primary_pressed']};
            }}
        """)
        self.confirm_button.setDefault(True)
        button_layout.addWidget(self.confirm_button)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        
        # 크기 설정 - 반응형 스케일링 적용
        min_width = int(400 * scale)
        max_width = int(600 * scale)
        self.setMinimumWidth(min_width)
        self.setMaximumWidth(max_width)
        if self.multiline:
            min_height_multiline = int(220 * scale)
            self.setMinimumHeight(min_height_multiline)
        else:
            self.adjustSize()
    
    def center_on_parent(self):
        """부모 윈도우 중앙에 위치"""
        if self.parent():
            # 부모 위젯의 글로벌 위치와 크기 계산
            parent_pos = self.parent().mapToGlobal(QPoint(0, 0))
            parent_size = self.parent().size()
            
            # 다이얼로그 크기 확인
            self.adjustSize()
            dialog_size = self.size()
            
            # 중앙 위치 계산
            center_x = parent_pos.x() + parent_size.width() // 2 - dialog_size.width() // 2
            center_y = parent_pos.y() + parent_size.height() // 2 - dialog_size.height() // 2
            self.move(center_x, center_y)
        else:
            screen = QApplication.primaryScreen()
            screen_rect = screen.availableGeometry()
            center_x = screen_rect.x() + screen_rect.width() // 2 - self.width() // 2
            center_y = screen_rect.y() + screen_rect.height() // 2 - self.height() // 2
            self.move(center_x, center_y)
    
    def accept(self):
        """확인 버튼 클릭"""
        if self.multiline:
            self.result_text = self.text_input.toPlainText()
        else:
            self.result_text = self.text_input.text()
        self.result_ok = True
        super().accept()
    
    def reject(self):
        """취소 버튼 클릭"""
        self.result_text = ""
        self.result_ok = False
        super().reject()
    
    @classmethod
    def getText(cls, parent, title, message, default_text="", placeholder=""):
        """텍스트 입력 다이얼로그 표시"""
        dialog = cls(parent, title, message, default_text, placeholder, False)
        dialog.exec()
        return dialog.result_text, dialog.result_ok
    
    @classmethod
    def getMultilineText(cls, parent, title, message, default_text="", placeholder=""):
        """여러 줄 텍스트 입력 다이얼로그 표시"""
        dialog = cls(parent, title, message, default_text, placeholder, True)
        dialog.exec()
        return dialog.result_text, dialog.result_ok


# ModernProjectUrlDialog는 features/rank_tracking/dialogs.py로 이동됨


class ModernSaveCompletionDialog(QDialog):
    """저장 완료 다이얼로그 - 닫기 및 폴더 열기 버튼"""
    
    def __init__(self, parent=None, title="저장 완료", message="", file_path=""):
        super().__init__(parent)
        self.title = title
        self.message = message
        self.file_path = file_path
        self.result_open_folder = False
        
        self.setup_ui()
        self.center_on_parent()
    
    def setup_ui(self):
        """UI 구성 - 반응형 스케일링 적용"""
        # 화면 스케일 팩터 가져오기
        scale = tokens.get_screen_scale_factor()
        
        self.setWindowFlags(Qt.Dialog)
        self.setWindowTitle(self.title)
        
        # 메인 레이아웃 - 반응형 스케일링 적용
        main_layout = QVBoxLayout()
        margin_h = int(25 * scale)
        margin_v = int(20 * scale)
        layout_spacing = int(15 * scale)
        main_layout.setContentsMargins(margin_h, margin_v, margin_h, margin_v)
        main_layout.setSpacing(layout_spacing)
        
        # 헤더 (아이콘 + 제목) - 반응형 스케일링 적용
        header_layout = QHBoxLayout()
        header_spacing = int(12 * scale)
        header_layout.setSpacing(header_spacing)
        
        # 성공 아이콘
        icon_label = QLabel("✅")
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: 24px;
                min-width: 30px;
                max-width: 30px;
            }}
        """)
        header_layout.addWidget(icon_label)
        
        # 제목
        title_label = QLabel(self.title)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                font-weight: 600;
                color: {ModernStyle.COLORS['text_primary']};
            }}
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        main_layout.addLayout(header_layout)
        
        # 메시지
        message_label = QLabel(self.message)
        message_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: {ModernStyle.COLORS['text_secondary']};
                line-height: 1.6;
                margin: 10px 20px 10px 42px;
                padding: 15px;
                background-color: {ModernStyle.COLORS['bg_input']};
                border-radius: 8px;
                border-left: 4px solid {ModernStyle.COLORS['success']};
            }}
        """)
        message_label.setWordWrap(True)
        message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        main_layout.addWidget(message_label)
        
        # 파일 경로 표시 (있는 경우)
        if self.file_path:
            path_label = QLabel(f"📁 저장 위치: {self.file_path}")
            path_label.setStyleSheet(f"""
                QLabel {{
                    font-size: 12px;
                    color: {ModernStyle.COLORS['text_muted']};
                    margin: 5px 20px 10px 42px;
                    padding: 8px 10px;
                    background-color: {ModernStyle.COLORS['bg_secondary']};
                    border-radius: 6px;
                    font-family: 'Consolas', 'Monaco', monospace;
                }}
            """)
            path_label.setWordWrap(True)
            path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            main_layout.addWidget(path_label)
        
        main_layout.addStretch()
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        # 닫기 버튼
        self.close_button = QPushButton("닫기")
        self.close_button.clicked.connect(self.reject)
        self.close_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernStyle.COLORS['bg_input']};
                color: {ModernStyle.COLORS['text_primary']};
                border: 1px solid {ModernStyle.COLORS['border']};
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {ModernStyle.COLORS['border']};
                color: {ModernStyle.COLORS['text_primary']};
            }}
        """)
        button_layout.addWidget(self.close_button)
        
        # 폴더 열기 버튼 (파일 경로가 있을 때만 표시)
        if self.file_path:
            self.open_folder_button = QPushButton("📁 폴더 열기")
            self.open_folder_button.clicked.connect(self.open_folder)
            self.open_folder_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ModernStyle.COLORS['success']};
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    font-size: 13px;
                    font-weight: 600;
                    min-width: 120px;
                }}
                QPushButton:hover {{
                    background-color: #059669;
                    color: white;
                }}
            """)
            self.open_folder_button.setDefault(True)
            button_layout.addWidget(self.open_folder_button)
        else:
            # 파일 경로가 없으면 닫기 버튼을 기본 버튼으로 설정
            self.close_button.setDefault(True)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        
        # 크기 설정
        self.adjustSize()
        self.setMinimumWidth(450)
        self.setMaximumWidth(600)
        self.setMinimumHeight(200)
        
        # 내용에 맞는 크기 계산
        required_height = main_layout.sizeHint().height() + 50
        required_width = max(450, min(600, main_layout.sizeHint().width() + 60))
        self.resize(required_width, max(200, required_height))
    
    def center_on_parent(self):
        """화면 중앙에 안전하게 위치"""
        screen = QApplication.primaryScreen()
        screen_rect = screen.availableGeometry()
        
        # 화면 중앙에 배치
        center_x = screen_rect.x() + screen_rect.width() // 2 - self.width() // 2
        center_y = screen_rect.y() + screen_rect.height() // 2 - self.height() // 2
        
        # 화면 경계 체크
        if center_x < screen_rect.x():
            center_x = screen_rect.x() + 20
        elif center_x + self.width() > screen_rect.right():
            center_x = screen_rect.right() - self.width() - 20
            
        if center_y < screen_rect.y():
            center_y = screen_rect.y() + 20
        elif center_y + self.height() > screen_rect.bottom():
            center_y = screen_rect.bottom() - self.height() - 20
        
        self.move(center_x, center_y)
    
    def position_near_widget(self, widget):
        """특정 위젯 근처에 다이얼로그 위치"""
        if not widget:
            self.center_on_parent()
            return
            
        try:
            # 위젯의 전역 좌표 계산
            widget_pos = widget.mapToGlobal(widget.rect().topLeft())
            widget_bottom = widget_pos.y() + widget.height()
            widget_center_x = widget_pos.x() + widget.width() // 2
            
            # 다이얼로그를 위젯 위쪽에 위치 (400px 더 위로)
            dialog_x = widget_center_x - self.width() // 2
            dialog_y = widget_pos.y() - self.height() - 400  # 위젯 위쪽 400px 간격
            
            # 화면 경계 체크
            screen = QApplication.primaryScreen()
            screen_rect = screen.availableGeometry()
            
            # x 좌표 조정 (화면 밖으로 나가지 않도록)
            if dialog_x < screen_rect.x():
                dialog_x = screen_rect.x() + 10
            elif dialog_x + self.width() > screen_rect.right():
                dialog_x = screen_rect.right() - self.width() - 10
                
            # y 좌표 조정 (화면 위로 나가면 아래로 이동)
            if dialog_y < screen_rect.top():
                dialog_y = widget_bottom + 15  # 위젯 아래 15px로 이동
                
            self.move(dialog_x, dialog_y)
            
        except Exception as e:
            print(f"위젯 근처 위치 설정 실패: {e}")
            self.center_on_parent()
    
    def open_folder(self):
        """폴더 열기"""
        if self.file_path:
            import os
            import subprocess
            import platform
            
            try:
                # 파일 경로를 절대 경로로 변환
                abs_file_path = os.path.abspath(self.file_path)
                folder_path = os.path.dirname(abs_file_path)
                
                # Windows에서만 폴더 열기 (단순하게)
                if platform.system() == "Windows":
                    # 폴더만 간단하게 열기 (중복 방지)
                    os.startfile(folder_path)
                    
                elif platform.system() == "Darwin":  # macOS
                    if os.path.exists(abs_file_path):
                        subprocess.run(['open', '-R', abs_file_path])
                    else:
                        subprocess.run(['open', folder_path])
                        
                else:  # Linux
                    subprocess.run(['xdg-open', folder_path])
                
                self.result_open_folder = True
                
            except Exception as e:
                print(f"폴더 열기 실패: {e}")
                # 최후의 수단: 기본 파일 관리자로 폴더 열기
                try:
                    folder_path = os.path.dirname(os.path.abspath(self.file_path))
                    if platform.system() == "Windows":
                        os.startfile(folder_path)
                    elif platform.system() == "Darwin":
                        subprocess.run(['open', folder_path])
                    else:
                        subprocess.run(['xdg-open', folder_path])
                except Exception as e2:
                    print(f"최후 폴더 열기도 실패: {e2}")
        
        self.accept()
    
    def reject(self):
        """닫기 버튼 클릭"""
        self.result_open_folder = False
        super().reject()
    
    def accept(self):
        """폴더 열기 버튼 클릭"""
        super().accept()
    
    @classmethod
    def show_save_completion(cls, parent, title="저장 완료", message="", file_path=""):
        """저장 완료 다이얼로그 표시"""
        dialog = cls(parent, title, message, file_path)
        dialog.exec()


class ModernScrollableDialog(QDialog):
    """스크롤 가능한 긴 메시지용 모던 다이얼로그"""
    
    def __init__(self, parent=None, title="정보", message="", 
                 confirm_text="확인", cancel_text=None, icon="ℹ️"):
        super().__init__(parent)
        self.title = title
        self.message = message
        self.confirm_text = confirm_text
        self.cancel_text = cancel_text
        self.icon = icon
        self.result_value = False
        
        self.setup_ui()
    
    def setup_ui(self):
        """UI 구성 - 스크롤 가능한 메시지"""
        # 화면 스케일 팩터 가져오기
        scale = tokens.get_screen_scale_factor()
        
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        self.setModal(True)
        self.setWindowTitle(self.title)
        
        # 다이얼로그 크기 설정 (화면 크기에 비례하되 적절한 제한)
        screen = QApplication.primaryScreen()
        screen_size = screen.availableGeometry()
        
        # 화면 크기의 60% 너비, 70% 높이로 설정 (최소/최대 제한)
        dialog_width = min(int(screen_size.width() * 0.6), int(700 * scale))
        dialog_width = max(dialog_width, int(500 * scale))  # 최소 너비
        
        dialog_height = min(int(screen_size.height() * 0.7), int(600 * scale))  
        dialog_height = max(dialog_height, int(400 * scale))  # 최소 높이
        
        self.setFixedSize(dialog_width, dialog_height)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        margin_h = int(20 * scale)
        margin_v = int(15 * scale)
        spacing = int(15 * scale)
        main_layout.setContentsMargins(margin_h, margin_v, margin_h, margin_v)
        main_layout.setSpacing(spacing)
        
        # 헤더 (아이콘 + 제목)
        header_layout = QHBoxLayout()
        header_spacing = int(10 * scale)
        header_layout.setSpacing(header_spacing)
        
        # 아이콘
        icon_label = QLabel(self.icon)
        icon_size = int(24 * scale)
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: {icon_size}px;
                min-width: {icon_size}px;
                max-width: {icon_size}px;
            }}
        """)
        header_layout.addWidget(icon_label)
        
        # 제목
        title_label = QLabel(self.title)
        title_font_size = int(16 * scale)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: {title_font_size}px;
                font-weight: 600;
                color: {ModernStyle.COLORS['text_primary']};
            }}
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        main_layout.addLayout(header_layout)
        
        # 스크롤 가능한 메시지 영역
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 메시지 라벨
        message_label = QLabel(self.message)
        message_font_size = int(14 * scale)
        message_padding = int(15 * scale)
        message_radius = int(8 * scale)
        message_border_width = int(1 * scale)
        message_label.setStyleSheet(f"""
            QLabel {{
                font-size: {message_font_size}px;
                color: {ModernStyle.COLORS['text_secondary']};
                line-height: 1.5;
                padding: {message_padding}px;
                background-color: {ModernStyle.COLORS['bg_input']};
                border-radius: {message_radius}px;
                border: {message_border_width}px solid {ModernStyle.COLORS['border']};
            }}
        """)
        message_label.setWordWrap(True)
        message_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)
        message_label.setAlignment(Qt.AlignTop)
        
        # HTML 지원 및 외부 링크 활성화
        message_label.setTextFormat(Qt.RichText)
        message_label.setOpenExternalLinks(True)
        
        # 스크롤 영역에 메시지 라벨 추가
        scroll_area.setWidget(message_label)
        main_layout.addWidget(scroll_area)
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        button_spacing = int(10 * scale)
        button_layout.setSpacing(button_spacing)
        button_layout.addStretch()
        
        # 취소 버튼 (cancel_text가 None이 아닐 때만 표시)
        if self.cancel_text is not None:
            self.cancel_button = QPushButton(self.cancel_text)
            self.cancel_button.clicked.connect(self.reject)
            cancel_padding_v = int(10 * scale)
            cancel_padding_h = int(18 * scale)
            cancel_radius = int(6 * scale)
            self.cancel_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {ModernStyle.COLORS['bg_secondary']};
                    color: {ModernStyle.COLORS['text_primary']};
                    border: none;
                    border-radius: {cancel_radius}px;
                    padding: {cancel_padding_v}px {cancel_padding_h}px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: {ModernStyle.COLORS['bg_muted']};
                }}
            """)
            button_layout.addWidget(self.cancel_button)
        
        # 확인 버튼
        self.confirm_button = QPushButton(self.confirm_text)
        self.confirm_button.clicked.connect(self.accept)
        confirm_padding_v = int(10 * scale)
        confirm_padding_h = int(18 * scale)
        confirm_radius = int(6 * scale)
        self.confirm_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {ModernStyle.COLORS['primary']};
                color: white;
                border: none;
                border-radius: {confirm_radius}px;
                padding: {confirm_padding_v}px {confirm_padding_h}px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {ModernStyle.COLORS['primary_hover']};
            }}
        """)
        button_layout.addWidget(self.confirm_button)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
    
    def showEvent(self, event):
        """다이얼로그가 표시될 때 중앙 정렬"""
        super().showEvent(event)
        self.center_on_parent()
    
    def center_on_parent(self):
        """화면 중앙에 안전하게 위치"""
        screen = QApplication.primaryScreen()
        screen_rect = screen.availableGeometry()
        
        # 화면 중앙에 배치
        center_x = screen_rect.x() + screen_rect.width() // 2 - self.width() // 2
        center_y = screen_rect.y() + screen_rect.height() // 2 - self.height() // 2
        
        # 화면 경계 체크
        if center_x < screen_rect.x():
            center_x = screen_rect.x() + 20
        elif center_x + self.width() > screen_rect.right():
            center_x = screen_rect.right() - self.width() - 20
            
        if center_y < screen_rect.y():
            center_y = screen_rect.y() + 20
        elif center_y + self.height() > screen_rect.bottom():
            center_y = screen_rect.bottom() - self.height() - 20
        
        self.move(center_x, center_y)
    
    def accept(self):
        """확인 버튼 클릭"""
        self.result_value = True
        super().accept()
    
    def reject(self):
        """취소/닫기 버튼 클릭"""
        self.result_value = False
        super().reject()