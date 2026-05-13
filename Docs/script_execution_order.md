# Script Execution Order
## TCGA CCRCC Database Project

Execute scripts in the following order. Do not skip steps — each depends on the previous.

---

## Prerequisites

```bash
pip install pandas openpyxl requests neo4j

# Also required:
# MySQL 8.0+ running locally or via XAMPP/MAMP
# Neo4j Desktop 5.x running locally (bolt://localhost:7687)
# All of Us Researcher Workbench access (Registered Tier)
```

---

## Step 1 — Clean source data
**Script:** `scripts/01_clean_tcga_ccrcc.py`
**Input:** `data/raw/data_clinical_sample.txt`, `data/raw/data_mutations.txt`
**Output:** 7 TSV files in `data/cleaned/`

```bash
python scripts/01_clean_tcga_ccrcc.py
```

Performs: 4-row header skip, null normalization, boolean and numeric coercion, 5NF decomposition into 7 tables, QUOTE_ALL TSV output safe for phpMyAdmin import.

Expected output files:
```
patient.tsv  tissue_source_site.tsv  cancer_type.tsv  sample.tsv
gene.tsv  variant_class.tsv  mutation.tsv
```

---

## Step 2 — Create MySQL schema
**Script:** `sql/01_create_schema.sql`
**Input:** Empty MySQL instance
**Output:** `tcga_ccrcc` database with 7 empty tables

```bash
mysql -u root -p < sql/01_create_schema.sql
```

Creates all tables with correct types, PKs, FKs, and indexes. Uses DROP DATABASE IF EXISTS — safe to re-run.

---

## Step 3 — Load cleaned data into MySQL
**Script:** `sql/02_load_cleaned_data.sql` or manual phpMyAdmin import
**Input:** TSV files from Step 1
**Output:** All 7 tables populated

Import each file via phpMyAdmin in this exact order:

| Order | Table | File |
|---|---|---|
| 1 | patient | patient.tsv |
| 2 | tissue_source_site | tissue_source_site.tsv |
| 3 | cancer_type | cancer_type.tsv |
| 4 | sample | sample.tsv |
| 5 | gene | gene.tsv |
| 6 | variant_class | variant_class.tsv |
| 7 | mutation | mutation.tsv |

phpMyAdmin settings for every file:
- Format: CSV
- Columns separated with: `\t`
- Columns enclosed with: `"`
- Columns escaped with: *(blank)*
- Lines terminated with: auto

**Required post-import SQL fixes (run in phpMyAdmin SQL tab):**
```sql
SET FOREIGN_KEY_CHECKS = 0;

-- Placeholder for 744 genes with unresolved Entrez IDs in source MAF
INSERT INTO gene (entrez_gene_id, hugo_symbol)
VALUES (0, 'UNKNOWN - entrez_gene_id 0 indicates no known gene ID in source data');

-- Remove stale gene symbols sharing Entrez IDs with current approved symbols
DELETE FROM gene WHERE entrez_gene_id = 1903   AND hugo_symbol = 'C9orf47';
DELETE FROM gene WHERE entrez_gene_id = 23499  AND hugo_symbol = 'KIAA0754';
DELETE FROM gene WHERE entrez_gene_id = 284697 AND hugo_symbol = 'KIAA1107';
DELETE FROM gene WHERE entrez_gene_id = 399687 AND hugo_symbol = 'TIAF1';

-- Correct known wrong Entrez ID in source data
UPDATE gene SET entrez_gene_id = 441108 WHERE hugo_symbol = 'C5orf56';

SET FOREIGN_KEY_CHECKS = 1;
```

---

## Step 4 — SNP selection
**Script:** `scripts/02_snp_selection_queries.sql`
**Input:** Populated MySQL database
**Output:** 5 selected SNPs (export as CSV from phpMyAdmin)

Run the final query in the file in phpMyAdmin SQL tab. Criteria applied:
- filter_status = PASS
- variant_type = SNP, variant_classification = Missense_Mutation
- polyphen LIKE probably_damaging%, sift LIKE deleterious%
- dbsnp_rs IS NOT NULL and matches ^rs[0-9]+ format
- VAF ≥ 0.25
- HAVING COUNT(DISTINCT sample_id) ≥ 2
- LIMIT 5

