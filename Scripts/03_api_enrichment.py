"""
03_api_enrichment.py
=====================
Enriches the 5 TCGA CCRCC SNPs in Neo4j with biological and chemical
data from four public REST APIs:

  1. UniProt  (EBI)   — protein function, length, subcellular location
  2. dbSNP    (NCBI)  — population allele frequency, global MAF
  3. ClinVar  (NCBI)  — clinical significance
  4. STRING           — protein-protein interaction network

Also computes Grantham scores locally (no API needed) to quantify
the chemical distance between reference and alternate amino acids.

Run AFTER:
  01_clean_tcga_ccrcc.py
  02_create_schema.sql / load data
  03_neo4j_import.cypher

Requirements:
  pip install requests neo4j

Neo4j connection: update NEO4J_URI, NEO4J_USER, NEO4J_PASS below.
"""

import requests
import time
from neo4j import GraphDatabase

# ── Neo4j connection ──────────────────────────────────────────
NEO4J_URI  = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASS = "admin"   # ← update this

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

# ── SNP manifest ─────────────────────────────────────────────
# All 5 selected SNPs with identifiers needed for each API
SNPS = [
    {
        "mutation_id":  62,
        "hugo_symbol":  "VHL",
        "uniprot_id":   "P40337",       # VHL human UniProt accession
        "dbsnp_rs":     "5030811",      # numeric only (no 'rs' prefix)
        "ref_aa":       "H",
        "alt_aa":       "N",
        "hgvsp_short":  "p.H115N",
    },
    {
        "mutation_id":  9861,
        "hugo_symbol":  "HNF1B",
        "uniprot_id":   "P35680",
        "dbsnp_rs":     None,           # no rs ID for this SNP
        "ref_aa":       "N",
        "alt_aa":       "K",
        "hgvsp_short":  "p.N302K",
    },
    {
        "mutation_id":  10329,
        "hugo_symbol":  "MTOR",
        "uniprot_id":   "P42345",
        "dbsnp_rs":     "1057519779",
        "ref_aa":       "L",
        "alt_aa":       "P",
        "hgvsp_short":  "p.L1460P",
    },
    {
        "mutation_id":  7393,
        "hugo_symbol":  "FNBP1L",
        "uniprot_id":   "Q9Y613",
        "dbsnp_rs":     "774614978",
        "ref_aa":       "R",
        "alt_aa":       "W",
        "hgvsp_short":  "p.R65W",
    },
    {
        "mutation_id":  3347,
        "hugo_symbol":  "BAK1",
        "uniprot_id":   "Q16611",
        "dbsnp_rs":     "766561404",
        "ref_aa":       "R",
        "alt_aa":       "W",
        "hgvsp_short":  "p.R76W",
    },
]

# Gene symbols for STRING PPI network query
GENE_SYMBOLS = [s["hugo_symbol"] for s in SNPS]

# ═══════════════════════════════════════════════════════════════
# GRANTHAM SCORE  (local — no API needed)
# Measures chemical distance between two amino acids.
# Score interpretation:
#   0–50   conservative
#   51–100 moderately conservative
#   101–150 moderately radical
#   >150   radical
# ═══════════════════════════════════════════════════════════════

