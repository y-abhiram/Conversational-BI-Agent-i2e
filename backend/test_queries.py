"""
Test script to validate the Conversational BI Agent with complex queries.

This demonstrates the system's capabilities across different query types.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from database.duckdb_manager import DuckDBManager
from agents.query_agent import QueryAgent
from agents.chart_agent import ChartAgent
import os
from dotenv import load_dotenv

load_dotenv()


TEST_QUERIES = [
    {
        "category": "Simple Aggregation",
        "questions": [
            "What are the top 10 most ordered products?",
            "How many total orders are there?",
            "What's the average number of products per order?",
        ],
    },
    {
        "category": "Multi-table Joins",
        "questions": [
            "Which department has the most orders?",
            "Show me the top 5 aisles by order count",
            "What are the most popular products in the produce department?",
        ],
    },
    {
        "category": "Temporal Analysis",
        "questions": [
            "Show order distribution by hour of day",
            "Which day of the week has the most orders?",
            "What's the average time between orders?",
        ],
    },
    {
        "category": "Reorder Behavior",
        "questions": [
            "Which products have the highest reorder rate?",
            "What percentage of items in orders are reorders?",
            "Which aisle has the highest reorder rate?",
        ],
    },
    {
        "category": "Complex Multi-step",
        "questions": [
            "Show me which departments have both high order volume and high reorder rate",
            "What's the correlation between basket position and reorder rate?",
            "Which products are most commonly added to cart first?",
        ],
    },
]


async def run_query_test(db_manager, query_agent, chart_agent, question):
    """Run a single query test."""
    print(f"\n  Question: {question}")
    print("  " + "-" * 70)

    try:
        # Generate SQL
        sql_gen = query_agent.generate_sql(question)

        print(f"  Reasoning: {sql_gen.reasoning[:100]}...")
        print(f"  Complexity: {sql_gen.complexity}")
        print(f"  Tables: {', '.join(sql_gen.tables_needed)}")

        # Validate SQL
        is_valid, error = db_manager.validate_sql(sql_gen.sql_query)

        if not is_valid:
            print(f"  ❌ VALIDATION FAILED: {error}")

            # Try to fix
            print("  Attempting to fix SQL...")
            fixed_sql = query_agent.validate_and_fix_sql(
                sql_gen.sql_query, error, question
            )

            is_valid, error = db_manager.validate_sql(fixed_sql)
            if is_valid:
                print("  ✓ SQL fixed successfully")
                sql_gen.sql_query = fixed_sql
            else:
                print(f"  ❌ STILL INVALID: {error}")
                return False

        # Execute query
        result = db_manager.execute_query(sql_gen.sql_query)

        print(f"  ✓ Query executed: {result['row_count']} rows in {result['execution_time_ms']:.2f}ms")

        # Select chart
        chart = chart_agent.select_chart(
            question,
            result['columns'],
            result['data'],
            sql_gen.expected_chart_type
        )

        print(f"  Chart type: {chart.type}")

        # Show sample data
        if result['data']:
            print(f"  Sample: {result['data'][0]}")

        return True

    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        return False


async def main():
    """Run all test queries."""
    print("="*80)
    print("CONVERSATIONAL BI AGENT - TEST SUITE")
    print("="*80)

    # Initialize components
    print("\nInitializing system...")
    db_manager = DuckDBManager(data_dir="./data")
    db_manager.connect()

    print("Loading dataset...")
    stats = db_manager.load_data()
    print(f"Loaded: {stats}")

    query_agent = QueryAgent(
        model_name=os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"),
        temperature=0.1
    )
    chart_agent = ChartAgent()

    # Run tests
    total_tests = 0
    passed_tests = 0

    for category_data in TEST_QUERIES:
        category = category_data["category"]
        questions = category_data["questions"]

        print(f"\n{'='*80}")
        print(f"CATEGORY: {category}")
        print(f"{'='*80}")

        for question in questions:
            total_tests += 1
            success = await run_query_test(db_manager, query_agent, chart_agent, question)

            if success:
                passed_tests += 1

    # Summary
    print(f"\n{'='*80}")
    print(f"TEST SUMMARY")
    print(f"{'='*80}")
    print(f"Total: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

    db_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
