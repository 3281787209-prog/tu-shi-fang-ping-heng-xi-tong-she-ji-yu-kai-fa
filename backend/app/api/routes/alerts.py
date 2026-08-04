"""
安全预警API路由（规则 + 告警 + 自动触发检查）
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.api.deps import get_current_user, require_role
from app.models.user import User
from app.models.alerts import SafetyAlertRule, SafetyAlert
from app.models.monitoring import MonitoringReading, MonitoringSensor

router = APIRouter()

LEVEL_LABELS = {
    "info": "提示",
    "warning": "警告",
    "critical": "严重",
}

LEVEL_COLORS = {
    "info": "#3b82f6",
    "warning": "#f59e0b",
    "critical": "#ef4444",
}

STATUS_LABELS = {
    "open": "待处理",
    "ack": "已确认",
    "closed": "已关闭",
}

COMPARATOR_LABELS = {
    ">": "大于",
    ">=": "大于等于",
    "<": "小于",
    "<=": "小于等于",
}


def _check_rules_for_reading(db: Session, project_id: Optional[int], reading: MonitoringReading):
    """检查新读数是否触发任何规则（内部函数，被监测路由调用）"""
    if project_id is None:
        return
    rules = db.query(SafetyAlertRule).filter(SafetyAlertRule.project_id == project_id).all()
    for rule in rules:
        if rule.field_key != reading.field_key:
            continue
        triggered = False
        v = reading.value
        if rule.comparator == ">" and v > rule.threshold:
            triggered = True
        elif rule.comparator == ">=" and v >= rule.threshold:
            triggered = True
        elif rule.comparator == "<" and v < rule.threshold:
            triggered = True
        elif rule.comparator == "<=" and v <= rule.threshold:
            triggered = True
        if triggered:
            # 避免短时间内重复告警（同规则同小时最多1条）
            hour_start = reading.timestamp.replace(minute=0, second=0, microsecond=0) if reading.timestamp else datetime.utcnow().replace(minute=0, second=0, microsecond=0)
            hour_end = hour_start + timedelta(hours=1)
            exist = (
                db.query(SafetyAlert)
                .filter(
                    SafetyAlert.rule_id == rule.id,
                    SafetyAlert.triggered_at >= hour_start,
                    SafetyAlert.triggered_at < hour_end,
                )
                .first()
            )
            if not exist:
                sensor = db.query(MonitoringSensor).filter(MonitoringSensor.id == reading.sensor_id).first()
                msg = (
                    f"[{LEVEL_LABELS.get(rule.level, rule.level)}] 传感器 {sensor.code if sensor else '#'+str(reading.sensor_id)} "
                    f"{rule.name} 触发: {reading.field_key} = {v:.4f} "
                    f"{COMPARATOR_LABELS.get(rule.comparator, rule.comparator)} {rule.threshold}"
                )
                alert = SafetyAlert(
                    project_id=project_id,
                    rule_id=rule.id,
                    level=rule.level,
                    message=msg,
                    status="open",
                    triggered_at=reading.timestamp or datetime.utcnow(),
                )
                db.add(alert)


# ========== 预警规则 ==========

@router.get("/rules", response_model=List[Dict[str, Any]])
def list_rules(
    project_id: Optional[int] = None,
    field_key: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取预警规则列表"""
    q = db.query(SafetyAlertRule)
    if project_id:
        q = q.filter(SafetyAlertRule.project_id == project_id)
    if field_key:
        q = q.filter(SafetyAlertRule.field_key == field_key)
    rows = q.order_by(SafetyAlertRule.created_at.desc()).all()
    return [{
        "id": r.id, "project_id": r.project_id, "name": r.name,
        "field_key": r.field_key, "comparator": r.comparator,
        "comparator_label": COMPARATOR_LABELS.get(r.comparator, r.comparator),
        "threshold": r.threshold, "level": r.level,
        "level_label": LEVEL_LABELS.get(r.level, r.level),
        "level_color": LEVEL_COLORS.get(r.level, "#666"),
        "created_at": r.created_at.isoformat() if r.created_at else None,
    } for r in rows]


