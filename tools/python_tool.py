import builtins
import contextlib
import io
import multiprocessing


_ALLOWED_BUILTINS = (
    "abs", "all", "any", "bool", "dict", "enumerate", "filter", "float",
    "int", "len", "list", "map", "max", "min", "print", "range", "repr",
    "reversed", "round", "set", "sorted", "str", "sum", "tuple", "zip",
)


def _worker(code: str, out):
    buf = io.StringIO()
    safe_builtins = {name: getattr(builtins, name) for name in _ALLOWED_BUILTINS}
    globals_dict = {"__builtins__": safe_builtins}
    try:
        with contextlib.redirect_stdout(buf):
            exec(compile(code, "<findupto-python>", "exec"), globals_dict, {})
        out.put((True, buf.getvalue()))
    except Exception as exc:
        out.put((False, f"{type(exc).__name__}: {exc}"))


def run_python(code: str, timeout: int = 8) -> tuple[bool, str]:
    """Run a small Python snippet in a separate process with a hard timeout.

    This is a bounded execution helper, not a security-grade sandbox. Keep it
    disabled unless the application policy explicitly permits tool execution.
    """
    timeout = max(1, int(timeout))
    q = multiprocessing.Queue()
    p = multiprocessing.Process(target=_worker, args=(code, q), daemon=True)
    p.start()
    p.join(timeout)
    if p.is_alive():
        p.terminate()
        p.join()
        return False, "Python execution timed out."
    return q.get() if not q.empty() else (False, "Python execution failed.")
