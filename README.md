# medaka-apis

SQL-loadable flat files extracted from the RIKEN BioResource RDF knowledge graph for medaka (*Oryzias latipes*). Each file is a curated CSV derived from a named SPARQL graph at `https://knowledge.brc.riken.jp/sparql`. The goal is to let researchers unfamiliar with RDF/SPARQL identify medaka strains as candidate human disease models, either via gene orthology (Path A) or phenotype similarity (Path B).

## Tables (v0.3)

| File | Source graph | Rows | Description |
|---|---|---|---|
| `data/curated/medaka_test.csv` | `medaka_test` | 297 | Anchor table — all NBRP Medaka strains with label, description, depositor |
| `data/curated/medaka_disease_similarityScore.csv` | `medaka_disease_similarityScore` | 57 | Path B — cosine similarity between medaka phenotype and human disease phenotype |
| `data/curated/medaka_diseaseID_throughMedgen_direct.csv` | `medaka_diseaseID_throughMedgen_direct` | 113 | Path A — medaka strain is-model-for human disease (via gene orthology) |
| `data/curated/medaka_hp.csv` | `medaka_hp` | 4 | Medaka strain to Human Phenotype Ontology term mapping |
| `data/curated/medaka_ncbigeneMedaka.csv` | `medaka_ncbigeneMedaka` | 37 | Medaka strain to medaka NCBI Gene ID (numeric Entrez IDs only) |
| `data/curated/medaka_ncbigeneHuman_usingNcbigene.csv` | `medaka_ncbigeneHuman_usingNcbigene` + `medaka_nlmNcbigeneHuman_usingNcbigene` | 24 | Medaka strain to human NCBI Gene ID (two source graphs merged and deduplicated) |
| `data/curated/medaka_medakaEnsemblGene.csv` | `medaka_medakaEnsemblGene` | 40 | Medaka strain to medaka Ensembl Gene ID |
| `data/curated/medaka_ensembl_entrezGene_mapping.csv` | `medaka_ensembl_entrezGene_mapping` | 19,011 | Shared lookup — medaka Ensembl Gene ID to Entrez Gene ID (genome-wide, skos:exactMatch only) |
| `data/curated/medaka_zp.csv` | `medaka_zp` | 181 | Medaka strain to Zebrafish Phenotype Ontology (ZP) term mapping |
| `data/curated/medaka_medaka_similarityScore.csv` | `medaka_medaka_similarityScore` | 1 | Path B — cosine similarity between medaka strains sharing phenotype (full source graph) |

Column definitions and source predicates: `metadata/codebook.csv`  
Schema DDL: `schema/schema.sql`  
Extraction provenance: `metadata/provenance.json`

## Load into SQLite

```sh
sqlite3 medaka.db < schema/schema.sql
sqlite3 medaka.db
```

```sql
.mode csv
.import --skip 1 data/curated/medaka_test.csv medaka_strains
.import --skip 1 data/curated/medaka_disease_similarityScore.csv medaka_disease_similarity
.import --skip 1 data/curated/medaka_diseaseID_throughMedgen_direct.csv medaka_disease_gene
.import --skip 1 data/curated/medaka_hp.csv medaka_phenotype_hp
.import --skip 1 data/curated/medaka_ncbigeneMedaka.csv medaka_ncbigene_medaka
.import --skip 1 data/curated/medaka_ncbigeneHuman_usingNcbigene.csv medaka_ncbigene_human
.import --skip 1 data/curated/medaka_medakaEnsemblGene.csv medaka_ensembl_gene
.import --skip 1 data/curated/medaka_ensembl_entrezGene_mapping.csv medaka_ensembl_entrez_mapping
.import --skip 1 data/curated/medaka_zp.csv medaka_phenotype_zp
.import --skip 1 data/curated/medaka_medaka_similarityScore.csv medaka_medaka_similarity
```

Verify:

```sql
SELECT count(*) FROM medaka_strains;              -- 297
SELECT count(*) FROM medaka_disease_similarity;   -- 57
SELECT count(*) FROM medaka_disease_gene;         -- 113
SELECT count(*) FROM medaka_phenotype_hp;         -- 4
SELECT count(*) FROM medaka_ncbigene_medaka;      -- 37
SELECT count(*) FROM medaka_ncbigene_human;       -- 24
SELECT count(*) FROM medaka_ensembl_gene;         -- 40
SELECT count(*) FROM medaka_ensembl_entrez_mapping; -- 19011
SELECT count(*) FROM medaka_phenotype_zp;         -- 181
SELECT count(*) FROM medaka_medaka_similarity;    -- 1
```

`--skip 1` requires SQLite 3.32+. On older versions, remove the header row first or use a script to load.

## Load into PostgreSQL

```sh
psql -d mydb -f schema/schema.sql
psql -d mydb -c "\copy medaka_strains FROM 'data/curated/medaka_test.csv' CSV HEADER"
psql -d mydb -c "\copy medaka_disease_similarity FROM 'data/curated/medaka_disease_similarityScore.csv' CSV HEADER"
psql -d mydb -c "\copy medaka_disease_gene FROM 'data/curated/medaka_diseaseID_throughMedgen_direct.csv' CSV HEADER"
psql -d mydb -c "\copy medaka_phenotype_hp FROM 'data/curated/medaka_hp.csv' CSV HEADER"
psql -d mydb -c "\copy medaka_ncbigene_medaka FROM 'data/curated/medaka_ncbigeneMedaka.csv' CSV HEADER"
psql -d mydb -c "\copy medaka_ncbigene_human FROM 'data/curated/medaka_ncbigeneHuman_usingNcbigene.csv' CSV HEADER"
psql -d mydb -c "\copy medaka_ensembl_gene FROM 'data/curated/medaka_medakaEnsemblGene.csv' CSV HEADER"
psql -d mydb -c "\copy medaka_ensembl_entrez_mapping FROM 'data/curated/medaka_ensembl_entrezGene_mapping.csv' CSV HEADER"
psql -d mydb -c "\copy medaka_phenotype_zp FROM 'data/curated/medaka_zp.csv' CSV HEADER"
psql -d mydb -c "\copy medaka_medaka_similarity FROM 'data/curated/medaka_medaka_similarityScore.csv' CSV HEADER"
```

## Integrity check

```sh
sha256sum -c SHA256SUMS
```

## License

Data source: RIKEN BioResource Research Center, `https://knowledge.brc.riken.jp/`  
License: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

**Citation:**

> RIKEN BioResource Research Center. Medaka RDF knowledge graph (extracted via SPARQL, retrieved 2026-06-23). Distributed as SQL-loadable flat files. https://github.com/kushidat/medaka-apis
