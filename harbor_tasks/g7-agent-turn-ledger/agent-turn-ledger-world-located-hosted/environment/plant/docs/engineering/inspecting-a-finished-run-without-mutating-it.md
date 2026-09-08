---
title: "Inspecting a finished run without mutating it"
author: nikolai
created_at: 2025-06-11T09:30:00+00:00
---

## why this page exists

hit this on tuesday. opened a finished run dir to read token counters off it and the ledger file came back with a new mtime and a reordered tail. run was done, nothing should have touched it

turned out fine in the end but i spent a while assuming the run itself had written late, which it hadnt. writing down the read path here before someone builds tooling on top of it and inherits the same confusion

scope: what is safe to open on a completed run dir, and what is not

## what actually writes during a run

for reference, the writers are:

- the step loop, appends to the ledger log as steps retire
- the sidecar, written once at the end from whatever the loop had in memory
- the responses file, appended per response, never rewritten in place

all three are append or write-once. there is no compaction pass and no rewrite-on-close. so a run dir that has been marked finished is not supposed to change again

which is the whole reason the mtime change was surprising

## the read path

the thing i had wrong: the mutation was not the run, it was the tool i opened it with. our older inspect helper opened the dir in the same mode the loop uses, which normalizes the log on open. that is the rewrite

same goes for the responses file. i opened a finished run to look at counters and load rewrote it under me. `load_ledger` is read the log, rebuild, verify_sidecar, nothing written

so if you are reading counters, go through `load_ledger` and nothing else. it takes the run dir, reads the log forward, rebuilds the counter state in memory and hands it to `verify_sidecar` to check against what the run recorded. the return is the rebuilt state plus a mismatch list. no file handle is opened for write anywhere in that path

i'd say treat anything that opens a run dir in loop mode as a writer even if it looks like a reader

## checklist before you open a finished run

- use `load_ledger`, not the loop level open
- snapshot mtimes first if you are debugging something and want to be sure. cheap and it would have saved me the tuesday
- if `verify_sidecar` comes back with mismatches, that is a real finding, do not paper over it by regenerating the sidecar. the sidecar is the runs own claim, the rebuild is ours, they disagreeing is information
- never copy a run dir with a tool that dereferences and rewrites. tar it

## follow ups

- the old inspect helper should either be removed or made read only, i'd lean remove since `load_ledger` covers everything it did. havent opened an issue yet
- open question whether we want run dirs chmodded read only once finished. solid enough as an idea, but it interacts with cleanup and archival and i havent thought that through
- no change needed to the write path from any of this
