"""LLM-powered SQL query generation agent with chain-of-thought reasoning."""

import logging
from typing import Dict, Any, Optional, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from database.schema import get_schema_description, get_example_queries

logger = logging.getLogger(__name__)


class ClarificationNeeded(Exception):
    """Raised when LLM needs clarification from the user."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class SQLGeneration(BaseModel):
    """Structured output for SQL generation."""

    reasoning: str = Field(description="Step-by-step reasoning about how to answer the question")
    tables_needed: List[str] = Field(description="List of tables required for this query")
    complexity: str = Field(description="Query complexity: simple, medium, or complex")
    sql_query: str = Field(description="The generated SQL query")
    expected_chart_type: str = Field(
        description="Suggested chart type: bar, line, pie, scatter, table, or number"
    )


class QueryAgent:
    """Agent that converts natural language to SQL using LLM with reasoning."""

    def __init__(
        self,
        model_name: str = "gpt-4-turbo-preview",
        temperature: float = 0.1,
    ):
        """
        Initialize query agent.

        Args:
            model_name: OpenAI model to use
            temperature: Sampling temperature (lower = more deterministic)
        """
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
        )
        self.schema_description = get_schema_description()
        self.example_queries = get_example_queries()
        self.parser = PydanticOutputParser(pydantic_object=SQLGeneration)

    def generate_sql(
        self,
        question: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> SQLGeneration:
        """
        Generate SQL query from natural language question.

        Args:
            question: Natural language question
            conversation_history: Previous exchanges for context

        Returns:
            SQLGeneration object with reasoning and SQL
        """
        logger.info(f"Generating SQL for question: {question}")

        # Build prompt with schema, examples, and question
        prompt = self._build_prompt(question, conversation_history)

        try:
            # Get response from LLM
            response = self.llm.invoke(prompt)

            # Parse structured output
            result = self._parse_response(response.content)

            logger.info(f"Generated SQL: {result.sql_query}")
            logger.info(f"Complexity: {result.complexity}")

            return result

        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            raise

    def _build_prompt(
        self,
        question: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> List[Any]:
        """Build the prompt with schema context and examples."""

        messages = [
            SystemMessage(content=f"""You are an expert SQL query generator for a Business Intelligence system.

{self.schema_description}

Your task is to convert natural language questions into SQL queries for DuckDB.

CRITICAL RULES:
1. ALWAYS use chain-of-thought reasoning BEFORE writing SQL
2. Identify which tables are needed and why
3. For product-related queries, JOIN through the hierarchy: order_products -> products -> aisles/departments
4. Use UNION ALL for combining prior and train sets when analyzing all orders
5. Handle NULL values in days_since_prior_order (first orders)
6. For reorder rate, use AVG(reordered) since it's a 0/1 flag
7. Return queries that are efficient (use LIMIT for large results, use WHERE before JOIN)
8. Suggest appropriate chart type based on data shape
9. ⚠️ NEVER use date/time functions - this dataset has NO dates, only integer hour/day values
10. For "trending" questions, use reorder counts or popularity (order frequency), NOT time-based trends
11. ⚠️ SCALE OPTIMIZATION: order_products_prior has 32M rows - ALWAYS use aggregations/GROUP BY before final LIMIT
12. For large table queries: filter early, aggregate in subqueries, use LIMIT wisely to avoid timeouts

RESPONSE FORMAT (JSON):
{self.parser.get_format_instructions()}

Think step by step:
1. What is being asked?
2. Which tables contain the needed data?
3. What joins are required?
4. What aggregations or filters are needed?
5. What's the best chart to visualize this?

