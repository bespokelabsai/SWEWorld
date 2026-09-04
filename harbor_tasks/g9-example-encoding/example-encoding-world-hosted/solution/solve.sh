#!/bin/bash
# Reference solution, run by `harbor run -a oracle` and by Horizon's validation
# gate — which is why it has to be real. Horizon refuses to schedule any
# evaluation against a task whose oracle does not score ~1.0:
#
#     409 Conflict: One or more tasks are blocked by the evaluation validation gate.
#
# And a real one here means more than applying a patch. `run_suites.py` clones
# and grades **the pushed `main`**, not the working tree, so an oracle that edits
# files and stops scores exactly zero with every test reporting "does not
# import". Pushing IS the solution in this world.
#
# The patch is embedded rather than read from a file beside this script: on the
# apex arms the sibling file was unreadable from the solution's own directory
# (/tests is root-owned 0700), and a heredoc has no permissions of its own. It is
# generated from fixtures/oracle.patch at build time, so it cannot drift from the
# suite that grades it.
set -uo pipefail

REPO_URL="http://worldadmin:worldadmin@git.world.local/worldadmin/curator.git"
WORK="$(mktemp -d)"

# The healthcheck should already have waited for gitea, but the oracle also runs
# in contexts that do not go through it. Cheap when it is already up.
wait-for-service --quiet gitea 2>/dev/null || true

git clone --quiet "$REPO_URL" "$WORK/curator" || { echo "oracle: clone failed"; exit 1; }
cd "$WORK/curator" || exit 1

cat > /tmp/oracle.patch <<'CURATOR_ORACLE_PATCH_EOF'
diff --git a/src/bespokelabs/curator/finetune/__init__.py b/src/bespokelabs/curator/finetune/__init__.py
index 7e8ba01..76231c7 100644
--- a/src/bespokelabs/curator/finetune/__init__.py
+++ b/src/bespokelabs/curator/finetune/__init__.py
@@ -50,6 +50,17 @@ Custom data formatting:
 
 from bespokelabs.curator.finetune.config import AdamParams, FireworksTrainerConfig, LoRAConfig, TinkerTrainerConfig
 from bespokelabs.curator.finetune.data_formatter import DataFormatter
+from bespokelabs.curator.finetune.encoding import (
+    ALLOWED_ROLES,
+    FIREWORKS_BYTES_PER_TOKEN,
+    MIN_RETAINED_PROMPT_TOKENS,
+    EncodingError,
+    EncodingReport,
+    ExampleTooLongError,
+    InvalidRoleSequenceError,
+    TokenizerCapabilityError,
+    validate_role_sequence,
+)
 from bespokelabs.curator.finetune.fireworks_data_formatter import FireworksDataFormatter
 from bespokelabs.curator.finetune.status_tracker import FinetuneStatusTracker
 from bespokelabs.curator.finetune.trainer import BaseTrainer, FireworksTrainer, TinkerTrainer
@@ -83,4 +94,14 @@ __all__ = [
     "DataFormatter",
     "FireworksDataFormatter",
     "FinetuneStatusTracker",
+    # Encoding policy
+    "EncodingError",
+    "ExampleTooLongError",
+    "InvalidRoleSequenceError",
+    "TokenizerCapabilityError",
+    "EncodingReport",
+    "MIN_RETAINED_PROMPT_TOKENS",
+    "FIREWORKS_BYTES_PER_TOKEN",
+    "ALLOWED_ROLES",
+    "validate_role_sequence",
 ]
diff --git a/src/bespokelabs/curator/finetune/data_formatter.py b/src/bespokelabs/curator/finetune/data_formatter.py
index 53809a8..deb317f 100644
--- a/src/bespokelabs/curator/finetune/data_formatter.py
+++ b/src/bespokelabs/curator/finetune/data_formatter.py
@@ -1,7 +1,14 @@
 """Data formatter for converting datasets to Tinker Datum format."""
 
