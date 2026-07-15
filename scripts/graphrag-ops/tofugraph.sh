#!/bin/bash
# tofugraph — GraphRAG ops adapter for Knowledge Manager (optional adapter).
# Verbs: build | search | status | doctor | heal | monitor | install-daemon | uninstall-daemon
#
# Best-effort by design: it FIXES what it safely can (stuck server restart, stale
# index re-build trigger) and only REPORTS what it can't (sudo/OS updates,
# hardware pressure, corrupted vault content). See km-graphrag-ops.md for the table.
#
# Config resolution: env > auto-detect > default. No paths are hardcoded.
#   GRAPHRAG_ROOT           graphrag home (default: nearest .team-os/graphrag walking up from cwd)
#   GRAPHRAG_API_URL        server base URL (default: http://127.0.0.1:8400)
#   GRAPHRAG_SERVICE_LABEL  launchd label / systemd user unit (default: auto-detect)
#   NTFY_TOPIC              optional push topic for daemon alerts (default: off)
set -uo pipefail

API="${GRAPHRAG_API_URL:-http://127.0.0.1:8400}"

resolve_root() {
  if [ -n "${GRAPHRAG_ROOT:-}" ]; then echo "$GRAPHRAG_ROOT"; return; fi
  local d="$PWD"
  while [ "$d" != "/" ]; do
    if [ -d "$d/.team-os/graphrag" ]; then echo "$d/.team-os/graphrag"; return; fi
    d=$(dirname "$d")
  done
  echo ""
}
ROOT=$(resolve_root)
LOGS="${ROOT:+$ROOT/logs}"

resolve_service() {
  # Prefer the *server* unit — a graphrag deployment may also run worker/build
  # units (embedding worker, daily rebuild) and restarting those heals nothing.
  if [ -n "${GRAPHRAG_SERVICE_LABEL:-}" ]; then echo "$GRAPHRAG_SERVICE_LABEL"; return; fi
  local all
  if [[ "$OSTYPE" == darwin* ]]; then
    all=$(launchctl list 2>/dev/null | awk '{print $3}' | grep -i graphrag)
  else
    all=$(systemctl --user list-units --type=service --all 2>/dev/null \
      | awk '{print $1}' | grep -i graphrag)
  fi
  echo "$all" | grep -i -E 'serve|server' | head -1 || echo "$all" | head -1
}

restart_server() {
  local label; label=$(resolve_service)
  if [ -z "$label" ]; then
    echo "  → cannot restart: no service registered (run install-daemon, or start the server manually)"
    return 1
  fi
  if [[ "$OSTYPE" == darwin* ]]; then
    launchctl kickstart -k "gui/$(id -u)/$label"
  else
    systemctl --user restart "$label"
  fi
}

wait_ready() {  # up to 60s
  for _ in $(seq 1 12); do
    sleep 5
    if curl -s -m 5 "$API/ready" 2>/dev/null \
      | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get('ready') else 1)" 2>/dev/null; then
      return 0
    fi
  done
  return 1
}

