# Data Dictionary
## TCGA CCRCC Relational Database + Neo4j SNP Graph

---

## MySQL Tables

### 1. `patient`
| Column | Type | Key | Nullable | Description |
|---|---|---|---|---|
| patient_id | VARCHAR(20) | PK | NO | TCGA patient barcode e.g. TCGA-3Z-A93Z |

---

### 2. `tissue_source_site`
| Column | Type | Key | Nullable | Description |
|---|---|---|---|---|
| tss_code | VARCHAR(10) | PK | NO | Two-character TCGA institution code e.g. 3Z |
| tss_name | VARCHAR(200) | — | NO | Full institution name |

---

### 3. `cancer_type`
| Column | Type | Key | Nullable | Description |
|---|---|---|---|---|
| oncotree_code | VARCHAR(20) | PK | NO | OncoTree code — CCRCC for all rows in this cohort |
| cancer_type | VARCHAR(200) | — | NO | Broad cancer type name |
| cancer_type_detailed | VARCHAR(200) | — | NO | Detailed cancer type name |
| tumor_type | VARCHAR(200) | — | NO | Tumor morphology classification |
| tumor_tissue_site | VARCHAR(100) | — | NO | Primary tissue of origin |

---

### 4. `sample`
| Column | Type | Key | Nullable | Description |
|---|---|---|---|---|
| sample_id | VARCHAR(25) | PK | NO | TCGA sample barcode e.g. TCGA-3Z-A93Z-01 |
| patient_id | VARCHAR(20) | FK → patient | NO | Parent patient barcode |
| oncotree_code | VARCHAR(20) | FK → cancer_type | NO | Cancer classification |
| tss_code | VARCHAR(10) | FK → tissue_source_site | NO | Collecting institution |
| grade | VARCHAR(5) | — | YES | WHO histologic grade: G1 G2 G3 G4 GX |
| tissue_prospective | VARCHAR(18) | — | YES | Prospective collection indicator. Intended TINYINT(1); stored as VARCHAR per live schema |
| tissue_retrospective | VARCHAR(20) | — | YES | Retrospective collection indicator. Intended TINYINT(1); stored as VARCHAR per live schema |
| sample_type | VARCHAR(50) | — | NO | Primary / Metastasis / Recurrence. All Primary in this cohort |
| somatic_status | VARCHAR(50) | — | NO | Matched / Unmatched. All Matched in this cohort |
| aneuploidy_score | VARCHAR(5) | — | YES | Number of aneuploid segments. Intended SMALLINT; stored as VARCHAR per live schema |
| msi_score_mantis | VARCHAR(12) | — | YES | MANTIS MSI score: >0.6 MSI-H, 0.4–0.6 indeterminate, <0.4 MSS. Intended DECIMAL(8,4); stored as VARCHAR |
| msi_sensor_score | VARCHAR(12) | — | YES | MSIsensor score: >10 MSI-H, 4–10 indeterminate, <4 MSS. Intended DECIMAL(8,4); stored as VARCHAR |
| tmb_nonsynonymous | VARCHAR(12) | — | YES | Nonsynonymous mutations per megabase. Intended DECIMAL(10,6); stored as VARCHAR |
| tbl_score | DECIMAL(8,4) | — | YES | Tumor break load: unbalanced somatic chromosomal breaks |

---

### 5. `gene`
| Column | Type | Key | Nullable | Description |
|---|---|---|---|---|
| entrez_gene_id | INT | PK | NO | NCBI Entrez Gene ID. 0 = placeholder for 744 genes with unresolved IDs in source MAF |
| hugo_symbol | VARCHAR(100) | — | NO | HGNC-approved gene symbol |

---

### 6. `variant_class`
| Column | Type | Key | Nullable | Description |
|---|---|---|---|---|
| variant_classification | VARCHAR(50) | PK | NO | VEP classification e.g. Missense_Mutation, Frame_Shift_Del |
| variant_type | VARCHAR(10) | — | NO | SNP / INS / DEL / ONP |
| impact | VARCHAR(20) | — | NO | HIGH / MODERATE / LOW / MODIFIER |

---