-from typing import Any, Dict, List, Optional
-
+from typing import Any, Dict, List, Optional, Tuple
+
+from bespokelabs.curator.finetune.encoding import (
+    MIN_RETAINED_PROMPT_TOKENS,
+    EncodingReport,
+    ExampleTooLongError,
+    TokenizerCapabilityError,
+    validate_role_sequence,
+)
 from bespokelabs.curator.finetune.types import ChatMessage, TrainingExample
 
 try:
@@ -24,6 +31,8 @@ class DataFormatter:
         """
         self.max_seq_length = max_seq_length
         self.train_on_assistant_only = train_on_assistant_only
+        self.last_report: EncodingReport = EncodingReport()
+        self._last_encoding: Dict[str, Any] = {}
 
     def format_chat_messages(self, messages: List[Dict[str, str]]) -> List[ChatMessage]:
         """Convert raw message dicts to ChatMessage objects.
@@ -57,84 +66,151 @@ class DataFormatter:
                     return TrainingExample(messages=messages)
         raise ValueError(f"Cannot format row: expected 'messages' key with list of chat messages, got {row.keys()}")
 
-    def _compute_weights(self, messages: List[ChatMessage], tokens: List[int], tokenizer: Any) -> List[float]:
-        """Compute loss weights for tokens based on which ones are assistant responses.
+    def _mock_chat_text(self, messages: List[ChatMessage]) -> str:
+        """Build the tokenizer-free chat text for a list of messages.
 
         Args:
             messages: List of chat messages
-            tokens: Tokenized input
-            tokenizer: Tokenizer to use for finding boundaries
 
         Returns:
-            List of weights (1.0 for assistant tokens, 0.0 for others)
+            The ``<|role|>`` rendering of the conversation
         """
-        if not self.train_on_assistant_only:
-            return [1.0] * len(tokens)
+        chat_text = ""
+        for msg in messages:
+            chat_text += f"<|{msg.role}|>\n{msg.content}\n"
+        return chat_text
 
-        message_dicts = [{"role": msg.role, "content": msg.content} for msg in messages]
-        weights = [0.0] * len(tokens)
+    def _supervised_spans(self, messages: List[ChatMessage], tokenizer: Optional[Any]) -> List[Tuple[int, int]]:
+        """Locate every assistant turn in the untruncated token sequence.
+
+        Boundaries come from prefix tokenization: the chat template rendered with
+        ``add_generation_prompt=True`` up to (but excluding) the assistant message
+        gives the start, the template rendered through it gives the end. Without a
+        tokenizer the same boundaries are derived from character offsets, matching
+        the mock ``len(text) // 4`` token count; there the ``<|assistant|>`` header
+        falls inside the span.
+
+        Failures of the tokenizer are not caught: a formatter that cannot locate
+        the assistant turns must not silently train on the prompt.
+
+        Args:
+            messages: List of chat messages
+            tokenizer: Tokenizer used to find boundaries, or None for the mock path
+
+        Returns:
+            Half-open ``[start, end)`` token index of every assistant turn, in
+            message order.
+        """
+        spans: List[Tuple[int, int]] = []
 
-        try:
-            cumulative_messages = []
+        if tokenizer is None:
+            for i, msg in enumerate(messages):
+                if msg.role == "assistant":
+                    len_before = len(self._mock_chat_text(messages[:i]))
+                    len_after = len(self._mock_chat_text(messages[: i + 1]))
+                    spans.append((len_before // 4, len_after // 4))
+            return spans
 
-            for msg in message_dicts:
-                cumulative_messages.append(msg)
+        message_dicts = [{"role": msg.role, "content": msg.content} for msg in messages]
+        cumulative_messages: List[Dict[str, str]] = []
 
-                if msg["role"] == "assistant":
-                    # Tokenize up to before this assistant message
-                    pre_assistant = cumulative_messages[:-1]
-                    if pre_assistant:
-                        pre_text = tokenizer.apply_chat_template(pre_assistant, tokenize=False, add_generation_prompt=True)
-                        pre_tokens = tokenizer.encode(pre_text, add_special_tokens=False)
-                        start_idx = len(pre_tokens)
-                    else:
-                        start_idx = 0
+        for msg in message_dicts:
+            cumulative_messages.append(msg)
 
-                    # Tokenize including this assistant message
-                    curr_text = tokenizer.apply_chat_template(cumulative_messages, tokenize=False, add_generation_prompt=False)
-                    curr_tokens = tokenizer.encode(curr_text, add_special_tokens=False)
-                    end_idx = len(curr_tokens)
+            if msg["role"] == "assistant":
+                # Tokenize up to before this assistant message
+                pre_assistant = cumulative_messages[:-1]
+                if pre_assistant:
+                    pre_text = tokenizer.apply_chat_template(pre_assistant, tokenize=False, add_generation_prompt=True)
+                    pre_tokens = tokenizer.encode(pre_text, add_special_tokens=False)
+                    start_idx = len(pre_tokens)
+                else:
+                    start_idx = 0
 
-                    # Set weights for assistant tokens
-                    for i in range(start_idx, min(end_idx, len(weights))):
-                        weights[i] = 1.0
+                # Tokenize including this assistant message
+                curr_text = tokenizer.apply_chat_template(cumulative_messages, tokenize=False, add_generation_prompt=False)
+                curr_tokens = tokenizer.encode(curr_text, add_special_tokens=False)
+                end_idx = len(curr_tokens)
 
-        except Exception:
-            # If boundary detection fails, fall back to training on all tokens
-            weights = [1.0] * len(tokens)
+                spans.append((start_idx, end_idx))
 
-        return weights
+        return spans
 
     def to_tinker_datum(self, example: TrainingExample, tokenizer: Optional[Any] = None) -> Any:
         """Convert a TrainingExample to Tinker Datum format.
 
