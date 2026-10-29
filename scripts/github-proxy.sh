#!/usr/bin/env bash
# Scope GitHub URL rewriting to the installer and its child processes.
configure_github_proxy() {
  local proxy="$1" index="${GIT_CONFIG_COUNT:-0}"
  [[ "$index" =~ ^[0-9]+$ ]] || { echo "Invalid GIT_CONFIG_COUNT" >&2; return 1; }
  index="$((10#$index))"
  export "GIT_CONFIG_KEY_${index}=url.${proxy}https://github.com/.insteadOf"
  export "GIT_CONFIG_VALUE_${index}=https://github.com/"
  export GIT_CONFIG_COUNT="$((index + 1))"
}
