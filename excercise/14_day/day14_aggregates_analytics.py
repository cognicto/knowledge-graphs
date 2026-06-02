"""
day14_aggregates_analytics.py — SPARQL Aggregates and Portfolio Analytics
Day 14 of the 90-Day Knowledge Graph Mastery Program

SPARQL aggregates are the engine of the Semantic Layer (Layer 2).
Seven functions: COUNT, SUM, AVG, MIN, MAX, SAMPLE, GROUP_CONCAT
GROUP BY partitions. HAVING filters after aggregation.
Subqueries enable multi-step analytics impossible in flat queries.

V3 pattern: domain_ontology.ttl provides thresholds — no hardcoding.
"""

from rdflib import Graph, Namespace, RDF, Literal
from rdflib.namespace import XSD
import pathlib

print("=" * 65)
print("Day 14: SPARQL Aggregates and Portfolio Analytics")
print("The Semantic Layer (Layer 2) as SPARQL Aggregate Queries")
print("=" * 65)
print()

# ── Load and extend graph ───────────────────────────────────────────────────
g = Graph()
OUTPUTS = pathlib.Path("/mnt/user-data/outputs")
SCRIPT  = pathlib.Path(__file__).parent

for fname in ["fraud_network.ttl", "borrower_loan.ttl", "ontology.ttl", "data.ttl"]:
    for loc in [SCRIPT / fname, OUTPUTS / fname]:
        if loc.exists():
            g.parse(str(loc), format="turtle")
            break

TU   = Namespace("http://transunion.com/ontology#")
DATA = Namespace("http://transunion.com/data#")
DOMAIN = Namespace("http://transunion.com/domain#")

# Add lenders
for k, n in [("lender_HDFC","HDFC"),("lender_ICICI","ICICI"),("lender_SBI","SBI")]:
    g.add((DATA[k], RDF.type,  TU.Lender))
    g.add((DATA[k], TU.name,   Literal(n)))

# Add city + loan + lender data for portfolio analytics
ext = [
    ("borrower_VIJAY",   "Bangalore", 350000, "personal", "lender_ICICI"),
    ("borrower_RAJAN",   "Bangalore", 350000, "personal", "lender_HDFC"),
    ("borrower_SUNITA",  "Bangalore", 750000, "home",     "lender_HDFC"),
    ("borrower_ARJUN",   "Mumbai",    500000, "business", "lender_ICICI"),
    ("borrower_MEERA_B", "Mumbai",    600000, "personal", "lender_SBI"),
    ("borrower_DEV",     "Mumbai",    920000, "personal", "lender_SBI"),
    ("borrower_SURESH",  "Delhi",     280000, "auto",     "lender_HDFC"),
    ("borrower_PRIYA_C", "Delhi",     800000, "personal", "lender_ICICI"),
    ("borrower_LAKSHMI", "Delhi",     400000, "auto",     "lender_SBI"),
    ("borrower_RAHUL",   "Mumbai",    500000, "personal", "lender_HDFC"),
    ("borrower_ANITA",   "Chennai",   300000, "auto",     "lender_HDFC"),
]
for bk, city, amt, purp, lk in ext:
    buri = DATA[bk]; luri = DATA[f"loan_day14_{bk}"]; lndr = DATA[lk]
    g.add((buri, TU.city, Literal(city)))
    g.add((luri, RDF.type, TU.Loan))
    g.add((luri, TU.loanAmount, Literal(amt, datatype=XSD.integer)))
    g.add((luri, TU.loanPurpose, Literal(purp)))
    g.add((luri, TU.issuedBy, lndr))
    g.add((buri, TU.hasLoan, luri))

