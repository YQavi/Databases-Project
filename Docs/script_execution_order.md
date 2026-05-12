# Script Execution Order
## TCGA CCRCC Database Project

Execute scripts in the following order. Do not skip steps — each script depends on outputs from the previous one.

---

## Prerequisites

Install required software before running anything:

```bash
# Python packages
pip install pandas openpyxl requests neo4j

# Database engines
# MySQL 8.0+ running locally or via XAMPP/MAMP
# Neo4j Desktop 5.x running locally (bolt://localhost:7687)
```

---

## Step 1 — Clean source data
**Script:** `scripts/01_clean_tcga_ccrcc.py`
**Input:** `data/raw/data_clinical_sample.txt`, `data/raw/data_mutations.txt`
**Output:** 7 TSV files written to `data/cleaned/`

```bash
python scripts/01_clean_tcga_ccrcc.py
```

This script:
- Skips the 4-row cBioPortal metadata header in the sample file
- Normalizes nulls, booleans, and numeric types
- Decomposes the source into 7 normalized tables matching the schema
- Writes all output as quoted TSV files safe for phpMyAdmin import

Expected output files in `data/cleaned/`:
```
patient.tsv
tissue_source_site.tsv
cancer_type.tsv
sample.tsv
gene.tsv
variant_class.tsv
mutation.tsv
```

---

## Step 2 — Create MySQL schema
**Script:** `sql/01_create_schema.sql`
**Input:** None (run against an empty MySQL instance)
**Output:** `tcga_ccrcc` database with 7 empty tables

Run in phpMyAdmin SQL tab or MySQL CLI:
```bash
mysql -u root -p < sql/01_create_schema.sql
```

This script:
- Creates the `tcga_ccrcc` database
- Creates all 7 tables with correct types, PKs, FKs, and indexes
- Safe to re-run (uses `DROP DATABASE IF EXISTS` at the top)

---

## Step 3 — Load cleaned data into MySQL
**Script:** `sql/02_load_cleaned_data.sql`  
**Input:** TSV files from Step 1
**Output:** All 7 tables populated

```bash
mysql -u root -p tcga_ccrcc < sql/02_load_cleaned_data.sql
```

**Or via phpMyAdmin:**
Import each TSV file into its table in this exact order (FK dependency order):

| Order | Table | File |
|---|---|---|
| 1 | patient | patient.tsv |
| 2 | tissue_source_site | tissue_source_site.tsv |
| 3 | cancer_type | cancer_type.tsv |
| 4 | sample | sample.tsv |
| 5 | gene | gene.tsv |
| 6 | variant_class | variant_class.tsv |
| 7 | mutation | mutation.tsv |

phpMyAdmin import settings for every file:
- Format: CSV
- Columns separated with: `\t`
- Columns enclosed with: `"`
- Columns escaped with: *(blank)*
- Lines terminated with: auto

**Post-import manual fixes required (documented decisions):**
```sql
-- 1. Insert placeholder for unresolved gene IDs
INSERT INTO gene (entrez_gene_id, hugo_symbol)
VALUES (0, 'UNKNOWN - entrez_gene_id 0 indicates no known gene ID in source data');

-- 2. Remove stale gene symbols with duplicate Entrez IDs
DELETE FROM gene WHERE entrez_gene_id = 1903   AND hugo_symbol = 'C9orf47';
DELETE FROM gene WHERE entrez_gene_id = 23499  AND hugo_symbol = 'KIAA0754';
DELETE FROM gene WHERE entrez_gene_id = 284697 AND hugo_symbol = 'KIAA1107';
DELETE FROM gene WHERE entrez_gene_id = 399687 AND hugo_symbol = 'TIAF1';

-- 3. Correct known wrong Entrez ID
UPDATE gene SET entrez_gene_id = 441108 WHERE hugo_symbol = 'C5orf56';
```

---

## Step 4 — SNP selection queries
**Script:** `scripts/02_snp_selection_queries.sql`
**Input:** Populated MySQL database from Steps 2-3
**Output:** Selected SNPs for Neo4j import (run in phpMyAdmin, export as CSV)

Run in phpMyAdmin SQL tab. Use the final query in the file (HAVING >= 2 with mandatory dbsnp_rs) to produce the 5 selected SNPs. Export result as CSV.

---

## Step 5 — Create Neo4j graph
**Script:** `scripts/03_neo4j_import.cypher`
**Input:** None (hardcoded from SNP selection results)
**Output:** Neo4j graph with Gene, SNP, and Sample nodes and relationships

Run in Neo4j Browser (http://localhost:7474):
1. Open Neo4j Browser
2. Paste entire contents of `03_neo4j_import.cypher`
3. Click Run

To verify after import:
```cypher
MATCH (n)-[r]->(m) RETURN n, r, m
```

---

## Step 6 — API enrichment
**Script:** `scripts/04_api_enrichment.py`
**Input:** Running Neo4j instance from Step 5
**Output:** SNP and Gene nodes enriched with UniProt, dbSNP, ClinVar, STRING, and Grantham data

Update Neo4j password on line 19 before running:
```python
NEO4J_PASS = "your_neo4j_password"
```

```bash
python scripts/04_api_enrichment.py
```

APIs called (requires internet connection):
- UniProt REST API — protein metadata for each gene
- NCBI dbSNP API — population allele frequencies
- NCBI ClinVar E-utilities — clinical significance
- STRING API — protein-protein interaction network

Verify enrichment in Neo4j Browser:
```cypher
MATCH (s:SNP) RETURN s
MATCH (g:Gene) RETURN g
MATCH (a:Gene)-[r:INTERACTS_WITH]-(b:Gene) RETURN a, r, b
```

---

## Complete execution summary

```
Step 1  python scripts/01_clean_tcga_ccrcc.py
Step 2  mysql < sql/01_create_schema.sql
Step 3  Import TSVs via phpMyAdmin + run post-import SQL fixes
Step 4  Run snp_selection_queries.sql in phpMyAdmin
Step 5  Run neo4j_import.cypher in Neo4j Browser
Step 6  python scripts/04_api_enrichment.py
```

Total runtime: approximately 15-20 minutes excluding manual phpMyAdmin steps.
