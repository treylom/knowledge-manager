---
description: 지식 관리 에이전트 (Agent Teams) - 풀스케일 병렬 처리 (Category Lead + RALPH + DA)
allowedTools: Task, Read, Write, Bash, Glob, Grep, mcp__obsidian__*, mcp__notion__*, mcp__playwright__*, mcp__hyperbrowser__*, WebFetch, AskUserQuestion, TeamCreate, TeamDelete, TaskCreate, TaskUpdate, TaskList, TaskGet, SendMessage
---

# Knowledge Manager - Agent Teams 호출

> **이 명령어는 풀스케일 Agent Teams(9명)를 자동 구성합니다.**
> 단일 에이전트 버전: `/knowledge-manager` (Agent Teams 미지원 환경용)
> 에이전트 정의: `.claude/agents/knowledge-manager-at.md` 참조
> 공유 사양: `.claude/agents/knowledge-manager.md` 참조

---

## 팀 아키텍처 요약

```
Lead (Main) - Opus 1M
 +-- vault-intel-lead (Sonnet 1M) — Category Lead
 |    +-- @graph-navigator (Sonnet, Explore)
 |    +-- @retrieval-specialist (Sonnet, Explore)
 |    +-- @link-curator (Haiku, Explore)
 +-- content-proc-lead (Sonnet 1M) — Category Lead
 |    +-- @content-extractor (Sonnet, general-purpose)
 |    +-- @deep-reader (Sonnet, Explore)
 |    +-- @content-analyzer (Sonnet, general-purpose)
 +-- @devils-advocate (Sonnet 4.6) — DA
```

---

## STEP 0: 환경 확인 (가장 먼저 실행!)

**환경 확인 후 Agent Office URL을 사용자에게 항상 표시합니다.**

### 0-0. Agent Office 대시보드 부트스트랩 (간소화 — ensure-server.sh)

**단일 스크립트로 서버 확인 + 자동 시작을 처리합니다.**

```
# === Agent Office 경로 감지 (2단계) ===
1. Glob("**/agent-office/ensure-server.sh") → 찾으면 agent_office_path = dirname 결과
2. Glob("agent-office/server.js") → 찾으면 agent_office_path = "agent-office"
3. 모두 실패 → agent_office_path = null

# === 대시보드 자동 실행 (한 줄 — CRITICAL) ===

IF agent_office_path != null:
  Bash("bash {agent_office_path}/ensure-server.sh $(pwd)")
  dashboard_available = (exit code == 0)

  # 브라우저 자동 오픈 (WSL 환경 대응)
  Bash("cmd.exe /c start http://localhost:3747 2>/dev/null || open http://localhost:3747 2>/dev/null || xdg-open http://localhost:3747 2>/dev/null || true")

  # URL 항상 표시 (자동 오픈 성공 여부 무관 — CRITICAL)
  "Agent Office 대시보드: http://localhost:3747"

  # WSL/tmux 환경 수동 접근 안내
  IF env_platform == "wsl":
    "tmux 세션에서 브라우저가 자동으로 열리지 않을 수 있습니다."
    "Windows 브라우저에서 직접 http://localhost:3747 을 열어주세요."

ELSE:
  dashboard_available = false
  "Agent Office 미설치. 대시보드 없이 진행."
```

### 0-1. .team-os/ 인프라 확인 (크로스 플랫폼)

```
# Step 1: 프로젝트 루트 절대 경로 획득
Bash("pwd") → {project_root}

# Step 2: 절대 경로로 Glob (WSL 상대 경로 실패 방지)
Glob("{project_root}/.team-os/registry.yaml") → 존재하면 Team OS 활성화
Glob("{project_root}/.team-os/spawn-prompts/*.md") → Spawn Prompt 사용 가능 여부

# Step 3: Glob 빈 결과 시 Bash 폴백
Bash("ls -la .team-os/registry.yaml 2>/dev/null && echo EXISTS || echo NOT_FOUND")
Bash("ls .team-os/spawn-prompts/*.md 2>/dev/null | wc -l")
```

### 0-2. Obsidian 환경 확인 (3-Tier)

```bash
OBSIDIAN_CLI="/mnt/c/Program Files/Obsidian/Obsidian.com"

# Tier 1: CLI 확인 (우선)
"$OBSIDIAN_CLI" version 2>/dev/null
→ 응답 있으면: obsidian_method = "cli"

# Tier 2: CLI 실패 시 MCP 확인
mcp__obsidian__list_notes({}) → 응답 여부
→ 응답 있으면: obsidian_method = "mcp"

# Tier 3: 둘 다 실패 → obsidian_method = "filesystem"
```

> 팀원 에이전트 스폰 시 `obsidian_method` 값을 컨텍스트로 전달

### 0-3. tmux 확인

```
Bash("which tmux && echo AVAILABLE || echo NOT_FOUND")

tmux 없으면:
  → 사용자에게 안내: "Agent Teams는 tmux가 필요합니다. /knowledge-manager (단일 에이전트 버전)을 사용해주세요."
  → 중단
```

---

## STEP 0.5: 모드 감지 (Mode Detection)

**STEP 1 진행 전에 사용자 요청을 분석하여 모드를 결정합니다.**

| 사용자 표현 | 모드 |
|------------|------|
| URL, "정리해줘", "분석해줘", 외부 콘텐츠 | **Mode I** (Content Ingestion) — 기존 워크플로우 |
| "아카이브 정리", "카테고리 재편", "일괄 링크", "대규모 재편" | **Mode R** (Archive Reorganization) |
| 기존 vault 폴더 50+ 파일 지칭 | **Mode R 제안** (사용자에게 확인) |

### Mode R 팀 아키텍처 (AT 버전)

```
Mode R Team:
Lead (Opus) — 전체 조율 + 모든 파일 쓰기 (Python 배치 직접 실행)
├── analyst-1..N (Sonnet, Explore) — Phase R1 병렬 분석
│   - 파일 수에 따라 2-5개 스폰
│   - Progressive Reading (frontmatter + 첫 5줄)
│   - 산출물: topic_clusters, series, reply_chains, hubs, cross_links
├── @devils-advocate (Sonnet) — Phase R2/R3 규칙 검증
│   - CATEGORY_DESIGN.md 검증
│   - {TARGET}_RULES.md 검증
│   - CONCERN → 수정 → ACCEPTABLE (최대 3회)
└── [쓰기 워커 없음 — Lead가 Python으로 직접 실행]
    - CRITICAL: worktree 버그로 팀원 쓰기 위임 금지
    - Lead가 apply_footers.py, update_mocs.py 등 직접 생성+실행
```

### Mode R 감지 시 분기

