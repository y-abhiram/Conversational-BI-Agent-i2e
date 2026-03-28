"""Pydantic models for request/response validation."""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class QueryRequest(BaseModel):
    """Request model for natural language queries."""

    question: str = Field(..., min_length=1, description="Natural language question")
    conversation_id: Optional[str] = Field(None, description="ID for conversation continuity")
    include_explanation: bool = Field(True, description="Include SQL and reasoning")


class ChartConfig(BaseModel):
    """Configuration for chart rendering."""

    type: Literal["bar", "line", "pie", "scatter", "table", "number", "heatmap", "grouped_bar"] = Field(
        ..., description="Chart type"
    )
    x_axis: Optional[str] = Field(None, description="X-axis column")
    y_axis: Optional[str] = Field(None, description="Y-axis column")
    group_by: Optional[str] = Field(None, description="Grouping column for grouped/multi-series charts")
    title: str = Field(..., description="Chart title")
    x_label: Optional[str] = Field(None, description="X-axis label")
    y_label: Optional[str] = Field(None, description="Y-axis label")
    interpretation: Optional[str] = Field(None, description="Natural language interpretation of the results")


class DashboardLayout(BaseModel):
    """Configuration for multi-chart dashboard layout."""

    charts: List[ChartConfig] = Field(..., description="List of charts to display")
    title: str = Field(..., description="Dashboard title")
    layout: Literal["grid", "vertical", "horizontal"] = Field("grid", description="Layout style")
    interpretation: Optional[str] = Field(None, description="Natural language interpretation of the results")


class QueryResult(BaseModel):
    """Result of a query execution."""

    data: List[Dict[str, Any]] = Field(..., description="Query result data")
    row_count: int = Field(..., description="Number of rows returned")
    columns: List[str] = Field(..., description="Column names")
    execution_time_ms: float = Field(..., description="Query execution time in milliseconds")


class QueryExplanation(BaseModel):
    """Explanation of query processing."""

    reasoning: str = Field(..., description="Chain-of-thought reasoning")
    sql_query: str = Field(..., description="Generated SQL query")
    tables_used: List[str] = Field(..., description="Tables involved")
    complexity: Literal["simple", "medium", "complex"] = Field(
        ..., description="Query complexity level"
    )


class QueryResponse(BaseModel):
    """Complete response for a query."""

    success: bool = Field(..., description="Whether query succeeded")
    result: Optional[QueryResult] = Field(None, description="Query results")
    chart: Optional[ChartConfig] = Field(None, description="Single chart configuration")
    dashboard: Optional[DashboardLayout] = Field(None, description="Dashboard with multiple charts")
    explanation: Optional[QueryExplanation] = Field(None, description="Query explanation")
    error: Optional[str] = Field(None, description="Error message if failed")
    conversation_id: str = Field(..., description="Conversation ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SchemaInfo(BaseModel):
    """Database schema information."""

    table_name: str
    columns: List[Dict[str, str]]  # [{"name": "col1", "type": "INTEGER"}, ...]
    row_count: int
    sample_data: List[Dict[str, Any]]


class HealthResponse(BaseModel):
    """Health check response."""

    status: Literal["healthy", "unhealthy"]
    database_loaded: bool
    tables_count: int
    total_rows: int
    version: str = "1.0.0"


class StreamEvent(BaseModel):
    """Server-sent event for streaming responses."""

    event: Literal["thinking", "querying", "visualizing", "complete", "error", "clarification"]
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
