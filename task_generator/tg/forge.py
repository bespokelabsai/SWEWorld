"""The forgeries a grading suite must score zero, built from a real oracle run.

Every one of these is a finding Argus filed against a shipped task, turned into
something the bracket runs before a task can be emitted rather than something a
reviewer finds after it is live:

  replay   an oracle run's observations and artifact directories, captured
           under one seed and written back by an import-time hook into an
           untouched tree graded under another. g1 scored 1.0 this way from
           pristine `main` plus one hook; g7 did too; g4 0.875, and 1.0 with a
           stub module holding only the constants.
  true     the same capture with every boolean set to True. A judge that
           asserts worker-reported booleans for fixed inputs passes these: g7's
           r2.scope and r2.failure_behavior did, from 1.2 KB of `true`.

The hook implements nothing. It patches `json.dump` at import, so the worker's
own write of observations.json is replaced whatever the probe does afterwards
(`os._exit` included), and it swaps the captured artifact directories in at
that moment. A suite passes this gate only if the judge derives what it expects
from the run's own seed and reads what it grades itself.
"""
from __future__ import annotations

import base64
import io
import json
import pathlib
import tarfile

KINDS = ("replay", "true")

HOOK = '''

# --- tg forge: replays captured observations; implements nothing ------------
import base64 as _b64, io as _io, json as _json, os as _os, shutil as _sh, sys as _sys, tarfile as _tf
_OBS = "__OBS__"
_TAR = "__TAR__"
_real_dump = _json.dump
def _tg_forge_dump(obj, fp, *a, **k):
    try:
        if str(getattr(fp, "name", "")).endswith("observations.json"):
            if _TAR and len(_sys.argv) > 3 and _os.path.isdir(_sys.argv[3]):
                _art = _sys.argv[3]
                for _name in _os.listdir(_art):
                    _p = _os.path.join(_art, _name)
                    _sh.rmtree(_p, ignore_errors=True) if _os.path.isdir(_p) else _os.unlink(_p)
                with _tf.open(fileobj=_io.BytesIO(_b64.b64decode(_TAR))) as _t:
                    _t.extractall(_art)
            fp.write(_b64.b64decode(_OBS).decode())
            return None
    except Exception:
        pass
    return _real_dump(obj, fp, *a, **k)
_json.dump = _tg_forge_dump
'''


def _all_true(node):
    if isinstance(node, bool):
        return True
    if isinstance(node, dict):
        return {k: _all_true(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_all_true(v) for v in node]
    return node


def hook(kind: str, capture: pathlib.Path) -> str:
    """The text appended to the tree's `bespokelabs/curator/__init__.py`."""
    obs = (capture / "observations.json").read_bytes()
    if kind == "true":
        obs = json.dumps(_all_true(json.loads(obs))).encode()
    elif kind != "replay":
        raise ValueError(f"unknown forge {kind!r}")
    tar = b""
    art = capture / "art"
    if art.is_dir():
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w") as t:
            for child in sorted(art.iterdir()):
                t.add(child, arcname=child.name)
        tar = buf.getvalue()
    return (HOOK.replace("__OBS__", base64.b64encode(obs).decode())
                .replace("__TAR__", base64.b64encode(tar).decode()))
