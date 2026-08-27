---
title: "Postmortem: kluster.ai DeepSeek Output-Token Default"
author: emil
created_at: 2025-03-18T09:49:00+00:00
---

# Postmortem: kluster.ai DeepSeek Output-Token Default

**Date:** 2025-03-18
**Status:** Open (action items not yet resolved)

---

## What Happened

curator estimates output tokens before a request completes, using `max_output_tokens // 4` as a proxy for rate-limit headroom. The assumption baked into that heuristic is that the provider's max output token ceiling is consistent with what curator expects.

kluster.ai's DeepSeek endpoint silently applies a different default for max output tokens than other providers. The pre-request estimate diverged significantly from actual usage. The run completed, cost figures were logged, and nothing indicated anything was wrong.

## Impact

- Cost estimates for kluster.ai DeepSeek runs were materially inaccurate. I don't have the exact magnitude to hand, need to pull the actual vs. estimated figures from whoever owns the cost log dashboard.
- Throughput headroom was also miscalculated for those runs, meaning the rate limiter was not working as intended.
- No user-visible error. No alert fired. The mismatch was completely invisible at the surface.

Duration of exposure is unclear. We caught it on a specific run but we don't know how many previous runs were also affected.

## Detection

Caught by manual inspection of cost logs after a run that appeared normal. The estimator feeds throughput control, not a validation gate, so there was nothing to trip on. No alert fired. If nobody had looked at the logs we would not have known.

## Root Cause

The `max_output_tokens // 4` heuristic assumes a provider-consistent token ceiling. kluster.ai's DeepSeek overrides that ceiling silently with its own value, and curator has no mechanism to detect the discrepancy. There is no cross-check between the estimated token budget used for rate limiting and the actual token counts returned in the response.

This is not a bug in the heuristic itself exactly. The heuristic is a reasonable approximation when the ceiling is what you expect. The problem is that there is no validation step that would surface a case where it is not.

## What Went Well

Manual log review caught it before it compounded further. The run completed without a crash or data loss, so the impact is scoped to cost accuracy and rate limiter fidelity.

## Open Questions

- **Batch mode:** whether batch-mode requests are exposed to the same blindspot is not yet verified. The batch processor uses a different request path and its cost-estimation surface has not been audited against this incident. This needs to happen before we close this postmortem.
- **Exposure window:** how many runs before detection were also affected? Needs someone to go back through the cost logs for kluster.ai DeepSeek runs.
- **Other providers:** are there other providers where the same silent ceiling mismatch could exist? I'd want a quick check before assuming this is kluster-specific.

## Action Items

- [ ] Cross-check estimated vs. actual token counts at run completion and warn (or log loudly) if they diverge beyond a threshold. No silent mismatch.
- [ ] Audit batch-mode cost estimation path against this incident before closing the postmortem.
- [ ] Pull historical kluster.ai DeepSeek run logs to assess exposure window. (needs whoever owns the cost log dashboard)
