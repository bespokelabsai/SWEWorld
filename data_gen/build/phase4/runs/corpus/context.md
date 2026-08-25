# Phase 4: what the simulation is told

Four things reach a model: the channel scenario and briefing (which the DIRECTOR sees, to pick who speaks next), the shared ground (which EVERYONE in the channel holds), each person's own grounding, and the turn budget.

Worth keeping in mind while reading:

1. **This is today, not history.** Everyone is told the state as of that morning.
2. **MUST RAISE** belongs to the person driving it; the engine holds the conversation open until it lands. **MUST SETTLE** is a planted clue: the engine pushes for it to be stated as a conclusion, and a channel-day that does not get its INFORMATION across is run again — told what was missing. The words are the persona's own; what is fixed is the point, and any identifier named under it.
3. **The forbidden list does not exist yet** on that date. Naming it is the failure this whole pipeline is built to prevent.


==============================================================================
# 2025-03-06 — 3 conversation(s), 32 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: PR 578 merged today needs code-review closure; PR 581 opened and needs first review; five older PRs are stale and need strategy

    Today is Thursday 6 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: PR 578 merged today needs code-review closure; PR 581 opened and needs first review; five older PRs are stale and need strategy
    
    What it should get through:
      1. Confirm PR 578 merge is complete and document the three-part Gemini landing   [Emil Brandvold must raise this]
           - Emil summarizes what merged (578) and what landed alongside it (failed-count fix, batch example)
           - Gideon or Dario confirms all three pieces are in and no rollback needed
           - Group agrees the Gemini rate limit story is closed
      2. Get PR 581 into review queue and identify blockers on 565/566   [Gideon Halloway must raise this]
           - Gideon walks through PR 581 implementation and context from PR 580
           - Emil or Dario notes whether it conflicts with other in-flight work
           - Group agrees if it is safe to merge or needs a dependency
    
    On the agenda: Review and merge PR 578 (Gemini rate limits); Assess PR 581 (Environment variable to disable rich) readiness; Decide on stale PR unblocking strategy
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 578 confirmed merged; PR 581 assigned reviewer; decision made on whether to unblock 565/566 before continuing
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 285 changes merged to date

    On the table
      - Weekly Notes — Week of Mar 3 (Emil Brandvold)
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
    role        Core Platform Engineer, Request Processing. Gemini rate limit handling and token-usage field fixes; context on the three-part landing (PR 578, failed-count fix, batch example)
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm PR 578 merge is complete and document the three-part Gemini landing   *** MUST RAISE ***
      2. Get PR 581 into review queue and identify blockers on 565/566
      3. what "Weekly Notes — Week of Mar 3" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm PR 578 merge is complete and document the three-part Gemini landing
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Fresh eyes on environment variable implementation; understanding of CLI-disabling use case
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm PR 578 merge is complete and document the three-part Gemini landing
      2. Get PR 581 into review queue and identify blockers on 565/566   *** MUST RAISE ***
    goal        Get PR 581 into review queue and identify blockers on 565/566
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Perspective on OpenAI/DeepSeek API work blocking; seniority to guide merge strategy
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm PR 578 merge is complete and document the three-part Gemini landing
      2. Get PR 581 into review queue and identify blockers on 565/566
    goal        PR 578 merged today needs code-review closure; PR 581 opened and needs first review; five older PRs are stale and need strategy
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 578 confirmed merged; PR 581 assigned reviewer; decision made on whether to unblock 565/566 before continuing


