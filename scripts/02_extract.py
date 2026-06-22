#!/usr/bin/env python3
# Day1 (1-4): Full extraction for the 4 core graphs.
# Usage: python3 scripts/02_extract.py
# Output:
#   data/raw/<graph>_triples.tsv  -- s, p, o raw triples (audit layer)
#   data/curated/<graph>.csv      -- shaped table
#
# medaka_disease_similarityScore is built from the raw TSV in Python instead of
# running the SPARQL join directly: the endpoint returns incomplete results for
# the same-predicate-twice join pattern (SIO:628 × 2). See queries/ file for details.

import csv
import json
import pathlib
import urllib.parse
import urllib.request
from collections import defaultdict

SPARQL = "https://knowledge.brc.riken.jp/sparql"
NS     = "http://metadb.riken.jp/db"
PAGE   = 5000

# graph name → extraction SPARQL file (or None → use raw-TSV parser)
GRAPHS = {
    "medaka_test":                           "queries/medaka_strains.rq",
    "medaka_disease_similarityScore":        None,   # built from raw TSV
    "medaka_diseaseID_throughMedgen_direct": "queries/medaka_disease_gene.rq",
    "medaka_hp":                             "queries/medaka_phenotype_hp.rq",
}

ROOT = pathlib.Path(__file__).resolve().parent.parent

SIO_628 = "http://semanticscience.org/resource/SIO_000628"
SIO_216 = "http://semanticscience.org/resource/SIO_000216"
SIO_300 = "http://semanticscience.org/resource/SIO_000300"


def sparql_json(query: str) -> dict:
    params = urllib.parse.urlencode({"query": query})
    req = urllib.request.Request(
        f"{SPARQL}?{params}",
        headers={"Accept": "application/sparql-results+json"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_raw_triples(graph_iri: str) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    offset = 0
    while True:
        q = (
            f"SELECT ?s ?p ?o WHERE {{ GRAPH <{graph_iri}> {{ ?s ?p ?o }} }}"
            f" LIMIT {PAGE} OFFSET {offset}"
        )
        batch = sparql_json(q)["results"]["bindings"]
        for b in batch:
            rows.append((b["s"]["value"], b["p"]["value"], b["o"]["value"]))
        print(f"    page offset={offset:>6}  got {len(batch)} triples", flush=True)
        if len(batch) < PAGE:
            break
        offset += PAGE
    return rows


def fetch_curated(query_text: str) -> tuple[list[str], list[list[str]]]:
    data = sparql_json(query_text)
    vars_ = data["head"]["vars"]
    rows: list[list[str]] = []
    for b in data["results"]["bindings"]:
        row = [b.get(v, {}).get("value") or "NA" for v in vars_]
        rows.append(row)
    return vars_, rows


def curated_similarity_from_raw(raw_path: pathlib.Path) -> tuple[list[str], list[list[str]]]:
    """Build medaka_disease_similarity by joining raw triples in Python.

    The SPARQL endpoint returns incomplete results for the same-predicate-twice
    join (SIO:628 × 2) when medaka IRI is bound via FILTER.  Parsing the raw TSV
    locally avoids that endpoint quirk and guarantees all associations are captured.
    """
    po: dict[str, list[tuple[str, str]]] = defaultdict(list)
    with raw_path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            po[row["s"]].append((row["p"], row["o"]))

    metric_score: dict[str, str] = {}
    assocs: list[dict] = []

    for subj, pairs in po.items():
        by_pred: dict[str, list[str]] = defaultdict(list)
        for p, o in pairs:
            by_pred[p].append(o)

        # Metric node: has SIO_000300
        if SIO_300 in by_pred:
            metric_score[subj] = by_pred[SIO_300][0]

        # Association node: has SIO_000628 twice and SIO_000216
        refs = by_pred.get(SIO_628, [])
        metrics = by_pred.get(SIO_216, [])
        if len(refs) >= 2 and metrics:
            medaka_iris  = [r for r in refs if "lod.nbrp" in r]
            disease_iris = [r for r in refs if "lod.nbrp" not in r]
            if medaka_iris and disease_iris:
                assocs.append({
                    "medaka":  medaka_iris[0],
                    "disease": disease_iris[0],
                    "metric":  metrics[0],
                })

    rows: list[list[str]] = []
    for a in assocs:
        score = metric_score.get(a["metric"], "NA")
        medaka_id  = a["medaka"].replace("http://lod.nbrp/Medaka/", "")
        disease    = a["disease"]
        if "orphanet" in disease:
            disease_id     = "Orphanet:" + disease.replace("http://identifiers.org/orphanet/", "")
            disease_source = "ordo"
        else:
            disease_id     = "OMIM:" + disease.replace("http://purl.bioontology.org/ontology/OMIM/", "")
            disease_source = "omim"
        rows.append([medaka_id, disease_id, disease_source, score])

    rows.sort(key=lambda r: (r[0], r[1]))
    headers = ["medaka_id", "disease_id", "disease_source", "score"]
    return headers, rows


def write_tsv(path: pathlib.Path, rows: list[tuple[str, str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write("s\tp\to\n")
        for row in rows:
            f.write("\t".join(row) + "\n")


def write_csv(path: pathlib.Path, headers: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)


def main() -> None:
    summary: list[tuple[str, int, int]] = []

    for graph, query_file in GRAPHS.items():
        iri = f"{NS}/{graph}"
        print(f"\n{'='*68}")
        print(f"Graph: {graph}")
        print(f"{'='*68}")

        # raw triples
        print("  [raw] fetching all triples...")
        triples = fetch_raw_triples(iri)
        raw_path = ROOT / "data" / "raw" / f"{graph}_triples.tsv"
        write_tsv(raw_path, triples)
        print(f"  [raw] {len(triples)} triples → {raw_path.relative_to(ROOT)}")

        # curated
        curated_path = ROOT / "data" / "curated" / f"{graph}.csv"
        if query_file is None:
            # Build from raw TSV (endpoint quirk workaround)
            print("  [curated] building from raw TSV (Python join)...")
            headers, rows = curated_similarity_from_raw(raw_path)
        else:
            qpath = ROOT / query_file
            print(f"  [curated] running {qpath.relative_to(ROOT)}...")
            headers, rows = fetch_curated(qpath.read_text(encoding="utf-8"))

        write_csv(curated_path, headers, rows)
        print(f"  [curated] {len(rows)} rows → {curated_path.relative_to(ROOT)}")

        summary.append((graph, len(triples), len(rows)))

    print(f"\n{'='*68}")
    print("件数サマリー")
    print(f"{'='*68}")
    print(f"{'graph':<45}  {'raw triples':>12}  {'curated rows':>12}")
    print("-" * 68)
    for graph, raw_n, cur_n in summary:
        print(f"{graph:<45}  {raw_n:>12}  {cur_n:>12}")


if __name__ == "__main__":
    main()
