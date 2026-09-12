import io
import contextlib
import multiprocessing


def _worker(code: str, out):
    buf = io.StringIO()
    safe_builtins = {k: __builtins__[k] for k in ("abs", "all", "any", "dict", "float", "int", "len", "list", "max", "min", "print", "range", "round", "set", "sum", "str", "tuple")}
    try:
        with contextlib.redirect_stdout(buf):
            exec(code, {"__builtins__": safe_builtins}, {})
        out.put((True, buf.getvalue()))
    except Exception as exc:
        out.put((False, str(exc)))


def run_python(code: str, timeout: int = 8) -> tuple[bool, str]:
    q = multiprocessing.Queue()
    p = multiprocessing.Process(target=_worker, args=(code, q), daemon=True)
    p.start(); p.join(timeout)
    if p.is_alive():
        p.terminate(); p.join()
        return False, "Python execution timed out."
    return q.get() if not q.empty() else (False, "Python execution failed.")
