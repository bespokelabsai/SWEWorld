# Phase 4: what the simulation is told

Four things reach a model: the channel scenario and briefing (which the DIRECTOR sees, to pick who speaks next), the shared ground (which EVERYONE in the channel holds), each person's own grounding, and the turn budget.

Worth keeping in mind while reading:

1. **This is today, not history.** Everyone is told the state as of that morning.
2. **MUST RAISE** belongs to the person driving it; the engine holds the conversation open until it lands. **MUST SETTLE** is a planted clue: the engine pushes for it to be stated as a conclusion, and a channel-day that does not get its INFORMATION across is run again — told what was missing. The words are the persona's own; what is fixed is the point, and any identifier named under it.
3. **The forbidden list does not exist yet** on that date. Naming it is the failure this whole pipeline is built to prevent.


==============================================================================
# 2025-02-14 — 3 conversation(s), 30 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 5 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Three PRs older than median merge time; two opened today need eyes; one merged needs follow-up on stale work

    Today is Friday 14 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Three PRs older than median merge time; two opened today need eyes; one merged needs follow-up on stale work
    
    What it should get through:
      1. Unblock PR 468 or confirm it is waiting on external decision   [Emil Brandvold must raise this]
           - Emil flags it has been 7 days since open
           - Gideon or Dermot asks what is blocking
           - Emil either lands it or names what is waiting
      2. Move PR 493 and PR 495 off stale list   [Gideon Halloway must raise this]
           - Gideon asks if PR 493 is ready for review or needs more work
           - Nikolai offers context on PR 495 requirements
           - Konrad or Dermot volunteers to review one of them
      3. Confirm PR 502 is safe to land   [Nikolai Berresford must raise this]
           - Nikolai walks through PR 502 scope
           - Konrad confirms approval stands
           - Emil or Dermot flag if it conflicts with PR 503
    
    On the agenda: Review PR 468 (n samples) for blocker status; Check PR 493 (progress bar) and PR 495 (code executor) readiness; Assess PR 502 (telemetry) and recent PR 503 merge
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Three stale PRs get a path forward: either merged, assigned a reviewer, or confirmed waiting on a blocker outside the team.
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 15 release(s) shipped, currently v0.1.18.post4
      - 252 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 493: Revamp CLI progress bar UI (Gideon Halloway)
      - PR 495: Code executor enhancements + tests (Nikolai Berresford)
      - PR 501: Update badges (Dario Kestrel)
      - PR 502: modify telemetry config (Nikolai Berresford)

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
      - — and 640 function/class names and 42 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Fresh commits on batch client and request processing; knows what PR 468 needs
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Unblock PR 468 or confirm it is waiting on external decision   *** MUST RAISE ***
      2. Move PR 493 and PR 495 off stale list
      3. Confirm PR 502 is safe to land
    goal        Unblock PR 468 or confirm it is waiting on external decision
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. CLI progress bar work; context on PR 493 stall
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Unblock PR 468 or confirm it is waiting on external decision
      2. Move PR 493 and PR 495 off stale list   *** MUST RAISE ***
      3. Confirm PR 502 is safe to land
    goal        Move PR 493 and PR 495 off stale list
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Telemetry config changes; knows PR 495 requirements
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Unblock PR 468 or confirm it is waiting on external decision
      2. Move PR 493 and PR 495 off stale list
      3. Confirm PR 502 is safe to land   *** MUST RAISE ***
    goal        Confirm PR 502 is safe to land
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Code review discipline; can spot integration issues
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Unblock PR 468 or confirm it is waiting on external decision
      2. Move PR 493 and PR 495 off stale list
      3. Confirm PR 502 is safe to land
    goal        Three PRs older than median merge time; two opened today need eyes; one merged needs follow-up on stale work
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Maintainer perspective; knows release readiness
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Unblock PR 468 or confirm it is waiting on external decision
      2. Move PR 493 and PR 495 off stale list
      3. Confirm PR 502 is safe to land
    goal        Three PRs older than median merge time; two opened today need eyes; one merged needs follow-up on stale work
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Three stale PRs get a path forward: either merged, assigned a reviewer, or confirmed waiting on a blocker outside the team.


------------------------------------------------------------------------------
## #engineering — 10 turns, 5 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Heavy refactor day on request processing; batch client merged; cost estimation bug opened; needs alignment before next release

    Today is Friday 14 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Heavy refactor day on request processing; batch client merged; cost estimation bug opened; needs alignment before next release
    
    What it should get through:
      1. Confirm batch client refactor is stable and handles all provider paths   [Emil Brandvold must raise this]
           - Emil summarizes the changes from PR 503
           - Dermot asks about edge cases in provider switching
           - Konrad confirms curator client API did not break
      2. Decide if PR 504 (cost estimation) blocks release or is v0.1.19 followup   [Gideon Halloway must raise this]
           - Gideon describes the cost bug scope
           - Emil or Dario estimates effort to fix
           - Group votes: hotfix or defer
      3. No surprise regressions in multimodal or offline paths after refactor   [Dermot Callaghan must raise this]
           - Dermot raises any test gaps he saw in review
           - Emil or Gideon confirms offline mode tests pass
           - Dario confirms concurrency limits still enforced
    
    On the agenda: Emil walks through the batch client commit and PR 503 merge; Gideon flags the cost estimation bug (PR 504) and where it lands; Group settles whether this is safe to ship or if a hotfix is needed
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team agrees the refactor is stable, cost bug is classified as hotfix or v0.1.19 work, and next release can proceed; it is settled that Gideon Halloway wants the reason for not reusing a stored job logged where the user sees it
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 15 release(s) shipped, currently v0.1.18.post4
      - 252 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 493: Revamp CLI progress bar UI (Gideon Halloway)
      - PR 495: Code executor enhancements + tests (Nikolai Berresford)
      - PR 501: Update badges (Dario Kestrel)
      - PR 502: modify telemetry config (Nikolai Berresford)

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
      - — and 640 function/class names and 42 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Nine commits across batch client, online processing, and offline mode; knows the scope of request handling changes
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm batch client refactor is stable and handles all provider paths   *** MUST RAISE ***
      2. Decide if PR 504 (cost estimation) blocks release or is v0.1.19 followup
      3. No surprise regressions in multimodal or offline paths after refactor
    goal        Confirm batch client refactor is stable and handles all provider paths
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Cost estimation issue flagged (PR 504); knows CLI observability surface
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm batch client refactor is stable and handles all provider paths
      2. Decide if PR 504 (cost estimation) blocks release or is v0.1.19 followup   *** MUST RAISE ***
      3. No surprise regressions in multimodal or offline paths after refactor
      4. whatever we do about reusing pending jobs, say why on the line where we skip one. today the only trace of a resume is the id at DEBUG level, and "resumed 1 pending batch job" with no reason attached is exactly how I burned an afternoon last month. one INFO line naming what didn't line up would have saved all of it.   *** MUST SETTLE (clue t3.r2.l_beh_gideon) ***
    goal        Decide if PR 504 (cost estimation) blocks release or is v0.1.19 followup
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Reviewed PR 503; knows multimodal/structured prompt requirements
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Confirm batch client refactor is stable and handles all provider paths
      2. Decide if PR 504 (cost estimation) blocks release or is v0.1.19 followup
      3. No surprise regressions in multimodal or offline paths after refactor   *** MUST RAISE ***
    goal        No surprise regressions in multimodal or offline paths after refactor
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Owns online-request-processing service; context on concurrency and rate limits
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm batch client refactor is stable and handles all provider paths
      2. Decide if PR 504 (cost estimation) blocks release or is v0.1.19 followup
      3. No surprise regressions in multimodal or offline paths after refactor
    goal        Heavy refactor day on request processing; batch client merged; cost estimation bug opened; needs alignment before next release
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Maintainer view; knows API surface stability
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm batch client refactor is stable and handles all provider paths
      2. Decide if PR 504 (cost estimation) blocks release or is v0.1.19 followup
      3. No surprise regressions in multimodal or offline paths after refactor
    goal        Heavy refactor day on request processing; batch client merged; cost estimation bug opened; needs alignment before next release
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team agrees the refactor is stable, cost bug is classified as hotfix or v0.1.19 work, and next release can proceed; it is settled that Gideon Halloway wants the reason for not reusing a stored job logged where the user sees it; Gideon Halloway wants the reason for not reusing a stored job logged where the user sees it


