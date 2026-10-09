---
description: vault 통합 검색 — GraphRAG(있으면) → Obsidian CLI → Obsidian MCP → 텍스트 검색 4단계 자동 폴백. quick(즉답)/deep(분석) 자동 라우팅
allowedTools: Bash, Read, Glob, Grep, mcp__obsidian__*
---

# /km:search — vault 통합 검색

$ARGUMENTS

> **핵심 설계**: 검색 창구는 이 명령 하나. **① GraphRAG → ② Obsidian CLI → ③ Obsidian MCP → ④ 텍스트 검색** 자동 폴백. GraphRAG 미설치도 ②~④로 동작.

> **찾는 범위**: vault 문서·개념·관계. 과거 대화·결정 경위는 메모리뱅크(Tier 0). 충돌은 `현재 기준`과 `과거 경위`로 나눠 표시. 한쪽 부재 ≠ 다른쪽 부재.

> 🚨 **실행 순서 계약 (고정)**: ① Phase -1 로 `VAULT_PATH`·`SEARCH_ENDPOINT` 읽기 → ② **곧바로 Tier 1 curl**. ①② 전에 vault rg/grep/find/ls/Read ❌. 로컬 파일은 Tier 1 `VAULT_MODE=same` 또는 Tier 1 실패 후만.

> 📎 **참조 로드**: `search-references/` (명령 파일 기준 같은 디렉터리; Codex 스킬 기준 `../../../commands/search-references/`). **정상 Tier 1 성공·QUICK 경로 참조 Read = 0.** 아래 성공 계약을 이 엔트리에서 실행한다. 참조는 Tier 2~4 폴백·DEEP·0건/빈약/lookup exact 0건/부재 단정 때만 조건부 1회 Read — 전부 선로드 ❌. 참조 Read = 규칙 로드(primary read 예산 **미포함**). **증거 노트 Read 기본 = 3** (QUICK 명시·얕은 질의 1-2 · DEEP·요구항목 미충족 ≤5 · 링크 추적 예산은 `phase-2.5-graph.txt`).

## Phase -1: 설정 읽기

1. `km-config.json`: 현재 폴더 → setup이 만든 위치 순. `storage.obsidian.vaultPath` → `VAULT_PATH`; 있으면 확정값이며 Obsidian 재대조·경로 추측 금지.
2. vaultPath가 없을 때만 Obsidian `open:true` 경로를 확인한다. 넓은 find·후보 순회 금지:
```bash
OBSIDIAN_JSON=$(ls -1 \
  "$HOME/Library/Application Support/obsidian/obsidian.json" \
  /mnt/c/Users/*/AppData/Roaming/obsidian/obsidian.json \
  "$APPDATA/obsidian/obsidian.json" 2>/dev/null | head -1)
python3 -c 'import json,sys;d=json.load(open(sys.argv[1]))["vaults"];print("\n".join(v["path"] for v in d.values() if v.get("open")))' "$OBSIDIAN_JSON"
```
WSL 경로는 `wslpath -u`. 파일/열린 항목을 못 찾을 때만 사용자에게 1회 묻는다. 사용자 경로는 `.obsidian`·최근 수정 md 유무를 확인하고 둘 다 아니면 사용 전 재확인한다.
3. `obsidianCli.path` → `OBSIDIAN_CLI`(없으면 Tier 2 자동 감지), `obsidianCli.vault` → `OBSIDIAN_VAULT`(없으면 vaultPath basename).
4. endpoint 우선순위 = 설정 → 환경 → 기본값. 미설정도 기본값 탐침. 아래 할당·echo 뒤 Tier 1 실행:
```bash
# CONFIG_ENDPOINT = linking.semantic_adapter.endpoint (없으면 빈 값)
SEARCH_ENDPOINT="${CONFIG_ENDPOINT:-${GRAPHRAG_API_URL:-http://127.0.0.1:8400}}"
echo "SEARCH_ENDPOINT=${SEARCH_ENDPOINT}"
```

## Phase 0 — 모드·구조·대상

**Tier 1 curl 이전에는 모드·대상만 결정하고 vault 접근은 금지. Phase 0.4 로컬 구조 문서는 Tier 1 `VAULT_MODE=same` 확인 또는 Tier 1 실패 후 실행한다. `other`에서는 STRUCT_DOCS=0·ROUTE_HUB_COUNT=0, 다른 vault임을 명시하고 구조 접근을 생략한다.**

## Phase 0: 모드 결정

query = "$ARGUMENTS"

IF query가 비어있으면:
  → "사용법: `/km:search <질문>` or `/km:search --deep <질문>`"
  → "예시: `/km:search MCP란?` | `/km:search --deep 프롬프트 엔지니어링 기법 비교`"
  → 종료

### 플래그 파싱
- `--quick` 또는 `-q` → **QUICK** (플래그 제거 후 나머지가 query)
- `--deep` 또는 `-d` → **DEEP** (플래그 제거 후 나머지가 query)
- `--no-moc` → MOC 제외, 원자 노트 전용
- 플래그 없음 → **AUTO**

### AUTO 라우팅
- DEEP: 문장형 5단어+, "~하려면/방법/비교/차이/관계/영향", 분석 요청("설명해줘/정리해줘"), 복수 개념("A vs B"), 방법론("어떻게/왜")
- QUICK: 그 외 (키워드 1-3개, 정의형 "~란?", 노트 찾기)

