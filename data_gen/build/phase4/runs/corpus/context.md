# Phase 4: what the simulation is told

Four things reach a model: the channel scenario and briefing (which the DIRECTOR sees, to pick who speaks next), the shared ground (which EVERYONE in the channel holds), each person's own grounding, and the turn budget.

Worth keeping in mind while reading:

1. **This is today, not history.** Everyone is told the state as of that morning.
2. **MUST RAISE** belongs to the person driving it; the engine holds the conversation open until it lands. **MUST SETTLE** is a planted clue: the engine pushes for it to be stated as a conclusion, and a channel-day that does not get its INFORMATION across is run again — told what was missing. The words are the persona's own; what is fixed is the point, and any identifier named under it.
3. **The forbidden list does not exist yet** on that date. Naming it is the failure this whole pipeline is built to prevent.


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
# 2025-03-10 — 4 conversation(s), 40 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #general — 8 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #general: Two new contractors are joining; Konrad Feltrin has onboarding materials and Dario Kestrel is welcoming them to the team

    Today is Monday 10 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two new contractors are joining; Konrad Feltrin has onboarding materials and Dario Kestrel is welcoming them to the team
    
    What it should get through:
      1. Nils receives setup and context for batch-mode work   [Konrad Feltrin must raise this]
           - Konrad shares onboarding doc and initial pointers
           - Nils acknowledges and asks clarifying questions
           - Emil adds note on batch-processor structure already in flight
    
    On the agenda: Konrad posts onboarding notes for Nils Brandt and Theo Marchetti; Dario's welcome message adds context on the team structure; Brief snapshot of current batch-mode and provider work
    
    Belongs in this channel: news the whole company needs: releases that matter to everyone, scheduling, people joining or moving on, and decisions that cross every team.
    Does NOT belong here: work on any individual service, and anything only one team cares about.
    
    Wrap when: Nils has the onboarding material, knows where the batch-mode work stands, and is ready to integrate into the codebase.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 285 changes merged to date

    On the table
      - onboarding-Nils Brandt (Konrad Feltrin)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 571: Feat/raft (Emil Brandvold)
      - PR 575: fix: use model name from config in  cost processor (Emil Brandvold)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates
      - issue 128: curator-viewer doesn't display the output of parse_func
      - issue 207: implementation of `has_capacity` using rate limit info from the headers returned from some providers/models
      - issue 233: Automatically detect the rate limits

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 465 function/class names and 13 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Konrad's setup notes for the incoming batch-backend contractor and the Mistral-batch examples contributor
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Nils receives setup and context for batch-mode work   *** MUST RAISE ***
      2. what "Onboarding: nils and theo" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Nils receives setup and context for batch-mode work
    available   around today

  Nils Brandt  (nils)
    role        Batch Backend Engineer (short-term contract). Presence as new contractor starting batch-mode work
    owns        batch-mode, provider-integrations
    agenda
      1. Nils receives setup and context for batch-mode work
    goal        Two new contractors are joining; Konrad Feltrin has onboarding materials and Dario Kestrel is welcoming them to the team
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Welcome message extending Konrad Feltrin's onboarding to the full team
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Nils receives setup and context for batch-mode work
    goal        Two new contractors are joining; Konrad Feltrin has onboarding materials and Dario Kestrel is welcoming them to the team
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Current state of the work Nils Brandt is joining into
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Nils receives setup and context for batch-mode work
    goal        Two new contractors are joining; Konrad Feltrin has onboarding materials and Dario Kestrel is welcoming them to the team
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Nils has the onboarding material, knows where the batch-mode work stands, and is ready to integrate into the codebase.


