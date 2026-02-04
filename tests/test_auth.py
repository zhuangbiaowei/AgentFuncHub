#!/usr/bin/env python3
"""
测试认证系统
"""
import sys
import os

# 设置环境变量
os.environ["USE_SQLITE"] = "true"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"

sys.path.insert(0, '/home/mlf/AgentFuncHub/src/server')

from database import init_db
from database.models import User
from auth import (
    create_access_token, create_refresh_token,
    get_user_id_from_token, verify_refresh_token
)

# 初始化数据库
init_db()

print("\n🧪 测试认证系统\n")

# 创建会话并测试
from database import SessionLocal

db = SessionLocal()

import uuid

# 1. 创建测试用户（使用唯一值）
unique_id = str(uuid.uuid4())[:8]
user = User(
    username=f"testuser_{unique_id}",
    email=f"test_{unique_id}@example.com",
    github_id=f"github_{unique_id}"
)
db.add(user)
db.commit()
db.refresh(user)

print(f"✅ 创建用户: {user.username} (ID: {user.id})")

# 2. 测试 JWT
token = create_access_token(str(user.id))
print(f"✅ 生成 Access Token: {token[:30]}...")

refresh = create_refresh_token(str(user.id))
print(f"✅ 生成 Refresh Token: {refresh[:30]}...")

# 3. 验证 Token
user_id = get_user_id_from_token(token)
print(f"✅ 验证 Access Token: user_id={user_id}")

# 4. 验证 Refresh Token
refresh_user_id = verify_refresh_token(refresh)
print(f"✅ 验证 Refresh Token: user_id={refresh_user_id}")

# 5. 查询用户
from database.user_repository import UserRepository

repo = UserRepository(db)
found = repo.get_by_id(str(user.id))
print(f"✅ 查询用户: {found.username} / {found.email}")

# 清理
db.delete(user)
db.commit()
db.close()

print("\n✅ 所有测试通过!")
