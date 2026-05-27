import pytest
from desmos.translate import Translator
from desmos.errors import DesmosTranslationError

T = Translator()


def expr(src):
    return T.compile_expression(src)


def func(src):
    return T.compile_function(src)


# ---- atoms ----
def test_int_constant():
    assert expr("3") == "3"

def test_float_constant():
    assert expr("3.5") == "3.5"

def test_float_integer():
    assert expr("3.0") == "3"

def test_bool_constant():
    assert expr("True") == "1"
    assert expr("False") == "0"

def test_name_single_char():
    assert expr("x") == "x"

def test_name_multi_char_subscripts():
    assert expr("zoom") == "z_{oom}"


# ---- arithmetic ----
def test_add():
    assert expr("x + y") == r"\left(x\right)+\left(y\right)"

def test_div_uses_frac():
    assert expr("x / y") == r"\frac{x}{y}"

def test_pow_uses_braces():
    assert expr("x ** 2") == r"\left(x\right)^{2}"

def test_mod():
    assert r"\operatorname{mod}" in expr("x % 3")

def test_unary_minus():
    assert expr("-x") == r"-\left(x\right)"


# ---- compare ----
def test_simple_compare():
    assert expr("x < 1") == "x<1"

def test_chained_compare():
    out = expr("0 < x < 1")
    assert out.startswith(r"\left\{") and out.endswith(r"\right\}")
    assert "0<x" in out and "x<1" in out


# ---- ternary ----
def test_ternary():
    assert expr("1 if x > 0 else -1") == r"\left\{x>0:1,-\left(1\right)\right\}"


# ---- calls / builtins ----
def test_abs():
    assert expr("abs(x)") == r"\left|x\right|"

def test_sqrt():
    assert expr("sqrt(x)") == r"\sqrt{x}"

def test_sin():
    assert expr("sin(x)") == r"\sin\left(x\right)"

def test_min_multi():
    assert expr("min(a, b, c)") == r"\operatorname{min}\left(a,b,c\right)"

def test_user_call_single_char():
    assert expr("f(x)") == r"f\left(x\right)"

def test_user_call_multi_char():
    assert expr("escape(c)") == r"\operatorname{escape}\left(c\right)"

def test_range_one_arg():
    assert expr("range(N)") == r"\left[1...N\right]"

def test_range_two_args():
    assert expr("range(1, 10)") == r"\left[1...10\right]"


# ---- containers ----
def test_tuple_is_point():
    assert expr("(1, 2)") == r"\left(1,2\right)"

def test_tuple_three_is_list():
    assert expr("(1, 2, 3)") == r"\left[1,2,3\right]"


# ---- attr / subscript ----
def test_attr_xy():
    assert expr("z.x") == "z.x"
    assert expr("z.y") == "z.y"

def test_attr_other_rejected():
    with pytest.raises(DesmosTranslationError):
        expr("z.foo")

def test_subscript_const_int_offset():
    assert expr("a[0]") == r"a\left[1\right]"
    assert expr("a[3]") == r"a\left[4\right]"

def test_subscript_variable_offset():
    assert expr("a[k]") == r"a\left[\left(k\right)+1\right]"


# ---- list comp ----
def test_listcomp_basic():
    out = expr("[k for k in range(N)]")
    assert out == r"\left[k\operatorname{for}k=\left[1...N\right]\right]"

def test_listcomp_with_filter_rejected():
    with pytest.raises(DesmosTranslationError):
        expr("[k for k in range(N) if k > 5]")

def test_listcomp_multi_gen_rejected():
    with pytest.raises(DesmosTranslationError):
        expr("[k*j for k in range(3) for j in range(3)]")


# ---- function compilation ----
def test_simple_function():
    name, params, body = func("def f(x): return x*x")
    assert name == "f"
    assert params == ["x"]
    assert body == r"\left(x\right)\cdot \left(x\right)"

def test_multichar_function():
    name, params, body = func("def square(x): return x ** 2")
    assert name == r"\operatorname{square}"
    assert params == ["x"]

def test_function_with_point_return():
    name, params, body = func(
        "def step(z, c):\n    return (z.x**2 - z.y**2 + c.x, 2*z.x*z.y + c.y)"
    )
    assert name == r"\operatorname{step}"
    assert params == ["z", "c"]
    assert body.startswith(r"\left(") and body.endswith(r"\right)")


# ---- rejected statements ----
def test_for_rejected():
    with pytest.raises(DesmosTranslationError):
        func("def f(x):\n    for i in range(3):\n        pass\n    return x")

def test_assign_in_body_rejected():
    with pytest.raises(DesmosTranslationError):
        func("def f(x):\n    y = x + 1\n    return y")

def test_lambda_rejected():
    with pytest.raises(DesmosTranslationError):
        expr("lambda x: x")