+        The example is encoded in full and then windowed from the left, so the
+        completion at the end of the conversation always survives and the oldest
+        context is what is lost. An assistant turn that begins before the window
+        is not supervised at all, and an example whose surviving prompt is shorter
+        than ``MIN_RETAINED_PROMPT_TOKENS`` is refused.
+
         Args:
             example: The training example to convert
             tokenizer: Tokenizer for creating model_input (required for real training)
 
         Returns:
             Tinker Datum object or dictionary in Tinker Datum format
+
+        Raises:
+            InvalidRoleSequenceError: If the roles are not a legal conversation.
+            TokenizerCapabilityError: If the tokenizer has no chat template.
+            ExampleTooLongError: If windowing would leave too little prompt.
         """
-        message_dicts = [{"role": msg.role, "content": msg.content} for msg in example.messages]
+        validate_role_sequence(example.messages)
+
+        if tokenizer is not None and not callable(getattr(tokenizer, "apply_chat_template", None)):
+            raise TokenizerCapabilityError(missing_method="apply_chat_template")
 
         if tokenizer is not None:
             # Use the tokenizer's chat template
+            message_dicts = [{"role": msg.role, "content": msg.content} for msg in example.messages]
             chat_text = tokenizer.apply_chat_template(message_dicts, tokenize=False, add_generation_prompt=False)
-            tokens = tokenizer.encode(chat_text, max_length=self.max_seq_length, truncation=True)
-
-            weights = self._compute_weights(example.messages, tokens, tokenizer)
+            tokens = tokenizer.encode(chat_text, add_special_tokens=False)
         else:
-            chat_text = ""
-            for msg in example.messages:
-                chat_text += f"<|{msg.role}|>\n{msg.content}\n"
-            mock_token_count = min(len(chat_text) // 4, self.max_seq_length)
-            tokens = list(range(mock_token_count))
-            weights = [1.0] * len(tokens)
+            chat_text = self._mock_chat_text(example.messages)
+            tokens = list(range(len(chat_text) // 4))
+
+        spans = self._supervised_spans(example.messages, tokenizer)
+
+        token_count = len(tokens)
+        window_start = max(0, token_count - self.max_seq_length)
+
+        if window_start > 0 and spans:
+            start_of_final = spans[-1][0]
+            if start_of_final - window_start < MIN_RETAINED_PROMPT_TOKENS:
+                raise ExampleTooLongError(
+                    token_count=token_count,
+                    max_seq_length=self.max_seq_length,
+                    retained_prompt_tokens=max(0, start_of_final - window_start),
+                    num_messages=len(example.messages),
+                )
+
+        if self.train_on_assistant_only:
+            weights = [0.0] * token_count
+            for start_idx, end_idx in spans:
+                # A turn the window cuts in half is not supervised at all.
+                if start_idx >= window_start:
+                    weights[start_idx:end_idx] = [1.0] * len(weights[start_idx:end_idx])
+        else:
+            weights = [1.0] * token_count
+
+        windowed_tokens = tokens[window_start:]
+        windowed_weights = weights[window_start:]
+
+        encoding = {
+            "tokenizer": tokenizer is not None,
+            "token_count": token_count,
+            "window_start": window_start,
+            "windowed": window_start > 0,
+            "supervised_tokens": sum(1 for weight in windowed_weights if weight == 1.0),
+        }
+        self._last_encoding = encoding
 
         # Causal-LM shift: input=tokens[:-1], target=tokens[1:], weights aligned to targets
-        input_tokens = tokens[:-1]
-        target_tokens = tokens[1:]
-        shifted_weights = weights[1:]
+        input_tokens = windowed_tokens[:-1]
+        target_tokens = windowed_tokens[1:]
+        shifted_weights = windowed_weights[1:]
 
         if TINKER_AVAILABLE and tokenizer is not None:
             model_input = tinker.ModelInput(chunks=[tinker.EncodedTextChunk(tokens=input_tokens)])
@@ -154,19 +230,47 @@ class DataFormatter:
                 "weights": shifted_weights,
             },
             "metadata": {
-                "original_text": chat_text if tokenizer is None else "",
+                "original_text": chat_text,
                 "num_messages": len(example.messages),
+                "encoding": encoding,
             },
         }
 
     def format_batch(self, examples: List[TrainingExample], tokenizer: Optional[Any] = None) -> List[Any]:
         """Format a batch of examples into Tinker Datum format.
 