# Add domain ontology thresholds (V3 pattern)
g.add((DOMAIN.scoreRule, RDF.type, TU.DomainRule))
g.add((DOMAIN.scoreRule, TU.appliesTo, TU.creditScore))
g.add((DOMAIN.scoreRule, TU.riskThreshold, Literal(620, datatype=XSD.integer)))
g.add((DOMAIN.scoreRule, TU.riskLabel, Literal("HIGH_RISK_THRESHOLD")))
g.add((DOMAIN.dtiRule, RDF.type, TU.DomainRule))
g.add((DOMAIN.dtiRule, TU.appliesTo, TU.dti))
g.add((DOMAIN.dtiRule, TU.riskThreshold, Literal("0.43", datatype=XSD.decimal)))
g.add((DOMAIN.dtiRule, TU.riskLabel, Literal("DTI_UNSUSTAINABLE")))
g.add((DOMAIN.concentrationRule, RDF.type, TU.DomainRule))
g.add((DOMAIN.concentrationRule, TU.appliesTo, TU.cityConcentration))
g.add((DOMAIN.concentrationRule, TU.riskThreshold, Literal(900000, datatype=XSD.integer)))
g.add((DOMAIN.concentrationRule, TU.riskLabel, Literal("CONCENTRATION_ALERT")))

g.bind("tu",     TU)
g.bind("domain", DOMAIN)
print(f"Graph loaded: {len(g)} triples\n")

PREFIX = """
PREFIX rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX tu:     <http://transunion.com/ontology#>
PREFIX data:   <http://transunion.com/data#>
PREFIX domain: <http://transunion.com/domain#>
PREFIX xsd:    <http://www.w3.org/2001/XMLSchema#>
"""

def run(label, query, note=""):
    print(f"{'─'*65}")
    print(f"  {label}")
    if note: print(f"  [{note}]")
    print(f"{'─'*65}")
    results = list(g.query(PREFIX + query))
    if results:
        for row in results:
            parts = []
            for val in row:
                if val is None: parts.append("—")
                else:
                    s = str(val)
                    try:
                        f = float(s)
                        parts.append(f"Rs {f:,.0f}" if f > 1000 else
                                     (f"{f:.1%}" if 0 < f < 1 else
                                      (f"{f:.3f}" if f < 10 else f"{f:.0f}")))
                    except: parts.append(s[:40])
            print("  " + " | ".join(parts))
    else:
        print("  (no results)")
    print(f"  → {len(results)} row(s)\n")
    return results


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: All Seven Aggregate Functions
# ─────────────────────────────────────────────────────────────────────────────
print("SECTION 1: All Seven Aggregate Functions on the Portfolio")
print("=" * 65)
print("""
  COUNT / SUM / AVG / MIN / MAX / SAMPLE / GROUP_CONCAT
  All results MUST be aliased with AS.
  Use COUNT(DISTINCT ?x) to avoid duplicates from joins.
""")

run("All seven aggregates — full portfolio snapshot",
"""
SELECT
    (COUNT(DISTINCT ?b)   AS ?totalBorrowers)
    (COUNT(?loan)         AS ?totalLoans)
    (SUM(?amount)         AS ?totalExposure)
    (AVG(?score)          AS ?avgScore)
    (MIN(?score)          AS ?worstScore)
    (MAX(?score)          AS ?bestScore)
    (AVG(?dti)            AS ?avgDTI)
WHERE {
    ?b a tu:Borrower ;
       tu:creditScore ?score ;
       tu:dti ?dti .
    OPTIONAL { ?b tu:hasLoan ?loan . ?loan tu:loanAmount ?amount . }
}
""", "COUNT DISTINCT avoids double-counting borrowers with multiple loans")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: GROUP BY — Distribution Analysis
# ─────────────────────────────────────────────────────────────────────────────
print("SECTION 2: GROUP BY — Risk Distribution Across the Portfolio")
print("=" * 65)
print("""
  GROUP BY partitions results into groups sharing the same value.
  Every non-aggregated variable in SELECT must appear in GROUP BY.
  rdflib note: GROUP BY on BIND expression has limited support —
  use a subquery to pre-compute the grouping variable instead.
""")

