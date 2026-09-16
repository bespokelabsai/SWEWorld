---
title: "Release notes: v0.1.16"
author: dermot
created_at: 2025-01-21T08:48:00+00:00
---

# Release Notes: v0.1.16

Eleventh Millrow release, shipped as part of the Stratos Crunch milestone.

## What shipped

### Version bump to v0.1.16

Release cut and tagged. No migration steps required.

### Anthropic online capacity guard

Requests against the Anthropic online backend are now checked against output-token limits before being sent. Previously an overrun would only surface after dispatch, which wasted quota and could stall downstream processing. The guard blocks early and surfaces the rejection cleanly to the caller.

### Max-parallel request processor

The online processor now accepts a configurable maximum-concurrency value. Before this, concurrency was unbounded, which caused pressure problems under heavy load. Setting the limit is optional, behaviour is unchanged if you leave it unset.

TBD: need to confirm where exactly this is configured (flag, env var, or config file key) - not entirely sure, check whoever owns the processor config docs.

### Gemini batch request processor

Initial support for Gemini as a provider in the batch layer. This is first-pass integration, i would not assume full feature parity with the existing batch providers yet.

### JSON output fix

Corrected a curly-brace handling bug in the JSON repair path. Malformed JSON that triggered the repair logic could produce output with mismatched or duplicated braces. That is now resolved.

## No breaking changes

Public API is unchanged. Caching and resume behaviour are unchanged. The subsystems primarily touched are provider-integrations and online-request-processing.
