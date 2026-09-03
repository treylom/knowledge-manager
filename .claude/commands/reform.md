---
description: 대량 변형 — plan(dry-run) 기본, apply 명시 시 이동·프론트매터·링크 일괄 + git 스냅샷·롤백 · check = 링크 게이트
allowedTools: Read, Write, Bash, Glob, Grep
---

# /km:reform — 대량 변형 (plan/apply/check)

$ARGUMENTS

> **엔진 인용 계약**: 이 커맨드는 이동·frontmatter·링크 수정 로직을 새로 구현하지 않는다. `apply` ② 단계는 `skills/km-archive-reorganization.md`(이동 — Mode R)와 `skills/km-batch-python.md`(frontmatter·links)의 기존 절차를 그대로 따른다. 여기서 하는 일은 그 절차를 순서대로 호출하고, 실행 전후로 스냅샷·감사·게이트를 배선하는 것뿐이다.

## 0. 문법

```
/km:reform <plan|apply|move|frontmatter|links|check> [경로|계획서]
```

- **인자 없음 = `plan`**(vault 전체를 대상으로 계획서만 만든다).
- `move`·`frontmatter`·`links` = 그 유형 하나만 다루는 `plan` 단축이다(예: `/km:reform move` → 이동 대상만 계획서에 담는다). `apply` 는 항상 먼저 만든 `plan` 산출물(계획서)을 인자로 받는다.
- `VAULT_PATH` 는 `commands/search.md` Phase -1 과 동일 규칙으로 정한다(추측 ❌ — `km-config.json` → `obsidian.json` `"open": true` 판정 → 그래도 없으면 사용자에게 1회 질문). `PLUGIN_ROOT` 는 이 플러그인 루트(`scripts/km_link_gate.py` 가 있는 경로)로, 밖에서 주어진다.
- 아래 절의 bash 블록은 `$VAULT_PATH`·`$PLUGIN_ROOT`·(있다면) `$ARGUMENTS` 세 값이 이미 정해져 있다고 가정한다.

## 1. plan (dry-run · 쓰기 = 계획서 1개뿐)

입력은 `_meta/KM-DESIGN.md` §G(있으면) 또는 사용자 서술이다. 이 단계는 **노트·폴더를 건드리지 않는다** — vault 안에서 쓰는 파일은 계획서 1개뿐이다.

```bash
TS=$(date +%Y%m%d-%H%M%S)
SOURCE="${VAULT_PATH}/_meta/KM-DESIGN.md"
if [ -f "$SOURCE" ]; then SOURCE_DESC="$SOURCE (§G)"; else SOURCE_DESC="사용자 서술(대화 맥락) — $SOURCE 없음"; fi
PLAN="${VAULT_PATH}/_meta/REFORM-PLAN-${TS}.md"
mkdir -p "${VAULT_PATH}/_meta"

# 대상 계수(근사) — move|frontmatter|links 로 좁혀 부르면 그 유형 범위만 센다.
TARGET_COUNT=$(find "$VAULT_PATH" -name '*.md' -not -path '*/_meta/*' | wc -l | tr -d ' ')
LINK_COUNT=$(grep -rho '\[\[[^]]*\]\]' "$VAULT_PATH" --include='*.md' 2>/dev/null | wc -l | tr -d ' ')

# 헤더는 변수로 우회한다(heredoc 안 리터럴 '## ' 가 바깥 절 목차 grep 을 오염시키지 않게).
SEC_TARGET="## 대상"; SEC_LINK="## 예상 링크 영향"; SEC_ROLLBACK="## 롤백 방법"; SEC_ETA="## 소요 예측"

cat > "$PLAN" <<EOF
---
schema_version: km-reform-plan-v1
source: ${SOURCE_DESC}
created: $(date +%F)
---

# Reform Plan — ${TS}

${SEC_TARGET}
- 파일 수(근사, .md 전체 — 유형 지정 시 해당 범위만): ${TARGET_COUNT}
- 변경 유형: ${ARGUMENTS:-plan(전체)}

${SEC_LINK}
- 현재 wikilink 총량(근사): ${LINK_COUNT}
- 예상 깨짐 수: 이동 대상 파일명을 위 근사값에서 별도로 grep 해 채운다(노트·폴더는 이 단계에서 건드리지 않는다)

${SEC_ROLLBACK}
- apply 실행 전 자동 스냅샷(태그 또는 stash)을 남긴다 → \`git -C "$VAULT_PATH" reset --hard km-reform-pre-<ts>\`

${SEC_ETA}
- 범위: 파일 수 기준 대략(정확한 단일 수치 금지 — 범위로만 제시)
EOF
echo "저장: $PLAN"
```

