# YouTube Transcript Extract & Analyze

YouTube 영상의 트랜스크립트(자막)를 추출하고 분석하여 Obsidian 노트로 정리합니다.

---

## 의존성

```bash
# 필수
pip install youtube-transcript-api

# 폴백 (트랜스크립트 API 실패 시)
pip install yt-dlp
```

---

## 트랜스크립트 추출

### Step 1: URL 파싱

```python
import re

def extract_video_id(url):
    """YouTube URL에서 video ID 추출"""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None
```

### Step 2: 트랜스크립트 추출 (Primary)

```python
from youtube_transcript_api import YouTubeTranscriptApi

def get_transcript(video_id, preferred_lang="ko"):
    """트랜스크립트 추출 — 한국어 우선, 영어 폴백 (v1.2.x API)"""
    ytt_api = YouTubeTranscriptApi()

    # 시도 순서: 한국어 → 영어 → 아무 자막
    lang_attempts = [preferred_lang, "en"]

    for lang in lang_attempts:
        try:
            transcript = ytt_api.fetch(video_id, languages=[lang])
            snippets = [{"text": s.text, "start": s.start, "duration": s.duration}
                        for s in transcript]
            return snippets, lang, "fetched"
        except Exception:
            continue

    # 폴백: 언어 지정 없이 시도
    try:
        transcript = ytt_api.fetch(video_id)
        snippets = [{"text": s.text, "start": s.start, "duration": s.duration}
                    for s in transcript]
        return snippets, "unknown", "fetched"
    except Exception as e:
        return None, None, str(e)
```

> **참고**: youtube-transcript-api v1.2.x는 인스턴스 메서드 `YouTubeTranscriptApi().fetch()` 사용.
> 이전 버전(v0.x)의 `YouTubeTranscriptApi.list_transcripts()` 클래스 메서드는 더 이상 작동하지 않음.

### Step 3: 트랜스크립트 폴백 (yt-dlp)

```python
import subprocess
import json

def get_transcript_ytdlp(video_id, preferred_lang="ko"):
    """yt-dlp로 자막 다운로드 (youtube-transcript-api 실패 시)"""
    url = f"https://www.youtube.com/watch?v={video_id}"

    # 자막 목록 확인
    result = subprocess.run(
        ["yt-dlp", "--list-subs", "--skip-download", url],
        capture_output=True, text=True
    )

    # 자막 다운로드
    lang = preferred_lang
    result = subprocess.run(
        ["yt-dlp", "--write-sub", "--write-auto-sub",
         "--sub-lang", f"{lang},en",
         "--sub-format", "json3",
         "--skip-download",
         "-o", f"/tmp/yt-{video_id}",
         url],
        capture_output=True, text=True
    )

    # JSON3 자막 파일 파싱
    import glob
    sub_files = glob.glob(f"/tmp/yt-{video_id}*.json3")
    if sub_files:
        with open(sub_files[0], 'r', encoding='utf-8') as f:
            data = json.load(f)
        return [
            {"text": ev.get("segs", [{}])[0].get("utf8", ""),
             "start": ev.get("tStartMs", 0) / 1000,
             "duration": (ev.get("dDurationMs", 0)) / 1000}
            for ev in data.get("events", [])
            if ev.get("segs")
        ]
    return None
```

---

## 영상 메타데이터 수집 (3-Tier 폴백)

### 1순위: yt-dlp (설치된 경우)

```python
def get_video_metadata(video_id):
    """yt-dlp로 영상 메타데이터 추출"""
    import subprocess, json

    result = subprocess.run(
        ["yt-dlp", "--dump-json", "--skip-download",
         f"https://www.youtube.com/watch?v={video_id}"],
        capture_output=True, text=True
    )

    if result.returncode == 0:
        data = json.loads(result.stdout)
        return {
            "title": data.get("title", ""),
            "channel": data.get("channel", ""),
            "upload_date": data.get("upload_date", ""),
            "duration": data.get("duration", 0),
            "description": data.get("description", "")[:500],
            "view_count": data.get("view_count", 0),
            "like_count": data.get("like_count", 0),
            "tags": data.get("tags", [])[:10]
        }
    return None
```

### 2순위: Playwright CLI (🚨 yt-dlp 실패/미설치 시 — MUST USE!)

> **CRITICAL**: WebFetch는 YouTube 접근 불가. yt-dlp 실패 시 반드시 Playwright CLI 사용!
> Playwright MCP(`mcp__playwright__*`)가 아닌 **`playwright-cli`** (Bash 기반)를 먼저 사용할 것.

```bash
# Step 1: YouTube 페이지 열기
playwright-cli open "https://www.youtube.com/watch?v={video_id}"

# Step 2: 접근성 스냅샷으로 메타데이터 추출
playwright-cli snapshot
```

스냅샷에서 추출할 정보:
- **제목**: `<h1>` 또는 페이지 타이틀에서 추출
- **채널명**: 채널 링크 텍스트
- **업로드일**: info-strings 영역
- **영상 길이**: 시크바 버튼 텍스트 (예: "0:00 / 23:11")
- **조회수**: view-count 텍스트
- **좋아요**: like 버튼 aria-label

추가로 description 확장 후 **챕터 정보** 추출:

