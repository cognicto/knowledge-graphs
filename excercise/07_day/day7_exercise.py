"""
day7_exercise.py — Why Graphs Beat Tables: Fraud Ring Detection
Day 7 of the 90-Day Knowledge Graph Mastery Program

This script demonstrates:
1. What SQL CAN detect (direct blacklist hits)
2. What SQL CANNOT detect (connected fraud rings)
3. How graph traversal finds the full fraud ring
4. The PayPal pattern applied to TransUnion credit risk
5. Property Graph (Cypher) vs RDF Graph (SPARQL) comparison

Key learning: SQL thinks in rows. Graphs think in connections.
"""

from rdflib import Graph, Namespace, RDF, Literal
from rdflib.namespace import RDFS

print("=" * 65)
print("Day 7: Why Graphs Beat Tables — Fraud Ring Detection")
print("PayPal Pattern Applied to TransUnion Credit Risk")
print("=" * 65)
print()

# Load the fraud ring data
g = Graph()
g.parse("fraud_ring_data.ttl", format="turtle")
print(f"Graph loaded: {len(g)} triples")
print()

TU   = Namespace("http://transunion.com/ontology#")
DATA = Namespace("http://transunion.com/data#")


# ─────────────────────────────────────────────────────────────
# SECTION 1: What SQL CAN Do — Direct Blacklist Check
# ─────────────────────────────────────────────────────────────

print("SECTION 1: SQL Approach — Direct Blacklist Check")
print("-" * 65)
print("""
  SQL Query (simulated):
  ─────────────────────
  SELECT name, credit_score, dti
  FROM borrowers
  WHERE has_default = TRUE
  ORDER BY credit_score ASC

  This checks: Is THIS applicant a defaulter?
  It CANNOT check: Are they CONNECTED to defaulters?
""")

# Simulate what SQL would find
sql_blacklist_query = """
PREFIX tu: <http://transunion.com/ontology#>
SELECT ?name ?score ?dti WHERE {
    ?borrower a tu:Borrower .
    ?borrower tu:name ?name .
    ?borrower tu:creditScore ?score .
    ?borrower tu:dti ?dti .
    ?borrower tu:hasDefault true .
}
ORDER BY ?score
"""
print("  SQL result — known defaulters (direct hit only):")
results = list(g.query(sql_blacklist_query))
if results:
    for row in results:
        print(f"    ❌ {row.name}: score={row.score}, dti={float(row.dti):.2f} → REJECT")
else:
    print("    (none found)")

print()
print("  SQL approach on NEW applicants (Meera and Suresh):")

sql_clean_query = """
PREFIX tu: <http://transunion.com/ontology#>
SELECT ?name ?score ?dti WHERE {
    ?borrower a tu:Borrower .
    ?borrower tu:name ?name .
    ?borrower tu:creditScore ?score .
    ?borrower tu:dti ?dti .
    ?borrower tu:hasDefault false .
    FILTER(?score >= 650)
}
ORDER BY DESC(?score)
"""
for row in g.query(sql_clean_query):
    name  = str(row.name)
    score = int(row.score)
    dti   = float(row.dti)
    print(f"    ✅ {name}: score={score}, dti={dti:.2f} → SQL says APPROVE")

print()
print("  SQL PROBLEM: Meera and Suresh both look clean!")
print("  SQL missed that they are connected to Vijay (known defaulter).")
print()


# ─────────────────────────────────────────────────────────────
# SECTION 2: What Graph CAN Do — Connection Detection
# ─────────────────────────────────────────────────────────────

print("SECTION 2: Graph Approach — Fraud Ring Detection")
print("-" * 65)
print("""
  The graph query checks:
  "Is this applicant connected (within 3 hops) to any known defaulter
   through shared phone, address, device, or employer?"

  This is the CORE of fraud ring detection.
  SQL cannot do this without recursive CTEs and multiple self-joins.
  SPARQL does it in 4 lines with property paths.
""")

# Graph fraud ring detection query
# Note: rdflib has limited property path support
# We break it into explicit hop queries for demonstration