+        Examples that do not fit are dropped and recorded in ``last_report``; a
+        malformed role sequence or an unusable tokenizer aborts the batch, since
+        that is a bug rather than a fact of life.
+
         Args:
             examples: List of TrainingExample objects
             tokenizer: Tokenizer for creating model_input
 
         Returns:
-            List of Tinker Datum objects or dictionaries
+            List of Tinker Datum objects or dictionaries, without the dropped ones
         """
-        return [self.to_tinker_datum(example, tokenizer) for example in examples]
+        data: List[Any] = []
+        dropped_indices: List[int] = []
+        windowed = 0
+        supervised_tokens = 0
+
+        for index, example in enumerate(examples):
+            try:
+                datum = self.to_tinker_datum(example, tokenizer)
+            except ExampleTooLongError:
+                dropped_indices.append(index)
+                continue
+
+            data.append(datum)
+            windowed += 1 if self._last_encoding.get("windowed") else 0
+            supervised_tokens += self._last_encoding.get("supervised_tokens", 0)
+
+        self.last_report = EncodingReport(
+            kept=len(data),
+            dropped=len(dropped_indices),
+            windowed=windowed,
+            dropped_indices=tuple(dropped_indices),
+            supervised_tokens=supervised_tokens,
+        )
+        return data
diff --git a/src/bespokelabs/curator/finetune/encoding.py b/src/bespokelabs/curator/finetune/encoding.py
new file mode 100644
index 0000000..ef8dafa
--- /dev/null
+++ b/src/bespokelabs/curator/finetune/encoding.py
@@ -0,0 +1,148 @@
+"""Encoding policy shared by every chat data formatter.
+
+A chat example is encoded once, as a whole, and then trimmed to fit. The policy
+is deliberately uniform across backends:
+
+* the *left* of an over-long example is dropped, never the completion at its end;
+* an assistant turn that the window cuts in half is not supervised at all;
+* an example whose surviving prompt is shorter than
+  :data:`MIN_RETAINED_PROMPT_TOKENS` is refused rather than trained on;
+* a malformed role sequence is a bug in the data and always raises.
+
+The formatters raise the exceptions defined here; batch-level entry points turn
+:class:`ExampleTooLongError` into a drop and record it in an
+:class:`EncodingReport`.
+"""
+
+from dataclasses import dataclass
+from typing import Any, List, Sequence, Tuple
+
+#: Minimum number of prompt tokens that must survive the left window for a
+#: windowed example to be worth training on.
+MIN_RETAINED_PROMPT_TOKENS: int = 16
+
+#: Bytes of serialized JSONL that the Fireworks path budgets per context token.
+FIREWORKS_BYTES_PER_TOKEN: int = 3
+
+#: The roles a chat example may use.
+ALLOWED_ROLES: frozenset = frozenset({"system", "user", "assistant"})
+
+
+class EncodingError(ValueError):
+    """Base class for every error raised by the encoding policy."""
+
+
+class ExampleTooLongError(EncodingError):
+    """Raised when windowing an example would leave too little prompt behind."""
+
+    def __init__(
+        self,
+        *,
+        token_count: int,
+        max_seq_length: int,
+        retained_prompt_tokens: int,
+        num_messages: int,
+    ) -> None:
+        """Initialize the error.
+
+        Args:
+            token_count: Length of the untruncated token sequence.
+            max_seq_length: The formatter's sequence length cap.
+            retained_prompt_tokens: Prompt tokens surviving ahead of the final
+                assistant turn.
+            num_messages: Number of messages in the refused example.
+        """
+        self.token_count = token_count
+        self.max_seq_length = max_seq_length
+        self.retained_prompt_tokens = retained_prompt_tokens
+        self.num_messages = num_messages
+        super().__init__(
+            f"example of {token_count} tokens exceeds max_seq_length={max_seq_length}: "
+            f"{retained_prompt_tokens} prompt tokens would survive, "
+            f"minimum is {MIN_RETAINED_PROMPT_TOKENS}"
+        )
+
+
+class InvalidRoleSequenceError(EncodingError):
+    """Raised when the roles of an example are not a legal conversation."""
+
+    def __init__(self, *, role_sequence: List[str], position: int, reason: str) -> None:
+        """Initialize the error.
+
+        Args:
+            role_sequence: The roles as given, in order.
+            position: Index of the offending message.
+            reason: One of ``"empty"``, ``"unknown_role"``, ``"misplaced_system"``,
+                ``"non_alternating"`` or ``"unterminated"``.
+        """
+        self.role_sequence = role_sequence
+        self.position = position
+        self.reason = reason
+        super().__init__(f"invalid role sequence at position {position} ({reason}): {role_sequence}")
+
+
+class TokenizerCapabilityError(EncodingError):
+    """Raised when a tokenizer cannot support the encoding policy."""
+
+    def __init__(self, *, missing_method: str) -> None:
+        """Initialize the error.
+
+        Args:
+            missing_method: Name of the method the tokenizer does not provide.
+        """
+        self.missing_method = missing_method
+        super().__init__(f"tokenizer is missing required method {missing_method!r}")
+
+
+@dataclass(frozen=True)
+class EncodingReport:
+    """Summary of what a batch-level encoding call kept, dropped and windowed."""
+
+    kept: int = 0
+    dropped: int = 0
+    windowed: int = 0
+    dropped_indices: Tuple[int, ...] = ()
+    supervised_tokens: int = 0
+
+
+def _role_of(message: Any) -> Any:
+    """Return the role of a ChatMessage-like object or a message dict."""
+    if isinstance(message, dict):
+        return message.get("role")
+    return getattr(message, "role", None)
+
+
+def validate_role_sequence(messages: Sequence[Any]) -> None:
+    """Raise InvalidRoleSequenceError if the roles are not a legal conversation.
+
+    A legal conversation is an optional leading ``system`` message followed by
+    strictly alternating ``user``/``assistant`` turns, ending on ``assistant``.
+
+    Args:
+        messages: Objects with a ``role`` attribute (``ChatMessage``) or dicts
+            with a ``"role"`` key; both are accepted.
+
+    Raises:
+        InvalidRoleSequenceError: On the first violation found.
+    """
+    roles = [_role_of(message) for message in messages]
+
+    if not roles:
+        raise InvalidRoleSequenceError(role_sequence=roles, position=0, reason="empty")
+
+    for index, role in enumerate(roles):
+        if role not in ALLOWED_ROLES:
+            raise InvalidRoleSequenceError(role_sequence=roles, position=index, reason="unknown_role")
+
+    for index, role in enumerate(roles[1:], start=1):
+        if role == "system":
+            raise InvalidRoleSequenceError(role_sequence=roles, position=index, reason="misplaced_system")
+
+    start = 1 if roles[0] == "system" else 0
+    for offset, role in enumerate(roles[start:]):
+        expected = "user" if offset % 2 == 0 else "assistant"
+        if role != expected:
+            raise InvalidRoleSequenceError(role_sequence=roles, position=start + offset, reason="non_alternating")
+
+    if roles[-1] != "assistant":
+        raise InvalidRoleSequenceError(role_sequence=roles, position=len(roles) - 1, reason="unterminated")
diff --git a/src/bespokelabs/curator/finetune/fireworks_data_formatter.py b/src/bespokelabs/curator/finetune/fireworks_data_formatter.py
index 61bf52c..28e4d4b 100644
--- a/src/bespokelabs/curator/finetune/fireworks_data_formatter.py
+++ b/src/bespokelabs/curator/finetune/fireworks_data_formatter.py
@@ -5,18 +5,41 @@ JSONL file: one JSON object per line of the form
 ``{"messages": [{"role": ..., "content": ...}, ...]}``. This formatter reuses the
 shared :class:`DataFormatter` row -> :class:`TrainingExample` logic and adds the
 JSONL serialization that the Fireworks Dataset upload requires.
+
+Fireworks tokenizes server side, so the shared sequence length policy applies here
+as a byte budget: a serialized line is kept only if it fits in
+``max_seq_length * FIREWORKS_BYTES_PER_TOKEN`` UTF-8 bytes. Nothing is truncated.
 """
 
 import json