------------------------------------------------------------------------------
## #engineering — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: PR 578 merged today closes a workstream; PR 581 opened; team is in the consolidation phase of the sprint and needs to know what just shipped

    Today is Thursday 6 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: PR 578 merged today closes a workstream; PR 581 opened; team is in the consolidation phase of the sprint and needs to know what just shipped
    
    What it should get through:
      1. Mark end of Gemini rate limits workstream and highlight the batch example users should follow   [Emil Brandvold must raise this]
           - Emil flags that Gemini rate limit handling is now in place and PR 578 is merged
           - Emil points to the new batch example (ep-e4b3066065c7) as the reference for users
           - Team acknowledges and notes it for documentation or blog
      2. Unblock OpenAI and DeepSeek client work by assessing the stale PR situation   [Dario Kestrel must raise this]
           - Dario notes that PRs 565 and 566 (OpenAI, DeepSeek) are now 4 days stale
           - Emil or Gideon raises whether Gemini landing clears the way for those to merge
           - Group decides: do those PRs need to be pulled forward or can they wait for the next release window
    
    On the agenda: Celebrate Gemini rate limits landing and point to the batch example; Brief update on environment variable for rich CLI; Briefly frame next provider integrations work (OpenAI, DeepSeek clients)
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team knows Gemini rate limits are live and batch example is the reference; OpenAI/DeepSeek client PR status is explicit
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 285 changes merged to date

    On the table
      - Q2 Plan: Consolidation and Provider Breadth (Konrad Feltrin)
      - Q2 Plan: Consolidation and Provider Breadth (Konrad Feltrin)
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
    role        Core Platform Engineer, Request Processing. Completion of Gemini rate limit handling; awareness of token-usage field work; context on the three-part landing and what users can do now
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Mark end of Gemini rate limits workstream and highlight the batch example users should follow   *** MUST RAISE ***
      2. Unblock OpenAI and DeepSeek client work by assessing the stale PR situation
      3. what "Q2 Plan: Consolidation and Provider Breadth" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Mark end of Gemini rate limits workstream and highlight the batch example users should follow
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. New environment-variable pattern for disabling rich; perspective on observability/CLI flexibility
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Mark end of Gemini rate limits workstream and highlight the batch example users should follow
      2. Unblock OpenAI and DeepSeek client work by assessing the stale PR situation
    goal        PR 578 merged today closes a workstream; PR 581 opened; team is in the consolidation phase of the sprint and needs to know what just shipped
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Broader provider API perspective; unblocking strategy for 565 and 566 (OpenAI and DeepSeek clients)
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Mark end of Gemini rate limits workstream and highlight the batch example users should follow
      2. Unblock OpenAI and DeepSeek client work by assessing the stale PR situation   *** MUST RAISE ***
      3. what "Q2 Plan: Consolidation and Provider Breadth" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Unblock OpenAI and DeepSeek client work by assessing the stale PR situation
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team knows Gemini rate limits are live and batch example is the reference; OpenAI/DeepSeek client PR status is explicit


------------------------------------------------------------------------------
## #viewer — 14 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #viewer: Gideon Halloway tried the draft with the progress display on and the exception came out mangled underneath a half-drawn progress bar

    Today is Thursday 6 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Gideon Halloway tried the draft with the progress display on and the exception came out mangled underneath a half-drawn progress bar
    
    What it should get through:
    
    On the agenda: Gideon Halloway shows the mangled output: the bars had already been started, so the traceback interleaved with them and the useful line scrolled off; Emil Brandvold notes the end-of-run summary table also printed with zeroes across it, which reads like a run that did nothing rather than a run that was refused; Dario Kestrel says if the thing is refused it should be refused before any of that furniture is on screen, so the message is the only thing the user sees
    
    Wrap when: consensus that the failure should land before the display is initialised; whether the summary table is suppressed or fixed is left to Gideon Halloway; it is settled that the team agrees a startup rejection has to surface a message naming what was rejected
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

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
      - — and 465 function/class names and 13 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. 
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Heads up from the CLI side: when a docker task dies at container start, all the progress table gets is the task marked failed plus a container id. People screenshot it and send it to me and I have nothing to tell them. If we are going to start having creates rejected, whatever text comes back needs to name the setting that was rejected or it lands in my inbox instead.   *** MUST SETTLE (clue t4.r2.L11) ***
    goal        the team agrees a startup rejection has to surface a message naming what was rejected
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. 
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
    goal        Gideon Halloway tried the draft with the progress display on and the exception came out mangled underneath a half-drawn progress bar
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
    goal        Gideon Halloway tried the draft with the progress display on and the exception came out mangled underneath a half-drawn progress bar
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   consensus that the failure should land before the display is initialised; whether the summary table is suppressed or fixed is left to Gideon Halloway; it is settled that the team agrees a startup rejection has to surface a message naming what was rejected


