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


class BlogSummaryPrompts:
    """1차 가공: 정보요약 AI를 위한 프롬프트 템플릿"""
    
    @staticmethod
    def generate_content_summary_prompt(combined_content: str, main_keyword: str, content_type: str = "정보/가이드형") -> str:
        """정보요약 AI용 1차 가공 프롬프트 생성"""
        
        
        # 1차 가공 프롬프트 (정보요약 AI용) - 간소화
        summary_prompt = f"""'{main_keyword}' 키워드 상위 블로그 3개 분석해서 다음 형식으로 정확히 출력해주세요:

## 1. 경쟁 블로그 제목들
- (상위 노출된 블로그들의 제목을 나열)

## 2. 핵심 키워드
- (자주 나오는 관련 키워드들을 나열)

## 3. 필수 내용  
- (모든 글이 다루는 공통 주제들을 정리)

## 4. 주요 포인트
- (각 글이 중점적으로 다루는 핵심 내용들을 정리)

## 5. 부족한 점
- (기존 글들이 놓친 부분이나 개선 가능한 점들을 정리)

**분석 대상**:
{combined_content}

위 형식을 정확히 지켜서 작성해주세요. 각 항목마다 구체적이고 실용적인 내용을 포함해주세요."""

        return summary_prompt


class BlogAIPrompts:
    """2차 가공: 글작성 AI를 위한 프롬프트 템플릿"""
    
    @staticmethod
    def generate_content_analysis_prompt(main_keyword: str, sub_keywords: str, structured_data: Dict, content_type: str = "정보/가이드형", tone: str = "정중한 존댓말체", review_detail: str = "", blogger_identity: str = "", summary_result: str = "") -> str:
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
                "focus_areas": ["개인 경험과 솔직한 후기", "장단점 균형 제시", "구체적 사용 데이터"]
            },
            "정보/가이드형": {
                "approach": "정확하고 풍부한 정보를 체계적으로 제공하여 검색자의 궁금증 완전 해결",
                "structure": "문제 정의 → 해결책 제시 → 단계별 가이드 → 주의사항 → 마무리",
                "keywords": ["완벽 정리", "총정리", "핵심 포인트", "단계별 가이드", "정확한 정보"],
                "focus_areas": ["체계적 구조와 소제목", "실용적 가이드 제공", "구체적 실행 방법"]
            },
            "비교/추천형": {
                "approach": "체계적 비교분석으로 독자의 선택 고민을 완전히 해결",
                "structure": "비교 기준 제시 → 각 옵션 분석 → 장단점 비교 → 상황별 추천 → 최종 결론",
                "keywords": ["VS 비교", "Best 5", "장단점", "상황별 추천", "가성비"],
                "focus_areas": ["객관적 비교 기준", "상황별 맞춤 추천", "명확한 선택 가이드"]
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
                "key_features": ["감탄사와 줄임말 활용", "개인적 경험 많이 포함", "유머와 재미 요소"]
            },
            "정중한 존댓말체": {
                "style": "정중하고 예의 바른 존댓말로 신뢰감 조성",
                "examples": ["사용해보았습니다", "추천드립니다", "도움이 되시길 바랍니다", "참고하시기 바랍니다"],
                "ending": "도움이 되었으면 좋겠습니다. 궁금한 점은 댓글로 문의해 주세요.",
                "sentence_style": "정중하고 완전한 문장",
                "key_features": ["일관된 존댓말", "겸손하고 정중한 표현", "신뢰감 있는 어조"]
            },
            "친근한 존댓말체": {
                "style": "친근하고 부드러운 존댓말로 따뜻한 느낌",
                "examples": ["궁금해서 찾아봤어요", "써봤는데 좋더라구요", "이런 게 있더라구요", "도움이 될 것 같아요"],
                "ending": "도움이 되셨으면 좋겠어요~ 궁금한 게 있으시면 댓글 남겨주세요!",
                "sentence_style": "부드럽고 따뜻한 존댓말 문장",
                "key_features": ["부드러운 존댓말", "따뜻하고 친근한 어조", "자연스러운 개인 경험"]
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
당신은 네이버 블로그에서 인기 있는 글을 쓰는 블로거입니다. 독자들이 진짜 도움이 되고 재미있게 읽을 수 있는 글을 쓰는 것이 목표입니다.

# 📝 작업 목표
**메인 키워드**: "{main_keyword}"
**보조 키워드**: "{sub_keywords if sub_keywords.strip() else '메인 키워드와 관련된 보조 키워드들을 3-5개 직접 생성하여 활용'}"
**목표**: 위 키워드로 네이버 검색 상위 노출을 위한 완성도 높은 블로그 글 작성

## 📊 참고할 경쟁 블로그 요약 정보
'{main_keyword}'로 검색시 노출되는 상위 {len(top_blogs)}개 블로그 글을 요약한 결과입니다. 이를 참고하여 더 나은 독창적인 콘텐츠를 작성해주세요:

{summary_result if summary_result.strip() else '참고할 만한 경쟁사 분석 정보가 없으니, 자연스럽고 유용한 콘텐츠로 작성해주세요.'}
"""
        
        prompt += f"""

## 🎨 글쓰기 스타일 가이드라인
**블로그 소개:** {blogger_identity if blogger_identity.strip() else '다양한 정보를 공유하는 일반적인 블로그'}

**컨텐츠 유형:** {content_type}
- **접근법:** {current_content['approach']}
- **구조:** {current_content['structure']}
- **핵심 표현:** {', '.join(current_content['keywords'])}

**말투 스타일:** {tone}
- **스타일:** {current_tone['style']}
- **예시 표현:** {', '.join(current_tone['examples'])}
- **문장 특징:** {current_tone['sentence_style']}
- **마무리 문구:** {current_tone['ending']}"""
        
        prompt += f"""

## 📋 SEO 최적화 원칙 (반드시 준수)
1. **제목 작성**: 위 요약 정보의 경쟁 블로그 제목들과 유사하지 않으면서도 독창적이고 매력적인 제목을 생성해 주세요. 메인키워드는 넣되 자연스럽게 배치
2. **글자 수**: 최소 1,500자 이상 작성 필수입니다. 상위 노출된 1~3위 블로그 포스팅의 평균 글자 수({summary.get('avg_content_length', 1500)}자)보다 더 풍부하고 상세하게 작성해 주세요. 이상적으로는 1,700자에서 2,000자(공백 제외) 사이로 적절히 길게 작성하여 검색 알고리즘에 유리하도록 해주세요
3. **키워드 반복**: 메인 키워드 5-6회, 보조 키워드들 각각 3-4회 자연스럽게 반복 (보조키워드가 제공되지 않은 경우 메인 키워드와 관련된 보조 키워드를 3-5개 직접 생성하여 활용)
4. **3초의 법칙**: 글 초반에 독자가 원하는 핵심 정보를 명확히 제시하여 흥미를 유발합니다
5. **서론 키워드**: 글 서론 부분에 타겟 키워드를 반드시 언급해 주세요
6. **소제목 활용**: 소제목에 필수 키워드를 삽입하면 스마트 블록 노출에 유리합니다
7. **이미지 배치**: 상위 1~3위 블로그 글의 이미지 수를 참고하여 적절한 수의 이미지를 배치할 계획이며, 이 글에는 {avg_image_count}장 이상의 이미지를 삽입할 예정입니다. (이미지) 표시로 위치 지정하되, 필요시 연속으로 여러 장 삽입 가능 (예: (이미지)(이미지)(이미지)(이미지) 등 최대 4장까지 연속 배치 허용)
8. **동영상 포함**: 동영상 1개를 글 중간 적절한 위치에 넣어주세요. 동영상을 넣을 위치에 (동영상)으로 표시해주세요



## 👤 독창성과 신뢰성 강화
- **고유한 관점**: 남들과 다른 독특한 시각이나 접근 방식 제시
- **구체적 정보**: 실용적인 수치, 시간, 상황 등을 포함한 현실감 있는 내용
- **자연스러운 문체**: 획일적이지 않은 개성 있는 어투로 작성
- **완전한 내용**: XX공원, OO병원 같은 placeholder 사용 금지. 구체적인 정보가 없다면 "근처 공원", "동네 병원" 등 일반적 표현 사용
- **다양한 구성 요소**: 단조로운 소제목-본문 반복 지양. 필요시 표, 체크리스트, 비교 목록, TOP5 순위, 단계별 가이드 등 다양한 형식 활용

이러한 개인화 작업을 통해 네이버의 AI 콘텐츠 필터링을 피하고, 독자들에게 진정성 있는 정보로 인식되도록 해야 합니다.

## 📋 출력 형식 (중요!)
**아래 형식에 맞춰 블로그에 바로 복사 붙여넣기 할 수 있도록 깔끔하게 작성해주세요. 추가적인 설명이나 인사말 없이 오직 블로그 콘텐츠만 출력하세요.**

### ✅ 필수 체크리스트:
**SEO 최적화:**
- [ ] 제목에 메인 키워드 자연스럽게 배치 완료
- [ ] 첫 문단에 핵심 답변 제시 (3초의 법칙)
- [ ] 메인 키워드 5-6회, 보조 키워드들 각각 3-4회 자연스럽게 반복
- [ ] 소제목에 관련 키워드 포함하여 구조화
- [ ] 최소 1,500자 이상, 이상적으로는 1,700~2,000자 범위 작성 (공백 제외)


**기술적 요소:**
- [ ] 이미지 삽입 위치 {avg_image_count}개 이상 표시 완료
- [ ] 동영상 삽입 위치 최소 1개 표시 완료
- [ ] 모바일 가독성 고려한 문단 구성

## 🎯 최종 출력 (블로그에 바로 사용)
**다른 설명 없이 아래 형식으로만 출력하세요:**

```
제목: [메인키워드가 자연스럽게 포함된 매력적인 제목]

[서론 - 3초의 법칙으로 핵심 답변 즉시 제시]

[본문은 다양한 형식으로 구성하세요]
- 소제목 + 본문
- 체크리스트 (✓ 항목들)
- 비교표 (| 항목 | 특징 | 가격 |)
- TOP5 순위 (1위: 제품명 - 특징)
- 단계별 가이드 (1단계, 2단계...)
- Q&A 형식 등을 적절히 조합

[결론 - 요약 및 독자 행동 유도]

추천 태그: 
{'[상위 블로그 인기 태그 참고: ' + ', '.join([f'#{tag.lstrip("#")}' for tag in summary.get("common_tags", [])]) + ']' if summary.get("common_tags") else ''}
[메인키워드와 보조키워드를 활용하여 글 내용에 적합한 태그 5개 이상 작성]
```
"""
        return prompt.strip()
    

def create_ai_request_data(main_keyword: str, sub_keywords: str, analyzed_blogs: List[Dict], content_type: str = "정보/가이드형", tone: str = "정중한 존댓말체", review_detail: str = "", blogger_identity: str = "", summary_result: str = "") -> Dict:
    """AI 요청용 데이터 생성 (컨텐츠 유형과 말투, 후기 세부 유형 포함)"""
    try:
        structure_analyzer = BlogContentStructure()
        structured_data = structure_analyzer.analyze_blog_structure(analyzed_blogs)
        structured_data["keyword"] = main_keyword  # 기존 호환성을 위해 메인 키워드 저장
        
        # AI 프롬프트 생성 (스타일 옵션 포함)
        prompt_generator = BlogAIPrompts()
        ai_prompt = prompt_generator.generate_content_analysis_prompt(main_keyword, sub_keywords, structured_data, content_type, tone, review_detail, blogger_identity, summary_result)
        
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


