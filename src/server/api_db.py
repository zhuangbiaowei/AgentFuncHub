"""
数据库版本的 API 端点
支持 PostgreSQL 存储
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging

# 导入数据库相关
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from database import get_db_session
from database.repository import FunctionRepository, UserRepository
from database.models import Function

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/db", tags=["database"])


def get_db():
    """获取数据库会话"""
    db = get_db_session()
    try:
        yield db
    finally:
        db.close()


@router.get("/functions")
async def list_functions_db(
    language: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """列出所有函数 (数据库版本)"""
    repo = FunctionRepository(db)
    
    tags = [tag] if tag else None
    functions, total = repo.list_all(
        language=language,
        tags=tags,
        limit=limit,
        offset=offset
    )
    
    return {
        "success": True,
        "total": total,
        "limit": limit,
        "offset": offset,
        "spec_version": "0.1",
        "functions": [f.to_dict() for f in functions]
    }


@router.get("/functions/{function_id}")
async def get_function_db(function_id: str, db: Session = Depends(get_db)):
    """获取函数详情 (数据库版本)"""
    repo = FunctionRepository(db)
    func = repo.get_by_id(function_id)
    
    if not func:
        raise HTTPException(status_code=404, detail="Function not found")
    
    # 增加查看次数
    repo.increment_view_count(function_id)
    
    return {
        "success": True,
        "spec_version": "0.1",
        "function": func.to_dict()
    }


@router.get("/tags")
async def get_tags_db(db: Session = Depends(get_db)):
    """获取所有标签 (数据库版本)"""
    repo = FunctionRepository(db)
    tags = repo.get_tags()
    
    return {
        "success": True,
        "tags": tags
    }


@router.get("/languages")
async def get_languages_db(db: Session = Depends(get_db)):
    """获取所有语言 (数据库版本)"""
    repo = FunctionRepository(db)
    languages = repo.get_languages()
    
    return {
        "success": True,
        "languages": languages
    }


@router.post("/search")
async def search_functions_db(
    query: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """搜索函数 (数据库版本 - 全文搜索)"""
    repo = FunctionRepository(db)
    
    query_text = query.get("query", "")
    language = query.get("language")
    limit = query.get("limit", 10)
    
    try:
        functions = repo.search_fulltext(query_text, language, limit)
    except Exception as e:
        logger.error(f"Search error: {e}")
        # 降级到普通列表
        functions, _ = repo.list_all(language=language, limit=limit)
    
    return {
        "success": True,
        "query": query_text,
        "total": len(functions),
        "spec_version": "0.1",
        "search_method": "fulltext",
        "results": [
            {
                "function_id": f.spec_id,
                "name": f.name,
                "description": f.description,
                "spec": f.to_dict()
            }
            for f in functions
        ]
    }
