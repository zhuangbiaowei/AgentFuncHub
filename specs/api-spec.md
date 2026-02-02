# AgentFuncHub API 规范 (v0.1)

> 适配 FunctionSpec v0.1 格式

## 基础信息

- **Base URL**: `http://localhost:8000` (开发) / `https://api.agentfunchub.io/v1` (生产)
- **协议**: HTTP/HTTPS
- **数据格式**: JSON
- **认证**: 暂无 (MVP阶段)

---

## 数据模型

### FunctionSpec v0.1

所有 API 使用 FunctionSpec v0.1 格式作为函数的标准表示。

```yaml
spec_version: "0.1"           # 规范版本
id: "domain.category.name"     # 点分ID
version: "1.0.0"               # 函数版本
name: "Function Name"          # 显示名称
description: "Description"     # 描述

language:
  name: "python"               # 编程语言
  runtime: "python>=3.8"       # 运行时要求

entrypoint:
  kind: "inline"               # inline/file/container/wasm
  symbol: "func_name"          # 入口函数名
  code: "..."                  # 代码 (inline时)

signature:
  inputs:                      # 输入参数 (map)
    param1:
      type: "string"
      required: true
      description: "..."
  outputs:                     # 输出参数 (map)
    result:
      type: "boolean"
      description: "..."
  errors:                      # 错误定义
    - code: "E_INVALID"
      description: "..."

semantics:
  deterministic: true          # 是否确定性
  side_effects: ["none"]       # 副作用列表
  purity: "pure"
  security:
    sandbox_required: true
    data_sensitivity: "low"

tests:
  framework: "builtin"
  cases:
    - name: "test1"
      input: { param1: "value" }
      expect: { result: true }

tags: ["validation", "email"]
```

---

## 核心 API

### 1. 函数管理

#### 列出所有函数

```http
GET /functions?language=python&tag=validation&limit=10&offset=0
```

**响应:**
```json
{
  "success": true,
  "total": 26,
  "limit": 10,
  "offset": 0,
  "spec_version": "0.1",
  "functions": [
    {
      "spec_version": "0.1",
      "id": "validation.email.basic",
      "version": "1.0.0",
      "name": "Email Validator",
      "description": "Validate email format...",
      "language": { "name": "python", "runtime": "python>=3.8" },
      "entrypoint": { "kind": "inline", "symbol": "validate_email", "code": "..." },
      "signature": { "inputs": {...}, "outputs": {...} },
      "semantics": { "deterministic": true, "side_effects": ["none"] },
      "tags": ["validation", "email"]
    }
  ]
}
```

#### 获取函数详情

```http
GET /functions/{function_id}
```

**响应:**
```json
{
  "success": true,
  "spec_version": "0.1",
  "function": {
    "spec_version": "0.1",
    "id": "validation.email.basic",
    "version": "1.0.0",
    "name": "Email Validator",
    "description": "Validate email format...",
    "language": { "name": "python", "runtime": "python>=3.8" },
    "entrypoint": { "kind": "inline", "symbol": "validate_email", "code": "..." },
    "signature": { "inputs": {...}, "outputs": {...} },
    "semantics": { "deterministic": true, "side_effects": ["none"] },
    "tests": { "framework": "builtin", "cases": [...] },
    "examples": [...],
    "tags": ["validation", "email"],
    "quality": { "maturity": "stable", "coverage": 0.95 },
    "provenance": { "created_at": "2026-02-01", "source": { "kind": "manual" } }
  }
}
```

#### 创建函数

```http
POST /functions
Content-Type: application/json

{
  "spec_version": "0.1",
  "id": "my.new.function",
  "version": "1.0.0",
  "name": "My New Function",
  "description": "Description of the function",
  "language": { "name": "python", "runtime": "python>=3.8" },
  "entrypoint": {
    "kind": "inline",
    "symbol": "my_function",
    "code": "def my_function(x: int) -> int:\n    return x * 2"
  },
  "signature": {
    "inputs": {
      "x": { "type": "integer", "required": true, "description": "Input number" }
    },
    "outputs": {
      "result": { "type": "integer", "description": "Doubled number" }
    }
  },
  "semantics": {
    "deterministic": true,
    "side_effects": ["none"],
    "purity": "pure"
  },
  "tests": {
    "framework": "builtin",
    "cases": [
      { "name": "basic", "input": { "x": 5 }, "expect": { "result": 10 } }
    ]
  },
  "tags": ["math", "multiply"]
}
```

**响应:**
```json
{
  "success": true,
  "function_id": "my.new.function",
  "url": "/functions/my.new.function",
  "message": "Function created successfully",
  "indexed": true
}
```

#### 删除函数

```http
DELETE /functions/{function_id}
```

**响应:**
```json
{
  "success": true,
  "message": "Function deleted successfully"
}
```

---

### 2. 语义搜索

#### 搜索函数

```http
POST /search
Content-Type: application/json

{
  "query": "验证邮箱地址格式",
  "language": "python",
  "limit": 10
}
```