# Grantham matrix — symmetric, 1-letter AA codes
# Source: Grantham R. (1974) Science 185:862-864
GRANTHAM = {
    ("A","R"):112,("A","N"):111,("A","D"):126,("A","C"):195,("A","Q"):91,
    ("A","E"):107,("A","G"):60, ("A","H"):86, ("A","I"):94, ("A","L"):96,
    ("A","K"):106,("A","M"):84, ("A","F"):113,("A","P"):27, ("A","S"):99,
    ("A","T"):58, ("A","W"):148,("A","Y"):112,("A","V"):64,
    ("R","N"):86, ("R","D"):96, ("R","C"):180,("R","Q"):43, ("R","E"):54,
    ("R","G"):125,("R","H"):29, ("R","I"):97, ("R","L"):102,("R","K"):26,
    ("R","M"):91, ("R","F"):97, ("R","P"):103,("R","S"):110,("R","T"):71,
    ("R","W"):101,("R","Y"):77, ("R","V"):96,
    ("N","D"):23, ("N","C"):139,("N","Q"):46, ("N","E"):42, ("N","G"):80,
    ("N","H"):68, ("N","I"):149,("N","L"):153,("N","K"):94, ("N","M"):142,
    ("N","F"):158,("N","P"):91, ("N","S"):46, ("N","T"):65, ("N","W"):174,
    ("N","Y"):143,("N","V"):133,
    ("D","C"):154,("D","Q"):61, ("D","E"):45, ("D","G"):94, ("D","H"):81,
    ("D","I"):168,("D","L"):172,("D","K"):101,("D","M"):160,("D","F"):177,
    ("D","P"):108,("D","S"):65, ("D","T"):85, ("D","W"):181,("D","Y"):160,
    ("D","V"):152,
    ("C","Q"):154,("C","E"):170,("C","G"):159,("C","H"):174,("C","I"):198,
    ("C","L"):198,("C","K"):202,("C","M"):196,("C","F"):205,("C","P"):169,
    ("C","S"):112,("C","T"):149,("C","W"):215,("C","Y"):194,("C","V"):192,
    ("Q","E"):29, ("Q","G"):87, ("Q","H"):24, ("Q","I"):109,("Q","L"):113,
    ("Q","K"):53, ("Q","M"):101,("Q","F"):116,("Q","P"):76, ("Q","S"):68,
    ("Q","T"):42, ("Q","W"):130,("Q","Y"):99, ("Q","V"):96,
    ("E","G"):98, ("E","H"):40, ("E","I"):134,("E","L"):138,("E","K"):56,
    ("E","M"):126,("E","F"):140,("E","P"):93, ("E","S"):80, ("E","T"):65,
    ("E","W"):152,("E","Y"):122,("E","V"):121,
    ("G","H"):98, ("G","I"):135,("G","L"):138,("G","K"):127,("G","M"):127,
    ("G","F"):153,("G","P"):42, ("G","S"):56, ("G","T"):59, ("G","W"):184,
    ("G","Y"):147,("G","V"):109,
    ("H","I"):94, ("H","L"):99, ("H","K"):32, ("H","M"):87, ("H","F"):100,
    ("H","P"):77, ("H","S"):89, ("H","T"):47, ("H","W"):115,("H","Y"):83,
    ("H","V"):84,
    ("I","L"):5,  ("I","K"):102,("I","M"):10, ("I","F"):21, ("I","P"):95,
    ("I","S"):142,("I","T"):89, ("I","W"):61, ("I","Y"):33, ("I","V"):29,
    ("L","K"):107,("L","M"):15, ("L","F"):22, ("L","P"):98, ("L","S"):145,
    ("L","T"):92, ("L","W"):61, ("L","Y"):36, ("L","V"):32,
    ("K","M"):95, ("K","F"):102,("K","P"):103,("K","S"):121,("K","T"):78,
    ("K","W"):110,("K","Y"):85, ("K","V"):97,
    ("M","F"):28, ("M","P"):87, ("M","S"):135,("M","T"):81, ("M","W"):67,
    ("M","Y"):36, ("M","V"):21,
    ("F","P"):114,("F","S"):155,("F","T"):103,("F","W"):40, ("F","Y"):22,
    ("F","V"):50,
    ("P","S"):74, ("P","T"):38, ("P","W"):147,("P","Y"):110,("P","V"):68,
    ("S","T"):58, ("S","W"):177,("S","Y"):144,("S","V"):124,
    ("T","W"):128,("T","Y"):92, ("T","V"):69,
    ("W","Y"):37, ("W","V"):88,
    ("Y","V"):55,
}

def grantham_score(aa1, aa2):
    """Return Grantham score between two 1-letter amino acid codes."""
    if aa1 == aa2:
        return 0
    key = (aa1, aa2) if (aa1, aa2) in GRANTHAM else (aa2, aa1)
    return GRANTHAM.get(key, None)

