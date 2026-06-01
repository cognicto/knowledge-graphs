"""
day9_exercise.py — URI and Namespace Design for TransUnion
Day 9 of the 90-Day Knowledge Graph Mastery Program

Plan:
  - Design URI scheme for TransUnion (6 namespace categories)
  - Generate 5 example URIs showing opaque vs meaningful tradeoff
  - Demonstrate hash-based privacy-safe borrower URIs
  - Show why version should NOT go in URIs
  - Reflection: Should SSN be in URI? How to handle URI changes?
"""

import hashlib
from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS, OWL
from rdflib.namespace import XSD

print("=" * 65)
print("Day 9: URIs and Namespaces — TransUnion Design")
print("Cagle + W3C Cool URIs Applied to Credit Risk Domain")
print("=" * 65)
print()


# ─────────────────────────────────────────────────────────────
# SECTION 1: The URI Template
# ─────────────────────────────────────────────────────────────

print("SECTION 1: The URI Template")
print("-" * 65)
print("""
  Standard URI structure (Cagle):
  http://{authority}/{path/to/term}[# or /]{localName}

  Breaking it down for TransUnion:
  ┌──────────┬──────────────────┬────────────┬───┬────────────┐
  │ Protocol │   Authority       │    Path    │sep│ LocalName  │
  ├──────────┼──────────────────┼────────────┼───┼────────────┤
  │ https:// │ transunion.com   │ /ontology  │ # │ Borrower   │
  │ https:// │ transunion.com   │ /data/     │ / │ borrower/  │
  │ https:// │ transunion.com   │ /graphs    │ / │ equifax/   │
  └──────────┴──────────────────┴────────────┴───┴────────────┘

  CURIE (Condensed URI) = prefix alias + localName
  @prefix tu: <http://transunion.com/ontology#>
  tu:Borrower  ←  CURIE that expands to full URI
""")


# ─────────────────────────────────────────────────────────────
# SECTION 2: The Complete TransUnion Namespace Scheme
# ─────────────────────────────────────────────────────────────

print("SECTION 2: TransUnion Namespace Scheme")
print("-" * 65)

namespaces = {
    "tu:":      ("http://transunion.com/ontology#",        "# uri", "Classes, Properties, SHACL Shapes"),
    "tu-sh:":   ("http://transunion.com/shapes#",          "# uri", "SHACL NodeShapes, PropertyShapes"),
    "tu-bwr:":  ("http://transunion.com/data/borrower/",   "/ uri", "Borrower instances (hashed IDs)"),
    "tu-loan:": ("http://transunion.com/data/loan/",       "/ uri", "Loan instances"),
    "tu-dec:":  ("http://transunion.com/data/decision/",   "/ uri", "Decision instances + audit trail"),
    "tu-rpt:":  ("http://transunion.com/data/report/",     "/ uri", "Credit report instances"),
    "tu-lndr:": ("http://transunion.com/data/lender/",     "/ uri", "Lender/bank instances"),
    "tu-g:":    ("http://transunion.com/graphs/",          "/ uri", "Named graphs (data containers)"),
    "tu-x:":    ("http://transunion.com/interchange#",     "# uri", "Interchange/partner ontology"),
}

print(f"  {'Prefix':<12} {'Namespace URI':<45} {'Type':<8} {'Purpose'}")
print("  " + "-" * 100)
for prefix, (uri, uri_type, purpose) in namespaces.items():
    print(f"  {prefix:<12} {uri:<45} {uri_type:<8} {purpose}")
print()


# ─────────────────────────────────────────────────────────────
# SECTION 3: Five Example URIs — Opaque vs Meaningful
# ─────────────────────────────────────────────────────────────

print("SECTION 3: Five Example URIs — Opaque vs Meaningful")
print("-" * 65)

