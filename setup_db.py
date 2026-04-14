import duckdb

conn = duckdb.connect("bio.db")

# Patient observations - confounded!
# Hidden factor (e.g. disease severity) affects BOTH 
# whether gene is expressed AND the outcome
# This is why WHERE != DO
conn.execute("""
    CREATE OR REPLACE TABLE observations (
        patient_id INTEGER,
        gene_expressed INTEGER,   -- 1 = gene active, 0 = silenced
        protein_level FLOAT,      -- caused by gene_expressed
        disease_outcome FLOAT     -- caused by protein_level
    )
""")

# Confounded data: sicker patients BOTH have gene expressed 
# AND worse outcomes naturally
conn.execute("""
    INSERT INTO observations VALUES
        (1,  1, 8.2, 7.1),
        (2,  1, 7.9, 6.8),
        (3,  1, 8.5, 7.4),
        (4,  1, 7.8, 6.9),
        (5,  0, 3.1, 6.8),
        (6,  0, 2.9, 6.5),
        (7,  0, 3.3, 7.0),
        (8,  0, 3.0, 6.7)
""")

# The causal DAG stored as a table
conn.execute("""
    CREATE OR REPLACE TABLE causal_dag (
        cause VARCHAR,
        effect VARCHAR
    )
""")

conn.execute("""
    INSERT INTO causal_dag VALUES
        ('gene_expressed', 'protein_level'),
        ('protein_level', 'disease_outcome'),
        ('hidden_severity', 'gene_expressed'),
        ('hidden_severity', 'disease_outcome')
""")

conn.close()
print("Database ready.")
print("Causal structure: hidden_severity -> gene_expressed -> protein_level -> disease_outcome")
print("                  hidden_severity ----------------------------------------> disease_outcome")