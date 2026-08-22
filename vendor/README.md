# `vendor/` — frozen third-party source

Snapshots of code the world imports, committed here so an image build needs no
network and produces the same bytes every time.

## `curator-461b4170b966.tar.gz`

`bespokelabs/curator`, the service the agent deploys.

| | |
|---|---|
| Upstream | `https://github.com/bespokelabsai/curator` |
| Commit | `461b4170b96690873a152e829185a920a941b960` |
| Committed | 2026-07-13 |
| Vendored | 2026-08-17 |
| sha256 | `452e3ae76b92cbe176100366230007db38e8070316150c01f903915ab7dd5230` |

Contains no `.git`. The tie to GitHub was severed once, here, rather than on
every build.

**Two files are deliberately absent:** `docs/curator-viewer.gif` (16M) and
`docs/curator-cli.gif` (12M). They are demo screencasts — 28M of the original
35M — and nothing inside an offline world can play them. The README links the
CLI one by absolute GitHub URL rather than a relative path, so no local
reference breaks. Dropping them is what makes this 2.8M instead of 31M, in a
git repository that cannot easily shed a blob once pushed.

## `actions-checkout-v4-11d5960a3267.tar.gz`

`actions/checkout`, resolved locally because `DEFAULT_ACTIONS_URL = self` makes
Gitea serve actions from its own instance.

| | |
|---|---|
| Upstream | `https://github.com/actions/checkout` |
| Ref | `v4` |
| Commit | `11d5960a326750d5838078e36cf38b85af677262` |
| Vendored | 2026-08-17 |
| sha256 | `1109431836ce0341bf635d5b59768f7a4dc14e83b5618d09775ed77cf2d0abdf` |

**Only the `v4` tree**, not the action's history: `world/ci-templates/python.yml`
names `actions/checkout@v4` and nothing else, and 61 branches plus 68 tags of an
action's development is 16M for a repository that serves one ref. The build
commits this tree fresh and tags it `v4`.

A workflow naming any other ref — `@v3`, `@main` — fails at resolution. That is
a loud CI error rather than a silent wrong answer, and the fix is to vendor the
extra ref.

## Why a tarball and not a clone

Both of these used to be cloned from GitHub during the image build —
`22-curator.sh` with `--depth 1`, `20-gitea.sh` with `--mirror`. That had three
problems, in increasing order of seriousness:

1. They needed the network, inside a build layer.
2. They re-ran far more often than it looked like they would. Both clones sit
   below `COPY world/ /world-src/`, so editing an nginx config or the
   credentials page invalidated them.
3. **They were not pinned.** Every other component in the Dockerfile is fixed by
   an `ARG` — `BOOKSTACK_VERSION`, `GITEA_VERSION`, `MATTERMOST_VERSION`. These
   two tracked whatever the upstream default branch happened to be, so two
   builds a week apart imported different source without saying so.

(3) is the one that matters, and it matters most for curator. The generated
history in `data/commits.jsonl` has to land exactly on that tree; if the tree
moves underneath it, the history stops matching the repository and the failure
looks like a bug in the generator.

## Refreshing it

Deliberately manual. Bumping the snapshot means the end state of the world
changes, and any generated history written against the old tree has to be
regenerated with it.

```bash
git clone --depth 1 https://github.com/bespokelabsai/curator.git /tmp/curator
SHA=$(git -C /tmp/curator rev-parse HEAD)
rm -rf /tmp/curator/.git /tmp/curator/docs/*.gif
tar -C /tmp/curator --sort=name --owner=0 --group=0 --numeric-owner \
    --mtime="@0" --format=gnu -cf - . | gzip -n -9 \
    > vendor/curator-${SHA:0:12}.tar.gz
git rm vendor/curator-<old>.tar.gz
```

The flags are what make the tarball byte-identical when rebuilt from the same
source — without them the mtimes and gzip header change every run and the blob
looks modified when nothing is.

Then update `CURATOR_SNAPSHOT` in `world/Dockerfile` and this file.
