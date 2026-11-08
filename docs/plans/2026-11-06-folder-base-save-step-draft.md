# 문안 초안 — KM 저장 흐름에 «폴더 노트 표(.base)» 단계 넣기 (경고 모드 · 시범)

> 상태: **초안** — `commands/knowledge-manager.md` 에 아직 넣지 않았다. 1폴더 시범(2026-11-06) 통과 뒤 넣을 문안.
> 근거: kepano/obsidian-skills `skills/obsidian-bases/SKILL.md`(작성 → 검증 → Obsidian 확인 · 필터 = 논리 키 정확히 하나) · 흡수 검토 결정(Base 만 · Canvas 제외 · 저장 조건 5).
> 넣을 자리: STEP 5.5(PROPAGATE)의 MOC 갱신 뒤 «5.5-3b» — 3-tier·주제별 분할처럼 **폴더 하나에 노트가 여러 개 생기는 저장**에서만. 단일 노트 저장에는 만들지 않는다.

---

### 5.5-3b. 폴더 노트 표(.base) — 경고 모드

폴더에 새 노트가 3개 이상 생겼고 그 폴더 MOC 가 있으면, 그 폴더만 거르는 노트 표 1개를 만든다.

1. **이름 고정**: `<폴더 이름>-노트표.base` (폴더 안). 이미 있으면 새로 만들지 않고 덮어쓴다 — 이름을 바꾸거나 `… 1.base` 를 만들지 않는다.
2. **내용**(필터 = 논리 키 하나, 그 아래 폴더 조건 — 빈 기본 표 ❌):

   ```yaml
   filters:
     and:
       - file.inFolder("<vault 상대 폴더>")
       - file.ext == "md"
   views:
     - type: table
       name: "노트 전체"
       groupBy:
         property: type
         direction: ASC
       order:
         - file.name
         - type
         - date
         - tags
   ```
   한 객체에 `and`·`or`·`not` 를 나란히 두지 않는다(kepano/obsidian-skills 2026-06-06 반영 수정 · PR #68 — 예전 예시 꼴은 오류).
3. **MOC 진입**: 폴더 MOC 에 `![[<폴더 이름>-노트표.base]]` 한 줄. 같은 줄이 이미 있으면 넣지 않는다(재저장 중복 0).
4. **라이브 vault 반영 뒤 검사**(Obsidian 이 열어 둔 vault 기준):

   ```bash
   python3 "$PLUGIN_ROOT/scripts/km_base_check.py" "$VAULT_PATH" \
     --folder "<vault 상대 폴더>" --base "<vault 상대 .base>" --moc "<vault 상대 MOC>" \
     --vault-name "<Obsidian 이 보는 vault 이름>"; BASE_RC=$?   # --vault-name = 여러 vault 를 열어 둘 때 (하나면 생략)
   echo "BASE_CHECK_RC=$BASE_RC"
   ```

   저장 조건 5 — 다섯 개가 모두 PASS 여야 «표 있음»으로 보고한다:
   | 조건 | 뜻 |
   |---|---|
   | filter | 전역 필터가 있고, 논리 키가 한 객체에 하나, 폴더(또는 태그) 조건 포함 |
   | expected-set | Obsidian 이 돌려준 노트 집합 = 그 폴더(하위 포함) `.md` 집합 |
   | query-rows | `base:query` 1행 이상 · 출력에 `Error:` 없음 |
   | moc-entry | 폴더 MOC 에서 들어갈 수 있음 |
   | no-duplicate | 같은 폴더를 거르는 `.base` 1개 · MOC 진입 줄 1개 |

| exit | 처리(경고 모드) |
|---|---|
| 0 | 보고서에 «노트 표: N행 = 폴더 노트 N개» 한 줄 |
| 1 | 저장은 그대로 두고, FAIL 조건과 사유를 보고서에 싣는다. 표를 지우지는 않는다 |
| 2 | 측정 불가(.base·MOC·CLI 없음) — «표 있음»으로 세지 않고 사유만 적는다 |

**함정(2026-11-06 실측)**
- Obsidian CLI 는 오류도 종료코드 0 으로 낸다(`Error: Base file not found: …`) → 종료코드가 아니라 출력의 `Error:` 로 가른다.
- 새 `.base` 를 쓴 직후 몇 초 동안 `base:query` 가 0바이트(rc 0)를 돌려준다 → 검사기는 3초 쉬고 최대 3번 다시 묻는다. 끝까지 0바이트면 «무결과»가 아니라 «0 B 응답»으로 적는다.
- 필터 없는 빈 `.base` 는 vault 전체(시범 vault 24,381행)를 돌려준다 → «1행 이상»만 보면 통과해 버린다. 그래서 filter·expected-set 두 조건이 따로 있다.
- 응답이 크면(2.3MB) 표준입력이 `/dev/null`(cron·CI 꼴)일 때 0바이트(rc 0)가 온다 · 열린 파이프·소켓이면 전부 온다(3/3) → 검사기는 열어 둔 빈 파이프를 표준입력으로 준다. 손으로 재 볼 때도 `< /dev/null` 을 붙이지 않는다.
- Obsidian 화면 렌더(표가 눈에 어떻게 보이나)는 검사기가 보지 않는다 — 처음 몇 번은 사람이 한 번 열어 본다.

**시범 1폴더 결과(2026-11-06)**: 노트 23개짜리 연구 주제 폴더 1개 · 5조건 PASS · rows 23 = 폴더 md 23 · 같은 저장 한 번 더 → `.base` 1 · MOC 진입 1 · 빈 껍데기 대조(`Untitled.base` 0B · `attachments/무제.base` 37B) = query-rows PASS(24,381행)인데 filter·expected-set FAIL.
