# Changelog

## 1.8.12 (2026-11-08) — kepano/obsidian-skills 에서 세 조각 흡수: 설명서 정합 · 노트 문법 경고 검사 · 폴더 노트 표(.base) 검사기
- 설명서 = 실제로 도는 순서: 일반 웹 페이지 추출 1순위 = 브라우저 자동 탐색(ego lite → Aside) → playwright-cli → WebFetch. Scrapling(`scripts/scrapling-crawl.py`)은 플러그인에 없으므로 «선택 — 따로 설치한 경우에만 맨 앞에서 먼저 시도»로 내림(명령·에이전트·스킬·Codex 사본). 소셜 1순위도 명령 문서를 에이전트·스킬과 같게(브라우저 자동 탐색).
- 버전 고정: `kordoc@latest` → `kordoc@4.24.47` · `@firecrawl/anydoc` → `@0.2.4`(2026-11-06 두 버전 모두 실제 변환 실행 확인 · kordoc 4.24.47 은 2026-11-08 HWP·HWPX 각 1건도 다시 변환 확인). 1.8.3 은 «npx 캐시의 옛 버전» 문제로 `@latest` 를 골랐는데, 정확한 버전 번호를 적으면 같은 문제가 풀리고, 버전이 바뀌는 때를 알 수 있다. 올릴 때 = `npm view` 확인 + 1회 실행 + 문서 줄 함께.
- 노트 틀 = lint 필수 필드: 생성 틀에 `aliases`·`author`·`date` 추가(`agent-office/km-tools/lib/lint.py` 의 `REQUIRED_FIELDS` 와 맞춤) · 원자·MOC 틀에 빠져 있던 `source` 도 추가(원본 URL·파일명, 원본 없이 직접 쓴 노트면 «직접 작성» · 영어 vault 면 «original» 등 — 원본이 없을 수 있는 노트 틀 전부에 같은 규칙 · 소셜·유튜브·카톡·문헌 노트처럼 출처가 늘 있는 틀은 그대로) — 틀대로 만든 원자·MOC 노트의 lint 완전성(필수 5칸 중 채운 비율) 0.2 → 1.0(1.8.11 틀은 `tags` 만 있었음) · 카테고리 MOC 틀에도 `source` · 틀 안 날짜 꼴 = `YYYY-MM-DD` 하나(`created` 는 검색 시간축이 읽으므로 유지).
- 소셜 미디어 스킬 소개문(«Playwright CLI 기반»)도 실제 순서(브라우저 자동 탐색 → playwright-cli)로.
- 검색 설명서 `base:query` 줄: «쓰지 않는다(문법 미확정)» → 검색 축엔 안 쓰되 .base 검증용 문법·함정(오류도 종료코드 0 + `Error:` · 빈 .base 는 vault 전체) 실측으로 고침.
- 새 `scripts/km_ofm_lint.py`(경고 모드 · 표준 라이브러리): 헤딩·블록 링크 대상 · 콜아웃 타입 · 접기 위치 · `%%`/`==` 짝 · tags 공백·`#`. 링크 게이트와 «함께» 돌고(대체 ❌), 게이트가 면제하는 MOC 도 검사. 저장을 막지 않음(exit 0 · `--strict` 일 때만 1 · 측정 불가 2 — vault·노트 없음, 읽을 수 없는 노트(끊긴 심링크·권한)). 콜아웃 타입 검사는 사용자 CSS 로 만든 콜아웃에도 경고를 낸다(그땐 무시). 실제 vault 3만여 노트에 돌려 헛경고 3종(표 안 `\|` 별칭 · 조사·문장부호 앞에서 닫는 `==` · `f(x)==2` 같은 코드식)과 tags 경고 줄 번호 오귀속을 찾아 고침. 참고로 작성자 vault 에서는 경고가 1,854건(2026-11-06)에서 377건(2026-11-08 다시 측정 · 32,725 노트 · exit 0)으로 줄었다 — 다른 vault 에선 수치가 그대로 재현되지 않는다.
- 새 `scripts/km_base_check.py` + 문안 초안 `docs/plans/2026-11-06-folder-base-save-step-draft.md`: 폴더 노트 표(.base) 저장 조건 5 검사(시범 · 저장 흐름엔 아직 안 넣음 · exit 1 = 미통과 판정이고 저장을 막을지는 부르는 쪽이 정함). 폴더 조건은 경로 단위로 비교(`topic-x` 가 `topic-xy` 에 걸리지 않음) · 읽을 수 없는 .base·MOC = 측정 불가 2.
- `km_base_check.py` 는 Obsidian CLI 를 열어 둔 빈 파이프를 표준입력으로 주고 부른다 — 표준입력이 `/dev/null`(cron·CI)이면 큰 응답(2.3MB)이 0바이트로 오는 CLI 동작이 있어서다(실측).
- 시험: `scripts/tests/test_km_ofm_lint.py`(18) · `scripts/tests/test_km_base_check.py`(19) — CI 에 추가.
- 알려진 한계(다음 판): 닫히지 않은 `==` 가 아주 많은 긴 줄은 느림(40KB 한 줄 20~25초 · 두 번 측정) · `km_base_check.py` 중복 셈은 점 폴더(`.trash` 등) 안 .base 도 셈 · `--folder /` 는 폴더 조건이 늘 통과 · 끊긴 심링크 노트 하나가 있으면 전체 스캔이 측정 불가(2)로 끝남.
- 프로젝트 폴더 설치(`install-to-project.sh`)는 링크 게이트처럼 두 새 검사기도 복사하지 않는다 — 안내 문구의 «복사 안 함» 목록에 추가(그 설치에선 OFM 검사가 «측정 불가»로 건너뜀).
- 매니페스트: .claude-plugin 1.8.11→1.8.12 · .codex-plugin(동시) · `scripts/tests/test_search_tier2_axes.sh` 의 버전 고정 2줄.

