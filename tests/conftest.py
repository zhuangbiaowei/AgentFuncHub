"""
AgentFuncHub 测试配置
支持 SQLite 模式运行，避免依赖 PostgreSQL
"""

import os
import sys
import pytest
from pathlib import Path

# 确保使用 SQLite 模式运行测试
os.environ["USE_SQLITE"] = "true"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["TESTING"] = "true"

# 添加 src/server 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "server"))

# 导入并初始化数据库
from database import init_db, reset_db
from database.models import User, Function, Execution, Rating
from database import SessionLocal


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """在整个测试会话开始时初始化数据库"""
    # 重置数据库（删除并重新创建表）
    reset_db()
    print("\n[TEST] Test database initialized (SQLite mode)")
    yield
    # 测试会话结束后的清理
    print("\n[TEST] Test session completed")


@pytest.fixture
def db_session():
    """提供数据库会话，每个测试函数独立"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user(db_session):
    """创建测试用户"""
    import uuid
    unique_suffix = str(uuid.uuid4())[:8]
    user = User(
        username=f"testuser_{unique_suffix}",
        email=f"test_{unique_suffix}@example.com",
        github_id=f"github_{unique_suffix}"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    yield user
    # 清理
    db_session.delete(user)
    db_session.commit()


@pytest.fixture
def sample_function_spec():
    """返回一个示例函数规范"""
    return {
        "spec_version": "0.1",
        "id": "test.function.sample",
        "version": "1.0.0",
        "name": "Test Sample Function",
        "description": "A sample function for testing",
        "language": {"name": "python", "runtime": "python>=3.8"},
        "entrypoint": {
            "kind": "inline",
            "symbol": "test_func",
            "code": "def test_func(x): return x * 2"
        },
        "signature": {
            "inputs": {
                "x": {"type": "integer", "required": True, "description": "Input value"}
            },
            "outputs": {
                "result": {"type": "integer", "description": "Output value"}
            }
        },
        "tags": ["test", "sample"]
    }


@pytest.fixture(autouse=True)
def mock_vector_search(monkeypatch):
    """模拟向量搜索服务，避免加载大型模型"""
    class MockVectorSearchService:
        def __init__(self):
            self.model = None
            self.model_name = "mock"
            self.function_ids = []
        
        def add_function(self, func_id, data):
            self.function_ids.append(func_id)
            return True
        
        def search(self, query, top_k=10):
            return []
        
        def search_hybrid(self, query, matches, top_k=10):
            return [(m, 0.5) for m in matches[:top_k]]
    
    # 模拟 vector_search 模块
    monkeypatch.setattr(
        "main.vector_service",
        MockVectorSearchService()
    )
