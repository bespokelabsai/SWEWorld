#!/bin/bash
# The reference solution: the whole specification, as an agent would have written
# it. The diff below is what the oracle build actually produced — generated, not a
# hand-written patch script that can drift out of step with the suite.
set -euo pipefail
cd /workdir/curator
cat > /tmp/oracle.patch <<'CURATOR_ORACLE_PATCH_EOF'
diff --git a/src/bespokelabs/curator/agent/agent.py b/src/bespokelabs/curator/agent/agent.py
index 150970e..7d2550f 100644
--- a/src/bespokelabs/curator/agent/agent.py
+++ b/src/bespokelabs/curator/agent/agent.py
@@ -7,6 +7,7 @@ from xxhash import xxh64
 from bespokelabs import curator
 from bespokelabs.curator.agent.agent_response import MultiTurnResponse
 from bespokelabs.curator.agent.processor import MultiTurnAgenticProcessor
+from bespokelabs.curator.agent.turn_ledger import COMPLETION_SENTINEL
 from bespokelabs.curator.client import Client
 from bespokelabs.curator.constants import PUBLIC_CURATOR_VIEWER_HOME_URL
 from bespokelabs.curator.db import MetadataDB
@@ -37,16 +38,22 @@ class Agent(curator.LLM):
         self.name = name
         super().__init__(*args, **kwargs)
 
-    def is_completed(self, response: str) -> bool:
+    def is_completed(self, response: t.Any) -> bool:
         """Check if the agent's response is signals conversation completion.
 
+        A response signals completion when it is a string ending with
+        `COMPLETION_SENTINEL`, ignoring trailing whitespace. Anything else - a
+        structured response, or nothing at all - does not.
+
         Args:
-            response (str): The response string to check.
+            response (Any): The response to check.
 
         Returns:
             bool: True if the conversation is completed, False otherwise.
         """
-        return False
+        if not isinstance(response, str):
+            return False
+        return response.rstrip().endswith(COMPLETION_SENTINEL)
 
     def __str__(self):
         """Return a string representation of the agent.
@@ -75,19 +82,29 @@ class MultiTurnAgents:
     Attributes:
         seeder (Agent): The agent that initiates the conversation.
         partner (Agent): The agent that responds to the seeder.
-        max_length (int): The maximum number of turns in the conversation.
+        max_length (int): The maximum number of responses generated in the conversation.
         seed_message (str): The initial message to start the conversation.
     """
 
-    def __init__(self, seeder: Agent, partner: Agent, max_length: int, seed_message: str):
+    def __init__(
+        self,
+        seeder: Agent,
+        partner: Agent,
+        max_length: int,
+        seed_message: str,
+        *,
+        now_fn: t.Callable[[], datetime] = datetime.now,
+    ):
         """Initialize a MultiTurnAgents instance.
 
         Args:
             seeder (Agent): The agent that initiates the conversation.
             partner (Agent): The agent that responds to the seeder.
-            max_length (int): The maximum number of turns in the conversation.
+            max_length (int): The maximum number of responses generated in the conversation.
+                              Note: The seed message is not one of them.
             seed_message (str): The initial message to start the conversation.
                                 Note: This message is send to partner agent.
+            now_fn (Callable[[], datetime.datetime]): The clock stamped on the seed record.
 
         Raises:
             AssertionError: If seeder and partner have the same name.
@@ -98,7 +115,7 @@ class MultiTurnAgents:
         self.seed_message = seed_message
 
         assert self.seeder.name != self.partner.name, "Seeder and partner must have different names"
-        self._processor = MultiTurnAgenticProcessor(self.seeder, self.partner, self.max_length, self.seed_message)
+        self._processor = MultiTurnAgenticProcessor(self.seeder, self.partner, self.max_length, self.seed_message, now_fn=now_fn)
 
     def _setup_metadata(self, fingerprint: str) -> dict:
         """Set up metadata for the curator.
diff --git a/src/bespokelabs/curator/agent/agent_response.py b/src/bespokelabs/curator/agent/agent_response.py
index 44ac6ae..3209858 100644
--- a/src/bespokelabs/curator/agent/agent_response.py
+++ b/src/bespokelabs/curator/agent/agent_response.py
@@ -89,7 +89,7 @@ class MultiTurnResponse:
             succeeded=tracker.num_responses,
             failed=tracker.num_errors,
             in_progress=0,  # AgentStatusTracker doesn't track this
-            cached=0,  # AgentStatusTracker doesn't track this
+            cached=tracker.num_cached,
         )
 
         # Update performance statistics
diff --git a/src/bespokelabs/curator/agent/processor.py b/src/bespokelabs/curator/agent/processor.py
index 907c702..024bd68 100644
--- a/src/bespokelabs/curator/agent/processor.py
+++ b/src/bespokelabs/curator/agent/processor.py
@@ -1,3 +1,4 @@
+import datetime
 import json
 import os
 import typing as t
@@ -8,9 +9,20 @@ from datasets import Dataset
 from datasets.arrow_writer import ArrowWriter
 
 from bespokelabs.curator.agent.agent_response import AgentResponse
