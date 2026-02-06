# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-02-06

### Added

#### 用户认证系统
- JWT Token 认证 (`src/server/auth.py`)
- GitHub OAuth 集成 (`src/server/github_oauth.py`)
- 用户注册/登录 API (`src/server/api_auth.py`)
- API Key 管理

#### 数据库支持
- SQLAlchemy ORM 模型 (`src/server/database/models.py`)
- SQLite 支持 (默认)
- PostgreSQL 支持 (可选)
- 用户仓库模式 (`src/server/database/user_repository.py`)

#### Web 前端界面
- React + TypeScript + Vite 项目 (`web/`)
- 函数列表页面 (`web/src/components/FunctionList.tsx`)
- 函数详情页面 (`web/src/components/FunctionDetail.tsx`)
- 函数发布页面 (`web/src/components/pages/PublishFunction.tsx`)
- 用户中心页面 (`web/src/components/pages/UserCenter.tsx`)
- GitHub OAuth 登录集成

#### Python SDK
- 同步客户端 (`src/sdk/python/agentfunchub/client.py`)
- 异步客户端 (`src/sdk/python/agentfunchub/async_client.py`)
- Function 对象封装 (`src/sdk/python/agentfunchub/function.py`)
- 异常处理 (`src/sdk/python/agentfunchub/exceptions.py`)
- SDK 文档 (`src/sdk/python/README.md`)

#### Docker 支持
- 后端 Dockerfile (`Dockerfile`)
- 前端 Dockerfile (`web/Dockerfile`)
- Docker Compose 配置 (`docker-compose.yml`)
- Nginx 配置 (`web/nginx.conf`)

#### CI/CD
- GitHub Actions CI 工作流 (`.github/workflows/ci.yml`)
- Release 工作流 (`.github/workflows/release.yml`)
- 部署文档 (`docs/deployment.md`)

#### 沙箱执行器
- Docker 沙箱执行环境 (`src/server/executor.py`)
- 函数执行 API (`src/server/api_execute.py`)
- 安全隔离和超时控制

### Changed

- 更新后端服务支持数据库存储
- 改进认证中间件
- 优化 API 响应格式
- 更新文档结构

### Fixed

- 修复测试配置，支持 SQLite 模式运行
- 修复 Pydantic V2 弃用警告 (`dict()` → `model_dump()`)
- 修复 FastAPI `on_event` 弃用警告

### Tests

- 新增 57 个测试用例，全部通过 ✅
  - `tests/test_api.py`: 21 个 API 测试
  - `tests/test_auth.py`: 16 个认证测试
  - `tests/test_integration.py`: 20 个集成测试
- 创建 `tests/conftest.py` 统一测试配置

## [0.1.0] - 2026-02-01

### Added

- FunctionSpec v0.1 规范定义
- 26 个示例函数
- FastAPI 后端服务
- 语义搜索功能 (向量搜索 + 关键词)
- 函数验证工具 (`scripts/validate_spec.py`)
- API 文档和项目愿景文档

[Unreleased]: https://github.com/zhuangbiaowei/AgentFuncHub/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/zhuangbiaowei/AgentFuncHub/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/zhuangbiaowei/AgentFuncHub/releases/tag/v0.1.0
