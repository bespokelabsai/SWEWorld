# Phase 4: what the simulation is told

Four things reach a model: the channel scenario and briefing (which the DIRECTOR sees, to pick who speaks next), the shared ground (which EVERYONE in the channel holds), each person's own grounding, and the turn budget.

Worth keeping in mind while reading:

1. **This is today, not history.** Everyone is told the state as of that morning.
2. **MUST RAISE** belongs to the person driving it; the engine holds the conversation open until it lands. **MUST SETTLE** is a planted clue: the engine pushes for it to be stated as a conclusion, and a channel-day that does not get its INFORMATION across is run again — told what was missing. The words are the persona's own; what is fixed is the point, and any identifier named under it.
3. **The forbidden list does not exist yet** on that date. Naming it is the failure this whole pipeline is built to prevent.


==============================================================================
# 2025-03-27 — 3 conversation(s), 36 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Two PRs opened today, both need eyes; six older PRs stalling

    Today is Thursday 27 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two PRs opened today, both need eyes; six older PRs stalling
    
    What it should get through:
      1. PR 606 authentication flow gets initial review   [Dermot Callaghan must raise this]
           - Emil presents the client-side auth shape and payload handling
           - Dermot flags any pipeline integration gaps
           - Gideon spots observability gaps if any
      2. PR 605 viewer deletion is complete and safe   [Konrad Feltrin must raise this]
           - Konrad walks the PR: what changed, what stays
           - Dermot confirms bulk-llm-inference unaffected
           - Agreement on whether HOSTED_CURATOR_VIER rename is thorough
    
    On the agenda: PR 606 authentication client flow and API surface; PR 605 viewer deletion scope and rename completeness; Stale PR triage: what unblocks PR 468, PR 579, PR 585, PR 590, PR 565, PR 583
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Both PRs either approved or have clear next-step feedback. Oldest stale PRs identified for either unblocking or deferral.
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 19 release(s) shipped, currently v0.1.21
      - 304 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 585: Feat/retry/batch (Emil Brandvold)
      - PR 590: ref: make prapogate false in logger (Emil Brandvold)

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
      - — and 407 function/class names and 52 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Authentication flow design and implementation
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. PR 606 authentication flow gets initial review
      2. PR 605 viewer deletion is complete and safe
    goal        Two PRs opened today, both need eyes; six older PRs stalling
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Context on viewer deletion and variable scope across services
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. PR 606 authentication flow gets initial review
      2. PR 605 viewer deletion is complete and safe   *** MUST RAISE ***
    goal        PR 605 viewer deletion is complete and safe
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Bulk-llm-inference perspective and integration context
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. PR 606 authentication flow gets initial review   *** MUST RAISE ***
      2. PR 605 viewer deletion is complete and safe
    goal        PR 606 authentication flow gets initial review
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Online request processing and observability angle
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. PR 606 authentication flow gets initial review
      2. PR 605 viewer deletion is complete and safe
    goal        Two PRs opened today, both need eyes; six older PRs stalling
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Both PRs either approved or have clear next-step feedback. Oldest stale PRs identified for either unblocking or deferral.


------------------------------------------------------------------------------
## #viewer — 10 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #viewer: PR 605 removes local curator viewer; clarifies hosted-only direction

    Today is Thursday 27 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: PR 605 removes local curator viewer; clarifies hosted-only direction
    
    What it should get through:
      1. Team agrees on local viewer deprecation rationale   [Konrad Feltrin must raise this]
           - Konrad explains consolidation goal and cost
           - Dario raises user friction if any
           - Emil confirms hosted viewer path is ready
    
    On the agenda: Why we deleted local viewer and the hosted alternative; What users do now for local dataset inspection; Authentication and access control for hosted viewer
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: No surprise to the team about local viewer removal. Shared understanding that hosted viewer is the user story going forward.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 19 release(s) shipped, currently v0.1.21
      - 304 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 585: Feat/retry/batch (Emil Brandvold)
      - PR 590: ref: make prapogate false in logger (Emil Brandvold)

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
      - — and 407 function/class names and 52 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Decision rationale for local viewer deprecation and path forward
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Team agrees on local viewer deprecation rationale   *** MUST RAISE ***
    goal        Team agrees on local viewer deprecation rationale
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Authentication surface implications and hosted viewer readiness
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Team agrees on local viewer deprecation rationale
    goal        PR 605 removes local curator viewer; clarifies hosted-only direction
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. User-facing surface stability concerns
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Team agrees on local viewer deprecation rationale
    goal        PR 605 removes local curator viewer; clarifies hosted-only direction
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Integration test and release perspective
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Team agrees on local viewer deprecation rationale
    goal        PR 605 removes local curator viewer; clarifies hosted-only direction
    available   around today

### 4. How it should land

    lands as  partial
    leaving   No surprise to the team about local viewer removal. Shared understanding that hosted viewer is the user story going forward.


------------------------------------------------------------------------------
## #help — 14 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #help: Gideon Halloway was testing Dario Kestrel's branch and the run sat at 0/12000 for an hour against a batch id Anthropic no longer recognises

    Today is Thursday 27 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Gideon Halloway was testing Dario Kestrel's branch and the run sat at 0/12000 for an hour against a batch id Anthropic no longer recognises
    
    What it should get through:
    
    On the agenda: Gideon Halloway pastes the poll loop spinning on a batch the provider answers 404 for, and says an hour of nothing with no error was the worst part of it; Dario Kestrel notes the same branch quietly started a new batch in a second test when the id was missing, and that he could not tell the two runs apart afterwards; Gideon Halloway says he would rather the thing stop and shout at him than guess
    
    Wrap when: both agree the 404 path is unhandled; whether it raises or resubmits is left open pending what the other providers return; it is settled that the team agrees resolving the executor image to `latest` breaks reproducibility for users
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 19 release(s) shipped, currently v0.1.21
      - 304 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 585: Feat/retry/batch (Emil Brandvold)
      - PR 590: ref: make prapogate false in logger (Emil Brandvold)

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
      - — and 407 function/class names and 52 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in. These DO exist today and are yours to name: latest.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. 
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. User in the forum ran the same RAFT verifier script two weeks apart and got different pass counts. Walked through it with them, their code is identical, the run log shows a different image digest the second time. We are handing people a `latest` and calling it reproducible.   *** MUST SETTLE (clue t4.r1.L8) ***
         must contain literally: latest
    goal        the team agrees resolving the executor image to `latest` breaks reproducibility for users
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
    goal        Gideon Halloway was testing Dario Kestrel's branch and the run sat at 0/12000 for an hour against a batch id Anthropic no longer recognises
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   both agree the 404 path is unhandled; whether it raises or resubmits is left open pending what the other providers return; it is settled that the team agrees resolving the executor image to `latest` breaks reproducibility for users


