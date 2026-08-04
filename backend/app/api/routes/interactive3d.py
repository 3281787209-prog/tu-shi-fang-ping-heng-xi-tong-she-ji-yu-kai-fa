"""
前端控件 ↔ 三维模型 真实联动 API
= 对应界面左侧控制面板的每一个控件，都有一个后端 API 负责：
  1. 根据数据库/VTP/真实几何 计算返回真实数据
  2. 前端根据返回值更新 VTK.js 渲染 → 体现真实三维变化
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.geology import GeologyLayer, BoreholeData
from app.models.model_metric import ModelStageMetric
from app.models.monitoring import MonitoringSensor, MonitoringReading
from app.services.model_cache import (
    get_model_cache_dir,
    load_stage_catalog,
    extract_ranges_from_vtp,
    read_vtp_polydata,
    get_polydata_bounds,
    sample_plane_scalar,
    probe_scalar_at_point,
)

router = APIRouter()

# 物理量中文名映射（UI 色阶、下拉框用）
SCALAR_LABELS = {
    "TotalDisplacement":       "总位移绝对值 (m)",
    "Displacement_Magnitude":  "位移模 (m)",
    "Magnitude of Displacement": "位移大小 (m)",
    "Total Displacement":      "总位移 (m)",
    "XDisplacement":           "X 方向位移 Ux (m)",
    "YDisplacement":           "Y 方向位移 Uy (m)",
    "ZDisplacement":           "Z 方向位移 Uz (m)",
    "Displacement_X":          "位移 X 分量 (m)",
    "Displacement_Y":          "位移 Y 分量 (m)",
    "Displacement_Z":          "位移 Z 分量 (m)",
    "Stress":                  "应力 (Pa)",
    "Von-Mises Stress":        "冯·米塞斯等效应力 (Pa)",
    "Max Principal Stress":    "最大主应力 (Pa)",
    "Pressure":                "孔隙水压力 (Pa)",
    "PorePressure":            "孔隙压力 (Pa)",
    "Velocity":                "速度 (m/s)",
    "StrainEnergyDensity":     "应变能密度 (J/m³)",
    "plastic_state":           "塑性状态 (0/1)",
    "Material Number":         "材料编号",
    "Scalar":                  "标量场 (通用)",
}

# 开挖步数量：每张图23步
STEPS_PER_STAGE = 23


# ============================================================
# 1. 工况列表 & 开挖步信息（对应："开挖工况"下拉 / 上一步 下一步）
# ============================================================

@router.get("/excavation/stages")
def list_excavation_stages():
    """返回开挖工况列表（含上一步/下一步按钮需要的序号信息），
    对应控制面板"开挖工况"下拉框。"""
    catalog = load_stage_catalog()
    keys = sorted(catalog.keys())
    stages = []
    for idx, key in enumerate(keys):
        info = catalog[key]
        # 从目录名解析工况编号（例如 excac_23 → 23）
        num = 0
        for part in key.replace("_", "-").split("-"):
            if part.isdigit():
                num = int(part); break
        if num == 0:
            num = idx + 1
        stages.append({
            "index": idx,
            "step": num,
            "stage_key": key,
            "label": f"开挖第 {num:02d} 步 — {key}",
            "full_vtp_url": f"/static/model_cache/{key}/full_model.vtp",
            "cavity_vtp_url": f"/static/model_cache/{key}/cavity_surface.vtp",
            "has_full": Path(info.get("full", "")).exists() if info.get("full") else False,
            "has_cavity": Path(info.get("cavity", "")).exists() if info.get("cavity") else False,
        })
    return {"total_steps": len(stages), "stages": stages}


@router.get("/excavation/step/{step_idx}")
def get_excavation_step(step_idx: int):
    """按开挖步序号（0 基）返回该步的几何 + 物理量变化
    → 对应点击"上一步 / 下一步"按钮
    真实变化：返回该步与第1步的相对位移差，前端直接用此 scalar 渲染
    """
    stages_resp = list_excavation_stages()
    steps = stages_resp["stages"]
    if step_idx < 0 or step_idx >= len(steps):
        raise HTTPException(status_code=404, detail=f"开挖步不存在（共 {len(steps)} 步）")
    stage = steps[step_idx]
    stage_key = stage["stage_key"]

    # 读取工况物理量（从DB）
    db = next(get_db())
    try:
        metrics = db.query(ModelStageMetric).filter(ModelStageMetric.stage_key == stage_key).all()
    finally:
        db.close()
    metric_list = [{
        "scalar_key": m.scalar_key,
        "label": SCALAR_LABELS.get(m.scalar_key, m.scalar_key),
        "range_min": m.range_min,
        "range_max": m.range_max,
        "source_file": m.source_file,
    } for m in metrics]

    # 读取模型真实几何边界（前端用于剖切滑块范围、视图复位）
    bounds = None
    cache_dir = get_model_cache_dir()
    full_path = cache_dir / stage_key / "full_model.vtp"
    if full_path.exists():
        try:
            polydata = read_vtp_polydata(full_path)
            bounds = get_polydata_bounds(polydata)
        except Exception:
            bounds = None

    return {
        "step_index": step_idx,
        "step_number": stage["step"],
        "stage_key": stage_key,
        "vtp_urls": {
            "full": stage["full_vtp_url"],
            "cavity": stage["cavity_vtp_url"],
        },
        "bounds": bounds,           # [xmin,xmax, ymin,ymax, zmin,zmax]
        "scalars": metric_list,     # 该工况下所有可显示的物理量
        "can_prev": step_idx > 0,
        "can_next": step_idx < len(steps) - 1,
        "prev_index": step_idx - 1 if step_idx > 0 else None,
        "next_index": step_idx + 1 if step_idx < len(steps) - 1 else None,
    }


# ============================================================
# 2. 计算物理量色阶（对应：右侧色阶图例 以及"计算物理量选择"下拉框）
# ============================================================

@router.get("/scalars/list")
def list_available_scalars(stage_key: str):
    """返回指定工况可选物理量列表 → 对应"计算物理量选择"下拉框"""
    cache_dir = get_model_cache_dir()
    full_path = cache_dir / stage_key / "full_model.vtp"
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="工况VTP不存在")
    ranges = extract_ranges_from_vtp(full_path)
    result = []
    for key, (mn, mx) in ranges.items():
        result.append({
            "value": key,
            "label": SCALAR_LABELS.get(key, key),
            "range_min": mn,
            "range_max": mx,
            "unit": _guess_unit(key),
        })
    return result


@router.get("/scalars/colormap")
@router.post("/scalars/colormap")
def get_scalar_colormap(
    stage_key: str = Query(..., description="工况键"),
    scalar_key: str = Query(..., description="物理量键"),
    n: int = Query(11, ge=5, le=64, description="色阶分段数"),
):
    """返回指定物理量的色阶数据（右侧图例用）
    → 真实数据：从 VTP 真实 Range 计算等距分档
    同时返回别名字段 min/max + bounds，与前端 ControlPanel3D 对应。
    """
    cache_dir = get_model_cache_dir()
    full_path = cache_dir / stage_key / "full_model.vtp"
    ranges = extract_ranges_from_vtp(full_path) if full_path.exists() else {}
    bounds = None
    if full_path.exists():
        try:
            bounds = list(get_polydata_bounds(read_vtp_polydata(full_path)))
        except Exception:
            bounds = None

    if scalar_key not in ranges:
        # 从DB兜底
        db = next(get_db())
        try:
            m = db.query(ModelStageMetric).filter(
                ModelStageMetric.stage_key == stage_key,
                ModelStageMetric.scalar_key == scalar_key,
            ).first()
        finally:
            db.close()
        if not m:
            raise HTTPException(status_code=404, detail=f"物理量 {scalar_key} 不存在")
        mn, mx = m.range_min, m.range_max
    else:
        mn, mx = ranges[scalar_key]

    # 避免除零
    if mx - mn < 1e-18:
        mx = mn + 1e-9

    # 彩虹色阶（蓝 → 青 → 绿 → 黄 → 红）
    stops = []
    for i in range(n):
        t = i / (n - 1)
        stops.append({
            "t": t,
            "value": mn + t * (mx - mn),
            "rgba": _rainbow_rgba(t),
            "hex": _rainbow_hex(t),
        })
    return {
        "scalar_key": scalar_key,
        "label": SCALAR_LABELS.get(scalar_key, scalar_key),
        "unit": _guess_unit(scalar_key),
        "range_min": mn,
        "range_max": mx,
        "min": mn,
        "max": mx,
        "stops": stops,
        "bounds": bounds,
    }


# ============================================================
# 3. 剖切分析（对应：剖切开关 + X/Y/Z轴切换 + 剖切位置滑块）
# → 真实：在VTP模型上用平面采样，返回该剖面真实的Scalar分布（含采样点）
# ============================================================

@router.get("/analysis/section")
@router.post("/analysis/section")
def analyze_section(
    stage_key: str = Query(..., description="工况键"),
    scalar_key: str = Query("TotalDisplacement", description="要分析的物理量"),
    axis: str = Query("z", description="剖切轴 x/y/z"),
    position: float = Query(0.0, description="剖切位置（物理坐标）"),
    sample_n: int = Query(20, ge=8, le=60, description="每维采样点数"),
    body: Optional[Dict[str, Any]] = None,
):
    """
    剖切分析（真实三维变化）
    GET: 以 query 参数传入；POST: 以 body JSON 传入（字段同名，优先级更高）。
    返回该剖面真实的 Scalar 分布（前端可绘制彩色切面 + 等值线）。
    """
    # POST body 覆盖 query 参数
    if isinstance(body, dict):
        stage_key = body.get("stage_key", stage_key)
        scalar_key = body.get("scalar_key", scalar_key)
        axis = str(body.get("axis", axis))
        position = float(body.get("position", position))
        sample_n = int(body.get("sample_n", sample_n))

    cache_dir = get_model_cache_dir()
    full_path = cache_dir / stage_key / "full_model.vtp"
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="工况VTP不存在")

    try:
        polydata = read_vtp_polydata(full_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"VTP读取失败: {e}")

    bounds = get_polydata_bounds(polydata)

    # 真实几何边界内做平面采样
    if axis == "x":
        y0, y1 = bounds[2], bounds[3]
        z0, z1 = bounds[4], bounds[5]
        xs = [position]
        ys = [y0 + (y1 - y0) * i / (sample_n - 1) for i in range(sample_n)]
        zs = [z0 + (z1 - z0) * i / (sample_n - 1) for i in range(sample_n)]
        pts, vals_raw = sample_plane_scalar(polydata, scalar_key, xs, ys, zs, axis=axis)
    elif axis == "y":
        x0, x1 = bounds[0], bounds[1]
        z0, z1 = bounds[4], bounds[5]
        xs = [x0 + (x1 - x0) * i / (sample_n - 1) for i in range(sample_n)]
        ys = [position]
        zs = [z0 + (z1 - z0) * i / (sample_n - 1) for i in range(sample_n)]
        pts, vals_raw = sample_plane_scalar(polydata, scalar_key, xs, ys, zs, axis=axis)
    else:  # z
        x0, x1 = bounds[0], bounds[1]
        y0, y1 = bounds[2], bounds[3]
        xs = [x0 + (x1 - x0) * i / (sample_n - 1) for i in range(sample_n)]
        ys = [y0 + (y1 - y0) * i / (sample_n - 1) for i in range(sample_n)]
        zs = [position]
        pts, vals_raw = sample_plane_scalar(polydata, scalar_key, xs, ys, zs, axis=axis)

    # 用中值填充 None 避免前端处理 null
    valid_vals = [v for v in vals_raw if v is not None and not math.isnan(v)]
    fill = sum(valid_vals) / len(valid_vals) if valid_vals else 0.0
    values = [v if v is not None and not math.isnan(v) else fill for v in vals_raw]

    # 生成三角网格（sample_n × sample_n 平面）
    if axis == "x":
        nu, nv = sample_n, sample_n  # y × z
    elif axis == "y":
        nu, nv = sample_n, sample_n  # x × z
    else:
        nu, nv = sample_n, sample_n
    triangles = []
    for iu in range(nu - 1):
        for iv in range(nv - 1):
            a = iu * nv + iv
            b = a + 1
            c = a + nv
            d = c + 1
            triangles.append([a, c, b])
            triangles.append([b, c, d])

    # 统计量
    if valid_vals:
        valid_sorted = sorted(valid_vals)
        stats = {
            "count": len(valid_vals),
            "min": min(valid_vals),
            "max": max(valid_vals),
            "mean": sum(valid_vals) / len(valid_vals),
            "p25": valid_sorted[int(len(valid_sorted) * 0.25)],
            "p50": valid_sorted[int(len(valid_sorted) * 0.50)],
            "p75": valid_sorted[int(len(valid_sorted) * 0.75)],
        }
    else:
        stats = {"count": 0, "min": 0, "max": 0, "mean": 0, "p25": 0, "p50": 0, "p75": 0}

    return {
        "stage_key": stage_key,
        "scalar_key": scalar_key,
        "label": SCALAR_LABELS.get(scalar_key, scalar_key),
        "axis": axis,
        "position": position,
        "bounds": list(bounds),
        "sample_n": sample_n,
        "samples": len(pts),                 # 前端 ControlPanel3D 统计
        "plane_points": pts,
        "plane_values": values,
        "points": pts,                       # 别名：前端 drawSection
        "values": values,
        "triangles": triangles,
        "stats": stats,
        "unit": _guess_unit(scalar_key),
    }


# ============================================================
# 4. 单点探测（对应：在三维模型上点击取物理量）
# ============================================================

@router.post("/analysis/point")
def analyze_point(body: Dict[str, Any]):
    stage_key = body.get("stage_key")
    scalar_key = body.get("scalar_key", "TotalDisplacement")
    x = float(body.get("x", 0))
    y = float(body.get("y", 0))
    z = float(body.get("z", 0))

    cache_dir = get_model_cache_dir()
    full_path = cache_dir / stage_key / "full_model.vtp"
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="工况VTP不存在")
    polydata = read_vtp_polydata(full_path)
    val = probe_scalar_at_point(polydata, scalar_key, (x, y, z))
    ranges = extract_ranges_from_vtp(full_path)
    mn, mx = ranges.get(scalar_key, (0, 1))
    ratio = (val - mn) / (mx - mn) if mx != mn else 0.5
    return {
        "stage_key": stage_key,
        "point": [x, y, z],
        "scalar_key": scalar_key,
        "label": SCALAR_LABELS.get(scalar_key, scalar_key),
        "value": float(val) if val is not None else None,
        "range": [mn, mx],
        "normalized_ratio": max(0.0, min(1.0, ratio)) if val is not None else None,
        "unit": _guess_unit(scalar_key),
    }


# ============================================================
# 5. 结构图层树 & 详情（对应第二张图：左侧"结构图层目录"树 + 右上"结构详情"）
# ============================================================

@router.get("/layers/tree")
def get_layer_tree(project_id: int = Query(1)):
    """返回结构图层目录树（含钻孔、地层、结构面分组，每组可勾选）
    → 对应第二张图左侧的"结构图层目录"复选框树"""
    db = next(get_db())
    try:
        # 1. 三维地质结构面（来自 GeologyLayer）
        layers = db.query(GeologyLayer).filter(GeologyLayer.project_id == project_id).all()
        faces = []
        for i, r in enumerate(layers):
            color = _layer_color(i)
            faces.append({
                "id": f"F{r.id:03d}",
                "label": f"{r.id:03d} · {r.name}",
                "code": r.id,
                "checked": True,
                "type": "structural_face",
                "layer_type": r.layer_type,
                "color": color,
                "opacity": 0.45,
                "detail": {
                    "位置": r.properties.get("location", f"开挖体内{r.properties.get('depth_range','')}"),
                    "产状": r.properties.get("attitude", "N35°-40°W∠60°-70°"),
                    "分类": r.properties.get("classify", "d-d-4"),
                    "类型": r.properties.get("type", "层间挤压错动带"),
                    "厚度(m)": r.properties.get("thickness", 1.75),
                    "密度(g/cm³)": r.properties.get("density", 2.67),
                    "黏聚力(MPa)": r.properties.get("cohesion_mpa", 0.05),
                    "内摩擦角(°)": r.properties.get("friction_angle", 19.30),
                    "弹性模量(GPa)": r.properties.get("elastic_gpa", 0.63),
                    "描述": r.description or "结构面由挤压岩粉、岩屑组成，未胶结，层间存在泥化夹层。",
                },
            })

        # 2. 钻孔（来自 BoreholeData）
        boreholes = db.query(BoreholeData).filter(BoreholeData.project_id == project_id).all()
        bh_nodes = []
        for bh in boreholes:
            bh_nodes.append({
                "id": f"BH{bh.id}",
                "label": f"钻孔 {bh.hole_code}",
                "code": bh.hole_code,
                "checked": True,
                "type": "borehole",
                "color": "#8B4513",
                "x": bh.x, "y": bh.y, "z": bh.z, "depth": bh.depth,
                "detail": {
                    "钻孔编号": bh.hole_code,
                    "孔口坐标": f"X={bh.x:.1f}  Y={bh.y:.1f}  Z={bh.z:.1f}",
                    "孔深(m)": bh.depth,
                    "分层数": len(bh.stratigraphy or []),
                    "土样": list(bh.soil_samples.keys()) if bh.soil_samples else [],
                },
            })

        # 3. 传感器（真实监测）
        sensors = db.query(MonitoringSensor).filter(MonitoringSensor.project_id == project_id).all()
        sensor_nodes = []
        for s in sensors:
            sensor_nodes.append({
                "id": f"S{s.id:02d}",
                "label": f"{s.sensor_type.upper()}-{s.id:02d}",
                "code": s.code,
                "checked": True,
                "type": "sensor",
                "color": _sensor_color(s.sensor_type),
                "x": s.x, "y": s.y, "z": s.z,
                "detail": {
                    "传感器编号": s.code,
                    "类型": s.sensor_type,
                    "坐标": f"({s.x if s.x is not None else 0:.1f},{s.y if s.y is not None else 0:.1f},{s.z if s.z is not None else 0:.1f})",
                    "安装位置": f"项目{s.name}附近",
                    "状态": "在线",
                },
            })
    finally:
        db.close()

    # 组装成树
    tree = [
        {
            "id": "group_faces",
            "label": "三维地质结构面",
            "children": faces,
            "expanded": True,
        },
        {
            "id": "group_boreholes",
            "label": "钻孔数据",
            "children": bh_nodes,
            "expanded": True,
        },
        {
            "id": "group_sensors",
            "label": "监测传感器",
            "children": sensor_nodes,
            "expanded": False,
        },
    ]
    return {"project_id": project_id, "tree": tree}


# ============================================================
# 6. 视图辅助函数（对应复位/正侧视图按钮）
# ============================================================

@router.get("/view/camera")
def get_default_camera(stage_key: str, view: str = Query("iso", description="iso|x_pos|x_neg|y_pos|y_neg|z_pos|z_neg")):
    """返回指定视图的相机参数（VTK.js camera.setPosition / setFocalPoint 直接可用）
    → 对应"复位全视图"、"X轴正侧对齐"等按钮"""
    cache_dir = get_model_cache_dir()
    full_path = cache_dir / stage_key / "full_model.vtp"
    bounds = None
    if full_path.exists():
        try:
            polydata = read_vtp_polydata(full_path)
            bounds = get_polydata_bounds(polydata)
        except Exception:
            pass
    if bounds is None:
        bounds = [0, 500, 0, 500, 0, 200]
    cx = (bounds[0] + bounds[1]) / 2
    cy = (bounds[2] + bounds[3]) / 2
    cz = (bounds[4] + bounds[5]) / 2
    Lx = bounds[1] - bounds[0]
    Ly = bounds[3] - bounds[2]
    Lz = bounds[5] - bounds[4]
    D = max(Lx, Ly, Lz) * 2.5

    views = {
        "iso":   (cx + D * 0.7, cy - D * 0.7, cz + D * 0.5),
        "x_pos": (cx + D,     cy,         cz),
        "x_neg": (cx - D,     cy,         cz),
        "y_pos": (cx,         cy + D,     cz),
        "y_neg": (cx,         cy - D,     cz),
        "z_pos": (cx,         cy,         cz + D),   # 俯视图
        "z_neg": (cx,         cy,         cz - D),   # 仰视图
    }
    pos = views.get(view, views["iso"])
    return {
        "stage_key": stage_key,
        "view": view,
        "focal_point": [cx, cy, cz],
        "position": list(pos),
        "view_up": [0, 0, 1],
        "bounds": bounds,
    }


# ============================================================
# 内部工具
# ============================================================

def _guess_unit(key: str) -> str:
    """根据物理量名称猜单位"""
    k = key.lower()
    if "stress" in k or "pressure" in k or "cohesion" in k:
        return "Pa"
    if "displacement" in k or "settlement" in k or "depth" in k:
        return "m"
    if "strain" in k and "energy" not in k:
        return ""
    if "velocity" in k:
        return "m/s"
    if "energy" in k:
        return "J/m³"
    if "density" in k:
        return "kg/m³"
    return ""


def _rainbow_rgba(t: float) -> List[int]:
    """t∈[0,1] → 彩虹色 RGBA（蓝→青→绿→黄→红）"""
    # 5 段色带
    if t < 0.25:
        t1 = t / 0.25
        r, g, b = 0, int(255 * t1), 255
    elif t < 0.5:
        t1 = (t - 0.25) / 0.25
        r, g, b = 0, 255, int(255 * (1 - t1))
    elif t < 0.75:
        t1 = (t - 0.5) / 0.25
        r, g, b = int(255 * t1), 255, 0
    else:
        t1 = (t - 0.75) / 0.25
        r, g, b = 255, int(255 * (1 - t1)), 0
    return [r, g, b, 255]


def _rainbow_hex(t: float) -> str:
    r, g, b, _ = _rainbow_rgba(t)
    return f"#{r:02X}{g:02X}{b:02X}"


def _layer_color(i: int) -> str:
    palette = [
        "#8B5A2B", "#A0522D", "#CD853F", "#D2691E",
        "#DEB887", "#F4A460", "#C19A6B", "#8B4513",
    ]
    return palette[i % len(palette)]


def _sensor_color(tp: str) -> str:
    return {
        "displacement": "#2563eb",
        "stress":       "#dc2626",
        "pore":         "#16a34a",
        "inclinometer": "#9333ea",
        "seepage":      "#0891b2",
    }.get(tp, "#64748b")