# URI 1: Borrower — OPAQUE (privacy required)
pan = "ABCDE1234F"
salt = "tu_secret_salt_2026"
pan_hash = hashlib.sha256(f"{salt}{pan}".encode()).hexdigest()[:16]
borrower_uri = f"http://transunion.com/data/borrower/{pan_hash}"

print("  URI 1: Borrower (OPAQUE — privacy required)")
print(f"    PAN:              {pan}")
print(f"    Hash of PAN:      {pan_hash}")
print(f"    Borrower URI:     {borrower_uri}")
print(f"    Why opaque:       PAN in URI → exposed in logs, browser history, error msgs")
print(f"    Why hash:         Same PAN always → same hash (stable). Cannot reverse.")
print()

# URI 2: Loan — MEANINGFUL local part (loan ID already opaque in most systems)
loan_id = "HDFC_LOAN_20260527_00123456"
loan_uri = f"http://transunion.com/data/loan/{loan_id}"

print("  URI 2: Loan (MEANINGFUL — loan ID is already system-generated opaque)")
print(f"    Loan system ID:   {loan_id}")
print(f"    Loan URI:         {loan_uri}")
print(f"    Why readable:     Loan IDs are already system-generated codes, not PII")
print(f"    Debugging:        'HDFC_LOAN_...' tells you instantly: HDFC bank, loan type")
print()

# URI 3: Decision — MEANINGFUL timestamp + app ID
app_id = "APP_20260527_001234"
decision_uri = f"http://transunion.com/data/decision/{app_id}"

print("  URI 3: Decision (MEANINGFUL — application ID + date)")
print(f"    Application ID:   {app_id}")
print(f"    Decision URI:     {decision_uri}")
print(f"    Why readable:     Decisions must be auditable. 'APP_20260527' tells date at a glance.")
print(f"    Regulatory:       Compliance teams can filter by date range in the URI itself.")
print()

# URI 4: Ontology class — MEANINGFUL (it's a schema term, not PII)
class_uri = "http://transunion.com/ontology#CreditReport"

print("  URI 4: Ontology Class (MEANINGFUL — schema terms should be readable)")
print(f"    Class URI:        {class_uri}")
print(f"    Why readable:     Schema terms are used in code, queries, documentation.")
print(f"    Cagle rule:       Predicates and classes have greater need to be human readable.")
print(f"    Stability:        This URI should NEVER change (partners depend on it).")
print()

# URI 5: Named Graph — MEANINGFUL with structure
graph_uri = "http://transunion.com/graphs/equifax/2026-05-20"

print("  URI 5: Named Graph (MEANINGFUL — type + date structure)")
print(f"    Named Graph URI:  {graph_uri}")
print(f"    Why readable:     Source (equifax) + date (2026-05-20) visible at a glance.")
print(f"    Query benefit:    SPARQL: GRAPH <.../equifax/2026-05-20> ← instantly understandable")
print(f"    Provenance:       URI itself tells you: Equifax data loaded on May 20.")
print()


# ─────────────────────────────────────────────────────────────
# SECTION 4: Hash URI Generation for All Entity Types
# ─────────────────────────────────────────────────────────────

print("SECTION 4: Privacy-Safe URI Generation for All Entity Types")
print("-" * 65)

def make_borrower_uri(pan: str, salt: str = "tu_2026") -> str:
    """Generate stable opaque borrower URI from PAN."""
    h = hashlib.sha256(f"{salt}{pan}".encode()).hexdigest()[:16]
    return f"http://transunion.com/data/borrower/{h}"

def make_report_uri(bureau: str, report_ref: str) -> str:
    """Generate report URI from bureau + reference number."""
    bureau_code = bureau.lower()[:3]
    return f"http://transunion.com/data/report/{bureau_code}_{report_ref}"

def make_decision_uri(app_id: str) -> str:
    """Generate decision URI from application ID."""
    return f"http://transunion.com/data/decision/{app_id}"

