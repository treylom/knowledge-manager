---
description: PDF를 Markdown으로 변환 (대용량 PDF, 한글 경로 지원)
allowedTools: Bash, Read, Write
---

# /pdf 스킬

## 사용 시점

1. **대용량 PDF**: "Prompt is too long" 오류 발생 시
2. **한글 경로 PDF**: UTF-8 인코딩 버그 우회
3. **텍스트 추출 실패 PDF**: marker로 재시도

## 기본 사용법

```bash
# 전체 PDF 변환
marker_single "파일.pdf" --output_format markdown --output_dir ./km-temp

# 결과 읽기
Read("./km-temp/파일/파일.md")
```

## 대용량 PDF 처리 (사용자가 직접 지정)

"Prompt is too long" 오류 발생 시, 사용자에게 페이지 범위 지정을 안내:

```
⚠️ PDF가 너무 커서 한 번에 처리할 수 없습니다.

페이지 범위를 지정해주세요:
/pdf "파일.pdf" --page_range "시작-끝"

예시:
- 처음 20페이지: /pdf "파일.pdf" --page_range "0-19"
- 21-40페이지: /pdf "파일.pdf" --page_range "20-39"
```

**⚠️ 자동으로 페이지 범위를 지정하지 마세요! 사용자가 직접 결정합니다.**

## 처리할 PDF

$ARGUMENTS
