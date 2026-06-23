-- medaka-apis schema v0.3
-- Source: RIKEN BioResource Knowledge Graph <https://knowledge.brc.riken.jp/sparql>
-- Graph IRI prefix: http://metadb.riken.jp/db/
-- License: CC BY
-- Encoding: UTF-8  Line endings: LF
-- Missing values are stored as the string 'NA'.

-- ============================================================
-- medaka_strains
-- Source graph: medaka_test
-- One row per NBRP Medaka strain.
-- ============================================================
CREATE TABLE medaka_strains (
    medaka_id    TEXT    NOT NULL,   -- NBRP strain ID, e.g. "MT10"
    label        TEXT,               -- strain name (rdfs:label)
    description  TEXT,               -- phenotype description (dc:description)
    deposit_org  TEXT,               -- depositing organisation, English label
    provider     TEXT,               -- provider organisation IRI (brso:provider)
    homepage     TEXT,               -- strain detail page URL (foaf:homepage)
    PRIMARY KEY (medaka_id)
);
CREATE INDEX idx_medaka_strains_id ON medaka_strains (medaka_id);

-- ============================================================
-- medaka_disease_similarity
-- Source graph: medaka_disease_similarityScore
-- Medaka–disease associations inferred via phenotype cosine similarity (Path B).
-- disease_id is in CURIE format: Orphanet:NNN or OMIM:NNN.
-- ============================================================
CREATE TABLE medaka_disease_similarity (
    medaka_id      TEXT    NOT NULL,
    disease_id     TEXT    NOT NULL,
    disease_source TEXT    NOT NULL CHECK (disease_source IN ('ordo', 'omim')),
    score          REAL    NOT NULL,   -- cosine similarity [0, 1]
    PRIMARY KEY (medaka_id, disease_id),
    FOREIGN KEY (medaka_id) REFERENCES medaka_strains (medaka_id)
);
CREATE INDEX idx_dis_sim_medaka  ON medaka_disease_similarity (medaka_id);
CREATE INDEX idx_dis_sim_disease ON medaka_disease_similarity (disease_id);

-- ============================================================
-- medaka_disease_gene
-- Source graph: medaka_diseaseID_throughMedgen_direct
-- Medaka–disease associations inferred via gene orthology (Path A).
-- disease_id is in CURIE format: Orphanet:NNN or OMIM:NNN.
-- ============================================================
CREATE TABLE medaka_disease_gene (
    medaka_id      TEXT    NOT NULL,
    disease_id     TEXT    NOT NULL,
    disease_source TEXT    NOT NULL CHECK (disease_source IN ('ordo', 'omim')),
    PRIMARY KEY (medaka_id, disease_id),
    FOREIGN KEY (medaka_id) REFERENCES medaka_strains (medaka_id)
);
CREATE INDEX idx_dis_gene_medaka  ON medaka_disease_gene (medaka_id);
CREATE INDEX idx_dis_gene_disease ON medaka_disease_gene (disease_id);

-- ============================================================
-- medaka_phenotype_hp
-- Source graph: medaka_hp
-- Direct medaka–Human Phenotype Ontology term annotations.
-- hp_id is in CURIE format: HP:NNNNNNN.
-- ============================================================
CREATE TABLE medaka_phenotype_hp (
    medaka_id  TEXT  NOT NULL,
    hp_id      TEXT  NOT NULL,   -- HPO term, e.g. "HP:0031377"
    PRIMARY KEY (medaka_id, hp_id),
    FOREIGN KEY (medaka_id) REFERENCES medaka_strains (medaka_id)
);
CREATE INDEX idx_pheno_hp_medaka ON medaka_phenotype_hp (medaka_id);
CREATE INDEX idx_pheno_hp_id     ON medaka_phenotype_hp (hp_id);

-- ============================================================
-- medaka_ncbigene_medaka  (v0.2)
-- Source graph: medaka_ncbigeneMedaka
-- Medaka strain → medaka Entrez (NCBI Gene) ID.
-- Transcript-level IDs (e.g. slc2a11b-201) excluded; integer IDs only.
-- ============================================================
CREATE TABLE medaka_ncbigene_medaka (
    medaka_id   TEXT  NOT NULL,
    ncbigene_id TEXT  NOT NULL,   -- NCBI Gene integer ID, e.g. "101159023"
    PRIMARY KEY (medaka_id, ncbigene_id),
    FOREIGN KEY (medaka_id) REFERENCES medaka_strains (medaka_id)
);
CREATE INDEX idx_ncbigene_medaka_strain ON medaka_ncbigene_medaka (medaka_id);
CREATE INDEX idx_ncbigene_medaka_gene   ON medaka_ncbigene_medaka (ncbigene_id);

