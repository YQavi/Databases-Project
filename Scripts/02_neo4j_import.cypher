// ============================================================
// TCGA CCRCC — Neo4j Graph Database
// SNP Characterization Graph
// ============================================================
// Node types:
//   (Gene)    — hugo_symbol, entrez_gene_id
//   (SNP)     — hgvsp_short, hgvsc, chromosome, position,
//               ref/alt allele, dbsnp_rs, polyphen, sift,
//               protein_position, transcript_id, impact
//   (Sample)  — sample_id, patient_id
//
// Relationship types:
//   (Gene)-[:HARBORS]->(SNP)
//   (Sample)-[:HAS_MUTATION {vaf}]->(SNP)
//   (SNP)-[:IN_GENE]->(Gene)        [back-reference for traversal]
// ============================================================

// ── Constraints (run once, ensures uniqueness) ───────────────
CREATE CONSTRAINT snp_id      IF NOT EXISTS FOR (s:SNP)    REQUIRE s.mutation_id       IS UNIQUE;
CREATE CONSTRAINT gene_id     IF NOT EXISTS FOR (g:Gene)   REQUIRE g.entrez_gene_id    IS UNIQUE;
CREATE CONSTRAINT sample_id   IF NOT EXISTS FOR (s:Sample) REQUIRE s.sample_id         IS UNIQUE;

// ── Indexes ──────────────────────────────────────────────────
CREATE INDEX snp_hgvsp   IF NOT EXISTS FOR (s:SNP)    ON (s.hgvsp_short);
CREATE INDEX gene_symbol IF NOT EXISTS FOR (g:Gene)   ON (g.hugo_symbol);

// ============================================================
// GENES
// ============================================================

MERGE (g:Gene {entrez_gene_id: 7428})
SET g.hugo_symbol   = 'VHL',
    g.full_name     = 'von Hippel-Lindau tumor suppressor',
    g.chromosome    = '3',
    g.role          = 'Tumor suppressor',
    g.pathway       = 'HIF/hypoxia signaling',
    g.ccrcc_driver  = true;

MERGE (g:Gene {entrez_gene_id: 2475})
SET g.hugo_symbol   = 'MTOR',
    g.full_name     = 'mechanistic target of rapamycin kinase',
    g.chromosome    = '1',
    g.role          = 'Oncogene',
    g.pathway       = 'PI3K/AKT/mTOR signaling',
    g.ccrcc_driver  = true;

MERGE (g:Gene {entrez_gene_id: 6928})
SET g.hugo_symbol   = 'HNF1B',
    g.full_name     = 'HNF1 homeobox B',
    g.chromosome    = '17',
    g.role          = 'Transcription factor',
    g.pathway       = 'Renal development / Wnt signaling',
    g.ccrcc_driver  = false;

MERGE (g:Gene {entrez_gene_id: 54874})
SET g.hugo_symbol   = 'FNBP1L',
    g.full_name     = 'formin binding protein 1 like',
    g.chromosome    = '1',
    g.role          = 'Regulator',
    g.pathway       = 'Actin cytoskeleton / endocytosis',
    g.ccrcc_driver  = false;

MERGE (g:Gene {entrez_gene_id: 578})
SET g.hugo_symbol   = 'BAK1',
    g.full_name     = 'BCL2 antagonist/killer 1',
    g.chromosome    = '6',
    g.role          = 'Tumor suppressor',
    g.pathway       = 'Apoptosis / BCL2 family',
    g.ccrcc_driver  = false;

// ============================================================
// SNPs
// ============================================================

MERGE (s:SNP {mutation_id: 62})
SET s.hugo_symbol          = 'VHL',
    s.hgvsp_short          = 'p.H115N',
    s.hgvsc                = 'ENST00000256474.2:c.343C>A',
    s.chromosome           = '3',
    s.start_position       = 10188200,
    s.reference_allele     = 'C',
    s.tumor_seq_allele2    = 'A',
    s.dbsnp_rs             = 'rs5030811',
    s.transcript_id        = 'ENST00000256474',
    s.protein_position     = 115,
    s.ref_aa               = 'H',
    s.alt_aa               = 'N',
    s.ref_aa_full          = 'Histidine',
    s.alt_aa_full          = 'Asparagine',
    s.variant_classification = 'Missense_Mutation',
    s.impact               = 'MODERATE',
    s.polyphen             = 'probably_damaging(0.993)',
    s.sift                 = 'deleterious(0)',
    s.n_samples            = 4,
    s.mean_vaf             = 0.3915;