```
Mode R 선택 시:
→ km-archive-reorganization.md 스킬의 Phase R0-R5 실행
→ 아래 STEP 1-6 (Mode I) 대신 Mode R 워크플로우
→ 팀 구성: analyst-1..N + DA (쓰기 워커 없음)

Mode R 추가 질문: 대상 폴더, 재편 범위, auto-commit 여부
(상세: km-archive-reorganization.md 사전 질문 섹션 참조)
```

**Mode I 선택 시** → 아래 STEP 1부터 기존 워크플로우 계속.

---

## STEP 1: 사용자 선호도 확인 (필수!)

**콘텐츠 처리/읽기 전에 반드시 AskUserQuestion을 호출하세요!**
**4개 질문을 한 번의 호출로 모두 물어봅니다!**

```json
AskUserQuestion({
  "questions": [
    {
      "question": "콘텐츠를 얼마나 상세하게 정리할까요?",
      "header": "상세 수준",
      "options": [
        {"label": "요약 (1-2p)", "description": "핵심만 간략히"},
        {"label": "보통 (3-5p)", "description": "주요 내용 + 약간의 설명"},
        {"label": "상세 (5p+) (권장)", "description": "모든 내용을 꼼꼼히"}
      ],
      "multiSelect": false
    },
    {
      "question": "어떤 영역에 중점을 둘까요?",
      "header": "중점 영역",
      "options": [
        {"label": "전체 균형 (권장)", "description": "모든 영역을 균형있게"},
        {"label": "개념/이론", "description": "핵심 아이디어와 원리"},
        {"label": "실용/활용", "description": "사용법, 예시, 튜토리얼"},
        {"label": "기술/코드", "description": "구현, 아키텍처, 코드"}
      ],
      "multiSelect": false
    },
    {
      "question": "노트를 어떻게 분할할까요?",
      "header": "노트 분할",
      "options": [
        {"label": "단일 노트", "description": "모든 내용을 하나의 노트에"},
        {"label": "주제별 분할", "description": "주요 주제마다 별도 노트 (MOC 포함)"},
        {"label": "원자적 분할", "description": "최대한 작은 단위로 분할 (Zettelkasten)"},
        {"label": "3-tier 계층 (권장)", "description": "메인MOC + 카테고리MOC + 원자노트"}
      ],
      "multiSelect": false
    },
    {
      "question": "기존 노트와 얼마나 연결할까요?",
      "header": "연결 수준",
      "options": [
        {"label": "최소", "description": "태그만 추가"},
        {"label": "보통", "description": "태그 + 관련 노트 링크 제안"},
        {"label": "최대 (권장)", "description": "태그 + 링크 + 기존 노트와 자동 연결 탐색"}
      ],
      "multiSelect": false
    }
  ]
})
```

> AT 버전에서는 RALPH가 항상 ON (max 5회), DA가 항상 ON입니다.
> 별도 질문 없이 자동 적용됩니다.

### 퀵 프리셋 (사용자 키워드 감지 시 질문 스킵)

| 사용자 표현 | 프리셋 | 질문 스킵 |
|------------|--------|----------|
| "빠르게", "간단히" | 요약, 전체균형, 단일노트, 최소 | O |
| "꼼꼼히", "자세히" | 상세, 전체균형, 원자적분할, 최대 | O |
| "기본으로", "기본" | 상세, 전체균형, 3-tier, 최대 | O |
| 키워드 없음 | - | X (질문 필수) |

---

## STEP 1.5A: 이미지/그래프 추출 여부 확인 (선택!)

소스에 이미지/차트/그래프가 포함될 수 있는 경우 사용자에게 확인합니다:

```json
AskUserQuestion({
  "questions": [
    {
      "question": "소스의 이미지/차트/그래프도 함께 추출하여 노트에 첨부할까요?",
      "header": "이미지 추출",
      "options": [
        {"label": "아니오 (기본)", "description": "텍스트만 추출 (빠름, 가벼움)"},
        {"label": "예 (권장)", "description": "이미지/차트/그래프도 추출하여 Obsidian 노트에 임베딩 + Notion에 삽입"}
      ],
      "multiSelect": false
    }
  ]
})
```

**"예" 선택 시:**
- `image_extraction_enabled = true`
- content-extractor에게 Image Catalog 생성 지시 추가
- Phase 5.25 (이미지 저장 및 임베딩) 활성화
- 참조 스킬: `km-image-pipeline.md`

**"아니오" 선택 시 (기본):**
- `image_extraction_enabled = false`
- 기존 텍스트 전용 파이프라인 유지
- Phase 5.25 스킵

### 퀵 프리셋 확장

| 사용자 표현 | 이미지 추출 | 질문 스킵 |
|------------|-----------|----------|
| "이미지도", "차트 포함", "그래프 포함" | true | O |
| "빠르게", "간단히", "텍스트만" | false | O |
| 키워드 없음 | - | X (질문 필수) |

---

## STEP 1.5B: PDF 처리 방식 확인 (PDF인 경우만!)

PDF 파일이 입력된 경우에만 이 질문을 합니다:

```json
AskUserQuestion({
  "questions": [
    {
      "question": "대용량 PDF입니까? /pdf 스킬로 처리하시겠습니까?",
      "header": "PDF 처리",
      "options": [
        {"label": "아니오 (기본)", "description": "Read로 직접 읽기 시도"},
        {"label": "예", "description": "/pdf 스킬로 전체 변환 후 처리"}
      ],
      "multiSelect": false
    }
  ]
})
```

---

## STEP 2: 팀 구성 + 공유 메모리 초기화

### 2-1. 팀 생성

```
TeamCreate({
  team_name: "km-at-{주제키워드}",
  description: "{사용자 요청 요약} - Agent Teams 풀스케일",
  agent_type: "knowledge-manager-at-lead"
})
```

### 2-2. 공유 메모리 초기화 (계층 + Steps 포함)

