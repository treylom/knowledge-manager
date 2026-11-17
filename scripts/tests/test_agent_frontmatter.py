#!/usr/bin/env python3
"""test_agent_frontmatter.py — 에이전트 파일의 앞머리(tools)와 «명령 파일이 이걸 한다»는 글이 사실과 맞는지 본다.

T1 `agents/*.md` 에 `tools:` 줄이 있으면 낱말마다 실제 도구 이름 꼴인가
   (내장 도구 이름 · `mcp__<서버>__<도구>` · `mcp__<서버>__*` · `Agent(이름, …)` 같은 괄호 꼴).
   `tools:` 는 허용 목록이라(그 밖은 못 쓴다) 이름이 틀리면 띄운 에이전트가 쓸 도구가 모자란다.
T2 본문이 쓰라고 하는 도구가 `tools:` 줄이 있을 때 그 안에 있는가
   — 묻기 요구(«반드시 질문» · AskUserQuestion) → AskUserQuestion · 호출 꼴 `Read(` `Write(` … · 셸 블록 → Bash ·
   `mcp__<서버>__<도구>` → 그 서버 · 팀 도구 낱말(TeamCreate · TeamDelete · TaskCreate · SendMessage — 단일 에이전트 제외:
   단일 에이전트의 팀 낱말은 T3 가 본다).
   `tools:` 줄이 없으면 물려받으므로 칸은 통과.
T3 «명령 파일이 X 를 한다» 글이 명령 파일 실제와 맞는가
   — `/knowledge-manager`(단일 에이전트) · `commands/knowledge-manager.md` · «commands 파일» 을 주어로 Agent Teams · 팀 구성 ·
     병렬 모드 결정 · 복잡도 판정을 «자동 구성 · 자동 실행 · 직접 호출» 한다는 줄이 있는데 그 명령 파일이 팀을
     만들지 않으면(허용 도구에 TeamCreate 없음 · 본문에 `TeamCreate(` 없음) 실패.
   — 단일 에이전트(name: knowledge-manager)에 팀 만들기 지시(TeamCreate · TaskCreate · TeamDelete · SendMessage)가
     «-at 전용» 머리 절 밖에 0.

인자(저장소 밖에 둔 사본을 검사할 때):
  --agents-dir D    에이전트 파일 폴더(기본 = 저장소 agents/)
  --commands-dir D  명령 파일 폴더(기본 = 저장소 commands/)
  --skills-dir D    T3 의 거짓 문장 찾기에 넣을 스킬 폴더(기본 = 저장소 skills/ · 빈 문자열 = 건너뜀)
  --no-docs         README.md · CLAUDE.md · AGENTS.md · .agent/skills 를 T3 찾기에서 뺀다
표준 라이브러리만. 자체 점검(양성 · 음성)은 매번 먼저 돈다.
"""
import argparse
import glob
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Claude Code 내장 도구 이름(대소문자 그대로). 모르는 낱말이 섞이면 T1 실패.
BUILTIN = {
    "Agent", "Task", "AskUserQuestion", "Bash", "BashOutput", "CronCreate", "CronDelete", "CronList", "Edit",
    "EnterPlanMode", "EnterWorktree", "ExitPlanMode", "ExitWorktree", "Glob", "Grep", "KillShell", "LSP",
    "ListMcpResourcesTool", "Monitor", "MultiEdit", "NotebookEdit", "NotebookRead", "PowerShell", "Read",
    "ReadMcpResourceTool", "SendMessage", "Skill", "SlashCommand", "TaskCreate", "TaskGet", "TaskList", "TaskOutput",
    "TaskStop", "TaskUpdate", "TeamCreate", "TeamDelete", "TodoWrite", "ToolSearch", "WebFetch", "WebSearch",
    "Workflow", "Write",
}
MCP_ENTRY = re.compile(r"^mcp__[A-Za-z0-9_-]+?__(\*|[A-Za-z0-9_-]+)$")
PAREN_ENTRY = re.compile(r"^([A-Za-z]+)\(.*\)$")

ASK_PAT = re.compile(r"AskUserQuestion|반드시 (아래 )?질문|질문 후 진행")
CALL_PAT = re.compile(r"\b(Read|Write|Edit|Bash|Glob|Grep|WebFetch|WebSearch)\(")
MCP_USE = re.compile(r"\bmcp__([A-Za-z0-9_-]+?)__([A-Za-z0-9_-]+)")
TEAM_PAT = re.compile(r"\b(TeamCreate|TeamDelete|TaskCreate|SendMessage)\b")
SHELL_FENCE = re.compile(r"^\s*```(bash|sh|zsh|shell)\s*$", re.M)

