from pydantic import BaseModel


class Notification(BaseModel):
    sender: str
    content: str
    timestamp: int
