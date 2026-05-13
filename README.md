# TCGA CCRCC Mutation Database
### BINF6970 — Databases for Bioinformatics | Georgetown University

A relational and graph database for somatic mutation analysis of kidney renal clear cell carcinoma (KIRC/CCRCC) using TCGA Pan-Cancer Atlas 2018 data, with population-level validation through the All of Us Research Program.

*Disclaimer: Claude AI was used to assist in the completion of this project*

---

## Project Summary

This project builds a fully normalized relational database (MySQL, 1NF–5NF) from TCGA clinical and somatic mutation data for 512 kidney clear cell carcinoma samples. Five missense SNPs were selected based on recurrence across independent patients, double-damaging functional predictions (PolyPhen probably_damaging + SIFT deleterious), registered dbSNP identifiers, and confirmed presence in the All of Us Controlled Tier Dataset v8. The selected SNPs were imported into a Neo4j graph database and enriched with protein chemistry data, four REST APIs, and population carrier and EHR data from All of Us.

**Final database contains:**
- 512 patient samples across 20 tissue source sites
- 31,073 somatic mutations across 7 normalized MySQL tables
- 5 SNPs confirmed in All of Us across 5 genes: VHL, ACADS, FNBP1L, BAK1, EDIL3
- 12 TCGA sample nodes connected by HAS_MUTATION edges carrying VAF and read depth
- SNP nodes enriched with Grantham scores, UniProt protein function, dbSNP population frequencies, ClinVar clinical significance, STRING PPI interactions, and All of Us carrier data

**Selected SNPs:**

| Gene | AA Change | rsID | TCGA n | Mean VAF | Grantham | All of Us Carriers |
|---|---|---|---|---|---|---|
| VHL | p.H115N | rs5030811 | 4 | 0.392 | 68 (mod. conservative) | Not found in AoU |
| ACADS | p.R330H | rs199633532 | 2 | 0.231 | 29 (conservative) | 74 |
| FNBP1L | p.R65W | rs774614978 | 2 | 0.319 | 101 (mod. radical) | 15 |
| BAK1 | p.R76W | rs766561404 | 2 | 0.072 | 101 (mod. radical) | 4 |
| EDIL3 | p.T343M | rs757863733 | 2 | 0.267 | 81 (mod. conservative) | 3 |

---

## Tools and Technologies

| Component | Tool |
|---|---|
| Relational database | MySQL 8.0 via phpMyAdmin |
| Graph database | Neo4j Desktop 5.x |
| Data cleaning | Python 3.12 (pandas) |
| API enrichment | Python (requests, neo4j) |
| Population validation | All of Us Controlled Tier Dataset v8 |
| Data source | cBioPortal — TCGA KIRC PanCancer Atlas 2018 |

---

## Repository Structure

```
tcga-ccrcc-database/
├── README.md
├── .gitignore
├── sql/
│   ├── 01_create_schema.sql          # DDL: creates all 7 MySQL tables
│   └── database_dump.sql             # Full MySQL export — skips steps 1-4
├── scripts/
│   ├── 01_clean_tcga_ccrcc.py        # Data cleaning and normalization pipeline
│   ├── 02_snp_selection_queries.sql  # SQL queries used to select the 5 SNPs
│   ├── 03_neo4j_import.cypher        # Neo4j graph creation
│   ├── 04_api_enrichment.py          # UniProt / dbSNP / ClinVar / STRING enrichment
│   ├── 05_allofus_enrichment.cypher  # All of Us carrier and EHR data into Neo4j
│   └── allofus_analysis.py           # All of Us Workbench notebook code
├── data/
│   ├── raw/                          # Original cBioPortal files (gitignored)
│   └── cleaned/                      # 7 TSV files output by script 01
├── docs/
│   ├── project_writeup.pdf           # Full project documentation
│   ├── data_dictionary.md            # Tables, columns, types, descriptions
│   ├── script_execution_order.md     # Step-by-step reproduction guide
│   └── decisions_and_limitations.md  # Design decisions and known limitations
└── diagrams/
    ├── conceptual_er_diagram.png     # Entity-relationship diagram
    └── logical_5nf_erd.png           # 5NF normalized schema diagram
```

---

## Data Sources

Raw data is included as `data/raw/data_mutation.zip` (compressed due to file size).
Unzip into `data/raw/` before running the cleaning script:
```bash
cd data/raw && unzip data_mutation.zip
```
Then run `scripts/01_clean_tcga_ccrcc.py`.