def grantham_label(score):
    if score is None:
        return "unknown"
    if score <= 50:
        return "conservative"
    if score <= 100:
        return "moderately conservative"
    if score <= 150:
        return "moderately radical"
    return "radical"

# ═══════════════════════════════════════════════════════════════
# 1. UNIPROT API
# ═══════════════════════════════════════════════════════════════

def fetch_uniprot(uniprot_id):
    """
    Fetch protein metadata from UniProt REST API.
    Endpoint: https://rest.uniprot.org/uniprotkb/{accession}.json
    Returns dict with function, length, subcellular location, disease.
    """
    url = f"https://rest.uniprot.org/uniprotkb/{uniprot_id}.json"
    headers = {"Accept": "application/json"}

    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()

        result = {
            "uniprot_id":         uniprot_id,
            "protein_name":       None,
            "protein_length":     None,
            "subcellular_location": None,
            "function":           None,
            "disease":            None,
        }

        # Protein recommended name
        try:
            result["protein_name"] = (
                data["proteinDescription"]
                    ["recommendedName"]
                    ["fullName"]["value"]
            )
        except (KeyError, TypeError):
            pass

        # Sequence length
        try:
            result["protein_length"] = data["sequence"]["length"]
        except (KeyError, TypeError):
            pass

        # Comments — function and subcellular location and disease
        for comment in data.get("comments", []):
            ctype = comment.get("commentType", "")

            if ctype == "FUNCTION" and result["function"] is None:
                try:
                    result["function"] = comment["texts"][0]["value"][:500]
                except (KeyError, IndexError):
                    pass

            if ctype == "SUBCELLULAR LOCATION" and result["subcellular_location"] is None:
                try:
                    locs = comment.get("subcellularLocations", [])
                    result["subcellular_location"] = "; ".join(
                        loc["location"]["value"] for loc in locs
                        if "location" in loc
                    )
                except (KeyError, TypeError):
                    pass

            if ctype == "DISEASE" and result["disease"] is None:
                try:
                    result["disease"] = comment["disease"]["diseaseId"]
                except (KeyError, TypeError):
                    pass

        return result

    except requests.exceptions.RequestException as e:
        print(f"  UniProt error for {uniprot_id}: {e}")
        return None

# ═══════════════════════════════════════════════════════════════
# 2. DBSNP API  (NCBI E-utilities)
# ═══════════════════════════════════════════════════════════════

def fetch_dbsnp(rs_id_numeric):
    """
    Fetch variant data from NCBI dbSNP via E-utilities.
    Endpoint: https://api.ncbi.nlm.nih.gov/variation/v0/beta/refsnp/{id}
    Returns global MAF and clinical significance if available.
    """
    if rs_id_numeric is None:
        return {"global_maf": None, "dbsnp_clinical_significance": None}

    url = f"https://api.ncbi.nlm.nih.gov/variation/v0/beta/refsnp/{rs_id_numeric}"
    headers = {"Accept": "application/json"}

    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()

        result = {
            "global_maf":                   None,
            "dbsnp_clinical_significance":  None,
        }

        # Global MAF from primary snapshot
        try:
            allele_annotations = (
                data.get("primary_snapshot_data", {})
                    .get("allele_annotations", [])
            )
            for ann in allele_annotations:
                for freq in ann.get("frequency", []):
                    if freq.get("observation", {}).get("obs_type") == "GLOBAL":
                        result["global_maf"] = freq.get("allele_count", {}).get("freq")
                        break
        except (KeyError, TypeError):
            pass

        # Clinical significance
        try:
            clin = data.get("primary_snapshot_data", {}).get("support", [])
            sigs = []
            for s in clin:
                sig = s.get("id", {}).get("type")
                if sig:
                    sigs.append(sig)
            if sigs:
                result["dbsnp_clinical_significance"] = "; ".join(set(sigs))
        except (KeyError, TypeError):
            pass

        return result

    except requests.exceptions.RequestException as e:
        print(f"  dbSNP error for rs{rs_id_numeric}: {e}")
        return {"global_maf": None, "dbsnp_clinical_significance": None}

# ═══════════════════════════════════════════════════════════════
# 3. CLINVAR API  (NCBI E-utilities)
# ═══════════════════════════════════════════════════════════════