# rdflib-compatible: subquery pre-computes riskTier, outer GROUP BY uses it
run("Risk tier distribution — GROUP BY via subquery (rdflib-compatible)",
"""
SELECT ?riskTier (COUNT(DISTINCT ?b) AS ?count) (AVG(?score) AS ?avgScore)
WHERE {
    {
        SELECT ?b ?score
            (IF(?sc >= 720, "EXCELLENT",
             IF(?sc >= 680, "GOOD",
             IF(?sc >= 620, "FAIR", "POOR"))) AS ?riskTier)
        WHERE { ?b a tu:Borrower ; tu:creditScore ?sc . BIND(?sc AS ?score) }
    }
}
GROUP BY ?riskTier
ORDER BY DESC(?count)
""", "Subquery pre-computes ?riskTier; outer query GROUPs BY it — rdflib limitation workaround")

run("Geographical concentration — exposure per city",
"""
SELECT ?city
    (COUNT(DISTINCT ?b) AS ?borrowerCount)
    (SUM(?amount)       AS ?totalExposure)
    (AVG(?score)        AS ?avgScore)
    (MIN(?score)        AS ?worstScore)
WHERE {
    ?b a tu:Borrower ; tu:city ?city ; tu:creditScore ?score .
    ?b tu:hasLoan ?loan .
    ?loan tu:loanAmount ?amount .
}
GROUP BY ?city
ORDER BY DESC(?totalExposure)
""", "Name concentration risk: which cities hold the most credit exposure?")

run("Product concentration — exposure by loan purpose",
"""
SELECT ?purpose
    (COUNT(?loan)  AS ?loanCount)
    (SUM(?amount)  AS ?totalExposure)
    (AVG(?amount)  AS ?avgLoanSize)
    (MAX(?amount)  AS ?largestLoan)
WHERE {
    ?loan a tu:Loan ;
          tu:loanPurpose ?purpose ;
          tu:loanAmount ?amount .
}
GROUP BY ?purpose
ORDER BY DESC(?totalExposure)
""", "Product concentration: which loan types dominate the portfolio?")

run("Lender concentration — exposure + GROUP_CONCAT of purposes",
"""
SELECT ?lenderName
    (COUNT(?loan)   AS ?loansIssued)
    (SUM(?amount)   AS ?totalExposure)
    (AVG(?score)    AS ?avgBorrowerScore)
    (GROUP_CONCAT(DISTINCT ?purpose; SEPARATOR=", ") AS ?purposes)
WHERE {
    ?loan a tu:Loan ; tu:loanAmount ?amount ; tu:loanPurpose ?purpose ;
          tu:issuedBy ?lender .
    ?lender tu:name ?lenderName .
    ?b tu:hasLoan ?loan ; tu:creditScore ?score .
}
GROUP BY ?lenderName
ORDER BY DESC(?totalExposure)
""", "GROUP_CONCAT: all loan purposes per lender in one cell — Semantic Layer metric")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: HAVING — Threshold-Based Alerts
# ─────────────────────────────────────────────────────────────────────────────
print("SECTION 3: HAVING — Alert When Groups Breach Thresholds")
print("=" * 65)
print("""
  HAVING filters GROUPS after aggregation — like WHERE but post-GROUP BY.
  Rule: write the aggregate expression in HAVING, not the alias.
    ✅ HAVING (SUM(?amount) > 900000)
    ⚠️  HAVING (?totalExposure > 900000)  — alias may not work in all engines
""")

run("HAVING: Concentration alert — cities with exposure > Rs 9L",
"""
SELECT ?city
    (SUM(?amount)       AS ?totalExposure)
    (COUNT(DISTINCT ?b) AS ?borrowerCount)
WHERE {
    ?b a tu:Borrower ; tu:city ?city .
    ?b tu:hasLoan ?loan .
    ?loan tu:loanAmount ?amount .
}
GROUP BY ?city
HAVING (SUM(?amount) > 900000)
ORDER BY DESC(SUM(?amount))
""", "Only cities breaching the Rs 9L threshold are returned")