## 1.8.11 (2026-11-07) — 검색 명령 문서의 내부 흔적 정리 · 영수증 helper 를 개인 경로 대신 git 뿌리에서 찾기
- `commands/search.md`·`.agent/skills/km-search/SKILL.md` 의 제목 괄호 3곳(메모리뱅크 축 · 영수증 · 1단 규칙 확장)에서 내부 사람 이름·메시지 번호·인용을 지우고 판·날짜만 남김(뜻 그대로).
- 영수증 helper(`km-search-receipt.py`) 폴백이 특정 사용자 홈 아래 고정 경로를 보던 것을, 플러그인 사본(`${CLAUDE_PLUGIN_ROOT}/scripts/`) → 볼트의 git 뿌리 → 지금 폴더의 git 뿌리 순으로 `.claude/scripts/km-search-receipt.py` 를 찾게 바꿈. 두 문서가 같은 꼴. 못 찾으면 기존처럼 영수증을 건너뜀. 실측: 볼트가 git 저장소가 아닌 설정(볼트 경로 = 동기화 사본)에서도 지금 폴더 쪽으로 찾음(bash·zsh × 볼트 경로 3가지 6/6) · git 밖 폴더 = 빈 값.
- Codex 사본도 플러그인 사본을 먼저 보게 됨(전엔 고정 경로 하나뿐).
- 시험: 기존 봉인 시험 그대로 통과(영수증 칸 포함) · 시험 파일 무변경.
- 매니페스트: .claude-plugin 1.8.10→1.8.11 · .codex-plugin(동시) · tier2 시험 버전 고정 2줄.