-from typing import Any, Dict, List
+from typing import TYPE_CHECKING, Any, Dict, List
 
 from bespokelabs.curator.finetune.data_formatter import DataFormatter
+from bespokelabs.curator.finetune.encoding import FIREWORKS_BYTES_PER_TOKEN, EncodingReport, validate_role_sequence
 from bespokelabs.curator.finetune.types import TrainingExample
 
+if TYPE_CHECKING:
+    from bespokelabs.curator.finetune.config import FireworksTrainerConfig
+
 
 class FireworksDataFormatter(DataFormatter):
     """Converts curator datasets to the Fireworks chat JSONL format."""
 
+    @classmethod
+    def from_config(cls, config: "FireworksTrainerConfig") -> "FireworksDataFormatter":
+        """Build a formatter whose budget matches the fine-tuning job's context.
+
+        Args:
+            config: The Fireworks trainer configuration.
+
+        Returns:
+            A formatter using ``config.max_context_length`` as its sequence length.
+        """
+        return cls(
+            max_seq_length=config.max_context_length if config.max_context_length is not None else 2048,
+            train_on_assistant_only=True,
+        )
+
     def example_to_dict(self, example: TrainingExample) -> Dict[str, Any]:
         """Convert a TrainingExample into a Fireworks chat-format dict.
 
@@ -31,13 +54,39 @@ class FireworksDataFormatter(DataFormatter):
     def to_jsonl_lines(self, examples: List[TrainingExample]) -> List[str]:
         """Serialize a list of examples to Fireworks chat JSONL lines.
 