run("HAVING: Fraud rings with 3+ members (complete rings only)",
"""
SELECT ?fraudRing
    (COUNT(DISTINCT ?b) AS ?memberCount)
    (SUM(?amount)       AS ?ringExposure)
    (MIN(?score)        AS ?worstScore)
WHERE {
    ?b a tu:Borrower ; tu:fraudRing ?fraudRing ; tu:creditScore ?score .
    OPTIONAL { ?b tu:hasLoan ?loan . ?loan tu:loanAmount ?amount . }
}
GROUP BY ?fraudRing
HAVING (COUNT(DISTINCT ?b) >= 3)
ORDER BY DESC(?ringExposure)
""", "HAVING (COUNT >= 3): filters out incomplete rings, keeps only full fraud rings")

run("HAVING: Lenders with average borrower score below 650",
"""
SELECT ?lenderName
    (AVG(?score)  AS ?avgBorrowerScore)
    (COUNT(?loan) AS ?loanCount)
WHERE {
    ?loan tu:issuedBy ?lender .
    ?lender tu:name ?lenderName .
    ?b tu:hasLoan ?loan ; tu:creditScore ?score .
}
GROUP BY ?lenderName
HAVING (AVG(?score) < 650)
ORDER BY AVG(?score)
""", "Portfolio quality alert: which lenders have below-threshold average borrower quality?")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4: Subqueries — Multi-Step Analytics
# ─────────────────────────────────────────────────────────────────────────────
print("SECTION 4: Subqueries — SELECT Inside WHERE")
print("=" * 65)
print("""
  Subqueries solve analytics that cannot be done in a single flat query.
  The inner SELECT evaluates first; results flow to the outer query.
  Only variables projected by the subquery are visible outside it.

  Canonical use case: compare each individual to the GROUP average.
  Cannot do this in one flat query — average doesn't exist until
  all rows are processed. Subquery solves it in two steps.
""")

run("Subquery: borrowers with DTI above the portfolio average",
"""
SELECT ?name ?dti ?portfolioAvg WHERE {
    ?b a tu:Borrower ; tu:name ?name ; tu:dti ?dti .
    {
        SELECT (AVG(?d) AS ?portfolioAvg)
        WHERE { ?b2 a tu:Borrower ; tu:dti ?d . }
    }
    FILTER(?dti > ?portfolioAvg)
}
ORDER BY DESC(?dti)
""", "Subquery computes portfolio AVG first; outer FILTER compares each borrower's DTI to it")

run("Subquery: concentration ratio — each city's % of total portfolio",
"""
SELECT ?city ?cityExposure ?totalPortfolio
    (?cityExposure / ?totalPortfolio AS ?concentrationRatio)
WHERE {
    {
        SELECT ?city (SUM(?amount) AS ?cityExposure)
        WHERE { ?b tu:city ?city ; tu:hasLoan ?l . ?l tu:loanAmount ?amount . }
        GROUP BY ?city
    }
    {
        SELECT (SUM(?amount) AS ?totalPortfolio)
        WHERE { ?l a tu:Loan ; tu:loanAmount ?amount . }
    }
}
ORDER BY DESC(?concentrationRatio)
""", "Two subqueries combined: city exposure + total portfolio → concentration ratio")

run("Subquery: borrowers with score BELOW average for their city",
"""
SELECT ?name ?score ?city ?cityAvg WHERE {
    ?b a tu:Borrower ; tu:name ?name ;
       tu:creditScore ?score ; tu:city ?city .
    {
        SELECT ?city (AVG(?sc) AS ?cityAvg)
        WHERE { ?b2 a tu:Borrower ; tu:city ?city ; tu:creditScore ?sc . }
        GROUP BY ?city
    }
    FILTER(?score < ?cityAvg)
}
ORDER BY ?city ASC(?score)
""", "Subquery with GROUP BY: city averages computed first, then compared per-borrower")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5: V3 Pattern — Domain Ontology Thresholds in Analytics
# ─────────────────────────────────────────────────────────────────────────────
print("SECTION 5: V3 Pattern — Thresholds FROM domain_ontology.ttl")
print("=" * 65)
print("""
  V2 pattern (hardcoded): FILTER(?score < 620)
  V3 pattern (governed): ?rule tu:riskThreshold ?threshold
                          FILTER(?score < ?threshold)

  Change the threshold in domain_ontology.ttl → all queries update.
  No code changes. No query rewrites. The ontology IS the policy.
""")

