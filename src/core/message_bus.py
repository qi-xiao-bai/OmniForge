"""
Message Bus - Agent 间消息通信总线
实现发布-订阅模式，支持消息路由、过滤与持久化
"""

import asyncio
from typing import Callable, Optional, Any
from collections import defaultdict
from datetime import datetime
import uuid
import structlog

logger = structlog.get_logger()


class MessageBus:
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._subscribers: dict[str, list[Callable]] = defaultdict(list)
            self._message_history: list[dict] = []
            self._max_history = 1000
            self._routes: dict[str, str] = {}
            logger.info("MessageBus initialized")

    def subscribe(self, topic: str, handler: Callable) -> str:
        subscription_id = str(uuid.uuid4())
        self._subscribers[topic].append(handler)
        logger.debug(f"Subscribed to topic: {topic}", subscription_id=subscription_id)
        return subscription_id

    def unsubscribe(self, topic: str, subscription_id: str = None):
        if subscription_id:
            self._subscribers[topic] = [
                h for h in self._subscribers[topic] if getattr(h, "id", None) != subscription_id
            ]
        else:
            self._subscribers[topic] = []

    def publish(self, topic: str, message: Any, metadata: Optional[dict] = None):
        self._record_message(topic, message, metadata)
        for handler in self._subscribers[topic]:
            try:
                if asyncio.iscoroutinefunction(handler):
                    asyncio.create_task(handler(message, metadata))
                else:
                    handler(message, metadata)
            except Exception as e:
                logger.error(f"Handler error for topic {topic}", error=str(e))

    async def publish_async(self, topic: str, message: Any, metadata: Optional[dict] = None):
        self._record_message(topic, message, metadata)
        tasks = []
        for handler in self._subscribers[topic]:
            try:
                if asyncio.iscoroutinefunction(handler):
                    tasks.append(handler(message, metadata))
                else:
                    handler(message, metadata)
            except Exception as e:
                logger.error(f"Handler error for topic {topic}", error=str(e))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def route(self, from_agent: str, to_agent: str):
        self._routes[from_agent] = to_agent
        logger.debug(f"Route established: {from_agent} -> {to_agent}")

    def get_route(self, from_agent: str) -> Optional[str]:
        return self._routes.get(from_agent)

    def _record_message(self, topic: str, message: Any, metadata: Optional[dict] = None):
        record = {
            "id": str(uuid.uuid4()),
            "topic": topic,
            "message": message,
            "metadata": metadata,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._message_history.append(record)
        if len(self._message_history) > self._max_history:
            self._message_history.pop(0)

    def get_history(self, topic: Optional[str] = None, limit: int = 100) -> list[dict]:
        if topic:
            filtered = [m for m in self._message_history if m["topic"] == topic]
            return filtered[-limit:]
        return self._message_history[-limit:]

    def clear_history(self):
        self._message_history.clear()
        logger.info("Message history cleared")


message_bus = MessageBus()