**响应:**
```json
{
  "success": true,
  "query": "验证邮箱地址格式",
  "total": 3,
  "spec_version": "0.1",
  "search_method": "hybrid",
  "results": [
    {
      "function_id": "validation.email.basic",
      "name": "Email Validator",
      "description": "Validate email format...",
      "similarity_score": 0.92,
      "spec": {
        "spec_version": "0.1",
        "id": "validation.email.basic",
        "name": "Email Validator",
        "description": "Validate email format...",
        "language": { "name": "python" },
        "tags": ["validation", "email"]
      }
    }
  ]
}
```

**搜索方法说明:**
- `hybrid` - 混合搜索（向量相似度 + 关键词匹配）
- `keyword` - 纯关键词搜索（当向量模型不可用时降级）

---

### 3. 验证服务

#### 验证函数

```http
POST /validate
Content-Type: application/json

{
  "spec_version": "0.1",
  "id": "test.function",
  "name": "Test Function",
  "description": "Test",
  "language": { "name": "python" },
  "entrypoint": {
    "kind": "inline",
    "symbol": "test",
    "code": "def test(x): return x"
  },
  "signature": {
    "inputs": { "x": { "type": "string", "required": true } },
    "outputs": { "result": { "type": "string" } }
  }
}
```

**响应:**
```json
{
  "valid": true,
  "spec_version": "0.1",
  "errors": [],
  "warnings": ["No test cases provided"]
}
```

**验证规则:**
- **必需字段**: `spec_version`, `id`, `version`, `name`, `description`, `language`, `entrypoint`, `signature`
- **ID 格式**: 建议使用点分格式 `domain.category.name`
- **版本格式**: 语义化版本 `x.y.z`
- **Entrypoint**: 
  - `inline` 类型必须提供 `code`
  - `file` 类型必须提供 `file`

---

### 4. 元数据查询

#### 获取所有标签

```http
GET /tags
```

**响应:**
```json
{
  "success": true,
  "tags": ["chinese", "convert", "csv", "data", "date", "email", "json", "list", "parse", "validation"]
}
```

#### 获取所有语言

```http
GET /languages
```

**响应:**
```json
{
  "success": true,
  "languages": ["python"]
}
```

---

### 5. 服务状态

#### 根路由

```http
GET /
```

**响应:**
```json
{
  "name": "AgentFuncHub",
  "version": "0.1.0",
  "spec_version": "0.1",
  "status": "running",
  "functions_count": 26,
  "search": {
    "method": "hybrid",
    "indexed_count": 26,
    "model": "all-MiniLM-L6-v2"
  }
}
```

#### 健康检查

```http
GET /health
```

**响应:**
```json
{
  "status": "healthy",
  "functions_loaded": 26,
  "spec_version": "0.1"
}
```

---

## 错误处理

### 错误响应格式

```json
{
  "detail": "Function not found"
}
```

### 常见错误码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 404 | 函数不存在 |
| 409 | 函数已存在 |
| 422 | 请求参数验证失败 |

---

## 从旧格式迁移

### 旧格式 (manifest.json)

```json
{
  "function_id": "func-001",
  "name": "validate_email",
  "display_name": "Email Validator",
  "description": "...",
  "language": "python",
  "signature": {
    "inputs": [{"name": "email", "type": "str"}],
    "outputs": [{"type": "bool"}]
  },
  "code": { "source": "..." }
}
```

### 新格式 (function.yaml)

```yaml
spec_version: "0.1"
id: "validation.email.basic"
name: "Email Validator"
description: "..."
language:
  name: "python"
entrypoint:
  kind: "inline"
  symbol: "validate_email"
  code: "..."
signature:
  inputs:
    email:
      type: "string"
      required: true
  outputs:
    is_valid:
      type: "boolean"
```

**主要变化:**
1. ID 格式从 `func-001` 变为点分格式 `validation.email.basic`
2. `signature.inputs` 从数组变为 map
3. `code.source` 变为 `entrypoint.code`
4. 新增 `semantics` 语义声明
5. 新增 `tests` 测试用例
6. 文件格式从 JSON 改为 YAML

---

## 本地开发

### 启动服务

```bash
cd src/server
python main.py
```

服务将在 `http://localhost:8000` 启动。

### 测试 API

```bash
# 列出函数
curl http://localhost:8000/functions

# 搜索函数
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "验证邮箱", "limit": 5}'

# 验证函数
curl -X POST http://localhost:8000/validate \
  -H "Content-Type: application/json" \
  -d @examples/validate_email/function.yaml
```

---

## SDK 示例 (规划中)

### Python SDK (未来)

```python
from agentfunchub import Client

client = Client()

# 搜索函数
results = client.search("验证邮箱", language="python")

# 获取函数详情
func = client.get_function("validation.email.basic")

# 发布函数
client.publish(function_spec)
```

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 0.1 | 2026-02-02 | 适配 FunctionSpec v0.1 |
