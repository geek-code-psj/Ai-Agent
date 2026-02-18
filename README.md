# AI Agent Framework

A production-ready AI agent system built with Python 3.12, LangChain, OpenAI GPT-4o-mini, FastAPI, and deployable to Google Kubernetes Engine (GKE).

## Features

- **ReAct Architecture**: Implements Reasoning + Acting pattern for intelligent decision-making
- **Multiple Specialized Agents**:
  - Research Agent: Web search and information synthesis
  - Code Agent: Safe Python execution and algorithmic problem-solving
  - Multi-Agent Orchestrator: Intelligent routing and collaboration
- **Comprehensive Tools**:
  - Web Search (DuckDuckGo)
  - Calculator (safe math evaluation)
  - File Reader (multiple formats)
  - Python Executor (sandboxed environment)
- **FastAPI + LangServe**: REST API with `/invoke`, `/stream`, `/chat` endpoints
- **Persistent Memory**: SQLite/PostgreSQL-backed conversation history
- **Authentication**: API key validation
- **Monitoring**: Prometheus metrics and health checks
- **Production-Ready**: Docker containerization and Kubernetes deployment

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│          Load Balancer / Ingress            │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│        FastAPI + LangServe API              │
│  (/chat, /invoke, /stream, /health, /metrics) │
└──────────────────┬──────────────────────────┘
                   │
         ┌─────────┼─────────┐
         ▼         ▼         ▼
    ┌────────┐ ┌────────┐ ┌────────┐
    │Research│ │  Code  │ │ Multi  │
    │ Agent  │ │ Agent  │ │ Agent  │
    └────┬───┘ └────┬───┘ └────┬───┘
         │          │          │
         └──────────┼──────────┘
                    │
         ┌──────────┼──────────┐
         ▼          ▼          ▼
    ┌────────┐ ┌────────┐ ┌────────┐
    │  Web   │ │  Code  │ │  File  │
    │ Search │ │  Exec  │ │ Reader │
    └────────┘ └────────┘ └────────┘
         │
         ▼
┌─────────────────────────┐
│  PostgreSQL / SQLite    │
│  (Session + Memory)     │
└─────────────────────────┘
```

## Project Structure

```
ai-agent-framework/
├── app/
│   ├── agents/
│   │   ├── base_agent.py          # Base ReAct agent
│   │   ├── research_agent.py      # Research specialist
│   │   ├── code_agent.py          # Code execution specialist
│   │   └── multi_agent.py         # Multi-agent orchestrator
│   ├── tools/
│   │   ├── base.py                # Tool interface
│   │   ├── web_search.py          # DuckDuckGo search
│   │   ├── calculator.py          # Math calculator
│   │   ├── file_reader.py         # File reading
│   │   └── python_executor.py     # Safe Python exec
│   ├── chains/
│   │   ├── research_chain.py      # Research chain
│   │   └── code_chain.py          # Code chain
│   ├── memory/
│   │   ├── conversation_buffer.py # In-memory buffer
│   │   └── persistent_memory.py   # DB-backed memory
│   ├── models/
│   │   └── session.py             # Database models
│   ├── middleware/
│   │   ├── auth.py                # API key auth
│   │   └── metrics.py             # Prometheus metrics
│   ├── core/
│   │   ├── config.py              # Configuration
│   │   └── database.py            # Database setup
│   ├── api.py                     # FastAPI app
│   └── main.py                    # Entry point
├── docker/
│   └── Dockerfile                 # Multi-stage build
├── k8s/
│   ├── namespace.yaml             # K8s namespace
│   ├── configmap.yaml             # Configuration
│   ├── secret.yaml                # Secrets
│   ├── deployment.yaml            # Deployment
│   ├── service.yaml               # LoadBalancer service
│   ├── hpa.yaml                   # Autoscaling
│   └── ingress.yaml               # Ingress
├── docker-compose.yml             # Local development
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment template
└── README.md                      # This file
```

## Prerequisites

- Python 3.12+
- OpenAI API key
- Docker (for containerization)
- Kubernetes cluster (for deployment)
- kubectl (for Kubernetes management)

## Local Setup

### 1. Clone and Setup

```bash
cd ai-agent-framework
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy example environment file
copy .env.example .env

