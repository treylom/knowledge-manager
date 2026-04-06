"""Pipeline state management — STEP completion tracking with prerequisite enforcement."""
import json
import os
from datetime import datetime, timezone

STATE_DIR = os.path.join(os.path.dirname(__file__), "..", "state")

STEP_ORDER = [
    "STEP-0", "STEP-0.5", "STEP-1", "STEP-1.5",
    "STEP-2", "STEP-3", "STEP-4", "STEP-4.5",
    "STEP-5", "STEP-5.5", "STEP-6", "STEP-7"
]

PREREQUISITES = {
    "STEP-4.5": ["STEP-4"],
    "STEP-5":   ["STEP-4.5"],
    "STEP-5.5": ["STEP-5"],
    "STEP-6":   ["STEP-5"],
}


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _latest_session_file():
    """Find the most recent session file in STATE_DIR."""
    os.makedirs(STATE_DIR, exist_ok=True)
    files = sorted(
        [f for f in os.listdir(STATE_DIR) if f.startswith("km-") and f.endswith(".json")],
        reverse=True
    )
    if not files:
        return None
    return os.path.join(STATE_DIR, files[0])


def _load_session():
    path = _latest_session_file()
    if not path:
        return None, None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f), path


def _save_session(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _get_missing_steps(step, completed):
    """Return list of missing prerequisite steps."""
    idx = STEP_ORDER.index(step)
    missing = []

    # All prior steps must be completed (sequential enforcement)
    for prior in STEP_ORDER[:idx]:
        if prior not in completed:
            missing.append(prior)

    # Explicit prerequisites
    for prereq in PREREQUISITES.get(step, []):
        if prereq not in completed and prereq not in missing:
            missing.append(prereq)

    return missing


def run_state(action, step=None):
    if action == "init":
        return _init()

    session, path = _load_session()
    if not session:
        return {"error": "NO_SESSION", "message": "No active session. Run 'state init' first."}

    if action == "complete":
        return _complete(session, path, step)
    elif action == "check":
        return _check(session, step)
    elif action == "show":
        return _show(session)


def _init():
    os.makedirs(STATE_DIR, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M")
    session_id = f"km-{ts}"
    data = {
        "session_id": session_id,
        "created_at": _now(),
        "mode": None,
        "completed": {},
        "current": "STEP-0",
        "lint_scores": [],
        "errors": []
    }
    path = os.path.join(STATE_DIR, f"{session_id}.json")
    _save_session(data, path)
    return {**data, "file": path}


def _complete(session, path, step):
    if step not in STEP_ORDER:
        return {"error": "INVALID_STEP", "message": f"Unknown step: {step}", "valid_steps": STEP_ORDER}

    # Idempotent: already completed
    if step in session["completed"]:
        session["current"] = _next_step(step)
        _save_session(session, path)
        return {"completed": session["completed"], "current": session["current"]}

    # Check prerequisites
    missing = _get_missing_steps(step, session["completed"])
    if missing:
        error = {
            "error": "STEP_SKIP_DETECTED",
            "message": f"{step} requires {missing}, but they are not completed",
            "completed": list(session["completed"].keys()),
            "missing": missing
        }
        session["errors"].append({"step": step, "error": "STEP_SKIP_DETECTED", "at": _now()})
        _save_session(session, path)
        return error

    session["completed"][step] = _now()
    session["current"] = _next_step(step)
    _save_session(session, path)
    return {"completed": session["completed"], "current": session["current"]}


def _check(session, step):
    if step not in STEP_ORDER:
        return {"error": "INVALID_STEP", "message": f"Unknown step: {step}"}
    missing = _get_missing_steps(step, session["completed"])
    return {
        "step": step,
        "ready": len(missing) == 0,
        "missing": missing,
        "completed": list(session["completed"].keys())
    }


def _show(session):
    total = len(STEP_ORDER)
    done = len(session["completed"])
    return {
        **session,
        "progress": f"{done}/{total}"
    }


def _next_step(step):
    idx = STEP_ORDER.index(step)
    if idx + 1 < len(STEP_ORDER):
        return STEP_ORDER[idx + 1]
    return "DONE"
