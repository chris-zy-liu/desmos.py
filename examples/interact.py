"""A draggable circle with buttons to grow/shrink and reset."""
from desmos import Graph


def main():
    g = Graph(bounds=(-5, 5, -5, 5), title="Interact demo")

    r = g.slider("r", 0.1, 4, value=1, step=0.05)
    cx = g.var("cx", 0.0)
    cy = g.var("cy", 0.0)

    # A draggable point sets cx, cy.  We use an action ticker would be wrong here;
    # for v1 we just show the circle as an implicit equation parameterised on cx, cy, r.
    g.expr(rf"\left(x-c_{{x}}\right)^{{2}}+\left(y-c_{{y}}\right)^{{2}}=r^{{2}}", color="#2d70b3")

    # Buttons
    g.button("Grow",   at=( 4,  4), action=r.set(r * 1.2))
    g.button("Shrink", at=( 4,  3), action=r.set(r / 1.2))
    g.button("Reset",  at=( 4,  2), action=[r.set(1), cx.set(0), cy.set(0)])

    g.to_html("interact.html")
    print("Wrote interact.html")


if __name__ == "__main__":
    main()
