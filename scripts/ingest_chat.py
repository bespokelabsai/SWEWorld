#!/usr/bin/env python3
"""Load chat history into Mattermost via its bulk import.

Input
-----
data/identities.yaml    the persona list
data/channels.yaml      channel definitions
data/messages.jsonl     one message per line, threads linked by thread_id

channels.yaml:

    version: 1
    team: world                     # must match MM_TEAM_NAME
    channels:
      - name: engineering           # required, ^[a-z0-9-_]+$
        display_name: Engineering   # required
        type: O                     # O public (default) | P private
        purpose: ...                # optional
        header: ...                 # optional
        members: [alice, bob]       # optional persona ids

messages.jsonl:

    {"id": "m1",                       # optional, required if replied to
     "channel": "engineering",         # required, or null for a DM
     "participants": ["alice","bob"],  # required when channel is null
     "author": "alice",                # required, persona id
     "created_at": "2026-02-11T09:02:14Z",  # required, ISO-8601
     "text": "Deploy is green.",       # required unless reactions present
     "thread_id": null,                # optional, id of the root message
     "reactions": [{"author":"bob","emoji":"tada"}],
     "pinned": false,
     "attachments": [{"path": "files/diagram.png"}]}

Why the input is flat but the output is not
-------------------------------------------
Mattermost's importer requires each object wrapped under a key matching its
type ({"type":"post","post":{...}}), objects in a fixed order
(version -> team -> channel -> user -> post -> direct_channel -> direct_post),
create_at in epoch MILLISECONDS, and thread replies nested inside their root
post's replies[] array with no parent pointer anywhere.

Authoring that by hand is error-prone and unreviewable, so messages.jsonl stays
flat and this script performs the conversion. See data/schemas/messages.md.

--dry-run writes the complete, valid import archive and stops without calling
mmctl. The archive path is printed so it can be inspected.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import worldlib as wl  # noqa: E402

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is required: pip install -r scripts/requirements.txt")

CHANNEL_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
CHANNEL_REQUIRED = ("name", "display_name")
CHANNEL_OPTIONAL = ("type", "purpose", "header", "members")
MESSAGE_REQUIRED = ("author", "created_at")
MESSAGE_OPTIONAL = ("id", "channel", "participants", "text", "thread_id",
                    "reactions", "pinned", "attachments")
REACTION_REQUIRED = ("author", "emoji")
REACTION_OPTIONAL = ("created_at",)

# Inside the world image everything is a local process: no docker, no compose.
MMCTL = "/opt/mattermost/bin/mmctl"
IMPORT_DIR = "/opt/mattermost/data/import"


# =============================================================================
# Parsing
# =============================================================================
def load_channels(path: Path, world: wl.World, identities: wl.Identities,
                  problems: wl.Problems) -> tuple[str, dict[str, dict]]:
    """Parse and validate channels.yaml. Returns (team_name, channels)."""
    if not path.exists():
        problems.error("channels.yaml not found", path)
        return "", {}
    try:
        raw = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError as exc:
        problems.error(f"invalid YAML: {exc}", path)
        return "", {}

    wl.check_keys(raw, required=("version", "team", "channels"),
                  problems=problems, path=path)
    if raw.get("version") != 1:
        problems.error(f"version must be 1, got {raw.get('version')!r}", path)

    team = raw.get("team", "")
    expected_team = world.env.get("MM_TEAM_NAME", "world")
    if team and team != expected_team:
        problems.error(
            f"team {team!r} does not match MM_TEAM_NAME {expected_team!r}", path
        )

    channels: dict[str, dict] = {}
    entries = raw.get("channels")
    if not isinstance(entries, list) or not entries:
        problems.error("channels must be a non-empty list", path)
        return team, channels

    for index, entry in enumerate(entries):
        context = f"channels[{index}]"
        if not isinstance(entry, dict):
            problems.error(f"{context} must be a mapping", path)
            continue
        wl.check_keys(entry, required=CHANNEL_REQUIRED, optional=CHANNEL_OPTIONAL,
                      problems=problems, path=path, context=context)

        name = entry.get("name")
        if isinstance(name, str) and not CHANNEL_NAME_RE.match(name):
            problems.error(
                f"{context}: name {name!r} must match {CHANNEL_NAME_RE.pattern}", path
            )
        if name in channels:
            problems.error(f"{context}: duplicate channel {name!r}", path)
            continue
        ctype = entry.get("type", "O")
        if ctype not in ("O", "P"):
            problems.error(f"{context}: type {ctype!r} must be 'O' or 'P'", path)
        for member in entry.get("members") or []:
            identities.require(member, problems, path, None, f"{context}.members")

        channels[name] = {
            "name": name,
            "display_name": entry.get("display_name", ""),
            "type": ctype,
            "purpose": entry.get("purpose", "") or "",
            "header": entry.get("header", "") or "",
            "members": entry.get("members") or [],
        }
    return team, channels


def load_messages(path: Path, channels: dict[str, dict], identities: wl.Identities,
                  data_dir: Path, problems: wl.Problems) -> list[dict]:
    """Parse messages.jsonl and validate every line."""
    rows = wl.read_jsonl(path, problems)
    messages: list[dict] = []
    ids: dict[str, int] = {}

    # First pass: collect ids so thread_id can be checked against them.
    for lineno, obj in rows:
        mid = obj.get("id")
        if mid is not None:
            if not isinstance(mid, str) or not mid:
                problems.error("id must be a non-empty string", path, lineno)
            elif mid in ids:
                problems.error(
                    f"duplicate message id {mid!r} (also on line {ids[mid]})", path, lineno
                )
            else:
                ids[mid] = lineno

    roots = {mid for mid, _ in ids.items()}

    for lineno, obj in rows:
        wl.check_keys(obj, required=MESSAGE_REQUIRED, optional=MESSAGE_OPTIONAL,
                      problems=problems, path=path, line=lineno)

        channel = obj.get("channel")
        participants = obj.get("participants")
        is_dm = channel is None

        if is_dm:
            if not isinstance(participants, list) or not (2 <= len(participants) <= 8):
                problems.error(
                    "a direct message needs 'participants' with 2-8 persona ids",
                    path, lineno,
                )
                participants = []
            for member in participants:
                identities.require(member, problems, path, lineno, "participants")
        else:
            if channel not in channels:
                known = ", ".join(sorted(channels)[:8]) or "(none)"
                problems.error(
                    f"unknown channel {channel!r} — declared channels: {known}",
                    path, lineno,
                )

        identities.require(obj.get("author"), problems, path, lineno, "author")
        created = wl.parse_ts(obj.get("created_at"), path=path, line=lineno,
                              problems=problems, field_name="created_at")

        text = obj.get("text", "")
        reactions = obj.get("reactions") or []
        if not isinstance(text, str):
            problems.error("text must be a string", path, lineno)
            text = ""
        if not text.strip() and not reactions:
            problems.error(
                "text is empty and there are no reactions — nothing to import",
                path, lineno,
            )

        for ridx, reaction in enumerate(reactions):
            context = f"reactions[{ridx}]"
            if not isinstance(reaction, dict):
                problems.error(f"{context} must be an object", path, lineno)
                continue
            wl.check_keys(reaction, required=REACTION_REQUIRED,
                          optional=REACTION_OPTIONAL, problems=problems,
                          path=path, line=lineno, context=context)
            identities.require(reaction.get("author"), problems, path, lineno,
                               f"{context}.author")
            emoji = reaction.get("emoji", "")
            if isinstance(emoji, str) and (emoji.startswith(":") or emoji.endswith(":")):
                problems.error(
                    f"{context}: emoji {emoji!r} must not include colons", path, lineno
                )

        thread_id = obj.get("thread_id")
        if thread_id is not None:
            if thread_id not in ids:
                problems.error(
                    f"thread_id {thread_id!r} does not match any message id", path, lineno
                )
            elif obj.get("id") is not None:
                problems.error(
                    "a message with a thread_id cannot itself have an id — "
                    "Mattermost has no sub-threads", path, lineno,
                )

        for aidx, attachment in enumerate(obj.get("attachments") or []):
            rel = (attachment or {}).get("path")
            if not rel or not (data_dir / rel).exists():
                problems.error(
                    f"attachments[{aidx}]: file {rel!r} not found under {data_dir}",
                    path, lineno,
                )

        messages.append({
            "lineno": lineno, "id": obj.get("id"), "channel": channel,
            "participants": participants or [], "author": obj.get("author"),
            "created_at": created, "text": text, "thread_id": thread_id,
            "reactions": reactions, "pinned": bool(obj.get("pinned", False)),
            "attachments": obj.get("attachments") or [], "is_dm": is_dm,
        })

    # A reply must live in the same channel as its root.
    by_id = {m["id"]: m for m in messages if m["id"]}
    for msg in messages:
        if msg["thread_id"] and msg["thread_id"] in by_id:
            root = by_id[msg["thread_id"]]
            if root["channel"] != msg["channel"]:
                problems.error(
                    f"reply is in channel {msg['channel']!r} but its root is in "
                    f"{root['channel']!r}", path, msg["lineno"],
                )
    return messages


# =============================================================================
# Conversion to Mattermost's import format
# =============================================================================
def build_import_lines(team: str, channels: dict[str, dict], messages: list[dict],
                       identities: wl.Identities) -> list[dict]:
    """Assemble the ordered, nested objects Mattermost's importer expects.

    Order is mandatory: version, team, channel, user, post, direct_channel,
    direct_post. Users must precede posts because the importer will not create
    a user implicitly from a post's `user` field.
    """
    lines: list[dict] = [{"type": "version", "version": 1}]

    lines.append({"type": "team", "team": {
        "name": team, "display_name": team.title(), "type": "O",
        "description": "", "allow_open_invite": True,
    }})

    for channel in channels.values():
        lines.append({"type": "channel", "channel": {
            "team": team, "name": channel["name"],
            "display_name": channel["display_name"], "type": channel["type"],
            "header": channel["header"], "purpose": channel["purpose"],
        }})

    # Only personas that actually appear, so an unused persona does not become
    # an empty account.
    referenced: set[str] = set()
    for msg in messages:
        referenced.add(msg["author"])
        referenced.update(msg["participants"])
        for reaction in msg["reactions"]:
            referenced.add(reaction["author"])
    for channel in channels.values():
        referenced.update(channel["members"])

    for pid in sorted(referenced):
        persona = identities.get(pid)
        if persona is None:
            continue
        memberships = [
            {"name": c["name"], "roles": "channel_user"}
            for c in channels.values()
            if not c["members"] or pid in c["members"]
        ]
        lines.append({"type": "user", "user": {
            "username": persona.mattermost_username,
            "email": persona.email,
            "nickname": "",
            "first_name": persona.first_name,
            "last_name": persona.last_name,
            "position": persona.role,
            "roles": "system_user system_admin" if persona.is_admin else "system_user",
            "locale": "en",
            "teams": [{
                "name": team,
                "roles": "team_admin team_user" if persona.is_admin else "team_user",
                "channels": memberships,
            }],
        }})

    # Group replies under their root.
    replies_by_root: dict[str, list[dict]] = defaultdict(list)
    for msg in messages:
        if msg["thread_id"]:
            replies_by_root[msg["thread_id"]].append(msg)

    def reaction_objects(msg: dict) -> list[dict]:
        out = []
        for reaction in msg["reactions"]:
            persona = identities.get(reaction["author"])
            when = reaction.get("created_at")
            parsed = wl.parse_ts(when) if when else msg["created_at"]
            out.append({
                "user": persona.mattermost_username if persona else reaction["author"],
                "emoji_name": reaction["emoji"],
                "create_at": wl.to_epoch_ms(parsed or msg["created_at"]),
            })
        return out

    def attachment_objects(msg: dict) -> list[dict]:
        return [{"path": a["path"]} for a in msg["attachments"]]

    regular = [m for m in messages if not m["is_dm"] and not m["thread_id"]]
    for msg in sorted(regular, key=lambda m: m["created_at"]):
        persona = identities.get(msg["author"])
        post: dict[str, Any] = {
            "team": team, "channel": msg["channel"],
            "user": persona.mattermost_username if persona else msg["author"],
            "message": msg["text"],
            "create_at": wl.to_epoch_ms(msg["created_at"]),
            "is_pinned": msg["pinned"],
        }
        if msg["reactions"]:
            post["reactions"] = reaction_objects(msg)
        if msg["attachments"]:
            post["attachments"] = attachment_objects(msg)

        thread = sorted(replies_by_root.get(msg["id"] or "", []),
                        key=lambda m: m["created_at"])
        if thread:
            post["replies"] = []
            for reply in thread:
                rpersona = identities.get(reply["author"])
                robj: dict[str, Any] = {
                    "user": rpersona.mattermost_username if rpersona else reply["author"],
                    "message": reply["text"],
                    "create_at": wl.to_epoch_ms(reply["created_at"]),
                }
                if reply["reactions"]:
                    robj["reactions"] = reaction_objects(reply)
                if reply["attachments"]:
                    robj["attachments"] = attachment_objects(reply)
                post["replies"].append(robj)
        lines.append({"type": "post", "post": post})

    # Direct channels and posts must come last.
    dms = [m for m in messages if m["is_dm"]]
    seen_dm: set[tuple] = set()
    for msg in dms:
        members = tuple(sorted(
            identities.get(p).mattermost_username if identities.get(p) else p
            for p in msg["participants"]
        ))
        if members not in seen_dm:
            seen_dm.add(members)
            lines.append({"type": "direct_channel", "direct_channel": {
                "members": list(members)}})
    for msg in sorted(dms, key=lambda m: m["created_at"]):
        persona = identities.get(msg["author"])
        members = sorted(
            identities.get(p).mattermost_username if identities.get(p) else p
            for p in msg["participants"]
        )
        lines.append({"type": "direct_post", "direct_post": {
            "channel_members": members,
            "user": persona.mattermost_username if persona else msg["author"],
            "message": msg["text"],
            "create_at": wl.to_epoch_ms(msg["created_at"]),
        }})

    return lines


def write_archive(lines: list[dict], messages: list[dict], data_dir: Path,
                  out_path: Path) -> Path:
    """Write import.jsonl plus any attachments into a zip archive."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as archive:
        payload = "\n".join(json.dumps(line, separators=(",", ":")) for line in lines)
        archive.writestr("import.jsonl", payload + "\n")
        for msg in messages:
            for attachment in msg["attachments"]:
                source = data_dir / attachment["path"]
                if source.exists():
                    archive.write(source, f"data/{attachment['path']}")
    return out_path


