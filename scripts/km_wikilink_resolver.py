"""Resolve wikilink names from a verified same-vault map note, then read the note through the unchanged path guard."""
import argparse
import hashlib
import importlib.util
import json
import os
import posixpath
import re
import stat
import unicodedata
from datetime import datetime
from pathlib import Path

_spec = importlib.util.spec_from_file_location("a2_guard", Path(__file__).with_name("km_search_guard.py"))
guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(guard)


def inventory_vault(root):
    started = datetime.now().astimezone().isoformat()
    paths = []
    errors = []
    skipped_symlinks = 0
    base = Path(root)
    try:
        if not stat.S_ISDIR(base.lstat().st_mode):
            raise OSError("root must be a regular directory")
        for current, dirs, names in os.walk(base, followlinks=False,
                                            onerror=lambda e: errors.append(type(e).__name__)):
            kept = []
            for name in sorted(dirs):
                if name in (".git", ".obsidian"):
                    continue
                try:
                    mode = (Path(current) / name).lstat().st_mode
                    if stat.S_ISLNK(mode):
                        skipped_symlinks += 1
                    elif stat.S_ISDIR(mode):
                        kept.append(name)
                except OSError as exc:
                    errors.append(type(exc).__name__)
            dirs[:] = kept
            for name in sorted(names):
                if not name.endswith(".md"):
                    continue
                item = Path(current) / name
                try:
                    mode = item.lstat().st_mode
                    if stat.S_ISLNK(mode):
                        skipped_symlinks += 1
                    elif stat.S_ISREG(mode):
                        paths.append(guard.relative_note(item.relative_to(base).as_posix()))
                except (OSError, ValueError) as exc:
                    errors.append(type(exc).__name__)
    except OSError as exc:
        errors.append(type(exc).__name__)
    if len(paths) != len(set(paths)):
        errors.append("normalized_path_collision")
    paths.sort()
    return {"paths": paths, "complete": not errors, "errors": errors,
            "started_at": started, "finished_at": datetime.now().astimezone().isoformat(),
            "path_count": len(paths), "skipped_symlinks": skipped_symlinks,
            "sha256": hashlib.sha256(json.dumps(paths, ensure_ascii=False,
                                                 separators=(",", ":")).encode()).hexdigest(),
            "scope": "regular .md files; no symlink traversal; .git/.obsidian excluded; non-atomic metadata observation"}


def resolve_wikilink(mode, map_source, target, inventory, complete, folder_hints=()):
    if mode != "same":
        return guard.unavailable("other_vault_resolution_disabled")
    if not complete:
        return guard.unavailable("inventory_incomplete")
    try:
        map_source = guard.relative_note(map_source)
        paths = [guard.relative_note(p) for p in inventory]
        if len(paths) != len(set(paths)):
            return guard.unavailable("inventory_path_collision")
        if not isinstance(folder_hints, (list, tuple)):
            return guard.unavailable("invalid_folder_hints")
        name = target.split("|", 1)[0].split("#", 1)[0].strip()
        name = name if name.endswith(".md") else name + ".md"
        strategy = "basename"
        if "/" in name:
            options = set()
            for raw in (name, posixpath.join(posixpath.dirname(map_source), name)):
                try:
                    options.add(guard.relative_note(posixpath.normpath(raw)))
                except ValueError:
                    continue
            candidates = sorted(p for p in paths if p in options)
            strategy = "root_or_map_relative"
            if not candidates:
                suffix = guard.relative_note(posixpath.normpath(name))
                candidates = sorted(p for p in paths if p.endswith("/" + suffix))
                strategy = "segment_suffix"
        else:
            name = guard.relative_note(name)
            candidates = sorted(p for p in paths if posixpath.basename(p) == name)
        before_paths = candidates[:]
        used_hint = len(candidates) > 1 and bool(folder_hints)
        if used_hint:
            hints = []
            for raw in folder_hints:
                hint = raw.rstrip("/")
                guard.relative_note(hint + "/__hint__.md")
                hints.append(unicodedata.normalize("NFC", hint))
            candidates = [p for p in candidates if all(p.startswith(h + "/") for h in hints)]
    except (ValueError, TypeError, AttributeError):
        return guard.unavailable("invalid_link_or_inventory")
    evidence = {"candidates_before": before_paths, "candidates_after": candidates,
                "candidate_count_before": len(before_paths),
                "candidate_count_after": len(candidates), "used_hint": used_hint,
                "strategy": strategy}
    if len(candidates) != 1:
        return {**guard.unavailable("ambiguous_link" if len(before_paths) > 1 else "no_link_candidate"),
                **evidence}
    return {"status": "resolved", "source_note": candidates[0], **evidence}


def folder_hints(line):
    # Hints must be explicit backticked directories on the link's own line.
    return [value for value in re.findall(r"`([^`]+)`", line)
            if value.endswith("/") and "/" in value and "://" not in value]


def follow(mode, root, map_source, target_name, inventory_builder=None):
    if mode != "same":
        return guard.unavailable("other_vault_resolution_disabled")
    mapped = guard.local_note(root, map_source)
    if mapped.get("status") != "verified":
        return {**guard.unavailable("map_not_verified"), "map_reason": mapped.get("reason")}
    builder = inventory_builder or inventory_vault
    inv = builder(root)
    body = mapped["body"]
    evidence = {"map_source_note": mapped["source_note"],
                "map_excerpt_sha256": mapped["body_sha256"],
                "map_excerpt_chars": len(body), "map_excerpt_truncated": mapped["truncated"],
                "map_excerpt_frontmatter": body.startswith("---\n") or body.startswith("---\r\n"),
                "inventory": {k: v for k, v in inv.items() if k != "paths"}, "links": []}
    expected = unicodedata.normalize("NFC", target_name.removesuffix(".md"))
    destinations = set()
    failed = False
    for match in re.finditer(r"\[\[([^\]\n]+)\]\]", body):
        token = match.group(1)
        target = token.split("|", 1)[0].split("#", 1)[0].strip()
        if unicodedata.normalize("NFC", posixpath.basename(target).removesuffix(".md")) != expected:
            continue
        line_start = body.rfind("\n", 0, match.start()) + 1
        line_end = body.find("\n", match.start())
        line = body[line_start:line_end if line_end >= 0 else len(body)]
        hints = folder_hints(line)
        resolution = resolve_wikilink(mode, map_source, target, inv["paths"],
                                      inv["complete"], hints)
        evidence["links"].append({"target": target, "line_1based": body[:match.start()].count("\n") + 1,
                                  "char_offset_0based": match.start(),
                                  "utf8_offset_0based": len(body[:match.start()].encode()),
                                  "folder_hints": hints, "resolution": resolution})
        if resolution.get("status") == "resolved":
            destinations.add(resolution["source_note"])
        else:
            failed = True
    if not evidence["links"] or failed or len(destinations) != 1:
        return {**guard.unavailable("link_not_uniquely_resolved"), **evidence}
    canonical = next(iter(destinations))
    note = guard.local_note(root, canonical)
    return {**note, **evidence, "resolved_source_note": canonical}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("same", "other"), required=True)
    parser.add_argument("--root", required=True)
    parser.add_argument("--map-source", required=True)
    parser.add_argument("--target-name", required=True)
    args = parser.parse_args()
    result = follow(args.mode, args.root, args.map_source, args.target_name)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("status") == "verified" else 3


if __name__ == "__main__":
    raise SystemExit(main())
