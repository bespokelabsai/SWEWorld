"""JSON schemas for the steps whose answer must be data, not prose.

Passed to `claude --json-schema`, so the model is forced into the shape rather
than asked for it and parsed hopefully. Nothing task-specific lives here: the
fields are the five `FACT_FIELDS` and the rubric's two catalogues, both of which
are properties of the method, not of any one task.
"""
from __future__ import annotations

from .model import FACT_FIELDS

_STR = {"type": "string"}

CATALOG_A = ("codebase_already_does_it", "prohibition_satisfied_by_inaction",
             "model_already_knows_it", "ticket_gives_it_away",
             "entailed_by_the_open_feature", "obvious_implementation_does_it")

CATALOG_B = ("state_is_unreachable", "contradicts_a_sibling",
             "behaviour_has_no_consequence", "observable_belongs_to_another_fact",
             "no_independent_content", "unbounded_in_time",
             "environment_cannot_be_built", "fake_defines_the_trigger")


def _findings(patterns: tuple[str, ...]) -> dict:
    return {
        "type": "array",
        "description": "one entry per pattern, every pattern present",
        "items": {
            "type": "object",
            "required": ["pattern", "applies", "why"],
            "properties": {
                "pattern": {"type": "string", "enum": list(patterns)},
                "applies": {"type": "boolean"},
                "why": {**_STR, "description": "what makes you say so; quote the fact or the code"},
            },
        },
    }


SPLIT = {
    "type": "object",
    "required": ["title", "description", "hidden_requirements", "fact_sources"],
    "properties": {
        "title": {**_STR, "description": "short noun phrase naming the feature"},
        "description": {**_STR, "description":
                        "THE VISIBLE TICKET. States the API openly, exact names and "
                        "signatures. Hints at no hidden part's chosen alternative."},
        "hidden_requirements": {
            "type": "array", "minItems": 2, "maxItems": 2,
            "items": {
                "type": "object",
                "required": ["requirement"],
                "properties": {
                    "requirement": {
                        "type": "object",
                        "required": ["rule"],
                        "properties": {f: {**_STR, "description":
                                           "declare only if it discriminates; omit otherwise"}
                                       for f in FACT_FIELDS},
                    },
                    "earlier_reversed_version": {
                        "type": ["string", "null"],
                        "description": "a decision the team really made and later reversed, or null",
                    },
                    "fragmentation_sources": {"type": "array", "items": _STR},
                    "hidden_requirement_types": {"type": "array", "items": _STR},
                },
            },
        },
        "fact_sources": {
            "type": "array",
            "description": "one entry per declared field, across both requirements",
            "items": {
                "type": "object",
                "required": ["req", "field", "part", "blind_alternative"],
                "properties": {
                    "req": {"type": "integer", "description": "1 or 2"},
                    "field": {"type": "string", "enum": list(FACT_FIELDS)},
                    "part": {**_STR, "description": "the spec part it came from, e.g. P3"},
                    "blind_alternative": {**_STR, "description":
                                          "in one clause, what a blind agent picks instead"},
                },
            },
        },
    },
}

AUDIT = {
    "type": "object",
    "required": ["verdict", "divergent_action", "catalog_a", "catalog_b",
                 "the_assertion", "recommendation"],
    "properties": {
        "verdict": {"type": "string", "enum": ["ship", "cut", "narrow", "retest"]},
        "divergent_action": {**_STR, "description":
                             "the concrete code an informed agent writes and a blind one "
                             "does not; empty string if you cannot name one"},
        "catalog_a": _findings(CATALOG_A),
        "catalog_b": _findings(CATALOG_B),
        "the_assertion": {**_STR, "description":
                          "the single assertion that decides this fact, quoted, and whether "
                          "it depends on anything but this requirement"},
        "blind_pass": {"type": ["string", "null"], "description":
                       "a reasonable ticket-only implementation that PASSES this fact, "
                       "quoted; null if you could not write one"},
        "correct_fail": {"type": ["string", "null"], "description":
                         "a legitimate reading of the requirement the test REJECTS, "
                         "quoted; null if you could not write one"},
        "recommendation": {**_STR, "description":
                           "what to do; for narrow/retest say exactly what to change"},
    },
}