```
# 세션별 파일 초기화 (MEMORY.md는 유지!)

# TEAM_PLAN.md — Steps 테이블 + Hierarchy 포함 (Agent Office 계층 그래프 렌더링용)
Write(".team-os/artifacts/TEAM_PLAN.md", """
# TEAM_PLAN

## Topic: {주제}
## Complexity: AT Full-Scale
## Team Size: 9

## Team
| # | name | role | model | Status |
|---|------|------|-------|--------|
| 1 | Lead | 총괄 오케스트레이션 (Main Lead) | opus | active |
| 2 | vault-intel-lead | Vault Intelligence Category Lead | sonnet | pending |
| 3 | content-proc-lead | Content Processing Category Lead | sonnet | pending |
| 4 | @graph-navigator | Wikilink 그래프 탐색 | sonnet | pending |
| 5 | @retrieval-specialist | 키워드+태그 검색 | sonnet | pending |
| 6 | @link-curator | 양방향 링크 추천 | haiku | pending |
| 7 | @content-extractor | 소스 콘텐츠 추출 | sonnet | pending |
| 8 | @deep-reader | Hub 노트 정독 + 교차 분석 | sonnet | pending |
| 9 | @content-analyzer | 노트 구조 설계 + 태그 추천 | sonnet | pending |
| 10 | @devils-advocate | 반론 + 교차 검증 | sonnet | pending |

## Hierarchy
| parent | children |
|--------|----------|
| Lead | vault-intel-lead, content-proc-lead, @devils-advocate |
| vault-intel-lead | @graph-navigator, @retrieval-specialist, @link-curator |
| content-proc-lead | @content-extractor, @deep-reader, @content-analyzer |

## Steps
| # | Step | Assignee | Dependency | Status |
|---|------|----------|------------|--------|
| S1 | 소스 콘텐츠 추출 | @content-extractor | - | pending |
| S2 | Wikilink 그래프 탐색 | @graph-navigator | - | pending |
| S3 | 키워드+태그 넓은 검색 | @retrieval-specialist | - | pending |
| S4 | Hub 노트 정독 + 교차 분석 | @deep-reader | S2 | pending |
| S5 | 양방향 링크 후보 추천 | @link-curator | S2 | pending |
| S6 | Vault Intelligence 통합 | vault-intel-lead | S2,S3,S5 | pending |
| S7 | Content Processing 통합 | content-proc-lead | S1,S4 | pending |
| S8 | 노트 구조 설계 + 태그 추천 | @content-analyzer | S1 | pending |
| S9 | 최종 반론 + 교차 검증 | @devils-advocate | S6,S7,S8 | pending |

## Quality Targets
| Metric | Target | Measure |
|--------|--------|---------|
| Hub 노트 발견 | 최소 2개 | Graph ∩ Retrieval 교차 확인 |
| 교차 검증 핵심 노트 | 최소 3개 | 2개+ 소스에서 확인 |
| 연결 후보 | 최소 5개 | 양방향 링크 가능 |
| 원문 추출 커버리지 | 90%+ | 주요 섹션 기준 |
| 이미지 추출 (활성 시) | 주요 차트/그래프 90%+ | Image Catalog 기준 |
| RALPH SHIP 기준 | 4개 차원 모두 충족 | vault/content 기준별 |
| DA ACCEPTABLE 기준 | 워커 간 일관성 + 커버리지 누락 없음 | 종합 검토 |
""")

Write(".team-os/artifacts/TEAM_BULLETIN.md", "# TEAM_BULLETIN\n\n## Updates\n\n(팀원 발견사항이 여기에 추가됩니다)\n")
Write(".team-os/artifacts/TEAM_PROGRESS.md", """
# TEAM_PROGRESS

## Status Board

| Agent | Task | Progress | Updated | Note |
|-------|------|----------|---------|------|
| Lead | 팀 구성 중 | 5% | {timestamp} | active |
| vault-intel-lead | | 0% | {timestamp} | pending |
| content-proc-lead | | 0% | {timestamp} | pending |
| @graph-navigator | | 0% | {timestamp} | pending |
| @retrieval-specialist | | 0% | {timestamp} | pending |
| @link-curator | | 0% | {timestamp} | pending |
| @content-extractor | | 0% | {timestamp} | pending |
| @deep-reader | | 0% | {timestamp} | pending |
| @content-analyzer | | 0% | {timestamp} | pending |
| @devils-advocate | | 0% | {timestamp} | pending |

## Checkpoints

| # | Name | Condition | Done |
|---|------|-----------|------|
| 1 | All workers spawned | 모든 워커 Task 생성 완료 | [ ] |
| 2 | All workers completed | 모든 워커 결과 수신 | [ ] |
| 3 | Artifacts generated | 최종 산출물 생성 | [ ] |
""")
Write(".team-os/artifacts/TEAM_FINDINGS.md", "# TEAM_FINDINGS\n\n## Session: {주제}\n\n(교차 검증 결과가 여기에 기록됩니다)\n")

# MEMORY.md에서 이전 세션 교훈 읽기
Read(".team-os/artifacts/MEMORY.md") → 관련 Lessons Learned 확인
```

### 2-3. 태스크 생성 (TaskCreate)

```
# Category Leads
TaskCreate("vault-intel-lead: Vault Intelligence 조율 - graph/retrieval/link 워커 관리")
TaskCreate("content-proc-lead: Content Processing 조율 - extractor/reader/analyzer 워커 관리")

# Vault Intelligence Workers
TaskCreate("graph-navigator: Wikilink 2-hop 그래프 탐색 - Hub 노트 식별")
TaskCreate("retrieval-specialist: 키워드+태그 넓은 검색 - TOP 20 정리")
TaskCreate("link-curator: 양방향 링크 후보 추천", blockedBy: [graph-navigator task ID])

# Content Processing Workers
TaskCreate("content-extractor: 소스 콘텐츠 추출")
TaskCreate("deep-reader: Hub 노트 깊이 읽기 + 교차 분석")
TaskCreate("content-analyzer: 노트 구조 설계 + 태그 추천")

# Devil's Advocate
TaskCreate("devils-advocate: 최종 결과 반론 + 교차 검증")
```

### 2-4. Agent Office 능동 대시보드 연동 (CRITICAL — 실시간 Push)

**원칙: 모든 상태 전환에서 curl API push + TEAM_PROGRESS.md + TEAM_BULLETIN.md 3중 업데이트 수행.**

> 파일 watcher만으로는 15초 폴링 지연이 발생합니다.
> curl API push를 함께 사용하면 SSE로 실시간 반영됩니다.

```
IF dashboard_available:
  # 팀 생성 직후 초기 progress push (Lead: 5%, "팀 구성 중")
  Bash("curl -s -X POST http://localhost:3747/api/progress -H 'Content-Type: application/json' -d '{\"agent\":\"Lead\",\"progress\":5,\"task\":\"팀 구성 중\",\"note\":\"active\"}' --connect-timeout 2 || true")

  # TEAM_BULLETIN.md 초기 기록
  TEAM_BULLETIN.md에 Append:
    ## [{timestamp}] - Lead
    **Task**: Team created
    **Findings**: KM-AT 풀스케일 팀 ({주제}) 생성 완료. 9명 스폰 대기.
    **Status**: active

ELSE:
  # dashboard_available = false → curl 호출 생략, 파일 업데이트만 수행
  "Agent Office 미실행. 파일 기반 진행률만 기록."
```

