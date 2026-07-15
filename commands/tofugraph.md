---
description: GraphRAG 구축·검색·상태·수리 — knowledge-manager 그래프 위에 얹는 검색 엔진 운영
allowed-tools: Bash, Read
---

# /tofugraph — GraphRAG 구축·운영·수리

knowledge-manager로 그린 그래프(frontmatter + 위키링크) 위에 GraphRAG 검색을 얹고, 그 서버를 관리·수리합니다. 상세 명세: [skills/km-graphrag-ops.md](../skills/km-graphrag-ops.md).

## 사용

```
/tofugraph              → doctor (진단 + 처방 — 첫 실행이면 여기부터)
/tofugraph build        → 인덱스 구축 (엔진 미설치면 설치 안내)
/tofugraph search <질문> → 검색 1회 (동작 확인)
/tofugraph status       → 상태 + 최근 24h 성능 요약
/tofugraph heal         → 1회성 수리 (이중 확인 후에만 재시작)
/tofugraph auto         → 자동 관리 켜기 (시간마다 감시·자가치유 데몬)
```

## 실행 절차 (에이전트용)

1. 인자를 파싱한다. 없으면 `doctor`.
2. `auto`는 `install-daemon`으로, 나머지는 동사 그대로 매핑:
   ```bash
   bash scripts/graphrag-ops/tofugraph.sh <verb> [args]
   ```
3. 출력을 **사용자 눈높이로 요약**한다 — doctor의 [FAIL]/[WARN] 항목은 처방(fix: 줄)을 그대로 전달하고, 전부 [OK]면 "검색 시스템 정상" 한 줄이면 충분.
4. `build`가 엔진 미설치를 보고하면 설치 명령을 사용자에게 보여주고 **실행 여부를 물어본다** (외부 레포 clone은 사용자 결정).
5. ⚠️ 경계: 디스크 부족·OS 업데이트류 [WARN]은 이 도구가 고치지 않는다 — 사용자에게 보고만 한다(자동 삭제·정리 금지).