## 1.8.10 (2026-11-07) — km:search 지도 하강: 글자 점수가 애매하면 모델이 허브 설명을 읽고 내려간다
- 지금까지 Phase 0.4 는 MOC-Map 을 글자 점수(awk — 키워드가 몇 개 걸리나)로만 읽고 상위 허브 3개를 골랐다. 점수가 같은 허브가 많거나 키워드가 다 걸린 허브가 없으면 줄 순서로 잘렸다. 이제 그럴 때만 /km:search 를 돌리는 모델이 지도에 적힌 허브 한 줄 설명을 읽고 고른 뒤, 필요하면 폴더 하나 → 허브 노트 안 링크까지 내려간다(문서 목차를 먼저 읽고 내려가는 PageIndex 방식의 «추론 하강»을 지도에 맞춘 것 · 새 트리를 만들지 않고 있는 지도를 쓴다).
- 언제 타나: `route` 출력에 `ambiguous`·`ambiguity` 를 더함 — `no_match`(키워드가 걸린 허브 0) · `partial_match`(모든 키워드를 가진 허브 없음) · `tie_at_cut`(3번째와 4번째 허브 점수가 같음). 이 셋 중 하나이거나 Phase 0.6 의 `target_status=ambiguous` 면 하강, 아니면 현행 그대로. 다른 vault(`VAULT_MODE=other`)는 로컬 지도 접근 0 그대로.
- 기존 글자 점수 경로는 폴백으로 남는다: `route` 의 기존 칸(허브·점수·순서·근거 줄)은 1.8.9 와 글자까지 같다(지도 1개 × 시험 키워드 30벌 대조 30/30) · 메뉴 실패·고를 것 없음 = 글자 점수 허브 그대로.
- 새 하위 명령(모델 호출 없음 · 대본은 여전히 네트워크를 쓰지 않음): `menu`(글자가 하나라도 걸린 허브 ≤60 — 제목·폴더·한 줄 설명·vault 경로, 최상위 폴더별 허브 수 · `--folder` 면 그 폴더 아래 허브를 들어오는 링크 많은 순 ≤60 + 하위 폴더 수) · `outlinks`(허브 노트 한 개의 링크 ≤40, 링크가 놓인 줄 글 포함 — 본문 2,500자 예산과 별개 · 원문 찾기와 같은 «심볼릭 링크를 따라가지 않는 열기» · vault 밖·절대 경로 = «미확보» exit 3). 하강 단계는 합계 ≤3(메뉴 1 · 폴더 ≤1 · 허브 안 ≤1).
- 근거 수치 [주의: 골드셋 30문항은 사람 검수 전 초안] — 같은 30문항 · 같은 키워드(문항마다 1회 뽑아 고정) · 판정 모델 Sonnet(도구 끔 · 질문과 메뉴만 봄, 정답 이름은 프롬프트에 없음) · 2회 반복:
  - hit@5(상위 5 안에 정답 노트): 현행(허브 ≤3) 9/30 · 같은 점수 상위 5 12/30 · **새 경로 15/30**(2회 모두).
  - hit@1: 현행 6/30 · **새 경로 11/30 · 9/30**.
  - 정답이 지도에 있는 문항(21): 현행 9 · 상위 5 12 · 새 경로 13. 정답이 지도에 없는 문항(9 — 허브 «아래» 노트): 현행 0(허브만 내므로 원리상 0) · 새 경로 2.
  - 비용: 하강을 탄 문항 29/30(애매 신호가 거의 늘 켜짐 — `tie_at_cut` 26 · `partial_match` 16 · `no_match` 1) · 문항당 모델 판단 단계 평균 1.47·1.57 · 문항당 시간 현행 0.03초 → 새 경로 평균 6.2초(중앙 5.3·6.2 · 최대 11.8) · 단계당 입력 약 4.7천 토큰(최대 1.1만).
  - 잃은 문항도 있다: «같은 점수 상위 5»는 맞혔는데 새 경로가 놓친 문항 회차마다 3(현행 허브 3개 대비로는 2·1) · 현행이 1위로 맞혔는데 새 경로가 1위를 놓친 문항 2·3. 시험의 판정 모델은 별도 호출로 흉내 낸 것이고, 실제 /km:search 에선 실행 중인 모델이 같은 메뉴를 읽는다.
- 한계: Codex 쪽 사본(`.agent/skills/km-search/SKILL.md`)엔 이번 판이 들어가지 않았다(Claude Code 명령만 · 1.8.7 과 같은 처리). 애매 신호가 거의 늘 켜지므로 사실상 하강이 기본 경로가 된다 — 신호를 좁히면(예: `tie_at_cut` 제외 → 17/30 에서만 하강) 같은 30문항에서 hit@5 가 11·10 으로 떨어졌다(같은 문항으로 고른 사후 비교라 참고만).
- 시험: `scripts/tests/test_km_map_descent.py`(17칸 — 기존 칸 불변 · 애매 신호 3종 · awk 와 같은 점수 · 메뉴 상한·폴더·vault 밖 링크 · 허브 링크 2,500자 뒤까지 · vault 밖·심볼릭 링크 = 미확보 · 명령 본문의 새 블록을 bash·zsh 로 실제 실행) — CI 에 추가.
- 매니페스트: .claude-plugin 1.8.9→1.8.10 · .codex-plugin(동시) · tier2 시험 버전 고정 2줄.

