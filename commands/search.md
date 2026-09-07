---
description: vault 통합 검색 — GraphRAG(있으면) → Obsidian CLI → Obsidian MCP → 텍스트 검색 4단계 자동 폴백. quick(즉답)/deep(분석) 자동 라우팅
allowedTools: Bash, Read, Glob, Grep, mcp__obsidian__*
---

# /km:search — vault 통합 검색

$ARGUMENTS

> **핵심 설계**: 검색 창구는 이 명령 하나입니다. 뒤에서 어떤 검색 엔진이 도는지는 자동으로 결정됩니다 —
> **① GraphRAG 서버(설치돼 있으면) → ② Obsidian CLI → ③ Obsidian MCP → ④ 텍스트 검색** 순서로,
> 앞 단계가 없거나 실패하면 자동으로 다음 단계로 넘어갑니다. GraphRAG를 아직 설치하지 않았어도
> 이 명령은 그대로 동작합니다(②~④가 받아줍니다). 나중에 GraphRAG 스택을 얹으면 **같은 명령이 자동으로 ①을 쓰기 시작합니다.**

> **찾는 범위**: 이 명령은 **vault 안의 문서·개념·문서 사이 관계**를 찾습니다. 반면 *과거 대화에서 무슨 말이 오갔는지·어떤 결정이 왜 내려졌는지*는 성격이 다른 질문이라, 대화 기록을 따로 보관·검색하는 도구가 있다면 그쪽이 먼저입니다.
> 둘 다 봐야 하는 질문이라면 **지금 기준·현재 상태는 문서 쪽**, **원래 발언·결정 경위는 대화 기록 쪽**을 우선하세요. 두 결과가 어긋나면 감추지 말고 `현재 기준`과 `과거 경위`로 나눠 적는 편이 낫습니다.
> 그리고 **한쪽에서 안 나왔다고 다른 쪽에도 없다고 단정하지 마세요** — 서로 다른 코퍼스입니다.

> 🚨 **실행 순서 계약 (고정 — 첫 행동을 여기서 정한다)**: ① Phase -1 로 설정 2개(`VAULT_PATH`·`SEARCH_ENDPOINT`)를 읽는다 → ② **곧바로 Tier 1 서버 검색 curl 을 실행한다.** 이 ①② 보다 먼저 vault 파일을 검색·나열·읽기(rg / grep / find / ls / Read) ❌ — 검색의 1차 수단은 서버이고, 로컬 파일은 Tier 1 의 원문 확보 계약(`VAULT_MODE=same`)이 허용할 때 또는 Tier 1 이 실패로 판정된 뒤(Tier 2~4)에만 연다. "vault 를 확인해보겠다"며 로컬부터 뒤지는 첫 행동 = 이 계약 위반이다.


## Phase -1: 설정 읽기

1. `km-config.json`을 찾는다 (현재 폴더 → 플러그인 설치 시 setup이 만든 위치 순).
2. `storage.obsidian.vaultPath` → `VAULT_PATH`. 없으면 사용자에게 vault 경로를 1회 묻고 진행.
   - **추측 금지**: 설정이 없을 때 그럴듯한 경로를 스스로 골라 검색하면 **낡은 사본에서 답하고도 출처가 붙어 있어** 사용자가 오류를 알아챌 수 없다(실측 사례: 백업 사본 17,923개 md 를 라이브 vault 로 착각). 반드시 묻는다.
   - **"진짜 쓰는 vault" 판정은 추측·후보 순회가 아니라 Obsidian 자기 설정으로 한다** (⚠️ km-config 에 `vaultPath` 가 이미 있으면 아래 판정을 실행하지 않는다 — 그 값이 정답) — `obsidian.json` 에서 `"open": true` 인 항목이 사용자가 실제로 열어 두는 vault 다. 백업 사본·형제 폴더도 `.obsidian` 을 갖고 있어서 그것만으론 안 갈린다.
     ```bash
     # 경로를 직접 짚는다 — 넓은 find 로 훑지 말 것(/mnt/c/Users 전수 탐색은 느리고 빈손으로 끝난다).
     OBSIDIAN_JSON=$(ls -1 \
       "$HOME/Library/Application Support/obsidian/obsidian.json" \
       /mnt/c/Users/*/AppData/Roaming/obsidian/obsidian.json \
       "$APPDATA/obsidian/obsidian.json" 2>/dev/null | head -1)
     python3 -c 'import json,sys;d=json.load(open(sys.argv[1]))["vaults"];print("\n".join(v["path"] for v in d.values() if v.get("open")))' "$OBSIDIAN_JSON"
     ```
     WSL 에서는 이 값이 윈도우 경로(`C:\Users\...`)로 나온다 — `wslpath -u` 로 바꿔 쓴다.
     이 파일이나 `"open": true` 항목을 못 찾았을 때만 사용자에게 묻는다.
   - 사용자가 준 경로도 한 번 검증한다 — `.obsidian` 폴더 존재, 최근 수정된 md 유무. 둘 다 아니면 그 경로를 쓰기 전에 다시 확인한다.
3. `obsidianCli.path` → `OBSIDIAN_CLI` (비어 있으면 아래 Tier 2의 자동 감지 사용).
   `obsidianCli.vault` → `OBSIDIAN_VAULT` (비어 있으면 `storage.obsidian.vaultPath` 의 basename)
