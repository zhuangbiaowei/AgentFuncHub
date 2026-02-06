# Release v0.2.0 - MVP 完整版

**发布日期**: 2026-02-06  
**代号**: Phase 2 Complete  
**状态**: 🎉 Ready for Release

---

## 🎯 版本亮点

AgentFuncHub v0.2.0 是 MVP (最小可行产品) 完整版，在 v0.1.0 的基础上新增了：

- ✅ **用户认证系统** - JWT + GitHub OAuth
- ✅ **数据库支持** - SQLite/PostgreSQL
- ✅ **Web 前端界面** - React + Ant Design
- ✅ **Python SDK** - 同步/异步客户端
- ✅ **Docker 化部署** - 一键启动
- ✅ **完整测试覆盖** - 57 个测试全部通过

---

## 📦 新功能

### 1. 用户认证系统

```bash
# 用户注册
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "email": "test@example.com", "password": "secret"}'

# GitHub OAuth 登录
# 访问: http://localhost:8000/auth/github/login
```

**包含**:
- JWT Token 认证 (access + refresh)
- GitHub OAuth 集成
- API Key 管理
- 用户权限控制

### 2. 数据库支持

**SQLite (默认)**:
```bash
export USE_SQLITE=true
```

**PostgreSQL (可选)**:
```bash
export USE_SQLITE=false
export DATABASE_URL=postgresql://user:pass@localhost:5432/agentfunchub
```

**包含**:
- SQLAlchemy 2.0 ORM
- 完整的数据库模型 (User, Function, Execution, Rating)
- 自动表创建
- 数据迁移支持

### 3. Web 前端界面

```bash
# Docker 启动
docker-compose up -d

# 访问
前端: http://localhost:3000
后端: http://localhost:8000
```

**页面**:
- 🏠 首页 - 函数列表
- 📖 函数详情 - 查看和测试函数
- ➕ 发布函数 - 提交新函数
- 👤 用户中心 - 管理个人信息和 API Keys

### 4. Python SDK

```python
from agentfunchub import Client

# 创建客户端
client = Client(base_url="http://localhost:8000")

# 搜索函数
results = client.search("验证邮箱", limit=5)

# 获取函数
func = client.get_function("validation.email.basic")

# 执行函数
result = client.call("validation.email.basic", email="test@example.com")

# 异步支持
from agentfunchub import AsyncClient

async with AsyncClient() as client:
    func = await client.get_function("validation.email.basic")
    result = await func.execute(email="test@example.com")
```

**安装**:
```bash
cd src/sdk/python
pip install -e .
```

### 5. Docker 化部署

```bash
# 1. 克隆仓库
git clone https://github.com/zhuangbiaowei/AgentFuncHub.git
cd AgentFuncHub

# 2. 配置环境变量 (可选)
echo "JWT_SECRET_KEY=your-secret-key" > .env

# 3. 一键启动
docker-compose up -d

# 4. 查看状态
docker-compose ps
docker-compose logs -f
```

**服务**:
- 后端 API: `localhost:8000`
- 前端界面: `localhost:3000`

### 6. 沙箱执行器

```bash
# 执行函数
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "function_id": "validation.email.basic",
    "input": {"email": "test@example.com"}
  }'
```

**特性**:
- Docker 沙箱隔离
- 执行超时控制 (默认 30s)
- 内存限制 (默认 128MB)
- 执行日志记录

---

## 🧪 测试覆盖

```
============================= test session starts ==============================
platform linux -- Python 3.10.12, pytest-7.4.3
collected 57 items

tests/test_api.py .............. 21 passed
tests/test_auth.py .............. 16 passed
tests/test_integration.py ....... 20 passed

======================== 57 passed, 9 warnings =========================
```

**测试配置**:
- 自动使用 SQLite 模式
- 模拟向量搜索服务
- 支持并行测试

---

## 📚 文档

### 新增文档
- `docs/deployment.md` - 部署指南
- `docs/database-schema.md` - 数据库设计
- `src/sdk/python/README.md` - SDK 文档
- `CHANGELOG.md` - 更新日志

### 更新文档
- `README.md` - 项目总览
- `STATUS.md` - 项目状态

---

## 🔧 技术栈

| 层级 | 技术 |
|------|------|
| **后端** | Python 3.11 + FastAPI |
| **前端** | React 19 + TypeScript + Vite + Ant Design |
| **数据库** | SQLite (默认) / PostgreSQL (可选) |
| **ORM** | SQLAlchemy 2.0 |
| **搜索** | sentence-transformers + scikit-learn |
| **沙箱** | Docker |
| **测试** | pytest |
| **CI/CD** | GitHub Actions |

---

## 🚀 快速开始

### 开发环境

```bash
# 1. 克隆仓库
git clone https://github.com/zhuangbiaowei/AgentFuncHub.git
cd AgentFuncHub

# 2. 安装依赖
pip install -r requirements.txt

# 3. 初始化数据库
export USE_SQLITE=true
cd src/server
python -c "from database import init_db; init_db()"

# 4. 启动服务
python main.py

# 5. 运行测试
cd ../..
python -m pytest tests/ -v
```

### Docker 部署

```bash
docker-compose up -d
```

---

## 📊 统计数据

| 指标 | v0.1.0 | v0.2.0 | 增长 |
|------|--------|--------|------|
| 示例函数 | 26 | 26 | - |
| API 端点 | 9 | 18 | +9 |
| 测试用例 | 21 | 57 | +36 |
| 代码行数 | ~3000 | ~9000 | +6000 |
| 文档页数 | 8 | 11 | +3 |

---

## 🎉 致谢

感谢所有贡献者和社区成员的支持！

---

## 📋 发布检查清单

- [x] 所有测试通过 (57/57)
- [x] 文档已更新
- [x] Docker 配置验证
- [x] CHANGELOG.md 已创建
- [x] 版本号已更新
- [x] Git tag 已推送
- [x] GitHub Release 已创建

---

**完整变更**: [v0.1.0...v0.2.0](https://github.com/zhuangbiaowei/AgentFuncHub/compare/v0.1.0...v0.2.0)

**下载**: 
- Source: https://github.com/zhuangbiaowei/AgentFuncHub/archive/v0.2.0.tar.gz
- Docker: `docker pull agentfunchub/backend:v0.2.0`

---

*Made with ❤️ for AI Agents*
