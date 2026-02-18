"""FastAPI application with LangServe integration."""

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from pydantic import BaseModel
from langserve import add_routes

from app.core.config import settings
from app.core.database import init_db, close_db, get_db
from app.chains.research_chain import create_research_chain
from app.chains.code_chain import create_code_chain
from app.agents.research_agent import ResearchAgent
from app.agents.code_agent import CodeAgent
from app.agents.multi_agent import MultiAgentOrchestrator
from app.middleware.auth import validate_api_key, get_api_key_dependency
from app.middleware.metrics import MetricsMiddleware, record_agent_execution
from sqlalchemy.ext.asyncio import AsyncSession


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for app initialization and cleanup.
    
    Args:
        app: FastAPI application
    """
    # Startup
    print("Starting AI Agent Framework...")
    await init_db()
    print("Database initialized")
    
    model_name = settings.gemini_model if settings.llm_provider == "gemini" else settings.openai_model
    print(f"LLM Provider: {settings.llm_provider.upper()} ({model_name})")
    print(f"API running on {settings.api_host}:{settings.api_port}")
    
    yield
    
    # Shutdown
    print("Shutting down AI Agent Framework...")
    await close_db()
    print("Database connections closed")


# Create FastAPI app
app = FastAPI(
    title="AI Agent Framework",
    description="""
# AI Agent Framework API

**Production-ready AI agent system building with Python, LangChain, and OpenAI/Gemini.**

---

## 🚀 Getting Started

### 1. Authorize
Click the **Authorize** button at the top right and enter your API key (if enabled).

### 2. Choose Your Agent
| Agent | Best For | Typical Choice |
|-------|----------|----------------|
| **Chat** | General questions, routing | ✅ Start Here |
| **Research** | Web search, factual analysis | Specific deep dives |
| **Code** | Python generation, math, data | Programming tasks |

### 3. Make Your First Call
Use the **Refined Chat Endpoint** for the simplest experience:
- **Endpoint**: `POST /chat`
- **Body**: `{"message": "Who won the 2024 Super Bowl?"}`

---

## ⚡ Execution Modes: Which one to use?

| Feature | **Invoke** | **Batch** | **Stream** |
| :--- | :--- | :--- | :--- |
| **Best For** | Chatbots, simple Q&A | Bulk processing (10+ items) | TI/UX with "typing" effect |
| **Latency** | Waits for full answer (2-10s) | Varies by volume | First token < 1s |
| **Response** | JSON Object | List of JSON Objects | Server-Sent Events (SSE) |
| **Use Case** | *"What is the capital of France?"* | *Analyze 500 reviews* | *Live code generation* |

---

## 🤖 Agent Relationships
* **Research Agent**: Think of this as a **"Librarian"**. It's great at finding facts, summarizing news, and verifying information. It CANNOT execute code.
* **Code Agent**: Think of this as a **"Developer"**. It writes and runs Python. It's great for math, data analysis, and algorithms. It verifies its own code.

