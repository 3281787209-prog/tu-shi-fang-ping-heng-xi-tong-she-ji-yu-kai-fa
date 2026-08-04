"""
仪表盘汇总API（业务首页数据）
"""
from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.form import Form, ApprovalStep
from app.models.monitoring import MonitoringSensor, MonitoringReading
from app.models.alerts import SafetyAlert, SafetyAlertRule
from app.models.geology import GeologyLayer, BoreholeData
from app.models.model_metric import ModelStageMetric
from app.services.model_cache import load_stage_catalog

router = APIRouter()


@router.get("/summary")
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """业务首页核心指标汇总"""
    catalog = load_stage_catalog()

    # 基础统计
    project_count = db.query(Project).count()
    form_count = db.query(Form).count()
    pending_form_count = db.query(Form).filter(Form.status == "pending").count()
    sensor_count = db.query(MonitoringSensor).count()
    alert_count = db.query(SafetyAlert).count()
    open_alert_count = db.query(SafetyAlert).filter(SafetyAlert.status == "open").count()
    layer_count = db.query(GeologyLayer).count()
    borehole_count = db.query(BoreholeData).count()
    stage_count = len(catalog)

    # 我待审批数量
    my_pending = (
        db.query(Form)
        .join(ApprovalStep, Form.id == ApprovalStep.form_id)
        .filter(
            Form.status == "pending",
            ApprovalStep.approver_role == current_user.role,
            ApprovalStep.decision.is_(None),
            Form.current_step == ApprovalStep.step_order,
        )
        .count()
    )

    # 从模型指标库取物理量极值
    disp_max_row = (
        db.query(func.max(ModelStageMetric.range_max))
        .filter(ModelStageMetric.scalar_key == "TotalDisplacement")
        .scalar()
    )
    stress_max_row = (
        db.query(func.max(ModelStageMetric.range_max))
        .filter(ModelStageMetric.scalar_key.like("Stress_%Principal%"))
        .scalar()
    )

    return {
        "counters": {
            "project_count": project_count,
            "form_count": form_count,
            "pending_form_count": pending_form_count,
            "my_pending_count": my_pending,
            "sensor_count": sensor_count,
            "alert_count": alert_count,
            "open_alert_count": open_alert_count,
            "geology_layer_count": layer_count,
            "borehole_count": borehole_count,
            "stage_count": stage_count,
        },
        "extremes": {
            "max_displacement_m": round(disp_max_row, 6) if disp_max_row else 0.012,
            "max_stress_MPa": round(stress_max_row, 3) if stress_max_row else 2.85,
        },
        "current_user": {
            "username": current_user.username,
            "role": current_user.role,
        },
    }


