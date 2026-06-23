#!/usr/bin/env python3
# v0.2: Full extraction for gene graphs.
# Usage: python3 scripts/02_extract_v02.py
#
# Input graphs (5):
#   medaka_ncbigeneMedaka, medaka_ncbigeneHuman_usingNcbigene,
#   medaka_nlmNcbigeneHuman_usingNcbigene, medaka_medakaEnsemblGene,
#   medaka_ensembl_entrezGene_mapping
#
# Output:
#   data/raw/<graph>_triples.tsv               (audit layer, all 5 graphs)
#   data/curated/medaka_ncbigene_medaka.csv    (numeric Entrez IDs only)
#   data/curated/medaka_ncbigene_human.csv     (ncbigeneHuman + nlm merged)
#   data/curated/medaka_ensembl_gene.csv
#   data/curated/medaka_ensembl_entrez_mapping.csv (skos:exactMatch only)
#
# Each graph's object IRIs come in 3–4 IRI forms; all are normalised to a
# single canonical ID (integer string for ncbigene, ENSORLG... for ensembl).

import csv
import json
import pathlib
import re
import urllib.parse
import urllib.request

SPARQL = "https://knowledge.brc.riken.jp/sparql"
NS     = "http://metadb.riken.jp/db"

ROOT = pathlib.Path(__file__).resolve().parent.parent

SKOS_EXACT   = "http://www.w3.org/2004/02/skos/core#exactMatch"
RELATED_GENE = "http://purl.org/rbrc/resource/relatedGene"

# ensembl_entrezGene_mapping is ~360 K triples; use larger page to reduce RTTs.
PAGE_DEFAULT = 5000
PAGE_LARGE   = 10000

FETCH_GRAPHS: list[tuple[str, int]] = [
    ("medaka_ncbigeneMedaka",                    PAGE_DEFAULT),
    ("medaka_ncbigeneHuman_usingNcbigene",        PAGE_DEFAULT),
    ("medaka_nlmNcbigeneHuman_usingNcbigene",     PAGE_DEFAULT),
    ("medaka_medakaEnsemblGene",                  PAGE_DEFAULT),
    ("medaka_ensembl_entrezGene_mapping",         PAGE_LARGE),
]


# ── ID normalisers ────────────────────────────────────────────────────────────

def norm_medaka(iri: str) -> str:
    return iri.replace("http://lod.nbrp/Medaka/", "")


def norm_ncbigene(iri: str) -> str | None:
    """Return integer Entrez ID, or None for transcript / unrecognised IRIs."""
    for prefix in (
        "http://identifiers.org/ncbigene/",
        "https://identifiers.org/ncbigene:",
        "https://www.ncbi.nlm.nih.gov/gene/",
        "http://purl.uniprot.org/geneid/",
    ):
        if iri.startswith(prefix):
            val = iri[len(prefix):]
            return val if val.isdigit() else None
    return None


def norm_ensembl(iri: str) -> str | None:
    """Return ENSORLG... gene ID, or None for unrecognised IRIs."""
    for prefix in (
        "http://rdf.ebi.ac.uk/resource/ensembl/",
        "http://identifiers.org/ensembl/",
        "https://identifiers.org/ensembl:",
    ):
        if iri.startswith(prefix):
            return iri[len(prefix):]
    m = re.search(r"[?&]g=(ENSORLG\w+)", iri)
    return m.group(1) if m else None


# ── Network / I/O helpers ─────────────────────────────────────────────────────