판정 직후 KM_MODE를 QUICK 또는 DEEP로 할당하고 실행(AUTO는 최종값 아님):
```bash
echo "KM_MODE=${KM_MODE}"
```
검색 시작마다 이전 KM_MODE·VAULT_MODE·KM_HITS를 버린다. 아래 마커는 실제 판정값만 출력한다. Bash 호출이 나뉘면 직전 stdout에서 관측한 값을 다음 호출에 명시적으로 재할당한다(셸 변수 지속 가정 금지). 영수증에는 이 검색에서 출력한 동일값을 넘긴다; 미관측 값은 인자를 생략한다.


## Phase 0.4: 구조 문서 축 (000-START-HERE)

셋업이 만든 3문서(`START-HERE`·`VAULT-STRUCTURE`·`MOC-Map`)는 **Tier 1 정합 확인 또는 실패 후 본문 근거 확보 전에 먼저 참조**한다 — 있으면 `MOC-Map` 을 Read(≤130줄)해서 질문을 허브에 매핑한 뒤 검색에 들어간다.
입력 변수는 `VAULT_PATH` 와 `QUERY_KEYWORDS`(핵심 키워드 1~3개, 공백 구분) 둘이고, 아래 블록은 그대로 실행할 수 있다.

```bash
STRUCT_DIR="${VAULT_PATH}/000-START-HERE"; STRUCT_DOCS=0; STRUCT_MISSING=""
for f in START-HERE VAULT-STRUCTURE MOC-Map; do
  if [ -f "$STRUCT_DIR/$f.md" ]; then STRUCT_DOCS=$((STRUCT_DOCS+1)); else STRUCT_MISSING="$STRUCT_MISSING $f"; fi
done
echo "STRUCT_DOCS=${STRUCT_DOCS}/3 missing=[${STRUCT_MISSING# }]"
# 허브 매핑: MOC-Map 앞 130줄에서 허브마다 «겹친 키워드 수»를 세어 많은 순 ≤3 · 동점 = 지도 위쪽(먼저 나온) 순
# 키워드는 awk 안에서 쪼갠다(zsh 는 $QUERY_KEYWORDS 를 안 쪼갬) · 대소문자 무시 글자 그대로 비교(정규식 ❌) · 허브명은 줄 단위(공백 든 이름 보존)
ROUTE_HUBS=""
if [ -f "$STRUCT_DIR/MOC-Map.md" ]; then
  ROUTE_HUBS="$(head -130 "$STRUCT_DIR/MOC-Map.md" | awk -v kws="$QUERY_KEYWORDS" '
    BEGIN { m = split(tolower(kws), T, " "); for (i = 1; i <= m; i++) if (!(T[i] in U)) { U[T[i]] = 1; K[++n] = T[i] } }
    { l = tolower($0); s = $0
      while (match(s, /\[\[[^]|#]*/)) { h = substr(s, RSTART + 2, RLENGTH - 2); s = substr(s, RSTART + RLENGTH)
        if (!(h in F)) F[h] = NR
        for (i = 1; i <= n; i++) if (index(l, K[i])) M[h SUBSEP i] = 1 } }
    END { for (h in F) { c = 0; for (i = 1; i <= n; i++) if ((h SUBSEP i) in M) c++; if (c) printf "%d\t%d\t%s\n", c, F[h], h } }' \
    | sort -t "$(printf '\t')" -k1,1nr -k2,2n | head -3 | cut -f3)"
fi
ROUTE_HUB_COUNT=$(printf '%s\n' "$ROUTE_HUBS" | awk 'NF' | wc -l | tr -d ' ')
echo "ROUTE_HUBS=[$(printf '%s\n' "$ROUTE_HUBS" | awk 'NF' | paste -sd '|' - | sed 's/|/ | /g')] count=${ROUTE_HUB_COUNT}"
```

- `STRUCT_DOCS` 가 3 미만이면 답변에 「구조 문서 없음(<빠진 것>) — `/km:setup` 재실행으로 생성」 1줄을 적고 **그대로 계속 진행**한다(멈춤 ❌).

## Phase 0.5: MOC 우선 라우팅

검색 결과 중 MOC 성격 노트(frontmatter `type`/`tags`에 MOC 포함, 또는 파일명에 `-MOC`)를 최상위로 고정한다:
0. `000-START-HERE/` 의 3문서가 결과에 있으면 파일명 축으로 MOC 로 «즉시» 분류하고, Phase 0.4 의 `ROUTE_HUBS` 를 📌 최상단 고정 후보에 합류시킨다.
1. 결과를 MOC / 원자 노트로 분류
2. 상위 최대 3개 MOC를 맨 위로 고정 (점수 순)
3. 원자 노트는 그 아래 점수 순
4. 표시: `📌 상위 MOC (N)` 섹션 + `📄 원자 노트 (N)` 섹션 분리 (MOC 0개면 📌 생략)

> Why: 노트가 많아질수록 원자 나열은 찾기 어려움 — MOC(지도 노트)가 허브·진입점 역할.

## Phase 0.6: 대상 고정(target binding) (1.8.1 · Tier 0/1 «앞»에서 1회)