4. `SEARCH_ENDPOINT` = `linking.semantic_adapter.endpoint` → 환경변수 `GRAPHRAG_API_URL` → 기본값 `http://127.0.0.1:8400` 순. **미설정이어도 기본값을 탐침한다** — 로컬에 서버가 없으면 즉시 연결 거부로 끝나 지연이 거의 없고(`--connect-timeout 3`은 상한일 뿐), 덕분에 나중에 `/tofugraph build`로 스택을 얹으면 설정 변경 없이 같은 명령이 자동으로 Tier 1을 쓰기 시작한다.

   ```bash
   # 필수 실행(집행 계약): endpoint 는 반드시 아래 셸 할당으로 결정하고, echo 로 확인한 뒤 Tier 1 을 호출한다.
   # CONFIG_ENDPOINT = km-config.json 의 linking.semantic_adapter.endpoint 값 (없으면 빈 값 유지)
   SEARCH_ENDPOINT="${CONFIG_ENDPOINT:-${GRAPHRAG_API_URL:-http://127.0.0.1:8400}}"
   echo "SEARCH_ENDPOINT=${SEARCH_ENDPOINT}"
   ```

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

## Phase 0.4: 구조 문서 축 (000-START-HERE)

셋업이 만든 3문서(`START-HERE`·`VAULT-STRUCTURE`·`MOC-Map`)는 **어느 티어든 본 검색 전에 먼저 참조**한다 — 있으면 `MOC-Map` 을 Read(≤130줄)해서 질문을 허브에 매핑한 뒤 검색에 들어간다.
입력 변수는 `VAULT_PATH` 와 `QUERY_KEYWORDS`(핵심 키워드 1~3개, 공백 구분) 둘이고, 아래 블록은 그대로 실행할 수 있다.

```bash
STRUCT_DIR="${VAULT_PATH}/000-START-HERE"; STRUCT_DOCS=0; STRUCT_MISSING=""
for f in START-HERE VAULT-STRUCTURE MOC-Map; do
  if [ -f "$STRUCT_DIR/$f.md" ]; then STRUCT_DOCS=$((STRUCT_DOCS+1)); else STRUCT_MISSING="$STRUCT_MISSING $f"; fi
done
echo "STRUCT_DOCS=${STRUCT_DOCS}/3 missing=[${STRUCT_MISSING# }]"
# 허브 매핑: MOC-Map 앞 130줄의 표 행에서 질의 키워드와 겹치는 [[허브]] ≤3
ROUTE_HUBS=""
if [ -f "$STRUCT_DIR/MOC-Map.md" ]; then
  for kw in $QUERY_KEYWORDS; do
    ROUTE_HUBS="$ROUTE_HUBS $(head -130 "$STRUCT_DIR/MOC-Map.md" | grep -i -- "$kw" | grep -o '\[\[[^]|#]*' | sed 's/^\[\[//')"
  done
  ROUTE_HUBS="$(echo $ROUTE_HUBS | tr ' ' '\n' | awk 'NF' | sort -u | head -3 | tr '\n' ' ')"
fi
ROUTE_HUB_COUNT=$(echo $ROUTE_HUBS | wc -w | tr -d ' ')
echo "ROUTE_HUBS=[${ROUTE_HUBS% }] count=${ROUTE_HUB_COUNT}"
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

## 검색 엔진 — 4단계 자동 폴백

### Tier 1 — GraphRAG 서버 (설치된 경우, 의미 기반 하이브리드 검색)
```bash
QUERY_ENCODED=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "${QUERY}")

# --max-time 필수: 서버가 "죽은 게 아니라 막힌" 상태면 연결은 성공하므로
# --connect-timeout 은 걸리지 않는다(무한 대기). 실측 근거는 아래 주석 참조.
gr_fetch() { curl -s -w '\n%{http_code}' --connect-timeout 3 --max-time 20 \
  "$1/api/search?q=${QUERY_ENCODED}&top_k=${TOP_K}&mode=hybrid"; }

_raw="$(gr_fetch "${SEARCH_ENDPOINT}")"; TIER1_RC=$?
TIER1_CODE="${_raw##*$'\n'}"   # 마지막 줄 = http_code
TIER1_JSON="${_raw%$'\n'*}"    # 그 앞 전체 = 본문

# 설정된 곳이 원격(다른 기계)일 수 있다. 거기가 안 되면 로컬 서버를 한 번 더 두드린다.
if { [ $TIER1_RC -ne 0 ] || [ -z "$TIER1_JSON" ]; } \
   && [ "${SEARCH_ENDPOINT}" != "http://127.0.0.1:8400" ]; then
  TIER1_JSON="$(gr_fetch http://127.0.0.1:8400)"; TIER1_RC=$?
  if [ $TIER1_RC -eq 0 ] && [ -n "$TIER1_JSON" ]; then
    ENDPOINT_SWITCHED="${SEARCH_ENDPOINT} → http://127.0.0.1:8400"
    SEARCH_ENDPOINT="http://127.0.0.1:8400"
  fi
fi

# 폴백 문구를 가르기 위한 상태 판정 — curl exit code 가 병명을 가른다.
#   7  = 연결 거부  → 서버가 없다      (absent)
#   28 = 시한 초과  → 서버는 있는데 막혔다 (unreachable)
# v1.1 (2026-09-01): HTTP 상태코드 축 추가. 404 는 curl exit=0 이고 본문도
# 비어있지 않아(`{"detail":"Not Found"}`) 구 판정식에서 «ok» 로 분류됐고, 이후 파싱에서
# results 부재 → 「no-hit」으로 둔갑했다(폴백조차 안 탐). 경로 오류를 misrouted 로 가른다.
if   [ $TIER1_RC -eq 0 ] && [ "$TIER1_CODE" = "200" ] && [ -n "$TIER1_JSON" ]; then
  GRAPHRAG_STATE=ok
elif [ $TIER1_RC -eq 0 ] && [ -n "$TIER1_CODE" ] && [ "$TIER1_CODE" != "200" ]; then
  GRAPHRAG_STATE=misrouted
elif [ $TIER1_RC -eq 7 ];                          then GRAPHRAG_STATE=absent
else                                                    GRAPHRAG_STATE=unreachable
fi