------------------------------------------------------------------------------
## #pipeline — 8 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Seven changes to provider-integrations, six to online-request-processing, four to batch mode; vLLM test fix; cost estimation bug opened; needs quick checkpoint

    Today is Friday 14 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Seven changes to provider-integrations, six to online-request-processing, four to batch mode; vLLM test fix; cost estimation bug opened; needs quick checkpoint
    
    What it should get through:
      1. No provider integration broke or regressed with batch client and request path changes   [Emil Brandvold must raise this]
           - Emil walks provider-integrations scope in PR 503
           - Dermot confirms CI matrix coverage
           - Gideon or Dario flags any provider that needs manual testing
      2. vLLM offline test fix will not regress again   [Dermot Callaghan must raise this]
           - Dermot describes the fix (#195dab23d0a4)
           - Emil or Gideon confirms the root cause
           - Team agrees monitoring or guard is in place
      3. Cost estimation bug (PR 504) is localized and has a clear owner   [Gideon Halloway must raise this]
           - Gideon shows where cost calc goes wrong
           - Emil or Dario traces it to a specific path
           - Owner commits to fix timeline
    
    On the agenda: Emil runs through the batch client commits and request path changes; Confirm vLLM offline test fix is solid and CI will stay green; Gideon's cost estimation bug: is it in batching, online, or both?
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team confirms providers are stable, vLLM fix is solid, and cost bug is assigned and tracked; it is settled that the team agrees the offline path's hardcoded model names contradicted the maintained support list
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 15 release(s) shipped, currently v0.1.18.post4
      - 252 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 493: Revamp CLI progress bar UI (Gideon Halloway)
      - PR 495: Code executor enhancements + tests (Nikolai Berresford)
      - PR 501: Update badges (Dario Kestrel)
      - PR 502: modify telemetry config (Nikolai Berresford)

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
      - — and 640 function/class names and 42 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Seven commits to provider-integrations and batch mode; knows exactly what changed in the request path
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. No provider integration broke or regressed with batch client and request path changes   *** MUST RAISE ***
      2. vLLM offline test fix will not regress again
      3. Cost estimation bug (PR 504) is localized and has a clear owner
    goal        No provider integration broke or regressed with batch client and request path changes
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Reviewed PR 503; knows which providers get tested in CI
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. No provider integration broke or regressed with batch client and request path changes
      2. vLLM offline test fix will not regress again   *** MUST RAISE ***
      3. Cost estimation bug (PR 504) is localized and has a clear owner
      4. Same flavour of thing on the offline path. vLLM run told a user their model can't do schema-constrained output while the identical model works fine over the API, because local-offline hardcodes its own set of names. That's the third file I've found this year carrying the same model strings around.   *** MUST SETTLE (clue t2.r2.l5) ***
    goal        vLLM offline test fix will not regress again
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Init commit on online-request-processing (#31ee2ee90b5c); opening PR 504 on cost; knows observability surface
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. No provider integration broke or regressed with batch client and request path changes
      2. vLLM offline test fix will not regress again
      3. Cost estimation bug (PR 504) is localized and has a clear owner   *** MUST RAISE ***
    goal        Cost estimation bug (PR 504) is localized and has a clear owner
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Owns the service; knows production constraints
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. No provider integration broke or regressed with batch client and request path changes
      2. vLLM offline test fix will not regress again
      3. Cost estimation bug (PR 504) is localized and has a clear owner
    goal        Seven changes to provider-integrations, six to online-request-processing, four to batch mode; vLLM test fix; cost estimation bug opened; needs quick checkpoint
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team confirms providers are stable, vLLM fix is solid, and cost bug is assigned and tracked; it is settled that the team agrees the offline path's hardcoded model names contradicted the maintained support list


==============================================================================
# 2025-02-17 — 4 conversation(s), 42 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 6 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Three PRs older than the median merge time; six opened or merged today; need to clear backlog

    Today is Monday 17 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Three PRs older than the median merge time; six opened or merged today; need to clear backlog
    
    What it should get through:
      1. Surface blockers on PR 468, PR 502, PR 495 and decide what needs review this week   [Emil Brandvold must raise this]
           - Emil flags that PR 468 is waiting on design; Nikolai Berresford explains PR 502 and PR 495 are waiting on his time
           - Gideon offers to review PR 495 this afternoon
           - Dario notes PR 468 is blocked on multi-sample cost accounting design
      2. write up Release notes: 0.1.19   [Gideon Halloway must raise this]
           - Gideon Halloway says they will write Release notes: 0.1.19 — Summarizes what shipped in the 0.1.19 release.
      3. send Weekly update: week of Feb 10 — pickler regression   [Konrad Feltrin must raise this]
           - Konrad Feltrin says they will send Weekly update: week of Feb 10 — pickler regression
    
    On the agenda: Where is PR 468 (n samples support)?; Where is PR 502 (telemetry config)?; Where is PR 495 (code executor)?; PR 509 (litellm) status; Green light on PR 514 (docs)
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Clear status on why each PR is stuck; at least one gets moved forward this week
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 16 release(s) shipped, currently 0.1.19
      - 258 changes merged to date

    On the table
      - Weekly sync notes: week of Feb 10 — pickler regression (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 495: Code executor enhancements + tests (Nikolai Berresford)
      - PR 502: modify telemetry config (Nikolai Berresford)
      - PR 509: Update/litellm (Emil Brandvold)
      - PR 514: Update README.md to stop kluster.ai promo (Konrad Feltrin)

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
      - — and 639 function/class names and 42 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Context on what PR 468 (n samples) and PR 509 (litellm) need; owns most of the active workstreams
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Surface blockers on PR 468, PR 502, PR 495 and decide what needs review this week   *** MUST RAISE ***
      2. write up Release notes: 0.1.19
      3. send Weekly update: week of Feb 10 — pickler regression
      4. what "Weekly sync notes: week of Feb 10 — pickler regression" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Surface blockers on PR 468, PR 502, PR 495 and decide what needs review this week
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Status of code executor enhancements and telemetry config work
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Surface blockers on PR 468, PR 502, PR 495 and decide what needs review this week
      2. write up Release notes: 0.1.19
      3. send Weekly update: week of Feb 10 — pickler regression
    goal        Three PRs older than the median merge time; six opened or merged today; need to clear backlog
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Can review progress-bar and online-request changes; shipped multiple merges today
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Surface blockers on PR 468, PR 502, PR 495 and decide what needs review this week
      2. write up Release notes: 0.1.19   *** MUST RAISE ***
      3. send Weekly update: week of Feb 10 — pickler regression
      4. that the doc "Release notes: 0.1.19" is done, and where the others can find it   *** MUST RAISE ***
    goal        write up Release notes: 0.1.19
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Status of docs-only changes
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Surface blockers on PR 468, PR 502, PR 495 and decide what needs review this week
      2. write up Release notes: 0.1.19
      3. send Weekly update: week of Feb 10 — pickler regression   *** MUST RAISE ***
      4. that "Weekly update: week of Feb 10 — pickler regression" has gone out, and what you asked in it   *** MUST RAISE ***
    goal        send Weekly update: week of Feb 10 — pickler regression
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Understanding of what bulk-llm-inference and request-processing need
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Surface blockers on PR 468, PR 502, PR 495 and decide what needs review this week
      2. write up Release notes: 0.1.19
      3. send Weekly update: week of Feb 10 — pickler regression
    goal        Three PRs older than the median merge time; six opened or merged today; need to clear backlog
    available   around today

  Priya Vandersloot  (priya)
    role        Software Engineer, LLM Interface. Status of function-calling example
    owns        multimodal-prompts, release-and-ci
    agenda
      1. Surface blockers on PR 468, PR 502, PR 495 and decide what needs review this week
      2. write up Release notes: 0.1.19
      3. send Weekly update: week of Feb 10 — pickler regression
    goal        Three PRs older than the median merge time; six opened or merged today; need to clear backlog
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Clear status on why each PR is stuck; at least one gets moved forward this week


------------------------------------------------------------------------------
## #engineering — 10 turns, 5 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: 25 commits, 6 merges, 4 PRs opened today; need to sync on what's next

    Today is Monday 17 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 25 commits, 6 merges, 4 PRs opened today; need to sync on what's next
    
    What it should get through:
      1. Confirm 0.1.19 is solid and decide what ships next week   [Emil Brandvold must raise this]
           - Emil says batch stabilization is done for now; cli revamp shipped; provider cost maps need one more pass
           - Gideon adds that the progress bar fix resolved the GC leak issue from last week
           - Konrad notes docs are clean
    
    On the agenda: 0.1.19 is out; what shipped; Where we are on the four active workstreams; Stale PRs and blockers this week
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team aligned on 0.1.19 shipping cleanly; Nikolai's two PRs unblocked; focus set on multi-sample support and provider cost maps for next week
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 16 release(s) shipped, currently 0.1.19
      - 258 changes merged to date

    On the table
      - release-0-1-19 (Gideon Halloway)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 495: Code executor enhancements + tests (Nikolai Berresford)
      - PR 502: modify telemetry config (Nikolai Berresford)
      - PR 509: Update/litellm (Emil Brandvold)
      - PR 514: Update README.md to stop kluster.ai promo (Konrad Feltrin)

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
      - — and 639 function/class names and 42 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Status of all four workstreams: batch stabilization mostly done, provider cost maps in progress, multimodal test hardening ongoing, CLI revamp shipped
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm 0.1.19 is solid and decide what ships next week   *** MUST RAISE ***
      2. what "Release notes: 0.1.19" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm 0.1.19 is solid and decide what ships next week
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Just shipped progress bar revamp and a dozen fixes to online request handling and cost tracking
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm 0.1.19 is solid and decide what ships next week
    goal        25 commits, 6 merges, 4 PRs opened today; need to sync on what's next
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Docs side is mostly cleanup; no blockers
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm 0.1.19 is solid and decide what ships next week
    goal        25 commits, 6 merges, 4 PRs opened today; need to sync on what's next
    available   around today

  Priya Vandersloot  (priya)
    role        Software Engineer, LLM Interface. The function-calling example is now fixed and shipped in 0.1.19
    owns        multimodal-prompts, release-and-ci
    agenda
      1. Confirm 0.1.19 is solid and decide what ships next week
    goal        25 commits, 6 merges, 4 PRs opened today; need to sync on what's next
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Observer; understands request layer
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm 0.1.19 is solid and decide what ships next week
    goal        25 commits, 6 merges, 4 PRs opened today; need to sync on what's next
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Team aligned on 0.1.19 shipping cleanly; Nikolai's two PRs unblocked; focus set on multi-sample support and provider cost maps for next week


------------------------------------------------------------------------------
## #general — 6 turns, 6 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #general: 0.1.19 shipped overnight; needs company visibility

    Today is Monday 17 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 0.1.19 shipped overnight; needs company visibility
    
    What it should get through:
      1. Announce 0.1.19 with key changes so everyone knows to upgrade   [Gideon Halloway must raise this]
           - Gideon posts announcement in general with summary of what shipped
           - Team confirms it looks good
           - Anyone running older version gets quiet nudge to upgrade
    
    On the agenda: Post 0.1.19 announcement with highlights; Surface any questions or issues
    
    Belongs in this channel: news the whole company needs: releases that matter to everyone, scheduling, people joining or moving on, and decisions that cross every team.
    Does NOT belong here: work on any individual service, and anything only one team cares about.
    
    Wrap when: 0.1.19 announced to the company; users notified to upgrade
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 16 release(s) shipped, currently 0.1.19
      - 258 changes merged to date

    On the table
      - announce-0-1-19 (Gideon Halloway)
      - release-0-1-19 (Gideon Halloway)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 495: Code executor enhancements + tests (Nikolai Berresford)
      - PR 502: modify telemetry config (Nikolai Berresford)
      - PR 509: Update/litellm (Emil Brandvold)
      - PR 514: Update README.md to stop kluster.ai promo (Konrad Feltrin)

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
      - — and 639 function/class names and 42 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. The release announcement and what changed
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Announce 0.1.19 with key changes so everyone knows to upgrade   *** MUST RAISE ***
      2. that "0.1.19 is out" has gone out, and what you asked in it   *** MUST RAISE ***
      3. what "Release notes: 0.1.19" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Announce 0.1.19 with key changes so everyone knows to upgrade
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Can answer questions about the release
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Announce 0.1.19 with key changes so everyone knows to upgrade
    goal        0.1.19 shipped overnight; needs company visibility
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Can provide context on what shipped and why
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Announce 0.1.19 with key changes so everyone knows to upgrade
    goal        0.1.19 shipped overnight; needs company visibility
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Can comment on docs and examples side
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Announce 0.1.19 with key changes so everyone knows to upgrade
    goal        0.1.19 shipped overnight; needs company visibility
    available   around today

  Priya Vandersloot  (priya)
    role        Software Engineer, LLM Interface. Can note the function-calling example fix
    owns        multimodal-prompts, release-and-ci
    agenda
      1. Announce 0.1.19 with key changes so everyone knows to upgrade
    goal        0.1.19 shipped overnight; needs company visibility
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Can comment on CI and test coverage
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Announce 0.1.19 with key changes so everyone knows to upgrade
    goal        0.1.19 shipped overnight; needs company visibility
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   0.1.19 announced to the company; users notified to upgrade


------------------------------------------------------------------------------
## #pipeline — 14 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Dario Kestrel wants a status before the week's cut and Gideon Halloway is buried in something else

    Today is Monday 17 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Dario Kestrel wants a status before the week's cut and Gideon Halloway is buried in something else
    
    What it should get through:
    
    On the agenda: Dario Kestrel asks where the draft stands; Gideon Halloway is chasing a viewer regression and has not looked; Gideon Halloway mentions in passing that the one version he did try took over two minutes on a 200k-row dataset because it opened each cache entry individually; Gideon Halloway also mentions he pointed the same script at a newer model snapshot last week and it completed in three seconds, which he found suspicious but did not chase
    
    Wrap when: No progress, two observations logged and nothing claimed; it is settled that the team agrees users want the cached-versus-backend split before starting a run
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 16 release(s) shipped, currently 0.1.19
      - 258 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 495: Code executor enhancements + tests (Nikolai Berresford)
      - PR 502: modify telemetry config (Nikolai Berresford)
      - PR 509: Update/litellm (Emil Brandvold)
      - PR 514: Update README.md to stop kluster.ai promo (Konrad Feltrin)

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
      - — and 639 function/class names and 42 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
    goal        Dario Kestrel wants a status before the week's cut and Gideon Halloway is buried in something else
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. 
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. people keep asking the same question before a re-run: how much of this is already on disk. Right now the only way to answer it is to run the thing and watch the hit counter go by on the progress bar, which is too late to decide anything.   *** MUST SETTLE (clue t1.r2.L13) ***
    goal        the team agrees users want the cached-versus-backend split before starting a run
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   No progress, two observations logged and nothing claimed; it is settled that the team agrees users want the cached-versus-backend split before starting a run


==============================================================================
# 2025-02-18 — 3 conversation(s), 37 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 5 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Two new PRs opened today, four under review, three stale; clearing the queue before they age further

    Today is Tuesday 18 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two new PRs opened today, four under review, three stale; clearing the queue before they age further
    
    What it should get through:
      1. Approve and land PR 515 error summarization   [Emil Brandvold must raise this]
           - Emil walks through the error-summarization logic for online mode
           - Dario checks the cost-map interaction
           - Gideon confirms no viewer surface impact
      2. Approve and land PR 516 curator viewer links   [Gideon Halloway must raise this]
           - Gideon presents the rich hyperlink UX
           - Emil confirms no request-layer impact
           - Dario approves the interface contract
      3. Unblock PR 495 code executor and PR 502 telemetry   [Nikolai Berresford must raise this]
           - Nikolai outlines what's blocking PR 495 and PR 502
           - Emil and Dario Kestrel offer suggestions on test coverage or integration points
           - Nikolai commits to next steps or surface remaining friction
    
    On the agenda: Land PR 515 error summarization; Land PR 516 curator viewer links; Discuss PR 495 code executor enhancements and PR 502 telemetry blockers
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 515 and PR 516 land cleanly; PR 495 and PR 502 have a clear path forward or concrete blockers named.
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 16 release(s) shipped, currently 0.1.19
      - 259 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 495: Code executor enhancements + tests (Nikolai Berresford)
      - PR 502: modify telemetry config (Nikolai Berresford)
      - PR 509: Update/litellm (Emil Brandvold)
      - PR 515: ref: summarize errors in online mode (Emil Brandvold)
      - PR 516: Rich hyperlink for curator viewer (Gideon Halloway)

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
      - — and 639 function/class names and 42 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Error summarization in online mode; knows the request-processing layer deeply
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Approve and land PR 515 error summarization   *** MUST RAISE ***
      2. Approve and land PR 516 curator viewer links
      3. Unblock PR 495 code executor and PR 502 telemetry
    goal        Approve and land PR 515 error summarization
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. UX polish on curator viewer links; knows the UI surface
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Approve and land PR 515 error summarization
      2. Approve and land PR 516 curator viewer links   *** MUST RAISE ***
      3. Unblock PR 495 code executor and PR 502 telemetry
    goal        Approve and land PR 516 curator viewer links
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Code execution testing rigor; knows verifier design
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Approve and land PR 515 error summarization
      2. Approve and land PR 516 curator viewer links
      3. Unblock PR 495 code executor and PR 502 telemetry   *** MUST RAISE ***
    goal        Unblock PR 495 code executor and PR 502 telemetry
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Request-processing depth; knows the core LLM interface
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Approve and land PR 515 error summarization
      2. Approve and land PR 516 curator viewer links
      3. Unblock PR 495 code executor and PR 502 telemetry
    goal        Two new PRs opened today, four under review, three stale; clearing the queue before they age further
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. README context; drove PR 514 to completion
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Approve and land PR 515 error summarization
      2. Approve and land PR 516 curator viewer links
      3. Unblock PR 495 code executor and PR 502 telemetry
    goal        Two new PRs opened today, four under review, three stale; clearing the queue before they age further
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 515 and PR 516 land cleanly; PR 495 and PR 502 have a clear path forward or concrete blockers named.


------------------------------------------------------------------------------
## #engineering — 14 turns, 5 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Eleven commits today, one merge, three stale PRs; team needs to see the shape of the current work and hand-offs

    Today is Tuesday 18 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Eleven commits today, one merge, three stale PRs; team needs to see the shape of the current work and hand-offs
    
    What it should get through:
      1. Confirm README Grooming completed and identify next cleanup work   [Konrad Feltrin must raise this]
           - Konrad confirms PR 514 merged and kluster.ai promo removed
           - Emil and Gideon Halloway check whether provider examples need follow-up
           - Team agrees on scope of next round if needed
      2. Socialize error handling and viewer link improvements   [Gideon Halloway must raise this]
           - Emil describes the error-summarization work in PR 515
           - Gideon walks the curator viewer link polish in PR 516
           - Dario and Konrad Feltrin note whether these unblock other work
      3. Name what is blocking sample support and code executor tests   [Dario Kestrel must raise this]
           - Dario outlines what's needed for PR 468 sample support
           - Nikolai surfaces the test coverage gap on PR 495
           - Team commits to next PR or identifies what must land first
    
    On the agenda: Recap README Grooming landing and what comes next; Dispatch work on error handling and viewer UX; Clarify blockers on sample support and code executor tests
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team sees the shape of work in flight; PR 514 handoff is clear; blockers on PR 468 and PR 495 are named or have a plan.
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 16 release(s) shipped, currently 0.1.19
      - 259 changes merged to date

    On the table
      - Release notes: 0.1.19 (Gideon Halloway)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 495: Code executor enhancements + tests (Nikolai Berresford)
      - PR 502: modify telemetry config (Nikolai Berresford)
      - PR 509: Update/litellm (Emil Brandvold)
      - PR 515: ref: summarize errors in online mode (Emil Brandvold)
      - PR 516: Rich hyperlink for curator viewer (Gideon Halloway)

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
      - — and 639 function/class names and 42 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Eight commits today across examples, docs, error handling; knows what's moving
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm README Grooming completed and identify next cleanup work
      2. Socialize error handling and viewer link improvements
      3. Name what is blocking sample support and code executor tests
    goal        Eleven commits today, one merge, three stale PRs; team needs to see the shape of the current work and hand-offs
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Three commits on rich markup and viewer links; owns progress-and-cli
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm README Grooming completed and identify next cleanup work
      2. Socialize error handling and viewer link improvements   *** MUST RAISE ***
      3. Name what is blocking sample support and code executor tests
    goal        Socialize error handling and viewer link improvements
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. README Grooming landed; knows what's next on examples-cookbooks
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm README Grooming completed and identify next cleanup work   *** MUST RAISE ***
      2. Socialize error handling and viewer link improvements
      3. Name what is blocking sample support and code executor tests
      4. what "Release notes: 0.1.19" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm README Grooming completed and identify next cleanup work
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Request-processing depth; knows the blockers on PR 468 and PR 121
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm README Grooming completed and identify next cleanup work
      2. Socialize error handling and viewer link improvements
      3. Name what is blocking sample support and code executor tests   *** MUST RAISE ***
    goal        Name what is blocking sample support and code executor tests
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Code execution design; knows the test coverage gaps on PR 495
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Confirm README Grooming completed and identify next cleanup work
      2. Socialize error handling and viewer link improvements
      3. Name what is blocking sample support and code executor tests
    goal        Eleven commits today, one merge, three stale PRs; team needs to see the shape of the current work and hand-offs
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team sees the shape of work in flight; PR 514 handoff is clear; blockers on PR 468 and PR 495 are named or have a plan.


------------------------------------------------------------------------------
## #pipeline — 11 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Seven changes to provider-integrations, five to online-request-processing, four each to bulk-llm-inference and caching-and-resume; core request layer is moving

    Today is Tuesday 18 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Seven changes to provider-integrations, five to online-request-processing, four each to bulk-llm-inference and caching-and-resume; core request layer is moving
    
    What it should get through:
      1. Validate error-summarization logic in online mode   [Emil Brandvold must raise this]
           - Emil walks the error-summarization beats in PR 515
           - Gideon checks logging contract with progress-and-cli
           - Dario confirms retry/resume behavior is unchanged
      2. Review cost-map refactoring and its interaction with caching   [Dario Kestrel must raise this]
           - Emil describes the cost completion method changes in #716e7b59b447
           - Dermot asks about persistence and cache invalidation
           - Dario names any contract changes needed in viewer or CLI
      3. Confirm provider example updates don't break integration tests   [Gideon Halloway must raise this]
           - Emil summarizes litellm and provider example updates
           - Dario and Dermot Callaghan ask whether CI coverage is sufficient
           - Gideon confirms no new telemetry or logging side-effects
    
    On the agenda: Error summarization and online-mode robustness; Cost-map refactoring and accuracy; Provider integration stability across examples
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Error handling and cost-map changes are understood; no hidden contract breaks; PR 515 is clear to land.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 16 release(s) shipped, currently 0.1.19
      - 259 changes merged to date

    On the table
      - Release notes: 0.1.19 (Gideon Halloway)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 495: Code executor enhancements + tests (Nikolai Berresford)
      - PR 502: modify telemetry config (Nikolai Berresford)
      - PR 509: Update/litellm (Emil Brandvold)
      - PR 515: ref: summarize errors in online mode (Emil Brandvold)
      - PR 516: Rich hyperlink for curator viewer (Gideon Halloway)

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
      - — and 639 function/class names and 42 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Eight commits across online-mode error handling, cost map, litellm updates; knows the request layer end-to-end
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Validate error-summarization logic in online mode   *** MUST RAISE ***
      2. Review cost-map refactoring and its interaction with caching
      3. Confirm provider example updates don't break integration tests
    goal        Validate error-summarization logic in online mode
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Three commits on rich markup and logger redirect; owns observability and progress tracking
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Validate error-summarization logic in online mode
      2. Review cost-map refactoring and its interaction with caching
      3. Confirm provider example updates don't break integration tests   *** MUST RAISE ***
      4. what "Release notes: 0.1.19" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm provider example updates don't break integration tests
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Core understanding of retry logic, concurrency, provider abstraction
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Validate error-summarization logic in online mode
      2. Review cost-map refactoring and its interaction with caching   *** MUST RAISE ***
      3. Confirm provider example updates don't break integration tests
    goal        Review cost-map refactoring and its interaction with caching
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Deep request-layer history; knows where caching and resume interact
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Validate error-summarization logic in online mode
      2. Review cost-map refactoring and its interaction with caching
      3. Confirm provider example updates don't break integration tests
    goal        Seven changes to provider-integrations, five to online-request-processing, four each to bulk-llm-inference and caching-and-resume; core request layer is moving
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Error handling and cost-map changes are understood; no hidden contract breaks; PR 515 is clear to land.


==============================================================================
# 2025-02-19 — 4 conversation(s), 44 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Three PRs opened or merged in a single day on logging and viewer; PR 516 stuck waiting on changes; logger work spans all services

    Today is Wednesday 19 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Three PRs opened or merged in a single day on logging and viewer; PR 516 stuck waiting on changes; logger work spans all services
    
    What it should get through:
      1. Land PR 518 (custom logger) or identify blockers   [Emil Brandvold must raise this]
           - Emil walks through logger design and where it surfaces
           - Dermot flags integration concerns with existing error handling
           - Decision: land or request changes
      2. Unblock PR 516 (rich hyperlink) from CHANGES_REQUESTED   [Gideon Halloway must raise this]
           - Gideon presents what the changes request is about
           - Dermot clarifies the blocker
           - Team decides: rework, accept, or defer
    
    On the agenda: Review PR 518 (Feat/logger) for scope and integration; Assess PR 520 (Feat/push to viewer) against PR 516 progress; Decide what unblocks PR 516 from CHANGES_REQUESTED
    
    Meeting today: Weekly sync
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 518 and PR 520 either land or have clear feedback; PR 516's path forward is known
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 16 release(s) shipped, currently 0.1.19
      - 260 changes merged to date

    On the table
      - notes-2025-02-17 (Gideon Halloway)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 495: Code executor enhancements + tests (Nikolai Berresford)
      - PR 502: modify telemetry config (Nikolai Berresford)
      - PR 509: Update/litellm (Emil Brandvold)
      - PR 516: Rich hyperlink for curator viewer (Gideon Halloway)
      - PR 518: Feat/logger (Emil Brandvold)

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
      - — and 639 function/class names and 42 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Four commits on logging and viewer integration; knows what the logger and push-to-viewer features need
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Land PR 518 (custom logger) or identify blockers   *** MUST RAISE ***
      2. Unblock PR 516 (rich hyperlink) from CHANGES_REQUESTED
      3. what "Weekly sync notes: week of Feb 17 — 0.1.19 shipped" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Land PR 518 (custom logger) or identify blockers
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Rich hyperlink work complete; owns progress-and-cli surface
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Land PR 518 (custom logger) or identify blockers
      2. Unblock PR 516 (rich hyperlink) from CHANGES_REQUESTED   *** MUST RAISE ***
      3. that the doc "Weekly sync notes: week of Feb 17 — 0.1.19 shipped" is done, and where the others can find it   *** MUST RAISE ***
    goal        Unblock PR 516 (rich hyperlink) from CHANGES_REQUESTED
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Reviewed PR 516 with changes requested; knows integration points
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Land PR 518 (custom logger) or identify blockers
      2. Unblock PR 516 (rich hyperlink) from CHANGES_REQUESTED
    goal        Three PRs opened or merged in a single day on logging and viewer; PR 516 stuck waiting on changes; logger work spans all services
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 518 and PR 520 either land or have clear feedback; PR 516's path forward is known


------------------------------------------------------------------------------
## #pipeline — 12 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Emil landed 4 commits (logger, error summary, curator init) touching 8+ services in online-request-processing and provider-integrations; Gideon made 5 commits to progress bar and status; mid-flight workstream

    Today is Wednesday 19 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Emil landed 4 commits (logger, error summary, curator init) touching 8+ services in online-request-processing and provider-integrations; Gideon made 5 commits to progress bar and status; mid-flight workstream
    
    What it should get through:
      1. Confirm logger design handles concurrent requests and retries safely   [Emil Brandvold must raise this]
           - Emil explains logger scope (what gets logged, where, at what level)
           - Dario raises concurrency or cleanup concerns
           - Team agrees logger is thread-safe or marks it for follow-up
      2. Validate error summary format works with rich progress bar without visual collision   [Gideon Halloway must raise this]
           - Gideon demonstrates rich console views with error output
           - Emil describes error summary format change
           - Dario or Gideon flags if they collide or decide one takes priority
    
    On the agenda: Walk through logger integration across services; Check error summary format against user-facing output; Validate provider backend changes don't introduce regressions
    
    Meeting today: Weekly sync
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Logger and error summary changes are safe for release; no regressions expected in provider integrations or retry paths
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 16 release(s) shipped, currently 0.1.19
      - 260 changes merged to date

    On the table
      - notes-2025-02-17 (Gideon Halloway)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 495: Code executor enhancements + tests (Nikolai Berresford)
      - PR 502: modify telemetry config (Nikolai Berresford)
      - PR 509: Update/litellm (Emil Brandvold)
      - PR 516: Rich hyperlink for curator viewer (Gideon Halloway)
      - PR 518: Feat/logger (Emil Brandvold)

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
      - — and 639 function/class names and 42 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Custom logger implementation; error summary refactor across all services; knows the context for each commit
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm logger design handles concurrent requests and retries safely   *** MUST RAISE ***
      2. Validate error summary format works with rich progress bar without visual collision
      3. what "Weekly sync notes: week of Feb 17 — 0.1.19 shipped" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm logger design handles concurrent requests and retries safely
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Rich console views for progress bar and CLI output; understands how status/error display flows to user
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm logger design handles concurrent requests and retries safely
      2. Validate error summary format works with rich progress bar without visual collision   *** MUST RAISE ***
    goal        Validate error summary format works with rich progress bar without visual collision
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Knows request layer concurrency and error propagation
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm logger design handles concurrent requests and retries safely
      2. Validate error summary format works with rich progress bar without visual collision
    goal        Emil landed 4 commits (logger, error summary, curator init) touching 8+ services in online-request-processing and provider-integrations; Gideon made 5 commits to progress bar and status; mid-flight workstream
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Logger and error summary changes are safe for release; no regressions expected in provider integrations or retry paths


------------------------------------------------------------------------------
## #viewer — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #viewer: Gideon landed 5 commits on progress bar, status, and rich console views; PR 516 blocked 1 day; rich hyperlink for viewer links is mid-implementation

    Today is Wednesday 19 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Gideon landed 5 commits on progress bar, status, and rich console views; PR 516 blocked 1 day; rich hyperlink for viewer links is mid-implementation
    
    What it should get through:
      1. Resolve PR 516 CHANGES_REQUESTED and land rich hyperlink feature   [Gideon Halloway must raise this]
           - Gideon presents the revised hyperlink approach
           - Dermot re-evaluates or confirms the change request is addressed
           - Team decides to land or iterate
      2. Coordinate logger output with progress bar visual layout   [Gideon Halloway must raise this]
           - Gideon shows how rich hyperlinks render with status messages
           - Emil flags any logger output that might overflow or collide
           - Decision: logger goes before/after progress, or in separate stream
    
    On the agenda: Review PR 516 (rich hyperlink) state and resolve CHANGES_REQUESTED; Link display in context of logger and error summary output; Run status and progress metadata capture in metadata.db
    
    Meeting today: Weekly sync
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: PR 516 unblocked or path to unblock is clear; progress bar, status, and logger output layout is settled
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 16 release(s) shipped, currently 0.1.19
      - 260 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 495: Code executor enhancements + tests (Nikolai Berresford)
      - PR 502: modify telemetry config (Nikolai Berresford)
      - PR 509: Update/litellm (Emil Brandvold)
      - PR 516: Rich hyperlink for curator viewer (Gideon Halloway)
      - PR 518: Feat/logger (Emil Brandvold)

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
      - — and 639 function/class names and 42 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Rich console views and hyperlink work; progress bar refinements; owns UI surface
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Resolve PR 516 CHANGES_REQUESTED and land rich hyperlink feature   *** MUST RAISE ***
      2. Coordinate logger output with progress bar visual layout   *** MUST RAISE ***
    goal        Resolve PR 516 CHANGES_REQUESTED and land rich hyperlink feature
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Logger work that will affect what status and error info displays
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Resolve PR 516 CHANGES_REQUESTED and land rich hyperlink feature
      2. Coordinate logger output with progress bar visual layout
    goal        Gideon landed 5 commits on progress bar, status, and rich console views; PR 516 blocked 1 day; rich hyperlink for viewer links is mid-implementation
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Watched PR 516 changes; knows integration story
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Resolve PR 516 CHANGES_REQUESTED and land rich hyperlink feature
      2. Coordinate logger output with progress bar visual layout
    goal        Gideon landed 5 commits on progress bar, status, and rich console views; PR 516 blocked 1 day; rich hyperlink for viewer links is mid-implementation
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 516 unblocked or path to unblock is clear; progress bar, status, and logger output layout is settled


------------------------------------------------------------------------------
## #engineering — 14 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: The counting work cannot be built on top of the current key without producing numbers people will not believe

    Today is Wednesday 19 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: The counting work cannot be built on top of the current key without producing numbers people will not believe
    
    What it should get through:
    
    On the agenda: Gideon Halloway says he fixed a typo in the system message inside a prompt function, reran, and got the old rows straight back, so he does not trust anything that hashes at the level of the function or the run; Dermot Callaghan argues for hashing the exact bytes we would put on the wire for that one row, Dario Kestrel worries provider-specific fields we inject ourselves will churn keys between releases; left open: what to do about fields the SDK adds after we build the payload
    
    Wrap when: Leaning towards a per-row payload hash, with Dario Kestrel's churn objection unresolved and no PR yet; it is settled that the team agrees adding a column prompt() ignores currently invalidates reuse and that this is a real cost
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 16 release(s) shipped, currently 0.1.19
      - 260 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 495: Code executor enhancements + tests (Nikolai Berresford)
      - PR 502: modify telemetry config (Nikolai Berresford)
      - PR 509: Update/litellm (Emil Brandvold)
      - PR 516: Rich hyperlink for curator viewer (Gideon Halloway)
      - PR 518: Feat/logger (Emil Brandvold)

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
      - — and 639 function/class names and 42 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in. These DO exist today and are yours to name: source_url.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. 
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
    goal        The counting work cannot be built on top of the current key without producing numbers people will not believe
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. 
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Heads up, I added a source_url column to the persona input set purely for provenance. prompt() does not look at it. Entire 40k run went back out to the API and billed me again. I did not touch a single prompt.   *** MUST SETTLE (clue t1.r1.l_prompt_1) ***
         must contain literally: source_url
    goal        the team agrees adding a column prompt() ignores currently invalidates reuse and that this is a real cost
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
    goal        The counting work cannot be built on top of the current key without producing numbers people will not believe
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Leaning towards a per-row payload hash, with Dario Kestrel's churn objection unresolved and no PR yet; it is settled that the team agrees adding a column prompt() ignores currently invalidates reuse and that this is a real cost


==============================================================================
# 2025-02-20 — 4 conversation(s), 49 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: three PRs merged today, five more waiting; stale PRs in the backlog need movement

    Today is Thursday 20 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: three PRs merged today, five more waiting; stale PRs in the backlog need movement
    
    What it should get through:
      1. land PR 530 and PR 509 together as the telemetry fix   [Emil Brandvold must raise this]
           - Emil Brandvold flags the expanduser fix is ready
           - Nikolai Berresford notes his config change rides along
           - Dermot Callaghan approves the pair
      2. unblock PR 520 (push to viewer) or defer it cleanly   [Emil Brandvold must raise this]
           - Emil Brandvold describes the blocker
           - Gideon Halloway weighs in on viewer readiness
           - group decides to land or defer
      3. move PR 495 and PR 502 forward or accept they slip to next week   [Nikolai Berresford must raise this]
           - Nikolai Berresford explains what's needed
           - Dermot Callaghan or Emil Brandvold offers review time
           - or group agrees it lands next week
    
    On the agenda: where PR 520 (push to viewer) stands and what's blocking; whether PR 518 (logger) and PR 530 (telemetry) can land today; PR 495 (code executor enhancements) and PR 502 (telemetry config) status
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: At least PR 530 and PR 509 land; decision on PR 520 (merge today or hold); PR 495/#502 either reviewed or deferred to next week
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 16 release(s) shipped, currently 0.1.19
      - 263 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 495: Code executor enhancements + tests (Nikolai Berresford)
      - PR 502: modify telemetry config (Nikolai Berresford)
      - PR 518: Feat/logger (Emil Brandvold)
      - PR 520: Feat/push to viewer (Emil Brandvold)

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
      - — and 637 function/class names and 42 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. the telemetry fix and the viewer push work; knows what's blocking the other PRs
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. land PR 530 and PR 509 together as the telemetry fix   *** MUST RAISE ***
      2. unblock PR 520 (push to viewer) or defer it cleanly   *** MUST RAISE ***
      3. move PR 495 and PR 502 forward or accept they slip to next week
    goal        land PR 530 and PR 509 together as the telemetry fix
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. context on the viewer hyperlink changes and the broader viewer UX epic
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. land PR 530 and PR 509 together as the telemetry fix
      2. unblock PR 520 (push to viewer) or defer it cleanly
      3. move PR 495 and PR 502 forward or accept they slip to next week
    goal        three PRs merged today, five more waiting; stale PRs in the backlog need movement
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. the async/docker timeout changes that unblock code-execution work
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. land PR 530 and PR 509 together as the telemetry fix
      2. unblock PR 520 (push to viewer) or defer it cleanly
      3. move PR 495 and PR 502 forward or accept they slip to next week   *** MUST RAISE ***
    goal        move PR 495 and PR 502 forward or accept they slip to next week
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. review stability and standards
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. land PR 530 and PR 509 together as the telemetry fix
      2. unblock PR 520 (push to viewer) or defer it cleanly
      3. move PR 495 and PR 502 forward or accept they slip to next week
    goal        three PRs merged today, five more waiting; stale PRs in the backlog need movement
    available   around today

### 4. How it should land

    lands as  partial
    leaving   At least PR 530 and PR 509 land; decision on PR 520 (merge today or hold); PR 495/#502 either reviewed or deferred to next week


------------------------------------------------------------------------------
## #engineering — 14 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: 20 commits, 3 PRs merged, 5 PRs waiting; new epic opened with six follow-up issues; team needs to calibrate priorities

    Today is Thursday 20 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 20 commits, 3 PRs merged, 5 PRs waiting; new epic opened with six follow-up issues; team needs to calibrate priorities
    
    What it should get through:
      1. celebrate the week's shipped work and understand the pattern   [Emil Brandvold must raise this]
           - Emil Brandvold summarizes the merged PRs
           - Gideon Halloway notes the viewer polish is paying off
           - team acknowledges the pace
      2. align on the viewer UX epic direction   [Gideon Halloway must raise this]
           - Gideon Halloway presents the epic (521) and the follow-ups (522–527)
           - Dermot Callaghan asks about effort vs. other work
           - group agrees to treat as roadmap items vs. immediate work
      3. decide which stale PR gets attention next   [Emil Brandvold must raise this]
           - Emil Brandvold flags PR 468 (n samples) is 13 days old
           - Nikolai Berresford defends PR 495 and PR 502
           - group decides on a clear next item
    
    On the agenda: what shipped this week (hyperlinks, telemetry, litellm); Gideon Halloway's new viewer UX epic and the six issues; where the stale PRs stand and what's genuinely blocking them
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team understands what shipped and why; viewer epic is mapped; one stale PR gets clear next steps
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 16 release(s) shipped, currently 0.1.19
      - 263 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 495: Code executor enhancements + tests (Nikolai Berresford)
      - PR 502: modify telemetry config (Nikolai Berresford)
      - PR 518: Feat/logger (Emil Brandvold)
      - PR 520: Feat/push to viewer (Emil Brandvold)

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
      - — and 637 function/class names and 42 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. summary of what landed: hyperlinks, telemetry fix, litellm bump
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. celebrate the week's shipped work and understand the pattern   *** MUST RAISE ***
      2. align on the viewer UX epic direction
      3. decide which stale PR gets attention next   *** MUST RAISE ***
    goal        celebrate the week's shipped work and understand the pattern
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. the viewer epic he just opened and six fresh issues
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. celebrate the week's shipped work and understand the pattern
      2. align on the viewer UX epic direction   *** MUST RAISE ***
      3. decide which stale PR gets attention next
    goal        align on the viewer UX epic direction
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. code-execution docker/async work; context on what's holding PR 495
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. celebrate the week's shipped work and understand the pattern
      2. align on the viewer UX epic direction
      3. decide which stale PR gets attention next
    goal        20 commits, 3 PRs merged, 5 PRs waiting; new epic opened with six follow-up issues; team needs to calibrate priorities
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. stability and standards perspective
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. celebrate the week's shipped work and understand the pattern
      2. align on the viewer UX epic direction
      3. decide which stale PR gets attention next
    goal        20 commits, 3 PRs merged, 5 PRs waiting; new epic opened with six follow-up issues; team needs to calibrate priorities
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team understands what shipped and why; viewer epic is mapped; one stale PR gets clear next steps


------------------------------------------------------------------------------
## #pipeline — 9 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: 14 commits to online-request-processing, 9 to bulk-llm-inference, 9 to caching-and-resume; three PRs merged affecting this layer

    Today is Thursday 20 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 14 commits to online-request-processing, 9 to bulk-llm-inference, 9 to caching-and-resume; three PRs merged affecting this layer
    
    What it should get through:
      1. confirm no regressions from the viewer/progress bar polish   [Gideon Halloway must raise this]
           - Gideon Halloway walks through the hyperlink and message changes
           - Emil Brandvold confirms no breaking changes
           - group signs off or flags a concern
      2. note the curator home and telemetry impact   [Emil Brandvold must raise this]
           - Emil Brandvold describes the curator home feature
           - group agrees it's safe or needs a follow-up test
    
    On the agenda: what the recent commits did to online, caching, and progress tracking; whether the viewer polish has any backend implications; any stability concerns from the week
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Pipeline layer stability confirmed; no concerns raised from recent changes
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 16 release(s) shipped, currently 0.1.19
      - 263 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 495: Code executor enhancements + tests (Nikolai Berresford)
      - PR 502: modify telemetry config (Nikolai Berresford)
      - PR 518: Feat/logger (Emil Brandvold)
      - PR 520: Feat/push to viewer (Emil Brandvold)

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
      - — and 637 function/class names and 42 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. the hyperlink, telemetry, and litellm work; knows what's live
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. confirm no regressions from the viewer/progress bar polish
      2. note the curator home and telemetry impact   *** MUST RAISE ***
    goal        note the curator home and telemetry impact
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. the viewer polish and the curator home feature; sees the UX side
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. confirm no regressions from the viewer/progress bar polish   *** MUST RAISE ***
      2. note the curator home and telemetry impact
    goal        confirm no regressions from the viewer/progress bar polish
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. standards and integration testing perspective
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. confirm no regressions from the viewer/progress bar polish
      2. note the curator home and telemetry impact
    goal        14 commits to online-request-processing, 9 to bulk-llm-inference, 9 to caching-and-resume; three PRs merged affecting this layer
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Pipeline layer stability confirmed; no concerns raised from recent changes


------------------------------------------------------------------------------
## #viewer — 14 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #viewer: The summary table is where most users will actually read these counts

    Today is Thursday 20 February 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: The summary table is where most users will actually read these counts
    
    What it should get through:
    
    On the agenda: Gideon Halloway wants the table to print exactly what cache_stats() returns and says the two lines have to add up to the number of rows the user handed in, otherwise people will not trust either surface; Emil Brandvold says when he ran with CURATOR_DISABLE_CACHE set the summary printed nothing at all and he assumed the run had died; he thinks it should just state that everything went to the provider and carry on; open: whether to also show a projected dollar figure for the re-run, or only counts
    
    Wrap when: Table wiring deferred until the method's return shape is fixed; cost projection unresolved; it is settled that the team agrees a fractional hit_rate is needed alongside raw counts
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Stratos Crunch: Backend Explosion and Loosened Process

    Settled
      - 16 release(s) shipped, currently 0.1.19
      - 263 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 495: Code executor enhancements + tests (Nikolai Berresford)
      - PR 502: modify telemetry config (Nikolai Berresford)
      - PR 518: Feat/logger (Emil Brandvold)
      - PR 520: Feat/push to viewer (Emil Brandvold)

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
      - — and 637 function/class names and 42 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in. These DO exist today and are yours to name: hit_rate.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. 
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. The end of run table says cached: 12,403 and the first thing every single user asks is out of what. A bare count tells nobody whether their rerun is cheap. Give me a hit_rate I can print as a percentage next to it.   *** MUST SETTLE (clue t1.r1.l_stats_1) ***
         must contain literally: hit_rate
    goal        the team agrees a fractional hit_rate is needed alongside raw counts
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. 
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
    goal        The summary table is where most users will actually read these counts
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
    goal        The summary table is where most users will actually read these counts
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Table wiring deferred until the method's return shape is fixed; cost projection unresolved; it is settled that the team agrees a fractional hit_rate is needed alongside raw counts