Tier 2 의 0-β 분해 JSON 을 **여기서 먼저** 산출한다(스폰 ❌ · 이 스킬을 실행하는 모델 자신이 도구 호출 전에 JSON 1개). 스키마(참조 없이 생성):
```json
{"intent":"nav|content|relation|meta|tag|temporal|mixed","targets":["노트명 후보 ≤3, 확신순"],"keywords":["핵심어 ≤5"],"tags":["태그 ≤3, # 제거"],"props":{"key":"value"},"path_hint":"폴더 힌트 or null","time":{"recent":false,"date":null},"axes":["bl|ln|prop|ctx|tag|full 실행 순서"],"topn":2}
```
여기에 다음 2키를 더한다:
- `target_status`: `resolved`(대상 개체 ≥1 을 질문에서 «근거 있게» 뽑음) · `unspecified`(대상 없는 일반·개념·비교 질문 — 개체를 지어내지 않는다) · `ambiguous`(같은 이름이 2+ 노트·허브에 걸림 — 둘 다 유지하고 라벨).
- `target_provenance`: {대상: `quote|wikilink|tag|proper_noun|alias:<출처 경로>`} — 별칭(한↔영 표기 등)은 **공개 입력에서만** 얻는다: 질문 본문 · 검색 결과 노트의 frontmatter `title`/`aliases` · MOC-Map 허브명. 정답표·문항별 사전 ❌.
- 대상은 «선택 사항»이다: `unspecified` 면 아래 티어를 원문 질의 그대로 진행한다(중단 ❌).
- 이 JSON 을 답변 앞머리에 1회 출력한다(`KM_SEARCH_RUN_DIR` 환경변수가 있으면 그 폴더의 `decomp.json` 에도 기록).
- 셸 변수 매핑: TARGET_STATUS ← target_status · TARGETS ← targets 배열을 공백으로 결합 · KEYWORDS_TOP ← keywords 앞 3개를 공백으로 결합(Tier 1 의 T1_QUERY 가 이 세 값을 쓴다).



## Tier 0 — 메모리뱅크 축 (v1.8.0 · 2026-09-14 · 재경님 1548711800 「우리 판 km:search 는 메모리뱅크도 함께 봐야」)

Tier 1 «앞에» 같은 질의로 과거 대화·결정 경위를 1회 조회한다(memory.md 축⑥: 과거 경위 = 메모리뱅크 / 현재 정본 = vault). 결과는 vault 결과와 **합치지 않고** 별도 절 `🧠 메모리뱅크 (과거 대화)` 에 ≤3건 병기, 각 줄 라벨 `[mb]`. CLI 부재·오류·0건 = 1줄 표기 후 **그대로 계속**(멈춤 ❌ · Tier 1 결과 불변).

```bash
MB_CLI="$(ls -d "$HOME/.claude/plugins/cache/memory-bank-dev/memory-bank"/*/cli/memory-bank.js 2>/dev/null | sort -V | tail -1)"
MB_OUT=""; MB_STATE=absent; MB_HITS=0
if [ -n "$MB_CLI" ]; then
  MB_OUT="$(node "$MB_CLI" search "${QUERY}" --limit 3 2>/dev/null | grep -vE '^(Loading|Embedding)')" && MB_STATE=ok || MB_STATE=error
  MB_HITS=$(printf '%s\n' "$MB_OUT" | grep -cE '^[0-9]+\. \[' || true)
fi
echo "MB_STATE=${MB_STATE} mb_hits=${MB_HITS}"
```
- 출력 규약: `[mb] <프로젝트, 날짜> — <첫 문장 ≤80자> (<jsonl 경로>:<Lines>)` ≤3줄. 메모리뱅크 히트는 «과거 경위»이지 현재 정본이 아니다 — 사실 주장은 vault 결과(Tier 1~4)가 이기고, 「왜 그렇게 결정했나·전에 어떻게 했나」 질문은 [mb] 가 1순위(memory.md 「주입 ≠ 조회 · 조회가 이김」과 동축).
- 마커: 답변 마지막 티어 줄에 `+ 메모리뱅크(<MB_STATE>·<MB_HITS>건)` 병기. 부재 단정 발화 전엔 [mb] 0건도 함께 적는다(두 코퍼스는 서로 부재를 증명하지 않는다).


## 검색 엔진 — 4단계 자동 폴백 (Tier 0 뒤)

### Tier 1 — GraphRAG 서버 (설치된 경우, 의미 기반 하이브리드 검색)
resolved는 대상+핵심어 ≤7단어, unspecified는 원문.
```bash
T1_QUERY="${QUERY}"
[ "${TARGET_STATUS:-unspecified}" = "resolved" ] && [ -n "${TARGETS:-}" ] && T1_QUERY="${TARGETS} ${KEYWORDS_TOP:-}"
[ -n "${KM_SEARCH_RUN_DIR:-}" ] && printf 'target_status=%s\nquery=%s\n' "${TARGET_STATUS:-unspecified}" "${T1_QUERY}" > "${KM_SEARCH_RUN_DIR}/tier1-query.txt"
QUERY_ENCODED=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "${T1_QUERY}")
gr_fetch() { curl -s -w '\n%{http_code}' --connect-timeout 3 --max-time 60 \
"$1/api/search?q=${QUERY_ENCODED}&top_k=${TOP_K}&mode=hybrid"; }
_raw="$(gr_fetch "${SEARCH_ENDPOINT}")"; TIER1_RC=$?
TIER1_CODE="${_raw##*$'\n'}"
TIER1_JSON="${_raw%$'\n'*}"
if { [ $TIER1_RC -ne 0 ] || [ -z "$TIER1_JSON" ]; } \
&& [ "${SEARCH_ENDPOINT}" != "http://127.0.0.1:8400" ]; then
TIER1_JSON="$(gr_fetch http://127.0.0.1:8400)"; TIER1_RC=$?
if [ $TIER1_RC -eq 0 ] && [ -n "$TIER1_JSON" ]; then
ENDPOINT_SWITCHED="${SEARCH_ENDPOINT} → http://127.0.0.1:8400"
SEARCH_ENDPOINT="http://127.0.0.1:8400"
fi
fi
if   [ $TIER1_RC -eq 0 ] && [ "$TIER1_CODE" = "200" ] && [ -n "$TIER1_JSON" ]; then
GRAPHRAG_STATE=ok
elif [ $TIER1_RC -eq 0 ] && [ -n "$TIER1_CODE" ] && [ "$TIER1_CODE" != "200" ]; then
GRAPHRAG_STATE=misrouted
elif [ $TIER1_RC -eq 7 ]; then GRAPHRAG_STATE=absent
else GRAPHRAG_STATE=unreachable
fi
if [ "$GRAPHRAG_STATE" = "absent" ] && [ -r /proc/net/tcp ] \
&& [ "$(wc -l < /proc/net/tcp)" -le 1 ]; then
GRAPHRAG_STATE=blocked
fi
echo "GRAPHRAG_STATE=${GRAPHRAG_STATE} endpoint=${SEARCH_ENDPOINT} rc=${TIER1_RC}"
echo "ENDPOINT_SWITCHED=${ENDPOINT_SWITCHED:-none}"
```
- `GRAPHRAG_STATE=ok` → 결과 사용. 그 외 Tier 2+ **`GRAPHRAG_STATE` 유지**.
Tier 1 결과 파싱 직후 results 배열 길이를 출력한다. 오류/미파싱은 0건이 아니므로 마커를 내지 않는다:
```bash
unset KM_HITS
if [ "$GRAPHRAG_STATE" = "ok" ]; then
KM_HITS=$(printf '%s' "$TIER1_JSON" | python3 -c 'import json,sys; r=json.load(sys.stdin)["results"]; assert isinstance(r,list); print(len(r))') && echo "KM_HITS=${KM_HITS}"
fi
```