```bash
# Step 3: 설명 영역 펼치기 (챕터 확인)
playwright-cli click "#expand"

# Step 4: 다시 스냅샷으로 챕터 목록 추출
playwright-cli snapshot

# Step 5: 브라우저 종료
playwright-cli close
```

**챕터 정보가 있으면 타임라인 테이블의 타임스탬프로 사용 (자막 추정 대신 정확한 시간).**

### 3순위: Playwright MCP (CLI 실패 시 폴백)

```tool-call
mcp__playwright__browser_navigate({ url: "https://www.youtube.com/watch?v={video_id}" })
mcp__playwright__browser_snapshot()
# 설명 펼치기
mcp__playwright__browser_click({ element: "설명 더보기 버튼", ref: "expand" })
mcp__playwright__browser_snapshot()
mcp__playwright__browser_close()
```

### 메타데이터 수집 실패 시

모든 방법 실패 시 트랜스크립트 내용만으로 진행하되 사용자에게 알림:
> "영상 메타데이터를 수집하지 못했습니다. 트랜스크립트 기반으로 분석합니다."

---

## 콘텐츠 분석 (프리셋 연동)

### 트랜스크립트 → 텍스트 정리

```python
def transcript_to_text(transcript_data):
    """타임스탬프 포함 텍스트 변환"""
    lines = []
    for entry in transcript_data:
        start = entry.get("start", 0)
        text = entry.get("text", "").strip()
        if text:
            minutes = int(start // 60)
            seconds = int(start % 60)
            lines.append(f"[{minutes:02d}:{seconds:02d}] {text}")
    return "\n".join(lines)
```

### 프리셋별 분석 깊이

| 프리셋 키워드 | 분석 깊이 | 출력 분량 |
|--------------|----------|----------|
| "요약", "요약해줘" | 핵심 요약 | 1-2페이지 |
| (기본) | 보통 정리 | 3-5페이지 |
| "분석", "자세히", "꼼꼼히" | 상세 분석 | 5페이지+ |

### 분석 항목

```
1. 핵심 주제 (Main Topics)
   - 영상의 주요 주제 3~5개 식별

2. 타임라인 구조 (Timeline)
   - 주요 섹션별 시작 시간
   - 각 섹션 핵심 내용

3. 핵심 인사이트 (Key Insights)
   - 새로운 정보/관점
   - 실용적 팁/조언

4. 인용구 (Notable Quotes)
   - 기억할 만한 발언 (타임스탬프 포함)

5. 참고 자료 (References)
   - 영상에서 언급된 도구, 서비스, 논문 등
```

---

## Obsidian 노트 형식

```markdown
---
tags: [youtube, {주제태그}, {채널태그}]
source: YouTube
url: {YouTube URL}
channel: {채널명}
upload_date: {업로드일}
duration: {영상 길이}
subtitle_lang: {자막 언어}
subtitle_type: {manual/auto-generated}
created: {처리일}
---

# {영상 제목}

> **채널**: [{채널명}]({채널 URL})
> **업로드**: {업로드일} | **길이**: {분:초}
> **원본**: [{YouTube URL}]({YouTube URL})

## 요약

{전체 요약 — 3~5문장}

## 타임라인

| 시간 | 주제 | 핵심 내용 |
|------|------|----------|
| 00:00 | 인트로 | {내용} |
| 03:15 | {주제1} | {내용} |
| 10:42 | {주제2} | {내용} |
| ... | ... | ... |

## 핵심 인사이트

### 1. {인사이트 제목}
{설명}

### 2. {인사이트 제목}
{설명}

## 주요 인용

> "{인용구}" — [{분:초}]({YouTube URL}&t={초})

## 언급된 참고 자료

- {도구/서비스/논문 이름} — {간략 설명}

---

> 원본: YouTube "{영상 제목}" by {채널명}
> 자막: {언어} ({수동/자동생성})
> 처리일: {날짜}
```

---

## 파이프라인 요약

```
사용자: "https://youtube.com/watch?v=XXX 요약해줘"
  ↓
STEP A: 트랜스크립트 추출
  youtube-transcript-api → 한국어/영어 자막
  실패 시 → yt-dlp 자막 다운로드 폴백
  ↓
STEP B: 영상 메타데이터 + 챕터 수집 (🚨 CRITICAL — 정확성 보장!)
  1순위: yt-dlp --dump-json
  2순위: playwright-cli open → snapshot (⭐ WebFetch 대체)
  3순위: Playwright MCP (CLI 실패 시)
  → 제목, 채널, 업로드일, 길이, 조회수, 챕터 목록
  → 챕터가 있으면 STEP C 타임라인의 타임스탬프로 사용!
  ↓
STEP C: 콘텐츠 분석 (프리셋 반영)
  요약/보통/상세에 따라 깊이 조정
  타임라인 구조화 (챕터 기반 > 자막 추정), 인사이트 추출
  ↓
STEP D: Obsidian 저장
  정리된 노트 생성 (km-export-formats.md 형식)
```

---

## 설정 (km-config.json)

```json
{
  "youtube": {
    "preferredLanguage": "ko",
    "fallbackLanguage": "en"
  }
}
```

- `preferredLanguage`: 우선 자막 언어 (기본: ko)
- `fallbackLanguage`: 폴백 자막 언어 (기본: en)