MERGE (s:SNP {mutation_id: 9861})
SET s.hugo_symbol          = 'HNF1B',
    s.hgvsp_short          = 'p.N302K',
    s.hgvsc                = 'ENST00000225893.4:c.906C>G',
    s.chromosome           = '17',
    s.start_position       = 36091725,
    s.reference_allele     = 'G',
    s.tumor_seq_allele2    = 'C',
    s.dbsnp_rs             = null,
    s.transcript_id        = 'ENST00000225893',
    s.protein_position     = 302,
    s.ref_aa               = 'N',
    s.alt_aa               = 'K',
    s.ref_aa_full          = 'Asparagine',
    s.alt_aa_full          = 'Lysine',
    s.variant_classification = 'Missense_Mutation',
    s.impact               = 'MODERATE',
    s.polyphen             = 'probably_damaging(0.93)',
    s.sift                 = 'deleterious(0)',
    s.n_samples            = 2,
    s.mean_vaf             = 0.3420;

MERGE (s:SNP {mutation_id: 10329})
SET s.hugo_symbol          = 'MTOR',
    s.hgvsp_short          = 'p.L1460P',
    s.hgvsc                = 'ENST00000361445.4:c.4379T>C',
    s.chromosome           = '1',
    s.start_position       = 11217299,
    s.reference_allele     = 'A',
    s.tumor_seq_allele2    = 'G',
    s.dbsnp_rs             = 'rs1057519779',
    s.transcript_id        = 'ENST00000361445',
    s.protein_position     = 1460,
    s.ref_aa               = 'L',
    s.alt_aa               = 'P',
    s.ref_aa_full          = 'Leucine',
    s.alt_aa_full          = 'Proline',
    s.variant_classification = 'Missense_Mutation',
    s.impact               = 'MODERATE',
    s.polyphen             = 'probably_damaging(0.936)',
    s.sift                 = 'deleterious(0)',
    s.n_samples            = 2,
    s.mean_vaf             = 0.3408;

MERGE (s:SNP {mutation_id: 7393})
SET s.hugo_symbol          = 'FNBP1L',
    s.hgvsp_short          = 'p.R65W',
    s.hgvsc                = 'ENST00000271234.7:c.193C>T',
    s.chromosome           = '1',
    s.start_position       = 93987691,
    s.reference_allele     = 'C',
    s.tumor_seq_allele2    = 'T',
    s.dbsnp_rs             = 'rs774614978',
    s.transcript_id        = 'ENST00000271234',
    s.protein_position     = 65,
    s.ref_aa               = 'R',
    s.alt_aa               = 'W',
    s.ref_aa_full          = 'Arginine',
    s.alt_aa_full          = 'Tryptophan',
    s.variant_classification = 'Missense_Mutation',
    s.impact               = 'MODERATE',
    s.polyphen             = 'probably_damaging(0.962)',
    s.sift                 = 'deleterious(0)',
    s.n_samples            = 2,
    s.mean_vaf             = 0.3194;

MERGE (s:SNP {mutation_id: 3347})
SET s.hugo_symbol          = 'BAK1',
    s.hgvsp_short          = 'p.R76W',
    s.hgvsc                = 'ENST00000374467.3:c.226C>T',
    s.chromosome           = '6',
    s.start_position       = 33543199,
    s.reference_allele     = 'G',
    s.tumor_seq_allele2    = 'A',
    s.dbsnp_rs             = 'rs766561404',
    s.transcript_id        = 'ENST00000374467',
    s.protein_position     = 76,
    s.ref_aa               = 'R',
    s.alt_aa               = 'W',
    s.ref_aa_full          = 'Arginine',
    s.alt_aa_full          = 'Tryptophan',
    s.variant_classification = 'Missense_Mutation',
    s.impact               = 'MODERATE',
    s.polyphen             = 'probably_damaging(0.986)',
    s.sift                 = 'deleterious(0)',
    s.n_samples            = 2,
    s.mean_vaf             = 0.0720;

// ============================================================
// SAMPLES
// ============================================================

MERGE (:Sample {sample_id: 'TCGA-3Z-A93Z-01',  patient_id: 'TCGA-3Z-A93Z'});
MERGE (:Sample {sample_id: 'TCGA-A3-3382-01',  patient_id: 'TCGA-A3-3382'});
MERGE (:Sample {sample_id: 'TCGA-CJ-4643-01',  patient_id: 'TCGA-CJ-4643'});
MERGE (:Sample {sample_id: 'TCGA-CZ-5470-01',  patient_id: 'TCGA-CZ-5470'});
MERGE (:Sample {sample_id: 'TCGA-B0-5694-01',  patient_id: 'TCGA-B0-5694'});
MERGE (:Sample {sample_id: 'TCGA-CW-5580-01',  patient_id: 'TCGA-CW-5580'});
MERGE (:Sample {sample_id: 'TCGA-B0-5701-01',  patient_id: 'TCGA-B0-5701'});
MERGE (:Sample {sample_id: 'TCGA-BP-5175-01',  patient_id: 'TCGA-BP-5175'});
MERGE (:Sample {sample_id: 'TCGA-B0-5096-01',  patient_id: 'TCGA-B0-5096'});
MERGE (:Sample {sample_id: 'TCGA-BP-4161-01',  patient_id: 'TCGA-BP-4161'});
MERGE (:Sample {sample_id: 'TCGA-A3-A6NN-01',  patient_id: 'TCGA-A3-A6NN'});
MERGE (:Sample {sample_id: 'TCGA-G6-A5PC-01',  patient_id: 'TCGA-G6-A5PC'});

