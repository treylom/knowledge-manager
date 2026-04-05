---
description: Knowledge Manager 업데이트 — upstream pull + vault 경로 재적용
allowed-tools: Bash
---

# /km-update — Knowledge Manager 업데이트

배포 repo의 최신 버전을 받고, 기존 vault 설정을 자동으로 재적용합니다.

## 실행

```bash
bash scripts/km-update.sh
```

## 동작 순서

1. skip-worktree 설정된 파일들의 잠금 해제
2. placeholder 템플릿으로 복원 (`git checkout HEAD`)
3. `git pull origin <current-branch>` 로 upstream 업데이트
4. `scripts/configure-vault-paths.sh` 재실행
5. skip-worktree 재설정

## 주의사항

- km-config.json 이외의 파일을 수동 편집했다면 stash 또는 commit 후 실행
- vault 경로를 **변경**하고 싶다면 `/km-update` 대신 `/knowledge-manager-setup` 재실행
- `/km-update` 실행 전 권장: `git status` 로 예상치 못한 로컬 변경 확인

## 에러 대응

| 에러 | 원인 | 해결 |
|---|---|---|
| "Uncommitted changes detected" | skip-worktree 바깥에서 수동 편집함 | `git stash` 또는 `git commit` 후 재실행 |
| "Merge conflict" | upstream이 치환 구간을 수정했음 | `git mergetool` 또는 수동 해결 후 `bash scripts/configure-vault-paths.sh` |
| "km-config.json not found" | setup 미실행 | `/knowledge-manager-setup` 먼저 실행 |
