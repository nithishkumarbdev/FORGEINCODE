import re
import subprocess
import sys
import tempfile
from pathlib import Path

from config import get_settings
from curriculum import Step

settings = get_settings()


def check_step(step: Step, submitted: str) -> dict:
    if step.check_type == "python_exec":
        return _check_python_exec(step, submitted)
    if step.check_type == "pattern":
        return _check_pattern(step, submitted)
    raise ValueError(f"Unknown check_type: {step.check_type}")


def _check_python_exec(step: Step, submitted_code: str) -> dict:
    """Runs the learner's code, followed by the step's assert-based harness,
    as a real subprocess - a fresh Python process, not exec() in this one.
    NOT a security sandbox: fine for a local learning tool running your own
    code, not for accepting code from anyone you don't trust. See README."""
    script = f"{submitted_code}\n\n{step.harness_code}\n\nprint('ALL_PASSED')\n"

    with tempfile.TemporaryDirectory() as tmp:
        script_path = Path(tmp) / "submission.py"
        script_path.write_text(script)
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=settings.code_timeout_seconds,
                cwd=tmp,
            )
        except subprocess.TimeoutExpired:
            return {
                "passed": False,
                "message": f"Your code took longer than {settings.code_timeout_seconds}s to run - check for an infinite loop.",
            }

    if result.returncode != 0:
        return {"passed": False, "message": _last_line(result.stderr)}

    if result.stdout.strip().endswith("ALL_PASSED"):
        return {"passed": True, "message": "All checks passed."}
    return {"passed": False, "message": "The checks didn't pass, but produced no details."}


def _check_pattern(step: Step, submitted_text: str) -> dict:
    failures = []
    for pattern, message in step.required_patterns:
        if not re.search(pattern, submitted_text, re.MULTILINE | re.IGNORECASE):
            failures.append(f"Missing: {message}")
    for pattern, message in step.forbidden_patterns:
        if re.search(pattern, submitted_text, re.MULTILINE | re.IGNORECASE):
            failures.append(f"Fix this: {message}")

    if failures:
        return {"passed": False, "message": "\n".join(failures)}
    return {"passed": True, "message": "Looks correct - every check passed."}


def _last_line(stderr: str) -> str:
    lines = [line for line in stderr.strip().splitlines() if line.strip()]
    return lines[-1] if lines else "Your code raised an error."
