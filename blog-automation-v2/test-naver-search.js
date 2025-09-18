const { naverAPI } = require('./src/services/naver-api.ts');

async function testNaverSearch() {
  console.log('🔍 네이버 API 블로그 검색 테스트: "강아지초콜렛"');
  
  try {
    // 네이버 API 설정 로드
    await naverAPI.loadConfig();
    
    // 블로그 검색 (최대 50개)
    const blogResults = await naverAPI.searchBlogs('강아지초콜렛', 50);
    
    console.log(`📝 총 ${blogResults.length}개 블로그 결과:`);
    console.log('');
    
    // URL 도메인별로 분류
    const urlDomains = {};
    
    blogResults.forEach((blog, index) => {
      const url = blog.link;
      let domain = '';
      
      try {
        const urlObj = new URL(url);
        domain = urlObj.hostname;
      } catch (e) {
        domain = 'invalid-url';
      }
      
      if (!urlDomains[domain]) {
        urlDomains[domain] = [];
      }
      urlDomains[domain].push({
        index: index + 1,
        title: blog.title.replace(/<[^>]*>/g, ''), // HTML 태그 제거
        url: url,
        blogger: blog.bloggername
      });
    });
    
    // 도메인별 통계 출력
    console.log('📊 도메인별 분포:');
    Object.keys(urlDomains).sort().forEach(domain => {
      console.log(`  ${domain}: ${urlDomains[domain].length}개`);
    });
    console.log('');
    
    // 각 도메인별 상세 정보
    Object.keys(urlDomains).sort().forEach(domain => {
      console.log(`🌐 ${domain} (${urlDomains[domain].length}개):`);
      urlDomains[domain].slice(0, 3).forEach(item => { // 각 도메인당 최대 3개만
        console.log(`  ${item.index}. ${item.title}`);
        console.log(`     URL: ${item.url}`);
        console.log(`     블로거: ${item.blogger}`);
        console.log('');
      });
      if (urlDomains[domain].length > 3) {
        console.log(`  ... 외 ${urlDomains[domain].length - 3}개 더`);
        console.log('');
      }
    });
    
  } catch (error) {
    console.error('❌ 테스트 실패:', error);
    
    if (error.message && error.message.includes('API')) {
      console.log('💡 네이버 API 설정이 필요할 수 있습니다.');
      console.log('   앱에서 API 설정을 먼저 완료해주세요.');
    }
  }
}

testNaverSearch();