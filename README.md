# OmniForge

**Multi-modal AI Content Creation Engine** — Powered by Xiaomi MiMo-V2.5 with multi-agent collaboration framework.

## Features

- **Multi-Agent Collaboration**: 5 specialized agents (Creative, Planner, Generator, Evaluator) working autonomously
- **Full Modal Generation**: Parallel generation of text, image, and speech synthesis
- **Intelligent Quality Evaluation**: Discriminator-driven iterative optimization
- **DAG Workflow Engine**: Visual task orchestration with automated execution
- **Context-Aware Consistency**: 128K long-context reasoning ensures consistent emotion and style across modalities

## Quick Start

### Prerequisites

- Python 3.11+
- Xiaomi MiMo API Key

### Installation

```bash
git clone https://github.com/qi-xiao-bai/OmniForge.git
cd OmniForge

pip install -r requirements.txt
```

### Configuration

```bash
export MIMO_API_KEY="your-api-key-here"
export MIMO_BASE_URL="https://api.mimomimo.com/v1"
```

### Run

```bash
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API Docs: http://localhost:8000/docs

### Docker

```bash
docker-compose up --build
```

## Architecture

```
User Input → Creative Agent (MiMo-V2.5 Reasoning)
         → Planner Agent (MiMo-V2.5 Reasoning)
         → Multi-Modal Generator Cluster
           ├─ Text Agent (MiMo-V2.5 Text)
           ├─ Image Agent (MiMo Multi-Modal)
           └─ Speech Agent (MiMo Speech Synthesis)
         → Evaluator Agent (MiMo-V2.5 Reasoning)
         → Post-Processing Pipeline
```

## API Examples

### Create Content Task

```bash
curl -X POST http://localhost:8000/api/v1/creative \
  -H "Content-Type: application/json" \
  -d '{
    "brief": "Create a video about the latest foldable smartphone for a tech review show",
    "content_type": "short_video",
    "style": "professional"
  }'
```

### Check Task Status

```bash
curl http://localhost:8000/api/v1/task/{task_id}
```

## System Requirements

| Component | Minimum |
|-----------|---------|
| CPU | 2 cores |
| Memory | 4 GB |
| Python | 3.11+ |
| Network | Access to MiMo API |

## Project Structure

```
OmniForge/
├── src/
│   ├── main.py                 # FastAPI entry point
│   ├── agents/                  # Agent implementations
│   │   ├── base.py              # Agent base class
│   │   ├── coordinator.py       # Collaboration orchestrator
│   │   ├── creative_agent.py    # Creative understanding
│   │   ├── planner_agent.py     # Content planning
│   │   ├── generator_agents.py  # Multi-modal generation
│   │   └── evaluator_agent.py   # Quality evaluation
│   ├── core/                    # Core modules
│   │   ├── mimo_client.py       # MiMo API client
│   │   ├── message_bus.py       # Message bus
│   │   └── workflow_engine.py   # DAG workflow
│   ├── api/                     # API layer
│   │   ├── routes.py            # Route definitions
│   │   └── schemas.py           # Data models
│   └── services/                # Business services
├── tests/                       # Test suite
├── docs/                        # Architecture docs
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## License

MIT