"""Vector field primitive: a grid of arrows that update live when their
inputs (charges, dipoles, ...) move.

This is the dynamic counterpart to ``primitives.arrow``, which only handles
static endpoints. ``field`` builds the arrow-head geometry as vectorised
Desmos LaTeX so heads recompute every frame.
"""
from __future__ import annotations

from .expr import Expression
from .actions import LatexExpr, _latex_of
from .translate import _func_ident, _ident


def field(g, Ex_fn, Ey_fn, *,
          x_range, y_range,
          length=0.25, head_size=0.08,
          name: str = "f",
          color: str = "#000000", line_width: float = 1.2):
    """A grid of unit-direction arrows for the field ``(Ex_fn, Ey_fn)``.

    Parameters
    ----------
    Ex_fn, Ey_fn : LatexExpr
        ``@g.func``-decorated functions of a single point ``p``.
    x_range, y_range : (min, max, n_or_step)
        Grid extent and resolution. If the third element is an ``int``, it's
        treated as the *count* of grid lines; otherwise as the spacing.
    length : float
        Shaft length of every arrow (the field is direction-only).
    head_size : float
        Length of each wing of the arrow head.
    name : str
        Identifier prefix for the helper expressions (must be unique within
        the graph if you have multiple fields).
    """
    def _list_latex(lo, hi, step_or_n):
        if isinstance(step_or_n, int):
            n = step_or_n
            if n < 2:
                raise ValueError("count must be >= 2")
            step = (hi - lo) / (n - 1)
        else:
            step = float(step_or_n)
        # Desmos list with stride: [lo, lo+step, ..., hi]
        return rf"\left[{lo},{lo + step},...,{hi}\right]"

    xs = _list_latex(*x_range)
    ys = _list_latex(*y_range)

    fmag  = _func_ident(name + "mag")
    ftip  = _func_ident(name + "tip")
    fwL   = _func_ident(name + "wL")
    fwR   = _func_ident(name + "wR")
    Gname = _ident(name + "G")
    Tname = _ident(name + "T")
    Lname = _ident(name + "L")
    Rname = _ident(name + "R")

    L  = length
    H  = head_size

    # mag(p) = sqrt(Ex^2 + Ey^2 + tiny)
    g._add(Expression(
        id=g._new_id(),
        latex=(rf"{fmag}\left(p\right)="
               rf"\sqrt{{\left({Ex_fn.latex}\left(p\right)\right)^{{2}}"
               rf"+\left({Ey_fn.latex}\left(p\right)\right)^{{2}}+0.001}}"),
    ))

    # tip(p) = p + L * E_hat
    g._add(Expression(
        id=g._new_id(),
        latex=(rf"{ftip}\left(p\right)=\left("
               rf"p.x+{L}\cdot \frac{{{Ex_fn.latex}\left(p\right)}}{{{fmag}\left(p\right)}},"
               rf"p.y+{L}\cdot \frac{{{Ey_fn.latex}\left(p\right)}}{{{fmag}\left(p\right)}}\right)"),
    ))

    # Perpendicular to E_hat = (Ex, Ey)/mag is N_hat = (-Ey, Ex)/mag.
    # back  = tip - H * E_hat
    # wingL = back + 0.5*H * N_hat = back + (-Ey, Ex) * 0.5*H/mag
    # wingR = back - 0.5*H * N_hat = back - (-Ey, Ex) * 0.5*H/mag
    Ex_over_mag = rf"\frac{{{Ex_fn.latex}\left(p\right)}}{{{fmag}\left(p\right)}}"
    Ey_over_mag = rf"\frac{{{Ey_fn.latex}\left(p\right)}}{{{fmag}\left(p\right)}}"
    Hh = H * 0.5

    def _wing(sx, sy):  # sx, sy ∈ {-1, +1} for the perpendicular component
        x = (rf"{ftip}\left(p\right).x-{H}\cdot {Ex_over_mag}"
             rf"{'+' if sx > 0 else '-'}{Hh}\cdot {Ey_over_mag}")
        y = (rf"{ftip}\left(p\right).y-{H}\cdot {Ey_over_mag}"
             rf"{'+' if sy > 0 else '-'}{Hh}\cdot {Ex_over_mag}")
        return rf"\left({x},{y}\right)"

    g._add(Expression(id=g._new_id(),
                      latex=rf"{fwL}\left(p\right)={_wing(-1, +1)}"))
    g._add(Expression(id=g._new_id(),
                      latex=rf"{fwR}\left(p\right)={_wing(+1, -1)}"))

    # Grid of tails and parallel head/wing lists.
    g._add(Expression(id=g._new_id(),
                      latex=rf"{Gname}=\left[\left(i,j\right)"
                            rf"\operatorname{{for}}i={xs},j={ys}\right]",
                      hidden=True))
    for vname, fn in [(Tname, ftip), (Lname, fwL), (Rname, fwR)]:
        g._add(Expression(
            id=g._new_id(),
            latex=rf"{vname}=\left[{fn}\left(p\right)\operatorname{{for}}p={Gname}\right]",
            hidden=True,
        ))

    # polygon(G, T, L, T, R) → N 5-vertex polylines: shaft + V-head.
    return g._add(Expression(
        id=g._new_id(),
        latex=rf"\operatorname{{polygon}}\left({Gname},{Tname},{Lname},{Tname},{Rname}\right)",
        color=color,
        line_width=str(line_width),
    ))
