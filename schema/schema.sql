-- medaka-apis schema v0.1
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
