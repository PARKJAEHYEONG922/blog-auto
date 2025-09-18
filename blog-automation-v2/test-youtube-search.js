const { testYouTubeAnalysis } = require('./src/services/youtube-analysis-engine');

async function runTest() {
  try {
    console.log('🎯 YouTube 분석 엔진 테스트 시작\n');
    
    // 테스트 키워드
    const keyword = '블로그 작성법';
    
    console.log(`검색 키워드: "${keyword}"`);
    console.log('상위 3개 동영상 분석 + 자막 추출\n');
    
    // 분석 실행
    const result = await testYouTubeAnalysis(keyword);
    
    console.log('\n🎉 테스트 완료!');
    console.log('\n=== 최종 결과 ===');
    console.log(`키워드: ${result.keyword}`);
    console.log(`발견된 총 동영상: ${result.totalVideosFound}개`);
    console.log(`분석된 동영상: ${result.analyzedVideos.length}개`);
    console.log(`자막 있는 동영상: ${result.summary.videosWithSubtitles}개`);
    console.log(`평균 분석 점수: ${result.summary.averageScore}점`);
    
    if (result.summary.topVideo) {
      console.log(`\n🏆 최고 점수 동영상:`);
      console.log(`   제목: ${result.summary.topVideo.title}`);
      console.log(`   채널: ${result.summary.topVideo.channelTitle}`);
      console.log(`   조회수: ${result.summary.topVideo.viewCount.toLocaleString()}회`);
      console.log(`   우선순위: ${result.summary.topVideo.priority}점`);
    }

  } catch (error) {
    console.error('❌ 테스트 실패:', error);
  }
}

// 테스트 실행
runTest();