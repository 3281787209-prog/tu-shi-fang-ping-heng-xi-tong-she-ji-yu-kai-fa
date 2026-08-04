"""
表单与审批流程API路由
支持：土石方调度方案审批、变更申请、异常上报、参数计算审批等
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_user, require_role
from app.models.user import User
from app.models.form import Form, ApprovalStep
from app.models.project import Project
from app.schemas.form import (
    FormCreate, FormOut, FormListOut,
    ApprovalDecision, ApprovalStepOut,
)

router = APIRouter()

# 按表单类型定义审批步骤（角色链）
APPROVAL_CHAINS = {
    "schedule_plan": ["manager", "engineer", "admin"],          # 土石方调度方案
    "change_request": ["manager", "admin"],                      # 变更申请
    "exception_report": ["manager", "engineer"],                 # 异常上报
    "param_calculation": ["engineer", "manager"],                # 参数计算审批
    "earthwork_allocation": ["manager", "engineer", "admin"],    # 土石方调配
    "geology_survey": ["engineer", "manager"],                   # 地质勘察报告
    "monitoring_report": ["engineer", "manager"],                # 监测报告
}

FORM_TYPE_LABELS = {
    "schedule_plan": "土石方调度方案",
    "change_request": "变更申请",
    "exception_report": "异常上报",
    "param_calculation": "参数计算审批",
    "earthwork_allocation": "土石方调配方案",
    "geology_survey": "地质勘察报告",
    "monitoring_report": "监测报告",
}


def _build_approval_steps(db: Session, form_id: int, form_type: str):
    """根据表单类型创建审批步骤链"""
    chain = APPROVAL_CHAINS.get(form_type, ["manager", "admin"])
    for i, role in enumerate(chain):
        step = ApprovalStep(
            form_id=form_id,
            step_order=i,
            approver_role=role,
        )
        db.add(step)


@router.get("/types")
def get_form_types():
    """获取所有表单类型及其审批链"""
    result = []
    for key, label in FORM_TYPE_LABELS.items():
        result.append({
            "type": key,
            "label": label,
            "approval_chain": APPROVAL_CHAINS.get(key, ["manager", "admin"]),
        })
    return result


@router.get("", response_model=List[FormListOut])
def list_forms(
    project_id: Optional[int] = None,
    form_type: Optional[str] = None,
    status: Optional[str] = None,
    created_by: Optional[str] = None,
    my_pending: Optional[bool] = Query(False, description="仅显示我待审批的"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取表单列表，支持多条件筛选"""
    q = db.query(Form)
    if project_id:
        q = q.filter(Form.project_id == project_id)
    if form_type:
        q = q.filter(Form.form_type == form_type)
    if status:
        q = q.filter(Form.status == status)
    if created_by:
        q = q.filter(Form.created_by == created_by)
    if my_pending:
        # 我作为当前步骤审批人的表单
        sub = (
            db.query(ApprovalStep.form_id)
            .filter(
                ApprovalStep.approver_role == current_user.role,
                ApprovalStep.decision.is_(None),
            )
            .subquery()
        )
        q = q.filter(
            Form.status == "pending",
            Form.id.in_(sub),
        )
    forms = q.order_by(Form.created_at.desc()).offset(skip).limit(limit).all()

    # 补充审批步骤信息
    result = []
    for f in forms:
        steps = db.query(ApprovalStep).filter(ApprovalStep.form_id == f.id).order_by(ApprovalStep.step_order).all()
        result.append({
            **FormOut.model_validate(f).model_dump(),
            "approvals": [ApprovalStepOut.model_validate(s).model_dump() for s in steps],
            "form_type_label": FORM_TYPE_LABELS.get(f.form_type, f.form_type),
        })
    return result


@router.get("/stats")
def get_form_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """表单统计概览"""
    total = db.query(Form).count()
    draft = db.query(Form).filter(Form.status == "draft").count()
    pending = db.query(Form).filter(Form.status == "pending").count()
    approved = db.query(Form).filter(Form.status == "approved").count()
    rejected = db.query(Form).filter(Form.status == "rejected").count()

    # 我待审批的数量
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

    # 按类型统计
    by_type = []
    for key, label in FORM_TYPE_LABELS.items():
        cnt = db.query(Form).filter(Form.form_type == key).count()
        by_type.append({"type": key, "label": label, "count": cnt})

    return {
        "total": total,
        "draft": draft,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "my_pending": my_pending,
        "by_type": by_type,
    }


