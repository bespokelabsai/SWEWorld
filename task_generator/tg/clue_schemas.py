"""Schemas for the clue stages, and phase 3's BRIEF lifted at read time.

The tree and herring shapes are phase 3's, rebuilt here because they are
parameterised by this task's people, facts and sources. The placement shape is new:
phase 3 chose a slot by token overlap against a conversation's *agenda*, and this
one asks a model to judge whether a remark could realistically have been made in a
conversation that actually happened.

`BRIEF` is read out of `data_gen/phase3_plant.py` rather than copied. It is the
load-bearing prompt of that whole stage -- one sentence per remark, at least two
leaves per subconclusion, somebody has to mind, somebody has to say what should
happen instead -- and a second copy of it would drift from the original silently.
"""
from __future__ import annotations

from .model import FACT_FIELDS, REPO

_STR = {"type": "string"}
_STRS = {"type": "array", "items": {"type": "string"}}

SOURCES = ("slack", "notion", "email")


def brief() -> str:
    """phase 3's BRIEF, verbatim, from its own source."""
    source = (REPO / "data_gen" / "phase3_plant.py").read_text()
    start = source.index('BRIEF = """') + len('BRIEF = """')
    return source[start:source.index('"""', start)].strip()


def tree_schema(people: list[str], facts: list[str], sources: list[str]) -> dict:
    """Subconclusions, and the leaves that imply them.

    No `minItems` anywhere, deliberately: phase 3 records that the structured-output
    API accepts only 0 or 1 and rejects the whole request otherwise. The floors --
    two leaves per subconclusion above all -- are enforced after the call.
    """
    return {
        "type": "object",
        "required": ["subconclusions", "leaves"],
        "properties": {
            "subconclusions": {"type": "array", "items": {
                "type": "object",
                "required": ["id", "text", "commonsense"],
                "properties": {
                    "id": _STR,
                    "text": {**_STR, "description":
                             "one component of the requirement, stated as a claim. Reaching "
                             "ALL of them, and nothing else, must give a reader the whole "
                             "requirement"},
                    "commonsense": {**_STR, "description":
                                    "the single inference a reader supplies to reach this "
                                    "from its leaves. Nobody ever says it."},
                }}},
            "leaves": {"type": "array", "items": {
                "type": "object",
                "required": ["id", "text", "leaves_open", "settles", "holder",
                             "source", "subconclusion", "covers"],
                "properties": {
                    "id": _STR,
                    "text": {**_STR, "description":
                             "the oblique remark, in this person's voice. ONE sentence, two "
                             "at the absolute most, under 30 words. ONE observation: what "
                             "they saw, or what it cost them, or what they want. Never the "
                             "conclusion its subconclusion states"},
                    "leaves_open": {**_STR, "description":
                                    "what a reader still CANNOT conclude from this remark "
                                    "alone, and must get from a sibling remark. If this is "
                                    "empty or trivial the remark is too complete -- narrow it"},
                    "settles": {**_STR, "description":
                                "the same point as one short third-person clause: "
                                "'the team agrees X'"},
                    "holder": {"type": "string", "enum": people or ["none"]},
                    "source": {"type": "string", "enum": sources or ["slack"]},
                    "subconclusion": _STR,
                    "covers": {"type": "array",
                               "items": {"type": "string", "enum": facts or ["rule"]},
                               "description": "at most two; more and it reads as a "
                                              "specification rather than a remark"},
                    "commonsense": {**_STR, "description":
                                    "what a reader must infer from this remark alone"},
                    "verbatim": {**_STRS, "description":
                                 "identifiers a reader must reproduce exactly, and which "
                                 "this text therefore contains literally"},
                    "forbidden_terms": {**_STRS, "description":
                                        "language that would give the requirement away"},
                }}},
        },
    }


def herring_schema(people: list[str]) -> dict:
    return {
        "type": "object",
        "required": ["herrings"],
        "properties": {"herrings": {"type": "array", "items": {
            "type": "object",
            "required": ["id", "text", "settles", "holder"],
            "properties": {
                "id": _STR,
                "text": {**_STR, "description":
                         "the remark, in this person's voice, as they would drop it at the "
                         "time. One sentence, two at most, under 30 words"},
                "settles": {**_STR, "description":
                            "the earlier decision as one short third-person clause"},
                "holder": {"type": "string", "enum": people or ["none"]},
                "forbidden_terms": {**_STRS, "description":
                                    "language that would reveal this was later reversed"},
            }}}},
    }


