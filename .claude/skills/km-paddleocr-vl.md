# PaddleOCR-VL-1.5 OCR 스킬

> Knowledge Manager의 고품질 로컬 OCR 엔진. 테이블/수식/차트/도장 인식 지원.
> **Optional Enhancement** - 설치 여부에 관계없이 Knowledge Manager는 정상 작동합니다.

---

## 모델 정보

| 항목 | 값 |
|------|-----|
| 모델 | PaddleOCR-VL-1.5 (0.9B params) |
| 정확도 | 94.5% (OmniDocBench v1.5 SOTA) |
| 지원 언어 | 90+ 언어 (한국어, 영어, 중국어 등) |
| 라이센스 | Apache 2.0 |
| HuggingFace | `PaddlePaddle/PaddleOCR-VL-1.5` |
| 설치 크기 | ~8GB (PyTorch + 모델 + 의존성) |

---

## OCR Tier 위치

```
Tier 1: Claude Read Tool (직접 읽기)
Tier 2: Marker (속도+구조 우위, Markdown 네이티브)
Tier 3: PaddleOCR-VL-1.5 ← 이 스킬 (선택적 설치, 스캔/수식/차트/도장 특화)
Tier 4: Gemini Flash OCR (최종 폴백)
```

> 배포용/로컬 모두 동일한 Tier 구조를 사용합니다.

### 비교 테스트 실측 데이터

> 2026-01-30, RTX 5060 Ti, 디지털 PDF 3페이지 기준:
> - **Marker**: 37.6초, Markdown 구조화 (테이블, 헤딩, 링크 보존)
> - **PaddleOCR-VL**: 312.7초, 평문 추출
> - Marker가 속도 7배, 구조화 품질 우위 → **Tier 2가 Marker인 이유**

### PaddleOCR-VL-1.5 (Tier 3) 적용 조건

Marker(Tier 2)가 실패하거나 부족한 경우 PaddleOCR-VL-1.5로 폴백:
1. **Marker 실패 시** (파싱 에러, 빈 결과 등)
2. **수식이 포함된 문서** → `Formula Recognition:` 태스크 (Marker 미지원)
3. **차트/그래프가 포함된 문서** → `Chart Recognition:` 태스크 (Marker 미지원)
4. **도장/인감이 포함된 문서** → `Seal Recognition:` 태스크 (Marker 미지원)
5. **스캔/왜곡된 문서** (사진 촬영, 기울어진, 저품질 스캔)
6. **복잡한 테이블** → `Table Recognition:` 태스크 (Marker로 구조 깨질 때)

### 사용하지 않는 경우

- Claude Read가 성공한 일반 PDF → Tier 1으로 충분
- Marker가 성공한 경우 → Tier 2로 충분
- PaddleOCR-VL-1.5가 설치되지 않은 환경 → Tier 4 (Gemini Flash)로 폴백

---

## 환경 자동 감지 및 설치 (배포용)

### 설치 전 환경 진단 (MANDATORY)

PaddleOCR-VL-1.5 설치 전 **반드시** 환경 진단 스크립트를 실행합니다:

```bash
python .claude/scripts/paddleocr-env-check.py --check
```

**진단 항목:**

| 항목 | 최소 요건 | 권장 요건 |
|------|----------|----------|
| GPU | NVIDIA CUDA GPU | VRAM 8GB+ |
| VRAM | 4GB (가능은 하나 느림) | 8GB+ (쾌적) |
| 디스크 여유 | 8GB | 12GB+ |
| Python | 3.10~3.13 | 3.12 |
| OS | Windows / Linux | - |

**진단 결과별 분기:**

| 결과 | 의미 | 행동 |
|------|------|------|
| `RECOMMENDED` | 모든 요건 충족 | 설치 진행 |
| `POSSIBLE` | 일부 제한 있음 (경고 참고) | 사용자에게 경고 표시 후 설치 여부 확인 |
| `NOT_RECOMMENDED` | 필수 요건 미충족 | 설치 미권장 안내, Tier 3로 운영 |

### 자동 설치