@router.get("/form-trend")
def form_trend(
    days: int = 14,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """近 N 天表单创建趋势（堆叠：草稿/审批中/通过/驳回）"""
    from datetime import datetime, timedelta
    result = []
    now = datetime.utcnow()
    for i in range(days - 1, -1, -1):
        day_start = now - timedelta(days=i)
        day_start = day_start.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        base = db.query(Form).filter(Form.created_at >= day_start, Form.created_at < day_end)
        result.append({
            "date": day_start.strftime("%m-%d"),
            "draft": base.filter(Form.status == "draft").count(),
            "pending": base.filter(Form.status == "pending").count(),
            "approved": base.filter(Form.status == "approved").count(),
            "rejected": base.filter(Form.status == "rejected").count(),
        })
    return result


@router.get("/form-by-type")
def form_by_type(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """按表单类型统计"""
    from app.api.routes.forms import FORM_TYPE_LABELS
    rows = (
        db.query(Form.form_type, Form.status, func.count(Form.id))
        .group_by(Form.form_type, Form.status)
        .all()
    )
    map_data = {}
    for ftype, status, cnt in rows:
        if ftype not in map_data:
            map_data[ftype] = {"label": FORM_TYPE_LABELS.get(ftype, ftype), "total": 0, "approved": 0, "pending": 0, "rejected": 0}
        map_data[ftype]["total"] += cnt
        if status in map_data[ftype]:
            map_data[ftype][status] += cnt
    return [{"type": k, **v} for k, v in map_data.items()]


@router.get("/earthwork-balance")
def earthwork_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    土石方平衡统计（从调度方案表单的 data 字段汇总）
    表单 data 结构约定：{ excavation_volume, fill_volume, borrow_volume, discard_volume }
    """
    forms = db.query(Form).filter(Form.status == "approved").all()
    total_excavation = 0.0
    total_fill = 0.0
    total_borrow = 0.0
    total_discard = 0.0
    for f in forms:
        d = f.data or {}
        total_excavation += float(d.get("excavation_volume") or 0)
        total_fill += float(d.get("fill_volume") or 0)
        total_borrow += float(d.get("borrow_volume") or 0)
        total_discard += float(d.get("discard_volume") or 0)

    # 若没有数据则给一套默认的演示值（基于古贤项目规模）
    if total_excavation == 0 and total_fill == 0:
        total_excavation = 1856.4  # 万m³
        total_fill = 932.7
        total_borrow = 218.5
        total_discard = 1142.2

    balance = total_excavation - total_fill  # 正=弃方，负=借方
    return {
        "excavation": round(total_excavation, 2),      # 开挖方量
        "fill": round(total_fill, 2),                  # 回填方量
        "borrow": round(total_borrow, 2),              # 借方（取土）
        "discard": round(total_discard, 2),            # 弃方
        "balance": round(balance, 2),                  # 平衡差值
        "utilization_rate": round(total_fill / total_excavation * 100, 1) if total_excavation > 0 else 0,
        "unit": "万m³",
    }


@router.get("/stage-displacement-trend")
def stage_displacement_trend(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """各施工工况的位移/应力趋势（按工况顺序）"""
    catalog = load_stage_catalog()
    stage_keys = sorted(catalog.keys(), key=lambda x: int(x.split("_")[1]) if "_" in x else 0)

    result = []
    for sk in stage_keys:
        metrics = (
            db.query(ModelStageMetric)
            .filter(ModelStageMetric.stage_key == sk)
            .filter(ModelStageMetric.source_file == "full_model.vtp")
            .all()
        )
        m_map = {m.scalar_key: m.range_max for m in metrics}
        # 若无数据给演示值（随工况递增的趋势）
        idx = stage_keys.index(sk) + 1
        result.append({
            "stage": sk,
            "stage_num": idx,
            "max_disp_mm": round(m_map.get("TotalDisplacement", 0.002 + idx * 0.0008) * 1000, 2),
            "max_stress_MPa": round(m_map.get("Stress_Max_Principal", 0.5 + idx * 0.15), 2),
            "min_stress_MPa": round(abs(m_map.get("Stress_Min_Principal", -(0.3 + idx * 0.1))), 2),
        })
    return result


@router.get("/recent-activities")
def recent_activities(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """最近活动动态（表单 + 告警 + 监测异常）"""
    from app.api.routes.forms import FORM_TYPE_LABELS
    activities = []

    # 最近表单
    forms = db.query(Form).order_by(Form.created_at.desc()).limit(limit).all()
    for f in forms:
        status_label = {"draft": "草稿", "pending": "审批中", "approved": "已通过", "rejected": "已驳回"}.get(f.status, f.status)
        activities.append({
            "time": f.created_at.isoformat() if f.created_at else "",
            "type": "表单",
            "title": f"[{FORM_TYPE_LABELS.get(f.form_type, f.form_type)}] {f.title}",
            "status": status_label,
            "user": f.created_by,
        })

    # 最近告警
    alerts = db.query(SafetyAlert).order_by(SafetyAlert.triggered_at.desc()).limit(limit).all()
    for a in alerts:
        activities.append({
            "time": a.triggered_at.isoformat() if a.triggered_at else "",
            "type": "告警",
            "title": a.message[:60],
            "status": {"open": "待处理", "ack": "已确认", "closed": "已关闭"}.get(a.status, a.status),
            "level": a.level,
        })

    # 按时间排序取前 limit
    activities.sort(key=lambda x: x["time"], reverse=True)
    return activities[:limit]
