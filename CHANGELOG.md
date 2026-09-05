# Changelog

## 1.4.2 (2026-09-05)

- 설치기: 설치 도중 중단(Ctrl-C·종료 신호)돼도 이전 파일을 되돌립니다. 되돌리지 못한 이전 사본은 새 파일 «안»이 아니라 옆(.old-*)에 두고 그 위치를 알립니다(1.4.1 검토 잔여 R1·R2).
- 팀 모드(`/knowledge-manager-at`) 문서의 Team OS 전용 경로(`.team-os/spawn-prompts`·`registry.yaml`) 11곳에 「이 플러그인에는 포함되지 않음 — 없으면 생략」 안내를 달고, 죽은 검색 스크립트 호출 1곳을 GraphRAG API 호출로 바꿨습니다. 실행 중 생성되는 `.team-os/artifacts` 등 상태 경로는 그대로입니다.
- 문서 정리: 셋업 명령 표기를 실제 명령 `/knowledge-manager-setup` 으로 통일했습니다(README·설치기 안내·`.mcp.json.template` 등 8곳). 존재하지 않는 `/tofugraph bench` 안내 3곳을 지웠습니다.
- README: 설치 스크립트가 복사하는 것(커맨드·스킬·에이전트), `.agent/skills/` 와 Claude Code 의 관계, Playwright MCP 패키지명(`@modelcontextprotocol/server-playwright`), Claude Code CLI 의 MCP 등록 위치를 실제 동작에 맞게 고쳤습니다.
- `scripts/scrapling-crawl.py` 를 안내하던 문서 8곳에 「이 플러그인에 포함되지 않음 — 별도 준비, 없으면 playwright-cli」 를 명시했습니다.
- 스크립트: 경로 접두어 제거가 glob 문자에 안전하도록 인용(`install-to-project.sh`·테스트), `configure-vault-paths.sh` 의 `sed -i` 를 macOS/Linux 공통 방식으로, `_lib-config.sh` 의 Node 인라인 문자열을 환경변수 전달로 바꿨습니다(특수문자 경로 안전).
- 설치기 usage 에 프로젝트로 복사되지 않는 파일(설정 스크립트·템플릿)을 적었습니다. `commands/knowledge-manager-setup.md` 의 저장소 전용 단계에 안내를 달고 템플릿 경로에 폴백을 두었습니다.
- 에이전트 문서의 개인 PC 경로 5곳을 `{{VAULT_PATH}}`·`./km-temp/` 로 바꿨고, `AGENTS.md` 의 두 자가 검사 기대값을 실제와 맞췄습니다. `CLAUDE.md` 의 저장소 트리를 현재 파일 목록에 맞게 갱신했습니다.
- 존재하지 않는 스킬 `km-graphrag-workflow.md` 참조를 `km-graphrag-ops.md`·`/km:search` 로, 죽은 `.team-os/…` 검색 경로를 GraphRAG API 호출로 바꿨습니다. 1.4.1 항목의 문안(원자적→검사 후 교체 등)도 다듬었습니다.

## 1.4.1 (2026-09-05)

- `scripts/install-to-project.sh` 가 심볼릭 링크를 따라가지 않습니다 — 설치기가 쓰는 경로(`.claude/`·`commands/`·`skills/`·`agents/`·`scripts/`·설치 대상 파일) 중 하나라도 심볼릭 링크이면 아무것도 쓰지 않고 종료 코드 1 로 멈춥니다(프로젝트 밖으로 파일이 새는 경로 차단).
- 설치가 검사 후 교체 방식으로 바뀌었습니다 — 파일을 `.claude/.km-install-staging.<pid>/` 에 먼저 모아 검사한 뒤 이름 바꾸기로 교체합니다. 검사 단계에서 실패하면 프로젝트는 그대로이고, 교체 단계에서 실패하면 이전 파일을 되돌린 뒤 멈춥니다(되돌리지 못하면 그 위치를 알려 줍니다). 프로젝트가 그대로이거나 이전 파일을 되돌린 경우에는 다시 실행하면 됩니다. 기존 파일 보존 규칙(같은 경로만 갱신, 나머지는 그대로)은 변하지 않았습니다.
- 플러그인에 없는 스크립트를 가리키던 문서 3건을 정리했습니다 — `skills/stealth-browsing.md`·`skills/km-content-extraction.md`(TS 스텔스 스크립트)·`skills/km-paddleocr-vl.md`(`paddleocr-env-check.py`)에 「플러그인 미포함」을 명시했습니다. 대체 수단으로 안내한 Scrapling stealth 모드의 `scripts/scrapling-crawl.py` 도 이 플러그인에 포함되지 않으며(별도 준비), 없으면 `playwright-cli` 로 갑니다.
- `scripts/tests/test_km_link_gate.sh` 의 픽스처를 저장소 안(`scripts/tests/fixtures/km-link-gate-vault/`)으로 옮겨 신선한 clone 에서도 바로 돕니다.
- GitHub Actions 워크플로(`.github/workflows/test.yml`)를 추가했습니다 — 셸 테스트 3종과 `agent-office/km-tools` pytest 를 push·PR 마다 실행합니다.
- 설치 테스트 4건을 추가했습니다(실패 시 무변경 · 링크 거부 3종) — `scripts/tests/test_install_to_project.sh` 8/8.