+        Lines whose UTF-8 size exceeds ``max_seq_length * FIREWORKS_BYTES_PER_TOKEN``
+        are dropped rather than truncated, and recorded in ``last_report``.
+
         Args:
             examples: The training examples to serialize.
 
         Returns:
-            A list of JSON strings, one per training example.
+            A list of JSON strings, one per retained training example.
+
+        Raises:
+            InvalidRoleSequenceError: If any example's roles are not a legal
+                conversation.
         """
-        return [json.dumps(self.example_to_dict(example), ensure_ascii=False) for example in examples]
+        budget = self.max_seq_length * FIREWORKS_BYTES_PER_TOKEN
+        lines: List[str] = []
+        dropped_indices: List[int] = []
+
+        for index, example in enumerate(examples):
+            validate_role_sequence(example.messages)
+            line = json.dumps(self.example_to_dict(example), ensure_ascii=False)
+            if len(line.encode("utf-8")) > budget:
+                dropped_indices.append(index)
+                continue
+            lines.append(line)
+
+        self.last_report = EncodingReport(
+            kept=len(lines),
+            dropped=len(dropped_indices),
+            windowed=0,
+            dropped_indices=tuple(dropped_indices),
+            supervised_tokens=0,
+        )
+        return lines
 
     def write_jsonl(self, examples: List[TrainingExample], path: str) -> str:
         """Write examples to a JSONL file in Fireworks chat format.