def make_loan_uri(bank_code: str, loan_ref: str) -> str:
    """Generate loan URI from bank + reference."""
    return f"http://transunion.com/data/loan/{bank_code}_{loan_ref}"

def make_context_graph_uri(app_id: str) -> str:
    """Generate named graph URI for a decision context."""
    return f"http://transunion.com/graphs/context/{app_id}"

# Generate sample URIs
test_cases = [
    ("Rahul (PAN: ABCDE1234F)",    make_borrower_uri("ABCDE1234F")),
    ("Priya (PAN: BCEDF5678G)",    make_borrower_uri("BCEDF5678G")),
    ("Rahul again (same PAN)",      make_borrower_uri("ABCDE1234F")),  # must be same!
    ("Equifax report #REF789",      make_report_uri("Equifax", "REF789012")),
    ("Decision for APP_001234",     make_decision_uri("APP_20260527_001234")),
    ("HDFC loan #LON456",           make_loan_uri("HDFC", "LON456789")),
    ("Context graph APP_001234",    make_context_graph_uri("APP_20260527_001234")),
]

for label, uri in test_cases:
    print(f"  {label}")
    print(f"    → {uri}")
print()

# Prove stability
print("  Key property: SAME PAN → SAME URI always (stability)")
print(f"    Rahul (first call):  {make_borrower_uri('ABCDE1234F')}")
print(f"    Rahul (second call): {make_borrower_uri('ABCDE1234F')}")
print(f"    Match: {make_borrower_uri('ABCDE1234F') == make_borrower_uri('ABCDE1234F')}")
print()


# ─────────────────────────────────────────────────────────────
# SECTION 5: Build a small KG using the full URI scheme
# ─────────────────────────────────────────────────────────────

print("SECTION 5: Building KG with Correct URI Scheme")
print("-" * 65)

g = Graph()

# Bind all TransUnion namespaces
TU      = Namespace("http://transunion.com/ontology#")
TU_BWR  = Namespace("http://transunion.com/data/borrower/")
TU_LOAN = Namespace("http://transunion.com/data/loan/")
TU_DEC  = Namespace("http://transunion.com/data/decision/")
TU_RPT  = Namespace("http://transunion.com/data/report/")
TU_G    = Namespace("http://transunion.com/graphs/")

g.bind("tu",      TU)
g.bind("tu-bwr",  TU_BWR)
g.bind("tu-loan", TU_LOAN)
g.bind("tu-dec",  TU_DEC)
g.bind("tu-rpt",  TU_RPT)
g.bind("tu-g",    TU_G)

# Create entities using the designed URI scheme
rahul_uri    = URIRef(make_borrower_uri("ABCDE1234F"))
report_uri   = URIRef(make_report_uri("Equifax", "REF789012"))
loan_uri     = URIRef(make_loan_uri("HDFC", "LON456789"))
decision_uri = URIRef(make_decision_uri("APP_20260527_001234"))

# Add triples
g.add((rahul_uri,    RDF.type,        TU.Borrower))
g.add((rahul_uri,    RDFS.label,      Literal("Rahul Sharma", lang="en")))
g.add((rahul_uri,    TU.creditScore,  Literal(755, datatype=XSD.integer)))
g.add((rahul_uri,    TU.dti,          Literal("0.27", datatype=XSD.decimal)))
g.add((rahul_uri,    TU.hasReport,    report_uri))
g.add((rahul_uri,    TU.hasLoan,      loan_uri))

g.add((report_uri,   RDF.type,        TU.CreditReport))
g.add((report_uri,   TU.creditScore,  Literal(755, datatype=XSD.integer)))
g.add((report_uri,   TU.reportDate,   Literal("2026-05-20", datatype=XSD.date)))
g.add((report_uri,   TU.bureau,       Literal("Equifax")))

g.add((loan_uri,     RDF.type,        TU.Loan))
g.add((loan_uri,     TU.loanAmount,   Literal(500000, datatype=XSD.integer)))
g.add((loan_uri,     TU.loanPurpose,  Literal("personal")))

