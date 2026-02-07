"""
数据库连接和会话管理
支持 PostgreSQL 和 SQLite
"""

import os
from contextlib import contextmanager
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

# 数据库连接配置
# 优先使用 PostgreSQL，如果不存在则使用 SQLite
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    # 尝试连接本地 PostgreSQL
    "postgresql://postgres:postgres@localhost:5432/agentfunchub"
)

# 如果没有 PostgreSQL，使用 SQLite
SQLITE_URL = "sqlite:///./agentfunchub.db"

def get_database_url():
    """获取数据库 URL"""
    # 检查是否强制使用 SQLite
    if os.getenv("USE_SQLITE", "false").lower() == "true":
        return SQLITE_URL
    return DATABASE_URL

# 创建引擎
engine_url = get_database_url()

if engine_url.startswith("sqlite"):
    # SQLite 配置
    engine = create_engine(
        engine_url,
        echo=False,
        connect_args={"check_same_thread": False}  # SQLite 需要这个
    )
    USE_SQLITE = True
else:
    # PostgreSQL 配置
    engine = create_engine(
        engine_url,
        echo=False,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True
    )
    USE_SQLITE = False

print(f"[DB] Using database: {'SQLite' if USE_SQLITE else 'PostgreSQL'}")

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    获取数据库会话的上下文管理器
    
    用法:
        with get_db_context() as db:
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


# 为向后兼容保留别名
get_db = get_db_context


def get_db_session() -> Generator[Session, None, None]:
    """
    获取数据库会话 (用于依赖注入)
    
    用法:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db_session)):
            return db.query(User).all()
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


def init_db():
    """初始化数据库 (创建表)"""
    from .models import Base
    Base.metadata.create_all(bind=engine)
    _ensure_auth_columns()
    print("[OK] Database tables created")


def reset_db():
    """重置数据库 (删除并重新创建表)"""
    from .models import Base
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("[OK] Database reset complete")


def _ensure_auth_columns():
    """确保认证相关列存在，避免旧库缺列导致注册/登录失败。"""
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    user_columns = {col["name"] for col in inspector.get_columns("users")}
    if "hashed_password" in user_columns:
        return

    alter_sql = "ALTER TABLE users ADD COLUMN hashed_password VARCHAR(255)"
    with engine.begin() as conn:
        conn.execute(text(alter_sql))
    print("[OK] Added missing column users.hashed_password")