> **진행률 갱신 규칙 (8레벨 스케일 — CRITICAL for Agent Office 실시간 반영)**:
> - 5%(created) → 10%(spawned) → 20%(first_message) → 30-70%(active, 작업 비례) → 80%(results_sent / SHIP) → 90%(DA review) → 95%(shutdown) → 100%(team_deleted)
> - Explore 워커: 10%(spawned) → 25→50→75%(active) → 80%(results_sent) → 95%(shutdown) → 100%(team_deleted)
> - Done(100%)은 TeamDelete 후에만 표시. 80-99%는 "Wrapping up"으로 표시.
> - 최소 2분마다 1회 갱신 (Agent Office 15초 폴링 + SSE로 실시간 반영)

---

## STEP 3: 팀원 스폰 (병렬!)

**반드시 하나의 메시지에서 모든 Task를 병렬로 호출하세요!**

> Spawn Prompt 로드: `.team-os/spawn-prompts/{role}.md`를 Read로 읽어서 프롬프트에 포함.
> `{{TOPIC}}`, `{{REPORT_TO}}`, `{{PREFERENCES}}` 등 변수를 실제 값으로 치환.

### 3-0. progress_update_rule 주입 확인 (CRITICAL)

각 spawn prompt에 `<progress_update_rule>` 섹션이 포함되어야 합니다.
- **general-purpose 워커** (content-extractor, content-analyzer): curl 기반 직접 push
- **Category Lead** (vault-intel-lead, content-proc-lead): curl 직접 push + Explore 워커 진행률 중계
- **Explore 워커** (graph-navigator, retrieval-specialist, link-curator, deep-reader): SendMessage 기반 보고 (Bash 불가)
- **DA** (devils-advocate): curl 기반 직접 push (아래 inline prompt에 포함)

spawn prompt 파일에 `<progress_update_rule>`이 이미 포함되어 있으므로 별도 주입 불필요.
단, 변수 치환 시 `{{REPORT_TO}}`가 정확히 치환되었는지 확인.

```
# 9명 동시 호출 (하나의 메시지에 모든 Task 포함):

# === Category Lead: Vault Intelligence ===
Task(@vault-intel-lead):
  subagent_type: "general-purpose"
  model: "sonnet"
  team_name: "km-at-{주제키워드}"
  name: "vault-intel-lead"
  run_in_background: true
  prompt: |
    [.team-os/spawn-prompts/vault-intel-lead.md 내용]
    ({{REPORT_TO}} = 'Lead', {{TOPIC}} = '{주제}', {{TOPIC_KEYWORD}} = '{키워드}')

# === Category Lead: Content Processing ===
Task(@content-proc-lead):
  subagent_type: "general-purpose"
  model: "sonnet"
  team_name: "km-at-{주제키워드}"
  name: "content-proc-lead"
  run_in_background: true
  prompt: |
    [.team-os/spawn-prompts/content-proc-lead.md 내용]
    ({{REPORT_TO}} = 'Lead', {{TOPIC}} = '{주제}', {{SOURCE_URL}} = '{URL}', {{PREFERENCES}} = '{선호도}')

# === Vault Intelligence Workers ===
Task(@graph-navigator):
  subagent_type: "Explore"
  model: "sonnet"
  team_name: "km-at-{주제키워드}"
  name: "graph-navigator"
  run_in_background: true
  prompt: |
    [.team-os/spawn-prompts/graph-navigator.md 내용]
    ({{REPORT_TO}} = 'vault-intel-lead', {{TOPIC}} = '{주제}', {{TOPIC_KEYWORD}} = '{키워드}')

Task(@retrieval-specialist):
  subagent_type: "Explore"
  model: "sonnet"
  team_name: "km-at-{주제키워드}"
  name: "retrieval-specialist"
  run_in_background: true
  prompt: |
    [.team-os/spawn-prompts/retrieval-specialist.md 내용]
    ({{REPORT_TO}} = 'vault-intel-lead', {{TOPIC}} = '{주제}')

Task(@link-curator):
  subagent_type: "Explore"
  model: "haiku"
  team_name: "km-at-{주제키워드}"
  name: "link-curator"
  run_in_background: true
  prompt: |
    [.team-os/spawn-prompts/link-curator.md 내용]
    ({{REPORT_TO}} = 'vault-intel-lead', {{TOPIC}} = '{주제}', {{NEW_NOTES}} = '생성 예정 노트 목록')

# === Content Processing Workers ===
Task(@content-extractor):
  subagent_type: "general-purpose"
  model: "sonnet"
  team_name: "km-at-{주제키워드}"
  name: "content-extractor"
  run_in_background: true
  prompt: |
    [.team-os/spawn-prompts/content-extractor.md 내용]
    ({{REPORT_TO}} = 'content-proc-lead', {{SOURCE_URL}} = '{URL}', {{SOURCE_TYPE}} = '{type}', {{TOPIC}} = '{주제}')

Task(@deep-reader):
  subagent_type: "Explore"
  model: "sonnet"
  team_name: "km-at-{주제키워드}"
  name: "deep-reader"
  run_in_background: true
  prompt: |
    [.team-os/spawn-prompts/deep-reader.md 내용]
    ({{REPORT_TO}} = 'content-proc-lead', {{TOPIC}} = '{주제}', {{HUB_NOTES}} = 'graph-navigator가 식별 예정')

Task(@content-analyzer):
  subagent_type: "general-purpose"
  model: "sonnet"
  team_name: "km-at-{주제키워드}"
  name: "content-analyzer"
  run_in_background: true
  prompt: |
    [.team-os/spawn-prompts/content-analyzer.md 내용]
    ({{REPORT_TO}} = 'content-proc-lead', {{TOPIC}} = '{주제}', {{PREFERENCES}} = '{사용자선호}')

# === Devil's Advocate ===
Task(@devils-advocate):
  subagent_type: "general-purpose"
  model: "sonnet"
  team_name: "km-at-{주제키워드}"
  name: "devils-advocate"
  run_in_background: true
  prompt: |
    당신은 Devil's Advocate입니다. km-at-{주제키워드} 팀의 DA로서,
    Lead의 최종 결과에 대해 반론을 제기합니다.
    Lead가 결과를 보내면 다음을 검토하세요:
    1. 누락된 관점/정보
    2. 편향된 해석
    3. 불완전한 연결
    4. 대안적 구조 제안
    평소에는 대기합니다. Lead가 메시지를 보내면 활동합니다.

    <progress_update_rule>
    작업 시작 시:
    Bash("curl -s -X POST http://localhost:3747/api/progress -H 'Content-Type: application/json' -d '{\"agent\":\"@devils-advocate\",\"progress\":10,\"task\":\"대기 중\"}'")
    검토 시작 시: progress=30, 검토 중 50, 반론 작성 80, 완료 100
    curl 실패해도 무시.
    </progress_update_rule>
```

### 3-1. 스폰 후 초기 진행 업데이트 (대시보드 연동 — tofu-at STEP 7-4-2 패턴)