diff --git a/src/bespokelabs/curator/finetune/trainer/fireworks_trainer.py b/src/bespokelabs/curator/finetune/trainer/fireworks_trainer.py
index 15b8ab8..22ad7d3 100644
--- a/src/bespokelabs/curator/finetune/trainer/fireworks_trainer.py
+++ b/src/bespokelabs/curator/finetune/trainer/fireworks_trainer.py
@@ -123,7 +123,7 @@ class FireworksTrainer(BaseTrainer):
             config: FireworksTrainerConfig with training parameters.
         """
         self.config = config
-        self.data_formatter = FireworksDataFormatter()
+        self.data_formatter = FireworksDataFormatter.from_config(config)
         self._output_model: Optional[str] = None
         self._job_name: Optional[str] = None
         self._job_url: Optional[str] = None
CURATOR_ORACLE_PATCH_EOF

git apply --whitespace=nowarn /tmp/oracle.patch || { echo "oracle: patch did not apply"; exit 1; }
rm -f /tmp/oracle.patch

git config user.email "worldadmin@world.local"
git config user.name  "worldadmin"
git add -A
git commit --quiet -m "One encoding policy for chat examples" || { echo "oracle: nothing to commit"; exit 1; }

# Straight to main when the branch is unprotected; a branch plus an immediately
# merged PR when it is not. The agents that scored provenance 1.0 took the second
# path, so it is known to work in this world — but the first is one round trip and
# the grader only cares that `main` moved.
if git push --quiet origin HEAD:main 2>/dev/null; then
  echo "oracle: pushed straight to main"
else
  BRANCH="oracle/example-encoding"
  git push --quiet --force origin "HEAD:$BRANCH" || { echo "oracle: push failed"; exit 1; }
  TOKEN="$(cat /etc/sweworld/gitea-token 2>/dev/null)"
  API="http://git.world.local/api/v1/repos/worldadmin/curator"
  NUM=$(curl -sS -X POST -H "Authorization: token $TOKEN" \
        -H 'Content-Type: application/json' "$API/pulls" \
        -d "{\"head\":\"$BRANCH\",\"base\":\"main\",\"title\":\"oracle: example-encoding\"}" \
        | python3 -c 'import json,sys; print(json.load(sys.stdin).get("number",""))' 2>/dev/null)
  [ -n "$NUM" ] || { echo "oracle: could not open a PR"; exit 1; }
  curl -sS -X POST -H "Authorization: token $TOKEN" -H 'Content-Type: application/json' \
    "$API/pulls/$NUM/merge" -d '{"Do":"merge"}' >/dev/null \
    || { echo "oracle: merge failed"; exit 1; }
  echo "oracle: merged PR #$NUM into main"
fi

# Not required by the score — `score.py` sets reward = hidden_mean and leaves
# provenance unweighted — but the deploy takes about half a minute here, and
# letting it land means the oracle run also demonstrates ci_green and deployed
# rather than leaving two checks reading zero for no reason.
sleep 45
echo "oracle: done"
exit 0
