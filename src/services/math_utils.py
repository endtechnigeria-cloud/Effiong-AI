"""
EFFIONG AI - Math engine
========================
Exact symbolic computation (algebra, calculus, equations, factorials, arithmetic) using SymPy, wrapped so that
user text can NEVER execute code:

  * only a strict character set and a whitelist of names is accepted
  * evaluation runs in a worker thread with a time limit
  * results are size-limited

Word problems and problems shown in IMAGES are solved by the multimodal brain (see brain_router.solve_math);
this engine gives that brain a verified computation to build its explanation on when the input is symbolic.
"""
from __future__ import annotations

import math
import re
import sys
import threading
from typing import Any, Dict, List, Optional

try:  # allow very large exact integers to be printed
    sys.set_int_max_str_digits(100000)
except AttributeError:
    pass

MAX_FACTORIAL_INPUT = 1000


def factorial(n: int):
    """Factorial with safety bounds and readable output for huge values."""
    if not isinstance(n, int):
        return "Invalid input. Please enter a whole integer."
    if n < 0:
        return "Factorial is not defined for negative numbers."
    if n > MAX_FACTORIAL_INPUT:
        return f"Input number {n} exceeds the safe calculation threshold (max limit is {MAX_FACTORIAL_INPUT})."
    result = str(math.factorial(n))
    if len(result) > 100:
        return f"{result[0]}.{result[1:5]} × 10^{len(result) - 1} (approx. {len(result)} total digits)"
    return result


_ALLOWED_NAMES = {
    "sin", "cos", "tan", "cot", "sec", "csc", "asin", "acos", "atan", "sinh", "cosh", "tanh", "exp", "log", "ln", "sqrt",
    "abs", "pi", "e", "oo", "factorial", "binomial", "gcd", "lcm", "floor", "ceiling", "sign", "cbrt",
    "integrate", "diff", "solve", "simplify", "expand", "factor", "limit", "sum", "product", "Sum", "Product",
    "Integral", "Derivative", "Eq", "det", "dx", "dt", "dy",
}
_SAFE_CHARS = re.compile(r"^[0-9A-Za-z+\-*/^()=,.\s<>!]+$")
_IDENT = re.compile(r"[A-Za-z_][A-Za-z_0-9]*")


def _names_ok(expr: str) -> bool:
    for name in _IDENT.findall(expr):
        if name in _ALLOWED_NAMES:
            continue
        if len(name) == 1 and name.isalpha():   # single-letter variables x, y, n ...
            continue
        return False
    return True


def _run_with_timeout(fn, seconds: float = 6.0) -> Any:
    box: Dict[str, Any] = {}

    def target() -> None:
        try:
            box["value"] = fn()
        except Exception as exc:
            box["error"] = exc

    th = threading.Thread(target=target, daemon=True)
    th.start()
    th.join(seconds)
    if th.is_alive():
        raise TimeoutError("computation took too long")
    if "error" in box:
        raise box["error"]
    return box.get("value")


def _strip_command(text: str) -> tuple[str, str]:
    """Split 'integrate x^2' style requests into (operation, expression)."""
    t = text.strip().rstrip("?.")
    t = re.sub(r"(?i)^(please\s+|can you\s+|could you\s+)", "", t)
    t = re.sub(r"(?i)\b(what is|what's|calculate|compute|evaluate|find|work out)\b\s*", "", t).strip()
    m = re.match(r"(?i)^(integrate|integral of|differentiate|derivative of|diff|solve|simplify|expand|factorise|factorize|factor|limit of)\s+(.*)$", t)
    if m:
        op = m.group(1).lower()
        op = {"integral of": "integrate", "differentiate": "diff", "derivative of": "diff", "factorise": "factor",
              "factorize": "factor", "limit of": "limit"}.get(op, op)
        return op, m.group(2).strip()
    return "eval", t