## 2. apply <계획서> (사용자 「apply」 명시 시만)

`/km:reform apply <계획서>` — 대화에서 사용자가 "apply" 를 명시했을 때만 실행한다. `<계획서>` 는 §1 로 만든 `_meta/REFORM-PLAN-<ts>.md` 다.

### ① 스냅샷

```bash
if ! git -C "$VAULT_PATH" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "vault 가 git 이 아닙니다 — git -C \"$VAULT_PATH\" init 후 apply 를 다시 실행하세요. 스냅샷 없이 apply 는 진행하지 않습니다."
  exit 1
fi
TS=$(date +%Y%m%d-%H%M%S)
if git -C "$VAULT_PATH" diff --quiet && git -C "$VAULT_PATH" diff --cached --quiet; then
  git -C "$VAULT_PATH" tag "km-reform-pre-$TS"
else
  git -C "$VAULT_PATH" stash push -m "km-reform-pre-$TS" && echo "미커밋 변경이 있어 stash 로 스냅샷했습니다 — 롤백은 태그 대신 git stash pop 을 씁니다."
fi
echo "스냅샷: km-reform-pre-$TS"
```

### ② 엔진

- `move`: `skills/km-archive-reorganization.md` Phase R4 "실행 순서"(스크립트 생성 → `--dry-run` → 사용자 승인 → 실행+즉시 커밋 → spot-check)를 그대로 따른다. 소량이면 같은 스킬 "개별 파일 이동(소량, 비배치)" 절의 CLI → MCP → `mv` 폴백 순서를 쓴다.
- `frontmatter`·`links`: `skills/km-batch-python.md` 5단계(스크립트 생성 → `--dry-run` 실행 → 사용자 승인 → 실행+즉시 커밋 → spot-check)를 그대로 따른다.
- 이 커맨드는 이동·수정 로직 자체를 새로 구현하지 않는다 — 위 두 스킬의 기존 절차를 그대로 호출한다.

### ③ km-link-audit 1회

`skills/km-link-audit.md` Phase 1~3(전체 노트 스캔 → 연결 그래프 → 문제점 식별)을 1회 실행해, 이번 적용으로 새로 생긴 고아 노트·깨진 링크·단방향 링크를 파악한다. 결과는 ⑤ 리포트의 "감사 결과"에 옮겨 적는다.

### ④ 링크 게이트

```bash
python3 "$PLUGIN_ROOT/scripts/km_link_gate.py" "$VAULT_PATH"
GATE_EXIT=$?
if [ "$GATE_EXIT" -eq 0 ]; then
  echo "exit 0 = 통과 — 리포트에 PASS 기록"
elif [ "$GATE_EXIT" -eq 1 ]; then
  echo "exit 1 = apply 실패 처리 — 미통과 표를 리포트에 기재하고 ⑥ 롤백을 안내한다"
  python3 "$PLUGIN_ROOT/scripts/km_link_gate.py" "$VAULT_PATH" --json
elif [ "$GATE_EXIT" -eq 2 ]; then
  echo "exit 2 = 측정 불가 — 통과 취급 ❌. 사유를 표시하고 정지한다"
  exit 2
fi
```

