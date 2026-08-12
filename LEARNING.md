# Learning notes

How Forge actually decides whether your work is right, and why it's built
the way it is.

## 1. The core idea: separate "does it work" from "is it good"

Forge deliberately keeps two things apart that a lot of AI coding tools
blur together:

- **Did you actually solve the problem?** Decided by a deterministic
  system - real code execution, real assertions, real pattern checks. No
  AI involved. This is `checker.py`.
- **Are you stuck and need a nudge?** That's the one place AI shows up -
  and even there, `mentor.py`'s system prompt explicitly forbids it from
  writing the fix for you.

This split matters because an AI grading its own hints would be grading
its own homework. Keeping the verdict entirely mechanical means you can
trust a "passed" the same way you'd trust a compiler succeeding - it's not
an opinion.

## 2. How the code-exercise checker works

Look at `checker.py`'s `_check_python_exec()`. The whole mechanism is:

```python
script = f"{submitted_code}\n\n{step.harness_code}\n\nprint('ALL_PASSED')\n"
```

That's it. It glues your submitted code together with a harness of plain
`assert` statements (written per-exercise in `curriculum.py`), runs the
combined file as a real subprocess, and checks whether it finished with
exit code 0. If an `assert` fails, Python raises `AssertionError` with
whatever message the exercise author wrote, prints a traceback to stderr,
and exits non-zero - `checker.py` just grabs the last line of that
traceback and hands it back as the failure message.

**This is not a novel technique - it's what `pytest` does under the hood,**
just without the framework. Understanding this file is a genuine window
into how every automated code-grading system (LeetCode, Codewars, CI test
runners) works at its core: run the code for real, assert on the result,
report what broke.

It runs as a real subprocess (`subprocess.run([sys.executable, ...])`), not
`exec()` inside the FastAPI process - so a submission that crashes, hangs,
or misbehaves can't take the whole server down with it. A timeout
(`CODE_TIMEOUT_SECONDS`, default 5s) kills anything that hangs, like an
accidental infinite loop.

**What this is not:** a security sandbox. It'll happily run whatever
Python you give it with the same permissions as the server process. For a
local tool checking your own code, that's the same trust model as running
`python your_script.py` yourself - fine. It would not be fine to expose
this to the public internet and let strangers submit code. The README says
this plainly rather than pretending otherwise.

## 3. How the config/security exercises work

Docker and security exercises don't execute anything - `_check_pattern()`
just runs a list of regexes against what you typed, split into
`required_patterns` (must be present) and `forbidden_patterns` (must be
absent). Each one carries a human-readable message, so a failure reads
like actual feedback ("add a `USER` instruction that isn't root") instead
of a raw regex mismatch.

This was **wrong on the first attempt**, and it's worth knowing how: the
SQL-injection exercise originally required the placeholder character to
appear literally inside the `execute(...)` call - `execute\([^)]*(\?|%s)`.
That works for `db.execute("... WHERE username = ?", (username,))` but
silently rejects the equally-correct, and more common, style of building
the query in a variable first:

```python
query = "SELECT * FROM users WHERE username = ?"
return db.execute(query, (username,))
```

The `?` is real, but it isn't textually inside the `execute(...)` parens -
it's in a different line entirely. Running actual solutions through the
checker (see the test block at the bottom of this file's git history, or
just try both styles yourself) caught it immediately. The fix splits it
into two independent checks - "a placeholder character exists somewhere in
a string literal" and "execute() is called with more than one argument" -
which both idiomatic styles satisfy. The lesson: **a pattern-matching
checker is only as good as the range of correct answers you actually test
it against**, not the range you can imagine in your head.

## 4. Why the curriculum is code, not data from an admin panel

`curriculum.py` is a plain Python file with `Track`/`Project`/`Step`
dataclasses and a literal list. No database table for exercises, no CMS,
no runtime editing. Deliberately:

- **It's reviewable.** A wrong test case is a diff you can read, the same
  way a bug in any other code is - not a row in a database you have to go
  query to inspect.
- **It's testable.** Nothing stops you from writing a real correct
  solution to every exercise and running it through `checker.py` as a
  regression test before you trust the exercise - which is exactly how
  every exercise in this file was actually verified before shipping.
- **It keeps the trust boundary simple.** The public `/api/curriculum`
  endpoint in `main.py` returns `id`/`title`/`instructions`/`starter_code`
  only - never `harness_code` or the regex patterns. If those lived in a
  database reachable the same way progress is, it'd be one bug away from
  leaking the answer key through the API.

## 5. The mentor's one real constraint

`mentor.py`'s system prompt has one non-negotiable line: "do NOT write the
complete corrected code or solution for them." Everything else about the
mentor call is a completely ordinary Claude API call - the only thing
protecting the "learn by doing" promise is that one sentence of prompt
engineering. Worth noticing: **there's no code-level enforcement of this**,
the same way there's no code-level guarantee a person won't just paste a
model's answer from somewhere else. The system's job is to make the doing
path easier than the shortcut, not to make the shortcut impossible.

## 6. Things worth trying

- Open `checker.py` and deliberately break a `harness_code` assertion in
  `curriculum.py` (e.g. change an expected value) - submit a correct
  solution and watch it now "fail" for the wrong reason. This is what a
  buggy test looks like from the other side, and it's exactly the class of
  bug the SQL-injection regex had.
- Submit code with an infinite `while True: pass` loop to any
  `python_exec` step and watch the timeout catch it instead of hanging the
  server.
- Read one exercise's `required_patterns` in `curriculum.py`, then try to
  write a submission that's *actually insecure* but *accidentally* matches
  every required pattern. If you can, that's a real weakness in that
  exercise's check - the same kind of thinking real security review
  requires.

## 7. Where to go from here

1. Add a fourth track, or another project to an existing one - the
   dataclasses in `curriculum.py` are the entire format; no other file
   needs to change.
2. Swap subprocess execution for a real sandbox (`gVisor`, `nsjail`, a
   locked-down Docker container with a seccomp profile and no network) if
   you ever want to let anyone but yourself submit code.
3. Add a "streak" - a `last_active_date` column in `database.py` and a
   small check on load - if you want a reason to come back daily.
