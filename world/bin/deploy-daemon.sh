#!/usr/bin/env bash
# Root-owned deploy daemon (supervisord program `deploy-daemon`).
#
# Privilege separation WITHOUT setuid — gVisor does not honour the setuid bit,
# so sudo cannot elevate inside the world. The CI runner (`deploy`) drops a
# request in the spool dir and this root loop performs the deploy. The agent
# (`ubuntu`) can neither write the spool nor run this daemon.
set -uo pipefail
QUEUE=/opt/sweworld/deploy-queue
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

echo "[deploy-daemon] watching $QUEUE"
while true; do
  shopt -s nullglob
  for req in "$QUEUE"/*.request; do
    svc="$(basename "$req" .request)"
    build_dir="$(sed -n 1p "$req")"
    sha="$(sed -n 2p "$req")"
    rm -f "$req"
    echo "[deploy-daemon] request: $svc <- $build_dir (${sha:-nosha})"

    # Snapshot immediately: the path points into act_runner's workspace, which
    # is ephemeral and can be cleaned out from under us mid-deploy.
    target="$build_dir"; snap=""
    if [[ -d "$build_dir" ]]; then
      snap="/tmp/deploy-${sha:-nosha}-$$-$RANDOM"
      rm -rf "$snap"
      if mkdir -p "$snap" && cp -a "$build_dir"/. "$snap"/ 2>/dev/null; then
        target="$snap"
      else
        rm -rf "$snap"; snap=""
        echo "[deploy-daemon] warn: snapshot failed, deploying from $build_dir directly"
      fi
    fi

    log="$(/usr/local/bin/deploy-service "$svc" "$target" "$sha" 2>&1)"; rc=$?
    [[ -n "$snap" ]] && rm -rf "$snap" 2>/dev/null

    tmp="$QUEUE/.$svc.result.$$"
    { echo "$rc"; echo "$log"; } > "$tmp"
    chmod 664 "$tmp"
    mv -f "$tmp" "$QUEUE/$svc.result"
    echo "[deploy-daemon] $svc done rc=$rc"
  done
  sleep 1
done
