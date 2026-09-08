# Knowledge Manager

> 📖 **[English documentation is available at the bottom of this page.](#-english-documentation)**

읽은 글·영상·PDF를 **Obsidian 노트로 정리해 주고, 나중에 그 노트를 찾아 주는** Claude Code 플러그인이에요. 링크 하나를 건네면 요약·태그·관련 노트 연결까지 마친 노트가 vault(볼트 — Obsidian 이 노트를 모아 두는 폴더)에 저장되고, 궁금할 땐 `/km:search` 한 줄로 되찾습니다.

## 설치

Claude Code 안에서 아래 세 줄을 순서대로 치면 끝이에요.

```
/plugin marketplace add treylom/knowledge-manager
/plugin install km@knowledge-manager
/km:setup
```

세 번째 줄 `/km:setup` 이 vault 경로·도구 설치·「당신은 어떤 사람인가」 인터뷰를 차례로 물어봐요. **vault 경로를 모르면**: Obsidian 앱 → 좌측 하단 ⚙️(설정) → 「파일 및 링크」 → 상단 「Vault 경로」를 복사하세요. Windows 는 역슬래시(`\`) 대신 슬래시(`/`)로 적습니다(`C:/Users/...`).

> 플러그인 없이 저장소를 클론해 쓰는 방법(`bash scripts/install-to-project.sh /your/project`)도 있어요. 그 경우 명령 이름에서 `km:` 접두어를 빼고 칩니다(예: `/knowledge-manager`).

## 명령어 한눈에 보기

| 명령 | 이걸 치면 이렇게 돼요 | 예시 |
|---|---|---|
| `/km:search` | vault 에서 질문에 맞는 노트를 찾아 답과 출처를 보여줘요 | `/km:search MCP란?` |
| `/km:knowledge-manager` | 링크·PDF·영상을 노트로 만들어 vault 에 저장해요 | `/km:knowledge-manager https://example.com/article` |
| `/km:setup` (= `/km:knowledge-manager-setup`) | 처음 한 번, vault 경로·도구·프로필을 설정해요 | `/km:setup` |
| `/km:interview` | 「내 vault 를 어떻게 짜야 하나」 상담 → 설계 문서 1장 | `/km:interview` |
| `/km:reform` | 폴더 이동·프론트매터·링크를 한꺼번에 손봐요(계획서 먼저) | `/km:reform plan` |
| `/km:pdf` | 너무 큰 PDF·한글 경로 PDF 를 Markdown 으로 바꿔요 | `/km:pdf "보고서.pdf" --page_range "0-19"` |
| `/km:tofugraph` | 검색 엔진(GraphRAG)을 설치·점검·수리해요 | `/km:tofugraph` |
| `/km:km-update` | 플러그인을 최신으로 받고 vault 설정을 다시 입혀요 | `/km:km-update` |
| `/km:knowledge-manager-at` | 위 정리 작업을 에이전트 9명이 나눠서 해요(tmux 필요) | `/km:knowledge-manager-at https://youtube.com/watch?v=XXX` |

## `/km:search` — vault 검색

**언제 쓰나**: 「그거 어디 적어 뒀더라」 싶을 때. 노트 이름을 몰라도 질문으로 찾아요.

**치는 법**
```
/km:search MCP란?
/km:search --deep 프롬프트 엔지니어링 기법 비교
/km:search --quick 옵시디언 단축키
```
플래그가 없으면 질문 모양을 보고 자동으로 고릅니다 — 키워드 1~3개·「~란?」 = QUICK(즉답 3~5줄), 문장형·「비교/방법/차이」 = DEEP(상세 분석 + 연결 맥락). `--no-moc` 을 붙이면 MOC(Map of Content — 목차 노트)를 빼고 낱개 노트만 봅니다. 검색 엔진은 뒤에서 자동으로 골라요: GraphRAG 서버(있으면) → Obsidian CLI → Obsidian MCP → 텍스트 검색 순으로, 앞 단계가 없으면 다음으로 넘어갑니다.

**결과는 어디에**: 채팅 답변에만 나와요. 이 명령은 **읽기 전용**이라 노트를 만들거나 고치지 않습니다. 답변 마지막 줄 `검색: <티어명> …` 이 어느 엔진으로 찾았는지 알려줘요.

**자주 하는 실수**: 질문 없이 `/km:search` 만 치면 사용법만 나와요. 「vault 에서 찾지 못했습니다」가 뜨면 그 자료가 아직 없다는 뜻 — `/km:knowledge-manager` 로 먼저 넣으세요.

## `/km:knowledge-manager` — 자료를 노트로 정리

**언제 쓰나**: 읽을 만한 링크·PDF·영상을 만났을 때. 요약하고, 태그 달고, 관련 노트와 연결한 노트를 만들어 줘요.

**치는 법**
```
/km:knowledge-manager https://example.com/article
/km:knowledge-manager /path/to/document.pdf
/km:knowledge-manager https://threads.net/@user/post/123
/km:knowledge-manager https://youtube.com/watch?v=XXX
```
받는 입력: 일반 웹 URL · YouTube · Threads/Instagram 포스트 · PDF · Word·Excel·PowerPoint 문서 · Notion 페이지 · 「vault 에 있는 것 종합해줘」. 처음엔 상세 수준·연결 강도 등을 물어보지만, `/km:setup` 인터뷰에서 만든 프로필(`_meta/USER-PROFILE.md`)이 있으면 그 값을 기본으로 잡고 확인만 받아요. 저장 전에 **품질 점검(중복·모순·누락 자동 검사)** 을 통과해야 하고, 관련 노트 링크가 실제로 들어갔는지도 검사합니다.

**결과는 어디에**: vault 안. 내가 쓴 글(원저자 = 본인)은 `Mine/` 아래, 남의 자료는 `Library/` 아래(예: 웹·YouTube 정리 → `Library/Zettelkasten/<주제>/`, 논문 → `Library/Papers/`). 끝나면 「처리 결과 보고」에 노트별 경로가 표로 나오고, 세션 기록이 `_km-log.md` 에 한 줄 남아요.

**자주 하는 실수**: 큰 PDF 를 바로 넣으면 「Prompt is too long」이 떠요. 그땐 `/km:pdf` 로 페이지를 나눠 변환한 뒤 넣으세요.

## `/km:setup` — 처음 설정 (= `/km:knowledge-manager-setup`)

**언제 쓰나**: 설치 직후 한 번. vault 경로를 바꾸고 싶을 때 다시 한 번. 두 이름은 같은 명령이에요(`setup` 이 짧은 별칭).

**치는 법**
```
/km:setup
```
순서대로 물어봐요: ① Obsidian 을 쓰는지 → ② vault 경로(안 쓰면 로컬 폴더 지정) → ③ 도구 설치(Playwright 는 필수, Obsidian·Notion 연결은 선택) → ④ **프로필 인터뷰** 6가지(무슨 일을 어떻게 하는지 — 옵션 클릭이 아니라 대화로) → ⑤ 설정 파일 `km-config.json` 생성 → ⑥ vault 현관 문서 3종(`000-START-HERE/` 의 START-HERE · VAULT-STRUCTURE · MOC-Map) 생성.

**결과는 어디에**: 프로젝트 폴더에 `km-config.json`, vault 안에 `_meta/USER-PROFILE.md` 와 `000-START-HERE/` 문서 3개.

**자주 하는 실수**: Windows 경로를 역슬래시로 적기. `C:\Users\...` 가 아니라 `C:/Users/...` 예요.

## `/km:interview` — 지식관리 설계 상담

**언제 쓰나**: 「폴더를 어떻게 나누지, MOC 는 뭘로 잡지」가 막막할 때. 15분 안에 대화로 설계안을 뽑아요.

**치는 법**
```
/km:interview
```
앵커 질문 5개를 하나씩 던지고 답마다 한 번 더 되물어요(옵션 클릭 없음). 중간에 끊겨도 그때까지 답을 `completeness: partial` 로 저장해 둡니다.

**결과는 어디에**: vault 의 `_meta/KM-DESIGN.md` **한 파일뿐**. 이미 있으면 `.bak-<시각>` 으로 백업하고 새로 써요.

**자주 하는 실수**: 이 명령이 노트나 폴더를 옮겨 줄 거라 기대하기. 옮기는 건 하지 않아요 — 설계안 §G 를 실제로 적용하려면 다음 절 `/km:reform plan` 을 치세요.

## `/km:reform` — 대량 변형 (계획서 먼저, 적용은 따로)

**언제 쓰나**: 노트 수백 개의 폴더·프론트매터(frontmatter — 노트 맨 위 메타데이터)·링크를 한꺼번에 손봐야 할 때.

**치는 법**
```
/km:reform plan
/km:reform apply _meta/REFORM-PLAN-<시각>.md
/km:reform check
```
`plan`(인자 없이 쳐도 같음)은 **계획서만** 만들고 노트는 건드리지 않아요. `move`·`frontmatter`·`links` 는 그 유형만 담는 plan 단축이에요. `apply` 는 계획서 파일을 인자로 받고, 실행 전에 git 스냅샷(`km-reform-pre-<시각>` 태그, 미커밋 변경이 있으면 stash)을 자동으로 남깁니다. `check` 는 링크가 깨지지 않았는지 보는 게이트예요.

**결과는 어디에**: `_meta/REFORM-PLAN-<시각>.md`(계획서) · `_meta/REFORM-REPORT-<시각>.md`(적용 결과). 되돌리기는 `git -C <vault> reset --hard km-reform-pre-<시각>`.

**자주 하는 실수**: vault 가 git 저장소가 아니면 `apply` 가 멈춰요(스냅샷 없이는 진행 안 함). 먼저 `git -C <vault> init` 을 하세요.

## `/km:pdf` — 큰 PDF 를 Markdown 으로

**언제 쓰나**: PDF 를 넣었더니 「Prompt is too long」이 뜰 때, 파일 경로에 한글이 있어 읽기가 실패할 때, 텍스트 추출이 안 될 때.

**치는 법**
```
/km:pdf "파일.pdf"
/km:pdf "파일.pdf" --page_range "0-19"
```
뒤에서 `marker_single`(PDF → Markdown 변환기)이 돌아요. 너무 크면 페이지 범위를 물어보니 `--page_range "시작-끝"` 으로 잘라서 다시 치면 됩니다(첫 페이지가 0).

**결과는 어디에**: 현재 폴더의 `./km-temp/<파일명>/<파일명>.md`. 이걸 `/km:knowledge-manager` 에 넣으면 노트가 돼요.

**자주 하는 실수**: 페이지 범위를 도구가 알아서 정해 주길 기다리기 — 일부러 안 정해요. 범위는 사용자가 직접 씁니다.

## `/km:tofugraph` — 검색 엔진(GraphRAG) 운영

**언제 쓰나**: `/km:search` 를 더 똑똑하게 만들고 싶을 때. GraphRAG(노트 사이 연결까지 보는 검색 서버)를 설치·점검·수리해요. 없어도 `/km:search` 는 다음 단계 엔진으로 동작합니다.

**치는 법**
```
/km:tofugraph
/km:tofugraph build
/km:tofugraph search <질문>
/km:tofugraph status
/km:tofugraph heal
/km:tofugraph auto
```
인자 없이 치면 `doctor`(진단 + 처방) — 처음이면 여기부터. `build` 는 인덱스 구축(엔진이 없으면 설치 명령을 보여주고 실행 여부를 물어요), `heal` 은 1회 수리, `auto` 는 1시간마다 감시·자가치유하는 데몬을 켭니다. `guard-set` 은 노트를 일부러 줄인 뒤 기준선을 다시 잡을 때만.

**결과는 어디에**: 검색 인덱스와 서버 상태. 노트 파일은 건드리지 않아요. 진단 결과는 채팅에 요약돼요([FAIL]/[WARN] 이면 처방 줄이 같이 나옴).

**자주 하는 실수**: 디스크 부족·OS 업데이트 경고까지 이 도구가 고쳐 주길 기대하기. 그런 건 보고만 하고 자동으로 지우지 않아요.

## `/km:km-update` — 플러그인 업데이트

**언제 쓰나**: 저장소를 클론해 쓰는 사용자가 새 버전을 받을 때. vault 경로 설정을 잃지 않고 갱신해요.

**치는 법**
```
/km:km-update
```
뒤에서 `bash scripts/km-update.sh` 가 ① 잠긴 설정 파일 해제 → ② 템플릿 복원 → ③ `git pull` → ④ vault 경로 재적용 → ⑤ 다시 잠금 순으로 돌아요.

**결과는 어디에**: 플러그인 폴더 자체가 최신이 되고, `km-config.json` 의 vault 경로가 스킬 파일에 다시 적용돼요.

**자주 하는 실수**: 플러그인 파일을 손으로 고쳐 둔 채 실행하면 「Uncommitted changes detected」로 멈춰요. 변경을 stash 하거나 커밋한 뒤 다시 치세요. vault 경로를 **바꾸려는** 거면 이 명령이 아니라 `/km:setup` 재실행이에요.

## `/km:knowledge-manager-at` — 에이전트 팀으로 정리

**언제 쓰나**: `/km:knowledge-manager` 와 같은 일을 더 큰 자료·더 많은 교차 검증으로 하고 싶을 때. Category Lead·RALPH·DA 등 9명이 병렬로 나눠 해요.

**치는 법**
```
/km:knowledge-manager-at https://youtube.com/watch?v=XXX
```
입력 유형·질문·저장 규칙은 `/km:knowledge-manager` 와 같아요. 다만 **tmux 와 `.team-os/` 하네스가 있는 프로젝트**에서만 팀이 뜹니다.

**결과는 어디에**: 노트는 `/km:knowledge-manager` 와 같은 자리(`Mine/`·`Library/`). 팀 작업 기록은 프로젝트의 `.team-os/artifacts/TEAM_PLAN.md`·`TEAM_PROGRESS.md`·`TEAM_FINDINGS.md`.

**자주 하는 실수**: tmux 없는 환경에서 치기. 그땐 「Agent Teams 는 tmux 가 필요합니다」 안내가 나오니 `/km:knowledge-manager` 를 쓰세요.

## 저장 방식

Obsidian 을 쓰면 vault 안에, 안 쓰면 `/km:setup` 에서 정한 로컬 폴더(`km-notes/`)에 Obsidian 호환 Markdown 으로 저장돼요. 뼈대는 같아요.

```
Your-Vault/
├── 000-START-HERE/     ← /km:setup 이 만드는 현관 문서 3종
├── _meta/              ← USER-PROFILE · KM-DESIGN · REFORM-PLAN/REPORT
├── Mine/               ← 내가 쓴 글
└── Library/            ← 남의 자료 (Zettelkasten · Papers · Clippings …)
```

## 문제 해결

- **도구 연결 확인**: `claude mcp list` 로 playwright·obsidian 서버가 보이는지 확인. Antigravity 는 Agent 패널 → ⋯ → MCP Servers 에서 Refresh.
- **설정 파일 위치**: 플러그인 설정은 프로젝트의 `km-config.json` 이 기준 파일. MCP 등록은 Claude Code CLI = `~/.claude.json`(user 스코프) · Claude Desktop = `%APPDATA%\Claude\claude_desktop_config.json` · Antigravity = `~/.gemini/antigravity/mcp_config.json`.
- **검색이 자꾸 텍스트 검색으로 떨어질 때**: `/km:tofugraph` 로 진단. GraphRAG 서버 주소는 `km-config.json` 의 `linking.semantic_adapter.endpoint`(기본 `http://127.0.0.1:8400`).
- **링크 가중치·MOC 게이트**: `km-config.json` 의 `linking.scheme`(`"v2"` 기본) · `linking.mocGate`(`"auto"` 기본 / `"confirm"` = 후보 1개 확인). 예시는 `km-config.example.json`.

## 기여 · 라이선스 · 링크

기여는 Fork → 브랜치 → 커밋 → Pull Request. MIT License — 자유롭게 사용·수정·배포하세요.

- [Claude Code](https://code.claude.com) · [Claude Code Plugins](https://claude.com/blog/claude-code-plugins)
- [MCP Protocol](https://modelcontextprotocol.io) · [Obsidian](https://obsidian.md)
- [Antigravity MCP 설정 가이드](https://composio.dev/blog/howto-mcp-antigravity)

---

# 🇺🇸 English Documentation

# Knowledge Manager

A Claude Code plugin that **turns what you read and watch into Obsidian notes, and finds those notes again later.** Hand it a link and you get back a note with a summary, tags, and links to related notes, saved in your vault (the folder where Obsidian keeps your notes). When you need it back, one line — `/km:search` — finds it.

## Install

Type these three lines inside Claude Code, in order.

```
/plugin marketplace add treylom/knowledge-manager
/plugin install km@knowledge-manager
/km:setup
```

The third line, `/km:setup`, walks you through the vault path, tool installation, and a short "how do you work?" interview. **Don't know your vault path?** Open Obsidian → ⚙️ (Settings, bottom left) → "Files and links" → copy the "Vault path" shown at the top. On Windows, write forward slashes (`/`) instead of backslashes (`\`): `C:/Users/...`.

> You can also clone the repository and install without the plugin system (`bash scripts/install-to-project.sh /your/project`). In that case, drop the `km:` prefix from every command name (for example, `/knowledge-manager`).

## Commands at a Glance

| Command | What happens when you type it | Example |
|---|---|---|
| `/km:search` | Finds notes in your vault that answer a question, with sources | `/km:search What is MCP?` |
| `/km:knowledge-manager` | Turns a link, PDF, or video into a note and saves it to your vault | `/km:knowledge-manager https://example.com/article` |
| `/km:setup` (= `/km:knowledge-manager-setup`) | One-time setup: vault path, tools, your profile | `/km:setup` |
| `/km:interview` | A consultation on how to structure your vault → one design document | `/km:interview` |
| `/km:reform` | Bulk changes to folders, frontmatter, and links (plan first) | `/km:reform plan` |
| `/km:pdf` | Converts oversized PDFs (or PDFs with non-ASCII paths) to Markdown | `/km:pdf "report.pdf" --page_range "0-19"` |
| `/km:tofugraph` | Installs, checks, and repairs the GraphRAG search engine | `/km:tofugraph` |
| `/km:km-update` | Pulls the latest plugin version and re-applies your vault settings | `/km:km-update` |
| `/km:knowledge-manager-at` | The same note-making job, split across a team of 9 agents (needs tmux) | `/km:knowledge-manager-at https://youtube.com/watch?v=XXX` |

## `/km:search` — Search Your Vault

**When to use it**: When you think "I wrote that down somewhere." You don't need the note's title — ask a question.

**How to type it**
```
/km:search What is MCP?
/km:search --deep compare prompt engineering techniques
/km:search --quick obsidian shortcuts
```
With no flag, the command picks a mode from the shape of your question: one to three keywords or a "what is X?" question gets QUICK (a direct answer in 3–5 lines); a full sentence or a "compare / how to / difference" question gets DEEP (a structured analysis plus the surrounding link context). Add `--no-moc` to skip MOC notes (Maps of Content — index notes) and search only atomic notes. The search engine is chosen for you: GraphRAG server (if installed) → Obsidian CLI → Obsidian MCP → plain text search, falling through whenever a stage is missing.

**Where the result goes**: Only into the chat reply. This command is **read-only** — it never creates or edits a note. The last line of the reply, `검색: <tier> …`, tells you which engine answered.

**Common mistake**: Typing `/km:search` with no question only prints the usage line. If you see "no related material in the vault", the material isn't there yet — add it first with `/km:knowledge-manager`.

## `/km:knowledge-manager` — Turn Material into Notes

**When to use it**: Whenever you meet a link, PDF, or video worth keeping. It summarizes, tags, links to related notes, and saves.

**How to type it**
```
/km:knowledge-manager https://example.com/article
/km:knowledge-manager /path/to/document.pdf
/km:knowledge-manager https://threads.net/@user/post/123
/km:knowledge-manager https://youtube.com/watch?v=XXX
```
Accepted input: ordinary web URLs · YouTube · Threads/Instagram posts · PDF · Word, Excel, and PowerPoint documents · Notion pages · "synthesize what's already in my vault". The first time, it asks about detail level and how strongly to link; once the `/km:setup` interview has produced a profile (`_meta/USER-PROFILE.md`), those answers become defaults and you only confirm. Before saving, the draft must pass a **quality check** (automatic detection of duplicates, contradictions, and gaps) and a check that links to related notes were actually written in.

**Where the result goes**: Into your vault. Material you authored yourself goes under `Mine/`; everything else under `Library/` (for example, web and YouTube notes → `Library/Zettelkasten/<topic>/`, papers → `Library/Papers/`). When it finishes, a "processing report" lists every note with its path, and one line is appended to `_km-log.md`.

**Common mistake**: Feeding in a large PDF directly, which fails with "Prompt is too long". Convert it in page ranges with `/km:pdf` first, then feed in the Markdown.

## `/km:setup` — First-Time Setup (= `/km:knowledge-manager-setup`)

**When to use it**: Once, right after installing. Again whenever you want to change the vault path. The two names run the same command (`setup` is the short alias).

**How to type it**
```
/km:setup
```
It asks, in order: ① whether you use Obsidian → ② your vault path (or a local folder if you don't) → ③ tool installation (Playwright is required; Obsidian and Notion connections are optional) → ④ a **profile interview** of six questions about how you work (a conversation, not multiple-choice) → ⑤ generation of the config file `km-config.json` → ⑥ three "front door" documents for the vault (`000-START-HERE/`: START-HERE · VAULT-STRUCTURE · MOC-Map).

**Where the result goes**: `km-config.json` in your project folder; `_meta/USER-PROFILE.md` and the three `000-START-HERE/` documents in your vault.

**Common mistake**: Writing a Windows path with backslashes. Use `C:/Users/...`, not `C:\Users\...`.

## `/km:interview` — Vault Design Consultation

**When to use it**: When you're stuck on "how should I split folders, what should my MOCs be?" A 15-minute conversation produces a design.

**How to type it**
```
/km:interview
```
It asks five anchor questions one at a time and follows up once on each answer (no option clicking). If you stop partway, what you've answered so far is saved with `completeness: partial`.

**Where the result goes**: A **single file**, `_meta/KM-DESIGN.md` in your vault. If one already exists, it's backed up as `.bak-<timestamp>` before being rewritten.

**Common mistake**: Expecting this command to move notes or folders. It doesn't — to apply the design's §G, run `/km:reform plan` (next section).

## `/km:reform` — Bulk Changes (Plan First, Apply Separately)

**When to use it**: When hundreds of notes need their folders, frontmatter (the metadata block at the top of a note), or links changed at once.

**How to type it**
```
/km:reform plan
/km:reform apply _meta/REFORM-PLAN-<timestamp>.md
/km:reform check
```
`plan` (also the default with no argument) writes **only a plan** and touches no notes. `move`, `frontmatter`, and `links` are shortcuts for a plan limited to that one kind of change. `apply` takes the plan file as its argument and, before doing anything, saves a git snapshot (a `km-reform-pre-<timestamp>` tag, or a stash if there are uncommitted changes). `check` is the gate that verifies no links were broken.

**Where the result goes**: `_meta/REFORM-PLAN-<timestamp>.md` (the plan) and `_meta/REFORM-REPORT-<timestamp>.md` (what was applied). To roll back: `git -C <vault> reset --hard km-reform-pre-<timestamp>`.

**Common mistake**: Running `apply` on a vault that isn't a git repository — it stops, because it won't proceed without a snapshot. Run `git -C <vault> init` first.

## `/km:pdf` — Large PDFs to Markdown

**When to use it**: When a PDF triggers "Prompt is too long", when a non-ASCII file path makes reading fail, or when text extraction comes back empty.

**How to type it**
```
/km:pdf "file.pdf"
/km:pdf "file.pdf" --page_range "0-19"
```
Under the hood it runs `marker_single` (a PDF-to-Markdown converter). If the file is too large it asks you for a page range — re-run with `--page_range "start-end"` (pages are numbered from 0).

**Where the result goes**: `./km-temp/<filename>/<filename>.md` in the current folder. Feed that file to `/km:knowledge-manager` to turn it into a note.

**Common mistake**: Waiting for the tool to pick a page range for you. It deliberately doesn't — you choose the range.

## `/km:tofugraph` — Run the GraphRAG Search Engine

**When to use it**: When you want `/km:search` to be smarter. GraphRAG is a search server that also follows the links between notes; this command installs, checks, and repairs it. Without it, `/km:search` still works through the next engine in line.

**How to type it**
```
/km:tofugraph
/km:tofugraph build
/km:tofugraph search <question>
/km:tofugraph status
/km:tofugraph heal
/km:tofugraph auto
```
With no argument it runs `doctor` (diagnosis plus a fix for each problem) — start here. `build` constructs the index (if the engine isn't installed, it shows the install command and asks before running it), `heal` is a one-time repair, and `auto` installs a daemon that watches and self-heals every hour. `guard-set` resets the baseline only after you've deliberately removed notes.

**Where the result goes**: The search index and server state. Note files are never touched. Diagnosis is summarized in chat; any [FAIL] or [WARN] item comes with its fix line.

**Common mistake**: Expecting it to fix low-disk or OS-update warnings too. Those are reported only — nothing is deleted automatically.

## `/km:km-update` — Update the Plugin

**When to use it**: When you installed by cloning the repository and want the latest version without losing your vault-path settings.

**How to type it**
```
/km:km-update
```
It runs `bash scripts/km-update.sh`, which ① unlocks the protected config files → ② restores the templates → ③ runs `git pull` → ④ re-applies your vault path → ⑤ locks the files again.

**Where the result goes**: The plugin folder itself is updated, and the vault path from `km-config.json` is re-applied to the skill files.

**Common mistake**: Running it while plugin files you edited by hand are still uncommitted — it stops with "Uncommitted changes detected". Stash or commit first, then re-run. If what you want is to **change** the vault path, re-run `/km:setup` instead.

## `/km:knowledge-manager-at` — Note-Making with an Agent Team

**When to use it**: For the same job as `/km:knowledge-manager` on bigger material, or when you want more cross-checking. Nine agents (Category Lead, RALPH, DA, and others) split the work in parallel.

**How to type it**
```
/km:knowledge-manager-at https://youtube.com/watch?v=XXX
```
Input types, questions, and save rules are identical to `/km:knowledge-manager`. The team only starts in a project that has **tmux and the `.team-os/` harness**.

**Where the result goes**: Notes land in the same places as `/km:knowledge-manager` (`Mine/`, `Library/`). The team's working records go to `.team-os/artifacts/TEAM_PLAN.md`, `TEAM_PROGRESS.md`, and `TEAM_FINDINGS.md` in your project.

**Common mistake**: Running it without tmux. You'll see "Agent Teams requires tmux" — use `/km:knowledge-manager` instead.

## How Notes Are Stored

With Obsidian, notes go into your vault; without it, into the local folder you chose in `/km:setup` (`km-notes/`), as Obsidian-compatible Markdown. The skeleton is the same either way.

```
Your-Vault/
├── 000-START-HERE/     ← the three front-door documents from /km:setup
├── _meta/              ← USER-PROFILE · KM-DESIGN · REFORM-PLAN/REPORT
├── Mine/               ← things you wrote
└── Library/            ← everyone else's material (Zettelkasten · Papers · Clippings …)
```

## Troubleshooting

- **Check tool connections**: `claude mcp list` should show the playwright and obsidian servers. In Antigravity: Agent panel → ⋯ → MCP Servers → Refresh.
- **Where the config files live**: Plugin settings are in `km-config.json` in your project — that's the reference file. MCP registrations: Claude Code CLI = `~/.claude.json` (user scope) · Claude Desktop = `%APPDATA%\Claude\claude_desktop_config.json` · Antigravity = `~/.gemini/antigravity/mcp_config.json`.
- **Search keeps falling back to text search**: Run `/km:tofugraph` for a diagnosis. The GraphRAG server address is `linking.semantic_adapter.endpoint` in `km-config.json` (default `http://127.0.0.1:8400`).
- **Link weights and the MOC gate**: In `km-config.json`, `linking.scheme` (`"v2"` by default) and `linking.mocGate` (`"auto"` by default; `"confirm"` proposes one candidate and asks). See `km-config.example.json` for examples.

## Contributing · License · Links

Contributions: fork → branch → commit → pull request. MIT License — use, modify, and redistribute freely.

- [Claude Code](https://code.claude.com) · [Claude Code Plugins](https://claude.com/blog/claude-code-plugins)
- [MCP Protocol](https://modelcontextprotocol.io) · [Obsidian](https://obsidian.md)
- [Antigravity MCP setup guide](https://composio.dev/blog/howto-mcp-antigravity)
