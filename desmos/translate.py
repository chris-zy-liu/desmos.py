"""Python AST → Desmos LaTeX compiler (strict v1 subset).

Supports a small documented subset of Python expressions. Statements other
than ``return`` are rejected. See README / plan for the full list.

Usage:
    src = inspect.getsource(fn)
    Translator().compile_function(src)  ->  (name, params, body_latex)
"""
from __future__ import annotations
import ast
import textwrap
from typing import Callable

from .errors import DesmosTranslationError


# --- name normalisation (kept in sync with graph._normalize_name) ---
def _ident(name: str) -> str:
    """Render a Python identifier as a Desmos variable identifier."""
    if "_" in name or "\\" in name or "{" in name:
        return name
    if len(name) <= 1:
        return name
    return f"{name[0]}_{{{name[1:]}}}"


def _func_ident(name: str) -> str:
    """Render a Python identifier as a Desmos function name."""
    if len(name) <= 1:
        return name
    return rf"\operatorname{{{name}}}"


# --- builtin dispatch ---
# Each entry: (min_args, max_args, formatter(args_latex: list[str]) -> str).
def _wrap1(latex_template: str):
    return lambda args: latex_template.format(args[0])


def _wrapN(name: str):
    return lambda args: rf"\operatorname{{{name}}}\left({','.join(args)}\right)"


def _wrap_bin(infix: str):
    def f(args):
        return rf"\left({args[0]}\right){infix}\left({args[1]}\right)"
    return f


BUILTINS: dict[str, tuple[int, int | None, Callable[[list[str]], str]]] = {
    "abs":   (1, 1, _wrap1(r"\left|{0}\right|")),
    "sqrt":  (1, 1, _wrap1(r"\sqrt{{{0}}}")),
    "sin":   (1, 1, _wrap1(r"\sin\left({0}\right)")),
    "cos":   (1, 1, _wrap1(r"\cos\left({0}\right)")),
    "tan":   (1, 1, _wrap1(r"\tan\left({0}\right)")),
    "exp":   (1, 1, _wrap1(r"\exp\left({0}\right)")),
    "log":   (1, 1, _wrap1(r"\ln\left({0}\right)")),
    "ln":    (1, 1, _wrap1(r"\ln\left({0}\right)")),
    "floor": (1, 1, _wrap1(r"\operatorname{{floor}}\left({0}\right)")),
    "ceil":  (1, 1, _wrap1(r"\operatorname{{ceil}}\left({0}\right)")),
    "round": (1, 1, _wrap1(r"\operatorname{{round}}\left({0}\right)")),
    "min":   (1, None, _wrapN("min")),
    "max":   (1, None, _wrapN("max")),
    "sum":   (1, 1, _wrap1(r"\operatorname{{total}}\left({0}\right)")),
    "len":   (1, 1, _wrap1(r"\operatorname{{length}}\left({0}\right)")),
    # range handled specially in visit_Call (produces Desmos list literal, not function call)
}


_BIN_OPS: dict[type, str] = {
    ast.Add: "+",
    ast.Sub: "-",
    ast.Mult: r"\cdot ",
    ast.Mod: r"\operatorname{mod}",  # handled specially
}

_CMP_OPS: dict[type, str] = {
    ast.Lt: "<",
    ast.LtE: r"\le ",
    ast.Gt: ">",
    ast.GtE: r"\ge ",
    ast.Eq: "=",
    ast.NotEq: r"\ne ",
}


def _err(node: ast.AST, msg: str) -> DesmosTranslationError:
    return DesmosTranslationError(msg, lineno=getattr(node, "lineno", None),
                                  node_type=type(node).__name__)


