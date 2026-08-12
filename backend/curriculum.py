from dataclasses import dataclass, field


@dataclass
class Step:
    id: str
    title: str
    language: str  # "python" | "text" - drives the editor's syntax mode
    instructions: str  # markdown
    check_type: str  # "python_exec" | "pattern"
    starter_code: str = ""
    harness_code: str = ""  # python_exec only: asserts run after the submission
    required_patterns: list[tuple[str, str]] = field(default_factory=list)  # (regex, human message)
    forbidden_patterns: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class Project:
    id: str
    title: str
    summary: str
    steps: list[Step]


@dataclass
class Track:
    id: str
    title: str
    summary: str
    projects: list[Project]


TRACKS: list[Track] = [
    Track(
        id="software-dev",
        title="Software Development",
        summary="Build a small real service from scratch, one working piece at a time.",
        projects=[
            Project(
                id="url-shortener",
                title="Build a URL Shortener",
                summary="The core logic behind a real product, in three pieces.",
                steps=[
                    Step(
                        id="shortener-1",
                        title="Generate a short code",
                        language="python",
                        check_type="python_exec",
                        instructions=(
                            "Write `shorten(url, existing_codes)`. It should return a 6-character "
                            "code made of letters and digits, and it must **not** be a code that's "
                            "already in `existing_codes` (a set of strings you're given).\n\n"
                            "This is the core trick behind every URL shortener: turn a long URL "
                            "into a short, unique-enough token."
                        ),
                        starter_code=(
                            "import random\n"
                            "import string\n\n\n"
                            "def shorten(url, existing_codes):\n"
                            "    # TODO: generate a 6-character code of letters and digits\n"
                            "    # that is not already present in existing_codes, and return it.\n"
                            "    pass\n"
                        ),
                        harness_code=(
                            "existing = {\"abc123\", \"zzz999\"}\n"
                            "code = shorten(\"https://example.com\", existing)\n"
                            "assert isinstance(code, str), \"shorten() should return a string\"\n"
                            "assert len(code) == 6, f\"expected a 6-character code, got {len(code)!r}\"\n"
                            "assert code.isalnum(), \"the code should only contain letters and digits\"\n"
                            "assert code not in existing, \"the code must not already be in existing_codes\"\n\n"
                            "existing.add(code)\n"
                            "code2 = shorten(\"https://example.com/other\", existing)\n"
                            "assert code2 != code, \"calling shorten() again should not return the same code\"\n"
                        ),
                    ),
                    Step(
                        id="shortener-2",
                        title="Validate the input",
                        language="python",
                        check_type="python_exec",
                        instructions=(
                            "Write `is_valid_url(url)`. Return `True` only for strings that start "
                            "with `http://` or `https://` **and** contain a `.` somewhere after "
                            "the scheme. Return `False` for anything else, including `None` and "
                            "empty strings - and don't let it raise an exception on bad input."
                        ),
                        starter_code=(
                            "def is_valid_url(url):\n"
                            "    # TODO: return True for well-formed http(s) URLs, False otherwise.\n"
                            "    pass\n"
                        ),
                        harness_code=(
                            "assert is_valid_url(\"https://example.com\") is True\n"
                            "assert is_valid_url(\"http://example.com/path\") is True\n"
                            "assert is_valid_url(\"ftp://example.com\") is False, \"only http/https should pass\"\n"
                            "assert is_valid_url(\"not a url\") is False\n"
                            "assert is_valid_url(\"\") is False\n"
                            "assert is_valid_url(None) is False, \"None should return False, not raise\"\n"
                        ),
                    ),
                    Step(
                        id="shortener-3",
                        title="Store the mapping",
                        language="python",
                        check_type="python_exec",
                        instructions=(
                            "Write a `Store` class with two methods: `save(code, url)` which "
                            "remembers the mapping, and `get(code)` which returns the URL for a "
                            "known code or `None` for an unknown one. Back it with a plain dict "
                            "internally."
                        ),
                        starter_code=(
                            "class Store:\n"
                            "    def __init__(self):\n"
                            "        # TODO: set up internal storage\n"
                            "        pass\n\n"
                            "    def save(self, code, url):\n"
                            "        # TODO\n"
                            "        pass\n\n"
                            "    def get(self, code):\n"
                            "        # TODO\n"
                            "        pass\n"
                        ),
                        harness_code=(
                            "store = Store()\n"
                            "store.save(\"abc123\", \"https://example.com\")\n"
                            "assert store.get(\"abc123\") == \"https://example.com\"\n"
                            "assert store.get(\"missing\") is None, \"an unknown code should return None\"\n"
                        ),
                    ),
                ],
            ),
        ],
    ),
    Track(
        id="cloud",
        title="Cloud & DevOps",
        summary="Package and harden a real app the way it'd actually ship.",
        projects=[
            Project(
                id="containerize",
                title="Containerize a Python Web App",
                summary="Go from source code to a production-lean container.",
                steps=[
                    Step(
                        id="docker-1",
                        title="Write a production-lean Dockerfile",
                        language="text",
                        check_type="pattern",
                        instructions=(
                            "Write a `Dockerfile` for a small Python web app. It should:\n\n"
                            "- start from a **slim, version-pinned** Python base image\n"
                            "- set a `WORKDIR`\n"
                            "- copy `requirements.txt` in and install it **before** copying the "
                            "rest of the source (so Docker can cache that layer)\n"
                            "- run as a **non-root user**\n"
                            "- define a `CMD` to start the app\n"
                        ),
                        starter_code="# Write your Dockerfile here\n",
                        required_patterns=[
                            (r"^FROM\s+python:\S+-slim", "start FROM a slim, version-pinned Python image (e.g. `python:3.12-slim`)"),
                            (r"WORKDIR\s+\S+", "set a WORKDIR"),
                            (r"COPY\s+requirements\.txt", "COPY requirements.txt in before the rest of the source"),
                            (r"RUN\s+pip install", "install dependencies with `RUN pip install`"),
                            (r"USER\s+(?!root\b)\w+", "add a `USER` instruction that isn't root"),
                            (r"CMD\s+\[", "define a `CMD` (exec form, e.g. `CMD [\"python\", \"app.py\"]`)"),
                        ],
                        forbidden_patterns=[
                            (r"FROM\s+python:latest", "avoid `python:latest` - pin a specific version so builds are reproducible"),
                        ],
                    ),
                    Step(
                        id="docker-2",
                        title="Write a .dockerignore",
                        language="text",
                        check_type="pattern",
                        instructions=(
                            "Write a `.dockerignore` that keeps local junk and secrets out of the "
                            "image: at minimum, exclude `__pycache__`, your virtual environment, "
                            "your `.env` file, and `.git`."
                        ),
                        starter_code="# Write your .dockerignore here\n",
                        required_patterns=[
                            (r"__pycache__", "exclude __pycache__"),
                            (r"\.env", "exclude .env - it's how secrets accidentally end up baked into images"),
                            (r"\.git", "exclude .git"),
                            (r"venv|\.venv", "exclude your virtual environment folder"),
                        ],
                    ),
                    Step(
                        id="docker-3",
                        title="Write a hardened docker-compose.yml",
                        language="text",
                        check_type="pattern",
                        instructions=(
                            "Write a `docker-compose.yml` for the same app. Include a "
                            "`healthcheck:`, a sensible `restart:` policy, and a memory limit. "
                            "Do **not** run it in privileged mode."
                        ),
                        starter_code="# Write your docker-compose.yml here\n",
                        required_patterns=[
                            (r"healthcheck:", "add a `healthcheck:` block"),
                            (r"restart:\s*(unless-stopped|on-failure|always)", "set a `restart:` policy"),
                            (r"mem_limit:|resources:", "set a memory limit"),
                        ],
                        forbidden_patterns=[
                            (r"privileged:\s*true", "avoid `privileged: true` - it disables container isolation entirely"),
                        ],
                    ),
                ],
            ),
        ],
    ),
    Track(
        id="security",
        title="Cybersecurity",
        summary="Find real vulnerabilities in real code, then fix them.",
        projects=[
            Project(
                id="find-and-fix",
                title="Find and Fix: Web App Vulnerabilities",
                summary="Three genuine, common bugs. Your job: spot them and patch them.",
                steps=[
                    Step(
                        id="vuln-1",
                        title="SQL injection",
                        language="python",
                        check_type="pattern",
                        instructions=(
                            "This function builds a SQL query by concatenating raw user input "
                            "directly into the string - a textbook SQL injection vulnerability. "
                            "Rewrite it to use a parameterized query instead (a `?` or `%s` "
                            "placeholder passed separately to `execute()`)."
                        ),
                        starter_code=(
                            "def get_user(username):\n"
                            "    query = \"SELECT * FROM users WHERE username = '\" + username + \"'\"\n"
                            "    return db.execute(query)\n"
                        ),
                        required_patterns=[
                            (r"['\"][^'\"]*(\?|%s)[^'\"]*['\"]", "put a `?` or `%s` placeholder inside the query string instead of concatenating the value in"),
                            (r"execute\([^)]*,", "pass the username as a separate argument to execute(), not concatenated into the query string"),
                        ],
                        forbidden_patterns=[
                            (r"\+\s*username", "don't concatenate `username` directly into the query string - that's the vulnerability"),
                        ],
                    ),
                    Step(
                        id="vuln-2",
                        title="Hardcoded secret",
                        language="python",
                        check_type="pattern",
                        instructions=(
                            "There's a live-looking API key hardcoded in this source file - which "
                            "means it's sitting in plain text in version control forever, visible "
                            "to anyone with repo access. Fix it by loading the key from an "
                            "environment variable instead."
                        ),
                        starter_code=(
                            "API_KEY = \"sk-live-51H8xJ2eKh9vQ3mN7pL0wZ9y\"\n\n"
                            "def call_service():\n"
                            "    return requests.get(URL, headers={\"Authorization\": API_KEY})\n"
                        ),
                        required_patterns=[
                            (r"os\.(getenv|environ)", "load the key from an environment variable using os.getenv() or os.environ"),
                        ],
                        forbidden_patterns=[
                            (r"sk-live-", "remove the hardcoded key from the source code entirely, not just rename it"),
                        ],
                    ),
                    Step(
                        id="vuln-3",
                        title="Reflected XSS",
                        language="python",
                        check_type="pattern",
                        instructions=(
                            "This function drops a user-supplied name directly into an HTML "
                            "response with no escaping - if `name` contains a `<script>` tag, it "
                            "runs in the victim's browser. Fix it by escaping the input before it "
                            "goes into the HTML."
                        ),
                        starter_code=(
                            "def render_greeting(name):\n"
                            "    return f\"<h1>Hello, {name}!</h1>\"\n"
                        ),
                        required_patterns=[
                            (r"escape\(|html\.escape|markupsafe", "escape the user input before inserting it into HTML (e.g. `html.escape()`)"),
                        ],
                    ),
                ],
            ),
        ],
    ),
]

STEP_INDEX: dict[str, Step] = {
    step.id: step
    for track in TRACKS
    for project in track.projects
    for step in project.steps
}


def find_step(step_id: str) -> Step | None:
    return STEP_INDEX.get(step_id)
