import { BlogCrawler } from './src/services/blog-crawler';

async function testBlogCrawler() {
  console.log('🔍 블로그 크롤러 테스트 시작...');
  
  // 사용자가 제공한 실제 네이버 블로그 URL로 테스트 (레거시 방식으로)
  const testBlogs = [
    {
      url: 'https://blog.naver.com/kimhw1020/223188057432',
      title: '실제 블로그 포스트',
      relevanceReason: '사용자 제공 테스트 URL - 레거시 방식 테스트'
    }
  ];
  
  const crawler = new BlogCrawler((progress) => {
    console.log(`진행률: ${progress.current}/${progress.total} - ${progress.status}: ${progress.url}`);
  });
  
  try {
    console.log('🚀 크롤링 시작...');
    const results = await crawler.crawlSelectedBlogs(testBlogs, 1);
    console.log('✅ 크롤링 완료!');
    
    if (results.length > 0) {
      const result = results[0];
      console.log('\n📊 크롤링 결과:');
      console.log(`📝 제목: ${result.title}`);
      console.log(`📄 본문 길이: ${result.contentLength}자`);
      console.log(`🖼️ 이미지: ${result.imageCount}개`);
      console.log(`🎬 GIF: ${result.gifCount}개`);
      console.log(`🎥 동영상: ${result.videoCount}개`);
      console.log(`✅ 성공 여부: ${result.success}`);
      
      if (result.error) {
        console.log(`❌ 오류: ${result.error}`);
      }
      
      if (result.textContent && result.textContent.length > 0) {
        console.log(`\n📖 본문 미리보기 (처음 200자):`);
        console.log(result.textContent.substring(0, 200) + '...');
      } else {
        console.log('\n⚠️ 본문이 추출되지 않았습니다.');
      }
    }
    
  } catch (error) {
    console.error('❌ 테스트 실패:', error);
  }
}

// 즉시 실행
testBlogCrawler();