def fetch_clinvar(rs_id_numeric):
    """
    Search ClinVar for a variant by rsID and return clinical significance.
    Uses NCBI E-utilities esearch + esummary.
    """
    if rs_id_numeric is None:
        return {"clinvar_significance": None, "clinvar_condition": None, "clinvar_review_stars": None}

    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    headers = {"Accept": "application/json"}

    try:
        # Step 1: search for the variant
        search_url = (
            f"{base}/esearch.fcgi"
            f"?db=clinvar&term=rs{rs_id_numeric}&retmode=json"
        )
        sr = requests.get(search_url, headers=headers, timeout=15)
        sr.raise_for_status()
        ids = sr.json().get("esearchresult", {}).get("idlist", [])

        if not ids:
            return {"clinvar_significance": "not in ClinVar",
                    "clinvar_condition": None,
                    "clinvar_review_stars": None}

        # Step 2: fetch summary for first hit
        uid = ids[0]
        summary_url = (
            f"{base}/esummary.fcgi"
            f"?db=clinvar&id={uid}&retmode=json"
        )
        time.sleep(0.35)   # NCBI rate limit: max 3 req/sec without API key
        dr = requests.get(summary_url, headers=headers, timeout=15)
        dr.raise_for_status()
        doc = dr.json().get("result", {}).get(uid, {})

        return {
            "clinvar_significance":  doc.get("clinical_significance", {}).get("description"),
            "clinvar_condition":     doc.get("trait_set", [{}])[0].get("trait_name") if doc.get("trait_set") else None,
            "clinvar_review_stars":  doc.get("clinical_significance", {}).get("review_status"),
        }

    except requests.exceptions.RequestException as e:
        print(f"  ClinVar error for rs{rs_id_numeric}: {e}")
        return {"clinvar_significance": None, "clinvar_condition": None, "clinvar_review_stars": None}

# ═══════════════════════════════════════════════════════════════
# 4. STRING API  — PPI network
# ═══════════════════════════════════════════════════════════════

def fetch_string_interactions(gene_list, species=9606, score_threshold=400):
    """
    Fetch protein-protein interactions from STRING for a list of gene symbols.
    species=9606 is Homo sapiens.
    score_threshold: 0-1000; 400=medium, 700=high, 900=very high confidence.
    Returns list of (gene_a, gene_b, score, interaction_type) tuples.
    """
    url = "https://string-db.org/api/json/network"
    params = {
        "identifiers":       "%0d".join(gene_list),  # newline-separated
        "species":           species,
        "required_score":    score_threshold,
        "network_type":      "functional",
        "add_nodes":         0,           # only interactions between submitted genes
        "show_query_node_labels": 1,
    }

    try:
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()

        interactions = []
        for edge in data:
            interactions.append({
                "gene_a":              edge.get("preferredName_A"),
                "gene_b":              edge.get("preferredName_B"),
                "string_score":        edge.get("score"),
                "experimental_score":  edge.get("escore"),
                "coexpression_score":  edge.get("coexpression"),
                "textmining_score":    edge.get("tscore"),
            })
        return interactions

    except requests.exceptions.RequestException as e:
        print(f"  STRING error: {e}")
        return []

# ═══════════════════════════════════════════════════════════════
# NEO4J WRITE FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def update_snp_node(tx, mutation_id, properties):
    """Add enriched properties to an existing SNP node."""
    set_clauses = ", ".join(f"s.{k} = ${k}" for k in properties)
    query = f"""
        MATCH (s:SNP {{mutation_id: $mutation_id}})
        SET {set_clauses}
    """
    tx.run(query, mutation_id=mutation_id, **properties)

def update_gene_node(tx, hugo_symbol, properties):
    """Add enriched properties to an existing Gene node."""
    set_clauses = ", ".join(f"g.{k} = ${k}" for k in properties)
    query = f"""
        MATCH (g:Gene {{hugo_symbol: $hugo_symbol}})
        SET {set_clauses}
    """
    tx.run(query, hugo_symbol=hugo_symbol, **properties)

