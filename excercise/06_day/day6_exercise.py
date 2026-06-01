"""
day6_exercise.py — RDF Fundamentals: John's Chase Card
Day 6 of the 90-Day Knowledge Graph Mastery Program

This script demonstrates:
1. Loading a Turtle file into rdflib (the Python RDF library)
2. Inspecting triples in different ways
3. Understanding URIs vs database IDs
4. Seeing the GRAPH structure emerge
5. Running basic SPARQL queries
6. Showing why triples beat relational rows

Run: python3 day6_exercise.py
"""

from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS, XSD
from rdflib.namespace import RDFS

print("=" * 65)
print("Day 6: RDF Fundamentals — John's $5,000 Chase Credit Card")
print("Week 2 of 90-Day Knowledge Graph Mastery Program")
print("=" * 65)
print()


# ─────────────────────────────────────────────────────────────
# SECTION 1: Load the Turtle file
# This is the MOST COMMON first step in any KG Python script
# ─────────────────────────────────────────────────────────────

print("STEP 1: Loading Turtle file into rdflib Graph")
print("-" * 65)

g = Graph()
g.parse("john_chase_card.ttl", format="turtle")

print(f"  File loaded successfully!")
print(f"  Total triples in graph: {len(g)}")
print()


# ─────────────────────────────────────────────────────────────
# SECTION 2: Inspect ALL triples — see the raw graph
# Every fact you wrote in the .ttl file is here as a triple
# ─────────────────────────────────────────────────────────────

print("STEP 2: All triples (Subject → Predicate → Object)")
print("(This is what the computer actually stores — pure triples)")
print("-" * 65)

# Define namespaces for readable output
TU   = Namespace("http://transunion.com/ontology#")
DATA = Namespace("http://transunion.com/data#")

def shorten(uri):
    """Convert long URI to readable short form for display."""
    uri_str = str(uri)
    replacements = {
        "http://transunion.com/ontology#":              "tu:",
        "http://transunion.com/data#":                  "data:",
        "http://www.w3.org/1999/02/22-rdf-syntax-ns#": "rdf:",
        "http://www.w3.org/2000/01/rdf-schema#":       "rdfs:",
        "http://www.w3.org/2001/XMLSchema#":            "xsd:",
    }
    for full, short in replacements.items():
        uri_str = uri_str.replace(full, short)
    return uri_str

# Print all triples sorted by subject for readability
current_subject = None
for s, p, o in sorted(g, key=lambda x: str(x[0])):
    s_short = shorten(s)
    p_short = shorten(p)
    o_short = shorten(o)
    if s_short != current_subject:
        print(f"\n  Subject: {s_short}")
        current_subject = s_short
    print(f"    → {p_short}: {o_short}")

print()


# ─────────────────────────────────────────────────────────────
# SECTION 3: URI vs Database ID demonstration
# This is the KEY concept from Day 6
# ─────────────────────────────────────────────────────────────

print("STEP 3: URI vs Database ID — Why URIs Are Better")
print("-" * 65)

print("""
  PROBLEM WITH DATABASE IDs:
  ─────────────────────────
  Equifax database: customer_id = 12345  ← means something to Equifax only
  Experian database: subject_id = 12345  ← same number, different person?
  Internal CRM: account_id = 12345       ← who knows if same person?

  To merge these you need MATCHING LOGIC:
  "Find records where name matches AND date_of_birth matches AND..."
  → Error-prone, expensive, requires application code.

  SOLUTION WITH URIs:
  ──────────────────
  All systems use: <http://transunion.com/borrower/PAN_ABCDE1234F>
  → Same URI = same person. GUARANTEED. No matching logic needed.
  → Any system that sees this URI knows exactly who it refers to.
  → You can load data from 10 systems and it all merges automatically.
""")

# Show the actual URI in our graph
john_uri = URIRef("http://transunion.com/data#borrower_PAN_ABCDE1234F")
print("  John Doe's URI in our graph:")
print(f"  {john_uri}")
print()

# Show all facts about John by querying on his URI
print("  All facts about John (queried by URI):")
for p, o in sorted(g.predicate_objects(john_uri)):
    print(f"    {shorten(p)}: {shorten(o)}")
