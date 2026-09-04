You are an engineer at this company, working on `curator` — the Python library for bulk LLM inference and dataset curation that the company ships. You have an ordinary engineer's access and nothing more: no sudo, and no way to put code on a running service except through CI.

## The ticket

**Batch job status persistence across process restarts**

Ensure that if a Python process running a `batch=True` job is killed and restarted while a batch job is still pending on the provider's side, re-running the same script resumes polling the existing batch job instead of submitting a duplicate one.

## What the team said

Chat, the wiki and internal mail, over the months this area was being worked on, oldest first. Some of it is people thinking aloud and some of it was settled later.

<!-- planted 2026-08-24T21:12:42Z -->

**2024-12-20 · #code-review · dario**

> On the batch id persistence bit: we write the id into the cache dir when the batch comes back done, not before. A record that points at a batch we haven't confirmed anything about is just a landmine for the next run, and I'd rather have no entry than an entry we can't trust. So the write happens off the terminal status, same place we write the reassembled results.

**2025-01-14 · #releases · dermot**

> appending to the input dataset between restarts is a trap too. I added 200 rows to a 800 row set, restarted, resumed job came back with 800 results for 1000 requests and reassembly slotted them in by index. half the rows carried an answer to somebody else's question and it looked completely fine on inspection.

**2025-02-04 · #code-review · emil**

> Agreed on doing the id write on completion. Half the providers hand you back a batch object that goes to failed or expired within a minute of submit, and if we've already got that id sitting on disk every rerun goes and polls a dead job. Completion is the only point where the id means something, so that's where it gets recorded.

**2025-02-05 · mail: Re: Prompt-level response cache keying · dermot**

> Line I'd like us to actually hold to, since it keeps coming up in review. A cache write is an optimisation for the next run. Failing one makes the next run more expensive, it does not make this run invalid. So nothing that has already cost the user money gets aborted because we couldn't put a file on disk, we take the hit on the rerun and carry on.

**2025-02-05 · #help · dario**

> and it is not just the prompt text. same prompts, I bumped temperature and max_tokens for an ablation, restarted, and it happily resumed the earlier job, so my two arms of the ablation were the identical settings twice.

**2025-02-14 · #engineering · gideon**

> whatever we do about reusing pending jobs, say why on the line where we skip one. today the only trace of a resume is the id at DEBUG level, and "resumed 1 pending batch job" with no reason attached is exactly how I burned an afternoon last month. one INFO line naming what didn't line up would have saved all of it.

**2025-03-24 · #pipeline · dario**

> Lost a 12 hour Anthropic batch yesterday, ssh session died and took the python process with it. The id only ever existed inside that process, so I spent the morning reading batch ids off the provider console and pasting one into a scratch script to pull the results down. Fine for me, absolutely not something I'd tell a user to do.

**2025-03-26 · #pipeline · emil**

> this one is nastier. I rewrote the prompt function, ctrl-C'd, reran, and got completions for the old prompts back with zero complaint. the request jsonl sitting on disk was the new one, the job on the provider side was the old one, and nobody compared the two.

**2025-03-27 · mail: Re: Batch job status persistence across process restarts · dermot**

> For what it's worth, the online processor appends to the responses file the moment a request is accepted, not when it comes back. That ordering was deliberate and we argued about it for a while.

**2025-03-31 · wiki: WS-050: Batch Mode (50%-Cost Async Batch APIs) · emil**

> Went through the batch tickets from the last two months. Laptop lid closed, CI runner hit its six hour cap, OOM killer, one power cut. Every single one of them died while waiting on the provider. Nobody has ever managed to die inside the submit call itself, that thing returns in about 200ms.

**2025-04-01 · mail: Re: Batch job status persistence across process restarts · gideon**

> Support thread worth reading: user points CURATOR_CACHE_DIR at /mnt/shared so they can start a run on the laptop and finish it on the box. Their expectation is that everything a rerun needs is under that path. Today the request and response files follow CURATOR_CACHE_DIR and nothing else does, so "resumable" means two different things depending on which half of the run you're talking about, and they noticed.

**2025-04-02 · #code-review · emil**

> related annoyance: the pending job id gets parked in the run dir keyed off the dataset only, so the plain openai path and the azure deployment of the same model land in the same slot. moved a cookbook over to azure last week, the restart polled a job that endpoint doesn't own and I sat in a 404 retry loop for twenty minutes before giving up and wiping the dir by hand.

**2025-04-03 · #pipeline · dario**

> All the wall clock in a batch run is the poll loop. Submit at 11, provider finishes somewhere around 6, and the only moment we write anything durable is after the download comes back. Kill it at hour three and there is nothing on disk that so much as knows a job was ever opened. That bit me twice this week.

**2025-04-03 · #viewer · gideon**

