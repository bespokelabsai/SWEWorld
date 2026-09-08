#!/bin/bash
# Launch one trial of one task variant and exit.
#
#   run.sh <group-dir> <variant-dir> <job-name> [model]
#
# OAuth only. Agent turns run on the subscription; ANTHROPIC_API_KEY lives in
# .env for phase-3 one-shots and must never reach an agent. Naming only
# CLAUDE_CODE_OAUTH_TOKEN in the config is NOT enough to achieve that — see the
# unset below the heredoc, which is what actually does it.
#
# Two guards, because this runs unattended overnight:
#
#   DISK  — a trial writes ~260MB (measured over the first eight). Below the
#           floor the run is refused rather than started, because harbor failing
#           on a full disk mid-trial looks exactly like an agent failure in the
#           results and would be scored as one.
#   SPEND — a hard ceiling on trials per night. Each is ~20 minutes and ~$9 of
#           subscription usage, and a loop that mistakes a stuck task for a
#           fixable one could otherwise run until morning on one requirement.
set -euo pipefail
cd /home/nidhi_bespokelabs_ai/SWEWorld
GROUP=$1; VARIANT=$2; JOB=$3
# Optional 4th arg: the model to run the agent on. Defaults to the model every
# number in state.json was measured with, so an omitted argument can never
# quietly change what a score means.
MODEL=${4:-anthropic/claude-opus-5}
LOOP=harbor_tasks/_loop
FLOOR_MB=2500
CAP=$(python3 -c "import json;print(json.load(open('$LOOP/state.json')).get('run_cap',35))")
# Every job directory, not a list of the arm names that existed when this was
# written. The clues and world arms were both invisible to the cap for as long
# as they existed, which is the opposite of what a spend guard is for.
#
# `run_cap` was rebased by hand when this widened, because the old glob matched
# 40 of 89 existing trials and the new one matches all 89 -- left alone, the
# change would have spent 49 trials of headroom on history. See state.json.
SPENT=$(ls -d jobs/*/ 2>/dev/null | wc -l)

FREE_MB=$(df -Pm / | awk 'NR==2{print $4}')
if [ "$FREE_MB" -lt "$FLOOR_MB" ]; then
  echo "REFUSED $JOB: ${FREE_MB}MB free, floor is ${FLOOR_MB}MB" | tee "/tmp/$JOB.refused"
  exit 3
fi
if [ "$SPENT" -ge "$CAP" ]; then
  echo "REFUSED $JOB: $SPENT trials already run, cap is $CAP" | tee "/tmp/$JOB.refused"
  exit 4
fi

CFG=$(mktemp /tmp/loopcfg-XXXX.yaml)
cat > "$CFG" <<YAML
n_concurrent_trials: 1
# Harbor's agent setup is `apt-get update && apt-get install curl procps`, then the
# Claude Code download, and it defaults to a 360s budget for all of it. The apt half
# is pure waste here -- curl and node are already in sweworld:0.4.4 -- but harbor
# runs it unconditionally, and archive.ubuntu.com is slow enough some nights to eat
# the whole budget on its own: two g6 trials in a row died at exactly 360s with the
# agent never started, while DNS, HTTPS and apt all worked fine when tested by hand.
# Tripling it costs nothing on a normal night (setup finishes in ~90s and the timer
# is never reached) and turns a class of phantom failure into a slow start.
agent_setup_timeout_multiplier: 3.0
agents:
  - name: claude-code
    model_name: $MODEL
    env:
      CLAUDE_CODE_OAUTH_TOKEN: \${CLAUDE_CODE_OAUTH_TOKEN}
      CLAUDE_FORCE_OAUTH: "1"
tasks:
  - path: harbor_tasks/$GROUP/$VARIANT
YAML
# .env carries ANTHROPIC_API_KEY for the phase-3 one-shots, and `set -a` exports
# it into harbor. Naming only CLAUDE_CODE_OAUTH_TOKEN in the config does NOT
# keep it away from the agent: harbor's claude-code adapter reads the key from
# its own environment and the CLI PREFERS it when both are set
# (agents/installed/claude_code.py — "API key and OAuth token both set; using
# the API key"). The first t12 trial ran that way, on the key, with the
# subscription token sitting unused beside it. Unset it here, and set harbor's
# own switch so the adapter drops it even if something else puts it back.
set -a; . ./.env; set +a
unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN
# A second subscription to spend from. The default account carries the session
# limit for interactive work, and a trial is 15-40 minutes of agent turns against
# the same quota -- so a day of measuring can lock the terminal out mid-task.
# Opt-in only: unset, this changes nothing, and the token still reaches the agent
# through the one variable the adapter reads.
if [ "${USE_PERSONAL_TOKEN:-0}" = "1" ]; then
  [ -n "${CLAUDE_CODE_PERSONAL_OAUTH_TOKEN:-}" ] || {
    echo "REFUSED $JOB: USE_PERSONAL_TOKEN=1 but CLAUDE_CODE_PERSONAL_OAUTH_TOKEN is not in .env" >&2; exit 5; }
  export CLAUDE_CODE_OAUTH_TOKEN="$CLAUDE_CODE_PERSONAL_OAUTH_TOKEN"
  echo "$JOB: running on the personal subscription token"
fi
export CLAUDE_FORCE_OAUTH=1
harbor run -c "$CFG" --job-name "$JOB" > "/tmp/$JOB.log" 2>&1
rc=$?
# Reclaim the trial's container and its writable layer. The env image is a thin
# layer over sweworld:repo-only-dev and costs almost nothing, so it is left.
docker container prune -f >/dev/null 2>&1 || true
exit $rc