### 7. `mutation`
| Column | Type | Key | Nullable | Description |
|---|---|---|---|---|
| mutation_id | INT AUTO_INCREMENT | PK | NO | Surrogate primary key |
| sample_id | VARCHAR(25) | FK → sample | NO | Tumor sample carrying the mutation |
| entrez_gene_id | INT | FK → gene | YES | Gene harboring the mutation; 0 = unknown |
| variant_classification | VARCHAR(50) | FK → variant_class | NO | Functional classification |
| ncbi_build | VARCHAR(10) | — | NO | Reference genome build; GRCh37 for all rows |
| chromosome | VARCHAR(5) | — | YES | Chromosome number or letter |
| start_position | DECIMAL(10,0) UNSIGNED | — | YES | Genomic start coordinate 1-based |
| end_position | DECIMAL(10,0) UNSIGNED | — | YES | Genomic end coordinate |
| reference_allele | TEXT | — | YES | Reference genome allele. Intended VARCHAR(500); stored as TEXT per live schema |
| tumor_seq_allele2 | VARCHAR(500) | — | YES | Alternate allele in tumor |
| dbsnp_rs | VARCHAR(30) | — | YES | dbSNP rsID if registered |
| hgvsc | VARCHAR(200) | — | YES | HGVS coding sequence notation e.g. c.343C>A |
| hgvsp_short | VARCHAR(100) | — | YES | HGVS protein notation e.g. p.H115N |
| transcript_id | VARCHAR(20) | — | YES | Ensembl canonical transcript ID |
| protein_position | VARCHAR(10) | — | YES | Amino acid position. Intended INT UNSIGNED; stored as VARCHAR per live schema |
| hotspot | TINYINT(1) | — | NO | 1 = known cancer hotspot. All 0 in this cohort |
| filter_status | VARCHAR(100) | — | YES | PASS or pipe-delimited caller filter flags |
| polyphen | VARCHAR(100) | — | YES | PolyPhen-2 prediction and score |
| sift | VARCHAR(100) | — | YES | SIFT prediction and score |
| t_ref_count | DECIMAL(10,0) UNSIGNED | — | YES | Tumor reference allele read depth |
| t_alt_count | DECIMAL(10,0) UNSIGNED | — | YES | Tumor alternate allele read depth |
| n_ref_count | DECIMAL(10,0) UNSIGNED | — | YES | Normal reference allele read depth |
| n_alt_count | DECIMAL(10,0) UNSIGNED | — | YES | Normal alternate allele read depth |
| t_depth | DECIMAL(10,0) UNSIGNED | — | YES | Total tumor sequencing depth |
| n_depth | DECIMAL(10,0) UNSIGNED | — | YES | Total normal sequencing depth |

---

## Neo4j Node Types

### `Gene` node
| Property | Type | Description |
|---|---|---|
| entrez_gene_id | Integer | NCBI Entrez ID — unique constraint |
| hugo_symbol | String | HGNC gene symbol — indexed |
| full_name | String | Full gene name |
| chromosome | String | Chromosomal location |
| role | String | Tumor suppressor / Oncogene / Metabolic enzyme / Regulator / etc. |
| pathway | String | Primary signaling or metabolic pathway |
| ccrcc_driver | Boolean | Known CCRCC driver gene (true only for VHL) |
| uniprot_id | String | UniProt accession (added by 04_api_enrichment.py) |
| protein_name | String | Recommended protein name from UniProt |
| protein_length | Integer | Amino acid sequence length |
| subcellular_location | String | Subcellular localization from UniProt |
| protein_function | String | Functional description from UniProt (first 500 chars) |
| disease_association | String | Known disease association from UniProt |

**Gene nodes in this graph:**

| hugo_symbol | entrez_gene_id | ccrcc_driver | pathway |
|---|---|---|---|
| VHL | 7428 | true | HIF/hypoxia signaling |
| ACADS | 35 | false | Fatty acid beta-oxidation |
| FNBP1L | 54874 | false | Actin cytoskeleton / endocytosis |
| BAK1 | 578 | false | Apoptosis / BCL2 family |
| EDIL3 | 10085 | false | Integrin signaling / angiogenesis |

---

