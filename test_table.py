#!/usr/bin/env python3
"""HTML 표 하이브리드 렌더링 테스트"""

# 테스트용 마크다운 표 데이터
test_markdown = """
## 테스트 제목

일반 텍스트입니다.

| 항목 | 가격 | 설명 |
|------|------|------|
| 사과 | 1000원 | 신선한 사과 |
| 바나나 | 800원 | 달콤한 바나나 |

**강조 텍스트**입니다.

### 소제목

더 많은 내용...
"""

def test_table_detection():
    """표 감지 로직 테스트"""
    lines = test_markdown.strip().split('\n')
    
    print("=== 표 감지 테스트 ===")
    for i, line in enumerate(lines):
        stripped = line.strip()
        is_table_line = (
            stripped.startswith('|') and 
            stripped.endswith('|') and 
            stripped.count('|') >= 3
        )
        print(f"{i:2d}: {is_table_line} | {line}")

def test_table_conversion():
    """표 변환 로직 테스트"""
    table_lines = [
        "| 항목 | 가격 | 설명 |",
        "|------|------|------|", 
        "| 사과 | 1000원 | 신선한 사과 |",
        "| 바나나 | 800원 | 달콤한 바나나 |"
    ]
    
    print("\n=== 표 변환 테스트 ===")
    
    # 표 데이터 파싱
    table_data = []
    for line in table_lines:
        if '---' in line:  # 구분선 스킵
            continue
        
        # | 기호로 분리하고 양쪽 공백 제거
        cells = [cell.strip() for cell in line.split('|')[1:-1]]  # 양쪽 빈 요소 제거
        if cells:
            table_data.append(cells)
    
    print(f"파싱된 표 데이터: {table_data}")
    
    if not table_data:
        print("표 데이터가 없습니다")
        return ""
    
    rows = len(table_data)
    cols = len(table_data[0]) if table_data else 0
    print(f"표 크기: {rows}행 × {cols}열")
    
    # HTML 변환
    html_parts = ['<table style="border-collapse: collapse; width: 100%; margin: 10px 0; border: 1px solid #ddd;">']
    
    for row_idx, row_data in enumerate(table_data):
        # 헤더 행 스타일
        if row_idx == 0:
            html_parts.append('<tr style="background-color: #f8f9fa;">')
        else:
            html_parts.append('<tr>')
        
        for col_idx, cell_data in enumerate(row_data):
            cell_html = f'<td style="border: 1px solid #ddd; padding: 12px; text-align: center;">{cell_data}</td>'
            html_parts.append(cell_html)
        
        html_parts.append('</tr>')
    
    html_parts.append('</table>')
    
    html_result = ''.join(html_parts)
    print(f"\n생성된 HTML:")
    print(html_result)
    
    return html_result

if __name__ == "__main__":
    test_table_detection()
    test_table_conversion()