""",
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Getting Started & Basic Chat", "description": "✅ **Beginner Friendly** - Start here!"},
        {"name": "Research Agent", "description": "🔎 **Web Research & Analysis** - For factual queries"},
        {"name": "Code Agent", "description": "💻 **Code Generation** - For programming & math"},
        {"name": "Observability & Monitoring", "description": "🔧 **Ops & Health** - Prometheus metrics and health checks"},
        {"name": "Feedback", "description": "👍 **RLHF & Tracing** - Send user feedback"},
        {"name": "Advanced: Config & Customization", "description": "⚙️ **Internals** - Configuration schemas"},
        {"name": "Internal/Utility", "description": "System endpoints"},
    ]
)

# Custom OpenAPI Schema Generator
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
    )
    
    # --- Customization Logic ---
    
    # 1. Rename confusing schemas
    schema_replacements = {
        "Research_agentresearch_agent_wrapper_config": "ResearchAgentConfig",
        "Code_agentcode_agent_wrapper_config": "CodeAgentConfig",
        "Research_agent_wrapper_input": "ResearchAgentInput",
        "Research_agent_wrapper_output": "ResearchAgentOutput",
        "Code_agent_wrapper_input": "CodeAgentInput",
        "Code_agent_wrapper_output": "CodeAgentOutput"
    }
    
    # Replace in components/schemas
    if "components" in openapi_schema and "schemas" in openapi_schema["components"]:
        new_schemas = {}
        for name, schema in openapi_schema["components"]["schemas"].items():
            new_name = schema_replacements.get(name, name)
            # Remove repetitive prefixes from other schemas if needed
            if name.startswith("Research_agent") and name not in schema_replacements:
                new_name = name.replace("Research_agent", "Research")
            if name.startswith("Code_agent") and name not in schema_replacements:
                new_name = name.replace("Code_agent", "Code")
                
            new_schemas[new_name] = schema
        openapi_schema["components"]["schemas"] = new_schemas

    # 2. Iterate paths to improve descriptions and tags
    for path, path_item in openapi_schema["paths"].items():
        for method, operation in path_item.items():
            op_id = operation.get("operationId", "")
            
            # --- Chat Endpoint ---
            if path == "/chat":
                operation["tags"] = ["Getting Started & Basic Chat"]
                operation["summary"] = "✅ Chat with Agent"
                operation["description"] = """
                **The primary entry point for most applications.**
                
                Automatically routes your message to the appropriate agent.
                
                **Use this when:**
                * You want a simple "chatbot" experience.
                * You don't know which specific agent to use.
                """
            
            # --- Research Agent Endpoints ---
            if "/research-agent/" in path:
                # Assign Tag
                if "/config" in path or "schema" in path:
                    operation["tags"] = ["Advanced: Config & Customization"]
                elif "feedback" in path or "trace" in path:
                    operation["tags"] = ["Feedback"]
                else:
                    operation["tags"] = ["Research Agent"]

                # Custom Descriptions
                if path.endswith("/invoke"):
                    operation["summary"] = "⚡ Run Research Task (Wait for Result)"
                    operation["description"] = "**Best for:** Chatbots, blocking operations, where you need the final answer at once."
                elif path.endswith("/batch"):
                    operation["summary"] = "⚡ Run Batch Research"
                    operation["description"] = "**Best for:** Processing many queries at once (e.g., analyzing 100 URLs)."
                elif path.endswith("/stream"):
                    operation["summary"] = "⚡ Stream Raw Tokens"
                    operation["description"] = "**Best for:** Real-time UI typing effects. Returns chunks of text as they are generated."
                elif path.endswith("/stream_log"):
                    operation["summary"] = "🔧 Stream Debug Logs"
                    operation["description"] = "**Best for:** Developers debugging agent reasoning. Shows tool calls and internal thoughts."
                elif path.endswith("/stream_events"):
                    operation["summary"] = "📡 Stream Lifecycle Events"
                    operation["description"] = "**Best for:** Building progress bars or structured monitoring. Emits JSON events for start, tool_use, and finish."
            
            # --- Code Agent Endpoints ---
            if "/code-agent/" in path:
                 # Assign Tag
                if "/config" in path or "schema" in path:
                    operation["tags"] = ["Advanced: Config & Customization"]
                elif "feedback" in path or "trace" in path:
                    operation["tags"] = ["Feedback"]
                else:
                    operation["tags"] = ["Code Agent"]
                
                # Custom Descriptions
                if path.endswith("/invoke"):
                    operation["summary"] = "⚡ Run Code Task (Wait for Result)"
                    operation["description"] = "**Best for:** Generating a script or solving a math problem and getting the final output."
                elif path.endswith("/stream"):
                    operation["summary"] = "⚡ Stream Code Generation"
                    operation["description"] = "**Best for:** Showing code being written in real-time."
                    
            # --- Clean up Op IDs and refs ---
            # (Recursive replacement of schema refs would go here in a full implementation, 
            #  but explicit schema renaming above handles the main definitions)

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add metrics middleware if enabled
if settings.enable_metrics:
    app.add_middleware(MetricsMiddleware)


# Request/Response models
class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    agent_type: str = "research"  # 'research', 'code', 'multi'
    session_id: str | None = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Find the latest news on fusion energy.",
                "agent_type": "research",
                "session_id": "session-123"
            }
        }


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    agent_type: str
    session_id: str | None = None
    execution_time: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "Recent breakthroughs in fusion energy include...",
                "agent_type": "research",
                "session_id": "session-123",
                "execution_time": 2.45
            }
        }


# Health check endpoint
@app.get("/health", tags=["Observability & Monitoring"], summary="✅ System Health")
async def health_check():
    """
    **Health check endpoint.**
    
    used by Kubernetes/Docker for liveness and readiness probes.
    """
    model_name = settings.gemini_model if settings.llm_provider == "gemini" else settings.openai_model
    return {
        "status": "healthy",
        "service": "ai-agent-framework",
        "version": "1.0.0",
        "provider": settings.llm_provider,
        "model": model_name,
    }


# Metrics endpoint
@app.get("/metrics", tags=["Observability & Monitoring"], summary="🔧 Prometheus Metrics")
async def metrics():
    """
    **Prometheus metrics endpoint.**
    
    Scraped by Prometheus for monitoring application performance and agent execution stats.
    """
    if not settings.enable_metrics:
        raise HTTPException(status_code=404, detail="Metrics disabled")
    
    return JSONResponse(
        content=generate_latest().decode('utf-8'),
        media_type=CONTENT_TYPE_LATEST
    )


# Chat endpoint
@app.post("/chat", response_model=ChatResponse, tags=["Getting Started & Basic Chat"], summary="✅ Chat with Agent")
async def chat(
    request: ChatRequest,
    api_key: str = Depends(get_api_key_dependency()),
    db: AsyncSession = Depends(get_db),
):
    """
    **Chat with an AI Agent.**
    
    This is the primary endpoint for user interaction.
    
    **Scenario: Customer Support Bot**
    *   **User**: "How do I reset my password?"
    *   **Agent**: "To reset your password, go to settings..."
    
    **Agent Types:**
    * `research`: Uses DuckDuckGo to find information.
    * `code`: Generates and executes Python code.
    """
    # Validate API key
    await validate_api_key(Request, api_key)
    
    start_time = time.time()
    
    try:
        # Create agent based on type
        if request.agent_type == "research":
            agent = ResearchAgent()
        elif request.agent_type == "code":
            agent = CodeAgent()
        elif request.agent_type == "multi":
            agent = MultiAgentOrchestrator()
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid agent type: {request.agent_type}. Use 'research', 'code', or 'multi'"
            )
        
        # Execute agent
        response = await agent.run(request.message)
        execution_time = time.time() - start_time
        
        # Record metrics
        if settings.enable_metrics:
            record_agent_execution(request.agent_type, execution_time, "success")
        
        return ChatResponse(
            response=response,
            agent_type=request.agent_type,
            session_id=request.session_id,
            execution_time=execution_time,
        )
        
    except Exception as e:
        execution_time = time.time() - start_time
        if settings.enable_metrics:
            record_agent_execution(request.agent_type, execution_time, "error")
        
        raise HTTPException(status_code=500, detail=str(e))


# Add LangServe routes for research agent
from fastapi import APIRouter
from fastapi.openapi.utils import get_openapi

research_agent_router = APIRouter()
add_routes(
    research_agent_router,
    create_research_chain(),
    path="/research-agent",
    enable_feedback_endpoint=True,
    enable_public_trace_link_endpoint=True,
)
app.include_router(research_agent_router) # Tags handled by custom_openapi

# Add LangServe routes for code agent
code_agent_router = APIRouter()
add_routes(
    code_agent_router,
    create_code_chain(),
    path="/code-agent",
    enable_feedback_endpoint=True,
    enable_public_trace_link_endpoint=True,
)
app.include_router(code_agent_router) # Tags handled by custom_openapi


# Root endpoint
@app.get("/", tags=["System & Monitoring"], include_in_schema=False)
async def root():
    """
    Root endpoint. Redirects to documentation.
    """
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
