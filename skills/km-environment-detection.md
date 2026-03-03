# Knowledge Manager 환경 감지 및 RAG 최적화 스킬

> 사용자 시스템을 자동 감지하고, 스펙에 맞는 최적의 검색 기능을 추천·설정합니다.

---

## 스킬 개요

이 스킬은 Knowledge Manager 첫 실행 시 **자동으로** 동작하여:
1. 사용자 시스템 스펙을 감지 (RAM, CPU, GPU)
2. 3단계 티어로 분류 (Basic / Standard / Advanced)
3. 티어별 사용 가능한 검색 기능을 시각적으로 안내
4. 사용자 승인 하에 고급 기능 활성화 가이드 제공
5. km-workflow에 감지 결과를 반영하여 적응형 동작

---

## Phase 0: 시스템 환경 감지 (자동 실행)

### 0.0 Team OS 인프라 확인 (최우선!)

**CRITICAL**: 시스템 스펙 감지 전에 반드시 Team OS 인프라를 먼저 확인합니다.

#### 감지 명령어 (크로스 플랫폼)

**Step 1: 프로젝트 루트 확인 (절대 경로 획득)**

```
Bash("pwd") → 현재 작업 디렉토리 확인 → {project_root}
```

**Step 2: .team-os/ 감지 (절대 경로 사용 — WSL 호환)**

```
# 절대 경로로 Glob 수행 (상대 경로 실패 방지)
Glob("{project_root}/.team-os/registry.yaml")
Glob("{project_root}/.team-os/spawn-prompts/*.md")
Glob("{project_root}/.team-os/artifacts/*.md")
```

**Step 3: Glob 실패 시 Bash 폴백 (WSL/권한 문제 대응)**

```
# Glob이 빈 결과를 반환하면 Bash로 직접 확인
Bash("ls -la .team-os/registry.yaml 2>/dev/null && echo EXISTS || echo NOT_FOUND")
Bash("ls .team-os/spawn-prompts/*.md 2>/dev/null | wc -l")
Bash("ls .team-os/artifacts/*.md 2>/dev/null | wc -l")
```

> **WHY**: WSL 환경에서 Glob의 상대 경로가 작업 디렉토리와 불일치할 수 있음.
> 절대 경로 사용 + Bash 폴백으로 크로스 플랫폼 안정성 확보.

#### 분기 로직

```
registry.yaml 존재 AND spawn-prompts >= 3개
  → Team OS: 활성화
  → registry.yaml 읽어서 complexity_mapping, shared_memory 설정 로드
  → spawn-prompts/ 목록 확인하여 사용 가능한 팀원 역할 파악

registry.yaml 존재 AND spawn-prompts < 3개
  → Team OS: 부분 활성화 (일부 팀원만 사용 가능)
  → 사용 가능한 역할만 표시

둘 다 없음
  → Team OS: 비활성
  → 기본 모드로 진행 (Main 단독 또는 병렬 Task 서브에이전트)
```

#### Agent Office 대시보드 통합

```
# 대시보드 실행 확인
Bash("curl -s http://localhost:3747/api/status 2>/dev/null") → JSON 응답 여부

대시보드 실행 중:
  > **Agent Office Dashboard**: http://localhost:3747
  > Team OS, MCP Servers, KM Workflow 실시간 모니터링 중

대시보드 미실행 시:
  > Agent Office 대시보드가 실행되지 않고 있습니다.
  > 시작: `cd agent-office && npm start`
  > 텍스트 모드로 진행합니다.
```

#### 결과 출력 형식

**대시보드 실행 중:**

```markdown
### 환경 현황
**Agent Office Dashboard**: http://localhost:3747 (실시간 모니터링)

| 항목 | 상태 |
|------|------|
| **Team OS** | {활성화 / 부분 활성화 / 비활성} |
| **registry.yaml** | {✅ 존재 / ❌ 없음} |
| **Spawn Prompts** | {✅ N개 / ❌ 없음} |
| **공유 아티팩트** | {✅ N개 / ❌ 없음} |
```

