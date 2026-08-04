from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from app.schemas.common import ORMModel


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(ORMModel):
    id: int
    username: str
    role: str


class UserCreate(BaseModel):
    username: str
    password: str
    role: Optional[str] = "user"


class UserUpdate(BaseModel):
    password: Optional[str] = None
    role: Optional[str] = None