#### Tier 1 성공 계약 — 참조 없이 실행
- ok는 결과 사용, 그 외 Tier 2+로 상태 유지. 결과별 `target_hit=title|path|body|none`은 별칭 일치 위치의 관측값이며 관련성 정답이 아니다. 이름 일치만으로 채택하지 않는다.
- 표시명=`entity`; `source_note`는 있을 때만 vault 상대 경로. 빈 `description`은 근거가 아니다. 원문 전 검색당 1회 정합 판정: 첫 응답에서 source_note 하나의 `${VAULT_PATH}/{source_note}` **존재만** `[ -f ... ]`로 확인(Read 금지). 존재면 `VAULT_MODE=same`, 부재/경로 가진 결과 0건이면 `VAULT_MODE=other`. 판정 직후 실행:
```bash
echo "VAULT_MODE=${VAULT_MODE}"
```
- 이후 모든 절이 이 값을 따른다. 다른 vault 탐색·Obsidian 설정 대조 금지(Phase -1의 vaultPath 미설정 판정만 별개). `same`+source_note면 로컬 Read 허용. `other`는 로컬 파일·CLI 보강·경로 변환·vault/로컬 그래프 탐색 전부 0회; QUICK/DEEP·Phase 2.5도 서버 body만 근거로 쓴다.
- 양 모드 원문 조회: `curl -s "${SEARCH_ENDPOINT}/api/note?name=<entity>&max_chars=2500" --connect-timeout 3 --max-time 15`; max_chars=100~20000, 응답=`note_path`+`body`. other 답변 말미=`검색: GraphRAG 서버 (다른 vault 인덱스 — 서버 본문 기반)`. 사용자 vault 색인을 원하면 `/tofugraph build`를 이 vault에서 실행하도록 안내.
- note 실패(예:404)는 이름 변경 재시도 없이 entity·source_note·점수만 사용하고 `원문 미확보 — 서버 메타데이터 기반`을 명시. 멈추지 않는다.
- ENDPOINT_SWITCHED≠none이면 반드시 `⚠️ 원래 서버(<원주소>)가 응답하지 않아 <새주소> 로 검색했습니다 — 색인된 vault 가 다를 수 있습니다`와 source_note 한 건을 그대로 표시. 경로 접두어는 vault 식별자가 아니다.
- `--max-time 60`: 냉시작 지연 때문에 connect-timeout만으로 부족하다. 조정 시 관측 정상 시간보다 넉넉히 잡는다. `/health` 200으로 검색 정상을 판단하지 않는다.
- 서버 미기동/미설치면 조용히 Tier 2; `/tofugraph`로 구축하면 자동 사용. 질의는 3~7단어 권장(문장도 허용); 빈손이어도 동일 질의 재시도 금지. 별칭·한/영 등 표현을 1회 바꾸고 다음 티어로 간다.

