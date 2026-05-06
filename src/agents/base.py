"""
Base Agent - 所有 Agent 的基类
定义 Agent 的通用接口、状态机和消息处理机制
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Optional
from datetime import datetime
import asyncio
import uuid
import structlog

logger = structlog.get_logger()


class AgentStatus(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    WAITING = "waiting"
    DONE = "done"
    ERROR = "error"


class Message:
    def __init__(
        self,
        sender: str,
        receiver: str,
        content: Any,
        msg_type: str = "text",
        metadata: Optional[dict] = None,
        conversation_id: Optional[str] = None,
    ):
        self.id = str(uuid.uuid4())
        self.sender = sender
        self.receiver = receiver
        self.content = content
        self.msg_type = msg_type
        self.metadata = metadata or {}
        self.conversation_id = conversation_id or str(uuid.uuid4())
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "sender": self.sender,
            "receiver": self.receiver,
            "content": self.content,
            "msg_type": self.msg_type,
            "metadata": self.metadata,
            "conversation_id": self.conversation_id,
            "timestamp": self.timestamp.isoformat(),
        }


class BaseAgent(ABC):
    def __init__(
        self,
        name: str,
        model: str = "MiMo-V2.5",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ):
        self.name = name
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.status = AgentStatus.IDLE
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.handlers: dict[str, Callable] = {}
        self.conversation_history: list[Message] = []
        self._running = False
        self._task: Optional[asyncio.Task] = None

        self._register_default_handlers()
        logger.info(f"Agent initialized: {self.name}", model=self.model)

    def _register_default_handlers(self):
        self.handlers = {
            "text": self.handle_text,
            "task": self.handle_task,
            "result": self.handle_result,
            "error": self.handle_error,
        }

    @abstractmethod
    async def think(self, message: Message) -> dict:
        raise NotImplementedError

    @abstractmethod
    async def act(self, thinking_result: dict) -> Message:
        raise NotImplementedError

    async def handle_text(self, message: Message) -> None:
        result = await self.think(message)
        response = await self.act(result)
        await self.send_message(message.sender, response.content, response.msg_type, response.metadata)

    async def handle_task(self, message: Message) -> None:
        self.status = AgentStatus.THINKING
        thinking_result = await self.think(message)
        self.status = AgentStatus.ACTING
        response = await self.act(thinking_result)
        self.status = AgentStatus.DONE
        await self.send_message(message.sender, response.content, response.msg_type, response.metadata)

    async def handle_result(self, message: Message) -> None:
        logger.info(f"{self.name} received result from {message.sender}", content=message.content)

    async def handle_error(self, message: Message) -> None:
        logger.error(f"{self.name} received error from {message.sender}", error=message.content)
        self.status = AgentStatus.ERROR

    async def send_message(
        self,
        receiver: str,
        content: Any,
        msg_type: str = "text",
        metadata: Optional[dict] = None,
    ) -> Message:
        msg = Message(
            sender=self.name,
            receiver=receiver,
            content=content,
            msg_type=msg_type,
            metadata=metadata,
        )
        from .coordinator import AgentCoordinator
        coordinator = AgentCoordinator.get_instance()
        await coordinator.route_message(msg)
        return msg

    async def receive_message(self, message: Message) -> None:
        self.conversation_history.append(message)
        msg_type = message.msg_type
        handler = self.handlers.get(msg_type, self.handle_text)
        await handler(message)

    async def run(self):
        self._running = True
        logger.info(f"Agent {self.name} started")
        while self._running:
            try:
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                await self.receive_message(message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Agent {self.name} error", error=str(e))
                self.status = AgentStatus.ERROR

    def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
        logger.info(f"Agent {self.name} stopped")

    def get_history(self, conversation_id: Optional[str] = None) -> list[Message]:
        if conversation_id:
            return [m for m in self.conversation_history if m.conversation_id == conversation_id]
        return self.conversation_history