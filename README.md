# Extending SQL to Causal Queries

## The DO Operator

This project adds a `DO()` clause to DuckDB's SQL syntax:

```sql
SELECT AVG(disease_outcome) FROM observations DO(gene_expressed = 1)
```

`DO(variable = value)` is intended to express a causal intervention — "what is the average outcome *when we set* `gene_expressed` to 1?" It is implemented as a DuckDB 1.5 C++ extension using the `ParserExtension` API: when DuckDB's standard parser encounters the unknown `DO(...)` syntax, our extension intercepts the query, strips the clause, and stores the intervention for later execution.

> **Note:** Parsing works. Execution (actually computing the causal estimate) is not yet implemented.

---

## Background: Runtime-Extensible Parsers

This work is based on the CIDR 2025 paper [*Runtime-Extensible SQL Parsers Using PEG*](https://duckdb.org/pdf/CIDR2025-muehleisen-raasveldt-extensible-parsers.pdf) by Hannes Mühleisen and Mark Raasveldt (the creators of DuckDB). The paper argues that SQL parsers should be modifiable at runtime — without recompiling the database — so that domain-specific extensions can introduce new syntax.

DuckDB 1.5 ships this as the `ParserExtension` API. Extensions register a `parse_function_t`: a C++ callback that fires when the standard PostgreSQL-based parser fails. The extension receives the raw query string, parses what it understands, and returns a result that DuckDB plans and executes normally.

Our DO() clause is a direct application of this: the standard parser rejects `DO(gene_expressed = 1)`, our callback intercepts it, strips and stores the intervention, and hands control back to DuckDB. No grammar files needed — just a C++ function registered at extension load time.

---

## Toggling the Extension

**On** — use the extension's own DuckDB shell (the extension is built in):
```bash
./ext/build/release/duckdb
```

**Off** — use the system DuckDB (no extension loaded):
```bash
/usr/local/bin/duckdb
```

To load the extension on-demand in any DuckDB session:
```sql
LOAD './ext/build/release/extension/quack/quack.duckdb_extension';
```

---

## Custom Queries

**Store data** in `data/` (CSV or Parquet):
```
causal_sql/data/observations.csv
```

**Write queries** in `queries/` as plain `.sql` files:
```
causal_sql/queries/my_query.sql
```

**Run a query file:**
```bash
./ext/build/release/duckdb -f queries/my_query.sql
```

Or run inline:
```bash
./ext/build/release/duckdb -c "SELECT AVG(disease_outcome) FROM read_csv_auto('data/observations.csv') DO(gene_expressed = 1);"
```