#### Tier 1-S — 신선도 보강 (v1.5.1 · P2 · 서버 무변경 · Tier 1 결과 불변)
Tier 1 이 `GRAPHRAG_STATE=ok` 로 끝난 «직후» 1회 실행한다. 색인 세대 밖(최근 생성·수정) 노트를 «부재»로 읽지 않기 위한 완충 — Tier 1 결과에 없는 최근 노트를 Tier 2 명령으로 «보강»한다(폴백 아님).
```bash
STALE_MIN="${KM_SEARCH_STALE_MIN:-40}"   # 증분 색인 주기(30분)+빌드 여유. 운영 우회 키와 공유 ❌
FIN=$(curl -s --connect-timeout 3 --max-time 3 "${SEARCH_ENDPOINT}/health" | python3 -c 'import sys,json
try: print(json.load(sys.stdin)["index_update"].get("finished_at") or "")
except Exception: print("")')
AGE_MIN=$(python3 -c 'import sys,datetime
f=sys.argv[1]
if not f: print(99999); sys.exit()
t=datetime.datetime.fromisoformat(f); print(int((datetime.datetime.now(t.tzinfo)-t).total_seconds()//60))' "$FIN")
RECENT=0; printf '%s' "${QUERY}" | grep -qE "오늘|어제|최근|이번 주|방금|$(date +%Y-%m-%d)|$(date -v-1d +%Y-%m-%d 2>/dev/null || date -d yesterday +%Y-%m-%d)" && RECENT=1
FRESH_CLI="${OBSIDIAN_CLI:-/Applications/Obsidian.app/Contents/MacOS/obsidian-cli}"
if [ "$GRAPHRAG_STATE" = "ok" ] && [ "$AGE_MIN" -gt "$STALE_MIN" ]; then
  echo "⚠ 색인 나이 ${AGE_MIN}분(finished_at ${FIN:-없음}) — 그 이후 생성·수정된 노트는 Tier 1 결과에 없음"
fi
# CLI 질의 이스케이프: Obsidian 검색은 `낱말:`·`14:26`·`https:` 를 연산자로 읽어 `Error: Operator "X" not recognized`(rc 0)로 끝난다
KM_CLI_Q="${CLAUDE_PLUGIN_ROOT:-}/scripts/km_cli_query.py"
[ -f "$KM_CLI_Q" ] || KM_CLI_Q="$(find "$HOME/.claude/plugins/cache/knowledge-manager" -name km_cli_query.py 2>/dev/null | sort | tail -1)"
cliq() { if [ -f "$KM_CLI_Q" ]; then python3 "$KM_CLI_Q" "$1"; else printf '%s' "$1" | sed -E 's/([^[:space:]"]):([[:space:])]|$)/\1\2/g'; fi; }
FRESH_JSON=""
if [ "$GRAPHRAG_STATE" = "ok" ] && { [ "$AGE_MIN" -gt "$STALE_MIN" ] || [ "$RECENT" = 1 ]; } && [ -x "$FRESH_CLI" ]; then
  # 질의 = Phase 0.6 키워드 앞 2개(CLI 는 낱말 전부 일치라 문장형은 「No matches」가 정상 — 실측 25/26) · 키워드가 비면 원문
  FRESH_Q="$(printf '%s' "${KEYWORDS_TOP:-}" | awk '{print $1, $2}' | sed 's/ *$//')"; [ -n "$FRESH_Q" ] || FRESH_Q="${QUERY}"
  FRESH_RAW="$("$FRESH_CLI" search query="$(cliq "${FRESH_Q}")" format=json limit=20 2>/dev/null)"
  # JSON 배열 1건+ 일 때만 보강으로 인정(오류 문자열·「No matches found.」 도 비어 있지 않아 예전엔 yes 로 찍혔다)
  FRESH_JSON="$(printf '%s' "$FRESH_RAW" | python3 -c 'import sys,json
try:
    r=json.load(sys.stdin); print(json.dumps(r, ensure_ascii=False) if isinstance(r,list) and r else "")
except Exception: print("")')"
  [ -z "$FRESH_JSON" ] && [ -n "$FRESH_RAW" ] && echo "FRESH_CLI_OUT=$(printf '%s' "$FRESH_RAW" | head -1 | cut -c1-80)"
fi
echo "FRESH: age=${AGE_MIN}m recent=${RECENT} supplement=$([ -n "${FRESH_JSON:-}" ] && echo yes || echo no)"
```
- `FRESH_JSON` 이 있으면 Tier 1 결과에 «없는» 경로만 골라 상위 5개를 `[fresh:cli]` 라벨로 Tier 1 결과 **아래**에 덧붙인다(Tier 1 순위 재배열 ❌). 두 조건 다 거짓이면 출력은 `FRESH:` 1줄뿐 = 현행과 동일.
- Tier 1 top5 중 `source_note` 결손 3+ → `⚠ source_note 결손 N/5` 1줄 병기.
- 근거: vault `100-project/2026-09-01-graphrag-search-quality/25-p2-km-freshness-design-v0.md` §2 · 선례 `080-Bug-Reports/2026-09-01-graphrag-recent-doc-search-failure.md` §5 P2.

#### Tier 1-T — 대상 보강 (1.8.1 · Tier 1 결과 불변 · 1회)
  - 조건: `target_status=resolved` 이고 Tier 1 top10 의 target_hit 가 전부 `none` 이면 **보강 질의 1회**
  - 동작: `q = <targets> + <keywords 앞 3>`(Tier 1 질의와 같은 대상 고정 — 핵심어만 앞 3개로 축소) 로 같은 `/api/search` 를 다시 호출해 Tier 1 결과에 «없는» 경로만 `[target]` 라벨로 Tier 1 결과 **아래**에 덧붙인다(순위 재배열 ❌). 추가로 대상이 (a) MOC-Map `ROUTE_HUBS` 의 허브면 그 허브의 outlink ≤15 (b) vault 폴더명과 일치하면 그 폴더 하위 md ≤15 를 `[target:hub]`/`[target:folder]` 라벨로 덧붙인다. 보강으로 들어온 후보는 «후보» 일 뿐 채택은 본문 근거로 판단한다.
  - 기록: `KM_SEARCH_RUN_DIR` 가 있으면 그 폴더의 `target-boost.json` 에도 기록: {targets, tier1_target_hit_n, requery, added:[{path,label}]}.

