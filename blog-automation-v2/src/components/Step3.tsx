import React, { useState, useRef, useEffect } from 'react';
import { WorkflowData, BlogWritingResult } from '../App';

interface Step3Props {
  data: WorkflowData;
  onComplete: (data: Partial<WorkflowData>) => void;
  onBack: () => void;
}

const Step3: React.FC<Step3Props> = ({ data, onComplete, onBack }) => {
  const editorRef = useRef<HTMLDivElement>(null);
  const [isPublishing, setIsPublishing] = useState(false);
  const [editedContent, setEditedContent] = useState('');
  const [charCount, setCharCount] = useState(0);
  const [charCountWithSpaces, setCharCountWithSpaces] = useState(0);
  const [currentFontSize, setCurrentFontSize] = useState('15px');

  // 폰트 크기 옵션
  const fontSizes = [
    { name: '대제목 (24px)', size: '24px', weight: 'bold' },
    { name: '소제목 (19px)', size: '19px', weight: 'bold' },
    { name: '강조 (16px)', size: '16px', weight: 'bold' },
    { name: '일반 (15px)', size: '15px', weight: 'normal' }
  ];

  // 글쓰기 결과 가져오기
  useEffect(() => {
    if (data.writingResult && data.writingResult.success) {
      const content = data.writingResult.content || '';
      // 마크다운 처리해서 HTML로 변환
      const processedContent = processMarkdown(content);
      setEditedContent(processedContent);
      
      if (editorRef.current) {
        editorRef.current.innerHTML = processedContent;
        updateCharCount();
      }
    }
  }, [data.writingResult]);

  // 마크다운 표를 네이버 블로그 표 구조로 변환
  const convertMarkdownTable = (lines: string[]): string => {
    const tableRows: string[] = [];
    let isHeaderRow = true;
    
    for (const line of lines) {
      if (line.includes('|') && !line.includes('---')) {
        const cells = line.split('|').filter(cell => cell.trim() !== '').map(cell => cell.trim());
        const cellWidth = (100 / cells.length).toFixed(2);
        
        const rowCells = cells.map(cellContent => {
          let processedContent = cellContent.replace(/\*\*([^*]+)\*\*/g, '<span class="se-ff-nanumgothic se-fs16" style="color: rgb(0, 0, 0); font-weight: bold;">$1</span>');
          
          return `
            <td class="__se-unit se-cell" style="width: ${cellWidth}%; height: 43px;">
              <div class="se-module se-module-text">
                <p class="se-text-paragraph se-text-paragraph-align-left" style="line-height: 1.6;">
                  <span class="se-ff-nanumgothic se-fs15" style="color: rgb(0, 0, 0);">${processedContent}</span>
                </p>
              </div>
            </td>`;
        }).join('');
        
        tableRows.push(`<tr class="se-tr">${rowCells}</tr>`);
        isHeaderRow = false;
      }
    }
    
    return `
      <div class="se-component se-table se-l-default">
        <div class="se-component-content">
          <div class="se-section se-section-table se-l-default se-section-align-left">
            <div class="se-table-container">
              <table class="se-table-content se-reflow-toggle">
                <tbody>
                  ${tableRows.join('')}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>`;
  };

  // AI 생성 콘텐츠 모바일 최적화 처리
  const cleanAIGeneratedContent = (content: string): string => {
    try {
      let cleanedContent = content.trim();
      
      // 코드 블록(```) 제거
      if (cleanedContent.startsWith('```') && cleanedContent.endsWith('```')) {
        cleanedContent = cleanedContent.slice(3, -3).trim();
      }
      
      // 연속된 이미지들 정규화 (모바일에서 보기 좋게)
      // (이미지) (이미지) → (이미지)(이미지)
      cleanedContent = cleanedContent.replace(/\(이미지\)\s*[,\s]*\s*\(이미지\)/g, '(이미지)(이미지)');
      // [이미지] [이미지] → [이미지][이미지]  
      cleanedContent = cleanedContent.replace(/\[이미지\]\s*[,\s]*\s*\[이미지\]/g, '[이미지][이미지]');
      
      // 3개 이상 연속된 이미지들도 처리
      cleanedContent = cleanedContent.replace(/(\(이미지\)+)\s*[,\s]*\s*\(이미지\)/g, '$1(이미지)');
      cleanedContent = cleanedContent.replace(/(\[이미지\]+)\s*[,\s]*\s*\[이미지\]/g, '$1[이미지]');
      
      // 이미지 그룹 앞뒤 텍스트와 분리 (모바일 가독성)
      cleanedContent = cleanedContent.replace(/([^\n\r])(\(이미지\)+)/g, '$1\n$2');
      cleanedContent = cleanedContent.replace(/([^\n\r])(\[이미지\]+)/g, '$1\n$2');
      cleanedContent = cleanedContent.replace(/(\(이미지\)+)([^\n\r])/g, '$1\n$2');
      cleanedContent = cleanedContent.replace(/(\[이미지\]+)([^\n\r])/g, '$1\n$2');
      
      // 불필요한 구조 설명 제거
      const patternsToRemove = [
        /\[서론 - 3초의 법칙으로 핵심 답변 즉시 제시\]/gi,
        /\[본문은 다양한 형식으로 구성하세요\]/gi,
        /\[결론 - 요약 및 독자 행동 유도\]/gi,
        /\[메인키워드와 보조키워드를 활용하여 글 내용에 적합한 태그.*?\]/gi,
        /\[상위 블로그 인기 태그 참고:.*?\]/gi
      ];
      
      for (const pattern of patternsToRemove) {
        cleanedContent = cleanedContent.replace(pattern, '');
      }
      
      // 해시태그 정리
      cleanedContent = cleanHashtags(cleanedContent);
      
      // 모바일 최적화: 25자 기준 줄바꿈 적용
      cleanedContent = applyMobileOptimization(cleanedContent);
      
      // 연속된 공백과 줄바꿈 정리
      cleanedContent = cleanedContent.replace(/\n\s*\n\s*\n/g, '\n\n');
      cleanedContent = cleanedContent.trim();
      
      return cleanedContent;
    } catch (error) {
      console.warn('콘텐츠 정리 중 오류:', error);
      return content;
    }
  };

  // 해시태그 정리: 중복 제거하고 한 줄로 정리
  const cleanHashtags = (content: string): string => {
    try {
      // 모든 해시태그 찾기
      const hashtags = content.match(/#\w+/g) || [];
      
      if (hashtags.length === 0) {
        return content;
      }
      
      // 중복 제거하되 순서 유지
      const seen = new Set<string>();
      const uniqueHashtags: string[] = [];
      
      for (const tag of hashtags) {
        if (!seen.has(tag.toLowerCase())) {
          seen.add(tag.toLowerCase());
          uniqueHashtags.push(tag);
        }
      }
      
      // 원본에서 해시태그 부분 제거
      const contentWithoutTags = content.replace(/#\w+/g, '').trim();
      
      // 정리된 태그들을 마지막에 한 줄로 추가
      if (uniqueHashtags.length > 0) {
        const tagsLine = uniqueHashtags.join(' ');
        return `${contentWithoutTags}\n\n${tagsLine}`;
      }
      
      return contentWithoutTags;
    } catch (error) {
      console.warn('해시태그 정리 중 오류:', error);
      return content;
    }
  };

  // 25자 기준 줄바꿈 (모바일 최적화)
  const splitTextByLength = (text: string, targetLength: number = 25): string[] => {
    if (text.length <= targetLength + 3) {
      return [text];
    }
    
    const result: string[] = [];
    let current = text;
    
    while (current.length > targetLength + 3) {
      // 25±3자 범위에서 가장 적절한 공백 찾기
      let bestPos = targetLength;
      
      // targetLength-3 ~ targetLength+5 범위에서 공백 찾기
      for (let i = Math.max(targetLength - 3, 10); i < Math.min(targetLength + 6, current.length); i++) {
        if (current[i] === ' ') {
          bestPos = i;
          break;
        }
      }
      
      // 공백을 찾았으면 그 위치에서 분리
      if (bestPos < current.length && current[bestPos] === ' ') {
        result.push(current.substring(0, bestPos).trim());
        current = current.substring(bestPos).trim();
      } else {
        // 공백이 없으면 targetLength에서 강제 분리
        result.push(current.substring(0, targetLength));
        current = current.substring(targetLength);
      }
    }
    
    // 남은 텍스트 추가
    if (current.trim()) {
      result.push(current.trim());
    }
    
    return result;
  };

  // 구조화된 콘텐츠인지 판별 (리스트, 단계별 설명 등은 줄바꿈하지 않음)
  const isStructuredContent = (line: string): boolean => {
    try {
      const lineStrip = line.trim();
      
      // 해시태그 줄 (# 기호가 여러 개 있는 경우 - 줄바꿈 제외)
      if (lineStrip.includes('#') && lineStrip.split(' ').filter(part => part.startsWith('#')).length >= 2) {
        return true;
      }
      
      // 마크다운 소제목 (## 또는 ###로 시작 - 줄바꿈 제외)
      if (lineStrip.startsWith('## ') || lineStrip.startsWith('### ')) {
        return true;
      }
      
      // 체크리스트/불릿 포인트 패턴 (다양한 형태)
      const bulletPatterns = [
        '✓ ', '✔ ', '✔️ ', '☑ ', '☑️ ', '✅ ',  // 체크마크
        '- ', '• ', '◦ ', '▪ ', '▫ ', '‣ ',     // 불릿
        '→ ', '➤ ', '► ', '▶ ', '🔸 ', '🔹 ',    // 화살표/도형
        '★ ', '⭐ ', '🌟 ', '💡 ', '📌 ', '🎯 '   // 기타 강조
      ];
      
      for (const pattern of bulletPatterns) {
        if (lineStrip.startsWith(pattern)) {
          return true;
        }
      }
      
      // 번호 목록 패턴 (숫자, 로마자, 한글 등)
      // 1. 2. 3. 또는 1) 2) 3) 패턴
      if (lineStrip.length > 0 && /^\d+[.)]\s/.test(lineStrip)) {
        return true;
      }
      
      // 로마자 패턴 (a. b. c. 또는 A. B. C.)
      if (lineStrip.length >= 3 && /^[a-zA-Z][.)]\s/.test(lineStrip)) {
        return true;
      }
      
      // 한글 자모 패턴 (가. 나. 다. 또는 ㄱ. ㄴ. ㄷ.)
      const koreanChars = 'ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅍㅎ가나다라마바사아자차카타파하';
      if (lineStrip.length >= 3 && lineStrip[1] === '.' && koreanChars.includes(lineStrip[0])) {
        return true;
      }
      
      // 단계별 패턴 (**1단계:**, **2단계:** 등)
      if (lineStrip.includes('단계:') || lineStrip.includes('**단계')) {
        return true;
      }
      
      // 표 형태나 구조화된 데이터 (: 기호가 많이 있는 경우)
      if ((lineStrip.match(/:/g) || []).length >= 2) {
        return true;
      }
      
      // 마크다운 표 형태 (| 기호로 구분)
      if (lineStrip.startsWith('|') && lineStrip.endsWith('|') && (lineStrip.match(/\|/g) || []).length >= 3) {
        return true;
      }
      
      // 표 구분선 (---|---|--- 형태)
      if (lineStrip.includes('---') && lineStrip.includes('|')) {
        return true;
      }
      
      // 짧은 줄 (30자 이하)
      if (lineStrip.length <= 30) {
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('구조화된 콘텐츠 판별 오류:', error);
      return false;
    }
  };

  // 모바일 최적화 텍스트 포맷팅 적용
  const applyMobileOptimization = (content: string): string => {
    const lines = content.split('\n');
    const optimizedLines: string[] = [];
    
    for (const line of lines) {
      const trimmed = line.trim();
      
      // 빈 줄이나 구조화된 콘텐츠는 그대로 유지
      if (!trimmed || isStructuredContent(trimmed)) {
        optimizedLines.push(line);
        continue;
      }
      
      // 긴 줄인 경우 25자 기준으로 분할
      if (trimmed.length > 30) {
        const splitLines = splitTextByLength(trimmed, 25);
        optimizedLines.push(...splitLines);
      } else {
        optimizedLines.push(line);
      }
    }
    
    return optimizedLines.join('\n');
  };

  // 마크다운을 네이버 블로그 호환 HTML로 변환
  const processMarkdown = (content: string): string => {
    // 먼저 모바일 최적화 처리
    const cleanedContent = cleanAIGeneratedContent(content);
    
    const lines = cleanedContent.split('\n');
    const result: string[] = [];
    let i = 0;
    
    while (i < lines.length) {
      const line = lines[i];
      
      // 표 감지 (| 포함된 연속 라인들)
      if (line.includes('|')) {
        const tableLines: string[] = [];
        let j = i;
        
        // 연속된 표 라인들 수집
        while (j < lines.length && (lines[j].includes('|') || lines[j].includes('---'))) {
          tableLines.push(lines[j]);
          j++;
        }
        
        if (tableLines.length > 0) {
          result.push(convertMarkdownTable(tableLines));
          i = j;
          continue;
        }
      }
      
      // 일반 텍스트 처리
      if (line.trim().startsWith('## ')) {
        const text = line.substring(line.indexOf('## ') + 3);
        result.push(`<p class="se-text-paragraph se-text-paragraph-align-left" style="line-height: 1.8;"><span class="se-ff-nanumgothic se-fs24" style="color: rgb(0, 0, 0); font-weight: bold;">${text}</span></p>`);
      } else if (line.trim().startsWith('### ')) {
        const text = line.substring(line.indexOf('### ') + 4);
        result.push(`<p class="se-text-paragraph se-text-paragraph-align-left" style="line-height: 1.8;"><span class="se-ff-nanumgothic se-fs19" style="color: rgb(0, 0, 0); font-weight: bold;">${text}</span></p>`);
      } else if (line.trim() === '') {
        result.push(`<p class="se-text-paragraph se-text-paragraph-align-left" style="line-height: 1.8;"><span class="se-ff-nanumgothic se-fs15" style="color: rgb(0, 0, 0);">&nbsp;</span></p>`);
      } else {
        // **강조** 처리
        let processedLine = line.replace(/\*\*([^*]+)\*\*/g, '<span class="se-ff-nanumgothic se-fs16" style="color: rgb(0, 0, 0); font-weight: bold;">$1</span>');
        result.push(`<p class="se-text-paragraph se-text-paragraph-align-left" style="line-height: 1.8;"><span class="se-ff-nanumgothic se-fs15" style="color: rgb(0, 0, 0);">${processedLine}</span></p>`);
      }
      
      i++;
    }
    
    return result.join('');
  };

  // 글자 수 계산
  const updateCharCount = () => {
    if (editorRef.current) {
      // innerText를 사용하여 실제 보이는 텍스트만 가져오기
      const textContent = editorRef.current.innerText || '';
      const textContentNoSpaces = textContent.replace(/\s+/g, '');
      
      setCharCount(textContentNoSpaces.length);
      setCharCountWithSpaces(textContent.length);
    }
  };

  // 콘텐츠 변경 처리
  const handleContentChange = () => {
    if (editorRef.current) {
      const content = editorRef.current.innerHTML;
      setEditedContent(content);
      updateCharCount();
    }
  };

  // 커서 위치의 폰트 크기 감지 - 네이버 블로그 클래스 기반
  const detectCursorFontSize = () => {
    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0) return;

    const range = selection.getRangeAt(0);
    let node = range.startContainer;
    
    if (node.nodeType === Node.TEXT_NODE) {
      node = node.parentElement;
    }
    
    let currentElement = node as HTMLElement;
    let detectedSize = '15px';
    
    while (currentElement && currentElement !== editorRef.current) {
      const classList = currentElement.classList;
      if (classList.contains('se-fs24')) {
        detectedSize = '24px';
        break;
      } else if (classList.contains('se-fs19')) {
        detectedSize = '19px';
        break;
      } else if (classList.contains('se-fs16')) {
        detectedSize = '16px';
        break;
      } else if (classList.contains('se-fs15')) {
        detectedSize = '15px';
        break;
      }
      currentElement = currentElement.parentElement as HTMLElement;
    }
    
    if (detectedSize !== currentFontSize) {
      setCurrentFontSize(detectedSize);
    }
  };

  // 클릭 이벤트 처리
  const handleClick = () => {
    setTimeout(() => {
      detectCursorFontSize();
      handleContentChange();
    }, 10);
  };

  // 간단한 엔터키 처리
  const handleKeyDown = (e: React.KeyboardEvent) => {
    // 기본 엔터키 동작 허용하되 추가 처리만
    if (e.key === 'Enter') {
      setTimeout(() => {
        handleContentChange();
      }, 0);
    }
    
    // 방향키나 클릭으로 커서 이동 시 폰트 크기 감지
    if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End'].includes(e.key)) {
      setTimeout(() => {
        detectCursorFontSize();
      }, 10);
    }
  };

  // 폰트 크기 변경 - 같은 크기여도 무조건 적용
  const handleFontSizeChange = (newSize: string) => {
    // 무조건 적용
    applyFontSizeToSelection(newSize);
    // 버튼 상태 업데이트
    setCurrentFontSize(newSize);
  };

  // 선택된 텍스트에 폰트 크기 적용 - 줄 구조 유지
  const applyFontSizeToSelection = (fontSize: string) => {
    if (!editorRef.current) return;
    
    const fontInfo = fontSizes.find(f => f.size === fontSize);
    if (!fontInfo) return;

    editorRef.current.focus();
    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0) return;

    // 선택된 텍스트가 있는 경우만 처리
    if (selection.toString().length > 0) {
      // execCommand 사용하되 즉시 정리
      document.execCommand('fontSize', false, '7'); // 임시 크기
      
      // 생성된 font 태그들을 span으로 교체
      const fontTags = editorRef.current.querySelectorAll('font[size="7"]');
      const createdSpans: HTMLElement[] = [];
      
      fontTags.forEach(fontTag => {
        const selectedText = fontTag.textContent || '';
        
        // 새로운 span 생성 (항상 새로 만들어서 중첩 문제 해결)
        const newSpan = document.createElement('span');
        newSpan.className = `se-ff-nanumgothic se-fs${fontSize.replace('px', '')}`;
        newSpan.style.color = 'rgb(0, 0, 0)';
        
        // font-weight 설정
        if (fontInfo.weight === 'bold') {
          newSpan.style.fontWeight = 'bold';
        } else {
          newSpan.style.fontWeight = 'normal';
        }
        
        newSpan.textContent = selectedText;
        createdSpans.push(newSpan);
        
        // font 태그를 새 span으로 교체
        fontTag.parentNode?.replaceChild(newSpan, fontTag);
      });
      
      // 변경된 모든 span을 다시 선택
      if (createdSpans.length > 0) {
        const newRange = document.createRange();
        newRange.setStartBefore(createdSpans[0]);
        newRange.setEndAfter(createdSpans[createdSpans.length - 1]);
        selection.removeAllRanges();
        selection.addRange(newRange);
      }
      
      handleContentChange();
    }
  };

  // 원본 복원
  const restoreOriginal = () => {
    if (data.writingResult && data.writingResult.success) {
      const content = data.writingResult.content || '';
      // 마크다운 처리해서 복원
      const processedContent = processMarkdown(content);
      setEditedContent(processedContent);
      
      if (editorRef.current) {
        editorRef.current.innerHTML = processedContent;
        updateCharCount();
      }
    }
  };

  // 클립보드 복사
  const copyToClipboard = () => {
    if (editorRef.current) {
      const content = editorRef.current.innerText || '';
      navigator.clipboard.writeText(content).then(() => {
        alert('클립보드에 복사되었습니다!');
      }).catch((err) => {
        console.error('복사 실패:', err);
        alert('복사에 실패했습니다.');
      });
    }
  };

  // 네이버 블로그 발행 (편집된 내용 그대로 전송)
  const publishToNaverBlog = async () => {
    setIsPublishing(true);
    
    try {
      // 현재 편집된 HTML 내용 가져오기
      const htmlContent = editorRef.current?.innerHTML || '';
      
      // 네이버 블로그 발행 데이터 준비
      const blogData = {
        title: data.selectedTitle,
        content: htmlContent, // 네이버 호환 HTML 그대로 전송
        tags: data.keyword ? [data.keyword] : [],
        htmlContent: htmlContent
      };
      
      console.log('네이버 블로그 발행 데이터:', blogData);
      
      // 실제 네이버 블로그 API 호출 (현재는 시뮬레이션)
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      alert('네이버 블로그에 성공적으로 발행되었습니다!\n\n편집된 폰트 크기와 스타일이 그대로 적용됩니다.');
      onComplete({ 
        generatedContent: editedContent,
        finalContent: htmlContent,
        publishedData: blogData
      });
    } catch (error) {
      console.error('발행 실패:', error);
      alert('발행에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setIsPublishing(false);
    }
  };

  const writingResult = data.writingResult as BlogWritingResult;
  const hasContent = writingResult && writingResult.success;

  if (!hasContent) {
    return (
      <div className="w-full h-full flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">❌</div>
          <h3 className="text-xl font-medium text-gray-900 mb-2">
            생성된 콘텐츠가 없습니다
          </h3>
          <p className="text-gray-600 mb-4">
            2단계에서 먼저 블로그 콘텐츠를 생성해주세요.
          </p>
          <button
            onClick={onBack}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            ← 2단계로 돌아가기
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full">
      <div className="max-w-5xl mx-auto px-6 py-4">
        <div className="ultra-card p-5 slide-in">
          {/* 헤더 */}
          <div className="text-center mb-4">
            <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2 justify-center">
              <span>✍️</span>
              <span>콘텐츠 편집 및 발행</span>
            </h1>
            <p className="text-base text-slate-600 leading-relaxed max-w-2xl mx-auto">
              AI가 생성한 콘텐츠를 편집하고 네이버 블로그에 발행하세요.
            </p>
          </div>

          {/* 작업 요약 */}
          <div className="section-card" style={{padding: '20px', marginBottom: '16px'}}>
            <div className="section-header" style={{marginBottom: '16px'}}>
              <div className="section-icon blue" style={{width: '32px', height: '32px', fontSize: '16px'}}>📋</div>
              <h2 className="section-title" style={{fontSize: '16px'}}>작업 요약</h2>
            </div>
            
            <div className="grid md:grid-cols-3 gap-4 text-sm">
              <div className="p-3 bg-blue-50 rounded-lg">
                <div className="text-blue-700 font-medium">📝 선택된 제목</div>
                <div className="text-blue-600">{data.selectedTitle}</div>
              </div>
              <div className="p-3 bg-green-50 rounded-lg">
                <div className="text-green-700 font-medium">🎯 메인 키워드</div>
                <div className="text-green-600">{data.keyword}</div>
              </div>
              <div className="p-3 bg-purple-50 rounded-lg">
                <div className="text-purple-700 font-medium">📊 글자 수</div>
                <div className="text-purple-600">
                  {charCount.toLocaleString()}자 / 공백포함: {charCountWithSpaces.toLocaleString()}자
                </div>
              </div>
            </div>
          </div>

          {/* 콘텐츠 편집기 */}
          <div className="section-card" style={{padding: '20px', marginBottom: '16px'}}>
            <div className="section-header" style={{marginBottom: '16px'}}>
              <div className="section-icon green" style={{width: '32px', height: '32px', fontSize: '16px'}}>📝</div>
              <h2 className="section-title" style={{fontSize: '16px'}}>콘텐츠 편집</h2>
            </div>
            
            {/* 편집 도구 바 */}
            <div className="flex flex-wrap gap-3 items-center justify-between mb-4">
              <div className="flex flex-wrap gap-3 items-center">
                {/* 폰트 크기 선택 */}
                <div className="flex items-center gap-2">
                  <label className="text-sm font-medium">폰트 크기:</label>
                  <select
                    value={currentFontSize}
                    onChange={(e) => handleFontSizeChange(e.target.value)}
                    className="text-xs border rounded px-2 py-1 cursor-pointer"
                  >
                    {fontSizes.map((font) => (
                      <option key={font.size} value={font.size}>
                        {font.name}
                      </option>
                    ))}
                  </select>
                  
                  {/* 강제 적용 버튼 (현재 선택된 폰트로 다시 적용) */}
                  <button
                    onClick={() => handleFontSizeChange(currentFontSize)}
                    className="text-xs px-2 py-1 bg-gray-100 border rounded hover:bg-gray-200"
                    title="현재 폰트 크기로 선택 영역 통일"
                  >
                    🔄
                  </button>
                </div>

                {/* 기능 버튼들 */}
                <button
                  onClick={restoreOriginal}
                  className="text-xs px-3 py-1 bg-yellow-500 text-white rounded hover:bg-yellow-600"
                >
                  🔄 원본 복원
                </button>
                
                <button
                  onClick={copyToClipboard}
                  className="text-xs px-3 py-1 bg-purple-500 text-white rounded hover:bg-purple-600"
                >
                  📋 복사
                </button>
              </div>
              
              {/* 글자 수 표시 */}
              <div className="text-sm text-gray-600">
                글자 수: {charCount.toLocaleString()}자 / 공백포함: {charCountWithSpaces.toLocaleString()}자
              </div>
            </div>
            
            <div
              ref={editorRef}
              contentEditable
              className="w-full min-h-96 p-4 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              style={{
                fontSize: '15px',
                lineHeight: '1.8',
                fontFamily: 'system-ui, -apple-system, sans-serif',
                backgroundColor: 'white',
                position: 'relative',
                zIndex: 1,
                minHeight: '400px',
                maxHeight: '600px',
                overflowY: 'auto'
              }}
              onInput={handleContentChange}
              onKeyDown={handleKeyDown}
              onClick={handleClick}
              suppressContentEditableWarning={true}
            />
            
            <style jsx>{`
              .se-text-paragraph {
                margin: 0;
                padding: 0;
                line-height: 1.8;
              }
              .se-text-paragraph-align-left {
                text-align: left;
              }
              .se-ff-nanumgothic {
                font-family: "Nanum Gothic", "나눔고딕", "돋움", Dotum, Arial, sans-serif;
              }
              .se-fs15 {
                font-size: 15px !important;
              }
              .se-fs16 {
                font-size: 16px !important;
              }
              .se-fs19 {
                font-size: 19px !important;
              }
              .se-fs24 {
                font-size: 24px !important;
              }
              /* 네이버 블로그 표 스타일 */
              .se-component {
                margin: 16px 0;
              }
              .se-table {
                width: 100%;
              }
              .se-table-content {
                width: 100%;
                border-collapse: collapse;
                border: 1px solid #ddd;
              }
              .se-cell {
                border: 1px solid #ddd;
                padding: 8px;
                vertical-align: top;
              }
              .se-tr {
                border: none;
              }
              .se-module-text {
                margin: 0;
                padding: 0;
              }
            `}</style>
            
            <div className="mt-3 text-xs text-gray-500">
              💡 <strong>편집 팁:</strong> 텍스트 선택 후 폰트 크기 변경 | 네이버 블로그 완전 호환 방식
            </div>
          </div>

          {/* 이미지 섹션 */}
          {(() => {
            // 다양한 형태의 이미지 태그 개수 계산
            // (이미지), [이미지], *이미지*, _이미지_ 등 모든 형태 감지
            const imageRegex = /[\(\[\*_]이미지[\)\]\*_]/g;
            const imageCount = (editedContent.match(imageRegex) || []).length;
            
            if (imageCount > 0) {
              // 더미 이미지 URL 생성
              const dummyImages = Array.from({ length: imageCount }, (_, idx) => 
                `https://via.placeholder.com/600x400/4F46E5/FFFFFF?text=Image+${idx + 1}`
              );
              
              return (
                <div className="section-card" style={{padding: '20px', marginBottom: '16px'}}>
                  <div className="section-header" style={{marginBottom: '16px'}}>
                    <div className="section-icon purple" style={{width: '32px', height: '32px', fontSize: '16px'}}>🖼️</div>
                    <h2 className="section-title" style={{fontSize: '16px'}}>생성된 이미지 ({imageCount}개)</h2>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {dummyImages.map((img, idx) => (
                      <div key={idx} className="border rounded-lg overflow-hidden">
                        <img 
                          src={img} 
                          alt={`Generated image ${idx + 1}`}
                          className="w-full h-24 object-cover"
                        />
                        <div className="p-2 text-xs text-gray-600 text-center">
                          이미지 {idx + 1}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            }
            return null;
          })()}

          {/* 발행 */}
          <div className="section-card" style={{padding: '20px', marginBottom: '16px'}}>
            <div className="section-header" style={{marginBottom: '16px'}}>
              <div className="section-icon red" style={{width: '32px', height: '32px', fontSize: '16px'}}>🚀</div>
              <h2 className="section-title" style={{fontSize: '16px'}}>네이버 블로그 발행</h2>
            </div>
            
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  <div className="text-yellow-600 text-xl">⚠️</div>
                </div>
                <div className="flex-1">
                  <h4 className="font-medium text-yellow-800 mb-1">발행 전 확인</h4>
                  <p className="text-sm text-yellow-700 mb-3">
                    편집된 콘텐츠를 검토하신 후 네이버 블로그에 자동으로 발행됩니다.
                  </p>
                  <button
                    onClick={publishToNaverBlog}
                    disabled={isPublishing}
                    className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                  >
                    {isPublishing ? '🚀 발행 중...' : '📤 네이버 블로그 작성하기'}
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* 네비게이션 */}
          <div className="flex justify-between pt-4">
            <button
              onClick={onBack}
              className="ultra-btn px-3 py-2 text-sm"
              style={{
                background: '#6b7280',
                borderColor: '#6b7280',
                color: 'white'
              }}
            >
              <span>← 이전 단계</span>
            </button>
            <button
              onClick={() => window.location.reload()}
              className="ultra-btn px-3 py-2 text-sm"
            >
              <span>🔄 새로운 글 작성하기</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Step3;