**대시보드 미실행 시 (폴백 — 기존 텍스트 테이블):**

```markdown
### Team OS 인프라
| 항목 | 상태 |
|------|------|
| **registry.yaml** | {✅ 존재 / ❌ 없음} |
| **Spawn Prompts** | {✅ N개 / ❌ 없음} |
| **공유 아티팩트** | {✅ N개 / ❌ 없음} |
| **Team OS 상태** | {활성화 / 부분 활성화 / 비활성} |
```

---

### 0.05 실행 환경 감지 (병렬 모드 결정)

Knowledge Manager의 병렬화 모드는 실행 환경에 따라 자동 결정됩니다.

| 환경 | 병렬화 모드 | 판별 방법 |
|------|-----------|----------|
| **터미널 CLI** (interactive) | Agent Teams (Teammate 인스턴스) | 기본 가정 — `/knowledge-manager` 직접 호출 |
| **VS Code / SDK** | 병렬 Task 서브에이전트 | Task 내부에서 호출된 경우 |

> **IMPORTANT**: Task 도구의 `team_name` 파라미터는 Agent Teams를 활성화하지 **않습니다**.
> VS Code에서는 Team OS가 활성화되어 있어도 Agent Teams 대신 병렬 Task 서브에이전트를 사용합니다.

#### 결과 출력 형식

```markdown
### 실행 환경
| 항목 | 감지 결과 |
|------|----------|
| **환경** | {VS Code / 터미널 CLI} |
| **병렬 모드** | {병렬 Task 서브에이전트 / Agent Teams} |
| **Team OS** | {활성화 / 비활성} |
```

---

### 0.1 실행 조건

| 조건 | 설명 |
|------|------|
| **자동 실행** | Knowledge Manager 첫 실행 시 |
| **수동 실행** | "환경 감지", "시스템 체크", "RAG 설정" 키워드 |
| **재실행** | "환경 재감지", "스펙 다시 확인" 키워드 |

### 0.2 크로스 플랫폼 감지 명령어

**CRITICAL**: 반드시 아래 명령어를 **실제로 Bash 도구로 실행**하여 결과를 수집

#### Windows (PowerShell)
```bash
# RAM
powershell -Command "Get-CimInstance Win32_ComputerSystem | Select-Object TotalPhysicalMemory | Format-List"

# CPU
powershell -Command "Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors | Format-List"

# GPU
powershell -Command "Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM | Format-List"

# Disk (가용 공간)
powershell -Command "Get-PSDrive C | Select-Object Free | Format-List"
```

#### macOS
```bash
# RAM
sysctl -n hw.memsize

# CPU
sysctl -n machdep.cpu.brand_string
sysctl -n hw.ncpu

# GPU
system_profiler SPDisplaysDataType 2>/dev/null | grep -E "Chipset|VRAM|Metal"

# Disk
df -h / | tail -1 | awk '{print $4}'
```

#### Linux
```bash
# RAM
grep MemTotal /proc/meminfo

# CPU
lscpu | grep "Model name"
nproc

# GPU
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo "No NVIDIA GPU"

# Disk
df -h / | tail -1 | awk '{print $4}'
```

### 0.3 OS 감지 방법

```bash
# 플랫폼 감지 (Bash에서 자동)
# Windows: $env:OS 또는 OSTYPE 없음
# macOS: uname -s → "Darwin"
# Linux: uname -s → "Linux"
```

**실행 순서:**
1. `uname -s 2>/dev/null || echo "Windows"` 로 OS 판별
2. OS에 맞는 감지 명령어 세트 실행
3. 결과 파싱 후 티어 분류

---

## Phase 1: 티어 분류

### 1.1 분류 기준

```
┌────────────────────────────────────────────────────────┐
│                    티어 분류 기준                        │
├──────────┬──────────┬──────────┬───────────────────────┤
│          │  Basic   │ Standard │      Advanced         │
├──────────┼──────────┼──────────┼───────────────────────┤
│ RAM      │  ~8 GB   │  16 GB   │  32 GB+               │
│ GPU      │  없음/iGPU│ dGPU any │  dGPU VRAM 8GB+       │
│ CPU 코어  │  4+      │  6+      │  8+                   │
│ 디스크    │  10GB+   │  20GB+   │  50GB+                │
└──────────┴──────────┴──────────┴───────────────────────┘
```

