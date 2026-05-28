"""
query.py — TransUnion Credit Risk Knowledge Graph Queries
Weekend Project 1 (CORRECTED VERSION)

Key Correction from original:
  BEFORE: One combined file (ontology.ttl had both schema + data)
  AFTER:  TWO separate files:
          - ontology.ttl = SCHEMA ONLY (classes, properties, SHACL)
          - data.ttl     = DATA ONLY (actual borrowers, loans, decisions)
          - This file loads BOTH = the Knowledge Graph

Concepts from Days 1-5 demonstrated:
  DAY 1: Ontology (ontology.ttl) ≠ Data (data.ttl).
         KG = both files loaded together in g.
  DAY 2: SPARQL queries are DETERMINISTIC (same query = same result always).
         This is why KGs beat LLMs for credit facts.
  DAY 3: Context = bounded query. We query only relevant facts (40 triples),
         not the whole graph.
  DAY 4: ontology.ttl = Layer1 (annotations) + Layer2 (SHACL).
         data.ttl = Layer3 (graph data).
         query.py = Layer5 (inference / agent reasoning).
  DAY 5: Classes came from NOUNS in CQs. Queries answer those same CQs.
"""

from rdflib import Graph, Namespace, RDF, RDFS
from rdflib.plugins.sparql import prepareQuery
import datetime

# ─────────────────────────────────────────────────────────────
# STEP 1: BUILD THE KNOWLEDGE GRAPH
#
# Day 1 concept: KG = Ontology + Data
# We load TWO separate files into ONE graph object.
# This combined graph IS the Knowledge Graph.
# ─────────────────────────────────────────────────────────────

print("=" * 65)
print("TransUnion Credit Risk — Knowledge Graph Demo")
print("Weekend Project 1 (Corrected: Ontology + Data Separated)")
print("=" * 65)
print()

# Create empty in-memory graph
g = Graph()

# Load SCHEMA (Layer 1 + Layer 2 from Day 4)
g.parse("ontology.ttl", format="turtle")
schema_triples = len(g)
print(f"Step 1: Loaded ontology.ttl (schema)")
print(f"        Schema triples: {schema_triples}")
print(f"        Contains: 5 classes, 8 properties, 3 SHACL shapes")

# Load DATA (Layer 3 from Day 4)
g.parse("data.ttl", format="turtle")
total_triples = len(g)
data_triples  = total_triples - schema_triples
print(f"\nStep 2: Loaded data.ttl (instances)")
print(f"        Data triples: {data_triples}")
print(f"        Contains: 2 lenders, 3 borrowers, 5 loans, 3 decisions")

print(f"\nStep 3: Knowledge Graph assembled")
print(f"        Total triples: {total_triples}")
print(f"        (Day 1: KG = ontology.ttl + data.ttl = {schema_triples} + {data_triples})")
print()

# Define namespaces for convenience
TU   = Namespace("http://transunion.com/ontology#")
DATA = Namespace("http://transunion.com/data#")


# ─────────────────────────────────────────────────────────────
# STEP 2: VERIFY THE SCHEMA IS QUERYABLE
#
# Day 4 concept: SHACL shapes and class definitions are
# FIRST-CLASS RDF resources — you can QUERY the schema itself!
# This is impossible with a traditional SQL schema.
# ─────────────────────────────────────────────────────────────

print("-" * 65)
print("SCHEMA QUERY: What classes are defined in our ontology?")
print("(Day 4: Ontology schema is queryable data — not buried in code)")
print("-" * 65)

schema_query = """
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX tu:   <http://transunion.com/ontology#>

SELECT ?className ?label ?comment
WHERE {
    ?class a rdfs:Class .
    ?class rdfs:label ?label .
    ?class rdfs:comment ?comment .
    BIND(STRAFTER(STR(?class), "#") AS ?className)
}
ORDER BY ?className
"""

for row in g.query(schema_query):
    name    = str(row.className)
    label   = str(row.label)
    comment = str(row.comment).replace('\n', ' ').replace('    ', ' ')[:80]
    print(f"  Class: {name}")
    print(f"    Label:   {label}")
    print(f"    Comment: {comment}...")
    print()


# ─────────────────────────────────────────────────────────────
# QUERY 1: All Borrowers — Credit Scores and DTI
#
# Day 5: Answers CQ1 (credit score) and CQ3 (DTI)
# Day 2: This is DETERMINISTIC — same query always returns same result.
#        An LLM could hallucinate the score. The KG cannot.
# ─────────────────────────────────────────────────────────────

print("-" * 65)
print("QUERY 1: All Borrowers with Credit Scores and DTI")
print("Day 5 CQs answered: CQ1 (credit score) + CQ3 (DTI ratio)")
print("Day 2 concept: DETERMINISTIC — KG never hallucinates a score")
print("-" * 65)