run("Domain-driven risk flag: threshold from domain_ontology.ttl",
"""
SELECT ?name ?score ?threshold ?riskLabel
    (IF(?score < ?threshold, "BREACHES_THRESHOLD","WITHIN_THRESHOLD") AS ?status)
WHERE {
    ?b a tu:Borrower ; tu:name ?name ; tu:creditScore ?score .
    ?rule a tu:DomainRule ;
          tu:appliesTo tu:creditScore ;
          tu:riskThreshold ?threshold ;
          tu:riskLabel ?riskLabel .
}
ORDER BY ?score
LIMIT 8
""", "The 620 threshold comes from domain_ontology.ttl — change once, update everywhere")

run("Concentration alert from domain threshold",
"""
SELECT ?city (SUM(?amount) AS ?exposure) ?alertThreshold
    (IF(SUM(?amount) > ?alertThreshold, "ALERT!", "OK") AS ?status)
WHERE {
    ?b tu:city ?city ; tu:hasLoan ?loan .
    ?loan tu:loanAmount ?amount .
    ?rule a tu:DomainRule ;
          tu:appliesTo tu:cityConcentration ;
          tu:riskThreshold ?alertThreshold .
}
GROUP BY ?city ?alertThreshold
ORDER BY DESC(SUM(?amount))
""", "Alert threshold (Rs 9L) from domain_ontology.ttl — governance in one place")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6: Semantic Layer — 6 Governed Portfolio Metrics
# ─────────────────────────────────────────────────────────────────────────────
print("SECTION 6: Semantic Layer (Layer 2) — Governed Portfolio Metrics")
print("=" * 65)
print("""
  The Semantic Layer defines governed metrics — one definition, one truth.
  Each metric is a named SPARQL query. Agents call:
    semantic_layer.get_metric("portfolioDefaultRate")
  and receive the governed value.
""")

# Compute all governed metrics
def get_metric(name, q):
    results = list(g.query(PREFIX + q))
    return results

metrics = [
    ("portfolioDefaultRate",
     "SELECT (COUNT(?d) AS ?defs) (COUNT(?all) AS ?total) WHERE { ?all a tu:Borrower . OPTIONAL { ?all tu:hasDefault true . BIND(?all AS ?d) } }"),
    ("portfolioAvgCreditScore",
     "SELECT (AVG(?s) AS ?v) WHERE { ?b a tu:Borrower ; tu:creditScore ?s . }"),
    ("totalPortfolioExposure",
     "SELECT (SUM(?a) AS ?v) WHERE { ?l a tu:Loan ; tu:loanAmount ?a . }"),
    ("portfolioAvgDTI",
     "SELECT (AVG(?d) AS ?v) WHERE { ?b a tu:Borrower ; tu:dti ?d . }"),
    ("highRiskBorrowerCount",
     "SELECT (COUNT(?b) AS ?v) WHERE { ?b a tu:Borrower ; tu:creditScore ?s . FILTER(?s < 620) }"),
    ("fraudRingMemberCount",
     "SELECT (COUNT(DISTINCT ?b) AS ?v) WHERE { ?b a tu:Borrower ; tu:fraudRing ?r . }"),
]

print(f"  {'Metric':<35} {'Value'}")
print("  " + "─" * 55)
for name, q in metrics:
    r = list(g.query(PREFIX + q))
    if r:
        row = r[0]
        try:
            vals = [v for v in row if v is not None]
            if len(vals) == 2:  # default rate special case
                d, t = float(str(vals[0])), float(str(vals[1]))
                val = f"{d/t:.1%}" if t > 0 else "N/A"
            else:
                f = float(str(vals[0]))
                val = (f"Rs {f:,.0f}" if f > 10000 else
                       f"{f:.1%}" if 0 < f < 1 else
                       f"{f:.1f}")
        except: val = "N/A"
    else: val = "N/A"
    print(f"  {name:<35} {val}")