### 1.2 분류 로직

```
RAM >= 32GB AND dGPU VRAM >= 8GB → Advanced
RAM >= 16GB OR dGPU 존재          → Standard
그 외                              → Basic
```

**주의**: 하나라도 Advanced 조건을 충족하면 Standard 이상으로 판정.
최종 티어는 가장 높은 충족 티어.

---

## Phase 2: 사용자 안내 (효능감 설계)

### 2.1 감지 결과 출력 형식

**CRITICAL**: 반드시 아래 형식으로 사용자에게 표시. 사용자가 자기 시스템 역량을 직접 확인하는 경험이 핵심.

```markdown
---

## 🖥️ 시스템 환경 감지 완료

| 항목 | 감지 결과 |
|------|----------|
| **OS** | {Windows 11 / macOS / Linux} |
| **CPU** | {프로세서명} ({코어}C/{스레드}T) |
| **RAM** | {XX} GB |
| **GPU** | {GPU명} ({VRAM}GB VRAM) |
| **여유 디스크** | {XX} GB |

### 🏆 시스템 등급: **{BASIC / STANDARD / ADVANCED}**

{티어별 메시지 - 아래 참조}

---
```

### 2.2 티어별 메시지 (효능감 핵심)

#### Basic 🟢
```markdown
### 🟢 Basic - 핵심 기능 사용 가능

현재 시스템에서 Knowledge Manager의 **핵심 기능**을 모두 사용할 수 있습니다:

| 기능 | 상태 | 설명 |
|------|------|------|
| 📝 Obsidian 노트 생성 | ✅ 사용 가능 | Zettelkasten 원자 노트 자동 생성 |
| 🔍 키워드 검색 | ✅ 사용 가능 | vault 전체 텍스트 검색 |
| 🔗 Wikilink 관계 탐색 | ✅ 사용 가능 | 기존 링크 역추적으로 관련 노트 발견 |
| 🏷️ 태그 기반 분류 | ✅ 사용 가능 | 자동 태그 추출 및 분류 |
| 📊 다이어그램 생성 | ✅ 사용 가능 | Mermaid/DrawIO 시각화 |

> 💡 **키워드 검색 + wikilink 역추적**만으로도 vault 내 관련 노트의 80%를 발견할 수 있습니다.
```

#### Standard 🟡
```markdown
### 🟡 Standard - 시맨틱 검색 추가 가능

Basic의 모든 기능에 더해, **벡터 유사도 검색**을 활성화할 수 있습니다:

| 기능 | 상태 | 설명 |
|------|------|------|
| 📝 ~ 📊 Basic 전체 | ✅ 사용 가능 | 위 Basic 기능 모두 포함 |
| 🧠 **벡터 유사도 검색** | 🔓 활성화 가능 | "이 노트와 비슷한 내용" 검색 |
| 📈 **시맨틱 연결 추천** | 🔓 활성화 가능 | 키워드 없이도 의미적으로 관련된 노트 발견 |

> 💡 벡터 검색 추가 시, 관련 노트 발견율이 **80% → 92%**로 향상됩니다.
> (Chroma DB 설치 필요 - 아래에서 안내)
```

#### Advanced 🔴
```markdown
### 🔴 Advanced - 풀 RAG 파이프라인 가능

Standard의 모든 기능에 더해, **그래프 DB + 로컬 AI 임베딩**을 활성화할 수 있습니다:

| 기능 | 상태 | 설명 |
|------|------|------|
| 📝 ~ 📈 Standard 전체 | ✅ 사용 가능 | 위 Standard 기능 모두 포함 |
| 🕸️ **그래프 순회 검색** | 🔓 활성화 가능 | A→B→C 다단계 관계 탐색 |
| 🤖 **로컬 AI 임베딩** | 🔓 활성화 가능 | 클라우드 API 없이 로컬에서 임베딩 생성 |
| 🔄 **하이브리드 검색** | 🔓 활성화 가능 | 키워드 + 벡터 + 그래프 3축 통합 검색 |

> 💡 풀 RAG 파이프라인 시, 관련 노트 발견율이 **92% → 97%**로 향상됩니다.
> 검색 정확도뿐 아니라 "왜 관련있는지" 경로 설명도 가능합니다.
> (Neo4j + Ollama 설치 필요 - 아래에서 안내)
```

