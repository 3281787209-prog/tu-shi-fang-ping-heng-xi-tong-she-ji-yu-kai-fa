from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Form(Base):
    """
    通用表单：用于“方案调度、变更、监测异常上报、参数计算申请”等。
    具体字段放在 data 里，便于甲方后续扩展。
    """

    __tablename__ = "forms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)

    form_type: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g. schedule_plan
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)  # draft|pending|approved|rejected
    current_step: Mapped[int] = mapped_column(Integer, default=0)

    data: Mapped[dict] = mapped_column(SQLITE_JSON, default=dict)
    created_by: Mapped[str] = mapped_column(String(64), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    approvals: Mapped[list["ApprovalStep"]] = relationship(
        back_populates="form", cascade="all, delete-orphan"
    )


class ApprovalStep(Base):
    __tablename__ = "approval_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    form_id: Mapped[int] = mapped_column(ForeignKey("forms.id"), index=True)
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)

    approver_role: Mapped[str] = mapped_column(String(32), default="manager")  # 简化：按角色
    decision: Mapped[str | None] = mapped_column(String(16), nullable=True)  # approved|rejected|null
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    form: Mapped[Form] = relationship(back_populates="approvals")

