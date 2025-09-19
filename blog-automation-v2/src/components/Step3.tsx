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

  // 마크다운을 HTML로 변환 - 모든 줄을 일관된 div로 처리
  const processMarkdown = (content: string): string => {
    const lines = content.split('\n');
    const processedLines: string[] = [];
    
    for (const line of lines) {
      if (line.trim().startsWith('## ')) {
        // 대제목 (24px)
        const text = line.substring(line.indexOf('## ') + 3);
        processedLines.push(`<div style="font-size: 24px; font-weight: bold; line-height: 1.8; margin: 8px 0; min-height: 1.8em;">${text}</div>`);
      } else if (line.trim().startsWith('### ')) {
        // 소제목 (19px)
        const text = line.substring(line.indexOf('### ') + 4);
        processedLines.push(`<div style="font-size: 19px; font-weight: bold; line-height: 1.8; margin: 8px 0; min-height: 1.8em;">${text}</div>`);
      } else if (line.trim() === '') {
        // 빈 줄도 일정한 높이의 div로 처리
        processedLines.push(`<div style="font-size: 15px; line-height: 1.8; margin: 0; min-height: 1.8em;"><br></div>`);
      } else {
        // 일반 텍스트 - **강조** 처리
        let processedLine = line.replace(/\*\*([^*]+)\*\*/g, '<span style="font-size: 16px; font-weight: bold;">$1</span>');
        
        // 모든 일반 텍스트를 동일한 스타일의 div로 감싸기
        processedLines.push(`<div style="font-size: 15px; line-height: 1.8; margin: 0; min-height: 1.8em;">${processedLine}</div>`);
      }
    }
    
    return processedLines.join('');
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

  // 커서 위치의 폰트 크기 감지
  const detectCursorFontSize = () => {
    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0) return;

    const range = selection.getRangeAt(0);
    if (!range.collapsed) return; // 텍스트가 선택된 경우는 무시

    // 현재 커서 위치 저장
    const startContainer = range.startContainer;
    const startOffset = range.startOffset;
    
    let detectedFontSize = '15px'; // 기본값
    
    // 부모 요소의 스타일 확인 (커서를 건드리지 않음)
    let node = startContainer;
    
    if (node.nodeType === Node.TEXT_NODE) {
      node = node.parentElement;
    }
    
    let currentElement = node as HTMLElement;
    while (currentElement && currentElement !== editorRef.current) {
      // 인라인 스타일이 있는 경우 우선적으로 사용
      if (currentElement.style.fontSize) {
        detectedFontSize = currentElement.style.fontSize;
        console.log('인라인 스타일 감지:', detectedFontSize);
        break;
      } 
      
      // span 요소인 경우 스타일 확인
      if (currentElement.tagName === 'SPAN') {
        const computedStyle = window.getComputedStyle(currentElement);
        const fontSize = computedStyle.fontSize;
        if (fontSize && fontSize !== '15px') {
          detectedFontSize = fontSize;
          console.log('span 스타일 감지:', detectedFontSize);
          break;
        }
      }
      
      // div 요소인 경우 (마크다운 처리된 헤더)
      if (currentElement.tagName === 'DIV') {
        const computedStyle = window.getComputedStyle(currentElement);
        const fontSize = computedStyle.fontSize;
        if (fontSize && fontSize !== '15px') {
          detectedFontSize = fontSize;
          console.log('div 스타일 감지:', detectedFontSize);
          break;
        }
      }
      
      currentElement = currentElement.parentElement as HTMLElement;
    }
    
    // 감지된 폰트 크기를 드롭다운에 반영
    const matchingFont = fontSizes.find(f => f.size === detectedFontSize);
    if (matchingFont && matchingFont.size !== currentFontSize) {
      console.log('드롭다운 업데이트:', detectedFontSize, '→', matchingFont.name);
      setCurrentFontSize(matchingFont.size);
    } else if (!matchingFont && currentFontSize !== '15px') {
      // 일치하는 폰트가 없으면 기본값으로
      console.log('기본 폰트로 설정');
      setCurrentFontSize('15px');
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

  // 폰트 크기 변경
  const handleFontSizeChange = (newSize: string) => {
    setCurrentFontSize(newSize);
    applyFontSizeToSelection(newSize);
  };

  // 선택된 텍스트에 폰트 크기 적용
  const applyFontSizeToSelection = (fontSize: string) => {
    if (!editorRef.current) return;
    
    const fontInfo = fontSizes.find(f => f.size === fontSize);
    if (!fontInfo) return;

    console.log('폰트 적용:', fontInfo); // 디버깅용

    // 에디터에 포커스
    editorRef.current.focus();

    const selection = window.getSelection();
    if (!selection) return;

    // 선택된 텍스트가 있는 경우
    if (selection.rangeCount > 0 && !selection.getRangeAt(0).collapsed) {
      const range = selection.getRangeAt(0);
      
      // 기존 스타일 요소들을 제거하고 순수 텍스트만 추출
      const selectedText = range.toString();
      const fragment = range.extractContents();
      
      // 모든 span과 div에서 텍스트만 추출
      const cleanText = fragment.textContent || selectedText;
      
      // 헤더 크기는 div, 일반/강조는 span 사용
      const isHeaderSize = fontInfo.size === '24px' || fontInfo.size === '19px';
      
      if (isHeaderSize) {
        // 헤더 크기는 div로 생성 (블록 요소, 마진 포함)
        const newDiv = document.createElement('div');
        newDiv.style.fontSize = fontInfo.size;
        newDiv.style.fontWeight = fontInfo.weight;
        newDiv.style.lineHeight = '1.8';
        newDiv.style.margin = '8px 0';
        const pxSize = parseInt(fontInfo.size);
        newDiv.style.minHeight = `${pxSize * 1.8}px`;
        newDiv.textContent = cleanText;
        
        range.insertNode(newDiv);
        range.selectNode(newDiv);
        
        console.log('헤더 div 생성:', fontInfo.size);
      } else {
        // 일반/강조는 span으로 생성 (인라인 요소, 기존 줄간격 유지)
        const newSpan = document.createElement('span');
        newSpan.style.fontSize = fontInfo.size;
        newSpan.style.fontWeight = fontInfo.weight;
        newSpan.style.lineHeight = '1.8';
        newSpan.textContent = cleanText;
        
        range.insertNode(newSpan);
        range.selectNode(newSpan);
        
        console.log('텍스트 span 생성:', fontInfo.size);
      }
      
      selection.removeAllRanges();
      selection.addRange(range);
      
      console.log('선택 텍스트 폰트 적용됨:', fontInfo.size, '텍스트:', cleanText);
      
      handleContentChange();
      return;
    }

    // 커서만 있는 경우 - 다음에 타이핑할 텍스트에 스타일 적용
    const isHeaderSize = fontInfo.size === '24px' || fontInfo.size === '19px';
    const range = selection.getRangeAt(0) || document.createRange();
    
    if (isHeaderSize) {
      // 헤더는 div로 생성
      const div = document.createElement('div');
      div.style.fontSize = fontInfo.size;
      div.style.fontWeight = fontInfo.weight;
      div.style.lineHeight = '1.8';
      div.style.margin = '8px 0';
      const pxSize = parseInt(fontInfo.size);
      div.style.minHeight = `${pxSize * 1.8}px`;
      div.textContent = '\u200B';
      
      range.insertNode(div);
      range.setStart(div, 0);
      range.collapse(true);
      
      console.log('커서 위치에 헤더 div 설정:', fontInfo.size);
    } else {
      // 일반/강조는 span으로 생성
      const span = document.createElement('span');
      span.style.fontSize = fontInfo.size;
      span.style.fontWeight = fontInfo.weight;
      span.style.lineHeight = '1.8';
      span.textContent = '\u200B';
      
      range.insertNode(span);
      range.setStartAfter(span);
      range.collapse(true);
      
      console.log('커서 위치에 텍스트 span 설정:', fontInfo.size);
    }
    
    selection.removeAllRanges();
    selection.addRange(range);
    
    // 포커스 유지
    setTimeout(() => {
      if (editorRef.current) {
        editorRef.current.focus();
      }
    }, 0);
    
    handleContentChange();
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

  // 발행
  const publishToNaverBlog = async () => {
    setIsPublishing(true);
    
    try {
      // 발행 시뮬레이션 (3초)
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      alert('네이버 블로그에 성공적으로 발행되었습니다!');
      onComplete({ 
        generatedContent: editedContent,
        finalContent: editedContent
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
                    className="text-xs border rounded px-2 py-1"
                  >
                    {fontSizes.map((font) => (
                      <option key={font.size} value={font.size}>
                        {font.name}
                      </option>
                    ))}
                  </select>
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
            
            <div className="mt-3 text-xs text-gray-500">
              💡 <strong>편집 팁:</strong> 텍스트 선택 후 폰트 크기 변경 | 콘텐츠는 이미 최적화된 상태입니다
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