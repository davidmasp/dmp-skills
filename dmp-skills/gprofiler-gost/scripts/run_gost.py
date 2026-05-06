#!/usr/bin/env python3

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

API_URL = "https://biit.cs.ut.ee/gprofiler/api/gost/profile/"
DATA_VERSIONS_URL = "https://biit.cs.ut.ee/gprofiler/api/util/data_versions"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run g:Profiler g:GOSt enrichment for a list of genes."
    )
    parser.add_argument("genes", nargs="*", help="Gene symbols or identifiers.")
    parser.add_argument("--genes-file", help="Path to a file containing genes.")
    parser.add_argument("--organism", default="hsapiens", help="g:Profiler organism ID.")
    parser.add_argument("--sources", nargs="*", default=None, help="Optional source IDs.")
    parser.add_argument(
        "--user-threshold",
        type=float,
        default=None,
        help="Custom significance threshold between 0 and 1.",
    )
    parser.add_argument(
        "--significance-threshold-method",
        choices=["g_SCS", "fdr", "bonferroni"],
        default=None,
        help="Multiple-testing correction method.",
    )
    parser.add_argument("--all-results", action="store_true", help="Include non-significant rows.")
    parser.add_argument("--ordered", action="store_true", help="Run ordered enrichment.")
    parser.add_argument("--combined", action="store_true", help="Combine named multi-query lists.")
    parser.add_argument(
        "--measure-underrepresentation",
        action="store_true",
        help="Return underrepresented terms.",
    )
    parser.add_argument("--no-iea", action="store_true", help="Exclude electronic GO annotations.")
    parser.add_argument(
        "--domain-scope",
        choices=["annotated", "known", "custom", "custom_annotated"],
        default=None,
        help="Statistical domain scope.",
    )
    parser.add_argument(
        "--numeric-ns",
        default=None,
        help="Namespace to assume for numeric IDs.",
    )
    parser.add_argument(
        "--background-file",
        help="Path to a file containing one background gene per line.",
    )
    parser.add_argument(
        "--no-evidences",
        action="store_true",
        help="Skip evidence lookup for faster responses.",
    )
    parser.add_argument("--highlight", action="store_true", help="Request highlighted GO results.")
    parser.add_argument(
        "--json-out",
        help="Write the full JSON response to this path.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of rows to print in the summary table.",
    )
    return parser.parse_args()


def load_tokens(path):
    content = Path(path).read_text(encoding="utf-8")
    return normalize_gene_tokens(content)


def normalize_gene_tokens(text):
    translation = str.maketrans({
        ",": " ",
        ";": " ",
        "\n": " ",
        "\t": " ",
        "\r": " ",
    })
    return [token for token in text.translate(translation).split(" ") if token]


def build_payload(args, genes):
    payload = {
        "organism": args.organism,
        "query": genes,
    }
    if args.sources is not None:
        payload["sources"] = args.sources
    if args.user_threshold is not None:
        payload["user_threshold"] = args.user_threshold
    if args.significance_threshold_method is not None:
        payload["significance_threshold_method"] = args.significance_threshold_method
    if args.all_results:
        payload["all_results"] = True
    if args.ordered:
        payload["ordered"] = True
    if args.combined:
        payload["combined"] = True
    if args.measure_underrepresentation:
        payload["measure_underrepresentation"] = True
    if args.no_iea:
        payload["no_iea"] = True
    if args.domain_scope is not None:
        payload["domain_scope"] = args.domain_scope
    if args.numeric_ns is not None:
        payload["numeric_ns"] = args.numeric_ns
    if args.no_evidences:
        payload["no_evidences"] = True
    if args.highlight:
        payload["highlight"] = True
    if args.background_file:
        background = load_tokens(args.background_file)
        payload["background"] = background
    return payload


def fetch_json(url, payload=None):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "uv-run-gprofiler-gost-skill",
    }
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method="POST" if payload else "GET")
    with urllib.request.urlopen(request) as response:
        return json.load(response)


