---
name: gprofiler-gost
description: Run g:Profiler g:GOSt functional enrichment for user-supplied gene lists, including gene symbols, protein names, and Ensembl identifiers. Use when a user asks to perform GO enrichment, pathway enrichment, or g:GOSt analysis from a pasted list of genes or IDs, and when Codex should call the g:Profiler API and summarize the significant terms.
---

# g:GOSt Enrichment

Use this skill to run g:Profiler g:GOSt enrichment on a gene list and return a short interpretation plus machine-readable results.

## Workflow

1. Extract the genes from the user request.
2. Assume `hsapiens` unless the user gives another organism.
3. Run `scripts/run_gost.py` with `uv run`.
4. Summarize the top significant terms, grouped by source when useful.
5. Call out unmapped or suspicious inputs if the API reports fewer query genes than expected.

## Gene Input Handling

- Accept plain symbols such as `TP53 BRCA2 EGFR`.
- Accept Ensembl IDs such as `ENSG00000141510`.
- Accept mixed lists. Let g:Profiler resolve them unless the user explicitly asks for a separate conversion step.
- If the prompt contains punctuation, commas, or line breaks, normalize to one gene token per item before invoking the script.
- If the user appears to have given proteins rather than genes, still run the query and note that identifier mapping may reduce coverage.

## Command Pattern

Run the helper directly:

```bash
uv run scripts/run_gost.py TP53 BRCA2 EGFR
```

Common options:

```bash
uv run scripts/run_gost.py \
  --organism hsapiens \
  --sources GO:BP GO:MF REAC \
  --top 15 \
  --user-threshold 0.05 \
  TP53 BRCA2 EGFR
```

Use `--genes-file` for long lists:

```bash
uv run scripts/run_gost.py --genes-file genes.txt --json-out gost.json
```

## Output Expectations

The script prints:

- query metadata
- mapped query size
- data version metadata when available
- a compact table of the top terms sorted by adjusted `p_value`

When replying to the user:

- report the organism and sources used
- state how many significant terms were found
- list the strongest terms with `source`, `native`, `name`, `p_value`, and `intersection_size/query_size`
- mention whether zero terms passed threshold
- reference the JSON output path if you wrote one

## Interpretation Rules

- Treat returned `p_value` as the corrected significance value from g:Profiler.
- Do not over-interpret broad GO terms; prefer the most specific high-signal terms near the top of the result set.
- If many sources are mixed, group the summary by source instead of flattening everything into one long list.
- If there are no significant hits, say so directly and suggest checking organism, identifier type, list size, or source selection.

## Parameters Worth Changing

- `--organism`: default `hsapiens`
- `--sources`: optional subset such as `GO:BP GO:MF GO:CC REAC KEGG`
- `--user-threshold`: significance cutoff
- `--significance-threshold-method`: `g_SCS`, `fdr`, or `bonferroni`
- `--no-iea`: exclude electronically inferred GO annotations
- `--ordered`: run ordered enrichment
- `--background-file`: custom background gene list
- `--domain-scope`: use `custom` or `custom_annotated` with a background list
- `--all-results`: include non-significant rows in the JSON response

Read [references/gost-api.md](references/gost-api.md) only when you need the full parameter list or field meanings.

## Failure Handling

- If the API returns an HTTP error, show the response body if available.
- If the result set is empty, confirm whether the API returned no significant terms or the input failed to map.
- If custom background is requested, require `--domain-scope custom` or `custom_annotated`.
- If the user asks for raw output, save JSON with `--json-out`.