# 네 번째 상태: 이 세션 자체의 네트워크가 막힌 경우(에이전트 샌드박스 등).
# 겉모습이 rc=7(연결 거부)이라 "서버 없음"과 구별되지 않는다 — 여기서 갈라 주지 않으면
# 서버가 멀쩡히 돌고 있는데 사용자에게 "미설치"라고 답하게 된다(2026-07-27 실측).
# 판별: 격리된 네트워크 네임스페이스는 /proc/net/tcp 가 헤더뿐이다(호스트=94줄 · 샌드박스=1줄 실측).
if [ "$GRAPHRAG_STATE" = "absent" ] && [ -r /proc/net/tcp ] \
   && [ "$(wc -l < /proc/net/tcp)" -le 1 ]; then
  GRAPHRAG_STATE=blocked
fi
echo "GRAPHRAG_STATE=${GRAPHRAG_STATE} endpoint=${SEARCH_ENDPOINT} rc=${TIER1_RC}"
echo "ENDPOINT_SWITCHED=${ENDPOINT_SWITCHED:-none}"
```
- `GRAPHRAG_STATE=ok` → 이 티어 결과를 쓴다. 그 외 → Tier 2로 내려가되 **상태값을 들고 간다**(Tier 4 표시 문구가 이 값으로 갈린다).
- **원문 확보 계약 (Tier 1 전용 — 멈춤 금지)**: 검색 응답에 노트 경로 필드는 따로 없다 — 표시명은 `entity`, `source_note` 는 채워져 있을 때만 vault 상대 경로다(`description` 은 비어 있을 수 있으니 근거로 지목하지 말 것). **원문을 읽기 전에 아래 0단 판정을 검색당 1회만 하고, 그 결과(`VAULT_MODE`)를 이후 모든 절이 따른다.** 어느 단계에서도 그 밖의 다른 vault 를 뒤지거나 Obsidian 설정(obsidian.json)과의 대조를 시도하지 말 것 — 무한 "대조 중" 멈춤의 원인이다. (Phase -1 의 obsidian.json vault 판정은 별개 — 그건 VAULT_PATH 가 설정에 없을 때의 설정 단계 1회다.)
  0. **vault 정합 판정 (검색당 1회 — 이 판정 전에는 로컬 노트를 열지 않는다)**: 첫 응답에서 `source_note` 가 있는 결과 하나를 골라 `${VAULT_PATH}/{source_note}` 의 **파일 존재만** 확인한다(`[ -f ... ]` 1회 — Read ❌).
     - 존재 → **`VAULT_MODE=same`** (서버 = 이 vault. 로컬 Read 허용)
     - 부재, 또는 `source_note` 가진 결과가 0건 → **`VAULT_MODE=other`** (서버는 다른 vault 를 인덱싱 중 — 예: 강의용 샘플 인덱스, 다른 폴더에서 build 한 인덱스). **이후 이 검색의 모든 단계에서 로컬 파일 접근·경로 변환(wslpath 등)·vault 탐색 = 0회.** 원문은 오직 `/api/note` 로 받는다 — QUICK/DEEP 의 "노트 원문 확보"와 Phase 2.5 도 전부 이 스위치를 따른다.
  1. (`same` 전용) `source_note` 가 있으면 `${VAULT_PATH}/{source_note}` 를 Read 한다 (기존 경로).
  2. (양 모드 공통) 원문이 필요하면 `curl -s "${SEARCH_ENDPOINT}/api/note?name=<entity>&max_chars=2500" --connect-timeout 3 --max-time 15` 로 조회한다(`max_chars` 는 100~20000) → 응답 = `note_path`(vault 상대 경로) + `body`(원문). **`other` 모드에서는 `body` 가 원문 근거의 전부다** — 그대로 인용해 답변한다(`body` 는 그 vault 노트의 실제 본문이므로 hallucination 금지 제약을 충족한다). 답변 말미 티어 표기 = `검색: GraphRAG 서버 (다른 vault 인덱스 — 서버 본문 기반)`. 사용자 vault 기준 인덱스를 원하면 "`/tofugraph build`를 이 vault에서 실행하면 서버가 이 vault를 검색 대상으로 제공합니다" 1줄을 덧붙인다.
  3. `/api/note` 가 실패하면(404 `note not indexed` — 엔티티는 그래프에 있으나 인덱싱된 원문이 없는 경우. 이름을 바꿔 재시도하지 말 것) → `entity`·`source_note`·점수만으로 답하되, 답변에 "원문 미확보 — 서버 메타데이터 기반" 한계를 명시한다.
- 🚨 **서버를 바꿔 탔으면 반드시 밝힌다.** 두 서버는 **서로 다른 vault 를 색인**하고 있을 수 있다(기계마다 자기 vault 를 색인한다). 조용히 전환하면 *다른 코퍼스에서 그럴듯한 답*이 나오고 사용자는 알아챌 수 없다 — Phase -1 의 "vault 경로 추측 금지"와 **같은 병**이다. `ENDPOINT_SWITCHED` 가 `none` 이 아니면 답변에 한 줄:
  `⚠️ 원래 서버(<원주소>)가 응답하지 않아 <새주소> 로 검색했습니다 — 색인된 vault 가 다를 수 있습니다`
- 전환했을 때는 결과의 `source_note` 경로를 **한 건 그대로** 함께 보여 준다 — 사용자가 "내 vault 가 맞나"를 눈으로 가릴 수 있게. ⚠️ 경로 앞부분이 vault 이름이라고 가정하지 말 것: 서버 설정에 따라 vault 이름으로 시작하기도 하고(`Tofu_LLM_Wiki/...`) vault 안 상대경로로 시작하기도 한다(`020-Library/...`) — 2026-07-27 두 서버 실측. 접두어는 힌트지 식별자가 아니다.
- **`--max-time 20` 의 근거(2026-07-27 실측)**: 정상 응답이 7.5초 걸린 경우가 있었고, 같은 서버가 30초를 넘겨 시한 초과한 경우도 있었다. 5초·3초로 잡으면 **멀쩡한 서버를 "없음"으로 만든다**. 환경별로 다르면 이 값을 조정하되, 관측된 정상 응답 시간보다 넉넉히 크게 잡는다.
- **`/health` 200 을 서버 정상의 근거로 쓰지 말 것** — `/health` 는 200 인데 `/api/search` 만 막히는 형태가 실제로 관측된다. 판정은 위처럼 **검색 경로 자체**로 한다.
- 서버 미기동/미설치 → 조용히 Tier 2로. (같은 플러그인의 `/tofugraph` 명령으로 GraphRAG 스택을 구축하면 이 티어가 자동으로 살아난다.)
- **질의 형식(참고)**: 의미 기반 검색이라 문장을 통째로 넣어도 받지만, **3~7단어 키워드형**이 무난하다. 빈손이어도 **같은 질의를 그대로 다시 던지지 말 것** — 결과가 바뀌지 않는다. 표현을 한 번 바꿔 보고(별칭·영/한 표기 변형 포함), 그래도 안 나오면 다음 티어로 넘어가는 편이 빠르다.

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
if [ "$GRAPHRAG_STATE" = "ok" ] && { [ "$AGE_MIN" -gt "$STALE_MIN" ] || [ "$RECENT" = 1 ]; } && [ -x "$FRESH_CLI" ]; then
  FRESH_JSON="$("$FRESH_CLI" search query="${QUERY}" format=json limit=20 2>/dev/null)"
fi
echo "FRESH: age=${AGE_MIN}m recent=${RECENT} supplement=$([ -n "${FRESH_JSON:-}" ] && echo yes || echo no)"
```
- `FRESH_JSON` 이 있으면 Tier 1 결과에 «없는» 경로만 골라 상위 5개를 `[fresh:cli]` 라벨로 Tier 1 결과 **아래**에 덧붙인다(Tier 1 순위 재배열 ❌). 두 조건 다 거짓이면 출력은 `FRESH:` 1줄뿐 = 현행과 동일.
- Tier 1 top5 중 `source_note` 결손 3+ → `⚠ source_note 결손 N/5` 1줄 병기.
- 근거: vault `100-project/2026-09-01-graphrag-search-quality/25-p2-km-freshness-design-v0.md` §2 · 선례 `080-Bug-Reports/2026-09-01-graphrag-recent-doc-search-failure.md` §5 P2.

