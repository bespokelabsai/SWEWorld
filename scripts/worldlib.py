#!/usr/bin/env python3
"""Shared plumbing for the SWEWorld ingestion scripts.

Everything in here exists because all four ingest_*.py scripts need it and
none of them should reimplement it: .env parsing, the persona list that is the
join key across all four services, a TLS-aware HTTP session, the timestamp
conversions each service demands, and an error collector that reports
`file:line: what is wrong` instead of a traceback.

See data/schemas/identities.md for the conventions this module enforces.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator, Sequence

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is required: pip install -r scripts/requirements.txt")

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENV_FILE = REPO_ROOT / ".env"
DEFAULT_DATA_DIR = REPO_ROOT / "data"
GITEA_TOKEN_FILE = Path("/etc/sweworld/gitea-token")
BOOKSTACK_TOKEN_FILE = Path("/etc/sweworld/bookstack-token")

ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,31}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


# =============================================================================
# Error reporting
# =============================================================================
class ValidationError(Exception):
    """A single problem with input data, located in a file."""

    def __init__(self, message: str, path: Path | str | None = None, line: int | None = None):
        self.message = message
        self.path = path
        self.line = line
        super().__init__(str(self))

    def __str__(self) -> str:
        where = ""
        if self.path is not None:
            try:
                rel = Path(self.path).relative_to(REPO_ROOT)
            except ValueError:
                rel = Path(self.path)
            where = str(rel)
            if self.line is not None:
                where += f":{self.line}"
            where += ": "
        return f"{where}{self.message}"


class Problems:
    """Collects every validation failure so one run reports all of them.

    Dying on the first error means fixing a generated dataset one line per run,
    which is miserable when the generator produced a hundred similar mistakes.
    """

    def __init__(self, fail_fast: bool = False):
        self.errors: list[ValidationError] = []
        self.warnings: list[ValidationError] = []
        self.fail_fast = fail_fast

    def error(self, message: str, path: Path | str | None = None, line: int | None = None) -> None:
        err = ValidationError(message, path, line)
        self.errors.append(err)
        if self.fail_fast:
            raise err

    def warn(self, message: str, path: Path | str | None = None, line: int | None = None) -> None:
        self.warnings.append(ValidationError(message, path, line))

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)

    # Deliberately no __bool__. An "is empty == falsy" collector made
    # `if problems:` silently mean "no collector was passed", which discarded
    # every validation error on clean-looking input.

    def print_warnings(self) -> None:
        for w in self.warnings:
            print(f"  warn  {w}", file=sys.stderr)

    def raise_if_any(self) -> None:
        """Print every collected error and exit non-zero."""
        self.print_warnings()
        if not self.errors:
            return
        print(
            f"\n{len(self.errors)} validation error(s):\n",
            file=sys.stderr,
        )
        for err in self.errors:
            print(f"  {err}", file=sys.stderr)
        print("", file=sys.stderr)
        raise SystemExit(1)


def check_keys(
    obj: dict,
    *,
    required: Iterable[str] = (),
    optional: Iterable[str] = (),
    problems: Problems,
    path: Path | str | None = None,
    line: int | None = None,
    context: str = "",
) -> None:
    """Enforce the 'unknown fields are rejected, not ignored' rule.

    A typo'd key that is silently dropped is the worst possible failure mode for
    generated data: everything appears to work and the field is just missing.
    """
    prefix = f"{context}: " if context else ""
    allowed = set(required) | set(optional)
    for key in required:
        if obj.get(key) in (None, ""):
            problems.error(f"{prefix}missing required field {key!r}", path, line)
    for key in obj:
        if key not in allowed:
            close = _closest(key, allowed)
            hint = f" (did you mean {close!r}?)" if close else ""
            problems.error(f"{prefix}unknown field {key!r}{hint}", path, line)


def _closest(word: str, candidates: Iterable[str]) -> str | None:
    """Cheap typo hint — no stdlib difflib import needed for this small job."""
    best, best_score = None, 0.0
    for cand in candidates:
        common = len(set(word) & set(cand))
        score = common / max(len(set(word) | set(cand)), 1)
        if score > best_score:
            best, best_score = cand, score
    return best if best_score >= 0.6 else None


# =============================================================================
# .env
# =============================================================================
def load_env(env_file: Path | None = None) -> dict[str, str]:
    """Parse .env if present, then fill in what the world provides itself.

    Inside the world image there is no .env: every service is configured at
    image build, so the scripts fall back to the same defaults and read tokens
    straight off disk. Running from outside, a .env supplies anything that
    differs.
    """
    env_file = Path(env_file) if env_file else DEFAULT_ENV_FILE
    env: dict[str, str] = {}
    if not env_file.exists():
        for key, path in (("GITEA_API_TOKEN", GITEA_TOKEN_FILE),
                          ("BOOKSTACK_TOKEN", BOOKSTACK_TOKEN_FILE)):
            if path.exists():
                env[key] = path.read_text().strip()
        return env
    for raw in env_file.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip()
    # Tokens on disk win only where .env is silent.
    for key, path in (("GITEA_API_TOKEN", GITEA_TOKEN_FILE),
                      ("BOOKSTACK_TOKEN", BOOKSTACK_TOKEN_FILE)):
        if not env.get(key) and path.exists():
            env[key] = path.read_text().strip()
    return env


@dataclass
class World:
    """Connection details for a running world, derived from .env."""

    env: dict[str, str]

    @property
    def domain(self) -> str:
        return self.env.get("WORLD_DOMAIN", "world.local")

    @property
    def http_port(self) -> int:
        return int(self.env.get("HTTP_PORT", "80"))

    @property
    def imap_port(self) -> int:
        return int(self.env.get("IMAP_PORT", "143"))

    @property
    def imaps_port(self) -> int:
        return int(self.env.get("IMAPS_PORT", "993"))

    @property
    def admin_user(self) -> str:
        return self.env.get("WORLD_ADMIN_USER", "worldadmin")

    @property
    def admin_password(self) -> str:
        return self.env.get("WORLD_ADMIN_PASSWORD", "worldadmin")

    @property
    def admin_email(self) -> str:
        return self.env.get("WORLD_ADMIN_EMAIL", f"worldadmin@{self.domain}")

    @property
    def persona_password(self) -> str:
        # Eight characters minimum: Gitea rejects anything shorter when
        # creating an account, and reports it as "PasswordIsRequired", which
        # sends you looking for a missing field rather than a short one. The
        # same value logs a persona into git, mail and the wiki, so it has to
        # satisfy the strictest of them.
        return self.env.get("MAIL_PERSONA_PASSWORD", "persona-world")

    def url(self, service: str, path: str = "") -> str:
        """http://<service>.<domain><path>, port included only if non-standard."""
        port = "" if self.http_port == 80 else f":{self.http_port}"
        return f"http://{service}.{self.domain}{port}{path}"

    def require(self, *keys: str) -> None:
        """Fail early and clearly if a needed credential is absent."""
        missing = [k for k in keys if not self.env.get(k)]
        if missing:
            raise SystemExit(
                "missing from .env: "
                + ", ".join(missing)
                + "\n  run ./scripts/bootstrap.sh to populate it"
            )