==============================================================================
# 2025-03-07 — 2 conversation(s), 18 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Two PRs opened today; six older PRs stale; need to clear the mime_type change before it cascades into multimodal and backend work.

    Today is Friday 7 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two PRs opened today; six older PRs stale; need to clear the mime_type change before it cascades into multimodal and backend work.
    
    What it should get through:
      1. Approve PR 582 or identify blockers   [Emil Brandvold must raise this]
           - Emil explains the Image type changes and their reach into batch/bulk/online
           - Dario or Gideon ask whether float-to-int wrapping for litellm is in scope
           - Land or defer
      2. Clarify PR 583 scope and release impact   [Emil Brandvold must raise this]
           - Emil reports that Nikolai Berresford opened PR 583 to disable metadata db via param
           - Check whether it blocks v0.1.20 or defers to next
           - Defer or queue for merge
    
    On the agenda: PR 582 mime_type extraction and its multimodal surface; PR 583 metadata db toggle and release readiness; Whether either blocks Dario Kestrel's backend PRs
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 582 approved or returned with clear feedback; PR 583 scoped as blocking or deferrable; Dario Kestrel unblocked on whether to merge his own backends before or after.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 285 changes merged to date

    On the table
      - Weekly Notes — Week of Mar 3 (Emil Brandvold)
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
    role        Core Platform Engineer, Request Processing. Just shipped mime_type extraction across multimodal types and opened PR 582; also driving cost processor cleanup (ws-042)
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Approve PR 582 or identify blockers   *** MUST RAISE ***
      2. Clarify PR 583 scope and release impact   *** MUST RAISE ***
      3. that the doc "WS-044: Blocks & Recipes (RAFT, SimpleStrat)" is done, and where the others can find it   *** MUST RAISE ***
      4. what "Weekly Notes — Week of Mar 3" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Approve PR 582 or identify blockers
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Owns request processing; context on whether backend client PRs (PR 565, PR 566) need anything from these multimodal changes
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Approve PR 582 or identify blockers
      2. Clarify PR 583 scope and release impact
    goal        Two PRs opened today; six older PRs stale; need to clear the mime_type change before it cascades into multimodal and backend work.
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR 582 approved or returned with clear feedback; PR 583 scoped as blocking or deferrable; Dario Kestrel unblocked on whether to merge his own backends before or after.