+from bespokelabs.curator.agent.turn_ledger import (
+    RESPONSES_FILENAME,
+    SEED_FINISH_REASON,
+    TurnLedger,
+    build_ledger,
+    build_seed_record,
+    read_log,
+    verify_sidecar,
+    write_sidecar,
+)
 from bespokelabs.curator.log import logger
 from bespokelabs.curator.request_processor.online.base_online_request_processor import APIRequest
 from bespokelabs.curator.status_tracker.agent_status_tracker import AgentStatusTracker, AgentTurn
+from bespokelabs.curator.types.generic_request import GenericRequest
 from bespokelabs.curator.types.generic_response import GenericResponse
 
 if t.TYPE_CHECKING:
@@ -24,29 +36,46 @@ class MultiTurnAgenticProcessor:
     and a partner agent, managing the conversation history, caching, and dataset
     creation. It supports both new conversations and resuming from cached states.
 
+    The conversation is kept in an append-only log, ``responses_0.jsonl``, whose first
+    line is the seed message; the log, read back as a :class:`TurnLedger`, decides who
+    speaks next and when the conversation is over.
+
     Attributes:
         seeder (Agent): The agent that initiates the conversation.
         partner (Agent): The agent that responds to the seeder.
-        max_length (int): The maximum number of turns in the conversation.
+        max_length (int): The budget of model-generated responses; the seed is not one.
         seed_message (str): The initial message to start the conversation.
+        now_fn (Callable[[], datetime.datetime]): The clock stamped on the seed record.
         conversation_history (list): List of message dictionaries containing role and content.
+        ledger (Optional[TurnLedger]): The state of the conversation, as last read or written.
         status_tracker (AgentStatusTracker): Tracks the status of the conversation.
     """
 
-    def __init__(self, seeder: "Agent", partner: "Agent", max_length: int, seed_message: str):
+    def __init__(
+        self,
+        seeder: "Agent",
+        partner: "Agent",
+        max_length: int,
+        seed_message: str,
+        now_fn: t.Callable[[], datetime.datetime] = datetime.datetime.now,
+    ):
         """Initialize a MultiTurnAgenticProcessor instance.
 
         Args:
             seeder (Agent): The agent that initiates the conversation.
             partner (Agent): The agent that responds to the seeder.
-            max_length (int): The maximum number of turns in the conversation.
+            max_length (int): The maximum number of responses generated in the conversation.
             seed_message (str): The initial message to start the conversation.
+            now_fn (Callable[[], datetime.datetime]): The clock stamped on the seed record.
         """
         self.seeder = seeder
         self.partner = partner
         self.max_length = max_length
         self.seed_message = seed_message
-        self.conversation_history = []
+        self.now_fn = now_fn
+        self.conversation_history: list[dict[str, str]] = []
+        self.ledger: t.Optional[TurnLedger] = None
+        self._records: list[AgentResponse] = []
 
         # Create status tracker with model information
         self.status_tracker = AgentStatusTracker(
@@ -57,31 +86,23 @@ class MultiTurnAgenticProcessor:
             partner_model=self.partner.model_name,  # Use partner's model for cost tracking
         )
 
-    def load_cache(self, working_dir: str) -> int:
-        """Load cached conversation history from a JSONL file.
+    def load_cache(self, working_dir: str) -> TurnLedger:
+        """Load the cached conversation from a working directory.
 
         Args:
             working_dir (str): Directory containing the cached conversation file.
 
         Returns:
-            int: The number of messages loaded from the cache.
+            TurnLedger: The state of the cached conversation. Empty when there is no log.
+
+        Raises:
+            TurnLedgerCorruptError: If a line of the log is not a valid agent response.
+            TurnLedgerDesyncError: If turn_ledger.json disagrees with the log.
         """
-        cache_file = os.path.join(working_dir, "responses_0.jsonl")
-        if os.path.exists(cache_file):
-            with open(cache_file, "r") as f:
-                for line in f:
-                    response = AgentResponse.model_validate_json(line)
-                    self.conversation_history.append({"role": response.name, "content": response.response_message})
-                    # Update status tracker for cached responses
-                    if response.name == self.seeder.name:
-                        self.status_tracker.update_turn(AgentTurn.SEEDER)
-                        if self.seeder.is_completed(response.response_message):
-                            return self.max_length
-                    else:
-                        self.status_tracker.update_turn(AgentTurn.PARTNER)
-                        if self.partner.is_completed(response.response_message):
-                            return self.max_length
-        return len(self.conversation_history)
+        self._records = read_log(working_dir)
+        ledger = self._build_ledger()
+        self._adopt(verify_sidecar(working_dir, ledger))
+        return self.ledger
 
     async def run(self, working_dir: str) -> Dataset:
         """Execute the multi-turn conversation between agents.
@@ -95,67 +116,53 @@ class MultiTurnAgenticProcessor:
         Returns:
             Dataset: A HuggingFace Dataset containing the conversation history.
         """
