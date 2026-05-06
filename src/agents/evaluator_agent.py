"""
Evaluator Agent - 质量评估 Agent
引入判别器机制，对生成内容进行多维度评分并触发迭代优化
"""

from typing import Optional
from .base import BaseAgent, Message
from ..core.mimo_client import mimo_client
import structlog

logger = structlog.get_logger()


class EvaluationCriteria:
    def __init__(self):
        self.criteria = {
            "relevance": {"weight": 0.3, "description": "内容与原始需求的契合度"},
            "creativity": {"weight": 0.25, "description": "创意表现与独特性"},
            "coherence": {"weight": 0.2, "description": "内容逻辑连贯性"},
            "engagement": {"weight": 0.15, "description": "受众吸引力"},
            "technical": {"weight": 0.1, "description": "技术质量（语法、格式、专业度）"},
        }
        self.passing_score = 0.75


class EvaluatorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="evaluator",
            model="MiMo-V2.5-Reasoning",
            temperature=0.3,
            max_tokens=1024,
        )
        self.criteria = EvaluationCriteria()

    async def think(self, message: Message) -> dict:
        content = message.content
        raw_results = content.get("raw_results", {})

        logger.info("Evaluator assessing content quality")

        evaluation_report = {}

        for content_type, results in raw_results.items():
            if isinstance(results, list):
                for idx, result in enumerate(results):
                    eval_result = await self._evaluate_single(
                        result, content_type, raw_results
                    )
                    evaluation_report[f"{content_type}_{idx}"] = eval_result
            else:
                eval_result = await self._evaluate_single(
                    results, content_type, raw_results
                )
                evaluation_report[content_type] = eval_result

        overall_score = self._calculate_overall_score(evaluation_report)
        needs_refinement = overall_score < self.criteria.passing_score

        return {
            "evaluation_report": evaluation_report,
            "overall_score": overall_score,
            "needs_refinement": needs_refinement,
            "original_results": raw_results,
            "agent": self.name,
        }

    async def _evaluate_single(
        self, result: dict, content_type: str, all_results: dict
    ) -> dict:
        content = result.get("content", result.get("image_url", ""))
        if not content:
            content = str(result)

        system_prompt = """你是一位专业内容质量评估师。请从以下维度对内容进行1-10分评分：
1. 相关性（relevance）：内容与需求的契合程度
2. 创意性（creativity）：创新程度和独特性
3. 连贯性（coherence）：逻辑是否通顺
4. 吸引力（engagement）：对目标受众的吸引程度
5. 技术质量（technical）：语法、专业度等

请以JSON格式输出：{"scores": {"relevance": X, "creativity": X, "coherence": X, "engagement": X, "technical": X}, "feedback": "简要评语", "suggestions": ["改进建议1", "改进建议2"]}"""

        try:
            eval_result = await mimo_client.text_generation(
                prompt=f"请评估以下{content_type}类型内容：\n{content[:500]}",
                system=system_prompt,
                temperature=0.3,
                max_tokens=512,
            )
            import json
            parsed = json.loads(eval_result["content"])
            return parsed
        except Exception as e:
            logger.warning(f"Evaluation parsing failed, using defaults: {e}")
            return {
                "scores": {
                    "relevance": 7, "creativity": 7, "coherence": 7,
                    "engagement": 7, "technical": 7
                },
                "feedback": "自动评估",
                "suggestions": [],
            }

    def _calculate_overall_score(self, evaluation_report: dict) -> float:
        if not evaluation_report:
            return 0.0

        total_weighted = 0.0
        total_weight = 0.0

        for item in evaluation_report.values():
            scores = item.get("scores", {})
            weights = self.criteria.criteria

            item_weighted = 0.0
            item_weight = 0.0

            for criterion, info in weights.items():
                if criterion in scores:
                    normalized_score = scores[criterion] / 10.0
                    item_weighted += normalized_score * info["weight"]
                    item_weight += info["weight"]

            if item_weight > 0:
                total_weighted += item_weighted / item_weight * sum(weights[c]["weight"] for c in weights)
                total_weight += sum(weights[c]["weight"] for c in weights)

        return total_weighted / total_weight if total_weight > 0 else 0.0

    async def act(self, thinking_result: dict) -> Message:
        evaluation = thinking_result

        if evaluation["needs_refinement"]:
            logger.info("Content needs refinement, sending back to generator")
            return Message(
                sender=self.name,
                receiver="generator",
                content={
                    "refinement_feedback": evaluation["evaluation_report"],
                    "overall_score": evaluation["overall_score"],
                    "original_results": evaluation["original_results"],
                },
                msg_type="task",
                metadata={"task_id": thinking_result.get("task_id"), "refinement": True},
            )
        else:
            logger.info(f"Content approved with score: {evaluation['overall_score']:.2f}")
            return Message(
                sender=self.name,
                receiver="coordinator",
                content={
                    "status": "approved",
                    "final_results": evaluation["original_results"],
                    "evaluation_report": evaluation["evaluation_report"],
                    "overall_score": evaluation["overall_score"],
                },
                msg_type="result",
                metadata={"task_id": thinking_result.get("task_id")},
            )