#### Tier 1-R — 규칙 코퍼스 보강 (S3 · 서버 무변경 · Tier 1 결과 불변 · 1회)
운영 규율·스킬·봇 레지스트리 질문의 정본은 vault 노트가 아니라 repo 루트 규칙 코퍼스(예: `docs/rules-*`·`.claude/rules`·`.claude/skills/*/SKILL.md`)에 있다 — Tier 1(색인 = vault .md)도 Tier 2(CLI = 열린 vault)도 닿지 않는다. km-config `search.ruleCorpus`(root·index·globs·top)가 있을 때만 실행, 없으면 `RULES: off` 1줄 = 현행과 동일. **실행 시점** = Tier 1 이 `ok` 면 Tier 1-S·1-T 뒤 1회 · Tier 1 이 실패(`absent|unreachable|blocked|misrouted`)면 Tier 2 들어가기 «전» 1회(서버와 무관한 로컬 축이라 서버가 죽었을 때도 돈다). `other` 만 건너뛴다.
```bash
KM_RULES="${CLAUDE_PLUGIN_ROOT:-}/scripts/km_rules_route.py"
[ -f "$KM_RULES" ] || KM_RULES="$(find "$HOME/.claude/plugins/cache/knowledge-manager" -name km_rules_route.py 2>/dev/null | sort | tail -1)"
# 문 = 영수증 VL_HITS 와 같은 모양: other → 건너뜀 · same 또는 Tier 1 실패 → 실행 · 그 밖(미관측) → 건너뜀
if [ "${VAULT_MODE:-}" = other ]; then echo "RULES: skip(vault_mode=other)"
elif ! { [ "${VAULT_MODE:-}" = same ] || [[ "${GRAPHRAG_STATE:-}" =~ ^(absent|unreachable|blocked|misrouted)$ ]]; }; then echo "RULES: skip(vault_mode=${VAULT_MODE:-미관측} graphrag=${GRAPHRAG_STATE:-미관측})"
elif [ -f "$KM_RULES" ]; then python3 "$KM_RULES" --config "./km-config.json" --config "${VAULT_PATH}/km-config.json" --query "${QUERY}" --keywords "${KEYWORDS_TOP:-}"; else echo "RULES: helper 없음"; fi
```
- 출력 `[rules:index]`(INDEX 트리거 표 겹침 → 그 rule 의 core·full 쌍) · `[rules:rg]`(코퍼스 낱말 겹침) 줄을 Tier 1 결과 **아래** 별도 절 `📐 규칙 코퍼스 (N)` 로 붙인다(Tier 1 실패 경로면 Tier 2~4 결과 아래 · 순위 재배열 ❌ · ≤5 · `other` 가 아니면 항상 실행 — 질의 내용으로 거르는 문 열기 조건 없음). 후보일 뿐 — 채택은 원문 Read 근거로, 읽은 경로는 출처에 그대로 적는다(vault 노트 아님을 경로로 구분). **읽기 예산(기본 3)은 늘리지 않는다** — 이 절의 경로를 Read 하면 그 3 안에서 센다.
- 정답표·문항별 사전 ❌(Phase 0.6 과 같은 선) — 코퍼스는 «원칙»으로 정한다: 규칙·스킬·공용 레지스트리 정본. 봇 작업 폴더(`agent-*/out` 등)는 넣지 않는다.

**other 보호:** Tier 1-S의 로컬 CLI 보강 및 Tier 1-T의 로컬 hub/folder 탐색은 `VAULT_MODE=same`일 때만 실행한다. `other`에서는 서버 질의·서버 body만 허용한다. Tier 1-R 의 로컬 코퍼스 읽기는 `VAULT_MODE=same` 또는 Tier 1 실패 뒤에만 실행한다 — `other` 에선 0회(블록 첫 줄이 `RULES: skip` 으로 막는다).

### Tier 2 — Obsidian CLI
Tier 1 실패/불충분 시: `tier2-struct-prelude.txt` → `tier2-cli.txt` 순 Read 후 실행. Tier 1 «실패»(ok 아님)면 그 전에 위 Tier 1-R 블록을 1회 실행한다(이 줄을 Tier 1 성공 경로에선 다시 돌리지 않는다).

### Tier 3 — Obsidian MCP
Tier 2 실패 시 `search-references/tier3-mcp.txt` Read 후 MCP 검색.

### Tier 4 — 텍스트 검색
Tier 3 불가 시 `search-references/tier4-text.txt` Read. `GRAPHRAG_STATE`별 폴백 문구 필수.

### 모드·읽기 예산
- **primary evidence reads 기본 = 3** (명시 `--quick`/얕은 질의 1-2 · DEEP·requirements 미충족 ≤5).
- top_k: QUICK 5 / DEEP 10. QUICK 정상 성공은 아래 인라인 형식을 사용한다. DEEP일 때만 `search-references/modes-output.txt` Read(요구항목 커버리지·읽기 중단 규칙 포함).

### 성공 근거·QUICK 출력 — 참조 없이 실행
### A. frontmatter 구조 신호 (읽는 모든 노트 공통)
노트를 Read 하면 본문 전에 frontmatter 를 먼저 해석한다:
- `aliases:` → **재질의 사전**: 1차 검색이 0건·빈약하면 별칭(영/한 표기 변형)으로 1회 재검색.
- `tags:` · `type:` → MOC/허브 판정(Phase 0.5 입력) + 답변의 분류 근거.
- `related:` · `parent:` · 본문 `[[링크]]` → 추가 Read 후보. **MOC·허브로 «올라가는» 링크 우선**(주변 노트→정본 허브 도달이 목적 — 2026-07-13 벤치: 에이전트 검색은 주변 노트엔 도달하나 **허브에 못 가는 게 주 실패 모드**. Phase 0.5 입구 라우팅과는 다른 실패층: 0.5 = 처음부터 허브로, 여기 = 주변에 떨어졌을 때 위로 복귀 · v1.7.1). 개수는 아래 «링크 추적 예산» 안에서.

