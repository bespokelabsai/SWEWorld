# g13-raft-document-set — blind arm of g13
FROM apex_arena:base

# curator's dependency closure WITHOUT curator. `src/bespokelabs/__init__.py` is a
# regular package, so an installed copy would shadow the agent's tree and every
# test would grade the vendored snapshot instead of the submission. Installing the
# wheel and then removing only the package is how the closure is obtained.
# Done at build time because the eval container has no network.
RUN pip install --no-cache-dir "bespokelabs-curator==0.1.29" \
 && pip uninstall -y bespokelabs-curator \
 && pip install --no-cache-dir pytest pytest-timeout

# Pillow, forced. The base image carries Debian's python3-pil 9.0.1 at
# /usr/lib/python3/dist-packages WITHOUT its `_imaging` C extension, and pip
# reports "Requirement already satisfied: Pillow in /usr/lib/python3/dist-packages"
# and installs nothing -- so curator's own dependency install leaves the broken copy
# in place. `curator/types/prompt.py` imports PIL, so `bespokelabs.curator` then
# fails PART WAY through its __init__ and never lands in sys.modules, and the next
# lookup raises `KeyError: 'bespokelabs.curator'` from the import machinery. That
# KeyError is what the grader sees; the ImportError underneath it is invisible.
RUN pip install --no-cache-dir --ignore-installed Pillow

# Fail the BUILD, not the grade. Without this the image ships happily and every
# fact scores 0 for a reason no one can read from the result -- which cost five
# hosted round trips before the ImportError above was found.
RUN python3 -c "import datasets, pydantic, PIL, PIL._imaging, pytest; print('deps ok')"

# The same switch CONFTEST and GRADER already set, extended to the AGENT's shell.
#
# Both of those set `CURATOR_DISABLE_RICH_DISPLAY` before curator is imported,
# because `curator/log.py` reads it at import time -- but only for the grading
# side. The agent inherited nothing, so constructing a status tracker started a
# rich/tqdm live display in a non-TTY container and wedged its shell: it sends
# `echo ok`, `pwd`, `ls`, gets nothing back for the rest of the rollout, and then
# reports the task complete unverified. Three of twelve blind rollouts of g7 died
# that way, both of its opus runs among them -- and an agent cannot avoid it when
# the thing it is implementing IS a tracker.
#
# It conveys nothing about any requirement and every arm carries it identically,
# so it cannot advantage one reading of a ticket over another.
ENV CURATOR_DISABLE_RICH_DISPLAY=1

# The tree the agent works in.
COPY ./tests/curator-src.tar.gz /tmp/curator-src.tar.gz
RUN mkdir -p /workdir/curator \
 && tar xzf /tmp/curator-src.tar.gz -C /workdir/curator \
 && rm /tmp/curator-src.tar.gz \
 && chown -R model:model /workdir/curator

# The submission tree must import against those deps before anything is graded.
RUN PYTHONPATH=/workdir/curator/src python3 -c     "import bespokelabs.curator; print('curator imports from the tree')"

# ------------ DONOT CHANGE --------------
COPY ./tests/ /tests/
COPY ./solution.sh /tests/
COPY ./grader.py /tests/
COPY ./data /workdir/data
RUN chown -R model:model /workdir/data && chmod -R 700 /workdir/data
# No chown/chmod of /tests here. apex_arena already creates it root-owned and
# 0700 — that is what keeps the suite away from the agent — and re-applying it
# from the task locked solution.sh out of the files beside it.