------------------------------------------------------------------------------
## #pipeline — 12 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Nils has committed 6 commits on Mistral batch processor in the first day; the structure and approach need eyes before he builds further

    Today is Monday 10 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Nils has committed 6 commits on Mistral batch processor in the first day; the structure and approach need eyes before he builds further
    
    What it should get through:
      1. Batch processor request/response parsing direction is confirmed or redirected   [Nils Brandt must raise this]
           - Nils shows the request parsing and response mapping flow
           - Emil spots alignment or asks about deviations from other batch processors
           - Group agrees on next steps or flags rework needed before file upload
      2. Token accounting approach for Mistral batch is settled   [Gideon Halloway must raise this]
           - Gideon asks how tokenUsage is being parsed and stored
           - Nils explains the current implementation
           - Group decides if immediate-response cost calc or batch-result polling needed
    
    On the agenda: Nils walks through the batch processor structure and parsing logic; Group assesses whether request/response mapping matches existing patterns; Talk through token accounting and cost implications
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Nils knows whether his batch processor structure is sound and has clarity on token accounting before the next round of commits.
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 285 changes merged to date

    On the table
      - onboarding-Nils Brandt (Konrad Feltrin)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 571: Feat/raft (Emil Brandvold)
      - PR 575: fix: use model name from config in  cost processor (Emil Brandvold)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates
      - issue 128: curator-viewer doesn't display the output of parse_func
      - issue 207: implementation of `has_capacity` using rate limit info from the headers returned from some providers/models
      - issue 233: Automatically detect the rate limits

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 465 function/class names and 13 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Nils Brandt  (nils)
    role        Batch Backend Engineer (short-term contract). Six commits building Mistral batch processor: request parsing, response handling, file upload, batch creation
    owns        batch-mode, provider-integrations
    agenda
      1. Batch processor request/response parsing direction is confirmed or redirected   *** MUST RAISE ***
      2. Token accounting approach for Mistral batch is settled
      3. what "Onboarding: nils and theo" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Batch processor request/response parsing direction is confirmed or redirected
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Context on how previous batch processors were structured; patterns for request/response mapping
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Batch processor request/response parsing direction is confirmed or redirected
      2. Token accounting approach for Mistral batch is settled
    goal        Nils has committed 6 commits on Mistral batch processor in the first day; the structure and approach need eyes before he builds further
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. High-level shape of how batch processors fit into provider-integrations
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Batch processor request/response parsing direction is confirmed or redirected
      2. Token accounting approach for Mistral batch is settled
    goal        Nils has committed 6 commits on Mistral batch processor in the first day; the structure and approach need eyes before he builds further
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Rate-limit and cost-accounting implications of batch APIs
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Batch processor request/response parsing direction is confirmed or redirected
      2. Token accounting approach for Mistral batch is settled   *** MUST RAISE ***
    goal        Token accounting approach for Mistral batch is settled
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Nils knows whether his batch processor structure is sound and has clarity on token accounting before the next round of commits.


