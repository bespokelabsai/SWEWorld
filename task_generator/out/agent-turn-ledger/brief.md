The multi-turn agent conversation record: what counts as a turn, what is durable, and
how a resumed run works out whose turn it is.

The area, concretely:
- `src/bespokelabs/curator/agent/processor.py` — `MultiTurnAgenticProcessor.run()`.
  On a fresh run the seed message is appended to `self.conversation_history` (line
  105) and `start_step = 0` (line 106); it is never written to `responses_0.jsonl`.
  `load_cache()` (lines 69-84) rebuilds history from that file alone, so a resumed
  run's history is the fresh run's minus the seed. `run()` then dispatches on
  `if step % 2 == 0` (line 112) to decide which agent speaks — a parity over a list
  whose length depends on whether the seed was counted, and it is counted in one
  case and not the other.
- The same `load_cache` returns `len(self.conversation_history)` as a step cursor
  (line 84) and, on two other branches, returns `self.max_length` as a "finished"
  sentinel (lines 79 and 83). The caller's `if start_step == self.max_length`
  (line 101) therefore cannot tell a completed conversation from one that happens to
  have run exactly that many messages.
- `max_length` is in two units at once. It bounds a range over *messages*
  (line 110) and is handed to `AgentStatusTracker(max_turns=...)` (line 55), while
  `agent.py:78` documents it as "the maximum number of turns in the conversation"
  and `agent_response.py:88` reports it as a request total.
- `src/bespokelabs/curator/status_tracker/agent_status_tracker.py` — `update_turn`
  (lines 249-253) increments `current_turn` and `num_responses` and, when
  `response_success` is false, `num_errors` as well — so a failed turn counts as
  both. `load_cache` calls the same method for every *cached* response, so a resume
  re-counts the whole history into the live totals.
- `_transform_conversation_history` (line 194) takes `[msg for msg in
  request.messages if msg["role"] == "system"][0]`, which raises when no system
  prompt was configured, then deletes the last history entry and re-inserts the
  system message at index 0.
- `create_dataset_file` (lines 218-225) reads only `responses_0.jsonl`, so the
  dataset a caller gets back never contains the message that started the
  conversation. `Agent.is_completed` (agent.py lines 40-49) returns `False`
  unconditionally.

Nothing states whether the seed is a durable turn — written, counted, present in the
dataset — or a prompt-only artifact; whether `max_length` bounds messages, exchanges
or per-agent turns; whether "whose turn is it" is derived from the log's last author
or from a counter kept beside it, and what happens when those two disagree; or
whether a failed turn consumes one. Two coherent designs exist and the file has half
of each: the append-only log as the single source of truth, or a cursor persisted
alongside it. Read both files and specify one.

Out of scope: `Agent._hash_fingerprint` and the `xxh64(seed_message)` run identity
(agent.py lines 193-196). That is another task's subject.

Constraints: pure and deterministic, no network, no sleeping, no threads. Clock
injected — the tracker uses `time.time()` and the agent `datetime.now()`. Testable by
constructing the processor with duck-typed fake agents (`name`, `model_name`,
`prompt_formatter`, `_request_processor`, `is_completed`), a hand-written
`responses_0.jsonl` in a temp directory, and a fake `call_single_request` returning a
canned `GenericResponse`. `aiohttp.ClientSession()` is constructed but never reaches
a socket; no real provider, no real network.