print("  Graph Query — 1-hop connections to defaulters:")
print("  (Direct connections: same phone, same address, same device)")
print()

hop1_query = """
PREFIX tu: <http://transunion.com/ontology#>

SELECT DISTINCT ?applicantName ?defaulterName ?connectionType WHERE {
    # Find known defaulters
    ?defaulter tu:hasDefault true .
    ?defaulter tu:name ?defaulterName .

    # Find applicants (not themselves defaulters) connected via shared entity
    ?applicant tu:hasDefault false .
    ?applicant tu:name ?applicantName .

    {
        # Connection via shared phone
        ?applicant tu:sharesPhone ?phone .
        ?defaulter tu:sharesPhone ?phone .
        BIND("SHARED PHONE" AS ?connectionType)
    } UNION {
        # Connection via shared address
        ?applicant tu:livesAt ?address .
        ?defaulter tu:livesAt ?address .
        BIND("SHARED ADDRESS" AS ?connectionType)
    } UNION {
        # Connection via shared device
        ?applicant tu:usesDevice ?device .
        ?defaulter tu:usesDevice ?device .
        BIND("SHARED DEVICE" AS ?connectionType)
    } UNION {
        # Connection via shared employer
        ?applicant tu:claimsEmployer ?employer .
        ?defaulter tu:claimsEmployer ?employer .
        BIND("SHARED EMPLOYER" AS ?connectionType)
    }
}
ORDER BY ?applicantName
"""

hop1_results = list(g.query(hop1_query))
if hop1_results:
    for row in hop1_results:
        print(f"    🚨 {row.applicantName} connected to {row.defaulterName} via {row.connectionType}")
else:
    print("    (No 1-hop connections found)")

print()


# 2-hop detection — find connections through an intermediate node
print("  Graph Query — 2-hop connections (friend of a fraudster):")
print()

hop2_query = """
PREFIX tu: <http://transunion.com/ontology#>

SELECT DISTINCT ?applicantName ?intermediaryName ?defaulterName WHERE {
    # Known defaulter
    ?defaulter tu:hasDefault true .
    ?defaulter tu:name ?defaulterName .

    # Intermediary connected to defaulter (1 hop)
    ?intermediary tu:hasDefault false .
    ?intermediary tu:name ?intermediaryName .
    {
        ?intermediary tu:sharesPhone ?p1 .
        ?defaulter tu:sharesPhone ?p1 .
    } UNION {
        ?intermediary tu:livesAt ?a1 .
        ?defaulter tu:livesAt ?a1 .
    }

    # Applicant connected to intermediary (2 hops)
    ?applicant tu:hasDefault false .
    ?applicant tu:name ?applicantName .
    FILTER(?applicant != ?intermediary)
    {
        ?applicant tu:usesDevice ?d1 .
        ?intermediary tu:usesDevice ?d1 .
    } UNION {
        ?applicant tu:claimsEmployer ?e1 .
        ?defaulter tu:claimsEmployer ?e1 .
    }

    FILTER(?applicantName != ?intermediaryName)
    FILTER(?applicantName != ?defaulterName)
}
"""

hop2_results = list(g.query(hop2_query))
if hop2_results:
    for row in hop2_results:
        print(f"    🚨 {row.applicantName} is 2 hops from {row.defaulterName} via {row.intermediaryName}")
else:
    print("    (No 2-hop connections found)")

print()


# ─────────────────────────────────────────────────────────────
# SECTION 3: The Combined Fraud Ring Report
# ─────────────────────────────────────────────────────────────

print("SECTION 3: Complete Fraud Ring Analysis Report")
print("-" * 65)

# Get all borrowers with their risk assessment
all_borrowers_query = """
PREFIX tu: <http://transunion.com/ontology#>
SELECT ?name ?score ?dti ?isDefault WHERE {
    ?borrower a tu:Borrower .
    ?borrower tu:name ?name .
    ?borrower tu:creditScore ?score .
    ?borrower tu:dti ?dti .
    ?borrower tu:hasDefault ?isDefault .
}
ORDER BY DESC(?score)
"""

