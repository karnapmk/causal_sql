import duckdb
from causal_parser import parse_causal_query
from intervention import run_causal_query

conn = duckdb.connect("bio.db")

print("=" * 60)
print("CAUSAL SQL DEMO")
print("=" * 60)
print()
print("Database: patient observations with confounding")
print("Causal DAG:")
print("  hidden_severity --> gene_expressed --> protein_level --> disease_outcome")
print("  hidden_severity -----------------------------------------> disease_outcome")
print()

# ---- The query ----
causal_query = """
SELECT AVG(disease_outcome) FROM observations DO(gene_expressed = 1)
"""

print(f"Query: {causal_query.strip()}")
print()

# Parse
base_sql, intervention = parse_causal_query(causal_query)

if intervention is None:
    result = conn.execute(base_sql).df()
    print("No DO clause — running as standard SQL:")
    print(result)
else:
    var = intervention["variable"]
    val = intervention["value"]
    
    obs_answer, do_answer, details = run_causal_query(conn, base_sql, intervention)
    
    print(f"Intervention: do({var} = {val})")
    print()
    print("--- OBSERVATIONAL answer (WHERE clause) ---")
    print(f"  SELECT AVG(disease_outcome) FROM observations WHERE {var} = {val}")
    print(f"  Result: {obs_answer}")
    print(f"  Interpretation: average outcome among patients who HAPPENED to have {var}={val}")
    print(f"  Problem: confounded by hidden_severity!")
    print()
    print("--- INTERVENTIONAL answer (DO operator) ---")
    print(f"  Result: {do_answer}")
    print(f"  Interpretation: expected outcome if we FORCED {var}={val} for everyone")
    print(f"  This breaks the hidden_severity -> {var} link")
    print()
    print("--- How the DO computation works ---")
    print(f"  Predicted protein_level when gene_expressed={val}: {details['step1_protein']}")
    print(f"  Causal effect of gene on protein: {details['slope_gene_to_protein']}")
    print(f"  Causal effect of protein on outcome: {details['slope_protein_to_outcome']}")
    print()
    if obs_answer != "no rows" and isinstance(obs_answer, float):
        diff = round(abs(do_answer - obs_answer), 4)
        print(f"  Difference between WHERE and DO: {diff}")
        print(f"  This difference IS the confounding bias.")

conn.close()