# =============================================================================
# Running the import
# =============================================================================
def run(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd[:4])}... failed:\n{proc.stderr.strip()}")
    return proc.stdout.strip()


def stage_archive(archive: Path) -> str:
    """Place the archive where the Mattermost server can read it.

    `mmctl import process --bypass-upload` takes a filesystem path, not the
    filestore name that `mmctl import list available` prints — passing the
    latter fails with "file doesn't exist".
    """
    import shutil
    Path(IMPORT_DIR).mkdir(parents=True, exist_ok=True)
    target = Path(IMPORT_DIR) / archive.name
    shutil.copy2(archive, target)
    shutil.chown(target, user="worldsvc", group="worldsvc")
    return str(target)


def _job_id(output: str) -> str | None:
    """Pull the job id out of `mmctl import process` output."""
    match = re.search(r"ID:\s*([a-z0-9]+)", output)
    return match.group(1) if match else None


def wait_for_job(job_id: str, timeout: int = 300, verbose: bool = False) -> str:
    """Poll an import job until it leaves the pending/in_progress states."""
    deadline = time.time() + timeout
    last = ""
    while time.time() < deadline:
        proc = subprocess.run([MMCTL, "--local", "import", "job", "show", job_id],
                              capture_output=True, text=True)
        match = re.search(r"Status:\s*(\S+)", proc.stdout)
        status = match.group(1) if match else "unknown"
        if status != last and verbose:
            wl.info(f"job {job_id}: {status}")
        last = status
        if status in ("success", "error", "canceled"):
            return status
        time.sleep(2)
    return "timeout"


