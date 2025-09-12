#!/usr/bin/env python3
"""
iframe 콘텐츠 추출 디버깅
"""
import requests
from bs4 import BeautifulSoup

def debug_iframe_content():
    """iframe 콘텐츠 구조 분석"""
    
    # 먼저 원본 페이지에서 iframe URL 추출
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
            
            iframe = soup.select_one('iframe#mainFrame')
            if iframe:
                iframe_src = iframe.get('src', '')
                print(f"iframe src: {iframe_src}")
                
                if iframe_src:
                    # 상대 URL을 절대 URL로 변환
                    if iframe_src.startswith('/'):
                        iframe_url = 'https://blog.naver.com' + iframe_src
                    else:
                        iframe_url = iframe_src
                    
                    print(f"iframe 절대 URL: {iframe_url}")
                    
                    # iframe 내부 콘텐츠 요청 (여러 URL 시도)
                    urls_to_try = [
                        iframe_url,  # 원본 URL
                        f"https://blog.naver.com/PostView.naver?blogId=kbs4674&logNo=223630011073",  # 간단한 URL
                    ]
                    
                    iframe_response = None
                    for test_url in urls_to_try:
                        print(f"시도하는 URL: {test_url}")
                        try:
                            iframe_response = requests.get(test_url, headers=headers, timeout=15)
                            print(f"응답 상태: {iframe_response.status_code}")
                            if iframe_response.status_code == 200:
                                break
                        except Exception as e:
                            print(f"요청 오류: {e}")
                    
                    if iframe_response and iframe_response.status_code == 200:
                        content_soup = BeautifulSoup(iframe_response.text, 'html.parser')
                        
                        print(f"\niframe 응답 크기: {len(iframe_response.text)} bytes")
                        
                        # 제목 찾기
                        title_selectors = [
                            '.se-title-text',
                            'h3.se-title-text',
                            '.se-module.se-module-text.se-title-text',
                            'h1', 'h2', 'h3',
                            'title'
                        ]
                        
                        print("\niframe에서 제목 후보들:")
                        for selector in title_selectors:
                            elements = content_soup.select(selector)
                            for element in elements[:2]:
                                text = element.get_text(strip=True)
                                if text:
                                    print(f"  {selector}: '{text}'")
                        
                        # 본문 텍스트 찾기
                        print("\niframe에서 본문 콘텐츠 후보들:")
                        content_selectors = [
                            '.se-module.se-module-text:not(.se-title-text)',
                            '.se-viewer',
                            '#post_view',
                            '.post_content',
                            '.se-main-container'
                        ]
                        
                        for selector in content_selectors:
                            elements = content_soup.select(selector)
                            if elements:
                                print(f"  {selector}: {len(elements)}개 요소")
                                if elements[0]:
                                    text = elements[0].get_text(strip=True)
                                    if text:
                                        print(f"    첫 번째 텍스트: '{text[:200]}...'")
                        
                        # 이미지 모듈 찾기
                        image_modules = content_soup.select('.se-module.se-module-image')
                        print(f"\niframe에서 이미지 모듈: {len(image_modules)}개")
                        
                        # 비디오 모듈 찾기
                        video_modules = content_soup.select('.se-module.se-module-video')
                        print(f"iframe에서 비디오 모듈: {len(video_modules)}개")
                        
                        # 전체 body 텍스트 확인
                        body = content_soup.select_one('body')
                        if body:
                            body_text = body.get_text(strip=True)
                            print(f"\niframe body 전체 텍스트 길이: {len(body_text)}자")
                            if body_text:
                                print(f"body 텍스트 미리보기: '{body_text[:300]}...'")
                    
                    else:
                        print(f"iframe 요청 실패: {iframe_response.status_code}")
                        
            else:
                print("iframe#mainFrame을 찾을 수 없습니다")
        
        else:
            print(f"원본 페이지 요청 실패: {response.status_code}")
    
    except Exception as e:
        print(f"오류: {e}")

if __name__ == "__main__":
    debug_iframe_content()