from pydantic import BaseModel


class StreamRequest(BaseModel):
    track_id: int
