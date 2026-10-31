# Changelog

## 1.8.5 (2026-10-31) — km:search 규칙 원본 단계 · 메모리뱅크 3건 고정 · 깊음 모드 그래프 확장
- 규칙 원본 축(구 Tier 1-R)을 Tier 0 블록(메모리뱅크 블록과 같은 Bash 호출)으로 옮김. 돌릴지 판정을 모델이 넘기는 `VAULT_MODE` 대신 `km_rules_route.py --auto` 가 직접 함(끔 스위치·서버 응답·결과 source_note 의 vault 실재) — `other` 확정 때만 건너뜀. 실측: 옛 판은 모델이 블록 자체를 안 돌린 회차가 15 중 11.
- 순위: rg 축 길이 정규화(BM25 꼴) · 조사 떼기 = 남는 줄기 2자 이상일 때만 · 루트 AGENTS.md·CLAUDE.md 를 코퍼스에 늘 포함. 원본 우선 원칙(규칙·절차 질문이면 후보 원본 최소 1개 Read · 원본 = 현재 기준).
- 끝 결정까지 읽기: 규칙 원본 후보마다 그 파일의 결정 표지(해제·대체·정정·철회) 줄 번호를 들여쓴 한 줄로 덧붙임 — 질문 낱말 겹침이 가장 큰 제목 절의 줄 범위 + 그 절 안 표지 줄 + 파일 마지막 표지 + «그 줄까지 읽고 날짜가 가장 늦은 결정 = 현재 기준». 실측 동기: 원본을 열고도 앞 «재개» 문단만 읽고 몇 줄 아래 «해제» 문단을 놓친 회차(9문항 중 1).
- 노트 미리 찾기: 후보 원본 안 `[[노트]]`(+ 백틱 `이름.md` · vault 에 실재하는 백틱 슬러그)를 대본이 vaultPath 안 파일 이름(`rg --files` · 없으면 os.walk · 시한 20초)으로 미리 풀어 `↳ 가리키는 노트` 줄로 덧붙임 — 경로 · «규칙 원본» · «볼트에 없음» · 찾기 실패는 «노트 찾기 못 함(부재 아님)» · 늘 «레포 전체 훑기 ❌». 고른 절 안 링크 먼저, 파일 전체 ≤12 · «못 함» 줄 끝 = vault 한정 `rg --files --hidden -g '<이름>.md' '<vaultPath>'`. 실측 동기: 노트 1개를 찾으려 레포 루트에서 prune 없는 find·grep -r 로 문항 시한 초과(4칸 중 3칸). 두 판 번갈아 3회 × 켬·끔: 첫 시도 시한 4/6 → 0/6.
- 영수증 절 vault-lookup = 시한 20초(`KM_VL_TIMEOUT`) — perl 로 감싸 프로세스 묶음째 끔 · 넘기면 `VL_HITS=timeout` + 기존 «VL_UNAVAILABLE=1 — 부재 단정 금지»(timeout = 부재 증거 아님). 실측 동기: 부하 때 vault-lookup 단독 183–221초.
- Tier 1 끔 스위치(`~/.claude-state/km-search-graphrag-off` 있으면 Tier 1 건너뜀 · `GRAPHRAG_STATE=disabled` · 실패 상태로 셈 · tier4 안내 문구 · Codex 쪽 km-search SKILL 같은 스위치) — 그동안 설치 캐시에만 있던 로컬 손질을 원본에 들임.
- 경로 줄 `${CLAUDE_PLUGIN_ROOT:-}` → `${CLAUDE_PLUGIN_ROOT}`(Claude Code 가 명령 본문의 `${CLAUDE_PLUGIN_ROOT}` 만 절대 경로로 바꿔 넣음 · `:-` 꼴은 그대로 남아 find 폴백으로 빠짐) — 규칙 원본 줄 · Tier 1-S `KM_CLI_Q` 줄 · 영수증 helper 줄.
- 영수증 helper 는 플러그인에 싣지 않는다 — 착수 게이트(vault 훅)와 짝인 vault 사본 하나가 정본이고 그쪽이 보통 길(사본이 둘이면 서로 어긋난다). helper 가 구판(`--km-mode` 모름)이면 `tiers_tried` 끝에 `rcpt:repo-legacy` + `RECEIPT_FALLBACK=repo-legacy` 줄(`src` 는 그대로 — 착수 게이트가 `src=manual` 만 셈).
- Tier 0(메모리뱅크): `--limit 3` 인데 6건이 나오던 문제 수리. memory-bank `search` 의 기본(both) 모드는 의미 검색 상위 N 과 글자 검색 상위 N 을 합친 뒤 자르지 않아 최대 2N 을 낸다. 이제 의미(`--vector --limit 2`)와 글자(`--text --limit 1`)를 따로 1번씩 부르고 `Lines A-B in <jsonl 경로>` 로 중복을 지워 합계 ≤3 으로 고정한다(겹치면 점수가 있는 의미 쪽을 남김). 라벨 `[mb:의미]`(% = 의미 유사도) · `[mb:글자]`(글자 그대로 일치 · 점수 없음). `MB_HITS` = 중복 제거 뒤 블록 수.
- Tier 0: 종료 코드를 `grep` 이 아니라 `node` 에서 받는다(옛 블록은 파이프 끝 `grep -v` 의 종료 코드로 ok/error 를 갈랐다). 한쪽만 실패해도 `error`, 살아 있는 쪽 블록은 그대로 보인다. 걸러 낸 블록을 bash 출력에 찍는다(옛 블록은 상태 줄만 찍어 결과 블록이 모델에 닿지 않았다).
- Phase 2.5-B(그래프 확장): backlinks 계수 명령과 정수 `BACKLINKS_N` 을 참조 파일(`search-references/phase-2.5-graph.txt`)에서 본문으로 옮김 — DEEP 이 참조 파일을 읽지 않아도 돈다. 계수 = 목록 자르기 전 전체 파일 수 · 0 도 0. 참조 파일엔 «본문으로 옮김» 1줄과 링크 추적 예산만 남김. 정상 QUICK 경로의 참조 Read = 0 은 그대로.
- 끝 줄 형식: DEEP 이고 `VAULT_MODE` 가 `other` 가 아니면 `+ 그래프 확장(backlinks N)` 생략 금지. 생략은 QUICK(2.5-B 안 돌림)·`other` 만. 같은 규칙을 적어 둔 참조 파일(`search-references/modes-output.txt`)도 맞춤 · `tier2-cli.txt` 의 «2.5-B backlinks 호출 = 1단 ② 로 대체»에 «grep 계수는 그대로» 덧붙임.
- 영수증: DEEP 이면 `--graph-expansion <done|skipped:사유>` · `--backlinks <N>` 을 넘긴다 — 단 helper `--help` 에 두 인자가 있을 때만(모르는 helper 에 넘기면 argparse 오류로 영수증이 깨진다). 없으면 `KM_RECEIPT_GRAPH_FIELDS=unsupported` 1줄.
- Phase 0.4(구조 문서 축) 절을 Tier 1 성공 계약 뒤(Tier 1-S 앞)로 옮김 — 실행 순서 계약(Tier 1 curl 전 vault 접근 금지)과 문서 차례를 맞춤. 본문 그대로, 제목 단계만 `##`→`####`(Tier 1 아래로 들어가게).
- 두 진입 파일(commands/search.md · .agent/skills/km-search/SKILL.md) 같은 뜻으로 수정.
- 시험: `scripts/tests/test_km_rules_route.py`(규칙 원본 대본) · `test_search_tier0_mb.sh`(가짜 memory-bank CLI · 의미 2+글자 1 → 3 · 겹침 → 2 · CLI 없음 → absent · 오류 → error · 결과 없음 → 0 · `--limit` 무시 CLI → 3 · 같은 가짜로 옛 블록 → 6) · `test_search_graph_expansion.sh`(링크 있는 노트 → 독립 계수와 같음 · 고아 노트 → 0 · 영수증 새/옛/반쪽 helper · 절 차례). 두 셸 시험은 bash 와 zsh 에서 돌리고 CI 에 추가.
- 매니페스트: .claude-plugin 1.8.4→1.8.5 · .codex-plugin 1.8.4→1.8.5(동시) · tier2 시험 버전 고정 2줄 1.8.5.

