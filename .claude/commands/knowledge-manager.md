---
description: 지식 관리 에이전트 - 웹, 파일, 소셜 미디어에서 콘텐츠를 추출하고 정리합니다
allowed-tools: Read, Write, Bash, Glob, Grep, mcp__playwright__*, mcp__obsidian__*, mcp__notion__*, mcp__hyperbrowser__*, AskUserQuestion
---

# Knowledge Manager Command

이 명령어는 knowledge-manager 에이전트를 실행합니다.

## 실행

다음 에이전트를 로드하여 실행:
→ `.claude/agents/knowledge-manager.md`

## 사용법

```
/knowledge-manager [입력]

입력 유형:
- URL: https://example.com/article
- 파일: /path/to/document.pdf
- Threads: https://threads.net/@user/post/123
- 키워드: "종합해줘", "연결 감사" 등
```

## 주요 기능

1. **웹 콘텐츠 추출**: URL에서 콘텐츠를 추출하여 노트로 정리
2. **파일 처리**: PDF, DOCX 등 파일을 분석하여 노트로 변환
3. **소셜 미디어**: Threads, Instagram 포스트를 정리
4. **Vault 종합**: 기존 노트들을 분석하여 인사이트 도출

## 워크플로우

```
1. 설정 로드 (km-config.json)
2. 입력 소스 감지
3. 사용자 선호도 수집
4. 콘텐츠 추출
5. 분석 및 구조화
6. 내보내기 (Obsidian/Notion/Local)
7. 결과 보고
```

## 설정 필요 시

설정 파일이 없으면 셋업 위저드를 안내합니다:

```
/knowledge-manager setup
```