==============================================================================
# 2025-03-31 — 4 conversation(s), 40 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #releases — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #releases: v0.1.22 tagged; three PRs merged overnight including authentication and Mistral batch; release notes due today.

    Today is Monday 31 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: v0.1.22 tagged; three PRs merged overnight including authentication and Mistral batch; release notes due today.
    
    What it should get through:
      1. Confirm v0.1.22 is ready to ship   [Emil Brandvold must raise this]
           - Emil flags the three merged PRs and their test coverage
           - Dario notes auth flow was reviewed and Mistral batch has real test coverage, not mocks
           - All agree the release is solid
      2. Publish release notes and announcement   [Emil Brandvold must raise this]
           - Emil has the changelog drafted: auth, Mistral batch, docs examples
           - Konrad notes the examples table cleanup landed with it
           - Release goes out to channels and users
    
    On the agenda: Mistral batch processor and auth flow landed; Verify no regressions in core inference; Announce v0.1.22 to the team
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: v0.1.22 announced; authentication flow, Mistral batch support, and examples refresh in users' hands.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 20 release(s) shipped, currently v0.1.22
      - 308 changes merged to date

    On the table
      - v0.1.21 Release Notes (Dermot Callaghan)
      - announce-v0-1-22 (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 585: Feat/retry/batch (Emil Brandvold)
      - PR 598: Feat/recipe/simplestrat (Emil Brandvold)

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
      - — and 406 function/class names and 51 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Version bump, authentication flow, and Mistral batch landed; changelog ready
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm v0.1.22 is ready to ship   *** MUST RAISE ***
      2. Publish release notes and announcement   *** MUST RAISE ***
      3. that "v0.1.22 is out" has gone out, and what you asked in it   *** MUST RAISE ***
      4. what "v0.1.21 Release Notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm v0.1.22 is ready to ship
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Reviewed the final PRs; knows the state of provider integrations
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm v0.1.22 is ready to ship
      2. Publish release notes and announcement
    goal        v0.1.22 tagged; three PRs merged overnight including authentication and Mistral batch; release notes due today.
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Examples and tutorials up to date in this version
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm v0.1.22 is ready to ship
      2. Publish release notes and announcement
    goal        v0.1.22 tagged; three PRs merged overnight including authentication and Mistral batch; release notes due today.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   v0.1.22 announced; authentication flow, Mistral batch support, and examples refresh in users' hands.


------------------------------------------------------------------------------
## #engineering — 10 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Three significant PRs merged: authentication, version bump, Mistral batch examples; landed between Friday and Monday.

    Today is Monday 31 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Three significant PRs merged: authentication, version bump, Mistral batch examples; landed between Friday and Monday.
    
    What it should get through:
      1. Note authentication flow is live   [Emil Brandvold must raise this]
           - Emil explains the new curator client auth surface
           - Dario notes it touches bulk-llm-inference, caching-and-resume, online-request-processing, and provider-integrations
           - Team acknowledges it is a breaking change for users; upgrade required
      2. Mistral batch is now a first-class provider   [Theo Marchetti must raise this]
           - Theo walks through the new mistral_batch.py example: setup, batch submission, waiting for results
           - Emil confirms the example has real batch API coverage, not unit mocks like before
           - Konrad notes this rounds out the batch provider story: Anthropic, Google, OpenAI, now Mistral
      3. Examples and docs are current   [Konrad Feltrin must raise this]
           - Konrad notes the examples table is up to date; tutorial is current
           - Theo's Mistral batch example and setup instructions are in the README
           - No stale docs pointing at old APIs
    
    On the agenda: Authentication flow merged; Mistral batch provider now live with real test coverage; Examples and docs refreshed
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team understands what shipped: authentication is required, Mistral batch is production-ready, and examples reflect the current API.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 20 release(s) shipped, currently v0.1.22
      - 308 changes merged to date

    On the table
      - WS-047: Release Engineering, CI & Test Suite (Nils Brandt)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 585: Feat/retry/batch (Emil Brandvold)
      - PR 598: Feat/recipe/simplestrat (Emil Brandvold)

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
      - — and 406 function/class names and 51 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Drove authentication flow and Mistral batch to merge; knows the surface changes users will see
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Note authentication flow is live   *** MUST RAISE ***
      2. Mistral batch is now a first-class provider
      3. Examples and docs are current
      4. the page you are writing, WS-050: Batch Mode (50%-Cost Async Batch APIs), has to say this in your own words: Went through the batch tickets from the last two months. Laptop lid closed, CI runner hit its six hour cap, OOM killer, one power cut. Every single one of them died while waiting on the provider. Nobody has ever managed to die inside the submit call itself, that thing returns in about 200ms.   *** MUST SETTLE (clue t3.r1.L6) ***
      5. that the doc "WS-050: Batch Mode (50%-Cost Async Batch APIs)" is done, and where the others can find it   *** MUST RAISE ***
      6. that the doc "v0.1.22 Release Notes" is done, and where the others can find it   *** MUST RAISE ***
    goal        Note authentication flow is live
    available   around today

  Theo Marchetti  (theo)
    role        Provider Examples Contributor (Mistral Batch). Mistral batch examples and setup instructions; knows the new provider surface
    owns        provider-integrations
    agenda
      1. Note authentication flow is live
      2. Mistral batch is now a first-class provider   *** MUST RAISE ***
      3. Examples and docs are current
      4. what "WS-047: Release Engineering, CI & Test Suite" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Mistral batch is now a first-class provider
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Examples table in good shape; provider examples filled in
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Note authentication flow is live
      2. Mistral batch is now a first-class provider
      3. Examples and docs are current   *** MUST RAISE ***
      4. that "Weekly update: week of Mar 24" has gone out, and what you asked in it   *** MUST RAISE ***
    goal        Examples and docs are current
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Reviewed both auth and Mistral batch; knows the request layer impact
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Note authentication flow is live
      2. Mistral batch is now a first-class provider
      3. Examples and docs are current
    goal        Three significant PRs merged: authentication, version bump, Mistral batch examples; landed between Friday and Monday.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team understands what shipped: authentication is required, Mistral batch is production-ready, and examples reflect the current API.


------------------------------------------------------------------------------
## #pipeline — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Three PRs merged touching bulk-llm-inference, provider-integrations, online-request-processing, and caching-and-resume; auth and Mistral batch are production changes.

    Today is Monday 31 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Three PRs merged touching bulk-llm-inference, provider-integrations, online-request-processing, and caching-and-resume; auth and Mistral batch are production changes.
    
    What it should get through:
      1. Auth flow does not break online request retry or resume   [Emil Brandvold must raise this]
           - Emil notes auth is now required at LLM instantiation, before any requests
           - Dario asks: does auth token refresh or expiry interrupt a running job mid-batch?
           - Emil confirms: token refresh is transparent; resume picks up after auth refresh; no per-request auth overhead
      2. Mistral batch provider is live and tested   [Theo Marchetti must raise this]
           - Theo confirms mistral_batch.py ran against real Mistral API, not mocks
           - Emil notes the batch submission, polling, and result download all have test coverage
           - Dario agrees: fourth batch provider with production confidence
      3. Resume and retry paths unchanged   [Dario Kestrel must raise this]
           - Dario confirms the three PRs do not touch retry backoff, exponential delays, or resume state storage
           - Emil confirms caching-and-resume was only touched by auth flow (instantiation time, not request time)
           - Team agrees: no regression risk in running jobs
    
    On the agenda: Auth flow impact on online request handling; Mistral batch provider integration working; No regressions in retry or resume logic
    
    No longer here: Nils Brandt — do not expect them back or wait on them
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Auth flow and Mistral batch are production-safe; online request processing, retry, and resume are unaffected.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 20 release(s) shipped, currently v0.1.22
      - 308 changes merged to date

    On the table
      - WS-047: Release Engineering, CI & Test Suite (Nils Brandt)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 585: Feat/retry/batch (Emil Brandvold)
      - PR 598: Feat/recipe/simplestrat (Emil Brandvold)

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
      - — and 406 function/class names and 51 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Auth flow and Mistral batch merged; knows the request layer changes
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Auth flow does not break online request retry or resume   *** MUST RAISE ***
      2. Mistral batch provider is live and tested
      3. Resume and retry paths unchanged
    goal        Auth flow does not break online request retry or resume
    available   around today

  Theo Marchetti  (theo)
    role        Provider Examples Contributor (Mistral Batch). Mistral batch example and cleanup commits; knows what the new provider surface looks like
    owns        provider-integrations
    agenda
      1. Auth flow does not break online request retry or resume
      2. Mistral batch provider is live and tested   *** MUST RAISE ***
      3. Resume and retry paths unchanged
      4. what "WS-047: Release Engineering, CI & Test Suite" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Mistral batch provider is live and tested
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Reviewed the auth flow and Mistral batch; knows the impact on online request processing
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Auth flow does not break online request retry or resume
      2. Mistral batch provider is live and tested
      3. Resume and retry paths unchanged   *** MUST RAISE ***
    goal        Resume and retry paths unchanged
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Auth flow and Mistral batch are production-safe; online request processing, retry, and resume are unaffected.


------------------------------------------------------------------------------
## #code-review — 14 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Dario Kestrel pushed a revision with the hook moved and a way to bypass the check, and Emil Brandvold has opinions about both

    Today is Monday 31 March 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Dario Kestrel pushed a revision with the hook moved and a way to bypass the check, and Emil Brandvold has opinions about both
    
    What it should get through:
    
    On the agenda: Emil Brandvold argues the bypass should read like the one we already have for caching so users can guess it, and points at CURATOR_DISABLE_CACHE as the shape people already know; Dario Kestrel describes the recursive model a user sent in, where his walker went several levels deep and then gave up, and says he does not know whether giving up should mean stop or continue; Dermot Callaghan says he has hit the nested-depth ceiling on a real schema before and the thing that annoyed him was not being told which nesting level was the problem
    
    Wrap when: bypass naming to be settled by Emil Brandvold, behaviour on models the walker cannot fully resolve still open; it is settled that the team agrees a missing cache directory currently raises and people are papering over it with mkdir
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 20 release(s) shipped, currently v0.1.22
      - 308 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 585: Feat/retry/batch (Emil Brandvold)
      - PR 598: Feat/recipe/simplestrat (Emil Brandvold)

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
      - — and 406 function/class names and 51 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in. These DO exist today and are yours to name: FileNotFoundError.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. 
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
    goal        Dario Kestrel pushed a revision with the hook moved and a way to bypass the check, and Emil Brandvold has opinions about both
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. fresh CI container, nothing has ever run in it, and the pre-flight estimate step went red with FileNotFoundError on the cache directory. I put a mkdir -p in the workflow to get past it, which I hate, because now the estimate step is the thing that creates the cache. Second time this month.   *** MUST SETTLE (clue t1.r2.L7) ***
         must contain literally: FileNotFoundError
    goal        the team agrees a missing cache directory currently raises and people are papering over it with mkdir
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. 
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
    goal        Dario Kestrel pushed a revision with the hook moved and a way to bypass the check, and Emil Brandvold has opinions about both
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   bypass naming to be settled by Emil Brandvold, behaviour on models the walker cannot fully resolve still open; it is settled that the team agrees a missing cache directory currently raises and people are papering over it with mkdir


==============================================================================
# 2025-04-01 — 2 conversation(s), 17 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 9 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Emil opened PR 612 same day he merged PR 585 (Feat/retry/batch); gemini batch is broken and needs to land fast.

    Today is Tuesday 1 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Emil opened PR 612 same day he merged PR 585 (Feat/retry/batch); gemini batch is broken and needs to land fast.
    
    What it should get through:
      1. Land PR 612 gemini batch fix   [Emil Brandvold must raise this]
           - Emil describes the gemini parts key missing in batch context
           - Konrad asks whether the fix handles the error at parse time or runtime
           - Gideon and Dario Kestrel agree the fix is narrow enough to land independently
      2. Clarify whether fix applies to other batch providers   [Konrad Feltrin must raise this]
           - Emil walks through which providers batch the same way
           - Dario notes openai client backend PR (PR 565) is waiting and may have the same shape
           - Agreed: fix is gemini-specific for now; check others on next sweep
    
    On the agenda: Root cause: why gemini batch parts key was missing; Fix scope and whether it generalizes to other providers; Unblocking stale PRs in flight
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 612 approved and ready to merge; gemini batch restored; scope of batch provider work clarified.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 20 release(s) shipped, currently v0.1.22
      - 309 changes merged to date

    On the table
      - WS-050: Batch Mode (50%-Cost Async Batch APIs) (Emil Brandvold)
      - WS-050: Batch Mode (50%-Cost Async Batch APIs) (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 598: Feat/recipe/simplestrat (Emil Brandvold)
      - PR 600: feat/env-disable-rich-cli (Gideon Halloway)

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
      - — and 400 function/class names and 50 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Root cause analysis of gemini batch parts key issue and the fix
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Land PR 612 gemini batch fix   *** MUST RAISE ***
      2. Clarify whether fix applies to other batch providers
      3. what "WS-050: Batch Mode (50%-Cost Async Batch APIs)" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Land PR 612 gemini batch fix
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Familiarity with batch-mode architecture
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Land PR 612 gemini batch fix
      2. Clarify whether fix applies to other batch providers   *** MUST RAISE ***
      3. what "WS-050: Batch Mode (50%-Cost Async Batch APIs)" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Clarify whether fix applies to other batch providers
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Understanding of batch API failure modes
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Land PR 612 gemini batch fix
      2. Clarify whether fix applies to other batch providers
    goal        Emil opened PR 612 same day he merged PR 585 (Feat/retry/batch); gemini batch is broken and needs to land fast.
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Request processing context
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Land PR 612 gemini batch fix
      2. Clarify whether fix applies to other batch providers
    goal        Emil opened PR 612 same day he merged PR 585 (Feat/retry/batch); gemini batch is broken and needs to land fast.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 612 approved and ready to merge; gemini batch restored; scope of batch provider work clarified.


------------------------------------------------------------------------------
## #pipeline — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Emil just merged retry/batch feature (PR 585) and opened gemini batch bug (PR 612) same day; pipeline needs to know what retry contract changed.

    Today is Tuesday 1 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Emil just merged retry/batch feature (PR 585) and opened gemini batch bug (PR 612) same day; pipeline needs to know what retry contract changed.
    
    What it should get through:
      1. Confirm retry semantics from PR 585 landed as designed   [Emil Brandvold must raise this]
           - Emil summarizes the retry/batch PR scope
           - Gideon asks whether retries count against user retry budget or are internal
           - Dario and Gideon Halloway agree on internal retry pool vs user-facing budget
      2. Align on batch provider sweep priority   [Gideon Halloway must raise this]
           - Gideon proposes which providers to sweep first based on volume
           - Emil confirms gemini fix is first; openai batch next
           - Agreed: start with gemini, then openai, then anthropic
    
    On the agenda: Retry semantics inside a batch (do failed items retry within batch or fail the whole job?); Cost and latency trade-offs of retry strategies; What the PR PR 585 (Feat/retry/batch) actually landed
    
    No longer here: Nils Brandt — do not expect them back or wait on them
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Retry semantics clarified; provider sweep plan in place; PR 612 unblocks the batch mode push.
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 20 release(s) shipped, currently v0.1.22
      - 309 changes merged to date

    On the table
      - WS-050: Batch Mode (50%-Cost Async Batch APIs) (Emil Brandvold)
      - WS-050: Batch Mode (50%-Cost Async Batch APIs) (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 598: Feat/recipe/simplestrat (Emil Brandvold)
      - PR 600: feat/env-disable-rich-cli (Gideon Halloway)

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
      - — and 400 function/class names and 50 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Retry/batch feature design and gemini specifics
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm retry semantics from PR 585 landed as designed   *** MUST RAISE ***
      2. Align on batch provider sweep priority
      3. what "WS-050: Batch Mode (50%-Cost Async Batch APIs)" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm retry semantics from PR 585 landed as designed
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Cost estimation and request lifecycle context
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm retry semantics from PR 585 landed as designed
      2. Align on batch provider sweep priority   *** MUST RAISE ***
      3. what "WS-050: Batch Mode (50%-Cost Async Batch APIs)" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Align on batch provider sweep priority
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Provider integration patterns and cost policy
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm retry semantics from PR 585 landed as designed
      2. Align on batch provider sweep priority
    goal        Emil just merged retry/batch feature (PR 585) and opened gemini batch bug (PR 612) same day; pipeline needs to know what retry contract changed.
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Retry semantics clarified; provider sweep plan in place; PR 612 unblocks the batch mode push.


==============================================================================
# 2025-04-02 — 3 conversation(s), 28 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Two batch-related PRs opened same day suggest systemic issue in batch cancellation flow

    Today is Wednesday 2 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two batch-related PRs opened same day suggest systemic issue in batch cancellation flow
    
    What it should get through:
      1. Understand if PR 614 and PR 615 are part of same bug or separate   [Konrad Feltrin must raise this]
           - Dermot explains the TypeError and the fix
           - Emil notes PR 615 is adding failed requests output, not fixing cancellation
           - Konrad asks if both touch cancel_batches or if they're orthogonal
      2. Get PR 614 approved and merged to unblock batch testing   [Dermot Callaghan must raise this]
           - Konrad reviews the logic
           - Emil flags if there are interaction risks with PR 615
           - Konrad approves or requests changes
      3. write up Weekly Notes — Week of Mar 31   [Emil Brandvold must raise this]
           - Emil Brandvold says they will write Weekly Notes — Week of Mar 31 — Emil's sync notes covering the v0.1.22 release.
    
    On the agenda: Why working_dir was passed to cancel_batches in the first place; Whether PR 614 and PR 615 are addressing the same root cause or separate bugs; Approval path for both PRs; Weekly Notes — Week of Mar 31
    
    Meeting today: Weekly sync
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 614 merged; clarity on whether PR 615 needs coordination with it; it is settled that Emil Brandvold hit a 404 polling loop because the stored job id was reused across two backends
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 20 release(s) shipped, currently v0.1.22
      - 309 changes merged to date

    On the table
      - WS-050: Batch Mode (50%-Cost Async Batch APIs) (Emil Brandvold)
      - Weekly Notes — Week of Mar 31 (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 598: Feat/recipe/simplestrat (Emil Brandvold)
      - PR 600: feat/env-disable-rich-cli (Gideon Halloway)

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
      - — and 400 function/class names and 50 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. The cancellation bug fix and context on why working_dir argument was incorrect
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Understand if PR 614 and PR 615 are part of same bug or separate
      2. Get PR 614 approved and merged to unblock batch testing   *** MUST RAISE ***
      3. write up Weekly Notes — Week of Mar 31
    goal        Get PR 614 approved and merged to unblock batch testing
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Maintainer perspective on API surface changes
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Understand if PR 614 and PR 615 are part of same bug or separate   *** MUST RAISE ***
      2. Get PR 614 approved and merged to unblock batch testing
      3. write up Weekly Notes — Week of Mar 31
      4. what "WS-050: Batch Mode (50%-Cost Async Batch APIs)" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Understand if PR 614 and PR 615 are part of same bug or separate
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Parallel experience with batch request handling from PR 615
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Understand if PR 614 and PR 615 are part of same bug or separate
      2. Get PR 614 approved and merged to unblock batch testing
      3. write up Weekly Notes — Week of Mar 31   *** MUST RAISE ***
      4. related annoyance: the pending job id gets parked in the run dir keyed off the dataset only, so the plain openai path and the azure deployment of the same model land in the same slot. moved a cookbook over to azure last week, the restart polled a job that endpoint doesn't own and I sat in a 404 retry loop for twenty minutes before giving up and wiping the dir by hand.   *** MUST SETTLE (clue t3.r2.l_prov_emil) ***
      5. that the doc "Weekly Notes — Week of Mar 31" is done, and where the others can find it   *** MUST RAISE ***
    goal        write up Weekly Notes — Week of Mar 31
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 614 merged; clarity on whether PR 615 needs coordination with it; it is settled that Emil Brandvold hit a 404 polling loop because the stored job id was reused across two backends; Emil Brandvold hit a 404 polling loop because the stored job id was reused across two backends


------------------------------------------------------------------------------
## #engineering — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Two concurrent batch fixes suggest instability in batch request handling mid-flight

    Today is Wednesday 2 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two concurrent batch fixes suggest instability in batch request handling mid-flight
    
    What it should get through:
      1. Determine if Gemini batch issues are resolved or ongoing   [Emil Brandvold must raise this]
           - Dermot walks through the TypeError: unexpected keyword argument
           - Emil notes PR 612 fixed parts key issue
           - Dario asks if there are other shape mismatches waiting
      2. Confirm batch cancellation is safe before release   [Dermot Callaghan must raise this]
           - Emil reviews test coverage for cancel_batches
           - Dario checks if multimodal vision batching has been tested
           - Team agrees on blockers or green-lights next phase
    
    On the agenda: What PR 614 fixes and why it matters for batch stability; Whether PR 612 (Gemini parts key) and PR 614 (cancellation) are related; Status of batch mode readiness for release
    
    Meeting today: Weekly sync
    
    No longer here: Priya Vandersloot — do not expect them back or wait on them
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Clarity on whether batch mode is stable enough for next release or if more fixes are pending
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 20 release(s) shipped, currently v0.1.22
      - 309 changes merged to date

    On the table
      - WS-050: Batch Mode (50%-Cost Async Batch APIs) (Emil Brandvold)
      - v0.1.22 Release Notes (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 598: Feat/recipe/simplestrat (Emil Brandvold)
      - PR 600: feat/env-disable-rich-cli (Gideon Halloway)

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
      - — and 400 function/class names and 50 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Overview of batch request flow and what PR 615's failed requests output reveals
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Determine if Gemini batch issues are resolved or ongoing   *** MUST RAISE ***
      2. Confirm batch cancellation is safe before release
      3. what "WS-050: Batch Mode (50%-Cost Async Batch APIs)" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Determine if Gemini batch issues are resolved or ongoing
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Direct encounter with cancel_batches API misuse and the fix
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Determine if Gemini batch issues are resolved or ongoing
      2. Confirm batch cancellation is safe before release   *** MUST RAISE ***
      3. what "v0.1.22 Release Notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm batch cancellation is safe before release
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Context on how multimodal prompts interact with batch mode
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Determine if Gemini batch issues are resolved or ongoing
      2. Confirm batch cancellation is safe before release
    goal        Two concurrent batch fixes suggest instability in batch request handling mid-flight
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Clarity on whether batch mode is stable enough for next release or if more fixes are pending


------------------------------------------------------------------------------
## #pipeline — 10 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Batch cancellation and failed request tracking are intertwined in request lifecycle

    Today is Wednesday 2 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Batch cancellation and failed request tracking are intertwined in request lifecycle
    
    What it should get through:
      1. Unblock batch request handling by fixing cancellation API misuse   [Dermot Callaghan must raise this]
           - Dermot explains the TypeError origin
           - Emil asks if PR 615's failed jsonl catches cancellation failures too
           - Gideon confirms cost tracking accounts for partial batches
      2. Enable visibility into batch request failures via jsonl output   [Emil Brandvold must raise this]
           - Emil describes what PR 615 captures
           - Gideon asks if it integrates with progress bars
           - Dermot notes this unblocks manual batch debugging
    
    On the agenda: What the failed requests jsonl will show and how it helps debugging; Why cancel_batches was being called with wrong arguments; Whether batch request failures are resetting retries correctly
    
    Meeting today: Weekly sync
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: PR 614 and PR 615 are clear on sequencing and integration; batch request visibility improves
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 20 release(s) shipped, currently v0.1.22
      - 309 changes merged to date

    On the table
      - WS-050: Batch Mode (50%-Cost Async Batch APIs) (Emil Brandvold)
      - WS-050: Batch Mode (50%-Cost Async Batch APIs) (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 598: Feat/recipe/simplestrat (Emil Brandvold)
      - PR 600: feat/env-disable-rich-cli (Gideon Halloway)

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
      - — and 400 function/class names and 50 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Failed requests output feature and visibility into where batch requests are failing
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Unblock batch request handling by fixing cancellation API misuse
      2. Enable visibility into batch request failures via jsonl output   *** MUST RAISE ***
      3. what "WS-050: Batch Mode (50%-Cost Async Batch APIs)" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Enable visibility into batch request failures via jsonl output
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. The cancellation bug fix and implications for request lifecycle management
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Unblock batch request handling by fixing cancellation API misuse   *** MUST RAISE ***
      2. Enable visibility into batch request failures via jsonl output
      3. what "WS-050: Batch Mode (50%-Cost Async Batch APIs)" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Unblock batch request handling by fixing cancellation API misuse
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Observability and progress tracking context; knows cost and retry implications
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Unblock batch request handling by fixing cancellation API misuse
      2. Enable visibility into batch request failures via jsonl output
    goal        Batch cancellation and failed request tracking are intertwined in request lifecycle
    available   around today

### 4. How it should land

    lands as  partial
    leaving   PR 614 and PR 615 are clear on sequencing and integration; batch request visibility improves


==============================================================================
# 2025-04-03 — 5 conversation(s), 62 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 5 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Two PRs just merged, six older ones waiting for review; team needs to triage and move the stale batch through.

    Today is Thursday 3 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two PRs just merged, six older ones waiting for review; team needs to triage and move the stale batch through.
    
    What it should get through:
      1. Clear what PR 612 and PR 615 need before merge   [Emil Brandvold must raise this]
           - Emil describes the gemini batch parts fix and failed requests jsonl additions
           - Konrad or Dario Kestrel push back if scope is unclear
           - Team decides: merge pending small fixes, or hold for polish
      2. Unblock PR 565 openai client backend or schedule it   [Dario Kestrel must raise this]
           - Dario raises that it has been open 32 days
           - Konrad or Emil Brandvold check if it's blocked on design or just review bandwidth
           - Team commits to either reviewing next or deferring to next sprint
      3. Decide on PR 600 PR 583 priority   [Nikolai Berresford must raise this]
           - Gideon and Nikolai Berresford flag their PRs are waiting
           - Emil or Konrad Feltrin says whether batch mode or another service blocks on them
           - Team orders them or defers
    
    On the agenda: Recent merges and what's next; Gemini and openai PRs stalling; Metadata and env config features
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Three older PRs have a path forward (merge, small fix, or scheduled review); PR 565 is either unblocked or formally queued.
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 20 release(s) shipped, currently v0.1.22
      - 311 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 600: feat/env-disable-rich-cli (Gideon Halloway)
      - PR 612: feat: fix gemini batch parts key missing (Emil Brandvold)

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
      - — and 380 function/class names and 47 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. Just merged SimpleStrat recipe; context on gemini batch and openai client work
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Clear what PR 612 and PR 615 need before merge   *** MUST RAISE ***
      2. Unblock PR 565 openai client backend or schedule it
      3. Decide on PR 600 PR 583 priority
    goal        Clear what PR 612 and PR 615 need before merge
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Cookbook and recipe design perspective
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Clear what PR 612 and PR 615 need before merge
      2. Unblock PR 565 openai client backend or schedule it
      3. Decide on PR 600 PR 583 priority
    goal        Two PRs just merged, six older ones waiting for review; team needs to triage and move the stale batch through.
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. CLI and observability context
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Clear what PR 612 and PR 615 need before merge
      2. Unblock PR 565 openai client backend or schedule it
      3. Decide on PR 600 PR 583 priority
    goal        Two PRs just merged, six older ones waiting for review; team needs to triage and move the stale batch through.
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Request processing and openai backend context
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Clear what PR 612 and PR 615 need before merge
      2. Unblock PR 565 openai client backend or schedule it   *** MUST RAISE ***
      3. Decide on PR 600 PR 583 priority
    goal        Unblock PR 565 openai client backend or schedule it
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Code execution and metadata perspective
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Clear what PR 612 and PR 615 need before merge
      2. Unblock PR 565 openai client backend or schedule it
      3. Decide on PR 600 PR 583 priority   *** MUST RAISE ***
    goal        Decide on PR 600 PR 583 priority
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Three older PRs have a path forward (merge, small fix, or scheduled review); PR 565 is either unblocked or formally queued.


------------------------------------------------------------------------------
## #cookbooks — 10 turns, 4 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #cookbooks: SimpleStrat recipe just merged; team needs to verify the example is good, consistent with RAFT shape, and covered by tests before the next release.

    Today is Thursday 3 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: SimpleStrat recipe just merged; team needs to verify the example is good, consistent with RAFT shape, and covered by tests before the next release.
    
    What it should get through:
      1. Confirm example is runnable and mirrors RAFT shape   [Emil Brandvold must raise this]
           - Emil walks through the recipe code and example
           - Konrad checks it against RAFT for consistency
           - Team agrees example is ready or flags tweaks needed
      2. Verify CI exercises the recipe   [Nikolai Berresford must raise this]
           - Nikolai or Dario Kestrel ask if the recipe is in the cookbook test suite
           - Emil confirms or commits to adding it
           - Team decides if it blocks the next release
    
    On the agenda: What SimpleStrat does and how it fits; Runnable example completeness; CI coverage for the recipe
    
    No longer here: Priya Vandersloot — do not expect them back or wait on them
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: SimpleStrat recipe is verified runnable, shape is consistent with RAFT, and CI coverage is confirmed or a PR is opened to add it; it is settled that the team agrees the workspace mount is writable when a custom image is used and not when the shipped one is
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 20 release(s) shipped, currently v0.1.22
      - 311 changes merged to date

    On the table
      - WS-050: Batch Mode (50%-Cost Async Batch APIs) (Emil Brandvold)
      - WS-047: Release Engineering, CI & Test Suite (Nils Brandt)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 600: feat/env-disable-rich-cli (Gideon Halloway)
      - PR 612: feat: fix gemini batch parts key missing (Emil Brandvold)

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
      - — and 380 function/class names and 47 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in. These DO exist today and are yours to name: CodeExecutor.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. SimpleStrat block implementation; understanding of recipe shape and raft comparison
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Confirm example is runnable and mirrors RAFT shape   *** MUST RAISE ***
      2. Verify CI exercises the recipe
      3. what "WS-050: Batch Mode (50%-Cost Async Batch APIs)" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm example is runnable and mirrors RAFT shape
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Cookbook design and user-facing recipe perspective
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm example is runnable and mirrors RAFT shape
      2. Verify CI exercises the recipe
    goal        SimpleStrat recipe just merged; team needs to verify the example is good, consistent with RAFT shape, and covered by tests before the next release.
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Release readiness and testing angle
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Confirm example is runnable and mirrors RAFT shape
      2. Verify CI exercises the recipe   *** MUST RAISE ***
      3. what "WS-047: Release Engineering, CI & Test Suite" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Verify CI exercises the recipe
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Release and integration context
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm example is runnable and mirrors RAFT shape
      2. Verify CI exercises the recipe
      3. Lost an afternoon. Pointed `CodeExecutor` at an image of my own so I would stop pip installing pandas per task, and the generated solution decided the tidiest way to pass was to rewrite the input CSV sitting in the mounted dir. Original gone, no backup. On the stock image the same script just errors out when it touches that file.   *** MUST SETTLE (clue t4.r2.L4) ***
         must contain literally: CodeExecutor
    goal        the team agrees the workspace mount is writable when a custom image is used and not when the shipped one is
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   SimpleStrat recipe is verified runnable, shape is consistent with RAFT, and CI coverage is confirmed or a PR is opened to add it; it is settled that the team agrees the workspace mount is writable when a custom image is used and not when the shipped one is


------------------------------------------------------------------------------
## #engineering — 12 turns, 5 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Two PRs just merged; team needs a sync on what shipped, what it means for users, and what's waiting in the queue.

    Today is Thursday 3 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two PRs just merged; team needs a sync on what shipped, what it means for users, and what's waiting in the queue.
    
    What it should get through:
      1. Communicate what SimpleStrat recipe does and unlocks   [Emil Brandvold must raise this]
           - Emil describes the recipe and its difference from manual stratification
           - Konrad frames it in terms of user friction it removes
           - Dario notes how it relates to n-samples work
      2. Confirm CLI demo is live and useful   [Gideon Halloway must raise this]
           - Gideon confirms the gif is updated and merged
           - Konrad notes it improves the README first impression
           - Team moves on
      3. Surface what is blocking the next batch of PRs   [Dario Kestrel must raise this]
           - Dario or Emil Brandvold raises that openai backend, n-samples, and gemini batch are all in flight
           - Konrad asks if any block on design or just review bandwidth
           - Team commits to next week's priority
    
    On the agenda: SimpleStrat recipe and what it enables; CLI demo refresh and user docs; What's blocking next feature work
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Team understands what shipped, sees the user impact, and has clarity on what is queued and whether any are design-blocked.
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 20 release(s) shipped, currently v0.1.22
      - 311 changes merged to date

    On the table
      - WS-050: Batch Mode (50%-Cost Async Batch APIs) (Emil Brandvold)
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 600: feat/env-disable-rich-cli (Gideon Halloway)
      - PR 612: feat: fix gemini batch parts key missing (Emil Brandvold)

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
      - — and 380 function/class names and 47 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. SimpleStrat feature and gemini batch context; aware of openai client stall
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
      1. Communicate what SimpleStrat recipe does and unlocks   *** MUST RAISE ***
      2. Confirm CLI demo is live and useful
      3. Surface what is blocking the next batch of PRs
      4. what "WS-050: Batch Mode (50%-Cost Async Batch APIs)" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Communicate what SimpleStrat recipe does and unlocks
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. CLI refresh and observability work
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Communicate what SimpleStrat recipe does and unlocks
      2. Confirm CLI demo is live and useful   *** MUST RAISE ***
      3. Surface what is blocking the next batch of PRs
    goal        Confirm CLI demo is live and useful
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Cookbook and user perspective
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Communicate what SimpleStrat recipe does and unlocks
      2. Confirm CLI demo is live and useful
      3. Surface what is blocking the next batch of PRs
    goal        Two PRs just merged; team needs a sync on what shipped, what it means for users, and what's waiting in the queue.
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Request processing context
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Communicate what SimpleStrat recipe does and unlocks
      2. Confirm CLI demo is live and useful
      3. Surface what is blocking the next batch of PRs   *** MUST RAISE ***
    goal        Surface what is blocking the next batch of PRs
    available   around today

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. Code execution and release perspective
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Communicate what SimpleStrat recipe does and unlocks
      2. Confirm CLI demo is live and useful
      3. Surface what is blocking the next batch of PRs
    goal        Two PRs just merged; team needs a sync on what shipped, what it means for users, and what's waiting in the queue.
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Team understands what shipped, sees the user impact, and has clarity on what is queued and whether any are design-blocked.


------------------------------------------------------------------------------
## #pipeline — 14 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Emil Brandvold found three batches on the OpenAI dashboard that finished and were paid for with no local record of them at all

    Today is Thursday 3 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Emil Brandvold found three batches on the OpenAI dashboard that finished and were paid for with no local record of them at all
    
    What it should get through:
    
    On the agenda: Emil Brandvold on the orphans: they were submitted, the process died before the first poll came back, and nothing on disk mentioned them; Dario Kestrel says today the tracker only gets written once the poll loop has a status to record, which is why the ids evaporated; Dermot Callaghan suggests the id gets appended and flushed the moment the provider returns it, before any polling starts, so the worst case is a record with no status yet
    
    Wrap when: Dermot Callaghan's ordering is the working plan but nobody has written it down as a decision; Dario Kestrel wants to check whether the batch submit call is even awaited per-batch or fired in a gather; it is settled that the team agrees writing run state only after the download completes leaves the entire polling window unrecoverable
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 20 release(s) shipped, currently v0.1.22
      - 311 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 600: feat/env-disable-rich-cli (Gideon Halloway)
      - PR 612: feat: fix gemini batch parts key missing (Emil Brandvold)

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
      - — and 380 function/class names and 47 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. All the wall clock in a batch run is the poll loop. Submit at 11, provider finishes somewhere around 6, and the only moment we write anything durable is after the download comes back. Kill it at hour three and there is nothing on disk that so much as knows a job was ever opened. That bit me twice this week.   *** MUST SETTLE (clue t3.r1.L5) ***
    goal        the team agrees writing run state only after the download completes leaves the entire polling window unrecoverable
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. 
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
    goal        Emil Brandvold found three batches on the OpenAI dashboard that finished and were paid for with no local record of them at all
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. 
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
    goal        Emil Brandvold found three batches on the OpenAI dashboard that finished and were paid for with no local record of them at all
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Dermot Callaghan's ordering is the working plan but nobody has written it down as a decision; Dario Kestrel wants to check whether the batch submit call is even awaited per-batch or fired in a gather; it is settled that the team agrees writing run state only after the download completes leaves the entire polling window unrecoverable


------------------------------------------------------------------------------
## #viewer — 14 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #viewer: Gideon Halloway wants to know what the CLI should show when a run reattaches mid-flight, before the reattach code lands

    Today is Thursday 3 April 2025. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Gideon Halloway wants to know what the CLI should show when a run reattaches mid-flight, before the reattach code lands
    
    What it should get through:
    
    On the agenda: Gideon Halloway on the resumed run showing 0 completed and a projected time computed from nothing; Emil Brandvold says the cost counter added the reattached batch's spend on top of what the first process had already reported; they trade guesses about whether the summary table should show one run or two and drop it
    
    Wrap when: nothing decided; Gideon Halloway says he will wait until the reattach lands before touching the progress code; it is settled that the team agrees duplicate submissions originate from restarts in the gap right after the first submission
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Consolidation and Provider Breadth: Pruning After the Sprint

    Settled
      - 20 release(s) shipped, currently v0.1.22
      - 311 changes merged to date

    On the table
      - PR 468: feat: add support for n samples in generation params (Emil Brandvold)
      - PR 565: add openai client backend (Dario Kestrel)
      - PR 579: Feat/openai/deepseek api (Emil Brandvold)
      - PR 583: feat: add param to disable metadata db (Nikolai Berresford)
      - PR 600: feat/env-disable-rich-cli (Gideon Halloway)
      - PR 612: feat: fix gemini batch parts key missing (Emil Brandvold)

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
      - — and 380 function/class names and 47 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. 
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Saw two jobs on one account's dashboard four minutes apart, identical request counts. Traced it: the user ctrl-c'd while the first status line was still printing and started the script again. So the second submission happened out of a window of maybe ninety seconds, before we had ever come back from the provider with a status.   *** MUST SETTLE (clue t3.r1.L7) ***
    goal        the team agrees duplicate submissions originate from restarts in the gap right after the first submission
    available   around today

  Emil Brandvold  (emil)
    role        Core Platform Engineer, Request Processing. 
    owns        release-and-ci, online-request-processing, provider-integrations, batch-mode
    agenda
    goal        Gideon Halloway wants to know what the CLI should show when a run reattaches mid-flight, before the reattach code lands
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   nothing decided; Gideon Halloway says he will wait until the reattach lands before touching the progress code; it is settled that the team agrees duplicate submissions originate from restarts in the gap right after the first submission