------------------------------------------------------------------------------
## #pipeline — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Three services touched by today's commits; cost estimation revamp (ws-038) mid-flight; need to confirm mime_type and token-handling fixes thread cleanly into request processing.

    Today is Friday 7 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Three services touched by today's commits; cost estimation revamp (ws-038) mid-flight; need to confirm mime_type and token-handling fixes thread cleanly into request processing.
    
    What it should get through:
      1. Confirm mime_type threading is complete across batch/online   [Emil Brandvold must raise this]
           - Emil walks image handling through batch/bulk paths
           - Gideon or Dario ask whether multimodal requests need extra marshalling
           - Confirm coverage or flag missing links
      2. Validate int wrapping fixes deepseek dump   [Gideon Halloway must raise this]
           - Gideon reports kluster deepseek soak was hitting output-token default 0 dump
           - Emil confirms int(estimate) wrapping is in PR 582
           - Schedule next soak or defer to next batch of provider work
    
    On the agenda: Emil's mime_type extraction and multimodal handling across batch/bulk/online; Int wrapping for litellm token estimates and deepseek backpressure; Cost projection with success factor (ws-038 mid-flight)
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Mime_type threading confirmed complete; int wrapping validated as addressing deepseek backpressure; Gideon Halloway has a clear next-step for cost estimation revamp soak.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 285 changes merged to date

    On the table
      - Weekly Notes — Week of Mar 3 (Emil Brandvold)
      - Postmortem: kluster.ai DeepSeek Output-Token Default (Emil Brandvold)
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
    role        Core Platform Engineer, Request Processing. Just landed mime_type extraction on Image; int-wrapping fix for litellm float token estimates; raft schema update for blocks-and-recipes
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm mime_type threading is complete across batch/online   *** MUST RAISE ***
      2. Validate int wrapping fixes deepseek dump
      3. what "Weekly Notes — Week of Mar 3" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm mime_type threading is complete across batch/online
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Diagnosed the deepseek output-token default dump in kluster testing; knows what cost estimation revamp needs
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm mime_type threading is complete across batch/online
      2. Validate int wrapping fixes deepseek dump   *** MUST RAISE ***
      3. what "Postmortem: kluster.ai DeepSeek Output-Token Default" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Validate int wrapping fixes deepseek dump
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Owns the full request path; context on whether these changes affect batch mode or online concurrency
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm mime_type threading is complete across batch/online
      2. Validate int wrapping fixes deepseek dump
    goal        Three services touched by today's commits; cost estimation revamp (ws-038) mid-flight; need to confirm mime_type and token-handling fixes thread cleanly into request processing.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Mime_type threading confirmed complete; int wrapping validated as addressing deepseek backpressure; Gideon Halloway has a clear next-step for cost estimation revamp soak.


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


==============================================================================
# 2025-03-11 — 3 conversation(s), 29 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Three new PRs opened today need eyes; token wrapping and mime type fixes are blocking batch mode work

    Today is Tuesday 11 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Three new PRs opened today need eyes; token wrapping and mime type fixes are blocking batch mode work
    
    What it should get through:
      1. Confirm int wrapping of litellm token estimates fixes rate limiter backpressure   [Gideon Halloway must raise this]
           - Gideon Halloway raises the deepseek zero-default token problem from postmortem-2025-03-01
           - Emil Brandvold walks through the int wrapping fix in PR 586
           - Konrad Feltrin checks test coverage for the change
      2. Land MIME type extraction so Image types carry format info to providers   [Emil Brandvold must raise this]
           - Emil Brandvold flags Image types weren't carrying mime_type, causing provider rejection on some formats
           - Konrad Feltrin asks about backward compatibility with existing Image objects
           - Gideon Halloway confirms the default fallback covers the gap
    
    On the agenda: Token estimate type safety in rate limiter; Image MIME type propagation through batch backends; Review status of PR 585 and PR 586
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 586 approved and merged; PR 585 queued for next review cycle pending team capacity; mime type extraction unblocks batch processing for image prompts
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 287 changes merged to date

    On the table
      - Postmortem: kluster.ai DeepSeek Output-Token Default (someone)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 571: Feat/raft (Emil Brandvold)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 581: Environment variable to disable rich (Gideon Halloway)

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
      - — and 464 function/class names and 13 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. litellm backend token estimate wrapping and mime_type extraction from Image objects
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm int wrapping of litellm token estimates fixes rate limiter backpressure
      2. Land MIME type extraction so Image types carry format info to providers   *** MUST RAISE ***
    goal        Land MIME type extraction so Image types carry format info to providers
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. structured output path knowledge and test coverage around input handling
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm int wrapping of litellm token estimates fixes rate limiter backpressure
      2. Land MIME type extraction so Image types carry format info to providers
    goal        Three new PRs opened today need eyes; token wrapping and mime type fixes are blocking batch mode work
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. rate limiter internals and the deepseek backpressure issue context
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm int wrapping of litellm token estimates fixes rate limiter backpressure   *** MUST RAISE ***
      2. Land MIME type extraction so Image types carry format info to providers
      3. what "postmortem-2025-03-01" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm int wrapping of litellm token estimates fixes rate limiter backpressure
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR 586 approved and merged; PR 585 queued for next review cycle pending team capacity; mime type extraction unblocks batch processing for image prompts


