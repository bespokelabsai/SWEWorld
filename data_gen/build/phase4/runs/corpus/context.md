# Phase 4: what the simulation is told

Four things reach a model: the channel scenario and briefing (which the DIRECTOR sees, to pick who speaks next), the shared ground (which EVERYONE in the channel holds), each person's own grounding, and the turn budget.

Worth keeping in mind while reading:

1. **This is today, not history.** Everyone is told the state as of that morning.
2. **MUST RAISE** belongs to the person driving it; the engine holds the conversation open until it lands. **MUST SETTLE** is a planted clue: the engine pushes for it to be stated as a conclusion, and a channel-day that does not get its INFORMATION across is run again — told what was missing. The words are the persona's own; what is fixed is the point, and any identifier named under it.
3. **The forbidden list does not exist yet** on that date. Naming it is the failure this whole pipeline is built to prevent.


==============================================================================
# 2024-12-17 — 1 conversation(s), 8 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #releases — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #releases: 0.1.12 shipped today; tag is out; release notes due; announce mail due

    Today is Tuesday 17 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 0.1.12 shipped today; tag is out; release notes due; announce mail due
    
    What it should get through:
      1. Release notes capture what shipped   [Dario Kestrel must raise this]
           - Dario sketches the eight merged PRs
           - Konrad confirms the changelog is complete
           - Dario posts release-v0-1-12
      2. Announce the release to the team   [Dario Kestrel must raise this]
           - Dario confirms the tag is live
           - Konrad checks it resolves
           - Dario posts announce-v0-1-12 mail
    
    On the agenda: Confirm v0.1.12 is tagged and live; Write and post release notes; Decide on next release cadence
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: v0.1.12 is tagged, release notes are written and posted, announcement mail is sent to the team
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 6 release(s) shipped, currently v0.1.12
      - 135 changes merged to date

    On the table
      - v0.1.12 release notes (Dario Kestrel)
      - Postmortem: Dec 4 revert of end-of-run retry logic (Gideon Halloway)
      - Postmortem: Dec 10 revert of batch auto-delete (Dermot Callaghan)
      - Postmortem: Dec 13 revert of batch context-manager refactor (PR PR 254) (Konrad Feltrin)
      - announce-v0-1-12 (Dario Kestrel)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 163: [curator-viewer] use getCacheDir helper function, add additional param for cache dir (Gideon Halloway)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 62: Support generation configuration for LLM
      - issue 86: Retry when structured output fails
      - issue 88: Add a way to disable caching for curator
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run

    DOES NOT EXIST YET (7 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - local-offline-inference
      - telemetry
      - — and 1184 function/class names and 156 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. merged all 8 PRs that shipped in 0.1.12; knows what changed and why
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Release notes capture what shipped   *** MUST RAISE ***
      2. Announce the release to the team   *** MUST RAISE ***
      3. that the doc "v0.1.12 release notes" is done, and where the others can find it   *** MUST RAISE ***
      4. that "v0.1.12 is out" has gone out, and what you asked in it   *** MUST RAISE ***
      5. what "Postmortem: Dec 4 revert of end-of-run retry logic" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      6. what "Postmortem: Dec 10 revert of batch auto-delete" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      7. what "Postmortem: Dec 13 revert of batch context-manager refactor (PR #254)" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Release notes capture what shipped
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. second pair of eyes on every change; saw the full arc from PR through merge
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Release notes capture what shipped
      2. Announce the release to the team
    goal        0.1.12 shipped today; tag is out; release notes due; announce mail due
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   v0.1.12 is tagged, release notes are written and posted, announcement mail is sent to the team


==============================================================================
# 2024-12-18 — 3 conversation(s), 42 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 12 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Two PRs merged today and six more are over a month old; the team needs to clear the backlog before v0.1.13 lands.

    Today is Wednesday 18 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Two PRs merged today and six more are over a month old; the team needs to clear the backlog before v0.1.13 lands.
    
    What it should get through:
      1. Unblock or defer PR 78, PR 90, PR 228 (Dario Kestrel's waiting PRs)   [Dario Kestrel must raise this]
           - Dario Kestrel lists the three: vLLM example, disable-cache arg, expired batches quick fix
           - Gideon Halloway notes PR 161 depends on similar infrastructure
           - Dario Kestrel marks PR 228 for v0.1.13, defers PR 78 and PR 90 to backlog
      2. Move PR 106 (Konrad's text-message summarization example) forward   [Konrad Feltrin must raise this]
           - Konrad Feltrin reminds the room of PR 106 waiting 34 days
           - Dario Kestrel or Gideon Halloway agrees to review this week
           - Konrad Feltrin commits to landing in v0.1.13
      3. Clarify scope of PR 161 and PR 163 (Gideon Halloway's PRs)   [Gideon Halloway must raise this]
           - Gideon Halloway flags both as blocking observability work
           - Dario Kestrel notes infrastructure overlap with other refactors
           - Gideon Halloway either pulls them from stale pile or accepts deferral
    
    On the agenda: Triage the six stale PRs: PR 78, PR 90, PR 106, PR 133, PR 161, PR 163; Decide what blocks release vs what defers to next cycle; Route each to owner or close if superseded
    
    Meeting today: Weekly sync
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Dario to action PR 228 before v0.1.13; PR 106 assigned to reviewer; PR 161, PR 163, PR 78, PR 90 either pulled forward or explicitly deferred with rationale.
    
    Do NOT wrap before about 8 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 6 release(s) shipped, currently v0.1.12
      - 137 changes merged to date

    On the table
      - Runbook: handling curator.LLM incidents (Dario Kestrel)
      - Bulk LLM Inference: next-phase design (Dermot Callaghan)
      - v0.1.12 release notes (Dario Kestrel)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 163: [curator-viewer] use getCacheDir helper function, add additional param for cache dir (Gideon Halloway)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 62: Support generation configuration for LLM
      - issue 86: Retry when structured output fails
      - issue 88: Add a way to disable caching for curator
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run

    DOES NOT EXIST YET (7 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - local-offline-inference
      - telemetry
      - — and 1184 function/class names and 156 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. approval authority and context on core refactors
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Unblock or defer PR 78, PR 90, PR 228 (Dario Kestrel's waiting PRs)   *** MUST RAISE ***
      2. Move PR 106 (Konrad's text-message summarization example) forward
      3. Clarify scope of PR 161 and PR 163 (Gideon Halloway's PRs)
      4. that the doc "Weekly notes: week of Dec 16 - v0.1.12 out" is done, and where the others can find it   *** MUST RAISE ***
      5. what "Runbook: handling curator.LLM incidents" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      6. what "Bulk LLM Inference: next-phase design" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Unblock or defer PR 78, PR 90, PR 228 (Dario Kestrel's waiting PRs)
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. ownership of examples workstream and recent merges
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Unblock or defer PR 78, PR 90, PR 228 (Dario Kestrel's waiting PRs)
      2. Move PR 106 (Konrad's text-message summarization example) forward   *** MUST RAISE ***
      3. Clarify scope of PR 161 and PR 163 (Gideon Halloway's PRs)
    goal        Move PR 106 (Konrad's text-message summarization example) forward
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. context on viewer and observability issues
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Unblock or defer PR 78, PR 90, PR 228 (Dario Kestrel's waiting PRs)
      2. Move PR 106 (Konrad's text-message summarization example) forward
      3. Clarify scope of PR 161 and PR 163 (Gideon Halloway's PRs)   *** MUST RAISE ***
      4. what "v0.1.12 release notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Clarify scope of PR 161 and PR 163 (Gideon Halloway's PRs)
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Dario to action PR 228 before v0.1.13; PR 106 assigned to reviewer; PR 161, PR 163, PR 78, PR 90 either pulled forward or explicitly deferred with rationale.


------------------------------------------------------------------------------
## #engineering — 14 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Dario has landed 10 commits including a generalized tracker and factory refactor; the team needs to validate the design before it hardens into the next release.

    Today is Wednesday 18 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Dario has landed 10 commits including a generalized tracker and factory refactor; the team needs to validate the design before it hardens into the next release.
    
    What it should get through:
      1. Walk through generalized tracker and abstract-method updates   [Dario Kestrel must raise this]
           - Dario Kestrel sketches the generalized tracker pattern across batch and online
           - Dermot Callaghan asks whether the factory still supports None backends cleanly
           - Dario Kestrel confirms typed-dict approach handles it; walk from there
      2. Verify SimpleLLM callers survive the split   [Dario Kestrel must raise this]
           - Konrad Feltrin points to the examples: do they still work with backend=None?
           - Dario Kestrel checks the default and notes any config bug surface
           - Dermot Callaghan suggests a quick integration test or manual smoke test
      3. Surface testing and design gaps before merge   [Dermot Callaghan must raise this]
           - Dermot Callaghan flags whether the refactor has test coverage for config edges
           - Dario Kestrel notes package-bump commit suggests version handling is in flight
           - Konrad Feltrin asks whether this blocks the examples merge or ships in parallel
    
    On the agenda: Tour the refactor: generalized tracker, config kwargs, request-processor handoff; Check SimpleLLM call sites and backward-compat surface; Flag design or testing gaps before v0.1.13
    
    Meeting today: Weekly sync
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Dario to confirm SimpleLLM backward-compat and flag any test gaps; Dermot Callaghan to sign off on design risk; Konrad Feltrin to understand the surface change for examples.
    
    Do NOT wrap before about 9 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 6 release(s) shipped, currently v0.1.12
      - 137 changes merged to date

    On the table
      - Bulk LLM Inference: next-phase design (Dermot Callaghan)
      - Onboarding: Petar Kovalenko on request-processing internals (Konrad Feltrin)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 163: [curator-viewer] use getCacheDir helper function, add additional param for cache dir (Gideon Halloway)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 62: Support generation configuration for LLM
      - issue 86: Retry when structured output fails
      - issue 88: Add a way to disable caching for curator
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run

    DOES NOT EXIST YET (7 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - local-offline-inference
      - telemetry
      - — and 1184 function/class names and 156 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. ten commits on core refactors, context on the factory/typed-dict/properties split underway
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Walk through generalized tracker and abstract-method updates   *** MUST RAISE ***
      2. Verify SimpleLLM callers survive the split   *** MUST RAISE ***
      3. Surface testing and design gaps before merge
      4. what "Bulk LLM Inference: next-phase design" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      5. what "Onboarding: petar on request-processing internals" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Walk through generalized tracker and abstract-method updates
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. fresh perspective on examples and API surface; recent merges of cleanup PRs
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Walk through generalized tracker and abstract-method updates
      2. Verify SimpleLLM callers survive the split
      3. Surface testing and design gaps before merge
    goal        Dario has landed 10 commits including a generalized tracker and factory refactor; the team needs to validate the design before it hardens into the next release.
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. design context from ws-012 and deep knowledge of SimpleLLM folding strategy
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Walk through generalized tracker and abstract-method updates
      2. Verify SimpleLLM callers survive the split
      3. Surface testing and design gaps before merge   *** MUST RAISE ***
    goal        Surface testing and design gaps before merge
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Dario to confirm SimpleLLM backward-compat and flag any test gaps; Dermot Callaghan to sign off on design risk; Konrad Feltrin to understand the surface change for examples.


------------------------------------------------------------------------------
## #pipeline — 16 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #pipeline: Seven commits to the core request pipeline services landed today; the team needs to validate the refactor preserves resilience and provider-integration stability.

    Today is Wednesday 18 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Seven commits to the core request pipeline services landed today; the team needs to validate the refactor preserves resilience and provider-integration stability.
    
    What it should get through:
      1. Generalized tracker: does it work for both batch and online?   [Dario Kestrel must raise this]
           - Dario Kestrel walks the abstract tracker interface and batch/online concrete types
           - Gideon Halloway asks whether progress reporting still fires for streamed responses
           - Dario Kestrel or Dermot Callaghan confirms the telemetry surface is unchanged
      2. Provider backends survive the config refactor   [Dario Kestrel must raise this]
           - Dermot Callaghan flags whether the factory still routes Anthropic, OpenAI, vLLM cleanly
           - Dario Kestrel confirms typed-dict kwargs flow through to each backend
           - Gideon Halloway checks whether the v0.1.12 provider interop still holds
      3. Caching and resume flow through the request-processor handoff   [Dermot Callaghan must raise this]
           - Dermot Callaghan traces the cache-hit path through the new processor layer
           - Dario Kestrel confirms config persists through serialization and resume
           - Gideon Halloway validates that the cache tables still get written and read correctly
    
    On the agenda: Review the generalized tracker contract across batch and online paths; Check provider-integration surface after the refactor; Verify caching and resume paths still work with the new config layout
    
    Meeting today: Weekly sync
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Dario to confirm tracker and config factory work for both batch and online; Dermot Callaghan to validate caching and resume paths; Gideon Halloway to sign off on progress reporting and provider stability.
    
    Do NOT wrap before about 11 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 6 release(s) shipped, currently v0.1.12
      - 137 changes merged to date

    On the table
      - Bulk LLM Inference: next-phase design (Dermot Callaghan)
      - v0.1.12 release notes (Dario Kestrel)
      - Runbook: handling curator.LLM incidents (Dario Kestrel)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 163: [curator-viewer] use getCacheDir helper function, add additional param for cache dir (Gideon Halloway)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 62: Support generation configuration for LLM
      - issue 86: Retry when structured output fails
      - issue 88: Add a way to disable caching for curator
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run

    DOES NOT EXIST YET (7 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - local-offline-inference
      - telemetry
      - — and 1184 function/class names and 156 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. seven commits on core refactor, generalized tracker, generation-config factory, request-processor handoff
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Generalized tracker: does it work for both batch and online?   *** MUST RAISE ***
      2. Provider backends survive the config refactor   *** MUST RAISE ***
      3. Caching and resume flow through the request-processor handoff
      4. what "Bulk LLM Inference: next-phase design" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      5. what "v0.1.12 release notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Generalized tracker: does it work for both batch and online?
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. operational knowledge of how the request layer handles errors, retries, and provider drift
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Generalized tracker: does it work for both batch and online?
      2. Provider backends survive the config refactor
      3. Caching and resume flow through the request-processor handoff   *** MUST RAISE ***
      4. what "Runbook: handling curator.LLM incidents" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Caching and resume flow through the request-processor handoff
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. understanding of progress tracking and run-level observability requirements
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Generalized tracker: does it work for both batch and online?
      2. Provider backends survive the config refactor
      3. Caching and resume flow through the request-processor handoff
    goal        Seven commits to the core request pipeline services landed today; the team needs to validate the refactor preserves resilience and provider-integration stability.
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Dario to confirm tracker and config factory work for both batch and online; Dermot Callaghan to validate caching and resume paths; Gideon Halloway to sign off on progress reporting and provider stability.


==============================================================================
# 2024-12-19 — 1 conversation(s), 10 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #engineering — 10 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #engineering: Dario landed 12 commits today on batch processor and config changes; config split created friction with examples and SimpleLLM callers; needs a quick sync on what still needs attention

    Today is Thursday 19 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Dario landed 12 commits today on batch processor and config changes; config split created friction with examples and SimpleLLM callers; needs a quick sync on what still needs attention
    
    What it should get through:
      1. Verify batch processor fixes are complete   [Dario Kestrel must raise this]
           - Dario Kestrel outlines the openai and anthropic batch processor bugs he found
           - Dermot Callaghan asks whether these show a pattern in how batch lifecycle is handled
           - Dario Kestrel confirms both were around request processor config initialization
      2. Confirm examples and integration tests are now passing   [Dario Kestrel must raise this]
           - Dario Kestrel reports on the example integration test fixes he landed
           - Dermot Callaghan checks whether SimpleLLM config defaults match what the new factory expects
           - both agree the backend=None default issue is closed
    
    On the agenda: Config refactoring aftermath: what broke in examples; Batch processor fixes for anthropic and openai; Integration test status and blockers
    
    Belongs in this channel: day to day work on the services this channel owns: design debate, code review, blockers between the people who own them, and progress on the current phase.
    Does NOT belong here: a production incident happening right now, which goes to the cross-cutting channel, and company-wide news, which goes to the announce channel.
    
    Wrap when: Dario and Dermot Callaghan align on whether the config refactor is landing cleanly and what to watch for in the next integration round; no blockers identified for merging into dev.
    
    Do NOT wrap before about 7 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 6 release(s) shipped, currently v0.1.12
      - 137 changes merged to date

    On the table
      - Bulk LLM Inference: next-phase design (Dermot Callaghan)
      - Runbook: handling curator.LLM incidents (Dario Kestrel)
      - Bulk LLM Inference: next-phase design (Dermot Callaghan)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 163: [curator-viewer] use getCacheDir helper function, add additional param for cache dir (Gideon Halloway)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 62: Support generation configuration for LLM
      - issue 86: Retry when structured output fails
      - issue 88: Add a way to disable caching for curator
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run

    DOES NOT EXIST YET (7 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - local-offline-inference
      - telemetry
      - — and 1184 function/class names and 156 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. 12 commits on batch processor fixes and config cleanup across anthropic, openai, and example integration tests
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Verify batch processor fixes are complete   *** MUST RAISE ***
      2. Confirm examples and integration tests are now passing   *** MUST RAISE ***
      3. what "Bulk LLM Inference: next-phase design" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      4. what "Runbook: handling curator.LLM incidents" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      5. what "Bulk LLM Inference: next-phase design" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Verify batch processor fixes are complete
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. ownership of bulk-llm-inference and multimodal-prompts; sees the config ripple effects
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Verify batch processor fixes are complete
      2. Confirm examples and integration tests are now passing
    goal        Dario landed 12 commits today on batch processor and config changes; config split created friction with examples and SimpleLLM callers; needs a quick sync on what still needs attention
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   Dario and Dermot Callaghan align on whether the config refactor is landing cleanly and what to watch for in the next integration round; no blockers identified for merging into dev.


==============================================================================
# 2024-12-20 — 1 conversation(s), 8 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: PR PR 281 merged today; four related issues opened same day signal more work in this area

    Today is Friday 20 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: PR PR 281 merged today; four related issues opened same day signal more work in this area
    
    What it should get through:
      1. Confirm PR 281 exception handling is sufficient   [Dario Kestrel must raise this]
           - Konrad Feltrin presents the three commits and litellm version pin
           - Dario Kestrel notes it already approved and asks about test coverage
           - Gideon Halloway asks if visibility into failed batches is affected
      2. Triage four new issues and assign owners   [Dario Kestrel must raise this]
           - Dario Kestrel lists 278, 279, 282, 283 and their overlap with PR 281
           - Konrad Feltrin notes 282 and 279 are related to provider error cases
           - Gideon Halloway flags 283 (batch failure logging) as tied to observability work
    
    On the agenda: Review PR 281 exception handling for litellm; Four new issues (278–283) opened today and their scope; Whether PR 280 (Google docstrings) blocks or ships in parallel
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: PR 281 lands confident; 278–283 are scoped and priorities set for next sprint. PR 280 ships when ready without blocking; it is settled that the batch job id is written to the cache directory only once the batch reaches a completed status
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 6 release(s) shipped, currently v0.1.12
      - 138 changes merged to date

    On the table
      - Bulk LLM Inference: next-phase design (Dermot Callaghan)
      - Runbook: handling curator.LLM incidents (Dario Kestrel)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 163: [curator-viewer] use getCacheDir helper function, add additional param for cache dir (Gideon Halloway)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 62: Support generation configuration for LLM
      - issue 86: Retry when structured output fails
      - issue 88: Add a way to disable caching for curator
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run

    DOES NOT EXIST YET (7 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - local-offline-inference
      - telemetry
      - — and 1184 function/class names and 156 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Three commits fixing litellm error handling and test formatting
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Confirm PR 281 exception handling is sufficient
      2. Triage four new issues and assign owners
    goal        PR PR 281 merged today; four related issues opened same day signal more work in this area
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Already approved PR 281; owns the request-processing layer where this lands
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Confirm PR 281 exception handling is sufficient   *** MUST RAISE ***
      2. Triage four new issues and assign owners   *** MUST RAISE ***
      3. On the batch id persistence bit: we write the id into the cache dir when the batch comes back done, not before. A record that points at a batch we haven't confirmed anything about is just a landmine for the next run, and I'd rather have no entry than an entry we can't trust. So the write happens off the terminal status, same place we write the reassembled results.   *** MUST SETTLE (clue t3.r1.h1) ***
      4. what "Bulk LLM Inference: next-phase design" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
      5. what "Runbook: handling curator.LLM incidents" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Confirm PR 281 exception handling is sufficient
    available   around today

  Gideon Halloway  (gideon)
    role        Core Engineer — Dataset Viewer & Run Observability. Owns observability and progress tracking; can spot if exception handling breaks visibility
    owns        online-request-processing, progress-and-cli, bulk-llm-inference, caching-and-resume
    agenda
      1. Confirm PR 281 exception handling is sufficient
      2. Triage four new issues and assign owners
    goal        PR PR 281 merged today; four related issues opened same day signal more work in this area
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   PR 281 lands confident; 278–283 are scoped and priorities set for next sprint. PR 280 ships when ready without blocking; it is settled that the batch job id is written to the cache directory only once the batch reaches a completed status


==============================================================================
# 2024-12-23 — 1 conversation(s), 8 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #releases — 8 turns, 3 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #releases: 0.1.13 tag is live; Konrad Feltrin just merged main and needs to confirm and announce

    Today is Monday 23 December 2024. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: 0.1.13 tag is live; Konrad Feltrin just merged main and needs to confirm and announce
    
    What it should get through:
      1. Lock in release notes and announce   [Konrad Feltrin must raise this]
           - Konrad Feltrin states the tag is live and o1 changes are baked in
           - Dario Kestrel confirms no blocking issues
           - Konrad Feltrin posts announcement
    
    On the agenda: Confirm 0.1.13 is built and tagged; Review what shipped: o1 structured output, date-based versions, formatting; Announce to the team
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: 0.1.13 release notes written and announcement sent; team knows o1 model support shipped
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Everything Through a Reviewed PR: Building the Request Pipeline

    Settled
      - 7 release(s) shipped, currently 0.1.13
      - 141 changes merged to date

    On the table
      - 0.1.13 release notes (Konrad Feltrin)
      - announce-0-1-13 (Konrad Feltrin)
      - v0.1.12 release notes (Dario Kestrel)
      - PR 78: vLLM example for OpenAIOnlineParallelProcessor (Dario Kestrel)
      - PR 90: Add an argument to disable cache for Prompter (Dario Kestrel)
      - PR 106: Add an example for summarizing text messages between two people. (Konrad Feltrin)
      - PR 133: adding an env example file (Otto Brennan)
      - PR 161: [Curator Usage Example] Prometheus LLM Judge evaluation (Gideon Halloway)
      - PR 163: [curator-viewer] use getCacheDir helper function, add additional param for cache dir (Gideon Halloway)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 48: ReadME documentation on batch
      - issue 50: Vary batch size based on request numbers
      - issue 52: Support multiple samples per request
      - issue 62: Support generation configuration for LLM
      - issue 86: Retry when structured output fails
      - issue 88: Add a way to disable caching for curator
      - issue 92: [UI] Detail View support better JSON / markdown etc file extension views
      - issue 93: [UI] Display status of the run

    DOES NOT EXIST YET (7 names)
      - agentic-curation
      - blocks-and-recipes
      - code-execution
      - finetuning
      - local-offline-inference
      - telemetry
      - — and 1185 function/class names and 151 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. Just merged main, version bumped, release tag live
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Lock in release notes and announce   *** MUST RAISE ***
      2. that the doc "0.1.13 release notes" is done, and where the others can find it   *** MUST RAISE ***
      3. that "0.1.13 is out" has gone out, and what you asked in it   *** MUST RAISE ***
      4. that "Weekly update: week of Dec 16" has gone out, and what you asked in it   *** MUST RAISE ***
      5. what "v0.1.12 release notes" actually says, having opened it yourself, and whether it answers your part (if it does not exist yet, say that plainly and leave it to whoever owes it)   *** MUST RAISE ***
    goal        Lock in release notes and announce
    available   around today

  Dario Kestrel  (dario)
    role        Core Engineer, Request Processing. Knowledge of what shipped and any last-minute issues
    owns        bulk-llm-inference, caching-and-resume, online-request-processing, provider-integrations
    agenda
      1. Lock in release notes and announce
    goal        0.1.13 tag is live; Konrad Feltrin just merged main and needs to confirm and announce
    available   around today

  Dermot Callaghan  (dermot)
    role        Founding Software Engineer — Core Pipeline & Release. Ownership of the bulk-llm-inference changes that landed
    owns        examples-cookbooks, bulk-llm-inference, multimodal-prompts, release-and-ci
    agenda
      1. Lock in release notes and announce
    goal        0.1.13 tag is live; Konrad Feltrin just merged main and needs to confirm and announce
    available   around today

### 4. How it should land

    lands as  resolves
    leaving   0.1.13 release notes written and announcement sent; team knows o1 model support shipped