g.add((decision_uri, RDF.type,           TU.Decision))
g.add((decision_uri, TU.decisionOutcome, Literal("APPROVED")))
g.add((decision_uri, TU.forBorrower,     rahul_uri))

print(f"  Graph built with {len(g)} triples using proper URI scheme")
print()
print("  Sample triples with correct URIs:")
for s, p, o in list(g)[:6]:
    s_str = str(s).replace("http://transunion.com/data/borrower/", "tu-bwr:")
    s_str = s_str.replace("http://transunion.com/ontology#", "tu:")
    p_str = str(p).replace("http://transunion.com/ontology#", "tu:")
    p_str = p_str.replace("http://www.w3.org/1999/02/22-rdf-syntax-ns#type", "a")
    p_str = p_str.replace("http://www.w3.org/2000/01/rdf-schema#label", "rdfs:label")
    o_str = str(o).replace("http://transunion.com/ontology#", "tu:")
    o_str = o_str.replace("http://transunion.com/data/", "tu-data:")
    print(f"    {s_str[:40]:<40} {p_str:<25} {o_str[:30]}")
print()


# ─────────────────────────────────────────────────────────────
# SECTION 6: Reflection Answers
# ─────────────────────────────────────────────────────────────

print("SECTION 6: Reflection Answers")
print("-" * 65)
print("""
  Q1: Should SSN or PAN be in the URI?
  ──────────────────────────────────────
  NEVER put raw SSN or PAN in a URI. Why:
  1. URIs appear in log files (web server, load balancer, CDN, monitoring)
  2. Browser history stores URIs with PII
  3. HTTP Referer headers send URIs to third parties
  4. Error messages display URIs in stack traces
  5. India IT Act & DPDP Act: PAN is regulated PII, exposure = compliance risk

  CORRECT APPROACH: Use a salted hash of the PAN
    URI: http://transunion.com/borrower/a3f8d2c19e47b051
    - Same PAN always → same hash (stable, globally unique)
    - Cannot reverse-engineer PAN from hash without the salt
    - Safe in logs, error messages, browser history

  Q2: How to handle URI changes over time?
  ─────────────────────────────────────────
  Rule 1: NEVER change ontology term URIs (tu:Borrower, tu:creditScore)
          Partners import these. 500M triples use them. Breaking = catastrophic.

  Rule 2: For deprecated terms, add owl:deprecated and owl:equivalentClass
          tu:OldBorrower owl:deprecated true ;
                         owl:equivalentClass tu:Borrower .

  Rule 3: For data URI changes, use owl:sameAs
          <old-uri> owl:sameAs <new-uri> .

  Rule 4: NEVER put version in URIs (Cagle: versioning is metadata)
          WRONG: http://transunion.com/ontology/v2#Borrower
          RIGHT: <http://transunion.com/ontology> owl:versionInfo "2.0" .

  Rule 5: For data URIs tied to unstable identifiers (employee ID changes),
          use an opaque internal UUID as the URI base. The UUID never changes
          even if the person's employee ID changes.
""")

print("=" * 65)
print("Day 9 Exercise Complete!")
print(f"  Namespaces designed: {len(namespaces)}")
print(f"  Example URIs generated: {len(test_cases)}")
print(f"  KG triples built with correct scheme: {len(g)}")
print()
print("Key decisions made:")
print("  ✅ Ontology terms: hash URIs (#) — stable vocabulary")
print("  ✅ Data instances: slash URIs (/) with type prefix")
print("  ✅ Borrowers: opaque hash of PAN (privacy-safe, stable)")
print("  ✅ Loans/Decisions: meaningful (already opaque system IDs)")
print("  ✅ Named Graphs: source + date structure")
print("  ✅ Version: metadata not URI (owl:versionInfo)")
print("  ✅ SSN/PAN: NEVER in URI. Hash with salt only.")
print("=" * 65)