# ---------------------------------------------------------------- doctor ----
doctor() {
  local fails=0 warns=0
  echo "tofugraph doctor — $(date '+%F %T')"
  echo "api=$API root=${ROOT:-'(not found)'}"
  echo

  # 1. server answering?
  local health
  health=$(curl -s -m 5 -o /dev/null -w '%{http_code}' "$API/health" 2>/dev/null || echo ERR)
  if [ "$health" = "200" ]; then
    echo "[OK]   1. server /health 200"
  else
    echo "[FAIL] 1. server /health=$health — server down or hung."
    echo "       fix: re-check in 60s (transient hiccups self-recover);"
    echo "            if still down, this tool can restart it: tofugraph.sh heal"
    fails=$((fails+1))
  fi

  # 2. ready (index loaded)?
  if curl -s -m 5 "$API/ready" 2>/dev/null \
    | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get('ready') else 1)" 2>/dev/null; then
    echo "[OK]   2. /ready true (index loaded)"
  else
    echo "[WARN] 2. /ready not true — warming up (normal ~30-60s after restart) or index missing."
    echo "       fix: wait 60s and re-run; if persistent, run: tofugraph.sh build"
    warns=$((warns+1))
  fi

  # 3. real search round-trip (health can be false-green while search is wedged)
  if [ "$health" = "200" ]; then
    local probe
    probe=$(curl -s -m 25 -o /tmp/tofugraph_probe.json -w '%{http_code}' \
      "$API/api/search?q=test&mode=hybrid&top_k=1" 2>/dev/null || echo ERR)
    if [ "$probe" = "200" ] && python3 -c \
      "import json; d=json.load(open('/tmp/tofugraph_probe.json')); assert 'results' in d" 2>/dev/null; then
      echo "[OK]   3. search probe answered (results key present)"
    else
      echo "[FAIL] 3. search probe http=$probe — 'wedge': health OK but search stuck."
      echo "       fix: tofugraph.sh heal  (restarts only after a second confirmation — no false-positive kills)"
      fails=$((fails+1))
    fi
  else
    echo "[SKIP] 3. search probe (server not answering)"
  fi

  # 4. index freshness
  if [ -n "$ROOT" ] && [ -f "$ROOT/index/vault_graph.db" ]; then
    local mtime now age_h
    if [[ "$OSTYPE" == darwin* ]]; then mtime=$(stat -f '%m' "$ROOT/index/vault_graph.db"); else mtime=$(stat -c '%Y' "$ROOT/index/vault_graph.db"); fi
    now=$(date +%s); age_h=$(( (now - mtime) / 3600 ))
    if [ "$age_h" -le 168 ]; then
      echo "[OK]   4. index freshness: updated ${age_h}h ago"
    else
      echo "[WARN] 4. index is ${age_h}h old (>7 days) — new notes are invisible to search."
      echo "       fix: tofugraph.sh build   (or check why the scheduled build stopped)"
      warns=$((warns+1))
    fi
  else
    echo "[WARN] 4. index db not found under \$GRAPHRAG_ROOT — not built yet?  fix: tofugraph.sh build"
    warns=$((warns+1))
  fi

  # 5. disk headroom (builds need transient space; low disk blocks everything)
  local free_gi
  free_gi=$(df "$([[ "$OSTYPE" == darwin* ]] && echo -g || echo -BG)" "${ROOT:-$PWD}" 2>/dev/null | tail -1 | awk '{print $4}' | tr -dc '0-9')
  if [ "${free_gi:-0}" -ge 10 ] 2>/dev/null; then
    echo "[OK]   5. disk ${free_gi}Gi free"
  else
    echo "[WARN] 5. disk ${free_gi:-?}Gi free (<10Gi) — REPORT-ONLY: freeing space / OS updates need a human."
    warns=$((warns+1))
  fi

  # 6. update/worker state (don't fight a running rebuild)
  local upd
  upd=$(curl -s -m 5 "$API/api/index/status" 2>/dev/null | python3 -c \
    "import json,sys
try: d=json.load(sys.stdin); print(('updating:'+d.get('phase','?')) if d.get('update_in_progress') else 'idle')
except Exception: print('unknown')" 2>/dev/null || echo unknown)
  echo "[INFO] 6. index update state: $upd  (while updating, slow probes are expected — do not restart)"

  # 7. service registration (auto mode)
  local label; label=$(resolve_service)
  if [ -n "$label" ]; then
    echo "[OK]   7. service registered: $label (auto-restart possible)"
  else
    echo "[INFO] 7. no service registered — manual mode. For auto-heal: tofugraph.sh install-daemon"
  fi

  echo
  echo "summary: ${fails} fail, ${warns} warn — $( [ $fails -eq 0 ] && echo 'usable' || echo 'needs attention' )"
  return $fails
}

# ------------------------------------------------------------------ heal ----
heal() {
  # Manual one-shot heal: confirm twice (60s apart) before restarting — the
  # double-check is what prevents false-positive kill loops (measured in prod).
  local h1 probe1
  h1=$(curl -s -m 5 -o /dev/null -w '%{http_code}' "$API/health" 2>/dev/null || echo ERR)
  probe1=$(curl -s -m 25 -o /dev/null -w '%{http_code}' "$API/api/search?q=test&mode=hybrid&top_k=1" 2>/dev/null || echo ERR)
  if [ "$h1" = "200" ] && [ "$probe1" = "200" ]; then
    echo "server healthy (health 200, search answers) — nothing to heal"; return 0
  fi
  echo "unhealthy (health=$h1 probe=$probe1) — confirming in 60s (transients self-recover)..."
  sleep 60
  h1=$(curl -s -m 5 -o /dev/null -w '%{http_code}' "$API/health" 2>/dev/null || echo ERR)
  probe1=$(curl -s -m 25 -o /dev/null -w '%{http_code}' "$API/api/search?q=test&mode=hybrid&top_k=1" 2>/dev/null || echo ERR)
  if [ "$h1" = "200" ] && [ "$probe1" = "200" ]; then
    echo "recovered on its own — no restart needed"; return 0
  fi
  echo "confirmed stuck → restarting service..."
  if restart_server; then
    if wait_ready; then echo "recovered: restart + /ready GREEN"; return 0
    else echo "partial: restarted but /ready timed out — wait 2-3min (model warm-up) and run doctor"; return 1; fi
  else
    echo "restart unavailable — start the server manually, then run doctor"; return 1
  fi
}

