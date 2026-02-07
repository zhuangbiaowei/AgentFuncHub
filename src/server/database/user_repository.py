"""
用户 Repository
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from .models import User
import uuid


class UserRepository:
    """用户数据访问层"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, user_id: str) -> Optional[User]:
        """通过 ID 获取用户"""
        try:
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
            return self.db.query(User).filter(User.id == user_uuid).first()
        except ValueError:
            return None
    
    def get_by_username(self, username: str) -> Optional[User]:
        """通过用户名获取用户"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """通过邮箱获取用户"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_by_github_id(self, github_id: str) -> Optional[User]:
        """通过 GitHub ID 获取用户"""
        return self.db.query(User).filter(User.github_id == github_id).first()
    
    def get_by_api_key(self, api_key: str) -> Optional[User]:
        """通过 API Key 获取用户"""
        return self.db.query(User).filter(User.api_key == api_key).first()
    
    def create(self, username: str, email: str, 
               hashed_password: Optional[str] = None,
               github_id: Optional[str] = None,
               avatar_url: Optional[str] = None,
               api_key: Optional[str] = None) -> User:
        """创建新用户"""
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            github_id=github_id,
            avatar_url=avatar_url,
            api_key=api_key
        )
        self.db.add(user)
        self.db.flush()  # 获取 ID
        return user
    
    def update(self, user: User) -> User:
        """更新用户信息"""
        self.db.merge(user)
        self.db.flush()
        return user
    
    def delete(self, user_id: str) -> bool:
        """删除用户"""
        user = self.get_by_id(user_id)
        if user:
            self.db.delete(user)
            return True
        return False
    
    def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """列出用户"""
        return self.db.query(User).offset(skip).limit(limit).all()
    
    def search_users(self, query: str) -> List[User]:
        """搜索用户"""
        return self.db.query(User).filter(
            or_(
                User.username.ilike(f"%{query}%"),
                User.email.ilike(f"%{query}%")
            )
        ).all()