환경 진단 통과 후 설치:

```bash
python .claude/scripts/paddleocr-env-check.py --install
```

**자동으로 수행되는 작업:**
1. Python venv 생성: `.venvs/paddleocr-vl/`
2. PyTorch 설치 (GPU 감지 시 CUDA 버전, 미감지 시 CPU 버전)
3. Transformers + accelerate + Pillow + huggingface_hub 설치
4. 설치 검증 (import 테스트)

**NOTE:** 모델 가중치(~2GB)는 첫 OCR 실행 시 HuggingFace에서 자동 다운로드됩니다.

### JSON 모드 (머신 파싱용)

```bash
python .claude/scripts/paddleocr-env-check.py --json
```

Claude Code에서 프로그래밍적으로 환경 확인 시 사용:

```python
import json, subprocess
result = subprocess.run(
    ["python", ".claude/scripts/paddleocr-env-check.py", "--json"],
    capture_output=True, text=True
)
env = json.loads(result.stdout)
can_install = env["evaluation"]["overall"] != "NOT_RECOMMENDED"
```

---

## 가용성 체크 (MANDATORY)

PaddleOCR-VL-1.5 호출 전 **반드시** 가용성 확인:

### 방법 1: venv 존재 여부 확인 (권장)

```bash
# Windows
if exist ".venvs\paddleocr-vl\Scripts\python.exe" (echo AVAILABLE) else (echo NOT_AVAILABLE)

# Linux/macOS
test -f .venvs/paddleocr-vl/bin/python && echo AVAILABLE || echo NOT_AVAILABLE
```

### 방법 2: JSON 진단으로 확인

```bash
python .claude/scripts/paddleocr-env-check.py --json
# → existing_venv.functional == true 이면 사용 가능
```

### 방법 3: vLLM 서버 체크 (서버 모드 사용 시)

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health
```

**결과별 분기:**
- venv 존재 + functional → PaddleOCR-VL-1.5 사용 (Tier 3)
- 그 외 → Tier 4 (Gemini Flash)로 폴백

---

## 6가지 태스크 프롬프트

PaddleOCR-VL-1.5는 프롬프트로 태스크를 지정합니다:

| 태스크 | 프롬프트 | 용도 |
|--------|---------|------|
| 일반 OCR | `OCR:` | 일반 텍스트 인식 |
| 테이블 인식 | `Table Recognition:` | 표/테이블 구조 추출 |
| 수식 인식 | `Formula Recognition:` | 수학 공식 LaTeX 추출 |
| 차트 분석 | `Chart Recognition:` | 차트/그래프 데이터 추출 |
| 텍스트 검출 | `Spotting:` | 텍스트 위치 + 바운딩 박스 |
| 도장 인식 | `Seal Recognition:` | 도장/인감 텍스트 추출 |

### 문서 유형별 자동 태스크 선택

| 문서 유형 | 기본 태스크 | 추가 태스크 |
|----------|-----------|-----------|
| 일반 문서 | `OCR:` | - |
| 표 포함 문서 | `OCR:` | `Table Recognition:` |
| 학술 논문 | `OCR:` | `Formula Recognition:` + `Table Recognition:` |
| 비즈니스 보고서 | `OCR:` | `Chart Recognition:` + `Table Recognition:` |
| 계약서/공문서 | `OCR:` | `Seal Recognition:` |
| 스캔 문서 | `OCR:` (왜곡 자동 처리) | - |

---

## 호출 방법

### 방법 A: Transformers API (권장 - 로컬 venv)

```bash
# venv의 Python으로 직접 실행
"{PROJECT_ROOT}/.venvs/paddleocr-vl/Scripts/python.exe" -c "
import torch
from PIL import Image
from transformers import AutoProcessor, AutoModelForImageTextToText

model_path = 'PaddlePaddle/PaddleOCR-VL-1.5'
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

model = AutoModelForImageTextToText.from_pretrained(
    model_path, torch_dtype=torch.bfloat16
).to(DEVICE).eval()

processor = AutoProcessor.from_pretrained(model_path)