------------------------------------------------------------------------------
## #engineering — 7 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Four commits to multimodal-prompts today; mime type fix is landing and needs team alignment

    Today is Tuesday 11 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Four commits to multimodal-prompts today; mime type fix is landing and needs team alignment
    
    What it should get through:
      1. Validate MIME type defaults won't cause regression for existing image prompts   [Emil Brandvold must raise this]
           - Emil Brandvold walks through the default mime type fallback logic
           - Konrad Feltrin raises cookbook examples that might be affected
           - Gideon Halloway confirms bulk path handles the default cleanly
      2. Confirm raft readme update captures the current recipe state   [Emil Brandvold must raise this]
           - Emil Brandvold notes the readme was updated as part of the sprint
           - Konrad Feltrin skims for completeness
           - decision to update docs after next release instead
    
    On the agenda: MIME type extraction and defaults in Image; RAFT readme update adequacy; Multimodal test coverage before next release
    
    No longer here: Priya Vandersloot — do not expect them back or wait on them
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team agrees mime type defaults are safe; raft readme deferred to next doc pass; multimodal surface stable for release
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 287 changes merged to date

    On the table
      - WS-044: Blocks & Recipes (RAFT, SimpleStrat) (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 571: Feat/raft (Emil Brandvold)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 581: Environment variable to disable rich (Gideon Halloway)

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
      - — and 464 function/class names and 13 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. mime type extraction work and the four commits touching multimodal today
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Validate MIME type defaults won't cause regression for existing image prompts   *** MUST RAISE ***
      2. Confirm raft readme update captures the current recipe state   *** MUST RAISE ***
      3. what "WS-044: Blocks & Recipes (RAFT, SimpleStrat)" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Validate MIME type defaults won't cause regression for existing image prompts
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. cookbook integration perspective and raft design context
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Validate MIME type defaults won't cause regression for existing image prompts
      2. Confirm raft readme update captures the current recipe state
    goal        Four commits to multimodal-prompts today; mime type fix is landing and needs team alignment
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. bulk inference path through multimodal prompts
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Validate MIME type defaults won't cause regression for existing image prompts
      2. Confirm raft readme update captures the current recipe state
    goal        Four commits to multimodal-prompts today; mime type fix is landing and needs team alignment
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Team agrees mime type defaults are safe; raft readme deferred to next doc pass; multimodal surface stable for release


------------------------------------------------------------------------------
## #cookbooks — 14 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #cookbooks: the RAFT block and the SimpleStrat recipe construct their Pydantic models dynamically, so any check that assumes a hand-written class needs to cope

    Today is Tuesday 11 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: the RAFT block and the SimpleStrat recipe construct their Pydantic models dynamically, so any check that assumes a hand-written class needs to cope
    
    What it should get through:
    
    On the agenda: Emil Brandvold explains how the SimpleStrat auto-stratification builds its model from the discovered strata, so the field set is not known until the recipe runs; Dermot Callaghan brings up the recipe-generation example, which uses a free-form dict for the ingredient map, and says he already had to flatten it once for a provider and would rather be told up front than flatten it again mid-run; Dario Kestrel asks whether recipes should get to opt out or whether they should just stop producing schemas that only work on one provider
    
    Wrap when: no decision; Emil Brandvold will list which of the shipped blocks and recipes would fail the draft check today; it is settled that the team agrees a dynamically built response model currently aborts the run in the lookup pass
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 287 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 571: Feat/raft (Emil Brandvold)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 581: Environment variable to disable rich (Gideon Halloway)

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
      - — and 464 function/class names and 13 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in. These DO exist today and are yours to name: TypeError: unhashable type, create_model.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
    goal        the RAFT block and the SimpleStrat recipe construct their Pydantic models dynamically, so any check that assumes a hand-written class needs to cope
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. 
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
    goal        the RAFT block and the SimpleStrat recipe construct their Pydantic models dynamically, so any check that assumes a hand-written class needs to cope
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. 
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. SimpleStrat builds its response model at runtime with pydantic create_model, and the lookup pass dies on it: TypeError: unhashable type. Run is dead at row zero, before a single request goes out. Traceback in thread.   *** MUST SETTLE (clue t1.r1.l_unhash_1) ***
         must contain literally: create_model, TypeError: unhashable type
    goal        the team agrees a dynamically built response model currently aborts the run in the lookup pass
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   no decision; Emil Brandvold will list which of the shipped blocks and recipes would fail the draft check today; it is settled that the team agrees a dynamically built response model currently aborts the run in the lookup pass


==============================================================================
# 2025-03-12 — 4 conversation(s), 41 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 10 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: 6 PRs older than the era's median merge time; need triage and decision

    Today is Wednesday 12 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 6 PRs older than the era's median merge time; need triage and decision
    
    What it should get through:
      1. Clear PR 571 and related RAFT work   [Emil Brandvold must raise this]
           - Emil walks through PR 571 RAFT merge status and related commits
           - Konrad asks about docs/example alignment
           - Decision: lands today or wait for secondary review
      2. Unblock batch-mode and provider-integrations queue   [Nils Brandt must raise this]
           - Nils flags PR 584 and PR 585 status
           - Team discusses what's blocking each
           - Assign next reviewer or defer if dependencies unclear
      3. Decide on OpenAI/DeepSeek backend timeline   [Dario Kestrel must raise this]
           - Dario updates on PR 565 and PR 566 age
           - Konrad checks if these can land in consolidation phase or need next sprint
           - Clear next step or defer
    
    On the agenda: RAFT block and multimodal PRs: what's ready; Batch and provider-integrations stale work: blockers; OpenAI/DeepSeek backend status
    
    Meeting today: Weekly sync
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: RAFT lands same day; batch/provider-integrations PRs either get assigned a reviewer or move to next week's queue; OpenAI/DeepSeek timeline clarified
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 288 changes merged to date

    On the table
      - WS-044: Blocks & Recipes (RAFT, SimpleStrat) (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 581: Environment variable to disable rich (Gideon Halloway)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)

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
      - — and 436 function/class names and 0 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Just landed RAFT block; context on multimodal-prompts and release-and-ci changes
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Clear PR 571 and related RAFT work   *** MUST RAISE ***
      2. Unblock batch-mode and provider-integrations queue
      3. Decide on OpenAI/DeepSeek backend timeline
      4. what "WS-044: Blocks & Recipes (RAFT, SimpleStrat)" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Clear PR 571 and related RAFT work
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Founding maintainer perspective; can clear blockages
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Clear PR 571 and related RAFT work
      2. Unblock batch-mode and provider-integrations queue
      3. Decide on OpenAI/DeepSeek backend timeline
    goal        6 PRs older than the era's median merge time; need triage and decision
    available   around today

  Nils Brandt  (nils)
    role        Batch Backend Engineer (short-term contract). Recent batch and provider-integrations work; knows constraints
    owns        batch-mode, provider-integrations
    agenda
      1. Clear PR 571 and related RAFT work
      2. Unblock batch-mode and provider-integrations queue   *** MUST RAISE ***
      3. Decide on OpenAI/DeepSeek backend timeline
      4. that the doc "Weekly Notes — Week of Mar 10" is done, and where the others can find it   *** MUST RAISE ***
    goal        Unblock batch-mode and provider-integrations queue
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Owns request-processing stack; OpenAI/DeepSeek client backend context
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Clear PR 571 and related RAFT work
      2. Unblock batch-mode and provider-integrations queue
      3. Decide on OpenAI/DeepSeek backend timeline   *** MUST RAISE ***
    goal        Decide on OpenAI/DeepSeek backend timeline
    available   around today

### 4. How it should land

    lands as  partial
    leaving   RAFT lands same day; batch/provider-integrations PRs either get assigned a reviewer or move to next week's queue; OpenAI/DeepSeek timeline clarified


------------------------------------------------------------------------------
## #engineering — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: 2 commits to multimodal-prompts (token wrapping, prompt__internal) need context before they propagate

    Today is Wednesday 12 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 2 commits to multimodal-prompts (token wrapping, prompt__internal) need context before they propagate
    
    What it should get through:
      1. Validate token estimate int wrapping fix   [Emil Brandvold must raise this]
           - Emil explains the bug (litellm returning float)
           - Dario asks if structured output tests cover this
           - Confirm fix is safe or flag test gap
      2. Confirm prompt__internal scope is safe   [Konrad Feltrin must raise this]
           - Konrad questions the scope of prompt__internal change
           - Emil walks through where it is and is not used
           - Land on: safe to proceed or needs audit
    
    On the agenda: Token estimate wrapping in litellm backend; prompt__internal usage pattern; Multimodal test coverage on these changes
    
    Meeting today: Weekly sync
    
    No longer here: Priya Vandersloot — do not expect them back or wait on them
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Token wrapping and prompt__internal changes are validated as safe; team has confidence in multimodal-prompts test coverage
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 288 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 581: Environment variable to disable rich (Gideon Halloway)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)

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
      - — and 436 function/class names and 0 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Just landed RAFT; owns multimodal-prompts; knows impact of prompt__internal change and token wrapping fix
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Validate token estimate int wrapping fix   *** MUST RAISE ***
      2. Confirm prompt__internal scope is safe
    goal        Validate token estimate int wrapping fix
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Founding context; can spot API surface issues
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Validate token estimate int wrapping fix
      2. Confirm prompt__internal scope is safe   *** MUST RAISE ***
    goal        Confirm prompt__internal scope is safe
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Request-processing perspective; knows downstream consumers
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Validate token estimate int wrapping fix
      2. Confirm prompt__internal scope is safe
    goal        2 commits to multimodal-prompts (token wrapping, prompt__internal) need context before they propagate
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Token wrapping and prompt__internal changes are validated as safe; team has confidence in multimodal-prompts test coverage