def session(world: World | None = None):
    """A plain requests session. Imported lazily so --dry-run works without it."""
    try:
        import requests
    except ImportError:  # pragma: no cover
        sys.exit("requests is required: pip install -r scripts/requirements.txt")
    return requests.Session()


# =============================================================================
# Timestamps
# =============================================================================
def parse_ts(value: Any, *, path=None, line=None, problems: Problems | None = None,
             field_name: str = "timestamp") -> dt.datetime | None:
    """Parse an ISO-8601 timestamp with an explicit offset.

    Bare local times are rejected: the schemas require an offset because these
    timestamps end up in four systems with different timezone handling, and an
    ambiguous one silently shifts content by hours.
    """
    # PyYAML resolves ISO-8601 scalars to datetime objects before we ever see
    # them, so a YAML-sourced timestamp arrives already parsed. Accept that,
    # but hold it to the same offset requirement as a string.
    if isinstance(value, dt.datetime):
        if value.tzinfo is None:
            if problems is not None:
                problems.error(
                    f"{field_name} {value.isoformat()} has no UTC offset "
                    "(use ...Z or ...+01:00)", path, line,
                )
            return None
        return value
    if isinstance(value, dt.date):
        if problems is not None:
            problems.error(
                f"{field_name} {value.isoformat()} is a date without a time or "
                "offset — use a full ISO-8601 timestamp", path, line,
            )
        return None
    if not isinstance(value, str):
        if problems is not None:
            problems.error(
                f"{field_name} must be an ISO-8601 timestamp, got "
                f"{type(value).__name__}", path, line,
            )
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = dt.datetime.fromisoformat(text)
    except ValueError:
        if problems is not None:
            problems.error(f"{field_name} {value!r} is not valid ISO-8601", path, line)
        return None
    if parsed.tzinfo is None:
        if problems is not None:
            problems.error(
                f"{field_name} {value!r} has no UTC offset (use ...Z or ...+01:00)", path, line
            )
        return None
    return parsed