# 태스크별 프롬프트
task_prompt = 'OCR:'  # 또는 'Table Recognition:', 'Formula Recognition:' 등

messages = [{
    'role': 'user',
    'content': [
        {'type': 'image', 'image': Image.open('INPUT_IMAGE_PATH').convert('RGB')},
        {'type': 'text', 'text': task_prompt},
    ]
}]

inputs = processor.apply_chat_template(
    messages,
    add_generation_prompt=True,
    tokenize=True,
    return_dict=True,
    return_tensors='pt'
).to(model.device)

outputs = model.generate(**inputs, max_new_tokens=4096)
result = processor.decode(outputs[0][inputs['input_ids'].shape[-1]:-1])
print(result)
"
```

**Windows 경로 예시:**
```bash
"C:\Users\{USER}\OneDrive\Desktop\AI\.venvs\paddleocr-vl\Scripts\python.exe" -c "..."
```

**Linux 경로 예시:**
```bash
".venvs/paddleocr-vl/bin/python" -c "..."
```

### 방법 B: PaddleOCR Python API

```bash
"{PROJECT_ROOT}/.venvs/paddleocr-vl/Scripts/python.exe" -c "
from paddleocr import PaddleOCRVL

pipeline = PaddleOCRVL()
output = pipeline.predict('INPUT_IMAGE_PATH')

for res in output:
    res.save_to_markdown(save_path='./km-temp')
"
```

### 방법 C: vLLM 서버 API (선택 - 서버 모드)

서버를 별도 실행한 경우에만 사용:

```bash
curl -s http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "PaddleOCR-VL-1.5-0.9B",
    "messages": [
      {
        "role": "user",
        "content": [
          {"type": "image_url", "image_url": {"url": "data:image/png;base64,{BASE64_IMAGE}"}},
          {"type": "text", "text": "OCR:"}
        ]
      }
    ],
    "max_tokens": 4096
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
  marker_single "{PDF경로}" --output_format markdown --output_dir ./km-temp
  → 성공? → 내용 처리 (종료)
  → 실패? → Step 3

Step 3: PaddleOCR-VL-1.5 가용성 체크 (Tier 3)
  venv 존재 확인: .venvs/paddleocr-vl/Scripts/python.exe
  → 존재? → Step 4
  → 미설치? → Step 5 (Gemini 폴백)

Step 4: PaddleOCR-VL-1.5 실행
  a) PDF → 이미지 변환 (페이지별)
  b) 각 이미지에 대해 태스크 실행:
     - 기본: "OCR:"
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
  → 실패 또는 수식/차트/도장 등 특수 인식 필요? → Step 3

Step 3: PaddleOCR-VL-1.5 호출 (Tier 3)
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
(기존 3-Tier, PaddleOCR 없이 정상 작동)
```

### 설치 환경 (향상)

```
Tier 1: Claude Read → Tier 2: Marker → Tier 3: PaddleOCR-VL → Tier 4: Gemini Flash
(Marker 실패 또는 수식/차트/도장 등 특수 인식 필요 시 PaddleOCR 활성화)
```

> 배포용/로컬 동일 구조. PaddleOCR-VL 미설치 시 자동 건너뜀.

### 사용자가 설치를 원할 때

1. 환경 진단: `python .claude/scripts/paddleocr-env-check.py --check`
2. 결과 확인 후 설치: `python .claude/scripts/paddleocr-env-check.py --install`
3. 첫 실행 시 모델 자동 다운로드 (~2GB, HuggingFace)

### 설치 제거

```bash
# venv 삭제만으로 완전 제거
# Windows
rmdir /s /q ".venvs\paddleocr-vl"