# Edit .env and set your OpenAI API key
# OPENAI_API_KEY=sk-your-key-here
```

### 5. Run Locally

```bash
# Run with Python
python app/main.py

# Or use Uvicorn directly
uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

### 6. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Chat with research agent
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the capital of France?",
    "agent_type": "research"
  }'

# Use LangServe invoke endpoint
curl -X POST http://localhost:8000/research-agent/invoke \
  -H "Content-Type: application/json" \
  -d '{"input": "Search for latest AI news"}'
```

### 7. Access LangServe Playground

Open your browser and navigate to:
- Research Agent: `http://localhost:8000/research-agent/playground/`
- Code Agent: `http://localhost:8000/code-agent/playground/`

## Docker Deployment

### 1. Build Docker Image

```bash
docker build -t ai-agent-framework:latest -f docker/Dockerfile .
```

### 2. Run with Docker

```bash
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your-key-here \
  ai-agent-framework:latest
```

### 3. Run with Docker Compose

```bash
# Set your OpenAI API key in .env file
echo "OPENAI_API_KEY=sk-your-key-here" > .env

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

This will start:
- PostgreSQL database on port 5432
- Agent Framework API on port 8000

## Google Kubernetes Engine (GKE) Deployment

### 1. Setup GCP and GKE

```bash
# Set your GCP project
gcloud config set project YOUR_PROJECT_ID

# Create GKE cluster (if not exists)
gcloud container clusters create agent-cluster \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type n1-standard-2 \
  --enable-autoscaling \
  --min-nodes 2 \
  --max-nodes 10

# Get credentials
gcloud container clusters get-credentials agent-cluster \
  --zone us-central1-a
```

### 2. Build and Push Docker Image

```bash
# Configure Docker for GCR
gcloud auth configure-docker

# Build image
docker build -t gcr.io/YOUR_PROJECT_ID/agent-framework:latest -f docker/Dockerfile .

# Push to Google Container Registry
docker push gcr.io/YOUR_PROJECT_ID/agent-framework:latest
```

### 3. Create Kubernetes Secrets

```bash
# Create secret with your OpenAI API key
kubectl create secret generic agent-framework-secret \
  --from-literal=OPENAI_API_KEY=sk-your-key-here \
  --from-literal=API_KEY=your-api-key-here \
  --namespace=ai-agents

# Or edit k8s/secret.yaml with base64-encoded values
# echo -n "sk-your-key" | base64
# Then apply: kubectl apply -f k8s/secret.yaml
```

### 4. Deploy to Kubernetes

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Apply ConfigMap
kubectl apply -f k8s/configmap.yaml

# Apply Secret (if using YAML method)
kubectl apply -f k8s/secret.yaml

# Deploy application
kubectl apply -f k8s/deployment.yaml

# Create service
kubectl apply -f k8s/service.yaml

# Create HPA
kubectl apply -f k8s/hpa.yaml

# Create Ingress (optional)
kubectl apply -f k8s/ingress.yaml
```

### 5. Verify Deployment

```bash
# Check pods
kubectl get pods -n ai-agents

# Check service
kubectl get svc -n ai-agents

# Check HPA
kubectl get hpa -n ai-agents

# View logs
kubectl logs -f deployment/agent-framework -n ai-agents

# Get LoadBalancer IP
kubectl get svc agent-framework-service -n ai-agents
```

### 6. Access the API

```bash
# Get external IP
EXTERNAL_IP=$(kubectl get svc agent-framework-service -n ai-agents -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Test health endpoint
curl http://$EXTERNAL_IP/health

# Chat with agent
curl -X POST http://$EXTERNAL_IP/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "message": "Write a Python function to calculate fibonacci numbers",
    "agent_type": "code"
  }'
```

## API Endpoints

### Core Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `POST /chat` - Chat with agents
- `GET /docs` - OpenAPI documentation

### LangServe Endpoints

#### Research Agent
- `POST /research-agent/invoke` - Invoke research agent
- `POST /research-agent/stream` - Stream research agent responses
- `GET /research-agent/playground/` - Interactive playground

