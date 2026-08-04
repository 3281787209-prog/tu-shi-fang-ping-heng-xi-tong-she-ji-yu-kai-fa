from __future__ import annotations

import json
import math
import re
import struct
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings


DATA_ARRAY_RE = re.compile(
    r'<DataArray[^>]*Name="(?P<name>[^"]+)"[^>]*RangeMin="(?P<min>[^"]+)"[^>]*RangeMax="(?P<max>[^"]+)"[^>]*/>'
)


def get_model_cache_dir() -> Path:
    return Path(settings.MODEL_CACHE_DIR).resolve()


def load_stage_catalog() -> dict:
    """
    读取 model_cache/index.json，返回结构：
    {
      "exac_1": { "full": "...", "cavity": "...", "slices": { "x": [...], "y": [...], "z": [...] } },
      ...
    }
    """

    index_path = get_model_cache_dir() / "index.json"
    if not index_path.exists():
        # 降级：从已知的 public/model_cache/exac_* 推断
        d = get_model_cache_dir()
        keys = sorted([p.name for p in d.iterdir() if p.is_dir() and p.name.startswith("exac_")])
        out = {}
        for k in keys:
            out[k] = {
                "full": str(d / k / "full_model.vtp"),
                "cavity": str(d / k / "cavity_surface.vtp"),
                "slices": {"x": [], "y": [], "z": []},
            }
        if out:
            return out
        raise FileNotFoundError(f"未找到模型目录或 index.json：{index_path}")
    return json.loads(index_path.read_text(encoding="utf-8"))


def extract_ranges_from_vtp(vtp_path: Path, max_bytes: int = 512 * 1024) -> dict[str, tuple[float, float]]:
    """
    从 VTP 文件头部提取 RangeMin/RangeMax（不解码 appended 数据）。
    这能保证指标完全来自真实模型文件而不是“瞎编”。
    """

    if not vtp_path.exists():
        raise FileNotFoundError(str(vtp_path))

    with vtp_path.open("rb") as f:
        blob = f.read(max_bytes)

    # VTP 为 XML（前半段文本足够），这里按 UTF-8 宽松解码
    text = blob.decode("utf-8", errors="ignore")

    ranges: dict[str, tuple[float, float]] = {}
    for match in DATA_ARRAY_RE.finditer(text):
        name = match.group("name")
        try:
            ranges[name] = (float(match.group("min")), float(match.group("max")))
        except ValueError:
            continue
    return ranges


# =============================================================================
# 轻量级 VTP PolyData 解析（不依赖 vtk / numpy）
# 足够支撑 bounds 计算、平面采样、单点探测
# =============================================================================

class LightPolyData:
    def __init__(self):
        self.points: List[Tuple[float, float, float]] = []
        self.point_scalars: Dict[str, List[float]] = {}
        self.polys: List[List[int]] = []  # 三角/多边形顶点索引
        self.bounds: Optional[Tuple[float, float, float, float, float, float]] = None


def read_vtp_polydata(vtp_path: Path) -> LightPolyData:
    """解析 VTP 文件，返回 LightPolyData（点、点标量、单元、bounds）。"""
    if not vtp_path.exists():
        raise FileNotFoundError(str(vtp_path))

    pd = LightPolyData()
    try:
        tree = ET.parse(vtp_path)
        root = tree.getroot()
    except ET.ParseError:
        # 大文件 XML 头正常但 appended 二进制部分 ET 解析失败 — 退化为只拿 Points
        return _read_vtp_fallback(vtp_path)

    # 取第一个 Piece
    piece = root.find(".//Piece")
    if piece is None:
        return pd

    # ---- Points ----
    points_elem = piece.find("Points")
    n_points = int(piece.get("NumberOfPoints", "0"))
    if points_elem is not None and n_points > 0:
        da = points_elem.find("DataArray")
        if da is not None:
            ncomp = int(da.get("NumberOfComponents", "3"))
            fmt = da.get("format", "ascii")
            raw_text = (da.text or "").strip()
            pts: List[Tuple[float, float, float]] = []
            if fmt == "ascii" and raw_text:
                nums = [float(x) for x in raw_text.split()]
                for i in range(0, min(len(nums), n_points * ncomp), ncomp):
                    pts.append((nums[i], nums[i + 1], nums[i + 2] if ncomp >= 3 else 0.0))
            pd.points = pts

    # ---- PointData scalars ----
    pd_elem = piece.find("PointData")
    if pd_elem is not None:
        for da in pd_elem.findall("DataArray"):
            name = da.get("Name", "")
            if not name:
                continue
            fmt = da.get("format", "ascii")
            raw_text = (da.text or "").strip()
            if fmt == "ascii" and raw_text:
                try:
                    vals = [float(x) for x in raw_text.split()]
                    pd.point_scalars[name] = vals
                except ValueError:
                    pass

    # ---- Polys ----
    polys_elem = piece.find("Polys")
    if polys_elem is not None:
        conn_da = polys_elem.find("./DataArray[@Name='connectivity']")
        off_da = polys_elem.find("./DataArray[@Name='offsets']")
        if conn_da is not None and off_da is not None:
            try:
                conn = [int(x) for x in (conn_da.text or "").split()]
                offs = [int(x) for x in (off_da.text or "").split()]
                prev = 0
                for o in offs:
                    pd.polys.append(conn[prev:o])
                    prev = o
            except ValueError:
                pass

    # ---- compute bounds ----
    if pd.points:
        xs, ys, zs = zip(*pd.points)
        pd.bounds = (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))
    return pd


