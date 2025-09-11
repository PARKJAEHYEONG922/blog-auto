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
    def generate_content_analysis_prompt(keyword: str, structured_data: Dict, content_type: str = "정보/가이드형", tone: str = "정중한 존댓말체", review_detail: str = "") -> str:
        """네이버 SEO 최적화 콘텐츠 분석 기반 AI 프롬프트 생성 (컨텐츠 유형과 말투, 후기 세부 유형 반영)"""
        
        competitor_info = structured_data.get("competitor_analysis", {})
        top_blogs = competitor_info.get("top_blogs", [])
        summary = competitor_info.get("summary", {})
        
        # 컨텐츠 유형별 지침 (네이버 SEO 최적화)
        content_guidelines = {
            "후기/리뷰형": {
                "approach": "개인 경험과 솔직한 후기를 중심으로 '유일무이한 콘텐츠' 작성",
                "structure": "사용 전 고민 → 직접 사용 경험 → 장단점 솔직 후기 → 최종 평가 및 추천",
                "keywords": ["직접 써봤어요", "솔직 후기", "개인적으로", "실제로 사용해보니", "추천하는 이유"],
                "detailed_tips": [
                    "🌟 개인의 고유한 스토리와 감정을 상세히 담아 검색 알고리즘에 최적화",
                    "생생한 묘사: 제품/서비스 사용 전후 변화를 구체적 에피소드로 서술",
                    "객관적 정보와 주관적 평가 균형: 장단점 명확 제시, 별점/평점 포함",
                    "제품 제공 방식 명시: 자비 구매, 협찬, 체험단 등 투명하게 공개하여 신뢰성 확보",
                    "실제 사용 모습의 고품질 사진/영상 (AI 생성 이미지보다 실제 사용 사진)",
                    "사용 기간, 횟수, 비용 등 구체적 수치와 데이터 제공",
                    "Before & After 명확한 비교 효과 설명"
                ]
            },
            "정보/가이드형": {
                "approach": "정확하고 풍부한 정보를 체계적으로 제공하여 검색자의 궁금증 완전 해결",
                "structure": "문제 정의 → 해결책 제시 → 단계별 가이드 → 주의사항 → 마무리",
                "keywords": ["완벽 정리", "총정리", "핵심 포인트", "단계별 가이드", "정확한 정보"],
                "detailed_tips": [
                    "📚 명확한 구조: 서론-본론-결론 + 소제목(H2, H3) 적극 활용으로 검색 최적화",
                    "객관적 데이터와 신뢰할 수 있는 자료 기반 정보 제공",
                    "단계별 설명, 비교표, 체크리스트로 실용적 가치 극대화",
                    "관련 검색어를 소제목과 본문에 자연스럽게 포함하여 검색 노출 증대",
                    "중요한 정보는 굵은 글씨나 인용 형태로 강조하여 가독성 향상",
                    "독자가 바로 따라할 수 있는 구체적 실행 방법 제시",
                    "전문 용어 쉽게 풀어서 설명, 시간/비용 등 현실적 정보 포함"
                ]
            },
            "비교/추천형": {
                "approach": "체계적 비교분석으로 독자의 선택 고민을 완전히 해결",
                "structure": "비교 기준 제시 → 각 옵션 분석 → 장단점 비교 → 상황별 추천 → 최종 결론",
                "keywords": ["VS 비교", "Best 5", "장단점", "상황별 추천", "가성비"],
                "detailed_tips": [
                    "⚖️ 체계적 비교 항목: 가격, 성능, 장단점, 대상 등 객관적 기준 명시",
                    "비교표 활용하여 한눈에 보는 특징 정리 (가독성과 정보 전달력 극대화)",
                    "상황별 맞춤 추천: 가성비 중시, 특정 기능 선호, 초보자용 등 구체적 분류",
                    "객관적 근거 제시: 실제 사용자 후기, 평점, 판매량 등 데이터 활용",
                    "카테고리별 1위 선정: 가성비 최고, 성능 최고, 디자인 최고 등",
                    "결론에서 명확한 선택 가이드와 최종 추천 순위 제시",
                    "구매 시 체크포인트와 주의사항 상세 안내"
                ]
            }
        }
        
        # 후기 세부 유형별 지침 (후기/리뷰형일 때 적용)
        review_detail_guidelines = {
            "내돈내산 후기": {
                "description": "직접 구매해서 써본 솔직한 개인 후기",
                "key_points": [
                    "💰 '직접 구매해서 써본 후기'임을 자연스럽게 언급",
                    "구매하게 된 이유와 고민했던 점들을 솔직하게 표현",
                    "실제 사용해보면서 느낀 장점과 아쉬운 점 균형있게 서술",
                    "가성비에 대한 개인적 평가와 추천 여부",
                    "비슷한 제품과 비교했을 때의 차이점",
                    "재구매 의향이나 지인 추천 의향 포함"
                ],
                "transparency": "개인 구매로 편견 없는 솔직한 후기임을 강조"
            },
            "협찬 후기": {
                "description": "브랜드에서 제공받은 제품의 정직한 리뷰",
                "key_points": [
                    "🤝 '브랜드로부터 제품을 제공받아 작성한 후기'임을 자연스럽게 언급",
                    "협찬이지만 솔직하고 공정한 평가를 하겠다는 의지 표현",
                    "제품의 장점과 아쉬운 점을 균형있게 서술하는 구조",
                    "독자 입장에서 객관적으로 평가하는 관점",
                    "실제 사용 시나리오와 느낀 점들을 상세히 표현",
                    "협찬 관계를 떠나 솔직한 의견 제시하는 톤"
                ],
                "transparency": "협찬 제품이지만 공정하고 솔직한 리뷰 제공"
            },
            "체험단 후기": {
                "description": "체험단 참여를 통한 제품 사용 후기",
                "key_points": [
                    "👥 '체험단에 참여하여 작성한 후기'임을 자연스럽게 언급",
                    "체험 기회를 얻게 된 것에 대한 감사함 표현",
                    "제품을 꼼꼼히 테스트해본 과정과 느낀 점 서술",
                    "체험단으로서 객관적이고 공정한 평가 의지 표현",
                    "일반 구매 고객 입장에서의 솔직한 의견 제시",
                    "체험단 후기지만 편견 없는 균형잡힌 리뷰 작성"
                ],
                "transparency": "체험단 참여 후기의 특성과 한계를 투명하게 공개"
            },
            "대여/렌탈 후기": {
                "description": "렌탈 서비스를 이용한 제품 사용 후기",
                "key_points": [
                    "🔄 '렌탈 서비스로 이용해본 후기'임을 자연스럽게 언급",
                    "렌탈을 선택한 이유와 고민했던 점들 표현",
                    "렌탈 서비스의 장점과 아쉬웠던 점 균형있게 서술",
                    "렌탈과 구매의 차이점에 대한 개인적 의견",
                    "경제성과 편의성 측면에서의 평가",
                    "어떤 상황에 렌탈이 적합할지에 대한 의견 제시"
                ],
                "transparency": "렌탈 서비스 특성상 제한적 사용 후기임을 명확히 안내"
            }
        }
        
        # 말투별 지침
        tone_guidelines = {
            "친근한 반말체": {
                "style": "친구와 대화하듯 편안하고 친근한 말투",
                "examples": ["써봤는데 진짜 좋더라~", "완전 강추!", "솔직히 말하면", "이거 진짜 대박이야"],
                "ending": "댓글로 궁금한 거 물어봐!",
                "sentence_style": "짧고 리드미컬한 문장",
                "detailed_tips": [
                    "감탄사와 의성어를 적절히 활용 (와~, 헉!, 음음)",
                    "줄임말과 신조어를 자연스럽게 사용 (갓템, 핵꿀템, 레게노)",
                    "이모티콘 대신 문자로 감정 표현 (~, !, ?를 활용)",
                    "개인적 경험을 많이 넣어 친밀감 조성",
                    "독자를 친구처럼 부르며 공감대 형성",
                    "어려운 내용도 쉽고 재미있게 풀어서 설명",
                    "농담이나 유머를 적절히 섞어 재미 요소 추가"
                ]
            },
            "정중한 존댓말체": {
                "style": "정중하고 예의 바른 존댓말로 신뢰감 조성",
                "examples": ["사용해보았습니다", "추천드립니다", "도움이 되시길 바랍니다", "참고하시기 바랍니다"],
                "ending": "도움이 되었으면 좋겠습니다. 궁금한 점은 댓글로 문의해 주세요.",
                "sentence_style": "정중하고 완전한 문장",
                "detailed_tips": [
                    "모든 문장을 존댓말로 일관성 있게 작성",
                    "정중한 표현과 겸손한 태도 유지",
                    "독자를 배려하는 마음가짐이 드러나는 표현 사용",
                    "확신보다는 '~것 같습니다', '~로 보입니다' 등 겸손한 표현",
                    "전문적이면서도 어렵지 않은 적절한 어휘 선택",
                    "독자의 상황을 고려한 배려 깊은 조언 제공",
                    "정보 제공 시 출처나 근거를 명확히 제시"
                ]
            },
            "전문가/리뷰어체": {
                "style": "객관적이고 전문적인 분석 톤",
                "examples": ["분석 결과", "객관적으로 평가하면", "전문적 견해로는", "데이터에 따르면"],
                "ending": "객관적인 분석이 도움이 되셨기를 바랍니다.",
                "sentence_style": "논리적이고 분석적인 문장",
                "detailed_tips": [
                    "구체적인 데이터와 수치를 근거로 제시",
                    "장단점을 균형있고 공정하게 분석",
                    "전문 용어를 정확히 사용하되 설명도 함께 제공",
                    "개인적 감정보다는 객관적 사실에 기반한 평가",
                    "비교 대상이 있을 때는 명확한 기준으로 비교",
                    "결론에 이르는 논리적 근거를 단계적으로 제시",
                    "신뢰성 있는 출처나 테스트 결과 인용"
                ]
            }
        }
        
        current_content = content_guidelines.get(content_type, content_guidelines["정보/가이드형"])
        current_tone = tone_guidelines.get(tone, tone_guidelines["정중한 존댓말체"])
        
        # 후기 세부 유형 정보 (후기/리뷰형일 때만 적용)
        current_review_detail = None
        if content_type == "후기/리뷰형" and review_detail:
            current_review_detail = review_detail_guidelines.get(review_detail)
        
        prompt = f"""
# 네이버 SEO 최적화 블로그 콘텐츠 생성 요청

## 🎯 목표 키워드
**"{keyword}"**

## 🚀 네이버 SEO 최적화 필수 원칙
당신은 15년 경력의 네이버 블로그 전문가이자 SEO 전문가입니다. 네이버의 최신 검색 알고리즘에 최적화된 상위 노출 콘텐츠를 작성해야 합니다.

### 📌 핵심 SEO 원칙 (반드시 준수):
1. **유일무이한 콘텐츠**: 검색자가 "이 글 너무 좋다"라고 느낄 만한 독창적 내용 작성
2. **제목 최적화**: 메인 키워드를 제목 맨 앞에 배치, 뾰족하고 간결한 제목
3. **글자 수**: 1,500~2,000자 (공백 제외) 권장, 2,000자 초과 금지
4. **키워드 반복**: 전체 글에서 타겟 키워드 5-6회 자연스럽게 반복
5. **3초의 법칙**: 첫 문단에서 독자가 원하는 답변 명확히 제시
6. **체류 시간 극대화**: 시각적 흥미 유발, 모바일 최적화 고려
7. **소제목 최적화**: 검색 노출 향상을 위해 소제목(H2, H3)에 타겟 키워드 포함

## 🎨 글쓰기 스타일 설정
**컨텐츠 유형:** {content_type}
- **접근법:** {current_content['approach']}
- **구조:** {current_content['structure']}
- **핵심 키워드:** {', '.join(current_content['keywords'])}

**말투 스타일:** {tone}
- **스타일:** {current_tone['style']}
- **예시 표현:** {', '.join(current_tone['examples'])}
- **문장 특징:** {current_tone['sentence_style']}
- **마무리 문구:** {current_tone['ending']}"""
        
        # 후기 세부 유형 정보 추가 (후기/리뷰형일 때만)
        if current_review_detail:
            prompt += f"""

**📝 후기 세부 유형:** {review_detail}
- **설명:** {current_review_detail['description']}
- **투명성 원칙:** {current_review_detail['transparency']}
- **필수 포함 요소:**
  • {chr(10).join([f"  - {point}" for point in current_review_detail['key_points']])}"""
        
        prompt += f"""

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

### 5. 🎨 스타일 적용 필수 지침
**반드시 다음 스타일을 적용해서 작성해주세요:**

**📝 컨텐츠 유형 ({content_type}) 적용:**
- {current_content['approach']}
- 구조를 따라 작성: {current_content['structure']}
- 다음 키워드들을 자연스럽게 활용: {', '.join(current_content['keywords'])}
- 세부 작성 지침:
  • {chr(10).join([f"  - {tip}" for tip in current_content['detailed_tips']])}

**🗣️ 말투 ({tone}) 적용:**
- {current_tone['style']}
- 다음과 같은 표현을 사용: {', '.join(current_tone['examples'])}
- {current_tone['sentence_style']}으로 작성
- 글 마지막은 "{current_tone['ending']}"와 유사한 톤으로 마무리
- 세부 말투 지침:
  • {chr(10).join([f"  - {tip}" for tip in current_tone['detailed_tips']])}

## 📝 네이버 SEO 최적화 결과 형식

다음 형식으로 네이버 상위 노출을 위한 완성된 블로그 글을 제공해주세요:

### ✅ 필수 체크리스트:
- [ ] 제목에 메인 키워드 맨 앞 배치 완료
- [ ] 첫 문단에 핵심 답변 제시 (3초의 법칙)
- [ ] 키워드 5-6회 자연스럽게 반복 
- [ ] 소제목(H2, H3)에 타겟 키워드 포함
- [ ] 1,500~2,000자 범위 준수 (공백 제외)
- [ ] 개인의 고유한 경험/감정 포함
- [ ] 모바일 가독성 고려한 문단 구성

```
**제목**: [키워드가 맨 앞에 있는 뾰족하고 간결한 제목]

**서론 (첫 문단 - 3초의 법칙)**:
[독자가 원하는 핵심 답변을 즉시 제시하고 공감을 불러일으키는 도입부]

**본문**:
[소제목을 활용한 체계적 구성, 키워드 자연스럽게 5-6회 반복]

**결론**:
[요약 및 행동 유도, 댓글 소통 유도 문구 포함]

**추천 태그**: #메인키워드, #연관키워드1, #연관키워드2, #연관키워드3, #연관키워드4

**이미지 삽입 위치 및 최적화**:
- [위치1] 제목과 관련된 메인 이미지 (고해상도, 키워드 포함 파일명)
- [위치2] 본문 설명용 이미지 (실제 사용/경험 사진 권장)
- [위치3] 비교/정리용 이미지 (표, 차트 등)

**최종 글자수**: [공백 제외 정확한 글자수]자

**SEO 최적화 포인트 요약**:
- 키워드 반복 횟수: [X]회
- 소제목 개수: [X]개  
- 예상 체류 시간: [X]분
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


def create_ai_request_data(keyword: str, analyzed_blogs: List[Dict], content_type: str = "정보/가이드형", tone: str = "정중한 존댓말체", review_detail: str = "") -> Dict:
    """AI 요청용 데이터 생성 (컨텐츠 유형과 말투, 후기 세부 유형 포함)"""
    try:
        structure_analyzer = BlogContentStructure()
        structured_data = structure_analyzer.analyze_blog_structure(analyzed_blogs)
        structured_data["keyword"] = keyword
        
        # AI 프롬프트 생성 (스타일 옵션 포함)
        prompt_generator = BlogAIPrompts()
        ai_prompt = prompt_generator.generate_content_analysis_prompt(keyword, structured_data, content_type, tone, review_detail)
        
        return {
            "structured_data": structured_data,
            "ai_prompt": ai_prompt,
            "raw_blogs": analyzed_blogs,
            "content_type": content_type,
            "tone": tone,
            "review_detail": review_detail
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