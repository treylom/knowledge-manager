---
name: km-batch-python
description: Python 배치 실행 + auto-sync 보호 — 규칙서 기반 Python 스크립트의 안전한 실행 프로토콜. worktree 버그 우회, --dry-run 필수, auto-sync 경합 방지.
---

# Python Batch Execution Skill

규칙서 기반 Python 스크립트를 안전하게 실행하는 프로토콜.
Agent Teams worktree 버그를 우회하고, auto-sync 경합을 방지.

## 적용 시점

- `km-archive-reorganization.md` Phase R4에서 호출
- 독립적으로도 사용 가능 (대규모 배치 파일 수정 시)

---

## 핵심 원칙

### CRITICAL: 실행 주체

| 허용 | 금지 |
|------|------|
| Lead가 Python 스크립트 생성 + 직접 Bash 실행 | Agent Teams 팀원에게 Write/Bash 위임 |
| Lead가 mcp__obsidian__create_note 직접 호출 | Task 에이전트에게 MCP 호출 위임 |

> **Why**: Agent Teams worktree 버그 — 팀원의 파일 수정이 TeamDelete 시 유실됨.
> 검증된 사례: 얼룩소 프로젝트 (Bug-2026-02-25-1700)

### Auto-sync 보호

```
매 배치 스크립트 실행 후:
git add -A && git commit -m "{Phase}: {설명}" && git push
```

> **Why**: Windows OneDrive 환경에서 지연 커밋 시 auto-sync가 파일을 덮어씀.
> 얼룩소 프로젝트에서 실제 경합 발생 → git checkout + 재적용 + 즉시 push로 복구.

---

## 실행 프로토콜 (5단계)

### Step 1: 스크립트 생성

```
스크립트 저장 위치: /tmp/{script_name}.py
```

> `/tmp/`에 생성하여 vault 오염 방지.

### 스크립트 필수 구조

```python
#!/usr/bin/env python3
"""
{스크립트 설명}
Usage: python3 {script_name}.py [--dry-run] {target_folder}
"""
import argparse, glob, os, re

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("target", help="대상 폴더 경로")
    parser.add_argument("--dry-run", action="store_true", help="변경 없이 예상 결과만 출력")
    args = parser.parse_args()

    changed = 0
    skipped = 0
    errors = []

    for filepath in glob.glob(os.path.join(args.target, "**/*.md"), recursive=True):
        try:
            content = open(filepath, encoding="utf-8").read()
            new_content = process(content, filepath)  # 규칙 적용

            if new_content != content:
                changed += 1
                if not args.dry_run:
                    open(filepath, "w", encoding="utf-8").write(new_content)
                else:
                    print(f"  [DRY-RUN] Would modify: {filepath}")
            else:
                skipped += 1
        except Exception as e:
            errors.append((filepath, str(e)))
            print(f"  [ERROR] {filepath}: {e}")

    print(f"\nResults: {changed} modified, {skipped} unchanged, {len(errors)} errors")
    if errors:
        print("Errors:")
        for f, e in errors:
            print(f"  - {f}: {e}")

def process(content, filepath):
    """규칙서 기반 변환 로직"""
    # ... 규칙 적용 코드 ...
    return content

if __name__ == "__main__":
    main()
```

### Step 2: Dry-run 실행

```bash
python3 /tmp/{script_name}.py --dry-run {target_folder}
```

- 변경 예정 파일 수 확인
- 에러 예상치 확인
- 예상과 다르면 스크립트 수정

### Step 3: 사용자 승인

```
Dry-run 결과:
- 변경 예정: {N}개 파일
- 예상 에러: {N}개

실행하시겠습니까? (예/아니오)
```

> 사용자 승인 없이 실행 금지.

### Step 4: 실행 + 즉시 커밋

```bash
# 실행
python3 /tmp/{script_name}.py {target_folder}

# 즉시 커밋 (auto-sync 경합 방지)
cd {project_root} && git add -A && git commit -m "{Phase}: {설명} ({N} files)" && git push
```

### Step 5: Spot-check 검증

```
1. Glob으로 변경된 파일 목록 확인
2. 5개 랜덤 파일 Read로 내용 확인
3. 예상 구조와 일치하는지 검증
```

---

## 표준 스크립트 템플릿

### apply_footers.py (푸터 삽입)

