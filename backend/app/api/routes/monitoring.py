"""
监测信息API路由（传感器 + 读数 + 趋势）
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.api.deps import get_current_user, require_role
from app.models.user import User
from app.models.monitoring import MonitoringSensor, MonitoringReading

router = APIRouter()

SENSOR_TYPE_LABELS = {
    "displacement": "位移计",
    "stress": "应力计",
    "water_level": "水位计",
    "inclinometer": "测斜仪",
    "piezometer": "渗压计",
    "strain_gauge": "应变计",
    "temperature": "温度计",
    "vibration": "振动传感器",
}

FIELD_KEY_LABELS = {
    "TotalDisplacement": "总位移",
    "X_Disp": "X向位移",
    "Y_Disp": "Y向位移",
    "Z_Disp": "Z向位移",
    "Stress_Max_Principal": "最大主应力",
    "Stress_Min_Principal": "最小主应力",
    "Stress_XX": "σxx 正应力",
    "Stress_YY": "σyy 正应力",
    "Stress_ZZ": "σzz 正应力",
    "PorePressure": "孔隙水压力",
    "WaterLevel": "水位",
    "Temperature": "温度",
}


@router.get("/sensors/types")
def get_sensor_types():
    """传感器类型字典"""
    return [{"type": k, "label": v} for k, v in SENSOR_TYPE_LABELS.items()]


@router.get("/sensors", response_model=List[Dict[str, Any]])
def list_sensors(
    project_id: Optional[int] = None,
    sensor_type: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取传感器列表"""
    q = db.query(MonitoringSensor)
    if project_id:
        q = q.filter(MonitoringSensor.project_id == project_id)
    if sensor_type:
        q = q.filter(MonitoringSensor.sensor_type == sensor_type)
    if keyword:
        q = q.filter(
            (MonitoringSensor.code.contains(keyword)) |
            (MonitoringSensor.name.contains(keyword))
        )
    rows = q.order_by(MonitoringSensor.id).all()
    result = []
    for s in rows:
        last = (
            db.query(MonitoringReading)
            .filter(MonitoringReading.sensor_id == s.id)
            .order_by(MonitoringReading.timestamp.desc())
            .first()
        )
        result.append({
            "id": s.id, "project_id": s.project_id, "code": s.code, "name": s.name,
            "sensor_type": s.sensor_type,
            "sensor_type_label": SENSOR_TYPE_LABELS.get(s.sensor_type, s.sensor_type),
            "x": s.x, "y": s.y, "z": s.z,
            "last_value": last.value if last else None,
            "last_field": last.field_key if last else None,
            "last_time": last.timestamp.isoformat() if last and last.timestamp else None,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        })
    return result


