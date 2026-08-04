from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MonitoringSensor(Base):
    __tablename__ = "monitoring_sensors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)

    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    sensor_type: Mapped[str] = mapped_column(String(64), default="displacement")  # displacement|stress|water_level|etc

    x: Mapped[float | None] = mapped_column(Float, nullable=True)
    y: Mapped[float | None] = mapped_column(Float, nullable=True)
    z: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MonitoringReading(Base):
    __tablename__ = "monitoring_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sensor_id: Mapped[int] = mapped_column(ForeignKey("monitoring_sensors.id"), index=True)

    field_key: Mapped[str] = mapped_column(String(128), default="value")  # TotalDisplacement 等
    value: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

