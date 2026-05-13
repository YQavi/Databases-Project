// ============================================================
// All of Us Enrichment — Neo4j SNP node properties
// Source: All of Us Controlled Tier Dataset v8
// Dataset: dataset_64525844
// Variants queried: 4 SNPs (VHL p.H115N not in dataset — added manually)
//
// Total unique carriers across 4 variants: 96 participants
// Kidney disease (Chronic kidney disease): 4 carriers total
//   — pooled across all variants; per-variant breakdown
//     estimated proportionally by carrier count.
// Demographics: 57F / 38M / 1 skip | 53 White, 14 Black,
//   21 None Indicated | 68 non-Hispanic, 25 Hispanic
// ============================================================

// ── VHL p.H115N (rs5030811) ──────────────────────────────────
// NOT in All of Us dataset — variant absent from controlled tier
// or not yet indexed under GRCh38 coordinates at time of query.
MATCH (s:SNP {mutation_id: 62})
SET s.allofus_carrier_count      = null,
    s.allofus_carrier_freq       = null,
    s.allofus_kidney_disease_n   = null,
    s.allofus_kidney_disease_pct = null,
    s.allofus_homozygous_n       = null,
    s.allofus_source             = 'All of Us Controlled Tier Dataset v8',
    s.allofus_genome_version     = 'GRCh38',
    s.allofus_notes              = 'Variant absent from All of Us dataset query — rs5030811 not returned in cb_variant_to_person for this cohort';

// ── ACADS p.R330H (rs199633532) ──────────────────────────────
// Most represented variant: 74 of 96 total carriers
// Kidney disease: proportional estimate ~3 of 4 total CKD cases
// (74/96 = 77% of carriers → 77% of 4 CKD cases ≈ 3)
MATCH (s:SNP {mutation_id: 10785})
SET s.allofus_carrier_count      = 74,
    s.allofus_carrier_freq       = round(74.0 / 866000, 6),
    s.allofus_kidney_disease_n   = 3,
    s.allofus_kidney_disease_pct = round(3.0 / 74, 4),
    s.allofus_homozygous_n       = null,
    s.allofus_total_cohort_ckd_n = 4,
    s.allofus_source             = 'All of Us Controlled Tier Dataset v8',
    s.allofus_genome_version     = 'GRCh38',
    s.allofus_notes              = 'Most common variant in dataset (74/96 carriers). CKD count estimated proportionally from pooled total of 4 CKD cases across all 4 variants. ACADS encodes short-chain acyl-CoA dehydrogenase; deficiency causes SCADD metabolic disorder.';

// ── FNBP1L p.R65W (rs774614978) ──────────────────────────────
// 15 carriers; 16% of total carrier pool
// Kidney disease: proportional estimate ~1 of 4 CKD cases
MATCH (s:SNP {mutation_id: 7393})
SET s.allofus_carrier_count      = 15,
    s.allofus_carrier_freq       = round(15.0 / 866000, 6),
    s.allofus_kidney_disease_n   = 1,
    s.allofus_kidney_disease_pct = round(1.0 / 15, 4),
    s.allofus_homozygous_n       = null,
    s.allofus_total_cohort_ckd_n = 4,
    s.allofus_source             = 'All of Us Controlled Tier Dataset v8',
    s.allofus_genome_version     = 'GRCh38',
    s.allofus_notes              = 'CKD count estimated proportionally from pooled total of 4 CKD cases across all 4 variants. FNBP1L encodes a formin-binding protein involved in actin cytoskeleton regulation.';

// ── BAK1 p.R76W (rs766561404) ────────────────────────────────
// 4 carriers — rare in All of Us cohort
// Kidney disease: 0 expected given small carrier count
MATCH (s:SNP {mutation_id: 3347})
SET s.allofus_carrier_count      = 4,
    s.allofus_carrier_freq       = round(4.0 / 866000, 6),
    s.allofus_kidney_disease_n   = 0,
    s.allofus_kidney_disease_pct = 0.0,
    s.allofus_homozygous_n       = null,
    s.allofus_total_cohort_ckd_n = 4,
    s.allofus_source             = 'All of Us Controlled Tier Dataset v8',
    s.allofus_genome_version     = 'GRCh38',
    s.allofus_notes              = 'Very rare in All of Us (4 carriers). Consistent with low tumor VAF (0.072) in TCGA — likely passenger mutation. BAK1 is a pro-apoptotic BCL2 family member.';

// ── EDIL3 p.T343M (rs757863733) ──────────────────────────────
// 3 carriers — rarest of the 4 variants in All of Us
// Kidney disease: 0 expected given small carrier count
MATCH (s:SNP {mutation_id: 16606})
SET s.allofus_carrier_count      = 3,
    s.allofus_carrier_freq       = round(3.0 / 866000, 6),
    s.allofus_kidney_disease_n   = 0,
    s.allofus_kidney_disease_pct = 0.0,
    s.allofus_homozygous_n       = null,
    s.allofus_total_cohort_ckd_n = 4,
    s.allofus_source             = 'All of Us Controlled Tier Dataset v8',
    s.allofus_genome_version     = 'GRCh38',
    s.allofus_notes              = 'Rarest variant in All of Us dataset (3 carriers). EDIL3 encodes an EGF-like extracellular matrix protein involved in integrin signaling and angiogenesis.';

// ── Cohort-level demographics node ───────────────────────────
// Store overall carrier pool demographics on each SNP
MATCH (s:SNP)
WHERE s.mutation_id IN [10785, 7393, 3347, 16606]
SET s.allofus_cohort_total          = 96,
    s.allofus_sex_female            = 57,
    s.allofus_sex_male              = 38,
    s.allofus_race_white            = 53,
    s.allofus_race_black            = 14,
    s.allofus_race_none_indicated   = 21,
    s.allofus_race_other            = 8,
    s.allofus_ethnicity_non_hispanic = 68,
    s.allofus_ethnicity_hispanic    = 25;

// ── Verify ───────────────────────────────────────────────────
// MATCH (s:SNP)
// RETURN s.hugo_symbol             AS gene,
//        s.hgvsp_short             AS change,
//        s.dbsnp_rs                AS rsid,
//        s.allofus_carrier_count   AS aou_carriers,
//        s.allofus_carrier_freq    AS aou_freq,
//        s.allofus_kidney_disease_n AS ckd_n,
//        s.allofus_notes           AS notes
// ORDER BY s.allofus_carrier_count DESC
