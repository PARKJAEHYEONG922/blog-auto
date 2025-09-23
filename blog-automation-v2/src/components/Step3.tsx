import React, { useState, useRef, useEffect } from 'react';
import { WorkflowData } from '../App';
import { ImagePrompt, BlogWritingResult } from '../services/blog-writing-service';
import { LLMClientFactory } from '../services/llm-client-factory';
import SimpleDialog from './SimpleDialog';
import PublishFactory from './publish/PublishFactory';

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
  
  // 이미지 관리 상태 - sessionStorage에서 복원
  const [imageFiles, setImageFiles] = useState<{ [key: number]: File | null }>({});
  const [imageUrls, setImageUrls] = useState<{ [key: number]: string }>(() => {
    try {
      const saved = sessionStorage.getItem('step3-image-urls');
      return saved ? JSON.parse(saved) : {};
    } catch {
      return {};
    }
  });
  const [imageStatus, setImageStatus] = useState<{ [key: number]: 'empty' | 'uploading' | 'completed' | 'generating' }>(() => {
    try {
      const saved = sessionStorage.getItem('step3-image-status');
      return saved ? JSON.parse(saved) : {};
    } catch {
      return {};
    }
  });
  
  // 이미지 히스토리 관리 (이전 버전 보관)
  const [imageHistory, setImageHistory] = useState<{ [key: number]: string[] }>(() => {
    try {
      const saved = sessionStorage.getItem('step3-image-history');
      return saved ? JSON.parse(saved) : {};
    } catch {
      return {};
    }
  });
  
  // 이미지 미리보기 모달
  const [previewModal, setPreviewModal] = useState<{ isOpen: boolean; imageUrl: string; imageIndex: number }>({
    isOpen: false,
    imageUrl: '',
    imageIndex: 0
  });
  
  // 이미지 선택 모달 (재생성 시)
  const [selectionModal, setSelectionModal] = useState<{ 
    isOpen: boolean; 
    imageIndex: number; 
    currentUrl: string; 
    newUrl: string; 
  }>({
    isOpen: false,
    imageIndex: 0,
    currentUrl: '',
    newUrl: ''
  });
  
  // 다이얼로그 상태 관리
  const [dialog, setDialog] = useState<{
    isOpen: boolean;
    type: 'info' | 'warning' | 'error' | 'success';
    title: string;
    message: string;
  }>({
    isOpen: false,
    type: 'info',
    title: '',
    message: ''
  });
  
  // 이미지 생성 제어 상태
  const [isGeneratingAll, setIsGeneratingAll] = useState(false);
  const stopGenerationRef = useRef(false); // 즉시 반영되는 정지 플래그
  
  // 이미지 AI 클라이언트 상태
  const [hasImageClient, setHasImageClient] = useState(false);
  const [imageClientInfo, setImageClientInfo] = useState('미설정');
  
  // 이미지 프롬프트 편집 상태 - 단순화
  const [editingPrompts, setEditingPrompts] = useState<{ [key: number]: string }>({});
  
  // 이미지 생성 옵션 상태 - API 설정에서 가져오기
  const [imageQuality, setImageQuality] = useState<'low' | 'medium' | 'high'>('high');
  const [imageSize, setImageSize] = useState<'512x768' | '768x512' | '1024x1024' | '1024x1536' | '1536x1024'>('1024x1024');
  const [imageStyle, setImageStyle] = useState<'realistic' | 'anime' | 'dreamy' | 'illustration' | 'photographic'>('realistic');
  const [currentImageProvider, setCurrentImageProvider] = useState<string>('');
  
  
  // 공급자 변경 시 해상도 호환성 체크
  useEffect(() => {
    if (currentImageProvider === 'openai') {
      // OpenAI는 제한된 해상도만 지원
      const openaiSizes = ['1024x1024', '1024x1536', '1536x1024'];
      if (!openaiSizes.includes(imageSize)) {
        console.log(`OpenAI는 ${imageSize}를 지원하지 않아 1024x1024로 변경합니다.`);
        setImageSize('1024x1024');
        LLMClientFactory.updateImageSetting('size', '1024x1024');
      }
    }
    // Runware는 모든 해상도 지원하므로 별도 처리 불필요
  }, [currentImageProvider, imageSize]);
  
  // 이미지 저장 함수
  const downloadImage = async (imageUrl: string, imageIndex: number) => {
    try {
      console.log('💾 이미지 다운로드 시작:', imageUrl);
      
      // 이미지를 Blob으로 변환
      const response = await fetch(imageUrl);
      const blob = await response.blob();
      
      // 파일명 생성 (현재 시간 + 이미지 인덱스)
      const now = new Date();
      const timestamp = now.toISOString().replace(/[:.]/g, '-').slice(0, -5);
      const filename = `blog-image-${imageIndex}-${timestamp}.png`;
      
      // Electron API가 있는 경우 (데스크톱 앱)
      if ((window as any).electronAPI && typeof (window as any).electronAPI.saveFile === 'function') {
        // Blob을 ArrayBuffer로 변환
        const arrayBuffer = await blob.arrayBuffer();
        const uint8Array = new Uint8Array(arrayBuffer);
        
        // Electron의 save dialog를 통해 저장
        const result = await (window as any).electronAPI.saveFile({
          defaultPath: filename,
          filters: [
            { name: 'PNG 이미지', extensions: ['png'] },
            { name: '모든 파일', extensions: ['*'] }
          ],
          data: Array.from(uint8Array)
        });
        
        if (result.success) {
          console.log('✅ 이미지 저장 성공:', result.filePath);
          // 성공 메시지 표시
          setDialog({
            isOpen: true,
            type: 'success',
            title: '💾 저장 완료',
            message: `이미지가 저장되었습니다:\n${result.filePath}`
          });
        } else {
          throw new Error(result.error || '저장이 취소되었습니다.');
        }
      } else {
        // 웹 브라우저의 경우 기본 다운로드
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        console.log('✅ 웹 다운로드 시작:', filename);
      }
    } catch (error) {
      console.error('❌ 이미지 저장 실패:', error);
      setDialog({
        isOpen: true,
        type: 'error',
        title: '💾 저장 실패',
        message: `이미지 저장에 실패했습니다:\n${(error as Error).message}`
      });
    }
  };

  // 이미지 AI 클라이언트 상태 체크 및 옵션 동기화
  useEffect(() => {
    const checkImageClient = () => {
      const hasClient = LLMClientFactory.hasImageClient();
      setHasImageClient(hasClient);
      
      if (hasClient) {
        const modelStatus = LLMClientFactory.getCachedModelStatus();
        setImageClientInfo(modelStatus.image || '설정됨');
        
        // API 설정에서 이미지 옵션 가져오기
        const cachedSettings = LLMClientFactory.getCachedSettings();
        const imageSettings = cachedSettings?.settings?.image;
        
        if (imageSettings) {
          // 현재 이미지 AI 공급자 저장
          setCurrentImageProvider(imageSettings.provider || '');
          
          // API 설정의 옵션을 Step3에 반영
          if (imageSettings.quality) {
            setImageQuality(imageSettings.quality as 'low' | 'medium' | 'high');
          }
          if (imageSettings.size) {
            // 공급자별 지원 해상도 체크
            if (imageSettings.provider === 'openai') {
              // OpenAI는 제한된 해상도만 지원
              const openaiSizes = ['1024x1024', '1024x1536', '1536x1024'];
              if (openaiSizes.includes(imageSettings.size)) {
                setImageSize(imageSettings.size as any);
              } else {
                setImageSize('1024x1024');
              }
            } else if (imageSettings.provider === 'runware') {
              // Runware 해상도 - API 설정과 동일
              const runwareSizes = ['512x768', '768x512', '1024x1024', '1024x1536', '1536x1024'];
              if (runwareSizes.includes(imageSettings.size)) {
                setImageSize(imageSettings.size as any);
              } else {
                setImageSize('1024x1024');
              }
            } else {
              // 기타는 기본값 (1024x1024는 모든 공급자가 지원)
              setImageSize('1024x1024');
            }
          }
          if (imageSettings.style) {
            setImageStyle(imageSettings.style as 'realistic' | 'anime' | 'dreamy' | 'illustration' | 'photographic');
          }
        }
      } else {
        setImageClientInfo('미설정');
      }
    };
    
    checkImageClient();
    // 주기적으로 체크 (설정 변경 감지를 위해)
    const interval = setInterval(checkImageClient, 2000);
    
    return () => clearInterval(interval);
  }, []);

  // 컴포넌트 마운트 시 조건부 이미지 갤러리 초기화
  useEffect(() => {
    // 새로운 글쓰기 세션인지 확인 (writingResult가 변경되었는지)
    const currentWritingId = data.writingResult ? JSON.stringify(data.writingResult.imagePrompts) : 'none';
    const lastWritingId = sessionStorage.getItem('step3-last-writing-id');
    
    // 새로운 글쓰기 결과이거나 처음 진입하는 경우에만 초기화
    if (currentWritingId !== lastWritingId) {
      console.log('🔄 새로운 글쓰기 세션 감지 - 이미지 갤러리 초기화');
      sessionStorage.removeItem('step3-image-urls');
      sessionStorage.removeItem('step3-image-status');
      sessionStorage.removeItem('step3-image-history');
      
      // 현재 세션 ID 저장
      sessionStorage.setItem('step3-last-writing-id', currentWritingId);
      
      // 상태도 초기화
      setImageFiles({});
      setImageUrls({});
      setImageStatus({});
      setImageHistory({});
      setEditingPrompts({});
    } else {
      console.log('🔄 동일한 글쓰기 세션 - 이미지 갤러리 유지');
    }
  }, []); // 빈 배열로 컴포넌트 마운트 시에만 실행

  // 이미지 상태 sessionStorage 저장
  useEffect(() => {
    sessionStorage.setItem('step3-image-urls', JSON.stringify(imageUrls));
  }, [imageUrls]);

  useEffect(() => {
    sessionStorage.setItem('step3-image-status', JSON.stringify(imageStatus));
  }, [imageStatus]);

  useEffect(() => {
    sessionStorage.setItem('step3-image-history', JSON.stringify(imageHistory));
  }, [imageHistory]);

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



  // (이미지) 플레이스홀더를 번호가 매겨진 형태로 변경
  const addImageNumbers = (content: string): string => {
    // 먼저 [이미지]를 (이미지)로 통일 (혼재 상황 방지)
    content = content.replace(/\[이미지\]/g, '(이미지)');
    
    let imageIndex = 1;
    
    // 모든 (이미지)를 순서대로 번호가 매겨진 형태로 변경
    content = content.replace(/\(이미지\)/g, () => {
      return `(이미지${imageIndex++})`;
    });
    
    console.log(`🔢 이미지 플레이스홀더 번호 매기기 완료: 총 ${imageIndex - 1}개`);
    return content;
  };

  // 마크다운을 네이버 블로그 호환 HTML로 변환
  const processMarkdown = (content: string): string => {
    // 먼저 콘텐츠 정리
    const cleanedContent = cleanAIGeneratedContent(content);
    
    // 이미지 플레이스홀더에 번호 매기기
    const numberedContent = addImageNumbers(cleanedContent);
    
    const lines = numberedContent.split('\n');
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

  // 클립보드에 HTML 복사 (네이버 발행용)
  const copyToClipboard = async (): Promise<boolean> => {
    if (editorRef.current) {
      try {
        // HTML 형식으로 복사하기 위해 선택 영역 생성
        const selection = window.getSelection();
        const range = document.createRange();
        range.selectNodeContents(editorRef.current);
        selection?.removeAllRanges();
        selection?.addRange(range);
        
        // 복사 실행
        const success = document.execCommand('copy');
        
        // 선택 해제
        selection?.removeAllRanges();
        
        if (success) {
          console.log('✅ HTML 형식으로 클립보드에 복사되었습니다!');
          return true;
        } else {
          throw new Error('복사 명령 실행 실패');
        }
      } catch (err) {
        console.error('복사 실패:', err);
        // 대체 방법: 텍스트만 복사
        const content = editorRef.current.innerText || '';
        await navigator.clipboard.writeText(content);
        console.log('⚠️ 텍스트 형식으로 복사되었습니다.');
        return false;
      }
    }
    return false;
  };

  // 이미지 위치 정보 수집 함수
  const collectImagePositions = () => {
    if (!editorRef.current) return [];
    
    const positions: Array<{
      index: number;
      textContent: string;
      parentClass: string;
      nextSibling: string | null;
      prevSibling: string | null;
    }> = [];
    
    // 모든 텍스트 노드를 순회하면서 (이미지) 찾기
    const walker = document.createTreeWalker(
      editorRef.current,
      NodeFilter.SHOW_TEXT,
      null,
      false
    );
    
    let node;
    let imageIndex = 1;
    
    while (node = walker.nextNode()) {
      const textContent = node.textContent || '';
      
      if (textContent.includes('(이미지)') || textContent.includes('[이미지]')) {
        const parentElement = node.parentElement;
        const parentClass = parentElement?.className || '';
        const nextSibling = node.nextSibling?.textContent?.substring(0, 20) || null;
        const prevSibling = node.previousSibling?.textContent?.substring(0, 20) || null;
        
        positions.push({
          index: imageIndex++,
          textContent: textContent.trim(),
          parentClass,
          nextSibling,
          prevSibling
        });
        
        console.log(`🔍 이미지 ${imageIndex - 1} 위치:`, {
          text: textContent.trim(),
          parent: parentClass,
          next: nextSibling,
          prev: prevSibling
        });
      }
    }
    
    return positions;
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

  // 현재 프롬프트 가져오기 (편집된 프롬프트 우선)
  const getCurrentPrompt = (imageIndex: number): string => {
    // 편집된 프롬프트가 있으면 사용
    if (editingPrompts.hasOwnProperty(imageIndex)) {
      return editingPrompts[imageIndex];
    }
    
    // 원본 프롬프트가 있으면 사용
    const imagePrompts = data.writingResult?.imagePrompts || [];
    const imagePrompt = imagePrompts.find(p => p.index === imageIndex);
    if (imagePrompt) {
      return imagePrompt.prompt;
    }
    
    // 둘 다 없으면 빈 문자열
    return '';
  };

  // 표시용 프롬프트 가져오기 (UI에서 사용)
  const getDisplayPrompt = (imageIndex: number): string => {
    return getCurrentPrompt(imageIndex);
  };

  // 프롬프트 편집 처리
  const handlePromptChange = (imageIndex: number, newPrompt: string) => {
    setEditingPrompts(prev => ({
      ...prev,
      [imageIndex]: newPrompt
    }));
  };

  // 프롬프트를 원본으로 리셋
  const resetPromptToOriginal = (imageIndex: number) => {
    setEditingPrompts(prev => {
      const newPrompts = { ...prev };
      delete newPrompts[imageIndex];
      return newPrompts;
    });
  };

  // AI 이미지 생성 (히스토리 관리 및 선택 기능 포함)
  const generateAIImage = async (imageIndex: number, originalPrompt: string, isPartOfBatch = false) => {
    setImageStatus(prev => ({ ...prev, [imageIndex]: 'generating' }));

    try {
      // 편집된 프롬프트가 있으면 사용, 없으면 원본 프롬프트 사용
      const finalPrompt = getCurrentPrompt(imageIndex) || originalPrompt;
      console.log(`🎨 AI 이미지 생성 시작 - 프롬프트: ${finalPrompt}`);
      
      // 이미지 생성 클라이언트 확인
      if (!LLMClientFactory.hasImageClient()) {
        throw new Error('이미지 생성 AI가 설정되지 않았습니다. 설정에서 이미지 AI를 먼저 설정해주세요.');
      }

      const imageClient = LLMClientFactory.getImageClient();
      
      // Step3에서 설정한 이미지 생성 옵션 사용
      const imageOptions = {
        quality: imageQuality,
        size: imageSize
      };
      
      console.log(`🎛️ 이미지 생성 옵션:`, imageOptions);
      
      // 스타일 적용된 프롬프트 생성
      const styledPrompt = applyStyleToPrompt(finalPrompt, imageStyle);
      console.log(`🎨 스타일 적용된 프롬프트: ${styledPrompt}`);
      
      // 실제 이미지 생성 API 호출
      const generatedImageUrl = await imageClient.generateImage(styledPrompt, imageOptions);
      
      // 정지 요청 확인 (배치 모드일 때만)
      if (stopGenerationRef.current && isPartOfBatch) {
        console.log(`이미지 ${imageIndex} 생성 중단됨`);
        setImageStatus(prev => ({ ...prev, [imageIndex]: 'empty' }));
        return;
      }
      
      if (generatedImageUrl && generatedImageUrl.trim()) {
        const currentUrl = imageUrls[imageIndex];
        
        // 기존 이미지가 있으면 선택 모달 표시 (배치 모드가 아닐 때만)
        if (currentUrl && !isPartOfBatch) {
          setSelectionModal({
            isOpen: true,
            imageIndex,
            currentUrl,
            newUrl: generatedImageUrl
          });
          setImageStatus(prev => ({ ...prev, [imageIndex]: 'completed' }));
        } else {
          // 새 이미지를 바로 적용
          applyNewImage(imageIndex, generatedImageUrl, currentUrl);
        }
        
        console.log(`✅ 이미지 ${imageIndex} 생성 완료: ${generatedImageUrl}`);
      } else {
        throw new Error('빈 이미지 URL이 반환되었습니다.');
      }
      
    } catch (error) {
      console.error('❌ AI 이미지 생성 실패:', error);
      setImageStatus(prev => ({ ...prev, [imageIndex]: 'empty' }));
      
      if (!isPartOfBatch) {
        const errorMessage = error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.';
        
        // 에러 유형별 사용자 친화적 메시지
        let title = '이미지 생성 실패';
        let message = '';
        let type: 'error' | 'warning' = 'error';
        
        if (errorMessage.includes('insufficientCredits') || errorMessage.includes('크레딧')) {
          title = '💳 크레딧이 부족합니다';
          message = 'Runware API 크레딧을 모두 사용했습니다.\n\n📍 해결 방법:\n• my.runware.ai/wallet에서 크레딧 충전\n• 또는 API 설정에서 다른 이미지 생성 AI로 변경';
          type = 'warning';
        } else if (errorMessage.includes('429') || errorMessage.includes('quota') || errorMessage.includes('할당량')) {
          title = '⏰ 일일 할당량 초과';
          message = '오늘의 무료 이미지 생성 할당량을 모두 사용했습니다.\n\n📍 해결 방법:\n• 내일 다시 시도하기\n• API 설정에서 다른 이미지 생성 AI로 변경\n• 유료 플랜으로 업그레이드';
          type = 'warning';
        } else if (errorMessage.includes('403') || errorMessage.includes('인증')) {
          title = '🔐 인증이 필요합니다';
          message = 'OpenAI 조직 인증이 필요합니다.\n\n📍 해결 방법:\n• platform.openai.com에서 조직 인증하기\n• 또는 다른 이미지 생성 AI 사용';
          type = 'warning';
        } else if (errorMessage.includes('invalidModel')) {
          title = '🚫 모델 오류';
          message = '선택한 이미지 생성 모델에 문제가 있습니다.\n\n📍 해결 방법:\n• API 설정에서 다른 모델 선택\n• 또는 다른 이미지 생성 AI로 변경';
          type = 'error';
        } else {
          title = '🔧 이미지 생성 오류';
          message = `이미지 생성 중 오류가 발생했습니다.\n\n오류 내용: ${errorMessage}\n\n📍 해결 방법:\n• 잠시 후 다시 시도\n• API 설정 확인\n• 다른 이미지 생성 AI로 변경`;
          type = 'error';
        }
        
        setDialog({
          isOpen: true,
          type,
          title,
          message
        });
      }
    }
  };

  // 새 이미지 적용 (히스토리 관리)
  const applyNewImage = (imageIndex: number, newUrl: string, currentUrl?: string) => {
    // 현재 이미지를 히스토리에 추가
    if (currentUrl) {
      setImageHistory(prev => ({
        ...prev,
        [imageIndex]: [...(prev[imageIndex] || []), currentUrl]
      }));
    }
    
    // 새 이미지 적용
    setImageUrls(prev => ({ ...prev, [imageIndex]: newUrl }));
    setImageStatus(prev => ({ ...prev, [imageIndex]: 'completed' }));
  };

  // 이미지 선택 (기존 유지 vs 새 이미지 사용)
  const handleImageSelection = (useNew: boolean) => {
    const { imageIndex, currentUrl, newUrl } = selectionModal;
    
    if (useNew) {
      // 새 이미지 사용: 현재 이미지를 히스토리에 추가하고 새 이미지를 현재로 설정
      applyNewImage(imageIndex, newUrl, currentUrl);
    } else {
      // 기존 이미지 유지: 새 이미지를 히스토리에 추가 (갤러리에서 선택할 수 있도록)
      if (newUrl) {
        setImageHistory(prev => ({
          ...prev,
          [imageIndex]: [...(prev[imageIndex] || []), newUrl]
        }));
        console.log(`📸 새 이미지를 갤러리에 저장: 이미지 ${imageIndex}`);
      }
    }
    
    setSelectionModal({
      isOpen: false,
      imageIndex: 0,
      currentUrl: '',
      newUrl: ''
    });
  };

  // 이미지 미리보기 모달 열기
  const openPreviewModal = (imageUrl: string, imageIndex: number) => {
    setPreviewModal({
      isOpen: true,
      imageUrl,
      imageIndex
    });
  };

  // 이미지 미리보기 모달 닫기
  const closePreviewModal = () => {
    setPreviewModal({
      isOpen: false,
      imageUrl: '',
      imageIndex: 0
    });
  };



  // AI 이미지 생성 처리 (빈 프롬프트면 원본 사용)
  const handleAIImageGeneration = (imageIndex: number) => {
    const currentPrompt = getCurrentPrompt(imageIndex);
    const imagePrompts = data.writingResult?.imagePrompts || [];
    const originalPrompt = imagePrompts.find(p => p.index === imageIndex)?.prompt || '';
    
    // 빈 프롬프트면 원본 프롬프트 사용
    const promptToUse = (!currentPrompt || currentPrompt.trim() === '') 
      ? originalPrompt 
      : currentPrompt.trim();
    
    // 원본 프롬프트도 없으면 에러
    if (!promptToUse || promptToUse.trim() === '') {
      setDialog({
        isOpen: true,
        type: 'warning',
        title: '⚠️ 프롬프트가 없습니다',
        message: '이미지 생성을 위한 프롬프트가 없습니다.'
      });
      return;
    }
    
    // AI 이미지 생성 실행
    generateAIImage(imageIndex, promptToUse);
  };

  // 갤러리에서 이미지 선택
  const selectImageFromGallery = (imageIndex: number, selectedImageUrl: string) => {
    // 현재 이미지를 히스토리에 추가 (있는 경우)
    const currentUrl = imageUrls[imageIndex];
    if (currentUrl && currentUrl !== selectedImageUrl) {
      setImageHistory(prev => ({
        ...prev,
        [imageIndex]: [...(prev[imageIndex] || []), currentUrl]
      }));
    }

    // 선택된 이미지를 현재 이미지로 설정
    setImageUrls(prev => ({ ...prev, [imageIndex]: selectedImageUrl }));
    setImageStatus(prev => ({ ...prev, [imageIndex]: 'completed' }));
    
    // 히스토리에서 선택된 이미지 제거 (중복 방지)
    setImageHistory(prev => ({
      ...prev,
      [imageIndex]: (prev[imageIndex] || []).filter(url => url !== selectedImageUrl)
    }));

    // 미리보기 모달의 이미지도 업데이트
    setPreviewModal(prev => ({
      ...prev,
      imageUrl: selectedImageUrl
    }));
  };

  // 스타일에 따른 프롬프트 조정
  const applyStyleToPrompt = (basePrompt: string, style: string): string => {
    let styledPrompt = basePrompt;
    
    switch (style) {
      case 'anime':
        styledPrompt += ', anime style, manga style, 2D illustration, cel shading';
        break;
      case 'dreamy':
        styledPrompt += ', dreamy atmosphere, soft lighting, ethereal, artistic, fantasy art, magical';
        break;
      case 'illustration':
        styledPrompt += ', digital illustration, concept art, stylized, artistic rendering';
        break;
      case 'photographic':
        styledPrompt += ', professional photography, high quality, detailed, photorealistic, studio lighting';
        break;
      case 'realistic':
      default:
        styledPrompt += ', realistic, detailed, high quality';
        break;
    }
    
    return styledPrompt;
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

  // 모든 이미지 초기화
  const clearAllImages = () => {
    // 모든 blob URL 메모리 해제
    Object.values(imageUrls).forEach(url => {
      if (url && url.startsWith('blob:')) {
        URL.revokeObjectURL(url);
      }
    });
    
    // 히스토리에 있는 URL들도 메모리 해제
    Object.values(imageHistory).forEach(urlArray => {
      urlArray.forEach(url => {
        if (url && url.startsWith('blob:')) {
          URL.revokeObjectURL(url);
        }
      });
    });
    
    setImageFiles({});
    setImageUrls({});
    setImageStatus({});
    setImageHistory({});
    
    // sessionStorage에서도 제거
    sessionStorage.removeItem('step3-image-urls');
    sessionStorage.removeItem('step3-image-status');
    sessionStorage.removeItem('step3-image-history');
  };

  // 빈 이미지 모두 AI로 생성 (정지 기능 포함)
  const generateAllMissingImages = async () => {
    const imagePrompts = data.writingResult?.imagePrompts || [];
    const imageRegex = /[\(\[\*_]이미지\d*[\)\]\*_]/g;
    const imageCount = (editedContent.match(imageRegex) || []).length;
    
    setIsGeneratingAll(true);
    stopGenerationRef.current = false;
    
    try {
      for (let i = 1; i <= imageCount; i++) {
        // 정지 요청이 있으면 중단
        if (stopGenerationRef.current) {
          console.log('일괄 이미지 생성이 사용자에 의해 중단되었습니다.');
          break;
        }
        
        const currentStatus = imageStatus[i];
        const imagePrompt = imagePrompts.find(p => p.index === i);
        
        if (currentStatus !== 'completed' && imagePrompt) {
          const currentPrompt = getCurrentPrompt(i);
          // 빈 프롬프트는 건너뛰기
          if (currentPrompt && currentPrompt.trim() !== '') {
            await generateAIImage(i, currentPrompt.trim(), true); // isPartOfBatch = true
            
            // 이미지 생성 완료 후 다시 정지 요청 확인
            if (stopGenerationRef.current) {
              console.log('일괄 이미지 생성이 사용자에 의해 중단되었습니다.');
              break;
            }
          }
          
          // 정지 요청이 없으면 다음 이미지 생성 전 1초 대기
          if (!stopGenerationRef.current) {
            await new Promise(resolve => setTimeout(resolve, 1000));
          }
        }
      }
    } finally {
      setIsGeneratingAll(false);
      stopGenerationRef.current = false;
    }
  };

  // 이미지 생성 정지
  const stopImageGeneration = () => {
    stopGenerationRef.current = true;
    console.log('이미지 생성 정지 요청됨');
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
              id="step3-editor"
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
            // 다양한 형태의 이미지 태그 개수 계산 (번호가 매겨진 형태 포함)
            const imageRegex = /[\(\[\*_]이미지\d*[\)\]\*_]/g;
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
                                <div 
                                  className="w-full h-full relative group cursor-pointer"
                                  onClick={() => openPreviewModal(imageUrl, imageIndex)}
                                >
                                  <img 
                                    src={imageUrl} 
                                    alt={`이미지 ${imageIndex}`}
                                    className="w-full h-full object-contain"
                                    style={{ imageRendering: 'auto' }}
                                  />
                                  {/* 호버 시 확대 아이콘 */}
                                  <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all duration-200 flex items-center justify-center">
                                    <div className="text-white text-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                                      🔍
                                    </div>
                                  </div>
                                </div>
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
                              <div className="mb-3">
                                {imagePrompt ? (
                                  <div className="text-xs text-slate-600 mb-1">
                                    <strong>컨텍스트:</strong> {imagePrompt.context}
                                  </div>
                                ) : (
                                  <div className="text-xs text-orange-600 mb-1">
                                    <strong>⚠️ 프롬프트 없음:</strong> AI가 생성하지 못한 이미지 위치입니다. 직접 프롬프트를 입력해주세요.
                                  </div>
                                )}
                                <div className="bg-slate-50 rounded p-2 border border-slate-200">
                                  <div className="flex items-center justify-between mb-1">
                                    <div className="text-xs font-medium text-slate-700">💡 이미지 프롬프트:</div>
                                    {editingPrompts.hasOwnProperty(imageIndex) && imagePrompt && (
                                      <button
                                        onClick={() => resetPromptToOriginal(imageIndex)}
                                        className="text-xs text-orange-600 hover:text-orange-800 transition-colors"
                                        title="원본으로 되돌리기"
                                      >
                                        🔄 원본
                                      </button>
                                    )}
                                  </div>
                                  <textarea
                                    value={getDisplayPrompt(imageIndex)}
                                    onChange={(e) => handlePromptChange(imageIndex, e.target.value)}
                                    className="w-full text-xs text-slate-800 bg-white border border-slate-300 rounded p-2 resize-none"
                                    rows={3}
                                    placeholder={imagePrompt ? 
                                      "이미지 생성을 위한 프롬프트를 영어로 입력하세요..." : 
                                      "프롬프트가 없습니다. 이미지 생성을 위한 영어 프롬프트를 직접 입력해주세요... (예: professional illustration related to blog content)"
                                    }
                                  />
                                </div>
                              </div>
                              
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
                                
                                <button
                                  onClick={() => handleAIImageGeneration(imageIndex)}
                                  disabled={!hasImageClient || status === 'generating' || isGeneratingAll || !getDisplayPrompt(imageIndex).trim()}
                                  className="px-3 py-1 bg-purple-500 text-white text-xs rounded hover:bg-purple-600 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                                  title={
                                    !hasImageClient ? '이미지 생성 AI가 설정되지 않았습니다' :
                                    !getDisplayPrompt(imageIndex).trim() ? '프롬프트를 입력해주세요' :
                                    ''
                                  }
                                >
                                  🎨 AI 이미지생성 {!imagePrompt && '(수동)'}
                                </button>
                                
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
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                          {/* 품질 설정 */}
                          <div>
                            <label className="text-xs font-medium text-slate-600 mb-1 block">품질</label>
                            <select
                              value={imageQuality}
                              onChange={(e) => {
                                const newQuality = e.target.value as 'low' | 'medium' | 'high';
                                setImageQuality(newQuality);
                                // API 설정에도 반영
                                LLMClientFactory.updateImageSetting('quality', newQuality);
                              }}
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
                              onChange={(e) => {
                                const newSize = e.target.value as '512x768' | '768x512' | '1024x1024' | '1024x1536' | '1536x1024';
                                setImageSize(newSize);
                                // API 설정에도 반영
                                LLMClientFactory.updateImageSetting('size', newSize);
                              }}
                              className="w-full text-xs border rounded px-2 py-1"
                            >
                              {/* 공급자별 해상도 옵션 - 지원하는 것만 표시 */}
                              {currentImageProvider === 'runware' ? (
                                <>
                                  <option value="1024x1024">1024x1024 (정사각형)</option>
                                  <option value="1024x1536">1024x1536 (세로형)</option>
                                  <option value="1536x1024">1536x1024 (가로형)</option>
                                  <option value="512x768">512x768 (초저가 세로형)</option>
                                  <option value="768x512">768x512 (초저가 가로형)</option>
                                </>
                              ) : currentImageProvider === 'openai' ? (
                                <>
                                  <option value="1024x1024">정사각형 (1024×1024)</option>
                                  <option value="1024x1536">세로형 (1024×1536)</option>
                                  <option value="1536x1024">가로형 (1536×1024)</option>
                                </>
                              ) : (
                                <>
                                  <option value="1024x1024">정사각형 (1024×1024)</option>
                                </>
                              )}
                            </select>
                          </div>
                          
                          {/* 스타일 설정 */}
                          <div>
                            <label className="text-xs font-medium text-slate-600 mb-1 block">스타일</label>
                            <select
                              value={imageStyle}
                              onChange={(e) => {
                                const newStyle = e.target.value as 'realistic' | 'anime' | 'dreamy' | 'illustration' | 'photographic';
                                setImageStyle(newStyle);
                                // API 설정에도 반영
                                LLMClientFactory.updateImageSetting('style', newStyle);
                              }}
                              className="w-full text-xs border rounded px-2 py-1"
                            >
                              <option value="realistic">사실적</option>
                              <option value="photographic">사진 같은</option>
                              <option value="anime">애니메이션</option>
                              <option value="illustration">일러스트</option>
                              <option value="dreamy">몽환적</option>
                            </select>
                          </div>
                        </div>
                        
                        {/* 예상 비용 및 품질 안내 */}
                        <div className="mt-2 text-xs text-slate-500">
                          💰 예상 비용: {(() => {
                            if (imageClientInfo.includes('runware')) {
                              return '$0.0006/이미지 (초저가)';
                            } else if (imageClientInfo.includes('openai') || imageClientInfo.includes('gpt')) {
                              const cost = imageQuality === 'low' ? '$0.040' : imageQuality === 'medium' ? '$0.060' : '$0.080';
                              return `${cost}/이미지`;
                            } else if (imageClientInfo.includes('gemini')) {
                              return '$0.039/이미지';
                            }
                            return '비용 정보 없음';
                          })()}
                        </div>
                        <div className="mt-1 text-xs text-blue-600">
                          💡 더 선명한 이미지를 원하면 품질을 고품질로 설정하세요
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

          {/* 발행 - PublishFactory 사용 */}
          <PublishFactory
            platform={data.platform}
            data={data}
            editedContent={editedContent}
            imageUrls={imageUrls}
            onComplete={onComplete}
            copyToClipboard={copyToClipboard}
          />

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

      {/* 이미지 미리보기 모달 */}
      {previewModal.isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50" onClick={closePreviewModal}>
          <div className="relative max-w-6xl max-h-screen p-4 flex flex-col" onClick={(e) => e.stopPropagation()}>
            <button
              onClick={closePreviewModal}
              className="absolute top-2 right-2 text-white text-2xl hover:text-gray-300 z-10 bg-black bg-opacity-50 rounded-full w-10 h-10 flex items-center justify-center"
            >
              ✕
            </button>
            
            {/* 메인 이미지 */}
            <div className="flex-1 flex items-center justify-center mb-4">
              <img
                src={previewModal.imageUrl}
                alt={`이미지 ${previewModal.imageIndex} 미리보기`}
                className="max-w-full max-h-[70vh] object-contain rounded-lg"
                style={{ imageRendering: 'auto' }}
              />
            </div>
            
            {/* 이미지 갤러리 */}
            {(() => {
              const currentImageUrl = imageUrls[previewModal.imageIndex];
              const historyImages = imageHistory[previewModal.imageIndex] || [];
              const allImages = [currentImageUrl, ...historyImages].filter(Boolean);
              
              return allImages.length > 1 && (
                <div className="bg-black bg-opacity-75 rounded-lg p-4">
                  <div className="text-white text-sm mb-3 text-center">
                    📸 이미지 갤러리 ({allImages.length}개) - 클릭해서 선택하세요
                  </div>
                  <div className="flex gap-2 overflow-x-auto justify-center">
                    {allImages.map((imageUrl, index) => (
                      <div
                        key={index}
                        className={`relative flex-shrink-0 cursor-pointer rounded-lg overflow-hidden border-2 transition-all ${
                          imageUrl === previewModal.imageUrl 
                            ? 'border-blue-400 shadow-lg transform scale-105' 
                            : 'border-gray-500 hover:border-gray-300'
                        }`}
                        onClick={() => selectImageFromGallery(previewModal.imageIndex, imageUrl)}
                      >
                        <img
                          src={imageUrl}
                          alt={`버전 ${index + 1}`}
                          className="w-24 h-24 object-cover"
                          style={{ imageRendering: 'auto' }}
                        />
                        {imageUrl === previewModal.imageUrl && (
                          <div className="absolute inset-0 bg-blue-500 bg-opacity-20 flex items-center justify-center">
                            <div className="bg-blue-500 text-white text-xs px-2 py-1 rounded">
                              현재
                            </div>
                          </div>
                        )}
                        <div className="absolute bottom-1 left-1 bg-black bg-opacity-75 text-white text-xs px-1 rounded">
                          {index + 1}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })()}
            
            {/* 하단 정보 및 저장 버튼 */}
            <div className="absolute bottom-4 left-4 bg-black bg-opacity-75 text-white px-3 py-2 rounded-lg">
              📸 이미지 {previewModal.imageIndex}
            </div>
            
            <div className="absolute bottom-4 right-4">
              <button
                onClick={() => downloadImage(previewModal.imageUrl, previewModal.imageIndex)}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
              >
                💾 저장
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 이미지 선택 모달 (재생성 시) */}
      {selectionModal.isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-4xl max-h-screen overflow-auto">
            <h3 className="text-lg font-bold text-center mb-4">
              🎨 이미지 {selectionModal.imageIndex} - 새로운 버전이 생성되었습니다!
            </h3>
            <p className="text-sm text-gray-600 text-center mb-6">
              어떤 이미지를 사용하시겠습니까?
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              {/* 현재 이미지 */}
              <div className="text-center">
                <h4 className="font-semibold mb-2 text-blue-600">🔷 현재 이미지 (기존)</h4>
                <div className="border rounded-lg overflow-hidden bg-gray-50">
                  <img
                    src={selectionModal.currentUrl}
                    alt="현재 이미지"
                    className="w-full h-64 object-contain"
                  />
                </div>
                <button
                  onClick={() => handleImageSelection(false)}
                  className="mt-3 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
                >
                  ✅ 현재 이미지 유지
                </button>
              </div>
              
              {/* 새 이미지 */}
              <div className="text-center">
                <h4 className="font-semibold mb-2 text-green-600">🔶 새 이미지 (AI 생성)</h4>
                <div className="border rounded-lg overflow-hidden bg-gray-50">
                  <img
                    src={selectionModal.newUrl}
                    alt="새 이미지"
                    className="w-full h-64 object-contain"
                  />
                </div>
                <button
                  onClick={() => handleImageSelection(true)}
                  className="mt-3 px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 transition-colors"
                >
                  🆕 새 이미지 사용
                </button>
              </div>
            </div>
            
            <div className="text-center">
              <p className="text-xs text-gray-500 mb-3">
                💡 현재 이미지를 선택해도 새 이미지는 히스토리에 보관됩니다.
              </p>
              <button
                onClick={() => handleImageSelection(false)}
                className="px-4 py-2 bg-gray-400 text-white rounded hover:bg-gray-500 transition-colors"
              >
                ⏹️ 취소 (현재 이미지 유지)
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 에러 다이얼로그 */}
      <SimpleDialog
        isOpen={dialog.isOpen}
        title={dialog.title}
        message={dialog.message}
        onClose={() => setDialog({ ...dialog, isOpen: false })}
      />
    </div>
  );
};

export default Step3;