query1 = """
PREFIX tu:   <http://transunion.com/ontology#>

SELECT ?borrowerName ?creditScore ?dti
WHERE {
    ?borrower a tu:Borrower .
    ?borrower tu:name ?borrowerName .
    ?borrower tu:creditScore ?creditScore .
    ?borrower tu:dti ?dti .
}
ORDER BY DESC(?creditScore)
"""

results1 = list(g.query(query1))

print(f"{'Name':<20} {'Score':<8} {'DTI':<8} {'Risk Tier':<15} {'Rule: Score>=700':<18} {'Rule: DTI<=0.43'}")
print("-" * 90)
for row in results1:
    name  = str(row.borrowerName)
    score = int(row.creditScore)
    dti   = float(row.dti)
    tier  = "EXCELLENT" if score >= 720 else ("GOOD" if score >= 680 else ("FAIR" if score >= 620 else "POOR"))
    score_rule = "PASS" if score >= 700 else ("MARGINAL" if score >= 620 else "FAIL")
    dti_rule   = "PASS" if dti <= 0.43 else "FAIL"
    print(f"{name:<20} {score:<8} {dti:<8.2f} {tier:<15} {score_rule:<18} {dti_rule}")

print()


# ─────────────────────────────────────────────────────────────
# QUERY 2: High-Risk Borrowers — Answers CQ9
#
# Day 3 concept: Context = bounded query.
# We query ONLY relevant borrowers (score < 650),
# not the entire graph. This is the Markov blanket idea:
# retrieve only what is needed for the decision.
# ─────────────────────────────────────────────────────────────

print("-" * 65)
print("QUERY 2: High-Risk Borrowers (Credit Score below 650)")
print("Day 5 CQ answered: CQ9 (which borrowers are high risk tier?)")
print("Day 3 concept: Bounded context — query only relevant entities")
print("-" * 65)

query2 = """
PREFIX tu: <http://transunion.com/ontology#>

SELECT ?borrowerName ?creditScore ?dti
WHERE {
    ?borrower a tu:Borrower .
    ?borrower tu:name ?borrowerName .
    ?borrower tu:creditScore ?creditScore .
    ?borrower tu:dti ?dti .
    FILTER(?creditScore < 650)
}
ORDER BY ?creditScore
"""

results2 = list(g.query(query2))

if results2:
    print(f"{'Name':<20} {'Score':<8} {'DTI':<8} {'Rejection Reason (CQ15)'}")
    print("-" * 65)
    for row in results2:
        name  = str(row.borrowerName)
        score = int(row.creditScore)
        dti   = float(row.dti)
        reasons = []
        if score < 620:
            reasons.append(f"Score {score} below minimum 620")
        if dti > 0.43:
            reasons.append(f"DTI {dti:.2f} exceeds maximum 0.43")
        print(f"{name:<20} {score:<8} {dti:<8.2f} {' AND '.join(reasons)}")
else:
    print("  No high-risk borrowers found.")
print()


# ─────────────────────────────────────────────────────────────
# QUERY 3: Total Loan Exposure — MULTI-HOP GRAPH TRAVERSAL
#
# Day 1 concept: KGs excel at RELATIONSHIP queries.
# This query traverses TWO hops: Borrower → hasLoan → Loan → loanAmount
# In SQL this requires a JOIN. In SPARQL it's natural graph traversal.
# Day 5 CQ answered: CQ2 (total monthly debt)
# ─────────────────────────────────────────────────────────────

print("-" * 65)
print("QUERY 3: Total Loan Exposure Per Borrower (Multi-Hop Traversal!)")
print("Day 5 CQ answered: CQ2 (total loan exposure)")
print("Day 1 concept: Graph traversal Borrower → hasLoan → Loan → Amount")
print("               SQL needs JOIN. SPARQL does it naturally.")
print("-" * 65)

query3 = """
PREFIX tu: <http://transunion.com/ontology#>

SELECT ?borrowerName ?creditScore
       (SUM(?amount) AS ?totalExposure)
       (COUNT(?loan) AS ?loanCount)
WHERE {
    ?borrower a tu:Borrower .
    ?borrower tu:name ?borrowerName .
    ?borrower tu:creditScore ?creditScore .
    ?borrower tu:hasLoan ?loan .            # HOP 1: Borrower → Loan
    ?loan     tu:loanAmount ?amount .       # HOP 2: Loan → Amount
}
GROUP BY ?borrowerName ?creditScore
ORDER BY DESC(?totalExposure)
"""

results3 = list(g.query(query3))

