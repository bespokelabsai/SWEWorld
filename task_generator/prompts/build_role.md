You are implementing a change to `bespokelabs/curator`, a Python library.

Your checkout is your working directory. Edit it in place, under `src/` only.
Do not create tests. Do not create notes, plans, or summary files. When you are
done, the tree is your answer.

## What to build

{{spec}}

## How to work

- The library is src-layout: `src/bespokelabs/curator/`.
- Read the surrounding code before you change it. Match its style, its typing
  conventions, and its docstring conventions.
- `python3` here **cannot import curator** — its dependencies are not installed
  on this machine. Do not spend turns fighting that. Instead, to run anything
  against your tree, use:

  ```
  {{exec_cmd}} --cmd 'python3 -c "from bespokelabs.curator... ; print(...)"'
  {{exec_cmd}} --cmd 'python3 check.py'      # a scratch script in your tree
  ```

  That copies your tree into a container where curator's dependencies exist and
  runs the command with `PYTHONPATH=<your tree>/src`. It is read-only with
  respect to your tree, it takes a few seconds, and you should use it — any exact
  number in the text above is worth confirming rather than trusting.
- Keep the change tight. Only what the specification above asks for.

{{role_instruction}}
