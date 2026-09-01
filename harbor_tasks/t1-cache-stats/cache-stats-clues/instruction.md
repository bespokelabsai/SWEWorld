You are an engineer at this company, working on `curator` — the Python library for bulk LLM inference and dataset curation that the company ships. You have an ordinary engineer's access and nothing more: no sudo, and no way to put code on a running service except through CI.

## The ticket

**Prompt-level response cache keying**

Add a `cache_stats()` method to `curator.LLM` that reports how many of the last run's requests were served from the local cache versus sent to the backend, so users can gauge how much a re-run will cost before running it.

## What the team said

Chat, the wiki and internal mail, over the months this area was being worked on, oldest first. Some of it is people thinking aloud and some of it was settled later.

<!-- planted 2026-08-24T21:12:42Z -->

**2024-11-26 · #code-review · dario**

> Worth writing down why the row hash is the right level for this. Keying on the row means resume and cache lookup need nothing but the dataset itself, no prompt callable, no live LLM object, so I can rebuild the whole hit/miss picture from the metadata DB on a cold process. That is exactly what cache_stats needs to be cheap. If the key depended on anything we can only compute by constructing the LLM, cache_stats stops being a thing you can call before a run and becomes another run.

**2024-11-27 · #engineering · dermot**

> To be clear on the cache key since it came up again in review: it is the hash of the raw input row, full stop. Row in, hash out, that is the whole contract and I want it to stay that narrow. Every time someone folds another thing into a fingerprint we end up with a key nobody can explain to a user who asks why their rerun did what it did. The row is the unit the dataset is made of, so the row is the unit the cache is keyed on. cache_stats should just report against those row hashes and nothing fancier.

**2024-12-09 · wiki: Bulk LLM Inference: next-phase design · dermot**

> Cache directory resolution lives in exactly one place in the caching layer and everything that needs the location calls it. I have deleted three hand-rolled path joins in review this quarter.

**2024-12-11 · wiki: Postmortem: Dec 10 revert of batch auto-delete · dermot**

> The counters we already keep per run are hits against the on-disk responses and requests that actually went out to the provider. Those are the same two numbers the summary table prints at the end.

**2024-12-16 · wiki: Runbook: handling curator.LLM incidents · dario**

> Putting this in the runbook because it keeps coming up: attaching extra metadata columns to a dataset for bookkeeping should come back free on the next run. It is the same set of requests going to the same place, nothing about the work changed.

**2025-01-14 · wiki: Postmortem: cache hashing regression revert on Jan 13 · dermot**

> For anyone new to this area: there is exactly one function that decides whether a row is reused or sent, and every processor calls it, online, batch and the local vLLM one.

**2025-01-28 · wiki: Prompt-level response cache keying · dario**

> Writing down what I think the sane behaviour is, because right now everyone's answer is rm -rf on the cache dir: if generation_params differ from the stored run, those rows should be going out to the provider again, and only those rows.

**2025-01-29 · #engineering · emil**

> RAFT emitted the same question against two chunk ids last night. Byte identical messages payload, I diffed them. Both went out as separate requests and both got billed. I would expect the second one to come straight back off disk since we already have that exact answer.

**2025-01-30 · #incidents · dermot**

> Every time I run a model sweep I end up exporting CURATOR_DISABLE_CACHE=1 for the whole thing, which then means the second and third models pay full price for the prompts I already have at that model.

**2025-02-03 · wiki: Handing off request-processing core and provider backends · dario**

> Triage note for cache questions: never believe a number a user pastes until you know the directory it came from. We ask for it on essentially every one of these tickets, and about half the time the user has switched shells or containers since their last run and does not realise there are two caches on the box.

**2025-02-06 · #pipeline · gideon**

> Recipes that construct their schema on the fly are never going to be reusable and I am fine with that. What I am not fine with is being worse off than someone who never had a cache at all. Those rows should just go to the provider and show up in the sent column at the end.

**2025-02-07 · #cookbooks · dario**

> Last summary table I looked at had reused plus sent coming to 900 short of the dataset length. I think those were the rows that errored mid flight and dropped out of both tallies. If the two numbers do not add up to the number of rows I processed, nobody is going to believe either of them, me included.

**2025-02-13 · #general · dario**

> burned an hour this morning on my little cache-poking script. It reports 12 hits out of 40k and I nearly re-budgeted the whole persona run on that. Turns out the script does os.path.expanduser("~/.cache/curator") and I have had CURATOR_CACHE_DIR=/mnt/scratch/curator-cache in my shell profile since June. The numbers were from a directory nothing has written to since October.

**2025-02-17 · #pipeline · gideon**

> people keep asking the same question before a re-run: how much of this is already on disk. Right now the only way to answer it is to run the thing and watch the hit counter go by on the progress bar, which is too late to decide anything.

**2025-02-19 · #engineering · dermot**

> Heads up, I added a source_url column to the persona input set purely for provenance. prompt() does not look at it. Entire 40k run went back out to the API and billed me again. I did not touch a single prompt.

**2025-02-20 · #viewer · gideon**

> The end of run table says cached: 12,403 and the first thing every single user asks is out of what. A bare count tells nobody whether their rerun is cheap. Give me a hit_rate I can print as a percentage next to it.

