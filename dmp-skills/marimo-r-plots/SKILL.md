---
name: marimo-r-plots
description: "Explicit-only integration skill for running R/ggplot2 code through rpy2 and displaying the resulting figures in marimo notebooks. Use when explicitly invoked as $marimo-r-plots. Default to static plots; implement interactive controls or reactive redraws only when the user explicitly requests them, even though the bundled example includes interaction."
---

# R plots in marimo

Keep this skill focused on the Python-to-R-to-image bridge. Preserve the notebook's existing environment and analytical intent.

## Integration workflow

1. Inspect the notebook and its dependency configuration. Use Python `marimo` and `rpy2`, a working local R runtime, and the required R packages (`ggplot2` for ggplots). Python dependency metadata does not install R or its packages. Verify the R runtime visible to `rpy2`, rather than assuming it matches a terminal R session.
2. Read [the integration patterns](references/integration.md) when implementing the bridge. The [original notebook](references/notebook.py) is an exact example snapshot; consult it for concrete cell structure or, only when requested, its slider-driven histogram.
3. Define R plotting functions through `rpy2.robjects.r`, return their callable objects as Python cell outputs, and pass data and parameters as function arguments. Keep input dependencies visible in Python; marimo cannot track assignments or package loading hidden inside R's shared environment. Prefer namespaced R calls or loading packages inside the function over relying on another plot cell's side effects.
4. Render with `ggsave(plot=..., width=..., height=..., units=..., dpi=...)`. For inline figures, prefer the example's temporary PNG → R raw vector → Python `bytes` → `mo.image()` pattern. Clean up temporary files after reading them. Use a deliberate output path when the user requests a saved figure; avoid shared fixed `/tmp` names for inline rendering.
5. Display `mo.image(png_bytes)` as the plotting cell's final expression. Use fixed parameters by default. Add widgets and `.value` dependencies only when the user explicitly requests interaction; invoking this skill alone is not such a request.
6. Run `marimo check` in the notebook's environment and execute the R renderer. Inspect the actual image. If interaction was requested, verify that two parameter values produce different renders. Report any missing-runtime limitation separately from notebook syntax validation.

## Companion skills

Load these when available and relevant; keep their detailed guidance in their own skills:

- **`ggplot-data-visualization`**: plot design, themes, scales, labels, palettes, and export quality. It is maintained in this repository at `dmp-skills/ggplot-data-visualization/SKILL.md`.
- **`marimo-notebook`**: notebook format, cell structure, and general marimo behavior. It is registered in this repository from `external/marimo-team/skills/skills/marimo-notebook/SKILL.md`.

Locate companions through the installed skill catalog or the repository checkout; those repository paths are not relative to this skill directory. If unavailable, continue with the integration guidance here. The example's `theme_minimal()`, full-width layout, explanatory accordion, and slider are demonstration choices, not requirements for new notebooks.