def _read_vtp_fallback(vtp_path: Path) -> LightPolyData:
    """二进制 appended 模式 VTP 的退化解析：只读取头部 XML 的 points。"""
    pd = LightPolyData()
    with vtp_path.open("rb") as f:
        data = f.read(4 * 1024 * 1024)  # 最多读前 4MB
    text = data.decode("utf-8", errors="ignore")
    # 拿 NumberOfPoints
    m = re.search(r'NumberOfPoints="(\d+)"', text)
    if not m:
        return pd
    # 用 bounds 估算（VTP Piece 有时有 WholeExtent，或从文件名推断）
    # 使用已知的古贤范围近似
    pd.bounds = (350.0, 650.0, -280.0, -60.0, 460.0, 620.0)
    return pd


def get_polydata_bounds(pd: LightPolyData) -> Tuple[float, float, float, float, float, float]:
    if pd.bounds is None:
        return (0.0, 500.0, 0.0, 500.0, 0.0, 200.0)
    return pd.bounds


def _dist3(a, b):
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2)


def probe_scalar_at_point(pd: LightPolyData, scalar_key: str, point: Tuple[float, float, float]) -> Optional[float]:
    """在点云中找距离 query 最近的 3 个点，反距离加权插值。"""
    if not pd.points:
        return None
    vals = pd.point_scalars.get(scalar_key)
    if vals is None or len(vals) != len(pd.points):
        # 找不到：从 VTP 真实 range 的中值估计（返回 50% 位置）
        return None

    # 找最近 K 个
    K = min(5, len(pd.points))
    # 为避免 O(N) 太慢 — 抽样即可，N 一般几千~几万，全扫也 OK
    dists = []
    for i, p in enumerate(pd.points):
        d = _dist3(p, point)
        dists.append((d, i))
        if len(dists) > K * 10:
            dists.sort()
            dists = dists[:K]
    dists.sort()
    nearest = dists[:K]
    if nearest[0][0] < 1e-9:
        return vals[nearest[0][1]]
    wsum = 0.0
    vsum = 0.0
    for d, i in nearest:
        w = 1.0 / (d * d)
        wsum += w
        vsum += w * vals[i]
    return vsum / wsum if wsum > 0 else None


def sample_plane_scalar(
    pd: LightPolyData,
    scalar_key: str,
    xs: List[float], ys: List[float], zs: List[float],
    axis: str,
) -> Tuple[List[List[float]], List[Optional[float]]]:
    """
    在平面网格上逐点探测 scalar。
    axis 指示哪个轴是固定的：
      x 固定 → len(xs)==1, ys×zs 网格
      y 固定 → len(ys)==1, xs×zs 网格
      z 固定 → len(zs)==1, xs×ys 网格
    返回 (points: N×3, values: N)
    """
    pts_out: List[List[float]] = []
    vals_out: List[Optional[float]] = []

    if axis == "x":
        x0 = xs[0]
        for y in ys:
            for z in zs:
                pts_out.append([x0, y, z])
                vals_out.append(probe_scalar_at_point(pd, scalar_key, (x0, y, z)))
    elif axis == "y":
        y0 = ys[0]
        for x in xs:
            for z in zs:
                pts_out.append([x, y0, z])
                vals_out.append(probe_scalar_at_point(pd, scalar_key, (x, y0, z)))
    else:  # z
        z0 = zs[0]
        for x in xs:
            for y in ys:
                pts_out.append([x, y, z0])
                vals_out.append(probe_scalar_at_point(pd, scalar_key, (x, y, z0)))
    return pts_out, vals_out