## 1.8.4 (2026-10-14)
- 브라우저가 필요한 자리(Scrapling 으로는 안 열리지만 브라우저로는 누구나 볼 수 있는 공개 페이지 · SNS · 브라우저 조작)는 Playwright 대신 Aside(`aside exec` · WSL `aside.exe exec`)를 먼저 쓴다. 일반 페이지는 기존 순서(Scrapling → … → WebFetch) 그대로. Aside 가 없거나 실패하면 그 이유를 남기고 Playwright 등 기존 순서로 넘어간다. km-config `browser.provider`(브라우저가 필요할 때의 공급자) 기본 aside.

## 1.8.3 (2026-09-28)
- kordoc 최신판 고정: 한글·한국어 문서 변환 호출을 `npx kordoc` → `npx -y kordoc@latest` 로 교체(skills/km-content-extraction.md · .agent/skills/km-content-extraction · .agent/skills/km-workflow). npx 캐시에 옛 판이 남아 있어도 항상 최신판(2026-09-28 확인 = 4.15.7)을 받는다.
- 안내 갱신: 지원 형식에 이미지(OCR) 추가 · 「PDF 는 `pdfjs-dist@4` peer 필요」 문구 삭제(4.15.7 은 선택 의존성으로 자동 설치 — HWP·PDF 변환 실측 OK) · `--ocr`·`--formula-ocr`·`--format chunks` 옵션 안내.
- 매니페스트: .claude-plugin 1.8.2→1.8.3 · .codex-plugin 1.8.2→1.8.3(동시) · tier2 시험 버전 고정 2줄 1.8.3.

