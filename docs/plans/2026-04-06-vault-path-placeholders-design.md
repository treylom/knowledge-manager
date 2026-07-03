# Vault Path Placeholders — Design Plan

**Date**: 2026-04-06
**Author**: Lead (Claude Opus 4.6) + treylom
**Status**: Approved, implementation in progress
**Branch**: `feature/vault-path-placeholders`
**Backup branch**: `backup/pre-vault-placeholders`

---

## Problem

knowledge-manager deployment repo는 사용자가 clone하여 설치하는 구조이지만, 다수 skill/agent/command 파일에 **개인 vault 경로와 Obsidian CLI 경로가 하드코딩**되어 있어 다른 사용자가 그대로 사용할 수 없다.

### 현황 (2026-04-06 baseline)

13개 파일에 약 66건의 하드코딩된 경로가 존재:

| 파일 | 하드코딩 수 |
|---|---:|
| skills/km-export-formats.md | 16 |
| agents/knowledge-manager.md | 11 |
| skills/km-image-pipeline.md | 8 |
| skills/km-content-extraction.md | 6 |
| commands/knowledge-manager-at.md | 6 |
| commands/knowledge-manager.md | 5 |
| commands/knowledge-manager-m.md | 5 |
| skills/km-glm-ocr.md | 4 |
| skills/km-workflow.md | 1 |
| skills/km-link-audit.md | 1 |
| skills/km-archive-reorganization.md | 1 |
| skills/km-storage-abstraction.md | 1 (anti-pattern 예시, 치환 제외) |
| skills/km-graphrag-report.md | 1 (GraphRAG, 배포 제외) |

패턴 예시:
- `/home/tofu/AI/AI_Second_Brain/...` (WSL)
- `/path/to/your/vault/...` (Windows via WSL)
- `C:\Users\YourName\OneDrive\Desktop\AI\AI_Second_Brain\...` (Windows native)
- `AI_Second_Brain/` (vault name 단독)

## Goals

1. 배포 repo의 모든 skill/agent/command 파일이 **사용자별 vault 경로에 자동 적응**
2. 기존 `/knowledge-manager-setup` 위저드와 **자연스럽게 통합**
3. `git pull`로 업데이트 수신 시 **충돌 없이** 재설정 가능
4. 추가 의존성 **0** (jq 등)
5. Claude Code, Codex, 기타 AI 에이전트가 이 repo를 편집할 때 **placeholder 규칙 명확히 인지**

## Non-Goals

- Windows 네이티브(Git Bash/PowerShell) 1차 지원 (WSL/Mac/Linux 우선)
- GraphRAG 관련 파일 배포 (검색/구축 모두 배포 제외)
- km-storage-abstraction.md 의 anti-pattern 교훈 변경 (내용 유지)
- `defaultFolder`, `researchFolder` 등 legacy 필드 제거 (호환 유지)

## Design Decisions (brainstorm 결과)

| 결정 | 선택 | 대안 |
|---|---|---|
| 치환 전략 | **In-place sed** | ~~Template 디렉토리~~, ~~Runtime 해결~~ |
| Placeholder 스코프 | **5개** (VAULT_PATH, VAULT_NAME, OBSIDIAN_CLI, ZETTELKASTEN_ROOT, RESEARCH_ROOT) | ~~3개만~~, ~~4개 모두~~ |
| 재실행 & git pull | **Skip-worktree + `/km-update` 커맨드** | ~~단순 revert~~, ~~스냅샷 디렉토리~~ |
| Git workflow | **모두 feature branch, 1회 merge** | ~~Group A 먼저 master~~ |
| JSON 파서 | **Node.js** (이미 필수 의존성) | ~~jq (추가 설치 필요)~~, ~~Python~~ |

## Architecture

```
knowledge-manager/
├── km-config.example.json            ← 스키마 확장 (+2 필드)
├── km-config.json                    ← 사용자 로컬 (gitignored, 위저드가 생성)
├── README.md                         ← Installation & Configuration 섹션 추가
├── CLAUDE.md                         ← 신규 (Claude Code용 프로젝트 계약)
├── AGENTS.md                         ← 신규 (범용 AI 에이전트용)
├── docs/
│   ├── plans/
│   │   └── 2026-04-06-vault-path-placeholders-design.md  ← 이 문서
│   └── vault-path-configuration.md   ← 신규 (기술 레퍼런스)
├── scripts/
│   ├── _lib-config.sh                ← 신규 (Node.js 기반 config 파서)
│   ├── configure-vault-paths.sh      ← 신규 (치환 엔진)
│   └── km-update.sh                  ← 신규 (업데이트 오케스트레이터)
├── commands/
│   ├── knowledge-manager-setup.md    ← 수정 (Phase 4에 스크립트 호출 추가)
│   └── km-update.md                  ← 신규 (/km-update 슬래시 커맨드)
├── skills/, agents/                  ← 13 파일 refactor (+ .claude/ mirror)
└── .claude/                          ← 모든 미러 동일하게
```

## Placeholder Taxonomy