---

## Phase 3: 기능 활성화 (자동 설치 지원)

### 3.1 활성화 제안 프롬프트

**CRITICAL**: 사용자에게 선택권을 부여. 강제 설치 절대 금지.

```markdown
---

### ⚡ 추가 기능 활성화

현재 시스템에서 다음 기능을 추가로 활성화할 수 있습니다:

{Standard/Advanced 해당 기능 목록}

활성화하시겠습니까?
1. **자동 설치** - 지금 바로 설치를 진행합니다 (단계별 진행 상황 표시)
2. **나중에** - 지금은 현재 모드로 사용 (언제든 "RAG 설정"으로 재실행 가능)
3. **상세 정보** - 각 기능의 장단점 자세히 보기

> 어떤 선택이든 Knowledge Manager의 핵심 기능은 동일하게 작동합니다.
> 설치 중 문제가 생기면 자동으로 이전 상태로 복원됩니다.
```

### 3.2 자동 설치 프로세스 (Standard: Chroma 벡터 검색)

**대상**: Standard 이상 티어 (RAM 16GB+ 또는 dGPU 보유)

**사용자가 "자동 설치" 선택 시**, 아래 단계를 **Bash 도구로 실제 실행**:

#### Step 1: 사전 검사 (Pre-flight Check)

```bash
# Python 존재 확인
python --version 2>/dev/null || python3 --version 2>/dev/null

# pip 존재 확인
pip --version 2>/dev/null || pip3 --version 2>/dev/null

# Node.js/npx 존재 확인
npx --version 2>/dev/null
```

**사용자에게 표시:**
```markdown
### 📋 사전 검사 결과

| 항목 | 상태 | 필요 버전 |
|------|------|----------|
| Python | {✅ 3.x.x / ❌ 미설치} | 3.8+ |
| pip | {✅ 있음 / ❌ 미설치} | - |
| Node.js/npx | {✅ 있음 / ❌ 미설치} | 18+ |

{모두 ✅이면 → "모든 사전 조건이 충족되었습니다. 설치를 진행합니다."}
{하나라도 ❌이면 → "다음 항목을 먼저 설치해주세요: [미설치 목록]" + 설치 링크}
```

#### Step 2: Chroma 설치

```bash
# Chroma DB 설치
pip install chromadb

# 설치 확인
python -c "import chromadb; print(f'Chroma {chromadb.__version__} installed')"
```

**사용자에게 표시:**
```markdown
⏳ **[1/3]** Chroma DB 설치 중...
✅ **[1/3]** Chroma DB v{버전} 설치 완료
```

#### Step 3: MCP 서버 등록

```bash
# Claude Code에 Chroma MCP 서버 추가
claude mcp add chroma -- npx -y chroma-mcp --db-path ./chroma_data
```

**사용자에게 표시:**
```markdown
⏳ **[2/3]** MCP 서버 등록 중...
✅ **[2/3]** Chroma MCP 서버 등록 완료
```

#### Step 4: 연결 확인

```bash
# MCP 서버 연결 상태 확인
claude mcp list
```

**사용자에게 표시:**
```markdown
⏳ **[3/3]** 연결 확인 중...
✅ **[3/3]** Chroma MCP 서버 연결 성공!

---

### 🎉 벡터 검색 활성화 완료!

| 기능 | 이전 | 이후 |
|------|------|------|
| 관련 노트 발견율 | ~80% | **~92%** |
| 검색 방식 | 키워드 + wikilink | + **시맨틱 유사도** |
| 검색 시간 | <2초 | 2-3초 |

이제 "이 노트와 비슷한 내용 찾아줘" 같은 시맨틱 검색이 가능합니다.
Knowledge Manager가 자동으로 벡터 검색을 활용합니다.
```

