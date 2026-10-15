# R-to-marimo integration patterns

## Example provenance and boundaries

[notebook.py](notebook.py) is an unchanged copy of `/Users/david.mas/Desktop/TMP_ttt/notebook.py`, captured on 2026-10-08. It was generated with marimo 0.25.1. Its source project declares Python ≥3.13, `marimo>=0.25.1`, and `rpy2>=3.6.8`; these describe the example environment, not minimum versions imposed by this skill. It also needs an R runtime and R's `ggplot2` package. It uses built-in `mtcars`, so no input download is needed.

The static scatterplot demonstrates `ro.r(...)`, `ggsave()`, and `mo.image(path)`, but writes to a shared `/tmp/marimo_ggplot.png`. The histogram demonstrates a better inline-image lifecycle: a unique temporary file, cleanup with `on.exit()`, a returned raw vector, and display from Python bytes. Use that lifecycle for static plots too. Its R function currently relies on `library(ggplot2)` from the scatterplot cell; new implementations should remove that hidden dependency.

Only reuse the example's slider and reactive redraw when the user explicitly asks for interaction. A static request needs no widgets, callbacks, or control panel.

## Static plot with PNG bytes

These are integration cells to adapt within a notebook, not a complete notebook template. Apply the companion ggplot skill's styling to the figure as appropriate.

```python
@app.cell
def r_imports():
    import marimo as mo
    import rpy2.robjects as ro
    return mo, ro


@app.cell
def r_renderer(ro):
    render_scatter_png = ro.r('''
        function() {
            library(ggplot2)
            plot <- ggplot(mtcars, aes(wt, mpg, colour = factor(cyl))) +
                geom_point() +
                labs(x = "Weight (1000 lb)", y = "Fuel economy (mpg)",
                     colour = "Cylinders") +
                theme_classic()

            image_path <- tempfile(fileext = ".png")
            on.exit(unlink(image_path), add = TRUE)
            ggsave(filename = image_path, plot = plot,
                   width = 7, height = 5, units = "in", dpi = 150)
            readBin(image_path, "raw", n = file.info(image_path)$size)
        }
    ''')
    return (render_scatter_png,)


@app.cell
def static_plot(mo, render_scatter_png):
    scatter_png = bytes(render_scatter_png())
    mo.image(scatter_png)
    return
```

Keep R data and plot objects local to the function where possible. Return a callable from its defining cell and consume it in the rendering cell so marimo sees the ordering. A separate R setup cell must expose a Python dependency consumed downstream; merely sharing `ro` does not establish ordering between sibling cells.

Pass changing inputs as arguments to the callable rather than interpolating Python values into R source or updating `ro.globalenv` from unrelated cells. For pandas data, use a scoped converter only around the conversion:

```python
from rpy2.robjects import pandas2ri

with (ro.default_converter + pandas2ri.converter).context():
    r_data = ro.conversion.get_conversion().py2rpy(data_frame)

# A renderer accepting function(data, ...) receives r_data explicitly.
png_bytes = bytes(render_data_png(r_data))
```

Add pandas only when needed. Inspect types, factor levels, and missing values after conversion when they affect plotting semantics.

## When interaction is requested

Consult `histogram_slider`, `r_histogram_renderer`, and `interactive_r_histogram` in [notebook.py](notebook.py). Define a widget in one cell, return it, and read its `.value` in a downstream plotting cell. Call the R renderer with that value and display the returned PNG bytes. This redraws a static R image on parameter changes; it does not provide linked brushing or an interactive ggplot canvas.

## Runtime checks

Use the notebook's Python environment for the import check, lint, and execution. For a uv project, useful checks are:

```bash
uv run python -m rpy2.situation
uv run python -c 'import rpy2.robjects as ro; print(ro.r("R.version.string")[0]); print(ro.r("R.home()")[0]); print(list(ro.r(".libPaths()"))); print(ro.r("as.character(packageVersion(\"ggplot2\"))")[0])'
uv run marimo check notebook.py
```

Run the renderer in a fresh process to catch hidden R setup dependencies, check that it returns nonempty PNG bytes, and inspect the image. Lint alone does not verify the R bridge. If imports fail, inspect `rpy2.situation`, the actual R library paths, and the error before changing runtime settings; do not copy a machine-specific `R_HOME` into the notebook.

The bridge uses callable R objects documented in [rpy2's function interface](https://rpy2.github.io/doc/latest/html/robjects_functions.html). Scoped conversion follows [rpy2's pandas guidance](https://rpy2.github.io/doc/latest/html/pandas.html), and display uses [marimo's image API](https://docs.marimo.io/api/media/#marimo.image). Consult these for API details rather than expanding this skill into a general manual.