## 1.8.9 (2026-11-06) — 명령 본문의 `$0`·`$1`·`$2` 가 질문 낱말로 바뀌던 문제
- Claude Code 는 슬래시 명령 본문을 싣기 전에 `$ARGUMENTS` 와 함께 `$0`·`$1`·`$2`… 도 사용자가 친 낱말로 바꿔 넣는다(`$0` = 첫 낱말, `$1` = 둘째 낱말) — 코드 블록·작은따옴표 안도 가리지 않는다. 그래서 `/km:search 8월 중순 회의 기록` 처럼 낱말이 두 개 이상인 질문이면 1단 검색 함수가 `"중순/api/search?q=…"` 로 깨져 서버를 못 부르고, 메모리뱅크 축 awk 가 `{print "V\t" 8월}` 로 깨졌다(실제 모델은 부르지 않고, 가짜 API 서버로 슬래시 명령이 보내는 첫 요청을 받아 확인). 그 번호의 낱말이 없으면 그대로 남아서 한 낱말 질문에선 안 보였다.
- 고친 곳 10곳 — `commands/search.md` 9곳(메모리뱅크 축 awk 4 · `gr_fetch` 1 · `cliq` 2 · 최신 확인 질의 awk 2) · `commands/knowledge-manager-setup.md` 1곳(awk). 뜻이 같고 치환되지 않는 꼴로: 셸 `"$1"` → `"${1}"` · awk `$0`·`$1` → `$(0)`·`$(1)`. Codex 사본(`.agent/skills/km-search/SKILL.md`)의 같은 3줄(5곳)도 똑같이 고침 — Codex 는 치환하지 않지만, Tier 0 시험이 두 파일이 글자까지 같은지 대조한다.
- `\$1` 로 막으면 안 된다 — Claude Code 가 역슬래시를 떼고 `$1` 을 남긴다(실측).
- 그대로 둔 것: `commands/search-references/*.txt` 와 스킬로 등록되지 않은 `skills/*.md` 단독 파일은 Read 로만 읽혀 치환되지 않는다(가짜 서버가 받은 요청 본문에 실리지 않음을 확인).
- 시험: `scripts/tests/test_command_posargs.py` — `commands/*.md` · `skills/*/SKILL.md` 에 `$숫자` 0 (일부러 넣은 틀린 꼴은 잡고 고친 꼴은 통과하는지 함께 확인) + 바꾼 꼴이 옛 꼴과 같은 출력(awk·bash·zsh) — CI 에 추가. 옛 판(1.8.8)에선 2파일 FAIL.
- 매니페스트: .claude-plugin 1.8.8→1.8.9 · .codex-plugin(동시) · tier2 시험 버전 고정 2줄.

## 1.8.8 (2026-11-05) — PDF 전용 명령 지움
- /km:pdf 명령(`commands/pdf.md`)을 지움 — PDF 도 `/km:knowledge-manager` 로 저장되므로 따로 명령이 필요 없음. 큰 PDF·한글 경로 PDF 는 `marker_single` 로 바로 바꾼다(README·명령·에이전트 안내를 그 길로 고침). PDF 처리 기능(`skills/pdf.md` 안내·추출 스킬·kordoc)은 그대로. 판 번호 1.8.7→1.8.8(플러그인 설정 2곳 · 시험 2줄).