def to_epoch_ms(when: dt.datetime) -> int:
    """Mattermost's create_at is epoch milliseconds."""
    return int(when.timestamp() * 1000)


def to_git_date(when: dt.datetime) -> str:
    """git accepts strict ISO-8601 in GIT_AUTHOR_DATE / GIT_COMMITTER_DATE."""
    return when.isoformat()


def to_iso(when: dt.datetime) -> str:
    return when.isoformat()


# =============================================================================
# Identities
# =============================================================================
@dataclass
class Persona:
    id: str
    display_name: str
    email: str
    role: str = ""
    timezone: str = "UTC"
    password: str | None = None
    gitea_username: str | None = None
    mattermost_username: str | None = None
    git_author: str | None = None
    mailbox: str | None = None
    is_admin: bool = False

    def resolved(self, world: World) -> "Persona":
        """Apply the documented defaults from identities.md."""
        return Persona(
            id=self.id,
            display_name=self.display_name,
            email=self.email,
            role=self.role,
            timezone=self.timezone,
            password=self.password or world.persona_password,
            gitea_username=self.gitea_username or self.id,
            mattermost_username=self.mattermost_username or self.id,
            git_author=self.git_author or f"{self.display_name} <{self.email}>",
            mailbox=self.mailbox or self.email,
            is_admin=self.is_admin,
        )

    @property
    def git_name(self) -> str:
        """Name half of 'Display Name <email>'."""
        author = self.git_author or ""
        return author.split("<")[0].strip() or self.display_name

    @property
    def git_email(self) -> str:
        """Email half of 'Display Name <email>'."""
        author = self.git_author or ""
        if "<" in author and ">" in author:
            return author.split("<", 1)[1].split(">", 1)[0].strip()
        return self.email

    @property
    def first_name(self) -> str:
        return self.display_name.split(" ", 1)[0]

    @property
    def last_name(self) -> str:
        parts = self.display_name.split(" ", 1)
        return parts[1] if len(parts) > 1 else ""


PERSONA_REQUIRED = ("id", "display_name", "email")
PERSONA_OPTIONAL = (
    "role", "timezone", "password", "gitea_username", "mattermost_username",
    "git_author", "mailbox", "is_admin",
)


