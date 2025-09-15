"""
블로그 자동화 AI 프롬프트 및 구조화된 데이터 생성
"""
from typing import Dict, List, Any
from src.foundation.logging import get_logger

logger = get_logger("blog_automation.ai_prompts")


class BlogPromptComponents:
    """블로그 프롬프트 공용 컴포넌트 모음"""

    # 컨텐츠 유형별 지침 (공용)
    CONTENT_GUIDELINES = {
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

    # 후기 세부 유형별 지침 (공용)
    REVIEW_DETAIL_GUIDELINES = {
        "내돈내산 후기": {
            "description": "직접 구매해서 써본 솔직한 개인 후기",
            "key_points": [
                "본문 제일 첫번째에 '직접 구매해서 사용해본 후기입니다' 또는 '내돈내산 후기입니다' 자연스럽게 명시",
                "구매하게 된 이유와 고민 표현",
                "장단점을 균형있게 서술"
            ],
            "transparency": "개인 구매로 편견 없는 솔직한 후기임을 강조"
        },
        "협찬 후기": {
            "description": "브랜드에서 제공받은 제품의 정직한 리뷰",
            "key_points": [
                "본문 제일 첫번째에 '브랜드로부터 제품을 제공받아 작성한 후기입니다' 명시",
                "협찬이지만 솔직한 평가를 하겠다고 표현",
                "장단점을 균형있게 서술"
            ],
            "transparency": "절대 '구매했다', '샀다' 등의 표현 사용 금지"
        },
        "체험단 후기": {
            "description": "체험단 참여를 통한 제품 사용 후기",
            "key_points": [
                "본문 제일 첫번째에 '체험단에 참여하여 작성한 후기입니다' 명시",
                "체험 기회에 대한 감사 표현",
                "객관적이고 공정한 평가 의지 표현"
            ],
            "transparency": "절대 '구매했다', '샀다' 등의 표현 사용 금지"
        },
        "대여/렌탈 후기": {
            "description": "렌탈 서비스를 이용한 제품 사용 후기",
            "key_points": [
                "본문 제일 첫번째에 '렌탈 서비스로 이용해본 후기입니다' 명시",
                "렌탈을 선택한 이유 표현",
                "렌탈 서비스의 장단점 균형있게 서술"
            ],
            "transparency": "렌탈 서비스 특성상 제한적 사용 후기임을 안내"
        }
    }

    # 말투별 지침 (공용)
    TONE_GUIDELINES = {
        "친근한 반말체": {
            "style": "친구와 대화하듯 편안하고 친근한 말투",
            "examples": ["써봤는데 진짜 좋더라~", "완전 강추!", "솔직히 말하면", "이거 진짜 대박이야"],
            "ending": "댓글로 궁금한 거 물어봐!",
            "sentence_style": "짧고 리드미컬한 문장",
            "key_features": ["감탄사와 줄임말 활용", "개인적 경험 많이 포함", "유머와 재미 요소"]
        },
        "친근한 존댓말체": {
            "style": "친근하고 부드러운 존댓말로 따뜻한 느낌",
            "examples": ["궁금해서 찾아봤어요", "써봤는데 좋더라구요", "이런 게 있더라구요", "도움이 될 것 같아요"],
            "ending": "도움이 되셨으면 좋겠어요~ 궁금한 게 있으시면 댓글 남겨주세요!",
            "sentence_style": "부드럽고 따뜻한 존댓말 문장",
            "key_features": ["부드러운 존댓말", "따뜻하고 친근한 어조", "자연스러운 개인 경험"]
        },
        "정중한 존댓말체": {
            "style": "정중하고 예의 바른 존댓말로 신뢰감 조성",
            "examples": ["사용해보았습니다", "추천드립니다", "도움이 되시길 바랍니다", "참고하시기 바랍니다"],
            "ending": "도움이 되었으면 좋겠습니다. 궁금한 점은 댓글로 문의해 주세요.",
            "sentence_style": "완성도 높은 정중한 문장",
            "key_features": ["전문성과 신뢰감", "체계적 정보 전달", "예의 바른 표현"]
        }
    }


    @classmethod
    def get_content_guideline(cls, content_type: str) -> Dict:
        """컨텐츠 유형별 지침 반환"""
        return cls.CONTENT_GUIDELINES.get(content_type, {})

    @classmethod
    def get_tone_guideline(cls, tone: str) -> Dict:
        """말투별 지침 반환"""
        return cls.TONE_GUIDELINES.get(tone, {})

    @classmethod
    def get_review_detail_guideline(cls, review_detail: str) -> Dict:
        """후기 세부 유형별 지침 반환"""
        return cls.REVIEW_DETAIL_GUIDELINES.get(review_detail, {})

    @classmethod
    def get_available_content_types(cls) -> List[str]:
        """사용 가능한 컨텐츠 유형 목록 반환"""
        return list(cls.CONTENT_GUIDELINES.keys())

    @classmethod
    def get_available_tones(cls) -> List[str]:
        """사용 가능한 말투 목록 반환"""
        return list(cls.TONE_GUIDELINES.keys())

    @classmethod
    def generate_title_suggestion_prompt(cls, main_keyword: str, content_type: str, sub_keywords: str = "", review_detail: str = "") -> str:
        """1단계: 제목 추천 프롬프트 생성 (공용 컴포넌트 활용)"""

        # 해당 유형의 지침 가져오기
        content_guideline = cls.get_content_guideline(content_type)

        if not content_guideline:
            content_type = "정보/가이드형"  # 기본값
            content_guideline = cls.get_content_guideline(content_type)

        approach = content_guideline.get("approach", "")
        keywords = content_guideline.get("keywords", [])
        focus_areas = content_guideline.get("focus_areas", [])

        # 후기 세부 유형 지침 가져오기 (후기/리뷰형일 때만)
        review_guideline = cls.get_review_detail_guideline(review_detail) if review_detail and content_type == "후기/리뷰형" else {}

        # 보조키워드 처리
        sub_keyword_text = ""
        sub_keyword_instruction = ""
        if sub_keywords.strip():
            sub_keyword_text = f"**보조키워드**: {sub_keywords}"
            sub_keyword_instruction = "- 보조키워드는 필수는 아니지만, 적절히 활용하면 더 구체적인 제목 생성 가능"

        prompt = f"""네이버 블로그 상위 노출에 유리한 '{content_type}' 스타일의 제목 10개를 추천해주세요.

**메인키워드**: {main_keyword}
{sub_keyword_text}

**{content_type} 특징**:
- 접근법: {approach}
- 핵심 키워드: {', '.join(keywords)}
- 중점 영역: {', '.join(focus_areas)}
{f'''
**후기 세부 유형**: {review_detail}
- 설명: {review_guideline.get("description", "")}
- 적절한 톤: {review_guideline.get("transparency", "")}''' if review_guideline else ''}

**제목 생성 규칙**:
1. 메인키워드를 자연스럽게 포함
2. 클릭 유도와 궁금증 자극
3. 30-60자 내외 권장
4. {content_type}의 특성 반영
5. 네이버 블로그 SEO 최적화
6. 이모티콘 사용 금지 (텍스트만 사용)
7. 구체적 년도 표기 금지 (2024, 2025 등 특정 년도 사용 금지. "최신", "현재" 등으로 대체)
{sub_keyword_instruction}

**출력 형식**:
JSON 형태로 정확히 10개 제목과 각 제목에 맞는 블로그 검색어를 함께 반환해주세요.

각 제목마다 "해당 제목과 유사한 내용의 블로그를 찾기 위한 네이버 블로그 검색어"를 함께 생성해주세요.
이 검색어는 다른 블로그를 검색해서 분석하여 참고용 자료로 활용됩니다.
검색어는 2-4개 단어 조합으로 구체적이고 관련성 높게 만들어주세요.

{{
  "titles_with_search": [
    {{
      "title": "제목1",
      "search_query": "관련 블로그 검색어1"
    }},
    {{
      "title": "제목2",
      "search_query": "관련 블로그 검색어2"
    }},
    ...
    {{
      "title": "제목10",
      "search_query": "관련 블로그 검색어10"
    }}
  ]
}}

각 제목은 {content_type}의 특성을 살리되, 서로 다른 접근 방식으로 다양하게 생성해주세요."""

        return prompt

    @classmethod
    def generate_blog_title_selection_prompt(cls, target_title: str, search_keyword: str, main_keyword: str, content_type: str, blog_titles: List[str], sub_keywords: str = "") -> str:
        """블로그 제목 선별 프롬프트 생성 - AI에게 30개 제목 중 관련도 높은 10개 선택 요청"""

        titles_text = "\n".join([f"{i+1}. {title}" for i, title in enumerate(blog_titles)])

        # 보조키워드 텍스트 준비
        sub_keywords_text = ""
        sub_keywords_criteria = ""
        if sub_keywords and sub_keywords.strip():
            sub_keywords_text = f"**보조 키워드**: {sub_keywords.strip()}"
            sub_keywords_criteria = f"6. 보조 키워드({sub_keywords.strip()})와 관련성이 있는 제목"

        prompt = f"""네이버 블로그에서 '{search_keyword}' 키워드로 검색한 블로그 제목들 중에서, 아래 조건에 가장 적합한 상위 10개를 선별해주세요.

**타겟 제목**: {target_title}
**메인 키워드**: {main_keyword}
{sub_keywords_text}
**검색 키워드**: {search_keyword}
**콘텐츠 유형**: {content_type}

**선별 기준**:
1. 타겟 제목과 주제적 관련성이 높은 글
2. 메인 키워드와 직접적으로 연관된 내용
3. {content_type} 유형에 적합한 접근방식의 글
4. 구체적이고 실용적인 정보를 담고 있을 것으로 예상되는 제목
5. 광고성이나 홍보성보다는 정보성 콘텐츠로 보이는 제목
{sub_keywords_criteria}

**검색된 블로그 제목들**:
{titles_text}

**출력 형식**:
위 제목들 중에서 관련도와 유용성이 높은 순서대로 상위 10개를 JSON 형태로 선별해주세요.

{{
  "selected_titles": [
    {{
      "rank": 1,
      "original_index": 3,
      "title": "선별된 제목 1",
      "relevance_reason": "선별 이유 (한 줄로 간단히)"
    }},
    {{
      "rank": 2,
      "original_index": 7,
      "title": "선별된 제목 2",
      "relevance_reason": "선별 이유 (한 줄로 간단히)"
    }},
    ...
    {{
      "rank": 10,
      "original_index": 25,
      "title": "선별된 제목 10",
      "relevance_reason": "선별 이유 (한 줄로 간단히)"
    }}
  ]
}}

각 제목이 왜 선택되었는지 간단한 이유와 함께 우선순위 순서대로 정확히 10개만 선별해주세요."""

        return prompt


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
    def generate_content_summary_prompt(selected_title: str, search_keyword: str, main_keyword: str, content_type: str, competitor_blogs: list, sub_keywords: str = "") -> str:
        """정보요약 AI용 1차 가공 프롬프트 생성 - JSON 입력 구조화"""

        # DEBUG: 파라미터 값 확인
        from src.foundation.logging import get_logger
        logger = get_logger("ai_prompts.summary_debug")
        logger.info(f"🔍 DEBUG summary_prompt: search_keyword='{search_keyword}', main_keyword='{main_keyword}'")

        import json

        # JSON 입력 데이터 구조화
        input_data = {
            "target_info": {
                "selected_title": selected_title,
                "search_keyword": search_keyword,
                "main_keyword": main_keyword,
                "content_type": content_type
            },
            "competitor_blogs": []
        }

        # 보조키워드가 있으면 추가
        if sub_keywords and sub_keywords.strip():
            input_data["target_info"]["sub_keywords"] = sub_keywords.strip()

        # 경쟁 블로그 데이터 추가
        for i, blog in enumerate(competitor_blogs, 1):
            input_data["competitor_blogs"].append({
                "blog_number": i,
                "title": blog.get('title', '제목 없음'),
                "content": blog.get('text_content', '내용 없음')[:2000]  # 내용 길이 제한
            })

        # JSON 문자열로 변환
        json_input = json.dumps(input_data, ensure_ascii=False, indent=2)

        # 1차 가공 프롬프트 (정보요약 AI용) - JSON 입력 구조
        summary_prompt = f"""아래 JSON 데이터를 분석해서 다음 형식으로 정확히 출력해주세요:

## 1. 경쟁 블로그 제목들
- (분석한 3개 블로그들의 제목을 나열)

## 2. 핵심 키워드
- (자주 나오는 관련 키워드들을 나열)

## 3. 필수 내용
- (모든 글이 다루는 공통 주제들을 정리)

## 4. 주요 포인트
- (각 글이 중점적으로 다루는 핵심 내용들을 정리)

## 5. 부족한 점
- (기존 글들이 놓친 부분이나 개선 가능한 점들을 정리)

**JSON 데이터 설명**:
- target_info: 내가 작성할 블로그의 정보
  - selected_title: 내가 선택한 블로그 제목 (실제 작성할 제목)
  - search_keyword: 관련 블로그를 찾기 위해 사용한 검색 키워드
  - main_keyword: 내 글의 핵심 타겟 키워드 (SEO 목표)
  - content_type: 내 글의 유형 (정보/가이드형, 후기/리뷰형 등)
  - sub_keywords: 보조 키워드들 (있는 경우에만 포함)
- competitor_blogs: search_keyword로 검색해서 찾은 경쟁사 분석용 참고 블로그 3개 (제목과 본문 내용)

**분석 데이터**:
```json
{json_input}
```

위 JSON 데이터를 기반으로 '{main_keyword}' 키워드와 '{content_type}' 컨텐츠 유형에 맞춰 분석해주세요.
각 항목마다 구체적이고 실용적인 내용을 포함해주세요."""

        return summary_prompt


class BlogAIPrompts:
    """2차 가공: 글작성 AI를 위한 프롬프트 템플릿"""
    
    @staticmethod
    def generate_content_analysis_prompt(main_keyword: str, sub_keywords: str, structured_data: Dict, content_type: str = "정보/가이드형", tone: str = "정중한 존댓말체", review_detail: str = "", blogger_identity: str = "", summary_result: str = "", selected_title: str = "", search_keyword: str = "") -> str:
        """네이버 SEO 최적화 콘텐츠 분석 기반 AI 프롬프트 생성 (컨텐츠 유형과 말투, 후기 세부 유형 반영)"""

        # DEBUG: 파라미터 값 확인
        from src.foundation.logging import get_logger
        logger = get_logger("ai_prompts.debug")
        logger.info(f"🔍 DEBUG ai_prompts: search_keyword='{search_keyword}', main_keyword='{main_keyword}'")

        competitor_info = structured_data.get("competitor_analysis", {})
        top_blogs = competitor_info.get("top_blogs", [])
        summary = competitor_info.get("summary", {})
        
        # 공용 컴포넌트에서 컨텐츠 지침 가져오기
        current_content = BlogPromptComponents.get_content_guideline(content_type)
        
        # 공용 컴포넌트에서 후기 세부 지침 가져오기
        current_review_detail = BlogPromptComponents.get_review_detail_guideline(review_detail) if review_detail else {}
        
        # 공용 컴포넌트에서 말투 지침 가져오기
        current_tone = BlogPromptComponents.get_tone_guideline(tone)
        
        # 평균 태그 개수 계산
        avg_tag_count = sum(len(blog.get("tags", [])) for blog in top_blogs) // max(1, len(top_blogs)) if top_blogs else 5
        
        # 평균 이미지 개수 계산
        avg_image_count = sum(blog.get("statistics", {}).get("image_count", 0) for blog in top_blogs) // max(1, len(top_blogs)) if top_blogs else 3
        

        # 블로그 소개 처리
        if blogger_identity and blogger_identity.strip():
            role_description = f"당신은 네이버 블로그에서 {blogger_identity.strip()} 블로그를 운영하고 있습니다. 독자들이 진짜 도움이 되고 재미있게 읽을 수 있는 글을 쓰는 것이 목표입니다."
        else:
            role_description = "당신은 네이버 블로그에서 인기 있는 글을 쓰는 블로거입니다. 독자들이 진짜 도움이 되고 재미있게 읽을 수 있는 글을 쓰는 것이 목표입니다."

        prompt = f"""
# AI 역할 설정
{role_description}

## 참고할 경쟁 블로그 요약 정보
'{search_keyword}'로 검색시 노출되는 상위 {len(top_blogs)}개 블로그 글을 요약한 결과입니다. 이를 참고하여 더 나은 독창적인 컨텐츠를 작성해주세요:

{summary_result if summary_result.strip() else '참고할 만한 경쟁사 분석 정보가 없으니, 자연스럽고 유용한 컨텐츠로 작성해주세요.'}

# 작성 지침

## 🚨 절대 규칙: 제목 고정 🚨
**❌ 제목 변경 절대 금지 ❌**
**✅ 반드시 다음 제목을 그대로 복사해서 사용: "{selected_title}"**
**🔒 이 제목을 1글자도 바꾸지 말고 정확히 그대로 출력하세요 🔒**

## 기본 정보
- **작성할 글 제목**: "{selected_title}"
- **메인 키워드**: "{main_keyword}"
- **보조 키워드**: "{sub_keywords if sub_keywords.strip() else '메인 키워드와 관련된 보조 키워드들을 3-5개 직접 생성하여 활용'}"
- **컨텐츠 유형**: {content_type} ({current_content['approach']})"""

        # 후기 세부 유형 가이드라인 추가 (후기/리뷰형일 때만) - 기본 정보 바로 다음에 위치
        if current_review_detail:
            prompt += f"""

## 후기 세부 유형
- **후기 유형**: {review_detail}
- **후기 설명**: {current_review_detail['description']}
- **투명성 원칙**: {current_review_detail['transparency']}
- **핵심 포인트**: {', '.join(current_review_detail['key_points'])}"""

        prompt += f"""

## 말투 지침
- **선택된 말투**: {tone}
- **말투 스타일**: {current_tone['style']}
- **예시 표현**: {', '.join(current_tone['examples'])}
- **문장 특징**: {current_tone['sentence_style']}
- **주요 특색**: {', '.join(current_tone['key_features'])}
- **마무리 문구**: {current_tone['ending']}

## 글 구성 방식
- **글 구조**: {current_content['structure']}
- **주요 초점**: {', '.join(current_content['focus_areas'])}
- **핵심 표현**: {', '.join(current_content['keywords'])}

## SEO 및 기술적 요구사항
- 글자 수: 1,700-2,000자 (공백 제외)
- 메인 키워드: 5-6회 자연 반복
- 보조 키워드: 각각 3-4회 사용
- 이미지: {avg_image_count}개 이상 (이미지) 표시로 배치, 필요시 연속 4개 배치 가능
- 동영상: 1개 (동영상) 표시로 배치

## 글쓰기 품질 요구사항
- **자연스러운 문체**: AI 생성티 없는 개성 있고 자연스러운 어투로 작성
- **완전한 내용**: XX공원, OO병원 같은 placeholder 사용 금지. 구체적인 정보가 없다면 "근처 공원", "동네 병원" 등 일반적 표현 사용"""



        prompt += f"""


# 🔥 출력 형식 🔥

🚨🚨🚨 제목 변경 절대 금지! 아래 제목을 정확히 복사하세요! 🚨🚨🚨
**제목: {selected_title}** ← 이것을 정확히 복사해서 출력!

다른 설명 없이 아래 형식으로만 출력하세요:

```
제목: {selected_title}

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
{'[상위 블로그 인기 태그 참고: ' + ', '.join(['#' + tag.lstrip("#") for tag in summary.get("common_tags", [])]) + ']' if summary.get("common_tags") else ''}
[메인키워드와 보조키워드를 활용하여 글 내용에 적합한 태그 5개 이상 작성]
```
"""
        return prompt.strip()
    

def create_ai_request_data(main_keyword: str, sub_keywords: str, analyzed_blogs: List[Dict], content_type: str = "정보/가이드형", tone: str = "정중한 존댓말체", review_detail: str = "", blogger_identity: str = "", summary_result: str = "", selected_title: str = "", search_keyword: str = "") -> Dict:
    """AI 요청용 데이터 생성 (컨텐츠 유형과 말투, 후기 세부 유형 포함)"""
    try:
        structure_analyzer = BlogContentStructure()
        structured_data = structure_analyzer.analyze_blog_structure(analyzed_blogs)
        structured_data["keyword"] = main_keyword  # 기존 호환성을 위해 메인 키워드 저장

        # AI 프롬프트 생성 (스타일 옵션 포함)
        prompt_generator = BlogAIPrompts()
        ai_prompt = prompt_generator.generate_content_analysis_prompt(main_keyword, sub_keywords, structured_data, content_type, tone, review_detail, blogger_identity, summary_result, selected_title, search_keyword)
        
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