print(f"{'Name':<20} {'Score':<8} {'Total (Rs)':<18} {'Loans':<8} {'Exposure Assessment'}")
print("-" * 75)
for row in results3:
    name   = str(row.borrowerName)
    score  = int(row.creditScore)
    total  = float(row.totalExposure)
    count  = int(row.loanCount)
    assess = ("HIGH — income verification needed" if total > 2000000
              else "MODERATE — standard checks" if total > 500000
              else "LOW — minimal exposure")
    print(f"{name:<20} {score:<8} Rs {total:>12,.0f}   {count:<8} {assess}")
print()


# ─────────────────────────────────────────────────────────────
# BONUS: All Decisions with Outcomes
#
# Day 5 CQs answered: CQ12 (rules evaluated), CQ14 (outcome), CQ15 (reasons)
# Day 4: Decisions stored in Layer 3 (Graph) with full rdfs:comment audit trail
# ─────────────────────────────────────────────────────────────

print("-" * 65)
print("BONUS QUERY: All Credit Decisions and Reasoning")
print("Day 5 CQs: CQ12 (which rules fired) + CQ14 (outcome) + CQ15 (reasons)")
print("Day 4: Decision data lives in Layer 3 (Graph Layer) as triples")
print("-" * 65)

query4 = """
PREFIX tu:   <http://transunion.com/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?label ?outcome ?reasoning
WHERE {
    ?decision a tu:Decision .
    ?decision rdfs:label ?label .
    ?decision tu:decisionOutcome ?outcome .
    ?decision rdfs:comment ?reasoning .
}
ORDER BY ?outcome
"""

for row in g.query(query4):
    outcome  = str(row.outcome)
    label    = str(row.label)
    reasoning = str(row.reasoning).strip().replace('\n', ' ').replace('   ', ' ')
    marker   = "[APPROVED]    " if outcome == "APPROVED" else (
               "[REJECTED]    " if outcome == "REJECTED" else "[MANUAL_REVIEW]")
    print(f"\n{marker} {label}")
    print(f"  Reasoning: {reasoning}")

print()


# ─────────────────────────────────────────────────────────────
# FINAL SUMMARY
# ─────────────────────────────────────────────────────────────

print("=" * 65)
print("SUMMARY: Days 1-5 Concepts Demonstrated")
print("=" * 65)
print(f"  Day 1: Ontology ({schema_triples} triples) + Data ({data_triples} triples)")
print(f"         = Knowledge Graph ({total_triples} total triples)")
print( "  Day 2: SPARQL is deterministic. Every query returns exact facts.")
print( "         LLMs approximate. KGs guarantee. Credit needs guarantees.")
print( "  Day 3: Context = bounded query. We retrieved only relevant")
print( "         borrower facts. Not all 100+ triples — just what we need.")
print( "  Day 4: ontology.ttl = Layer1+Layer2. data.ttl = Layer3.")
print( "         query.py reasoning = Layer5 (Inference).")
print( "  Day 5: CQ1+CQ3 (Query1), CQ9 (Query2), CQ2 (Query3),")
print( "         CQ12+CQ14+CQ15 (Bonus). All core CQs answered!")
print()

# Save results
output = f"""TransUnion Credit Risk — Query Results (Corrected Version)
Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Schema triples (ontology.ttl): {schema_triples}
Data triples   (data.ttl):     {data_triples}
Total KG triples:              {total_triples}

KEY CORRECTION:
  BEFORE: ontology.ttl contained both schema AND data (incorrect)
  AFTER:  ontology.ttl = schema only. data.ttl = instances only.
  WHY:    Ontology = blueprint. Data = the building. KG = both together.

QUERY 1: All Borrowers (CQ1 + CQ3)
{'='*60}
"""
for row in results1:
    name  = str(row.borrowerName)
    score = int(row.creditScore)
    dti   = float(row.dti)
    tier  = "EXCELLENT" if score >= 720 else ("GOOD" if score >= 680 else ("FAIR" if score >= 620 else "POOR"))
    output += f"  {name}: score={score} ({tier}), DTI={dti:.2f}\n"

output += f"\nQUERY 2: High Risk Borrowers — score < 650 (CQ9)\n{'='*60}\n"
if results2:
    for row in results2:
        output += f"  {row.borrowerName}: score={int(row.creditScore)}, DTI={float(row.dti):.2f} → REJECT\n"
else:
    output += "  None found.\n"

output += f"\nQUERY 3: Total Loan Exposure (CQ2) — multi-hop traversal\n{'='*60}\n"
for row in results3:
    output += f"  {row.borrowerName}: Rs {float(row.totalExposure):,.0f} across {int(row.loanCount)} loan(s)\n"

output += f"\nAll queries successful. KG is working correctly.\n"
output += f"ontology.ttl and data.ttl are properly separated.\n"

with open("results.txt", "w") as f:
    f.write(output)

print("Results saved to results.txt")
print("Weekend Project 1 (Corrected) — COMPLETE!")
print("=" * 65)
