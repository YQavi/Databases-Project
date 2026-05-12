"""
TCGA CCRCC — Data Cleaning Pipeline
====================================
Input files:
  - data_clinical_sample.txt  (512 samples, 19 columns; 4-row cBioPortal header)
  - data_mutations.txt        (31,073 mutations, 114 columns; MAF format)

Output: cleaned TSV files ready for SQL import
  - out/patient.tsv
  - out/tissue_source_site.tsv
  - out/cancer_type.tsv
  - out/sample.tsv
  - out/gene.tsv
  - out/variant_class.tsv
  - out/mutation.tsv

Normalization applied (1NF–5NF):
  1NF  — atomic values, no repeating groups, unique PKs
  2NF  — removed partial dependencies (cancer_type, tss moved out of sample)
  3NF  — removed transitive dependencies (grade codes decoded, no derived cols)
  4NF  — no multi-valued facts in one row
  5NF  — join dependencies decomposed into GENE and VARIANT_CLASS lookup tables
"""

import os
import re
import pandas as pd

# ── paths ──────────────────────────────────────────────────────────────────
SAMPLE_FILE   = "data_clinical_sample.txt"
MUTATION_FILE = "data_mutations.txt"
OUT_DIR       = "out"
os.makedirs(OUT_DIR, exist_ok=True)

# ── helpers ────────────────────────────────────────────────────────────────

def clean_bool(series: pd.Series) -> pd.Series:
    """Map Yes/No/NaN strings → 1/0/NULL."""
    return series.map({"Yes": 1, "No": 0}).where(series.notna(), other=None)

def null_dot(series: pd.Series) -> pd.Series:
    """cBioPortal uses '.' as NULL sentinel; replace with NaN."""
    return series.replace(".", pd.NA)

def strip_str(series: pd.Series) -> pd.Series:
    return series.str.strip()

def to_tsv(df: pd.DataFrame, name: str) -> None:
    path = os.path.join(OUT_DIR, f"{name}.tsv")
    df.to_csv(path, sep="\t", index=False, na_rep="\\N")  # \N = MySQL NULL
    print(f"  wrote {path}  ({len(df):,} rows × {len(df.columns)} cols)")

# ══════════════════════════════════════════════════════════════════════════
# STEP 1 — Load clinical sample file
#   cBioPortal format: 4 comment rows (lines starting with #), then header
# ══════════════════════════════════════════════════════════════════════════
print("\n[1] Loading data_clinical_sample.txt …")
raw = pd.read_csv(SAMPLE_FILE, sep="\t", skiprows=4, low_memory=False)

# Enforce consistent null: blank strings → NaN
raw.replace("", pd.NA, inplace=True)

print(f"    raw shape: {raw.shape}")

# ══════════════════════════════════════════════════════════════════════════
# STEP 2 — Clean & validate sample file columns
# ══════════════════════════════════════════════════════════════════════════
print("[2] Cleaning sample columns …")

raw["PATIENT_ID"] = strip_str(raw["PATIENT_ID"])
raw["SAMPLE_ID"]  = strip_str(raw["SAMPLE_ID"])

# Boolean indicators
raw["TISSUE_PROSPECTIVE"]   = clean_bool(raw["TISSUE_PROSPECTIVE_COLLECTION_INDICATOR"])
raw["TISSUE_RETROSPECTIVE"] = clean_bool(raw["TISSUE_RETROSPECTIVE_COLLECTION_INDICATOR"])

# Numeric columns — coerce bad values to NaN
for col in ["ANEUPLOIDY_SCORE", "MSI_SCORE_MANTIS", "MSI_SENSOR_SCORE",
            "TMB_NONSYNONYMOUS", "TBL_SCORE"]:
    raw[col] = pd.to_numeric(raw[col], errors="coerce")

# Validate FK: SAMPLE_ID must start with PATIENT_ID
bad_fk = raw[~raw.apply(lambda r: r["SAMPLE_ID"].startswith(r["PATIENT_ID"]), axis=1)]
if not bad_fk.empty:
    print(f"    WARNING: {len(bad_fk)} samples with mismatched PATIENT_ID prefix!")

# Duplicate check
dup_samples = raw[raw["SAMPLE_ID"].duplicated(keep=False)]
if not dup_samples.empty:
    print(f"    WARNING: {len(dup_samples)} duplicate SAMPLE_ID rows found — deduplicating.")
    raw = raw.drop_duplicates(subset="SAMPLE_ID", keep="first")

print(f"    cleaned shape: {raw.shape}")

# ══════════════════════════════════════════════════════════════════════════
# STEP 3 — Extract lookup tables (2NF / 3NF decomposition)
# ══════════════════════════════════════════════════════════════════════════
print("[3] Building lookup tables …")

# -- PATIENT (identity table; patient file absent, derive from sample) -----
patient = raw[["PATIENT_ID"]].drop_duplicates().reset_index(drop=True)
to_tsv(patient, "patient")