EXAMPLES:
""")
        ]

        # Add few-shot examples
        for example in self.example_queries:
            messages.append(
                HumanMessage(content=f"Question: {example['question']}")
            )
            messages.append(
                AIMessage(content=f"""{{
  "reasoning": "{example['reasoning']}",
  "tables_needed": ["(inferred from SQL)"],
  "complexity": "medium",
  "sql_query": "{example['sql'].strip()}",
  "expected_chart_type": "bar"
}}""")
            )

        # Add conversation history if exists
        if conversation_history:
            messages.append(
                SystemMessage(content="\nPREVIOUS CONVERSATION CONTEXT:")
            )
            for exchange in conversation_history[-3:]:  # Last 3 exchanges
                messages.append(HumanMessage(content=exchange.get("question", "")))
                if "sql" in exchange:
                    messages.append(
                        AIMessage(content=f"Generated SQL: {exchange['sql']}")
                    )

        # Add current question
        messages.append(HumanMessage(content=f"Question: {question}"))

        return messages

    def _parse_response(self, response: str) -> SQLGeneration:
        """Parse LLM response into structured output."""
        try:
            # Try to parse as JSON
            result = self.parser.parse(response)
            return result
        except Exception as e:
            logger.warning(f"Failed to parse structured output: {e}")

            # Fallback: extract SQL manually
            sql = self._extract_sql_fallback(response)

            return SQLGeneration(
                reasoning="Failed to generate structured reasoning",
                tables_needed=["unknown"],
                complexity="medium",
                sql_query=sql,
                expected_chart_type="table",
            )

    def _extract_sql_fallback(self, response: str) -> str:
        """Extract SQL from unstructured response."""
        # Check if LLM is asking for clarification or refusing to answer
        clarification_phrases = ["sorry", "cannot", "don't have", "not include", "doesn't exist", "unavailable", "need more", "could you", "please provide", "please specify"]
        if any(phrase in response.lower() for phrase in clarification_phrases):
            # LLM needs clarification - extract clean message
            raise ClarificationNeeded(response.strip())

        # Look for SQL in code blocks
        if "```sql" in response:
            start = response.find("```sql") + 6
            end = response.find("```", start)
            return response[start:end].strip()
        elif "SELECT" in response.upper():
            # Find the SELECT statement
            start = response.upper().find("SELECT")
            return response[start:].strip()
        else:
            raise ValueError("Could not extract SQL from response")

    def validate_and_fix_sql(
        self,
        sql: str,
        error_message: str,
        original_question: str,
    ) -> str:
        """
        Attempt to fix a failing SQL query.

        Args:
            sql: The failing SQL query
            error_message: Error from database
            original_question: Original question

        Returns:
            Fixed SQL query
        """
        logger.info("Attempting to fix SQL query")

        prompt = [
            SystemMessage(content=f"""You are debugging a SQL query that failed.

{self.schema_description}

ORIGINAL QUESTION: {original_question}

FAILED SQL:
{sql}

ERROR MESSAGE:
{error_message}

Analyze the error and provide a CORRECTED SQL query. Common issues:
- Table names or column names misspelled
- Missing JOIN conditions
- Invalid aggregation
- Syntax errors

Respond with ONLY the corrected SQL query, no explanation."""),
        ]

        try:
            response = self.llm.invoke(prompt)
            fixed_sql = response.content.strip()

            # Clean up response
            if "```sql" in fixed_sql:
                start = fixed_sql.find("```sql") + 6
                end = fixed_sql.find("```", start)
                fixed_sql = fixed_sql[start:end].strip()

            logger.info(f"Generated fixed SQL: {fixed_sql}")
            return fixed_sql

        except Exception as e:
            logger.error(f"Failed to fix SQL: {e}")
            raise


class ConversationMemory:
    """Manages conversation history for context."""

    def __init__(self, max_exchanges: int = 5):
        """
        Initialize conversation memory.

        Args:
            max_exchanges: Maximum number of exchanges to remember
        """
        self.max_exchanges = max_exchanges
        self.conversations: Dict[str, List[Dict[str, Any]]] = {}

    def add_exchange(
        self,
        conversation_id: str,
        question: str,
        sql: str,
        result_summary: str,
    ) -> None:
        """Add an exchange to conversation history."""
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []

        self.conversations[conversation_id].append({
            "question": question,
            "sql": sql,
            "result_summary": result_summary,
        })

        # Keep only last N exchanges
        if len(self.conversations[conversation_id]) > self.max_exchanges:
            self.conversations[conversation_id] = self.conversations[conversation_id][
                -self.max_exchanges:
            ]

    def get_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get conversation history."""
        return self.conversations.get(conversation_id, [])

    def clear(self, conversation_id: str) -> None:
        """Clear conversation history."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
