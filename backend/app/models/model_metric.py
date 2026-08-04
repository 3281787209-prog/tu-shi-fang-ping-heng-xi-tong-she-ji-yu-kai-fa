from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ModelStageMetric(Base):
    """
    从 VTP 文件头部 RangeMin/RangeMax 提取的真实物理量范围。
    这类数据“来自真实模型文件”，不需要人为编造。
    """

    __tablename__ = "model_stage_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    stage_key: Mapped[str] = mapped_column(String(64), index=True, nullable=False)  # exac_1
    source_file: Mapped[str] = mapped_column(String(256), nullable=False)  # full_model.vtp
    scalar_key: Mapped[str] = mapped_column(String(128), index=True, nullable=False)  # TotalDisplacement...
    range_min: Mapped[float] = mapped_column(Float, nullable=False)
    range_max: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

