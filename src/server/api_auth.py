"""
认证 API 路由
提供用户注册、登录、GitHub OAuth 等功能
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
from sqlalchemy.orm import Session

from auth import (
    create_access_token, create_refresh_token, 
    get_user_id_from_token, verify_refresh_token,
    Token
)
from github_oauth import (
    get_github_authorize_url, exchange_code_for_token,
    get_github_user, get_github_user_emails
)
from database import get_db_session
from database.user_repository import UserRepository
from database.models import User
import secrets
import os

router = APIRouter(prefix="/auth", tags=["认证"])
security = HTTPBearer(auto_error=False)

# 配置
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


# 请求/响应模型
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    is_active: bool
    created_at: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class APIKeyResponse(BaseModel):
    api_key: str
    message: str


# 依赖: 获取当前用户
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db_session)
) -> User:
    """获取当前登录用户"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing authorization token")
    
    user_id = get_user_id_from_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is deactivated")
    
    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db_session)
) -> Optional[User]:
    """可选获取当前用户（用于公开接口）"""
    if not credentials:
        return None
    
    user_id = get_user_id_from_token(credentials.credentials)
    if not user_id:
        return None
    
    repo = UserRepository(db)
    return repo.get_by_id(user_id)


# ===== 用户注册/登录 API =====

@router.post("/register", response_model=Token)
async def register(data: UserRegister, db: Session = Depends(get_db_session)):
    """用户注册"""
    repo = UserRepository(db)
    
    # 检查用户名是否已存在
    if repo.get_by_username(data.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # 检查邮箱是否已存在
    if repo.get_by_email(data.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # 创建用户
    user = repo.create(
        username=data.username,
        email=data.email,
    )
    
    # 生成 Token
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=1800  # 30 minutes
    )


@router.post("/login", response_model=Token)
async def login(data: UserLogin, db: Session = Depends(get_db_session)):
    """用户登录（用户名/密码）"""
    repo = UserRepository(db)
    
    user = repo.get_by_username(data.username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # TODO: 验证密码（需要添加密码字段到 User 模型）
    # 暂时只支持 GitHub OAuth 登录
    raise HTTPException(status_code=400, detail="Please use GitHub OAuth login")


@router.post("/refresh", response_model=Token)
async def refresh_token(data: RefreshTokenRequest):
    """刷新访问令牌"""
    user_id = verify_refresh_token(data.refresh_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=1800
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return UserResponse(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        full_name=getattr(current_user, 'full_name', None),
        avatar_url=current_user.avatar_url,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat() if current_user.created_at else None
    )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """用户登出（客户端删除 Token）"""
    # JWT 是无状态的，登出只需客户端删除 Token
    # 如需实现 Token 黑名单，需要 Redis 等存储
    return {"message": "Logout successful"}


# ===== GitHub OAuth API =====

@router.get("/github/login")
async def github_login():
    """GitHub OAuth 登录入口"""
    # 生成随机 state 防止 CSRF
    state = secrets.token_urlsafe(32)
    authorize_url = await get_github_authorize_url(state)
    
    return {
        "authorization_url": authorize_url,
        "state": state
    }


@router.get("/github/callback")
async def github_callback(
    code: str,
    state: Optional[str] = None,
    db: Session = Depends(get_db_session)
):
    """GitHub OAuth 回调"""
    # 交换 code 获取 access_token
    access_token = await exchange_code_for_token(code)
    if not access_token:
        raise HTTPException(status_code=400, detail="Failed to get access token from GitHub")
    
    # 获取 GitHub 用户信息
    github_user = await get_github_user(access_token)
    if not github_user:
        raise HTTPException(status_code=400, detail="Failed to get user info from GitHub")
    
    # 获取邮箱
    emails = await get_github_user_emails(access_token)
    primary_email = None
    if emails:
        for email_data in emails:
            if email_data.get("primary"):
                primary_email = email_data.get("email")
                break
        if not primary_email:
            primary_email = emails[0].get("email")
    
    github_id = str(github_user.get("id"))
    username = github_user.get("login")
    email = primary_email or github_user.get("email")
    avatar_url = github_user.get("avatar_url")
    name = github_user.get("name")
    
    repo = UserRepository(db)
    
    # 查找或创建用户
    user = repo.get_by_github_id(github_id)
    
    if not user:
        # 检查用户名是否已存在
        existing = repo.get_by_username(username)
        if existing:
            # 添加随机后缀
            username = f"{username}_{secrets.token_hex(4)}"
        
        # 创建新用户
        user = repo.create(
            username=username,
            email=email or f"{username}@github.com",  # 备用邮箱
            github_id=github_id,
            avatar_url=avatar_url
        )
        print(f"✅ Created new user: {username} (GitHub ID: {github_id})")
    else:
        print(f"✅ Existing user logged in: {username}")
    
    # 生成 Token
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    
    # 构建前端回调 URL
    redirect_url = f"{FRONTEND_URL}/auth/callback?"
    redirect_url += f"access_token={access_token}"
    redirect_url += f"&refresh_token={refresh_token}"
    redirect_url += f"&token_type=bearer"
    redirect_url += f"&expires_in=1800"
    
    return RedirectResponse(url=redirect_url)


# ===== API Key 管理 =====

@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    name: str = "Default API Key",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """创建新的 API Key"""
    # 生成 API Key
    api_key = f"afh_{secrets.token_urlsafe(32)}"
    
    # 更新用户 API Key
    current_user.api_key = api_key
    repo = UserRepository(db)
    repo.update(current_user)
    
    return APIKeyResponse(
        api_key=api_key,
        message="API Key created successfully. Store it safely - it won't be shown again."
    )


@router.get("/api-keys")
async def list_api_keys(current_user: User = Depends(get_current_user)):
    """列出用户的 API Keys"""
    # 目前每个用户只有一个 API Key
    if current_user.api_key:
        return {
            "api_keys": [{
                "name": "Default",
                "preview": current_user.api_key[:8] + "...",
                "created_at": current_user.created_at.isoformat() if current_user.created_at else None
            }]
        }
    return {"api_keys": []}


@router.delete("/api-keys")
async def revoke_api_key(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """撤销 API Key"""
    current_user.api_key = None
    repo = UserRepository(db)
    repo.update(current_user)
    
    return {"message": "API Key revoked successfully"}