# ---------------------------------------------------------------- status ----
status() {
  doctor | head -4
  local qlog="${LOGS:+$LOGS/query-log.jsonl}"
  if [ -n "$qlog" ] && [ -f "$qlog" ]; then
    python3 - "$qlog" << 'PY'
import json, sys, statistics as st, datetime
cut = (datetime.datetime.now().astimezone() - datetime.timedelta(hours=24)).isoformat()
el = []
with open(sys.argv[1]) as f:
    for line in f:
        try: r = json.loads(line)
        except Exception: continue
        if r.get('timestamp_kst','') >= cut and r.get('top_k') != 1:
            el.append(r['elapsed_ms']/1000)
if el:
    el.sort(); n = len(el)
    p90 = el[min(n-1, int(0.9*n))]
    print(f"last 24h: {n} queries | median {st.median(el):.2f}s | p90 {p90:.2f}s | >10s {sum(1 for e in el if e>10)}/{n}")
else:
    print("last 24h: no queries logged")
PY
  else
    echo "query log not found (server logs to \$GRAPHRAG_ROOT/logs/query-log.jsonl)"
  fi
}

# --------------------------------------------------------------- monitor ----
monitor() {
  # One daemon tick: dead-server double-check → wedge double-check → restart+verify.
  # State lives next to the logs so consecutive ticks share the wedge counter.
  [ -z "$ROOT" ] && { echo "monitor needs GRAPHRAG_ROOT"; return 1; }
  mkdir -p "$LOGS"
  local heal_log="$LOGS/auto-heal.log" wedge_state="$LOGS/wedge-consecutive-count.state"
  local ts; ts=$(date '+%F %T')

  local health
  health=$(curl -s -m 5 -o /dev/null -w '%{http_code}' "$API/health" 2>/dev/null || echo ERR)
  if [ "$health" != "200" ]; then
    echo "[$ts] health=$health (1st,5s) → recheck in 60s" >> "$heal_log"
    sleep 60
    health=$(curl -s -m 5 -o /dev/null -w '%{http_code}' "$API/health" 2>/dev/null || echo ERR)
    if [ "$health" != "200" ]; then
      echo "[$ts] health=$health persists → dead server → restart" >> "$heal_log"
      if restart_server >> "$heal_log" 2>&1 && wait_ready; then
        echo "[$ts] recovered: dead-server restart + /ready GREEN" >> "$heal_log"
      else
        echo "[$ts] UNHEALED: restart failed or /ready timeout — needs a human" >> "$heal_log"
        [ -n "${NTFY_TOPIC:-}" ] && curl -s -H "Title: graphrag auto-heal" -d "$ts unhealed dead server" "ntfy.sh/$NTFY_TOPIC" >/dev/null 2>&1
      fi
      echo 0 > "$wedge_state"; return 0
    fi
    echo "[$ts] health recovered on 2nd check (transient)" >> "$heal_log"
  fi

  # skip probe while a rebuild is running (probing then = self-inflicted wedge alarms)
  local upd
  upd=$(curl -s -m 5 "$API/api/index/status" 2>/dev/null | python3 -c \
    "import json,sys
try: d=json.load(sys.stdin); print('busy' if d.get('update_in_progress') or (d.get('embedding_worker') or {}).get('phase')=='activating' else 'idle')
except Exception: print('idle')" 2>/dev/null || echo idle)
  if [ "$upd" = "busy" ]; then
    echo "[$ts] index update in progress → probe skipped this tick" >> "$heal_log"; return 0
  fi

  local wedge="" probe
  probe=$(curl -s -m 25 -o /tmp/tofugraph_probe.json -w '%{http_code}' \
    "$API/api/search?q=test&mode=hybrid&top_k=1" 2>/dev/null || echo ERR)
  if [ "$probe" != "200" ]; then wedge="probe_http=$probe"
  elif ! python3 -c "import json; d=json.load(open('/tmp/tofugraph_probe.json')); assert 'results' in d" 2>/dev/null; then
    wedge="probe_no_results_key"
  fi

  local count; count=$(cat "$wedge_state" 2>/dev/null || echo 0)
  if [ -n "$wedge" ]; then count=$((count+1)); else count=0; fi
  echo "$count" > "$wedge_state"
  if [ -n "$wedge" ] && [ "$count" -lt 2 ]; then
    echo "[$ts] wedge=$wedge (1st) → hold, need 2 consecutive" >> "$heal_log"; return 0
  fi
  if [ -n "$wedge" ]; then
    echo "[$ts] wedge=$wedge (x$count) → restart" >> "$heal_log"
    if restart_server >> "$heal_log" 2>&1 && wait_ready; then
      echo "[$ts] recovered: wedge restart + /ready GREEN" >> "$heal_log"
    else
      echo "[$ts] UNHEALED wedge — needs a human" >> "$heal_log"
      [ -n "${NTFY_TOPIC:-}" ] && curl -s -H "Title: graphrag auto-heal" -d "$ts unhealed wedge" "ntfy.sh/$NTFY_TOPIC" >/dev/null 2>&1
    fi
  fi
}

# ---------------------------------------------------------- install-daemon --
install_daemon() {
  local self; self=$(cd "$(dirname "$0")" && pwd)/$(basename "$0")
  if [[ "$OSTYPE" == darwin* ]]; then
    local plist="$HOME/Library/LaunchAgents/com.km.tofugraph-monitor.plist"
    cat > "$plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.km.tofugraph-monitor</string>
  <key>ProgramArguments</key><array>
    <string>/bin/bash</string><string>$self</string><string>monitor</string>
  </array>
  <key>EnvironmentVariables</key><dict>
    <key>GRAPHRAG_ROOT</key><string>${ROOT}</string>
    <key>GRAPHRAG_API_URL</key><string>${API}</string>
  </dict>
  <key>StartInterval</key><integer>3600</integer>
  <key>RunAtLoad</key><false/>
</dict></plist>
EOF
    launchctl unload "$plist" 2>/dev/null; launchctl load "$plist" \
      && echo "installed: hourly monitor (launchd com.km.tofugraph-monitor). uninstall: tofugraph.sh uninstall-daemon"
  else
    local line="0 * * * * GRAPHRAG_ROOT='$ROOT' GRAPHRAG_API_URL='$API' /bin/bash '$self' monitor"
    ( crontab -l 2>/dev/null | grep -v tofugraph ; echo "$line" ) | crontab - \
      && echo "installed: hourly monitor (crontab). uninstall: tofugraph.sh uninstall-daemon"
  fi
}

uninstall_daemon() {
  if [[ "$OSTYPE" == darwin* ]]; then
    local plist="$HOME/Library/LaunchAgents/com.km.tofugraph-monitor.plist"
    launchctl unload "$plist" 2>/dev/null; rm -f "$plist"; echo "removed launchd monitor"
  else
    crontab -l 2>/dev/null | grep -v tofugraph | crontab -; echo "removed crontab monitor"
  fi
}

# ---------------------------------------------------------- build / search --
delegate_engine() {
  # The GraphRAG engine (indexer/server) ships with ThisCode's vendor tree —
  # this adapter never bundles a second copy (single-source principle).
  local verb="$1"; shift
  if [ -n "$ROOT" ] && [ -f "$ROOT/scripts/cli.py" ]; then
    "$ROOT/.venv/bin/python3" "$ROOT/scripts/cli.py" "$verb" "$@"; return
  fi
  if [ -n "$ROOT" ] && [ -d "$ROOT/scripts" ]; then
    echo "engine found at $ROOT/scripts — run its documented build entry (see ThisCode docs/06-graphrag-setup.md)."
    return 0
  fi
  cat << 'EOF'
GraphRAG engine not installed yet. This adapter operates an engine; it doesn't bundle one.
Install once (public, keyless local-embedding default):
  git clone https://github.com/treylom/ThisCode && ThisCode/scripts/install-graphrag.sh
then re-run: tofugraph.sh build
EOF
  return 1
}

case "${1:-help}" in
  doctor)  doctor ;;
  status)  status ;;
  heal)    heal ;;
  monitor) monitor ;;
  install-daemon)   install_daemon ;;
  uninstall-daemon) uninstall_daemon ;;
  build)   shift; delegate_engine build "$@" ;;
  search)  shift; q="${1:-}"; [ -z "$q" ] && { echo "usage: tofugraph.sh search <query>"; exit 1; }
           curl -s -m 30 "$API/api/search?q=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$q")&mode=hybrid&top_k=5" \
             | python3 -m json.tool ;;
  *) echo "tofugraph — GraphRAG ops adapter"
     echo "usage: tofugraph.sh {doctor|status|heal|monitor|install-daemon|uninstall-daemon|build|search <q>}"
     echo "env: GRAPHRAG_ROOT, GRAPHRAG_API_URL, GRAPHRAG_SERVICE_LABEL, NTFY_TOPIC" ;;
esac
