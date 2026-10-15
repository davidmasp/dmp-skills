import marimo

__generated_with = "0.25.1"
app = marimo.App(width="full")


@app.cell(hide_code=True)
def tutorial_intro(mo):
    mo.md("""
    # Plotting with R in marimo

    This short tutorial shows how to create R plots inside a marimo notebook
    and connect them to Python controls. `rpy2` bridges Python and R,
    `ggplot2` draws the figures, and marimo displays them.

    The examples use R's built-in `mtcars` dataset, so no data download is needed.
    Start with a static scatterplot, then move a slider to redraw an R histogram
    automatically.
    """)
    return


@app.cell(hide_code=True)
def setup_intro(mo):
    mo.md("""
    ## 1. Setup

    You need the Python packages `marimo` and `rpy2`, an R installation, and the
    R package `ggplot2`. The imports below connect the notebook to R; the first
    plotting cell loads `ggplot2`.

    Expand **R environment** to inspect the R runtime and library paths used
    by this notebook.
    """)
    return


@app.cell
def python_imports():
    import marimo as mo
    import rpy2.robjects as ro

    return mo, ro


@app.cell(hide_code=True)
def r_environment(mo, ro):
    mo.accordion({
        "R environment": mo.md(f"""
    - **R version:** {ro.r('R.version.string')[0]}
    - **R home:** `{ro.r('R.home()')[0]}`
    - **Library paths:** `{'; '.join(ro.r('.libPaths()'))}`
        """)
    })
    return


@app.cell(hide_code=True)
def static_plot_intro(mo):
    mo.md("""
    ## 2. Static R plot

    Compare car weight (`wt`, in thousands of pounds) with fuel economy
    (`mpg`, in miles per US gallon), coloured by the number of cylinders.

    `ro.r(...)` runs the R code, `ggsave()` saves the figure, and `mo.image()`
    displays it in the notebook.
    """)
    return


@app.cell
def static_r_scatterplot(mo, ro):
    ro.r("""
        library(ggplot2)

        p <- ggplot(mtcars, aes(wt, mpg, colour = factor(cyl))) +
            geom_point(size = 3) +
            theme_minimal()

        ggsave(
            "/tmp/marimo_ggplot.png",
            plot = p,
            width = 7,
            height = 5,
            dpi = 150
        )
    """)

    mo.image("/tmp/marimo_ggplot.png")
    return


@app.cell(hide_code=True)
def interactive_r_intro(mo):
    mo.md("""
    ## 3. Interactive R plot: histogram bin width

    Move the slider to change the bin width for fuel economy in R's built-in
    `mtcars` data. marimo passes `bin_width.value` to an R function through
    `rpy2` and reruns the plot cell whenever the slider changes.
    """)
    return


@app.cell
def histogram_slider(mo):
    bin_width = mo.ui.slider(
        start=0.5,
        stop=8.0,
        step=0.5,
        value=2.0,
        label="Bin width (mpg)",
        show_value=True,
    )
    bin_width
    return (bin_width,)


@app.cell(hide_code=True)
def r_histogram_renderer(ro):
    render_mpg_histogram = ro.r("""
        function(bin_width) {
            histogram <- ggplot(mtcars, aes(x = mpg)) +
                geom_histogram(
                    binwidth = bin_width,
                    boundary = 0,
                    fill = "#377EB8",
                    colour = "white"
                ) +
                scale_y_continuous(
                    breaks = function(limits) seq(0, ceiling(limits[2]), by = 1),
                    expand = expansion(mult = c(0, 0.05))
                ) +
                coord_cartesian(xlim = c(8, 40)) +
                labs(
                    title = "Fuel economy in mtcars",
                    subtitle = sprintf("32 cars | Bin width: %.1f mpg", bin_width),
                    x = "Fuel economy (miles per US gallon)",
                    y = "Number of cars"
                ) +
                theme_minimal() +
                theme(text = element_text(size = 8))

            # Return PNG bytes; the temporary file is removed after each render.
            image_path <- tempfile(fileext = ".png")
            on.exit(unlink(image_path), add = TRUE)
            ggsave(image_path, histogram, width = 7, height = 5, dpi = 150)
            readBin(image_path, "raw", n = file.info(image_path)$size)
        }
    """)
    return (render_mpg_histogram,)


@app.cell
def interactive_r_histogram(bin_width, mo, render_mpg_histogram):
    interactive_histogram_png = bytes(render_mpg_histogram(bin_width.value))
    mo.image(interactive_histogram_png, width=840)
    return


if __name__ == "__main__":
    app.run()
