#!/usr/bin/env python3
"""
HTML 콘텐츠 추출 상세 디버깅
"""
import requests
from bs4 import BeautifulSoup

def debug_html_content():
    """HTML 콘텐츠 구조 분석"""
    
    url = "https://blog.naver.com/kbs4674/223630011073"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            print(f"HTML 응답 크기: {len(response.text)} bytes")
            
            # 1. iframe 확인
            iframes = soup.select('iframe')
            print(f"\niframe 개수: {len(iframes)}")
            for i, iframe in enumerate(iframes[:3]):  # 처음 3개만
                src = iframe.get('src', '')
                id_attr = iframe.get('id', '')
                print(f"  iframe {i+1}: id='{id_attr}', src='{src[:100]}...'")
            
            # 2. 제목 확인
            title_selectors = [
                'title',
                'h1', 'h2', 'h3',
                '.se-title-text',
                'meta[property="og:title"]'
            ]
            
            print("\n제목 후보들:")
            for selector in title_selectors:
                elements = soup.select(selector)
                for element in elements[:3]:  # 각 선택자당 최대 3개
                    if selector.startswith('meta'):
                        text = element.get('content', '')
                    else:
                        text = element.get_text(strip=True)
                    if text:
                        print(f"  {selector}: '{text[:100]}'")
            
            # 3. 본문 콘텐츠 확인
            print("\n본문 콘텐츠 후보들:")
            content_selectors = [
                '.se-module.se-module-text',
                '.se-viewer',
                '#post_view',
                '.post_content',
                'body'
            ]
            
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    print(f"  {selector}: {len(elements)}개 요소")
                    # 첫 번째 요소의 텍스트 미리보기
                    if elements[0]:
                        text = elements[0].get_text(strip=True)
                        print(f"    첫 번째 요소 텍스트: '{text[:200]}...'")
            
            # 4. 스크립트 내용 확인 (블로그 데이터가 있을 수 있음)
            scripts = soup.select('script')
            print(f"\nscript 태그 개수: {len(scripts)}")
            for i, script in enumerate(scripts[:5]):  # 처음 5개만
                script_content = script.string or script.get_text()
                if script_content and len(script_content) > 50:
                    print(f"  script {i+1}: '{script_content[:100]}...'")
            
            # 5. 메타 태그들 확인
            meta_tags = soup.select('meta')
            print(f"\n주요 메타 태그들:")
            for meta in meta_tags:
                name = meta.get('name', '') or meta.get('property', '')
                content = meta.get('content', '')
                if name and content and len(content) > 10:
                    print(f"  {name}: '{content[:100]}...'")
            
        else:
            print(f"HTTP 요청 실패: {response.status_code}")
    
    except Exception as e:
        print(f"오류: {e}")

if __name__ == "__main__":
    debug_html_content()