-        request_file = os.path.join(working_dir, "responses_0.jsonl")
-        if os.path.exists(request_file):
-            start_step = self.load_cache(working_dir)
-            if start_step == self.max_length:
-                self.status_tracker.stop_tracker()
-                return Dataset.from_file(self.create_dataset_file(working_dir))
-        else:
-            self.conversation_history.append({"role": self.seeder.name, "content": self.seed_message})
-            start_step = 0
+        request_file = os.path.join(working_dir, RESPONSES_FILENAME)
+        ledger = self.load_cache(working_dir)
+        self.status_tracker.adopt_ledger(cached_responses=ledger.responses)
 
         async with aiohttp.ClientSession() as session:
             async with aiofiles.open(request_file, "a") as f:
-                for step in range(start_step, self.max_length):
+                if self.ledger.turns == 0:
+                    seed = build_seed_record(
+                        seeder_name=self.seeder.name,
+                        seed_message=self.seed_message,
+                        model_name=self.seeder.model_name,
+                        now=self.now_fn(),
+                    )
+                    await self.append_response(self.seeder.name, f, seed)
+                    await f.flush()
+                    self._record(seed, status="created")
+                    write_sidecar(working_dir, self.ledger)
+
+                while not self.ledger.completed:
+                    name = self.ledger.next_speaker
+                    agent = self._agent_for(name)
+                    turn = AgentTurn.SEEDER if name == self.seeder.name else AgentTurn.PARTNER
                     try:
-                        if step % 2 == 0:
-                            partener_request = self._transform_conversation_history(self.partner)
-                            partener_request = APIRequest(
-                                task_id=step,
-                                generic_request=partener_request,
-                                api_specific_request=self.partner._request_processor.create_api_specific_request_online(partener_request),
-                                attempts_left=1,
-                                prompt_formatter=self.partner.prompt_formatter,
-                            )
-                            partener_response = await self.partner._request_processor.call_single_request(partener_request, session, status_tracker=None)
-                            await self.append_response(self.partner.name, f, partener_response)
-                            self.conversation_history.append({"role": self.partner.name, "content": partener_response.response_message})
-                            self.status_tracker.update_turn(AgentTurn.PARTNER, token_usage=partener_response.token_usage, cost=partener_response.response_cost)
-                            if self._check_stop_condition(step, self.partner, partener_response.response_message):
-                                break
-                        else:
-                            seeder_request = self._transform_conversation_history(self.seeder)
-                            seeder_request = APIRequest(
-                                task_id=step,
-                                generic_request=seeder_request,
-                                api_specific_request=self.seeder._request_processor.create_api_specific_request_online(seeder_request),
-                                attempts_left=1,
-                                prompt_formatter=self.seeder.prompt_formatter,
-                            )
-                            seeder_response = await self.seeder._request_processor.call_single_request(seeder_request, session, status_tracker=None)
-                            await self.append_response(self.seeder.name, f, seeder_response)
-                            self.conversation_history.append({"role": self.seeder.name, "content": seeder_response.response_message})
-                            self.status_tracker.update_turn(AgentTurn.SEEDER, token_usage=seeder_response.token_usage, cost=seeder_response.response_cost)
-                            if self._check_stop_condition(step, self.seeder, seeder_response.response_message):
-                                break
+                        request = self._transform_conversation_history(agent)
+                        request = APIRequest(
+                            task_id=self.ledger.responses,
+                            generic_request=request,
+                            api_specific_request=agent._request_processor.create_api_specific_request_online(request),
+                            attempts_left=1,
+                            prompt_formatter=agent.prompt_formatter,
+                        )
+                        response = await agent._request_processor.call_single_request(request, session, status_tracker=None)
+                        await self.append_response(name, f, response)
+                        await f.flush()
+                        self._record(self._as_agent_response(name, response))
+                        self.status_tracker.update_turn(turn, token_usage=response.token_usage, cost=response.response_cost)
+                        write_sidecar(working_dir, self.ledger)
+                        if self.ledger.completion_reason == "agent_signal":
+                            logger.info(f"Agent {name} completed conversation at turn {self.ledger.turns - 1}.")
                     except Exception as e:
                         # Update status tracker with error
-                        if step % 2 == 0:
-                            self.status_tracker.update_turn(AgentTurn.PARTNER, response_success=False)
-                        else:
-                            self.status_tracker.update_turn(AgentTurn.SEEDER, response_success=False)
+                        self.status_tracker.update_turn(turn, response_success=False)
                         raise e
 
         self.status_tracker.stop_tracker()
         return Dataset.from_file(self.create_dataset_file(working_dir))
 
