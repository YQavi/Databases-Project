# Decisions and Limitations
## TCGA CCRCC Database Project

---

## Known Limitations

### Source Data Limitations

**Annotation freeze date.** The mutation file was annotated using GRCh37 (hg19) and VEP circa 2014–2016. Gene symbols, Entrez IDs, and functional predictions reflect the state of annotation at that time. 744 genes have Entrez_Gene_Id = 0 because they were not resolvable at annotation time, including genes since officially renamed (e.g. TCEB1 → ELOB, IL8 → CXCL8, PARK2 → PRKN).

**No patient clinical data.** The patient table contains only the TCGA patient barcode. Age, sex, stage, and survival data were absent from the downloaded cBioPortal files.

**Single cancer type.** All 512 samples are CCRCC. The cancer_type table has one row. The normalization benefit of that table only materializes when data from multiple cancer types is integrated.

**Hotspot column all zero.** All 31,073 mutation rows have hotspot = 0. No mutations in this cohort were flagged as known hotspot positions in the source MAF. The column is retained for schema completeness.

**BAK1 low VAF.** BAK1 p.R76W has a mean VAF of 0.072, substantially lower than the other four SNPs (0.23–0.39). This suggests a subclonal rather than clonal event. This is further supported by the All of Us data showing only 4 population carriers, consistent with a rare variant that may represent passenger noise rather than a driver event. It was retained because it met all filter criteria and the contrast with higher-VAF SNPs is analytically informative.

**VHL p.H115N absent from All of Us.** VHL p.H115N (rs5030811) was not returned in the All of Us Controlled Tier Dataset v8 query using GRCh38 coordinates. This may reflect coordinate discrepancy between GRCh37 (used in TCGA) and GRCh38 (used by All of Us), or the variant may be indexed under a different variant ID in the All of Us system. A LiftOver conversion from GRCh37 to GRCh38 would be required to confirm the correct coordinate for future queries.

---

### SNP Selection Decisions

**Selection criteria.** SNPs were selected using PASS filter, SNP variant type, Missense classification, PolyPhen probably_damaging, SIFT deleterious, mandatory dbSNP rsID (formatted as rs[digits]), VAF ≥ 0.25, and HAVING ≥ 2 samples. The VAF floor of 0.25 was applied to exclude likely subclonal variants. BAK1 p.R76W (VAF 0.072) is the only exception, retained because it passed all other filters and was confirmed in All of Us.

**Initial SNP selection was revised.** The first set of 5 SNPs included HNF1B p.N302K, MTOR p.L1460P, FNBP1L p.R65W, BAK1 p.R76W, and VHL p.H115N. HNF1B and MTOR p.L1460P were replaced after confirming that HNF1B p.N302K lacked a dbSNP rsID (preventing All of Us lookup) and the full selection pool was re-evaluated to prioritize variants confirmed present in the All of Us Controlled Tier. The final selection (VHL p.H115N, ACADS p.R330H, FNBP1L p.R65W, BAK1 p.R76W, EDIL3 p.T343M) was chosen because all four non-VHL SNPs returned confirmed carrier counts in All of Us.

**Non-canonical driver genes included.** ACADS, FNBP1L, BAK1, and EDIL3 are not established CCRCC driver genes. They were selected because they met the recurrence and functional impact criteria in the data and were confirmed in All of Us, making them suitable for population-level characterization. Their inclusion does not imply driver status.

---

### Database Design Decisions

**Surrogate key for mutation table.** A surrogate integer mutation_id was used rather than a composite natural key. The natural key spans five columns and would be unwieldy as a foreign key target. The surrogate key satisfies 1NF while maintaining join performance.

**reference_allele stored as TEXT.** Changed from VARCHAR(500) to TEXT during phpMyAdmin import troubleshooting. TEXT prevents indexing on this column; acceptable for this project since reference allele is not a query filter.

**protein_position stored as VARCHAR(10).** Changed from INT UNSIGNED due to null handling failures in phpMyAdmin CSV import. All values are numeric integers in practice.

**Six sample columns stored as VARCHAR.** tissue_prospective, tissue_retrospective, aneuploidy_score, msi_score_mantis, msi_sensor_score, and tmb_nonsynonymous were inferred as VARCHAR by phpMyAdmin during import. The intended types are documented in 01_create_schema.sql comments.

**Gene placeholder row (entrez_gene_id = 0).** A placeholder row was inserted rather than setting the FK nullable for 744 unresolvable genes, preserving FK integrity enforcement.

**Neo4j scoped to 5 SNPs.** The graph was intentionally limited to 5 SNPs for the purposes of this project. The selection criteria are fully documented in scripts/02_snp_selection_queries.sql.

---

### All of Us Limitations

**Kidney disease counts are pooled.** The 4 chronic kidney disease EHR diagnoses were identified across the combined 96-carrier pool, not per variant. Per-variant EHR attribution would require a separate BigQuery join for each variant's carrier set. The per-SNP kidney disease numbers in the Neo4j graph are proportional estimates, not exact counts.

**VHL p.H115N not found.** As noted above, VHL p.H115N was absent from the All of Us query results. Its allofus properties are set to null in the graph.

**All of Us genome version mismatch.** TCGA mutations are annotated on GRCh37. All of Us uses GRCh38. The four variant IDs used in the Workbench query (e.g. 1-93522134-C-T) are GRCh38 coordinates and may not exactly correspond to the GRCh37 positions in the TCGA MAF. A UCSC LiftOver conversion was not performed.

**Carrier counts reflect All of Us v8 snapshot.** The All of Us dataset grows over time. Carrier counts will increase in future dataset versions.

---

### API Limitations

**STRING interactions.** The five genes (VHL, ACADS, FNBP1L, BAK1, EDIL3) do not all have high-confidence direct interactions in STRING. INTERACTS_WITH edges may be sparse. The score threshold was set to 200 (medium-low confidence) to maximize coverage.

**NCBI rate limiting.** dbSNP and ClinVar API calls include 350ms delays to respect the NCBI rate limit of 3 requests/second without an API key.

---

### Reproducibility Notes

**phpMyAdmin manual steps.** Four post-import SQL fixes (placeholder gene row, three stale symbol deletions, one Entrez ID correction) are not automated and must be run manually after loading data. They are documented in docs/script_execution_order.md Step 4.

**All of Us access required.** Reproducing the All of Us enrichment step requires Registered Tier access, which requires completion of CITI training. The enrichment Cypher (05_allofus_enrichment.cypher) contains the real values from the query and can be run directly in Neo4j without re-running the Workbench analysis.

**SQL dump.** sql/database_dump.sql is a complete export of the populated database and can be used to bypass Steps 2–4 entirely.

---

## Future Work

- Perform UCSC LiftOver from GRCh37 to GRCh38 to resolve VHL p.H115N in All of Us
- Run per-variant kidney disease EHR joins in All of Us to replace proportional estimates with exact counts
- Integrate mRNA-seq expression data as an expression table to enable mutation-expression correlation queries
- Remap 744 zero-ID genes using current NCBI Homo_sapiens.gene_info to recover correct Entrez IDs for renamed genes
- Fix VARCHAR type deviations in the live sample table using ALTER TABLE to restore intended numeric types
- Extend the Neo4j graph to include all double-damaging missense SNPs at HAVING ≥ 2 for a more complete PPI network