**모든 Task 스폰 직후, 대시보드에 실행 상태를 반영합니다.**

```
# 모든 Task 스폰 직후:
FOR each spawned_role in [vault-intel-lead, content-proc-lead, graph-navigator, retrieval-specialist, link-curator, content-extractor, deep-reader, content-analyzer, devils-advocate]:
  TEAM_PROGRESS.md의 해당 Agent 행 업데이트:
    Progress: 0% → 10%
    Note: pending → spawned
    Updated: {current_timestamp}

  IF dashboard_available:
    Bash("curl -s -X POST http://localhost:3747/api/progress -H 'Content-Type: application/json' -d '{\"agent\":\"{spawned_role}\",\"progress\":10,\"task\":\"초기화 중\",\"note\":\"spawned\"}' --connect-timeout 2 || true")

# Lead Progress 업데이트: 5% → 10%
TEAM_PROGRESS.md: Lead → Progress: 10%, Note: spawning complete
IF dashboard_available:
  Bash("curl -s -X POST http://localhost:3747/api/progress -H 'Content-Type: application/json' -d '{\"agent\":\"Lead\",\"progress\":10,\"task\":\"팀 스폰 완료\",\"note\":\"spawning complete\"}' --connect-timeout 2 || true")

# Checkpoint 1 업데이트:
TEAM_PROGRESS.md의 Checkpoints:
  | 1 | All workers spawned | 모든 워커 Task 생성 완료 | [x] |

# TEAM_BULLETIN.md에 Append:
  ## [{timestamp}] - Lead
  **Task**: Team spawn complete
  **Findings**: 9명 워커 스폰 완료: vault-intel-lead, content-proc-lead, graph-navigator, retrieval-specialist, link-curator, content-extractor, deep-reader, content-analyzer, devils-advocate
  **Status**: active
```

### 3-4. 사용자 알림

팀 구성 후 사용자에게 표시:

```
Knowledge Manager AT가 풀스케일 Agent Teams 모드로 실행됩니다.

| 계층 | 팀원 | 역할 | 모델 | 상태 |
|------|------|------|------|------|
| Lead | Main | 총괄 오케스트레이션 | Opus 1M | 실행 중 |
| Cat.Lead | vault-intel-lead | Vault 탐색 조율 | Sonnet 1M | 실행 중 |
| Cat.Lead | content-proc-lead | 콘텐츠 처리 조율 | Sonnet 1M | 실행 중 |
| Worker | @graph-navigator | Wikilink 그래프 탐색 | Sonnet | 실행 중 |
| Worker | @retrieval-specialist | 키워드+태그 검색 | Sonnet | 실행 중 |
| Worker | @content-extractor | 소스 콘텐츠 추출 | Sonnet | 실행 중 |
| Worker | @deep-reader | 핵심 노트 정독 | Sonnet | 실행 중 |
| Worker | @content-analyzer | 노트 구조 설계 | Sonnet | 실행 중 |
| Worker | @link-curator | 연결 후보 추천 | Haiku | 대기 중 |
| DA | @devils-advocate | 결과 반론 검증 | Sonnet | 대기 중 |

RALPH Loop: ON (최대 5회) | DA: ON
팀원들이 병렬 처리 중입니다. Category Lead가 결과를 통합하여 보고합니다.
```

---

## STEP 4: 결과 수집 + RALPH + DA (대시보드 실시간 갱신 포함)

### Phase 1: Category Lead 결과 수신 (Health Check 루프 강화 — tofu-at STEP 7-5.5)

```
# Category Lead들이 워커 결과를 통합하여 SendMessage로 보고
# 대기: vault-intel-lead + content-proc-lead 모두 보고할 때까지

WHILE (미완료 Category Lead 존재):
  # TEAM_PROGRESS.md에서 각 에이전트의 마지막 업데이트 시간 확인
  FOR each active_lead in [vault-intel-lead, content-proc-lead]:
    last_update = TEAM_PROGRESS.md에서 해당 Agent의 Updated 열 파싱
    elapsed = current_time - last_update

    IF elapsed > 5분:
      # 1차: 상태 확인 메시지 전송
      SendMessage(
        recipient: "{active_lead}",
        content: "상태 확인: 마지막 업데이트로부터 5분 경과. 현재 진행 상황을 보고해주세요.",
        summary: "Health check for {active_lead}"
      )

      # 2차 (10분 경과 시): 셧다운 + 교체 판단
      IF elapsed > 10분 AND 이미 상태 확인 메시지 전송 완료:
        → SendMessage(type: "shutdown_request", recipient: "{active_lead}")
        → 새 에이전트 스폰 (같은 이름 재사용 금지! e.g., vault-intel-lead-2)
        → TEAM_BULLETIN.md에 기록: "Agent {active_lead} replaced due to inactivity"
        → TEAM_PROGRESS.md: 해당 Agent Note → "replaced (inactivity)"

  WAIT  # 메시지 자동 수신 대기
```

### Phase 2: RALPH Loop (자동, 최대 5회 — 대시보드 3중 업데이트)

```
FOR iteration IN 1..5:
  vault_intel_result = vault-intel-lead 보고서
  content_proc_result = content-proc-lead 보고서

  # 평가 기준
  vault_criteria:
    - Hub 노트 >= 2개
    - 교차 검증 핵심 노트 >= 3개
    - 연결 후보 >= 5개

  content_criteria:
    - 원문 주요 섹션 90%+ 추출
    - 교차 분석 항목 >= 3개
    - 노트 구조 제안 포함
    - 태그 추천 >= 5개

  IF vault_intel 충족:
    # === SHIP 판정: 3중 업데이트 ===
    TEAM_PROGRESS.md: vault-intel-lead → Progress: 80%, Note: SHIP (DA 리뷰 대기)
    IF dashboard_available:
      Bash("curl -s -X POST http://localhost:3747/api/progress -H 'Content-Type: application/json' -d '{\"agent\":\"vault-intel-lead\",\"progress\":80,\"task\":\"SHIP - DA 리뷰 대기\",\"note\":\"awaiting DA comprehensive review\"}' --connect-timeout 2 || true")
    TEAM_BULLETIN.md에 Append:
      ## [{timestamp}] - vault-intel-lead
      **Task**: Vault Intelligence 통합
      **Findings**: {결과 요약 1-2줄}
      **Status**: SHIP (DA 리뷰 대기)

    SendMessage(recipient: "vault-intel-lead", content: "SHIP 판정. DA 종합 리뷰 대기 중입니다.", summary: "SHIP - awaiting DA review")

  ELSE:
    # === REVISE 판정: 3중 업데이트 ===
    TEAM_PROGRESS.md: vault-intel-lead → Progress: 50%, Note: REVISE #{iteration}
    IF dashboard_available:
      Bash("curl -s -X POST http://localhost:3747/api/progress -H 'Content-Type: application/json' -d '{\"agent\":\"vault-intel-lead\",\"progress\":50,\"task\":\"REVISE\",\"note\":\"iteration #{iteration}\"}' --connect-timeout 2 || true")
    TEAM_BULLETIN.md에 Append:
      ## [{timestamp}] - Lead (RALPH)
      **Iteration**: {iteration}/5
      **Target**: vault-intel-lead
      **Feedback**: {구체적 부족 항목}
      **Status**: retry

    SendMessage({
      type: "message",
      recipient: "vault-intel-lead",
      content: "REVISE #{iteration}: {구체적 부족 항목}. 추가 탐색 요청.",
      summary: "RALPH: Vault Intel 보완 요청"
    })
    → 보완 결과 대기

  # content-proc-lead에 대해서도 동일한 SHIP/REVISE 3중 업데이트 패턴 적용
  # (위 vault-intel-lead 패턴을 content-proc-lead로 변경하여 반복)

  IF 모두 SHIP:
    BREAK → Phase 3으로
```