def sparql_json(query: str) -> dict:
    params = urllib.parse.urlencode({"query": query})
    req = urllib.request.Request(
        f"{SPARQL}?{params}",
        headers={"Accept": "application/sparql-results+json"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_raw_triples(graph: str, page: int) -> list[tuple[str, str, str]]:
    iri  = f"{NS}/{graph}"
    rows: list[tuple[str, str, str]] = []
    offset = 0
    while True:
        q = (
            f"SELECT ?s ?p ?o WHERE {{ GRAPH <{iri}> {{ ?s ?p ?o }} }}"
            f" LIMIT {page} OFFSET {offset}"
        )
        batch = sparql_json(q)["results"]["bindings"]
        for b in batch:
            rows.append((b["s"]["value"], b["p"]["value"], b["o"]["value"]))
        print(f"    offset={offset:>7}  +{len(batch)}", flush=True)
        if len(batch) < page:
            break
        offset += page
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


# ── Curated builders ──────────────────────────────────────────────────────────

def curated_ncbigene_medaka(raw: pathlib.Path) -> tuple[list[str], list[list[str]]]:
    seen: set[tuple[str, str]] = set()
    rows: list[list[str]] = []
    for s, p, o in read_raw(raw):
        if p != RELATED_GENE:
            continue
        gid = norm_ncbigene(o)
        if gid is None:
            continue         # transcript ID (e.g. slc2a11b-201) — excluded
        key = (norm_medaka(s), gid)
        if key not in seen:
            seen.add(key)
            rows.append(list(key))
    rows.sort()
    return ["medaka_id", "ncbigene_id"], rows


def curated_ncbigene_human(
    raw_ncbi: pathlib.Path, raw_nlm: pathlib.Path
) -> tuple[list[str], list[list[str]]]:
    seen: set[tuple[str, str]] = set()
    rows: list[list[str]] = []
    for path in (raw_ncbi, raw_nlm):
        for s, p, o in read_raw(path):
            if p != RELATED_GENE:
                continue
            gid = norm_ncbigene(o)
            if gid is None:
                continue
            key = (norm_medaka(s), gid)
            if key not in seen:
                seen.add(key)
                rows.append(list(key))
    rows.sort()
    return ["medaka_id", "ncbigene_id"], rows


def curated_ensembl_gene(raw: pathlib.Path) -> tuple[list[str], list[list[str]]]:
    seen: set[tuple[str, str]] = set()
    rows: list[list[str]] = []
    for s, p, o in read_raw(raw):
        if p != RELATED_GENE:
            continue
        eid = norm_ensembl(o)
        if eid is None:
            continue
        key = (norm_medaka(s), eid)
        if key not in seen:
            seen.add(key)
            rows.append(list(key))
    rows.sort()
    return ["medaka_id", "ensembl_id"], rows


def curated_ensembl_entrez(raw: pathlib.Path) -> tuple[list[str], list[list[str]]]:
    seen: set[tuple[str, str]] = set()
    rows: list[list[str]] = []
    for s, p, o in read_raw(raw):
        if p != SKOS_EXACT:
            continue         # DEPENDENT / MISC — excluded
        eid = norm_ensembl(s)
        gid = norm_ncbigene(o)
        if eid is None or gid is None:
            continue
        key = (eid, gid)
        if key not in seen:
            seen.add(key)
            rows.append(list(key))
    rows.sort()
    return ["ensembl_id", "ncbigene_id"], rows


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    raw_paths: dict[str, pathlib.Path] = {}
    raw_counts: dict[str, int] = {}

    # Step 1: fetch raw triples
    for graph, page in FETCH_GRAPHS:
        print(f"\n{'='*68}")
        print(f"[raw] {graph}  (page={page})")
        print(f"{'='*68}")
        triples = fetch_raw_triples(graph, page)
        path = ROOT / "data" / "raw" / f"{graph}_triples.tsv"
        write_tsv(path, triples)
        raw_paths[graph]  = path
        raw_counts[graph] = len(triples)
        print(f"  → {len(triples)} triples  {path.relative_to(ROOT)}")

    # Step 2: build curated tables
    print(f"\n{'='*68}")
    print("Building curated tables")
    print(f"{'='*68}")

    curated_results: list[tuple[str, int]] = []

    def save(name: str, headers: list[str], rows: list[list[str]]) -> None:
        p = ROOT / "data" / "curated" / f"{name}.csv"
        write_csv(p, headers, rows)
        print(f"  {name}.csv  {len(rows)} rows")
        curated_results.append((name, len(rows)))

    h, r = curated_ncbigene_medaka(raw_paths["medaka_ncbigeneMedaka"])
    save("medaka_ncbigene_medaka", h, r)

    h, r = curated_ncbigene_human(
        raw_paths["medaka_ncbigeneHuman_usingNcbigene"],
        raw_paths["medaka_nlmNcbigeneHuman_usingNcbigene"],
    )
    save("medaka_ncbigene_human", h, r)

    h, r = curated_ensembl_gene(raw_paths["medaka_medakaEnsemblGene"])
    save("medaka_ensembl_gene", h, r)

    h, r = curated_ensembl_entrez(raw_paths["medaka_ensembl_entrezGene_mapping"])
    save("medaka_ensembl_entrez_mapping", h, r)

    # Step 3: summary
    print(f"\n{'='*68}")
    print("Summary")
    print(f"{'='*68}")
    print(f"\n{'Graph':<48} {'raw triples':>12}")
    print("-" * 62)
    for g, n in raw_counts.items():
        print(f"  {g:<46} {n:>12}")
    print(f"\n{'Table':<48} {'curated rows':>12}")
    print("-" * 62)
    for name, n in curated_results:
        print(f"  {name:<46} {n:>12}")


if __name__ == "__main__":
    main()
