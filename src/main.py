"""
OmniForge FastAPI Application
多模态 AI 内容创作引擎 API 服务
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog
import asyncio

from .api.routes import router
from .agents.coordinator import coordinator
from .agents.creative_agent import CreativeAgent
from .agents.planner_agent import PlannerAgent
from .agents.generator_agents import GeneratorAgent
from .agents.evaluator_agent import EvaluatorAgent

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)

logger = structlog.get_logger()

app = FastAPI(
    title="OmniForge",
    description="多模态 AI 内容创作引擎 - 基于 MiMo-V2.5 的多 Agent 协作框架",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    logger.info("OmniForge starting up...")

    creative = CreativeAgent()
    planner = PlannerAgent()
    generator = GeneratorAgent()
    evaluator = EvaluatorAgent()

    coordinator.register_agent(creative)
    coordinator.register_agent(planner)
    coordinator.register_agent(generator)
    coordinator.register_agent(evaluator)

    await coordinator.start()

    logger.info("OmniForge started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("OmniForge shutting down...")
    await coordinator.stop()
    logger.info("OmniForge stopped")


@app.get("/")
async def root():
    return {
        "name": "OmniForge",
        "version": "1.0.0",
        "description": "多模态 AI 内容创作引擎",
        "status": "running",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}