### Phase 3: DA 종합 리뷰 (2-Phase Review — tofu-at STEP 7-6.5 패턴)

**모든 Category Lead 결과 수집 완료 후, DA에게 전체 결과를 종합 검토하도록 요청합니다.**

```
# PRECONDITION: 모든 Category Lead 결과 수집 완료 (각 lead progress == 80%)

# Phase 3-A: DA에게 전체 결과 종합 검토 요청
all_results_summary = vault_intel_report + content_proc_report 종합 1페이지 요약
SendMessage(
  recipient: "devils-advocate",
  content: "전체 결과를 종합 검토해주세요:\n\n{all_results_summary}\n\n검토 관점:\n1. Category Lead 간 결과 일관성\n2. 전체 커버리지 누락 여부\n3. 교차 검증 불일치\n4. 종합 recommendation: ACCEPTABLE 또는 CONCERN + 재작업 대상",
  summary: "DA comprehensive review request"
)

# DA 응답 수신
da_review = DA 메시지 자동 수신
da_iteration = 0

# Phase 3-B: DA 판정 처리
IF da_review.recommendation == "ACCEPTABLE":
  # 모든 워커/리드 100%로 업데이트
  FOR each agent in [vault-intel-lead, content-proc-lead, graph-navigator, retrieval-specialist, link-curator, content-extractor, deep-reader, content-analyzer]:
    TEAM_PROGRESS.md: Progress → 100%, Note → completed (DA ACCEPTABLE)
    IF dashboard_available:
      Bash("curl -s -X POST http://localhost:3747/api/progress -H 'Content-Type: application/json' -d '{\"agent\":\"{agent}\",\"progress\":100,\"task\":\"completed\",\"note\":\"DA ACCEPTABLE\"}' --connect-timeout 2 || true")

  # Checkpoint 2 업데이트
  TEAM_PROGRESS.md: | 2 | All workers completed | 모든 워커 결과 수신 | [x] |
  → Phase 4로

ELIF da_review.recommendation == "CONCERN":
  da_iteration += 1
  rework_targets = da_review에서 재작업 필요 대상 추출

  WHILE da_iteration < 3 AND rework_targets not empty:
    FOR each rework_target in rework_targets:
      SendMessage(
        recipient: "{rework_target}",
        content: "DA 종합 리뷰 피드백:\n{da_review.feedback}\n\n수정 후 다시 결과를 보내주세요.",
        summary: "DA rework request for {rework_target}"
      )
      # 3중 업데이트 (REVISE)
      TEAM_PROGRESS.md: {rework_target} → Progress: 50%, Note: DA rework #{da_iteration}
      IF dashboard_available:
        Bash("curl -s -X POST http://localhost:3747/api/progress -H 'Content-Type: application/json' -d '{\"agent\":\"{rework_target}\",\"progress\":50,\"task\":\"DA rework\",\"note\":\"iteration #{da_iteration}\"}' --connect-timeout 2 || true")
      TEAM_BULLETIN.md에 Append:
        ## [{timestamp}] - Lead (DA CONCERN)
        **Target**: {rework_target}
        **Feedback**: {da_review.feedback 요약}
        **Status**: DA rework #{da_iteration}

    # 수정 결과 재수신
    FOR each rework_target:
      reworked_result = 메시지 자동 수신
      TEAM_PROGRESS.md: {rework_target} → Progress: 80%, Note: rework submitted

    # DA 재검토
    da_iteration += 1
    SendMessage(
      recipient: "devils-advocate",
      content: "수정된 결과를 재검토해주세요:\n{reworked_results_summary}\n\nrecommendation: ACCEPTABLE 또는 CONCERN",
      summary: "DA re-review #{da_iteration}"
    )
    da_review = DA 메시지 자동 수신

    IF da_review.recommendation == "ACCEPTABLE":
      FOR each agent:
        TEAM_PROGRESS.md: Progress → 100%, Note → completed (DA ACCEPTABLE)
        IF dashboard_available:
          Bash("curl ... progress:100 ...")
      BREAK

    rework_targets = da_review에서 재작업 필요 대상 추출

  IF da_iteration >= 3:
    → 경고: "DA 리뷰 최대 반복(3)에 도달. 현재 결과로 진행."
    FOR each agent:
      TEAM_PROGRESS.md: Progress → 100%, Note → completed (DA max iterations)

# TEAM_FINDINGS.md에 DA 결과 기록
TEAM_FINDINGS.md:
  ## DA Review
  - Recommendation: {ACCEPTABLE/CONCERN}
  - Iterations: {da_iteration}
  - Feedback: {da_review 전문}
  - Lead Decision: {판정 사유}
```

### Phase 4: 교차 검증 통합

```
# 최종 교차 검증
Graph ∩ Retrieval → 핵심 노트 (확실히 관련)
Graph only → 관계 기반 발견 (간접 연결)
Retrieval only → 고립 노트 (링크 후보)

# Checkpoint 2 업데이트 (Phase 3에서 미완료 시)
TEAM_PROGRESS.md: | 2 | All workers completed | 모든 워커 결과 수신 | [x] |

# TEAM_FINDINGS.md 최종 작성
TEAM_FINDINGS.md:
  ## Cross-Validation Summary
  | Category | Count | Notes |
  |----------|-------|-------|
  | Core (Graph ∩ Retrieval) | N | ... |
  | Graph Only | N | ... |
  | Retrieval Only | N | ... |

  ## Key Insights
  1. ...

  ## DA Review
  - Recommendation: {ACCEPTABLE/CONCERN}
  - Iterations: {da_iteration}
  - Lead Decision: ...
```

---

