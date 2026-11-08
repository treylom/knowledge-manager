---
name: km-content-extraction
description: Content extraction routing for KM - local documents (HWP/HWPX/PDF/DOCX/XLSX), web, and vault sources. Use when input is a local file or when km-workflow reaches Phase 2 with a non-URL input.
---

# KM Content Extraction (Codex)

> km-workflow Phase 2 의 추출 라우터. **입력 형식을 먼저 판정하고, 아래 표의 도구를 실제로 호출한다** — 도구 호출 없이 콘텐츠를 추측·요약하는 것은 금지.
> 전문(이미지 파이프라인·병렬 처리·포맷별 상세)은 플러그인 `skills/km-content-extraction.md` (1,087줄) 참조.

## 소스별 추출 라우팅 (필수 도구 호출)

| 소스 유형 | 🚨 필수 도구 호출 |
|----------|------------------|
| **한글 (HWP/HWP3/HWPX/HWPML)** | **kordoc**: `npx -y kordoc@4.24.47 <files> -d <outdir>` → 변환 md 를 `Read` — anydoc 은 HWP 미지원, 한글 문서는 처음부터 kordoc |
| PDF | 1순위 `Read` → 2순위 `opendataloader-pdf` → 3순위 `marker_single` — 🔴 anydoc 으로 보내지 않는다(다단 레이아웃 순서 붕괴) |
| Word (DOCX) | 1순위 `npx -y @firecrawl/anydoc@0.2.4 "[파일]"` → 2순위 `Read` — 표가 복잡해 깨지면 kordoc |
| Excel (XLSX) | 1순위 `npx -y @firecrawl/anydoc@0.2.4 "[파일]"` (수식 없는 표 한정) — 수식·분석·편집은 xlsx 계열 도구 |
| CSV | `Read` (anydoc 편입 보류 — 헤더 밀림) |
| PowerPoint | `Read` (anydoc 미편입 — 슬라이드 경계 소실) |
| TXT/MD | `Read` |
| 이미지 | `Read` (Vision) |
| 일반 웹/소셜 | → `$km:km-browser-abstraction` / `$km:km-social-media` |
| Vault 종합 | → `$km:km-search` |

## 한국어 로컬 문서 fallback = kordoc

입력이 로컬 문서인데 기본 경로(`Read`·anydoc)로 충실히 못 읽는 형식 — **HWP·HWPX, 표가 복잡한 XLSX/DOCX, 한국어 PDF** — 은 kordoc 으로 마크다운 변환 후 진행한다:

```bash
npx -y kordoc@4.24.47 <files> -d <outdir>   # HWP3/HWP/HWPX/HWPML/PDF/XLS/XLSX/DOCX/이미지(OCR — 기본은 Read) → Markdown
```

- `<files>` 복수 일괄 지원. 산출 = `<outdir>/<파일명>.md`.
- 변환 md 는 **원문 보존 검증**(표 행수·수치 표본 대조) 후 사용한다.
- Pinned versions = kordoc 4.24.47 · anydoc 0.2.4 (verified by running 2026-11-06) — to upgrade, check the new version with `npm view <package> version`, run it once, then change this line and the calls together.
- PDF (`pdfjs-dist`) and OCR runtimes install automatically as optional dependencies — no separate peer install (measured on 4.15.7; the pinned 4.24.47 was re-checked only for docx, HWP and HWPX — PDF/OCR not re-checked) / PDF(`pdfjs-dist`)·OCR 런타임은 선택 의존성으로 자동 설치(별도 peer 설치 불필요 — 4.15.7 실측 · 고정 버전 4.24.47 은 docx·HWP·HWPX 만 다시 확인 · PDF·OCR 은 다시 확인하지 않음), OCR 모델은 첫 사용 시 다운로드 — 스캔 PDF `--ocr`(~18MB) · 수식 `--formula-ocr`(~155MB) · RAG 청크 `--format chunks`.

## anydoc ↔ kordoc 역할 분리

| | anydoc | kordoc |
|---|---|---|
| 고유 영역 | epub · rtf · odt/ods/odp | **HWP3/HWP/HWPX/HWPML** (anydoc 미지원) |
| 겹치는 영역 | DOCX · XLS/XLSX · PDF | DOCX · XLS/XLSX · PDF |
| 성격 | 순수 Rust · 1회 호출 = 1문서 | Node · 한국어 특화 · 복수 일괄 |

- DOCX·XLSX 기본 = anydoc. 깨지거나 한글(HWP) 계열이면 kordoc.
- 🔴 PDF 는 anydoc 금지(순서 붕괴) — 위 표의 다단 경로 유지.

## Phase 2 완료 검증 (필수)

```
□ 해당 소스 유형의 도구를 실제로 호출했는가?
□ 도구 응답에서 추출된 실제 텍스트를 확인했는가 (추측 아님)?
□ 변환 문서는 원문 보존 검증(표 행수·수치 표본)을 했는가?
⚠️ 미완료 시 Phase 3(분석) 진행 금지.
```