# Collect fraud ring members (from hop1 detection)
fraud_ring = {str(r.applicantName) for r in hop1_results}
fraud_ring.update({str(r.applicantName) for r in hop2_results})
known_defaulters = set()
for row in g.query(sql_blacklist_query):
    known_defaulters.add(str(row.name))

print()
print(f"  {'Name':<20} {'Score':<8} {'DTI':<8} {'Default':<10} {'SQL':<20} {'GRAPH'}")
print("  " + "-" * 80)

for row in g.query(all_borrowers_query):
    name   = str(row.name)
    score  = int(row.score)
    dti    = float(row.dti)
    is_def = str(row.isDefault) == "true"

    if is_def:
        sql_result   = "REJECT (blacklist)"
        graph_result = "REJECT (blacklist)"
    elif name in fraud_ring:
        sql_result   = "APPROVE ← WRONG!"
        graph_result = "REJECT (fraud ring)"
    else:
        sql_result   = "APPROVE"
        graph_result = "APPROVE"

    flag = "🚨" if (name in fraud_ring or is_def) else "✅"
    print(f"  {flag} {name:<18} {score:<8} {dti:<8.2f} {'YES' if is_def else 'NO':<10} {sql_result:<20} {graph_result}")

print()


# ─────────────────────────────────────────────────────────────
# SECTION 4: SQL vs SPARQL Comparison for Fraud Detection
# ─────────────────────────────────────────────────────────────

print("SECTION 4: SQL vs SPARQL — The Code Comparison")
print("-" * 65)

print("""
  TASK: Find all borrowers within 3 hops of a known defaulter

  SQL APPROACH (3 hops requires 3 self-joins + recursive CTE):
  ─────────────────────────────────────────────────────────────
  WITH RECURSIVE fraud_network AS (
    -- Base: direct defaulters
    SELECT borrower_id, 0 as hops FROM borrowers WHERE has_default = TRUE

    UNION ALL

    -- Hop 1: share phone
    SELECT b2.borrower_id, fn.hops + 1
    FROM fraud_network fn
    JOIN phone_mappings pm1 ON fn.borrower_id = pm1.borrower_id
    JOIN phone_mappings pm2 ON pm1.phone = pm2.phone
    JOIN borrowers b2 ON pm2.borrower_id = b2.borrower_id
    WHERE fn.hops < 3

    UNION ALL

    -- Hop 2: share address (need another CTE block)
    ...

    UNION ALL

    -- Hop 3: share device (another CTE block)
    ...
  )
  SELECT DISTINCT b.name, b.credit_score
  FROM fraud_network fn
  JOIN borrowers b ON fn.borrower_id = b.borrower_id
  WHERE fn.hops > 0;

  Problems:
  → 50+ lines of SQL just for 3 hop types
  → Adding new relationship type = rewrite entire query
  → Variable depth (1-3 hops) requires RECURSIVE which is slow
  → Performance degrades exponentially with graph size


  SPARQL APPROACH (all in ~8 lines with property paths):
  ──────────────────────────────────────────────────────
  SELECT ?suspicious ?name WHERE {
      ?defaulter tu:hasDefault true .

      ?defaulter (tu:sharesPhone|tu:livesAt|
                  tu:usesDevice|tu:claimsEmployer){1,3} ?suspicious .

      ?suspicious tu:name ?name .
      ?suspicious tu:hasDefault false .
  }

  Advantages:
  → 8 lines total (vs 50+ SQL lines)
  → Add new relationship: just add to | list
  → Change depth: just change {1,3} to {1,5}
  → Same performance regardless of depth
  → Reads like English: follow any of these relationships 1-3 hops
""")


# ─────────────────────────────────────────────────────────────
# SECTION 5: Property Graph vs RDF Graph Comparison
# ─────────────────────────────────────────────────────────────

print("SECTION 5: Property Graph (Neo4j/Cypher) vs RDF (SPARQL)")
print("-" * 65)

