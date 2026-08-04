"""
认证相关API路由：登录、获取当前用户、用户管理
"""
from datetime import timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core import security
from app.core.config import settings
from app.api.deps import get_current_user, require_role
from app.models.user import User
from app.schemas.auth import Token, LoginRequest, UserOut, UserCreate, UserUpdate

router = APIRouter()


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """用户名密码登录，返回JWT Token"""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = security.create_access_token(
        subject=user.username,
        expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login-json", response_model=Token)
def login_json(body: LoginRequest, db: Session = Depends(get_db)):
    """JSON Body方式登录（前端Axios更友好）"""
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not security.verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    access_token = security.create_access_token(
        subject=user.username,
        expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return current_user


@router.get("/users", response_model=List[UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """[管理员] 获取所有用户列表"""
    return db.query(User).order_by(User.id).all()


@router.post("/users", response_model=UserOut)
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """[管理员] 创建新用户"""
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = User(
        username=body.username,
        hashed_password=security.hash_password(body.password),
        role=body.role or "user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    body: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """[管理员] 更新用户信息"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if body.role is not None:
        user.role = body.role
    if body.password:
        user.hashed_password = security.hash_password(body.password)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """[管理员] 删除用户"""
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.delete(user)
    db.commit()
    return {"message": "删除成功"}
