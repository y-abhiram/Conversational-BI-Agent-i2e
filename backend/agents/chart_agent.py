"""Intelligent chart selection agent."""

import logging
from typing import List, Dict, Any, Optional, Union
from models.schemas import ChartConfig, DashboardLayout
from agents.interpretation_agent import InterpretationAgent

logger = logging.getLogger(__name__)


class ChartAgent:
    """Selects appropriate chart type based on query results and question."""

    def __init__(self):
        """Initialize chart agent with interpretation capability."""
        self.interpretation_agent = InterpretationAgent()

    def select_visualization(
        self,
        question: str,
        columns: List[str],
        data: List[Dict[str, Any]],
        suggested_type: str = "table",
    ) -> Union[ChartConfig, DashboardLayout]:
        """
        Select appropriate visualization (single chart or dashboard).

        Args:
            question: Original question
            columns: Column names in result
            data: Query result data
            suggested_type: LLM's suggested chart type

        Returns:
            ChartConfig for simple queries or DashboardLayout for complex multi-dimensional queries
        """
        # Check if this is a multi-dimensional query that needs a dashboard
        if self._is_multi_dimensional(question, columns, data):
            return self._create_dashboard(question, columns, data)
        else:
            return self.select_chart(question, columns, data, suggested_type)

    def select_chart(
        self,
        question: str,
        columns: List[str],
        data: List[Dict[str, Any]],
        suggested_type: str = "table",
    ) -> ChartConfig:
        """
        Select appropriate chart type and configuration.

        Args:
            question: Original question
            columns: Column names in result
            data: Query result data
            suggested_type: LLM's suggested chart type

        Returns:
            ChartConfig with type and axis configuration
        """
        if not data or not columns:
            return self._create_empty_chart(question)

        # Single value result
        if len(data) == 1 and len(columns) == 1:
            return self._create_number_chart(question, columns[0], data[0])

        # Two columns: likely x/y relationship
        if len(columns) == 2:
            return self._create_two_column_chart(
                question, columns, data, suggested_type
            )

        # Multiple columns: table or complex chart
        if len(columns) > 2:
            return self._create_multi_column_chart(
                question, columns, data, suggested_type
            )

        # Default: table view
        return ChartConfig(
            type="table",
            title=self._generate_title(question),
        )

    def _create_empty_chart(self, question: str) -> ChartConfig:
        """Create config for empty results."""
        return ChartConfig(
            type="table",
            title=f"No results found for: {question}",
        )

    def _create_number_chart(
        self, question: str, column: str, data: Dict[str, Any]
    ) -> ChartConfig:
        """Create config for single number result."""
        return ChartConfig(
            type="number",
            title=self._generate_title(question),
            y_axis=column,
        )

    def _create_two_column_chart(
        self,
        question: str,
        columns: List[str],
        data: List[Dict[str, Any]],
        suggested_type: str,
    ) -> ChartConfig:
        """Create config for two-column results."""
        x_col, y_col = columns[0], columns[1]

        # Determine chart type based on data characteristics
        chart_type = self._determine_chart_type(
            x_col, y_col, data, suggested_type
        )

        # Generate interpretation for this chart
        interpretation = self.interpretation_agent.generate_interpretation(
            question=question,
            data=data,
            columns=columns,
            chart_type=chart_type
        )

        return ChartConfig(
            type=chart_type,
            x_axis=x_col,
            y_axis=y_col,
            title=self._generate_title(question),
            x_label=self._format_label(x_col),
            y_label=self._format_label(y_col),
            interpretation=interpretation,
        )

    def _create_multi_column_chart(
        self,
        question: str,
        columns: List[str],
        data: List[Dict[str, Any]],
        suggested_type: str,
    ) -> ChartConfig:
        """Create config for multi-column results."""
        # For 3+ columns, use table unless specifically suggested otherwise
        if suggested_type in ["bar", "line", "scatter"] and len(columns) <= 4:
            # Use first column as x, second as y
            return ChartConfig(
                type=suggested_type,
                x_axis=columns[0],
                y_axis=columns[1],
                title=self._generate_title(question),
                x_label=self._format_label(columns[0]),
                y_label=self._format_label(columns[1]),
            )

        return ChartConfig(
            type="table",
            title=self._generate_title(question),
        )

    def _determine_chart_type(
        self,
        x_col: str,
        y_col: str,
        data: List[Dict[str, Any]],
        suggested_type: str,
    ) -> str:
        """
        Determine best chart type based on data characteristics.

        Logic:
        - Time series (hour, day, sequential numbers) -> line chart
        - Proportions/percentages/rates (< 10 items) -> pie chart
        - Categories with counts -> bar chart (horizontal if many items)
        - Two numeric columns -> scatter plot
        - Distribution/frequency -> histogram/line
        """
        if not data:
            return "bar"

        # Check for time-related or sequential columns
        time_keywords = ["hour", "day", "date", "time", "week", "month", "year", "dow"]
        is_time_series = any(keyword in x_col.lower() for keyword in time_keywords)

        # Check data types
        sample_x = data[0][x_col] if data else None
        sample_y = data[0][y_col] if data else None

        x_is_string = isinstance(sample_x, str)
        x_is_numeric = isinstance(sample_x, (int, float))
        y_is_numeric = isinstance(sample_y, (int, float))

        # Both numeric -> check if it's a scatter plot first
        # If y-axis has aggregated metrics (avg, sum, count), prefer scatter
        scatter_y_keywords = ["avg", "average", "mean", "sum", "total", "size"]
        is_scatter_metric = any(keyword in y_col.lower() for keyword in scatter_y_keywords)

        # Time series with simple counts -> line chart
        if is_time_series and y_is_numeric and not is_scatter_metric:
            return "line"

        # Sequential numeric x-axis (like hours 0-23) -> check if scatter is better
        if x_is_numeric and y_is_numeric and len(data) > 5:
            # Check if x values are sequential
            x_values = sorted([row[x_col] for row in data])
            is_sequential = all(
                x_values[i+1] - x_values[i] == 1
                for i in range(len(x_values)-1)
            ) if len(x_values) > 1 else False

            # If it's showing relationship between two metrics, use scatter
            if is_sequential and is_scatter_metric:
                return "scatter"
            elif is_sequential:
                return "line"

        # Percentage/rate/ratio columns -> pie chart (for few categories)
        rate_keywords = ["rate", "percent", "ratio", "share", "proportion"]
        is_percentage = any(keyword in y_col.lower() for keyword in rate_keywords)

        if x_is_string and y_is_numeric and is_percentage and len(data) <= 10:
            return "pie"

        # Categorical with numeric -> bar chart
        if x_is_string and y_is_numeric:
            return "bar"

        # Both numeric -> scatter plot
        if x_is_numeric and y_is_numeric:
            # Unless it's a clear distribution/frequency
            if "count" in y_col.lower() or "frequency" in y_col.lower():
                return "bar"
            return "scatter"

        # Respect LLM suggestion if it makes sense
        if suggested_type in ["bar", "line", "pie", "scatter"]:
            return suggested_type

        # Default to bar chart
        return "bar"

    def _generate_title(self, question: str) -> str:
        """Generate chart title from question."""
        # Capitalize first letter, ensure it's not too long
        title = question.strip()
        if len(title) > 80:
            title = title[:77] + "..."

        return title[0].upper() + title[1:] if title else "Query Result"

    def _format_label(self, column_name: str) -> str:
        """Format column name into readable label."""
        # Replace underscores with spaces and title case
        label = column_name.replace("_", " ").title()
        return label

    def _is_multi_dimensional(
        self,
        question: str,
        columns: List[str],
        data: List[Dict[str, Any]],
    ) -> bool:
        """
        Detect if query results are multi-dimensional requiring dashboard.

        Indicators:
        - Multiple metrics (2+ numeric columns) showing correlations
        - Keywords like "correlate", "relationship", "compare"
        - Breakdown queries with multiple dimensions
        """
        if not data or len(columns) < 3:
            return False

        # Exclude simple "list all" or "show all" queries
        simple_list_keywords = ["list all", "show all", "all products", "all orders", "all departments"]
        if any(keyword in question.lower() for keyword in simple_list_keywords):
            return False

        # Check if we have multiple numeric columns (metrics)
        sample = data[0]
        numeric_cols = [
            col for col in columns
            if isinstance(sample.get(col), (int, float)) and col.lower() not in ['id', 'count']
        ]
        categorical_cols = [col for col in columns if isinstance(sample.get(col), str)]

        # Multi-metric correlation queries (like "correlate X with Y")
        correlation_keywords = [
            "correlate", "correlation", "relationship", "compare", "vs",
            "versus", "how that correlates", "and how"
        ]
        has_correlation = any(keyword in question.lower() for keyword in correlation_keywords)

        # Multi-dimensional breakdown queries
        breakdown_keywords = [
            "breakdown", "broken down", "across",
            "by day of week", "by hour", "by department and", "by aisle and"
        ]
        has_breakdown = any(keyword in question.lower() for keyword in breakdown_keywords)

        # Trigger dashboard if:
        # 1. Multiple metrics (2+) with correlation intent
        # 2. OR breakdown query with 2+ categorical dimensions AND 2+ metrics
        return (has_correlation and len(numeric_cols) >= 2) or \
               (has_breakdown and len(numeric_cols) >= 2 and len(categorical_cols) >= 2)

    def _create_dashboard(
        self,
        question: str,
        columns: List[str],
        data: List[Dict[str, Any]],
    ) -> DashboardLayout:
        """
        Create a dashboard with multiple complementary visualizations.

        For complex queries, create:
        1. Summary/KPI chart (top metrics)
        2. Detailed breakdown chart
        3. Heatmap for 2D categorical data
        """
        charts = []

        # Identify column types
        sample = data[0]
        categorical_cols = [col for col in columns if isinstance(sample.get(col), str)]
        numeric_cols = [
            col for col in columns
            if isinstance(sample.get(col), (int, float)) and col.lower() not in ['id']
        ]

        # Chart 1: Main metric bar chart (first categorical × first numeric)
        if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
            main_cat = categorical_cols[0]
            main_metric = numeric_cols[0]

            charts.append(ChartConfig(
                type="bar",
                x_axis=main_cat,
                y_axis=main_metric,
                title=f"{self._format_label(main_metric)} by {self._format_label(main_cat)}",
                x_label=self._format_label(main_cat),
                y_label=self._format_label(main_metric),
            ))

        # Chart 2: Grouped bar chart if we have 2 categorical dimensions
        if len(categorical_cols) >= 2 and len(numeric_cols) >= 1:
            charts.append(ChartConfig(
                type="grouped_bar",
                x_axis=categorical_cols[0],
                y_axis=numeric_cols[0],
                group_by=categorical_cols[1],
                title=f"{self._format_label(numeric_cols[0])} by {self._format_label(categorical_cols[0])} and {self._format_label(categorical_cols[1])}",
                x_label=self._format_label(categorical_cols[0]),
                y_label=self._format_label(numeric_cols[0]),
            ))

        # Chart 3: Heatmap for 2D categorical data
        if len(categorical_cols) >= 2 and len(numeric_cols) >= 1:
            charts.append(ChartConfig(
                type="heatmap",
                x_axis=categorical_cols[1],
                y_axis=categorical_cols[0],
                group_by=numeric_cols[0],  # Use as intensity
                title=f"Heatmap: {self._format_label(numeric_cols[0])}",
                x_label=self._format_label(categorical_cols[1]),
                y_label=self._format_label(categorical_cols[0]),
            ))

        # Chart 4: Secondary metric if available
        if len(numeric_cols) >= 2:
            # If only one categorical dimension, show second metric
            if len(categorical_cols) == 1:
                charts.append(ChartConfig(
                    type="bar",
                    x_axis=categorical_cols[0],
                    y_axis=numeric_cols[1],
                    title=f"{self._format_label(numeric_cols[1])} by {self._format_label(categorical_cols[0])}",
                    x_label=self._format_label(categorical_cols[0]),
                    y_label=self._format_label(numeric_cols[1]),
                ))

                # Add correlation scatter plot showing relationship between two metrics
                charts.append(ChartConfig(
                    type="scatter",
                    x_axis=numeric_cols[0],
                    y_axis=numeric_cols[1],
                    title=f"Correlation: {self._format_label(numeric_cols[0])} vs {self._format_label(numeric_cols[1])}",
                    x_label=self._format_label(numeric_cols[0]),
                    y_label=self._format_label(numeric_cols[1]),
                ))
            else:
                # Multi-dimensional case: just show the second metric trend
                charts.append(ChartConfig(
                    type="bar",
                    x_axis=categorical_cols[0],
                    y_axis=numeric_cols[1],
                    title=f"{self._format_label(numeric_cols[1])} by {self._format_label(categorical_cols[0])}",
                    x_label=self._format_label(categorical_cols[0]),
                    y_label=self._format_label(numeric_cols[1]),
                ))

        # Fallback: if no charts created, make a table
        if not charts:
            charts.append(ChartConfig(
                type="table",
                title=self._generate_title(question),
            ))

        # Generate natural language interpretation
        interpretation = self.interpretation_agent.generate_interpretation(
            question=question,
            data=data,
            columns=columns,
            chart_type="dashboard"
        )

        return DashboardLayout(
            charts=charts,
            title=self._generate_title(question),
            layout="grid",
            interpretation=interpretation,
        )