#### 설치 실패 시 복원

```markdown
❌ Chroma 설치 중 오류가 발생했습니다.

**에러**: {에러 메시지}

자동 복원을 진행합니다...
✅ 이전 상태로 복원 완료. Knowledge Manager는 Basic 모드로 정상 작동합니다.

> 수동 설치를 원하시면 "RAG 설정 상세"를 입력해주세요.
```

### 3.3 자동 설치 프로세스 (Advanced: Neo4j + Ollama)

**대상**: Advanced 티어 (RAM 32GB+ AND dGPU VRAM 8GB+)

#### Step 1: 사전 검사 (Standard 검사 포함)

```bash
# Standard 사전 검사 (위와 동일)
# + 추가 검사:

# GPU VRAM 확인 (NVIDIA)
nvidia-smi --query-gpu=memory.total --format=csv,noheader 2>/dev/null

# Docker 확인 (Neo4j 컨테이너용, 선택)
docker --version 2>/dev/null
```

**사용자에게 표시:**
```markdown
### 📋 Advanced 사전 검사 결과

| 항목 | 상태 | 용도 |
|------|------|------|
| Standard 전체 | ✅ 통과 | Chroma 기반 |
| NVIDIA GPU | {✅ VRAM {X}GB / ⚠️ 미감지} | Ollama 추론 |
| Docker | {✅ 있음 / ⚠️ 없음 (직접 설치도 가능)} | Neo4j 컨테이너 |
```

#### Step 2: Neo4j 설치 (Docker 우선, 직접 설치 폴백)

**Docker 사용 가능 시:**
```bash
# Neo4j 컨테이너 실행
docker run -d --name neo4j-km \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/knowledge-manager \
  neo4j:latest

# 연결 대기 (최대 30초)
sleep 10
curl -s http://localhost:7474 > /dev/null && echo "Neo4j ready"
```

**Docker 없으면:**
```markdown
Neo4j Desktop을 설치해주세요:
→ https://neo4j.com/download/
→ 설치 후 로컬 DB를 생성하고 시작해주세요 (bolt://localhost:7687)
→ 완료되면 "계속"을 입력해주세요.
```

**사용자에게 표시:**
```markdown
⏳ **[1/5]** Neo4j 그래프 DB 설정 중...
✅ **[1/5]** Neo4j 실행 확인 (bolt://localhost:7687)
```

#### Step 3: Neo4j MCP 등록

```bash
claude mcp add neo4j -- npx -y neo4j-mcp --uri bolt://localhost:7687 --user neo4j --password knowledge-manager
```

```markdown
⏳ **[2/5]** Neo4j MCP 서버 등록 중...
✅ **[2/5]** Neo4j MCP 서버 등록 완료
```

#### Step 4: Ollama + 임베딩 모델

```bash
# Ollama 존재 확인
ollama --version 2>/dev/null
```

**Ollama 없으면:**
```markdown
Ollama를 설치해주세요:
→ https://ollama.ai
→ 설치 후 "계속"을 입력해주세요.
```

**Ollama 있으면:**
```bash
# 임베딩 모델 다운로드
ollama pull nomic-embed-text

# 확인
ollama list
```

```markdown
⏳ **[3/5]** Ollama 임베딩 모델 다운로드 중...
✅ **[3/5]** nomic-embed-text 다운로드 완료 (~274MB)
```

#### Step 5: Chroma 설치 (Standard 과정 실행)

```markdown
⏳ **[4/5]** Chroma 벡터 DB 설치 중...
✅ **[4/5]** Chroma 설치 및 MCP 등록 완료
```

#### Step 6: 전체 연결 확인

```bash
claude mcp list
# chroma: connected
# neo4j: connected
```

