# Phase 4: what the simulation is told

Four things reach a model: the channel scenario and briefing (which the DIRECTOR sees, to pick who speaks next), the shared ground (which EVERYONE in the channel holds), each person's own grounding, and the turn budget.

Worth keeping in mind while reading:

1. **This is today, not history.** Everyone is told the state as of that morning.
2. **MUST RAISE** belongs to the person driving it; the engine holds the conversation open until it lands. **MUST SETTLE** is a planted clue: the engine pushes for it to be stated as a conclusion, and a channel-day that does not get its INFORMATION across is run again — told what was missing. The words are the persona's own; what is fixed is the point, and any identifier named under it.
3. **The forbidden list does not exist yet** on that date. Naming it is the failure this whole pipeline is built to prevent.


==============================================================================
# 2025-02-07 — 5 conversation(s), 54 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Six open PRs pile up; three are old enough that they block downstream; releases just shipped, so review bandwidth is there

    Today is Friday 7 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Six open PRs pile up; three are old enough that they block downstream; releases just shipped, so review bandwidth is there
    
    What it should get through:
      1. unblock PR 430 and PR 460 by resolving logging strategy   [Dario Kestrel must raise this]
           - Dario Kestrel flags that PR 460 has been waiting since yesterday and examples are stale without it
           - Konrad Feltrin notes that readme examples also broke on empty responses and had to revert
           - Emil Brandvold pushes back: logging hooks need to land as a coherent piece, not half-baked; Dario Kestrel agrees to land PR 460 as-is in post5 if PR 430 stalls
      2. merge Emil Brandvold's three test PRs in order: PR 466 (raw prompt), PR 468 (n samples), PR 469 (GC)   [Emil Brandvold must raise this]
           - Emil Brandvold walks through the test payload changes across all three; Konrad Feltrin notes PR 466 is raw prompt so it doesn't block; Emil Brandvold wants PR 468 (n samples) next because it's part of the multimodal payload hardening
           - Priya Vandersloot: PR 468 will collide with my PR 443 on generation_params signature; Emil Brandvold: no, PR 443 adds per-row, PR 468 adds to the global LLM interface, they nest cleanly
           - Emil Brandvold: PR 469 is the GC leak from the test suite, should land alongside the version bump
      3. merge PR 443 (generation_params per row) once multimodal test suite lands   [Priya Vandersloot must raise this]
           - Priya Vandersloot: blocked for two days; the API is solid, reviews are done
           - Konrad Feltrin: once PR 468 lands we can merge PR 443 the same day, no collision
           - Emil Brandvold confirms: multimodal hardening is done, PR 468 will land today
    
    On the agenda: triage PR 362, PR 430, PR 443 — three stale opens, which land first; Emil Brandvold's three test PRs: PR 466, PR 468, PR 469 — order and blockers; Dario Kestrel's PR 473 typo and PR 430 OpenRouter examples — resolve logging question; Priya Vandersloot's PR 443 generation_params — when it's safe to merge
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 466, PR 468, PR 469 merge today; PR 430 gets a timeline (post5 or deferred); PR 443 unblocked for merge on Friday afternoon once PR 468 lands; PR 362 (Ilse Vandekerckhove's old json PR) and PR 460 (Dario Kestrel's logging) stay open but have clear owners and next steps
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 15 release(s) shipped, currently v0.1.18.post4
      - 236 changes merged to date

    On the table
      - announce-v0-1-18-post4 (Dermot Callaghan)
      - WS-028 design: Release Engineering, CI & Test Suite, round two (Dermot Callaghan)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 430: Reasoning with OpenRouter examples (Dario Kestrel)
      - PR 443: feat: added generation_params per row (Priya Vandersloot)
      - PR 460: logging (only log cost retrieval failure in debug) (Dario Kestrel)
      - PR 466: test: raw prompt as list of dict (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates

    DOES NOT EXIST YET (4 names)
      - agentic-curation
      - blocks-and-recipes
      - finetuning
      - — and 664 function/class names and 48 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. context on multimodal test hardening and the test payload changes across PR 466, PR 468, PR 469
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. unblock PR 430 and PR 460 by resolving logging strategy
      2. merge Emil Brandvold's three test PRs in order: PR 466 (raw prompt), PR 468 (n samples), PR 469 (GC)   *** MUST RAISE ***
      3. merge PR 443 (generation_params per row) once multimodal test suite lands
      4. what "WS-028 design: Release Engineering, CI & Test Suite, round two" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        merge Emil Brandvold's three test PRs in order: PR 466 (raw prompt), PR 468 (n samples), PR 469 (GC)
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. owns request-processing; context on PR 430 (OpenRouter examples) and PR 460 (logging)
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. unblock PR 430 and PR 460 by resolving logging strategy   *** MUST RAISE ***
      2. merge Emil Brandvold's three test PRs in order: PR 466 (raw prompt), PR 468 (n samples), PR 469 (GC)
      3. merge PR 443 (generation_params per row) once multimodal test suite lands
      4. what "v0.1.18.post4 hotfix is out" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        unblock PR 430 and PR 460 by resolving logging strategy
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. owns examples-cookbooks; context on what examples need and why PR 430 matters for docs
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. unblock PR 430 and PR 460 by resolving logging strategy
      2. merge Emil Brandvold's three test PRs in order: PR 466 (raw prompt), PR 468 (n samples), PR 469 (GC)
      3. merge PR 443 (generation_params per row) once multimodal test suite lands
    goal        Six open PRs pile up; three are old enough that they block downstream; releases just shipped, so review bandwidth is there
    available   around today

  Priya Vandersloot  (priya)
    role        Software Engineer, LLM Interface. owns multimodal-prompts; context on generation_params API
    owns        multimodal-prompts, release-and-ci
    agenda
      1. unblock PR 430 and PR 460 by resolving logging strategy
      2. merge Emil Brandvold's three test PRs in order: PR 466 (raw prompt), PR 468 (n samples), PR 469 (GC)
      3. merge PR 443 (generation_params per row) once multimodal test suite lands   *** MUST RAISE ***
    goal        merge PR 443 (generation_params per row) once multimodal test suite lands
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR 466, PR 468, PR 469 merge today; PR 430 gets a timeline (post5 or deferred); PR 443 unblocked for merge on Friday afternoon once PR 468 lands; PR 362 (Ilse Vandekerckhove's old json PR) and PR 460 (Dario Kestrel's logging) stay open but have clear owners and next steps


------------------------------------------------------------------------------
## #releases — 8 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #releases: v0.1.18.post4 shipped and needs documentation; release notes are due today; postmortem is being written

    Today is Friday 7 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: v0.1.18.post4 shipped and needs documentation; release notes are due today; postmortem is being written
    
    What it should get through:
      1. finalize release-v0-1-18-post4 notes covering GC leak, empty response fix, and inference.net   [Dermot Callaghan must raise this]
           - Dermot Callaghan: post4 is six commits: curator tag, Rich overlap fix, inference.net, empty response fix, version bump, GC fix
           - Emil Brandvold: the GC fix is the headline for users; it was leaking Live objects in test suites
           - Konrad Feltrin: inference.net addition should be called out so docs examples can use it
      2. announce post4 and link postmortem so the incident context is public   [Nikolai Berresford must raise this]
           - Nikolai Berresford: postmortem is done and explains the root cause (logging hook collision)
           - Dermot Callaghan: announce already went out; Nikolai Berresford should include the postmortem link in the release notes
           - Konrad Feltrin: users need to know this was a test-suite leak, not a runtime issue
    
    On the agenda: review what landed in post4 and draft the notes; link the postmortem so users understand the hotfix; check that the announce went out to the right list
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: release-v0-1-18-post4 doc is written and published; announce confirms the version is live; postmortem is linked so the incident context is available; users see the GC fix as the reason to upgrade
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 15 release(s) shipped, currently v0.1.18.post4
      - 236 changes merged to date

    On the table
      - Release notes: v0.1.18.post4 (Dermot Callaghan)
      - postmortem-2025-02-06 (Nikolai Berresford)
      - postmortem-2025-02-06 (Nikolai Berresford)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 430: Reasoning with OpenRouter examples (Dario Kestrel)
      - PR 443: feat: added generation_params per row (Priya Vandersloot)
      - PR 460: logging (only log cost retrieval failure in debug) (Dario Kestrel)
      - PR 466: test: raw prompt as list of dict (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates

    DOES NOT EXIST YET (4 names)
      - agentic-curation
      - blocks-and-recipes
      - finetuning
      - — and 664 function/class names and 48 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. shipped post2 and post4 today; owns the version bump cadence
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. finalize release-v0-1-18-post4 notes covering GC leak, empty response fix, and inference.net   *** MUST RAISE ***
      2. announce post4 and link postmortem so the incident context is public
      3. that the doc "Release notes: v0.1.18.post4" is done, and where the others can find it   *** MUST RAISE ***
      4. that "v0.1.18.post4 hotfix is out" has gone out, and what you asked in it   *** MUST RAISE ***
      5. what "Postmortem: provider-integrations example revert on Feb 6" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        finalize release-v0-1-18-post4 notes covering GC leak, empty response fix, and inference.net
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. owns release-and-ci; context on what each fix was for and which commits matter
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. finalize release-v0-1-18-post4 notes covering GC leak, empty response fix, and inference.net
      2. announce post4 and link postmortem so the incident context is public
    goal        v0.1.18.post4 shipped and needs documentation; release notes are due today; postmortem is being written
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. owns release-and-ci and telemetry; context on the incident that triggered post4
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. finalize release-v0-1-18-post4 notes covering GC leak, empty response fix, and inference.net
      2. announce post4 and link postmortem so the incident context is public   *** MUST RAISE ***
      3. that the doc "Postmortem: provider-integrations example revert on Feb 6" is done, and where the others can find it   *** MUST RAISE ***
      4. what "Postmortem: provider-integrations example revert on Feb 6" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        announce post4 and link postmortem so the incident context is public
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. owns examples-cookbooks; context on why inference.net landed in post4
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. finalize release-v0-1-18-post4 notes covering GC leak, empty response fix, and inference.net
      2. announce post4 and link postmortem so the incident context is public
    goal        v0.1.18.post4 shipped and needs documentation; release notes are due today; postmortem is being written
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   release-v0-1-18-post4 doc is written and published; announce confirms the version is live; postmortem is linked so the incident context is available; users see the GC fix as the reason to upgrade


------------------------------------------------------------------------------
## #pipeline — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: PR 463 landed to fix empty responses; examples had to revert yesterday; PR 470 opened asking to summarize request errors; need to settle the error-handling strategy before it cascades

    Today is Friday 7 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: PR 463 landed to fix empty responses; examples had to revert yesterday; PR 470 opened asking to summarize request errors; need to settle the error-handling strategy before it cascades
    
    What it should get through:
      1. confirm empty response fix handles nested structures and provider quirks   [Emil Brandvold must raise this]
           - Emil Brandvold: fix catches empty string and null at the top level; Gideon Halloway: what about empty arrays in structured output?
           - Dermot Callaghan: litellm had its own quirk where a failed request returns None instead of raising; that's in the fix now
           - Emil Brandvold: need to test against inference.net too since it's fresh and might have its own edge case
      2. close the loop on error handling: spam raw to terminal or summarize after retries exhaust   [Gideon Halloway must raise this]
           - Gideon Halloway: PR 470 asks for error summary, not raw log spam; users are annoyed by mid-run noise
           - Dermot Callaghan: we fixed the Rich overlap so errors don't stomp the bar anymore; maybe that was the real pain point
           - Emil Brandvold: if users are still complaining, we should batch errors and show a summary at the end; that's the multimodal hardening pattern
    
    On the agenda: walk through the empty response fix (PR 463) and edge cases; check that litellm examples don't break again; discuss whether to summarize errors or let them flow raw
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: empty response fix is confirmed solid; litellm examples stay merged; decision made on error summarization (likely: batch and show summary at end, defer raw spam config to post5); it is settled that the team agrees a bad model plus schema combination currently burns spend before anything surfaces
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 15 release(s) shipped, currently v0.1.18.post4
      - 236 changes merged to date

    On the table
      - announce-v0-1-18-post4 (Dermot Callaghan)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 430: Reasoning with OpenRouter examples (Dario Kestrel)
      - PR 443: feat: added generation_params per row (Priya Vandersloot)
      - PR 460: logging (only log cost retrieval failure in debug) (Dario Kestrel)
      - PR 466: test: raw prompt as list of dict (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates

    DOES NOT EXIST YET (4 names)
      - agentic-curation
      - blocks-and-recipes
      - finetuning
      - — and 664 function/class names and 48 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. shipped the empty response fix across two commits; owns the examples-cookbooks integration point
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. confirm empty response fix handles nested structures and provider quirks
      2. close the loop on error handling: spam raw to terminal or summarize after retries exhaust
      3. last night's cookbook run pushed somewhere around 9k requests before the provider started 400ing on the schema and the whole thing unwound. real money, zero usable rows. finding out what our own request can't do from someone else's error response is not a great place to be   *** MUST SETTLE (clue t2.r1.L8) ***
    goal        the team agrees a bad model plus schema combination currently burns spend before anything surfaces
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. driving multimodal test hardening; context on what empty responses mean for parsing and structured output
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. confirm empty response fix handles nested structures and provider quirks   *** MUST RAISE ***
      2. close the loop on error handling: spam raw to terminal or summarize after retries exhaust
      3. what "v0.1.18.post4 hotfix is out" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        confirm empty response fix handles nested structures and provider quirks
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. owns progress-and-cli and run observability; context on what users see when a response is empty
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. confirm empty response fix handles nested structures and provider quirks
      2. close the loop on error handling: spam raw to terminal or summarize after retries exhaust   *** MUST RAISE ***
    goal        close the loop on error handling: spam raw to terminal or summarize after retries exhaust
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   empty response fix is confirmed solid; litellm examples stay merged; decision made on error summarization (likely: batch and show summary at end, defer raw spam config to post5); it is settled that the team agrees a bad model plus schema combination currently burns spend before anything surfaces


------------------------------------------------------------------------------
## #engineering — 10 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Friday wrap; five workstreams at mid-flight; two patch releases shipped; three days of fast commits; team needs to agree on what's done and what continues

    Today is Friday 7 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Friday wrap; five workstreams at mid-flight; two patch releases shipped; three days of fast commits; team needs to agree on what's done and what continues
    
    What it should get through:
      1. confirm GC leak and empty response fixes are final; ws-028 (release hardening) can ease off   [Emil Brandvold must raise this]
           - Emil Brandvold: multimodal test GC leak is fixed in post4; rich Live objects are properly disposed now
           - Nikolai Berresford: postmortem is done; we know the root cause and it won't happen again
           - Konrad Feltrin: examples are stable; the revert was a one-time pain; going forward the fix holds
      2. ws-024, ws-025, ws-026, ws-027 continue at mid-flight; pick Monday's focus   [Konrad Feltrin must raise this]
           - Konrad Feltrin: examples cleanup is nearly done; inference.net is in; we can close ws-024 after one more pass on docs
           - Emil Brandvold: multimodal support is solid in the core; next is hardening the cost maps for non-standard providers, that's ws-025 still
           - Dermot Callaghan: request processing is clean; error handling is next, that's Gideon Halloway's territory and it's in ws-026
    
    On the agenda: recap week: two patch releases, multimodal hardening, provider breadth; check which workstreams close and which continue; plan Monday: what's the next big work after Stratos Crunch
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: team agrees that the hotfix cycle is done; ws-024 will close; ws-025, ws-026, ws-027 continue; Monday plan is clear: error handling polish and cost map hardening; team feels the week was productive and the patch train worked
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 15 release(s) shipped, currently v0.1.18.post4
      - 236 changes merged to date

    On the table
      - postmortem-2025-02-06 (Nikolai Berresford)
      - release-v0-1-18-post4 (Dermot Callaghan)
      - Weekly sync notes: week of Feb 3 — v0.1.18 and v0.1.18.post4 shipped (Emil Brandvold)
      - WS-028 design: Release Engineering, CI & Test Suite, round two (Dermot Callaghan)
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 430: Reasoning with OpenRouter examples (Dario Kestrel)
      - PR 443: feat: added generation_params per row (Priya Vandersloot)
      - PR 460: logging (only log cost retrieval failure in debug) (Dario Kestrel)
      - PR 466: test: raw prompt as list of dict (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates

    DOES NOT EXIST YET (4 names)
      - agentic-curation
      - blocks-and-recipes
      - finetuning
      - — and 664 function/class names and 48 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. drove four workstreams to mid-flight; context on multimodal hardening, provider breadth, and release cadence
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. confirm GC leak and empty response fixes are final; ws-028 (release hardening) can ease off   *** MUST RAISE ***
      2. ws-024, ws-025, ws-026, ws-027 continue at mid-flight; pick Monday's focus
      3. what "Postmortem: provider-integrations example revert on Feb 6" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      4. what "Release notes: v0.1.18.post4" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      5. what "Weekly sync notes: week of Feb 3 — v0.1.18 and v0.1.18.post4 shipped" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        confirm GC leak and empty response fixes are final; ws-028 (release hardening) can ease off
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. shipped two patch releases; owns examples-cookbooks; context on docs pain points
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. confirm GC leak and empty response fixes are final; ws-028 (release hardening) can ease off
      2. ws-024, ws-025, ws-026, ws-027 continue at mid-flight; pick Monday's focus
    goal        Friday wrap; five workstreams at mid-flight; two patch releases shipped; three days of fast commits; team needs to agree on what's done and what continues
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. owns examples-cookbooks; context on what examples need and what docs are out of sync
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. confirm GC leak and empty response fixes are final; ws-028 (release hardening) can ease off
      2. ws-024, ws-025, ws-026, ws-027 continue at mid-flight; pick Monday's focus   *** MUST RAISE ***
      3. what "WS-028 design: Release Engineering, CI & Test Suite, round two" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        ws-024, ws-025, ws-026, ws-027 continue at mid-flight; pick Monday's focus
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. owns code-execution and release-and-ci; context on test stability and release process
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. confirm GC leak and empty response fixes are final; ws-028 (release hardening) can ease off
      2. ws-024, ws-025, ws-026, ws-027 continue at mid-flight; pick Monday's focus
    goal        Friday wrap; five workstreams at mid-flight; two patch releases shipped; three days of fast commits; team needs to agree on what's done and what continues
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   team agrees that the hotfix cycle is done; ws-024 will close; ws-025, ws-026, ws-027 continue; Monday plan is clear: error handling polish and cost map hardening; team feels the week was productive and the patch train worked


------------------------------------------------------------------------------
## #cookbooks — 14 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #cookbooks: The published examples are where users will first see these counts, so the numbers need to be defensible there

    Today is Friday 7 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: The published examples are where users will first see these counts, so the numbers need to be defensible there
    
    What it should get through:
    
    On the agenda: Emil Brandvold flags that persona-hub carries a solid chunk of literally identical prompts, they get collapsed into one call, and the end-of-run count comes out lower than the dataset length; people keep filing that as data loss, and he says the repeats should land on the served-from-disk side of the tally rather than quietly disappearing; Dario Kestrel describes adding one field to the response_format model on the RAFT block, rerunning, and getting rows back without the field, then spending an hour blaming the structured-output parser; Dermot Callaghan asks whether the cookbooks should print cache_stats() at the end of each script; no decision
    
    Wrap when: Emil Brandvold files the duplicate-accounting issue; the response_format problem is acknowledged and unowned; it is settled that the team agrees the reuse and send figures must reconcile with the number of processed rows
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 15 release(s) shipped, currently v0.1.18.post4
      - 236 changes merged to date

    On the table
      - PR 362: Fix_json adds curly braces (Ilse Vandekerckhove)
      - PR 430: Reasoning with OpenRouter examples (Dario Kestrel)
      - PR 443: feat: added generation_params per row (Priya Vandersloot)
      - PR 460: logging (only log cost retrieval failure in debug) (Dario Kestrel)
      - PR 466: test: raw prompt as list of dict (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates

    DOES NOT EXIST YET (4 names)
      - agentic-curation
      - blocks-and-recipes
      - finetuning
      - — and 664 function/class names and 48 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. 
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
    goal        The published examples are where users will first see these counts, so the numbers need to be defensible there
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Last summary table I looked at had reused plus sent coming to 900 short of the dataset length. I think those were the rows that errored mid flight and dropped out of both tallies. If the two numbers do not add up to the number of rows I processed, nobody is going to believe either of them, me included.   *** MUST SETTLE (clue t1.r1.l_stats_3) ***
    goal        the team agrees the reuse and send figures must reconcile with the number of processed rows
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. 
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
    goal        The published examples are where users will first see these counts, so the numbers need to be defensible there
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Emil Brandvold files the duplicate-accounting issue; the response_format problem is acknowledged and unowned; it is settled that the team agrees the reuse and send figures must reconcile with the number of processed rows


==============================================================================
# 2025-02-10 — 2 conversation(s), 18 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Manual cost maps land today; Dario Kestrel and Emil Brandvold need alignment on provider edge cases

    Today is Monday 10 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Manual cost maps land today; Dario Kestrel and Emil Brandvold need alignment on provider edge cases
    
    What it should get through:
      1. Approve or request changes on PR PR 481   [Dario Kestrel must raise this]
           - Emil Brandvold walks through the manual cost-map design
           - Dario Kestrel flags any missing validation or test scenarios
           - decision to merge or iterate
    
    On the agenda: Review PR PR 481 scope and test coverage; Cost-map validation and edge cases; Integration with existing provider backends
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR PR 481 reviewed and either merged or sent back with clear next steps
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 15 release(s) shipped, currently v0.1.18.post4
      - 243 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 477: Fix/local url/file (Emil Brandvold)
      - PR 481: feat: support manual cost map (Emil Brandvold)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates

    DOES NOT EXIST YET (4 names)
      - agentic-curation
      - blocks-and-recipes
      - finetuning
      - — and 655 function/class names and 45 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Manual cost-map implementation for non-standard providers
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Approve or request changes on PR PR 481
    goal        Manual cost maps land today; Dario Kestrel and Emil Brandvold need alignment on provider edge cases
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Request-processing context and provider API knowledge
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Approve or request changes on PR PR 481   *** MUST RAISE ***
    goal        Approve or request changes on PR PR 481
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR PR 481 reviewed and either merged or sent back with clear next steps


------------------------------------------------------------------------------
## #engineering — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Emil landed 4 commits over the weekend including a revert; team needs to know what changed and why

    Today is Monday 10 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Emil landed 4 commits over the weekend including a revert; team needs to know what changed and why
    
    What it should get through:
      1. Align on pickler strategy and fallback approach   [Emil Brandvold must raise this]
           - Emil Brandvold explains what broke in recursive pickling
           - Dario Kestrel and Dermot Callaghan ask about impact on existing code
           - decision: is dill fallback temporary or the new default
      2. Review scope of manual cost-map feature   [Emil Brandvold must raise this]
           - Emil Brandvold walks through cost-map design and test coverage
           - Dario Kestrel confirms it integrates cleanly with provider backends
           - green light or feedback for code-review
    
    On the agenda: Summary of pickler issues and revert; Cache-timing test and what it covers; Manual cost-map feature and scope
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team understands what landed, why the pickler was reverted, and whether cost-map PR is ready to merge
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 15 release(s) shipped, currently v0.1.18.post4
      - 243 changes merged to date

    On the table
      - weekly-2025-02-03 (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 477: Fix/local url/file (Emil Brandvold)
      - PR 481: feat: support manual cost map (Emil Brandvold)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates

    DOES NOT EXIST YET (4 names)
      - agentic-curation
      - blocks-and-recipes
      - finetuning
      - — and 655 function/class names and 45 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Details on pickler revert, cache-timing test, and cost-map feature
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Align on pickler strategy and fallback approach   *** MUST RAISE ***
      2. Review scope of manual cost-map feature   *** MUST RAISE ***
      3. that "Weekly update: week of Feb 3 — v0.1.18 and v0.1.18.post4 shipped" has gone out, and what you asked in it   *** MUST RAISE ***
      4. that the doc "WS-033 design: Code Execution & Verifiers" is done, and where the others can find it   *** MUST RAISE ***
      5. that the doc "Postmortem: v0.1.18.post4 hotfix" is done, and where the others can find it   *** MUST RAISE ***
    goal        Align on pickler strategy and fallback approach
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Eyes on request-layer changes and provider integration concerns
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Align on pickler strategy and fallback approach
      2. Review scope of manual cost-map feature
    goal        Emil landed 4 commits over the weekend including a revert; team needs to know what changed and why
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Integration context for multimodal changes
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Align on pickler strategy and fallback approach
      2. Review scope of manual cost-map feature
    goal        Emil landed 4 commits over the weekend including a revert; team needs to know what changed and why
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team understands what landed, why the pickler was reverted, and whether cost-map PR is ready to merge


==============================================================================
# 2025-02-11 — 4 conversation(s), 40 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 5 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Two PRs opened today, one stale PR needs attention, test and merge decisions needed fast.

    Today is Tuesday 11 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two PRs opened today, one stale PR needs attention, test and merge decisions needed fast.
    
    What it should get through:
      1. Land PR 491 (curator-viewer client) or surface blocking concerns   [Emil Brandvold must raise this]
           - Emil explains the client surface and why it was split out
           - Dermot spots if the interface layer breaks multimodal or cost accounting paths
           - Group decides: merge as-is, request changes, or land pending follow-up
      2. Approve PR 490 (TogetherAI ratelimit refactor) or defer behind cost-map work   [Emil Brandvold must raise this]
           - Emil flags what changed in the rate-limit handling
           - Dario checks if batch-mode or online request processing surface is affected
           - Group: land, or wait until PR 481 (cost-map) stabilizes
      3. Decide on PR 468 (n-samples): land now, pull forward in scope, or defer to next cycle   [Emil Brandvold must raise this]
           - Emil states what's blocking it and what's left to review
           - Group weighs if it should merge behind a flag, or if it should wait for cost-map fix to land first
           - Land or defer
    
    On the agenda: PR 491: Curator viewer client — shape and scope; PR 490: RateLimit refactor for TogetherAI — impact check; PR 468: n-samples support — unblock decision
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 491 merged or with clear path forward; PR 490 approved or deferred; PR 468 unblocked or explicitly pushed to next batch.
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 15 release(s) shipped, currently v0.1.18.post4
      - 244 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 481: feat: support manual cost map (Emil Brandvold)
      - PR 490: Ref/ratelimit/togetherai (Emil Brandvold)
      - PR 491: Feat/curator/client (Emil Brandvold)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates

    DOES NOT EXIST YET (4 names)
      - agentic-curation
      - blocks-and-recipes
      - finetuning
      - — and 654 function/class names and 43 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Three active workstreams in flight: bulk-llm-inference multimodal hardening, test/patch train work, and batch backend stabilization. Can explain what each PR closes and what's still pending.
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Land PR 491 (curator-viewer client) or surface blocking concerns   *** MUST RAISE ***
      2. Approve PR 490 (TogetherAI ratelimit refactor) or defer behind cost-map work   *** MUST RAISE ***
      3. Decide on PR 468 (n-samples): land now, pull forward in scope, or defer to next cycle   *** MUST RAISE ***
    goal        Land PR 491 (curator-viewer client) or surface blocking concerns
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Fresh eyes on the curator-viewer client work (PR 491); owns bulk-llm-inference and multimodal-prompts so can spot integration issues.
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Land PR 491 (curator-viewer client) or surface blocking concerns
      2. Approve PR 490 (TogetherAI ratelimit refactor) or defer behind cost-map work
      3. Decide on PR 468 (n-samples): land now, pull forward in scope, or defer to next cycle
    goal        Two PRs opened today, one stale PR needs attention, test and merge decisions needed fast.
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Just landed code-execution tests and fixed an example. Can flag if PR 490 or PR 491 touch his surface.
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Land PR 491 (curator-viewer client) or surface blocking concerns
      2. Approve PR 490 (TogetherAI ratelimit refactor) or defer behind cost-map work
      3. Decide on PR 468 (n-samples): land now, pull forward in scope, or defer to next cycle
    goal        Two PRs opened today, one stale PR needs attention, test and merge decisions needed fast.
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Owns request processing core and online request handling. Can spot if batch or provider integration changes have downstream impact.
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Land PR 491 (curator-viewer client) or surface blocking concerns
      2. Approve PR 490 (TogetherAI ratelimit refactor) or defer behind cost-map work
      3. Decide on PR 468 (n-samples): land now, pull forward in scope, or defer to next cycle
    goal        Two PRs opened today, one stale PR needs attention, test and merge decisions needed fast.
    available   around today

  Priya Vandersloot  (priya)
    role        Software Engineer, LLM Interface. Multimodal interface owner. Can flag if the curator-viewer client PR respects the multimodal-prompts API shape.
    owns        multimodal-prompts, release-and-ci
    agenda
      1. Land PR 491 (curator-viewer client) or surface blocking concerns
      2. Approve PR 490 (TogetherAI ratelimit refactor) or defer behind cost-map work
      3. Decide on PR 468 (n-samples): land now, pull forward in scope, or defer to next cycle
    goal        Two PRs opened today, one stale PR needs attention, test and merge decisions needed fast.
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR 491 merged or with clear path forward; PR 490 approved or deferred; PR 468 unblocked or explicitly pushed to next batch.


------------------------------------------------------------------------------
## #pipeline — 10 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Two active cost-related workstreams (batch-mode Gemini fix, bulk-llm-inference cost-map hardening) and a new client PR touching the LLM interface.

    Today is Tuesday 11 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two active cost-related workstreams (batch-mode Gemini fix, bulk-llm-inference cost-map hardening) and a new client PR touching the LLM interface.
    
    What it should get through:
      1. Confirm batch-mode Gemini cost fix closes the request-counting gap and doesn't regress other backends   [Emil Brandvold must raise this]
           - Emil explains the Gemini batch processor bug (undercounting or overcounting against max-requests-per-batch)
           - Dario and Gideon flag if other batch backends (e.g. Anthropic, Azure) are affected
           - Group confirms the fix is scoped to Gemini or is backend-agnostic; lands or defers
      2. Document manual cost-map work and ensure it doesn't override automated cost paths unexpectedly   [Emil Brandvold must raise this]
           - Emil explains cost-map PR PR 481 shape and when it overrides automated costs
           - Dermot checks if it breaks cost accounting for multimodal or structured prompts
           - Confirm: does it merge today or wait for batch-mode fix to land first?
      3. Validate that curator-viewer client PR PR 491 doesn't change the request-processing contract   [Emil Brandvold must raise this]
           - Emil walks through the client API shape
           - Dario and Gideon confirm the request submission and status-polling paths are unchanged
           - Land or surface concerns before merge
    
    On the agenda: Batch-mode cost counting: Gemini request-per-batch fix and its scope; Manual cost-map work: shape and interaction with automated cost paths; Curator-viewer client: does it change the request-processing contract?
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Batch-mode Gemini fix confirmed as safe or deferred; cost-map work signed off or deferred pending batch-mode stability; curator-viewer client either merged or identified as needing changes.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 15 release(s) shipped, currently v0.1.18.post4
      - 244 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 481: feat: support manual cost map (Emil Brandvold)
      - PR 490: Ref/ratelimit/togetherai (Emil Brandvold)
      - PR 491: Feat/curator/client (Emil Brandvold)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates

    DOES NOT EXIST YET (4 names)
      - agentic-curation
      - blocks-and-recipes
      - finetuning
      - — and 654 function/class names and 43 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Three active workstreams: bulk-llm-inference cost-map hardening, batch-mode stabilization (Gemini request-count fix), and PR PR 491 (curator-viewer client touching the LLM interface). Can explain what each does and where they intersect.
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm batch-mode Gemini cost fix closes the request-counting gap and doesn't regress other backends   *** MUST RAISE ***
      2. Document manual cost-map work and ensure it doesn't override automated cost paths unexpectedly   *** MUST RAISE ***
      3. Validate that curator-viewer client PR PR 491 doesn't change the request-processing contract   *** MUST RAISE ***
    goal        Confirm batch-mode Gemini cost fix closes the request-counting gap and doesn't regress other backends
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Bulk-llm-inference owner. Can flag if multimodal or cost-accounting changes in flight will break the existing cost paths or provider backends.
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm batch-mode Gemini cost fix closes the request-counting gap and doesn't regress other backends
      2. Document manual cost-map work and ensure it doesn't override automated cost paths unexpectedly
      3. Validate that curator-viewer client PR PR 491 doesn't change the request-processing contract
    goal        Two active cost-related workstreams (batch-mode Gemini fix, bulk-llm-inference cost-map hardening) and a new client PR touching the LLM interface.
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Batch and online request processing owner. Knows which backends batch-mode supports and which ones have cost-counting bugs.
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm batch-mode Gemini cost fix closes the request-counting gap and doesn't regress other backends
      2. Document manual cost-map work and ensure it doesn't override automated cost paths unexpectedly
      3. Validate that curator-viewer client PR PR 491 doesn't change the request-processing contract
    goal        Two active cost-related workstreams (batch-mode Gemini fix, bulk-llm-inference cost-map hardening) and a new client PR touching the LLM interface.
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Observability and progress tracking. Can spot if cost-accounting changes will break the run-summary or cost-counter display.
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm batch-mode Gemini cost fix closes the request-counting gap and doesn't regress other backends
      2. Document manual cost-map work and ensure it doesn't override automated cost paths unexpectedly
      3. Validate that curator-viewer client PR PR 491 doesn't change the request-processing contract
    goal        Two active cost-related workstreams (batch-mode Gemini fix, bulk-llm-inference cost-map hardening) and a new client PR touching the LLM interface.
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Batch-mode Gemini fix confirmed as safe or deferred; cost-map work signed off or deferred pending batch-mode stability; curator-viewer client either merged or identified as needing changes.


------------------------------------------------------------------------------
## #cookbooks — 8 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #cookbooks: Two commits landed today in code-execution and examples-cookbooks; tests and a fix need validation.

    Today is Tuesday 11 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two commits landed today in code-execution and examples-cookbooks; tests and a fix need validation.
    
    What it should get through:
      1. Validate code-execution tests cover the verifier API properly and align with published recipes   [Nikolai Berresford must raise this]
           - Nikolai explains what the new tests cover (e.g., does it exercise the code sandbox? the structured return? the failure modes?)
           - Konrad and Dermot confirm the surface matches the reasoning-dataset pipeline expectations
           - Land or request coverage additions
      2. Assess code-execution example fix and decide if it should roll into published cookbooks   [Nikolai Berresford must raise this]
           - Nikolai describes the example break and the fix
           - Konrad and Dario decide: is this a one-off example-dir fix, or should it update the published RAFT/reasoning-dataset recipe?
           - Land or defer to next cookbook publish
    
    On the agenda: Code-execution tests: coverage and API surface; Example fix: scope and cookbook impact
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Code-execution tests approved and merged; example fix landed with scope decision made (one-off or cookbook rollout); it is settled that the team agrees the executor currently pulls a moving image and this has repeatedly broken CI
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 15 release(s) shipped, currently v0.1.18.post4
      - 244 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 481: feat: support manual cost map (Emil Brandvold)
      - PR 490: Ref/ratelimit/togetherai (Emil Brandvold)
      - PR 491: Feat/curator/client (Emil Brandvold)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates

    DOES NOT EXIST YET (4 names)
      - agentic-curation
      - blocks-and-recipes
      - finetuning
      - — and 654 function/class names and 43 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Just added tests to code-execution and fixed an example in that service. Knows what the code-execution API surface is and where the example was broken.
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Validate code-execution tests cover the verifier API properly and align with published recipes   *** MUST RAISE ***
      2. Assess code-execution example fix and decide if it should roll into published cookbooks   *** MUST RAISE ***
    goal        Validate code-execution tests cover the verifier API properly and align with published recipes
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Founding maintainer. Knows the reasoning-dataset handoff story and the code-execution verifier use case. Can spot if Nikolai Berresford's changes align with the published cookbook recipes.
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Validate code-execution tests cover the verifier API properly and align with published recipes
      2. Assess code-execution example fix and decide if it should roll into published cookbooks
    goal        Two commits landed today in code-execution and examples-cookbooks; tests and a fix need validation.
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Examples-cookbooks owner. Can flag if Nikolai Berresford's example fix should be surfaced in the published cookbooks or if it's a one-off fix.
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Validate code-execution tests cover the verifier API properly and align with published recipes
      2. Assess code-execution example fix and decide if it should roll into published cookbooks
      3. CI died overnight again on the code execution job and nothing changed on our side. The container the executor pulled has a different digest than the one Monday's run used. Third time this month I have rerun a red build and had it go green by itself. I am tired of it.   *** MUST SETTLE (clue t4.r1.L7) ***
    goal        the team agrees the executor currently pulls a moving image and this has repeatedly broken CI
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Also owns the examples side. Can confirm if the code-execution example fix should roll into the RAFT or other reasoning-dataset recipes.
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Validate code-execution tests cover the verifier API properly and align with published recipes
      2. Assess code-execution example fix and decide if it should roll into published cookbooks
    goal        Two commits landed today in code-execution and examples-cookbooks; tests and a fix need validation.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Code-execution tests approved and merged; example fix landed with scope decision made (one-off or cookbook rollout); it is settled that the team agrees the executor currently pulls a moving image and this has repeatedly broken CI


------------------------------------------------------------------------------
## #engineering — 10 turns, 5 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Three active mid-flight workstreams; test hardening, batch-mode stabilization, and multimodal cost-map work in parallel; postmortem due today.

    Today is Tuesday 11 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Three active mid-flight workstreams; test hardening, batch-mode stabilization, and multimodal cost-map work in parallel; postmortem due today.
    
    What it should get through:
      1. Broadcast patch-train status: pdf fixture, local url/file fix, pickler revert postmortem due, and what's next   [Emil Brandvold must raise this]
           - Emil and Nikolai Berresford walk through today's fixes (pdf fixture for CI, local url/file patch)
           - Emil flags the pickler revert postmortem due today — explains why the initial change didn't stick
           - Group confirms: are these patches for the next post5, or are they waiting for batch-mode/cost-map to stabilize first?
      2. Surface batch-mode Gemini cost fix and cost-map manual-entry work; confirm they don't conflict   [Emil Brandvold must raise this]
           - Emil explains batch-mode Gemini request-counting bug and the fix landing today
           - Emil explains cost-map PR PR 481 shape and why it's needed
           - Group confirms: do they ship together, or does batch-mode fix land first? Does cost-map work land behind a flag?
      3. Announce curator-viewer client PR PR 491 and gather early feedback on the interface   [Emil Brandvold must raise this]
           - Emil walks through the client API: does it feel right? Does it break any existing code paths?
           - Priya confirms multimodal-prompts API is untouched
           - Group: is this landing today or waiting for feedback in code-review?
    
    On the agenda: Patch train: what shipped in the last 24h and what's still in flight; Batch-mode and cost-map: current state and interaction; Curator-viewer client: shape and readiness
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team is aligned on what's in flight (patch-train, batch-mode cost fix, cost-map, curator-viewer client), dependencies are flagged, and postmortem is due.
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 15 release(s) shipped, currently v0.1.18.post4
      - 244 changes merged to date

    On the table
      - Postmortem: pickler revert on Feb 10 (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 481: feat: support manual cost map (Emil Brandvold)
      - PR 490: Ref/ratelimit/togetherai (Emil Brandvold)
      - PR 491: Feat/curator/client (Emil Brandvold)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates

    DOES NOT EXIST YET (4 names)
      - agentic-curation
      - blocks-and-recipes
      - finetuning
      - — and 654 function/class names and 43 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Three active mid-flight workstreams: bulk-llm-inference cost-map hardening (handling Gemini batch cost bugs, manual cost-map entry), test and patch train (pdf fixture, local url/file fix, pickler revert postmortem due today), and curator-viewer client work. Can explain the current state and what landed today.
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Broadcast patch-train status: pdf fixture, local url/file fix, pickler revert postmortem due, and what's next   *** MUST RAISE ***
      2. Surface batch-mode Gemini cost fix and cost-map manual-entry work; confirm they don't conflict   *** MUST RAISE ***
      3. Announce curator-viewer client PR PR 491 and gather early feedback on the interface   *** MUST RAISE ***
      4. that the doc "Postmortem: pickler revert on Feb 10" is done, and where the others can find it   *** MUST RAISE ***
    goal        Broadcast patch-train status: pdf fixture, local url/file fix, pickler revert postmortem due, and what's next
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Just landed code-execution tests and example fixes. Helping with the patch-train workstream. Can report what stabilization landed today.
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Broadcast patch-train status: pdf fixture, local url/file fix, pickler revert postmortem due, and what's next
      2. Surface batch-mode Gemini cost fix and cost-map manual-entry work; confirm they don't conflict
      3. Announce curator-viewer client PR PR 491 and gather early feedback on the interface
    goal        Three active mid-flight workstreams; test hardening, batch-mode stabilization, and multimodal cost-map work in parallel; postmortem due today.
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Senior engineer. Can validate that the cost-map and batch-mode work doesn't break existing bulk-llm-inference paths. Reviewed today's PRs.
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Broadcast patch-train status: pdf fixture, local url/file fix, pickler revert postmortem due, and what's next
      2. Surface batch-mode Gemini cost fix and cost-map manual-entry work; confirm they don't conflict
      3. Announce curator-viewer client PR PR 491 and gather early feedback on the interface
    goal        Three active mid-flight workstreams; test hardening, batch-mode stabilization, and multimodal cost-map work in parallel; postmortem due today.
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Request-processing owner. Can flag if batch-mode or curator-viewer client changes affect online request handling.
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Broadcast patch-train status: pdf fixture, local url/file fix, pickler revert postmortem due, and what's next
      2. Surface batch-mode Gemini cost fix and cost-map manual-entry work; confirm they don't conflict
      3. Announce curator-viewer client PR PR 491 and gather early feedback on the interface
    goal        Three active mid-flight workstreams; test hardening, batch-mode stabilization, and multimodal cost-map work in parallel; postmortem due today.
    available   around today

  Priya Vandersloot  (priya)
    role        Software Engineer, LLM Interface. Multimodal interface owner. Can confirm the cost-map and client changes respect the multimodal-prompts API.
    owns        multimodal-prompts, release-and-ci
    agenda
      1. Broadcast patch-train status: pdf fixture, local url/file fix, pickler revert postmortem due, and what's next
      2. Surface batch-mode Gemini cost fix and cost-map manual-entry work; confirm they don't conflict
      3. Announce curator-viewer client PR PR 491 and gather early feedback on the interface
    goal        Three active mid-flight workstreams; test hardening, batch-mode stabilization, and multimodal cost-map work in parallel; postmortem due today.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team is aligned on what's in flight (patch-train, batch-mode cost fix, cost-map, curator-viewer client), dependencies are flagged, and postmortem is due.


==============================================================================
# 2025-02-12 — 3 conversation(s), 36 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 6 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Three opened, eight reviewed; one PR stale five days. Emil driving two workstreams. Gideon shipped two merges already.

    Today is Wednesday 12 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Three opened, eight reviewed; one PR stale five days. Emil driving two workstreams. Gideon shipped two merges already.
    
    What it should get through:
      1. Get PR 493 and PR 496 past final review   [Gideon Halloway must raise this]
           - Gideon Halloway describes the emoji and progress bar changes
           - Dario Kestrel or Dermot Callaghan flags anything that breaks the CLI surface
           - both ship if no blockers
      2. Unblock PR 490 and PR 491 for landing tomorrow   [Emil Brandvold must raise this]
           - Emil Brandvold says what PR 490 needs (togetherai ratelimit fix) and PR 491 needs (curator client async)
           - Dario Kestrel asks whether test coverage is enough
           - both mark as ready-to-land if tests pass
      3. Decide whether PR 468 (five days old) is worth keeping or should close   [Dario Kestrel must raise this]
           - Dario Kestrel or Emil Brandvold flags it as blocked or deprioritized
           - either merges if tests pass or closes the ticket
    
    On the agenda: PR 493 and PR 496 shipping, PR 495 ready to merge; PR 490 and PR 491 status — what's blocking them; PR 468 five days old — is it still worth holding
    
    Meeting today: Weekly sync
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 493, PR 496 merge today. PR 490, PR 491 marked ready-to-land. Either PR 468 lands or gets closed.
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 15 release(s) shipped, currently v0.1.18.post4
      - 246 changes merged to date

    On the table
      - Postmortem: pickler revert on Feb 10 (Emil Brandvold)
      - Handover doc: Request-processing core and provider backends, Dario Kestrel to Emil Brandvold (Dario Kestrel)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 490: Ref/ratelimit/togetherai (Emil Brandvold)
      - PR 491: Feat/curator/client (Emil Brandvold)
      - PR 493: Revamp CLI progress bar UI (Gideon Halloway)
      - PR 495: Code executor enhancements + tests (Nikolai Berresford)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates

    DOES NOT EXIST YET (4 names)
      - agentic-curation
      - blocks-and-recipes
      - finetuning
      - — and 653 function/class names and 43 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Seven commits across request processing and cost map hardening; knows what's blocking downstream
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Get PR 493 and PR 496 past final review
      2. Unblock PR 490 and PR 491 for landing tomorrow   *** MUST RAISE ***
      3. Decide whether PR 468 (five days old) is worth keeping or should close
      4. what "Handover doc: Request-processing core and provider backends, dario to emil" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Unblock PR 490 and PR 491 for landing tomorrow
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. New progress bar UI and batch status tracker; knows the CLI surface
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Get PR 493 and PR 496 past final review   *** MUST RAISE ***
      2. Unblock PR 490 and PR 491 for landing tomorrow
      3. Decide whether PR 468 (five days old) is worth keeping or should close
      4. what "Postmortem: pickler revert on Feb 10" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Get PR 493 and PR 496 past final review
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Code executor test suite and enhancements; owns the verifier path
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Get PR 493 and PR 496 past final review
      2. Unblock PR 490 and PR 491 for landing tomorrow
      3. Decide whether PR 468 (five days old) is worth keeping or should close
    goal        Three opened, eight reviewed; one PR stale five days. Emil driving two workstreams. Gideon shipped two merges already.
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Request-processing ownership; two approvals already on PR 481 and PR 490
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Get PR 493 and PR 496 past final review
      2. Unblock PR 490 and PR 491 for landing tomorrow
      3. Decide whether PR 468 (five days old) is worth keeping or should close   *** MUST RAISE ***
    goal        Decide whether PR 468 (five days old) is worth keeping or should close
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Release engineering and test suite ownership
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Get PR 493 and PR 496 past final review
      2. Unblock PR 490 and PR 491 for landing tomorrow
      3. Decide whether PR 468 (five days old) is worth keeping or should close
    goal        Three opened, eight reviewed; one PR stale five days. Emil driving two workstreams. Gideon shipped two merges already.
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Context on which examples are stale and which providers still matter
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Get PR 493 and PR 496 past final review
      2. Unblock PR 490 and PR 491 for landing tomorrow
      3. Decide whether PR 468 (five days old) is worth keeping or should close
    goal        Three opened, eight reviewed; one PR stale five days. Emil driving two workstreams. Gideon shipped two merges already.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 493, PR 496 merge today. PR 490, PR 491 marked ready-to-land. Either PR 468 lands or gets closed.


------------------------------------------------------------------------------
## #engineering — 14 turns, 6 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: 21 commits, 2 merged. Three workstreams mid-flight. Emil writing week summary.

    Today is Wednesday 12 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 21 commits, 2 merged. Three workstreams mid-flight. Emil writing week summary.
    
    What it should get through:
      1. Capture the week (pickler revert, hotfix, cost maps) in notes-2025-02-10   [Emil Brandvold must raise this]
           - Emil Brandvold walks through what went wrong Tuesday and what was reverted
           - Dario Kestrel or Nikolai Berresford confirms the incident count
           - everyone agrees what the dominant work was
      2. Confirm multimodal and cost-map work is stable enough to release next week   [Emil Brandvold must raise this]
           - Emil Brandvold lists what's in PR 490, PR 491, and PR 468
           - Dario Kestrel flags whether any are blockers for the next cut
           - Konrad Feltrin asks whether examples need updating
      3. Design debt: either ship or defer the progress bar emoji   [Gideon Halloway must raise this]
           - Gideon Halloway shows the new UI
           - someone asks whether the emoji helps or hurts
           - either ship PR 493 or roll it back
    
    On the agenda: Week summary: pickler revert, 66 commits, three merges, one incident; Cost maps and multimodal hardening — what's still blocked; Progress bar and batch status UI — what's next; Code executor tests and verifiers — design doc coverage
    
    Meeting today: Weekly sync
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Week summary written. Multimodal and cost-map work confirmed stable. Progress bar shipped or deferred. No design surprises left.
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 15 release(s) shipped, currently v0.1.18.post4
      - 246 changes merged to date

    On the table
      - Weekly sync notes: week of Feb 10 — pickler regression (Emil Brandvold)
      - Postmortem: pickler revert on Feb 10 (Emil Brandvold)
      - Handover doc: Request-processing core and provider backends, Dario Kestrel to Emil Brandvold (Dario Kestrel)
      - WS-033 design: Code Execution & Verifiers (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 490: Ref/ratelimit/togetherai (Emil Brandvold)
      - PR 491: Feat/curator/client (Emil Brandvold)
      - PR 493: Revamp CLI progress bar UI (Gideon Halloway)
      - PR 495: Code executor enhancements + tests (Nikolai Berresford)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates

    DOES NOT EXIST YET (4 names)
      - agentic-curation
      - blocks-and-recipes
      - finetuning
      - — and 653 function/class names and 43 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Seven commits; week's work dominated by reverts and hardening; owns the cost-map and multimodal surface
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Capture the week (pickler revert, hotfix, cost maps) in notes-2025-02-10   *** MUST RAISE ***
      2. Confirm multimodal and cost-map work is stable enough to release next week   *** MUST RAISE ***
      3. Design debt: either ship or defer the progress bar emoji
      4. that the doc "Weekly sync notes: week of Feb 10 — pickler regression" is done, and where the others can find it   *** MUST RAISE ***
      5. what "Postmortem: pickler revert on Feb 10" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      6. what "Handover doc: Request-processing core and provider backends, dario to emil" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      7. what "WS-033 design: Code Execution & Verifiers" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Capture the week (pickler revert, hotfix, cost maps) in notes-2025-02-10
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Ten commits on progress bar and batch status UI; knows which observability gaps remain
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Capture the week (pickler revert, hotfix, cost maps) in notes-2025-02-10
      2. Confirm multimodal and cost-map work is stable enough to release next week
      3. Design debt: either ship or defer the progress bar emoji   *** MUST RAISE ***
    goal        Design debt: either ship or defer the progress bar emoji
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Code executor tests and enhancements; knows what the design doc promised
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Capture the week (pickler revert, hotfix, cost maps) in notes-2025-02-10
      2. Confirm multimodal and cost-map work is stable enough to release next week
      3. Design debt: either ship or defer the progress bar emoji
    goal        21 commits, 2 merged. Three workstreams mid-flight. Emil writing week summary.
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Request-processing ownership; two approvals on PR 481
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Capture the week (pickler revert, hotfix, cost maps) in notes-2025-02-10
      2. Confirm multimodal and cost-map work is stable enough to release next week
      3. Design debt: either ship or defer the progress bar emoji
    goal        21 commits, 2 merged. Three workstreams mid-flight. Emil writing week summary.
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Release engineering view; spotted the post4 hotfix
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Capture the week (pickler revert, hotfix, cost maps) in notes-2025-02-10
      2. Confirm multimodal and cost-map work is stable enough to release next week
      3. Design debt: either ship or defer the progress bar emoji
    goal        21 commits, 2 merged. Three workstreams mid-flight. Emil writing week summary.
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Provider and example context; knows which docs are stale
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Capture the week (pickler revert, hotfix, cost maps) in notes-2025-02-10
      2. Confirm multimodal and cost-map work is stable enough to release next week
      3. Design debt: either ship or defer the progress bar emoji
    goal        21 commits, 2 merged. Three workstreams mid-flight. Emil writing week summary.
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Week summary written. Multimodal and cost-map work confirmed stable. Progress bar shipped or deferred. No design surprises left.


------------------------------------------------------------------------------
## #pipeline — 10 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: 11 changes to online-request-processing. 7 to provider-integrations. 6 each to bulk-llm-inference and caching-and-resume. Emil driving both workstreams.

    Today is Wednesday 12 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 11 changes to online-request-processing. 7 to provider-integrations. 6 each to bulk-llm-inference and caching-and-resume. Emil driving both workstreams.
    
    What it should get through:
      1. Confirm cost-map PR PR 481 is safe and ready to ship   [Emil Brandvold must raise this]
           - Emil Brandvold describes what the config validator checks
           - Dario Kestrel flags whether the manual cost map can mis-bind providers
           - either ship or ask for changes
      2. Surface any unsafe patterns in the request-processing commits before they compound   [Dario Kestrel must raise this]
           - Gideon Halloway asks about the status-update plumbing in the async client
           - Emil Brandvold explains what parse_func failure means
           - Dario Kestrel flags whether skip logic needs keyword-only args
      3. Plan whether to harden cost-map fallbacks this week or defer   [Emil Brandvold must raise this]
           - Emil Brandvold describes what breaks if a provider has no cost_map
           - Dario Kestrel asks whether it should error or use a default
           - either ship the fallback or doc it as a known gap
    
    On the agenda: Cost-map config validator and the manual cost-map PR PR 481; Cost map edge cases — what still needs hardening; Curator viewer async client and status-update plumbing; Request processing internals — kwargs binding, parse failures, skip logic
    
    Meeting today: Weekly sync
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Cost-map PR confirmed safe. Any unsafe request-processing patterns flagged. Cost-map fallback plan set.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 15 release(s) shipped, currently v0.1.18.post4
      - 246 changes merged to date

    On the table
      - Handover doc: Request-processing core and provider backends, Dario Kestrel to Emil Brandvold (Dario Kestrel)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 490: Ref/ratelimit/togetherai (Emil Brandvold)
      - PR 491: Feat/curator/client (Emil Brandvold)
      - PR 493: Revamp CLI progress bar UI (Gideon Halloway)
      - PR 495: Code executor enhancements + tests (Nikolai Berresford)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates

    DOES NOT EXIST YET (4 names)
      - agentic-curation
      - blocks-and-recipes
      - finetuning
      - — and 653 function/class names and 43 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Seven commits across request-processing, cost-map config, and curator-viewer async. Knows what the config validator did. Knows what's still unsafe.
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm cost-map PR PR 481 is safe and ready to ship   *** MUST RAISE ***
      2. Surface any unsafe patterns in the request-processing commits before they compound
      3. Plan whether to harden cost-map fallbacks this week or defer   *** MUST RAISE ***
      4. what "Handover doc: Request-processing core and provider backends, dario to emil" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm cost-map PR PR 481 is safe and ready to ship
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Ten commits on progress bar and batch status. Knows what metrics are exposed. Knows which status transitions are still noisy.
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm cost-map PR PR 481 is safe and ready to ship
      2. Surface any unsafe patterns in the request-processing commits before they compound
      3. Plan whether to harden cost-map fallbacks this week or defer
    goal        11 changes to online-request-processing. 7 to provider-integrations. 6 each to bulk-llm-inference and caching-and-resume. Emil driving both workstreams.
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Request-processing ownership. Approved cost-map PR PR 481. Knows what can break in the request layer.
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm cost-map PR PR 481 is safe and ready to ship
      2. Surface any unsafe patterns in the request-processing commits before they compound   *** MUST RAISE ***
      3. Plan whether to harden cost-map fallbacks this week or defer
    goal        Surface any unsafe patterns in the request-processing commits before they compound
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Release engineering view. Knows what hotfixes we shipped last week.
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm cost-map PR PR 481 is safe and ready to ship
      2. Surface any unsafe patterns in the request-processing commits before they compound
      3. Plan whether to harden cost-map fallbacks this week or defer
    goal        11 changes to online-request-processing. 7 to provider-integrations. 6 each to bulk-llm-inference and caching-and-resume. Emil driving both workstreams.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Cost-map PR confirmed safe. Any unsafe request-processing patterns flagged. Cost-map fallback plan set.


==============================================================================
# 2025-02-13 — 4 conversation(s), 44 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 6 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Four PRs merged today; one batch-mode fix landed, then a follow-up on request counting; README cleanup and badge refresh; all reviewed by today end-of-day

    Today is Thursday 13 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Four PRs merged today; one batch-mode fix landed, then a follow-up on request counting; README cleanup and badge refresh; all reviewed by today end-of-day
    
    What it should get through:
      1. Confirm batch request counting is correct, not regressing again   [Emil Brandvold must raise this]
           - Emil flags the gemini-fix followed immediately by refetch patch
           - Dermot cross-checks the logic against the provider spec
           - Gideon asks if the UI change affects error logging
      2. Ship README refresh and provider links cleanup   [Dario Kestrel must raise this]
           - Dario ships the badges and docs refresh
           - Konrad confirms provider links are current
    
    On the agenda: Batch status tracker and Gemini processor fixes land; README and badge updates merge; Serialization refactoring holds up under review
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Four PRs ship cleanly; batch counting confidence restored; README reflects current state and provider landscape. No blockers remain on the fixes.
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 15 release(s) shipped, currently v0.1.18.post4
      - 251 changes merged to date

    On the table
      - Postmortem: pickler revert on Feb 10 (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 493: Revamp CLI progress bar UI (Gideon Halloway)
      - PR 495: Code executor enhancements + tests (Nikolai Berresford)
      - PR 501: Update badges (Dario Kestrel)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates

    DOES NOT EXIST YET (4 names)
      - agentic-curation
      - blocks-and-recipes
      - finetuning
      - — and 641 function/class names and 42 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. The batch tracker and Gemini processor fixes that close the gap on request counting; the refactored serialization layer that lets batch state survive across runs
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm batch request counting is correct, not regressing again   *** MUST RAISE ***
      2. Ship README refresh and provider links cleanup
      3. what "Postmortem: pickler revert on Feb 10" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm batch request counting is correct, not regressing again
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Production logging and URL fixes; has reviewed all four merged PRs
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm batch request counting is correct, not regressing again
      2. Ship README refresh and provider links cleanup
    goal        Four PRs merged today; one batch-mode fix landed, then a follow-up on request counting; README cleanup and badge refresh; all reviewed by today end-of-day
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. README and badge updates that reflect current state
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm batch request counting is correct, not regressing again
      2. Ship README refresh and provider links cleanup   *** MUST RAISE ***
    goal        Ship README refresh and provider links cleanup
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Progress bar width fix; visibility into whether the UI changes interfere with error output
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm batch request counting is correct, not regressing again
      2. Ship README refresh and provider links cleanup
    goal        Four PRs merged today; one batch-mode fix landed, then a follow-up on request counting; README cleanup and badge refresh; all reviewed by today end-of-day
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Provider link accuracy; examples that actually run
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm batch request counting is correct, not regressing again
      2. Ship README refresh and provider links cleanup
    goal        Four PRs merged today; one batch-mode fix landed, then a follow-up on request counting; README cleanup and badge refresh; all reviewed by today end-of-day
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Test coverage on the batch tracker serialization
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Confirm batch request counting is correct, not regressing again
      2. Ship README refresh and provider links cleanup
    goal        Four PRs merged today; one batch-mode fix landed, then a follow-up on request counting; README cleanup and badge refresh; all reviewed by today end-of-day
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Four PRs ship cleanly; batch counting confidence restored; README reflects current state and provider landscape. No blockers remain on the fixes.


------------------------------------------------------------------------------
## #engineering — 12 turns, 7 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Twenty-three commits and five merges ship today; four workstreams in mid-flight to landing state; wrap-up on multimodal support and batch stabilization before post5 decision

    Today is Thursday 13 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Twenty-three commits and five merges ship today; four workstreams in mid-flight to landing state; wrap-up on multimodal support and batch stabilization before post5 decision
    
    What it should get through:
      1. Confirm multimodal support and batch mode are landing cleanly with no regressions   [Emil Brandvold must raise this]
           - Emil recaps the batch counting fix and curator client merge
           - Gideon flags progress bar interaction and gets patched-in-post5 commitment
           - Dermot confirms logging and cost paths are solid
      2. Close out CLI observability work without error spam regressions   [Gideon Halloway must raise this]
           - Gideon surfaces the full-width bar and asks if error output needs gating
           - Emil confirms error handling strategy for post5
      3. Test coverage and examples are shipped with the landing   [Nikolai Berresford must raise this]
           - Nikolai confirms batch tracker tests are in
           - Dario notes README examples pass
           - Konrad confirms provider links are fresh
    
    On the agenda: Multimodal and batch mode landing status; Progress bar and CLI observability; Test coverage and example cleanup
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team confirms multimodal and batch mode landing is stable; cli observability improvement ships; decision point on post5 timing reached. No outstanding blockers on the sprint wrap-up.
    
    Do NOT wrap before about 10 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 15 release(s) shipped, currently v0.1.18.post4
      - 251 changes merged to date

    On the table
      - Weekly sync notes: week of Feb 10 — pickler regression (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 493: Revamp CLI progress bar UI (Gideon Halloway)
      - PR 495: Code executor enhancements + tests (Nikolai Berresford)
      - PR 501: Update badges (Dario Kestrel)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates

    DOES NOT EXIST YET (4 names)
      - agentic-curation
      - blocks-and-recipes
      - finetuning
      - — and 641 function/class names and 42 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Eleven commits shipping today across batch mode, rate limits, and serialization; curator client and batch tracker refactors; ratelimit for TogetherAI landing
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm multimodal support and batch mode are landing cleanly with no regressions   *** MUST RAISE ***
      2. Close out CLI observability work without error spam regressions
      3. Test coverage and examples are shipped with the landing
      4. what "Weekly sync notes: week of Feb 10 — pickler regression" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm multimodal support and batch mode are landing cleanly with no regressions
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Full-width progress bar rendering; owns the CLI observability side
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm multimodal support and batch mode are landing cleanly with no regressions
      2. Close out CLI observability work without error spam regressions   *** MUST RAISE ***
      3. Test coverage and examples are shipped with the landing
    goal        Close out CLI observability work without error spam regressions
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Test coverage and code execution enhancements; unblocking ws-033
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Confirm multimodal support and batch mode are landing cleanly with no regressions
      2. Close out CLI observability work without error spam regressions
      3. Test coverage and examples are shipped with the landing   *** MUST RAISE ***
    goal        Test coverage and examples are shipped with the landing
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Production logging and URL fixes; holds the release view
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm multimodal support and batch mode are landing cleanly with no regressions
      2. Close out CLI observability work without error spam regressions
      3. Test coverage and examples are shipped with the landing
    goal        Twenty-three commits and five merges ship today; four workstreams in mid-flight to landing state; wrap-up on multimodal support and batch stabilization before post5 decision
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. README and example cleanup
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm multimodal support and batch mode are landing cleanly with no regressions
      2. Close out CLI observability work without error spam regressions
      3. Test coverage and examples are shipped with the landing
    goal        Twenty-three commits and five merges ship today; four workstreams in mid-flight to landing state; wrap-up on multimodal support and batch stabilization before post5 decision
    available   around today

  Priya Vandersloot  (priya)
    role        Software Engineer, LLM Interface. Multimodal prompt handling confidence
    owns        multimodal-prompts, release-and-ci
    agenda
      1. Confirm multimodal support and batch mode are landing cleanly with no regressions
      2. Close out CLI observability work without error spam regressions
      3. Test coverage and examples are shipped with the landing
    goal        Twenty-three commits and five merges ship today; four workstreams in mid-flight to landing state; wrap-up on multimodal support and batch stabilization before post5 decision
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Provider breadth and example accuracy
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm multimodal support and batch mode are landing cleanly with no regressions
      2. Close out CLI observability work without error spam regressions
      3. Test coverage and examples are shipped with the landing
    goal        Twenty-three commits and five merges ship today; four workstreams in mid-flight to landing state; wrap-up on multimodal support and batch stabilization before post5 decision
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Team confirms multimodal and batch mode landing is stable; cli observability improvement ships; decision point on post5 timing reached. No outstanding blockers on the sprint wrap-up.


------------------------------------------------------------------------------
## #pipeline — 10 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Twelve changes to online-request-processing, ten to provider-integrations, eight to bulk-llm-inference; batch mode and rate limit work landing; need confirmation on correctness before post5

    Today is Thursday 13 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Twelve changes to online-request-processing, ten to provider-integrations, eight to bulk-llm-inference; batch mode and rate limit work landing; need confirmation on correctness before post5
    
    What it should get through:
      1. Confirm Gemini batch processor request counting is correct and won't regress   [Emil Brandvold must raise this]
           - Emil walks through the first fix and the refetch patch
           - Dermot asks how this interacts with retries
           - Gideon notes if progress bar accounting matches
      2. Rate limit and provider integration changes don't break existing backends   [Emil Brandvold must raise this]
           - Emil recaps TogetherAI rate limit ref
           - Gideon confirms no timeout side effects
           - Dermot checks prod behavior
      3. Cost accounting path from request submission to completion is solid   [Dermot Callaghan must raise this]
           - Dermot flags the logging additions and where they touch cost tracking
           - Emil confirms batch tracker telemetry won't double-count
           - Gideon checks if progress bar cost estimates match
    
    On the agenda: Batch processing request counting accuracy; Rate limit ref and provider integration stability; Cost accounting and telemetry path from request to completion
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Batch mode counting verified correct; rate limit handling stable; cost accounting path confirmed end-to-end. Post5 release decision can proceed.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 15 release(s) shipped, currently v0.1.18.post4
      - 251 changes merged to date

    On the table
      - Postmortem: pickler revert on Feb 10 (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 493: Revamp CLI progress bar UI (Gideon Halloway)
      - PR 495: Code executor enhancements + tests (Nikolai Berresford)
      - PR 501: Update badges (Dario Kestrel)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates

    DOES NOT EXIST YET (4 names)
      - agentic-curation
      - blocks-and-recipes
      - finetuning
      - — and 641 function/class names and 42 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Gemini batch processor fix for request counting; TogetherAI rate limit ref; batch tracker telemetry and serialization; multimodal safety handling in the request layer
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm Gemini batch processor request counting is correct and won't regress   *** MUST RAISE ***
      2. Rate limit and provider integration changes don't break existing backends   *** MUST RAISE ***
      3. Cost accounting path from request submission to completion is solid
      4. what "Postmortem: pickler revert on Feb 10" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm Gemini batch processor request counting is correct and won't regress
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Progress bar integration with request tracking; can spot if concurrency tuning is off
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm Gemini batch processor request counting is correct and won't regress
      2. Rate limit and provider integration changes don't break existing backends
      3. Cost accounting path from request submission to completion is solid
    goal        Twelve changes to online-request-processing, ten to provider-integrations, eight to bulk-llm-inference; batch mode and rate limit work landing; need confirmation on correctness before post5
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Production URL and logging fixes; reviewed the batch fixes
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm Gemini batch processor request counting is correct and won't regress
      2. Rate limit and provider integration changes don't break existing backends
      3. Cost accounting path from request submission to completion is solid   *** MUST RAISE ***
    goal        Cost accounting path from request submission to completion is solid
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Nothing specific today; owns the subsystem
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm Gemini batch processor request counting is correct and won't regress
      2. Rate limit and provider integration changes don't break existing backends
      3. Cost accounting path from request submission to completion is solid
    goal        Twelve changes to online-request-processing, ten to provider-integrations, eight to bulk-llm-inference; batch mode and rate limit work landing; need confirmation on correctness before post5
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Batch mode counting verified correct; rate limit handling stable; cost accounting path confirmed end-to-end. Post5 release decision can proceed.


------------------------------------------------------------------------------
## #general — 14 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #general: Dario Kestrel put up a draft cache_stats() to make the discussion concrete

    Today is Thursday 13 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Dario Kestrel put up a draft cache_stats() to make the discussion concrete
    
    What it should get through:
    
    On the agenda: Emil Brandvold: the draft constructs a backend client inside cache_stats() to normalise the model alias, which means it demands API keys; CI has none and his run sat on a proxy timeout for ninety seconds before failing, and he wants it reading nothing but what is already on disk; Gideon Halloway: the draft walks every file under ~/.curator, so his numbers included two unrelated projects' runs; asks for it to be scoped to what this instance actually just ran; return type comes back round again, dict versus a small dataclass, still not decided
    
    Wrap when: Changes requested; Dario Kestrel takes both points, return type still open; it is settled that the team agrees a hand-built home-directory path gives wrong numbers when CURATOR_CACHE_DIR is set
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 15 release(s) shipped, currently v0.1.18.post4
      - 251 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 493: Revamp CLI progress bar UI (Gideon Halloway)
      - PR 495: Code executor enhancements + tests (Nikolai Berresford)
      - PR 501: Update badges (Dario Kestrel)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run
      - issue 94: metadata.db updates run status (enum), run progress (percentage), etc
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates

    DOES NOT EXIST YET (4 names)
      - agentic-curation
      - blocks-and-recipes
      - finetuning
      - — and 641 function/class names and 42 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in. These DO exist today and are yours to name: CURATOR_CACHE_DIR.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. burned an hour this morning on my little cache-poking script. It reports 12 hits out of 40k and I nearly re-budgeted the whole persona run on that. Turns out the script does os.path.expanduser("~/.cache/curator") and I have had CURATOR_CACHE_DIR=/mnt/scratch/curator-cache in my shell profile since June. The numbers were from a directory nothing has written to since October.   *** MUST SETTLE (clue t1.r2.L1) ***
         must contain literally: CURATOR_CACHE_DIR
    goal        the team agrees a hand-built home-directory path gives wrong numbers when CURATOR_CACHE_DIR is set
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. 
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
    goal        Dario Kestrel put up a draft cache_stats() to make the discussion concrete
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. 
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
    goal        Dario Kestrel put up a draft cache_stats() to make the discussion concrete
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Changes requested; Dario Kestrel takes both points, return type still open; it is settled that the team agrees a hand-built home-directory path gives wrong numbers when CURATOR_CACHE_DIR is set