@dataclass
class Identities:
    personas: dict[str, Persona] = field(default_factory=dict)
    path: Path | None = None

    def __iter__(self) -> Iterator[Persona]:
        return iter(self.personas.values())

    def __len__(self) -> int:
        return len(self.personas)

    def get(self, persona_id: str) -> Persona | None:
        return self.personas.get(persona_id)

    def require(self, persona_id: Any, problems: Problems, path=None, line=None,
                field_name: str = "author") -> Persona | None:
        """Look up a persona, recording a precise error if it is unknown."""
        if persona_id is None:
            # check_keys already reported the field as missing; saying it twice
            # just pads the error list.
            return None
        if not isinstance(persona_id, str) or not persona_id:
            problems.error(f"{field_name} must be a persona id string", path, line)
            return None
        persona = self.personas.get(persona_id)
        if persona is None:
            known = ", ".join(sorted(self.personas)[:8]) or "(none)"
            problems.error(
                f"unknown persona {persona_id!r} in {field_name} — known ids: {known}",
                path, line,
            )
        return persona

    @classmethod
    def load(cls, path: Path, world: World, problems: Problems) -> "Identities":
        """Parse and validate data/identities.yaml per data/schemas/identities.md."""
        if not path.exists():
            problems.error(
                "identities file not found — every other schema references it", path
            )
            return cls(path=path)
        try:
            raw = yaml.safe_load(path.read_text()) or {}
        except yaml.YAMLError as exc:
            problems.error(f"invalid YAML: {exc}", path)
            return cls(path=path)

        if not isinstance(raw, dict):
            problems.error("top level must be a mapping", path)
            return cls(path=path)

        check_keys(raw, required=("version", "domain", "personas"),
                   problems=problems, path=path)

        if raw.get("version") != 1:
            problems.error(f"version must be 1, got {raw.get('version')!r}", path)
        domain = raw.get("domain")
        if domain and domain != world.domain:
            problems.error(
                f"domain {domain!r} does not match WORLD_DOMAIN {world.domain!r} "
                "— this data was generated for a different world",
                path,
            )

        entries = raw.get("personas")
        if not isinstance(entries, list) or not entries:
            problems.error("personas must be a non-empty list", path)
            return cls(path=path)

        personas: dict[str, Persona] = {}
        seen_emails: dict[str, str] = {}
        seen_gitea: dict[str, str] = {}
        seen_mm: dict[str, str] = {}

        for index, entry in enumerate(entries):
            where = f"personas[{index}]"
            if not isinstance(entry, dict):
                problems.error(f"{where} must be a mapping", path)
                continue
            check_keys(entry, required=PERSONA_REQUIRED, optional=PERSONA_OPTIONAL,
                       problems=problems, path=path, context=where)

            pid = entry.get("id")
            if not isinstance(pid, str) or not ID_RE.match(pid or ""):
                problems.error(
                    f"{where}: id {pid!r} must match {ID_RE.pattern}", path
                )
                continue
            if pid in personas:
                problems.error(f"{where}: duplicate persona id {pid!r}", path)
                continue

            email = entry.get("email", "")
            if not EMAIL_RE.match(email or ""):
                problems.error(f"{where}: email {email!r} is not a valid address", path)
            elif domain and not email.endswith(f"@{domain}"):
                problems.error(
                    f"{where}: email {email!r} is not in domain {domain!r}", path
                )

            persona = Persona(
                id=pid,
                display_name=entry.get("display_name", ""),
                email=email,
                role=entry.get("role", ""),
                timezone=entry.get("timezone", "UTC"),
                password=entry.get("password"),
                gitea_username=entry.get("gitea_username"),
                mattermost_username=entry.get("mattermost_username"),
                git_author=entry.get("git_author"),
                mailbox=entry.get("mailbox"),
                is_admin=bool(entry.get("is_admin", False)),
            ).resolved(world)

            for value, seen, label in (
                (persona.email, seen_emails, "email"),
                (persona.gitea_username, seen_gitea, "gitea_username"),
                (persona.mattermost_username, seen_mm, "mattermost_username"),
            ):
                if value in seen:
                    problems.error(
                        f"{where}: {label} {value!r} already used by persona "
                        f"{seen[value]!r}", path,
                    )
                else:
                    seen[value] = pid

            personas[pid] = persona

        return cls(personas=personas, path=path)