## QUICK 모드 — 즉답 (3-5줄)

상위 노트 원문 확보(primary reads 기본 3, QUICK 예외 1-2) → frontmatter + 핵심 섹션 추출. 원문 = Tier 1 이면 원문 확보 계약을 따른다(`VAULT_MODE=same`=로컬 Read · `other`=`/api/note` 의 `body`, 로컬 경로 접근 ❌). Tier 2~4 로 검색한 경우 = 로컬 Read.

```
**답변:**
[3~5줄 직접 답변. 노트 내용 기반.]

📌 **상위 MOC** (N)
1. **[[MOC 제목]]** — [범위·역할 한 줄] (`경로`)

📄 **원자 노트** (N)
1. **[노트 제목]** — [핵심 한 줄] (`경로`)
```

### Phase 2.5 — 조건부 로드
- `VAULT_MODE=other`는 전체 생략; 로컬 접근 0회.
- `same`의 DEEP, QUICK top hit 빈약, 검색 0건, lookup 제목 exact 0건, 또는 부재 문장을 쓸 경우에만 `search-references/phase-2.5-graph.txt` Read 후 A/B/C 해당 계약을 반드시 실행한다. 부재 3단 실행 및 lookup exact 0건 의무 줄 생략 금지.
- 정상 QUICK은 frontmatter 인라인 A만 적용. 링크 추가 Read ≤1, 총 ≤3. DEEP 추가 ≤3·총 ≤8, 허브로 올라가는 링크 우선. 기본 primary=3은 참조 Read와 별도.

## 제약

- **읽기 전용**: 노트 생성/수정 금지
- **hallucination 금지**: 반드시 실제 노트 내용 기반. 노트에 없는 내용은 "vault에 관련 자료가 없습니다" 명시 (Tier 1 에서는 `/api/note` 의 `body` 와 `source_note` 경로의 원문이 '실제 노트 내용'이다 — 둘 다 그 vault 노트에서 나온다. 로컬 원문 Read 는 경로가 실재할 때의 보강이지, Read 실패가 답변을 막는 게이트가 아니다)
- **출처 필수**: 실제 읽은 노트 경로 표기
- **사용 티어 명시 (형식 고정)**: 답변 마지막 줄은 정확히 이 형식으로 쓴다 — `검색: <티어명> + 구조 문서(<D>/3 참조 · 허브 <k>) + 그래프 확장(backlinks N)`. **D = Phase 0.4 의 `STRUCT_DOCS`, k = `ROUTE_HUB_COUNT`(둘 다 실측 정수)** · backlinks N = Phase 2.5-B backlink grep 결과 줄 수(실측 정수, 생략·"1-hop" 같은 서술 대체 ❌). 그래프 확장을 안 한 답변(QUICK 얕은 질의, 또는 Tier 1 `VAULT_MODE=other` 로 Phase 2.5 를 생략한 경우)은 `검색: <티어명> + 구조 문서(<D>/3 참조 · 허브 <k>)` 까지 허용.
- **질문/스킬/에이전트 스폰 금지**: 직접 검색만 수행 — 예외 1 = 0-β 분해(`--decomp=sub` 시 헤드리스 haiku 1회, 도구 0·질문 0), 그 외 스폰 ❌
- 상태 메시지 없이 바로 결과 출력 · Read 실패 시 다음 노트로
- QUICK: 5줄 이내 + 출처 1-2개 / DEEP: 제한 없음 + 출처 3-5개


## 부재·단정 확인 절차
부재·단정 발화 전에 실제 검색 증거 또는 `search checked: <top-hit-or-no-hit> | query="…"` 마커를 붙인다. top-hit/no-hit와 query는 실측값으로 대체하며 placeholder 금지. "볼트에 없다" 단정 전에는 `VAULT_MODE=same` 또는 Tier 1 실패 뒤 `bash .claude/scripts/vault-lookup.sh "${KEYWORD}"`를 vault 루트에서 1회 실행한다(3단 재질의와 별도). helper 부재·오류·실행 불가는 한계를 명시하고 확인된 범위만 답하며 볼트 전체 부재로 단정하지 않는다. `other`에서는 로컬 접근 0회 계약 때문에 helper 실행 금지; 다른 서버 인덱스의 검색 결과 한계만 말하고 사용자의 vault 전체 부재를 주장하지 않는다. no-hit도 실측 `search checked:` 마커와 영수증을 남긴다. 영수증 블록이 찍는 `VL_HITS`를 부재 단정 근거에 인용하되, 이는 helper 출력의 비어 있지 않은 줄 수(노트 히트 수 아님)이며 `skip`·`VL_UNAVAILABLE=1`·helper 부재의 0은 부재 증거가 아니다; 이 1회는 영수증 블록에서 수행하며 별도 선행 호출은 하지 않는다.

## 완료 전 게이트 — 모든 분기 공통
정상 성공 / 오류 폴백 / 낮은결과·부재 / 다른 vault / DEEP 모두: 실제 읽은 근거·제약·조건부 보강·의무 마커·아래 영수증을 확인 후 답한다. 영수증 수행 관측을 다른 봇의 시간 구간 기록으로 대체하지 않는다. 결과 0건도 영수증을 남긴다. 정상 성공에서 참조 없이 답한 것이 품질 통과를 뜻하지 않는다.
운영 단계 목표 ≤6: ①설정+모드+대상+Tier1 ②정합+memory+구조 ③원문 기본3 ④신선도/대상 보강 ⑤해당 조건의 확장/폴백/DEEP ⑥영수증+필수 마커. 단계는 관측치로 측정하고, 목표 때문에 조건별 계약·근거 읽기를 생략하지 않는다. 독립 셸 검사는 가능한 같은 Bash 호출에 묶되 Phase -1→Tier1 및 정합 이전 로컬 접근 금지 유지.

