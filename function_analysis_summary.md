# 블로그자동화 프로젝트 함수 분석 결과

## 개요
전체 112개의 Python 파일을 분석하여 중복 함수와 미사용 함수를 찾았습니다.

## 중복 함수 분석 (6개)

### 1. 즉시 정리 권장
다음 함수들은 다른 파일 간 중복 정의로 정리가 필요합니다:

#### main 함수
- `analyze_functions.py:302`
- `main.py:36`
- **권장**: analyze_functions.py의 main 함수를 다른 이름으로 변경

#### handle_web_automation_errors 함수  
- `src\features\blog_automation\adapters.py:25`
- `src\features\blog_automation\adapters_selenium_backup.py:22`
- **권장**: adapters_selenium_backup.py는 백업 파일이므로 삭제 검토

#### decorator 함수
- `src\features\blog_automation\adapters.py:27`
- `src\features\blog_automation\adapters_selenium_backup.py:24`  
- `src\foundation\http_client.py:22`
- **권장**: 공통 데코레이터는 foundation/http_client.py에만 유지

#### wrapper 함수
- `src\features\blog_automation\adapters.py:29`
- `src\features\blog_automation\adapters_selenium_backup.py:26`
- `src\foundation\exceptions.py:384`
- `src\foundation\http_client.py:24`
- **권장**: 공통 wrapper는 foundation에만 유지

#### create_blog_adapter 함수
- `src\features\blog_automation\adapters.py:2618`
- `src\features\blog_automation\adapters_selenium_backup.py:1396`
- **권장**: 백업 파일의 중복 삭제

#### get_keyword_tool_client 함수
- `src\vendors\naver\client_factory.py:241`
- `src\vendors\naver\searchad\keyword_client.py:125`
- **권장**: client_factory.py의 함수만 유지

## 미사용 함수 분석 (324개)

### 안전하게 삭제 가능 (16개)
다음 함수들은 private 메서드이거나 테스트 함수로 안전하게 삭제 가능합니다:

- `_wait_and_click_element` - adapters.py와 adapters_selenium_backup.py에서 중복
- `_monitor_two_factor_auth` - worker.py에서 중복  
- `_extract_*` 관련 private 메서드들 - neighbor_add/adapters.py
- `__post_init__`, `__lt__`, `__aenter__`, `__aexit__` 등 매직 메서드들

### 검토 후 삭제 권장 (308개)
다음 범주의 함수들은 검토 후 삭제를 권장합니다:

#### API 관련 함수들
- `apply_*_api`, `delete_*_api` 등 API 설정 관련 함수들
- `show_*_help` 도움말 관련 함수들
- `get_supported_models`, `get_model_info` 등 모델 정보 함수들

#### UI 이벤트 핸들러들  
- `on_*_clicked`, `on_*_completed` 등 이벤트 핸들러들
- `set_status`, `copy_content` 등 UI 업데이트 함수들

#### 데이터베이스 유틸리티들
- `get_*`, `add_*`, `update_*`, `delete_*` 등 DB 접근 함수들
- 사용되지 않는 테이블 관련 메서드들

#### 포맷팅/유틸리티 함수들
- `format_*` 관련 포맷팅 함수들
- `validate_*` 검증 함수들
- `extract_*` 추출 관련 함수들

## 정리 우선순위

### 1순위: 중복 함수 정리
1. `adapters_selenium_backup.py` 파일 전체 삭제 검토
2. foundation 모듈의 공통 함수들로 통합
3. analyze_functions.py의 main 함수명 변경

### 2순위: 명확한 미사용 함수 삭제  
1. private 메서드 중 실제 사용되지 않는 것들
2. 중복된 유틸리티 함수들
3. 사용되지 않는 API wrapper 함수들

### 3순위: 조심스러운 검토 필요
1. UI 이벤트 핸들러들 (동적 호출 가능성)
2. 데이터베이스 유틸리티들 (미래 사용 가능성)
3. 플러그인/확장 포인트가 될 수 있는 함수들

## 권장 사항

### 즉시 적용 가능
1. `adapters_selenium_backup.py` 파일 삭제 (백업이므로)
2. analyze_functions.py의 main → analyze_main으로 변경
3. 명확히 사용되지 않는 private 메서드들 삭제

### 점진적 적용
1. 중복된 데코레이터/wrapper 함수들을 foundation 모듈로 통합
2. 사용되지 않는 format/validation 함수들 정리
3. 코드 리뷰를 통해 실제 필요한 함수들 확인

### 주의 사항
1. UI 이벤트 핸들러는 Qt 시그널/슬롯으로 동적 연결될 수 있음
2. 데이터베이스 함수들은 향후 기능 확장에서 사용될 수 있음  
3. 테스트 파일들은 독립적으로 실행되므로 사용 여부 판단이 어려움

이 분석을 바탕으로 점진적으로 코드 정리를 진행하시면 코드베이스를 더욱 깔끔하게 관리할 수 있을 것입니다.