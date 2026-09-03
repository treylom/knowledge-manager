---
description: 지식관리 설계 상담 — 폴더·MOC·wiki 대상·스킬 추천을 KM-DESIGN 문서로
allowedTools: Read, Write, Bash, Glob, Grep
---

# /km:interview — 지식관리 설계 상담

$ARGUMENTS

> **근거 문서 계약**: 답하기 전에 `skills/km-vault-design-principles.md`(지식원 D3, 절 `## A`~`## G`)를 **반드시 Read** 한다. D3 에 없는 처방은 반드시 "일반 권장" 라벨을 붙여 D3 원칙과 구분한다 — 라벨 없이 섞어 말하지 않는다.

> **대화 방식**(`knowledge-manager-setup.md` Phase 4 인터뷰와 동일): AskUserQuestion 옵션 클릭 ❌ — 평문 질문 + 답변마다 후속 되묻기 1개. 한 번에 앵커 하나만 묻는다. 전체 15분 상한, 중간에 끊겨도 `_meta/KM-DESIGN.md` 에 `completeness: partial` 로 저장한다.

## 0. 진입

`VAULT_PATH` 는 `search.md` Phase -1 과 동일 규칙으로 정한다(추측 ❌: `km-config.json` → `obsidian.json` `"open": true` 판정 → 그래도 없으면 사용자에게 1회 질문). 이어서 `000-START-HERE` 3문서와 `_meta/USER-PROFILE.md` 존재를 센다.

```bash
# VAULT_PATH 결정 — search.md Phase -1 규칙 그대로(추측 금지)
if [ -z "$VAULT_PATH" ]; then
  VAULT_PATH="$(python3 -c "import json,sys;d=json.load(open('km-config.json'));print(d.get('storage',{}).get('obsidian',{}).get('vaultPath',''))" 2>/dev/null)"
fi
if [ -z "$VAULT_PATH" ]; then
  OBSIDIAN_JSON=$(ls -1 "$HOME/Library/Application Support/obsidian/obsidian.json" /mnt/c/Users/*/AppData/Roaming/obsidian/obsidian.json "$APPDATA/obsidian/obsidian.json" 2>/dev/null | head -1)
  [ -n "$OBSIDIAN_JSON" ] && VAULT_PATH="$(python3 -c 'import json,sys;d=json.load(open(sys.argv[1]))["vaults"];print("\n".join(v["path"] for v in d.values() if v.get("open")))' "$OBSIDIAN_JSON" | head -1)"
fi
[ -n "$VAULT_PATH" ] || echo "VAULT_PATH 미확정 — 사용자에게 1회 질문(추측 금지)"

SH_DIR="${VAULT_PATH}/000-START-HERE"; STRUCT_DOCS=0
for f in START-HERE VAULT-STRUCTURE MOC-Map; do
  [ -f "$SH_DIR/$f.md" ] && STRUCT_DOCS=$((STRUCT_DOCS+1))
done
PROFILE="${VAULT_PATH}/_meta/USER-PROFILE.md"; PROFILE_EXISTS=0
[ -f "$PROFILE" ] && PROFILE_EXISTS=1
echo "STRUCT_DOCS=${STRUCT_DOCS}/3 PROFILE_EXISTS=${PROFILE_EXISTS}"

if [ "$STRUCT_DOCS" -lt 3 ]; then
  echo "⚠️ 구조 문서 없음 — /km:setup 재실행 안내"
  (cd "$VAULT_PATH" && find . -maxdepth 2 -type d -not -path '*/.*' | sort)
fi
```

- `PROFILE_EXISTS=1` 이면 **재질문 ❌** — `_meta/USER-PROFILE.md` 의 `roles`·`info_flow`·`north_star` 값을 그대로 인용해 앵커 ①·⑤ 맥락으로 삼는다.
- `PROFILE_EXISTS=0` 이면 여기서 앵커 ①·⑤ 두 개만 즉석으로 묻는다(②③④는 §1 에서 순서대로). 최소 착지점 없이 §1 로 넘어가지 않는다.

## 1. 앵커 5(설계 전용)

대화형(한 번에 하나) · 각 답변에 후속 되묻기 1개 · 전체 15분 상한 · 중간 이탈 시 `_meta/KM-DESIGN.md` 에 `completeness: partial` 저장.

| # | 앵커 | 질문 | 후속 되묻기 예 |
|---|---|---|---|
| ① | 자료 종류·양·유입 경로 | "요즘 이 볼트에 들어오는 자료가 뭔가요? 어떤 형태(PDF·웹·메모·대화 캡처)로, 얼마나 자주요?" | "그중 양이 제일 많은 하나는? 어디서 들어오나요?" |
| ② | 다시 찾는 패턴·못 찾은 사례 | "저장한 자료를 나중에 어떻게 다시 찾나요? 최근에 못 찾아서 헤맨 적 있나요?" | "그때 뭘 했나요? 얼마나 걸렸나요?" |
| ③ | 혼자/여럿/봇(owner 경계) | "이 볼트를 혼자 쓰나요, 아니면 다른 사람이나 자동화 도구도 같이 쓰나요?" | "같이 쓴다면 누가 어디를 건드리나요? 겹친 적 있나요?" |
| ④ | 지키고 싶은 것 | "지금 구조에서 절대 안 바꿨으면 하는 부분이 있나요?" | "왜 그게 중요한가요?" |
| ⑤ | 3개월 목표 1개 | "3개월 뒤 이 볼트가 정리돼 있다면 뭐가 제일 달라져 있을까요? 딱 하나만." | "그게 되면 지금 대비 뭐가 줄어드나요(시간·스트레스)?" |

