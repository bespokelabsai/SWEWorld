---
title: "Batch job status persistence across process restarts"
author: emil
created_at: 2025-03-21T09:14:00+00:00
---

# Batch job status persistence across process restarts

## The problem

When a batch run is interrupted, the restart needs to answer three questions: which requests have already been submitted, which have received responses, and which were still in flight when the process died. Right now the answer is split across two stores, and a restart that only consults one of them gets a partial picture.

This happens more than it should. The two stores have different write paths, different owners, and nothing currently enforces that a restart reads both before deciding what to do.

## What persists where

- **Responses file**, append-only, keyed by request hash
  - written by the online processor
  - an entry is appended the moment a request is accepted, not when the response arrives back
  - that ordering matters: a restart can tell which requests went out without waiting on results
- **Metadata db**, holds the batch job records: submission IDs, status, file IDs, per-row accounting
  - written exclusively by batch-mode
  - nothing else should write to it (see house rules below)

These two stores are intentionally separate in what they track. The responses file is about cache state. The metadata db is about job lifecycle. A restart needs both.

## House rules

**Read-only opens for anything that only reports.** Any path that reads job records to decide what to do next, status reporting, resume-eligibility checks, anything like that, must open the metadata db with `mode=ro`. The reason is straightforward: a read-only connection cant leave a partial write that a concurrent batch worker reads back as settled state. This has burned us before (not entirely sure of the exact incident but i believe it was the March resync run that had the duplicate submission problem, need to confirm with whoever owns the batch polling code).

Write access stays with the submission and polling paths, which already serialize through a single executor. That part is fine as-is.

## Open gap: CURATOR_CACHE_DIR portability

A user configured `CURATOR_CACHE_DIR=/mnt/shared` so they could start a run on one machine and resume on another. The responses file and request files follow `CURATOR_CACHE_DIR` correctly. The metadata db does not, it defaults to a path that is not under `CURATOR_CACHE_DIR`, which means "resumable" means two different things depending on which half of the state you're asking.

This is a real gap and not a corner case. Anyone doing distributed or machine-hopping runs hits it immediately. Not yet tracked as an issue as of today.

- [ ] open an issue for the metadata db path not respecting `CURATOR_CACHE_DIR`
- [ ] confirm whether fixing this is just a path default change or if there are schema migration concerns (TBD, need someone who knows the db init code)

## Open questions

- Does the online processor guarantee the append to the responses file is flushed before the batch worker reads it back? I assume yes but haven't verified.
- If a restart finds a request in the responses file but no corresponding record in the metadata db, what wins? I think the responses file should, but we need to be intentional here about which store is authoritative for submission state vs. cache state.
