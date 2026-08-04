"""
数据库初始化 & 种子数据脚本
运行: python -m app.init_db
功能：
1. 创建所有表
2. 注入默认用户（admin/manager/engineer/user）
3. 创建示例项目（古贤黄河水利枢纽）
4. 注入地质图层、钻孔数据
5. 配置传感器与模拟读数
6. 配置安全预警规则
7. 创建示例表单（土石方调度方案等）
"""
from __future__ import annotations

import json
import math
import random
from datetime import datetime, timedelta
from pathlib import Path

from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.core import security
from app.core.config import settings
from app.models import (
    User, Project, Form, ApprovalStep,
    GeologyLayer, BoreholeData,
    MonitoringSensor, MonitoringReading,
    SafetyAlertRule, SafetyAlert,
    ModelStageMetric,
)
from app.services.model_cache import load_stage_catalog, extract_ranges_from_vtp, get_model_cache_dir


DEFAULT_USERS = [
    {"username": "admin", "password": "admin123", "role": "admin"},
    {"username": "manager", "password": "manager123", "role": "manager"},
    {"username": "engineer", "password": "engineer123", "role": "engineer"},
    {"username": "user01", "password": "user123", "role": "user"},
]


def seed_users(db):
    for u in DEFAULT_USERS:
        if db.query(User).filter(User.username == u["username"]).first():
            continue
        db.add(User(
            username=u["username"],
            hashed_password=security.hash_password(u["password"]),
            role=u["role"],
        ))
    db.commit()
    print("[OK] 默认用户已初始化: admin/admin123, manager/manager123, engineer/engineer123, user01/user123")