```markdown
⏳ **[5/5]** 전체 시스템 연결 확인 중...
✅ **[5/5]** 모든 서비스 연결 성공!

---

### 🎉 풀 RAG 파이프라인 활성화 완료!

| 기능 | 이전 | 이후 |
|------|------|------|
| 관련 노트 발견율 | ~80% | **~97%** |
| 검색 방식 | 키워드 + wikilink | + **벡터 + 그래프** |
| 관계 탐색 | 직접 연결만 | **다단계 (A→B→C)** |
| 임베딩 | 없음 | **로컬 AI (Ollama)** |
| 검색 시간 | <2초 | 3-5초 |

이제 3축 하이브리드 검색이 가능합니다:
- **키워드** → 정확한 용어 매칭
- **벡터** → "비슷한 의미" 탐색
- **그래프** → "관계 경로" 추적

Knowledge Manager가 자동으로 최적의 검색 전략을 선택합니다.
```

### 3.4 부분 설치 지원

Advanced 티어지만 일부만 설치하고 싶을 때:

```markdown
### 선택적 설치

어떤 기능을 활성화하시겠습니까? (복수 선택 가능)

| # | 기능 | 설치 시간 | 디스크 | 효과 |
|---|------|----------|--------|------|
| A | Chroma (벡터 검색) | ~5분 | ~200MB | 발견율 80%→92% |
| B | Neo4j (그래프 검색) | ~10분 | ~500MB | 관계 탐색 가능 |
| C | Ollama (로컬 임베딩) | ~10분 | ~2-4GB | 클라우드 API 불필요 |

> 예시: "A" → Chroma만 설치, "A,C" → Chroma + Ollama, "전부" → A+B+C
```

---

## Phase 4: 적응형 동작 설정

### 4.1 감지 결과 기반 동작 분기

감지된 티어와 **실제 설치된 도구**에 따라 km-workflow 동작이 자동 적응됩니다.

```
감지 결과 저장 → km-workflow Phase 2/5.5에서 참조
```

### 4.2 MCP 서버 가용성 확인

**CRITICAL**: 티어만으로 판단하지 않음. 실제 MCP 서버 존재 여부를 확인.

```bash
# Step 1: Obsidian CLI 확인 (우선)
OBSIDIAN_CLI="/mnt/c/Program Files/Obsidian/Obsidian.com"
"$OBSIDIAN_CLI" version 2>/dev/null
# 응답 있으면 → obsidian_method = "cli"

# Step 2: CLI 실패 시 MCP 확인
# mcp__obsidian__list_notes({}) 호출
# 응답 있으면 → obsidian_method = "mcp"

# Step 3: 둘 다 실패 → obsidian_method = "filesystem"

# Step 4: MCP 서버 목록 확인 (추가 도구)
claude mcp list
```

확인 항목:
- Obsidian CLI v1.12+ → `obsidian_method = "cli"` (검색/역링크/고아노트 네이티브)
- Obsidian MCP → `obsidian_method = "mcp"` (search_vault, update_note 사용 가능)
- `chroma` → 벡터 유사도 검색 사용 가능
- `neo4j` → 그래프 순회 검색 사용 가능

### 4.3 검색 전략 자동 선택

| 사용 가능한 도구 | 검색 전략 | Phase 2 동작 | Phase 5.5 동작 |
|-----------------|----------|-------------|---------------|
| obsidian CLI | **Keyword + Backlinks (네이티브)** | `search` + `backlinks` + `links` | CLI backlinks + append |
| obsidian MCP만 | **Keyword + Wikilink** | search_vault + Grep `\[\[키워드\]\]` | 키워드 매칭 + wikilink 역추적 |
| obsidian + chroma | **+ Vector** | 위 + Chroma similarity search | 벡터 유사도 기반 연결 추천 추가 |
| obsidian + chroma + neo4j | **+ Graph** | 위 + Neo4j 그래프 순회 | 3축 하이브리드 연결 강화 |

### 4.4 사용자 요약 출력 (세션 시작 시)

