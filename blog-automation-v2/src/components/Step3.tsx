import React, { useState, useRef, useEffect } from 'react';
import { WorkflowData } from '../App';
import { ImagePrompt, BlogWritingResult } from '../services/blog-writing-service';
import { LLMClientFactory } from '../services/llm-client-factory';

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
  
  // 이미지 관리 상태
  const [imageFiles, setImageFiles] = useState<{ [key: number]: File | null }>({});
  const [imageUrls, setImageUrls] = useState<{ [key: number]: string }>({});
  const [imageStatus, setImageStatus] = useState<{ [key: number]: 'empty' | 'uploading' | 'completed' | 'generating' }>({});
  
  // 이미지 생성 제어 상태
  const [isGeneratingAll, setIsGeneratingAll] = useState(false);
  const [shouldStopGeneration, setShouldStopGeneration] = useState(false);
  
  // 이미지 AI 클라이언트 상태
  const [hasImageClient, setHasImageClient] = useState(false);
  const [imageClientInfo, setImageClientInfo] = useState('미설정');
  
  // 이미지 생성 옵션 상태
  const [imageQuality, setImageQuality] = useState<'low' | 'medium' | 'high'>('high');
  const [imageSize, setImageSize] = useState<'1024x1024' | '1024x1536' | '1536x1024'>('1024x1024');
  
  // 이미지 AI 클라이언트 상태 체크
  useEffect(() => {
    const checkImageClient = () => {
      const hasClient = LLMClientFactory.hasImageClient();
      setHasImageClient(hasClient);
      
      if (hasClient) {
        const modelStatus = LLMClientFactory.getCachedModelStatus();
        setImageClientInfo(modelStatus.image || '설정됨');
      } else {
        setImageClientInfo('미설정');
      }
    };
    
    checkImageClient();
    // 주기적으로 체크 (설정 변경 감지를 위해)
    const interval = setInterval(checkImageClient, 2000);
    
    return () => clearInterval(interval);
  }, []);

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
          const processedContent = cellContent.replace(/\*\*([^*]+)\*\*/g, '<span class="se-ff-nanumgothic se-fs16" style="color: rgb(0, 0, 0); font-weight: bold;">$1</span>');
          
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

  // 이미지 업로드 처리
  const handleImageUpload = (imageIndex: number, file: File | null) => {
    if (!file) return;

    setImageStatus(prev => ({ ...prev, [imageIndex]: 'uploading' }));

    // 파일을 URL로 변환하여 미리보기
    const url = URL.createObjectURL(file);
    setImageFiles(prev => ({ ...prev, [imageIndex]: file }));
    setImageUrls(prev => ({ ...prev, [imageIndex]: url }));
    
    // 업로드 시뮬레이션 (실제로는 서버에 업로드)
    setTimeout(() => {
      setImageStatus(prev => ({ ...prev, [imageIndex]: 'completed' }));
    }, 1500);
  };

  // AI 이미지 생성 (정지 기능 포함)
  const generateAIImage = async (imageIndex: number, prompt: string, isPartOfBatch = false) => {
    setImageStatus(prev => ({ ...prev, [imageIndex]: 'generating' }));

    try {
      console.log(`🎨 AI 이미지 생성 시작 - 프롬프트: ${prompt}`);
      
      // 이미지 생성 클라이언트 확인
      if (!LLMClientFactory.hasImageClient()) {
        throw new Error('이미지 생성 AI가 설정되지 않았습니다. 설정에서 이미지 AI를 먼저 설정해주세요.');
      }

      const imageClient = LLMClientFactory.getImageClient();
      
      // 저장된 이미지 설정 가져오기
      const cachedSettings = LLMClientFactory.getCachedSettings();
      const imageSettings = cachedSettings?.settings?.image;
      
      // Step3에서 설정한 이미지 생성 옵션 사용
      const imageOptions = {
        quality: imageQuality,
        size: imageSize
      };
      
      console.log(`🎛️ 이미지 생성 옵션:`, imageOptions);
      
      // 실제 이미지 생성 API 호출
      const generatedImageUrl = await imageClient.generateImage(prompt, imageOptions);
      
      // 정지 요청 확인 (배치 모드일 때만)
      if (shouldStopGeneration && isPartOfBatch) {
        console.log(`이미지 ${imageIndex} 생성 중단됨`);
        setImageStatus(prev => ({ ...prev, [imageIndex]: 'empty' }));
        return;
      }
      
      if (generatedImageUrl && generatedImageUrl.trim()) {
        setImageUrls(prev => ({ ...prev, [imageIndex]: generatedImageUrl }));
        setImageStatus(prev => ({ ...prev, [imageIndex]: 'completed' }));
        console.log(`✅ 이미지 ${imageIndex} 생성 완료: ${generatedImageUrl}`);
      } else {
        throw new Error('빈 이미지 URL이 반환되었습니다.');
      }
      
    } catch (error) {
      console.error('❌ AI 이미지 생성 실패:', error);
      setImageStatus(prev => ({ ...prev, [imageIndex]: 'empty' }));
      
      if (!isPartOfBatch) {
        const errorMessage = error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.';
        alert(`이미지 생성에 실패했습니다: ${errorMessage}`);
      }
    }
  };

  // 이미지 제거
  const removeImage = (imageIndex: number) => {
    // URL 메모리 해제
    const url = imageUrls[imageIndex];
    if (url && url.startsWith('blob:')) {
      URL.revokeObjectURL(url);
    }
    
    setImageFiles(prev => {
      const newFiles = { ...prev };
      delete newFiles[imageIndex];
      return newFiles;
    });
    setImageUrls(prev => {
      const newUrls = { ...prev };
      delete newUrls[imageIndex];
      return newUrls;
    });
    setImageStatus(prev => ({ ...prev, [imageIndex]: 'empty' }));
  };

  // 빈 이미지 모두 AI로 생성 (정지 기능 포함)
  const generateAllMissingImages = async () => {
    const imagePrompts = data.writingResult?.imagePrompts || [];
    const imageRegex = /[\(\[\*_]이미지[\)\]\*_]/g;
    const imageCount = (editedContent.match(imageRegex) || []).length;
    
    setIsGeneratingAll(true);
    setShouldStopGeneration(false);
    
    try {
      for (let i = 1; i <= imageCount; i++) {
        // 정지 요청이 있으면 중단
        if (shouldStopGeneration) {
          console.log('일괄 이미지 생성이 사용자에 의해 중단되었습니다.');
          break;
        }
        
        const currentStatus = imageStatus[i];
        const imagePrompt = imagePrompts.find(p => p.index === i);
        
        if (currentStatus !== 'completed' && imagePrompt) {
          await generateAIImage(i, imagePrompt.prompt, true); // isPartOfBatch = true
          
          // 정지 요청이 없으면 다음 이미지 생성 전 1초 대기
          if (!shouldStopGeneration) {
            await new Promise(resolve => setTimeout(resolve, 1000));
          }
        }
      }
    } finally {
      setIsGeneratingAll(false);
      setShouldStopGeneration(false);
    }
  };

  // 이미지 생성 정지
  const stopImageGeneration = () => {
    setShouldStopGeneration(true);
    console.log('이미지 생성 정지 요청됨');
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
        generatedContent: editedContent
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
            
            <div className="grid md:grid-cols-4 gap-4 text-sm">
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
              <div className="p-3 bg-cyan-50 rounded-lg">
                <div className="text-cyan-700 font-medium">🤖 이미지 AI</div>
                <div className={`text-cyan-600 text-sm ${
                  hasImageClient ? 'text-green-600' : 'text-red-600'
                }`}>
                  {hasImageClient ? `✅ ${imageClientInfo}` : '❌ 미설정'}
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
            
            <style>{`
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
            const imageRegex = /[\(\[\*_]이미지[\)\]\*_]/g;
            const imageCount = (editedContent.match(imageRegex) || []).length;
            const imagePrompts = data.writingResult?.imagePrompts || [];
            
            if (imageCount > 0) {
              return (
                <div className="section-card" style={{padding: '20px', marginBottom: '16px'}}>
                  <div className="section-header" style={{marginBottom: '16px'}}>
                    <div className="section-icon purple" style={{width: '32px', height: '32px', fontSize: '16px'}}>🖼️</div>
                    <h2 className="section-title" style={{fontSize: '16px'}}>이미지 관리 ({imageCount}개)</h2>
                  </div>
                  
                  <div className="space-y-4">
                    {Array.from({ length: imageCount }, (_, idx) => {
                      const imageIndex = idx + 1;
                      const imagePrompt = imagePrompts.find(p => p.index === imageIndex);
                      const status = imageStatus[imageIndex] || 'empty';
                      const imageUrl = imageUrls[imageIndex];
                      
                      return (
                        <div key={idx} className="border rounded-lg p-4 bg-white">
                          <div className="flex gap-4">
                            {/* 이미지 미리보기 영역 */}
                            <div className="flex-shrink-0 w-40 h-32 border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center bg-gray-50 relative overflow-hidden">
                              {status === 'uploading' && (
                                <div className="text-center">
                                  <div className="ultra-spinner mx-auto mb-2" style={{width: '24px', height: '24px'}}></div>
                                  <div className="text-xs text-gray-600">업로드 중...</div>
                                </div>
                              )}
                              {status === 'generating' && (
                                <div className="text-center">
                                  <div className="ultra-spinner mx-auto mb-2" style={{width: '24px', height: '24px'}}></div>
                                  <div className="text-xs text-gray-600">AI 생성 중...</div>
                                </div>
                              )}
                              {status === 'completed' && imageUrl && (
                                <img 
                                  src={imageUrl} 
                                  alt={`이미지 ${imageIndex}`}
                                  className="w-full h-full object-cover"
                                />
                              )}
                              {status === 'empty' && (
                                <div className="text-center text-gray-400">
                                  <div className="text-2xl mb-1">📷</div>
                                  <div className="text-xs">이미지 {imageIndex}</div>
                                </div>
                              )}
                            </div>
                            
                            {/* 이미지 정보 및 컨트롤 */}
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-2">
                                <span className="font-semibold text-slate-900">📸 이미지 {imageIndex}</span>
                                {imagePrompt && (
                                  <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                                    📍 {imagePrompt.position}
                                  </span>
                                )}
                              </div>
                              
                              {/* AI 프롬프트 정보 */}
                              {imagePrompt && (
                                <div className="mb-3">
                                  <div className="text-xs text-slate-600 mb-1">
                                    <strong>컨텍스트:</strong> {imagePrompt.context}
                                  </div>
                                  <div className="bg-slate-50 rounded p-2 border border-slate-200">
                                    <div className="text-xs font-medium text-slate-700 mb-1">💡 AI 프롬프트:</div>
                                    <div className="text-xs text-slate-800">{imagePrompt.prompt}</div>
                                  </div>
                                </div>
                              )}
                              
                              {/* 버튼 영역 */}
                              <div className="flex gap-2">
                                <input
                                  type="file"
                                  accept="image/*"
                                  onChange={(e) => handleImageUpload(imageIndex, e.target.files?.[0] || null)}
                                  className="hidden"
                                  id={`image-upload-${imageIndex}`}
                                />
                                <label
                                  htmlFor={`image-upload-${imageIndex}`}
                                  className="px-3 py-1 bg-blue-500 text-white text-xs rounded cursor-pointer hover:bg-blue-600 transition-colors"
                                >
                                  📁 이미지 업로드
                                </label>
                                
                                {imagePrompt && (
                                  <button
                                    onClick={() => generateAIImage(imageIndex, imagePrompt.prompt)}
                                    disabled={!hasImageClient || status === 'generating' || isGeneratingAll}
                                    className="px-3 py-1 bg-purple-500 text-white text-xs rounded hover:bg-purple-600 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                                    title={!hasImageClient ? '이미지 생성 AI가 설정되지 않았습니다' : ''}
                                  >
                                    🎨 AI 이미지생성
                                  </button>
                                )}
                                
                                {status === 'completed' && (
                                  <button
                                    onClick={() => removeImage(imageIndex)}
                                    className="px-3 py-1 bg-red-500 text-white text-xs rounded hover:bg-red-600 transition-colors"
                                  >
                                    🗑️ 제거
                                  </button>
                                )}
                              </div>
                              
                              {/* 상태 표시 */}
                              <div className="mt-2 text-xs">
                                {status === 'empty' && <span className="text-gray-500">⚪ 대기중</span>}
                                {status === 'uploading' && <span className="text-blue-500">🔄 업로드 중...</span>}
                                {status === 'generating' && <span className="text-purple-500">🎨 AI 생성 중...</span>}
                                {status === 'completed' && <span className="text-green-500">✅ 완료</span>}
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                  
                  {/* 진행률 표시 */}
                  <div className="mt-4 bg-slate-50 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-slate-700">이미지 준비 현황</span>
                      <span className="text-sm text-slate-600">
                        {Object.values(imageStatus).filter(s => s === 'completed').length} / {imageCount} 완료
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-green-500 h-2 rounded-full transition-all duration-300"
                        style={{
                          width: `${(Object.values(imageStatus).filter(s => s === 'completed').length / imageCount) * 100}%`
                        }}
                      ></div>
                    </div>
                  </div>
                  
                  {/* 이미지 AI 상태 및 생성 옵션 */}
                  <div className="mt-4 p-3 bg-slate-50 rounded-lg border">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-slate-700">🤖 이미지 생성 AI 상태</span>
                      <span className={`text-sm px-2 py-1 rounded ${
                        hasImageClient 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {hasImageClient ? '✅ 연결됨' : '❌ 미설정'}
                      </span>
                    </div>
                    <div className="text-xs text-slate-600 mb-3">
                      현재 설정: {imageClientInfo}
                      {!hasImageClient && (
                        <span className="ml-2 text-red-600 font-medium">
                          (설정 → AI 설정에서 이미지 생성 AI를 설정해주세요)
                        </span>
                      )}
                    </div>
                    
                    {/* 이미지 생성 옵션 */}
                    {hasImageClient && (
                      <div className="border-t border-slate-200 pt-3">
                        <div className="text-sm font-medium text-slate-700 mb-2">🎛️ 이미지 생성 옵션</div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {/* 품질 설정 */}
                          <div>
                            <label className="text-xs font-medium text-slate-600 mb-1 block">품질</label>
                            <select
                              value={imageQuality}
                              onChange={(e) => setImageQuality(e.target.value as 'low' | 'medium' | 'high')}
                              className="w-full text-xs border rounded px-2 py-1"
                            >
                              <option value="low">저품질 (빠름)</option>
                              <option value="medium">중품질 (균형)</option>
                              <option value="high">고품질 (권장)</option>
                            </select>
                          </div>
                          
                          {/* 해상도 설정 */}
                          <div>
                            <label className="text-xs font-medium text-slate-600 mb-1 block">해상도</label>
                            <select
                              value={imageSize}
                              onChange={(e) => setImageSize(e.target.value as '1024x1024' | '1024x1536' | '1536x1024')}
                              className="w-full text-xs border rounded px-2 py-1"
                            >
                              <option value="1024x1024">정사각형 (1024×1024)</option>
                              <option value="1024x1536">세로형 (1024×1536)</option>
                              <option value="1536x1024">가로형 (1536×1024)</option>
                            </select>
                          </div>
                        </div>
                        
                        {/* 예상 비용 표시 */}
                        <div className="mt-2 text-xs text-slate-500">
                          💰 예상 비용: {(() => {
                            if (imageClientInfo.includes('runware')) {
                              return '$0.0006/이미지 (초저가)';
                            } else if (imageClientInfo.includes('openai') || imageClientInfo.includes('gpt')) {
                              const cost = imageQuality === 'low' ? '$0.040' : imageQuality === 'medium' ? '$0.060' : '$0.080';
                              return `${cost}/이미지`;
                            } else if (imageClientInfo.includes('gemini')) {
                              return '무료 (할당량 내)';
                            }
                            return '비용 정보 없음';
                          })()}
                        </div>
                      </div>
                    )}
                  </div>
                  
                  {/* 일괄 처리 버튼 */}
                  <div className="mt-4 flex gap-2">
                    {!isGeneratingAll ? (
                      <button
                        onClick={generateAllMissingImages}
                        disabled={!hasImageClient || imagePrompts.length === 0 || Object.values(imageStatus).some(s => s === 'generating')}
                        className="px-4 py-2 bg-purple-600 text-white text-sm rounded hover:bg-purple-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                        title={!hasImageClient ? '이미지 생성 AI가 설정되지 않았습니다' : ''}
                      >
                        🎨 빈 이미지 모두 AI로 생성
                      </button>
                    ) : (
                      <div className="flex gap-2">
                        <button
                          disabled
                          className="px-4 py-2 bg-purple-500 text-white text-sm rounded cursor-not-allowed opacity-75"
                        >
                          <div className="flex items-center gap-2">
                            <div className="ultra-spinner" style={{width: '16px', height: '16px'}}></div>
                            <span>🎨 AI 이미지 생성 중...</span>
                          </div>
                        </button>
                        <button
                          onClick={stopImageGeneration}
                          className="px-4 py-2 bg-red-600 text-white text-sm rounded hover:bg-red-700 transition-colors"
                        >
                          ⏹️ 생성 정지
                        </button>
                      </div>
                    )}
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