# T3 — 단일 에이전트 명령을 주어로 팀 구성을 «한다»고 적은 줄
CLAIM_SUBJECT = re.compile(r"`/knowledge-manager`|/knowledge-manager(?![-\w])|commands/knowledge-manager\.md|commands 파일")
CLAIM_OBJECT = re.compile(r"Agent Teams|TeamCreate|팀 구성|병렬 모드 결정|복잡도 판정")
CLAIM_VERB = re.compile(r"자동 ?구성|자동으로 구성|자동 실행|직접 호출")
NEGATION = re.compile(r"않|없|아님|❌|미지원|not ")
# 머리 글이 «-at 전용» 으로 시작하고 바로 뒤가 «아님» 이 아닐 때만 그 절을 뺀다
AT_ONLY_HEAD = re.compile(r"^-at 전용(?!\s*(아님|이 아님|아닌))(\s|—|-|$)")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")

fails = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (" — " + detail if detail else ""))
    if not ok:
        fails.append(name)


def split_front(text):
    """(frontmatter dict of raw values, body). 앞머리가 없으면 ({}, text)."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, text
    fm, i = {}, 1
    key = None
    while i < len(lines) and lines[i].strip() != "---":
        line = lines[i]
        m = re.match(r"^([A-Za-z][\w-]*):\s*(.*)$", line)
        if m:
            key = m.group(1)
            v = m.group(2).strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":  # name: "knowledge-manager" 같은 따옴표 꼴
                v = v[1:-1]
            fm[key] = v
        elif key and re.match(r"^\s+-\s+", line):  # YAML 목록 꼴
            fm[key] = (fm[key] + ", " if fm[key] else "") + re.sub(r"^\s+-\s+", "", line).strip()
        i += 1
    return fm, "\n".join(lines[i + 1:])


def split_entries(value):
    """쉼표로 가르되 괄호 안 쉼표는 두고, 대괄호 목록 꼴도 받는다."""
    v = value.strip()
    if v.startswith("[") and v.endswith("]"):
        v = v[1:-1]
    out, depth, cur = [], 0, ""
    for ch in v:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur.strip().strip("'\""))
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip().strip("'\""))
    return [e for e in out if e]


def bad_tool_entries(value):
    bad = []
    for e in split_entries(value):
        m = PAREN_ENTRY.match(e)
        if e in BUILTIN or MCP_ENTRY.match(e) or (m and m.group(1) in BUILTIN):
            continue
        bad.append(e)
    return bad


def kept_lines(text):
    """«-at 전용» 머리 절(코드 울타리 밖 머리 · 같거나 높은 머리까지)을 뺀 (원래 줄 번호, 줄) 목록."""
    out, skip_level, fence = [], None, None  # fence = 연 울타리 표지(``` 또는 ~~~ 와 길이) — 같은 표지로만 닫힌다
    for no, line in enumerate(text.split("\n"), 1):
        f = FENCE.match(line)
        if f:
            mark = f.group(1)
            if fence is None:
                fence = mark
            elif mark[0] == fence[0] and len(mark) >= len(fence) and not line.strip()[len(mark):].strip():
                fence = None
        head = None if fence is not None or f else re.match(r"^(#{1,6})\s+(.*)$", line)
        if head:
            level = len(head.group(1))
            if skip_level is not None and level <= skip_level:
                skip_level = None
            if skip_level is None and AT_ONLY_HEAD.search(head.group(2).strip()):
                skip_level = level
        if skip_level is None:
            out.append((no, line))
    return out


def strip_at_only(body):
    """«-at 전용» 머리 절을 뺀 본문(kept_lines 와 같은 파서)."""
    return "\n".join(l for _, l in kept_lines(body))


def required_tools(body, team=True):
    """team=False: 팀 도구 낱말은 요구하지 않는다 — 단일 에이전트의 팀 낱말은 T3 의 몫(칸이 겹쳐 세지 않게)."""
    req = set()
    if ASK_PAT.search(body):
        req.add("AskUserQuestion")
    req.update(CALL_PAT.findall(body))
    if SHELL_FENCE.search(body):
        req.add("Bash")
    req.update("mcp__%s__" % s for s, _ in MCP_USE.findall(body))
    if team:
        req.update(TEAM_PAT.findall(body))
    return req


def missing_tools(tools_value, body, team=True):
    entries = split_entries(tools_value)
    names = {PAREN_ENTRY.match(e).group(1) if PAREN_ENTRY.match(e) else e for e in entries}
    miss = []
    for r in sorted(required_tools(body, team)):
        if r.startswith("mcp__"):
            if not any(e == r + "*" or e.startswith(r) and not e.endswith("__") for e in entries):
                miss.append(r + "*")
        elif r not in names:
            miss.append(r)
    return miss


def claim_lines(text):
    hits = []
    for i, line in enumerate(text.split("\n"), 1):
        if CLAIM_SUBJECT.search(line) and CLAIM_OBJECT.search(line) and CLAIM_VERB.search(line) \
                and not NEGATION.search(line):
            hits.append((i, line.strip()))
    return hits


def command_builds_team(commands_dir):
    p = os.path.join(commands_dir, "knowledge-manager.md")
    if not os.path.exists(p):
        return None
    fm, _ = split_front(open(p, encoding="utf-8").read())
    # 팀을 꾸리려면 TeamCreate 도구가 허용돼 있어야 한다 — 본문 글(부정문 포함)로는 판정하지 않는다
    allowed = fm.get("allowed-tools", "") + "," + fm.get("allowedTools", "")
    return "TeamCreate" in split_entries(allowed)


def team_lines_outside_at(text):
    """파일 전문을 받아 «-at 전용» 절 밖의 팀 도구 줄을 (파일 줄 번호, 줄) 로."""
    return [(i, l.strip()) for i, l in kept_lines(text) if TEAM_PAT.search(l)]


def self_test():
    """자체 점검 쌍 — 검사 함수가 나쁜 꼴은 잡고(양성) 좋은 꼴은 놓아주는지(음성)."""
    shipped = "hyperbrowser, obsidian, notion, file-operations, read, write, bash, drawio, playwright, notebooklm"
    check("bait-T1-positive (shipped line rejected)", set(bad_tool_entries(shipped)) == set(split_entries(shipped)),
          ",".join(bad_tool_entries(shipped)))
    check("bait-T1-negative (real names accepted)",
          bad_tool_entries("Read, Write, Bash, Glob, mcp__notion__*, mcp__plugin_playwright_playwright__*, "
                           "mcp__obsidian__create_note, Agent(worker, researcher), AskUserQuestion") == [])
    check("bait-T1-lowercase (read ≠ Read)", bad_tool_entries("read, Write") == ["read"])
    body_ask = "**콘텐츠 처리 전 반드시 아래 질문을 사용자에게 표시:**\n```bash\nls\n```\nWrite(\"a\")\nmcp__notion__API-post-page"
    check("bait-T2-positive (asks but no AskUserQuestion)", "AskUserQuestion" in missing_tools("Read, Write, Bash, mcp__notion__*", body_ask))
    check("bait-T2-negative (all covered)", missing_tools("Read, Write, Bash, AskUserQuestion, mcp__notion__*", body_ask) == [])
    check("bait-T2-mcp (server not covered)", missing_tools("Read, Write, Bash, AskUserQuestion", body_ask) == ["mcp__notion__*"])
    check("bait-T2-team (team words need team tools, unless single agent)",
          missing_tools("Read", "SendMessage relay · TeamDelete") == ["SendMessage", "TeamDelete"]
          and missing_tools("Read", "SendMessage relay · TeamDelete", team=False) == [])
    check("bait-T3-positive", len(claim_lines(
        "**CRITICAL**: `/knowledge-manager` 호출 시 `commands/knowledge-manager.md`가 Agent Teams를 자동 구성합니다.\n"
        "| **터미널 CLI** | Agent Teams | 기본 가정 — `/knowledge-manager` 직접 호출 |\n"
        "Phase 0: 병렬 모드 결정 ⭐ (commands 파일에서 자동 실행)")) == 3)
    check("bait-T3-negative", claim_lines(
        "이 명령어는 풀스케일 Agent Teams(9명)를 자동 구성합니다.\n"
        "팀 병렬 처리(Agent Teams)는 `/knowledge-manager-at`(`commands/knowledge-manager-at.md`)이 자동 구성합니다.\n"
        "`/knowledge-manager` 는 Agent Teams 를 자동 구성하지 않습니다.\n"
        "단일 에이전트 버전: `/knowledge-manager` (Agent Teams 미지원 환경용)") == [])
    sec = ("## A\nTeamCreate 밖\n```bash\n# 코드 안 머리 아님 -at 전용\nTaskCreate\n```\n"
           "### -at 전용 — 이 에이전트는 실행하지 않음\nTeamCreate 안\n#### 아래 단계\nSendMessage 안\n## B\nok")
    outside = [l for _, l in team_lines_outside_at(sec)]
    check("bait-T3-section (outside counted, inside skipped, code # ignored)",
          outside == ["TeamCreate 밖", "TaskCreate"], repr(outside))
    tricky = ("### -at 전용 아님\nTeamCreate 아님절\n## C\n````md\n```\n# 안쪽 머리 -at 전용\n````\nSendMessage 울타리 뒤\n"
              "### 이건 -at 전용 아님 설명\nTaskCreate 중간머리")
    got = [l for _, l in team_lines_outside_at(tricky)]
    check("bait-T3-section-strict (only a heading that starts with «-at 전용» · fences close on the same marker)",
          got == ["TeamCreate 아님절", "SendMessage 울타리 뒤", "TaskCreate 중간머리"], repr(got))
    fm, _ = split_front('---\nname: "knowledge-manager"\ntools: Read\n---\nbody')
    check("bait-frontmatter-quoted-name", fm.get("name") == "knowledge-manager", repr(fm.get("name")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agents-dir", default=os.path.join(REPO, "agents"))
    ap.add_argument("--commands-dir", default=os.path.join(REPO, "commands"))
    ap.add_argument("--skills-dir", default=os.path.join(REPO, "skills"))
    ap.add_argument("--no-docs", action="store_true")
    a = ap.parse_args()

    self_test()

    agents = sorted(glob.glob(os.path.join(a.agents_dir, "*.md")))
    check("targets-found", len(agents) >= 1, f"{len(agents)} agent files in {a.agents_dir}")
    builds_team = command_builds_team(a.commands_dir)
    check("command-file-found", builds_team is not None, os.path.join(a.commands_dir, "knowledge-manager.md"))

    for p in agents:
        rel = os.path.basename(p)
        text = open(p, encoding="utf-8").read()
        fm, body = split_front(text)
        is_single = fm.get("name") == "knowledge-manager"
        scan_body = strip_at_only(body) if is_single else body
        if "tools" in fm:
            bad = bad_tool_entries(fm["tools"])
            check("T1 tools-names " + rel, not bad, "unknown: " + ", ".join(bad) if bad else fm["tools"][:120])
            miss = missing_tools(fm["tools"], scan_body, team=not is_single)
            check("T2 tools-cover-body " + rel, not miss, "missing: " + ", ".join(miss) if miss else "")
        else:
            check("T1 tools-names " + rel, True, "no tools: line (inherits)")
            check("T2 tools-cover-body " + rel, True, "no tools: line (inherits)")
        if is_single:
            outside = team_lines_outside_at(text)
            check("T3 single-agent-no-team-steps-outside-at-only " + rel, not outside,
                  "; ".join(f"{i}:{l[:80]}" for i, l in outside[:4]))

    # T3 거짓 주장 — 에이전트 · 명령 · 스킬 · (기본) 안내 문서
    files = agents + sorted(glob.glob(os.path.join(a.commands_dir, "*.md")))
    if a.skills_dir:
        files += sorted(glob.glob(os.path.join(a.skills_dir, "*.md")) + glob.glob(os.path.join(a.skills_dir, "*", "SKILL.md")))
    if not a.no_docs:
        files += [os.path.join(REPO, n) for n in ("README.md", "CLAUDE.md", "AGENTS.md") if os.path.exists(os.path.join(REPO, n))]
        files += sorted(glob.glob(os.path.join(REPO, ".agent", "skills", "*", "SKILL.md")))
    claims = []
    for p in files:
        for i, line in claim_lines(open(p, encoding="utf-8").read()):
            claims.append(f"{os.path.relpath(p, REPO) if p.startswith(REPO) else p}:{i}: {line[:90]}")
    check("T3 claims-match-command-file", builds_team or not claims,
          f"command builds team={builds_team} · false claims {len(claims)}: " + " | ".join(claims[:4]))

    print("OK" if not fails else f"FAILED {len(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