#### Code Agent
- `POST /code-agent/invoke` - Invoke code agent
- `POST /code-agent/stream` - Stream code agent responses
- `GET /code-agent/playground/` - Interactive playground

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | `openai` or `gemini` | `gemini` |
| `GOOGLE_API_KEY` | Google Gemini API key (required for Gemini) | - |
| `GEMINI_MODEL` | Gemini model to use | `gemini-1.5-flash` |
| `OPENAI_API_KEY` | OpenAI API key (required for OpenAI) | - |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4o-mini` |
| `DATABASE_URL` | Database connection URL | `sqlite:///./agent_framework.db` |
| `API_HOST` | API host | `0.0.0.0` |
| `API_PORT` | API port | `8000` |
| `API_KEY` | API authentication key | `None` |
| `MAX_ITERATIONS` | Max agent iterations | `10` |
| `MAX_EXECUTION_TIME` | Max execution time (sec) | `300` |
| `CONVERSATION_MEMORY_SIZE` | Messages in memory | `10` |
| `ENABLE_WEB_SEARCH` | Enable web search tool | `true` |
| `ENABLE_CODE_EXECUTION` | Enable code execution | `true` |
| `ENABLE_FILE_OPERATIONS` | Enable file operations | `true` |
| `ENABLE_METRICS` | Enable Prometheus metrics | `true` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `CORS_ORIGINS` | CORS allowed origins | `*` |

## Usage Examples

### Python SDK

```python
import httpx

# Chat with research agent
response = httpx.post(
    "http://localhost:8000/chat",
    json={
        "message": "What are the latest developments in AI?",
        "agent_type": "research"
    }
)
print(response.json()["response"])

# Use code agent
response = httpx.post(
    "http://localhost:8000/chat",
    json={
        "message": "Write a function to sort a list using quicksort",
        "agent_type": "code"
    }
)
print(response.json()["response"])
```

### Using LangServe Client

```python
from langserve import RemoteRunnable

# Connect to research agent
research_agent = RemoteRunnable("http://localhost:8000/research-agent/")

# Invoke
result = research_agent.invoke({"input": "What is quantum computing?"})
print(result["output"])

# Stream
for chunk in research_agent.stream({"input": "Explain machine learning"}):
    print(chunk, end="", flush=True)
```

## Monitoring

### Prometheus Metrics

Access metrics at `http://localhost:8000/metrics`

Available metrics:
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request duration
- `http_requests_in_progress` - Active requests
- `agent_executions_total` - Total agent executions
- `agent_execution_duration_seconds` - Agent execution time

### Health Checks

Kubernetes uses `/health` endpoint for:
- Liveness probe: Pod restart if unhealthy
- Readiness probe: Traffic routing control

## Security Features

- **Non-root Container**: Runs as user 1000
- **API Key Authentication**: Optional X-API-Key header
- **Sandboxed Code Execution**: RestrictedPython environment
- **Path Traversal Prevention**: Secure file reading
- **Resource Limits**: CPU and memory constraints
- **Network Policies**: Kubernetes network isolation

## Troubleshooting

### Local Development

```bash
# Check logs
python app/main.py

# Test OpenAI connection
python -c "from app.core.config import settings; print(settings.openai_api_key)"

# Database issues
rm agent_framework.db  # Reset SQLite
```

### Docker

```bash
# View logs
docker logs <container-id>

# Enter container
docker exec -it <container-id> /bin/sh

# Rebuild without cache
docker build --no-cache -t ai-agent-framework:latest -f docker/Dockerfile .
```

### Kubernetes

```bash
# Pod not starting
kubectl describe pod <pod-name> -n ai-agents

# View logs
kubectl logs <pod-name> -n ai-agents

# Check secrets
kubectl get secret agent-framework-secret -n ai-agents -o yaml

# Delete and redeploy
kubectl delete -f k8s/deployment.yaml
kubectl apply -f k8s/deployment.yaml
```

## Performance Tuning

### HPA Configuration

Adjust in `k8s/hpa.yaml`:
- `minReplicas`: Minimum pods (default: 2)
- `maxReplicas`: Maximum pods (default: 10)
- `targetCPUUtilizationPercentage`: CPU threshold (default: 70%)

### Resource Limits

Adjust in `k8s/deployment.yaml`:
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- GitHub Issues: [Create an issue]
- Documentation: `/docs` endpoint
- Health Status: `/health` endpoint

## Acknowledgments

- LangChain for agent framework
- OpenAI for GPT-4o-mini
- FastAPI for web framework
- LangServe for chain serving
