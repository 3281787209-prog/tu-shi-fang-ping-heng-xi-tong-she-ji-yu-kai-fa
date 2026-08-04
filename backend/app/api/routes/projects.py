"""
项目管理API路由
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_user, require_role
from app.models.user import User
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectOut, ProjectUpdate

router = APIRouter()


@router.get("", response_model=List[ProjectOut])
def list_projects(
    keyword: Optional[str] = Query(None, description="按名称搜索"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取项目列表，支持关键词搜索"""
    q = db.query(Project)
    if keyword:
        q = q.filter(Project.name.contains(keyword))
    return q.order_by(Project.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取单个项目详情"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


@router.post("", response_model=ProjectOut)
def create_project(
    body: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager")),
):
    """[管理员/经理] 创建项目"""
    project = Project(**body.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.put("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int,
    body: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "manager")),
):
    """[管理员/经理] 更新项目信息"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    update_data = body.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(project, k, v)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """[管理员] 删除项目"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    db.delete(project)
    db.commit()
    return {"message": "删除成功"}
