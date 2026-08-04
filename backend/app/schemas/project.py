from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.common import ORMModel


class ProjectCreate(BaseModel):
    name: str
    location: Optional[str] = None
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None


class ProjectOut(ORMModel):
    id: int
    name: str
    location: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None
