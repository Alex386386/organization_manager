from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ActivityBase(BaseModel):
    name: str


class ActivityUpdate(ActivityBase):
    name: Optional[str] = None
    parent_id: Optional[int] = None


class ActivityCreate(ActivityBase):
    parent_id: Optional[int] = None


class ActivityDB(ActivityBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    level: int
    create_date: datetime
    update_date: datetime
