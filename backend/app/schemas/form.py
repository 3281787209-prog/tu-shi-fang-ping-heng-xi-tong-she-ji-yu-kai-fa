from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Any

from pydantic import BaseModel

from app.schemas.common import ORMModel


class FormCreate(BaseModel):
    project_id: Optional[int] = None
    form_type: str
    title: str
    data: dict = {}


class FormOut(ORMModel):
    id: int
    project_id: Optional[int] = None
    form_type: str
    title: str
    status: str
    current_step: int
    data: dict
    created_by: str
    created_at: datetime | None = None


class FormListOut(FormOut):
    approvals: List[Any] = []
    form_type_label: Optional[str] = None


class ApprovalDecision(BaseModel):
    decision: str  # approved|rejected
    comment: str | None = None


class ApprovalStepOut(ORMModel):
    id: int
    form_id: int
    step_order: int
    approver_role: str
    decision: str | None = None
    comment: str | None = None
    decided_by: str | None = None
    decided_at: datetime | None = None
