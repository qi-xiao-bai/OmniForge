"""
Agent Coordinator - 多 Agent 协作编排器
负责任务分发、状态管理与结果聚合
"""

import asyncio
from typing import Optional, Any
from datetime import datetime
import structlog
from .message_bus import message_bus
from .mimo_client import mimo_client

logger = structlog.get_logger()


class AgentCoordinator:
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._agents: dict[str, Any] = {}
            self._agent_tasks: dict[str, asyncio.Task] = {}
            self._task_queue: asyncio.Queue = asyncio.Queue()
            self._results: dict[str, Any] = {}
            self._running = False
            self._task: Optional[asyncio.Task] = None
            message_bus.subscribe("agent.result", self._handle_result)
            message_bus.subscribe("agent.error", self._handle_error)
            logger.info("AgentCoordinator initialized")

    @classmethod
    def get_instance(cls) -> "AgentCoordinator":
        if cls._instance is None:
            cls._instance = AgentCoordinator()
        return cls._instance

    def register_agent(self, agent: Any):
        self._agents[agent.name] = agent
        message_bus.route(agent.name, "coordinator")
        logger.info(f"Agent registered: {agent.name}")

    def unregister_agent(self, agent_name: str):
        if agent_name in self._agents:
            del self._agents[agent_name]
            logger.info(f"Agent unregistered: {agent_name}")

    async def route_message(self, message):
        receiver = message.receiver
        if receiver in self._agents:
            await self._agents[receiver].receive_message(message)
        else:
            logger.warning(f"Message routed to unknown agent: {receiver}", message_id=message.id)

    async def _handle_result(self, result: Any, metadata: Optional[dict] = None):
        task_id = metadata.get("task_id") if metadata else None
        if task_id:
            self._results[task_id] = result
            logger.info(f"Result received for task: {task_id}")

    async def _handle_error(self, error: Any, metadata: Optional[dict] = None):
        task_id = metadata.get("task_id") if metadata else None
        logger.error(f"Agent error for task: {task_id}", error=error)

    async def submit_task(self, task: dict) -> str:
        task_id = task.get("id", str(datetime.utcnow().timestamp()))
        task["task_id"] = task_id
        task["submitted_at"] = datetime.utcnow().isoformat()
        await self._task_queue.put(task)
        logger.info(f"Task submitted: {task_id}", task_type=task.get("type"))
        return task_id

    async def get_result(self, task_id: str, timeout: float = 120.0) -> Optional[Any]:
        start = datetime.utcnow()
        while (datetime.utcnow() - start).total_seconds() < timeout:
            if task_id in self._results:
                return self._results.pop(task_id)
            await asyncio.sleep(0.5)
        logger.warning(f"Task result timeout: {task_id}")
        return None

    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._process_tasks())
        for agent in self._agents.values():
            self._agent_tasks[agent.name] = asyncio.create_task(agent.run())
        logger.info("AgentCoordinator started")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
        for task in self._agent_tasks.values():
            task.cancel()
        for agent in self._agents.values():
            agent.stop()
        await mimo_client.close()
        logger.info("AgentCoordinator stopped")

    async def _process_tasks(self):
        while self._running:
            try:
                task = await asyncio.wait_for(self._task_queue.get(), timeout=1.0)
                await self._execute_task(task)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Task processing error", error=str(e))

    async def _execute_task(self, task: dict):
        task_id = task.get("task_id")
        task_type = task.get("type")
        payload = task.get("payload", {})

        logger.info(f"Executing task: {task_id}", type=task_type)

        try:
            if task_type == "creative_brief":
                await self._execute_creative_workflow(task_id, payload)
            elif task_type == "content_generation":
                await self._execute_content_workflow(task_id, payload)
            else:
                logger.warning(f"Unknown task type: {task_type}")
        except Exception as e:
            logger.error(f"Task execution failed: {task_id}", error=str(e))
            message_bus.publish("agent.error", str(e), {"task_id": task_id})

    async def _execute_creative_workflow(self, task_id: str, payload: dict):
        creative_agent = self._agents.get("creative")
        planner_agent = self._agents.get("planner")
        generator = self._agents.get("generator")

        if not all([creative_agent, planner_agent, generator]):
            logger.error("Required agents not registered")
            return

        from .base import Message
        brief_msg = Message(
            sender="coordinator",
            receiver="creative",
            content=payload.get("brief", ""),
            msg_type="task",
            metadata={"task_id": task_id, "workflow": "creative"},
        )
        await creative_agent.receive_message(brief_msg)

    async def _execute_content_workflow(self, task_id: str, payload: dict):
        generator = self._agents.get("generator")
        if generator:
            from .base import Message
            gen_msg = Message(
                sender="coordinator",
                receiver="generator",
                content=payload,
                msg_type="task",
                metadata={"task_id": task_id, "workflow": "content"},
            )
            await generator.receive_message(gen_msg)


coordinator = AgentCoordinator.get_instance()