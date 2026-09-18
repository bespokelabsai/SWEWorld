"""XXH64 spelled out in the stdlib, for a judge that must RE-DERIVE the digest.

`judge.py` runs under `python3 -I` with an empty PYTHONPATH on root's system
interpreter, so `xxhash` is not importable there and cannot be made so. For
three versions the judge therefore argued about the digest from proxies — its
shape, an AST hit on a call named `xxh64`, an import ban on other hash
libraries — and the TB3 "Verifiable" review failed v7 for precisely that: "An
implementation could make an unused xxh64 call, then generate the digest with a
custom deterministic hash while still satisfying every check. Likewise, the
verifier never establishes that RUN_IDENTITY_VERSION is included in the hashed
serialization." No proxy can answer either half. Re-hashing the bytes the
module actually fed to xxh64 answers both, so the primitive lives here.

This is the published XXH64 (Yann Collet, xxHash r39+): the four-accumulator
32-byte stripe loop, the 8/4/1-byte tail, the final avalanche, with the seed as
a parameter because `xxhash.xxh64(data, seed)` takes one. It was checked against
`xxhash.xxh64` in the world's curator venv over the empty string, one-byte and
short inputs, the 31/32/33-byte boundaries of the stripe loop, inputs of 64 and
1000 bytes, non-ASCII UTF-8 and non-zero seeds — the comparison is in this
task's round-3 report. `KNOWN_VECTORS` keeps a handful of those answers so a
judge run proves the reference is intact before it decides anything with it;
`_get_function_hash(None)` returning `ef46db3751d8e999` is the same agreement,
asserted against the submission's own runtime on every run.
"""
from __future__ import annotations

_MASK = (1 << 64) - 1

_P1 = 0x9E3779B185EBCA87
_P2 = 0xC2B2AE3D27D4EB4F
_P3 = 0x165667B19E3779F9
_P4 = 0x85EBCA77C2B2AE63
_P5 = 0x27D4EB2F165667C5

# Input -> xxh64 hexdigest at seed 0, and one at a non-zero seed. Read off
# `xxhash.xxh64` in the curator venv; the boundary cases are the ones a wrong
# transcription of the stripe loop gets wrong while the empty string still works.
KNOWN_VECTORS = (
    (b"", 0, "ef46db3751d8e999"),
    (b"a", 0, "d24ec4f1a98c6e5b"),
    (b"abc", 0, "44bc2cf5ad770999"),
    (b"0123456789abcdef", 0, "5c5b90c34e376d0b"),
    (b"0123456789abcdef0123456789abcde", 0, "1fdfc63febacfde7"),
    (b"0123456789abcdef0123456789abcdef", 0, "642a94958e71e6c5"),
    (b"0123456789abcdef0123456789abcdefx", 0, "3903d2645ffea35f"),
    (b"abc", 42, "13c1d910702770e6"),
)


def _rotl(value: int, bits: int) -> int:
    return ((value << bits) | (value >> (64 - bits))) & _MASK


def _round(acc: int, lane: int) -> int:
    acc = (acc + lane * _P2) & _MASK
    acc = _rotl(acc, 31)
    return (acc * _P1) & _MASK


def _merge_round(acc: int, lane: int) -> int:
    acc ^= _round(0, lane)
    return (acc * _P1 + _P4) & _MASK


def hexdigest(data: bytes, seed: int = 0) -> str:
    """The xxh64 hexdigest of `data`, as `xxhash.xxh64(data, seed).hexdigest()`."""
    data = bytes(data)
    seed &= _MASK
    total = len(data)
    i = 0

    if total >= 32:
        v1 = (seed + _P1 + _P2) & _MASK
        v2 = (seed + _P2) & _MASK
        v3 = seed
        v4 = (seed - _P1) & _MASK
        while total - i >= 32:
            v1 = _round(v1, int.from_bytes(data[i:i + 8], "little"))
            v2 = _round(v2, int.from_bytes(data[i + 8:i + 16], "little"))
            v3 = _round(v3, int.from_bytes(data[i + 16:i + 24], "little"))
            v4 = _round(v4, int.from_bytes(data[i + 24:i + 32], "little"))
            i += 32
        acc = (_rotl(v1, 1) + _rotl(v2, 7) + _rotl(v3, 12) + _rotl(v4, 18)) & _MASK
        for lane in (v1, v2, v3, v4):
            acc = _merge_round(acc, lane)
    else:
        acc = (seed + _P5) & _MASK

    acc = (acc + total) & _MASK

    while total - i >= 8:
        acc ^= _round(0, int.from_bytes(data[i:i + 8], "little"))
        acc = (_rotl(acc, 27) * _P1 + _P4) & _MASK
        i += 8
    if total - i >= 4:
        acc ^= (int.from_bytes(data[i:i + 4], "little") * _P1) & _MASK
        acc = (_rotl(acc, 23) * _P2 + _P3) & _MASK
        i += 4
    while i < total:
        acc ^= (data[i] * _P5) & _MASK
        acc = (_rotl(acc, 11) * _P1) & _MASK
        i += 1

    acc ^= acc >> 33
    acc = (acc * _P2) & _MASK
    acc ^= acc >> 29
    acc = (acc * _P3) & _MASK
    acc ^= acc >> 32
    return format(acc, "016x")


def self_check() -> str:
    """"" if this reference still agrees with `KNOWN_VECTORS`, else what differs."""
    for data, seed, want in KNOWN_VECTORS:
        got = hexdigest(data, seed)
        if got != want:
            return f"xxh64_ref is broken: {data!r} seed {seed} hashes to {got}, not {want}"
    return ""
