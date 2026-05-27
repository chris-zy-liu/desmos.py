"""Mandelbrot explorer, entirely in Desmos.

Pan via cx/cy buttons; zoom via zm; iteration depth via N.
"""
from desmos import Graph


def main():
    # Viewport is wider than the math region so buttons sit off to the side.
    g = Graph(bounds=(-2.0, 2.5, -1.5, 1.5), title="Mandelbrot")

    # Resolution must be an int (drives the size of the static grid).
    RES = 50

    # Interactive controls
    N    = g.slider("N",  10, 100, value=40, step=1)
    cx   = g.var("cx", -0.5)
    cy   = g.var("cy",  0.0)
    zm   = g.var("zm",  1.5)

    # --- Mandelbrot math ---
    @g.func
    def step(z, c):
        return (z.x ** 2 - z.y ** 2 + c.x, 2 * z.x * z.y + c.y)

    @g.func
    def magsq(z):
        return z.x ** 2 + z.y ** 2

    orbit = g.iterate(step, (0, 0), name="orbit", extra_params=["c"])

    @g.func
    def inside(k, c):
        return 1 if magsq(orbit(k, c)) < 4 else 0

    @g.func
    def escape(c):
        return sum([inside(k, c) for k in range(N)])

    # --- coloured grid ---
    g.heatmap(
        escape,
        x_range=(cx - zm, cx + zm, RES),
        y_range=(cy - zm, cy + zm, RES),
        max_value=N,
        palette="fire",
        name="M",
        point_size=12,
        display_bounds=(-2.0, 1.0, -1.5, 1.5),  # where pixels live on screen
    )

    # --- controls (placed in the right-side margin) ---
    g.button("Zoom in",   at=( 1.7,  1.2),  action=zm.set(zm * 0.5))
    g.button("Zoom out",  at=( 1.7,  1.0),  action=zm.set(zm * 2.0))
    g.button("Pan left",  at=( 1.7,  0.6),  action=cx.set(cx - zm * 0.3))
    g.button("Pan right", at=( 1.7,  0.4),  action=cx.set(cx + zm * 0.3))
    g.button("Pan up",    at=( 1.7,  0.2),  action=cy.set(cy + zm * 0.3))
    g.button("Pan down",  at=( 1.7,  0.0),  action=cy.set(cy - zm * 0.3))
    g.button("Reset",     at=( 1.7, -0.3),
             action=[cx.set(-0.5), cy.set(0.0), zm.set(1.5)])

    g.to_html("mandelbrot.html")
    print("Wrote mandelbrot.html")


if __name__ == "__main__":
    main()
