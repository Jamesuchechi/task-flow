from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AttachmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    owner_id: int
    filename: str
    content_type: str
    size_bytes: int
    created_at: datetime