def create_ppi_relationship(tx, gene_a, gene_b, props):
    """Create INTERACTS_WITH relationship between two Gene nodes."""
    query = """
        MATCH (a:Gene {hugo_symbol: $gene_a})
        MATCH (b:Gene {hugo_symbol: $gene_b})
        MERGE (a)-[r:INTERACTS_WITH]-(b)
        SET r.string_score        = $string_score,
            r.experimental_score  = $experimental_score,
            r.coexpression_score  = $coexpression_score,
            r.textmining_score    = $textmining_score,
            r.source              = 'STRING'
    """
    tx.run(query, gene_a=gene_a, gene_b=gene_b, **props)

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    print("\n" + "="*60)
    print("TCGA CCRCC — Neo4j API Enrichment Pipeline")
    print("="*60)

    with driver.session() as session:

        # ── Grantham scores (local, instant) ──────────────────
        print("\n[1] Computing Grantham scores (local)...")
        for snp in SNPS:
            score = grantham_score(snp["ref_aa"], snp["alt_aa"])
            label = grantham_label(score)
            props = {
                "grantham_score":          score,
                "grantham_label":          label,
                "ref_aa_full":             {
                    "H":"Histidine","N":"Asparagine","L":"Leucine",
                    "R":"Arginine","K":"Lysine","P":"Proline",
                    "W":"Tryptophan"
                }.get(snp["ref_aa"], snp["ref_aa"]),
                "alt_aa_full":             {
                    "H":"Histidine","N":"Asparagine","L":"Leucine",
                    "R":"Arginine","K":"Lysine","P":"Proline",
                    "W":"Tryptophan"
                }.get(snp["alt_aa"], snp["alt_aa"]),
                "charge_change":           _charge_change(snp["ref_aa"], snp["alt_aa"]),
                "polarity_change":         _polarity_change(snp["ref_aa"], snp["alt_aa"]),
                "hydrophobicity_change":   _hydrophobicity_change(snp["ref_aa"], snp["alt_aa"]),
            }
            session.execute_write(update_snp_node, snp["mutation_id"], props)
            print(f"  {snp['hugo_symbol']} {snp['hgvsp_short']}: "
                  f"Grantham={score} ({label})")

        # ── UniProt ───────────────────────────────────────────
        print("\n[2] Fetching UniProt protein data...")
        seen_genes = set()
        for snp in SNPS:
            if snp["hugo_symbol"] in seen_genes:
                continue
            seen_genes.add(snp["hugo_symbol"])

            print(f"  Querying UniProt for {snp['hugo_symbol']} ({snp['uniprot_id']})...")
            data = fetch_uniprot(snp["uniprot_id"])
            if data:
                gene_props = {
                    "uniprot_id":             data["uniprot_id"],
                    "protein_name":           data["protein_name"],
                    "protein_length":         data["protein_length"],
                    "subcellular_location":   data["subcellular_location"],
                    "protein_function":       data["function"],
                    "disease_association":    data["disease"],
                }
                session.execute_write(update_gene_node, snp["hugo_symbol"], gene_props)
                print(f"    ✓ {data['protein_name']} | length={data['protein_length']} | "
                      f"location={data['subcellular_location']}")
            time.sleep(0.5)

        # ── dbSNP ─────────────────────────────────────────────
        print("\n[3] Fetching dbSNP population frequencies...")
        for snp in SNPS:
            print(f"  Querying dbSNP for {snp['hugo_symbol']} {snp['hgvsp_short']}...")
            data = fetch_dbsnp(snp["dbsnp_rs"])
            props = {
                "global_maf":                   data["global_maf"],
                "dbsnp_clinical_significance":  data["dbsnp_clinical_significance"],
            }
            session.execute_write(update_snp_node, snp["mutation_id"], props)
            print(f"    ✓ global_maf={data['global_maf']} | "
                  f"significance={data['dbsnp_clinical_significance']}")
            time.sleep(0.35)

        # ── ClinVar ───────────────────────────────────────────
        print("\n[4] Fetching ClinVar clinical significance...")
        for snp in SNPS:
            print(f"  Querying ClinVar for {snp['hugo_symbol']} {snp['hgvsp_short']}...")
            data = fetch_clinvar(snp["dbsnp_rs"])
            props = {
                "clinvar_significance":  data["clinvar_significance"],
                "clinvar_condition":     data["clinvar_condition"],
                "clinvar_review_stars":  data["clinvar_review_stars"],
            }
            session.execute_write(update_snp_node, snp["mutation_id"], props)
            print(f"    ✓ significance={data['clinvar_significance']} | "
                  f"condition={data['clinvar_condition']}")
            time.sleep(0.35)

        # ── STRING PPI ────────────────────────────────────────
        print("\n[5] Fetching STRING protein-protein interactions...")
        interactions = fetch_string_interactions(GENE_SYMBOLS, score_threshold=400)
        if interactions:
            for edge in interactions:
                if edge["gene_a"] and edge["gene_b"]:
                    session.execute_write(create_ppi_relationship,
                                          edge["gene_a"], edge["gene_b"],
                                          {k: v for k, v in edge.items()
                                           if k not in ("gene_a", "gene_b")})
                    print(f"  ✓ {edge['gene_a']} ↔ {edge['gene_b']} "
                          f"(score={edge['string_score']})")
        else:
            print("  No interactions found above threshold between these 5 genes.")
            print("  Consider lowering score_threshold to 200 or adding interaction partners.")

    driver.close()
    print("\n✓ Enrichment complete. All properties written to Neo4j.")
    print("\nVerify in Neo4j Browser:")
    print("  MATCH (s:SNP) RETURN s")
    print("  MATCH (g:Gene) RETURN g")
    print("  MATCH (a:Gene)-[r:INTERACTS_WITH]-(b:Gene) RETURN a,r,b")