def reversal_schema(people: list[str], herrings: list[str], facts: list[str]) -> dict:
    """One remark per herring, saying the earlier decision is gone.

    `reverses` is an enum over the herring ids rather than free text: a reversal
    naming no herring cannot be checked against the one it is supposed to
    overturn, and `unreversed()` would report the herring as unanswered while the
    remark sat in the corpus doing the job.
    """
    return {
        "type": "object",
        "required": ["reversals"],
        "properties": {"reversals": {"type": "array", "items": {
            "type": "object",
            "required": ["reverses", "text", "settles", "holder"],
            "properties": {
                "reverses": {"type": "string", "enum": herrings or ["none"],
                             "description": "the earlier remark this one overturns"},
                "text": {**_STR, "description":
                         "the remark, in this person's voice: what was dropped, that "
                         "it is dropped, and what replaced it. Under 40 words"},
                "settles": {**_STR, "description":
                            "one short third-person clause: what now holds instead"},
                "holder": {"type": "string", "enum": people or ["none"]},
                "covers": {"type": "array", "items": {"type": "string", "enum": facts},
                           "description": "fact fields this remark carries, if any"},
                "verbatim": {**_STRS, "description":
                             "identifiers that must appear in the remark literally"},
            }}}},
    }


# What an invented carrier may be, per source. The enum is narrowed to ONE kind
# rather than offered as a choice: asked to pick, the model answers `chat_thread`
# for a wiki remark most of the time, and ten of the first re-placement's remarks
# came out as Slack threads with `notion` or `email` still written in the ledger.
INVENT_KIND = {"slack": "chat_thread", "notion": "doc_new", "email": "mail_new"}


def place_schema(keys: list[str], channels: list[str] | None = None,
                 source: str = "slack") -> dict:
    """Where the remark goes, and how it reads once it is there.

    `choice: "none"` is a first-class answer, not a failure -- it is how a new
    conversation or document comes to exist. A remark wedged into a room it does not
    belong in is more visible to a reader than one more conversation that makes
    sense.
    """
    return {
        "type": "object",
        "required": ["choice", "why", "realism", "adapted"],
        "properties": {
            "choice": {"type": "string", "enum": [*keys, "none"],
                       "description": "the candidate this remark belongs in, or 'none'"},
            "why": {**_STR, "description":
                    "what that room was already chewing on that this answers or "
                    "complicates. For 'none', why no listed place works."},
            "realism": {"type": "integer", "minimum": 1, "maximum": 5,
                        "description": "5 = a reader would never question it; "
                                       "1 = it arrives from nowhere"},
            "adapted": {**_STR, "description":
                        "the remark as it would actually have appeared there. Same "
                        "information, same identifiers, still one or two sentences."},
            "insert_after": {**_STR, "description":
                             "for a conversation: the author and minute of the message this "
                             "follows, e.g. '09:26 gideon'. Empty to end the day."},
            "anchor": {**_STR, "description":
                       "for a page: the heading or the first few words of the paragraph "
                       "this should follow"},
            "invent": {"type": "object",
                       "description": "only when choice is 'none': the conversation or "
                                      "document that should have existed",
                       "properties": {
                           "kind": {"type": "string",
                                    "enum": [INVENT_KIND.get(source, "chat_thread")]},
                           # An enum, not free text. A model asked for "the channel
                           # this should have happened in" invents plausible ones
                           # (`batch-mode`), and a channel that is not in
                           # channels.yaml fails the Mattermost import long after
                           # the clue was paid for.
                           "channel": ({"type": "string", "enum": channels}
                                       if channels else _STR),
                           "date": {**_STR, "description": "YYYY-MM-DD, a weekday in range"},
                           "participants": _STRS,
                           "title": {**_STR, "description": "subject or page title"},
                           "prompted_by": {**_STR, "description":
                                           "what makes this conversation happen that day"},
                       }},
        },
    }


