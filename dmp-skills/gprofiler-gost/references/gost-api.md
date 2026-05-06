# g:Profiler g:GOSt Reference

Use this file only when you need parameter or field details that are too long for `SKILL.md`.

## Core Request Shape

POST `https://biit.cs.ut.ee/gprofiler/api/gost/profile/`

Minimum payload:

```json
{
  "organism": "hsapiens",
  "query": ["TP53", "BRCA2", "EGFR"]
}
```

## Frequently Used Parameters

- `organism`: species ID, for example `hsapiens`
- `query`: list of genes or a dictionary of named lists for multi-query mode
- `sources`: list of source IDs such as `GO:BP`, `GO:MF`, `GO:CC`, `KEGG`, `REAC`, `WP`, `TF`, `MIRNA`, `HPA`, `CORUM`, `HP`
- `user_threshold`: significance cutoff between 0 and 1
- `all_results`: include rows below threshold
- `ordered`: enable ordered enrichment
- `combined`: combine multiple named queries
- `measure_underrepresentation`: return underrepresented terms
- `no_iea`: exclude electronically inferred GO annotations
- `domain_scope`: `annotated`, `known`, `custom`, or `custom_annotated`
- `numeric_ns`: namespace to assume for numeric IDs
- `significance_threshold_method`: `g_SCS`, `bonferroni`, or `fdr`
- `background`: custom background gene list
- `output`: keep as `json`
- `no_evidences`: skip evidence lookup for faster responses
- `highlight`: request highlighted GO results

## Important Result Fields

- `name`: term name
- `native`: source-native term ID
- `p_value`: corrected enrichment p-value
- `significant`: boolean significance flag
- `source`: datasource abbreviation
- `intersection_size`: overlap between query and term
- `term_size`: genes annotated to the term
- `query_size`: genes considered in the tested query
- `precision`: `intersection_size / query_size`
- `recall`: `intersection_size / term_size`
- `intersections`: gene-level overlap annotations
- `effective_domain_size`: statistical universe size

## Practical Notes

- Empty `sources` means all supported sources for the organism.
- `query_size` can be smaller than the original list after mapping or background filtering.
- Mixed identifier types are acceptable, but mapping quality may vary.
- For large user prompts, clean the list first and then pass the normalized tokens to the script.
