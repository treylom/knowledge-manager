---
name: km-search
description: vault 통합 검색 — GraphRAG(있으면) → Obsidian CLI → (Obsidian MCP) → 텍스트 검색 4단계 자동 폴백. quick(즉답)/deep(분석) 자동 라우팅
---

# km-search — vault 통합 검색

사용자가 vault 검색을 요청하면(예: "vault에서 X 찾아줘", "km search X", "--deep X") 이 스킬의 절차를 따른다. **query = 사용자의 질문 본문**(아래 플래그 제거 후).

> **핵심 설계**: 검색 창구는 이 스킬 하나입니다. 뒤에서 어떤 검색 엔진이 도는지는 자동으로 결정됩니다 —
> **① GraphRAG 서버(설치돼 있으면) → ② Obsidian CLI → ③ Obsidian MCP(연결된 경우) → ④ 텍스트 검색** 순서로,
> 앞 단계가 없거나 실패하면 자동으로 다음 단계로 넘어갑니다. GraphRAG를 아직 설치하지 않았어도
> 이 스킬은 그대로 동작합니다(②~④가 받아줍니다). 나중에 GraphRAG 스택을 얹으면 **같은 절차가 자동으로 ①을 쓰기 시작합니다.**

## Phase -1: 설정 읽기

1. `km-config.json`을 찾는다 (현재 폴더 → 플러그인 설치 시 setup이 만든 위치 순).
2. `storage.obsidian.vaultPath` → `VAULT_PATH`. 없으면 사용자에게 vault 경로를 1회 묻고 진행.
3. `obsidianCli.path` → `OBSIDIAN_CLI` (비어 있으면 아래 Tier 2의 자동 감지 사용).
4. `SEARCH_ENDPOINT` = `linking.semantic_adapter.endpoint` → 환경변수 `GRAPHRAG_API_URL` → 기본값 `http://127.0.0.1:8400` 순. **미설정이어도 기본값을 탐침한다** — 로컬에 서버가 없으면 즉시 연결 거부로 끝나 지연이 거의 없고(`--connect-timeout 3`은 상한일 뿐), 덕분에 나중에 `/tofugraph build`로 스택을 얹으면 설정 변경 없이 같은 절차가 자동으로 Tier 1을 쓰기 시작한다.

   ```bash
   # 필수 실행(집행 계약): endpoint 는 반드시 아래 셸 할당으로 결정하고, echo 로 확인한 뒤 Tier 1 을 호출한다.
   # CONFIG_ENDPOINT = km-config.json 의 linking.semantic_adapter.endpoint 값 (없으면 빈 값 유지)
   SEARCH_ENDPOINT="${CONFIG_ENDPOINT:-${GRAPHRAG_API_URL:-http://127.0.0.1:8400}}"
   echo "SEARCH_ENDPOINT=${SEARCH_ENDPOINT}"
   ```

## Phase 0: 모드 결정

IF query가 비어있으면:
  → "사용법: `km-search <질문>` 또는 `km-search --deep <질문>`"
  → "예시: `km-search MCP란?` | `km-search --deep 프롬프트 엔지니어링 기법 비교`"
  → 종료

### 플래그 파싱
- `--quick` 또는 `-q` → **QUICK** (플래그 제거 후 나머지가 query)
- `--deep` 또는 `-d` → **DEEP** (플래그 제거 후 나머지가 query)
- `--no-moc` → MOC 제외, 원자 노트 전용
- 플래그 없음 → **AUTO**

### AUTO 라우팅
- DEEP: 문장형 5단어+, "~하려면/방법/비교/차이/관계/영향", 분석 요청("설명해줘/정리해줘"), 복수 개념("A vs B"), 방법론("어떻게/왜")
- QUICK: 그 외 (키워드 1-3개, 정의형 "~란?", 노트 찾기)

## Phase 0.5: MOC 우선 라우팅

검색 결과 중 MOC 성격 노트(frontmatter `type`/`tags`에 MOC 포함, 또는 파일명에 `-MOC`)를 최상위로 고정한다:
1. 결과를 MOC / 원자 노트로 분류
2. 상위 최대 3개 MOC를 맨 위로 고정 (점수 순)
3. 원자 노트는 그 아래 점수 순
4. 표시: `📌 상위 MOC (N)` 섹션 + `📄 원자 노트 (N)` 섹션 분리 (MOC 0개면 📌 생략)

> Why: 노트가 많아질수록 원자 나열은 찾기 어려움 — MOC(지도 노트)가 허브·진입점 역할.