print()


# ─────────────────────────────────────────────────────────────
# SECTION 4: Why Triples Beat Rows — The Graph Traversal Demo
# ─────────────────────────────────────────────────────────────

print("STEP 4: Why Triples Beat Rows — Graph Traversal")
print("-" * 65)

print("""
  SQL approach for "What bank issued John's credit card?":
  ────────────────────────────────────────────────────────
  SELECT b.name
  FROM borrowers bor
  JOIN accounts acc ON bor.id = acc.borrower_id
  JOIN banks b ON acc.bank_id = b.id
  WHERE bor.pan = 'ABCDE1234F'

  SPARQL approach (RDF graph traversal):
  ──────────────────────────────────────
""")

sparql_traverse = """
PREFIX tu: <http://transunion.com/ontology#>

SELECT ?bankName WHERE {
    ?borrower tu:panNumber "ABCDE1234F" .      # Find John by PAN
    ?borrower tu:hasAccount ?account .          # HOP 1: John → Account
    ?account tu:issuedBy ?bank .               # HOP 2: Account → Bank
    ?bank tu:name ?bankName .                  # HOP 3: Bank → Name
}
"""

results = list(g.query(sparql_traverse))
print("  Query: 'Which bank issued John's credit card?'")
print(f"  Answer: {[str(r.bankName) for r in results]}")
print()
print("""  The graph traversal is IDENTICAL for 2 hops or 10 hops.
  SQL requires one new JOIN per hop.
  SPARQL just extends the chain: ?a → ?b → ?c → ?d → ?e
""")


# ─────────────────────────────────────────────────────────────
# SECTION 5: Three SPARQL Queries answering real questions
# ─────────────────────────────────────────────────────────────

print("STEP 5: Three SPARQL Queries on John's Credit Card Data")
print("-" * 65)

# Query 1: Basic credit profile
q1 = """
PREFIX tu: <http://transunion.com/ontology#>
SELECT ?name ?creditScore ?dti ?employedAt WHERE {
    ?borrower a tu:Borrower .
    ?borrower tu:name ?name .
    ?borrower tu:hasReport ?report .
    ?report tu:creditScore ?creditScore .
    ?borrower tu:dti ?dti .
    ?borrower tu:employedAt ?employedAt .
}
"""
print("  Query 1: John's credit profile")
for row in g.query(q1):
    print(f"    Name: {row.name}")
    print(f"    Credit Score: {row.creditScore}")
    print(f"    DTI: {row.dti}")
    print(f"    Employed at: {row.employedAt}")
print()

# Query 2: Account utilization
q2 = """
PREFIX tu: <http://transunion.com/ontology#>
SELECT ?accountType ?limit ?balance ?utilization ?bank WHERE {
    ?borrower a tu:Borrower .
    ?borrower tu:hasAccount ?account .
    ?account a ?accountType .
    ?account tu:creditLimit ?limit .
    ?account tu:currentBalance ?balance .
    ?account tu:utilizationRate ?utilization .
    ?account tu:issuedBy ?bankNode .
    ?bankNode tu:name ?bank .
}
"""
print("  Query 2: Credit card utilization analysis")
for row in g.query(q2):
    acct_type = shorten(str(row.accountType))
    print(f"    Account type: {acct_type}")
    print(f"    Credit limit: Rs {row.limit}")
    print(f"    Current balance: Rs {row.balance}")
    print(f"    Utilization: {float(row.utilization)*100:.0f}%")
    print(f"    Bank: {row.bank}")
print()