| Placeholder | Config 필드 | 기본값 | 치환 대상 |
|---|---|---|---|
| `{{VAULT_PATH}}` | `storage.obsidian.vaultPath` | — (필수) | Absolute vault path |
| `{{VAULT_NAME}}` | derived from VAULT_PATH basename | — | Vault 폴더명 (예: `AI_Second_Brain`) |
| `{{OBSIDIAN_CLI}}` | `obsidianCli.path` | `""` | Obsidian CLI 실행파일 |
| `{{ZETTELKASTEN_ROOT}}` | `storage.obsidian.zettelkastenRoot` | `"Zettelkasten"` | Zettelkasten 루트 (vault 상대) |
| `{{RESEARCH_ROOT}}` | `storage.obsidian.researchRoot` | `"Research"` | Research 루트 (vault 상대) |

## Config Schema Extension

`km-config.example.json`의 `storage.obsidian` 섹션에 2개 필드 추가:

```json
{
  "storage": {
    "obsidian": {
      "vaultPath": "/path/to/your/obsidian/vault",
      "zettelkastenRoot": "Zettelkasten",
      "_zettelkastenRoot_help": "Zettelkasten 노트 루트 (vault 상대). 예: 'Zettelkasten' 또는 'Library/Zettelkasten'",
      "researchRoot": "Research",
      "_researchRoot_help": "Research 노트 루트 (vault 상대). 예: 'Research' 또는 'Library/Research'",
      "defaultFolder": "Zettelkasten",      // legacy, 유지
      "researchFolder": "Research",          // legacy, 유지
      "threadsFolder": "Threads"             // legacy, 유지
    }
  }
}
```

## Data Flow

### Setup flow
```
사용자가 /knowledge-manager-setup 실행
    ↓
위저드가 vault 경로 수집 + Obsidian CLI 감지
    ↓
km-config.json 생성
    ↓
configure-vault-paths.sh 자동 호출
    ↓
Node.js로 km-config.json 파싱 → 5개 placeholder 값 추출
    ↓
find skills/ agents/ commands/ .claude/ -name "*.md" → sed 치환
    ↓
git update-index --skip-worktree <치환된 tracked 파일들>
    ↓
사용자 환경 준비 완료
```

### Update flow (`/km-update`)
```
사용자가 /km-update 실행
    ↓
km-update.sh:
  1. git ls-files -v | grep ^S → skip-worktree 파일 목록 추출
  2. git update-index --no-skip-worktree <파일들>
  3. git checkout HEAD -- <파일들>  (placeholder 복원)
  4. git pull origin <current-branch>
  5. bash scripts/configure-vault-paths.sh  (재치환)
  6. git update-index --skip-worktree <파일들>  (재잠금)
```

### Re-configuration flow
```
사용자가 vault 경로 변경 원함
    ↓
/knowledge-manager-setup 재실행
    ↓
기존 km-config.json 백업 (timestamp)
    ↓
새 config 생성
    ↓
configure-vault-paths.sh:
  1. skip-worktree 해제
  2. git checkout HEAD -- (placeholder 복원)
  3. 새 값으로 재치환
  4. skip-worktree 재적용
```

## Components

### 1. `scripts/_lib-config.sh` — Common JSON parser

Node.js 기반 dot-path JSON 읽기 함수 제공:

- `config_get "storage.obsidian.vaultPath" "default"` — 단일 값 조회
- `vault_name "$path"` — basename 추출 (backslash 정규화 포함)
- `path_normalize "$path"` — Windows backslash → forward slash

### 2. `scripts/configure-vault-paths.sh` — Substitution engine

1. `km-config.json` 존재 확인 (없으면 에러 종료)
2. `_lib-config.sh` 로드 → 5개 값 추출
3. 필수 필드 검증 (`VAULT_PATH` 비어있으면 에러)
4. `find skills agents commands .claude -name "*.md"` 열거
5. `km-storage-abstraction.md` 제외 (anti-pattern 파일)
6. placeholder 포함 파일에만 sed 실행 (fast path)
7. tracked 파일에 `git update-index --skip-worktree` 적용

### 3. `scripts/km-update.sh` — Update orchestrator

1. 예상치 못한 로컬 변경 감지 → 안전 가드 (stash/commit 요청)
2. skip-worktree 해제
3. `git checkout HEAD --` (placeholder 복원)
4. `git pull origin <current-branch>`
5. `configure-vault-paths.sh` 재실행

### 4. `commands/km-update.md` — Slash command wrapper

`/km-update` 실행 시 `bash scripts/km-update.sh` 호출.

### 5. `commands/knowledge-manager-setup.md` Phase 4 수정

기존 Phase 4 (km-config.json 생성) 말미에 `bash scripts/configure-vault-paths.sh` 호출 추가.

### 6. Documentation layer

- **README.md** — Installation & Configuration 섹션 추가 (placeholder 개요, setup/update 명령)
- **CLAUDE.md** — Claude Code가 이 repo 편집 시 지켜야 할 규칙 (placeholder 금지/허용, 미러 동기화)
- **AGENTS.md** — 범용 AI 에이전트용 계약
- **docs/vault-path-configuration.md** — 기술 레퍼런스 + 트러블슈팅

## Special Cases

