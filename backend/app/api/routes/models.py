"""
三维模型、地质信息、参数繁衍相关API路由
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.geology import GeologyLayer, BoreholeData
from app.models.model_metric import ModelStageMetric
from app.services.model_cache import (
    get_model_cache_dir,
    load_stage_catalog,
    extract_ranges_from_vtp,
)

router = APIRouter()


# ========== 三维模型工况 ==========

@router.get("/catalog")
def get_model_catalog():
    """获取三维模型工况目录（index.json）"""
    return load_stage_catalog()


@router.get("/stages")
def list_stages():
    """列出所有工况键及基本信息"""
    catalog = load_stage_catalog()
    result = []
    for key, info in catalog.items():
        slices = info.get("slices", {})
        result.append({
            "stage_key": key,
            "full_path": info.get("full"),
            "cavity_path": info.get("cavity"),
            "slice_count_x": len(slices.get("x", [])),
            "slice_count_y": len(slices.get("y", [])),
            "slice_count_z": len(slices.get("z", [])),
        })
    return result


@router.get("/stages/{stage_key}")
def get_stage_detail(stage_key: str):
    """获取单个工况的完整切片信息"""
    catalog = load_stage_catalog()
    if stage_key not in catalog:
        raise HTTPException(status_code=404, detail="工况不存在")
    return {"stage_key": stage_key, **catalog[stage_key]}


@router.get("/stages/{stage_key}/metrics")
def get_stage_metrics(
    stage_key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取工况的物理量指标范围（从VTP真实提取）"""
    catalog = load_stage_catalog()
    if stage_key not in catalog:
        raise HTTPException(status_code=404, detail="工况不存在")

    # 优先从数据库读（已入库的）
    metrics = db.query(ModelStageMetric).filter(ModelStageMetric.stage_key == stage_key).all()
    if metrics:
        return {"stage_key": stage_key, "metrics": [
            {
                "source_file": m.source_file,
                "scalar_key": m.scalar_key,
                "range_min": m.range_min,
                "range_max": m.range_max,
            } for m in metrics
        ]}

    # 否则实时从VTP提取
    cache_dir = get_model_cache_dir()
    stage_info = catalog[stage_key]
    all_metrics = []

    # full_model
    full_path = cache_dir / stage_key / "full_model.vtp"
    if full_path.exists():
        ranges = extract_ranges_from_vtp(full_path)
        for k, (mn, mx) in ranges.items():
            all_metrics.append({
                "source_file": "full_model.vtp",
                "scalar_key": k,
                "range_min": mn,
                "range_max": mx,
            })
            # 顺便入库
            m = ModelStageMetric(
                stage_key=stage_key, source_file="full_model.vtp",
                scalar_key=k, range_min=mn, range_max=mx,
            )
            db.add(m)

    # cavity_surface
    cavity_path = cache_dir / stage_key / "cavity_surface.vtp"
    if cavity_path.exists():
        ranges = extract_ranges_from_vtp(cavity_path)
        for k, (mn, mx) in ranges.items():
            all_metrics.append({
                "source_file": "cavity_surface.vtp",
                "scalar_key": k,
                "range_min": mn,
                "range_max": mx,
            })
            m = ModelStageMetric(
                stage_key=stage_key, source_file="cavity_surface.vtp",
                scalar_key=k, range_min=mn, range_max=mx,
            )
            db.add(m)
    db.commit()
    return {"stage_key": stage_key, "metrics": all_metrics}


@router.get("/metrics/refresh")
def refresh_all_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """重新扫描所有工况VTP并更新指标库"""
    catalog = load_stage_catalog()
    cache_dir = get_model_cache_dir()
    db.query(ModelStageMetric).delete()

    total = 0
    for stage_key in catalog:
        for fname in ["full_model.vtp", "cavity_surface.vtp"]:
            fpath = cache_dir / stage_key / fname
            if fpath.exists():
                ranges = extract_ranges_from_vtp(fpath)
                for k, (mn, mx) in ranges.items():
                    m = ModelStageMetric(
                        stage_key=stage_key, source_file=fname,
                        scalar_key=k, range_min=mn, range_max=mx,
                    )
                    db.add(m)
                    total += 1
    db.commit()
    return {"message": f"已刷新 {total} 条指标记录"}