CONVERSATION = {
    "type": "object",
    "required": ["messages"],
    "properties": {"messages": {"type": "array", "items": {
        "type": "object",
        "required": ["author", "minute", "text"],
        "properties": {
            "author": _STR,
            "minute": {**_STR, "description": "HH:MM, in order, inside working hours"},
            "text": _STR,
            "is_the_remark": {"type": "boolean",
                              "description": "true on the one message that carries the clue"},
        }}}},
}


def repair_schema(people: list[str], facts: list[str], sources: list[str]) -> dict:
    """Rewrites of remarks that failed a measured proof, plus at most one addition.

    Rewrites carry an id because they keep their slot: the conversation they sit in
    already exists and the remark already reads as part of it, so re-placing it would
    throw away the one thing about it that was working.
    """
    leaf = tree_schema(people, facts, sources)["properties"]["leaves"]["items"]
    return {
        "type": "object",
        "required": ["rewrites"],
        "properties": {
            "rewrites": {"type": "array", "items": {
                "type": "object",
                "required": ["clue_id", "text", "why"],
                "properties": {
                    "clue_id": _STR,
                    "text": {**_STR, "description":
                             "the remark as it should have read: same voice, same "
                             "conversation, one or two sentences"},
                    "why": {**_STR, "description":
                            "what this rewrite adds that the old wording did not carry"},
                    "verbatim": {**_STRS, "description":
                                 "identifiers this text contains literally"},
                }}},
            "addition": {**leaf, "description":
                         "one more remark, only if no rewrite can carry the missing "
                         "piece without stating the requirement outright"},
        },
    }


def judge_schema(claim_ids: list[str]) -> dict:
    """Per graded assertion: was a reader told, or left to work it out?

    `claim` is an enum so a verdict cannot be returned for an assertion that does not
    exist, and `settle.judge` fills in `absent` for any id the model skipped -- a
    claim nobody ruled on is not a claim that passed.
    """
    return {
        "type": "object",
        "required": ["verdicts"],
        "properties": {"verdicts": {"type": "array", "items": {
            "type": "object",
            "required": ["claim", "verdict", "why"],
            "properties": {
                "claim": {"type": "string", "enum": claim_ids or ["none"]},
                "verdict": {"type": "string",
                            "enum": ["stated", "implied", "absent", "not_required"]},
                "clues": {**_STRS, "description":
                          "the remark ids the verdict rests on: which say it, or "
                          "which come closest"},
                "why": {**_STR, "description":
                        "one sentence. For 'implied', what the reader is left to "
                        "supply that nobody supplied for them."},
            }}}},
    }


def settle_schema(people: list[str], facts: list[str], sources: list[str]) -> dict:
    """Rewrites that make a claim stated, plus however many new remarks it takes.

    `additions` is an array where `repair_schema`'s is a single object: repair fixes
    one fact that one measurement blamed, and this fixes every assertion in a fact
    that nobody said out loud, which is regularly more than one remark's worth.
    """
    leaf = tree_schema(people, facts, sources)["properties"]["leaves"]["items"]
    return {
        "type": "object",
        "required": ["rewrites"],
        "properties": {
            "rewrites": {"type": "array", "items": {
                "type": "object",
                "required": ["clue_id", "text", "why"],
                "properties": {
                    "clue_id": _STR,
                    "text": {**_STR, "description":
                             "the remark as it should have read: same voice, same "
                             "conversation, one or two sentences, now SAYING the "
                             "thing rather than gesturing at it"},
                    "why": {**_STR, "description":
                            "which missing claim this now states"},
                    "verbatim": {**_STRS, "description":
                                 "identifiers this text contains literally"},
                }}},
            "additions": {"type": "array", "items": leaf,
                          "description": "new remarks, where no rewrite can carry a "
                                         "missing claim without becoming a spec"},
        },
    }


DOCUMENT = {
    "type": "object",
    "required": ["title", "collection", "sections"],
    "properties": {
        "title": {**_STR, "description": "what this page is called; about its own "
                                         "subject, never about the remark"},
        "collection": {**_STR, "description": "the wiki collection it belongs in, "
                                              "e.g. engineering"},
        "sections": {"type": "array", "items": {
            "type": "object",
            "required": ["heading", "body"],
            "properties": {
                "heading": _STR,
                "body": {**_STR, "description": "markdown; prose or bullets, the "
                                                "register the other pages use"},
                "carries_the_remark": {"type": "boolean"},
            }}},
    },
}

