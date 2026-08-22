#!/usr/bin/env python3
"""Render the two grounding files into one browsable HTML report.

`engineering_grounding.json` and `engineering_episodes.json` are the contract a
later generation step consumes, but they are also the thing a human has to
*trust* — and 4.5MB of JSON is not reviewable. This projects both files down to
what a reader needs to judge them, and inlines it into `report_template.html`.

The report is a function of the two JSON files, so it regenerates with them:

    python3 data_gen/analyze_repository.py
    python3 data_gen/build_episodes.py
    python3 data_gen/make_report.py

Nothing is computed here that is not already in those files. If a number in the
report looks wrong, it is wrong in the data, which is the point.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import repolib as rl  # noqa: E402

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "report_template.html"
DEFAULT_OUT = rl.DEFAULT_BUILD_DIR / "report.html"
EPISODE_FILE_LIMIT = 12          # files listed per episode in the explorer
EPISODE_SYMBOL_LIMIT = 8


def project_grounding(g: dict) -> dict:
    src = g["source"]
    cfg = g["configuration"]
    ci = g["ci_cd"]
    tests = g["test_architecture"]
    docs = g["documentation"]
    deps = g["dependencies"]
    hot = g["change_hotspots"]

    workflow = ci["workflows"][0] if ci["workflows"] else None
    job_steps = []
    if workflow:
        for job_id, job in workflow["jobs"].items():
            for step in job["steps"]:
                job_steps.append({
                    "job": job_id,
                    "name": step["name"] or step["uses"] or (step["run"] or "")[:60],
                    "uses": step["uses"],
                    "run": step["run"],
                })

    return {
        "layout": g.get("layout"),
        "source": {
            "remote": src["remote"],
            "head": src["head_commit"],
            "commits": src["commit_count"],
            "merges": src["merge_commit_count"],
            "files": src["tracked_files"],
            "first": (src["first_commit"] or {}).get("date"),
            "last": (src["last_commit"] or {}).get("date"),
            "tags": len(src["tags"]),
            "latest_tag": src["tags"][-1]["name"] if src["tags"] else None,
            "by_month": src["commits_by_month"],
        },
        "generated_at": g["generated_at"],
        "headline": {
            "capability_areas": len(g["capability_areas"]),
            "subsystems": sum(1 for s in g["subsystems"] if s["role"] == "src"),
            "extension_points": len(g["interfaces"]["extension_points"]),
            "classes": g["interfaces"]["class_count"],
            "test_functions": tests["test_function_count"],
            "test_ratio": tests["test_to_source_ratio"],
            "contributors": sum(1 for c in g["contributors"] if not c["is_bot"]),
            "bots": sum(1 for c in g["contributors"] if c["is_bot"]),
            "source_lines": tests["source_lines"],
            "modules": deps["internal"]["module_count"],
            "edges": deps["internal"]["edge_count"],
            "runtime_deps": len(cfg["runtime_dependencies"]),
        },
        "capability_areas": [
            {
                "key": a["key"], "name": a["name"], "purpose": a["purpose"],
                "loc": a["lines_of_code"], "commits": a["change_volume"]["commits"],
                "recent": a["change_volume"]["recency_weighted"],
                "last_touched": a["change_volume"]["last_touched"],
                "owners": a["owners"][:4], "bus_factor": a["bus_factor"],
                "exports": a["public_exports"],
                "extension_points": a["extension_points"],
                "tests": a["tests"]["file_count"],
                "work_mix": a["work_type_mix"],
                "paths": a["paths"][:6],
            }
            for a in g.get("capability_areas_measured", g["capability_areas"])
        ],
        "interfaces": {
            "public_api": g["interfaces"]["public_api"],
            "counts": {
                "classes": g["interfaces"]["class_count"],
                "abstract": g["interfaces"]["abstract_class_count"],
                "protocols": g["interfaces"]["protocol_count"],
                "models": len(g["interfaces"]["pydantic_models"]),
                "factories": len(g["interfaces"]["factories"]),
            },
            "points": [
                {"name": p["name"], "path": p["path"], "subsystem": p["subsystem"],
                 "doc": p["docstring"], "abstract": p["abstract_methods"],
                 "subclasses": p["subclasses"], "protocol": p["is_protocol"],
                 "is_abstract": p["is_abstract"]}
                for p in g["interfaces"]["extension_points"]
            ],
        },
        "tests": {
            "directories": tests["directories"],
            "declared_markers": tests["declared_markers"],
            "used_markers": tests["used_markers"],
            "unused_markers": tests["declared_but_unused_markers"],
            "fixtures": tests["conftest_fixtures"],
            "cassettes": tests["vcr_cassette_count"],
            "cassette_dirs": tests["cassette_backends"],
            "covered": tests["subsystems_covered"],
            "source_lines": tests["source_lines"],
            "test_lines": tests["test_lines"],
            "ratio": tests["test_to_source_ratio"],
            "functions": tests["test_function_count"],
        },
        "config": {
            "package": cfg["package_name"], "version": cfg["version"],
            "python": cfg["python_requires"], "backend": cfg["build_backend"],
            "entry_points": cfg["entry_points"], "extras": cfg["extras"],
            "pinned": cfg["pinned_dependencies"], "optional": cfg["optional_dependencies"],
            "runtime": [{"name": d["name"], "constraint": d["constraint"],
                         "pinned": d["pinned"], "optional": d["optional"]}
                        for d in cfg["runtime_dependencies"]],
            "dev_count": len(cfg["dependency_groups"].get("dev", [])),
            "targets": [t["name"] for t in cfg["makefile_targets"]],
            "hooks": cfg["pre_commit_hooks"],
            "lockfile": cfg["lockfile"], "publish_script": cfg["publish_script"],
            "containerised": cfg["containerised"],
        },
        "ci": {
            "provider": ci["provider"],
            "workflow": workflow["name"] if workflow else None,
            "path": workflow["path"] if workflow else None,
            "triggers": workflow["triggers"] if workflow else {},
            "gates": workflow["gates"] if workflow else {},
            "steps": job_steps,
            "publishes": ci["publishes_from_ci"],
            "manual_release": ci["release_is_manual"],
        },
        "deps": {
            "most_depended": deps["internal"]["most_depended_on"][:12],
            "most_dependent": deps["internal"]["most_dependent"][:12],
            "cycles": deps["internal"]["cycles"],
            "subsystem_edges": deps["internal"]["subsystem_edges"][:14],
            "external": deps["external"]["imported"][:14],
            "declared": deps["external"]["declared"],
        },
        "docs": {
            "sections": [s for s in docs["readme"]["sections"] if s["level"] <= 2][:24],
            "bytes": docs["readme"]["bytes"],
            "files": [f for f in docs["files"] if f["language"] in ("markdown", "text")],
            "conventions": docs["stated_conventions"],
            "adherence": docs["observed_adherence"],
        },
        "hotspots": {
            "note": hot["note"],
            "files": hot["top_files"][:18],
            "recent": hot["top_files_recent"][:18],
            "subsystems": hot["by_subsystem"][:18],
            "coupling": hot["co_change_coupling"][:12],
            "per_year": hot["by_subsystem_per_year"],
        },
        "people": [
            {"id": c["id"], "name": c["display_name"], "login": c["github_login"],
             "bot": c["is_bot"], "commits": c["commits"], "aliases": c["aliases"],
             "first": c["first_commit"], "last": c["last_commit"],
             "months": c["active_months"], "subsystems": c["subsystems"],
             "roles": c["file_roles"], "work": c["work_types"]}
            for c in g["contributors"]
        ],
        "roles": g["roles"],
        "ownership": g["ownership"],
        "work_types": g["work_types"],
        "org": project_organization(g),
    }


def project_organization(g: dict) -> dict | None:
    """The interpreted sections, or None when the file was built with --no-enrich."""
    if "eras" not in g:
        return None
    analysis = g.get("analysis", {})
    return {
        "analysis": {
            "model": analysis.get("model"),
            "effort": analysis.get("effort"),
            "generated_at": analysis.get("generated_at"),
            "citations_checked": analysis.get("citation_check", {}).get("citations_checked"),
            "citation_problems": len(analysis.get("citation_check", {}).get("problems", [])),
            "interpreted_keys": analysis.get("interpreted_keys", []),
            "usage": analysis.get("usage", {}),
        },
        "eras": g["eras"],
        "areas": g["capability_areas"],
        "people": g["people"],
        "process": g["process"],
        "collaboration": g["collaboration"],
        "timeline": g["timeline"],
    }


def project_episodes(e: dict) -> dict:
    stats = e["stats"]
    episodes = []
    per_month: Counter[str] = Counter()
    per_month_type: dict[str, Counter] = defaultdict(Counter)
    reviewer_counts: Counter[str] = Counter()
    author_counts: Counter[str] = Counter()

    for ep in e["episodes"]:
        pr = ep["provenance"]["pull_request"]
        m = ep["metrics"]
        when = (ep["timeline"]["merged_at"] or ep["timeline"]["first_commit_at"] or "")[:7]
        if when:
            per_month[when] += 1
            per_month_type[when][ep["change_type"]["primary"]] += 1
        for reviewer in ep["people"]["reviewers"]:
            reviewer_counts[reviewer["login"]] += 1
        if ep["people"]["author"]:
            author_counts[ep["people"]["author"]] += 1

        symbols = {"added": 0, "removed": 0, "modified": 0}
        named: list[str] = []
        for f in ep["files"]:
            if not f.get("symbols"):
                continue
            for key in symbols:
                symbols[key] += len(f["symbols"][key])
                if len(named) < EPISODE_SYMBOL_LIMIT:
                    named += [f"{key[0].upper()} {name}" for name in f["symbols"][key][:2]]

        episodes.append({
            "id": ep["id"],
            "title": ep["title"],
            "objective": (ep["objective"] or "")[:400],
            "type": ep["change_type"]["primary"],
            "confidence": ep["change_type"]["confidence"],
            "why": [f'{v["rule"]}: {v["detail"]}' for v in ep["change_type"]["evidence"][:4]],
            "style": ep["provenance"]["merge_style"],
            "rule": ep["provenance"]["grouping_rule"],
            "branch": ep["provenance"]["branch"],
            "pr": pr["number"] if pr else None,
            "pr_url": pr["url"] if pr else None,
            "issues": [{"n": i["number"], "title": i["title"], "link": i["link"]}
                       for i in ep["provenance"]["issues"]],
            "when": ep["timeline"]["merged_at"] or ep["timeline"]["first_commit_at"],
            "commits": m["commits_in_clone"],
            "commits_new": m["commits_first_seen_here"],
            "commits_branch": m["commits_on_branch"],
            "files": m["files_changed"],
            "add": m["lines_added"],
            "del": m["lines_deleted"],
            "cycles": m["review_cycles"],
            "approvals": m["approvals"],
            "changes_requested": m["changes_requested"],
            "t_open_merge": m["time_pr_open_to_merge_s"],
            "t_issue_pr": m["time_issue_to_pr_s"],
            "t_first_review": m["time_pr_open_to_first_review_s"],
            "author": ep["people"]["author"],
            "login": ep["people"]["author_login"],
            "reviewers": [{"login": r["login"], "states": r["states"], "n": r["reviews"]}
                          for r in ep["people"]["reviewers"]],
            "subsystems": m["file_distribution"]["by_subsystem"],
            "roles": m["file_distribution"]["by_role"],
            "before": ep["state"]["before"]["commit"],
            "after": ep["state"]["after"]["commit"],
            "deps": [{"id": d["episode_id"], "kind": d["kind"], "why": d["evidence"]}
                     for d in ep["dependencies"]],
            "contains": len(ep["provenance"]["contains_episodes"]),
            "inside": len(ep["provenance"]["contained_by_episodes"]),
            "gaps": ep["provenance_gaps"],
            "symbols": symbols,
            "symbol_names": named[:EPISODE_SYMBOL_LIMIT],
            "top_files": [
                {"p": f["path"], "s": f["status"], "a": f["lines_added"],
                 "d": f["lines_deleted"], "sym": f.get("symbols")}
                for f in sorted(ep["files"],
                                key=lambda f: -(f["lines_added"] + f["lines_deleted"]))
            ][:EPISODE_FILE_LIMIT],
            "sources": [{"sha": c["sha"][:9], "subject": c["subject"][:110],
                         "author": c["author"], "new": c["first_in_episode"]}
                        for c in ep["provenance"]["source_commits"][:14]],
            "source_total": len(ep["provenance"]["source_commits"]),
        })

    # A month with no episodes must still occupy a column, or the axis silently
    # compresses the five-month gap in 2025 and the timeline lies about pace.
    months = sorted(per_month)
    filled: dict[str, int] = {}
    if months:
        year, month = (int(x) for x in months[0].split("-"))
        end_year, end_month = (int(x) for x in months[-1].split("-"))
        while (year, month) <= (end_year, end_month):
            key = f"{year:04d}-{month:02d}"
            filled[key] = per_month.get(key, 0)
            year, month = (year + 1, 1) if month == 12 else (year, month + 1)

    return {
        "generated_at": e["generated_at"],
        "source": e["source"],
        "stats": stats,
        "per_month": filled,
        "per_month_type": {k: dict(v) for k, v in sorted(per_month_type.items())},
        "reviewers": reviewer_counts.most_common(12),
        "authors": author_counts.most_common(12),
        "episodes": episodes,
    }


SAMPLE_TRIPLES = 15
TRIPLE_PATCH_CAP = 5000


def project_history(doc: dict, blob_dir: Path) -> dict:
    """A view of the Stage 0 record — including real before/patch/after triples.

    The record is 47MB and the blob store 62MB, so this is deliberately a
    sample: enough to see that actual code was retained rather than described.
    """
    commits = doc["commits"]
    changes = [(c, f) for c in commits for f in c["files"]]
    noise_ext: Counter[str] = Counter()
    for _, f in changes:
        if f["noise"]:
            noise_ext[Path(f["path"]).suffix or Path(f["path"]).name] += 1

    # Pick modified Python files with a patch big enough to be interesting and
    # small enough to read, spread across the history rather than clustered.
    candidates = [
        (c, f) for c, f in changes
        if f.get("patch") and not f.get("patch_truncated") and f["status"] == "M"
        and f["path"].endswith(".py") and 300 < len(f["patch"]) < TRIPLE_PATCH_CAP
        and f["blob_before"] and f["blob_after"]
    ]
    candidates.sort(key=lambda cf: cf[0]["author"]["date"])
    step = max(1, len(candidates) // SAMPLE_TRIPLES)
    triples = []
    for c, f in candidates[::step][:SAMPLE_TRIPLES]:
        before = blob_dir / f["blob_before"]
        after = blob_dir / f["blob_after"]
        triples.append({
            "path": f["path"],
            "commit": c["sha"][:12],
            "subject": c["subject"][:120],
            "author": c["author"]["person"],
            "date": c["author"]["date"][:10],
            "patch": f["patch"],
            "added": f["lines_added"], "deleted": f["lines_deleted"],
            "blob_before": f["blob_before"][:12], "blob_after": f["blob_after"][:12],
            "bytes_before": before.stat().st_size if before.exists() else None,
            "bytes_after": after.stat().st_size if after.exists() else None,
        })

    per_year: Counter[str] = Counter()
    for c in commits:
        per_year[c["author"]["date"][:4]] += 1

    return {
        "generated_at": doc["generated_at"],
        "repository": doc["repository"],
        "totals": doc["totals"],
        "retention": doc["retention"],
        "commits_per_year": dict(sorted(per_year.items())),
        "dag": {
            "all_refs": len(commits),
            "on_head": len(doc["refs"]["head_sequence"]),
            "side_branch_only": len(commits) - len(doc["refs"]["head_sequence"]),
            "first_parent": len(doc["refs"]["first_parent_sequence"]),
            "merges": doc["totals"]["merges"],
        },
        "branches": doc["branch_topology"][:12],
        "branch_count": len(doc["refs"]["branches"]),
        "tags": doc["refs"]["tags"][-12:],
        "tag_count": len(doc["refs"]["tags"]),
        "releases": [{"name": r.get("name"), "tag": r.get("tag_name"),
                      "published": (r.get("published_at") or "")[:10],
                      "prerelease": r.get("prerelease")}
                     for r in doc["github"]["releases"]][:12],
        "labels": [{"name": l.get("name"), "description": l.get("description")}
                   for l in doc["github"]["labels"]],
        "patterns": doc["patterns"],
        "noise_excluded": dict(noise_ext.most_common(10)),
        "blob_languages": dict(Counter(
            b["language"] for b in doc["blob_index"].values()).most_common(10)),
        "triples": triples,
    }


def main() -> None:
    parser = rl.base_parser(__doc__.split("\n\n")[0])
    parser.add_argument("--grounding", type=Path,
                        default=rl.DEFAULT_BUILD_DIR / "engineering_grounding.json")
    parser.add_argument("--episodes", type=Path,
                        default=rl.DEFAULT_BUILD_DIR / "engineering_episodes.json")
    parser.add_argument("--history", type=Path,
                        default=rl.DEFAULT_BUILD_DIR / "repository_history.json")
    parser.add_argument("--blobs-dir", type=Path,
                        default=rl.DEFAULT_BUILD_DIR / "repository_blobs")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    for path in (args.grounding, args.episodes, TEMPLATE):
        if not path.exists():
            rl.fail(f"{path} does not exist — run the two build scripts first")

    rl.heading("Projecting")
    grounding = project_grounding(json.loads(args.grounding.read_text()))
    episodes = project_episodes(json.loads(args.episodes.read_text()))
    history = None
    if args.history.exists():
        history = project_history(
            json.loads(args.history.read_text(encoding="utf-8")), args.blobs_dir)
        rl.ok(f"stage 0 record: {history['totals']['commits']} commits, "
              f"{len(history['triples'])} before/patch/after samples")
    else:
        rl.warn(f"{args.history} not found — the raw-record tab will be omitted")

    payload = {"grounding": grounding, "episodes": episodes, "history": history}
    blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    rl.ok(f"{len(grounding['capability_areas'])} capability areas, "
          f"{len(episodes['episodes'])} episodes -> {rl.human_bytes(len(blob.encode()))} of data")

    # </script> inside a JSON string would close the host <script> tag early.
    blob = blob.replace("</", "<\\/")
    html = TEMPLATE.read_text(encoding="utf-8").replace("__REPORT_DATA__", blob)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html, encoding="utf-8")

    rl.heading("Wrote")
    rl.ok(f"{args.out} ({rl.human_bytes(len(html.encode()))})")


if __name__ == "__main__":
    main()