| Source | Resource | Description |
|---|---|---|
| cBioPortal | data_clinical_sample.txt | 512 CCRCC samples with clinical metadata |
| cBioPortal | data_mutations.txt | 31,073 somatic mutations in MAF format |
| All of Us | Controlled Tier Dataset v8 | Population carrier counts and kidney disease EHR data |

cBioPortal: https://www.cbioportal.org/study/summary?id=kirc_tcga_pan_can_atlas_2018

All of Us data requires Registered Tier access and completion of CITI training at researchallofus.org.

---

## How to Recreate the Database

### Option A — From SQL dump (fastest)
```bash
mysql -u root -p -e "CREATE DATABASE tcga_ccrcc;"
mysql -u root -p tcga_ccrcc < sql/database_dump.sql
```
Skip to Step 6.

### Option B — From scratch

**Step 1 — Install dependencies**
```bash
pip install pandas openpyxl requests neo4j
```

**Step 2 — Clean source data**
```bash
python scripts/01_clean_tcga_ccrcc.py
```
Output: 7 TSV files in `data/cleaned/`

**Step 3 — Create MySQL schema**
```bash
mysql -u root -p < sql/01_create_schema.sql
```

**Step 4 — Load data into MySQL via phpMyAdmin**

Import each TSV in FK dependency order. Settings: Format=CSV, Separated=`\t`, Enclosed=`"`, Escaped=*(blank)*, Terminated=auto.

| Order | Table | File |
|---|---|---|
| 1 | patient | patient.tsv |
| 2 | tissue_source_site | tissue_source_site.tsv |
| 3 | cancer_type | cancer_type.tsv |
| 4 | sample | sample.tsv |
| 5 | gene | gene.tsv |
| 6 | variant_class | variant_class.tsv |
| 7 | mutation | mutation.tsv |

Run post-import fixes in phpMyAdmin SQL tab:
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

**Step 5 — Select SNPs**

Run `scripts/02_snp_selection_queries.sql` in phpMyAdmin. The final query applies: PASS filter, SNP + Missense type, PolyPhen probably_damaging, SIFT deleterious, mandatory dbSNP rsID, VAF ≥ 0.25, HAVING ≥ 2 samples, LIMIT 5.

**Step 6 — Build Neo4j graph**

Open Neo4j Browser at http://localhost:7474 and run `scripts/03_neo4j_import.cypher`.

```cypher
MATCH (n)-[r]->(m) RETURN n, r, m   // verify import
```

**Step 7 — API enrichment**

Update `NEO4J_PASS` on line 19 of `scripts/04_api_enrichment.py`, then:
```bash
python scripts/04_api_enrichment.py
```
Calls: UniProt, dbSNP, ClinVar, STRING. Requires internet connection.

**Step 8 — All of Us enrichment**

1. Complete All of Us CITI training at researchallofus.org
2. Create a dataset in the Researcher Workbench using the 5 variant IDs
3. Export notebook and run `scripts/allofus_analysis.py` inside the Workbench
4. Fill real values from output into `scripts/05_allofus_enrichment.cypher`
5. Run the Cypher in Neo4j Browser

---

## All of Us Findings

Variants queried using GRCh38 coordinates in All of Us Controlled Tier Dataset v8 (n ≈ 866,000). 96 unique carriers identified across 4 variants. 4 carriers had a chronic kidney disease EHR diagnosis (pooled across all variants).

| Gene | rsID | AoU Carriers | Est. CKD Carriers |
|---|---|---|---|
| ACADS p.R330H | rs199633532 | 74 | ~3 |
| FNBP1L p.R65W | rs774614978 | 15 | ~1 |
| BAK1 p.R76W | rs766561404 | 4 | 0 |
| EDIL3 p.T343M | rs757863733 | 3 | 0 |
| VHL p.H115N | rs5030811 | not found | — |

Carrier demographics (n=96): 57F / 38M; 53 White, 14 Black, 21 None Indicated; 68 non-Hispanic, 25 Hispanic.

---

## Expected Final Result

**MySQL verification:**
```sql
SELECT COUNT(*) FROM mutation;  -- 31073
SELECT COUNT(*) FROM sample;    -- 512
SELECT COUNT(*) FROM gene;      -- ~3800
```

**Neo4j verification:**
```cypher
MATCH (n)-[r]->(m) RETURN n, r, m

MATCH (s:SNP)
RETURN s.hugo_symbol, s.hgvsp_short, s.grantham_score,
       s.clinvar_significance, s.allofus_carrier_count
ORDER BY s.allofus_carrier_count DESC
```
