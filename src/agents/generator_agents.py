"""
Generator Agent - 多模态内容生成 Agent 集群
并行调用 MiMo 文本、图像、语音合成模型完成内容产出
"""

import asyncio
from typing import Optional
from .base import BaseAgent, Message
from ..core.mimo_client import mimo_client
from ..services.text_service import TextGenerationService
from ..services.image_service import ImageGenerationService
from ..services.speech_service import SpeechSynthesisService
import structlog

logger = structlog.get_logger()


class GeneratorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="generator",
            model="MiMo-V2.5-Multimodal",
            temperature=0.7,
            max_tokens=2048,
        )
        self.text_service = TextGenerationService()
        self.image_service = ImageGenerationService()
        self.speech_service = SpeechSynthesisService()
        self.generation_queue: asyncio.Queue = asyncio.Queue()

    async def think(self, message: Message) -> dict:
        content = message.content
        task_plan = content.get("task_plan", [])
        creative_analysis = content.get("creative_analysis", "")

        logger.info(f"Generator processing {len(task_plan)} tasks")

        results = {}
        text_tasks = []
        image_tasks = []
        speech_tasks = []

        for task in task_plan:
            task_type = task.get("type", "text")
            if task_type == "text":
                text_tasks.append(task)
            elif task_type == "image":
                image_tasks.append(task)
            elif task_type == "voice":
                speech_tasks.append(task)

        if text_tasks:
            text_results = await self._generate_text_batch(text_tasks, creative_analysis)
            results["text"] = text_results

        if image_tasks:
            image_results = await self._generate_image_batch(image_tasks, creative_analysis)
            results["image"] = image_results

        if speech_tasks:
            speech_results = await self._generate_speech_batch(speech_tasks, creative_analysis)
            results["speech"] = speech_results

        return {
            "generation_results": results,
            "task_count": len(task_plan),
            "agent": self.name,
        }

    async def _generate_text_batch(self, tasks: list[dict], context: str) -> list[dict]:
        results = await self.text_service.batch_generate(tasks, context)
        logger.info(f"Generated {len(results)} text contents")
        return results

    async def _generate_image_batch(self, tasks: list[dict], context: str) -> list[dict]:
        results = await self.image_service.batch_generate(tasks, context)
        logger.info(f"Generated {len(results)} images")
        return results

    async def _generate_speech_batch(self, tasks: list[dict], context: str) -> list[dict]:
        results = await self.speech_service.batch_generate(tasks, context)
        logger.info(f"Generated {len(results)} speech clips")
        return results

    async def act(self, thinking_result: dict) -> Message:
        generation_results = thinking_result["generation_results"]

        return Message(
            sender=self.name,
            receiver="evaluator",
            content={
                "raw_results": generation_results,
                "generation_metadata": thinking_result,
            },
            msg_type="task",
            metadata={"task_id": thinking_result.get("task_id")},
        )

    async def generate_single(
        self,
        content_type: str,
        prompt: str,
        context: Optional[str] = None
    ) -> dict:
        if content_type == "text":
            return await self.text_service.generate(prompt, context)
        elif content_type == "image":
            return await self.image_service.generate(prompt, context)
        elif content_type == "voice":
            return await self.speech_service.generate(prompt, context)
        else:
            raise ValueError(f"Unknown content type: {content_type}")