# Query 3: Full risk profile
q3 = """
PREFIX tu: <http://transunion.com/ontology#>
SELECT ?name ?creditScore ?dti ?income ?delinquencies WHERE {
    ?borrower a tu:Borrower .
    ?borrower tu:name ?name .
    ?borrower tu:monthlyIncome ?income .
    ?borrower tu:dti ?dti .
    ?borrower tu:hasReport ?report .
    ?report tu:creditScore ?creditScore .
    ?report tu:delinquencies ?delinquencies .
}
"""
print("  Query 3: Full risk assessment profile")
for row in g.query(q3):
    score = int(row.creditScore)
    dti   = float(row.dti)
    risk  = "LOW RISK" if score >= 720 and dti <= 0.43 else "MEDIUM RISK"
    print(f"    Borrower: {row.name}")
    print(f"    Credit Score: {score} → {'PASS (>=700)' if score >= 700 else 'FAIL (<700)'}")
    print(f"    DTI: {dti:.3f} → {'PASS (<=0.43)' if dti <= 0.43 else 'FAIL (>0.43)'}")
    print(f"    Monthly Income: Rs {row.income}")
    print(f"    Delinquencies: {row.delinquencies}")
    print(f"    OVERALL RISK: {risk}")
print()


# ─────────────────────────────────────────────────────────────
# SECTION 6: Creating triples in Python (not just from file)
# ─────────────────────────────────────────────────────────────

print("STEP 6: Adding New Triples in Python (no .ttl file needed)")
print("-" * 65)

# You can also create triples directly in Python!
# This is how agents write their outputs back to the graph

g2 = Graph()
TU_NS   = Namespace("http://transunion.com/ontology#")
DATA_NS = Namespace("http://transunion.com/data#")

john = DATA_NS.borrower_PAN_ABCDE1234F

# Add triples one by one using rdflib
g2.add((john, RDF.type,         TU_NS.Borrower))
g2.add((john, TU_NS.name,       Literal("John Doe")))
g2.add((john, TU_NS.creditScore,Literal(720, datatype=XSD.integer)))
g2.add((john, TU_NS.dti,        Literal("0.017", datatype=XSD.decimal)))

print(f"  Created graph with {len(g2)} triples using Python rdflib API")
print(f"  (Same result as parsing a .ttl file)")
print()

# Export back to Turtle format
turtle_output = g2.serialize(format="turtle")
print("  Exported to Turtle format:")
print("  " + "\n  ".join(turtle_output.split("\n")[:12]))
print()


# ─────────────────────────────────────────────────────────────
# SECTION 7: TransUnion Connection — Fraud Detection Preview
# ─────────────────────────────────────────────────────────────

print("STEP 7: TransUnion Connection — How Triples Enable Fraud Detection")
print("-" * 65)

print("""
  In this exercise, John has ONE credit card with ONE bank.
  In production, TransUnion's graph might show:

  John_Doe ──[hasAccount]──▶ Chase_Card_CC001 ──[issuedBy]──▶ Chase_Bank
  John_Doe ──[hasAccount]──▶ HDFC_Card_CC002
  John_Doe ──[cosignedFor]──▶ Mary_Smith
  Mary_Smith ──[hasDefault]──▶ Default_2025_Dec
  John_Doe ──[samePhone]──▶ Bob_Jones
  Bob_Jones ──[hasDefault]──▶ Default_2026_Jan

  SPARQL fraud query:
  ───────────────────
  SELECT ?connected ?relationship WHERE {
      data:borrower_PAN_ABCDE1234F
          (:samePhone|:cosignedFor|:sameAddress){1,3} ?connected .
      ?connected tu:hasDefault ?default .
  }

  Result: John is 1 hop from Mary (via cosignedFor) who defaulted.
          John is 1 hop from Bob (via samePhone) who defaulted.
  → FLAG as SUSPICIOUS NETWORK!

  This multi-hop traversal is impossible to express simply in SQL.
  In SPARQL: one query, any depth, any relationship type.
  This is why TransUnion needs knowledge graphs.
""")

print("=" * 65)
print("Day 6 Exercise Complete!")
print(f"Triples loaded from file: {len(g)}")
print("Concepts demonstrated:")
print("  ✅ Turtle file loading with rdflib")
print("  ✅ All triples inspection")
print("  ✅ URI vs database ID difference")
print("  ✅ Graph traversal (3 hops in one SPARQL query)")
print("  ✅ 3 SPARQL queries answering real credit questions")
print("  ✅ Adding triples programmatically in Python")
print("  ✅ Fraud detection preview")
print("=" * 65)
