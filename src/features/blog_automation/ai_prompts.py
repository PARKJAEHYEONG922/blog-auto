"""
블로그 자동화 AI 프롬프트 및 구조화된 데이터 생성
"""
from typing import Dict, List, Any
from src.foundation.logging import get_logger

logger = get_logger("blog_automation.ai_prompts")


class BlogContentStructure:
    """블로그 콘텐츠 구조 분석 및 AI용 데이터 생성"""
    
    def __init__(self):
        self.content_elements = []
        self.analysis_data = {}
    
    def analyze_blog_structure(self, analyzed_blogs: List[Dict]) -> Dict:
        """분석된 블로그들의 구조를 분석하여 AI용 데이터 생성"""
        try:
            structured_data = {
                "keyword": "",
                "competitor_analysis": {
                    "top_blogs": [],
                    "summary": {
                        "total_blogs": len(analyzed_blogs),
                        "avg_content_length": 0,
                        "common_tags": [],
                        "content_patterns": []
                    }
                }
            }
            
            total_length = 0
            all_tags = []
            
            for blog in analyzed_blogs:
                # 개별 블로그 구조 분석
                blog_structure = self.extract_blog_structure(blog)
                structured_data["competitor_analysis"]["top_blogs"].append(blog_structure)
                
                # 통계 계산용
                total_length += blog.get('content_length', 0)
                all_tags.extend(blog.get('tags', []))
            
            # 평균 및 공통 패턴 계산
            if analyzed_blogs:
                structured_data["competitor_analysis"]["summary"]["avg_content_length"] = total_length // len(analyzed_blogs)
                
                # 가장 많이 사용된 태그 상위 5개
                from collections import Counter
                tag_counter = Counter(all_tags)
                structured_data["competitor_analysis"]["summary"]["common_tags"] = [
                    tag for tag, count in tag_counter.most_common(5)
                ]
            
            return structured_data
            
        except Exception as e:
            logger.error(f"블로그 구조 분석 실패: {e}")
            return {}
    
    def extract_blog_structure(self, blog: Dict) -> Dict:
        """개별 블로그의 구조 추출"""
        return {
            "rank": blog.get('rank', 0),
            "title": blog.get('title', ''),
            "url": blog.get('url', ''),
            "statistics": {
                "content_length": blog.get('content_length', 0),
                "image_count": blog.get('image_count', 0),
                "gif_count": blog.get('gif_count', 0),
                "video_count": blog.get('video_count', 0),
                "tag_count": len(blog.get('tags', []))
            },
            "tags": blog.get('tags', []),
            "content_preview": blog.get('text_content', '')[:200] + "..." if blog.get('text_content', '') else ''
        }


