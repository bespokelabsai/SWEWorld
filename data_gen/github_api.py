#!/usr/bin/env python3
"""A small, cached, rate-limit-aware GitHub REST client.

Review cycles, issue-open times and reviewer identity exist nowhere in a git
clone — they are GitHub state, and only the API has them. So `build_episodes.py`
requires a token, and this module makes that requirement survivable:

* every response is written to `cache/github/`, keyed by URL, with its ETag;
* a re-run revalidates with `If-None-Match`, which GitHub does not bill against
  the rate limit when it answers 304;
* `--no-refresh` serves the whole run from cache and never opens a socket;
* the backfill is resumable, because each response is cached the moment it
  lands rather than at the end of the run.

Roughly 1,100 requests cover this repository's ~475 PRs. Authenticated, the
limit is 5,000/hour; unauthenticated it is 60/hour, which is why the token is
not optional.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import urlencode

import repolib

try:
    import requests
except ImportError:  # pragma: no cover
    raise SystemExit("requests is required: pip install -r data_gen/requirements.txt")

API_ROOT = "https://api.github.com"
TOKEN_ENV_VARS = ("GITHUB_TOKEN", "GH_TOKEN")


class GitHubError(RuntimeError):
    pass


class MissingFromCache(GitHubError):
    pass


def resolve_token(explicit: str | None = None) -> str:
    if explicit:
        return explicit
    for var in TOKEN_ENV_VARS:
        value = os.environ.get(var, "").strip()
        if value:
            return value
    for var in TOKEN_ENV_VARS:
        value = repolib.env_value(var)
        if value:
            return value
    raise SystemExit(
        "A GitHub token is required.\n"
        "  Review cycles, reviewer identity and issue timings are only in the API,\n"
        "  and unauthenticated access is 60 requests/hour against a repository that\n"
        "  needs ~1,100. Set GITHUB_TOKEN (a classic token with public_repo, or a\n"
        "  fine-grained token with public repository read access) and re-run:\n\n"
        "    GITHUB_TOKEN=ghp_... python3 data_gen/build_episodes.py\n\n"
        "  or add a GITHUB_TOKEN=... line to the gitignored .env at the repo root.\n"
        "  Once the cache is warm, --no-refresh runs the whole thing offline."
    )


class GitHub:
    def __init__(self, owner: str, repo: str, cache_dir: Path, *,
                 token: str | None = None, refresh: bool = True, verbose: int = 0):
        self.owner, self.repo = owner, repo
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.refresh = refresh
        self.verbose = verbose
        self.stats = {"requests": 0, "cache_hits": 0, "not_modified": 0, "waited_s": 0.0}
        self._session = requests.Session()
        if refresh:
            self.token = resolve_token(token)
            self._session.headers.update({
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "SWEWorld-data_gen/1",
            })
        else:
            self.token = ""

    # -- cache ---------------------------------------------------------------
    def _cache_path(self, url: str) -> Path:
        return self.cache_dir / f"{hashlib.sha256(url.encode()).hexdigest()}.json"

    def _read_cache(self, url: str) -> dict | None:
        path = self._cache_path(url)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            path.unlink(missing_ok=True)
            return None

    def _write_cache(self, url: str, entry: dict) -> None:
        path = self._cache_path(url)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(entry, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)

    # -- transport -----------------------------------------------------------
    def _respect_rate_limit(self, response: "requests.Response") -> None:
        remaining = response.headers.get("X-RateLimit-Remaining")
        reset = response.headers.get("X-RateLimit-Reset")
        if remaining is None or reset is None:
            return
        try:
            remaining, reset = int(remaining), int(reset)
        except ValueError:
            return
        if remaining > 5:
            return
        wait = max(0, reset - int(time.time())) + 2
        if wait > 0:
            print(f"  rate limit exhausted; sleeping {wait}s until reset")
            self.stats["waited_s"] += wait
            time.sleep(wait)

    def _fetch(self, url: str) -> dict:
        """Return a cache entry for `url`, fetching or revalidating as needed."""
        cached = self._read_cache(url)
        if cached is not None and not self.refresh:
            self.stats["cache_hits"] += 1
            return cached
        if cached is None and not self.refresh:
            raise MissingFromCache(
                f"--no-refresh, but {url} is not cached. Run once without it to backfill."
            )

        headers = {}
        if cached and cached.get("etag"):
            headers["If-None-Match"] = cached["etag"]

        last_error = None
        for attempt in range(5):
            try:
                response = self._session.get(url, headers=headers, timeout=30)
            except requests.RequestException as exc:
                last_error = exc
                time.sleep(2 ** attempt)
                continue

            self.stats["requests"] += 1
            self._respect_rate_limit(response)

            if response.status_code == 304 and cached:
                self.stats["not_modified"] += 1
                return cached
            if response.status_code == 200:
                entry = {
                    "url": url,
                    "etag": response.headers.get("ETag"),
                    "next": _next_link(response.headers.get("Link", "")),
                    "data": response.json(),
                }
                self._write_cache(url, entry)
                return entry
            if response.status_code == 404:
                entry = {"url": url, "etag": None, "next": None, "data": None}
                self._write_cache(url, entry)
                return entry
            if response.status_code in (403, 429):
                retry_after = response.headers.get("Retry-After")
                wait = int(retry_after) if retry_after and retry_after.isdigit() else 60
                # A 403 with quota left is the secondary (abuse) limit, which
                # only backing off will clear.
                print(f"  throttled ({response.status_code}); waiting {wait}s")
                self.stats["waited_s"] += wait
                time.sleep(wait)
                continue
            if 500 <= response.status_code < 600:
                time.sleep(2 ** attempt)
                last_error = GitHubError(f"{response.status_code} from {url}")
                continue
            raise GitHubError(f"{response.status_code} from {url}: {response.text[:200]}")

        raise GitHubError(f"giving up on {url}: {last_error}")

    # -- public --------------------------------------------------------------
    def get(self, path: str, **params: Any) -> Any:
        url = path if path.startswith("http") else f"{API_ROOT}{path}"
        if params:
            url = f"{url}?{urlencode(params)}"
        return self._fetch(url)["data"]

    def paginate(self, path: str, **params: Any) -> Iterator[dict]:
        """Follow Link rel=next.

        The `next` URL is followed rather than reconstructed with page numbers,
        because GitHub answers some endpoints (issues, notably) with opaque
        cursors instead.
        """
        params.setdefault("per_page", 100)
        url = path if path.startswith("http") else f"{API_ROOT}{path}"
        url = f"{url}?{urlencode(params)}"
        while url:
            entry = self._fetch(url)
            data = entry.get("data") or []
            if isinstance(data, dict):
                data = [data]
            yield from data
            url = entry.get("next")

    # -- endpoints this project needs ---------------------------------------
    def pulls(self) -> list[dict]:
        return list(self.paginate(f"/repos/{self.owner}/{self.repo}/pulls",
                                  state="all", sort="created", direction="asc"))

    def pull_reviews(self, number: int) -> list[dict]:
        return list(self.paginate(f"/repos/{self.owner}/{self.repo}/pulls/{number}/reviews"))

    def pull_commits(self, number: int) -> list[dict]:
        return list(self.paginate(f"/repos/{self.owner}/{self.repo}/pulls/{number}/commits"))

    def issues(self) -> list[dict]:
        """Every issue, including PRs — the caller filters on `pull_request`."""
        return list(self.paginate(f"/repos/{self.owner}/{self.repo}/issues",
                                  state="all", sort="created", direction="asc"))

    def pull_review_comments(self, number: int) -> list[dict]:
        """Line-level review comments: which file and line a reviewer objected to."""
        return list(self.paginate(f"/repos/{self.owner}/{self.repo}/pulls/{number}/comments"))

    def issue_comments(self, number: int) -> list[dict]:
        """The conversation on an issue or pull request."""
        return list(self.paginate(
            f"/repos/{self.owner}/{self.repo}/issues/{number}/comments"))

    def releases(self) -> list[dict]:
        return list(self.paginate(f"/repos/{self.owner}/{self.repo}/releases"))

    def labels(self) -> list[dict]:
        return list(self.paginate(f"/repos/{self.owner}/{self.repo}/labels"))

    def branches(self) -> list[dict]:
        return list(self.paginate(f"/repos/{self.owner}/{self.repo}/branches"))


def _next_link(link_header: str) -> str | None:
    for part in link_header.split(","):
        section = part.split(";")
        if len(section) < 2:
            continue
        if 'rel="next"' in section[1].strip():
            return section[0].strip().strip("<>")
    return None
