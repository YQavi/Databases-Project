# TCGA CCRCC Mutation Database
### BINF6970 — Databases for Bioinformatics | Georgetown University

A relational and graph database for somatic mutation analysis of kidney renal clear cell carcinoma (KIRC/CCRCC) using TCGA Pan-Cancer Atlas 2018 data.

---

## Project Summary

This project builds a fully normalized relational database (MySQL, 1NF–5NF) from TCGA clinical and mutation data for 512 kidney clear cell carcinoma samples, selects 5 biologically significant SNPs based on recurrence and functional impact criteria, and imports them into a Neo4j graph database enriched with protein chemistry and interaction data from four public REST APIs (UniProt, dbSNP, ClinVar, STRING).

**Final database contains:**
- 512 patient samples across 20 tissue source sites
- 31,073 somatic mutations across 7 normalized MySQL tables
- 5 recurrently mutated, double-damaging missense SNPs in Neo4j
- Gene, SNP, and Sample nodes connected by mutation and PPI relationships
- API-enriched node properties including Grantham scores, UniProt protein function, ClinVar significance, and STRING interaction scores

---

## Tools and Technologies

| Component | Tool |
|---|---|
| Relational database | MySQL 8.0 via phpMyAdmin |
| Graph database | Neo4j Desktop 5.x |
| Data cleaning | Python 3.12 (pandas) |
| API calls | Python (requests, neo4j) |
| Data source | cBioPortal — TCGA KIRC PanCancer Atlas 2018 |

---

## Repository Structure

```
tcga-ccrcc-database/
├── README.md                        # This file
├── .gitignore
├── sql/
│   ├── 01_create_schema.sql         # DDL: creates all 7 tables
│   ├── 02_load_cleaned_data.sql     # LOAD DATA statements
│   └── database_dump.sql            # Full MySQL export (skip steps 1-3)
├── scripts/
│   ├── 01_clean_tcga_ccrcc.py       # Data cleaning pipeline
│   ├── 02_snp_selection_queries.sql # SELECT queries for SNP selection
│   ├── 03_neo4j_import.cypher       # Neo4j graph creation
│   └── 04_api_enrichment.py         # API enrichment pipeline
├── data/
│   ├── raw/                         # Original cBioPortal source files
│   └── cleaned/                     # Cleaned TSV files (output of script 01)
├── docs/
│   ├── project_writeup.pdf          # Full cleaning and design justification
│   ├── data_dictionary.md           # All tables, columns, types, and descriptions
│   ├── script_execution_order.md    # Step-by-step reproduction instructions
│   └── decisions_and_limitations.md # Design decisions and known limitations
└── diagrams/
    ├── conceptual_er_diagram.png    # Entity-relationship diagram
    └── logical_5nf_erd.png          # Normalized schema diagram (5NF)
```

---

## Data Sources

| File | Description | Rows | Source |
|---|---|---|---|
| data_clinical_sample.txt | Sample-level clinical data | 512 | cBioPortal TCGA KIRC PanAtlas 2018 |
| data_mutations.txt | Somatic mutation MAF file | 31,073 | cBioPortal TCGA KIRC PanAtlas 2018 |

Data downloaded from: https://www.cbioportal.org/study/summary?id=kirc_tcga_pan_can_atlas_2018

---

## How to Recreate the Database

### Option A — From SQL dump (fastest)
```bash
mysql -u root -p -e "CREATE DATABASE tcga_ccrcc;"
mysql -u root -p tcga_ccrcc < sql/database_dump.sql
```
Then skip to Step 5.

### Option B — From scratch

**Step 1 — Clean the source data**
```bash
pip install pandas openpyxl requests neo4j
python scripts/01_clean_tcga_ccrcc.py
```
Output: 7 TSV files in `data/cleaned/`

**Step 2 — Create MySQL schema**
```bash
mysql -u root -p < sql/01_create_schema.sql
```

**Step 3 — Load data into MySQL**

Import each file from `data/cleaned/` into phpMyAdmin in this order using these settings:
- Format: CSV | Columns separated: `\t` | Columns enclosed: `"` | Escaped: *(blank)*

| Order | Table | File |
|---|---|---|
| 1 | patient | patient.tsv |
| 2 | tissue_source_site | tissue_source_site.tsv |
| 3 | cancer_type | cancer_type.tsv |
| 4 | sample | sample.tsv |
| 5 | gene | gene.tsv |
| 6 | variant_class | variant_class.tsv |
| 7 | mutation | mutation.tsv |

Then run these post-import fixes in the phpMyAdmin SQL tab:
```sql
SET FOREIGN_KEY_CHECKS = 0;

INSERT INTO gene (entrez_gene_id, hugo_symbol)
VALUES (0, 'UNKNOWN - entrez_gene_id 0 indicates no known gene ID in source data');

DELETE FROM gene WHERE entrez_gene_id = 1903   AND hugo_symbol = 'C9orf47';
DELETE FROM gene WHERE entrez_gene_id = 23499  AND hugo_symbol = 'KIAA0754';
DELETE FROM gene WHERE entrez_gene_id = 284697 AND hugo_symbol = 'KIAA1107';
DELETE FROM gene WHERE entrez_gene_id = 399687 AND hugo_symbol = 'TIAF1';

UPDATE gene SET entrez_gene_id = 441108 WHERE hugo_symbol = 'C5orf56';

SET FOREIGN_KEY_CHECKS = 1;
```

**Step 4 — Select SNPs**

Run `scripts/02_snp_selection_queries.sql` in phpMyAdmin to identify the 5 SNPs of interest.

**Step 5 — Build Neo4j graph**

Open Neo4j Browser at http://localhost:7474, paste and run `scripts/03_neo4j_import.cypher`.

**Step 6 — Enrich with APIs**

Update `NEO4J_PASS` on line 19 of `scripts/04_api_enrichment.py`, then:
```bash
python scripts/04_api_enrichment.py
```

---

## Documentation and Diagrams

| Document | Location |
|---|---|
| Full project write-up | `docs/project_writeup.pdf` |
| Data dictionary | `docs/data_dictionary.md` |
| Script execution order | `docs/script_execution_order.md` |
| Design decisions and limitations | `docs/decisions_and_limitations.md` |
| ER diagram | `diagrams/conceptual_er_diagram.png` |
| 5NF logical model | `diagrams/logical_5nf_erd.png` |

---

## Expected Final Result

After successful execution:
- MySQL database `tcga_ccrcc` with 7 populated tables (512 samples, 31,073 mutations)
- Neo4j graph with 5 Gene nodes, 5 SNP nodes, 12 Sample nodes, and HARBORS / HAS_MUTATION / INTERACTS_WITH relationships
- SNP nodes enriched with Grantham scores, UniProt protein data, dbSNP population frequencies, and ClinVar clinical significance
- Gene nodes enriched with STRING PPI interaction edges

Verify MySQL:
```sql
SELECT COUNT(*) FROM mutation;    -- expect 31073
SELECT COUNT(*) FROM sample;      -- expect 512
SELECT COUNT(*) FROM gene;        -- expect ~3800
```

Verify Neo4j:
```cypher
MATCH (n)-[r]->(m) RETURN n, r, m
MATCH (s:SNP) RETURN s.hgvsp_short, s.grantham_score, s.clinvar_significance
```
