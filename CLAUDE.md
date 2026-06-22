# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

Extract medaka (*Oryzias latipes*) RDF knowledge graph data from RIKEN BioResource and distribute it as SQL-loadable flat files (CSV/TSV/JSON + schema + codebook + provenance) for external researchers unfamiliar with RDF/SPARQL.

The scientific goal: let researchers identify medaka strains as candidate human disease models via two inference pathways:
- **Path A (gene)**: medaka strain → medaka gene → human ortholog gene → human disease
- **Path B (phenotype similarity)**: medaka phenotype ↔ human disease phenotype cosine similarity

`medaka_test` is the anchor table for both paths. `medaka_diseaseID_throughMedgen_direct` = Path A result. `medaka_disease_similarityScore` = Path B result.

**DESIGN.md** is the authoritative design document — read it before making architectural decisions. It is also uploaded as a Claude Project persistent knowledge.

## Data Sources

- **SPARQL endpoint**: `https://knowledge.brc.riken.jp/sparql`
- **SPARQList REST API**: `https://splist.brc.riken.jp/sparqlist/api/medaka_sample_by_graph?graph=<GRAPH_IRI>&limit=&offset=`
- **Graph IRI prefix**: `http://metadb.riken.jp/db/<graph>` — this is the SPARQL query namespace; `https://knowledge.brc.riken.jp/bioresource/upload/db/<graph>` is the upload path only, not for queries
- **License**: CC BY — always include source graph IRI and retrieval date in distributed files

## Scripts

```bash
# Day0: Connectivity check — tests all 13 candidate graphs against both IRI namespaces
bash scripts/00_check_graphs.sh

# Day1: Predicate frequency + sample extraction for the 4 core graphs
python3 scripts/01_inspect.py
```

`01_inspect.py` queries the live SPARQL endpoint (no local data needed). Output goes to stdout; redirect to `output/` for reference. The script covers the 4 core graphs: `medaka_test`, `medaka_disease_similarityScore`, `medaka_diseaseID_throughMedgen_direct`, `medaka_hp`.

## Target Graphs and Distribution Plan

13 graphs total; distribution status from DESIGN.md §3:

| Graph | Distribute | Notes |
|---|---|---|
| `medaka_test` | ✓ | Anchor for all joins |
| `medaka_disease_similarityScore` | ✓ | Core — Path B disease inference |
| `medaka_diseaseID_throughMedgen_direct` | ✓ | Core — Path A disease inference |
| `medaka_hp` | ✓ | Core — medaka→HP phenotype mapping |
| `medaka_zp` | pending | Path B raw data |
| `medaka_ncbigeneMedaka` | ✓ | Path A gene (Entrez) |
| `medaka_ncbigeneHuman_usingNcbigene` | ✓ | Path A — merge with nlm variant into 1 table |
| `medaka_nlmNcbigeneHuman_usingNcbigene` | ✓ merged | Same content as above, different IRI prefix |
| `medaka_medakaEnsemblGene` | pending | Path A gene (Ensembl) |
| `medaka_ensembl_entrezGene_mapping` | shared lookup | FK bridge, not standalone |
| `medaka_medaka_similarityScore` | pending | medaka↔medaka similarity |
| `medaka_ordo_similarityScore` | ✗ | Subset of `disease_similarityScore` |
| `medaka_omim_similarityScore` | ✗ | Subset of `disease_similarityScore` |

v0.1 = core 4 graphs; v0.2 = gene graphs.

## Join Keys

- **Medaka strain ID** (`http://lod.nbrp/Medaka/<id>`) — common join key across all graphs. IDs appear in both `MT104` and `337` formats; normalization needed (see DESIGN.md §3).
- **Gene**: `identifiers.org/ncbigene/...` links `ncbigeneMedaka` ↔ `ncbigeneHuman`; `ENSORLG...` for Ensembl, bridged via `ensembl_entrezGene_mapping`.
- **Disease**: ordo (`identifiers.org/orphanet/...`) and omim (`purl.bioontology.org/ontology/OMIM/...`) IDs link Path A and Path B results.

## RDF Schema — `*_similarityScore` Graphs

These use reification: each association is a blank node with:
- `sio:SIO_000628` (refers to) → medaka IRI
- `sio:SIO_000628` (refers to) → disease IRI
- `sio:SIO_000216` (has measurement value) → metric node
  - `sio:SIO_000300` (has value) → float score

Planned curated table shape: `(medaka_id, medaka_label, disease_id, disease_source[ordo|omim], measure[jaccard|dice|simpson|cosine], score)` with PK=(medaka_id, disease_id, measure).

## Planned Repository Structure

```
medaka-apis/
├── queries/          # SPARQL files per graph
├── scripts/          # extract.sh (batch curl), build.py (JSON→CSV/schema)
├── data/
│   ├── raw/          # <graph>_triples.tsv (audit layer)
│   └── curated/      # <graph>.{csv,tsv,json} (distribution layer)
├── schema/           # <graph>.schema.sql (CREATE TABLE DDL)
├── metadata/         # codebook.csv, predicate_catalog.csv, provenance.json, manifest.csv
└── SHA256SUMS
```

## Key Design Rules (from DESIGN.md §7 and §9)

- **Never invent column definitions** — derive them from actual SPARQL samples and predicate frequencies first.
- Missing values → `NA` (unified). Encoding: UTF-8, line endings: LF.
- Both machine ID and human-readable label must appear in every curated table.
- `metadata/manifest.csv` is the single source of truth for what's new vs. unchanged across releases.
- The pipeline (`extract.sh` / `build.py`) must be idempotent and config-driven — re-running only generates missing files.
- Do not work on `medaka_ordo_similarityScore` or `medaka_omim_similarityScore` — they are excluded as subsets.
- Batch work: generate multiple files in a single script run; check results with `git log`/`diff` once at the end.
- Completion is declared by actual output (row counts, SHA, Release URL) — not by script generation alone.