# ═══════════════════════════════════════════════════════════════
# AMINO ACID PROPERTY HELPERS (local, no API)
# ═══════════════════════════════════════════════════════════════

# Charge at physiological pH (7.4)
_CHARGE = {
    "R":"positive","K":"positive","H":"positive(weak)",
    "D":"negative","E":"negative",
    "A":"neutral","N":"neutral","C":"neutral","Q":"neutral",
    "G":"neutral","I":"neutral","L":"neutral","M":"neutral",
    "F":"neutral","P":"neutral","S":"neutral","T":"neutral",
    "W":"neutral","Y":"neutral","V":"neutral",
}

# Polarity
_POLARITY = {
    "R":"polar","K":"polar","H":"polar","D":"polar","E":"polar",
    "N":"polar","Q":"polar","S":"polar","T":"polar","Y":"polar","C":"polar",
    "A":"nonpolar","G":"nonpolar","I":"nonpolar","L":"nonpolar",
    "M":"nonpolar","F":"nonpolar","P":"nonpolar","V":"nonpolar","W":"nonpolar",
}

# Normalized hydrophobicity (Kyte-Doolittle scale)
_HYDROPHOBICITY = {
    "I":4.5,"V":4.2,"L":3.8,"F":2.8,"C":2.5,"M":1.9,"A":1.8,
    "G":-0.4,"T":-0.7,"S":-0.8,"W":-0.9,"Y":-1.3,"P":-1.6,
    "H":-3.2,"E":-3.5,"Q":-3.5,"D":-3.5,"N":-3.5,"K":-3.9,"R":-4.5,
}

def _charge_change(ref, alt):
    rc, ac = _CHARGE.get(ref,"unknown"), _CHARGE.get(alt,"unknown")
    if rc == ac:
        return "no change"
    return f"{rc} → {ac}"

def _polarity_change(ref, alt):
    rp, ap = _POLARITY.get(ref,"unknown"), _POLARITY.get(alt,"unknown")
    if rp == ap:
        return "no change"
    return f"{rp} → {ap}"

def _hydrophobicity_change(ref, alt):
    rh = _HYDROPHOBICITY.get(ref)
    ah = _HYDROPHOBICITY.get(alt)
    if rh is None or ah is None:
        return None
    return round(ah - rh, 2)   # positive = more hydrophobic after mutation


if __name__ == "__main__":
    main()