## 1.8.7 (2026-11-05) — km:search 원문은 결과 경로로 찾기 · 지도 노트 위키링크 이름 풀기
- 원문 찾기: 검색 결과의 원문을 `entity`(이름)가 아니라 결과의 `source_note`(경로)로 찾는다 — `scripts/km_note_caller.sh` → `scripts/km_search_guard.py`. 같은 vault 면 vault 안의 그 경로만 읽고 서버를 부르지 않는다. 다른 vault 면 서버 `/api/note` 를 한 번 부르되, 돌아온 `note_path` 가 기대한 `source_note` 와 유니코드 정규화(NFC) 뒤 글자 그대로 같을 때만 본문을 쓴다(이름만 같은 노트 ❌ · 앞 폴더 떼기 ❌). 경로 없음·절대 경로·부모 폴더 탈출·심볼릭 링크·다른 경로·깨진 응답·HTTP 실패·256KB 넘는 노트 = «원문 미확보»(exit 3) — 확보 0건을 성공으로 세지 않는다. 연결 3초·전체 15초·본문 앞 2,500자는 그대로. 같은 vault 읽기는 심볼릭 링크를 따라가지 않는 열기(`O_NOFOLLOW` · 폴더 기준 열기)가 되는 OS(맥·리눅스)에서만 하고, 그게 안 되는 파이썬(Windows 등)에선 멈추지 않고 «원문 미확보»로 빠진다(Windows 실측 전).
- 지도 노트 위키링크 이름 풀기: 지도(MOC) 노트에 실제로 적힌 `[[이름]]` 을 따라갈 때 `scripts/km_wikilink_resolver.py` 가 같은 vault 의 md 파일 목록에서 이름을 푼다. 후보 1개 = 그 경로 · 2개 이상 = 같은 줄의 백틱 폴더 힌트(vault 뿌리 기준 경로)로 좁히고, 안 좁혀지면 «모호»(추측 ❌) · `/` 가 든 링크 = 폴더 경계 기준 끝맞춤(여전히 후보 1개만) · 다른 vault = 로컬 파일 목록·본문 읽기 0 · 파일 목록을 끝까지 못 읽었으면(읽기 오류·유니코드 정규화 충돌) «미확보». 풀린 경로는 위 원문 찾기 검사를 그대로 거친다.
- Phase 0.4(구조 문서 축): MOC-Map 앞 130줄만 보던 허브 매핑을 지도 전체로 넓힘(점수·순서·최대 3허브 규칙은 그대로). 130줄은 근거로 읽는 줄 수 상한이고 후보를 찾는 범위를 자르지 않는다. 출력 줄이 `ROUTE_SCAN=ok|unmeasured ROUTE_HUB_COUNT=…` + 결과 JSON 으로 바뀜.
- 한계: 본문은 앞 2,500자 고정 — 찾던 내용이 그 뒤에 있으면 못 가져온다(실측 사례는 2,500자 경계 1자 앞에서 끝났다). Codex 쪽 사본(`.agent/skills/km-search/SKILL.md`)엔 이번 판이 들어가지 않았다(Claude Code 명령만).
- 시험: `scripts/tests/test_km_note_fragment_boundary.py`(경계 1자 앞에서 끝나는 주소 = 통째로 옴 · 1자 밀면 잘림 · 같은/다른 vault 두 길) · `scripts/tests/test_km_note_guard_platform.py`(심볼릭 링크 막는 열기가 없는 파이썬 흉내 → «원문 미확보» exit 3 · 원래 환경은 그대로 읽음) — CI 에 추가.
- 매니페스트: .claude-plugin 1.8.6→1.8.7 · .codex-plugin(동시) · tier2 시험 버전 고정 2줄.

## 1.8.6 (2026-11-05) — 브라우저 자동 탐색: ego lite → Aside → 기존 순서
- 웹 페이지를 브라우저로 열어야 할 때 km 이 먼저 `scripts/km_browser_detect.py` 를 한 번 돌려, 깔려 있고 대답하는 브라우저를 고른다: ego lite(`ego-browser skill` 안내가 끝까지 나옴) → Aside(`aside --version` 성공) → 기존 순서(Playwright CLI → Playwright MCP → WebFetch). 사용자가 브라우저를 고르거나 설정하는 단계는 없다.
- 실행 파일 절대 경로를 돌려준다 — `~/.local/bin` 이 PATH 에 없는 맥에서도 ego lite·Aside 를 찾는다(고정 설치 폴더도 본다). 확인 명령마다 시한(기본 15초 · `KM_BROWSER_PROBE_TIMEOUT`)이 있어, 멈춘 CLI 가 있어도 한 도구당 최대 15초만 기다린다.
- ego lite 가 꺼져 있어도 `ego-browser nodejs` 명령이 앱 창을 띄운다(맥 실측) — 따로 켜는 단계 없음.
- ego lite 는 에이전트 작업을 별도 작업 공간에서 해서 창엔 빈 새 탭만 보인다 — 처음 열 때 «숫자 버튼 → ‘km read’ 공간» 한 줄을 사용자에게 알린다(맥 실측).
- ego lite 가 사이트 권한 창(알림 허용 등)에서 «사용자 차례»로 멈추면 다른 브라우저로 넘어가지 않고, ego lite 창에서 무엇을 누르면 되는지 안내한 뒤 같은 작업 공간에서 이어 간다. 1.8.6 맥 실측에서는 «실행 중 실패하면 다음 칸» 문장대로 Aside 로 넘어갔다. ego lite 안내대로 권한 창은 사용자가 처리하고, 봇이 우회하지 않는다. 추출 스킬·에이전트·스텔스 문서의 «실패하면 다음 순위» 줄 4곳에도 같은 예외를 넣었다.
- `browser.provider`: 새 기본값 `auto`(설정 마법사 · km-config.example.json). 예전 기본값 `aside`(1.8.4~1.8.5 예시)가 적힌 설정은 Aside 가 깔려 있고 대답하면 Aside 를 먼저 쓰고, 아니면 자동 순서로 넘어간다. `playwright`(예전 설정 마법사 기본값)는 `auto` 와 같게 다뤄 자동 순서(ego lite → Aside → 기존 순서)를 따른다. `hyperbrowser`·`antigravity` 를 적은 경우만 그대로 따른다.
- 설정 마법사(`/km:setup`): Playwright 설치 질문 전에 감지기를 돌려, ego lite·Aside 가 있으면 질문을 건너뛰고 «웹페이지는 ego lite(또는 Aside)로 읽어요» 한 줄만 보여 준다. 끝 요약의 도구 줄도 실제 상태대로. (1.8.5 실측: ego lite 가 있어도 «웹 = Playwright 필수»로 설치를 권하고, 끝 안내도 «웹페이지 = Playwright 먼저 설치».)
- 문서: 명령(`commands/knowledge-manager.md`)·브라우저 추상화·추출 스킬·에이전트 정의·Codex 사본의 «Aside 3순위» 자리를 «브라우저 자동 탐색» 자리로 바꿈. Scrapling 이 없을 때 3순위(브라우저)를 건너뛰고 Playwright CLI 로 가던 문장도 고침.
- 시험: `scripts/tests/test_km_browser_detect.py`(ego 만 · Aside 만 · 둘 다 · 둘 다 없음 + PATH 밖 설치 · 대답 없는 CLI · 시한 · 설정값 갈래) — CI 에 추가.
- 한계: 설정은 지금 작업 폴더의 `km-config.json` 을 vault 쪽보다 먼저 읽는다 · 감지 대본이 여러 판 깔려 있으면 이름순 마지막 하나를 쓴다 · Windows 는 PATH 만 본다(고정 설치 폴더는 맥·리눅스 기준 · 실측 전).
- 매니페스트: .claude-plugin 1.8.5→1.8.6 · .codex-plugin(동시) · tier2 시험 버전 고정 2줄.