def maybe_get_data_versions(organism):
    url = f"{DATA_VERSIONS_URL}?organism={organism}"
    try:
        return fetch_json(url)
    except Exception:
        return None


def print_metadata(payload, response):
    result = response.get("result", [])
    meta = response.get("meta", {})
    genes_metadata = meta.get("genes_metadata", {})
    query_entries = genes_metadata.get("query", {})
    mapped_ensgs = []
    for entry in query_entries.values():
        mapped_ensgs.extend(entry.get("ensgs", []))
    failed = genes_metadata.get("failed", [])
    duplicates = genes_metadata.get("duplicates", [])
    ambiguous = genes_metadata.get("ambiguous", {})

    print(f"organism: {payload['organism']}")
    print(f"input_gene_count: {len(payload['query'])}")
    print(f"mapped_gene_count: {len(mapped_ensgs)}")
    print(f"result_count: {len(result)}")
    if "sources" in payload:
        sources = payload["sources"] or []
        print(f"sources: {', '.join(sources) if sources else 'all'}")
    else:
        print("sources: all")
    if failed:
        print(f"failed_genes: {', '.join(failed)}")
    if duplicates:
        print(f"duplicate_genes: {', '.join(duplicates)}")
    if ambiguous:
        print(f"ambiguous_gene_count: {len(ambiguous)}")


def print_data_versions(versions, selected_sources=None):
    if not versions:
        return
    if not isinstance(versions, dict):
        return
    gprofiler_version = versions.get("gprofiler_version")
    if gprofiler_version:
        print(f"gprofiler_version: {gprofiler_version}")
    sources = versions.get("sources")
    if isinstance(sources, dict):
        source_preview = []
        source_ids = sorted(sources)
        if selected_sources:
            source_ids = [source_id for source_id in selected_sources if source_id in sources]
        for source_id in source_ids[:5]:
            version = sources[source_id].get("version", "")
            compact = version.splitlines()[0] if isinstance(version, str) else str(version)
            source_preview.append(f"{source_id}={compact}")
        if source_preview:
            print(f"source_versions: {', '.join(source_preview)}")


def summarize_rows(rows, top_n):
    if not rows:
        print("No result rows returned.")
        return

    sorted_rows = sorted(rows, key=lambda row: row.get("p_value", 1.0))
    print("")
    print("top_terms:")
    print("source\tnative\tp_value\tintersection\tquery_size\tterm_size\tname")
    for row in sorted_rows[:top_n]:
        source = row.get("source", "")
        native = row.get("native", "")
        p_value = row.get("p_value", "")
        intersection = row.get("intersection_size", "")
        query_size = row.get("query_size", "")
        term_size = row.get("term_size", "")
        name = row.get("name", "")
        print(f"{source}\t{native}\t{p_value}\t{intersection}\t{query_size}\t{term_size}\t{name}")


def main():
    args = parse_args()
    genes = list(args.genes)
    if args.genes_file:
        genes.extend(load_tokens(args.genes_file))
    if not genes:
        print("Provide genes as positional arguments or via --genes-file.", file=sys.stderr)
        return 2
    if args.background_file and args.domain_scope not in {"custom", "custom_annotated"}:
        print(
            "--background-file requires --domain-scope custom or custom_annotated.",
            file=sys.stderr,
        )
        return 2
    if args.user_threshold is not None and not 0 <= args.user_threshold <= 1:
        print("--user-threshold must be between 0 and 1.", file=sys.stderr)
        return 2

    payload = build_payload(args, genes)

    try:
        response = fetch_json(API_URL, payload)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP error: {exc.code}", file=sys.stderr)
        print(body, file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"Network error: {exc}", file=sys.stderr)
        return 1

    if args.json_out:
        out_path = Path(args.json_out)
        out_path.write_text(json.dumps(response, indent=2, sort_keys=True), encoding="utf-8")
        print(f"json_out: {out_path}")

    print_metadata(payload, response)
    versions = maybe_get_data_versions(args.organism)
    print_data_versions(versions, payload.get("sources"))
    summarize_rows(response.get("result", []), args.top)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
