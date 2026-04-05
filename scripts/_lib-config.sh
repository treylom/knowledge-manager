#!/bin/bash
# _lib-config.sh — km-config.json parser using Node.js (no jq dependency)
# Sourced by other scripts. Not meant to be executed directly.

CONFIG_FILE="${CONFIG_FILE:-km-config.json}"

# Read a dot-path value from km-config.json.
# Usage: config_get "storage.obsidian.vaultPath" "/default/path"
config_get() {
  local path="$1"
  local default="${2:-}"
  node -e "
    try {
      const c = require('./$CONFIG_FILE');
      const parts = '$path'.split('.');
      let v = c;
      for (const p of parts) v = v == null ? undefined : v[p];
      console.log(v == null ? '$default' : v);
    } catch (e) {
      console.log('$default');
    }
  "
}

# Extract vault name (basename) from vault path.
# Usage: vault_name "/path/to/MyVault"
vault_name() {
  local vp="$1"
  node -e "
    const p = ('$vp').replace(/\\\\/g, '/').replace(/\/+\$/, '');
    const parts = p.split('/').filter(Boolean);
    console.log(parts[parts.length - 1] || 'MyVault');
  "
}

# Normalize path (Windows backslash → forward slash).
# Usage: path_normalize 'C:\Users\foo'
path_normalize() {
  node -e "console.log(('$1').replace(/\\\\/g, '/'))"
}