#### Tier 2·3 공통 — 구조 문서 선실행 (본 검색 전에 1회)

```bash
# 3문서만 대상으로 같은 키워드 1회 선검색(CLI 가 있으면 CLI, 없거나 0 B 면 grep) → 히트 = 📌 고정
STRUCT_HITS=0
if [ -d "$STRUCT_DIR" ]; then
  for kw in $QUERY_KEYWORDS; do STRUCT_HITS=$((STRUCT_HITS + $(grep -il -- "$kw" "$STRUCT_DIR"/*.md 2>/dev/null | wc -l | tr -d ' '))); done
fi
echo "구조 문서: 참조함(${STRUCT_DOCS}/3 · 히트 ${STRUCT_HITS})"
# ROUTE_HUBS 각 MOC 의 outlink 를 후보에 추가(Phase 2.5-B 와 같은 grep)
for hub in $ROUTE_HUBS; do
  HUB_FILE="$(find "$VAULT_PATH" -name "$hub.md" -not -path '*/.*' | head -1)"
  [ -n "$HUB_FILE" ] && grep -o '\[\[[^]|#]*' "$HUB_FILE" | sed 's/^\[\[//' | sort -u | head -15
done
```
- Obsidian CLI 는 **앱 내장 경로 우선**(mac `/Applications/Obsidian.app/Contents/MacOS/obsidian-cli`) + `vault=<볼트 이름>` 을 명시한다.
- 출력이 0 B 인데 rc 가 0 이면 「도구가 순간 빈손」이므로 1회 재시도한다. 무결과 문구(≠0 B)일 때만 「없음」으로 판정한다.
- 미히트여도 위 `구조 문서: 참조함(…)` 줄은 반드시 표기한다 — 참조 «했음»의 증명이다.

### Tier 2 — Obsidian CLI (질문 분해 → 재조립 → 실행 · v1.7.0)
vault 이름 = km-config `obsidianCli.vault`(비면 `storage.obsidian.vaultPath` 의 basename) → `OBSIDIAN_VAULT`. **모든 CLI 호출에 `vault="${OBSIDIAN_VAULT}"` 를 붙인다**(기본 vault 가 테스트용 vault 일 수 있음).
**0-α 활성 vault 대조(1회)**: `"$OBSIDIAN_CLI" vault info=path` 실측값 ≠ `OBSIDIAN_VAULT` 의 경로(`"$OBSIDIAN_CLI" vaults verbose` 에서 이름→경로) 이면 `⚠ 활성 vault 불일치: <실측> (설정 <기대>)` 1줄 출력 후 계속 — CLI 의 `vault=` 인자는 search·backlinks·properties·tags 전부에서 무시되고 «앱에서 열린 vault» 로 동작한다(36 §8 ②).

