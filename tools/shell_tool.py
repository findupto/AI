import subprocess


def run_shell(command: str, timeout: int = 30, cwd: str | None = None):
    """Run a local project command; caller must enforce policy/approval."""
    if not command.strip():
        return False, "Empty command."
    try:
        completed = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True, timeout=max(1, int(timeout)))
        output = (completed.stdout + ("\n" + completed.stderr if completed.stderr else "")).strip()
        return completed.returncode == 0, output[:50_000]
    except subprocess.TimeoutExpired as exc:
        return False, f"Command timed out after {timeout}s: {exc}"
    except OSError as exc:
        return False, str(exc)
