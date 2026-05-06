# OmniForge Architecture

## Overview

OmniForge is a multi-modal AI content creation engine built on Xiaomi MiMo-V2.5 large language models, featuring a multi-agent collaboration framework for end-to-end automated content creation.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway Layer                         │
│                    (FastAPI + Uvicorn)                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Agent Coordinator                           │
│           (Task Distribution & Result Aggregation)              │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Creative    │───▶│   Planner    │───▶│  Generator   │
│    Agent     │    │    Agent     │    │   (Multi)    │
└──────────────┘    └──────────────┘    └──────────────┘
                                              │
                                              ▼
                                     ┌──────────────┐
                                     │  Evaluator   │
                                     │    Agent     │
                                     └──────────────┘
                                              │
                                              ▼
                                     ┌──────────────┐
                                     │   Result     │
                                     │  Collection  │
                                     └──────────────┘
```

## Core Components

### 1. Agent System

#### Creative Agent
- Analyzes creative briefs using MiMo-V2.5 reasoning model
- Extracts core themes, emotional tone, target audience
- Generates creative extensions and alternatives

#### Planner Agent
- Converts creative analysis into executable task sequences
- Manages task dependencies and priorities
- Creates DAG workflow representations

#### Generator Agent Cluster
- **Text Agent**: Generates scripts, copy, descriptions
- **Image Agent**: Creates visual content prompts and images
- **Speech Agent**: Synthesizes voice content

#### Evaluator Agent
- Quality assessment using discriminator mechanism
- Multi-dimensional scoring (relevance, creativity, coherence, engagement, technical)
- Iterative refinement triggering

### 2. Message Bus
- Publish-subscribe pattern for agent communication
- Message routing and filtering
- Conversation history persistence

### 3. Workflow Engine
- DAG-based workflow representation
- Task scheduling and dependency resolution
- Parallel execution support

### 4. MiMo API Integration
- Unified client for all MiMo models
- Automatic retry with tenacity
- Token usage tracking

## Data Flow

1. **Request Ingress**: User submits creative brief via API
2. **Creative Analysis**: Creative Agent analyzes and extracts insights
3. **Task Planning**: Planner Agent creates execution task sequence
4. **Parallel Generation**: Generator Agents produce content in parallel
5. **Quality Evaluation**: Evaluator Agent scores and provides feedback
6. **Refinement Loop** (optional): Iterative improvement if quality below threshold
7. **Result Aggregation**: Final results collected and returned to user

## Technology Stack

- **Runtime**: Python 3.11+
- **Web Framework**: FastAPI + Uvicorn
- **Async**: asyncio
- **AI Models**: Xiaomi MiMo-V2.5 Series
- **Logging**: structlog
- **Testing**: pytest + pytest-asyncio
- **Deployment**: Docker + Kubernetes

## Scaling Considerations

- Agent instances can be scaled horizontally
- Message bus supports Redis-backed distributed mode
- Workflow engine supports distributed task execution
- MiMo API calls are pooled and rate-limited