**0-β 질문 분해(1.7.0 · 스폰 ❌ · 이 스킬을 실행하는 모델 자신이 첫 단계로 아래 JSON 1개를 낸다 — 도구 호출 전, 다른 문장 ❌)**:
```json
{"intent":"nav|content|relation|meta|tag|temporal|mixed","targets":["노트명 후보 ≤3, 확신순"],"keywords":["핵심어 ≤5"],"tags":["태그 ≤3, # 제거"],"props":{"key":"value"},"path_hint":"폴더 힌트 or null","time":{"recent":false,"date":null},"axes":["bl|ln|prop|ctx|tag|full 실행 순서"],"topn":2}
```
intent: nav=위치·정본·목록·구조 / content=내용·설명·비교 / relation=역링크·정방향·누가 참조 / meta=속성·created·aliases / tag=태그 / temporal=최근·오늘·날짜 / mixed=둘 이상. `--decomp=sub`(DEEP 전용) 이면 이 JSON 을 `claude -p --model haiku --strict-mcp-config --mcp-config '{"mcpServers":{}}' --no-session-persistence "<같은 지시+질문>" < /dev/null` 로 받는다(상한 10s · 초과·JSON 파싱 실패 = 0-β 생략 = 1.6.0 규칙 파이프라인 그대로).

**0-γ 재조립(분해 JSON → 호출 목록 · 규칙 고정)**:
| intent | 먼저 | 그 다음 | 인자 |
|---|---|---|---|
| relation | targets 각각 ① `backlinks file=T format=json` + ② `links file=T` | ①이 `No backlinks found`(또는 0건)이면 **본문 언급 폴백**: `search query="T" format=json limit=50` → 경로 목록을 `[mention]` 라벨로(역링크 아님을 라벨로 구분 · «역링크 0·본문 언급 N건» 1줄 병기) · `search query=T total` 로 후보 검증(0 이면 다음 후보) | targets 없으면 keywords `search` 1회 → 상위 1건을 T 로 |
| meta | ③ `properties file=T format=json` · props 있으면 `search query="[k:v]" format=json limit=20` | `property:read name=k file=T` | `[k:v]` 는 CLI 가 해석(부분일치) |
| tag | ⑤ `tags counts format=json` 부분일치 후보 ≤3 → ⑤-b `search query="tag:t" limit=50` | 결과 ≤3 이면 ④ | 현행 ⑤/⑤-b |
| nav | ④-name **파일명 축**: `"$OBSIDIAN_CLI" search query="<targets[0]>" format=json limit=200` 결과 경로 중 basename(.md 제거)에 targets[0] 의 토큰(공백 분리, 2자+)이 «모두» 포함된 경로를 [name] 라벨로 최상위(≤3) · 0건이면 targets[1..] 반복 | ④ `search query=keywords path=path_hint format=json limit=50`(path_hint null 이면 path 생략 + Phase 0.4/0.5 결과 ∪) → 상위 TOPN `properties`·`links` | Tier 1 결과 ∪ · [name] 히트가 있으면 그것이 답의 1순위 |
| content | ④ `search query=keywords format=json limit=1000` → ④-b `search:context query=keywords path=<상위 1건 폴더> limit=3` | DEEP 이면 상위 TOPN `backlinks` | 현행 ④/④-b |
| temporal | Tier 1-S 신선도 보강 강제(RECENT=1) + `search query="[created:<time.date 또는 YYYY-MM>]" format=json limit=20` | content 규칙 | 날짜 없으면 이번 달 |
| mixed | axes 순서대로 위 행을 이어 붙임(중복 호출 제거) | — | 호출 상한 = 현행 유지 |
분해가 없거나(0-β 생략) intent 를 못 정하면 아래 0단·1단을 «그대로» 실행한다(1.7.0 은 앞머리 추가이지 1.6.0 을 빼지 않는다). **1단 규칙 확장(TOPN 노트의 ①prop ②bl ③ln)은 intent 와 무관하게 항상 실행**(재경님 2026-09-07 1546446498).

