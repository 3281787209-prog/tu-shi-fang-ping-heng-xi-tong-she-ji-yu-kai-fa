from __future__ import annotations

from pydantic import BaseModel

from app.schemas.common import ORMModel


class ModelStageOut(BaseModel):
    stage_key: str
    full: str
    cavity: str
    slices: dict


class ModelMetricOut(ORMModel):
    id: int
    stage_key: str
    source_file: str
    scalar_key: str
    range_min: float
    range_max: float


class DashboardSummary(BaseModel):
    project_count: int
    pending_form_count: int
    stage_count: int
    displacement_max: float | None = None
    stress_max: float | None = None