## 2. 지식원 Read

1. `skills/km-vault-design-principles.md` 전문을 Read 한다(스킵 ❌) — 절 `## A`~`## G` 전부.
2. 앵커 ①~⑤ 답변을 아래 표로 D3 절과 대조해 관련 절만 추린다.
3. D3 절에 원칙이 있으면 그 절 번호(A~G)를 인용해 §3 산출에 반영한다.
4. D3 에 없는 처방(예: 특정 도구·서비스 추천)은 반드시 "일반 권장" 라벨을 붙인다.
5. 대조가 끝나면 §3 산출 KM-DESIGN 으로 넘어간다.

| D3 절(지식원) | 대응하는 산출 절 |
|---|---|
| A 접두 폴더 체계 | B 폴더 설계안 |
| B MOC 원칙 | C MOC 지도 초안 |
| C raw→wiki 층 | D wiki 대상/비대상 표 |
| D 다주체 경계 | A 현황 진단(owner 축) · G 3문서 개정안(권한표) |
| E 폴더 변경 절차 | G 3문서 개정안(적용 절차) |
| F 스킬 역할 맵 | E 스킬 추천 순서 |
| G 안티패턴 | A 현황 진단(위험 신호) · F 재상담 트리거 |

## 3. 산출 KM-DESIGN

`_meta/KM-DESIGN.md` 골격을 heredoc 으로 생성한다. 이미 있으면 `.bak-<타임스탬프>` 로 보존한 뒤 재생성한다(끊긴 이전 초안을 덮어쓰기 전에 남겨 둔다).

```bash
DESIGN="${VAULT_PATH}/_meta/KM-DESIGN.md"
mkdir -p "${VAULT_PATH}/_meta"
[ -f "$DESIGN" ] && cp "$DESIGN" "${DESIGN}.bak-$(date +%Y%m%d-%H%M%S)"
COMPLETENESS="${KM_INTERVIEW_COMPLETENESS:-full}"   # 앵커 5개 다 못 채우고 끊기면 partial
SECA="## A 현황 진단"; SECB="## B 폴더 설계안"; SECC="## C MOC 지도 초안"
SECD="## D wiki 대상/비대상 표"; SECE="## E 스킬 추천 순서"
SECF="## F 첫 2주 루틴 + 재상담 트리거"; SECG="## G 3문서 개정안"
export DESIGN COMPLETENESS SECA SECB SECC SECD SECE SECF SECG VAULT_PATH
cat > "$DESIGN" <<EOF
---
schema_version: km-design-v1
based_on: [USER-PROFILE, START-HERE, VAULT-STRUCTURE, MOC-Map]
completeness: ${COMPLETENESS}
updated: $(date +%F)
---

# KM 설계 — $(basename "$VAULT_PATH")

${SECA}

(앵커 ①~③ + §0 find 트리 대조 결과를 채운다)

${SECB}

(D3 A 접두 체계 근거 — 접두 표 초안. 빈 대역에만 배정, 번호 없는 plain 폴더 신설 ❌)

${SECC}

(D3 B MOC 원칙 근거 — 도메인별 허브 후보. 폴더 경계에 묶이지 않아도 됨)

${SECD}

(D3 C raw→wiki 층 근거 — 대상=반복 참조·연결·갱신되는 개념/절차/결정, 비대상=원본 raw·1회성 스크랩·일정·개인 원문. 표 1개, 층 분리 보관)

${SECE}

(D3 F 스킬 역할 맵 근거 — setup → knowledge-manager(-at) → tofugraph → search → reform, 각 행에 「언제·왜」 1행)

${SECF}

(앵커 ⑤ 목표 근거 — 첫 2주 실행 순서 + 재상담 트리거 조건: 예 노트 급증·owner 추가)

${SECG}

(VAULT-STRUCTURE/MOC-Map 델타 — 추가·이동·삭제 행. 적용은 사용자 승인 후 /km:reform plan)
EOF
echo "저장: $DESIGN (completeness=${COMPLETENESS})"
```

## 4. 개정안 → reform 인계

§G 를 적용하려면 `/km:reform plan _meta/KM-DESIGN.md` 를 사용자에게 안내한다. **이 커맨드는 노트·폴더를 옮기지 않는다** — 개정안은 문서로만 남기고, 실행은 항상 `/km:reform` 계열에 인계한다.

## 제약

- 쓰기 대상은 `_meta/KM-DESIGN.md` **1개뿐** — 노트·폴더를 만들거나 옮기지 않는다.
- D3(`km-vault-design-principles.md`) 밖의 처방은 반드시 "일반 권장" 라벨을 붙인다.
- 사용자 대면 문장은 평이한 한국어로 쓴다 — 전문어(MOC·owner 경계 등)는 첫 등장에 1줄 풀이를 붙인다.
- 질문은 한 번에 하나만 던진다(옵션 클릭 ❌).
