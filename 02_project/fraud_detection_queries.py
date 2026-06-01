"""
fraud_detection_queries.py — Weekend Project 2 Runner
Executes all SPARQL queries from fraud_detection_queries.sparql
and generates fraud_ring_visualization.png + HTML interactive viz.
"""

from rdflib import Graph, Namespace, RDF, RDFS
from pyvis.network import Network
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import textwrap

print("=" * 65)
print("Weekend Project 2: Fraud Detection Graph")
print("Executing all SPARQL queries on fraud_network.ttl")
print("=" * 65)
print()

# ── Load Graph ───────────────────────────────────────────────
g = Graph()
g.parse("fraud_network.ttl", format="turtle")
print(f"Graph loaded: {len(g)} triples\n")

TU   = Namespace("http://transunion.com/ontology#")
DATA = Namespace("http://transunion.com/data#")

PREFIX = """
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX tu:   <http://transunion.com/ontology#>
PREFIX data: <http://transunion.com/data#>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>
"""

# ── Query 1: Direct connections ──────────────────────────────
print("─" * 65)
print("QUERY 1: Direct 1-Hop Connections to Known Defaulters")
print("─" * 65)

q1 = PREFIX + """
SELECT DISTINCT ?suspectName ?defaulterName ?connectionType ?sharedEntity
WHERE {
    ?defaulter a tu:Borrower ; tu:hasDefault true ; tu:name ?defaulterName .
    ?suspect   a tu:Borrower ; tu:hasDefault false ; tu:name ?suspectName .
    {
        ?defaulter tu:sharesPhone ?shared . ?suspect tu:sharesPhone ?shared .
        BIND("SHARED_PHONE" AS ?connectionType) ?shared tu:name ?sharedEntity
    } UNION {
        ?defaulter tu:livesAt ?shared . ?suspect tu:livesAt ?shared .
        BIND("SHARED_ADDRESS" AS ?connectionType) ?shared tu:name ?sharedEntity
    } UNION {
        ?defaulter tu:claimsEmployer ?shared . ?suspect tu:claimsEmployer ?shared .
        BIND("SHARED_EMPLOYER" AS ?connectionType) ?shared tu:name ?sharedEntity
    } UNION {
        ?defaulter tu:usesDevice ?shared . ?suspect tu:usesDevice ?shared .
        BIND("SHARED_DEVICE" AS ?connectionType) ?shared tu:name ?sharedEntity
    }
} ORDER BY ?defaulterName ?suspectName
"""
r1 = list(g.query(q1))
print(f"{'Suspect':<20} {'Defaulter':<18} {'Connection':<18} {'Shared Entity'}")
print("-" * 75)
for row in r1:
    entity = str(row.sharedEntity)[:30]
    print(f"{str(row.suspectName):<20} {str(row.defaulterName):<18} "
          f"{str(row.connectionType):<18} {entity}")
print(f"\n→ SQL would MISS these {len(r1)} connections (looks at each borrower in isolation)")
print()

# ── Query 2: 3-hop traversal ─────────────────────────────────
print("─" * 65)
print("QUERY 2: 3-Hop Traversal Using SPARQL Property Paths")
print("─" * 65)
print("SPARQL: (tu:sharesPhone|tu:livesAt|tu:claimsEmployer|tu:usesDevice){1,3}")
print()

q2 = PREFIX + """
SELECT DISTINCT ?defaulterName ?suspectName ?suspectScore ?suspectDTI
WHERE {
    ?defaulter a tu:Borrower ; tu:hasDefault true ; tu:name ?defaulterName .
    # Note: rdflib uses + (one-or-more) for multi-hop; {1,3} supported in Stardog/full SPARQL 1.1
    ?defaulter (tu:sharesPhone|tu:livesAt|tu:claimsEmployer|tu:usesDevice)+ ?shared .
    ?suspect   (tu:sharesPhone|tu:livesAt|tu:claimsEmployer|tu:usesDevice) ?shared .
    ?suspect a tu:Borrower ; tu:hasDefault false ;
             tu:name ?suspectName ; tu:creditScore ?suspectScore ; tu:dti ?suspectDTI .
    FILTER(?suspect != ?defaulter)
} ORDER BY ?defaulterName ASC(?suspectScore)
"""
r2 = list(g.query(q2))
print(f"{'Defaulter':<18} {'Suspect':<20} {'Score':<8} {'DTI':<8} {'Action'}")
print("-" * 70)
for row in r2:
    score = int(row.suspectScore)
    dti   = float(row.suspectDTI)
    action = "REJECT" if score < 620 or dti > 0.43 else "FLAG FOR REVIEW"
    print(f"{str(row.defaulterName):<18} {str(row.suspectName):<20} "
          f"{score:<8} {dti:<8.2f} {action}")