class Translator(ast.NodeVisitor):
    """AST → LaTeX string. Each visit_* method returns a LaTeX string."""

    def __init__(self, extra_builtins: dict | None = None):
        self.builtins = dict(BUILTINS)
        if extra_builtins:
            self.builtins.update(extra_builtins)

    # ---- top-level entry points ----
    def compile_expression(self, source: str) -> str:
        tree = ast.parse(source, mode="eval")
        return self.visit(tree.body)

    def compile_function(self, source: str) -> tuple[str, list[str], str]:
        """Compile a single ``def`` to (latex_name, params, body_latex)."""
        source = textwrap.dedent(source)
        tree = ast.parse(source)
        if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
            raise DesmosTranslationError("source must contain exactly one function definition")
        fn: ast.FunctionDef = tree.body[0]
        if fn.decorator_list:
            # Decorators are stripped before getsource if applied by the lib;
            # if any remain (e.g. unrelated), ignore them rather than fail.
            pass
        if fn.args.vararg or fn.args.kwarg or fn.args.kwonlyargs or fn.args.defaults:
            raise _err(fn, "function may only take positional parameters (no defaults, *args, **kwargs)")
        params = [a.arg for a in fn.args.args]
        if len(fn.body) != 1 or not isinstance(fn.body[0], ast.Return):
            raise _err(fn, "function body must be a single `return <expr>` statement")
        ret = fn.body[0]
        if ret.value is None:
            raise _err(ret, "bare `return` is not supported")
        body = self.visit(ret.value)
        return _func_ident(fn.name), [_ident(p) for p in params], body

    # ---- dispatch / unsupported nodes ----
    def generic_visit(self, node):  # pragma: no cover (catches anything not listed below)
        raise _err(node, f"unsupported Python construct: {type(node).__name__}")

    # ---- atoms ----
    def visit_Constant(self, node: ast.Constant) -> str:
        v = node.value
        if isinstance(v, bool):
            return "1" if v else "0"
        if isinstance(v, (int, float)):
            if isinstance(v, float) and v.is_integer():
                return str(int(v))
            return repr(v)
        raise _err(node, f"unsupported constant type: {type(v).__name__}")

    def visit_Name(self, node: ast.Name) -> str:
        return _ident(node.id)

    # ---- arithmetic ----
    def visit_BinOp(self, node: ast.BinOp) -> str:
        op = type(node.op)
        if op is ast.Div:
            return rf"\frac{{{self.visit(node.left)}}}{{{self.visit(node.right)}}}"
        if op is ast.Pow:
            return rf"\left({self.visit(node.left)}\right)^{{{self.visit(node.right)}}}"
        if op is ast.Mod:
            return rf"\operatorname{{mod}}\left({self.visit(node.left)},{self.visit(node.right)}\right)"
        if op not in _BIN_OPS:
            raise _err(node, f"unsupported binary operator: {op.__name__}")
        return rf"\left({self.visit(node.left)}\right){_BIN_OPS[op]}\left({self.visit(node.right)}\right)"

    def visit_UnaryOp(self, node: ast.UnaryOp) -> str:
        if isinstance(node.op, ast.UAdd):
            return self.visit(node.operand)
        if isinstance(node.op, ast.USub):
            return rf"-\left({self.visit(node.operand)}\right)"
        raise _err(node, f"unsupported unary operator: {type(node.op).__name__}")

    # ---- comparisons (single + chained) ----
    def visit_Compare(self, node: ast.Compare) -> str:
        for op in node.ops:
            if type(op) not in _CMP_OPS:
                raise _err(node, f"unsupported comparison operator: {type(op).__name__}")
        # chained `a < b < c` → Desmos piecewise condition list `\left\{a<b,b<c\right\}`
        parts = []
        left = self.visit(node.left)
        for op, right_node in zip(node.ops, node.comparators):
            right = self.visit(right_node)
            parts.append(f"{left}{_CMP_OPS[type(op)]}{right}")
            left = right
        if len(parts) == 1:
            return parts[0]
        return r"\left\{" + ",".join(parts) + r"\right\}"

    # ---- ternary → Desmos piecewise ----
    def visit_IfExp(self, node: ast.IfExp) -> str:
        cond = self.visit(node.test)
        then = self.visit(node.body)
        else_ = self.visit(node.orelse)
        return rf"\left\{{{cond}:{then},{else_}\right\}}"

    # ---- calls (builtins, range, user funcs) ----
    def visit_Call(self, node: ast.Call) -> str:
        if node.keywords:
            raise _err(node, "keyword arguments are not supported")
        if not isinstance(node.func, ast.Name):
            raise _err(node, "only direct function calls (by name) are supported")
        name = node.func.id
        args = [self.visit(a) for a in node.args]

        if name == "range":
            return self._compile_range(node, args)

        if name in self.builtins:
            mn, mx, fmt = self.builtins[name]
            if len(args) < mn or (mx is not None and len(args) > mx):
                expected = str(mn) if mn == mx else f"{mn}..{'inf' if mx is None else mx}"
                raise _err(node, f"{name}() expects {expected} args, got {len(args)}")
            return fmt(args)

        # user-defined function
        return rf"{_func_ident(name)}\left({','.join(args)}\right)"

    def _compile_range(self, node: ast.Call, args: list[str]) -> str:
        if len(args) == 1:
            # range(n) -> [1...n]   (1-based; matches Desmos lists)
            return rf"\left[1...{args[0]}\right]"
        if len(args) == 2:
            return rf"\left[{args[0]}...{args[1]}\right]"
        raise _err(node, "range() with 3 args (step) is not supported")

    # ---- containers ----
    def visit_Tuple(self, node: ast.Tuple) -> str:
        items = [self.visit(e) for e in node.elts]
        if len(items) == 2:
            return rf"\left({items[0]},{items[1]}\right)"
        # Longer tuples → Desmos list (Desmos has no n-tuples)
        return rf"\left[{','.join(items)}\right]"

    def visit_List(self, node: ast.List) -> str:
        items = [self.visit(e) for e in node.elts]
        return rf"\left[{','.join(items)}\right]"

    # ---- attribute / subscript ----
    def visit_Attribute(self, node: ast.Attribute) -> str:
        if node.attr not in ("x", "y"):
            raise _err(node, f"only .x and .y attribute access is supported (got .{node.attr})")
        return f"{self.visit(node.value)}.{node.attr}"

    def visit_Subscript(self, node: ast.Subscript) -> str:
        base = self.visit(node.value)
        # ast slice handling differs by python version; we expect a value, not a Slice
        idx_node = node.slice
        if isinstance(idx_node, ast.Slice):
            raise _err(node, "slices are not supported")
        idx = self.visit(idx_node)
        # Python is 0-based, Desmos is 1-based. If the index is a plain integer
        # constant, fold the +1; otherwise emit (idx + 1).
        if isinstance(idx_node, ast.Constant) and isinstance(idx_node.value, int):
            return f"{base}\\left[{idx_node.value + 1}\\right]"
        return rf"{base}\left[\left({idx}\right)+1\right]"

    # ---- list comprehension (single for, no filter) ----
    def visit_ListComp(self, node: ast.ListComp) -> str:
        if len(node.generators) != 1:
            raise _err(node, "only single-generator list comprehensions are supported")
        gen = node.generators[0]
        if gen.ifs:
            raise _err(node, "list comprehensions with `if` filters are not supported in v1")
        if gen.is_async:
            raise _err(node, "async comprehensions are not supported")
        if not isinstance(gen.target, ast.Name):
            raise _err(node, "comprehension target must be a single name")
        var = _ident(gen.target.id)
        iter_latex = self.visit(gen.iter)
        # range(n) returns "\left[1...n\right]" but for `for k in list` we want "k=list"
        # Strip the surrounding [ ] from a range to get the list literal form, otherwise
        # use as-is.
        body = self.visit(node.elt)
        return rf"\left[{body}\operatorname{{for}}{var}={iter_latex}\right]"
