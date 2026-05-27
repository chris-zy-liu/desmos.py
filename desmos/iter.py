"""Helpers for iteration and grid evaluation.

Desmos does not have Python-style recursion in user-defined arrows, but it
DOES allow piecewise-recursive function definitions. ``iterate`` emits one.
"""
from __future__ import annotations

from .expr import Expression
from .actions import LatexExpr, _latex_of
from .translate import _func_ident, _ident


def iterate(g, step, x0, *, name: str, extra_params: list[str] = ()):
    """Define recursive function ``name(k, *extras) = step^k(x0)`` evaluated at extras.

    ``step`` is the LatexExpr returned by an ``@g.func``-decorated function.
    The first argument of ``step`` is the iterated state; remaining arguments
    are the extras, passed through unchanged.
    """
    fname = _func_ident(name)
    extras = ",".join(extra_params)
    sig = f"k,{extras}" if extras else "k"
    self_call = (rf"{fname}\left(k-1,{extras}\right)"
                 if extras else rf"{fname}\left(k-1\right)")
    step_args = f"{self_call},{extras}" if extras else self_call
    step_call = rf"{step.latex}\left({step_args}\right)"
    x0_lat = _latex_of(x0)
    body = rf"\left\{{k=0:{x0_lat},{step_call}\right\}}"
    latex = rf"{fname}\left({sig}\right)={body}"
    g._add(Expression(id=g._new_id(), latex=latex))
    return LatexExpr(fname)


def heatmap(g, value_fn, *, x_range, y_range, max_value, palette: str = "fire",
            name: str = "G", point_size: float = 6,
            display_bounds: tuple | None = None):
    """Render a coloured point grid where each point's colour comes from
    ``value_fn(math_point)`` (a LatexExpr returned by ``@g.func``).

    ``x_range`` and ``y_range`` are ``(min, max, n)`` triples giving the
    **mathematical** region to evaluate over. ``min`` / ``max`` may be Vars /
    LatexExprs so the region pans/zooms.

    The points are *displayed* at ``display_bounds = (xmin, xmax, ymin, ymax)``
    — by default the Graph's viewport — so they always fill the screen
    regardless of the math region's size. This means zooming in (shrinking the
    math region) actually magnifies the picture, rather than squeezing the
    points into a smaller patch.
    """
    mxmin, mxmax, nx = x_range
    mymin, mymax, ny = y_range

    mxmin_l, mxmax_l = LatexExpr(_latex_of(mxmin)), LatexExpr(_latex_of(mxmax))
    mymin_l, mymax_l = LatexExpr(_latex_of(mymin)), LatexExpr(_latex_of(mymax))

    if display_bounds is None:
        dxmin, dxmax, dymin, dymax = g.xmin, g.xmax, g.ymin, g.ymax
    else:
        dxmin, dxmax, dymin, dymax = display_bounds

    # display step (constant numbers, since viewport is fixed)
    ddx = (dxmax - dxmin) / (nx - 1)
    ddy = (dymax - dymin) / (ny - 1)
    # math step (may involve Vars)
    mdx = (mxmax_l - mxmin_l) / (nx - 1)
    mdy = (mymax_l - mymin_l) / (ny - 1)

    # display grid: where points are drawn on screen (static)
    disp_grid = (
        rf"\left[\left({_latex_of(dxmin)}+i\cdot {_latex_of(ddx)},"
        rf"{_latex_of(dymin)}+j\cdot {_latex_of(ddy)}\right)"
        rf"\operatorname{{for}}i=\left[0...{nx - 1}\right],"
        rf"j=\left[0...{ny - 1}\right]\right]"
    )
    disp_name = _ident(name + "disp")
    g._add(Expression(id=g._new_id(),
                      latex=rf"{disp_name}={disp_grid}", hidden=True))

    # math grid: where escape is evaluated (follows pan/zoom)
    math_grid = (
        rf"\left[\left({mxmin_l.latex}+i\cdot \left({mdx.latex}\right),"
        rf"{mymin_l.latex}+j\cdot \left({mdy.latex}\right)\right)"
        rf"\operatorname{{for}}i=\left[0...{nx - 1}\right],"
        rf"j=\left[0...{ny - 1}\right]\right]"
    )
    grid_name = _ident(name + "grid")
    g._add(Expression(id=g._new_id(),
                      latex=rf"{grid_name}={math_grid}", hidden=True))

    # values: V = [value_fn(p) for p = math_grid]
    val_name = _ident(name + "val")
    g._add(Expression(
        id=g._new_id(),
        latex=(rf"{val_name}=\left[{value_fn.latex}\left(p\right)"
               rf"\operatorname{{for}}p={grid_name}\right]"),
        hidden=True,
    ))

    # colorLatex: per-point colour based on V / max_value.
    # Desmos hsv() takes hue in DEGREES [0,360], s and v in [0,1].
    norm = rf"\frac{{{val_name}}}{{{_latex_of(max_value)}}}"
    if palette == "fire":
        # 0 (escaped) -> blue (240°), N (in set) -> red (0°)
        color_latex = rf"\operatorname{{hsv}}\left(240\cdot \left(1-{norm}\right),1,1\right)"
    elif palette == "grayscale":
        color_latex = rf"\operatorname{{rgb}}\left(255\cdot {norm},255\cdot {norm},255\cdot {norm}\right)"
    else:
        raise ValueError(f"unknown palette: {palette}")

    # plot the DISPLAY grid (fills viewport) with colours from the math grid
    e = Expression(
        id=g._new_id(),
        latex=disp_name,
        points=True,
        lines=False,
        point_size=str(point_size),
        color_latex=color_latex,
    )
    return g._add(e)
