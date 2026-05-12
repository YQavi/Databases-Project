-- ============================================================
-- TCGA CCRCC — Database & Table Creation
-- MySQL 8.0+  |  utf8mb4  |  InnoDB
-- Schema reflects live database as of project completion.
-- Normal forms: 1NF–5NF
-- ============================================================

DROP DATABASE IF EXISTS tcga_ccrcc;

CREATE DATABASE tcga_ccrcc
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE tcga_ccrcc;

-- ============================================================
-- 1. PATIENT
-- ============================================================
CREATE TABLE patient (
    patient_id  VARCHAR(20)  NOT NULL
                             COMMENT 'TCGA patient barcode e.g. TCGA-3Z-A93Z',
    PRIMARY KEY (patient_id)
) ENGINE=InnoDB;

-- ============================================================
-- 2. TISSUE_SOURCE_SITE
--    2NF decomposition: tss_name depends only on tss_code,
--    not on sample_id.
-- ============================================================
CREATE TABLE tissue_source_site (
    tss_code    VARCHAR(10)   NOT NULL
                              COMMENT 'Two-character TCGA TSS code e.g. 3Z',
    tss_name    VARCHAR(200)  NOT NULL
                              COMMENT 'Full institution name',
    PRIMARY KEY (tss_code)
) ENGINE=InnoDB;

-- ============================================================
-- 3. CANCER_TYPE
--    2NF decomposition: all descriptors depend only on
--    oncotree_code, not on sample_id.
-- ============================================================
CREATE TABLE cancer_type (
    oncotree_code        VARCHAR(20)   NOT NULL
                                       COMMENT 'OncoTree code e.g. CCRCC',
    cancer_type          VARCHAR(200)  NOT NULL,
    cancer_type_detailed VARCHAR(200)  NOT NULL,
    tumor_type           VARCHAR(200)  NOT NULL,
    tumor_tissue_site    VARCHAR(100)  NOT NULL,
    PRIMARY KEY (oncotree_code)
) ENGINE=InnoDB;