print("""
  THE SAME FRAUD QUERY IN BOTH LANGUAGES:

  ── Neo4j Cypher (Property Graph) ──────────────────────────
  MATCH (defaulter:Borrower {hasDefault: true})
  MATCH (defaulter)-[:SHARES_PHONE|LIVES_AT|
                      USES_DEVICE|CLAIMS_EMPLOYER*1..3]-(suspicious)
  WHERE suspicious.hasDefault = false
  RETURN suspicious.name, suspicious.creditScore

  ── SPARQL (RDF Graph) ──────────────────────────────────────
  SELECT ?name ?score WHERE {
      ?defaulter tu:hasDefault true .
      ?defaulter (tu:sharesPhone|tu:livesAt|
                  tu:usesDevice|tu:claimsEmployer){1,3} ?suspicious .
      ?suspicious tu:hasDefault false .
      ?suspicious tu:name ?name .
      ?suspicious tu:creditScore ?score .
  }

  BOTH return the same result!
  Cypher is slightly more readable for SQL developers.
  SPARQL is the W3C standard and works across any SPARQL database.

  KEY DIFFERENCE — Edge Properties:
  Cypher:  (borrower)-[:APPLIED_FOR {date: '2026-05-28', amount: 50000}]->(loan)
           The EDGE itself can have properties!

  SPARQL:  data:borrower_001 tu:hasAppliedFor data:application_001 .
           data:application_001 tu:applicationDate '2026-05-28' .
           data:application_001 tu:requestedAmount 50000 .
           Need an INTERMEDIATE NODE for edge properties.

  FOR TRANSUNION: Use RDF + SPARQL because:
  1. SHACL validation requires RDF (Days 4-5)
  2. OWL reasoning requires RDF (Week 7-9)
  3. W3C standard = vendor independence
  4. Regulatory compliance prefers standards
""")


# ─────────────────────────────────────────────────────────────
# SECTION 6: PayPal Lessons for TransUnion
# ─────────────────────────────────────────────────────────────

print("SECTION 6: PayPal Lessons Applied to TransUnion")
print("-" * 65)
print("""
  PayPal's Key Insights → TransUnion Implementation:

  1. THREE-TIER ARCHITECTURE:
     PayPal: Real-time + Interactive + Analytics graph layers
     TransUnion:
       Layer 1 (real-time):  Fraud check + risk score in < 2 seconds
       Layer 2 (interactive): Underwriter explores suspicious networks
       Layer 3 (analytics):  Nightly ML model retraining on graph features

  2. EVENT-DRIVEN UPDATES:
     PayPal: Every login, transaction, device change updates graph
     TransUnion: Every bureau pull, employment change, address update
                 triggers graph edge addition in near real-time

  3. REPEAT FRAUDSTER PATTERN:
     PayPal: New account + old device = same fraudster detected
     TransUnion: New PAN + old phone/address = fraud ring member detected

  4. GRAPH ALGORITHMS:
     PayPal: PageRank for influential nodes, Community detection for rings
     TransUnion: Connected components for family clusters,
                 Betweenness centrality for money mules,
                 Anomaly detection on temporal transaction patterns

  5. BUILD VS BUY:
     PayPal: Built custom graph DB (needed million QPS)
     TransUnion: Use Stardog/GraphDB/Amazon Neptune (thousands of QPS)
                 Off-the-shelf is sufficient. No need to build custom.
""")

print("=" * 65)
print("Day 7 Exercise Complete!")
print()
print("Key Results:")
print(f"  SQL missed fraud ring members: {len(fraud_ring)} borrowers")
print(f"  Graph detected all: {len(fraud_ring) + len(known_defaulters)} suspicious borrowers")
print()
print("Concepts demonstrated:")
print("  ✅ SQL blacklist check (what SQL can do)")
print("  ✅ 1-hop fraud ring detection (what SQL misses)")
print("  ✅ 2-hop fraud ring detection (PayPal pattern)")
print("  ✅ SQL vs SPARQL comparison for fraud queries")
print("  ✅ Property graph (Cypher) vs RDF (SPARQL) difference")
print("  ✅ PayPal three-tier architecture applied to TransUnion")
print("=" * 65)
