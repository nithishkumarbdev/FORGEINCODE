# Forge

Learn software development, cloud/DevOps, and security by actually doing
it - not by reading about it or chatting with an AI about it.

Pick an exercise. Write real code or a real config file in a real editor.
Click **Check my work** and a real system checks it - either by actually
running your code against test assertions, or by inspecting what you wrote
for the specific things that matter. If you're stuck, an AI mentor is one
click away - but it's built to give you a nudge in the right direction,
never the answer.

- **Backend:** FastAPI + SQLite (progress only - curriculum is code)
- **Frontend:** plain HTML/CSS/JS + CodeMirror for the editor, no build step
- **Checking:** real Python subprocess execution for code exercises, regex
  pattern checks for config/security exercises
- **AI:** Claude API, used only for hints - the pass/fail verdict is never
  decided by the model

New here? Read [`LEARNING.md`](./LEARNING.md) - it walks through how the
checking system works and why it's built this way.

## Project structure

```
forge/
├── backend/
│   ├── main.py           # FastAPI app, routes
│   ├── config.py         # typed settings, loaded from .env
│   ├── curriculum.py     # every track/project/step - the actual content
│   ├── checker.py        # runs the real checks (code execution + patterns)
│   ├── mentor.py         # AI hint endpoint, deliberately answer-shy
│   ├── database.py       # progress tracking only
│   ├── schemas.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   └── markdown.js       # small in-house renderer for instructions
└── .gitignore
```

## Setup

**1. Install dependencies**
```bash
cd forge/backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**2. Configure (optional, but needed for the mentor)**
```bash
cp .env.example .env
```
Add `ANTHROPIC_API_KEY` if you want the "Ask the mentor" hints to work.
Everything else - exercises, checking, progress tracking - works with no
key at all.

**3. Run**
```bash
uvicorn main:app --reload
```
Open **http://127.0.0.1:8000**.

## What's actually in it right now

- **Software Development** → Build a URL Shortener (3 steps): write the
  core logic, add input validation, build a storage layer.
- **Cloud & DevOps** → Containerize a Python Web App (3 steps): a
  production-lean Dockerfile, a `.dockerignore`, a hardened
  `docker-compose.yml`.
- **Cybersecurity** → Find and Fix (3 steps): SQL injection, a hardcoded
  secret, reflected XSS - each a real vulnerable snippet you patch yourself.

Nine exercises total. Small on purpose - see `LEARNING.md` for exactly how
to add your own, since the curriculum is just a Python data structure.

## Honest limitations

- **Code execution is not a security sandbox.** `checker.py` runs your
  submitted Python in a real subprocess with a timeout - which is exactly
  right for a local tool checking *your own* code, and exactly wrong for
  accepting code from anyone you don't trust. Don't expose this publicly
  without adding real sandboxing (gVisor, Firecracker, a container with a
  locked-down seccomp profile) first.
- **No auth.** Same reasoning as AutoMind and Cortex - add the optional
  `X-API-Key` pattern from AutoMind's `main.py` if this needs to leave your
  machine.
- **The curriculum is small and hand-written on purpose**, not
  AI-generated at runtime - see `LEARNING.md` for why that's a deliberate
  choice, not a shortcut.

## Natural next steps

More tracks/steps (the format in `curriculum.py` is meant to be extended),
a real sandbox for code execution, a "streak" or spaced-repetition layer,
exporting your solved exercises as a portfolio.