------------------------------------------------------------------------------
## #cookbooks — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #cookbooks: Emil is driving ws-044 (RAFT block cleanup and finetuning example) which is at kickoff; the PR has been under review with 11 comments from both Emil Brandvold and Konrad Feltrin, and the design doc was posted 2025-03-07

    Today is Monday 10 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Emil is driving ws-044 (RAFT block cleanup and finetuning example) which is at kickoff; the PR has been under review with 11 comments from both Emil Brandvold and Konrad Feltrin, and the design doc was posted 2025-03-07
    
    What it should get through:
      1. RAFT block data schema cleanup is approved or iteration is clear   [Emil Brandvold must raise this]
           - Emil explains the schema changes and why they were needed
           - Konrad pushes back or validates the new shape
           - Group agrees it's ready or flags what needs one more pass
      2. Finetuning example demonstrates the end-to-end shape   [Emil Brandvold must raise this]
           - Emil shows what the example teaches: generated data → finetuning → sampling
           - Konrad/Dario Kestrel assess whether the example is clear enough for cookbooks
           - Outcome: example is ready to ship or needs one more refinement
      3. write up Onboarding: Nils Brandt and Theo Marchetti   [Konrad Feltrin must raise this]
           - Konrad Feltrin says they will write Onboarding: Nils Brandt and Theo Marchetti — Konrad's setup notes for the incoming batch-backend contractor and the Mistral-batch examples contributor.
    
    On the agenda: Emil walks through the RAFT block cleanup and what changed in the data schema; Review of the finetuning example and what it teaches users; Integration test setup and whether it's ready for CI; Onboarding: Nils Brandt and Theo Marchetti
    
    Out today: Nikolai Berresford (no commit, review or comment 2025-02-27..2025-03-15) — their input is missing and people may say so
    
    No longer here: Priya Vandersloot — do not expect them back or wait on them
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: PR 571 can move forward with clarity on whether the schema cleanup and example shape are ready, or what one more pass looks like.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 285 changes merged to date

    On the table
      - WS-044: Blocks & Recipes (RAFT, SimpleStrat) (Emil Brandvold)
      - Onboarding: Nils Brandt and Theo Marchetti (Konrad Feltrin)
      - weekly-2025-03-03 (Konrad Feltrin)
      - welcome-Nils Brandt-2025-03-10 (Konrad Feltrin)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 571: Feat/raft (Emil Brandvold)
      - PR 575: fix: use model name from config in  cost processor (Emil Brandvold)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates
      - issue 128: curator-viewer doesn't display the output of parse_func
      - issue 207: implementation of `has_capacity` using rate limit info from the headers returned from some providers/models
      - issue 233: Automatically detect the rate limits

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 465 function/class names and 13 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Five commits on RAFT block: data schema cleanup, finetuning example, multimodal reqs, OCR backend support, integration test
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. RAFT block data schema cleanup is approved or iteration is clear   *** MUST RAISE ***
      2. Finetuning example demonstrates the end-to-end shape   *** MUST RAISE ***
      3. write up Onboarding: Nils Brandt and Theo Marchetti
      4. what "WS-044: Blocks & Recipes (RAFT, SimpleStrat)" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        RAFT block data schema cleanup is approved or iteration is clear
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Perspective on the data schema cleanup and whether it satisfies the gaps from the previous iteration
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. RAFT block data schema cleanup is approved or iteration is clear
      2. Finetuning example demonstrates the end-to-end shape
      3. write up Onboarding: Nils Brandt and Theo Marchetti   *** MUST RAISE ***
      4. the page you are writing, Onboarding: nils and theo, has to say this in your own words: Reminder on the Sandbox Image Release Log: the promoted line on this page is the only statement of which curator-sandbox build has actually been signed off. The registry tag list is not curated, CI pushes a tag for every branch build and the sort order there means nothing. If you need to know what is safe to run, read this page, do not read the registry.   *** MUST SETTLE (clue t4.r1.L1) ***
         must contain literally: curator-sandbox
      5. that the doc "Onboarding: nils and theo" is done, and where the others can find it   *** MUST RAISE ***
      6. that "Weekly update: week of Mar 3" has gone out, and what you asked in it   *** MUST RAISE ***
      7. that "Welcome nils (and theo)" has gone out, and what you asked in it   *** MUST RAISE ***
    goal        write up Onboarding: Nils Brandt and Theo Marchetti
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. CI/release readiness perspective on the RAFT example and new integration test
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. RAFT block data schema cleanup is approved or iteration is clear
      2. Finetuning example demonstrates the end-to-end shape
      3. write up Onboarding: Nils Brandt and Theo Marchetti
    goal        Emil is driving ws-044 (RAFT block cleanup and finetuning example) which is at kickoff; the PR has been under review with 11 comments from both Emil Brandvold and Konrad Feltrin, and the design doc was posted 2025-03-07
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 571 can move forward with clarity on whether the schema cleanup and example shape are ready, or what one more pass looks like.