# =============================================================================
# JSONL
# =============================================================================
def read_jsonl(path: Path, problems: Problems) -> list[tuple[int, dict]]:
    """Read a .jsonl file, returning (line_number, object) pairs.

    Malformed lines are recorded with their line number and skipped, so one run
    reports every bad line rather than stopping at the first.
    """
    if not path.exists():
        problems.error("file not found", path)
        return []
    rows: list[tuple[int, dict]] = []
    for lineno, raw in enumerate(path.read_text().splitlines(), start=1):
        text = raw.strip()
        if not text or text.startswith("#"):
            continue
        try:
            obj = json.loads(text)
        except json.JSONDecodeError as exc:
            problems.error(f"invalid JSON ({exc.msg} at column {exc.colno})", path, lineno)
            continue
        if not isinstance(obj, dict):
            problems.error("each line must be a JSON object", path, lineno)
            continue
        rows.append((lineno, obj))
    return rows


# =============================================================================
# CLI
# =============================================================================
def base_parser(description: str) -> argparse.ArgumentParser:
    """Arguments common to every ingestion script."""
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--data-dir", type=Path, default=DEFAULT_DATA_DIR,
        help="directory holding the generated content (default: data/)",
    )
    parser.add_argument(
        "--env-file", type=Path, default=DEFAULT_ENV_FILE,
        help="path to .env (default: .env)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="parse, validate and build artifacts without writing to any service",
    )
    parser.add_argument(
        "--fail-fast", action="store_true",
        help="stop at the first validation error instead of collecting all of them",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="per-item output")
    return parser


def validate_common_args(args: argparse.Namespace) -> None:
    """Check the arguments themselves before touching any data."""
    if not args.data_dir.exists():
        raise SystemExit(f"--data-dir {args.data_dir} does not exist")
    if not args.data_dir.is_dir():
        raise SystemExit(f"--data-dir {args.data_dir} is not a directory")
    # No .env is required: inside the world image every value has a default and
    # the tokens are read from /etc/sweworld/.


def setup(args: argparse.Namespace) -> tuple[World, Identities, Problems]:
    """Load .env and identities.yaml — the first step of every script."""
    validate_common_args(args)
    # load_env handles a missing .env itself, falling back to the tokens the
    # world writes to /etc/sweworld/. Short-circuiting to {} here skipped that.
    env = load_env(args.env_file)
    world = World(env=env)
    problems = Problems(fail_fast=args.fail_fast)
    identities = Identities.load(args.data_dir / "identities.yaml", world, problems)
    return world, identities, problems


# =============================================================================
# Output
# =============================================================================
GREEN, RED, YELLOW, CYAN, GREY, BOLD, RESET = (
    "\033[32m", "\033[31m", "\033[33m", "\033[36m", "\033[90m", "\033[1m", "\033[0m"
)


def heading(text: str) -> None:
    print(f"\n{BOLD}{CYAN}==>{RESET} {BOLD}{text}{RESET}")


def ok(text: str) -> None:
    print(f"  {GREEN}ok{RESET}    {text}")


def info(text: str) -> None:
    print(f"  {GREY}{text}{RESET}")


def warn(text: str) -> None:
    print(f"  {YELLOW}warn{RESET}  {text}")


def dry(text: str) -> None:
    print(f"  {CYAN}plan{RESET}  {text}")


def summarise(dry_run: bool, actions: Sequence[str]) -> None:
    heading("Summary")
    for line in actions:
        print(f"  {line}")
    if dry_run:
        print(f"\n{YELLOW}Dry run — nothing was written to any service.{RESET}")
    else:
        print(f"\n{GREEN}Done.{RESET}")