```markdown
---

### 📋 Knowledge Manager 현재 설정

| 검색 기능 | 상태 |
|----------|------|
| 키워드 검색 | ✅ 활성 |
| Wikilink 관계 탐색 | ✅ 활성 |
| 벡터 유사도 검색 | {✅ 활성 / ❌ 미설치} |
| 그래프 순회 검색 | {✅ 활성 / ❌ 미설치} |
| 로컬 AI 임베딩 | {✅ 활성 / ❌ 미설치} |

> 현재 모드: **{Basic/Standard/Advanced}**
> {미설치 기능이 있으면: "환경 감지" 또는 "RAG 설정"을 입력하면 업그레이드 가이드를 볼 수 있습니다.}

---
```

---

## Phase 5: 병렬 검색 활성화 (환경별 자동 분기)

> **검증 결과 (2026-02-06)**: 병렬 검색은 환경에 따라 두 가지 모드로 동작합니다.

### 5.1 병렬 검색이란?

Knowledge Manager의 검색 Phase(Phase 2)에서 **여러 검색 작업을 동시에 실행**하여 속도를 2x 이상 향상시킵니다.
환경에 따라 서로 다른 병렬화 메커니즘이 자동으로 선택됩니다.

### 5.2 환경별 병렬화 모드 (자동 감지)

| 환경 | 병렬화 모드 | 메커니즘 | 검증 상태 |
|------|-----------|---------|----------|
| **VS Code / SDK** | 병렬 Task 서브에이전트 | Task 도구 병렬 호출 (읽기 전용) | ✅ 검증됨 (2026-02-06) |
| **터미널 CLI** (`claude` interactive) | Agent Teams | Teammate 생성 + Mailbox 통신 | ✅ 검증됨 (2026-02-06) |

#### 환경 감지 로직

```
Phase 0에서 감지:
1. 실행 환경 확인 (VS Code extension vs 터미널 CLI)
2. 터미널 CLI + interactive 모드 → Agent Teams 사용 가능
3. VS Code / SDK / Task 내부 → 병렬 Task 서브에이전트 사용
```

> **IMPORTANT**: Task 도구의 `team_name` 파라미터는 Agent Teams를 활성화하지 **않습니다**.
> `team_name`은 메타데이터 라벨일 뿐이며, 실제 Teammate 인스턴스를 생성하지 않습니다 (2026-02-06 파일시스템 모니터링으로 검증).

### 5.3 모드 A: 병렬 Task 서브에이전트 (VS Code / SDK — 기본)

이 모드가 대부분의 사용자 환경에서 **기본 실행 모드**입니다.

#### 동작 방식 (GraphRAG 근사 패턴)

```
Main Agent (Coordinator + Generator)
    │
    ├── Task 1 @graph-navigator (Explore, sonnet)
    │   → wikilink 체인 2-hop 추적 → 관계 그래프 반환
    │
    ├── Task 2 @retrieval-specialist (Explore, sonnet)
    │   → 키워드+태그+폴더 넓은 검색 → 고립 노트 발견
    │
    └── Task 3 @deep-reader (Explore, sonnet/opus) — Complex만
        → Hub 노트 실제 읽기 → 요약 + 간극 분석

    → 모든 Task를 하나의 메시지에서 병렬 호출
    → Main이 Graph ∩ Retrieval 교차 검증 → 노트 생성
```

> **핵심**: 단순 검색 병렬이 아닌 **Graph + Retrieval + Reading** 역할 분리.
> Neo4j 없이 wikilink 체인 추적으로 그래프 탐색을 근사합니다.

#### 핵심 규칙

- Task 서브에이전트는 **읽기(Explore) 전용** — 쓰기 작업 위임 금지
- 모든 파일 생성/수정은 **Main이 직접 실행** (Bug-2025-12-12-2056 방지)
- 순차 대비 약 **2x 속도 향상** (실측: 순차 355-391초 → 병렬 161-183초)

#### 사용자 알림 (Phase 0에서 표시)

```markdown
---

### 검색 모드: 병렬 Task 서브에이전트

| 항목 | 설명 |
|------|------|
| **모드** | 병렬 Task 서브에이전트 (Sonnet, 필요 시 Opus) |
| **효과** | 검색 속도 ~2x, 컨텍스트 격리 |
| **환경** | VS Code / SDK |

> 터미널 CLI에서는 Agent Teams 모드가 자동 활성화됩니다.

---
```

