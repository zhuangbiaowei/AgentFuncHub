"""
数据库连接和会话管理
"""

import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

# 数据库连接配置
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/agentfunchub"
)

# 创建引擎
engine = create_engine(
    DATABASE_URL,
    echo=False,  # 设置为 True 查看 SQL 日志
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True  # 自动检测断开的连接
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话的上下文管理器
    
    用法:
        with get_db() as db:
            user = db.query(User).first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_session() -> Session:
    """
    获取数据库会话 (用于依赖注入)
    
    用法:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db_session)):
            return db.query(User).all()
    """
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()


def init_db():
    """初始化数据库 (创建表)"""
    from .models import Base
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")


def reset_db():
    """重置数据库 (删除并重新创建表)"""
    from .models import Base
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✅ Database reset complete")
