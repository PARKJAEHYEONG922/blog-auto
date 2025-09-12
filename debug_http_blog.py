#!/usr/bin/env python3
"""
HTTP 기반 블로그 분석 디버깅
"""
import sys
import os
import requests
import re
from bs4 import BeautifulSoup

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_blog_url_conversion():
    """블로그 URL 변환 디버깅"""
    
    test_url = "https://blog.naver.com/kbs4674/223630011073"
    print(f"원본 URL: {test_url}")
    
    # URL 패턴 매칭 테스트
    pattern = r'https://blog\.naver\.com/([^/]+)/(\d+)'
    match = re.search(pattern, test_url)
    
    if match:
        blog_id = match.group(1)
        log_no = match.group(2)
        postview_url = f"https://blog.naver.com/PostView.naver?blogId={blog_id}&logNo={log_no}"
        print(f"변환된 PostView URL: {postview_url}")
        return postview_url
    else:
        print("URL 패턴 매칭 실패")
        return None

def debug_http_request(postview_url):
    """HTTP 요청 디버깅"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print(f"HTTP 요청 시도: {postview_url}")
        response = requests.get(postview_url, headers=headers, timeout=10)
        print(f"HTTP 응답 상태: {response.status_code}")
        print(f"응답 크기: {len(response.text)} bytes")
        
        if response.status_code == 200:
            # HTML 파싱 테스트
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 제목 찾기 테스트
            title_selectors = [
                '.se-title-text',
                'h3.se-title-text', 
                '.se-module.se-module-text.se-title-text',
                'h2.htitle',
                '.blog-title',
                'title'
            ]
            
            print("\n제목 찾기 테스트:")
            for selector in title_selectors:
                element = soup.select_one(selector)
                if element:
                    title = element.get_text(strip=True)
                    print(f"  {selector}: '{title}'")
                    if title and title != '네이버 블로그':
                        break
            else:
                print("  모든 제목 선택자 실패")
            
            # 텍스트 모듈 찾기 테스트
            text_modules = soup.select('.se-module.se-module-text:not(.se-title-text)')
            print(f"\n텍스트 모듈 개수: {len(text_modules)}")
            
            if text_modules:
                total_text = ""
                for i, module in enumerate(text_modules[:3]):  # 처음 3개만 확인
                    module_text = module.get_text(strip=True)
                    print(f"  모듈 {i+1}: '{module_text[:100]}...'")
                    total_text += module_text + ' '
                
                clean_text = ' '.join(total_text.split())
                content_length = len(clean_text.replace(' ', ''))
                print(f"\n총 글자수: {content_length}")
            else:
                print("  텍스트 모듈 없음")
            
            # 이미지 모듈 테스트
            image_modules = soup.select('.se-module.se-module-image')
            print(f"\n이미지 모듈 개수: {len(image_modules)}")
            
            # 비디오 모듈 테스트
            video_modules = soup.select('.se-module.se-module-video')
            print(f"비디오 모듈 개수: {len(video_modules)}")
            
            return True
            
        else:
            print(f"HTTP 요청 실패: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"HTTP 요청 오류: {e}")
        return False

if __name__ == "__main__":
    print("HTTP 블로그 분석 디버깅 시작")
    print("=" * 50)
    
    postview_url = debug_blog_url_conversion()
    if postview_url:
        print("\n" + "=" * 50)
        debug_http_request(postview_url)
    
    # 원본 URL도 시도
    original_url = "https://blog.naver.com/kbs4674/223630011073"
    print("\n" + "=" * 50)
    print("원본 URL 시도")
    debug_http_request(original_url)
    
    print("\n디버깅 완료")