"""
GitHub OAuth 集成
"""

import httpx
from typing import Optional, Dict, Any
import os
from pydantic import BaseModel

# GitHub OAuth 配置
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:8000/auth/github/callback")

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"


class GitHubUser(BaseModel):
    """GitHub 用户信息"""
    id: str
    login: str
    email: Optional[str] = None
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None


async def get_github_authorize_url(state: Optional[str] = None) -> str:
    """获取 GitHub 授权 URL"""
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": GITHUB_REDIRECT_URI,
        "scope": "user:email",
    }
    if state:
        params["state"] = state
    
    query = "&".join([f"{k}={v}" for k, v in params.items()])
    return f"{GITHUB_AUTH_URL}?{query}"


async def exchange_code_for_token(code: str) -> Optional[str]:
    """用授权码交换访问令牌"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GITHUB_TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": GITHUB_REDIRECT_URI,
            },
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        return None


async def get_github_user(access_token: str) -> Optional[Dict[str, Any]]:
    """获取 GitHub 用户信息"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            GITHUB_USER_URL,
            headers={
                "Authorization": f"token {access_token}",
                "Accept": "application/vnd.github.v3+json",
            },
        )
        
        if response.status_code == 200:
            return response.json()
        return None


async def get_github_user_emails(access_token: str) -> Optional[list]:
    """获取 GitHub 用户邮箱列表"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.github.com/user/emails",
            headers={
                "Authorization": f"token {access_token}",
                "Accept": "application/vnd.github.v3+json",
            },
        )
        
        if response.status_code == 200:
            return response.json()
        return None