### ⑤ 리포트

```bash
REPORT="${VAULT_PATH}/_meta/REFORM-REPORT-${TS}.md"
# 헤더는 변수로 우회한다(heredoc 안 리터럴 '## ' 가 바깥 절 목차 grep 을 오염시키지 않게).
SEC_CHANGES="## 변경 목록"; SEC_AUDIT="## 감사 결과 (km-link-audit)"; SEC_GATE="## 게이트 결과"
cat > "$REPORT" <<EOF
---
schema_version: km-reform-report-v1
snapshot: km-reform-pre-${TS}
gate_exit: ${GATE_EXIT}
created: $(date +%F)
---

# Reform Report — ${TS}

${SEC_CHANGES}
(② 엔진 실행 로그에서 채운다 — move/frontmatter/links 별 변경 파일 수)

${SEC_AUDIT}
(③ 단계 결과 요약 — 고아 노트·깨진 링크·단방향 링크)

${SEC_GATE}
- exit: ${GATE_EXIT} (0=통과 · 1=apply 실패 처리 · 2=측정 불가 — 통과 취급 ❌)
- 미통과 노트: exit 1 일 때 위 --json 출력의 failed 배열을 표로 옮긴다
EOF
echo "저장: $REPORT"
```

### ⑥ 롤백

```bash
# ① 에서 태그로 스냅샷했다면:
git -C "$VAULT_PATH" reset --hard "km-reform-pre-${TS}"
# ① 에서 stash 로 스냅샷했다면(태그 대신):
git -C "$VAULT_PATH" stash pop
```

## 3. check

apply 없이 게이트만 돈다. ④ 명령을 단독으로 실행한다.

```bash
python3 "$PLUGIN_ROOT/scripts/km_link_gate.py" "$VAULT_PATH"
```

일부 노트만 검사하고 싶으면 `--notes` 로 쉼표 목록을 준다(지정 시 `--exclude` 는 무시된다):

```bash
python3 "$PLUGIN_ROOT/scripts/km_link_gate.py" "$VAULT_PATH" --notes "020-Library/web/x.md,010-Notes/a/note-a1.md"
```

| exit | 의미 |
|---|---|
| exit 0 | 전건 통과 |
| exit 1 | 1건 이상 미통과(FAIL) — 사용자 대면 출력에 note·reason 을 표로 보여준다 |
| exit 2 | 측정 불가(vault 없음·md 0건·검사 대상 0건 등) — 통과 취급 ❌, 사유를 그대로 보여준다 |

## 4. --parallel (기본 ❌)

기본은 순차 처리다. 폴더 단위 병렬(`-at` 팀 병렬)은 사용자가 `--parallel` 을 명시했을 때만 켠다 — 대상 폴더별로 나눠 동시에 ② 엔진을 돌리되, ① 스냅샷은 병렬 여부와 무관하게 apply 전체에 1회만 남긴다(폴더별 개별 태그 ❌). 게이트(④)·리포트(⑤)도 전체 적용이 끝난 뒤 한 번만 돈다.

## 5. 범위 밖(YAGNI, 1.3.0)

- 본문 재작성(문장 단위 리라이팅)
- 정규식 자유 치환(사용자 임의 패턴 지정 교체)
- 삭제(파일·폴더 제거)

이 셋은 1.3.0 범위 밖이다. 필요하면 사용자가 별도 스크립트를 직접 작성해 실행한다.

## 제약

- `apply` 는 사용자가 "apply" 를 명시했을 때만 실행한다 — `plan` 결과만으로 자동 승격 ❌.
- 스냅샷(① 단계) 없이 vault 를 변경하지 않는다.
- 사용자 대면 문장은 평이한 한국어로 쓴다 — `MOC`·`wikilink`·`frontmatter` 등 전문어는 첫 등장에 1줄 풀이를 붙인다.
