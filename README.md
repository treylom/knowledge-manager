[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/treylom-knowledge-manager-badge.png)](https://mseep.ai/app/treylom-knowledge-manager)

# Knowledge Manager Agent

> 📖 **[English documentation is available at the bottom of this page.](#-english-documentation)**
>
> **역할 경계**: Knowledge Manager는 특정 내부 인프라(GraphRAG 검색 서버 등)에 의존하지 않고 단독 동작하는 범용 지식관리 제품입니다 — 그런 연동은 선택적 어댑터로만 제공됩니다.

Claude Code용 종합 지식 관리 에이전트. 다양한 소스에서 콘텐츠를 수집하고, Zettelkasten 원칙에 따라 분석하여, Obsidian 또는 Notion에 저장합니다.

## ✨ 특징

- **다중 소스 입력**: 웹페이지, PDF, Notion
- **YouTube 트랜스크립트**: YouTube 영상 자막 자동 추출 + 분석 + 노트 생성 ⭐ NEW
- **카카오톡 채팅 분석**: 채팅방 메시지 분석 + 노트 생성 (macOS: 자동, Windows: 수동 내보내기) ⭐ NEW
- **PDF 및 이미지 OCR**: 스캔된 PDF와 이미지에서 텍스트 추출 (Claude Code용)
- **스마트 추출**: AI 기반 콘텐츠 분석 및 원자적 아이디어 추출
- **유연한 저장**: Obsidian, Notion, 또는 로컬 Markdown 파일
- **PPT/슬라이드 생성**: AI 이미지 기반 고퀄리티 프레젠테이션 (15+ 스타일)
- **간단한 설정**: 셋업 위저드가 모든 것을 안내
- **카카오톡 전송**: 정리된 노트를 카카오톡으로 자동 전송 (Windows/WSL)

---

## 📱 카카오톡 전송 설정

카카오톡 자동 전송은 [kmsg](https://github.com/channprj/kmsg)에서 영감을 받아 제작되었습니다.

| 플랫폼 | 도구 | 설치 |
|--------|------|------|
| **macOS** | [kmsg](https://github.com/channprj/kmsg) (원본) | `brew install channprj/tap/kmsg` |
| **Windows/WSL** | `send_kakao.py` (동봉) | 추가 설치 불필요 |

> **Windows/WSL**: KakaoTalk PC 버전이 실행 중이어야 합니다. `send_kakao.py`는 Win32 SendInput API로 메시지를 전송합니다.
>
> **macOS**: kmsg는 macOS용 Swift 바이너리입니다. 자세한 사용법은 [kmsg README](https://github.com/channprj/kmsg#readme)를 참고하세요.

#### km-config.json 설정

```json
{
  "kakao": {
    "enabled": true,
    "selfName": "홍길동"
  }
}
```

- `selfName`: 본인 카카오톡 채팅방 이름 (실명). **"나"가 아닌 본인 이름을 입력하세요!**

---

## 🔍 vault 검색 — `/km:search`

수집·정리한 vault를 **명령 하나로 검색**합니다. 뒤에서 어떤 검색 엔진이 도는지는 자동으로 결정됩니다:

```
① GraphRAG 서버(설치돼 있으면) → ② Obsidian CLI → ③ Obsidian MCP → ④ 텍스트 검색
```

앞 단계가 없거나 실패하면 자동으로 다음 단계로 넘어가기 때문에, **GraphRAG 없이도 바로 쓸 수 있고**, 나중에 GraphRAG 스택을 얹으면 같은 명령이 자동으로 의미 기반 검색으로 올라섭니다 (스택 구축은 같은 플러그인의 `/tofugraph` 명령 — 상세: `skills/km-graphrag-ops.md`).

```bash
/km:search MCP란?                          # 즉답 (quick)
/km:search --deep A와 B의 관계는?           # 상세 분석 (deep)
/km:search --deep --decomp=sub 질문…        # deep + 질문 분해를 별도 소형 모델에 맡김(선택)
```

### 검색이 실제로 하는 일 (1.5 → 1.7)

| 단계 | 하는 일 | 왜 필요한가 |
|---|---|---|
| **질문 분해 → 재조립** (1.7.0) | 검색 전에 질문을 `{의도, 대상 노트, 핵심어, 태그, 속성, 폴더 힌트, 시간}` 으로 한 번 분해하고, 의도별 고정 규칙표로 Obsidian CLI 호출을 짜 맞춥니다. 의도 7종: `nav`(어디 있나) · `content`(내용·비교) · `relation`(누가 참조하나) · `meta`(속성) · `tag` · `temporal`(최근·날짜) · `mixed` | 「어디 있어」와 「무슨 내용이야」는 다른 검색입니다. 파일명 축(한↔영 동의어: 회의록↔meeting/minutes 등)과 「역링크 0 → 본문 언급 폴백」이 여기서 붙습니다 |
| **5축 규칙 확장** (1.6.0) | 상위 노트(quick 2 · deep 5)마다 속성·역링크·아웃링크·문맥·태그 5축을 **항상** 실행하고 결과마다 축 라벨(`[prop] [bl] [ln] [ctx] [tag:#…]`)을 붙입니다 | 검색 결과 한 줄이 아니라 그 노트의 «주변»까지 한 번에 보입니다 |
| **신선도 보강** (1.5.1) | GraphRAG 색인이 40분 이상 오래됐거나 질문에 「오늘·어제·최근」이 있으면 Obsidian CLI 결과를 `[fresh:cli]` 라벨로 **덧붙입니다** (GraphRAG 순위는 그대로) | 방금 만든 노트가 「없다」로 나오는 일을 막습니다 |

분해에 실패하면 1.6.0 방식(규칙 파이프라인)으로 그대로 진행하고, 어느 단계든 답변은 실제 노트 내용 기반 + 출처 경로를 표기합니다.

### 실제 사례 (2026-09-08 · 노트 약 15,000개 vault · GraphRAG 서버 + Obsidian CLI)

> 아래는 2026-09-08 아침에 실제 vault(노트 약 15,000개)에서 1.7.0 절차를 그대로 돌린 기록입니다. vault 이름·경로는 `<vault>` 로 가렸고, 나머지 노트 이름·수치는 측정한 그대로입니다. 6건 중 2건은 GraphRAG 서버가 첫 호출에 20초 안에 답하지 않았습니다 — 사례 기록 자체는 원인을 조사하지 않았고, 직후(07:29) 별도로 잰 값은 스왑 8.3GB/9.2GB·서버 상주 메모리 18MB 로 서버가 스왑에 밀려 있었습니다(추정 원인). 그 경우에도 검색이 멈추지 않고 다음 단계로 넘어가는 모습을 그대로 실었습니다. 참고로 같은 서버의 검색 API 는 별도 24문항 벤치마크(같은 날 05:20, 3회 반복)에서 중앙값 0.23초였고, 이번 6사례의 정상 응답 4건은 5~8초였습니다.

**1. `GraphRAG 이론 MOC 어디 있어` — 위치 찾기(nav)**
- 분해: `intent=nav · targets=[GraphRAG-Theory-MOC, GraphRAG 이론 MOC] · keywords=[GraphRAG, 이론, MOC]`
- 실행: GraphRAG 서버 20초 무응답 → **Obsidian CLI 로 자동 전환** → 파일명 축 `search query="GraphRAG-Theory-MOC"` → 상위 노트 속성·역링크·아웃링크 확장
- 답: `GraphRAG-Theory-MOC.md` 가 **두 곳**(vault 루트 · `020-Library/Research/_MOC/`)에 같은 이름으로 있음을 짚어 주고, 역링크 45건과 함께 표시. 같은 결함 패턴(파일명 축이 없으면 「언급만 한 문서」가 상위로 올라옴)은 1.7.0 개발 중 다른 질문(「fable51 회의록 어디 있어」)에서 실제로 확인돼 파일명 축을 넣게 됐습니다.

**2. `누가 GraphRAG-Theory-MOC 를 참조하나` — 역링크(relation)**
- 분해: `intent=relation · targets=[GraphRAG-Theory-MOC]`
- 실행: GraphRAG 서버 8초 응답(상위 1위 = 같은 노트, 점수 0.048) → 신선도 확인 `FRESH: age=12m recent=0 supplement=no` → `backlinks file="GraphRAG-Theory-MOC"` → `links` · `properties` · `search:context`
- 답: 역링크 **45건** 목록, 아웃링크 0건(`No links found`). 서버 결과와 CLI 역링크가 같은 노트를 가리켜 교차 확인.

**3. `#graphrag 태그 붙은 최근 문서` — 태그 + 최근(mixed)**
- 분해: `intent=mixed · tags=[graphrag] · keywords=[graphrag, 최근, 문서]`
- 실행: GraphRAG 서버 5초 응답 → 「최근」이 있어 **신선도 보강이 켜짐** `FRESH: age=15m recent=1 supplement=yes` → `tags counts` 에서 부분 일치 후보(`#topic/graphrag` 88 · `#graphrag-theory` 33 · `#GraphRAG` 23) → 후보별 `search query="tag:…"` → `search query="[created:2026-09]"`
- 답: 세 태그 합계 **106건** + 색인 밖 최신 노트 1건을 `[fresh:cli]` 로 덧붙임. 서버 상위 5 중 3건은 출처 노트가 비어 있어 `⚠ source_note 결손 3/5` 를 함께 표기.

**4. `MCP란?` — 즉답(content · quick)**
- 분해: `intent=content · keywords=[MCP]`
- 실행: GraphRAG 서버 20초 무응답 → Obsidian CLI `search query="MCP" limit=1000`(1,000건 상한 도달) → `search:context query="MCP"` → 상위 노트 원문 읽기
- 답: 「Model Context Protocol — AI 모델을 도구·데이터·앱과 연결하는 개방형 표준, 공개 MCP 서버 1만 개 이상」 요약 + 출처 노트 경로. 서버 없이 CLI 만으로 즉답이 나오는 경로입니다.

**5. `--deep reranker 와 tier boost 의 차이` — 상세 비교(content · deep)**
- 분해: `intent=content · targets=[reranker, tier boost]`
- 실행: GraphRAG 서버 5초 응답(상위: `RAG-검색품질-향상기법-MOC` · `Reranker-검색-재정렬-기법`) → `FRESH: age=14m recent=0 supplement=no` → 원문 2건 읽기 → 상위 2 노트의 역링크·아웃링크 확장
- 답: 「reranker 는 1차 후보를 다시 줄 세우는 후처리, tier boost 는 노트 구조 등급(T1/T2/T3)에 따른 사전 가산점 — 작동 층과 시점이 다르다」 + 출처 2건. 소요 77초.

**6. `오늘 만든 에이전트 팀 관련 문서` — 최근(temporal)**
- 분해: `intent=temporal · targets=[에이전트 팀] · time.recent=true`
- 실행: GraphRAG 서버 5초 응답 → 「오늘」 → **신선도 보강이 켜짐** `FRESH: age=17m recent=1 supplement=yes` → CLI 결과 중 서버 결과에 없는 상위 5건을 `[fresh:cli]` 로 병기
- 답: 서버 상위 5(허브 MOC 위주)는 「오늘 만든 문서」를 직접 가리키지 못한다고 **솔직히 표기**하고, `[fresh:cli]` 5건을 그 아래 붙임. 1위는 출처 노트가 비어 있어 원문을 열지 못했고, 원문을 연 2위(`AI-에이전트`)는 머리말만 있는 빈 노트(스텁)임도 명시.

6건 중 GraphRAG 서버가 첫 시도에 응답한 것은 4건, 파일명 축이 실제로 쓰인 것은 1번, 신선도 보강이 켜진 것은 3·6번입니다.

### 설정·선택 사항

- `km-config.json` → `obsidianCli.vault`: CLI 가 붙을 vault 이름(비우면 `storage.obsidian.vaultPath` 의 폴더명). 기본 vault 가 테스트용일 수 있어 **모든 CLI 호출에 명시**됩니다.
- 환경변수 `KM_SEARCH_STALE_MIN`(기본 40): 신선도 보강이 켜지는 색인 나이(분). GraphRAG 서버 주소는 환경변수 `GRAPHRAG_API_URL` 또는 `km-config.json` 의 `linking.semantic_adapter.endpoint`(기본 `http://127.0.0.1:8400`).
- **Codex CLI 설치(방법 4)에서도 같은 검색이 `km-search` 스킬로 동작합니다.**
- 검색 전에 `000-START-HERE/` 구조 문서 3종을 먼저 참조하고, 답변 마지막 줄에 `구조 문서(<D>/3 참조 · 허브 <k>)` 로 참조 사실을 표기합니다.

## 🧭 지식관리 상담·대량 변형 — `/km:interview` · `/km:reform`

```
/km:interview                 # 폴더 나누기·MOC 허브·wiki 대상/비대상·스킬 추천을 상담해 _meta/KM-DESIGN.md 로 정리
/km:reform                    # (= plan) 변경 계획서만 작성 — 파일은 건드리지 않음
/km:reform apply <계획서>      # 계획서대로 이동·프론트매터·링크 일괄 적용 (git 스냅샷 자동, 롤백 1줄 안내)
/km:reform check              # 노트마다 MOC 링크 1개 + 일반 링크 1개 이상인지 코드로 검사
```

- `/km:setup` 이 `000-START-HERE/` 에 구조 문서 3종(START-HERE · VAULT-STRUCTURE · MOC-Map)을 만들고, `/km:search` 는 어느 검색 단계에서든 이 문서를 먼저 참조합니다.
- `/km:interview` 는 셋업 때 적은 프로필과 구조 문서를 읽고 상담하므로, 셋업을 먼저 마치면 질문이 줄어듭니다.
- 대량 변경은 항상 `plan` 으로 먼저 보고, `apply` 는 사용자가 명시할 때만 실행됩니다.
- **지원 범위**: `/km:interview`·`/km:reform` 은 Claude Code 커맨드입니다. Codex·Antigravity 공용 스킬 미러(`.agent/skills/`)에는 아직 없어 그 환경에서는 쓸 수 없습니다(다음 패치).

## 🚀 설치 방법

### 방법 1: Claude Code 플러그인 (권장)

Claude Code 1.0.33 이상에서 플러그인으로 설치할 수 있습니다.

```bash
# 마켓플레이스 추가
/plugin marketplace add treylom/knowledge-manager

# 플러그인 설치
/plugin install km@knowledge-manager
```

설치 후 `/km:setup`으로 셋업 위저드를 실행하세요.

### 방법 2: 수동 복사 (Claude Code / Claude Desktop)

```bash
# 저장소 클론
git clone https://github.com/treylom/knowledge-manager.git
cd knowledge-manager

# 커맨드·스킬·에이전트를 프로젝트에 설치
bash scripts/install-to-project.sh /your/project
```

기존 프로젝트 파일은 그대로 두고 플러그인 파일만 추가·갱신합니다.
설치기는 심볼릭 링크를 따라가지 않고(링크가 있으면 멈춤), 검사가 끝나기 전에는 최종 위치에 쓰지 않습니다(작업 파일은 `.claude/.km-install-staging.<pid>/` 에 모았다가 실패하면 제거하되, 되돌리지 못한 경우에는 보관하고 그 위치를 알려 줍니다) — 검사 단계에서 실패하면 프로젝트는 그대로이고, 교체 단계에서 실패하면 이전 파일을 되돌립니다(되돌리지 못한 경우 그 위치를 알려 줍니다). 설치 도중 HUP·INT(Ctrl-C)·TERM 신호를 받으면 같은 방식으로 이전 파일을 되돌립니다.

강제 종료(SIGKILL)나 전원 손실 때는 복구 코드를 실행할 수 없습니다. `.claude/.km-install-staging.*`가 남아 있으면 다음 설치는 파일을 바꾸지 않고 중단합니다. 안내된 작업 폴더와 `.old-*` 사본을 확인해 필요한 파일을 복구한 뒤 재시도하세요. 복구 전에 이 사본을 지우지 마세요. 신호 주입 시험은 실제 정전이나 디스크 기록의 내구성을 검증한 것이 아닙니다.

설치 후 `/knowledge-manager-setup`으로 셋업 위저드를 실행하세요.

### 방법 3: Antigravity 설정

Antigravity(Google)는 Agent Skills 표준을 지원합니다. `.agent/skills/` 폴더를 사용하면 스킬이 자동으로 인식됩니다.

> **장점**: Antigravity는 강력한 **내장 브라우저 에이전트**가 있어서 Playwright MCP가 필요 없습니다!
> Obsidian MCP만 설정하면 됩니다.

#### Step 1: 저장소 클론 및 스킬 복사

```bash
# 저장소 클론
git clone https://github.com/treylom/knowledge-manager.git

# .agent 폴더를 프로젝트에 복사 (Antigravity 스킬)
cp -r knowledge-manager/.agent /your/antigravity/project/

# 커맨드·스킬·에이전트는 설치 스크립트로 (프로젝트 .claude/ 에 복사)
bash knowledge-manager/scripts/install-to-project.sh /your/antigravity/project
```

> **참고**: `.agent/skills/` 폴더는 Antigravity, Gemini CLI, OpenCode 등 Agent Skills 표준을 지원하는 도구에서 호환됩니다. Claude Code 는 `.agent/skills/` 를 읽지 않고 `.claude/skills/` 를 쓰므로 위 설치 스크립트로 복사된 사본을 사용합니다.

#### Step 2: 자동 설정 (권장)

복사 후 Antigravity에서 다음과 같이 요청하세요:

**Windows:**
```
Knowledge Manager 설정을 도와줘.
내 Obsidian vault는 C:/Users/내이름/Documents/MyVault 야.
```

**Mac:**
```
Knowledge Manager 설정을 도와줘.
내 Obsidian vault는 /Users/내이름/Documents/MyVault 야.
```

**Linux:**
```
Knowledge Manager 설정을 도와줘.
내 Obsidian vault는 /home/내이름/Documents/MyVault 야.
```

에이전트가 자동으로:
1. MCP 설정 파일에 서버 추가
   - Windows: `%USERPROFILE%\.gemini\antigravity\mcp_config.json`
   - Mac/Linux: `~/.gemini/antigravity/mcp_config.json`
2. `km-config.json` 생성
3. 설정 완료 후 Refresh 방법 안내

#### Step 2 (대안): 수동 설정

자동 설정이 작동하지 않으면 수동으로 설정할 수 있습니다.

<details>
<summary>📋 수동 설정 방법 (클릭하여 펼치기)</summary>

**MCP 서버 설정:**

1. Antigravity에서 Agent 패널 열기
2. 우측 상단 **⋯** (점 세 개) 클릭
3. **MCP Servers** 선택
4. **Manage MCP Servers** 클릭
5. **View raw config** 클릭

설정 파일 위치: `C:\Users\<사용자명>\.gemini\antigravity\mcp_config.json`

`mcp_config.json`에 다음 내용을 추가하세요:

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "npx",
      "args": ["-y", "@huangyihe/obsidian-mcp"],
      "env": {
        "OBSIDIAN_VAULT_PATH": "C:/Users/YourName/Documents/YourVault"
      }
    }
  }
}
```

> **참고**: `OBSIDIAN_VAULT_PATH`를 실제 Obsidian vault 경로로 변경하세요.
>
> **Playwright는 선택 사항입니다.** Antigravity 내장 브라우저가 웹 스크래핑을 처리합니다.
> 스크린샷 캡처, DOM 조작 등 고급 기능이 필요한 경우에만 Playwright를 추가하세요.

**설정 새로고침:**

1. **Manage MCP Servers** 창에서 **Refresh** 클릭
2. obsidian 서버가 목록에 표시되는지 확인

**km-config.json 생성:**

프로젝트 폴더에 `km-config.json` 파일을 생성하세요:

```json
{
  "storage": {
    "primary": "obsidian",
    "obsidian": {
      "enabled": true,
      "vaultPath": "C:/Users/YourName/Documents/YourVault",
      "defaultFolder": "Zettelkasten"
    },
    "local": {
      "enabled": true,
      "outputPath": "./km-notes"
    }
  },
  "browser": {
    "provider": "antigravity"
  }
}
```

</details>

#### Step 3: 설정 확인

설정이 완료되면:

1. **Manage MCP Servers** 창에서 **Refresh** 클릭
2. obsidian 서버가 목록에 표시되는지 확인
3. 테스트: "https://example.com 이 페이지를 정리해줘"

### 방법 4: Codex CLI 플러그인 (ChatGPT Codex)

```bash
# 저장소 클론 (또는 이미 받아둔 로컬 경로 사용)
git clone https://github.com/treylom/knowledge-manager.git

# 로컬 마켓플레이스 등록 + 플러그인 설치
codex plugin marketplace add ./knowledge-manager
codex plugin add km@knowledge-manager
```

- 설치되면 `.agent/skills/`의 스킬 세트(km-workflow · km-setup · **km-search** 등)가 Codex 스킬 카탈로그에 노출됩니다.
- **vault 검색도 동일하게 동작합니다** (Codex 스킬명은 `km-search`): 위 `/km:search`와 같은 4단계 자동 폴백을 수행합니다 — GraphRAG 서버가 없어도 Obsidian CLI·텍스트 검색이 받아줍니다. (③ Obsidian MCP 티어는 MCP를 연결한 경우에만 사용됩니다.)
- Codex 환경은 이미 떠 있는 GraphRAG 서버(`GRAPHRAG_API_URL` 환경변수 또는 기본 `http://127.0.0.1:8400`)에 자동으로 연결합니다.
- ⚠️ **Codex sandbox 주의**: Codex 기본 sandbox 는 외부 바이너리 실행·네트워크를 제한합니다 — Obsidian CLI 검색 티어를 쓰려면 승인 응답 또는 `~/.codex/config.toml` 의 `sandbox_mode` 상향이 필요합니다(막히면 텍스트 검색으로 자동 폴백은 됩니다). Obsidian 데스크톱 앱이 실행 중이어야 CLI 티어가 동작합니다.
- **지원 범위**: Codex 플러그인은 현재 핵심 스킬 세트(km-workflow · km-setup · km-search · export · storage · social · zettelkasten 등 9종)를 제공합니다. PDF/YouTube/이미지 파이프라인·GraphRAG 운영(`/tofugraph`) 등 세부 스킬은 아직 Claude Code 전용입니다. `km-setup` 의 자동 환경분기도 Codex 미지원 — vault 경로는 첫 실행 때 직접 입력하면 됩니다. 1.3.0 에서 신설된 `/km:interview`·`/km:reform` 도 아직 Claude Code 전용입니다.

---

## 💡 Obsidian Vault 경로 찾기

Vault 경로를 모르시면 아래 방법으로 확인하세요.

### 방법 1: Obsidian 앱에서 확인

1. Obsidian 앱 실행
2. 좌측 하단 ⚙️ (설정) 클릭
3. **"파일 및 링크"** 메뉴 선택
4. 상단에 표시된 **"Vault 경로"** 복사

### 방법 2: AI에게 요청

Claude Code 또는 Antigravity에게 직접 물어보세요:

```
내 Obsidian vault 경로 찾는 법 알려줘
```

### OS별 일반적인 경로 예시

| OS | 경로 예시 |
|----|----------|
| **Windows** | `C:/Users/YourName/Documents/MyVault` |
| **Mac** | `/Users/YourName/Documents/MyVault` |
| **Linux** | `/home/yourname/Documents/MyVault` |

> ⚠️ **Windows 사용자**: 역슬래시(`\`) 대신 슬래시(`/`)를 사용하세요!
> - ❌ `C:\Users\...`
> - ✅ `C:/Users/...`

---

## 📋 요구사항

### 필수

| 항목 | 설명 |
|------|------|
| Claude Code / Antigravity | CLI, Desktop, 또는 Antigravity |
| Node.js 18+ | MCP 서버 실행용 |

### Playwright MCP 설치 (Claude Code 필수)

> **Antigravity 사용자**: 내장 브라우저가 있어 Playwright MCP 불필요. 이 섹션 건너뛰기.

Claude Code 환경에서 웹 콘텐츠를 추출하려면 **Playwright MCP 서버**가 필요합니다.

```bash
# Playwright MCP 자동 설치 (권장)
claude mcp add playwright -- npx -y @modelcontextprotocol/server-playwright

# 설치 확인
claude mcp list
# → playwright 서버가 표시되어야 함
```

**웹 크롤링 도구 우선순위:**

| 콘텐츠 유형 | 1순위 도구 | 2순위 (Fallback) |
|------------|-----------|------------------|
| SNS (Threads, Instagram) | Playwright MCP (필수) | - |
| 일반 웹 | WebFetch | Playwright MCP |

### YouTube 트랜스크립트 (선택)

| 항목 | 설치 명령 | 용도 |
|------|----------|------|
| youtube-transcript-api | `pip install youtube-transcript-api` | YouTube 자막 추출 (필수) |
| yt-dlp | `pip install yt-dlp` | 자막 폴백 + 메타데이터 (권장) |

### 카카오톡 채팅 분석 (선택)

> 카카오톡은 메시지 읽기 API를 제공하지 않아, macOS만 자동 수집이 가능합니다.

| 플랫폼 | 도구 | 자동화 | 설치 |
|--------|------|--------|------|
| macOS | [kmsg](https://github.com/channprj/kmsg) | 자동 (Accessibility API) | `brew install channprj/tap/kmsg` |
| Windows/WSL | 수동 "대화 내보내기" → TXT 파싱 | **수동 필요** | 추가 설치 불필요 |
| (TXT 파서) | kakaotalk_msg_preprocessor | - | `pip install kakaotalk_msg_preprocessor` |

### 선택 (셋업 위저드가 안내)

| 항목 | 용도 |
|------|------|
| Obsidian | 로컬 지식 관리 앱 (무료) |
| Notion 계정 | 팀 협업용 |

### PDF/OCR 처리용 (Claude Code 환경)

> **Antigravity 사용자**: 자체 내장 PDF/이미지 처리 기능 사용. 아래 설치 불필요.

| 항목 | 설치 명령 | 용도 |
|------|----------|------|
| Marker | `pip install marker-pdf` | PDF → Markdown 변환 (권장) |
| pytesseract | `pip install pytesseract pdf2image` | 스캔 PDF OCR |
| Tesseract OCR | [설치 가이드](https://github.com/tesseract-ocr/tesseract) | OCR 엔진 |
| pdfplumber | `pip install pdfplumber` | 테이블 추출 |

---

## 📖 사용법

### Claude Code에서

```
# 셋업 위저드 (최초 1회)
/knowledge-manager-setup

# 웹 아티클 정리
/knowledge-manager https://example.com/article

# PDF 파일 처리
/knowledge-manager /path/to/document.pdf

# Threads 포스트 정리
/knowledge-manager https://threads.net/@user/post/123

# YouTube 영상 트랜스크립트 정리
/knowledge-manager https://youtube.com/watch?v=XXX

# 카카오톡 채팅방 분석 (대화 내보내기 TXT 파일)
/knowledge-manager 카톡방 "AI 오픈채팅" 이번 주 내용 정리해줘
```

### 플러그인으로 설치한 경우

```
# 셋업 위저드
/km:setup

# 웹 아티클 정리
/km https://example.com/article

# 지식관리 상담
/km:interview

# 대량 변형(계획서만)
/km:reform
```

---

## 🎨 PPT/슬라이드 생성 (NEW!)

AI 이미지 생성 기반의 고퀄리티 프레젠테이션을 만들 수 있습니다.

> 📦 **Powered by [baoyu-slide-deck](https://github.com/JimLiu/baoyu-skills)** - JimLiu의 baoyu-skills에서 제공하는 슬라이드 생성 스킬입니다.

### 사용법

```bash
# 콘텐츠에서 PPT 생성
/knowledge-manager https://example.com/article PPT로 만들어줘

# 스타일 지정
/knowledge-manager content.md sketch-notes 스타일로 슬라이드 생성

# 직접 슬라이드 생성
/baoyu-slide-deck content.md --style corporate
```

### 스타일 가이드

| 스타일 | 용도 | 추천 상황 |
|--------|------|----------|
| `sketch-notes` | 교육/튜토리얼 | 강의, 워크샵 |
| `blueprint` | 기술 문서 | 아키텍처, 시스템 설계 |
| `corporate` | 비즈니스 | 투자 발표, 경영 보고 |
| `minimal` | 미니멀 | 심플한 발표 |
| `chalkboard` | 강의실 | 교육 콘텐츠 |
| `notion` | SaaS 대시보드 | 제품 데모, B2B |

### 옵션

| 옵션 | 설명 | 예시 |
|------|------|------|
| `--style <name>` | 비주얼 스타일 | `--style corporate` |
| `--audience <type>` | 대상 청중 | `--audience executives` |
| `--lang <code>` | 출력 언어 | `--lang ko` |
| `--slides <number>` | 슬라이드 수 | `--slides 15` |
| `--outline-only` | 아웃라인만 생성 | - |

### 출력물

```
slide-deck/{topic}/
├── outline.md           # 아웃라인
├── 01-slide-cover.png   # 개별 슬라이드 이미지
├── ...
├── {topic}.pptx         # PowerPoint 파일
└── {topic}.pdf          # PDF 파일
```

---

## 📁 저장 방식

### Obsidian 사용자

Obsidian vault에 Zettelkasten 스타일 노트로 저장됩니다.

```
Your-Vault/
├── Zettelkasten/
│   └── AI-연구/
│       └── MCP 프로토콜 개요 - 2026-01-17.md
├── Research/
└── Threads/
```

### Obsidian 없이 사용

로컬 폴더에 Obsidian 호환 Markdown 파일로 저장됩니다.

```
km-notes/
├── Zettelkasten/
├── Research/
└── Threads/
```

---

## 🔧 문제 해결

### Claude Code: MCP 서버 상태 확인

```bash
claude mcp list
```

### Antigravity: MCP 서버 확인

1. Agent 패널 → **⋯** → **MCP Servers**
2. 서버 목록에서 playwright, obsidian 상태 확인
3. 연결 실패 시 **Refresh** 클릭

### 설정 파일 위치

| 환경 | 설정 파일 |
|------|----------|
| Claude Code CLI | `claude mcp list` 로 확인(user 스코프 `~/.claude.json`) — 프로젝트 `.mcp.json` 은 직접 등록한 경우만 |
| Claude Desktop | `%APPDATA%\Claude\claude_desktop_config.json` |
| Antigravity | `C:\Users\<사용자명>\.gemini\antigravity\mcp_config.json` |

---

**링크 가중치·MOC 게이트 (1.3.0)**: `km-config.json` 의 `linking.scheme` = `"v1"`(기존 배점) 또는 `"v2"`(기본 — 구조 40 · 내용 45 · 의미 25, `agent-office/km-tools/km-tools.py print-weights --scheme v2` 로 표 확인) · `linking.mocGate` = `"auto"`(가장 가까운 MOC 에 자동 등록, 기본) 또는 `"confirm"`(후보 1개를 제안한 뒤 확인). 예시는 `km-config.example.json` 의 `linking` 절에 있습니다.

## 고급 옵션

### Hyperbrowser (선택적 대안)

> ⚠️ **권장하지 않음**: 기본적으로 Playwright MCP를 사용하세요. Hyperbrowser는 Playwright가 차단당하는 특수한 경우에만 고려하세요.

Playwright MCP가 특정 사이트에서 지속적으로 차단당하는 경우에만 Hyperbrowser를 고려하세요.

1. [hyperbrowser.ai](https://hyperbrowser.ai)에서 API 키 발급
2. `km-config.json`에서 `browser.provider`를 `"hyperbrowser"`로 변경
3. MCP 설정에 hyperbrowser 서버 추가:

```json
"hyperbrowser": {
  "command": "npx",
  "args": ["-y", "hyperbrowser-mcp"],
  "env": {
    "HYPERBROWSER_API_KEY": "your-api-key"
  }
}
```

**주의**: Hyperbrowser는 유료 서비스이며, 설정이 복잡해질 수 있습니다. 대부분의 경우 Playwright MCP로 충분합니다.

### 환경 변수 지원

```bash
# (참고) 설정은 km-config.json 이 정본입니다 — 환경변수 오버라이드는 현재 미지원.
```

---

## 🤝 기여

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 라이선스

MIT License - 자유롭게 사용, 수정, 배포하세요.

## 🔗 관련 링크

- [Claude Code](https://code.claude.com)
- [Claude Code Plugins](https://claude.com/blog/claude-code-plugins)
- [MCP Protocol](https://modelcontextprotocol.io)
- [Obsidian](https://obsidian.md)
- [Antigravity MCP 설정 가이드](https://composio.dev/blog/howto-mcp-antigravity)

---

# 🇺🇸 English Documentation

> **Role boundary**: Knowledge Manager is a standalone, general-purpose knowledge tool — it does not depend on any private infrastructure (e.g., a GraphRAG search server); such integrations ship only as optional adapters.

## What is Knowledge Manager?

A comprehensive knowledge management agent for Claude Code. It collects content from various sources, analyzes it using Zettelkasten principles, and saves it to Obsidian or Notion.

## Features

- **Multiple Input Sources**: Web pages, PDFs, Notion
- **YouTube Transcripts**: Auto-extract YouTube subtitles + analyze + generate notes
- **KakaoTalk Chat Analysis**: Analyze chat messages + generate notes (macOS: auto, Windows: manual export)
- **PDF & Image OCR**: Extract text from scanned PDFs and images (Claude Code)
- **Smart Extraction**: AI-powered content analysis and atomic idea extraction
- **Flexible Storage**: Obsidian, Notion, or local Markdown files
- **KakaoTalk Send**: Auto-send notes to KakaoTalk (Windows/WSL)
- **Easy Setup**: Setup wizard guides you through everything

---

## Installation

### Option 1: Claude Code Plugin (Recommended)

Available for Claude Code 1.0.33 and above.

```bash
# Add marketplace
/plugin marketplace add treylom/knowledge-manager

# Install plugin
/plugin install km@knowledge-manager
```

After installation, run `/km:setup` to start the setup wizard.

### Option 2: Manual Copy (Claude Code / Claude Desktop)

```bash
# Clone repository
git clone https://github.com/treylom/knowledge-manager.git
cd knowledge-manager

# Install commands, skills, and agents into your project
bash scripts/install-to-project.sh /your/project
```

Existing project files are kept; only the plugin's files are added or refreshed.
The installer never follows symbolic links (it stops if it finds one) and writes nothing to the final locations until every file has been staged (under `.claude/.km-install-staging.<pid>/`) and checked — if the check fails the project is unchanged, and if the final swap fails the previous files are put back (anything it could not put back is kept beside the new files and listed). HUP, INT (Ctrl-C), and TERM signals trigger the same rollback.

SIGKILL and power loss cannot run cleanup. If `.claude/.km-install-staging.*` remains, the next install refuses to change any files. Inspect the named staging directory and `.old-*` copies, recover the files you need, then retry; do not delete those copies before recovery. Signal-injection tests do not verify physical power loss or disk-write durability.

After installing, run `/knowledge-manager-setup` to start the setup wizard.

### Option 3: Antigravity Setup

Antigravity (Google) supports the Agent Skills standard. The `.agent/skills/` folder is automatically recognized.

> **Advantage**: Antigravity has a powerful **built-in browser agent**, so Playwright MCP is not required!
> You only need to configure Obsidian MCP.

#### Step 1: Clone and Copy Skills

```bash
# Clone repository
git clone https://github.com/treylom/knowledge-manager.git

# Copy .agent folder (Antigravity skills)
cp -r knowledge-manager/.agent /your/antigravity/project/

# Commands, skills, and agents go in via the install script (copied into the project's .claude/)
bash knowledge-manager/scripts/install-to-project.sh /your/antigravity/project
```

> **Note**: The `.agent/skills/` folder is compatible with tools supporting the Agent Skills standard, such as Antigravity, Gemini CLI, and OpenCode. Claude Code does not read `.agent/skills/`; it uses `.claude/skills/`, which the install script above populates.

#### Step 2: Automatic Setup (Recommended)

After copying, ask Antigravity:

**Windows:**
```
Help me set up Knowledge Manager.
My Obsidian vault is at C:/Users/MyName/Documents/MyVault.
```

**Mac:**
```
Help me set up Knowledge Manager.
My Obsidian vault is at /Users/MyName/Documents/MyVault.
```

**Linux:**
```
Help me set up Knowledge Manager.
My Obsidian vault is at /home/myname/Documents/MyVault.
```

The agent will automatically:
1. Add MCP servers to config file
   - Windows: `%USERPROFILE%\.gemini\antigravity\mcp_config.json`
   - Mac/Linux: `~/.gemini/antigravity/mcp_config.json`
2. Create `km-config.json`
3. Guide you to refresh the configuration

#### Step 2 (Alternative): Manual Setup

If automatic setup doesn't work, you can configure manually.

<details>
<summary>📋 Manual Setup Instructions (click to expand)</summary>

**Configure MCP Servers:**

1. Open Agent panel in Antigravity
2. Click **⋯** (three dots) in the top right
3. Select **MCP Servers**
4. Click **Manage MCP Servers**
5. Click **View raw config**

Config file location: `C:\Users\<username>\.gemini\antigravity\mcp_config.json`

Add the following to `mcp_config.json`:

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "npx",
      "args": ["-y", "@huangyihe/obsidian-mcp"],
      "env": {
        "OBSIDIAN_VAULT_PATH": "C:/Users/YourName/Documents/YourVault"
      }
    }
  }
}
```

> **Note**: Replace `OBSIDIAN_VAULT_PATH` with your actual Obsidian vault path.
>
> **Playwright is optional.** Antigravity's built-in browser handles web scraping.
> Only add Playwright if you need advanced features like screenshot capture or DOM manipulation.

**Refresh Configuration:**

1. Click **Refresh** in the Manage MCP Servers window
2. Verify that obsidian server appears in the list

**Create km-config.json:**

Create a `km-config.json` file in your project folder:

```json
{
  "storage": {
    "primary": "obsidian",
    "obsidian": {
      "enabled": true,
      "vaultPath": "C:/Users/YourName/Documents/YourVault",
      "defaultFolder": "Zettelkasten"
    },
    "local": {
      "enabled": true,
      "outputPath": "./km-notes"
    }
  },
  "browser": {
    "provider": "antigravity"
  }
}
```

</details>

#### Step 3: Verify Setup

After setup is complete:

1. Click **Refresh** in the Manage MCP Servers window
2. Verify that obsidian server appears in the list
3. Test: "Summarize this page: https://example.com"

---

## 💡 Finding Your Obsidian Vault Path

If you don't know your vault path, here's how to find it.

### Method 1: From Obsidian App

1. Open Obsidian app
2. Click ⚙️ (Settings) in the bottom left
3. Select **"Files & Links"**
4. Copy the **"Vault path"** shown at the top

### Method 2: Ask AI

Ask Claude Code or Antigravity directly:

```
Help me find my Obsidian vault path
```

### Typical Paths by OS

| OS | Example Path |
|----|--------------|
| **Windows** | `C:/Users/YourName/Documents/MyVault` |
| **Mac** | `/Users/YourName/Documents/MyVault` |
| **Linux** | `/home/yourname/Documents/MyVault` |

> ⚠️ **Windows users**: Use forward slashes (`/`) instead of backslashes (`\`)!
> - ❌ `C:\Users\...`
> - ✅ `C:/Users/...`

---

## Requirements

### Required

| Item | Description |
|------|-------------|
| Claude Code / Antigravity | CLI, Desktop, or Antigravity |
| Node.js 18+ | For running MCP servers |

### Playwright MCP Installation (Required for Claude Code)

> **Antigravity users**: Has built-in browser, Playwright MCP not needed. Skip this section.

To extract web content in Claude Code, you need the **Playwright MCP server**.

```bash
# Auto-install Playwright MCP (recommended)
claude mcp add playwright -- npx -y @modelcontextprotocol/server-playwright

# Verify installation
claude mcp list
# → playwright server should appear
```

**Web Crawling Tool Priority:**

| Content Type | Primary Tool | Fallback |
|--------------|-------------|----------|
| SNS (Threads, Instagram) | Playwright MCP (required) | - |
| General Web | WebFetch | Playwright MCP |

### YouTube Transcripts (Optional)

| Item | Install Command | Purpose |
|------|-----------------|---------|
| youtube-transcript-api | `pip install youtube-transcript-api` | YouTube subtitle extraction (required) |
| yt-dlp | `pip install yt-dlp` | Subtitle fallback + metadata (recommended) |

### KakaoTalk Chat Analysis (Optional)

> KakaoTalk provides no message reading API. Only macOS supports auto-collection.

| Platform | Tool | Automation | Install |
|----------|------|------------|---------|
| macOS | [kmsg](https://github.com/channprj/kmsg) | Auto (Accessibility API) | `brew install channprj/tap/kmsg` |
| Windows/WSL | Manual "Export Chat" → TXT parsing | **Manual required** | No additional install needed |
| (TXT parser) | kakaotalk_msg_preprocessor | - | `pip install kakaotalk_msg_preprocessor` |

### Optional (Setup wizard will guide you)

| Item | Purpose |
|------|---------|
| Obsidian | Local knowledge management app (free) |
| Notion account | For team collaboration |

### For PDF/OCR Processing (Claude Code)

> **Antigravity users**: Use built-in PDF/image processing. No installation required.

| Item | Install Command | Purpose |
|------|-----------------|---------|
| Marker | `pip install marker-pdf` | PDF → Markdown (recommended) |
| pytesseract | `pip install pytesseract pdf2image` | Scanned PDF OCR |
| Tesseract OCR | [Install Guide](https://github.com/tesseract-ocr/tesseract) | OCR engine |
| pdfplumber | `pip install pdfplumber` | Table extraction |

---

## Installation & Configuration

knowledge-manager is distributed as a git repository that adapts to **your** Obsidian vault at install time. The skill, agent, and command files in this repo contain placeholder tokens (e.g. `{{VAULT_PATH}}`) that get substituted with your real paths the first time you run the setup wizard. After that, `git pull` + `/km-update` keeps you current without ever touching your personal config.

### First-time setup

```bash
# 1. Clone the repository
git clone https://github.com/treylom/knowledge-manager.git
cd knowledge-manager

# 2. (Optional) Install Node.js 18+ and Playwright MCP — see Requirements section above

# 3. Run the setup wizard inside Claude Code
#    Inside Claude Code, type:
/knowledge-manager-setup
```

The setup wizard will:

1. Ask for your Obsidian vault path (e.g. `/home/you/Documents/MyVault` or `C:/Users/You/Documents/MyVault`).
2. Auto-detect your Obsidian CLI executable (v1.12.4+) if Obsidian desktop is installed.
3. Generate `km-config.json` in the repo root (this file is gitignored — your personal config stays local).
4. Run `scripts/configure-vault-paths.sh` which replaces every `{{VAULT_PATH}}`, `{{VAULT_NAME}}`, `{{OBSIDIAN_CLI}}`, `{{ZETTELKASTEN_ROOT}}`, and `{{RESEARCH_ROOT}}` placeholder in `skills/`, `agents/`, and `commands/` with your real values.
5. Mark the substituted files with `git update-index --skip-worktree` so the replacements never show up as dirty in `git status`.

When the wizard finishes, every skill and command file points to **your** vault — no manual find-and-replace required.

### Updating to the latest version

When you want to pull upstream improvements, use the `/km-update` slash command instead of a raw `git pull`:

```
/km-update
```

Under the hood this runs `scripts/km-update.sh`, which:

1. Unlocks the skip-worktree flag on every placeholder-substituted file.
2. Restores the original placeholder content with `git checkout HEAD -- <files>`.
3. Runs `git pull origin <current-branch>` to fetch upstream changes.
4. Re-runs `scripts/configure-vault-paths.sh` to re-substitute placeholders with your current `km-config.json` values.
5. Re-applies the skip-worktree lock.

A plain `git pull` will still work — but if your previous substitution has diverged from upstream (e.g. upstream changed a line around a placeholder), you may hit a merge conflict. `/km-update` is the safe path.

### Re-configuring your vault path

If you move your vault, rename it, or want to point knowledge-manager at a different vault, just re-run the setup wizard:

```
/knowledge-manager-setup
```

The wizard backs up your existing `km-config.json` (timestamped), generates a new one, and re-runs the substitution engine. Your previous values are preserved in the backup file in case you need to roll back.

### Under the hood — placeholder system

Source files in this repo use these 5 placeholder tokens. The setup wizard replaces them with values from your `km-config.json`:

| Placeholder | Config field | Default | Meaning |
|---|---|---|---|
| `{{VAULT_PATH}}` | `storage.obsidian.vaultPath` | *(required)* | Absolute path to your Obsidian vault |
| `{{VAULT_NAME}}` | derived from basename of `vaultPath` | *(derived)* | Vault folder name (e.g. `MyVault`) |
| `{{OBSIDIAN_CLI}}` | `obsidianCli.path` | `""` (empty) | Path to Obsidian CLI executable; empty string if Obsidian desktop is not installed |
| `{{ZETTELKASTEN_ROOT}}` | `storage.obsidian.zettelkastenRoot` | `"Zettelkasten"` | Vault-relative path to your Zettelkasten root folder |
| `{{RESEARCH_ROOT}}` | `storage.obsidian.researchRoot` | `"Research"` | Vault-relative path to your research/MOC root folder |

If you edit a skill file yourself and need it to stay portable, write the placeholder form (e.g. `{{VAULT_PATH}}/Zettelkasten/note.md`) and re-run `/knowledge-manager-setup` (or `bash scripts/configure-vault-paths.sh` directly). See [`docs/vault-path-configuration.md`](docs/vault-path-configuration.md) for the full technical reference, troubleshooting, and the skip-worktree rationale.

---

## Usage

### In Claude Code

```
# Setup wizard (first time only)
/knowledge-manager-setup

# Process web article
/knowledge-manager https://example.com/article

# Process PDF file
/knowledge-manager /path/to/document.pdf

# Process Threads post
/knowledge-manager https://threads.net/@user/post/123

# YouTube video transcript
/knowledge-manager https://youtube.com/watch?v=XXX

# KakaoTalk chat analysis
/knowledge-manager Analyze "AI Chat Room" messages from this week
```

### If installed as plugin

```
# Setup wizard
/km:setup

# Process web article
/km https://example.com/article
```

---

## 🔍 Searching your vault — `/km:search`

One command searches the vault you have been building. The engine is picked automatically:

```
① GraphRAG server (if installed) → ② Obsidian CLI → ③ Obsidian MCP → ④ plain-text search
```

Each stage falls through to the next when it is missing or fails, so it **works without GraphRAG** and upgrades itself to semantic search once you add the stack (`/tofugraph` in the same plugin — see `skills/km-graphrag-ops.md`).

```bash
/km:search What is MCP?                       # quick answer
/km:search --deep How do A and B relate?      # detailed analysis
/km:search --deep --decomp=sub …              # deep + delegate query decomposition to a small model (optional)
```

### What actually happens (1.5 → 1.7)

| Step | What it does | Why |
|---|---|---|
| **Decompose → reassemble** (1.7.0) | Before searching, the question is split into `{intent, target notes, keywords, tags, properties, folder hint, time}` and a fixed per-intent rule table turns that into Obsidian CLI calls. Seven intents: `nav` · `content` · `relation` · `meta` · `tag` · `temporal` · `mixed` | "Where is X?" and "What does X say?" are different searches. This is where the filename axis (with Korean↔English synonyms such as 회의록 ↔ meeting / minutes) and the "no backlinks → body-mention fallback" live |
| **Rule-driven 5-axis expansion** (1.6.0) | For the top notes (quick 2 · deep 5) it **always** runs five axes — properties, backlinks, outlinks, context lines, tags — and labels every line (`[prop] [bl] [ln] [ctx] [tag:#…]`) | You see the neighbourhood of a note, not just one hit |
| **Freshness supplement** (1.5.1) | If the GraphRAG index is older than 40 minutes, or the question says "today / yesterday / recent", Obsidian CLI results are **appended** with a `[fresh:cli]` label (GraphRAG ranking untouched) | Notes you wrote a minute ago no longer come back as "not found" |

If decomposition fails, the 1.6.0 rule pipeline runs unchanged. Every answer is grounded in actual note content and cites source paths.

### Real examples (2026-09-08 · ~15,000-note vault · GraphRAG server + Obsidian CLI)

> Recorded on the morning of 2026-09-08 against a real vault (~15,000 notes) by running the 1.7.0 procedure step by step. Vault names and paths are masked as `<vault>`; note names and numbers are as measured. In 2 of the 6 cases the GraphRAG server did not answer the first call within 20 s — the case logs themselves did not investigate why; a separate reading taken right after (07:29) showed swap at 8.3 GB of 9.2 GB and the server's resident memory down to 18 MB, i.e. the server had been paged out (probable cause). Those cases are kept as-is because they show the search falling through to the next stage instead of stopping. For scale: the same server's search API had a median of 0.23 s in a separate 24-question benchmark that day (05:20, 3 runs), while the 4 normal answers in these 6 cases took 5–8 s.

**1. `Where is the GraphRAG theory MOC?` — locate (nav)**
- Decomposed: `intent=nav · targets=[GraphRAG-Theory-MOC, GraphRAG 이론 MOC] · keywords=[GraphRAG, 이론, MOC]`
- Ran: GraphRAG server silent for 20 s → **automatic switch to Obsidian CLI** → filename axis `search query="GraphRAG-Theory-MOC"` → properties / backlinks / outlinks of the top notes
- Answer: points out that `GraphRAG-Theory-MOC.md` exists in **two places** (vault root and `020-Library/Research/_MOC/`) and lists its 45 backlinks. The same failure pattern (without a filename axis, a note that merely *mentions* the target ranks first) was observed on a different question while 1.7.0 was being built — that is why the filename axis exists.

**2. `Who references GraphRAG-Theory-MOC?` — backlinks (relation)**
- Decomposed: `intent=relation · targets=[GraphRAG-Theory-MOC]`
- Ran: GraphRAG server answered in 8 s (top hit = the note itself, score 0.048) → freshness check `FRESH: age=12m recent=0 supplement=no` → `backlinks file="GraphRAG-Theory-MOC"` → `links` · `properties` · `search:context`
- Answer: **45 backlinks**, 0 outlinks (`No links found`). Server ranking and CLI backlinks agree on the same note.

**3. `Recent notes tagged #graphrag` — tag + recency (mixed)**
- Decomposed: `intent=mixed · tags=[graphrag] · keywords=[graphrag, recent, notes]`
- Ran: server answered in 5 s → the word "recent" **triggers the freshness supplement** `FRESH: age=15m recent=1 supplement=yes` → `tags counts` partial matches (`#topic/graphrag` 88 · `#graphrag-theory` 33 · `#GraphRAG` 23) → `search query="tag:…"` per candidate → `search query="[created:2026-09]"`
- Answer: **106 notes** across the three tags, plus one note newer than the index appended as `[fresh:cli]`. Three of the server's top-5 lacked a source note, flagged with the `⚠ source_note 결손 3/5` line (“source note missing 3/5” — the label is printed in Korean).

**4. `What is MCP?` — quick answer (content)**
- Decomposed: `intent=content · keywords=[MCP]`
- Ran: server silent for 20 s → Obsidian CLI `search query="MCP" limit=1000` (hit the cap) → `search:context query="MCP"` → read the top note
- Answer: "Model Context Protocol — an open standard that connects AI models to tools, data and apps; 10,000+ public MCP servers" with the source path. This is the CLI-only path that works with no server at all.

**5. `--deep difference between reranker and tier boost` — detailed comparison (content · deep)**
- Decomposed: `intent=content · targets=[reranker, tier boost]`
- Ran: server answered in 5 s (top: `RAG-검색품질-향상기법-MOC`, `Reranker-검색-재정렬-기법`) → `FRESH: age=14m recent=0 supplement=no` → read both notes → backlinks/outlinks of the top 2
- Answer: "a reranker re-orders first-pass candidates after retrieval; tier boost is a pre-computed bonus from the note's structural tier (T1/T2/T3) — different layer, different moment" with two sources. 77 s end to end.

**6. `Agent-team notes created today` — recency (temporal)**
- Decomposed: `intent=temporal · targets=[agent team] · time.recent=true`
- Ran: server answered in 5 s → "today" **triggers the freshness supplement** `FRESH: age=17m recent=1 supplement=yes` → the top 5 CLI results absent from the server list are appended as `[fresh:cli]`
- Answer: says plainly that the server's top 5 (mostly hub MOCs) do not point at anything created today, then appends the 5 `[fresh:cli]` notes; also notes that the #1 hit had no source note to open, and the #2 hit (`AI-에이전트`), the only one actually opened, is a front-matter-only stub.

Across the six: the GraphRAG server answered on the first try in 4, the filename axis actually fired in #1, and the freshness supplement fired in #3 and #6.

### Configuration

- `km-config.json` → `obsidianCli.vault`: the vault name passed to every CLI call (falls back to the folder name of `storage.obsidian.vaultPath`).
- `KM_SEARCH_STALE_MIN` (default 40): index age in minutes that triggers the freshness supplement. The GraphRAG server URL comes from the `GRAPHRAG_API_URL` environment variable or `linking.semantic_adapter.endpoint` in `km-config.json` (default `http://127.0.0.1:8400`).
- The same search runs as the `km-search` skill under Codex CLI (Option 4).
- Before searching, the three structure notes under `000-START-HERE/` are consulted first, and the last line of every answer records it as `구조 문서(<D>/3 참조 · 허브 <k>)` (“structure docs consulted <D>/3 · hubs <k>”).

## Storage

### For Obsidian Users

Notes are saved in Zettelkasten style in your Obsidian vault.

```
Your-Vault/
├── Zettelkasten/
│   └── AI-Research/
│       └── MCP Protocol Overview - 2026-01-17.md
├── Research/
└── Threads/
```

### Without Obsidian

Notes are saved as Obsidian-compatible Markdown files in a local folder.

```
km-notes/
├── Zettelkasten/
├── Research/
└── Threads/
```

---

## Troubleshooting

### Claude Code: Check MCP Server Status

```bash
claude mcp list
```

### Antigravity: Check MCP Servers

1. Agent panel → **⋯** → **MCP Servers**
2. Check status of playwright and obsidian in server list
3. Click **Refresh** if connection failed

### Config File Locations

| Environment | Config File |
|-------------|-------------|
| Claude Code CLI | check with `claude mcp list` (user scope, `~/.claude.json`) — a project `.mcp.json` applies only if you registered it there yourself |
| Claude Desktop | `%APPDATA%\Claude\claude_desktop_config.json` |
| Antigravity | `C:\Users\<username>\.gemini\antigravity\mcp_config.json` |

---

## Advanced Options

### Hyperbrowser (Optional Alternative)

> ⚠️ **Not recommended**: Use Playwright MCP by default. Only consider Hyperbrowser if Playwright is consistently blocked.

Only consider Hyperbrowser if Playwright MCP is consistently blocked on specific sites.

1. Get API key from [hyperbrowser.ai](https://hyperbrowser.ai)
2. Change `browser.provider` to `"hyperbrowser"` in `km-config.json`
3. Add hyperbrowser server to MCP config:

```json
"hyperbrowser": {
  "command": "npx",
  "args": ["-y", "hyperbrowser-mcp"],
  "env": {
    "HYPERBROWSER_API_KEY": "your-api-key"
  }
}
```

**Note**: Hyperbrowser is a paid service and may add configuration complexity. Playwright MCP is sufficient for most cases.

### Environment Variable Support

```bash
# (Note) km-config.json is the source of truth — env-var overrides are not currently supported.
```

---

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

MIT License - Free to use, modify, and distribute.

## Related Links

- [Claude Code](https://code.claude.com)
- [Claude Code Plugins](https://claude.com/blog/claude-code-plugins)
- [MCP Protocol](https://modelcontextprotocol.io)
- [Obsidian](https://obsidian.md)
- [Antigravity MCP Setup Guide](https://composio.dev/blog/howto-mcp-antigravity)
- [baoyu-skills](https://github.com/JimLiu/baoyu-skills) - PPT/슬라이드 생성 스킬 원본
- [kmsg](https://github.com/channprj/kmsg) - KakaoTalk 메시지 전송 CLI (macOS)