# -- TISSUE_SOURCE_SITE (tss_code → tss_name) --------------------------------
tss = (raw[["TISSUE_SOURCE_SITE_CODE", "TISSUE_SOURCE_SITE"]]
       .drop_duplicates()
       .rename(columns={"TISSUE_SOURCE_SITE_CODE": "tss_code",
                         "TISSUE_SOURCE_SITE": "tss_name"})
       .reset_index(drop=True))
to_tsv(tss, "tissue_source_site")

# -- CANCER_TYPE (oncotree_code → cancer_type attrs) --------------------------
cancer_type = (raw[["ONCOTREE_CODE", "CANCER_TYPE", "CANCER_TYPE_DETAILED",
                      "TUMOR_TYPE", "TUMOR_TISSUE_SITE"]]
               .drop_duplicates()
               .rename(columns={"ONCOTREE_CODE": "oncotree_code",
                                 "CANCER_TYPE": "cancer_type",
                                 "CANCER_TYPE_DETAILED": "cancer_type_detailed",
                                 "TUMOR_TYPE": "tumor_type",
                                 "TUMOR_TISSUE_SITE": "tumor_tissue_site"})
               .reset_index(drop=True))
to_tsv(cancer_type, "cancer_type")

# ══════════════════════════════════════════════════════════════════════════
# STEP 4 — Build SAMPLE fact table
# ══════════════════════════════════════════════════════════════════════════
print("[4] Building sample table …")

sample = raw[[
    "SAMPLE_ID", "PATIENT_ID", "ONCOTREE_CODE", "TISSUE_SOURCE_SITE_CODE",
    "GRADE", "TISSUE_PROSPECTIVE", "TISSUE_RETROSPECTIVE",
    "SAMPLE_TYPE", "SOMATIC_STATUS",
    "ANEUPLOIDY_SCORE", "MSI_SCORE_MANTIS", "MSI_SENSOR_SCORE",
    "TMB_NONSYNONYMOUS", "TBL_SCORE"
]].rename(columns={
    "SAMPLE_ID": "sample_id",
    "PATIENT_ID": "patient_id",
    "ONCOTREE_CODE": "oncotree_code",
    "TISSUE_SOURCE_SITE_CODE": "tss_code",
    "GRADE": "grade",
    "TISSUE_PROSPECTIVE": "tissue_prospective",
    "TISSUE_RETROSPECTIVE": "tissue_retrospective",
    "SAMPLE_TYPE": "sample_type",
    "SOMATIC_STATUS": "somatic_status",
    "ANEUPLOIDY_SCORE": "aneuploidy_score",
    "MSI_SCORE_MANTIS": "msi_score_mantis",
    "MSI_SENSOR_SCORE": "msi_sensor_score",
    "TMB_NONSYNONYMOUS": "tmb_nonsynonymous",
    "TBL_SCORE": "tbl_score",
}).copy()

to_tsv(sample, "sample")

# ══════════════════════════════════════════════════════════════════════════
# STEP 5 — Load mutations (select essential columns only)
# ══════════════════════════════════════════════════════════════════════════
print("[5] Loading data_mutations.txt (31k rows × 114 cols — selecting subset) …")

MUT_COLS = [
    "Hugo_Symbol", "Entrez_Gene_Id",
    "NCBI_Build", "Chromosome", "Start_Position", "End_Position",
    "Variant_Classification", "Variant_Type", "IMPACT",
    "Reference_Allele", "Tumor_Seq_Allele2",
    "dbSNP_RS", "Tumor_Sample_Barcode",
    "HGVSc", "HGVSp_Short", "Transcript_ID", "Protein_position",
    "Hotspot", "FILTER",
    "PolyPhen", "SIFT",
    "t_ref_count", "t_alt_count", "n_ref_count", "n_alt_count",
    "t_depth", "n_depth",
]

mut_raw = pd.read_csv(MUTATION_FILE, sep="\t", usecols=MUT_COLS, low_memory=False)
print(f"    loaded shape: {mut_raw.shape}")

# ══════════════════════════════════════════════════════════════════════════
# STEP 6 — Clean mutations
# ══════════════════════════════════════════════════════════════════════════
print("[6] Cleaning mutation columns …")

# Dot-null sentinel
for col in ["dbSNP_RS", "HGVSc", "HGVSp_Short", "Transcript_ID",
            "PolyPhen", "SIFT", "Chromosome"]:
    mut_raw[col] = null_dot(mut_raw[col])

# Hotspot: 0/NaN → 1/0 integer (NaN treated as 0)
mut_raw["Hotspot"] = mut_raw["Hotspot"].fillna(0).astype(int)

# Numeric coercion — cast float cols to pandas nullable Int64 so nulls
# write as empty string (not "\\N" or "400.0") in the TSV
for col in ["Entrez_Gene_Id", "Protein_position", "t_ref_count", "t_alt_count",
            "n_ref_count", "n_alt_count", "t_depth", "n_depth",
            "Start_Position", "End_Position"]:
    mut_raw[col] = pd.to_numeric(mut_raw[col], errors="coerce").astype("Int64")