def verify_threads(world: wl.World, team: str, messages: list[dict],
                   identities: wl.Identities) -> tuple[int, int]:
    """Confirm imported replies actually became threads.

    Mattermost has a history of bulk-imported replies not landing as threads
    (mattermost#14959). Checking here means a regression is visible now rather
    than discovered much later.
    """
    expected = defaultdict(int)
    for msg in messages:
        if msg["thread_id"]:
            expected[msg["thread_id"]] += 1
    if not expected:
        return 0, 0

    sess = wl.session(world)
    login = sess.post(world.url("chat", "/api/v4/users/login"), timeout=30,
                      json={"login_id": world.admin_user,
                            "password": world.admin_password})
    if login.status_code != 200:
        raise RuntimeError(f"could not log into Mattermost to verify threads: {login.status_code}")
    token = login.headers.get("Token", "")
    headers = {"Authorization": f"Bearer {token}"}

    found = 0
    channels = {m["channel"] for m in messages if m["thread_id"]}
    for channel_name in channels:
        chan = sess.get(
            world.url("chat", f"/api/v4/teams/name/{team}/channels/name/{channel_name}"),
            headers=headers, timeout=30)
        if chan.status_code != 200:
            continue
        posts = sess.get(
            world.url("chat", f"/api/v4/channels/{chan.json()['id']}/posts"),
            headers=headers, timeout=30)
        if posts.status_code != 200:
            continue
        for post in posts.json().get("posts", {}).values():
            if post.get("root_id"):
                found += 1
    return found, sum(expected.values())