-    def _check_stop_condition(self, step: int, agent: "Agent", response_message: str) -> bool:
-        if agent.is_completed(response_message):
-            logger.info(f"Agent {agent.name} completed conversation at step {step}.")
-            return True
-        return False
-
     async def append_response(self, name: str, f, response: GenericResponse) -> None:
         """Append a response to the conversation history file.
 
@@ -168,43 +175,121 @@ class MultiTurnAgenticProcessor:
         response["name"] = name
         await f.write(json.dumps(response, default=str) + "\n")
 
-    def _transform_conversation_history(self, target_agent: "Agent"):
+    def _agent_for(self, name: str) -> "Agent":
+        """Return the agent a log line is attributed to.
+
+        Args:
+            name (str): The name of the agent.
+
+        Returns:
+            Agent: The seeder or the partner.
+
+        Raises:
+            KeyError: If the name is neither agent's.
+        """
+        return {self.seeder.name: self.seeder, self.partner.name: self.partner}[name]
+
+    def _is_completed(self, author: str, content: t.Any) -> bool:
+        """Check whether a message ends the conversation.
+
+        Args:
+            author (str): The name of the agent that wrote the message.
+            content (Any): The message itself.
+
+        Returns:
+            bool: True if the author's agent signals completion, False for an unknown author.
+        """
+        try:
+            agent = self._agent_for(author)
+        except KeyError:
+            return False
+        return agent.is_completed(content)
+
+    def _build_ledger(self, status: str = "verified") -> TurnLedger:
+        """Derive a ledger from the records read or written so far.
+
+        Args:
+            status (str): Where the ledger came from, one of LEDGER_STATUSES.
+
+        Returns:
+            TurnLedger: The state of the conversation.
+        """
+        return build_ledger(
+            self._records,
+            seeder_name=self.seeder.name,
+            partner_name=self.partner.name,
+            max_responses=self.max_length,
+            is_completed=self._is_completed,
+            status=status,
+        )
+
+    def _adopt(self, ledger: TurnLedger) -> None:
+        """Adopt a ledger as the processor's state.
+
+        Args:
+            ledger (TurnLedger): The ledger to adopt.
+        """
+        self.ledger = ledger
+        self.conversation_history = ledger.messages()
+
+    def _record(self, record: AgentResponse, status: t.Optional[str] = None) -> None:
+        """Add a freshly written record to the conversation and rebuild the ledger.
+
+        Args:
+            record (AgentResponse): The record just appended to the log.
+            status (Optional[str]): The status of the new ledger; the current one by default.
+        """
+        self._records.append(record)
+        self._adopt(self._build_ledger(status=status or self.ledger.status))
+
+    def _as_agent_response(self, name: str, response: GenericResponse) -> AgentResponse:
+        """Attribute a generic response to an agent.
+
+        Args:
+            name (str): The name of the agent that generated the response.
+            response (GenericResponse): The response to attribute.
+
+        Returns:
+            AgentResponse: The response as it was written to the log.
+        """
+        return AgentResponse.model_validate({**response.model_dump(), "name": name})
+
+    def _transform_conversation_history(self, target_agent: "Agent") -> GenericRequest:
         """Transform the conversation history into a format suitable for the target agent.
 
-        This method converts the conversation history into a format that the target agent
-        can process, including system prompts and proper role assignments.
+        Every message the target agent wrote becomes an assistant message and every other
+        message becomes a user message; the last message is then re-rendered by the agent's
+        prompt formatter, whose system prompt, if it has one, leads the request.
 
         Args:
             target_agent (Agent): The agent for whom the conversation history is being transformed.
 
         Returns:
-            APIRequest: A request object containing the transformed conversation history.
+            GenericRequest: A request object containing the transformed conversation history.
         """
         transformed_conversation_history = []
-        if len(self.conversation_history) == 1:
-            transformed_conversation_history.append({"role": "user", "content": self.conversation_history[0]["content"]})
-        else:
-            for message in self.conversation_history:
-                if message["role"] == target_agent.name:
-                    transformed_conversation_history.append({"role": "assistant", "content": message["content"]})
-                else:
-                    transformed_conversation_history.append({"role": "user", "content": message["content"]})
+        for message in self.conversation_history:
+            if message["role"] == target_agent.name:
+                transformed_conversation_history.append({"role": "assistant", "content": message["content"]})
+            else:
+                transformed_conversation_history.append({"role": "user", "content": message["content"]})
 
         request = target_agent.prompt_formatter.create_generic_request({"prompt": transformed_conversation_history[-1]["content"]}, 0)
-        system_prompt = [msg for msg in request.messages if msg["role"] == "system"][0]
+        system_prompts = [msg for msg in request.messages if msg["role"] == "system"]
         request.messages = [msg for msg in request.messages if msg["role"] != "system"]
 
         del transformed_conversation_history[-1]
         transformed_conversation_history += request.messages
         request.messages = transformed_conversation_history
-        request.messages.insert(0, system_prompt)
+        if system_prompts:
+            request.messages.insert(0, system_prompts[0])
         return request
 
     def create_dataset_file(self, working_dir: str) -> str:
         """Create a dataset file from the conversation history.
 
         This method converts the JSONL conversation history into an Arrow dataset file
-        for efficient storage and processing.
+        for efficient storage and processing. The seed is row 0.
 
         Args:
             working_dir (str): Directory where the dataset file will be created.