## STEP 5: 노트 생성 (Main이 직접 실행!)

**CRITICAL**: 노트 생성은 **반드시 Main이 직접** 수행합니다.
팀원에게 쓰기 작업을 위임하면 안 됩니다! (Bug-2025-12-12-2056)

### 5-1. Obsidian 노트 생성

```bash
# Tier 1: CLI (우선)
"$OBSIDIAN_CLI" create path="적절한/경로/파일명.md" content="YAML frontmatter + 노트 내용"

# Tier 2: MCP (CLI 실패 시)
mcp__obsidian__create_note({
  path: "적절한/경로/파일명.md",
  content: "YAML frontmatter + 노트 내용"
})

# Tier 3: Write (MCP 실패 시)
Write({ file_path: "{vault_absolute_path}/적절한/경로/파일명.md", content: "..." })
```

**경로 규칙** (CLAUDE.md 참조):
- Vault root = `AI_Second_Brain`
- 경로는 vault root 기준 상대 경로
- `AI_Second_Brain/`를 prefix로 붙이지 말 것!

### 5-2. 3-tier 구조 (해당 시)

3-tier 선택 시 다음 순서로 생성:
1. 원자적 노트들 (각 개념당 1개)
2. 카테고리 MOC (각 챕터당 1개)
3. 메인 MOC (전체 요약 + 모든 카테고리 MOC 링크)

**모든 노트에 네비게이션 푸터 포함!** (km-export-formats.md 참조)

### 5-3. 저장 검증 (필수!)

```
모든 create_note 호출 후:
1. 응답에서 "created successfully" 확인
2. Glob으로 파일 존재 확인
3. 실패 시 Write 도구로 폴백
```

---

## STEP 5.25: 이미지 저장 및 임베딩 (image_extraction_enabled 시 — Main 직접 실행!)

**CRITICAL**: 이 Phase는 `image_extraction_enabled = true`일 때만 실행합니다.
**CRITICAL**: 파일 저장은 반드시 Main이 직접 수행! (Task 에이전트 쓰기 버그 방지)

참조 스킬: `km-image-pipeline.md`

### Phase 5.25 워크플로우

```
1. content-extractor Image Catalog 파싱:
   - content-proc-lead 보고서에서 Image Catalog 테이블 추출
   - 각 이미지의 Type, Source, URL/Path, Context, Placement 확인

2. Resources/images/{topic-folder}/ 디렉토리 생성:
   Bash("mkdir -p /home/tofu/AI/AI_Second_Brain/Resources/images/{topic-folder}/")

3. 각 이미지 다운로드/복사:

   웹 이미지:
   Bash("curl -sLo '/home/tofu/AI/AI_Second_Brain/Resources/images/{topic-folder}/{NN}-{descriptive-name}.{ext}' '{url}'")

   PDF 이미지 (marker 출력):
   Bash("cp km-temp/{name}/images/{file} '/home/tofu/AI/AI_Second_Brain/Resources/images/{topic-folder}/{NN}-{descriptive-name}.{ext}'")

4. 다운로드 실패 시 Playwright 스크린샷 폴백:
   - 원본 URL로 navigate
   - browser_take_screenshot으로 해당 요소 캡처
   - 저장 경로: Resources/images/{topic-folder}/{NN}-screenshot.png

5. 노트 콘텐츠에 이미지 임베드 (본문 흐름 배치!):
   - 개념 설명 → (빈 줄) → ![[Resources/images/{topic-folder}/{filename}]] → (빈 줄) → 상세 설명
   - content-analyzer의 Placement 제안에 따라 적절한 위치에 삽입
   - 이미지 연속 배치 금지 (반드시 텍스트로 분리)

6. Notion 페이로드에 이미지 블록 추가:
   - 외부 URL 이미지: { "type": "image", "image": { "type": "external", "external": { "url": "{원본URL}" } } }
   - 로컬 전용 이미지: callout 블록으로 대체 — "[이미지: Resources/images/{topic-folder}/{filename}]"

7. 저장 검증:
   Glob("AI_Second_Brain/Resources/images/{topic-folder}/*") → 파일 존재 확인
   각 이미지 파일 크기 > 0 확인
```

### 대시보드 진행률 (Phase 5.25)

```
IF dashboard_available AND image_extraction_enabled:
  Bash("curl -s -X POST http://localhost:3747/api/progress -H 'Content-Type: application/json' -d '{\"agent\":\"Lead\",\"progress\":72,\"task\":\"이미지 저장 중\",\"note\":\"Phase 5.25\"}' --connect-timeout 2 || true")
```

---

## STEP 6: 연결 강화 + 팀 정리

### 6-1. 연결 강화 (연결 수준 "보통" 또는 "최대"일 때)

상세 워크플로우: `km-link-strengthening.md` 참조

```
1. 새 노트 핵심 키워드 추출
2. CLI `"$OBSIDIAN_CLI" search` / MCP search_vault로 관련 노트 탐색
   - CLI `"$OBSIDIAN_CLI" deadends` → 나가는 링크 없는 파일 = 연결 강화 우선 후보 (format 옵션 미지원, 플레인 텍스트 목록 반환)
3. 관련성 점수 3점 이상인 노트와 양방향 링크 생성
4. CLI `"$OBSIDIAN_CLI" append` / MCP update_note로 기존 노트에 역방향 링크 추가
   - CLI `"$OBSIDIAN_CLI" prepend` → 네비게이션 헤더 추가 시 사용
```

### 6-2. 팀 셧다운 + 활동 로그 (tofu-at STEP 7-7 패턴)

