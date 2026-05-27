"""Electric field of two point charges — one positive, one negative.

The charges (red ``+`` and blue ``-``) are draggable points; the black
arrows update live as you move them.
"""
from desmos import Graph


def main():
    g = Graph(bounds=(-3.5, 3.5, -2.5, 2.5), title="Electric Field")

    # Two draggable point charges.
    g.expr(r"P_{1}=\left(-1,0\right)",
           drag_mode="XY", point_size="20",
           color="#c74440", label="+1", show_label=True)
    g.expr(r"P_{2}=\left(1,0\right)",
           drag_mode="XY", point_size="20",
           color="#2d70b3", label="-1", show_label=True)

    # Field from one charge ``q`` at ``src``. A small softening term in the
    # denominator keeps the field finite at the charges themselves.
    @g.func
    def Exfrom(p, q, src):
        return q * (p.x - src.x) / ((p.x - src.x)**2 + (p.y - src.y)**2 + 0.02)**1.5

    @g.func
    def Eyfrom(p, q, src):
        return q * (p.y - src.y) / ((p.x - src.x)**2 + (p.y - src.y)**2 + 0.02)**1.5

    # Total field: +1 at P1, -1 at P2.
    @g.func
    def Ex(p):
        return Exfrom(p, 1, P1) + Exfrom(p, -1, P2)

    @g.func
    def Ey(p):
        return Eyfrom(p, 1, P1) + Eyfrom(p, -1, P2)

    # The whole vector field in one call.
    g.field(
        Ex, Ey,
        x_range=(-3, 3, 13),       # 13 columns of arrows
        y_range=(-2, 2, 9),        # 9 rows
        length=0.25,
        head_size=0.08,
        color="#000000",
    )

    g.to_html("electric_field.html")
    print("Wrote electric_field.html")


if __name__ == "__main__":
    main()