**0단 진입(신호어가 있으면 그 축을 먼저 · 신호 축이 돌아도 ④ 전문 검색은 항상 함께 실행 = 1단 TOPN 모집단) — 신호어 없으면 ④ 부터:**
| 질의 신호 | 서브커맨드 | 출력 |
|---|---|---|
| ① `[[이름]]` 포함 또는 「역링크·백링크·어디서 참조·누가 링크」 + 노트명 | `"$OBSIDIAN_CLI" backlinks file="<노트명>" vault="${OBSIDIAN_VAULT}" format=json` | JSON `[{"file":…}]` |
| ② 「이 노트가 링크하는·아웃링크·참조 목록」 + 노트명 | `"$OBSIDIAN_CLI" links file="<노트명>" vault="${OBSIDIAN_VAULT}"` | 평문 경로 줄(format 무시) |
| ③ 「속성·frontmatter·메타·created/updated/aliases 값」 + 노트명 | `"$OBSIDIAN_CLI" properties file="<노트명>" vault="${OBSIDIAN_VAULT}" format=json` | JSON 객체 |
| ⑤ `#태그` 토큰 또는 「태그·tag·태그가 붙은·태그로」 + 태그명 | `"$OBSIDIAN_CLI" tags vault="${OBSIDIAN_VAULT}" counts format=json` 에서 태그명 대소문자 무시 부분 일치로 후보 ≤5(count 내림차순) | 태그 후보 배열(각 `{tag,count}`) |
| ⑤-b ⑤ 후보마다(후보 0 → ④ 폴백) | `"$OBSIDIAN_CLI" search query="tag:<태그(앞 # 제거)>" vault="${OBSIDIAN_VAULT}" format=json limit=50` → 후보별 결과 합집합, 각 경로에 `[tag:#…]` 라벨(리터럴 `#태그` 검색은 쓰지 않음) | 경로 배열, `[tag:#…]` 라벨 |
| ④ 그 외(전문) | `"$OBSIDIAN_CLI" search query="${QUERY}" vault="${OBSIDIAN_VAULT}" format=json limit=1000` | 파일 배열 |
| ④-b DEEP 모드 또는 ④ 결과 ≤3건 | `"$OBSIDIAN_CLI" search:context query="${QUERY}" vault="${OBSIDIAN_VAULT}" format=json limit=20` | 파일:줄:문맥 |
**1단 규칙 확장(항상):**
```
TOPN = QUICK 2 / DEEP 5 (Tier 1 결과 ∪ 0단 결과에서 상위 TOPN 노트 · 노트명 = 경로 basename(.md 제거))
각 노트 F 에 대해 순서 고정:
 ① properties file="F" → created/updated/tags/aliases 요약 1줄 [prop]
 ② backlinks file="F" format=json (≤5) [bl] · ③ links file="F" (≤5) [ln]
 ④ search:context query="${QUERY}" path="<F 의 폴더>" limit=3 → F 의 매치 줄 ≤3 [ctx]
 ⑤ ① 의 tags 중 상위 2개 → search query="tag:<t>" format=json limit=20 → 기존 결과에 없는 경로 ≤3 [tag:#t]
중복 경로 제거 · 각 줄에 축 라벨 · CLI 오류·0B 는 그 축만 건너뛰고 계속(전체 중단 ❌) · 호출 상한 = 0단 ≤6(④ 1 + ④-b 1 + ⑤ 후보 ≤5 중 실행분) + 1단 TOPN×6(①②③④ 4 + ⑤ 태그 2)
```
- 출력 규약: Tier 1/2 본 결과 «아래»에 `## 확장(규칙 5축)` 블록 — 노트별 5줄 이내. 본 결과 순위 재배열 ❌.
- 기존 Phase 2.5-B(그래프 확장)와의 관계: Phase 2.5-B 의 backlinks 호출은 이 1단 ② 로 «대체»(중복 호출 ❌).
- 노트명 = `file=` 는 wikilink 처럼 «이름»으로 해석(경로 ❌), 추출 우선순위: ① `[[…]]` 안 ② 따옴표(`" "` · `' '` · 「」) 안 ③ 둘 다 없으면 질의에서 조사(이/가/을/를/의/에/은/는/과/와) 직전 토큰 중 vault 노트 이름과 일치하는 것 — 확인 명령 `"$OBSIDIAN_CLI" search query="<토큰>" vault="${OBSIDIAN_VAULT}" path= total`(total ≥1). 일치 0 이면 ④ 전문 검색으로 폴백. 예: 「MOC-Map 이 링크하는 노트는?」 → ③ 「MOC-Map」.
- **0 B·rc 0 ≠ 무결과** — 무결과 = `No matches found.`. 0 B 는 도구 순간 빈손 → 같은 명령 1회 재시도, 재현 시 Tier 3.
- `base:query` 는 쓰지 않는다(문법 미확정).
- 전제: Obsidian 데스크톱 앱 설치 + 실행 중 (setup 위저드가 감지·안내).
- **질의는 핵심 키워드 1~2개로 축약해 넣는다** — CLI 는 전문 일치(full-text) 검색이라 문장형 통짜 질의는 0히트가 정상이다(실측: 문장형 "No matches" vs 키워드 2개 다수 히트). **0건이면 키워드 변형(동의어·영/한 표기) 1회 재질의**, 그래도 0건일 때만 다음 티어로.
- CLI는 관련도 순위가 약하므로 흔한 단어는 limit을 크게 잡고 결과에서 추린다.
- CLI 부재·실행 오류 → Tier 3로.

### Tier 3 — Obsidian MCP (연결된 경우)
연결된 Obsidian MCP의 검색 도구를 사용한다(서버 구현마다 도구명이 다르다 — 예: `simple_search`, `obsidian_simple_search`). MCP 서버 미연결 → Tier 4로.

### Tier 4 — 텍스트 검색 (비상 폴백, 항상 가능)
```bash
grep -rln "${QUERY}" "${STRUCT_DIR}" --include="*.md" 2>/dev/null  # 3문서 우선
grep -rn "${QUERY}" "${VAULT_PATH}" --include="*.md" -l | head -20
```
- 문장형 질의는 통짜로 넣지 말고 **핵심 키워드 1~2개를 추출해** 검색한다(통짜 문장은 0히트).
- 이 티어를 쓴 경우 답변에 **왜 여기까지 내려왔는지**를 명시한다. 문구는 `GRAPHRAG_STATE` 로 가른다:
  - `misrouted` → **"GraphRAG 서버는 응답했으나 검색 경로가 HTTP `${TIER1_CODE}` 를 반환했습니다(엔드포인트 경로 불일치 가능) — 텍스트 검색으로 대체했습니다. 서버 부재가 아니므로 «자료 없음»으로 읽지 마십시오"**
  - `absent` → **"의미 검색 엔진 미설치로 텍스트 검색 결과입니다"**
  - `unreachable` → **"GraphRAG 서버(`${SEARCH_ENDPOINT}`)가 응답하지 않아 텍스트 검색으로 대체했습니다 — 결과가 평소보다 부정확할 수 있습니다"**
  - `blocked` → **"이 세션은 네트워크가 막혀 있어 GraphRAG 서버에 접속할 수 없습니다 — 서버 문제가 아닙니다. 에이전트 실행 시 네트워크를 허용하면(codex: `-c sandbox_workspace_write.network_access=true`) 의미 검색이 살아납니다"**
  - ⚠️ 엔진이 **설치돼 있는데 응답만 없는** 경우에 "미설치"라고 쓰면 사용자는 원인을 영영 못 찾는다. 두 경우는 처방이 다르다(설치 vs 서버 점검).

### 모드별 파라미터
- **QUICK**: top_k=5, 노트 읽기 1-2개
- **DEEP**: top_k=10, 노트 읽기 3-5개

> 💡 **top_k 를 더 올리고 싶을 때** — 후보 수를 늘리면 결과가 좋아질 것 같지만, 실제로는 반대로 가는 경우가 많습니다. 풀이 커지면 원래 상위에 있던 정답이 뒤로 밀립니다. **품질을 올리는 지렛대는 후보 수가 아니라 순위**라서, DEEP 의 심화는 top_k 보다 Phase 2.5(frontmatter·backlinks 그래프 확장) 쪽이 담당합니다.
> 올려야 할 때는 하나뿐입니다 — **"정말 없는지" 확인할 때.** 상위 결과만으로 부재를 단정할 수 없으면 경계 확인용으로 넓히고, 그 결과는 상위 근거와 **분리해서** 표기하세요.