class BlogAIPrompts:
    """블로그 AI 생성을 위한 프롬프트 템플릿"""
    
    @staticmethod
    def generate_naver_seo_prompt(keyword: str, structured_data: Dict) -> str:
        """네이버 SEO 최적화 프롬프트 생성 (새로운 버전)"""
        
        competitor_info = structured_data.get("competitor_analysis", {})
        top_blogs = competitor_info.get("top_blogs", [])
        summary = competitor_info.get("summary", {})
        
        # 평균 계산
        avg_content_length = summary.get('avg_content_length', 1500)
        total_images = sum(blog['statistics']['image_count'] for blog in top_blogs) if top_blogs else 3
        avg_images = total_images // len(top_blogs) if top_blogs else 3
        
        prompt = f"""[AI 역할 및 페르소나 설정] 
당신은 15년 경력의 네이버 블로그 전문 마케터이자 SEO 전문가입니다. 잠재 고객의 검색 의도를 정확히 파악하고, 그들이 흥미로워할 만한 깊이 있고 유일무이한 콘텐츠를 전문적이고 친근한 어조로 작성하여 매출 전환을 유도하는 것이 당신의 목표입니다. 네이버의 C-Rank, DIA, Air Search 로직을 완벽하게 이해하고 이를 글쓰기에 적용해야 합니다.

[작업 내용 및 목표] 
주어진 키워드에 대해 상위 노출을 목표로 하는 네이버 블로그 포스팅을 작성해야 합니다. 내가 제공하는 상위 3개 블로그 글 데이터를 철저히 분석하여 우리 글에 최대한 반영하고, 네이버 검색 엔진 최적화(SEO) 원칙을 준수하여 높은 품질의 글을 생성해 주세요.

[타겟 키워드 및 글 주제]
• 타겟 키워드: "{keyword}"
• 글 주제: "{keyword} 관련 전문적이고 유용한 정보 제공"

[상위 3개 블로그 데이터 분석 및 적용 지시]
다음은 {keyword}로 상위 노출된 블로그 글 3개의 데이터입니다. 이 데이터를 면밀히 분석하여 우리 글 작성에 반영해 주세요.
"""
        
        # 각 블로그 정보 추가
        for i, blog in enumerate(top_blogs[:3], 1):
            stats = blog.get('statistics', {})
            prompt += f"""
• 블로그 #{i}:
    ◦ 제목: {blog.get('title', '제목 없음')}
    ◦ 이미지 수: {stats.get('image_count', 0)}장
    ◦ GIF 수: {stats.get('gif_count', 0)}개
    ◦ 동영상 수: {stats.get('video_count', 0)}개
    ◦ 글자 수 (공백 제외): {stats.get('content_length', 0)}자"""
        
        prompt += f"""

위 데이터 분석 결과 적용 가이드라인:
1. 제목 작성:
    ◦ 제공된 상위 블로그 3개의 제목과 유사하지 않으면서도 독창적이고 매력적인 제목을 생성해 주세요.
    ◦ 제목은 명확하고 간결해야 하며, 사용자의 검색 의도를 이해하고 원하는 정보가 글에 담겨있음을 잘 표현해야 합니다.
    ◦ 타겟 키워드를 제목 맨 앞에 배치해 주세요.
    ◦ 여러 키워드를 한 제목에 나열하는 멀티 키워드 삽입 전략은 피하고, 하나의 키워드에 집중하여 작성해 주세요.

2. 글자 수:
    ◦ 상위 노출된 1~3위 블로그 포스팅의 평균 글자 수({avg_content_length}자)를 기준으로 최적화해 주세요.
    ◦ 목표 글자 수: {avg_content_length + 200}자 (공백 제외) - 경쟁사보다 약간 더 길게
    ◦ 2,000자를 넘지 않도록 주의해 주세요.

3. 이미지, GIF, 동영상 수:
    ◦ 상위 1~3위 블로그 글의 평균 이미지 수({avg_images}장)를 참고하여 적절한 수의 이미지 배치 계획
    ◦ 이 글에는 {avg_images + 1}장 이상의 이미지를 삽입할 예정입니다.
    ◦ 동영상은 최소 1개 이상 포함하는 것을 권장합니다.

4. 키워드 반복 횟수:
    ◦ 글 전체에서 타겟 키워드가 5~6회 정도 자연스럽게 반복되도록 작성해 주세요.
    ◦ 소제목에 필수 키워드를 삽입하여 스마트 블록 노출에 유리한 구조를 만들어 주세요.
    ◦ 글 서론 부분에 타겟 키워드를 반드시 언급해 주세요.

[글쓰기 상세 지시사항 (네이버 SEO 최적화)]
1. 글의 구성 및 흐름:
    ◦ 서론(10-15%): 독자의 관심을 끌고 문제를 제시하며, 초반 3초 내에 독자가 원하는 핵심 정보를 명확히 제시하고, 개인의 경험이나 감정을 담아 공감대를 형성하는 방식으로 시작해 주세요. 타겟 키워드를 반드시 언급해야 합니다.
    ◦ 본론(70-80%): 구체적인 정보와 해결책을 제공하며, 독자가 원하는 정보를 충분히 제공하고, 글의 흐름을 방해하지 않는 선에서 관련 내용을 자연스럽게 풀어내세요.
    ◦ 결론(10-15%): 내용을 요약하고 독자의 행동(예: 댓글, 구매 등)을 유도하는 문구를 포함하여 마무리해 주세요.
    ◦ 문단 구분: 문장을 두 세 개 정도 이어서 문단의 형태로 작성하고, 문단 구분을 확실히 해 주세요.

2. 체류 시간 극대화 전략:
    ◦ 시각 자료 적극 활용: 긴 텍스트를 나누는 용도로 이미지를 적절히 삽입하여 가독성을 높이고, 독자의 흥미를 유발하세요.
    ◦ 소통 유도: 댓글과 소통을 유도하는 문구를 포함하여 체류 시간을 늘리세요.

3. 가독성 및 포맷팅:
    ◦ 인용구 사용: 문단을 구분하거나 내용을 강조할 때 인용구를 적절히 사용하여 글의 연관성을 높이고 가독성을 향상시켜 주세요.
    ◦ 정렬: 기본적으로 좌측 정렬을 하되, 문장을 두 세 개 정도 이어서 문단으로 작성하고 문단 구분을 확실히 해주세요.

[결과 형식]
다음 형식으로 결과를 제공해주세요:

**제목:** [키워드가 앞에 포함된 매력적인 제목]

**본문:**
[서론 - 키워드 포함, 공감대 형성]

[본론 - 구체적 정보와 해결책, 소제목 활용]

[결론 - 요약 및 행동 유도]

**추천 태그:** #태그1, #태그2, #태그3, #태그4, #태그5

**이미지 삽입 위치:**
- [첫 번째 이미지 위치와 설명]
- [두 번째 이미지 위치와 설명]
- [세 번째 이미지 위치와 설명]

**최종 글자수:** [공백 제외 글자수]자
"""
        return prompt.strip()
    
    @staticmethod
    def generate_content_analysis_prompt(keyword: str, structured_data: Dict) -> str:
        """콘텐츠 분석 기반 AI 프롬프트 생성"""
        
        competitor_info = structured_data.get("competitor_analysis", {})
        top_blogs = competitor_info.get("top_blogs", [])
        summary = competitor_info.get("summary", {})
        
        prompt = f"""
# 블로그 콘텐츠 생성 요청

## 🎯 목표 키워드
**"{keyword}"**

## 📊 경쟁사 분석 데이터

### 상위 {len(top_blogs)}개 블로그 분석 결과:
"""
        
        # 각 블로그 정보 추가
        for i, blog in enumerate(top_blogs, 1):
            prompt += f"""
**{i}위 블로그:**
- 제목: {blog['title']}
- 글자수: {blog['statistics']['content_length']}자
- 이미지: {blog['statistics']['image_count']}개, GIF: {blog['statistics']['gif_count']}개, 동영상: {blog['statistics']['video_count']}개
- 태그: {', '.join(blog['tags'][:5])}{'...' if len(blog['tags']) > 5 else ''}
- 내용 미리보기: {blog['content_preview']}
"""
        
        # 종합 분석
        prompt += f"""
### 📈 종합 분석:
- 평균 글자수: {summary.get('avg_content_length', 0)}자
- 인기 태그: {', '.join(summary.get('common_tags', []))}
- 분석 대상: {summary.get('total_blogs', 0)}개 블로그

## 🚀 요청사항

다음 조건을 만족하는 블로그 글을 작성해주세요:

### 1. 제목 생성
- "{keyword}" 키워드를 포함하되 경쟁사와 차별화
- 클릭을 유도하는 매력적인 제목
- SEO에 최적화된 구조

### 2. 콘텐츠 구조
- **글자수**: {summary.get('avg_content_length', 1000) + 200}자 내외 (경쟁사보다 약간 길게)
- **구성**: 도입 → 문제 제기 → 해결책 제시 → 결론/행동 유도
- **톤앤매너**: 친근하고 전문적, 독자의 고민에 공감

### 3. SEO 최적화
- 목표 키워드 자연스럽게 배치
- 관련 키워드 및 롱테일 키워드 활용
- 태그 추천: {', '.join(summary.get('common_tags', []))} 기반으로 5-8개

### 4. 콘텐츠 특징
- 실용적이고 actionable한 정보 제공
- 경쟁사 대비 차별화된 관점이나 정보
- 독자의 문제를 구체적으로 해결

## 📝 결과 형식

다음 형식으로 결과를 제공해주세요:

```
제목: [생성된 제목]

본문:
[생성된 본문 내용]

추천 태그: [#태그1, #태그2, #태그3, ...]

이미지 삽입 위치:
- [첫 번째 이미지 위치와 설명]
- [두 번째 이미지 위치와 설명]
```
"""
        return prompt.strip()
    
    @staticmethod
    def generate_blog_structure_prompt(blog_content_structure: str) -> str:
        """블로그 구조 기반 프롬프트 생성 (HTML 구조 분석 버전)"""
        
        prompt = f"""
# 블로그 콘텐츠 구조 분석 및 재작성

## 📋 분석된 콘텐츠 구조:

{blog_content_structure}

## 🎯 요청사항

위 구조를 참고하여 다음을 수행해주세요:

### 1. 구조 분석
- 콘텐츠 흐름 패턴 파악
- 텍스트와 미디어의 배치 방식 분석
- 효과적인 구성 요소 식별

### 2. 개선된 버전 제작
- 동일한 구조를 유지하되 내용은 완전히 새롭게
- 더 매력적이고 유용한 정보로 재구성
- SEO 최적화 고려

### 3. 결과 형식
```
구조 분석:
[원본 구조의 특징과 장점 분석]

개선된 콘텐츠:

제목: [새로운 제목]

본문:
[텍스트 부분]

[이미지 위치 - 설명: xxx]

[텍스트 부분]

[GIF 위치 - 설명: xxx]

[텍스트 부분]

[동영상 위치 - 설명: xxx]

[텍스트 부분]

태그: [추천 태그들]
```
"""
        return prompt.strip()
    
    @staticmethod
    def generate_simple_rewrite_prompt(title: str, content: str, tags: List[str]) -> str:
        """간단한 리라이팅 프롬프트"""
        
        prompt = f"""
# 블로그 글 리라이팅 요청

## 원본 콘텐츠:
**제목:** {title}
**태그:** {', '.join(tags)}

**내용:**
{content}

## 요청사항:
1. 동일한 주제와 정보를 다루되 완전히 새로운 문체와 구성으로 작성
2. 더 매력적이고 읽기 쉬운 글로 개선
3. SEO 최적화 고려
4. 원본보다 10-20% 더 길게 작성

## 결과 형식:
```
제목: [새로운 제목]

본문:
[리라이팅된 내용]

추천 태그: [#태그1, #태그2, ...]
```
"""
        return prompt.strip()