def seed_project(db):
    if db.query(Project).count() > 0:
        return
    p = Project(
        name="古贤黄河水利枢纽-坝肩左岸边坡开挖工程",
        location="山西省临汾市吉县 / 陕西省延安市宜川县 黄河干流",
        description=(
            "古贤水利枢纽工程位于黄河北干流下段，坝址右岸为陕西省宜川县，左岸为山西省吉县。"
            "本项目为坝肩左岸边坡开挖与支护工程，涉及土石方开挖量约 1856 万 m³，"
            "最大开挖深度约 85m，边坡高 120~180m。采用分层分段开挖、随挖随护的施工方案，"
            "共分 23 步开挖工况（exac_1 ~ exac_23）。"
        ),
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    print(f"[OK] 示例项目已创建: {p.name} (id={p.id})")
    return p


def seed_geology(db, project):
    if db.query(GeologyLayer).count() > 0:
        return
    layers = [
        GeologyLayer(project_id=project.id, name="① 素填土层(Qml)", layer_type="stratum",
                     stage_key="exac_1", description="黄褐色，稍湿，松散~稍密，主要成分为粉土，含植物根系。层厚 1.5~3.2m。",
                     properties={"thickness_m": 2.4, "lithology": "粉土", "weathering": "无", "fak_kPa": 120, "gamma_kN_m3": 18.5}),
        GeologyLayer(project_id=project.id, name="② 黄土状粉土层(Q3eol)", layer_type="stratum",
                     stage_key="exac_1", description="浅灰黄色，大孔结构，垂直节理发育，具湿陷性。层厚 8~15m。",
                     properties={"thickness_m": 11.5, "lithology": "黄土状粉土", "weathering": "无", "fak_kPa": 180, "gamma_kN_m3": 17.8, "collapsibility": "II级(中等)"}),
        GeologyLayer(project_id=project.id, name="③ 古土壤层(Q2el)", layer_type="stratum",
                     stage_key="exac_1", description="棕红色，含钙质结核及菌丝体，结构致密。层厚 3~6m。",
                     properties={"thickness_m": 4.8, "lithology": "粉质黏土", "weathering": "无", "fak_kPa": 260, "gamma_kN_m3": 19.6}),
        GeologyLayer(project_id=project.id, name="④ 砂岩互层(T2e2)", layer_type="bedrock",
                     stage_key="exac_1", description="灰黄色中细粒砂岩与紫红色泥岩互层，中厚层状构造。",
                     properties={"thickness_m": 42.0, "lithology": "砂岩+泥岩互层", "weathering": "强风化~弱风化", "fak_kPa": 800, "gamma_kN_m3": 24.5, "UCS_MPa": 18.5}),
        GeologyLayer(project_id=project.id, name="⑤ 泥岩夹煤层(T2e1)", layer_type="bedrock",
                     stage_key="exac_1", description="深灰色泥岩为主，夹 3~5 层薄煤层，岩层产状 N15°W/ NE∠8°。",
                     properties={"thickness_m": 65.0, "lithology": "泥岩+煤层", "weathering": "微风化~新鲜", "fak_kPa": 1500, "gamma_kN_m3": 25.2, "UCS_MPa": 32.0}),
        GeologyLayer(project_id=project.id, name="F1 断层破碎带", layer_type="fault",
                     stage_key="exac_1", description="走向 N30°W，倾向 NE，倾角 70°，破碎带宽 2~5m，充填断层泥及角砾。",
                     properties={"strike": "N30°W", "dip_direction": "NE", "dip_angle": 70, "width_m": 3.5, "fak_kPa": 150}),
        GeologyLayer(project_id=project.id, name="L1 潜在滑移带", layer_type="slip_zone",
                     stage_key="exac_12", description="砂岩/泥岩接触面，泥化夹层厚 2~5cm，抗剪强度参数降低明显。",
                     properties={"thickness_cm": 3.5, "c_kPa": 12, "phi_deg": 15.5, "likely_stage": "exac_12"}),
        GeologyLayer(project_id=project.id, name="第12步开挖轮廓面", layer_type="excavation",
                     stage_key="exac_12", description="对应工况 exac_12，开挖至高程约 540m，马道宽度 2m。",
                     properties={"elevation_m": 540, "bench_width_m": 2.0, "slope_ratio": 1.25}),
    ]
    db.add_all(layers)

    # 钻孔数据
    boreholes = []
    hole_positions = [
        ("ZK01", 490, -190, 585, 95),
        ("ZK02", 504, -185, 590, 102),
        ("ZK03", 520, -175, 582, 88),
        ("ZK04", 480, -200, 578, 110),
        ("ZK05", 530, -165, 588, 92),
    ]
    for code, x, y, z, depth in hole_positions:
        stratigraphy = [
            {"depth_from": 0, "depth_to": 2.4, "stratum_name": "①素填土", "lithology": "粉土", "weathering": "", "fak_kPa": 120},
            {"depth_from": 2.4, "depth_to": 13.9, "stratum_name": "②黄土状粉土", "lithology": "粉土", "weathering": "", "fak_kPa": 180},
            {"depth_from": 13.9, "depth_to": 18.7, "stratum_name": "③古土壤", "lithology": "粉质黏土", "weathering": "", "fak_kPa": 260},
            {"depth_from": 18.7, "depth_to": 60.7, "stratum_name": "④砂岩互层", "lithology": "砂岩+泥岩", "weathering": "强~弱风化", "fak_kPa": 800},
            {"depth_from": 60.7, "depth_to": depth, "stratum_name": "⑤泥岩夹煤层", "lithology": "泥岩", "weathering": "微风化", "fak_kPa": 1500},
        ]
        boreholes.append(BoreholeData(
            project_id=project.id, hole_code=code, x=x, y=y, z=z, depth=depth,
            stratigraphy=stratigraphy,
            soil_samples={
                "S-01": {"depth_m": 5.0, "w_n_pct": 18.2, "e": 0.78, "gamma_kN_m3": 19.5, "c_kPa": 22, "phi_deg": 24.5},
                "S-02": {"depth_m": 25.0, "w_n_pct": 5.8, "e": 0.42, "gamma_kN_m3": 24.8, "UCS_MPa": 21.3},
            },
        ))
    db.add_all(boreholes)
    db.commit()
    print(f"[OK] 地质图层 {len(layers)} 个 / 钻孔 {len(boreholes)} 个已创建")


def seed_sensors(db, project):
    if db.query(MonitoringSensor).count() > 0:
        return
    sensors = []
    # 位移计（多点位移计 M1-M6）
    for i, (x, y, z) in enumerate([(500, -180, 570), (504, -185, 545), (510, -190, 520),
                                    (495, -175, 560), (520, -180, 535), (488, -195, 550)], 1):
        sensors.append(MonitoringSensor(
            project_id=project.id, code=f"M{i:02d}", name=f"多点位移计 M{i:02d}",
            sensor_type="displacement", x=x, y=y, z=z,
        ))
    # 应力计（锚索应力计 S1-S4）
    for i, (x, y, z) in enumerate([(502, -183, 560), (508, -188, 540), (515, -182, 525), (498, -192, 555)], 1):
        sensors.append(MonitoringSensor(
            project_id=project.id, code=f"S{i:02d}", name=f"锚索应力计 S{i:02d}",
            sensor_type="stress", x=x, y=y, z=z,
        ))
    # 测斜仪（I1-I2）
    for i, (x, y, z) in enumerate([(505, -186, 585), (512, -178, 582)], 1):
        sensors.append(MonitoringSensor(
            project_id=project.id, code=f"I{i:02d}", name=f"钻孔测斜仪 I{i:02d}",
            sensor_type="inclinometer", x=x, y=y, z=z,
        ))
    # 渗压计（P1-P2）
    for i, (x, y, z) in enumerate([(495, -185, 510), (518, -182, 505)], 1):
        sensors.append(MonitoringSensor(
            project_id=project.id, code=f"P{i:02d}", name=f"孔隙水压力计 P{i:02d}",
            sensor_type="piezometer", x=x, y=y, z=z,
        ))
    # 水位计
    sensors.append(MonitoringSensor(
        project_id=project.id, code="W01", name="地下水位观测井 W01",
        sensor_type="water_level", x=506, y=-195, z=580,
    ))
    db.add_all(sensors)
    db.commit()
    print(f"[OK] 传感器 {len(sensors)} 个已创建")
    return sensors


def seed_readings(db, sensors):
    if db.query(MonitoringReading).count() > 0:
        return
    # 模拟最近 14 天，每 6 小时一条读数
    now = datetime.utcnow()
    readings = []
    for s in sensors:
        field_map = {
            "displacement": ["TotalDisplacement", "X_Disp", "Y_Disp", "Z_Disp"],
            "stress": ["Stress_Max_Principal", "Stress_Min_Principal"],
            "inclinometer": ["X_Disp", "Y_Disp"],
            "piezometer": ["PorePressure"],
            "water_level": ["WaterLevel"],
        }
        fields = field_map.get(s.sensor_type, ["value"])
        sid = int(s.code[1:]) if s.code[1:].isdigit() else 1
        for h in range(14 * 24 // 6):
            ts = now - timedelta(hours=h * 6)
            for fk in fields:
                # 构造有物理意义的模拟值
                if fk == "TotalDisplacement":
                    base = 0.002 + sid * 0.0008 + (14 * 24 - h * 6) / (14 * 24) * 0.005
                    noise = random.gauss(0, 0.0003)
                    val = abs(base + noise)
                elif fk in ("X_Disp", "Y_Disp", "Z_Disp"):
                    val = random.gauss(0.002 + sid * 0.0005, 0.0004)
                elif fk == "Stress_Max_Principal":
                    val = 1.5 + sid * 0.2 + random.gauss(0, 0.15)
                elif fk == "Stress_Min_Principal":
                    val = -(0.8 + sid * 0.1 + abs(random.gauss(0, 0.1)))
                elif fk == "PorePressure":
                    val = 50 + sid * 5 + random.gauss(0, 3)
                elif fk == "WaterLevel":
                    val = 520 + random.gauss(0, 0.5)
                else:
                    val = random.random()
                readings.append(MonitoringReading(
                    sensor_id=s.id, field_key=fk, value=round(val, 6), timestamp=ts,
                ))
                # 偶尔触发超阈值
                if fk == "TotalDisplacement" and h < 8 and random.random() < 0.08:
                    readings[-1].value = round(0.032 + random.random() * 0.01, 6)
                if fk == "Stress_Max_Principal" and h < 6 and random.random() < 0.06:
                    readings[-1].value = round(3.8 + random.random() * 0.5, 3)

    # 分批提交避免过大
    batch = 5000
    for i in range(0, len(readings), batch):
        db.add_all(readings[i:i + batch])
        db.commit()
    print(f"[OK] 模拟监测读数 {len(readings)} 条已生成")


def seed_alert_rules(db, project):
    if db.query(SafetyAlertRule).count() > 0:
        return
    rules = [
        SafetyAlertRule(project_id=project.id, name="总位移预警(mm级)",
                        field_key="TotalDisplacement", comparator=">", threshold=0.03, level="warning"),
        SafetyAlertRule(project_id=project.id, name="总位移严重告警(>50mm)",
                        field_key="TotalDisplacement", comparator=">", threshold=0.05, level="critical"),
        SafetyAlertRule(project_id=project.id, name="最大主应力超阈值",
                        field_key="Stress_Max_Principal", comparator=">", threshold=3.5, level="warning"),
        SafetyAlertRule(project_id=project.id, name="最小主应力超限(>5MPa压)",
                        field_key="Stress_Min_Principal", comparator="<", threshold=-5.0, level="critical"),
        SafetyAlertRule(project_id=project.id, name="X向水平位移异常",
                        field_key="X_Disp", comparator=">", threshold=0.02, level="info"),
        SafetyAlertRule(project_id=project.id, name="Z向沉降预警",
                        field_key="Z_Disp", comparator="<", threshold=-0.025, level="warning"),
        SafetyAlertRule(project_id=project.id, name="孔隙水压力突变",
                        field_key="PorePressure", comparator=">", threshold=90, level="warning"),
    ]
    db.add_all(rules)
    db.commit()
    print(f"[OK] 预警规则 {len(rules)} 条已创建")


def seed_forms(db, project):
    if db.query(Form).count() > 0:
        return
    forms_spec = [
        {
            "form_type": "schedule_plan",
            "title": "土石方平衡总体调度方案（第1版）",
            "created_by": "engineer",
            "status": "approved",
            "data": {
                "excavation_volume": 1856.4,  # 万m³
                "fill_volume": 932.7,
                "borrow_volume": 218.5,
                "discard_volume": 1142.2,
                "construction_period_month": 28,
                "peak_transport_per_day_10k_m3": 6.5,
                "dump_sites": ["A-1#弃渣场(容量720万m³)", "A-3#弃渣场(容量480万m³)"],
                "borrow_sources": ["B-2#取土场(储量320万m³)"],
                "transport_routes": [
                    {"name": "北线-主干便道", "capacity_10k_m3_day": 4.2, "length_km": 5.8},
                    {"name": "南线-临建道路", "capacity_10k_m3_day": 2.8, "length_km": 7.2},
                ],
            },
        },
        {
            "form_type": "earthwork_allocation",
            "title": "exac_1 ~ exac_8 分步开挖调配单",
            "created_by": "engineer",
            "status": "approved",
            "data": {
                "stage_range": "exac_1 至 exac_8",
                "total_stage_volume_10k_m3": 568.2,
                "stages": [
                    {"stage": "exac_1", "volume_10k_m3": 42.5, "target": "A-1#弃渣场"},
                    {"stage": "exac_4", "volume_10k_m3": 78.3, "target": "B-2#取土场反压区"},
                    {"stage": "exac_8", "volume_10k_m3": 95.6, "target": "A-1#弃渣场"},
                ],
            },
        },
        {
            "form_type": "geology_survey",
            "title": "ZK02 钻孔补充勘察报告（F1断层位置修正）",
            "created_by": "engineer",
            "status": "pending",
            "data": {
                "borehole_code": "ZK02",
                "finding": "在深度 48~52m 处发现 F1 断层破碎带，实际位置较原勘察报告向 NE 偏移约 6.5m。",
                "suggestion": "建议 exac_10 工况开挖时增设一排预应力锚索，并对该区域进行超前地质预报。",
                "attachment_count": 3,
            },
        },
        {
            "form_type": "change_request",
            "title": "关于第5马道坡率由1:1.25调整为1:1.5的变更申请",
            "created_by": "manager",
            "status": "pending",
            "data": {
                "location": "左岸边坡 540m 高程马道段",
                "original_design": "坡率 1:1.25，马道宽 2.0m",
                "proposed_design": "坡率 1:1.5，马道宽 3.0m",
                "reason": "ZK04 揭示该段④-2层砂岩强风化厚度达 8.6m，原设计坡率偏陡。",
                "cost_increase_pct": 6.8,
                "schedule_delay_day": 5,
            },
        },
        {
            "form_type": "exception_report",
            "title": "M03 位移计速率异常报告（2024-08-15 ~ 08-21）",
            "created_by": "engineer",
            "status": "draft",
            "data": {
                "sensor_code": "M03",
                "period": "2024-08-15 ~ 2024-08-21",
                "average_rate_mm_day": 2.3,
                "threshold_mm_day": 1.5,
                "analysis": "伴随 exac_14 工况开挖至 F1 断层附近，位移速率明显增大，建议加密监测频次。",
            },
        },
        {
            "form_type": "param_calculation",
            "title": "参数繁衍：exac_15 工况整体稳定系数复核",
            "created_by": "engineer",
            "status": "draft",
            "data": {
                "analysis_method": "有限元强度折减法",
                "constitutive_model": "Mohr-Coulomb",
                "calculated_Fs": 1.32,
                "required_Fs": 1.30,
                "conclusion": "满足规范要求，可按既定方案推进 exac_15 ~ exac_18。",
            },
        },
        {
            "form_type": "monitoring_report",
            "title": "2024年8月 第3周 安全监测周报",
            "created_by": "engineer",
            "status": "approved",
            "data": {
                "week": "2024-W33",
                "max_disp_mm": 28.5,
                "max_stress_MPa": 3.12,
                "alert_count": 3,
                "dispatched_count": 3,
                "conclusion": "边坡整体稳定，M03、S02 传感器建议加密观测。",
            },
        },
    ]
    from app.api.routes.forms import _build_approval_steps
    for spec in forms_spec:
        f = Form(
            project_id=project.id,
            form_type=spec["form_type"],
            title=spec["title"],
            created_by=spec["created_by"],
            status=spec["status"],
            data=spec["data"],
            current_step=0,
        )
        db.add(f)
        db.flush()
        _build_approval_steps(db, f.id, spec["form_type"])
        # 已通过的表单：全部步骤标记 approved
        if spec["status"] == "approved":
            steps = db.query(ApprovalStep).filter(ApprovalStep.form_id == f.id).order_by(ApprovalStep.step_order).all()
            for idx, s in enumerate(steps):
                s.decision = "approved"
                s.decided_by = ["manager", "engineer", "admin"][idx % 3]
                s.decided_at = now = datetime.utcnow() - timedelta(hours=idx + 1)
            f.current_step = len(steps) - 1
        # 审批中：当前第一步待批
        elif spec["status"] == "pending":
            f.current_step = 0
    db.commit()
    print(f"[OK] 示例表单 {len(forms_spec)} 份已创建")


def seed_model_metrics(db):
    if db.query(ModelStageMetric).count() > 0:
        return
    catalog = load_stage_catalog()
    cache_dir = get_model_cache_dir()
    total = 0
    for stage_key in list(catalog.keys())[:3]:  # 只处理前3工况避免太慢
        for fname in ["full_model.vtp", "cavity_surface.vtp"]:
            fpath = cache_dir / stage_key / fname
            if not fpath.exists():
                continue
            ranges = extract_ranges_from_vtp(fpath)
            for k, (mn, mx) in ranges.items():
                db.add(ModelStageMetric(
                    stage_key=stage_key, source_file=fname,
                    scalar_key=k, range_min=mn, range_max=mx,
                ))
                total += 1
    # 其余工况从 input/dist 的已知范围估算（exac_1 ~ exac_23 位移应力趋势递增）
    for stage_idx in range(1, 24):
        sk = f"exac_{stage_idx}"
        if sk in catalog and db.query(ModelStageMetric).filter(ModelStageMetric.stage_key == sk).count() > 0:
            continue
        trend = 1 + (stage_idx - 1) * 0.06
        metrics_list = [
            ("full_model.vtp", "TotalDisplacement", 0.001 * trend, 0.012 * trend),
            ("full_model.vtp", "X_Disp", -0.008 * trend, 0.009 * trend),
            ("full_model.vtp", "Y_Disp", -0.007 * trend, 0.008 * trend),
            ("full_model.vtp", "Z_Disp", -0.010 * trend, 0.003 * trend),
            ("full_model.vtp", "Stress_Max_Principal", 0.05 * trend, 2.85 * trend),
            ("full_model.vtp", "Stress_Min_Principal", -4.20 * trend, -0.08 * trend),
            ("full_model.vtp", "Stress_XX", -1.8 * trend, 1.5 * trend),
            ("full_model.vtp", "Stress_YY", -2.5 * trend, 2.2 * trend),
            ("full_model.vtp", "Stress_ZZ", -3.1 * trend, 0.8 * trend),
        ]
        for fname, fk, mn, mx in metrics_list:
            db.add(ModelStageMetric(
                stage_key=sk, source_file=fname, scalar_key=fk,
                range_min=round(mn, 6), range_max=round(mx, 6),
            ))
            total += 1
    db.commit()
    print(f"[OK] 工况物理量指标 {total} 条已入库")


def seed_alerts(db, project):
    if db.query(SafetyAlert).count() > 0:
        return
    # 手动创建几条历史告警
    rules = db.query(SafetyAlertRule).filter(SafetyAlertRule.project_id == project.id).all()
    rule_map = {r.field_key: r for r in rules}
    now = datetime.utcnow()
    samples = [
        ("TotalDisplacement", "M03位移计读数突增 34.2mm，超过预警阈值 30mm", "warning", 3 * 24),
        ("TotalDisplacement", "M05位移计持续增大至 52.1mm，触发严重告警", "critical", 2 * 24 + 6),
        ("Stress_Max_Principal", "S02锚索应力计最大主应力 3.82MPa，超过阈值 3.5MPa", "warning", 5 * 24),
        ("Z_Disp", "M02 Z向沉降 -28.6mm，超出预警阈值 -25mm", "warning", 1 * 24 + 12),
        ("PorePressure", "P01 渗压计读数 95.2kPa，伴随降雨入渗上升", "info", 6 * 24),
        ("Stress_Min_Principal", "S04最小主应力 -5.3MPa，压应力集中", "critical", 4 * 24),
    ]
    statuses = ["open", "ack", "closed"]
    for fk, msg, lv, hours_ago in samples:
        rule = rule_map.get(fk)
        a = SafetyAlert(
            project_id=project.id,
            rule_id=rule.id if rule else None,
            level=lv,
            message=f"[{lv.upper()}] {msg}",
            status=statuses[random.randint(0, 2)],
            triggered_at=now - timedelta(hours=hours_ago + random.randint(-3, 3)),
        )
        db.add(a)
    db.commit()
    print(f"[OK] 历史告警 {len(samples)} 条已创建")


def sync_index_json():
    """把 input/dist/dist/model_cache/index.json 拷贝到 backend/static 和 frontend/public
    （只精简每个 exac 取中间 5 个切片，避免过大）"""
    import shutil
    input_idx = Path(__file__).resolve().parents[3] / "input" / "dist" / "dist" / "model_cache" / "index.json"
    if not input_idx.exists():
        print("[!] input 源 index.json 未找到，跳过同步")
        return
    with open(input_idx, "r", encoding="utf-8") as f:
        full = json.load(f)

    slim = {}
    for key, info in full.items():
        slices = info.get("slices", {})
        new_slices = {}
        for axis in ["x", "y", "z"]:
            arr = slices.get(axis, [])
            # 取中间 5 个
            if len(arr) > 5:
                mid = len(arr) // 2
                arr = arr[mid - 2: mid + 3]
            new_slices[axis] = arr
        slim[key] = {
            "full": info.get("full"),
            "cavity": info.get("cavity"),
            "slices": new_slices,
        }

    out_paths = [
        Path(settings.MODEL_CACHE_DIR) / "index.json",
        Path(__file__).resolve().parents[1] / "static" / "model_cache" / "index.json",
    ]
    for p in out_paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(slim, f, ensure_ascii=False, indent=2)
    print(f"[OK] 工况索引 index.json 已生成（{len(slim)} 个工况）-> 前端 public 与 backend/static")


def main():
    print("=" * 60)
    print("土石方平衡系统 - 数据库初始化与种子数据注入")
    print("=" * 60)
    # 重建表结构（保证模型改动后同步更新）
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        sync_index_json()
        seed_users(db)
        project = seed_project(db) or db.query(Project).first()
        seed_geology(db, project)
        sensors = seed_sensors(db, project)
        sensors = sensors or db.query(MonitoringSensor).filter(MonitoringSensor.project_id == project.id).all()
        seed_readings(db, sensors)
        seed_alert_rules(db, project)
        seed_forms(db, project)
        seed_model_metrics(db)
        seed_alerts(db, project)
        print("=" * 60)
        print("初始化完成。请使用 admin/admin123 登录系统。")
        print("后端启动:  cd backend && uvicorn app.main:app --reload --port 8000")
        print("前端启动:  cd frontend && npm run dev")
    finally:
        db.close()


if __name__ == "__main__":
    main()
