# Knowledge Manager 에 기여하기

🇺🇸 English is below.

## 피드백이 먼저

Knowledge Manager 를 써 보고 안 된 점이나 바라는 점이 있으면 **킷 사용 피드백** 양식으로 이슈를 열어 주세요(Issues → New issue → 킷 사용 피드백 / Kit feedback). GitHub 계정이 필요합니다. 이메일·실명은 적지 않아도 되고, 연락은 이슈 댓글로만 합니다. 로그를 붙일 때는 토큰·비밀번호·개인정보를 지워 주세요.

## 피드백이 고침이 되기까지

1. **피드백** — 킷 사용 피드백 이슈를 엽니다.
2. **결정** — 관리자가 그 이슈에 댓글 한 줄을 남깁니다: 받아들임 · 나중에 · 받지 않음, 이유 한 줄과 함께.
3. **고침** — 고치는 Pull Request 는 PR 양식의 **피드백 출처: #이슈 번호** 칸을 채우고 이슈를 연결합니다(`Refs #N` 또는 `Fixes #N`).
4. **출처 표기** — 고친 커밋이나 PR 에 이슈 번호를 남기고, 그 고침이 들어간 CHANGELOG 항목 끝에 `(피드백 #N)` 을 붙입니다. 누구나 어떤 고침이 어떤 피드백에서 시작됐는지 따라갈 수 있게 하려는 것입니다. 이 규칙 전에 쓴 CHANGELOG 항목은 고치지 않습니다.

## 코드 기여

Fork → 브랜치 → 커밋 → Pull Request. 올리기 전에 바꾼 부분의 시험을 돌리고 PR 에 무엇을 확인했는지 적어 주세요. 피드백 이슈에서 시작한 고침이면 피드백 출처 칸을 채워 주세요.

---

# Contributing to Knowledge Manager

## Feedback first

If you used Knowledge Manager and something did not work, or you wished it did something else, open an issue with the **Kit feedback** form (Issues → New issue → Kit feedback). You need a GitHub account. No email address or real name is needed, and we only follow up in the issue's comments. Please remove tokens, passwords and personal details from logs before you paste them.

## How feedback becomes a change

1. **Feedback** — you open a Kit feedback issue.
2. **Decision** — the maintainer leaves one comment on that issue: accepted, not now, or declined, with a one-line reason.
3. **Change** — the pull request that makes the change fills in **Feedback source: #issue-number** in the PR template and links the issue (`Refs #N` or `Fixes #N`).
4. **Credit** — the commit or pull request that ships the change names the issue number, and the CHANGELOG entry for that change ends with `(feedback #N)`, so anyone can trace a change back to the feedback that started it. CHANGELOG entries written before this rule are left as they are.

## Code contributions

Fork → branch → commit → pull request. Before you push, run the tests for the part you changed and say in the PR what you checked. If your change comes from a feedback issue, fill in the feedback source line.
