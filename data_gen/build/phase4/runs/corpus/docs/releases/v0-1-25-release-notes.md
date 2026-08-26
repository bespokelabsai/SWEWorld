---
title: "v0.1.25 Release Notes"
author: emil
created_at: 2025-05-30T09:14:00+00:00
---

# v0.1.25 Release Notes

## What's in this release

### o3 family support

o3-mini is now in the provider support table with schema support enabled. Group fallback does not cover the o3 family reliably, so these models are not picked up automatically the way other families are. If you are targeting o3-mini or any other o3 variant, use the explicit table entry. Do not rely on group fallback here.

### Finetuning client

New client interface for finetuning workflows. I dont have a lot more detail on the surface API to document here yet, lets circle back on that once the usage guide is written.

### Torch now optional

Previously, importing the package in an environment without `torch` installed would crash on import. That is fixed. Torch is now optional and the import handles its absence cleanly.

### Curator LLM default app ID

Added a default `app_id` parameter to the curator LLM. Callers no longer need to supply one on every invocation. If you were passing it explicitly before, that still works.

---

## Known gaps

- Download dataset from viewer (PR 652) is still open, did not make this cut. Will land in a follow-on release.

---

## Stats

357 changes merged across 24 releases to date.
