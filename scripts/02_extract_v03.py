#!/usr/bin/env python3
# v0.3: Full extraction for remaining phenotype/similarity graphs.
# Usage: python3 scripts/02_extract_v03.py
#
# Graphs:
#   medaka_zp                    → data/curated/medaka_phenotype_zp.csv
#   medaka_medaka_similarityScore → data/curated/medaka_medaka_similarity.csv
#
# medaka_zp: flat RO:0002200 triples, same structure as medaka_hp.
# medaka_medaka_similarityScore: SIO reification identical to disease_similarityScore
#   but both SIO_628 objects are medaka IRIs. Subject IRIs use example.org namespace.
#   Pair stored with medaka_id_1 < medaka_id_2 (lexicographic) to avoid duplicates.

import csv
import json
import pathlib
import urllib.parse
import urllib.request
from collections import defaultdict

SPARQL = "https://knowledge.brc.riken.jp/sparql"
NS     = "http://metadb.riken.jp/db"
PAGE   = 5000

ROOT = pathlib.Path(__file__).resolve().parent.parent

RO_0002200 = "http://purl.obolibrary.org/obo/RO_0002200"
SIO_628    = "http://semanticscience.org/resource/SIO_000628"
SIO_216    = "http://semanticscience.org/resource/SIO_000216"
SIO_300    = "http://semanticscience.org/resource/SIO_000300"

FETCH_GRAPHS = [
    "medaka_zp",
    "medaka_medaka_similarityScore",
]


# ── ID normalisers ─────────────────────────────────────────────────────────────

def norm_medaka(iri: str) -> str:
    return iri.replace("http://lod.nbrp/Medaka/", "")


def norm_zp(iri: str) -> str | None:
    prefix = "http://purl.obolibrary.org/obo/ZP_"
    if iri.startswith(prefix):
        return "ZP:" + iri[len(prefix):]
    return None


# ── Network / I/O helpers ──────────────────────────────────────────────────────

def sparql_json(query: str) -> dict:
    params = urllib.parse.urlencode({"query": query})
    req = urllib.request.Request(
        f"{SPARQL}?{params}",
        headers={"Accept": "application/sparql-results+json"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_raw_triples(graph: str) -> list[tuple[str, str, str]]:
    iri  = f"{NS}/{graph}"
    rows: list[tuple[str, str, str]] = []
    offset = 0
    while True:
        q = (
            f"SELECT ?s ?p ?o WHERE {{ GRAPH <{iri}> {{ ?s ?p ?o }} }}"
            f" LIMIT {PAGE} OFFSET {offset}"
        )
        batch = sparql_json(q)["results"]["bindings"]
        for b in batch:
            rows.append((b["s"]["value"], b["p"]["value"], b["o"]["value"]))
        print(f"    offset={offset:>7}  +{len(batch)}", flush=True)
        if len(batch) < PAGE:
            break
        offset += PAGE
    return rows


def write_tsv(path: pathlib.Path, rows: list[tuple[str, str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        f.write("s\tp\to\n")
        for row in rows:
            f.write("\t".join(row) + "\n")


def write_csv(path: pathlib.Path, headers: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(headers)
        w.writerows(rows)


def read_raw(path: pathlib.Path) -> list[tuple[str, str, str]]:
    with path.open(encoding="utf-8") as f:
        return [(r["s"], r["p"], r["o"]) for r in csv.DictReader(f, delimiter="\t")]


# ── Curated builders ───────────────────────────────────────────────────────────

def curated_phenotype_zp(raw: pathlib.Path) -> tuple[list[str], list[list[str]]]:
    seen: set[tuple[str, str]] = set()
    rows: list[list[str]] = []
    for s, p, o in read_raw(raw):
        if p != RO_0002200:
            continue
        zp = norm_zp(o)
        if zp is None:
            continue
        key = (norm_medaka(s), zp)
        if key not in seen:
            seen.add(key)
            rows.append(list(key))
    rows.sort()
    return ["medaka_id", "zp_id"], rows


def curated_medaka_similarity(raw: pathlib.Path) -> tuple[list[str], list[list[str]]]:
    """SIO reification: both SIO_628 objects are medaka IRIs.
    Pair is ordered lexicographically (medaka_id_1 < medaka_id_2).
    Subject IRIs use example.org namespace and are not used for ID extraction.
    """
    po: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for s, p, o in read_raw(raw):
        po[s].append((p, o))

    metric_score: dict[str, str] = {}
    assocs: list[dict] = []

    for subj, pairs in po.items():
        by_pred: dict[str, list[str]] = defaultdict(list)
        for p, o in pairs:
            by_pred[p].append(o)

        if SIO_300 in by_pred:
            metric_score[subj] = by_pred[SIO_300][0]

        refs    = by_pred.get(SIO_628, [])
        metrics = by_pred.get(SIO_216, [])
        if len(refs) >= 2 and metrics:
            medaka_iris = [r for r in refs if "lod.nbrp" in r]
            if len(medaka_iris) >= 2:
                ids = sorted(norm_medaka(r) for r in medaka_iris)
                assocs.append({"id1": ids[0], "id2": ids[1], "metric": metrics[0]})

    rows: list[list[str]] = []
    for a in assocs:
        score = metric_score.get(a["metric"], "NA")
        rows.append([a["id1"], a["id2"], score])
    rows.sort()
    return ["medaka_id_1", "medaka_id_2", "score"], rows


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    raw_paths: dict[str, pathlib.Path] = {}
    raw_counts: dict[str, int] = {}

    for graph in FETCH_GRAPHS:
        print(f"\n{'='*68}")
        print(f"[raw] {graph}")
        print(f"{'='*68}")
        triples = fetch_raw_triples(graph)
        path = ROOT / "data" / "raw" / f"{graph}_triples.tsv"
        write_tsv(path, triples)
        raw_paths[graph]  = path
        raw_counts[graph] = len(triples)
        print(f"  → {len(triples)} triples  {path.relative_to(ROOT)}")

    print(f"\n{'='*68}")
    print("Building curated tables")
    print(f"{'='*68}")

    curated_results: list[tuple[str, int]] = []

    def save(name: str, headers: list[str], rows: list[list[str]]) -> None:
        p = ROOT / "data" / "curated" / f"{name}.csv"
        write_csv(p, headers, rows)
        print(f"  {name}.csv  {len(rows)} rows")
        curated_results.append((name, len(rows)))

    h, r = curated_phenotype_zp(raw_paths["medaka_zp"])
    save("medaka_phenotype_zp", h, r)

    h, r = curated_medaka_similarity(raw_paths["medaka_medaka_similarityScore"])
    save("medaka_medaka_similarity", h, r)

    print(f"\n{'='*68}")
    print("Summary")
    print(f"{'='*68}")
    print(f"\n{'Graph':<45} {'raw triples':>12}")
    print("-" * 60)
    for g, n in raw_counts.items():
        print(f"  {g:<43} {n:>12}")
    print(f"\n{'Table':<45} {'curated rows':>12}")
    print("-" * 60)
    for name, n in curated_results:
        print(f"  {name:<43} {n:>12}")


if __name__ == "__main__":
    main()
