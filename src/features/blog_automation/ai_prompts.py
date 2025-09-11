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
    def generate_content_analysis_prompt(main_keyword: str, sub_keywords: str, structured_data: Dict, content_type: str = "정보/가이드형", tone: str = "정중한 존댓말체", review_detail: str = "") -> str:
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
            "친근한 존댓말체": {
                "style": "친근하고 부드러운 존댓말로 따뜻한 느낌",
                "examples": ["궁금해서 찾아봤어요", "써봤는데 좋더라구요", "이런 게 있더라구요", "도움이 될 것 같아요"],
                "ending": "도움이 되셨으면 좋겠어요~ 궁금한 게 있으시면 댓글 남겨주세요!",
                "sentence_style": "부드럽고 따뜻한 존댓말 문장",
                "detailed_tips": [
                    "'~했어요', '~더라구요', '~것 같아요' 등 부드러운 존댓말 활용",
                    "독자를 배려하는 친근하고 따뜻한 어조 유지",
                    "개인적 경험을 자연스럽게 녹여서 친밀감 형성",
                    "어려운 내용도 쉽고 친근하게 설명하는 접근",
                    "독자의 입장을 이해하고 공감하는 표현 사용",
                    "정보 전달 시에도 부담스럽지 않은 온화한 톤 유지",
                    "마무리는 항상 따뜻하고 도움되는 마음으로 작성"
                ]
            }
        }
        
        current_content = content_guidelines.get(content_type, content_guidelines["정보/가이드형"])
        current_tone = tone_guidelines.get(tone, tone_guidelines["정중한 존댓말체"])
        
        # 후기 세부 유형 정보 (후기/리뷰형일 때만 적용)
        current_review_detail = None
        if content_type == "후기/리뷰형" and review_detail:
            current_review_detail = review_detail_guidelines.get(review_detail)
        
        # 평균 태그 개수 계산
        avg_tag_count = sum(len(blog.get("tags", [])) for blog in top_blogs) // max(1, len(top_blogs)) if top_blogs else 5
        
        # 평균 이미지 개수 계산
        avg_image_count = sum(blog.get("statistics", {}).get("image_count", 0) for blog in top_blogs) // max(1, len(top_blogs)) if top_blogs else 3
        
        prompt = f"""
# 🎭 AI 역할 설정
당신은 15년 경력의 네이버 블로그 전문가이자 SEO 전문가입니다. 네이버의 최신 검색 알고리즘에 최적화된 상위 노출 콘텐츠를 작성해야 합니다.

# 📝 작업 목표
**메인 키워드**: "{main_keyword}"
**보조 키워드**: "{sub_keywords if sub_keywords.strip() else '메인 키워드와 관련된 보조 키워드들을 3-5개 직접 생성하여 활용'}"
**미션**: 검색자가 "이 글 너무 좋다!"라고 느낄 만한 유일무이한 블로그 콘텐츠 작성

## 📊 경쟁사 분석 데이터
### 상위 {len(top_blogs)}개 블로그 분석 결과:"""

        # 경쟁사 데이터를 먼저 보여줌
        for i, blog in enumerate(top_blogs, 1):
            prompt += f"""
**{i}위 블로그:**
- 제목: {blog['title']}
- 글자수: {blog['statistics']['content_length']}자
- 이미지: {blog['statistics']['image_count']}개, GIF: {blog['statistics']['gif_count']}개, 동영상: {blog['statistics']['video_count']}개
- 태그: {', '.join(blog['tags'][:5])}{'...' if len(blog['tags']) > 5 else ''}
- 내용 미리보기: {blog['content_preview']}
"""
        
        prompt += f"""

## 🎨 글쓰기 스타일 가이드라인
**컨텐츠 유형:** {content_type}
- **접근법:** {current_content['approach']}
- **구조:** {current_content['structure']}
- **핵심 키워드:** {', '.join(current_content['keywords'])}

**말투 스타일:** {tone}
- **스타일:** {current_tone['style']}
- **예시 표현:** {', '.join(current_tone['examples'])}
- **문장 특징:** {current_tone['sentence_style']}
- **마무리 문구:** {current_tone['ending']}"""
        
        prompt += f"""

## 📋 SEO 최적화 원칙 (반드시 준수)
1. **제목 작성**: 제공된 상위 블로그 3개의 제목과 유사하지 않으면서도 독창적이고 매력적인 제목을 생성해 주세요. 메인키워드는 넣되 자연스럽게 배치
2. **글자 수**: 상위 노출된 1~3위 블로그 포스팅의 평균 글자 수({summary.get('avg_content_length', 1500)}자)를 분석하여 이를 기준으로 최적화해 주세요. 일반적으로 1,500자에서 2,000자(공백 제외) 사이가 적합하며, 2,000자를 넘지 않도록 주의해 주세요
3. **키워드 반복**: 메인 키워드 5-6회, 보조 키워드들 각각 3-4회 자연스럽게 반복 (보조키워드가 제공되지 않은 경우 메인 키워드와 관련된 보조 키워드를 3-5개 직접 생성하여 활용)
4. **3초의 법칙**: 글 초반에 독자가 원하는 핵심 정보를 명확히 제시하여 흥미를 유발합니다
5. **서론 키워드**: 글 서론 부분에 타겟 키워드를 반드시 언급해 주세요
6. **소제목 활용**: 소제목에 필수 키워드를 삽입하면 스마트 블록 노출에 유리합니다
7. **이미지 배치**: 상위 1~3위 블로그 글의 이미지 수를 참고하여 적절한 수의 이미지를 배치할 계획이며, 이 글에는 {avg_image_count}장 이상의 이미지를 삽입할 예정입니다. (이미지) 표시로 위치 지정하되, 필요시 연속으로 여러 장 삽입 가능 (예: (이미지)(이미지)(이미지)(이미지) 등 최대 4장까지 연속 배치 허용)
8. **동영상 포함**: 동영상은 최소 1개 이상 포함하는 것을 권장하며, 동영상 제목에도 키워드를 넣어 유입 경로를 늘려주세요. 동영상은 (동영상)으로 표시
9. **경쟁사 차별화**: 상위 블로그들보다 더 풍부하고 구체적인 내용 작성

## 📖 글의 구성 및 흐름
1. **서론(10-15%)**: 독자의 관심을 끌고 문제를 제시하며, 초반 3초 내에 독자가 원하는 핵심 정보를 명확히 제시하고, 개인의 경험이나 감정을 담아 공감대를 형성하는 방식으로 시작해 주세요. 타겟 키워드를 반드시 언급해야 합니다.
2. **본론(70-80%)**: 구체적인 정보와 해결책을 제공하며, 독자가 원하는 정보를 충분히 제공하고, 글의 흐름을 방해하지 않는 선에서 관련 내용을 자연스럽게 풀어내세요. 다이아 로직에 따라 유일무이한 콘텐츠가 되도록 자신만의 전문성이나 스토리를 담아주세요.
3. **결론(10-15%)**: 내용을 요약하고 독자의 행동(예: 댓글, 구매 등)을 유도하는 문구를 포함하여 마무리해 주세요.
4. **문단 구분**: 문장을 두 세 개 정도 이어서 문단의 형태로 작성하고, 문단 구분을 확실히 해 주세요.

## ⏱️ 체류 시간 극대화 전략
1. **시각 자료 적극 활용**: 긴 텍스트를 나누는 용도로 이미지를 적절히 삽입하여 가독성을 높이고, 독자의 흥미를 유발하세요.
2. **내부 링크 활용**: 관련된 다른 포스팅으로 연결되는 내부 링크를 활용하여 독자가 블로그 내에서 더 많은 시간을 보내도록 유도해 주세요.
3. **소통 유도**: 댓글과 소통을 유도하는 문구를 포함하여 체류 시간을 늘리세요. (예: "궁금한 점은 댓글로 남겨주세요.")

## 👤 개인적 터치와 독창성 강화
생성된 콘텐츠에 반드시 다음 요소들을 포함하여 인간적이고 신뢰감 있는 글로 만들어야 합니다:
- **개인 경험 스토리**: 실제 겪은 일화나 느낌을 자연스럽게 녹여내기
- **감정적 표현**: 솔직한 감정과 개인적 의견을 적절히 표현하여 공감대 형성
- **고유한 관점**: 남들과 다른 독특한 시각이나 접근 방식 제시
- **세부적 묘사**: 구체적인 상황, 수치, 시간 등을 포함한 현실감 있는 내용
- **개성 있는 표현**: 획일적이지 않은 자연스러운 어투와 문체 사용

이러한 개인화 작업을 통해 네이버의 AI 콘텐츠 필터링을 피하고, 독자들에게 진정성 있는 정보로 인식되도록 해야 합니다.

**반드시 다음과 같은 구조로 완성된 블로그 글을 작성해주세요:**

### ✅ 필수 체크리스트:
**SEO 최적화:**
- [ ] 제목에 메인 키워드 자연스럽게 배치 완료
- [ ] 첫 문단에 핵심 답변 제시 (3초의 법칙)
- [ ] 메인 키워드 5-6회, 보조 키워드들 각각 3-4회 자연스럽게 반복
- [ ] 소제목에 관련 키워드 포함하여 구조화
- [ ] {max(1500, summary.get('avg_content_length', 1500))}~2,000자 범위 준수 (공백 제외)

**콘텐츠 품질:**
- [ ] 개인 경험 스토리와 감정적 표현 포함
- [ ] 구체적인 수치, 시간, 상황 등 세부 묘사 완료
- [ ] 상위 블로그 대비 차별화된 관점 제시
- [ ] 독자 행동 유도 문구 포함 (댓글, 소통 등)

**기술적 요소:**
- [ ] 이미지 삽입 위치 {avg_image_count}개 이상 표시 완료
- [ ] 동영상 삽입 위치 최소 1개 표시 완료
- [ ] 모바일 가독성 고려한 문단 구성
- [ ] 태그 {avg_tag_count}개 작성 (브랜드명 제외)

```
**제목**: [메인키워드가 자연스럽게 포함된 뾰족하고 간결한 제목]

**서론 (첫 문단 - 3초의 법칙)**:
[독자가 원하는 핵심 답변을 즉시 제시하고 공감을 불러일으키는 도입부]

**본문**:
[소제목을 활용한 체계적 구성, 메인키워드 5-6회 + 보조키워드들 3-4회씩 자연스럽게 반복]

**결론**:
[요약 및 행동 유도, 댓글 소통 유도 문구 포함]

**추천 태그**: 총 {avg_tag_count}개 태그를 작성하되, #{main_keyword}{"" if not sub_keywords else ", #" + ", #".join([kw.strip() for kw in sub_keywords.split(",") if kw.strip()])} 포함 필수, 나머지는 위 분석된 인기 태그 참고하여 브랜드명 제외하고 작성
```
"""
        return prompt.strip()
    

def create_ai_request_data(main_keyword: str, sub_keywords: str, analyzed_blogs: List[Dict], content_type: str = "정보/가이드형", tone: str = "정중한 존댓말체", review_detail: str = "") -> Dict:
    """AI 요청용 데이터 생성 (컨텐츠 유형과 말투, 후기 세부 유형 포함)"""
    try:
        structure_analyzer = BlogContentStructure()
        structured_data = structure_analyzer.analyze_blog_structure(analyzed_blogs)
        structured_data["keyword"] = main_keyword  # 기존 호환성을 위해 메인 키워드 저장
        
        # AI 프롬프트 생성 (스타일 옵션 포함)
        prompt_generator = BlogAIPrompts()
        ai_prompt = prompt_generator.generate_content_analysis_prompt(main_keyword, sub_keywords, structured_data, content_type, tone, review_detail)
        
        return {
            "structured_data": structured_data,
            "ai_prompt": ai_prompt,
            "raw_blogs": analyzed_blogs,
            "main_keyword": main_keyword,
            "sub_keywords": sub_keywords,
            "content_type": content_type,
            "tone": tone,
            "review_detail": review_detail
        }
        
    except Exception as e:
        logger.error(f"AI 요청 데이터 생성 실패: {e}")
        return {}