@@ -212,15 +297,20 @@ class MultiTurnAgenticProcessor:
         Returns:
             str: Path to the created dataset file.
         """
-        response_file = os.path.join(working_dir, "responses_0.jsonl")
+        response_file = os.path.join(working_dir, RESPONSES_FILENAME)
         dataset_file = os.path.join(working_dir, "dataset.arrow")
 
         with ArrowWriter(path=dataset_file) as writer:
             with open(response_file, "r") as f_in:
-                for line in f_in:
+                for turn, line in enumerate(f_in):
                     response = AgentResponse.model_validate_json(line)
                     row = response.model_dump()
-                    response = {"content": row["response_message"], "role": row["name"]}
+                    response = {
+                        "role": row["name"],
+                        "content": str(row["response_message"]),
+                        "turn": turn,
+                        "source": SEED_FINISH_REASON if turn == 0 else "response",
+                    }
                     # Write the row to the arrow file
                     writer.write(response)
 
diff --git a/src/bespokelabs/curator/agent/turn_ledger.py b/src/bespokelabs/curator/agent/turn_ledger.py
new file mode 100644
index 0000000..2dd2374
--- /dev/null
+++ b/src/bespokelabs/curator/agent/turn_ledger.py
@@ -0,0 +1,429 @@
+"""The durable record of a multi-turn agent conversation.
+
+A conversation between two agents lives in a single append-only log,
+``responses_0.jsonl``, beside a small JSON sidecar, ``turn_ledger.json``. The log
+is the authority: the sidecar only records what the log looked like the last time
+this library appended to it, so that a resumed run can notice a log that was
+edited or truncated behind its back.
+
+This module owns the vocabulary of that record: how the seed message is written
+as a turn, how the log is read back, and how the two files are compared.
+"""
+
+import datetime
+import json
+import os
+import typing as t
+from dataclasses import dataclass, replace
+
+from bespokelabs.curator.agent.agent_response import AgentResponse
+from bespokelabs.curator.types.generic_request import GenericRequest
+
+TURN_LEDGER_VERSION: int = 2
+TURN_LEDGER_FILENAME: str = "turn_ledger.json"
+RESPONSES_FILENAME: str = "responses_0.jsonl"
+SEED_FINISH_REASON: str = "seed"
+COMPLETION_SENTINEL: str = "<<END_OF_CONVERSATION>>"
+COMPLETION_REASONS: tuple[str, ...] = ("open", "budget", "agent_signal")
+LEDGER_STATUSES: tuple[str, ...] = ("created", "adopted", "verified")
+
+
+class TurnLedgerError(RuntimeError):
+    """Base class for every turn-ledger failure."""
+
+
+class TurnLedgerCorruptError(TurnLedgerError):
+    """Raised when a line of responses_0.jsonl cannot be read as an AgentResponse.
+
+    Attributes:
+        path (str): The log the bad line was read from.
+        line_number (int): The 1-based index of the line, counting every physical line.
+        reason (str): Why the line could not be read.
+    """
+
+    def __init__(self, path: str, line_number: int, reason: str) -> None:
+        """Initialize a TurnLedgerCorruptError.
+
+        Args:
+            path (str): The log the bad line was read from.
+            line_number (int): The 1-based index of the line, counting every physical line.
+            reason (str): Why the line could not be read.
+        """
+        self.path: str = path
+        self.line_number: int = line_number
+        self.reason: str = reason
+        super().__init__(f"{path}:{line_number} is not a valid agent response ({reason})")
+
+
+class TurnLedgerDesyncError(TurnLedgerError):
+    """Raised when turn_ledger.json disagrees with the log it sits beside.
+
+    Attributes:
+        path (str): The sidecar that disagrees.
+        log_responses (int): The number of responses the log holds.
+        recorded_responses (int): The number of responses the sidecar records.
+        log_last_author (Optional[str]): The author of the log's last entry.
+        recorded_last_author (Optional[str]): The last author the sidecar records.
+    """
+
+    def __init__(
+        self,
+        path: str,
+        log_responses: int,
+        recorded_responses: int,
+        log_last_author: t.Optional[str],
+        recorded_last_author: t.Optional[str],
+    ) -> None:
+        """Initialize a TurnLedgerDesyncError.
+
+        Args:
+            path (str): The sidecar that disagrees.
+            log_responses (int): The number of responses the log holds.
+            recorded_responses (int): The number of responses the sidecar records.
+            log_last_author (Optional[str]): The author of the log's last entry.
+            recorded_last_author (Optional[str]): The last author the sidecar records.
+        """
+        self.path: str = path
+        self.log_responses: int = log_responses
+        self.recorded_responses: int = recorded_responses
+        self.log_last_author: t.Optional[str] = log_last_author
+        self.recorded_last_author: t.Optional[str] = recorded_last_author
+        super().__init__(
+            f"{path} records {recorded_responses} response(s) last authored by "
+            f"{recorded_last_author!r}, the log holds {log_responses} last authored by "
+            f"{log_last_author!r}"
+        )
+
+
+@dataclass(frozen=True)
+class TurnEntry:
+    """One line of the log, read back.
+
+    Attributes:
+        turn (int): The 0-based index of the line in the log; the seed is 0.
+        author (str): The agent name the line was written under.
+        content (str): The response message, coerced with str() when it is not already one.
+        source (str): "seed" for turn 0, "response" for every other turn.
+    """
+
+    turn: int
+    author: str
+    content: str
+    source: str
+
+
+@dataclass(frozen=True)
+class TurnLedger:
+    """Everything the log says about a conversation.
+
+    Attributes:
+        entries (tuple[TurnEntry, ...]): The log, in log order.
+        seeder_name (str): The name of the agent that seeded the conversation.
+        partner_name (str): The name of the agent that answers the seeder.
+        max_responses (int): The budget of model-generated responses; the seed is not one.
+        responses (int): The number of generated responses, len(entries) - 1, never negative.
+        turns (int): The number of entries, seed included.
+        next_speaker (Optional[str]): The agent that speaks next; None if the conversation is over.
+        last_author (Optional[str]): The author of the last entry; None for an empty log.
+        interleave_faults (int): The number of entries written by the author of the entry before them.
+        completed (bool): Whether the conversation is over.
+        completion_reason (str): One of COMPLETION_REASONS.
+        status (str): One of LEDGER_STATUSES.
+    """
+
+    entries: tuple[TurnEntry, ...]
+    seeder_name: str
+    partner_name: str
+    max_responses: int
+    responses: int
+    turns: int
+    next_speaker: t.Optional[str]
+    last_author: t.Optional[str]
+    interleave_faults: int
+    completed: bool
+    completion_reason: str
+    status: str
+
+    def messages(self) -> list[dict[str, str]]:
+        """Return the conversation as role/content dictionaries.
+
+        Returns:
+            list[dict[str, str]]: One ``{"role": author, "content": content}`` per entry, in log order.
+        """
+        return [{"role": entry.author, "content": entry.content} for entry in self.entries]
+
+    def sidecar_state(self) -> dict[str, t.Any]:
+        """Return the state written to turn_ledger.json.
+
+        Returns:
+            dict[str, t.Any]: The eight keys the sidecar holds.
+        """
+        return {
+            "version": TURN_LEDGER_VERSION,
+            "responses": self.responses,
+            "turns": self.turns,
+            "last_author": self.last_author,
+            "next_speaker": self.next_speaker,
+            "interleave_faults": self.interleave_faults,
+            "completed": self.completed,
+            "completion_reason": self.completion_reason,
+        }
+
+
+def build_seed_record(*, seeder_name: str, seed_message: str, model_name: str, now: datetime.datetime) -> AgentResponse:
+    """Build the record that makes the seed message a durable turn.
+
+    Args:
+        seeder_name (str): The agent the seed message is attributed to.
+        seed_message (str): The message that starts the conversation.
+        model_name (str): The model of the seeding agent.
+        now (datetime.datetime): The timestamp stamped on the record.
+
+    Returns:
+        AgentResponse: The first line of the log.
+    """
+    generic_request = GenericRequest(
+        model=model_name,
+        messages=[{"role": "user", "content": seed_message}],
+        original_row={"prompt": seed_message},
+        original_row_idx=0,
+        response_format=None,
+        generation_params={},
+        is_multimodal_prompt=False,
+    )
+    # AgentResponse is a pydantic model wrapped in a dataclass, so it is built by validation.
+    return AgentResponse.model_validate(
+        {
+            "name": seeder_name,
+            "response_message": seed_message,
+            "parsed_response_message": None,
+            "response_errors": None,
+            "raw_response": None,
+            "raw_request": None,
+            "generic_request": generic_request,
+            "created_at": now,
+            "finished_at": now,
+            "token_usage": None,
+            "response_cost": 0.0,
+            "finish_reason": SEED_FINISH_REASON,
+        }
+    )
+
+
+def read_log(working_dir: str) -> list[AgentResponse]:
+    """Read every response recorded in a working directory.
+
+    Blank lines are skipped; a line that cannot be read as an AgentResponse is an error.
+
+    Args:
+        working_dir (str): The directory holding responses_0.jsonl.
+
+    Returns:
+        list[AgentResponse]: The records, in log order. Empty when there is no log.
+
+    Raises:
+        TurnLedgerCorruptError: If a non-blank line is not a valid agent response.
+    """
+    log_file = os.path.join(working_dir, RESPONSES_FILENAME)
+    if not os.path.exists(log_file):
+        return []
+
+    records: list[AgentResponse] = []
+    with open(log_file, "r") as f:
+        for line_number, line in enumerate(f, start=1):
+            if not line.strip():
+                continue
+            try:
+                records.append(AgentResponse.model_validate_json(line))
+            except Exception as e:
+                raise TurnLedgerCorruptError(log_file, line_number, str(e)) from e
+    return records
+
+
+def _entry_content(record: AgentResponse) -> str:
+    """Return a record's response message as a string.
+
+    Args:
+        record (AgentResponse): The record to read.
+
+    Returns:
+        str: The response message, coerced with str() when it is not already a string.
+    """
+    message = record.response_message
+    return message if isinstance(message, str) else str(message)
+
+
+def build_ledger(
+    records: t.Sequence[AgentResponse],
+    *,
+    seeder_name: str,
+    partner_name: str,
+    max_responses: int,
+    is_completed: t.Callable[[str, t.Any], bool],
+    status: str = "verified",
+) -> TurnLedger:
+    """Derive a ledger from the records of a log.
+
+    Whose turn it is comes from the log's last author, never from an index parity, so a log
+    in which the same agent speaks twice in a row is legal: the adjacency is counted in
+    ``interleave_faults`` and the next turn still goes to the complement of the last author.
+
+    Args:
+        records (Sequence[AgentResponse]): The log, in log order.
+        seeder_name (str): The name of the agent that seeded the conversation.
+        partner_name (str): The name of the agent that answers the seeder.
+        max_responses (int): The budget of model-generated responses.
+        is_completed (Callable[[str, Any], bool]): Whether an author's message ends the conversation.
+        status (str): One of LEDGER_STATUSES, describing where the ledger came from.
+
+    Returns:
+        TurnLedger: The state of the conversation.
+    """
+    entries = tuple(
+        TurnEntry(
+            turn=index,
+            author=record.name,
+            content=_entry_content(record),
+            source=SEED_FINISH_REASON if index == 0 else "response",
+        )
+        for index, record in enumerate(records)
+    )
+
+    turns = len(entries)
+    responses = max(0, turns - 1)
+    last_author = entries[-1].author if entries else None
+    interleave_faults = sum(1 for i in range(1, turns) if entries[i].author == entries[i - 1].author)
+
+    if entries and is_completed(entries[-1].author, entries[-1].content):
+        completion_reason = "agent_signal"
+    elif responses >= max_responses:
+        completion_reason = "budget"
+    else:
+        completion_reason = "open"
+    completed = completion_reason != "open"
+
+    if not entries or completed:
+        next_speaker = None
+    else:
+        next_speaker = partner_name if last_author == seeder_name else seeder_name
+
+    return TurnLedger(
+        entries=entries,
+        seeder_name=seeder_name,
+        partner_name=partner_name,
+        max_responses=max_responses,
+        responses=responses,
+        turns=turns,
+        next_speaker=next_speaker,
+        last_author=last_author,
+        interleave_faults=interleave_faults,
+        completed=completed,
+        completion_reason=completion_reason,
+        status=status,
+    )
+
+
+def read_sidecar(working_dir: str) -> t.Optional[dict[str, t.Any]]:
+    """Read turn_ledger.json.
+
+    Args:
+        working_dir (str): The directory holding the sidecar.
+
+    Returns:
+        Optional[dict[str, t.Any]]: The recorded state, or None when it is missing or unreadable.
+    """
+    sidecar_file = os.path.join(working_dir, TURN_LEDGER_FILENAME)
+    try:
+        with open(sidecar_file, "r") as f:
+            state = json.load(f)
+    except (OSError, ValueError):
+        return None
+    if not isinstance(state, dict):
+        return None
+    return state
+
+
+def write_sidecar(working_dir: str, ledger: TurnLedger) -> str:
+    """Write turn_ledger.json beside the log.
+
+    Args:
+        working_dir (str): The directory holding the log.
+        ledger (TurnLedger): The state to record.
+
+    Returns:
+        str: The absolute path of the sidecar.
+    """
+    sidecar_file = os.path.join(working_dir, TURN_LEDGER_FILENAME)
+    with open(sidecar_file, "w") as f:
+        f.write(json.dumps(ledger.sidecar_state(), indent=2, sort_keys=True) + "\n")
+    return os.path.abspath(sidecar_file)
+
+
+def verify_sidecar(working_dir: str, ledger: TurnLedger) -> TurnLedger:
+    """Check a ledger derived from the log against the sidecar beside it.
+
+    A missing, unreadable or older-version sidecar is adopted without complaint and rewritten
+    on the next append. A current-version sidecar that disagrees with the log is an error; the
+    log is never rewritten from the sidecar.
+
+    Args:
+        working_dir (str): The directory holding the log and the sidecar.
+        ledger (TurnLedger): The ledger derived from the log.
+
+    Returns:
+        TurnLedger: The ledger, with its status set to "verified" or "adopted".
+
+    Raises:
+        TurnLedgerDesyncError: If a current-version sidecar disagrees with the log.
+    """
+    state = read_sidecar(working_dir)
+    if state is None or state.get("version") != TURN_LEDGER_VERSION:
+        return replace(ledger, status="adopted")
+
+    recorded_responses = state.get("responses")
+    recorded_last_author = state.get("last_author")
+    if recorded_responses == ledger.responses and recorded_last_author == ledger.last_author:
+        return replace(ledger, status="verified")
+
+    raise TurnLedgerDesyncError(
+        os.path.join(working_dir, TURN_LEDGER_FILENAME),
+        ledger.responses,
+        recorded_responses,
+        ledger.last_author,
+        recorded_last_author,
+    )
+
+
+def load_ledger(
+    working_dir: str,
+    *,
+    seeder_name: str,
+    partner_name: str,
+    max_responses: int,
+    is_completed: t.Callable[[str, t.Any], bool],
+) -> TurnLedger:
+    """Read a working directory and return the state of its conversation.
+
+    Args:
+        working_dir (str): The directory holding the log and the sidecar.
+        seeder_name (str): The name of the agent that seeded the conversation.
+        partner_name (str): The name of the agent that answers the seeder.
+        max_responses (int): The budget of model-generated responses.
+        is_completed (Callable[[str, Any], bool]): Whether an author's message ends the conversation.
+
+    Returns:
+        TurnLedger: The state of the conversation. Nothing is written.
+
+    Raises:
+        TurnLedgerCorruptError: If a line of the log is not a valid agent response.
+        TurnLedgerDesyncError: If a current-version sidecar disagrees with the log.
+    """
+    records = read_log(working_dir)
+    ledger = build_ledger(
+        records,
+        seeder_name=seeder_name,
+        partner_name=partner_name,
+        max_responses=max_responses,
+        is_completed=is_completed,
+    )
+    return verify_sidecar(working_dir, ledger)
diff --git a/src/bespokelabs/curator/status_tracker/agent_status_tracker.py b/src/bespokelabs/curator/status_tracker/agent_status_tracker.py
index fd09df7..2d267de 100644
--- a/src/bespokelabs/curator/status_tracker/agent_status_tracker.py
+++ b/src/bespokelabs/curator/status_tracker/agent_status_tracker.py
@@ -43,10 +43,12 @@ class AgentStatusTracker:
         max_turns (int): Maximum number of turns in the conversation.
         current_turn (int): Current turn number in the conversation.
         current_agent (AgentTurn): Which agent's turn it currently is.
-        num_responses (int): Total number of responses generated.
+        num_responses (int): Number of responses generated by this process.
         num_errors (int): Number of errors encountered.
+        num_cached (int): Number of responses inherited from a previous process.
         start_time (float): Time when the conversation started.
         last_update_time (float): Time of the last status update.
+        time_fn (Callable[[], float]): The clock the tracker reads.
         pbar (Optional[tqdm.tqdm]): Progress bar for tracking progress.
         total_tokens (_TokenUsage): Total tokens used in the conversation.
         total_cost (float): Total cost of the conversation.
@@ -59,8 +61,10 @@ class AgentStatusTracker:
     current_agent: AgentTurn = AgentTurn.SEEDER
     num_responses: int = 0
     num_errors: int = 0
-    start_time: float = field(default_factory=time.time)
-    last_update_time: float = field(default_factory=time.time)
+    num_cached: int = 0
+    start_time: float = 0.0
+    last_update_time: float = 0.0
+    time_fn: t.Callable[[], float] = field(default=time.time, repr=False, compare=False)
     pbar: t.Optional[tqdm.tqdm] = field(default=None, repr=False, compare=False)
 
     # Token and cost tracking
@@ -85,6 +89,8 @@ class AgentStatusTracker:
 
     def __post_init__(self):
         """Initialize the tracker."""
+        self.start_time = self.time_fn()
+        self.last_update_time = self.start_time
         self.input_cost_per_million = self.input_cost_per_million or {"seeder": None, "partner": None}
         self.output_cost_per_million = self.output_cost_per_million or {"seeder": None, "partner": None}
 
@@ -246,10 +252,11 @@ class AgentStatusTracker:
             token_usage (Optional[_TokenUsage]): Token usage for this turn.
             cost (Optional[float]): Cost for this turn.
         """
