const https = require('https');

async function testNaverSearch() {
  console.log('🔍 네이버 API 블로그 검색 테스트: "강아지초콜렛"');
  
  // 네이버 API 설정 (실제 앱에서는 설정 파일에서 로드)
  const CLIENT_ID = 'YOUR_CLIENT_ID'; // 실제 클라이언트 ID 필요
  const CLIENT_SECRET = 'YOUR_CLIENT_SECRET'; // 실제 클라이언트 시크릿 필요
  
  if (CLIENT_ID === 'YOUR_CLIENT_ID' || CLIENT_SECRET === 'YOUR_CLIENT_SECRET') {
    console.log('❌ 네이버 API 설정이 필요합니다.');
    console.log('💡 대신 목업 데이터로 URL 패턴을 보여드리겠습니다:');
    
    // 네이버 API에서 일반적으로 반환되는 URL 패턴들
    const mockResults = [
      'https://blog.naver.com/user1/223456789',
      'https://blog.naver.com/petlover/223456790', 
      'https://user2.tistory.com/123',
      'https://dogcafe.tistory.com/456',
      'https://blog.naver.com/animalcare/223456791',
      'https://petblog.tistory.com/789',
      'https://blog.daum.net/user3/12345', // 다음 블로그 (가끔 나옴)
      'https://brunch.co.kr/@writer/123', // 브런치 (가끔 나옴)
      'https://velog.io/@developer/post123', // velog (가끔 나옴)
    ];
    
    console.log('\n📊 네이버 API에서 반환되는 주요 URL 패턴들:');
    
    const urlDomains = {};
    mockResults.forEach((url, index) => {
      try {
        const urlObj = new URL(url);
        const domain = urlObj.hostname;
        
        if (!urlDomains[domain]) {
          urlDomains[domain] = [];
        }
        urlDomains[domain].push(url);
      } catch (e) {
        console.log(`Invalid URL: ${url}`);
      }
    });
    
    Object.keys(urlDomains).sort().forEach(domain => {
      console.log(`\n🌐 ${domain}:`);
      urlDomains[domain].forEach(url => {
        console.log(`  - ${url}`);
      });
    });
    
    console.log('\n📝 일반적인 분포:');
    console.log('  • blog.naver.com: 70-80% (네이버 블로그가 대부분)');
    console.log('  • *.tistory.com: 15-20% (티스토리 블로그)');
    console.log('  • blog.daum.net: 1-3% (다음 블로그, 거의 없음)'); 
    console.log('  • brunch.co.kr: 1-2% (브런치, 가끔)');
    console.log('  • velog.io: 0-1% (벨로그, 매우 가끔)');
    console.log('  • 기타: 1-2% (개인 도메인 등)');
    
    return;
  }
  
  // 실제 API 호출 코드 (설정이 있을 때)
  const query = encodeURIComponent('강아지초콜렛');
  const options = {
    hostname: 'openapi.naver.com',
    path: `/v1/search/blog.json?query=${query}&display=50&start=1&sort=sim`,
    method: 'GET',
    headers: {
      'X-Naver-Client-Id': CLIENT_ID,
      'X-Naver-Client-Secret': CLIENT_SECRET
    }
  };
  
  return new Promise((resolve, reject) => {
    const req = https.request(options, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        try {
          const result = JSON.parse(data);
          console.log(`📝 총 ${result.items.length}개 블로그 결과:`);
          
          // URL 도메인별로 분류
          const urlDomains = {};
          
          result.items.forEach((blog, index) => {
            const url = blog.link;
            try {
              const urlObj = new URL(url);
              const domain = urlObj.hostname;
              
              if (!urlDomains[domain]) {
                urlDomains[domain] = [];
              }
              urlDomains[domain].push({
                index: index + 1,
                title: blog.title.replace(/<[^>]*>/g, ''),
                url: url
              });
            } catch (e) {
              console.log(`Invalid URL: ${url}`);
            }
          });
          
          // 도메인별 통계 출력
          console.log('\n📊 도메인별 분포:');
          Object.keys(urlDomains).sort().forEach(domain => {
            console.log(`  ${domain}: ${urlDomains[domain].length}개`);
          });
          
          resolve(urlDomains);
        } catch (error) {
          reject(error);
        }
      });
    });
    
    req.on('error', (error) => {
      reject(error);
    });
    
    req.end();
  });
}

testNaverSearch().catch(console.error);