------------------------------------------------------------------------------
## #pipeline — 9 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: 3 commits each to batch-mode and provider-integrations; PR 584 (Mistral) is 1 day old and needs review

    Today is Wednesday 12 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 3 commits each to batch-mode and provider-integrations; PR 584 (Mistral) is 1 day old and needs review
    
    What it should get through:
      1. Align on Mistral batch processor design   [Nils Brandt must raise this]
           - Nils walks through Mistral batch design and PR PR 584 constraints
           - Emil flags how it interacts with PR 585 retry/batch work
           - Dario asks about token accounting and rate limits
           - Decision: ready to review or needs refinement
      2. Validate Pydantic model refactor and upload logic   [Nils Brandt must raise this]
           - Nils explains tempfile refactor and BatchJobOut model
           - Emil checks for side effects on existing batches
           - Confirm it's safe to land
      3. Unblock retry/batch interaction   [Emil Brandvold must raise this]
           - Emil flags PR 585 age (1 day) and concerns
           - Nils and Dario discuss whether Mistral work unblocks or complicates it
           - Set priority: land Mistral first or run in parallel
    
    On the agenda: Mistral batch processor design and PR PR 584; Upload file logic and Pydantic models; Retry/batch interaction and PR PR 585 status
    
    Meeting today: Weekly sync
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Mistral batch processor design is clear and aligned; PR 584 is ready for review or has blockers named; PR 585 path is clarified (can land after Mistral or in parallel); it is settled that the team agrees a private copy of the model names in batch mode contradicted the maintained support list and cost a day
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 288 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 581: Environment variable to disable rich (Gideon Halloway)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)

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
      - — and 436 function/class names and 0 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Nils Brandt  (nils)
    role        Batch Backend Engineer (short-term contract). Just landed batch upload logic refactor and Pydantic model work; knows current state
    owns        batch-mode, provider-integrations
    agenda
      1. Align on Mistral batch processor design   *** MUST RAISE ***
      2. Validate Pydantic model refactor and upload logic   *** MUST RAISE ***
      3. Unblock retry/batch interaction
    goal        Align on Mistral batch processor design
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Owns three core services; context on litellm wrapping fix and how batch interacts
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Align on Mistral batch processor design
      2. Validate Pydantic model refactor and upload logic
      3. Unblock retry/batch interaction   *** MUST RAISE ***
      4. Lost most of yesterday to batch mode. The model was in the support list, online run gave me clean JSON objects, the batch submission for the exact same config refused to attach a schema. Turned out the batch submitter was checking against a tuple of model names it keeps in its own file, last touched in January.   *** MUST SETTLE (clue t2.r2.l4) ***
    goal        Unblock retry/batch interaction
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Senior request-processing owner; can spot interaction issues
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Align on Mistral batch processor design
      2. Validate Pydantic model refactor and upload logic
      3. Unblock retry/batch interaction
    goal        3 commits each to batch-mode and provider-integrations; PR 584 (Mistral) is 1 day old and needs review
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Mistral batch processor design is clear and aligned; PR 584 is ready for review or has blockers named; PR 585 path is clarified (can land after Mistral or in parallel); it is settled that the team agrees a private copy of the model names in batch mode contradicted the maintained support list and cost a day