def create_ai_request_data(keyword: str, analyzed_blogs: List[Dict]) -> Dict:
    """AI 요청용 데이터 생성"""
    try:
        structure_analyzer = BlogContentStructure()
        structured_data = structure_analyzer.analyze_blog_structure(analyzed_blogs)
        structured_data["keyword"] = keyword
        
        # AI 프롬프트 생성
        prompt_generator = BlogAIPrompts()
        ai_prompt = prompt_generator.generate_content_analysis_prompt(keyword, structured_data)
        
        return {
            "structured_data": structured_data,
            "ai_prompt": ai_prompt,
            "raw_blogs": analyzed_blogs
        }
        
    except Exception as e:
        logger.error(f"AI 요청 데이터 생성 실패: {e}")
        return {}


# 사용 예시
if __name__ == "__main__":
    # 테스트용 데이터
    test_blogs = [
        {
            "rank": 1,
            "title": "강아지 다이어트 사료 추천",
            "content_length": 1247,
            "image_count": 8,
            "gif_count": 2,
            "video_count": 1,
            "tags": ["#강아지사료", "#다이어트", "#추천"],
            "text_content": "강아지 다이어트에 대한 내용..."
        }
    ]
    
    # AI 요청 데이터 생성
    ai_data = create_ai_request_data("강아지 다이어트 사료", test_blogs)
    print(ai_data["ai_prompt"])