# Strip whitespace
mut_raw["Hugo_Symbol"] = strip_str(mut_raw["Hugo_Symbol"])
mut_raw["Tumor_Sample_Barcode"] = strip_str(mut_raw["Tumor_Sample_Barcode"])

# Validate FK: Tumor_Sample_Barcode must exist in sample table
valid_samples = set(sample["sample_id"])
orphan = mut_raw[~mut_raw["Tumor_Sample_Barcode"].isin(valid_samples)]
if not orphan.empty:
    print(f"    WARNING: {len(orphan)} mutations reference unknown samples — will be excluded.")
    mut_raw = mut_raw[mut_raw["Tumor_Sample_Barcode"].isin(valid_samples)]

# Duplicate mutation check (same position + sample + allele)
dup_key = ["Tumor_Sample_Barcode", "Chromosome", "Start_Position",
           "Reference_Allele", "Tumor_Seq_Allele2"]
dup_muts = mut_raw[mut_raw.duplicated(subset=dup_key, keep=False)]
if not dup_muts.empty:
    print(f"    WARNING: {len(dup_muts)} duplicate mutation rows — deduplicating.")
    mut_raw = mut_raw.drop_duplicates(subset=dup_key, keep="first")

print(f"    cleaned shape: {mut_raw.shape}")

# ══════════════════════════════════════════════════════════════════════════
# STEP 7 — Extract GENE lookup table (5NF decomposition)
# ══════════════════════════════════════════════════════════════════════════
print("[7] Building gene lookup table …")

gene = (mut_raw[["Entrez_Gene_Id", "Hugo_Symbol"]]
        .dropna(subset=["Entrez_Gene_Id"])
        .drop_duplicates(subset=["Entrez_Gene_Id"])
        .rename(columns={"Entrez_Gene_Id": "entrez_gene_id",
                          "Hugo_Symbol": "hugo_symbol"})
        .astype({"entrez_gene_id": int})
        .reset_index(drop=True))
to_tsv(gene, "gene")

# ══════════════════════════════════════════════════════════════════════════
# STEP 8 — Extract VARIANT_CLASS lookup table
# ══════════════════════════════════════════════════════════════════════════
print("[8] Building variant_class lookup table …")

variant_class = (mut_raw[["Variant_Classification", "Variant_Type", "IMPACT"]]
                 .drop_duplicates(subset=["Variant_Classification"])
                 .rename(columns={"Variant_Classification": "variant_classification",
                                   "Variant_Type": "variant_type",
                                   "IMPACT": "impact"})
                 .reset_index(drop=True))
to_tsv(variant_class, "variant_class")

# ══════════════════════════════════════════════════════════════════════════
# STEP 9 — Build MUTATION fact table with surrogate PK
# ══════════════════════════════════════════════════════════════════════════
print("[9] Building mutation fact table …")

mutation = mut_raw.rename(columns={
    "Tumor_Sample_Barcode": "sample_id",
    "Entrez_Gene_Id": "entrez_gene_id",
    "Variant_Classification": "variant_classification",
    "NCBI_Build": "ncbi_build",
    "Chromosome": "chromosome",
    "Start_Position": "start_position",
    "End_Position": "end_position",
    "Reference_Allele": "reference_allele",
    "Tumor_Seq_Allele2": "tumor_seq_allele2",
    "dbSNP_RS": "dbsnp_rs",
    "HGVSc": "hgvsc",
    "HGVSp_Short": "hgvsp_short",
    "Transcript_ID": "transcript_id",
    "Protein_position": "protein_position",
    "Hotspot": "hotspot",
    "FILTER": "filter_status",
    "PolyPhen": "polyphen",
    "SIFT": "sift",
    "t_ref_count": "t_ref_count",
    "t_alt_count": "t_alt_count",
    "n_ref_count": "n_ref_count",
    "n_alt_count": "n_alt_count",
    "t_depth": "t_depth",
    "n_depth": "n_depth",
})[
    ["sample_id", "entrez_gene_id", "variant_classification",
     "ncbi_build", "chromosome", "start_position", "end_position",
     "reference_allele", "tumor_seq_allele2", "dbsnp_rs",
     "hgvsc", "hgvsp_short", "transcript_id", "protein_position",
     "hotspot", "filter_status", "polyphen", "sift",
     "t_ref_count", "t_alt_count", "n_ref_count", "n_alt_count",
     "t_depth", "n_depth"]
].copy()

# Add surrogate PK
mutation.insert(0, "mutation_id", range(1, len(mutation) + 1))

to_tsv(mutation, "mutation")

# ══════════════════════════════════════════════════════════════════════════
# DONE
# ══════════════════════════════════════════════════════════════════════════
print("\n✓ All output files written to ./out/")
print("  Load order for SQL (respects FK dependencies):")
print("  1. patient  2. tissue_source_site  3. cancer_type")
print("  4. sample   5. gene  6. variant_class  7. mutation")