-- ============================================================
-- medaka_ncbigene_human  (v0.2)
-- Source graphs: medaka_ncbigeneHuman_usingNcbigene +
--                medaka_nlmNcbigeneHuman_usingNcbigene (merged, deduped)
-- Medaka strain → human ortholog Entrez ID.
-- ============================================================
CREATE TABLE medaka_ncbigene_human (
    medaka_id   TEXT  NOT NULL,
    ncbigene_id TEXT  NOT NULL,   -- human NCBI Gene integer ID, e.g. "51151"
    PRIMARY KEY (medaka_id, ncbigene_id),
    FOREIGN KEY (medaka_id) REFERENCES medaka_strains (medaka_id)
);
CREATE INDEX idx_ncbigene_human_strain ON medaka_ncbigene_human (medaka_id);
CREATE INDEX idx_ncbigene_human_gene   ON medaka_ncbigene_human (ncbigene_id);

-- ============================================================
-- medaka_ensembl_gene  (v0.2)
-- Source graph: medaka_medakaEnsemblGene
-- Medaka strain → medaka Ensembl gene ID (ENSORLG...).
-- ============================================================
CREATE TABLE medaka_ensembl_gene (
    medaka_id  TEXT  NOT NULL,
    ensembl_id TEXT  NOT NULL,   -- Ensembl gene ID, e.g. "ENSORLG00000008054"
    PRIMARY KEY (medaka_id, ensembl_id),
    FOREIGN KEY (medaka_id) REFERENCES medaka_strains (medaka_id)
);
CREATE INDEX idx_ensembl_gene_strain  ON medaka_ensembl_gene (medaka_id);
CREATE INDEX idx_ensembl_gene_ensembl ON medaka_ensembl_gene (ensembl_id);

-- ============================================================
-- medaka_ensembl_entrez_mapping  (v0.2)
-- Source graph: medaka_ensembl_entrezGene_mapping
-- Medaka Ensembl gene ↔ Entrez gene ID bridge table (skos:exactMatch only).
-- Covers the full medaka genome (~60 K pairs), not only strains in this release.
-- Join path: medaka_ensembl_gene.ensembl_id
--          → medaka_ensembl_entrez_mapping.ensembl_id
--          → medaka_ncbigene_medaka.ncbigene_id
-- ============================================================
CREATE TABLE medaka_ensembl_entrez_mapping (
    ensembl_id  TEXT  NOT NULL,
    ncbigene_id TEXT  NOT NULL,
    PRIMARY KEY (ensembl_id, ncbigene_id)
);
CREATE INDEX idx_ensembl_entrez_ensembl ON medaka_ensembl_entrez_mapping (ensembl_id);
CREATE INDEX idx_ensembl_entrez_ncbi    ON medaka_ensembl_entrez_mapping (ncbigene_id);

-- ============================================================
-- medaka_phenotype_zp  (v0.3)
-- Source graph: medaka_zp
-- Direct medaka–Zebrafish Phenotype Ontology term annotations.
-- zp_id is in CURIE format: ZP:NNNNNNN.
-- ============================================================
CREATE TABLE medaka_phenotype_zp (
    medaka_id  TEXT  NOT NULL,
    zp_id      TEXT  NOT NULL,   -- ZPO term, e.g. "ZP:0002438"
    PRIMARY KEY (medaka_id, zp_id),
    FOREIGN KEY (medaka_id) REFERENCES medaka_strains (medaka_id)
);
CREATE INDEX idx_pheno_zp_medaka ON medaka_phenotype_zp (medaka_id);
CREATE INDEX idx_pheno_zp_id     ON medaka_phenotype_zp (zp_id);

-- ============================================================
-- medaka_medaka_similarity  (v0.3)
-- Source graph: medaka_medaka_similarityScore
-- Medaka–medaka phenotype cosine similarity.
-- Pair stored with medaka_id_1 < medaka_id_2 (lexicographic) to avoid duplicates.
-- Note: subject IRIs in source graph use example.org namespace.
-- ============================================================
CREATE TABLE medaka_medaka_similarity (
    medaka_id_1  TEXT  NOT NULL,
    medaka_id_2  TEXT  NOT NULL,
    score        REAL  NOT NULL,   -- cosine similarity [0, 1]
    PRIMARY KEY (medaka_id_1, medaka_id_2),
    FOREIGN KEY (medaka_id_1) REFERENCES medaka_strains (medaka_id),
    FOREIGN KEY (medaka_id_2) REFERENCES medaka_strains (medaka_id)
);
CREATE INDEX idx_medaka_sim_id1 ON medaka_medaka_similarity (medaka_id_1);
CREATE INDEX idx_medaka_sim_id2 ON medaka_medaka_similarity (medaka_id_2);
