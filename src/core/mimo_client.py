"""
MiMo API Client - Xiaomi MiMo 大模型 API 集成层
支持文本生成、图像生成、语音合成等多模态能力
"""

import os
import httpx
from typing import Optional, Any
import asyncio
import structlog

logger = structlog.get_logger()


class MiMoModelType:
    TEXT_REASONING = "text-reasoning"
    TEXT_GENERATION = "text-generation"
    MULTIMODAL = "multimodal"
    SPEECH_SYNTHESIS = "speech-synthesis"


class MiMoClient:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.mimomimo.com/v1"):
        self.api_key = api_key or os.getenv("MIMO_API_KEY", "")
        self.base_url = base_url
        self.timeout = 120.0
        self._client: Optional[httpx.AsyncClient] = None

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=self.timeout,
            )
        return self._client

    async def text_generation(
        self,
        prompt: str,
        model: str = "MiMo-V2.5-Reasoning",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        system: Optional[str] = None,
        conversation_history: Optional[list[dict]] = None,
    ) -> dict:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        logger.info("MiMo text_generation request", model=model, prompt_length=len(prompt))
        client = await self.get_client()
        try:
            response = await client.post("/chat/completions", json=payload)
            response.raise_for_status()
            result = response.json()
            logger.info("MiMo text_generation success", model=model)
            return {
                "content": result["choices"][0]["message"]["content"],
                "usage": result.get("usage", {}),
                "model": result.get("model", model),
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"MiMo API error: {e.response.status_code}", detail=e.response.text)
            raise

    async def text_reasoning(
        self,
        prompt: str,
        temperature: float = 0.5,
        max_tokens: int = 4096,
        system: Optional[str] = None,
    ) -> dict:
        return await self.text_generation(
            prompt=prompt,
            model="MiMo-V2.5-Reasoning",
            temperature=temperature,
            max_tokens=max_tokens,
            system=system,
        )

    async def image_generation(
        self,
        prompt: str,
        model: str = "MiMo-V2.5-Multimodal",
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "vivid",
    ) -> dict:
        payload = {
            "model": model,
            "prompt": prompt,
            "n": 1,
            "size": size,
            "quality": quality,
            "style": style,
        }

        logger.info("MiMo image_generation request", model=model, prompt_length=len(prompt))
        client = await self.get_client()
        try:
            response = await client.post("/images/generations", json=payload)
            response.raise_for_status()
            result = response.json()
            logger.info("MiMo image_generation success", model=model)
            return {
                "image_url": result["data"][0]["url"],
                "revised_prompt": result["data"][0].get("revised_prompt", prompt),
                "usage": result.get("usage", {}),
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"MiMo image API error: {e.response.status_code}")
            raise

    async def speech_synthesis(
        self,
        text: str,
        model: str = "MiMo-Speech-01",
        voice: str = "female_yunyi",
        speed: float = 1.0,
        pitch: float = 1.0,
    ) -> bytes:
        payload = {
            "model": model,
            "input": text,
            "voice": voice,
            "speed": speed,
            "pitch": pitch,
        }

        logger.info("MiMo speech_synthesis request", model=model, text_length=len(text))
        client = await self.get_client()
        try:
            response = await client.post("/audio/speech", json=payload)
            response.raise_for_status()
            logger.info("MiMo speech_synthesis success", model=model)
            return response.content
        except httpx.HTTPStatusError as e:
            logger.error(f"MiMo speech API error: {e.response.status_code}")
            raise

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()


mimo_client = MiMoClient()