## 1.8.2 (2026-09-24)
- /km:knowledge-manager STEP 0: `/using-superpowers` 강제 호출 게이트 제거(아키텍처 Phase 0 요약 · STEP 0 제목 · MANDATORY 배너 · 0-PRE MUST 3줄). superpowers 는 비자명 build/bug 착수 때만 부르는 운영 방침에 맞춤. km-pipeline 오버레이 참조는 그대로 둠.
- skills/km-pipeline.md: 같은 강제 문구 5곳 제거(Constraints 1번 · Mandatory Skills 표 행 · Phase 0 의 MUST 줄과 제목 「스킬 활성화」 · 「추가된 것」 표 행 · Final Reminder 1번). 뒤 번호를 당기고 「세 가지 → 두 가지 절대 규칙」. Phase 0 의 모드 감지·선호도 수집 줄은 유지.
- commands/knowledge-manager.md Auto-Learned Patterns 의 2026-04-04 기록(게이트 삽입 권고)에 폐지 표기 — 실행 프롬프트에 실려 반대 지시로 읽히지 않게.
- 매니페스트: .claude-plugin 1.8.1→1.8.2 · .codex-plugin 1.8.1→1.8.2(동시) · tier2 시험의 매니페스트 버전 고정 2줄 1.8.2.

## 1.8.1 (2026-09-22)
- /km:search Phase 0.6: 대상 고정(target binding · `target_status` resolved/unspecified/ambiguous · 공개 입력에서만 별칭) + Tier 1 질의 고정·`target_hit` 라벨.
- Tier 1-T: 대상 보강 질의 1회(순위 재배열 없음).
- DEEP 읽기 중단 규칙(미독·미충족·충돌이 남으면 「충분」으로 멈추지 않음).
- 요구 항목 커버리지 표(requirements 가 있을 때).
- 근거: 2026-09-21 채점(55) · 같은 6문항×3방식 18행 재관측에서 코드+Jev 방식 3문항이 FAIL→PASS(원18행 PASS 합계 5 = 수리 전과 동일 · 대조군 6은 API 제한으로 미실행 · 수리 단독 인과·모델 우열 미분리).
- 매니페스트: .claude-plugin 1.8.0→1.8.1 · .codex-plugin 1.7.1→1.8.1(동시) · 시험: tier1-unchanged → tier1-contract(앵커 6 + 미끼) · plugin-version 기대값 1.8.1(두 매니페스트).
- 내부 추적: r6 L1-a~d(절차 수리 4건의 내부 식별자 — 본문에는 노출하지 않음).