@router.get("/{form_id}", response_model=FormOut)
def get_form(
    form_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取表单详情（含审批步骤）"""
    form = db.query(Form).filter(Form.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="表单不存在")
    steps = db.query(ApprovalStep).filter(ApprovalStep.form_id == form.id).order_by(ApprovalStep.step_order).all()
    result = FormOut.model_validate(form).model_dump()
    result["approvals"] = [ApprovalStepOut.model_validate(s).model_dump() for s in steps]
    result["form_type_label"] = FORM_TYPE_LABELS.get(form.form_type, form.form_type)
    return result


@router.post("", response_model=FormOut)
def create_form(
    body: FormCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建表单（草稿状态）"""
    if body.project_id:
        proj = db.query(Project).filter(Project.id == body.project_id).first()
        if not proj:
            raise HTTPException(status_code=400, detail="所属项目不存在")

    form = Form(
        project_id=body.project_id,
        form_type=body.form_type,
        title=body.title,
        data=body.data or {},
        created_by=current_user.username,
        status="draft",
        current_step=0,
    )
    db.add(form)
    db.flush()
    _build_approval_steps(db, form.id, body.form_type)
    db.commit()
    db.refresh(form)

    steps = db.query(ApprovalStep).filter(ApprovalStep.form_id == form.id).order_by(ApprovalStep.step_order).all()
    result = FormOut.model_validate(form).model_dump()
    result["approvals"] = [ApprovalStepOut.model_validate(s).model_dump() for s in steps]
    result["form_type_label"] = FORM_TYPE_LABELS.get(form.form_type, form.form_type)
    return result


@router.post("/{form_id}/submit")
def submit_form(
    form_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """提交表单进入审批流程"""
    form = db.query(Form).filter(Form.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="表单不存在")
    if form.created_by != current_user.username and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="只能提交自己创建的表单")
    if form.status not in ("draft", "rejected"):
        raise HTTPException(status_code=400, detail="当前状态不可提交")

    # 重置审批链
    steps = db.query(ApprovalStep).filter(ApprovalStep.form_id == form.id).all()
    for s in steps:
        s.decision = None
        s.comment = None
        s.decided_by = None
        s.decided_at = None

    form.status = "pending"
    form.current_step = 0
    db.commit()
    return {"message": "已提交审批"}


@router.post("/{form_id}/approve")
def decide_form(
    form_id: int,
    body: ApprovalDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """审批表单（通过/驳回）"""
    form = db.query(Form).filter(Form.id == form_id).first()
    if not form or form.status != "pending":
        raise HTTPException(status_code=400, detail="表单状态不正确")

    step = (
        db.query(ApprovalStep)
        .filter(
            ApprovalStep.form_id == form_id,
            ApprovalStep.step_order == form.current_step,
        )
        .first()
    )
    if not step:
        raise HTTPException(status_code=400, detail="审批步骤不存在")
    if step.approver_role != current_user.role and current_user.role != "admin":
        raise HTTPException(status_code=403, detail=f"需要 {step.approver_role} 角色审批")
    if step.decision is not None:
        raise HTTPException(status_code=400, detail="该步骤已审批")

    step.decision = body.decision
    step.comment = body.comment
    step.decided_by = current_user.username
    step.decided_at = datetime.utcnow()

    if body.decision == "rejected":
        form.status = "rejected"
    elif body.decision == "approved":
        # 检查是否还有后续步骤
        total_steps = db.query(ApprovalStep).filter(ApprovalStep.form_id == form_id).count()
        if form.current_step + 1 >= total_steps:
            form.status = "approved"
        else:
            form.current_step += 1
    db.commit()
    return {"message": "审批成功", "new_status": form.status}


@router.delete("/{form_id}")
def delete_form(
    form_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除表单（仅草稿或创建者本人/管理员）"""
    form = db.query(Form).filter(Form.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="表单不存在")
    if form.created_by != current_user.username and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限删除")
    if form.status not in ("draft", "rejected") and current_user.role != "admin":
        raise HTTPException(status_code=400, detail="审批中的表单不可删除")
    db.delete(form)
    db.commit()
    return {"message": "删除成功"}
