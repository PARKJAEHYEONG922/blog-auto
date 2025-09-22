// 자막 파싱 테스트
function parseYouTubeRawSubtitles(rawText) {
  try {
    console.log(`🔍 [파싱] 원시 데이터 분석 시작 (${rawText.length}자)`);
    console.log(`🔍 [파싱] 데이터 샘플: ${rawText.substring(0, 300)}...`);
    
    const subtitleTexts = [];
    
    // 방법 1: 간단한 split 방식으로 segs utf8 찾기
    const segments = rawText.split('segs utf8');
    console.log(`🔍 [파싱] segs utf8로 분할: ${segments.length}개 세그먼트`);
    
    for (let i = 1; i < segments.length; i++) { // 첫 번째는 메타데이터이므로 제외
      let segment = segments[i].trim();
      
      // 다음 tStartMs까지만 자르기
      const nextTimestamp = segment.indexOf('tStartMs');
      if (nextTimestamp > 0) {
        segment = segment.substring(0, nextTimestamp);
      }
      
      // 앞뒤 공백, 쉼표 제거
      segment = segment.replace(/^[\s,]+|[\s,]+$/g, '');
      
      if (segment && segment.length > 1) {
        subtitleTexts.push(segment);
        console.log(`🔍 [파싱] 세그먼트 ${i}: "${segment}"`);
      }
    }
    
    // 방법 2: 세그먼트가 없으면 한국어 텍스트 직접 추출
    if (subtitleTexts.length === 0) {
      console.log(`🔍 [파싱] 대체 방법: 한국어 텍스트 직접 추출`);
      
      // 한국어 문장 패턴 추출 (더 넓은 범위)
      const koreanPattern = /[가-힣][가-힣\s\d?!.,()~]+[가-힣?!.]/g;
      const matches = rawText.match(koreanPattern);
      
      if (matches) {
        console.log(`🔍 [파싱] 한국어 패턴 ${matches.length}개 발견`);
        for (const match of matches) {
          const cleaned = match.trim();
          // 메타데이터 키워드가 포함되지 않은 것만
          if (cleaned.length > 3 && 
              !cleaned.includes('wireMagic') && 
              !cleaned.includes('tStartMs') &&
              !cleaned.includes('dDurationMs') &&
              !cleaned.includes('pb3')) {
            subtitleTexts.push(cleaned);
            console.log(`🔍 [파싱] 한국어 텍스트: "${cleaned}"`);
          }
        }
      }
    }
    
    // 결과 조합
    const result = subtitleTexts.join(' ').replace(/\s+/g, ' ').trim();
    
    console.log(`📝 [파싱] 최종 결과: ${subtitleTexts.length}개 세그먼트, ${result.length}자`);
    console.log(`📝 [파싱] 최종 텍스트: ${result.substring(0, 150)}...`);
    
    return result;
    
  } catch (error) {
    console.error('❌ [파싱] 원시 자막 데이터 파싱 실패:', error);
    return rawText; // 실패 시 원본 반환
  }
}

// 테스트 데이터
const testData = "wireMagic pb3 , pens , wsWinStyles , wpWinPositions , events tStartMs 1167, dDurationMs 4471, segs utf8 단호박 , 감자 , 고구마 중 어떤 것이 우리집 강아지 간식으로 좋을까요? , tStartMs 6039, dDurationMs 4972, segs utf8 그리고 셋 중에 어떤 간식이 우리 강아지 건강, 다이어트에도 좋을까요? , tStartMs 11544, dDurationMs 3571, segs utf8 보통 GI 나 GL 지수로 많이들 비교하시는데요";

console.log("=== 자막 파싱 테스트 ===");
const result = parseYouTubeRawSubtitles(testData);
console.log("\n=== 최종 결과 ===");
console.log(result);