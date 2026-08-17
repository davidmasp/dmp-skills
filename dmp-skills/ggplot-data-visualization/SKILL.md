---
name: ggplot-data-visualization
description: Create, revise, and review data visualizations in R with ggplot2, using consistent themes, typography, axis expansion, categorical palettes, labels, legends, and export settings. Use when writing R plotting code, replacing base R plots, choosing a plot type, styling related panels, or preparing figures for reports and publications.
---

# ggplot2 data visualization

Use ggplot2 for new R data visualizations by default. Use base R graphics only when the user explicitly requests them, an existing figure must be preserved, or ggplot2 is genuinely unsuitable. Prefer a clear, honest, readable figure over decorative styling.

## Workflow

1. Identify the analytical question, the variables and their types, grouping, units, and whether the data are raw observations or summaries.
2. Choose the simplest suitable ggplot2 geometry. Keep mappings in `aes()` and put fixed aesthetics outside it.
3. Apply the shared style below unless the user, project, journal, or existing figure specifies another style.
4. Make scales, labels, ordering, legends, and uncertainty explicit.
5. Inspect the rendered figure at its intended output size. Check readability, axis meaning, clipping, palette consistency, and whether the visual comparison is fair.
6. Save with explicit dimensions and resolution when creating a file; do not rely on the device default.

## Shared style

Use this as the default scaffold, adapting only what the plot needs:

```r
library(ggplot2)

p <- ggplot(df, aes(x = group, y = value, fill = group)) +
  geom_col() +
  scale_fill_brewer(palette = "Set1") +
  theme_classic() +
  theme(
    text = element_text(size = 8),
    legend.key.size = grid::unit(0.1, "in")
  ) +
  labs(x = NULL, y = "Value (unit)", fill = NULL)
```

- Use `theme_classic()` when relevant, especially for clean report or publication figures. Respect an explicit project theme or a user-requested theme.
- Set the general text size with `theme(text = element_text(size = 8))`. Add targeted size changes only when required for hierarchy or legibility; keep labels and legends proportionate.
- Set legend keys to `theme(legend.key.size = grid::unit(0.1, "in"))` unless the figure has a specific reason to use a larger key.
- Write informative axis labels with units, concise titles, and captions or subtitles when they clarify the comparison. Remove redundant labels with `NULL` rather than leaving unexplained defaults.
- Order categorical axes deliberately. Use factor levels, `reorder()`, or explicit scale limits; never make an important order depend on incidental input order.
- Rotate likely-long x-axis labels without running code merely to measure them. Use `theme(axis.text.x = element_text(angle = 45, hjust = 1, vjust = 1))`; use a 90-degree rotation or `coord_flip()` when labels remain crowded. Check that the final rendered labels are not clipped.

## Scales and baselines

Anchor plots that should meet the lower x-axis—especially bar/column plots, histograms, density plots, areas, and similar nonnegative displays—at zero while leaving modest headroom:

```r
scale_y_continuous(expand = expansion(mult = c(0, 0.05)))
```

Use the matching scale when the numeric axis is horizontal, for example after `coord_flip()`:

```r
scale_x_continuous(expand = expansion(mult = c(0, 0.05)))
```

Use this rule when zero is meaningful and the geometry is expected to start at the baseline. Do not force zero for quantities where a truncated axis is analytically appropriate; explain or label such a choice. For bar charts, keep the value axis at zero unless the user explicitly requests a different treatment.

For continuous scales, prefer explicit breaks, labels, limits, and units when they improve interpretation. Use `coord_cartesian()` to zoom without dropping data; use scale limits only when filtering is intentional. Avoid unnecessary dual axes.

## Color and related plots

For categorical variables, use RColorBrewer palettes by default, preferentially `Set1` for strong, high-contrast categories and `Set3` for softer multi-category displays:

```r
scale_color_brewer(palette = "Set1")
scale_fill_brewer(palette = "Set1")
```

Use the same palette and category-to-color mapping across related plots, facets, or separate panels. Define a named palette once and reuse it rather than allowing each plot to assign colors in a different order:

```r
groups <- c("Control", "Treatment A", "Treatment B")
group_colors <- setNames(
  RColorBrewer::brewer.pal(length(groups), "Set1"),
  groups
)

scale_fill_manual(values = group_colors, limits = groups, drop = FALSE)
scale_color_manual(values = group_colors, limits = groups, drop = FALSE)
```

Use a palette with enough distinct colors for the number of categories. For continuous data, use a perceptually ordered continuous scale rather than forcing a categorical palette. If color carries essential meaning, add a non-color cue such as shape, linetype, direct labels, or faceting. When Set1 or Set3 would be difficult to distinguish for the audience, prefer an accessible alternative such as a colorblind-safe palette or `viridis`, and state the adaptation briefly.

Keep legends concise and consistent: give them a meaningful title or remove a redundant title, order entries intentionally, and avoid duplicate legends for the same variable. Use direct labels when they reduce decoding effort without causing clutter.

## Geometry guidance

- Use `geom_col()` when values are already summarized and `geom_bar()` with the correct `stat` when counts or another aggregation should be computed.
- Use points plus a summary or interval layer when individual observations matter. Avoid hiding distributions behind bars when a dot, boxplot, violin, or jittered display communicates the data better.
- For density plots, histograms, and areas, use a baseline-aware y scale as above and make the statistic and units clear.
- Use lines only when x has a meaningful order or continuity. Preserve group identity with color, linetype, or facets; do not connect unrelated categories.
- Use error bars or ribbons only when the interval definition is known and label it in the caption or legend (for example, SD, SE, or 95% CI). Do not imply uncertainty that was not calculated.
- Use faceting to compare panels with a shared visual grammar. Keep scales fixed when magnitude comparisons matter; use free scales only when differences in within-panel pattern are the point and label that choice clearly.

## Reusable plot components

When several figures share a style, define reusable objects or functions for the theme, palette, common scales, and labels. Keep the palette object outside individual plot expressions so later plots cannot silently remap categories.

```r
plot_theme <- theme_classic() +
  theme(
    text = element_text(size = 8),
    legend.key.size = grid::unit(0.1, "in")
  )

baseline_y <- scale_y_continuous(expand = expansion(mult = c(0, 0.05)))

p1 <- base_plot + plot_theme + baseline_y +
  scale_fill_manual(values = group_colors, limits = groups, drop = FALSE)
p2 <- other_plot + plot_theme + baseline_y +
  scale_fill_manual(values = group_colors, limits = groups, drop = FALSE)
```

Do not duplicate near-identical style code across panels if a named object or small helper makes consistency easier to verify.

## Export and QA

Render and inspect the actual output, especially when labels are rotated or the figure will be reduced in size. Confirm that:

- text remains legible at the intended dimensions and general text is 8 pt unless a deliberate exception is needed;
- legend keys are 0.1 in unless a larger key is explicitly justified by the geometry or audience;
- bars, densities, and comparable nonnegative geoms meet the baseline when appropriate;
- labels include units and are not clipped or ambiguous;
- colors, category order, and legends match related figures;
- the chosen geometry does not conceal raw data or exaggerate differences;
- missing values, zero values, transformations, and uncertainty are handled honestly.

Use explicit output settings, for example:

```r
ggsave("figure.png", p, width = 90, height = 70, units = "mm", dpi = 300)
```

Adapt dimensions, device, and resolution to the destination. Preserve the plot object so it can be re-rendered after review.
