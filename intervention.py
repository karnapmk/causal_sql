import duckdb
import pandas as pd
import numpy as np

def observational_answer(conn, base_sql, variable, value):
    """What WHERE gives you — observational, potentially wrong."""
    where_sql = base_sql + f" WHERE {variable} = {value}"
    try:
        result = conn.execute(where_sql).fetchone()
        return round(result[0], 4) if result and result[0] is not None else "no rows"
    except Exception as e:
        return f"error: {e}"

def interventional_answer(conn, base_sql, variable, value):
    """
    What DO gives you — interventional.
    
    Key idea: do(gene_expressed = 1) means we imagine a world where
    gene_expressed is FORCED to 1 for everyone, breaking the link
    from hidden_severity -> gene_expressed.
    
    We estimate this using the backdoor adjustment formula:
    E[outcome | do(X=x)] = sum_z E[outcome | X=x, Z=z] * P(Z=z)
    
    Where Z = hidden_severity (the confounder).
    
    Since we can't observe hidden_severity directly, we use a 
    linear structural equation model fit from the data.
    """
    data = conn.execute("SELECT * FROM observations").df()
    
    # Step 1: Fit structural equation: protein_level ~ gene_expressed
    x = data["gene_expressed"].values
    y_protein = data["protein_level"].values
    
    # Simple linear regression
    slope_p = np.cov(x, y_protein)[0,1] / np.var(x)
    intercept_p = np.mean(y_protein) - slope_p * np.mean(x)
    
    # Step 2: Fit structural equation: disease_outcome ~ protein_level
    protein = data["protein_level"].values
    y_outcome = data["disease_outcome"].values
    
    slope_o = np.cov(protein, y_outcome)[0,1] / np.var(protein)
    intercept_o = np.mean(y_outcome) - slope_o * np.mean(protein)
    
    # Step 3: Apply intervention — set gene_expressed = value for EVERYONE
    # This breaks the hidden_severity -> gene_expressed link
    predicted_protein = intercept_p + slope_p * value
    predicted_outcome = intercept_o + slope_o * predicted_protein
    
    return round(predicted_outcome, 4), {
        "step1_protein": round(predicted_protein, 4),
        "slope_gene_to_protein": round(slope_p, 4),
        "slope_protein_to_outcome": round(slope_o, 4)
    }

def run_causal_query(conn, base_sql, intervention):
    variable = intervention["variable"]
    value = intervention["value"]
    
    obs = observational_answer(conn, base_sql, variable, value)
    do_val, details = interventional_answer(conn, base_sql, variable, value)
    
    return obs, do_val, details