print(f"\n→ Found {len(r2)} suspicious borrowers via 3-hop traversal")
print("→ SQL equivalent would require 3+ recursive CTEs — 50+ lines")
print()

# ── Query 3: Clusters (3+ shared entities) ───────────────────
print("─" * 65)
print("QUERY 3: Clusters — Borrower Pairs with 2+ Shared Entities")
print("─" * 65)

q3 = PREFIX + """
SELECT ?b1Name ?b2Name (COUNT(DISTINCT ?shared) AS ?sharedCount)
WHERE {
    ?b1 a tu:Borrower ; tu:name ?b1Name .
    ?b2 a tu:Borrower ; tu:name ?b2Name .
    { ?b1 tu:sharesPhone ?shared . ?b2 tu:sharesPhone ?shared . } UNION
    { ?b1 tu:livesAt ?shared .     ?b2 tu:livesAt ?shared . } UNION
    { ?b1 tu:claimsEmployer ?shared . ?b2 tu:claimsEmployer ?shared . } UNION
    { ?b1 tu:usesDevice ?shared .  ?b2 tu:usesDevice ?shared . }
    FILTER(?b1 != ?b2)
    FILTER(STR(?b1Name) < STR(?b2Name))
} GROUP BY ?b1Name ?b2Name
HAVING (COUNT(DISTINCT ?shared) >= 2)
ORDER BY DESC(?sharedCount)
"""
r3 = list(g.query(q3))
print(f"{'Borrower 1':<22} {'Borrower 2':<22} {'Shared Entities':<8} {'Risk Level'}")
print("-" * 65)
for row in r3:
    count = int(row.sharedCount)
    risk  = "HIGH RISK — Fraud Ring" if count >= 2 else "MEDIUM RISK"
    print(f"{str(row.b1Name):<22} {str(row.b2Name):<22} {count:<8} {risk}")
print()

# ── Query 4: Address clusters ─────────────────────────────────
print("─" * 65)
print("QUERY 4: Synthetic Identity — Multiple Borrowers at Same Address")
print("─" * 65)

q4 = PREFIX + """
SELECT ?addressName (COUNT(DISTINCT ?borrower) AS ?count)
       (GROUP_CONCAT(DISTINCT ?borrowerName; separator=", ") AS ?borrowers)
WHERE {
    ?borrower a tu:Borrower ; tu:name ?borrowerName ; tu:livesAt ?address .
    ?address tu:name ?addressName .
} GROUP BY ?addressName HAVING (COUNT(DISTINCT ?borrower) >= 2) ORDER BY DESC(?count)
"""
for row in g.query(q4):
    print(f"Address: {str(row.addressName)[:50]}")
    print(f"  Count: {row['count']} borrowers")
    print(f"  Who:   {row.borrowers}")
    print()

# ── Query 5: Bust-out detection ───────────────────────────────
print("─" * 65)
print("QUERY 5: Bust-Out Scheme — Same Employer + Same Device")
print("─" * 65)

q5 = PREFIX + """
SELECT ?employerName ?deviceName (COUNT(DISTINCT ?borrower) AS ?count)
       (GROUP_CONCAT(DISTINCT ?borrowerName; separator=", ") AS ?borrowers)
WHERE {
    ?borrower a tu:Borrower ; tu:name ?borrowerName ;
              tu:claimsEmployer ?employer ; tu:usesDevice ?device .
    ?employer tu:name ?employerName . ?device tu:name ?deviceName .
} GROUP BY ?employerName ?deviceName HAVING (COUNT(DISTINCT ?borrower) >= 2)
"""
for row in g.query(q5):
    print(f"Employer: {row.employerName}")
    print(f"Device:   {str(row.deviceName)[:30]}...")
    print(f"Count:    {row['count']} borrowers sharing both!")
    print(f"Who:      {row.borrowers}")
    print()

# ── Query 6: Risk ranking ─────────────────────────────────────
print("─" * 65)
print("QUERY 6: Risk-Ranked Suspicious Applicants")
print("─" * 65)