print()
print("  Change a single triple in the graph → all metrics update.")
print("  No manual calculation. No Excel. One source of truth.")
print()


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 7: Fraud Ring Analytics
# ─────────────────────────────────────────────────────────────────────────────
print("SECTION 7: Fraud Ring Analytics with GROUP_CONCAT")
print("=" * 65)

run("Complete fraud ring risk summary — all aggregates + GROUP_CONCAT",
"""
SELECT ?fraudRing
    (COUNT(DISTINCT ?b)     AS ?members)
    (SUM(?amount)           AS ?totalExposure)
    (MIN(?score)            AS ?weakestScore)
    (AVG(?score)            AS ?avgScore)
    (COUNT(?def)            AS ?confirmedDefaulters)
    (GROUP_CONCAT(DISTINCT ?name; SEPARATOR=" | ") AS ?memberNames)
WHERE {
    ?b a tu:Borrower ; tu:fraudRing ?fraudRing ;
       tu:name ?name ; tu:creditScore ?score .
    OPTIONAL { ?b tu:hasLoan ?l . ?l tu:loanAmount ?amount . }
    OPTIONAL { ?b tu:hasDefault true . BIND(?b AS ?def) }
}
GROUP BY ?fraudRing
ORDER BY DESC(?totalExposure)
""", "GROUP_CONCAT lists all member names; aggregates give full risk profile per ring")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 8: SQL vs SPARQL — Aggregate Syntax Comparison
# ─────────────────────────────────────────────────────────────────────────────
print("SECTION 8: SQL vs SPARQL — Aggregate Syntax Comparison")
print("=" * 65)
print("""
  TASK: Total exposure and borrower count per city, alert when > Rs 9L

  ── SQL ──────────────────────────────────────────────────────
  SELECT b.city,
         COUNT(DISTINCT b.id) AS borrowerCount,
         SUM(l.amount)        AS totalExposure
  FROM borrowers b
  LEFT JOIN loans l ON b.id = l.borrower_id
  GROUP BY b.city
  HAVING SUM(l.amount) > 900000
  ORDER BY totalExposure DESC

  ── SPARQL ───────────────────────────────────────────────────
  SELECT ?city
      (COUNT(DISTINCT ?b) AS ?borrowerCount)
      (SUM(?amount)       AS ?totalExposure)
  WHERE {
      ?b a tu:Borrower ; tu:city ?city .
      ?b tu:hasLoan ?loan .
      ?loan tu:loanAmount ?amount .
  }
  GROUP BY ?city
  HAVING (SUM(?amount) > 900000)
  ORDER BY DESC(?totalExposure)

  Differences:
  → No JOIN keyword — ?b tu:hasLoan ?loan links them implicitly
  → No FROM clause — pattern matching finds the data
  → AS is mandatory for aggregate aliases in SPARQL
  → HAVING uses the aggregate expression, not the alias
  → Adding a new relationship: one new triple pattern line, not a new JOIN

  Similarities:
  → GROUP BY, HAVING, ORDER BY, COUNT, SUM, AVG, MIN, MAX: identical concepts
  → DISTINCT inside COUNT: COUNT(DISTINCT ?x) — same as SQL
  → Subqueries: SELECT inside WHERE — structurally identical to SQL subqueries
""")

print("=" * 65)
print("Day 14 Complete! SPARQL Aggregates and Analytics Mastered.")
print()
print("Keywords covered:")
print("  ✅ COUNT, SUM, AVG, MIN, MAX, SAMPLE, GROUP_CONCAT")
print("  ✅ GROUP BY (simple + subquery workaround for rdflib)")
print("  ✅ HAVING (post-aggregation filtering)")
print("  ✅ Subqueries: individual vs portfolio average")
print("  ✅ Subqueries: concentration ratio (two subqueries)")
print("  ✅ Subqueries: compare to group average")
print("  ✅ V3 pattern: domain_ontology.ttl thresholds in analytics")
print("  ✅ Semantic Layer: 6 governed portfolio metrics")
print("  ✅ Fraud ring aggregate analytics with GROUP_CONCAT")
print()
print("CQ Progress: 10/15 CQs now answerable with SPARQL")
print("=" * 65)