// ============================================================
// GENE → SNP RELATIONSHIPS
// ============================================================

MATCH (g:Gene {entrez_gene_id: 7428}),  (s:SNP {mutation_id: 62})    MERGE (g)-[:HARBORS]->(s) MERGE (s)-[:IN_GENE]->(g);
MATCH (g:Gene {entrez_gene_id: 6928}),  (s:SNP {mutation_id: 9861})  MERGE (g)-[:HARBORS]->(s) MERGE (s)-[:IN_GENE]->(g);
MATCH (g:Gene {entrez_gene_id: 2475}),  (s:SNP {mutation_id: 10329}) MERGE (g)-[:HARBORS]->(s) MERGE (s)-[:IN_GENE]->(g);
MATCH (g:Gene {entrez_gene_id: 54874}), (s:SNP {mutation_id: 7393})  MERGE (g)-[:HARBORS]->(s) MERGE (s)-[:IN_GENE]->(g);
MATCH (g:Gene {entrez_gene_id: 578}),   (s:SNP {mutation_id: 3347})  MERGE (g)-[:HARBORS]->(s) MERGE (s)-[:IN_GENE]->(g);

// ============================================================
// SAMPLE → SNP RELATIONSHIPS  (with VAF as edge property)
// ============================================================

// VHL p.H115N
MATCH (sa:Sample {sample_id: 'TCGA-3Z-A93Z-01'}), (s:SNP {mutation_id: 62})    MERGE (sa)-[:HAS_MUTATION {vaf: 0.2745}]->(s);
MATCH (sa:Sample {sample_id: 'TCGA-A3-3382-01'}), (s:SNP {mutation_id: 62})    MERGE (sa)-[:HAS_MUTATION {vaf: 0.6022}]->(s);
MATCH (sa:Sample {sample_id: 'TCGA-CJ-4643-01'}), (s:SNP {mutation_id: 62})    MERGE (sa)-[:HAS_MUTATION {vaf: 0.3179}]->(s);
MATCH (sa:Sample {sample_id: 'TCGA-CZ-5470-01'}), (s:SNP {mutation_id: 62})    MERGE (sa)-[:HAS_MUTATION {vaf: 0.3714}]->(s);

// HNF1B p.N302K
MATCH (sa:Sample {sample_id: 'TCGA-B0-5694-01'}), (s:SNP {mutation_id: 9861})  MERGE (sa)-[:HAS_MUTATION {vaf: 0.3451}]->(s);
MATCH (sa:Sample {sample_id: 'TCGA-CW-5580-01'}), (s:SNP {mutation_id: 9861})  MERGE (sa)-[:HAS_MUTATION {vaf: 0.3388}]->(s);

// MTOR p.L1460P
MATCH (sa:Sample {sample_id: 'TCGA-B0-5701-01'}), (s:SNP {mutation_id: 10329}) MERGE (sa)-[:HAS_MUTATION {vaf: 0.3810}]->(s);
MATCH (sa:Sample {sample_id: 'TCGA-BP-5175-01'}), (s:SNP {mutation_id: 10329}) MERGE (sa)-[:HAS_MUTATION {vaf: 0.3005}]->(s);

// FNBP1L p.R65W
MATCH (sa:Sample {sample_id: 'TCGA-B0-5096-01'}), (s:SNP {mutation_id: 7393})  MERGE (sa)-[:HAS_MUTATION {vaf: 0.1842}]->(s);
MATCH (sa:Sample {sample_id: 'TCGA-BP-4161-01'}), (s:SNP {mutation_id: 7393})  MERGE (sa)-[:HAS_MUTATION {vaf: 0.4545}]->(s);

// BAK1 p.R76W
MATCH (sa:Sample {sample_id: 'TCGA-A3-A6NN-01'}), (s:SNP {mutation_id: 3347})  MERGE (sa)-[:HAS_MUTATION {vaf: 0.0633}]->(s);
MATCH (sa:Sample {sample_id: 'TCGA-G6-A5PC-01'}), (s:SNP {mutation_id: 3347})  MERGE (sa)-[:HAS_MUTATION {vaf: 0.0806}]->(s);