MAIL = {
    "type": "object",
    "required": ["subject", "messages"],
    "properties": {
        "subject": _STR,
        "messages": {"type": "array", "items": {
            "type": "object",
            "required": ["sender", "to", "body"],
            "properties": {
                "sender": _STR,
                "to": _STRS,
                "minute": {**_STR, "description": "HH:MM, in order"},
                "body": {**_STR, "description": "a few sentences, this person's voice"},
                "is_the_remark": {"type": "boolean",
                                  "description": "true on the one message carrying the clue"},
            }}},
    },
}


# A conversation that FRAGMENTS its remark rather than containing it. `pieces` is
# the model's own account of where each part landed -- kept because it is useful to
# read, never trusted as the check: `thread_schema`'s output is verified by a second
# call that is shown the remark and the thread and not this list.
THREAD = {
    "type": "object",
    "required": ["messages", "pieces"],
    "properties": {
        "messages": {"type": "array", "items": {
            "type": "object",
            "required": ["author", "minute", "text"],
            "properties": {
                "author": _STR,
                "minute": {**_STR, "description": "HH:MM, in order, working hours"},
                "text": _STR,
            }}},
        "pieces": {"type": "array", "items": {
            "type": "object",
            "required": ["piece", "carried_by"],
            "properties": {
                "piece": {**_STR, "description": "one distinct part of the material"},
                "carried_by": {**_STR, "description": "author and minute of the turn"},
            }}},
    },
}


def carriage_schema(parts: int = 8) -> dict:
    """Is every part of the remark somewhere in the thread? One row per part.

    Separate call from the one that wrote the thread, and shown the remark rather
    than the writer's own `pieces`, because a model asked to mark its own homework
    marks the homework it remembers setting. `carried` is not asked for -- it is
    computed from these rows in code, for the same reason phase 4 stopped trusting
    a judge's summary boolean over its own element list.
    """
    return {
        "type": "object",
        "required": ["parts"],
        "properties": {"parts": {"type": "array", "maxItems": parts, "items": {
            "type": "object",
            "required": ["part", "present", "where"],
            "properties": {
                "part": {**_STR, "description": "one distinct claim the remark makes"},
                "present": {"type": "boolean",
                            "description": "a reader of the thread alone recovers it"},
                "where": {**_STR, "description": "the turn carrying it, or why not"},
            }}}},
    }


def consistency_schema(rows: int = 12) -> dict:
    """Does anything in the corpus state this fact WRONGLY and get away with it?

    One row per statement that contradicts the requirement, never a summary
    verdict -- the same reason `carriage_schema` returns parts and lets code do
    the arithmetic. The gate's decision is made here in Python from `reversed_by`
    and the dates, not by the judge, because a judge asked "is this fair" answers
    about the corpus it just read rather than about the reader who meets it in
    date order.

    Numbers cannot settle this. The invention that cost g2 a fact was "first 16k,
    last 48k" against a requirement holding 16, 48, 64, 29, 3 and 4 -- two of its
    own numbers with their roles swapped. Only a reader of the sentence can tell.
    """
    return {
        "type": "object",
        "required": ["conflicts"],
        "properties": {"conflicts": {"type": "array", "maxItems": rows, "items": {
            "type": "object",
            "required": ["clue_id", "quote", "says", "reversed_by"],
            "properties": {
                "clue_id": {**_STR, "description": "the remark the statement sits in"},
                "quote": {**_STR, "description": "the words that state it wrongly"},
                "says": {**_STR, "description":
                         "what a reader takes from it, and how that differs from "
                         "the requirement"},
                "reversed_by": {**_STR, "description":
                                "clue_id of a LATER remark that plainly overturns "
                                "it -- names the old decision and says it is gone. "
                                "Empty string if nothing does. A remark that merely "
                                "states the truth without referring to this one is "
                                "NOT a reversal."},
            }}}},
    }