## 1.8.5 (2026-10-31) — km:search 규칙 원본 단계 · 메모리뱅크 3건 고정 · 깊음 모드 그래프 확장
- 규칙 원본 축(구 Tier 1-R)을 Tier 0 블록(메모리뱅크 블록과 같은 Bash 호출)으로 옮김. 돌릴지 판정을 모델이 넘기는 `VAULT_MODE` 대신 `km_rules_route.py --auto` 가 직접 함(끔 스위치·서버 응답·결과 source_note 의 vault 실재) — `other` 확정 때만 건너뜀. 실측: 옛 판은 모델이 블록 자체를 안 돌린 회차가 15 중 11.
- 순위: rg 축 길이 정규화(BM25 꼴) · 조사 떼기 = 남는 줄기 2자 이상일 때만 · 루트 AGENTS.md·CLAUDE.md 를 코퍼스에 늘 포함. 원본 우선 원칙(규칙·절차 질문이면 후보 원본 최소 1개 Read · 원본 = 현재 기준).
- 끝 결정까지 읽기: 규칙 원본 후보마다 그 파일의 결정 표지(해제·대체·정정·철회) 줄 번호를 들여쓴 한 줄로 덧붙임 — 질문 낱말 겹침이 가장 큰 제목 절의 줄 범위 + 그 절 안 표지 줄 + 파일 마지막 표지 + «그 줄까지 읽고 날짜가 가장 늦은 결정 = 현재 기준». 실측 동기: 원본을 열고도 앞 «재개» 문단만 읽고 몇 줄 아래 «해제» 문단을 놓친 회차(9문항 중 1).
- 노트 미리 찾기: 후보 원본 안 `[[노트]]`(+ 백틱 `이름.md` · vault 에 실재하는 백틱 슬러그)를 대본이 vaultPath 안 파일 이름(`rg --files` · 없으면 os.walk · 시한 20초)으로 미리 풀어 `↳ 가리키는 노트` 줄로 덧붙임 — 경로 · «규칙 원본» · «볼트에 없음» · 찾기 실패는 «노트 찾기 못 함(부재 아님)» · 늘 «레포 전체 훑기 ❌». 고른 절 안 링크 먼저, 파일 전체 ≤12 · «못 함» 줄 끝 = vault 한정 `rg --files --hidden -g <이름>.md -- "$VAULT_PATH"`. 실측 동기: 노트 1개를 찾으려 레포 루트에서 prune 없는 find·grep -r 로 문항 시한 초과(4칸 중 3칸). 두 판 번갈아 3회 × 켬·끔: 첫 시도 시한 4/6 → 0/6.
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
- 보안·실패 처리 고침(공개 전 검토 반영): ① 그래프 확장 = fail-closed — vault·노트를 먼저 확인하고 backlink·outlink 를 따로 재며 grep 오류(없는 vault·없는/읽기 불가 노트·읽기 불가 하위 폴더)면 `done/backlinks 0` 이 아니라 `failed:<사유>` · 빈 계수 · 블록 rc 1, 끝 줄 `그래프 확장(실패: <사유>)` · vault 는 실제 경로로 훑음(심볼릭 링크 vault 를 0 으로 세던 문제) · vault 밖 노트(절대·`..`·현재 폴더의 같은 이름)·줄바꿈 든 경로는 `failed:no-note` · 훑기는 `command grep`(하네스가 grep 을 셸 함수로 덮어도 실제 grep) ② «노트 찾기 못 함» 뒤 명령을 따로 한 줄(`↳ $ …`)로 · vault 경로는 문자열이 아니라 `"$VAULT_PATH"` 변수 · 노트 이름은 늘 작은따옴표로 감싼 `-g` 값(작은따옴표·`$(…)`·백틱·`=이름` 이 명령이 되던 문제 · 표시용 이름으로 명령 시작점을 속이던 문제 · 출력에 찍는 경로·이름의 제어 문자 = `?`) ③ `--auto` 탐침: `source_note` = vault 상대 경로만(절대·`..`·NUL·비문자열·깨진 유니코드·앞뒤 공백·vault 밖으로 풀리는 링크 = 거절 수만 `notes_rejected=N` · 예외 없음 · 거절만으로 `other` 확정 ❌) · 설정 vault 폴더가 없으면 `unknown` · endpoint = http/https + 그 host 만(계정 정보·`?`·`#` 붙은 주소 거절) · redirect 안 따라감 · 응답 1MiB 상한 · 연결·헤더·본문 합친 벽시계 예산(한 바이트·한 줄씩 흘리는 응답) · 응답 모양 검사 ④ 시험 모집단 권위: tier0·graph 시험이 칸 id 목록과 개수를 정확히 대조(칸 하나 빠지면 실패) · node 없음 = 실패(rc 1) · CI 는 zsh 를 깔고 `KM_TEST_REQUIRE_SHELLS="bash zsh"` 로 셸이 빠지면 실패 · 규칙 원본 시험을 CI 에 추가.
- 재검 2차 반영: ① 그래프 확장 노트 = 마지막 경로 칸까지 풀어(심볼릭 링크 따라감 · 최대 8번) 실제 폴더가 vault 안일 때만 받고, 그 폴더로 들어가 `O_NOFOLLOW` 로 한 번 연 파일 바이트만 읽음(vault 밖을 가리키는 노트 링크 = `failed:no-note` · 확인 뒤 바꿔치기 = 열기 거절 · 읽기 실패 = `failed:outlink-scan`) ② `km_rules_route.py` 잘못된 설정 모양(`storage`·`storage.obsidian`·`linking.semantic_adapter`·`search.ruleCorpus` 칸이 객체가 아님 · 문자열·목록 칸 형 틀림)과 `KM_RULES_PROBE_TIMEOUT`(숫자 아님·무한·0 이하·30초 초과) = traceback 없이 기본값 + stderr `RULES_CONFIG_IGNORED=<칸>: <사유>` ③ 영수증: 모드가 정해졌는데 vault 판정이 없으면 `--vault-mode unknown` 을 넘김 · Codex 쪽 영수증 블록은 그래프 칸을 `--km-mode DEEP --vault-mode …` 와 한 묶음으로(helper 가 네 인자를 다 알 때만) ④ 시험 권위 = 시험 파일 밖 `scripts/tests/cells.manifest`(칸 id 정본 + 시험 파일 구역별 sha256) 를 `scripts/tests/seal_cells.py check` 가 판정 · manifest sha256 은 저장소 밖(CI 저장소 변수 `KM_TEST_MANIFEST_SEAL`)에 고정 — 칸 삭제·id 중복·본문 바꿔치기·다시 봉인한 사본 = 실패.
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
