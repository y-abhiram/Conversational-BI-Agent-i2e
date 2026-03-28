"""Database schema definitions and relationships."""

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class TableSchema:
    """Schema definition for a table."""

    name: str
    file_name: str
    primary_key: str
    columns: Dict[str, str]  # column_name -> type
    description: str


@dataclass
class Relationship:
    """Foreign key relationship between tables."""

    from_table: str
    from_column: str
    to_table: str
    to_column: str


# Instacart schema definitions
TABLES = {
    "orders": TableSchema(
        name="orders",
        file_name="orders.csv",
        primary_key="order_id",
        columns={
            "order_id": "INTEGER",
            "user_id": "INTEGER",
            "eval_set": "VARCHAR",
            "order_number": "INTEGER",
            "order_dow": "INTEGER",
            "order_hour_of_day": "INTEGER",
            "days_since_prior_order": "FLOAT",
        },
        description="Core order table with user, timing, and sequence information",
    ),
    "order_products_prior": TableSchema(
        name="order_products_prior",
        file_name="order_products__prior.csv",
        primary_key="order_id,product_id",
        columns={
            "order_id": "INTEGER",
            "product_id": "INTEGER",
            "add_to_cart_order": "INTEGER",
            "reordered": "INTEGER",
        },
        description="Products in prior orders (largest table: ~32M rows)",
    ),
    "order_products_train": TableSchema(
        name="order_products_train",
        file_name="order_products__train.csv",
        primary_key="order_id,product_id",
        columns={
            "order_id": "INTEGER",
            "product_id": "INTEGER",
            "add_to_cart_order": "INTEGER",
            "reordered": "INTEGER",
        },
        description="Products in training set orders (~1.4M rows)",
    ),
    "products": TableSchema(
        name="products",
        file_name="products.csv",
        primary_key="product_id",
        columns={
            "product_id": "INTEGER",
            "product_name": "VARCHAR",
            "aisle_id": "INTEGER",
            "department_id": "INTEGER",
        },
        description="Product catalog with hierarchy (product -> aisle -> department)",
    ),
    "aisles": TableSchema(
        name="aisles",
        file_name="aisles.csv",
        primary_key="aisle_id",
        columns={
            "aisle_id": "INTEGER",
            "aisle": "VARCHAR",
        },
        description="Aisle lookup table (134 aisles)",
    ),
    "departments": TableSchema(
        name="departments",
        file_name="departments.csv",
        primary_key="department_id",
        columns={
            "department_id": "INTEGER",
            "department": "VARCHAR",
        },
        description="Department lookup table (21 departments)",
    ),
}

# Define relationships
RELATIONSHIPS = [
    # Order products to orders
    Relationship("order_products_prior", "order_id", "orders", "order_id"),
    Relationship("order_products_train", "order_id", "orders", "order_id"),
    # Order products to products
    Relationship("order_products_prior", "product_id", "products", "product_id"),
    Relationship("order_products_train", "product_id", "products", "product_id"),
    # Products to aisles
    Relationship("products", "aisle_id", "aisles", "aisle_id"),
    # Products to departments
    Relationship("products", "department_id", "departments", "department_id"),
]