q6 = PREFIX + """
SELECT ?suspectName ?suspectScore ?suspectDTI
       (COUNT(DISTINCT ?defaulterName) AS ?connectedDefaulters)
       (GROUP_CONCAT(DISTINCT ?connectionType; separator=" | ") AS ?riskSignals)
WHERE {
    ?defaulter a tu:Borrower ; tu:hasDefault true ; tu:name ?defaulterName .
    ?suspect   a tu:Borrower ; tu:hasDefault false ;
               tu:name ?suspectName ; tu:creditScore ?suspectScore ; tu:dti ?suspectDTI .
    { ?defaulter tu:sharesPhone ?s . ?suspect tu:sharesPhone ?s .
      BIND("PHONE" AS ?connectionType) } UNION
    { ?defaulter tu:livesAt ?s . ?suspect tu:livesAt ?s .
      BIND("ADDRESS" AS ?connectionType) } UNION
    { ?defaulter tu:claimsEmployer ?s . ?suspect tu:claimsEmployer ?s .
      BIND("EMPLOYER" AS ?connectionType) } UNION
    { ?defaulter tu:usesDevice ?s . ?suspect tu:usesDevice ?s .
      BIND("DEVICE" AS ?connectionType) }
} GROUP BY ?suspectName ?suspectScore ?suspectDTI
ORDER BY DESC(?connectedDefaulters) ASC(?suspectScore)
"""
r6 = list(g.query(q6))
print(f"{'#':<3} {'Name':<20} {'Score':<8} {'DTI':<6} {'Defaulters':<12} {'Risk Signals'}")
print("-" * 72)
for i, row in enumerate(r6, 1):
    print(f"{i:<3} {str(row.suspectName):<20} {int(row.suspectScore):<8} "
          f"{float(row.suspectDTI):<6.2f} {int(row.connectedDefaulters):<12} {row.riskSignals}")
print()

# ── Query 7: Fraud ring membership ───────────────────────────
print("─" * 65)
print("QUERY 7: Full Fraud Ring Membership")
print("─" * 65)

q7 = PREFIX + """
SELECT ?borrowerName ?creditScore ?hasDefault ?fraudRing
WHERE {
    ?borrower a tu:Borrower ; tu:name ?borrowerName ;
              tu:creditScore ?creditScore ; tu:hasDefault ?hasDefault .
    OPTIONAL { ?borrower tu:fraudRing ?fraudRing }
    FILTER(BOUND(?fraudRing))
} ORDER BY ?fraudRing ASC(?creditScore)
"""
current_ring = None
for row in g.query(q7):
    ring = str(row.fraudRing)
    if ring != current_ring:
        print(f"\n  [{ring}]")
        current_ring = ring
    default_flag = "⚠️  DEFAULTER" if str(row.hasDefault) == "true" else "   clean"
    print(f"    {str(row.borrowerName):<22} score={int(row.creditScore)}  {default_flag}")
print()

# ═══════════════════════════════════════════════════════════════
# VISUALIZATION 1: MATPLOTLIB PNG (fraud_ring_visualization.png)
# ═══════════════════════════════════════════════════════════════

print("─" * 65)
print("Generating fraud_ring_visualization.png...")
print("─" * 65)

fig, ax = plt.subplots(1, 1, figsize=(18, 12))
ax.set_facecolor('#0d1117')
fig.patch.set_facecolor('#0d1117')

G = nx.DiGraph()

# Node definitions
borrowers = {
    "Vijay Kumar":    {"ring": "A", "default": True,  "score": 480},
    "Rajan Verma":    {"ring": "A", "default": False, "score": 695},
    "Sunita Rao":     {"ring": "A", "default": False, "score": 720},
    "Dev Mehta":      {"ring": "B", "default": True,  "score": 510},
    "Arjun Kapoor":   {"ring": "B", "default": False, "score": 660},
    "Meera Sharma":   {"ring": "B", "default": False, "score": 710},
    "Suresh Patel":   {"ring": "C", "default": True,  "score": 540},
    "Priya Patel":    {"ring": "C", "default": False, "score": 685},
    "Lakshmi Patel":  {"ring": "C", "default": False, "score": 640},
    "Rahul Mehta":    {"ring": "CLEAN", "default": False, "score": 755},
    "Anita Singh":    {"ring": "CLEAN", "default": False, "score": 730},
}

shared = {
    "Phone_A":       {"type": "phone",   "ring": "A"},
    "Addr_A":        {"type": "address", "ring": "A"},
    "Employer_B":    {"type": "employer","ring": "B"},
    "Device_B":      {"type": "device",  "ring": "B"},
    "Addr_C":        {"type": "address", "ring": "C"},
}

