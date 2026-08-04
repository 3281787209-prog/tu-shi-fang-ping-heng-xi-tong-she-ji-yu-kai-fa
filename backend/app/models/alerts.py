from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SafetyAlertRule(Base):
    __tablename__ = "safety_alert_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    field_key: Mapped[str] = mapped_column(String(128), nullable=False)  # e.g. TotalDisplacement
    comparator: Mapped[str] = mapped_column(String(8), default=">")  # >|>=|<|<=
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    level: Mapped[str] = mapped_column(String(16), default="warning")  # info|warning|critical

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SafetyAlert(Base):
    __tablename__ = "safety_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    rule_id: Mapped[int | None] = mapped_column(ForeignKey("safety_alert_rules.id"), nullable=True)

    level: Mapped[str] = mapped_column(String(16), default="warning")  # info|warning|critical
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="open")  # open|ack|closed
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