### `SNP` node
| Property | Type | Description |
|---|---|---|
| mutation_id | Integer | Unique constraint; matches MySQL mutation.mutation_id |
| hugo_symbol | String | Gene symbol |
| hgvsp_short | String | Protein change notation — indexed |
| hgvsc | String | Coding sequence change notation |
| chromosome | String | GRCh37 chromosomal location |
| start_position | Integer | GRCh37 genomic coordinate |
| reference_allele | String | Reference base |
| tumor_seq_allele2 | String | Alternate base |
| dbsnp_rs | String | dbSNP rsID |
| transcript_id | String | Ensembl transcript |
| protein_position | Integer | Amino acid position |
| ref_aa / alt_aa | String | Single-letter amino acid codes |
| ref_aa_full / alt_aa_full | String | Full amino acid names |
| variant_classification | String | Functional class |
| impact | String | Predicted impact level |
| polyphen | String | PolyPhen-2 score |
| sift | String | SIFT score |
| n_samples | Integer | TCGA samples carrying this SNP |
| mean_vaf | Float | Mean variant allele frequency across TCGA samples |
| grantham_score | Integer | Chemical distance between ref and alt AA (Grantham 1974) |
| grantham_label | String | conservative / moderately conservative / moderately radical / radical |
| charge_change | String | Charge change at physiological pH 7.4 |
| polarity_change | String | Polarity change |
| hydrophobicity_change | Float | Kyte-Doolittle hydrophobicity delta (alt minus ref) |
| global_maf | Float | Population allele frequency from dbSNP |
| dbsnp_clinical_significance | String | dbSNP clinical annotation |
| clinvar_significance | String | ClinVar clinical significance |
| clinvar_condition | String | Associated disease condition in ClinVar |
| clinvar_review_stars | String | ClinVar evidence review status |
| allofus_carrier_count | Integer | Number of All of Us participants carrying this variant |
| allofus_carrier_freq | Float | Carrier frequency in All of Us cohort (~866,000 participants) |
| allofus_kidney_disease_n | Integer | Carriers with kidney disease EHR diagnosis (estimated) |
| allofus_kidney_disease_pct | Float | Proportion of carriers with kidney disease |
| allofus_homozygous_n | Integer | Carriers who are homozygous for the alternate allele |
| allofus_cohort_total | Integer | Total unique carriers across all 4 queried variants (96) |
| allofus_source | String | All of Us Controlled Tier Dataset v8 |
| allofus_genome_version | String | GRCh38 |
| allofus_notes | String | Notable findings or caveats |
| allofus_sex_female | Integer | Female carriers in cohort |
| allofus_sex_male | Integer | Male carriers in cohort |
| allofus_race_white | Integer | White carriers |
| allofus_race_black | Integer | Black or African American carriers |
| allofus_ethnicity_hispanic | Integer | Hispanic or Latino carriers |
| allofus_ethnicity_non_hispanic | Integer | Non-Hispanic carriers |

**SNP summary:**

| mutation_id | Gene | Change | rsID | Grantham | AoU Carriers | CKD est. |
|---|---|---|---|---|---|---|
| 62 | VHL | p.H115N | rs5030811 | 68 mod. conservative | null (not found) | — |
| 10785 | ACADS | p.R330H | rs199633532 | 29 conservative | 74 | ~3 |
| 7393 | FNBP1L | p.R65W | rs774614978 | 101 mod. radical | 15 | ~1 |
| 3347 | BAK1 | p.R76W | rs766561404 | 101 mod. radical | 4 | 0 |
| 16606 | EDIL3 | p.T343M | rs757863733 | 81 mod. conservative | 3 | 0 |

---

### `Sample` node
| Property | Type | Description |
|---|---|---|
| sample_id | String | TCGA sample barcode — unique constraint |
| patient_id | String | TCGA patient barcode |

**Sample nodes in this graph (12 total):**

| sample_id | SNP carried |
|---|---|
| TCGA-3Z-A93Z-01, TCGA-A3-3382-01, TCGA-CJ-4643-01, TCGA-CZ-5470-01 | VHL p.H115N |
| TCGA-B0-5709-01, TCGA-CJ-4634-01 | ACADS p.R330H |
| TCGA-B0-5096-01, TCGA-BP-4161-01 | FNBP1L p.R65W |
| TCGA-A3-A6NN-01, TCGA-G6-A5PC-01 | BAK1 p.R76W |
| TCGA-BP-4989-01, TCGA-G6-A8L8-01 | EDIL3 p.T343M |

---

## Neo4j Relationship Types

| Relationship | From | To | Properties | Description |
|---|---|---|---|---|
| HARBORS | Gene | SNP | — | Gene contains this SNP |
| IN_GENE | SNP | Gene | — | Back-reference for bidirectional traversal |
| HAS_MUTATION | Sample | SNP | vaf, t_alt_count, t_depth | Sample carries this mutation at given VAF with read support |
| INTERACTS_WITH | Gene | Gene | string_score, experimental_score, coexpression_score, textmining_score, source | STRING protein-protein interaction (source = STRING) |