# Edges
edges_raw = [
    ("Vijay Kumar",  "Phone_A",    "sharesPhone"),
    ("Rajan Verma",  "Phone_A",    "sharesPhone"),
    ("Vijay Kumar",  "Addr_A",     "livesAt"),
    ("Rajan Verma",  "Addr_A",     "livesAt"),
    ("Sunita Rao",   "Addr_A",     "livesAt"),
    ("Dev Mehta",    "Employer_B", "claimsEmployer"),
    ("Arjun Kapoor", "Employer_B", "claimsEmployer"),
    ("Meera Sharma", "Employer_B", "claimsEmployer"),
    ("Dev Mehta",    "Device_B",   "usesDevice"),
    ("Arjun Kapoor", "Device_B",   "usesDevice"),
    ("Meera Sharma", "Device_B",   "usesDevice"),
    ("Suresh Patel", "Addr_C",     "livesAt"),
    ("Priya Patel",  "Addr_C",     "livesAt"),
    ("Lakshmi Patel","Addr_C",     "livesAt"),
]

for n in borrowers: G.add_node(n, ntype="borrower")
for n in shared:    G.add_node(n, ntype="shared")
for s, t, l in edges_raw: G.add_edge(s, t, label=l)

# Manual layout — rings clustered together
pos = {
    # Ring A — top left
    "Vijay Kumar":  (-3.5, 2.0),
    "Rajan Verma":  (-4.5, 0.5),
    "Sunita Rao":   (-2.5, 0.5),
    "Phone_A":      (-4.5, 1.5),
    "Addr_A":       (-2.5, 1.5),
    # Ring B — top right
    "Dev Mehta":    (3.5,  2.0),
    "Arjun Kapoor": (2.5,  0.5),
    "Meera Sharma": (4.5,  0.5),
    "Employer_B":   (2.5,  1.5),
    "Device_B":     (4.5,  1.5),
    # Ring C — bottom center
    "Suresh Patel": (0.0, -1.0),
    "Priya Patel":  (-1.5, -2.5),
    "Lakshmi Patel":(1.5,  -2.5),
    "Addr_C":       (0.0,  -2.5),
    # Clean — far right bottom
    "Rahul Mehta":  (4.5,  -2.0),
    "Anita Singh":  (4.5,  -3.0),
}

# Node colours
node_colors, node_sizes, node_shapes = [], [], []
for node in G.nodes():
    if node in borrowers:
        b = borrowers[node]
        if b["default"]:
            node_colors.append("#e53935")   # red for defaulters
        elif b["ring"] == "CLEAN":
            node_colors.append("#43a047")   # green for clean
        elif b["ring"] == "A":
            node_colors.append("#ff9800")   # orange for ring A
        elif b["ring"] == "B":
            node_colors.append("#7b1fa2")   # purple for ring B
        else:
            node_colors.append("#0288d1")   # blue for ring C
        node_sizes.append(1400 if b["default"] else 1000)
    else:
        et = shared[node]["type"]
        color_map = {"phone":"#26c6da","address":"#66bb6a","employer":"#ffa726","device":"#ab47bc"}
        node_colors.append(color_map.get(et, "#aaa"))
        node_sizes.append(600)

nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes,
                       alpha=0.9, ax=ax)
nx.draw_networkx_edges(G, pos, edge_color="#555577", arrows=True,
                       arrowsize=12, width=1.5, ax=ax,
                       connectionstyle="arc3,rad=0.05")

# Labels
for node, (x, y) in pos.items():
    if node in borrowers:
        b = borrowers[node]
        label = f"{node}\n(Score:{b['score']})"
        if b["default"]: label += "\n⚠ DEFAULT"
        fontsize, fontweight = 7, "bold"
        color = "white"
    else:
        label = node.replace("_", "\n")
        fontsize, fontweight, color = 6, "normal", "#cccccc"
    ax.text(x, y, label, ha="center", va="center",
            fontsize=fontsize, fontweight=fontweight,
            color=color, zorder=5,
            bbox=dict(boxstyle="round,pad=0.2", facecolor="none", edgecolor="none"))

# Ring boundary circles
ring_centres = {
    "A: Synthetic Identity\n(Shared Phone + Address)": (-3.5, 1.2, 2.0, "#ff9800"),
    "B: Bust-Out Scheme\n(Fake Employer + Device)":    (3.5,  1.2, 2.0, "#7b1fa2"),
    "C: Family Collusion\n(Shared Address)":            (0.0, -1.8, 1.8, "#0288d1"),
}
for label, (cx, cy, r, color) in ring_centres.items():
    circle = plt.Circle((cx, cy), r, fill=False, color=color,
                        linewidth=2, linestyle="--", alpha=0.6)
    ax.add_patch(circle)
    ax.text(cx, cy + r + 0.15, label, ha="center", va="bottom",
            fontsize=8, color=color, fontweight="bold")