------------------------------------------------------------------------------
## #code-review — 10 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: 9 PRs are open and older than the era's median merge time (6.6h); 6 are marked as stale; Emil Brandvold has 3 PRs waiting and reviewed heavily today; Nils Brandt' first batch of commits are likely to PR soon

    Today is Monday 10 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 9 PRs are open and older than the era's median merge time (6.6h); 6 are marked as stale; Emil Brandvold has 3 PRs waiting and reviewed heavily today; Nils Brandt' first batch of commits are likely to PR soon
    
    What it should get through:
      1. RAFT and cost processor PR review feedback is current or next   [Emil Brandvold must raise this]
           - Emil flags the RAFT (571), cost processor (575), and payload PRs as priority
           - Konrad confirms he can turn around review on RAFT and cost processor
           - Group agrees on whether to gate Dario Kestrel's backend PRs behind RAFT landing
      2. Nils knows review expectations for batch-mode PRs   [Nils Brandt must raise this]
           - Nils asks about the review cycle for batch processor PRs
           - Emil explains the pattern: structural review early, then test coverage sweep
           - Outcome: Nils Brandt knows to post early and expect iterative feedback
    
    On the agenda: Snapshot of which PRs are blocking what; Review priorities given the week's workstreams; Expectations for Nils Brandt' batch-mode PRs
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Review priorities are clear, Nils Brandt knows how PRs flow through the team, and blockers on Dario Kestrel's backend PRs are identified; it is settled that the team agrees new code should go through supports_structured_output rather than adding its own set of model names
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 285 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 571: Feat/raft (Emil Brandvold)
      - PR 575: fix: use model name from config in  cost processor (Emil Brandvold)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 105: Distribution graph is skewed for data viewer 
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates
      - issue 128: curator-viewer doesn't display the output of parse_func
      - issue 207: implementation of `has_capacity` using rate limit info from the headers returned from some providers/models
      - issue 233: Automatically detect the rate limits

    DOES NOT EXIST YET (3 names)
      - agentic-curation
      - finetuning
      - — and 465 function/class names and 13 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in. These DO exist today and are yours to name: supports_structured_output.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Multiple PRs in flight: RAFT block (571), cost processor fix (575), and payload handling (582)
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. RAFT and cost processor PR review feedback is current or next   *** MUST RAISE ***
      2. Nils knows review expectations for batch-mode PRs
    goal        RAFT and cost processor PR review feedback is current or next
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Context on the RAFT cleanup design and cost processor semantics
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. RAFT and cost processor PR review feedback is current or next
      2. Nils knows review expectations for batch-mode PRs
    goal        9 PRs are open and older than the era's median merge time (6.6h); 6 are marked as stale; Emil Brandvold has 3 PRs waiting and reviewed heavily today; Nils Brandt' first batch of commits are likely to PR soon
    available   around today

  Nils Brandt  (nils)
    role        Batch Backend Engineer (short-term contract). Mistral batch work now in PRs; new to the codebase and unfamiliar with the review process
    owns        batch-mode, provider-integrations
    agenda
      1. RAFT and cost processor PR review feedback is current or next
      2. Nils knows review expectations for batch-mode PRs   *** MUST RAISE ***
    goal        Nils knows review expectations for batch-mode PRs
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. OpenAI and DeepSeek backend PRs (565, 566) waiting on provider-integrations review
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. RAFT and cost processor PR review feedback is current or next
      2. Nils knows review expectations for batch-mode PRs
      3. Left a comment on the kluster PR: drop the set of model names you added and call supports_structured_output instead. That helper is already what we edit when a new model lands, and I don't want to be grepping for model strings again next time o3-mini ships.   *** MUST SETTLE (clue t2.r2.l7) ***
         must contain literally: supports_structured_output
    goal        the team agrees new code should go through supports_structured_output rather than adding its own set of model names
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Review priorities are clear, Nils Brandt knows how PRs flow through the team, and blockers on Dario Kestrel's backend PRs are identified; it is settled that the team agrees new code should go through supports_structured_output rather than adding its own set of model names

