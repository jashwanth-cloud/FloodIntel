from pydantic import BaseModel, Field


class AssistantRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User's question for the FloodIntel AI Assistant.",
    )

    language: str = Field(
        default="en",
        min_length=2,
        max_length=5,
        description="FloodIntel language code.",
    )