def try_symbolic(text: str) -> Optional[Dict[str, str]]:
    """
    Return {'operation','input','result','latex'} when `text` is a self-contained symbolic / arithmetic request,
    otherwise None (the brain handles it).
    """
    try:
        import sympy as sp
        from sympy.parsing.sympy_parser import (convert_xor, implicit_multiplication_application, parse_expr,
                                                standard_transformations)
    except Exception:
        return None
    op, expr = _strip_command(text)
    expr = expr.replace("×", "*").replace("÷", "/").replace("−", "-").replace("²", "^2").replace("³", "^3").replace("√", "sqrt")
    expr = re.sub(r"(?i)\bwith respect to\s+[a-z]\b", "", expr).strip()
    if not expr or len(expr) > 240 or not _SAFE_CHARS.match(expr) or not _names_ok(expr):
        return None
    if op == "eval" and not re.search(r"[\d)]", expr):
        return None
    # plain words like "the sun is hot" never pass _names_ok; bare numbers alone are not interesting
    if op == "eval" and re.fullmatch(r"[\d.\s]+", expr):
        return None
    if op == "eval" and not re.search(r"[+\-*/^()!]|sqrt|sin|cos|tan|log|ln|exp|pi|factorial", expr):
        return None

    transforms = standard_transformations + (implicit_multiplication_application, convert_xor)
    namespace: Dict[str, Any] = {name: getattr(sp, name) for name in ("sin", "cos", "tan", "cot", "sec", "csc", "asin", "acos", "atan", "sinh",
                                                                      "cosh", "tanh", "exp", "log", "sqrt", "pi", "E", "oo", "factorial",
                                                                      "binomial", "gcd", "lcm", "floor", "ceiling", "sign", "Abs", "cbrt")}
    namespace.update({"ln": sp.log, "e": sp.E, "abs": sp.Abs})
    # names the transformed code refers to; no builtins, so nothing else can be reached
    safe_globals: Dict[str, Any] = {"__builtins__": {}, "Symbol": sp.Symbol, "Integer": sp.Integer, "Float": sp.Float,
                                    "Rational": sp.Rational, "Function": sp.Function, "Mul": sp.Mul, "Add": sp.Add, "Pow": sp.Pow}

    def parse(s: str):
        return parse_expr(s, local_dict=dict(namespace), global_dict=dict(safe_globals), transformations=transforms, evaluate=True)

    def compute():
        x = sp.Symbol("x")
        if op == "eval":
            if "=" in expr and "==" not in expr:
                left, right = expr.split("=", 1)
                eq = sp.Eq(parse(left), parse(right))
                syms = sorted(eq.free_symbols, key=str)
                sol = sp.solve(eq, syms[0] if syms else x)
                return "solve", sp.pretty(eq, use_unicode=False), sol
            val = parse(expr)
            res = sp.simplify(val)
            approx = ""
            try:
                if res.free_symbols == set() and not res.is_Integer:
                    approx = f"  ≈ {sp.N(res, 15)}"
            except Exception:
                pass
            return "evaluate", expr, f"{res}{approx}"
        if op == "solve":
            if "=" in expr:
                left, right = expr.split("=", 1)
                eq = sp.Eq(parse(left), parse(right))
            else:
                eq = parse(expr)
            syms = sorted(eq.free_symbols, key=str)
            return "solve", str(eq), sp.solve(eq, syms[0] if syms else x)
        val = parse(expr)
        var = sorted(val.free_symbols, key=str)[0] if val.free_symbols else x
        if op == "integrate":
            return "integrate", f"∫ {expr} d{var}", f"{sp.integrate(val, var)} + C"
        if op == "diff":
            return "differentiate", f"d/d{var} ({expr})", sp.diff(val, var)
        if op == "simplify":
            return "simplify", expr, sp.simplify(val)
        if op == "expand":
            return "expand", expr, sp.expand(val)
        if op == "factor":
            return "factor", expr, sp.factor(val)
        if op == "limit":
            return "limit", expr, sp.limit(val, var, 0)
        raise ValueError("unsupported")

    try:
        operation, shown, result = _run_with_timeout(compute)
    except Exception:
        return None
    result_text = str(result)
    if len(result_text) > 4000:
        result_text = result_text[:4000] + " …"
    return {"operation": operation, "input": shown, "result": result_text}
