import aiohttp
import asyncio
from typing import Optional
from pydantic import BaseModel, Field


async def emit(emitter, msg, done):
    await emitter(
        {
            "type": "status",
            "data": {
                "done": done,
                "description": msg,
            },
        }
    )


class Action:
    class Valves(BaseModel):
        priority: int = Field(
            default=0,
            description="Priority level for the filter operations.",
        )
        api_url: str = Field(
            default="https://api.siliconflow.cn/v1",
            description="Base URL for the Siliconflow API.",
        )
        api_key: str = Field(
            default="",
            description="API Key for the Siliconflow API.",
        )

    class UserValves(BaseModel):
        size: str = Field(
            default="1024x1024",
            description="1024x1024, 512x1024, 768x512, 768x1024, 1024x576, 576x1024.",
        )
        steps: int = Field(
            default=20,
            description="The number of inference steps to be performed (1-100).",
        )
        model: str = Field(
            default="black-forest-labs/FLUX.1-dev",
            description="The name of the model.",
        )
        pnum: int = Field(
            default=1,
            description="The number of pictures.",
        )
        seed: Optional[int] = Field(
            default=None,
            description="The seed.",
        )

    def __init__(self):
        self.valves = self.Valves()

    async def request(self, prompt, __user__):
        url = f"{self.valves.api_url}/image/generations"

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {self.valves.api_key}",
        }

        payload = {
            "prompt": prompt,
            "model": __user__["valves"].model,
            "image_size": __user__["valves"].size,
            "num_inference_steps": __user__["valves"].steps,
        }

        if seed := __user__["valves"].seed:
            payload["seed"] = seed

        pnum = __user__["valves"].pnum

        async with aiohttp.ClientSession() as sess:
            tasks = [sess.post(url, json=payload, headers=headers) for _ in range(pnum)]
            res = await asyncio.gather(*tasks)
            ret = []

            for i, r in enumerate(res):
                if (s := r.status) == 200:
                    json = await r.json()
                    url = json["images"][0]["url"]
                    ret.append(f"![image{i}]({url})")
                else:
                    text = await r.text()
                    ret.append(f"> The {i} request failed ({s}): {text}.")

            return ret

    async def action(self, body, __user__, __event_call__, __event_emitter__):
        prompt = await __event_call__(
            {
                "type": "input",
                "data": {
                    "title": "Prompt",
                    "placeholder": "",
                    "message": "Enter your prompt.",
                },
            }
        )

        if not isinstance(prompt, str) or not prompt:
            return

        await emit(__event_emitter__, f"Generating pictures, please wait...", False)
        res = await self.request(prompt, __user__)

        for r in res:
            await __event_emitter__(
                {"type": "message", "data": {"content": f"\n\n{r}"}}
            )

        await emit(
            __event_emitter__, f"Generated successfully, click to preview!", True
        )