**2025-02-21 · #pipeline · gideon**

> We only ever assert on reuse counts in the online tests. The batch e2e checks the reassembled output and nothing else, which is exactly how the last regression rode out to a release. It bit me on the Azure batch run too.

**2025-02-21 · #help · dermot**

> the shared example cache on the box is mounted so only the nightly job can write to it, everybody else gets it as a read-only mount. Any script that opens the metadata sqlite the normal way dies with "attempt to write a readonly database" before it has read a single row, because sqlite wants to put a journal next to the file. Bit me twice trying to count entries.

**2025-02-24 · wiki: Structured output schema validation before dispatch · dario**

> Adding this to the troubleshooting page since it is the third report: if you edit your response_format between runs, either wipe the cache directory or set CURATOR_DISABLE_CACHE=1 first, otherwise you will get objects built to the previous schema.

**2025-02-24 · #engineering · emil**

> Added a confidence field to the response model on the ungrounded QA example, reran, and got back last week's objects with no confidence on them. Then the downstream validator threw on every row and I spent an hour looking at the validator.

**2025-02-25 · #releases · emil**

> same shape in the onboarding notebook. Cell two of the quickstart asks how much the run will cost, user has never generated anything, they get a traceback and file an issue saying curator is broken on their machine. Three of those in the last two weeks and all three were day-one installs.

**2025-02-26 · #pipeline · emil**

> related annoyance from the notebook walkthrough: people import curator in cell 1 and then set CURATOR_CACHE_DIR in cell 4 because that is the order the tutorial reads. The sizing helper I wrote grabs the path once when the module loads, so it kept telling them about the default directory for the rest of the session and I got two emails about it.

**2025-02-27 · #general · gideon**

> support thread from yesterday, three round trips. User pasted counts showing zero served locally, we were sure their re-run should have been almost free. I had to get them to echo their env, then ls two directories, before we worked out they had one cache from a docker session and another from their laptop shell. The counts on their own told me nothing.

**2025-02-28 · #help · gideon**

> Bumped temperature from 0 to 1.2 on the poem set to get some variety and got the identical 5k rows back. I spent an hour convinced vLLM was ignoring temperature before I worked out where they were coming from.

**2025-03-11 · #cookbooks · emil**

> SimpleStrat builds its response model at runtime with pydantic create_model, and the lookup pass dies on it: TypeError: unhashable type. Run is dead at row zero, before a single request goes out. Traceback in thread.

**2025-03-12 · #incidents · gideon**

> Nuking the whole cache dir every time I tweak one field is the main reason people here do not trust reruns. On a 200k set that is real money to get one extra field.

**2025-03-18 · #random · gideon**

> Lost most of yesterday to this. Swapped gpt-4o-mini for gpt-4o on the reannotation set, run finished in nine seconds, summary said everything came off disk. The outputs were the mini ones. I only noticed because the formatting was too sloppy for 4o.

**2025-03-21 · wiki: Batch job status persistence across process restarts · emil**

> House rule for anything that only reports on the cache: connect to the metadata db with mode=ro.

**2025-03-25 · #engineering · emil**

> Reminder for whoever touches the reuse pass: batch submission builds its jsonl off the same lookup, that is why when the online path stopped re-sending duplicates last month the batch path quietly stopped too.

**2025-03-26 · #help · dermot**

> I wrapped that call in a try/except locally to get the demo dataset out for the Friday cut and I have been carrying the patch since. Not shipping it, but I am also not deleting it, which tells you something.

**2025-03-31 · #code-review · dario**

> fresh CI container, nothing has ever run in it, and the pre-flight estimate step went red with FileNotFoundError on the cache directory. I put a mkdir -p in the workflow to get past it, which I hate, because now the estimate step is the thing that creates the cache. Second time this month.

**2025-04-17 · #random · gideon**

> self-inflicted, posting so nobody else does it. I typo'd the path in my cache-poking script last night, it did a mkdir -p on the way in, and this morning's cookbook run found a shiny empty cache directory at the typo, decided nothing was cached and re-sent 38k requests. Bill is real. The script only ever wanted to count rows.

**2025-04-18 · #engineering · emil**

> Same shape of thing with max_tokens for me. Response came back truncated mid sentence, I raised max_tokens, reran, got handed the truncated text again. Deleted the cache directory in the end, which also threw away four thousand rows that were perfectly fine.

**2025-04-28 · #viewer · emil**

> cheap fix for the support loop: whatever object these reporting calls hand back should carry the directory it looked at as a field, the way the end-of-run summary already prints the db path.

**2025-05-01 · wiki: Handing off status tracking, cost reporting & the viewer · gideon**

> For a machine with no history the truthful answer is that nothing is on disk and every request will go to the provider. That is a perfectly good number to report, all hits at zero and everything counted as going to the backend.

**2025-05-02 · wiki: Handing off status tracking, cost reporting & the viewer · emil**

> For the cost estimate in the cookbook I do not want a percentage I have to invert. I want misses as a plain int so I can multiply it by price per row and put a dollar figure in front of someone before they hit go.


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