------------------------------------------------------------------------------
## #incidents — 14 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #incidents: a batch job submitted overnight came back with every line failed on the same schema complaint, twenty-two hours after submission

    Today is Wednesday 12 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: a batch job submitted overnight came back with every line failed on the same schema complaint, twenty-two hours after submission
    
    What it should get through:
    
    On the agenda: Dario Kestrel posts the batch object ids and the error line repeated 60k times, and notes the submit call itself returned 200 so nothing looked wrong at bedtime; Emil Brandvold points out the batch retry logic dutifully resubmitted the failures, which cost another cycle and produced the identical result; Gideon Halloway says the wait is the expensive part here and this path in particular cannot be allowed to reach the submit call with a schema the provider will not take
    
    Wrap when: incident closed by hand-editing the schema and resubmitting; the batch path is now explicitly in scope for the pre-dispatch check and Dario Kestrel notes the online path was already assumed; it is settled that the team agrees a schema change should resend only the affected rows rather than discard everything
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 18 release(s) shipped, currently v0.1.20
      - 288 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 566: deepseek api (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 581: Environment variable to disable rich (Gideon Halloway)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)

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
      - — and 436 function/class names and 0 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
    goal        a batch job submitted overnight came back with every line failed on the same schema complaint, twenty-two hours after submission
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. 
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
    goal        a batch job submitted overnight came back with every line failed on the same schema complaint, twenty-two hours after submission
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. 
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Nuking the whole cache dir every time I tweak one field is the main reason people here do not trust reruns. On a 200k set that is real money to get one extra field.   *** MUST SETTLE (clue t1.r1.l_schema_3) ***
    goal        the team agrees a schema change should resend only the affected rows rather than discard everything
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   incident closed by hand-editing the schema and resubmitting; the batch path is now explicitly in scope for the pre-dispatch check and Dario Kestrel notes the online path was already assumed; it is settled that the team agrees a schema change should resend only the affected rows rather than discard everything

