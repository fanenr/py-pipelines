from pydantic import BaseModel, Field


class Filter:
    class Valves(BaseModel):
        priority: int = Field(
            default=0,
            description="Priority level for the filter operations.",
        )
        hard: int = Field(
            default=50,
            description="Above that many messages, flat out refuse.",
        )
        soft: int = Field(
            default=25,
            description="Number of message when to start warning the user.",
        )

    def __init__(self):
        self.valves = self.Valves()

    async def on_valves_updated(self):
        assert self.valves.soft < self.valves.hard, "soft must be smaller than hard."

    async def inlet(self, body, __user__, __event_emitter__):
        async def emit(msg):
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "done": True,
                        "description": msg,
                    },
                }
            )

        if len(body["messages"]) > self.valves.hard * 2:
            await emit(
                f"The conversation has reached its limit. Please start a new chat."
            )
            raise Exception(
                f"The conversation has reached its limit. Please start a new chat."
            )

        elif len(body["messages"]) > self.valves.soft * 2:
            await emit(f"Too many conversation rounds, consider starting a new chat.")

        return body

    async def outlet(self, body, __user__):
        return body
