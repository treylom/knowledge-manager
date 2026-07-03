"""KM Tools v2 - knowledge-manager pipeline enforcement tools."""
import argparse
import sys
import json


def main():
    parser = argparse.ArgumentParser(
        prog="km-tools",
        description="knowledge-manager pipeline enforcement tools"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # lint
    lint_parser = subparsers.add_parser("lint", help="Calculate lint_score for a draft note")
    lint_parser.add_argument("draft", help="Path to draft markdown file")
    lint_parser.add_argument("--consistency", type=float, default=None)
    lint_parser.add_argument("--suggestions", type=float, default=None)
    lint_parser.add_argument("--coverage", type=float, default=None)

    # diff
    diff_parser = subparsers.add_parser("diff", help="Section-level diff between two notes")
    diff_parser.add_argument("existing", help="Path to existing note")
    diff_parser.add_argument("new", help="Path to new content")

    # state
    state_parser = subparsers.add_parser("state", help="Pipeline state management")
    state_sub = state_parser.add_subparsers(dest="action", required=True)
    state_sub.add_parser("init", help="Start new session")
    complete_parser = state_sub.add_parser("complete", help="Mark STEP as completed")
    complete_parser.add_argument("step", help="STEP name (e.g. STEP-2)")
    check_parser = state_sub.add_parser("check", help="Check prerequisites for STEP")
    check_parser.add_argument("step", help="STEP name to check")
    state_sub.add_parser("show", help="Show current state")

    # score-links
    sl_parser = subparsers.add_parser(
        "score-links",
        help="Score candidate wikilinks and tier them (inline/related/log)",
    )
    sl_parser.add_argument(
        "input",
        help="JSON file: {target:{...}, candidates:[{...}], linking:{...}?}",
    )
    sl_parser.add_argument("--inline-threshold", type=float, default=None,
                           help="score >= this -> inline (default 0.6)")
    sl_parser.add_argument("--related-threshold", type=float, default=None,
                           help="score >= this -> related section (default 0.4)")

    args = parser.parse_args()

    if args.command == "lint":
        from lib.lint import run_lint
        result = run_lint(args.draft, args.consistency, args.suggestions, args.coverage)
    elif args.command == "diff":
        from lib.diff import run_diff
        result = run_diff(args.existing, args.new)
    elif args.command == "state":
        from lib.state import run_state
        result = run_state(args.action, getattr(args, "step", None))
    elif args.command == "score-links":
        from lib.link_scorer import (
            DEFAULT_INLINE_THRESHOLD,
            DEFAULT_RELATED_THRESHOLD,
            score_links,
        )
        from lib.adapters import load_adapter

        with open(args.input, encoding="utf-8") as f:
            payload = json.load(f)
        adapter = load_adapter(payload.get("linking"))
        result = score_links(
            payload.get("target", {}),
            payload.get("candidates", []),
            inline_threshold=(
                args.inline_threshold
                if args.inline_threshold is not None
                else DEFAULT_INLINE_THRESHOLD
            ),
            related_threshold=(
                args.related_threshold
                if args.related_threshold is not None
                else DEFAULT_RELATED_THRESHOLD
            ),
            adapter=adapter,
        )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
