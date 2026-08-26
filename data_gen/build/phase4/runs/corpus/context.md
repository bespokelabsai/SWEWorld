# Phase 4: what the simulation is told

Four things reach a model: the channel scenario and briefing (which the DIRECTOR sees, to pick who speaks next), the shared ground (which EVERYONE in the channel holds), each person's own grounding, and the turn budget.

Worth keeping in mind while reading:

1. **This is today, not history.** Everyone is told the state as of that morning.
2. **MUST RAISE** belongs to the person driving it; the engine holds the conversation open until it lands. **MUST SETTLE** is a planted clue: the engine pushes for it to be stated as a conclusion, and a channel-day that does not get its INFORMATION across is run again — told what was missing. The words are the persona's own; what is fixed is the point, and any identifier named under it.
3. **The forbidden list does not exist yet** on that date. Naming it is the failure this whole pipeline is built to prevent.


==============================================================================
# 2026-01-27 — 1 conversation(s), 8 turns budgeted
==============================================================================

------------------------------------------------------------------------------
## #code-review — 8 turns, 2 people
------------------------------------------------------------------------------

### 1. What the DIRECTOR is told

Channel #code-review: Fresh PR needs initial eyes; five older PRs waiting suggest review capacity is sparse with team departed

    Today is Tuesday 27 January 2026. This conversation is happening NOW and everything below is true as of this morning.
    
    Why it is happening: Fresh PR needs initial eyes; five older PRs waiting suggest review capacity is sparse with team departed
    
    What it should get through:
      1. Get initial feedback on GEPA integration approach   [Nikolai Berresford must raise this]
           - Nikolai Berresford describes what GEPA adds and where it plugs in
           - Konrad Feltrin asks about interaction with existing finetuning flows
           - Nikolai Berresford explains decision to land integration in this pass
      2. Identify any blockers before full review cycle   [Konrad Feltrin must raise this]
           - Konrad Feltrin scans for conflicts with code-execution or finetuning services
           - Nikolai Berresford clarifies scope boundaries
           - both agree on next step: full review or defer to later pass
    
    On the agenda: Overview of GEPA integration scope and API surface; Assessment of integration points with existing finetuning subsystem; Blockers or design concerns before full code review
    
    Belongs in this channel: the practice itself: what is broken now, what is waiting on review, what is shipping, and who is picking it up.
    Does NOT belong here: routine work on one service, which belongs in the team channel that owns it.
    
    Wrap when: Nikolai gets early feedback on integration direction; both agree whether this needs full review now or can wait given sparse reviewer availability
    
    Do NOT wrap before about 6 exchanges. There is more here than a single answer: if it feels finished early, the part that has not been said yet is somebody's — find who still owes something above and go to them.

### 2. What EVERYONE in the channel shares

    Project    Millrow
    Milestone  Solo Maintainer, Second Act: Fine-Tuning and Drive-By PRs

    Settled
      - 25 release(s) shipped, currently v0.1.26
      - 373 changes merged to date

    On the table
      - PR 653: Shreyas/finetuning client (Nikolai Berresford)
      - PR 675: add default app id parameter for curator llm (Nolan Whitfield)
      - PR 690: Fix Multimodal Gemini Batch Request Creation (Emil Brandvold)
      - PR 693: Streaming support for openAI's online requests  (Emil Brandvold)
      - PR 698: fix: ensure proxy support and bump anthropic dependency (Dario Kestrel)
      - PR 709: Integrate GEPA into Curator (Nikolai Berresford)

    Settled decisions everyone works to
      - House style for pointing at work in chat: a pull request or issue goes by its number with the word in front (issue 163, PR 528), never a bare #number — in Mattermost that opens a channel autocomplete. A wiki page goes by its title. Say it in full the first time, short form after.

    Open questions
      - issue 52: Support multiple samples per request
      - issue 102: Clarify that we must return a dictionary without Pydantic objects for each row
      - issue 121: Should we handle pydantic to dict and back for the user when adding to a row? 
      - issue 124: inspect(func) is sensitive to comments and whitespace - cache invalidates
      - issue 207: implementation of `has_capacity` using rate limit info from the headers returned from some providers/models
      - issue 233: Automatically detect the rate limits
      - issue 290: ModuleNotFoundError: No module named 'resource'
      - issue 293: OpenAI Usage and Costs via API

    DOES NOT EXIST YET (1 names)
      - — and 262 function/class names and 26 files that this codebase only grows LATER. Do not name a function, class or file unless it has already come up in this conversation or you own the code it is in.

### 3. What EACH PERSON is told

  Nikolai Berresford  (nikolai)
    role        Research Platform Engineer — Code Execution & Data-Generation Recipes. GEPA integration design and implementation details
    owns        code-execution, release-and-ci, telemetry
    agenda
      1. Get initial feedback on GEPA integration approach   *** MUST RAISE ***
      2. Identify any blockers before full review cycle
    goal        Get initial feedback on GEPA integration approach
    available   around today

  Konrad Feltrin  (konrad)
    role        Founding Maintainer, Curation Platform. codebase context and finetuning ownership
    owns        examples-cookbooks, code-execution, finetuning
    agenda
      1. Get initial feedback on GEPA integration approach
      2. Identify any blockers before full review cycle   *** MUST RAISE ***
    goal        Identify any blockers before full review cycle
    available   around today

### 4. How it should land

    lands as  partial
    leaving   Nikolai gets early feedback on integration direction; both agree whether this needs full review now or can wait given sparse reviewer availability