# Linux/macOS
rm -rf .venvs/paddleocr-vl
```

모델 캐시 제거 (선택):
```bash
# HuggingFace 캐시에서 모델 삭제
# Windows: %USERPROFILE%\.cache\huggingface\hub\models--PaddlePaddle--PaddleOCR-VL-1.5
# Linux: ~/.cache/huggingface/hub/models--PaddlePaddle--PaddleOCR-VL-1.5
```

---

## 서버 모드 (선택)

상시 서버로 운영하고 싶은 경우:

### vLLM 서버

```bash
# venv에서 vllm 추가 설치
pip install vllm
vllm serve PaddlePaddle/PaddleOCR-VL-1.5 --host 0.0.0.0 --port 8080
```

### Docker

```bash
docker run --rm --gpus all --network host \
    ccr-2vdh3abv-pub.cnc.bj.baidubce.com/paddlepaddle/paddleocr-genai-vllm-server:latest-nvidia-gpu \
    paddleocr genai_server --model_name PaddleOCR-VL-1.5-0.9B \
    --host 0.0.0.0 --port 8080 --backend vllm
```

---

## 에러 처리

| 에러 | 원인 | 대응 |
|------|------|------|
| venv 미존재 | 미설치 | Tier 4 (Gemini Flash)로 폴백 |
| import 실패 | 의존성 깨짐 | `--install`로 재설치 |
| CUDA OOM | 이미지가 너무 큼 | 이미지 리사이즈 후 재시도 |
| 빈 결과 반환 | 이미지 품질 문제 | `Spotting:` 태스크로 재시도 |
| 느린 응답 | GPU 부하 또는 CPU 모드 | 타임아웃 설정 (60초) 후 Tier 4 (Gemini Flash) 폴백 |
| Python 버전 호환 | 3.14+ 사용 중 | 3.12 별도 설치 후 `--install` |

---

## 성능 참고

### 실측 데이터 (2026-01-30, RTX 5060 Ti 16GB)

**PaddleOCR-VL-1.5 (Transformers API, 150 DPI):**

| 페이지 | 내용 | 해상도 | 추론 시간 | 추출 문자 |
|--------|------|--------|----------|----------|
| Page 1 (표지) | 제목+로고 | 1650x1275 (2.1M px) | 9.6초 | 58자 |
| Page 2 (목차) | 테이블 | 1650x1275 (2.1M px) | 35.2초 | 406자 |
| Page 3 (본문) | 긴 텍스트 | 1650x1275 (2.1M px) | 267.9초 | 2,138자 |
| **합계** | | | **312.7초** | **2,602자** |

**Marker 1.10.1 비교:**

| 항목 | PaddleOCR-VL-1.5 | Marker 1.10.1 |
|------|-------------------|---------------|
| 3페이지 처리 시간 | 312.7초 | **37.6초** (7배 빠름) |
| 추출 문자 수 | 2,602자 | 2,618자 |
| 구조화 (헤딩) | 평문 | **Markdown 헤딩** |
| 테이블 형식 | 공백 정렬 | **Markdown 테이블** |
| 링크 보존 | 미보존 | **하이퍼링크 보존** |

> **참고**: 텍스트 양이 많을수록 추론 시간이 급격히 증가합니다 (Page 3: 268초).
> 150 DPI에서도 2.1M pixels → 모델 최적 입력(~1M px) 대비 2배 초과.
> **디지털 PDF에는 Marker 사용을 권장합니다.**

### 스펙

| 항목 | 값 |
|------|-----|
| 모델 크기 | ~2 GB (BF16) |
| 설치 총 크기 | ~8 GB (venv 포함) |
| 최대 입력 해상도 | ~1M pixels (기본), ~1.6M pixels (Spotting) |
| 지원 형식 | PNG, JPG, PDF (페이지별 변환 필요) |
| 첫 실행 모델 다운로드 | ~2 GB (HuggingFace, 1회만) |
| **권장 사용 시나리오** | **스캔 문서, 수식, 차트, 도장, 왜곡 문서** |

---

## 파일 구조

```
.claude/
  scripts/
    paddleocr-env-check.py    ← 환경 진단 + 자동 설치 스크립트
  skills/
    km-paddleocr-vl.md        ← 이 파일 (스킬 문서)
.venvs/
  paddleocr-vl/               ← 설치 시 생성되는 Python venv
    Scripts/python.exe         (Windows)
    bin/python                 (Linux/macOS)
```