-        self.current_turn += 1
         self.current_agent = agent
-        self.num_responses += 1
-        if not response_success:
+        if response_success:
+            self.current_turn += 1
+            self.num_responses += 1
+        else:
             self.num_errors += 1
 
         if token_usage:
@@ -262,6 +269,25 @@ class AgentStatusTracker:
 
         self.update_display()
 
+    def adopt_ledger(self, *, cached_responses: int) -> None:
+        """Adopt the responses a previous process already generated.
+
+        The inherited work is counted once, as `num_cached`, and never as work done by this
+        process: `current_turn` describes the conversation while `num_responses`, `num_errors`
+        and the token and cost totals describe this process only.
+
+        Args:
+            cached_responses (int): The number of responses already in the conversation.
+        """
+        self.current_turn = cached_responses
+        self.num_cached = cached_responses
+        self.num_responses = 0
+        self.num_errors = 0
+        self.total_cost = 0.0
+        self.total_tokens.input = 0
+        self.total_tokens.output = 0
+        self.total_tokens.total = 0
+
     def update_display(self):
         """Update the display with current status."""
         current_time = time.time()
@@ -357,6 +383,7 @@ class AgentStatusTracker:
         self.pbar = None
         metadata = asdict(self)
         metadata.pop("pbar", None)
+        metadata.pop("time_fn", None)
         # Restore pbar if needed
         self.pbar = temp_pbar
 
CURATOR_ORACLE_PATCH_EOF
git apply --whitespace=nowarn /tmp/oracle.patch
rm -f /tmp/oracle.patch
echo "applied the reference solution"