## 영수증 — 실행 기록 (v1.8.0 · 착수 게이트 입력 · 재경님 1548711722 「스킬 만든 이유가 없지 않나」)

답변을 출력하기 «직전» 1회 실행한다. 이 영수증이 없으면 착수 게이트(`.claude/hooks/km-onboarding-gate.py`, PreToolUse)가 이 세션의 `100-project/`·`deck-state/` 첫 쓰기와 02-progress 「착수」 기록을 막는다 — 안 쓰면 못 시작한다.

```bash
# helper만 폴백한다. 측정 명령 본문은 이 사본 그대로이며 설치본 캐시 탐색은 하지 않는다.
if [ "${VAULT_MODE:-}" = other ]; then VL_HITS=skip; elif [ "${VAULT_MODE:-}" = same ] || [[ "${GRAPHRAG_STATE:-}" =~ ^(absent|unreachable|blocked|misrouted)$ ]]; then VL_HITS=$(set -o pipefail; (set -f; set -- $(printf '%s' "${KEYWORDS_TOP:-$QUERY}"); VL_GIT="$(git rev-parse --show-toplevel 2>/dev/null)"; cd "${VAULT_PATH:?vaultPath required}" || exit 1; VL_H=.claude/scripts/vault-lookup.sh; [ -f "$VL_H" ] || VL_H="${VL_GIT:+$VL_GIT/.claude/scripts/vault-lookup.sh}"; [ -n "$VL_H" ] && [ -f "$VL_H" ] && bash "$VL_H" "$@") 2>/dev/null | command grep -c .) || { VL_HITS=${VL_HITS:-0}; echo "VL_UNAVAILABLE=1 — 부재 단정 금지"; }; else VL_HITS=skip; fi; echo "VL_HITS=${VL_HITS}"
RCPT=""
if [ -n "${CLAUDE_PLUGIN_ROOT:-}" ] && [ -f "$CLAUDE_PLUGIN_ROOT/scripts/km-search-receipt.py" ]; then
  RCPT="$CLAUDE_PLUGIN_ROOT/scripts/km-search-receipt.py"
elif [ -f "$HOME/obsidian-ai-vault/.claude/scripts/km-search-receipt.py" ]; then
  RCPT="$HOME/obsidian-ai-vault/.claude/scripts/km-search-receipt.py"
fi
MARKER_ARGS=()
[ -n "${KM_MODE:-}" ] && MARKER_ARGS+=(--km-mode "$KM_MODE")
[ -n "${VAULT_MODE:-}" ] && MARKER_ARGS+=(--vault-mode "$VAULT_MODE")
[ -n "${KM_HITS:-}" ] && MARKER_ARGS+=(--km-hits "$KM_HITS")
if [ -f "$RCPT" ]; then
  # 구형 vault helper는 신규 인자를 받지 않는다. 기존 영수증은 남기고 미지원은 표시한다.
  if ! python3 "$RCPT" --help 2>/dev/null | grep -q -- '--km-mode'; then
    MARKER_ARGS=()
    echo "KM_RECEIPT_MARKER_FIELDS=unsupported"
  fi
  python3 "$RCPT" --session-id "${CLAUDE_CODE_SESSION_ID:-${CODEX_COMPANION_SESSION_ID:-unknown}}" \
    --query "${QUERY}" --tiers-tried "mb:${MB_STATE:-skip},t1:${GRAPHRAG_STATE:-skip}" \
    --top-hit "<상위 1건 source_note 경로 또는 no-hit>" --n-hits <Tier 1~4 히트 수 정수> "${MARKER_ARGS[@]}"
else
  echo "영수증 생략: helper 파일 없음"
fi
```
- `VL_HITS`는 stdout 전용이며 신·구형 helper 모두 인자로 전달하지 않는다(저장 필드 미지원). 실행 전 이번 검색의 `VAULT_PATH`·`VAULT_MODE`·`GRAPHRAG_STATE`·`KEYWORDS_TOP`·`QUERY`를 관측값으로 재할당하며 미관측 상태는 skip, `other`는 실패 상태여도 skip이다.
- 마커 필드 `km_mode`·`vault_mode`·`km_hits`는 stdout과 동일; 미관측은 null. 구형 vault helper 폴백은 기존 스키마만 기록하므로 신규 3필드는 없고 `KM_RECEIPT_MARKER_FIELDS=unsupported`로 표시한다. `km_hits`는 Tier 1 반환 건수, 기존 `n_hits`는 Tier 1~4 최종 건수다.
- 영수증 = `~/.claude-state/km-search-receipts.jsonl` 1행(ts·session_id·bot·query·tiers_tried·top_hit·n_hits). no-hit 도 영수증이다(검색을 «했다»는 기록이지 «찾았다»는 기록이 아니다).
- 스킬을 거치지 않고 curl 만 던진 검색은 영수증이 없다 — 그건 게이트가 의도한 대로 막는다.

### 결과 없음
```
vault에서 "{query}" 관련 자료를 찾지 못했습니다.
(재질의 3단: ①"<축약어>" 0건 ②"<변형어>" 0건 ③[[언급]] 0건 — Phase 2.5-C 증빙 형식)
/knowledge-manager로 자료를 수집해보세요.
```

