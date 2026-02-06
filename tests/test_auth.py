#!/usr/bin/env python3
"""
测试认证系统
"""
import pytest
import sys
import os
import uuid

# 确保使用 SQLite 模式
os.environ["USE_SQLITE"] = "true"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"

sys.path.insert(0, '/home/mlf/AgentFuncHub/src/server')

from database import init_db, reset_db, SessionLocal
from database.models import User
from database.user_repository import UserRepository

# 尝试导入认证模块
try:
    from auth import (
        create_access_token, create_refresh_token,
        get_user_id_from_token, verify_refresh_token
    )
    AUTH_AVAILABLE = True
except ImportError as e:
    AUTH_AVAILABLE = False
    print(f"⚠️ Auth module not available: {e}")


@pytest.fixture(scope="module")
def setup_database():
    """模块级别的数据库初始化"""
    reset_db()
    yield
    # 模块结束后的清理


@pytest.fixture
def db_session():
    """提供数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user(db_session):
    """创建测试用户"""
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


@pytest.mark.skipif(not AUTH_AVAILABLE, reason="Auth module not available")
class TestAuthentication:
    """测试认证系统"""
    
    def test_create_access_token(self, setup_database, test_user):
        """测试生成 Access Token"""
        token = create_access_token(str(test_user.id))
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 30  # JWT token 应该比较长
    
    def test_create_refresh_token(self, setup_database, test_user):
        """测试生成 Refresh Token"""
        token = create_refresh_token(str(test_user.id))
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 30
    
    def test_verify_access_token(self, setup_database, test_user):
        """测试验证 Access Token"""
        token = create_access_token(str(test_user.id))
        user_id = get_user_id_from_token(token)
        assert user_id == str(test_user.id)
    
    def test_verify_refresh_token(self, setup_database, test_user):
        """测试验证 Refresh Token"""
        token = create_refresh_token(str(test_user.id))
        user_id = verify_refresh_token(token)
        assert user_id == str(test_user.id)
    
    def test_invalid_token(self, setup_database):
        """测试无效 token"""
        # 应该抛出异常或返回 None
        try:
            result = get_user_id_from_token("invalid.token.here")
            # 如果返回了结果，应该是无效的
            assert result is None or result == ""
        except Exception:
            # 抛出异常也是可接受的
            pass


class TestUserRepository:
    """测试用户仓库"""
    
    def test_create_user(self, setup_database, db_session):
        """测试创建用户"""
        unique_suffix = str(uuid.uuid4())[:8]
        user = User(
            username=f"repo_test_{unique_suffix}",
            email=f"repo_{unique_suffix}@example.com"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.id is not None
        assert user.username == f"repo_test_{unique_suffix}"
        
        # 清理
        db_session.delete(user)
        db_session.commit()
    
    def test_get_user_by_id(self, setup_database, db_session, test_user):
        """测试通过 ID 查询用户"""
        repo = UserRepository(db_session)
        found = repo.get_by_id(str(test_user.id))
        assert found is not None
        assert found.username == test_user.username
        assert found.email == test_user.email
    
    def test_get_user_by_username(self, setup_database, db_session, test_user):
        """测试通过用户名查询用户"""
        repo = UserRepository(db_session)
        found = repo.get_by_username(test_user.username)
        assert found is not None
        assert found.id == test_user.id
    
    def test_get_user_by_email(self, setup_database, db_session, test_user):
        """测试通过邮箱查询用户"""
        repo = UserRepository(db_session)
        found = repo.get_by_email(test_user.email)
        assert found is not None
        assert found.id == test_user.id
    
    def test_get_user_by_github_id(self, setup_database, db_session, test_user):
        """测试通过 GitHub ID 查询用户"""
        repo = UserRepository(db_session)
        found = repo.get_by_github_id(test_user.github_id)
        assert found is not None
        assert found.id == test_user.id
    
    def test_user_not_found(self, setup_database, db_session):
        """测试查询不存在的用户"""
        repo = UserRepository(db_session)
        found = repo.get_by_id("00000000-0000-0000-0000-000000000000")
        assert found is None


class TestUserModel:
    """测试用户模型"""
    
    def test_user_creation(self, setup_database, db_session):
        """测试用户创建"""
        unique_suffix = str(uuid.uuid4())[:8]
        user = User(
            username=f"model_test_{unique_suffix}",
            email=f"model_{unique_suffix}@example.com",
            is_active=True,
            is_admin=False
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.is_active is True
        assert user.is_admin is False
        assert user.created_at is not None
        
        # 清理
        db_session.delete(user)
        db_session.commit()
    
    def test_user_relationships(self, setup_database, db_session):
        """测试用户关系"""
        # 用户模型应该有 functions, executions, ratings 关系
        unique_id = str(uuid.uuid4())[:8]
        user = User(
            username=f"rel_test_{unique_id}",
            email=f"rel_{unique_id}@example.com"
        )
        db_session.add(user)
        db_session.commit()
        
        # 检查关系属性存在
        assert hasattr(user, 'functions')
        assert hasattr(user, 'executions')
        assert hasattr(user, 'ratings')
        
        # 清理
        db_session.delete(user)
        db_session.commit()