def get_schema_description() -> str:
    """Generate a human-readable schema description for LLM context."""

    schema_desc = "DATABASE SCHEMA:\n\n"

    for table_name, table in TABLES.items():
        schema_desc += f"Table: {table.name}\n"
        schema_desc += f"Description: {table.description}\n"
        schema_desc += "Columns:\n"
        for col_name, col_type in table.columns.items():
            schema_desc += f"  - {col_name} ({col_type})\n"
        schema_desc += f"Primary Key: {table.primary_key}\n\n"

    schema_desc += "\nRELATIONSHIPS:\n"
    for rel in RELATIONSHIPS:
        schema_desc += f"  - {rel.from_table}.{rel.from_column} -> {rel.to_table}.{rel.to_column}\n"

    schema_desc += """
IMPORTANT NOTES:
1. order_products data is split into 'prior' and 'train' sets based on orders.eval_set
2. For most BI queries, use UNION of both order_products tables or just prior (larger set)
3. days_since_prior_order is NULL for first orders
4. reordered flag: 1 = product was ordered before by this user, 0 = first time
5. add_to_cart_order indicates the sequence products were added (1 = first)
6. order_dow: day of week (0-6 INTEGER), order_hour_of_day: hour (0-23 INTEGER)
7. Product hierarchy: product -> aisle -> department (requires joins through products table)

CRITICAL LIMITATIONS - NO DATE/TIME DATA:
⚠️ This dataset contains NO actual dates, timestamps, or temporal ordering beyond sequence numbers
⚠️ order_hour_of_day and order_dow are INTEGERS (0-23 and 0-6), NOT date/time types
⚠️ NEVER use: DATE_TRUNC, CURRENT_DATE, INTERVAL, TIMESTAMP, DATE functions
⚠️ CANNOT analyze: monthly trends, seasonal patterns, time-series, date ranges
⚠️ For "trending" products: Use reorder rate (AVG(reordered)) or total order count
⚠️ For "popular" analysis: Use aggregation counts, NOT time-based growth
"""

    return schema_desc


def get_example_queries() -> List[Dict[str, str]]:
    """Provide example queries for few-shot learning."""

    return [
        {
            "question": "What are the top 10 most ordered products?",
            "sql": """
SELECT
    p.product_name,
    COUNT(*) as order_count
FROM order_products_prior op
JOIN products p ON op.product_id = p.product_id
GROUP BY p.product_name
ORDER BY order_count DESC
LIMIT 10
""",
            "reasoning": "Simple aggregation with one join. Use prior table (larger set). Join to products for names.",
        },
        {
            "question": "Which department has the highest reorder rate?",
            "sql": """
SELECT
    d.department,
    AVG(op.reordered) as reorder_rate,
    COUNT(*) as total_orders
FROM order_products_prior op
JOIN products p ON op.product_id = p.product_id
JOIN departments d ON p.department_id = d.department_id
GROUP BY d.department
ORDER BY reorder_rate DESC
LIMIT 1
""",
            "reasoning": "Multi-table join through product hierarchy. Reorder rate = AVG(reordered flag).",
        },
        {
            "question": "Show orders by hour of day",
            "sql": """
SELECT
    order_hour_of_day as hour,
    COUNT(*) as order_count
FROM orders
GROUP BY order_hour_of_day
ORDER BY order_hour_of_day
""",
            "reasoning": "Simple aggregation on orders table. No joins needed. Results in time-series format.",
        },
        {
            "question": "What's the average basket size per order?",
            "sql": """
SELECT
    AVG(basket_size) as avg_basket_size
FROM (
    SELECT order_id, COUNT(*) as basket_size
    FROM order_products_prior
    GROUP BY order_id
)
""",
            "reasoning": "Requires subquery: first count products per order, then average those counts.",
        },
        {
            "question": "What are the trending products?",
            "sql": """
SELECT
    p.product_name,
    COUNT(*) as total_orders,
    AVG(op.reordered) as reorder_rate
FROM order_products_prior op
JOIN products p ON op.product_id = p.product_id
GROUP BY p.product_name
HAVING COUNT(*) > 1000
ORDER BY reorder_rate DESC, total_orders DESC
LIMIT 10
""",
            "reasoning": "For 'trending', use reorder rate as proxy. GROUP BY aggregates 32M rows efficiently.",
        },
        {
            "question": "Show me the distribution of basket positions for all products",
            "sql": """
SELECT
    add_to_cart_order as basket_position,
    COUNT(*) as product_count,
    AVG(reordered) as avg_reorder_rate
FROM order_products_prior
WHERE add_to_cart_order <= 20
GROUP BY add_to_cart_order
ORDER BY add_to_cart_order
""",
            "reasoning": "Efficiently handles 32M rows: WHERE filters early, GROUP BY aggregates, result is small (~20 rows). No timeout risk.",
        },
    ]
