"""
Planner Agent - 内容规划 Agent
将创意拆解为可执行的创作任务序列
"""

from typing import Optional
from .base import BaseAgent, Message
from ..core.mimo_client import mimo_client
import structlog

logger = structlog.get_logger()


class TaskNode:
    def __init__(self, task_id: str, task_type: str, description: str, dependencies: list[str] = None, priority: int = 1):
        self.task_id = task_id
        self.task_type = task_type
        self.description = description
        self.dependencies = dependencies or []
        self.priority = priority
        self.status = "pending"
        self.result = None


class PlannerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="planner",
            model="MiMo-V2.5-Reasoning",
            temperature=0.5,
            max_tokens=2048,
        )
        self.task_templates = {
            "short_video": ["script", "image_prompts", "voiceover_text", "bgm_selection"],
            "marketing": ["headline", "body_copy", "call_to_action", "hashtags"],
            "educational": ["outline", "script", "visuals_plan", "summary"],
            "social": ["post_text", "image_concepts", "engagement_hooks"],
        }

    async def think(self, message: Message) -> dict:
        content = message.content
        creative_analysis = content.get("creative_analysis", "")
        original_brief = content.get("original_brief", "")

        logger.info("Planner agent creating task sequence")

        system_prompt = """你是一位任务规划专家，擅长将创意分析结果转化为可执行的任务序列。
请根据创意分析，制定详细的内容创作任务序列，包含：
1. 任务列表（按执行顺序）
2. 每个任务的具体要求
3. 任务间的依赖关系
4. 质量检查点

以JSON数组格式输出任务列表。"""

        result = await mimo_client.text_reasoning(
            prompt=f"创意分析：{creative_analysis}\n\n原始需求：{original_brief}\n\n请制定任务计划",
            system=system_prompt,
            max_tokens=2048,
        )

        task_plan = self._parse_task_plan(result["content"])

        return {
            "task_plan": task_plan,
            "creative_analysis": creative_analysis,
            "original_brief": original_brief,
            "agent": self.name,
        }

    def _parse_task_plan(self, plan_text: str) -> list[dict]:
        tasks = []
        task_types = ["text", "image", "voice", "evaluation"]

        lines = plan_text.split("\n")
        current_task = None

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line[0].isdigit() and "." in line[:3]:
                if current_task:
                    tasks.append(current_task)
                current_task = {
                    "id": f"task_{len(tasks) + 1}",
                    "type": task_types[len(tasks) % len(task_types)],
                    "description": line,
                    "dependencies": [],
                    "priority": len(tasks) + 1,
                }
            elif current_task and "依赖" in line:
                deps = [d.strip() for d in line.split(":")[-1].split(",")]
                current_task["dependencies"] = deps

        if current_task:
            tasks.append(current_task)

        if not tasks:
            for i, t_type in enumerate(task_types):
                tasks.append({
                    "id": f"task_{i + 1}",
                    "type": t_type,
                    "description": f"自动规划任务 {i + 1}",
                    "dependencies": [],
                    "priority": i + 1,
                })

        return tasks

    async def act(self, thinking_result: dict) -> Message:
        task_plan = thinking_result["task_plan"]

        return Message(
            sender=self.name,
            receiver="generator",
            content={
                "task_plan": task_plan,
                "creative_analysis": thinking_result["creative_analysis"],
            },
            msg_type="task",
            metadata={
                "task_id": thinking_result.get("task_id"),
                "workflow": "content_creation",
            },
        )

    def create_dag(self, tasks: list[dict]) -> dict:
        dag = {"nodes": [], "edges": []}

        for task in tasks:
            dag["nodes"].append({
                "id": task["id"],
                "type": task["type"],
                "status": "pending",
            })

            for dep in task.get("dependencies", []):
                dag["edges"].append({
                    "from": dep,
                    "to": task["id"],
                })

        return dag