## 1.4.0 (2026-09-05)

- 저장소 안 `.claude/` 미러를 제거했습니다. 커맨드·스킬·에이전트는 최상위 `commands/`·`skills/`·`agents/` 한 곳에만 있고, 프로젝트 설치는 `scripts/install-to-project.sh` 가 담당합니다.
- `scripts/install-to-project.sh` 추가 — `bash scripts/install-to-project.sh /your/project` 로 커맨드·스킬·에이전트를 프로젝트 `.claude/` 에 복사하고, `scripts/send_kakao.py` 와 `km-config.example.json` 도 함께 놓습니다. 복사 뒤 파일 수를 디렉터리별로 검사해 하나라도 빠지면 종료 코드 1 로 멈춥니다.
- 설치 스크립트는 프로젝트에 이미 있던 파일을 지우지 않습니다 — 같은 경로의 파일만 새 내용으로 바뀌고 나머지는 그대로 남습니다. 검사 기준은 「저장소가 제공하는 파일이 전부 프로젝트에 있는가」입니다.
- `.claude/` 에만 있던 파일 8개를 최상위로 옮겼습니다 — `skills/docx.md`, `skills/drawio-diagram.md`, `skills/notion-knowledge-capture.md`, `skills/notion-research-documentation.md`, `skills/pptx.md`, `skills/stealth-browsing.md`, `skills/xlsx.md`, `scripts/send_kakao.py`.
- 미러 사이에서 어긋나 있던 `km-link-strengthening` 스킬 1건을 최상위 최신 파일로 정리했습니다.

## 1.3.0 (2026-09-04)

- `/km:interview` 신설 — 폴더 나누기·MOC 허브·wiki 대상/비대상·스킬 추천을 상담해 `_meta/KM-DESIGN.md` 로 정리합니다.
- `/km:reform` 신설 — 기본은 `plan`(변경 계획서만 작성), `apply` 는 사용자가 명시할 때만 실행합니다. 적용 전 git 스냅샷을 자동으로 남기고 롤백 방법을 1줄로 안내하며, `check` 로 링크 상태를 검사합니다.
- `/km:setup` 에 Phase 5.5 추가 — `000-START-HERE/` 에 구조 문서 3종(START-HERE · VAULT-STRUCTURE · MOC-Map)을 템플릿으로 생성합니다.
- `/km:search` 에 Phase 0.4 구조 문서 축 추가 — Tier 2·3 보다 먼저 실행하고 티어 표시 줄을 확장합니다. 링크 게이트 `scripts/km_link_gate.py`(노트마다 MOC 링크 1개 이상·일반 링크 1개 이상, 종료 코드 0/1/2)와 지식원 `km-vault-design-principles` 를 함께 추가했습니다.
- 알려진 한계: Codex·Antigravity 공용 스킬 미러(`.agent/skills/` — `.codex-plugin/plugin.json` 이 가리키는 곳)에는 `km-search` 구조 문서 축을 이식했지만, `km-setup` 미러에는 Phase 5.5 가 아직 없고 `/km:interview`·`/km:reform` 은 Claude Code 커맨드로만 제공됩니다(Codex·Antigravity 에서는 아직 쓸 수 없음 — 다음 패치).

## 1.2.5 이전

- git 이력 참조