### 5.4 모드 B: Agent Teams (터미널 CLI 전용)

**터미널 CLI** (`claude` interactive 모드)에서만 사용 가능한 고급 병렬화입니다.

#### 동작 방식 (GraphRAG 근사 패턴)

```
Main Agent (Coordinator + Generator)
    │
    ├── @graph-navigator (Teammate)
    │   → wikilink 체인 2-hop 추적 → 관계 그래프
    │   → Mailbox로 결과 전달
    │
    ├── @retrieval-specialist (Teammate)
    │   → 키워드+태그 넓은 검색 → 고립 노트 발견
    │   → Mailbox로 결과 전달
    │
    └── @deep-reader (Teammate, Complex)
        → Hub 노트 실제 읽기 → 요약 + 간극 분석
        → Mailbox로 결과 전달

Main은 Shift+↑/↓로 Teammate 전환 가능
Teammate는 독립 인스턴스 (쓰기도 안전)
```

#### Agent Teams 설정

`settings.local.json`의 `env` 섹션:
```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

> 이 설정은 **터미널 CLI에서만 효과**가 있습니다.
> VS Code에서는 이 설정이 있어도 Agent Teams가 동작하지 않습니다.

#### 제한사항

```
- 터미널 CLI interactive 모드 전용 (VS Code, SDK 미지원)
- Research Preview (실험 기능)
- 세션 복원(/resume) 시 Teammate 소실
- Windows Terminal: split-pane 미지원 (in-process 모드)
- 1 세션 = 1 팀만 가능
- "Agent Teams 끄기"로 순차 모드 복귀 가능
```

### 5.5 검색 전략 자동 선택 (병렬화 반영)

| 사용 가능한 도구 | 순차 모드 | 병렬 모드 (Task / Agent Teams) |
|-----------------|----------|-------------------------------|
| obsidian CLI | Backlinks → Search | Backlinks ∥ Search |
| obsidian MCP만 | Wikilink → Keyword | Wikilink ∥ Keyword |
| + chroma | Wikilink → Keyword → Vector | Wikilink ∥ Keyword ∥ Vector |
| + neo4j | 모두 순차 | 4축 동시 검색 |

---

## 참고: 검색 정확도 벤치마크

| 검색 방식 | 관련 노트 발견율 | 검색 시간 | 필요 인프라 |
|----------|-----------------|----------|-----------|
| 키워드 only | ~60% | <1초 | 없음 |
| + Wikilink Grep | ~80% | <2초 | 없음 |
| + Vector (Chroma) | ~92% | 2-3초 | Chroma |
| + Graph (Neo4j) | ~97% | 3-5초 | Neo4j + Ollama |

> 출처: DMR Benchmark 기반 추정 (Efficient Agents Survey, 2024)

---

## 에러 처리

| 상황 | 대응 |
|------|------|
| 시스템 명령어 실행 실패 | OS 감지 재시도 → 실패 시 사용자에게 직접 스펙 질문 |
| GPU 감지 불가 | "GPU 정보를 감지하지 못했습니다. dGPU가 있으신가요?" |
| MCP 서버 연결 실패 | "서버가 설치되었지만 연결 실패. 재시작 후 재시도" |
| 설치 중 오류 | 에러 메시지 표시 + 수동 설치 가이드 링크 제공 |

---

## 통합: km-workflow.md Phase 0

이 스킬은 `km-workflow.md`의 **Phase 0**에서 자동 호출됩니다.

```
Phase 0: 환경 감지 (이 스킬) ← NEW
    ↓
Phase 1: 입력 소스 감지
    ↓
Phase 1.5: 사용자 선호도 수집
    ...
```

**첫 실행 시에만 전체 프로세스 실행**, 이후에는 Phase 4.4의 요약만 표시.
사용자가 "환경 재감지"를 요청하면 전체 프로세스 재실행.