### km-storage-abstraction.md line 63 — Anti-pattern teaching

현재 `❌ 틀림: AI_Second_Brain/Zettelkasten/...  (vault 이름 중복 금지)` 는 "vault 이름을 경로 접두사로 쓰지 말라"는 교훈.

sed 치환하면 `❌ 틀림: {{VAULT_NAME}}/...` → 치환 후 실제 값으로 바뀌어 교훈 소실.

**해결**: 수동 리팩터링으로 구체적 vault 이름을 제네릭 문구로 교체:
```markdown
❌ 틀림: YourVaultName/Zettelkasten/...  (vault 이름 중복 금지)
```

스크립트는 이 파일을 **명시적 제외** (`! -path "*/km-storage-abstraction.md"`).

### GraphRAG files — 배포 제외

3개 untracked 파일 (`skills/km-graphrag-{search,report,sync}.md` + `.claude/` mirror 3개) 은 GraphRAG 검색/구축 기능이 배포 범위 밖이므로 Phase 0에서 working copy에서 삭제.

## Implementation Phases

### Phase 0 — Lead 단독 (✅ 완료)
- [x] backup/pre-vault-placeholders 브랜치 생성 + push
- [x] feature/vault-path-placeholders 브랜치 생성
- [x] untracked graphrag 파일 6개 삭제
- [x] Group A 커밋 (18 파일, SNS crawling + frontmatter)
- [ ] 이 design doc 커밋

### Phase 1 — 5개 워커 병렬 (/tofu-at-codex)

| Worker | Scope | 파일 수 |
|---|---|---:|
| α Infrastructure | scripts/ 3개, km-config.example.json, /km-update 커맨드, setup 위저드 Phase 4 수정 | ~8 |
| β Documentation | README.md 수정, CLAUDE.md 신규, AGENTS.md 신규, docs/vault-path-configuration.md 신규 | 4 |
| γ Skills Large | km-export-formats, km-image-pipeline, km-content-extraction (+ mirror) | 6 |
| δ Skills Small + Anti-pattern | km-glm-ocr, km-workflow, km-link-audit, km-archive-reorganization, km-storage-abstraction (+ mirror) | 10 |
| ε Agents + Commands | agents/knowledge-manager, commands/knowledge-manager{,-m,-at} (+ mirror) | 8 |

**충돌 방지**: 각 워커는 고유한 파일 집합 소유, `scripts/` 는 Worker α 전용, 타 워커는 touch 금지.

**브랜치 전략**: 각 워커가 `feature/vp-worker-{alpha,beta,gamma,delta,epsilon}` sub-branch에서 작업 → Lead가 순차 머지.

### Phase 2 — Lead 검증 + 머지

1. 5개 sub-branch 머지 (`--no-ff`)
2. Verification 체크리스트 실행:
   - `bash scripts/configure-vault-paths.sh` 테스트 실행 (mock km-config.json 사용)
   - `grep -rE "/home/[^/]+/|/Users/[^/]+/|C:\\\\Users\\\\" skills/ agents/ commands/ .claude/` → 0 hits
   - Mirror diff: 모든 `skills/X.md` ≡ `.claude/skills/X.md`
   - Group A 기능 보존 확인 (SNS crawling 변경 + frontmatter 유지)
3. `feature/vault-path-placeholders` → `master` merge (`--no-ff`)
4. `git push origin master`
5. Backup 브랜치는 1-2주 유지 후 삭제

## Verification Criteria

### Hard gates (실패 시 머지 금지)
- [ ] `configure-vault-paths.sh` 가 sample km-config.json으로 정상 동작
- [ ] 치환 후 개인 경로 하드코딩 0건 (grep 검증)
- [ ] 모든 mirror 쌍 일치 (diff -q silent)
- [ ] Group A의 SNS 크롤링 변경이 보존됨
- [ ] `km-storage-abstraction.md` 의 anti-pattern 교훈이 placeholder 없이 제네릭 문구로 유지
- [ ] `CLAUDE.md`, `AGENTS.md`, `README.md` 가 placeholder 시스템을 정확히 설명

### Soft gates (경고만)
- [ ] `scripts/km-update.sh` dry-run 가능 (실제 git pull 없이)
- [ ] Obsidian CLI 경로가 비어있어도 스크립트 정상 종료 (Obsidian 미사용 케이스)
- [ ] `docs/vault-path-configuration.md` 트러블슈팅 섹션 3개 이상 케이스 커버

## Rollback Plan

1. `git checkout master && git reset --hard backup/pre-vault-placeholders`
2. `git push origin master --force-with-lease` (필요 시)
3. backup 브랜치는 merge 후 1-2주 보존

## Open Questions

- Windows 네이티브 사용자 지원은 follow-up PR에서 PowerShell 버전으로 처리
- 향후 `obsidianCli.path` 자동 감지 로직을 스크립트에도 포함할지 (현재는 위저드만 감지)

## References

- Brainstorming session: 이 문서 작성 전 대화 로그
- Related files: Section 3 (File inventory) 참조
- Related skills: `superpowers:brainstorming`, `superpowers:writing-plans`, `tofu-at-codex`
