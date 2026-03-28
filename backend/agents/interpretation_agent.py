"""Natural language interpretation agent for query results."""

import logging
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


class InterpretationAgent:
    """Generates natural language interpretations of query results."""

    def __init__(
        self,
        model_name: str = "gpt-4o",
        temperature: float = 0.3,
    ):
        """
        Initialize interpretation agent.

        Args:
            model_name: OpenAI model to use
            temperature: Sampling temperature (higher = more creative)
        """
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
        )

    def generate_interpretation(
        self,
        question: str,
        data: List[Dict[str, Any]],
        columns: List[str],
        chart_type: str = None,
    ) -> str:
        """
        Generate a natural language interpretation of query results.

        Args:
            question: Original question asked
            data: Query result data
            columns: Column names
            chart_type: Type of chart being displayed (optional)

        Returns:
            Natural language interpretation explaining the results
        """
        logger.info(f"Generating interpretation for: {question}")

        if not data:
            return "No results were found for this query."

        # Build context from data
        row_count = len(data)
        sample_data = data[:5]  # First 5 rows for context

        # Extract key insights
        insights = self._extract_insights(data, columns)

        prompt = [
            SystemMessage(content="""You are a data analyst explaining query results to business users.

Your task is to provide a clear, concise interpretation of the data in simple English.

GUIDELINES:
1. Explain what the data shows in 2-4 sentences
2. Highlight the most important insights (highest/lowest values, trends, correlations)
3. Use simple business language, avoid technical jargon
4. Be specific with numbers and percentages
5. If it's a multi-dimensional analysis, explain relationships between dimensions
6. Keep it conversational and easy to understand

Example:
Question: "Show me which aisles have the highest reorder rate"
Interpretation: "The data shows that fresh herbs has the highest reorder rate at 72%, meaning customers frequently reorder items from this aisle. This is followed by packaged cheese (68%) and vitamins supplements (65%). These high reorder rates suggest strong customer loyalty and repeat purchase behavior for these product categories."
"""),
            HumanMessage(content=f"""Question: {question}

Columns: {', '.join(columns)}
Total rows: {row_count}

Sample data (first 5 rows):
{self._format_sample_data(sample_data, columns)}

Key insights:
{insights}

Provide a natural language interpretation of these results in 2-4 sentences, explaining what the data reveals."""),
        ]

        try:
            response = self.llm.invoke(prompt)
            interpretation = response.content.strip()
            logger.info(f"Generated interpretation: {interpretation[:100]}...")
            return interpretation

        except Exception as e:
            logger.error(f"Failed to generate interpretation: {e}")
            return "The data has been retrieved successfully. Please review the visualization for insights."

    def _extract_insights(self, data: List[Dict[str, Any]], columns: List[str]) -> str:
        """Extract key statistical insights from data."""
        if not data:
            return "No data available"

        insights = []

        # Find numeric columns
        sample = data[0]
        numeric_cols = [
            col for col in columns
            if isinstance(sample.get(col), (int, float))
        ]

        # Get top and bottom values for numeric columns
        for col in numeric_cols[:2]:  # Limit to first 2 numeric columns
            values = [(row.get(col, 0), row) for row in data]
            values.sort(key=lambda x: x[0], reverse=True)

            if values:
                top_val, top_row = values[0]
                bottom_val, bottom_row = values[-1]

                # Find the label column (first string column)
                label_col = next(
                    (c for c in columns if isinstance(top_row.get(c), str)),
                    columns[0]
                )

                insights.append(
                    f"- Highest {col}: {top_val} ({top_row.get(label_col)})"
                )
                insights.append(
                    f"- Lowest {col}: {bottom_val} ({bottom_row.get(label_col)})"
                )

        return "\n".join(insights) if insights else "Data shows various metrics across categories"

    def _format_sample_data(
        self, data: List[Dict[str, Any]], columns: List[str]
    ) -> str:
        """Format sample data for the prompt."""
        if not data:
            return "No data"

        lines = []
        for i, row in enumerate(data, 1):
            row_str = ", ".join([f"{col}: {row.get(col)}" for col in columns])
            lines.append(f"  Row {i}: {row_str}")

        return "\n".join(lines)