> 💡 **찾은 결과를 쓸 때** — 검색기를 좋게 만들어도 답이 같은 폭으로 좋아지지는 않습니다. 정답 문서가 결과에 들어와 있는데도 안 쓰이는 일이 흔합니다.
> - **답에 근거로 쓸 문서는 실제로 열어 읽으세요.** 제목과 미리보기만 보고 "있다 / 없다 / 원인은 이것"을 단정하지 마세요. 위 `노트 읽기` 개수가 그 최소선입니다. (그냥 둘러보는 중이라면 해당 없습니다.)
> - **상위 몇 건이 같은 주장만 반복하면**, 기존 폴백 단계 안에서 다른 성격의 근거가 나올 때까지 다음 결과를 더 여세요.
> - **근거는 앞쪽에.** 결과를 다음 단계로 넘길 때 결론이 실제로 기대는 문서를 앞에 `문서 — 근거 한 줄 — 왜 관련되는지 한 줄` 로 묶고 보조 자료는 뒤로 보내세요. 같은 근거를 본문·부록·요약에 반복해 넣을 필요는 없습니다.
> - **여러 건을 넘길 때는 관계를 한 줄로.** 세 건 이상을 다른 도구나 에이전트에 넘긴다면 `A=원인 · B=재현 · C=해결` 처럼 문서 사이 관계를 한 줄 적어 주세요. 검색 결과를 통째로 직렬화해 넘기는 것보다 받는 쪽이 훨씬 잘 씁니다.

## Phase 2.5: 그래프 확장 — frontmatter·backlinks (DEEP 필수 · 0건/빈약 시 의무)

검색 엔진은 "어느 노트인가"까지만 안다. vault 의 진짜 구조 신호는 노트 안에 있다 — **frontmatter(태그·별칭·관련)와 wikilink 그래프(backlinks)를 활용**해야 검색이 똑똑해진다.

> ⚠️ **Tier 1 `VAULT_MODE=other`(서버가 다른 vault 인덱싱 중)면 본 Phase 전체를 생략한다** — 로컬 vault 의 frontmatter·backlinks 는 서버 인덱스와 다른 지식그래프라 근거가 되지 않고, 로컬 grep 은 "로컬 접근 0회" 원칙을 깬다. 서버 본문(`body`) 기반으로만 답한다.

### A. frontmatter 구조 신호 (읽는 모든 노트 공통)
노트를 Read 하면 본문 전에 frontmatter 를 먼저 해석한다:
- `aliases:` → **재질의 사전**: 1차 검색이 0건·빈약하면 별칭(영/한 표기 변형)으로 1회 재검색.
- `tags:` · `type:` → MOC/허브 판정(Phase 0.5 입력) + 답변의 분류 근거.
- `related:` · `parent:` · 본문 `[[링크]]` → 추가 Read 후보(질문과 키워드가 겹치는 것 1~2개).

### B. backlinks 1-hop (DEEP 필수 · QUICK 은 top hit 이 얇을 때)
top 1~2 노트에 대해 **backlink(그 노트를 가리키는 노트)** 와 **outlink(그 노트가 가리키는 노트)** 를 실측한다:
```bash
# 집행 계약: DEEP 모드에서 top 1~2 노트에 반드시 실행. backlinks = 전 플랫폼 grep 근사 —
# Obsidian CLI 의 backlinks 서브커맨드가 있으면(맥 데스크톱) 그걸 우선, 부재·오류 시 아래가 항상 동작한다.
# Tier 2 1단 ②가 이미 돌았으면 재호출 없이 그 결과 사용(중복 호출 ❌).
"$OBSIDIAN_CLI" backlinks file="<top노트 basename(.md 제거)>" vault="${OBSIDIAN_VAULT}" format=json
# 변수 규약: NOTE_PATH = VAULT_PATH 기준 상대경로. (절대경로가 들어와도 아래 NOTE_FILE 라인이 흡수한다.)
NOTE_FILE="${VAULT_PATH}/${NOTE_PATH}"; [ -f "$NOTE_FILE" ] || NOTE_FILE="${NOTE_PATH}"
STEM="$(basename "${NOTE_PATH}" .md)"
grep -rl --include="*.md" -F "[[${STEM}" "${VAULT_PATH}" | head -10
grep -o '\[\[[^]|#]*' "${NOTE_FILE}" | sed 's/^\[\[//' | sort -u | head -15
```
- backlinks 가 많은 노트 = 허브 → 답변 진입점으로 우선한다.
- backlinks/outlinks 중 질문과 겹치는 노트 1~2개를 추가 Read → 답변의 "🔗 연결 맥락"에 반영.
- **backlink grep 결과 줄 수를 센다(`| wc -l`) → 이 정수 N 이 답변 마지막 줄 `그래프 확장(backlinks N)` 에 들어간다** (제약 §"사용 티어 명시" 형식 고정과 1:1).

### C. 부재 발화 전 3단 재질의 (특히 Codex 등 도구가 얇은 환경)
**트리거 (상태 기반 — 부재 문장을 쓸 계획이 있든 없든 무관)**: 다음 중 하나면 **답변을 쓰기 전에** 아래 3단을 실행한다.
- ⓐ 검색 전체가 0건.
- ⓑ **질의가 특정 노트·제목·자료를 지목하는 lookup 형인데, 그 제목과 일치하는 파일이 결과에 0건인 상태** — 관련 MOC·유사 노트를 찾았어도, 부재 문장을 생략하고 관련 내용만 답할 생각이어도 트리거된다. **트리거는 문장이 아니라 "exact 0건 상태"다** (부재 문구를 안 쓰는 우회 = 계약 위반).
- ⓒ 그 외 "없다/확인되지 않았다"를 답변에 쓰려는 모든 경우.

