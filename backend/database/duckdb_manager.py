"""DuckDB database manager for efficient analytics on large datasets."""

import duckdb
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
import time
import logging
from contextlib import contextmanager

from database.schema import TABLES, get_schema_description

logger = logging.getLogger(__name__)


class DuckDBManager:
    """Manages DuckDB connection and query execution."""

    def __init__(self, data_dir: str = "./data", db_path: Optional[str] = None):
        """
        Initialize DuckDB manager.

        Args:
            data_dir: Directory containing CSV files
            db_path: Path to DuckDB file (None for in-memory)
        """
        self.data_dir = Path(data_dir)
        self.db_path = db_path
        self.conn: Optional[duckdb.DuckDBPyConnection] = None
        self.schema_description = get_schema_description()
        self._loaded_tables = set()

    def connect(self) -> None:
        """Establish database connection."""
        if self.db_path:
            logger.info(f"Connecting to DuckDB at {self.db_path}")
            self.conn = duckdb.connect(self.db_path)
        else:
            logger.info("Creating in-memory DuckDB instance")
            self.conn = duckdb.connect(":memory:")

        # Optimize for analytics workloads
        self.conn.execute("SET threads TO 4")
        self.conn.execute("SET memory_limit = '4GB'")

        # Enable performance optimizations for large datasets
        self.conn.execute("SET enable_object_cache = true")
        self.conn.execute("SET preserve_insertion_order = false")  # Faster aggregations

        logger.info("DuckDB optimized for 32M+ row analytics workloads")

    def load_data(self) -> Dict[str, int]:
        """
        Load all CSV files into DuckDB tables.

        Returns:
            Dictionary of table_name -> row_count
        """
        if not self.conn:
            self.connect()

        stats = {}

        for table_name, table_schema in TABLES.items():
            csv_path = self.data_dir / table_schema.file_name

            if not csv_path.exists():
                logger.warning(f"CSV file not found: {csv_path}")
                continue

            logger.info(f"Loading {table_name} from {csv_path}")
            start_time = time.time()

            # Use DuckDB's native CSV reader (much faster than pandas)
            try:
                self.conn.execute(f"DROP TABLE IF EXISTS {table_name}")

                # DuckDB auto-detects schema, but we can hint for better performance
                self.conn.execute(f"""
                    CREATE TABLE {table_name} AS
                    SELECT * FROM read_csv_auto('{csv_path}')
                """)

                # Get row count
                result = self.conn.execute(
                    f"SELECT COUNT(*) FROM {table_name}"
                ).fetchone()
                row_count = result[0] if result else 0

                elapsed = time.time() - start_time
                logger.info(
                    f"Loaded {table_name}: {row_count:,} rows in {elapsed:.2f}s"
                )

                stats[table_name] = row_count
                self._loaded_tables.add(table_name)

            except Exception as e:
                logger.error(f"Failed to load {table_name}: {e}")
                stats[table_name] = 0

        # Create indexes for common join columns
        self._create_indexes()

        return stats

    def _create_indexes(self) -> None:
        """Create indexes for frequently joined columns."""
        if not self.conn:
            return

        # Note: DuckDB doesn't have traditional indexes, but we can
        # optimize common queries with views or materialized CTEs
        logger.info("DuckDB uses automatic indexing - no manual indexes needed")

    def execute_query(
        self, sql: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a SQL query and return results with metadata.

        Args:
            sql: SQL query string
            params: Optional query parameters

        Returns:
            Dictionary with data, columns, row_count, and execution_time_ms
        """
        if not self.conn:
            raise RuntimeError("Database not connected")

        start_time = time.time()

        try:
            # Execute query
            result = self.conn.execute(sql, params or {})

            # Fetch results
            data = result.fetchall()
            columns = [desc[0] for desc in result.description] if result.description else []

            # Convert to list of dictionaries
            rows = [dict(zip(columns, row)) for row in data]

            execution_time = (time.time() - start_time) * 1000  # Convert to ms

            logger.info(
                f"Query executed: {len(rows)} rows in {execution_time:.2f}ms"
            )

            return {
                "data": rows,
                "columns": columns,
                "row_count": len(rows),
                "execution_time_ms": execution_time,
            }

        except Exception as e:
            logger.error(f"Query execution failed: {e}\nSQL: {sql}")
            raise

    def validate_sql(self, sql: str) -> tuple[bool, Optional[str]]:
        """
        Validate SQL without executing it.

        Args:
            sql: SQL query string

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.conn:
            return False, "Database not connected"

        try:
            # Use EXPLAIN to validate without execution
            self.conn.execute(f"EXPLAIN {sql}")
            return True, None
        except Exception as e:
            return False, str(e)

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get information about a specific table."""
        if not self.conn:
            raise RuntimeError("Database not connected")

        # Get schema
        schema = self.conn.execute(
            f"DESCRIBE {table_name}"
        ).fetchall()

        columns = [
            {"name": row[0], "type": row[1]}
            for row in schema
        ]

        # Get row count
        row_count = self.conn.execute(
            f"SELECT COUNT(*) FROM {table_name}"
        ).fetchone()[0]

        # Get sample data
        sample = self.conn.execute(
            f"SELECT * FROM {table_name} LIMIT 5"
        ).fetchall()

        sample_columns = [desc[0] for desc in self.conn.description]
        sample_data = [dict(zip(sample_columns, row)) for row in sample]

        return {
            "table_name": table_name,
            "columns": columns,
            "row_count": row_count,
            "sample_data": sample_data,
        }

    def get_all_tables(self) -> List[str]:
        """Get list of all loaded tables."""
        if not self.conn:
            return []

        result = self.conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='main'"
        ).fetchall()

        return [row[0] for row in result]

    def get_database_stats(self) -> Dict[str, Any]:
        """Get overall database statistics."""
        if not self.conn:
            return {
                "tables_count": 0,
                "total_rows": 0,
                "loaded_tables": [],
            }

        tables = self.get_all_tables()
        total_rows = 0

        for table in tables:
            count = self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            total_rows += count

        return {
            "tables_count": len(tables),
            "total_rows": total_rows,
            "loaded_tables": tables,
        }

    @contextmanager
    def transaction(self):
        """Context manager for transactions."""
        if not self.conn:
            raise RuntimeError("Database not connected")

        try:
            self.conn.execute("BEGIN TRANSACTION")
            yield self.conn
            self.conn.execute("COMMIT")
        except Exception as e:
            self.conn.execute("ROLLBACK")
            raise e

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("Database connection closed")

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