ax.set_title("TransUnion Fraud Detection Knowledge Graph\n"
             "Three Fraud Rings: Synthetic Identity (A) | Bust-Out (B) | Family Collusion (C)",
             fontsize=13, color="white", fontweight="bold", pad=15)

# Legend
legend_elements = [
    mpatches.Patch(color="#e53935", label="Known Defaulter"),
    mpatches.Patch(color="#ff9800", label="Ring A: Synthetic Identity"),
    mpatches.Patch(color="#7b1fa2", label="Ring B: Bust-Out Scheme"),
    mpatches.Patch(color="#0288d1", label="Ring C: Family Collusion"),
    mpatches.Patch(color="#43a047", label="Clean Borrower"),
    mpatches.Patch(color="#26c6da", label="Shared Phone"),
    mpatches.Patch(color="#66bb6a", label="Shared Address"),
    mpatches.Patch(color="#ffa726", label="Shared Employer"),
    mpatches.Patch(color="#ab47bc", label="Shared Device"),
]
ax.legend(handles=legend_elements, loc="lower left",
          facecolor="#1a1a2e", edgecolor="#555", labelcolor="white",
          fontsize=8, framealpha=0.9)

ax.set_xlim(-6.5, 6.5)
ax.set_ylim(-4.5, 4.0)
ax.axis("off")

plt.tight_layout()
plt.savefig("fraud_ring_visualization.png", dpi=150, bbox_inches="tight",
            facecolor='#0d1117')
print("  fraud_ring_visualization.png saved!")
plt.close()

# ═══════════════════════════════════════════════════════════════
# VISUALIZATION 2: PYVIS INTERACTIVE HTML
# ═══════════════════════════════════════════════════════════════

print("  Generating fraud_network_interactive.html...")

net = Network(height="700px", width="100%", bgcolor="#0d1117",
              font_color="white", directed=False)
net.set_options("""
{
  "nodes": {"font": {"size": 13}},
  "edges": {"color": {"color":"#444466"}, "font": {"size":10, "color":"#aaaaaa"},
             "smooth": {"type":"curvedCW","roundness":0.2}},
  "physics": {"barnesHut": {"gravitationalConstant":-8000,
               "centralGravity":0.3,"springLength":180}},
  "interaction": {"hover": true, "tooltipDelay": 200}
}
""")

ring_colors = {"A":"#ff9800","B":"#7b1fa2","C":"#0288d1","CLEAN":"#43a047"}
shared_colors = {"phone":"#26c6da","address":"#66bb6a","employer":"#ffa726","device":"#ab47bc"}

for name, b in borrowers.items():
    color = "#e53935" if b["default"] else ring_colors.get(b["ring"], "#888")
    size  = 35 if b["default"] else 25
    title = (f"<b>{name}</b><br>Score: {b['score']}<br>"
             f"Ring: {b['ring']}<br>Default: {b['default']}")
    label = f"{'⚠ ' if b['default'] else ''}{name}\nScore:{b['score']}"
    net.add_node(name, label=label, color=color, size=size,
                 title=title, shape="ellipse")

for name, s in shared.items():
    color = shared_colors.get(s["type"], "#888")
    title = f"<b>{name}</b><br>Type: {s['type']}<br>Ring: {s['ring']}"
    net.add_node(name, label=name, color=color, size=15,
                 title=title, shape="diamond")

edge_labels = {"sharesPhone":"phone","livesAt":"address",
               "claimsEmployer":"employer","usesDevice":"device"}
for s, t, l in edges_raw:
    net.add_edge(s, t, label=edge_labels.get(l, l), width=2)

net.save_graph("fraud_network_interactive.html")
print("  fraud_network_interactive.html saved!")

print()
print("=" * 65)
print("All queries executed. All visualizations generated.")
print()
print("Files created:")
print("  fraud_ring_visualization.png  — static graph for analysis.md")
print("  fraud_network_interactive.html — Neo4j Browser-style interactive")
print()
print("Key findings:")
print(f"  Borrowers flagged (1-hop):  {len(r1)} connections found")
print(f"  Borrowers flagged (3-hop):  {len(r2)} suspicious applicants")
print(f"  High-risk clusters:         {len(r3)} pairs with 2+ shared entities")
print(f"  Fraud ring members:         9 out of 11 borrowers")
print(f"  Clean borrowers:            2 (Rahul Mehta, Anita Singh)")
print("=" * 65)