@router.get("/sensors/{sensor_id}")
def get_sensor_detail(
    sensor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """传感器详情"""
    s = db.query(MonitoringSensor).filter(MonitoringSensor.id == sensor_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="传感器不存在")
    # 统计指标
    last_reading = (
        db.query(MonitoringReading)
        .filter(MonitoringReading.sensor_id == sensor_id)
        .order_by(MonitoringReading.timestamp.desc())
        .first()
    )
    reading_count = db.query(func.count(MonitoringReading.id)).filter(MonitoringReading.sensor_id == sensor_id).scalar()
    avg_val = (
        db.query(func.avg(MonitoringReading.value))
        .filter(MonitoringReading.sensor_id == sensor_id)
        .scalar()
    ) or 0
    max_val = (
        db.query(func.max(MonitoringReading.value))
        .filter(MonitoringReading.sensor_id == sensor_id)
        .scalar()
    ) or 0
    min_val = (
        db.query(func.min(MonitoringReading.value))
        .filter(MonitoringReading.sensor_id == sensor_id)
        .scalar()
    ) or 0
    return {
        "id": s.id, "project_id": s.project_id, "code": s.code, "name": s.name,
        "sensor_type": s.sensor_type,
        "sensor_type_label": SENSOR_TYPE_LABELS.get(s.sensor_type, s.sensor_type),
        "x": s.x, "y": s.y, "z": s.z,
        "reading_count": reading_count,
        "last_value": last_reading.value if last_reading else None,
        "last_field": last_reading.field_key if last_reading else None,
        "last_time": last_reading.timestamp.isoformat() if last_reading and last_reading.timestamp else None,
        "avg_value": round(avg_val, 4),
        "max_value": round(max_val, 4),
        "min_value": round(min_val, 4),
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


@router.post("/sensors")
def create_sensor(
    body: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager", "engineer")),
):
    """创建传感器"""
    if db.query(MonitoringSensor).filter(MonitoringSensor.code == body["code"]).first():
        raise HTTPException(status_code=400, detail="传感器编号已存在")
    s = MonitoringSensor(
        project_id=body.get("project_id"),
        code=body["code"],
        name=body["name"],
        sensor_type=body.get("sensor_type", "displacement"),
        x=body.get("x"), y=body.get("y"), z=body.get("z"),
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return {"id": s.id, "message": "创建成功"}


@router.put("/sensors/{sensor_id}")
def update_sensor(
    sensor_id: int,
    body: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager", "engineer")),
):
    s = db.query(MonitoringSensor).filter(MonitoringSensor.id == sensor_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="传感器不存在")
    for f in ["project_id", "code", "name", "sensor_type", "x", "y", "z"]:
        if f in body:
            setattr(s, f, body[f])
    db.commit()
    return {"message": "更新成功"}


@router.delete("/sensors/{sensor_id}")
def delete_sensor(
    sensor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    s = db.query(MonitoringSensor).filter(MonitoringSensor.id == sensor_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="传感器不存在")
    db.delete(s)
    db.commit()
    return {"message": "删除成功"}


# ========== 读数 ==========

@router.get("/sensors/{sensor_id}/readings")
def get_sensor_readings(
    sensor_id: int,
    hours: int = Query(24, description="最近多少小时数据"),
    interval: Optional[str] = Query(None, description="聚合粒度: hour/day，None=原始数据"),
    limit: int = 5000,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取传感器读数时间序列"""
    s = db.query(MonitoringSensor).filter(MonitoringSensor.id == sensor_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="传感器不存在")
    start = datetime.utcnow() - timedelta(hours=hours)

    q = db.query(MonitoringReading).filter(
        MonitoringReading.sensor_id == sensor_id,
        MonitoringReading.timestamp >= start,
    ).order_by(MonitoringReading.timestamp)

    rows = q.limit(limit).all()

    data = [{
        "time": r.timestamp.isoformat() if r.timestamp else "",
        "field_key": r.field_key,
        "field_label": FIELD_KEY_LABELS.get(r.field_key, r.field_key),
        "value": r.value,
    } for r in rows]

    # 统计
    if data:
        values = [d["value"] for d in data]
        stats = {
            "count": len(values),
            "avg": round(sum(values) / len(values), 4),
            "max": round(max(values), 4),
            "min": round(min(values), 4),
            "latest": values[-1],
        }
    else:
        stats = {"count": 0, "avg": 0, "max": 0, "min": 0, "latest": 0}

    return {
        "sensor": {"id": s.id, "code": s.code, "name": s.name, "type": s.sensor_type},
        "time_range": {"start": start.isoformat(), "end": datetime.utcnow().isoformat()},
        "stats": stats,
        "data": data,
    }


@router.post("/sensors/{sensor_id}/readings")
def add_sensor_reading(
    sensor_id: int,
    body: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager", "engineer")),
):
    """新增一条传感器读数"""
    s = db.query(MonitoringSensor).filter(MonitoringSensor.id == sensor_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="传感器不存在")
    reading = MonitoringReading(
        sensor_id=sensor_id,
        field_key=body.get("field_key", "value"),
        value=float(body["value"]),
        timestamp=datetime.fromisoformat(body["timestamp"]) if body.get("timestamp") else datetime.utcnow(),
    )
    db.add(reading)
    # 触发告警规则检查
    from app.api.routes.alerts import _check_rules_for_reading
    _check_rules_for_reading(db, s.project_id, reading)
    db.commit()
    return {"message": "读数已入库"}


@router.post("/readings/batch")
def batch_add_readings(
    body: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager", "engineer")),
):
    """批量导入传感器读数"""
    items = body.get("items", [])
    added = 0
    for item in items:
        code = item.get("sensor_code")
        if not code:
            continue
        s = db.query(MonitoringSensor).filter(MonitoringSensor.code == code).first()
        if not s:
            continue
        r = MonitoringReading(
            sensor_id=s.id,
            field_key=item.get("field_key", "value"),
            value=float(item["value"]),
            timestamp=datetime.fromisoformat(item["timestamp"]) if item.get("timestamp") else datetime.utcnow(),
        )
        db.add(r)
        added += 1
    db.commit()
    return {"message": f"成功导入 {added} 条读数"}


# ========== 监测概览 ==========

@router.get("/overview")
def monitoring_overview(
    project_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """监测信息总览"""
    q_sensor = db.query(MonitoringSensor)
    if project_id:
        q_sensor = q_sensor.filter(MonitoringSensor.project_id == project_id)
    total_sensors = q_sensor.count()

    # 按类型统计
    by_type_rows = (
        q_sensor.with_entities(
            MonitoringSensor.sensor_type, func.count(MonitoringSensor.id)
        )
        .group_by(MonitoringSensor.sensor_type)
        .all()
    )
    by_type = [
        {"type": t, "label": SENSOR_TYPE_LABELS.get(t, t), "count": c}
        for t, c in by_type_rows
    ]

    # 最近 24 小时读数数量
    start = datetime.utcnow() - timedelta(hours=24)
    reading_24h = db.query(func.count(MonitoringReading.id)).filter(
        MonitoringReading.timestamp >= start
    ).scalar() or 0

    return {
        "total_sensors": total_sensors,
        "by_type": by_type,
        "reading_count_24h": reading_24h,
    }