@router.post("/rules")
def create_rule(
    body: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager", "engineer")),
):
    """创建预警规则"""
    r = SafetyAlertRule(
        project_id=body.get("project_id"),
        name=body["name"],
        field_key=body["field_key"],
        comparator=body.get("comparator", ">"),
        threshold=float(body["threshold"]),
        level=body.get("level", "warning"),
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return {"id": r.id, "message": "规则已创建"}


@router.put("/rules/{rule_id}")
def update_rule(
    rule_id: int,
    body: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager", "engineer")),
):
    r = db.query(SafetyAlertRule).filter(SafetyAlertRule.id == rule_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="规则不存在")
    for f in ["project_id", "name", "field_key", "comparator", "threshold", "level"]:
        if f in body:
            val = body[f]
            if f == "threshold":
                val = float(val)
            setattr(r, f, val)
    db.commit()
    return {"message": "规则已更新"}


@router.delete("/rules/{rule_id}")
def delete_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    r = db.query(SafetyAlertRule).filter(SafetyAlertRule.id == rule_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="规则不存在")
    db.delete(r)
    db.commit()
    return {"message": "规则已删除"}


# ========== 告警记录 ==========

@router.get("/alerts", response_model=List[Dict[str, Any]])
def list_alerts(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    level: Optional[str] = None,
    days: int = Query(30, description="最近多少天"),
    skip: int = 0,
    limit: int = 200,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取告警记录列表"""
    start = datetime.utcnow() - timedelta(days=days)
    q = db.query(SafetyAlert).filter(SafetyAlert.triggered_at >= start)
    if project_id:
        q = q.filter(SafetyAlert.project_id == project_id)
    if status:
        q = q.filter(SafetyAlert.status == status)
    if level:
        q = q.filter(SafetyAlert.level == level)
    rows = q.order_by(SafetyAlert.triggered_at.desc()).offset(skip).limit(limit).all()
    return [{
        "id": a.id, "project_id": a.project_id, "rule_id": a.rule_id,
        "level": a.level, "level_label": LEVEL_LABELS.get(a.level, a.level),
        "level_color": LEVEL_COLORS.get(a.level, "#666"),
        "message": a.message,
        "status": a.status, "status_label": STATUS_LABELS.get(a.status, a.status),
        "triggered_at": a.triggered_at.isoformat() if a.triggered_at else None,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    } for a in rows]


@router.get("/alerts/stats")
def alert_stats(
    project_id: Optional[int] = None,
    days: int = 14,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """告警统计"""
    start = datetime.utcnow() - timedelta(days=days)
    q = db.query(SafetyAlert).filter(SafetyAlert.triggered_at >= start)
    if project_id:
        q = q.filter(SafetyAlert.project_id == project_id)

    total = q.count()
    open_count = q.filter(SafetyAlert.status == "open").count()
    ack_count = q.filter(SafetyAlert.status == "ack").count()
    closed_count = q.filter(SafetyAlert.status == "closed").count()
    critical_count = q.filter(SafetyAlert.level == "critical").count()
    warning_count = q.filter(SafetyAlert.level == "warning").count()
    info_count = q.filter(SafetyAlert.level == "info").count()

    # 按天趋势
    daily = []
    for i in range(days - 1, -1, -1):
        day_start = datetime.utcnow() - timedelta(days=i)
        day_start = day_start.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        dq = q.filter(SafetyAlert.triggered_at >= day_start, SafetyAlert.triggered_at < day_end)
        daily.append({
            "date": day_start.strftime("%m-%d"),
            "critical": dq.filter(SafetyAlert.level == "critical").count(),
            "warning": dq.filter(SafetyAlert.level == "warning").count(),
            "info": dq.filter(SafetyAlert.level == "info").count(),
        })

    return {
        "summary": {
            "total": total, "open": open_count, "ack": ack_count, "closed": closed_count,
            "critical": critical_count, "warning": warning_count, "info": info_count,
        },
        "daily": daily,
    }


@router.post("/alerts/{alert_id}/ack")
def ack_alert(
    alert_id: int,
    body: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager", "engineer")),
):
    """确认告警"""
    a = db.query(SafetyAlert).filter(SafetyAlert.id == alert_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="告警不存在")
    a.status = "ack"
    db.commit()
    return {"message": "告警已确认"}


@router.post("/alerts/{alert_id}/close")
def close_alert(
    alert_id: int,
    body: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager", "engineer")),
):
    """关闭告警"""
    a = db.query(SafetyAlert).filter(SafetyAlert.id == alert_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="告警不存在")
    a.status = "closed"
    db.commit()
    return {"message": "告警已关闭"}


@router.post("/alerts/check-all")
def run_full_alert_check(
    project_id: Optional[int] = None,
    hours: int = Query(1, description="检查最近多少小时的读数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager")),
):
    """手动触发全量告警检查（巡检）"""
    start = datetime.utcnow() - timedelta(hours=hours)
    q = db.query(MonitoringReading).filter(MonitoringReading.timestamp >= start)
    readings = q.order_by(MonitoringReading.timestamp).all()
    triggered = 0
    for r in readings:
        sensor = db.query(MonitoringSensor).filter(MonitoringSensor.id == r.sensor_id).first()
        if not sensor:
            continue
        pid = project_id or sensor.project_id
        _check_rules_for_reading(db, pid, r)
        triggered += 1
    db.commit()
    return {"message": f"检查了 {len(readings)} 条读数，告警已同步更新"}