-- ============================================================
-- 4. SAMPLE
--    Column types reflect live database after import:
--    tissue_prospective/retrospective stored as VARCHAR due to
--    phpMyAdmin type inference during import. aneuploidy_score,
--    msi scores, and tmb also inferred as VARCHAR — these
--    should ideally be numeric but are VARCHAR in the live DB.
--    tbl_score retained as DECIMAL(8,4) as originally designed.
-- ============================================================
CREATE TABLE sample (
    sample_id             VARCHAR(25)   NOT NULL
                                        COMMENT 'TCGA sample barcode e.g. TCGA-3Z-A93Z-01',
    patient_id            VARCHAR(20)   NOT NULL,
    oncotree_code         VARCHAR(20)   NOT NULL,
    tss_code              VARCHAR(10)   NOT NULL,
    grade                 VARCHAR(5)    NULL
                                        COMMENT 'WHO histologic grade: G1 G2 G3 G4 GX',
    tissue_prospective    VARCHAR(18)   NULL
                                        COMMENT '1=Yes 0=No — stored as VARCHAR per live schema',
    tissue_retrospective  VARCHAR(20)   NULL
                                        COMMENT '1=Yes 0=No — stored as VARCHAR per live schema',
    sample_type           VARCHAR(50)   NOT NULL
                                        COMMENT 'Primary / Metastasis / Recurrence',
    somatic_status        VARCHAR(50)   NOT NULL
                                        COMMENT 'Matched / Unmatched',
    aneuploidy_score      VARCHAR(5)    NULL
                                        COMMENT 'Number of aneuploid segments — VARCHAR per live schema',
    msi_score_mantis      VARCHAR(12)   NULL
                                        COMMENT 'MANTIS MSI score — VARCHAR per live schema',
    msi_sensor_score      VARCHAR(12)   NULL
                                        COMMENT 'MSIsensor score — VARCHAR per live schema',
    tmb_nonsynonymous     VARCHAR(12)   NULL
                                        COMMENT 'Mutations per megabase — VARCHAR per live schema',
    tbl_score             DECIMAL(8,4)  NULL
                                        COMMENT 'Tumor break load',
    PRIMARY KEY (sample_id),
    CONSTRAINT fk_sample_patient
        FOREIGN KEY (patient_id)
        REFERENCES patient (patient_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_sample_cancer_type
        FOREIGN KEY (oncotree_code)
        REFERENCES cancer_type (oncotree_code)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_sample_tss
        FOREIGN KEY (tss_code)
        REFERENCES tissue_source_site (tss_code)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    INDEX idx_sample_patient  (patient_id),
    INDEX idx_sample_oncotree (oncotree_code),
    INDEX idx_sample_tss      (tss_code),
    INDEX idx_sample_grade    (grade)
) ENGINE=InnoDB;

-- ============================================================
-- 5. GENE
--    5NF decomposition: hugo_symbol depends only on
--    entrez_gene_id, independent of any mutation.
--    entrez_gene_id = 0 is a placeholder for the 744 genes
--    with unresolved IDs in the source MAF file.
-- ============================================================
CREATE TABLE gene (
    entrez_gene_id  INT           NOT NULL
                                   COMMENT 'NCBI Entrez Gene ID. 0 = unresolved in source data',
    hugo_symbol     VARCHAR(100)  NOT NULL
                                   COMMENT 'HGNC-approved gene symbol',
    PRIMARY KEY (entrez_gene_id),
    INDEX idx_gene_symbol (hugo_symbol)
) ENGINE=InnoDB;

-- ============================================================
-- 6. VARIANT_CLASS
--    5NF decomposition: variant_type and impact are fixed
--    properties of the classification, not of any mutation.
-- ============================================================
CREATE TABLE variant_class (
    variant_classification  VARCHAR(50)  NOT NULL
                                          COMMENT 'e.g. Missense_Mutation, Frame_Shift_Del',
    variant_type            VARCHAR(10)  NOT NULL
                                          COMMENT 'SNP | INS | DEL | ONP',
    impact                  VARCHAR(20)  NOT NULL
                                          COMMENT 'HIGH | MODERATE | LOW | MODIFIER',
    PRIMARY KEY (variant_classification)
) ENGINE=InnoDB;

-- ============================================================
-- 7. MUTATION
--    Surrogate PK satisfies 1NF.
--    reference_allele stored as TEXT per live schema
--    (changed from VARCHAR(500) during import troubleshooting).
--    protein_position stored as VARCHAR(10) per live schema
--    (changed from INT UNSIGNED due to null handling in
--    phpMyAdmin CSV import).
--    All depth/count columns stored as DECIMAL(10,0) UNSIGNED
--    after INT caused import failures with empty cells.
-- ============================================================
CREATE TABLE mutation (
    mutation_id             INT                    NOT NULL AUTO_INCREMENT,
    sample_id               VARCHAR(25)            NOT NULL,
    entrez_gene_id          INT                    NULL
                                                    COMMENT 'NULL for unannotated loci; 0 = unknown gene',
    variant_classification  VARCHAR(50)            NOT NULL,
    ncbi_build              VARCHAR(10)            NOT NULL DEFAULT 'GRCh37',
    chromosome              VARCHAR(5)             NULL,
    start_position          DECIMAL(10,0) UNSIGNED NULL,
    end_position            DECIMAL(10,0) UNSIGNED NULL,
    reference_allele        TEXT                   NULL
                                                    COMMENT 'TEXT per live schema; originally VARCHAR(500)',
    tumor_seq_allele2       VARCHAR(500)           NULL,
    dbsnp_rs                VARCHAR(30)            NULL
                                                    COMMENT 'rs ID or NULL if novel',
    hgvsc                   VARCHAR(200)           NULL
                                                    COMMENT 'Coding sequence change e.g. c.1199T>C',
    hgvsp_short             VARCHAR(100)           NULL
                                                    COMMENT 'Protein change e.g. p.L400P',
    transcript_id           VARCHAR(20)            NULL
                                                    COMMENT 'Ensembl transcript ID',
    protein_position        VARCHAR(10)            NULL
                                                    COMMENT 'VARCHAR per live schema; originally INT UNSIGNED',
    hotspot                 TINYINT(1)             NOT NULL DEFAULT 0
                                                    COMMENT '1 = known cancer hotspot. All 0 in this cohort',
    filter_status           VARCHAR(100)           NULL
                                                    COMMENT 'PASS or pipe-delimited filter flags',
    polyphen                VARCHAR(100)           NULL
                                                    COMMENT 'PolyPhen-2 prediction and score',
    sift                    VARCHAR(100)           NULL
                                                    COMMENT 'SIFT prediction and score',
    t_ref_count             DECIMAL(10,0) UNSIGNED NULL
                                                    COMMENT 'Tumor ref allele read depth',
    t_alt_count             DECIMAL(10,0) UNSIGNED NULL
                                                    COMMENT 'Tumor alt allele read depth',
    n_ref_count             DECIMAL(10,0) UNSIGNED NULL
                                                    COMMENT 'Normal ref allele read depth',
    n_alt_count             DECIMAL(10,0) UNSIGNED NULL
                                                    COMMENT 'Normal alt allele read depth',
    t_depth                 DECIMAL(10,0) UNSIGNED NULL
                                                    COMMENT 'Total tumor read depth',
    n_depth                 DECIMAL(10,0) UNSIGNED NULL
                                                    COMMENT 'Total normal read depth',
    PRIMARY KEY (mutation_id),
    CONSTRAINT fk_mutation_sample
        FOREIGN KEY (sample_id)
        REFERENCES sample (sample_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_mutation_gene
        FOREIGN KEY (entrez_gene_id)
        REFERENCES gene (entrez_gene_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_mutation_variant_class
        FOREIGN KEY (variant_classification)
        REFERENCES variant_class (variant_classification)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    INDEX idx_mut_sample  (sample_id),
    INDEX idx_mut_gene    (entrez_gene_id),
    INDEX idx_mut_chr_pos (chromosome, start_position),
    INDEX idx_mut_hotspot (filter_status),
    INDEX idx_mut_filter  (hotspot)
) ENGINE=InnoDB;