# =============================================================================
# Main
# =============================================================================
def main(argv: list[str] | None = None) -> int:
    parser = wl.base_parser(__doc__)
    parser.add_argument("--keep-archive", type=Path,
                        help="write the import archive here instead of a temp dir")
    parser.add_argument("--no-verify-threads", action="store_true",
                        help="skip the post-import thread check")
    args = parser.parse_args(argv)

    world, identities, problems = wl.setup(args)

    wl.heading("Parsing")
    team, channels = load_channels(args.data_dir / "channels.yaml", world,
                                   identities, problems)
    messages = load_messages(args.data_dir / "messages.jsonl", channels,
                             identities, args.data_dir, problems)
    problems.raise_if_any()

    threads = sum(1 for m in messages if m["thread_id"])
    dms = sum(1 for m in messages if m["is_dm"])
    wl.ok(f"{len(channels)} channel(s), {len(messages)} message(s)")
    wl.ok(f"{threads} threaded reply(ies), {dms} direct message(s)")

    wl.heading("Building import archive")
    lines = build_import_lines(team, channels, messages, identities)
    counts: dict[str, int] = defaultdict(int)
    for line in lines:
        counts[line["type"]] += 1
    wl.ok("objects: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))

    archive_path = args.keep_archive or (
        Path(tempfile.mkdtemp(prefix="sweworld-chat-")) / "world-import.zip"
    )
    write_archive(lines, messages, args.data_dir, archive_path)
    wl.ok(f"archive written to {archive_path}")

    if args.dry_run:
        wl.heading("Dry run")
        wl.dry(f"would run: mmctl --local import process --bypass-upload {archive_path.name}")
        wl.dry("archive is complete and valid; inspect it with:")
        wl.info(f"unzip -p {archive_path} import.jsonl | head")
        wl.summarise(True, [
            f"{len(messages)} message(s) in {len(channels)} channel(s)",
            f"archive: {archive_path}",
        ])
        return 0

    wl.heading("Importing into Mattermost")
    container_path = stage_archive(archive_path)
    output = run([MMCTL, "--local", "import", "process", "--bypass-upload", container_path])
    if args.verbose:
        wl.info(output)

    # The import runs as an asynchronous job. Without waiting for it, the script
    # would report success the moment the job was queued and the thread check
    # below would race an import that has not run yet.
    job_id = _job_id(output)
    if not job_id:
        raise RuntimeError(f"could not parse an import job id from: {output}")
    status = wait_for_job(job_id, verbose=args.verbose)
    if status != "success":
        raise RuntimeError(
            f"import job {job_id} finished with status {status!r} — inspect with: "
            f"docker compose exec mattermost mmctl --local import job show {job_id}"
        )
    wl.ok(f"import job {job_id} completed: {status}")

    actions = [f"{len(messages)} message(s) imported into {len(channels)} channel(s)"]
    if not args.no_verify_threads and threads:
        found, expected = verify_threads(world, team, messages, identities)
        if found >= expected:
            wl.ok(f"thread check: {found}/{expected} replies are threaded")
        else:
            wl.warn(
                f"thread check: only {found}/{expected} replies came back threaded — "
                "see mattermost#14959"
            )
        actions.append(f"threads verified: {found}/{expected}")

    actions.append(f"browse at {world.url('chat')}")
    wl.summarise(False, actions)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"\n\033[31mfailed\033[0m  {exc}", file=sys.stderr)
        raise SystemExit(1)
