# Changelog

## 1.4.0 (2026-09-05)

- 저장소 안 `.claude/` 미러를 제거했습니다. 커맨드·스킬·에이전트는 최상위 `commands/`·`skills/`·`agents/` 한 곳에만 있고, 프로젝트 설치는 `scripts/install-to-project.sh` 가 담당합니다.
- `scripts/install-to-project.sh` 추가 — `bash scripts/install-to-project.sh /your/project` 로 커맨드·스킬·에이전트를 프로젝트 `.claude/` 에 복사하고, `scripts/send_kakao.py` 와 `km-config.example.json` 도 함께 놓습니다. 복사 뒤 파일 수를 디렉터리별로 검사해 하나라도 빠지면 종료 코드 1 로 멈춥니다.
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
