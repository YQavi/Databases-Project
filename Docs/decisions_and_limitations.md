# Decisions and Limitations
## TCGA CCRCC Database Project

---

## Known Limitations

### Source Data Limitations

**Annotation freeze date.** The mutation file was annotated using GRCh37 (hg19) and VEP circa 2014-2016. Gene symbols, Entrez IDs, and functional predictions reflect the state of annotation at that time. 744 genes have Entrez_Gene_Id = 0 because they were not resolvable at the time of annotation, including genes that have since been officially renamed (e.g. TCEB1 → ELOB, IL8 → CXCL8, PARK2 → PRKN).

**No patient clinical data.** The dataset includes `data_clinical_patient.txt` by name in the cBioPortal export, but no patient-level clinical variables (age, sex, stage, survival) were present in the downloaded files. The patient table therefore contains only the patient barcode as an identity record.

**Single cancer type.** All 512 samples are CCRCC (clear cell renal cell carcinoma). The `cancer_type` table has only one row. This is by design for this cohort but means the normalization benefit of that table only materializes when data from multiple cancer types is integrated.

**Hotspot column.** All 31,073 mutation rows have `hotspot = 0`. No mutations in this cohort were flagged as known hotspot positions in the source MAF. The column is retained for schema completeness and future data integration.

**BAK1 low VAF.** The BAK1 p.R76W SNP has a mean VAF of 0.072, substantially lower than the other four selected SNPs (0.18-0.39). This suggests the mutation may be subclonal rather than a clonal driver event. It was retained in the SNP selection because it met all filter criteria and provides a useful contrast case in the Neo4j graph.

---

### Database Design Decisions

**Surrogate key for mutation table.** A surrogate integer `mutation_id` was used rather than a composite natural key (sample + chromosome + position + allele). The natural key would span five columns and be unwieldy as a foreign key target. The surrogate key satisfies 1NF while keeping join performance practical.

**`reference_allele` stored as TEXT.** During phpMyAdmin import troubleshooting the column type was changed from VARCHAR(500) to TEXT. TEXT prevents indexing on this column. Since reference allele is not expected to be a query filter in this project this is acceptable, but would need to be reverted to VARCHAR(500) in a production system.

**`protein_position` stored as VARCHAR(10).** Originally designed as INT UNSIGNED, the column was changed to VARCHAR during import due to null handling issues with phpMyAdmin. The values are all numeric integers in practice but the type change was necessary to complete the import without custom LOAD DATA configuration.

**Sample-level constants retained in `sample` table.** `sample_type` (all Primary) and `somatic_status` (all Matched) have only one unique value in this cohort. These are not normalization violations — they are attributes of the sample, not of any other key — but they add no discriminatory information for this dataset. They are retained because they would carry meaningful information if the database were extended with other cancer types or unmatched samples.

**Gene placeholder row (entrez_gene_id = 0).** Rather than setting the FK column to nullable for all 744 unresolvable genes, a placeholder row was inserted into the gene table with entrez_gene_id = 0. This preserves FK integrity enforcement for future inserts while keeping the 744 affected mutations in the database rather than dropping them. The hugo_symbol of the placeholder is descriptive: `UNKNOWN - entrez_gene_id 0 indicates no known gene ID in source data`.

**Neo4j graph contains only 5 SNPs.** The full mutation table contains 31,073 rows. The Neo4j graph was scoped to 5 recurrently mutated, double-damaging missense SNPs for the purposes of this project. The selection criteria (PASS filter, SNP type, Missense classification, PolyPhen probably_damaging, SIFT deleterious, ≥2 samples, mandatory dbSNP rsID) are documented in `scripts/02_snp_selection_queries.sql`.

---

### API and Enrichment Limitations

**STRING interactions.** The 5 selected genes (VHL, HNF1B, MTOR, FNBP1L, BAK1) may not all have high-confidence direct interactions with each other in STRING. If `INTERACTS_WITH` edges are not created, lower the `score_threshold` parameter in `fetch_string_interactions()` from 400 to 200, or add known interaction partners to the gene list to expand the network context.

**HNF1B has no dbSNP rsID.** The SNP HNF1B p.N302K (mutation_id 9861) was not found in dbSNP at the time of the TCGA annotation. The dbSNP and ClinVar API calls will return null values for this SNP. This is expected behavior and does not indicate a script error.

**NCBI rate limiting.** The dbSNP and ClinVar API calls include 350ms delays between requests to respect the NCBI rate limit of 3 requests per second without an API key. If you have an NCBI API key, set it as an environment variable and pass it in the request headers to increase the limit to 10 requests per second.

---

### Reproducibility Notes

**phpMyAdmin manual steps.** Three post-import SQL fixes (placeholder gene row, stale symbol deletion, C5orf56 ID correction) were applied manually via the phpMyAdmin SQL tab and are not automated in the scripts. They are documented in `docs/script_execution_order.md` Step 3 and must be run manually after loading the data.

**SQL dump.** The `sql/database_dump.sql` file is a complete export of the populated database and can be used to skip Steps 1-3 entirely. Import it directly into MySQL to get the fully populated database without running the cleaning script or manual import steps.

---

## Future Work

- Integrate `data_mrna_seq` expression data as an `expression` table linking sample and gene, enabling mutation-expression correlation queries
- Remap the 744 zero-ID genes using the current NCBI Homo_sapiens.gene_info file to recover correct Entrez IDs for renamed genes
- Extend the Neo4j graph to include all double-damaging missense SNPs (approximately 50 unique amino acid changes at HAVING >= 2) for a more complete PPI network
- Add All of Us phenotype data to contextualize the 5 selected SNPs against population health outcomes
- Lift over coordinates from GRCh37 to GRCh38 using UCSC LiftOver to enable integration with newer annotation resources