# ========== 地质图层 ==========

@router.get("/geology/layers", response_model=List[Dict[str, Any]])
def list_geology_layers(
    project_id: Optional[int] = None,
    layer_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取地质图层列表"""
    q = db.query(GeologyLayer)
    if project_id:
        q = q.filter(GeologyLayer.project_id == project_id)
    if layer_type:
        q = q.filter(GeologyLayer.layer_type == layer_type)
    rows = q.order_by(GeologyLayer.created_at.desc()).all()
    return [
        {
            "id": r.id, "project_id": r.project_id, "name": r.name,
            "layer_type": r.layer_type, "description": r.description,
            "stage_key": r.stage_key, "properties": r.properties or {},
            "created_at": r.created_at.isoformat() if r.created_at else None,
        } for r in rows
    ]


@router.post("/geology/layers")
def create_geology_layer(
    body: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建地质图层"""
    layer = GeologyLayer(
        project_id=body.get("project_id"),
        name=body["name"],
        layer_type=body.get("layer_type", "stratum"),
        description=body.get("description"),
        stage_key=body.get("stage_key"),
        properties=body.get("properties", {}),
    )
    db.add(layer)
    db.commit()
    db.refresh(layer)
    return {"id": layer.id, "message": "创建成功"}


@router.put("/geology/layers/{layer_id}")
def update_geology_layer(
    layer_id: int,
    body: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新地质图层"""
    layer = db.query(GeologyLayer).filter(GeologyLayer.id == layer_id).first()
    if not layer:
        raise HTTPException(status_code=404, detail="图层不存在")
    for f in ["name", "layer_type", "description", "stage_key", "project_id"]:
        if f in body:
            setattr(layer, f, body[f])
    if "properties" in body:
        layer.properties = body["properties"]
    db.commit()
    return {"message": "更新成功"}


@router.delete("/geology/layers/{layer_id}")
def delete_geology_layer(
    layer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    layer = db.query(GeologyLayer).filter(GeologyLayer.id == layer_id).first()
    if not layer:
        raise HTTPException(status_code=404, detail="图层不存在")
    db.delete(layer)
    db.commit()
    return {"message": "删除成功"}


# ========== 钻孔数据 ==========

@router.get("/geology/boreholes", response_model=List[Dict[str, Any]])
def list_boreholes(
    project_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取钻孔数据列表"""
    q = db.query(BoreholeData)
    if project_id:
        q = q.filter(BoreholeData.project_id == project_id)
    rows = q.order_by(BoreholeData.hole_code).all()
    return [
        {
            "id": r.id, "project_id": r.project_id, "hole_code": r.hole_code,
            "x": r.x, "y": r.y, "z": r.z, "depth": r.depth,
            "stratigraphy": r.stratigraphy or [],
            "soil_samples": r.soil_samples or {},
            "created_at": r.created_at.isoformat() if r.created_at else None,
        } for r in rows
    ]


@router.post("/geology/boreholes")
def create_borehole(
    body: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建钻孔数据"""
    bh = BoreholeData(
        project_id=body.get("project_id"),
        hole_code=body["hole_code"],
        x=body.get("x"), y=body.get("y"), z=body.get("z"),
        depth=body.get("depth"),
        stratigraphy=body.get("stratigraphy", []),
        soil_samples=body.get("soil_samples", {}),
    )
    db.add(bh)
    db.commit()
    db.refresh(bh)
    return {"id": bh.id, "message": "创建成功"}


# ========== 参数繁衍（模型参数配置） ==========

PARAM_DEFAULTS = {
    "material_params": {
        "soil_density": {"label": "土体天然密度", "value": 1950, "unit": "kg/m³", "range": [1500, 2500]},
        "cohesion": {"label": "黏聚力 c", "value": 25.5, "unit": "kPa", "range": [0, 200]},
        "friction_angle": {"label": "内摩擦角 φ", "value": 28.0, "unit": "°", "range": [0, 50]},
        "elastic_modulus": {"label": "弹性模量 E", "value": 120, "unit": "MPa", "range": [10, 2000]},
        "poisson_ratio": {"label": "泊松比 ν", "value": 0.32, "unit": "", "range": [0.1, 0.5]},
        "permeability": {"label": "渗透系数 k", "value": 5e-6, "unit": "m/s", "range": [1e-9, 1e-2]},
    },
    "excavation_params": {
        "max_excavation_depth": {"label": "最大开挖深度", "value": 85.0, "unit": "m", "range": [0, 200]},
        "single_layer_height": {"label": "单层开挖高度", "value": 3.0, "unit": "m", "range": [0.5, 10]},
        "slope_ratio": {"label": "坡率", "value": 1.25, "unit": "", "range": [0.5, 3.0]},
        "bench_width": {"label": "马道宽度", "value": 2.0, "unit": "m", "range": [0, 10]},
        "support_strength": {"label": "支护强度", "value": 200, "unit": "kN/m²", "range": [0, 1000]},
    },
    "safety_factors": {
        "global_stability": {"label": "整体稳定安全系数", "value": 1.30, "unit": "", "range": [1.0, 2.0]},
        "local_stability": {"label": "局部稳定安全系数", "value": 1.20, "unit": "", "range": [1.0, 2.0]},
        "seismic_factor": {"label": "地震影响系数", "value": 0.05, "unit": "", "range": [0, 0.5]},
        "deformation_control": {"label": "变形控制阈值", "value": 0.03, "unit": "m", "range": [0.001, 0.5]},
    },
    "calculation_settings": {
        "analysis_method": {"label": "分析方法", "value": "有限元强度折减法", "unit": "", "options": ["有限元强度折减法", "极限平衡法", "有限差分法"]},
        "constitutive_model": {"label": "本构模型", "value": "Mohr-Coulomb", "unit": "", "options": ["Mohr-Coulomb", "Drucker-Prager", "Cam-Clay", "线弹性"]},
        "iteration_max": {"label": "最大迭代步数", "value": 1000, "unit": "步", "range": [100, 10000]},
        "convergence_tol": {"label": "收敛容差", "value": 1e-6, "unit": "", "range": [1e-9, 1e-3]},
    },
}


@router.get("/params/schema")
def get_param_schema():
    """获取参数繁衍的完整配置结构（含标签、单位、范围）"""
    return PARAM_DEFAULTS


@router.get("/params/values")
def get_param_values(
    stage_key: Optional[str] = Query(None, description="工况键，不传返回默认"),
):
    """获取参数值（简化：以默认值为主，可按工况扩展）"""
    # 这里可以扩展为按 stage_key 从数据库读取自定义配置
    result = {}
    for group, items in PARAM_DEFAULTS.items():
        result[group] = {}
        for key, meta in items.items():
            result[group][key] = meta["value"]
    return result


@router.post("/params/calculate")
def calculate_derived_params(body: Dict[str, Any]):
    """
    基于输入参数推导衍生参数（参数繁衍核心逻辑）
    输入：PARAM_DEFAULTS 结构的参数值
    输出：衍生指标（土方量估算、稳定性估算、沉降估算等）
    """
    material = body.get("material_params", {})
    excavation = body.get("excavation_params", {})
    safety = body.get("safety_factors", {})

    # 取参数（带默认值保护）
    density = material.get("soil_density", 1950)
    cohesion = material.get("cohesion", 25.5)
    friction = material.get("friction_angle", 28.0)
    E = material.get("elastic_modulus", 120) * 1e6  # MPa -> Pa
    nu = material.get("poisson_ratio", 0.32)

    max_depth = excavation.get("max_excavation_depth", 85.0)
    layer_h = excavation.get("single_layer_height", 3.0)
    slope_ratio = excavation.get("slope_ratio", 1.25)
    bench_w = excavation.get("bench_width", 2.0)

    # 1. 开挖总层数
    total_layers = int(max_depth / layer_h) + (1 if max_depth % layer_h > 0 else 0)

    # 2. 边坡水平投影宽度估算
    slope_horizontal = max_depth * slope_ratio

    # 3. 土方量估算（简化模型：梯形截面 × 典型开挖宽度 100m）
    top_width = slope_horizontal * 2 + 60  # 底宽约60m
    bottom_width = 60
    section_area = (top_width + bottom_width) * max_depth / 2
    typical_length = 100
    earthwork_volume = section_area * typical_length  # m³

    # 4. 土体重力荷载
    earth_weight = earthwork_volume * density * 9.81 / 1e6  # MN

    # 5. 简化边坡稳定安全系数估算（泰勒简化）
    import math
    phi_rad = math.radians(friction)
    # 近似：Fs = (2c·sin(φ+45°)^2)/(γ·H·tan(45°-φ/2))
    gamma = density * 9.81 / 1e3  # kN/m³
    numerator = 2 * cohesion * (math.sin(phi_rad + math.pi / 4)) ** 2
    denominator = gamma * max_depth * math.tan(math.pi / 4 - phi_rad / 2) if max_depth > 0 else 1
    estimated_Fs = numerator / denominator if denominator > 0 else 99.0

    # 6. 最大沉降估算（基础公式 s ≈ q·B·(1-ν²)/E  ，B=底宽）
    q = gamma * max_depth  # kPa
    B = bottom_width  # m
    max_settlement = (q * 1e3) * B * (1 - nu ** 2) / E  # m

    # 7. 分类级别判断
    if estimated_Fs >= safety.get("global_stability", 1.30):
        stability_level = "满足规范要求"
    elif estimated_Fs >= safety.get("global_stability", 1.30) * 0.9:
        stability_level = "接近临界，建议加强支护"
    else:
        stability_level = "不满足要求，需调整参数"

    if max_settlement <= safety.get("deformation_control", 0.03):
        deformation_level = "变形可控"
    elif max_settlement <= safety.get("deformation_control", 0.03) * 1.5:
        deformation_level = "变形偏大，需监测"
    else:
        deformation_level = "变形超标，需加固"

    return {
        "derived": {
            "total_layers": total_layers,
            "slope_horizontal_width": round(slope_horizontal, 2),
            "section_area": round(section_area, 2),
            "earthwork_volume": round(earthwork_volume, 2),
            "earthwork_weight_MN": round(earth_weight, 2),
            "estimated_Fs": round(estimated_Fs, 3),
            "max_settlement_mm": round(max_settlement * 1000, 2),
        },
        "classification": {
            "stability_level": stability_level,
            "deformation_level": deformation_level,
            "earthwork_class": "大型" if earthwork_volume > 1e6 else ("中型" if earthwork_volume > 1e5 else "小型"),
            "excavation_class": "超深" if max_depth > 60 else ("深" if max_depth > 30 else "一般"),
        },
        "suggestions": [
            f"建议分 {total_layers} 层开挖，每层 {layer_h}m",
            f"预计总开挖方量约 {earthwork_volume/1e4:.1f} 万 m³",
            f"边坡估算安全系数 Fs ≈ {estimated_Fs:.2f}，{stability_level}",
            f"预计最大沉降约 {max_settlement*1000:.1f} mm，{deformation_level}",
            "建议每开挖 2~3 层进行一次支护与监测复核",
        ],
    }