## 1.7.1 (2026-09-08)
- /km:search Phase 2.5: 링크 확장에 «허브로 올라가는 링크 우선» 축 역이식(vault 2026-07-13 벤치 근거 — 주변 노트엔 도달하나 허브 미도달이 주 실패 모드) · 링크 추적 예산 명시(A+B 합산 QUICK ≤1 / DEEP ≤3 · 총 Read QUICK 3 / DEEP 8) — fable51 재기획 D-15(2026-09-08).
- 매니페스트: `.codex-plugin/plugin.json` version 1.5.0→1.7.1 동시 bump(1.5.1~1.7.0 세 판 연속 정지 결손 보수 — 릴리스 절차: 두 매니페스트 동시).

## 1.7.0 (2026-09-07)

- /km:search Tier 2: 0-α 활성 vault 대조 · 0-β 질문 분해(in-context JSON, --decomp=sub 헤드리스 haiku 옵션) · 0-γ intent→CLI 재조립 규칙표(relation/meta/tag/nav/content/temporal/mixed) · 분해 실패 = 1.6.0 규칙 파이프라인 그대로 · 1단 3축(prop/bl/ln) 항상 유지. 근거 = vault 36-p4 v0.1.
- 손질(예시 5 실측): nav = 파일명 축 [name] 최상위 · relation = 역링크 0 → 본문 언급 [mention] 폴백.
- 손질 3: nav 파일명 축 = 경로 전체 + 한↔영 동의어표(회의록→meeting|minutes 등 10쌍).
- README: /km:search 절 최신화 — 1.5.1~1.7.0 기능표 + 2026-09-08 실측 사례 6건(한/영) · 영문판 search 절 신설.

## 1.6.0 (2026-09-07)

- /km:search Tier 2: Obsidian CLI 5축(backlinks·links·properties·search:context·tags)을 규칙으로 «항상» 실행(상위 QUICK 2/DEEP 5 노트 · 축 라벨) + 신호어는 진입 순서만 + obsidianCli.vault 키 + 0B/No-matches 구별.

## 1.5.1 (2026-09-07)

- /km:search Tier 1-S 신선도 보강: /health finished_at 나이 > KM_SEARCH_STALE_MIN(40분) 또는 최근지향 질의면 Obsidian CLI 결과를 [fresh:cli] 로 보강(Tier 1 결과 불변). 근거 = vault 25-p2.

## 1.5.0 (2026-09-06)

- 파이프라인 스킬 이름을 `km-pipeline` 으로 바꿨습니다(명령·스킬 문서와 테스트 픽스처의 표기도 함께 맞춤). 동작 변화는 없습니다.

## 1.4.3 (2026-09-05)

- 설치 테스트 2건을 추가했습니다(`scripts/tests/test_install_to_project.sh` 18/18). ① 교체 1단계에서 이전 파일을 옆으로 옮기는 이름 바꾸기가 아예 실패한 경우: 프로젝트의 파일이 체크섬까지 그대로 남고, 옆으로 옮긴 사본도 새 파일도 남지 않으며, 무엇을 옮기지 못했는지 알린 뒤 멈춥니다. ② 그 이름 바꾸기가 이전 사본과 원래 자리를 둘 다 남긴 채 설치가 중단된 경우: 두 사본 중 어느 쪽도 손대지 않고, 이전 사본이 어디에 있는지 알린 뒤 종료 코드 143 으로 멈춥니다.
- `agent-office/km-tools` 테스트에서 검사 출처 예시로 쓰던 사람 이름을 중립적인 값(`subagent:검토자-a`)으로 바꿨습니다. 검사 동작과 기대값은 그대로입니다.

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
