# GLM-OCR 스킬

> Knowledge Manager의 고속 로컬 OCR 엔진. PaddleOCR-VL 대비 5.6배 빠른 속도.
> **Optional Enhancement** - 설치 여부에 관계없이 Knowledge Manager는 정상 작동합니다.

---

## 모델 정보

| 항목 | 값 |
|------|-----|
| 모델 | GLM-OCR (0.9B params) |
| 정확도 | 94.62% (OmniDocBench v1.5 #1) |
| 지원 언어 | 8개 언어 (한국어, 영어, 중국어 등) |
| 라이센스 | MIT |
| HuggingFace | `zai-org/GLM-OCR` |
| 설치 크기 | ~4GB (PyTorch + 모델 + 의존성) |

### 공식 벤치마크 (Z.AI)

| 메트릭 | 수치 |
|--------|------|
| OmniDocBench V1.5 | 94.62 (#1) |
| PDF 처리 속도 | 1.86 pages/sec |
| 이미지 처리 속도 | 0.67 images/sec |

---

## OCR Tier 위치

```
Tier 1: Claude Read Tool (직접 읽기)
Tier 2: Marker (속도+구조 우위, Markdown 네이티브)
Tier 3: GLM-OCR ← 이 스킬 (선택적 설치, 스캔/수식/테이블/복잡 문서 특화)
Tier 4: Gemini Flash OCR (최종 폴백)
```

> 배포용/로컬 모두 동일한 Tier 구조를 사용합니다.

### 비교 테스트 실측 데이터

> 2026-02-03, RTX 5060 Ti 16GB, PDF 3페이지 기준:
> - **Marker**: 37.6초, Markdown 구조화 (테이블, 헤딩, 링크 보존)
> - **GLM-OCR**: 55.6초 (18.5초/페이지), 평문 추출
> - **PaddleOCR-VL**: 312.7초 (104초/페이지), 평문 추출
> - GLM-OCR은 PaddleOCR-VL 대비 **5.6배 빠름**

### GLM-OCR (Tier 3) 적용 조건

Marker(Tier 2)가 실패하거나 부족한 경우 GLM-OCR로 폴백:
1. **Marker 실패 시** (파싱 에러, 빈 결과 등)
2. **수식이 포함된 문서** → `Formula Recognition:` 태스크 (Marker 미지원)
3. **테이블이 복잡한 문서** → `Table Recognition:` 태스크 (Marker로 구조 깨질 때)
4. **스캔/왜곡된 문서** (사진 촬영, 기울어진, 저품질 스캔)
5. **코드 블록이 많은 문서** → GLM-OCR이 코드 인식에 강점

### 사용하지 않는 경우

- Claude Read가 성공한 일반 PDF → Tier 1으로 충분
- Marker가 성공한 경우 → Tier 2로 충분
- GLM-OCR이 설치되지 않은 환경 → Tier 4 (Gemini Flash)로 폴백

---

## 설치 방법

### 요구 사항

| 항목 | 최소 요건 | 권장 요건 |
|------|----------|----------|
| GPU | NVIDIA CUDA GPU | VRAM 8GB+ |
| VRAM | 4GB (가능은 하나 느림) | 8GB+ (쾌적) |
| 디스크 여유 | 4GB | 8GB+ |
| Python | 3.10~3.12 | 3.12 |
| transformers | 5.0.1+ (git 버전) | 최신 git 버전 |

### 신규 설치

```bash
# 1. venv 생성 (기존 paddleocr-vl venv 재사용 가능)
# Python 3.12 권장
python3 -m venv .venvs/glm-ocr

# 2. 의존성 설치
".venvs/glm-ocr/bin/pip" install torch torchvision --index-url https://download.pytorch.org/whl/cu128
".venvs/glm-ocr/bin/pip" install git+https://github.com/huggingface/transformers.git
".venvs/glm-ocr/bin/pip" install accelerate pillow pymupdf

# 3. 모델 다운로드 (첫 실행 시 자동, ~2GB)
```

### 기존 paddleocr-vl venv 업그레이드

```bash
# transformers를 git 버전으로 업그레이드
".venvs/paddleocr-vl/bin/pip" install --upgrade git+https://github.com/huggingface/transformers.git
```

---

## 가용성 체크 (MANDATORY)

GLM-OCR 호출 전 **반드시** 가용성 확인:

### venv 존재 여부 확인

```bash
# paddleocr-vl venv 재사용
test -f .venvs/paddleocr-vl/bin/python && echo AVAILABLE || echo NOT_AVAILABLE

# 또는 전용 venv
test -f .venvs/glm-ocr/bin/python && echo AVAILABLE || echo NOT_AVAILABLE
```

**결과별 분기:**
- venv 존재 + transformers 5.0.1+ → GLM-OCR 사용 (Tier 3)
- 그 외 → Tier 4 (Gemini Flash)로 폴백

---

## 3가지 태스크 프롬프트

GLM-OCR은 프롬프트로 태스크를 지정합니다:

| 태스크 | 프롬프트 | 용도 |
|--------|---------|------|
| 일반 OCR | `Text Recognition:` | 일반 텍스트 인식 |
| 테이블 인식 | `Table Recognition:` | 표/테이블 구조 추출 |
| 수식 인식 | `Formula Recognition:` | 수학 공식 LaTeX 추출 |

### 문서 유형별 자동 태스크 선택

| 문서 유형 | 기본 태스크 | 추가 태스크 |
|----------|-----------|-----------|
| 일반 문서 | `Text Recognition:` | - |
| 표 포함 문서 | `Text Recognition:` | `Table Recognition:` |
| 학술 논문 | `Text Recognition:` | `Formula Recognition:` + `Table Recognition:` |
| 코드 문서 | `Text Recognition:` | - (코드 인식 강점) |
| 스캔 문서 | `Text Recognition:` (왜곡 자동 처리) | - |

---

## 호출 방법

### 방법 A: Transformers API (권장 - 로컬 venv)

```python
import time
import torch
from transformers import AutoProcessor, AutoModelForImageTextToText
from PIL import Image

MODEL_PATH = "zai-org/GLM-OCR"

# 모델 로드
processor = AutoProcessor.from_pretrained(MODEL_PATH)
model = AutoModelForImageTextToText.from_pretrained(
    MODEL_PATH,
    torch_dtype="auto",
    device_map="auto"
)

# 메시지 구성
messages = [
    {
        "role": "user",
        "content": [
            {"type": "image", "url": "INPUT_IMAGE_PATH"},
            {"type": "text", "text": "Text Recognition:"}
        ],
    }
]

# 추론
inputs = processor.apply_chat_template(
    messages,
    tokenize=True,
    add_generation_prompt=True,
    return_dict=True,
    return_tensors="pt"
).to(model.device)

inputs.pop("token_type_ids", None)

generated_ids = model.generate(**inputs, max_new_tokens=8192)
output_text = processor.decode(
    generated_ids[0][inputs["input_ids"].shape[1]:],
    skip_special_tokens=True
)

print(output_text)
```

**실행 예시:**
```bash
".venvs/glm-ocr/bin/python" "test_glm_ocr.py"
```

### 방법 B: Ollama (설치 필요)

```bash
# Ollama 설치 후
ollama run glm-ocr "Text Recognition: ./image.png"
```

### 방법 C: vLLM 서버 (선택 - 서버 모드)

```bash
# vLLM 서버 실행
pip install vllm --extra-index-url https://wheels.vllm.ai/nightly
vllm serve zai-org/GLM-OCR --allowed-local-media-path / --port 8080

# API 호출
curl -s http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "zai-org/GLM-OCR",
    "messages": [
      {
        "role": "user",
        "content": [
          {"type": "image_url", "image_url": {"url": "data:image/png;base64,{BASE64_IMAGE}"}},
          {"type": "text", "text": "Text Recognition:"}
        ]
      }
    ],
    "max_tokens": 8192
  }'
```

---

## Knowledge Manager 통합 워크플로우

### PDF 처리 시

```
Step 1: Claude Read 시도 (Tier 1)
  → 성공? → 내용 처리 (종료)
  → 실패? → Step 2

Step 2: Marker 실행 (Tier 2)
  marker_single.exe "{PDF경로}" --output_format markdown --output_dir ./km-temp
  → 성공? → 내용 처리 (종료)
  → 실패? → Step 3

Step 3: GLM-OCR 가용성 체크 (Tier 3)
  venv 존재 확인: .venvs/paddleocr-vl/bin/python (또는 glm-ocr venv)
  → 존재? → Step 4
  → 미설치? → Step 5 (Gemini 폴백)

Step 4: GLM-OCR 실행
  a) PDF → 이미지 변환 (페이지별, PyMuPDF)
  b) 각 이미지에 대해 태스크 실행:
     - 기본: "Text Recognition:"
     - 테이블 감지 시: "Table Recognition:" 추가
     - 수식 감지 시: "Formula Recognition:" 추가
  c) 결과 Markdown으로 통합
  → 성공? → 내용 처리 (종료)
  → 실패? → Step 5

Step 5: Gemini Flash OCR (Tier 4 - 최종)
```

### 이미지 처리 시

```
Step 1: Claude Read (Vision) 시도 (Tier 1)
  → 성공? → 내용 처리 (종료)
  → 실패? → Step 2

Step 2: Marker 시도 (Tier 2)
  → 성공? → 내용 처리 (종료)
  → 실패 또는 수식/테이블 등 특수 인식 필요? → Step 3

Step 3: GLM-OCR 호출 (Tier 3)
  - venv 존재 확인
  - 이미지 파일 그대로 입력
  - 적절한 태스크 프롬프트 선택
  → 결과 반환
```

---

## 배포 전략: Optional Enhancement 패턴

### 미설치 환경 (기본)

```
Tier 1: Claude Read → Tier 2: Marker → Tier 3: Gemini Flash
(기존 3-Tier, GLM-OCR 없이 정상 작동)
```

### 설치 환경 (향상)

```
Tier 1: Claude Read → Tier 2: Marker → Tier 3: GLM-OCR → Tier 4: Gemini Flash
(Marker 실패 또는 수식/테이블 등 특수 인식 필요 시 GLM-OCR 활성화)
```

> 배포용/로컬 동일 구조. GLM-OCR 미설치 시 자동 건너뜀.

### 설치 제거

```bash
# venv 삭제만으로 완전 제거
rm -rf .venvs/glm-ocr
```

모델 캐시 제거 (선택):
```bash
# HuggingFace 캐시에서 모델 삭제
# Windows: %USERPROFILE%\.cache\huggingface\hub\models--zai-org--GLM-OCR
# Linux: ~/.cache/huggingface/hub/models--zai-org--GLM-OCR
```

---

## 에러 처리

| 에러 | 원인 | 대응 |
|------|------|------|
| venv 미존재 | 미설치 | Tier 4 (Gemini Flash)로 폴백 |
| `KeyError: 'glm_ocr'` | transformers 구버전 | `pip install git+https://...transformers.git` |
| CUDA OOM | 이미지가 너무 큼 | 이미지 리사이즈 후 재시도 |
| 빈 결과 반환 | 이미지 품질 문제 | max_new_tokens 증가 (8192) |
| 느린 응답 | GPU 부하 또는 CPU 모드 | 타임아웃 설정 (60초) 후 Tier 4 폴백 |

---

## 성능 참고

### 실측 데이터 (2026-02-03, RTX 5060 Ti 16GB)

**GLM-OCR (Transformers API, 150 DPI):**

| 페이지 | 추론 시간 | 추출 문자 |
|--------|----------|----------|
| Page 1 | 17.76초 | 2,825자 |
| Page 2 | 15.86초 | 3,166자 |
| Page 3 | 22.00초 | 4,546자 |
| **합계** | **55.62초** | **10,537자** |

**속도 비교:**

| 항목 | GLM-OCR | PaddleOCR-VL-1.5 | Marker |
|------|---------|------------------|--------|
| 3페이지 처리 시간 | **55.62초** | 312.7초 | 37.6초 |
| 페이지당 평균 | 18.54초 | 104초 | 12.5초 |
| 속도 비교 | 5.6x 빠름 (vs Paddle) | 기준 | 4.4x 빠름 |
| 구조화 | 평문 | 평문 | Markdown |

> **권장 사용 시나리오**: Marker 실패 시 폴백, 스캔 문서, 수식, 코드 블록, 복잡한 테이블

### 스펙

| 항목 | 값 |
|------|-----|
| 모델 크기 | ~2 GB |
| 설치 총 크기 | ~4 GB (venv 포함) |
| VRAM 사용량 | ~3 GB (추론 시) |
| 지원 형식 | PNG, JPG, PDF (페이지별 변환 필요) |
| 첫 실행 모델 다운로드 | ~2 GB (HuggingFace, 1회만) |

---

## 파일 구조

```
.claude/
  skills/
    km-glm-ocr.md             ← 이 파일 (스킬 문서)
.venvs/
  paddleocr-vl/               ← 기존 venv 재사용 가능 (transformers 업그레이드 필요)
    bin/python
  glm-ocr/                    ← 또는 전용 venv
    bin/python
```

---

## PaddleOCR에서 마이그레이션

### 변경 사항

| 항목 | PaddleOCR-VL-1.5 | GLM-OCR |
|------|------------------|---------|
| 모델 경로 | `PaddlePaddle/PaddleOCR-VL-1.5` | `zai-org/GLM-OCR` |
| 기본 프롬프트 | `OCR:` | `Text Recognition:` |
| 속도 | 104초/페이지 | **18.5초/페이지** |
| 도장 인식 | `Seal Recognition:` 지원 | 미지원 |
| 차트 인식 | `Chart Recognition:` 지원 | 미지원 |
| 코드 인식 | 보통 | **우수** |

### 마이그레이션 단계

1. transformers 업그레이드: `pip install git+https://...transformers.git`
2. 모델 경로 변경: `PaddlePaddle/...` → `zai-org/GLM-OCR`
3. 프롬프트 변경: `OCR:` → `Text Recognition:`
4. (선택) 도장/차트 인식 필요 시 PaddleOCR 유지 또는 Gemini 폴백 사용
