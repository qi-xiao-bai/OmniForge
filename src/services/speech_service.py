"""
Speech Synthesis Service
基于 MiMo 语音合成模型生成语音内容
"""

from ..core.mimo_client import mimo_client
import structlog

logger = structlog.get_logger()


class SpeechSynthesisService:
    def __init__(self):
        self.available_voices = {
            "female_yunyi": "云依（女声）",
            "male_yunyang": "云扬（男声）",
            "female_xiaoyuan": "小媛（女声）",
            "male_xiaoyu": "小宇（男声）",
        }
        self.default_voice = "female_yunyi"

    async def generate(
        self,
        text: str,
        voice: str = "female_yunyi",
        speed: float = 1.0,
        pitch: float = 1.0,
    ) -> dict:
        logger.info(f"Speech synthesis: voice={voice}, text_length={len(text)}")

        audio_data = await mimo_client.speech_synthesis(
            text=text,
            voice=voice,
            speed=speed,
            pitch=pitch,
        )

        import base64
        audio_b64 = base64.b64encode(audio_data).decode("utf-8")

        return {
            "type": "speech",
            "audio_data": audio_b64,
            "format": "mp3",
            "text": text,
            "voice": voice,
            "duration_estimate": len(text) / (5 * speed),
        }

    async def batch_generate(self, tasks: list[dict], context: str) -> list[dict]:
        results = []
        for task in tasks:
            prompt = task.get("description", context)
            voice = task.get("voice", self.default_voice)
            result = await self.generate(text=prompt, voice=voice)
            result["task_id"] = task.get("id")
            results.append(result)
        return results

    def estimate_duration(self, text: str, speed: float = 1.0) -> float:
        chars_per_second = 5 * speed
        return len(text) / chars_per_second