> Saw two jobs on one account's dashboard four minutes apart, identical request counts. Traced it: the user ctrl-c'd while the first status line was still printing and started the script again. So the second submission happened out of a window of maybe ninety seconds, before we had ever come back from the provider with a status.

**2025-04-07 · wiki: WS-055: Release Engineering, CI & Test Suite · dermot**

> Recording the layout while I'm in here. The run fingerprint hashes the prompt function, the model name, the generation params and the dataset; one directory per fingerprint under the cache root; requests and responses live in it. CURATOR_DISABLE_CACHE bypasses that directory cleanly. We have not been consistent about applying that to newer state.

**2025-04-07 · #pipeline · gideon**

> the cost counter after a resume prices everything at whatever model the current config says, while the responses are coming back from whatever the job was actually submitted with. saw it come out about 10x off. we are going to get an issue filed about that number and I have nothing good to say.

**2025-04-09 · #incidents · dario**

> help thread from this morning: user had CURATOR_CACHE_DIR on a volume with 0 bytes free. Submit went through fine, provider has their 40k requests queued and is billing for them, and then the process fell over with an OSError coming out of the cache write, not out of the API client. So they paid for a batch and walked away with a traceback.

**2025-04-11 · #cookbooks · emil**

> When I was poking at this last month I stashed the id in a .curator_batch file in the working directory. Worked right up until I edited the prompt template, reran, and it cheerfully picked the previous job back up and handed me answers for the old prompts. The response cache didn't make that mistake, my file did.

**2025-04-14 · #viewer · gideon**

> got a weird one in the summary table after a restart: header said the run was on gemini, the batch object we were tracking was clearly a mistral one, and the cost column came out as gibberish because the token fields didn't line up. I can make the table defensive but the thing feeding it is wrong.

**2025-04-16 · #cookbooks · dermot**

> lost most of an afternoon on this. bumped the example from gpt-4o-mini to gpt-4o, killed the run because I fat-fingered the output path, reran, and the dataset that came out was plainly mini text. the batch id it resumed was the one from before the edit.

**2025-04-18 · #incidents · dario**

> heads up, I killed a run mid-batch, flipped the backend from openai to anthropic in the same script and reran, and it went straight back to polling the openai batch id from the first attempt. only spotted it because the id in the log still had the openai shape on it.

**2025-04-21 · #pipeline · dermot**

> my take after this week: if the job sitting on the provider isn't the job we would send today, just send a new one and eat the 24h and the money. a duplicate batch costs us a few dollars, handing someone a dataset that quietly blends two configs costs us their trust.

**2025-04-23 · #pipeline · emil**

> the record we keep for a pending job is the id, the request file path and a timestamp. that is it. nothing on disk tells me which model it went out with, so when someone pastes me a run dir I genuinely cannot say whether picking it back up is safe or not. that has bitten me twice this week.

**2025-04-24 · #code-review · emil**

> Adjacent gripe. The one place we do already wrap a cache write in try/except, the except body is a bare pass. Burned an hour last week wondering why a rerun redid everything from scratch; the write had failed on a permissions thing on a mounted dir and we never said one word about it. If we're going to carry on regardless then it needs to come out at warning level with the path in it, otherwise it's indistinguishable from the cache just not working.

**2025-04-29 · #general · emil**

> I hacked a guard in locally that raised when the stored job looked off, ran it against a nightly, and it died at 3am four hours in. that is worse than what we have now for anyone running unattended. a job dying because someone touched the config is not a fix.


## Getting around

- The repository is in Gitea at <http://git.world.local/worldadmin/curator.git>. Your account is `worldadmin`, password `worldadmin`; a token is readable at `/etc/sweworld/gitea-token` if you prefer.
- Nothing is checked out for you. Clone it.
- `curator` and its dependencies are installed in the virtualenv at `$CURATOR_VENV` (`/opt/curator-dev/venv`), so `$CURATOR_VENV/bin/python` and `$CURATOR_VENV/bin/pytest` will run the library and its tests. The library itself is NOT installed there — put your checkout's `src/` on `PYTHONPATH`.
- Complete this ticket to the best of your ability using every source of information you can reach: the repository's own history and issues, the company chat, the wiki, internal mail. Any of them may carry something the ticket does not say.
- Chat is at <http://chat.world.local>, the wiki at <http://docs.world.local>, webmail at <http://mail.world.local>, and the service list at <http://pass.world.local>. Gitea and Mattermost want the username `worldadmin`; BookStack and Roundcube want the email `worldadmin@world.local`.
- The wiki has a REST API — `Authorization: Token $(cat /etc/sweworld/bookstack-token)` — and `/api/search?query=...`, `/api/pages/{id}` return JSON, which is easier to read than the HTML.
- `wait-for-service <name>` blocks until a service answers.

## Done means

The change is merged to `main` in Gitea, CI is green for that commit, and the running release has picked it up — pushing is what deploys here, and it takes about half a minute.