어느 쪽이든 3단을 **각각 독립 실행**한 뒤에만 답변을 작성할 수 있다.

① **축약 재질의 (실행)** — 핵심 키워드 1~2개로 줄여 현재 티어를 1회 재실행.
② **별칭·표기 변형 재질의 (실행)** — 읽은 노트 frontmatter `aliases` + 영↔한 표기 변형으로 1회 재실행.
③ **wikilink 언급 탐색 (실행)**:
```bash
grep -rln --include="*.md" -F "[[${KEYWORD}" "${VAULT_PATH}" | head -10
```
(노트 *제목*에는 없어도 다른 노트들이 `[[링크]]`로 언급하는 경우를 잡는다.)
- **③이 히트하면 "없음"이 아니다** — "직접 노트는 없고 `[[링크]]` 언급으로 존재(N개 노트)"를 답하고 언급 노트를 출처로 제시한다.
- **부재 발화 형식 고정 (증빙 동반 의무)**: `…관련 자료 없음 (재질의 3단: ①"<축약어>" 0건 ②"<변형어>" 0건 ③[[언급]] 0건)` — 3단 증빙이 없는 부재 발화는 계약 위반이다.
- **ⓑ lookup 질의 답변 말미 의무 줄 (형식 고정 — 관련 MOC 로 답한 경우에도 생략 ❌)**: `지목 자료: "<대상>" — exact 0건 · 재질의: ①"<축약어>" <n1>건 ②"<변형어>" <n2>건 ③[[언급]] <n3>건`. n3 > 0 이면 언급 노트를 출처 목록에 올린다. 이 줄이 없는 lookup 답변은 미완이다.

## QUICK 모드 — 즉답 (3-5줄)

상위 1-2개 노트의 원문 확보 → frontmatter + 핵심 섹션 추출. 원문 = Tier 1 이면 원문 확보 계약을 따른다(`VAULT_MODE=same`=로컬 Read · `other`=`/api/note` 의 `body`, 로컬 경로 접근 ❌). Tier 2~4 로 검색한 경우 = 로컬 Read.

```
**답변:**
[3~5줄 직접 답변. 노트 내용 기반.]

📌 **상위 MOC** (N)
1. **[[MOC 제목]]** — [범위·역할 한 줄] (`경로`)

📄 **원자 노트** (N)
1. **[노트 제목]** — [핵심 한 줄] (`경로`)
```

## DEEP 모드 — 상세 분석

상위 3-5개 노트의 원문 확보(Tier 1 `VAULT_MODE=other` 면 `/api/note` 의 `body` — 로컬 Read ❌) → Phase 2.5 그래프 확장(frontmatter·backlinks 1-hop — `other` 면 생략) 실행 → 제목·요약·핵심 섹션 + 연결 맥락을 종합하여 질문에 직접 답변(목록·표·단계 활용).

```
## {질문 요약}

{답변 본문. 구조화된 분석.}

### 📌 상위 MOC (진입점)
1. [[MOC1]] — {범위·역할 1줄} (`경로`)

### 📄 원자 노트 (출처)
1. [[노트1]] — {핵심 정보 1줄} (`경로`)

### 🔗 연결 맥락 (Phase 2.5)
- [[허브노트]] ← backlinks {N}개 · 따라간 링크: [[관련1]], [[관련2]] (그래프 신호 없으면 섹션 생략)
```

## 제약

- **읽기 전용**: 노트 생성/수정 금지
- **hallucination 금지**: 반드시 실제 노트 내용 기반. 노트에 없는 내용은 "vault에 관련 자료가 없습니다" 명시 (Tier 1 에서는 `/api/note` 의 `body` 와 `source_note` 경로의 원문이 '실제 노트 내용'이다 — 둘 다 그 vault 노트에서 나온다. 로컬 원문 Read 는 경로가 실재할 때의 보강이지, Read 실패가 답변을 막는 게이트가 아니다)
- **출처 필수**: 실제 읽은 노트 경로 표기
- **사용 티어 명시 (형식 고정)**: 답변 마지막 줄은 정확히 이 형식으로 쓴다 — `검색: <티어명> + 구조 문서(<D>/3 참조 · 허브 <k>) + 그래프 확장(backlinks N)`. **D = Phase 0.4 의 `STRUCT_DOCS`, k = `ROUTE_HUB_COUNT`(둘 다 실측 정수)** · backlinks N = Phase 2.5-B backlink grep 결과 줄 수(실측 정수, 생략·"1-hop" 같은 서술 대체 ❌). 그래프 확장을 안 한 답변(QUICK 얕은 질의, 또는 Tier 1 `VAULT_MODE=other` 로 Phase 2.5 를 생략한 경우)은 `검색: <티어명> + 구조 문서(<D>/3 참조 · 허브 <k>)` 까지 허용.
- **질문/스킬/에이전트 스폰 금지**: 직접 검색만 수행 — 예외 1 = 0-β 분해(`--decomp=sub` 시 헤드리스 haiku 1회, 도구 0·질문 0), 그 외 스폰 ❌
- 상태 메시지 없이 바로 결과 출력 · Read 실패 시 다음 노트로
- QUICK: 5줄 이내 + 출처 1-2개 / DEEP: 제한 없음 + 출처 3-5개

### 결과 없음
```
vault에서 "{query}" 관련 자료를 찾지 못했습니다.
(재질의 3단: ①"<축약어>" 0건 ②"<변형어>" 0건 ③[[언급]] 0건 — Phase 2.5-C 증빙 형식)
/knowledge-manager로 자료를 수집해보세요.
```
