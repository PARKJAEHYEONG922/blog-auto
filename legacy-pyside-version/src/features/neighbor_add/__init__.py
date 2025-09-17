"""
네이버 블로그 서로이웃 추가 자동화 모듈
"""

from .service import NeighborAddService
from .ui_main import NeighborAddMainUI


def register(app):
    """메인 앱에 서로이웃추가 모듈 등록"""
    from .ui_main import NeighborAddMainUI
    
    # 서로이웃추가 UI 등록
    neighbor_ui = NeighborAddMainUI()
    app.add_feature_tab(neighbor_ui, '서로이웃 추가')