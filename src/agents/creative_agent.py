"""
Creative Agent - 创意理解 Agent
基于 MiMo-V2.5 推理模型进行语义解析与创意延展
"""

from typing import Optional
from .base import BaseAgent, Message
from ..core.mimo_client import mimo_client, MiMoModelType
import structlog

logger = structlog.get_logger()


class CreativeAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="creative",
            model="MiMo-V2.5-Reasoning",
            temperature=0.7,
            max_tokens=2048,
        )
        self.creative_styles = [
            "professional", "casual", "humorous", "inspirational", "technical", "artistic"
        ]
        self.content_types = [
            "short_video_script", "marketing_copy", "educational_content",
            "social_media_post", "product_description", "brand_story"
        ]

    async def think(self, message: Message) -> dict:
        brief = message.content
        logger.info(f"Creative agent analyzing brief: {brief[:100]}...")

        system_prompt = """你是一位顶级创意总监，擅长将简单的创作需求转化为富有感染力的内容策略。
请从以下维度分析输入的创作需求：
1. 核心主题与情感基调
2. 目标受众画像
3. 内容形式与风格建议
4. 关键信息点提炼
5. 创意延展方向（3个备选）

请以结构化JSON格式输出分析结果。"""

        result = await mimo_client.text_reasoning(
            prompt=f"请分析这个创作需求：{brief}",
            system=system_prompt,
            max_tokens=2048,
        )

        return {
            "analysis": result["content"],
            "original_brief": brief,
            "agent": self.name,
        }

    async def act(self, thinking_result: dict) -> Message:
        analysis = thinking_result["analysis"]
        target_agent = "planner"

        logger.info(f"Creative agent forwarding to {target_agent}")

        return Message(
            sender=self.name,
            receiver=target_agent,
            content={
                "creative_analysis": analysis,
                "original_brief": thinking_result["original_brief"],
                "next_action": "plan_tasks"
            },
            msg_type="task",
            metadata=thinking_result,
        )

    async def elaborate_idea(self, idea: str, style: str = "professional") -> dict:
        system_prompt = f"""你是一位创意文案专家，根据给定的主题和风格，生成富有创意的内容大纲。
风格要求：{style}
请生成包含以下部分的内容方案：
1. 核心概念深化
2. 叙事结构设计
3. 关键视觉/听觉元素建议
4. 情感曲线规划
5. 行动号召（CTA）设计"""

        result = await mimo_client.text_generation(
            prompt=f"请为以下创意延展：{idea}",
            system=system_prompt,
            temperature=0.8,
        )

        return {
            "elaborated": result["content"],
            "original_idea": idea,
            "style": style,
        }