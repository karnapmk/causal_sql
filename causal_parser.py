import re

def parse_causal_query(query):
    """
    Accepts queries like:
        SELECT AVG(disease_outcome) FROM observations DO(gene_expressed = 1)
    
    Returns (base_sql, intervention_dict) or (query, None) if no DO clause.
    """
    query = query.strip()
    do_match = re.search(
        r'\bDO\s*\(\s*(\w+)\s*=\s*([\d.]+)\s*\)',
        query,
        re.IGNORECASE
    )

    if not do_match:
        return query, None

    variable = do_match.group(1)
    value = float(do_match.group(2))
    
    # Strip the DO(...) clause to get base SQL
    base_sql = (query[:do_match.start()] + query[do_match.end():]).strip()

    return base_sql, {"variable": variable, "value": value}