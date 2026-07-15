---
name: km-graphrag-ops
description: Use when needing GraphRAG 구축·운영·수리 실행. build/search/status/doctor/heal 커맨드, 자동(데몬)·수동(1회 진단) 이원 모드, wedge 2연속 확인 자가치유. 검색 전략(km-graphrag-search)·동기화(km-graphrag-sync)와 보완 — 이 스킬은 실행 계층.
---

# km-graphrag-ops: GraphRAG 구축·운영·수리 (실행 계층)

> **역할 경계**: 선택적 어댑터입니다 — Knowledge Manager 코어 기능은 이 스킬 없이 완전 동작하며,
> GraphRAG 엔진(인덱서·서버)은 이 스킬이 번들하지 않고 별도 설치물([ThisCode](https://github.com/treylom/ThisCode) vendor)을 운영합니다.
> 기존 km-graphrag-search(검색 전략)·km-graphrag-sync(frontmatter 동기화)·km-graphrag-report(보고서)가 *이론·전략* 계층이라면, 본 스킬은 *설치·구축·운영·수리 실행* 계층입니다.

## 진입점

```bash
scripts/graphrag-ops/tofugraph.sh {doctor|status|heal|monitor|install-daemon|uninstall-daemon|build|search <q>}
```

환경변수(전부 선택 — 미지정 시 자동 감지/기본값): `GRAPHRAG_ROOT`(엔진 홈, 기본 = cwd에서 위로 걸으며 `.team-os/graphrag` 탐지) · `GRAPHRAG_API_URL`(기본 `http://127.0.0.1:8400`) · `GRAPHRAG_SERVICE_LABEL`(서비스명, 기본 = launchd/systemd에서 'graphrag' 자동 탐지) · `NTFY_TOPIC`(데몬 경보 푸시, 기본 꺼짐).

## 동사 4+2

| 동사 | 하는 일 | 언제 |
|---|---|---|
| `build` | vault → 온톨로지·임베딩·인덱스 구축 (엔진 위임) | 최초 1회 + 대량 노트 추가 후 |
| `search <q>` | 하이브리드 검색 1회 (동작 확인용) | 구축 직후 "됐나?" 확인 |
| `status` | 서버 상태 + 최근 24h 성능 요약(중앙값·p90·10s 초과율) | 궁금할 때 아무 때나 |
| `doctor` | **수동 모드 핵심** — 7단 진단 트리 실측 + 항목별 처방 출력 | 뭔가 이상할 때 첫 명령 |
| `heal` | 1회성 수리 — 60s 재확인 후에만 재시작(오탐 방지) + /ready 검증 | doctor가 FAIL을 짚었을 때 |
| `monitor` | **자동 모드 핵심** — 데몬 1틱(아래 자가치유 로직) | install-daemon이 시간마다 호출 |

## 자동 모드 (install-daemon)

Mac = launchd(`com.km.tofugraph-monitor`, 1시간 틱) / Linux·WSL = crontab. 틱 로직은 실전에서 검증된 안전장치를 그대로 이식:

1. **dead-server 이중 확인**: /health 무응답 1회 = 60s 대기 후 재확인 — 지속 시에만 재시작(일시 hiccup은 자연 회복).
2. **wedge 감지**: /health 200이어도 실제 검색이 막힌 상태(false-green)를 search probe(25s)로 잡되, **연속 2틱 확인 후에만 재시작** — 단발 오탐이 정상 서버를 죽이는 kill-loop 방지(실측 사고에서 나온 규칙).
3. **재구축 중 보호**: 인덱스 업데이트 진행 중(`update_in_progress`)엔 probe 자체를 쉬어 모니터가 가해자가 되는 걸 차단.
4. **재시작 후 검증**: kickstart가 성공해도 /ready true까지 폴링으로 확인해야 "복구"로 기록.

## 고칠 수 있는 것 vs 알려만 주는 것 (best-effort 경계)

| 증상 | 이 스킬이 하는 일 |
|---|---|
| 서버 무응답·행(hung) | ✅ 이중 확인 후 재시작 + 검증 |
| 검색만 막힘(wedge) | ✅ 2연속 확인 후 재시작 |
| 인덱스 오래됨(7일+) | ✅ build 재실행 안내/실행 |
| 재시작 직후 느림 | ✅ 워밍업으로 판정, 기다리라고 안내 (재시작 반복 ❌) |
| 디스크 부족·OS 업데이트 | ⚠️ **보고만** — 공간 확보/설치는 사람 결정 |
| 하드웨어(메모리/GPU) 압박 | ⚠️ 보고만 |
| vault 노트 자체 손상 | ⚠️ 보고만 (지식 데이터는 이 도구가 건드리지 않음) |

## 검증 이력 (이 로직이 실전에서 겪은 것)

수리 전후 24h 실측: 검색 중앙값 16.6s→3.4s(-80%)·p90 194.9s→35.8s·재시작 crash-loop 7회→확인된 2회. probe 단발 timeout을 즉시 kill로 이었던 초기 버전이 오탐 kill-loop를 만들었고(하루 14회 재시작 실측), "2연속 확인" 규칙이 그 수리 결과다 — 본 스킬의 안전장치는 전부 실제 장애에서 역산됐다.
