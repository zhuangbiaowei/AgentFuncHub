"""
数据库 CRUD 操作
Function 模型的数据库操作封装
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from .models import Function, User


class FunctionRepository:
    """函数数据仓库"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, func_data: Dict[str, Any]) -> Function:
        """创建函数"""
        func = Function(**func_data)
        self.db.add(func)
        self.db.commit()
        self.db.refresh(func)
        return func
    
    def get_by_id(self, func_id: str) -> Optional[Function]:
        """通过 spec_id 获取函数"""
        return self.db.query(Function).filter(Function.spec_id == func_id).first()
    
    def get_by_db_id(self, db_id: str) -> Optional[Function]:
        """通过数据库 UUID 获取函数"""
        return self.db.query(Function).filter(Function.id == db_id).first()
    
    def list_all(
        self,
        language: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10,
        offset: int = 0
    ) -> tuple[List[Function], int]:
        """列出所有函数"""
        query = self.db.query(Function)
        
        # 过滤条件
        if language:
            query = query.filter(Function.language == language)
        
        if tags:
            # 包含所有指定标签
            for tag in tags:
                query = query.filter(Function.tags.contains([tag]))
        
        # 总数
        total = query.count()
        
        # 分页
        functions = query.order_by(Function.created_at.desc()).offset(offset).limit(limit).all()
        
        return functions, total
    
    def search_fulltext(
        self,
        query_text: str,
        language: Optional[str] = None,
        limit: int = 10
    ) -> List[Function]:
        """全文搜索"""
        # 使用 PostgreSQL 全文搜索
        from sqlalchemy import text
        
        # 构建查询
        sql = """
            SELECT * FROM functions
            WHERE search_text @@ plainto_tsquery('chinese', :query)
        """
        
        if language:
            sql += " AND language = :language"
        
        sql += " ORDER BY ts_rank(search_text, plainto_tsquery('chinese', :query)) DESC LIMIT :limit"
        
        result = self.db.execute(
            text(sql),
            {"query": query_text, "language": language, "limit": limit}
        )
        
        # 转换为 Function 对象
        rows = result.mappings().all()
        
        # 获取完整的 Function 对象
        spec_ids = [row["spec_id"] for row in rows]
        functions = self.db.query(Function).filter(Function.spec_id.in_(spec_ids)).all()
        
        # 按搜索结果排序
        func_map = {f.spec_id: f for f in functions}
        return [func_map[sid] for sid in spec_ids if sid in func_map]
    
    def update(self, func_id: str, update_data: Dict[str, Any]) -> Optional[Function]:
        """更新函数"""
        func = self.get_by_id(func_id)
        if not func:
            return None
        
        for key, value in update_data.items():
            setattr(func, key, value)
        
        self.db.commit()
        self.db.refresh(func)
        return func
    
    def delete(self, func_id: str) -> bool:
        """删除函数"""
        func = self.get_by_id(func_id)
        if not func:
            return False
        
        self.db.delete(func)
        self.db.commit()
        return True
    
    def increment_view_count(self, func_id: str) -> None:
        """增加查看次数"""
        self.db.query(Function).filter(Function.spec_id == func_id).update(
            {"view_count": Function.view_count + 1}
        )
        self.db.commit()
    
    def increment_call_count(self, func_id: str) -> None:
        """增加调用次数"""
        self.db.query(Function).filter(Function.spec_id == func_id).update(
            {"call_count": Function.call_count + 1}
        )
        self.db.commit()
    
    def get_tags(self) -> List[str]:
        """获取所有标签"""
        result = self.db.query(Function.tags).all()
        tags = set()
        for row in result:
            tags.update(row[0] or [])
        return sorted(list(tags))
    
    def get_languages(self) -> List[str]:
        """获取所有语言"""
        result = self.db.query(Function.language).distinct().all()
        return sorted([row[0] for row in result])


class UserRepository:
    """用户数据仓库"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, user_data: Dict[str, Any]) -> User:
        """创建用户"""
        user = User(**user_data)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_by_id(self, user_id: str) -> Optional[User]:
        """通过 ID 获取用户"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_username(self, username: str) -> Optional[User]:
        """通过用户名获取用户"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_by_github_id(self, github_id: str) -> Optional[User]:
        """通过 GitHub ID 获取用户"""
        return self.db.query(User).filter(User.github_id == github_id).first()
    
    def get_by_api_key(self, api_key: str) -> Optional[User]:
        """通过 API Key 获取用户"""
        return self.db.query(User).filter(User.api_key == api_key).first()
    
    def update(self, user_id: str, update_data: Dict[str, Any]) -> Optional[User]:
        """更新用户"""
        user = self.get_by_id(user_id)
        if not user:
            return None
        
        for key, value in update_data.items():
            setattr(user, key, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user
