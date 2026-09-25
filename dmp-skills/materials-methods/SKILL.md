---
name: materials-methods
description: Use only when the user explicitly invokes materials-methods to draft a publication-style Materials and Methods document from an analysis folder, script project, or pipeline.
metadata: {"opencode/autoinvoke": "false"}
---

# Materials and Methods

Run this workflow only when the user explicitly requests this skill by name. If loaded for a general methods-writing request, state that it requires explicit invocation and stop.

Create a source-faithful draft that a researcher can later adapt for a publication. Describe the scientific procedures implemented by the project, rather than everything that appears in its dependency list.

## Inspect the analysis

1. Set the analysis root to the directory the user names, or to the current directory if none is named. Keep the investigation and output scoped to that root, except for pipeline modules, scripts, and environment files it directly references. The default output is `<analysis-root>/docs/mm.md`, regardless of where the chat began. Honor a different output path if the user requests one; read an existing document before revising it.
2. Make a quick inventory to identify a Nextflow pipeline, a collection of scripts, or a small analysis folder. For Nextflow, trace the relevant path through `main.nf`, `workflows/`, `modules/`, configuration parameters, and called scripts; follow linked module or pipeline locations as needed. For other projects, inspect the relevant scripts, `bin/`, `Justfile`, and analysis configuration. Follow the steps that produce the analysis, not unused code or incidental utilities.
3. Record the methods-bearing steps in order: inputs and their provenance when documented, tools and algorithms, scientifically meaningful parameters and thresholds, transformations, statistical analyses, and resulting data products. Check the code behind each claim. Distinguish a configured step from evidence that it was actually run; do not invent sample counts, settings, results, or rationale.

## Resolve software versions

- Include versions of scientifically relevant tools and packages when supported by project evidence. For a pipeline, inspect the Conda environment files used by the relevant modules, including those at referenced pipeline paths. For custom Python scripts, prioritize their Conda environments and inline dependency annotations; do not inspect whatever happens to be installed in the agent's Python environment. For R, inspect recorded environments, lockfiles, and version annotations rather than treating the agent's R installation as the analysis environment.
- Judge package relevance by its scientific role. Name packages that implement a reported analysis or numerical method, such as Scanpy or NumPy when their methods matter. Omit routine data handling or execution dependencies such as pandas, Polars, uv, Typer, or requests unless their behavior is itself part of the reported scientific method.
- Treat a version range as a range, not an exact installed version. If a relevant version or other material fact is missing or conflicting, ask the user a focused question. Provide a runnable command for information only the analysis environment can supply; for example, request R package versions with `Rscript -e 'for (p in c("PACKAGE_A", "PACKAGE_B")) cat(p, as.character(packageVersion(p)), "\n")'`, to be run in the original analysis environment. Do not guess from current online releases.

## Agree on scope, then draft

After inspecting the source, present a short bullet outline of the proposed sections and methods, along with the specific uncertainties that affect the draft. Ask the user to confirm or correct it, and wait for confirmation before writing the document.

Write the confirmed draft in academic prose with active voice and first-person plural where appropriate: “We used [tool] (v. [version]) to align …”. Use separate sections when the workflow has distinct blocks. Describe methods and analytical choices, including reported thresholds, while excluding machine names, cluster resources, workflow profiles, Conda or container execution, and other operational details. Do not turn the document into a runbook, dependency inventory, results section, or discussion.

Finally, report the document path, the sections written, and any unresolved facts or weakly supported claims that need the researcher's review.
