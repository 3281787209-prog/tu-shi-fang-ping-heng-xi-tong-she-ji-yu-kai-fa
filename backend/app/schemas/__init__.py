from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


# ============ 认证 ============
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(ORMModel):
    id: int
    username: str
    role: str


class UserCreate(BaseModel):
    username: str
    password: str
    role: Optional[str] = "user"


class UserUpdate(BaseModel):
    password: Optional[str] = None
    role: Optional[str] = None


# ============ 项目 ============
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


# ============ 表单审批 ============
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
    created_at: Optional[datetime] = None


class FormListOut(FormOut):
    approvals: list = []
    form_type_label: Optional[str] = None


class ApprovalDecision(BaseModel):
    decision: str  # approved|rejected
    comment: Optional[str] = None


class ApprovalStepOut(ORMModel):
    id: int
    form_id: int
    step_order: int
    approver_role: str
    decision: Optional[str] = None
    comment: Optional[str] = None
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None


# ============ 模型 ============
class ModelStageOut(BaseModel):
    stage_key: str
    full: Optional[str] = None
    cavity: Optional[str] = None
    slices: dict = {}


class ModelMetricOut(ORMModel):
    id: int
    stage_key: str
    source_file: str
    scalar_key: str
    range_min: float
    range_max: float
    created_at: Optional[datetime] = None


class DashboardSummary(BaseModel):
    project_count: int
    pending_form_count: int
    stage_count: int
    displacement_max: Optional[float] = None
    stress_max: Optional[float] = None
