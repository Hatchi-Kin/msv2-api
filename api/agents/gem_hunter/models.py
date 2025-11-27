from pydantic import BaseModel, Field


class Justification(BaseModel):
    """Structured justification for the agent's recommendation."""

    understanding: str = Field(
        description="Explanation of what the agent understood about the user's playlist vibe (Part 1)"
    )
    selection: str = Field(
        description="Explanation of how the selected tracks match that vibe (Part 2)"
    )