## 검색 엔진 — 4단계 자동 폴백

### Tier 1 — GraphRAG 서버 (설치된 경우, 의미 기반 하이브리드 검색)
```bash
QUERY_ENCODED=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "${QUERY}")
curl -s "${SEARCH_ENDPOINT}/api/search?q=${QUERY_ENCODED}&top_k=${TOP_K}&mode=hybrid" --connect-timeout 3
```
- 서버 미기동/미설치 → 조용히 Tier 2로. (같은 플러그인의 `/tofugraph` 명령으로 GraphRAG 스택을 구축하면 이 티어가 자동으로 살아난다.)

### Tier 2 — Obsidian CLI (전문 full-text 검색)
```bash
# km-config의 obsidianCli.path 우선, 비어 있으면 자동 감지:
#   mac:     /Applications/Obsidian.app/Contents/MacOS/obsidian-cli
#   wsl:     /mnt/c/Program Files/Obsidian/Obsidian.com
#   windows: C:\Program Files\Obsidian\Obsidian.com
"$OBSIDIAN_CLI" search query="${QUERY}" format=json limit=1000
```
- 전제: Obsidian 데스크톱 앱 설치 + 실행 중 (setup 위저드가 감지·안내).
- CLI는 관련도 순위가 약하므로 흔한 단어는 limit을 크게 잡고 결과에서 추린다.
- CLI 부재·실행 오류 → Tier 3로.

### Tier 3 — Obsidian MCP (연결된 경우)
연결된 Obsidian MCP의 검색 도구를 사용한다(서버 구현마다 도구명이 다르다 — 예: `simple_search`, `obsidian_simple_search`). MCP 서버 미연결 → Tier 4로.
- Codex CLI 등 Obsidian MCP를 붙이지 않은 환경에서는 이 티어가 보통 비어 있다 — 그대로 Tier 4로 넘어가면 된다(폴백 설계상 정상 경로).

### Tier 4 — 텍스트 검색 (비상 폴백, 항상 가능)
```bash
grep -rn "${QUERY}" "${VAULT_PATH}" --include="*.md" -l | head -20
```
- 문장형 질의는 통짜로 넣지 말고 **핵심 키워드 1~2개를 추출해** 검색한다(통짜 문장은 0히트).
- 이 티어를 쓴 경우 답변에 **"의미 검색 엔진 미설치로 텍스트 검색 결과입니다"** 를 명시한다.

### 모드별 파라미터
- **QUICK**: top_k=5, 노트 읽기 1-2개
- **DEEP**: top_k=10, 노트 읽기 3-5개

## QUICK 모드 — 즉답 (3-5줄)

상위 1-2개 노트만 Read (`${VAULT_PATH}/{note_path}`) → frontmatter + 핵심 섹션 추출.

```
**답변:**
[3~5줄 직접 답변. 노트 내용 기반.]

📌 **상위 MOC** (N)
1. **[[MOC 제목]]** — [범위·역할 한 줄] (`경로`)

📄 **원자 노트** (N)
1. **[노트 제목]** — [핵심 한 줄] (`경로`)
```

## DEEP 모드 — 상세 분석

상위 3-5개 노트를 실제 Read → 제목·요약·핵심 섹션 추출 → 종합하여 질문에 직접 답변(목록·표·단계 활용).

```
## {질문 요약}

{답변 본문. 구조화된 분석.}

### 📌 상위 MOC (진입점)
1. [[MOC1]] — {범위·역할 1줄} (`경로`)

### 📄 원자 노트 (출처)
1. [[노트1]] — {핵심 정보 1줄} (`경로`)
```

## 제약

- **읽기 전용**: 노트 생성/수정 금지
- **hallucination 금지**: 반드시 실제 노트 내용 기반. 노트에 없는 내용은 "vault에 관련 자료가 없습니다" 명시
- **출처 필수**: 실제 읽은 노트 경로 표기
- **사용 티어 명시**: 답변 끝에 어느 티어로 검색했는지 1줄 (예: "검색: Obsidian CLI")
- **질문/스킬/에이전트 스폰 금지**: 직접 검색만 수행
- 상태 메시지 없이 바로 결과 출력 · Read 실패 시 다음 노트로
- QUICK: 5줄 이내 + 출처 1-2개 / DEEP: 제한 없음 + 출처 3-5개

### 결과 없음
```
vault에서 "{query}" 관련 자료를 찾지 못했습니다.
knowledge-manager로 자료를 수집해보세요.
```