Final 5 selected SNPs confirmed in All of Us:

| mutation_id | Gene | AA Change | rsID |
|---|---|---|---|
| 62 | VHL | p.H115N | rs5030811 |
| 10785 | ACADS | p.R330H | rs199633532 |
| 7393 | FNBP1L | p.R65W | rs774614978 |
| 3347 | BAK1 | p.R76W | rs766561404 |
| 16606 | EDIL3 | p.T343M | rs757863733 |

---

## Step 5 — Create Neo4j graph
**Script:** `scripts/03_neo4j_import.cypher`
**Input:** None (hardcoded from SNP selection results)
**Output:** Neo4j graph with Gene, SNP, Sample nodes and relationships

1. Open Neo4j Browser at http://localhost:7474
2. Paste entire contents of `03_neo4j_import.cypher`
3. Click Run

Verify:
```cypher
MATCH (n)-[r]->(m) RETURN n, r, m
```

Expected: 5 Gene nodes, 5 SNP nodes, 12 Sample nodes, HARBORS / IN_GENE / HAS_MUTATION relationships.

---

## Step 6 — API enrichment
**Script:** `scripts/04_api_enrichment.py`
**Input:** Running Neo4j instance from Step 5
**Output:** SNP and Gene nodes enriched with external data

Update NEO4J_PASS on line 19, then:
```bash
python scripts/04_api_enrichment.py
```

APIs called in order:
1. Grantham score — computed locally from lookup table
2. UniProt REST API — protein name, length, subcellular location, function
3. NCBI dbSNP API — global population allele frequency
4. NCBI ClinVar E-utilities — clinical significance and condition
5. STRING API — protein-protein interaction network (threshold=200)

Verify:
```cypher
MATCH (s:SNP) RETURN s.hugo_symbol, s.hgvsp_short, s.grantham_score,
       s.clinvar_significance, s.global_maf
MATCH (a:Gene)-[r:INTERACTS_WITH]-(b:Gene) RETURN a.hugo_symbol, r.string_score, b.hugo_symbol
```

---

## Step 7 — All of Us enrichment
**Script:** `scripts/05_allofus_enrichment.cypher` (pre-filled with real values)
**Input:** Running Neo4j instance from Step 6
**Output:** SNP nodes enriched with All of Us carrier counts and EHR data

The file is pre-filled with real values from the All of Us Controlled Tier Dataset v8 query. Simply paste and run in Neo4j Browser.

To reproduce the All of Us analysis from scratch:
1. Register at researchallofus.org with an institutional email
2. Complete CITI training modules (~3 hours)
3. Create a dataset in the Researcher Workbench using these GRCh38 variant IDs:
   - `1-93522134-C-T` (FNBP1L p.R65W)
   - `6-33575422-G-A` (BAK1 p.R76W)
   - `12-120738875-G-A` (ACADS p.R330H)
   - `5-84060409-G-A` (EDIL3 p.T343M)
4. Export to a Python notebook and run `scripts/allofus_analysis.py`
5. Update placeholder values in `05_allofus_enrichment.cypher` with real output

Verify:
```cypher
MATCH (s:SNP)
RETURN s.hugo_symbol, s.hgvsp_short, s.allofus_carrier_count,
       s.allofus_kidney_disease_n, s.allofus_notes
ORDER BY s.allofus_carrier_count DESC
```

---

## Complete Execution Summary

```
Step 1   python scripts/01_clean_tcga_ccrcc.py
Step 2   mysql < sql/01_create_schema.sql
Step 3   Import TSVs via phpMyAdmin + run 5 post-import SQL fixes
Step 4   Run 02_snp_selection_queries.sql in phpMyAdmin
Step 5   Run 03_neo4j_import.cypher in Neo4j Browser
Step 6   python scripts/04_api_enrichment.py
Step 7   Run 05_allofus_enrichment.cypher in Neo4j Browser
```

Estimated runtime: 20–30 minutes excluding phpMyAdmin manual steps and All of Us training.

**Shortcut:** Import `sql/database_dump.sql` directly into MySQL to skip Steps 1–4, then proceed from Step 5.
