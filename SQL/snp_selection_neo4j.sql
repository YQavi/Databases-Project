SELECT
    MIN(m.mutation_id)                        AS representative_mutation_id,
    g.hugo_symbol,
    g.entrez_gene_id,
    m.chromosome,
    m.start_position,
    m.reference_allele,
    m.tumor_seq_allele2,
    m.hgvsc,
    m.hgvsp_short,
    m.protein_position,
    m.transcript_id,
    m.dbsnp_rs,
    vc.variant_classification,
    vc.impact,
    m.polyphen,
    m.sift,
    COUNT(DISTINCT m.sample_id)               AS n_samples,
    ROUND(AVG(m.t_alt_count / m.t_depth), 4) AS mean_vaf
FROM mutation m
JOIN gene          g  ON m.entrez_gene_id        = g.entrez_gene_id
JOIN variant_class vc ON m.variant_classification = vc.variant_classification
WHERE m.filter_status = 'PASS'
  AND vc.variant_type = 'SNP'
  AND vc.variant_classification = 'Missense_Mutation'
  AND m.polyphen LIKE 'probably_damaging%'
  AND m.sift     LIKE 'deleterious%'
  AND m.hgvsp_short IS NOT NULL
  AND m.dbsnp_rs IS NOT NULL
  AND m.dbsnp_rs != '.'
GROUP BY
    g.hugo_symbol,
    g.entrez_gene_id,
    m.chromosome,
    m.start_position,
    m.reference_allele,
    m.tumor_seq_allele2,
    m.hgvsc,
    m.hgvsp_short,
    m.protein_position,
    m.transcript_id,
    m.dbsnp_rs,
    vc.variant_classification,
    vc.impact,
    m.polyphen,
    m.sift
HAVING COUNT(DISTINCT m.sample_id) >= 2
ORDER BY n_samples DESC, mean_vaf DESC;
