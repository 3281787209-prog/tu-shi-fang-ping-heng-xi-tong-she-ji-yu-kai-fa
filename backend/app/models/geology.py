from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class GeologyLayer(Base):
    __tablename__ = "geology_layers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    layer_type: Mapped[str] = mapped_column(String(64), default="stratum")  # stratum|fault|excavation|bedrock|slip_zone
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 关联三维演示工况（如 exac_1）；真实项目可扩展为多个 stage / 多套模型。
    stage_key: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # 附加属性（厚度、岩性、风化程度、承载力特征值 fak 等）
    properties: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BoreholeData(Base):
    """钻孔数据：孔位坐标、深度、分层柱状图等"""
    __tablename__ = "borehole_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)

    hole_code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    # 孔口三维坐标
    x: Mapped[float | None] = mapped_column(Integer, nullable=True)
    y: Mapped[float | None] = mapped_column(Integer, nullable=True)
    z: Mapped[float | None] = mapped_column(Integer, nullable=True)
    depth: Mapped[float | None] = mapped_column(Integer, nullable=True)  # 钻孔深度 m

    # 分层信息：[{depth_from, depth_to, stratum_name, lithology, weathering, fak_kPa}]
    stratigraphy: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # 土样/岩样试验：{"sample_1": {w_n, e, c_kPa, phi_deg, ...}}
    soil_samples: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
