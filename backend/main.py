"""FastAPI main application for Conversational BI Agent."""

import logging
import os
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import json

from dotenv import load_dotenv

from database.duckdb_manager import DuckDBManager
from agents.query_agent import QueryAgent, ConversationMemory, ClarificationNeeded
from agents.chart_agent import ChartAgent
from models.schemas import (
    QueryRequest,
    QueryResponse,
    QueryResult,
    QueryExplanation,
    HealthResponse,
    SchemaInfo,
    StreamEvent,
    ChartConfig,
    DashboardLayout,
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global instances
db_manager: DuckDBManager = None
query_agent: QueryAgent = None
chart_agent: ChartAgent = None
conversation_memory: ConversationMemory = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown."""
    # Startup
    logger.info("Starting Conversational BI Agent...")

    global db_manager, query_agent, chart_agent, conversation_memory

    # Initialize database
    data_dir = os.getenv("DATA_DIR", "./data")
    db_path = os.getenv("DUCKDB_PATH")

    db_manager = DuckDBManager(data_dir=data_dir, db_path=db_path)
    db_manager.connect()

    # Load data
    logger.info("Loading dataset...")
    stats = db_manager.load_data()
    logger.info(f"Loaded tables: {stats}")

    # Initialize agents
    model_name = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.1"))

    query_agent = QueryAgent(model_name=model_name, temperature=temperature)
    chart_agent = ChartAgent()
    conversation_memory = ConversationMemory(max_exchanges=5)

    logger.info("Conversational BI Agent ready!")

    yield

    # Shutdown
    logger.info("Shutting down...")
    if db_manager:
        db_manager.close()


# Create FastAPI app
app = FastAPI(
    title="Conversational BI Agent",
    description="AI-powered Business Intelligence agent for Instacart dataset",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Conversational BI Agent API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    stats = db_manager.get_database_stats()

    return HealthResponse(
        status="healthy" if stats["tables_count"] > 0 else "unhealthy",
        database_loaded=stats["tables_count"] > 0,
        tables_count=stats["tables_count"],
        total_rows=stats["total_rows"],
    )


@app.get("/schema", response_model=list[SchemaInfo], tags=["Database"])
async def get_schema():
    """Get database schema information."""
    tables = db_manager.get_all_tables()
    schema_info = []

    for table_name in tables:
        try:
            info = db_manager.get_table_info(table_name)
            schema_info.append(SchemaInfo(**info))
        except Exception as e:
            logger.error(f"Failed to get info for {table_name}: {e}")

    return schema_info


@app.post("/query", response_model=QueryResponse, tags=["Query"])
async def query(request: QueryRequest):
    """
    Execute a natural language query.

    This endpoint:
    1. Converts natural language to SQL
    2. Executes the query
    3. Selects appropriate visualization
    4. Returns results with explanation
    """
    try:
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or str(uuid.uuid4())

        # Get conversation history
        history = conversation_memory.get_history(conversation_id)

        # Generate SQL with LLM
        logger.info(f"Processing question: {request.question}")
        sql_generation = query_agent.generate_sql(
            question=request.question,
            conversation_history=history,
        )

        # Validate SQL
        is_valid, error_msg = db_manager.validate_sql(sql_generation.sql_query)

        if not is_valid:
            logger.warning(f"Invalid SQL generated: {error_msg}")

            # Try to fix the SQL
            try:
                fixed_sql = query_agent.validate_and_fix_sql(
                    sql=sql_generation.sql_query,
                    error_message=error_msg,
                    original_question=request.question,
                )

                # Re-validate
                is_valid, error_msg = db_manager.validate_sql(fixed_sql)
                if is_valid:
                    sql_generation.sql_query = fixed_sql
                    logger.info("SQL fixed successfully")
            except Exception as fix_error:
                logger.error(f"Failed to fix SQL: {fix_error}")

        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to generate valid SQL: {error_msg}",
            )

        # Execute query
        result_data = db_manager.execute_query(sql_generation.sql_query)

        # Select visualization (chart or dashboard)
        visualization = chart_agent.select_visualization(
            question=request.question,
            columns=result_data["columns"],
            data=result_data["data"],
            suggested_type=sql_generation.expected_chart_type,
        )

        # Update conversation memory
        result_summary = f"Returned {result_data['row_count']} rows"
        conversation_memory.add_exchange(
            conversation_id=conversation_id,
            question=request.question,
            sql=sql_generation.sql_query,
            result_summary=result_summary,
        )

        # Build response
        explanation = None
        if request.include_explanation:
            explanation = QueryExplanation(
                reasoning=sql_generation.reasoning,
                sql_query=sql_generation.sql_query,
                tables_used=sql_generation.tables_needed,
                complexity=sql_generation.complexity,
            )

        # Determine if it's a chart or dashboard
        chart_config = visualization if isinstance(visualization, ChartConfig) else None
        dashboard_config = visualization if isinstance(visualization, DashboardLayout) else None

        return QueryResponse(
            success=True,
            result=QueryResult(**result_data),
            chart=chart_config,
            dashboard=dashboard_config,
            explanation=explanation,
            conversation_id=conversation_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query/stream", tags=["Query"])
async def query_stream(request: QueryRequest):
    """
    Execute a query with streaming progress updates.

    Sends Server-Sent Events (SSE) with progress:
    - thinking: LLM is generating SQL
    - querying: Executing SQL
    - visualizing: Selecting chart
    - complete: Final result
    - error: If something fails
    """

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            conversation_id = request.conversation_id or str(uuid.uuid4())
            history = conversation_memory.get_history(conversation_id)

            # Event 1: Thinking
            yield f"data: {json.dumps({'event': 'thinking', 'data': {'message': 'Analyzing your question...'}, 'timestamp': None})}\n\n"

            # Generate SQL
            sql_generation = query_agent.generate_sql(
                question=request.question,
                conversation_history=history,
            )

            # Event 2: Generated SQL
            yield f"data: {json.dumps({'event': 'thinking', 'data': {'reasoning': sql_generation.reasoning, 'sql': sql_generation.sql_query}, 'timestamp': None})}\n\n"

            # Validate and potentially fix SQL
            is_valid, error_msg = db_manager.validate_sql(sql_generation.sql_query)
            if not is_valid:
                try:
                    fixed_sql = query_agent.validate_and_fix_sql(
                        sql=sql_generation.sql_query,
                        error_message=error_msg,
                        original_question=request.question,
                    )
                    sql_generation.sql_query = fixed_sql
                except:
                    pass

            # Event 3: Querying
            yield f"data: {json.dumps({'event': 'querying', 'data': {'message': 'Executing query...'}, 'timestamp': None})}\n\n"

            # Execute query
            result_data = db_manager.execute_query(sql_generation.sql_query)

            # Event 4: Visualizing
            yield f"data: {json.dumps({'event': 'visualizing', 'data': {'message': 'Creating visualization...'}, 'timestamp': None})}\n\n"

            # Select visualization (chart or dashboard)
            visualization = chart_agent.select_visualization(
                question=request.question,
                columns=result_data["columns"],
                data=result_data["data"],
                suggested_type=sql_generation.expected_chart_type,
            )

            # Update memory
            conversation_memory.add_exchange(
                conversation_id=conversation_id,
                question=request.question,
                sql=sql_generation.sql_query,
                result_summary=f"Returned {result_data['row_count']} rows",
            )

            # Determine if it's a chart or dashboard
            chart_config = visualization if isinstance(visualization, ChartConfig) else None
            dashboard_config = visualization if isinstance(visualization, DashboardLayout) else None

            # Event 5: Complete
            response = QueryResponse(
                success=True,
                result=QueryResult(**result_data),
                chart=chart_config,
                dashboard=dashboard_config,
                explanation=QueryExplanation(
                    reasoning=sql_generation.reasoning,
                    sql_query=sql_generation.sql_query,
                    tables_used=sql_generation.tables_needed,
                    complexity=sql_generation.complexity,
                ) if request.include_explanation else None,
                conversation_id=conversation_id,
            )

            yield f"data: {json.dumps({'event': 'complete', 'data': response.model_dump(mode='json'), 'timestamp': None})}\n\n"

        except ClarificationNeeded as e:
            # LLM needs clarification - send as a normal assistant message, not an error
            logger.info(f"Clarification needed: {e.message}")
            yield f"data: {json.dumps({'event': 'clarification', 'data': {'message': e.message}, 'timestamp': None})}\n\n"
        except Exception as e:
            logger.error(f"Stream query failed: {e}", exc_info=True)
            # Make error messages more user-friendly
            error_msg = str(e)
            if "LLM cannot answer" in error_msg:
                # Extract the LLM's explanation
                error_msg = error_msg.split("LLM cannot answer: ", 1)[1] if "LLM cannot answer: " in error_msg else error_msg
            yield f"data: {json.dumps({'event': 'error', 'data': {'message': error_msg}, 'timestamp': None})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.delete("/conversation/{conversation_id}", tags=["Conversation"])
async def clear_conversation(conversation_id: str):
    """Clear conversation history."""
    conversation_memory.clear(conversation_id)
    return {"message": f"Conversation {conversation_id} cleared"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "True").lower() == "true",
    )