```
PRECONDITION (셧다운 전제 조건 — DA 활성화):
  da_review.recommendation == "ACCEPTABLE"
  OR da_iteration >= 3

# DA 미승인 시 셧다운 불가 — STEP 4 Phase 3 완료 후에만 진행

0. 전 agent Progress → 95% curl push (셧다운 직전):
   FOR each agent in [Lead, vault-intel-lead, content-proc-lead, graph-navigator, retrieval-specialist, link-curator, content-extractor, deep-reader, content-analyzer, devils-advocate]:
     TEAM_PROGRESS.md: Progress → 95%, Note → shutting down
     IF dashboard_available:
       Bash("curl -s -X POST http://localhost:3747/api/progress -H 'Content-Type: application/json' -d '{\"agent\":\"{agent}\",\"progress\":95,\"task\":\"shutdown\",\"note\":\"shutting down\"}' --connect-timeout 2 || true")

1. 각 팀원에게 shutdown_request:
   FOR each member in [vault-intel-lead, content-proc-lead, graph-navigator, retrieval-specialist, content-extractor, deep-reader, content-analyzer, link-curator, devils-advocate]:
     SendMessage({ type: "shutdown_request", recipient: "{member}", content: "작업 완료." })

2. shutdown_response 대기 (최대 10초):
   각 팀원의 shutdown_response를 대기.
   10초 내 응답 없는 팀원은 아래 3번에서 강제 정리.

3. 잔류 tmux pane 강제 정리 (CRITICAL — scurrying 방지):
   Read("~/.claude/teams/km-at-{주제키워드}/config.json")
   FOR each member in team_config.members (리드 제외):
     IF member.tmuxPaneId:
       Bash("tmux kill-pane -t {member.tmuxPaneId} 2>/dev/null || true")
   FOR each member in team_config.members (리드 제외):
     IF member.isActive != false:
       config.json에서 해당 member의 isActive = false 설정

4. TeamDelete()

4.1. Results 보고서 자동 전송 (MANDATORY — TeamDelete 직후):
   report = {
     "id": "{timestamp}-km-at-{주제키워드}",
     "timestamp": "{ISO 8601}",
     "teamName": "km-at-{주제키워드}",
     "subject": "{주제}",
     "complexity": "AT Full-Scale",
     "duration": "{실행 소요 시간}",
     "sourceCommand": "/knowledge-manager-at",
     "team": [각 role의 { name, role, model, status }],
     "steps": [각 step의 { id, step, assignee, status }],
     "checkpoints": [각 checkpoint의 { name, done }],
     "bulletin": [{최근 bulletin 항목들}],
     "results": { "summary": "...", "details": "...", "artifacts": [...] },
     "ralph": { "iterations": {...}, "verdict": "..." },
     "da": { "recommendation": "...", "iterations": N }
   }

   # Primary: Agent Office 서버로 POST
   IF dashboard_available:
     Bash("curl -s -X POST http://localhost:3747/api/reports -H 'Content-Type: application/json' -d '{report JSON}' --connect-timeout 5")

     # Fallback: curl 실패 시 파일로 직접 저장
     IF curl 실패 (exit code != 0 또는 HTTP != 200/201):
       Bash("mkdir -p .team-os/reports")
       Write(".team-os/reports/{report.id}.json", JSON.stringify(report, null, 2))

5. 대시보드 아티팩트 정리:
   IF dashboard_available:
     Bash("curl -s -X POST http://localhost:3747/api/session/clear --connect-timeout 2 || true")
   → .team-os/artifacts/TEAM_*.md 삭제 (MEMORY.md 유지)
   → 대시보드가 stale 팀 데이터 표시하지 않도록 방지

6. TEAM_FINDINGS.md → MEMORY.md 이관:
   Read(".team-os/artifacts/TEAM_FINDINGS.md")
   → Key Insights → MEMORY.md Lessons Learned 테이블에 추가
   → 주요 결정사항 → MEMORY.md Decisions 테이블에 추가
   → Session Log 테이블에 현재 세션 기록 추가:
     | # | 날짜 | 주제 | 팀규모 | 생성노트 | 연결수 | RALPH횟수 | DA판정 |
```

### 6-3. 결과 보고

```
## 처리 결과 보고

### 입력 요약
- 소스: [URL/파일/vault종합]
- 모드: Agent Teams (풀스케일, 9명)
- Team OS: 활성
- Agent Office: [실행 중 / 미실행]
- Dashboard Push: [활성 / 비활성]

### Agent Teams 요약
| 계층 | 팀원 | 역할 | 모델 | 결과 |
|------|------|------|------|------|
| Cat.Lead | vault-intel-lead | Vault 탐색 조율 | Sonnet 1M | 핵심 {N}개, 관계 {N}개 |
| Cat.Lead | content-proc-lead | 콘텐츠 처리 조율 | Sonnet 1M | 추출 완료, 구조 설계 |
| Worker | @graph-navigator | 그래프 탐색 | Sonnet | Hub {N}개, 1-hop {N}개 |
| Worker | @retrieval-specialist | 키워드 검색 | Sonnet | 관련 노트 {N}개 |
| Worker | @content-extractor | 콘텐츠 추출 | Sonnet | {N} words |
| Worker | @deep-reader | 깊이 읽기 | Sonnet | 교차 분석 {N}개 |
| Worker | @content-analyzer | 구조 설계 | Sonnet | 노트 {N}개 제안 |
| Worker | @link-curator | 링크 추천 | Haiku | 연결 후보 {N}개 |
| DA | @devils-advocate | 반론 검증 | Sonnet | {반론수} 반론, {수용수} 수용 |

### RALPH Loop 요약
| 이터레이션 | 대상 | 피드백 | 결과 |
|-----------|------|--------|------|
| 1 | ... | ... | accepted/retry |

### 처리 요약
- 검색된 관련 노트: N개
- 교차 검증 핵심 노트: N개
- 생성된 노트: N개
- 추가된 양방향 링크: N개
- 이미지 추출 (활성 시): N개 다운로드, N개 임베딩
- 이미지 실패 (있으면): N개 (사유 포함)

### 출력 위치
| 노트 | 경로 | 상태 |
|------|------|------|
| [MOC명] | Research/... | 성공 |

### Checkpoints 요약
| # | Checkpoint | 상태 |
|---|-----------|------|
| 1 | All workers spawned | ✅/❌ |
| 2 | All workers completed | ✅/❌ |
| 3 | Artifacts generated | ✅/❌ |

### DA 종합 리뷰
- Recommendation: {ACCEPTABLE/CONCERN}
- Iterations: {N}
- Rework 대상: {목록 또는 없음}

### Team OS 아티팩트
- TEAM_BULLETIN: .team-os/artifacts/TEAM_BULLETIN.md
- MEMORY: .team-os/artifacts/MEMORY.md
- Findings: .team-os/artifacts/TEAM_FINDINGS.md
- Results: .team-os/reports/{report-id}.json (Agent Office 전송 실패 시)
```

---

## 참조 스킬 (상세 워크플로우)

| 기능 | 참조 스킬 |
|------|----------|
| 전체 워크플로우 | `km-workflow.md` |
| 환경 감지 | `km-environment-detection.md` |
| 콘텐츠 추출 | `km-content-extraction.md` |
| **YouTube 트랜스크립트** | `km-youtube-transcript.md` |
| 소셜 미디어 | `km-social-media.md` |
| 출력 형식 | `km-export-formats.md` |
| 연결 강화 | `km-link-strengthening.md` |
| 연결 감사 | `km-link-audit.md` |
| Obsidian 노트 형식 | `zettelkasten-note.md` |
| 다이어그램 | `drawio-diagram.md` |
| **Mode R: 아카이브 재편** | `km-archive-reorganization.md` |
| **Mode R: 규칙 엔진** | `km-rules-engine.md` |
| **Mode R: 배치 실행** | `km-batch-python.md` |

---

## 사용자 요청 내용

$ARGUMENTS
