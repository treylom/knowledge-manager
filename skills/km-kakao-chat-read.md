# KakaoTalk Chat Read & Analyze

카카오톡 채팅방 메시지를 읽고 분석하여 Obsidian 노트로 정리합니다.

---

## 플랫폼별 메시지 수집

### macOS: kmsg

[kmsg](https://github.com/channprj/kmsg) CLI를 사용하여 메시지를 직접 읽습니다.

```bash
# 설치
brew install channprj/tap/kmsg

# 사용
kmsg read "{chatName}" --limit 500 --json
```

**출력 형식 (JSON):**
```json
[
  {
    "sender": "홍길동",
    "message": "안녕하세요",
    "timestamp": "2026-02-27T10:30:00"
  }
]
```

### Windows/WSL: 대화 내보내기 + TXT 파싱

카카오톡 PC의 "대화 내보내기" 기능을 활용합니다.

**Step 1: 내보내기 파일 확보**

```
사용자에게 안내:
1. 카카오톡 PC에서 해당 채팅방 열기
2. 우측 상단 ≡ (햄버거 메뉴) 클릭
3. "대화 내보내기" 선택
4. 텍스트 파일(.txt) 저장

또는 사용자가 이미 가지고 있는 .txt 파일 경로를 받기
```

**Step 2: TXT 파싱**

카카오톡 내보내기 TXT 형식:
```
--------------- 2026년 2월 27일 목요일 ---------------
[홍길동] [오전 10:30] 안녕하세요
[김철수] [오전 10:31] 반갑습니다
[홍길동] [오전 10:32] 오늘 회의 주제가 뭐였죠?
```

**파싱 로직 (Python):**

```python
import re
from datetime import datetime

def parse_kakao_export(filepath):
    """카카오톡 내보내기 TXT 파싱"""
    messages = []
    current_date = None
    date_pattern = re.compile(r'-+ (\d{4})년 (\d{1,2})월 (\d{1,2})일 .+? -+')
    msg_pattern = re.compile(r'\[(.+?)\] \[(오전|오후) (\d{1,2}):(\d{2})\] (.+)')

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            # 날짜 구분선
            date_match = date_pattern.match(line)
            if date_match:
                year, month, day = int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3))
                current_date = f"{year}-{month:02d}-{day:02d}"
                continue

            # 메시지 줄
            msg_match = msg_pattern.match(line)
            if msg_match and current_date:
                sender = msg_match.group(1)
                ampm = msg_match.group(2)
                hour = int(msg_match.group(3))
                minute = int(msg_match.group(4))
                text = msg_match.group(5)

                if ampm == "오후" and hour != 12:
                    hour += 12
                elif ampm == "오전" and hour == 12:
                    hour = 0

                messages.append({
                    "sender": sender,
                    "message": text,
                    "timestamp": f"{current_date}T{hour:02d}:{minute:02d}:00",
                    "date": current_date
                })

    return messages
```

**대안: kakaotalk_msg_preprocessor (pip)**

```bash
pip install kakaotalk_msg_preprocessor
```

```python
from kakaotalk_msg_preprocessor import KakaoMsgPreprocessor
kmp = KakaoMsgPreprocessor()
df = kmp.read("export.txt")
# pandas DataFrame으로 반환
```

### readMethod 자동 감지

```
km-config.json의 kakao.readMethod 확인:
  "auto" → 플랫폼 자동 감지
    macOS: kmsg 사용
    Windows/WSL: 내보내기 TXT 파싱
  "kmsg" → macOS kmsg 강제
  "export" → Windows 내보내기 강제
```

---

## 시간 필터링

수집된 메시지에서 특정 기간만 추출:

```python
def filter_by_period(messages, period="이번 주"):
    """기간별 필터링"""
    from datetime import datetime, timedelta

    now = datetime.now()

    if period in ("이번 주", "this week"):
        start = now - timedelta(days=now.weekday())
    elif period in ("오늘", "today"):
        start = now.replace(hour=0, minute=0, second=0)
    elif period in ("이번 달", "this month"):
        start = now.replace(day=1)
    elif period in ("최근 3일", "last 3 days"):
        start = now - timedelta(days=3)
    else:
        return messages  # 필터 없음

    start_str = start.strftime("%Y-%m-%dT%H:%M:%S")
    return [m for m in messages if m["timestamp"] >= start_str]
```

---

## 콘텐츠 분석

### A. 메시지 요약/정리

```
수집된 메시지 → AI 분석:
1. 주요 주제/토픽 식별
2. 핵심 논의 사항 요약
3. 결론/합의 사항 정리
4. 액션 아이템 추출
```

### B. 링크 추출

```python
import re

def extract_links(messages):
    """메시지에서 URL 추출"""
    url_pattern = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')
    links = []
    for msg in messages:
        urls = url_pattern.findall(msg["message"])
        for url in urls:
            links.append({
                "url": url,
                "shared_by": msg["sender"],
                "timestamp": msg["timestamp"],
                "context": msg["message"]
            })
    return links
```

### C. 선택적 링크 리서치

추출된 URL을 WebFetch/Playwright로 크롤링하여 내용 분석:

```
links = extract_links(messages)

for link in links:
  content = WebFetch(link["url"])
  link["summary"] = AI 요약(content)
```

---

## Obsidian 노트 형식

```markdown
---
tags: [kakao-chat, {채팅방이름}, {주요주제태그}]
source: KakaoTalk - {채팅방이름}
period: {시작일} ~ {종료일}
message_count: {메시지 수}
created: {날짜}
---

# {채팅방이름} - {기간} 정리

## 요약

{전체 요약 - 2~3문장}

## 주요 주제

### 주제 1: {주제명}
- {핵심 내용}
- {관련 논의}

### 주제 2: {주제명}
- ...

## 공유된 링크

| 링크 | 공유자 | 요약 |
|------|--------|------|
| [제목](URL) | {이름} | {한줄 요약} |

## 액션 아이템

- [ ] {할 일 1}
- [ ] {할 일 2}

## 참가자 통계

| 참가자 | 메시지 수 | 비율 |
|--------|----------|------|
| {이름} | {수} | {%} |

---

> 원본: KakaoTalk "{채팅방이름}" ({기간})
> 처리일: {날짜}
```

---

## 파이프라인 요약

```
사용자: "AI 오픈채팅방 이번 주 내용 정리해줘"
  ↓
STEP A: 채팅방 메시지 수집
  macOS: kmsg read "AI 오픈채팅" --limit 500 --json
  Windows: 대화 내보내기 TXT 파일 확보 → 파싱 → 날짜 필터
  ↓
STEP B: 콘텐츠 분석
  메시지 분류, 핵심 주제 추출, 링크 수집
  ↓
STEP C: (선택) 링크 리서치
  추출된 URL → WebFetch/Playwright → 내용 분석
  ↓
STEP D: Obsidian 저장
  정리된 노트 생성 (km-export-formats.md 형식)
```