```python
# 핵심 데이터 구조 (규칙서에서 변환)
SERIES_REGISTRY = {
    "시리즈명": {
        "category": "카테고리-MOC",
        "members": ["파일1.md", "파일2.md"],  # 순서대로
        "status": "complete"  # complete | ongoing
    }
}

CROSS_LINKS = {
    "교차주제": {
        "catA": "카테고리A-MOC",
        "catB": "카테고리B-MOC",
        "pairs": [("파일A.md", "파일B.md")]
    }
}

CLUSTERS = {
    "클러스터명": ["파일1.md", "파일2.md", "파일3.md"]
}

def generate_footer(filepath, content):
    """규칙서 기반 푸터 생성"""
    sections = []
    filename = os.path.basename(filepath)

    # 같은 시리즈
    series_section = get_series_section(filename)
    if series_section:
        sections.append(series_section)

    # 유사 주제 (최대 5개, 교차 카테고리 최대 3개)
    similar = get_similar_topics(filename, max_total=5, max_cross=3)
    if similar:
        sections.append(similar)

    # 답글/원글
    replies = get_reply_chain(filename)
    if replies:
        sections.append(replies)

    if not sections:
        return ""

    footer = "\n---\n\n## 관련 노트\n\n"
    footer += "\n\n".join(sections)
    footer += f"\n\n---\n← [[{get_category_moc(filename)}|카테고리]] · [[메인-MOC|전체 목록]]"
    return footer
```

### update_mocs.py (MOC 업데이트)

```python
def generate_main_moc(categories, series, stats):
    """메인 MOC 생성"""
    content = f"""---
title: "{project_name} MOC"
type: MOC
---

# {project_name} MOC

## 카테고리

| 카테고리 | 편수 | 설명 |
|---------|------|------|
"""
    for cat in categories:
        content += f"| [[{cat['moc']}|{cat['name']}]] | {cat['count']} | {cat['desc']} |\n"

    content += "\n## 시리즈 인덱스\n\n| 시리즈 | 편수 | 카테고리 |\n|--------|------|--------|\n"
    for s in series:
        content += f"| {s['name']} | {s['count']} | [[{s['category']}]] |\n"

    content += f"\n## 통계\n\n- **전체 글**: {stats['total']}편\n"
    return content

def generate_category_moc(category, members, series):
    """카테고리별 MOC 생성"""
    # ... 카테고리 소속 글 + 시리즈 + 교차 링크 ...
```

### restructure.py (폴더 재구조화)

```python
def restructure(file_assignments, dry_run=False):
    """파일을 새 카테고리 폴더로 이동"""
    for filepath, new_folder in file_assignments.items():
        new_path = os.path.join(new_folder, os.path.basename(filepath))
        if dry_run:
            print(f"  [DRY-RUN] {filepath} → {new_path}")
        else:
            os.makedirs(new_folder, exist_ok=True)
            os.rename(filepath, new_path)
```

---

## Auto-sync 경합 대응

### 예방

```
매 배치 후 즉시 커밋:
git add -A && git commit -m "{msg}" && git push
```

### 경합 발생 시 복구

```bash
# 1. auto-sync가 덮어쓴 파일 되돌리기
git checkout -- .

# 2. 스크립트 재실행
python3 /tmp/{script_name}.py {target_folder}

# 3. 즉시 커밋+푸시 (지연 없이!)
git add -A && git commit -m "re-apply: {msg}" && git push
```

### 감지 방법

```bash
# git status에서 예상치 않은 변경 확인
git status --short | head -20

# 최근 커밋과 working tree 차이 확인
git diff --stat
```

---

## 에러 처리

### 개별 파일 에러

- 해당 파일 스킵, 나머지 계속 처리
- 에러 로그에 기록
- 배치 완료 후 에러 파일 목록 표시

### 전체 배치 에러

- 즉시 중단
- git checkout으로 변경 되돌리기
- 원인 분석 후 스크립트 수정

### 인코딩 에러

```python
# UTF-8 with BOM 대응
content = open(filepath, encoding="utf-8-sig").read()
```

---

## 참조

| 스킬 | 관계 |
|------|------|
| `km-archive-reorganization.md` | Phase R4에서 이 스킬 호출 |
| `km-rules-engine.md` | Step 6에서 스크립트 생성 지시 |

## 검증된 사례

- **얼룩소 아카이브**: apply_footers.py (587파일), update_mocs.py (9개 MOC)
  - auto-sync 경합 1회 발생 → git checkout + 재적용 + 즉시 push로 복구
  - 결과: 587/587 100% 커버리지
