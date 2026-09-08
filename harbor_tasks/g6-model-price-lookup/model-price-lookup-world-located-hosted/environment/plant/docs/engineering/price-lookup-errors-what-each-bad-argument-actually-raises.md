---
title: "Price Lookup Errors: What Each Bad Argument Actually Raises"
author: gideon
created_at: 2025-05-13T09:30:00+00:00
---

## Why this page exists

**Date:** 2025-05-13

A run showed up in the viewer with the cost column empty, and the only thing in the logs was a `PriceLookupError` with a message that honestly told us nothing about which of the three arguments was the broken one. Took me most of a morning to figure out it was the model key and not the provider.

So basically I sat down and worked through the two i could reproduce on demand — a provider we do not have, and a model key that is not under a provider we do — and wrote down what comes back for each, plus what happens when both are wrong at once. That last part is the bit that cost me the morning, so it gets its own section.

This is a description of current behaviour on main as of 2025-05-13. It is not a proposal, and it is not the whole error surface — see the caveat below. If we change the precedence later this page needs updating.

## The call being described

Everything below is about the single entry point:

```
get_model_price(provider, model_key, context_window)
```

It raises `PriceLookupError` on anything it cannot resolve, and the useful part is the `code` attribute on the exception, not the message. The message is the thing that was unhelpful in the first place.

Validation happens in this order internally: provider registry lookup, then model table lookup within that provider, then the context window tier. That order matters and it is the whole reason for the precedence section below.

## The two i could pin down

Each row here is a call where exactly one argument is bad and the other two are good.

| what is broken | code you get |
| --- | --- |
| provider string is not in the registry at all (typo, or a provider we never added) | `unknown_provider` |
| provider is fine, model key does not exist under that provider | `unknown_model` |

**What this page does not cover.** The window tier is the third check and i could not get a stable answer out of it — same call, same args, different code depending on which branch caught it first, and at least one path where it quietly borrowed a neighbouring tier instead of failing at all. I am not writing a code name into this page that i am not sure of; somebody who actually owns that check should write down what a bad window comes back as, because right now it is folklore. Same for a tier that resolves fine and simply has no number in it — that is a data problem on our side rather than a caller mistake, and it needs its own owner and its own page.

Also, passing `None` for the context window is not an error. It falls back to the model's default window. tbh i expected it to blow up and it does not, so if you are debugging a wrong-but-not-missing cost, check whether somebody is passing None and silently getting the default tier.

## When more than one argument is wrong

First failure in the validation order wins, and nothing after it runs. That is the entire rule, but it surprises people so here is a worked pair.

Call it with a provider that is not registered, a garbage model key and a nonsense context window like `-1`, and you get `unknown_provider`. Fine, that is what you would guess.

Same args but with a provider we do have registered and it comes back `unknown_model` instead, so the junk window never even gets looked at. Meaning: a green `unknown_model` does not tell you the context window you passed was acceptable. It tells you nothing at all about the window, because that check was never reached.

The practical consequence is that fixing errors here is iterative. You fix the provider, re-run, and get a second error you did not know about. Do not assume one clean error means one broken argument.

## What to do with each code

- `unknown_provider` — caller side. Check spelling against the registry, and check whether the provider was ever registered in this environment. We have had cases where it exists in prod config and not in a local run.
- `unknown_model` — caller side, usually a stale model key after a provider renames something. Grep the model table before assuming the price data is missing.

Anything that comes back and is neither of those two is outside what i tested, and i would not assume the code you are looking at means what its name suggests until somebody has checked it the way i checked these.

One follow-up i am not doing in this page: the exception message should include which argument failed, so that reading the `code` attribute is not required. i dunno who owns that helper now, but it is a small change and would have saved the morning that started this.
