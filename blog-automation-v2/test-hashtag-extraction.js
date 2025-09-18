/**
 * 네이버 블로그 해시태그 추출 기능 테스트
 */

const { BlogCrawler } = require('./dist/services/blog-crawler');

async function testHashtagExtraction() {
  console.log('🧪 네이버 블로그 해시태그 추출 테스트 시작...\n');
  
  const crawler = new BlogCrawler();
  
  // 테스트할 네이버 블로그 URL
  const testUrls = [
    'https://blog.naver.com/test/123',  // 실제 네이버 블로그 URL로 교체 필요
  ];
  
  for (const url of testUrls) {
    try {
      console.log(`🔗 테스트 URL: ${url}`);
      
      // 크롤링 시도
      const result = await crawler.crawlBlogContent(url, '테스트 제목');
      
      if (result.success) {
        console.log(`✅ 크롤링 성공`);
        console.log(`📝 제목: ${result.title}`);
        console.log(`📄 콘텐츠 길이: ${result.contentLength}자`);
        console.log(`🖼️ 이미지: ${result.imageCount}개`);
        console.log(`🏷️ 해시태그: [${result.tags.join(', ')}] (${result.tags.length}개)`);
        
        if (result.tags.length > 0) {
          console.log('✅ 해시태그 추출 성공!');
        } else {
          console.log('⚠️ 해시태그가 추출되지 않았습니다');
        }
      } else {
        console.log(`❌ 크롤링 실패: ${result.error}`);
      }
      
      console.log('─'.repeat(60));
      
    } catch (error) {
      console.error(`❌ 테스트 오류: ${error.message}`);
    }
  }
  
  console.log('\n🧪 해시태그 추출 테스트 완료');
}

// 테스트 실행
if (require.main === module) {
  testHashtagExtraction().catch(console.error);
}

module.exports = { testHashtagExtraction };