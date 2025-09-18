const { BlogCrawler } = require('./src/services/blog-crawler.ts');

async function testBlogCrawler() {
  console.log('🔍 블로그 크롤러 테스트 시작...');
  
  // 테스트용 네이버 블로그 URL (공개 블로그)
  const testBlogs = [
    {
      url: 'https://blog.naver.com/PostView.naver?blogId=example&logNo=123',
      title: '테스트 블로그 포스트'
    }
  ];
  
  const crawler = new BlogCrawler((progress) => {
    console.log(`진행률: ${progress.current}/${progress.total} - ${progress.status}: ${progress.url}`);
  });
  
  try {
    const results = await crawler.crawlSelectedBlogs(testBlogs, 1);
    console.log('✅ 크롤링 결과:', results);
    
    if (results.length > 0) {
      const result = results[0];
      console.log(`📝 제목: ${result.title}`);
      console.log(`📄 본문 길이: ${result.contentLength}자`);
      console.log(`🖼️ 이미지: ${result.imageCount}개`);
      console.log(`🎬 GIF: ${result.gifCount}개`);
      console.log(`🎥 동영상: ${result.videoCount}개`);
      console.log(`✅ 성공 여부: ${result.success}`);
      if (result.error) {
        console.log(`❌ 오류: ${result.error}`);
      }
    }
    
  } catch (error) {
    console.error('❌ 테스트 실패:', error);
  }
}

testBlogCrawler();